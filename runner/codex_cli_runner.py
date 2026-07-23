from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTO_WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
AUTO_ADDITIONAL_WRITE_ROOTS = (
    PROJECT_ROOT / "frontend",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "assets-source",
)
AUTO_WRITE_ROOT_LABELS = ("workspace", "frontend", "docs", "assets-source")
AUTO_DENIED_CONTROL_PLANE_ROOTS = (
    "backend",
    "runner",
    "contracts",
    "data/runtime",
    "scripts",
    "installer",
    ".git",
)
VENV_ROOT = PROJECT_ROOT / "runner" / ".venv"
CODEX_BIN = VENV_ROOT / "Lib" / "site-packages" / "codex_cli_bin" / "bin" / "codex.exe"
RUNTIME_DIR = PROJECT_ROOT / "data" / "runtime"
CODEX_RUNS_DIR = RUNTIME_DIR / "codex-runs"
ORCHESTRATION_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json"
AGENTS_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "agents" / "agents.json"
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
CHAT_MODEL = "gpt-5.5"
CHAT_DISABLED_FEATURES = (
    "shell_tool",
    "shell_snapshot",
    "computer_use",
    "browser_use",
    "browser_use_external",
    "in_app_browser",
    "apps",
    "plugins",
    "hooks",
    "multi_agent",
    "multi_agent_v2",
    "goals",
    "memories",
    "image_generation",
    "imagegenext",
    "workspace_dependencies",
    "tool_call_mcp_elicitation",
    "skill_mcp_dependency_install",
    "tool_suggest",
    "enable_mcp_apps",
    "request_permissions_tool",
    "standalone_web_search",
    "code_mode",
    "code_mode_only",
)
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(?:api[_ -]?key|token|password|passwd|secret|authorization|cookie|bot[_ -]?token|broker[_ -]?password|database[_ -]?url|connection[_ -]?string|private[_ -]?key|aws[_ -]?secret[_ -]?access[_ -]?key|github[_ -]?token)\b[\"']?\s*[:=]\s*[\"']?[^\s,;}\"']{4,}"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]{12,}"),
    re.compile(r"\bsk-[a-zA-Z0-9_-]{16,}\b"),
    re.compile(r"\b\d{6,12}:[a-zA-Z0-9_-]{20,}\b"),
    re.compile(r"\beyJ[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{8,}\b"),
    re.compile(r"\b(?:gh[pousr]_[a-zA-Z0-9]{20,}|xox[baprs]-[a-zA-Z0-9-]{16,})\b"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


def redact_text(value: str, limit: int = 20000) -> str:
    text = str(value or "")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET]", text)
    home = str(Path.home())
    if home:
        text = text.replace(home, "%USERPROFILE%")
    return text[:limit]


def contains_potential_secret(value: str) -> bool:
    text = str(value or "")
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def sanitized_environment() -> dict[str, str]:
    allowed_names = {
        "APPDATA",
        "CODEX_HOME",
        "COMSPEC",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LANG",
        "LC_ALL",
        "LOCALAPPDATA",
        "NUMBER_OF_PROCESSORS",
        "PATH",
        "PATHEXT",
        "PROCESSOR_ARCHITECTURE",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TERM",
        "TMP",
        "USERPROFILE",
        "WINDIR",
    }
    return {
        key: value
        for key, value in os.environ.items()
        if key.upper() in allowed_names
    }


def load_model_tiers() -> dict:
    try:
        payload = json.loads(ORCHESTRATION_CONTRACT_PATH.read_text(encoding="utf-8"))
        tiers = payload.get("modelTiers") if isinstance(payload, dict) else {}
        return tiers if isinstance(tiers, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def resolve_model_tier(tier_id: str) -> tuple[str, dict]:
    tiers = load_model_tiers()
    selected = tier_id if tier_id in tiers else "specialist_fast"
    tier = tiers.get(selected) if isinstance(tiers.get(selected), dict) else {}
    return selected, tier


def load_agent_persona(agent_id: str) -> dict | None:
    try:
        payload = json.loads(AGENTS_CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    agents = payload.get("agents") if isinstance(payload, dict) else []
    agent = next(
        (
            item
            for item in agents or []
            if isinstance(item, dict) and item.get("id") == agent_id
        ),
        None,
    )
    if not isinstance(agent, dict):
        return None
    return {
        "id": agent_id,
        "name": redact_text(str(agent.get("name") or agent_id), 120),
        "role": redact_text(str(agent.get("role") or "AI Agent"), 240),
        "goal": redact_text(str(agent.get("goal") or ""), 1200),
        "blockedActions": [
            redact_text(str(item), 120)
            for item in (agent.get("blocked_actions") or [])[:30]
            if isinstance(item, str)
        ],
        "memoryScope": redact_text(str(agent.get("memory_scope") or ""), 800),
        "outputFormat": redact_text(str(agent.get("output_format") or ""), 160),
    }


def sanitize_chat_history(history: object, max_turns: int = 8, max_chars: int = 12000) -> list[dict]:
    if not isinstance(history, list):
        return []
    cleaned = []
    for item in history[-200:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        if role not in {"user", "assistant"}:
            continue
        limit = 4000 if role == "user" else 5000
        content = redact_text(str(item.get("content") or ""), limit).strip()
        if not content or contains_potential_secret(content):
            continue
        cleaned.append({"role": role, "content": content})

    exchanges = []
    index = 0
    while index + 1 < len(cleaned):
        user_message = cleaned[index]
        assistant_reply = cleaned[index + 1]
        if user_message["role"] == "user" and assistant_reply["role"] == "assistant":
            exchanges.append((user_message, assistant_reply))
            index += 2
        else:
            index += 1

    exchange_limit = max(1, max_turns // 2)
    exchanges = exchanges[-exchange_limit:]
    bounded = []
    total_chars = 0
    for user_message, assistant_reply in reversed(exchanges):
        exchange_chars = len(user_message["content"]) + len(assistant_reply["content"])
        if total_chars + exchange_chars > max_chars:
            break
        bounded.append((user_message, assistant_reply))
        total_chars += exchange_chars
    bounded.reverse()
    return [message for exchange in bounded for message in exchange]


def safe_artifact_path(run_id: str, suffix: str) -> Path:
    if not SAFE_ID_PATTERN.fullmatch(run_id):
        raise ValueError("Unsafe run id.")
    root = CODEX_RUNS_DIR.resolve()
    path = (CODEX_RUNS_DIR / f"{run_id}{suffix}").resolve()
    if path.parent != root:
        raise ValueError("Artifact path escapes the Codex run directory.")
    return path


def write_sanitized_artifact(path: Path, value: str, limit: int) -> tuple[str, bool]:
    """Redact before an artifact ever enters the project/OneDrive runtime."""
    raw_value = str(value or "")
    secret_redacted = contains_potential_secret(raw_value)
    sanitized = redact_text(raw_value, limit)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(sanitized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
    return sanitized, secret_redacted


def run_command(command: list[str], timeout: int = 30, stdin: str | None = None) -> dict:
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            env=sanitized_environment(),
        )
        return {
            "ok": result.returncode == 0,
            "exitCode": result.returncode,
            "stdout": redact_text((result.stdout or "").strip(), 40000),
            "stderr": redact_text((result.stderr or "").strip(), 40000),
            "durationMs": round((time.perf_counter() - started) * 1000),
        }
    except subprocess.TimeoutExpired as error:
        return {
            "ok": False,
            "exitCode": "timeout",
            "stdout": redact_text((error.stdout or "").strip(), 40000) if isinstance(error.stdout, str) else "",
            "stderr": f"Timed out after {timeout}s.",
            "durationMs": round((time.perf_counter() - started) * 1000),
        }
    except Exception as error:
        return {
            "ok": False,
            "exitCode": "exception",
            "stdout": "",
            "stderr": redact_text(str(error), 4000),
            "durationMs": round((time.perf_counter() - started) * 1000),
        }


def _create_windows_kill_job(process: subprocess.Popen) -> dict | None:
    """Assign a suspended process to a kill-on-close Windows Job Object."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None
        information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        information.BasicLimitInformation.LimitFlags = 0x00002000
        if not kernel32.SetInformationJobObject(
            job,
            9,
            ctypes.byref(information),
            ctypes.sizeof(information),
        ):
            kernel32.CloseHandle(job)
            return None
        if not kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(int(process._handle))):
            kernel32.CloseHandle(job)
            return None
        return {
            "handle": int(job),
            "lock": threading.Lock(),
            "closed": False,
            "closeSucceeded": False,
        }
    except Exception:
        return None


def _close_windows_kill_job(job_holder: dict | None) -> bool | None:
    if not isinstance(job_holder, dict):
        return None
    lock = job_holder.get("lock")
    if not hasattr(lock, "__enter__"):
        return None
    with lock:
        if job_holder.get("closed"):
            return bool(job_holder.get("closeSucceeded"))
        handle = job_holder.get("handle")
        job_holder["closed"] = True
        job_holder["handle"] = None
        if not handle:
            return False
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            succeeded = bool(kernel32.CloseHandle(wintypes.HANDLE(int(handle))))
        except Exception:
            succeeded = False
        job_holder["closeSucceeded"] = succeeded
        return succeeded


def _resume_windows_process(process: subprocess.Popen) -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes

        ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtResumeProcess.restype = ctypes.c_long
        return ntdll.NtResumeProcess(wintypes.HANDLE(int(process._handle))) == 0
    except Exception:
        return False


def _terminate_process_tree(
    process: subprocess.Popen,
    job_holder: dict | None = None,
) -> bool:
    if process.poll() is not None:
        _close_windows_kill_job(job_holder)
        return True
    tree_signal_succeeded = False
    if os.name == "nt":
        job_closed = _close_windows_kill_job(job_holder)
        if job_closed is not None:
            tree_signal_succeeded = bool(job_closed)
        else:
            system_root = os.environ.get("SYSTEMROOT") or os.environ.get("WINDIR") or r"C:\Windows"
            taskkill = Path(system_root) / "System32" / "taskkill.exe"
            try:
                result = subprocess.run(
                    [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    timeout=8,
                    shell=False,
                    env=sanitized_environment(),
                )
                tree_signal_succeeded = result.returncode == 0
                if not tree_signal_succeeded and process.poll() is None:
                    process.kill()
            except Exception:
                if process.poll() is None:
                    process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            tree_signal_succeeded = True
        except (ProcessLookupError, PermissionError, OSError):
            if process.poll() is None:
                process.kill()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        if process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return False
    return tree_signal_succeeded and process.poll() is not None


def run_chat_command(
    command: list[str],
    timeout: int,
    stdin: str,
    cwd: Path,
    output_limit: int = 60000,
) -> dict:
    """Run one ephemeral chat process and kill its process tree on timeout."""
    started = time.perf_counter()
    creationflags = (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "CREATE_SUSPENDED", 0x00000004)
    ) if os.name == "nt" else 0
    process = None
    job_holder = None
    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            env=sanitized_environment(),
            creationflags=creationflags,
            start_new_session=os.name != "nt",
        )
        job_holder = _create_windows_kill_job(process)
        if os.name == "nt" and (not job_holder or not _resume_windows_process(process)):
            _terminate_process_tree(process, job_holder)
            raise RuntimeError("Unable to start Codex inside the guarded Windows process job.")
        try:
            stdout, stderr = process.communicate(input=stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            tree_terminated = _terminate_process_tree(process, job_holder)
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                if process.poll() is None:
                    process.kill()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                stdout, stderr = "", ""
                tree_terminated = False
            return {
                "ok": False,
                "exitCode": "timeout",
                "stdout": redact_text(stdout or "", output_limit),
                "stderr": f"Timed out after {timeout}s.",
                "durationMs": round((time.perf_counter() - started) * 1000),
                "processStarted": True,
                "processTreeTerminated": tree_terminated,
            }
        _close_windows_kill_job(job_holder)
        return {
            "ok": process.returncode == 0,
            "exitCode": process.returncode,
            "stdout": redact_text(stdout or "", output_limit),
            "stderr": redact_text(stderr or "", output_limit),
            "durationMs": round((time.perf_counter() - started) * 1000),
            "processStarted": True,
            "processTreeTerminated": False,
        }
    except Exception as error:
        tree_terminated = False
        if process is not None and process.poll() is None:
            tree_terminated = _terminate_process_tree(process, job_holder)
        return {
            "ok": False,
            "exitCode": "exception",
            "stdout": "",
            "stderr": redact_text(str(error), 4000),
            "durationMs": round((time.perf_counter() - started) * 1000),
            "processStarted": process is not None,
            "processTreeTerminated": tree_terminated,
        }
    finally:
        _close_windows_kill_job(job_holder)


def status() -> dict:
    if not CODEX_BIN.exists():
        return {
            "ok": False,
            "status": "missing",
            "codexBin": str(CODEX_BIN),
            "message": "Project Codex SDK binary is missing. Run runner setup first.",
        }

    version = run_command([str(CODEX_BIN), "--version"], timeout=10)
    login = run_command([str(CODEX_BIN), "login", "status"], timeout=15)
    login_text = login["stdout"] or login["stderr"]
    is_logged_in = login["ok"] and "logged in" in login_text.lower()
    login_lower = login_text.lower()
    config_error = "error loading configuration" in login_lower or "unknown variant" in login_lower
    if version["ok"] and is_logged_in:
        status_name = "ready"
        message = "Project Codex runner is ready."
    elif config_error and version["ok"]:
        status_name = "ready_guarded"
        message = "Codex runtime พร้อมสำหรับ guarded exec ซึ่งจะแยก user config ที่มีปัญหาออก; ระบบจะตรวจ Login จริงตอนเริ่มคำขอ"
    else:
        status_name = "auth_required"
        message = "Codex runner needs login."

    return {
        "ok": status_name in {"ready", "ready_guarded"},
        "status": status_name,
        "codexBin": str(CODEX_BIN),
        "version": redact_text(version["stdout"] or version["stderr"], 500),
        "diagnostic": redact_text(login_text, 1200),
        "message": message,
        "configIgnoredForGuardedExec": status_name == "ready_guarded",
        "authChecked": status_name == "ready",
        "time": utc_now(),
    }


def _bounded_percent(value: object) -> int | float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    bounded = max(0.0, min(100.0, number))
    return int(bounded) if bounded.is_integer() else round(bounded, 2)


def _rate_limit_reset_iso(value: object) -> str | None:
    try:
        timestamp = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if timestamp <= 0:
        return None
    try:
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")
    except (OSError, OverflowError, ValueError):
        return None


def sanitize_rate_limit_window(value: object) -> dict | None:
    """Allowlist one Codex quota window for the frontend-safe read model."""
    if not isinstance(value, dict):
        return None
    used_percent = _bounded_percent(value.get("usedPercent"))
    if used_percent is None:
        return None
    remaining_percent = _bounded_percent(100 - float(used_percent))
    try:
        duration = int(value.get("windowDurationMins"))
    except (TypeError, ValueError, OverflowError):
        duration = None
    if duration is not None and duration <= 0:
        duration = None
    return {
        "usedPercent": used_percent,
        "remainingPercent": remaining_percent,
        "windowDurationMinutes": duration,
        "resetsAt": _rate_limit_reset_iso(value.get("resetsAt")),
    }


def sanitize_rate_limits_response(value: object) -> dict:
    """Project the app-server response without account, plan, credit, or auth data."""
    if not isinstance(value, dict):
        return {
            "ok": False,
            "status": "unavailable",
            "message": "Codex rate-limit data is unavailable.",
            "source": "codex_app_server",
            "checkedAt": utc_now(),
            "stale": False,
        }
    buckets = value.get("rateLimitsByLimitId")
    snapshot = buckets.get("codex") if isinstance(buckets, dict) else None
    if not isinstance(snapshot, dict):
        snapshot = value.get("rateLimits")
    if not isinstance(snapshot, dict):
        return {
            "ok": False,
            "status": "unavailable",
            "message": "Codex did not return a canonical rate-limit meter.",
            "source": "codex_app_server",
            "checkedAt": utc_now(),
            "stale": False,
        }
    primary = sanitize_rate_limit_window(snapshot.get("primary"))
    secondary = sanitize_rate_limit_window(snapshot.get("secondary"))
    if primary is None:
        return {
            "ok": False,
            "status": "unavailable",
            "message": "Codex returned an incomplete rate-limit meter.",
            "source": "codex_app_server",
            "checkedAt": utc_now(),
            "stale": False,
        }
    return {
        "ok": True,
        "status": "ready",
        "source": "codex_app_server",
        "meter": {"id": "codex", "name": "Codex"},
        "primary": primary,
        "secondary": secondary,
        "limitReached": snapshot.get("rateLimitReachedType") is not None,
        "checkedAt": utc_now(),
        "stale": False,
    }


def _rate_limit_error(status_name: str) -> dict:
    messages = {
        "auth_required": "Codex login is required before quota can be read.",
        "config_error": "Codex configuration must be fixed before quota can be read.",
        "timeout": "Codex rate-limit check timed out.",
        "missing": "The project Codex runtime is unavailable.",
    }
    return {
        "ok": False,
        "status": status_name,
        "message": messages.get(status_name, "Codex rate-limit data is unavailable."),
        "source": "codex_app_server",
        "checkedAt": utc_now(),
        "stale": False,
    }


def read_rate_limits(timeout: int = 12) -> dict:
    """Read the logged-in Codex meter through app-server, never through auth files."""
    if not CODEX_BIN.exists():
        return _rate_limit_error("missing")
    timeout = max(3, min(30, int(timeout)))
    result_queue: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=1)
    client_holder: dict[str, object] = {}
    client_guard = threading.Lock()
    cancelled = threading.Event()

    def query_app_server() -> None:
        try:
            from openai_codex import CodexConfig
            from openai_codex.client import CodexClient
            from openai_codex.generated.v2_all import GetAccountRateLimitsResponse

            client = CodexClient(CodexConfig(
                codex_bin=str(CODEX_BIN),
                cwd=str(PROJECT_ROOT),
                env=sanitized_environment(),
                client_name="metafx_hq_rate_monitor",
                client_title="Metafxclub AI Agent HQ Rate Monitor",
                experimental_api=False,
            ))
            with client_guard:
                if cancelled.is_set():
                    return
                client_holder["client"] = client
                client.start()
            client.initialize()
            response = client.request(
                "account/rateLimits/read",
                None,
                response_model=GetAccountRateLimitsResponse,
            )
            raw = response.model_dump(by_alias=True, mode="json")
            result_queue.put_nowait(("ok", raw))
        except BaseException as error:
            try:
                result_queue.put_nowait(("error", error))
            except queue.Full:
                pass

    worker = threading.Thread(target=query_app_server, name="codex-rate-limit-read", daemon=True)
    worker.start()
    try:
        kind, payload = result_queue.get(timeout=timeout)
    except queue.Empty:
        cancelled.set()
        with client_guard:
            client = client_holder.get("client")
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
        worker.join(timeout=0.5)
        return _rate_limit_error("timeout")
    finally:
        cancelled.set()
        with client_guard:
            client = client_holder.get("client")
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass

    if kind == "ok":
        return sanitize_rate_limits_response(payload)
    error_text = str(payload).lower()
    if any(token in error_text for token in ("not logged in", "login required", "unauthorized")):
        return _rate_limit_error("auth_required")
    if any(token in error_text for token in ("error loading configuration", "unknown variant", "config.toml")):
        return _rate_limit_error("config_error")
    return _rate_limit_error("unavailable")


def chat_status() -> dict:
    """Check only the chat runtime; guarded exec is the authority for auth/config."""
    if not CODEX_BIN.exists():
        return {"ok": False, "status": "missing", "message": "Codex runtime สำหรับ Chat ยังไม่พร้อม"}
    version = run_command([str(CODEX_BIN), "--version"], timeout=10)
    if not version.get("ok"):
        return {
            "ok": False,
            "status": "unavailable",
            "message": "Codex Chat Runtime ยังไม่พร้อมใช้งาน",
        }
    return {
        "ok": True,
        "status": "runtime_ready",
        "message": "Codex Chat Runtime พร้อม โดยจะตรวจ Login และ Config ตอนส่งคำขอแบบ guarded exec",
        "version": redact_text(str(version.get("stdout") or ""), 200),
        "authChecked": False,
    }


def build_chat_prompt(
    message: str,
    persona: dict,
    history: list[dict],
    output_limit: int,
) -> str:
    blocked_actions = ", ".join(persona.get("blockedActions") or []) or "ไม่มีรายการเพิ่มเติม"
    history_lines = []
    for item in history:
        speaker = "ผู้ใช้" if item["role"] == "user" else str(persona.get("name") or "Agent")
        history_lines.append(f"{speaker}: {item['content']}")
    history_text = "\n".join(history_lines) if history_lines else "(ยังไม่มีบทสนทนาก่อนหน้า)"
    return f"""คุณกำลังตอบในโหมด Agent Chat ของ Metafxclub AI Agent HQ

ตัวตน:
- ชื่อ: {persona.get("name")}
- บทบาท: {persona.get("role")}
- เป้าหมายของบทบาท: {persona.get("goal")}
- ขอบเขตความจำที่เกี่ยวข้อง: {persona.get("memoryScope")}
- งานที่ถูกบล็อก: {blocked_actions}

กติกา Chat ที่ต้องทำตาม:
- ตอบเป็นภาษาไทยที่อ่านง่าย คำศัพท์เทคนิคใช้ภาษาอังกฤษได้เมื่อจำเป็น
- รักษาบุคลิกตามบทบาท ผู้บริหารตอบเชิงตัดสินใจและภาพรวม ผู้เชี่ยวชาญตอบตามสาขาของตน
- ทักทายและสนทนาอย่างเป็นธรรมชาติ ไม่บังคับรูปแบบรายงานสามหัวข้อ
- ห้ามใช้ Tool, Shell, Computer Use, Browser, Plugin, MCP หรืออ่านไฟล์ในเครื่อง
- ห้ามสร้าง Mission, Task, แก้ไฟล์, เปิดโปรแกรม, ส่งข้อความภายนอก หรือสั่งเทรด
- จำแนกข้อความใหม่เป็น intent = conversation เมื่อเป็นการทักทาย คำถาม คำแนะนำ หรือการคุยทั่วไป
- จำแนกเป็น intent = task_request เฉพาะเมื่อผู้ใช้สั่งให้ Agent ลงมือทำงานที่ควรส่งต่อไปยัง Backend
- หากเป็น task_request ให้เขียน taskGoal เป็นเป้าหมายงานแบบครบถ้วน กระชับ และไม่ใส่ Secret; Backend จะเป็นผู้สร้าง Mission หลัง Chat จบ
- หากเป็น conversation ให้ taskGoal เป็นข้อความว่าง
- อย่าบอกให้ผู้ใช้กดปุ่มสร้าง Task เพราะ Backend จะจัดการคำขอ task_request ให้โดยอัตโนมัติ
- ห้ามอ้างว่าได้ตรวจเครื่อง รันคำสั่ง เปิดไฟล์ หรือทำงานจริงแล้ว
- ห้ามเปิดเผย Token, Cookie, Auth, Password, Account, Broker หรือ Secret
- ตอบไม่เกิน {output_limit} ตัวอักษร

บทสนทนาล่าสุดของ Agent และ Session นี้เท่านั้น:
{history_text}

ข้อความใหม่จากผู้ใช้:
{message}

ตอบข้อความใหม่อย่างเป็นธรรมชาติในบทบาทที่กำหนด"""


def _chat_failure_status(result: dict) -> tuple[str, str]:
    if result.get("exitCode") == "timeout":
        return "timeout", "Codex Chat ใช้เวลานานเกินกำหนดและถูกหยุดแล้ว"
    diagnostic = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".lower()
    if any(token in diagnostic for token in ("not logged in", "login required", "unauthorized")):
        return "auth_required", "กรุณา Login Codex ในเครื่องก่อนเริ่ม Chat"
    if any(token in diagnostic for token in ("unknown feature", "unexpected argument", "unknown variant", "error loading configuration")):
        return "guard_config_error", "Codex รุ่นนี้ไม่รองรับ Guard สำหรับ Chat ครบถ้วน ระบบจึงหยุดแบบปลอดภัย"
    if any(token in diagnostic for token in ("rate limit", "usage limit")):
        return "rate_limited", "Codex แจ้งว่า Rate Limit ยังไม่พร้อมสำหรับข้อความใหม่"
    return "failed", "Codex Chat ทำงานไม่สำเร็จและไม่ได้ลองซ้ำอัตโนมัติ"


def _chat_quota_consumption(result: dict, status_name: str) -> tuple[bool, str]:
    """Return whether Codex was started and a conservative quota classification."""
    attempted = bool(result.get("processStarted", False))
    if not attempted:
        return False, "none"
    if result.get("ok") is True:
        return True, "confirmed"
    if status_name in {"auth_required", "guard_config_error", "rate_limited"}:
        return True, "none"
    return True, "possible"


def run_agent_chat(
    message: str,
    agent_id: str,
    session_id: str,
    history: object = None,
    timeout: int = 120,
    model_tier: str = "specialist_fast",
    output_limit: int = 5000,
) -> dict:
    if not SAFE_ID_PATTERN.fullmatch(agent_id) or not SAFE_ID_PATTERN.fullmatch(session_id):
        return {"ok": False, "status": "invalid_id", "message": "Agent หรือ Session ID ไม่ถูกต้อง"}
    persona = load_agent_persona(agent_id)
    if not persona:
        return {"ok": False, "status": "unknown_agent", "message": "ไม่พบ Agent นี้ในสัญญาระบบ"}
    message = str(message or "").strip()
    if not message or len(message) > 4000:
        return {"ok": False, "status": "invalid_message", "message": "ข้อความต้องมีความยาว 1-4,000 ตัวอักษร"}
    if contains_potential_secret(message):
        return {"ok": False, "status": "secret_blocked", "message": "พบข้อมูลที่อาจเป็นความลับ ระบบจึงไม่ได้ส่งข้อความไป Codex"}

    timeout = max(15, min(180, int(timeout)))
    output_limit = max(1000, min(5000, int(output_limit)))
    model_tier, tier = resolve_model_tier(model_tier)
    reasoning_effort = str(tier.get("reasoningEffort") or "low")
    if reasoning_effort not in {"low", "medium", "high"}:
        reasoning_effort = "low"
    readiness = chat_status()
    if not readiness.get("ok"):
        return {
            "ok": False,
            "status": str(readiness.get("status") or "unavailable"),
            "message": str(readiness.get("message") or "Codex Chat ยังไม่พร้อมใช้งาน"),
            "quotaAttempted": False,
            "quotaConsumption": "none",
        }

    safe_history = sanitize_chat_history(history, max_turns=16, max_chars=12000)
    wrapped_prompt = build_chat_prompt(message, persona, safe_history, output_limit)
    output_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"type": "string", "const": "completed"},
            "reply": {"type": "string", "minLength": 1, "maxLength": output_limit},
            "intent": {"type": "string", "enum": ["conversation", "task_request"]},
            "taskGoal": {"type": "string", "maxLength": 4000},
        },
        "required": ["status", "reply", "intent", "taskGoal"],
    }
    with tempfile.TemporaryDirectory(prefix="metafx-hq-chat-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        schema_path = temporary_root / "chat-output-schema.json"
        final_path = temporary_root / "chat-final.json"
        schema_path.write_text(json.dumps(output_schema, ensure_ascii=False), encoding="utf-8")
        command = [
            str(CODEX_BIN),
            "exec",
            "--model",
            CHAT_MODEL,
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--strict-config",
            "--sandbox",
            "read-only",
            "--cd",
            str(temporary_root),
            "--color",
            "never",
            "-c",
            f'model_reasoning_effort="{reasoning_effort}"',
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(final_path),
        ]
        for feature in CHAT_DISABLED_FEATURES:
            command.extend(["--disable", feature])
        command.append("-")
        result = run_chat_command(
            command,
            timeout=timeout,
            stdin=wrapped_prompt,
            cwd=temporary_root,
            output_limit=max(20000, output_limit * 4),
        )
        if not result.get("ok"):
            status_name, failure_message = _chat_failure_status(result)
            quota_attempted, quota_consumption = _chat_quota_consumption(result, status_name)
            return {
                "ok": False,
                "status": status_name,
                "message": failure_message,
                "durationMs": result.get("durationMs"),
                "modelTier": model_tier,
                "model": CHAT_MODEL,
                "reasoningEffort": reasoning_effort,
                "quotaAttempted": quota_attempted,
                "quotaConsumption": quota_consumption,
                "processTreeTerminated": result.get("processTreeTerminated"),
            }
        try:
            if not final_path.is_file() or final_path.stat().st_size > max(24000, output_limit * 4):
                raise ValueError("missing or oversized chat result")
            raw_final = final_path.read_text(encoding="utf-8", errors="replace")
            parsed = json.loads(raw_final)
        except (OSError, ValueError, json.JSONDecodeError):
            return {
                "ok": False,
                "status": "invalid_output",
                "message": "Codex Chat ส่งผลลัพธ์ที่ตรวจสอบรูปแบบไม่ได้",
                "durationMs": result.get("durationMs"),
                "modelTier": model_tier,
                "model": CHAT_MODEL,
                "reasoningEffort": reasoning_effort,
                "quotaAttempted": True,
                "quotaConsumption": "confirmed",
            }

    if not isinstance(parsed, dict) or parsed.get("status") != "completed":
        return {
            "ok": False,
            "status": "invalid_output",
            "message": "Codex Chat ส่งสถานะที่ไม่ตรงกับสัญญาระบบ",
            "durationMs": result.get("durationMs"),
            "modelTier": model_tier,
            "model": CHAT_MODEL,
            "reasoningEffort": reasoning_effort,
            "quotaAttempted": True,
            "quotaConsumption": "confirmed",
        }
    raw_reply = str(parsed.get("reply") or "").strip()
    if not raw_reply:
        return {
            "ok": False,
            "status": "empty_output",
            "message": "Codex Chat ไม่ได้ส่งข้อความตอบกลับ",
            "durationMs": result.get("durationMs"),
            "modelTier": model_tier,
            "model": CHAT_MODEL,
            "reasoningEffort": reasoning_effort,
            "quotaAttempted": True,
            "quotaConsumption": "confirmed",
        }
    intent = str(parsed.get("intent") or "").strip()
    raw_task_goal = str(parsed.get("taskGoal") or "").strip()
    if intent not in {"conversation", "task_request"}:
        return {
            "ok": False,
            "status": "invalid_output",
            "message": "Codex Chat ส่งประเภทคำขอที่ไม่ตรงกับสัญญาระบบ",
            "durationMs": result.get("durationMs"),
            "modelTier": model_tier,
            "model": CHAT_MODEL,
            "reasoningEffort": reasoning_effort,
            "quotaAttempted": True,
            "quotaConsumption": "confirmed",
        }
    if intent == "conversation":
        raw_task_goal = ""
    elif not raw_task_goal or len(raw_task_goal) > 4000 or contains_potential_secret(raw_task_goal):
        return {
            "ok": False,
            "status": "invalid_task_goal",
            "message": "Codex Chat ไม่สามารถสร้างเป้าหมายงานที่ปลอดภัยได้ จึงยังไม่สร้าง Mission",
            "durationMs": result.get("durationMs"),
            "modelTier": model_tier,
            "model": CHAT_MODEL,
            "reasoningEffort": reasoning_effort,
            "quotaAttempted": True,
            "quotaConsumption": "confirmed",
        }
    secret_redacted = contains_potential_secret(raw_reply)
    reply = redact_text(raw_reply, output_limit).strip()
    task_goal = redact_text(raw_task_goal, 4000).strip()
    return {
        "ok": True,
        "status": "completed",
        "message": "Codex Chat ตอบกลับแล้ว",
        "finalMessage": reply,
        "intent": intent,
        "taskGoal": task_goal,
        "agentName": persona["name"],
        "durationMs": result.get("durationMs"),
        "modelTier": model_tier,
        "model": CHAT_MODEL,
        "reasoningEffort": reasoning_effort,
        "quotaAttempted": True,
        "quotaConsumption": "confirmed",
        "usage": {
            "outputChars": len(reply),
            "timeoutSeconds": timeout,
            "outputLimitChars": output_limit,
            "contextTurns": len(safe_history),
            "secretRedacted": secret_redacted,
        },
        "guardrails": {
            "toolsEnabled": False,
            "computerUseEnabled": False,
            "projectWorkspaceExposed": False,
            "ephemeral": True,
        },
    }


def build_prompt(
    prompt: str,
    agent_id: str,
    mission_id: str,
    model_tier: str,
    output_limit: int,
    execution_mode: str = "manual_guarded",
) -> str:
    if execution_mode == "auto_guarded":
        write_roots = ", ".join(
            [str(AUTO_WORKSPACE_ROOT), *(str(path) for path in AUTO_ADDITIONAL_WRITE_ROOTS)]
        )
        denied_roots = ", ".join(AUTO_DENIED_CONTROL_PLANE_ROOTS)
        work_mode = f"""- Guarded allowlisted workspace mode.
- Your working directory is: {AUTO_WORKSPACE_ROOT}
- You may create or edit files only in these writable roots: {write_roots}
- The rest of the repository is read-only.
- Never modify these control-plane roots: {denied_roots}
- Follow every applicable AGENTS.md and project instruction. Never disable or ignore project rules.
- Local, non-destructive commands are allowed only when needed for this mission.
- Do not delete files or directories. Do not move or rename existing files.
- Do not use network access, Browser, Computer Use, MCP, Plugin, external apps, Telegram, MT4/MT5 terminals, broker software, or cloud services.
- Do not trade, place/close orders, deploy, publish externally, restart VPS, spend money/credit, or touch live infrastructure.
- Do not read or reveal tokens, auth files, cookies, broker credentials, passwords, private keys, or other secrets.
- If the requested result needs any forbidden action, stop that part and explain which human approval or adapter is required."""
    else:
        work_mode = """- Read-only diagnostic/report mode.
- Do not edit, create, move, rename, or delete files.
- Do not run destructive commands.
- Do not use network access, external apps, live trading, Telegram sending, or deployment.
- Do not reveal secrets, tokens, auth files, cookies, or private credentials.
- If the user asks for a risky action, report that approval is required."""
    return f"""You are the real Codex worker behind Metafxclub AI Agent HQ.

Agent: {agent_id}
Mission: {mission_id}
Model tier: {model_tier}

Work mode:
{work_mode}
- Reply in Thai unless a technical term is clearer in English.
- Keep the final response within {output_limit} characters.

User mission:
{prompt}

Return a concise dashboard-ready report with:
1. สถานะงาน
2. สิ่งที่ตรวจพบ
3. ขั้นตอนถัดไป
"""


def run_codex(
    prompt: str,
    agent_id: str = "manager",
    mission_id: str = "manual",
    timeout: int = 240,
    model_tier: str = "specialist_fast",
    output_limit: int = 7000,
    execution_mode: str = "manual_guarded",
) -> dict:
    if not SAFE_ID_PATTERN.fullmatch(mission_id) or not SAFE_ID_PATTERN.fullmatch(agent_id):
        return {"ok": False, "status": "invalid_id", "message": "Agent or mission id is invalid."}
    if contains_potential_secret(prompt):
        return {"ok": False, "status": "secret_blocked", "message": "Potential secret detected. Submit intent without credentials."}
    if execution_mode not in {"manual_guarded", "auto_guarded"}:
        return {"ok": False, "status": "invalid_execution_mode", "message": "Unsupported execution mode."}
    prompt = str(prompt or "")[:8000]
    timeout = max(15, min(600, int(timeout)))
    output_limit = max(1000, min(20000, int(output_limit)))
    model_tier, tier = resolve_model_tier(model_tier)
    current_status = status()
    if current_status.get("status") not in {"ready", "ready_guarded"}:
        return {
            "ok": False,
            "status": current_status.get("status", "auth_required"),
            "message": current_status.get("message", "Codex runner is not ready."),
            "runner": current_status,
        }

    if execution_mode == "auto_guarded":
        try:
            for writable_root in (AUTO_WORKSPACE_ROOT, *AUTO_ADDITIONAL_WRITE_ROOTS):
                writable_root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            return {
                "ok": False,
                "status": "workspace_setup_failed",
                "message": "ไม่สามารถเตรียมพื้นที่ทำงานที่อนุญาตไว้ได้ จึงยังไม่เริ่ม Codex",
                "error": redact_text(str(error), 1000),
                "executionMode": execution_mode,
                "sandbox": "workspace-write",
                "workingDirectory": "workspace",
                "writeRoots": list(AUTO_WRITE_ROOT_LABELS),
                "controlPlaneWritable": False,
                "processStarted": False,
                "processTreeTerminated": False,
            }
    CODEX_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    mission_hash = hashlib.sha256(mission_id.encode("utf-8", errors="replace")).hexdigest()[:16]
    run_id = f"run-{mission_hash}-{int(time.time() * 1000)}"
    final_path = safe_artifact_path(run_id, ".final.md")
    stderr_path = safe_artifact_path(run_id, ".stderr.log")
    stdout_path = safe_artifact_path(run_id, ".stdout.log")

    wrapped_prompt = build_prompt(
        prompt,
        agent_id,
        mission_id,
        model_tier,
        output_limit,
        execution_mode,
    )
    reasoning_effort = str(tier.get("reasoningEffort") or "low")
    if reasoning_effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
        reasoning_effort = "low"
    with tempfile.TemporaryDirectory(prefix="metafx-hq-codex-") as temporary_directory:
        raw_final_path = Path(temporary_directory) / "raw-final.md"
        working_directory = AUTO_WORKSPACE_ROOT if execution_mode == "auto_guarded" else PROJECT_ROOT
        command = [
            str(CODEX_BIN),
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--strict-config",
            "--sandbox",
            "workspace-write" if execution_mode == "auto_guarded" else "read-only",
            "--cd",
            str(working_directory),
            "-c",
            f'model_reasoning_effort="{reasoning_effort}"',
            "-o",
            str(raw_final_path),
            "-",
        ]
        if execution_mode == "auto_guarded":
            add_dir_args = []
            for allowed_root in AUTO_ADDITIONAL_WRITE_ROOTS:
                add_dir_args.extend(["--add-dir", str(allowed_root)])
            command[command.index("-c"):command.index("-c")] = add_dir_args
        model_name = tier.get("model")
        if isinstance(model_name, str) and model_name.strip():
            command[2:2] = ["--model", model_name.strip()]

        result = run_chat_command(
            command,
            timeout=timeout,
            stdin=wrapped_prompt,
            cwd=working_directory,
            output_limit=max(40000, output_limit + 10000),
        )
        raw_final = raw_final_path.read_text(encoding="utf-8", errors="replace") if raw_final_path.exists() else result.get("stdout", "")

    safe_stdout, stdout_secret_redacted = write_sanitized_artifact(stdout_path, result.get("stdout", ""), output_limit)
    safe_stderr, stderr_secret_redacted = write_sanitized_artifact(stderr_path, result.get("stderr", ""), output_limit)
    final_message, final_secret_redacted = write_sanitized_artifact(final_path, raw_final, output_limit)

    diagnostic = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".lower()
    if result["ok"]:
        result_status = "completed"
        result_message = "Codex ทำงานเสร็จแล้ว"
    elif result.get("exitCode") == "timeout":
        result_status = "timeout"
        result_message = "Codex ใช้เวลานานเกินกำหนดและถูกหยุดแล้ว"
    elif any(token in diagnostic for token in ("not logged in", "login required", "unauthorized")):
        result_status = "auth_required"
        result_message = "กรุณา Login Codex ในเครื่องก่อนเริ่มงาน"
    elif any(token in diagnostic for token in ("rate limit", "usage limit")):
        result_status = "rate_limited"
        result_message = "Codex แจ้งว่า Rate Limit ยังไม่พร้อมสำหรับงานใหม่"
    elif any(token in diagnostic for token in ("unknown feature", "unexpected argument", "error loading configuration")):
        result_status = "guard_config_error"
        result_message = "Codex รุ่นนี้ไม่รองรับ Guard ที่กำหนดครบถ้วน ระบบจึงหยุดแบบปลอดภัย"
    else:
        result_status = "failed"
        result_message = "Codex ทำงานไม่สำเร็จ"

    return {
        "ok": result["ok"],
        "status": result_status,
        "message": result_message,
        "exitCode": result["exitCode"],
        "durationMs": result["durationMs"],
        "processStarted": bool(result.get("processStarted", False)),
        "processTreeTerminated": bool(result.get("processTreeTerminated", False)),
        "finalMessage": final_message.strip(),
        "modelTier": model_tier,
        "executionMode": execution_mode,
        "sandbox": "workspace-write" if execution_mode == "auto_guarded" else "read-only",
        "workingDirectory": "workspace" if execution_mode == "auto_guarded" else ".",
        "writeRoots": list(AUTO_WRITE_ROOT_LABELS) if execution_mode == "auto_guarded" else [],
        "controlPlaneWritable": False,
        "reasoningEffort": reasoning_effort,
        "usage": {
            "outputChars": len(final_message),
            "timeoutSeconds": timeout,
            "outputLimitChars": output_limit,
            "secretRedacted": stdout_secret_redacted or stderr_secret_redacted or final_secret_redacted,
        },
        "artifacts": {
            "final": project_relative(final_path),
            "stdout": project_relative(stdout_path),
            "stderr": project_relative(stderr_path),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Metafxclub project Codex runner")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--rate-limits", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--chat", action="store_true")
    parser.add_argument("--chat-request-stdin", action="store_true")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--prompt-stdin", action="store_true")
    parser.add_argument("--agent-id", default="manager")
    parser.add_argument("--mission-id", default="manual")
    parser.add_argument("--session-id", default="session")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--model-tier", default="specialist_fast")
    parser.add_argument("--output-limit", type=int, default=7000)
    parser.add_argument(
        "--execution-mode",
        choices=("manual_guarded", "auto_guarded"),
        default="manual_guarded",
    )
    args = parser.parse_args()

    if args.status:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0
    if args.rate_limits:
        print(json.dumps(read_rate_limits(args.timeout), ensure_ascii=False, indent=2))
        return 0
    if args.chat:
        if not args.chat_request_stdin:
            result = {"ok": False, "status": "invalid_request", "message": "Chat request must be supplied through stdin."}
        else:
            try:
                request = json.loads(sys.stdin.read())
            except json.JSONDecodeError:
                request = None
            if not isinstance(request, dict):
                result = {"ok": False, "status": "invalid_request", "message": "Chat request JSON is invalid."}
            else:
                result = run_agent_chat(
                    str(request.get("message") or ""),
                    args.agent_id,
                    args.session_id,
                    request.get("history"),
                    args.timeout,
                    args.model_tier,
                    args.output_limit,
                )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.run:
        prompt = sys.stdin.read() if args.prompt_stdin else args.prompt
        print(
            json.dumps(
                run_codex(
                    prompt,
                    args.agent_id,
                    args.mission_id,
                    args.timeout,
                    args.model_tier,
                    args.output_limit,
                    args.execution_mode,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
