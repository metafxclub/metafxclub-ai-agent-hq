from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
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
BRIDGE_RUNTIME_VERSION = "0.6.1"
SERVER_STARTED_AT = datetime.now(timezone.utc).isoformat()
SERVER_STARTED_MONOTONIC = time.monotonic()
RUNTIME_DIR = PROJECT_ROOT / "data" / "runtime"
MISSIONS_PATH = RUNTIME_DIR / "missions.json"
AUDIT_PATH = RUNTIME_DIR / "bridge-audit.jsonl"
UI_SESSION_PATH = RUNTIME_DIR / "ui-session.json"
AGENT_EVENTS_PATH = RUNTIME_DIR / "agent-events.jsonl"
MEMORY_DIR = PROJECT_ROOT / "data" / "memory"
MEMORY_INDEX_PATH = MEMORY_DIR / "memory-index.json"
MEETING_TRANSCRIPTS_PATH = MEMORY_DIR / "meetings" / "meeting-transcripts.jsonl"
AGENTS_PATH = PROJECT_ROOT / "contracts" / "agents" / "agents.json"
ROOM_PATH = PROJECT_ROOT / "contracts" / "rooms" / "command-room.json"
PROPERTY_ROLE_MAP_PATH = PROJECT_ROOT / "contracts" / "props" / "property-role-map.json"
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
REAL_RUN_SEMAPHORE = threading.BoundedSemaphore(value=1)
RATE_LIMIT_STATE: dict[str, list[float]] = {}
CODEX_RATE_LIMIT_CACHE: dict[str, object] = {
    "payload": None,
    "fetchedMonotonic": 0.0,
    "invalidated": False,
}
CODEX_RATE_LIMIT_CACHE_TTL_SECONDS = 75
CODEX_RATE_LIMIT_STALE_MAX_SECONDS = 15 * 60
CODEX_RATE_LIMIT_FORCE_MIN_SECONDS = 15
CODEX_RATE_LIMIT_TELEMETRY_MISSION_ID = "system-codex-rate-monitor"
CODEX_RATE_LIMIT_OWNER_AGENT_ID = "codex_mcp_operator"
CODEX_RUNNER_PYTHON = PROJECT_ROOT / "runner" / ".venv" / "Scripts" / "python.exe"
CODEX_RUNNER_SCRIPT = PROJECT_ROOT / "runner" / "codex_cli_runner.py"

STATIC_ALLOWED_EXACT = {"/", "/index.html", "/frontend", "/frontend/"}
STATIC_ALLOWED_PREFIXES = ("/frontend/", "/contracts/")
LOCAL_HOSTS = {"127.0.0.1", "127.0.0.1:4186", "localhost", "localhost:4186", "[::1]", "[::1]:4186"}
LOCAL_ORIGINS = {"http://127.0.0.1:4186", "http://localhost:4186", "http://[::1]:4186"}
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


def payload_digest(*parts: str) -> str:
    joined = "\n".join(str(part or "") for part in parts)
    return hashlib.sha256(joined.encode("utf-8", errors="replace")).hexdigest()


def mission_payload_digest(mission: dict) -> str:
    """Bind one approval to the complete execution-relevant mission packet."""
    packet = {
        "owner": str(mission.get("owner") or ""),
        "toolId": str(mission.get("toolId") or ""),
        "targetId": str(mission.get("targetId") or ""),
        "detail": str(mission.get("detail") or ""),
        "modelTier": str(mission.get("modelTier") or ""),
        "budget": mission.get("budget") if isinstance(mission.get("budget"), dict) else {},
        "risk": str(mission.get("risk") or ""),
        "reportType": str(mission.get("reportType") or ""),
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
    if agent_id == "manager":
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
    routed_reports = [
        report for report in load_runtime_reports(limit=120)
        if prop_id == report.get("linkedPropId")
    ][:8]
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
        "updatedAt": utc_now(),
    }
    if is_global_mission_view:
        response.update({
            "missionScope": "global_all_missions",
            "missionSummary": summarize_missions(all_missions),
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


def run_safe_command(command: list[str], timeout: int = 8, output_limit: int = 1200, input_text: str | None = None) -> dict:
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
    if codex["status"] == "ready":
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
            "realCodexTaskDefault": "approval_required",
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
            runtime_ready = codex_status == "ready"
        elif tool_id == "mcp_tool_run":
            runtime_status = f"{mcp_status}_adapter_unimplemented"
            runtime_ready = False
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
            "autoRunnable": bool(policy.get("autoRunnable", False)),
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
        return "right_server_racks"
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
    """Fail closed on legacy or expired records that still claim to wait for approval."""
    reconciled: list[dict] = []
    parent_ids: set[str] = set()
    now = datetime.now(timezone.utc)
    reconciled_at = utc_now()
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            if mission.get("status") != "waiting_approval":
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
            if mission.get("status") != "running" or approval.get("state") != "consumed":
                continue
            mission["status"] = "failed"
            mission["phase"] = "interrupted"
            mission["errorCode"] = "bridge_restart_interrupted"
            mission["result"] = (
                "The previous Bridge process ended while this guarded task was running. "
                "Its single-use approval remains consumed and no automatic retry was attempted."
            )
            mission["updatedAt"] = recovered_at
            mission["completedAt"] = recovered_at
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
    active_count = sum(counts.get(status, 0) for status in ("queued", "running", "waiting_approval"))
    attention_count = outcome_summary["notSucceeded"] if not active_count else sum(
        1 for item in children if mission_outcome_status(item) in {"blocked", "failed", "unknown"}
    )
    delegation = parent.get("delegation") if isinstance(parent.get("delegation"), dict) else {}
    delegation["subtaskCount"] = len(children)
    delegation["subtaskStatusCounts"] = counts
    delegation["lastAggregatedAt"] = utc_now()

    if active_count:
        parent["status"] = "running"
        parent["phase"] = "awaiting_specialists"
        delegation["state"] = "awaiting_specialists"
        parent["result"] = f"Manager is waiting for {active_count} of {len(children)} specialist missions."
        parent["completedAt"] = None
    else:
        completed_count = outcome_summary["succeeded"]
        clean_completion = completed_count == len(children) and attention_count == 0
        parent["status"] = "completed" if clean_completion else "blocked"
        parent["phase"] = "synthesized" if clean_completion else "review_required"
        delegation["state"] = parent["phase"]
        parent["result"] = (
            f"Manager collected {completed_count}/{len(children)} specialist results and completed the executive synthesis."
            if clean_completion
            else f"Manager collected all terminal specialist states; {attention_count} mission(s) require review before closure."
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
            "nextActions": [] if clean_completion else ["Review blocked, failed, or archived-without-success specialist missions at Mission Strategy Table"],
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


def find_mission_by_idempotency(idempotency_key: str) -> dict | None:
    if not idempotency_key:
        return None
    return next((mission for mission in load_missions() if mission.get("idempotencyKey") == idempotency_key), None)


def same_idempotency_scope(mission: dict, requester: str, tool_id: str, owner: str) -> bool:
    return (
        str(mission.get("requester") or "") == requester
        and str(mission.get("toolId") or "") == tool_id
        and str(mission.get("owner") or "") == owner
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
    prompt = redact_text(str(payload.get("prompt") or payload.get("detail") or payload.get("title") or "Review mission packet.").strip(), 8000)
    agent_id = str(payload.get("agentId") or payload.get("owner") or "manager")
    requester = str(payload.get("requester") or "human")
    tool_id = str(payload.get("toolId") or "manager_mission")
    tool_policy = get_tool_policy(tool_id) or {}
    risk = effective_risk(payload.get("risk"), tool_policy.get("risk"))
    target_id = str(payload.get("targetId") or pick_target_for_task(prompt))
    model_tier, budget = resolve_budget(payload, agent_id, tool_policy, allow_model_override=allow_model_override)
    raw_idempotency_key = str(payload.get("idempotencyKey") or "").strip()
    if raw_idempotency_key and not SAFE_IDEMPOTENCY_PATTERN.fullmatch(raw_idempotency_key):
        raise RequestError("Idempotency key must be a short safe identifier.", 422)
    idempotency_key = raw_idempotency_key
    existing = find_mission_by_idempotency(idempotency_key)
    if existing:
        if same_idempotency_scope(existing, requester, tool_id, agent_id):
            return existing
        raise RequestError("Idempotency key is already used by a different mission scope.", 409)

    approval_required = bool(tool_policy.get("approvalRequired", False) or tool_id in APPROVAL_REQUIRED)
    approval_minutes = clamp_int((load_orchestration_contract().get("costRateGuard") or {}).get("approvalTtlMinutes"), 15, 1, 1440)
    approval = {
        "required": approval_required,
        "id": safe_id(None, "approval") if approval_required else None,
        "state": "pending" if approval_required else "not_required",
        "requiredActors": required_approval_actors(risk) if approval_required else [],
        "decisions": [],
        "expiresAt": utc_after(approval_minutes) if approval_required else None,
        "consumedAt": None,
        "payloadDigest": None,
    }
    now = utc_now()
    mission = {
        "id": safe_id(payload.get("id"), "mission"),
        "title": redact_text(str(payload.get("title") or prompt[:72]), 160),
        "detail": prompt,
        "owner": agent_id,
        "requester": requester,
        "parentMissionId": payload.get("parentMissionId"),
        "subtaskIds": payload.get("subtaskIds") if isinstance(payload.get("subtaskIds"), list) else [],
        "toolId": tool_id,
        "targetId": target_id,
        "status": "waiting_approval" if approval_required and status == "queued" else status,
        "risk": risk,
        "modelTier": model_tier,
        "reportType": str(payload.get("reportType") or report_type_for_prop(target_id)),
        "idempotencyKey": idempotency_key or None,
        "budget": budget,
        "approval": approval,
        "result": "",
        "artifactPath": None,
        "reportIds": [],
        "attemptCount": 0,
        "createdAt": now,
        "updatedAt": now,
        "completedAt": None,
    }
    if approval_required:
        approval["payloadDigest"] = mission_payload_digest(mission)
    with MISSIONS_LOCK:
        missions = load_missions()
        if idempotency_key:
            existing = next((item for item in missions if item.get("idempotencyKey") == idempotency_key), None)
            if existing:
                if same_idempotency_scope(existing, requester, tool_id, agent_id):
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
    })
    return mission


def manager_delegate(payload: dict) -> dict:
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

    idempotency_key = str(payload.get("idempotencyKey") or "").strip()
    if idempotency_key and not SAFE_IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        return {"ok": False, "kind": "invalid_idempotency_key", "message": "Idempotency key must be a short safe identifier.", "_httpStatus": 422}
    existing = find_mission_by_idempotency(idempotency_key)
    if existing and same_idempotency_scope(existing, requester, "manager_delegate", "manager"):
        subtask_ids = existing.get("subtaskIds") or []
        subtasks = [mission for mission in load_missions() if mission.get("id") in subtask_ids]
        reports = [report for report in load_runtime_reports() if report.get("linkedMissionId") == existing.get("id")]
        return {"ok": True, "kind": "manager_plan", "parent": existing, "subtasks": subtasks, "report": reports[0] if reports else None, "idempotentReplay": True}
    if existing:
        return {"ok": False, "kind": "idempotency_conflict", "message": "Idempotency key is already used by a different mission scope.", "_httpStatus": 409}

    contract = load_orchestration_contract()
    manager_rules = contract.get("managerAutoDelegation") if isinstance(contract.get("managerAutoDelegation"), dict) else {}
    guard = contract.get("costRateGuard") if isinstance(contract.get("costRateGuard"), dict) else {}
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
    }, status="running", allow_model_override=True)

    max_subtasks = clamp_int(manager_rules.get("maxSubtasks"), 6, 1, 12)
    matched_rules = []
    seen = set()
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
            "risk": str(rule.get("risk") or tool_policy.get("risk") or "medium"),
            "modelTier": str(rule.get("modelTier") or role_default_model_tier(agent_id)),
            "reportType": str(rule.get("reportType") or report_type_for_prop(target_id)),
            "idempotencyKey": f"{parent['id']}:subtask:{index}",
        }, status="queued", allow_model_override=True)
        subtasks.append(subtask)

    delegated_at = utc_now()
    subtask_status_counts = summarize_missions(subtasks)["byStatus"]
    parent["subtaskIds"] = [item["id"] for item in subtasks]
    parent["status"] = "running" if subtasks else "blocked"
    parent["phase"] = "delegated" if subtasks else "delegation_blocked"
    parent["result"] = (
        f"Delegated {len(subtasks)} guarded specialist missions; each real run remains mission-bound and approval-gated. No real tool was executed."
        if subtasks
        else "No specialist mission passed the backend tool-permission matrix. Nothing was executed."
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
        "nextActions": ["Review each specialist mission", "Approve only the intended bounded Codex run", "Collect structured reports before Manager synthesis"],
    })
    parent["reportIds"] = [report["id"]]
    replace_mission(parent)
    append_audit({
        "type": "manager.delegated",
        "missionId": parent["id"],
        "subtaskIds": parent["subtaskIds"],
        "status": parent["status"],
        "phase": parent["phase"],
        "plannerMode": "deterministic_guarded_mission_queue",
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
        mission["result"] = f"Adapter {tool_id} is not implemented. Live and external actions remain disabled."
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        refresh_parent_mission(mission.get("parentMissionId"))
        append_audit({"type": "adapter.blocked", "missionId": mission_id, "toolId": tool_id})
        return {"ok": False, "kind": "adapter_not_implemented", "mission": mission, "message": mission["result"], "_httpStatus": 501}

    status = bridge_status()
    if status.get("codex", {}).get("status") != "ready":
        mission["status"] = "waiting_approval"
        mission["runnerStatus"] = status.get("codex", {}).get("status")
        mission["result"] = status.get("codex", {}).get("message") or "Codex runner is not ready."
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
            "message": "Codex reports that the current account rate limit is reached. No runner task was started.",
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
        mission["result"] = "The guarded runner failed internally. No automatic retry was attempted."
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
            self.send_json(health, status=200 if health["ok"] else 503)
            return
        if path == "/api/bridge/status":
            self.send_json(bridge_status())
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

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print("Refusing to bind the local bridge to a non-loopback address.", file=sys.stderr)
        return 2

    ensure_runtime_dir()
    ensure_memory_dir()
    reconciled_approval_count = reconcile_stale_approval_missions()
    recovered_count = recover_interrupted_missions()
    httpd = BridgeHTTPServer((args.host, args.port), BridgeHandler)
    append_audit({
        "type": "bridge.server_start",
        "host": args.host,
        "port": args.port,
        "reconciledApprovalMissions": reconciled_approval_count,
        "recoveredInterruptedMissions": recovered_count,
    })
    print(f"Metafx Local Bridge running at http://{args.host}:{args.port}/", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        append_audit({"type": "bridge.server_stop", "host": args.host, "port": args.port})
    return 0


if __name__ == "__main__":
    sys.exit(main())
