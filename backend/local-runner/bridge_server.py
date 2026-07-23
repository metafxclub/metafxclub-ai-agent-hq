from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import secrets
import signal
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_RUNTIME_VERSION = "0.9.0"
SERVER_STARTED_AT = datetime.now(timezone.utc).isoformat()
SERVER_STARTED_MONOTONIC = time.monotonic()
RUNTIME_DIR = PROJECT_ROOT / "data" / "runtime"
PROJECT_RUNTIME_DIR = RUNTIME_DIR
MISSIONS_PATH = RUNTIME_DIR / "missions.json"
OPERATOR_MODE_PATH = RUNTIME_DIR / "operator-mode.json"
AUDIT_PATH = RUNTIME_DIR / "bridge-audit.jsonl"
UI_SESSION_PATH = RUNTIME_DIR / "ui-session.json"
AGENT_EVENTS_PATH = RUNTIME_DIR / "agent-events.jsonl"
MEMORY_DIR = PROJECT_ROOT / "data" / "memory"
MEMORY_INDEX_PATH = MEMORY_DIR / "memory-index.json"
MEETING_TRANSCRIPTS_PATH = MEMORY_DIR / "meetings" / "meeting-transcripts.jsonl"
AGENTS_PATH = PROJECT_ROOT / "contracts" / "agents" / "agents.json"
ROOM_PATH = PROJECT_ROOT / "contracts" / "rooms" / "command-room.json"
PROPERTY_ROLE_MAP_PATH = PROJECT_ROOT / "contracts" / "props" / "property-role-map.json"
DASHBOARD_CONNECTION_PATH = PROJECT_ROOT / "contracts" / "connections" / "dashboard-connection-contract.json"
TOOL_PERMISSION_PATH = PROJECT_ROOT / "contracts" / "tools" / "tool-permission-contract.json"
REPORT_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "reports" / "report-contract.json"
ORCHESTRATION_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json"
RUNTIME_REPORTS_DIR = RUNTIME_DIR / "reports"
AGENT_EVENTS_LOCK = threading.Lock()
MEETING_TRANSCRIPTS_LOCK = threading.Lock()
MEMORY_INDEX_LOCK = threading.RLock()
AUDIT_LOCK = threading.Lock()
MISSIONS_LOCK = threading.RLock()
REPORTS_LOCK = threading.RLock()
RATE_LIMIT_LOCK = threading.Lock()
CODEX_RATE_LIMIT_CACHE_LOCK = threading.Lock()
METATRADER_CACHE_LOCK = threading.Lock()
METATRADER_TARGETS_LOCK = threading.RLock()
AGENT_CHAT_LOCK = threading.RLock()
AGENT_CHAT_INFLIGHT: set[str] = set()
REAL_RUN_SEMAPHORE = threading.BoundedSemaphore(value=1)
MISSION_WORKER_LOCK = threading.RLock()
MISSION_WORKER_WAKE = threading.Event()
MISSION_WORKER_STOP = threading.Event()
MISSION_WORKER_THREAD: threading.Thread | None = None
MISSION_WORKER_WATCHDOG_THREAD: threading.Thread | None = None
MISSION_WORKER_PROCESS_LOCK = threading.RLock()
MISSION_WORKER_PROCESS: subprocess.Popen | None = None
MISSION_WORKER_JOB_HOLDER: dict | None = None
MISSION_WORKER_STATE: dict[str, object] = {
    "status": "stopped",
    "workerId": None,
    "currentMissionId": None,
    "startedAt": None,
    "heartbeatAt": None,
    "lastError": None,
}
RATE_LIMIT_STATE: dict[str, list[float]] = {}
CODEX_RATE_LIMIT_CACHE: dict[str, object] = {
    "payload": None,
    "fetchedMonotonic": 0.0,
    "invalidated": False,
}
METATRADER_CACHE: dict[str, object] = {
    "payload": None,
    "fetchedMonotonic": 0.0,
}
CODEX_RATE_LIMIT_CACHE_TTL_SECONDS = 75
CODEX_RATE_LIMIT_STALE_MAX_SECONDS = 15 * 60
CODEX_RATE_LIMIT_FORCE_MIN_SECONDS = 15
CODEX_RATE_LIMIT_TELEMETRY_MISSION_ID = "system-codex-rate-monitor"
CODEX_RATE_LIMIT_OWNER_AGENT_ID = "codex_mcp_operator"
METATRADER_CACHE_TTL_SECONDS = 45
METATRADER_TARGET_STORE_FILENAME = "metatrader-targets.json"
AGENT_CHAT_TRANSCRIPT_FILENAME = "agent-chat-transcripts.jsonl"
AGENT_CHAT_RESULTS_DIRNAME = "agent-chat-results"
METATRADER_TARGET_PROP_IDS = frozenset({
    "right_server_racks",
    "left_analytics_console",
    "terminal_workstation",
    "left_signal_cube",
})
CODEX_RUNNER_PYTHON = PROJECT_ROOT / "runner" / ".venv" / "Scripts" / "python.exe"
CODEX_RUNNER_SCRIPT = PROJECT_ROOT / "runner" / "codex_cli_runner.py"

STATIC_ALLOWED_EXACT = {"/", "/index.html", "/frontend", "/frontend/"}
STATIC_ALLOWED_PREFIXES = ("/frontend/", "/contracts/")
MAX_REQUEST_BYTES = 65536
JSONL_SEGMENT_MAX_BYTES = 5 * 1024 * 1024
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
SAFE_IDEMPOTENCY_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$")
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(?:api[_ -]?key|token|password|passwd|secret|authorization|cookie|bot[_ -]?token|broker[_ -]?password|database[_ -]?url|connection[_ -]?string|private[_ -]?key|aws[_ -]?secret[_ -]?access[_ -]?key|github[_ -]?token)\b[\"']?\s*[:=]\s*[\"']?[^\s,;}\"']{4,}"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]{12,}"),
    re.compile(r"\bsk-[a-zA-Z0-9_-]{16,}\b"),
    re.compile(r"\b\d{6,12}:[a-zA-Z0-9_-]{20,}\b"),
    re.compile(r"\beyJ[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{8,}\b"),
    re.compile(r"\b(?:gh[pousr]_[a-zA-Z0-9]{20,}|xox[baprs]-[a-zA-Z0-9-]{16,})\b"),
]
HIGH_IMPACT_INTENT_PATTERNS = (
    ("delete_or_remove", re.compile(
        r"(?i)(?:"
        r"\b(?:delete|remove|erase|wipe|purge)\b.{0,80}\b(?:file|folder|directory|path|repo(?:sitory)?|codebase|source\s+tree)\b|"
        r"\b(?:file|folder|directory|path|repo(?:sitory)?|codebase|source\s+tree)\b.{0,80}\b(?:delete|remove|erase|wipe|purge)\b|"
        r"\b(?:delete|remove|erase|wipe|purge)\b.{0,100}\b[a-z0-9_.-]+\.(?:js|mjs|cjs|ts|tsx|jsx|py|ps1|bat|cmd|json|toml|ya?ml|xml|ini|cfg|md|txt|csv|mq4|mq5|ex4|ex5|dll|exe)\b|"
        r"(?:^|[\s;&|])(?:rm|del|rmdir|unlink|remove-item)(?:\.exe)?(?:\s|$)|"
        r"ลบ\s*ไฟล์|ลบ\s*โฟลเดอร์|ลบ\s*ไดเรกทอรี|ล้าง\s*ไฟล์|ล้าง\s*โฟลเดอร์|เอา\s*ไฟล์\s*ออก"
        r")"
    )),
    ("restart_infrastructure", re.compile(
        r"(?i)(?:\b(?:reboot|restart)\b.{0,40}\b(?:vps|server|terminal)\b|"
        r"\b(?:vps|server|terminal)\b.{0,40}\b(?:reboot|restart)\b|"
        r"(?:รีบูต|รีสตาร์ต).{0,40}(?:vps|server|terminal|เซิร์ฟเวอร์|เทอร์มินัล)|"
        r"(?:vps|server|terminal|เซิร์ฟเวอร์|เทอร์มินัล).{0,40}(?:รีบูต|รีสตาร์ต))"
    )),
    ("production_publish", re.compile(
        r"(?i)(?:\bdeploy\b|\bpublish\b.{0,50}\bproduction\b|"
        r"\bproduction\b.{0,50}\bpublish\b|\bgo\s+live\b|"
        r"\b(?:post|publish|share|upload)\b.{0,80}\b(?:publicly|public|externally|external|internet)\b|"
        r"ดีพลอย|ขึ้น\s*production|เผยแพร่.{0,30}(?:production|สาธารณะ|ภายนอก))"
    )),
    ("live_trading", re.compile(
        r"(?i)(?:\blive\s+(?:account|trade|trading)\b|\btrade\b.{0,40}\blive\s+account\b|"
        r"\b(?:place|open|close|execute)\b.{0,30}\b(?:order|position)\b|"
        r"เทรดจริง|เทรดบัญชีจริง|เปิด\s*position|ปิด\s*position|ยิงออเดอร์|ส่งออเดอร์|เปิดออเดอร์|ปิดออเดอร์|คำสั่งซื้อขาย)"
    )),
    ("real_telegram_send", re.compile(
        r"(?i)(?:\b(?:send|post)\b.{0,60}\btelegram\b|\btelegram\b.{0,60}\b(?:send|post|message)\b|"
        r"ส่งข้อความ.{0,30}(?:telegram|เทเลแกรม)|ส่งเข้า.{0,20}(?:telegram|เทเลแกรม)|ส่งเทเลแกรมจริง)"
    )),
    ("external_message_send", re.compile(
        r"(?i)(?:\b(?:send|post|forward)\b.{0,60}\b(?:e-?mail|slack|teams|discord)\b|"
        r"\b(?:e-?mail|slack|teams|discord)\b.{0,60}\b(?:send|post|forward|message)\b|"
        r"ส่ง.{0,40}(?:อีเมล|อีเมล์|slack|teams|discord))"
    )),
    ("secret_or_credential_access", re.compile(
        r"(?i)(?:"
        r"\b(?:read|open|show|print|inspect|summari[sz]e|cat|type)\b.{0,80}\b(?:auth(?:entication)?(?:\.json)?|credentials?|passwords?|tokens?|cookies?|secrets?|private\s+keys?|config\.toml)\b|"
        r"\b(?:auth(?:entication)?(?:\.json)?|credentials?|passwords?|tokens?|cookies?|secrets?|private\s+keys?|config\.toml)\b.{0,80}\b(?:read|open|show|print|inspect|summari[sz]e|cat|type)\b|"
        r"(?:อ่าน|เปิด|แสดง|สรุป|ตรวจ).{0,60}(?:ไฟล์\s*auth|ข้อมูลลับ|รหัสผ่าน|โทเคน|คุกกี้|private\s*key|credentials?)"
        r")"
    )),
    ("money_or_withdrawal", re.compile(
        r"(?i)(?:\breal\s+money\b|\bwithdraw(?:al)?\b|\b(?:spend|buy|purchase|pay|subscribe)\b|"
        r"ใช้เงินจริง|ถอนเงิน|จ่ายเงิน|ซื้อ.{0,30}(?:บริการ|เครดิต)|ใช้เครดิต)"
    )),
)
SENSITIVE_FIELD_SUFFIXES = (
    "token",
    "password",
    "passwd",
    "secret",
    "cookie",
    "authorization",
    "privatekey",
    "apikey",
    "databaseurl",
    "connectionstring",
    "account",
    "accountid",
    "accountlogin",
    "accountnumber",
    "brokerserver",
    "terminalpath",
    "processid",
)
SENSITIVE_FIELD_METADATA = {"containssecret", "secretredacted", "frontendsecrets"}

APPROVAL_REQUIRED = [
    "codex_cli_task",
    "mcp_tool_run",
    "live_trading",
    "send_telegram",
    "delete_files",
    "publish_external",
    "spend_credit",
    "restart_vps",
    "production_deploy",
    "spawn_worker",
]

MISSION_STRATEGY_TABLE_PROP_ID = "mission_strategy_table"
MISSION_STATUS_ORDER = (
    "queued",
    "running",
    "waiting_approval",
    "blocked",
    "completed",
    "failed",
    "archived",
)
EXPECTED_AGENT_IDS = (
    "manager",
    "ceo",
    "ea_developer",
    "backtest_analyst",
    "optimization_agent",
    "vps_watch",
    "telegram_ops",
    "risk_guard",
    "codex_mcp_operator",
    "mission_archivist",
)


class RequestError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


class DataIntegrityError(RuntimeError):
    """Raised when a durable JSON store exists but cannot be trusted."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_after(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def clamp_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def contains_potential_secret(value: str) -> bool:
    text = str(value or "")
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def is_sensitive_field_name(value: object) -> bool:
    compact = re.sub(r"[^a-z0-9]", "", str(value or "").lower())
    return bool(compact) and compact not in SENSITIVE_FIELD_METADATA and compact.endswith(SENSITIVE_FIELD_SUFFIXES)


def json_contains_potential_secret(value, depth: int = 0) -> bool:
    if depth > 8:
        return False
    if isinstance(value, str):
        return contains_potential_secret(value)
    if isinstance(value, list):
        return any(json_contains_potential_secret(item, depth + 1) for item in value[:500])
    if isinstance(value, dict):
        return any(
            (is_sensitive_field_name(key) and item is not None)
            or json_contains_potential_secret(item, depth + 1)
            for key, item in list(value.items())[:500]
        )
    return False


def redact_text(value: str, limit: int = 8000) -> str:
    text = str(value or "")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET]", text)
    text = re.sub(r"(?i)\b(?:pid|process[_ .-]?id)\b\s*[:=#-]?\s*\d+\b", "[REDACTED_SECRET]", text)
    text = re.sub(
        r"(?i)\b(?:account[_ .-]?(?:number|no|id|login)|broker[_ .-]?server|terminal[_ .-]?path|process[_ .-]?id|pid)\b\s*[\"']?\s*(?::|=|#|\bis\b)\s*(?:\"[^\"]*\"|'[^']*'|[^,;|\n]+)",
        "[REDACTED_SECRET]",
        text,
    )
    text = re.sub(r"(?i)\b[A-Z]:\\[^,;|\"'\n]+", "[REDACTED_PATH]", text)
    text = re.sub(r"\\\\[^,;|\"'\n]+", "[REDACTED_PATH]", text)
    text = re.sub(r"(?i)(?<!\w)/(?:Users|home|root|var|etc|tmp|opt|srv)/[^,;|\"'\n]+", "[REDACTED_PATH]", text)
    home = str(Path.home())
    if home:
        text = text.replace(home, "%USERPROFILE%")
    return text[:limit]


def sanitize_json_value(value, depth: int = 0, collection_limit: int = 100, string_limit: int = 8000):
    if depth > 6:
        return "[TRUNCATED]"
    if isinstance(value, str):
        return redact_text(value, string_limit)
    if isinstance(value, list):
        return [sanitize_json_value(item, depth + 1, collection_limit, string_limit) for item in value[:collection_limit]]
    if isinstance(value, dict):
        cleaned = {}
        for key, item in list(value.items())[:collection_limit]:
            safe_key = str(key)[:120]
            cleaned[safe_key] = (
                None if item is None else "[REDACTED_SECRET]"
            ) if is_sensitive_field_name(safe_key) else sanitize_json_value(item, depth + 1, collection_limit, string_limit)
        return cleaned
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_text(str(value), 1000)


def is_visual_simulation(payload: dict) -> bool:
    if bool(payload.get("simulation", False)) or str(payload.get("kind") or "").lower() == "autonomy":
        return True
    sample = json.dumps(payload, ensure_ascii=False)[:12000].lower()
    return "autonomous status sync" in sample or "autonomous patrol" in sample


def safe_id(value: str | None, prefix: str = "item") -> str:
    candidate = str(value or "").strip()
    if candidate and SAFE_ID_PATTERN.fullmatch(candidate):
        return candidate
    return f"{prefix}-{int(time.time() * 1000)}-{secrets.token_hex(3)}"


def safe_reference(value: object) -> str | None:
    candidate = str(value or "").strip()
    return candidate if candidate and SAFE_ID_PATTERN.fullmatch(candidate) else None


def safe_codex_artifact_reference(value: object) -> str | None:
    candidate = str(value or "").strip().replace("\\", "/")
    if not candidate or Path(candidate).is_absolute() or ".." in Path(candidate).parts:
        return None
    resolved = (PROJECT_ROOT / Path(candidate)).resolve(strict=False)
    allowed_root = (RUNTIME_DIR / "codex-runs").resolve(strict=False)
    try:
        resolved.relative_to(allowed_root)
    except ValueError:
        return None
    return resolved.relative_to(PROJECT_ROOT.resolve(strict=False)).as_posix()


def payload_digest(*parts: str) -> str:
    joined = "\n".join(str(part or "") for part in parts)
    return hashlib.sha256(joined.encode("utf-8", errors="replace")).hexdigest()


def mission_payload_digest(mission: dict) -> str:
    """Bind one approval to the complete execution-relevant mission packet."""
    execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
    packet = {
        "owner": str(mission.get("owner") or ""),
        "toolId": str(mission.get("toolId") or ""),
        "targetId": str(mission.get("targetId") or ""),
        "detail": str(mission.get("detail") or ""),
        "modelTier": str(mission.get("modelTier") or ""),
        "budget": mission.get("budget") if isinstance(mission.get("budget"), dict) else {},
        "risk": str(mission.get("risk") or ""),
        "reportType": str(mission.get("reportType") or ""),
        "executionAuthorization": {
            "executionMode": str(mission.get("executionMode") or ""),
            "autoEligible": mission.get("autoEligible") is True,
            "autoQueuedAt": str(mission.get("autoQueuedAt") or ""),
            "requiresHumanApproval": mission.get("requiresHumanApproval") is True,
            "schema": str(execution.get("schema") or ""),
            "authorizationId": str(execution.get("authorizationId") or ""),
            "authorizationIssuedAt": str(execution.get("authorizationIssuedAt") or ""),
        },
    }
    canonical = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8", errors="replace")).hexdigest()


def tail_jsonl(path: Path, limit: int = 80, max_bytes: int = 262144) -> list[dict]:
    if not path.exists():
        return []
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes), os.SEEK_SET)
        raw = handle.read().decode("utf-8", errors="replace")
    rows = raw.splitlines()
    if size > max_bytes and rows:
        rows = rows[1:]
    records = []
    for row in rows[-limit:]:
        try:
            item = json.loads(row)
            if isinstance(item, dict):
                records.append(item)
        except json.JSONDecodeError:
            records.append({"type": "log_parse_warning", "detail": "A legacy malformed log line was skipped."})
    return records


def rotate_jsonl_segment(path: Path, max_bytes: int = JSONL_SEGMENT_MAX_BYTES) -> Path | None:
    """Archive a full append-only segment without deleting history."""
    if not path.exists() or path.stat().st_size < max_bytes:
        return None
    if path == MEETING_TRANSCRIPTS_PATH:
        archive_dir = path.parent / "archive"
    else:
        archive_dir = RUNTIME_DIR / "archive" / path.stem
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = archive_dir / f"{path.stem}-{stamp}-{secrets.token_hex(3)}{path.suffix}"
    os.replace(path, destination)
    return destination


def ensure_runtime_dir() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        relative_path = path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path.name
        raise DataIntegrityError(f"JSON integrity check failed for {relative_path}.") from error


def write_json(path: Path, payload, *, keep_backup: bool = False) -> None:
    ensure_runtime_dir()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{threading.get_ident()}.tmp")
    backup = path.with_name(f"{path.name}.bak")
    backup_temporary = path.with_name(f".{path.name}.bak.{threading.get_ident()}.tmp")
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        if keep_backup and path.exists():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                relative_path = path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path.name
                raise DataIntegrityError(
                    f"Refusing to overwrite corrupt JSON store {relative_path}; restore its .bak copy first."
                ) from error
            shutil.copyfile(path, backup_temporary)
            os.replace(backup_temporary, backup)
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
            handle.flush()
            if keep_backup:
                os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        for leftover in (temporary, backup_temporary):
            try:
                leftover.unlink(missing_ok=True)
            except OSError:
                pass


def load_tool_permissions() -> dict:
    return read_json(TOOL_PERMISSION_PATH, {"tools": [], "blocked_everywhere": []})


def load_orchestration_contract() -> dict:
    return read_json(ORCHESTRATION_CONTRACT_PATH, {"modelTiers": {}, "costRateGuard": {}})


def operator_mode_policy() -> dict:
    contract = load_orchestration_contract()
    policy = contract.get("operatorMode") if isinstance(contract.get("operatorMode"), dict) else {}
    return policy


def _operator_mode_default() -> str:
    configured = str(operator_mode_policy().get("defaultMode") or "manual_guarded")
    return configured if configured in {"auto_guarded", "manual_guarded"} else "manual_guarded"


def load_operator_mode_record() -> dict:
    default_mode = _operator_mode_default()
    if not OPERATOR_MODE_PATH.exists():
        return {"mode": default_mode, "updatedAt": SERVER_STARTED_AT, "source": "contract_default"}
    stored = read_json(OPERATOR_MODE_PATH, {})
    if not isinstance(stored, dict):
        raise DataIntegrityError("Operator mode store has an invalid shape.")
    mode = str(stored.get("mode") or "")
    if mode not in {"auto_guarded", "manual_guarded"}:
        raise DataIntegrityError("Operator mode store contains an unsupported mode.")
    return {
        "mode": mode,
        "updatedAt": stored.get("updatedAt") or SERVER_STARTED_AT,
        "source": "runtime_store",
    }


def ensure_operator_mode_store() -> dict:
    record = load_operator_mode_record()
    if OPERATOR_MODE_PATH.exists():
        return record
    persisted = {
        "version": "operator-mode-store-v1",
        "mode": record["mode"],
        "updatedAt": utc_now(),
        "source": "contract_default",
    }
    write_json(OPERATOR_MODE_PATH, persisted)
    return persisted


def mission_worker_read_model() -> dict:
    with MISSION_WORKER_LOCK:
        state = dict(MISSION_WORKER_STATE)
    try:
        missions = load_missions()
    except (DataIntegrityError, OSError):
        missions = []
    queued = sum(
        1
        for mission in missions
        if mission.get("status") == "queued"
        and mission.get("autoEligible") is True
        and mission.get("executionMode") == "auto_guarded"
        and isinstance(mission.get("execution"), dict)
        and mission["execution"].get("schema") == "auto-guarded-execution-v1"
        and mission["execution"].get("dispatchState") in {"queued", "deferred"}
    )
    return {
        "status": redact_text(str(state.get("status") or "stopped"), 40),
        "workerId": safe_reference(state.get("workerId")),
        "currentMissionId": safe_reference(state.get("currentMissionId")),
        "startedAt": state.get("startedAt"),
        "heartbeatAt": state.get("heartbeatAt"),
        "queued": queued,
        "watchdogAlive": bool(
            MISSION_WORKER_WATCHDOG_THREAD
            and MISSION_WORKER_WATCHDOG_THREAD.is_alive()
        ),
        "lastError": redact_text(str(state.get("lastError") or ""), 240) or None,
    }


def operator_mode_read_model() -> dict:
    policy = operator_mode_policy()
    record = load_operator_mode_record()
    mode = str(record.get("mode") or _operator_mode_default())
    auto_tools = [
        value
        for value in (safe_reference(item) for item in (policy.get("autoEligibleTools") or ["codex_cli_task"]))
        if value
    ]
    always_gated = [
        redact_text(str(item), 120)
        for item in (policy.get("alwaysRequireHumanApprovalFor") or [])
        if str(item).strip()
    ]
    return {
        "mode": mode,
        "labelTh": "ทำงานอัตโนมัติแบบมีระบบป้องกัน" if mode == "auto_guarded" else "ยืนยันงานจริงด้วยตนเอง",
        "autoExecute": mode == "auto_guarded",
        "guardrails": {
            "autoEligibleTools": auto_tools,
            "maxRisk": redact_text(str(policy.get("maxRisk") or "medium"), 20),
            "alwaysRequireHumanApprovalFor": always_gated,
        },
        "worker": mission_worker_read_model(),
        "updatedAt": record.get("updatedAt") or SERVER_STARTED_AT,
    }


def set_operator_mode(payload: dict) -> dict:
    if not isinstance(payload, dict) or set(payload) != {"mode"}:
        return {
            "ok": False,
            "kind": "invalid_operator_mode_request",
            "message": "Operator mode accepts only the mode field.",
            "_httpStatus": 422,
        }
    mode = str(payload.get("mode") or "")
    if mode not in {"auto_guarded", "manual_guarded"}:
        return {
            "ok": False,
            "kind": "invalid_operator_mode",
            "message": "Mode must be auto_guarded or manual_guarded.",
            "_httpStatus": 422,
        }
    previous = load_operator_mode_record()
    changed_at = utc_now()
    write_json(
        OPERATOR_MODE_PATH,
        {
            "version": "operator-mode-store-v1",
            "mode": mode,
            "updatedAt": changed_at,
            "source": "local_operator_api",
        },
        keep_backup=OPERATOR_MODE_PATH.exists(),
    )
    append_audit({
        "type": "operator_mode.changed",
        "previousMode": previous.get("mode"),
        "mode": mode,
        "autoExecute": mode == "auto_guarded",
        "source": "local_operator_api",
    })
    MISSION_WORKER_WAKE.set()
    return {"ok": True, "kind": "operator_mode", **operator_mode_read_model()}


def _high_impact_reasons(tool_id: str, detail: str, risk: str) -> list[str]:
    policy = operator_mode_policy()
    reasons: list[str] = []
    gated_tools = {
        str(item)
        for item in (policy.get("alwaysRequireHumanApprovalTools") or [])
        if str(item).strip()
    }
    if tool_id in gated_tools:
        reasons.append(f"tool:{tool_id}")
    blocked_keywords = [
        str(item).strip().lower()
        for item in (policy.get("blockedIntentKeywords") or [])
        if str(item).strip()
    ]
    lower_detail = str(detail or "").lower()
    for keyword in blocked_keywords:
        if keyword_matches(lower_detail, keyword):
            reasons.append(f"intent:{keyword}")
    for label, pattern in HIGH_IMPACT_INTENT_PATTERNS:
        if pattern.search(str(detail or "")):
            reasons.append(f"intent_pattern:{label}")
    if str(risk or "").lower() == "high":
        reasons.append("risk:high")
    if contains_potential_secret(detail):
        reasons.append("potential_secret")
    return list(dict.fromkeys(reasons))


def auto_guarded_eligibility(mission: dict, *, require_operator_mode: bool = True) -> dict:
    policy = operator_mode_policy()
    operator = load_operator_mode_record()
    tool_id = str(mission.get("toolId") or "")
    agent_id = str(mission.get("owner") or mission.get("agentId") or "")
    risk = str(mission.get("risk") or "medium").lower()
    detail = str(mission.get("detail") or mission.get("prompt") or "")
    tool_policy = get_tool_policy(tool_id) or {}
    reasons: list[str] = []
    if require_operator_mode and operator.get("mode") != "auto_guarded":
        reasons.append("operator_mode_manual")
    allowlist = {
        str(item)
        for item in (policy.get("autoEligibleTools") or ["codex_cli_task"])
        if str(item).strip()
    }
    if tool_id not in allowlist:
        reasons.append("tool_not_allowlisted")
    if not bool(tool_policy.get("autoRunnable", False)):
        reasons.append("tool_contract_auto_run_disabled")
    max_risk = str(policy.get("maxRisk") or "medium").lower()
    risk_order = {"low": 0, "medium": 1, "high": 2}
    if risk_order.get(risk, 2) > risk_order.get(max_risk, 1):
        reasons.append("risk_above_auto_limit")
    allowed_modes = {
        str(item)
        for item in (policy.get("allowedToolModes") or ["read_only_diagnostic"])
        if str(item).strip()
    }
    if str(tool_policy.get("defaultMode") or "") not in allowed_modes:
        reasons.append("tool_mode_not_allowlisted")
    adapter_status = str(tool_policy.get("adapterStatus") or "unimplemented").lower()
    if not adapter_status.startswith("implemented"):
        reasons.append("adapter_not_implemented")
    if not bool(tool_policy.get("realExecutionAvailable", False)):
        reasons.append("real_execution_unavailable")
    permission = evaluate_tool_permission(agent_id, tool_id)
    if not permission.get("allowed"):
        reasons.append(str(permission.get("reason") or "permission_denied"))
    reasons.extend(_high_impact_reasons(tool_id, detail, risk))
    return {
        "eligible": not reasons,
        "mode": "auto_guarded" if not reasons else "manual_guarded",
        "reasons": list(dict.fromkeys(reasons)),
    }


def backend_auto_guard_review(mission: dict, approval: dict) -> tuple[str, str]:
    """Approve only a digest-bound, allowlisted local mission in operator auto mode."""
    expected_digest = str(approval.get("payloadDigest") or "")
    actual_digest = mission_payload_digest(mission)
    eligibility = auto_guarded_eligibility(mission, require_operator_mode=True)
    if not expected_digest or not secrets.compare_digest(expected_digest, actual_digest):
        decision, reason = "rejected", "mission_digest_mismatch"
    elif not eligibility.get("eligible"):
        decision = "rejected"
        reason = str((eligibility.get("reasons") or ["auto_guard_policy_denied"])[0])
    else:
        decision, reason = "approved", "backend_auto_review_allowlisted_local_workspace"
    reviewed_at = utc_now()
    decisions = [
        item
        for item in (approval.get("decisions") or [])
        if isinstance(item, dict) and item.get("actorId") != "risk_guard"
    ]
    decisions.append({
        "actorId": "risk_guard",
        "actorProvenance": "backend_auto_review",
        "decision": decision,
        "note": reason,
        "time": reviewed_at,
        "payloadDigest": expected_digest,
        "ruleVersion": "auto-guard-v1",
    })
    approval["decisions"] = decisions
    mission["riskGuardReview"] = {
        "decision": decision,
        "reason": reason,
        "ruleVersion": "auto-guard-v1",
        "payloadDigest": expected_digest,
        "reviewedAt": reviewed_at,
    }
    append_audit({
        "type": "mission.auto_guard_review",
        "missionId": mission.get("id"),
        "approvalId": approval.get("id"),
        "actorId": "risk_guard",
        "actorProvenance": "backend_auto_review",
        "decision": decision,
        "reason": reason,
        "payloadDigest": expected_digest,
    })
    return decision, reason


def load_report_contract() -> dict:
    return read_json(REPORT_CONTRACT_PATH, {"report_targets": {}})


def load_agent_contracts() -> list[dict]:
    payload = read_json(AGENTS_PATH, {"agents": []})
    return [item for item in payload.get("agents", []) if isinstance(item, dict)]


def get_tool_policy(tool_id: str) -> dict | None:
    tools = load_tool_permissions().get("tools", [])
    return next((item for item in tools if isinstance(item, dict) and item.get("id") == tool_id), None)


def evaluate_tool_permission(agent_id: str, tool_id: str) -> dict:
    agent_ids = {str(item.get("id")) for item in load_agent_contracts()}
    if agent_id not in agent_ids:
        return {"allowed": False, "reason": "unknown_agent", "message": "Unknown agent id."}
    policy = get_tool_policy(tool_id)
    if not policy:
        return {"allowed": False, "reason": "unknown_tool", "message": "Unknown tools are denied by default."}
    allowed_agents = policy.get("allowedAgents") if isinstance(policy.get("allowedAgents"), list) else []
    if agent_id not in allowed_agents:
        return {"allowed": False, "reason": "agent_not_allowed", "message": f"Agent {agent_id} is not permitted to use {tool_id}."}
    return {"allowed": True, "reason": "allowed", "policy": policy}


def role_default_model_tier(agent_id: str) -> str:
    if agent_id in {"manager", "ceo"}:
        return "manager_quality"
    if agent_id == "risk_guard":
        return "risk_quality"
    if agent_id in {"ea_developer", "backtest_analyst", "optimization_agent"}:
        return "specialist_balanced"
    return "specialist_fast"


def resolve_model_tier(
    agent_id: str,
    requested_tier: str | None = None,
    tool_policy: dict | None = None,
    allow_requested: bool = False,
) -> tuple[str, dict]:
    contract = load_orchestration_contract()
    tiers = contract.get("modelTiers") if isinstance(contract.get("modelTiers"), dict) else {}
    policy_tier = str((tool_policy or {}).get("modelTier") or "")
    tier_id = policy_tier if policy_tier and policy_tier != "role_default" else role_default_model_tier(agent_id)
    if allow_requested and requested_tier and requested_tier in tiers:
        tier_id = requested_tier
    if tier_id not in tiers:
        tier_id = "specialist_fast" if "specialist_fast" in tiers else next(iter(tiers), "specialist_fast")
    tier = tiers.get(tier_id) if isinstance(tiers.get(tier_id), dict) else {}
    return tier_id, tier


def resolve_budget(
    payload: dict,
    agent_id: str,
    tool_policy: dict | None = None,
    allow_model_override: bool = False,
    allow_budget_override: bool = False,
) -> tuple[str, dict]:
    tier_id, tier = resolve_model_tier(agent_id, payload.get("modelTier"), tool_policy, allow_model_override)
    contract = load_orchestration_contract()
    guard = contract.get("costRateGuard") if isinstance(contract.get("costRateGuard"), dict) else {}
    hard_timeout = guard.get("hardTimeoutSeconds") if isinstance(guard.get("hardTimeoutSeconds"), dict) else {}
    minimum = clamp_int(hard_timeout.get("min"), 15, 1, 600)
    maximum = clamp_int(hard_timeout.get("max"), 600, minimum, 3600)
    default_timeout = clamp_int(tier.get("maxSeconds"), 120, minimum, maximum)
    hard_output = clamp_int(guard.get("hardOutputChars"), 20000, 1000, 100000)
    default_output = clamp_int(tier.get("maxOutputChars"), 7000, 1000, hard_output)
    budget_payload = payload.get("budget") if allow_budget_override and isinstance(payload.get("budget"), dict) else {}
    requested_timeout = payload.get("timeout") if allow_budget_override else None
    return tier_id, {
        "timeoutSeconds": clamp_int(requested_timeout if requested_timeout is not None else budget_payload.get("timeoutSeconds"), default_timeout, minimum, maximum),
        "outputLimitChars": clamp_int(budget_payload.get("outputLimitChars"), default_output, 1000, hard_output),
        "maxRuns": 1,
    }


def check_rate_limit(key: str, max_per_hour: int, cooldown_seconds: int = 0, consume: bool = True) -> tuple[bool, int]:
    now = time.time()
    with RATE_LIMIT_LOCK:
        rows = [stamp for stamp in RATE_LIMIT_STATE.get(key, []) if now - stamp < 3600]
        if rows and cooldown_seconds > 0 and now - rows[-1] < cooldown_seconds:
            retry_after = max(1, int(cooldown_seconds - (now - rows[-1]) + 0.999))
            RATE_LIMIT_STATE[key] = rows
            return False, retry_after
        if len(rows) >= max(1, max_per_hour):
            retry_after = max(1, int(3600 - (now - rows[0]) + 0.999))
            RATE_LIMIT_STATE[key] = rows
            return False, retry_after
        if consume:
            rows.append(now)
            RATE_LIMIT_STATE[key] = rows
        elif rows:
            RATE_LIMIT_STATE[key] = rows
        else:
            RATE_LIMIT_STATE.pop(key, None)
    return True, 0


def ensure_memory_dir() -> None:
    for folder in [
        MEMORY_DIR,
        MEMORY_DIR / "agent-notes",
        MEMORY_DIR / "meetings",
        MEMORY_DIR / "summaries",
        MEMORY_DIR / "reports",
        MEMORY_DIR / "artifacts",
        MEMORY_DIR / "screenshots",
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def load_memory_index() -> dict:
    ensure_memory_dir()
    data = read_json(MEMORY_INDEX_PATH, {"version": "memory-index-v001", "items": []})
    if not isinstance(data, dict):
        return {"version": "memory-index-v001", "items": []}
    data.setdefault("version", "memory-index-v001")
    data.setdefault("items", [])
    if not isinstance(data["items"], list):
        data["items"] = []
    return data


def save_memory_index(index: dict) -> None:
    ensure_memory_dir()
    index["updatedAt"] = utc_now()
    with MEMORY_INDEX_LOCK:
        write_json(MEMORY_INDEX_PATH, index, keep_backup=True)


def memory_item_text(item: dict) -> str:
    fields = [
        item.get("id"),
        item.get("kind"),
        item.get("title"),
        item.get("summary"),
        item.get("sourcePath"),
        " ".join(item.get("agents") or []),
        " ".join(item.get("tags") or []),
    ]
    return " ".join(str(field or "") for field in fields).lower()


def search_memory_items(query: str = "", limit: int = 12) -> list[dict]:
    index = load_memory_index()
    items = [item for item in index.get("items", []) if isinstance(item, dict)]
    text = " ".join(str(query or "").lower().split())
    if not text:
        return items[:limit]
    tokens = [token for token in text.replace("/", " ").replace("_", " ").split() if token]

    scored: list[tuple[int, dict]] = []
    for item in items:
        haystack = memory_item_text(item)
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda row: (row[0], row[1].get("updatedAt") or row[1].get("createdAt") or ""), reverse=True)
    return [item for _, item in scored[:limit]]


def upsert_memory_item(payload: dict) -> dict:
    ensure_memory_dir()
    with MEMORY_INDEX_LOCK:
        index = load_memory_index()
        item_id = str(payload.get("id") or f"mem-{int(time.time() * 1000)}")
        existing_items = [item for item in index.get("items", []) if isinstance(item, dict)]
        previous = next((item for item in existing_items if item.get("id") == item_id), {})
        raw_summary = str(payload.get("summary") or previous.get("summary") or "")
        secret_redacted = json_contains_potential_secret(payload)
        item = {
            **previous,
            "id": item_id,
            "kind": str(payload.get("kind") or previous.get("kind") or "note"),
            "title": redact_text(str(payload.get("title") or previous.get("title") or "Untitled Memory"), 160),
            "summary": redact_text(raw_summary, 2400),
            "sourcePath": redact_text(str(payload.get("sourcePath") or previous.get("sourcePath") or ""), 500),
            "agents": sanitize_json_value(payload.get("agents") if isinstance(payload.get("agents"), list) else previous.get("agents", [])),
            "tags": sanitize_json_value(payload.get("tags") if isinstance(payload.get("tags"), list) else previous.get("tags", [])),
            "createdAt": previous.get("createdAt") or utc_now(),
            "updatedAt": utc_now(),
            "safety": {
                "containsSecret": False,
                "secretRedacted": secret_redacted,
                "approvalRequired": False,
                "publicShareable": False,
            },
        }
        index["items"] = [item] + [row for row in existing_items if row.get("id") != item_id]
        save_memory_index(index)
    append_audit({"type": "memory.upsert", "memoryId": item["id"], "kind": item["kind"], "secretRedacted": secret_redacted})
    return item


def load_meeting_records(limit: int = 80) -> list[dict]:
    ensure_memory_dir()
    return tail_jsonl(MEETING_TRANSCRIPTS_PATH, limit=limit, max_bytes=524288)[::-1]


def append_meeting_record(payload: dict, kind: str = "meeting") -> dict:
    ensure_memory_dir()
    participants = payload.get("participants") if isinstance(payload.get("participants"), list) else []
    messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    record = {
        "id": str(payload.get("id") or f"meeting-{int(time.time() * 1000)}"),
        "kind": kind,
        "time": utc_now(),
        "title": redact_text(str(payload.get("title") or payload.get("agenda") or "Agent Meeting"), 160),
        "agenda": redact_text(str(payload.get("agenda") or ""), 1200),
        "participants": [item for item in (safe_reference(value) for value in participants[:20]) if item],
        "summary": redact_text(str(payload.get("summary") or payload.get("message") or ""), 2400),
        "messages": sanitize_json_value(messages[:80]),
        "source": redact_text(str(payload.get("source") or "frontend"), 160),
        "simulation": bool(payload.get("simulation", False)),
        "linkedMissionId": safe_reference(payload.get("linkedMissionId")),
        "linkedPropId": safe_reference(payload.get("linkedPropId")),
    }
    with MEETING_TRANSCRIPTS_LOCK:
        rotate_jsonl_segment(MEETING_TRANSCRIPTS_PATH)
        with MEETING_TRANSCRIPTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    append_audit({"type": "meeting.recorded", "meetingId": record["id"], "kind": kind})
    return record


def find_room_prop(prop_id: str) -> dict | None:
    room = read_json(ROOM_PATH, {})
    candidates = []
    if isinstance(room, dict):
        candidates.extend(room.get("props") or [])
        candidates.extend(room.get("hotspots") or [])
    return next((item for item in candidates if item.get("id") == prop_id), None)


def load_property_role_map() -> dict:
    return read_json(PROPERTY_ROLE_MAP_PATH, {"properties": {}, "routingRules": []})


def load_dashboard_connection_contract() -> dict:
    return read_json(DASHBOARD_CONNECTION_PATH, {"profiles": {}, "statusVocabulary": []})


def find_dashboard_connection_profile(prop_id: str) -> dict:
    role = find_property_role(prop_id)
    profile_id = str(role.get("connectionProfileId") or prop_id)
    contract = load_dashboard_connection_contract()
    profiles = contract.get("profiles") if isinstance(contract.get("profiles"), dict) else {}
    profile = profiles.get(profile_id) if isinstance(profiles, dict) else None
    return profile if isinstance(profile, dict) else {}


def keyword_matches(text: str, token: str) -> bool:
    token = str(token or "").strip().lower()
    if not token:
        return False
    if re.fullmatch(r"[a-z0-9_]+", token):
        return re.search(rf"(?<![a-z0-9_]){re.escape(token)}(?![a-z0-9_])", text) is not None
    return token in text


def find_property_role(prop_id: str) -> dict:
    role_map = load_property_role_map()
    properties = role_map.get("properties") if isinstance(role_map, dict) else {}
    role = properties.get(prop_id) if isinstance(properties, dict) else None
    return role if isinstance(role, dict) else {}


def routing_keywords_for_prop(prop_id: str) -> list[str]:
    role_map = load_property_role_map()
    keywords: list[str] = []
    for rule in role_map.get("routingRules", []):
        if isinstance(rule, dict) and rule.get("targetPropId") == prop_id:
            keywords.extend(str(item) for item in (rule.get("keywords") or []) if str(item).strip())
    return keywords


def load_runtime_reports(limit: int = 120) -> list[dict]:
    ensure_runtime_dir()
    reports = []
    for path in sorted(RUNTIME_REPORTS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
        payload = read_json(path, None)
        if isinstance(payload, dict):
            reports.append(payload)
    return reports


def create_report(payload: dict) -> dict:
    ensure_runtime_dir()
    secret_redacted = json_contains_potential_secret(payload)
    report_id = safe_id(payload.get("id"), "report")
    report_path = RUNTIME_REPORTS_DIR / f"{report_id}.json"
    existing = read_json(report_path, {}) if report_path.exists() else {}
    now = utc_now()
    report = {
        "id": report_id,
        "type": str(payload.get("type") or "prop_report"),
        "title": redact_text(str(payload.get("title") or "Agent Report"), 160),
        "summary": redact_text(str(payload.get("summary") or ""), 8000),
        "ownerAgentId": str(payload.get("ownerAgentId") or "manager"),
        "linkedMissionId": payload.get("linkedMissionId"),
        "linkedPropId": payload.get("linkedPropId"),
        "status": str(payload.get("status") or "ready"),
        "findings": sanitize_json_value(payload.get("findings") if isinstance(payload.get("findings"), list) else []),
        "metrics": sanitize_json_value(payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}),
        "risks": sanitize_json_value(payload.get("risks") if isinstance(payload.get("risks"), list) else []),
        "nextActions": sanitize_json_value(payload.get("nextActions") if isinstance(payload.get("nextActions"), list) else []),
        "artifacts": sanitize_json_value(payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []),
        "safety": {
            "containsSecret": False,
            "secretRedacted": secret_redacted,
            "approvalRequired": bool((payload.get("safety") or {}).get("approvalRequired", False)),
            "publicShareable": bool((payload.get("safety") or {}).get("publicShareable", False)),
        },
        "createdAt": existing.get("createdAt") or now,
        "updatedAt": now,
    }
    with REPORTS_LOCK:
        write_json(report_path, report)
    append_audit({"type": "report.updated" if existing else "report.created", "reportId": report_id, "missionId": report.get("linkedMissionId"), "propId": report.get("linkedPropId")})
    return report


def report_type_for_prop(prop_id: str) -> str:
    role = find_property_role(prop_id)
    return str(role.get("reportType") or "prop_report")


def mission_read_model_item(mission: dict) -> dict:
    """Return a frontend-safe mission card without internal approval digests or paths."""
    approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
    execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
    delegation = mission.get("delegation") if isinstance(mission.get("delegation"), dict) else {}
    subtask_ids = mission.get("subtaskIds") if isinstance(mission.get("subtaskIds"), list) else []
    report_ids = mission.get("reportIds") if isinstance(mission.get("reportIds"), list) else []
    required_actors = approval.get("requiredActors") if isinstance(approval.get("requiredActors"), list) else []
    return {
        "id": redact_text(str(mission.get("id") or ""), 120),
        "title": redact_text(str(mission.get("title") or "Untitled mission"), 160),
        "detail": redact_text(str(mission.get("detail") or ""), 8000),
        "owner": redact_text(str(mission.get("owner") or "manager"), 120),
        "requester": redact_text(str(mission.get("requester") or "human"), 120),
        "parentMissionId": safe_reference(mission.get("parentMissionId")),
        "subtaskIds": [item for item in (safe_reference(value) for value in subtask_ids[:100]) if item],
        "toolId": redact_text(str(mission.get("toolId") or ""), 120),
        "targetId": redact_text(str(mission.get("targetId") or MISSION_STRATEGY_TABLE_PROP_ID), 120),
        "status": redact_text(str(mission.get("status") or "unknown"), 40),
        "executionMode": redact_text(str(mission.get("executionMode") or "manual_guarded"), 40),
        "autoEligible": bool(mission.get("autoEligible", False)),
        "dispatchState": redact_text(str(execution.get("dispatchState") or ""), 40) or None,
        "nextAttemptAt": execution.get("nextAttemptAt"),
        "runnerStatus": redact_text(str(mission.get("runnerStatus") or ""), 80) or None,
        "requiresHumanApproval": bool(
            mission.get("requiresHumanApproval", approval.get("required", False))
        ),
        "startedAt": execution.get("startedAt") or mission.get("startedAt"),
        "heartbeatAt": execution.get("heartbeatAt") or mission.get("heartbeatAt"),
        "archivedFromStatus": redact_text(str(mission.get("archivedFromStatus") or ""), 40) or None,
        "archivedSuccessful": bool(mission.get("archivedSuccessful", False)),
        "phase": redact_text(str(mission.get("phase") or ""), 80),
        "risk": redact_text(str(mission.get("risk") or "low"), 40),
        "modelTier": redact_text(str(mission.get("modelTier") or ""), 80),
        "reportType": redact_text(str(mission.get("reportType") or ""), 120),
        "budget": sanitize_json_value(mission.get("budget") if isinstance(mission.get("budget"), dict) else {}),
        "approval": {
            "required": bool(approval.get("required", False)),
            "state": redact_text(str(approval.get("state") or "not_required"), 40),
            "requiredActors": [redact_text(str(value), 80) for value in required_actors[:20]],
            "expiresAt": approval.get("expiresAt"),
            "consumedAt": approval.get("consumedAt"),
        },
        "readyToExecute": (
            str(mission.get("status") or "") == "waiting_approval"
            and str(approval.get("state") or "") == "approved"
        ),
        "delegation": {
            "state": redact_text(str(delegation.get("state") or ""), 40),
            "mode": redact_text(str(delegation.get("mode") or ""), 120),
            "subtaskCount": clamp_int(delegation.get("subtaskCount"), 0, 0, 100000),
            "subtaskStatusCounts": sanitize_json_value(delegation.get("subtaskStatusCounts") if isinstance(delegation.get("subtaskStatusCounts"), dict) else {}),
            "summaryTargetId": safe_reference(delegation.get("summaryTargetId")),
            "realToolExecuted": bool(delegation.get("realToolExecuted", False)),
            "delegatedAt": delegation.get("delegatedAt"),
            "lastAggregatedAt": delegation.get("lastAggregatedAt"),
            "finalReportId": safe_reference(delegation.get("finalReportId")),
        },
        "result": redact_text(str(mission.get("result") or ""), 8000),
        "reportIds": [item for item in (safe_reference(value) for value in report_ids[:100]) if item],
        "attemptCount": clamp_int(mission.get("attemptCount"), 0, 0, 100000),
        "createdAt": mission.get("createdAt"),
        "updatedAt": mission.get("updatedAt"),
        "completedAt": mission.get("completedAt"),
    }


def report_read_model_item(report: dict) -> dict:
    """Return report metadata and findings without local artifact paths."""
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    return {
        "id": safe_reference(report.get("id")),
        "type": redact_text(str(report.get("type") or "prop_report"), 120),
        "title": redact_text(str(report.get("title") or "Agent Report"), 160),
        "summary": redact_text(str(report.get("summary") or ""), 8000),
        "ownerAgentId": safe_reference(report.get("ownerAgentId")),
        "linkedMissionId": safe_reference(report.get("linkedMissionId")),
        "linkedPropId": safe_reference(report.get("linkedPropId")),
        "status": redact_text(str(report.get("status") or "ready"), 40),
        "findings": sanitize_json_value(report.get("findings") if isinstance(report.get("findings"), list) else []),
        "metrics": sanitize_json_value(report.get("metrics") if isinstance(report.get("metrics"), dict) else {}),
        "risks": sanitize_json_value(report.get("risks") if isinstance(report.get("risks"), list) else []),
        "nextActions": sanitize_json_value(report.get("nextActions") if isinstance(report.get("nextActions"), list) else []),
        "artifactCount": sum(1 for item in artifacts if item),
        "safety": sanitize_json_value(report.get("safety") if isinstance(report.get("safety"), dict) else {}),
        "createdAt": report.get("createdAt"),
        "updatedAt": report.get("updatedAt"),
    }


def frontend_api_result(payload: dict) -> dict:
    """Project mission/report objects before any API response reaches the frontend."""
    result = dict(payload)
    for key in ("mission", "parent"):
        if isinstance(result.get(key), dict):
            result[key] = mission_read_model_item(result[key])
    if isinstance(result.get("subtasks"), list):
        result["subtasks"] = [mission_read_model_item(item) for item in result["subtasks"] if isinstance(item, dict)]
    if isinstance(result.get("report"), dict):
        result["report"] = report_read_model_item(result["report"])
    if isinstance(result.get("reports"), list):
        result["reports"] = [report_read_model_item(item) for item in result["reports"] if isinstance(item, dict)]
    if "artifacts" in result:
        artifacts = result.pop("artifacts")
        if isinstance(artifacts, dict):
            count = sum(1 for value in artifacts.values() if value)
        elif isinstance(artifacts, list):
            count = sum(1 for value in artifacts if value)
        else:
            count = 1 if artifacts else 0
        result["artifactSummary"] = {"available": count > 0, "count": count}
    return result


def summarize_missions(missions: list[dict]) -> dict:
    counts = {status: 0 for status in MISSION_STATUS_ORDER}
    for mission in missions:
        status = str(mission.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return {
        "total": len(missions),
        "byStatus": counts,
        "active": sum(counts.get(status, 0) for status in ("queued", "running", "waiting_approval")),
        "terminal": sum(counts.get(status, 0) for status in ("completed", "failed", "archived")),
        "attentionRequired": sum(counts.get(status, 0) for status in ("waiting_approval", "blocked", "failed")),
        "rootMissions": sum(1 for mission in missions if not mission.get("parentMissionId")),
        "subtasks": sum(1 for mission in missions if mission.get("parentMissionId")),
    }


def summarize_reports(reports: list[dict]) -> dict:
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for report in reports:
        status_name = redact_text(str(report.get("status") or "unknown"), 40)
        report_type = redact_text(str(report.get("type") or "prop_report"), 120)
        by_status[status_name] = by_status.get(status_name, 0) + 1
        by_type[report_type] = by_type.get(report_type, 0) + 1
    return {
        "total": len(reports),
        "byStatus": by_status,
        "byType": by_type,
    }


def prop_report(prop_id: str) -> dict:
    prop = find_room_prop(prop_id) or {"id": prop_id, "label": prop_id, "summary": "No room contract entry found."}
    property_role = find_property_role(prop_id)
    label = str(prop.get("label") or prop_id)
    keywords = routing_keywords_for_prop(prop_id)
    target_text = " ".join([prop_id, label, str(property_role.get("functionName") or ""), *keywords]).lower()
    all_missions = load_missions()
    is_global_mission_view = prop_id == MISSION_STRATEGY_TABLE_PROP_ID
    if is_global_mission_view:
        # Mission Strategy Table is the deliberate global exception: it shows
        # every root mission and specialist subtask, regardless of target prop.
        routed_missions = all_missions
        related_missions = [mission_read_model_item(mission) for mission in routed_missions]
    else:
        # Every other prop remains strictly routed to its own work surface.
        routed_missions = [
            mission for mission in all_missions
            if prop_id == mission.get("targetId")
            or prop_id == mission.get("linkedPropId")
            or (not mission.get("targetId") and any(keyword_matches(f"{mission.get('title', '')} {mission.get('detail', '')}".lower(), token) for token in keywords))
        ][:8]
        related_missions = [mission_read_model_item(mission) for mission in routed_missions]
    related_events = [
        event for event in load_agent_events(limit=120)
        if prop_id == event.get("targetId")
        or prop_id in str(event.get("detail") or "").lower()
        or any(keyword_matches(f"{event.get('title', '')} {event.get('detail', '')}".lower(), token) for token in keywords)
    ][:8]
    all_reports = load_runtime_reports(limit=120)
    summary_source_prop_ids: set[str] = set()
    if is_global_mission_view:
        connection_contract = load_dashboard_connection_contract()
        profiles = connection_contract.get("profiles") if isinstance(connection_contract.get("profiles"), dict) else {}
        summary_source_prop_ids = {
            str(profile_id)
            for profile_id, profile in profiles.items()
            if isinstance(profile, dict)
            and isinstance(profile.get("reportRoute"), dict)
            and profile["reportRoute"].get("summaryTargetPropId") == prop_id
        }
        candidate_reports = [
            report for report in all_reports
            if report.get("linkedPropId") == prop_id
            or report.get("linkedPropId") in summary_source_prop_ids
        ]
    else:
        candidate_reports = [report for report in all_reports if prop_id == report.get("linkedPropId")][:8]

    routed_reports = []
    seen_report_ids: set[str] = set()
    for index, report in enumerate(candidate_reports):
        report_id = safe_reference(report.get("id")) or f"anonymous-{index}"
        if report_id in seen_report_ids:
            continue
        seen_report_ids.add(report_id)
        routed_reports.append(report)
    related_reports = [report_read_model_item(report) for report in routed_reports]
    related_mission_ids = {str(mission.get("id") or "") for mission in routed_missions}
    related_owner_ids = {str(mission.get("owner") or "") for mission in routed_missions}
    meetings = load_meeting_records(limit=120)
    if is_global_mission_view:
        related_meetings = meetings[:8]
    else:
        related_meetings = [
            meeting for meeting in meetings
            if meeting.get("linkedPropId") == prop_id
            or meeting.get("linkedMissionId") in related_mission_ids
            or bool(related_owner_ids.intersection(set(meeting.get("participants") or [])))
            or any(
                keyword_matches(
                    f"{meeting.get('title', '')} {meeting.get('agenda', '')} {meeting.get('summary', '')}".lower(),
                    token,
                )
                for token in keywords
            )
        ][:8]
    memory_items = search_memory_items(target_text, limit=6)
    live_bridge_status = bridge_status()
    registry = capability_registry(live_bridge_status)
    dashboard_profile = find_dashboard_connection_profile(prop_id)
    filtered_capabilities = [
        item for item in registry.get("capabilities", [])
        if prop_id in (item.get("linkedPropIds") or [])
    ]
    response = {
        "prop": prop,
        "propertyRole": property_role,
        "missions": related_missions,
        "events": related_events,
        "reports": related_reports,
        "meetings": sanitize_json_value(related_meetings),
        "memory": memory_items,
        "capabilities": filtered_capabilities,
        "capabilitySummary": {
            "total": len(filtered_capabilities),
            "runtimeReady": sum(1 for item in filtered_capabilities if item.get("runtimeReady")),
            "approvalGated": sum(1 for item in filtered_capabilities if item.get("approvalRequired")),
            "realExecutionAvailable": sum(1 for item in filtered_capabilities if item.get("realExecutionAvailable")),
        },
        "bridge": registry["bridge"],
        "dashboardProfile": {
            "moduleNameTh": redact_text(str(dashboard_profile.get("moduleNameTh") or label), 160),
            "availability": sanitize_json_value(dashboard_profile.get("availability") if isinstance(dashboard_profile.get("availability"), dict) else {}),
            "codexUsage": sanitize_json_value(dashboard_profile.get("codexUsage") if isinstance(dashboard_profile.get("codexUsage"), dict) else {}),
            "reportRoute": sanitize_json_value(dashboard_profile.get("reportRoute") if isinstance(dashboard_profile.get("reportRoute"), dict) else {}),
        } if dashboard_profile else {},
        "connectionChecklist": dashboard_connection_checklist(prop_id, bridge=live_bridge_status) if dashboard_profile else {},
        "updatedAt": utc_now(),
    }
    if is_global_mission_view:
        response.update({
            "missionScope": "global_all_missions",
            "missionSummary": summarize_missions(all_missions),
            "reportScope": "dashboard_summaries",
            "reportSummary": summarize_reports(routed_reports),
            "summarySourcePropIds": sorted(summary_source_prop_ids),
            "readModel": "mission_strategy_table_v1",
        })
    return response


def append_audit(event: dict) -> None:
    ensure_runtime_dir()
    record = {
        "time": utc_now(),
        **sanitize_json_value(event),
    }
    with AUDIT_LOCK:
        rotate_jsonl_segment(AUDIT_PATH)
        with AUDIT_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _agent_chat_transcript_path() -> Path:
    return RUNTIME_DIR / AGENT_CHAT_TRANSCRIPT_FILENAME


def _agent_chat_result_path(agent_id: str, session_id: str, idempotency_key: str) -> Path:
    digest = payload_digest(agent_id, session_id, idempotency_key)
    return RUNTIME_DIR / AGENT_CHAT_RESULTS_DIRNAME / f"{digest}.json"


def _agent_chat_usage_read_model(value: object, replay: bool = False) -> dict:
    source = value if isinstance(value, dict) else {}
    quota_consumption = str(source.get("quotaConsumptionStatus") or "none")
    if quota_consumption not in {"none", "possible", "confirmed"}:
        quota_consumption = "none"
    if replay:
        quota_consumption = "none"
    return {
        "durationMs": clamp_int(source.get("durationMs"), 0, 0, 3_600_000),
        "outputChars": clamp_int(source.get("outputChars"), 0, 0, 5000),
        "timeoutSeconds": clamp_int(source.get("timeoutSeconds"), 120, 15, 180),
        "outputLimitChars": clamp_int(source.get("outputLimitChars"), 5000, 1000, 5000),
        "contextTurns": clamp_int(source.get("contextTurns"), 0, 0, 16),
        "secretRedacted": bool(source.get("secretRedacted", False)),
        "idempotentReplay": replay,
        "quotaConsumptionStatus": quota_consumption,
    }


def _agent_chat_rate_limit_read_model(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    primary = source.get("primary") if isinstance(source.get("primary"), dict) else {}
    remaining = primary.get("remainingPercent")
    try:
        remaining_value = max(0.0, min(100.0, float(remaining))) if remaining is not None else None
    except (TypeError, ValueError, OverflowError):
        remaining_value = None
    return {
        "status": redact_text(str(source.get("status") or "unavailable"), 40),
        "limitReached": bool(source.get("limitReached", False)),
        "remainingPercent": int(remaining_value) if remaining_value is not None and remaining_value.is_integer() else remaining_value,
        "stale": bool(source.get("stale", False)),
    }


def agent_chat_response_read_model(payload: dict, replay: bool = False) -> dict:
    consumes_codex_quota = bool(payload.get("consumesCodexQuota", True)) and not replay
    usage_source = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    usage_source = {
        **usage_source,
        "quotaConsumptionStatus": payload.get(
            "quotaConsumptionStatus",
            usage_source.get("quotaConsumptionStatus"),
        ),
    }
    intent = str(payload.get("intent") or "conversation")
    if intent not in {"conversation", "task_request"}:
        intent = "conversation"
    task_mission_ids = payload.get("taskMissionIds") if isinstance(payload.get("taskMissionIds"), list) else []
    return {
        "ok": bool(payload.get("ok", False)),
        "kind": "agent_chat",
        "turnId": safe_reference(payload.get("turnId")),
        "sessionId": safe_reference(payload.get("sessionId")),
        "agentId": safe_reference(payload.get("agentId")),
        "agentName": redact_text(str(payload.get("agentName") or "AI Agent"), 120),
        "reply": redact_text(str(payload.get("reply") or ""), 5000),
        "status": redact_text(str(payload.get("status") or "failed"), 40),
        "modelTier": safe_reference(payload.get("modelTier")),
        "consumesCodexQuota": consumes_codex_quota,
        "toolsExecuted": False,
        "intent": intent,
        "taskCreated": bool(payload.get("taskCreated", False)),
        "taskMissionIds": [
            item for item in (safe_reference(value) for value in task_mission_ids[:100]) if item
        ],
        "taskStatus": redact_text(str(payload.get("taskStatus") or "not_requested"), 40),
        "autoExecute": bool(payload.get("autoExecute", False)),
        "usage": _agent_chat_usage_read_model(usage_source, replay=replay),
        "rateLimit": _agent_chat_rate_limit_read_model(payload.get("rateLimit")),
    }


def load_agent_chat_result(agent_id: str, session_id: str, idempotency_key: str) -> dict | None:
    path = _agent_chat_result_path(agent_id, session_id, idempotency_key)
    if not path.exists():
        return None
    payload = read_json(path, None)
    if not isinstance(payload, dict):
        raise DataIntegrityError("Agent chat idempotency result has an invalid shape.")
    if payload.get("agentId") != agent_id or payload.get("sessionId") != session_id:
        raise DataIntegrityError("Agent chat idempotency scope does not match its storage key.")
    return payload


def write_agent_chat_result(
    agent_id: str,
    session_id: str,
    idempotency_key: str,
    message_digest: str,
    response: dict,
) -> None:
    path = _agent_chat_result_path(agent_id, session_id, idempotency_key)
    payload = {
        "agentId": agent_id,
        "sessionId": session_id,
        "idempotencyDigest": payload_digest(agent_id, session_id, idempotency_key),
        "messageDigest": message_digest,
        "response": agent_chat_response_read_model(response),
        "httpStatus": clamp_int(response.get("_httpStatus"), 200, 200, 599),
        "createdAt": utc_now(),
    }
    write_json(path, payload, keep_backup=path.exists())


def load_agent_chat_history(
    agent_id: str,
    session_id: str,
    recent_turns: int = 8,
    max_chars: int = 12000,
) -> list[dict]:
    records = [
        item
        for item in tail_jsonl(_agent_chat_transcript_path(), limit=400, max_bytes=2 * 1024 * 1024)
        if item.get("type") == "agent.chat_turn"
        and item.get("agentId") == agent_id
        and item.get("sessionId") == session_id
        and item.get("status") == "completed"
    ][-max(1, min(10, recent_turns)):]
    exchanges = []
    total_chars = 0
    for item in reversed(records):
        user_message = redact_text(str(item.get("userMessage") or ""), 4000).strip()
        assistant_reply = redact_text(str(item.get("assistantReply") or ""), 5000).strip()
        if (
            not user_message
            or not assistant_reply
            or contains_potential_secret(user_message)
            or contains_potential_secret(assistant_reply)
        ):
            continue
        exchange_chars = len(user_message) + len(assistant_reply)
        if total_chars + exchange_chars > max_chars:
            break
        exchanges.append((
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_reply},
        ))
        total_chars += exchange_chars
    exchanges.reverse()
    return [message for exchange in exchanges for message in exchange]


def append_agent_chat_transcript(payload: dict) -> dict:
    ensure_runtime_dir()
    quota_consumption = str(payload.get("quotaConsumptionStatus") or "none")
    if quota_consumption not in {"none", "possible", "confirmed"}:
        quota_consumption = "none"
    record = {
        "type": "agent.chat_turn",
        "time": utc_now(),
        "turnId": safe_reference(payload.get("turnId")),
        "sessionId": safe_reference(payload.get("sessionId")),
        "agentId": safe_reference(payload.get("agentId")),
        "agentName": redact_text(str(payload.get("agentName") or "AI Agent"), 120),
        "idempotencyDigest": redact_text(str(payload.get("idempotencyDigest") or ""), 64),
        "userMessage": redact_text(str(payload.get("userMessage") or ""), 4000),
        "assistantReply": redact_text(str(payload.get("assistantReply") or ""), 5000),
        "status": redact_text(str(payload.get("status") or "failed"), 40),
        "modelTier": safe_reference(payload.get("modelTier")),
        "consumesCodexQuota": bool(payload.get("consumesCodexQuota", True)),
        "quotaConsumptionStatus": quota_consumption,
        "toolsExecuted": False,
        "intent": (
            str(payload.get("intent"))
            if str(payload.get("intent")) in {"conversation", "task_request"}
            else "conversation"
        ),
        "taskCreated": bool(payload.get("taskCreated", False)),
        "taskMissionIds": [
            item
            for item in (
                safe_reference(value)
                for value in (
                    payload.get("taskMissionIds")
                    if isinstance(payload.get("taskMissionIds"), list)
                    else []
                )[:100]
            )
            if item
        ],
        "taskStatus": redact_text(str(payload.get("taskStatus") or "not_requested"), 40),
        "autoExecute": bool(payload.get("autoExecute", False)),
        "usage": _agent_chat_usage_read_model({
            **(payload.get("usage") if isinstance(payload.get("usage"), dict) else {}),
            "quotaConsumptionStatus": quota_consumption,
        }),
    }
    transcript_path = _agent_chat_transcript_path()
    with AGENT_CHAT_LOCK:
        rotate_jsonl_segment(transcript_path)
        with transcript_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def append_agent_event(event: dict) -> dict:
    ensure_runtime_dir()
    record = {
        "time": utc_now(),
        "kind": event.get("kind", "office"),
        "agentId": event.get("agentId", "manager"),
        "title": redact_text(str(event.get("title", "Agent Event")), 120),
        "detail": redact_text(str(event.get("detail", "")), 1200),
        "missionId": safe_reference(event.get("missionId")),
        "targetId": safe_reference(event.get("targetId")),
        "simulation": bool(event.get("simulation", False)),
    }
    with AGENT_EVENTS_LOCK:
        rotate_jsonl_segment(AGENT_EVENTS_PATH)
        with AGENT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def load_agent_events(limit: int = 120) -> list[dict]:
    return tail_jsonl(AGENT_EVENTS_PATH, limit=limit, max_bytes=524288)


def _create_windows_kill_job(process: subprocess.Popen) -> dict | None:
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


def _terminate_command_process_tree(
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


def _run_safe_command_with_tree_timeout(
    command: list[str],
    timeout: int,
    output_limit: int,
    input_text: str | None,
    cancel_event: threading.Event | None = None,
) -> dict:
    global MISSION_WORKER_PROCESS, MISSION_WORKER_JOB_HOLDER
    started = time.perf_counter()
    creationflags = (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "CREATE_SUSPENDED", 0x00000004)
    ) if os.name == "nt" else 0
    process = None
    cancel_watcher = None
    cancel_watcher_stop = threading.Event()
    cancellation = {"requested": False, "treeTerminated": False}
    job_holder = None
    try:
        process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            creationflags=creationflags,
            start_new_session=os.name != "nt",
        )
        job_holder = _create_windows_kill_job(process)
        if os.name == "nt" and (not job_holder or not _resume_windows_process(process)):
            _terminate_command_process_tree(process, job_holder)
            raise RuntimeError("Unable to start command inside the guarded Windows process job.")
        if cancel_event is MISSION_WORKER_STOP:
            with MISSION_WORKER_PROCESS_LOCK:
                MISSION_WORKER_PROCESS = process
                MISSION_WORKER_JOB_HOLDER = job_holder
        if cancel_event is not None:
            def watch_for_cancellation() -> None:
                if cancel_event.wait():
                    if cancel_watcher_stop.is_set():
                        return
                    cancellation["requested"] = True
                    with MISSION_WORKER_PROCESS_LOCK:
                        cancellation["treeTerminated"] = _terminate_command_process_tree(process, job_holder)

            cancel_watcher = threading.Thread(
                target=watch_for_cancellation,
                name=f"command-cancel-{process.pid}",
                daemon=True,
            )
            cancel_watcher.start()
        try:
            stdout, stderr = process.communicate(input=input_text, timeout=timeout)
        except subprocess.TimeoutExpired:
            tree_terminated = _terminate_command_process_tree(process, job_holder)
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                if process.poll() is None:
                    process.kill()
                stdout, stderr = "", ""
                tree_terminated = False
            return {
                "ok": False,
                "exitCode": "timeout",
                "output": f"Command timed out after {timeout}s.",
                "durationMs": round((time.perf_counter() - started) * 1000),
                "processTreeTerminated": tree_terminated,
                "processStarted": True,
            }
        if cancellation["requested"]:
            if cancel_watcher and cancel_watcher.is_alive():
                cancel_watcher.join(timeout=12)
            return {
                "ok": False,
                "exitCode": "cancelled",
                "output": "Command was cancelled because the local Bridge is stopping.",
                "durationMs": round((time.perf_counter() - started) * 1000),
                "processTreeTerminated": bool(cancellation["treeTerminated"]),
                "processStarted": True,
            }
        output = redact_text((stdout or stderr or "").strip(), output_limit)
        _close_windows_kill_job(job_holder)
        return {
            "ok": process.returncode == 0,
            "exitCode": process.returncode,
            "output": output,
            "durationMs": round((time.perf_counter() - started) * 1000),
            "processTreeTerminated": False,
            "processStarted": True,
        }
    except PermissionError as error:
        return {
            "ok": False,
            "exitCode": "permission_denied",
            "output": redact_text(str(error), output_limit),
            "durationMs": round((time.perf_counter() - started) * 1000),
            "processTreeTerminated": False,
            "processStarted": False,
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "exitCode": "not_found",
            "output": redact_text(str(error), output_limit),
            "durationMs": round((time.perf_counter() - started) * 1000),
            "processTreeTerminated": False,
            "processStarted": False,
        }
    except Exception as error:
        tree_terminated = False
        if process is not None and process.poll() is None:
            tree_terminated = _terminate_command_process_tree(process, job_holder)
        return {
            "ok": False,
            "exitCode": "exception",
            "output": redact_text(str(error), output_limit),
            "durationMs": round((time.perf_counter() - started) * 1000),
            "processTreeTerminated": tree_terminated,
            "processStarted": process is not None,
        }
    finally:
        cancel_watcher_stop.set()
        if cancel_watcher and cancel_watcher.is_alive():
            cancel_watcher.join(timeout=1)
        if cancel_event is MISSION_WORKER_STOP:
            with MISSION_WORKER_PROCESS_LOCK:
                if MISSION_WORKER_PROCESS is process:
                    MISSION_WORKER_PROCESS = None
                    MISSION_WORKER_JOB_HOLDER = None
        _close_windows_kill_job(job_holder)


def run_safe_command(
    command: list[str],
    timeout: int = 8,
    output_limit: int = 1200,
    input_text: str | None = None,
    *,
    kill_process_tree_on_timeout: bool = False,
    cancel_event: threading.Event | None = None,
) -> dict:
    if kill_process_tree_on_timeout:
        return _run_safe_command_with_tree_timeout(
            command,
            timeout,
            output_limit,
            input_text,
            cancel_event=cancel_event,
        )
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        output = redact_text((result.stdout or result.stderr or "").strip(), output_limit)
        return {
            "ok": result.returncode == 0,
            "exitCode": result.returncode,
            "output": output,
            "durationMs": round((time.perf_counter() - started) * 1000),
        }
    except PermissionError as error:
        return {
            "ok": False,
            "exitCode": "permission_denied",
            "output": redact_text(str(error), output_limit),
            "durationMs": round((time.perf_counter() - started) * 1000),
        }
    except FileNotFoundError as error:
        return {
            "ok": False,
            "exitCode": "not_found",
            "output": redact_text(str(error), output_limit),
            "durationMs": round((time.perf_counter() - started) * 1000),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exitCode": "timeout",
            "output": f"Command timed out after {timeout}s.",
            "durationMs": round((time.perf_counter() - started) * 1000),
        }


def detect_codex() -> dict:
    if CODEX_RUNNER_PYTHON.exists() and CODEX_RUNNER_SCRIPT.exists():
        runner = run_safe_command([str(CODEX_RUNNER_PYTHON), str(CODEX_RUNNER_SCRIPT), "--status"], timeout=20)
        try:
            payload = json.loads(runner["output"]) if runner["output"] else {}
        except json.JSONDecodeError:
            payload = {}

        if payload:
            return {
                "status": payload.get("status", "blocked"),
                "path": "project_runner" if payload.get("codexBin") else None,
                "version": payload.get("version"),
                "message": redact_text(payload.get("message") or payload.get("login") or "Project Codex runner checked.", 1200),
                "diagnostic": redact_text(payload.get("diagnostic") or payload.get("login") or "", 1200),
                "runner": "project_sdk",
                "exitCode": runner["exitCode"],
            }

    codex_path = shutil.which("codex") or shutil.which("codex.exe")
    if not codex_path:
        return {
            "status": "unavailable",
            "path": None,
            "version": None,
            "message": "Codex CLI was not found in PATH.",
        }

    check = run_safe_command(["codex", "--version"], timeout=8)
    status = "ready" if check["ok"] else "blocked"
    return {
        "status": status,
        "path": "path_runner",
        "version": check["output"] if check["ok"] else None,
        "message": "Codex CLI is callable." if check["ok"] else redact_text(check["output"], 1200),
        "exitCode": check["exitCode"],
    }


def detect_mcp() -> dict:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    config_path = codex_home / "config.toml"
    return {
        "status": "config_present" if config_path.exists() else "not_configured",
        "codexHomePresent": codex_home.exists(),
        "configPresent": config_path.exists(),
        "message": "MCP config can be discovered by the local runner." if config_path.exists() else "No MCP config file detected yet.",
    }


def bridge_status() -> dict:
    codex = detect_codex()
    mcp = detect_mcp()
    operator_mode = load_operator_mode_record().get("mode") or _operator_mode_default()
    if codex["status"] in {"ready", "ready_guarded"}:
        mode = "Codex Runner Ready"
    elif codex["status"] in {"blocked", "config_error", "auth_required", "degraded"}:
        mode = "Local Runner Blocked"
    else:
        mode = "Mock"

    return {
        "ok": True,
        "mode": mode,
        "status": "guarded",
        "server": "Metafx Local Bridge",
        "root": "local_project",
        "codex": codex,
        "mcp": mcp,
        "policy": {
            "frontendSecrets": False,
            "approvalRequired": APPROVAL_REQUIRED,
            "allowedSmokeCommands": ["codex --version"],
            "operatorMode": operator_mode,
            "realCodexTaskDefault": "auto_guarded_allowlist" if operator_mode == "auto_guarded" else "approval_required",
            "frontendApprovedBooleanTrusted": False,
            "staticServing": "frontend_and_contracts_only",
        },
        "time": utc_now(),
    }


def bridge_status_read_model(status: dict | None = None) -> dict:
    status = status if isinstance(status, dict) else bridge_status()
    codex = status.get("codex") if isinstance(status.get("codex"), dict) else {}
    mcp = status.get("mcp") if isinstance(status.get("mcp"), dict) else {}
    return {
        "mode": redact_text(str(status.get("mode") or "Unknown"), 80),
        "status": redact_text(str(status.get("status") or "unknown"), 40),
        "runtimeVersion": BRIDGE_RUNTIME_VERSION,
        "codex": {
            "status": redact_text(str(codex.get("status") or "unknown"), 40),
            "version": redact_text(str(codex.get("version") or ""), 120) or None,
            "runner": redact_text(str(codex.get("runner") or ""), 80) or None,
        },
        "mcp": {
            "status": redact_text(str(mcp.get("status") or "unknown"), 40),
            "configPresent": bool(mcp.get("configPresent", False)),
        },
        "policy": {
            "frontendSecrets": False,
            "frontendIsIntentOnly": True,
            "realExecution": "backend_guarded",
            "unknownToolDefault": "deny",
            "operatorMode": redact_text(str((status.get("policy") or {}).get("operatorMode") or _operator_mode_default()), 40),
        },
        "checkedAt": status.get("time") or utc_now(),
    }


def capability_registry(status: dict | None = None) -> dict:
    """Build a sanitized capability read model from the tool permission contract."""
    bridge = status if isinstance(status, dict) else bridge_status()
    bridge_model = bridge_status_read_model(bridge)
    codex_status = str((bridge.get("codex") or {}).get("status") or "unknown")
    mcp_status = str((bridge.get("mcp") or {}).get("status") or "unknown")
    contract = load_tool_permissions()
    operator = operator_mode_read_model()
    operator_auto_tools = set(operator.get("guardrails", {}).get("autoEligibleTools") or [])
    capabilities = []
    for policy in contract.get("tools", []):
        if not isinstance(policy, dict):
            continue
        tool_id = safe_reference(policy.get("id"))
        if not tool_id:
            continue
        linked_props = [
            value for value in (safe_reference(item) for item in (policy.get("linkedPropIds") or [])) if value
        ]
        adapter_status = redact_text(str(policy.get("adapterStatus") or "unimplemented"), 80)
        runtime_status = adapter_status
        runtime_ready = adapter_status.startswith("implemented")
        if tool_id in {"codex_status", "codex_cli_smoke", "codex_cli_task"}:
            runtime_status = codex_status
            runtime_ready = codex_status in {"ready", "ready_guarded"}
        elif tool_id == "mcp_tool_run":
            runtime_status = f"{mcp_status}_adapter_unimplemented"
            runtime_ready = False
        policy_auto_runnable = bool(policy.get("autoRunnable", False))
        auto_runnable = (
            policy_auto_runnable
            and operator.get("autoExecute") is True
            and runtime_ready
        ) if tool_id in operator_auto_tools else policy_auto_runnable
        capabilities.append({
            "id": tool_id,
            "label": redact_text(str(policy.get("label") or tool_id), 120),
            "defaultMode": redact_text(str(policy.get("defaultMode") or "deny"), 80),
            "risk": redact_text(str(policy.get("risk") or "medium"), 20),
            "approvalRequired": bool(policy.get("approvalRequired", False)),
            "allowedAgents": [
                value for value in (safe_reference(item) for item in (policy.get("allowedAgents") or [])) if value
            ],
            "modelTier": redact_text(str(policy.get("modelTier") or "role_default"), 80),
            "linkedPropIds": linked_props,
            "adapterStatus": adapter_status,
            "runtimeStatus": redact_text(runtime_status, 80),
            "runtimeReady": runtime_ready,
            "realExecutionAvailable": bool(policy.get("realExecutionAvailable", False)),
            "autoRunnable": auto_runnable,
        })
    disabled_count = sum(
        1 for item in capabilities
        if str(item.get("adapterStatus") or "").startswith("disabled")
        or item.get("adapterStatus") in {"unimplemented", "not_implemented"}
    )
    return {
        "version": "capability-registry-v1",
        "contractVersion": redact_text(str(contract.get("version") or "unknown"), 80),
        "bridge": bridge_model,
        "capabilities": capabilities,
        "summary": {
            "total": len(capabilities),
            "runtimeReady": sum(1 for item in capabilities if item.get("runtimeReady")),
            "approvalGated": sum(1 for item in capabilities if item.get("approvalRequired")),
            "realExecutionAvailable": sum(1 for item in capabilities if item.get("realExecutionAvailable")),
            "disabledOrUnimplemented": disabled_count,
        },
        "policy": {
            "source": "tool_permission_contract",
            "frontendSecrets": False,
            "frontendIsIntentOnly": True,
            "unknownToolDefault": "deny",
            "disabledToolsFailClosed": True,
            "operatorMode": operator.get("mode"),
        },
        "updatedAt": utc_now(),
    }


def _codex_rate_window_read_model(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    try:
        used = float(value.get("usedPercent"))
    except (TypeError, ValueError, OverflowError):
        return None
    if used != used or used in {float("inf"), float("-inf")}:
        return None
    used = max(0.0, min(100.0, used))
    used_value: int | float = int(used) if used.is_integer() else round(used, 2)
    remaining = max(0.0, min(100.0, 100.0 - used))
    remaining_value: int | float = int(remaining) if remaining.is_integer() else round(remaining, 2)
    try:
        duration = int(value.get("windowDurationMinutes"))
    except (TypeError, ValueError, OverflowError):
        duration = None
    if duration is not None and not 1 <= duration <= 525600:
        duration = None
    reset = parse_iso(str(value.get("resetsAt") or ""))
    return {
        "usedPercent": used_value,
        "remainingPercent": remaining_value,
        "windowDurationMinutes": duration,
        "resetsAt": reset.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if reset else None,
    }


def codex_rate_limits_read_model(value: object) -> dict:
    """Strict allowlist between the Codex runner and every frontend response."""
    checked_at = utc_now()
    if isinstance(value, dict):
        parsed_checked_at = parse_iso(str(value.get("checkedAt") or ""))
        if parsed_checked_at:
            checked_at = parsed_checked_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if not isinstance(value, dict) or value.get("ok") is not True:
        raw_status = str(value.get("status") or "unavailable") if isinstance(value, dict) else "unavailable"
        status_name = raw_status if raw_status in {"auth_required", "config_error", "timeout", "missing", "unavailable"} else "unavailable"
        messages = {
            "auth_required": "Codex login is required before quota can be read.",
            "config_error": "Codex configuration must be fixed before quota can be read.",
            "timeout": "Codex rate-limit check timed out.",
            "missing": "The project Codex runtime is unavailable.",
            "unavailable": "Codex rate-limit data is unavailable.",
        }
        return {
            "ok": False,
            "status": status_name,
            "message": messages[status_name],
            "source": "codex_app_server",
            "missionId": CODEX_RATE_LIMIT_TELEMETRY_MISSION_ID,
            "ownerAgentId": CODEX_RATE_LIMIT_OWNER_AGENT_ID,
            "checkedAt": checked_at,
            "stale": False,
        }
    primary = _codex_rate_window_read_model(value.get("primary"))
    secondary = _codex_rate_window_read_model(value.get("secondary"))
    if primary is None:
        return codex_rate_limits_read_model({"ok": False, "status": "unavailable", "checkedAt": checked_at})
    return {
        "ok": True,
        "status": "ready",
        "source": "codex_app_server",
        "missionId": CODEX_RATE_LIMIT_TELEMETRY_MISSION_ID,
        "ownerAgentId": CODEX_RATE_LIMIT_OWNER_AGENT_ID,
        "meter": {"id": "codex", "name": "Codex"},
        "primary": primary,
        "secondary": secondary,
        "limitReached": bool(value.get("limitReached")),
        "checkedAt": checked_at,
        "stale": False,
    }


def invalidate_codex_rate_limit_cache() -> None:
    with CODEX_RATE_LIMIT_CACHE_LOCK:
        CODEX_RATE_LIMIT_CACHE["invalidated"] = True


def codex_rate_limits(force: bool = False) -> dict:
    """Return a coalesced, sanitized Codex quota snapshot with bounded stale fallback."""
    now = time.monotonic()
    with CODEX_RATE_LIMIT_CACHE_LOCK:
        cached = CODEX_RATE_LIMIT_CACHE.get("payload")
        fetched = float(CODEX_RATE_LIMIT_CACHE.get("fetchedMonotonic") or 0.0)
        age = max(0.0, now - fetched) if fetched else float("inf")
        invalidated = bool(CODEX_RATE_LIMIT_CACHE.get("invalidated"))
        force_allowed = bool(force and age >= CODEX_RATE_LIMIT_FORCE_MIN_SECONDS)
        if isinstance(cached, dict) and not force_allowed and not invalidated and age < CODEX_RATE_LIMIT_CACHE_TTL_SECONDS:
            return {**cached, "cacheHit": True, "cacheAgeSeconds": round(age, 1)}

        started = time.perf_counter()
        if CODEX_RUNNER_PYTHON.exists() and CODEX_RUNNER_SCRIPT.exists():
            runner = run_safe_command(
                [str(CODEX_RUNNER_PYTHON), str(CODEX_RUNNER_SCRIPT), "--rate-limits", "--timeout", "12"],
                timeout=18,
                output_limit=12000,
            )
            try:
                raw_payload = json.loads(runner.get("output") or "{}")
            except json.JSONDecodeError:
                raw_payload = {"ok": False, "status": "unavailable"}
        else:
            runner = {"ok": False, "exitCode": "not_found", "durationMs": 0}
            raw_payload = {"ok": False, "status": "missing"}
        fresh = codex_rate_limits_read_model(raw_payload)
        duration_ms = round((time.perf_counter() - started) * 1000)

        if fresh.get("ok"):
            CODEX_RATE_LIMIT_CACHE.update({
                "payload": fresh,
                "fetchedMonotonic": time.monotonic(),
                "invalidated": False,
            })
            primary = fresh.get("primary") if isinstance(fresh.get("primary"), dict) else {}
            append_audit({
                "type": "codex.rate_limits_refresh",
                "missionId": CODEX_RATE_LIMIT_TELEMETRY_MISSION_ID,
                "ownerAgentId": CODEX_RATE_LIMIT_OWNER_AGENT_ID,
                "ok": True,
                "status": "ready",
                "durationMs": duration_ms,
                "usedPercent": primary.get("usedPercent"),
                "remainingPercent": primary.get("remainingPercent"),
                "windowDurationMinutes": primary.get("windowDurationMinutes"),
                "resetsAt": primary.get("resetsAt"),
            })
            return {**fresh, "cacheHit": False, "cacheAgeSeconds": 0}

        status_name = str(fresh.get("status") or "unavailable")
        if status_name == "auth_required":
            CODEX_RATE_LIMIT_CACHE.update({"payload": None, "fetchedMonotonic": 0.0, "invalidated": False})
        elif isinstance(cached, dict) and age <= CODEX_RATE_LIMIT_STALE_MAX_SECONDS:
            stale_base = {
                **cached,
                "stale": True,
                "message": "Showing the last known Codex quota while refresh is unavailable.",
            }
            stale_payload = {**stale_base, "cacheHit": True, "cacheAgeSeconds": round(age, 1)}
            CODEX_RATE_LIMIT_CACHE["payload"] = stale_base
            CODEX_RATE_LIMIT_CACHE["invalidated"] = False
            append_audit({
                "type": "codex.rate_limits_refresh",
                "missionId": CODEX_RATE_LIMIT_TELEMETRY_MISSION_ID,
                "ownerAgentId": CODEX_RATE_LIMIT_OWNER_AGENT_ID,
                "ok": False,
                "status": status_name,
                "durationMs": duration_ms,
                "servedStale": True,
            })
            return stale_payload
        else:
            CODEX_RATE_LIMIT_CACHE["invalidated"] = False

        append_audit({
            "type": "codex.rate_limits_refresh",
            "missionId": CODEX_RATE_LIMIT_TELEMETRY_MISSION_ID,
            "ownerAgentId": CODEX_RATE_LIMIT_OWNER_AGENT_ID,
            "ok": False,
            "status": status_name,
            "durationMs": duration_ms,
            "servedStale": False,
        })
        return {**fresh, "cacheHit": False, "cacheAgeSeconds": None}


def peek_codex_rate_limits() -> dict:
    """Read the in-memory quota snapshot without starting Codex or writing an audit record."""
    with CODEX_RATE_LIMIT_CACHE_LOCK:
        cached = CODEX_RATE_LIMIT_CACHE.get("payload")
        fetched = float(CODEX_RATE_LIMIT_CACHE.get("fetchedMonotonic") or 0.0)
        if not isinstance(cached, dict):
            return {
                "ok": False,
                "status": "not_checked",
                "message": "ยังไม่ได้อ่าน Rate Limit ในรอบนี้",
                "checkedAt": None,
            }
        age = max(0.0, time.monotonic() - fetched) if fetched else None
        return {**cached, "cacheHit": True, "cacheAgeSeconds": round(age, 1) if age is not None else None}


def _bounded_children(path: Path, limit: int = 256) -> list[Path]:
    try:
        return [item for index, item in enumerate(path.iterdir()) if index < limit]
    except (OSError, PermissionError):
        return []


def _metatrader_target_store_path() -> Path:
    """Resolve against the live runtime root so isolated tests cannot write to the real store."""
    return RUNTIME_DIR / METATRADER_TARGET_STORE_FILENAME


def _empty_metatrader_target_store() -> dict:
    return {
        "schemaVersion": 1,
        "candidates": {},
        "selections": {},
        "updatedAt": None,
    }


def _load_metatrader_target_store_unlocked() -> dict:
    payload = read_json(_metatrader_target_store_path(), _empty_metatrader_target_store())
    if not isinstance(payload, dict):
        raise DataIntegrityError("MetaTrader target registry is not a JSON object.")
    candidates = payload.get("candidates")
    selections = payload.get("selections")
    if not isinstance(candidates, dict) or not isinstance(selections, dict):
        raise DataIntegrityError("MetaTrader target registry has an invalid shape.")
    return {
        "schemaVersion": 1,
        "candidates": candidates,
        "selections": selections,
        "updatedAt": payload.get("updatedAt"),
    }


def _write_metatrader_target_store_unlocked(payload: dict) -> None:
    payload["schemaVersion"] = 1
    payload["updatedAt"] = utc_now()
    write_json(_metatrader_target_store_path(), payload, keep_backup=True)


def _canonical_metatrader_location(path: Path) -> str:
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError):
        resolved = path.absolute()
    return os.path.normcase(str(resolved))


def _metatrader_identity_key(platform: str, local_path: str) -> str:
    """Backend-only lookup key; the public candidate id is independently random."""
    source = f"{platform}\0{os.path.normcase(local_path)}"
    return hashlib.sha256(source.encode("utf-8", errors="replace")).hexdigest()


def _new_metatrader_candidate_id() -> str:
    """Generate an opaque random id without decimal runs that resemble a PID/account."""
    alphabet = "abcdefghijkmnpqrstuvwxyz"
    return "mtc-" + "".join(secrets.choice(alphabet) for _ in range(26))


def _metatrader_running_state(running: dict, platform: str) -> str:
    if not bool(running.get("supported", False)):
        return "unknown"
    return "platform_running_detected" if max(0, int(running.get(platform) or 0)) else "not_running_detected"


def _public_metatrader_candidate(record: dict) -> dict | None:
    candidate_id = safe_reference(record.get("candidateId"))
    platform = str(record.get("platform") or "").lower()
    if not candidate_id or not candidate_id.startswith("mtc-") or platform not in {"mt4", "mt5"}:
        return None
    if not bool(record.get("available", False)):
        return None
    ordinal = clamp_int(record.get("ordinal"), 1, 1, 9999)
    running_state = str(record.get("runningState") or "unknown")
    if running_state not in {"unknown", "platform_running_detected", "not_running_detected"}:
        running_state = "unknown"
    label = "MT4" if platform == "mt4" else "MT5"
    return {
        "candidateId": candidate_id,
        "platform": platform,
        "labelTh": f"{label} ที่ตรวจพบ #{ordinal}",
        "detected": True,
        "runningState": running_state,
    }


def _available_metatrader_candidates_from_store() -> list[dict]:
    with METATRADER_TARGETS_LOCK:
        store = _load_metatrader_target_store_unlocked()
        candidates = [
            public
            for record in store["candidates"].values()
            if isinstance(record, dict)
            for public in [_public_metatrader_candidate(record)]
            if public
        ]
    return sorted(candidates, key=lambda item: (item["platform"], item["labelTh"], item["candidateId"]))


def _sync_metatrader_candidate_registry(discovered: list[dict], running: dict) -> list[dict]:
    """Persist random public ids while keeping canonical locations backend-only."""
    now = utc_now()
    with METATRADER_TARGETS_LOCK:
        store = _load_metatrader_target_store_unlocked()
        candidates = store["candidates"]
        for record in candidates.values():
            if isinstance(record, dict):
                record["available"] = False
                record["runningState"] = "unknown"

        existing_by_identity = {
            str(record.get("identityKey")): record
            for record in candidates.values()
            if isinstance(record, dict) and str(record.get("identityKey") or "")
        }
        next_ordinal = {
            platform: 1 + max(
                [
                    clamp_int(record.get("ordinal"), 0, 0, 9999)
                    for record in candidates.values()
                    if isinstance(record, dict) and record.get("platform") == platform
                ]
                or [0]
            )
            for platform in ("mt4", "mt5")
        }
        seen_identity_keys: set[str] = set()
        ordered = sorted(
            (item for item in discovered if isinstance(item, dict)),
            key=lambda item: (str(item.get("platform") or ""), str(item.get("localPath") or "")),
        )
        for item in ordered[:1024]:
            platform = str(item.get("platform") or "").lower()
            local_path = str(item.get("localPath") or "")
            if platform not in {"mt4", "mt5"} or not local_path:
                continue
            identity_key = _metatrader_identity_key(platform, local_path)
            if identity_key in seen_identity_keys:
                continue
            seen_identity_keys.add(identity_key)
            record = existing_by_identity.get(identity_key)
            if not isinstance(record, dict):
                candidate_id = _new_metatrader_candidate_id()
                while candidate_id in candidates:
                    candidate_id = _new_metatrader_candidate_id()
                record = {
                    "candidateId": candidate_id,
                    "identityKey": identity_key,
                    "platform": platform,
                    "ordinal": next_ordinal[platform],
                    "firstSeenAt": now,
                }
                next_ordinal[platform] += 1
                candidates[candidate_id] = record
                existing_by_identity[identity_key] = record
            record.update({
                "localPath": local_path,
                "lastSeenAt": now,
                "available": True,
                "runningState": _metatrader_running_state(running, platform),
            })

        _write_metatrader_target_store_unlocked(store)
        public_candidates = [
            public
            for record in candidates.values()
            if isinstance(record, dict)
            for public in [_public_metatrader_candidate(record)]
            if public
        ]
    return sorted(public_candidates, key=lambda item: (item["platform"], item["labelTh"], item["candidateId"]))


def _ephemeral_metatrader_candidates(discovered: list[dict], running: dict) -> list[dict]:
    """Return safe test/diagnostic candidates without touching the persistent registry."""
    counters = {"mt4": 0, "mt5": 0}
    candidates = []
    ordered = sorted(
        (item for item in discovered if isinstance(item, dict)),
        key=lambda item: (str(item.get("platform") or ""), str(item.get("localPath") or "")),
    )
    for item in ordered[:1024]:
        platform = str(item.get("platform") or "").lower()
        if platform not in counters:
            continue
        counters[platform] += 1
        label = "MT4" if platform == "mt4" else "MT5"
        candidates.append({
            "candidateId": _new_metatrader_candidate_id(),
            "platform": platform,
            "labelTh": f"{label} ที่ตรวจพบ #{counters[platform]}",
            "detected": True,
            "runningState": _metatrader_running_state(running, platform),
        })
    return candidates


def discover_metatrader_installations(roots: list[Path] | None = None, include_candidates: bool = False) -> dict:
    """Inspect bounded, well-known local folders without reading terminal accounts or config."""
    found: dict[str, dict[str, str]] = {"mt4": {}, "mt5": {}}
    candidate_roots: list[Path] = []
    if roots is not None:
        candidate_roots.extend(Path(item) for item in roots)
    else:
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidate_roots.append(Path(appdata) / "MetaQuotes" / "Terminal")
        for name in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
            value = os.environ.get(name)
            if value:
                candidate_roots.append(Path(value))
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            candidate_roots.append(Path(local_appdata) / "Programs")

    for root in candidate_roots[:12]:
        if not root.is_dir():
            continue
        root_name = root.name.lower()
        children = _bounded_children(root)
        # A supplied root may itself be a terminal/profile directory.
        entries = [root, *children]
        for entry in entries[:257]:
            if not entry.is_dir():
                continue
            local_path = _canonical_metatrader_location(entry)
            identity = _metatrader_identity_key("location", local_path)
            name = entry.name.lower()
            try:
                has_mql4 = (entry / "MQL4").is_dir()
                has_mql5 = (entry / "MQL5").is_dir()
                has_terminal = (entry / "terminal.exe").is_file()
                has_terminal64 = (entry / "terminal64.exe").is_file()
            except OSError:
                continue
            if has_mql4 or (has_terminal and ("metatrader 4" in name or name.startswith("mt4"))):
                found["mt4"][identity] = local_path
            if has_mql5 or (has_terminal64 and ("metatrader 5" in name or name.startswith("mt5"))):
                found["mt5"][identity] = local_path
            # MetaQuotes data roots contain opaque hash folders. MQL4/MQL5 is
            # the only inspected signal; origin/login/server files are ignored.
            if root_name == "terminal":
                if has_mql4:
                    found["mt4"][identity] = local_path
                if has_mql5:
                    found["mt5"][identity] = local_path

    result = {"mt4": len(found["mt4"]), "mt5": len(found["mt5"])}
    if include_candidates:
        result["_candidateLocations"] = [
            {"platform": platform, "localPath": local_path}
            for platform in ("mt4", "mt5")
            for local_path in found[platform].values()
        ]
    return result


def discover_running_metatrader(process_rows: list[str] | None = None) -> dict:
    """Count only terminal image names; never expose PID, command line, account or path."""
    if process_rows is None:
        if os.name != "nt":
            return {"supported": False, "mt4": 0, "mt5": 0}
        probe = run_safe_command(["tasklist", "/FO", "CSV", "/NH"], timeout=6, output_limit=200000)
        if not probe.get("ok"):
            return {"supported": False, "mt4": 0, "mt5": 0}
        process_rows = str(probe.get("output") or "").splitlines()

    counts = {"mt4": 0, "mt5": 0}
    for row in process_rows[:10000]:
        try:
            values = next(csv.reader([str(row)]))
        except (csv.Error, StopIteration):
            continue
        image_name = str(values[0] if values else row).strip().strip('"').lower()
        if image_name == "terminal.exe":
            counts["mt4"] += 1
        elif image_name == "terminal64.exe":
            counts["mt5"] += 1
    return {"supported": True, **counts}


def metatrader_status_read_model(installed: dict, running: dict, candidates: list[dict] | None = None) -> dict:
    platforms = {}
    for key, label in (("mt4", "MT4"), ("mt5", "MT5")):
        installed_count = max(0, int(installed.get(key) or 0))
        running_count = max(0, int(running.get(key) or 0))
        if running_count:
            status_name = "detected"
            detail = f"ตรวจพบ {label} กำลังทำงาน {running_count} รายการ แต่ยังไม่ได้เชื่อม Adapter สำหรับสั่งงาน"
        elif installed_count:
            status_name = "detected"
            detail = f"ตรวจพบ {label} ในเครื่อง {installed_count} รายการ และยังไม่พบว่ากำลังทำงาน"
        else:
            status_name = "not_found"
            detail = f"ยังไม่พบ {label} จากตำแหน่งมาตรฐานในเครื่อง"
        platforms[key] = {
            "label": label,
            "status": status_name,
            "installedCount": installed_count,
            "runningCount": running_count,
            "detailTh": detail,
        }
    safe_candidates = []
    for item in candidates or []:
        if not isinstance(item, dict):
            continue
        candidate_id = safe_reference(item.get("candidateId"))
        platform = str(item.get("platform") or "").lower()
        if not candidate_id or not candidate_id.startswith("mtc-") or platform not in {"mt4", "mt5"}:
            continue
        running_state = str(item.get("runningState") or "unknown")
        if running_state not in {"unknown", "platform_running_detected", "not_running_detected"}:
            running_state = "unknown"
        safe_candidates.append({
            "candidateId": candidate_id,
            "platform": platform,
            "labelTh": redact_text(str(item.get("labelTh") or ("MT4" if platform == "mt4" else "MT5")), 120),
            "detected": True,
            "runningState": running_state,
        })
    return {
        "status": "detected" if any(item["status"] == "detected" for item in platforms.values()) else "not_found",
        "mode": "read_only",
        "sideEffects": False,
        "processProbeSupported": bool(running.get("supported", False)),
        "adapterConnection": "coming_soon",
        "adapterReady": False,
        "candidateCount": len(safe_candidates),
        "candidates": safe_candidates,
        "platforms": platforms,
        "checkedAt": utc_now(),
        "privacy": "ไม่อ่านตำแหน่งโปรแกรม หมายเลข Process ข้อมูลบัญชี ชื่อโบรกเกอร์ รหัสผ่าน หรือข้อมูลการเทรด",
    }


def metatrader_status(force: bool = False, roots: list[Path] | None = None, process_rows: list[str] | None = None) -> dict:
    now = time.monotonic()
    with METATRADER_CACHE_LOCK:
        cached = METATRADER_CACHE.get("payload")
        fetched = float(METATRADER_CACHE.get("fetchedMonotonic") or 0.0)
        age = max(0.0, now - fetched) if fetched else float("inf")
        if isinstance(cached, dict) and not force and roots is None and process_rows is None and age < METATRADER_CACHE_TTL_SECONDS:
            return {**cached, "cacheHit": True, "cacheAgeSeconds": round(age, 1)}
        installed = discover_metatrader_installations(roots=roots, include_candidates=True)
        running = discover_running_metatrader(process_rows=process_rows)
        discovered = installed.get("_candidateLocations") if isinstance(installed.get("_candidateLocations"), list) else []
        isolated_runtime = os.path.normcase(str(RUNTIME_DIR.resolve(strict=False))) != os.path.normcase(
            str(PROJECT_RUNTIME_DIR.resolve(strict=False))
        )
        persist_candidates = (roots is None and process_rows is None) or isolated_runtime
        candidates = (
            _sync_metatrader_candidate_registry(discovered, running)
            if persist_candidates
            else _ephemeral_metatrader_candidates(discovered, running)
        )
        payload = metatrader_status_read_model(installed, running, candidates)
        if roots is None and process_rows is None:
            METATRADER_CACHE.update({"payload": payload, "fetchedMonotonic": time.monotonic()})
        return {**payload, "cacheHit": False, "cacheAgeSeconds": 0}


def peek_metatrader_status() -> dict:
    with METATRADER_CACHE_LOCK:
        cached = METATRADER_CACHE.get("payload")
        fetched = float(METATRADER_CACHE.get("fetchedMonotonic") or 0.0)
        if not isinstance(cached, dict):
            candidates = _available_metatrader_candidates_from_store()
            return {
                "status": "not_checked",
                "mode": "read_only",
                "sideEffects": False,
                "adapterConnection": "coming_soon",
                "adapterReady": False,
                "candidateCount": len(candidates),
                "candidates": candidates,
                "platforms": {
                    "mt4": {"label": "MT4", "status": "not_checked", "installedCount": 0, "runningCount": 0, "detailTh": "ยังกดค้นหา MT4 / MT5 ในรอบนี้"},
                    "mt5": {"label": "MT5", "status": "not_checked", "installedCount": 0, "runningCount": 0, "detailTh": "ยังกดค้นหา MT4 / MT5 ในรอบนี้"},
                },
                "checkedAt": None,
            }
        age = max(0.0, time.monotonic() - fetched) if fetched else None
        return {**cached, "cacheHit": True, "cacheAgeSeconds": round(age, 1) if age is not None else None}


def _metatrader_allowed_platforms_for_prop(prop_id: str) -> set[str]:
    if prop_id not in METATRADER_TARGET_PROP_IDS:
        return set()
    profile = find_dashboard_connection_profile(prop_id)
    allowed = set()
    for connection in profile.get("connections") or []:
        if not isinstance(connection, dict) or connection.get("action") != "discover_metatrader":
            continue
        item_id = str(connection.get("id") or "")
        if item_id == "mt4_terminal":
            allowed.add("mt4")
        elif item_id == "mt5_terminal":
            allowed.add("mt5")
    return allowed


def _metatrader_selection_read_model(prop_id: str, terminal_model: dict) -> dict:
    allowed_platforms = _metatrader_allowed_platforms_for_prop(prop_id)
    candidates = []
    for item in terminal_model.get("candidates") or []:
        if not isinstance(item, dict):
            continue
        candidate_id = safe_reference(item.get("candidateId"))
        platform = str(item.get("platform") or "").lower()
        if not candidate_id or not candidate_id.startswith("mtc-") or platform not in allowed_platforms:
            continue
        running_state = str(item.get("runningState") or "unknown")
        if running_state not in {"unknown", "platform_running_detected", "not_running_detected"}:
            running_state = "unknown"
        candidates.append({
            "candidateId": candidate_id,
            "platform": platform,
            "labelTh": redact_text(str(item.get("labelTh") or ("MT4" if platform == "mt4" else "MT5")), 120),
            "detected": True,
            "runningState": running_state,
        })
    candidates = sorted(candidates, key=lambda item: (item["platform"], item["labelTh"], item["candidateId"]))
    candidate_map = {item["candidateId"]: item for item in candidates}
    selected_candidate = None
    selected_at = None
    stale_selection = False
    with METATRADER_TARGETS_LOCK:
        store = _load_metatrader_target_store_unlocked()
        raw_selection = store["selections"].get(prop_id)
        if isinstance(raw_selection, dict):
            selected_id = safe_reference(raw_selection.get("candidateId"))
            selected_candidate = candidate_map.get(selected_id or "")
            stored_candidate = store["candidates"].get(selected_id or "")
            current_selection = bool(
                selected_candidate
                and isinstance(stored_candidate, dict)
                and _metatrader_candidate_record_is_current(stored_candidate)
            )
            if not current_selection:
                selected_candidate = None
            stale_selection = bool(selected_id and not current_selection)
            parsed_selected_at = parse_iso(str(raw_selection.get("selectedAt") or ""))
            if selected_candidate and parsed_selected_at:
                selected_at = parsed_selected_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    applicable = bool(allowed_platforms)
    if not applicable:
        status_name = "not_required"
        configuration_status = "not_required"
        detail = "Dashboard นี้ไม่ต้องเลือกเป้าหมาย MT4 / MT5"
    elif selected_candidate:
        status_name = "selected"
        configuration_status = "configured"
        detail = f"เลือก {selected_candidate['labelTh']} สำหรับ Dashboard นี้แล้ว แต่ Adapter สั่งงานจริงยังไม่เปิด"
    elif stale_selection:
        status_name = "not_selected"
        configuration_status = "not_configured"
        detail = "เป้าหมายเดิมไม่พร้อมใช้งานแล้ว กรุณาค้นหาและเลือกใหม่"
    elif candidates:
        status_name = "not_selected"
        configuration_status = "not_configured"
        detail = "ตรวจพบ MT4 / MT5 แล้ว กรุณาเลือกเป้าหมายสำหรับ Dashboard นี้"
    else:
        status_name = "not_selected"
        configuration_status = "not_configured"
        detail = "ยังไม่มีเป้าหมายที่เลือกได้ กรุณากดค้นหา MT4 / MT5 ก่อน"
    return {
        "propId": prop_id,
        "required": applicable,
        "detectedStatus": str(terminal_model.get("status") or "not_checked"),
        "status": status_name,
        "configurationStatus": configuration_status,
        "candidateCount": len(candidates),
        "candidates": candidates,
        "selectedCandidate": selected_candidate,
        "selectedAt": selected_at,
        "staleSelection": stale_selection,
        "adapterConnection": "coming_soon",
        "adapterReady": False,
        "canSelect": applicable and bool(candidates),
        "detailTh": detail,
    }


def _metatrader_candidate_record_is_current(record: dict) -> bool:
    candidate_id = safe_reference(record.get("candidateId"))
    platform = str(record.get("platform") or "").lower()
    local_path = str(record.get("localPath") or "")
    identity_key = str(record.get("identityKey") or "")
    if (
        not candidate_id
        or not candidate_id.startswith("mtc-")
        or platform not in {"mt4", "mt5"}
        or not local_path
        or not bool(record.get("available", False))
    ):
        return False
    if not secrets.compare_digest(identity_key, _metatrader_identity_key(platform, local_path)):
        return False
    location = Path(local_path)
    try:
        if not location.is_dir():
            return False
        if platform == "mt4":
            return (location / "MQL4").is_dir() or (location / "terminal.exe").is_file()
        return (location / "MQL5").is_dir() or (location / "terminal64.exe").is_file()
    except (OSError, PermissionError):
        return False


def _connection_probe_freshness(value: dict, stale_after_seconds: int | None = None) -> dict:
    parsed_checked_at = parse_iso(str(value.get("checkedAt") or "")) if isinstance(value, dict) else None
    checked_at = (
        parsed_checked_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if parsed_checked_at
        else None
    )
    try:
        cache_age = max(0.0, float(value.get("cacheAgeSeconds"))) if value.get("cacheAgeSeconds") is not None else None
    except (TypeError, ValueError, OverflowError):
        cache_age = None
    stale = bool(value.get("stale", False))
    if stale_after_seconds is not None and cache_age is not None and cache_age > stale_after_seconds:
        stale = True
    return {
        "checkedAt": checked_at,
        "cacheHit": bool(value.get("cacheHit", False)),
        "cacheAgeSeconds": round(cache_age, 1) if cache_age is not None else None,
        "stale": stale,
    }


def _connection_item_status(
    connection: dict,
    bridge: dict,
    quota: dict,
    terminals: dict,
    codex_active: bool,
    probe_freshness: dict[str, dict],
    metatrader_selection: dict | None = None,
) -> dict:
    item_id = str(connection.get("id") or "unknown")
    adapter_status = str(connection.get("adapterStatus") or "coming_soon")
    status_name = "ready"
    detail = "พร้อมใช้งานผ่าน Local Runner"
    status_source = "contract"
    item_freshness = _connection_probe_freshness({})
    execution_adapter_status = None
    terminal_selection_fields = None

    if adapter_status == "coming_soon":
        status_name = "coming_soon"
        detail = "วางโครงไว้แล้ว แต่ Adapter จริงยังไม่เปิดใช้งาน"
    elif adapter_status == "disabled":
        status_name = "disabled"
        detail = "ปิดไว้เพื่อความปลอดภัย"

    if item_id == "local_bridge":
        status_source = "bridge_probe"
        item_freshness = probe_freshness["bridge"]
        status_name, detail = "connected", "Local Bridge ทำงานในเครื่องและ Frontend ส่งเฉพาะคำสั่งแบบ Intent"
    elif item_id == "codex_runner":
        status_source = "bridge_probe"
        item_freshness = probe_freshness["bridge"]
        codex_status = str((bridge.get("codex") or {}).get("status") or "unknown")
        if codex_status == "ready":
            status_name = "connected"
            detail = "Codex CLI พร้อม ใช้บัญชีที่ Login อยู่ในเครื่องผ่าน Runner แบบมี Guard"
        elif codex_status == "auth_required":
            status_name, detail = "needs_login", "ต้อง Login Codex ในเครื่องก่อนจึงจะเรียกงาน AI ได้"
        elif codex_status in {"config_error", "blocked", "degraded"}:
            status_name, detail = "unavailable", "Codex Runner ยังติดปัญหา Config หรือการเริ่มทำงาน"
        else:
            status_name, detail = "not_found", "ยังไม่พบ Codex Runtime ที่พร้อมใช้งาน"
    elif item_id == "codex_quota":
        status_source = "codex_quota_probe"
        item_freshness = probe_freshness["codexQuota"]
        quota_status = str(quota.get("status") or "not_checked")
        if quota.get("ok") is True:
            primary = quota.get("primary") if isinstance(quota.get("primary"), dict) else {}
            used = primary.get("usedPercent")
            remaining = primary.get("remainingPercent")
            if quota.get("limitReached"):
                status_name, detail = "unavailable", "Codex ถึงขีดจำกัดแล้ว งาน AI ใหม่จะถูกหยุด แต่ Dashboard แบบอ่านอย่างเดียวยังเปิดได้"
            elif codex_active:
                status_name, detail = "connected", f"Dashboard นี้มีงาน Codex กำลังทำงาน ใช้แล้ว {used}% เหลือ {remaining}%"
            else:
                status_name, detail = "ready", f"อ่าน Rate Limit ได้: ใช้แล้ว {used}% เหลือ {remaining}% แต่ Dashboard นี้ไม่ได้กำลังใช้ Codex"
        elif quota_status == "auth_required":
            status_name, detail = "needs_login", "ต้อง Login Codex ก่อนอ่าน Rate Limit"
        elif quota_status == "not_checked":
            status_name, detail = "not_checked", "ยังไม่ได้ตรวจ Rate Limit ในรอบนี้ ดูค่ากลางได้ที่มุมซ้ายบน"
        else:
            status_name, detail = "unavailable", "ยังอ่าน Rate Limit ของ Codex ไม่ได้"
    elif item_id == "mcp_config":
        status_source = "bridge_probe"
        item_freshness = probe_freshness["bridge"]
        mcp_status = str((bridge.get("mcp") or {}).get("status") or "unknown")
        if mcp_status == "config_present":
            status_name, detail = "configured", "พบการตั้งค่า MCP แล้ว แต่การสั่ง MCP จาก HQ ยังต้องรอ Adapter"
        else:
            status_name, detail = "not_configured", "ยังไม่พบการตั้งค่า MCP ใน Codex ของเครื่องนี้"
    elif item_id in {"mt4_terminal", "mt5_terminal"}:
        status_source = "metatrader_probe"
        item_freshness = probe_freshness["metatrader"]
        execution_adapter_status = str(terminals.get("adapterConnection") or "coming_soon")
        platform_id = item_id[:3]
        platform = terminals.get("platforms", {}).get(platform_id, {})
        status_name = str(platform.get("status") or "not_checked")
        detail = str(platform.get("detailTh") or "ยังกดค้นหา MT4 / MT5")
        selection_model = metatrader_selection if isinstance(metatrader_selection, dict) else {}
        selected_candidate = selection_model.get("selectedCandidate")
        selected_here = bool(
            isinstance(selected_candidate, dict)
            and selected_candidate.get("platform") == platform_id
        )
        has_platform_candidate = any(
            isinstance(candidate, dict) and candidate.get("platform") == platform_id
            for candidate in (selection_model.get("candidates") or [])
        )
        terminal_selection_fields = {
            "detectionStatus": status_name,
            "selectionStatus": "selected" if selected_here else ("not_selected" if has_platform_candidate else "not_available"),
            "configurationStatus": "configured" if selected_here else "not_configured",
            "selected": selected_here,
            "adapterReady": False,
        }
    elif item_id == "memory_store":
        status_name, detail = "ready", "คลังความจำ Local พร้อมใช้งานแบบไม่ส่งข้อมูลออกนอกเครื่อง"
    elif item_id == "report_store":
        status_name, detail = "ready", "คลังรายงาน Local พร้อมรับผลจาก Mission"
    elif item_id == "workspace_adapter":
        status_name, detail = "ready", "พื้นที่โปรเจกต์พร้อม แต่การแก้ไฟล์จริงยังผ่าน Backend Guard"
    elif item_id == "tool_registry":
        status_name, detail = "ready", "อ่านทะเบียนสิทธิ์ Plugin / Tool ได้จาก Contract"
    elif item_id in {"risk_policy", "audit_log", "approval_service"}:
        status_name, detail = "ready", "ระบบตรวจความเสี่ยง บันทึก Log และ Approval พร้อมใช้งาน"
    elif item_id == "mission_store":
        status_name, detail = "ready", "Mission Queue พร้อมบันทึกสถานะงาน"
    elif item_id == "agent_event_store":
        status_name, detail = "ready", "Event Log ของ Agent พร้อมรับสถานะและรายงาน"
    elif item_id == "report_routing":
        status_name, detail = "ready", "รายงานจะกลับมาแสดงที่ Dashboard นี้และสรุปรวมที่ Mission Table"

    result = {
        "id": item_id,
        "labelTh": redact_text(str(connection.get("labelTh") or item_id), 160),
        "required": bool(connection.get("required", False)),
        "adapterStatus": adapter_status,
        "executionAdapterStatus": execution_adapter_status,
        "status": status_name,
        "statusSource": status_source,
        "detailTh": redact_text(detail, 500),
        "action": safe_reference(connection.get("action")),
        **item_freshness,
    }
    if terminal_selection_fields:
        result.update(terminal_selection_fields)
    return result


def dashboard_connection_checklist(
    prop_id: str,
    bridge: dict | None = None,
    quota: dict | None = None,
    terminals: dict | None = None,
) -> dict:
    profile = find_dashboard_connection_profile(prop_id)
    if not profile:
        return {}
    bridge_source = bridge if isinstance(bridge, dict) else bridge_status()
    bridge_model = bridge_status_read_model(bridge_source)
    quota_model = quota if isinstance(quota, dict) else peek_codex_rate_limits()
    terminal_model = terminals if isinstance(terminals, dict) else peek_metatrader_status()
    bridge_probe = {
        "checkedAt": bridge_source.get("time") or bridge_source.get("checkedAt"),
        "cacheHit": bridge_source.get("cacheHit", False),
        "cacheAgeSeconds": bridge_source.get("cacheAgeSeconds"),
        "stale": bridge_source.get("stale", False),
    }
    probe_freshness = {
        "bridge": _connection_probe_freshness(bridge_probe),
        "codexQuota": _connection_probe_freshness(quota_model, CODEX_RATE_LIMIT_CACHE_TTL_SECONDS),
        "metatrader": _connection_probe_freshness(terminal_model, METATRADER_CACHE_TTL_SECONDS),
    }
    codex_active = any(
        mission.get("status") == "running"
        and mission.get("toolId") == "codex_cli_task"
        and mission.get("targetId") == prop_id
        for mission in load_missions()
    )
    metatrader_selection = _metatrader_selection_read_model(prop_id, terminal_model)
    items = [
        _connection_item_status(
            item,
            bridge_model,
            quota_model,
            terminal_model,
            codex_active,
            probe_freshness,
            metatrader_selection,
        )
        for item in (profile.get("connections") or [])
        if isinstance(item, dict)
    ]
    item_map = {str(item.get("id") or ""): item for item in items}
    required_items = [item for item in items if item.get("required")]
    hard_problem = any(item.get("status") in {"needs_login", "not_configured", "not_found", "unavailable", "disabled"} for item in required_items)
    waiting_adapter = any(item.get("status") == "coming_soon" for item in required_items)
    optional_gap = any(
        not item.get("required")
        and item.get("status") in {"coming_soon", "needs_login", "not_configured", "not_found", "unavailable", "disabled"}
        for item in items
    )
    raw_requirements = profile.get("connectionRequirements") if isinstance(profile.get("connectionRequirements"), dict) else {}
    any_of_ids = [
        item_id for item_id in (safe_reference(value) for value in (raw_requirements.get("anyOf") or []))
        if item_id and item_id in item_map
    ]
    successful_connection_statuses = {"connected", "ready", "detected", "configured"}
    any_of_satisfied = not any_of_ids or any(
        item_map[item_id].get("status") in successful_connection_statuses
        for item_id in any_of_ids
    )
    any_of_statuses = [str(item_map[item_id].get("status") or "not_checked") for item_id in any_of_ids]
    if any_of_satisfied:
        any_of_status = "ready" if any_of_ids else "not_required"
        any_of_detail = "ตรวจพบการเชื่อมต่ออย่างน้อยหนึ่งรายการตามเงื่อนไข" if any_of_ids else "Dashboard นี้ไม่มีเงื่อนไขแบบเลือกอย่างน้อยหนึ่งรายการ"
    elif any(status == "not_checked" for status in any_of_statuses):
        any_of_status = "not_checked"
        any_of_detail = "ยังต้องตรวจ MT4 / MT5 และยืนยันว่าพบอย่างน้อยหนึ่งโปรแกรม"
    else:
        any_of_status = "needs_attention"
        any_of_detail = "ยังไม่พบ MT4 หรือ MT5 อย่างน้อยหนึ่งโปรแกรมตามที่ Dashboard นี้ต้องใช้"
    if hard_problem or any_of_status == "needs_attention":
        overall_status = "needs_attention"
    elif any_of_status == "not_checked":
        overall_status = "not_checked"
    else:
        overall_status = "partial" if waiting_adapter or optional_gap else "ready"
    operation = profile.get("operation") if isinstance(profile.get("operation"), dict) else {}
    planned_modes = operation.get("plannedModes") if isinstance(operation.get("plannedModes"), list) else []
    interval = operation.get("intervalMinutes")
    codex_usage = profile.get("codexUsage") if isinstance(profile.get("codexUsage"), dict) else {}
    connection_ids = set(item_map)
    relevant_probe_names = ["bridge"]
    if "codex_quota" in connection_ids:
        relevant_probe_names.append("codexQuota")
    if connection_ids.intersection({"mt4_terminal", "mt5_terminal"}):
        relevant_probe_names.append("metatrader")
    relevant_freshness = {name: probe_freshness[name] for name in relevant_probe_names}
    checked_candidates = [
        value.get("checkedAt") for value in relevant_freshness.values()
        if value.get("checkedAt") and parse_iso(value.get("checkedAt"))
    ]
    freshness_complete = len(checked_candidates) == len(relevant_freshness)
    checked_at = (
        min(checked_candidates, key=lambda value: parse_iso(value))
        if freshness_complete and checked_candidates
        else None
    )
    cache_ages = [
        value.get("cacheAgeSeconds") for value in relevant_freshness.values()
        if value.get("cacheAgeSeconds") is not None
    ]
    return {
        "dashboardId": prop_id,
        "overallStatus": overall_status,
        "operationMode": {
            "current": "manual",
            "labelTh": "สั่งทำงานเอง",
            "aiEveryTwoHours": {
                "status": "coming_soon" if "ai_every_2_hours" in planned_modes else "not_required",
                "labelTh": "AI ตรวจและส่งรายงานทุก 2 ชั่วโมง" if "ai_every_2_hours" in planned_modes else "Dashboard นี้ไม่ใช้รอบอัตโนมัติ",
                "intervalMinutes": interval if isinstance(interval, int) else None,
                "backendOwned": True,
                "enabled": False,
            },
        },
        "codexUsage": {
            "dependency": str(codex_usage.get("dependency") or "none"),
            "activeNow": codex_active,
            "usesLoggedInAccountQuota": str(codex_usage.get("dependency") or "none") != "none",
            "quotaStatus": str(quota_model.get("status") or "not_checked"),
            "readOnlyDashboardAvailableWhenLimited": bool(codex_usage.get("keepReadOnlyDashboardAvailable", True)),
        },
        "connectionRequirements": {
            "anyOf": any_of_ids,
            "anyOfSatisfied": any_of_satisfied,
            "status": any_of_status,
            "detailTh": any_of_detail,
        },
        "metatraderSelection": metatrader_selection,
        "items": items,
        "freshness": relevant_freshness,
        "freshnessComplete": freshness_complete,
        "checkedAt": checked_at,
        "cacheHit": any(value.get("cacheHit") for value in relevant_freshness.values()),
        "cacheAgeSeconds": max(cache_ages) if cache_ages else None,
        "stale": any(value.get("stale") for value in relevant_freshness.values()),
    }


def _complete_diagnostic_mission(mission: dict, report: dict, result: str) -> dict:
    mission["status"] = "completed"
    mission["result"] = redact_text(result, 1200)
    mission["reportIds"] = [report["id"]]
    mission["completedAt"] = utc_now()
    mission["updatedAt"] = mission["completedAt"]
    replace_mission(mission)
    return mission


def _fail_diagnostic_mission(mission: dict, audit_type: str, error_code: str) -> dict:
    failed_at = utc_now()
    mission["status"] = "failed"
    mission["phase"] = "diagnostic_failed"
    mission["errorCode"] = error_code
    mission["result"] = "การตรวจแบบ Read-only ทำงานไม่สำเร็จ ระบบไม่ลองซ้ำอัตโนมัติและไม่ได้สั่งงานภายนอก"
    mission["reportIds"] = []
    mission["completedAt"] = failed_at
    mission["updatedAt"] = failed_at
    replace_mission(mission)
    append_audit({
        "type": audit_type,
        "missionId": mission.get("id"),
        "ownerAgentId": mission.get("owner"),
        "dashboardId": mission.get("targetId"),
        "status": "failed",
        "errorCode": error_code,
        "sideEffects": False,
        "automaticRetry": False,
    })
    return mission


def refresh_dashboard_connections(prop_id: str) -> dict:
    profile = find_dashboard_connection_profile(prop_id)
    if not profile:
        raise RequestError("Dashboard connection profile was not found.", 404)
    allowed, retry_after = check_rate_limit(f"dashboard-connection:{prop_id}", 60, cooldown_seconds=2)
    if not allowed:
        raise RequestError(f"กรุณารอ {retry_after} วินาทีก่อนตรวจการเชื่อมต่อซ้ำ", 429)
    role = find_property_role(prop_id)
    owner = str(role.get("primaryOwnerAgentId") or "manager")
    mission = create_mission({
        "title": f"ตรวจการเชื่อมต่อ {profile.get('moduleNameTh') or prop_id}",
        "prompt": "ตรวจสถานะการเชื่อมต่อแบบ Read-only และส่งรายงานกลับ Dashboard",
        "agentId": owner,
        "requester": "human",
        "toolId": "dashboard_connection_check",
        "targetId": prop_id,
        "risk": "low",
        "reportType": "dashboard_connection_report",
    }, status="running")
    try:
        connection_ids = {str(item.get("id")) for item in (profile.get("connections") or []) if isinstance(item, dict)}
        live_bridge = bridge_status()
        quota = codex_rate_limits(force=True) if "codex_quota" in connection_ids else peek_codex_rate_limits()
        terminals = metatrader_status(force=True) if connection_ids.intersection({"mt4_terminal", "mt5_terminal"}) else peek_metatrader_status()
        checklist = dashboard_connection_checklist(prop_id, live_bridge, quota, terminals)
        report = create_report({
            "type": "dashboard_connection_report",
            "title": f"สถานะการเชื่อมต่อ: {profile.get('moduleNameTh') or prop_id}",
            "summary": "ตรวจการเชื่อมต่อจาก Local Runner แล้ว โดยไม่เปิดโปรแกรม ไม่สั่งเทรด และไม่อ่านข้อมูลลับ",
            "ownerAgentId": owner,
            "linkedMissionId": mission["id"],
            "linkedPropId": prop_id,
            "status": "ready",
            "findings": [f"{item['labelTh']}: {item['status']} — {item['detailTh']}" for item in checklist.get("items", [])],
            "metrics": {
                "diagnosticStatus": checklist.get("overallStatus") or "unknown",
                "connectionCount": len(checklist.get("items", [])),
                "readyCount": sum(1 for item in checklist.get("items", []) if item.get("status") in {"connected", "ready", "detected", "configured"}),
                "comingSoonCount": sum(1 for item in checklist.get("items", []) if item.get("status") == "coming_soon"),
            },
            "risks": ["ระบบ AI ตามรอบเวลายังปิดอยู่ จนกว่าจะมี Scheduler หลังบ้านและนโยบายอนุมัติที่พร้อมใช้งาน"],
            "nextActions": ["ตรวจรายการที่ยังไม่พร้อมจาก Checklist", "กดค้นหา MT4 / MT5 หาก Dashboard นี้ต้องใช้ Terminal"],
            "safety": {"approvalRequired": False, "publicShareable": False},
        })
        _complete_diagnostic_mission(mission, report, "ตรวจการเชื่อมต่อแบบ Read-only เสร็จแล้ว")
        append_audit({
            "type": "dashboard.connection_check",
            "missionId": mission["id"],
            "ownerAgentId": owner,
            "dashboardId": prop_id,
            "status": checklist.get("overallStatus"),
            "sideEffects": False,
        })
        return {
            "ok": True,
            "missionId": mission["id"],
            "ownerAgentId": owner,
            "status": "completed",
            "connectionChecklist": checklist,
            "report": report_read_model_item(report),
        }
    except Exception:
        _fail_diagnostic_mission(mission, "dashboard.connection_check_failed", "dashboard_connection_check_failed")
        raise


def run_metatrader_discovery(prop_id: str) -> dict:
    profile = find_dashboard_connection_profile(prop_id)
    actions = {
        str(item.get("action") or "")
        for item in (profile.get("connections") or [])
        if isinstance(item, dict)
    }
    if "discover_metatrader" not in actions:
        raise RequestError("Dashboard นี้ไม่ต้องใช้การค้นหา MT4 / MT5", 422)
    allowed, retry_after = check_rate_limit(f"terminal-discovery:{prop_id}", 60, cooldown_seconds=3)
    if not allowed:
        raise RequestError(f"กรุณารอ {retry_after} วินาทีก่อนค้นหา MT4 / MT5 ซ้ำ", 429)
    role = find_property_role(prop_id)
    owner = str(role.get("primaryOwnerAgentId") or "vps_watch")
    permission = evaluate_tool_permission(owner, "terminal_discovery")
    if not permission.get("allowed"):
        raise RequestError("Agent เจ้าของ Dashboard ไม่มีสิทธิ์ตรวจ Terminal", 403)
    mission = create_mission({
        "title": "ค้นหา MT4 / MT5 ในเครื่องแบบ Read-only",
        "prompt": "ตรวจเฉพาะว่ามีโปรแกรม MT4 / MT5 และกำลังทำงานหรือไม่ ห้ามเปิด ปิด เชื่อมบัญชี หรืออ่านข้อมูลการเทรด",
        "agentId": owner,
        "requester": "human",
        "toolId": "terminal_discovery",
        "targetId": prop_id,
        "risk": "low",
        "reportType": "terminal_discovery_report",
    }, status="running")
    try:
        terminal_state = metatrader_status(force=True)
        mt4 = terminal_state["platforms"]["mt4"]
        mt5 = terminal_state["platforms"]["mt5"]
        report = create_report({
        "type": "terminal_discovery_report",
        "title": "ผลค้นหา MT4 / MT5 แบบ Read-only",
        "summary": "ตรวจเฉพาะการติดตั้งและชื่อ Process มาตรฐาน ไม่ได้เชื่อม Terminal และไม่ได้อ่านบัญชีหรือข้อมูลเทรด",
        "ownerAgentId": owner,
        "linkedMissionId": mission["id"],
        "linkedPropId": prop_id,
        "status": "ready",
        "findings": [mt4["detailTh"], mt5["detailTh"], "Terminal Adapter สำหรับสั่งงานจริง: Coming Soon"],
        "metrics": {
            "diagnosticStatus": terminal_state["status"],
            "mt4InstalledCount": mt4["installedCount"],
            "mt4RunningCount": mt4["runningCount"],
            "mt5InstalledCount": mt5["installedCount"],
            "mt5RunningCount": mt5["runningCount"],
            "candidateCount": terminal_state.get("candidateCount", 0),
        },
        "risks": ["การตรวจพบโปรแกรมไม่เท่ากับเชื่อมต่อเพื่อสั่ง Backtest, Optimization หรือ Trading"],
        "nextActions": ["เชื่อม Adapter แบบ Read-only ก่อน", "ทดสอบ Demo ก่อนเปิดงาน Semi-auto", "Live Trading ยังปิด"],
        "safety": {"approvalRequired": False, "publicShareable": False},
        })
        _complete_diagnostic_mission(mission, report, "ค้นหา MT4 / MT5 แบบ Read-only เสร็จแล้ว")
        append_audit({
            "type": "terminal.discovery",
            "missionId": mission["id"],
            "ownerAgentId": owner,
            "dashboardId": prop_id,
            "status": terminal_state["status"],
            "mode": "read_only",
            "sideEffects": False,
            "mt4Installed": mt4["installedCount"],
            "mt4Running": mt4["runningCount"],
            "mt5Installed": mt5["installedCount"],
            "mt5Running": mt5["runningCount"],
        })
        return {
            "ok": True,
            "missionId": mission["id"],
            "ownerAgentId": owner,
            "status": "completed",
            "terminalStatus": terminal_state,
            "connectionChecklist": dashboard_connection_checklist(prop_id, terminals=terminal_state),
            "report": report_read_model_item(report),
        }
    except Exception:
        _fail_diagnostic_mission(mission, "terminal.discovery_failed", "terminal_discovery_failed")
        raise


def select_metatrader_target(prop_id: str, candidate_id: str) -> dict:
    if not SAFE_ID_PATTERN.fullmatch(prop_id) or not find_room_prop(prop_id):
        raise RequestError("Unknown dashboard id.", 404)
    if not SAFE_ID_PATTERN.fullmatch(candidate_id) or not candidate_id.startswith("mtc-"):
        raise RequestError("รหัสเป้าหมาย MT4 / MT5 ไม่ถูกต้อง", 422)

    allowed_platforms = _metatrader_allowed_platforms_for_prop(prop_id)
    if not allowed_platforms:
        raise RequestError("Dashboard นี้ไม่มี Action สำหรับเลือกเป้าหมาย MT4 / MT5", 422)
    role = find_property_role(prop_id)
    allowed_dashboard_actions = {
        str(item)
        for item in (role.get("allowedDashboardActions") or [])
        if isinstance(item, str)
    }
    if "select_metatrader_target" not in allowed_dashboard_actions:
        raise RequestError("Dashboard นี้ไม่ได้เปิด Action สำหรับเลือกเป้าหมาย Terminal", 403)
    owner = str(role.get("primaryOwnerAgentId") or "vps_watch")
    permission = evaluate_tool_permission(owner, "terminal_target_select")
    if not permission.get("allowed"):
        raise RequestError("Agent เจ้าของ Dashboard ไม่มีสิทธิ์เลือกเป้าหมาย Terminal", 403)
    policy = permission.get("policy") if isinstance(permission.get("policy"), dict) else {}
    linked_props = {
        str(item)
        for item in (policy.get("linkedPropIds") or [])
        if isinstance(item, str)
    }
    if prop_id not in linked_props:
        raise RequestError("Dashboard นี้ไม่ได้รับอนุญาตให้ใช้ Action เลือก Terminal", 403)

    with METATRADER_TARGETS_LOCK:
        store = _load_metatrader_target_store_unlocked()
        record = store["candidates"].get(candidate_id)
        if not isinstance(record, dict):
            raise RequestError("ไม่พบเป้าหมายนี้ กรุณากดค้นหา MT4 / MT5 ใหม่", 404)
        if str(record.get("platform") or "") not in allowed_platforms:
            raise RequestError("เป้าหมายนี้ไม่ตรงกับ Terminal ที่ Dashboard รองรับ", 422)
        if not _metatrader_candidate_record_is_current(record):
            raise RequestError("เป้าหมายนี้ไม่พร้อมใช้งานแล้ว กรุณากดค้นหา MT4 / MT5 ใหม่", 409)

    allowed, retry_after = check_rate_limit(f"terminal-target-select:{prop_id}", 120, cooldown_seconds=1)
    if not allowed:
        raise RequestError(f"กรุณารอ {retry_after} วินาทีก่อนเลือกเป้าหมายอีกครั้ง", 429)
    mission = create_mission({
        "title": "เลือกเป้าหมาย MT4 / MT5 สำหรับ Dashboard",
        "prompt": "บันทึกเป้าหมายที่ผู้ใช้เลือกไว้ใน Local Runner เท่านั้น ห้ามเปิดโปรแกรม รัน Terminal เชื่อมบัญชี หรือส่งคำสั่งเทรด",
        "agentId": owner,
        "requester": "human",
        "toolId": "terminal_target_select",
        "targetId": prop_id,
        "risk": "low",
        "reportType": "terminal_selection_report",
    }, status="running")
    try:
        selected_at = utc_now()
        with METATRADER_TARGETS_LOCK:
            store = _load_metatrader_target_store_unlocked()
            record = store["candidates"].get(candidate_id)
            if (
                not isinstance(record, dict)
                or str(record.get("platform") or "") not in allowed_platforms
                or not _metatrader_candidate_record_is_current(record)
            ):
                raise RequestError("เป้าหมายเปลี่ยนแปลงระหว่างดำเนินการ กรุณาค้นหาและเลือกใหม่", 409)
            selected_candidate = _public_metatrader_candidate(record)
            if not selected_candidate:
                raise RequestError("เป้าหมายนี้ไม่พร้อมให้เลือก", 409)
            store["selections"][prop_id] = {
                "candidateId": candidate_id,
                "selectedAt": selected_at,
            }
            _write_metatrader_target_store_unlocked(store)

        terminal_state = peek_metatrader_status()
        available_candidates = _available_metatrader_candidates_from_store()
        terminal_state = {
            **terminal_state,
            "candidateCount": len(available_candidates),
            "candidates": available_candidates,
            "adapterConnection": "coming_soon",
            "adapterReady": False,
        }
        checklist = dashboard_connection_checklist(prop_id, terminals=terminal_state)
        selection_model = checklist.get("metatraderSelection") if isinstance(checklist.get("metatraderSelection"), dict) else {}
        report = create_report({
            "type": "terminal_selection_report",
            "title": f"เลือกเป้าหมาย Terminal: {selected_candidate['labelTh']}",
            "summary": "บันทึกเป้าหมายไว้ใน Backend แบบ Local-only แล้ว แต่ยังไม่ได้เปิดหรือเชื่อม Terminal และ Adapter สั่งงานจริงยังเป็น Coming Soon",
            "ownerAgentId": owner,
            "linkedMissionId": mission["id"],
            "linkedPropId": prop_id,
            "status": "ready",
            "findings": [
                f"เป้าหมายที่เลือก: {selected_candidate['labelTh']}",
                f"Platform: {selected_candidate['platform'].upper()}",
                "สถานะการตั้งค่า: configured",
                "Terminal Adapter สำหรับสั่งงานจริง: Coming Soon",
            ],
            "metrics": {
                "candidateId": selected_candidate["candidateId"],
                "platform": selected_candidate["platform"],
                "detectionStatus": "detected",
                "configurationStatus": "configured",
                "adapterReady": False,
            },
            "risks": ["การเลือกเป้าหมายไม่เท่ากับเชื่อมต่อเพื่อ Backtest, Optimization หรือ Trading"],
            "nextActions": ["รอ Adapter แบบ Read-only", "ทดสอบ Demo ก่อน Semi-auto", "Live Trading ยังปิด"],
            "safety": {"approvalRequired": False, "publicShareable": False},
        })
        _complete_diagnostic_mission(mission, report, "บันทึกเป้าหมาย MT4 / MT5 ใน Local Runner แล้ว โดยยังไม่ได้เปิดหรือสั่งงาน Terminal")
        append_audit({
            "type": "terminal.target_selected",
            "missionId": mission["id"],
            "ownerAgentId": owner,
            "dashboardId": prop_id,
            "candidateId": selected_candidate["candidateId"],
            "platform": selected_candidate["platform"],
            "status": "configured",
            "mode": "backend_local_configuration_only",
            "sideEffects": False,
            "localStateChanged": True,
            "adapterConnection": "coming_soon",
            "adapterReady": False,
        })
        selection_response = {
            "propId": prop_id,
            "status": str(selection_model.get("status") or "selected"),
            "configurationStatus": str(selection_model.get("configurationStatus") or "configured"),
            "selectedCandidate": selection_model.get("selectedCandidate") or selected_candidate,
            "selectedAt": selection_model.get("selectedAt") or selected_at,
            "adapterConnection": "coming_soon",
            "adapterReady": False,
        }
        return {
            "ok": True,
            "missionId": mission["id"],
            "ownerAgentId": owner,
            "status": "completed",
            "selection": selection_response,
            "terminalStatus": terminal_state,
            "connectionChecklist": checklist,
            "report": report_read_model_item(report),
        }
    except Exception:
        _fail_diagnostic_mission(mission, "terminal.target_selection_failed", "terminal_target_selection_failed")
        raise


def resolve_contract_asset_path(value: object) -> Path | None:
    """Map project contract asset references to their published source file."""
    raw = str(value or "").strip().replace("\\", "/")
    if not raw or raw.startswith(("http:", "https:", "data:", "blob:", "/")):
        return None
    normalized = re.sub(r"^\./", "", raw)
    if normalized.startswith("frontend/"):
        return PROJECT_ROOT / Path(normalized)
    if not normalized.startswith("assets/"):
        return None
    asset_path = normalized.removeprefix("assets/")
    public_assets = PROJECT_ROOT / "frontend" / "public" / "assets"
    if asset_path.startswith(("custom-props", "prop-sheets")):
        return public_assets / "props" / Path(asset_path)
    if asset_path.startswith("navigation/"):
        return public_assets / "maps" / "command-room" / Path(asset_path)
    if asset_path.startswith("exact-scene-layers"):
        return public_assets / "maps" / "command-room" / "layers" / Path(asset_path)
    if asset_path.startswith("agents/"):
        return public_assets / "agents" / "legacy-prototype-agents" / Path(asset_path.removeprefix("agents/"))
    return public_assets / "maps" / "command-room" / Path(asset_path)


def runtime_health() -> dict:
    """Return a fast, side-effect-free readiness signal for launchers and UI recovery."""
    critical_paths = {
        "frontendIndex": PROJECT_ROOT / "frontend" / "index.html",
        "frontendRuntime": PROJECT_ROOT / "frontend" / "src" / "app" / "main.js",
        "frontendStyles": PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css",
        "roomContract": ROOM_PATH,
        "agentContract": AGENTS_PATH,
    }
    critical_files = {name: path.is_file() for name, path in critical_paths.items()}
    parsed_json = {}
    json_specs = {
        "roomContract": (ROOM_PATH, True, lambda value: isinstance(value, dict) and isinstance(value.get("props"), list) and isinstance(value.get("layers"), list)),
        "agentContract": (AGENTS_PATH, True, lambda value: isinstance(value, dict) and isinstance(value.get("agents"), list) and bool(value.get("agents"))),
        "missionStore": (MISSIONS_PATH, False, lambda value: isinstance(value, list) or (isinstance(value, dict) and isinstance(value.get("missions"), list))),
        "memoryIndex": (MEMORY_INDEX_PATH, False, lambda value: isinstance(value, dict) and isinstance(value.get("items"), list)),
    }
    json_integrity = {}
    for name, (path, required, validator) in json_specs.items():
        exists = path.is_file()
        if not exists:
            # Mission and memory stores are created on first use. A clean
            # student installation must therefore be healthy without them.
            parsed_json[name] = {}
            valid_json = not required
            schema_valid = not required
        else:
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                parsed_json[name] = value
                valid_json = True
                schema_valid = bool(validator(value))
            except (OSError, UnicodeError, json.JSONDecodeError):
                parsed_json[name] = {}
                valid_json = False
                schema_valid = False
        json_integrity[name] = {
            "exists": exists,
            "required": required,
            "validJson": valid_json,
            "schemaValid": schema_valid,
            "backupAvailable": path.with_name(f"{path.name}.bak").is_file(),
        }
    room_contract = parsed_json["roomContract"]
    agent_contract = parsed_json["agentContract"]
    agents = agent_contract.get("agents") if isinstance(agent_contract, dict) else []
    agent_count = len(agents) if isinstance(agents, list) else 0
    agent_ids = [str(item.get("id") or "") for item in agents if isinstance(item, dict)]
    expected_agent_ids = list(EXPECTED_AGENT_IDS)
    agent_roster_complete = (
        len(agent_ids) == len(expected_agent_ids)
        and len(set(agent_ids)) == len(expected_agent_ids)
        and set(agent_ids) == set(expected_agent_ids)
    )

    room = room_contract.get("room") if isinstance(room_contract, dict) and isinstance(room_contract.get("room"), dict) else {}
    navigation = room_contract.get("navigation") if isinstance(room_contract, dict) and isinstance(room_contract.get("navigation"), dict) else {}
    props = room_contract.get("props") if isinstance(room_contract, dict) and isinstance(room_contract.get("props"), list) else []
    room_image = resolve_contract_asset_path(room.get("image"))
    walkable_mask = resolve_contract_asset_path(navigation.get("walkableMask"))
    agent_images = {
        str(item.get("id") or f"agent-{index}"): bool(
            (resolve_contract_asset_path((item.get("visual") or {}).get("static_image")) or Path("__missing__")).is_file()
        )
        for index, item in enumerate(agents)
        if isinstance(item, dict)
    }
    prop_images = {
        str(item.get("id") or f"prop-{index}"): bool(
            (resolve_contract_asset_path(item.get("asset")) or Path("__missing__")).is_file()
        )
        for index, item in enumerate(props)
        if isinstance(item, dict) and item.get("asset")
    }
    asset_integrity = {
        "roomImage": bool(room_image and room_image.is_file()),
        "walkableMask": bool(walkable_mask and walkable_mask.is_file()),
        "agentImages": agent_images,
        "propImages": prop_images,
    }
    assets_ready = (
        asset_integrity["roomImage"]
        and asset_integrity["walkableMask"]
        and len(agent_images) == len(expected_agent_ids)
        and all(agent_images.values())
        and all(prop_images.values())
    )
    ready = all(critical_files.values()) and all(
        item["validJson"] and item["schemaValid"] for item in json_integrity.values()
    ) and agent_roster_complete and assets_ready
    return {
        "ok": ready,
        "status": "ready" if ready else "degraded",
        "server": "Metafx Local Bridge",
        "version": BRIDGE_RUNTIME_VERSION,
        "startedAt": SERVER_STARTED_AT,
        "uptimeSeconds": round(max(0.0, time.monotonic() - SERVER_STARTED_MONOTONIC), 1),
        "agentCount": agent_count,
        "expectedAgentCount": len(expected_agent_ids),
        "agentRosterComplete": agent_roster_complete,
        "criticalFiles": critical_files,
        "jsonIntegrity": json_integrity,
        "assetIntegrity": asset_integrity,
        "policy": {
            "loopbackOnly": True,
            "frontendSecrets": False,
            "realExecution": "guarded",
        },
        "time": utc_now(),
    }


def pick_target_for_task(text: str) -> str:
    lower = text.lower()
    if any(keyword_matches(lower, token) for token in ["risk", "approval", "secret", "token", "password", "live order", "delete", "deploy production", "send telegram"]):
        return "left_audit_crystals"
    if any(keyword_matches(lower, token) for token in ["executive summary", "mission plan", "manager plan"]):
        return "mission_strategy_table"
    role_map = load_property_role_map()
    for rule in role_map.get("routingRules", []):
        target_id = str(rule.get("targetPropId") or "")
        keywords = rule.get("keywords") if isinstance(rule.get("keywords"), list) else []
        if target_id and any(keyword_matches(lower, token) for token in keywords):
            return target_id
    if any(keyword_matches(lower, token) for token in ["backtest", "back test", "drawdown", "profit factor", "equity", "แบคเทส", "แบคเทรด"]):
        return "left_analytics_console"
    if any(keyword_matches(lower, token) for token in ["auto trade", "auto trading", "autotrade", "ai trader", "live trading", "order", "position", "signal", "ea status", "ออโต้เทรด", "เทรดอัตโนมัติ", "ออเดอร์", "โพซิชั่น", "ซิกแนล"]):
        return "left_signal_cube"
    if any(keyword_matches(lower, token) for token in ["ea", "mt4", "mt5", "compile", "indicator"]):
        return "terminal_workstation"
    if any(keyword_matches(lower, token) for token in ["vps", "latency", "uptime", "cpu", "ram", "server"]):
        return "right_status_crystals"
    if any(keyword_matches(lower, token) for token in ["telegram", "alert", "summary"]):
        return "right_tool_console"
    if any(keyword_matches(lower, token) for token in ["risk", "approval", "secret", "compliance"]):
        return "left_audit_crystals"
    if any(keyword_matches(lower, token) for token in ["mcp", "codex", "runner", "bridge", "cli"]):
        return "codex_mcp_portal"
    return "mission_strategy_table"


def load_missions() -> list[dict]:
    with MISSIONS_LOCK:
        data = read_json(MISSIONS_PATH, {"missions": []})
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return [item for item in data.get("missions", []) if isinstance(item, dict)]


def save_missions(missions: list[dict]) -> None:
    with MISSIONS_LOCK:
        # Missions are an audit/history source for Mission Archivist. Do not
        # silently discard older records when the active queue grows.
        write_json(MISSIONS_PATH, {"updatedAt": utc_now(), "missions": missions}, keep_backup=True)


def replace_mission(updated: dict) -> None:
    with MISSIONS_LOCK:
        missions = load_missions()
        for index, mission in enumerate(missions):
            if mission.get("id") == updated.get("id"):
                missions[index] = updated
                save_missions(missions)
                return
        missions.insert(0, updated)
        save_missions(missions)


def find_mission(mission_id: str) -> dict | None:
    return next((mission for mission in load_missions() if mission.get("id") == mission_id), None)


def reconcile_stale_approval_missions() -> int:
    """Fail closed on expired or inconsistent approval-gated records."""
    reconciled: list[dict] = []
    parent_ids: set[str] = set()
    now = datetime.now(timezone.utc)
    reconciled_at = utc_now()
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            is_auto_queue = (
                mission.get("status") == "queued"
                and mission.get("autoEligible") is True
                and mission.get("executionMode") == "auto_guarded"
                and execution.get("schema") == "auto-guarded-execution-v1"
            )
            if mission.get("status") != "waiting_approval" and not is_auto_queue:
                continue
            approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
            state = str(approval.get("state") or "not_required")
            expires_at = parse_iso(approval.get("expiresAt"))
            reason = None
            if not approval.get("required"):
                reason = "legacy_waiting_without_required_approval"
            elif state in {"rejected", "expired", "invalidated", "consumed"}:
                reason = f"closed_approval_state_{state}"
            elif expires_at and now >= expires_at:
                approval["state"] = "expired"
                reason = "approval_expired_during_startup_reconciliation"
            if not reason:
                continue
            mission["approval"] = approval
            mission["status"] = "blocked"
            mission["phase"] = "approval_reconciled"
            mission["errorCode"] = reason
            mission["result"] = (
                "Mission was blocked during Bridge startup because its stored approval state "
                "is expired or inconsistent. No tool executed; create a fresh mission if the intent is still needed."
            )
            mission["updatedAt"] = reconciled_at
            mission["completedAt"] = reconciled_at
            if is_auto_queue:
                execution["dispatchState"] = "blocked"
                execution["completedAt"] = reconciled_at
                execution["heartbeatAt"] = reconciled_at
                mission["execution"] = execution
            reconciled.append(mission)
            parent_id = safe_reference(mission.get("parentMissionId"))
            if parent_id:
                parent_ids.add(parent_id)
        if reconciled:
            save_missions(missions)

    for mission in reconciled:
        append_audit({
            "type": "mission.approval_reconciled",
            "missionId": mission.get("id"),
            "ownerAgentId": mission.get("owner"),
            "toolId": mission.get("toolId"),
            "status": mission.get("status"),
            "reason": mission.get("errorCode"),
            "realToolExecuted": False,
        })
    for parent_id in parent_ids:
        refresh_parent_mission(parent_id)
    return len(reconciled)


def recover_interrupted_missions() -> int:
    """Fail closed on real jobs whose single-use approval was consumed before a restart."""
    recovered: list[dict] = []
    parent_ids: set[str] = set()
    with MISSIONS_LOCK:
        missions = load_missions()
        recovered_at = utc_now()
        for mission in missions:
            approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            auto_run_interrupted = (
                mission.get("executionMode") == "auto_guarded"
                and mission.get("autoEligible") is True
                and execution.get("schema") == "auto-guarded-execution-v1"
                and execution.get("dispatchState") == "running"
                and bool(execution.get("leaseId"))
                and int(mission.get("attemptCount") or 0) > 0
            )
            if mission.get("status") != "running" or (
                approval.get("state") != "consumed" and not auto_run_interrupted
            ):
                continue
            mission["status"] = "failed"
            mission["phase"] = "auto_worker_interrupted" if auto_run_interrupted else "interrupted"
            mission["errorCode"] = "auto_worker_interrupted" if auto_run_interrupted else "bridge_restart_interrupted"
            mission["result"] = (
                "The previous Bridge process ended while this guarded task was running. "
                "Its single-use approval remains consumed and no automatic retry was attempted."
            )
            mission["updatedAt"] = recovered_at
            mission["completedAt"] = recovered_at
            if auto_run_interrupted:
                execution["dispatchState"] = "failed"
                execution["heartbeatAt"] = recovered_at
                execution["completedAt"] = recovered_at
                execution["automaticRetry"] = False
                mission["execution"] = execution
            recovered.append(mission)
            parent_id = safe_reference(mission.get("parentMissionId"))
            if parent_id:
                parent_ids.add(parent_id)
        if recovered:
            save_missions(missions)

    for mission in recovered:
        append_audit({
            "type": "mission.interrupted_recovered",
            "missionId": mission.get("id"),
            "ownerAgentId": mission.get("owner"),
            "toolId": mission.get("toolId"),
            "status": mission.get("status"),
            "automaticRetry": False,
        })
    for parent_id in parent_ids:
        refresh_parent_mission(parent_id)
    return len(recovered)


def mission_outcome_status(mission: dict) -> str:
    status = str(mission.get("status") or "unknown")
    if status != "archived":
        return status
    archived_from = str(mission.get("archivedFromStatus") or "unknown")
    return "completed" if archived_from == "completed" else archived_from


def summarize_mission_outcomes(missions: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for mission in missions:
        status = mission_outcome_status(mission)
        counts[status] = counts.get(status, 0) + 1
    succeeded = counts.get("completed", 0)
    return {
        "total": len(missions),
        "byOutcome": counts,
        "succeeded": succeeded,
        "notSucceeded": max(0, len(missions) - succeeded),
    }


def mission_display_status(mission: dict) -> str:
    status = str(mission.get("status") or "unknown")
    archived_from = str(mission.get("archivedFromStatus") or "unknown")
    return f"archived (from {archived_from})" if status == "archived" else status


def refresh_parent_mission(parent_mission_id: str | None) -> dict | None:
    """Roll child status and final reports back into the Manager parent mission."""
    if not parent_mission_id:
        return None
    missions = load_missions()
    parent = next((item for item in missions if item.get("id") == parent_mission_id), None)
    if not parent:
        return None
    children = [item for item in missions if item.get("parentMissionId") == parent_mission_id]
    if not children:
        return parent

    summary = summarize_missions(children)
    outcome_summary = summarize_mission_outcomes(children)
    counts = summary["byStatus"]
    running_count = counts.get("running", 0)
    waiting_count = counts.get("waiting_approval", 0)
    queued_count = counts.get("queued", 0)
    active_count = running_count + waiting_count + queued_count
    attention_count = outcome_summary["notSucceeded"] if not active_count else sum(
        1 for item in children if mission_outcome_status(item) in {"blocked", "failed", "unknown"}
    )
    delegation = parent.get("delegation") if isinstance(parent.get("delegation"), dict) else {}
    delegation["subtaskCount"] = len(children)
    delegation["subtaskStatusCounts"] = counts
    delegation["realToolExecuted"] = any(
        bool(
            (item.get("execution") if isinstance(item.get("execution"), dict) else {}).get(
                "processStarted"
            )
        )
        for item in children
    )
    delegation["lastAggregatedAt"] = utc_now()

    if running_count:
        parent["status"] = "running"
        parent["phase"] = "specialists_running"
        delegation["state"] = "specialists_running"
        parent["result"] = (
            f"Agent ผู้เชี่ยวชาญกำลังทำงานจริง {running_count} งาน และมีอีก "
            f"{active_count - running_count} งานที่อยู่ในคิวหรือรอการอนุมัติ"
        )
        parent["completedAt"] = None
    elif waiting_count:
        parent["status"] = "waiting_approval"
        parent["phase"] = "awaiting_specialist_approval"
        delegation["state"] = "awaiting_specialist_approval"
        parent["result"] = (
            f"ขณะนี้ยังไม่มี Agent ผู้เชี่ยวชาญกำลังรันงาน มี {waiting_count} งานรอการอนุมัติ "
            f"และ {queued_count} งานอยู่ในคิว"
        )
        parent["completedAt"] = None
    elif queued_count:
        parent["status"] = "queued"
        parent["phase"] = "awaiting_specialist_start"
        delegation["state"] = "awaiting_specialist_start"
        parent["result"] = f"ขณะนี้ยังไม่มี Agent ผู้เชี่ยวชาญกำลังรันงาน และมี {queued_count} งานอยู่ในคิว"
        parent["completedAt"] = None
    else:
        completed_count = outcome_summary["succeeded"]
        clean_completion = completed_count == len(children) and attention_count == 0
        parent["status"] = "completed" if clean_completion else "blocked"
        parent["phase"] = "synthesized" if clean_completion else "review_required"
        delegation["state"] = parent["phase"]
        parent["result"] = (
            f"Manager รวบรวมผลจาก Agent ผู้เชี่ยวชาญครบ {completed_count}/{len(children)} งาน และสรุปภาพรวมเรียบร้อยแล้ว"
            if clean_completion
            else f"Manager รวบรวมสถานะสุดท้ายครบแล้ว แต่ยังมี {attention_count} งานที่ต้องตรวจสอบก่อนปิด Mission"
        )
        parent["completedAt"] = utc_now()
        final_report = create_report({
            "id": delegation.get("finalReportId"),
            "type": "executive_summary",
            "title": f"Executive summary: {parent.get('title') or parent_mission_id}",
            "summary": parent["result"],
            "ownerAgentId": "manager",
            "linkedMissionId": parent_mission_id,
            "linkedPropId": "mission_strategy_table",
            "status": "ready" if clean_completion else "blocked",
            "findings": [
                f"{item.get('owner')}: {mission_display_status(item)} - {redact_text(str(item.get('result') or 'No report summary.'), 600)}"
                for item in children
            ],
            "metrics": {**summary, "outcomes": outcome_summary},
            "risks": [
                f"{item.get('owner')}: {item.get('errorCode') or mission_outcome_status(item)}"
                for item in children if mission_outcome_status(item) != "completed"
            ],
            "nextActions": [] if clean_completion else ["ตรวจงานที่ติดขัด ไม่สำเร็จ หรือถูกเก็บโดยยังไม่สำเร็จที่โต๊ะวางแผน Mission"],
        })
        delegation["finalReportId"] = final_report["id"]
        report_ids = parent.get("reportIds") if isinstance(parent.get("reportIds"), list) else []
        parent["reportIds"] = list(dict.fromkeys([*report_ids, final_report["id"]]))

    parent["delegation"] = delegation
    parent["updatedAt"] = utc_now()
    replace_mission(parent)
    append_audit({
        "type": "manager.parent_refreshed",
        "missionId": parent_mission_id,
        "status": parent["status"],
        "phase": parent["phase"],
        "subtaskStatusCounts": counts,
        "subtaskOutcomeCounts": outcome_summary["byOutcome"],
    })
    return parent


def reconcile_parent_mission_statuses() -> int:
    """Re-derive Manager parent cards so no parent claims running without a running child."""
    parent_ids = {
        parent_id
        for parent_id in (
            safe_reference(mission.get("parentMissionId"))
            for mission in load_missions()
        )
        if parent_id
    }
    refreshed = 0
    for parent_id in sorted(parent_ids):
        if refresh_parent_mission(parent_id):
            refreshed += 1
    return refreshed


def find_mission_by_idempotency(idempotency_key: str) -> dict | None:
    if not idempotency_key:
        return None
    return next((mission for mission in load_missions() if mission.get("idempotencyKey") == idempotency_key), None)


def same_idempotency_scope(
    mission: dict,
    requester: str,
    tool_id: str,
    owner: str,
    request_digest: str,
) -> bool:
    stored_digest = str(mission.get("idempotencyScopeDigest") or "")
    return (
        str(mission.get("requester") or "") == requester
        and str(mission.get("toolId") or "") == tool_id
        and str(mission.get("owner") or "") == owner
        and bool(stored_digest)
        and bool(request_digest)
        and secrets.compare_digest(stored_digest, request_digest)
    )


def required_approval_actors(risk: str) -> list[str]:
    gate = load_orchestration_contract().get("approvalGate") or {}
    key = "highRiskRequiredActors" if risk == "high" else "mediumRiskRequiredActors"
    actors = gate.get(key) if isinstance(gate.get(key), list) else ["human"]
    return [str(actor) for actor in actors]


def effective_risk(requested: object, policy_risk: object) -> str:
    """A caller may raise risk, but may never downgrade the tool contract."""
    order = {"low": 0, "medium": 1, "high": 2}
    requested_value = str(requested or "low").lower()
    policy_value = str(policy_risk or "low").lower()
    if requested_value not in order:
        requested_value = "medium"
    if policy_value not in order:
        policy_value = "medium"
    return max((requested_value, policy_value), key=lambda value: order[value])


def backend_risk_guard_review(mission: dict, approval: dict) -> tuple[str, str]:
    """Apply a backend-owned, deterministic high-risk policy to one bound packet."""
    gate = load_orchestration_contract().get("approvalGate") or {}
    review_policy = gate.get("riskGuardReview") if isinstance(gate.get("riskGuardReview"), dict) else {}
    rule_version = str(review_policy.get("ruleVersion") or "risk-guard-v1")
    allowlist = {
        str(value) for value in review_policy.get("implementedToolAllowlist", ["codex_cli_task"])
    }
    blocked_keywords = [
        str(value).lower() for value in review_policy.get("blockedIntentKeywords", [
            "live trading", "live order", "send telegram", "delete", "deploy", "publish external", "spend credit", "restart vps",
        ])
        if str(value).strip()
    ]
    expected_digest = str(approval.get("payloadDigest") or "")
    actual_digest = mission_payload_digest(mission)
    tool_id = str(mission.get("toolId") or "")
    policy = get_tool_policy(tool_id) or {}
    adapter_status = str(policy.get("adapterStatus") or "unimplemented").lower()
    detail = str(mission.get("detail") or "").lower()

    if not expected_digest or not secrets.compare_digest(expected_digest, actual_digest):
        decision, reason = "rejected", "mission_digest_mismatch"
    elif tool_id not in allowlist:
        decision, reason = "rejected", "tool_not_in_high_risk_allowlist"
    elif adapter_status.startswith("disabled") or adapter_status in {"unimplemented", "not_implemented", "not_configured"}:
        decision, reason = "rejected", "adapter_disabled_or_unimplemented"
    elif not bool(policy.get("realExecutionAvailable", False)):
        decision, reason = "rejected", "real_execution_unavailable"
    elif any(keyword in detail for keyword in blocked_keywords):
        decision, reason = "rejected", "blocked_high_risk_intent"
    else:
        decision, reason = "approved", "bounded_implemented_backend_adapter"

    decisions = [
        item for item in (approval.get("decisions") or [])
        if isinstance(item, dict) and item.get("actorId") != "risk_guard"
    ]
    decisions.append({
        "actorId": "risk_guard",
        "actorProvenance": "backend_deterministic_policy",
        "decision": decision,
        "note": reason,
        "time": utc_now(),
        "payloadDigest": expected_digest,
        "ruleVersion": rule_version,
    })
    approval["decisions"] = decisions
    mission["riskGuardReview"] = {
        "decision": decision,
        "reason": reason,
        "ruleVersion": rule_version,
        "payloadDigest": expected_digest,
        "reviewedAt": utc_now(),
    }
    append_audit({
        "type": "mission.risk_guard_review",
        "missionId": mission.get("id"),
        "approvalId": approval.get("id"),
        "actorId": "risk_guard",
        "actorProvenance": "backend_deterministic_policy",
        "decision": decision,
        "reason": reason,
        "ruleVersion": rule_version,
        "payloadDigest": expected_digest,
    })
    return decision, reason


def create_mission(payload: dict, status: str = "queued", allow_model_override: bool = False) -> dict:
    raw_prompt = str(payload.get("prompt") or payload.get("detail") or payload.get("title") or "Review mission packet.").strip()
    if contains_potential_secret(raw_prompt):
        raise RequestError("Potential secret detected. Submit intent without credentials.", 422)
    prompt = redact_text(raw_prompt, 8000)
    agent_id = str(payload.get("agentId") or payload.get("owner") or "manager")
    requester = str(payload.get("requester") or "human")
    tool_id = str(payload.get("toolId") or "manager_mission")
    tool_policy = get_tool_policy(tool_id) or {}
    risk = effective_risk(payload.get("risk"), tool_policy.get("risk"))
    hard_gate_reasons = [] if tool_id in {"manager_delegate", "manager_mission"} else _high_impact_reasons(tool_id, prompt, risk)
    if hard_gate_reasons:
        risk = "high"
    target_id = str(payload.get("targetId") or pick_target_for_task(prompt))
    model_tier, budget = resolve_budget(payload, agent_id, tool_policy, allow_model_override=allow_model_override)
    report_type = str(payload.get("reportType") or report_type_for_prop(target_id))
    parent_mission_id = safe_reference(payload.get("parentMissionId"))
    supplied_scope_digest = str(payload.get("_idempotencyScopeDigest") or "")
    request_scope_digest = (
        supplied_scope_digest
        if re.fullmatch(r"[0-9a-f]{64}", supplied_scope_digest)
        else payload_digest(
            "mission-request-v2",
            requester,
            tool_id,
            agent_id,
            prompt,
            target_id,
            risk,
            model_tier,
            budget,
            report_type,
            parent_mission_id,
        )
    )
    raw_idempotency_key = str(payload.get("idempotencyKey") or "").strip()
    if raw_idempotency_key and not SAFE_IDEMPOTENCY_PATTERN.fullmatch(raw_idempotency_key):
        raise RequestError("Idempotency key must be a short safe identifier.", 422)
    idempotency_key = raw_idempotency_key
    existing = find_mission_by_idempotency(idempotency_key)
    if existing:
        if same_idempotency_scope(
            existing,
            requester,
            tool_id,
            agent_id,
            request_scope_digest,
        ):
            return existing
        raise RequestError("Idempotency key is already used by a different mission scope.", 409)

    now = utc_now()
    mission = {
        "id": safe_id(payload.get("id"), "mission"),
        "title": redact_text(str(payload.get("title") or prompt[:72]), 160),
        "detail": prompt,
        "owner": agent_id,
        "requester": requester,
        "parentMissionId": parent_mission_id,
        "subtaskIds": payload.get("subtaskIds") if isinstance(payload.get("subtaskIds"), list) else [],
        "toolId": tool_id,
        "targetId": target_id,
        "status": status,
        "risk": risk,
        "modelTier": model_tier,
        "reportType": report_type,
        "idempotencyKey": idempotency_key or None,
        "idempotencyScopeDigest": request_scope_digest if idempotency_key else None,
        "budget": budget,
        "result": "",
        "artifactPath": None,
        "reportIds": [],
        "attemptCount": 0,
        "createdAt": now,
        "updatedAt": now,
        "completedAt": None,
    }
    eligibility = auto_guarded_eligibility(mission, require_operator_mode=True)
    auto_eligible = status == "queued" and eligibility.get("eligible") is True
    approval_required = bool(
        tool_policy.get("approvalRequired", False)
        or tool_id in APPROVAL_REQUIRED
        or risk == "high"
    )
    guard = load_orchestration_contract().get("costRateGuard") or {}
    approval_minutes_key = "autoApprovalTtlMinutes" if auto_eligible else "approvalTtlMinutes"
    approval_minutes_default = 1440 if auto_eligible else 15
    approval_minutes = clamp_int(guard.get(approval_minutes_key), approval_minutes_default, 1, 1440)
    approval = {
        "required": approval_required,
        "id": safe_id(None, "approval") if approval_required else None,
        "state": "pending" if approval_required else "not_required",
        "gateMode": "backend_auto_review" if auto_eligible else ("human_review" if approval_required else "not_required"),
        "requiredActors": (
            ["risk_guard"]
            if auto_eligible and approval_required
            else (required_approval_actors(risk) if approval_required else [])
        ),
        "decisions": [],
        "expiresAt": utc_after(approval_minutes) if approval_required else None,
        "consumedAt": None,
        "payloadDigest": None,
    }
    mission["approval"] = approval
    mission["executionMode"] = "auto_guarded" if auto_eligible else "manual_guarded"
    mission["autoEligible"] = bool(auto_eligible)
    mission["requiresHumanApproval"] = bool(approval_required and not auto_eligible)
    if auto_eligible:
        authorization_id = safe_id(None, "auto-auth")
        mission["autoQueuedAt"] = now
        mission["phase"] = "auto_guarded_queued"
        mission["execution"] = {
            "schema": "auto-guarded-execution-v1",
            "authorizationId": authorization_id,
            "authorizationIssuedAt": now,
            "dispatchState": "queued",
            "autoQueuedAt": now,
            "workerId": None,
            "leaseId": None,
            "startedAt": None,
            "heartbeatAt": None,
            "timeoutAt": None,
            "processStarted": False,
            "processTreeTerminated": False,
            "nextAttemptAt": None,
            "completedAt": None,
        }
    elif approval_required and status == "queued":
        mission["status"] = "waiting_approval"
    if approval_required:
        approval["payloadDigest"] = mission_payload_digest(mission)
    if auto_eligible:
        decision, reason = backend_auto_guard_review(mission, approval)
        approval["state"] = "approved" if decision == "approved" else "rejected"
        if decision != "approved":
            mission["status"] = "blocked"
            mission["phase"] = "auto_guarded_review_blocked"
            mission["errorCode"] = reason
            mission["result"] = "Backend Risk Guard rejected automatic execution. No tool executed."
            mission["execution"]["dispatchState"] = "blocked"
            mission["completedAt"] = utc_now()
    with MISSIONS_LOCK:
        missions = load_missions()
        if idempotency_key:
            existing = next((item for item in missions if item.get("idempotencyKey") == idempotency_key), None)
            if existing:
                if same_idempotency_scope(
                    existing,
                    requester,
                    tool_id,
                    agent_id,
                    request_scope_digest,
                ):
                    return existing
                raise RequestError("Idempotency key is already used by a different mission scope.", 409)
        missions.insert(0, mission)
        save_missions(missions)
    append_audit({
        "type": "mission.created",
        "missionId": mission["id"],
        "ownerAgentId": agent_id,
        "toolId": tool_id,
        "targetId": target_id,
        "status": mission["status"],
        "modelTier": model_tier,
        "budget": budget,
        "executionMode": mission["executionMode"],
        "autoEligible": mission["autoEligible"],
        "requiresHumanApproval": mission["requiresHumanApproval"],
        "hardGateReasons": hard_gate_reasons,
    })
    if auto_eligible and mission["status"] == "queued":
        append_audit({
            "type": "mission.auto_enqueued",
            "missionId": mission["id"],
            "ownerAgentId": agent_id,
            "toolId": tool_id,
            "executionMode": "auto_guarded",
            "autoQueuedAt": mission["autoQueuedAt"],
            "approvalState": approval["state"],
            "gateMode": approval["gateMode"],
        })
        MISSION_WORKER_WAKE.set()
    return mission


def role_default_target_id(agent_id: str) -> str:
    rules = (load_orchestration_contract().get("managerAutoDelegation") or {}).get("specialistRules") or []
    for rule in rules:
        if isinstance(rule, dict) and str(rule.get("agentId") or "") == agent_id:
            target_id = str(rule.get("targetPropId") or "")
            if target_id and find_room_prop(target_id):
                return target_id
    fallback = {
        "manager": "mission_strategy_table",
        "ceo": "mission_strategy_table",
        "ea_developer": "terminal_workstation",
        "backtest_analyst": "left_analytics_console",
        "optimization_agent": "right_server_racks",
        "vps_watch": "right_status_crystals",
        "telegram_ops": "right_tool_console",
        "risk_guard": "left_audit_crystals",
        "codex_mcp_operator": "codex_mcp_portal",
        "mission_archivist": "left_server_racks",
    }.get(agent_id, "mission_strategy_table")
    return fallback if find_room_prop(fallback) else MISSION_STRATEGY_TABLE_PROP_ID


def allowed_targets_for_agent(agent_id: str) -> set[str]:
    rules = (load_orchestration_contract().get("managerAutoDelegation") or {}).get("specialistRules") or []
    targets = {
        str(rule.get("targetPropId"))
        for rule in rules
        if isinstance(rule, dict)
        and str(rule.get("agentId") or "") == agent_id
        and find_room_prop(str(rule.get("targetPropId") or ""))
    }
    targets.add(role_default_target_id(agent_id))
    return targets


def target_for_agent_goal(agent_id: str, goal: str) -> str:
    rules = (load_orchestration_contract().get("managerAutoDelegation") or {}).get("specialistRules") or []
    lower_goal = str(goal or "").lower()
    matches = [
        rule
        for rule in rules
        if isinstance(rule, dict)
        and str(rule.get("agentId") or "") == agent_id
        and find_room_prop(str(rule.get("targetPropId") or ""))
        and any(
            keyword_matches(lower_goal, str(keyword))
            for keyword in (rule.get("keywords") if isinstance(rule.get("keywords"), list) else [])
        )
    ]
    if matches:
        selected = max(matches, key=lambda item: int(item.get("priority", 0)))
        return str(selected.get("targetPropId"))
    return role_default_target_id(agent_id)


def manager_delegate(payload: dict, *, backend_risk_context: str | None = None) -> dict:
    requester = str(payload.get("agentId") or "manager")
    permission = evaluate_tool_permission(requester, "manager_delegate")
    if not permission.get("allowed"):
        return {"ok": False, "kind": "permission_denied", "message": permission["message"], "_httpStatus": 403}

    goal = str(payload.get("goal") or payload.get("prompt") or "").strip()
    if not goal:
        return {"ok": False, "kind": "invalid_request", "message": "Manager goal is required.", "_httpStatus": 422}
    if contains_potential_secret(goal):
        append_audit({"type": "guard.secret_blocked", "agentId": requester, "surface": "manager_delegate"})
        return {"ok": False, "kind": "secret_blocked", "message": "Potential secret detected. Remove credentials and submit an intent only.", "_httpStatus": 422}
    forbidden_fields = sorted(
        field for field in ("toolId", "modelTier", "budget", "risk", "approval", "approved")
        if field in payload
    )
    if forbidden_fields:
        append_audit({
            "type": "manager.delegation_untrusted_fields_blocked",
            "agentId": requester,
            "fieldCount": len(forbidden_fields),
        })
        return {
            "ok": False,
            "kind": "untrusted_execution_fields",
            "message": "Manager delegation selects tool, model, budget, risk, and approval on the backend.",
            "_httpStatus": 422,
        }

    idempotency_key = str(payload.get("idempotencyKey") or "").strip()
    if idempotency_key and not SAFE_IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        return {"ok": False, "kind": "invalid_idempotency_key", "message": "Idempotency key must be a short safe identifier.", "_httpStatus": 422}
    requested_owner = str(payload.get("requestedOwnerAgentId") or "").strip()
    requested_target = str(payload.get("requestedTargetId") or "").strip()
    delegation_scope_digest = payload_digest(
        "manager-delegation-v2",
        requester,
        goal,
        requested_owner,
        requested_target,
    )
    existing = find_mission_by_idempotency(idempotency_key)
    if existing and same_idempotency_scope(
        existing,
        requester,
        "manager_delegate",
        "manager",
        delegation_scope_digest,
    ):
        subtask_ids = existing.get("subtaskIds") or []
        subtasks = [mission for mission in load_missions() if mission.get("id") in subtask_ids]
        reports = [report for report in load_runtime_reports() if report.get("linkedMissionId") == existing.get("id")]
        return {"ok": True, "kind": "manager_plan", "parent": existing, "subtasks": subtasks, "report": reports[0] if reports else None, "idempotentReplay": True}
    if existing:
        return {"ok": False, "kind": "idempotency_conflict", "message": "Idempotency key is already used by a different mission scope.", "_httpStatus": 409}

    contract = load_orchestration_contract()
    manager_rules = contract.get("managerAutoDelegation") if isinstance(contract.get("managerAutoDelegation"), dict) else {}
    guard = contract.get("costRateGuard") if isinstance(contract.get("costRateGuard"), dict) else {}
    combined_risk_context = f"{goal}\n{str(backend_risk_context or '')}"
    delegation_high_impact_reasons = _high_impact_reasons(
        str(manager_rules.get("defaultSubtaskToolId") or "codex_cli_task"),
        combined_risk_context,
        "medium",
    )
    direct_rule = None
    if requested_owner:
        known_agents = {str(item.get("id")) for item in load_agent_contracts()}
        if (
            not SAFE_ID_PATTERN.fullmatch(requested_owner)
            or requested_owner not in known_agents
            or requested_owner in {"manager", "ceo"}
        ):
            return {
                "ok": False,
                "kind": "invalid_requested_owner",
                "message": "requestedOwnerAgentId must name one specialist Agent from the backend roster.",
                "_httpStatus": 422,
            }
        requested_target = requested_target or target_for_agent_goal(requested_owner, goal)
        if (
            not SAFE_ID_PATTERN.fullmatch(requested_target)
            or requested_target not in allowed_targets_for_agent(requested_owner)
        ):
            return {
                "ok": False,
                "kind": "invalid_requested_target",
                "message": "requestedTargetId is not an approved workstation for this specialist.",
                "_httpStatus": 422,
            }
        matched_rule = next((
            rule
            for rule in (manager_rules.get("specialistRules") or [])
            if isinstance(rule, dict)
            and str(rule.get("agentId") or "") == requested_owner
            and str(rule.get("targetPropId") or "") == requested_target
        ), None)
        direct_rule = matched_rule or {
            "agentId": requested_owner,
            "targetPropId": requested_target,
            "reportType": report_type_for_prop(requested_target),
            "modelTier": role_default_model_tier(requested_owner),
        }
    elif requested_target:
        return {
            "ok": False,
            "kind": "requested_owner_required",
            "message": "requestedTargetId requires requestedOwnerAgentId.",
            "_httpStatus": 422,
        }
    max_per_hour = clamp_int(guard.get("managerDelegationsPerHour"), 30, 1, 500)
    cooldown = clamp_int(guard.get("managerDelegationCooldownSeconds"), 2, 0, 60)
    allowed, retry_after = check_rate_limit(f"delegate:{requester}", max_per_hour, cooldown)
    if not allowed:
        append_audit({"type": "guard.rate_limited", "agentId": requester, "toolId": "manager_delegate", "retryAfterSeconds": retry_after})
        return {"ok": False, "kind": "rate_limited", "message": "Manager delegation rate limit reached.", "retryAfterSeconds": retry_after, "_httpStatus": 429}

    parent = create_mission({
        "title": f"Manager plan: {goal[:96]}",
        "prompt": goal,
        "agentId": "manager",
        "requester": requester,
        "toolId": "manager_delegate",
        "targetId": str(manager_rules.get("summaryTargetPropId") or "mission_strategy_table"),
        "risk": "low",
        "modelTier": "manager_quality",
        "reportType": "mission_plan",
        "idempotencyKey": idempotency_key,
        "_idempotencyScopeDigest": delegation_scope_digest,
    }, status="queued", allow_model_override=True)

    max_subtasks = clamp_int(manager_rules.get("maxSubtasks"), 6, 1, 12)
    matched_rules = []
    seen = set()
    if requested_owner:
        matched_rules = [direct_rule]
    else:
        for rule in sorted((manager_rules.get("specialistRules") or []), key=lambda item: int(item.get("priority", 0)), reverse=True):
            if not isinstance(rule, dict):
                continue
            keywords = rule.get("keywords") if isinstance(rule.get("keywords"), list) else []
            if not any(keyword_matches(goal.lower(), token) for token in keywords):
                continue
            key = (rule.get("agentId"), rule.get("targetPropId"), rule.get("reportType"))
            if key in seen:
                continue
            seen.add(key)
            matched_rules.append(rule)
            if len(matched_rules) >= max_subtasks:
                break

    if not matched_rules:
        matched_rules = [manager_rules.get("fallback") or {
            "agentId": "manager",
            "targetPropId": "mission_strategy_table",
            "reportType": "mission_plan",
            "modelTier": "manager_quality",
        }]

    subtasks = []
    default_subtask_tool_id = str(manager_rules.get("defaultSubtaskToolId") or "codex_cli_task")
    for index, rule in enumerate(matched_rules, start=1):
        agent_id = str(rule.get("agentId") or "manager")
        target_id = str(rule.get("targetPropId") or "mission_strategy_table")
        tool_id = str(rule.get("toolId") or default_subtask_tool_id)
        tool_policy = get_tool_policy(tool_id) or {}
        permission = evaluate_tool_permission(agent_id, tool_id)
        if not permission.get("allowed"):
            append_audit({
                "type": "manager.delegation_policy_denied",
                "missionId": parent["id"],
                "agentId": agent_id,
                "toolId": tool_id,
                "reason": permission.get("reason"),
            })
            continue
        subtask = create_mission({
            "title": f"{agent_id}: {goal[:96]}",
            "prompt": goal,
            "agentId": agent_id,
            "requester": "manager",
            "parentMissionId": parent["id"],
            "toolId": tool_id,
            "targetId": target_id,
            "risk": (
                "high"
                if delegation_high_impact_reasons
                else str(rule.get("risk") or tool_policy.get("risk") or "medium")
            ),
            "modelTier": str(rule.get("modelTier") or role_default_model_tier(agent_id)),
            "reportType": str(rule.get("reportType") or report_type_for_prop(target_id)),
            "idempotencyKey": f"{parent['id']}:subtask:{index}",
        }, status="queued", allow_model_override=True)
        subtasks.append(subtask)

    delegated_at = utc_now()
    subtask_status_counts = summarize_missions(subtasks)["byStatus"]
    parent["subtaskIds"] = [item["id"] for item in subtasks]
    parent["status"] = "queued" if subtasks else "blocked"
    parent["phase"] = "delegated" if subtasks else "delegation_blocked"
    parent["result"] = (
        f"Manager แบ่งงานให้ Agent ผู้เชี่ยวชาญ {len(subtasks)} งานแล้ว แต่ละงานยังอยู่ภายใต้ระบบป้องกันและการอนุมัติของ Backend โดยยังไม่มีเครื่องมือจริงถูกเรียกใช้ในขั้นวางแผน"
        if subtasks
        else "ยังไม่มีงานของ Agent ผู้เชี่ยวชาญที่ผ่านสิทธิ์การใช้เครื่องมือของ Backend จึงยังไม่มีการเรียกใช้เครื่องมือจริง"
    )
    parent["delegation"] = {
        "state": "delegated",
        "mode": "deterministic_guarded_mission_queue",
        "subtaskCount": len(subtasks),
        "subtaskStatusCounts": subtask_status_counts,
        "summaryTargetId": MISSION_STRATEGY_TABLE_PROP_ID,
        "realToolExecuted": False,
        "delegatedAt": delegated_at,
    }
    parent["updatedAt"] = delegated_at
    parent["completedAt"] = None
    report = create_report({
        "type": "mission_plan",
        "title": parent["title"],
        "summary": parent["result"],
        "ownerAgentId": "manager",
        "linkedMissionId": parent["id"],
        "linkedPropId": "mission_strategy_table",
        "findings": [f"{item['owner']} -> {item['targetId']} ({item['modelTier']})" for item in subtasks],
        "nextActions": ["ตรวจ Mission ของ Agent ผู้เชี่ยวชาญแต่ละตัว", "อนุมัติเฉพาะงาน Codex ที่ระบุขอบเขตชัดเจน", "รวบรวมรายงานแบบมีโครงสร้างก่อนให้ Manager สรุปผล"],
    })
    parent["reportIds"] = [report["id"]]
    replace_mission(parent)
    if subtasks:
        parent = refresh_parent_mission(parent["id"]) or parent
        MISSION_WORKER_WAKE.set()
    append_audit({
        "type": "manager.delegated",
        "missionId": parent["id"],
        "subtaskIds": parent["subtaskIds"],
        "status": parent["status"],
        "phase": parent["phase"],
        "plannerMode": "deterministic_guarded_mission_queue",
        "highImpactReasons": delegation_high_impact_reasons,
        "realToolExecuted": False,
    })
    return {"ok": True, "kind": "manager_plan", "parent": parent, "subtasks": subtasks, "report": report, "_httpStatus": 201}


def approve_mission(mission_id: str, payload: dict) -> dict:
    with MISSIONS_LOCK:
        return _approve_mission_locked(mission_id, payload)


def _approve_mission_locked(mission_id: str, payload: dict) -> dict:
    mission = find_mission(mission_id)
    if not mission:
        return {"ok": False, "kind": "not_found", "message": "Mission not found.", "_httpStatus": 404}
    if mission.get("status") != "waiting_approval":
        return {"ok": False, "kind": "invalid_mission_state", "message": "Only waiting_approval missions can receive a decision.", "_httpStatus": 409}
    approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
    if not approval.get("required"):
        return {"ok": False, "kind": "approval_not_required", "message": "This mission does not require approval.", "_httpStatus": 409}
    if approval.get("state") in {"consumed", "rejected"}:
        return {"ok": False, "kind": "approval_closed", "message": "Approval is already closed.", "_httpStatus": 409}
    expires_at = parse_iso(approval.get("expiresAt"))
    if expires_at and datetime.now(timezone.utc) >= expires_at:
        approval["state"] = "expired"
        mission["status"] = "blocked"
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        return {"ok": False, "kind": "approval_expired", "message": "Approval expired. Create a new mission.", "_httpStatus": 409}

    expected_digest = str(approval.get("payloadDigest") or "")
    actual_digest = mission_payload_digest(mission)
    if not expected_digest or not secrets.compare_digest(expected_digest, actual_digest):
        approval["state"] = "invalidated"
        mission["approval"] = approval
        mission["status"] = "blocked"
        mission["result"] = "Approval invalidated because the mission payload changed."
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        append_audit({"type": "mission.approval_digest_mismatch", "missionId": mission_id, "approvalId": approval.get("id")})
        return {"ok": False, "kind": "approval_digest_mismatch", "message": mission["result"], "_httpStatus": 409}

    decision = str(payload.get("decision") or "").lower()
    actor_id = str(payload.get("actorId") or "human").lower()
    if decision not in {"approved", "rejected"}:
        return {"ok": False, "kind": "invalid_decision", "message": "Decision must be approved or rejected.", "_httpStatus": 422}
    if actor_id != "human":
        return {"ok": False, "kind": "backend_actor_required", "message": "Frontend may record only the local human decision. CEO and Risk Guard decisions must come from a backend-owned reviewer.", "_httpStatus": 403}
    if str(payload.get("confirmMissionId") or "") != mission_id:
        return {"ok": False, "kind": "mission_confirmation_required", "message": "Approval must explicitly confirm the same mission id.", "_httpStatus": 422}
    note = redact_text(str(payload.get("note") or ""), 1200)
    if len(note.strip()) < 12:
        return {"ok": False, "kind": "approval_note_required", "message": "An explicit local-user approval note is required.", "_httpStatus": 422}

    decisions = [item for item in (approval.get("decisions") or []) if isinstance(item, dict) and item.get("actorId") != actor_id]
    decisions.append({"actorId": actor_id, "decision": decision, "note": note, "time": utc_now(), "payloadDigest": approval.get("payloadDigest")})
    approval["decisions"] = decisions
    if decision == "rejected":
        approval["state"] = "rejected"
        mission["status"] = "blocked"
        mission["result"] = "Mission rejected at the approval gate."
    else:
        required = set(approval.get("requiredActors") or ["human"])
        risk_decision = None
        risk_reason = None
        if "risk_guard" in required:
            risk_decision, risk_reason = backend_risk_guard_review(mission, approval)
        approved_actors = {item.get("actorId") for item in decisions if item.get("decision") == "approved"}
        approved_actors = {
            item.get("actorId") for item in (approval.get("decisions") or [])
            if isinstance(item, dict) and item.get("decision") == "approved"
        }
        if risk_decision == "rejected":
            approval["state"] = "rejected"
            mission["status"] = "blocked"
            mission["result"] = f"Backend Risk Guard rejected this mission: {risk_reason}. No tool executed."
        else:
            approval["state"] = "approved" if required.issubset(approved_actors) else "pending"
            mission["status"] = "waiting_approval"
    mission["approval"] = approval
    mission["updatedAt"] = utc_now()
    replace_mission(mission)
    if mission.get("status") == "blocked":
        refresh_parent_mission(mission.get("parentMissionId"))
    append_audit({
        "type": "mission.approval_decision",
        "missionId": mission_id,
        "approvalId": approval.get("id"),
        "actorId": actor_id,
        "actorProvenance": "local_visual_office_human_confirmation",
        "decision": decision,
        "approvalState": approval["state"],
    })
    if approval["state"] == "approved":
        message = "Approval recorded. The mission remains bound to the reviewed payload digest."
    elif approval["state"] == "rejected":
        message = mission.get("result") or "Mission rejected at the approval gate."
    else:
        message = "Human decision recorded; required backend approval is still pending."
    return {"ok": True, "kind": "approval_recorded", "mission": mission, "readyToExecute": approval["state"] == "approved", "message": message}


def execute_mission(mission_id: str, payload: dict | None = None) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    if str(payload.get("confirmMissionId") or "") != mission_id:
        return {
            "ok": False,
            "kind": "mission_confirmation_required",
            "message": "Execution must explicitly confirm the same mission id.",
            "_httpStatus": 422,
        }
    mission = find_mission(mission_id)
    if not mission:
        return {"ok": False, "kind": "not_found", "message": "Mission not found.", "_httpStatus": 404}
    if mission.get("status") != "waiting_approval":
        return {"ok": False, "kind": "invalid_mission_state", "message": "Only waiting_approval missions can be executed.", "_httpStatus": 409}
    approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
    if approval.get("state") != "approved":
        return {"ok": False, "kind": "approval_required", "mission": mission, "message": "Stored mission approval is not complete.", "_httpStatus": 409}
    expires_at = parse_iso(approval.get("expiresAt"))
    if expires_at and datetime.now(timezone.utc) >= expires_at:
        approval["state"] = "expired"
        mission["status"] = "blocked"
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        refresh_parent_mission(mission.get("parentMissionId"))
        return {"ok": False, "kind": "approval_expired", "mission": mission, "message": "Stored approval expired.", "_httpStatus": 409}
    expected_digest = str(approval.get("payloadDigest") or "")
    actual_digest = mission_payload_digest(mission)
    if not expected_digest or not secrets.compare_digest(expected_digest, actual_digest):
        approval["state"] = "invalidated"
        mission["approval"] = approval
        mission["status"] = "blocked"
        mission["result"] = "Approval invalidated because the mission payload changed."
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        refresh_parent_mission(mission.get("parentMissionId"))
        append_audit({"type": "mission.execute_digest_mismatch", "missionId": mission_id, "approvalId": approval.get("id")})
        return {"ok": False, "kind": "approval_digest_mismatch", "mission": mission, "message": mission["result"], "_httpStatus": 409}

    tool_id = str(mission.get("toolId") or "")
    agent_id = str(mission.get("owner") or "manager")
    permission = evaluate_tool_permission(agent_id, tool_id)
    if not permission.get("allowed"):
        append_audit({"type": "policy.denied", "missionId": mission_id, "agentId": agent_id, "toolId": tool_id, "reason": permission.get("reason")})
        return {"ok": False, "kind": "permission_denied", "mission": mission, "message": permission["message"], "_httpStatus": 403}
    if tool_id != "codex_cli_task":
        mission["status"] = "blocked"
        mission["result"] = f"Adapter {tool_id} ยังไม่พร้อมใช้งาน งาน Live และงานที่ส่งออกภายนอกจึงยังปิดอยู่"
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        refresh_parent_mission(mission.get("parentMissionId"))
        append_audit({"type": "adapter.blocked", "missionId": mission_id, "toolId": tool_id})
        return {"ok": False, "kind": "adapter_not_implemented", "mission": mission, "message": mission["result"], "_httpStatus": 501}

    status = bridge_status()
    if status.get("codex", {}).get("status") != "ready":
        mission["status"] = "waiting_approval"
        mission["runnerStatus"] = status.get("codex", {}).get("status")
        mission["result"] = status.get("codex", {}).get("message") or "Codex Runner ยังไม่พร้อมใช้งาน"
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        append_audit({"type": "bridge.runner_blocked", "missionId": mission_id, "runnerStatus": mission["runnerStatus"]})
        return {"ok": False, "kind": "runner_not_ready", "mission": mission, "bridge": status, "message": mission["result"], "_httpStatus": 503}

    tier_id = str(mission.get("modelTier") or role_default_model_tier(agent_id))
    tier = (load_orchestration_contract().get("modelTiers") or {}).get(tier_id) or {}
    max_runs = clamp_int(tier.get("maxRunsPerHour"), 12, 1, 200)
    quota = codex_rate_limits()
    if quota.get("ok") is True and quota.get("limitReached") is True:
        append_audit({
            "type": "guard.codex_limit_reached",
            "missionId": mission_id,
            "agentId": agent_id,
            "toolId": tool_id,
            "quotaStatus": quota.get("status"),
            "quotaStale": bool(quota.get("stale", False)),
        })
        return {
            "ok": False,
            "kind": "codex_limit_reached",
            "mission": mission,
            "message": "Codex แจ้งว่าบัญชีถึง Rate Limit แล้ว ระบบจึงไม่ได้เริ่มงานใหม่ใน Runner",
            "_httpStatus": 429,
        }

    rate_key = f"real:{agent_id}:{tool_id}:{tier_id}"
    allowed, retry_after = check_rate_limit(rate_key, max_runs, consume=False)
    if not allowed:
        append_audit({"type": "guard.rate_limited", "missionId": mission_id, "agentId": agent_id, "toolId": tool_id, "retryAfterSeconds": retry_after})
        return {"ok": False, "kind": "rate_limited", "mission": mission, "message": "Real-run rate limit reached.", "retryAfterSeconds": retry_after, "_httpStatus": 429}
    if not REAL_RUN_SEMAPHORE.acquire(blocking=False):
        return {"ok": False, "kind": "runner_busy", "mission": mission, "message": "Another real runner task is active.", "_httpStatus": 429}
    allowed, retry_after = check_rate_limit(rate_key, max_runs, consume=True)
    if not allowed:
        REAL_RUN_SEMAPHORE.release()
        append_audit({"type": "guard.rate_limited", "missionId": mission_id, "agentId": agent_id, "toolId": tool_id, "retryAfterSeconds": retry_after})
        return {"ok": False, "kind": "rate_limited", "mission": mission, "message": "Real-run rate limit reached.", "retryAfterSeconds": retry_after, "_httpStatus": 429}

    budget = mission.get("budget") if isinstance(mission.get("budget"), dict) else {}
    timeout_seconds = clamp_int(budget.get("timeoutSeconds"), 120, 15, 600)
    output_limit = clamp_int(budget.get("outputLimitChars"), 7000, 1000, 20000)
    try:
        approval["state"] = "consumed"
        approval["consumedAt"] = utc_now()
        mission["approval"] = approval
        mission["status"] = "running"
        mission["attemptCount"] = int(mission.get("attemptCount") or 0) + 1
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        append_audit({
            "type": "bridge.codex_run_start",
            "missionId": mission_id,
            "ownerAgentId": agent_id,
            "toolId": tool_id,
            "modelTier": tier_id,
            "timeoutSeconds": timeout_seconds,
            "outputLimitChars": output_limit,
        })
        runner = run_safe_command(
            [
                str(CODEX_RUNNER_PYTHON),
                str(CODEX_RUNNER_SCRIPT),
                "--run",
                "--execution-mode", "manual_guarded",
                "--agent-id", agent_id,
                "--mission-id", mission_id,
                "--prompt-stdin",
                "--timeout", str(timeout_seconds),
                "--model-tier", tier_id,
                "--output-limit", str(output_limit),
            ],
            timeout=timeout_seconds + 30,
            output_limit=max(40000, output_limit + 10000),
            input_text=str(mission.get("detail") or ""),
        )
        try:
            result = json.loads(runner["output"]) if runner["output"] else {}
        except json.JSONDecodeError:
            result = {"ok": False, "status": "failed", "message": "Runner returned invalid JSON."}

        final_message = redact_text((result.get("finalMessage") or "").strip(), output_limit)
        mission["status"] = "completed" if result.get("ok") else "failed"
        mission["errorCode"] = None if result.get("ok") else str(result.get("status") or result.get("exitCode") or "runner_failed")
        mission["result"] = final_message or redact_text(str(result.get("message") or "Runner did not return a report."), output_limit)
        mission["artifactPath"] = result.get("artifacts", {}).get("final")
        mission["updatedAt"] = utc_now()
        mission["completedAt"] = mission["updatedAt"]
        report = create_report({
            "type": mission.get("reportType") or "bridge_status_report",
            "title": mission.get("title"),
            "summary": mission["result"],
            "ownerAgentId": agent_id,
            "linkedMissionId": mission_id,
            "linkedPropId": mission.get("targetId"),
            "status": "ready" if result.get("ok") else "blocked",
            "artifacts": [mission["artifactPath"]] if mission.get("artifactPath") else [],
            "risks": [] if result.get("ok") else [mission.get("errorCode")],
        })
        mission["reportIds"] = [report["id"]]
        replace_mission(mission)
        refresh_parent_mission(mission.get("parentMissionId"))
        append_audit({
            "type": "bridge.codex_run_end",
            "missionId": mission_id,
            "ownerAgentId": agent_id,
            "toolId": tool_id,
            "modelTier": tier_id,
            "durationMs": result.get("durationMs", runner.get("durationMs")),
            "outputChars": len(final_message),
            "status": mission["status"],
        })
        return {
            "ok": bool(result.get("ok")),
            "kind": "codex_cli_task",
            "mission": mission,
            "report": report,
            "targetId": mission.get("targetId"),
            "bridge": bridge_status(),
            "message": redact_text(str(result.get("message") or mission["result"]), 1200),
            "finalMessage": final_message,
            "artifacts": sanitize_json_value(result.get("artifacts", {})),
            "usage": sanitize_json_value(result.get("usage", {})),
        }
    except Exception:
        mission["status"] = "failed"
        mission["errorCode"] = "internal_runner_error"
        mission["result"] = "Guarded Runner เกิดข้อผิดพลาดภายใน ระบบหยุดแบบปลอดภัยและไม่ลองรันซ้ำอัตโนมัติ"
        mission["updatedAt"] = utc_now()
        mission["completedAt"] = mission["updatedAt"]
        try:
            replace_mission(mission)
            refresh_parent_mission(mission.get("parentMissionId"))
            append_audit({"type": "bridge.codex_run_exception", "missionId": mission_id, "toolId": tool_id, "status": "failed"})
        except Exception:
            pass
        return {"ok": False, "kind": "internal_runner_error", "mission": mission, "message": mission["result"], "_httpStatus": 500}
    finally:
        invalidate_codex_rate_limit_cache()
        REAL_RUN_SEMAPHORE.release()


def mission_worker_config() -> dict:
    contract = load_orchestration_contract()
    configured = contract.get("missionWorker") if isinstance(contract.get("missionWorker"), dict) else {}
    return {
        "idlePollSeconds": clamp_int(configured.get("idlePollSeconds"), 5, 1, 60),
        "heartbeatSeconds": clamp_int(configured.get("heartbeatSeconds"), 10, 2, 60),
        "runnerUnavailableBackoffSeconds": clamp_int(
            configured.get("runnerUnavailableBackoffSeconds"), 60, 5, 900
        ),
        "quotaBackoffSeconds": clamp_int(configured.get("quotaBackoffSeconds"), 60, 5, 900),
        "busyBackoffSeconds": clamp_int(configured.get("busyBackoffSeconds"), 5, 1, 60),
        "reconcileIntervalSeconds": clamp_int(configured.get("reconcileIntervalSeconds"), 60, 10, 600),
        "timeoutWatchdogIntervalSeconds": clamp_int(
            configured.get("timeoutWatchdogIntervalSeconds"),
            10,
            2,
            60,
        ),
        "timeoutWatchdogGraceSeconds": clamp_int(
            configured.get("timeoutWatchdogGraceSeconds"),
            45,
            5,
            300,
        ),
    }


def update_mission_worker_state(**values: object) -> None:
    with MISSION_WORKER_LOCK:
        MISSION_WORKER_STATE.update(values)


def auto_execution_authorization_error(mission: dict, *, require_operator_mode: bool = True) -> str | None:
    """Validate the immutable, digest-bound marker required for automatic execution."""
    execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
    approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
    if mission.get("autoEligible") is not True or mission.get("executionMode") != "auto_guarded":
        return "auto_authorization_marker_missing"
    if execution.get("schema") != "auto-guarded-execution-v1":
        return "auto_execution_schema_invalid"
    authorization_id = str(execution.get("authorizationId") or "")
    if not authorization_id or not SAFE_ID_PATTERN.fullmatch(authorization_id):
        return "auto_authorization_id_invalid"
    auto_queued_at = str(mission.get("autoQueuedAt") or "")
    if (
        not auto_queued_at
        or str(execution.get("autoQueuedAt") or "") != auto_queued_at
        or str(execution.get("authorizationIssuedAt") or "") != auto_queued_at
    ):
        return "auto_authorization_time_mismatch"
    if not approval.get("required") or approval.get("gateMode") != "backend_auto_review":
        return "auto_approval_gate_invalid"
    if set(approval.get("requiredActors") or []) != {"risk_guard"}:
        return "auto_required_actors_invalid"
    if approval.get("state") != "approved":
        return "auto_approval_not_approved"
    expected_digest = str(approval.get("payloadDigest") or "")
    if not expected_digest or not secrets.compare_digest(expected_digest, mission_payload_digest(mission)):
        return "auto_approval_digest_mismatch"
    approved_review = next(
        (
            item
            for item in (approval.get("decisions") or [])
            if isinstance(item, dict)
            and item.get("actorId") == "risk_guard"
            and item.get("actorProvenance") == "backend_auto_review"
            and item.get("decision") == "approved"
            and secrets.compare_digest(str(item.get("payloadDigest") or ""), expected_digest)
        ),
        None,
    )
    if not approved_review:
        return "auto_backend_review_missing"
    expires_at = parse_iso(approval.get("expiresAt"))
    if expires_at and datetime.now(timezone.utc) >= expires_at:
        return "auto_approval_expired"
    eligibility = auto_guarded_eligibility(mission, require_operator_mode=require_operator_mode)
    if not eligibility.get("eligible"):
        return str((eligibility.get("reasons") or ["auto_guard_policy_denied"])[0])
    return None


def block_auto_mission(mission_id: str, reason: str) -> dict | None:
    blocked = None
    parent_id = None
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            if mission.get("id") != mission_id or mission.get("status") != "queued":
                continue
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
            if approval.get("state") == "approved":
                approval["state"] = "invalidated"
            mission["approval"] = approval
            mission["status"] = "blocked"
            mission["phase"] = "auto_guarded_authorization_blocked"
            mission["errorCode"] = redact_text(str(reason or "auto_guard_policy_denied"), 120)
            mission["result"] = (
                "ระบบหยุดการทำงานอัตโนมัติ เพราะตรวจสอบเครื่องหมายอนุญาตหรือกติกาความปลอดภัยของ Backend ไม่ผ่าน โดยยังไม่มีการเรียกใช้เครื่องมือจริง"
            )
            mission["updatedAt"] = utc_now()
            mission["completedAt"] = mission["updatedAt"]
            execution["dispatchState"] = "blocked"
            execution["heartbeatAt"] = mission["updatedAt"]
            execution["completedAt"] = mission["updatedAt"]
            mission["execution"] = execution
            blocked = mission
            parent_id = safe_reference(mission.get("parentMissionId"))
            break
        if blocked:
            save_missions(missions)
    if not blocked:
        return None
    append_audit({
        "type": "mission.auto_authorization_blocked",
        "missionId": mission_id,
        "ownerAgentId": blocked.get("owner"),
        "toolId": blocked.get("toolId"),
        "reason": blocked.get("errorCode"),
        "realToolExecuted": False,
    })
    if parent_id:
        refresh_parent_mission(parent_id)
    return blocked


def defer_auto_mission(mission_id: str, reason: str, retry_after_seconds: int) -> dict | None:
    deferred = None
    retry_after_seconds = max(1, min(3600, int(retry_after_seconds)))
    next_attempt = (datetime.now(timezone.utc) + timedelta(seconds=retry_after_seconds)).isoformat()
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            if mission.get("id") != mission_id or mission.get("status") != "queued":
                continue
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            if (
                mission.get("autoEligible") is not True
                or mission.get("executionMode") != "auto_guarded"
                or execution.get("schema") != "auto-guarded-execution-v1"
            ):
                return None
            mission["phase"] = "auto_guarded_deferred"
            mission["runnerStatus"] = redact_text(str(reason), 80)
            mission["updatedAt"] = utc_now()
            execution["dispatchState"] = "deferred"
            execution["nextAttemptAt"] = next_attempt
            execution["lastDeferredReason"] = redact_text(str(reason), 120)
            execution["deferralCount"] = int(execution.get("deferralCount") or 0) + 1
            mission["execution"] = execution
            deferred = mission
            break
        if deferred:
            save_missions(missions)
    if deferred:
        append_audit({
            "type": "mission.auto_deferred",
            "missionId": mission_id,
            "ownerAgentId": deferred.get("owner"),
            "toolId": deferred.get("toolId"),
            "reason": reason,
            "retryAfterSeconds": retry_after_seconds,
            "approvalConsumed": False,
            "realToolExecuted": False,
        })
    return deferred


def find_next_auto_mission() -> dict | None:
    if load_operator_mode_record().get("mode") != "auto_guarded":
        return None
    now = datetime.now(timezone.utc)
    candidates = []
    invalid: tuple[str, str] | None = None
    with MISSIONS_LOCK:
        for mission in load_missions():
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            explicitly_auto = (
                mission.get("status") == "queued"
                and mission.get("autoEligible") is True
                and mission.get("executionMode") == "auto_guarded"
            )
            if not explicitly_auto:
                continue
            error = auto_execution_authorization_error(mission, require_operator_mode=True)
            if error:
                invalid = (str(mission.get("id") or ""), error)
                break
            if execution.get("dispatchState") not in {"queued", "deferred"}:
                invalid = (str(mission.get("id") or ""), "auto_dispatch_state_invalid")
                break
            next_attempt = parse_iso(execution.get("nextAttemptAt"))
            if next_attempt and now < next_attempt:
                continue
            candidates.append(mission)
    if invalid and invalid[0]:
        block_auto_mission(*invalid)
        return None
    if not candidates:
        return None
    return min(candidates, key=lambda item: str(item.get("autoQueuedAt") or item.get("createdAt") or ""))


def claim_auto_mission(mission_id: str, worker_id: str) -> dict | None:
    claimed = None
    parent_id = None
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            if mission.get("id") != mission_id or mission.get("status") != "queued":
                continue
            error = auto_execution_authorization_error(mission, require_operator_mode=True)
            if error:
                break
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            if execution.get("dispatchState") not in {"queued", "deferred"}:
                break
            next_attempt = parse_iso(execution.get("nextAttemptAt"))
            if next_attempt and datetime.now(timezone.utc) < next_attempt:
                break
            now = utc_now()
            lease_id = safe_id(None, "lease")
            budget = mission.get("budget") if isinstance(mission.get("budget"), dict) else {}
            timeout_seconds = clamp_int(budget.get("timeoutSeconds"), 120, 15, 600)
            approval = mission.get("approval") if isinstance(mission.get("approval"), dict) else {}
            approval["state"] = "consumed"
            approval["consumedAt"] = now
            mission["approval"] = approval
            mission["status"] = "running"
            mission["phase"] = "auto_guarded_running"
            mission["attemptCount"] = int(mission.get("attemptCount") or 0) + 1
            mission["startedAt"] = now
            mission["heartbeatAt"] = now
            mission["updatedAt"] = now
            execution.update({
                "dispatchState": "running",
                "workerId": worker_id,
                "leaseId": lease_id,
                "startedAt": now,
                "heartbeatAt": now,
                "timeoutAt": (datetime.now(timezone.utc) + timedelta(seconds=timeout_seconds)).isoformat(),
                "processStarted": False,
                "processTreeTerminated": False,
                "nextAttemptAt": None,
            })
            mission["execution"] = execution
            claimed = mission
            parent_id = safe_reference(mission.get("parentMissionId"))
            break
        if claimed:
            save_missions(missions)
    if not claimed:
        return None
    append_audit({
        "type": "mission.auto_claimed",
        "missionId": mission_id,
        "ownerAgentId": claimed.get("owner"),
        "toolId": claimed.get("toolId"),
        "workerId": worker_id,
        "leaseId": (claimed.get("execution") or {}).get("leaseId"),
        "attemptCount": claimed.get("attemptCount"),
        "approvalState": "consumed",
    })
    if parent_id:
        refresh_parent_mission(parent_id)
    return claimed


def heartbeat_auto_mission(mission_id: str, lease_id: str, stop_event: threading.Event, interval: int) -> None:
    while not stop_event.wait(interval):
        heartbeat_at = utc_now()
        updated = False
        with MISSIONS_LOCK:
            missions = load_missions()
            for mission in missions:
                execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
                if (
                    mission.get("id") == mission_id
                    and mission.get("status") == "running"
                    and execution.get("leaseId") == lease_id
                    and execution.get("dispatchState") == "running"
                ):
                    mission["heartbeatAt"] = heartbeat_at
                    mission["updatedAt"] = heartbeat_at
                    execution["heartbeatAt"] = heartbeat_at
                    mission["execution"] = execution
                    updated = True
                    break
            if updated:
                save_missions(missions)
        if not updated:
            return
        update_mission_worker_state(heartbeatAt=heartbeat_at)


def reconcile_timed_out_running_missions() -> int:
    """Fail closed when an auto-run lease remains blue/running past its hard deadline."""
    config = mission_worker_config()
    now = datetime.now(timezone.utc)
    candidates: list[tuple[str, str]] = []
    for mission in load_missions():
        execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
        timeout_at = parse_iso(execution.get("timeoutAt"))
        if (
            mission.get("status") != "running"
            or mission.get("executionMode") != "auto_guarded"
            or execution.get("schema") != "auto-guarded-execution-v1"
            or execution.get("dispatchState") != "running"
            or not execution.get("leaseId")
            or not timeout_at
            or now < timeout_at + timedelta(seconds=config["timeoutWatchdogGraceSeconds"])
        ):
            continue
        candidates.append((str(mission.get("id") or ""), str(execution.get("leaseId") or "")))

    reconciled: list[dict] = []
    for mission_id, lease_id in candidates:
        if not mission_id or not lease_id:
            continue
        tree_terminated: bool | None = None
        process_was_started = False
        with MISSION_WORKER_LOCK:
            current_mission_id = str(MISSION_WORKER_STATE.get("currentMissionId") or "")
        if current_mission_id == mission_id:
            with MISSION_WORKER_PROCESS_LOCK:
                active_process = MISSION_WORKER_PROCESS
                if active_process is not None:
                    process_was_started = True
                    if active_process.poll() is None:
                        tree_terminated = _terminate_command_process_tree(
                            active_process,
                            MISSION_WORKER_JOB_HOLDER,
                        )

        failed = None
        parent_id = None
        with MISSIONS_LOCK:
            missions = load_missions()
            for mission in missions:
                execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
                timeout_at = parse_iso(execution.get("timeoutAt"))
                if (
                    mission.get("id") != mission_id
                    or mission.get("status") != "running"
                    or execution.get("leaseId") != lease_id
                    or execution.get("dispatchState") != "running"
                    or not timeout_at
                    or datetime.now(timezone.utc)
                    < timeout_at + timedelta(seconds=config["timeoutWatchdogGraceSeconds"])
                ):
                    continue
                failed_at = utc_now()
                mission["status"] = "failed"
                mission["phase"] = "auto_worker_timeout_watchdog"
                mission["errorCode"] = "auto_worker_timeout"
                mission["result"] = (
                    "งานเกินเวลาที่กำหนดและไม่ส่งผลลัพธ์กลับมา ระบบจึงหยุด Process Tree "
                    "และปิด Mission แบบปลอดภัยโดยไม่ลองรันซ้ำอัตโนมัติ"
                )
                mission["updatedAt"] = failed_at
                mission["heartbeatAt"] = failed_at
                mission["completedAt"] = failed_at
                execution["dispatchState"] = "failed"
                execution["heartbeatAt"] = failed_at
                execution["completedAt"] = failed_at
                execution["watchdogTriggeredAt"] = failed_at
                execution["processStarted"] = bool(
                    process_was_started or execution.get("processStarted")
                )
                if tree_terminated is not None:
                    execution["processTreeTerminated"] = bool(tree_terminated)
                execution["automaticRetry"] = False
                mission["execution"] = execution
                failed = mission
                parent_id = safe_reference(mission.get("parentMissionId"))
                break
            if failed:
                save_missions(missions)
        if not failed:
            continue

        try:
            report = create_report({
                "type": failed.get("reportType") or "bridge_status_report",
                "title": failed.get("title") or "Mission timeout",
                "summary": failed["result"],
                "ownerAgentId": failed.get("owner"),
                "linkedMissionId": mission_id,
                "linkedPropId": failed.get("targetId"),
                "status": "blocked",
                "risks": ["auto_worker_timeout"],
            })
            with MISSIONS_LOCK:
                missions = load_missions()
                for mission in missions:
                    if (
                        mission.get("id") == mission_id
                        and mission.get("status") == "failed"
                        and mission.get("errorCode") == "auto_worker_timeout"
                    ):
                        mission["reportIds"] = list(dict.fromkeys([
                            *(mission.get("reportIds") or []),
                            report["id"],
                        ]))
                        failed = mission
                        break
                save_missions(missions)
        except Exception:
            # The mission failure itself is already durable. A report write
            # failure must never return the card to running or trigger a retry.
            pass
        append_audit({
            "type": "mission.auto_timeout_watchdog",
            "missionId": mission_id,
            "ownerAgentId": failed.get("owner"),
            "toolId": failed.get("toolId"),
            "leaseId": lease_id,
            "processTreeTerminated": tree_terminated,
            "automaticRetry": False,
        })
        if parent_id:
            refresh_parent_mission(parent_id)
        reconciled.append(failed)

    if reconciled:
        update_mission_worker_state(lastError="auto_worker_timeout")
    return len(reconciled)


def finish_auto_mission(mission_id: str, lease_id: str, runner: dict, result: dict) -> dict | None:
    current = find_mission(mission_id)
    execution = current.get("execution") if isinstance((current or {}).get("execution"), dict) else {}
    if not current or current.get("status") != "running" or execution.get("leaseId") != lease_id:
        append_audit({
            "type": "mission.auto_finish_lease_lost",
            "missionId": mission_id,
            "leaseId": lease_id,
            "realToolExecuted": bool(runner.get("processStarted")),
        })
        return None
    budget = current.get("budget") if isinstance(current.get("budget"), dict) else {}
    output_limit = clamp_int(budget.get("outputLimitChars"), 7000, 1000, 20000)
    final_message = redact_text(str(result.get("finalMessage") or "").strip(), output_limit)
    succeeded = result.get("ok") is True
    summary = final_message or redact_text(
        str(result.get("message") or "Codex Worker ที่มีระบบป้องกันไม่ได้ส่งรายงานกลับมา"),
        output_limit,
    )
    artifacts = result.get("artifacts") if isinstance(result.get("artifacts"), dict) else {}
    artifact_path = safe_codex_artifact_reference(artifacts.get("final"))
    report_id = f"auto-report-{payload_digest(mission_id, lease_id)[:24]}"
    report_payload = {
        "id": report_id,
        "type": current.get("reportType") or "bridge_status_report",
        "title": current.get("title"),
        "summary": summary,
        "ownerAgentId": current.get("owner"),
        "linkedMissionId": mission_id,
        "linkedPropId": current.get("targetId"),
        "status": "ready" if succeeded else "blocked",
        "artifacts": [artifact_path] if artifact_path else [],
        "risks": [] if succeeded else [str(result.get("status") or runner.get("exitCode") or "runner_failed")],
    }
    finished = None
    parent_id = None
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            if (
                mission.get("id") != mission_id
                or mission.get("status") != "running"
                or execution.get("leaseId") != lease_id
            ):
                continue
            finished_at = utc_now()
            mission["status"] = "completed" if succeeded else "failed"
            mission["phase"] = "auto_guarded_completed" if succeeded else "auto_guarded_failed"
            mission["errorCode"] = None if succeeded else str(
                result.get("status") or runner.get("exitCode") or "runner_failed"
            )
            mission["result"] = summary
            mission["artifactPath"] = artifact_path
            mission["reportIds"] = [report_id]
            mission["updatedAt"] = finished_at
            mission["heartbeatAt"] = finished_at
            mission["completedAt"] = finished_at
            execution["dispatchState"] = "completed" if succeeded else "failed"
            execution["heartbeatAt"] = finished_at
            execution["completedAt"] = finished_at
            execution["processStarted"] = bool(
                result.get("processStarted", runner.get("processStarted", False))
            )
            execution["processTreeTerminated"] = bool(
                result.get(
                    "processTreeTerminated",
                    runner.get("processTreeTerminated", False),
                )
            )
            execution["workingDirectory"] = redact_text(
                str(result.get("workingDirectory") or ""),
                240,
            )
            execution["writeRoots"] = [
                value
                for value in (
                    safe_reference(item)
                    for item in (
                        result.get("writeRoots")
                        if isinstance(result.get("writeRoots"), list)
                        else []
                    )[:20]
                )
                if value
            ]
            execution["controlPlaneWritable"] = bool(
                result.get("controlPlaneWritable", False)
            )
            execution["automaticRetry"] = False
            mission["execution"] = execution
            finished = mission
            parent_id = safe_reference(mission.get("parentMissionId"))
            break
        if finished:
            save_missions(missions)
    if not finished:
        return None
    try:
        create_report(report_payload)
    except Exception:
        with MISSIONS_LOCK:
            missions = load_missions()
            for mission in missions:
                execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
                if (
                    mission.get("id") != mission_id
                    or execution.get("leaseId") != lease_id
                    or mission.get("status") not in {"completed", "failed"}
                ):
                    continue
                failed_at = utc_now()
                mission["status"] = "failed"
                mission["phase"] = "auto_guarded_report_failed"
                mission["errorCode"] = "report_persist_failed"
                mission["result"] = (
                    f"{summary}\n\nระบบได้รับผลจาก Codex แต่บันทึกรายงานไม่สำเร็จ "
                    "Mission จึงถูกปิดเป็นไม่สำเร็จและจะไม่ลองรันซ้ำอัตโนมัติ"
                )
                mission["reportIds"] = [
                    item for item in (mission.get("reportIds") or []) if item != report_id
                ]
                mission["updatedAt"] = failed_at
                mission["completedAt"] = failed_at
                execution["dispatchState"] = "failed"
                execution["completedAt"] = failed_at
                execution["automaticRetry"] = False
                mission["execution"] = execution
                finished = mission
                break
            save_missions(missions)
        append_audit({
            "type": "mission.auto_report_persist_failed",
            "missionId": mission_id,
            "leaseId": lease_id,
            "automaticRetry": False,
        })
    if parent_id:
        refresh_parent_mission(parent_id)
    append_audit({
        "type": "mission.auto_run_end",
        "missionId": mission_id,
        "ownerAgentId": finished.get("owner"),
        "toolId": finished.get("toolId"),
        "workerId": execution.get("workerId"),
        "leaseId": lease_id,
        "status": finished.get("status"),
        "durationMs": result.get("durationMs", runner.get("durationMs")),
        "outputChars": len(final_message),
        "realToolExecuted": bool(execution.get("processStarted")),
        "workingDirectory": execution.get("workingDirectory"),
        "writeRoots": execution.get("writeRoots"),
        "controlPlaneWritable": execution.get("controlPlaneWritable"),
        "automaticRetry": False,
    })
    return finished


def process_auto_mission(worker_id: str, mission: dict) -> None:
    mission_id = str(mission.get("id") or "")
    agent_id = str(mission.get("owner") or "manager")
    tool_id = str(mission.get("toolId") or "")
    config = mission_worker_config()
    if not CODEX_RUNNER_PYTHON.is_file() or not CODEX_RUNNER_SCRIPT.is_file():
        defer_auto_mission(mission_id, "runner_missing", config["runnerUnavailableBackoffSeconds"])
        return
    status_snapshot = bridge_status()
    if status_snapshot.get("codex", {}).get("status") not in {"ready", "ready_guarded"}:
        defer_auto_mission(
            mission_id,
            str(status_snapshot.get("codex", {}).get("status") or "runner_not_ready"),
            config["runnerUnavailableBackoffSeconds"],
        )
        return
    quota = codex_rate_limits()
    if quota.get("ok") is not True or quota.get("stale") is True:
        defer_auto_mission(mission_id, "quota_unavailable_or_stale", config["quotaBackoffSeconds"])
        return
    if quota.get("limitReached") is True:
        defer_auto_mission(mission_id, "codex_limit_reached", config["quotaBackoffSeconds"])
        return
    tier_id = str(mission.get("modelTier") or role_default_model_tier(agent_id))
    tier = (load_orchestration_contract().get("modelTiers") or {}).get(tier_id) or {}
    max_runs = clamp_int(tier.get("maxRunsPerHour"), 12, 1, 200)
    rate_key = f"real:{agent_id}:{tool_id}:{tier_id}"
    allowed, retry_after = check_rate_limit(rate_key, max_runs, consume=False)
    if not allowed:
        defer_auto_mission(mission_id, "local_rate_limited", retry_after)
        return
    if not REAL_RUN_SEMAPHORE.acquire(blocking=False):
        defer_auto_mission(mission_id, "runner_busy", config["busyBackoffSeconds"])
        return
    try:
        allowed, retry_after = check_rate_limit(rate_key, max_runs, consume=True)
        if not allowed:
            defer_auto_mission(mission_id, "local_rate_limited", retry_after)
            return
        claimed = claim_auto_mission(mission_id, worker_id)
        if not claimed:
            return
        execution = claimed.get("execution") if isinstance(claimed.get("execution"), dict) else {}
        lease_id = str(execution.get("leaseId") or "")
        budget = claimed.get("budget") if isinstance(claimed.get("budget"), dict) else {}
        timeout_seconds = clamp_int(budget.get("timeoutSeconds"), 120, 15, 600)
        output_limit = clamp_int(budget.get("outputLimitChars"), 7000, 1000, 20000)
        update_mission_worker_state(
            status="running",
            currentMissionId=mission_id,
            heartbeatAt=utc_now(),
            lastError=None,
        )
        append_audit({
            "type": "mission.auto_run_start",
            "missionId": mission_id,
            "ownerAgentId": agent_id,
            "toolId": tool_id,
            "modelTier": tier_id,
            "workerId": worker_id,
            "leaseId": lease_id,
            "timeoutSeconds": timeout_seconds,
            "outputLimitChars": output_limit,
            "sandbox": "workspace-write",
            "workingDirectory": "workspace",
            "writeRoots": ["workspace", "frontend", "docs", "assets-source"],
            "controlPlaneWritable": False,
        })
        heartbeat_stop = threading.Event()
        heartbeat_thread = threading.Thread(
            target=heartbeat_auto_mission,
            args=(mission_id, lease_id, heartbeat_stop, config["heartbeatSeconds"]),
            name=f"mission-heartbeat-{mission_id[:24]}",
            daemon=True,
        )
        heartbeat_thread.start()
        try:
            runner = run_safe_command(
                [
                    str(CODEX_RUNNER_PYTHON),
                    str(CODEX_RUNNER_SCRIPT),
                    "--run",
                    "--execution-mode", "auto_guarded",
                    "--agent-id", agent_id,
                    "--mission-id", mission_id,
                    "--prompt-stdin",
                    "--timeout", str(timeout_seconds),
                    "--model-tier", tier_id,
                    "--output-limit", str(output_limit),
                ],
                timeout=timeout_seconds + 30,
                output_limit=max(40000, output_limit + 10000),
                input_text=str(claimed.get("detail") or ""),
                kill_process_tree_on_timeout=True,
                cancel_event=MISSION_WORKER_STOP,
            )
        finally:
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=max(2, config["heartbeatSeconds"] + 1))
        try:
            result = json.loads(runner.get("output") or "{}")
        except json.JSONDecodeError:
            if runner.get("exitCode") == "cancelled":
                result = {
                    "ok": False,
                    "status": "bridge_shutdown_cancelled",
                    "message": "Bridge กำลังปิด ระบบจึงหยุดงานนี้แบบปลอดภัยและไม่ลองรันซ้ำอัตโนมัติ",
                }
            else:
                result = {
                    "ok": False,
                    "status": "invalid_runner_output",
                    "message": "Codex Worker ที่มีระบบป้องกันส่งผลลัพธ์กลับมาในรูปแบบที่ตรวจสอบไม่ได้",
                }
        if not isinstance(result, dict):
            result = {"ok": False, "status": "invalid_runner_output", "message": "Invalid runner result."}
        finish_auto_mission(mission_id, lease_id, runner, result)
    except Exception:
        current = find_mission(mission_id)
        execution = current.get("execution") if isinstance((current or {}).get("execution"), dict) else {}
        lease_id = str(execution.get("leaseId") or "")
        if lease_id:
            finish_auto_mission(
                mission_id,
                lease_id,
                {"processStarted": False, "exitCode": "internal_worker_error"},
                {
                    "ok": False,
                    "status": "internal_worker_error",
                    "message": "Mission Worker เกิดข้อผิดพลาดภายใน ระบบหยุดแบบปลอดภัยและไม่ลองรันซ้ำอัตโนมัติ",
                },
            )
        update_mission_worker_state(lastError="internal_worker_error")
    finally:
        invalidate_codex_rate_limit_cache()
        update_mission_worker_state(currentMissionId=None, heartbeatAt=utc_now())
        REAL_RUN_SEMAPHORE.release()


def mission_worker_loop(worker_id: str) -> None:
    config = mission_worker_config()
    update_mission_worker_state(
        status="starting",
        workerId=worker_id,
        currentMissionId=None,
        startedAt=utc_now(),
        heartbeatAt=utc_now(),
        lastError=None,
    )
    last_reconcile = 0.0
    while not MISSION_WORKER_STOP.is_set():
        try:
            if time.monotonic() - last_reconcile >= config["reconcileIntervalSeconds"]:
                reconcile_stale_approval_missions()
                reconcile_timed_out_running_missions()
                reconcile_parent_mission_statuses()
                last_reconcile = time.monotonic()
            if load_operator_mode_record().get("mode") != "auto_guarded":
                update_mission_worker_state(status="paused_manual", currentMissionId=None, heartbeatAt=utc_now())
                MISSION_WORKER_WAKE.wait(config["idlePollSeconds"])
                MISSION_WORKER_WAKE.clear()
                continue
            mission = find_next_auto_mission()
            if mission:
                process_auto_mission(worker_id, mission)
                continue
            update_mission_worker_state(status="idle", currentMissionId=None, heartbeatAt=utc_now())
            MISSION_WORKER_WAKE.wait(config["idlePollSeconds"])
            MISSION_WORKER_WAKE.clear()
        except DataIntegrityError:
            update_mission_worker_state(status="blocked", lastError="data_integrity_error", heartbeatAt=utc_now())
            MISSION_WORKER_WAKE.wait(config["runnerUnavailableBackoffSeconds"])
            MISSION_WORKER_WAKE.clear()
        except Exception:
            update_mission_worker_state(status="degraded", lastError="worker_loop_error", heartbeatAt=utc_now())
            MISSION_WORKER_WAKE.wait(config["runnerUnavailableBackoffSeconds"])
            MISSION_WORKER_WAKE.clear()
    update_mission_worker_state(status="stopped", currentMissionId=None, heartbeatAt=utc_now())


def mission_timeout_watchdog_loop() -> None:
    """Watch running leases independently while the single worker is blocked in Codex."""
    config = mission_worker_config()
    while not MISSION_WORKER_STOP.wait(config["timeoutWatchdogIntervalSeconds"]):
        try:
            reconcile_timed_out_running_missions()
        except (DataIntegrityError, OSError):
            update_mission_worker_state(lastError="timeout_watchdog_data_error")
        except Exception:
            update_mission_worker_state(lastError="timeout_watchdog_error")


def start_mission_worker() -> threading.Thread:
    global MISSION_WORKER_THREAD, MISSION_WORKER_WATCHDOG_THREAD
    with MISSION_WORKER_LOCK:
        if MISSION_WORKER_THREAD and MISSION_WORKER_THREAD.is_alive():
            if not MISSION_WORKER_WATCHDOG_THREAD or not MISSION_WORKER_WATCHDOG_THREAD.is_alive():
                MISSION_WORKER_WATCHDOG_THREAD = threading.Thread(
                    target=mission_timeout_watchdog_loop,
                    name="metafx-mission-timeout-watchdog",
                    daemon=False,
                )
                MISSION_WORKER_WATCHDOG_THREAD.start()
            return MISSION_WORKER_THREAD
        MISSION_WORKER_STOP.clear()
        worker_id = safe_id(None, "mission-worker")
        MISSION_WORKER_WATCHDOG_THREAD = threading.Thread(
            target=mission_timeout_watchdog_loop,
            name="metafx-mission-timeout-watchdog",
            daemon=False,
        )
        MISSION_WORKER_THREAD = threading.Thread(
            target=mission_worker_loop,
            args=(worker_id,),
            name="metafx-mission-worker",
            daemon=False,
        )
        MISSION_WORKER_WATCHDOG_THREAD.start()
        MISSION_WORKER_THREAD.start()
        return MISSION_WORKER_THREAD


def stop_mission_worker() -> None:
    MISSION_WORKER_STOP.set()
    MISSION_WORKER_WAKE.set()
    forced_tree_termination = None
    with MISSION_WORKER_PROCESS_LOCK:
        active_process = MISSION_WORKER_PROCESS
        if active_process is not None and active_process.poll() is None:
            forced_tree_termination = _terminate_command_process_tree(
                active_process,
                MISSION_WORKER_JOB_HOLDER,
            )
    if forced_tree_termination is not None:
        append_audit({
            "type": "mission.worker_shutdown_cancel",
            "missionId": mission_worker_read_model().get("currentMissionId"),
            "processTreeTerminated": forced_tree_termination,
            "automaticRetry": False,
        })
    worker = MISSION_WORKER_THREAD
    if worker and worker.is_alive():
        worker.join(timeout=30)
    watchdog = MISSION_WORKER_WATCHDOG_THREAD
    if watchdog and watchdog.is_alive():
        watchdog.join(timeout=15)
    if not worker or not worker.is_alive():
        update_mission_worker_state(status="stopped", currentMissionId=None, heartbeatAt=utc_now())
    else:
        update_mission_worker_state(status="stopping", lastError="worker_shutdown_timeout", heartbeatAt=utc_now())
        append_audit({
            "type": "mission.worker_shutdown_timeout",
            "missionId": mission_worker_read_model().get("currentMissionId"),
            "processTreeTerminated": forced_tree_termination,
        })


def run_bridge_task(payload: dict) -> dict:
    tool_id = str(payload.get("toolId") or "manager_mission")
    prompt = str(payload.get("prompt") or "Prepare a guarded mission summary.").strip()
    agent_id = str(payload.get("agentId") or "manager")
    if contains_potential_secret(prompt):
        append_audit({"type": "guard.secret_blocked", "agentId": agent_id, "toolId": tool_id, "surface": "bridge_run"})
        return {"ok": False, "kind": "secret_blocked", "message": "Potential secret detected. Frontend may submit intent only.", "_httpStatus": 422}
    guard = load_orchestration_contract().get("costRateGuard") or {}
    max_prompt_chars = clamp_int(guard.get("maxPromptChars"), 8000, 100, 50000)
    if len(prompt) > max_prompt_chars:
        return {"ok": False, "kind": "prompt_too_large", "message": f"Prompt exceeds {max_prompt_chars} characters.", "_httpStatus": 413}
    if "approved" in payload:
        append_audit({"type": "guard.frontend_approval_ignored", "agentId": agent_id, "toolId": tool_id})

    permission = evaluate_tool_permission(agent_id, tool_id)
    if not permission.get("allowed"):
        append_audit({"type": "policy.denied", "agentId": agent_id, "toolId": tool_id, "reason": permission.get("reason")})
        return {"ok": False, "kind": "permission_denied", "message": permission["message"], "_httpStatus": 403}
    tool_policy = permission.get("policy") or {}

    if tool_id == "codex_status":
        status = bridge_status()
        append_audit({"type": "bridge.status", "agentId": agent_id, "toolId": tool_id})
        return {"ok": True, "kind": "status", "bridge": status, "message": status["codex"]["message"]}

    if tool_id == "codex_cli_smoke":
        check = run_safe_command([str(CODEX_RUNNER_PYTHON), str(CODEX_RUNNER_SCRIPT), "--status"], timeout=20, output_limit=8000)
        append_audit({"type": "bridge.smoke", "agentId": agent_id, "toolId": tool_id, "ok": check["ok"], "exitCode": check["exitCode"]})
        return {"ok": check["ok"], "kind": "codex_cli_smoke", "result": check, "bridge": bridge_status(), "message": check["output"]}

    requested_target = str(payload.get("targetId") or "").strip()
    target_id = requested_target or pick_target_for_task(prompt)
    if not find_room_prop(target_id):
        return {"ok": False, "kind": "unknown_target", "message": "Unknown target prop id.", "_httpStatus": 422}
    owner_agent_id = str(payload.get("ownerAgentId") or agent_id) if tool_id == "manager_mission" else agent_id
    if owner_agent_id not in {str(item.get("id")) for item in load_agent_contracts()}:
        return {"ok": False, "kind": "unknown_owner", "message": "Mission owner agent is unknown.", "_httpStatus": 422}
    requester = str(payload.get("requester") or agent_id or "human")
    known_actor_ids = {str(item.get("id")) for item in load_agent_contracts()} | {"human"}
    if requester not in known_actor_ids:
        requester = agent_id
    requested_report_type = str(payload.get("reportType") or "").strip()
    known_report_types = set((load_report_contract().get("report_targets") or {}).keys()) | {"prop_report"}
    report_type = requested_report_type if requested_report_type in known_report_types else report_type_for_prop(target_id)
    idempotency_key = str(payload.get("idempotencyKey") or "").strip()
    if idempotency_key and not SAFE_IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        return {"ok": False, "kind": "invalid_idempotency_key", "message": "Idempotency key must be a short safe identifier.", "_httpStatus": 422}
    mission = create_mission({
        "prompt": prompt,
        "agentId": owner_agent_id,
        "requester": requester,
        "toolId": tool_id,
        "targetId": target_id,
        "risk": tool_policy.get("risk") or "low",
        "modelTier": role_default_model_tier(owner_agent_id),
        "reportType": report_type,
        "budget": {},
        "idempotencyKey": idempotency_key,
    }, status="queued")
    status = bridge_status()
    if mission.get("approval", {}).get("required"):
        append_audit({"type": "bridge.approval_required", "missionId": mission["id"], "agentId": agent_id, "toolId": tool_id})
        return {
            "ok": False,
            "kind": "approval_required",
            "mission": mission,
            "targetId": mission["targetId"],
            "bridge": status,
            "message": "Mission is queued and bound to a server-side approval record. No tool executed.",
            "_httpStatus": 202,
        }

    append_audit({"type": "bridge.mission_queued", "missionId": mission["id"], "agentId": agent_id, "toolId": tool_id})
    return {
        "ok": True,
        "kind": "mission_queued",
        "mission": mission,
        "targetId": mission["targetId"],
        "bridge": status,
        "message": "Mission queued through the local bridge. No real tool executed.",
        "_httpStatus": 202,
    }


def _agent_chat_error(
    kind: str,
    message: str,
    http_status: int,
    *,
    agent_id: str | None = None,
    session_id: str | None = None,
    retry_after: int | None = None,
    consumes_codex_quota: bool = False,
) -> dict:
    response = {
        "ok": False,
        "kind": kind,
        "status": "blocked",
        "message": redact_text(message, 1200),
        "agentId": safe_reference(agent_id),
        "sessionId": safe_reference(session_id),
        "consumesCodexQuota": bool(consumes_codex_quota),
        "toolsExecuted": False,
        "taskCreated": False,
        "_httpStatus": http_status,
    }
    if retry_after is not None:
        response["retryAfterSeconds"] = max(1, int(retry_after))
    return response


def _agent_chat_validation_error(
    kind: str,
    message: str,
    http_status: int,
    reason: str,
    *,
    agent_id: str | None = None,
    session_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    audit = {
        "type": "agent.chat_blocked",
        "reason": reason,
    }
    if agent_id and SAFE_ID_PATTERN.fullmatch(agent_id):
        audit["agentId"] = agent_id
    if session_id:
        audit["sessionDigest"] = payload_digest(session_id)[:16]
    if isinstance(metadata, dict):
        audit.update(sanitize_json_value(metadata, collection_limit=20, string_limit=160))
    append_audit(audit)
    return _agent_chat_error(
        kind,
        message,
        http_status,
        agent_id=agent_id,
        session_id=session_id,
        consumes_codex_quota=False,
    )


def create_agent_chat_task(
    agent_id: str,
    task_goal: str,
    scope_digest: str,
    *,
    raw_message: str | None = None,
) -> dict:
    """Create exactly one idempotent task path after a tool-free Chat classification."""
    task_goal = str(task_goal or "").strip()
    if (
        not task_goal
        or len(task_goal) > 4000
        or contains_potential_secret(task_goal)
        or not re.fullmatch(r"[0-9a-f]{64}", str(scope_digest or ""))
    ):
        return {
            "taskCreated": False,
            "taskMissionIds": [],
            "taskStatus": "create_blocked",
            "autoExecute": False,
        }
    task_key = f"chat-task-{scope_digest[:32]}"
    risk_context = f"{task_goal}\n{str(raw_message or '')}"
    high_impact_reasons = _high_impact_reasons("codex_cli_task", risk_context, "medium")
    if agent_id in {"manager", "ceo"}:
        result = manager_delegate({
            "agentId": agent_id,
            "goal": task_goal,
            "idempotencyKey": task_key,
        }, backend_risk_context=raw_message)
        if result.get("ok") is not True:
            append_audit({
                "type": "agent.chat_task_create_failed",
                "agentId": agent_id,
                "idempotencyDigest": scope_digest[:16],
                "reason": result.get("kind") or "manager_delegate_failed",
            })
            return {
                "taskCreated": False,
                "taskMissionIds": [],
                "taskStatus": str(result.get("kind") or "create_failed"),
                "autoExecute": False,
            }
        parent = result.get("parent") if isinstance(result.get("parent"), dict) else {}
        subtasks = [
            item for item in (result.get("subtasks") or []) if isinstance(item, dict)
        ]
        missions = [item for item in [parent, *subtasks] if item.get("id")]
        task_status = str(parent.get("status") or "queued")
    else:
        permission = evaluate_tool_permission(agent_id, "codex_cli_task")
        if not permission.get("allowed"):
            append_audit({
                "type": "agent.chat_task_create_failed",
                "agentId": agent_id,
                "idempotencyDigest": scope_digest[:16],
                "reason": permission.get("reason") or "permission_denied",
            })
            return {
                "taskCreated": False,
                "taskMissionIds": [],
                "taskStatus": "permission_denied",
                "autoExecute": False,
            }
        target_id = target_for_agent_goal(agent_id, task_goal)
        tool_policy = permission.get("policy") if isinstance(permission.get("policy"), dict) else {}
        mission = create_mission({
            "title": f"{agent_id}: {task_goal[:96]}",
            "prompt": task_goal,
            "agentId": agent_id,
            "requester": agent_id,
            "toolId": "codex_cli_task",
            "targetId": target_id,
            "risk": "high" if high_impact_reasons else (tool_policy.get("risk") or "medium"),
            "modelTier": role_default_model_tier(agent_id),
            "reportType": report_type_for_prop(target_id),
            "idempotencyKey": task_key,
        }, status="queued")
        missions = [mission]
        task_status = str(mission.get("status") or "queued")
    mission_ids = [
        str(item.get("id"))
        for item in missions
        if safe_reference(item.get("id"))
    ]
    auto_execute = any(
        item.get("autoEligible") is True
        and item.get("executionMode") == "auto_guarded"
        and item.get("status") in {"queued", "running"}
        for item in missions
    )
    append_audit({
        "type": "agent.chat_task_created",
        "agentId": agent_id,
        "idempotencyDigest": scope_digest[:16],
        "missionIds": mission_ids,
        "taskStatus": task_status,
        "autoExecute": auto_execute,
        "highImpact": any(item.get("risk") == "high" for item in missions),
        "highImpactReasons": high_impact_reasons,
    })
    if auto_execute:
        MISSION_WORKER_WAKE.set()
    return {
        "taskCreated": bool(mission_ids),
        "taskMissionIds": mission_ids,
        "taskStatus": task_status,
        "autoExecute": auto_execute,
    }


def run_agent_chat_request(payload: dict) -> dict:
    field_order = ("agentId", "message", "sessionId", "idempotencyKey")
    allowed_fields = set(field_order)
    if not isinstance(payload, dict):
        return _agent_chat_validation_error(
            "invalid_request",
            "Agent Chat ต้องรับข้อมูลแบบ JSON Object",
            422,
            "invalid_payload_shape",
        )
    unexpected_fields = sorted(str(key) for key in payload if key not in allowed_fields)
    if unexpected_fields:
        return _agent_chat_validation_error(
            "invalid_request",
            "Agent Chat รับเฉพาะ Agent, ข้อความ, Session และ Idempotency Key",
            422,
            "unexpected_frontend_fields",
            metadata={"fieldCount": len(unexpected_fields)},
        )
    missing_fields = [field for field in field_order if field not in payload]
    if missing_fields:
        return _agent_chat_validation_error(
            "invalid_request",
            "Agent Chat ต้องส่ง Agent, ข้อความ, Session และ Idempotency Key ให้ครบ",
            422,
            "missing_required_fields",
            metadata={"missingFields": missing_fields},
        )

    agent_value = payload.get("agentId")
    message_value = payload.get("message")
    if not isinstance(agent_value, str):
        return _agent_chat_validation_error(
            "invalid_agent",
            "Agent ID ต้องเป็นข้อความ",
            422,
            "invalid_agent_type",
        )
    agent_id = agent_value.strip()
    if not SAFE_ID_PATTERN.fullmatch(agent_id):
        return _agent_chat_validation_error(
            "invalid_agent",
            "Agent ID ไม่ถูกต้อง",
            422,
            "invalid_agent_format",
            metadata={"valueDigest": payload_digest(agent_id)[:16], "valueChars": len(agent_id)},
        )
    agent = next((item for item in load_agent_contracts() if item.get("id") == agent_id), None)
    if not isinstance(agent, dict):
        return _agent_chat_validation_error(
            "unknown_agent",
            "ไม่พบ Agent นี้ในสัญญาระบบ",
            404,
            "unknown_agent",
            metadata={"valueDigest": payload_digest(agent_id)[:16]},
        )
    permission = evaluate_tool_permission(agent_id, "agent_chat")
    if not permission.get("allowed"):
        append_audit({"type": "agent.chat_blocked", "agentId": agent_id, "reason": permission.get("reason")})
        return _agent_chat_error(
            "permission_denied",
            "Agent นี้ไม่ได้รับสิทธิ์ใช้ Codex Chat",
            403,
            agent_id=agent_id,
        )
    if not isinstance(message_value, str):
        return _agent_chat_validation_error(
            "invalid_message",
            "ข้อความ Chat ต้องเป็นข้อความธรรมดา",
            422,
            "invalid_message_type",
            agent_id=agent_id,
        )

    contract = load_orchestration_contract()
    guard = contract.get("costRateGuard") if isinstance(contract.get("costRateGuard"), dict) else {}
    max_message_chars = clamp_int(guard.get("agentChatMaxMessageChars"), 4000, 1, 4000)
    output_limit = clamp_int(guard.get("agentChatMaxOutputChars"), 5000, 1000, 5000)
    timeout_seconds = clamp_int(guard.get("agentChatTimeoutSeconds"), 120, 15, 180)
    message = message_value.strip()
    if not message or len(message) > max_message_chars:
        return _agent_chat_validation_error(
            "invalid_message",
            f"ข้อความ Chat ต้องมีความยาว 1-{max_message_chars:,} ตัวอักษร",
            422,
            "invalid_message_length",
            agent_id=agent_id,
            metadata={"messageChars": len(message)},
        )
    message_digest = payload_digest(message)
    if contains_potential_secret(message) or json_contains_potential_secret({"message": message}):
        append_audit({
            "type": "agent.chat_blocked",
            "agentId": agent_id,
            "reason": "potential_secret",
            "messageDigest": message_digest[:16],
            "messageChars": len(message),
        })
        return _agent_chat_error(
            "secret_blocked",
            "พบข้อมูลที่อาจเป็นความลับ ระบบจึงไม่บันทึกและไม่ส่งข้อความนี้ไป Codex",
            422,
            agent_id=agent_id,
        )
    raw_high_impact_reasons = _high_impact_reasons("codex_cli_task", message, "medium")

    session_value = payload.get("sessionId")
    if not isinstance(session_value, str):
        return _agent_chat_validation_error(
            "invalid_session",
            "Session ID ต้องเป็นข้อความ",
            422,
            "invalid_session_type",
            agent_id=agent_id,
        )
    session_id = session_value.strip()
    if contains_potential_secret(session_id):
        return _agent_chat_validation_error(
            "secret_blocked",
            "Session ID มีรูปแบบคล้ายข้อมูลลับ ระบบจึงไม่บันทึกคำขอนี้",
            422,
            "potential_secret_session",
            agent_id=agent_id,
        )
    if not SAFE_ID_PATTERN.fullmatch(session_id):
        return _agent_chat_validation_error(
            "invalid_session",
            "Session ID ไม่ถูกต้อง",
            422,
            "invalid_session_format",
            agent_id=agent_id,
            metadata={"valueDigest": payload_digest(session_id)[:16], "valueChars": len(session_id)},
        )
    idempotency_value = payload.get("idempotencyKey")
    if not isinstance(idempotency_value, str):
        return _agent_chat_validation_error(
            "invalid_idempotency_key",
            "Idempotency Key ต้องเป็นข้อความ",
            422,
            "invalid_idempotency_type",
            agent_id=agent_id,
            session_id=session_id,
        )
    idempotency_key = idempotency_value.strip()
    if contains_potential_secret(idempotency_key):
        return _agent_chat_validation_error(
            "secret_blocked",
            "Idempotency Key มีรูปแบบคล้ายข้อมูลลับ ระบบจึงไม่บันทึกคำขอนี้",
            422,
            "potential_secret_idempotency",
            agent_id=agent_id,
            session_id=session_id,
        )
    if not SAFE_IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        return _agent_chat_validation_error(
            "invalid_idempotency_key",
            "Idempotency Key ไม่ถูกต้อง",
            422,
            "invalid_idempotency_format",
            agent_id=agent_id,
            session_id=session_id,
            metadata={"valueDigest": payload_digest(idempotency_key)[:16], "valueChars": len(idempotency_key)},
        )

    scope_digest = payload_digest(agent_id, session_id, idempotency_key)
    with AGENT_CHAT_LOCK:
        stored = load_agent_chat_result(agent_id, session_id, idempotency_key)
        if stored:
            if not secrets.compare_digest(str(stored.get("messageDigest") or ""), message_digest):
                append_audit({
                    "type": "agent.chat_blocked",
                    "agentId": agent_id,
                    "sessionDigest": payload_digest(session_id)[:16],
                    "reason": "idempotency_conflict",
                    "idempotencyDigest": scope_digest[:16],
                })
                return _agent_chat_error(
                    "idempotency_conflict",
                    "Idempotency Key นี้ถูกใช้กับข้อความอื่นแล้ว",
                    409,
                    agent_id=agent_id,
                    session_id=session_id,
                )
            stored_response = stored.get("response") if isinstance(stored.get("response"), dict) else {}
            replay = agent_chat_response_read_model(stored_response, replay=True)
            replay["_httpStatus"] = clamp_int(stored.get("httpStatus"), 200, 200, 599)
            append_audit({
                "type": "agent.chat_end",
                "agentId": agent_id,
                "sessionId": session_id,
                "turnId": replay.get("turnId"),
                "status": replay.get("status"),
                "idempotentReplay": True,
                "consumedCodexQuota": False,
                "toolsExecuted": False,
                "intent": replay.get("intent"),
                "taskCreated": replay.get("taskCreated"),
                "taskMissionIds": replay.get("taskMissionIds"),
                "taskStatus": replay.get("taskStatus"),
                "autoExecute": replay.get("autoExecute"),
            })
            return replay
        if scope_digest in AGENT_CHAT_INFLIGHT:
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "duplicate_inflight",
            })
            return _agent_chat_error(
                "request_inflight",
                "ข้อความนี้กำลังประมวลผลอยู่ กรุณารอผลเดิม",
                409,
                agent_id=agent_id,
                session_id=session_id,
            )
        AGENT_CHAT_INFLIGHT.add(scope_digest)

    semaphore_acquired = False
    runner_invoked = False
    quota_attempted = False
    quota_consumption = "none"
    process_tree_terminated = None
    turn_id = safe_id(None, "chat-turn")
    model_tier = role_default_model_tier(agent_id)
    tier = (contract.get("modelTiers") or {}).get(model_tier)
    tier = tier if isinstance(tier, dict) else {}
    global_max_runs = clamp_int(guard.get("agentChatRunsPerHour"), 40, 1, 200)
    agent_max_runs = min(global_max_runs, clamp_int(tier.get("maxRunsPerHour"), 12, 1, 200))
    cooldown_seconds = clamp_int(guard.get("agentChatCooldownSeconds"), 1, 0, 60)
    global_rate_key = "agent-chat:global"
    agent_rate_key = f"agent-chat:{agent_id}:{model_tier}"
    quota = peek_codex_rate_limits()
    try:
        if not CODEX_RUNNER_PYTHON.is_file() or not CODEX_RUNNER_SCRIPT.is_file():
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "runner_missing",
            })
            return _agent_chat_error(
                "runner_unavailable",
                "Codex Chat Runner ยังไม่พร้อมในเครื่อง",
                503,
                agent_id=agent_id,
                session_id=session_id,
            )

        quota = codex_rate_limits()
        if quota.get("ok") is True and quota.get("limitReached") is True:
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "codex_limit_reached",
                "quotaStatus": quota.get("status"),
                "quotaStale": bool(quota.get("stale", False)),
            })
            response = _agent_chat_error(
                "codex_limit_reached",
                "Codex แจ้งว่าบัญชีถึง Rate Limit แล้ว ระบบจึงไม่ได้ส่งข้อความใหม่",
                429,
                agent_id=agent_id,
                session_id=session_id,
            )
            response["rateLimit"] = _agent_chat_rate_limit_read_model(quota)
            return response

        allowed, retry_after = check_rate_limit(
            global_rate_key,
            global_max_runs,
            cooldown_seconds,
            consume=False,
        )
        if not allowed:
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "global_rate_limited",
                "retryAfterSeconds": retry_after,
            })
            return _agent_chat_error(
                "rate_limited",
                "Agent Chat ถูกจำกัดความถี่ชั่วคราว",
                429,
                agent_id=agent_id,
                session_id=session_id,
                retry_after=retry_after,
            )
        allowed, retry_after = check_rate_limit(agent_rate_key, agent_max_runs, consume=False)
        if not allowed:
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "agent_rate_limited",
                "retryAfterSeconds": retry_after,
            })
            return _agent_chat_error(
                "rate_limited",
                "Agent นี้ใช้โควตา Chat ต่อชั่วโมงครบแล้ว",
                429,
                agent_id=agent_id,
                session_id=session_id,
                retry_after=retry_after,
            )
        if not REAL_RUN_SEMAPHORE.acquire(blocking=False):
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "runner_busy",
            })
            return _agent_chat_error(
                "runner_busy",
                "Codex Runner กำลังทำงานอื่น กรุณาลองใหม่อีกครั้ง",
                429,
                agent_id=agent_id,
                session_id=session_id,
                retry_after=1,
            )
        semaphore_acquired = True
        allowed, retry_after = check_rate_limit(agent_rate_key, agent_max_runs, consume=True)
        if not allowed:
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "agent_rate_limited_after_lock",
                "retryAfterSeconds": retry_after,
            })
            return _agent_chat_error(
                "rate_limited",
                "Agent นี้ใช้โควตา Chat ต่อชั่วโมงครบแล้ว",
                429,
                agent_id=agent_id,
                session_id=session_id,
                retry_after=retry_after,
            )
        allowed, retry_after = check_rate_limit(
            global_rate_key,
            global_max_runs,
            cooldown_seconds,
            consume=True,
        )
        if not allowed:
            append_audit({
                "type": "agent.chat_blocked",
                "agentId": agent_id,
                "sessionDigest": payload_digest(session_id)[:16],
                "reason": "global_rate_limited_after_lock",
                "retryAfterSeconds": retry_after,
            })
            return _agent_chat_error(
                "rate_limited",
                "Agent Chat ถูกจำกัดความถี่ชั่วคราว",
                429,
                agent_id=agent_id,
                session_id=session_id,
                retry_after=retry_after,
            )

        history = load_agent_chat_history(agent_id, session_id, recent_turns=8, max_chars=12000)
        append_audit({
            "type": "agent.chat_start",
            "turnId": turn_id,
            "agentId": agent_id,
            "sessionId": session_id,
            "idempotencyDigest": scope_digest[:16],
            "messageDigest": message_digest[:16],
            "messageChars": len(message),
            "historyMessages": len(history),
            "modelTier": model_tier,
            "model": "gpt-5.5",
            "timeoutSeconds": timeout_seconds,
            "outputLimitChars": output_limit,
            "codexRequestAttempted": False,
            "quotaConsumptionStatus": "pending",
            "toolsEnabled": False,
            "taskCreated": False,
            "highImpactIntentDetected": bool(raw_high_impact_reasons),
        })
        runner_invoked = True
        runner = run_safe_command(
            [
                str(CODEX_RUNNER_PYTHON),
                str(CODEX_RUNNER_SCRIPT),
                "--chat",
                "--chat-request-stdin",
                "--agent-id",
                agent_id,
                "--session-id",
                session_id,
                "--timeout",
                str(timeout_seconds),
                "--model-tier",
                model_tier,
                "--output-limit",
                str(output_limit),
            ],
            timeout=timeout_seconds + 45,
            output_limit=30000,
            input_text=json.dumps({"message": message, "history": history}, ensure_ascii=False),
            kill_process_tree_on_timeout=True,
        )
        try:
            runner_result = json.loads(runner.get("output") or "{}")
        except json.JSONDecodeError:
            runner_result = {
                "ok": False,
                "status": "invalid_runner_output",
                "message": "Codex Chat Runner ส่งผลลัพธ์ที่ตรวจสอบไม่ได้",
            }
        runner_result = runner_result if isinstance(runner_result, dict) else {}
        quota_attempted = bool(runner_result.get("quotaAttempted", False))
        quota_consumption = str(runner_result.get("quotaConsumption") or "")
        if quota_consumption not in {"none", "possible", "confirmed"}:
            if runner_result.get("ok") is True:
                quota_attempted = True
                quota_consumption = "confirmed"
            elif runner.get("processStarted") is True:
                quota_attempted = True
                quota_consumption = "possible"
            else:
                quota_consumption = "none"
        quota_consumed = quota_consumption in {"possible", "confirmed"}
        process_tree_value = runner_result.get("processTreeTerminated")
        process_tree_terminated = process_tree_value if isinstance(process_tree_value, bool) else None
        runner_usage = runner_result.get("usage") if isinstance(runner_result.get("usage"), dict) else {}
        usage = _agent_chat_usage_read_model({
            **runner_usage,
            "durationMs": runner_result.get("durationMs", runner.get("durationMs")),
        })
        agent_name = redact_text(str(agent.get("name") or agent_id), 120)
        if runner_result.get("ok") is True:
            guardrails = runner_result.get("guardrails") if isinstance(runner_result.get("guardrails"), dict) else {}
            guarded = (
                runner_result.get("model") == "gpt-5.5"
                and guardrails.get("toolsEnabled") is False
                and guardrails.get("computerUseEnabled") is False
                and guardrails.get("projectWorkspaceExposed") is False
                and guardrails.get("ephemeral") is True
            )
            reply = redact_text(str(runner_result.get("finalMessage") or "").strip(), output_limit)
            intent = str(runner_result.get("intent") or "")
            task_goal = str(runner_result.get("taskGoal") or "").strip()
            classification_valid = (
                intent in {"conversation", "task_request"}
                and (intent == "conversation" or bool(task_goal))
                and len(task_goal) <= 4000
                and not contains_potential_secret(task_goal)
            )
            if guarded and reply and classification_valid:
                task_fields = {
                    "taskCreated": False,
                    "taskMissionIds": [],
                    "taskStatus": "not_requested",
                    "autoExecute": False,
                }
                if intent == "task_request":
                    try:
                        task_fields = create_agent_chat_task(
                            agent_id,
                            task_goal,
                            scope_digest,
                            raw_message=message,
                        )
                    except RequestError as error:
                        task_fields = {
                            "taskCreated": False,
                            "taskMissionIds": [],
                            "taskStatus": "create_failed",
                            "autoExecute": False,
                        }
                        append_audit({
                            "type": "agent.chat_task_create_failed",
                            "agentId": agent_id,
                            "idempotencyDigest": scope_digest[:16],
                            "reason": "request_error",
                            "httpStatus": error.status,
                        })
                response = agent_chat_response_read_model({
                    "ok": True,
                    "turnId": turn_id,
                    "sessionId": session_id,
                    "agentId": agent_id,
                    "agentName": agent_name,
                    "reply": reply,
                    "status": "completed",
                    "modelTier": model_tier,
                    "intent": intent,
                    **task_fields,
                    "consumesCodexQuota": quota_consumed,
                    "quotaConsumptionStatus": quota_consumption,
                    "usage": usage,
                    "rateLimit": quota,
                })
                write_agent_chat_result(
                    agent_id,
                    session_id,
                    idempotency_key,
                    message_digest,
                    response,
                )
                append_agent_chat_transcript({
                    "turnId": turn_id,
                    "sessionId": session_id,
                    "agentId": agent_id,
                    "agentName": agent_name,
                    "idempotencyDigest": scope_digest[:16],
                    "userMessage": message,
                    "assistantReply": reply,
                    "status": "completed",
                    "modelTier": model_tier,
                    "consumesCodexQuota": quota_consumed,
                    "quotaConsumptionStatus": quota_consumption,
                    "intent": intent,
                    **task_fields,
                    "usage": usage,
                })
                append_audit({
                    "type": "agent.chat_end",
                    "turnId": turn_id,
                    "agentId": agent_id,
                    "sessionId": session_id,
                    "status": "completed",
                    "modelTier": model_tier,
                    "durationMs": usage["durationMs"],
                    "outputChars": usage["outputChars"],
                    "idempotentReplay": False,
                    "codexRequestAttempted": quota_attempted,
                    "quotaConsumptionStatus": quota_consumption,
                    "consumedCodexQuota": quota_consumption == "confirmed",
                    "mayHaveConsumedCodexQuota": quota_consumption == "possible",
                    "toolsExecuted": False,
                    "intent": intent,
                    **task_fields,
                })
                return response
            runner_result = {
                "ok": False,
                "status": "guard_validation_failed",
                "message": "Codex Chat Guard ตรวจสอบผลลัพธ์ไม่ผ่าน",
                "quotaAttempted": quota_attempted,
                "quotaConsumption": quota_consumption,
                "processTreeTerminated": process_tree_terminated,
            }

        failure_status = redact_text(str(runner_result.get("status") or "failed"), 40)
        failure_message = redact_text(
            str(runner_result.get("message") or "Codex Chat ทำงานไม่สำเร็จและไม่ได้ลองซ้ำอัตโนมัติ"),
            1200,
        )
        if failure_status == "timeout" and process_tree_terminated is not True:
            failure_status = "guard_cleanup_unconfirmed"
            failure_message = (
                "Codex Chat หมดเวลาและระบบยืนยันการปิด Process Tree ไม่ได้ "
                "จึงหยุดแบบ Fail Closed และไม่ลองซ้ำอัตโนมัติ"
            )
        http_status = 504 if failure_status == "timeout" else (
            429 if failure_status == "rate_limited" else (
                503
                if failure_status in {
                    "auth_required",
                    "config_error",
                    "guard_config_error",
                    "guard_cleanup_unconfirmed",
                    "missing",
                    "unavailable",
                }
                else 502
            )
        )
        failure_response = {
            **agent_chat_response_read_model({
                "ok": False,
                "turnId": turn_id,
                "sessionId": session_id,
                "agentId": agent_id,
                "agentName": agent_name,
                "reply": failure_message,
                "status": failure_status,
                "modelTier": model_tier,
                "consumesCodexQuota": quota_consumed,
                "quotaConsumptionStatus": quota_consumption,
                "usage": usage,
                "rateLimit": quota,
            }),
            "_httpStatus": http_status,
        }
        write_agent_chat_result(
            agent_id,
            session_id,
            idempotency_key,
            message_digest,
            failure_response,
        )
        append_agent_chat_transcript({
            "turnId": turn_id,
            "sessionId": session_id,
            "agentId": agent_id,
            "agentName": agent_name,
            "idempotencyDigest": scope_digest[:16],
            "userMessage": message,
            "assistantReply": failure_message,
            "status": failure_status,
            "modelTier": model_tier,
            "consumesCodexQuota": quota_consumed,
            "quotaConsumptionStatus": quota_consumption,
            "usage": usage,
        })
        append_audit({
            "type": "agent.chat_end",
            "turnId": turn_id,
            "agentId": agent_id,
            "sessionId": session_id,
            "status": failure_status,
            "modelTier": model_tier,
            "durationMs": usage["durationMs"],
            "outputChars": usage["outputChars"],
            "idempotentReplay": False,
            "codexRequestAttempted": quota_attempted,
            "quotaConsumptionStatus": quota_consumption,
            "consumedCodexQuota": quota_consumption == "confirmed",
            "mayHaveConsumedCodexQuota": quota_consumption == "possible",
            "processTreeTerminated": process_tree_terminated,
            "toolsExecuted": False,
            "taskCreated": False,
        })
        return failure_response
    except DataIntegrityError:
        raise
    except Exception:
        append_audit({
            "type": "agent.chat_blocked",
            "turnId": turn_id,
            "agentId": agent_id,
            "sessionDigest": payload_digest(session_id)[:16],
            "reason": "internal_error",
            "runnerInvoked": runner_invoked,
            "codexRequestAttempted": quota_attempted,
            "quotaConsumptionStatus": quota_consumption,
            "processTreeTerminated": process_tree_terminated,
        })
        return _agent_chat_error(
            "internal_error",
            "Agent Chat เกิดข้อผิดพลาดภายในและไม่ได้ลองซ้ำอัตโนมัติ",
            500,
            agent_id=agent_id,
            session_id=session_id,
            consumes_codex_quota=quota_consumption in {"possible", "confirmed"},
        )
    finally:
        if runner_invoked:
            invalidate_codex_rate_limit_cache()
        if semaphore_acquired:
            REAL_RUN_SEMAPHORE.release()
        with AGENT_CHAT_LOCK:
            AGENT_CHAT_INFLIGHT.discard(scope_digest)


def archive_mission(mission_id: str) -> dict:
    mission = find_mission(mission_id)
    if not mission:
        return {"ok": False, "kind": "not_found", "message": "Mission not found.", "_httpStatus": 404}
    if mission.get("status") in {"running", "waiting_approval"}:
        return {"ok": False, "kind": "mission_active", "message": "Active or approval-pending missions cannot be archived.", "_httpStatus": 409}
    archived_from_status = str(mission.get("status") or "unknown")
    mission["archivedFromStatus"] = archived_from_status
    mission["archivedSuccessful"] = archived_from_status == "completed"
    mission["status"] = "archived"
    mission["updatedAt"] = utc_now()
    replace_mission(mission)
    refresh_parent_mission(mission.get("parentMissionId"))
    append_audit({
        "type": "mission.archived",
        "missionId": mission_id,
        "archivedFromStatus": archived_from_status,
        "archivedSuccessful": mission["archivedSuccessful"],
    })
    return {"ok": True, "kind": "mission_archived", "mission": mission}


class BridgeHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class BridgeHandler(SimpleHTTPRequestHandler):
    server_version = f"MetafxLocalBridge/{BRIDGE_RUNTIME_VERSION}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Bridge-Policy", "local-runner-no-frontend-secrets")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'")
        super().end_headers()

    def send_json(self, payload, status: int = 200) -> None:
        safe_payload = sanitize_json_value(payload, collection_limit=1000, string_limit=20000)
        body = json.dumps(safe_payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_result(self, payload: dict, default_status: int = 200) -> None:
        result = frontend_api_result(payload)
        status = int(result.pop("_httpStatus", default_status))
        self.send_json(result, status=status)

    def validate_local_request(self) -> None:
        host_header = str(self.headers.get("Host") or "").strip().lower()
        if host_header.startswith("["):
            host_name = host_header.split("]", 1)[0] + "]"
        else:
            host_name = host_header.split(":", 1)[0]
        if host_name not in {"127.0.0.1", "localhost", "[::1]"}:
            raise RequestError("Local bridge accepts loopback Host headers only.", 403)
        origin = str(self.headers.get("Origin") or "").strip()
        if origin:
            parsed_origin = urlparse(origin)
            origin_host = (parsed_origin.hostname or "").lower()
            origin_port = parsed_origin.port or 80
            if parsed_origin.scheme != "http" or origin_host not in {"127.0.0.1", "localhost", "::1"} or origin_port != self.server.server_port:
                raise RequestError("Cross-origin requests are not allowed.", 403)
        if str(self.headers.get("Sec-Fetch-Site") or "").lower() == "cross-site":
            raise RequestError("Cross-site requests are not allowed.", 403)

    def static_path_allowed(self, raw_path: str) -> bool:
        path = unquote(urlparse(raw_path).path)
        if "\x00" in path or "\\" in path or ".." in path.split("/"):
            return False
        if any(segment.startswith(".") for segment in path.split("/") if segment):
            return False
        if path in {"/", "/index.html"}:
            return True
        if not (path in STATIC_ALLOWED_EXACT or any(path.startswith(prefix) for prefix in STATIC_ALLOWED_PREFIXES)):
            return False
        candidate = (PROJECT_ROOT / path.lstrip("/")).resolve(strict=False)
        for allowed_root in (PROJECT_ROOT / "frontend", PROJECT_ROOT / "contracts"):
            try:
                candidate.relative_to(allowed_root.resolve(strict=False))
                return True
            except ValueError:
                continue
        return False

    def read_payload(self) -> dict:
        content_type = str(self.headers.get("Content-Type") or "").lower()
        if not content_type.startswith("application/json"):
            raise RequestError("POST requests require application/json.", 415)
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError as error:
            raise RequestError("Invalid Content-Length.", 400) from error
        if length <= 0:
            return {}
        if length > MAX_REQUEST_BYTES:
            raise RequestError(f"Request body exceeds {MAX_REQUEST_BYTES} bytes.", 413)
        try:
            raw = self.rfile.read(length).decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise RequestError("Request body must be UTF-8.", 400) from error
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise RequestError("Malformed JSON request body.", 400) from error
        if not isinstance(payload, dict):
            raise RequestError("JSON request body must be an object.", 422)
        return payload

    def do_HEAD(self) -> None:
        try:
            self.validate_local_request()
            if not self.static_path_allowed(self.path):
                self.send_error(404, "Static path is not published")
                return
            super().do_HEAD()
        except RequestError as error:
            self.send_json({"ok": False, "error": str(error)}, status=error.status)
        except DataIntegrityError:
            request_id = safe_id(None, "request")
            try:
                append_audit({"type": "bridge.data_integrity_failed", "requestId": request_id, "path": urlparse(self.path).path})
            except Exception:
                pass
            self.send_json({
                "ok": False,
                "kind": "data_integrity_error",
                "error": "A local JSON store failed integrity validation. Restore its .bak file before continuing.",
                "requestId": request_id,
            }, status=503)
        except Exception:
            request_id = safe_id(None, "request")
            try:
                append_audit({"type": "bridge.request_failed", "requestId": request_id, "path": urlparse(self.path).path})
            except Exception:
                pass
            self.send_json({"ok": False, "error": "Internal guarded bridge error.", "requestId": request_id}, status=500)

    def do_GET(self) -> None:
        try:
            self._do_GET_guarded()
        except RequestError as error:
            self.send_json({"ok": False, "error": str(error)}, status=error.status)
        except DataIntegrityError:
            request_id = safe_id(None, "request")
            try:
                append_audit({
                    "type": "bridge.data_integrity_failed",
                    "requestId": request_id,
                    "path": urlparse(self.path).path,
                })
            except Exception:
                pass
            self.send_json({
                "ok": False,
                "kind": "data_integrity_error",
                "error": "A local JSON store failed integrity validation. Restore its .bak file before continuing.",
                "requestId": request_id,
            }, status=503)
        except Exception:
            request_id = safe_id(None, "request")
            try:
                append_audit({"type": "bridge.request_failed", "requestId": request_id, "path": urlparse(self.path).path})
            except Exception:
                pass
            self.send_json({"ok": False, "error": "Internal guarded bridge error.", "requestId": request_id}, status=500)

    def _do_GET_guarded(self) -> None:
        try:
            self.validate_local_request()
        except RequestError as error:
            self.send_json({"ok": False, "error": str(error)}, status=error.status)
            return
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/health":
            health = runtime_health()
            health["endpoint"] = {
                "host": "127.0.0.1",
                "port": int(self.server.server_port),
                "url": f"http://127.0.0.1:{self.server.server_port}/",
            }
            self.send_json(health, status=200 if health["ok"] else 503)
            return
        if path == "/api/bridge/status":
            self.send_json(bridge_status_read_model())
            return
        if path == "/api/operator-mode":
            self.send_json(operator_mode_read_model())
            return
        if path == "/api/capabilities":
            self.send_json(capability_registry())
            return
        if path == "/api/codex/rate-limits":
            force = str(query.get("refresh", [""])[0]).lower() in {"1", "true", "yes"}
            self.send_json(codex_rate_limits(force=force))
            return
        if path == "/api/agents":
            self.send_json(read_json(AGENTS_PATH, {"agents": []}))
            return
        if path == "/api/tools":
            self.send_json(load_tool_permissions())
            return
        if path == "/api/orchestration":
            self.send_json(load_orchestration_contract())
            return
        if path == "/api/mission-strategy-table":
            self.send_json(prop_report(MISSION_STRATEGY_TABLE_PROP_ID))
            return
        if path == "/api/missions":
            all_missions = load_missions()
            missions = all_missions
            status_filter = str(query.get("status", [""])[0])
            if status_filter:
                missions = [mission for mission in missions if mission.get("status") == status_filter]
            counts: dict[str, int] = {}
            for mission in all_missions:
                key = str(mission.get("status") or "unknown")
                counts[key] = counts.get(key, 0) + 1
            self.send_json({
                "missions": [mission_read_model_item(mission) for mission in missions],
                "counts": counts,
                "readModel": "mission_list_v1",
                "updatedAt": utc_now(),
            })
            return
        if path == "/api/reports":
            self.send_json({
                "reports": [report_read_model_item(report) for report in load_runtime_reports()],
                "readModel": "report_list_v1",
                "updatedAt": utc_now(),
            })
            return
        if path == "/api/ui-session":
            self.send_json(read_json(UI_SESSION_PATH, {"session": None, "updatedAt": None}))
            return
        if path == "/api/audit":
            self.send_json({"events": tail_jsonl(AUDIT_PATH, limit=80), "updatedAt": utc_now()})
            return
        if path == "/api/agent-events":
            self.send_json({"events": load_agent_events(), "updatedAt": utc_now()})
            return
        if path == "/api/memory":
            self.send_json(load_memory_index())
            return
        if path == "/api/memory/search":
            search_text = query.get("q", [""])[0]
            self.send_json({"query": search_text, "items": search_memory_items(search_text), "updatedAt": utc_now()})
            return
        if path == "/api/meetings":
            self.send_json({"meetings": load_meeting_records(), "updatedAt": utc_now()})
            return
        if path.startswith("/api/props/") and path.endswith("/connections"):
            prop_id = path.removeprefix("/api/props/").removesuffix("/connections").strip("/")
            if not SAFE_ID_PATTERN.fullmatch(prop_id) or not find_room_prop(prop_id):
                raise RequestError("Unknown dashboard id.", 404)
            self.send_json({"ok": True, "connectionChecklist": dashboard_connection_checklist(prop_id)})
            return
        if path.startswith("/api/props/") and path.endswith("/report"):
            prop_id = path.removeprefix("/api/props/").removesuffix("/report").strip("/")
            self.send_json(prop_report(prop_id))
            return
        if path.startswith("/api/"):
            self.send_json({"ok": False, "error": f"Unknown endpoint: {path}"}, status=404)
            return
        if not self.static_path_allowed(self.path):
            self.send_error(404, "Static path is not published")
            return
        super().do_GET()

    def do_POST(self) -> None:
        try:
            self.validate_local_request()
            path = urlparse(self.path).path
            payload = self.read_payload()
            if path == "/api/operator-mode":
                self.send_result(set_operator_mode(payload))
                return
            if path == "/api/agents/chat":
                self.send_result(run_agent_chat_request(payload))
                return
            if path == "/api/manager/delegate":
                self.send_result(manager_delegate(payload))
                return
            mission_action = re.fullmatch(r"/api/missions/([^/]+)/(approval|execute|archive)", path)
            if mission_action:
                mission_id = unquote(mission_action.group(1))
                if not SAFE_ID_PATTERN.fullmatch(mission_id):
                    raise RequestError("Invalid mission id.", 422)
                action = mission_action.group(2)
                if action == "approval":
                    self.send_result(approve_mission(mission_id, payload))
                elif action == "execute":
                    self.send_result(execute_mission(mission_id, payload))
                else:
                    self.send_result(archive_mission(mission_id))
                return
            if path == "/api/missions":
                request_payload = {**payload, "toolId": str(payload.get("toolId") or "manager_mission")}
                self.send_result(run_bridge_task(request_payload))
                return
            if path == "/api/ui-session":
                session = sanitize_json_value(payload.get("session", payload))
                write_json(UI_SESSION_PATH, {"updatedAt": utc_now(), "session": session})
                self.send_json({"ok": True, "updatedAt": utc_now()})
                return
            if path == "/api/agent-events":
                if is_visual_simulation(payload):
                    self.send_json({"ok": True, "suppressed": True, "reason": "visual_simulation_not_durable"})
                    return
                event = append_agent_event(payload)
                if not event.get("simulation"):
                    append_audit({"type": "agent.event", "agentId": event["agentId"], "kind": event["kind"], "title": event["title"], "missionId": event.get("missionId")})
                self.send_json({"ok": True, "event": event})
                return
            if path == "/api/memory/items":
                item = upsert_memory_item(payload)
                self.send_json({"ok": True, "item": item})
                return
            if path == "/api/meetings":
                if is_visual_simulation(payload):
                    self.send_json({"ok": True, "suppressed": True, "reason": "visual_simulation_not_durable"})
                    return
                record = append_meeting_record(payload, "meeting")
                self.send_json({"ok": True, "meeting": record})
                return
            if path == "/api/meetings/turn":
                if is_visual_simulation(payload):
                    self.send_json({"ok": True, "suppressed": True, "reason": "visual_simulation_not_durable"})
                    return
                record = append_meeting_record(payload, "meeting.turn")
                self.send_json({"ok": True, "meeting": record})
                return
            if path == "/api/bridge/run":
                self.send_result(run_bridge_task(payload))
                return
            connection_refresh = re.fullmatch(r"/api/props/([^/]+)/connections/refresh", path)
            if connection_refresh:
                prop_id = unquote(connection_refresh.group(1))
                if not SAFE_ID_PATTERN.fullmatch(prop_id) or not find_room_prop(prop_id):
                    raise RequestError("Unknown dashboard id.", 404)
                self.send_result(refresh_dashboard_connections(prop_id))
                return
            if path == "/api/integrations/metatrader/discover":
                prop_id = str(payload.get("propId") or "").strip()
                if not SAFE_ID_PATTERN.fullmatch(prop_id) or not find_room_prop(prop_id):
                    raise RequestError("Unknown dashboard id.", 404)
                self.send_result(run_metatrader_discovery(prop_id))
                return
            if path == "/api/integrations/metatrader/select":
                prop_id = str(payload.get("propId") or "").strip()
                candidate_id = str(payload.get("candidateId") or "").strip()
                self.send_result(select_metatrader_target(prop_id, candidate_id))
                return
            self.send_json({"ok": False, "error": f"Unknown endpoint: {path}"}, status=404)
        except RequestError as error:
            self.send_json({"ok": False, "error": str(error)}, status=error.status)
        except DataIntegrityError:
            request_id = safe_id(None, "request")
            try:
                append_audit({"type": "bridge.data_integrity_failed", "requestId": request_id, "path": urlparse(self.path).path})
            except Exception:
                pass
            self.send_json({
                "ok": False,
                "kind": "data_integrity_error",
                "error": "A local JSON store failed integrity validation. Restore its .bak file before continuing.",
                "requestId": request_id,
            }, status=503)
        except Exception:
            request_id = safe_id(None, "request")
            try:
                append_audit({"type": "bridge.request_failed", "requestId": request_id, "path": urlparse(self.path).path})
            except Exception:
                pass
            self.send_json({"ok": False, "error": "Internal guarded bridge error.", "requestId": request_id}, status=500)

    def log_message(self, format: str, *args) -> None:
        message = format % args
        if "/api/ui-session" in message:
            return
        super().log_message(format, *args)


def main() -> int:
    parser = argparse.ArgumentParser(description="Metafxclub AI Agent HQ local bridge server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4186)
    args = parser.parse_args()

    if args.host != "127.0.0.1":
        print("Refusing to bind the local bridge anywhere except 127.0.0.1.", file=sys.stderr)
        return 2
    if not 1024 <= args.port <= 65535:
        print("Refusing to use a port outside 1024-65535.", file=sys.stderr)
        return 2

    ensure_runtime_dir()
    ensure_memory_dir()
    ensure_operator_mode_store()
    reconciled_approval_count = reconcile_stale_approval_missions()
    recovered_count = recover_interrupted_missions()
    reconciled_parent_count = reconcile_parent_mission_statuses()
    httpd = BridgeHTTPServer((args.host, args.port), BridgeHandler)
    actual_port = int(httpd.server_port)
    try:
        start_mission_worker()
        append_audit({
            "type": "bridge.server_start",
            "host": args.host,
            "port": actual_port,
            "operatorMode": load_operator_mode_record().get("mode"),
            "reconciledApprovalMissions": reconciled_approval_count,
            "recoveredInterruptedMissions": recovered_count,
            "reconciledParentMissions": reconciled_parent_count,
            "missionWorker": mission_worker_read_model(),
        })
        print(f"Metafx Local Bridge running at http://{args.host}:{actual_port}/", flush=True)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        stop_mission_worker()
        append_audit({"type": "bridge.server_stop", "host": args.host, "port": actual_port})
    return 0


if __name__ == "__main__":
    sys.exit(main())
