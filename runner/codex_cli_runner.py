from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
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
VENV_ROOT = PROJECT_ROOT / "runner" / ".venv"
CODEX_BIN = VENV_ROOT / "Lib" / "site-packages" / "codex_cli_bin" / "bin" / "codex.exe"
RUNTIME_DIR = PROJECT_ROOT / "data" / "runtime"
CODEX_RUNS_DIR = RUNTIME_DIR / "codex-runs"
ORCHESTRATION_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json"
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
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
    elif config_error:
        status_name = "config_error"
        message = "Codex configuration is invalid. Fix the reported config value before checking login again."
    else:
        status_name = "auth_required"
        message = "Codex runner needs login."

    return {
        "ok": status_name == "ready",
        "status": status_name,
        "codexBin": str(CODEX_BIN),
        "version": redact_text(version["stdout"] or version["stderr"], 500),
        "diagnostic": redact_text(login_text, 1200),
        "message": message,
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


def build_prompt(prompt: str, agent_id: str, mission_id: str, model_tier: str, output_limit: int) -> str:
    return f"""You are the real Codex worker behind Metafxclub AI Agent HQ.

Agent: {agent_id}
Mission: {mission_id}
Model tier: {model_tier}

Work mode:
- Read-only diagnostic/report mode.
- Do not edit files.
- Do not run destructive commands.
- Do not reveal secrets, tokens, auth files, cookies, or private credentials.
- If the user asks for a risky action, report that approval is required.
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
) -> dict:
    if not SAFE_ID_PATTERN.fullmatch(mission_id) or not SAFE_ID_PATTERN.fullmatch(agent_id):
        return {"ok": False, "status": "invalid_id", "message": "Agent or mission id is invalid."}
    if contains_potential_secret(prompt):
        return {"ok": False, "status": "secret_blocked", "message": "Potential secret detected. Submit intent without credentials."}
    prompt = str(prompt or "")[:8000]
    timeout = max(15, min(600, int(timeout)))
    output_limit = max(1000, min(20000, int(output_limit)))
    model_tier, tier = resolve_model_tier(model_tier)
    current_status = status()
    if current_status.get("status") != "ready":
        return {
            "ok": False,
            "status": current_status.get("status", "auth_required"),
            "message": current_status.get("message", "Codex runner is not ready."),
            "runner": current_status,
        }

    CODEX_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    mission_hash = hashlib.sha256(mission_id.encode("utf-8", errors="replace")).hexdigest()[:16]
    run_id = f"run-{mission_hash}-{int(time.time() * 1000)}"
    final_path = safe_artifact_path(run_id, ".final.md")
    stderr_path = safe_artifact_path(run_id, ".stderr.log")
    stdout_path = safe_artifact_path(run_id, ".stdout.log")

    wrapped_prompt = build_prompt(prompt, agent_id, mission_id, model_tier, output_limit)
    reasoning_effort = str(tier.get("reasoningEffort") or "low")
    if reasoning_effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
        reasoning_effort = "low"
    with tempfile.TemporaryDirectory(prefix="metafx-hq-codex-") as temporary_directory:
        raw_final_path = Path(temporary_directory) / "raw-final.md"
        command = [
            str(CODEX_BIN),
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--cd",
            str(PROJECT_ROOT),
            "-c",
            f'model_reasoning_effort="{reasoning_effort}"',
            "-o",
            str(raw_final_path),
            "-",
        ]
        model_name = tier.get("model")
        if isinstance(model_name, str) and model_name.strip():
            command[2:2] = ["--model", model_name.strip()]

        result = run_command(command, timeout=timeout, stdin=wrapped_prompt)
        raw_final = raw_final_path.read_text(encoding="utf-8", errors="replace") if raw_final_path.exists() else result.get("stdout", "")

    safe_stdout, stdout_secret_redacted = write_sanitized_artifact(stdout_path, result.get("stdout", ""), output_limit)
    safe_stderr, stderr_secret_redacted = write_sanitized_artifact(stderr_path, result.get("stderr", ""), output_limit)
    final_message, final_secret_redacted = write_sanitized_artifact(final_path, raw_final, output_limit)

    return {
        "ok": result["ok"],
        "status": "completed" if result["ok"] else "failed",
        "message": "Codex run completed." if result["ok"] else "Codex run failed.",
        "exitCode": result["exitCode"],
        "durationMs": result["durationMs"],
        "finalMessage": final_message.strip(),
        "modelTier": model_tier,
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
    parser.add_argument("--prompt", default="")
    parser.add_argument("--prompt-stdin", action="store_true")
    parser.add_argument("--agent-id", default="manager")
    parser.add_argument("--mission-id", default="manual")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--model-tier", default="specialist_fast")
    parser.add_argument("--output-limit", type=int, default=7000)
    args = parser.parse_args()

    if args.status:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0
    if args.rate_limits:
        print(json.dumps(read_rate_limits(args.timeout), ensure_ascii=False, indent=2))
        return 0
    if args.run:
        prompt = sys.stdin.read() if args.prompt_stdin else args.prompt
        print(json.dumps(run_codex(prompt, args.agent_id, args.mission_id, args.timeout, args.model_tier, args.output_limit), ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
