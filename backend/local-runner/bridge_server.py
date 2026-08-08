from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import ipaddress
import importlib.util
import json
import math
import os
import re
import secrets
import signal
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_RUNTIME_VERSION = "0.9.1"
SERVER_STARTED_AT = datetime.now(timezone.utc).isoformat()
SERVER_STARTED_MONOTONIC = time.monotonic()
RUNTIME_DIR = PROJECT_ROOT / "data" / "runtime"
PROJECT_RUNTIME_DIR = RUNTIME_DIR
MISSIONS_PATH = RUNTIME_DIR / "missions.json"
OPERATOR_MODE_PATH = RUNTIME_DIR / "operator-mode.json"
COLLABORATION_SCHEDULE_PATH = RUNTIME_DIR / "collaboration-schedule.json"
DASHBOARD_WORKFLOW_SETTINGS_PATH = RUNTIME_DIR / "dashboard-workflow-settings.json"
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
AI_TRADE_COUNCIL_PROMPTS_PATH = (
    PROJECT_ROOT
    / "contracts"
    / "orchestration"
    / "ai-trade-council-prompts.json"
)
RUNTIME_REPORTS_DIR = RUNTIME_DIR / "reports"
AGENT_EVENTS_LOCK = threading.Lock()
MEETING_TRANSCRIPTS_LOCK = threading.Lock()
COLLABORATION_SCHEDULE_LOCK = threading.RLock()
DASHBOARD_WORKFLOW_SETTINGS_LOCK = threading.RLock()
COLLABORATION_RUN_LOCK = threading.Lock()
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
AI_TRADE_COUNCIL_RUN_SEMAPHORE = threading.BoundedSemaphore(value=3)
MISSION_WORKER_LOCK = threading.RLock()
MISSION_WORKER_WAKE = threading.Event()
MISSION_WORKER_STOP = threading.Event()
MISSION_WORKER_THREAD: threading.Thread | None = None
MISSION_WORKER_WATCHDOG_THREAD: threading.Thread | None = None
AI_TRADE_COUNCIL_WORKER_THREADS: list[threading.Thread] = []
MISSION_WORKER_PROCESS_LOCK = threading.RLock()
MISSION_WORKER_PROCESS: subprocess.Popen | None = None
MISSION_WORKER_JOB_HOLDER: dict | None = None
MISSION_WORKER_PROCESSES: dict[str, dict[str, object]] = {}
COLLABORATION_SCHEDULER_THREAD: threading.Thread | None = None
COLLABORATION_SESSION_THREAD: threading.Thread | None = None
COLLABORATION_SCHEDULER_STOP = threading.Event()
COLLABORATION_SCHEDULER_WAKE = threading.Event()
AI_TRADE_COUNCIL_AUTOMATION_LOCK = threading.RLock()
AI_TRADE_COUNCIL_AUTOMATION_RUN_LOCK = threading.Lock()
AI_TRADE_COUNCIL_QUEUE_LOCK = threading.RLock()
UI_SESSION_LOCK = threading.RLock()
UI_SESSION_REPLACE_MAX_ATTEMPTS = 4
UI_SESSION_REPLACE_INITIAL_DELAY_SECONDS = 0.025
PARENT_MISSION_REFRESH_LOCK = threading.RLock()
AI_TRADE_COUNCIL_ANALYSIS_CACHE_LOCK = threading.RLock()
AI_TRADE_COUNCIL_ANALYSIS_CACHE: dict[str, dict[str, dict]] = {}
AI_TRADE_COUNCIL_DEEP_ANALYSIS_PACKAGE_LOCK = threading.RLock()
AI_TRADE_COUNCIL_AUTOMATION_STOP = threading.Event()
AI_TRADE_COUNCIL_AUTOMATION_WAKE = threading.Event()
AI_TRADE_COUNCIL_AUTOMATION_THREAD: threading.Thread | None = None
COLLABORATION_STATE_LOCK = threading.RLock()
COLLABORATION_STATE: dict[str, object] = {
    "status": "stopped",
    "activeMeetingId": None,
    "activeMissionId": None,
    "startedAt": None,
    "heartbeatAt": None,
    "lastError": None,
}
MISSION_WORKER_STATE: dict[str, object] = {
    "status": "stopped",
    "workerId": None,
    "currentMissionId": None,
    "startedAt": None,
    "heartbeatAt": None,
    "lastError": None,
}
RATE_LIMIT_STATE: dict[str, list[float]] = {}
PERSISTED_RATE_LIMIT_SCHEMA = "local-rate-limit-state-v1"
PERSISTED_RATE_LIMIT_PREFIXES = ("real:",)
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
AI_TRADE_COUNCIL_AUTOMATION_STORE_FILENAME = "ai-trade-council-automation.json"
AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES = (
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
    "W1",
    "MN1",
)
AI_TRADE_COUNCIL_TIMEFRAME_SECONDS = {
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
    "W1": 604800,
    "MN1": 2592000,
}
AI_TRADE_COUNCIL_HIGHER_TIMEFRAME = {
    "M5": "M15",
    "M15": "H1",
    "M30": "H4",
    "H1": "H4",
    "H4": "D1",
    "D1": "W1",
    "W1": "MN1",
    "MN1": None,
}
AI_TRADE_COUNCIL_AUTOMATION_POLL_SECONDS = 5
AI_TRADE_COUNCIL_AUTOMATION_SETTLE_SECONDS = 10
AI_TRADE_COUNCIL_QUEUE_ASSEMBLY_GRACE_SECONDS = 30
AI_TRADE_COUNCIL_AUTOMATION_MAX_DAILY_ROUNDS = 24
AI_TRADE_COUNCIL_AUTOMATION_MIN_REMAINING_PERCENT = 30
AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS = (120, 180, 240, 300, 500, 1000)
AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT = 120
AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES = (1, 2, 3)
AI_TRADE_COUNCIL_DEFAULT_REQUIRED_VOTES = 3
AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION = (
    "metafx-deterministic-core20-price-action-v3"
)
AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION = (
    "metafx-protective-plan-atr-structure-v1"
)
AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MINIMUM_STOP_ATR = 1.0
AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_STRUCTURE_BUFFER_ATR = 0.25
AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MAX_STRUCTURE_DISTANCE_ATR = 3.0
AI_TRADE_COUNCIL_ANALYSIS_CACHE_MAX_ENTRIES = 8
AI_TRADE_COUNCIL_TECHNICAL_MODULES = (
    "sma_family",
    "ema_family",
    "rsi14",
    "macd_12_26_9",
    "stochastic_14_3_3",
    "atr14",
    "bollinger_20_2",
    "adx_dmi14",
    "cci20",
    "williams_r14",
    "roc12",
    "momentum10",
    "obv",
    "mfi14",
)
AI_TRADE_COUNCIL_PRICE_ACTION_MODULES = (
    "confirmed_swing_pivots",
    "support_resistance",
    "trendlines",
    "fibonacci_latest_confirmed_swing",
    "rsi_divergence",
    "macd_divergence",
)
AI_TRADE_COUNCIL_DEEP_ANALYSIS_BAR_COUNT = 300
AI_TRADE_COUNCIL_DEEP_ANALYSIS_MIN_SOURCE_BARS = 500
AI_TRADE_COUNCIL_TECHNICAL_SERIES_FIELDS = (
    "time",
    "sma20",
    "sma50",
    "sma200",
    "ema9",
    "ema20",
    "ema50",
    "ema200",
    "rsi14",
    "atr14",
    "macdLine",
    "macdSignal",
    "macdHistogram",
    "stochasticK",
    "stochasticD",
    "bollingerMiddle",
    "bollingerUpper",
    "bollingerLower",
    "adx14",
    "plusDI14",
    "minusDI14",
    "cci20",
    "williamsR14",
    "roc12",
    "momentum10",
    "obv",
    "mfi14",
    "volumeMA20",
)
METATRADER_SNAPSHOT_SCHEMA_VERSION = "metafx-hq-mt4-snapshot-v1"
METATRADER_SNAPSHOT_MAX_BYTES = 512 * 1024
METATRADER_SNAPSHOT_FRESH_SECONDS = 20
METATRADER_SNAPSHOT_MAX_BARS = 1000
METATRADER_COMMON_FILES_DIR = (
    Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    / "MetaQuotes"
    / "Terminal"
    / "Common"
    / "Files"
)
METATRADER_UNIFIED_EA_SOURCE_PATH = (
    PROJECT_ROOT
    / "integrations"
    / "mt4-trade-gateway"
    / "MetafxHQTradeGateway.mq4"
)
METATRADER_SNAPSHOT_FALLBACK_SOURCE_PATH = (
    PROJECT_ROOT
    / "integrations"
    / "mt4-readonly"
    / "MetafxHQReadOnlySnapshot.mq4"
)
# The unified EA is the primary install. The standalone indicator remains a
# read-only recovery/diagnostic option for terminals where execution is disabled.
METATRADER_SNAPSHOT_SOURCE_PATH = METATRADER_UNIFIED_EA_SOURCE_PATH
AI_TRADE_COUNCIL_WORKSPACE_DIR = PROJECT_ROOT / "workspace"
AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
    AI_TRADE_COUNCIL_WORKSPACE_DIR / "ai-trade-council" / "snapshots"
)
AI_TRADE_COUNCIL_DEEP_ANALYSIS_DIR = (
    AI_TRADE_COUNCIL_WORKSPACE_DIR / "ai-trade-council" / "deep-analysis"
)
MT4_TRADE_GATEWAY_MODULE_PATH = (
    PROJECT_ROOT / "backend" / "local-runner" / "mt4_trade_gateway.py"
)
MT4_TRADE_GATEWAY_STATE_DIRNAME = "mt4-trade-gateway"
MT4_TRADE_GATEWAY_STATUS_SCHEMA_VERSION = "metafx-hq-mt4-status-v4"
MT4_TRADE_GATEWAY_LEGACY_STATUS_SCHEMA_VERSION = "metafx-hq-mt4-status-v3"
MT4_TRADE_GATEWAY_STATUS_MAX_BYTES = 16 * 1024
MT4_TRADE_GATEWAY_STATUS_FRESH_SECONDS = 20
MT4_TRADE_GATEWAY_INIT_STATUS_SCHEMA_VERSION = "metafx-hq-mt4-init-status-v1"
MT4_TRADE_GATEWAY_INIT_STATUS_MAX_BYTES = 8 * 1024
MT4_TRADE_GATEWAY_INIT_STATUS_FRESH_SECONDS = 24 * 60 * 60
MT4_TRADE_GATEWAY_INIT_STATUS_FIELDS = frozenset({
    "schemaVersion",
    "eaVersion",
    "channelId",
    "profile",
    "gatewayMode",
    "accountMode",
    "liveArmed",
    "severity",
    "stage",
    "reasonCode",
    "warningCode",
    "returnCode",
    "observedAt",
})
MT4_TRADE_GATEWAY_STATUS_FIELDS = frozenset({
    "schemaVersion",
    "channelId",
    "profile",
    "mode",
    "demoAccount",
    "accountMode",
    "liveArmed",
    "fixedLot",
    "symbol",
    "timeframe",
    "observedAt",
    "autoTradingAllowed",
    "tradeAllowed",
    "killSwitchActive",
    "commandSchemaVersion",
    "ackSchemaVersion",
    "signedCommandVerificationAvailable",
    "activeSigningKeyId",
    "signingKeyPinned",
    "signatureAlgorithm",
    "lastSignatureVerificationStatus",
    "executionGuardReady",
    "executionGuardReason",
    "maxManagedPositions",
    "currentManagedPositions",
    "maxManagedLots",
    "currentManagedLots",
    "maxTradesToday",
    "currentTradesToday",
    "maxLossPerTradePercent",
    "maxDailyLossPercent",
    "managedDailyPnl",
    "maxAccountEquityDrawdownPercent",
    "currentAccountEquityDrawdownPercent",
    "minRewardRiskRatio",
    "minProjectedMarginLevelPercent",
    "currentMarginLevelPercent",
    "maxSnapshotAgeSeconds",
    "maxSignalDriftPoints",
    "maxQuoteAgeSeconds",
})
MT4_TRADE_GATEWAY_LEGACY_STATUS_FIELDS = (
    MT4_TRADE_GATEWAY_STATUS_FIELDS - {"demoAccount", "accountMode"}
)
MT4_TRADE_GATEWAY_LOCK = threading.RLock()
MT4_TRADE_GATEWAY_MODULE = None
MT4_TRADE_GATEWAY_REJECTED_ACK_EVENTS: set[str] = set()
AGENT_CHAT_TRANSCRIPT_FILENAME = "agent-chat-transcripts.jsonl"
AGENT_CHAT_RESULTS_DIRNAME = "agent-chat-results"
AI_TRADE_COUNCIL_CHAT_CONTEXT_MAX_CHARS = 6000
METATRADER_TARGET_PROP_IDS = frozenset({
    "right_server_racks",
    "right_tool_console",
    "left_analytics_console",
    "terminal_workstation",
})
CODEX_RUNNER_PYTHON = PROJECT_ROOT / "runner" / ".venv" / "Scripts" / "python.exe"
CODEX_RUNNER_SCRIPT = PROJECT_ROOT / "runner" / "codex_cli_runner.py"

STATIC_ALLOWED_EXACT = {"/", "/index.html", "/frontend", "/frontend/"}
STATIC_ALLOWED_PREFIXES = ("/frontend/", "/contracts/")
MAX_REQUEST_BYTES = 65536
MAX_REPORT_IMAGE_BYTES = 20 * 1024 * 1024
MAX_REPORT_DOWNLOAD_BYTES = 10 * 1024 * 1024
REPORT_IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
REPORT_DOWNLOAD_MEDIA_TYPES = {
    ".mq4": "text/plain; charset=utf-8",
    ".mq5": "text/plain; charset=utf-8",
    ".pine": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".json": "application/json",
    ".csv": "text/csv; charset=utf-8",
    ".zip": "application/zip",
}
REPORT_DOWNLOAD_TEXT_EXTENSIONS = frozenset(
    extension for extension in REPORT_DOWNLOAD_MEDIA_TYPES if extension != ".zip"
)
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
    "codex_web_research",
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

DASHBOARD_WORKFLOW_PROP_IDS = frozenset({
    "codex_mcp_portal",
    "left_server_racks",
    "right_server_racks",
    "right_tool_console",
    "left_audit_crystals",
    "left_signal_cube",
    "terminal_workstation",
    "right_status_crystals",
})

DASHBOARD_WORKFLOW_TABS = {
    "codex_mcp_portal": (
        {
            "id": "systems",
            "labelTh": "ระบบเทรดใหม่",
            "descriptionTh": "ค้นหาระบบเทรดจากแหล่งสาธารณะและตรวจรายการซ้ำกับรายงานเดิม",
            "actionIds": ["discover_trading_systems"],
        },
        {
            "id": "ea_updates",
            "labelTh": "EA และงานวิจัยใหม่",
            "descriptionTh": "ติดตาม EA แนวคิดใหม่ และงานวิจัยที่มีแหล่งอ้างอิงตรวจสอบได้",
            "actionIds": ["discover_ea_updates"],
        },
        {
            "id": "schedule",
            "labelTh": "รอบค้นหารายวัน",
            "descriptionTh": "เก็บเวลาที่ต้องการไว้ก่อน ระบบยังไม่รันงานภายนอกตามเวลาอัตโนมัติ",
            "actionIds": ["save_discovery_schedule"],
        },
        {
            "id": "catalog",
            "labelTh": "คลังรายการและ Google Sheet",
            "descriptionTh": "ดูโครงสร้างข้อมูล 42 ช่องและสถานะการเชื่อม โดย Google Sheets Adapter ยังไม่เชื่อม",
            "actionIds": [],
        },
    ),
    "left_server_racks": (
        {
            "id": "research_queue",
            "labelTh": "คิววิจัยเชิงลึก",
            "descriptionTh": "เลือกผลค้นหาจากประตูสำรวจเพื่อขยายหลักฐานและวิธีประยุกต์",
            "actionIds": ["deep_research_system"],
        },
        {
            "id": "verified_archive",
            "labelTh": "คลังวิจัยที่ตรวจแล้ว",
            "descriptionTh": "อ่านรายงานวิจัยที่ Agent ส่งกลับมายังตู้นี้",
            "actionIds": [],
        },
        {
            "id": "application",
            "labelTh": "แนวทางประยุกต์",
            "descriptionTh": "สรุปวิธีแปลงงานวิจัยเป็นกฎระบบ โดยแยกข้อเท็จจริงออกจากสมมติฐาน",
            "actionIds": [],
        },
        {
            "id": "evidence",
            "labelTh": "หลักฐานย้อนหลัง",
            "descriptionTh": "เปิดรายงาน แหล่งอ้างอิง และประวัติ Mission ที่ Backend บันทึกไว้",
            "actionIds": [],
        },
    ),
    "right_server_racks": (
        {
            "id": "builder",
            "labelTh": "สร้าง EA / Indicator",
            "descriptionTh": "สร้างร่าง Source Code จากระบบที่เลือก โดยยังไม่ Compile หรือรัน MT4/MT5",
            "actionIds": ["build_strategy_code"],
        },
        {
            "id": "code_review",
            "labelTh": "ตรวจ Source Code",
            "descriptionTh": "ตรวจโครงสร้างและความเสี่ยงของ Source Code แบบ Static โดยไม่เปิด MetaEditor",
            "actionIds": ["review_source_code"],
        },
        {
            "id": "compile",
            "labelTh": "สถานะ Compile และ Error",
            "descriptionTh": "แสดงผล Compile เมื่อ Compiler Adapter เชื่อมแล้ว ปัจจุบันยังเป็น Coming Soon",
            "actionIds": [],
        },
        {
            "id": "outputs",
            "labelTh": "ผลงานที่ส่งกลับ",
            "descriptionTh": "ดูรายงานและไฟล์อ้างอิงที่ Backend ตรวจแล้ว",
            "actionIds": [],
        },
    ),
    "right_tool_console": (
        {
            "id": "backtest",
            "labelTh": "Auto Backtest",
            "descriptionTh": "เตรียมแผน Backtest และช่วงข้อมูลก่อนต่อ Adapter ของ MetaTrader",
            "actionIds": ["prepare_backtest_plan"],
        },
        {
            "id": "optimization",
            "labelTh": "Auto Optimization",
            "descriptionTh": "เตรียมแผนพารามิเตอร์และเกณฑ์คัดเลือก โดยยังไม่รัน Optimization จริง",
            "actionIds": ["prepare_optimization_plan"],
        },
        {
            "id": "ea_discovery",
            "labelTh": "EA Discovery",
            "descriptionTh": "ออกแบบแผนค้นหา EA จากเป้าหมายกำไร Drawdown และจำนวน Order",
            "actionIds": ["prepare_ea_discovery_plan"],
        },
        {
            "id": "history",
            "labelTh": "ผลทดลองและประวัติ",
            "descriptionTh": "รวมรายงานแผนและผลจริงที่ Backend ส่งกลับ โดยไม่สร้างผลทดสอบจำลอง",
            "actionIds": [],
        },
    ),
    "left_audit_crystals": (
        {
            "id": "discoveries",
            "labelTh": "Indicator ที่ค้นพบใหม่",
            "descriptionTh": "ค้นหา Indicator จากเว็บไซต์สาธารณะและเก็บหลักฐานที่ตรวจย้อนกลับได้",
            "actionIds": ["discover_new_indicators"],
        },
        {
            "id": "evidence",
            "labelTh": "หลักฐานและแหล่งข้อมูล",
            "descriptionTh": "ดู URL วันที่ตรวจ และข้อจำกัดจากรายงานที่ Backend บันทึก",
            "actionIds": [],
        },
        {
            "id": "schedule",
            "labelTh": "เวลาที่ต้องการให้ค้นหา",
            "descriptionTh": "บันทึกเวลาไว้เป็นการตั้งค่าเท่านั้น Scheduler จริงยังไม่เปิดใช้งาน",
            "actionIds": ["save_indicator_scout_schedule"],
        },
        {
            "id": "archive",
            "labelTh": "ประวัติการค้นหา",
            "descriptionTh": "ดู Mission และ Report เดิมโดยไม่อ้างว่าตรวจรายการซ้ำกับระบบภายนอกแล้ว",
            "actionIds": [],
        },
    ),
    "left_signal_cube": (
        {
            "id": "today",
            "labelTh": "ข่าวตลาดวันนี้",
            "descriptionTh": "วิเคราะห์ข่าวและเหตุการณ์จากแหล่งสาธารณะที่มี URL อ้างอิง",
            "actionIds": ["analyze_daily_market_news"],
        },
        {
            "id": "pair_bias",
            "labelTh": "มุมมอง 28 คู่เงิน",
            "descriptionTh": "สร้าง Bias ระยะสั้น กลาง และยาวจากรายงานข่าวที่ตรวจแล้ว",
            "actionIds": ["build_fx_pair_bias"],
        },
        {
            "id": "horizons",
            "labelTh": "ผลกระทบตามช่วงเวลา",
            "descriptionTh": "แยกผลกระทบระยะสั้น กลาง และยาว พร้อมคำเตือนข้อมูลไม่ครบ",
            "actionIds": [],
        },
        {
            "id": "schedule_history",
            "labelTh": "เวลาอัปเดตและประวัติ",
            "descriptionTh": "บันทึกเวลาที่ต้องการและดูประวัติ โดยยังไม่เปิด Scheduler จริง",
            "actionIds": ["save_news_bias_schedule"],
        },
    ),
    "terminal_workstation": (
        {
            "id": "source",
            "labelTh": "Source EA ต้นทาง",
            "descriptionTh": "เลือกเฉพาะ Source MQL4/MQL5 ที่ Backend ตรวจสายงานและชนิดไฟล์แล้ว",
            "actionIds": ["inspect_ea_source"],
        },
        {
            "id": "development_brief",
            "labelTh": "พัฒนา EA",
            "descriptionTh": "ส่ง Brief ให้ EA Developer ทำงานใน Workspace แบบ Guarded",
            "actionIds": ["develop_ea_source"],
        },
        {
            "id": "performance_goals",
            "labelTh": "เป้าหมายประสิทธิภาพ",
            "descriptionTh": "เสนอแนวทางปรับปรุงจากเป้าหมายกำไร Drawdown และจำนวน Order โดยไม่อ้างผลทดสอบจริง",
            "actionIds": ["propose_ea_performance_improvements"],
        },
        {
            "id": "outputs",
            "labelTh": "ผลงานและสถานะตรวจ",
            "descriptionTh": "ดู Report และไฟล์ project-relative; Compile และ Install ยัง Coming Soon",
            "actionIds": [],
        },
    ),
    "right_status_crystals": (
        {
            "id": "vps",
            "labelTh": "สถานะ VPS",
            "descriptionTh": "ตรวจสุขภาพแบบ Read-only จากข้อมูลที่ Backend มองเห็นจริง",
            "actionIds": ["refresh_vps_hq_status"],
        },
        {
            "id": "hq_bridge",
            "labelTh": "สถานะ HQ และ Bridge",
            "descriptionTh": "ดูสถานะ Local Runner, Mission Worker และ Codex แบบไม่แสดงข้อมูลลับ",
            "actionIds": [],
        },
        {
            "id": "agent_settings",
            "labelTh": "ตั้งค่าการแสดงผล Agent",
            "descriptionTh": "เก็บเฉพาะค่าการแสดงผลที่ปลอดภัย ไม่รับ Token, Auth หรือ Model Credential",
            "actionIds": ["save_agent_preferences"],
        },
        {
            "id": "activity_history",
            "labelTh": "ประวัติกิจกรรม",
            "descriptionTh": "ดู Mission, Event และ Report ที่ Backend บันทึก",
            "actionIds": [],
        },
    ),
}

DASHBOARD_WORKFLOW_ACTIONS = {
    "discover_trading_systems": {
        "propId": "codex_mcp_portal",
        "tabId": "systems",
        "labelTh": "ค้นหาระบบเทรดทั่วโลก",
        "descriptionTh": "ค้นแหล่งสาธารณะ อ่านอย่างเดียว พร้อม URL และหลักฐานวันที่",
        "toolId": "codex_web_research",
        "ownerAgentId": "codex_mcp_operator",
        "reportType": "trading_system_discovery_report",
        "executionScope": "public_web_read_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "formFields": (
            {"id": "query", "labelTh": "หัวข้อที่ต้องการค้น", "type": "text", "required": False},
            {"id": "market", "labelTh": "ตลาด", "type": "text", "required": False},
            {"id": "timeframe", "labelTh": "Timeframe", "type": "text", "required": False},
        ),
    },
    "discover_ea_updates": {
        "propId": "codex_mcp_portal",
        "tabId": "ea_updates",
        "labelTh": "ค้นหา EA และงานวิจัยใหม่",
        "descriptionTh": "ค้นข้อมูล EA และงานวิจัยใหม่จากแหล่งสาธารณะที่ตรวจย้อนกลับได้",
        "toolId": "codex_web_research",
        "ownerAgentId": "codex_mcp_operator",
        "reportType": "ea_discovery_report",
        "executionScope": "public_web_read_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "formFields": (
            {"id": "query", "labelTh": "แนว EA ที่สนใจ", "type": "text", "required": False},
            {"id": "market", "labelTh": "ตลาด", "type": "text", "required": False},
            {"id": "platform", "labelTh": "แพลตฟอร์ม", "type": "select", "required": False, "options": ["any", "mt4", "mt5", "tradingview"]},
        ),
    },
    "save_discovery_schedule": {
        "propId": "codex_mcp_portal",
        "tabId": "schedule",
        "labelTh": "บันทึกเวลาค้นหารายวัน",
        "descriptionTh": "บันทึกความต้องการไว้ใน Local Runner โดยยังไม่รันงานภายนอกตามเวลา",
        "toolId": None,
        "ownerAgentId": "codex_mcp_operator",
        "reportType": None,
        "executionScope": "settings_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "formFields": (
            {"id": "enabled", "labelTh": "ต้องการเปิดเมื่อระบบ Scheduler พร้อม", "type": "boolean", "required": False},
            {"id": "times", "labelTh": "เวลาที่ต้องการ", "type": "time_list", "required": True},
        ),
    },
    "deep_research_system": {
        "propId": "left_server_racks",
        "tabId": "research_queue",
        "labelTh": "วิจัยระบบที่เลือกต่อ",
        "descriptionTh": "ตรวจหลายแหล่ง ขยายกติกา และแยกข้อเท็จจริงออกจากข้อสันนิษฐาน",
        "toolId": "codex_web_research",
        "ownerAgentId": "mission_archivist",
        "reportType": "trading_system_research_report",
        "executionScope": "public_web_read_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "ระบบต้นทาง", "type": "source_report", "required": True},
            {"id": "brief", "labelTh": "ประเด็นที่ต้องการเจาะลึก", "type": "textarea", "required": False},
        ),
    },
    "build_strategy_code": {
        "propId": "right_server_racks",
        "tabId": "builder",
        "labelTh": "สร้างร่าง EA / Indicator",
        "descriptionTh": "สร้าง Source Code ใน Workspace เท่านั้น และติดป้ายว่ายังไม่ Compile",
        "toolId": "codex_cli_task",
        "ownerAgentId": "ea_developer",
        "reportType": "ea_build_report",
        "executionScope": "workspace_source_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "ระบบต้นทาง", "type": "source_report", "required": True},
            {"id": "platform", "labelTh": "แพลตฟอร์ม", "type": "select", "required": True, "options": ["mt4", "mt5", "tradingview"]},
            {"id": "brief", "labelTh": "เงื่อนไขเพิ่มเติม", "type": "textarea", "required": False},
        ),
    },
    "review_source_code": {
        "propId": "right_server_racks",
        "tabId": "code_review",
        "labelTh": "ตรวจ Source Code แบบไม่รัน",
        "descriptionTh": "Static review เท่านั้น ไม่เปิด MetaEditor และไม่ Compile",
        "toolId": "codex_cli_task",
        "ownerAgentId": "ea_developer",
        "reportType": "ea_build_report",
        "executionScope": "workspace_analysis_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "ผลงานต้นทาง", "type": "source_report", "required": True},
            {"id": "platform", "labelTh": "แพลตฟอร์ม", "type": "select", "required": True, "options": ["mt4", "mt5", "tradingview"]},
            {"id": "brief", "labelTh": "จุดที่ต้องการตรวจ", "type": "textarea", "required": False},
        ),
    },
    "prepare_backtest_plan": {
        "propId": "right_tool_console",
        "tabId": "backtest",
        "labelTh": "เตรียมแผน Auto Backtest",
        "descriptionTh": "วางแผนชุดทดสอบและเกณฑ์อ่านผล โดยยังไม่เปิดหรือควบคุม MetaTrader",
        "toolId": "codex_cli_task",
        "ownerAgentId": "backtest_analyst",
        "reportType": "ea_experiment_report",
        "executionScope": "analysis_plan_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "EA / Source ต้นทาง", "type": "source_report", "required": True},
            {"id": "platform", "labelTh": "แพลตฟอร์ม", "type": "select", "required": False, "options": ["mt4", "mt5"]},
            {"id": "market", "labelTh": "คู่เงินหรือตลาด", "type": "text", "required": False},
            {"id": "timeframe", "labelTh": "Timeframe", "type": "select", "required": False, "options": ["M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]},
            {"id": "dateRange", "labelTh": "ช่วงข้อมูลทดสอบ", "type": "text", "required": False},
            {"id": "brief", "labelTh": "เงื่อนไขเพิ่มเติม", "type": "textarea", "required": False},
        ),
    },
    "prepare_optimization_plan": {
        "propId": "right_tool_console",
        "tabId": "optimization",
        "labelTh": "เตรียมแผน Auto Optimization",
        "descriptionTh": "วาง Parameter Range และเกณฑ์ป้องกัน Overfit โดยยังไม่รัน Optimization จริง",
        "toolId": "codex_cli_task",
        "ownerAgentId": "optimization_agent",
        "reportType": "ea_experiment_report",
        "executionScope": "analysis_plan_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "EA / Source ต้นทาง", "type": "source_report", "required": True},
            {"id": "platform", "labelTh": "แพลตฟอร์ม", "type": "select", "required": False, "options": ["mt4", "mt5"]},
            {"id": "market", "labelTh": "คู่เงินหรือตลาด", "type": "text", "required": False},
            {"id": "timeframe", "labelTh": "Timeframe", "type": "select", "required": False, "options": ["M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]},
            {"id": "targetProfitPercent", "labelTh": "กำไรเป้าหมาย (%)", "type": "number", "required": False},
            {"id": "maxDrawdownPercent", "labelTh": "Drawdown สูงสุด (%)", "type": "number", "required": False},
            {"id": "parameterRanges", "labelTh": "ช่วงพารามิเตอร์", "type": "textarea", "required": False},
            {"id": "validationMethod", "labelTh": "วิธีตรวจสอบ", "type": "select", "required": False, "options": ["train_test", "walk_forward", "out_of_sample", "monte_carlo"]},
            {"id": "brief", "labelTh": "เป้าหมายและพารามิเตอร์", "type": "textarea", "required": False},
        ),
    },
    "prepare_ea_discovery_plan": {
        "propId": "right_tool_console",
        "tabId": "ea_discovery",
        "labelTh": "เตรียมแผน EA Discovery",
        "descriptionTh": "ออกแบบรอบค้นหา EA จากเป้าหมาย โดยยังไม่ Compile, Backtest หรือ Optimization จริง",
        "toolId": "codex_cli_task",
        "ownerAgentId": "ea_developer",
        "reportType": "ea_discovery_report",
        "executionScope": "analysis_plan_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "แรงบันดาลใจต้นทาง", "type": "source_report", "required": True},
            {"id": "platform", "labelTh": "แพลตฟอร์ม", "type": "select", "required": False, "options": ["mt4", "mt5"]},
            {"id": "symbol", "labelTh": "คู่เงินหรือสัญลักษณ์", "type": "text", "required": False},
            {"id": "timeframe", "labelTh": "Timeframe", "type": "select", "required": False, "options": ["M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]},
            {"id": "targetProfitPercent", "labelTh": "กำไรเป้าหมาย (%)", "type": "number", "required": False},
            {"id": "maxDrawdownPercent", "labelTh": "Drawdown สูงสุด (%)", "type": "number", "required": False},
            {"id": "targetTrades", "labelTh": "จำนวน Order เป้าหมาย", "type": "integer", "required": False},
            {"id": "validationMethod", "labelTh": "วิธีตรวจสอบ", "type": "select", "required": False, "options": ["train_test", "walk_forward", "out_of_sample", "monte_carlo"]},
            {"id": "brief", "labelTh": "เงื่อนไขเพิ่มเติม", "type": "textarea", "required": False},
        ),
    },
    "discover_new_indicators": {
        "propId": "left_audit_crystals",
        "tabId": "discoveries",
        "labelTh": "ค้นหา Indicator ใหม่จากเว็บไซต์สาธารณะ",
        "descriptionTh": "ใช้ Guarded Web Research แบบอ่านอย่างเดียว พร้อม URL และวันที่ตรวจสอบ",
        "toolId": "codex_web_research",
        "ownerAgentId": "codex_mcp_operator",
        "reportType": "indicator_scout_report",
        "executionScope": "public_web_read_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "formFields": (
            {"id": "query", "labelTh": "Indicator หรือแนวคิดที่ต้องการหา", "type": "text", "required": False},
            {"id": "platform", "labelTh": "แพลตฟอร์ม", "type": "select", "required": False, "options": ["any", "mt4", "mt5", "tradingview"]},
            {"id": "category", "labelTh": "หมวด", "type": "select", "required": False, "options": ["any", "trend", "momentum", "volatility", "volume", "price_action", "machine_learning"]},
            {"id": "maxItems", "labelTh": "จำนวนรายการสูงสุด", "type": "integer", "required": False},
        ),
    },
    "save_indicator_scout_schedule": {
        "propId": "left_audit_crystals",
        "tabId": "schedule",
        "labelTh": "บันทึกเวลาค้นหา Indicator",
        "descriptionTh": "บันทึก Preference ใน Local Runner; ยังไม่เปิด Scheduler หรือ Screenshot Adapter",
        "toolId": None,
        "ownerAgentId": "codex_mcp_operator",
        "reportType": "indicator_scout_report",
        "executionScope": "settings_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "localHandler": "indicator_schedule",
        "formFields": (
            {"id": "enabled", "labelTh": "ต้องการเปิดเมื่อ Scheduler พร้อม", "type": "boolean", "required": False},
            {"id": "times", "labelTh": "เวลาที่ต้องการ", "type": "time_list", "required": True},
        ),
    },
    "analyze_daily_market_news": {
        "propId": "left_signal_cube",
        "tabId": "today",
        "labelTh": "วิเคราะห์ข่าวตลาดวันนี้",
        "descriptionTh": "ค้นข่าวสาธารณะจริง พร้อมเวลาข่าว ระดับผลกระทบ คำเตือน และ URL อ้างอิง",
        "toolId": "codex_web_research",
        "ownerAgentId": "codex_mcp_operator",
        "reportType": "fx_news_bias_report",
        "executionScope": "public_web_read_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "formFields": (
            {"id": "marketDate", "labelTh": "วันที่ตลาด", "type": "text", "required": False},
            {"id": "minimumImpact", "labelTh": "ระดับผลกระทบขั้นต่ำ", "type": "select", "required": False, "options": ["low", "medium", "high"]},
            {"id": "brief", "labelTh": "ประเด็นที่ต้องการเน้น", "type": "textarea", "required": False},
        ),
    },
    "build_fx_pair_bias": {
        "propId": "left_signal_cube",
        "tabId": "pair_bias",
        "labelTh": "สร้าง Bias สำหรับ 28 คู่เงิน",
        "descriptionTh": "ใช้รายงานข่าวที่พร้อมแล้วสร้างมุมมองระยะสั้น กลาง และยาว โดยทุกแถวต้องมีแหล่งอ้างอิง",
        "toolId": "codex_web_research",
        "ownerAgentId": "codex_mcp_operator",
        "reportType": "fx_news_bias_report",
        "executionScope": "public_web_read_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "รายงานข่าวต้นทาง", "type": "source_report", "required": True},
            {"id": "brief", "labelTh": "เงื่อนไขเพิ่มเติม", "type": "textarea", "required": False},
        ),
    },
    "save_news_bias_schedule": {
        "propId": "left_signal_cube",
        "tabId": "schedule_history",
        "labelTh": "บันทึกเวลาอัปเดตข่าวและ Bias",
        "descriptionTh": "บันทึก Preference เท่านั้น ระบบยังไม่รันข่าวตามเวลาอัตโนมัติ",
        "toolId": None,
        "ownerAgentId": "codex_mcp_operator",
        "reportType": "fx_news_bias_report",
        "executionScope": "settings_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "localHandler": "news_bias_schedule",
        "formFields": (
            {"id": "enabled", "labelTh": "ต้องการเปิดเมื่อ Scheduler พร้อม", "type": "boolean", "required": False},
            {"id": "times", "labelTh": "เวลาที่ต้องการ", "type": "time_list", "required": True},
            {"id": "minimumImpact", "labelTh": "ระดับผลกระทบขั้นต่ำ", "type": "select", "required": False, "options": ["low", "medium", "high"]},
        ),
    },
    "inspect_ea_source": {
        "propId": "terminal_workstation",
        "tabId": "source",
        "labelTh": "ตรวจ Source EA ก่อนพัฒนา",
        "descriptionTh": "ตรวจ MQL4/MQL5 แบบ Static ใน Guarded Workspace โดยไม่ Compile หรือ Install",
        "toolId": "codex_cli_task",
        "ownerAgentId": "ea_developer",
        "reportType": "ea_development_report",
        "executionScope": "workspace_analysis_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "รายงาน Source ต้นทาง", "type": "source_report", "required": False},
            {"id": "workspaceSourceId", "labelTh": "Source ใน Workspace", "type": "workspace_source", "required": False},
            {"id": "platform", "labelTh": "ภาษา", "type": "select", "required": True, "options": ["mql4", "mql5"]},
            {"id": "brief", "labelTh": "จุดที่ต้องการตรวจ", "type": "textarea", "required": False},
        ),
    },
    "develop_ea_source": {
        "propId": "terminal_workstation",
        "tabId": "development_brief",
        "labelTh": "พัฒนา Source EA",
        "descriptionTh": "แก้หรือสร้าง MQL4/MQL5 ใน Project Workspace และส่งไฟล์แบบ project-relative",
        "toolId": "codex_cli_task",
        "ownerAgentId": "ea_developer",
        "reportType": "ea_development_report",
        "executionScope": "workspace_source_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "รายงาน Source ต้นทาง", "type": "source_report", "required": False},
            {"id": "workspaceSourceId", "labelTh": "Source ใน Workspace", "type": "workspace_source", "required": False},
            {"id": "platform", "labelTh": "ภาษา", "type": "select", "required": True, "options": ["mql4", "mql5"]},
            {"id": "outputName", "labelTh": "ชื่อผลงาน", "type": "text", "required": False},
            {"id": "brief", "labelTh": "โจทย์พัฒนา", "type": "textarea", "required": True},
        ),
    },
    "propose_ea_performance_improvements": {
        "propId": "terminal_workstation",
        "tabId": "performance_goals",
        "labelTh": "เสนอแนวทางปรับปรุงประสิทธิภาพ EA",
        "descriptionTh": "วางแผนปรับ Source จากเป้าหมาย โดยไม่อ้างว่า Backtest หรือ Compile แล้ว",
        "toolId": "codex_cli_task",
        "ownerAgentId": "ea_developer",
        "reportType": "ea_development_report",
        "executionScope": "workspace_analysis_only",
        "analysisOnly": True,
        "sourceRequired": True,
        "formFields": (
            {"id": "sourceReportId", "labelTh": "รายงาน Source ต้นทาง", "type": "source_report", "required": False},
            {"id": "workspaceSourceId", "labelTh": "Source ใน Workspace", "type": "workspace_source", "required": False},
            {"id": "platform", "labelTh": "ภาษา", "type": "select", "required": True, "options": ["mql4", "mql5"]},
            {"id": "targetProfitPercent", "labelTh": "กำไรเป้าหมาย (%)", "type": "number", "required": False},
            {"id": "maxDrawdownPercent", "labelTh": "Drawdown สูงสุด (%)", "type": "number", "required": False},
            {"id": "targetTrades", "labelTh": "จำนวน Order เป้าหมาย", "type": "integer", "required": False},
            {"id": "brief", "labelTh": "ข้อจำกัดเพิ่มเติม", "type": "textarea", "required": False},
        ),
    },
    "refresh_vps_hq_status": {
        "propId": "right_status_crystals",
        "tabId": "vps",
        "labelTh": "ตรวจสถานะ VPS และ HQ ใหม่",
        "descriptionTh": "อ่านสุขภาพ Local Runner และ Mission Worker จาก Backend โดยไม่เรียก Codex",
        "toolId": None,
        "ownerAgentId": "vps_watch",
        "reportType": "ops_overview_report",
        "executionScope": "local_read_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "localHandler": "vps_hq_health",
        "formFields": (),
    },
    "save_agent_preferences": {
        "propId": "right_status_crystals",
        "tabId": "agent_settings",
        "labelTh": "บันทึกการแสดงผล Agent",
        "descriptionTh": "เก็บเฉพาะ Filter และ Refresh Preference ที่ปลอดภัย",
        "toolId": None,
        "ownerAgentId": "manager",
        "reportType": "ops_overview_report",
        "executionScope": "settings_only",
        "analysisOnly": True,
        "sourceRequired": False,
        "localHandler": "agent_preferences",
        "formFields": (
            {"id": "language", "labelTh": "ภาษาหลัก", "type": "select", "required": False, "options": ["th", "en"]},
            {"id": "modelTier", "labelTh": "ระดับโมเดล", "type": "select", "required": False, "options": ["manager_quality", "risk_quality", "specialist_balanced", "specialist_fast"]},
            {"id": "tokenBudget", "labelTh": "งบ Token ต่อภารกิจ", "type": "integer", "required": False},
            {"id": "timeoutSeconds", "labelTh": "เวลาสูงสุดต่อภารกิจ (วินาที)", "type": "integer", "required": False},
            {"id": "outputLimitChars", "labelTh": "ขนาดผลลัพธ์สูงสุด (ตัวอักษร)", "type": "integer", "required": False},
            {"id": "rateReservePercent", "labelTh": "Rate Limit สำรอง (%)", "type": "integer", "required": False},
        ),
    },
}

DASHBOARD_WORKFLOW_COORDINATION_MODE = "agent_mission_only"
DASHBOARD_WORKFLOW_TRANSFER_MODE = "agent_mission_report"
DASHBOARD_WORKFLOW_SOURCE_READY_STATUSES = frozenset({"ready", "completed", "verified", "published"})
DASHBOARD_WORKFLOW_SOURCE_MISSION_READY_STATUSES = frozenset({"completed", "archived"})

DASHBOARD_WORKFLOW_SOURCE_POLICIES = {
    "deep_research_system": {
        "propIds": {"codex_mcp_portal"},
        "reportTypes": {"trading_system_discovery_report", "ea_discovery_report"},
    },
    "build_strategy_code": {
        "propIds": {"codex_mcp_portal", "left_server_racks"},
        "reportTypes": {"trading_system_discovery_report", "ea_discovery_report", "trading_system_research_report"},
    },
    "review_source_code": {
        "propIds": {"right_server_racks"},
        "reportTypes": {"ea_build_report", "ea_compile_report"},
    },
    "prepare_backtest_plan": {
        "propIds": {"right_server_racks"},
        "reportTypes": {"ea_build_report", "ea_compile_report"},
    },
    "prepare_optimization_plan": {
        "propIds": {"right_server_racks"},
        "reportTypes": {"ea_build_report", "ea_compile_report"},
    },
    "prepare_ea_discovery_plan": {
        "propIds": {"codex_mcp_portal", "left_server_racks", "right_server_racks"},
        "reportTypes": {
            "trading_system_discovery_report",
            "ea_discovery_report",
            "trading_system_research_report",
            "ea_build_report",
            "ea_compile_report",
        },
    },
    "build_fx_pair_bias": {
        "propIds": {"left_signal_cube"},
        "reportTypes": {"fx_news_bias_report"},
    },
    "inspect_ea_source": {
        "propIds": {"right_server_racks", "terminal_workstation"},
        "reportTypes": {"ea_build_report", "ea_compile_report", "ea_development_report", "code_change_report"},
        "platforms": {"mt4", "mt5", "mql4", "mql5"},
    },
    "develop_ea_source": {
        "propIds": {"right_server_racks", "terminal_workstation"},
        "reportTypes": {"ea_build_report", "ea_compile_report", "ea_development_report", "code_change_report"},
        "platforms": {"mt4", "mt5", "mql4", "mql5"},
    },
    "propose_ea_performance_improvements": {
        "propIds": {"right_server_racks", "terminal_workstation"},
        "reportTypes": {"ea_build_report", "ea_compile_report", "ea_development_report", "code_change_report"},
        "platforms": {"mt4", "mt5", "mql4", "mql5"},
    },
}

DASHBOARD_WORKFLOW_REPORT_TYPES = {
    "codex_mcp_portal": {"trading_system_discovery_report", "ea_discovery_report"},
    "left_server_racks": {"trading_system_research_report"},
    "right_server_racks": {"ea_build_report", "ea_compile_report"},
    "right_tool_console": {"ea_experiment_report", "ea_discovery_report", "backtest_report", "optimization_report"},
    "left_audit_crystals": {"indicator_scout_report"},
    "left_signal_cube": {"fx_news_bias_report"},
    "terminal_workstation": {"ea_development_report", "ea_build_report", "ea_compile_report", "code_change_report"},
    "right_status_crystals": {"ops_overview_report", "vps_report"},
}
DASHBOARD_WORKFLOW_CONTEXT_REQUIRED_PROP_IDS = frozenset({
    "left_audit_crystals",
    "left_signal_cube",
})

FX_BIAS_PAIRS = (
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY",
    "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD",
    "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
)

DASHBOARD_DISCOVERY_SHEET_COLUMNS = (
    "discovery_id",
    "record_type",
    "discovered_at",
    "last_verified_at",
    "system_name",
    "trader_or_author",
    "source_title",
    "source_url",
    "source_published_at",
    "source_country",
    "source_language",
    "market",
    "symbols",
    "timeframe",
    "entry_rules",
    "exit_rules",
    "recovery_or_averaging_rules",
    "stop_loss",
    "take_profit",
    "special_conditions",
    "suitable_for",
    "evidence_status",
    "deduplication_key",
    "research_status",
    "position_sizing",
    "indicators",
    "price_action_concepts",
    "expected_trade_frequency",
    "claimed_performance",
    "verification_status",
    "normalized_source_url",
    "duplicate_status",
    "duplicate_of_discovery_id",
    "risks_and_limitations",
    "application_notes",
    "research_priority",
    "linked_mission_id",
    "linked_report_id",
    "target_platform",
    "license_or_usage_terms",
    "tags",
    "notes",
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
    # Dashboard responses contain nested action metadata such as
    # workflowDashboard.actions[].formFields[].options[].  A depth limit of
    # six replaced those harmless select values with "[TRUNCATED]" at the
    # final HTTP projection and also clipped deeper report evidence.  Keep a
    # finite ceiling for hostile or accidental nesting, but allow the public
    # read model to survive the second sanitization performed by send_json().
    if depth > 12:
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
    analysis_context = mission.get("analysisContext")
    if isinstance(analysis_context, dict) and analysis_context:
        packet["analysisContext"] = sanitize_json_value(analysis_context)
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


def _bounded_atomic_replace(
    source: Path,
    destination: Path,
    *,
    max_attempts: int = 1,
    initial_delay_seconds: float = 0.0,
) -> None:
    """Atomically replace a file, retrying only transient Windows access denial."""
    attempts = max(1, min(8, int(max_attempts)))
    initial_delay = max(0.0, min(0.25, float(initial_delay_seconds)))
    for attempt in range(attempts):
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if attempt + 1 >= attempts:
                raise
            time.sleep(min(0.25, initial_delay * (2**attempt)))


def write_json(
    path: Path,
    payload,
    *,
    keep_backup: bool = False,
    replace_max_attempts: int = 1,
    replace_initial_delay_seconds: float = 0.0,
) -> None:
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
            _bounded_atomic_replace(
                backup_temporary,
                backup,
                max_attempts=replace_max_attempts,
                initial_delay_seconds=replace_initial_delay_seconds,
            )
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
            handle.flush()
            if keep_backup:
                os.fsync(handle.fileno())
        _bounded_atomic_replace(
            temporary,
            path,
            max_attempts=replace_max_attempts,
            initial_delay_seconds=replace_initial_delay_seconds,
        )
    finally:
        for leftover in (temporary, backup_temporary):
            try:
                leftover.unlink(missing_ok=True)
            except OSError:
                pass


def ui_session_dashboard_version(session) -> int:
    if not isinstance(session, dict):
        return 0
    modal = session.get("modal")
    if not isinstance(modal, dict):
        return 0
    try:
        return max(0, int(modal.get("signalDashboardVersion") or 0))
    except (TypeError, ValueError):
        return 0


def store_ui_session(session) -> dict:
    # Browser tabs can persist the same session at nearly the same time. Keep
    # the read/version-check/write transaction serialized so an older tab can
    # never overwrite a newer dashboard version. Windows security scanners can
    # briefly deny an atomic replace, so this low-risk UI store uses a small,
    # bounded backoff while the last-good file and backup remain untouched.
    with UI_SESSION_LOCK:
        existing = read_json(UI_SESSION_PATH, {"session": None, "updatedAt": None})
        existing_session = existing.get("session") if isinstance(existing, dict) else None
        existing_version = ui_session_dashboard_version(existing_session)
        incoming_version = ui_session_dashboard_version(session)
        if existing_version > incoming_version:
            return {
                "ok": True,
                "ignored": True,
                "reason": "older_dashboard_version",
                "updatedAt": existing.get("updatedAt") if isinstance(existing, dict) else None,
                "storedDashboardVersion": existing_version,
            }
        updated_at = utc_now()
        write_json(
            UI_SESSION_PATH,
            {"updatedAt": updated_at, "session": session},
            keep_backup=UI_SESSION_PATH.exists(),
            replace_max_attempts=UI_SESSION_REPLACE_MAX_ATTEMPTS,
            replace_initial_delay_seconds=UI_SESSION_REPLACE_INITIAL_DELAY_SECONDS,
        )
        return {
            "ok": True,
            "ignored": False,
            "updatedAt": updated_at,
            "storedDashboardVersion": incoming_version,
        }


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
    COLLABORATION_SCHEDULER_WAKE.set()
    AI_TRADE_COUNCIL_AUTOMATION_WAKE.set()
    return {"ok": True, "kind": "operator_mode", **operator_mode_read_model()}


THAILAND_TIMEZONE = timezone(timedelta(hours=7))
COLLABORATION_CONFIG_FIELDS = frozenset({
    "enabled",
    "topic",
    "startTime",
    "endTime",
    "intervalMinutes",
    "maxTurns",
    "maxDailyRuns",
    "minRemainingPercent",
})
COLLABORATION_DEFAULT_PARTICIPANTS = (
    "ea_developer",
    "backtest_analyst",
    "optimization_agent",
    "manager",
)


def _collaboration_default_store() -> dict:
    return {
        "version": "agent-collaboration-store-v1",
        "config": {
            "enabled": False,
            "topic": "ช่วยกันทบทวนและเสนอวิธีพัฒนา Product ของ Metafxclub ให้ใช้งานง่าย ปลอดภัย และวัดผลได้ดีขึ้น",
            "timezone": "Asia/Bangkok",
            "startTime": "09:00",
            "endTime": "18:00",
            "intervalMinutes": 120,
            "maxTurns": 3,
            "maxDailyRuns": 3,
            "minRemainingPercent": 30,
            "participants": list(COLLABORATION_DEFAULT_PARTICIPANTS),
            "maxParticipants": 4,
            "perTurnTimeoutSeconds": 90,
            "perTurnOutputChars": 1800,
            "targetPropId": MISSION_STRATEGY_TABLE_PROP_ID,
            "autoCreateFollowup": False,
        },
        "state": {
            "dailyRunDate": None,
            "dailyRunCount": 0,
            "lastRunAt": None,
            "lastCompletedAt": None,
            "lastStatus": "idle",
            "lastReason": None,
            "lastMeetingId": None,
            "lastMissionId": None,
        },
        "updatedAt": utc_now(),
    }


def _valid_collaboration_time(value: object) -> str | None:
    candidate = str(value or "").strip()
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", candidate):
        return None
    return candidate


def _collaboration_local_now() -> datetime:
    return datetime.now(THAILAND_TIMEZONE)


def _collaboration_day_key(now_local: datetime | None = None) -> str:
    return (now_local or _collaboration_local_now()).date().isoformat()


def _collaboration_store_shape(value: object) -> dict:
    defaults = _collaboration_default_store()
    if not isinstance(value, dict):
        raise DataIntegrityError("Agent collaboration store has an invalid shape.")
    raw_config = value.get("config")
    raw_state = value.get("state")
    if not isinstance(raw_config, dict) or not isinstance(raw_state, dict):
        raise DataIntegrityError("Agent collaboration store is missing config or state.")
    config = {**defaults["config"], **raw_config}
    state = {**defaults["state"], **raw_state}
    participants = [
        item
        for item in (safe_reference(entry) for entry in (config.get("participants") or []))
        if item in EXPECTED_AGENT_IDS
    ]
    if "manager" not in participants:
        participants.append("manager")
    config["participants"] = list(dict.fromkeys(participants))[:4] or list(COLLABORATION_DEFAULT_PARTICIPANTS)
    config["timezone"] = "Asia/Bangkok"
    config["targetPropId"] = MISSION_STRATEGY_TABLE_PROP_ID
    config["autoCreateFollowup"] = False
    config["maxParticipants"] = 4
    config["perTurnTimeoutSeconds"] = clamp_int(config.get("perTurnTimeoutSeconds"), 90, 30, 120)
    config["perTurnOutputChars"] = clamp_int(config.get("perTurnOutputChars"), 1800, 800, 3000)
    config["intervalMinutes"] = clamp_int(config.get("intervalMinutes"), 120, 30, 1440)
    config["maxTurns"] = clamp_int(config.get("maxTurns"), 3, 2, 4)
    config["maxDailyRuns"] = clamp_int(config.get("maxDailyRuns"), 3, 1, 6)
    config["minRemainingPercent"] = clamp_int(config.get("minRemainingPercent"), 30, 10, 80)
    config["enabled"] = bool(config.get("enabled", False))
    config["topic"] = redact_text(str(config.get("topic") or defaults["config"]["topic"]), 600)
    config["startTime"] = _valid_collaboration_time(config.get("startTime")) or "09:00"
    config["endTime"] = _valid_collaboration_time(config.get("endTime")) or "18:00"
    state["dailyRunCount"] = clamp_int(state.get("dailyRunCount"), 0, 0, 1000)
    for key in ("dailyRunDate", "lastRunAt", "lastCompletedAt", "lastStatus", "lastReason", "lastMeetingId", "lastMissionId"):
        if state.get(key) is not None:
            state[key] = redact_text(str(state.get(key)), 240)
    return {
        "version": "agent-collaboration-store-v1",
        "config": config,
        "state": state,
        "updatedAt": value.get("updatedAt") or defaults["updatedAt"],
    }


def load_collaboration_schedule_store() -> dict:
    with COLLABORATION_SCHEDULE_LOCK:
        if not COLLABORATION_SCHEDULE_PATH.exists():
            return _collaboration_default_store()
        return _collaboration_store_shape(read_json(COLLABORATION_SCHEDULE_PATH, {}))


def ensure_collaboration_schedule_store() -> dict:
    with COLLABORATION_SCHEDULE_LOCK:
        store = load_collaboration_schedule_store()
        if not COLLABORATION_SCHEDULE_PATH.exists():
            write_json(COLLABORATION_SCHEDULE_PATH, store)
        return store


def _save_collaboration_schedule_store(store: dict) -> dict:
    normalized = _collaboration_store_shape(store)
    normalized["updatedAt"] = utc_now()
    with COLLABORATION_SCHEDULE_LOCK:
        write_json(
            COLLABORATION_SCHEDULE_PATH,
            normalized,
            keep_backup=COLLABORATION_SCHEDULE_PATH.exists(),
        )
    return normalized


def _mutate_collaboration_schedule_store(mutator) -> dict:
    """Apply one in-process read/modify/write transaction to the schedule store."""
    with COLLABORATION_SCHEDULE_LOCK:
        if COLLABORATION_SCHEDULE_PATH.exists():
            store = _collaboration_store_shape(read_json(COLLABORATION_SCHEDULE_PATH, {}))
        else:
            store = _collaboration_default_store()
        updated = mutator(store)
        if updated is not None:
            store = updated
        normalized = _collaboration_store_shape(store)
        normalized["updatedAt"] = utc_now()
        write_json(
            COLLABORATION_SCHEDULE_PATH,
            normalized,
            keep_backup=COLLABORATION_SCHEDULE_PATH.exists(),
        )
        return normalized


def _update_collaboration_store_state(**values: object) -> dict:
    def apply_state(store: dict) -> dict:
        store["state"] = {**store["state"], **values}
        return store

    return _mutate_collaboration_schedule_store(apply_state)


def _rollover_collaboration_daily_state(store: dict, now_local: datetime | None = None) -> tuple[dict, bool]:
    current_day = _collaboration_day_key(now_local)
    state = store["state"]
    if state.get("dailyRunDate") == current_day:
        return store, False
    state["dailyRunDate"] = current_day
    state["dailyRunCount"] = 0
    return store, True


def _collaboration_inside_window(config: dict, now_local: datetime | None = None) -> bool:
    now_local = now_local or _collaboration_local_now()
    start_text = _valid_collaboration_time(config.get("startTime")) or "09:00"
    end_text = _valid_collaboration_time(config.get("endTime")) or "18:00"
    start_hour, start_minute = (int(part) for part in start_text.split(":"))
    end_hour, end_minute = (int(part) for part in end_text.split(":"))
    current = now_local.hour * 60 + now_local.minute
    start = start_hour * 60 + start_minute
    end = end_hour * 60 + end_minute
    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


def _collaboration_quota_gate(config: dict, *, refresh: bool) -> dict:
    quota = codex_rate_limits(force=True) if refresh else peek_codex_rate_limits()
    if quota.get("ok") is not True:
        return {
            "allowed": False,
            "reason": "quota_unavailable",
            "messageTh": "พักไว้ก่อน เพราะยังอ่าน Rate Limit ของ Codex ไม่ได้",
            "remainingPercent": None,
            "quota": quota,
        }
    if quota.get("stale") is True:
        return {
            "allowed": False,
            "reason": "quota_stale",
            "messageTh": "พักไว้ก่อน เพราะข้อมูล Rate Limit เก่าเกินไป",
            "remainingPercent": None,
            "quota": quota,
        }
    if quota.get("limitReached") is True:
        return {
            "allowed": False,
            "reason": "quota_limit_reached",
            "messageTh": "พักไว้ก่อน เพราะ Codex ถึง Rate Limit แล้ว",
            "remainingPercent": 0,
            "quota": quota,
        }
    remaining_values = []
    for key in ("primary", "secondary"):
        window = quota.get(key)
        if not isinstance(window, dict):
            continue
        try:
            remaining_values.append(float(window.get("remainingPercent")))
        except (TypeError, ValueError, OverflowError):
            continue
    if not remaining_values:
        return {
            "allowed": False,
            "reason": "quota_incomplete",
            "messageTh": "พักไว้ก่อน เพราะข้อมูล Rate Limit ยังไม่ครบ",
            "remainingPercent": None,
            "quota": quota,
        }
    remaining = min(remaining_values)
    threshold = clamp_int(config.get("minRemainingPercent"), 30, 10, 80)
    if remaining < threshold:
        return {
            "allowed": False,
            "reason": "quota_below_reserve",
            "messageTh": f"พักการประชุมเพื่อเก็บโควตาไว้ใช้งาน เหลือ {remaining:g}% ต่ำกว่าเกณฑ์ {threshold}%",
            "remainingPercent": remaining,
            "quota": quota,
        }
    return {
        "allowed": True,
        "reason": "ready",
        "messageTh": f"Rate Limit พร้อม เหลืออย่างน้อย {remaining:g}%",
        "remainingPercent": remaining,
        "quota": quota,
    }


def _collaboration_next_run_at(store: dict, now_local: datetime | None = None) -> str | None:
    config = store["config"]
    state = store["state"]
    if not config.get("enabled"):
        return None
    now_local = now_local or _collaboration_local_now()
    start_hour, start_minute = (int(part) for part in str(config.get("startTime") or "09:00").split(":"))
    candidate = now_local
    if not _collaboration_inside_window(config, now_local):
        start_today = now_local.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        if now_local < start_today:
            candidate = start_today
        else:
            candidate = start_today + timedelta(days=1)
    last_run = parse_iso(state.get("lastRunAt"))
    if last_run:
        interval_candidate = last_run.astimezone(THAILAND_TIMEZONE) + timedelta(
            minutes=clamp_int(config.get("intervalMinutes"), 120, 30, 1440)
        )
        if interval_candidate > candidate:
            candidate = interval_candidate
            if not _collaboration_inside_window(config, candidate):
                next_start = candidate.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                if candidate >= next_start:
                    next_start += timedelta(days=1)
                candidate = next_start
    return candidate.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _collaboration_gate(
    trigger: str,
    *,
    refresh_quota: bool,
    now_local: datetime | None = None,
) -> tuple[dict, dict]:
    now_local = now_local or _collaboration_local_now()
    with COLLABORATION_SCHEDULE_LOCK:
        store = load_collaboration_schedule_store()
        store, rolled = _rollover_collaboration_daily_state(store, now_local)
        if rolled and COLLABORATION_SCHEDULE_PATH.exists():
            store = _save_collaboration_schedule_store(store)
    config = store["config"]
    state = store["state"]
    with COLLABORATION_STATE_LOCK:
        runtime_state = dict(COLLABORATION_STATE)
    if runtime_state.get("status") in {"starting", "running"}:
        return store, {"allowed": False, "reason": "already_running", "messageTh": "Agent กำลังประชุมกันอยู่"}
    if load_operator_mode_record().get("mode") != "auto_guarded":
        return store, {"allowed": False, "reason": "full_access_required", "messageTh": "ต้องเปิด Full Access ก่อนจึงจะปล่อยให้ Agent ประชุมอัตโนมัติได้"}
    if contains_potential_secret(config.get("topic")):
        return store, {"allowed": False, "reason": "potential_secret", "messageTh": "หัวข้อประชุมมีข้อมูลที่อาจเป็นความลับ กรุณาแก้หัวข้อก่อน"}
    if trigger == "schedule" and not config.get("enabled"):
        return store, {"allowed": False, "reason": "disabled", "messageTh": "ปิดการประชุมอัตโนมัติอยู่"}
    if trigger == "schedule" and not _collaboration_inside_window(config, now_local):
        return store, {"allowed": False, "reason": "outside_time_window", "messageTh": "ยังไม่ถึงช่วงเวลาที่อนุญาตให้ Agent ประชุม"}
    if state.get("dailyRunCount", 0) >= config.get("maxDailyRuns", 3):
        return store, {"allowed": False, "reason": "daily_cap_reached", "messageTh": "ครบจำนวนการประชุมสูงสุดของวันนี้แล้ว"}
    last_run = parse_iso(state.get("lastRunAt"))
    if last_run:
        elapsed_seconds = max(0.0, (datetime.now(timezone.utc) - last_run.astimezone(timezone.utc)).total_seconds())
        minimum_gap = config.get("intervalMinutes", 120) * 60 if trigger == "schedule" else 5 * 60
        if elapsed_seconds < minimum_gap:
            return store, {
                "allowed": False,
                "reason": "cooldown",
                "messageTh": "ยังอยู่ในช่วงพักเพื่อลดการใช้ Rate Limit",
                "retryAfterSeconds": int(minimum_gap - elapsed_seconds),
            }
    quota_gate = _collaboration_quota_gate(config, refresh=refresh_quota)
    if not quota_gate.get("allowed"):
        return store, quota_gate
    if not CODEX_RUNNER_PYTHON.is_file() or not CODEX_RUNNER_SCRIPT.is_file():
        return store, {"allowed": False, "reason": "runner_unavailable", "messageTh": "Codex Runner ยังไม่พร้อมสำหรับการประชุม"}
    return store, quota_gate


def collaboration_schedule_read_model() -> dict:
    store = load_collaboration_schedule_store()
    now_local = _collaboration_local_now()
    store, _ = _rollover_collaboration_daily_state(store, now_local)
    config = store["config"]
    state = store["state"]
    _, gate = _collaboration_gate("schedule", refresh_quota=False, now_local=now_local)
    with COLLABORATION_STATE_LOCK:
        runtime_state = dict(COLLABORATION_STATE)
    runtime_status = str(runtime_state.get("status") or "")
    status = runtime_status if runtime_status in {"starting", "running"} else (
        "scheduled" if config.get("enabled") and gate.get("allowed") else (
            "paused" if config.get("enabled") else "disabled"
        )
    )
    return {
        "ok": True,
        "version": "agent-collaboration-read-model-v1",
        "status": status,
        "enabled": bool(config.get("enabled")),
        "topic": redact_text(str(config.get("topic") or ""), 600),
        "timezone": "Asia/Bangkok",
        "startTime": config.get("startTime"),
        "endTime": config.get("endTime"),
        "intervalMinutes": config.get("intervalMinutes"),
        "maxTurns": config.get("maxTurns"),
        "maxDailyRuns": config.get("maxDailyRuns"),
        "dailyRunCount": state.get("dailyRunCount", 0),
        "minRemainingPercent": config.get("minRemainingPercent"),
        "participants": [
            item for item in config.get("participants", [])
            if item in EXPECTED_AGENT_IDS
        ],
        "targetPropId": MISSION_STRATEGY_TABLE_PROP_ID,
        "nextRunAt": _collaboration_next_run_at(store, now_local),
        "pausedReason": None if gate.get("allowed") else gate.get("reason"),
        "messageTh": "พร้อมเริ่มประชุมตามเวลา" if gate.get("allowed") else gate.get("messageTh"),
        "remainingPercent": gate.get("remainingPercent"),
        "lastRunAt": state.get("lastRunAt"),
        "lastCompletedAt": state.get("lastCompletedAt"),
        "lastStatus": state.get("lastStatus"),
        "lastMeetingId": safe_reference(state.get("lastMeetingId")),
        "lastMissionId": safe_reference(state.get("lastMissionId")),
        "activeMeetingId": safe_reference(runtime_state.get("activeMeetingId")),
        "activeMissionId": safe_reference(runtime_state.get("activeMissionId")),
        "updatedAt": store.get("updatedAt"),
        "guardrails": {
            "toolsEnabledDuringMeeting": False,
            "autoCreateFollowup": False,
            "freshRateLimitRequired": True,
            "fullAccessRequired": True,
            "externalActionsAllowed": False,
        },
    }


def set_collaboration_schedule(payload: dict) -> dict:
    if not isinstance(payload, dict) or not payload or not set(payload).issubset(COLLABORATION_CONFIG_FIELDS):
        return {
            "ok": False,
            "kind": "invalid_collaboration_schedule_request",
            "messageTh": "รับเฉพาะการเปิดใช้งาน หัวข้อ ช่วงเวลา ความถี่ จำนวนรอบ และโควตาสำรอง",
            "_httpStatus": 422,
        }
    integer_rules = {
        "intervalMinutes": (30, 1440),
        "maxTurns": (2, 4),
        "maxDailyRuns": (1, 6),
        "minRemainingPercent": (10, 80),
    }
    validated: dict[str, object] = {}
    if "enabled" in payload:
        if not isinstance(payload.get("enabled"), bool):
            return {"ok": False, "kind": "invalid_enabled", "messageTh": "สถานะเปิดใช้งานต้องเป็น true หรือ false", "_httpStatus": 422}
        validated["enabled"] = payload["enabled"]
    if "topic" in payload:
        if not isinstance(payload.get("topic"), str):
            return {"ok": False, "kind": "invalid_topic", "messageTh": "หัวข้อประชุมต้องเป็นข้อความ", "_httpStatus": 422}
        topic = payload["topic"].strip()
        if not 10 <= len(topic) <= 600 or contains_potential_secret(topic):
            return {"ok": False, "kind": "invalid_topic", "messageTh": "หัวข้อต้องยาว 10-600 ตัวอักษรและไม่มีข้อมูลลับ", "_httpStatus": 422}
        validated["topic"] = topic
    for field in ("startTime", "endTime"):
        if field not in payload:
            continue
        value = _valid_collaboration_time(payload.get(field))
        if not value:
            return {"ok": False, "kind": "invalid_time", "messageTh": "เวลาใช้รูปแบบ HH:MM เท่านั้น", "_httpStatus": 422}
        validated[field] = value
    for field, (minimum, maximum) in integer_rules.items():
        if field not in payload:
            continue
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            return {
                "ok": False,
                "kind": f"invalid_{field}",
                "messageTh": f"ค่า {field} ต้องเป็นจำนวนเต็มระหว่าง {minimum}-{maximum}",
                "_httpStatus": 422,
            }
        validated[field] = value

    def apply_config(store: dict) -> dict:
        store["config"] = {**store["config"], **validated}
        return store

    store = _mutate_collaboration_schedule_store(apply_config)
    config = store["config"]
    append_audit({
        "type": "collaboration.schedule_changed",
        "enabled": config.get("enabled"),
        "topicDigest": payload_digest(str(config.get("topic") or ""))[:16],
        "startTime": config.get("startTime"),
        "endTime": config.get("endTime"),
        "intervalMinutes": config.get("intervalMinutes"),
        "maxTurns": config.get("maxTurns"),
        "maxDailyRuns": config.get("maxDailyRuns"),
        "minRemainingPercent": config.get("minRemainingPercent"),
    })
    COLLABORATION_SCHEDULER_WAKE.set()
    return {"ok": True, "kind": "collaboration_schedule", "collaboration": collaboration_schedule_read_model()}


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
    analysis_context = (
        mission.get("analysisContext")
        if isinstance(mission.get("analysisContext"), dict)
        else {}
    )
    council_context_valid = (
        analysis_context.get("kind") == "ai_trade_council_vote"
        and analysis_context.get("agentId") == agent_id
        and analysis_context.get("roleId") == AI_TRADE_COUNCIL_AGENT_ROLES.get(agent_id)
        and tool_id == AI_TRADE_COUNCIL_ALLOWED_TOOLS.get(agent_id)
        and re.fullmatch(r"[0-9a-f]{64}", str(analysis_context.get("snapshotId") or "")) is not None
        and analysis_context.get("snapshotArtifact")
        == ai_trade_council_snapshot_reference(
            str(analysis_context.get("snapshotId") or ""),
            str(analysis_context.get("snapshotArtifactDigest") or ""),
        )
        and analysis_context.get("readOnly") is True
    )
    reasons.extend(
        _ai_trade_council_high_impact_reasons(tool_id, detail)
        if council_context_valid
        else _high_impact_reasons(tool_id, detail, risk)
    )
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


def tool_execution_capability_unavailable(policy: object) -> bool:
    if not isinstance(policy, dict):
        return True
    adapter_status = str(policy.get("adapterStatus") or "").strip().lower()
    unavailable_markers = ("missing", "unimplemented", "not_implemented", "disabled", "coming_soon")
    return (
        policy.get("realExecutionAvailable") is not True
        and any(marker in adapter_status for marker in unavailable_markers)
    )


def mark_mission_capability_unavailable(mission: dict, tool_policy: dict) -> dict:
    tool_id = str(mission.get("toolId") or "unknown_tool")
    adapter_status = str(tool_policy.get("adapterStatus") or "adapter_missing")
    completed_at = utc_now()
    mission["status"] = "blocked"
    mission["phase"] = "capability_unavailable"
    mission["workStatus"] = "blocked"
    mission["errorCode"] = "capability_unavailable"
    mission["result"] = (
        f"{tool_id} ยังไม่มี Adapter สำหรับงานจริง ({adapter_status}) "
        "การอนุมัติหรือ Full Access ไม่สามารถปลดล็อกความสามารถนี้ได้"
    )
    mission["updatedAt"] = completed_at
    mission["completedAt"] = completed_at
    replace_mission(mission)
    append_audit({
        "type": "adapter.capability_unavailable",
        "missionId": mission.get("id"),
        "ownerAgentId": mission.get("owner"),
        "toolId": tool_id,
        "adapterStatus": adapter_status,
        "approvalRequested": False,
        "realToolExecuted": False,
    })
    return mission


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


def _persisted_rate_limit_path() -> Path:
    """Keep cost-guard evidence beside the mission store used by this Bridge."""
    return MISSIONS_PATH.parent / "local-rate-limit-state.json"


def _load_persisted_rate_limits_unlocked() -> dict[str, list[float]]:
    path = _persisted_rate_limit_path()
    data = read_json(
        path,
        {"schemaVersion": PERSISTED_RATE_LIMIT_SCHEMA, "buckets": {}},
    )
    if (
        not isinstance(data, dict)
        or data.get("schemaVersion") != PERSISTED_RATE_LIMIT_SCHEMA
        or not isinstance(data.get("buckets"), dict)
    ):
        raise DataIntegrityError("Local rate-limit state has an invalid schema.")
    buckets: dict[str, list[float]] = {}
    for raw_key, raw_rows in data["buckets"].items():
        if (
            not isinstance(raw_key, str)
            or not raw_key.startswith(PERSISTED_RATE_LIMIT_PREFIXES)
            or len(raw_key) > 240
            or not isinstance(raw_rows, list)
        ):
            raise DataIntegrityError("Local rate-limit state contains an invalid bucket.")
        rows: list[float] = []
        for raw_stamp in raw_rows:
            if (
                isinstance(raw_stamp, bool)
                or not isinstance(raw_stamp, (int, float))
                or not math.isfinite(float(raw_stamp))
                or float(raw_stamp) <= 0
            ):
                raise DataIntegrityError("Local rate-limit state contains an invalid timestamp.")
            rows.append(float(raw_stamp))
        buckets[raw_key] = rows
    return buckets


def _save_persisted_rate_limits_unlocked(buckets: dict[str, list[float]]) -> None:
    write_json(
        _persisted_rate_limit_path(),
        {
            "schemaVersion": PERSISTED_RATE_LIMIT_SCHEMA,
            "updatedAt": utc_now(),
            "buckets": {
                key: list(rows)
                for key, rows in sorted(buckets.items())
                if key.startswith(PERSISTED_RATE_LIMIT_PREFIXES) and rows
            },
        },
        keep_backup=True,
    )


def check_rate_limit(key: str, max_per_hour: int, cooldown_seconds: int = 0, consume: bool = True) -> tuple[bool, int]:
    now = time.time()
    with RATE_LIMIT_LOCK:
        persisted = key.startswith(PERSISTED_RATE_LIMIT_PREFIXES)
        persisted_buckets = _load_persisted_rate_limits_unlocked() if persisted else {}
        combined_rows = [
            *persisted_buckets.get(key, []),
            *RATE_LIMIT_STATE.get(key, []),
        ]
        # The in-memory row is also present in the durable store after a consume.
        # De-duplicate exact timestamps so one run is never counted twice.
        rows = sorted({
            float(stamp)
            for stamp in combined_rows
            if now - float(stamp) < 3600
        })
        if rows and cooldown_seconds > 0 and now - rows[-1] < cooldown_seconds:
            retry_after = max(1, int(cooldown_seconds - (now - rows[-1]) + 0.999))
            RATE_LIMIT_STATE[key] = rows
            if persisted:
                persisted_buckets[key] = rows
                _save_persisted_rate_limits_unlocked(persisted_buckets)
            return False, retry_after
        if len(rows) >= max(1, max_per_hour):
            retry_after = max(1, int(3600 - (now - rows[0]) + 0.999))
            RATE_LIMIT_STATE[key] = rows
            if persisted:
                persisted_buckets[key] = rows
                _save_persisted_rate_limits_unlocked(persisted_buckets)
            return False, retry_after
        if consume:
            rows.append(now)
            RATE_LIMIT_STATE[key] = rows
        elif rows:
            RATE_LIMIT_STATE[key] = rows
        else:
            RATE_LIMIT_STATE.pop(key, None)
        if persisted:
            if rows:
                persisted_buckets[key] = rows
            else:
                persisted_buckets.pop(key, None)
            _save_persisted_rate_limits_unlocked(persisted_buckets)
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


def memory_read_model_item(item: object) -> dict:
    """Project a memory card without returning a local filesystem path."""
    source = item if isinstance(item, dict) else {}
    raw_source_path = str(source.get("sourcePath") or "").strip()
    agents = source.get("agents") if isinstance(source.get("agents"), list) else []
    tags = source.get("tags") if isinstance(source.get("tags"), list) else []
    return {
        "id": safe_reference(source.get("id")),
        "kind": redact_text(str(source.get("kind") or "note"), 80),
        "title": redact_text(str(source.get("title") or "Memory"), 160),
        "summary": redact_text(str(source.get("summary") or ""), 2400),
        "agents": [
            value
            for value in (safe_reference(entry) for entry in agents[:20])
            if value
        ],
        "tags": [redact_text(str(entry), 80) for entry in tags[:30]],
        "hasLocalSource": bool(raw_source_path),
        "createdAt": source.get("createdAt"),
        "updatedAt": source.get("updatedAt"),
        "safety": {
            "containsSecret": False,
            "secretRedacted": bool((source.get("safety") or {}).get("secretRedacted", False))
            if isinstance(source.get("safety"), dict)
            else False,
            "localPathExposed": False,
        },
    }


def memory_index_read_model(index: object | None = None) -> dict:
    source = index if isinstance(index, dict) else load_memory_index()
    rows = source.get("items") if isinstance(source.get("items"), list) else []
    return {
        "version": redact_text(str(source.get("version") or "memory-index-v001"), 80),
        "items": [memory_read_model_item(item) for item in rows if isinstance(item, dict)],
        "updatedAt": source.get("updatedAt"),
        "readModel": "memory_index_frontend_v1",
    }


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
    records = tail_jsonl(MEETING_TRANSCRIPTS_PATH, limit=max(limit * 3, limit), max_bytes=524288)[::-1]
    durable = [
        item for item in records
        if item.get("simulation") is not True
        and not str(item.get("source") or "").startswith("frontend.")
    ]
    return durable[:limit]


def append_meeting_record(payload: dict, kind: str = "meeting") -> dict:
    ensure_memory_dir()
    participants = payload.get("participants") if isinstance(payload.get("participants"), list) else []
    messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    decisions = payload.get("decisions") if isinstance(payload.get("decisions"), list) else []
    next_actions = payload.get("nextActions") if isinstance(payload.get("nextActions"), list) else []
    record = {
        "id": str(payload.get("id") or f"meeting-{int(time.time() * 1000)}"),
        "kind": kind,
        "time": utc_now(),
        "title": redact_text(str(payload.get("title") or payload.get("agenda") or "Agent Meeting"), 160),
        "agenda": redact_text(str(payload.get("agenda") or ""), 1200),
        "participants": [item for item in (safe_reference(value) for value in participants[:20]) if item],
        "summary": redact_text(str(payload.get("summary") or payload.get("message") or ""), 2400),
        "messages": sanitize_json_value(messages[:80]),
        "decisions": sanitize_json_value(decisions[:20]),
        "nextActions": sanitize_json_value(next_actions[:20]),
        "source": redact_text(str(payload.get("source") or "frontend"), 160),
        "simulation": bool(payload.get("simulation", False)),
        "status": redact_text(str(payload.get("status") or "completed"), 40),
        "trigger": redact_text(str(payload.get("trigger") or "manual"), 40),
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


def _verified_metatrader_execution_record(
    source: dict,
    report_type: object,
    linked_mission_id: object,
) -> dict | None:
    """Resolve an MT execution claim only from backend-owned Mission and audit proof."""
    verification_id = safe_reference(source.get("backendVerificationId"))
    mission_id = safe_reference(linked_mission_id)
    tool_id = safe_reference(source.get("toolId"))
    platform = str(source.get("platform") or "").strip().lower()
    terminal_candidate_id = safe_reference(source.get("terminalCandidateId"))
    if (
        not verification_id
        or not mission_id
        or tool_id != "discovery_lab_mt4"
        or platform not in {"mt4", "mt5"}
        or not terminal_candidate_id
    ):
        return None
    try:
        mission = find_mission(mission_id)
    except (DataIntegrityError, OSError):
        return None
    if (
        not isinstance(mission, dict)
        or mission.get("status") != "completed"
        or safe_reference(mission.get("toolId")) != tool_id
    ):
        return None
    report_type_name = str(report_type or "")
    requires_visual_backtest = report_type_name in {
        "backtest_report",
        "backtest_optimization_report",
        "optimization_report",
    }
    requires_optimization = report_type_name in {
        "backtest_optimization_report",
        "optimization_report",
    }
    sha256_pattern = re.compile(r"^[a-f0-9]{64}$")
    try:
        records = tail_jsonl(AUDIT_PATH, limit=400, max_bytes=2 * 1024 * 1024)
    except OSError:
        return None
    for event in reversed(records):
        if (
            event.get("type") != "metatrader.execution_verified"
            or safe_reference(event.get("verificationId")) != verification_id
            or safe_reference(event.get("missionId")) != mission_id
            or safe_reference(event.get("toolId")) != tool_id
            or str(event.get("platform") or "").strip().lower() != platform
            or safe_reference(event.get("terminalCandidateId")) != terminal_candidate_id
            or event.get("status") != "completed"
            or event.get("visibleApplicationProof") is not True
            or event.get("liveTrading") is not False
        ):
            continue
        compile_digest = str(event.get("compileArtifactSha256") or "").strip().lower()
        backtest_digest = str(event.get("visualBacktestImageSha256") or "").strip().lower()
        optimization_digest = str(event.get("optimizationArtifactSha256") or "").strip().lower()
        if not sha256_pattern.fullmatch(compile_digest):
            continue
        if requires_visual_backtest and not sha256_pattern.fullmatch(backtest_digest):
            continue
        if requires_optimization and not sha256_pattern.fullmatch(optimization_digest):
            continue
        return event
    return None


def report_execution_evidence_read_model(
    value: object,
    report_type: object = None,
    linked_mission_id: object = None,
) -> dict:
    source = value if isinstance(value, dict) else {}
    claimed_source_kind = str(source.get("sourceKind") or "analysis_only").strip().lower()
    if claimed_source_kind not in {"analysis_only", "existing_report", "mt4_visible_run", "mt5_visible_run"}:
        claimed_source_kind = "analysis_only"
    verified_record = _verified_metatrader_execution_record(source, report_type, linked_mission_id)
    mt_execution_verified = verified_record is not None
    source_kind = (
        f"{str(source.get('platform')).strip().lower()}_visible_run"
        if mt_execution_verified
        else ("existing_report" if claimed_source_kind == "existing_report" else "analysis_only")
    )
    platform = str(source.get("platform") or "").strip().lower() if mt_execution_verified else None
    terminal_candidate_id = safe_reference(source.get("terminalCandidateId")) if mt_execution_verified else None
    compile_verified = mt_execution_verified
    report_type_name = str(report_type or "")
    requires_backtest = report_type_name in {
        "backtest_report",
        "backtest_optimization_report",
        "optimization_report",
    }
    requires_optimization = report_type_name in {
        "backtest_optimization_report",
        "optimization_report",
    }
    visual_backtest_verified = bool(mt_execution_verified and requires_backtest)
    optimization_verified = bool(mt_execution_verified and requires_optimization)
    return {
        "sourceKind": source_kind,
        "toolId": safe_reference(source.get("toolId")) if mt_execution_verified else None,
        "platform": platform,
        "terminalCandidateId": terminal_candidate_id,
        "backendVerificationId": safe_reference(source.get("backendVerificationId")) if mt_execution_verified else None,
        "compileProofVerified": compile_verified,
        "visualBacktestProofVerified": visual_backtest_verified,
        "optimizationProofVerified": optimization_verified,
        "mtExecutionVerified": mt_execution_verified,
        "scopeLabelTh": (
            "ยืนยันผลจาก MT4/MT5 แบบมองเห็นโปรแกรม"
            if mt_execution_verified
            else "วิเคราะห์โค้ดหรือรายงานที่มีอยู่ ยังไม่ได้ยืนยันการรัน MT4/MT5 จริง"
        ),
    }


def _agent_transfer_storage(value: object) -> dict | None:
    """Validate and project a backend-owned cross-dashboard transfer record."""
    if not isinstance(value, dict):
        return None
    if str(value.get("mode") or "") != DASHBOARD_WORKFLOW_TRANSFER_MODE:
        return None
    source_report_id = safe_reference(value.get("sourceReportId"))
    source_prop_id = safe_reference(value.get("sourcePropId"))
    source_mission_id = safe_reference(value.get("sourceMissionId"))
    transfer_agent_id = safe_reference(value.get("transferAgentId"))
    source_owner_agent_id = safe_reference(value.get("sourceOwnerAgentId"))
    target_prop_id = safe_reference(value.get("targetPropId"))
    handoff_mission_id = safe_reference(value.get("handoffMissionId"))
    if (
        not source_report_id
        or source_prop_id not in DASHBOARD_WORKFLOW_PROP_IDS
        or not source_mission_id
        or transfer_agent_id not in EXPECTED_AGENT_IDS
        or source_owner_agent_id not in EXPECTED_AGENT_IDS
        or target_prop_id not in DASHBOARD_WORKFLOW_PROP_IDS
        or not handoff_mission_id
    ):
        return None
    return {
        "mode": DASHBOARD_WORKFLOW_TRANSFER_MODE,
        "sourceReportId": source_report_id,
        "sourcePropId": source_prop_id,
        "sourceMissionId": source_mission_id,
        "transferAgentId": transfer_agent_id,
        "sourceOwnerAgentId": source_owner_agent_id,
        "targetPropId": target_prop_id,
        "handoffMissionId": handoff_mission_id,
        "status": "recorded",
    }


def _workflow_context_storage(value: object) -> dict | None:
    if not isinstance(value, dict) or value.get("schemaVersion") != "dashboard-workflow-lineage-v1":
        return None
    prop_id = safe_reference(value.get("propId"))
    action_id = safe_reference(value.get("actionId"))
    input_digest = str(value.get("inputDigest") or "")
    if (
        prop_id not in DASHBOARD_WORKFLOW_PROP_IDS
        or action_id not in DASHBOARD_WORKFLOW_ACTIONS
        or not re.fullmatch(r"[0-9a-f]{64}", input_digest)
    ):
        return None
    source = value.get("source") if isinstance(value.get("source"), dict) else None
    agent_transfer = _agent_transfer_storage(value.get("agentTransfer"))
    safe_source = None
    if source:
        safe_source = {
            "reportId": safe_reference(source.get("reportId")),
            "artifactId": safe_reference(source.get("artifactId")),
            "kind": redact_text(str(source.get("kind") or "report"), 40),
            "propId": safe_reference(source.get("propId")),
            "missionId": safe_reference(source.get("missionId")),
            "transferAgentId": safe_reference(source.get("transferAgentId")),
            "type": redact_text(str(source.get("type") or ""), 120),
            "status": redact_text(str(source.get("status") or ""), 40),
        }
        if safe_source["kind"] == "report":
            if not agent_transfer:
                return None
            if (
                safe_source["reportId"] != agent_transfer["sourceReportId"]
                or safe_source["propId"] != agent_transfer["sourcePropId"]
                or safe_source["missionId"] != agent_transfer["sourceMissionId"]
                or safe_source["transferAgentId"] != agent_transfer["transferAgentId"]
                or prop_id != agent_transfer["targetPropId"]
            ):
                return None
    inputs = value.get("inputs") if isinstance(value.get("inputs"), dict) else {}
    return {
        "schemaVersion": "dashboard-workflow-lineage-v1",
        "propId": prop_id,
        "actionId": action_id,
        "coordinationMode": DASHBOARD_WORKFLOW_COORDINATION_MODE,
        "source": safe_source,
        "agentTransfer": agent_transfer,
        "inputs": sanitize_json_value(inputs),
        "inputDigest": input_digest,
        "submittedAt": value.get("submittedAt"),
    }


def workflow_context_read_model(value: object) -> dict | None:
    context = _workflow_context_storage(value)
    if not context:
        return None
    return {
        "schemaVersion": context["schemaVersion"],
        "propId": context["propId"],
        "actionId": context["actionId"],
        "coordinationMode": context["coordinationMode"],
        "source": context["source"],
        "agentTransfer": context["agentTransfer"],
        "inputDigest": context["inputDigest"],
        "inputFields": sorted(str(key) for key in (context.get("inputs") or {}))[:40],
        "submittedAt": context.get("submittedAt"),
    }


def create_report(payload: dict) -> dict:
    ensure_runtime_dir()
    secret_redacted = json_contains_potential_secret(payload)
    report_id = safe_id(payload.get("id"), "report")
    report_path = RUNTIME_REPORTS_DIR / f"{report_id}.json"
    existing = read_json(report_path, {}) if report_path.exists() else {}
    now = utc_now()
    safe_workflow_context = _workflow_context_storage(payload.get("workflowContext"))
    safe_agent_transfer = _agent_transfer_storage(
        payload.get("agentTransfer")
        or ((safe_workflow_context or {}).get("agentTransfer"))
    )
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
        "evidence": evidence_read_model(payload.get("evidence")),
        "executionEvidence": report_execution_evidence_read_model(
            payload.get("executionEvidence"),
            payload.get("type"),
            payload.get("linkedMissionId"),
        ),
        "artifacts": sanitize_json_value(payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []),
        "workflowContext": safe_workflow_context,
        "agentTransfer": safe_agent_transfer,
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


def evidence_read_model(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:20]:
        if not isinstance(item, dict):
            continue
        label = redact_text(str(item.get("label") or "").strip(), 300)
        raw_url = str(item.get("url") or "").strip()
        note = redact_text(str(item.get("note") or "").strip(), 800)
        if not label or not raw_url or len(raw_url) > 2000 or contains_potential_secret(raw_url):
            continue
        try:
            parsed = urlparse(raw_url)
        except ValueError:
            continue
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.netloc
            or parsed.username
            or parsed.password
        ):
            continue
        result.append({
            "label": label,
            "url": redact_text(raw_url, 2000),
            "note": note,
        })
    return result


def report_attachment_roots() -> tuple[Path, ...]:
    return (
        MEMORY_DIR / "screenshots",
        MEMORY_DIR / "artifacts",
        RUNTIME_DIR / "codex-runs",
    )


def report_download_roots() -> tuple[Path, ...]:
    return (
        PROJECT_ROOT / "workspace",
        PROJECT_ROOT / "artifacts",
        PROJECT_ROOT / "outputs",
        MEMORY_DIR / "artifacts",
        RUNTIME_DIR / "codex-runs",
    )


def report_artifact_storage_value(value: object) -> tuple[str, str]:
    if isinstance(value, dict):
        raw_path = value.get("storageRef") or value.get("path") or value.get("file")
        label = value.get("label") or value.get("caption") or ""
        return str(raw_path or "").strip(), redact_text(str(label or "").strip(), 300)
    return str(value or "").strip(), ""


def report_image_magic_matches(path: Path, media_type: str) -> bool:
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
    except OSError:
        return False
    if media_type == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if media_type == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")
    if media_type == "image/webp":
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    return False


def resolve_report_image_artifact(value: object) -> tuple[Path, str, str] | None:
    raw_path, label = report_artifact_storage_value(value)
    if not raw_path or "\x00" in raw_path or contains_potential_secret(raw_path):
        return None
    normalized = raw_path.replace("\\", "/")
    raw_candidate = Path(normalized)
    if ".." in raw_candidate.parts:
        return None
    candidate = raw_candidate if raw_candidate.is_absolute() else PROJECT_ROOT / raw_candidate
    if candidate.is_symlink():
        return None
    resolved = candidate.resolve(strict=False)
    allowed = False
    for root in report_attachment_roots():
        try:
            resolved.relative_to(root.resolve(strict=False))
            allowed = True
            break
        except ValueError:
            continue
    if not allowed or not resolved.is_file():
        return None
    media_type = REPORT_IMAGE_MEDIA_TYPES.get(resolved.suffix.lower())
    if not media_type:
        return None
    try:
        byte_size = resolved.stat().st_size
    except OSError:
        return None
    if byte_size <= 0 or byte_size > MAX_REPORT_IMAGE_BYTES:
        return None
    if not report_image_magic_matches(resolved, media_type):
        return None
    return resolved, media_type, label


def _download_path_is_within_approved_root(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    for root in report_download_roots():
        try:
            resolved.relative_to(root.resolve(strict=False))
            return True
        except ValueError:
            continue
    return False


def _report_download_content_is_safe(path: Path) -> bool:
    suffix = path.suffix.lower()
    try:
        if suffix in REPORT_DOWNLOAD_TEXT_EXTENSIONS:
            content = path.read_bytes()
            if len(content) > MAX_REPORT_DOWNLOAD_BYTES:
                return False
            return not contains_potential_secret(content.decode("utf-8", errors="replace"))
        if suffix != ".zip":
            return False
        total_uncompressed = 0
        with zipfile.ZipFile(path, "r") as archive:
            members = archive.infolist()
            if not members or len(members) > 100:
                return False
            for member in members:
                member_path = Path(member.filename.replace("\\", "/"))
                if (
                    member.is_dir()
                    or member.flag_bits & 0x1
                    or member_path.is_absolute()
                    or ".." in member_path.parts
                    or (member.external_attr >> 16) & 0o170000 == 0o120000
                    or member_path.suffix.lower() not in REPORT_DOWNLOAD_TEXT_EXTENSIONS
                ):
                    return False
                total_uncompressed += int(member.file_size)
                if total_uncompressed > MAX_REPORT_DOWNLOAD_BYTES:
                    return False
                content = archive.read(member)
                if contains_potential_secret(content.decode("utf-8", errors="replace")):
                    return False
        return True
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError):
        return False


def resolve_report_download_artifact(value: object) -> tuple[Path, str, str] | None:
    raw_path, label = report_artifact_storage_value(value)
    if not raw_path or "\x00" in raw_path or contains_potential_secret(raw_path):
        return None
    normalized = raw_path.replace("\\", "/")
    raw_candidate = Path(normalized)
    if ".." in raw_candidate.parts:
        return None
    candidate = raw_candidate if raw_candidate.is_absolute() else PROJECT_ROOT / raw_candidate
    if candidate.is_symlink():
        return None
    resolved = candidate.resolve(strict=False)
    if not _download_path_is_within_approved_root(resolved) or not resolved.is_file():
        return None
    media_type = REPORT_DOWNLOAD_MEDIA_TYPES.get(resolved.suffix.lower())
    if not media_type:
        return None
    try:
        byte_size = resolved.stat().st_size
    except OSError:
        return None
    if byte_size <= 0 or byte_size > MAX_REPORT_DOWNLOAD_BYTES:
        return None
    if not _report_download_content_is_safe(resolved):
        return None
    return resolved, media_type, label


def report_download_id(report_id: str, index: int, path: Path, byte_size: int | None = None) -> str:
    stat = path.stat()
    size = stat.st_size if byte_size is None else byte_size
    digest = payload_digest(report_id, str(index), path.name, str(size), str(stat.st_mtime_ns))
    return f"artifact-{digest[:20]}"


def report_download_read_model(report: dict) -> list[dict]:
    report_id = safe_reference(report.get("id"))
    workflow_context = report.get("workflowContext") if isinstance(report.get("workflowContext"), dict) else {}
    if (
        not report_id
        or report.get("linkedPropId") != "terminal_workstation"
        or report.get("type") not in DASHBOARD_WORKFLOW_REPORT_TYPES.get("terminal_workstation", set())
        or str(report.get("status") or "").lower() not in DASHBOARD_WORKFLOW_SOURCE_READY_STATUSES
        or workflow_context.get("propId") != "terminal_workstation"
    ):
        return []
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    result = []
    for index, artifact in enumerate(artifacts[:40]):
        resolved = resolve_report_download_artifact(artifact)
        if not resolved:
            continue
        path, media_type, label = resolved
        byte_size = path.stat().st_size
        artifact_id = report_download_id(report_id, index, path, byte_size)
        public_file_name = f"source-output{path.suffix.lower()}"
        public_media_type = media_type.split(";", 1)[0]
        result.append({
            "id": artifact_id,
            "kind": "source_download",
            # Never expose a backend-provided label here: old reports may have
            # stored an absolute local path in that field.  The public download
            # model intentionally uses a stable, non-sensitive display label.
            "label": "ไฟล์ Source จาก Backend",
            "available": True,
            "fileName": public_file_name,
            "contentType": public_media_type,
            "mediaType": public_media_type,
            "extension": path.suffix.lower(),
            "byteSize": byte_size,
            "url": f"/api/reports/{report_id}/downloads/{artifact_id}",
        })
    return result


def resolve_report_download(report_id: str, artifact_id: str) -> tuple[Path, str] | None:
    if not SAFE_ID_PATTERN.fullmatch(report_id) or not SAFE_ID_PATTERN.fullmatch(artifact_id):
        return None
    report_path = RUNTIME_REPORTS_DIR / f"{report_id}.json"
    report = read_json(report_path, None) if report_path.is_file() else None
    if not isinstance(report, dict) or safe_reference(report.get("id")) != report_id:
        return None
    allowed_ids = {item.get("id") for item in report_download_read_model(report)}
    if artifact_id not in allowed_ids:
        return None
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    for index, artifact in enumerate(artifacts[:40]):
        resolved = resolve_report_download_artifact(artifact)
        if not resolved:
            continue
        path, media_type, _label = resolved
        if report_download_id(report_id, index, path, path.stat().st_size) == artifact_id:
            return path, media_type
    return None


def report_attachment_id(
    report_id: str,
    index: int,
    path: Path,
    byte_size: int | None = None,
) -> str:
    size = path.stat().st_size if byte_size is None else byte_size
    digest = payload_digest(report_id, str(index), path.name, str(size))
    return f"image-{digest[:20]}"


def report_attachment_read_model(report: dict) -> list[dict]:
    report_id = safe_reference(report.get("id"))
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    if not report_id:
        return []
    result = []
    for index, artifact in enumerate(artifacts[:40]):
        resolved = resolve_report_image_artifact(artifact)
        if not resolved:
            continue
        path, media_type, label = resolved
        try:
            byte_size = path.stat().st_size
        except OSError:
            continue
        attachment_id = report_attachment_id(report_id, index, path, byte_size)
        result.append({
            "id": attachment_id,
            "kind": "image",
            "label": label or f"รูปหลักฐาน {len(result) + 1}",
            "mediaType": media_type,
            "url": f"/api/reports/{report_id}/attachments/{attachment_id}",
            "byteSize": byte_size,
        })
    return result


def resolve_report_attachment(report_id: str, attachment_id: str) -> tuple[Path, str] | None:
    if not SAFE_ID_PATTERN.fullmatch(report_id) or not SAFE_ID_PATTERN.fullmatch(attachment_id):
        return None
    report_path = RUNTIME_REPORTS_DIR / f"{report_id}.json"
    report = read_json(report_path, None) if report_path.is_file() else None
    if not isinstance(report, dict) or safe_reference(report.get("id")) != report_id:
        return None
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    for index, artifact in enumerate(artifacts[:40]):
        resolved = resolve_report_image_artifact(artifact)
        if not resolved:
            continue
        path, media_type, _label = resolved
        try:
            byte_size = path.stat().st_size
        except OSError:
            continue
        if report_attachment_id(report_id, index, path, byte_size) == attachment_id:
            return path, media_type
    return None


def _mission_blocker_read_model(mission: dict) -> dict | None:
    """Explain a blocked mission in Thai without exposing prompts, paths, or secrets."""
    if not isinstance(mission, dict):
        return None
    status = str(mission.get("status") or "").strip().lower()
    work_status = str(mission.get("workStatus") or "").strip().lower()
    phase = str(mission.get("phase") or "").strip().lower()
    if (
        status not in {"blocked", "failed", "error"}
        and work_status not in {"blocked", "failed", "error", "invalid_council_output"}
        and phase not in {
            "council_round_expired",
            "council_queue_incomplete",
            "auto_guarded_authorization_blocked",
        }
    ):
        return None

    execution = (
        mission.get("execution")
        if isinstance(mission.get("execution"), dict)
        else {}
    )
    context = (
        mission.get("analysisContext")
        if isinstance(mission.get("analysisContext"), dict)
        else {}
    )
    reason_code = redact_text(
        str(mission.get("errorCode") or work_status or phase or status or "blocked"),
        120,
    )
    root_cause_code = redact_text(
        str(
            execution.get("lastDeferredReason")
            or mission.get("runnerStatus")
            or mission.get("blockedCapability")
            or reason_code
        ),
        120,
    )
    owner = str(mission.get("owner") or "")
    role_name = {
        "optimization_agent": "Technical Consultant",
        "backtest_analyst": "Price Action Consultant",
        "codex_mcp_operator": "News Consultant",
    }.get(owner, "Agent ตัวนี้")

    title_th = f"{role_name} ยังทำงานรอบนี้ไม่สำเร็จ"
    cause_th = (
        "Local Runner หยุดงานรอบนี้ไว้เพื่อไม่ให้ผลที่ไม่ครบถูกนำไปใช้ต่อ"
    )
    resolution_steps_th = [
        "กดตรวจสถานะใหม่เพื่ออ่านสถานะล่าสุดจาก Local Runner",
        "เมื่อมี Snapshot ใหม่ ให้เริ่มวิเคราะห์ Specialist ทั้ง 3 ตัวพร้อมกันอีกครั้ง",
    ]

    if root_cause_code == "local_rate_limited":
        title_th = f"คิวงานของ {role_name} เต็มในช่วงเวลานั้น"
        cause_th = (
            "Local Runner เลื่อนงานเพราะ Agent ตัวนี้ใช้จำนวนรอบต่อชั่วโมงครบแล้ว "
            "งานจึงยังไม่ได้เปิด Codex และหมดเวลาร่วมของสภาก่อนเริ่ม"
        )
        resolution_steps_th = [
            "รอให้รอบจำกัดต่อชั่วโมงคืน หรือรอแท่งเทียนใหม่",
            "กดตรวจสถานะใหม่ แล้วเริ่มวิเคราะห์ Specialist ทั้ง 3 ตัวพร้อมกัน",
            "ไม่ต้องรันเฉพาะ Agent ตัวเดียว เพราะทั้ง 3 ตัวต้องใช้ Snapshot และเวลารอบเดียวกัน",
        ]
    elif root_cause_code in {"codex_limit_reached", "codex_rate_limited"}:
        title_th = "Codex ถึงขีดจำกัดการใช้งานของรอบนี้"
        cause_th = (
            "Local Runner ตรวจพบว่าโควตา Codex ยังไม่พร้อม จึงไม่ได้เริ่มงานวิเคราะห์และไม่ได้ส่งคำสั่งไป MT4"
        )
        resolution_steps_th = [
            "รอให้หน้า Rate Limit แสดงว่ามีโควตาใช้งาน",
            "กดตรวจสถานะใหม่ แล้วเริ่มวิเคราะห์ทั้ง 3 ตัวจาก Snapshot ใหม่",
        ]
    elif root_cause_code in {"quota_unavailable_or_stale", "quota_unavailable"}:
        title_th = "ยังยืนยันสถานะ Rate Limit ของ Codex ไม่ได้"
        cause_th = (
            "ข้อมูลโควตาที่ Local Runner อ่านได้เก่าหรือไม่สมบูรณ์ ระบบจึงหยุดไว้ก่อนเพื่อไม่ให้เริ่มงานโดยเดา"
        )
        resolution_steps_th = [
            "ตรวจว่า Codex ยัง Login อยู่และหน้า Rate Limit อัปเดตได้",
            "กดตรวจสถานะใหม่ก่อนเริ่มวิเคราะห์ทั้ง 3 ตัว",
        ]
    elif root_cause_code in {"auth_required", "codex_auth_required"}:
        title_th = "Codex ในเครื่องยังต้องเข้าสู่ระบบ"
        cause_th = "Local Runner ยังใช้บัญชี Codex ที่ Login ในเครื่องไม่ได้ จึงยังไม่เปิดงานวิเคราะห์"
        resolution_steps_th = [
            "เปิด Codex และเข้าสู่ระบบให้เรียบร้อย",
            "กลับมากดตรวจสถานะใหม่ แล้วเริ่มวิเคราะห์ทั้ง 3 ตัว",
        ]
    elif root_cause_code in {"runner_busy", "worker_busy"}:
        title_th = "Local Runner กำลังทำงานอื่นอยู่"
        cause_th = "ช่องทำงานพร้อมกันเต็มในช่วงเวลานั้น และรอบสภาหมดเวลาก่อน Agent ตัวนี้ได้เริ่ม"
        resolution_steps_th = [
            "รอให้งานที่กำลังทำอยู่จบ",
            "กดตรวจสถานะใหม่ แล้วเริ่มรอบใหม่เมื่อมี Snapshot ใหม่",
        ]
    elif root_cause_code in {"runner_missing", "runner_not_ready", "auth_error"}:
        title_th = "Codex Runner ยังไม่พร้อมทำงาน"
        cause_th = "Local Runner ยังเปิดตัวรัน Codex ไม่สำเร็จ จึงหยุดงานนี้โดยไม่เรียกเครื่องมือจริง"
        resolution_steps_th = [
            "ตรวจสถานะ Bridge และ Codex Runner ให้ขึ้นพร้อมใช้งาน",
            "กดตรวจสถานะใหม่ แล้วเริ่มวิเคราะห์ทั้ง 3 ตัวอีกครั้ง",
        ]
    elif root_cause_code in {
        "council_round_deadline_expired",
        "council_round_deadline_insufficient",
        "council_rate_limit_exceeds_round_deadline",
        "council_quota_backoff_exceeds_round_deadline",
        "council_runner_backoff_exceeds_round_deadline",
    } or reason_code in {
        "council_round_deadline_expired",
        "council_round_deadline_insufficient",
        "council_rate_limit_exceeds_round_deadline",
        "council_quota_backoff_exceeds_round_deadline",
        "council_runner_backoff_exceeds_round_deadline",
    }:
        title_th = "เวลาร่วมของสภา AI หมดก่อนวิเคราะห์ครบ 3 ตัว"
        cause_th = "Agent ทำงานไม่ครบภายในเวลาของ Snapshot เดียวกัน ระบบจึงยกเลิกรอบนี้และไม่ส่งคำสั่งไป MT4"
        resolution_steps_th = [
            "กดตรวจสถานะใหม่เพื่อยืนยันว่า Local Runner พร้อม",
            "รอ Snapshot ใหม่ แล้วเริ่ม Specialist ทั้ง 3 ตัวพร้อมกันอีกครั้ง",
        ]
    elif work_status == "invalid_council_output" or reason_code == "invalid_council_output":
        title_th = f"คำตอบของ {role_name} ยังไม่ผ่านรูปแบบของสภา"
        cause_th = "ผลตอบกลับไม่ครบหรือไม่ตรงกับ Snapshot และบทบาทที่กำหนด ระบบจึงไม่นำผลนี้ไปโหวต"
        resolution_steps_th = [
            "กดตรวจสถานะใหม่เพื่อดูว่า Snapshot เปลี่ยนแล้วหรือยัง",
            "เริ่มวิเคราะห์ทั้ง 3 ตัวใหม่จาก Snapshot ปัจจุบัน",
        ]
    elif root_cause_code in {"web_search_unavailable", "network_unavailable"}:
        title_th = "News Consultant ยังอ่านข่าวภายนอกไม่ได้"
        cause_th = "Web Search หรือเครือข่ายยังไม่พร้อม ระบบจึงไม่สร้างข้อมูลข่าวจำลองและไม่นำผลไปโหวต"
        resolution_steps_th = [
            "ตรวจอินเทอร์เน็ตและสถานะ Web Search ของ Codex Runner",
            "กดตรวจสถานะใหม่ แล้วเริ่มวิเคราะห์ทั้ง 3 ตัวอีกครั้ง",
        ]

    safe_resolution_steps = [
        redact_text(step, 300) for step in resolution_steps_th[:4]
    ]
    return {
        "schemaVersion": "mission-blocker-v1",
        "active": True,
        "titleTh": redact_text(title_th, 220),
        "causeTh": redact_text(cause_th, 1000),
        "resolutionStepsTh": safe_resolution_steps,
        # Flat copies remain readable when this mission is nested deeply inside
        # a prop report whose generic JSON sanitizer reaches its depth limit.
        "resolutionStep1Th": safe_resolution_steps[0] if safe_resolution_steps else None,
        "resolutionStep2Th": safe_resolution_steps[1] if len(safe_resolution_steps) > 1 else None,
        "resolutionStep3Th": safe_resolution_steps[2] if len(safe_resolution_steps) > 2 else None,
        "resolutionStep4Th": safe_resolution_steps[3] if len(safe_resolution_steps) > 3 else None,
        "reasonCode": reason_code,
        "rootCauseCode": root_cause_code,
        "retryAction": "refresh_status",
        "retryLabelTh": "ตรวจสถานะใหม่",
        "retryOnNewSnapshot": True,
        "terminalActionBlocked": True,
        "processStarted": bool(execution.get("processStarted", False)),
        "deferralCount": clamp_int(execution.get("deferralCount"), 0, 0, 1000),
        "retryAt": execution.get("nextAttemptAt"),
        "roundDeadlineAt": context.get("roundDeadlineAt"),
        "roleId": safe_reference(context.get("roleId")),
        "snapshotId": safe_reference(context.get("snapshotId")),
        "source": "backend_mission_truth",
    }


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
        "webSearchEnabled": bool(
            execution.get("webSearchEnabled", mission.get("toolId") == "codex_web_research")
        ),
        "webSearchMode": redact_text(str(execution.get("webSearchMode") or ""), 40) or (
            "live" if mission.get("toolId") == "codex_web_research" else "disabled"
        ),
        "webSearchUsed": bool(
            execution.get("webSearchUsed", mission.get("webSearchUsed", False))
        ),
        "webSearchEvidenceVerified": bool(
            execution.get(
                "webSearchEvidenceVerified",
                mission.get("webSearchEvidenceVerified", False),
            )
        ),
        "nextAttemptAt": execution.get("nextAttemptAt"),
        "runnerStatus": redact_text(str(mission.get("runnerStatus") or ""), 80) or None,
        "workStatus": redact_text(str(mission.get("workStatus") or ""), 40) or None,
        "blockedCapability": redact_text(str(mission.get("blockedCapability") or ""), 160) or None,
        "reasonCode": redact_text(str(mission.get("errorCode") or ""), 120) or None,
        "blocker": _mission_blocker_read_model(mission),
        "evidence": evidence_read_model(mission.get("evidence")),
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
        "workflowContext": workflow_context_read_model(mission.get("workflowContext")),
        "agentTransfer": _agent_transfer_storage(
            mission.get("agentTransfer")
            or ((mission.get("workflowContext") or {}).get("agentTransfer") if isinstance(mission.get("workflowContext"), dict) else None)
        ),
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
            "snapshotId": safe_reference(delegation.get("snapshotId")),
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
    downloads = report_download_read_model(report)
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
        "evidence": evidence_read_model(report.get("evidence")),
        "executionEvidence": report_execution_evidence_read_model(
            report.get("executionEvidence"),
            report.get("type"),
            report.get("linkedMissionId"),
        ),
        "attachments": report_attachment_read_model(report),
        "downloads": downloads,
        "downloadCount": len(downloads),
        "artifactCount": sum(1 for item in artifacts if item),
        "safety": sanitize_json_value(report.get("safety") if isinstance(report.get("safety"), dict) else {}),
        "workflowContext": workflow_context_read_model(report.get("workflowContext")),
        "agentTransfer": _agent_transfer_storage(
            report.get("agentTransfer")
            or ((report.get("workflowContext") or {}).get("agentTransfer") if isinstance(report.get("workflowContext"), dict) else None)
        ),
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


def _default_dashboard_workflow_settings() -> dict:
    return {
        "version": "dashboard-workflow-settings-v1",
        "discoverySchedule": {
            "requestedEnabled": False,
            "times": ["09:00"],
            "timezone": "Asia/Bangkok",
            "savedAt": None,
        },
        "indicatorScoutSchedule": {
            "requestedEnabled": False,
            "times": ["09:00"],
            "timezone": "Asia/Bangkok",
            "savedAt": None,
        },
        "newsBiasSchedule": {
            "requestedEnabled": False,
            "times": ["07:00", "13:00", "19:00"],
            "minimumImpact": "high",
            "timezone": "Asia/Bangkok",
            "savedAt": None,
        },
        "agentPreferences": {
            "language": "th",
            "modelTier": "specialist_balanced",
            "tokenBudget": 12000,
            "timeoutSeconds": 120,
            "outputLimitChars": 7000,
            "rateReservePercent": 30,
            "savedAt": None,
        },
    }


def load_dashboard_workflow_settings() -> dict:
    ensure_runtime_dir()
    with DASHBOARD_WORKFLOW_SETTINGS_LOCK:
        payload = read_json(
            DASHBOARD_WORKFLOW_SETTINGS_PATH,
            _default_dashboard_workflow_settings(),
        )
    return payload if isinstance(payload, dict) else _default_dashboard_workflow_settings()


def _dashboard_discovery_schedule_read_model(settings: object | None = None) -> dict:
    source = settings if isinstance(settings, dict) else load_dashboard_workflow_settings()
    schedule = (
        source.get("discoverySchedule")
        if isinstance(source.get("discoverySchedule"), dict)
        else {}
    )
    times = [
        value
        for value in (
            str(item).strip()
            for item in (schedule.get("times") if isinstance(schedule.get("times"), list) else [])[:6]
        )
        if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value)
    ]
    return {
        # The request can be saved now, but there is no background workflow
        # scheduler for this dashboard yet. Effective execution stays off.
        "enabled": False,
        "requestedEnabled": bool(schedule.get("requestedEnabled", False)),
        "times": times or ["09:00"],
        "timezone": "Asia/Bangkok",
        "lastSavedAt": schedule.get("savedAt"),
        "automaticExternalActions": False,
        "automaticRunsImplemented": False,
        "status": "saved_no_scheduler" if schedule.get("savedAt") else "disabled_by_default",
        "statusLabelTh": (
            "บันทึกเวลาแล้ว แต่ยังไม่เปิดงานอัตโนมัติ"
            if schedule.get("savedAt")
            else "ยังไม่เปิดรอบค้นหาอัตโนมัติ"
        ),
    }


def _dashboard_saved_schedule_read_model(
    settings_key: str,
    *,
    default_times: list[str],
    settings: object | None = None,
) -> dict:
    source = settings if isinstance(settings, dict) else load_dashboard_workflow_settings()
    schedule = source.get(settings_key) if isinstance(source.get(settings_key), dict) else {}
    times = []
    for item in (schedule.get("times") if isinstance(schedule.get("times"), list) else [])[:6]:
        candidate = str(item or "").strip()
        if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", candidate) and candidate not in times:
            times.append(candidate)
    model = {
        "enabled": False,
        "requestedEnabled": bool(schedule.get("requestedEnabled", False)),
        "times": times or list(default_times),
        "timezone": "Asia/Bangkok",
        "lastSavedAt": schedule.get("savedAt"),
        "automaticExternalActions": False,
        "automaticRunsImplemented": False,
        "status": "saved_no_scheduler" if schedule.get("savedAt") else "disabled_by_default",
        "statusLabelTh": (
            "บันทึกเวลาแล้ว แต่ยังไม่มี Scheduler ทำงานอัตโนมัติ"
            if schedule.get("savedAt")
            else "ยังไม่เปิด Scheduler อัตโนมัติ"
        ),
    }
    minimum_impact = str(schedule.get("minimumImpact") or "").strip().lower()
    if minimum_impact in {"low", "medium", "high"}:
        model["minimumImpact"] = minimum_impact
    return model


def _dashboard_agent_preferences_read_model(settings: object | None = None) -> dict:
    source = settings if isinstance(settings, dict) else load_dashboard_workflow_settings()
    defaults = _default_dashboard_workflow_settings()["agentPreferences"]
    stored = source.get("agentPreferences") if isinstance(source.get("agentPreferences"), dict) else {}
    language = str(stored.get("language") or defaults["language"])
    model_tier = str(stored.get("modelTier") or defaults["modelTier"])
    return {
        "language": language if language in {"th", "en"} else "th",
        "modelTier": (
            model_tier
            if model_tier in {"manager_quality", "risk_quality", "specialist_balanced", "specialist_fast"}
            else "specialist_balanced"
        ),
        "tokenBudget": clamp_int(stored.get("tokenBudget"), 12000, 256, 100000),
        "timeoutSeconds": clamp_int(stored.get("timeoutSeconds"), 120, 15, 1800),
        "outputLimitChars": clamp_int(stored.get("outputLimitChars"), 7000, 1000, 100000),
        "rateReservePercent": clamp_int(stored.get("rateReservePercent"), 30, 0, 90),
        "lastSavedAt": stored.get("savedAt"),
        "providerModelIdAccepted": False,
        "credentialsAccepted": False,
    }


def _empty_fx_bias_rows() -> list[dict]:
    return [
        {
            "pair": pair,
            "shortBias": "unknown",
            "mediumBias": "unknown",
            "longBias": "unknown",
            "confidence": None,
            "sourceLinks": [],
            "status": "pending",
            "updatedAt": None,
        }
        for pair in FX_BIAS_PAIRS
    ]


def _normalize_fx_bias(value: object) -> str:
    candidate = str(value or "").strip().lower()
    aliases = {
        "buy": "bullish",
        "long": "bullish",
        "bullish": "bullish",
        "sell": "bearish",
        "short": "bearish",
        "bearish": "bearish",
        "hold": "neutral",
        "neutral": "neutral",
        "unknown": "unknown",
    }
    return aliases.get(candidate, "unknown")


def _fx_bias_source_links(value: object) -> list[dict]:
    rows = value if isinstance(value, list) else []
    candidates = []
    for index, item in enumerate(rows[:12]):
        if isinstance(item, dict):
            candidates.append({
                "label": item.get("label") or f"Source {index + 1}",
                "url": item.get("url"),
                "note": item.get("note") or "",
            })
        elif isinstance(item, str):
            candidates.append({"label": f"Source {index + 1}", "url": item, "note": ""})
    return evidence_read_model(candidates)


def _fx_bias_read_model(reports: list[dict] | None = None) -> dict:
    rows = _empty_fx_bias_rows()
    by_pair = {row["pair"]: row for row in rows}
    candidates = reports if isinstance(reports, list) else load_runtime_reports(limit=240)
    verified_report = next((
        report for report in candidates
        if isinstance(report, dict)
        and report.get("linkedPropId") == "left_signal_cube"
        and report.get("type") == "fx_news_bias_report"
        and str(report.get("status") or "").lower() in DASHBOARD_WORKFLOW_SOURCE_READY_STATUSES
        and isinstance(report.get("workflowContext"), dict)
        and report["workflowContext"].get("propId") == "left_signal_cube"
        and report["workflowContext"].get("actionId") == "build_fx_pair_bias"
    ), None)
    verified_count = 0
    if isinstance(verified_report, dict):
        metrics = verified_report.get("metrics") if isinstance(verified_report.get("metrics"), dict) else {}
        pair_bias = metrics.get("pairBias") if isinstance(metrics.get("pairBias"), list) else []
        for item in pair_bias[:56]:
            if not isinstance(item, dict):
                continue
            pair = str(item.get("pair") or "").strip().upper()
            if pair not in by_pair:
                continue
            links = _fx_bias_source_links(item.get("sourceLinks") or item.get("sources"))
            if not links:
                continue
            row = by_pair[pair]
            row.update({
                "shortBias": _normalize_fx_bias(item.get("shortBias") or item.get("short")),
                "mediumBias": _normalize_fx_bias(item.get("mediumBias") or item.get("medium")),
                "longBias": _normalize_fx_bias(item.get("longBias") or item.get("long")),
                "confidence": clamp_int(item.get("confidence"), 0, 0, 100) if item.get("confidence") is not None else None,
                "sourceLinks": links,
                "status": "verified",
                "updatedAt": verified_report.get("updatedAt") or verified_report.get("createdAt"),
            })
            verified_count += 1
    return {
        "schemaVersion": "fx-pair-bias-read-model-v1",
        "pairs": rows,
        "pairCount": len(rows),
        "verifiedPairCount": verified_count,
        "complete28": verified_count == len(FX_BIAS_PAIRS),
        "dataStatus": "verified" if verified_count else "no_verified_data",
        "sourceReportId": safe_reference(verified_report.get("id")) if isinstance(verified_report, dict) else None,
        "fabricatedData": False,
    }


def _safe_vps_hq_health_snapshot(bridge: dict | None = None) -> dict:
    status = bridge if isinstance(bridge, dict) else bridge_status()
    worker = mission_worker_read_model()
    codex = status.get("codex") if isinstance(status.get("codex"), dict) else {}
    mcp = status.get("mcp") if isinstance(status.get("mcp"), dict) else {}
    return {
        "schemaVersion": "vps-hq-health-v1",
        "checkedAt": status.get("time") or utc_now(),
        "localBridge": {
            "status": redact_text(str(status.get("status") or "unknown"), 40),
            "mode": redact_text(str(status.get("mode") or "unknown"), 80),
        },
        "codexRunner": {"status": redact_text(str(codex.get("status") or "unknown"), 40)},
        "mcp": {
            "status": redact_text(str(mcp.get("status") or "unknown"), 40),
            "configPresent": bool(mcp.get("configPresent", False)),
        },
        "missionWorker": {
            "status": worker.get("status"),
            "queued": worker.get("queued", 0),
            "watchdogAlive": bool(worker.get("watchdogAlive", False)),
        },
        "vpsMetrics": {
            "status": "not_observed",
            "cpuPercent": None,
            "memoryPercent": None,
            "diskPercent": None,
            "uptimeSeconds": None,
        },
        "credentialsExposed": False,
        "rateLimitDetailsIncluded": False,
    }


def _workflow_report_platforms(report: dict) -> set[str]:
    platforms: set[str] = set()
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    workflow_context = report.get("workflowContext") if isinstance(report.get("workflowContext"), dict) else {}
    inputs = workflow_context.get("inputs") if isinstance(workflow_context.get("inputs"), dict) else {}
    for value in (metrics.get("platform"), inputs.get("platform"), report.get("platform")):
        candidate = str(value or "").strip().lower()
        if candidate in {"mt4", "mt5", "mql4", "mql5"}:
            platforms.add(candidate)
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    for artifact in artifacts[:40]:
        candidate, _label = report_artifact_storage_value(artifact)
        candidate = candidate.replace("\\", "/")
        if not candidate or Path(candidate).is_absolute() or ".." in Path(candidate).parts:
            continue
        suffix = Path(candidate).suffix.lower()
        if suffix == ".mq4":
            platforms.update({"mt4", "mql4"})
        elif suffix == ".mq5":
            platforms.update({"mt5", "mql5"})
    projected = report.get("platforms") if isinstance(report.get("platforms"), list) else []
    platforms.update(
        str(value).strip().lower()
        for value in projected
        if str(value).strip().lower() in {"mt4", "mt5", "mql4", "mql5"}
    )
    return platforms


def _workspace_source_catalog() -> list[dict]:
    roots = (
        (PROJECT_ROOT / "workspace").resolve(strict=False),
        (MEMORY_DIR / "artifacts").resolve(strict=False),
    )
    rows = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
            if len(rows) >= 200 or not path.is_file() or path.is_symlink():
                continue
            suffix = path.suffix.lower()
            if suffix not in {".mq4", ".mq5"}:
                continue
            resolved = path.resolve(strict=False)
            try:
                relative = resolved.relative_to(PROJECT_ROOT.resolve(strict=False))
                source_relative = resolved.relative_to(root)
                stat = resolved.stat()
            except (ValueError, OSError):
                continue
            if stat.st_size <= 0 or stat.st_size > MAX_REPORT_DOWNLOAD_BYTES:
                continue
            if not _report_download_content_is_safe(resolved):
                continue
            source_id = "workspace-" + payload_digest(
                "workspace-source-v1",
                relative.as_posix(),
                str(stat.st_size),
                str(stat.st_mtime_ns),
            )[:20]
            rows.append({
                "id": source_id,
                "sourceId": source_id,
                "label": redact_text(path.name, 160),
                "displayName": redact_text(path.name, 160),
                "platform": "mql4" if suffix == ".mq4" else "mql5",
                "language": "MQL4" if suffix == ".mq4" else "MQL5",
                "extension": suffix,
                "byteSize": stat.st_size,
                "updatedAt": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "storageRef": relative.as_posix(),
                "workspaceRelative": source_relative.as_posix(),
            })
    return rows


def _workspace_source_read_model() -> list[dict]:
    return [
        {key: value for key, value in row.items() if key not in {"storageRef", "workspaceRelative"}}
        for row in _workspace_source_catalog()
    ]


def _resolve_workspace_source(source_id: object, platform: object) -> dict | None:
    safe_source_id = safe_reference(source_id)
    expected_platform = str(platform or "").strip().lower()
    if not safe_source_id or expected_platform not in {"mql4", "mql5"}:
        return None
    row = next((item for item in _workspace_source_catalog() if item.get("id") == safe_source_id), None)
    if not row or row.get("platform") != expected_platform:
        return None
    return row


def _workflow_source_allowed(action_id: str, report: dict) -> bool:
    policy = DASHBOARD_WORKFLOW_SOURCE_POLICIES.get(action_id)
    if not isinstance(policy, dict):
        return False
    source_prop_id = safe_reference(report.get("linkedPropId") or report.get("sourcePropId"))
    report_type = str(report.get("type") or "").strip()
    status = str(report.get("status") or "").strip().lower()
    allowed = bool(
        source_prop_id in set(policy.get("propIds") or ())
        and report_type in set(policy.get("reportTypes") or ())
        and status in DASHBOARD_WORKFLOW_SOURCE_READY_STATUSES
    )
    required_platforms = set(policy.get("platforms") or ())
    if allowed and required_platforms:
        allowed = bool(_workflow_report_platforms(report).intersection(required_platforms))
    return allowed


def _workflow_record_matches_prop(record: dict, prop_id: str) -> bool:
    allowed_types = DASHBOARD_WORKFLOW_REPORT_TYPES.get(prop_id, set())
    report_type = str(record.get("reportType") or record.get("type") or "")
    context = record.get("workflowContext") if isinstance(record.get("workflowContext"), dict) else {}
    context_matches = bool(
        context.get("propId") == prop_id
        and context.get("actionId") in DASHBOARD_WORKFLOW_ACTIONS
        and DASHBOARD_WORKFLOW_ACTIONS[context.get("actionId")].get("propId") == prop_id
    )
    type_matches = report_type in allowed_types
    if prop_id in DASHBOARD_WORKFLOW_CONTEXT_REQUIRED_PROP_IDS:
        return bool(type_matches and context_matches)
    return bool(type_matches or context_matches)


def _workflow_source_binding(
    target_prop_id: str,
    action_id: str,
    report: dict,
    missions: list[dict],
) -> dict | None:
    """Validate the source Mission/Report pair without creating a delivery."""
    action = DASHBOARD_WORKFLOW_ACTIONS.get(action_id)
    if not isinstance(action, dict) or action.get("propId") != target_prop_id:
        return None
    report_id = safe_reference(report.get("id"))
    source_prop_id = safe_reference(report.get("linkedPropId") or report.get("sourcePropId"))
    source_mission_id = safe_reference(report.get("linkedMissionId"))
    source_owner_agent_id = safe_reference(report.get("ownerAgentId"))
    transfer_agent_id = safe_reference(action.get("ownerAgentId"))
    if (
        not report_id
        or source_prop_id not in DASHBOARD_WORKFLOW_PROP_IDS
        or not source_mission_id
        or source_owner_agent_id not in EXPECTED_AGENT_IDS
        or transfer_agent_id not in EXPECTED_AGENT_IDS
    ):
        return None
    source_mission = next(
        (
            mission
            for mission in missions
            if isinstance(mission, dict)
            and safe_reference(mission.get("id")) == source_mission_id
        ),
        None,
    )
    if not source_mission:
        return None
    mission_status = str(source_mission.get("status") or "").strip().lower()
    if mission_status not in DASHBOARD_WORKFLOW_SOURCE_MISSION_READY_STATUSES:
        return None
    if mission_status == "archived" and source_mission.get("archivedSuccessful") is not True:
        return None
    mission_report_ids = {
        item
        for item in (
            safe_reference(value)
            for value in (source_mission.get("reportIds") if isinstance(source_mission.get("reportIds"), list) else [])
        )
        if item
    }
    if (
        report_id not in mission_report_ids
        or safe_reference(source_mission.get("targetId")) != source_prop_id
        or safe_reference(source_mission.get("owner")) != source_owner_agent_id
    ):
        return None
    return {
        "mode": DASHBOARD_WORKFLOW_TRANSFER_MODE,
        "sourceReportId": report_id,
        "sourcePropId": source_prop_id,
        "sourceMissionId": source_mission_id,
        "transferAgentId": transfer_agent_id,
        "sourceOwnerAgentId": source_owner_agent_id,
        "targetPropId": target_prop_id,
    }


def _workflow_source_transfer_record(
    target_prop_id: str,
    action_id: str,
    report: dict,
    missions: list[dict],
) -> dict | None:
    """Resolve only a completed Agent handoff Mission delivered to this prop."""
    binding = _workflow_source_binding(target_prop_id, action_id, report, missions)
    if not binding:
        return None
    for handoff in missions:
        if not isinstance(handoff, dict):
            continue
        handoff_id = safe_reference(handoff.get("id"))
        handoff_status = str(handoff.get("status") or "").strip().lower()
        if (
            not handoff_id
            or handoff.get("toolId") != "agent_report_transfer"
            or handoff_status not in DASHBOARD_WORKFLOW_SOURCE_MISSION_READY_STATUSES
            or (handoff_status == "archived" and handoff.get("archivedSuccessful") is not True)
            or safe_reference(handoff.get("targetId")) != target_prop_id
            or safe_reference(handoff.get("owner")) != binding["transferAgentId"]
        ):
            continue
        transfer = _agent_transfer_storage(
            handoff.get("agentTransfer")
            or ((handoff.get("workflowContext") or {}).get("agentTransfer") if isinstance(handoff.get("workflowContext"), dict) else None)
        )
        if not transfer or transfer.get("handoffMissionId") != handoff_id:
            continue
        if all(transfer.get(key) == value for key, value in binding.items()):
            return transfer
    return None


def _workflow_transfer_sources(
    prop_id: str,
    reports: list[dict] | None = None,
    action_id: str | None = None,
    missions: list[dict] | None = None,
) -> list[dict]:
    eligible_action_ids = [
        candidate_id
        for candidate_id, action in DASHBOARD_WORKFLOW_ACTIONS.items()
        if action.get("propId") == prop_id
        and candidate_id in DASHBOARD_WORKFLOW_SOURCE_POLICIES
        and (not action_id or candidate_id == action_id)
    ]
    if not eligible_action_ids:
        return []
    candidates = reports if isinstance(reports, list) else load_runtime_reports(limit=240)
    mission_rows = missions if isinstance(missions, list) else load_missions()
    rows: list[dict] = []
    seen: set[str] = set()
    for report in candidates:
        if not isinstance(report, dict):
            continue
        source_prop_id = safe_reference(report.get("linkedPropId") or report.get("sourcePropId"))
        report_id = safe_reference(report.get("id"))
        transfer_records = {
            candidate_id: transfer
            for candidate_id in eligible_action_ids
            if _workflow_source_allowed(candidate_id, report)
            for transfer in [_workflow_source_transfer_record(prop_id, candidate_id, report, mission_rows)]
            if transfer
        }
        allowed_action_ids = list(transfer_records)
        if (
            not report_id
            or report_id in seen
            or not allowed_action_ids
        ):
            continue
        seen.add(report_id)
        item = report_read_model_item(report)
        rows.append({
            "reportId": report_id,
            "sourcePropId": source_prop_id,
            "title": item.get("title"),
            "summary": item.get("summary"),
            "type": item.get("type"),
            "ownerAgentId": item.get("ownerAgentId"),
            "status": item.get("status"),
            "updatedAt": item.get("updatedAt") or item.get("createdAt"),
            "allowedActionIds": allowed_action_ids,
            "platforms": sorted(_workflow_report_platforms(report)),
            "agentTransfer": transfer_records.get(action_id) if action_id else None,
            "agentTransfersByActionId": transfer_records,
        })
        if len(rows) >= 80:
            break
    return rows


def _workflow_agent_transfer_destinations(source_prop_id: str) -> list[dict]:
    """Expose safe handoff destinations without exposing reports or direct dependencies."""
    if source_prop_id not in DASHBOARD_WORKFLOW_PROP_IDS:
        return []
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for action_id, policy in DASHBOARD_WORKFLOW_SOURCE_POLICIES.items():
        if source_prop_id not in set(policy.get("propIds") or ()):
            continue
        action = DASHBOARD_WORKFLOW_ACTIONS.get(action_id)
        if not isinstance(action, dict):
            continue
        target_prop_id = safe_reference(action.get("propId"))
        transfer_agent_id = safe_reference(action.get("ownerAgentId"))
        key = (target_prop_id or "", action_id)
        if (
            target_prop_id not in DASHBOARD_WORKFLOW_PROP_IDS
            or transfer_agent_id not in EXPECTED_AGENT_IDS
            or key in seen
        ):
            continue
        seen.add(key)
        rows.append({
            "targetPropId": target_prop_id,
            "actionId": action_id,
            "labelTh": redact_text(str(action.get("labelTh") or action_id), 160),
            "transferAgentId": transfer_agent_id,
        })
    return rows


def _workflow_action_contract_gate(prop_id: str, action_id: str, action: dict) -> dict:
    role = find_property_role(prop_id)
    allowed_actions = role.get("allowedDashboardActions") if isinstance(role.get("allowedDashboardActions"), list) else []
    if allowed_actions and action_id not in allowed_actions:
        return {"allowed": False, "reason": "action_not_allowed_by_property_contract"}
    action_policy = get_tool_policy(action_id)
    if not isinstance(action_policy, dict):
        return {"allowed": False, "reason": "missing_action_policy"}
    if prop_id not in set(action_policy.get("linkedPropIds") or ()):
        return {"allowed": False, "reason": "action_policy_prop_mismatch"}
    owner_agent_id = str(action.get("ownerAgentId") or "manager")
    if owner_agent_id not in set(action_policy.get("allowedAgents") or ()):
        return {"allowed": False, "reason": "action_policy_agent_denied"}
    tool_id = safe_reference(action.get("toolId"))
    tool_permission = evaluate_tool_permission(owner_agent_id, tool_id) if tool_id else {"allowed": True, "policy": {}}
    if not tool_permission.get("allowed"):
        return {"allowed": False, "reason": str(tool_permission.get("reason") or "tool_policy_denied")}
    return {
        "allowed": True,
        "reason": "allowed",
        "actionPolicy": action_policy,
        "toolPolicy": tool_permission.get("policy") if isinstance(tool_permission.get("policy"), dict) else {},
    }


def _workflow_action_availability(prop_id: str, action_id: str, action: dict, bridge: dict) -> dict:
    contract_gate = _workflow_action_contract_gate(prop_id, action_id, action)
    if not contract_gate.get("allowed"):
        return {
            "status": "configuration_required",
            "adapterStatus": redact_text(str(contract_gate.get("reason") or "policy_denied"), 80),
            "adapterImplemented": False,
            "runtimeReady": False,
            "realToolAvailable": False,
        }
    tool_id = safe_reference(action.get("toolId"))
    if not tool_id:
        action_policy = contract_gate.get("actionPolicy") if isinstance(contract_gate.get("actionPolicy"), dict) else {}
        return {
            "status": "settings_only",
            "adapterStatus": redact_text(str(action_policy.get("adapterStatus") or "backend_settings_store"), 80),
            "adapterImplemented": True,
            "runtimeReady": True,
            "realToolAvailable": False,
        }
    owner_agent_id = str(action.get("ownerAgentId") or "manager")
    permission = evaluate_tool_permission(owner_agent_id, tool_id)
    policy = permission.get("policy") if isinstance(permission.get("policy"), dict) else {}
    action_policy = contract_gate.get("actionPolicy") if isinstance(contract_gate.get("actionPolicy"), dict) else {}
    adapter_implemented = bool(
        permission.get("allowed")
        and policy
        and not tool_execution_capability_unavailable(policy)
    )
    codex_status = str((bridge.get("codex") or {}).get("status") or "unknown")
    runtime_ready = codex_status in {"ready", "ready_guarded"}
    return {
        "status": "ready" if adapter_implemented and runtime_ready else "configuration_required",
        "adapterStatus": redact_text(str(policy.get("adapterStatus") or "not_configured"), 80),
        "adapterImplemented": adapter_implemented,
        "runtimeReady": runtime_ready,
        "realToolAvailable": bool(adapter_implemented and runtime_ready),
        "codexStatus": redact_text(codex_status, 40),
        "webSearchAvailable": bool(
            tool_id == "codex_web_research"
            and policy.get("autoWebSearchAvailable") is True
        ),
        "actionPolicyReady": True,
        "requiresFullAccess": bool(action_policy.get("requiresFullAccess", False)),
        "approvalRequired": bool(action_policy.get("approvalRequired", False)),
    }


def workflow_dashboard_read_model(
    prop_id: str,
    *,
    reports: list[dict] | None = None,
    bridge: dict | None = None,
) -> dict:
    if prop_id not in DASHBOARD_WORKFLOW_PROP_IDS:
        return {}
    bridge_truth = bridge if isinstance(bridge, dict) else bridge_status()
    role = find_property_role(prop_id)
    contract_metadata = (
        role.get("workflowDashboard")
        if isinstance(role.get("workflowDashboard"), dict)
        else (role.get("workflow") if isinstance(role.get("workflow"), dict) else {})
    )
    default_titles = {
        "codex_mcp_portal": ("global_discovery", "เรดาร์ระบบเทรดทั่วโลก", "ค้นระบบและ EA ใหม่จากข้อมูลสาธารณะ พร้อมหลักฐานและการตรวจรายการซ้ำ"),
        "left_server_racks": ("deep_research", "คลังวิจัยระบบเทรด", "ขยายผลรายการที่เลือก ตรวจหลายแหล่ง และเก็บงานวิจัยที่ตรวจสอบแล้ว"),
        "right_server_racks": ("source_builder", "โรงงานสร้าง EA และ Indicator", "สร้างและตรวจ Source Code ใน Workspace โดยไม่อ้างว่า Compile หรือทดสอบแล้ว"),
        "right_tool_console": ("experiment_planning", "ห้องทดลอง EA", "เตรียมแผน Backtest, Optimization และ EA Discovery ก่อนต่อ Adapter จริง"),
        "left_audit_crystals": ("indicator_scout", "ศูนย์ค้นหา Indicator", "ค้นหา Indicator ใหม่จากเว็บไซต์สาธารณะ พร้อมหลักฐานและประวัติที่ไม่ปะปนกับงาน Risk เดิม"),
        "left_signal_cube": ("fx_news_bias", "ข่าวตลาดและมุมมอง FX", "สรุปข่าวและ Bias ระยะสั้น กลาง และยาวสำหรับ 28 คู่เงินโดยไม่สร้างข้อมูลแทนแหล่งข่าว"),
        "terminal_workstation": ("ea_development", "EA Development Studio", "ตรวจและพัฒนา Source MQL4/MQL5 ใน Workspace แบบ Source-only พร้อมไฟล์ดาวน์โหลดที่ Backend อนุญาต"),
        "right_status_crystals": ("hq_operations", "สถานะ VPS / HQ และ Agent", "อ่านสุขภาพ Local Runner และเก็บค่าแสดงผล Agent โดยไม่เปิดเผย Credential หรือข้อมูลบัญชี"),
    }
    stage, title_th, summary_th = default_titles[prop_id]
    display_order = clamp_int(contract_metadata.get("displayOrder"), 0, 0, 99)
    action_rows = []
    for action_id, action in DASHBOARD_WORKFLOW_ACTIONS.items():
        if action.get("propId") != prop_id:
            continue
        action_rows.append({
            "id": action_id,
            "labelTh": redact_text(str(action.get("labelTh") or action_id), 160),
            "descriptionTh": redact_text(str(action.get("descriptionTh") or ""), 600),
            "tabId": safe_reference(action.get("tabId")),
            "toolId": safe_reference(action.get("toolId")),
            "ownerAgentId": safe_reference(action.get("ownerAgentId")),
            "executionScope": redact_text(str(action.get("executionScope") or "analysis_only"), 80),
            "analysisOnly": bool(action.get("analysisOnly", True)),
            "sourceRequired": bool(action.get("sourceRequired", False)),
            "availability": _workflow_action_availability(prop_id, action_id, action, bridge_truth),
            "formFields": sanitize_json_value(list(action.get("formFields") or ())),
        })
    model = {
        "schemaVersion": "dashboard-workflow-v2",
        "propId": prop_id,
        "dashboardId": redact_text(str(contract_metadata.get("id") or stage), 80),
        "displayOrder": display_order or None,
        "independent": True,
        "coordinationMode": DASHBOARD_WORKFLOW_COORDINATION_MODE,
        "agentTransferOnly": True,
        "directDashboardDependency": False,
        "titleTh": redact_text(str(contract_metadata.get("titleTh") or role.get("displayTitle") or title_th), 160),
        "summaryTh": redact_text(str(contract_metadata.get("summaryTh") or role.get("purpose") or summary_th), 800),
        "tabs": sanitize_json_value(list(DASHBOARD_WORKFLOW_TABS.get(prop_id, ()))),
        "contractTabs": sanitize_json_value(
            role.get("localTabs") if isinstance(role.get("localTabs"), list) else []
        ),
        "allowedActionIds": [
            action_id
            for action_id in (role.get("allowedDashboardActions") or [])
            if action_id in DASHBOARD_WORKFLOW_ACTIONS
            and DASHBOARD_WORKFLOW_ACTIONS[action_id].get("propId") == prop_id
        ],
        "actions": action_rows,
        "transferPolicy": {
            "mode": DASHBOARD_WORKFLOW_COORDINATION_MODE,
            "agentTransferOnly": True,
            "directDashboardDependency": False,
            "publicSourceCatalogExposed": False,
            "frontendMaySubmitFields": ["sourceReportId"],
            "backendDerivedFields": [
                "sourcePropId",
                "sourceMissionId",
                "transferAgentId",
                "sourceOwnerAgentId",
                "targetPropId",
                "handoffMissionId",
            ],
            "missionStrategyTableRole": "global_ledger_only",
        },
        "agentTransferDestinations": _workflow_agent_transfer_destinations(prop_id),
        "agentDeliveredSources": _workflow_transfer_sources(prop_id, reports=reports),
        "guardrails": [
            "Frontend ส่งเฉพาะ Intent; Local Runner เป็นผู้สร้าง Mission และ Audit",
            "ไม่รับ Token, Cookie, รหัสผ่าน Broker หรือ Secret จากหน้าเว็บ",
            "งานสร้างโค้ดและแผนทดลองเป็น Source/Analysis only จนกว่าจะมี Adapter ที่ตรวจสอบได้",
            "การค้นเว็บอ่านข้อมูลสาธารณะเท่านั้น ไม่ Sign in ไม่กรอกฟอร์ม และไม่ส่งข้อมูลภายนอก",
        ],
        "contractMetadata": sanitize_json_value(contract_metadata),
        "updatedAt": utc_now(),
    }
    if prop_id == "codex_mcp_portal":
        model["schedule"] = _dashboard_discovery_schedule_read_model()
        model["sheetTemplate"] = {
            "schemaVersion": "global-trading-system-sheet-v1",
            "columns": list(DASHBOARD_DISCOVERY_SHEET_COLUMNS),
            "deduplicationFields": ["normalized_source_url", "system_name", "market", "timeframe"],
            "templateReference": "contracts/research/trading-system-sheet-template.csv",
            "connectionStatus": "not_connected",
            "connectionLabelTh": "ยังไม่ได้เชื่อม Google Sheet",
            "credentialsAcceptedByFrontend": False,
        }
        model["deduplication"] = {
            "backendOwned": False,
            "localReportCatalogAvailable": True,
            "googleSheetRowsAvailable": False,
            "deterministicComparisonAvailable": False,
            "mode": "prompt_assisted_unverified",
            "scopeLabelTh": "ขณะนี้ตรวจซ้ำได้เพียงช่วยเทียบกับ Report ในเครื่อง ยังไม่มีตัวตัดสินซ้ำแบบ deterministic และยังไม่รวม Google Sheet",
        }
    elif prop_id == "left_audit_crystals":
        model["schedule"] = _dashboard_saved_schedule_read_model(
            "indicatorScoutSchedule",
            default_times=["09:00"],
        )
        model["discoveryTruth"] = {
            "publicWebReadOnly": True,
            "localReportCatalogAvailable": True,
            "deterministicDeduplicationAvailable": False,
            "externalArchiveConnected": False,
            "screenshotAdapter": "coming_soon",
            "screenshotClaimAllowed": False,
        }
    elif prop_id == "left_signal_cube":
        model["schedule"] = _dashboard_saved_schedule_read_model(
            "newsBiasSchedule",
            default_times=["07:00", "13:00", "19:00"],
        )
        model["fxBias"] = _fx_bias_read_model(reports)
        model["newsTruth"] = {
            "publicWebReadOnly": True,
            "liveFeedConnected": False,
            "automaticSchedulerImplemented": False,
            "unknownWhenUnverified": True,
        }
    elif prop_id == "terminal_workstation":
        model["workspaceSources"] = _workspace_source_read_model()
        model["adapters"] = {
            "staticSourceInspection": "available",
            "workspaceSourceDevelopment": "guarded",
            "compiler": "coming_soon",
            "metaEditor": "coming_soon",
            "terminalInstall": "coming_soon",
            "backtest": "coming_soon",
        }
        model["downloads"] = {
            "availableFromVerifiedReportsOnly": True,
            "pathOpaque": True,
            "allowedExtensions": sorted(REPORT_DOWNLOAD_MEDIA_TYPES),
            "maxBytes": MAX_REPORT_DOWNLOAD_BYTES,
            "filesystemPathsExposed": False,
        }
    elif prop_id == "right_status_crystals":
        model["health"] = _safe_vps_hq_health_snapshot(bridge_truth)
        model["agentPreferences"] = _dashboard_agent_preferences_read_model()
        model["healthTruth"] = {
            "localObservationOnly": True,
            "vpsMetricsAdapter": "not_connected",
            "credentialsIncluded": False,
            "rateLimitAccountDetailsIncluded": False,
        }
    return model


def _sanitize_dashboard_workflow_form(action: dict, value: object) -> dict:
    if not isinstance(value, dict):
        raise RequestError("Workflow form must be an object.", 422)
    field_contracts = {
        str(item.get("id")): item
        for item in (action.get("formFields") or ())
        if isinstance(item, dict) and item.get("id")
    }
    unexpected = sorted(set(str(key) for key in value) - set(field_contracts) - {"timezone"})
    if unexpected:
        raise RequestError("Workflow form contains unsupported fields.", 422)
    result: dict[str, object] = {}
    for field_id, field in field_contracts.items():
        raw = value.get(field_id)
        field_type = str(field.get("type") or "text")
        required = bool(field.get("required", False))
        if field_type == "boolean":
            if raw is None and not required:
                continue
            if not isinstance(raw, bool):
                raise RequestError(f"Invalid boolean workflow field: {field_id}", 422)
            result[field_id] = raw
            continue
        if field_type == "time_list":
            values = raw if isinstance(raw, list) else [raw] if raw is not None else []
            times = []
            for item in values[:6]:
                candidate = str(item or "").strip()
                if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", candidate) and candidate not in times:
                    times.append(candidate)
            if required and not times:
                raise RequestError("กรุณาระบุเวลาอย่างน้อย 1 เวลาในรูปแบบ HH:MM", 422)
            result[field_id] = times
            continue
        if field_type in {"number", "integer"}:
            if raw is None or raw == "":
                if required:
                    raise RequestError(f"Missing required workflow field: {field_id}", 422)
                continue
            try:
                numeric = float(raw)
            except (TypeError, ValueError):
                raise RequestError(f"Invalid numeric workflow field: {field_id}", 422)
            if not math.isfinite(numeric):
                raise RequestError(f"Invalid numeric workflow field: {field_id}", 422)
            if field_id in {"targetProfitPercent", "maxDrawdownPercent"}:
                numeric = max(0.0, min(10000.0, numeric))
            if field_id == "targetTrades":
                numeric = max(1, min(100000, int(numeric)))
            if field_id == "maxItems":
                numeric = max(1, min(50, int(numeric)))
            if field_id == "tokenBudget":
                numeric = max(256, min(100000, int(numeric)))
            if field_id == "timeoutSeconds":
                numeric = max(15, min(1800, int(numeric)))
            if field_id == "outputLimitChars":
                numeric = max(1000, min(100000, int(numeric)))
            if field_id == "rateReservePercent":
                numeric = max(0, min(90, int(numeric)))
            result[field_id] = int(numeric) if field_type == "integer" else numeric
            continue
        text_value = " ".join(str(raw or "").replace("\x00", " ").split()).strip()
        if field_type == "source_report":
            reference = safe_reference(text_value)
            if required and not reference:
                raise RequestError("กรุณาเลือกรายงานต้นทาง", 422)
            if reference:
                result[field_id] = reference
            continue
        if field_type == "workspace_source":
            reference = safe_reference(text_value)
            if required and not reference:
                raise RequestError("กรุณาเลือก Source ใน Workspace", 422)
            if reference:
                result[field_id] = reference
            continue
        if field_type == "select":
            options = {str(item) for item in (field.get("options") or [])}
            if not text_value and not required:
                continue
            if text_value not in options:
                raise RequestError(f"Unsupported workflow option: {field_id}", 422)
            result[field_id] = text_value
            continue
        if required and not text_value:
            raise RequestError(f"Missing required workflow field: {field_id}", 422)
        if text_value:
            if contains_potential_secret(text_value):
                raise RequestError("Potential secret detected. Submit intent without credentials.", 422)
            if field_id == "marketDate":
                try:
                    datetime.strptime(text_value, "%Y-%m-%d")
                except ValueError as error:
                    raise RequestError("marketDate must use YYYY-MM-DD.", 422) from error
            result[field_id] = redact_text(text_value, 1800 if field_type == "textarea" else 300)
    result["timezone"] = "Asia/Bangkok"
    return result


def _workflow_selected_source(prop_id: str, action_id: str, form: dict) -> dict | None:
    report_id = safe_reference(form.get("sourceReportId"))
    workspace_source_id = safe_reference(form.get("workspaceSourceId"))
    if report_id and workspace_source_id:
        raise RequestError("Select exactly one source: report or workspace source.", 422)
    if workspace_source_id:
        if prop_id != "terminal_workstation" or action_id not in {
            "inspect_ea_source",
            "develop_ea_source",
            "propose_ea_performance_improvements",
        }:
            raise RequestError("Workspace source is not allowed for this dashboard action.", 422)
        row = _resolve_workspace_source(workspace_source_id, form.get("platform"))
        if not row:
            raise RequestError("Workspace source is unavailable or does not match the selected platform.", 422)
        return {
            "reportId": None,
            "artifactId": workspace_source_id,
            "sourceKind": "workspace_source",
            "sourcePropId": "terminal_workstation",
            "type": "workspace_source",
            "status": "ready",
            "title": row.get("label"),
            "summary": "Backend-approved MQL source in the project workspace.",
            "platforms": [row.get("platform")],
            "structuredPayload": {
                "artifactId": workspace_source_id,
                "sourceKind": "workspace_source",
                "platform": row.get("platform"),
                "fileName": row.get("label"),
                "workspaceReference": row.get("storageRef"),
                "byteSize": row.get("byteSize"),
            },
        }
    if not report_id:
        return None
    source = next(
        (item for item in _workflow_transfer_sources(prop_id, action_id=action_id) if item.get("reportId") == report_id),
        None,
    )
    if not source:
        raise RequestError("รายงานต้นทางไม่อยู่ในสายงานที่อุปกรณ์นี้อนุญาต", 422)
    agent_transfer = _agent_transfer_storage(source.get("agentTransfer"))
    if not agent_transfer:
        raise RequestError("Source report transfer record is invalid or incomplete.", 422)
    validation_view = {
        "linkedPropId": source.get("sourcePropId"),
        "type": source.get("type"),
        "status": source.get("status"),
        "platforms": source.get("platforms") if isinstance(source.get("platforms"), list) else [],
    }
    if not _workflow_source_allowed(action_id, validation_view):
        raise RequestError("รายงานต้นทางมีประเภทหรือสถานะที่ยังไม่พร้อมสำหรับงานนี้", 422)
    raw_report = next(
        (
            item
            for item in load_runtime_reports(limit=240)
            if isinstance(item, dict) and safe_reference(item.get("id")) == report_id
        ),
        None,
    )
    payload_source = raw_report if isinstance(raw_report, dict) else source
    source = dict(source)
    source["sourceMissionId"] = agent_transfer["sourceMissionId"]
    source["transferAgentId"] = agent_transfer["transferAgentId"]
    source["sourceOwnerAgentId"] = agent_transfer["sourceOwnerAgentId"]
    source["agentTransfer"] = agent_transfer
    source["structuredPayload"] = sanitize_json_value({
        "reportId": report_id,
        "sourcePropId": source.get("sourcePropId"),
        "sourceMissionId": agent_transfer.get("sourceMissionId"),
        "transferAgentId": agent_transfer.get("transferAgentId"),
        "handoffMissionId": agent_transfer.get("handoffMissionId"),
        "type": source.get("type"),
        "status": source.get("status"),
        "title": redact_text(str(payload_source.get("title") or source.get("title") or ""), 160),
        "summary": redact_text(str(payload_source.get("summary") or source.get("summary") or ""), 2400),
        "findings": payload_source.get("findings") if isinstance(payload_source.get("findings"), list) else [],
        "metrics": payload_source.get("metrics") if isinstance(payload_source.get("metrics"), dict) else {},
        "risks": payload_source.get("risks") if isinstance(payload_source.get("risks"), list) else [],
        "nextActions": payload_source.get("nextActions") if isinstance(payload_source.get("nextActions"), list) else [],
        "evidence": evidence_read_model(payload_source.get("evidence")),
    })
    return source


def _workflow_prompt(action_id: str, form: dict, source: dict | None) -> str:
    source_context = ""
    if source:
        structured_source = source.get("structuredPayload") if isinstance(source.get("structuredPayload"), dict) else source
        source_context = (
            "\nรายงานต้นทางที่ Backend ตรวจสิทธิ์ ประเภท และสถานะแล้ว (ข้อมูลแบบมีโครงสร้าง): "
            + redact_text(json.dumps(structured_source, ensure_ascii=False, sort_keys=True), 6000)
        )
    user_fields = {
        key: value
        for key, value in form.items()
        if key not in {"sourceReportId", "timezone"}
        and value is not None
        and value != ""
        and value != []
    }
    field_context = (
        "\nเงื่อนไขจากผู้ใช้: " + json.dumps(user_fields, ensure_ascii=False, sort_keys=True)
        if user_fields
        else ""
    )
    common = (
        "\nกติกาบังคับ: ห้ามขอหรือแสดง Token, Cookie, รหัสผ่าน, Broker credential หรือ Secret; "
        "รายงานต้องระบุข้อจำกัด แหล่งหลักฐาน และสิ่งที่ยังไม่ได้ทำจริงอย่างตรงไปตรงมา."
    )
    prompts = {
        "discover_trading_systems": (
            "ค้นหาระบบเทรดใหม่จากเว็บไซต์สาธารณะทั่วโลกแบบอ่านอย่างเดียว ใช้ Web Search จริง "
            "และแนบ URL หลักฐานอย่างน้อย 2 แหล่งเมื่อหาได้ เปรียบเทียบกับรายงานเดิมเพื่อหลีกเลี่ยงรายการซ้ำ. "
            "สรุปชื่อระบบ ผู้พัฒนา/ผู้เผยแพร่ ตลาด Symbol Timeframe กติกาเข้า กติกาออก การแก้ไม้/ถัวเฉลี่ย "
            "SL TP เงื่อนไขพิเศษ ผู้ใช้ที่เหมาะสม วันที่เผยแพร่ และ deduplication key. "
            "ห้าม Sign in ห้ามกรอกฟอร์ม ห้ามดาวน์โหลดหรือรันไฟล์ และห้ามคัดลอกข้อมูลไป Google Sheet เพราะยังไม่มี Adapter."
        ),
        "discover_ea_updates": (
            "ค้นหา EA แนวคิดใหม่และงานวิจัยระบบเทรดจากเว็บไซต์สาธารณะแบบอ่านอย่างเดียว "
            "ใช้ Web Search จริงและแนบ URL/วันที่หลักฐาน ตรวจรายการซ้ำกับรายงานเดิม. "
            "แยกข้อมูลที่ยืนยันได้ออกจากคำโฆษณา ห้าม Sign in กรอกฟอร์ม ดาวน์โหลด รันไฟล์ หรือเชื่อม Google Sheet."
        ),
        "deep_research_system": (
            "วิจัยระบบเทรดจากรายงานต้นทางต่อแบบอ่านเว็บไซต์สาธารณะอย่างเดียว ตรวจหลายแหล่ง "
            "ขยายกติกาเข้า/ออก การจัดการไม้ SL/TP ตลาด Timeframe ข้อจำกัด วิธีประยุกต์ และความเสี่ยง. "
            "แยก fact, inference และ unknown ชัดเจน พร้อม URL หลักฐาน ห้าม Sign in กรอกฟอร์ม ดาวน์โหลดหรือรันไฟล์."
        ),
        "build_strategy_code": (
            "สร้างร่าง Source Code ตามรายงานต้นทางและแพลตฟอร์มที่เลือก ภายใน PROJECT_ROOT/workspace เท่านั้น. "
            "ผลลัพธ์นี้เป็น SOURCE-ONLY / UNCOMPILED. ห้ามเปิด MetaEditor, MT4, MT5 หรือ TradingView; "
            "ห้าม Compile, Backtest, Optimize, Deploy หรือส่งคำสั่งเทรด. รายงานไฟล์แบบ project-relative เท่านั้นและระบุขั้นตรวจถัดไป."
        ),
        "review_source_code": (
            "ตรวจ Source Code แบบ STATIC ANALYSIS / SOURCE-ONLY จากผลงานต้นทาง. ห้ามเปิด MetaEditor, MT4, MT5 หรือ TradingView; "
            "ห้าม Compile, Backtest, Optimize, Deploy หรือเทรด. สรุป syntax risk, logic risk, look-ahead/repaint, money-management risk "
            "และรายการแก้ไขโดยห้ามอ้างว่าผ่าน Compile หรือทดสอบแล้ว."
        ),
        "prepare_backtest_plan": (
            "จัดทำ BACKTEST PLAN / ANALYSIS-ONLY สำหรับ Source ที่เลือก. ห้ามเปิดหรือควบคุม MT4/MT5, "
            "ห้าม Compile, Backtest, Optimize, Deploy หรือเทรดจริง. ระบุข้อมูล ช่วงเวลา Symbol Timeframe spread/model "
            "เกณฑ์ตรวจผล และ checklist ที่ Adapter จริงต้องทำภายหลัง."
        ),
        "prepare_optimization_plan": (
            "จัดทำ OPTIMIZATION PLAN / ANALYSIS-ONLY สำหรับ Source ที่เลือก. ห้ามเปิดหรือควบคุม MT4/MT5, "
            "ห้าม Compile, Backtest, Optimize, Deploy หรือเทรดจริง. ระบุ parameter range, train/test split, walk-forward, "
            "เกณฑ์ Drawdown/Profit Factor และวิธีตรวจ overfit สำหรับรอบที่ Adapter จริงจะทำภายหลัง."
        ),
        "prepare_ea_discovery_plan": (
            "จัดทำ EA DISCOVERY PLAN / ANALYSIS-ONLY จากระบบต้นทางและเป้าหมายผู้ใช้. ออกแบบ hypothesis, variants, "
            "objective และ rejection criteria เท่านั้น. ห้ามเปิด MT4/MT5/MetaEditor, ห้าม Compile, Backtest, Optimize, Deploy หรือเทรด. "
            "ห้ามอ้างผลกำไรหรือ Drawdown ที่ยังไม่ได้ทดสอบจริง."
        ),
        "discover_new_indicators": (
            "ค้นหา Indicator ใหม่จากเว็บไซต์สาธารณะแบบอ่านอย่างเดียวด้วย Web Search จริง. "
            "แต่ละรายการต้องมีชื่อ ผู้พัฒนา แพลตฟอร์ม หมวด แนวคิดการคำนวณ การใช้งาน ข้อจำกัด License/Availability "
            "วันที่ตรวจ URL หลักฐาน และ deduplication key ที่อธิบายได้. ห้าม Sign in กรอกฟอร์ม ดาวน์โหลด หรือติดตั้งไฟล์. "
            "Screenshot Adapter ยังไม่มี จึงห้ามอ้างว่าถ่ายภาพหรือเห็นภาพหน้าจอแล้ว. แยกข้อมูลที่ยืนยันได้ ข้อสันนิษฐาน และ unknown ให้ชัดเจน."
        ),
        "analyze_daily_market_news": (
            "ค้นและวิเคราะห์ข่าวตลาด Forex ของวันที่กำหนดจากเว็บไซต์สาธารณะแบบอ่านอย่างเดียว. "
            "ระบุเวลาข่าวพร้อมเขตเวลา สกุลเงินที่เกี่ยวข้อง ระดับผลกระทบ เหตุผล ผลกระทบระยะสั้น/กลาง/ยาว คำเตือน และ URL หลักฐานจริง. "
            "ห้ามอ้างว่าเป็น Live Feed ห้ามแต่งข่าวหรือราคา และหากหาแหล่งยืนยันไม่ได้ให้ระบุ unknown. "
            "ห้าม Sign in กรอกฟอร์ม ดาวน์โหลด หรือส่งข้อมูลไปบริการภายนอก."
        ),
        "build_fx_pair_bias": (
            "ใช้เฉพาะรายงานข่าวต้นทางที่ Backend ตรวจสายงานแล้วเพื่อจัดทำ Bias สำหรับ 28 คู่เงินต่อไปนี้เท่านั้น: "
            + ", ".join(FX_BIAS_PAIRS)
            + ". ทุกคู่ต้องแยก short, medium, long เป็น bullish/bearish/neutral/unknown พร้อม confidence และ URL หลักฐานของแถวนั้น. "
            "ถ้าหลักฐานไม่พอให้ใช้ unknown ห้ามอนุมานเป็นข้อมูลจริง ห้ามแต่งข่าว ราคา หรือสภาวะตลาด. "
            "นี่เป็น Analysis-only ไม่ใช่คำสั่งเทรด และห้ามเรียก MetaTrader หรือส่ง Order."
        ),
        "inspect_ea_source": (
            "ตรวจ Source MQL4/MQL5 ที่ Backend เลือกให้แบบ STATIC ANALYSIS / SOURCE-ONLY ภายใน Project Workspace. "
            "ตรวจ syntax risk, trade logic, look-ahead/repaint, order lifecycle, money management, error handling และ compatibility risk. "
            "ห้ามเปิด MetaEditor/MT4/MT5 ห้าม Compile, Install, Backtest, Optimize, Deploy หรือส่ง Order. "
            "ห้ามอ้างว่าผ่าน Compile/ทดสอบแล้ว และให้รายงานข้อจำกัดกับขั้นตอนตรวจจริงที่ยังต้องทำ."
        ),
        "develop_ea_source": (
            "พัฒนา Source MQL4/MQL5 จาก Source ที่ Backend เลือก ภายใน Project Workspace เท่านั้น. "
            "ผลลัพธ์ต้องเป็น SOURCE-ONLY / UNCOMPILED และอ้างไฟล์แบบ project-relative เท่านั้น. "
            "ห้ามเปิด MetaEditor/MT4/MT5 ห้าม Compile, Install, Backtest, Optimize, Deploy หรือเทรด. "
            "ห้ามเขียน Credential ลง Source และต้องสรุปสิ่งที่แก้ ความเสี่ยง และ checklist สำหรับการ Compile/Test จริงภายหลัง."
        ),
        "propose_ea_performance_improvements": (
            "วิเคราะห์ Source MQL4/MQL5 ที่ Backend เลือกและเสนอสมมติฐานการปรับปรุงตามเป้าหมายกำไร Drawdown และจำนวน Order. "
            "แยก code change hypothesis, parameter hypothesis, validation plan และ rejection criteria. "
            "ห้ามอ้างว่าจะได้กำไรหรือ Drawdown ตามเป้าหมาย ห้ามอ้างผล Backtest/Compile ที่ยังไม่ได้เกิดขึ้น และห้ามเปิด MetaTrader, Compile, Install, Optimize, Deploy หรือเทรด."
        ),
    }
    return redact_text(prompts[action_id] + source_context + field_context + common, 8000)


def save_dashboard_discovery_schedule(form: dict) -> dict:
    settings = load_dashboard_workflow_settings()
    settings["version"] = "dashboard-workflow-settings-v1"
    settings["discoverySchedule"] = {
        "requestedEnabled": bool(form.get("enabled", False)),
        "times": list(form.get("times") or ["09:00"]),
        "timezone": "Asia/Bangkok",
        "savedAt": utc_now(),
    }
    with DASHBOARD_WORKFLOW_SETTINGS_LOCK:
        write_json(
            DASHBOARD_WORKFLOW_SETTINGS_PATH,
            settings,
            keep_backup=DASHBOARD_WORKFLOW_SETTINGS_PATH.exists(),
        )
    return _dashboard_discovery_schedule_read_model(settings)


def _save_dashboard_schedule_preference(settings_key: str, form: dict) -> dict:
    settings = load_dashboard_workflow_settings()
    entry = {
        "requestedEnabled": bool(form.get("enabled", False)),
        "times": list(form.get("times") or []),
        "timezone": "Asia/Bangkok",
        "savedAt": utc_now(),
    }
    minimum_impact = str(form.get("minimumImpact") or "").strip().lower()
    if minimum_impact in {"low", "medium", "high"}:
        entry["minimumImpact"] = minimum_impact
    settings["version"] = "dashboard-workflow-settings-v1"
    settings[settings_key] = entry
    with DASHBOARD_WORKFLOW_SETTINGS_LOCK:
        write_json(
            DASHBOARD_WORKFLOW_SETTINGS_PATH,
            settings,
            keep_backup=DASHBOARD_WORKFLOW_SETTINGS_PATH.exists(),
        )
    defaults = ["09:00"] if settings_key == "indicatorScoutSchedule" else ["07:00", "13:00", "19:00"]
    return _dashboard_saved_schedule_read_model(settings_key, default_times=defaults, settings=settings)


def _save_dashboard_agent_preferences(form: dict) -> dict:
    settings = load_dashboard_workflow_settings()
    current = _dashboard_agent_preferences_read_model(settings)
    values = {
        "language": form.get("language", current["language"]),
        "modelTier": form.get("modelTier", current["modelTier"]),
        "tokenBudget": form.get("tokenBudget", current["tokenBudget"]),
        "timeoutSeconds": form.get("timeoutSeconds", current["timeoutSeconds"]),
        "outputLimitChars": form.get("outputLimitChars", current["outputLimitChars"]),
        "rateReservePercent": form.get("rateReservePercent", current["rateReservePercent"]),
        "savedAt": utc_now(),
    }
    settings["version"] = "dashboard-workflow-settings-v1"
    settings["agentPreferences"] = values
    with DASHBOARD_WORKFLOW_SETTINGS_LOCK:
        write_json(
            DASHBOARD_WORKFLOW_SETTINGS_PATH,
            settings,
            keep_backup=DASHBOARD_WORKFLOW_SETTINGS_PATH.exists(),
        )
    return _dashboard_agent_preferences_read_model(settings)


def _workflow_existing_report(mission: dict) -> dict | None:
    report_ids = mission.get("reportIds") if isinstance(mission.get("reportIds"), list) else []
    safe_ids = {item for item in (safe_reference(value) for value in report_ids) if item}
    if not safe_ids:
        return None
    return next((report for report in load_runtime_reports(limit=240) if report.get("id") in safe_ids), None)


def _complete_local_dashboard_workflow_action(
    prop_id: str,
    action_id: str,
    action: dict,
    form: dict,
    lineage: dict,
    idempotency_key: str,
) -> dict:
    handler = str(action.get("localHandler") or "")
    form_digest = payload_digest(
        "dashboard-workflow-local-form-v1",
        prop_id,
        action_id,
        json.dumps(form, ensure_ascii=False, sort_keys=True),
    )
    prompt = redact_text(
        (
            f"Local dashboard intent: {action_id}; fields={','.join(sorted(form))}; "
            f"formDigest={form_digest}; no external execution."
        ),
        800,
    )
    existing_before = find_mission_by_idempotency(idempotency_key) if idempotency_key else None
    mission = create_mission(
        {
            "title": action.get("labelTh") or action_id,
            "prompt": prompt,
            "agentId": action.get("ownerAgentId"),
            "requester": "human",
            "toolId": action_id,
            "targetId": prop_id,
            "reportType": action.get("reportType") or next(iter(DASHBOARD_WORKFLOW_REPORT_TYPES.get(prop_id, ())), "prop_report"),
            "idempotencyKey": idempotency_key,
        },
        status="completed",
        workflow_context=lineage,
    )
    replay = bool(
        existing_before
        and safe_reference(existing_before.get("id"))
        and safe_reference(existing_before.get("id")) == safe_reference(mission.get("id"))
    )
    if replay:
        report = _workflow_existing_report(mission)
        append_audit({
            "type": "dashboard.workflow_action_replayed",
            "propId": prop_id,
            "actionId": action_id,
            "missionId": mission.get("id"),
            "localHandler": handler,
        })
        return {
            "ok": True,
            "kind": "workflow_local_completed",
            "propId": prop_id,
            "actionId": action_id,
            "mission": mission,
            "report": report,
            "idempotentReplay": True,
            "messageTh": "ใช้ผลการตั้งค่าเดิมจาก Idempotency Key นี้ โดยไม่ทำซ้ำ",
        }

    if handler == "indicator_schedule":
        output = _save_dashboard_schedule_preference("indicatorScoutSchedule", form)
        summary = "บันทึกเวลาค้นหา Indicator แล้ว แต่ Scheduler และ Screenshot Adapter ยังไม่ทำงานอัตโนมัติ"
        findings = ["effective scheduler: disabled", "screenshot adapter: coming_soon"]
    elif handler == "news_bias_schedule":
        output = _save_dashboard_schedule_preference("newsBiasSchedule", form)
        summary = "บันทึกเวลาอัปเดตข่าวและ Bias แล้ว แต่ Scheduler ข่าวยังไม่ทำงานอัตโนมัติ"
        findings = ["effective scheduler: disabled", "live news feed: not_connected"]
    elif handler == "agent_preferences":
        output = _save_dashboard_agent_preferences(form)
        summary = "บันทึกค่าการแสดงผลและงบการทำงานของ Agent แบบจำกัดขอบเขตแล้ว"
        findings = ["credentials accepted: false", "provider model id accepted: false"]
    elif handler == "vps_hq_health":
        output = _safe_vps_hq_health_snapshot()
        summary = "ตรวจสุขภาพ Local Runner และ Mission Worker จากข้อมูลในเครื่องแล้ว; ค่า VPS OS ยังไม่มี Adapter"
        findings = ["local runner observed", "VPS CPU/RAM/disk/uptime: not_observed"]
    else:
        raise RequestError("Unknown local workflow handler.", 500)

    now = utc_now()
    mission["status"] = "completed"
    mission["phase"] = "local_workflow_completed"
    mission["workStatus"] = "completed"
    mission["result"] = summary
    mission["requiresHumanApproval"] = False
    mission["updatedAt"] = now
    mission["completedAt"] = now
    report = create_report({
        "type": action.get("reportType") or "prop_report",
        "title": action.get("labelTh") or action_id,
        "summary": summary,
        "ownerAgentId": action.get("ownerAgentId"),
        "linkedMissionId": mission.get("id"),
        "linkedPropId": prop_id,
        "status": "ready",
        "findings": findings,
        "metrics": {"localResult": output},
        "risks": [],
        "nextActions": [],
        "workflowContext": lineage,
    })
    mission["reportIds"] = [report["id"]]
    replace_mission(mission)
    append_agent_event({
        "kind": "workflow.completed",
        "agentId": action.get("ownerAgentId"),
        "title": action.get("labelTh") or action_id,
        "detail": summary,
        "missionId": mission.get("id"),
        "targetId": prop_id,
    })
    append_audit({
        "type": "dashboard.workflow_local_completed",
        "propId": prop_id,
        "actionId": action_id,
        "missionId": mission.get("id"),
        "reportId": report.get("id"),
        "localHandler": handler,
        "externalExecution": False,
    })
    return {
        "ok": True,
        "kind": "workflow_local_completed",
        "propId": prop_id,
        "actionId": action_id,
        "mission": mission,
        "report": report,
        "localResult": output,
        "idempotentReplay": False,
        "messageTh": summary,
    }


def _dashboard_workflow_lineage(
    prop_id: str,
    action_id: str,
    form: dict,
    source: dict | None,
) -> dict:
    safe_inputs = {
        key: value
        for key, value in form.items()
        if key != "timezone"
    }
    source_lineage = None
    agent_transfer = None
    if isinstance(source, dict):
        agent_transfer = _agent_transfer_storage(source.get("agentTransfer"))
        source_lineage = {
            "reportId": safe_reference(source.get("reportId")),
            "artifactId": safe_reference(source.get("artifactId")),
            "kind": redact_text(str(source.get("sourceKind") or "report"), 40),
            "propId": safe_reference(source.get("sourcePropId")),
            "missionId": safe_reference(source.get("sourceMissionId")),
            "transferAgentId": safe_reference(source.get("transferAgentId")),
            "type": redact_text(str(source.get("type") or ""), 120),
            "status": redact_text(str(source.get("status") or ""), 40),
        }
    return sanitize_json_value({
        "schemaVersion": "dashboard-workflow-lineage-v1",
        "propId": safe_reference(prop_id),
        "actionId": safe_reference(action_id),
        "coordinationMode": DASHBOARD_WORKFLOW_COORDINATION_MODE,
        "source": source_lineage,
        "agentTransfer": agent_transfer,
        "inputs": safe_inputs,
        "inputDigest": payload_digest(
            "dashboard-workflow-input-v1",
            prop_id,
            action_id,
            json.dumps(safe_inputs, ensure_ascii=False, sort_keys=True),
        ),
        "submittedAt": utc_now(),
    })


def deliver_dashboard_report(prop_id: str, payload: object) -> dict:
    """Record an explicit Agent handoff before another dashboard can see a report."""
    request = payload if isinstance(payload, dict) else {}
    unexpected_fields = sorted(set(request) - {"actionId", "sourceReportId", "idempotencyKey"})
    if unexpected_fields:
        raise RequestError("Report transfer contains unsupported fields.", 422)
    if prop_id not in DASHBOARD_WORKFLOW_PROP_IDS or not find_room_prop(prop_id):
        raise RequestError("Unknown destination dashboard id.", 404)
    action_id = safe_reference(request.get("actionId"))
    source_report_id = safe_reference(request.get("sourceReportId"))
    action = DASHBOARD_WORKFLOW_ACTIONS.get(action_id)
    if (
        not action_id
        or not isinstance(action, dict)
        or action.get("propId") != prop_id
        or action_id not in DASHBOARD_WORKFLOW_SOURCE_POLICIES
    ):
        raise RequestError("Destination action does not accept Agent report transfers.", 422)
    if not source_report_id:
        raise RequestError("sourceReportId is required.", 422)
    reports = load_runtime_reports(limit=240)
    missions = load_missions()
    source_report = next(
        (
            report
            for report in reports
            if isinstance(report, dict) and safe_reference(report.get("id")) == source_report_id
        ),
        None,
    )
    if not source_report or not _workflow_source_allowed(action_id, source_report):
        raise RequestError("Source report type, status, or source dashboard is not allowed for this action.", 422)
    binding = _workflow_source_binding(prop_id, action_id, source_report, missions)
    if not binding:
        raise RequestError("Source report is not bound to a completed source Mission.", 422)
    supplied_key = str(request.get("idempotencyKey") or "").strip()
    if supplied_key and (
        contains_potential_secret(supplied_key)
        or not SAFE_IDEMPOTENCY_PATTERN.fullmatch(supplied_key)
    ):
        raise RequestError("Idempotency key must be a short safe identifier.", 422)
    idempotency_key = supplied_key or (
        "agent-transfer-"
        + payload_digest(
            "dashboard-agent-transfer-v1",
            prop_id,
            action_id,
            source_report_id,
            binding["sourceMissionId"],
        )[:32]
    )
    existing = find_mission_by_idempotency(idempotency_key)
    if existing:
        existing_transfer = _agent_transfer_storage(
            existing.get("agentTransfer")
            or ((existing.get("workflowContext") or {}).get("agentTransfer") if isinstance(existing.get("workflowContext"), dict) else None)
        )
        if (
            existing.get("toolId") == "agent_report_transfer"
            and safe_reference(existing.get("targetId")) == prop_id
            and existing_transfer
            and all(existing_transfer.get(key) == value for key, value in binding.items())
        ):
            return {
                "ok": True,
                "kind": "agent_report_transfer_recorded",
                "mission": mission_read_model_item(existing),
                "agentTransfer": existing_transfer,
                "idempotentReplay": True,
            }
        raise RequestError("Idempotency key is already used by a different report transfer.", 409)

    handoff_mission_id = safe_id(None, "mission")
    transfer = _agent_transfer_storage({
        **binding,
        "handoffMissionId": handoff_mission_id,
        "status": "recorded",
    })
    if not transfer:
        raise RequestError("Unable to create a valid Agent report transfer record.", 500)
    source = {
        "reportId": transfer["sourceReportId"],
        "sourceKind": "report",
        "sourcePropId": transfer["sourcePropId"],
        "sourceMissionId": transfer["sourceMissionId"],
        "transferAgentId": transfer["transferAgentId"],
        "sourceOwnerAgentId": transfer["sourceOwnerAgentId"],
        "type": str(source_report.get("type") or "prop_report"),
        "status": str(source_report.get("status") or "ready"),
        "agentTransfer": transfer,
    }
    lineage = _dashboard_workflow_lineage(prop_id, action_id, {}, source)
    mission = create_mission(
        {
            "id": handoff_mission_id,
            "title": f"Agent report transfer: {source_report_id}",
            "prompt": (
                f"Transfer report {source_report_id} from {transfer['sourcePropId']} "
                f"to {prop_id} for action {action_id}. Backend lineage only; no external execution."
            ),
            "agentId": transfer["transferAgentId"],
            "requester": "human",
            "toolId": "agent_report_transfer",
            "targetId": prop_id,
            "reportType": str(source_report.get("type") or "prop_report"),
            "risk": "low",
            "idempotencyKey": idempotency_key,
        },
        status="completed",
        workflow_context=lineage,
    )
    now = utc_now()
    mission["status"] = "completed"
    mission["phase"] = "agent_report_transfer_recorded"
    mission["workStatus"] = "completed"
    mission["result"] = "Agent delivered a validated Mission/Report record to the destination dashboard."
    mission["agentTransfer"] = transfer
    mission["reportIds"] = []
    mission["requiresHumanApproval"] = False
    mission["updatedAt"] = now
    mission["completedAt"] = now
    replace_mission(mission)
    append_agent_event({
        "kind": "workflow.report_transferred",
        "agentId": transfer["transferAgentId"],
        "title": "Agent delivered a report",
        "detail": f"{transfer['sourceReportId']} -> {transfer['targetPropId']}",
        "missionId": mission["id"],
        "targetId": prop_id,
    })
    append_audit({
        "type": "dashboard.agent_report_transfer_recorded",
        "missionId": mission["id"],
        "sourceReportId": transfer["sourceReportId"],
        "sourceMissionId": transfer["sourceMissionId"],
        "sourcePropId": transfer["sourcePropId"],
        "targetPropId": transfer["targetPropId"],
        "transferAgentId": transfer["transferAgentId"],
        "frontendIntentOnly": True,
        "externalExecution": False,
    })
    return {
        "ok": True,
        "kind": "agent_report_transfer_recorded",
        "mission": mission_read_model_item(mission),
        "agentTransfer": transfer,
        "idempotentReplay": False,
    }


def run_dashboard_workflow_action(prop_id: str, payload: object) -> dict:
    request = payload if isinstance(payload, dict) else {}
    action_id = str(request.get("actionId") or "").strip()
    append_audit({
        "type": "dashboard.workflow_action_requested",
        "propId": safe_reference(prop_id),
        "actionId": safe_reference(action_id),
        "frontendIntentOnly": True,
    })
    stage = "request_validation"
    try:
        unexpected_request_fields = sorted(set(request) - {"actionId", "form", "idempotencyKey"})
        if unexpected_request_fields:
            raise RequestError("Workflow request contains unsupported fields.", 422)
        if prop_id not in DASHBOARD_WORKFLOW_PROP_IDS or not find_room_prop(prop_id):
            stage = "unknown_dashboard"
            raise RequestError("Unknown workflow dashboard id.", 404)
        action = DASHBOARD_WORKFLOW_ACTIONS.get(action_id)
        if not isinstance(action, dict) or action.get("propId") != prop_id:
            stage = "action_not_allowed_for_prop"
            raise RequestError("Action is not allowed for this dashboard.", 422)
        stage = "action_contract_policy"
        contract_gate = _workflow_action_contract_gate(prop_id, action_id, action)
        if not contract_gate.get("allowed"):
            raise RequestError("Action is denied by the backend workflow contract.", 403)
        raw_idempotency_key = str(request.get("idempotencyKey") or "").strip()
        if raw_idempotency_key and (
            contains_potential_secret(raw_idempotency_key)
            or not SAFE_IDEMPOTENCY_PATTERN.fullmatch(raw_idempotency_key)
        ):
            stage = "invalid_idempotency_key"
            raise RequestError("Idempotency key must be a short safe identifier.", 422)
        stage = "invalid_form"
        form = _sanitize_dashboard_workflow_form(action, request.get("form", {}))
        stage = "invalid_source"
        source = _workflow_selected_source(prop_id, action_id, form)
        if action.get("sourceRequired") is True and not source:
            stage = "source_required"
            raise RequestError("กรุณาเลือก Source ต้นทางก่อนส่งงาน", 422)
        lineage = _dashboard_workflow_lineage(prop_id, action_id, form, source)
        if action.get("localHandler"):
            stage = "local_handler"
            return _complete_local_dashboard_workflow_action(
                prop_id,
                action_id,
                action,
                form,
                lineage,
                raw_idempotency_key,
            )
        if action_id == "save_discovery_schedule":
            schedule = save_dashboard_discovery_schedule(form)
            append_audit({
                "type": "dashboard.workflow_schedule_saved",
                "propId": prop_id,
                "actionId": action_id,
                "requestedEnabled": schedule.get("requestedEnabled"),
                "effectiveEnabled": False,
                "automaticExternalActions": False,
                "timeCount": len(schedule.get("times") or []),
            })
            return {
                "ok": True,
                "kind": "workflow_schedule_saved",
                "propId": prop_id,
                "actionId": action_id,
                "schedule": schedule,
                "messageTh": "บันทึกเวลาแล้ว แต่ระบบยังไม่รันงานค้นหาภายนอกอัตโนมัติ",
            }
        prompt = _workflow_prompt(action_id, form, source)
        existing = find_mission_by_idempotency(raw_idempotency_key) if raw_idempotency_key else None
        stage = "bridge_dispatch"
        result = run_bridge_task({
            "toolId": action.get("toolId"),
            "agentId": action.get("ownerAgentId"),
            "ownerAgentId": action.get("ownerAgentId"),
            "requester": "human",
            "targetId": prop_id,
            "reportType": action.get("reportType"),
            "prompt": prompt,
            "idempotencyKey": raw_idempotency_key,
        }, trusted_workflow_context=lineage)
    except RequestError as exc:
        append_audit({
            "type": "dashboard.workflow_action_rejected",
            "propId": safe_reference(prop_id),
            "actionId": safe_reference(action_id),
            "reason": stage,
            "httpStatus": exc.status,
        })
        raise
    mission_id = (
        safe_reference((result.get("mission") or {}).get("id"))
        if isinstance(result.get("mission"), dict)
        else None
    )
    idempotent_replay = bool(existing and mission_id and mission_id == safe_reference(existing.get("id")))
    if idempotent_replay:
        append_audit({
            "type": "dashboard.workflow_action_replayed",
            "propId": prop_id,
            "actionId": action_id,
            "missionId": mission_id,
        })
    if not result.get("ok"):
        append_audit({
            "type": "dashboard.workflow_action_rejected",
            "propId": prop_id,
            "actionId": action_id,
            "reason": redact_text(str(result.get("kind") or "bridge_rejected"), 80),
            "httpStatus": result.get("_httpStatus"),
        })
    append_audit({
        "type": "dashboard.workflow_action_dispatched",
        "propId": prop_id,
        "actionId": action_id,
        "toolId": action.get("toolId"),
        "ownerAgentId": action.get("ownerAgentId"),
        "missionId": mission_id,
        "resultKind": redact_text(str(result.get("kind") or "unknown"), 80),
        "ok": bool(result.get("ok", False)),
        "analysisOnly": True,
        "realMetaTraderActionAllowed": False,
    })
    return {
        **result,
        "propId": prop_id,
        "actionId": action_id,
        "idempotentReplay": idempotent_replay,
        "messageTh": (
            "ส่ง Intent ให้ Local Runner แล้ว งานจริงจะมี Mission, Audit และ Report กลับมาที่อุปกรณ์นี้"
            if result.get("ok")
            else redact_text(str(result.get("messageTh") or result.get("message") or "ไม่สามารถสร้าง Mission ได้"), 800)
        ),
    }


AI_TRADE_COUNCIL_PROP_ID = "left_analytics_console"
# The former signal cube is now the News/FX Bias workflow. Keep the legacy
# auto-trading read model on the AI Trade Council surface so old data never
# leaks into the repurposed dashboard.
AUTO_TRADING_STATUS_PROP_ID = AI_TRADE_COUNCIL_PROP_ID
AI_TRADE_COUNCIL_REPORT_TYPES = frozenset({
    "ai_trade_council_report",
    "backtest_report",
    "backtest_optimization_report",
})
AUTO_TRADING_STATUS_REPORT_TYPES = frozenset({"auto_trading_status_report"})
TRADING_CONNECTION_REPORT_TYPES = frozenset({
    "dashboard_connection_report",
    "terminal_discovery_report",
    "terminal_selection_report",
})


def _connection_checklist_item(checklist: dict, item_id: str) -> dict:
    return next(
        (
            item
            for item in (checklist.get("items") or [])
            if isinstance(item, dict) and item.get("id") == item_id
        ),
        {},
    )


def _ai_trade_council_read_model(
    missions: list[dict],
    reports: list[dict],
    connection_checklist: dict,
    prop_id: str = AI_TRADE_COUNCIL_PROP_ID,
) -> dict:
    """Expose only backend-observed trading facts; missing adapters remain unavailable."""
    selection = (
        connection_checklist.get("metatraderSelection")
        if isinstance(connection_checklist.get("metatraderSelection"), dict)
        else {}
    )
    candidates = [
        item
        for item in (selection.get("candidates") or [])
        if isinstance(item, dict)
    ]
    selected_candidate = (
        selection.get("selectedCandidate")
        if isinstance(selection.get("selectedCandidate"), dict)
        else None
    )
    mt4_item = _connection_checklist_item(connection_checklist, "mt4_terminal")
    mt5_item = _connection_checklist_item(connection_checklist, "mt5_terminal")
    trading_state_item = _connection_checklist_item(connection_checklist, "trading_state_adapter")
    ensemble_item = _connection_checklist_item(connection_checklist, "ai_trader_ensemble")
    mission_risk_item = _connection_checklist_item(connection_checklist, "risk_policy")
    live_trading_item = _connection_checklist_item(connection_checklist, "live_trading")

    detected_platforms = [
        platform
        for platform, item in (("mt4", mt4_item), ("mt5", mt5_item))
        if item.get("status") == "detected"
    ]
    process_detected = any(
        item.get("runningState") == "platform_running_detected"
        for item in candidates
    )
    terminal_selected = bool(selected_candidate)

    snapshot = metatrader_snapshot_read_model(prop_id)
    snapshot_adapter = snapshot.get("adapter") if isinstance(snapshot.get("adapter"), dict) else {}
    chart_snapshot = snapshot.get("chartSnapshot") if isinstance(snapshot.get("chartSnapshot"), dict) else {}
    daily_summary = snapshot.get("dailySummary") if isinstance(snapshot.get("dailySummary"), dict) else {}
    analysis_readiness = snapshot.get("analysisReadiness") if isinstance(snapshot.get("analysisReadiness"), dict) else {}
    terminal_adapter_ready = snapshot_adapter.get("ready") is True
    trading_state_available = terminal_adapter_ready
    trade_gateway = mt4_trade_gateway_status_read_model()
    selected_platform = (
        str(selected_candidate.get("platform") or "").strip().lower()
        if selected_candidate
        else ""
    )
    terminal_runtime_detected = bool(
        detected_platforms
        or process_detected
        or terminal_adapter_ready
        or trade_gateway.get("connected") is True
    )
    runtime_platforms = list(detected_platforms)
    if terminal_runtime_detected and selected_platform and selected_platform not in runtime_platforms:
        runtime_platforms.append(selected_platform)
    ensemble_available = (
        terminal_adapter_ready
        and ensemble_item.get("status") == "ready"
        and analysis_readiness.get("available") is True
    )
    live_order_execution_available = (
        trade_gateway.get("liveOrderExecutionAvailable") is True
    )
    # "Enabled" must describe the complete execution path, not merely the two
    # local EA switches.  In particular, an armed Live EA with a missing or
    # mismatched signing key is still blocked and must never be reported ready.
    live_trading_enabled = live_order_execution_available
    trading_kill_switch_available = (
        trade_gateway.get("killSwitchAvailable") is True
    )

    council_missions = [
        item
        for item in missions
        if (
            isinstance(item.get("analysisContext"), dict)
            and item["analysisContext"].get("kind")
            in {"ai_trade_council_parent", "ai_trade_council_vote"}
        )
        or (
            isinstance(item.get("delegation"), dict)
            and item["delegation"].get("mode") == "ai_trade_council_read_only"
        )
    ]
    mission_models = [
        mission_read_model_item(item)
        for item in council_missions[:20]
    ]
    mission_summary = summarize_missions(council_missions)
    # A chart snapshot can refresh every few seconds while a Council round can
    # take minutes. Keep the newest Manager consensus visible with the snapshot
    # it actually analyzed instead of hiding it when the live chart advances.
    latest_council_parent = next(
        (
            item
            for item in council_missions
            if isinstance(item.get("councilDecision"), dict)
            and isinstance(item.get("analysisContext"), dict)
            and item["analysisContext"].get("kind") == "ai_trade_council_parent"
        ),
        None,
    )
    latest_gateway_result = (
        latest_council_parent.get("tradeGateway")
        if latest_council_parent
        and isinstance(latest_council_parent.get("tradeGateway"), dict)
        else None
    )
    if isinstance(latest_gateway_result, dict):
        latest_command = _mt4_trade_gateway_command_read_model(
            latest_gateway_result.get("commandId")
        )
        if latest_command:
            latest_ack = (
                latest_command.get("ack")
                if isinstance(latest_command.get("ack"), dict)
                else {}
            )
            latest_ack_status = str(latest_ack.get("status") or "")
            latest_gateway_result = _ai_trade_council_gateway_result(
                status=(
                    f"ack_{latest_ack_status.lower()}"
                    if latest_ack_status
                    else str(latest_command.get("status") or "waiting_ack")
                ),
                reason_code=(
                    str(latest_ack.get("reasonCode") or "waiting_ea_ack")
                    if latest_ack
                    else "waiting_ea_ack"
                ),
                gateway_status=trade_gateway,
                command=latest_command,
                command_published=True,
            )
    latest_council_consensus = (
        {
            **latest_council_parent["councilDecision"],
            "sourceMissionId": safe_reference(latest_council_parent.get("id")),
            "tradeGateway": latest_gateway_result,
        }
        if latest_council_parent
        else None
    )
    consensus_matches_current_snapshot = bool(
        latest_council_consensus
        and latest_council_consensus.get("snapshotId")
        and chart_snapshot.get("snapshotId")
        and latest_council_consensus.get("snapshotId") == chart_snapshot.get("snapshotId")
    )
    active_statuses = {"queued", "running", "waiting_approval"}
    blocked_statuses = {"blocked", "failed"}
    completed_statuses = {"completed"}
    archived_statuses = {"archived"}

    def mission_items_for(statuses: set[str]) -> list[dict]:
        return [
            item
            for item in mission_models
            if str(item.get("status") or "") in statuses
        ]

    report_models = [report_read_model_item(item) for item in reports[:20]]
    trading_reports = [
        item
        for item in report_models
        if item.get("type") in AI_TRADE_COUNCIL_REPORT_TYPES
    ]
    connection_reports = [
        item
        for item in report_models
        if item.get("type") in TRADING_CONNECTION_REPORT_TYPES
    ]
    other_reports = [
        item
        for item in report_models
        if item.get("type") not in (
            AI_TRADE_COUNCIL_REPORT_TYPES
            | TRADING_CONNECTION_REPORT_TYPES
        )
    ]

    adapter_reason = str(snapshot_adapter.get("reasonCode") or "trading_state_adapter_missing")
    truth_message = (
        "ตรวจพบโปรแกรม MT4/MT5 แบบอ่านอย่างเดียว"
        if terminal_runtime_detected
        else "ยังไม่พบโปรแกรม MT4/MT5 จากการตรวจแบบอ่านอย่างเดียว"
    )
    truth_message += (
        " และบันทึก Terminal เป้าหมายแล้ว"
        if terminal_selected
        else " แต่ยังไม่ได้เลือก Terminal เป้าหมายสำหรับจุดนี้"
    )
    truth_message += (
        (
            " Adapter Read-only ส่งข้อมูลกราฟและสรุปประจำวันเข้ามาแล้ว "
            "พร้อมให้ Agent วิเคราะห์เมื่อผู้ใช้สั่ง"
        )
        if terminal_adapter_ready
        else (
            " ยังไม่ได้รับ Snapshot ที่สดใหม่จาก Adapter Read-only "
            "ระบบวิเคราะห์สาม Agent และการส่งคำสั่งซื้อขายยังปิดใช้งาน"
        )
    )
    if trade_gateway.get("connected") is True:
        gateway_mode = str(trade_gateway.get("mode") or "unknown")
        gateway_reason = str(trade_gateway.get("executionGuardReason") or "")
        if trade_gateway.get("executionGuardReady") is True:
            truth_message += (
                f" Trade Gateway EA เชื่อมแล้วในโหมด {gateway_mode} และพร้อมรับคำสั่งตาม Guard; "
                "Fixed Lot อ่านจาก Inputs ของ EA เท่านั้น"
            )
        elif gateway_reason == "QUOTE_NOT_OBSERVED":
            truth_message += (
                f" Trade Gateway EA เชื่อมแล้วในโหมด {gateway_mode} และกำลังรอ Quote สดจาก Broker; "
                "Fixed Lot อ่านจาก Inputs ของ EA เท่านั้น"
            )
        else:
            truth_message += (
                f" Trade Gateway EA เชื่อมแล้วในโหมด {gateway_mode} แต่ Execution Guard ยังไม่พร้อม"
                + (f" ({gateway_reason})" if gateway_reason else "")
                + "; Fixed Lot อ่านจาก Inputs ของ EA เท่านั้น"
            )
    else:
        truth_message += (
            " Trade Gateway EA ยังไม่เชื่อม จึงวิเคราะห์และสร้างแผนได้ "
            "แต่ยังไม่ส่งคำสั่งซื้อขาย"
        )

    return {
        "schemaVersion": "ai-trade-council-v2",
        "tabOrder": ["dailySummary", "liveAnalysis", "decisionPipeline", "history"],
        "autoAnalysis": ai_trade_council_automation_read_model(),
        "tradeGateway": trade_gateway,
        "runtimeTruth": {
            "scope": "read_only_snapshot" if terminal_adapter_ready else "terminal_detection_only",
            "terminalDetection": {
                "available": True,
                "detected": terminal_runtime_detected,
                "platforms": runtime_platforms,
                "processDetected": process_detected,
                "selected": terminal_selected,
                "selectedPlatform": (
                    selected_platform or None
                ),
                "adapterReady": terminal_adapter_ready,
                "checkedAt": connection_checklist.get("checkedAt"),
            },
            "tradingStateAdapter": {
                "available": trading_state_available,
                "status": str(snapshot_adapter.get("status") or trading_state_item.get("status") or "awaiting_snapshot"),
                "adapterStatus": "implemented_read_only_snapshot",
                "mode": "read_only",
                "reasonCode": adapter_reason,
            },
            "ensemble": {
                "available": ensemble_available,
                "status": str(ensemble_item.get("status") or "waiting_snapshot"),
            },
            "missionRiskGuardAvailable": mission_risk_item.get("status") == "ready",
            "tradingKillSwitchAvailable": trading_kill_switch_available,
            "liveTradingEnabled": live_trading_enabled,
            "liveTradingStatus": (
                "ready"
                if live_order_execution_available
                else str(
                    trade_gateway.get("reasonCode")
                    or live_trading_item.get("status")
                    or "disabled"
                )
            ),
            "liveOrderExecutionAvailable": live_order_execution_available,
            "demoOrderExecutionAvailable": (
                trade_gateway.get("demoOrderExecutionAvailable") is True
            ),
            "shadowValidationAvailable": (
                trade_gateway.get("shadowValidationAvailable") is True
            ),
            "tradeGateway": trade_gateway,
            "tradingDataObservedAt": chart_snapshot.get("observedAt"),
            "messageTh": truth_message,
        },
        "liveAnalysis": {
            "available": bool(chart_snapshot.get("available")),
            "status": str(chart_snapshot.get("status") or "awaiting_snapshot"),
            "dataScope": "read_only_snapshot" if chart_snapshot.get("available") else "terminal_detection_only",
            "observedAt": chart_snapshot.get("observedAt"),
            "market": {
                "available": bool(chart_snapshot.get("available")),
                "symbol": chart_snapshot.get("symbol"),
                "timeframe": chart_snapshot.get("timeframe"),
                "price": chart_snapshot.get("bid"),
                "bid": chart_snapshot.get("bid"),
                "ask": chart_snapshot.get("ask"),
                "spreadPoints": chart_snapshot.get("spreadPoints"),
                "reasonCode": adapter_reason,
            },
            "eaHealth": {
                "available": trade_gateway.get("connected") is True,
                "status": trade_gateway.get("status"),
                "mode": trade_gateway.get("mode"),
                "reasonCode": trade_gateway.get("reasonCode"),
            },
            "positionsSummary": {
                "available": bool(daily_summary.get("available")),
                "count": daily_summary.get("openPositions"),
                "items": None,
                "reasonCode": adapter_reason,
            },
            "latestSignal": {
                "available": False,
                "direction": None,
                "confidence": None,
                "generatedAt": None,
                "reasonCode": adapter_reason,
            },
            "consensus": {
                "available": bool(latest_council_consensus),
                "sourceMissionId": (
                    latest_council_consensus.get("sourceMissionId")
                    if latest_council_consensus
                    else None
                ),
                "snapshotId": (
                    latest_council_consensus.get("snapshotId")
                    if latest_council_consensus
                    else None
                ),
                "currentSnapshotId": chart_snapshot.get("snapshotId"),
                "matchesCurrentSnapshot": consensus_matches_current_snapshot,
                "decision": (
                    latest_council_consensus.get("decision")
                    if latest_council_consensus
                    else None
                ),
                "confidence": (
                    latest_council_consensus.get("averageConfidence")
                    if latest_council_consensus
                    else None
                ),
                "votes": (
                    latest_council_consensus.get("votes")
                    if latest_council_consensus
                    else None
                ),
                "unanimous": bool(
                    latest_council_consensus
                    and latest_council_consensus.get("unanimous")
                ),
                "consensusReached": bool(
                    latest_council_consensus
                    and latest_council_consensus.get("consensusReached")
                ),
                "agreementMet": bool(
                    latest_council_consensus
                    and latest_council_consensus.get("consensusReached")
                ),
                "directionalAgreementMet": bool(
                    latest_council_consensus
                    and latest_council_consensus.get("consensusReached")
                ),
                "selectedDirection": (
                    latest_council_consensus.get("selectedDirection")
                    if latest_council_consensus
                    else None
                ),
                "requiredVotes": (
                    latest_council_consensus.get("requiredVotes")
                    if latest_council_consensus
                    else _configured_ai_trade_council_required_votes()
                ),
                "directionalVoteCount": (
                    latest_council_consensus.get("directionalVoteCount")
                    if latest_council_consensus
                    else 0
                ),
                "directionConflict": bool(
                    latest_council_consensus
                    and latest_council_consensus.get("directionConflict")
                ),
                "conflictingDirections": bool(
                    latest_council_consensus
                    and latest_council_consensus.get("directionConflict")
                ),
                "directionCounts": (
                    latest_council_consensus.get("directionCounts")
                    if latest_council_consensus
                    else {"BUY": 0, "HOLD": 0, "SELL": 0, "NO_DATA": 0}
                ),
                "voteCount": (
                    latest_council_consensus.get("voteCount")
                    if latest_council_consensus
                    else 0
                ),
                "riskGuard": (
                    latest_council_consensus.get("riskGuard")
                    if latest_council_consensus
                    else {
                        "agentId": "risk_guard",
                        "voting": False,
                        "status": "waiting_votes",
                        "terminalActions": False,
                    }
                ),
                "tradePlan": (
                    latest_council_consensus.get("tradePlan")
                    if latest_council_consensus
                    else {
                        "available": False,
                        "direction": None,
                        "stopLossPrice": None,
                        "takeProfitPrice": None,
                        "lotPolicy": "ea_fixed_lot_only",
                        "aiLotAllowed": False,
                    }
                ),
                "reasonCode": (
                    "ready"
                    if latest_council_consensus
                    else str(ensemble_item.get("status") or "waiting_snapshot")
                ),
            },
        },
        "dailySummary": daily_summary,
        "chartSnapshot": chart_snapshot,
        "analysisReadiness": {
            **analysis_readiness,
            "available": ensemble_available,
            "status": (
                "ready"
                if ensemble_available
                else str(ensemble_item.get("status") or analysis_readiness.get("status") or "waiting_snapshot")
            ),
        },
        "decisionPipeline": {
            "available": True,
            "snapshot": {
                "available": bool(
                    (latest_council_consensus or {}).get("snapshotId")
                    or chart_snapshot.get("available")
                ),
                "id": (
                    (latest_council_consensus or {}).get("snapshotId")
                    or chart_snapshot.get("snapshotId")
                ),
                "observedAt": (
                    chart_snapshot.get("observedAt")
                    if not latest_council_consensus
                    or consensus_matches_current_snapshot
                    else None
                ),
                "currentId": chart_snapshot.get("snapshotId"),
                "matchesCurrent": consensus_matches_current_snapshot,
            },
            "consensus": latest_council_consensus or {
                "schemaVersion": "ai-trade-council-consensus-v4",
                "snapshotId": chart_snapshot.get("snapshotId"),
                "ready": False,
                "decision": "NO_DATA",
                "unanimous": False,
                "consensusReached": False,
                "agreementMet": False,
                "directionalAgreementMet": False,
                "selectedDirection": None,
                "requiredVotes": _configured_ai_trade_council_required_votes(),
                "directionalVoteCount": 0,
                "directionConflict": False,
                "conflictingDirections": False,
                "directionCounts": {"BUY": 0, "HOLD": 0, "SELL": 0, "NO_DATA": 0},
                "voteCount": 0,
                "votes": [],
                "averageConfidence": 0,
                "tradePlan": {
                    "available": False,
                    "direction": None,
                    "stopLossPrice": None,
                    "takeProfitPrice": None,
                    "priceAggregation": "unavailable",
                    "protectivePriceOwnerRole": None,
                    "rewardRiskRatio": None,
                    "protectivePlanSource": "unavailable",
                    "protectivePlanReasonCode": "consensus_not_trade_eligible",
                    "protectivePlanPolicyVersion": (
                        AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION
                    ),
                    "protectivePlanFallbackUsed": False,
                    "protectivePlanProvenance": None,
                    "lotPolicy": "ea_fixed_lot_only",
                    "aiLotAllowed": False,
                },
                "riskGuard": {
                    "agentId": "risk_guard",
                    "voting": False,
                    "status": "waiting_votes",
                    "terminalActions": False,
                },
                "terminalActions": False,
            },
            "status": (
                "active"
                if mission_summary.get("active")
                else (
                    "needs_attention"
                    if mission_summary.get("attentionRequired")
                    else "idle"
                )
            ),
            "summary": mission_summary,
            "items": mission_models,
            "activeItems": mission_items_for(active_statuses),
            "completedItems": mission_items_for(completed_statuses),
            "blockedItems": mission_items_for(blocked_statuses),
            "archivedItems": mission_items_for(archived_statuses),
            "hasMore": len(council_missions) > len(mission_models),
            "sourceScope": "exact_analytics_console_mission_routing",
        },
        "history": {
            "available": True,
            "summary": summarize_reports(reports),
            "items": report_models,
            "tradingReports": trading_reports,
            "connectionReports": connection_reports,
            "otherReports": other_reports,
            "hasMore": len(reports) > len(report_models),
            "sourceScope": "exact_analytics_console_linked_reports_only",
            "memoryIncluded": False,
            "meetingsIncluded": False,
        },
    }


def _auto_trading_status_read_model(
    reports: list[dict],
    connection_checklist: dict,
) -> dict:
    """Monitor the canonical Council runtime without copying its decisions."""
    unavailable_runtime = _ai_trade_council_read_model(
        [],
        [],
        connection_checklist,
        prop_id=AI_TRADE_COUNCIL_PROP_ID,
    )
    runtime_truth = {
        key: value
        for key, value in unavailable_runtime["runtimeTruth"].items()
        if key != "ensemble"
    }
    runtime_truth["messageTh"] = (
        "จุดนี้แสดงสถานะโปรแกรมและความพร้อมของ Auto Trading แบบอ่านอย่างเดียว "
        "การตรวจพบ MT4/MT5 ไม่ได้หมายความว่าเชื่อมข้อมูลเทรดหรือส่งคำสั่งซื้อขายได้"
    )
    status = dict(unavailable_runtime["liveAnalysis"])
    status.pop("consensus", None)
    report_models = [report_read_model_item(item) for item in reports[:20]]
    status_reports = [
        item
        for item in report_models
        if item.get("type") in AUTO_TRADING_STATUS_REPORT_TYPES
    ]
    connection_reports = [
        item
        for item in report_models
        if item.get("type") in TRADING_CONNECTION_REPORT_TYPES
    ]
    other_reports = [
        item
        for item in report_models
        if item.get("type") not in (
            AUTO_TRADING_STATUS_REPORT_TYPES
            | TRADING_CONNECTION_REPORT_TYPES
        )
    ]
    return {
        "schemaVersion": "auto-trading-status-dashboard-v1",
        "runtimeTruth": runtime_truth,
        "status": status,
        "history": {
            "available": True,
            "summary": summarize_reports(reports),
            "items": report_models,
            "statusReports": status_reports,
            "connectionReports": connection_reports,
            "otherReports": other_reports,
            "hasMore": len(reports) > len(report_models),
            "sourceScope": "exact_signal_cube_linked_reports_only",
            "memoryIncluded": False,
            "meetingsIncluded": False,
        },
    }


def _workflow_linked_meetings(
    prop_id: str,
    meetings: list[dict],
    mission_ids: set[str],
) -> list[dict]:
    """Fail closed: participant names and keywords never route workflow meetings."""
    if prop_id not in DASHBOARD_WORKFLOW_PROP_IDS:
        return []
    return [
        meeting
        for meeting in meetings
        if isinstance(meeting, dict)
        and (
            safe_reference(meeting.get("linkedPropId")) == prop_id
            or safe_reference(meeting.get("linkedMissionId")) in mission_ids
        )
    ]


def _workflow_linked_memory_items(
    prop_id: str,
    items: list[dict],
    mission_ids: set[str],
) -> list[dict]:
    """Fail closed when a memory card has no explicit prop or Mission linkage."""
    if prop_id not in DASHBOARD_WORKFLOW_PROP_IDS:
        return []
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        linked_prop_ids = {
            linked_prop_id
            for linked_prop_id in (
                safe_reference(value)
                for value in (
                    item.get("linkedPropIds")
                    if isinstance(item.get("linkedPropIds"), list)
                    else []
                )
            )
            if linked_prop_id
        }
        linked_mission_id = safe_reference(item.get("linkedMissionId"))
        if prop_id in linked_prop_ids or linked_mission_id in mission_ids:
            rows.append(item)
    return rows


def prop_report(prop_id: str) -> dict:
    prop = find_room_prop(prop_id) or {"id": prop_id, "label": prop_id, "summary": "No room contract entry found."}
    property_role = find_property_role(prop_id)
    label = str(prop.get("label") or prop_id)
    keywords = routing_keywords_for_prop(prop_id)
    target_text = " ".join([prop_id, label, str(property_role.get("functionName") or ""), *keywords]).lower()
    all_missions = load_missions()
    workflow_legacy_mission_count = 0
    workflow_legacy_report_count = 0
    is_global_mission_view = prop_id == MISSION_STRATEGY_TABLE_PROP_ID
    if is_global_mission_view:
        # Mission Strategy Table is the deliberate global exception: it shows
        # every root mission and specialist subtask, regardless of target prop.
        routed_missions = all_missions
        related_missions = [mission_read_model_item(mission) for mission in routed_missions]
    elif prop_id in DASHBOARD_WORKFLOW_PROP_IDS:
        # Workflow devices never infer ownership from titles or keyword matches.
        routed_missions = [
            mission for mission in all_missions
            if prop_id == mission.get("targetId")
            or prop_id == mission.get("linkedPropId")
        ]
        relevant_missions = [
            mission
            for mission in routed_missions
            if _workflow_record_matches_prop(mission, prop_id)
        ]
        workflow_legacy_mission_count = max(0, len(routed_missions) - len(relevant_missions))
        routed_missions = relevant_missions[:8]
        related_missions = [mission_read_model_item(mission) for mission in routed_missions]
    else:
        routed_missions = [
            mission for mission in all_missions
            if prop_id == mission.get("targetId")
            or prop_id == mission.get("linkedPropId")
            or (not mission.get("targetId") and any(keyword_matches(f"{mission.get('title', '')} {mission.get('detail', '')}".lower(), token) for token in keywords))
        ]
        routed_missions = routed_missions[:8]
        related_missions = [mission_read_model_item(mission) for mission in routed_missions]
    routed_mission_ids_for_events = {
        safe_reference(mission.get("id")) for mission in routed_missions
        if safe_reference(mission.get("id"))
    }
    related_events = [
        event for event in load_agent_events(limit=120)
        if (
            (
                event.get("missionId") in routed_mission_ids_for_events
                or event.get("targetId") == prop_id
            )
            if prop_id in DASHBOARD_WORKFLOW_PROP_IDS
            else (
                prop_id == event.get("targetId")
                or prop_id in str(event.get("detail") or "").lower()
                or any(keyword_matches(f"{event.get('title', '')} {event.get('detail', '')}".lower(), token) for token in keywords)
            )
        )
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
        candidate_reports = [report for report in all_reports if prop_id == report.get("linkedPropId")]
        if prop_id in DASHBOARD_WORKFLOW_PROP_IDS:
            relevant_reports = [
                report
                for report in candidate_reports
                if _workflow_record_matches_prop(report, prop_id)
            ]
            workflow_legacy_report_count = max(0, len(candidate_reports) - len(relevant_reports))
            candidate_reports = relevant_reports
        candidate_reports = candidate_reports[:8]

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
    elif prop_id in DASHBOARD_WORKFLOW_PROP_IDS:
        related_meetings = _workflow_linked_meetings(
            prop_id,
            meetings,
            related_mission_ids,
        )[:8]
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
    if prop_id in DASHBOARD_WORKFLOW_PROP_IDS:
        memory_index = load_memory_index()
        raw_memory_items = (
            memory_index.get("items")
            if isinstance(memory_index.get("items"), list)
            else []
        )
        memory_items = [
            memory_read_model_item(item)
            for item in _workflow_linked_memory_items(
                prop_id,
                raw_memory_items,
                related_mission_ids,
            )[:6]
        ]
    else:
        memory_items = [
            memory_read_model_item(item)
            for item in search_memory_items(target_text, limit=6)
        ]
    live_bridge_status = bridge_status()
    registry = capability_registry(live_bridge_status)
    dashboard_profile = find_dashboard_connection_profile(prop_id)
    filtered_capabilities = [
        item for item in registry.get("capabilities", [])
        if prop_id in (item.get("linkedPropIds") or [])
    ]
    connection_source_prop_id = (
        AI_TRADE_COUNCIL_PROP_ID
        if prop_id == AUTO_TRADING_STATUS_PROP_ID
        else prop_id
    )
    connection_source_profile = find_dashboard_connection_profile(
        connection_source_prop_id
    )
    connection_checklist = (
        dashboard_connection_checklist(
            connection_source_prop_id,
            bridge=live_bridge_status,
        )
        if connection_source_profile
        else {}
    )
    response = {
        "prop": prop,
        "propertyRole": property_role,
        "missions": related_missions,
        "events": related_events,
        "reports": related_reports,
        "workflowLegacy": {
            "missionCount": workflow_legacy_mission_count,
            "reportCount": workflow_legacy_report_count,
            "detailsExposed": False,
        } if prop_id in DASHBOARD_WORKFLOW_PROP_IDS else None,
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
        "connectionChecklist": connection_checklist,
        "connectionSourcePropId": connection_source_prop_id,
        "updatedAt": utc_now(),
    }
    if prop_id in METATRADER_TARGET_PROP_IDS:
        response["metatraderReadOnly"] = metatrader_snapshot_read_model(
            connection_source_prop_id
        )
    if prop_id in DASHBOARD_WORKFLOW_PROP_IDS:
        response["workflowDashboard"] = workflow_dashboard_read_model(
            prop_id,
            reports=all_reports,
            bridge=live_bridge_status,
        )
    if prop_id == AI_TRADE_COUNCIL_PROP_ID:
        council_missions = [
            mission
            for mission in all_missions
            if prop_id == mission.get("targetId")
            or prop_id == mission.get("linkedPropId")
        ]
        council_reports = [
            report
            for report in all_reports
            if prop_id == report.get("linkedPropId")
        ]
        response["aiTradeCouncil"] = _ai_trade_council_read_model(
            council_missions,
            council_reports,
            connection_checklist,
        )
        response["autoTradingStatus"] = _auto_trading_status_read_model(
            council_reports,
            connection_checklist,
        )
    elif prop_id == AUTO_TRADING_STATUS_PROP_ID:
        status_reports = [
            report
            for report in all_reports
            if prop_id == report.get("linkedPropId")
        ]
        response["autoTradingStatus"] = _auto_trading_status_read_model(
            status_reports,
            connection_checklist,
        )
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


def ai_trade_council_status_read_model() -> dict:
    """Reuse the canonical prop report assembly for the standalone status API."""
    report = prop_report(AI_TRADE_COUNCIL_PROP_ID)
    council = report.get("aiTradeCouncil") if isinstance(report, dict) else None
    if not isinstance(council, dict):
        raise RuntimeError("AI Trade Council read model is unavailable.")
    return council


def _ai_trade_council_chat_unavailable(agent_id: str, reason_code: str) -> dict:
    role_id = AI_TRADE_COUNCIL_AGENT_ROLES.get(agent_id)
    return {
        "schemaVersion": "agent-chat-council-context-v1",
        "status": "unavailable",
        "reasonCode": reason_code,
        "agentId": agent_id,
        "roleId": role_id,
        "snapshotId": None,
        "snapshotIdPrefix": None,
        "symbol": None,
        "timeframe": None,
        "observedAt": None,
        "direction": None,
        "confidence": None,
        "stopLossPrice": None,
        "takeProfitPrice": None,
        "reasons": [],
        "evidence": [],
        "freshness": "unknown",
        "ageSeconds": None,
        "sourceStatus": None,
        "sourceUpdatedAt": None,
    }


def _ai_trade_council_chat_timestamp(value: object) -> tuple[str | None, datetime | None]:
    parsed = None
    if isinstance(value, (int, float)) or (
        isinstance(value, str) and re.fullmatch(r"\d{9,12}", value.strip())
    ):
        try:
            parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OSError, OverflowError, TypeError, ValueError):
            parsed = None
    if parsed is None:
        parsed = parse_iso(str(value or ""))
    if (
        parsed is None
        or parsed < datetime(2000, 1, 1, tzinfo=timezone.utc)
        or parsed > datetime.now(timezone.utc) + timedelta(days=2)
    ):
        return None, None
    normalized = parsed.astimezone(timezone.utc)
    return normalized.isoformat().replace("+00:00", "Z"), normalized


def _ai_trade_council_public_url(value: object) -> str | None:
    raw_url = str(value or "").strip()
    if (
        not raw_url
        or len(raw_url) > 1000
        or contains_potential_secret(raw_url)
    ):
        return None
    try:
        parsed = urlparse(raw_url)
    except ValueError:
        return None
    hostname = str(parsed.hostname or "").strip().lower().rstrip(".")
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not hostname
        or parsed.username
        or parsed.password
        or hostname == "localhost"
        or hostname.endswith((".localhost", ".local", ".internal"))
        or any(is_sensitive_field_name(key) for key in parse_qs(parsed.query))
    ):
        return None
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        return None
    return redact_text(raw_url, 1000)


def _ai_trade_council_chat_safe_text(value: object, limit: int) -> str | None:
    text = str(value or "").strip()
    if not text or json_contains_potential_secret(text):
        return None
    if re.search(
        r"(?i)(?:"
        r"\b(?:account|broker|ticket|token|password|passwd|cookie|secret|"
        r"terminal\s*path|process\s*id|pid)\b|"
        r"[A-Z]:\\|\\\\|/(?:Users|home|root|var|etc|tmp|opt|srv)/"
        r")",
        text,
    ):
        return None
    cleaned = redact_text(text, limit).strip()
    return cleaned if cleaned and "[REDACTED_" not in cleaned else None


def _ai_trade_council_chat_vote(value: object, agent_id: str) -> dict | None:
    vote = value if isinstance(value, dict) else None
    role_id = AI_TRADE_COUNCIL_AGENT_ROLES.get(agent_id)
    if not vote or not role_id:
        return None
    snapshot_id = str(vote.get("snapshotId") or "")
    direction = str(vote.get("decision") or "").upper()
    confidence = _safe_snapshot_number(vote.get("confidence"), minimum=0, maximum=100)
    if (
        vote.get("schemaVersion") != "ai-trade-council-vote-v2"
        or vote.get("readOnly") is not True
        or not re.fullmatch(r"[0-9a-f]{64}", snapshot_id)
        or vote.get("agentId") != agent_id
        or vote.get("roleId") != role_id
        or direction not in {"BUY", "HOLD", "SELL", "NO_DATA"}
        or confidence is None
    ):
        return None
    stop_loss = _safe_snapshot_number(
        vote.get("stopLossPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    take_profit = _safe_snapshot_number(
        vote.get("takeProfitPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    if direction in {"BUY", "SELL"}:
        if stop_loss is None or take_profit is None:
            return None
    elif vote.get("stopLossPrice") is not None or vote.get("takeProfitPrice") is not None:
        return None
    reasons = []
    for item in (
        vote.get("observations")
        if isinstance(vote.get("observations"), list)
        else []
    ):
        safe_reason = _ai_trade_council_chat_safe_text(item, 600)
        if safe_reason:
            reasons.append(safe_reason)
        if len(reasons) == 3:
            break
    evidence = []
    for item in (
        vote.get("evidence")
        if isinstance(vote.get("evidence"), list)
        else []
    ):
        if not isinstance(item, dict):
            continue
        source_url = _ai_trade_council_public_url(
            item.get("sourceUrl") or item.get("url")
        )
        label = _ai_trade_council_chat_safe_text(item.get("label"), 300)
        if not source_url or not label:
            continue
        evidence_observed_at, _ = _ai_trade_council_chat_timestamp(
            item.get("observedAt")
        )
        evidence.append({
            "label": label,
            "observedAt": evidence_observed_at,
            "sourceUrl": source_url,
        })
        if len(evidence) == 3:
            break
    return {
        "snapshotId": snapshot_id,
        "agentId": agent_id,
        "roleId": role_id,
        "direction": direction,
        "confidence": confidence,
        "stopLossPrice": stop_loss if direction in {"BUY", "SELL"} else None,
        "takeProfitPrice": take_profit if direction in {"BUY", "SELL"} else None,
        "reasons": reasons,
        "evidence": evidence,
    }


def _ai_trade_council_chat_source_context(
    source: dict,
    missions_by_id: dict[str, dict],
) -> tuple[str | None, str | None, str | None, datetime | None]:
    context = (
        source.get("analysisContext")
        if isinstance(source.get("analysisContext"), dict)
        else {}
    )
    parent_id = safe_reference(source.get("parentMissionId"))
    parent = missions_by_id.get(parent_id) if parent_id else None
    parent_context = (
        parent.get("analysisContext")
        if isinstance(parent, dict) and isinstance(parent.get("analysisContext"), dict)
        else {}
    )
    closed_bar = (
        context.get("closedBarIdentity")
        if isinstance(context.get("closedBarIdentity"), dict)
        else parent_context.get("closedBarIdentity")
        if isinstance(parent_context.get("closedBarIdentity"), dict)
        else {}
    )
    symbol = _safe_snapshot_symbol(closed_bar.get("symbol"))
    timeframe = _safe_snapshot_timeframe(closed_bar.get("timeframe"))
    observed_at, observed_time = _ai_trade_council_chat_timestamp(
        closed_bar.get("closedBarTime")
    )
    if observed_at is None:
        observed_at, observed_time = _ai_trade_council_chat_timestamp(
            source.get("completedAt")
            or source.get("updatedAt")
            or source.get("createdAt")
        )
    return symbol, timeframe, observed_at, observed_time


def ai_trade_council_agent_chat_context(agent_id: str) -> dict | None:
    """Build one bounded, agent-isolated explanation context from durable Council data."""
    if agent_id not in AI_TRADE_COUNCIL_AGENT_ROLES:
        return None
    unavailable = _ai_trade_council_chat_unavailable(
        agent_id,
        "latest_vote_unavailable",
    )
    try:
        missions = load_missions()
        reports = load_runtime_reports(limit=240)
    except (DataIntegrityError, OSError):
        return _ai_trade_council_chat_unavailable(
            agent_id,
            "council_store_unavailable",
        )
    missions_by_id = {
        mission_id: item
        for item in missions
        if isinstance(item, dict)
        and (mission_id := safe_reference(item.get("id")))
    }
    candidates: list[tuple[datetime, dict, dict, str]] = []
    for mission in missions:
        if not isinstance(mission, dict) or mission.get("owner") != agent_id:
            continue
        context = (
            mission.get("analysisContext")
            if isinstance(mission.get("analysisContext"), dict)
            else {}
        )
        source_status = str(mission.get("status") or "")
        archived_success = (
            source_status == "archived"
            and (
                mission.get("archivedSuccessful") is True
                or mission.get("archivedFromStatus") == "completed"
            )
        )
        if (
            context.get("kind") != "ai_trade_council_vote"
            or (source_status != "completed" and not archived_success)
        ):
            continue
        vote = _ai_trade_council_chat_vote(mission.get("councilVote"), agent_id)
        source_updated_at, source_time = _ai_trade_council_chat_timestamp(
            mission.get("completedAt")
            or mission.get("updatedAt")
            or mission.get("createdAt")
        )
        if vote and source_updated_at and source_time:
            candidates.append((source_time, vote, mission, source_status))
    for report in reports:
        if (
            not isinstance(report, dict)
            or report.get("type") != "ai_trade_council_vote"
            or report.get("ownerAgentId") != agent_id
        ):
            continue
        linked_mission_id = safe_reference(report.get("linkedMissionId"))
        linked_mission = (
            missions_by_id.get(linked_mission_id)
            if linked_mission_id
            else None
        )
        parsed_summary = _extract_json_object(report.get("summary"))
        vote = _ai_trade_council_chat_vote(parsed_summary, agent_id)
        source_updated_at, source_time = _ai_trade_council_chat_timestamp(
            report.get("updatedAt") or report.get("createdAt")
        )
        if vote and isinstance(linked_mission, dict) and source_updated_at and source_time:
            candidates.append((
                source_time,
                vote,
                linked_mission,
                str(report.get("status") or "ready"),
            ))
    if not candidates:
        return unavailable
    source_time, vote, source, source_status = max(
        candidates,
        key=lambda item: item[0],
    )
    symbol, timeframe, observed_at, observed_time = (
        _ai_trade_council_chat_source_context(source, missions_by_id)
    )
    source_updated_at, _ = _ai_trade_council_chat_timestamp(
        source.get("completedAt")
        or source.get("updatedAt")
        or source.get("createdAt")
    )
    if not symbol or not timeframe or not observed_at or observed_time is None:
        return _ai_trade_council_chat_unavailable(
            agent_id,
            "latest_vote_context_incomplete",
        )
    interval_seconds = {
        "M5": 300,
        "M15": 900,
        "M30": 1800,
        "H1": 3600,
        "H4": 14400,
        "D1": 86400,
        "W1": 604800,
        "MN1": 2592000,
    }.get(timeframe)
    age_seconds = max(
        0,
        int((datetime.now(timezone.utc) - observed_time).total_seconds()),
    )
    freshness = (
        "fresh"
        if interval_seconds is not None and age_seconds <= max(600, interval_seconds * 3)
        else "stale"
    )
    context = {
        "schemaVersion": "agent-chat-council-context-v1",
        "status": "available",
        "reasonCode": "latest_vote_available",
        "agentId": agent_id,
        "roleId": vote["roleId"],
        "snapshotId": vote["snapshotId"],
        "snapshotIdPrefix": vote["snapshotId"][:12],
        "symbol": symbol,
        "timeframe": timeframe,
        "observedAt": observed_at,
        "direction": vote["direction"],
        "confidence": vote["confidence"],
        "stopLossPrice": vote["stopLossPrice"],
        "takeProfitPrice": vote["takeProfitPrice"],
        "reasons": vote["reasons"],
        "evidence": vote["evidence"],
        "freshness": freshness,
        "ageSeconds": age_seconds,
        "sourceStatus": redact_text(source_status, 40),
        "sourceUpdatedAt": source_updated_at,
    }
    serialized = json.dumps(
        context,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if (
        len(serialized) > AI_TRADE_COUNCIL_CHAT_CONTEXT_MAX_CHARS
        or json_contains_potential_secret(context)
        or "[REDACTED_" in serialized
    ):
        return _ai_trade_council_chat_unavailable(
            agent_id,
            "latest_vote_context_rejected",
        )
    return context


def _agent_chat_runner_request_payload(
    message: str,
    history: list[dict],
    agent_id: str,
) -> dict:
    payload = {
        "message": message,
        "history": history,
    }
    council_context = ai_trade_council_agent_chat_context(agent_id)
    if council_context is not None:
        payload["councilContext"] = council_context
    return payload


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
    tracking_key: str | None = None,
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
                if tracking_key:
                    MISSION_WORKER_PROCESSES[tracking_key] = {
                        "process": process,
                        "jobHolder": job_holder,
                    }
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
                if tracking_key:
                    tracked = MISSION_WORKER_PROCESSES.get(tracking_key)
                    if isinstance(tracked, dict) and tracked.get("process") is process:
                        MISSION_WORKER_PROCESSES.pop(tracking_key, None)
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
    tracking_key: str | None = None,
) -> dict:
    if kill_process_tree_on_timeout:
        return _run_safe_command_with_tree_timeout(
            command,
            timeout,
            output_limit,
            input_text,
            cancel_event=cancel_event,
            tracking_key=tracking_key,
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
        if tool_id in {"codex_status", "codex_cli_smoke", "codex_cli_task", "codex_web_research"}:
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
            "webSearchEnabled": bool(policy.get("autoWebSearchAvailable", False)),
            "webSearchMode": redact_text(str(policy.get("autoWebSearchMode") or "disabled"), 40),
        })
    disabled_count = sum(
        1 for item in capabilities
        if str(item.get("adapterStatus") or "").startswith("disabled")
        or item.get("adapterStatus") in {"unimplemented", "not_implemented"}
        or "missing" in str(item.get("adapterStatus") or "")
        or "coming_soon" in str(item.get("adapterStatus") or "")
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


def _metatrader_origin_install_path(data_dir: Path, platform: str) -> str | None:
    """Read only MetaQuotes' origin path; never inspect account/server config."""
    origin_path = data_dir / "origin.txt"
    try:
        if not origin_path.is_file() or origin_path.stat().st_size > 4096:
            return None
        raw = origin_path.read_bytes()
    except (OSError, PermissionError):
        return None
    text = None
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            text = raw.decode(encoding).strip("\x00\r\n ")
            if text:
                break
        except UnicodeError:
            continue
    if not text or "\x00" in text:
        return None
    install_dir = Path(text)
    executable_name = "terminal.exe" if platform == "mt4" else "terminal64.exe"
    try:
        if not install_dir.is_absolute() or not (install_dir / executable_name).is_file():
            return None
    except (OSError, PermissionError):
        return None
    return _canonical_metatrader_location(install_dir)


def _metatrader_process_locations() -> dict:
    """Return backend-only install roots for running terminals without PID/title."""
    empty = {"supported": False, "mt4": [], "mt5": []}
    if os.name != "nt":
        return empty
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        (
            "$ErrorActionPreference='SilentlyContinue';"
            "@(Get-Process -Name terminal,terminal64 -ErrorAction SilentlyContinue | "
            "Where-Object { -not [string]::IsNullOrWhiteSpace($_.Path) } | "
            "ForEach-Object { [pscustomobject]@{name=$_.ProcessName;path=$_.Path} }) | "
            "ConvertTo-Json -Compress"
        ),
    ]
    try:
        probe = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=6,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return empty
    if probe.returncode != 0:
        return empty
    raw_output = (probe.stdout or "").strip()
    if not raw_output:
        return {"supported": True, "mt4": [], "mt5": []}
    try:
        decoded = json.loads(raw_output)
    except json.JSONDecodeError:
        return empty
    rows = decoded if isinstance(decoded, list) else [decoded]
    result = {"supported": True, "mt4": [], "mt5": []}
    for row in rows[:128]:
        if not isinstance(row, dict):
            continue
        process_name = str(row.get("name") or "").strip().lower()
        executable_path = str(row.get("path") or "").strip()
        platform = "mt4" if process_name == "terminal" else ("mt5" if process_name == "terminal64" else None)
        if not platform or not executable_path:
            continue
        expected_leaf = "terminal.exe" if platform == "mt4" else "terminal64.exe"
        executable = Path(executable_path)
        try:
            if executable.name.lower() != expected_leaf or not executable.is_file():
                continue
            install_dir = _canonical_metatrader_location(executable.parent)
        except (OSError, PermissionError):
            continue
        if install_dir not in result[platform]:
            result[platform].append(install_dir)
    return result


def _metatrader_running_state(
    running: dict,
    platform: str,
    install_path: str | None = None,
) -> str:
    if not bool(running.get("supported", False)):
        return "unknown"
    process_locations = running.get("_processInstallPaths")
    if isinstance(process_locations, dict):
        exact_locations = {
            os.path.normcase(str(item))
            for item in (process_locations.get(platform) or [])
            if str(item).strip()
        }
        if install_path:
            return (
                "platform_running_detected"
                if os.path.normcase(str(install_path)) in exact_locations
                else "not_running_detected"
            )
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
            install_path = str(item.get("installPath") or "")
            data_path = str(item.get("dataPath") or "")
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
                "installPath": install_path or None,
                "dataPath": data_path or None,
                "lastSeenAt": now,
                "available": True,
                "runningState": _metatrader_running_state(
                    running,
                    platform,
                    install_path or None,
                ),
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
        install_path = str(item.get("installPath") or "")
        counters[platform] += 1
        label = "MT4" if platform == "mt4" else "MT5"
        candidates.append({
            "candidateId": _new_metatrader_candidate_id(),
            "platform": platform,
            "labelTh": f"{label} ที่ตรวจพบ #{counters[platform]}",
            "detected": True,
            "runningState": _metatrader_running_state(
                running,
                platform,
                install_path or None,
            ),
        })
    return candidates


def discover_metatrader_installations(roots: list[Path] | None = None, include_candidates: bool = False) -> dict:
    """Inspect bounded, well-known local folders without reading terminal accounts or config."""
    found: dict[str, dict[str, dict[str, str | None]]] = {"mt4": {}, "mt5": {}}
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
            name = entry.name.lower()
            try:
                has_mql4 = (entry / "MQL4").is_dir()
                has_mql5 = (entry / "MQL5").is_dir()
                has_terminal = (entry / "terminal.exe").is_file()
                has_terminal64 = (entry / "terminal64.exe").is_file()
            except OSError:
                continue
            if has_mql4 or has_terminal:
                install_path = (
                    _canonical_metatrader_location(entry)
                    if has_terminal
                    else _metatrader_origin_install_path(entry, "mt4")
                )
                identity = _metatrader_identity_key("location", local_path)
                found["mt4"][identity] = {
                    "localPath": local_path,
                    "installPath": install_path,
                    "dataPath": local_path if has_mql4 else None,
                }
            if has_mql5 or has_terminal64:
                install_path = (
                    _canonical_metatrader_location(entry)
                    if has_terminal64
                    else _metatrader_origin_install_path(entry, "mt5")
                )
                identity = _metatrader_identity_key("location", local_path)
                found["mt5"][identity] = {
                    "localPath": local_path,
                    "installPath": install_path,
                    "dataPath": local_path if has_mql5 else None,
                }
            # MetaQuotes data roots contain opaque hash folders. MQL4/MQL5 is
            # the inspected platform signal. Only origin.txt is read to pair
            # that data folder with an exact executable; account/server files
            # remain out of scope.
            if root_name == "terminal":
                if has_mql4:
                    identity = _metatrader_identity_key("location", local_path)
                    found["mt4"][identity] = {
                        "localPath": local_path,
                        "installPath": _metatrader_origin_install_path(entry, "mt4"),
                        "dataPath": local_path,
                    }
                if has_mql5:
                    identity = _metatrader_identity_key("location", local_path)
                    found["mt5"][identity] = {
                        "localPath": local_path,
                        "installPath": _metatrader_origin_install_path(entry, "mt5"),
                        "dataPath": local_path,
                    }

    # When a data directory points back to an executable through origin.txt,
    # keep the data-directory candidate and suppress the duplicate bare
    # installation candidate. The selected record still retains the exact
    # executable root backend-side for per-candidate running-state matching.
    for platform in ("mt4", "mt5"):
        data_install_paths = {
            str(location.get("installPath") or "")
            for location in found[platform].values()
            if location.get("dataPath") and location.get("installPath")
        }
        found[platform] = {
            identity: location
            for identity, location in found[platform].items()
            if location.get("dataPath")
            or str(location.get("installPath") or "") not in data_install_paths
        }

    result = {"mt4": len(found["mt4"]), "mt5": len(found["mt5"])}
    if include_candidates:
        result["_candidateLocations"] = [
            {"platform": platform, **location}
            for platform in ("mt4", "mt5")
            for location in found[platform].values()
        ]
    return result


def discover_running_metatrader(
    process_rows: list[str] | None = None,
    process_locations: dict | None = None,
) -> dict:
    """Count terminals and keep exact executable roots backend-only."""
    if process_locations is None and process_rows is None:
        exact = _metatrader_process_locations()
        if exact.get("supported"):
            return {
                "supported": True,
                "mt4": len(exact.get("mt4") or []),
                "mt5": len(exact.get("mt5") or []),
                "_processInstallPaths": {
                    "mt4": list(exact.get("mt4") or []),
                    "mt5": list(exact.get("mt5") or []),
                },
            }
    if isinstance(process_locations, dict):
        normalized = {"mt4": [], "mt5": []}
        for platform in ("mt4", "mt5"):
            for item in process_locations.get(platform) or []:
                value = str(item or "").strip()
                if value:
                    normalized[platform].append(_canonical_metatrader_location(Path(value)))
        return {
            "supported": True,
            "mt4": len(set(normalized["mt4"])),
            "mt5": len(set(normalized["mt5"])),
            "_processInstallPaths": {
                "mt4": sorted(set(normalized["mt4"])),
                "mt5": sorted(set(normalized["mt5"])),
            },
        }
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


def _selected_metatrader_candidate_record(prop_id: str) -> dict | None:
    if prop_id not in METATRADER_TARGET_PROP_IDS:
        return None
    with METATRADER_TARGETS_LOCK:
        store = _load_metatrader_target_store_unlocked()
        selection = store["selections"].get(prop_id)
        if not isinstance(selection, dict):
            return None
        candidate_id = safe_reference(selection.get("candidateId"))
        record = store["candidates"].get(candidate_id or "")
        if not isinstance(record, dict) or not _metatrader_candidate_record_is_current(record):
            return None
        return dict(record)


def _load_mt4_trade_gateway_module():
    """Load the sibling gateway without relying on the caller's sys.path."""
    global MT4_TRADE_GATEWAY_MODULE
    if MT4_TRADE_GATEWAY_MODULE is not None:
        return MT4_TRADE_GATEWAY_MODULE
    if not MT4_TRADE_GATEWAY_MODULE_PATH.is_file():
        raise RuntimeError("MT4 Trade Gateway backend module is missing.")
    spec = importlib.util.spec_from_file_location(
        "metafx_mt4_trade_gateway_runtime",
        MT4_TRADE_GATEWAY_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("MT4 Trade Gateway backend module cannot be loaded.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    MT4_TRADE_GATEWAY_MODULE = module
    return module


def _mt4_trade_gateway_instance():
    module = _load_mt4_trade_gateway_module()
    return module.MT4TradeGateway(
        file_common_root=METATRADER_COMMON_FILES_DIR,
        state_root=RUNTIME_DIR / MT4_TRADE_GATEWAY_STATE_DIRNAME,
        command_ttl_seconds=30,
        heartbeat_ttl_seconds=30,
    )


def _mt4_trade_gateway_status_path(channel_id: str) -> Path | None:
    if (
        not channel_id.startswith("mtc-")
        or not SAFE_ID_PATTERN.fullmatch(channel_id)
    ):
        return None
    common_root = METATRADER_COMMON_FILES_DIR.resolve(strict=False)
    path = (
        common_root
        / "MetafxHQ"
        / channel_id
        / "trade-gateway"
        / "status.json"
    ).resolve(strict=False)
    try:
        path.relative_to(common_root)
    except ValueError:
        return None
    return path


def _mt4_trade_gateway_init_status_path(channel_id: str) -> Path | None:
    status_path = _mt4_trade_gateway_status_path(channel_id)
    if status_path is None:
        return None
    return status_path.with_name("init-status.json")


def _empty_mt4_trade_gateway_init_status(
    *,
    read_status: str = "not_observed",
    read_reason_code: str = "gateway_init_status_not_observed",
) -> dict:
    return {
        "available": False,
        "readStatus": read_status,
        "readReasonCode": read_reason_code,
        "sourceSchemaVersion": None,
        "eaVersion": None,
        "gatewayMode": None,
        "accountMode": None,
        "liveArmed": False,
        "severity": None,
        "stage": None,
        "reasonCode": None,
        "warningCode": None,
        "returnCode": None,
        "observedAt": None,
        "ageSeconds": None,
        "stale": False,
        "supersededByLiveStatus": False,
    }


def _read_mt4_trade_gateway_init_status(selected_candidate: dict) -> dict:
    """Read one strictly validated EA OnInit diagnostic without exposing files or secrets."""
    candidate_id = str(selected_candidate.get("candidateId") or "")
    init_path = _mt4_trade_gateway_init_status_path(candidate_id)
    if init_path is None:
        return _empty_mt4_trade_gateway_init_status(
            read_status="invalid_channel",
            read_reason_code="gateway_init_status_channel_invalid",
        )
    try:
        stat = init_path.stat()
        init_is_file = init_path.is_file()
    except FileNotFoundError:
        return _empty_mt4_trade_gateway_init_status()
    except (OSError, PermissionError):
        return _empty_mt4_trade_gateway_init_status(
            read_status="unreadable",
            read_reason_code="gateway_init_status_unreadable",
        )
    if (
        not init_is_file
        or stat.st_size <= 0
        or stat.st_size > MT4_TRADE_GATEWAY_INIT_STATUS_MAX_BYTES
    ):
        return _empty_mt4_trade_gateway_init_status(
            read_status="invalid",
            read_reason_code="gateway_init_status_size_invalid",
        )
    try:
        payload = json.loads(init_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _empty_mt4_trade_gateway_init_status(
            read_status="invalid",
            read_reason_code="gateway_init_status_json_invalid",
        )
    if (
        not isinstance(payload, dict)
        or set(payload) != MT4_TRADE_GATEWAY_INIT_STATUS_FIELDS
        or payload.get("schemaVersion") != MT4_TRADE_GATEWAY_INIT_STATUS_SCHEMA_VERSION
        or payload.get("channelId") != candidate_id
        or payload.get("profile") != "special"
        or payload.get("gatewayMode") not in {"shadow", "demo", "live"}
        or payload.get("accountMode") not in {"demo", "live"}
        or not isinstance(payload.get("liveArmed"), bool)
        or payload.get("severity") not in {"info", "warning", "error"}
        or not isinstance(payload.get("eaVersion"), str)
        or not re.fullmatch(r"[0-9]+\.[0-9]+", str(payload.get("eaVersion") or ""))
        or not isinstance(payload.get("stage"), str)
        or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", str(payload.get("stage") or ""))
        or not isinstance(payload.get("reasonCode"), str)
        or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,119}", str(payload.get("reasonCode") or ""))
        or not isinstance(payload.get("warningCode"), str)
        or (
            str(payload.get("warningCode") or "")
            and not re.fullmatch(r"[A-Z][A-Z0-9_]{0,119}", str(payload.get("warningCode") or ""))
        )
        or isinstance(payload.get("returnCode"), bool)
        or not isinstance(payload.get("returnCode"), int)
        or not -2_147_483_648 <= int(payload.get("returnCode")) <= 2_147_483_647
        or isinstance(payload.get("observedAt"), bool)
        or not isinstance(payload.get("observedAt"), int)
        or not 946684800 <= int(payload.get("observedAt")) <= 2_147_483_647
    ):
        return _empty_mt4_trade_gateway_init_status(
            read_status="invalid",
            read_reason_code="gateway_init_status_schema_invalid",
        )

    observed_at = int(payload["observedAt"])
    now = datetime.now(timezone.utc)
    clock_delta = int(now.timestamp()) - observed_at
    if clock_delta < -10:
        return _empty_mt4_trade_gateway_init_status(
            read_status="invalid",
            read_reason_code="gateway_init_status_clock_skew",
        )
    try:
        file_age = max(
            0.0,
            (now - datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)).total_seconds(),
        )
    except (OSError, OverflowError, ValueError):
        return _empty_mt4_trade_gateway_init_status(
            read_status="invalid",
            read_reason_code="gateway_init_status_timestamp_invalid",
        )
    age_seconds = max(0, clock_delta)
    stale = bool(
        age_seconds > MT4_TRADE_GATEWAY_INIT_STATUS_FRESH_SECONDS
        or file_age > MT4_TRADE_GATEWAY_INIT_STATUS_FRESH_SECONDS
    )
    return {
        "available": True,
        "readStatus": "stale" if stale else "ready",
        "readReasonCode": "gateway_init_status_stale" if stale else "ready",
        "sourceSchemaVersion": MT4_TRADE_GATEWAY_INIT_STATUS_SCHEMA_VERSION,
        "eaVersion": str(payload["eaVersion"]),
        "gatewayMode": str(payload["gatewayMode"]),
        "accountMode": str(payload["accountMode"]),
        "liveArmed": bool(payload["liveArmed"]),
        "severity": str(payload["severity"]),
        "stage": str(payload["stage"]),
        "reasonCode": str(payload["reasonCode"]),
        "warningCode": str(payload["warningCode"]) or None,
        "returnCode": int(payload["returnCode"]),
        "observedAt": datetime.fromtimestamp(observed_at, tz=timezone.utc).isoformat(),
        "ageSeconds": age_seconds,
        "stale": stale,
        "supersededByLiveStatus": False,
    }


def _reconcile_mt4_trade_gateway_init_status(
    init_status: dict,
    ea_status: dict | None,
) -> dict:
    reconciled = dict(init_status)
    if reconciled.get("available") is not True or not isinstance(ea_status, dict):
        return reconciled
    try:
        init_observed_at = datetime.fromisoformat(str(reconciled.get("observedAt") or ""))
        live_observed_at = datetime.fromisoformat(str(ea_status.get("observedAt") or ""))
    except (TypeError, ValueError):
        return reconciled
    reconciled["supersededByLiveStatus"] = live_observed_at >= init_observed_at
    return reconciled


def _mt4_trade_gateway_init_status_message_th(init_status: dict) -> str:
    if not isinstance(init_status, dict) or init_status.get("available") is not True:
        return ""
    severity = str(init_status.get("severity") or "")
    reason_code = str(init_status.get("reasonCode") or "")
    warning_code = str(init_status.get("warningCode") or "")
    superseded = init_status.get("supersededByLiveStatus") is True
    stale = init_status.get("stale") is True
    if stale and superseded:
        return ""
    if severity == "error" and superseded:
        return ""
    effective_code = warning_code or reason_code
    if severity not in {"error", "warning"} and not warning_code:
        return ""
    reason_labels = {
        "SNAPSHOT_CHANNEL_INVALID": "Channel ID ไม่ถูกต้อง",
        "LIVE_SIGNING_KEY_PIN_INVALID": "Key ID สำหรับโหมด Live มีรูปแบบไม่ถูกต้อง",
        "OPTIONAL_SIGNING_KEY_PIN_INVALID_IGNORED": "Key ID ที่ใส่ใน Demo หรือ Shadow ไม่ถูกต้อง ระบบจึงไม่ใช้ค่านี้",
        "OPTIONAL_SIGNING_KEY_PIN_MISMATCH_IGNORED": "Key ID ที่ใส่ใน Demo หรือ Shadow ไม่ตรงกับ Backend ระบบจึงใช้ค่าจาก Backend",
        "CRYPTO_SELF_TEST_FAILED": "การตรวจระบบลายเซ็น HMAC-SHA256 ไม่ผ่าน",
        "GATEWAY_INPUT_CONFIGURATION_INVALID": "ค่าตั้งต้นของ EA ไม่ผ่านการตรวจสอบ",
        "SYMBOL_OR_TIMEFRAME_NOT_ALLOWED": "คู่เงินหรือ Timeframe ของกราฟไม่อยู่ในรายการที่อนุญาต",
        "SNAPSHOT_CHANNEL_ALREADY_OWNED": "มี EA อีกตัวใช้ Channel ID นี้อยู่แล้ว",
        "GATEWAY_TIMER_START_FAILED": "EA เริ่มตัวจับเวลาเบื้องหลังไม่สำเร็จ",
        "INITIAL_SNAPSHOT_WRITE_FAILED": "EA เขียน Snapshot แรกไม่สำเร็จ",
        "INITIAL_CAPABILITIES_WRITE_FAILED": "EA เขียนข้อมูลความสามารถเริ่มต้นไม่สำเร็จ",
        "INITIAL_STATUS_WRITE_FAILED": "EA เขียนสถานะเริ่มต้นไม่สำเร็จ",
    }
    stage_labels = {
        "channel": "การตั้งค่า Channel ID",
        "signing": "การตั้งค่า Key ID",
        "crypto": "การตรวจระบบลายเซ็น",
        "inputs": "การตั้งค่า Inputs ของ EA",
        "chart": "คู่เงินและ Timeframe ของกราฟ",
        "fixed_lot": "การตั้งค่า Fixed Lot",
        "managed_magic_numbers": "การตั้งค่า Magic Number",
        "channel_lock": "การใช้ Channel ID ซ้ำ",
        "timer": "การเริ่มระบบจับเวลา",
        "snapshot": "การเขียน Snapshot",
        "capabilities": "การเขียนข้อมูลความสามารถของ EA",
        "status": "การเขียนสถานะของ EA",
    }
    detail = reason_labels.get(effective_code) or stage_labels.get(
        str(init_status.get("stage") or ""),
        "การเริ่มทำงานของ EA",
    )
    age_note = " ข้อมูลนี้เก่าและใช้เพื่อช่วยวินิจฉัยเท่านั้น" if stale else ""
    if severity == "error":
        return f"EA เริ่มทำงานไม่สำเร็จ: {detail}.{age_note}".strip()
    return f"EA เริ่มทำงานแล้ว แต่มีคำเตือน: {detail}.{age_note}".strip()


def _empty_mt4_trade_gateway_status(
    *,
    selected_candidate: dict | None = None,
    status: str = "not_connected",
    reason_code: str = "gateway_status_not_observed",
    backend_status: dict | None = None,
    init_status: dict | None = None,
) -> dict:
    candidate_id = safe_reference((selected_candidate or {}).get("candidateId"))
    platform = str((selected_candidate or {}).get("platform") or "") or None
    return {
        "schemaVersion": "metafx-hq-mt4-trade-gateway-read-model-v1",
        "sourceReady": MT4_TRADE_GATEWAY_MODULE_PATH.is_file(),
        "eaSourceReady": (
            PROJECT_ROOT
            / "integrations"
            / "mt4-trade-gateway"
            / "MetafxHQTradeGateway.mq4"
        ).is_file(),
        "connected": False,
        "status": status,
        "reasonCode": reason_code,
        "selectedCandidateId": candidate_id,
        "selectedPlatform": platform,
        "profile": "special",
        "mode": None,
        "statusSchemaVersion": None,
        "demoAccount": None,
        "accountMode": None,
        "accountModeMatchesGateway": False,
        "liveArmed": False,
        "fixedLot": None,
        "fixedLotSource": "ea_input_read_only",
        "aiCanSetLotOrRisk": False,
        "symbol": None,
        "timeframe": None,
        "observedAt": None,
        "ageSeconds": None,
        "autoTradingAllowed": False,
        "tradeAllowed": False,
        "killSwitchAvailable": False,
        "killSwitchActive": False,
        "commandSchemaVersion": None,
        "ackSchemaVersion": None,
        "signedCommandVerificationAvailable": False,
        "activeSigningKeyId": None,
        "signingKeyPinned": False,
        "signatureAlgorithm": None,
        "lastSignatureVerificationStatus": None,
        "signingKeyMatch": False,
        "executionGuardReady": False,
        "executionGuardReason": None,
        "maxManagedPositions": None,
        "currentManagedPositions": None,
        "maxManagedLots": None,
        "currentManagedLots": None,
        "maxTradesToday": None,
        "currentTradesToday": None,
        "maxLossPerTradePercent": None,
        "maxDailyLossPercent": None,
        "managedDailyPnl": None,
        "maxAccountEquityDrawdownPercent": None,
        "currentAccountEquityDrawdownPercent": None,
        "minRewardRiskRatio": None,
        "minProjectedMarginLevelPercent": None,
        "currentMarginLevelPercent": None,
        "maxSnapshotAgeSeconds": None,
        "maxSignalDriftPoints": None,
        "maxQuoteAgeSeconds": None,
        "shadowValidationAvailable": False,
        "demoOrderExecutionAvailable": False,
        "liveOrderExecutionAvailable": False,
        "backend": backend_status or {
            "available": MT4_TRADE_GATEWAY_MODULE_PATH.is_file(),
            "status": "not_initialized",
            "activeCommandId": None,
            "singleOutstanding": True,
            "eaSizingPolicy": "ea_input_only",
            "signedCommandRequiredForLive": True,
            "signedCommandVerificationAvailable": False,
            "activeSigningKeyId": None,
            "signedEnvelopeSchemaVersion": None,
            "signatureAlgorithm": None,
            "liveExecutionAvailable": False,
            "liveBlockReason": "signing_key_not_initialized",
        },
        "initStatus": init_status or _empty_mt4_trade_gateway_init_status(),
        "activeCommand": None,
        "latestCommand": None,
        "executionUnknownRecovery": None,
        "ackEvents": [],
        "updatedAt": utc_now(),
    }


def _read_mt4_trade_gateway_ea_status(
    selected_candidate: dict,
) -> tuple[dict | None, str]:
    candidate_id = str(selected_candidate.get("candidateId") or "")
    status_path = _mt4_trade_gateway_status_path(candidate_id)
    if status_path is None:
        return None, "gateway_channel_invalid"
    try:
        stat = status_path.stat()
    except FileNotFoundError:
        return None, "gateway_status_not_observed"
    except (OSError, PermissionError):
        return None, "gateway_status_unreadable"
    try:
        status_is_file = status_path.is_file()
    except (OSError, PermissionError):
        return None, "gateway_status_unreadable"
    if not status_is_file or stat.st_size <= 0 or stat.st_size > MT4_TRADE_GATEWAY_STATUS_MAX_BYTES:
        return None, "gateway_status_size_invalid"
    try:
        payload = json.loads(status_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "gateway_status_json_invalid"
    if not isinstance(payload, dict):
        return None, "gateway_status_schema_invalid"
    status_schema_version = str(payload.get("schemaVersion") or "")
    status_fields = set(payload)
    status_fields.discard("eaVersion")
    current_status_schema = bool(
        status_schema_version == MT4_TRADE_GATEWAY_STATUS_SCHEMA_VERSION
        and status_fields == MT4_TRADE_GATEWAY_STATUS_FIELDS
    )
    legacy_status_schema = bool(
        status_schema_version == MT4_TRADE_GATEWAY_LEGACY_STATUS_SCHEMA_VERSION
        and set(payload) == MT4_TRADE_GATEWAY_LEGACY_STATUS_FIELDS
    )
    if (
        not (current_status_schema or legacy_status_schema)
        or payload.get("channelId") != candidate_id
        or payload.get("profile") != "special"
        or payload.get("mode") not in {"shadow", "demo", "live"}
    ):
        return None, "gateway_status_schema_invalid"
    boolean_fields = [
        "liveArmed",
        "autoTradingAllowed",
        "tradeAllowed",
        "killSwitchActive",
        "signedCommandVerificationAvailable",
        "signingKeyPinned",
        "executionGuardReady",
    ]
    if current_status_schema:
        boolean_fields.append("demoAccount")
    for field in boolean_fields:
        if not isinstance(payload.get(field), bool):
            return None, "gateway_status_schema_invalid"
    active_signing_key_id = str(payload.get("activeSigningKeyId") or "")
    ea_version = str(payload.get("eaVersion") or "")
    account_mode = (
        str(payload.get("accountMode") or "")
        if current_status_schema
        else None
    )
    signature_algorithm = str(payload.get("signatureAlgorithm") or "")
    signature_status = str(payload.get("lastSignatureVerificationStatus") or "")
    if (
        payload.get("commandSchemaVersion") != "metafx-hq-mt4-command-v2"
        or payload.get("ackSchemaVersion") != "metafx-hq-mt4-ack-v3"
        or (
            current_status_schema
            and (
                account_mode not in {"demo", "live"}
                or bool(payload.get("demoAccount")) != (account_mode == "demo")
            )
        )
        or not isinstance(payload.get("activeSigningKeyId"), str)
        or not isinstance(payload.get("signatureAlgorithm"), str)
        or not isinstance(payload.get("lastSignatureVerificationStatus"), str)
        or (
            active_signing_key_id
            and not re.fullmatch(r"hk-[0-9a-f]{64}", active_signing_key_id)
        )
        or signature_algorithm != "HMAC-SHA256"
        or (ea_version and not re.fullmatch(r"[0-9]+\.[0-9]+", ea_version))
        or (
            signature_status
            and not re.fullmatch(r"[A-Z][A-Z0-9_]{0,119}", signature_status)
        )
        or not isinstance(payload.get("executionGuardReason"), str)
        or not re.fullmatch(
            r"[A-Z][A-Z0-9_]{0,119}",
            str(payload.get("executionGuardReason") or ""),
        )
    ):
        return None, "gateway_status_schema_invalid"

    def strict_status_count(field: str, *, minimum: int = 0, maximum: int = 1_000_000) -> int | None:
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value if minimum <= value <= maximum else None

    def strict_status_number(
        field: str,
        *,
        minimum: float = -1.0e12,
        maximum: float = 1.0e12,
    ) -> float | None:
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        number = float(value)
        if not math.isfinite(number) or number < minimum or number > maximum:
            return None
        return round(number, 8)

    status_counts = {
        "maxManagedPositions": strict_status_count("maxManagedPositions", minimum=1, maximum=1_000),
        "currentManagedPositions": strict_status_count("currentManagedPositions", maximum=10_000),
        "maxTradesToday": strict_status_count("maxTradesToday", minimum=1, maximum=100_000),
        "currentTradesToday": strict_status_count("currentTradesToday", maximum=1_000_000),
        "maxSnapshotAgeSeconds": strict_status_count("maxSnapshotAgeSeconds", minimum=1, maximum=86_400),
        "maxSignalDriftPoints": strict_status_count("maxSignalDriftPoints", maximum=10_000_000),
        "maxQuoteAgeSeconds": strict_status_count("maxQuoteAgeSeconds", minimum=1, maximum=3_600),
    }
    status_numbers = {
        "maxManagedLots": strict_status_number("maxManagedLots", minimum=0.00000001, maximum=1_000),
        "currentManagedLots": strict_status_number("currentManagedLots", minimum=0, maximum=10_000),
        "maxLossPerTradePercent": strict_status_number("maxLossPerTradePercent", minimum=0, maximum=100),
        "maxDailyLossPercent": strict_status_number("maxDailyLossPercent", minimum=0, maximum=100),
        "managedDailyPnl": strict_status_number("managedDailyPnl"),
        "maxAccountEquityDrawdownPercent": strict_status_number("maxAccountEquityDrawdownPercent", minimum=0, maximum=100),
        "currentAccountEquityDrawdownPercent": strict_status_number("currentAccountEquityDrawdownPercent", minimum=0, maximum=100),
        "minRewardRiskRatio": strict_status_number("minRewardRiskRatio", minimum=0, maximum=1_000),
        "minProjectedMarginLevelPercent": strict_status_number("minProjectedMarginLevelPercent", minimum=0, maximum=1_000_000_000),
        "currentMarginLevelPercent": strict_status_number("currentMarginLevelPercent", minimum=0, maximum=1_000_000_000),
    }
    if any(value is None for value in (*status_counts.values(), *status_numbers.values())):
        return None, "gateway_status_value_invalid"
    fixed_lot = _safe_snapshot_number(
        payload.get("fixedLot"),
        minimum=0.00000001,
        maximum=1000,
    )
    symbol = _safe_snapshot_symbol(payload.get("symbol"))
    timeframe = _safe_snapshot_timeframe(payload.get("timeframe"))
    observed_at = payload.get("observedAt")
    if (
        fixed_lot is None
        or not symbol
        or timeframe not in AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES
        or isinstance(observed_at, bool)
        or not isinstance(observed_at, int)
        or not 946684800 <= observed_at <= 2_147_483_647
    ):
        return None, "gateway_status_value_invalid"
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    clock_delta = now_epoch - observed_at
    try:
        file_age = max(
            0.0,
            (
                datetime.now(timezone.utc)
                - datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            ).total_seconds(),
        )
    except (OSError, OverflowError, ValueError):
        return None, "gateway_status_timestamp_invalid"
    if clock_delta < -10:
        return None, "gateway_status_clock_skew"
    age_seconds = max(0, clock_delta)
    if (
        age_seconds > MT4_TRADE_GATEWAY_STATUS_FRESH_SECONDS
        or file_age > MT4_TRADE_GATEWAY_STATUS_FRESH_SECONDS
    ):
        return None, "gateway_status_stale"
    return {
        "profile": "special",
        "mode": str(payload["mode"]),
        "demoAccount": (
            bool(payload["demoAccount"])
            if current_status_schema
            else None
        ),
        "accountMode": account_mode,
        "statusSchemaVersion": status_schema_version,
        "eaVersion": ea_version or None,
        "liveArmed": bool(payload["liveArmed"]),
        "fixedLot": fixed_lot,
        "symbol": symbol,
        "timeframe": timeframe,
        "observedAt": datetime.fromtimestamp(
            observed_at,
            tz=timezone.utc,
        ).isoformat(),
        "ageSeconds": age_seconds,
        "autoTradingAllowed": bool(payload["autoTradingAllowed"]),
        "tradeAllowed": bool(payload["tradeAllowed"]),
        "killSwitchActive": bool(payload["killSwitchActive"]),
        "commandSchemaVersion": str(payload["commandSchemaVersion"]),
        "ackSchemaVersion": str(payload["ackSchemaVersion"]),
        "signedCommandVerificationAvailable": bool(
            payload["signedCommandVerificationAvailable"]
        ),
        "activeSigningKeyId": active_signing_key_id or None,
        "signingKeyPinned": bool(payload["signingKeyPinned"]),
        "signatureAlgorithm": signature_algorithm,
        "lastSignatureVerificationStatus": signature_status or None,
        "executionGuardReady": bool(payload["executionGuardReady"]),
        "executionGuardReason": str(payload["executionGuardReason"]),
        **status_counts,
        **status_numbers,
    }, "ready"


def _mt4_trade_gateway_command_summary(
    command_record: dict | None,
) -> dict | None:
    if not isinstance(command_record, dict):
        return None
    command = (
        command_record.get("command")
        if isinstance(command_record.get("command"), dict)
        else {}
    )
    ack = (
        command_record.get("ack")
        if isinstance(command_record.get("ack"), dict)
        else {}
    )
    return {
        "commandId": safe_reference(command.get("commandId")),
        "missionId": safe_reference(command.get("missionId")),
        "snapshotId": safe_reference(command.get("snapshotId")),
        "councilDecisionId": safe_reference(command.get("councilDecisionId")),
        "action": str(command.get("action") or "") or None,
        "symbol": _safe_snapshot_symbol(command.get("symbol")),
        "timeframe": _safe_snapshot_timeframe(command.get("timeframe")),
        "stopLossPrice": _safe_snapshot_number(
            command.get("stopLoss"),
            minimum=0.00000001,
        ),
        "takeProfitPrice": _safe_snapshot_number(
            command.get("takeProfit"),
            minimum=0.00000001,
        ),
        "status": str(command_record.get("status") or "unknown"),
        "outstanding": bool(command_record.get("outstanding")),
        "ack": (
            {
                "status": str(ack.get("status") or "") or None,
                "reasonCode": redact_text(str(ack.get("reasonCode") or ""), 120) or None,
                "mode": str(ack.get("mode") or "") or None,
                "observedAt": ack.get("observedAt"),
                "ticket": ack.get("ticket"),
                "filledPrice": _safe_snapshot_number(
                    ack.get("filledPrice"),
                    minimum=0.00000001,
                ),
                "filledSlippagePoints": _safe_snapshot_number(
                    ack.get("filledSlippagePoints"),
                    minimum=0,
                ),
                "actualStopLoss": _safe_snapshot_number(
                    ack.get("actualStopLoss"),
                    minimum=0.00000001,
                ),
                "actualTakeProfit": _safe_snapshot_number(
                    ack.get("actualTakeProfit"),
                    minimum=0.00000001,
                ),
                "actualMagicNumber": (
                    int(ack["actualMagicNumber"])
                    if isinstance(ack.get("actualMagicNumber"), int)
                    and not isinstance(ack.get("actualMagicNumber"), bool)
                    else None
                ),
                "actualComment": redact_text(
                    str(ack.get("actualComment") or ""),
                    80,
                ) or None,
                "verificationStatus": redact_text(
                    str(ack.get("verificationStatus") or ""),
                    80,
                ) or None,
                "executionState": redact_text(
                    str(ack.get("executionState") or ""),
                    40,
                ) or None,
                "closedAt": ack.get("closedAt"),
                "closedPnl": _safe_snapshot_number(ack.get("closedPnl")),
                "errorCode": ack.get("errorCode"),
                "statePersisted": bool(ack.get("statePersisted")),
                "eaSizingStatus": str(
                    command_record.get("eaSizingStatus") or "not_reported"
                ),
            }
            if ack
            else None
        ),
        "createdAt": command_record.get("createdAt"),
        "updatedAt": command_record.get("updatedAt"),
    }


def mt4_trade_gateway_status_read_model() -> dict:
    """Reconcile the backend ledger and expose a sanitized EA status model."""
    record = _selected_metatrader_candidate_record(AI_TRADE_COUNCIL_PROP_ID)
    public_candidate = _public_metatrader_candidate(record) if record else None
    if not public_candidate:
        return _empty_mt4_trade_gateway_status(
            status="not_selected",
            reason_code="selected_mt4_terminal_missing",
        )
    if public_candidate.get("platform") != "mt4":
        return _empty_mt4_trade_gateway_status(
            selected_candidate=public_candidate,
            status="unsupported_platform",
            reason_code="mt4_trade_gateway_required",
        )
    init_status = _read_mt4_trade_gateway_init_status(public_candidate)
    ack_events: list[dict] = []
    active_command = None
    latest_command = None
    signing_key_metadata: dict = {}
    try:
        with MT4_TRADE_GATEWAY_LOCK:
            gateway = _mt4_trade_gateway_instance()
            # Key provisioning is backend-owned and returns only public
            # metadata.  The key material and filesystem path never enter this
            # read model, an audit event, or the Frontend response.
            ensured_key = gateway.ensure_signing_key(
                str(public_candidate.get("candidateId") or "")
            )
            if not isinstance(ensured_key, dict):
                raise RuntimeError("MT4 Trade Gateway signing metadata is invalid.")
            signing_key_metadata = dict(ensured_key)
            ack_events = gateway.ingest_pending_acks()
            expired = gateway.expire_pending()
            backend_status = gateway.status()
            active_command_id = safe_reference(backend_status.get("activeCommandId"))
            if active_command_id:
                active_command = _mt4_trade_gateway_command_summary(
                    gateway.read_command(active_command_id)
                )
            latest_command_id = safe_reference(backend_status.get("latestCommandId"))
            if latest_command_id:
                latest_command = _mt4_trade_gateway_command_summary(
                    gateway.read_command(latest_command_id)
                )
    except Exception as error:
        module = None
        try:
            module = _load_mt4_trade_gateway_module()
        except Exception:
            pass
        code = (
            str(getattr(error, "code", "") or "gateway_backend_unavailable")
            if module is not None
            else "gateway_backend_unavailable"
        )
        return _empty_mt4_trade_gateway_status(
            selected_candidate=public_candidate,
            status="backend_blocked",
            reason_code=code,
            init_status=init_status,
        )
    for event in ack_events:
        if (
            isinstance(event, dict)
            and event.get("ok") is True
            and event.get("idempotentReplay") is not True
        ):
            append_audit({
                "type": "mt4_trade_gateway.ack_ingested",
                "commandId": event.get("commandId"),
                "status": event.get("status"),
                "outstandingReleased": event.get("outstandingReleased"),
                "eaSizingStatus": event.get("eaSizingStatus"),
                "referencePriceBinding": event.get("referencePriceBinding"),
            })
        elif isinstance(event, dict) and event.get("ok") is False:
            rejection_key = payload_digest(
                str(event.get("code") or ""),
                str(event.get("fileName") or ""),
            )
            if rejection_key not in MT4_TRADE_GATEWAY_REJECTED_ACK_EVENTS:
                MT4_TRADE_GATEWAY_REJECTED_ACK_EVENTS.add(rejection_key)
                if len(MT4_TRADE_GATEWAY_REJECTED_ACK_EVENTS) > 256:
                    MT4_TRADE_GATEWAY_REJECTED_ACK_EVENTS.clear()
                    MT4_TRADE_GATEWAY_REJECTED_ACK_EVENTS.add(rejection_key)
                append_audit({
                    "type": "mt4_trade_gateway.ack_rejected",
                    "code": event.get("code"),
                    "fileName": event.get("fileName"),
                })
    if expired.get("expiredCount"):
        append_audit({
            "type": "mt4_trade_gateway.command_expired",
            "commandIds": expired.get("commandIds"),
            "slotReleased": False,
        })
    ea_status, reason_code = _read_mt4_trade_gateway_ea_status(public_candidate)
    init_status = _reconcile_mt4_trade_gateway_init_status(init_status, ea_status)
    backend_signing_key_id = str(signing_key_metadata.get("keyId") or "")
    backend_signature_algorithm = str(
        signing_key_metadata.get("algorithm")
        or backend_status.get("signatureAlgorithm")
        or ""
    )
    backend_envelope_version = str(
        signing_key_metadata.get("envelopeSchemaVersion")
        or backend_status.get("signedEnvelopeSchemaVersion")
        or ""
    )
    signing_metadata_valid = bool(
        signing_key_metadata.get("ok") is True
        and signing_key_metadata.get("channelId")
        == public_candidate.get("candidateId")
        and re.fullmatch(r"hk-[0-9a-f]{64}", backend_signing_key_id)
        and backend_signature_algorithm == "HMAC-SHA256"
        and backend_envelope_version == "metafx-hq-mt4-signed-envelope-v1"
    )
    backend_public = {
        "available": True,
        "status": (
            "waiting_ack"
            if backend_status.get("activeCommandId")
            else "ready"
        ),
        "activeCommandId": safe_reference(backend_status.get("activeCommandId")),
        "latestCommandId": safe_reference(backend_status.get("latestCommandId")),
        "commandCount": clamp_int(
            backend_status.get("commandCount"),
            0,
            0,
            1_000_000,
        ),
        "singleOutstanding": backend_status.get("singleOutstanding") is True,
        "eaSizingPolicy": "ea_input_only",
        "ledgerRevision": clamp_int(
            backend_status.get("ledgerRevision"),
            0,
            0,
            2_147_483_647,
        ),
        "signedCommandRequiredForLive": (
            backend_status.get("signedCommandRequiredForLive") is True
        ),
        "signedCommandVerificationAvailable": (
            backend_status.get("signedCommandVerificationAvailable") is True
            and signing_metadata_valid
        ),
        "activeSigningKeyId": (
            backend_signing_key_id if signing_metadata_valid else None
        ),
        "signedEnvelopeSchemaVersion": (
            backend_envelope_version if signing_metadata_valid else None
        ),
        "signatureAlgorithm": (
            backend_signature_algorithm if signing_metadata_valid else None
        ),
        "liveExecutionAvailable": (
            backend_status.get("liveExecutionAvailable") is True
            and signing_metadata_valid
        ),
        "liveBlockReason": redact_text(
            str(
                backend_status.get("liveBlockReason")
                or ("" if signing_metadata_valid else "signing_key_metadata_invalid")
            ),
            120,
        ) or None,
        "executionUnknownQuarantineAvailable": (
            backend_status.get("executionUnknownQuarantineAvailable") is True
        ),
        "outcomeTrackingAvailable": (
            backend_status.get("outcomeTrackingAvailable") is True
        ),
        "byStatus": sanitize_json_value(
            backend_status.get("byStatus")
            if isinstance(backend_status.get("byStatus"), dict)
            else {}
        ),
    }
    if ea_status is None:
        return _empty_mt4_trade_gateway_status(
            selected_candidate=public_candidate,
            status="awaiting_ea",
            reason_code=reason_code,
            backend_status=backend_public,
            init_status=init_status,
        )
    mode = str(ea_status["mode"])
    demo_account = ea_status.get("demoAccount")
    account_identity_available = isinstance(demo_account, bool)
    account_mode_matches_gateway = bool(
        account_identity_available
        and (
            mode == "shadow"
            or (mode == "demo" and demo_account is True)
            or (mode == "live" and demo_account is False)
        )
    )
    base_trade_ready = (
        ea_status["autoTradingAllowed"] is True
        and ea_status["tradeAllowed"] is True
        and ea_status["killSwitchActive"] is False
        and ea_status["executionGuardReady"] is True
    )
    backend_signer_ready = (
        backend_public["signedCommandVerificationAvailable"] is True
        and backend_public["activeSigningKeyId"] is not None
        and backend_public["signatureAlgorithm"] == "HMAC-SHA256"
    )
    ea_signing_key_id = str(ea_status.get("activeSigningKeyId") or "")
    signing_key_match = bool(
        backend_signer_ready
        and ea_signing_key_id
        and ea_signing_key_id == backend_public["activeSigningKeyId"]
    )
    signed_command_verification_ready = bool(
        backend_signer_ready
        and ea_status["signedCommandVerificationAvailable"] is True
        and ea_status["signatureAlgorithm"] == "HMAC-SHA256"
        and signing_key_match
    )
    live_signed_execution_ready = bool(
        signed_command_verification_ready
        and ea_status["signingKeyPinned"] is True
    )
    signed_verification_block_reason = (
        str(backend_public.get("liveBlockReason") or "backend_signer_not_ready")
        if not backend_signer_ready
        else "ea_signed_command_verifier_not_ready"
        if ea_status["signedCommandVerificationAvailable"] is not True
        else "signing_key_identity_mismatch"
        if not signing_key_match
        else "signed_command_verification_not_ready"
    )
    live_signature_block_reason = (
        signed_verification_block_reason
        if not signed_command_verification_ready
        else "ea_signing_key_not_pinned"
        if ea_status["signingKeyPinned"] is not True
        else "signed_execution_not_ready"
    )
    # Shadow/Demo may follow the channel's active signing key. Live execution is
    # stricter: the EA must explicitly pin the exact trusted key identity.
    demo_ready = (
        mode == "demo"
        and demo_account is True
        and base_trade_ready
        and signed_command_verification_ready
    )
    live_ready = (
        mode == "live"
        and demo_account is False
        and ea_status["liveArmed"] is True
        and base_trade_ready
        and live_signed_execution_ready
        and backend_public["liveExecutionAvailable"] is True
    )
    public_status = (
        "shadow"
        if mode == "shadow" and account_identity_available
        else "legacy_status_read_only"
        if mode == "shadow" and not account_identity_available
        else "demo_blocked"
        if mode == "demo" and demo_account is not True
        else "live_blocked"
        if mode == "live" and demo_account is not False
        else "execution_guard_blocked"
        if mode in {"demo", "live"} and not base_trade_ready
        else "demo_ready"
        if demo_ready
        else "demo_blocked"
        if mode == "demo"
        else "live_ready"
        if live_ready
        else "live_locked"
        if mode == "live" and ea_status["liveArmed"] is not True
        else "live_blocked"
        if mode == "live"
        else "ready"
    )
    execution_unknown_recovery = None
    if (
        isinstance(active_command, dict)
        and isinstance(active_command.get("ack"), dict)
        and active_command["ack"].get("status") == "EXECUTION_UNKNOWN"
        and backend_status.get("executionUnknownQuarantineAvailable") is True
    ):
        execution_unknown_recovery = {
            "required": True,
            "commandId": active_command.get("commandId"),
            "expectedLedgerRevision": backend_public["ledgerRevision"],
            "killSwitchWillActivate": True,
            "barClaimWillBeRetained": True,
            "automaticRetry": False,
        }
    return {
        **_empty_mt4_trade_gateway_status(
            selected_candidate=public_candidate,
            backend_status=backend_public,
            init_status=init_status,
        ),
        **ea_status,
        "connected": True,
        "status": public_status,
        "executionGuardReady": bool(
            ea_status["executionGuardReady"] is True
            and (mode == "shadow" or account_identity_available)
        ),
        "executionGuardReason": (
            str(ea_status["executionGuardReason"])
            if account_identity_available
            else "ACCOUNT_IDENTITY_UNAVAILABLE"
        ),
        "accountModeMatchesGateway": account_mode_matches_gateway,
        "signingKeyMatch": signing_key_match,
        "reasonCode": (
            "ready"
            if public_status in {"shadow", "demo_ready", "live_ready", "ready"}
            else "gateway_status_account_identity_unavailable"
            if not account_identity_available
            else "demo_mode_requires_demo_account"
            if mode == "demo" and demo_account is False
            else "live_mode_requires_non_demo_account"
            if mode == "live" and demo_account is True
            else "execution_guard_not_ready"
            if public_status == "execution_guard_blocked"
            else "live_arm_not_enabled"
            if mode == "live" and ea_status["liveArmed"] is not True
            else signed_verification_block_reason
            if mode == "demo" and not signed_command_verification_ready
            else live_signature_block_reason
            if mode == "live" and not live_signed_execution_ready
            else str(
                backend_public.get("liveBlockReason")
                or "live_execution_unavailable"
            )
        ),
        "killSwitchAvailable": True,
        "shadowValidationAvailable": mode == "shadow",
        "demoOrderExecutionAvailable": demo_ready,
        "liveOrderExecutionAvailable": live_ready,
        "activeCommand": active_command,
        "latestCommand": latest_command,
        "executionUnknownRecovery": execution_unknown_recovery,
        "ackEvents": [
            {
                "kind": str(item.get("kind") or ""),
                "commandId": safe_reference(item.get("commandId")),
                "status": str(item.get("status") or ""),
            }
            for item in ack_events
            if isinstance(item, dict)
        ],
        "updatedAt": utc_now(),
    }


def _mt4_trade_gateway_command_read_model(command_id: object) -> dict | None:
    safe_command_id = safe_reference(command_id)
    if not safe_command_id or not safe_command_id.startswith("cmd-"):
        return None
    try:
        with MT4_TRADE_GATEWAY_LOCK:
            gateway = _mt4_trade_gateway_instance()
            return _mt4_trade_gateway_command_summary(
                gateway.read_command(safe_command_id)
            )
    except Exception:
        return None


def mt4_trade_gateway_outcome_read_model(command_id: object) -> dict:
    """Return only validated EA lifecycle evidence for one exact command."""
    safe_command_id = safe_reference(command_id)
    if not safe_command_id or not safe_command_id.startswith("cmd-"):
        return {
            "ok": False,
            "kind": "invalid_command_id",
            "outcome": None,
            "_httpStatus": 422,
        }
    try:
        with MT4_TRADE_GATEWAY_LOCK:
            gateway = _mt4_trade_gateway_instance()
            outcome = gateway.read_outcome(safe_command_id)
    except Exception as error:
        return {
            "ok": False,
            "kind": str(getattr(error, "code", "") or "outcome_unavailable"),
            "outcome": None,
            "_httpStatus": 409,
        }
    return {
        "ok": True,
        "kind": "mt4_trade_outcome_read",
        "commandId": safe_command_id,
        "outcome": sanitize_json_value(outcome) if outcome else None,
        "updatedAt": utc_now(),
    }


def quarantine_mt4_execution_unknown(payload: dict) -> dict:
    """Fail closed for one exact uncertain command; never retry or infer a fill."""
    if set(payload) != {"commandId", "expectedLedgerRevision"}:
        return {
            "ok": False,
            "kind": "invalid_execution_unknown_recovery_request",
            "messageTh": "คำขอกักคำสั่งต้องมี Command ID และ Ledger Revision ล่าสุดเท่านั้น",
            "_httpStatus": 422,
        }
    command_id = safe_reference(payload.get("commandId"))
    expected_revision = payload.get("expectedLedgerRevision")
    if (
        not command_id
        or not command_id.startswith("cmd-")
        or isinstance(expected_revision, bool)
        or not isinstance(expected_revision, int)
        or expected_revision < 0
    ):
        return {
            "ok": False,
            "kind": "invalid_execution_unknown_recovery_request",
            "messageTh": "ข้อมูลคำสั่งหรือ Ledger Revision ไม่ถูกต้อง",
            "_httpStatus": 422,
        }
    try:
        with MT4_TRADE_GATEWAY_LOCK:
            gateway = _mt4_trade_gateway_instance()
            result = gateway.quarantine_execution_unknown(
                command_id,
                expected_ledger_revision=expected_revision,
            )
    except Exception as error:
        code = str(getattr(error, "code", "") or "execution_unknown_recovery_blocked")
        append_audit({
            "type": "mt4_trade_gateway.execution_unknown_quarantine_blocked",
            "commandId": command_id,
            "expectedLedgerRevision": expected_revision,
            "reason": code,
            "automaticRetry": False,
        })
        return {
            "ok": False,
            "kind": code,
            "messageTh": "ยังไม่สามารถกักคำสั่งนี้ได้ กรุณารีเฟรชสถานะล่าสุดก่อน",
            "automaticRetry": False,
            "_httpStatus": 409,
        }
    append_audit({
        "type": "mt4_trade_gateway.execution_unknown_quarantined",
        "commandId": command_id,
        "expectedLedgerRevision": expected_revision,
        "killSwitchActive": result.get("killSwitchActive") is True,
        "barClaimRetained": result.get("barClaimRetained") is True,
        "automaticRetry": False,
    })
    return {
        **result,
        "automaticRetry": False,
        "messageTh": "กักคำสั่งที่ผลไม่แน่ชัดแล้ว เปิด Kill Switch และไม่ส่งคำสั่งเดิมซ้ำ",
    }


def _safe_snapshot_number(
    value: object,
    *,
    minimum: float = -1.0e15,
    maximum: float = 1.0e15,
) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or number < minimum or number > maximum:
        return None
    return round(number, 8)


def _safe_snapshot_count(value: object, maximum: int = 1_000_000) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if number < 0 or number > maximum:
        return None
    return number


def _safe_snapshot_symbol(value: object) -> str | None:
    symbol = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9._#-]{1,24}", symbol):
        return None
    return symbol


def _safe_snapshot_timeframe(value: object) -> str | None:
    timeframe = str(value or "").strip().upper()
    return timeframe if timeframe in {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"} else None


def _technical_output_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return round(number, 8) if math.isfinite(number) else None


def _technical_ema_series(values: list[float], period: int) -> list[float | None]:
    """Return an SMA-seeded EMA series with explicit null warm-up values."""
    result: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return result
    seed = sum(values[:period]) / period
    if not math.isfinite(seed):
        return result
    result[period - 1] = seed
    multiplier = 2.0 / (period + 1.0)
    previous = seed
    for index in range(period, len(values)):
        previous = ((values[index] - previous) * multiplier) + previous
        if not math.isfinite(previous):
            return [None] * len(values)
        result[index] = previous
    return result


def _technical_ema(values: list[float], period: int) -> float | None:
    series = _technical_ema_series(values, period)
    return _technical_output_number(series[-1]) if series else None


def _technical_rsi_wilder_series(
    closes: list[float],
    period: int = 14,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    if period <= 0 or len(closes) < period + 1:
        return result
    changes = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
    average_gain = sum(max(value, 0.0) for value in changes[:period]) / period
    average_loss = sum(max(-value, 0.0) for value in changes[:period]) / period

    def rsi_value(gain: float, loss: float) -> float:
        if loss == 0.0:
            return 100.0 if gain > 0.0 else 50.0
        relative_strength = gain / loss
        return 100.0 - (100.0 / (1.0 + relative_strength))

    result[period] = rsi_value(average_gain, average_loss)
    for index in range(period + 1, len(closes)):
        change = changes[index - 1]
        average_gain = (
            (average_gain * (period - 1)) + max(change, 0.0)
        ) / period
        average_loss = (
            (average_loss * (period - 1)) + max(-change, 0.0)
        ) / period
        current = rsi_value(average_gain, average_loss)
        if not math.isfinite(current):
            return [None] * len(closes)
        result[index] = current
    return result


def _technical_atr_wilder_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    if period <= 0 or len(closes) < period:
        return result
    true_ranges: list[float] = []
    for index in range(len(closes)):
        if index == 0:
            value = highs[index] - lows[index]
        else:
            previous_close = closes[index - 1]
            value = max(
                highs[index] - lows[index],
                abs(highs[index] - previous_close),
                abs(lows[index] - previous_close),
            )
        if not math.isfinite(value) or value < 0:
            return result
        true_ranges.append(value)
    previous = sum(true_ranges[:period]) / period
    result[period - 1] = previous
    for index in range(period, len(closes)):
        previous = ((previous * (period - 1)) + true_ranges[index]) / period
        if not math.isfinite(previous):
            return [None] * len(closes)
        result[index] = previous
    return result


def _technical_macd_signal_series(
    macd_line: list[float | None],
    period: int = 9,
) -> list[float | None]:
    result: list[float | None] = [None] * len(macd_line)
    observed = [
        (index, float(value))
        for index, value in enumerate(macd_line)
        if value is not None and math.isfinite(float(value))
    ]
    if period <= 0 or len(observed) < period:
        return result
    seed = sum(value for _, value in observed[:period]) / period
    seed_index = observed[period - 1][0]
    result[seed_index] = seed
    multiplier = 2.0 / (period + 1.0)
    previous = seed
    for index, value in observed[period:]:
        previous = ((value - previous) * multiplier) + previous
        if not math.isfinite(previous):
            return [None] * len(macd_line)
        result[index] = previous
    return result


def _technical_sma_series(
    values: list[float],
    period: int,
) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return result
    rolling = sum(values[:period])
    result[period - 1] = rolling / period
    for index in range(period, len(values)):
        rolling += values[index] - values[index - period]
        result[index] = rolling / period
    return result


def _technical_stochastic_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    lookback: int = 14,
    slowing: int = 3,
    signal: int = 3,
) -> tuple[list[float | None], list[float | None]]:
    raw: list[float | None] = [None] * len(closes)
    for index in range(lookback - 1, len(closes)):
        high = max(highs[index - lookback + 1:index + 1])
        low = min(lows[index - lookback + 1:index + 1])
        raw[index] = 50.0 if high == low else ((closes[index] - low) / (high - low)) * 100.0

    def smoothed(source: list[float | None], period: int) -> list[float | None]:
        output: list[float | None] = [None] * len(source)
        for index in range(period - 1, len(source)):
            window = source[index - period + 1:index + 1]
            if all(value is not None for value in window):
                output[index] = sum(float(value) for value in window) / period
        return output

    percent_k = smoothed(raw, slowing)
    return percent_k, smoothed(percent_k, signal)


def _technical_bollinger_series(
    closes: list[float],
    period: int = 20,
    deviations: float = 2.0,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    middle = _technical_sma_series(closes, period)
    upper: list[float | None] = [None] * len(closes)
    lower: list[float | None] = [None] * len(closes)
    for index in range(period - 1, len(closes)):
        window = closes[index - period + 1:index + 1]
        mean = float(middle[index])
        variance = sum((value - mean) ** 2 for value in window) / period
        standard_deviation = math.sqrt(max(variance, 0.0))
        upper[index] = mean + (deviations * standard_deviation)
        lower[index] = mean - (deviations * standard_deviation)
    return middle, upper, lower


def _technical_adx_dmi_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    size = len(closes)
    adx: list[float | None] = [None] * size
    plus_di: list[float | None] = [None] * size
    minus_di: list[float | None] = [None] * size
    if period <= 0 or size <= period:
        return adx, plus_di, minus_di
    true_ranges = [0.0] * size
    plus_dm = [0.0] * size
    minus_dm = [0.0] * size
    for index in range(1, size):
        true_ranges[index] = max(
            highs[index] - lows[index],
            abs(highs[index] - closes[index - 1]),
            abs(lows[index] - closes[index - 1]),
        )
        upward = highs[index] - highs[index - 1]
        downward = lows[index - 1] - lows[index]
        plus_dm[index] = upward if upward > downward and upward > 0.0 else 0.0
        minus_dm[index] = downward if downward > upward and downward > 0.0 else 0.0
    smoothed_tr = sum(true_ranges[1:period + 1])
    smoothed_plus = sum(plus_dm[1:period + 1])
    smoothed_minus = sum(minus_dm[1:period + 1])
    dx: list[float | None] = [None] * size
    for index in range(period, size):
        if index > period:
            smoothed_tr = smoothed_tr - (smoothed_tr / period) + true_ranges[index]
            smoothed_plus = smoothed_plus - (smoothed_plus / period) + plus_dm[index]
            smoothed_minus = smoothed_minus - (smoothed_minus / period) + minus_dm[index]
        if smoothed_tr <= 0.0:
            plus = minus = 0.0
        else:
            plus = 100.0 * smoothed_plus / smoothed_tr
            minus = 100.0 * smoothed_minus / smoothed_tr
        plus_di[index] = plus
        minus_di[index] = minus
        denominator = plus + minus
        dx[index] = 0.0 if denominator == 0.0 else 100.0 * abs(plus - minus) / denominator
    first_adx_index = (period * 2) - 1
    if size > first_adx_index:
        seed_values = [float(value) for value in dx[period:first_adx_index + 1] if value is not None]
        if len(seed_values) == period:
            previous = sum(seed_values) / period
            adx[first_adx_index] = previous
            for index in range(first_adx_index + 1, size):
                current_dx = dx[index]
                if current_dx is None:
                    continue
                previous = ((previous * (period - 1)) + current_dx) / period
                adx[index] = previous
    return adx, plus_di, minus_di


def _technical_cci_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 20,
) -> list[float | None]:
    typical = [(highs[index] + lows[index] + closes[index]) / 3.0 for index in range(len(closes))]
    result: list[float | None] = [None] * len(closes)
    for index in range(period - 1, len(closes)):
        window = typical[index - period + 1:index + 1]
        mean = sum(window) / period
        mean_deviation = sum(abs(value - mean) for value in window) / period
        result[index] = 0.0 if mean_deviation == 0.0 else (typical[index] - mean) / (0.015 * mean_deviation)
    return result


def _technical_williams_r_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    for index in range(period - 1, len(closes)):
        high = max(highs[index - period + 1:index + 1])
        low = min(lows[index - period + 1:index + 1])
        result[index] = -50.0 if high == low else -100.0 * (high - closes[index]) / (high - low)
    return result


def _technical_rate_series(
    closes: list[float],
    period: int,
    *,
    base: float,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    for index in range(period, len(closes)):
        previous = closes[index - period]
        if previous > 0.0:
            result[index] = (closes[index] / previous) * base
            if base == 100.0:
                result[index] -= 100.0
    return result


def _technical_momentum_series(
    closes: list[float],
    period: int = 10,
) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    for index in range(period, len(closes)):
        previous = closes[index - period]
        if previous > 0.0:
            result[index] = (closes[index] / previous) * 100.0
    return result


def _technical_obv_series(
    closes: list[float],
    volumes: list[float],
) -> list[float | None]:
    if not closes:
        return []
    result: list[float | None] = [0.0] * len(closes)
    for index in range(1, len(closes)):
        previous = float(result[index - 1])
        if closes[index] > closes[index - 1]:
            result[index] = previous + volumes[index]
        elif closes[index] < closes[index - 1]:
            result[index] = previous - volumes[index]
        else:
            result[index] = previous
    return result


def _technical_mfi_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float],
    period: int = 14,
) -> list[float | None]:
    size = len(closes)
    result: list[float | None] = [None] * size
    typical = [(highs[index] + lows[index] + closes[index]) / 3.0 for index in range(size)]
    positive = [0.0] * size
    negative = [0.0] * size
    for index in range(1, size):
        flow = typical[index] * volumes[index]
        if typical[index] > typical[index - 1]:
            positive[index] = flow
        elif typical[index] < typical[index - 1]:
            negative[index] = flow
    for index in range(period, size):
        positive_sum = sum(positive[index - period + 1:index + 1])
        negative_sum = sum(negative[index - period + 1:index + 1])
        if negative_sum == 0.0:
            result[index] = 100.0 if positive_sum > 0.0 else 50.0
        else:
            result[index] = 100.0 - (100.0 / (1.0 + (positive_sum / negative_sum)))
    return result


def _technical_indicator_snapshot_uncached(bars: list[dict]) -> dict:
    """Calculate reproducible indicators from one exact closed-bar window."""
    times: list[int | None] = []
    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    volumes: list[float] = []
    payload_valid = bool(bars)
    for item in bars:
        if not isinstance(item, dict):
            payload_valid = False
            break
        open_price = _technical_output_number(item.get("open"))
        close = _technical_output_number(item.get("close"))
        high = _technical_output_number(item.get("high"))
        low = _technical_output_number(item.get("low"))
        volume = _technical_output_number(item.get("volume"))
        timestamp = item.get("time")
        if (
            open_price is None
            or not isinstance(timestamp, int)
            or isinstance(timestamp, bool)
            or timestamp <= 0
            or close is None
            or high is None
            or low is None
            or volume is None
            or min(open_price, close, high, low) <= 0
            or volume < 0
            or high < max(open_price, close)
            or low > min(open_price, close)
            or high < low
        ):
            payload_valid = False
            break
        times.append(timestamp)
        closes.append(close)
        highs.append(high)
        lows.append(low)
        volumes.append(volume)

    empty_series: list[dict] = []
    if not payload_valid:
        return {
            "available": False,
            "reasonCode": "invalid_closed_bar_payload",
            "basis": "backend_calculated_closed_bars_only",
            "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
            "moduleCount": len(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
            "modules": list(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
            "barCount": len(bars),
            "latestClosedBarTime": None,
            "latestClose": None,
            "sma20": None,
            "sma50": None,
            "sma200": None,
            "ema9": None,
            "ema12": None,
            "ema20": None,
            "ema26": None,
            "ema50": None,
            "ema200": None,
            "rsi14": None,
            "atr14": None,
            "atrPercent": None,
            "macdLine": None,
            "macdSignal": None,
            "macdHistogram": None,
            "stochasticK": None,
            "stochasticD": None,
            "bollingerMiddle": None,
            "bollingerUpper": None,
            "bollingerLower": None,
            "adx14": None,
            "plusDI14": None,
            "minusDI14": None,
            "cci20": None,
            "williamsR14": None,
            "roc12": None,
            "momentum10": None,
            "obv": None,
            "mfi14": None,
            "volumeMA20": None,
            "averageVolume20": None,
            "closeVsEma20": None,
            "trendState": "UNAVAILABLE",
            "series": empty_series,
        }

    def latest(series: list[float | None]) -> float | None:
        return _technical_output_number(series[-1]) if series else None

    sma20_series = _technical_sma_series(closes, 20)
    sma50_series = _technical_sma_series(closes, 50)
    sma200_series = _technical_sma_series(closes, 200)
    ema9_series = _technical_ema_series(closes, 9)
    ema12_series = _technical_ema_series(closes, 12)
    ema20_series = _technical_ema_series(closes, 20)
    ema26_series = _technical_ema_series(closes, 26)
    ema50_series = _technical_ema_series(closes, 50)
    ema200_series = _technical_ema_series(closes, 200)
    rsi14_series = _technical_rsi_wilder_series(closes, 14)
    atr14_series = _technical_atr_wilder_series(highs, lows, closes, 14)
    stochastic_k_series, stochastic_d_series = _technical_stochastic_series(
        highs,
        lows,
        closes,
    )
    (
        bollinger_middle_series,
        bollinger_upper_series,
        bollinger_lower_series,
    ) = _technical_bollinger_series(closes)
    adx14_series, plus_di14_series, minus_di14_series = _technical_adx_dmi_series(
        highs,
        lows,
        closes,
    )
    cci20_series = _technical_cci_series(highs, lows, closes)
    williams_r14_series = _technical_williams_r_series(highs, lows, closes)
    roc12_series = _technical_rate_series(closes, 12, base=100.0)
    momentum10_series = _technical_momentum_series(closes, 10)
    obv_series = _technical_obv_series(closes, volumes)
    mfi14_series = _technical_mfi_series(highs, lows, closes, volumes)
    volume_ma20_series = _technical_sma_series(volumes, 20)
    macd_line_series: list[float | None] = [
        (ema12_series[index] - ema26_series[index])
        if ema12_series[index] is not None and ema26_series[index] is not None
        else None
        for index in range(len(closes))
    ]
    macd_signal_series = _technical_macd_signal_series(macd_line_series, 9)
    macd_histogram_series: list[float | None] = [
        (macd_line_series[index] - macd_signal_series[index])
        if macd_line_series[index] is not None
        and macd_signal_series[index] is not None
        else None
        for index in range(len(closes))
    ]
    latest_close = closes[-1]
    sma20 = latest(sma20_series)
    sma50 = latest(sma50_series)
    sma200 = latest(sma200_series)
    ema9 = latest(ema9_series)
    ema12 = latest(ema12_series)
    ema20 = latest(ema20_series)
    ema26 = latest(ema26_series)
    ema50 = latest(ema50_series)
    ema200 = latest(ema200_series)
    rsi14 = latest(rsi14_series)
    atr14 = latest(atr14_series)
    macd_line = latest(macd_line_series)
    macd_signal = latest(macd_signal_series)
    macd_histogram = latest(macd_histogram_series)
    stochastic_k = latest(stochastic_k_series)
    stochastic_d = latest(stochastic_d_series)
    bollinger_middle = latest(bollinger_middle_series)
    bollinger_upper = latest(bollinger_upper_series)
    bollinger_lower = latest(bollinger_lower_series)
    adx14 = latest(adx14_series)
    plus_di14 = latest(plus_di14_series)
    minus_di14 = latest(minus_di14_series)
    cci20 = latest(cci20_series)
    williams_r14 = latest(williams_r14_series)
    roc12 = latest(roc12_series)
    momentum10 = latest(momentum10_series)
    obv = latest(obv_series)
    mfi14 = latest(mfi14_series)
    volume_ma20 = latest(volume_ma20_series)
    atr_percent = (
        _technical_output_number((atr14 / latest_close) * 100.0)
        if atr14 is not None and latest_close > 0
        else None
    )
    if ema20 is None or ema50 is None:
        trend_state = "UNAVAILABLE"
    elif (
        latest_close > ema20 > ema50
        and (ema200 is None or ema50 > ema200)
    ):
        trend_state = "BULLISH"
    elif (
        latest_close < ema20 < ema50
        and (ema200 is None or ema50 < ema200)
    ):
        trend_state = "BEARISH"
    else:
        trend_state = "MIXED"
    available = all(
        value is not None
        for value in (
            ema20,
            ema50,
            rsi14,
            atr14,
            macd_line,
            stochastic_k,
            bollinger_middle,
            adx14,
            cci20,
            williams_r14,
            roc12,
            momentum10,
            obv,
            mfi14,
        )
    )
    return {
        "available": available,
        "reasonCode": "ready" if available else "indicator_warmup_incomplete",
        "basis": "backend_calculated_closed_bars_only",
        "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
        "moduleCount": len(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
        "modules": list(AI_TRADE_COUNCIL_TECHNICAL_MODULES),
        "barCount": len(bars),
        "latestClosedBarTime": bars[-1].get("time") if bars else None,
        "latestClose": _technical_output_number(latest_close),
        "sma20": sma20,
        "sma50": sma50,
        "sma200": sma200,
        "ema9": ema9,
        "ema12": ema12,
        "ema20": ema20,
        "ema26": ema26,
        "ema50": ema50,
        "ema200": ema200,
        "rsi14": rsi14,
        "atr14": atr14,
        "atrPercent": atr_percent,
        "macdLine": macd_line,
        "macdSignal": macd_signal,
        "macdHistogram": macd_histogram,
        "stochasticK": stochastic_k,
        "stochasticD": stochastic_d,
        "bollingerMiddle": bollinger_middle,
        "bollingerUpper": bollinger_upper,
        "bollingerLower": bollinger_lower,
        "adx14": adx14,
        "plusDI14": plus_di14,
        "minusDI14": minus_di14,
        "cci20": cci20,
        "williamsR14": williams_r14,
        "roc12": roc12,
        "momentum10": momentum10,
        "obv": obv,
        "mfi14": mfi14,
        "volumeMA20": volume_ma20,
        "averageVolume20": volume_ma20,
        "closeVsEma20": (
            "above"
            if latest_close > ema20
            else "below"
            if latest_close < ema20
            else "equal"
        ) if ema20 is not None else None,
        "trendState": trend_state,
        "series": [
            {
                "time": times[index],
                "sma20": _technical_output_number(sma20_series[index]),
                "sma50": _technical_output_number(sma50_series[index]),
                "sma200": _technical_output_number(sma200_series[index]),
                "ema9": _technical_output_number(ema9_series[index]),
                "ema20": _technical_output_number(ema20_series[index]),
                "ema50": _technical_output_number(ema50_series[index]),
                "ema200": _technical_output_number(ema200_series[index]),
                "rsi14": _technical_output_number(rsi14_series[index]),
                "atr14": _technical_output_number(atr14_series[index]),
                "macdLine": _technical_output_number(macd_line_series[index]),
                "macdSignal": _technical_output_number(macd_signal_series[index]),
                "macdHistogram": _technical_output_number(
                    macd_histogram_series[index]
                ),
                "stochasticK": _technical_output_number(stochastic_k_series[index]),
                "stochasticD": _technical_output_number(stochastic_d_series[index]),
                "bollingerMiddle": _technical_output_number(
                    bollinger_middle_series[index]
                ),
                "bollingerUpper": _technical_output_number(
                    bollinger_upper_series[index]
                ),
                "bollingerLower": _technical_output_number(
                    bollinger_lower_series[index]
                ),
                "adx14": _technical_output_number(adx14_series[index]),
                "plusDI14": _technical_output_number(plus_di14_series[index]),
                "minusDI14": _technical_output_number(minus_di14_series[index]),
                "cci20": _technical_output_number(cci20_series[index]),
                "williamsR14": _technical_output_number(
                    williams_r14_series[index]
                ),
                "roc12": _technical_output_number(roc12_series[index]),
                "momentum10": _technical_output_number(momentum10_series[index]),
                "obv": _technical_output_number(obv_series[index]),
                "mfi14": _technical_output_number(mfi14_series[index]),
                "volumeMA20": _technical_output_number(volume_ma20_series[index]),
            }
            for index in range(len(closes))
        ],
    }


def _price_action_confirmed_pivots(
    bars: list[dict],
    *,
    left: int = 3,
    right: int = 3,
) -> tuple[list[dict], list[dict]]:
    """Return only pivots confirmed by already-closed bars to their right."""
    highs = [float(item["high"]) for item in bars]
    lows = [float(item["low"]) for item in bars]
    high_pivots: list[dict] = []
    low_pivots: list[dict] = []
    for index in range(left, len(bars) - right):
        high = highs[index]
        low = lows[index]
        if all(high > highs[offset] for offset in range(index - left, index)) and all(
            high > highs[offset] for offset in range(index + 1, index + right + 1)
        ):
            high_pivots.append({
                "index": index,
                "time": bars[index]["time"],
                "confirmedAtTime": bars[index + right]["time"],
                "price": _technical_output_number(high),
                "type": "HIGH",
            })
        if all(low < lows[offset] for offset in range(index - left, index)) and all(
            low < lows[offset] for offset in range(index + 1, index + right + 1)
        ):
            low_pivots.append({
                "index": index,
                "time": bars[index]["time"],
                "confirmedAtTime": bars[index + right]["time"],
                "price": _technical_output_number(low),
                "type": "LOW",
            })
    return high_pivots, low_pivots


def _price_action_cluster_levels(
    pivots: list[dict],
    *,
    current_price: float,
    threshold: float,
    side: str,
) -> list[dict]:
    clusters: list[dict] = []
    for pivot in pivots:
        price = float(pivot["price"])
        matching = next(
            (
                cluster
                for cluster in clusters
                if abs(price - float(cluster["price"])) <= threshold
            ),
            None,
        )
        if matching is None:
            clusters.append({
                "price": price,
                "touches": 1,
                "firstTime": pivot["time"],
                "lastTime": pivot["time"],
                "lastConfirmedAtTime": pivot["confirmedAtTime"],
                "pivotTimes": [pivot["time"]],
            })
            continue
        touches = int(matching["touches"])
        matching["price"] = ((float(matching["price"]) * touches) + price) / (touches + 1)
        matching["touches"] = touches + 1
        matching["lastTime"] = pivot["time"]
        matching["lastConfirmedAtTime"] = pivot["confirmedAtTime"]
        matching["pivotTimes"].append(pivot["time"])
    if side == "support":
        clusters = [cluster for cluster in clusters if float(cluster["price"]) <= current_price]
    else:
        clusters = [cluster for cluster in clusters if float(cluster["price"]) >= current_price]
    clusters.sort(
        key=lambda cluster: (
            abs(float(cluster["price"]) - current_price),
            -int(cluster["touches"]),
        )
    )
    return [
        {
            **cluster,
            "price": _technical_output_number(cluster["price"]),
            "distancePercent": _technical_output_number(
                abs(float(cluster["price"]) - current_price) / current_price * 100.0
            ),
        }
        for cluster in clusters[:6]
    ]


def _price_action_trendline(
    pivots: list[dict],
    *,
    kind: str,
    latest_index: int,
    latest_time: int,
) -> dict | None:
    if len(pivots) < 2:
        return None
    first, second = pivots[-2], pivots[-1]
    distance = int(second["index"]) - int(first["index"])
    if distance <= 0:
        return None
    slope = (float(second["price"]) - float(first["price"])) / distance
    epsilon = max(abs(float(second["price"])) * 1e-10, 1e-10)
    direction = "RISING" if slope > epsilon else "FALLING" if slope < -epsilon else "FLAT"
    projected = float(second["price"]) + slope * (latest_index - int(second["index"]))
    return {
        "kind": kind,
        "direction": direction,
        "first": dict(first),
        "second": dict(second),
        "slopePerBar": _technical_output_number(slope),
        "projectedPrice": _technical_output_number(projected),
        "validThroughTime": latest_time,
    }


def _price_action_latest_fibonacci(
    high_pivots: list[dict],
    low_pivots: list[dict],
) -> dict:
    pivots = sorted([*high_pivots, *low_pivots], key=lambda item: int(item["index"]))
    if len(pivots) < 2:
        return {
            "available": False,
            "direction": None,
            "from": None,
            "to": None,
            "range": None,
            "levels": [],
        }
    end = pivots[-1]
    start = next(
        (pivot for pivot in reversed(pivots[:-1]) if pivot["type"] != end["type"]),
        None,
    )
    if start is None:
        return {
            "available": False,
            "direction": None,
            "from": None,
            "to": None,
            "range": None,
            "levels": [],
        }
    direction = "UP" if start["type"] == "LOW" and end["type"] == "HIGH" else "DOWN"
    price_range = abs(float(end["price"]) - float(start["price"]))
    ratios = (
        (0.0, "0%"),
        (0.236, "23.6%"),
        (0.382, "38.2%"),
        (0.5, "50%"),
        (0.618, "61.8%"),
        (0.786, "78.6%"),
        (1.0, "100%"),
    )
    return {
        "available": price_range > 0.0,
        "direction": direction,
        "from": dict(start),
        "to": dict(end),
        "range": _technical_output_number(price_range),
        "levels": [
            {
                "ratio": ratio,
                "label": label,
                "price": _technical_output_number(
                    float(end["price"])
                    + ((float(start["price"]) - float(end["price"])) * ratio)
                ),
            }
            for ratio, label in ratios
        ],
    }


def _price_action_regular_divergence(
    pivots: list[dict],
    oscillator_series: list[float | None],
    *,
    oscillator: str,
    bullish: bool,
) -> dict | None:
    observed = [
        pivot
        for pivot in pivots
        if 0 <= int(pivot["index"]) < len(oscillator_series)
        and oscillator_series[int(pivot["index"])] is not None
    ]
    if len(observed) < 2:
        return None
    first, second = observed[-2], observed[-1]
    first_value = float(oscillator_series[int(first["index"])] or 0.0)
    second_value = float(oscillator_series[int(second["index"])] or 0.0)
    confirmed = (
        float(second["price"]) < float(first["price"])
        and second_value > first_value
        if bullish
        else float(second["price"]) > float(first["price"])
        and second_value < first_value
    )
    if not confirmed:
        return None

    def evidence(pivot: dict, value: float) -> dict:
        return {
            "index": pivot["index"],
            "time": pivot["time"],
            "confirmedAtTime": pivot["confirmedAtTime"],
            "price": pivot["price"],
            "oscillatorValue": _technical_output_number(value),
        }

    return {
        "kind": "REGULAR_BULLISH" if bullish else "REGULAR_BEARISH",
        "oscillator": oscillator,
        "first": evidence(first, first_value),
        "second": evidence(second, second_value),
        "detectedAtTime": second["confirmedAtTime"],
    }


def _price_action_features_snapshot_uncached(
    bars: list[dict],
    technical: dict,
) -> dict:
    series = technical.get("series") if isinstance(technical.get("series"), list) else []
    if technical.get("reasonCode") == "invalid_closed_bar_payload" or not bars or len(series) != len(bars):
        return {
            "available": False,
            "reasonCode": "invalid_closed_bar_payload",
            "basis": "backend_calculated_confirmed_closed_bars_only",
            "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
            "moduleCount": len(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
            "modules": list(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
            "barCount": len(bars),
            "pivotConfig": {"leftBars": 3, "rightBars": 3, "confirmedOnly": True},
            "swings": {"highs": [], "lows": [], "latestHigh": None, "latestLow": None},
            "supportResistance": {"supports": [], "resistances": [], "threshold": None},
            "trendlines": {"support": None, "resistance": None},
            "fibonacci": _price_action_latest_fibonacci([], []),
            "divergences": {
                "rsi": {"bullish": None, "bearish": None},
                "macd": {"bullish": None, "bearish": None},
            },
        }
    high_pivots, low_pivots = _price_action_confirmed_pivots(bars)
    latest_price = float(bars[-1]["close"])
    latest_atr = technical.get("atr14")
    threshold = max(
        (float(latest_atr) * 0.35) if isinstance(latest_atr, (int, float)) else 0.0,
        latest_price * 0.001,
    )
    rsi_series = [item.get("rsi14") if isinstance(item, dict) else None for item in series]
    macd_series = [item.get("macdLine") if isinstance(item, dict) else None for item in series]
    fibonacci = _price_action_latest_fibonacci(high_pivots, low_pivots)
    ready = bool(high_pivots and low_pivots)
    return {
        "available": ready,
        "reasonCode": "ready" if ready else "confirmed_pivot_warmup_incomplete",
        "basis": "backend_calculated_confirmed_closed_bars_only",
        "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
        "moduleCount": len(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
        "modules": list(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
        "barCount": len(bars),
        "latestClosedBarTime": bars[-1]["time"],
        "pivotConfig": {"leftBars": 3, "rightBars": 3, "confirmedOnly": True},
        "swings": {
            "highs": [dict(item) for item in high_pivots[-24:]],
            "lows": [dict(item) for item in low_pivots[-24:]],
            "latestHigh": dict(high_pivots[-1]) if high_pivots else None,
            "latestLow": dict(low_pivots[-1]) if low_pivots else None,
        },
        "supportResistance": {
            "supports": _price_action_cluster_levels(
                low_pivots,
                current_price=latest_price,
                threshold=threshold,
                side="support",
            ),
            "resistances": _price_action_cluster_levels(
                high_pivots,
                current_price=latest_price,
                threshold=threshold,
                side="resistance",
            ),
            "threshold": _technical_output_number(threshold),
        },
        "trendlines": {
            "support": _price_action_trendline(
                low_pivots,
                kind="support",
                latest_index=len(bars) - 1,
                latest_time=bars[-1]["time"],
            ),
            "resistance": _price_action_trendline(
                high_pivots,
                kind="resistance",
                latest_index=len(bars) - 1,
                latest_time=bars[-1]["time"],
            ),
        },
        "fibonacci": fibonacci,
        "divergences": {
            "rsi": {
                "bullish": _price_action_regular_divergence(
                    low_pivots,
                    rsi_series,
                    oscillator="RSI14",
                    bullish=True,
                ),
                "bearish": _price_action_regular_divergence(
                    high_pivots,
                    rsi_series,
                    oscillator="RSI14",
                    bullish=False,
                ),
            },
            "macd": {
                "bullish": _price_action_regular_divergence(
                    low_pivots,
                    macd_series,
                    oscillator="MACD_LINE",
                    bullish=True,
                ),
                "bearish": _price_action_regular_divergence(
                    high_pivots,
                    macd_series,
                    oscillator="MACD_LINE",
                    bullish=False,
                ),
            },
        },
    }


def _ai_trade_council_analysis_cache_key(bars: list[dict]) -> str:
    canonical = json.dumps(
        bars,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(
        AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION.encode("ascii") + b"\0" + canonical
    ).hexdigest()


def _ai_trade_council_analysis_feature_bundle(bars: list[dict]) -> dict[str, dict]:
    try:
        cache_key = _ai_trade_council_analysis_cache_key(bars)
    except (TypeError, ValueError, OverflowError):
        technical = _technical_indicator_snapshot_uncached(bars)
        return {
            "technicalIndicators": technical,
            "priceActionFeatures": _price_action_features_snapshot_uncached(
                bars,
                technical,
            ),
        }
    with AI_TRADE_COUNCIL_ANALYSIS_CACHE_LOCK:
        cached = AI_TRADE_COUNCIL_ANALYSIS_CACHE.get(cache_key)
        if cached is not None:
            return copy.deepcopy(cached)
    technical = _technical_indicator_snapshot_uncached(bars)
    price_action = _price_action_features_snapshot_uncached(bars, technical)
    bundle = {
        "technicalIndicators": technical,
        "priceActionFeatures": price_action,
    }
    with AI_TRADE_COUNCIL_ANALYSIS_CACHE_LOCK:
        AI_TRADE_COUNCIL_ANALYSIS_CACHE[cache_key] = copy.deepcopy(bundle)
        while len(AI_TRADE_COUNCIL_ANALYSIS_CACHE) > AI_TRADE_COUNCIL_ANALYSIS_CACHE_MAX_ENTRIES:
            AI_TRADE_COUNCIL_ANALYSIS_CACHE.pop(next(iter(AI_TRADE_COUNCIL_ANALYSIS_CACHE)))
    return copy.deepcopy(bundle)


def _technical_indicator_snapshot(bars: list[dict]) -> dict:
    return _ai_trade_council_analysis_feature_bundle(bars)["technicalIndicators"]


def _price_action_features_snapshot(bars: list[dict]) -> dict:
    return _ai_trade_council_analysis_feature_bundle(bars)["priceActionFeatures"]


def _valid_ai_trade_council_analysis_bar_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return (
        value
        if value in AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS
        else None
    )


def _configured_ai_trade_council_analysis_bar_count() -> int:
    try:
        store = load_ai_trade_council_automation_store()
        configured = _valid_ai_trade_council_analysis_bar_count(
            (store.get("config") or {}).get("analysisBarCount")
        )
    except (DataIntegrityError, OSError, TypeError, ValueError):
        configured = None
    return configured or AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT


def _valid_ai_trade_council_required_votes(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value in AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES else None


def _configured_ai_trade_council_required_votes() -> int:
    try:
        store = load_ai_trade_council_automation_store()
        configured = _valid_ai_trade_council_required_votes(
            (store.get("config") or {}).get("requiredVotes")
        )
    except (DataIntegrityError, OSError, TypeError, ValueError):
        configured = None
    return configured or AI_TRADE_COUNCIL_DEFAULT_REQUIRED_VOTES


def _ai_trade_council_analysis_window(
    bars: list[dict],
    requested_bars: int,
) -> tuple[list[dict], dict]:
    """Select one exact closed-bar suffix without silently reducing its size."""
    source_bar_count = len(bars)
    enough_bars = source_bar_count >= requested_bars
    selected = list(bars[-requested_bars:]) if enough_bars else []
    return selected, {
        "requestedBars": requested_bars,
        "usedBars": len(selected),
        "startTime": selected[0].get("time") if selected else None,
        "endTime": selected[-1].get("time") if selected else None,
        "closedBarsOnly": True,
        "sourceBarCount": source_bar_count,
        "indicatorFormulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
        "status": "ready" if enough_bars else "insufficient_closed_bars",
    }


def _ai_trade_council_dashboard_feature_state(
    bars: list[dict],
    requested_bars: int,
) -> dict:
    """Keep Dashboard drawing data full-size while bounding the Codex window."""
    analysis_bars, analysis_window = _ai_trade_council_analysis_window(
        bars,
        requested_bars,
    )
    display_features = _ai_trade_council_analysis_feature_bundle(bars)
    for feature in display_features.values():
        feature.update({
            "scope": "dashboard_source_window",
            "sourceBarCount": len(bars),
            "requestedBarCount": requested_bars,
            "analysisBarCount": len(analysis_bars),
            "seriesBarCount": len(bars),
        })
    analysis_features = _ai_trade_council_analysis_feature_bundle(
        analysis_bars if analysis_bars else []
    )
    analysis_technical = analysis_features["technicalIndicators"]
    if not analysis_bars:
        analysis_technical.update({
            "available": False,
            "reasonCode": "insufficient_closed_bars",
            "barCount": 0,
            "sourceBarCount": len(bars),
            "requestedBarCount": requested_bars,
        })
    analysis_window_ready = bool(
        len(analysis_bars) == requested_bars
        and analysis_technical.get("available") is True
    )
    return {
        "displayFeatures": display_features,
        "analysisFeatures": analysis_features,
        "analysisBars": analysis_bars,
        "analysisWindow": analysis_window,
        "analysisWindowReady": analysis_window_ready,
    }


def _ai_trade_council_windowed_snapshot(
    snapshot_model: dict,
    requested_bars: int,
) -> dict:
    """Build the immutable analysis view while retaining the source snapshot id."""
    chart = (
        snapshot_model.get("chartSnapshot")
        if isinstance(snapshot_model.get("chartSnapshot"), dict)
        else {}
    )
    source_bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    selected_bars, analysis_window = _ai_trade_council_analysis_window(
        source_bars,
        requested_bars,
    )
    if len(selected_bars) != requested_bars:
        raise RequestError(
            (
                f"ข้อมูลแท่งปิดมี {len(source_bars)} แท่ง แต่ตั้งให้วิเคราะห์ "
                f"{requested_bars} แท่ง กรุณาเพิ่ม SnapshotBars ใน EA "
                "หรือเลือกลดจำนวนแท่งก่อนเริ่มวิเคราะห์"
            ),
            409,
        )
    analysis_features = _ai_trade_council_analysis_feature_bundle(selected_bars)
    for feature in analysis_features.values():
        feature.update({
            "scope": "codex_analysis_window",
            "sourceBarCount": len(source_bars),
            "requestedBarCount": requested_bars,
            "seriesBarCount": len(selected_bars),
        })
    windowed_chart = {
        **chart,
        "sourceBarCount": len(source_bars),
        "barCount": len(selected_bars),
        "bars": selected_bars,
        "analysisWindow": analysis_window,
        **analysis_features,
    }
    return {
        **snapshot_model,
        "chartSnapshot": windowed_chart,
        "analysisWindow": analysis_window,
        "sourceBarCount": len(source_bars),
        "analysisBarCount": len(selected_bars),
        "indicatorFormulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
    }


def _snapshot_has_forbidden_keys(value: object) -> bool:
    forbidden = {
        "account",
        "accountid",
        "accountlogin",
        "accountnumber",
        "brokerserver",
        "password",
        "investorpassword",
        "token",
        "secret",
        "cookie",
        "terminalpath",
        "processid",
        "pid",
        "ticket",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized_key in forbidden:
                return True
            if _snapshot_has_forbidden_keys(item):
                return True
    elif isinstance(value, list):
        return any(_snapshot_has_forbidden_keys(item) for item in value[:1000])
    return False


def _empty_metatrader_snapshot_read_model(
    prop_id: str,
    status: str,
    reason_code: str,
    *,
    selected_candidate: dict | None = None,
) -> dict:
    candidate_id = safe_reference((selected_candidate or {}).get("candidateId"))
    platform = str((selected_candidate or {}).get("platform") or "") or None
    source_ready = METATRADER_SNAPSHOT_SOURCE_PATH.is_file()
    requested_analysis_bars = _configured_ai_trade_council_analysis_bar_count()
    empty_analysis_window = {
        "requestedBars": requested_analysis_bars,
        "usedBars": 0,
        "startTime": None,
        "endTime": None,
        "closedBarsOnly": True,
        "sourceBarCount": 0,
        "indicatorFormulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
        "status": "waiting_snapshot",
    }
    analysis_agents = [
        {
            "agentId": "optimization_agent",
            "roleId": "technical",
            "labelTh": "วิเคราะห์ Indicator และ Technical Signal เท่านั้น",
            "ready": False,
        },
        {
            "agentId": "backtest_analyst",
            "roleId": "price_action",
            "labelTh": "วิเคราะห์กราฟเปล่า โครงสร้างราคา Trendline แนวรับแนวต้าน และ HMC/ICT",
            "ready": False,
        },
        {
            "agentId": "codex_mcp_operator",
            "roleId": "news",
            "labelTh": "วิเคราะห์ข่าวและสถานการณ์ระยะสั้น กลาง และยาว",
            "ready": False,
        },
    ]
    return {
        "schemaVersion": "metafx-hq-mt4-read-model-v1",
        "propId": prop_id,
        "selectedCandidateId": candidate_id,
        "selectedPlatform": platform,
        "adapter": {
            "available": True,
            "ready": False,
            "status": status,
            "mode": "read_only",
            "source": "mt4_file_common_snapshot",
            "freshnessSeconds": METATRADER_SNAPSHOT_FRESH_SECONDS,
            "reasonCode": reason_code,
            "orderSubmissionAvailable": False,
        },
        "installPreparation": {
            "sourceReady": source_ready,
            "sourceAsset": "integrations/mt4-trade-gateway/MetafxHQTradeGateway.mq4",
            "sourceDisplayName": "MetafxHQ AI Council EA",
            "installKind": "expert_advisor",
            "defaultGatewayMode": "shadow",
            "provides": ["snapshot_telemetry", "guarded_trade_command_gateway"],
            "fallbackSourceAsset": "integrations/mt4-readonly/MetafxHQReadOnlySnapshot.mq4",
            "snapshotChannel": candidate_id,
            "requiresVisibleAttach": True,
            "automaticAttachAvailable": False,
        },
        "dailySummary": {
            "available": False,
            "status": status,
            "reasonCode": reason_code,
            "basis": "broker_server_day",
            "serverDay": None,
            "currency": None,
            "realizedProfit": None,
            "floatingProfit": None,
            "netPnl": None,
            "balance": None,
            "equity": None,
            "tradesClosed": None,
            "wins": None,
            "losses": None,
            "openPositions": None,
        },
        "chartSnapshot": {
            "available": False,
            "status": status,
            "reasonCode": reason_code,
            "snapshotId": None,
            "observedAt": None,
            "ageSeconds": None,
            "symbol": None,
            "timeframe": None,
            "bid": None,
            "ask": None,
            "spreadPoints": None,
            "barCount": 0,
            "sourceBarCount": 0,
            "bars": [],
            "analysisWindow": empty_analysis_window,
            "technicalIndicators": {
                "available": False,
                "reasonCode": "waiting_snapshot",
                "basis": "backend_calculated_closed_bars_only",
                "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
                "scope": "dashboard_source_window",
                "barCount": 0,
                "sourceBarCount": 0,
                "requestedBarCount": requested_analysis_bars,
                "analysisBarCount": 0,
                "seriesBarCount": 0,
                "series": [],
            },
            "priceActionFeatures": {
                "available": False,
                "reasonCode": "waiting_snapshot",
                "basis": "backend_calculated_confirmed_closed_bars_only",
                "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
                "scope": "dashboard_source_window",
                "moduleCount": len(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
                "modules": list(AI_TRADE_COUNCIL_PRICE_ACTION_MODULES),
                "barCount": 0,
                "sourceBarCount": 0,
                "requestedBarCount": requested_analysis_bars,
                "analysisBarCount": 0,
                "seriesBarCount": 0,
                "pivotConfig": {"leftBars": 3, "rightBars": 3, "confirmedOnly": True},
                "swings": {"highs": [], "lows": [], "latestHigh": None, "latestLow": None},
                "supportResistance": {"supports": [], "resistances": [], "threshold": None},
                "trendlines": {"support": None, "resistance": None},
                "fibonacci": {
                    "available": False,
                    "direction": None,
                    "from": None,
                    "to": None,
                    "range": None,
                    "levels": [],
                },
                "divergences": {
                    "rsi": {"bullish": None, "bearish": None},
                    "macd": {"bullish": None, "bearish": None},
                },
            },
        },
        "analysisReadiness": {
            "available": False,
            "status": "waiting_snapshot",
            "snapshotId": None,
            "sourceBarCount": 0,
            "analysisBarCount": 0,
            "requestedAnalysisBarCount": requested_analysis_bars,
            "analysisWindow": empty_analysis_window,
            "indicatorFormulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
            "managerAgentId": "manager",
            "riskGuardAgentId": "risk_guard",
            "riskGuardVoting": False,
            "agentCount": 3,
            "agents": analysis_agents,
            "liveOrderActionAvailable": False,
        },
    }


def _metatrader_snapshot_file(candidate_id: str) -> Path | None:
    if not candidate_id.startswith("mtc-") or not SAFE_ID_PATTERN.fullmatch(candidate_id):
        return None
    common_root = METATRADER_COMMON_FILES_DIR.resolve(strict=False)
    snapshot_path = (common_root / "MetafxHQ" / candidate_id / "snapshot.json").resolve(strict=False)
    try:
        snapshot_path.relative_to(common_root)
    except ValueError:
        return None
    return snapshot_path


def _legacy_metatrader_snapshot_file(record: dict, candidate_id: str) -> Path | None:
    """Resolve only the selected terminal's old MQL4/Files snapshot location."""
    if not candidate_id.startswith("mtc-") or not SAFE_ID_PATTERN.fullmatch(candidate_id):
        return None
    data_path_value = str(record.get("dataPath") or "").strip()
    local_path_value = str(record.get("localPath") or "").strip()
    if not data_path_value or not local_path_value:
        return None
    try:
        data_path = Path(data_path_value).resolve(strict=False)
        local_path = Path(local_path_value).resolve(strict=False)
        if (
            data_path != local_path
            or not data_path.is_dir()
            or not (data_path / "MQL4").is_dir()
        ):
            return None
        files_root = (data_path / "MQL4" / "Files").resolve(strict=False)
        snapshot_path = (
            files_root
            / "MetafxHQ"
            / candidate_id
            / "snapshot.json"
        ).resolve(strict=False)
        snapshot_path.relative_to(files_root)
    except (OSError, PermissionError, RuntimeError, ValueError):
        return None
    return snapshot_path


def _metatrader_snapshot_source_files(
    record: dict,
    candidate_id: str,
) -> list[tuple[str, Path]]:
    sources = []
    common_path = _metatrader_snapshot_file(candidate_id)
    if common_path is not None:
        sources.append(("mt4_file_common_snapshot", common_path))
    legacy_path = _legacy_metatrader_snapshot_file(record, candidate_id)
    if legacy_path is not None and legacy_path != common_path:
        sources.append(("mt4_terminal_local_snapshot_legacy", legacy_path))
    return sources


def metatrader_snapshot_read_model(prop_id: str) -> dict:
    record = _selected_metatrader_candidate_record(prop_id)
    if not record:
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "not_selected",
            "selected_terminal_missing",
        )
    candidate_public = _public_metatrader_candidate(record)
    if not candidate_public:
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "not_selected",
            "selected_terminal_missing",
        )
    if candidate_public.get("platform") != "mt4":
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "unsupported_platform",
            "mt4_snapshot_adapter_required",
            selected_candidate=candidate_public,
        )
    candidate_id = str(candidate_public["candidateId"])
    snapshot_sources = _metatrader_snapshot_source_files(record, candidate_id)
    if not snapshot_sources:
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "invalid_channel",
            "snapshot_channel_invalid",
            selected_candidate=candidate_public,
        )
    observed_sources = []
    unreadable_source = False
    for source_name, source_path in snapshot_sources:
        try:
            source_stat = source_path.stat()
        except FileNotFoundError:
            continue
        except (OSError, PermissionError):
            unreadable_source = True
            continue
        try:
            source_is_file = source_path.is_file()
        except (OSError, PermissionError):
            unreadable_source = True
            continue
        if source_is_file:
            observed_sources.append((
                source_stat.st_mtime_ns,
                source_name == "mt4_file_common_snapshot",
                source_name,
                source_path,
                source_stat,
            ))
    if not observed_sources and not unreadable_source:
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "awaiting_snapshot",
            "snapshot_not_observed",
            selected_candidate=candidate_public,
        )
    if not observed_sources:
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "unavailable",
            "snapshot_unreadable",
            selected_candidate=candidate_public,
        )
    _, _, snapshot_source, snapshot_path, snapshot_stat = max(observed_sources)
    size = snapshot_stat.st_size
    if size <= 0 or size > METATRADER_SNAPSHOT_MAX_BYTES:
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "invalid_snapshot",
            "snapshot_size_invalid",
            selected_candidate=candidate_public,
        )
    try:
        raw = snapshot_path.read_bytes()
        payload = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "invalid_snapshot",
            "snapshot_json_invalid",
            selected_candidate=candidate_public,
        )
    if (
        not isinstance(payload, dict)
        or payload.get("schemaVersion") != METATRADER_SNAPSHOT_SCHEMA_VERSION
        or payload.get("adapterId") != candidate_id
        or payload.get("mode") != "read_only"
        or _snapshot_has_forbidden_keys(payload)
    ):
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "invalid_snapshot",
            "snapshot_schema_invalid",
            selected_candidate=candidate_public,
        )
    try:
        modified_at = datetime.fromtimestamp(snapshot_stat.st_mtime, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "invalid_snapshot",
            "snapshot_timestamp_invalid",
            selected_candidate=candidate_public,
        )
    age_seconds = max(0.0, (datetime.now(timezone.utc) - modified_at).total_seconds())
    snapshot_id = hashlib.sha256(raw).hexdigest()
    chart = payload.get("chart") if isinstance(payload.get("chart"), dict) else {}
    daily = payload.get("daily") if isinstance(payload.get("daily"), dict) else {}
    account_summary = payload.get("accountSummary") if isinstance(payload.get("accountSummary"), dict) else {}
    positions = payload.get("positionsSummary") if isinstance(payload.get("positionsSummary"), dict) else {}
    symbol = _safe_snapshot_symbol(chart.get("symbol"))
    timeframe = _safe_snapshot_timeframe(chart.get("timeframe"))
    bid = _safe_snapshot_number(chart.get("bid"), minimum=0)
    ask = _safe_snapshot_number(chart.get("ask"), minimum=0)
    spread_points = _safe_snapshot_number(chart.get("spreadPoints"), minimum=0, maximum=1.0e7)
    raw_bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    bars = []
    for item in raw_bars[-METATRADER_SNAPSHOT_MAX_BARS:]:
        if not isinstance(item, dict):
            continue
        epoch = _safe_snapshot_count(item.get("time"), maximum=4_102_444_800)
        open_value = _safe_snapshot_number(item.get("open"), minimum=0)
        high_value = _safe_snapshot_number(item.get("high"), minimum=0)
        low_value = _safe_snapshot_number(item.get("low"), minimum=0)
        close_value = _safe_snapshot_number(item.get("close"), minimum=0)
        volume = _safe_snapshot_number(item.get("volume"), minimum=0)
        if (
            epoch is None
            or None in {open_value, high_value, low_value, close_value, volume}
            or high_value < max(open_value, close_value, low_value)
            or low_value > min(open_value, close_value, high_value)
        ):
            continue
        bars.append({
            "time": epoch,
            "open": open_value,
            "high": high_value,
            "low": low_value,
            "close": close_value,
            "volume": volume,
        })
    required_numbers = {
        "realizedProfit": _safe_snapshot_number(daily.get("realizedProfit")),
        "floatingProfit": _safe_snapshot_number(daily.get("floatingProfit")),
        "netPnl": _safe_snapshot_number(daily.get("netPnl")),
        "balance": _safe_snapshot_number(account_summary.get("balance")),
        "equity": _safe_snapshot_number(account_summary.get("equity")),
    }
    server_day = str(daily.get("serverDay") or "")
    currency = str(account_summary.get("currency") or "").strip().upper()
    daily_valid = (
        re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", server_day) is not None
        and re.fullmatch(r"[A-Z0-9]{1,8}", currency) is not None
        and all(value is not None for value in required_numbers.values())
    )
    chart_valid = bool(symbol and timeframe and bid is not None and ask is not None and bars)
    snapshot_fresh = age_seconds <= METATRADER_SNAPSHOT_FRESH_SECONDS
    if not chart_valid or not daily_valid:
        return _empty_metatrader_snapshot_read_model(
            prop_id,
            "invalid_snapshot",
            "snapshot_payload_invalid",
            selected_candidate=candidate_public,
        )
    status = "ready" if snapshot_fresh else "stale"
    reason_code = "ready" if snapshot_fresh else "snapshot_stale"
    result = _empty_metatrader_snapshot_read_model(
        prop_id,
        status,
        reason_code,
        selected_candidate=candidate_public,
    )
    result["adapter"].update({
        "ready": snapshot_fresh,
        "status": status,
        "reasonCode": reason_code,
        "source": snapshot_source,
        "legacyFallback": snapshot_source == "mt4_terminal_local_snapshot_legacy",
        "migrationNeeded": snapshot_source == "mt4_terminal_local_snapshot_legacy",
        "observedAt": modified_at.isoformat().replace("+00:00", "Z"),
        "ageSeconds": round(age_seconds, 1),
    })
    result["dailySummary"] = {
        "available": snapshot_fresh,
        "status": status,
        "reasonCode": reason_code,
        "basis": "broker_server_day",
        "serverDay": server_day,
        "currency": currency,
        **required_numbers,
        "tradesClosed": _safe_snapshot_count(daily.get("tradesClosed")),
        "wins": _safe_snapshot_count(daily.get("wins")),
        "losses": _safe_snapshot_count(daily.get("losses")),
        "openPositions": _safe_snapshot_count(positions.get("count")),
    }
    requested_analysis_bars = _configured_ai_trade_council_analysis_bar_count()
    feature_state = _ai_trade_council_dashboard_feature_state(
        bars,
        requested_analysis_bars,
    )
    analysis_bars = feature_state["analysisBars"]
    analysis_window = feature_state["analysisWindow"]
    display_features = feature_state["displayFeatures"]
    technical_indicators = display_features["technicalIndicators"]
    price_action_features = display_features["priceActionFeatures"]
    analysis_window_ready = feature_state["analysisWindowReady"]
    result["chartSnapshot"] = {
        "available": snapshot_fresh,
        "status": status,
        "reasonCode": reason_code,
        "snapshotId": snapshot_id,
        "observedAt": modified_at.isoformat().replace("+00:00", "Z"),
        "ageSeconds": round(age_seconds, 1),
        "symbol": symbol,
        "timeframe": timeframe,
        "bid": bid,
        "ask": ask,
        "spreadPoints": spread_points,
        "marketOpen": chart.get("marketOpen") if isinstance(chart.get("marketOpen"), bool) else None,
        "marketSession": (
            redact_text(str(chart.get("marketSession") or ""), 80) or None
        ),
        "barCount": len(bars),
        "sourceBarCount": len(bars),
        "bars": bars,
        "analysisWindow": analysis_window,
        "technicalIndicators": technical_indicators,
        "priceActionFeatures": price_action_features,
    }
    analysis_agents = result["analysisReadiness"]["agents"]
    for agent in analysis_agents:
        agent["ready"] = snapshot_fresh and analysis_window_ready
    result["analysisReadiness"].update({
        "available": snapshot_fresh and analysis_window_ready,
        "status": (
            "snapshot_stale"
            if not snapshot_fresh
            else "ready_for_manual_analysis"
            if analysis_window_ready
            else "insufficient_closed_bars"
        ),
        "snapshotId": snapshot_id,
        "sourceBarCount": len(bars),
        "analysisBarCount": len(analysis_bars),
        "requestedAnalysisBarCount": requested_analysis_bars,
        "analysisWindow": analysis_window,
        "indicatorFormulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
    })
    return result


AI_TRADE_COUNCIL_AGENT_ROLES = {
    "optimization_agent": "technical",
    "backtest_analyst": "price_action",
    "codex_mcp_operator": "news",
}
AI_TRADE_COUNCIL_ALLOWED_TOOLS = {
    "optimization_agent": "codex_cli_task",
    "backtest_analyst": "codex_cli_task",
    "codex_mcp_operator": "codex_web_research",
}


def _ai_trade_council_deep_analysis_snapshot_metadata(chart: dict) -> dict:
    bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    latest_closed_bar_time = (
        bars[-1].get("time")
        if bars and isinstance(bars[-1], dict)
        else None
    )
    snapshot_id = str(chart.get("snapshotId") or "")
    return {
        "snapshotId": (
            snapshot_id
            if re.fullmatch(r"[0-9a-f]{64}", snapshot_id)
            else None
        ),
        "observedAt": redact_text(str(chart.get("observedAt") or ""), 120) or None,
        "ageSeconds": _safe_snapshot_number(
            chart.get("ageSeconds"),
            minimum=0,
            maximum=31_536_000,
        ),
        "symbol": _safe_snapshot_symbol(chart.get("symbol")),
        "timeframe": _safe_snapshot_timeframe(chart.get("timeframe")),
        "bid": _safe_snapshot_number(chart.get("bid"), minimum=0),
        "ask": _safe_snapshot_number(chart.get("ask"), minimum=0),
        "spreadPoints": _safe_snapshot_number(
            chart.get("spreadPoints"),
            minimum=0,
            maximum=1.0e7,
        ),
        "marketOpen": (
            chart.get("marketOpen")
            if isinstance(chart.get("marketOpen"), bool)
            else None
        ),
        "marketSession": (
            redact_text(str(chart.get("marketSession") or ""), 80) or None
        ),
        "latestClosedBarTime": latest_closed_bar_time,
        "sourceAvailable": (
            chart.get("available")
            if isinstance(chart.get("available"), bool)
            else None
        ),
        "sourceStatus": redact_text(str(chart.get("status") or ""), 80) or None,
        "sourceReasonCode": (
            redact_text(str(chart.get("reasonCode") or ""), 120) or None
        ),
    }


def _ai_trade_council_deep_analysis_daily_summary(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    allowed_fields = (
        "available",
        "status",
        "reasonCode",
        "basis",
        "serverDay",
        "currency",
        "realizedProfit",
        "floatingProfit",
        "netPnl",
        "balance",
        "equity",
        "tradesClosed",
        "wins",
        "losses",
        "openPositions",
    )
    return {
        key: sanitize_json_value(source.get(key))
        for key in allowed_fields
        if key in source
    }


def _ai_trade_council_deep_analysis_bars(value: object) -> list[dict]:
    source = value if isinstance(value, list) else []
    bars = []
    previous_time = 0
    for item in source[-METATRADER_SNAPSHOT_MAX_BARS:]:
        if not isinstance(item, dict):
            return []
        epoch = _safe_snapshot_count(item.get("time"), maximum=4_102_444_800)
        open_value = _safe_snapshot_number(item.get("open"), minimum=0)
        high_value = _safe_snapshot_number(item.get("high"), minimum=0)
        low_value = _safe_snapshot_number(item.get("low"), minimum=0)
        close_value = _safe_snapshot_number(item.get("close"), minimum=0)
        volume = _safe_snapshot_number(item.get("volume"), minimum=0)
        if (
            epoch is None
            or epoch <= previous_time
            or None in {open_value, high_value, low_value, close_value, volume}
            or high_value < max(open_value, close_value, low_value)
            or low_value > min(open_value, close_value, high_value)
        ):
            return []
        previous_time = epoch
        bars.append({
            "time": epoch,
            "open": open_value,
            "high": high_value,
            "low": low_value,
            "close": close_value,
            "volume": volume,
        })
    return bars


def _ai_trade_council_deep_analysis_news_vote(
    value: object,
    *,
    source_mission_id: str | None,
    source_updated_at: str | None,
    current_snapshot_id: str | None,
) -> dict | None:
    vote = value if isinstance(value, dict) else None
    if not vote:
        return None
    snapshot_id = str(vote.get("snapshotId") or "")
    decision = str(vote.get("decision") or "").upper()
    confidence = _safe_snapshot_number(vote.get("confidence"), minimum=0, maximum=100)
    if (
        vote.get("schemaVersion") != "ai-trade-council-vote-v3"
        or vote.get("readOnly") is not True
        or vote.get("agentId") != "codex_mcp_operator"
        or vote.get("roleId") != "news"
        or not re.fullmatch(r"[0-9a-f]{64}", snapshot_id)
        or decision not in {"BUY", "HOLD", "SELL", "NO_DATA"}
        or confidence is None
    ):
        return None
    observations = []
    for item in vote.get("observations") if isinstance(vote.get("observations"), list) else []:
        safe_text = _ai_trade_council_chat_safe_text(item, 600)
        if safe_text:
            observations.append(safe_text)
        if len(observations) == 5:
            break
    warnings = []
    for item in vote.get("warnings") if isinstance(vote.get("warnings"), list) else []:
        safe_text = _ai_trade_council_chat_safe_text(item, 600)
        if safe_text:
            warnings.append(safe_text)
        if len(warnings) == 5:
            break
    evidence = []
    for item in vote.get("evidence") if isinstance(vote.get("evidence"), list) else []:
        if not isinstance(item, dict):
            continue
        label = _ai_trade_council_chat_safe_text(item.get("label"), 500)
        source_url = _ai_trade_council_public_url(
            item.get("sourceUrl") or item.get("url")
        )
        observed_at, _ = _ai_trade_council_chat_timestamp(item.get("observedAt"))
        if label and source_url:
            evidence.append({
                "label": label,
                "observedAt": observed_at,
                "sourceUrl": source_url,
            })
        if len(evidence) == 8:
            break
    raw_news_evidence = (
        vote.get("newsEvidence")
        if isinstance(vote.get("newsEvidence"), dict)
        else {}
    )
    return {
        "available": True,
        "status": (
            "ready"
            if snapshot_id == current_snapshot_id
            else "latest_vote_for_different_snapshot"
        ),
        "reasonCode": (
            "matching_snapshot"
            if snapshot_id == current_snapshot_id
            else "snapshot_mismatch"
        ),
        "usableForCurrentSnapshot": snapshot_id == current_snapshot_id,
        "sourceMissionId": source_mission_id,
        "sourceUpdatedAt": source_updated_at,
        "snapshotId": snapshot_id,
        "decision": decision,
        "confidence": confidence,
        "eventRisk": (
            str(vote.get("eventRisk") or "").upper()
            if str(vote.get("eventRisk") or "").upper() in {"ALLOW", "HOLD", "VETO"}
            else None
        ),
        "horizonBars": _safe_snapshot_count(vote.get("horizonBars"), maximum=20),
        "validUntilBarTime": _safe_snapshot_count(
            vote.get("validUntilBarTime"),
            maximum=4_102_444_800,
        ),
        "observations": observations,
        "evidence": evidence,
        "warnings": warnings,
        "newsEvidence": {
            "fresh": (
                raw_news_evidence.get("fresh")
                if isinstance(raw_news_evidence.get("fresh"), bool)
                else None
            ),
            "distinctDomains": _safe_snapshot_count(
                raw_news_evidence.get("distinctDomains"),
                maximum=100,
            ),
            "requiredDistinctDomains": _safe_snapshot_count(
                raw_news_evidence.get("requiredDistinctDomains"),
                maximum=100,
            ),
            "reasonCodes": [
                redact_text(str(item), 120)
                for item in (
                    raw_news_evidence.get("reasonCodes")
                    if isinstance(raw_news_evidence.get("reasonCodes"), list)
                    else []
                )[:8]
                if str(item).strip()
            ],
        },
        "readOnly": True,
    }


def _latest_ai_trade_council_deep_analysis_news(
    current_snapshot_id: str | None,
) -> dict:
    try:
        missions = load_missions()
    except (DataIntegrityError, OSError):
        return {
            "available": False,
            "status": "unavailable",
            "reasonCode": "council_store_unavailable",
            "usableForCurrentSnapshot": False,
            "readOnly": True,
        }
    candidates: list[tuple[datetime, dict]] = []
    for mission in missions:
        if not isinstance(mission, dict):
            continue
        context = (
            mission.get("analysisContext")
            if isinstance(mission.get("analysisContext"), dict)
            else {}
        )
        if (
            context.get("kind") != "ai_trade_council_vote"
            or context.get("roleId") != "news"
            or mission.get("owner") != "codex_mcp_operator"
            or mission.get("status") not in {"completed", "archived"}
        ):
            continue
        source_updated_at, source_time = _ai_trade_council_chat_timestamp(
            mission.get("completedAt")
            or mission.get("updatedAt")
            or mission.get("createdAt")
        )
        news = _ai_trade_council_deep_analysis_news_vote(
            mission.get("councilVote"),
            source_mission_id=safe_reference(mission.get("id")),
            source_updated_at=source_updated_at,
            current_snapshot_id=current_snapshot_id,
        )
        if news and source_time:
            candidates.append((source_time, news))
    if not candidates:
        return {
            "available": False,
            "status": "unavailable",
            "reasonCode": "news_vote_unavailable",
            "usableForCurrentSnapshot": False,
            "readOnly": True,
        }
    return max(candidates, key=lambda item: item[0])[1]


def _ai_trade_council_deep_analysis_unavailable(
    status: str,
    reason_code: str,
    *,
    chart: dict | None = None,
    source_bar_count: int = 0,
) -> dict:
    chart = chart if isinstance(chart, dict) else {}
    metadata = _ai_trade_council_deep_analysis_snapshot_metadata(chart)
    return {
        "schemaVersion": "ai-trade-council-deep-analysis-v1",
        "available": False,
        "status": redact_text(status, 80),
        "reasonCode": redact_text(reason_code, 120),
        "fresh": False,
        "decisionEligible": False,
        "snapshot": metadata,
        "sourceBarCount": max(0, int(source_bar_count)),
        "minimumSourceBarCount": AI_TRADE_COUNCIL_DEEP_ANALYSIS_MIN_SOURCE_BARS,
        "analysisBarCount": 0,
        "requestedAnalysisBarCount": AI_TRADE_COUNCIL_DEEP_ANALYSIS_BAR_COUNT,
        "warmupBarsUsed": 0,
        "analysisWindow": None,
        "bars": [],
        "technicalIndicators": {
            "available": False,
            "reasonCode": redact_text(reason_code, 120),
            "series": [],
        },
        "priceActionFeatures": {
            "available": False,
            "reasonCode": redact_text(reason_code, 120),
        },
        "news": _latest_ai_trade_council_deep_analysis_news(
            metadata.get("snapshotId")
        ),
        "readOnly": True,
        "generatedAt": utc_now(),
    }


def _ai_trade_council_deep_analysis_from_snapshot(snapshot_model: object) -> dict:
    source = snapshot_model if isinstance(snapshot_model, dict) else {}
    chart = source.get("chartSnapshot") if isinstance(source.get("chartSnapshot"), dict) else {}
    source_bars = _ai_trade_council_deep_analysis_bars(chart.get("bars"))
    source_bar_count = len(source_bars)
    chart_status = str(chart.get("status") or "")
    inspectable_snapshot = chart_status in {"ready", "stale"}
    if not inspectable_snapshot:
        return _ai_trade_council_deep_analysis_unavailable(
            str(chart.get("status") or source.get("status") or "unavailable"),
            str(chart.get("reasonCode") or source.get("reasonCode") or "snapshot_unavailable"),
            chart=chart,
            source_bar_count=source_bar_count,
        )
    metadata = _ai_trade_council_deep_analysis_snapshot_metadata(chart)
    if not metadata.get("snapshotId"):
        return _ai_trade_council_deep_analysis_unavailable(
            "invalid_snapshot",
            "snapshot_id_invalid",
            chart=chart,
            source_bar_count=source_bar_count,
        )
    raw_source_bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    if not source_bars or len(source_bars) != len(raw_source_bars):
        return _ai_trade_council_deep_analysis_unavailable(
            "invalid_snapshot",
            "closed_bar_payload_invalid",
            chart=chart,
            source_bar_count=source_bar_count,
        )
    if source_bar_count < AI_TRADE_COUNCIL_DEEP_ANALYSIS_MIN_SOURCE_BARS:
        return _ai_trade_council_deep_analysis_unavailable(
            "insufficient_closed_bars",
            "minimum_500_closed_bars_required",
            chart=chart,
            source_bar_count=source_bar_count,
        )

    source_features = _ai_trade_council_analysis_feature_bundle(source_bars)
    source_technical = source_features.get("technicalIndicators")
    source_technical = source_technical if isinstance(source_technical, dict) else {}
    source_series = (
        source_technical.get("series")
        if isinstance(source_technical.get("series"), list)
        else []
    )
    if (
        source_technical.get("available") is not True
        or len(source_series) != source_bar_count
    ):
        return _ai_trade_council_deep_analysis_unavailable(
            "indicator_unavailable",
            str(source_technical.get("reasonCode") or "indicator_warmup_incomplete"),
            chart=chart,
            source_bar_count=source_bar_count,
        )

    analysis_count = AI_TRADE_COUNCIL_DEEP_ANALYSIS_BAR_COUNT
    decision_bars = copy.deepcopy(source_bars[-analysis_count:])
    decision_series = []
    for item in source_series[-analysis_count:]:
        if not isinstance(item, dict):
            return _ai_trade_council_deep_analysis_unavailable(
                "indicator_unavailable",
                "indicator_series_invalid",
                chart=chart,
                source_bar_count=source_bar_count,
            )
        decision_series.append({
            field: sanitize_json_value(item.get(field))
            for field in AI_TRADE_COUNCIL_TECHNICAL_SERIES_FIELDS
        })
    if (
        len(decision_series) != analysis_count
        or decision_series[0].get("time") != decision_bars[0].get("time")
        or decision_series[-1].get("time") != decision_bars[-1].get("time")
    ):
        return _ai_trade_council_deep_analysis_unavailable(
            "indicator_unavailable",
            "indicator_series_window_mismatch",
            chart=chart,
            source_bar_count=source_bar_count,
        )

    warmup_bars_used = source_bar_count - analysis_count
    technical = copy.deepcopy(source_technical)
    technical.update({
        "barCount": analysis_count,
        "scope": "deep_analysis_decision_window",
        "calculationOrder": "source_then_slice",
        "calculationSourceBarCount": source_bar_count,
        "warmupBarsUsed": warmup_bars_used,
        "seriesBarCount": analysis_count,
        "series": decision_series,
    })
    price_action = _price_action_features_snapshot_uncached(
        decision_bars,
        technical,
    )
    price_action.update({
        "scope": "deep_analysis_decision_window",
        "calculationOrder": "source_indicators_then_decision_features",
        "calculationSourceBarCount": source_bar_count,
        "warmupBarsUsed": warmup_bars_used,
    })
    analysis_window = {
        "requestedBars": analysis_count,
        "usedBars": analysis_count,
        "startTime": decision_bars[0]["time"],
        "endTime": decision_bars[-1]["time"],
        "closedBarsOnly": True,
        "sourceBarCount": source_bar_count,
        "minimumSourceBarCount": AI_TRADE_COUNCIL_DEEP_ANALYSIS_MIN_SOURCE_BARS,
        "warmupBarsUsed": warmup_bars_used,
        "calculationStartTime": source_bars[0]["time"],
        "calculationOrder": "source_then_slice",
        "indicatorFormulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
    }
    snapshot_fresh = chart_status == "ready" and chart.get("available") is True
    response = {
        "schemaVersion": "ai-trade-council-deep-analysis-v1",
        "available": True,
        "status": "ready" if snapshot_fresh else "stale",
        "reasonCode": (
            "ready"
            if snapshot_fresh
            else str(chart.get("reasonCode") or "snapshot_stale")
        ),
        "fresh": snapshot_fresh,
        "decisionEligible": snapshot_fresh,
        "snapshot": metadata,
        "sourceBarCount": source_bar_count,
        "minimumSourceBarCount": AI_TRADE_COUNCIL_DEEP_ANALYSIS_MIN_SOURCE_BARS,
        "analysisBarCount": analysis_count,
        "requestedAnalysisBarCount": analysis_count,
        "warmupBarsUsed": warmup_bars_used,
        "analysisWindow": analysis_window,
        "dailySummary": _ai_trade_council_deep_analysis_daily_summary(
            source.get("dailySummary")
        ),
        "bars": decision_bars,
        "technicalIndicators": technical,
        "priceActionFeatures": price_action,
        "news": _latest_ai_trade_council_deep_analysis_news(
            metadata.get("snapshotId")
        ),
        "readOnly": True,
        "generatedAt": utc_now(),
    }
    if _snapshot_has_forbidden_keys(response) or json_contains_potential_secret(response):
        return _ai_trade_council_deep_analysis_unavailable(
            "unavailable",
            "deep_analysis_safety_filter_failed",
            chart=chart,
            source_bar_count=source_bar_count,
        )
    return response


def ai_trade_council_deep_analysis_read_model() -> dict:
    """Build the heavy 300-bar view only when its dedicated API is requested."""
    return _ai_trade_council_deep_analysis_from_snapshot(
        metatrader_snapshot_read_model(AI_TRADE_COUNCIL_PROP_ID)
    )


def _ai_trade_council_deep_analysis_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _ai_trade_council_deep_analysis_csv_bytes(
    rows: list[dict],
    fields: tuple[str, ...],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(fields),
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            field: "" if row.get(field) is None else row.get(field)
            for field in fields
        })
    return buffer.getvalue().encode("utf-8")


def _ai_trade_council_deep_analysis_file_record(
    package_relative_dir: str,
    name: str,
    content: bytes,
) -> dict:
    return {
        "name": name,
        "path": f"{package_relative_dir}/{name}",
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def _ai_trade_council_deep_analysis_existing_package(
    package_dir: Path,
    snapshot_id: str,
) -> dict:
    # Windows hosted runners can expose the same Temp directory once through
    # an 8.3 alias (RUNNER~1) and once through its long path (runneradmin).
    # Resolve both sides after the package exists before applying the
    # containment check; comparing the raw spellings makes a valid package
    # look as if it escaped the workspace.
    package_dir = package_dir.resolve(strict=False)
    workspace_root = AI_TRADE_COUNCIL_WORKSPACE_DIR.resolve(strict=False)
    manifest_path = package_dir / "manifest.json"
    manifest = read_json(manifest_path, None)
    if (
        not isinstance(manifest, dict)
        or manifest.get("schemaVersion")
        != "ai-trade-council-deep-analysis-package-v1"
        or manifest.get("snapshotId") != snapshot_id
        or manifest.get("immutable") is not True
        or manifest.get("readOnly") is not True
    ):
        raise DataIntegrityError("Deep-analysis package manifest is invalid.")
    try:
        package_relative_dir = package_dir.relative_to(workspace_root).as_posix()
    except ValueError as error:
        raise DataIntegrityError("Deep-analysis package escapes Workspace.") from error
    expected_names = {
        "bars-300.csv",
        "technical-300.csv",
        "price-action.json",
        "local-summary.json",
    }
    raw_files = manifest.get("files") if isinstance(manifest.get("files"), list) else []
    if {str(item.get("name") or "") for item in raw_files if isinstance(item, dict)} != expected_names:
        raise DataIntegrityError("Deep-analysis package file set is invalid.")
    records = []
    for item in raw_files:
        name = str(item.get("name") or "")
        file_path = package_dir / name
        if item.get("path") != f"{package_relative_dir}/{name}" or not file_path.is_file():
            raise DataIntegrityError("Deep-analysis package path is invalid.")
        content = file_path.read_bytes()
        record = _ai_trade_council_deep_analysis_file_record(
            package_relative_dir,
            name,
            content,
        )
        if (
            item.get("sha256") != record["sha256"]
            or item.get("bytes") != record["bytes"]
        ):
            raise DataIntegrityError("Deep-analysis package hash verification failed.")
        records.append(record)
    manifest_content = manifest_path.read_bytes()
    records.insert(
        0,
        _ai_trade_council_deep_analysis_file_record(
            package_relative_dir,
            "manifest.json",
            manifest_content,
        ),
    )
    return {
        "manifest": manifest,
        "files": records,
        "workspaceRelativeDirectory": package_relative_dir,
    }


def create_ai_trade_council_deep_analysis_package(payload: object) -> dict:
    request = payload if isinstance(payload, dict) else {}
    unexpected_fields = set(request) - {"snapshotId"}
    if unexpected_fields:
        raise RequestError("Deep-analysis package request has unknown fields.", 422)
    requested_snapshot_id = str(request.get("snapshotId") or "").strip()
    if requested_snapshot_id and not re.fullmatch(r"[0-9a-f]{64}", requested_snapshot_id):
        raise RequestError("Deep-analysis Snapshot ID is invalid.", 422)

    deep_analysis = ai_trade_council_deep_analysis_read_model()
    snapshot_id = str((deep_analysis.get("snapshot") or {}).get("snapshotId") or "")
    if deep_analysis.get("available") is not True or not snapshot_id:
        return {
            "ok": False,
            "kind": "deep_analysis_unavailable",
            "reasonCode": deep_analysis.get("reasonCode"),
            "deepAnalysis": deep_analysis,
            "_httpStatus": 409,
        }
    if requested_snapshot_id and requested_snapshot_id != snapshot_id:
        return {
            "ok": False,
            "kind": "deep_analysis_snapshot_changed",
            "reasonCode": "snapshot_id_mismatch",
            "snapshotId": snapshot_id,
            "_httpStatus": 409,
        }

    workspace_root = AI_TRADE_COUNCIL_WORKSPACE_DIR.resolve(strict=False)
    package_root = AI_TRADE_COUNCIL_DEEP_ANALYSIS_DIR.resolve(strict=False)
    try:
        package_root.relative_to(workspace_root)
    except ValueError as error:
        raise DataIntegrityError("Deep-analysis package root escapes Workspace.") from error
    package_dir = (package_root / snapshot_id).resolve(strict=False)
    try:
        package_dir.relative_to(package_root)
    except ValueError as error:
        raise DataIntegrityError("Deep-analysis package path escapes its root.") from error

    with AI_TRADE_COUNCIL_DEEP_ANALYSIS_PACKAGE_LOCK:
        created = False
        if package_dir.exists():
            verified = _ai_trade_council_deep_analysis_existing_package(
                package_dir,
                snapshot_id,
            )
        else:
            package_root.mkdir(parents=True, exist_ok=True)
            package_relative_dir = package_dir.relative_to(workspace_root).as_posix()
            technical = deep_analysis["technicalIndicators"]
            technical_series = technical.get("series") if isinstance(technical.get("series"), list) else []
            local_summary = {
                "schemaVersion": "ai-trade-council-deep-analysis-local-summary-v1",
                "snapshot": deep_analysis["snapshot"],
                "sourceBarCount": deep_analysis["sourceBarCount"],
                "analysisBarCount": deep_analysis["analysisBarCount"],
                "warmupBarsUsed": deep_analysis["warmupBarsUsed"],
                "fresh": deep_analysis["fresh"],
                "decisionEligible": deep_analysis["decisionEligible"],
                "status": deep_analysis["status"],
                "reasonCode": deep_analysis["reasonCode"],
                "analysisWindow": deep_analysis["analysisWindow"],
                "dailySummary": deep_analysis.get("dailySummary", {}),
                "technicalSummary": {
                    key: value
                    for key, value in technical.items()
                    if key != "series"
                },
                "priceActionSummary": {
                    key: deep_analysis["priceActionFeatures"].get(key)
                    for key in (
                        "available",
                        "reasonCode",
                        "basis",
                        "formulaVersion",
                        "moduleCount",
                        "modules",
                        "barCount",
                        "latestClosedBarTime",
                        "scope",
                        "calculationOrder",
                        "calculationSourceBarCount",
                        "warmupBarsUsed",
                    )
                },
                "news": deep_analysis["news"],
                "readOnly": True,
                "generatedAt": deep_analysis["generatedAt"],
            }
            file_contents = {
                "bars-300.csv": _ai_trade_council_deep_analysis_csv_bytes(
                    deep_analysis["bars"],
                    ("time", "open", "high", "low", "close", "volume"),
                ),
                "technical-300.csv": _ai_trade_council_deep_analysis_csv_bytes(
                    technical_series,
                    AI_TRADE_COUNCIL_TECHNICAL_SERIES_FIELDS,
                ),
                "price-action.json": _ai_trade_council_deep_analysis_json_bytes(
                    deep_analysis["priceActionFeatures"]
                ),
                "local-summary.json": _ai_trade_council_deep_analysis_json_bytes(
                    local_summary
                ),
            }
            file_records = [
                _ai_trade_council_deep_analysis_file_record(
                    package_relative_dir,
                    name,
                    content,
                )
                for name, content in file_contents.items()
            ]
            manifest = {
                "schemaVersion": "ai-trade-council-deep-analysis-package-v1",
                "snapshotId": snapshot_id,
                "createdAt": utc_now(),
                "workspaceRelativeDirectory": package_relative_dir,
                "immutable": True,
                "readOnly": True,
                "sourceBarCount": deep_analysis["sourceBarCount"],
                "analysisBarCount": deep_analysis["analysisBarCount"],
                "warmupBarsUsed": deep_analysis["warmupBarsUsed"],
                "fresh": deep_analysis["fresh"],
                "decisionEligible": deep_analysis["decisionEligible"],
                "sourceStatus": deep_analysis["status"],
                "sourceReasonCode": deep_analysis["reasonCode"],
                "indicatorFormulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
                "files": file_records,
            }
            manifest_content = _ai_trade_council_deep_analysis_json_bytes(manifest)
            stage_dir = package_root / f".{snapshot_id}.{secrets.token_hex(6)}.tmp"
            try:
                stage_dir.mkdir(parents=False, exist_ok=False)
                for name, content in file_contents.items():
                    (stage_dir / name).write_bytes(content)
                (stage_dir / "manifest.json").write_bytes(manifest_content)
                os.replace(stage_dir, package_dir)
            finally:
                if stage_dir.exists() and stage_dir.parent == package_root:
                    shutil.rmtree(stage_dir)
            created = True
            verified = _ai_trade_council_deep_analysis_existing_package(
                package_dir,
                snapshot_id,
            )

    audit_id = safe_id(None, "audit")
    package_model = {
        "schemaVersion": "ai-trade-council-deep-analysis-package-v1",
        "snapshotId": snapshot_id,
        "created": created,
        "immutable": True,
        "readOnly": True,
        "fresh": deep_analysis["fresh"],
        "decisionEligible": deep_analysis["decisionEligible"],
        "sourceStatus": deep_analysis["status"],
        "sourceReasonCode": deep_analysis["reasonCode"],
        "workspaceRelativeDirectory": verified["workspaceRelativeDirectory"],
        "files": verified["files"],
        "auditId": audit_id,
    }
    append_audit({
        "type": (
            "ai_trade_council.deep_analysis_package_created"
            if created
            else "ai_trade_council.deep_analysis_package_reused"
        ),
        "auditId": audit_id,
        "snapshotId": snapshot_id,
        "workspaceRelativeDirectory": verified["workspaceRelativeDirectory"],
        "files": verified["files"],
        "immutable": True,
        "readOnly": True,
    })
    return {
        "ok": True,
        "kind": "ai_trade_council_deep_analysis_package",
        "package": package_model,
        "updatedAt": utc_now(),
    }


def _ai_trade_council_automation_store_path() -> Path:
    return RUNTIME_DIR / AI_TRADE_COUNCIL_AUTOMATION_STORE_FILENAME


def _ai_trade_council_automation_default_store() -> dict:
    return {
        "version": "ai-trade-council-automation-store-v1",
        "config": {
            "enabled": False,
            "triggerMode": "last_closed_candle_time_change",
            "pollSeconds": AI_TRADE_COUNCIL_AUTOMATION_POLL_SECONDS,
            "settleSeconds": AI_TRADE_COUNCIL_AUTOMATION_SETTLE_SECONDS,
            "maxDailyRounds": AI_TRADE_COUNCIL_AUTOMATION_MAX_DAILY_ROUNDS,
            "minRemainingPercent": AI_TRADE_COUNCIL_AUTOMATION_MIN_REMAINING_PERCENT,
            "analysisBarCount": AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT,
            "requiredVotes": AI_TRADE_COUNCIL_DEFAULT_REQUIRED_VOTES,
            "supportedTimeframes": list(AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES),
        },
        "state": {
            "status": "disabled",
            "reason": "automation_disabled",
            "startupId": None,
            "dailyRunDate": None,
            "dailyRunCount": 0,
            "candidateId": None,
            "streamKey": None,
            "symbol": None,
            "timeframe": None,
            "lastObservedClosedBarTime": None,
            "lastAnalyzedClosedBarTime": None,
            "lastAnalyzedSnapshotId": None,
            "lastMissionId": None,
            "pendingClosedBarTime": None,
            "pendingSnapshotId": None,
            "pendingDetectedAt": None,
        },
        "updatedAt": utc_now(),
    }


def _automation_optional_count(
    value: object,
    *,
    maximum: int = 4_102_444_800,
) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if 0 <= number <= maximum else None


def _ai_trade_council_automation_store_shape(value: object) -> dict:
    defaults = _ai_trade_council_automation_default_store()
    if not isinstance(value, dict):
        raise DataIntegrityError("AI Trade Council automation store is not a JSON object.")
    raw_config = value.get("config")
    raw_state = value.get("state")
    if not isinstance(raw_config, dict) or not isinstance(raw_state, dict):
        raise DataIntegrityError("AI Trade Council automation store is missing config or state.")

    config = {**defaults["config"], **raw_config}
    configured_analysis_bar_count = config.get("analysisBarCount")
    if (
        isinstance(configured_analysis_bar_count, bool)
        or not isinstance(configured_analysis_bar_count, int)
        or configured_analysis_bar_count
        not in AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS
    ):
        configured_analysis_bar_count = AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT
    configured_required_votes = config.get("requiredVotes")
    if (
        isinstance(configured_required_votes, bool)
        or not isinstance(configured_required_votes, int)
        or configured_required_votes not in AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES
    ):
        configured_required_votes = AI_TRADE_COUNCIL_DEFAULT_REQUIRED_VOTES
    config.update({
        "enabled": bool(config.get("enabled", False)),
        "triggerMode": "last_closed_candle_time_change",
        "pollSeconds": AI_TRADE_COUNCIL_AUTOMATION_POLL_SECONDS,
        "settleSeconds": AI_TRADE_COUNCIL_AUTOMATION_SETTLE_SECONDS,
        "maxDailyRounds": clamp_int(
            config.get("maxDailyRounds"),
            AI_TRADE_COUNCIL_AUTOMATION_MAX_DAILY_ROUNDS,
            1,
            AI_TRADE_COUNCIL_AUTOMATION_MAX_DAILY_ROUNDS,
        ),
        "minRemainingPercent": clamp_int(
            config.get("minRemainingPercent"),
            AI_TRADE_COUNCIL_AUTOMATION_MIN_REMAINING_PERCENT,
            10,
            80,
        ),
        "analysisBarCount": configured_analysis_bar_count,
        "requiredVotes": configured_required_votes,
        "supportedTimeframes": list(AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES),
    })

    state = {**defaults["state"], **raw_state}
    state["status"] = redact_text(str(state.get("status") or "idle"), 48)
    state["reason"] = redact_text(str(state.get("reason") or "waiting"), 120)
    state["startupId"] = (
        redact_text(str(state.get("startupId")), 80)
        if state.get("startupId")
        else None
    )
    daily_date = str(state.get("dailyRunDate") or "")
    state["dailyRunDate"] = daily_date if re.fullmatch(r"\d{4}-\d{2}-\d{2}", daily_date) else None
    state["dailyRunCount"] = clamp_int(state.get("dailyRunCount"), 0, 0, 100_000)
    candidate_id = safe_reference(state.get("candidateId"))
    state["candidateId"] = (
        candidate_id
        if candidate_id and candidate_id.startswith("mtc-")
        else None
    )
    stream_key = str(state.get("streamKey") or "")
    state["streamKey"] = stream_key if re.fullmatch(r"[0-9a-f]{64}", stream_key) else None
    state["symbol"] = _safe_snapshot_symbol(state.get("symbol"))
    state["timeframe"] = _safe_snapshot_timeframe(state.get("timeframe"))
    for field in (
        "lastObservedClosedBarTime",
        "lastAnalyzedClosedBarTime",
        "pendingClosedBarTime",
    ):
        state[field] = _automation_optional_count(state.get(field))
    for field in ("lastAnalyzedSnapshotId", "pendingSnapshotId"):
        snapshot_id = str(state.get(field) or "")
        state[field] = snapshot_id if re.fullmatch(r"[0-9a-f]{64}", snapshot_id) else None
    state["lastMissionId"] = safe_reference(state.get("lastMissionId"))
    pending_detected_at = str(state.get("pendingDetectedAt") or "")
    state["pendingDetectedAt"] = (
        pending_detected_at
        if parse_iso(pending_detected_at)
        else None
    )
    return {
        "version": "ai-trade-council-automation-store-v1",
        "config": config,
        "state": state,
        "updatedAt": value.get("updatedAt") or defaults["updatedAt"],
    }


def load_ai_trade_council_automation_store() -> dict:
    path = _ai_trade_council_automation_store_path()
    with AI_TRADE_COUNCIL_AUTOMATION_LOCK:
        if not path.exists():
            return _ai_trade_council_automation_default_store()
        return _ai_trade_council_automation_store_shape(read_json(path, {}))


def _save_ai_trade_council_automation_store(store: dict) -> dict:
    normalized = _ai_trade_council_automation_store_shape(store)
    normalized["updatedAt"] = utc_now()
    path = _ai_trade_council_automation_store_path()
    with AI_TRADE_COUNCIL_AUTOMATION_LOCK:
        write_json(path, normalized, keep_backup=path.exists())
    return normalized


def ensure_ai_trade_council_automation_store() -> dict:
    path = _ai_trade_council_automation_store_path()
    with AI_TRADE_COUNCIL_AUTOMATION_LOCK:
        store = load_ai_trade_council_automation_store()
        if not path.exists():
            write_json(path, store)
        return store


def _automation_day_key(now_local: datetime | None = None) -> str:
    return (now_local or datetime.now(THAILAND_TIMEZONE)).date().isoformat()


def _rollover_ai_trade_council_automation_day(
    store: dict,
    now_local: datetime | None = None,
) -> tuple[dict, bool]:
    current_day = _automation_day_key(now_local)
    state = store["state"]
    if state.get("dailyRunDate") == current_day:
        return store, False
    state["dailyRunDate"] = current_day
    state["dailyRunCount"] = 0
    return store, True


def ai_trade_council_automation_read_model() -> dict:
    store = load_ai_trade_council_automation_store()
    store, rolled = _rollover_ai_trade_council_automation_day(store)
    if rolled and _ai_trade_council_automation_store_path().exists():
        store = _save_ai_trade_council_automation_store(store)
    config = store["config"]
    state = store["state"]
    return {
        "schemaVersion": "ai-trade-council-automation-v1",
        "config": {
            "enabled": bool(config.get("enabled")),
            "triggerMode": "last_closed_candle_time_change",
            "pollSeconds": AI_TRADE_COUNCIL_AUTOMATION_POLL_SECONDS,
            "settleSeconds": AI_TRADE_COUNCIL_AUTOMATION_SETTLE_SECONDS,
            "maxDailyRounds": config.get("maxDailyRounds"),
            "minRemainingPercent": config.get("minRemainingPercent"),
            "analysisBarCount": config.get("analysisBarCount"),
            "requiredVotes": config.get("requiredVotes"),
            "allowedRequiredVotes": list(AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES),
            "allowedAnalysisBarCounts": list(
                AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS
            ),
            "supportedTimeframes": list(AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES),
        },
        "state": {
            "status": state.get("status"),
            "reason": state.get("reason"),
            "symbol": state.get("symbol"),
            "timeframe": state.get("timeframe"),
            "lastObservedClosedBarTime": state.get("lastObservedClosedBarTime"),
            "lastAnalyzedClosedBarTime": state.get("lastAnalyzedClosedBarTime"),
            "dailyRunCount": state.get("dailyRunCount", 0),
            "lastMissionId": state.get("lastMissionId"),
        },
        "updatedAt": store.get("updatedAt"),
    }


def set_ai_trade_council_automation(payload: dict) -> dict:
    allowed_fields = {
        "enabled",
        "maxDailyRounds",
        "minRemainingPercent",
        "analysisBarCount",
        "requiredVotes",
    }
    if (
        not isinstance(payload, dict)
        or not payload
        or not set(payload).issubset(allowed_fields)
    ):
        return {
            "ok": False,
            "kind": "invalid_ai_trade_council_automation_request",
            "messageTh": (
                "รับเฉพาะ enabled, maxDailyRounds, minRemainingPercent "
                "analysisBarCount และ requiredVotes"
            ),
            "_httpStatus": 422,
        }
    validated: dict[str, object] = {}
    if "enabled" in payload:
        if not isinstance(payload.get("enabled"), bool):
            return {
                "ok": False,
                "kind": "invalid_enabled",
                "messageTh": "enabled ต้องเป็น true หรือ false",
                "_httpStatus": 422,
            }
        validated["enabled"] = payload["enabled"]
    integer_rules = {
        "maxDailyRounds": (1, AI_TRADE_COUNCIL_AUTOMATION_MAX_DAILY_ROUNDS),
        "minRemainingPercent": (10, 80),
    }
    for field, (minimum, maximum) in integer_rules.items():
        if field not in payload:
            continue
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            return {
                "ok": False,
                "kind": f"invalid_{field}",
                "messageTh": f"{field} ต้องเป็นจำนวนเต็มระหว่าง {minimum}-{maximum}",
                "_httpStatus": 422,
            }
        validated[field] = value
    if "analysisBarCount" in payload:
        analysis_bar_count = payload.get("analysisBarCount")
        if (
            isinstance(analysis_bar_count, bool)
            or not isinstance(analysis_bar_count, int)
            or analysis_bar_count
            not in AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS
        ):
            append_audit({
                "type": "ai_trade_council.automation_change_rejected",
                "reason": "invalid_analysis_bar_count",
                "providedType": type(analysis_bar_count).__name__,
                "allowedAnalysisBarCounts": list(
                    AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS
                ),
                "terminalActions": False,
            })
            return {
                "ok": False,
                "kind": "invalid_analysisBarCount",
                "messageTh": (
                    "analysisBarCount ต้องเป็น 120, 180, 240, 300, 500 หรือ 1000 เท่านั้น"
                ),
                "allowedAnalysisBarCounts": list(
                    AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS
                ),
                "_httpStatus": 422,
            }
        validated["analysisBarCount"] = analysis_bar_count
    if "requiredVotes" in payload:
        required_votes = payload.get("requiredVotes")
        if (
            isinstance(required_votes, bool)
            or not isinstance(required_votes, int)
            or required_votes not in AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES
        ):
            append_audit({
                "type": "ai_trade_council.automation_change_rejected",
                "reason": "invalid_required_votes",
                "providedType": type(required_votes).__name__,
                "allowedRequiredVotes": list(
                    AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES
                ),
                "terminalActions": False,
            })
            return {
                "ok": False,
                "kind": "invalid_requiredVotes",
                "messageTh": "requiredVotes ต้องเป็น 1, 2 หรือ 3 เท่านั้น",
                "allowedRequiredVotes": list(
                    AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES
                ),
                "_httpStatus": 422,
            }
        validated["requiredVotes"] = required_votes

    with AI_TRADE_COUNCIL_AUTOMATION_LOCK:
        store = load_ai_trade_council_automation_store()
        was_enabled = bool(store["config"].get("enabled"))
        store["config"] = {**store["config"], **validated}
        enabled = bool(store["config"].get("enabled"))
        if enabled and not was_enabled:
            store["state"].update({
                "status": "starting",
                "reason": "baseline_required",
                "startupId": None,
                "candidateId": None,
                "streamKey": None,
                "symbol": None,
                "timeframe": None,
                "lastObservedClosedBarTime": None,
                "pendingClosedBarTime": None,
                "pendingSnapshotId": None,
                "pendingDetectedAt": None,
            })
        elif not enabled:
            store["state"].update({
                "status": "disabled",
                "reason": "automation_disabled",
                "pendingClosedBarTime": None,
                "pendingSnapshotId": None,
                "pendingDetectedAt": None,
            })
        store = _save_ai_trade_council_automation_store(store)
    append_audit({
        "type": "ai_trade_council.automation_changed",
        "enabled": store["config"].get("enabled"),
        "maxDailyRounds": store["config"].get("maxDailyRounds"),
        "minRemainingPercent": store["config"].get("minRemainingPercent"),
        "analysisBarCount": store["config"].get("analysisBarCount"),
        "requiredVotes": store["config"].get("requiredVotes"),
        "allowedRequiredVotes": list(AI_TRADE_COUNCIL_ALLOWED_REQUIRED_VOTES),
        "allowedAnalysisBarCounts": list(
            AI_TRADE_COUNCIL_ALLOWED_ANALYSIS_BAR_COUNTS
        ),
        "triggerMode": "last_closed_candle_time_change",
        "terminalActions": False,
    })
    AI_TRADE_COUNCIL_AUTOMATION_WAKE.set()
    return {
        "ok": True,
        "kind": "ai_trade_council_automation",
        "automation": ai_trade_council_automation_read_model(),
    }


def _ai_trade_council_closed_bar_identity(snapshot: dict) -> tuple[dict | None, str]:
    adapter = snapshot.get("adapter") if isinstance(snapshot.get("adapter"), dict) else {}
    chart = snapshot.get("chartSnapshot") if isinstance(snapshot.get("chartSnapshot"), dict) else {}
    if adapter.get("ready") is not True or chart.get("available") is not True:
        return None, str(adapter.get("reasonCode") or chart.get("reasonCode") or "snapshot_not_ready")
    candidate_id = safe_reference(snapshot.get("selectedCandidateId"))
    symbol = _safe_snapshot_symbol(chart.get("symbol"))
    timeframe = _safe_snapshot_timeframe(chart.get("timeframe"))
    snapshot_id = str(chart.get("snapshotId") or "")
    bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    closed_bar_times = [
        value
        for value in (
            _automation_optional_count(item.get("time"))
            for item in bars
            if isinstance(item, dict)
        )
        if value is not None and value > 0
    ]
    if (
        not candidate_id
        or not candidate_id.startswith("mtc-")
        or not symbol
        or not timeframe
        or not re.fullmatch(r"[0-9a-f]{64}", snapshot_id)
        or not closed_bar_times
    ):
        return None, "closed_bar_identity_unavailable"
    last_closed_bar_time = max(closed_bar_times)
    stream_key = payload_digest(candidate_id, symbol, timeframe)
    return {
        "candidateId": candidate_id,
        "streamKey": stream_key,
        "symbol": symbol,
        "timeframe": timeframe,
        "lastClosedBarTime": last_closed_bar_time,
        "snapshotId": snapshot_id,
    }, "ready"


def _active_ai_trade_council_parent() -> dict | None:
    missions = load_missions()
    missions_by_id = {
        str(mission.get("id") or ""): mission
        for mission in missions
        if safe_reference(mission.get("id"))
    }
    for mission in missions:
        context = mission.get("analysisContext") if isinstance(mission.get("analysisContext"), dict) else {}
        if (
            context.get("kind") == "ai_trade_council_parent"
            and mission.get("status") in {"queued", "running", "waiting_approval"}
        ):
            return mission
    # Fail closed when a parent status is stale/terminal but one of its Council
    # votes is still executable. Starting another round in that state can make
    # two sets of Specialists race on the same local runner and MT4 channel.
    for mission in missions:
        if (
            mission.get("status") in {"queued", "running", "waiting_approval"}
            and _is_ai_trade_council_vote_mission(mission)
        ):
            parent_id = safe_reference(mission.get("parentMissionId"))
            return missions_by_id.get(str(parent_id or ""), mission)
    return None


def _find_ai_trade_council_parent_by_closed_bar(
    stream_key: str,
    closed_bar_time: int,
) -> dict | None:
    for mission in load_missions():
        context = (
            mission.get("analysisContext")
            if isinstance(mission.get("analysisContext"), dict)
            else {}
        )
        if context.get("kind") != "ai_trade_council_parent":
            continue
        bar_identity = (
            context.get("closedBarIdentity")
            if isinstance(context.get("closedBarIdentity"), dict)
            else {}
        )
        automation = (
            context.get("automation")
            if isinstance(context.get("automation"), dict)
            else {}
        )
        observed_stream_key = str(
            bar_identity.get("streamKey")
            or automation.get("streamKey")
            or ""
        )
        observed_bar_time = _automation_optional_count(
            bar_identity.get("closedBarTime")
            if bar_identity
            else automation.get("closedBarTime")
        )
        if (
            observed_stream_key == stream_key
            and observed_bar_time == closed_bar_time
        ):
            return mission
    return None


def _ai_trade_council_manual_retry_allowed(parent: dict) -> bool:
    """Allow a human to retry a terminal round only when no MT4 command exists."""
    gateway = (
        parent.get("tradeGateway")
        if isinstance(parent.get("tradeGateway"), dict)
        else {}
    )
    return bool(
        parent.get("status") in {"blocked", "failed"}
        and gateway.get("commandPublished") is not True
        and not safe_reference(gateway.get("commandId"))
    )


def _next_ai_trade_council_retry_idempotency(
    base_key: str,
) -> tuple[str, str]:
    """Create a bounded unique suffix for an explicit retry on one snapshot."""
    used_keys = {
        str(mission.get("idempotencyKey") or "")
        for mission in load_missions()
    }
    retry_pattern = re.compile(rf"^{re.escape(base_key)}-retry-([0-9]{{1,3}})$")
    used_indexes = [
        int(matched.group(1))
        for key in used_keys
        for matched in [retry_pattern.fullmatch(key)]
        if matched and 2 <= int(matched.group(1)) <= 999
    ]
    retry_index = max([1, *used_indexes]) + 1
    if retry_index <= 999:
        suffix = f"-retry-{retry_index}"
        candidate = f"{base_key}{suffix}"
        if len(candidate) <= 160 and candidate not in used_keys:
            return candidate, suffix
    raise RequestError(
        "AI Trade Council retry limit reached for this Snapshot.",
        409,
    )


def _latest_ai_trade_council_retry_parent(base_key: str) -> dict | None:
    """Return the newest parent in one manual retry lineage.

    The base mission remains in history after retry #2. Looking up only the
    base key would therefore incorrectly allow retry #3 even when retry #2 had
    already published a command.
    """
    pattern = re.compile(rf"^{re.escape(base_key)}-retry-([0-9]{{1,3}})$")
    latest: tuple[int, dict] | None = None
    for mission in load_missions():
        key = str(mission.get("idempotencyKey") or "")
        retry_index = 1 if key == base_key else None
        if retry_index is None:
            matched = pattern.fullmatch(key)
            if matched and 2 <= int(matched.group(1)) <= 999:
                retry_index = int(matched.group(1))
        if retry_index is None:
            continue
        context = (
            mission.get("analysisContext")
            if isinstance(mission.get("analysisContext"), dict)
            else {}
        )
        if context.get("kind") != "ai_trade_council_parent":
            continue
        if latest is None or retry_index > latest[0]:
            latest = (retry_index, mission)
    return latest[1] if latest else None


def _update_ai_trade_council_automation_state(
    **values: object,
) -> tuple[dict, bool]:
    with AI_TRADE_COUNCIL_AUTOMATION_LOCK:
        store = load_ai_trade_council_automation_store()
        store, rolled = _rollover_ai_trade_council_automation_day(store)
        state = store["state"]
        changed = rolled or any(state.get(key) != value for key, value in values.items())
        if changed:
            state.update(values)
            store = _save_ai_trade_council_automation_store(store)
        return store, changed


def ai_trade_council_snapshot_reference(
    snapshot_id: str,
    artifact_digest: str,
) -> str:
    if (
        re.fullmatch(r"[0-9a-f]{64}", str(snapshot_id or "")) is None
        or re.fullmatch(r"[0-9a-f]{64}", str(artifact_digest or "")) is None
    ):
        return ""
    return (
        Path("ai-trade-council")
        / "snapshots"
        / f"{artifact_digest}.json"
    ).as_posix()


def _ai_trade_council_canonical_instrument(symbol: object) -> dict:
    """Map broker aliases to a stable public-market identity without guessing a feed."""
    observed = str(symbol or "").strip().upper()
    compact = re.sub(r"[^A-Z0-9]", "", observed)
    if compact.startswith("XAUUSD") or compact.startswith("GOLD"):
        return {
            "observedSymbol": observed,
            "canonicalSymbol": "XAUUSD",
            "assetClass": "precious_metal",
            "newsQuery": "gold XAUUSD US dollar",
            "mappingStatus": "mapped",
        }
    return {
        "observedSymbol": observed,
        "canonicalSymbol": observed,
        "assetClass": "unknown",
        "newsQuery": observed,
        "mappingStatus": "identity_only",
    }


def _ai_trade_council_expected_valid_until(
    closed_bar_time: int,
    timeframe: str,
    horizon_bars: int,
) -> int | None:
    seconds = AI_TRADE_COUNCIL_TIMEFRAME_SECONDS.get(str(timeframe or "").upper())
    if not seconds or horizon_bars < 1:
        return None
    # closed_bar_time is the open time of shift=1. The first future decision
    # bar closes two intervals after that timestamp.
    return int(closed_bar_time) + (int(horizon_bars) + 1) * seconds


def _ai_trade_council_data_quality_gate(
    snapshot_model: dict,
    policy: dict,
) -> dict:
    """Build a deterministic, audit-safe gate before spending three model calls."""
    chart = (
        snapshot_model.get("chartSnapshot")
        if isinstance(snapshot_model.get("chartSnapshot"), dict)
        else {}
    )
    bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    timeframe = str(chart.get("timeframe") or "").upper()
    minimum_bars = int(policy["minimumBars"])
    reasons: list[str] = []
    if len(bars) < minimum_bars:
        reasons.append("insufficient_closed_bars")

    observed_times: list[int] = []
    sane_bars = True
    for row in bars:
        if not isinstance(row, dict):
            sane_bars = False
            continue
        timestamp = row.get("time")
        values = [row.get(field) for field in ("open", "high", "low", "close", "volume")]
        if (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, int)
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values)
            or any(not math.isfinite(float(value)) for value in values)
        ):
            sane_bars = False
            continue
        open_value, high_value, low_value, close_value, volume = map(float, values)
        if (
            min(open_value, high_value, low_value, close_value) <= 0
            or volume < 0
            or high_value < max(open_value, close_value, low_value)
            or low_value > min(open_value, close_value, high_value)
        ):
            sane_bars = False
        observed_times.append(timestamp)
    ordered_unique = bool(observed_times) and all(
        current > previous
        for previous, current in zip(observed_times, observed_times[1:])
    )
    if not sane_bars:
        reasons.append("ohlc_payload_invalid")
    if not ordered_unique:
        reasons.append("bar_times_not_strictly_ordered_unique")

    bid = _safe_snapshot_number(chart.get("bid"), minimum=0.00000001)
    ask = _safe_snapshot_number(chart.get("ask"), minimum=0.00000001)
    spread = _safe_snapshot_number(
        chart.get("spreadPoints"),
        minimum=0,
        maximum=float(policy["maximumSnapshotSpreadPoints"]),
    )
    quote_valid = bool(bid is not None and ask is not None and ask >= bid and spread is not None)
    if not quote_valid:
        reasons.append("quote_or_spread_invalid")

    technical = (
        chart.get("technicalIndicators")
        if isinstance(chart.get("technicalIndicators"), dict)
        else {}
    )
    required_indicator_fields = ("ema20", "ema50", "rsi14", "atr14", "macdLine")
    indicator_values = {
        field: _safe_snapshot_number(technical.get(field))
        for field in required_indicator_fields
    }
    latest_close = _safe_snapshot_number(technical.get("latestClose"), minimum=0.00000001)
    atr_value = _safe_snapshot_number(technical.get("atr14"), minimum=0.00000001)
    indicator_ready = bool(
        technical.get("available") is True
        and len(bars) >= minimum_bars
        and latest_close is not None
        and atr_value is not None
        and all(value is not None for value in indicator_values.values())
    )
    if not indicator_ready:
        reasons.append("deterministic_indicator_data_incomplete")
    volatility_percent = (
        round(atr_value / latest_close * 100.0, 8)
        if atr_value is not None and latest_close is not None
        else None
    )
    volatility_state = None
    if volatility_percent is not None:
        volatility_state = (
            "LOW"
            if volatility_percent < float(policy["volatilityLowPercent"])
            else "HIGH"
            if volatility_percent > float(policy["volatilityHighPercent"])
            else "NORMAL"
        )

    market_open = chart.get("marketOpen")
    market_state = (
        {
            "status": "available",
            "marketOpen": bool(market_open),
            "session": redact_text(str(chart.get("marketSession") or "unknown"), 80),
            "reasonCode": "feed_reported_market_state",
        }
        if isinstance(market_open, bool)
        else {
            "status": "unavailable",
            "marketOpen": None,
            "session": None,
            "reasonCode": "snapshot_market_state_unavailable",
        }
    )
    higher_timeframe = AI_TRADE_COUNCIL_HIGHER_TIMEFRAME.get(timeframe)
    higher_timeframe_context = {
        "status": "unavailable",
        "requestedTimeframe": higher_timeframe,
        "reasonCode": (
            "snapshot_current_timeframe_only"
            if higher_timeframe
            else "no_higher_timeframe_defined"
        ),
        "data": None,
    }
    core_passed = not reasons
    market_execution_ready = bool(
        market_state["status"] == "available" and market_state["marketOpen"] is True
    )
    return {
        "schemaVersion": "ai-trade-council-quality-gate-v2",
        "passed": core_passed,
        "status": "passed" if core_passed else "blocked",
        "reasonCodes": reasons,
        "minimumBars": minimum_bars,
        "observedBars": len(bars),
        "orderedUniqueBars": ordered_unique,
        "saneOhlc": sane_bars,
        "quoteValid": quote_valid,
        "canonicalInstrument": _ai_trade_council_canonical_instrument(chart.get("symbol")),
        "higherTimeframeContext": higher_timeframe_context,
        "marketState": market_state,
        "executionEligibility": {
            "shadow": core_passed,
            "demo": core_passed and market_execution_ready,
            "live": core_passed and market_execution_ready,
        },
        "technical": {
            "indicatorDataSufficient": indicator_ready,
            "requiredFields": list(required_indicator_fields),
            "volatilityPercent": volatility_percent,
            "volatilityState": volatility_state,
        },
        "checkedAt": utc_now(),
    }


def load_ai_trade_council_prompt_contract() -> dict:
    """Load the fixed three-agent prompt packet and fail closed on drift."""
    if not AI_TRADE_COUNCIL_PROMPTS_PATH.is_file():
        raise RequestError("ยังไม่พบสัญญา Prompt สำหรับสภา AI Trade", 503)
    contract = read_json(AI_TRADE_COUNCIL_PROMPTS_PATH, None)
    if not isinstance(contract, dict) or contract.get("schemaVersion") != "ai-trade-council-prompts-v2":
        raise RequestError("สัญญา Prompt สำหรับสภา AI Trade ไม่ถูกต้อง", 503)
    if (
        contract.get("managerAgentId") != "manager"
        or contract.get("riskGuardAgentId") != "risk_guard"
    ):
        raise RequestError("สัญญา Prompt กำหนดผู้จัดการหรือ Risk Guard ไม่ถูกต้อง", 503)
    shared_policy = contract.get("sharedPolicy")
    output_schema = contract.get("outputSchema")
    agent_rows = contract.get("agents")
    quality_gate = shared_policy.get("qualityGate") if isinstance(shared_policy, dict) else None
    protective_fallback = (
        quality_gate.get("protectivePlanFallback")
        if isinstance(quality_gate, dict)
        and isinstance(quality_gate.get("protectivePlanFallback"), dict)
        else None
    )
    if (
        not isinstance(shared_policy, dict)
        or shared_policy.get("analysisMode") != "read_only"
        or shared_policy.get("sameSnapshotRequired") is not True
        or shared_policy.get("liveOrderSubmissionAllowed") is not False
        or shared_policy.get("runnerVoteTransport") != "schema_bound_final_json_v1"
        or shared_policy.get("localSnapshotReadPolicy") != "backend_validated_embedded_read_only"
        or shared_policy.get("reportTargetPropId") != AI_TRADE_COUNCIL_PROP_ID
        or not isinstance(output_schema, dict)
        or output_schema.get("type") != "object"
        or not isinstance(agent_rows, list)
        or len(agent_rows) != 3
        or not isinstance(quality_gate, dict)
        or quality_gate.get("schemaVersion") != "ai-trade-council-quality-gate-v2"
        or not isinstance(protective_fallback, dict)
        or protective_fallback.get("enabled") is not True
        or protective_fallback.get("trigger")
        != "directional_consensus_price_action_hold_null_prices_no_opposite_no_news_veto"
        or protective_fallback.get("source") != "backend_deterministic_fallback"
        or protective_fallback.get("policyVersion")
        != AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION
        or protective_fallback.get("closedBarsOnly") is not True
        or protective_fallback.get("atrPeriod") != 14
        or protective_fallback.get("minimumStopAtrMultiplier")
        != AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MINIMUM_STOP_ATR
        or protective_fallback.get("structureBufferAtrMultiplier")
        != AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_STRUCTURE_BUFFER_ATR
        or protective_fallback.get("maximumStructureDistanceAtr")
        != AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MAX_STRUCTURE_DISTANCE_ATR
        or protective_fallback.get("priceActionNoDataAllowed") is not False
        or protective_fallback.get("modelCallAllowed") is not False
        or protective_fallback.get("terminalActionAllowed") is not False
    ):
        raise RequestError("นโยบายสภา AI Trade ไม่ผ่านการตรวจสอบความปลอดภัย", 503)
    normalized_agents = []
    observed_ids: set[str] = set()
    for row in agent_rows:
        if not isinstance(row, dict):
            raise RequestError("รายการ Agent ในสัญญา Prompt ไม่ถูกต้อง", 503)
        agent_id = str(row.get("agentId") or "")
        role_id = str(row.get("roleId") or "")
        tool_id = str(row.get("toolId") or "")
        model_tier = str(row.get("modelTier") or "")
        prompt_template = str(row.get("promptTemplate") or "").strip()
        role_output_rule = str(row.get("roleOutputRule") or "").strip()
        if (
            agent_id not in AI_TRADE_COUNCIL_AGENT_ROLES
            or agent_id in observed_ids
            or role_id != AI_TRADE_COUNCIL_AGENT_ROLES[agent_id]
            or tool_id != AI_TRADE_COUNCIL_ALLOWED_TOOLS[agent_id]
            or model_tier not in {"specialist_balanced", "specialist_fast"}
            or "{{snapshotId}}" not in prompt_template
            or "{{snapshotArtifact}}" not in prompt_template
            or not prompt_template
            or not role_output_rule
        ):
            raise RequestError("บทบาทหรือเครื่องมือของ Agent ในสัญญา Prompt ไม่ถูกต้อง", 503)
        timeout_seconds = clamp_int(row.get("timeoutSeconds"), 120, 30, 300)
        output_limit = clamp_int(row.get("outputLimitChars"), 7000, 1000, 12000)
        normalized_agents.append({
            "agentId": agent_id,
            "roleId": role_id,
            "titleTh": redact_text(str(row.get("titleTh") or agent_id), 160),
            "toolId": tool_id,
            "modelTier": model_tier,
            "timeoutSeconds": timeout_seconds,
            "outputLimitChars": output_limit,
            "promptTemplate": prompt_template,
            "roleOutputRule": role_output_rule,
        })
        observed_ids.add(agent_id)
    if (
        observed_ids != set(AI_TRADE_COUNCIL_AGENT_ROLES)
        or [item["agentId"] for item in normalized_agents]
        != list(AI_TRADE_COUNCIL_AGENT_ROLES)
    ):
        raise RequestError("สัญญา Prompt ต้องมี Agent วิเคราะห์ครบ 3 ตัวเท่านั้น", 503)
    required_output_fields = {
        "snapshotId",
        "agentId",
        "roleId",
        "decision",
        "confidence",
        "horizonBars",
        "validUntilBarTime",
        "horizon",
        "observations",
        "invalidation",
        "evidence",
        "warnings",
        "stopLossPrice",
        "takeProfitPrice",
        "indicatorValidation",
        "volatilityState",
        "eventRisk",
    }
    if set(output_schema.get("required") or []) != required_output_fields:
        raise RequestError("Output Schema ของสภา AI Trade ไม่ครบถ้วน", 503)
    confidence_by_role = quality_gate.get("confidenceFloorByRole")
    if not isinstance(confidence_by_role, dict):
        confidence_by_role = {}

    def quality_float(field: str, default: float) -> float:
        value = quality_gate.get(field)
        try:
            parsed = float(value if value is not None else default)
        except (TypeError, ValueError, OverflowError):
            raise RequestError(
                f"AI Trade Council quality gate field {field} is invalid.",
                503,
            )
        if not math.isfinite(parsed):
            raise RequestError(
                f"AI Trade Council quality gate field {field} is invalid.",
                503,
            )
        return parsed

    normalized_quality_gate = {
        "schemaVersion": "ai-trade-council-quality-gate-v2",
        "minimumBars": clamp_int(quality_gate.get("minimumBars"), 120, 50, 300),
        "confidenceFloorDefault": clamp_int(quality_gate.get("confidenceFloorDefault"), 70, 0, 100),
        "confidenceFloorByRole": {
            role_id: clamp_int(
                confidence_by_role.get(role_id),
                clamp_int(quality_gate.get("confidenceFloorDefault"), 70, 0, 100),
                0,
                100,
            )
            for role_id in AI_TRADE_COUNCIL_AGENT_ROLES.values()
        },
        "horizonBars": clamp_int(quality_gate.get("horizonBars"), 1, 1, 20),
        "roundDeadlineSeconds": clamp_int(quality_gate.get("roundDeadlineSeconds"), 240, 60, 290),
        "maximumSnapshotSpreadPoints": clamp_int(quality_gate.get("maximumSnapshotSpreadPoints"), 1000, 1, 10_000_000),
        "maximumNewsAgeSeconds": clamp_int(quality_gate.get("maximumNewsAgeSeconds"), 86400, 300, 604800),
        "maximumFutureEvidenceSkewSeconds": clamp_int(quality_gate.get("maximumFutureEvidenceSkewSeconds"), 300, 0, 3600),
        "minimumDistinctNewsDomains": clamp_int(quality_gate.get("minimumDistinctNewsDomains"), 2, 2, 8),
        "minimumRewardRiskRatio": quality_float("minimumRewardRiskRatio", 1.0),
        "protectivePlanFallback": {
            "enabled": True,
            "trigger": str(protective_fallback.get("trigger") or ""),
            "source": "backend_deterministic_fallback",
            "policyVersion": (
                AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION
            ),
            "closedBarsOnly": True,
            "atrPeriod": 14,
            "minimumStopAtrMultiplier": (
                AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MINIMUM_STOP_ATR
            ),
            "structureBufferAtrMultiplier": (
                AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_STRUCTURE_BUFFER_ATR
            ),
            "maximumStructureDistanceAtr": (
                AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MAX_STRUCTURE_DISTANCE_ATR
            ),
            "priceActionNoDataAllowed": False,
            "modelCallAllowed": False,
            "terminalActionAllowed": False,
        },
        "volatilityLowPercent": quality_float("volatilityLowPercent", 0.15),
        "volatilityHighPercent": quality_float("volatilityHighPercent", 3.0),
    }
    if not (
        0 < normalized_quality_gate["minimumRewardRiskRatio"] <= 100
        and 0 <= normalized_quality_gate["volatilityLowPercent"]
        < normalized_quality_gate["volatilityHighPercent"] <= 100
    ):
        raise RequestError("AI Trade Council quality gate numeric policy is invalid.", 503)
    return {
        **contract,
        "sharedPolicy": {**shared_policy, "qualityGate": normalized_quality_gate},
        "agents": normalized_agents,
        "outputSchema": output_schema,
    }


def _render_ai_trade_council_prompt(
    row: dict,
    snapshot_id: str,
    snapshot_artifact: str,
    output_schema: dict,
) -> str:
    schema_text = json.dumps(output_schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prompt = (
        str(row.get("promptTemplate") or "")
        .replace("{{snapshotId}}", snapshot_id)
        .replace("{{snapshotArtifact}}", snapshot_artifact)
    )
    role_output_rule = str(row.get("roleOutputRule") or "").strip()
    prompt = (
        f"{prompt}\n\nRole-specific output rule: {role_output_rule}\n\n"
        "Backend จะตรวจและฝัง Snapshot JSON จาก Workspace ให้ใน Prompt ของ Runner โดยตรง "
        "ห้ามค้นหาไฟล์อื่น ห้ามใช้ Shell/Terminal และห้ามเปิด MT4/MT5 หรืออ่าน Secret ใด ๆ\n"
        "ตอบกลับเป็น JSON object เพียงหนึ่งก้อนเท่านั้น ห้ามครอบด้วย Markdown "
        f"และต้องตรงกับ schema ต่อไปนี้: {schema_text}"
    )
    if len(prompt) > 8000:
        raise RequestError("Prompt สำหรับสภา AI Trade ยาวเกินขีดจำกัด", 503)
    if contains_potential_secret(prompt) or _ai_trade_council_high_impact_reasons(
        str(row.get("toolId") or ""),
        prompt,
    ):
        raise RequestError("Prompt สำหรับสภา AI Trade ชนกฎความปลอดภัย", 503)
    return prompt


def _ai_trade_council_high_impact_reasons(tool_id: str, prompt: str) -> list[str]:
    # BUY is a read-only classification in this fixed output schema, not a
    # purchase instruction. Scrub only this exact enum token before applying
    # the unchanged global high-impact detector. The helper is used solely by
    # backend-owned Council prompt packets.
    classification_safe_prompt = re.sub(r"\bBUY\b", "DIRECTION_UP", prompt)
    return _high_impact_reasons(tool_id, classification_safe_prompt, "medium")


def _ai_trade_council_snapshot_artifact_core(snapshot_model: dict) -> dict:
    chart = snapshot_model.get("chartSnapshot") if isinstance(snapshot_model.get("chartSnapshot"), dict) else {}
    analysis_window = (
        chart.get("analysisWindow")
        if isinstance(chart.get("analysisWindow"), dict)
        else {}
    )
    snapshot_id = str(chart.get("snapshotId") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot_id):
        raise RequestError("Snapshot ID ไม่ถูกต้อง", 409)
    return {
        "schemaVersion": "ai-trade-council-input-v1",
        "snapshotId": snapshot_id,
        "sourceMode": "mt4_read_only_snapshot",
        "dailySummary": snapshot_model.get("dailySummary"),
        "chartSnapshot": chart,
        "policy": {
            "readOnly": True,
            "sameSnapshotRequired": True,
            "terminalActionsAllowed": False,
            "riskGuardVoting": False,
            "sourceBarCount": chart.get("sourceBarCount"),
            "analysisBarCountRequested": analysis_window.get("requestedBars"),
            "analysisBarCountUsed": analysis_window.get("usedBars"),
            "analysisWindow": analysis_window,
            "indicatorFormulaVersion": (
                AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION
            ),
            "qualityGate": snapshot_model.get("councilQualityGate"),
        },
    }


def _ai_trade_council_snapshot_artifact_digest(artifact: dict) -> str:
    """Hash only the immutable, schema-owned artifact payload."""
    canonical = {
        key: artifact.get(key)
        for key in (
            "schemaVersion",
            "snapshotId",
            "sourceMode",
            "dailySummary",
            "chartSnapshot",
            "policy",
        )
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_ai_trade_council_snapshot_artifact(snapshot_model: dict) -> str:
    core = _ai_trade_council_snapshot_artifact_core(snapshot_model)
    snapshot_id = str(core["snapshotId"])
    artifact_digest = _ai_trade_council_snapshot_artifact_digest(core)
    artifact = {
        **core,
        "createdAt": utc_now(),
        "artifactDigest": artifact_digest,
    }
    AI_TRADE_COUNCIL_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = (
        AI_TRADE_COUNCIL_SNAPSHOT_DIR
        / f"{artifact_digest}.json"
    )
    if artifact_path.exists():
        existing = read_json(artifact_path, None)
        if (
            not isinstance(existing, dict)
            or existing.get("artifactDigest") != artifact_digest
            or _ai_trade_council_snapshot_artifact_digest(existing)
            != artifact_digest
        ):
            raise RequestError(
                "Snapshot Artifact ชื่อซ้ำแต่เนื้อหาไม่ตรงกับ Digest",
                409,
            )
    else:
        # The full artifact digest already binds snapshotId plus the immutable
        # payload. A digest-only filename keeps the path below legacy Windows
        # MAX_PATH limits while preserving collision resistance and exact
        # content verification for every in-flight Council round.
        write_json(artifact_path, artifact, keep_backup=False)
    return artifact_path.relative_to(AI_TRADE_COUNCIL_WORKSPACE_DIR).as_posix()


def _extract_json_object(value: object) -> dict | None:
    text = str(value or "").strip()
    if not text:
        return None
    candidates = [text]
    fenced = re.fullmatch(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        candidates.insert(0, fenced.group(1))
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if 0 <= first_brace < last_brace:
        candidates.append(text[first_brace:last_brace + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def validate_ai_trade_council_vote(value: object, context: object) -> dict | None:
    """Return one sanitized vote only when it is bound to the expected snapshot and role."""
    if not isinstance(context, dict):
        return None
    parsed = _extract_json_object(value)
    if not isinstance(parsed, dict) or _snapshot_has_forbidden_keys(parsed):
        return None
    snapshot_id = str(context.get("snapshotId") or "")
    agent_id = str(context.get("agentId") or "")
    role_id = str(context.get("roleId") or "")
    if (
        parsed.get("snapshotId") != snapshot_id
        or parsed.get("agentId") != agent_id
        or parsed.get("roleId") != role_id
        or AI_TRADE_COUNCIL_AGENT_ROLES.get(agent_id) != role_id
    ):
        return None
    expected_vote_fields = {
        "snapshotId",
        "agentId",
        "roleId",
        "decision",
        "confidence",
        "horizonBars",
        "validUntilBarTime",
        "horizon",
        "observations",
        "invalidation",
        "evidence",
        "warnings",
        "stopLossPrice",
        "takeProfitPrice",
        "indicatorValidation",
        "volatilityState",
        "eventRisk",
    }
    if set(parsed) != expected_vote_fields:
        return None
    decision = str(parsed.get("decision") or "").upper()
    confidence = _safe_snapshot_number(parsed.get("confidence"), minimum=0, maximum=100)
    if decision not in {"BUY", "HOLD", "SELL", "NO_DATA"} or confidence is None:
        return None
    horizon_bars = parsed.get("horizonBars")
    valid_until_bar_time = parsed.get("validUntilBarTime")
    expected_horizon_bars = context.get("horizonBars")
    expected_valid_until = context.get("validUntilBarTime")
    if (
        isinstance(horizon_bars, bool)
        or not isinstance(horizon_bars, int)
        or isinstance(valid_until_bar_time, bool)
        or not isinstance(valid_until_bar_time, int)
        or horizon_bars != expected_horizon_bars
        or valid_until_bar_time != expected_valid_until
    ):
        return None
    reference_price = _safe_snapshot_number(
        context.get("referencePrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    stop_loss_price = _safe_snapshot_number(
        parsed.get("stopLossPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    take_profit_price = _safe_snapshot_number(
        parsed.get("takeProfitPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    indicator_validation = parsed.get("indicatorValidation")
    volatility_state = parsed.get("volatilityState")
    event_risk = parsed.get("eventRisk")
    if role_id == "price_action" and decision in {"BUY", "SELL"}:
        if reference_price is None or stop_loss_price is None or take_profit_price is None:
            return None
        if decision == "BUY" and not stop_loss_price < reference_price < take_profit_price:
            return None
        if decision == "SELL" and not take_profit_price < reference_price < stop_loss_price:
            return None
    elif parsed.get("stopLossPrice") is not None or parsed.get("takeProfitPrice") is not None:
        return None
    if role_id == "technical":
        expected_volatility_state = str(context.get("volatilityState") or "")
        if (
            indicator_validation not in {"PASS", "HOLD", "NO_DATA"}
            or volatility_state != expected_volatility_state
            or volatility_state not in {"LOW", "NORMAL", "HIGH"}
            or event_risk is not None
            or (decision in {"BUY", "SELL"} and indicator_validation != "PASS")
            or (decision == "NO_DATA" and indicator_validation != "NO_DATA")
        ):
            return None
    elif role_id == "price_action":
        if any(value is not None for value in (indicator_validation, volatility_state, event_risk)):
            return None
    elif role_id == "news":
        if (
            indicator_validation is not None
            or volatility_state is not None
            or event_risk not in {"ALLOW", "HOLD", "VETO"}
            or (event_risk == "VETO" and decision != "HOLD")
            or (event_risk == "HOLD" and decision not in {"HOLD", "NO_DATA"})
            or (decision in {"BUY", "SELL"} and event_risk != "ALLOW")
        ):
            return None
    horizon = redact_text(str(parsed.get("horizon") or "").strip(), 240)
    invalidation = redact_text(str(parsed.get("invalidation") or "").strip(), 800)
    observations = [
        redact_text(str(item), 600)
        for item in (parsed.get("observations") if isinstance(parsed.get("observations"), list) else [])[:5]
        if str(item).strip()
    ]
    warnings = [
        redact_text(str(item), 600)
        for item in (parsed.get("warnings") if isinstance(parsed.get("warnings"), list) else [])[:5]
        if str(item).strip()
    ]
    evidence = []
    raw_evidence = parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else []
    for item in raw_evidence[:8]:
        if not isinstance(item, dict):
            continue
        label = redact_text(str(item.get("label") or "").strip(), 600)
        observed_at = redact_text(str(item.get("observedAt") or "").strip(), 120)
        source_url = str(item.get("sourceUrl") or "").strip()
        if source_url and not re.fullmatch(r"https?://[^\s]{1,1000}", source_url):
            source_url = ""
        if label and observed_at:
            evidence.append({
                "label": label,
                "observedAt": observed_at,
                "sourceUrl": source_url or None,
            })
    if not horizon or not invalidation or not observations:
        return None
    news_evidence = {
        "fresh": None,
        "distinctDomains": 0,
        "requiredDistinctDomains": None,
        "reasonCodes": [],
    }
    if role_id == "news":
        quality_policy = (
            context.get("qualityPolicy")
            if isinstance(context.get("qualityPolicy"), dict)
            else {}
        )
        maximum_age = clamp_int(quality_policy.get("maximumNewsAgeSeconds"), 86400, 300, 604800)
        future_skew = clamp_int(quality_policy.get("maximumFutureEvidenceSkewSeconds"), 300, 0, 3600)
        required_domains = clamp_int(quality_policy.get("minimumDistinctNewsDomains"), 2, 2, 8)
        now = datetime.now(timezone.utc)
        domains: set[str] = set()
        fresh_items = 0
        for item in evidence:
            source_url = str(item.get("sourceUrl") or "")
            observed = parse_iso(str(item.get("observedAt") or ""))
            if not source_url or observed is None:
                continue
            observed_utc = observed.astimezone(timezone.utc)
            age_seconds = (now - observed_utc).total_seconds()
            if -future_skew <= age_seconds <= maximum_age:
                hostname = (urlparse(source_url).hostname or "").lower()
                if hostname.startswith("www."):
                    hostname = hostname[4:]
                if hostname:
                    domains.add(hostname)
                    fresh_items += 1
        news_evidence = {
            "fresh": fresh_items >= required_domains,
            "distinctDomains": len(domains),
            "requiredDistinctDomains": required_domains,
            "reasonCodes": [],
        }
        if fresh_items < required_domains:
            news_evidence["reasonCodes"].append("insufficient_fresh_news_evidence")
        if len(domains) < required_domains:
            news_evidence["reasonCodes"].append("news_sources_not_distinct")
        if decision in {"BUY", "SELL"} and (
            fresh_items < required_domains or len(domains) < required_domains
        ):
            return None
    return {
        "schemaVersion": "ai-trade-council-vote-v3",
        "snapshotId": snapshot_id,
        "agentId": agent_id,
        "roleId": role_id,
        "decision": decision,
        "confidence": confidence,
        "horizonBars": horizon_bars,
        "validUntilBarTime": valid_until_bar_time,
        "stopLossPrice": stop_loss_price if role_id == "price_action" and decision in {"BUY", "SELL"} else None,
        "takeProfitPrice": take_profit_price if role_id == "price_action" and decision in {"BUY", "SELL"} else None,
        "indicatorValidation": indicator_validation if role_id == "technical" else None,
        "volatilityState": volatility_state if role_id == "technical" else None,
        "eventRisk": event_risk if role_id == "news" else None,
        "horizon": horizon,
        "observations": observations,
        "invalidation": invalidation,
        "evidence": evidence,
        "warnings": warnings,
        "newsEvidence": news_evidence if role_id == "news" else None,
        "readOnly": True,
    }


def validate_ai_trade_council_vote_result(result: object, context: object) -> dict | None:
    """Validate the exact schema-bound Council vote returned as finalMessage."""
    if not isinstance(result, dict):
        return None
    return validate_ai_trade_council_vote(result.get("finalMessage"), context)


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
        if codex_status in {"ready", "ready_guarded"}:
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


def _discovery_lab_readiness_read_model(
    prop_id: str,
    terminals: dict,
    metatrader_selection: dict,
) -> dict:
    applicable = prop_id in {
        "terminal_workstation",
        "right_server_racks",
    }
    selected = (
        metatrader_selection.get("selectedCandidate")
        if isinstance(metatrader_selection.get("selectedCandidate"), dict)
        else None
    )
    mt4_platform = terminals.get("platforms", {}).get("mt4", {})
    mt4_detected = int(mt4_platform.get("installedCount") or 0) > 0
    selected_mt4 = bool(selected and selected.get("platform") == "mt4")
    terminal_running = bool(
        selected_mt4
        and selected.get("runningState") == "platform_running_detected"
    )
    stages = [
        {"id": "workflow_contract", "labelTh": "กติกา Discovery Lab", "status": "ready", "ready": True},
        {"id": "mt4_detected", "labelTh": "ตรวจพบ MT4", "status": "detected" if mt4_detected else "not_found", "ready": mt4_detected},
        {"id": "target_selected", "labelTh": "เลือก MT4 เป้าหมาย", "status": "configured" if selected_mt4 else "not_configured", "ready": selected_mt4},
        {"id": "terminal_running", "labelTh": "MT4 กำลังทำงาน", "status": "detected" if terminal_running else "not_found", "ready": terminal_running},
        {"id": "plugin_binding", "labelTh": "ผูก Plugin กับ HQ", "status": "coming_soon", "ready": False},
        {"id": "front_office_adapter", "labelTh": "ควบคุม MetaEditor / Strategy Tester แบบมองเห็นจริง", "status": "coming_soon", "ready": False},
        {"id": "compile_proof", "labelTh": "หลักฐาน Compile 0 errors และไฟล์ .ex4", "status": "coming_soon", "ready": False},
        {"id": "visual_backtest_proof", "labelTh": "Visual Backtest ก่อน Optimization", "status": "coming_soon", "ready": False},
    ]
    if not applicable:
        detail = "Dashboard นี้ไม่ใช่จุดทำงานของ EA Discovery Lab MT4"
    elif not mt4_detected:
        detail = "ยังไม่พบ MT4 และยังไม่มี Adapter สั่งงานจริง"
    elif not selected_mt4:
        detail = "พบ MT4 แล้ว แต่ยังต้องเลือกเป้าหมาย และ Adapter สั่งงานจริงยังไม่พร้อม"
    elif not terminal_running:
        detail = "เลือก MT4 แล้ว แต่ยังไม่พบว่ากำลังทำงาน และ Adapter สั่ง MetaEditor / Backtest ยังไม่พร้อม"
    else:
        detail = "MT4 พร้อมในระดับตรวจพบและเลือกเป้าหมาย แต่ Plugin Binding กับ Front-Office Adapter ยังไม่พร้อม"
    return {
        "applicable": applicable,
        "status": "coming_soon" if applicable else "not_required",
        "detailTh": detail,
        "pluginId": "metafx-ea-discovery-lab-mt4",
        "pluginBindingAvailable": False,
        "adapterReady": False,
        "realExecutionAvailable": False,
        "selectedMt4": selected_mt4,
        "terminalRunning": terminal_running,
        "offlineDemoOnly": True,
        "liveTradingAllowed": False,
        "stages": stages if applicable else [],
    }


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
    discovery_lab_readiness = _discovery_lab_readiness_read_model(
        prop_id,
        terminal_model,
        metatrader_selection,
    )
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
    if prop_id == AI_TRADE_COUNCIL_PROP_ID:
        snapshot_model = metatrader_snapshot_read_model(prop_id)
        snapshot_adapter = (
            snapshot_model.get("adapter")
            if isinstance(snapshot_model.get("adapter"), dict)
            else {}
        )
        chart_snapshot = (
            snapshot_model.get("chartSnapshot")
            if isinstance(snapshot_model.get("chartSnapshot"), dict)
            else {}
        )
        snapshot_ready = (
            snapshot_adapter.get("ready") is True
            and chart_snapshot.get("available") is True
        )
        codex_runtime_status = str((bridge_model.get("codex") or {}).get("status") or "")
        codex_ready = codex_runtime_status in {"ready", "ready_guarded"}
        quota_ready = (
            quota_model.get("ok") is True
            and quota_model.get("stale") is not True
            and quota_model.get("limitReached") is not True
        )
        operator_auto = load_operator_mode_record().get("mode") == "auto_guarded"
        trade_gateway = mt4_trade_gateway_status_read_model()
        gateway_init_status = (
            trade_gateway.get("initStatus")
            if isinstance(trade_gateway.get("initStatus"), dict)
            else {}
        )
        gateway_init_message = _mt4_trade_gateway_init_status_message_th(
            gateway_init_status
        )
        for item in items:
            item_id = str(item.get("id") or "")
            if item_id == "trading_state_adapter":
                item.update({
                    "adapterStatus": "implemented_unified_ea_snapshot",
                    "statusSource": "mt4_snapshot_probe",
                    "status": (
                        "connected"
                        if snapshot_ready
                        else str(snapshot_adapter.get("status") or "awaiting_snapshot")
                    ),
                    "detailTh": (
                        "รับ Snapshot กราฟและสรุปประจำวันจาก MetafxHQ AI Council EA แล้ว"
                        if snapshot_ready
                        else {
                            "stale": "Snapshot ล่าสุดเก่าเกินกำหนด กรุณาตรวจ MetafxHQ AI Council EA ที่กราฟ MT4",
                            "not_selected": "ยังไม่ได้เลือก MT4 เป้าหมายสำหรับ Analytics Console",
                            "unsupported_platform": "จุดนี้ต้องเลือก MT4 สำหรับ MetafxHQ AI Council EA รุ่นปัจจุบัน",
                            "invalid_snapshot": "พบไฟล์ Snapshot แต่ข้อมูลไม่ผ่าน Schema ความปลอดภัย",
                        }.get(
                            str(snapshot_adapter.get("status") or ""),
                            "รอ Snapshot แรกจาก MetafxHQ AI Council EA บนกราฟ MT4 (ค่าเริ่มต้น Shadow ไม่ส่ง Order)",
                        )
                    ),
                    "checkedAt": chart_snapshot.get("observedAt"),
                    "cacheHit": False,
                    "cacheAgeSeconds": chart_snapshot.get("ageSeconds"),
                    "stale": str(snapshot_adapter.get("status") or "") == "stale",
                })
            elif item_id == "ai_trader_ensemble":
                if not snapshot_ready:
                    ensemble_status = "waiting_snapshot"
                    ensemble_detail = "รอ Snapshot กราฟที่สดใหม่ก่อนส่งให้ Agent ทั้ง 3 ตัว"
                elif not codex_ready:
                    ensemble_status = "unavailable"
                    ensemble_detail = "Snapshot พร้อมแล้ว แต่ Codex Runner ยังไม่พร้อม"
                elif not quota_ready:
                    ensemble_status = "waiting_quota"
                    ensemble_detail = "Snapshot และ Codex พร้อมแล้ว แต่ Rate Limit ยังไม่พร้อมสำหรับรอบใหม่"
                elif not operator_auto:
                    ensemble_status = "disabled"
                    ensemble_detail = "กรุณาเปิด Full Access แบบมีระบบป้องกันเพื่อรัน Agent อัตโนมัติ"
                else:
                    ensemble_status = "ready"
                    ensemble_detail = "พร้อมส่ง Snapshot เดียวกันให้ Agent 3 ตัววิเคราะห์แบบ Read-only"
                item.update({
                    "adapterStatus": "implemented_guarded_manual",
                    "statusSource": "backend_council_readiness",
                    "status": ensemble_status,
                    "detailTh": ensemble_detail,
                    "checkedAt": utc_now(),
                    "cacheHit": False,
                    "cacheAgeSeconds": 0,
                    "stale": False,
                })
            elif item_id == "mt4_trade_gateway":
                gateway_connected = trade_gateway.get("connected") is True
                gateway_detail = (
                    f"MetafxHQ AI Council EA เชื่อมแล้วในโหมด {trade_gateway.get('mode')} "
                    f"และใช้ Fixed Lot {trade_gateway.get('fixedLot')} จาก Inputs ของ EA"
                    if gateway_connected
                    else "Source พร้อมแล้ว แต่ยังต้อง Compile และติด MetafxHQ AI Council EA ที่ MT4 เป้าหมาย"
                )
                if gateway_init_message:
                    gateway_detail = f"{gateway_detail} • {gateway_init_message}"
                item.update({
                    "adapterStatus": "implemented_ea_gateway",
                    "statusSource": "mt4_trade_gateway_status",
                    "status": (
                        "connected"
                        if gateway_connected
                        else str(trade_gateway.get("status") or "awaiting_ea")
                    ),
                    "detailTh": gateway_detail,
                    "checkedAt": (
                        trade_gateway.get("observedAt")
                        or gateway_init_status.get("observedAt")
                    ),
                    "cacheHit": False,
                    "cacheAgeSeconds": (
                        trade_gateway.get("ageSeconds")
                        if trade_gateway.get("ageSeconds") is not None
                        else gateway_init_status.get("ageSeconds")
                    ),
                    "stale": trade_gateway.get("reasonCode") == "gateway_status_stale",
                })
            elif item_id == "kill_switch_adapter":
                item.update({
                    "adapterStatus": "implemented_in_trade_gateway",
                    "statusSource": "mt4_trade_gateway_status",
                    "status": (
                        "active"
                        if trade_gateway.get("killSwitchActive") is True
                        else "ready"
                        if trade_gateway.get("connected") is True
                        else "awaiting_ea"
                    ),
                    "detailTh": (
                        "Kill Switch กำลังหยุดการรับคำสั่งซื้อขาย"
                        if trade_gateway.get("killSwitchActive") is True
                        else "Kill Switch พร้อมหยุด Gateway"
                        if trade_gateway.get("connected") is True
                        else "Kill Switch จะพร้อมเมื่อเชื่อม MetafxHQ AI Council EA"
                    ),
                    "checkedAt": trade_gateway.get("observedAt"),
                    "cacheHit": False,
                    "cacheAgeSeconds": trade_gateway.get("ageSeconds"),
                    "stale": trade_gateway.get("reasonCode") == "gateway_status_stale",
                })
            elif item_id == "live_trading":
                item.update({
                    "adapterStatus": "ea_local_arm_required",
                    "statusSource": "mt4_trade_gateway_status",
                    "status": (
                        "ready"
                        if trade_gateway.get("liveOrderExecutionAvailable") is True
                        else "demo_ready"
                        if trade_gateway.get("demoOrderExecutionAvailable") is True
                        else "shadow"
                        if trade_gateway.get("shadowValidationAvailable") is True
                        else "disabled"
                    ),
                    "detailTh": (
                        "EA เปิดโหมด Live และ LiveArmed แล้ว"
                        if trade_gateway.get("liveOrderExecutionAvailable") is True
                        else "EA พร้อมส่ง Order เฉพาะบัญชี Demo"
                        if trade_gateway.get("demoOrderExecutionAvailable") is True
                        else "EA อยู่ในโหมด Shadow: ตรวจคำสั่งและ ACK แต่ไม่ส่ง Order"
                        if trade_gateway.get("shadowValidationAvailable") is True
                        else "การส่ง Order ยังปิดอยู่ที่ EA"
                    ),
                    "checkedAt": trade_gateway.get("observedAt"),
                    "cacheHit": False,
                    "cacheAgeSeconds": trade_gateway.get("ageSeconds"),
                    "stale": trade_gateway.get("reasonCode") == "gateway_status_stale",
                })
    if discovery_lab_readiness.get("applicable"):
        items.append({
            "id": "discovery_lab_mt4",
            "labelTh": "EA Discovery Lab MT4",
            "required": False,
            "adapterStatus": "workflow_contract_only_adapter_missing",
            "executionAdapterStatus": "coming_soon",
            "status": "coming_soon",
            "statusSource": "backend_readiness",
            "detailTh": discovery_lab_readiness["detailTh"],
            "action": None,
            "checkedAt": terminal_model.get("checkedAt"),
            "cacheHit": bool(terminal_model.get("cacheHit", False)),
            "cacheAgeSeconds": terminal_model.get("cacheAgeSeconds"),
            "stale": False,
        })
    item_map = {str(item.get("id") or ""): item for item in items}
    required_items = [item for item in items if item.get("required")]
    hard_problem = any(
        item.get("status")
        in {
            "needs_login",
            "not_configured",
            "not_found",
            "unavailable",
            "disabled",
            "awaiting_snapshot",
            "waiting_snapshot",
            "waiting_quota",
            "awaiting_ea",
            "active",
            "stale",
            "invalid_snapshot",
        }
        for item in required_items
    )
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
    operation_mode = {
        "current": "manual",
        "labelTh": "สั่งทำงานเอง",
        "aiEveryTwoHours": {
            "status": "coming_soon" if "ai_every_2_hours" in planned_modes else "not_required",
            "labelTh": "AI ตรวจและส่งรายงานทุก 2 ชั่วโมง" if "ai_every_2_hours" in planned_modes else "Dashboard นี้ไม่ใช้รอบอัตโนมัติ",
            "intervalMinutes": interval if isinstance(interval, int) else None,
            "backendOwned": True,
            "enabled": False,
        },
    }
    if prop_id == "left_analytics_console":
        automation = ai_trade_council_automation_read_model()
        automation_config = automation.get("config") if isinstance(automation.get("config"), dict) else {}
        automation_state = automation.get("state") if isinstance(automation.get("state"), dict) else {}
        automation_enabled = bool(automation_config.get("enabled"))
        automation_reason = str(automation_state.get("reason") or "")
        reason_labels = {
            "snapshot_stale": "เปิดอยู่ • รอ Snapshot ใหม่จาก MT4",
            "snapshot_unavailable": "เปิดอยู่ • รอ Snapshot จาก MT4",
            "baseline_required": "เปิดอยู่ • กำลังตั้งแท่งปัจจุบันเป็นจุดเริ่มต้น",
            "waiting_next_closed_bar": "เปิดอยู่ • รอแท่งใหม่ปิด",
            "unsupported_timeframe": "เปิดอยู่ • Timeframe นี้ใช้ปุ่มวิเคราะห์เอง",
            "daily_limit_reached": "พักชั่วคราว • ครบจำนวนรอบวันนี้",
            "quota_reserve_reached": "พักชั่วคราว • รักษา Rate Limit สำรอง",
            "automation_disabled": "ปิดอยู่ • ใช้ปุ่มวิเคราะห์เอง",
        }
        automation_label = (
            reason_labels.get(automation_reason, "เปิดอยู่ • วิเคราะห์เมื่อแท่งใหม่ปิด")
            if automation_enabled
            else "ปิดอยู่ • ใช้ปุ่มวิเคราะห์เอง"
        )
        operation_mode = {
            "current": "auto_on_new_closed_bar" if automation_enabled else "manual",
            "labelTh": "อัตโนมัติเมื่อแท่งใหม่ปิด" if automation_enabled else "สั่งวิเคราะห์เอง",
            "autoAnalysis": {
                "status": str(automation_state.get("status") or ("enabled" if automation_enabled else "disabled")),
                "reason": automation_reason or ("waiting_next_closed_bar" if automation_enabled else "automation_disabled"),
                "labelTh": automation_label,
                "pollSeconds": automation_config.get("pollSeconds"),
                "backendOwned": True,
                "enabled": automation_enabled,
            },
            "aiEveryTwoHours": {
                "status": "not_required",
                "labelTh": "ใช้แท่งที่ปิดล่าสุดเป็นตัวกระตุ้น ไม่ใช้รอบทุก 2 ชั่วโมง",
                "intervalMinutes": None,
                "backendOwned": True,
                "enabled": False,
            },
        }
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
        "operationMode": operation_mode,
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
        "discoveryLabReadiness": discovery_lab_readiness,
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
            AI_TRADE_COUNCIL_AUTOMATION_WAKE.set()

        terminal_state = peek_metatrader_status()
        available_candidates = _available_metatrader_candidates_from_store()
        terminal_state = {
            **terminal_state,
            "candidateCount": len(available_candidates),
            "candidates": available_candidates,
            "adapterConnection": "read_only_snapshot",
            "adapterReady": False,
        }
        snapshot_model = metatrader_snapshot_read_model(prop_id)
        snapshot_adapter = (
            snapshot_model.get("adapter")
            if isinstance(snapshot_model.get("adapter"), dict)
            else {}
        )
        terminal_state["adapterReady"] = snapshot_adapter.get("ready") is True
        checklist = dashboard_connection_checklist(prop_id, terminals=terminal_state)
        selection_model = checklist.get("metatraderSelection") if isinstance(checklist.get("metatraderSelection"), dict) else {}
        report = create_report({
            "type": "terminal_selection_report",
            "title": f"เลือกเป้าหมาย Terminal: {selected_candidate['labelTh']}",
            "summary": "บันทึกเป้าหมายไว้ใน Backend แบบ Local-only แล้ว โดยไม่ได้เปิดหรือควบคุม Terminal ขณะนี้รอ Snapshot จาก MetafxHQ AI Council EA",
            "ownerAgentId": owner,
            "linkedMissionId": mission["id"],
            "linkedPropId": prop_id,
            "status": "ready",
            "findings": [
                f"เป้าหมายที่เลือก: {selected_candidate['labelTh']}",
                f"Platform: {selected_candidate['platform'].upper()}",
                "สถานะการตั้งค่า: configured",
                "MetafxHQ AI Council EA: เตรียม Source แล้วและรอการ Compile/ติดตั้งบนกราฟแบบมองเห็นได้ โดยเริ่มใน Shadow Mode",
            ],
            "metrics": {
                "candidateId": selected_candidate["candidateId"],
                "platform": selected_candidate["platform"],
                "detectionStatus": "detected",
                "configurationStatus": "configured",
                "adapterReady": snapshot_adapter.get("ready") is True,
            },
            "risks": ["การเลือกเป้าหมายไม่เท่ากับเชื่อมต่อเพื่อ Backtest, Optimization หรือ Trading"],
            "nextActions": ["Compile และติดตั้ง MetafxHQ AI Council EA บนกราฟ MT4 ที่เลือก", "เริ่มด้วย Shadow Mode แล้วรอ Snapshot ล่าสุด", "ยังไม่เปิด Demo/Live จนกว่าจะทดสอบ Gateway"],
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
            "adapterConnection": "read_only_snapshot",
            "adapterReady": snapshot_adapter.get("ready") is True,
        })
        selection_response = {
            "propId": prop_id,
            "status": str(selection_model.get("status") or "selected"),
            "configurationStatus": str(selection_model.get("configurationStatus") or "configured"),
            "selectedCandidate": selection_model.get("selectedCandidate") or selected_candidate,
            "selectedAt": selection_model.get("selectedAt") or selected_at,
            "adapterConnection": "read_only_snapshot",
            "adapterReady": snapshot_adapter.get("ready") is True,
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


def _ai_trade_council_rate_preflight(prompt_contract: dict) -> list[dict]:
    """Check all three worker buckets before creating any Council mission."""
    tiers = load_orchestration_contract().get("modelTiers") or {}
    blockers: list[dict] = []
    rows = (
        prompt_contract.get("agents")
        if isinstance(prompt_contract, dict)
        and isinstance(prompt_contract.get("agents"), list)
        else []
    )
    for row in rows:
        if not isinstance(row, dict):
            continue
        agent_id = str(row.get("agentId") or "")
        tool_id = str(row.get("toolId") or "")
        tier_id = str(row.get("modelTier") or role_default_model_tier(agent_id))
        tier = tiers.get(tier_id) if isinstance(tiers, dict) else {}
        tier = tier if isinstance(tier, dict) else {}
        max_runs = clamp_int(tier.get("maxRunsPerHour"), 12, 1, 200)
        allowed, retry_after = check_rate_limit(
            f"real:{agent_id}:{tool_id}:{tier_id}",
            max_runs,
            consume=False,
        )
        if not allowed:
            blockers.append({
                "agentId": agent_id,
                "roleId": safe_reference(row.get("roleId")),
                "titleTh": redact_text(str(row.get("titleTh") or agent_id), 160),
                "retryAfterSeconds": max(1, min(3600, int(retry_after))),
                "reasonCode": "local_rate_limited",
            })
    return blockers


def run_ai_trade_council_analysis(
    payload: dict,
    *,
    automation_context: dict | None = None,
) -> dict:
    """Serialize manual and scheduled Council queue creation."""
    with AI_TRADE_COUNCIL_QUEUE_LOCK:
        return _run_ai_trade_council_analysis_unlocked(
            payload,
            automation_context=automation_context,
        )


def _run_ai_trade_council_analysis_unlocked(
    payload: dict,
    *,
    automation_context: dict | None = None,
) -> dict:
    """Queue exactly three snapshot-bound Codex analyses; never control MT4."""
    if not isinstance(payload, dict) or set(payload) - {
        "propId",
        "snapshotId",
        "analysisBarCount",
    }:
        raise RequestError(
            (
                "คำขอวิเคราะห์รับเฉพาะ propId, snapshotId "
                "และ analysisBarCount เท่านั้น"
            ),
            422,
        )
    requested_analysis_bar_count = (
        _configured_ai_trade_council_analysis_bar_count()
    )
    required_votes = _configured_ai_trade_council_required_votes()
    if "analysisBarCount" in payload:
        requested_analysis_bar_count = (
            _valid_ai_trade_council_analysis_bar_count(
                payload.get("analysisBarCount")
            )
        )
        if requested_analysis_bar_count is None:
            raise RequestError(
                "จำนวนแท่งวิเคราะห์ต้องเป็น 120, 180, 240 หรือ 300 เท่านั้น",
                422,
            )
    prop_id = str(payload.get("propId") or AI_TRADE_COUNCIL_PROP_ID).strip()
    if prop_id != AI_TRADE_COUNCIL_PROP_ID:
        raise RequestError("สภา AI Trade ใช้งานที่หน้าจอ Analytics Console เท่านั้น", 422)
    if load_operator_mode_record().get("mode") != "auto_guarded":
        raise RequestError("กรุณาเปิดโหมด Full Access แบบมีระบบป้องกันก่อนเริ่มวิเคราะห์", 409)
    snapshot_model = metatrader_snapshot_read_model(prop_id)
    try:
        evaluate_ai_trade_council_outcomes(snapshot_model)
    except (DataIntegrityError, OSError, ValueError):
        append_audit({
            "type": "ai_trade_council.outcome_evaluation_skipped",
            "reason": "snapshot_or_runtime_unavailable",
        })
    adapter = snapshot_model.get("adapter") if isinstance(snapshot_model.get("adapter"), dict) else {}
    chart = snapshot_model.get("chartSnapshot") if isinstance(snapshot_model.get("chartSnapshot"), dict) else {}
    if (
        adapter.get("ready") is not True
        or chart.get("available") is not True
        or not re.fullmatch(r"[0-9a-f]{64}", str(chart.get("snapshotId") or ""))
    ):
        raise RequestError(
            "ยังไม่มี Snapshot กราฟ MT4 ที่สดพอสำหรับ Agent ทั้ง 3 ตัว กรุณาติดตั้ง MetafxHQ AI Council EA ในโหมด Shadow แล้วรอข้อมูลล่าสุด",
            409,
        )
    requested_snapshot_id = str(payload.get("snapshotId") or "").strip()
    if requested_snapshot_id:
        if not re.fullmatch(r"[0-9a-f]{64}", requested_snapshot_id):
            raise RequestError("Snapshot ID ที่ส่งมาไม่ถูกต้อง", 422)
        if not secrets.compare_digest(
            requested_snapshot_id,
            str(chart.get("snapshotId") or ""),
        ):
            raise RequestError("Snapshot เปลี่ยนแล้ว กรุณารีเฟรชข้อมูลก่อนเริ่มวิเคราะห์", 409)

    source_bar_count = len(
        chart.get("bars") if isinstance(chart.get("bars"), list) else []
    )
    try:
        snapshot_model = _ai_trade_council_windowed_snapshot(
            snapshot_model,
            requested_analysis_bar_count,
        )
    except RequestError:
        append_audit({
            "type": "ai_trade_council.analysis_window_blocked",
            "snapshotId": chart.get("snapshotId"),
            "sourceBarCount": source_bar_count,
            "requestedAnalysisBarCount": requested_analysis_bar_count,
            "usedAnalysisBarCount": 0,
            "indicatorFormulaVersion": (
                AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION
            ),
            "reason": "insufficient_closed_bars",
            "closedBarsOnly": True,
            "terminalActions": False,
        })
        raise
    chart = snapshot_model["chartSnapshot"]
    analysis_window = chart["analysisWindow"]
    used_analysis_bar_count = int(analysis_window["usedBars"])
    analysis_context_metadata = {
        "sourceBarCount": source_bar_count,
        "requestedAnalysisBarCount": requested_analysis_bar_count,
        "usedAnalysisBarCount": used_analysis_bar_count,
        "analysisWindow": analysis_window,
        "indicatorFormulaVersion": (
            AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION
        ),
    }

    closed_bar_identity, closed_bar_identity_reason = (
        _ai_trade_council_closed_bar_identity(snapshot_model)
    )
    closed_bar_packet = (
        {
            "candidateId": closed_bar_identity["candidateId"],
            "streamKey": closed_bar_identity["streamKey"],
            "symbol": closed_bar_identity["symbol"],
            "timeframe": closed_bar_identity["timeframe"],
            "closedBarTime": closed_bar_identity["lastClosedBarTime"],
        }
        if closed_bar_identity
        else None
    )
    automation_packet = None
    if automation_context is not None:
        if not isinstance(automation_context, dict):
            raise RequestError("Invalid AI Trade Council automation context.", 422)
        if closed_bar_identity is None:
            raise RequestError(
                f"AI Trade Council closed-bar identity is unavailable: {closed_bar_identity_reason}",
                409,
            )
        expected = {
            "triggerMode": "last_closed_candle_time_change",
            "streamKey": closed_bar_identity["streamKey"],
            "symbol": closed_bar_identity["symbol"],
            "timeframe": closed_bar_identity["timeframe"],
            "closedBarTime": closed_bar_identity["lastClosedBarTime"],
            "analysisBarCount": requested_analysis_bar_count,
        }
        for field, expected_value in expected.items():
            if automation_context.get(field) != expected_value:
                raise RequestError(
                    f"AI Trade Council automation context mismatch: {field}",
                    409,
                )
        day_key = str(automation_context.get("dayKey") or "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day_key):
            raise RequestError("Invalid AI Trade Council automation day key.", 422)
        automation_packet = {
            "source": "backend_scheduler",
            **expected,
            "dayKey": day_key,
        }

    prompt_contract = load_ai_trade_council_prompt_contract()
    quality_policy = prompt_contract["sharedPolicy"]["qualityGate"]
    council_quality_gate = _ai_trade_council_data_quality_gate(
        snapshot_model,
        quality_policy,
    )
    if council_quality_gate.get("passed") is not True:
        append_audit({
            "type": "ai_trade_council.quality_gate_blocked",
            "stage": "input",
            "snapshotId": chart.get("snapshotId"),
            "reasonCodes": council_quality_gate.get("reasonCodes"),
            "observedBars": council_quality_gate.get("observedBars"),
            **analysis_context_metadata,
            "terminalActions": False,
        })
        raise RequestError(
            "AI Trade Council input data did not pass the deterministic quality gate.",
            409,
        )
    if closed_bar_identity is None:
        raise RequestError(
            f"AI Trade Council closed-bar identity is unavailable: {closed_bar_identity_reason}",
            409,
        )
    horizon_bars = int(quality_policy["horizonBars"])
    valid_until_bar_time = _ai_trade_council_expected_valid_until(
        int(closed_bar_identity["lastClosedBarTime"]),
        str(closed_bar_identity["timeframe"]),
        horizon_bars,
    )
    if valid_until_bar_time is None:
        raise RequestError("AI Trade Council horizon cannot be normalized.", 409)
    round_started_at = datetime.now(timezone.utc)
    round_deadline_at = round_started_at + timedelta(
        seconds=int(quality_policy["roundDeadlineSeconds"])
    )
    council_quality_gate.update({
        "confidenceFloorDefault": quality_policy["confidenceFloorDefault"],
        "confidenceFloorByRole": quality_policy["confidenceFloorByRole"],
        "horizonBars": horizon_bars,
        "validUntilBarTime": valid_until_bar_time,
        "roundStartedAt": round_started_at.isoformat().replace("+00:00", "Z"),
        "roundDeadlineAt": round_deadline_at.isoformat().replace("+00:00", "Z"),
        "maximumNewsAgeSeconds": quality_policy["maximumNewsAgeSeconds"],
        "minimumDistinctNewsDomains": quality_policy["minimumDistinctNewsDomains"],
        "minimumRewardRiskRatio": quality_policy["minimumRewardRiskRatio"],
        **analysis_context_metadata,
    })
    snapshot_model["councilQualityGate"] = council_quality_gate
    contract_digest = payload_digest(
        json.dumps(prompt_contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )[:12]
    snapshot_id = str(chart["snapshotId"])
    bid = _safe_snapshot_number(chart.get("bid"), minimum=0.00000001, maximum=1_000_000_000)
    ask = _safe_snapshot_number(chart.get("ask"), minimum=0.00000001, maximum=1_000_000_000)
    reference_price = (
        round((bid + ask) / 2, 8)
        if bid is not None and ask is not None
        else _safe_snapshot_number(chart.get("price"), minimum=0.00000001, maximum=1_000_000_000)
    )
    if reference_price is None:
        raise RequestError("Snapshot ไม่มีราคาอ้างอิงที่ปลอดภัยสำหรับตรวจ SL และ TP", 409)
    parent_idempotency = (
        f"ai-council-auto-{automation_packet['streamKey'][:24]}-"
        f"{automation_packet['closedBarTime']}-{contract_digest}-v{required_votes}"
        if automation_packet
        else f"ai-council-{snapshot_id[:32]}-{contract_digest}-v{required_votes}"
    )
    round_retry_suffix = ""
    existing_parent = (
        find_mission_by_idempotency(parent_idempotency)
        if automation_packet
        else _latest_ai_trade_council_retry_parent(parent_idempotency)
    )
    if automation_packet and existing_parent is None:
        existing_parent = _find_ai_trade_council_parent_by_closed_bar(
            automation_packet["streamKey"],
            automation_packet["closedBarTime"],
        )
    if existing_parent:
        existing_children = [
            mission
            for mission in load_missions()
            if mission.get("parentMissionId") == existing_parent.get("id")
        ]
        existing_context = (
            existing_parent.get("analysisContext")
            if isinstance(existing_parent.get("analysisContext"), dict)
            else {}
        )
        existing_requested_bars = existing_context.get(
            "requestedAnalysisBarCount"
        )
        if (
            isinstance(existing_requested_bars, int)
            and not isinstance(existing_requested_bars, bool)
            and existing_requested_bars != requested_analysis_bar_count
        ):
            raise RequestError(
                "This Snapshot already has a Council round with a different analysis bar count. Start the new scope on the next closed candle.",
                409,
            )
        existing_ids = {str(item.get("owner") or "") for item in existing_children}
        if (
            automation_packet is None
            and _ai_trade_council_manual_retry_allowed(existing_parent)
        ):
            previous_parent_id = safe_reference(existing_parent.get("id"))
            parent_idempotency, round_retry_suffix = (
                _next_ai_trade_council_retry_idempotency(parent_idempotency)
            )
            existing_parent = None
            existing_children = []
            append_audit({
                "type": "ai_trade_council.manual_retry_started",
                "previousMissionId": previous_parent_id,
                "snapshotId": snapshot_id,
                "retryIdempotencyKey": parent_idempotency,
                "terminalActions": False,
            })
        elif existing_ids == set(AI_TRADE_COUNCIL_AGENT_ROLES) and len(existing_children) == 3:
            refreshed_parent = refresh_parent_mission(
                safe_reference(existing_parent.get("id"))
            )
            if refreshed_parent:
                existing_parent = refreshed_parent
            existing_context = (
                existing_parent.get("analysisContext")
                if isinstance(existing_parent.get("analysisContext"), dict)
                else {}
            )
            existing_analysis_window = (
                existing_context.get("analysisWindow")
                if isinstance(existing_context.get("analysisWindow"), dict)
                else None
            )
            existing_gateway = (
                existing_parent.get("tradeGateway")
                if isinstance(existing_parent.get("tradeGateway"), dict)
                else {}
            )
            existing_analysis_metadata = {
                "sourceBarCount": existing_context.get("sourceBarCount"),
                "requestedAnalysisBarCount": existing_context.get(
                    "requestedAnalysisBarCount"
                ),
                "usedAnalysisBarCount": existing_context.get(
                    "usedAnalysisBarCount"
                ),
                "analysisWindow": existing_analysis_window,
                "indicatorFormulaVersion": existing_context.get(
                    "indicatorFormulaVersion"
                ),
            }
            append_audit({
                "type": "ai_trade_council.existing_returned",
                "missionId": existing_parent.get("id"),
                "snapshotId": snapshot_id,
                **existing_analysis_metadata,
                "terminalActions": (
                    existing_gateway.get("commandPublished") is True
                ),
            })
            return {
                "ok": True,
                "kind": "ai_trade_council_existing",
                "status": str(existing_parent.get("status") or "queued"),
                "propId": prop_id,
                "snapshotId": snapshot_id,
                **existing_analysis_metadata,
                "readOnly": True,
                "terminalActions": existing_gateway.get("commandPublished") is True,
                "tradeGateway": existing_gateway,
                "manager": mission_read_model_item(existing_parent),
                "parent": mission_read_model_item(existing_parent),
                "subtasks": [mission_read_model_item(item) for item in existing_children],
                "analysisReadiness": snapshot_model.get("analysisReadiness"),
                "_httpStatus": 200,
            }

    active_parent = _active_ai_trade_council_parent()
    if active_parent:
        append_audit({
            "type": "ai_trade_council.analysis_blocked",
            "reason": "council_round_already_active",
            "activeMissionId": safe_reference(active_parent.get("id")),
            "terminalActions": False,
        })
        raise RequestError(
            "มีรอบวิเคราะห์ของ Specialist 3 ตัวกำลังทำงานอยู่ กรุณารอให้รอบนี้จบก่อนเริ่มรอบใหม่",
            409,
        )

    bridge = bridge_status()
    codex_status = str((bridge.get("codex") or {}).get("status") or "")
    if codex_status not in {"ready", "ready_guarded"}:
        raise RequestError("Codex Runner ยังไม่พร้อม จึงยังไม่สร้างงานวิเคราะห์", 503)
    quota = codex_rate_limits()
    if quota.get("ok") is not True or quota.get("stale") is True:
        raise RequestError("ยังตรวจสอบ Rate Limit ของ Codex ไม่ได้ จึงหยุดไว้ก่อนแบบปลอดภัย", 503)
    if quota.get("limitReached") is True:
        raise RequestError("Codex ถึง Rate Limit แล้ว กรุณารอรอบถัดไป", 429)
    allowed, retry_after = check_rate_limit(
        "ai-trade-council:analyze",
        12,
        cooldown_seconds=3,
        consume=False,
    )
    if not allowed:
        raise RequestError(f"กรุณารอ {retry_after} วินาทีก่อนเริ่มรอบวิเคราะห์ใหม่", 429)

    snapshot_artifact = _write_ai_trade_council_snapshot_artifact(snapshot_model)
    snapshot_artifact_digest = _ai_trade_council_snapshot_artifact_digest(
        _ai_trade_council_snapshot_artifact_core(snapshot_model)
    )
    prepared_rows = []
    for row in prompt_contract["agents"]:
        prompt = _render_ai_trade_council_prompt(
            row,
            snapshot_id,
            snapshot_artifact,
            prompt_contract["outputSchema"],
        )
        eligibility = auto_guarded_eligibility({
            "toolId": row["toolId"],
            "owner": row["agentId"],
            "risk": "medium",
            "detail": prompt,
            "analysisContext": {
                "kind": "ai_trade_council_vote",
                "snapshotId": snapshot_id,
                "snapshotArtifact": snapshot_artifact,
                "snapshotArtifactDigest": snapshot_artifact_digest,
                "agentId": row["agentId"],
                "roleId": row["roleId"],
                "referencePrice": reference_price,
                "horizonBars": horizon_bars,
                "validUntilBarTime": valid_until_bar_time,
                "volatilityState": (council_quality_gate.get("technical") or {}).get("volatilityState"),
                "qualityPolicy": quality_policy,
                **analysis_context_metadata,
                "readOnly": True,
            },
        })
        if eligibility.get("eligible") is not True:
            reason = str((eligibility.get("reasons") or ["policy_denied"])[0])
            raise RequestError(f"Agent {row['agentId']} ไม่ผ่านระบบป้องกัน: {reason}", 503)
        prepared_rows.append((row, prompt))

    rate_blockers = _ai_trade_council_rate_preflight(prompt_contract)
    if rate_blockers:
        retry_after = max(
            int(item.get("retryAfterSeconds") or 1) for item in rate_blockers
        )
        blocked_titles = ", ".join(
            str(item.get("titleTh") or item.get("agentId") or "Agent")
            for item in rate_blockers
        )
        append_audit({
            "type": "ai_trade_council.preflight_blocked",
            "snapshotId": snapshot_id,
            "reason": "local_rate_limited",
            "blockedAgents": [
                {
                    "agentId": item.get("agentId"),
                    "roleId": item.get("roleId"),
                    "retryAfterSeconds": item.get("retryAfterSeconds"),
                }
                for item in rate_blockers
            ],
            "terminalActions": False,
        })
        raise RequestError(
            (
                f"ยังเริ่มรอบวิเคราะห์ไม่ได้ เพราะคิวของ {blocked_titles} เต็ม "
                f"กรุณารอประมาณ {retry_after} วินาที แล้วเริ่ม Specialist ทั้ง 3 ตัวพร้อมกันอีกครั้ง"
            ),
            429,
        )

    allowed, retry_after = check_rate_limit(
        "ai-trade-council:analyze",
        12,
        cooldown_seconds=3,
        consume=True,
    )
    if not allowed:
        raise RequestError(f"กรุณารอ {retry_after} วินาทีก่อนเริ่มรอบวิเคราะห์ใหม่", 429)

    parent = existing_parent or create_mission({
        "title": f"สภา AI Trade วิเคราะห์ {chart.get('symbol')} {chart.get('timeframe')}",
        "prompt": (
            f"Manager ประสานผลการวิเคราะห์แบบอ่านอย่างเดียวจาก Agent 3 ตัว "
            f"โดยใช้ Snapshot {snapshot_id} เดียวกัน"
        ),
        "agentId": "manager",
        "requester": "system_scheduler" if automation_packet else "human",
        "toolId": "manager_mission",
        "targetId": prop_id,
        "risk": "low",
        "reportType": "ai_trade_council_report",
        "idempotencyKey": parent_idempotency,
        "analysisContext": {
            "kind": "ai_trade_council_parent",
            "snapshotId": snapshot_id,
            "snapshotArtifact": snapshot_artifact,
            "snapshotArtifactDigest": snapshot_artifact_digest,
            "propId": prop_id,
            "referencePrice": reference_price,
            "snapshotObservedAt": chart.get("observedAt"),
            "horizonBars": horizon_bars,
            "validUntilBarTime": valid_until_bar_time,
            "roundStartedAt": council_quality_gate["roundStartedAt"],
            "roundDeadlineAt": council_quality_gate["roundDeadlineAt"],
            "qualityGate": council_quality_gate,
            "requiredVotes": required_votes,
            **analysis_context_metadata,
            "readOnly": True,
            "contractDigest": contract_digest,
            **({"closedBarIdentity": closed_bar_packet} if closed_bar_packet else {}),
            **({"automation": automation_packet} if automation_packet else {}),
        },
    }, status="running", allow_analysis_context=True)

    subtasks = []
    try:
        for row, prompt in prepared_rows:
            child_key = (
                f"ai-council-auto-{automation_packet['streamKey'][:18]}-"
                f"{automation_packet['closedBarTime']}-{contract_digest}-v{required_votes}-{row['roleId']}"
                if automation_packet
                else (
                    f"ai-council-{snapshot_id[:24]}-{contract_digest}-"
                    f"v{required_votes}{round_retry_suffix}-{row['roleId']}"
                )
            )
            existing_child = find_mission_by_idempotency(child_key)
            child = existing_child or create_mission({
                "title": row["titleTh"],
                "prompt": prompt,
                "agentId": row["agentId"],
                "requester": "manager",
                "toolId": row["toolId"],
                "targetId": prop_id,
                "risk": "medium",
                "reportType": "ai_trade_council_vote",
                "parentMissionId": parent["id"],
                "idempotencyKey": child_key,
                "modelTier": row["modelTier"],
                "timeout": row["timeoutSeconds"],
                "budget": {
                    "timeoutSeconds": row["timeoutSeconds"],
                    "outputLimitChars": row["outputLimitChars"],
                },
                "analysisContext": {
                    "kind": "ai_trade_council_vote",
                    "snapshotId": snapshot_id,
                    "snapshotArtifact": snapshot_artifact,
                    "snapshotArtifactDigest": snapshot_artifact_digest,
                    "agentId": row["agentId"],
                    "roleId": row["roleId"],
                    "referencePrice": reference_price,
                    "horizonBars": horizon_bars,
                    "validUntilBarTime": valid_until_bar_time,
                    "volatilityState": (council_quality_gate.get("technical") or {}).get("volatilityState"),
                    "qualityPolicy": quality_policy,
                    "roundDeadlineAt": council_quality_gate["roundDeadlineAt"],
                    "snapshotObservedAt": chart.get("observedAt"),
                    "propId": prop_id,
                    **analysis_context_metadata,
                    "readOnly": True,
                    "contractDigest": contract_digest,
                    **({"closedBarIdentity": closed_bar_packet} if closed_bar_packet else {}),
                    **({"automation": automation_packet} if automation_packet else {}),
                },
            }, status="queued", allow_model_override=True, allow_budget_override=True, allow_analysis_context=True)
            if (
                child.get("parentMissionId") != parent["id"]
                or child.get("autoEligible") is not True
                or child.get("executionMode") != "auto_guarded"
            ):
                raise RequestError(f"งานของ Agent {row['agentId']} ไม่พร้อมรันอัตโนมัติ", 503)
            subtasks.append(child)
    except Exception:
        failed_at = utc_now()
        cancelled_subtasks = 0
        with PARENT_MISSION_REFRESH_LOCK:
            with MISSIONS_LOCK:
                missions = load_missions()
                stored_parent = next(
                    (
                        item
                        for item in missions
                        if item.get("id") == parent.get("id")
                    ),
                    parent,
                )
                stored_parent["status"] = "blocked"
                stored_parent["phase"] = "council_queue_incomplete"
                stored_parent["errorCode"] = "council_queue_incomplete"
                stored_parent["result"] = "สร้างงานวิเคราะห์ไม่ครบ 3 Agent ระบบจึงหยุดไว้โดยไม่ส่งคำสั่งไป Terminal"
                stored_parent["completedAt"] = failed_at
                stored_parent["updatedAt"] = failed_at
                for mission in missions:
                    mission_context = (
                        mission.get("analysisContext")
                        if isinstance(mission.get("analysisContext"), dict)
                        else {}
                    )
                    if (
                        mission.get("parentMissionId") != parent.get("id")
                        or mission_context.get("kind") != "ai_trade_council_vote"
                        or mission.get("status")
                        not in {"queued", "waiting_approval"}
                    ):
                        continue
                    mission["status"] = "blocked"
                    mission["phase"] = "council_queue_incomplete"
                    mission["errorCode"] = "council_parent_queue_incomplete"
                    mission["result"] = (
                        "Council round assembly failed before all three votes were queued. "
                        "No tool was started."
                    )
                    mission["completedAt"] = failed_at
                    mission["updatedAt"] = failed_at
                    approval = (
                        mission.get("approval")
                        if isinstance(mission.get("approval"), dict)
                        else {}
                    )
                    if approval.get("state") == "approved":
                        approval["state"] = "invalidated"
                    mission["approval"] = approval
                    execution = (
                        mission.get("execution")
                        if isinstance(mission.get("execution"), dict)
                        else {}
                    )
                    execution["dispatchState"] = "blocked"
                    execution["completedAt"] = failed_at
                    mission["execution"] = execution
                    cancelled_subtasks += 1
                save_missions(missions)
                parent = stored_parent
        append_audit({
            "type": "ai_trade_council.queue_failed",
            "missionId": parent.get("id"),
            "snapshotId": snapshot_id,
            "createdSubtaskCount": len(subtasks),
            "cancelledSubtaskCount": cancelled_subtasks,
            **analysis_context_metadata,
            "terminalActions": False,
        })
        raise

    parent["subtaskIds"] = [item["id"] for item in subtasks]
    parent["status"] = "queued" if all(item.get("status") == "queued" for item in subtasks) else "running"
    parent["phase"] = "council_specialists_queued"
    parent["result"] = "ส่ง Snapshot เดียวกันให้ Agent วิเคราะห์ครบ 3 บทบาทแล้ว"
    parent["completedAt"] = None
    parent["updatedAt"] = utc_now()
    parent["delegation"] = {
        "mode": "ai_trade_council_read_only",
        "state": "specialists_queued",
        "snapshotId": snapshot_id,
        "contractDigest": contract_digest,
        "qualityGateSchema": "ai-trade-council-quality-gate-v2",
        "horizonBars": horizon_bars,
        "validUntilBarTime": valid_until_bar_time,
        "requiredVotes": required_votes,
        "roundDeadlineAt": council_quality_gate["roundDeadlineAt"],
        **analysis_context_metadata,
        "subtaskCount": 3,
        "subtaskStatusCounts": summarize_missions(subtasks).get("byStatus", {}),
        "summaryTargetId": prop_id,
        "riskGuardAgentId": "risk_guard",
        "riskGuardVoting": False,
        "terminalActions": False,
        "realToolExecuted": False,
        "triggerMode": (
            "auto_on_new_closed_bar"
            if automation_packet
            else "manual"
        ),
        **({"closedBarIdentity": closed_bar_packet} if closed_bar_packet else {}),
        "delegatedAt": utc_now(),
    }
    replace_mission(parent)
    append_audit({
        "type": "ai_trade_council.queued",
        "missionId": parent["id"],
        "snapshotId": snapshot_id,
        "ownerAgentId": "manager",
        "subtaskIds": parent["subtaskIds"],
        "subtaskCount": 3,
        "sameSnapshotRequired": True,
        "requiredVotes": required_votes,
        **analysis_context_metadata,
        "triggerMode": (
            "auto_on_new_closed_bar"
            if automation_packet
            else "manual"
        ),
        **({"closedBarIdentity": closed_bar_packet} if closed_bar_packet else {}),
        "riskGuardVoting": False,
        "terminalActions": False,
        "budgets": [
            {
                "agentId": item.get("owner"),
                "modelTier": item.get("modelTier"),
                "timeoutSeconds": (item.get("budget") or {}).get("timeoutSeconds"),
                "outputLimitChars": (item.get("budget") or {}).get("outputLimitChars"),
            }
            for item in subtasks
        ],
    })
    MISSION_WORKER_WAKE.set()
    return {
        "ok": True,
        "kind": "ai_trade_council_queued",
        "status": parent["status"],
        "propId": prop_id,
        "snapshotId": snapshot_id,
        "requiredVotes": required_votes,
        **analysis_context_metadata,
        "readOnly": True,
        "terminalActions": False,
        "manager": mission_read_model_item(parent),
        "parent": mission_read_model_item(parent),
        "subtasks": [mission_read_model_item(item) for item in subtasks],
        "analysisReadiness": snapshot_model.get("analysisReadiness"),
        "_httpStatus": 201,
    }


def _ai_trade_council_checkpoint_metrics(
    decision: str,
    reference_price: float,
    stop_loss: float | None,
    take_profit: float | None,
    bars: list[dict],
) -> dict:
    last_close = float(bars[-1]["close"])
    if decision not in {"BUY", "SELL"}:
        return {
            "directionalReturnPercent": None,
            "mfePercent": None,
            "maePercent": None,
            "protectivePriceOutcome": "not_applicable",
        }
    direction_sign = 1.0 if decision == "BUY" else -1.0
    directional_return = (
        (last_close - reference_price) / reference_price * 100.0 * direction_sign
    )
    if decision == "BUY":
        favorable = max(float(item["high"]) - reference_price for item in bars)
        adverse = min(float(item["low"]) - reference_price for item in bars)
    else:
        favorable = max(reference_price - float(item["low"]) for item in bars)
        adverse = min(reference_price - float(item["high"]) for item in bars)

    protective_outcome = "open"
    protective_hit_bar_time = None
    if stop_loss is not None and take_profit is not None:
        for item in bars:
            low = float(item["low"])
            high = float(item["high"])
            stop_hit = low <= stop_loss if decision == "BUY" else high >= stop_loss
            target_hit = high >= take_profit if decision == "BUY" else low <= take_profit
            if stop_hit and target_hit:
                protective_outcome = "both_hit_same_bar_unknown_order"
            elif target_hit:
                protective_outcome = "take_profit_hit"
            elif stop_hit:
                protective_outcome = "stop_loss_hit"
            else:
                continue
            protective_hit_bar_time = item.get("time")
            break
    return {
        "directionalReturnPercent": round(directional_return, 8),
        "mfePercent": round(max(0.0, favorable) / reference_price * 100.0, 8),
        "maePercent": round(min(0.0, adverse) / reference_price * 100.0, 8),
        "protectivePriceOutcome": protective_outcome,
        "protectivePriceHitBarTime": protective_hit_bar_time,
    }


def evaluate_ai_trade_council_outcomes(
    snapshot_model: dict | None = None,
) -> dict:
    """Evaluate 1/3/5-bar outcomes only after each future closed bar exists."""
    missions = load_missions()
    pending = [
        mission
        for mission in missions
        if isinstance(mission.get("councilDecision"), dict)
        and isinstance(mission["councilDecision"].get("outcomeTracking"), dict)
        and mission["councilDecision"]["outcomeTracking"].get("status") == "pending"
    ]
    if not pending:
        return {"updated": 0, "pending": 0}
    if snapshot_model is None:
        snapshot_model = metatrader_snapshot_read_model(AI_TRADE_COUNCIL_PROP_ID)
    identity, _ = _ai_trade_council_closed_bar_identity(snapshot_model)
    chart = (
        snapshot_model.get("chartSnapshot")
        if isinstance(snapshot_model, dict)
        and isinstance(snapshot_model.get("chartSnapshot"), dict)
        else {}
    )
    source_bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    if identity is None or not source_bars:
        return {"updated": 0, "pending": len(pending)}
    bars = [
        row
        for row in source_bars
        if isinstance(row, dict)
        and isinstance(row.get("time"), int)
        and not isinstance(row.get("time"), bool)
        and all(
            isinstance(row.get(field), (int, float))
            and not isinstance(row.get(field), bool)
            and math.isfinite(float(row.get(field)))
            for field in ("open", "high", "low", "close")
        )
    ]
    bars.sort(key=lambda item: int(item["time"]))
    updated_parents: list[dict] = []
    for parent in pending:
        consensus = parent["councilDecision"]
        provenance = (
            consensus.get("decisionProvenance")
            if isinstance(consensus.get("decisionProvenance"), dict)
            else {}
        )
        decision_identity = (
            provenance.get("closedBarIdentity")
            if isinstance(provenance.get("closedBarIdentity"), dict)
            else {}
        )
        if (
            decision_identity.get("streamKey") != identity.get("streamKey")
            or decision_identity.get("symbol") != identity.get("symbol")
            or decision_identity.get("timeframe") != identity.get("timeframe")
        ):
            continue
        decision_bar_time = decision_identity.get("closedBarTime")
        if not isinstance(decision_bar_time, int) or isinstance(decision_bar_time, bool):
            continue
        future_bars = [row for row in bars if int(row["time"]) > decision_bar_time]
        tracking = consensus["outcomeTracking"]
        existing = {
            int(item.get("barsAfterDecision")): item
            for item in (tracking.get("evaluations") or [])
            if isinstance(item, dict)
            and isinstance(item.get("barsAfterDecision"), int)
        }
        checkpoints = [1, 3, 5]
        added = False
        trade_plan = (
            consensus.get("tradePlan")
            if isinstance(consensus.get("tradePlan"), dict)
            else {}
        )
        reference_price = _safe_snapshot_number(
            (parent.get("analysisContext") or {}).get("referencePrice"),
            minimum=0.00000001,
            maximum=1_000_000_000,
        )
        if reference_price is None:
            continue
        stop_loss = _safe_snapshot_number(
            trade_plan.get("stopLossPrice"),
            minimum=0.00000001,
            maximum=1_000_000_000,
        )
        take_profit = _safe_snapshot_number(
            trade_plan.get("takeProfitPrice"),
            minimum=0.00000001,
            maximum=1_000_000_000,
        )
        for checkpoint in checkpoints:
            if checkpoint in existing or len(future_bars) < checkpoint:
                continue
            observed = future_bars[:checkpoint]
            existing[checkpoint] = {
                "barsAfterDecision": checkpoint,
                "evaluatedThroughBarTime": observed[-1]["time"],
                "evaluatedAt": utc_now(),
                **_ai_trade_council_checkpoint_metrics(
                    str(consensus.get("decision") or "NO_TRADE"),
                    reference_price,
                    stop_loss,
                    take_profit,
                    observed,
                ),
            }
            added = True
        if not added:
            continue
        tracking["evaluations"] = [existing[key] for key in sorted(existing)]
        tracking["status"] = (
            "evaluated"
            if all(checkpoint in existing for checkpoint in checkpoints)
            else "pending"
        )
        tracking["lastEvaluatedAt"] = utc_now()
        tracking["latestSnapshotId"] = identity.get("snapshotId")
        consensus["outcomeTracking"] = tracking
        parent["councilDecision"] = consensus
        parent["updatedAt"] = utc_now()
        updated_parents.append(parent)

    if not updated_parents:
        return {"updated": 0, "pending": len(pending)}
    updated_by_id = {str(item.get("id") or ""): item for item in updated_parents}
    with MISSIONS_LOCK:
        latest = load_missions()
        for index, mission in enumerate(latest):
            replacement = updated_by_id.get(str(mission.get("id") or ""))
            if replacement:
                latest[index] = {
                    **mission,
                    "councilDecision": replacement["councilDecision"],
                    "updatedAt": replacement["updatedAt"],
                }
        save_missions(latest)
    for parent in updated_parents:
        tracking = parent["councilDecision"]["outcomeTracking"]
        for report_id in parent.get("reportIds") or []:
            safe_report_id = safe_reference(report_id)
            if not safe_report_id:
                continue
            report_path = RUNTIME_REPORTS_DIR / f"{safe_report_id}.json"
            report = read_json(report_path, None) if report_path.is_file() else None
            if not isinstance(report, dict):
                continue
            metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
            report["metrics"] = {
                **metrics,
                "outcomeTracking": sanitize_json_value(tracking),
            }
            report["updatedAt"] = utc_now()
            with REPORTS_LOCK:
                write_json(report_path, report)
        append_audit({
            "type": "ai_trade_council.outcome_evaluated",
            "missionId": parent.get("id"),
            "snapshotId": parent["councilDecision"].get("snapshotId"),
            "status": tracking.get("status"),
            "evaluatedBars": [
                item.get("barsAfterDecision")
                for item in tracking.get("evaluations") or []
            ],
            "futureDataGuard": "closed_bars_only",
        })
    return {
        "updated": len(updated_parents),
        "pending": sum(
            1
            for item in updated_parents
            if item["councilDecision"]["outcomeTracking"].get("status") == "pending"
        ),
    }


def ai_trade_council_automation_tick() -> dict:
    """Queue at most one read-only Council round for a newly closed candle."""
    if not AI_TRADE_COUNCIL_AUTOMATION_RUN_LOCK.acquire(blocking=False):
        return {
            "ok": False,
            "kind": "ai_trade_council_automation_busy",
            "automation": ai_trade_council_automation_read_model(),
        }
    try:
        try:
            evaluate_ai_trade_council_outcomes()
        except (DataIntegrityError, OSError, ValueError):
            append_audit({
                "type": "ai_trade_council.outcome_evaluation_skipped",
                "reason": "snapshot_or_runtime_unavailable",
            })
        store = load_ai_trade_council_automation_store()
        store, rolled = _rollover_ai_trade_council_automation_day(store)
        if rolled:
            store = _save_ai_trade_council_automation_store(store)
        config = store["config"]
        state = store["state"]
        if not config.get("enabled"):
            _update_ai_trade_council_automation_state(
                status="disabled",
                reason="automation_disabled",
                pendingClosedBarTime=None,
                pendingSnapshotId=None,
                pendingDetectedAt=None,
            )
            return {
                "ok": True,
                "kind": "ai_trade_council_automation_disabled",
                "automation": ai_trade_council_automation_read_model(),
            }

        snapshot = metatrader_snapshot_read_model(AI_TRADE_COUNCIL_PROP_ID)
        identity, identity_reason = _ai_trade_council_closed_bar_identity(snapshot)
        if identity is None:
            _, changed = _update_ai_trade_council_automation_state(
                status="waiting_snapshot",
                reason=identity_reason,
            )
            if changed:
                append_audit({
                    "type": "ai_trade_council.automation_paused",
                    "reason": identity_reason,
                    "terminalActions": False,
                })
            return {
                "ok": False,
                "kind": "ai_trade_council_automation_waiting_snapshot",
                "reason": identity_reason,
                "automation": ai_trade_council_automation_read_model(),
            }

        current_fields = {
            "startupId": SERVER_STARTED_AT,
            "candidateId": identity["candidateId"],
            "streamKey": identity["streamKey"],
            "symbol": identity["symbol"],
            "timeframe": identity["timeframe"],
        }
        closed_bar_time = int(identity["lastClosedBarTime"])
        previous_bar_time = state.get("lastObservedClosedBarTime")
        baseline_reason = None
        if state.get("startupId") != SERVER_STARTED_AT:
            baseline_reason = "restart_baseline"
        elif state.get("streamKey") != identity["streamKey"]:
            baseline_reason = "stream_change_baseline"
        elif previous_bar_time is None:
            baseline_reason = "first_observation_baseline"
        elif closed_bar_time < int(previous_bar_time):
            baseline_reason = "bar_time_regression_baseline"

        if baseline_reason:
            _update_ai_trade_council_automation_state(
                **current_fields,
                status="baseline",
                reason=baseline_reason,
                lastObservedClosedBarTime=closed_bar_time,
                pendingClosedBarTime=None,
                pendingSnapshotId=None,
                pendingDetectedAt=None,
            )
            append_audit({
                "type": "ai_trade_council.automation_baseline",
                "reason": baseline_reason,
                "streamKey": identity["streamKey"],
                "candidateId": identity["candidateId"],
                "symbol": identity["symbol"],
                "timeframe": identity["timeframe"],
                "closedBarTime": closed_bar_time,
                "snapshotId": identity["snapshotId"],
                "catchUp": False,
                "terminalActions": False,
            })
            return {
                "ok": True,
                "kind": "ai_trade_council_automation_baseline",
                "reason": baseline_reason,
                "automation": ai_trade_council_automation_read_model(),
            }

        if identity["timeframe"] not in AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES:
            _, changed = _update_ai_trade_council_automation_state(
                **current_fields,
                status="unsupported_timeframe",
                reason="timeframe_not_supported",
                lastObservedClosedBarTime=closed_bar_time,
                pendingClosedBarTime=None,
                pendingSnapshotId=None,
                pendingDetectedAt=None,
            )
            if changed:
                append_audit({
                    "type": "ai_trade_council.automation_paused",
                    "reason": "timeframe_not_supported",
                    "symbol": identity["symbol"],
                    "timeframe": identity["timeframe"],
                    "closedBarTime": closed_bar_time,
                    "terminalActions": False,
                })
            return {
                "ok": False,
                "kind": "ai_trade_council_automation_unsupported_timeframe",
                "automation": ai_trade_council_automation_read_model(),
            }

        if closed_bar_time > int(previous_bar_time):
            detected_at = utc_now()
            _update_ai_trade_council_automation_state(
                **current_fields,
                status="settling",
                reason="new_closed_bar_detected",
                lastObservedClosedBarTime=closed_bar_time,
                pendingClosedBarTime=closed_bar_time,
                pendingSnapshotId=identity["snapshotId"],
                pendingDetectedAt=detected_at,
            )
            append_audit({
                "type": "ai_trade_council.closed_bar_detected",
                "streamKey": identity["streamKey"],
                "candidateId": identity["candidateId"],
                "symbol": identity["symbol"],
                "timeframe": identity["timeframe"],
                "closedBarTime": closed_bar_time,
                "snapshotId": identity["snapshotId"],
                "settleSeconds": AI_TRADE_COUNCIL_AUTOMATION_SETTLE_SECONDS,
                "terminalActions": False,
            })
            return {
                "ok": True,
                "kind": "ai_trade_council_automation_settling",
                "automation": ai_trade_council_automation_read_model(),
            }

        pending_bar_time = state.get("pendingClosedBarTime")
        if pending_bar_time != closed_bar_time:
            _update_ai_trade_council_automation_state(
                **current_fields,
                status="idle",
                reason="waiting_for_new_closed_bar",
            )
            return {
                "ok": True,
                "kind": "ai_trade_council_automation_idle",
                "automation": ai_trade_council_automation_read_model(),
            }

        detected_at = parse_iso(state.get("pendingDetectedAt"))
        if detected_at is None:
            _update_ai_trade_council_automation_state(
                **current_fields,
                status="settling",
                reason="settle_timer_restarted",
                pendingSnapshotId=identity["snapshotId"],
                pendingDetectedAt=utc_now(),
            )
            return {
                "ok": True,
                "kind": "ai_trade_council_automation_settling",
                "automation": ai_trade_council_automation_read_model(),
            }
        elapsed = max(
            0.0,
            (
                datetime.now(timezone.utc)
                - detected_at.astimezone(timezone.utc)
            ).total_seconds(),
        )
        if elapsed < AI_TRADE_COUNCIL_AUTOMATION_SETTLE_SECONDS:
            _update_ai_trade_council_automation_state(
                **current_fields,
                status="settling",
                reason="waiting_for_snapshot_settle",
                pendingSnapshotId=identity["snapshotId"],
            )
            return {
                "ok": True,
                "kind": "ai_trade_council_automation_settling",
                "settleRemainingSeconds": round(
                    AI_TRADE_COUNCIL_AUTOMATION_SETTLE_SECONDS - elapsed,
                    1,
                ),
                "automation": ai_trade_council_automation_read_model(),
            }

        store = load_ai_trade_council_automation_store()
        config = store["config"]
        state = store["state"]
        if not config.get("enabled"):
            _update_ai_trade_council_automation_state(
                status="disabled",
                reason="automation_disabled",
                pendingClosedBarTime=None,
                pendingSnapshotId=None,
                pendingDetectedAt=None,
            )
            return {
                "ok": True,
                "kind": "ai_trade_council_automation_disabled",
                "automation": ai_trade_council_automation_read_model(),
            }
        if state.get("dailyRunCount", 0) >= config.get("maxDailyRounds", 24):
            _, changed = _update_ai_trade_council_automation_state(
                status="daily_cap_reached",
                reason="daily_cap_reached",
                pendingClosedBarTime=None,
                pendingSnapshotId=None,
                pendingDetectedAt=None,
            )
            if changed:
                append_audit({
                    "type": "ai_trade_council.automation_skipped",
                    "reason": "daily_cap_reached",
                    "closedBarTime": closed_bar_time,
                    "maxDailyRounds": config.get("maxDailyRounds"),
                    "terminalActions": False,
                })
            return {
                "ok": False,
                "kind": "ai_trade_council_automation_daily_cap",
                "automation": ai_trade_council_automation_read_model(),
            }

        active_parent = _active_ai_trade_council_parent()
        gate_reason = None
        if active_parent:
            gate_reason = "council_round_already_active"
        elif load_operator_mode_record().get("mode") != "auto_guarded":
            gate_reason = "full_access_required"
        else:
            bridge = bridge_status()
            codex_status = str((bridge.get("codex") or {}).get("status") or "")
            if codex_status not in {"ready", "ready_guarded"}:
                gate_reason = "codex_runner_not_ready"
        quota_gate = None
        if gate_reason is None:
            quota_gate = _collaboration_quota_gate(config, refresh=True)
            if quota_gate.get("allowed") is not True:
                gate_reason = str(quota_gate.get("reason") or "quota_blocked")
        if gate_reason is not None:
            _, changed = _update_ai_trade_council_automation_state(
                **current_fields,
                status="waiting_gate",
                reason=gate_reason,
                pendingSnapshotId=identity["snapshotId"],
            )
            if changed:
                append_audit({
                    "type": "ai_trade_council.automation_paused",
                    "reason": gate_reason,
                    "activeMissionId": (
                        active_parent.get("id")
                        if isinstance(active_parent, dict)
                        else None
                    ),
                    "remainingPercent": (
                        quota_gate.get("remainingPercent")
                        if isinstance(quota_gate, dict)
                        else None
                    ),
                    "closedBarTime": closed_bar_time,
                    "terminalActions": False,
                })
            return {
                "ok": False,
                "kind": "ai_trade_council_automation_waiting_gate",
                "reason": gate_reason,
                "automation": ai_trade_council_automation_read_model(),
            }

        response = run_ai_trade_council_analysis(
            {
                "propId": AI_TRADE_COUNCIL_PROP_ID,
                "snapshotId": identity["snapshotId"],
                "analysisBarCount": config.get(
                    "analysisBarCount",
                    AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT,
                ),
            },
            automation_context={
                "triggerMode": "last_closed_candle_time_change",
                "streamKey": identity["streamKey"],
                "symbol": identity["symbol"],
                "timeframe": identity["timeframe"],
                "closedBarTime": closed_bar_time,
                "analysisBarCount": config.get(
                    "analysisBarCount",
                    AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT,
                ),
                "dayKey": _automation_day_key(),
            },
        )
        parent = (
            response.get("parent")
            if isinstance(response.get("parent"), dict)
            else response.get("manager")
        )
        mission_id = safe_reference(
            parent.get("id") if isinstance(parent, dict) else None
        )
        queued_new = response.get("kind") == "ai_trade_council_queued"
        latest_store = load_ai_trade_council_automation_store()
        latest_count = int(latest_store["state"].get("dailyRunCount") or 0)
        _update_ai_trade_council_automation_state(
            **current_fields,
            status="queued" if queued_new else "existing",
            reason=(
                "closed_bar_round_queued"
                if queued_new
                else "closed_bar_round_already_recorded"
            ),
            lastObservedClosedBarTime=closed_bar_time,
            lastAnalyzedClosedBarTime=closed_bar_time,
            lastAnalyzedSnapshotId=identity["snapshotId"],
            lastMissionId=mission_id,
            dailyRunCount=latest_count + (1 if queued_new else 0),
            pendingClosedBarTime=None,
            pendingSnapshotId=None,
            pendingDetectedAt=None,
        )
        append_audit({
            "type": "ai_trade_council.automation_queued",
            "missionId": mission_id,
            "streamKey": identity["streamKey"],
            "candidateId": identity["candidateId"],
            "symbol": identity["symbol"],
            "timeframe": identity["timeframe"],
            "closedBarTime": closed_bar_time,
            "snapshotId": identity["snapshotId"],
            "newMission": queued_new,
            "sourceBarCount": response.get("sourceBarCount"),
            "requestedAnalysisBarCount": response.get(
                "requestedAnalysisBarCount"
            ),
            "usedAnalysisBarCount": response.get("usedAnalysisBarCount"),
            "analysisWindow": response.get("analysisWindow"),
            "indicatorFormulaVersion": response.get(
                "indicatorFormulaVersion"
            ),
            "terminalActions": False,
        })
        return {
            **response,
            "automation": ai_trade_council_automation_read_model(),
        }
    except RequestError as error:
        reason = f"request_error_{error.status}"
        _, changed = _update_ai_trade_council_automation_state(
            status="waiting_gate",
            reason=reason,
        )
        if changed:
            append_audit({
                "type": "ai_trade_council.automation_paused",
                "reason": reason,
                "httpStatus": error.status,
                "terminalActions": False,
            })
        return {
            "ok": False,
            "kind": "ai_trade_council_automation_waiting_gate",
            "reason": reason,
            "automation": ai_trade_council_automation_read_model(),
        }
    finally:
        AI_TRADE_COUNCIL_AUTOMATION_RUN_LOCK.release()


def ai_trade_council_automation_scheduler_loop() -> None:
    while not AI_TRADE_COUNCIL_AUTOMATION_STOP.is_set():
        try:
            ai_trade_council_automation_tick()
        except DataIntegrityError:
            append_audit({
                "type": "ai_trade_council.automation_failed",
                "reason": "data_integrity_error",
                "terminalActions": False,
            })
        except Exception as error:
            append_audit({
                "type": "ai_trade_council.automation_failed",
                "reason": "scheduler_loop_error",
                "errorType": type(error).__name__,
                "errorMessage": redact_text(str(error), 240),
                "terminalActions": False,
            })
        AI_TRADE_COUNCIL_AUTOMATION_WAKE.wait(
            AI_TRADE_COUNCIL_AUTOMATION_POLL_SECONDS
        )
        AI_TRADE_COUNCIL_AUTOMATION_WAKE.clear()


def start_ai_trade_council_automation_scheduler() -> threading.Thread:
    global AI_TRADE_COUNCIL_AUTOMATION_THREAD
    with AI_TRADE_COUNCIL_AUTOMATION_LOCK:
        if (
            AI_TRADE_COUNCIL_AUTOMATION_THREAD
            and AI_TRADE_COUNCIL_AUTOMATION_THREAD.is_alive()
        ):
            return AI_TRADE_COUNCIL_AUTOMATION_THREAD
        AI_TRADE_COUNCIL_AUTOMATION_STOP.clear()
        AI_TRADE_COUNCIL_AUTOMATION_THREAD = threading.Thread(
            target=ai_trade_council_automation_scheduler_loop,
            name="metafx-ai-trade-council-automation",
            daemon=True,
        )
        AI_TRADE_COUNCIL_AUTOMATION_THREAD.start()
        return AI_TRADE_COUNCIL_AUTOMATION_THREAD


def stop_ai_trade_council_automation_scheduler() -> None:
    AI_TRADE_COUNCIL_AUTOMATION_STOP.set()
    AI_TRADE_COUNCIL_AUTOMATION_WAKE.set()
    thread = AI_TRADE_COUNCIL_AUTOMATION_THREAD
    if thread and thread.is_alive():
        thread.join(timeout=15)


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
    with COLLABORATION_STATE_LOCK:
        collaboration_runtime = dict(COLLABORATION_STATE)
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
        "collaboration": {
            "schedulerStatus": redact_text(str(collaboration_runtime.get("status") or "stopped"), 40),
            "toolsEnabledDuringMeeting": False,
            "scheduleStoreReady": COLLABORATION_SCHEDULE_PATH.is_file(),
        },
        "time": utc_now(),
    }


def pick_target_for_task(text: str) -> str:
    lower = text.lower()
    if any(keyword_matches(lower, token) for token in ["risk", "approval", "secret", "token", "password", "enable live trading", "start live trading", "activate live trading", "live order", "delete", "deploy production", "send telegram"]):
        return MISSION_STRATEGY_TABLE_PROP_ID
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
    if any(keyword_matches(lower, token) for token in ["auto trade status", "auto trading status", "live trading status", "ea status", "terminal status", "mt4 status", "mt5 status", "terminal connection", "adapter status", "ea running", "สถานะ auto trade", "สถานะออโต้เทรด", "สถานะ live trading", "สถานะ ea", "สถานะ terminal", "สถานะ mt4", "สถานะ mt5", "ความพร้อม adapter"]):
        return AI_TRADE_COUNCIL_PROP_ID
    if any(keyword_matches(lower, token) for token in ["ai trade council", "trade council", "multi-agent trading", "agent vote", "consensus", "auto trade", "auto trading", "autotrade", "ai trader", "order", "position", "signal", "chart analysis", "news analysis", "สภา ai trade", "เอเจนต์โหวต", "วิเคราะห์ร่วม", "ออโต้เทรด", "เทรดอัตโนมัติ", "ออเดอร์", "โพซิชั่น", "ซิกแนล"]):
        return "left_analytics_console"
    if any(keyword_matches(lower, token) for token in ["ea", "mt4", "mt5", "compile", "indicator"]):
        return "terminal_workstation"
    if any(keyword_matches(lower, token) for token in ["vps", "latency", "uptime", "cpu", "ram", "server"]):
        return "right_status_crystals"
    if any(keyword_matches(lower, token) for token in ["telegram", "alert", "summary"]):
        # right_tool_console is now the EA experiment lab.  Telegram work stays
        # visible in the central mission queue unless a dedicated prop exists.
        return MISSION_STRATEGY_TABLE_PROP_ID
    if any(keyword_matches(lower, token) for token in ["risk", "approval", "secret", "compliance"]):
        return MISSION_STRATEGY_TABLE_PROP_ID
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


def recover_interrupted_collaboration_missions() -> int:
    """Close collaboration missions left non-terminal by a previous Bridge process."""
    recovered: list[dict] = []
    with MISSIONS_LOCK:
        missions = load_missions()
        recovered_at = utc_now()
        for mission in missions:
            if (
                mission.get("toolId") != "agent_collaboration"
                or mission.get("status") not in {"queued", "running"}
            ):
                continue
            previous_status = str(mission.get("status"))
            reason = (
                "bridge_restart_interrupted"
                if previous_status == "running"
                else "bridge_restart_before_start"
            )
            summary = (
                "Bridge รอบก่อนหน้าปิดระหว่างการประชุม Agent ระบบไม่ลองใช้ Codex ซ้ำอัตโนมัติ"
                if previous_status == "running"
                else "Bridge รอบก่อนหน้าปิดก่อนเริ่มการประชุม Agent ระบบปิด Mission เดิมและไม่เริ่มซ้ำอัตโนมัติ"
            )
            report = create_report({
                "type": "collaboration_report",
                "title": "กู้สถานะการประชุม Agent หลัง Bridge เริ่มใหม่",
                "summary": summary,
                "ownerAgentId": "manager",
                "linkedMissionId": mission.get("id"),
                "linkedPropId": MISSION_STRATEGY_TABLE_PROP_ID,
                "status": "blocked",
                "findings": [],
                "metrics": {"turnCount": 0, "toolsExecuted": False, "automaticRetry": False},
                "risks": [reason],
                "nextActions": ["ตรวจ Rate Limit และเริ่มการประชุมใหม่เมื่อพร้อม"],
            })
            mission["status"] = "failed"
            mission["phase"] = "agent_collaboration_recovered_after_restart"
            mission["workStatus"] = "failed"
            mission["errorCode"] = reason
            mission["result"] = summary
            mission["reportIds"] = [report["id"]]
            mission["updatedAt"] = recovered_at
            mission["completedAt"] = recovered_at
            recovered.append(mission)
        if recovered:
            save_missions(missions)
    for mission in recovered:
        append_audit({
            "type": "collaboration.interrupted_recovered",
            "missionId": mission.get("id"),
            "previousStatus": "running" if mission.get("errorCode") == "bridge_restart_interrupted" else "queued",
            "status": mission.get("status"),
            "reason": mission.get("errorCode"),
            "automaticRetry": False,
            "toolsExecuted": False,
        })
    if recovered:
        try:
            latest = recovered[-1]
            _update_collaboration_store_state(
                lastCompletedAt=latest.get("completedAt"),
                lastStatus="failed",
                lastReason=latest.get("errorCode"),
                lastMissionId=latest.get("id"),
            )
        except (DataIntegrityError, OSError):
            pass
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


def _ai_trade_council_protective_fallback_result(
    *,
    snapshot_id: str,
    reason_code: str,
    minimum_reward_risk_ratio: float,
    available: bool = False,
    stop_loss_price: float | None = None,
    take_profit_price: float | None = None,
    reward_risk_ratio: float | None = None,
    provenance: dict | None = None,
) -> dict:
    source = "backend_deterministic_fallback" if available else "unavailable"
    owner_role = "backend_deterministic_guard" if available else None
    detail = {
        "schemaVersion": "ai-trade-council-protective-plan-v1",
        "source": source,
        "reasonCode": reason_code,
        "policyVersion": AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION,
        "snapshotId": snapshot_id or None,
        "closedBarsOnly": True,
        "formulaVersion": AI_TRADE_COUNCIL_INDICATOR_FORMULA_VERSION,
        "minimumRewardRiskRatio": minimum_reward_risk_ratio,
        **(provenance if isinstance(provenance, dict) else {}),
    }
    return {
        "available": available,
        "stopLossPrice": stop_loss_price,
        "takeProfitPrice": take_profit_price,
        "rewardRiskRatio": reward_risk_ratio,
        "priceAggregation": (
            "backend_deterministic_atr_market_structure"
            if available
            else "unavailable"
        ),
        "protectivePriceOwnerRole": owner_role,
        "protectivePlanSource": source,
        "protectivePlanReasonCode": reason_code,
        "protectivePlanPolicyVersion": (
            AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION
        ),
        "protectivePlanFallbackUsed": available,
        "protectivePlanProvenance": detail,
    }


def _ai_trade_council_deterministic_protective_plan(
    *,
    context: dict,
    direction: str,
    minimum_reward_risk_ratio: float,
) -> dict:
    """Build fail-closed SL/TP from the exact stored closed-bar Snapshot.

    This is a backend calculation only. It performs no model call and no
    terminal action. The dispatcher still owns every broker, EA, deadline,
    signature, idempotency, and audit guard after consensus.
    """
    snapshot_id = str(context.get("snapshotId") or "")

    def unavailable(reason_code: str, **detail: object) -> dict:
        return _ai_trade_council_protective_fallback_result(
            snapshot_id=snapshot_id,
            reason_code=reason_code,
            minimum_reward_risk_ratio=minimum_reward_risk_ratio,
            provenance=detail,
        )

    if direction not in {"BUY", "SELL"} or not re.fullmatch(
        r"[0-9a-f]{64}", snapshot_id
    ):
        return unavailable("fallback_plan_invalid")
    expected_artifact_digest = str(
        context.get("snapshotArtifactDigest") or ""
    ).lower()
    snapshot_artifact = str(context.get("snapshotArtifact") or "").replace(
        "\\", "/"
    )
    if not re.fullmatch(r"[0-9a-f]{64}", expected_artifact_digest):
        return unavailable("fallback_snapshot_digest_missing")
    expected_artifact_name = f"{expected_artifact_digest}.json"
    expected_artifact_relative = (
        f"ai-trade-council/snapshots/{expected_artifact_name}"
    )
    if snapshot_artifact != expected_artifact_relative:
        return unavailable("fallback_snapshot_digest_mismatch")
    artifact_path = AI_TRADE_COUNCIL_SNAPSHOT_DIR / expected_artifact_name
    try:
        if not artifact_path.is_file():
            return unavailable("fallback_snapshot_missing")
        if artifact_path.stat().st_size > METATRADER_SNAPSHOT_MAX_BYTES * 8:
            return unavailable("fallback_snapshot_mismatch")
        artifact = read_json(artifact_path, None)
    except (DataIntegrityError, OSError):
        return unavailable("fallback_snapshot_mismatch")
    if not isinstance(artifact, dict):
        return unavailable("fallback_snapshot_mismatch")
    if set(artifact) != {
        "schemaVersion",
        "snapshotId",
        "createdAt",
        "sourceMode",
        "dailySummary",
        "chartSnapshot",
        "policy",
        "artifactDigest",
    }:
        return unavailable("fallback_snapshot_digest_mismatch")
    try:
        observed_artifact_digest = (
            _ai_trade_council_snapshot_artifact_digest(artifact)
        )
    except (TypeError, ValueError):
        return unavailable("fallback_snapshot_digest_mismatch")
    if (
        artifact.get("artifactDigest") != expected_artifact_digest
        or observed_artifact_digest != expected_artifact_digest
    ):
        return unavailable(
            "fallback_snapshot_digest_mismatch",
            expectedArtifactDigest=expected_artifact_digest,
            observedArtifactDigest=observed_artifact_digest,
        )
    chart = (
        artifact.get("chartSnapshot")
        if isinstance(artifact.get("chartSnapshot"), dict)
        else {}
    )
    artifact_policy = (
        artifact.get("policy")
        if isinstance(artifact.get("policy"), dict)
        else {}
    )
    if (
        artifact.get("schemaVersion") != "ai-trade-council-input-v1"
        or artifact.get("snapshotId") != snapshot_id
        or chart.get("snapshotId") != snapshot_id
        or artifact.get("sourceMode") != "mt4_read_only_snapshot"
        or artifact_policy.get("readOnly") is not True
        or artifact_policy.get("sameSnapshotRequired") is not True
        or artifact_policy.get("terminalActionsAllowed") is not False
    ):
        return unavailable("fallback_snapshot_mismatch")
    bars = chart.get("bars") if isinstance(chart.get("bars"), list) else []
    expected_bar_count = context.get("usedAnalysisBarCount")
    if (
        isinstance(expected_bar_count, int)
        and not isinstance(expected_bar_count, bool)
        and expected_bar_count > 0
        and len(bars) != expected_bar_count
    ):
        return unavailable(
            "fallback_snapshot_mismatch",
            observedBarCount=len(bars),
            expectedBarCount=expected_bar_count,
        )
    bar_times = [
        item.get("time") if isinstance(item, dict) else None
        for item in bars
    ]
    if (
        len(bars) < 20
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
            for value in bar_times
        )
        or any(
            int(bar_times[index]) <= int(bar_times[index - 1])
            for index in range(1, len(bar_times))
        )
    ):
        return unavailable("fallback_inputs_unavailable")
    closed_bar_identity = (
        context.get("closedBarIdentity")
        if isinstance(context.get("closedBarIdentity"), dict)
        else {}
    )
    if closed_bar_identity:
        expected_symbol = _safe_snapshot_symbol(closed_bar_identity.get("symbol"))
        expected_timeframe = _safe_snapshot_timeframe(
            closed_bar_identity.get("timeframe")
        )
        expected_closed_bar_time = closed_bar_identity.get("closedBarTime")
        if (
            (expected_symbol and _safe_snapshot_symbol(chart.get("symbol")) != expected_symbol)
            or (
                expected_timeframe
                and _safe_snapshot_timeframe(chart.get("timeframe"))
                != expected_timeframe
            )
            or (
                isinstance(expected_closed_bar_time, int)
                and not isinstance(expected_closed_bar_time, bool)
                and int(bar_times[-1]) != expected_closed_bar_time
            )
        ):
            return unavailable("fallback_closed_bar_mismatch")

    reference_price = _safe_snapshot_number(
        context.get("referencePrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    bid = _safe_snapshot_number(
        chart.get("bid"), minimum=0.00000001, maximum=1_000_000_000
    )
    ask = _safe_snapshot_number(
        chart.get("ask"), minimum=0.00000001, maximum=1_000_000_000
    )
    artifact_reference = (
        (bid + ask) / 2.0
        if bid is not None and ask is not None
        else _safe_snapshot_number(
            chart.get("price"),
            minimum=0.00000001,
            maximum=1_000_000_000,
        )
    )
    if (
        reference_price is None
        or artifact_reference is None
        or abs(reference_price - artifact_reference)
        > max(0.00000001, artifact_reference * 0.00000001)
    ):
        return unavailable("fallback_snapshot_mismatch")

    feature_bundle = _ai_trade_council_analysis_feature_bundle(bars)
    technical = feature_bundle["technicalIndicators"]
    price_action = feature_bundle["priceActionFeatures"]
    atr14 = _safe_snapshot_number(
        technical.get("atr14"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    if (
        technical.get("available") is not True
        or price_action.get("available") is not True
        or atr14 is None
    ):
        return unavailable("fallback_inputs_unavailable")

    support_resistance = (
        price_action.get("supportResistance")
        if isinstance(price_action.get("supportResistance"), dict)
        else {}
    )
    swings = (
        price_action.get("swings")
        if isinstance(price_action.get("swings"), dict)
        else {}
    )
    anchor_candidates: list[tuple[float, str]] = []
    target_candidates: list[tuple[float, str]] = []

    def collect(
        rows: object,
        *,
        field: str,
        label: str,
        destination: list[tuple[float, str]],
    ) -> None:
        if not isinstance(rows, list):
            return
        for row in rows:
            value = _safe_snapshot_number(
                row.get(field) if isinstance(row, dict) else None,
                minimum=0.00000001,
                maximum=1_000_000_000,
            )
            if value is not None:
                destination.append((value, label))

    if direction == "BUY":
        collect(
            support_resistance.get("supports"),
            field="price",
            label="confirmed_support",
            destination=anchor_candidates,
        )
        collect(
            swings.get("lows"),
            field="price",
            label="confirmed_swing_low",
            destination=anchor_candidates,
        )
        collect(
            support_resistance.get("resistances"),
            field="price",
            label="confirmed_resistance",
            destination=target_candidates,
        )
        collect(
            swings.get("highs"),
            field="price",
            label="confirmed_swing_high",
            destination=target_candidates,
        )
        for row in bars[-20:]:
            anchor_candidates.append((float(row["low"]), "recent_closed_bar_low"))
            target_candidates.append((float(row["high"]), "recent_closed_bar_high"))
    else:
        collect(
            support_resistance.get("resistances"),
            field="price",
            label="confirmed_resistance",
            destination=anchor_candidates,
        )
        collect(
            swings.get("highs"),
            field="price",
            label="confirmed_swing_high",
            destination=anchor_candidates,
        )
        collect(
            support_resistance.get("supports"),
            field="price",
            label="confirmed_support",
            destination=target_candidates,
        )
        collect(
            swings.get("lows"),
            field="price",
            label="confirmed_swing_low",
            destination=target_candidates,
        )
        for row in bars[-20:]:
            anchor_candidates.append((float(row["high"]), "recent_closed_bar_high"))
            target_candidates.append((float(row["low"]), "recent_closed_bar_low"))

    maximum_anchor_distance = (
        atr14 * AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MAX_STRUCTURE_DISTANCE_ATR
    )
    directional_anchors = [
        (price, label)
        for price, label in anchor_candidates
        if (
            (price < reference_price if direction == "BUY" else price > reference_price)
            and abs(price - reference_price) <= maximum_anchor_distance
        )
    ]
    anchor_price, anchor_type = (
        min(
            directional_anchors,
            key=lambda item: (abs(item[0] - reference_price), item[1], item[0]),
        )
        if directional_anchors
        else (None, "atr_only")
    )
    minimum_stop_distance = (
        atr14 * AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MINIMUM_STOP_ATR
    )
    structure_buffer = (
        atr14 * AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_STRUCTURE_BUFFER_ATR
    )
    if direction == "BUY":
        atr_stop = reference_price - minimum_stop_distance
        stop_loss = min(
            atr_stop,
            (anchor_price - structure_buffer)
            if anchor_price is not None
            else atr_stop,
        )
        risk_distance = reference_price - stop_loss
        minimum_target = (
            reference_price + risk_distance * minimum_reward_risk_ratio
        )
        eligible_targets = [
            (price, label)
            for price, label in target_candidates
            if minimum_target <= price <= reference_price + risk_distance * max(
                4.0, minimum_reward_risk_ratio
            )
        ]
        take_profit, target_basis = (
            min(eligible_targets, key=lambda item: (item[0], item[1]))
            if eligible_targets
            else (minimum_target, "minimum_reward_risk_ratio")
        )
    else:
        atr_stop = reference_price + minimum_stop_distance
        stop_loss = max(
            atr_stop,
            (anchor_price + structure_buffer)
            if anchor_price is not None
            else atr_stop,
        )
        risk_distance = stop_loss - reference_price
        minimum_target = (
            reference_price - risk_distance * minimum_reward_risk_ratio
        )
        eligible_targets = [
            (price, label)
            for price, label in target_candidates
            if reference_price - risk_distance * max(
                4.0, minimum_reward_risk_ratio
            ) <= price <= minimum_target
        ]
        take_profit, target_basis = (
            max(eligible_targets, key=lambda item: (item[0], item[1]))
            if eligible_targets
            else (minimum_target, "minimum_reward_risk_ratio")
        )

    stop_loss = round(float(stop_loss), 8)
    take_profit = round(float(take_profit), 8)
    risk_distance = (
        reference_price - stop_loss
        if direction == "BUY"
        else stop_loss - reference_price
    )
    reward_distance = (
        take_profit - reference_price
        if direction == "BUY"
        else reference_price - take_profit
    )
    reward_risk_ratio = (
        round(reward_distance / risk_distance, 4)
        if risk_distance > 0 and reward_distance > 0
        else None
    )
    if (
        stop_loss <= 0
        or take_profit <= 0
        or reward_risk_ratio is None
        or reward_risk_ratio < minimum_reward_risk_ratio
    ):
        return unavailable(
            "fallback_plan_invalid",
            atr14=round(float(atr14), 8),
            analysisBarCount=len(bars),
            latestClosedBarTime=bar_times[-1],
        )
    return _ai_trade_council_protective_fallback_result(
        snapshot_id=snapshot_id,
        reason_code="price_action_hold_consensus_fallback",
        minimum_reward_risk_ratio=minimum_reward_risk_ratio,
        available=True,
        stop_loss_price=stop_loss,
        take_profit_price=take_profit,
        reward_risk_ratio=reward_risk_ratio,
        provenance={
            "atr14": round(float(atr14), 8),
            "minimumStopAtrMultiplier": (
                AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MINIMUM_STOP_ATR
            ),
            "structureBufferAtrMultiplier": (
                AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_STRUCTURE_BUFFER_ATR
            ),
            "maximumStructureDistanceAtr": (
                AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_MAX_STRUCTURE_DISTANCE_ATR
            ),
            "structureAnchorType": anchor_type,
            "structureAnchorPrice": (
                round(float(anchor_price), 8)
                if anchor_price is not None
                else None
            ),
            "targetBasis": target_basis,
            "analysisBarCount": len(bars),
            "latestClosedBarTime": bar_times[-1],
            "referencePrice": round(float(reference_price), 8),
            "snapshotArtifactDigest": expected_artifact_digest,
        },
    )


def ai_trade_council_consensus(parent: dict, children: list[dict]) -> dict:
    context = parent.get("analysisContext") if isinstance(parent.get("analysisContext"), dict) else {}
    snapshot_id = str(context.get("snapshotId") or "")
    quality_input = (
        context.get("qualityGate")
        if isinstance(context.get("qualityGate"), dict)
        else {}
    )
    quality_policy = {
        "confidenceFloorDefault": clamp_int(
            quality_input.get("confidenceFloorDefault"), 70, 0, 100
        ),
        "confidenceFloorByRole": (
            quality_input.get("confidenceFloorByRole")
            if isinstance(quality_input.get("confidenceFloorByRole"), dict)
            else {}
        ),
        "minimumRewardRiskRatio": (
            _safe_snapshot_number(
                quality_input.get("minimumRewardRiskRatio"),
                minimum=0.00000001,
                maximum=100,
            )
            or 1.0
        ),
    }
    expected_horizon_bars = context.get("horizonBars")
    expected_valid_until = context.get("validUntilBarTime")
    votes = []
    seen_agents: set[str] = set()
    for child in children:
        vote = child.get("councilVote") if isinstance(child.get("councilVote"), dict) else None
        agent_id = str(child.get("owner") or "")
        if (
            not vote
            or agent_id in seen_agents
            or agent_id not in AI_TRADE_COUNCIL_AGENT_ROLES
            or vote.get("agentId") != agent_id
            or vote.get("roleId") != AI_TRADE_COUNCIL_AGENT_ROLES[agent_id]
            or vote.get("snapshotId") != snapshot_id
            or vote.get("horizonBars") != expected_horizon_bars
            or vote.get("validUntilBarTime") != expected_valid_until
        ):
            continue
        seen_agents.add(agent_id)
        votes.append(vote)
    complete = (
        len(votes) == 3
        and seen_agents == set(AI_TRADE_COUNCIL_AGENT_ROLES)
        and bool(snapshot_id)
        and isinstance(expected_horizon_bars, int)
        and not isinstance(expected_horizon_bars, bool)
        and isinstance(expected_valid_until, int)
        and not isinstance(expected_valid_until, bool)
    )
    vote_by_role = {
        str(item.get("roleId") or ""): item
        for item in votes
    }
    decisions = [str(item.get("decision") or "") for item in votes]
    required_votes = (
        _valid_ai_trade_council_required_votes(context.get("requiredVotes"))
        or AI_TRADE_COUNCIL_DEFAULT_REQUIRED_VOTES
    )
    direction_counts = {
        "BUY": decisions.count("BUY"),
        "HOLD": decisions.count("HOLD"),
        "SELL": decisions.count("SELL"),
        "NO_DATA": decisions.count("NO_DATA"),
    }
    direction_conflict = bool(
        direction_counts["BUY"] > 0 and direction_counts["SELL"] > 0
    )
    selected_direction = None
    if complete and not direction_conflict:
        if direction_counts["BUY"] >= required_votes:
            selected_direction = "BUY"
        elif direction_counts["SELL"] >= required_votes:
            selected_direction = "SELL"
    directional_vote_count = (
        direction_counts[selected_direction]
        if selected_direction in {"BUY", "SELL"}
        else max(direction_counts["BUY"], direction_counts["SELL"])
    )
    consensus_reached = selected_direction in {"BUY", "SELL"}
    unanimous_direction = (
        decisions[0]
        if complete and len(set(decisions)) == 1 and decisions[0] in {"BUY", "SELL"}
        else None
    )
    quality_reasons: list[str] = []
    if not complete:
        quality_reasons.append("incomplete_or_mismatched_votes")
    if quality_input.get("passed") is not True:
        quality_reasons.extend(
            str(item)
            for item in (quality_input.get("reasonCodes") or ["input_quality_gate_not_passed"])
            if str(item)
        )

    round_deadline = parse_iso(str(context.get("roundDeadlineAt") or ""))
    completed_vote_times = [
        completed_at.astimezone(timezone.utc)
        for completed_at in (
            parse_iso(str(child.get("completedAt") or ""))
            for child in children
            if isinstance(child.get("councilVote"), dict)
        )
        if completed_at is not None
    ]
    # A completed round is evaluated at the instant its final vote arrived.  The
    # reconciliation worker may revisit historical missions later; wall-clock
    # time must not retroactively turn a valid decision into an expired one.
    evaluation_time = (
        max(completed_vote_times)
        if complete and len(completed_vote_times) == len(votes)
        else datetime.now(timezone.utc)
    )
    round_expired = bool(
        round_deadline is None
        or evaluation_time > round_deadline.astimezone(timezone.utc)
    )
    if round_deadline is None:
        quality_reasons.append("round_deadline_unavailable")
    elif round_expired:
        quality_reasons.append("round_deadline_expired")
    horizon_expired = bool(
        not isinstance(expected_valid_until, int)
        or isinstance(expected_valid_until, bool)
        or int(evaluation_time.timestamp()) >= expected_valid_until
    )
    if horizon_expired:
        quality_reasons.append("decision_horizon_expired")

    confidence_checks = {}
    for role_id in AI_TRADE_COUNCIL_AGENT_ROLES.values():
        vote = vote_by_role.get(role_id)
        floor = clamp_int(
            quality_policy["confidenceFloorByRole"].get(role_id),
            quality_policy["confidenceFloorDefault"],
            0,
            100,
        )
        observed = (
            _safe_snapshot_number(vote.get("confidence"), minimum=0, maximum=100)
            if isinstance(vote, dict)
            else None
        )
        required_for_consensus = bool(
            consensus_reached
            and isinstance(vote, dict)
            and vote.get("decision") == selected_direction
        )
        observed_passed = observed is not None and observed >= floor
        passed = bool(not required_for_consensus or observed_passed)
        confidence_checks[role_id] = {
            "observed": observed,
            "floor": floor,
            "required": required_for_consensus,
            "passed": passed,
        }
        if complete and required_for_consensus and not observed_passed:
            quality_reasons.append(f"confidence_below_floor:{role_id}")

    technical_vote = vote_by_role.get("technical") or {}
    expected_volatility = str(
        ((quality_input.get("technical") or {}).get("volatilityState"))
        if isinstance(quality_input.get("technical"), dict)
        else ""
    )
    technical_required = complete
    technical_observed_passed = bool(
        complete
        and technical_vote.get("decision") in {"BUY", "HOLD", "SELL"}
        and technical_vote.get("indicatorValidation") == "PASS"
        and technical_vote.get("volatilityState") == expected_volatility
        and expected_volatility in {"LOW", "NORMAL", "HIGH"}
    )
    technical_passed = bool(
        complete and (not technical_required or technical_observed_passed)
    )
    if complete and technical_required and not technical_observed_passed:
        quality_reasons.append("technical_deterministic_validation_failed")

    news_vote = vote_by_role.get("news") or {}
    news_evidence = (
        news_vote.get("newsEvidence")
        if isinstance(news_vote.get("newsEvidence"), dict)
        else {}
    )
    news_decision = str(news_vote.get("decision") or "")
    news_event_risk = str(news_vote.get("eventRisk") or "")
    news_directional = news_decision in {"BUY", "SELL"}
    news_required = bool(complete and news_directional)
    news_veto = news_event_risk == "VETO"
    news_abstained = bool(
        complete
        and news_decision == "HOLD"
        and news_event_risk in {"ALLOW", "HOLD"}
    )
    directional_news_evidence_passed = bool(
        news_directional
        and news_event_risk == "ALLOW"
        and news_evidence.get("fresh") is True
        and int(news_evidence.get("distinctDomains") or 0)
        >= int(news_evidence.get("requiredDistinctDomains") or 2)
    )
    news_observed_passed = bool(
        complete
        and not news_veto
        and (news_abstained or directional_news_evidence_passed)
    )
    news_passed = news_observed_passed
    if complete and not news_observed_passed:
        quality_reasons.append(
            "news_event_veto"
            if news_veto
            else (
                "news_evidence_gate_failed"
                if news_directional
                else "news_vote_unavailable"
            )
        )

    price_action_vote = vote_by_role.get("price_action") or {}
    stop_loss = _safe_snapshot_number(
        price_action_vote.get("stopLossPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    take_profit = _safe_snapshot_number(
        price_action_vote.get("takeProfitPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    reference_price = _safe_snapshot_number(
        context.get("referencePrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    reward_risk_ratio = None
    if (
        selected_direction in {"BUY", "SELL"}
        and price_action_vote.get("decision") == selected_direction
        and stop_loss is not None
        and take_profit is not None
        and reference_price is not None
    ):
        risk_distance = (
            reference_price - stop_loss
            if selected_direction == "BUY"
            else stop_loss - reference_price
        )
        reward_distance = (
            take_profit - reference_price
            if selected_direction == "BUY"
            else reference_price - take_profit
        )
        if risk_distance > 0 and reward_distance > 0:
            reward_risk_ratio = round(reward_distance / risk_distance, 4)
    agent_protective_prices_ready = bool(
        reward_risk_ratio is not None
        and reward_risk_ratio >= quality_policy["minimumRewardRiskRatio"]
    )
    protective_plan = {
        "available": agent_protective_prices_ready,
        "stopLossPrice": stop_loss,
        "takeProfitPrice": take_profit,
        "rewardRiskRatio": reward_risk_ratio,
        "priceAggregation": (
            "price_action_single_owner"
            if agent_protective_prices_ready
            else "unavailable"
        ),
        "protectivePriceOwnerRole": (
            "price_action" if agent_protective_prices_ready else None
        ),
        "protectivePlanSource": (
            "price_action_agent"
            if agent_protective_prices_ready
            else "unavailable"
        ),
        "protectivePlanReasonCode": (
            "price_action_directional_plan"
            if agent_protective_prices_ready
            else "consensus_not_trade_eligible"
        ),
        "protectivePlanPolicyVersion": (
            "price-action-agent-output-v1"
            if agent_protective_prices_ready
            else AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION
        ),
        "protectivePlanFallbackUsed": False,
        "protectivePlanProvenance": {
            "schemaVersion": "ai-trade-council-protective-plan-v1",
            "source": (
                "price_action_agent"
                if agent_protective_prices_ready
                else "unavailable"
            ),
            "reasonCode": (
                "price_action_directional_plan"
                if agent_protective_prices_ready
                else "consensus_not_trade_eligible"
            ),
            "policyVersion": (
                "price-action-agent-output-v1"
                if agent_protective_prices_ready
                else AI_TRADE_COUNCIL_PROTECTIVE_FALLBACK_POLICY_VERSION
            ),
            "snapshotId": snapshot_id or None,
            "closedBarsOnly": True,
            "formulaVersion": context.get("indicatorFormulaVersion"),
            "minimumRewardRiskRatio": quality_policy[
                "minimumRewardRiskRatio"
            ],
        },
    }
    protective_fallback_attempted = False
    fallback_eligible = bool(
        complete
        and consensus_reached
        and not direction_conflict
        and not quality_reasons
        and technical_passed
        and news_passed
        and not round_expired
        and not horizon_expired
        and price_action_vote.get("decision") == "HOLD"
        and stop_loss is None
        and take_profit is None
    )
    if not agent_protective_prices_ready and fallback_eligible:
        protective_fallback_attempted = True
        protective_plan = _ai_trade_council_deterministic_protective_plan(
            context=context,
            direction=str(selected_direction or ""),
            minimum_reward_risk_ratio=quality_policy[
                "minimumRewardRiskRatio"
            ],
        )
        if protective_plan.get("available") is True:
            stop_loss = _safe_snapshot_number(
                protective_plan.get("stopLossPrice"),
                minimum=0.00000001,
                maximum=1_000_000_000,
            )
            take_profit = _safe_snapshot_number(
                protective_plan.get("takeProfitPrice"),
                minimum=0.00000001,
                maximum=1_000_000_000,
            )
            reward_risk_ratio = _safe_snapshot_number(
                protective_plan.get("rewardRiskRatio"),
                minimum=0.00000001,
                maximum=100,
            )
    protective_prices_ready = bool(
        protective_plan.get("available") is True
        and stop_loss is not None
        and take_profit is not None
        and reward_risk_ratio is not None
        and reward_risk_ratio >= quality_policy["minimumRewardRiskRatio"]
    )
    if complete and consensus_reached and not protective_prices_ready:
        quality_reasons.append("price_action_protective_plan_failed")
        fallback_reason = str(
            protective_plan.get("protectivePlanReasonCode") or ""
        )
        if protective_fallback_attempted and fallback_reason.startswith("fallback_"):
            quality_reasons.append(fallback_reason)
    if complete and direction_conflict:
        quality_reasons.append("direction_conflict_buy_sell")
    elif complete and not consensus_reached:
        quality_reasons.append("directional_votes_below_threshold")

    quality_reasons = list(dict.fromkeys(quality_reasons))
    quality_passed = bool(
        complete
        and consensus_reached
        and not direction_conflict
        and protective_prices_ready
        and technical_passed
        and news_passed
        and not round_expired
        and not horizon_expired
        and not quality_reasons
    )
    decision = (
        selected_direction
        if quality_passed
        else ("NO_TRADE" if complete else "NO_DATA")
    )
    trade_plan = (
        {
            "available": True,
            "direction": decision,
            "stopLossPrice": round(float(stop_loss), 8),
            "takeProfitPrice": round(float(take_profit), 8),
            "priceAggregation": protective_plan.get("priceAggregation"),
            "protectivePriceOwnerRole": protective_plan.get(
                "protectivePriceOwnerRole"
            ),
            "rewardRiskRatio": reward_risk_ratio,
            "protectivePlanSource": protective_plan.get(
                "protectivePlanSource"
            ),
            "protectivePlanReasonCode": protective_plan.get(
                "protectivePlanReasonCode"
            ),
            "protectivePlanPolicyVersion": protective_plan.get(
                "protectivePlanPolicyVersion"
            ),
            "protectivePlanFallbackUsed": protective_plan.get(
                "protectivePlanFallbackUsed"
            ) is True,
            "protectivePlanProvenance": protective_plan.get(
                "protectivePlanProvenance"
            ),
            "lotPolicy": "ea_fixed_lot_only",
            "aiLotAllowed": False,
        }
        if decision in {"BUY", "SELL"}
        else {
            "available": False,
            "direction": None,
            "stopLossPrice": None,
            "takeProfitPrice": None,
            "priceAggregation": protective_plan.get("priceAggregation"),
            "protectivePriceOwnerRole": protective_plan.get(
                "protectivePriceOwnerRole"
            ),
            "rewardRiskRatio": reward_risk_ratio,
            "protectivePlanSource": protective_plan.get(
                "protectivePlanSource"
            ),
            "protectivePlanReasonCode": protective_plan.get(
                "protectivePlanReasonCode"
            ),
            "protectivePlanPolicyVersion": protective_plan.get(
                "protectivePlanPolicyVersion"
            ),
            "protectivePlanFallbackUsed": protective_plan.get(
                "protectivePlanFallbackUsed"
            ) is True,
            "protectivePlanProvenance": protective_plan.get(
                "protectivePlanProvenance"
            ),
            "lotPolicy": "ea_fixed_lot_only",
            "aiLotAllowed": False,
        }
    )
    average_confidence = (
        round(sum(float(item.get("confidence") or 0) for item in votes) / len(votes), 2)
        if votes
        else 0
    )
    return {
        "schemaVersion": "ai-trade-council-consensus-v4",
        "snapshotId": snapshot_id or None,
        "ready": complete,
        "decision": decision,
        "unanimous": unanimous_direction in {"BUY", "SELL"},
        "consensusReached": consensus_reached,
        "agreementMet": consensus_reached,
        "directionalAgreementMet": consensus_reached,
        "selectedDirection": selected_direction,
        "requiredVotes": required_votes,
        "directionalVoteCount": directional_vote_count,
        "directionConflict": direction_conflict,
        "conflictingDirections": direction_conflict,
        "directionCounts": direction_counts,
        "voteCount": len(votes),
        "votes": votes,
        "tradePlan": trade_plan,
        "averageConfidence": average_confidence,
        "horizonBars": expected_horizon_bars,
        "validUntilBarTime": expected_valid_until,
        "qualityGate": {
            "schemaVersion": "ai-trade-council-decision-quality-v2",
            "passed": quality_passed,
            "status": "passed" if quality_passed else "blocked",
            "reasonCodes": quality_reasons,
            "inputQualityPassed": quality_input.get("passed") is True,
            "confidence": confidence_checks,
            "technicalValidationPassed": technical_passed,
            "technicalValidationRequired": technical_required,
            "newsEvidencePassed": news_passed,
            "newsEvidenceRequired": news_required,
            "newsVeto": news_veto,
            "newsAbstained": news_abstained,
            "protectivePlanPassed": protective_prices_ready,
            "protectivePlanFallbackAttempted": protective_fallback_attempted,
            "protectivePlanFallbackUsed": trade_plan.get(
                "protectivePlanFallbackUsed"
            ) is True,
            "protectivePlanSource": trade_plan.get("protectivePlanSource"),
            "protectivePlanReasonCode": trade_plan.get(
                "protectivePlanReasonCode"
            ),
            "protectivePlanPolicyVersion": trade_plan.get(
                "protectivePlanPolicyVersion"
            ),
            "consensusThresholdPassed": consensus_reached,
            "requiredVotes": required_votes,
            "directionalVoteCount": directional_vote_count,
            "directionConflict": direction_conflict,
            "roundDeadlineAt": context.get("roundDeadlineAt"),
            "roundExpired": round_expired,
            "horizonExpired": horizon_expired,
            "higherTimeframeContext": quality_input.get("higherTimeframeContext"),
            "marketState": quality_input.get("marketState"),
            "executionEligibility": quality_input.get("executionEligibility"),
        },
        "decisionProvenance": {
            "schemaVersion": "ai-trade-council-decision-provenance-v1",
            "snapshotId": snapshot_id or None,
            "contractDigest": context.get("contractDigest"),
            "closedBarIdentity": context.get("closedBarIdentity"),
            "agentIds": [
                str(item.get("agentId") or "")
                for item in votes
            ],
            "roleIds": [
                str(item.get("roleId") or "")
                for item in votes
            ],
            "consensusRule": (
                f"{required_votes}_of_three_no_opposite_direction_plus_quality_gate"
            ),
            "requiredVotes": required_votes,
            "directionalVoteCount": directional_vote_count,
            "directionConflict": direction_conflict,
            "protectivePriceOwnerRole": trade_plan.get(
                "protectivePriceOwnerRole"
            ),
            "protectivePlanSource": trade_plan.get("protectivePlanSource"),
            "protectivePlanReasonCode": trade_plan.get(
                "protectivePlanReasonCode"
            ),
            "protectivePlanPolicyVersion": trade_plan.get(
                "protectivePlanPolicyVersion"
            ),
            "protectivePlanFallbackUsed": trade_plan.get(
                "protectivePlanFallbackUsed"
            ) is True,
            "createdAt": evaluation_time.isoformat().replace("+00:00", "Z"),
        },
        "outcomeTracking": {
            "schemaVersion": "ai-trade-council-outcome-tracking-v1",
            "status": "pending" if complete else "unavailable",
            "evaluationBars": [1, 3, 5],
            "decision": decision,
            "snapshotId": snapshot_id or None,
            "horizonBars": expected_horizon_bars,
            "validUntilBarTime": expected_valid_until,
            "evaluations": [],
            "decisionProvenanceStatus": (
                "recorded" if complete else "incomplete"
            ),
        },
        "riskGuard": {
            "agentId": "risk_guard",
            "voting": False,
            "status": "not_evaluated_by_agent",
            "qualityGateStatus": "passed" if quality_passed else "blocked",
            "terminalActions": False,
        },
        "terminalActions": False,
    }


def _ai_trade_council_gateway_result(
    *,
    status: str,
    reason_code: str,
    gateway_status: dict | None = None,
    command: dict | None = None,
    command_published: bool = False,
) -> dict:
    observed_gateway = gateway_status if isinstance(gateway_status, dict) else {}
    command_ack = (
        command.get("ack")
        if isinstance(command, dict) and isinstance(command.get("ack"), dict)
        else {}
    )
    ack_status = str(command_ack.get("status") or "")
    return {
        "schemaVersion": "ai-trade-council-gateway-result-v1",
        "status": status,
        "reasonCode": reason_code,
        "connected": observed_gateway.get("connected") is True,
        "mode": observed_gateway.get("mode"),
        "fixedLot": observed_gateway.get("fixedLot"),
        "fixedLotSource": "ea_input_read_only",
        "aiCanSetLotOrRisk": False,
        "liveArmed": observed_gateway.get("liveArmed") is True,
        "killSwitchActive": observed_gateway.get("killSwitchActive") is True,
        "executionGuardReady": observed_gateway.get("executionGuardReady") is True,
        "executionGuardReason": observed_gateway.get("executionGuardReason"),
        "commandPublished": command_published,
        "commandId": (
            safe_reference(command.get("commandId"))
            if isinstance(command, dict)
            else None
        ),
        "command": command,
        "ackStatus": ack_status or None,
        "orderExecutionConfirmed": ack_status == "EXECUTED",
        "shadowValidationConfirmed": ack_status == "SHADOWED",
        "updatedAt": utc_now(),
    }


def dispatch_ai_trade_council_trade_plan(
    parent: dict,
    consensus: dict,
) -> dict:
    """Publish only a threshold-qualified Direction+SL+TP plan to the selected MT4 EA."""
    context = (
        parent.get("analysisContext")
        if isinstance(parent.get("analysisContext"), dict)
        else {}
    )
    prior = (
        parent.get("tradeGateway")
        if isinstance(parent.get("tradeGateway"), dict)
        else {}
    )
    prior_command_id = safe_reference(prior.get("commandId"))
    if prior_command_id:
        stored_command = _mt4_trade_gateway_command_read_model(prior_command_id)
        if stored_command:
            gateway_status = mt4_trade_gateway_status_read_model()
            stored_ack = (
                stored_command.get("ack")
                if isinstance(stored_command.get("ack"), dict)
                else {}
            )
            ack_status = str(stored_ack.get("status") or "")
            return _ai_trade_council_gateway_result(
                status=(
                    f"ack_{ack_status.lower()}"
                    if ack_status
                    else str(stored_command.get("status") or "waiting_ack")
                ),
                reason_code=(
                    str(stored_ack.get("reasonCode") or "waiting_ea_ack")
                    if stored_ack
                    else "waiting_ea_ack"
                ),
                gateway_status=gateway_status,
                command=stored_command,
                command_published=True,
            )
        # A previously published command is a durable one-way boundary. If its
        # ledger record is unavailable, fail closed instead of reconstructing
        # and publishing a second order command from the same Council result.
        return {
            **prior,
            "schemaVersion": str(
                prior.get("schemaVersion")
                or "ai-trade-council-gateway-result-v1"
            ),
            "status": "blocked",
            "reasonCode": "published_command_record_missing",
            "commandPublished": True,
            "commandId": prior_command_id,
            "orderExecutionConfirmed": False,
            "updatedAt": utc_now(),
        }
    if prior.get("commandPublished") is True:
        return {
            **prior,
            "schemaVersion": str(
                prior.get("schemaVersion")
                or "ai-trade-council-gateway-result-v1"
            ),
            "status": "blocked",
            "reasonCode": "published_command_identity_missing",
            "commandPublished": True,
            "commandId": None,
            "orderExecutionConfirmed": False,
            "updatedAt": utc_now(),
        }

    trade_plan = (
        consensus.get("tradePlan")
        if isinstance(consensus.get("tradePlan"), dict)
        else {}
    )
    decision_quality = (
        consensus.get("qualityGate")
        if isinstance(consensus.get("qualityGate"), dict)
        else {}
    )
    direction = str(trade_plan.get("direction") or "").upper()
    required_votes = (
        _valid_ai_trade_council_required_votes(consensus.get("requiredVotes"))
        or AI_TRADE_COUNCIL_DEFAULT_REQUIRED_VOTES
    )
    directional_vote_count = consensus.get("directionalVoteCount")
    if isinstance(directional_vote_count, bool) or not isinstance(
        directional_vote_count, int
    ):
        directional_vote_count = (
            3
            if required_votes == 3 and consensus.get("unanimous") is True
            else 0
        )
    consensus_reached = bool(
        consensus.get("consensusReached") is True
        or (
            "consensusReached" not in consensus
            and required_votes == 3
            and consensus.get("unanimous") is True
        )
    )
    selected_direction = str(
        consensus.get("selectedDirection")
        or (direction if required_votes == 3 and consensus.get("unanimous") is True else "")
    ).upper()
    if not (
        consensus.get("ready") is True
        and consensus_reached
        and consensus.get("directionConflict") is not True
        and directional_vote_count >= required_votes
        and selected_direction == direction
        and consensus.get("voteCount") == 3
        and decision_quality.get("passed") is True
        and trade_plan.get("available") is True
        and direction in {"BUY", "SELL"}
    ):
        return _ai_trade_council_gateway_result(
            status="no_trade",
            reason_code=(
                "decision_quality_gate_not_passed"
                if consensus_reached and consensus.get("ready") is True
                else "consensus_threshold_not_met"
            ),
        )

    dispatch_deadline = parse_iso(str(context.get("roundDeadlineAt") or ""))
    now_utc = datetime.now(timezone.utc)
    if (
        dispatch_deadline is None
        or now_utc >= dispatch_deadline.astimezone(timezone.utc)
    ):
        return _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="decision_dispatch_window_expired",
        )

    stop_loss = _safe_snapshot_number(
        trade_plan.get("stopLossPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    take_profit = _safe_snapshot_number(
        trade_plan.get("takeProfitPrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    reference_price = _safe_snapshot_number(
        context.get("referencePrice"),
        minimum=0.00000001,
        maximum=1_000_000_000,
    )
    snapshot_observed = parse_iso(str(context.get("snapshotObservedAt") or ""))
    snapshot_observed_at = (
        int(snapshot_observed.astimezone(timezone.utc).timestamp())
        if snapshot_observed is not None
        else None
    )
    bar_identity = (
        context.get("closedBarIdentity")
        if isinstance(context.get("closedBarIdentity"), dict)
        else {}
    )
    channel_id = safe_reference(bar_identity.get("candidateId"))
    stream_key = str(bar_identity.get("streamKey") or "")
    symbol = _safe_snapshot_symbol(bar_identity.get("symbol"))
    timeframe = _safe_snapshot_timeframe(bar_identity.get("timeframe"))
    bar_time = bar_identity.get("closedBarTime")
    snapshot_id = str(consensus.get("snapshotId") or "")
    valid_until_bar_time = consensus.get("validUntilBarTime")
    if (
        isinstance(valid_until_bar_time, bool)
        or not isinstance(valid_until_bar_time, int)
        or int(datetime.now(timezone.utc).timestamp()) >= valid_until_bar_time
    ):
        return _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="decision_horizon_expired",
        )
    valid_price_direction = bool(
        stop_loss is not None
        and take_profit is not None
        and reference_price is not None
        and (
            (
                direction == "BUY"
                and stop_loss < reference_price < take_profit
            )
            or (
                direction == "SELL"
                and take_profit < reference_price < stop_loss
            )
        )
    )
    if not (
        valid_price_direction
        and channel_id
        and channel_id.startswith("mtc-")
        and re.fullmatch(r"[0-9a-f]{64}", stream_key)
        and symbol
        and timeframe in AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES
        and isinstance(bar_time, int)
        and not isinstance(bar_time, bool)
        and 946684800 <= bar_time <= 2_147_483_647
        and isinstance(snapshot_observed_at, int)
        and 946684800 <= snapshot_observed_at <= 2_147_483_647
        and re.fullmatch(r"[0-9a-f]{64}", snapshot_id)
    ):
        result = _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="trade_plan_identity_invalid",
        )
        append_audit({
            "type": "ai_trade_council.trade_gateway_blocked",
            "missionId": parent.get("id"),
            "snapshotId": snapshot_id or None,
            "reason": result["reasonCode"],
            "aiLotAllowed": False,
        })
        return result

    gateway_status = mt4_trade_gateway_status_read_model()
    if gateway_status.get("connected") is not True:
        return _ai_trade_council_gateway_result(
            status="waiting_gateway",
            reason_code=str(
                gateway_status.get("reasonCode")
                or "mt4_trade_gateway_not_connected"
            ),
            gateway_status=gateway_status,
        )
    if (
        gateway_status.get("selectedCandidateId") != channel_id
        or str(gateway_status.get("symbol") or "").upper() != symbol.upper()
        or gateway_status.get("timeframe") != timeframe
    ):
        result = _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="gateway_chart_mismatch",
            gateway_status=gateway_status,
        )
        append_audit({
            "type": "ai_trade_council.trade_gateway_blocked",
            "missionId": parent.get("id"),
            "snapshotId": snapshot_id,
            "reason": result["reasonCode"],
            "symbol": symbol,
            "timeframe": timeframe,
            "channelId": channel_id,
        })
        return result
    mode = str(gateway_status.get("mode") or "")
    execution_eligibility = (
        decision_quality.get("executionEligibility")
        if isinstance(decision_quality.get("executionEligibility"), dict)
        else {}
    )
    if mode in {"shadow", "demo", "live"} and execution_eligibility.get(mode) is not True:
        result = _ai_trade_council_gateway_result(
            status="blocked",
            reason_code=(
                "market_state_unavailable_or_closed"
                if mode in {"demo", "live"}
                else "shadow_quality_gate_not_ready"
            ),
            gateway_status=gateway_status,
        )
        append_audit({
            "type": "ai_trade_council.trade_gateway_blocked",
            "missionId": parent.get("id"),
            "snapshotId": snapshot_id,
            "reason": result["reasonCode"],
            "modeObservedFromEa": mode,
            "marketState": decision_quality.get("marketState"),
            "aiLotAllowed": False,
        })
        return result
    if gateway_status.get("killSwitchActive") is True:
        return _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="kill_switch_active",
            gateway_status=gateway_status,
        )
    if (
        mode in {"demo", "live"}
        and gateway_status.get("executionGuardReady") is not True
    ):
        return _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="execution_guard_not_ready",
            gateway_status=gateway_status,
        )
    if (
        mode == "demo"
        and gateway_status.get("demoOrderExecutionAvailable") is not True
    ):
        return _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="demo_execution_gate_not_ready",
            gateway_status=gateway_status,
        )
    if (
        mode == "live"
        and gateway_status.get("liveOrderExecutionAvailable") is not True
    ):
        return _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="live_execution_gate_not_ready",
            gateway_status=gateway_status,
        )
    if mode not in {"shadow", "demo", "live"}:
        return _ai_trade_council_gateway_result(
            status="blocked",
            reason_code="gateway_mode_invalid",
            gateway_status=gateway_status,
        )

    council_decision_id = (
        f"council-{payload_digest(str(parent.get('id') or ''), snapshot_id)[:24]}"
    )
    intent = {
        "channelId": channel_id,
        "streamKey": stream_key,
        "snapshotId": snapshot_id,
        "snapshotObservedAt": snapshot_observed_at,
        "barTime": bar_time,
        "missionId": str(parent.get("id") or ""),
        "councilDecisionId": council_decision_id,
        "ownerAgentId": "manager",
        "action": direction,
        "symbol": symbol,
        "timeframe": timeframe,
        "referencePrice": reference_price,
        "stopLoss": stop_loss,
        "takeProfit": take_profit,
    }
    try:
        with MT4_TRADE_GATEWAY_LOCK:
            gateway = _mt4_trade_gateway_instance()
            published = gateway.queue_trade_intent(intent)
            command_id = safe_reference(
                (published.get("command") or {}).get("commandId")
            )
            command = (
                _mt4_trade_gateway_command_summary(
                    gateway.read_command(command_id)
                )
                if command_id
                else None
            )
    except Exception as error:
        reason_code = str(
            getattr(error, "code", "")
            or "trade_gateway_publish_failed"
        )
        result = _ai_trade_council_gateway_result(
            status=(
                "waiting_previous_ack"
                if reason_code == "single_outstanding_command"
                else "blocked"
            ),
            reason_code=reason_code,
            gateway_status=gateway_status,
        )
        append_audit({
            "type": "ai_trade_council.trade_gateway_blocked",
            "missionId": parent.get("id"),
            "snapshotId": snapshot_id,
            "reason": reason_code,
            "direction": direction,
            "requiredVotes": required_votes,
            "directionalVoteCount": directional_vote_count,
            "symbol": symbol,
            "timeframe": timeframe,
            "aiLotAllowed": False,
        })
        return result
    result = _ai_trade_council_gateway_result(
        status=(
            "queued_existing"
            if published.get("idempotentReplay") is True
            else "queued"
        ),
        reason_code=str(published.get("kind") or "mt4_trade_command_published"),
        gateway_status=gateway_status,
        command=command,
        command_published=True,
    )
    append_audit({
        "type": "ai_trade_council.trade_gateway_published",
        "missionId": parent.get("id"),
        "councilDecisionId": council_decision_id,
        "commandId": result.get("commandId"),
        "snapshotId": snapshot_id,
        "snapshotObservedAt": snapshot_observed_at,
        "closedBarTime": bar_time,
        "referencePrice": reference_price,
        "direction": direction,
        "requiredVotes": required_votes,
        "directionalVoteCount": directional_vote_count,
        "symbol": symbol,
        "timeframe": timeframe,
        "stopLossPrice": stop_loss,
        "takeProfitPrice": take_profit,
        "modeObservedFromEa": mode,
        "fixedLotSource": "ea_input_only",
        "aiLotAllowed": False,
        "idempotentReplay": published.get("idempotentReplay") is True,
    })
    return result


def _parent_child_aggregation_digest(children: list[dict]) -> str:
    """Hash child semantics while ignoring heartbeat/timestamp-only updates."""
    packets = []
    for child in children:
        execution = (
            child.get("execution")
            if isinstance(child.get("execution"), dict)
            else {}
        )
        packets.append({
            "id": str(child.get("id") or ""),
            "owner": str(child.get("owner") or ""),
            "status": str(child.get("status") or ""),
            "outcomeStatus": mission_outcome_status(child),
            "phase": str(child.get("phase") or ""),
            "result": str(child.get("result") or ""),
            "errorCode": str(child.get("errorCode") or ""),
            "archivedFromStatus": str(child.get("archivedFromStatus") or ""),
            "archivedSuccessful": child.get("archivedSuccessful") is True,
            "processStarted": execution.get("processStarted") is True,
            "dispatchState": str(execution.get("dispatchState") or ""),
            "councilVote": sanitize_json_value(
                child.get("councilVote")
                if isinstance(child.get("councilVote"), dict)
                else {}
            ),
        })
    packets.sort(key=lambda item: (item["id"], item["owner"]))
    canonical = json.dumps(
        packets,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8", errors="replace")).hexdigest()


def _parent_expected_active_state(children: list[dict]) -> tuple[str, str] | None:
    statuses = {str(child.get("status") or "") for child in children}
    if "running" in statuses:
        return "running", "specialists_running"
    if "waiting_approval" in statuses:
        return "waiting_approval", "awaiting_specialist_approval"
    if "queued" in statuses:
        return "queued", "awaiting_specialist_start"
    return None


def _ai_trade_council_parent_queue_complete(parent: dict, children: list[dict]) -> bool:
    context = (
        parent.get("analysisContext")
        if isinstance(parent.get("analysisContext"), dict)
        else {}
    )
    if context.get("kind") != "ai_trade_council_parent":
        return True
    expected_owners = set(AI_TRADE_COUNCIL_AGENT_ROLES)
    child_ids = {
        str(child.get("id") or "")
        for child in children
        if safe_reference(child.get("id"))
    }
    parent_child_ids = {
        str(child_id)
        for child_id in (parent.get("subtaskIds") or [])
        if safe_reference(child_id)
    }
    child_owners = {str(child.get("owner") or "") for child in children}
    parent_snapshot_id = str(context.get("snapshotId") or "")
    parent_contract_digest = str(context.get("contractDigest") or "")
    child_contexts_match = all(
        _is_ai_trade_council_vote_mission(child)
        and str((child.get("analysisContext") or {}).get("snapshotId") or "")
        == parent_snapshot_id
        and str((child.get("analysisContext") or {}).get("contractDigest") or "")
        == parent_contract_digest
        for child in children
    )
    return bool(
        len(children) == 3
        and child_owners == expected_owners
        and len(child_ids) == 3
        and parent_child_ids == child_ids
        and re.fullmatch(r"[0-9a-f]{64}", parent_snapshot_id)
        and parent_contract_digest
        and child_contexts_match
        and str(parent.get("phase") or "")
        in {
            "council_specialists_queued",
            "awaiting_specialist_start",
            "specialists_running",
            "awaiting_specialist_approval",
        }
    )


def _ai_trade_council_queue_assembly_is_stale(parent: dict) -> bool:
    created_at = parse_iso(str(parent.get("createdAt") or ""))
    if created_at is None:
        return True
    return (
        datetime.now(timezone.utc) - created_at
    ).total_seconds() >= AI_TRADE_COUNCIL_QUEUE_ASSEMBLY_GRACE_SECONDS


def _parent_mission_is_already_aggregated(parent: dict, children: list[dict]) -> bool:
    """Avoid side effects when the parent already represents child semantics."""
    status = str(parent.get("status") or "")
    if status == "archived":
        return True
    delegation = (
        parent.get("delegation")
        if isinstance(parent.get("delegation"), dict)
        else {}
    )
    active_state = _parent_expected_active_state(children)
    # Terminal parents never move back to an active state. Invalid active
    # descendants are handled fail-closed by the worker-parent gate.
    if status in {"completed", "blocked", "failed"} and active_state is not None:
        return True

    stored_digest = str(delegation.get("childStateDigest") or "")
    if re.fullmatch(r"[0-9a-f]{64}", stored_digest):
        if not secrets.compare_digest(
            stored_digest,
            _parent_child_aggregation_digest(children),
        ):
            return False
        stored_parent_status = str(delegation.get("lastAggregatedParentStatus") or "")
        stored_parent_phase = str(delegation.get("lastAggregatedParentPhase") or "")
        if stored_parent_status and stored_parent_status != status:
            return False
        if stored_parent_phase and stored_parent_phase != str(parent.get("phase") or ""):
            return False
        if active_state is not None:
            return (
                status == active_state[0]
                and str(parent.get("phase") or "") == active_state[1]
            )
        return bool(
            status in {"completed", "blocked", "failed"}
            and delegation.get("finalReportId")
        )

    if status not in {"completed", "blocked", "failed"}:
        return False
    if not delegation.get("finalReportId"):
        return False
    aggregated_at = parse_iso(str(delegation.get("lastAggregatedAt") or ""))
    if aggregated_at is None:
        return False
    child_updates = []
    for child in children:
        for field in ("updatedAt", "completedAt", "createdAt"):
            stamp = parse_iso(str(child.get(field) or ""))
            if stamp is not None:
                child_updates.append(stamp)
                break
    if not child_updates:
        return False
    return max(child_updates) <= aggregated_at


def refresh_parent_mission(parent_mission_id: str | None) -> dict | None:
    with PARENT_MISSION_REFRESH_LOCK:
        return _refresh_parent_mission_locked(parent_mission_id)


def _refresh_parent_mission_locked(parent_mission_id: str | None) -> dict | None:
    """Roll child status and final reports back into the Manager parent mission."""
    if not parent_mission_id:
        return None
    missions = load_missions()
    parent = next((item for item in missions if item.get("id") == parent_mission_id), None)
    if not parent:
        return None
    children = [item for item in missions if item.get("parentMissionId") == parent_mission_id]
    parent_context = (
        parent.get("analysisContext")
        if isinstance(parent.get("analysisContext"), dict)
        else {}
    )
    if (
        parent_context.get("kind") == "ai_trade_council_parent"
        and parent.get("status") in {"queued", "running", "waiting_approval"}
        and not _ai_trade_council_parent_queue_complete(parent, children)
    ):
        if not _ai_trade_council_queue_assembly_is_stale(parent):
            return parent
        recovered_at = utc_now()
        recovered_children = 0
        with MISSIONS_LOCK:
            latest_missions = load_missions()
            latest_parent = next(
                (
                    item
                    for item in latest_missions
                    if item.get("id") == parent_mission_id
                ),
                None,
            )
            latest_children = [
                item
                for item in latest_missions
                if item.get("parentMissionId") == parent_mission_id
            ]
            if (
                not isinstance(latest_parent, dict)
                or latest_parent.get("status")
                not in {"queued", "running", "waiting_approval"}
                or _ai_trade_council_parent_queue_complete(
                    latest_parent,
                    latest_children,
                )
                or not _ai_trade_council_queue_assembly_is_stale(latest_parent)
            ):
                return latest_parent
            for child in latest_children:
                if child.get("status") not in {"queued", "waiting_approval"}:
                    continue
                child["status"] = "blocked"
                child["phase"] = "council_queue_incomplete"
                child["errorCode"] = "council_parent_queue_incomplete"
                child["result"] = (
                    "Council round assembly did not complete. No tool was started."
                )
                child["completedAt"] = recovered_at
                child["updatedAt"] = recovered_at
                execution = (
                    child.get("execution")
                    if isinstance(child.get("execution"), dict)
                    else {}
                )
                execution["dispatchState"] = "blocked"
                execution["completedAt"] = recovered_at
                child["execution"] = execution
                recovered_children += 1
            latest_parent["status"] = "blocked"
            latest_parent["phase"] = "council_queue_incomplete"
            latest_parent["errorCode"] = "council_queue_incomplete_recovered"
            latest_parent["result"] = (
                "Council round assembly was incomplete after a runner interruption. "
                "The round was stopped without terminal action."
            )
            latest_parent["completedAt"] = recovered_at
            latest_parent["updatedAt"] = recovered_at
            save_missions(latest_missions)
            parent = latest_parent
        append_audit({
            "type": "ai_trade_council.queue_incomplete_recovered",
            "missionId": parent_mission_id,
            "blockedSubtaskCount": recovered_children,
            "terminalActions": False,
        })
        return parent
    if not children:
        return parent
    if _parent_mission_is_already_aggregated(parent, children):
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
    delegation["childStateDigest"] = _parent_child_aggregation_digest(children)

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
        parent_context = (
            parent.get("analysisContext")
            if isinstance(parent.get("analysisContext"), dict)
            else {}
        )
        is_council_parent = parent_context.get("kind") == "ai_trade_council_parent"
        council_consensus = (
            ai_trade_council_consensus(parent, children)
            if is_council_parent
            else None
        )
        trade_gateway_result = None
        if is_council_parent and not council_consensus.get("ready"):
            clean_completion = False
            attention_count = max(1, attention_count)
        parent["status"] = "completed" if clean_completion else "blocked"
        parent["phase"] = "synthesized" if clean_completion else "review_required"
        delegation["state"] = parent["phase"]
        if is_council_parent and clean_completion:
            decision_label = str(council_consensus.get("decision") or "NO_TRADE")
            trade_gateway_result = dispatch_ai_trade_council_trade_plan(
                parent,
                council_consensus,
            )
            parent["councilDecision"] = council_consensus
            parent["tradeGateway"] = trade_gateway_result
            gateway_state = str(trade_gateway_result.get("status") or "")
            if gateway_state == "no_trade":
                gateway_message = (
                    "ผลโหวตหรือ Quality Gate ยังไม่ผ่านเกณฑ์ "
                    f"{council_consensus.get('requiredVotes') or 3}/3 "
                    "จึงไม่มีคำสั่งส่งไป MT4"
                )
            elif trade_gateway_result.get("orderExecutionConfirmed") is True:
                gateway_message = "EA ยืนยันการส่ง Order แล้ว และบันทึก ACK กลับสู่ Audit"
            elif trade_gateway_result.get("shadowValidationConfirmed") is True:
                gateway_message = "EA ตรวจคำสั่งในโหมด Shadow ผ่านแล้ว โดยไม่ได้ส่ง Order"
            elif trade_gateway_result.get("commandPublished") is True:
                gateway_message = (
                    f"ส่งแผน Direction/SL/TP ไปยัง EA โหมด "
                    f"{trade_gateway_result.get('mode') or 'ไม่ทราบ'} แล้ว และกำลังรอ ACK"
                )
            elif gateway_state == "waiting_gateway":
                gateway_message = "แผนพร้อมแล้ว แต่กำลังรอให้ติดตั้งและเชื่อม Trade Gateway EA"
            else:
                gateway_message = (
                    "ยังไม่ส่งคำสั่งไป MT4 เพราะระบบป้องกันของ Trade Gateway "
                    f"หยุดไว้ที่ {trade_gateway_result.get('reasonCode') or 'ไม่ทราบสาเหตุ'}"
                )
            parent["result"] = (
                "Manager รวมผลวิเคราะห์จาก Agent ครบ 3 ตัวแล้ว "
                f"ใช้เกณฑ์ {council_consensus.get('requiredVotes') or 3}/3; "
                f"มติของสภา: {decision_label} "
                f"จาก Snapshot เดียวกัน; {gateway_message} "
                "Lot มาจาก FixedLot ใน EA เท่านั้น AI ไม่มีสิทธิ์กำหนด Lot หรือ Risk"
            )
        elif is_council_parent:
            parent["result"] = (
                "ผลวิเคราะห์ของสภา AI Trade ไม่ครบหรือไม่ตรงกับ Snapshot เดียวกัน "
                "ระบบจึงไม่ออกมติและไม่ดำเนินการกับ Terminal"
            )
            parent["councilDecision"] = council_consensus
        else:
            parent["result"] = (
                f"Manager รวบรวมผลจาก Agent ผู้เชี่ยวชาญครบ {completed_count}/{len(children)} งาน และสรุปภาพรวมเรียบร้อยแล้ว"
                if clean_completion
                else f"Manager รวบรวมสถานะสุดท้ายครบแล้ว แต่ยังมี {attention_count} งานที่ต้องตรวจสอบก่อนปิด Mission"
            )
        parent["completedAt"] = parent.get("completedAt") or utc_now()
        final_report = create_report({
            "id": delegation.get("finalReportId"),
            "type": "ai_trade_council_report" if is_council_parent else "executive_summary",
            "title": (
                f"สรุปสภา AI Trade: {(council_consensus or {}).get('decision') or 'NO_DATA'}"
                if is_council_parent
                else f"Executive summary: {parent.get('title') or parent_mission_id}"
            ),
            "summary": parent["result"],
            "ownerAgentId": "manager",
            "linkedMissionId": parent_mission_id,
            "linkedPropId": AI_TRADE_COUNCIL_PROP_ID if is_council_parent else "mission_strategy_table",
            "status": "ready" if clean_completion else "blocked",
            "findings": [
                (
                    f"{(item.get('councilVote') or {}).get('agentId')}: "
                    f"{(item.get('councilVote') or {}).get('decision')} "
                    f"({(item.get('councilVote') or {}).get('confidence')}%)"
                    if is_council_parent and isinstance(item.get("councilVote"), dict)
                    else f"{item.get('owner')}: {mission_display_status(item)} - {redact_text(str(item.get('result') or 'No report summary.'), 600)}"
                )
                for item in children
            ],
            "metrics": (
                {
                    **summary,
                    "outcomes": outcome_summary,
                    "snapshotId": (council_consensus or {}).get("snapshotId"),
                    "decision": (council_consensus or {}).get("decision"),
                    "unanimous": bool((council_consensus or {}).get("unanimous")),
                    "consensusReached": bool(
                        (council_consensus or {}).get("consensusReached")
                    ),
                    "selectedDirection": (council_consensus or {}).get(
                        "selectedDirection"
                    ),
                    "requiredVotes": (council_consensus or {}).get("requiredVotes"),
                    "directionalVoteCount": (council_consensus or {}).get(
                        "directionalVoteCount"
                    ),
                    "directionConflict": bool(
                        (council_consensus or {}).get("directionConflict")
                    ),
                    "directionCounts": (council_consensus or {}).get(
                        "directionCounts"
                    ),
                    "averageConfidence": (council_consensus or {}).get("averageConfidence"),
                    "voteCount": (council_consensus or {}).get("voteCount"),
                    "tradePlan": (council_consensus or {}).get("tradePlan"),
                    "horizonBars": (council_consensus or {}).get("horizonBars"),
                    "validUntilBarTime": (council_consensus or {}).get("validUntilBarTime"),
                    "qualityGate": (council_consensus or {}).get("qualityGate"),
                    "decisionProvenance": (council_consensus or {}).get("decisionProvenance"),
                    "outcomeTracking": (council_consensus or {}).get("outcomeTracking"),
                    "tradeGateway": trade_gateway_result,
                    "riskGuardVoting": False,
                    "terminalActions": bool(
                        isinstance(trade_gateway_result, dict)
                        and trade_gateway_result.get("commandPublished") is True
                    ),
                }
                if is_council_parent
                else {**summary, "outcomes": outcome_summary}
            ),
            "risks": [
                f"{item.get('owner')}: {item.get('errorCode') or mission_outcome_status(item)}"
                for item in children if mission_outcome_status(item) != "completed"
            ],
            "nextActions": (
                []
                if clean_completion
                else [
                    (
                        "เก็บ Snapshot ใหม่แล้วเริ่มการวิเคราะห์อีกครั้ง"
                        if is_council_parent
                        else "ตรวจงานที่ติดขัด ไม่สำเร็จ หรือถูกเก็บโดยยังไม่สำเร็จที่โต๊ะวางแผน Mission"
                    )
                ]
            ),
        })
        delegation["finalReportId"] = final_report["id"]
        report_ids = parent.get("reportIds") if isinstance(parent.get("reportIds"), list) else []
        parent["reportIds"] = list(dict.fromkeys([*report_ids, final_report["id"]]))

    parent["delegation"] = delegation
    delegation["lastAggregatedParentStatus"] = str(parent.get("status") or "")
    delegation["lastAggregatedParentPhase"] = str(parent.get("phase") or "")
    parent["updatedAt"] = utc_now()
    replace_mission(parent)
    append_audit({
        "type": "manager.parent_refreshed",
        "missionId": parent_mission_id,
        "status": parent["status"],
        "phase": parent["phase"],
        "subtaskStatusCounts": counts,
        "subtaskOutcomeCounts": outcome_summary["byOutcome"],
        **(
            {
                "councilDecision": parent.get("councilDecision", {}).get("decision"),
                "councilQualityGate": parent.get("councilDecision", {}).get("qualityGate"),
                "councilProtectivePlan": parent.get("councilDecision", {}).get(
                    "tradePlan"
                ),
                "councilOutcomeTracking": parent.get("councilDecision", {}).get("outcomeTracking"),
            }
            if isinstance(parent.get("councilDecision"), dict)
            else {}
        ),
    })
    AI_TRADE_COUNCIL_AUTOMATION_WAKE.set()
    return parent


def reconcile_parent_mission_statuses() -> int:
    with AI_TRADE_COUNCIL_QUEUE_LOCK:
        return _reconcile_parent_mission_statuses_unlocked()


def _reconcile_parent_mission_statuses_unlocked() -> int:
    """Re-derive Manager parent cards so no parent claims running without a running child."""
    missions = load_missions()
    parent_ids = {
        parent_id
        for parent_id in (
            safe_reference(mission.get("parentMissionId"))
            for mission in missions
        )
        if parent_id
    }
    parent_ids.update(
        str(mission.get("id"))
        for mission in missions
        if safe_reference(mission.get("id"))
        and mission.get("status") in {"queued", "running", "waiting_approval"}
        and isinstance(mission.get("analysisContext"), dict)
        and mission["analysisContext"].get("kind") == "ai_trade_council_parent"
    )
    refreshed = 0
    for parent_id in sorted(parent_ids):
        parent = next(
            (mission for mission in missions if mission.get("id") == parent_id),
            None,
        )
        children = [
            mission
            for mission in missions
            if mission.get("parentMissionId") == parent_id
        ]
        if (
            isinstance(parent, dict)
            and children
            and _parent_mission_is_already_aggregated(parent, children)
        ):
            continue
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


def create_mission(
    payload: dict,
    status: str = "queued",
    allow_model_override: bool = False,
    allow_budget_override: bool = False,
    allow_analysis_context: bool = False,
    workflow_context: dict | None = None,
) -> dict:
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
    analysis_context = (
        payload.get("analysisContext")
        if allow_analysis_context and isinstance(payload.get("analysisContext"), dict)
        else {}
    )
    council_context_valid = (
        analysis_context.get("kind") == "ai_trade_council_vote"
        and analysis_context.get("agentId") == agent_id
        and analysis_context.get("roleId") == AI_TRADE_COUNCIL_AGENT_ROLES.get(agent_id)
        and tool_id == AI_TRADE_COUNCIL_ALLOWED_TOOLS.get(agent_id)
        and re.fullmatch(r"[0-9a-f]{64}", str(analysis_context.get("snapshotId") or "")) is not None
        and analysis_context.get("snapshotArtifact")
        == ai_trade_council_snapshot_reference(
            str(analysis_context.get("snapshotId") or ""),
            str(analysis_context.get("snapshotArtifactDigest") or ""),
        )
        and analysis_context.get("readOnly") is True
    )
    if council_context_valid:
        hard_gate_reasons = _ai_trade_council_high_impact_reasons(tool_id, prompt)
    if hard_gate_reasons:
        risk = "high"
    raw_target_id = str(payload.get("targetId") or pick_target_for_task(prompt))
    target_id = canonical_specialist_target_id(
        agent_id,
        raw_target_id,
        payload.get("reportType"),
    )
    model_tier, budget = resolve_budget(
        payload,
        agent_id,
        tool_policy,
        allow_model_override=allow_model_override,
        allow_budget_override=allow_budget_override,
    )
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
    safe_workflow_context = _workflow_context_storage(workflow_context)
    if safe_workflow_context:
        mission["workflowContext"] = safe_workflow_context
        if safe_workflow_context.get("agentTransfer"):
            mission["agentTransfer"] = safe_workflow_context["agentTransfer"]
    if analysis_context:
        mission["analysisContext"] = sanitize_json_value(analysis_context)
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


def canonical_specialist_target_id(
    agent_id: str,
    target_id: object,
    report_type: object = None,
) -> str:
    """Keep legacy specialist rules away from repurposed dashboard surfaces."""
    candidate = str(target_id or "").strip()
    report_name = str(report_type or "").strip()
    if report_name == "risk_review" or (
        agent_id == "risk_guard" and candidate == "left_audit_crystals"
    ):
        return MISSION_STRATEGY_TABLE_PROP_ID
    if report_name == "auto_trading_status_report" or (
        agent_id == "vps_watch" and candidate == "left_signal_cube"
    ):
        return AI_TRADE_COUNCIL_PROP_ID
    if agent_id == "telegram_ops" and candidate == "right_tool_console":
        return MISSION_STRATEGY_TABLE_PROP_ID
    return candidate


def role_default_target_id(agent_id: str) -> str:
    fallback = {
        "manager": "mission_strategy_table",
        "ceo": "mission_strategy_table",
        "ea_developer": "terminal_workstation",
        "backtest_analyst": "left_analytics_console",
        "optimization_agent": "right_server_racks",
        "vps_watch": "right_status_crystals",
        "telegram_ops": "mission_strategy_table",
        "risk_guard": "mission_strategy_table",
        "codex_mcp_operator": "codex_mcp_portal",
        "mission_archivist": "left_server_racks",
    }.get(agent_id, "mission_strategy_table")
    return fallback if find_room_prop(fallback) else MISSION_STRATEGY_TABLE_PROP_ID


def allowed_targets_for_agent(agent_id: str) -> set[str]:
    rules = (load_orchestration_contract().get("managerAutoDelegation") or {}).get("specialistRules") or []
    targets = {
        canonical_specialist_target_id(
            agent_id,
            rule.get("targetPropId"),
            rule.get("reportType"),
        )
        for rule in rules
        if isinstance(rule, dict)
        and str(rule.get("agentId") or "") == agent_id
        and find_room_prop(canonical_specialist_target_id(
            agent_id,
            rule.get("targetPropId"),
            rule.get("reportType"),
        ))
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
        return canonical_specialist_target_id(
            agent_id,
            selected.get("targetPropId"),
            selected.get("reportType"),
        )
    return role_default_target_id(agent_id)


def goal_requires_web_research(goal: object) -> bool:
    text = str(goal or "").strip().lower()
    if not text:
        return False
    if re.search(r"https?://", text):
        return True
    web_tokens = (
        "web search",
        "search the web",
        "search online",
        "public website",
        "website",
        "browser",
        "internet",
        "online source",
        "external site",
        "latest news",
        "current news",
        "เว็บ",
        "เว็ป",
        "เว็บไซต์",
        "เว็บนอก",
        "อินเทอร์เน็ต",
        "ออนไลน์",
        "ค้นเว็บ",
        "ค้นจากเว็บ",
        "ตรวจสอบเว็บ",
        "เปิดเว็บ",
        "เปิดลิงก์",
        "ข่าวล่าสุด",
    )
    return any(token in text for token in web_tokens)


def goal_requires_metatrader_execution(goal: object) -> bool:
    text = re.sub(r"\s+", " ", str(goal or "").strip().lower())
    if not text:
        return False
    analysis_only_tokens = (
        "analyze report",
        "analyse report",
        "analyze screenshot",
        "analyse screenshot",
        "review report",
        "summarize report",
        "summary of report",
        "existing report",
        "วิเคราะห์รายงาน",
        "วิเคราะห์ screenshot",
        "วิเคราะห์ภาพ",
        "อ่านรายงาน",
        "สรุปรายงาน",
        "ตรวจรายงาน",
        "ตรวจภาพ",
        "วิเคราะห์ผล backtest",
        "วิเคราะห์ผล optimization",
    )
    explicit_followup_execution_tokens = (
        "then run",
        "then open",
        "then compile",
        "then backtest",
        "then optimize",
        "and run",
        "and open",
        "and compile",
        "and backtest",
        "and optimize",
        "please run",
        "run a new",
        "run new",
        "แล้วรัน",
        "แล้วเปิด",
        "แล้วคอมไพล์",
        "แล้วทดสอบ",
        "แล้ว backtest",
        "แล้ว optimize",
        "แล้วแบ็กเทสต์",
        "แล้วแบคเทสต์",
        "แล้วออปติไมซ์",
        "แล้วทำ backtest",
        "แล้วทํา backtest",
        "แล้วทำ optimization",
        "แล้วทํา optimization",
        "จากนั้นรัน",
        "จากนั้นเปิด",
        "จากนั้นคอมไพล์",
        "จากนั้นทดสอบ",
        "จากนั้นทำ backtest",
        "จากนั้นทํา backtest",
        "จากนั้นทำ optimization",
        "จากนั้นทํา optimization",
        "ต่อด้วยการรัน",
        "ต่อด้วยการเปิด",
        "ต่อด้วยการคอมไพล์",
        "ต่อด้วยการทดสอบ",
        "รันใหม่",
        "ทดสอบใหม่",
    )
    if (
        any(token in text for token in analysis_only_tokens)
        and not any(token in text for token in explicit_followup_execution_tokens)
    ):
        return False
    direct_execution_tokens = (
        "compile ea",
        "compile mq4",
        "compile mq5",
        "run mt4",
        "run mt5",
        "open mt4",
        "open mt5",
        "launch mt4",
        "launch mt5",
        "run backtest",
        "visual backtest",
        "backtest this ea",
        "run optimization",
        "optimize this ea",
        "เปิด mt4",
        "เปิด mt5",
        "รัน mt4",
        "รัน mt5",
        "เปิด metaeditor",
        "คอมไพล์",
        "รัน backtest",
        "ทำ backtest",
        "ทํา backtest",
        "ทดสอบย้อนหลัง ea",
        "รัน optimization",
        "ทำ optimization",
        "ทํา optimization",
    )
    if any(token in text for token in direct_execution_tokens):
        return True
    platform_or_ea_tokens = (
        "mt4",
        "mt5",
        "metatrader",
        "mq4",
        "mq5",
        " ea ",
        "ea ตัว",
        "discovery lab",
    )
    execution_action_tokens = (
        "backtest",
        "back test",
        "optimize",
        "optimization",
        "compile",
        "ทดสอบ ea",
        "ทดสอบย้อนหลัง",
        "แบ็กเทสต์",
        "แบคเทสต์",
        "ออปติไมซ์",
    )
    padded_text = f" {text} "
    return (
        any(token in padded_text for token in platform_or_ea_tokens)
        and any(token in text for token in execution_action_tokens)
    )


def tool_for_agent_goal(goal: object, default_tool_id: str = "codex_cli_task") -> str:
    if default_tool_id == "codex_cli_task" and goal_requires_metatrader_execution(goal):
        return "discovery_lab_mt4"
    if default_tool_id == "codex_cli_task" and goal_requires_web_research(goal):
        return "codex_web_research"
    return default_tool_id


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
            and canonical_specialist_target_id(
                requested_owner,
                rule.get("targetPropId"),
                rule.get("reportType"),
            ) == requested_target
        ), None)
        direct_rule = (
            {**matched_rule, "targetPropId": requested_target}
            if matched_rule
            else {
                "agentId": requested_owner,
                "targetPropId": requested_target,
                "reportType": report_type_for_prop(requested_target),
                "modelTier": role_default_model_tier(requested_owner),
            }
        )
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
            rule_agent_id = str(rule.get("agentId") or "manager")
            canonical_target_id = canonical_specialist_target_id(
                rule_agent_id,
                rule.get("targetPropId"),
                rule.get("reportType"),
            )
            key = (rule_agent_id, canonical_target_id, rule.get("reportType"))
            if key in seen:
                continue
            seen.add(key)
            matched_rules.append({**rule, "targetPropId": canonical_target_id})
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
        target_id = canonical_specialist_target_id(
            agent_id,
            rule.get("targetPropId") or "mission_strategy_table",
            rule.get("reportType"),
        )
        tool_id = tool_for_agent_goal(
            goal,
            str(rule.get("toolId") or default_subtask_tool_id),
        )
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
        capability_unavailable = tool_execution_capability_unavailable(tool_policy)
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
        }, status="blocked" if capability_unavailable else "queued", allow_model_override=True)
        if capability_unavailable:
            subtask = mark_mission_capability_unavailable(subtask, tool_policy)
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
    if tool_id not in {"codex_cli_task", "codex_web_research"}:
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
            "webSearchEnabled": tool_id == "codex_web_research",
        })
        runner_command = [
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
        ]
        if tool_id == "codex_web_research":
            runner_command.append("--web-search")
        runner = run_safe_command(
            runner_command,
            timeout=timeout_seconds + 30,
            output_limit=max(40000, output_limit + 10000),
            input_text=str(mission.get("detail") or ""),
        )
        try:
            result = json.loads(runner["output"]) if runner["output"] else {}
        except json.JSONDecodeError:
            result = {"ok": False, "status": "failed", "message": "Runner returned invalid JSON."}

        final_message = redact_text((result.get("finalMessage") or "").strip(), output_limit)
        work_status = str(result.get("workStatus") or result.get("status") or "failed")
        if result.get("ok") is True and work_status == "completed":
            mission_status = "completed"
        elif work_status in {"blocked", "waiting_input"}:
            mission_status = "blocked"
        else:
            mission_status = "failed"
        mission["status"] = mission_status
        mission["phase"] = f"manual_guarded_{work_status}"
        mission["workStatus"] = work_status
        mission["errorCode"] = None if mission_status == "completed" else str(
            result.get("status") or result.get("exitCode") or "runner_failed"
        )
        mission["result"] = final_message or redact_text(str(result.get("message") or "Runner did not return a report."), output_limit)
        mission["evidence"] = sanitize_json_value(
            result.get("evidence") if isinstance(result.get("evidence"), list) else []
        )
        mission["blockedCapability"] = redact_text(str(result.get("blockedCapability") or ""), 160)
        mission["webSearchUsed"] = bool(result.get("webSearchUsed", False))
        mission["webSearchEvidenceVerified"] = bool(
            result.get("webSearchEvidenceVerified", False)
        )
        mission["artifactPath"] = safe_codex_artifact_reference(
            (result.get("artifacts") if isinstance(result.get("artifacts"), dict) else {}).get("final")
        )
        mission["updatedAt"] = utc_now()
        mission["completedAt"] = mission["updatedAt"]
        report = create_report({
            "type": mission.get("reportType") or "bridge_status_report",
            "title": mission.get("title"),
            "summary": mission["result"],
            "ownerAgentId": agent_id,
            "linkedMissionId": mission_id,
            "linkedPropId": mission.get("targetId"),
            "status": "ready" if mission_status == "completed" else "blocked",
            "findings": result.get("findings") if isinstance(result.get("findings"), list) else [],
            "nextActions": result.get("nextSteps") if isinstance(result.get("nextSteps"), list) else [],
            "evidence": result.get("evidence") if isinstance(result.get("evidence"), list) else [],
            "artifacts": [mission["artifactPath"]] if mission.get("artifactPath") else [],
            "risks": [] if mission_status == "completed" else [mission.get("errorCode")],
            "workflowContext": mission.get("workflowContext"),
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
            "webSearchUsed": mission.get("webSearchUsed", False),
            "webSearchEvidenceVerified": mission.get(
                "webSearchEvidenceVerified",
                False,
            ),
        })
        return {
            "ok": mission_status == "completed",
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


def _is_ai_trade_council_vote_mission(mission: object) -> bool:
    if not isinstance(mission, dict):
        return False
    context = (
        mission.get("analysisContext")
        if isinstance(mission.get("analysisContext"), dict)
        else {}
    )
    agent_id = str(mission.get("owner") or "")
    return bool(
        context.get("kind") == "ai_trade_council_vote"
        and context.get("agentId") == agent_id
        and context.get("roleId") == AI_TRADE_COUNCIL_AGENT_ROLES.get(agent_id)
        and mission.get("toolId") == AI_TRADE_COUNCIL_ALLOWED_TOOLS.get(agent_id)
    )


def _council_vote_parent_state_error(
    mission: dict,
    missions: list[dict],
) -> str | None:
    if not _is_ai_trade_council_vote_mission(mission):
        return None
    parent_id = safe_reference(mission.get("parentMissionId"))
    if not parent_id:
        return "council_parent_missing"
    parent = next(
        (item for item in missions if item.get("id") == parent_id),
        None,
    )
    if not isinstance(parent, dict):
        return "council_parent_missing"
    parent_context = (
        parent.get("analysisContext")
        if isinstance(parent.get("analysisContext"), dict)
        else {}
    )
    child_context = (
        mission.get("analysisContext")
        if isinstance(mission.get("analysisContext"), dict)
        else {}
    )
    if parent_context.get("kind") != "ai_trade_council_parent":
        return "council_parent_invalid"
    if parent.get("status") not in {"queued", "running", "waiting_approval"}:
        return "council_parent_not_active"
    parent_snapshot_id = str(parent_context.get("snapshotId") or "")
    child_snapshot_id = str(child_context.get("snapshotId") or "")
    if (
        not re.fullmatch(r"[0-9a-f]{64}", parent_snapshot_id)
        or not secrets.compare_digest(parent_snapshot_id, child_snapshot_id)
    ):
        return "council_parent_snapshot_mismatch"
    children = [
        item
        for item in missions
        if item.get("parentMissionId") == parent_id
    ]
    if not _ai_trade_council_parent_queue_complete(parent, children):
        return (
            "council_parent_queue_incomplete"
            if _ai_trade_council_queue_assembly_is_stale(parent)
            else "council_parent_assembling"
        )
    return None


def find_next_auto_mission(*, council_only: bool | None = None) -> dict | None:
    with AI_TRADE_COUNCIL_QUEUE_LOCK:
        return _find_next_auto_mission_unlocked(council_only=council_only)


def _find_next_auto_mission_unlocked(
    *,
    council_only: bool | None = None,
) -> dict | None:
    if load_operator_mode_record().get("mode") != "auto_guarded":
        return None
    now = datetime.now(timezone.utc)
    candidates = []
    invalid: tuple[str, str] | None = None
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            explicitly_auto = (
                mission.get("status") == "queued"
                and mission.get("autoEligible") is True
                and mission.get("executionMode") == "auto_guarded"
            )
            if not explicitly_auto:
                continue
            is_council_vote = _is_ai_trade_council_vote_mission(mission)
            if council_only is True and not is_council_vote:
                continue
            if council_only is False and is_council_vote:
                continue
            parent_error = _council_vote_parent_state_error(mission, missions)
            if parent_error == "council_parent_assembling":
                continue
            if parent_error:
                invalid = (str(mission.get("id") or ""), parent_error)
                break
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
    with AI_TRADE_COUNCIL_QUEUE_LOCK:
        return _claim_auto_mission_unlocked(mission_id, worker_id)


def _claim_auto_mission_unlocked(
    mission_id: str,
    worker_id: str,
) -> dict | None:
    claimed = None
    parent_id = None
    invalid: tuple[str, str] | None = None
    with MISSIONS_LOCK:
        missions = load_missions()
        for mission in missions:
            if mission.get("id") != mission_id or mission.get("status") != "queued":
                continue
            parent_error = _council_vote_parent_state_error(mission, missions)
            if parent_error == "council_parent_assembling":
                break
            if parent_error:
                invalid = (mission_id, parent_error)
                break
            error = auto_execution_authorization_error(mission, require_operator_mode=True)
            if error:
                invalid = (mission_id, error)
                break
            execution = mission.get("execution") if isinstance(mission.get("execution"), dict) else {}
            if execution.get("dispatchState") not in {"queued", "deferred"}:
                invalid = (mission_id, "auto_dispatch_state_invalid")
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
    if invalid:
        block_auto_mission(*invalid)
        return None
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
        with MISSION_WORKER_PROCESS_LOCK:
            tracked = MISSION_WORKER_PROCESSES.get(mission_id)
            active_process = (
                tracked.get("process")
                if isinstance(tracked, dict)
                else None
            )
            active_job_holder = (
                tracked.get("jobHolder")
                if isinstance(tracked, dict)
                else None
            )
        if isinstance(active_process, subprocess.Popen):
            process_was_started = True
            if active_process.poll() is None:
                tree_terminated = _terminate_command_process_tree(
                    active_process,
                    active_job_holder if isinstance(active_job_holder, dict) else None,
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
                "workflowContext": failed.get("workflowContext"),
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
    work_status = str(result.get("workStatus") or result.get("status") or "failed")
    succeeded = result.get("ok") is True and work_status == "completed"
    analysis_context = (
        current.get("analysisContext")
        if isinstance(current.get("analysisContext"), dict)
        else {}
    )
    council_vote = None
    if analysis_context.get("kind") == "ai_trade_council_vote" and succeeded:
        council_vote = validate_ai_trade_council_vote_result(result, analysis_context)
        if council_vote is None:
            succeeded = False
            work_status = "invalid_council_output"
    mission_status = "completed" if succeeded else (
        "blocked" if work_status in {"blocked", "waiting_input"} else "failed"
    )
    if analysis_context.get("kind") == "ai_trade_council_vote" and council_vote is None and final_message:
        summary = (
            "ผลวิเคราะห์ไม่ผ่าน Output Schema หรือไม่ตรงกับ Snapshot และบทบาทที่กำหนด "
            "ระบบจึงไม่รวมผลนี้ในการลงมติ"
        )
    elif council_vote is not None:
        summary = json.dumps(council_vote, ensure_ascii=False, sort_keys=True)
    else:
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
        "status": "ready" if mission_status == "completed" else "blocked",
        "findings": (
            council_vote.get("observations")
            if council_vote is not None
            else (result.get("findings") if isinstance(result.get("findings"), list) else [])
        ),
        "metrics": (
            {
                "snapshotId": council_vote.get("snapshotId"),
                "roleId": council_vote.get("roleId"),
                "decision": council_vote.get("decision"),
                "confidence": council_vote.get("confidence"),
                "stopLossPrice": council_vote.get("stopLossPrice"),
                "takeProfitPrice": council_vote.get("takeProfitPrice"),
                "aiLotAllowed": False,
                "readOnly": True,
            }
            if council_vote is not None
            else {}
        ),
        "nextActions": result.get("nextSteps") if isinstance(result.get("nextSteps"), list) else [],
        "evidence": (
            council_vote.get("evidence")
            if council_vote is not None
            else (result.get("evidence") if isinstance(result.get("evidence"), list) else [])
        ),
        "artifacts": [artifact_path] if artifact_path else [],
        "risks": [] if succeeded else [str(result.get("status") or runner.get("exitCode") or "runner_failed")],
        "workflowContext": current.get("workflowContext"),
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
            mission["status"] = mission_status
            mission["phase"] = f"auto_guarded_{work_status}"
            mission["workStatus"] = work_status
            mission["errorCode"] = None if mission_status == "completed" else str(
                result.get("status") or runner.get("exitCode") or "runner_failed"
            )
            mission["result"] = summary
            if council_vote is not None:
                mission["councilVote"] = council_vote
            mission["evidence"] = sanitize_json_value(
                council_vote.get("evidence")
                if council_vote is not None
                else (result.get("evidence") if isinstance(result.get("evidence"), list) else [])
            )
            mission["blockedCapability"] = redact_text(
                str(result.get("blockedCapability") or ""),
                160,
            )
            mission["webSearchUsed"] = bool(result.get("webSearchUsed", False))
            mission["webSearchEvidenceVerified"] = bool(
                result.get("webSearchEvidenceVerified", False)
            )
            mission["artifactPath"] = artifact_path
            mission["reportIds"] = [report_id]
            mission["updatedAt"] = finished_at
            mission["heartbeatAt"] = finished_at
            mission["completedAt"] = finished_at
            execution["dispatchState"] = mission_status
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
            execution["webSearchEnabled"] = bool(
                result.get("webSearchEnabled", current.get("toolId") == "codex_web_research")
            )
            execution["webSearchMode"] = redact_text(
                str(result.get("webSearchMode") or "disabled"),
                40,
            )
            execution["webSearchUsed"] = bool(result.get("webSearchUsed", False))
            execution["webSearchEvidenceVerified"] = bool(
                result.get("webSearchEvidenceVerified", False)
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
                    or mission.get("status") not in {"completed", "blocked", "failed"}
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
        "webSearchUsed": execution.get("webSearchUsed", False),
        "webSearchEvidenceVerified": execution.get(
            "webSearchEvidenceVerified",
            False,
        ),
        "automaticRetry": False,
    })
    return finished


def _ai_trade_council_round_remaining_seconds(mission: dict) -> float | None:
    context = (
        mission.get("analysisContext")
        if isinstance(mission.get("analysisContext"), dict)
        else {}
    )
    if context.get("kind") != "ai_trade_council_vote":
        return None
    deadline = parse_iso(str(context.get("roundDeadlineAt") or ""))
    if deadline is None:
        return 0.0
    return (
        deadline.astimezone(timezone.utc) - datetime.now(timezone.utc)
    ).total_seconds()


def _expire_ai_trade_council_vote_mission(
    mission_id: str,
    reason_code: str = "council_round_deadline_expired",
) -> dict | None:
    mission = find_mission(mission_id)
    if not mission:
        return None
    context = (
        mission.get("analysisContext")
        if isinstance(mission.get("analysisContext"), dict)
        else {}
    )
    if context.get("kind") != "ai_trade_council_vote":
        return mission
    if mission.get("status") in {"completed", "failed", "blocked", "archived"}:
        return mission
    mission["status"] = "blocked"
    mission["phase"] = "council_round_expired"
    mission["workStatus"] = "blocked"
    mission["errorCode"] = reason_code
    mission["result"] = (
        "รอบวิเคราะห์สภา AI หมดเวลาก่อนเริ่มหรือก่อนจบ Agent จึงยกเลิกผลรอบนี้ "
        "และไม่ส่งคำสั่งไป MT4"
    )
    mission["completedAt"] = utc_now()
    mission["updatedAt"] = utc_now()
    execution = (
        mission.get("execution")
        if isinstance(mission.get("execution"), dict)
        else {}
    )
    mission["execution"] = {
        **execution,
        "processStarted": bool(execution.get("processStarted", False)),
        "automaticRetry": False,
        "roundExpired": True,
    }
    replace_mission(mission)
    append_audit({
        "type": "ai_trade_council.vote_cancelled",
        "missionId": mission_id,
        "parentMissionId": mission.get("parentMissionId"),
        "snapshotId": context.get("snapshotId"),
        "agentId": mission.get("owner"),
        "roleId": context.get("roleId"),
        "roundDeadlineAt": context.get("roundDeadlineAt"),
        "reason": reason_code,
        "terminalActions": False,
    })
    refresh_parent_mission(safe_reference(mission.get("parentMissionId")))
    return mission


def _defer_auto_mission_with_round_deadline(
    mission: dict,
    reason: str,
    retry_after_seconds: int,
) -> dict | None:
    """Never leave a Council card blue when its next attempt cannot finish."""
    remaining = _ai_trade_council_round_remaining_seconds(mission)
    retry_after_seconds = max(1, min(3600, int(retry_after_seconds)))
    budget = mission.get("budget") if isinstance(mission.get("budget"), dict) else {}
    timeout_seconds = clamp_int(budget.get("timeoutSeconds"), 120, 15, 600)
    # run_safe_command may legitimately use timeout + 30 seconds while it
    # terminates the process tree. Keep another five seconds for validation,
    # parent reconciliation, and guarded command publication.
    reserve_seconds = timeout_seconds + 35
    if remaining is not None and (
        remaining <= reserve_seconds
        or retry_after_seconds >= max(1, int(remaining) - reserve_seconds)
    ):
        if reason in {"quota_unavailable_or_stale", "codex_limit_reached"}:
            reason_code = "council_quota_backoff_exceeds_round_deadline"
        elif reason == "local_rate_limited":
            reason_code = "council_rate_limit_exceeds_round_deadline"
        else:
            reason_code = "council_runner_backoff_exceeds_round_deadline"
        return _expire_ai_trade_council_vote_mission(
            str(mission.get("id") or ""),
            reason_code,
        )
    return defer_auto_mission(
        str(mission.get("id") or ""),
        reason,
        retry_after_seconds,
    )


def process_auto_mission(worker_id: str, mission: dict) -> None:
    mission_id = str(mission.get("id") or "")
    agent_id = str(mission.get("owner") or "manager")
    tool_id = str(mission.get("toolId") or "")
    config = mission_worker_config()
    round_remaining = _ai_trade_council_round_remaining_seconds(mission)
    is_council_candidate = _is_ai_trade_council_vote_mission(mission)
    budget = mission.get("budget") if isinstance(mission.get("budget"), dict) else {}
    round_completion_reserve = (
        clamp_int(budget.get("timeoutSeconds"), 120, 15, 600) + 35
        if is_council_candidate
        else 0
    )
    run_semaphore = (
        AI_TRADE_COUNCIL_RUN_SEMAPHORE
        if is_council_candidate
        else REAL_RUN_SEMAPHORE
    )
    if (
        round_remaining is not None
        and round_remaining <= round_completion_reserve
    ):
        _expire_ai_trade_council_vote_mission(
            mission_id,
            "council_round_deadline_insufficient",
        )
        return
    if not CODEX_RUNNER_PYTHON.is_file() or not CODEX_RUNNER_SCRIPT.is_file():
        _defer_auto_mission_with_round_deadline(
            mission,
            "runner_missing",
            config["runnerUnavailableBackoffSeconds"],
        )
        return
    status_snapshot = bridge_status()
    if status_snapshot.get("codex", {}).get("status") not in {"ready", "ready_guarded"}:
        _defer_auto_mission_with_round_deadline(
            mission,
            str(status_snapshot.get("codex", {}).get("status") or "runner_not_ready"),
            config["runnerUnavailableBackoffSeconds"],
        )
        return
    quota = codex_rate_limits()
    if quota.get("ok") is not True or quota.get("stale") is True:
        _defer_auto_mission_with_round_deadline(
            mission,
            "quota_unavailable_or_stale",
            config["quotaBackoffSeconds"],
        )
        return
    if quota.get("limitReached") is True:
        _defer_auto_mission_with_round_deadline(
            mission,
            "codex_limit_reached",
            config["quotaBackoffSeconds"],
        )
        return
    tier_id = str(mission.get("modelTier") or role_default_model_tier(agent_id))
    tier = (load_orchestration_contract().get("modelTiers") or {}).get(tier_id) or {}
    max_runs = clamp_int(tier.get("maxRunsPerHour"), 12, 1, 200)
    rate_key = f"real:{agent_id}:{tool_id}:{tier_id}"
    allowed, retry_after = check_rate_limit(rate_key, max_runs, consume=False)
    if not allowed:
        _defer_auto_mission_with_round_deadline(
            mission,
            "local_rate_limited",
            retry_after,
        )
        return
    if not run_semaphore.acquire(blocking=False):
        _defer_auto_mission_with_round_deadline(
            mission,
            "runner_busy",
            config["busyBackoffSeconds"],
        )
        return
    try:
        allowed, retry_after = check_rate_limit(rate_key, max_runs, consume=True)
        if not allowed:
            _defer_auto_mission_with_round_deadline(
                mission,
                "local_rate_limited",
                retry_after,
            )
            return
        claimed = claim_auto_mission(mission_id, worker_id)
        if not claimed:
            return
        execution = claimed.get("execution") if isinstance(claimed.get("execution"), dict) else {}
        lease_id = str(execution.get("leaseId") or "")
        budget = claimed.get("budget") if isinstance(claimed.get("budget"), dict) else {}
        timeout_seconds = clamp_int(budget.get("timeoutSeconds"), 120, 15, 600)
        output_limit = clamp_int(budget.get("outputLimitChars"), 7000, 1000, 20000)
        analysis_context = (
            claimed.get("analysisContext")
            if isinstance(claimed.get("analysisContext"), dict)
            else {}
        )
        council_snapshot_id = str(analysis_context.get("snapshotId") or "")
        council_snapshot_digest = str(
            analysis_context.get("snapshotArtifactDigest") or ""
        )
        council_role_id = str(analysis_context.get("roleId") or "")
        is_council_vote = (
            analysis_context.get("kind") == "ai_trade_council_vote"
            and analysis_context.get("agentId") == agent_id
            and council_role_id == AI_TRADE_COUNCIL_AGENT_ROLES.get(agent_id)
            and tool_id == AI_TRADE_COUNCIL_ALLOWED_TOOLS.get(agent_id)
            and analysis_context.get("snapshotArtifact")
            == ai_trade_council_snapshot_reference(
                council_snapshot_id,
                council_snapshot_digest,
            )
            and analysis_context.get("readOnly") is True
        )
        if is_council_vote:
            round_remaining = _ai_trade_council_round_remaining_seconds(claimed)
            # Reserve time for process shutdown, JSON validation, parent synthesis,
            # and deterministic dispatch gating before the shared round deadline.
            if round_remaining is None or round_remaining <= 50:
                _expire_ai_trade_council_vote_mission(
                    mission_id,
                    "council_round_deadline_insufficient",
                )
                return
            timeout_seconds = min(
                timeout_seconds,
                max(15, int(round_remaining) - 35),
            )
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
            "requestedSandbox": "read-only" if is_council_vote else "workspace-write",
            "workingDirectory": "workspace",
            "writeRoots": [] if is_council_vote else ["workspace", "frontend", "docs", "assets-source"],
            "controlPlaneWritable": False,
            "webSearchEnabled": tool_id == "codex_web_research",
            "webSearchMode": "live" if tool_id == "codex_web_research" else "disabled",
            "concurrencyGroup": (
                "ai_trade_council_parallel_3"
                if is_council_vote
                else "general_serial_1"
            ),
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
            runner_command = [
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
            ]
            if tool_id == "codex_web_research":
                runner_command.append("--web-search")
            if is_council_vote:
                runner_command.extend([
                    "--result-mode",
                    "ai_trade_council_vote",
                    "--council-snapshot-id",
                    council_snapshot_id,
                    "--council-snapshot-digest",
                    council_snapshot_digest,
                    "--council-role-id",
                    council_role_id,
                ])
            runner = run_safe_command(
                runner_command,
                timeout=timeout_seconds + 30,
                output_limit=max(40000, output_limit + 10000),
                input_text=str(claimed.get("detail") or ""),
                kill_process_tree_on_timeout=True,
                cancel_event=MISSION_WORKER_STOP,
                tracking_key=mission_id,
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
        run_semaphore.release()


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
            mission = find_next_auto_mission(council_only=False)
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


def ai_trade_council_worker_loop(worker_id: str) -> None:
    """Run only Council votes; three instances form the bounded parallel round pool."""
    config = mission_worker_config()
    while not MISSION_WORKER_STOP.is_set():
        try:
            if load_operator_mode_record().get("mode") != "auto_guarded":
                MISSION_WORKER_WAKE.wait(config["idlePollSeconds"])
                MISSION_WORKER_WAKE.clear()
                continue
            mission = find_next_auto_mission(council_only=True)
            if mission:
                process_auto_mission(worker_id, mission)
                continue
            MISSION_WORKER_WAKE.wait(config["idlePollSeconds"])
            MISSION_WORKER_WAKE.clear()
        except DataIntegrityError:
            MISSION_WORKER_WAKE.wait(config["runnerUnavailableBackoffSeconds"])
            MISSION_WORKER_WAKE.clear()
        except Exception:
            append_audit({
                "type": "ai_trade_council.worker_error",
                "workerId": worker_id,
                "automaticRetry": False,
            })
            MISSION_WORKER_WAKE.wait(config["runnerUnavailableBackoffSeconds"])
            MISSION_WORKER_WAKE.clear()


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
    global MISSION_WORKER_THREAD, MISSION_WORKER_WATCHDOG_THREAD, AI_TRADE_COUNCIL_WORKER_THREADS
    with MISSION_WORKER_LOCK:
        if MISSION_WORKER_THREAD and MISSION_WORKER_THREAD.is_alive():
            if not MISSION_WORKER_WATCHDOG_THREAD or not MISSION_WORKER_WATCHDOG_THREAD.is_alive():
                MISSION_WORKER_WATCHDOG_THREAD = threading.Thread(
                    target=mission_timeout_watchdog_loop,
                    name="metafx-mission-timeout-watchdog",
                    daemon=False,
                )
                MISSION_WORKER_WATCHDOG_THREAD.start()
            active_council_workers = [
                thread
                for thread in AI_TRADE_COUNCIL_WORKER_THREADS
                if thread.is_alive()
            ]
            while len(active_council_workers) < 3:
                worker_index = len(active_council_workers) + 1
                thread = threading.Thread(
                    target=ai_trade_council_worker_loop,
                    args=(safe_id(None, f"council-worker-{worker_index}"),),
                    name=f"metafx-council-worker-{worker_index}",
                    daemon=False,
                )
                thread.start()
                active_council_workers.append(thread)
            AI_TRADE_COUNCIL_WORKER_THREADS = active_council_workers
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
        AI_TRADE_COUNCIL_WORKER_THREADS = [
            threading.Thread(
                target=ai_trade_council_worker_loop,
                args=(safe_id(None, f"council-worker-{index}"),),
                name=f"metafx-council-worker-{index}",
                daemon=False,
            )
            for index in range(1, 4)
        ]
        MISSION_WORKER_WATCHDOG_THREAD.start()
        MISSION_WORKER_THREAD.start()
        for thread in AI_TRADE_COUNCIL_WORKER_THREADS:
            thread.start()
        append_audit({
            "type": "ai_trade_council.parallel_workers_started",
            "workerCount": 3,
            "concurrencyLimit": 3,
            "generalMissionConcurrencyLimit": 1,
        })
        return MISSION_WORKER_THREAD


def stop_mission_worker() -> None:
    MISSION_WORKER_STOP.set()
    MISSION_WORKER_WAKE.set()
    forced_tree_termination = None
    tracked_processes: list[tuple[str, object, object]] = []
    with MISSION_WORKER_PROCESS_LOCK:
        tracked_processes = [
            (mission_id, record.get("process"), record.get("jobHolder"))
            for mission_id, record in MISSION_WORKER_PROCESSES.items()
            if isinstance(record, dict)
        ]
        if not tracked_processes and MISSION_WORKER_PROCESS is not None:
            tracked_processes = [
                (
                    str(MISSION_WORKER_STATE.get("currentMissionId") or "unknown"),
                    MISSION_WORKER_PROCESS,
                    MISSION_WORKER_JOB_HOLDER,
                )
            ]
    terminated_by_mission = {}
    for mission_id, active_process, job_holder in tracked_processes:
        if isinstance(active_process, subprocess.Popen) and active_process.poll() is None:
            terminated_by_mission[mission_id] = _terminate_command_process_tree(
                active_process,
                job_holder if isinstance(job_holder, dict) else None,
            )
    if terminated_by_mission:
        forced_tree_termination = all(terminated_by_mission.values())
    if forced_tree_termination is not None:
        append_audit({
            "type": "mission.worker_shutdown_cancel",
            "missionIds": list(terminated_by_mission),
            "processTreeTerminated": forced_tree_termination,
            "automaticRetry": False,
        })
    worker = MISSION_WORKER_THREAD
    if worker and worker.is_alive():
        worker.join(timeout=30)
    watchdog = MISSION_WORKER_WATCHDOG_THREAD
    if watchdog and watchdog.is_alive():
        watchdog.join(timeout=15)
    for council_worker in list(AI_TRADE_COUNCIL_WORKER_THREADS):
        if council_worker.is_alive():
            council_worker.join(timeout=30)
    if not worker or not worker.is_alive():
        update_mission_worker_state(status="stopped", currentMissionId=None, heartbeatAt=utc_now())
    else:
        update_mission_worker_state(status="stopping", lastError="worker_shutdown_timeout", heartbeatAt=utc_now())
        append_audit({
            "type": "mission.worker_shutdown_timeout",
            "missionId": mission_worker_read_model().get("currentMissionId"),
            "processTreeTerminated": forced_tree_termination,
        })


def run_bridge_task(
    payload: dict,
    *,
    trusted_workflow_context: dict | None = None,
) -> dict:
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

    if tool_execution_capability_unavailable(tool_policy):
        adapter_status = str(tool_policy.get("adapterStatus") or "adapter_missing")
        append_audit({
            "type": "adapter.capability_unavailable",
            "agentId": agent_id,
            "toolId": tool_id,
            "adapterStatus": adapter_status,
            "approvalRequested": False,
            "missionCreated": False,
            "realToolExecuted": False,
        })
        return {
            "ok": False,
            "kind": "capability_unavailable",
            "messageTh": (
                f"{tool_id} ยังไม่มี Adapter สำหรับงานจริง ({adapter_status}) "
                "จึงไม่สร้างงานรออนุมัติและยังไม่มี Tool ใดทำงาน"
            ),
            "message": "Capability unavailable; no approval mission was created and no tool executed.",
            "_httpStatus": 501,
        }

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
    }, status="queued", workflow_context=trusted_workflow_context)
    status = bridge_status()
    if mission.get("approval", {}).get("required"):
        if (
            mission.get("autoEligible") is True
            and mission.get("executionMode") == "auto_guarded"
            and mission.get("requiresHumanApproval") is False
            and mission.get("approval", {}).get("state") == "approved"
            and mission.get("status") in {"queued", "running"}
        ):
            MISSION_WORKER_WAKE.set()
            append_audit({
                "type": "bridge.mission_auto_queued",
                "missionId": mission["id"],
                "agentId": agent_id,
                "toolId": tool_id,
            })
            return {
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": mission,
                "targetId": mission["targetId"],
                "bridge": status,
                "message": "Backend approved this guarded mission and queued it for automatic execution.",
                "_httpStatus": 202,
            }
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
    task_tool_id = tool_for_agent_goal(risk_context)
    high_impact_reasons = _high_impact_reasons(task_tool_id, risk_context, "medium")
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
        permission = evaluate_tool_permission(agent_id, task_tool_id)
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
        capability_unavailable = tool_execution_capability_unavailable(tool_policy)
        mission = create_mission({
            "title": f"{agent_id}: {task_goal[:96]}",
            "prompt": task_goal,
            "agentId": agent_id,
            "requester": agent_id,
            "toolId": task_tool_id,
            "targetId": target_id,
            "risk": "high" if high_impact_reasons else (tool_policy.get("risk") or "medium"),
            "modelTier": role_default_model_tier(agent_id),
            "reportType": report_type_for_prop(target_id),
            "idempotencyKey": task_key,
        }, status="blocked" if capability_unavailable else "queued")
        if capability_unavailable:
            mission = mark_mission_capability_unavailable(mission, tool_policy)
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
        runner_request = _agent_chat_runner_request_payload(
            message,
            history,
            agent_id,
        )
        council_chat_context = (
            runner_request.get("councilContext")
            if isinstance(runner_request.get("councilContext"), dict)
            else {}
        )
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
            "councilContextStatus": (
                council_chat_context.get("status")
                if council_chat_context
                else "not_applicable"
            ),
            "councilSnapshotPrefix": (
                council_chat_context.get("snapshotIdPrefix")
                if council_chat_context.get("status") == "available"
                else None
            ),
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
            input_text=json.dumps(runner_request, ensure_ascii=False),
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


def update_collaboration_runtime_state(**values: object) -> None:
    with COLLABORATION_STATE_LOCK:
        COLLABORATION_STATE.update(values)


def _collaboration_agent_name(agent_id: str) -> str:
    agent = next((item for item in load_agent_contracts() if item.get("id") == agent_id), None)
    return redact_text(str((agent or {}).get("name") or agent_id), 120)


def _collaboration_report_context(target_prop_id: str, limit: int = 2) -> str:
    rows = []
    for report in load_runtime_reports(limit=80):
        if report.get("linkedPropId") not in {target_prop_id, MISSION_STRATEGY_TABLE_PROP_ID}:
            continue
        title = redact_text(str(report.get("title") or "รายงาน"), 140)
        summary = redact_text(str(report.get("summary") or ""), 400).strip()
        if summary:
            rows.append(f"- {title}: {summary}")
        if len(rows) >= limit:
            break
    return "\n".join(rows) if rows else "- ยังไม่มีรายงานล่าสุดที่เกี่ยวข้อง ใช้หัวข้อประชุมเป็นกรอบหลัก"


def _collaboration_speakers(config: dict, daily_run_count: int) -> list[str]:
    participants = [
        item
        for item in config.get("participants", [])
        if item in EXPECTED_AGENT_IDS
    ]
    specialists = [item for item in participants if item != "manager"]
    max_turns = clamp_int(config.get("maxTurns"), 3, 2, 4)
    contributor_count = max(1, max_turns - 1)
    if specialists:
        offset = daily_run_count % len(specialists)
        specialists = specialists[offset:] + specialists[:offset]
    selected = specialists[:contributor_count]
    return [*selected, "manager"][:max_turns]


def _run_collaboration_agent_turn(
    *,
    meeting_id: str,
    mission_id: str,
    speaker_agent_id: str,
    topic: str,
    context: str,
    prior_turns: list[dict],
    turn_number: int,
    final_turn: bool,
    timeout_seconds: int,
    output_limit: int,
) -> dict:
    previous = "\n".join(
        f"- {_collaboration_agent_name(str(item.get('speakerAgentId') or 'agent'))}: "
        f"{redact_text(str(item.get('message') or ''), 450)}"
        for item in prior_turns[-2:]
    ) or "- ยังไม่มีข้อเสนอจาก Agent คนก่อนหน้า"
    if final_turn:
        instruction = (
            "คุณเป็น Manager Agent รอบสุดท้าย กรุณาสรุปข้อเสนอที่ใช้ได้จริง ตัดสิ่งที่ซ้ำหรือเสี่ยงออก "
            "และระบุสิ่งที่ควรทำต่อโดยยังไม่สร้าง Task หรือเรียก Tool"
        )
        model_tier = "manager_quality"
    else:
        instruction = (
            "เสนอหนึ่งแนวทางที่เพิ่มคุณภาพผลลัพธ์ พร้อมเหตุผล ข้อควรระวัง "
            "และวิธีตรวจว่าดีขึ้นจริง โดยไม่สร้าง Task หรือเรียก Tool"
        )
        model_tier = "specialist_fast"
    message = redact_text(f"""หัวข้อ: {topic}

บริบทจากรายงานใน HQ:
{context}

ข้อเสนอจากรอบก่อนหน้า:
{previous}

หน้าที่ในรอบที่ {turn_number}:
{instruction}
""", 3800)
    append_audit({
        "type": "collaboration.turn_start",
        "meetingId": meeting_id,
        "missionId": mission_id,
        "speakerAgentId": speaker_agent_id,
        "turnNumber": turn_number,
        "modelTier": model_tier,
        "timeoutSeconds": timeout_seconds,
        "outputLimitChars": output_limit,
        "toolsEnabled": False,
    })
    runner = run_safe_command(
        [
            str(CODEX_RUNNER_PYTHON),
            str(CODEX_RUNNER_SCRIPT),
            "--collaboration-turn",
            "--collaboration-request-stdin",
            "--agent-id",
            speaker_agent_id,
            "--session-id",
            meeting_id,
            "--timeout",
            str(timeout_seconds),
            "--model-tier",
            model_tier,
            "--output-limit",
            str(output_limit),
        ],
        timeout=timeout_seconds + 45,
        output_limit=max(16000, output_limit * 5),
        input_text=json.dumps({"message": message, "history": []}, ensure_ascii=False),
        kill_process_tree_on_timeout=True,
        cancel_event=COLLABORATION_SCHEDULER_STOP,
    )
    try:
        result = json.loads(runner.get("output") or "{}")
    except json.JSONDecodeError:
        result = {
            "ok": False,
            "status": "invalid_runner_output",
            "message": "Codex ส่งผลประชุมที่ตรวจสอบรูปแบบไม่ได้",
        }
    result = result if isinstance(result, dict) else {}
    guardrails = result.get("guardrails") if isinstance(result.get("guardrails"), dict) else {}
    guarded = (
        result.get("ok") is True
        and result.get("kind") == "agent_collaboration_turn"
        and guardrails.get("toolsEnabled") is False
        and guardrails.get("computerUseEnabled") is False
        and guardrails.get("projectWorkspaceExposed") is False
        and guardrails.get("taskCreationEnabled") is False
        and result.get("taskCreationEnabled") is False
    )
    reply = redact_text(str(result.get("finalMessage") or "").strip(), output_limit)
    if not guarded or not reply:
        status_name = redact_text(str(result.get("status") or "guard_validation_failed"), 60)
        append_audit({
            "type": "collaboration.turn_end",
            "meetingId": meeting_id,
            "missionId": mission_id,
            "speakerAgentId": speaker_agent_id,
            "turnNumber": turn_number,
            "status": status_name,
            "durationMs": result.get("durationMs", runner.get("durationMs")),
            "outputChars": 0,
            "quotaAttempted": bool(result.get("quotaAttempted", False)),
            "quotaConsumptionStatus": result.get("quotaConsumption") or "unknown",
            "processTreeTerminated": bool(
                result.get("processTreeTerminated", runner.get("processTreeTerminated", False))
            ),
            "toolsExecuted": False,
            "taskCreated": False,
        })
        return {
            "ok": False,
            "status": status_name,
            "message": redact_text(str(result.get("message") or "Agent ส่งผลประชุมไม่ผ่าน Guard"), 800),
            "durationMs": result.get("durationMs", runner.get("durationMs")),
            "quotaAttempted": bool(result.get("quotaAttempted", False)),
            "quotaConsumption": result.get("quotaConsumption") or "unknown",
            "processTreeTerminated": bool(
                result.get("processTreeTerminated", runner.get("processTreeTerminated", False))
            ),
        }
    append_audit({
        "type": "collaboration.turn_end",
        "meetingId": meeting_id,
        "missionId": mission_id,
        "speakerAgentId": speaker_agent_id,
        "turnNumber": turn_number,
        "status": "completed",
        "durationMs": result.get("durationMs", runner.get("durationMs")),
        "outputChars": len(reply),
        "modelTier": model_tier,
        "quotaConsumptionStatus": result.get("quotaConsumption"),
        "toolsExecuted": False,
        "taskCreated": False,
    })
    return {
        "ok": True,
        "status": "completed",
        "message": reply,
        "durationMs": result.get("durationMs", runner.get("durationMs")),
        "modelTier": model_tier,
    }


def _record_collaboration_session_failure(
    *,
    trigger: str,
    meeting_id: str,
    mission: dict | None,
    turns: list[dict],
    failure_reason: str,
) -> None:
    if mission:
        mission["status"] = "failed"
        mission["phase"] = "agent_collaboration_failed"
        mission["workStatus"] = "failed"
        mission["errorCode"] = failure_reason
        mission["result"] = "การประชุม Agent หยุดแบบปลอดภัยเพราะ Backend พบข้อผิดพลาดภายใน"
        mission["updatedAt"] = utc_now()
        mission["completedAt"] = mission["updatedAt"]
        try:
            replace_mission(mission)
        except (DataIntegrityError, OSError):
            pass
    try:
        append_audit({
            "type": "collaboration.session_end",
            "meetingId": meeting_id,
            "missionId": (mission or {}).get("id"),
            "trigger": trigger,
            "status": "failed",
            "reason": failure_reason,
            "turnCount": len(turns),
            "toolsExecuted": False,
            "taskCreated": False,
        })
    except (DataIntegrityError, OSError):
        pass
    try:
        _update_collaboration_store_state(
            lastCompletedAt=utc_now(),
            lastStatus="failed",
            lastReason=failure_reason,
            lastMissionId=(mission or {}).get("id"),
        )
    except (DataIntegrityError, OSError):
        pass


def _block_collaboration_mission_before_start(
    *,
    trigger: str,
    mission: dict,
    failure_reason: str,
    summary: str,
) -> dict:
    report = create_report({
        "type": "collaboration_report",
        "title": "การประชุม Agent ยังไม่เริ่ม",
        "summary": summary,
        "ownerAgentId": "manager",
        "linkedMissionId": mission["id"],
        "linkedPropId": MISSION_STRATEGY_TABLE_PROP_ID,
        "status": "blocked",
        "findings": [],
        "nextActions": ["รอให้งาน Codex ปัจจุบันจบ หรือตรวจ Full Access และ Rate Limit แล้วจึงเริ่มใหม่"],
        "risks": [failure_reason],
        "metrics": {
            "turnCount": 0,
            "toolsExecuted": False,
            "followupTaskCreated": False,
        },
    })
    completed_at = utc_now()
    mission["status"] = "blocked"
    mission["phase"] = "agent_collaboration_not_started"
    mission["workStatus"] = "blocked"
    mission["errorCode"] = failure_reason
    mission["result"] = summary
    mission["reportIds"] = [report["id"]]
    mission["updatedAt"] = completed_at
    mission["completedAt"] = completed_at
    replace_mission(mission)
    _update_collaboration_store_state(
        lastRunAt=completed_at,
        lastCompletedAt=completed_at,
        lastStatus="blocked",
        lastReason=failure_reason,
        lastMissionId=mission["id"],
    )
    append_audit({
        "type": "collaboration.session_end",
        "meetingId": None,
        "missionId": mission["id"],
        "reportId": report["id"],
        "trigger": trigger,
        "status": "blocked",
        "reason": failure_reason,
        "turnCount": 0,
        "toolsExecuted": False,
        "taskCreated": False,
    })
    return report


def _complete_collaboration_session(trigger: str, store: dict, mission: dict) -> None:
    global COLLABORATION_SESSION_THREAD
    semaphore_acquired = False
    meeting_id = safe_id(None, "meeting")
    report: dict | None = None
    turns: list[dict] = []
    failure_reason = None
    try:
        if COLLABORATION_SCHEDULER_STOP.is_set():
            failure_reason = "bridge_shutdown"
            _block_collaboration_mission_before_start(
                trigger=trigger,
                mission=mission,
                failure_reason=failure_reason,
                summary="ยกเลิกการประชุมก่อนเริ่ม เพราะ Local Bridge กำลังปิด",
            )
            return
        if not REAL_RUN_SEMAPHORE.acquire(blocking=False):
            failure_reason = "runner_busy"
            _block_collaboration_mission_before_start(
                trigger=trigger,
                mission=mission,
                failure_reason=failure_reason,
                summary="ยังไม่เริ่มการประชุม เพราะ Codex Runner กำลังทำ Mission อื่นอยู่",
            )
            update_collaboration_runtime_state(
                status="paused",
                heartbeatAt=utc_now(),
                lastError=failure_reason,
            )
            append_audit({
                "type": "collaboration.session_paused",
                "trigger": trigger,
                "reason": failure_reason,
                "toolsExecuted": False,
            })
            return
        semaphore_acquired = True
        config = store["config"]
        topic = str(config.get("topic") or "").strip()
        if contains_potential_secret(topic):
            failure_reason = "potential_secret"
            _block_collaboration_mission_before_start(
                trigger=trigger,
                mission=mission,
                failure_reason=failure_reason,
                summary="ยังไม่เริ่มการประชุม เพราะหัวข้อมีข้อมูลที่อาจเป็นความลับ",
            )
            return
        started_at = utc_now()
        claim_failure = None
        with COLLABORATION_STATE_LOCK:
            with MISSIONS_LOCK:
                missions = load_missions()
                mission_index = next(
                    (index for index, item in enumerate(missions) if item.get("id") == mission.get("id")),
                    None,
                )
                current_mission = missions[mission_index] if mission_index is not None else None
                if not isinstance(current_mission, dict) or current_mission.get("status") != "queued":
                    claim_failure = "mission_not_queued"
                elif COLLABORATION_SCHEDULER_STOP.is_set():
                    claim_failure = "bridge_shutdown"
                else:
                    current_mission["status"] = "running"
                    current_mission["phase"] = "agent_collaboration_running"
                    current_mission["workStatus"] = "running"
                    current_mission["startedAt"] = started_at
                    current_mission["heartbeatAt"] = started_at
                    current_mission["updatedAt"] = started_at
                    missions[mission_index] = current_mission
                    save_missions(missions)
                    mission.clear()
                    mission.update(current_mission)
        if claim_failure == "bridge_shutdown":
            failure_reason = claim_failure
            _block_collaboration_mission_before_start(
                trigger=trigger,
                mission=mission,
                failure_reason=failure_reason,
                summary="ยกเลิกการประชุมก่อนเริ่ม เพราะ Local Bridge กำลังปิด",
            )
            update_collaboration_runtime_state(
                status="stopping",
                heartbeatAt=utc_now(),
                lastError=failure_reason,
            )
            return
        if claim_failure:
            failure_reason = claim_failure
            update_collaboration_runtime_state(
                status="paused",
                heartbeatAt=utc_now(),
                lastError=failure_reason,
            )
            append_audit({
                "type": "collaboration.session_rejected",
                "trigger": trigger,
                "missionId": mission.get("id"),
                "reason": failure_reason,
                "toolsExecuted": False,
            })
            return

        def begin_run(current_store: dict) -> dict:
            current_store, _ = _rollover_collaboration_daily_state(current_store)
            state = current_store["state"]
            state["dailyRunDate"] = _collaboration_day_key()
            state["dailyRunCount"] = clamp_int(state.get("dailyRunCount"), 0, 0, 1000) + 1
            state["lastRunAt"] = started_at
            state["lastStatus"] = "running"
            state["lastReason"] = None
            state["lastMeetingId"] = meeting_id
            state["lastMissionId"] = mission["id"]
            current_store["state"] = state
            return current_store

        store = _mutate_collaboration_schedule_store(begin_run)
        state = store["state"]
        update_collaboration_runtime_state(
            status="running",
            activeMeetingId=meeting_id,
            activeMissionId=mission["id"],
            startedAt=utc_now(),
            heartbeatAt=utc_now(),
            lastError=None,
        )
        speakers = _collaboration_speakers(config, state["dailyRunCount"] - 1)
        context = _collaboration_report_context(MISSION_STRATEGY_TABLE_PROP_ID)
        append_meeting_record({
            "id": meeting_id,
            "title": "Agent ร่วมประชุมพัฒนา Product",
            "agenda": topic,
            "participants": speakers,
            "summary": "เริ่มการประชุมผ่าน Codex แบบปิด Tool",
            "messages": [],
            "source": "backend.collaboration_scheduler",
            "simulation": False,
            "status": "running",
            "trigger": trigger,
            "linkedMissionId": mission["id"],
            "linkedPropId": MISSION_STRATEGY_TABLE_PROP_ID,
        }, "meeting.start")
        append_audit({
            "type": "collaboration.session_start",
            "meetingId": meeting_id,
            "missionId": mission["id"],
            "trigger": trigger,
            "participants": speakers,
            "maxTurns": config.get("maxTurns"),
            "dailyRunCount": state.get("dailyRunCount"),
            "toolsEnabled": False,
            "autoCreateFollowup": False,
        })
        guard = load_orchestration_contract().get("costRateGuard") or {}
        hourly_turn_cap = clamp_int(guard.get("collaborationTurnsPerHour"), 12, 2, 40)
        timeout_seconds = clamp_int(config.get("perTurnTimeoutSeconds"), 90, 30, 120)
        output_limit = clamp_int(config.get("perTurnOutputChars"), 1800, 800, 3000)
        for index, speaker_agent_id in enumerate(speakers, start=1):
            if COLLABORATION_SCHEDULER_STOP.is_set():
                failure_reason = "scheduler_stopping"
                break
            if load_operator_mode_record().get("mode") != "auto_guarded":
                failure_reason = "full_access_revoked"
                break
            quota_gate = _collaboration_quota_gate(config, refresh=True)
            if not quota_gate.get("allowed"):
                failure_reason = str(quota_gate.get("reason") or "quota_guard")
                break
            allowed, _ = check_rate_limit(
                "agent-collaboration:global",
                hourly_turn_cap,
                0,
                consume=True,
            )
            if not allowed:
                failure_reason = "hourly_turn_cap"
                break
            heartbeat_at = utc_now()
            update_collaboration_runtime_state(heartbeatAt=heartbeat_at)
            mission["heartbeatAt"] = heartbeat_at
            mission["updatedAt"] = heartbeat_at
            replace_mission(mission)
            turn = _run_collaboration_agent_turn(
                meeting_id=meeting_id,
                mission_id=mission["id"],
                speaker_agent_id=speaker_agent_id,
                topic=topic,
                context=context,
                prior_turns=turns,
                turn_number=index,
                final_turn=index == len(speakers),
                timeout_seconds=timeout_seconds,
                output_limit=output_limit,
            )
            invalidate_codex_rate_limit_cache()
            if turn.get("ok") is not True:
                failure_reason = str(turn.get("status") or "turn_failed")
                break
            turn_record = {
                "speakerAgentId": speaker_agent_id,
                "speakerName": _collaboration_agent_name(speaker_agent_id),
                "message": turn["message"],
                "intent": "decision" if index == len(speakers) else "proposal",
                "turnNumber": index,
                "createdAt": utc_now(),
            }
            turns.append(turn_record)
            append_meeting_record({
                "id": f"{meeting_id}-turn-{index}",
                "title": f"รอบที่ {index}: {_collaboration_agent_name(speaker_agent_id)}",
                "agenda": topic,
                "participants": speakers,
                "summary": turn["message"],
                "messages": [turn_record],
                "source": "backend.collaboration_scheduler",
                "simulation": False,
                "status": "completed",
                "trigger": trigger,
                "linkedMissionId": mission["id"],
                "linkedPropId": MISSION_STRATEGY_TABLE_PROP_ID,
            }, "meeting.turn")
        manager_turn = next(
            (item for item in reversed(turns) if item.get("speakerAgentId") == "manager"),
            None,
        )
        completed = bool(manager_turn) and not failure_reason
        summary = (
            str(manager_turn.get("message") or "")
            if manager_turn
            else (
                f"การประชุมหยุดไว้ก่อน: {failure_reason or 'ยังสรุปผลไม่ครบ'}"
            )
        )
        meeting_status = "completed" if completed else "blocked"
        decisions = [str(manager_turn.get("message") or "")] if manager_turn else []
        next_actions = (
            ["เปิดรายงานการประชุมที่โต๊ะ Mission เพื่อพิจารณาก่อนสร้าง Task จริง"]
            if completed
            else ["ตรวจ Rate Limit หรือสถานะ Codex Runner แล้วจึงเริ่มประชุมรอบใหม่"]
        )
        append_meeting_record({
            "id": meeting_id,
            "title": "สรุปการประชุม Agent เพื่อพัฒนา Product",
            "agenda": topic,
            "participants": speakers,
            "summary": summary,
            "messages": turns,
            "decisions": decisions,
            "nextActions": next_actions,
            "source": "backend.collaboration_scheduler",
            "simulation": False,
            "status": meeting_status,
            "trigger": trigger,
            "linkedMissionId": mission["id"],
            "linkedPropId": MISSION_STRATEGY_TABLE_PROP_ID,
        }, "meeting")
        report = create_report({
            "type": "collaboration_report",
            "title": "ผลการประชุม Agent เพื่อพัฒนา Product",
            "summary": summary,
            "ownerAgentId": "manager",
            "linkedMissionId": mission["id"],
            "linkedPropId": MISSION_STRATEGY_TABLE_PROP_ID,
            "status": "ready" if completed else "blocked",
            "findings": [
                f"{item.get('speakerName')}: {item.get('message')}"
                for item in turns
                if item.get("speakerAgentId") != "manager"
            ],
            "nextActions": next_actions,
            "risks": [] if completed else [failure_reason or "meeting_incomplete"],
            "metrics": {
                "turnCount": len(turns),
                "plannedTurnCount": len(speakers),
                "dailyRunCount": state.get("dailyRunCount"),
                "toolsExecuted": False,
                "followupTaskCreated": False,
            },
        })
        mission["status"] = "completed" if completed else "blocked"
        mission["phase"] = "agent_collaboration_completed" if completed else "agent_collaboration_blocked"
        mission["workStatus"] = mission["status"]
        mission["result"] = summary
        mission["reportIds"] = [report["id"]]
        mission["updatedAt"] = utc_now()
        mission["completedAt"] = mission["updatedAt"]
        mission["errorCode"] = None if completed else (failure_reason or "meeting_incomplete")
        replace_mission(mission)
        _update_collaboration_store_state(
            lastCompletedAt=mission["completedAt"],
            lastStatus=mission["status"],
            lastReason=mission.get("errorCode"),
            lastMissionId=mission["id"],
            lastMeetingId=meeting_id,
        )
        append_audit({
            "type": "collaboration.session_end",
            "meetingId": meeting_id,
            "missionId": mission["id"],
            "reportId": report["id"],
            "trigger": trigger,
            "status": mission["status"],
            "reason": mission.get("errorCode"),
            "turnCount": len(turns),
            "toolsExecuted": False,
            "taskCreated": False,
            "followupTaskCreated": False,
        })
    except DataIntegrityError:
        failure_reason = failure_reason or "data_integrity_error"
        _record_collaboration_session_failure(
            trigger=trigger,
            meeting_id=meeting_id,
            mission=mission,
            turns=turns,
            failure_reason=failure_reason,
        )
    except Exception:
        failure_reason = failure_reason or "internal_error"
        _record_collaboration_session_failure(
            trigger=trigger,
            meeting_id=meeting_id,
            mission=mission,
            turns=turns,
            failure_reason=failure_reason,
        )
    finally:
        update_collaboration_runtime_state(
            status="stopped" if COLLABORATION_SCHEDULER_STOP.is_set() else "idle",
            activeMeetingId=None,
            activeMissionId=None,
            heartbeatAt=utc_now(),
            lastError=failure_reason,
        )
        if semaphore_acquired:
            REAL_RUN_SEMAPHORE.release()
        with COLLABORATION_STATE_LOCK:
            if COLLABORATION_SESSION_THREAD is threading.current_thread():
                COLLABORATION_SESSION_THREAD = None
        COLLABORATION_RUN_LOCK.release()
        COLLABORATION_SCHEDULER_WAKE.set()


def queue_collaboration_session(trigger: str = "manual") -> dict:
    global COLLABORATION_SESSION_THREAD
    normalized_trigger = "schedule" if trigger == "schedule" else "manual"
    if COLLABORATION_SCHEDULER_STOP.is_set():
        return {
            "ok": False,
            "kind": "collaboration_stopping",
            "messageTh": "ระบบกำลังปิด จึงไม่รับการประชุม Agent รอบใหม่",
            "collaboration": collaboration_schedule_read_model(),
            "_httpStatus": 503,
        }
    if not COLLABORATION_RUN_LOCK.acquire(blocking=False):
        return {
            "ok": False,
            "kind": "collaboration_busy",
            "messageTh": "Agent กำลังประชุมกันอยู่",
            "collaboration": collaboration_schedule_read_model(),
            "_httpStatus": 409,
        }
    worker_started = False
    try:
        store, gate = _collaboration_gate(
            normalized_trigger,
            refresh_quota=True,
        )
        if not gate.get("allowed"):
            append_audit({
                "type": "collaboration.session_rejected",
                "trigger": normalized_trigger,
                "reason": gate.get("reason"),
                "toolsExecuted": False,
            })
            return {
                "ok": False,
                "kind": str(gate.get("reason") or "collaboration_paused"),
                "messageTh": gate.get("messageTh"),
                "collaboration": collaboration_schedule_read_model(),
                "_httpStatus": 429 if str(gate.get("reason") or "").startswith("quota") else 409,
            }
        if COLLABORATION_SCHEDULER_STOP.is_set():
            return {
                "ok": False,
                "kind": "collaboration_stopping",
                "messageTh": "ระบบกำลังปิด จึงยกเลิกการเริ่มประชุม Agent รอบใหม่",
                "collaboration": collaboration_schedule_read_model(),
                "_httpStatus": 503,
            }
        topic = str(store["config"].get("topic") or "").strip()
        mission = create_mission({
            "title": f"Agent ร่วมประชุม: {topic[:88]}",
            "prompt": topic,
            "agentId": "manager",
            "requester": "manager",
            "toolId": "agent_collaboration",
            "targetId": MISSION_STRATEGY_TABLE_PROP_ID,
            "risk": "low",
            "modelTier": "manager_quality",
            "reportType": "collaboration_report",
            "idempotencyKey": f"collab-{payload_digest(normalized_trigger, topic, utc_now())[:32]}",
        }, status="queued")
        mission["phase"] = "agent_collaboration_queued"
        mission["workStatus"] = "queued"
        mission["result"] = "Backend รับคำขอแล้วและกำลังตรวจคิว Codex Runner"
        mission["updatedAt"] = utc_now()
        replace_mission(mission)
        update_collaboration_runtime_state(
            status="starting",
            activeMeetingId=None,
            activeMissionId=mission["id"],
            startedAt=utc_now(),
            heartbeatAt=utc_now(),
            lastError=None,
        )
        worker = threading.Thread(
            target=_complete_collaboration_session,
            args=(normalized_trigger, store, mission),
            name=f"metafx-agent-collaboration-{normalized_trigger}",
            daemon=True,
        )
        rejected_for_shutdown = False
        start_error = None
        with COLLABORATION_STATE_LOCK:
            if COLLABORATION_SCHEDULER_STOP.is_set():
                rejected_for_shutdown = True
            else:
                COLLABORATION_SESSION_THREAD = worker
                try:
                    worker.start()
                    worker_started = True
                except Exception as error:
                    start_error = error
                    COLLABORATION_SESSION_THREAD = None
        if rejected_for_shutdown:
            _block_collaboration_mission_before_start(
                trigger=normalized_trigger,
                mission=mission,
                failure_reason="bridge_shutdown",
                summary="ยกเลิกการประชุมก่อนเริ่ม เพราะ Local Bridge กำลังปิด",
            )
            update_collaboration_runtime_state(
                status="stopping",
                activeMeetingId=None,
                activeMissionId=None,
                heartbeatAt=utc_now(),
                lastError="bridge_shutdown",
            )
            return {
                "ok": False,
                "kind": "collaboration_stopping",
                "messageTh": "ระบบกำลังปิด จึงยกเลิกการเริ่มประชุม Agent รอบใหม่",
                "collaboration": collaboration_schedule_read_model(),
                "_httpStatus": 503,
            }
        if start_error is not None:
            with COLLABORATION_STATE_LOCK:
                COLLABORATION_SESSION_THREAD = None
            _record_collaboration_session_failure(
                trigger=normalized_trigger,
                meeting_id="",
                mission=mission,
                turns=[],
                failure_reason="session_thread_start_failed",
            )
            raise start_error
        return {
            "ok": True,
            "kind": "collaboration_queued",
            "messageTh": "รับคำขอแล้ว Agent จะเริ่มประชุมผ่าน Codex และส่งสรุปกลับโต๊ะ Mission",
            "mission": mission_read_model_item(mission),
            "collaboration": collaboration_schedule_read_model(),
            "_httpStatus": 202,
        }
    finally:
        if not worker_started and COLLABORATION_RUN_LOCK.locked():
            COLLABORATION_RUN_LOCK.release()


def collaboration_scheduler_loop() -> None:
    update_collaboration_runtime_state(
        status="idle",
        startedAt=utc_now(),
        heartbeatAt=utc_now(),
        lastError=None,
    )
    last_pause_reason = None
    while not COLLABORATION_SCHEDULER_STOP.is_set():
        try:
            store = load_collaboration_schedule_store()
            config = store["config"]
            if config.get("enabled"):
                _, gate = _collaboration_gate("schedule", refresh_quota=True)
                reason = None if gate.get("allowed") else str(gate.get("reason") or "paused")
                if gate.get("allowed") and not COLLABORATION_SCHEDULER_STOP.is_set():
                    queue_collaboration_session("schedule")
                    last_pause_reason = None
                elif reason != last_pause_reason:
                    append_audit({
                        "type": "collaboration.scheduler_paused",
                        "reason": reason,
                        "toolsExecuted": False,
                    })
                    last_pause_reason = reason
            else:
                last_pause_reason = "disabled"
            update_collaboration_runtime_state(heartbeatAt=utc_now())
        except DataIntegrityError:
            update_collaboration_runtime_state(status="blocked", lastError="data_integrity_error", heartbeatAt=utc_now())
        except Exception:
            update_collaboration_runtime_state(status="degraded", lastError="scheduler_loop_error", heartbeatAt=utc_now())
        COLLABORATION_SCHEDULER_WAKE.wait(60)
        COLLABORATION_SCHEDULER_WAKE.clear()
    update_collaboration_runtime_state(status="stopped", heartbeatAt=utc_now())


def start_collaboration_scheduler() -> threading.Thread:
    global COLLABORATION_SCHEDULER_THREAD
    with COLLABORATION_STATE_LOCK:
        if COLLABORATION_SCHEDULER_THREAD and COLLABORATION_SCHEDULER_THREAD.is_alive():
            return COLLABORATION_SCHEDULER_THREAD
        COLLABORATION_SCHEDULER_STOP.clear()
        COLLABORATION_SCHEDULER_THREAD = threading.Thread(
            target=collaboration_scheduler_loop,
            name="metafx-agent-collaboration-scheduler",
            daemon=True,
        )
        COLLABORATION_SCHEDULER_THREAD.start()
        return COLLABORATION_SCHEDULER_THREAD


def stop_collaboration_scheduler() -> None:
    with COLLABORATION_STATE_LOCK:
        COLLABORATION_SCHEDULER_STOP.set()
        COLLABORATION_SCHEDULER_WAKE.set()
    thread = COLLABORATION_SCHEDULER_THREAD
    if thread and thread.is_alive():
        thread.join(timeout=25)
    with COLLABORATION_STATE_LOCK:
        session_thread = COLLABORATION_SESSION_THREAD
    if session_thread and session_thread.is_alive():
        session_thread.join(timeout=8)
    update_collaboration_runtime_state(
        status="stopping" if session_thread and session_thread.is_alive() else "stopped",
        heartbeatAt=utc_now(),
    )


def archive_mission(mission_id: str) -> dict:
    with PARENT_MISSION_REFRESH_LOCK:
        with MISSIONS_LOCK:
            missions = load_missions()
            mission_index = next(
                (index for index, item in enumerate(missions) if item.get("id") == mission_id),
                None,
            )
            if mission_index is None:
                return {"ok": False, "kind": "not_found", "message": "Mission not found.", "_httpStatus": 404}
            mission = missions[mission_index]
            active_statuses = {"queued", "running", "waiting_approval"}
            has_active_children = any(
                item.get("parentMissionId") == mission_id
                and item.get("status") in active_statuses
                for item in missions
            )
            if mission.get("status") in active_statuses or has_active_children:
                return {"ok": False, "kind": "mission_active", "message": "Queued, active, approval-pending missions, and parents with active subtasks cannot be archived.", "_httpStatus": 409}
            archived_from_status = str(mission.get("status") or "unknown")
            mission["archivedFromStatus"] = archived_from_status
            mission["archivedSuccessful"] = archived_from_status == "completed"
            mission["status"] = "archived"
            mission["updatedAt"] = utc_now()
            missions[mission_index] = mission
            save_missions(missions)
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

    def send_report_attachment(self, report_id: str, attachment_id: str) -> None:
        resolved = resolve_report_attachment(report_id, attachment_id)
        if not resolved:
            raise RequestError("Unknown report attachment.", 404)
        path, media_type = resolved
        try:
            byte_size = path.stat().st_size
            handle = path.open("rb")
        except OSError as error:
            raise RequestError("Report attachment is unavailable.", 404) from error
        with handle:
            self.send_response(200)
            self.send_header("Content-Type", media_type)
            self.send_header("Content-Length", str(byte_size))
            self.send_header("Content-Disposition", f'inline; filename="report-evidence{path.suffix.lower()}"')
            self.end_headers()
            shutil.copyfileobj(handle, self.wfile, length=64 * 1024)

    def send_report_download(self, report_id: str, artifact_id: str) -> None:
        resolved = resolve_report_download(report_id, artifact_id)
        if not resolved:
            raise RequestError("Unknown or disallowed report download.", 404)
        path, media_type = resolved
        try:
            byte_size = path.stat().st_size
            handle = path.open("rb")
        except OSError as error:
            raise RequestError("Report download is unavailable.", 404) from error
        append_audit({
            "type": "report.artifact_downloaded",
            "reportId": report_id,
            "artifactId": artifact_id,
            "byteSize": byte_size,
            "filesystemPathExposed": False,
        })
        with handle:
            self.send_response(200)
            self.send_header("Content-Type", media_type)
            self.send_header("Content-Length", str(byte_size))
            self.send_header("Content-Disposition", f'attachment; filename="source-output{path.suffix.lower()}"')
            self.end_headers()
            shutil.copyfileobj(handle, self.wfile, length=64 * 1024)

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
        except Exception as error:
            request_id = safe_id(None, "request")
            try:
                append_audit({
                    "type": "bridge.request_failed",
                    "requestId": request_id,
                    "path": urlparse(self.path).path,
                    "errorType": type(error).__name__,
                    "errorMessage": redact_text(str(error), 240),
                })
            except Exception:
                pass
            self.send_json({
                "ok": False,
                "kind": "internal_guarded_bridge_error",
                "error": "Local Runner เกิดข้อผิดพลาดภายใน กรุณาลองใหม่อีกครั้ง หากยังเกิดซ้ำให้ตรวจ Bridge Log ด้วย Request ID นี้",
                "messageTh": "Local Runner เกิดข้อผิดพลาดภายใน กรุณาลองใหม่อีกครั้ง หากยังเกิดซ้ำให้ตรวจ Bridge Log ด้วย Request ID นี้",
                "requestId": request_id,
            }, status=500)

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
        except Exception as error:
            request_id = safe_id(None, "request")
            try:
                append_audit({
                    "type": "bridge.request_failed",
                    "requestId": request_id,
                    "path": urlparse(self.path).path,
                    "errorType": type(error).__name__,
                    "errorMessage": redact_text(str(error), 240),
                })
            except Exception:
                pass
            self.send_json({
                "ok": False,
                "kind": "internal_guarded_bridge_error",
                "error": "Local Runner เกิดข้อผิดพลาดภายใน กรุณาลองใหม่อีกครั้ง หากยังเกิดซ้ำให้ตรวจ Bridge Log ด้วย Request ID นี้",
                "messageTh": "Local Runner เกิดข้อผิดพลาดภายใน กรุณาลองใหม่อีกครั้ง หากยังเกิดซ้ำให้ตรวจ Bridge Log ด้วย Request ID นี้",
                "requestId": request_id,
            }, status=500)

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
        report_attachment_match = re.fullmatch(r"/api/reports/([^/]+)/attachments/([^/]+)", path)
        if report_attachment_match:
            report_id = unquote(report_attachment_match.group(1))
            attachment_id = unquote(report_attachment_match.group(2))
            self.send_report_attachment(report_id, attachment_id)
            return
        report_download_match = re.fullmatch(r"/api/reports/([^/]+)/downloads/([^/]+)", path)
        if report_download_match:
            report_id = unquote(report_download_match.group(1))
            artifact_id = unquote(report_download_match.group(2))
            self.send_report_download(report_id, artifact_id)
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
            self.send_json(memory_index_read_model())
            return
        if path == "/api/memory/search":
            search_text = query.get("q", [""])[0]
            self.send_json({
                "query": redact_text(str(search_text), 300),
                "items": [
                    memory_read_model_item(item)
                    for item in search_memory_items(search_text)
                ],
                "updatedAt": utc_now(),
                "readModel": "memory_search_frontend_v1",
            })
            return
        if path == "/api/meetings":
            self.send_json({"meetings": load_meeting_records(), "updatedAt": utc_now()})
            return
        if path == "/api/collaboration/schedule":
            self.send_json(collaboration_schedule_read_model())
            return
        if path == "/api/integrations/metatrader/snapshot":
            prop_id = str(query.get("propId", [AI_TRADE_COUNCIL_PROP_ID])[0]).strip()
            if not SAFE_ID_PATTERN.fullmatch(prop_id) or prop_id not in METATRADER_TARGET_PROP_IDS:
                raise RequestError("Unknown dashboard id.", 404)
            self.send_json({
                "ok": True,
                "metatraderReadOnly": metatrader_snapshot_read_model(prop_id),
                "updatedAt": utc_now(),
            })
            return
        if path == "/api/mt4-trade-gateway/status":
            self.send_json({
                "ok": True,
                "tradeGateway": mt4_trade_gateway_status_read_model(),
                "updatedAt": utc_now(),
            })
            return
        if path == "/api/mt4-trade-gateway/outcome":
            command_id = str(query.get("commandId", [""])[0]).strip()
            self.send_result(mt4_trade_gateway_outcome_read_model(command_id))
            return
        if path == "/api/ai-trade-council/status":
            self.send_json({
                "ok": True,
                "aiTradeCouncil": ai_trade_council_status_read_model(),
                "updatedAt": utc_now(),
            })
            return
        if path == "/api/ai-trade-council/deep-analysis":
            self.send_json({
                "ok": True,
                **ai_trade_council_deep_analysis_read_model(),
            })
            return
        if path == "/api/ai-trade-council/automation":
            self.send_json({
                "ok": True,
                "automation": ai_trade_council_automation_read_model(),
                "updatedAt": utc_now(),
            })
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
            if path == "/api/collaboration/schedule":
                self.send_result(set_collaboration_schedule(payload))
                return
            if path == "/api/collaboration/run-now":
                if payload:
                    self.send_result({
                        "ok": False,
                        "kind": "invalid_collaboration_run_request",
                        "messageTh": "คำสั่งประชุมตอนนี้ไม่รับข้อมูลเพิ่มเติม",
                        "_httpStatus": 422,
                    })
                else:
                    self.send_result(queue_collaboration_session("manual"))
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
                self.send_json(store_ui_session(session))
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
                self.send_json({"ok": True, "item": memory_read_model_item(item)})
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
            workflow_action = re.fullmatch(r"/api/props/([^/]+)/workflow/actions", path)
            if workflow_action:
                prop_id = unquote(workflow_action.group(1))
                if not SAFE_ID_PATTERN.fullmatch(prop_id):
                    raise RequestError("Invalid dashboard id.", 422)
                self.send_result(run_dashboard_workflow_action(prop_id, payload))
                return
            workflow_transfer = re.fullmatch(r"/api/props/([^/]+)/workflow/transfers", path)
            if workflow_transfer:
                prop_id = unquote(workflow_transfer.group(1))
                if not SAFE_ID_PATTERN.fullmatch(prop_id):
                    raise RequestError("Invalid destination dashboard id.", 422)
                self.send_result(deliver_dashboard_report(prop_id, payload))
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
            if path == "/api/ai-trade-council/automation":
                self.send_result(set_ai_trade_council_automation(payload))
                return
            if path == "/api/ai-trade-council/analyze":
                self.send_result(run_ai_trade_council_analysis(payload))
                return
            if path == "/api/ai-trade-council/deep-analysis/package":
                self.send_result(
                    create_ai_trade_council_deep_analysis_package(payload)
                )
                return
            if path == "/api/mt4-trade-gateway/execution-unknown/quarantine":
                self.send_result(quarantine_mt4_execution_unknown(payload))
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
        except Exception as error:
            request_id = safe_id(None, "request")
            try:
                append_audit({
                    "type": "bridge.request_failed",
                    "requestId": request_id,
                    "path": urlparse(self.path).path,
                    "errorType": type(error).__name__,
                    "errorMessage": redact_text(str(error), 240),
                })
            except Exception:
                pass
            self.send_json({
                "ok": False,
                "kind": "internal_guarded_bridge_error",
                "error": "Local Runner เกิดข้อผิดพลาดภายใน กรุณาลองใหม่อีกครั้ง หากยังเกิดซ้ำให้ตรวจ Bridge Log ด้วย Request ID นี้",
                "messageTh": "Local Runner เกิดข้อผิดพลาดภายใน กรุณาลองใหม่อีกครั้ง หากยังเกิดซ้ำให้ตรวจ Bridge Log ด้วย Request ID นี้",
                "requestId": request_id,
            }, status=500)

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
    ensure_collaboration_schedule_store()
    ensure_ai_trade_council_automation_store()
    reconciled_approval_count = reconcile_stale_approval_missions()
    recovered_count = recover_interrupted_missions()
    recovered_collaboration_count = recover_interrupted_collaboration_missions()
    reconciled_parent_count = reconcile_parent_mission_statuses()
    httpd = BridgeHTTPServer((args.host, args.port), BridgeHandler)
    actual_port = int(httpd.server_port)
    try:
        start_mission_worker()
        start_collaboration_scheduler()
        start_ai_trade_council_automation_scheduler()
        append_audit({
            "type": "bridge.server_start",
            "host": args.host,
            "port": actual_port,
            "operatorMode": load_operator_mode_record().get("mode"),
            "reconciledApprovalMissions": reconciled_approval_count,
            "recoveredInterruptedMissions": recovered_count,
            "recoveredInterruptedCollaborationMissions": recovered_collaboration_count,
            "reconciledParentMissions": reconciled_parent_count,
            "missionWorker": mission_worker_read_model(),
            "collaboration": collaboration_schedule_read_model(),
            "aiTradeCouncilAutomation": ai_trade_council_automation_read_model(),
        })
        print(f"Metafx Local Bridge running at http://{args.host}:{actual_port}/", flush=True)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        stop_ai_trade_council_automation_scheduler()
        stop_collaboration_scheduler()
        stop_mission_worker()
        append_audit({"type": "bridge.server_stop", "host": args.host, "port": actual_port})
    return 0


if __name__ == "__main__":
    sys.exit(main())
