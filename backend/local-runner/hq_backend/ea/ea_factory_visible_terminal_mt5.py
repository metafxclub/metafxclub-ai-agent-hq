from __future__ import annotations

"""Fail-closed visible MT5 MetaEditor/Strategy Tester adapter.

This module is deliberately standalone so it can be wired into ``bridge_server``
without changing the established MT4 adapter.  The bridge owns terminal
selection and passes a backend-created immutable request.  Browser input never
chooses an executable or a data directory.

Safety invariants:

* only ``terminal64.exe`` + ``MetaEditor64.exe`` + the matching ``MQL5`` tree;
* only ``.mq5`` sources and ``.ex5`` compiled experts;
* no terminal launch/close, chart attachment, Algo Trading toggle, or live trade;
* a tester Start click is preceded by an exclusive durable start-boundary;
* a retry after that boundary is collection-only and cannot click Start again;
* success requires persisted screenshots, an exact exported MT5 report, and a
  durable receipt whose evidence digests are rechecked on recovery.

The accompanying PowerShell helper performs visible UI Automation.  Where an
MT5 build/localisation does not expose an exact control or report flow, it fails
closed rather than guessing coordinates or manufacturing evidence.
"""

import copy
import hashlib
import html as html_lib
import json
import math
import os
import re
import secrets
import stat
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Mapping
from xml.etree import ElementTree

try:  # Bridge imports the guarded adapters from the EA package.
    from hq_backend.ea.ea_factory_visible_terminal import (  # type: ignore
        VisibleTerminalAdapterError as _Mt4VisibleTerminalAdapterError,
    )
except ModuleNotFoundError:  # Direct spec loading in isolated unit tests.
    _Mt4VisibleTerminalAdapterError = RuntimeError


REQUEST_SCHEMA = "ea-factory-visible-front-office-request-v1"
RESULT_SCHEMA = "ea-factory-visible-front-office-result-v1"
POWERSHELL_REQUEST_SCHEMA = "ea-factory-visible-powershell-request-v1"
POWERSHELL_RESULT_SCHEMA = "ea-factory-visible-powershell-result-v1"
PROCESS_BINDING_SCHEMA = "ea-factory-front-office-process-binding-v1"
RECEIPT_SCHEMA = "ea-factory-visible-front-office-receipt-v1"
ACTION_INTENT_SCHEMA = "ea-factory-visible-front-office-action-intent-v1"
ACTION_REQUEST_SCHEMA = "ea-factory-visible-mt5-action-request-v1"
START_BOUNDARY_SCHEMA = "ea-factory-tester-start-boundary-v1"
RESOLVED_TESTER_SCHEMA = "ea-factory-resolved-tester-settings-v1"
TESTER_SETTINGS_SCHEMA = "ea-factory-tester-settings-v1"
OPTIMIZATION_INTENT_SCHEMA = "ea-factory-mt5-optimization-intent-v1"
INPUT_MANIFEST_SCHEMA = "ea-factory-mt5-input-manifest-v1"
SET_REF_SCHEMA = "ea-factory-mt5-set-ref-v1"
COMPILED_DEPLOYMENT_SCHEMA = "ea-factory-mt5-compiled-deployment-v1"
TESTER_INPUT_PRESET_SCHEMA = "ea-factory-tester-input-preset-v1"
RESOLVED_TESTER_INPUT_PRESET_SCHEMA = "ea-factory-resolved-tester-input-preset-v1"
EXPERT_CATALOG_REFRESH_SCHEMA = "ea-factory-mt5-expert-catalog-refresh-v2"
TESTER_COMPLETION_EVIDENCE_SCHEMA = "ea-factory-mt5-tester-completion-evidence-v2"
STRATEGY_EXECUTION_PROFILE_SCHEMA = "ea-factory-strategy-execution-profile-v1"
STRATEGY_EXECUTION_PROOF_SCHEMA = "ea-factory-strategy-execution-proof-v1"
CERTIFIED_EMA_SMOKE_PROFILE_ID = "custom-ema-10-60-closed-bar-smoke-mt5-v3"
EXPERT_CATALOG_REFRESH_BOUNDARY_SCHEMA = (
    "ea-factory-mt5-expert-catalog-refresh-boundary-v1"
)
OPTIMIZATION_COMPLETION_CHECKPOINT_SCHEMA = (
    "ea-factory-mt5-optimization-completion-checkpoint-v1"
)
SYMBOL_UNIVERSE_SCHEMA = "ea-factory-mt5-symbol-universe-v1"
EVIDENCE_MODE = "visible_front_office_v1"

MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_BINARY_BYTES = 64 * 1024 * 1024
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024
MAX_OPTIMIZATION_XML_BYTES = 512 * 1024 * 1024
MAX_OPTIMIZATION_RESULT_ROWS = 100_000
MAX_OPTIMIZATION_PREVIEW_ROWS = 5_000
MAX_OPTIMIZATION_RESULT_COLUMNS = 96
MAX_OPTIMIZATION_CELL_CHARS = 512
MAX_SET_BYTES = 1024 * 1024
MAX_OPTIMIZATION_CACHE_BYTES = 64 * 1024 * 1024
DEFAULT_UI_TIMEOUT_SECONDS = 180
DEFAULT_TESTER_TIMEOUT_SECONDS = 2 * 60 * 60
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
SAFE_OPERATION_ID = re.compile(r"ea-visible-[a-f0-9]{24}\Z")
SAFE_SYMBOL = re.compile(r"[A-Za-z0-9._#-]{1,40}\Z")
SAFE_INPUT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}\Z")
TESTER_SIMULATION_NAME_PATTERN = re.compile(
    r"(?:Fundamental|External|Eligibility|Screen|Criteria)", re.IGNORECASE
)
TESTER_SIMULATION_FORBIDDEN_NAME_PATTERN = re.compile(
    r"(?:EnableTrading|TradingEnabled|AllowTrading|LiveTrading|AutoTrading|Safety)",
    re.IGNORECASE,
)
MT5_INPUT_INTEGER_TYPES = frozenset({
    "char", "uchar", "short", "ushort", "int", "uint", "long", "ulong",
})
MT5_INPUT_DECIMAL_TYPES = frozenset({"float", "double"})
MT5_INPUT_MANIFEST_MAX_COUNT = 80
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ZERO_COMPILE_RESULT = re.compile(
    r"(?:Result:\s*)?0\s+errors?,\s*0\s+warnings?"
    r"(?:,\s*[0-9]+\s+ms\s+elapsed,\s*cpu='[A-Za-z0-9 +_.-]{1,80}')?\Z",
    re.I,
)
ALLOWED_PERIODS = frozenset(
    {"M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30", "H1", "H2", "H3", "H4", "H6", "H8", "H12", "D1", "W1", "MN1"}
)
ALLOWED_MODELS = frozenset(
    {"every_tick", "every_tick_real_ticks", "one_minute_ohlc", "open_prices", "math_calculations"}
)
REQUIRED_TESTER_AUTOMATION_IDS = {
    "testerPane": "32846",
    "expert": "10485",
    "symbol": "10486",
    "timeframe": "10487",
    "deposit": "10489",
    "useDate": "10123",
    "fromDate": "10550",
    "toDate": "10551",
    "modelling": "10515",
    "optimization": "10491",
    "forward": "10492",
    "visualMode": "10490",
    "criterion": "10507",
    "start": "16790",
    "tabs": "10002",
}
# MT5 creates the optimization criterion control only after optimization is
# enabled, while its visual-mode checkbox is present only for a single
# backtest.  Keep the shared Settings controls separate, then bind the exact
# stage-specific native control.  Optimization still sends the criterion id
# separately so the native adapter can bind and prove it only after enabling
# optimization, before Start.
BASE_TESTER_AUTOMATION_IDS = {
    key: value
    for key, value in REQUIRED_TESTER_AUTOMATION_IDS.items()
    if key not in {"criterion", "visualMode"}
}
BACKTEST_TESTER_AUTOMATION_IDS = {
    **BASE_TESTER_AUTOMATION_IDS,
    "visualMode": REQUIRED_TESTER_AUTOMATION_IDS["visualMode"],
}
OPTIMIZATION_TESTER_AUTOMATION_IDS = dict(BASE_TESTER_AUTOMATION_IDS)


class VisibleTerminalAdapterError(_Mt4VisibleTerminalAdapterError):
    """Path-free public failure code used by the bridge boundary."""

    def __init__(self, code: str, *, retryable: bool = False) -> None:
        if _Mt4VisibleTerminalAdapterError is RuntimeError:
            RuntimeError.__init__(self, str(code))
        else:
            _Mt4VisibleTerminalAdapterError.__init__(
                self, str(code), retryable=retryable
            )
        self.code = str(code)
        self.retryable = bool(retryable)

    def public_details(self) -> dict:
        return {"reasonCode": self.code, "retryable": self.retryable}


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(value: object) -> str:
    return _sha256_bytes(str(value or "").encode("utf-8", errors="replace"))


def _bridge_payload_digest(prefix: str, value: object) -> str:
    """Stay byte-compatible with ``bridge_server.payload_digest``."""

    return hashlib.sha256(
        f"{prefix}\n{value}".encode("utf-8", errors="replace")
    ).hexdigest()


def _tester_completion_identity_digest(
    *,
    operation_id: str,
    completion_marker: str,
    expert_symbol_period_sha256: str,
    log_identity_sha256: str,
    core_sources_sha256: str,
    core_thread_identities_sha256: str,
    start_line_sha256: str,
    completion_line_sha256: str,
    start_line_ordinal: int,
    completion_line_ordinal: int,
    completion_pass_count: int | None,
) -> str:
    pass_token = "" if completion_pass_count is None else str(completion_pass_count)
    return _sha256_text(
        "\n".join(
            (
                operation_id,
                completion_marker,
                expert_symbol_period_sha256,
                log_identity_sha256,
                core_sources_sha256,
                core_thread_identities_sha256,
                start_line_sha256,
                completion_line_sha256,
                str(start_line_ordinal),
                str(completion_line_ordinal),
                pass_token,
            )
        )
    )


def _validate_tester_completion_evidence(
    raw: object,
    *,
    expected_marker: str,
    expected_operation_id: str,
    expected_expert_file_name: str,
    expected_expert_ui_path: str,
    expected_deployed_expert_sha256: str,
    expected_symbol: str,
    expected_period: str,
) -> tuple[dict, str]:
    """Require a fresh, post-boundary MT5 log completion proof.

    A Stop -> Start button transition is intentionally insufficient because it
    is also observed when a local tester Core disconnects or crashes.
    """

    required = {
        "schemaVersion",
        "source",
        "boundaryCreatedAt",
        "runStartedAt",
        "runCompletedAt",
        "startLineSha256",
        "completionLineSha256",
        "completionMarker",
        "startLogPathSha256",
        "completionLogPathSha256",
        "startSourceSha256",
        "completionSourceSha256",
        "coreSourceCount",
        "coreSourceSha256s",
        "coreSourcesSha256",
        "coreThreadCount",
        "coreThreadIdentitySha256s",
        "coreThreadIdentitiesSha256",
        "startLineOrdinal",
        "completionLineOrdinal",
        "expertUiPathSha256",
        "deployedExpertSha256",
        "expertSymbolPeriodSha256",
        "logIdentitySha256",
        "executionThreadIdentitySha256",
        "runIdentitySha256",
        "completionPassCount",
        "coreDisconnectObserved",
        "verified",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise VisibleTerminalAdapterError("mt5_tester_clean_completion_unverified")
    try:
        boundary = _parse_utc(raw.get("boundaryCreatedAt"))
        started = _parse_utc(raw.get("runStartedAt"))
        completed = _parse_utc(raw.get("runCompletedAt"))
    except VisibleTerminalAdapterError as error:
        raise VisibleTerminalAdapterError(
            "mt5_tester_clean_completion_unverified"
        ) from error
    core_source_count = raw.get("coreSourceCount")
    core_source_sha256s = raw.get("coreSourceSha256s")
    core_thread_count = raw.get("coreThreadCount")
    core_thread_identity_sha256s = raw.get("coreThreadIdentitySha256s")
    start_line_ordinal = raw.get("startLineOrdinal")
    completion_line_ordinal = raw.get("completionLineOrdinal")
    completion_pass_count = raw.get("completionPassCount")
    expected_expert_ui_path_sha256 = _sha256_text(expected_expert_ui_path)
    expected_expert_symbol_period_sha256 = _sha256_text(
        "\n".join(
            (
                expected_expert_file_name,
                expected_deployed_expert_sha256,
                expected_expert_ui_path_sha256,
                expected_symbol,
                expected_period,
            )
        )
    )
    expected_log_identity_sha256 = _sha256_text(
        "\n".join(
            (
                str(raw.get("startLogPathSha256") or ""),
                str(raw.get("completionLogPathSha256") or ""),
                str(raw.get("startSourceSha256") or ""),
                str(raw.get("completionSourceSha256") or ""),
            )
        )
    )
    expected_execution_thread_identity_sha256 = _sha256_text(
        "\n".join(
            (
                expected_log_identity_sha256,
                str(start_line_ordinal),
                str(completion_line_ordinal),
                str(raw.get("coreThreadIdentitiesSha256") or ""),
            )
        )
    )
    expected_run_identity_sha256 = None
    if (
        isinstance(start_line_ordinal, int)
        and not isinstance(start_line_ordinal, bool)
        and isinstance(completion_line_ordinal, int)
        and not isinstance(completion_line_ordinal, bool)
        and (
            completion_pass_count is None
            or (
                isinstance(completion_pass_count, int)
                and not isinstance(completion_pass_count, bool)
            )
        )
        and expected_log_identity_sha256 is not None
    ):
        expected_run_identity_sha256 = _tester_completion_identity_digest(
            operation_id=expected_operation_id,
            completion_marker=expected_marker,
            expert_symbol_period_sha256=expected_expert_symbol_period_sha256,
            log_identity_sha256=expected_log_identity_sha256,
            core_sources_sha256=str(raw.get("coreSourcesSha256") or ""),
            core_thread_identities_sha256=str(
                raw.get("coreThreadIdentitiesSha256") or ""
            ),
            start_line_sha256=str(raw.get("startLineSha256") or ""),
            completion_line_sha256=str(raw.get("completionLineSha256") or ""),
            start_line_ordinal=start_line_ordinal,
            completion_line_ordinal=completion_line_ordinal,
            completion_pass_count=completion_pass_count,
        )
    if (
        raw.get("schemaVersion") != TESTER_COMPLETION_EVIDENCE_SCHEMA
        or raw.get("source") != "fresh_tester_log_completion"
        or expected_marker not in {"thread_finished", "optimization_finished"}
        or raw.get("completionMarker") != expected_marker
        or SHA256.fullmatch(str(raw.get("startLineSha256") or "")) is None
        or SHA256.fullmatch(str(raw.get("completionLineSha256") or "")) is None
        or SHA256.fullmatch(str(raw.get("startLogPathSha256") or "")) is None
        or SHA256.fullmatch(str(raw.get("completionLogPathSha256") or "")) is None
        or SHA256.fullmatch(str(raw.get("startSourceSha256") or "")) is None
        or SHA256.fullmatch(str(raw.get("completionSourceSha256") or "")) is None
        or (
            expected_marker == "optimization_finished"
            and (
                raw.get("completionLogPathSha256")
                != raw.get("startLogPathSha256")
                or raw.get("completionSourceSha256")
                != raw.get("startSourceSha256")
            )
        )
        or isinstance(core_source_count, bool)
        or not isinstance(core_source_count, int)
        or core_source_count < 1
        or core_source_count > 64
        or not isinstance(core_source_sha256s, list)
        or len(core_source_sha256s) != core_source_count
        or core_source_sha256s != sorted(set(core_source_sha256s))
        or any(
            not isinstance(value, str) or SHA256.fullmatch(value) is None
            for value in core_source_sha256s
        )
        or SHA256.fullmatch(str(raw.get("coreSourcesSha256") or "")) is None
        or raw.get("coreSourcesSha256")
        != _sha256_text("\n".join(core_source_sha256s))
        or isinstance(core_thread_count, bool)
        or not isinstance(core_thread_count, int)
        or core_thread_count < 1
        or core_thread_count > 64
        or (expected_marker == "thread_finished" and core_thread_count != 1)
        or not isinstance(core_thread_identity_sha256s, list)
        or len(core_thread_identity_sha256s) != core_thread_count
        or core_thread_identity_sha256s
        != sorted(set(core_thread_identity_sha256s))
        or any(
            not isinstance(value, str) or SHA256.fullmatch(value) is None
            for value in core_thread_identity_sha256s
        )
        or SHA256.fullmatch(
            str(raw.get("coreThreadIdentitiesSha256") or "")
        )
        is None
        or raw.get("coreThreadIdentitiesSha256")
        != _sha256_text("\n".join(core_thread_identity_sha256s))
        or (
            expected_marker == "thread_finished"
            and _sha256_text(
                f"{raw.get('completionLogPathSha256')}\n{raw.get('completionSourceSha256')}"
            )
            not in core_thread_identity_sha256s
        )
        or isinstance(start_line_ordinal, bool)
        or not isinstance(start_line_ordinal, int)
        or start_line_ordinal <= 0
        or isinstance(completion_line_ordinal, bool)
        or not isinstance(completion_line_ordinal, int)
        or (
            raw.get("completionLogPathSha256") == raw.get("startLogPathSha256")
            and completion_line_ordinal <= start_line_ordinal
        )
        or raw.get("expertUiPathSha256") != expected_expert_ui_path_sha256
        or raw.get("deployedExpertSha256") != expected_deployed_expert_sha256
        or raw.get("expertSymbolPeriodSha256")
        != expected_expert_symbol_period_sha256
        or raw.get("logIdentitySha256") != expected_log_identity_sha256
        or raw.get("executionThreadIdentitySha256")
        != expected_execution_thread_identity_sha256
        or raw.get("runIdentitySha256") != expected_run_identity_sha256
        or (
            expected_marker == "optimization_finished"
            and (
                isinstance(completion_pass_count, bool)
                or not isinstance(completion_pass_count, int)
                or completion_pass_count < 2
            )
        )
        or (
            expected_marker == "thread_finished"
            and completion_pass_count is not None
        )
        or raw.get("coreDisconnectObserved") is not False
        or raw.get("verified") is not True
        or started < boundary
        or completed < started
        or completed > datetime.now(timezone.utc) + timedelta(minutes=5)
    ):
        raise VisibleTerminalAdapterError("mt5_tester_clean_completion_unverified")
    evidence = copy.deepcopy(raw)
    return evidence, _sha256_bytes(_canonical_json(evidence))


def _ensure_tester_completion_evidence_checkpoint(
    path: Path, evidence: dict, *, allow_create: bool
) -> str:
    """Commit the runner proof outside the mutable receipt and rebind replay."""

    code = "tester_completion_evidence_checkpoint_invalid"
    expected_bytes = _canonical_json(evidence)
    expected_digest = _sha256_bytes(expected_bytes)
    if not path.exists():
        if not allow_create:
            raise VisibleTerminalAdapterError(code)
        _write_exclusive(path, expected_bytes, code)
    raw, digest, _size = _stable_single_link_bytes(
        path, maximum_bytes=128 * 1024, code=code
    )
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if (
        raw != expected_bytes
        or digest != expected_digest
        or not isinstance(parsed, dict)
        or parsed != evidence
    ):
        raise VisibleTerminalAdapterError(code)
    return digest


def _validate_strategy_execution_profile(
    raw: object,
    *,
    stage_id: str,
    source_digest: str,
) -> dict | None:
    """Validate the bridge-authored opt-in for strategy-level log proof.

    Generic EAs deliberately omit this profile.  The only admitted profile is
    the immutable EMA smoke EA, and it is meaningful only for the visual
    backtest stage.  The profile digest is part of the durable action identity.
    """

    if raw is None:
        return None
    required = {
        "schemaVersion",
        "profileId",
        "sourceDigest",
        "proofRequired",
        "fastPeriod",
        "slowPeriod",
        "previousShift",
        "currentShift",
        "requiredDirections",
        "profileDigest",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise VisibleTerminalAdapterError("strategy_execution_profile_invalid")
    core = {key: copy.deepcopy(raw[key]) for key in required if key != "profileDigest"}
    expected_digest = _sha256_bytes(_canonical_json(core))
    if (
        stage_id != "backtest_recheck"
        or raw.get("schemaVersion") != STRATEGY_EXECUTION_PROFILE_SCHEMA
        or raw.get("profileId") != CERTIFIED_EMA_SMOKE_PROFILE_ID
        or raw.get("sourceDigest") != source_digest
        or raw.get("proofRequired") is not True
        or raw.get("fastPeriod") != 10
        or raw.get("slowPeriod") != 60
        or raw.get("previousShift") != 2
        or raw.get("currentShift") != 1
        or raw.get("requiredDirections") != ["BUY", "SELL"]
        or raw.get("profileDigest") != expected_digest
    ):
        raise VisibleTerminalAdapterError("strategy_execution_profile_invalid")
    return copy.deepcopy(raw)


def _validate_strategy_execution_proof(
    raw: object,
    *,
    profile: dict | None,
    operation_id: str,
    symbol: str,
    period: str,
) -> tuple[dict | None, str | None]:
    """Validate signal -> pending -> real entry telemetry for the smoke EA."""

    if profile is None:
        if raw is not None:
            raise VisibleTerminalAdapterError("unexpected_strategy_execution_proof")
        return None, None
    required = {
        "schemaVersion",
        "profileId",
        "sourceDigest",
        "operationId",
        "symbol",
        "period",
        "eventCount",
        "signalCount",
        "entryCount",
        "rejectedCount",
        "orphanCount",
        "pendingCount",
        "dataUnavailableCount",
        "buySignalCount",
        "sellSignalCount",
        "buyEntryCount",
        "sellEntryCount",
        "sequences",
        "telemetryLineSha256s",
        "telemetryDigest",
        "finalLineSha256",
        "verified",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise VisibleTerminalAdapterError("strategy_execution_proof_invalid")
    counts = {
        key: raw.get(key)
        for key in (
            "eventCount",
            "signalCount",
            "entryCount",
            "rejectedCount",
            "orphanCount",
            "pendingCount",
            "dataUnavailableCount",
            "buySignalCount",
            "sellSignalCount",
            "buyEntryCount",
            "sellEntryCount",
        )
    }
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in counts.values()
    ):
        raise VisibleTerminalAdapterError("strategy_execution_proof_invalid")
    sequences = raw.get("sequences")
    line_hashes = raw.get("telemetryLineSha256s")
    signal_count = counts["signalCount"]
    if (
        raw.get("schemaVersion") != STRATEGY_EXECUTION_PROOF_SCHEMA
        or raw.get("profileId") != profile["profileId"]
        or raw.get("sourceDigest") != profile["sourceDigest"]
        or raw.get("operationId") != operation_id
        or raw.get("symbol") != symbol
        or raw.get("period") != period
        or raw.get("verified") is not True
        or counts["signalCount"] != counts["entryCount"]
        or counts["rejectedCount"] != 0
        or counts["orphanCount"] != 0
        or counts["pendingCount"] != 0
        or counts["buySignalCount"] != counts["buyEntryCount"]
        or counts["sellSignalCount"] != counts["sellEntryCount"]
        or counts["buySignalCount"] + counts["sellSignalCount"] != signal_count
        or counts["buySignalCount"] < 1
        or counts["sellSignalCount"] < 1
        or counts["eventCount"] != (signal_count * 3) + 1
        or not isinstance(sequences, list)
        or len(sequences) != signal_count
        or not isinstance(line_hashes, list)
        or len(line_hashes) != counts["eventCount"]
        or any(not isinstance(item, str) or SHA256.fullmatch(item) is None for item in line_hashes)
        or len(set(line_hashes)) != len(line_hashes)
        or SHA256.fullmatch(str(raw.get("finalLineSha256") or "")) is None
        or raw.get("finalLineSha256") != line_hashes[-1]
        or SHA256.fullmatch(str(raw.get("telemetryDigest") or "")) is None
        or raw.get("telemetryDigest") != _sha256_text("\n".join(line_hashes))
    ):
        raise VisibleTerminalAdapterError("strategy_execution_proof_invalid")
    sequence_keys = {
        "seq",
        "direction",
        "closedBarTime",
        "fast2",
        "fast1",
        "slow2",
        "slow1",
        "deal",
        "signalLineSha256",
        "pendingLineSha256",
        "entryLineSha256",
    }
    seen_deals: set[int] = set()
    for index, item in enumerate(sequences):
        if not isinstance(item, dict) or set(item) != sequence_keys:
            raise VisibleTerminalAdapterError("strategy_execution_proof_invalid")
        direction = item.get("direction")
        numeric = [item.get(name) for name in ("fast2", "fast1", "slow2", "slow1")]
        deal = item.get("deal")
        closed_bar_time = item.get("closedBarTime")
        if (
            item.get("seq") != index + 1
            or direction not in {"BUY", "SELL"}
            or isinstance(closed_bar_time, bool)
            or not isinstance(closed_bar_time, int)
            or closed_bar_time <= 0
            or isinstance(deal, bool)
            or not isinstance(deal, int)
            or deal <= 0
            or deal in seen_deals
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in numeric
            )
            or item.get("signalLineSha256") != line_hashes[index * 3]
            or item.get("pendingLineSha256") != line_hashes[index * 3 + 1]
            or item.get("entryLineSha256") != line_hashes[index * 3 + 2]
        ):
            raise VisibleTerminalAdapterError("strategy_execution_proof_invalid")
        fast2, fast1, slow2, slow1 = (float(value) for value in numeric)
        crosses = (
            fast2 <= slow2 and fast1 > slow1
            if direction == "BUY"
            else fast2 >= slow2 and fast1 < slow1
        )
        if not crosses:
            raise VisibleTerminalAdapterError("strategy_execution_proof_invalid")
        seen_deals.add(deal)
    proof = copy.deepcopy(raw)
    return proof, _sha256_bytes(_canonical_json(proof))


def _validate_expert_catalog_refresh_evidence(
    raw: object,
    expected_expert_ui_path: str,
    *,
    expected_process_id: int | None = None,
    expected_window_handle: int | None = None,
) -> tuple[dict, str]:
    """Validate the exact, bounded Navigator catalogue decision evidence."""

    required = {
        "schemaVersion",
        "attempted",
        "recoveredAfterBoundary",
        "commandCount",
        "commandName",
        "boundarySha256",
        "navigatorPaneAutomationId",
        "navigatorTreeAutomationId",
        "expertNodeName",
        "refreshMenuAutomationId",
        "refreshMenuName",
        "refreshMenuProvider",
        "refreshMenuWindowClass",
        "refreshMenuNativeCommandId",
        "refreshMenuDispatchMethod",
        "matchCountBefore",
        "matchCountAfter",
        "selectedExpertReadback",
        "idleStateBefore",
        "idleStateImmediatelyBeforeRefresh",
        "idleStateAfter",
        "algoTradingStateBefore",
        "algoTradingStateAfter",
        "terminalProcessId",
        "terminalWindowHandle",
        "elapsedMs",
        "verified",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise VisibleTerminalAdapterError(
            "mt5_expert_catalog_refresh_evidence_invalid"
        )
    attempted = raw.get("attempted")
    recovered = raw.get("recoveredAfterBoundary")
    command_count = raw.get("commandCount")
    match_before = raw.get("matchCountBefore")
    match_after = raw.get("matchCountAfter")
    process_id = raw.get("terminalProcessId")
    window_handle = raw.get("terminalWindowHandle")
    elapsed_ms = raw.get("elapsedMs")
    algo_before = raw.get("algoTradingStateBefore")
    algo_after = raw.get("algoTradingStateAfter")
    selected = str(raw.get("selectedExpertReadback") or "").strip().replace(
        "/", "\\"
    )
    expected = str(expected_expert_ui_path or "").strip().replace("/", "\\")
    expected_names = {expected.casefold(), (expected + ".ex5").casefold()}
    if (
        raw.get("schemaVersion") != EXPERT_CATALOG_REFRESH_SCHEMA
        or type(attempted) is not bool
        or type(recovered) is not bool
        or (recovered and not attempted)
        or type(command_count) is not int
        or command_count != (1 if attempted else 0)
        or raw.get("commandName") != ("Refresh" if attempted else None)
        or (
            (attempted and SHA256.fullmatch(str(raw.get("boundarySha256") or "")) is None)
            or (not attempted and raw.get("boundarySha256") is not None)
        )
        or raw.get("navigatorPaneAutomationId") != "32845"
        or raw.get("navigatorTreeAutomationId") != "10064"
        or raw.get("expertNodeName") != "Expert Advisors"
        or raw.get("refreshMenuAutomationId") is not None
        or raw.get("refreshMenuName") != "Refresh"
        or raw.get("refreshMenuProvider") != "native_hmenu"
        or raw.get("refreshMenuWindowClass") != "#32768"
        or raw.get("refreshMenuNativeCommandId") != 33416
        or raw.get("refreshMenuDispatchMethod") != "targeted_menu_keyboard"
        or type(match_before) is not int
        or (
            (attempted and not recovered and match_before != 0)
            or (attempted and recovered and match_before not in {0, 1})
            or (not attempted and match_before != 1)
        )
        or type(match_after) is not int
        or match_after != 1
        or not expected
        or selected.casefold() not in expected_names
        or raw.get("idleStateBefore") != "Start"
        or raw.get("idleStateAfter") != "Start"
        or raw.get("idleStateImmediatelyBeforeRefresh")
        != ("Start" if attempted and not recovered else None)
        or type(algo_before) is not bool
        or type(algo_after) is not bool
        or algo_before != algo_after
        or type(process_id) is not int
        or process_id <= 0
        or (
            expected_process_id is not None
            and process_id != expected_process_id
        )
        or type(window_handle) is not int
        or window_handle <= 0
        or (
            expected_window_handle is not None
            and window_handle != expected_window_handle
        )
        or type(elapsed_ms) is not int
        or elapsed_ms < 0
        or elapsed_ms > 30_000
        or raw.get("verified") is not True
    ):
        raise VisibleTerminalAdapterError(
            "mt5_expert_catalog_refresh_evidence_invalid"
        )
    normalized = copy.deepcopy(raw)
    return normalized, _sha256_bytes(_canonical_json(normalized))


def _validate_expert_catalog_refresh_boundary(
    path: Path, expected: dict, evidence: dict
) -> str | None:
    """Bind the operation-scoped at-most-once Refresh boundary to evidence."""

    if evidence["attempted"] is not True:
        if path.exists():
            raise VisibleTerminalAdapterError(
                "mt5_expert_catalog_refresh_boundary_unexpected"
            )
        return None
    if _read_json_object(
        path, "mt5_expert_catalog_refresh_boundary_invalid"
    ) != expected:
        raise VisibleTerminalAdapterError(
            "mt5_expert_catalog_refresh_boundary_mismatch"
        )
    digest, _ = _stable_digest(path, maximum_bytes=64 * 1024)
    expected_digest = _sha256_bytes(_canonical_json(expected))
    if (
        digest != expected_digest
        or evidence.get("boundarySha256") != expected_digest
    ):
        raise VisibleTerminalAdapterError(
            "mt5_expert_catalog_refresh_boundary_mismatch"
        )
    return digest


def _path_has_reparse_component(path: Path) -> bool:
    try:
        absolute = path.absolute()
    except (OSError, RuntimeError, ValueError):
        return True
    for candidate in (absolute, *absolute.parents):
        if candidate.parent == candidate:
            continue
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        except (OSError, RuntimeError, ValueError):
            return True
        if stat.S_ISLNK(metadata.st_mode):
            return True
        if int(getattr(metadata, "st_file_attributes", 0) or 0) & 0x400:
            return True
    return False


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolved_directory(path: object, code: str) -> Path:
    candidate = Path(str(path or ""))
    try:
        if (
            not candidate.is_absolute()
            or _path_has_reparse_component(candidate)
            or not candidate.is_dir()
        ):
            raise VisibleTerminalAdapterError(code)
        return candidate.resolve(strict=True)
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error


def _resolved_file(path: object, code: str, *, maximum_bytes: int) -> Path:
    candidate = Path(str(path or ""))
    try:
        if (
            not candidate.is_absolute()
            or _path_has_reparse_component(candidate)
            or not candidate.is_file()
        ):
            raise VisibleTerminalAdapterError(code)
        resolved = candidate.resolve(strict=True)
        size = resolved.stat(follow_symlinks=False).st_size
        if size <= 0 or size > maximum_bytes:
            raise VisibleTerminalAdapterError(code)
        return resolved
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error


def _require_single_link(path: Path, code: str) -> None:
    try:
        metadata = path.stat(follow_symlinks=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if not stat.S_ISREG(metadata.st_mode) or int(metadata.st_nlink) != 1:
        raise VisibleTerminalAdapterError(code)


def _stable_digest(path: Path, *, maximum_bytes: int) -> tuple[str, int]:
    try:
        if _path_has_reparse_component(path) or not path.is_file():
            raise VisibleTerminalAdapterError("evidence_file_unavailable")
        before = path.stat(follow_symlinks=False)
        if before.st_size <= 0 or before.st_size > maximum_bytes:
            raise VisibleTerminalAdapterError("evidence_file_size_invalid")
        digest = hashlib.sha256()
        observed = 0
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(64 * 1024), b""):
                observed += len(block)
                if observed > maximum_bytes:
                    raise VisibleTerminalAdapterError("evidence_file_size_invalid")
                digest.update(block)
        after = path.stat(follow_symlinks=False)
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError("evidence_file_unavailable") from error
    if (
        observed != before.st_size
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
        or getattr(after, "st_ino", None) != getattr(before, "st_ino", None)
    ):
        raise VisibleTerminalAdapterError("evidence_file_changed_during_read")
    return digest.hexdigest(), observed


def _stable_single_link_bytes(
    path: Path, *, maximum_bytes: int, code: str
) -> tuple[bytes, str, int]:
    """Read one immutable operation checkpoint through one verified handle."""

    try:
        if _path_has_reparse_component(path):
            raise VisibleTerminalAdapterError(code)
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or int(getattr(before, "st_file_attributes", 0) or 0) & 0x400
            or int(before.st_nlink) != 1
            or before.st_size <= 0
            or before.st_size > maximum_bytes
        ):
            raise VisibleTerminalAdapterError(code)
        chunks: list[bytes] = []
        observed = 0
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or int(opened.st_nlink) != 1
                or opened.st_dev != before.st_dev
                or opened.st_ino != before.st_ino
                or opened.st_size != before.st_size
            ):
                raise VisibleTerminalAdapterError(code)
            for block in iter(lambda: handle.read(64 * 1024), b""):
                observed += len(block)
                if observed > maximum_bytes:
                    raise VisibleTerminalAdapterError(code)
                chunks.append(block)
            handle_after = os.fstat(handle.fileno())
        after = path.lstat()
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if (
        observed != before.st_size
        or int(handle_after.st_nlink) != 1
        or int(after.st_nlink) != 1
        or handle_after.st_dev != before.st_dev
        or handle_after.st_ino != before.st_ino
        or after.st_dev != before.st_dev
        or after.st_ino != before.st_ino
        or handle_after.st_size != before.st_size
        or after.st_size != before.st_size
        or handle_after.st_mtime_ns != opened.st_mtime_ns
        or after.st_mtime_ns != before.st_mtime_ns
        or handle_after.st_ctime_ns != opened.st_ctime_ns
        or after.st_ctime_ns != before.st_ctime_ns
    ):
        raise VisibleTerminalAdapterError(code)
    payload = b"".join(chunks)
    return payload, _sha256_bytes(payload), observed


def _validate_start_boundary_checkpoint(
    path: Path,
    *,
    expected_bytes: bytes,
    expected_payload: dict,
    expected_digest: str,
) -> None:
    code = "tester_start_boundary_mismatch"
    raw, digest, _size = _stable_single_link_bytes(
        path, maximum_bytes=32 * 1024, code=code
    )
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if (
        raw != expected_bytes
        or digest != expected_digest
        or not isinstance(payload, dict)
        or payload != expected_payload
    ):
        raise VisibleTerminalAdapterError(code)


def _write_exclusive(path: Path, payload: bytes, code: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise VisibleTerminalAdapterError(code) from error
    except (OSError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_json_object(path: Path, code: str, *, maximum_bytes: int = 256 * 1024) -> dict:
    try:
        _digest, _size = _stable_digest(path, maximum_bytes=maximum_bytes)
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except VisibleTerminalAdapterError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if not isinstance(value, dict):
        raise VisibleTerminalAdapterError(code)
    return value


def _managed_path(root: Path, relative: object, code: str) -> Path:
    raw = str(relative or "").replace("\\", "/")
    if (
        not raw
        or len(raw) > 260
        or raw.startswith("/")
        or ":" in raw
        or any(part in {"", ".", ".."} for part in raw.split("/"))
    ):
        raise VisibleTerminalAdapterError(code)
    candidate = root.joinpath(*raw.split("/"))
    try:
        parent = candidate.parent.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if _path_has_reparse_component(parent) or not _is_relative_to(parent, root):
        raise VisibleTerminalAdapterError(code)
    return parent / candidate.name


def _copy_exclusive_or_verify(
    source: Path,
    destination: Path,
    *,
    maximum_bytes: int,
    code: str,
) -> tuple[str, int, bool]:
    _require_single_link(source, code)
    source_digest, source_size = _stable_digest(source, maximum_bytes=maximum_bytes)
    if not destination.parent.is_dir() or _path_has_reparse_component(destination.parent):
        raise VisibleTerminalAdapterError(code)
    if destination.exists():
        _require_single_link(destination, code)
        digest, size = _stable_digest(destination, maximum_bytes=maximum_bytes)
        if size != source_size or not secrets.compare_digest(digest, source_digest):
            raise VisibleTerminalAdapterError(f"{code}_collision")
        return source_digest, source_size, True
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor: int | None = None
    try:
        descriptor = os.open(destination, flags, 0o600)
        with source.open("rb") as input_handle, os.fdopen(descriptor, "wb") as output_handle:
            descriptor = None
            for block in iter(lambda: input_handle.read(64 * 1024), b""):
                output_handle.write(block)
            output_handle.flush()
            os.fsync(output_handle.fileno())
    except FileExistsError:
        return _copy_exclusive_or_verify(
            source, destination, maximum_bytes=maximum_bytes, code=code
        )
    except (OSError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    digest, size = _stable_digest(destination, maximum_bytes=maximum_bytes)
    _require_single_link(destination, code)
    if size != source_size or not secrets.compare_digest(digest, source_digest):
        raise VisibleTerminalAdapterError(f"{code}_digest_mismatch")
    return digest, size, False


def _safe_tree(root: Path, components: tuple[str, ...], code: str) -> Path:
    current = root.resolve(strict=True)
    for name in components:
        if not name or any(token in name for token in ("/", "\\", ":")):
            raise VisibleTerminalAdapterError(code)
        candidate = current / name
        try:
            candidate.mkdir(exist_ok=True)
            metadata = candidate.lstat()
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or stat.S_ISLNK(metadata.st_mode)
                or int(getattr(metadata, "st_file_attributes", 0) or 0) & 0x400
                or _path_has_reparse_component(candidate)
            ):
                raise VisibleTerminalAdapterError(code)
            current = candidate.resolve(strict=True)
        except VisibleTerminalAdapterError:
            raise
        except (OSError, RuntimeError, ValueError) as error:
            raise VisibleTerminalAdapterError(code) from error
        if not _is_relative_to(current, root):
            raise VisibleTerminalAdapterError(code)
    return current


def _validate_png(path: Path) -> tuple[str, int]:
    digest, size = _stable_digest(path, maximum_bytes=MAX_EVIDENCE_BYTES)
    try:
        header = path.read_bytes()[:8]
    except OSError as error:
        raise VisibleTerminalAdapterError("screenshot_unreadable") from error
    if header != b"\x89PNG\r\n\x1a\n" or size < 1024:
        raise VisibleTerminalAdapterError("screenshot_invalid")
    return digest, size


def _relative_path(path: Path, workspace: Path) -> str:
    resolved = path.resolve(strict=True)
    if not _is_relative_to(resolved, workspace):
        raise VisibleTerminalAdapterError("artifact_outside_workspace")
    return resolved.relative_to(workspace).as_posix()


def _artifact(
    alias: str, path: Path, workspace: Path, *, artifact_kind: str
) -> dict:
    return {
        "alias": alias,
        "relativePath": _relative_path(path, workspace),
        "artifactKind": artifact_kind,
    }


def _validate_target(
    raw: object,
    terminal_binding: dict,
    platform: str,
    stage_id: str,
) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("terminal_target_missing")
    required = {
        "candidateId",
        "selectionRevision",
        "bindingDigest",
        "platform",
        "installPath",
        "dataPath",
        "terminalPath",
        "compilerPath",
    }
    if not required.issubset(raw):
        raise VisibleTerminalAdapterError("terminal_target_incomplete")
    if platform != "mt5" or raw.get("platform") != "mt5":
        raise VisibleTerminalAdapterError("mt5_platform_required")
    if stage_id not in {"compile_validate", "backtest_recheck", "optimize"}:
        raise VisibleTerminalAdapterError("visible_stage_unsupported")
    if (
        raw.get("candidateId") != terminal_binding.get("candidateId")
        or raw.get("selectionRevision") != terminal_binding.get("selectionRevision")
        or raw.get("bindingDigest") != terminal_binding.get("bindingDigest")
        or re.fullmatch(r"mtc-[A-Za-z0-9._-]{1,115}", str(raw.get("candidateId") or ""))
        is None
        or isinstance(raw.get("selectionRevision"), bool)
        or not isinstance(raw.get("selectionRevision"), int)
        or raw.get("selectionRevision") < 1
        or SHA256.fullmatch(str(raw.get("bindingDigest") or "")) is None
    ):
        raise VisibleTerminalAdapterError("terminal_binding_mismatch")
    install = _resolved_directory(raw.get("installPath"), "terminal_install_path_invalid")
    data = _resolved_directory(raw.get("dataPath"), "terminal_data_path_invalid")
    terminal = _resolved_file(
        raw.get("terminalPath"), "terminal_executable_invalid", maximum_bytes=1024 * 1024 * 1024
    )
    compiler = _resolved_file(
        raw.get("compilerPath"), "metaeditor_executable_invalid", maximum_bytes=1024 * 1024 * 1024
    )
    mql5 = data / "MQL5"
    if (
        terminal.name.casefold() != "terminal64.exe"
        or compiler.name.casefold() != "metaeditor64.exe"
        or terminal.parent != install
        or compiler.parent != install
        or not mql5.is_dir()
        or _path_has_reparse_component(mql5)
    ):
        raise VisibleTerminalAdapterError("terminal_target_origin_invalid")
    terminal_digest, _ = _stable_digest(terminal, maximum_bytes=1024 * 1024 * 1024)
    compiler_digest, _ = _stable_digest(compiler, maximum_bytes=1024 * 1024 * 1024)
    front_office_digest = (
        compiler_digest if stage_id == "compile_validate" else terminal_digest
    )
    for field, digest in (
        ("terminalExecutableSha256", terminal_digest),
        ("frontOfficeExecutableSha256", front_office_digest),
    ):
        supplied = raw.get(field)
        if supplied is not None and not secrets.compare_digest(str(supplied), digest):
            raise VisibleTerminalAdapterError("terminal_target_executable_digest_mismatch")
    return {
        "candidateId": raw["candidateId"],
        "selectionRevision": raw["selectionRevision"],
        "bindingDigest": raw["bindingDigest"],
        "platform": "mt5",
        "installPath": install,
        "dataPath": data,
        "terminalPath": terminal,
        "compilerPath": compiler,
        "terminalExecutableSha256": terminal_digest,
        "frontOfficeExecutableSha256": front_office_digest,
    }


def _validate_request(raw: object, expected_stage: str) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("visible_request_invalid")
    required = {
        "schemaVersion",
        "buildId",
        "stageId",
        "platform",
        "artifactKind",
        "workspaceRoot",
        "versions",
        "terminalBinding",
        "visibleOperation",
        "missionId",
        "reportId",
        "safety",
    }
    allowed = required | {
        "processBinding",
        "terminalTarget",
        "resolvedTarget",
        "testerSettings",
        "optimizationIntent",
        "compiledDeployment",
        "mt5InputBinding",
        "mt5InputManifest",
        "strategyExecutionProfile",
        "capabilityCheckedAt",
    }
    if not required.issubset(raw) or not set(raw).issubset(allowed):
        raise VisibleTerminalAdapterError("visible_request_shape_invalid")
    if (
        raw.get("schemaVersion") != REQUEST_SCHEMA
        or raw.get("stageId") != expected_stage
        or raw.get("platform") != "mt5"
        or raw.get("artifactKind") != "expert_advisor"
        or not SAFE_ID.fullmatch(str(raw.get("buildId") or ""))
        or not SAFE_ID.fullmatch(str(raw.get("missionId") or ""))
        or not SAFE_ID.fullmatch(str(raw.get("reportId") or ""))
    ):
        raise VisibleTerminalAdapterError("visible_request_contract_invalid")
    binding = raw.get("terminalBinding")
    operation = raw.get("visibleOperation")
    safety = raw.get("safety")
    expected_optimization = expected_stage == "optimize"
    expected_visual = expected_stage == "backtest_recheck"
    never_start = safety.get("neverStart", False) if isinstance(safety, dict) else False
    service_action = safety.get("serviceAction") if isinstance(safety, dict) else None
    base_safety_keys = {
        "liveTradingAllowed",
        "autoTradingMayBeToggled",
        "chartAttachmentAllowed",
        "terminalShutdownAllowed",
        "optimizationAllowed",
        "visualModeRequired",
    }
    safety_keys = frozenset(safety) if isinstance(safety, dict) else frozenset()
    dynamic_safety_keys = {"neverStart", "serviceAction"}
    if (
        not isinstance(binding, dict)
        or binding.get("platform") != "mt5"
        or not isinstance(operation, dict)
        or not SAFE_OPERATION_ID.fullmatch(str(operation.get("operationId") or ""))
        or operation.get("stageId") != expected_stage
        or operation.get("state") != "reserved"
        or operation.get("requiresExplicitResume") is not False
        or not isinstance(safety, dict)
        or safety_keys not in {frozenset(base_safety_keys), frozenset(base_safety_keys | dynamic_safety_keys)}
        or (
            expected_optimization
            and safety_keys != frozenset(base_safety_keys | dynamic_safety_keys)
        )
        or safety.get("liveTradingAllowed") is not False
        or safety.get("autoTradingMayBeToggled") is not False
        or safety.get("chartAttachmentAllowed") is not False
        or safety.get("terminalShutdownAllowed") is not False
        or safety.get("optimizationAllowed") is not expected_optimization
        or safety.get("visualModeRequired") is not expected_visual
        or ("neverStart" in safety and type(never_start) is not bool)
        or (
            "neverStart" in safety
            and (
                service_action not in {"start_round", "collect_round", "recover_round"}
                or never_start is not (service_action != "start_round")
            )
        )
    ):
        raise VisibleTerminalAdapterError("visible_request_safety_invalid")
    workspace = _resolved_directory(raw.get("workspaceRoot"), "workspace_root_invalid")
    versions = raw.get("versions")
    if not isinstance(versions, list) or not versions or len(versions) > 20:
        raise VisibleTerminalAdapterError("source_version_missing")
    candidates: list[dict] = []
    for item in versions:
        if not isinstance(item, dict):
            raise VisibleTerminalAdapterError("source_version_invalid")
        source = _managed_path(
            workspace,
            item.get("versionFile") or item.get("sourceFile"),
            "source_path_invalid",
        )
        source = _resolved_file(source, "source_file_invalid", maximum_bytes=MAX_SOURCE_BYTES)
        digest, _ = _stable_digest(source, maximum_bytes=MAX_SOURCE_BYTES)
        if (
            source.suffix.casefold() != ".mq5"
            or SHA256.fullmatch(str(item.get("sourceDigest") or "")) is None
            or not secrets.compare_digest(digest, str(item.get("sourceDigest")))
        ):
            raise VisibleTerminalAdapterError("source_digest_mismatch")
        candidates.append({"row": copy.deepcopy(item), "path": source, "digest": digest})
    strategy_execution_profile = _validate_strategy_execution_profile(
        raw.get("strategyExecutionProfile"),
        stage_id=expected_stage,
        source_digest=candidates[-1]["digest"],
    )
    return {
        "raw": copy.deepcopy(raw),
        "platform": "mt5",
        "stageId": expected_stage,
        "workspace": workspace,
        "source": candidates[-1],
        "strategyExecutionProfile": strategy_execution_profile,
        "terminalBinding": copy.deepcopy(binding),
        "operation": copy.deepcopy(operation),
    }


def _semantic_input_value_equal(left: object, right: object, value_kind: str) -> bool:
    left_text = str(left).strip()
    right_text = str(right).strip()
    if value_kind == "bool":
        aliases = {"true": "1", "false": "0", "1": "1", "0": "0"}
        left_value = aliases.get(left_text.casefold())
        right_value = aliases.get(right_text.casefold())
        return (
            left_value is not None
            and right_value is not None
            and left_value == right_value
        )
    try:
        from decimal import Decimal, InvalidOperation

        return Decimal(left_text) == Decimal(right_text)
    except (InvalidOperation, ValueError):
        return False


def _validate_input_manifest(
    raw: object,
    source_digest: str,
    source_code: str | None = None,
) -> dict:
    if not isinstance(raw, dict) or set(raw) != {
        "schemaVersion",
        "sourceDigest",
        "entries",
        "manifestDigest",
    }:
        raise VisibleTerminalAdapterError("mt5_input_manifest_invalid")
    entries = raw.get("entries")
    if not isinstance(entries, list) or not (
        1 <= len(entries) <= MT5_INPUT_MANIFEST_MAX_COUNT
    ):
        raise VisibleTerminalAdapterError("mt5_input_manifest_invalid")
    normalized_entries: list[dict] = []
    seen: set[str] = set()
    for ordinal, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {
            "ordinal",
            "qualifier",
            "declaredType",
            "inputName",
            "valueKind",
            "setDefault",
            "enumValues",
            "optimizable",
        }:
            raise VisibleTerminalAdapterError("mt5_input_manifest_invalid")
        name = str(entry.get("inputName") or "")
        qualifier = str(entry.get("qualifier") or "")
        declared_type = str(entry.get("declaredType") or "")
        value_kind = str(entry.get("valueKind") or "")
        default = entry.get("setDefault")
        enum_values = entry.get("enumValues")
        if (
            entry.get("ordinal") != ordinal
            or SAFE_INPUT_NAME.fullmatch(name) is None
            or name.casefold() in seen
            or qualifier not in {"input", "sinput"}
            or SAFE_INPUT_NAME.fullmatch(declared_type) is None
            or value_kind not in {"bool", "integer", "decimal", "enum"}
            or not isinstance(default, str)
            or not default.strip()
            or not isinstance(enum_values, list)
            or len(enum_values) > 128
            or any(not isinstance(value, str) or not value.strip() for value in enum_values)
            or type(entry.get("optimizable")) is not bool
            or entry.get("optimizable") is not (qualifier == "input")
            or (value_kind == "enum") is not bool(enum_values)
        ):
            raise VisibleTerminalAdapterError("mt5_input_manifest_invalid")
        seen.add(name.casefold())
        normalized_entries.append(copy.deepcopy(entry))
    core = {
        "schemaVersion": INPUT_MANIFEST_SCHEMA,
        "sourceDigest": source_digest,
        "entries": normalized_entries,
    }
    manifest_digest = _sha256_bytes(_canonical_json(core))
    if (
        raw.get("schemaVersion") != INPUT_MANIFEST_SCHEMA
        or raw.get("sourceDigest") != source_digest
        or raw.get("manifestDigest") != manifest_digest
    ):
        raise VisibleTerminalAdapterError("mt5_input_manifest_invalid")
    normalized = {**core, "manifestDigest": manifest_digest}
    if source_code is not None:
        expected = _input_manifest_from_source(source_code, source_digest)
        if normalized != expected:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_mismatch"
            )
    return normalized


def _decode_set_payload(payload: bytes) -> str:
    candidates = (
        ("utf-16",) if payload.startswith((b"\xff\xfe", b"\xfe\xff")) else ()
    ) + (("utf-16-le",) if payload[:512].count(b"\x00") > 40 else ()) + (
        "utf-8-sig",
        "ascii",
    )
    for encoding in candidates:
        try:
            return payload.decode(encoding, errors="strict")
        except UnicodeError:
            continue
    raise VisibleTerminalAdapterError("mt5_set_encoding_invalid")


def _read_set_entries(path: Path) -> list[dict]:
    digest, size = _stable_digest(path, maximum_bytes=MAX_SET_BYTES)
    del digest
    if size <= 0:
        raise VisibleTerminalAdapterError("mt5_set_empty")
    try:
        text = _decode_set_payload(path.read_bytes())
    except OSError as error:
        raise VisibleTerminalAdapterError("mt5_set_unreadable") from error
    result: list[dict] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        match = re.fullmatch(
            r"([A-Za-z_][A-Za-z0-9_]*)=([^|\r\n]+)\|\|([^|\r\n]+)\|\|"
            r"([^|\r\n]+)\|\|([^|\r\n]+)\|\|([YyNn10])",
            line,
        )
        if match is None or match.group(1).casefold() in seen:
            raise VisibleTerminalAdapterError("mt5_set_semantic_invalid")
        seen.add(match.group(1).casefold())
        result.append(
            {
                "inputName": match.group(1),
                "current": match.group(2).strip(),
                "start": match.group(3).strip(),
                "step": match.group(4).strip(),
                "stop": match.group(5).strip(),
                "enabled": match.group(6).upper() in {"Y", "1"},
            }
        )
    if not result:
        raise VisibleTerminalAdapterError("mt5_set_semantic_invalid")
    return result


def _validate_expected_readback_entries(
    raw: object,
    manifest: dict,
    *,
    fixed_current_overrides: dict[str, str] | None = None,
) -> list[dict]:
    if not isinstance(raw, list) or len(raw) != len(manifest["entries"]):
        raise VisibleTerminalAdapterError("mt5_set_reference_invalid")
    overrides = (
        dict(fixed_current_overrides)
        if isinstance(fixed_current_overrides, dict)
        else {}
    )
    if fixed_current_overrides is not None and not isinstance(
        fixed_current_overrides, dict
    ):
        raise VisibleTerminalAdapterError("mt5_set_reference_invalid")
    normalized: list[dict] = []
    for ordinal, (entry, declared) in enumerate(zip(raw, manifest["entries"])):
        if not isinstance(entry, dict) or set(entry) != {
            "ordinal",
            "inputName",
            "qualifier",
            "declaredType",
            "valueKind",
            "current",
            "start",
            "step",
            "stop",
            "enabled",
        }:
            raise VisibleTerminalAdapterError("mt5_set_reference_invalid")
        input_name = str(declared["inputName"])
        expected_current = overrides.pop(input_name, declared["setDefault"])
        if (
            entry.get("ordinal") != ordinal
            or entry.get("inputName") != input_name
            or entry.get("qualifier") != declared["qualifier"]
            or entry.get("declaredType") != declared["declaredType"]
            or entry.get("valueKind") != declared["valueKind"]
            or any(
                not isinstance(entry.get(field), str) or not entry.get(field).strip()
                for field in ("current", "start", "step", "stop")
            )
            or type(entry.get("enabled")) is not bool
            or (declared["qualifier"] == "sinput" and entry.get("enabled") is not False)
            or not _semantic_input_value_equal(
                entry.get("current"), expected_current, declared["valueKind"]
            )
        ):
            raise VisibleTerminalAdapterError("mt5_set_reference_invalid")
        normalized.append(copy.deepcopy(entry))
    if overrides:
        raise VisibleTerminalAdapterError("mt5_set_reference_invalid")
    return normalized


def _native_disabled_bool_range_matches(actual: dict, wanted: dict) -> bool:
    """Accept the one range normalization emitted by MT5's native Save.

    MT5 preserves the current value and the disabled flag, but serializes the
    otherwise inactive bool optimization range as false/0/true.  Keep this
    deliberately narrow: the signed source contract must describe a disabled
    default-only bool row, and the native row must use that exact canonical
    range.  Current-value drift is never waived.
    """

    return (
        str(wanted["valueKind"]) == "bool"
        and wanted["enabled"] is False
        and _semantic_input_value_equal(
            wanted["start"], wanted["current"], "bool"
        )
        and _semantic_input_value_equal(wanted["step"], "1", "bool")
        and _semantic_input_value_equal(
            wanted["stop"], wanted["current"], "bool"
        )
        and _semantic_input_value_equal(actual["start"], "false", "bool")
        and _semantic_input_value_equal(actual["step"], "0", "bool")
        and _semantic_input_value_equal(actual["stop"], "true", "bool")
    )


def _assert_set_matches_expected(
    path: Path,
    expected: list[dict],
    *,
    allow_native_disabled_bool_range: bool = False,
) -> str:
    observed = _read_set_entries(path)
    if len(observed) != len(expected):
        raise VisibleTerminalAdapterError("mt5_set_readback_mismatch")
    for actual, wanted in zip(observed, expected):
        identity_or_current_mismatch = (
            actual["inputName"] != wanted["inputName"]
            or actual["enabled"] is not wanted["enabled"]
            or not _semantic_input_value_equal(
                actual["current"], wanted["current"], str(wanted["valueKind"])
            )
        )
        range_matches = all(
            _semantic_input_value_equal(
                actual[field], wanted[field], str(wanted["valueKind"])
            )
            for field in ("start", "step", "stop")
        )
        native_bool_range_matches = (
            allow_native_disabled_bool_range
            and _native_disabled_bool_range_matches(actual, wanted)
        )
        if identity_or_current_mismatch or not (
            range_matches or native_bool_range_matches
        ):
            raise VisibleTerminalAdapterError("mt5_set_readback_mismatch")
    return _sha256_bytes(_canonical_json(expected))


def _validate_set_reference(
    raw: object,
    *,
    workspace: Path,
    manifest: dict,
    code: str,
    fixed_current_overrides: dict[str, str] | None = None,
) -> dict:
    if not isinstance(raw, dict) or set(raw) != {
        "schemaVersion",
        "relativePath",
        "sha256",
        "inputManifestDigest",
        "entryCount",
        "expectedReadbackEntries",
        "expectedReadbackEntriesDigest",
        "refDigest",
    }:
        raise VisibleTerminalAdapterError(code)
    expected = _validate_expected_readback_entries(
        raw.get("expectedReadbackEntries"),
        manifest,
        fixed_current_overrides=fixed_current_overrides,
    )
    core = {
        "schemaVersion": SET_REF_SCHEMA,
        "relativePath": raw.get("relativePath"),
        "sha256": raw.get("sha256"),
        "inputManifestDigest": raw.get("inputManifestDigest"),
        "entryCount": raw.get("entryCount"),
        "expectedReadbackEntries": expected,
        "expectedReadbackEntriesDigest": raw.get("expectedReadbackEntriesDigest"),
    }
    expected_entries_digest = _sha256_bytes(_canonical_json(expected))
    ref_digest = _sha256_bytes(_canonical_json(core))
    if (
        raw.get("schemaVersion") != SET_REF_SCHEMA
        or raw.get("inputManifestDigest") != manifest["manifestDigest"]
        or raw.get("entryCount") != len(expected)
        or raw.get("expectedReadbackEntriesDigest") != expected_entries_digest
        or raw.get("refDigest") != ref_digest
        or SHA256.fullmatch(str(raw.get("sha256") or "")) is None
    ):
        raise VisibleTerminalAdapterError(code)
    path = _managed_path(workspace, raw.get("relativePath"), code)
    path = _resolved_file(path, code, maximum_bytes=MAX_SET_BYTES)
    digest, _ = _stable_digest(path, maximum_bytes=MAX_SET_BYTES)
    if not secrets.compare_digest(digest, str(raw.get("sha256"))):
        raise VisibleTerminalAdapterError(code)
    _assert_set_matches_expected(path, expected)
    return {**copy.deepcopy(raw), "path": str(path)}


def _validate_backtest_set_reference(raw: object, *, workspace: Path) -> tuple[dict, dict]:
    """Validate the bridge's full MT5 default-set binding.

    Backtest requests intentionally do not duplicate the optimization input
    manifest.  The reference itself still carries every ordered source input,
    declared type, qualifier and semantic default.  Its canonical ref digest,
    immutable file digest, and the tester preset's manifest digest bind that
    complete contract without accepting a range subset.
    """

    if not isinstance(raw, dict) or set(raw) != {
        "schemaVersion",
        "relativePath",
        "sha256",
        "inputManifestDigest",
        "entryCount",
        "expectedReadbackEntries",
        "expectedReadbackEntriesDigest",
        "refDigest",
    }:
        raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
    entries = raw.get("expectedReadbackEntries")
    if not isinstance(entries, list) or not (
        1 <= len(entries) <= MT5_INPUT_MANIFEST_MAX_COUNT
    ):
        raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
    normalized: list[dict] = []
    seen: set[str] = set()
    pseudo_manifest_entries: list[dict] = []
    for ordinal, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {
            "ordinal",
            "inputName",
            "qualifier",
            "declaredType",
            "valueKind",
            "current",
            "start",
            "step",
            "stop",
            "enabled",
        }:
            raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
        name = str(entry.get("inputName") or "")
        kind = str(entry.get("valueKind") or "")
        default = entry.get("current")
        if (
            entry.get("ordinal") != ordinal
            or SAFE_INPUT_NAME.fullmatch(name) is None
            or name.casefold() in seen
            or entry.get("qualifier") not in {"input", "sinput"}
            or SAFE_INPUT_NAME.fullmatch(str(entry.get("declaredType") or "")) is None
            or kind not in {"bool", "integer", "decimal", "enum"}
            or any(
                not isinstance(entry.get(field), str) or not entry.get(field).strip()
                for field in ("current", "start", "step", "stop")
            )
            or entry.get("enabled") is not False
            or any(
                not _semantic_input_value_equal(entry[field], expected, kind)
                for field, expected in (
                    ("start", default),
                    ("step", "1"),
                    ("stop", default),
                )
            )
        ):
            raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
        seen.add(name.casefold())
        normalized.append(copy.deepcopy(entry))
        pseudo_manifest_entries.append(
            {
                "ordinal": ordinal,
                "qualifier": entry["qualifier"],
                "declaredType": entry["declaredType"],
                "inputName": name,
                "valueKind": kind,
                "setDefault": default,
                "enumValues": [default] if kind == "enum" else [],
                "optimizable": entry["qualifier"] == "input",
            }
        )
    core = {
        "schemaVersion": SET_REF_SCHEMA,
        "relativePath": raw.get("relativePath"),
        "sha256": raw.get("sha256"),
        "inputManifestDigest": raw.get("inputManifestDigest"),
        "entryCount": raw.get("entryCount"),
        "expectedReadbackEntries": normalized,
        "expectedReadbackEntriesDigest": raw.get("expectedReadbackEntriesDigest"),
    }
    if (
        raw.get("schemaVersion") != SET_REF_SCHEMA
        or SHA256.fullmatch(str(raw.get("sha256") or "")) is None
        or SHA256.fullmatch(str(raw.get("inputManifestDigest") or "")) is None
        or raw.get("entryCount") != len(normalized)
        or raw.get("expectedReadbackEntriesDigest")
        != _sha256_bytes(_canonical_json(normalized))
        or raw.get("refDigest") != _sha256_bytes(_canonical_json(core))
    ):
        raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
    path = _managed_path(workspace, raw.get("relativePath"), "mt5_input_binding_invalid")
    path = _resolved_file(path, "mt5_input_binding_invalid", maximum_bytes=MAX_SET_BYTES)
    digest, _ = _stable_digest(path, maximum_bytes=MAX_SET_BYTES)
    if digest != raw.get("sha256"):
        raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
    _assert_set_matches_expected(path, normalized)
    pseudo_manifest = {
        "schemaVersion": INPUT_MANIFEST_SCHEMA,
        "sourceDigest": None,
        "entries": pseudo_manifest_entries,
        "manifestDigest": raw["inputManifestDigest"],
    }
    return {**copy.deepcopy(raw), "path": str(path)}, pseudo_manifest


def _validate_compiled_deployment(
    raw: object,
    *,
    workspace: Path,
    source: dict,
    target: dict,
) -> dict:
    if not isinstance(raw, dict) or set(raw) != {
        "schemaVersion",
        "deploymentRef",
        "sourceRelativePath",
        "sourceSha256",
        "binaryRelativePath",
        "binarySha256",
        "expertFileName",
        "terminalCandidateId",
        "terminalSelectionRevision",
        "terminalBindingDigest",
        "reuseRequired",
        "bindingDigest",
    }:
        raise VisibleTerminalAdapterError("compiled_deployment_binding_invalid")
    core = {key: raw[key] for key in raw if key != "bindingDigest"}
    deployment_ref = str(raw.get("deploymentRef") or "")
    if (
        raw.get("schemaVersion") != COMPILED_DEPLOYMENT_SCHEMA
        or re.fullmatch(r"mt5deploy_[0-9a-f]{24}", deployment_ref) is None
        or raw.get("sourceSha256") != source["digest"]
        or raw.get("terminalCandidateId") != target["candidateId"]
        or raw.get("terminalSelectionRevision") != target["selectionRevision"]
        or raw.get("terminalBindingDigest") != target["bindingDigest"]
        or raw.get("reuseRequired") is not True
        or raw.get("bindingDigest") != _sha256_bytes(_canonical_json(core))
    ):
        raise VisibleTerminalAdapterError("compiled_deployment_binding_invalid")
    source_path = _managed_path(
        workspace, raw.get("sourceRelativePath"), "compiled_deployment_binding_invalid"
    )
    source_path = _resolved_file(
        source_path, "compiled_deployment_binding_invalid", maximum_bytes=MAX_SOURCE_BYTES
    )
    binary_path = _managed_path(
        workspace, raw.get("binaryRelativePath"), "compiled_deployment_binding_invalid"
    )
    binary_path = _resolved_file(
        binary_path, "compiled_deployment_binding_invalid", maximum_bytes=MAX_BINARY_BYTES
    )
    source_sha, _ = _stable_digest(source_path, maximum_bytes=MAX_SOURCE_BYTES)
    binary_sha, _ = _stable_digest(binary_path, maximum_bytes=MAX_BINARY_BYTES)
    if (
        source_path != source["path"]
        or source_sha != raw.get("sourceSha256")
        or binary_sha != raw.get("binarySha256")
        or binary_path.suffix.casefold() != ".ex5"
        or binary_path.name != raw.get("expertFileName")
        or source_path.with_suffix(".ex5") != binary_path
    ):
        raise VisibleTerminalAdapterError("compiled_deployment_binding_invalid")
    return {
        **copy.deepcopy(raw),
        "sourcePath": source_path,
        "binaryPath": binary_path,
    }


def _mask_mql_comments_and_strings(source_text: str) -> str | None:
    output = list(source_text)
    state = "code"
    index = 0
    while index < len(source_text):
        current = source_text[index]
        following = source_text[index + 1] if index + 1 < len(source_text) else ""
        if state == "code":
            if current == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if current == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if current == '"':
                output[index] = " "
                index += 1
                state = "string"
                continue
        elif state == "line_comment":
            if current in "\r\n":
                state = "code"
            else:
                output[index] = " "
            index += 1
            continue
        elif state == "block_comment":
            if current == "*" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "code"
                continue
            if current not in "\r\n":
                output[index] = " "
            index += 1
            continue
        elif state == "string":
            output[index] = current if current in "\r\n" else " "
            if current == "\\" and index + 1 < len(source_text):
                if source_text[index + 1] not in "\r\n":
                    output[index + 1] = " "
                index += 2
                continue
            if current == '"':
                state = "code"
            elif current in "\r\n":
                return None
            index += 1
            continue
        index += 1
    return "".join(output) if state in {"code", "line_comment"} else None


def _brace_depth_at(code: str, position: int) -> int:
    depth = 0
    for character in code[:position]:
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return -1
    return depth


def _mt5_input_integer_literal(value: str) -> int | None:
    text = str(value or "").strip()
    if re.fullmatch(r"[+-]?(?:0[xX][0-9a-fA-F]+|[0-9]+)", text) is None:
        return None
    try:
        sign = -1 if text.startswith("-") else 1
        unsigned = text[1:] if text[:1] in {"+", "-"} else text
        return sign * int(unsigned, 16 if unsigned.lower().startswith("0x") else 10)
    except ValueError:
        return None


def _mt5_input_decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral_value():
        return str(normalized.quantize(Decimal(1)))
    return format(normalized, "f")


def _mt5_input_enums(code: str) -> dict[str, dict]:
    enum_tokens = list(re.finditer(r"(?i)\benum\b", code))
    enums: dict[str, dict] = {}
    consumed: set[int] = set()
    for token in enum_tokens:
        match = re.match(
            r"(?is)enum[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*"
            r"\{([^{}]*)\}[ \t]*;",
            code[token.start():],
        )
        if match is None or _brace_depth_at(code, token.start()) != 0:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_invalid"
            )
        consumed.add(token.start())
        enum_name = match.group(1)
        if enum_name.casefold() in {name.casefold() for name in enums}:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_invalid"
            )
        members: dict[str, int] = {}
        next_value = 0
        for raw_member in match.group(2).split(","):
            member = raw_member.strip()
            if not member:
                continue
            parsed = re.fullmatch(
                r"([A-Za-z_][A-Za-z0-9_]*)(?:[ \t]*=[ \t]*(.+))?",
                member,
            )
            if parsed is None:
                raise VisibleTerminalAdapterError(
                    "mt5_input_manifest_source_invalid"
                )
            member_name = parsed.group(1)
            if member_name.casefold() in {name.casefold() for name in members}:
                raise VisibleTerminalAdapterError(
                    "mt5_input_manifest_source_invalid"
                )
            if parsed.group(2) is not None:
                explicit = _mt5_input_integer_literal(parsed.group(2))
                if explicit is None:
                    raise VisibleTerminalAdapterError(
                        "mt5_input_manifest_source_invalid"
                    )
                next_value = explicit
            members[member_name] = next_value
            next_value += 1
        if not members:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_invalid"
            )
        enums[enum_name] = {
            "members": members,
            "values": list(dict.fromkeys(members.values())),
        }
    if len(consumed) != len(enum_tokens):
        raise VisibleTerminalAdapterError("mt5_input_manifest_source_invalid")
    return enums


def _mt5_input_source_default(
    declared_type: str,
    literal: str,
    enums: dict[str, dict],
) -> tuple[str, str, list[str]] | None:
    kind = declared_type.casefold()
    token = str(literal or "").strip()
    if kind == "bool":
        folded = token.casefold()
        return ("bool", folded, []) if folded in {"true", "false"} else None
    if kind in MT5_INPUT_INTEGER_TYPES:
        parsed = _mt5_input_integer_literal(token)
        return ("integer", str(parsed), []) if parsed is not None else None
    if kind in MT5_INPUT_DECIMAL_TYPES:
        try:
            parsed_decimal = Decimal(token)
        except (InvalidOperation, ValueError):
            return None
        if not parsed_decimal.is_finite():
            return None
        return "decimal", _mt5_input_decimal_text(parsed_decimal), []
    enum = enums.get(declared_type)
    if not isinstance(enum, dict):
        return None
    members = enum.get("members") if isinstance(enum.get("members"), dict) else {}
    if token not in members:
        return None
    return "enum", str(members[token]), [
        str(value) for value in (enum.get("values") or [])
    ]


def _input_manifest_from_source(source_code: str, source_digest: str) -> dict:
    code = _mask_mql_comments_and_strings(source_code)
    if code is None:
        raise VisibleTerminalAdapterError("mt5_input_manifest_source_invalid")
    enums = _mt5_input_enums(code)
    tokens = list(re.finditer(r"(?i)\b(?:input|sinput)\b", code))
    if not tokens or len(tokens) > MT5_INPUT_MANIFEST_MAX_COUNT:
        raise VisibleTerminalAdapterError("mt5_input_manifest_source_invalid")
    entries: list[dict] = []
    seen_lines: set[int] = set()
    seen_names: set[str] = set()
    for token_match in tokens:
        line_start = code.rfind("\n", 0, token_match.start()) + 1
        line_end = code.find("\n", token_match.end())
        if line_end < 0:
            line_end = len(code)
        if line_start in seen_lines:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_invalid"
            )
        seen_lines.add(line_start)
        line = code[line_start:line_end].rstrip("\r")
        if re.fullmatch(r"[ \t]*input[ \t]+group\b.*", line, re.IGNORECASE):
            continue
        declaration = re.fullmatch(
            r"[ \t]*(input|sinput)[ \t]+([A-Za-z_][A-Za-z0-9_]*)"
            r"[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*"
            r"([^;\r\n]+?)[ \t]*;[ \t]*",
            line,
            re.IGNORECASE,
        )
        if declaration is None or _brace_depth_at(code, line_start) != 0:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_invalid"
            )
        qualifier = declaration.group(1).lower()
        declared_type = declaration.group(2)
        input_name = declaration.group(3)
        folded_name = input_name.casefold()
        if folded_name in seen_names:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_invalid"
            )
        seen_names.add(folded_name)
        parsed_default = _mt5_input_source_default(
            declared_type, declaration.group(4), enums
        )
        if parsed_default is None:
            raise VisibleTerminalAdapterError(
                "mt5_input_manifest_source_invalid"
            )
        value_kind, set_default, enum_values = parsed_default
        entries.append({
            "ordinal": len(entries),
            "qualifier": qualifier,
            "declaredType": declared_type,
            "inputName": input_name,
            "valueKind": value_kind,
            "setDefault": set_default,
            "enumValues": enum_values,
            "optimizable": qualifier == "input",
        })
    if not entries:
        raise VisibleTerminalAdapterError("mt5_input_manifest_source_invalid")
    core = {
        "schemaVersion": INPUT_MANIFEST_SCHEMA,
        "sourceDigest": source_digest,
        "entries": entries,
    }
    return {**core, "manifestDigest": _sha256_bytes(_canonical_json(core))}


def _top_level_void_function_body(code: str, function_name: str) -> str | None:
    pattern = re.compile(
        rf"(?i)\bvoid[ \t]+{re.escape(function_name)}[ \t]*"
        r"\([ \t\r\n]*\)[ \t\r\n]*\{"
    )
    matches = [
        match
        for match in pattern.finditer(code)
        if _brace_depth_at(code, match.start()) == 0
    ]
    if len(matches) != 1:
        return None
    match = matches[0]
    depth = 1
    for index in range(match.end(), len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return code[match.end():index]
            if depth < 0:
                return None
    return None


def _top_level_function_bodies(code: str) -> dict[str, str] | None:
    pattern = re.compile(
        r"(?m)^[ \t]*(?:static[ \t]+)?[A-Za-z_][A-Za-z0-9_]*"
        r"(?:[ \t]*[*&])?[ \t]+([A-Za-z_][A-Za-z0-9_]*)"
        r"[ \t]*\([^;{}]*\)[ \t\r\n]*\{"
    )
    bodies: dict[str, str] = {}
    folded_names: set[str] = set()
    for match in pattern.finditer(code):
        if _brace_depth_at(code, match.start()) != 0:
            continue
        name = match.group(1)
        folded = name.casefold()
        if folded in folded_names:
            return None
        depth = 1
        for index in range(match.end(), len(code)):
            if code[index] == "{":
                depth += 1
            elif code[index] == "}":
                depth -= 1
                if depth == 0:
                    bodies[name] = code[match.end():index]
                    folded_names.add(folded)
                    break
                if depth < 0:
                    return None
        else:
            return None
    return bodies


def _native_entry_submission_present(body: str) -> bool:
    if re.search(
        r"(?i)\b[A-Za-z_][A-Za-z0-9_]*[ \t]*\.[ \t]*"
        r"(?:Buy|Sell|BuyLimit|SellLimit|BuyStop|SellStop|"
        r"BuyStopLimit|SellStopLimit|PositionOpen|OrderOpen)[ \t]*\(",
        body,
    ) is not None:
        return True
    for match in re.finditer(
        r"(?i)\b(?:OrderSend|OrderSendAsync)[ \t]*\([ \t]*"
        r"([A-Za-z_][A-Za-z0-9_]*)?",
        body,
    ):
        request_name = match.group(1)
        if not request_name:
            return True
        before_call = body[:match.start()]
        if re.search(
            rf"(?i)\b{re.escape(request_name)}[ \t]*\.[ \t]*"
            r"(?:position|position_by)[ \t]*=",
            before_call,
        ) is None:
            return True
    return False


def _local_function_calls(body: str, function_names: set[str]) -> set[str]:
    folded = {name.casefold() for name in function_names}
    return {
        match.group(1).casefold()
        for match in re.finditer(
            r"(?<![.A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)[ \t]*\(",
            body,
        )
        if match.group(1).casefold() in folded
    }


def _entry_submission_functions(bodies: dict[str, str]) -> set[str]:
    names = set(bodies)
    hazardous = {
        name.casefold()
        for name, body in bodies.items()
        if _native_entry_submission_present(body)
    }
    changed = True
    while changed:
        changed = False
        for name, body in bodies.items():
            folded = name.casefold()
            if folded in hazardous:
                continue
            if _local_function_calls(body, names) & hazardous:
                hazardous.add(folded)
                changed = True
    return hazardous


def _guarded_tester_simulation(code: str, input_name: str) -> bool:
    if (
        TESTER_SIMULATION_NAME_PATTERN.search(input_name) is None
        or TESTER_SIMULATION_FORBIDDEN_NAME_PATTERN.search(input_name) is not None
    ):
        return False
    on_tick = _top_level_void_function_body(code, "OnTick")
    if on_tick is None:
        return False
    name = re.escape(input_name)
    guard = re.search(
        rf"(?mi)^[ \t]*if[ \t]*\([ \t]*(?:![ \t]*{name}\b|"
        rf"{name}\b[ \t]*==[ \t]*false\b|false\b[ \t]*==[ \t]*{name}\b)"
        r"[ \t]*\)[ \t]*(?:\{[ \t]*)?return[ \t]*;",
        on_tick,
    )
    if guard is None or _brace_depth_at(on_tick, guard.start()) != 0:
        return False
    before_guard = on_tick[:guard.start()]
    previous_line = before_guard.rstrip().splitlines()[-1:] or [""]
    if re.fullmatch(
        r"[ \t]*(?:if|for|while|switch)[ \t]*\([^;{}]*\)[ \t]*|"
        r"[ \t]*else[ \t]*",
        previous_line[0],
        re.IGNORECASE,
    ) is not None:
        return False
    if re.search(
        r"(?is)(?:^|[;{}])[ \t\r\n]*"
        r"(?:if|for|while|switch)[ \t\r\n]*\([^{}]*\)[ \t\r\n]*$|"
        r"(?:^|[;{}])[ \t\r\n]*else[ \t\r\n]*$",
        before_guard,
    ) is not None:
        return False
    if re.search(
        r"(?mi)^[ \t]*#(?:if|ifdef|ifndef|elif|else|endif)\b",
        before_guard,
    ) is not None:
        return False
    # A test-only eligibility override must gate entry execution, not merely
    # appear in dead/late code after an order was already submitted. Existing
    # position-management calls remain allowed before the entry gate.
    bodies = _top_level_function_bodies(code)
    if bodies is None:
        return False
    hazardous_functions = _entry_submission_functions(bodies)
    if (
        _native_entry_submission_present(before_guard)
        or _local_function_calls(before_guard, set(bodies)) & hazardous_functions
    ):
        return False
    for function_name, body in bodies.items():
        if function_name.casefold() == "ontick":
            continue
        if (
            function_name.startswith("On")
            and len(function_name) > 2
            and function_name[2].isupper()
            and (
                _native_entry_submission_present(body)
                or _local_function_calls(body, set(bodies)) & hazardous_functions
            )
        ):
            return False
    return True


def _simulation_reason(input_name: str) -> str:
    if input_name == "FundamentalCriteriaConfirmed":
        return "simulate_external_fundamental_confirmation_for_historical_test_only"
    if input_name == "ExternalBenchmarkUptrendConfirmed":
        return "simulate_external_benchmark_uptrend_for_historical_test_only"
    return "simulate_external_manual_confirmation_for_historical_test_only"


def _tester_value_from_token(token: str, input_type: str) -> bool | int | float:
    if input_type == "bool":
        aliases = {"true": True, "1": True, "false": False, "0": False}
        if token.casefold() in aliases:
            return aliases[token.casefold()]
    elif input_type == "int" and re.fullmatch(r"[+-]?\d{1,20}", token):
        return int(token)
    elif input_type == "double":
        value = float(token)
        if math.isfinite(value):
            return value
    raise VisibleTerminalAdapterError("tester_input_preset_invalid")


def _validate_tester_input_preset(
    raw: object,
    manifest: dict,
    source_code: str,
) -> dict:
    if not isinstance(raw, dict) or set(raw) != {
        "schemaVersion",
        "mode",
        "scope",
        "sourceDigest",
        "inputManifestDigest",
        "assumptions",
        "liveSourceDefaultsPreserved",
        "visibleExpertPropertiesRequired",
        "readbackRequired",
        "liveTradingAllowed",
        "fullCertifiedInputSnapshot",
        "simulationInputNames",
        "presetDigest",
    }:
        raise VisibleTerminalAdapterError("tester_input_preset_invalid")
    assumptions = raw.get("assumptions")
    if not isinstance(assumptions, list) or len(assumptions) != len(manifest["entries"]):
        raise VisibleTerminalAdapterError("tester_input_preset_invalid")
    code = _mask_mql_comments_and_strings(source_code)
    if code is None:
        raise VisibleTerminalAdapterError("tester_input_preset_invalid")
    normalized: list[dict] = []
    expected_simulation_names: list[str] = []
    for item, entry in zip(assumptions, manifest["entries"]):
        if not isinstance(item, dict) or set(item) != {
            "inputName",
            "inputType",
            "sourceDefault",
            "testerValue",
            "reasonCode",
        }:
            raise VisibleTerminalAdapterError("tester_input_preset_invalid")
        expected_type = (
            "bool"
            if entry["valueKind"] == "bool"
            else "double"
            if entry["valueKind"] == "decimal"
            else "int"
        )
        expected_value = _tester_value_from_token(entry["setDefault"], expected_type)
        simulation = bool(
            expected_type == "bool"
            and expected_value is False
            and _guarded_tester_simulation(code, str(entry["inputName"]))
        )
        expected_tester_value = True if simulation else expected_value
        expected_reason = (
            _simulation_reason(str(entry["inputName"]))
            if simulation
            else "reset_to_immutable_source_default_to_prevent_stale_tester_state"
        )
        if (
            item.get("inputName") != entry["inputName"]
            or item.get("inputType") != expected_type
            or item.get("reasonCode") != expected_reason
            or type(item.get("sourceDefault")) is not type(expected_value)
            or type(item.get("testerValue")) is not type(expected_tester_value)
            or item.get("sourceDefault") != expected_value
            or item.get("testerValue") != expected_tester_value
        ):
            raise VisibleTerminalAdapterError("tester_input_preset_invalid")
        if simulation:
            expected_simulation_names.append(str(entry["inputName"]))
        normalized.append(copy.deepcopy(item))
    unsigned = {key: copy.deepcopy(value) for key, value in raw.items() if key != "presetDigest"}
    if (
        raw.get("schemaVersion") != TESTER_INPUT_PRESET_SCHEMA
        or raw.get("mode")
        != (
            "full_immutable_source_snapshot_with_explicit_simulation_assumptions"
            if expected_simulation_names
            else "full_immutable_source_default_snapshot"
        )
        or raw.get("scope") != "mt5_strategy_tester_only"
        or raw.get("sourceDigest") != manifest["sourceDigest"]
        or raw.get("inputManifestDigest") != manifest["manifestDigest"]
        or raw.get("liveSourceDefaultsPreserved") is not True
        or raw.get("visibleExpertPropertiesRequired") is not True
        or raw.get("readbackRequired") is not True
        or raw.get("liveTradingAllowed") is not False
        or raw.get("fullCertifiedInputSnapshot") is not True
        or raw.get("simulationInputNames") != expected_simulation_names
        or raw.get("presetDigest") != _sha256_bytes(_canonical_json(unsigned))
    ):
        raise VisibleTerminalAdapterError("tester_input_preset_invalid")
    return copy.deepcopy(raw)


def _tester_value_token(value: object, input_type: str) -> str:
    if input_type == "bool" and type(value) is bool:
        return "true" if value else "false"
    if input_type == "int" and type(value) is int:
        return str(value)
    if input_type == "double" and type(value) in {int, float}:
        number = float(value)
        if math.isfinite(number):
            return str(number)
    raise VisibleTerminalAdapterError("tester_input_preset_invalid")


def _validate_backtest_binding_against_manifest_and_preset(
    binding: dict,
    manifest: dict,
    preset: dict,
) -> None:
    entries = binding.get("expectedReadbackEntries")
    assumptions = preset.get("assumptions")
    if (
        binding.get("inputManifestDigest") != manifest.get("manifestDigest")
        or not isinstance(entries, list)
        or not isinstance(assumptions, list)
        or len(entries) != len(manifest["entries"])
        or len(assumptions) != len(manifest["entries"])
    ):
        raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
    for ordinal, (entry, declared, assumption) in enumerate(
        zip(entries, manifest["entries"], assumptions)
    ):
        if not isinstance(entry, dict) or not isinstance(assumption, dict):
            raise VisibleTerminalAdapterError("mt5_input_binding_invalid")
        expected_token = _tester_value_token(
            assumption.get("testerValue"), str(assumption.get("inputType") or "")
        )
        if (
            entry.get("ordinal") != ordinal
            or entry.get("inputName") != declared.get("inputName")
            or entry.get("qualifier") != declared.get("qualifier")
            or entry.get("declaredType") != declared.get("declaredType")
            or entry.get("valueKind") != declared.get("valueKind")
            or entry.get("enabled") is not False
            or any(
                not _semantic_input_value_equal(
                    entry.get(field), expected_token, str(declared.get("valueKind") or "")
                )
                for field in ("current", "start", "stop")
            )
            or not _semantic_input_value_equal(
                entry.get("step"), "1", str(declared.get("valueKind") or "")
            )
        ):
            raise VisibleTerminalAdapterError("mt5_input_binding_invalid")


def _validate_tester_settings(raw: object, *, stage_id: str, binary_name: str) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("tester_settings_missing")
    allowed = {
        "schemaVersion",
        "expertFileName",
        "symbolPolicy",
        "symbol",
        "period",
        "model",
        "spreadPolicy",
        "useDate",
        "fromDate",
        "toDate",
        "depositPolicy",
        "visualMode",
        "optimizationEnabled",
        "shutdownTerminalAfterTest",
        "liveTradingAllowed",
        "testerInputPreset",
    }
    required = allowed - {"symbol", "testerInputPreset"}
    if not required.issubset(raw) or not set(raw).issubset(allowed):
        raise VisibleTerminalAdapterError("tester_settings_shape_invalid")
    optimization = stage_id == "optimize"
    visual = stage_id == "backtest_recheck"
    symbol = raw.get("symbol")
    if symbol is not None and SAFE_SYMBOL.fullmatch(str(symbol)) is None:
        raise VisibleTerminalAdapterError("tester_symbol_invalid")
    use_date = raw.get("useDate")
    if use_date is True:
        for key in ("fromDate", "toDate"):
            try:
                datetime.strptime(str(raw.get(key) or ""), "%Y-%m-%d")
            except ValueError as error:
                raise VisibleTerminalAdapterError("tester_date_invalid") from error
        if str(raw["fromDate"]) > str(raw["toDate"]):
            raise VisibleTerminalAdapterError("tester_date_range_invalid")
    elif raw.get("fromDate") is not None or raw.get("toDate") is not None:
        raise VisibleTerminalAdapterError("tester_date_policy_invalid")
    if (
        raw.get("schemaVersion") != TESTER_SETTINGS_SCHEMA
        or raw.get("expertFileName") != binary_name
        or Path(binary_name).suffix.casefold() != ".ex5"
        or raw.get("symbolPolicy")
        not in {"explicit", "current_tester_selection_required"}
        or (raw.get("symbolPolicy") == "explicit" and symbol is None)
        or raw.get("period") not in ALLOWED_PERIODS
        or raw.get("model") not in ALLOWED_MODELS
        or raw.get("spreadPolicy") not in {"current", "fixed"}
        or not isinstance(use_date, bool)
        or raw.get("depositPolicy") != "current_tester_deposit"
        or raw.get("visualMode") is not visual
        or raw.get("optimizationEnabled") is not optimization
        or raw.get("shutdownTerminalAfterTest") is not False
        or raw.get("liveTradingAllowed") is not False
        or (stage_id == "backtest_recheck" and not isinstance(raw.get("testerInputPreset"), dict))
        or (stage_id == "optimize" and raw.get("testerInputPreset") is not None)
    ):
        raise VisibleTerminalAdapterError("tester_settings_policy_invalid")
    return copy.deepcopy(raw)


def _validate_optimization_intent(
    raw: object,
    workspace: Path,
    source_digest: str,
    source_code: str,
) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("optimization_intent_missing")
    required = {
        "schemaVersion",
        "sourceDigest",
        "inputManifest",
        "inputManifestDigest",
        "setFile",
        "setDigest",
        "setRef",
        "baselinePresetRef",
        "testerInputPreset",
        "ranges",
        "rangesDigest",
        "visibleInputsRequired",
        "reportRequired",
        "startOnce",
    }
    allowed = required | {"criterion", "mode"}
    if not required.issubset(raw) or not set(raw).issubset(allowed):
        raise VisibleTerminalAdapterError("optimization_intent_shape_invalid")
    manifest = _validate_input_manifest(
        raw.get("inputManifest"), source_digest, source_code
    )
    if raw.get("inputManifestDigest") != manifest["manifestDigest"]:
        raise VisibleTerminalAdapterError("optimization_input_manifest_changed")
    tester_input_preset = _validate_tester_input_preset(
        raw.get("testerInputPreset"), manifest, source_code
    )
    fixed_current_overrides: dict[str, str] = {}
    for assumption in tester_input_preset["assumptions"]:
        if assumption["sourceDefault"] == assumption["testerValue"]:
            continue
        if (
            type(assumption["sourceDefault"]) is not bool
            or assumption["sourceDefault"] is not False
            or type(assumption["testerValue"]) is not bool
            or assumption["testerValue"] is not True
            or assumption["inputName"]
            not in tester_input_preset["simulationInputNames"]
        ):
            raise VisibleTerminalAdapterError("tester_input_preset_invalid")
        fixed_current_overrides[str(assumption["inputName"])] = "true"
    set_ref = _validate_set_reference(
        raw.get("setRef"),
        workspace=workspace,
        manifest=manifest,
        code="optimization_set_reference_invalid",
        fixed_current_overrides=fixed_current_overrides,
    )
    baseline_ref = _validate_set_reference(
        raw.get("baselinePresetRef"),
        workspace=workspace,
        manifest=manifest,
        code="optimization_baseline_reference_invalid",
        fixed_current_overrides=fixed_current_overrides,
    )
    set_path = set_ref["path"]
    set_digest = set_ref["sha256"]
    if raw.get("setFile") != raw["setRef"].get("relativePath") or raw.get(
        "setDigest"
    ) != set_digest:
        raise VisibleTerminalAdapterError("optimization_set_changed")
    ranges = raw.get("ranges")
    if not isinstance(ranges, list) or not ranges or len(ranges) > 64:
        raise VisibleTerminalAdapterError("optimization_ranges_invalid")
    normalized_ranges: list[dict] = []
    seen: set[str] = set()
    range_keys = {
        "inputName",
        "start",
        "step",
        "stop",
        "enabled",
    }
    typed_range_keys = range_keys | {"sourceDefault", "valueKind"}
    for item in ranges:
        if not isinstance(item, dict) or frozenset(item) not in {
            frozenset(range_keys),
            frozenset(typed_range_keys),
        }:
            raise VisibleTerminalAdapterError("optimization_range_shape_invalid")
        name = str(item.get("inputName") or "")
        if (
            SAFE_INPUT_NAME.fullmatch(name) is None
            or name.casefold() in seen
            or item.get("enabled") is not True
        ):
            raise VisibleTerminalAdapterError("optimization_range_invalid")
        seen.add(name.casefold())
        for field in ("start", "step", "stop"):
            value = item.get(field)
            if isinstance(value, (dict, list, bool)) or value is None or not str(value).strip():
                raise VisibleTerminalAdapterError("optimization_range_value_invalid")
        normalized_ranges.append(copy.deepcopy(item))
    ranges_digest = _sha256_bytes(_canonical_json(normalized_ranges))
    selected = {item["inputName"]: item for item in normalized_ranges}
    for declared, optimized, baseline in zip(
        manifest["entries"],
        set_ref["expectedReadbackEntries"],
        baseline_ref["expectedReadbackEntries"],
    ):
        default = declared["setDefault"]
        value_kind = declared["valueKind"]
        chosen = selected.get(declared["inputName"])
        fixed_override = fixed_current_overrides.get(declared["inputName"])
        effective_current = fixed_override if fixed_override is not None else default
        expected_enabled = chosen is not None
        if (
            (
                chosen is not None
                and "valueKind" in chosen
                and (
                    chosen.get("valueKind") != value_kind
                    or not _semantic_input_value_equal(
                        chosen.get("sourceDefault"), default, value_kind
                    )
                )
            )
            or (chosen is not None and fixed_override is not None)
            or optimized["enabled"] is not expected_enabled
            or not _semantic_input_value_equal(
                optimized["current"], effective_current, value_kind
            )
            or not _semantic_input_value_equal(
                optimized["start"],
                chosen["start"] if chosen else effective_current,
                value_kind,
            )
            or not _semantic_input_value_equal(
                optimized["step"], chosen["step"] if chosen else "1", value_kind
            )
            or not _semantic_input_value_equal(
                optimized["stop"],
                chosen["stop"] if chosen else effective_current,
                value_kind,
            )
            or baseline["enabled"] is not False
            or any(
                not _semantic_input_value_equal(baseline[field], expected, value_kind)
                for field, expected in (
                    ("current", effective_current),
                    ("start", effective_current),
                    ("step", "1"),
                    ("stop", effective_current),
                )
            )
        ):
            raise VisibleTerminalAdapterError("optimization_set_reference_invalid")
    if (
        raw.get("schemaVersion") != OPTIMIZATION_INTENT_SCHEMA
        or raw.get("sourceDigest") != source_digest
        or raw.get("inputManifestDigest") != manifest["manifestDigest"]
        or SHA256.fullmatch(str(raw.get("rangesDigest") or "")) is None
        or not secrets.compare_digest(ranges_digest, str(raw.get("rangesDigest")))
        or raw.get("visibleInputsRequired") is not True
        or raw.get("reportRequired") is not True
        or raw.get("startOnce") is not True
        or raw.get("criterion", "balance_max")
        not in {"balance_max", "profit_factor_max", "drawdown_min", "recovery_factor_max", "sharpe_max"}
        or raw.get("mode", "fast_genetic") not in {"fast_genetic", "complete", "all_symbols_market_watch"}
    ):
        raise VisibleTerminalAdapterError("optimization_intent_invalid")
    normalized = copy.deepcopy(raw)
    normalized["criterion"] = str(raw.get("criterion") or "balance_max")
    normalized["mode"] = str(raw.get("mode") or "fast_genetic")
    normalized["setPath"] = str(set_path)
    normalized["inputManifest"] = manifest
    normalized["testerInputPreset"] = tester_input_preset
    normalized["setRef"] = set_ref
    normalized["baselinePresetRef"] = baseline_ref
    normalized["ranges"] = normalized_ranges
    return normalized


def _decode_report_payload(payload: bytes) -> str:
    candidates = []
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        candidates.extend(("utf-16", "utf-8-sig"))
    else:
        candidates.extend(("utf-8-sig", "utf-16", "cp1252"))
    for encoding in candidates:
        try:
            text = payload.decode(encoding)
        except UnicodeError:
            continue
        folded = text.casefold()
        if (
            "<html" in folded
            or "<!doctype" in folded
            or (
                "<workbook" in folded
                and "urn:schemas-microsoft-com:office:spreadsheet" in folded
            )
        ):
            return text
    raise VisibleTerminalAdapterError("mt5_tester_report_encoding_invalid")


def _decode_report(path: Path) -> str:
    payload, _digest, _size = _stable_single_link_bytes(
        path,
        maximum_bytes=MAX_EVIDENCE_BYTES,
        code="mt5_tester_report_changed_during_read",
    )
    return _decode_report_payload(payload)


_SPREADSHEET_NS = "urn:schemas-microsoft-com:office:spreadsheet"
_OFFICE_NS = "urn:schemas-microsoft-com:office:office"
_SS = f"{{{_SPREADSHEET_NS}}}"
_OFFICE = f"{{{_OFFICE_NS}}}"
_SPREADSHEET_NUMBER = re.compile(
    r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?\Z"
)


def _report_maximum_bytes(path: Path) -> int:
    return (
        MAX_OPTIMIZATION_XML_BYTES
        if path.suffix.casefold() == ".xml"
        else MAX_EVIDENCE_BYTES
    )


def _reject_forbidden_xml_declarations(path: Path) -> None:
    """Reject DTD/entity declarations without loading a large report in memory."""

    try:
        carry = b""
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(64 * 1024), b""):
                window = carry + block
                # Removing NULs makes the ASCII XML declaration tokens visible
                # for UTF-16/UTF-32 as well as UTF-8 without decoding the report.
                folded = window.replace(b"\x00", b"").lower()
                if b"<!doctype" in folded or b"<!entity" in folded:
                    raise VisibleTerminalAdapterError("mt5_optimization_xml_invalid")
                carry = window[-64:]
    except VisibleTerminalAdapterError:
        raise
    except OSError as error:
        raise VisibleTerminalAdapterError("mt5_optimization_xml_invalid") from error


def _spreadsheetml_row_values(
    row_element: ElementTree.Element,
) -> tuple[list[str], list[str]]:
    if (
        row_element.attrib
        or (row_element.text and row_element.text.strip())
        or (row_element.tail and row_element.tail.strip())
    ):
        raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
    cells = list(row_element)
    if (
        len(cells) < 2
        or len(cells) > MAX_OPTIMIZATION_RESULT_COLUMNS
        or any(cell.tag != f"{_SS}Cell" for cell in cells)
    ):
        raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
    values: list[str] = []
    value_types: list[str] = []
    for cell in cells:
        if (
            any(name != f"{_SS}StyleID" for name in cell.attrib)
            or (cell.text and cell.text.strip())
            or (cell.tail and cell.tail.strip())
        ):
            # Native MT5 result cells may carry only a style reference.  Sparse
            # ss:Index cells, formulas and merged cells make row identity
            # ambiguous and are therefore rejected.
            raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
        children = list(cell)
        if len(children) != 1 or children[0].tag != f"{_SS}Data":
            raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
        data = children[0]
        if list(data) or set(data.attrib) != {f"{_SS}Type"}:
            raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
        value_type = str(data.get(f"{_SS}Type") or "")
        if value_type not in {"Number", "String"}:
            raise VisibleTerminalAdapterError("mt5_optimization_xml_type_invalid")
        raw_value = data.text or ""
        if len(raw_value) > MAX_OPTIMIZATION_CELL_CHARS:
            raise VisibleTerminalAdapterError("mt5_optimization_xml_value_too_long")
        value = " ".join(raw_value.split())
        if len(value) > MAX_OPTIMIZATION_CELL_CHARS:
            raise VisibleTerminalAdapterError("mt5_optimization_xml_value_too_long")
        if data.tail and data.tail.strip():
            raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
        if value_type == "Number":
            if _SPREADSHEET_NUMBER.fullmatch(value) is None:
                raise VisibleTerminalAdapterError("mt5_optimization_xml_type_invalid")
            try:
                number = Decimal(value)
            except InvalidOperation as error:
                raise VisibleTerminalAdapterError(
                    "mt5_optimization_xml_type_invalid"
                ) from error
            if not number.is_finite():
                raise VisibleTerminalAdapterError("mt5_optimization_xml_type_invalid")
        values.append(value)
        value_types.append(value_type)
    return values, value_types


def _spreadsheetml_optimization_evidence(
    path: Path, *, intent: dict | None = None
) -> dict:
    """Stream, structurally validate and bind every native MT5 result row."""

    report_digest, report_size = _stable_digest(
        path, maximum_bytes=MAX_OPTIMIZATION_XML_BYTES
    )
    _reject_forbidden_xml_declarations(path)
    grid: list[tuple] = []
    complete_count: int | None = None
    if intent is not None:
        grid, complete_count = _optimization_range_grid(intent)
    all_symbols_mode = bool(
        intent is not None and intent.get("mode") == "all_symbols_market_watch"
    )

    property_values: dict[str, str] = {}
    worksheet_name = ""
    worksheet_count = 0
    properties_count = 0
    table_count = 0
    table_expanded_rows: int | None = None
    table_expanded_columns: int | None = None
    header: list[str] | None = None
    fields: list[str] | None = None
    numeric_columns: set[int] = set()
    range_columns: list[tuple[int, tuple]] = []
    symbol_column: int | None = None
    result_count = 0
    seen_pass_ids: set[int] = set()
    seen_combinations: set[tuple[object, ...]] = set()
    seen_symbols: dict[str, str] = {}
    raw_preview_rows: list[list[str]] = []
    result_preview: list[dict[str, str | int | float]] = []
    stack: list[ElementTree.Element] = []
    before = path.stat(follow_symlinks=False)

    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                opened.st_size != report_size
                or opened.st_size != before.st_size
                or getattr(opened, "st_ino", None) != getattr(before, "st_ino", None)
            ):
                raise VisibleTerminalAdapterError(
                    "evidence_file_changed_during_read"
                )
            for event, element in ElementTree.iterparse(handle, events=("start", "end")):
                if event == "start":
                    stack.append(element)
                    depth = len(stack)
                    parent = stack[-2] if depth > 1 else None
                    if depth == 1 and element.tag != f"{_SS}Workbook":
                        raise VisibleTerminalAdapterError("mt5_optimization_xml_invalid")
                    if depth == 2 and parent is not None:
                        if element.tag == f"{_OFFICE}DocumentProperties":
                            properties_count += 1
                        elif element.tag == f"{_SS}Styles":
                            pass
                        elif element.tag == f"{_SS}Worksheet":
                            worksheet_count += 1
                            if set(element.attrib) != {f"{_SS}Name"}:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_xml_shape_invalid"
                                )
                            worksheet_name = str(
                                element.get(f"{_SS}Name") or ""
                            ).strip()
                        else:
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_xml_shape_invalid"
                            )
                    if (
                        depth > 2
                        and stack[1].tag == f"{_SS}Styles"
                        and not element.tag.startswith(_SS)
                    ):
                        raise VisibleTerminalAdapterError(
                            "mt5_optimization_xml_shape_invalid"
                        )
                    if parent is not None:
                        if (
                            parent.tag == f"{_OFFICE}DocumentProperties"
                            and not element.tag.startswith(_OFFICE)
                        ) or (
                            parent.tag == f"{_SS}Worksheet"
                            and element.tag != f"{_SS}Table"
                        ) or (
                            parent.tag == f"{_SS}Table"
                            and element.tag not in {f"{_SS}Column", f"{_SS}Row"}
                        ) or (
                            parent.tag == f"{_SS}Column"
                        ) or (
                            parent.tag == f"{_SS}Row"
                            and element.tag != f"{_SS}Cell"
                        ) or (
                            parent.tag == f"{_SS}Cell"
                            and element.tag != f"{_SS}Data"
                        ) or parent.tag == f"{_SS}Data":
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_xml_shape_invalid"
                            )
                    if element.tag == f"{_SS}Table":
                        if parent is None or parent.tag != f"{_SS}Worksheet":
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_xml_shape_invalid"
                            )
                        table_count += 1
                        for attribute, value in element.attrib.items():
                            if attribute not in {
                                f"{_SS}ExpandedRowCount",
                                f"{_SS}ExpandedColumnCount",
                            } or len(value) > 9 or re.fullmatch(r"[1-9]\d*", value) is None:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_xml_shape_invalid"
                                )
                            if attribute == f"{_SS}ExpandedRowCount":
                                table_expanded_rows = int(value)
                                if table_expanded_rows > MAX_OPTIMIZATION_RESULT_ROWS + 1:
                                    raise VisibleTerminalAdapterError(
                                        "mt5_optimization_xml_row_count_invalid"
                                    )
                            elif attribute == f"{_SS}ExpandedColumnCount":
                                table_expanded_columns = int(value)
                                if table_expanded_columns > MAX_OPTIMIZATION_RESULT_COLUMNS:
                                    raise VisibleTerminalAdapterError(
                                        "mt5_optimization_xml_shape_invalid"
                                    )
                    elif element.tag == f"{_SS}Row" and (
                        parent is None or parent.tag != f"{_SS}Table"
                    ):
                        raise VisibleTerminalAdapterError(
                            "mt5_optimization_xml_shape_invalid"
                        )
                    elif element.tag == f"{_SS}Cell" and (
                        parent is None or parent.tag != f"{_SS}Row"
                    ):
                        raise VisibleTerminalAdapterError(
                            "mt5_optimization_xml_shape_invalid"
                        )
                    elif element.tag == f"{_SS}Data" and (
                        parent is None or parent.tag != f"{_SS}Cell"
                    ):
                        raise VisibleTerminalAdapterError(
                            "mt5_optimization_xml_shape_invalid"
                        )
                    continue

                if not stack or stack[-1] is not element:
                    raise VisibleTerminalAdapterError(
                        "mt5_optimization_xml_shape_invalid"
                    )
                parent = stack[-2] if len(stack) > 1 else None
                if (
                    element.tag == f"{_OFFICE}DocumentProperties"
                    and parent is not None
                    and parent.tag == f"{_SS}Workbook"
                ):
                    for item in list(element):
                        if (
                            not item.tag.startswith(_OFFICE)
                            or item.attrib
                            or list(item)
                        ):
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_xml_shape_invalid"
                            )
                        name = item.tag[len(_OFFICE) :]
                        raw_value = item.text or ""
                        value = " ".join(raw_value.split())
                        if (
                            len(raw_value) > MAX_OPTIMIZATION_CELL_CHARS
                            or len(value) > MAX_OPTIMIZATION_CELL_CHARS
                            or name in property_values
                        ):
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_xml_identity_mismatch"
                            )
                        property_values[name] = value
                elif (
                    element.tag == f"{_SS}Row"
                    and parent is not None
                    and parent.tag == f"{_SS}Table"
                ):
                    values, value_types = _spreadsheetml_row_values(element)
                    if header is None:
                        folded = [value.casefold() for value in values]
                        if (
                            any(value_type != "String" for value_type in value_types)
                            or any(not value for value in values)
                            or folded[0] != "pass"
                            or not set(folded).intersection(
                                {"result", "profit", "trades"}
                            )
                            or len(set(folded)) != len(folded)
                        ):
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_result_header_missing"
                            )
                        header = values
                        used: set[str] = set()
                        fields = [
                            _result_field_name(label, index, used)
                            for index, label in enumerate(header)
                        ]
                        numeric_result_labels = {
                            "pass",
                            "result",
                            "profit",
                            "expected payoff",
                            "profit factor",
                            "recovery factor",
                            "sharpe ratio",
                            "custom",
                            "equity dd %",
                            "equity drawdown %",
                            "drawdown %",
                            "trades",
                        }
                        numeric_columns = {
                            index
                            for index, label in enumerate(folded)
                            if label in numeric_result_labels
                        }
                        if grid:
                            header_columns = {
                                label: index for index, label in enumerate(header)
                            }
                            for specification in grid:
                                name = specification[0]
                                if name not in header_columns:
                                    raise VisibleTerminalAdapterError(
                                        "mt5_optimization_result_range_mismatch"
                                    )
                                range_columns.append(
                                    (header_columns[name], specification)
                                )
                                if specification[4] in {"integer", "decimal"}:
                                    numeric_columns.add(header_columns[name])
                        if all_symbols_mode:
                            symbol_matches = [
                                index
                                for index, label in enumerate(folded)
                                if label == "symbol"
                            ]
                            if len(symbol_matches) != 1:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_symbol_universe_unverified"
                                )
                            symbol_column = symbol_matches[0]
                        raw_preview_rows.append(copy.deepcopy(values))
                    else:
                        if fields is None or len(values) != len(header):
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_result_row_invalid"
                            )
                        result_count += 1
                        if result_count > MAX_OPTIMIZATION_RESULT_ROWS:
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_xml_row_count_invalid"
                            )
                        required_numeric_columns = {0}.union(
                            column
                            for column, specification in range_columns
                            if specification[4] in {"integer", "decimal"}
                        )
                        if (
                            value_types[0] != "Number"
                            or re.fullmatch(r"\d+", values[0]) is None
                            or any(
                                value_types[index] != "Number"
                                for index in required_numeric_columns
                            )
                            or any(
                                value_types[index] != "Number"
                                and not (
                                    value_types[index] == "String"
                                    and values[index] == ""
                                )
                                for index in numeric_columns
                                - required_numeric_columns
                            )
                        ):
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_result_row_invalid"
                            )
                        pass_id = int(values[0])
                        if pass_id in seen_pass_ids:
                            raise VisibleTerminalAdapterError(
                                "mt5_optimization_result_duplicate_pass"
                            )
                        seen_pass_ids.add(pass_id)
                        symbol: str | None = None
                        if all_symbols_mode:
                            if (
                                symbol_column is None
                                or value_types[symbol_column] != "String"
                                or SAFE_SYMBOL.fullmatch(values[symbol_column]) is None
                            ):
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_symbol_universe_unverified"
                                )
                            symbol = values[symbol_column]
                            folded_symbol = symbol.casefold()
                            prior_symbol = seen_symbols.get(folded_symbol)
                            if prior_symbol is not None and prior_symbol != symbol:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_symbol_universe_unverified"
                                )
                            seen_symbols[folded_symbol] = symbol
                        combination: list[object] = []
                        for column, specification in range_columns:
                            (
                                _name,
                                start,
                                step,
                                stop,
                                value_kind,
                                domain,
                                source_default,
                                count,
                            ) = specification
                            try:
                                value = _optimization_typed_cell_decimal(
                                    values[column],
                                    value_types[column],
                                    value_kind=value_kind,
                                    domain=domain,
                                )
                            except VisibleTerminalAdapterError as error:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_result_range_mismatch"
                                ) from error
                            if all_symbols_mode:
                                if value != source_default:
                                    raise VisibleTerminalAdapterError(
                                        "mt5_optimization_result_range_mismatch"
                                    )
                                combination.append(value)
                                continue
                            try:
                                offset = (value - start) / step
                            except (InvalidOperation, OverflowError) as error:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_result_range_mismatch"
                                ) from error
                            if (
                                not value.is_finite()
                                or value < start
                                or value > stop
                                or offset != offset.to_integral_value()
                            ):
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_result_range_mismatch"
                                )
                            index = int(offset)
                            if index < 0 or index >= count:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_result_range_mismatch"
                                )
                            combination.append(index)
                        if range_columns:
                            combination_key = (
                                (symbol, *combination)
                                if all_symbols_mode
                                else tuple(combination)
                            )
                            if combination_key in seen_combinations:
                                raise VisibleTerminalAdapterError(
                                    "mt5_optimization_result_duplicate_combination"
                                )
                            seen_combinations.add(combination_key)
                        if len(result_preview) < MAX_OPTIMIZATION_PREVIEW_ROWS:
                            raw_preview_rows.append(copy.deepcopy(values))
                            result_preview.append(
                                {
                                    field: _result_scalar(value)
                                    for field, value in zip(
                                        fields, values, strict=True
                                    )
                                }
                            )
                    parent.remove(element)
                    element.clear()
                elif len(stack) > 2 and stack[1].tag == f"{_SS}Styles":
                    element.clear()
                stack.pop()
            handle_after = os.fstat(handle.fileno())
        after = path.stat(follow_symlinks=False)
    except VisibleTerminalAdapterError:
        raise
    except (ElementTree.ParseError, OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError("mt5_optimization_xml_invalid") from error

    final_digest, final_size = _stable_digest(
        path, maximum_bytes=MAX_OPTIMIZATION_XML_BYTES
    )
    if (
        final_digest != report_digest
        or final_size != report_size
        or handle_after.st_size != before.st_size
        or after.st_size != before.st_size
        or handle_after.st_mtime_ns != opened.st_mtime_ns
        or after.st_mtime_ns != before.st_mtime_ns
        or getattr(handle_after, "st_ino", None) != getattr(opened, "st_ino", None)
        or getattr(after, "st_ino", None) != getattr(before, "st_ino", None)
    ):
        raise VisibleTerminalAdapterError("evidence_file_changed_during_read")
    if properties_count != 1 or worksheet_count != 1 or table_count != 1:
        raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
    if worksheet_name != "Tester Optimizator Results":
        raise VisibleTerminalAdapterError("mt5_optimization_xml_identity_mismatch")
    title = property_values.get("Title")
    author = property_values.get("Author")
    company = property_values.get("Company")
    if (
        not title
        or author != "MetaQuotes Ltd."
        or not company
        or "MetaQuotes" not in company
    ):
        raise VisibleTerminalAdapterError("mt5_optimization_xml_identity_mismatch")
    if header is None or fields is None or result_count == 0:
        raise VisibleTerminalAdapterError("mt5_optimization_result_rows_missing")
    if (
        table_expanded_rows is not None
        and table_expanded_rows != result_count + 1
    ) or (
        table_expanded_columns is not None
        and table_expanded_columns != len(header)
    ):
        raise VisibleTerminalAdapterError("mt5_optimization_xml_shape_invalid")
    if intent is not None and intent.get("mode") == "complete" and (
        complete_count is None
        or result_count != complete_count
        or len(seen_combinations) != complete_count
    ):
        raise VisibleTerminalAdapterError("mt5_optimization_pass_count_invalid")
    symbol_universe = None
    symbol_universe_digest = None
    if all_symbols_mode:
        if (
            symbol_column is None
            or not seen_symbols
            or len(seen_symbols) != result_count
            or len(seen_combinations) != result_count
        ):
            raise VisibleTerminalAdapterError(
                "mt5_optimization_symbol_universe_unverified"
            )
        symbol_universe = {
            "schemaVersion": SYMBOL_UNIVERSE_SCHEMA,
            "source": "native_spreadsheetml_symbol_column",
            "symbols": sorted(seen_symbols.values()),
        }
        symbol_universe_digest = _sha256_bytes(_canonical_json(symbol_universe))
    return {
        "title": title,
        "worksheetName": worksheet_name,
        "rows": raw_preview_rows,
        "resultRows": result_preview,
        "dataRowCount": result_count,
        "uniquePassCount": len(seen_pass_ids),
        "uniqueCombinationCount": len(seen_combinations),
        "completeCombinationCount": complete_count,
        "symbolUniverse": symbol_universe,
        "symbolUniverseDigest": symbol_universe_digest,
        "reportSha256": report_digest,
        "reportByteSize": report_size,
    }


def _css_has_unverifiable_visibility(css: str, *, context: str) -> bool:
    """Reject CSS that can make parsed proof differ from browser-visible proof."""

    # MT5's native export uses ordinary font/spacing declarations.  CSS
    # capable of suppressing, moving, painting over, or synthesising proof is
    # rejected rather than guessed at.
    source = re.sub(r"(?s)/\*.*?\*/", "", css).casefold()
    if re.search(r"(?i)@import\b|url\s*\(", source):
        return True
    # A CSS escape in a property name (for example ``opac\69ty``) can hide a
    # declaration from a textual property matcher while the browser decodes
    # it.  Native MT5 uses escapes only in mso-number-format *values*.
    if re.search(r"(?:^|[;{])\s*[^:;{}]*\\[^:;{}]*\s*:", source):
        return True
    declarations = re.findall(r"([a-z-]+)\s*:\s*([^;{}]+)", source)
    allowed_properties = (
        {"font", "height", "width"}
        if context == "inline"
        else {"font", "mso-number-format", "margin"}
    )
    if any(property_name not in allowed_properties for property_name, _ in declarations):
        return True
    if context == "inline" and source.strip() and not declarations:
        return True
    for property_name, raw_value in declarations:
        normalized_value = " ".join(raw_value.split())
        compact_value = re.sub(r"\s+", "", raw_value)
        if property_name in {"width", "height"}:
            size = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(px|pt|%)", compact_value)
            if size is None or not 0 < Decimal(size.group(1)) <= 10_000:
                return True
        if property_name == "font":
            size = re.fullmatch(
                r"([0-9]+(?:\.[0-9]+)?)(px|pt)"
                r"\s+([A-Za-z][A-Za-z0-9 _,\"'-]*)",
                normalized_value,
            )
            if size is None or not 6 <= Decimal(size.group(1)) <= 100:
                return True
            family = re.sub(r"\s*,\s*", ",", size.group(3)).casefold()
            if family not in {"tahoma", "tahoma,arial"}:
                return True
        if property_name == "margin":
            size = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(px|pt|%)", compact_value)
            if size is None or not 0 <= Decimal(size.group(1)) <= 100:
                return True
    return False


_HTML_ALLOWED_ATTRIBUTES = {
    "html": frozenset(),
    "head": frozenset(),
    "title": frozenset(),
    "meta": frozenset({"name", "content"}),
    "style": frozenset({"type"}),
    "body": frozenset(),
    "div": frozenset({"align", "style"}),
    "table": frozenset({"border", "cellpadding", "cellspacing"}),
    "tbody": frozenset(),
    "thead": frozenset(),
    "tfoot": frozenset(),
    "tr": frozenset({"align", "bgcolor"}),
    "td": frozenset({"align", "colspan", "nowrap", "style"}),
    "th": frozenset({"align", "colspan", "nowrap", "style"}),
    "b": frozenset(),
    "strong": frozenset(),
    "span": frozenset({"style"}),
    "p": frozenset({"align", "style"}),
    "br": frozenset(),
    "img": frozenset({"alt", "border", "height", "src", "title", "width"}),
}


def _html_element_contract_valid(
    tag: str, attrs: list[tuple[str, str | None]]
) -> bool:
    normalized_tag = tag.casefold()
    allowed = _HTML_ALLOWED_ATTRIBUTES.get(normalized_tag)
    if allowed is None:
        return False
    names = [str(name).casefold() for name, _ in attrs]
    if len(names) != len(set(names)) or any(name not in allowed for name in names):
        return False
    normalized = {str(name).casefold(): str(value or "") for name, value in attrs}
    align = normalized.get("align")
    if align is not None and align.casefold() not in {"left", "right", "center"}:
        return False
    bgcolor = normalized.get("bgcolor")
    # Native MT5 reports use this third, fixed zebra-row colour on some
    # builds/broker skins.  Keep the allow-list exact so arbitrary colours
    # cannot be used to disguise report evidence.
    if bgcolor is not None and bgcolor.upper() not in {
        "#E5F0FC",
        "#F7F7F7",
        "#FFFFFF",
    }:
        return False
    for integer_name, lower, upper in (
        ("border", 0, 10),
        ("cellpadding", 0, 20),
        ("cellspacing", 0, 20),
        ("colspan", 1, 64),
        ("width", 1, 5_000),
        ("height", 1, 5_000),
    ):
        if integer_name not in normalized:
            continue
        value = normalized[integer_name]
        if re.fullmatch(r"[0-9]+", value) is None or not lower <= int(value) <= upper:
            return False
    if "nowrap" in normalized and normalized["nowrap"]:
        return False
    style = normalized.get("style")
    if style is not None and _css_has_unverifiable_visibility(style, context="inline"):
        return False
    if normalized_tag == "style" and normalized.get("type", "text/css").casefold() not in {
        "",
        "text/css",
    }:
        return False
    if normalized_tag == "meta" and normalized != {
        "name": "generator",
        "content": "strategy tester",
    }:
        return False
    if normalized_tag == "img":
        source = normalized.get("src", "")
        if re.fullmatch(r"[A-Za-z0-9._-]+\.(?:png|gif|jpe?g)", source, re.I) is None:
            return False
        for text_name in ("alt", "title"):
            value = normalized.get(text_name)
            if value is not None and (
                len(value) > 128 or any(ord(character) < 32 for character in value)
            ):
                return False
    return True


def _html_structure_start_valid(
    tag: str,
    stack: list[tuple[str, bool]],
    counts: dict[str, int],
) -> bool:
    normalized = tag.casefold()
    ancestors = [item[0] for item in stack]
    parent = ancestors[-1] if ancestors else None
    if normalized == "html":
        return parent is None and counts["html"] == 0
    if counts["html"] != 1:
        return False
    if normalized == "head":
        return parent == "html" and counts["head"] == 0 and counts["body"] == 0
    if normalized == "body":
        return (
            parent == "html"
            and counts["head"] == 1
            and counts["title"] == 1
            and counts["body"] == 0
        )
    if normalized == "title":
        return parent == "head" and counts["title"] == 0 and counts["body"] == 0
    if normalized in {"meta", "style"}:
        return parent == "head" and counts["body"] == 0
    if counts["body"] != 1 or "body" not in ancestors:
        return False
    if any(item in {"head", "title", "style"} for item in ancestors):
        return False
    allowed_parents = {
        "table": {"body", "div", "td", "th"},
        "tbody": {"table"},
        "thead": {"table"},
        "tfoot": {"table"},
        "tr": {"table", "tbody", "thead", "tfoot"},
        "td": {"tr"},
        "th": {"tr"},
        "div": {"body", "div", "td", "th"},
        "p": {"body", "div", "td", "th"},
        "span": {"body", "div", "td", "th", "p", "span"},
        "b": {"body", "div", "td", "th", "p", "span"},
        "strong": {"body", "div", "td", "th", "p", "span"},
        "br": {"body", "div", "td", "th", "p", "span", "b", "strong"},
        "img": {"body", "div", "td", "th", "p"},
    }
    return parent in allowed_parents.get(normalized, set())


def _html_element_suppressed(
    tag: str,
    attrs: list[tuple[str, str | None]],
    hidden_classes: frozenset[str] = frozenset(),
) -> bool:
    normalized_tag = tag.casefold()
    if normalized_tag in {"script", "style", "template", "noscript"}:
        return True
    normalized = {str(name).casefold(): str(value or "") for name, value in attrs}
    if "hidden" in normalized or normalized.get("aria-hidden", "").casefold() == "true":
        return True
    # Closed details/dialog contents are not browser-visible.  Suppressing the
    # whole subtree is conservative and prevents their hidden table cells from
    # serving as report evidence.
    if normalized_tag in {"details", "dialog"} and "open" not in normalized:
        return True
    classes = {
        item.casefold()
        for item in normalized.get("class", "").split()
        if item.strip()
    }
    if classes.intersection(hidden_classes):
        return True
    style = normalized.get("style", "")
    compact_style = re.sub(r"\s+", "", style.casefold())
    if "display:none" in compact_style or "visibility:hidden" in compact_style:
        return True
    # HTMLParser supplies quoted and unquoted attributes through the same
    # path, so opacity/filter/off-screen tricks cannot bypass the raw regex.
    return _css_has_unverifiable_visibility(style, context="inline")


_HTML_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


def _html_hidden_classes(decoded: str) -> frozenset[str]:
    hidden: set[str] = set()
    for stylesheet in re.findall(
        r"(?is)<style\b[^>]*>(.*?)</style\s*>", decoded
    ):
        stylesheet = re.sub(r"(?s)/\*.*?\*/", "", stylesheet)
        for selector, body in re.findall(r"(?s)([^{}]+)\{([^{}]*)\}", stylesheet):
            normalized_body = re.sub(r"\s+", "", body.casefold())
            if (
                "display:none" not in normalized_body
                and "visibility:hidden" not in normalized_body
            ):
                continue
            hidden.update(
                item.casefold()
                for item in re.findall(r"\.([A-Za-z_][A-Za-z0-9_-]*)", selector)
            )
    return frozenset(hidden)


def _html_has_unverifiable_stylesheet_visibility(decoded: str) -> bool:
    stylesheets = re.findall(r"(?is)<style\b[^>]*>(.*?)</style\s*>", decoded)
    if any(
        _css_has_unverifiable_visibility(sheet, context="stylesheet")
        for sheet in stylesheets
    ):
        return True
    return any(
        re.search(r"(?i)\brel\s*=\s*['\"]?[^>]*\bstylesheet\b", tag)
        is not None
        for tag in re.findall(r"(?is)<link\b[^>]*>", decoded)
    )


class _VisibleTextParser(HTMLParser):
    def __init__(self, hidden_classes: frozenset[str]) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.invalid = False
        self._hidden_classes = hidden_classes
        self._tag_stack: list[tuple[str, bool]] = []
        self.structure_counts = {"html": 0, "head": 0, "title": 0, "body": 0}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.casefold()
        if (
            not _html_element_contract_valid(tag, attrs)
            or not _html_structure_start_valid(
                tag, self._tag_stack, self.structure_counts
            )
        ):
            self.invalid = True
        if normalized in self.structure_counts:
            self.structure_counts[normalized] += 1
        parent_suppressed = bool(self._tag_stack and self._tag_stack[-1][1])
        suppressed = parent_suppressed or _html_element_suppressed(
            tag, attrs, self._hidden_classes
        )
        if normalized not in _HTML_VOID_ELEMENTS:
            self._tag_stack.append((normalized, suppressed))

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if normalized in _HTML_VOID_ELEMENTS:
            self.invalid = True
            return
        if not self._tag_stack or self._tag_stack[-1][0] != normalized:
            self.invalid = True
            return
        self._tag_stack.pop()

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if (
            tag.casefold() not in _HTML_VOID_ELEMENTS
            or not _html_element_contract_valid(tag, attrs)
            or not _html_structure_start_valid(
                tag, self._tag_stack, self.structure_counts
            )
        ):
            self.invalid = True

    def handle_data(self, data: str) -> None:
        if self._tag_stack and self._tag_stack[-1][1]:
            return
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


class _ReportTableParser(HTMLParser):
    """Collect bounded visible table cells from an exported MT5 HTML report."""

    def __init__(self, hidden_classes: frozenset[str]) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.tables: list[list[list[str]]] = []
        self.invalid = False
        self.overflow = False
        self._hidden_classes = hidden_classes
        self._tag_stack: list[tuple[str, bool]] = []
        self.structure_counts = {"html": 0, "head": 0, "title": 0, "body": 0}
        self._table_stack: list[int] = []
        self._row_table_index: int | None = None
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.casefold()
        if (
            not _html_element_contract_valid(tag, attrs)
            or not _html_structure_start_valid(
                tag, self._tag_stack, self.structure_counts
            )
        ):
            self.invalid = True
        if normalized in self.structure_counts:
            self.structure_counts[normalized] += 1
        parent_suppressed = bool(self._tag_stack and self._tag_stack[-1][1])
        suppressed = parent_suppressed or _html_element_suppressed(
            tag, attrs, self._hidden_classes
        )
        if normalized not in _HTML_VOID_ELEMENTS:
            self._tag_stack.append((normalized, suppressed))
        if suppressed:
            return
        if normalized == "table":
            if len(self.tables) >= 128:
                self.overflow = True
                self._table_stack.append(-1)
            else:
                self.tables.append([])
                self._table_stack.append(len(self.tables) - 1)
        elif normalized == "tr" and self._table_stack:
            self._row = []
            self._row_table_index = self._table_stack[-1]
        elif normalized in {"td", "th"} and self._row is not None:
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if (
            (self._tag_stack and self._tag_stack[-1][1])
            or self._cell_parts is None
        ):
            return
        value = " ".join(data.split())
        if value:
            self._cell_parts.append(value)

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if normalized in _HTML_VOID_ELEMENTS:
            self.invalid = True
            return
        if not self._tag_stack or self._tag_stack[-1][0] != normalized:
            self.invalid = True
            return
        _, suppressed = self._tag_stack.pop()
        if suppressed:
            return
        if normalized in {"td", "th"} and self._cell_parts is not None:
            if self._row is not None:
                if len(self._row) >= 96:
                    self.overflow = True
                else:
                    self._row.append(" ".join(self._cell_parts).strip())
            self._cell_parts = None
        elif normalized == "tr" and self._row is not None:
            if any(cell for cell in self._row):
                if len(self.rows) >= 10_000:
                    self.overflow = True
                else:
                    bounded = list(self._row)
                    self.rows.append(bounded)
                    if self._row_table_index is not None and self._row_table_index >= 0:
                        table = self.tables[self._row_table_index]
                        if len(table) >= 10_000:
                            self.overflow = True
                        else:
                            table.append(bounded)
            self._row = None
            self._row_table_index = None
            self._cell_parts = None
        elif normalized == "table" and self._table_stack:
            self._table_stack.pop()

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if (
            tag.casefold() not in _HTML_VOID_ELEMENTS
            or not _html_element_contract_valid(tag, attrs)
            or not _html_structure_start_valid(
                tag, self._tag_stack, self.structure_counts
            )
        ):
            self.invalid = True


def _html_report_evidence_from_payload(payload: bytes) -> dict:
    """Parse one bounded immutable HTML payload with the native MT5 contract."""

    if (
        not isinstance(payload, bytes)
        or not payload
        or len(payload) > MAX_EVIDENCE_BYTES
    ):
        raise VisibleTerminalAdapterError("mt5_tester_report_missing")
    report_digest = _sha256_bytes(payload)
    report_size = len(payload)
    decoded = _decode_report_payload(payload)
    if _html_has_unverifiable_stylesheet_visibility(decoded):
        raise VisibleTerminalAdapterError("mt5_tester_report_html_invalid")
    hidden_classes = _html_hidden_classes(decoded)
    text_parser = _VisibleTextParser(hidden_classes)
    table_parser = _ReportTableParser(hidden_classes)
    try:
        text_parser.feed(decoded)
        text_parser.close()
        table_parser.feed(decoded)
        table_parser.close()
    except (ValueError, TypeError) as error:
        raise VisibleTerminalAdapterError("mt5_tester_report_html_invalid") from error
    if (
        text_parser.invalid
        or table_parser.invalid
        or table_parser.overflow
        or text_parser._tag_stack
        or table_parser._tag_stack
        or table_parser._table_stack
        or table_parser._row is not None
        or table_parser._cell_parts is not None
        or text_parser.structure_counts
        != {"html": 1, "head": 1, "title": 1, "body": 1}
        or table_parser.structure_counts
        != {"html": 1, "head": 1, "title": 1, "body": 1}
    ):
        raise VisibleTerminalAdapterError("mt5_tester_report_html_invalid")
    return {
        # HTMLParser(convert_charrefs=True) already performs the one decode a
        # browser applies.  A second unescape would turn literal visible text
        # such as ``&colon;`` into proof punctuation and create a fail-open.
        "text": "\n".join(text_parser.parts),
        "rows": [list(row) for row in table_parser.rows],
        "tables": [
            [list(row) for row in table[:10_000]] for table in table_parser.tables
        ],
        "reportSha256": report_digest,
        "reportByteSize": report_size,
    }


def _html_report_evidence(path: Path) -> dict:
    """Parse visible text and rows from one stable on-disk HTML snapshot."""

    payload, report_digest, report_size = _stable_single_link_bytes(
        path,
        maximum_bytes=MAX_EVIDENCE_BYTES,
        code="mt5_tester_report_changed_during_read",
    )
    evidence = _html_report_evidence_from_payload(payload)
    if (
        evidence.get("reportSha256") != report_digest
        or evidence.get("reportByteSize") != report_size
    ):
        raise VisibleTerminalAdapterError("mt5_tester_report_changed_during_read")
    # Parsing is intentionally followed by a second stable digest.  Metrics
    # come only from the snapshot above, and a writer that changes/replaces the
    # report while those metrics are derived invalidates the whole proof.
    final_digest, final_size = _stable_digest(
        path, maximum_bytes=MAX_EVIDENCE_BYTES
    )
    if final_size != report_size or not secrets.compare_digest(
        final_digest, report_digest
    ):
        raise VisibleTerminalAdapterError("mt5_tester_report_changed_during_read")
    return evidence


def _report_text(path: Path) -> str:
    if path.suffix.casefold() == ".xml":
        evidence = _spreadsheetml_optimization_evidence(path)
        visible = [
            evidence["title"],
            evidence["worksheetName"],
            *(cell for row in evidence["rows"] for cell in row if cell),
        ]
        return "\n".join(visible)
    return str(_html_report_evidence(path)["text"])


def _report_rows(path: Path) -> list[list[str]]:
    if path.suffix.casefold() == ".xml":
        return copy.deepcopy(_spreadsheetml_optimization_evidence(path)["rows"])
    return copy.deepcopy(_html_report_evidence(path)["rows"])


def _result_field_name(label: str, index: int, used: set[str]) -> str:
    known = {
        "pass": "passNumber",
        "result": "result",
        "profit": "profit",
        "expected payoff": "expectedPayoff",
        "profit factor": "profitFactor",
        "recovery factor": "recoveryFactor",
        "sharpe ratio": "sharpeRatio",
        "custom": "custom",
        "equity dd %": "equityDrawdownPercent",
        "equity drawdown %": "equityDrawdownPercent",
        "drawdown %": "drawdownPercent",
        "trades": "trades",
    }
    folded = " ".join(str(label or "").split()).casefold()
    candidate = known.get(folded)
    if candidate is None:
        raw_label = " ".join(str(label or "").split())
        if SAFE_INPUT_NAME.fullmatch(raw_label):
            # MT5 appends optimized input names to the result columns.  Keep the
            # exact MQL identifier so a result can be joined back to its
            # immutable input range without a lossy case conversion.
            candidate = raw_label
        else:
            words = re.findall(r"[A-Za-z0-9]+", raw_label)
        if candidate is None and words:
            candidate = words[0].casefold() + "".join(
                word[:1].upper() + word[1:] for word in words[1:]
            )
        elif candidate is None:
            candidate = f"field{index + 1}"
        if not candidate or not candidate[0].isalpha():
            candidate = "field" + candidate[:70]
    candidate = candidate[:80]
    base = candidate
    suffix = 2
    while candidate.casefold() in used:
        token = str(suffix)
        candidate = (base[: 80 - len(token)] + token)
        suffix += 1
    used.add(candidate.casefold())
    return candidate


def _result_scalar(value: str) -> str | int | float:
    text = " ".join(str(value or "").split())[:128]
    normalized = text.replace("\u00a0", " ").replace(" ", "")
    if re.fullmatch(r"[-+]?\d+", normalized):
        try:
            number = int(normalized)
            if abs(number) <= 2**53:
                return number
        except ValueError:
            pass
    decimal_candidate = normalized.replace(",", "")
    if re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", decimal_candidate):
        try:
            number = float(decimal_candidate)
            if math.isfinite(number):
                return number
        except ValueError:
            pass
    return text


def _optimization_result_rows(
    path: Path, *, intent: dict | None = None
) -> list[dict[str, str | int | float]]:
    return copy.deepcopy(
        _spreadsheetml_optimization_evidence(path, intent=intent)["resultRows"]
    )


def _optimization_manifest_range_types(intent: dict) -> dict[str, dict]:
    manifest = intent.get("inputManifest")
    if manifest is None:
        return {}
    entries = manifest.get("entries") if isinstance(manifest, dict) else None
    if not isinstance(entries, list) or not entries:
        raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
    result: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        name = str(entry.get("inputName") or "")
        value_kind = str(entry.get("valueKind") or "")
        if (
            SAFE_INPUT_NAME.fullmatch(name) is None
            or name in result
            or value_kind not in {"bool", "integer", "decimal", "enum"}
            or not isinstance(entry.get("setDefault"), str)
        ):
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        result[name] = entry
    return result


def _optimization_domain_decimal(raw: object, value_kind: str) -> Decimal:
    token = str(raw).strip()
    if value_kind == "bool":
        aliases = {
            "false": Decimal(0),
            "0": Decimal(0),
            "true": Decimal(1),
            "1": Decimal(1),
        }
        value = aliases.get(token.casefold())
        if value is None:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_range_lineage_invalid"
            )
        return value
    try:
        value = Decimal(token)
    except (InvalidOperation, ValueError) as error:
        raise VisibleTerminalAdapterError(
            "mt5_optimization_range_lineage_invalid"
        ) from error
    if not value.is_finite() or (
        value_kind in {"integer", "enum"}
        and value != value.to_integral_value()
    ):
        raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
    return value


def _optimization_typed_cell_decimal(
    value: str,
    value_type: str,
    *,
    value_kind: str,
    domain: frozenset[Decimal],
) -> Decimal:
    if value_kind in {"integer", "decimal"}:
        if value_type != "Number":
            raise VisibleTerminalAdapterError("mt5_optimization_result_row_invalid")
        try:
            parsed = Decimal(value)
        except InvalidOperation as error:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_result_row_invalid"
            ) from error
        if not parsed.is_finite() or (
            value_kind == "integer" and parsed != parsed.to_integral_value()
        ):
            raise VisibleTerminalAdapterError("mt5_optimization_result_row_invalid")
        return parsed
    if value_kind == "bool":
        if value_type == "String":
            aliases = {
                "false": Decimal(0),
                "0": Decimal(0),
                "true": Decimal(1),
                "1": Decimal(1),
            }
            parsed = aliases.get(value.casefold())
            if parsed is None:
                raise VisibleTerminalAdapterError(
                    "mt5_optimization_result_row_invalid"
                )
        elif value_type == "Number":
            try:
                parsed = Decimal(value)
            except InvalidOperation as error:
                raise VisibleTerminalAdapterError(
                    "mt5_optimization_result_row_invalid"
                ) from error
        else:
            raise VisibleTerminalAdapterError("mt5_optimization_result_row_invalid")
    elif value_kind == "enum":
        if value_type not in {"Number", "String"}:
            raise VisibleTerminalAdapterError("mt5_optimization_result_row_invalid")
        try:
            parsed = Decimal(value)
        except InvalidOperation as error:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_result_row_invalid"
            ) from error
    else:
        raise VisibleTerminalAdapterError("mt5_optimization_result_row_invalid")
    if not parsed.is_finite() or parsed != parsed.to_integral_value() or parsed not in domain:
        raise VisibleTerminalAdapterError("mt5_optimization_result_row_invalid")
    return parsed


def _optimization_range_grid(
    intent: dict,
) -> tuple[
    list[
        tuple[
            str,
            Decimal,
            Decimal,
            Decimal,
            str,
            frozenset[Decimal],
            Decimal,
            int,
        ]
    ],
    int,
]:
    ranges = intent.get("ranges")
    if not isinstance(ranges, list) or not ranges:
        raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
    manifest_types = _optimization_manifest_range_types(intent)
    grid: list[
        tuple[
            str,
            Decimal,
            Decimal,
            Decimal,
            str,
            frozenset[Decimal],
            Decimal,
            int,
        ]
    ] = []
    total = 1
    for item in ranges:
        if not isinstance(item, dict):
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        name = str(item.get("inputName") or "")
        declared = manifest_types.get(name)
        if manifest_types and declared is None:
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        value_kind = str(
            (declared or {}).get("valueKind")
            or item.get("valueKind")
            or "decimal"
        )
        if value_kind not in {"bool", "integer", "decimal", "enum"}:
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        if "valueKind" in item and item.get("valueKind") != value_kind:
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        try:
            start = Decimal(str(item.get("start")))
            step = Decimal(str(item.get("step")))
            stop = Decimal(str(item.get("stop")))
        except (InvalidOperation, ValueError) as error:
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid") from error
        if (
            SAFE_INPUT_NAME.fullmatch(name) is None
            or not start.is_finite()
            or not step.is_finite()
            or not stop.is_finite()
            or step <= 0
            or stop < start
        ):
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        if value_kind in {"bool", "integer", "enum"} and any(
            value != value.to_integral_value() for value in (start, step, stop)
        ):
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        if value_kind == "bool":
            domain = frozenset({Decimal(0), Decimal(1)})
        elif value_kind == "enum":
            enum_values = (declared or {}).get("enumValues")
            if not isinstance(enum_values, list) or not enum_values:
                raise VisibleTerminalAdapterError(
                    "mt5_optimization_range_lineage_invalid"
                )
            domain = frozenset(
                _optimization_domain_decimal(value, "enum") for value in enum_values
            )
            if len(domain) != len(enum_values):
                raise VisibleTerminalAdapterError(
                    "mt5_optimization_range_lineage_invalid"
                )
        else:
            domain = frozenset()
        source_default = _optimization_domain_decimal(
            (declared or {}).get("setDefault", item.get("sourceDefault", start)),
            value_kind,
        )
        if "sourceDefault" in item and not _semantic_input_value_equal(
            item.get("sourceDefault"), source_default, value_kind
        ):
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        if domain and source_default not in domain:
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        try:
            step_count = (stop - start) / step
            if not step_count.is_finite() or step_count > 99_999:
                raise VisibleTerminalAdapterError(
                    "mt5_optimization_range_lineage_invalid"
                )
            count = int(step_count.to_integral_value(rounding=ROUND_FLOOR)) + 1
        except (InvalidOperation, OverflowError, ValueError) as error:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_range_lineage_invalid"
            ) from error
        if count < 1 or count > 100_000 or total > 100_000 // count:
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        if domain and any(
            start + (step * index) not in domain for index in range(count)
        ):
            raise VisibleTerminalAdapterError("mt5_optimization_range_lineage_invalid")
        total *= count
        grid.append(
            (
                name,
                start,
                step,
                stop,
                value_kind,
                domain,
                source_default,
                count,
            )
        )
    return grid, total


def _normalized_report_cell_label(value: object) -> str:
    return " ".join(str(value or "").split()).rstrip(":").strip().casefold()


def _report_nonempty_cells(row: list[str]) -> list[str]:
    return [" ".join(str(cell or "").split()) for cell in row if str(cell or "").strip()]


def _report_standalone_row(
    rows: list[list[str]], label: str, *, code: str
) -> int:
    normalized = _normalized_report_cell_label(label)
    matches = [
        index
        for index, row in enumerate(rows)
        if [_normalized_report_cell_label(cell) for cell in _report_nonempty_cells(row)]
        == [normalized]
    ]
    if len(matches) != 1:
        raise VisibleTerminalAdapterError(code)
    return matches[0]


def _report_unique_pair(
    rows: list[list[str]],
    labels: frozenset[str],
    *,
    start: int,
    stop: int,
    code: str,
) -> tuple[int, str, str]:
    normalized_labels = {
        _normalized_report_cell_label(label) for label in labels
    }
    matches: list[tuple[int, str, str]] = []
    for index in range(start, stop):
        cells = _report_nonempty_cells(rows[index])
        normalized_cells = [_normalized_report_cell_label(cell) for cell in cells]
        label_positions = [
            cell_index
            for cell_index, normalized in enumerate(normalized_cells)
            if normalized in normalized_labels
        ]
        if not label_positions:
            continue
        if (
            label_positions != [0]
            or len(cells) != 2
            or normalized_cells[0] not in normalized_labels
            or not cells[1]
        ):
            raise VisibleTerminalAdapterError(code)
        matches.append((index, normalized_cells[0], cells[1]))
    if len(matches) != 1:
        raise VisibleTerminalAdapterError(code)
    return matches[0]


def _report_unique_label_value(
    rows: list[list[str]],
    label: str,
    *,
    start: int,
    stop: int,
    value_pattern: str,
    code: str,
) -> tuple[int, int, str]:
    normalized_label = _normalized_report_cell_label(label)
    matches: list[tuple[int, int, str]] = []
    for row_index in range(start, stop):
        cells = _report_nonempty_cells(rows[row_index])
        normalized_cells = [_normalized_report_cell_label(cell) for cell in cells]
        for cell_index, normalized in enumerate(normalized_cells):
            if normalized != normalized_label:
                continue
            if cell_index + 1 >= len(cells):
                raise VisibleTerminalAdapterError(code)
            value = cells[cell_index + 1]
            if re.fullmatch(value_pattern, value, re.I) is None:
                raise VisibleTerminalAdapterError(code)
            matches.append((row_index, cell_index, value))
    if len(matches) != 1:
        raise VisibleTerminalAdapterError(code)
    return matches[0]


_CANONICAL_REPORT_INTEGER = (
    r"(?:0|[1-9][0-9]*|"
    r"[1-9][0-9]{0,2}(?:,[0-9]{3})+|"
    r"[1-9][0-9]{0,2}(?: [0-9]{3})+)"
)


def _parse_canonical_report_integer(value: str, *, code: str) -> int:
    normalized = " ".join(str(value or "").split())
    if re.fullmatch(_CANONICAL_REPORT_INTEGER, normalized) is None:
        raise VisibleTerminalAdapterError(code)
    return int(normalized.replace(",", "").replace(" ", ""))


def _native_mt5_report_contract(evidence: dict, resolved: dict) -> dict:
    """Bind one broker-branded native MT5 report to exact table evidence.

    Product words in headings or scripts are not identity evidence.  A report
    is accepted only when a single main table has the native MT5 section order,
    unique exact identity rows, and the MT5-only results layout.  This keeps an
    MT4 report, a secondary label bag, or duplicate/prefix identity rows from
    satisfying the verifier.
    """

    code = "mt5_tester_report_identity_mismatch"
    tables = evidence.get("tables")
    if not isinstance(tables, list):
        raise VisibleTerminalAdapterError(code)
    main_tables: list[tuple[int, list[list[str]]]] = []
    for table_index, table in enumerate(tables):
        if not isinstance(table, list):
            continue
        heading_rows = [
            row
            for row in table
            if [
                _normalized_report_cell_label(cell)
                for cell in _report_nonempty_cells(row)
            ]
            == ["strategy tester report"]
        ]
        if heading_rows:
            main_tables.append((table_index, table))
    if len(main_tables) != 1:
        raise VisibleTerminalAdapterError(code)
    main_table_index, rows = main_tables[0]

    # No secondary table may carry another proof label/value pair.  Native
    # detail tables may legitimately contain a multi-column ``Symbol`` header,
    # so Symbol is rejected externally only when shaped as an identity pair.
    external_forbidden_labels = {
        "strategy tester report",
        "settings",
        "results",
        "expert",
        "period",
        "inputs",
        "parameters",
        "history quality",
        "bars",
        "ticks",
        "symbols",
        "balance drawdown absolute",
        "equity drawdown absolute",
        "balance drawdown maximal",
        "equity drawdown maximal",
        "balance drawdown relative",
        "equity drawdown relative",
        "ontester result",
        "total trades",
        "short trades (won %)",
        "long trades (won %)",
        "total deals",
    }
    for table_index, table in enumerate(tables):
        if table_index == main_table_index or not isinstance(table, list):
            continue
        for row in table:
            cells = _report_nonempty_cells(row)
            normalized_cells = [
                _normalized_report_cell_label(cell) for cell in cells
            ]
            if any(label in external_forbidden_labels for label in normalized_cells):
                raise VisibleTerminalAdapterError(code)
            if (
                len(normalized_cells) == 2
                and normalized_cells[0] == "symbol"
                and cells[1]
            ):
                raise VisibleTerminalAdapterError(code)
    heading_index = _report_standalone_row(
        rows, "Strategy Tester Report", code=code
    )
    if heading_index != 0:
        raise VisibleTerminalAdapterError(code)

    standalone_builds: list[tuple[int, str, int]] = []
    for index, row in enumerate(rows):
        cells = _report_nonempty_cells(row)
        if len(cells) != 1:
            continue
        build_match = re.fullmatch(
            r"\S(?:.*\S)?\s*\(build\s+([1-9][0-9]{3,5})\)",
            cells[0],
            re.I,
        )
        if build_match is not None:
            standalone_builds.append((index, cells[0], int(build_match.group(1))))
    if len(standalone_builds) != 1:
        raise VisibleTerminalAdapterError(code)
    build_index, build_heading, build_number = standalone_builds[0]
    settings_index = _report_standalone_row(rows, "Settings", code=code)
    results_index = _report_standalone_row(rows, "Results", code=code)
    if not heading_index < build_index < settings_index < results_index:
        raise VisibleTerminalAdapterError(code)

    mt4_markers = {
        "bars in test",
        "ticks modelled",
        "modelling quality",
    }
    if any(
        _normalized_report_cell_label(cell) in mt4_markers
        for row in rows
        for cell in row
    ):
        raise VisibleTerminalAdapterError(code)

    expert_row, _, expert_value = _report_unique_pair(
        rows,
        frozenset({"Expert"}),
        start=0,
        stop=len(rows),
        code=code,
    )
    symbol_row, _, symbol_value = _report_unique_pair(
        rows,
        frozenset({"Symbol"}),
        start=0,
        stop=len(rows),
        code=code,
    )
    period_row, _, period_value = _report_unique_pair(
        rows,
        frozenset({"Period"}),
        start=0,
        stop=len(rows),
        code=code,
    )
    inputs_row, _, first_input = _report_unique_pair(
        rows,
        frozenset({"Inputs", "Parameters"}),
        start=0,
        stop=len(rows),
        code=code,
    )
    if not settings_index < expert_row < symbol_row < period_row < inputs_row < results_index:
        raise VisibleTerminalAdapterError(code)

    expected_expert = Path(str(resolved.get("expertFileName") or "")).stem
    expected_symbol = str(resolved.get("symbol") or "")
    expected_period = str(resolved.get("period") or "").upper()
    if (
        not expected_expert
        or not expected_symbol
        or not expected_period
        or expert_value.casefold() != expected_expert.casefold()
        or symbol_value.casefold() != expected_symbol.casefold()
    ):
        raise VisibleTerminalAdapterError(code)
    period_match = re.fullmatch(
        rf"{re.escape(expected_period)}(?:\s+\(([0-9]{{4}}\.[0-9]{{2}}\.[0-9]{{2}})"
        rf"\s+-\s+([0-9]{{4}}\.[0-9]{{2}}\.[0-9]{{2}})\))?",
        period_value,
        re.I,
    )
    if period_match is None:
        raise VisibleTerminalAdapterError(code)
    if resolved.get("useDate") is True:
        expected_from = str(resolved.get("fromDate") or "").replace("-", ".")
        expected_to = str(resolved.get("toDate") or "").replace("-", ".")
        if (
            not expected_from
            or not expected_to
            or period_match.group(1) != expected_from
            or period_match.group(2) != expected_to
        ):
            raise VisibleTerminalAdapterError(code)

    input_values = [first_input]
    for row in rows[inputs_row + 1 : results_index]:
        if len(row) >= 2 and not str(row[0] or "").strip():
            continuations = _report_nonempty_cells(row[1:])
            if len(continuations) != 1:
                raise VisibleTerminalAdapterError(code)
            input_values.append(continuations[0])
            continue
        break
    input_text = "; ".join(input_values)

    metric_start = 0
    metric_stop = len(rows)
    history = _report_unique_label_value(
        rows,
        "History Quality",
        start=metric_start,
        stop=metric_stop,
        value_pattern=r"(?:100(?:\.0+)?|[0-9]{1,2}(?:\.[0-9]+)?)%",
        code=code,
    )
    integer_pattern = _CANONICAL_REPORT_INTEGER
    bars = _report_unique_label_value(
        rows, "Bars", start=metric_start, stop=metric_stop,
        value_pattern=integer_pattern, code=code,
    )
    ticks = _report_unique_label_value(
        rows, "Ticks", start=metric_start, stop=metric_stop,
        value_pattern=integer_pattern, code=code,
    )
    symbols = _report_unique_label_value(
        rows, "Symbols", start=metric_start, stop=metric_stop,
        value_pattern=integer_pattern, code=code,
    )
    if not (
        bars[0] == ticks[0] == symbols[0]
        and bars[1] < ticks[1] < symbols[1]
    ):
        raise VisibleTerminalAdapterError(code)

    number = rf"{_CANONICAL_REPORT_INTEGER}(?:\.[0-9]+)?"
    percent = r"(?:100(?:\.0+)?|[0-9]{1,2}(?:\.[0-9]+)?)%"
    absolute_balance = _report_unique_label_value(
        rows, "Balance Drawdown Absolute", start=metric_start, stop=metric_stop,
        value_pattern=number, code=code,
    )
    absolute_equity = _report_unique_label_value(
        rows, "Equity Drawdown Absolute", start=metric_start, stop=metric_stop,
        value_pattern=number, code=code,
    )
    maximal_balance = _report_unique_label_value(
        rows, "Balance Drawdown Maximal", start=metric_start, stop=metric_stop,
        value_pattern=rf"{number}\s*\(\s*{percent}\s*\)", code=code,
    )
    maximal_equity = _report_unique_label_value(
        rows, "Equity Drawdown Maximal", start=metric_start, stop=metric_stop,
        value_pattern=rf"{number}\s*\(\s*{percent}\s*\)", code=code,
    )
    relative_balance = _report_unique_label_value(
        rows, "Balance Drawdown Relative", start=metric_start, stop=metric_stop,
        value_pattern=rf"{percent}\s*\(\s*{number}\s*\)", code=code,
    )
    relative_equity = _report_unique_label_value(
        rows, "Equity Drawdown Relative", start=metric_start, stop=metric_stop,
        value_pattern=rf"{percent}\s*\(\s*{number}\s*\)", code=code,
    )
    for balance, equity in (
        (absolute_balance, absolute_equity),
        (maximal_balance, maximal_equity),
        (relative_balance, relative_equity),
    ):
        if balance[0] != equity[0] or balance[1] >= equity[1]:
            raise VisibleTerminalAdapterError(code)

    ontester = _report_unique_label_value(
        rows, "OnTester result", start=metric_start, stop=metric_stop,
        value_pattern=r"[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][-+]?[0-9]+)?",
        code=code,
    )
    total_trades = _report_unique_label_value(
        rows, "Total Trades", start=metric_start, stop=metric_stop,
        value_pattern=integer_pattern, code=code,
    )
    short_trades = _report_unique_label_value(
        rows, "Short Trades (won %)", start=metric_start, stop=metric_stop,
        value_pattern=rf"{integer_pattern}\s*\(\s*{percent}\s*\)", code=code,
    )
    long_trades = _report_unique_label_value(
        rows, "Long Trades (won %)", start=metric_start, stop=metric_stop,
        value_pattern=rf"{integer_pattern}\s*\(\s*{percent}\s*\)", code=code,
    )
    total_deals = _report_unique_label_value(
        rows, "Total Deals", start=metric_start, stop=metric_stop,
        value_pattern=integer_pattern, code=code,
    )
    if not (
        total_trades[0] == short_trades[0] == long_trades[0]
        and total_trades[1] < short_trades[1] < long_trades[1]
        and total_deals[0] > total_trades[0]
    ):
        raise VisibleTerminalAdapterError(code)
    if not (
        results_index
        < history[0]
        <= bars[0]
        < absolute_balance[0]
        < maximal_balance[0]
        < relative_balance[0]
        < ontester[0]
        < total_trades[0]
        < total_deals[0]
    ):
        raise VisibleTerminalAdapterError(code)

    return {
        "rows": copy.deepcopy(rows),
        "inputsText": input_text,
        "buildHeading": build_heading,
        "buildNumber": build_number,
    }


def _report_summary_count(
    rows: list[list[str]],
    *,
    labels: frozenset[str],
    percentage_suffix_allowed: bool,
    code: str,
) -> int:
    normalized_labels = {
        _normalized_report_cell_label(label) for label in labels
    }
    matches: list[int] = []
    for row in rows:
        for index, cell in enumerate(row):
            if _normalized_report_cell_label(cell) not in normalized_labels:
                continue
            if index + 1 >= len(row):
                raise VisibleTerminalAdapterError(code)
            value = " ".join(str(row[index + 1] or "").split())
            if percentage_suffix_allowed:
                match = re.fullmatch(
                    rf"({_CANONICAL_REPORT_INTEGER})"
                    r"(?:\s*\(\s*([0-9]+(?:\.[0-9]+)?)%\s*\))?",
                    value,
                )
                if match is not None and match.group(2) is not None:
                    try:
                        percentage = Decimal(match.group(2))
                    except InvalidOperation as error:
                        raise VisibleTerminalAdapterError(code) from error
                    if not percentage.is_finite() or not 0 <= percentage <= 100:
                        raise VisibleTerminalAdapterError(code)
            else:
                match = re.fullmatch(rf"({_CANONICAL_REPORT_INTEGER})", value)
            if match is None:
                raise VisibleTerminalAdapterError(code)
            matches.append(_parse_canonical_report_integer(match.group(1), code=code))
    if len(matches) != 1:
        raise VisibleTerminalAdapterError(code)
    return matches[0]


def _tester_report_preset_matches(parameters: str, preset: dict) -> bool:
    assumptions = preset.get("assumptions") if isinstance(preset, dict) else None
    if not isinstance(assumptions, list) or not assumptions:
        return False
    if not isinstance(parameters, str) or not parameters.strip():
        return False
    for item in assumptions:
        if not isinstance(item, dict):
            return False
        name = str(item.get("inputName") or "")
        matches = re.findall(
            rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*=\s*([^\s;,<]+)",
            parameters,
        )
        if len(matches) != 1:
            return False
        try:
            observed = _tester_value_from_token(
                matches[0], str(item.get("inputType") or "")
            )
        except VisibleTerminalAdapterError:
            return False
        expected = item.get("testerValue")
        if type(observed) is not type(expected):
            return False
        if isinstance(expected, float):
            if not math.isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-12):
                return False
        elif observed != expected:
            return False
    return True


def _backtest_attention_fields(zero_trade: bool, mismatched_chart_errors: int) -> dict:
    history_quality_issue = mismatched_chart_errors > 0
    if zero_trade and history_quality_issue:
        reason = "backtest_zero_trades_and_history_quality_errors"
        outcome = "completed_zero_trades_with_history_quality_errors"
    elif zero_trade:
        reason = "backtest_zero_trades"
        outcome = "completed_zero_trades"
    elif history_quality_issue:
        reason = "backtest_history_quality_errors"
        outcome = "completed_with_trades_history_quality_errors"
    else:
        reason = None
        outcome = "completed_with_trades"
    attention_required = bool(zero_trade or history_quality_issue)
    return {
        "mismatchedChartErrors": mismatched_chart_errors,
        "historyQualityIssue": history_quality_issue,
        "historyQualityVerified": not history_quality_issue,
        "attentionRequired": attention_required,
        "attentionReasonCode": reason,
        "performanceEvaluationAvailable": not attention_required,
        "executionOutcome": outcome,
    }


def _validate_optimization_symbol_universe(
    raw: object,
    digest: object,
    *,
    required: bool,
    result_rows: object = None,
    complete_result_rows: bool = False,
) -> dict | None:
    if not required:
        if raw is not None or digest is not None:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_symbol_universe_unverified"
            )
        return None
    if not isinstance(raw, dict) or set(raw) != {
        "schemaVersion",
        "source",
        "symbols",
    }:
        raise VisibleTerminalAdapterError(
            "mt5_optimization_symbol_universe_unverified"
        )
    symbols = raw.get("symbols")
    if (
        raw.get("schemaVersion") != SYMBOL_UNIVERSE_SCHEMA
        or raw.get("source") != "native_spreadsheetml_symbol_column"
        or not isinstance(symbols, list)
        or not symbols
        or len(symbols) > MAX_OPTIMIZATION_RESULT_ROWS
        or any(
            not isinstance(symbol, str)
            or SAFE_SYMBOL.fullmatch(symbol) is None
            for symbol in symbols
        )
        or symbols != sorted(symbols)
        or len({symbol.casefold() for symbol in symbols}) != len(symbols)
        or SHA256.fullmatch(str(digest or "")) is None
        or not secrets.compare_digest(
            _sha256_bytes(_canonical_json(raw)), str(digest)
        )
    ):
        raise VisibleTerminalAdapterError(
            "mt5_optimization_symbol_universe_unverified"
        )
    if result_rows is not None:
        if not isinstance(result_rows, list) or any(
            not isinstance(row, dict)
            or not isinstance(row.get("Symbol"), str)
            or row.get("Symbol") not in symbols
            for row in result_rows
        ):
            raise VisibleTerminalAdapterError(
                "mt5_optimization_symbol_universe_unverified"
            )
        if complete_result_rows and sorted(
            str(row["Symbol"]) for row in result_rows
        ) != symbols:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_symbol_universe_unverified"
            )
    return copy.deepcopy(raw)


def _verify_mt5_tester_report_evidence(
    html_evidence: dict,
    resolved: object,
    preset: object,
) -> dict:
    """Verify parsed native MT5 evidence against one resolved tester request."""

    if not isinstance(resolved, dict):
        raise VisibleTerminalAdapterError("mt5_tester_settings_missing")
    if not isinstance(html_evidence, dict):
        raise VisibleTerminalAdapterError("mt5_tester_report_html_invalid")
    text = str(html_evidence["text"])
    contract = _native_mt5_report_contract(html_evidence, resolved)
    if not isinstance(preset, dict) or not _tester_report_preset_matches(
        str(contract["inputsText"]), preset
    ):
        raise VisibleTerminalAdapterError("mt5_tester_report_input_preset_mismatch")
    rows = copy.deepcopy(contract["rows"])
    trade_count = _report_summary_count(
        rows,
        labels=frozenset({"Total Trades"}),
        percentage_suffix_allowed=False,
        code="mt5_tester_report_trade_count_missing",
    )
    buy_count = _report_summary_count(
        rows,
        labels=frozenset({"Long Trades (won %)", "Long Positions"}),
        percentage_suffix_allowed=True,
        code="mt5_tester_report_trade_rows_mismatch",
    )
    sell_count = _report_summary_count(
        rows,
        labels=frozenset({"Short Trades (won %)", "Short Positions"}),
        percentage_suffix_allowed=True,
        code="mt5_tester_report_trade_rows_mismatch",
    )
    if buy_count + sell_count != trade_count:
        raise VisibleTerminalAdapterError("mt5_tester_report_trade_rows_mismatch")
    mismatch = re.search(
        r"(?is)Mismatched\s+Charts?\s+Errors?\s*[:\r\n ]+\s*([0-9][0-9, ]*)",
        text,
    )
    mismatched_chart_errors = (
        int(mismatch.group(1).replace(",", "").replace(" ", ""))
        if mismatch is not None
        else 0
    )
    attention = _backtest_attention_fields(
        trade_count == 0, mismatched_chart_errors
    )
    return {
        "backtestVerified": True,
        "testerTradeRowsVerified": True,
        "testerInputPresetReportVerified": True,
        "tradeCount": trade_count,
        "tradeRowCount": trade_count,
        "buyTradeCount": buy_count,
        "sellTradeCount": sell_count,
        "zeroTrade": trade_count == 0,
        **attention,
        "reportSha256": html_evidence["reportSha256"],
    }


def verify_mt5_tester_report_payload(
    payload: bytes,
    *,
    resolved_tester_settings: object,
    tester_input_preset: object,
) -> dict:
    """Verify immutable native MT5 report bytes without weakening HTML checks."""

    return _verify_mt5_tester_report_evidence(
        _html_report_evidence_from_payload(payload),
        resolved_tester_settings,
        tester_input_preset,
    )


def verify_mt5_tester_report(context: dict) -> dict:
    """Verify one exported MT5 backtest report against visible UI readback."""

    if not isinstance(context, dict) or context.get("platform") != "mt5":
        raise VisibleTerminalAdapterError("mt5_tester_verifier_context_invalid")
    report = _resolved_file(
        context.get("testerReportPath"),
        "mt5_tester_report_missing",
        maximum_bytes=MAX_EVIDENCE_BYTES,
    )
    return _verify_mt5_tester_report_evidence(
        _html_report_evidence(report),
        context.get("resolvedTesterSettings"),
        context.get("testerInputPreset"),
    )


def verify_mt5_optimization_report(context: dict) -> dict:
    """Verify a native MT5 SpreadsheetML optimization export and range lineage."""

    if not isinstance(context, dict) or context.get("platform") != "mt5":
        raise VisibleTerminalAdapterError("mt5_optimization_verifier_context_invalid")
    report = _resolved_file(
        context.get("optimizationReportPath"),
        "mt5_optimization_report_missing",
        maximum_bytes=MAX_OPTIMIZATION_XML_BYTES,
    )
    resolved = context.get("resolvedTesterSettings")
    intent = context.get("optimizationIntent")
    if not isinstance(resolved, dict) or not isinstance(intent, dict):
        raise VisibleTerminalAdapterError("mt5_optimization_context_invalid")
    if report.suffix.casefold() != ".xml":
        raise VisibleTerminalAdapterError("mt5_optimization_report_format_invalid")
    xml_evidence = _spreadsheetml_optimization_evidence(report, intent=intent)
    expert = Path(str(resolved.get("expertFileName") or "")).stem
    expected_title = f"{expert} {resolved.get('symbol')},{resolved.get('period')}"
    if resolved.get("useDate") is True:
        from_date = str(resolved.get("fromDate") or "").replace("-", ".")
        to_date = str(resolved.get("toDate") or "").replace("-", ".")
        expected_title += f" {from_date}-{to_date}"
    if not secrets.compare_digest(xml_evidence["title"], expected_title):
        raise VisibleTerminalAdapterError("mt5_optimization_report_identity_mismatch")
    result_rows = copy.deepcopy(xml_evidence["resultRows"])
    pass_count = int(xml_evidence["dataRowCount"])
    if (
        pass_count < 2
        or len(result_rows) < 2
        or len(result_rows) > pass_count
        or int(xml_evidence["uniquePassCount"]) != pass_count
        or int(xml_evidence["uniqueCombinationCount"]) != pass_count
    ):
        raise VisibleTerminalAdapterError("mt5_optimization_pass_count_invalid")
    if intent.get("mode") == "complete" and (
        xml_evidence["completeCombinationCount"] is None
        or pass_count != int(xml_evidence["completeCombinationCount"])
    ):
        # Exact coverage of a complete grid proves that no persisted MT5 result
        # filter silently removed rows from the exported worksheet.
        raise VisibleTerminalAdapterError("mt5_optimization_pass_count_invalid")
    all_symbols_mode = intent.get("mode") == "all_symbols_market_watch"
    symbol_universe = _validate_optimization_symbol_universe(
        xml_evidence.get("symbolUniverse"),
        xml_evidence.get("symbolUniverseDigest"),
        required=all_symbols_mode,
        result_rows=result_rows,
        complete_result_rows=len(result_rows) == pass_count,
    )
    set_path = Path(str(intent.get("setPath") or ""))
    set_digest, _ = _stable_digest(set_path, maximum_bytes=MAX_SET_BYTES)
    if not secrets.compare_digest(set_digest, str(intent.get("setDigest") or "")):
        raise VisibleTerminalAdapterError("optimization_set_changed")
    return {
        "optimizationVerified": True,
        "optimizationPassCount": pass_count,
        "optimizationReturnedPassCount": len(result_rows),
        "optimizationRowsTruncated": len(result_rows) < pass_count,
        "optimizationResultRows": result_rows,
        "optimizationSymbolUniverse": symbol_universe,
        "optimizationSymbolUniverseDigest": xml_evidence.get(
            "symbolUniverseDigest"
        ),
        "reportSha256": xml_evidence["reportSha256"],
        "setSha256": set_digest,
        "rangesDigest": intent["rangesDigest"],
    }


def verify_visible_metaeditor_compile_mt5(context: dict) -> dict:
    if not isinstance(context, dict) or context.get("platform") != "mt5":
        raise VisibleTerminalAdapterError("compile_verifier_context_invalid")
    source = _resolved_file(
        context.get("sourcePath"), "compile_verifier_source_missing", maximum_bytes=MAX_SOURCE_BYTES
    )
    binary = _resolved_file(
        context.get("binaryPath"), "compile_verifier_binary_missing", maximum_bytes=MAX_BINARY_BYTES
    )
    if source.suffix.casefold() != ".mq5" or binary.suffix.casefold() != ".ex5":
        raise VisibleTerminalAdapterError("compile_verifier_artifact_type_invalid")
    source_digest, _ = _stable_digest(source, maximum_bytes=MAX_SOURCE_BYTES)
    binary_digest, _ = _stable_digest(binary, maximum_bytes=MAX_BINARY_BYTES)
    ui = context.get("visibleUiResult")
    result_line = str((ui or {}).get("compileResultLine") or "").strip()
    if (
        source_digest != context.get("sourceDigest")
        or binary_digest != context.get("compiledDigest")
        or ZERO_COMPILE_RESULT.fullmatch(result_line) is None
        or (ui or {}).get("freshBinaryObserved") is not True
        or SHA256.fullmatch(
            str((ui or {}).get("compileResultBeforeSha256") or "")
        )
        is None
        or SHA256.fullmatch(
            str((ui or {}).get("compileResultAfterSha256") or "")
        )
        is None
        or secrets.compare_digest(
            str((ui or {}).get("compileResultBeforeSha256")),
            str((ui or {}).get("compileResultAfterSha256")),
        )
    ):
        raise VisibleTerminalAdapterError("compile_verifier_result_invalid")
    return {
        "compileVerified": True,
        # Publish one canonical bridge-facing success line. Keep accepting
        # the exact native MetaEditor detail above without making downstream
        # validation depend on build-specific elapsed/cpu suffixes.
        "compileResultLine": "Result: 0 errors, 0 warnings",
        "nativeCompileResultLine": result_line,
        "compiledBinarySha256": binary_digest,
    }


def _powershell_executable() -> Path:
    system_root = Path(os.environ.get("WINDIR") or r"C:\Windows")
    candidate = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if not candidate.is_file() or _path_has_reparse_component(candidate):
        raise VisibleTerminalAdapterError("powershell_runtime_unavailable")
    return candidate.resolve(strict=True)


def _default_powershell_runner(
    payload: dict, *, response_path: Path, timeout_seconds: int
) -> dict:
    try:
        script = Path(__file__).with_suffix(".ps1").resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError("visible_ui_script_missing") from error
    action = str(payload.get("action") or "")
    operation_id = str(payload.get("operationId") or "")
    if re.fullmatch(r"[a-z_]{3,40}", action) is None or not SAFE_OPERATION_ID.fullmatch(
        operation_id
    ):
        raise VisibleTerminalAdapterError("visible_ui_request_invalid")
    # A probe/start/collect call for one operation must never share the same
    # transport files.  A Python crash can leave PowerShell alive long enough
    # to finish the original action; action-scoped files let recovery consume
    # that result without launching a second Start action.
    action_response_path = response_path.with_name(
        response_path.stem + f"-{action}.json"
    )
    request_path = response_path.with_name(
        response_path.stem + f"-{action}-request.json"
    )
    request_payload = _canonical_json(payload)
    durable_start_action = action in {"backtest", "optimize"}
    if action_response_path.exists():
        try:
            cached = json.loads(action_response_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise VisibleTerminalAdapterError("visible_ui_response_invalid") from error
        finally:
            try:
                if not durable_start_action:
                    action_response_path.unlink(missing_ok=True)
                request_path.unlink(missing_ok=True)
            except OSError:
                pass
        if (
            not isinstance(cached, dict)
            or cached.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or cached.get("action") != action
            or cached.get("operationId") != operation_id
            or cached.get("ok") is not True
        ):
            raise VisibleTerminalAdapterError("visible_ui_response_invalid")
        cached["recoveredPowerShellResponse"] = True
        cached["pythonObservedDurationMs"] = 0
        return cached
    if request_path.exists():
        try:
            existing_request = request_path.read_bytes()
        except OSError as error:
            raise VisibleTerminalAdapterError(
                "visible_ui_request_in_flight_or_orphaned", retryable=True
            ) from error
        if not secrets.compare_digest(existing_request, request_payload):
            raise VisibleTerminalAdapterError("visible_ui_request_conflict")
        # Do not remove or replay an ambiguous request.  The operation-scoped
        # PowerShell mutex and the subsequent collect action provide the safe
        # recovery path once the original child exits or publishes a response.
        raise VisibleTerminalAdapterError(
            "visible_ui_request_in_flight_or_orphaned", retryable=True
        )
    _write_exclusive(request_path, request_payload, "ui_request_exists")
    command = [
        str(_powershell_executable()),
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-RequestPath",
        str(request_path),
        "-ResponsePath",
        str(action_response_path),
    ]
    started = time.perf_counter()
    bounded_timeout = max(10, min(int(timeout_seconds), DEFAULT_TESTER_TIMEOUT_SECONDS))
    try:
        result = subprocess.run(
            command,
            cwd=str(script.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=bounded_timeout + 60,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise VisibleTerminalAdapterError("visible_ui_timeout", retryable=True) from error
    except (OSError, ValueError) as error:
        raise VisibleTerminalAdapterError("visible_ui_process_failed", retryable=True) from error
    finally:
        try:
            request_path.unlink(missing_ok=True)
        except OSError:
            pass
    if len(result.stdout or b"") + len(result.stderr or b"") > 64 * 1024:
        raise VisibleTerminalAdapterError("visible_ui_output_exceeded")
    if not action_response_path.is_file():
        raise VisibleTerminalAdapterError("visible_ui_response_missing", retryable=True)
    try:
        raw = json.loads(action_response_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        try:
            action_response_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise VisibleTerminalAdapterError("visible_ui_response_invalid") from error
    if result.returncode != 0 or not isinstance(raw, dict) or raw.get("ok") is not True:
        code = (
            str(raw.get("reasonCode") or "visible_ui_action_failed")
            if isinstance(raw, dict)
            else "visible_ui_action_failed"
        )
        if re.fullmatch(r"[a-z0-9_]{3,100}", code) is None:
            code = "visible_ui_action_failed"
        try:
            action_response_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise VisibleTerminalAdapterError(
            code, retryable=code.endswith(("_timeout", "_not_ready"))
        )
    # A successful Start action response is part of the exact-once recovery
    # boundary.  Keep it until the canonical Python receipt is fsynced; a
    # process crash after this return can then consume the completed evidence
    # without pressing Start a second time.  Probe/compile/collect responses do
    # not represent a tester dispatch and remain ephemeral transport files.
    if not durable_start_action:
        try:
            action_response_path.unlink(missing_ok=True)
        except OSError:
            pass
    else:
        raw["durableStartResponseSha256"] = _stable_digest(
            action_response_path, maximum_bytes=256 * 1024
        )[0]
    raw["pythonObservedDurationMs"] = round((time.perf_counter() - started) * 1000)
    return raw


def _powershell_action_response_path(response_path: Path, action: str) -> Path:
    return response_path.with_name(response_path.stem + f"-{action}.json")


def _read_cached_start_response(
    response_path: Path,
    *,
    action: str,
    operation_id: str,
    boundary_path: Path,
    dispatch_path: Path,
) -> tuple[dict, str, Path] | None:
    """Read, but do not delete, a completed prior Start response.

    The caller may use this only after validating the durable boundary and
    dispatch confirmation.  Keeping the response until the Python receipt is
    committed makes another Python crash recoverable without ever replaying
    Strategy Tester Start.
    """

    path = _powershell_action_response_path(response_path, action)
    if not path.exists():
        return None
    digest, size = _stable_digest(path, maximum_bytes=256 * 1024)
    if size <= 2:
        raise VisibleTerminalAdapterError("visible_ui_response_invalid")
    payload = _read_json_object(path, "visible_ui_response_invalid")
    try:
        response_stat = path.stat(follow_symlinks=False)
        boundary_stat = boundary_path.stat(follow_symlinks=False)
        dispatch_stat = dispatch_path.stat(follow_symlinks=False)
    except (OSError, ValueError) as error:
        raise VisibleTerminalAdapterError("visible_ui_response_invalid") from error
    if (
        not isinstance(payload, dict)
        or payload.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
        or payload.get("ok") is not True
        or payload.get("action") != action
        or payload.get("operationId") != operation_id
        or response_stat.st_mtime_ns < boundary_stat.st_mtime_ns
        or response_stat.st_mtime_ns < dispatch_stat.st_mtime_ns
    ):
        raise VisibleTerminalAdapterError("visible_ui_response_invalid")
    payload["recoveredPowerShellStartResponse"] = True
    payload["pythonObservedDurationMs"] = 0
    payload["durableStartResponseSha256"] = digest
    return payload, digest, path


_ISO_FRACTION = re.compile(
    r"^(.*\d{2}:\d{2}:\d{2})\.(\d+)([+-]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?)?$"
)


def _parse_utc(value: object) -> datetime:
    text = str(value or "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    # PowerShell's round-trip format ("o") carries seven fractional digits.
    # Python 3.11+ truncates any fraction to microseconds, but Python 3.10
    # accepts only three or six digits, so normalize to six first and keep
    # the supported 3.10-3.14 matrix fail-closed on everything else.
    fraction = _ISO_FRACTION.fullmatch(text)
    if fraction is not None:
        text = "{0}.{1}{2}".format(
            fraction.group(1),
            fraction.group(2)[:6].ljust(6, "0"),
            fraction.group(3) or "",
        )
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise VisibleTerminalAdapterError("process_observation_time_invalid") from error
    if parsed.tzinfo is None:
        raise VisibleTerminalAdapterError("process_observation_time_invalid")
    return parsed.astimezone(timezone.utc)


def _dispatch_confirmation_path(boundary_path: Path) -> Path:
    return Path(str(boundary_path) + ".dispatch-confirmed")


def _dispatch_confirmation_entry_present(path: Path) -> bool:
    """Distinguish exact absence from an invalid existing path entry.

    Existing symlinks, hard links, directories, and reparse-backed entries are
    intentionally handed to the strict validator so they retain the granular
    ``tester_start_dispatch_unconfirmed`` reason instead of being mistaken for
    the crash-window state.
    """

    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(
            "tester_start_dispatch_unconfirmed"
        ) from error
    return True


def _validate_dispatch_confirmation(
    path: Path, *, operation_id: str, action_digest: str, boundary_digest: str
) -> str:
    code = "tester_start_dispatch_unconfirmed"
    raw, digest, _size = _stable_single_link_bytes(
        path, maximum_bytes=32 * 1024, code=code
    )
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise VisibleTerminalAdapterError(code) from error
    if (
        not isinstance(payload, dict)
        or set(payload)
        != {
            "schemaVersion",
            "operationId",
            "actionRequestDigest",
            "startBoundarySha256",
            "confirmedAt",
        }
        or payload.get("schemaVersion") != "ea-factory-mt5-start-dispatch-v1"
        or payload.get("operationId") != operation_id
        or payload.get("actionRequestDigest") != action_digest
        or payload.get("startBoundarySha256") != boundary_digest
    ):
        raise VisibleTerminalAdapterError("tester_start_dispatch_unconfirmed")
    confirmed = _parse_utc(payload.get("confirmedAt"))
    now = datetime.now(timezone.utc)
    # Dispatch confirmation is durable operation evidence, not a short-lived
    # bearer credential.  Expiring it by wall clock made a valid completed
    # receipt unrecoverable after a long course/VPS pause.  Reject only a
    # materially future timestamp; identity and ordering are bound by the
    # immutable action/boundary digests and file hashes.
    if (confirmed - now).total_seconds() > 300:
        raise VisibleTerminalAdapterError("tester_start_dispatch_unconfirmed")
    return digest


def _recovery_checkpoint_file_present(path: Path) -> bool:
    """Return exact regular-file presence for a recovery checkpoint.

    A broken link, directory, hard link, or reparse-backed path is not an
    absent checkpoint.  It is an invalid checkpoint state and must stop the
    retry before any visible-terminal action is dispatched.
    """

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(
            "mt5_tester_recovery_checkpoint_invalid"
        ) from error
    try:
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or int(getattr(metadata, "st_file_attributes", 0) or 0) & 0x400
            or int(metadata.st_nlink) != 1
            or _path_has_reparse_component(path)
        ):
            raise VisibleTerminalAdapterError(
                "mt5_tester_recovery_checkpoint_invalid"
            )
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(
            "mt5_tester_recovery_checkpoint_invalid"
        ) from error
    return True


def _classify_tester_recovery_checkpoints(
    *,
    settings_screenshot: Path,
    result_screenshot: Path,
    report_screenshot: Path,
    report: Path,
    boundary_path: Path,
    dispatch_path: Path,
    expert_catalog_refresh_boundary_path: Path,
) -> dict:
    """Validate and classify safe immutable post-Start retry states.

    The immutable Start boundary is not proof that Start was dispatched.  An
    exact durable dispatch receipt is mandatory for every recovery state; if
    it is absent, fail closed before considering same-config results or logs.
    """

    code = "mt5_tester_recovery_checkpoint_invalid"
    paths = {
        "settings": settings_screenshot,
        "result": result_screenshot,
        "reportProof": report_screenshot,
        "report": report,
    }
    present = {
        name: _recovery_checkpoint_file_present(path)
        for name, path in paths.items()
    }
    if not present["settings"] or present["reportProof"] is not present["report"]:
        raise VisibleTerminalAdapterError(code)
    if not present["result"] and (present["report"] or present["reportProof"]):
        raise VisibleTerminalAdapterError(code)

    dispatch_present = _recovery_checkpoint_file_present(dispatch_path)
    if not dispatch_present:
        raise VisibleTerminalAdapterError("tester_start_dispatch_unconfirmed")

    try:
        boundary_stat = boundary_path.stat(follow_symlinks=False)
        dispatch_stat = (
            dispatch_path.stat(follow_symlinks=False) if dispatch_present else None
        )
        now_ns = time.time_ns()
        future_tolerance_ns = 300 * 1_000_000_000
        ordering_tolerance_ns = 3 * 1_000_000_000

        settings_digest, _ = _validate_png(settings_screenshot)
        settings_stat = settings_screenshot.stat(follow_symlinks=False)
        if (
            settings_stat.st_mtime_ns
            > boundary_stat.st_mtime_ns + ordering_tolerance_ns
            or settings_stat.st_mtime_ns > now_ns + future_tolerance_ns
        ):
            raise VisibleTerminalAdapterError(code)
        if _recovery_checkpoint_file_present(expert_catalog_refresh_boundary_path):
            refresh_stat = expert_catalog_refresh_boundary_path.stat(
                follow_symlinks=False
            )
            if (
                settings_stat.st_mtime_ns + ordering_tolerance_ns
                < refresh_stat.st_mtime_ns
            ):
                raise VisibleTerminalAdapterError(code)

        result_digest = None
        report_digest = None
        report_screenshot_digest = None
        if present["result"]:
            if dispatch_stat is None:
                raise VisibleTerminalAdapterError(code)
            result_digest, _ = _validate_png(result_screenshot)
            result_stat = result_screenshot.stat(follow_symlinks=False)
            if (
                result_stat.st_mtime_ns + ordering_tolerance_ns
                < dispatch_stat.st_mtime_ns
                or result_stat.st_mtime_ns > now_ns + future_tolerance_ns
            ):
                raise VisibleTerminalAdapterError(code)
        if present["report"]:
            report_digest, _ = _stable_digest(
                report, maximum_bytes=_report_maximum_bytes(report)
            )
            report_screenshot_digest, _ = _validate_png(report_screenshot)
            report_stat = report.stat(follow_symlinks=False)
            proof_stat = report_screenshot.stat(follow_symlinks=False)
            if (
                report_stat.st_mtime_ns + ordering_tolerance_ns
                < result_stat.st_mtime_ns
                or proof_stat.st_mtime_ns + ordering_tolerance_ns
                < report_stat.st_mtime_ns
                or report_stat.st_mtime_ns > now_ns + future_tolerance_ns
                or proof_stat.st_mtime_ns > now_ns + future_tolerance_ns
            ):
                raise VisibleTerminalAdapterError(code)
    except VisibleTerminalAdapterError as error:
        if str(error) == code:
            raise
        raise VisibleTerminalAdapterError(code) from error
    except (OSError, RuntimeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error

    state = (
        "in_flight"
        if not present["result"]
        else ("collected" if present["report"] else "completed")
    )
    return {
        "state": state,
        "testerSettingsSha256": settings_digest,
        "testerResultSha256": result_digest,
        "testerReportSha256": report_digest,
        "testerReportScreenshotSha256": report_screenshot_digest,
    }


def _optimization_cache_timestamps_valid(
    *, cache_ctime_ns: int, cache_mtime_ns: int, dispatch_mtime_ns: int
) -> bool:
    """Require cache contents written by this dispatch, including cache reuse.

    MT5 deliberately reuses the same ``.opt`` inode for an identical expert,
    symbol, period, date range and optimizer configuration.  Its creation time
    can therefore predate the current operation by hours or days.  The
    authoritative boundary is the completed content write: it must occur at or
    after the durable dispatch confirmation and cannot precede file creation.
    Exact filename, embedded expert path, symbol and digest checks provide the
    remaining lineage binding.
    """

    return (
        cache_mtime_ns >= dispatch_mtime_ns
        and cache_mtime_ns >= cache_ctime_ns
    )


def _optimization_cache_lineage(
    *,
    data_path: Path,
    expert_file_name: str,
    expert_ui_path: str,
    deployed_expert_sha256: str,
    policy: dict,
    dispatch_path: Path,
) -> dict:
    """Bind one MT5 optimizer cache file to the exact dispatched settings.

    The proprietary ``.opt`` payload is completion lineage only.  No result
    row or performance metric is ever decoded from it; the exported XML
    remains the sole authoritative optimization-result source.
    """

    code = "mt5_optimization_completion_lineage_invalid"
    try:
        cache_root = (data_path / "Tester" / "cache").resolve(strict=True)
        expected_data_root = data_path.resolve(strict=True)
        if (
            not cache_root.is_dir()
            or not _is_relative_to(cache_root, expected_data_root)
            or _path_has_reparse_component(cache_root)
        ):
            raise VisibleTerminalAdapterError(code)
        dispatch_stat = dispatch_path.stat(follow_symlinks=False)
        expert_stem = Path(expert_file_name).stem
        symbol = str(policy.get("symbol") or "")
        period = str(policy.get("period") or "")
        if not expert_stem or not symbol or not period:
            raise VisibleTerminalAdapterError(code)
        if policy.get("useDate") is True:
            date_from = datetime.strptime(str(policy.get("fromDate")), "%Y-%m-%d").strftime(
                "%Y%m%d"
            )
            date_to = datetime.strptime(str(policy.get("toDate")), "%Y-%m-%d").strftime(
                "%Y%m%d"
            )
            date_pattern = rf"{date_from}\.{date_to}"
            date_policy = "custom_period"
        elif policy.get("useDate") is False and policy.get("fromDate") is None and policy.get(
            "toDate"
        ) is None:
            date_pattern = r"(?P<cacheFrom>[0-9]{8})\.(?P<cacheTo>[0-9]{8})"
            date_policy = "entire_history"
        else:
            raise VisibleTerminalAdapterError(code)
        filename_pattern = re.compile(
            rf"{re.escape(expert_stem)}\.{re.escape(symbol)}\."
            rf"{re.escape(period)}\.{date_pattern}\.[0-9A-Fa-f]{{2}}\."
            rf"[0-9A-Fa-f]{{32}}\.opt\Z",
            re.IGNORECASE,
        )
        expected_deployment = (
            "Experts\\" + expert_ui_path.replace("/", "\\").lstrip("\\")
        )
        if not expected_deployment.casefold().endswith(".ex5"):
            expected_deployment += ".ex5"
        now_ns = time.time_ns()
        future_tolerance_ns = 300 * 1_000_000_000
        candidates: list[dict] = []
        for candidate in cache_root.glob("*.opt"):
            match = filename_pattern.fullmatch(candidate.name)
            if match is None:
                continue
            if not _recovery_checkpoint_file_present(candidate):
                continue
            before = candidate.stat(follow_symlinks=False)
            if (
                before.st_size < 512
                or before.st_size > MAX_OPTIMIZATION_CACHE_BYTES
                or not _optimization_cache_timestamps_valid(
                    cache_ctime_ns=before.st_ctime_ns,
                    cache_mtime_ns=before.st_mtime_ns,
                    dispatch_mtime_ns=dispatch_stat.st_mtime_ns,
                )
                or before.st_ctime_ns > now_ns + future_tolerance_ns
                or before.st_mtime_ns > now_ns + future_tolerance_ns
            ):
                continue
            digest, size = _stable_digest(
                candidate, maximum_bytes=MAX_OPTIMIZATION_CACHE_BYTES
            )
            raw = candidate.read_bytes()
            after = candidate.stat(follow_symlinks=False)
            if (
                after.st_size != before.st_size
                or after.st_mtime_ns != before.st_mtime_ns
                or after.st_ctime_ns != before.st_ctime_ns
                or len(raw) != size
            ):
                raise VisibleTerminalAdapterError(code)
            strings = {
                item
                for item in re.findall(r"[ -~]{3,}", raw.decode("utf-16-le", errors="ignore"))
            }
            required_strings = {expert_stem, expected_deployment, symbol}
            if not all(
                any(observed.casefold() == expected.casefold() for observed in strings)
                for expected in required_strings
            ):
                continue
            candidates.append(
                {
                    "schemaVersion": "ea-factory-mt5-optimization-cache-lineage-v1",
                    "relativePath": candidate.relative_to(expected_data_root).as_posix(),
                    "sha256": digest,
                    "byteSize": size,
                    "createdTimeUtcNs": before.st_ctime_ns,
                    "lastWriteTimeUtcNs": before.st_mtime_ns,
                    "expertFileName": expert_file_name,
                    "expertUiPath": expert_ui_path,
                    "deployedExpertSha256": deployed_expert_sha256,
                    "embeddedExpertPath": expected_deployment,
                    "symbol": symbol,
                    "period": period,
                    "datePolicy": date_policy,
                    "fromDate": policy.get("fromDate"),
                    "toDate": policy.get("toDate"),
                    "cacheFromDate": (
                        match.groupdict().get("cacheFrom")
                        if date_policy == "entire_history"
                        else date_from
                    ),
                    "cacheToDate": (
                        match.groupdict().get("cacheTo")
                        if date_policy == "entire_history"
                        else date_to
                    ),
                }
            )
        if len(candidates) != 1:
            raise VisibleTerminalAdapterError(code)
        return candidates[0]
    except VisibleTerminalAdapterError:
        raise
    except (OSError, RuntimeError, UnicodeError, ValueError) as error:
        raise VisibleTerminalAdapterError(code) from error


def _optimization_cache_lineage_digest(lineage: dict) -> str:
    fields = (
        "schemaVersion",
        "relativePath",
        "sha256",
        "byteSize",
        "createdTimeUtcNs",
        "lastWriteTimeUtcNs",
        "expertFileName",
        "expertUiPath",
        "deployedExpertSha256",
        "embeddedExpertPath",
        "symbol",
        "period",
        "datePolicy",
        "fromDate",
        "toDate",
        "cacheFromDate",
        "cacheToDate",
    )
    return _sha256_bytes(
        "\n".join("" if lineage.get(field) is None else str(lineage[field]) for field in fields).encode(
            "utf-8"
        )
    )


def _ensure_optimization_completion_checkpoint(
    *,
    checkpoint_path: Path,
    allow_create: bool,
    operation_id: str,
    action_digest: str,
    boundary_digest: str,
    dispatch_digest: str,
    data_path: Path,
    expert_file_name: str,
    expert_ui_path: str,
    deployed_expert_sha256: str,
    policy: dict,
    dispatch_path: Path,
    tester_settings_sha256: str,
    tester_result_sha256: str,
) -> tuple[dict, str]:
    lineage = _optimization_cache_lineage(
        data_path=data_path,
        expert_file_name=expert_file_name,
        expert_ui_path=expert_ui_path,
        deployed_expert_sha256=deployed_expert_sha256,
        policy=policy,
        dispatch_path=dispatch_path,
    )
    expected = {
        "schemaVersion": OPTIMIZATION_COMPLETION_CHECKPOINT_SCHEMA,
        "operationId": operation_id,
        "stageId": "optimize",
        "actionRequestDigest": action_digest,
        "startBoundarySha256": boundary_digest,
        "dispatchConfirmationSha256": dispatch_digest,
        "testerSettingsSha256": tester_settings_sha256,
        "testerResultSha256": tester_result_sha256,
        "optimizationCacheLineage": lineage,
        "optimizationCacheLineageDigest": _optimization_cache_lineage_digest(
            lineage
        ),
    }
    checkpoint_exists = _recovery_checkpoint_file_present(checkpoint_path)
    if checkpoint_exists:
        raw_checkpoint, checkpoint_digest, _checkpoint_size = (
            _stable_single_link_bytes(
                checkpoint_path,
                maximum_bytes=256 * 1024,
                code="mt5_optimization_completion_checkpoint_invalid",
            )
        )
        try:
            actual_checkpoint = json.loads(raw_checkpoint.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_completion_checkpoint_invalid"
            ) from error
        if actual_checkpoint != expected:
            raise VisibleTerminalAdapterError(
                "mt5_optimization_completion_checkpoint_mismatch"
            )
    elif allow_create:
        _write_exclusive(
            checkpoint_path,
            _canonical_json(expected),
            "mt5_optimization_completion_checkpoint_exists",
        )
    else:
        raise VisibleTerminalAdapterError(
            "mt5_optimization_completion_checkpoint_missing"
        )
    if not _recovery_checkpoint_file_present(checkpoint_path):
        raise VisibleTerminalAdapterError(
            "mt5_optimization_completion_checkpoint_invalid"
        )
    raw_checkpoint, checkpoint_digest, _checkpoint_size = _stable_single_link_bytes(
        checkpoint_path,
        maximum_bytes=256 * 1024,
        code="mt5_optimization_completion_checkpoint_invalid",
    )
    try:
        persisted_checkpoint = json.loads(raw_checkpoint.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise VisibleTerminalAdapterError(
            "mt5_optimization_completion_checkpoint_invalid"
        ) from error
    if persisted_checkpoint != expected:
        raise VisibleTerminalAdapterError(
            "mt5_optimization_completion_checkpoint_mismatch"
        )
    return expected, checkpoint_digest


def _validate_probe(raw: object, target: dict) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("terminal_process_probe_missing")
    required = {
        "observedAt",
        "processId",
        "executablePath",
        "windowHandle",
        "windowOwnerProcessId",
        "windowTitle",
        "windowClass",
    }
    if set(raw) != required:
        raise VisibleTerminalAdapterError("terminal_process_probe_shape_invalid")
    observed = _parse_utc(raw["observedAt"])
    if abs((datetime.now(timezone.utc) - observed).total_seconds()) > 30:
        raise VisibleTerminalAdapterError("terminal_process_probe_stale")
    path = _resolved_file(
        raw.get("executablePath"), "terminal_process_image_invalid", maximum_bytes=1024 * 1024 * 1024
    )
    if (
        isinstance(raw.get("processId"), bool)
        or not isinstance(raw.get("processId"), int)
        or raw["processId"] <= 0
        or raw.get("processId") != raw.get("windowOwnerProcessId")
        or isinstance(raw.get("windowHandle"), bool)
        or not isinstance(raw.get("windowHandle"), int)
        or raw["windowHandle"] <= 0
        or os.path.normcase(str(path)) != os.path.normcase(str(target["terminalPath"]))
        or not str(raw.get("windowTitle") or "").strip()
        or not str(raw.get("windowClass") or "").strip()
    ):
        raise VisibleTerminalAdapterError("terminal_process_probe_invalid")
    digest, _ = _stable_digest(path, maximum_bytes=1024 * 1024 * 1024)
    if digest != target["terminalExecutableSha256"]:
        raise VisibleTerminalAdapterError("terminal_process_image_changed")
    return {
        "observedAt": observed.isoformat(),
        "processId": raw["processId"],
        "windowHandle": raw["windowHandle"],
        "executableSha256": digest,
        "windowTitleSha256": _sha256_text(raw["windowTitle"]),
        "windowClassSha256": _sha256_text(raw["windowClass"]),
    }


def _process_binding_digest(value: Mapping[str, object]) -> str:
    ordered = {key: value.get(key) for key in sorted(value) if key != "processBindingDigest"}
    return _sha256_text(f"{PROCESS_BINDING_SCHEMA}\n{ordered}")


def _validate_binding(raw: object, *, target: dict, stage_id: str) -> dict:
    if not isinstance(raw, dict):
        raise VisibleTerminalAdapterError("process_binding_missing")
    required = {
        "observedAt",
        "terminalProcessId",
        "terminalExecutablePath",
        "terminalWindowHandle",
        "terminalWindowOwnerProcessId",
        "terminalWindowTitle",
        "terminalWindowClass",
        "frontOfficeKind",
        "frontOfficeProcessId",
        "frontOfficeExecutablePath",
        "frontOfficeWindowHandle",
        "frontOfficeWindowOwnerProcessId",
        "frontOfficeWindowTitle",
        "frontOfficeWindowClass",
        "autoTradingState",
    }
    if set(raw) != required:
        raise VisibleTerminalAdapterError("process_binding_shape_invalid")
    observed = _parse_utc(raw["observedAt"])
    terminal = _resolved_file(
        raw["terminalExecutablePath"], "terminal_process_image_invalid", maximum_bytes=1024 * 1024 * 1024
    )
    front = _resolved_file(
        raw["frontOfficeExecutablePath"], "front_office_process_image_invalid", maximum_bytes=1024 * 1024 * 1024
    )
    expected_front = target["compilerPath"] if stage_id == "compile_validate" else target["terminalPath"]
    expected_kind = "metaeditor" if stage_id == "compile_validate" else "strategy_tester"
    integer_fields = (
        "terminalProcessId",
        "terminalWindowHandle",
        "terminalWindowOwnerProcessId",
        "frontOfficeProcessId",
        "frontOfficeWindowHandle",
        "frontOfficeWindowOwnerProcessId",
    )
    if (
        any(isinstance(raw.get(k), bool) or not isinstance(raw.get(k), int) or raw[k] <= 0 for k in integer_fields)
        or raw["terminalProcessId"] != raw["terminalWindowOwnerProcessId"]
        or raw["frontOfficeProcessId"] != raw["frontOfficeWindowOwnerProcessId"]
        or os.path.normcase(str(terminal)) != os.path.normcase(str(target["terminalPath"]))
        or os.path.normcase(str(front)) != os.path.normcase(str(expected_front))
        or raw.get("frontOfficeKind") != expected_kind
        or not isinstance(raw.get("autoTradingState"), bool)
        or not str(raw.get("terminalWindowTitle") or "").strip()
        or not str(raw.get("frontOfficeWindowTitle") or "").strip()
    ):
        raise VisibleTerminalAdapterError("process_binding_target_mismatch")
    terminal_digest, _ = _stable_digest(terminal, maximum_bytes=1024 * 1024 * 1024)
    front_digest, _ = _stable_digest(front, maximum_bytes=1024 * 1024 * 1024)
    binding = {
        "schemaVersion": PROCESS_BINDING_SCHEMA,
        "observedAt": observed.isoformat(),
        "stageId": stage_id,
        "terminalCandidateId": target["candidateId"],
        "terminalSelectionRevision": target["selectionRevision"],
        "terminalBindingDigest": target["bindingDigest"],
        "terminalProcessId": raw["terminalProcessId"],
        "terminalExecutableSha256": terminal_digest,
        "terminalWindowHandle": raw["terminalWindowHandle"],
        "terminalWindowOwnerProcessId": raw["terminalWindowOwnerProcessId"],
        "terminalWindowTitleSha256": _sha256_text(raw["terminalWindowTitle"]),
        "terminalWindowClassSha256": _sha256_text(raw["terminalWindowClass"]),
        "frontOfficeKind": expected_kind,
        "frontOfficeProcessId": raw["frontOfficeProcessId"],
        "frontOfficeExecutableSha256": front_digest,
        "frontOfficeWindowHandle": raw["frontOfficeWindowHandle"],
        "frontOfficeWindowOwnerProcessId": raw["frontOfficeWindowOwnerProcessId"],
        "frontOfficeWindowTitleSha256": _sha256_text(raw["frontOfficeWindowTitle"]),
        "frontOfficeWindowClassSha256": _sha256_text(raw["frontOfficeWindowClass"]),
    }
    binding["processBindingDigest"] = _process_binding_digest(binding)
    return binding


def _binding_pair(
    ui: dict, *, target: dict, stage_id: str
) -> tuple[dict, dict, bool, bool]:
    before_raw = ui.get("processBinding")
    after_raw = ui.get("postProcessBinding")
    first = _validate_binding(before_raw, target=target, stage_id=stage_id)
    second = _validate_binding(after_raw, target=target, stage_id=stage_id)
    assert isinstance(before_raw, dict) and isinstance(after_raw, dict)
    before_state = before_raw.get("autoTradingState")
    after_state = after_raw.get("autoTradingState")
    if (
        first["terminalProcessId"] != second["terminalProcessId"]
        or first["terminalWindowHandle"] != second["terminalWindowHandle"]
        or first["frontOfficeProcessId"] != second["frontOfficeProcessId"]
        or first["frontOfficeWindowHandle"] != second["frontOfficeWindowHandle"]
        or before_state is not after_state
    ):
        raise VisibleTerminalAdapterError("process_binding_drift")
    return first, second, before_state, after_state


class VisibleFrontOfficeAdapterMt5:
    """Bridge-callable visible MT5 adapter with durable start-once receipts."""

    supported_platforms = frozenset({"mt5"})

    def __init__(
        self,
        *,
        target_resolver: Callable[..., dict],
        powershell_runner: Callable[..., dict] | None = None,
        compile_verifier: Callable[[dict], dict] | None = verify_visible_metaeditor_compile_mt5,
        backtest_verifier: Callable[[dict], dict] | None = verify_mt5_tester_report,
        optimization_verifier: Callable[[dict], dict] | None = verify_mt5_optimization_report,
    ) -> None:
        if not callable(target_resolver):
            raise TypeError("target_resolver must be callable")
        self._target_resolver = target_resolver
        self._powershell_runner = powershell_runner or _default_powershell_runner
        self._compile_verifier = compile_verifier
        self._backtest_verifier = backtest_verifier
        self._optimization_verifier = optimization_verifier
        self._probe_lock = threading.Lock()
        self._operation_probes: dict[tuple[str, str], dict] = {}

    def _target(self, request: dict, context: dict) -> dict:
        supplied = request.get("resolvedTarget") or request.get("terminalTarget")
        if supplied is None:
            try:
                supplied = self._target_resolver(
                    platform="mt5",
                    terminal_binding=copy.deepcopy(context["terminalBinding"]),
                )
            except VisibleTerminalAdapterError:
                raise
            except Exception as error:
                raise VisibleTerminalAdapterError("terminal_target_resolution_failed") from error
        if not isinstance(supplied, dict):
            raise VisibleTerminalAdapterError("terminal_target_missing")
        merged = dict(supplied)
        merged.update(
            {
                "candidateId": context["terminalBinding"].get("candidateId"),
                "selectionRevision": context["terminalBinding"].get("selectionRevision"),
                "bindingDigest": context["terminalBinding"].get("bindingDigest"),
                "platform": "mt5",
            }
        )
        return _validate_target(
            merged,
            context["terminalBinding"],
            "mt5",
            context["stageId"],
        )

    def capability_provider(
        self,
        *,
        platform: str,
        stage_id: str,
        terminal_binding: dict,
        visible_operation: dict,
        resolved_target: dict | None = None,
        tester_settings: dict | None = None,
    ) -> dict:
        common = {
            "ready": False,
            "reasonCode": None,
            "freshProcessProbe": False,
            "foregroundInteraction": True,
            "visibleEvidenceCapture": True,
            "terminalSelectionBound": True,
            "liveTradingAllowed": False,
            "terminalProcessMayRemainOpen": True,
            "processAndWindowBinding": True,
            "idempotentOperationBinding": True,
            "durableReceiptRecovery": True,
            "durableStartBoundary": stage_id in {"backtest_recheck", "optimize"},
            "terminalShutdownAllowed": False,
            "autoTradingMayBeToggled": False,
            "chartAttachmentAllowed": False,
            "visibleMetaEditorCompile": stage_id == "compile_validate",
            "visibleStrategyTester": stage_id in {"backtest_recheck", "optimize"},
            "visibleOptimization": stage_id == "optimize",
            "visualModeRequired": stage_id == "backtest_recheck",
            "testerTradeRowsEvidence": stage_id == "backtest_recheck",
            "testerStartState": None,
            "terminalOnlyPreflight": True,
            "automationIds": (
                copy.deepcopy(BACKTEST_TESTER_AUTOMATION_IDS)
                if stage_id == "backtest_recheck"
                else (
                    copy.deepcopy(OPTIMIZATION_TESTER_AUTOMATION_IDS)
                    if stage_id == "optimize"
                    else {}
                )
            ),
        }
        try:
            if platform != "mt5":
                raise VisibleTerminalAdapterError("mt5_platform_required")
            if stage_id not in {"compile_validate", "backtest_recheck", "optimize"}:
                raise VisibleTerminalAdapterError("visible_stage_unsupported")
            operation_id = str((visible_operation or {}).get("operationId") or "")
            if not SAFE_OPERATION_ID.fullmatch(operation_id):
                raise VisibleTerminalAdapterError("visible_operation_invalid")
            target_raw = resolved_target or self._target_resolver(
                platform="mt5", terminal_binding=copy.deepcopy(terminal_binding)
            )
            merged = dict(target_raw)
            merged.update(
                {
                    "candidateId": terminal_binding.get("candidateId"),
                    "selectionRevision": terminal_binding.get("selectionRevision"),
                    "bindingDigest": terminal_binding.get("bindingDigest"),
                    "platform": "mt5",
                }
            )
            target = _validate_target(merged, terminal_binding, "mt5", stage_id)
            if stage_id == "compile_validate" and not callable(self._compile_verifier):
                raise VisibleTerminalAdapterError("compile_verifier_not_connected")
            if stage_id == "backtest_recheck" and not callable(self._backtest_verifier):
                raise VisibleTerminalAdapterError("backtest_verifier_not_connected")
            if stage_id == "optimize" and not callable(self._optimization_verifier):
                raise VisibleTerminalAdapterError("optimization_verifier_not_connected")
            with tempfile.TemporaryDirectory(prefix="metafx-visible-mt5-probe-") as temporary:
                probe = self._powershell_runner(
                    {
                        "schemaVersion": POWERSHELL_REQUEST_SCHEMA,
                        "action": "probe",
                        "platform": "mt5",
                        "stageId": stage_id,
                        "operationId": operation_id,
                        "terminalPath": str(target["terminalPath"]),
                        "compilerPath": str(target["compilerPath"]),
                        "dataPath": str(target["dataPath"]),
                        "requiredAutomationIds": common["automationIds"],
                    },
                    response_path=Path(temporary) / "probe-response.json",
                    timeout_seconds=20,
                )
            if (
                not isinstance(probe, dict)
                or probe.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
                or probe.get("action") != "probe"
                or probe.get("operationId") != operation_id
            ):
                raise VisibleTerminalAdapterError("terminal_process_probe_invalid")
            terminal_probe = _validate_probe(probe.get("terminalProbe"), target)
            if stage_id in {"backtest_recheck", "optimize"}:
                observed_ids = probe.get("automationControlsVerified")
                if observed_ids != common["automationIds"]:
                    raise VisibleTerminalAdapterError("mt5_tester_controls_not_verified")
                tester_start_state = probe.get("testerStartState")
                if tester_start_state not in {"Start", "Stop"}:
                    raise VisibleTerminalAdapterError("mt5_tester_start_state_unverified")
                common["testerStartState"] = tester_start_state
            elif probe.get("testerStartState") is not None:
                raise VisibleTerminalAdapterError("mt5_tester_start_state_unverified")
            common["terminalProcessProbe"] = terminal_probe
        except VisibleTerminalAdapterError as error:
            common["reasonCode"] = error.code
            return common
        except Exception:
            common["reasonCode"] = "terminal_capability_probe_failed"
            return common
        common["freshProcessProbe"] = True
        common["ready"] = True
        with self._probe_lock:
            self._operation_probes[(operation_id, stage_id)] = {
                "terminalCandidateId": target["candidateId"],
                "terminalSelectionRevision": target["selectionRevision"],
                "terminalBindingDigest": target["bindingDigest"],
                "probe": copy.deepcopy(terminal_probe),
            }
        return common

    def _operation_probe(self, context: dict, target: dict) -> dict:
        operation_id = context["operation"]["operationId"]
        with self._probe_lock:
            stored = copy.deepcopy(
                self._operation_probes.get((operation_id, context["stageId"]))
            )
        if (
            not isinstance(stored, dict)
            or stored.get("terminalCandidateId") != target["candidateId"]
            or stored.get("terminalSelectionRevision") != target["selectionRevision"]
            or stored.get("terminalBindingDigest") != target["bindingDigest"]
            or not isinstance(stored.get("probe"), dict)
        ):
            raise VisibleTerminalAdapterError("capability_process_probe_missing")
        observed = _parse_utc(stored["probe"].get("observedAt"))
        if (datetime.now(timezone.utc) - observed).total_seconds() > 60:
            raise VisibleTerminalAdapterError("capability_process_probe_stale")
        return stored["probe"]

    @staticmethod
    def _assert_probe(binding: dict, probe: dict) -> None:
        if (
            binding.get("terminalProcessId") != probe.get("processId")
            or binding.get("terminalWindowHandle") != probe.get("windowHandle")
            or binding.get("terminalExecutableSha256") != probe.get("executableSha256")
        ):
            raise VisibleTerminalAdapterError("terminal_process_changed_after_capability_probe")

    def _refresh_tester_post_process_binding(
        self,
        *,
        context: dict,
        target: dict,
        process_binding: dict,
        prior_post_binding: dict,
        auto_trading_state: bool,
    ) -> dict:
        """Re-probe the idle Tester after Python finishes report verification.

        Native MT5 report validation can outlive the bridge's 15-second process
        proof window.  The original action proof still binds the actual Start
        lifecycle; this final read-only probe proves that the exact terminal,
        Tester window and Algo Trading state are unchanged immediately before
        the adapter returns evidence to the bridge.  The probe has no Start
        capability and therefore cannot repeat a completed test.
        """

        stage_id = context["stageId"]
        if stage_id not in {"backtest_recheck", "optimize"}:
            raise VisibleTerminalAdapterError("visible_stage_unsupported")
        operation_id = context["operation"]["operationId"]
        automation_ids = copy.deepcopy(
            OPTIMIZATION_TESTER_AUTOMATION_IDS
            if stage_id == "optimize"
            else BACKTEST_TESTER_AUTOMATION_IDS
        )
        with tempfile.TemporaryDirectory(
            prefix="metafx-visible-mt5-post-proof-"
        ) as temporary:
            refreshed = self._powershell_runner(
                {
                    "schemaVersion": POWERSHELL_REQUEST_SCHEMA,
                    "action": "post_probe",
                    "platform": "mt5",
                    "stageId": stage_id,
                    "operationId": operation_id,
                    "terminalPath": str(target["terminalPath"]),
                    "compilerPath": str(target["compilerPath"]),
                    "dataPath": str(target["dataPath"]),
                    "requiredAutomationIds": automation_ids,
                    "expectedTerminalProcessId": process_binding[
                        "terminalProcessId"
                    ],
                    "expectedTerminalWindowHandle": process_binding[
                        "terminalWindowHandle"
                    ],
                },
                response_path=Path(temporary) / "post-proof-response.json",
                timeout_seconds=20,
            )
        native_response_keys = {
            "schemaVersion",
            "ok",
            "action",
            "operationId",
            "terminalProbe",
            "testerStartState",
            "processBinding",
        }
        transport_duration = (
            refreshed.get("pythonObservedDurationMs")
            if isinstance(refreshed, dict)
            else None
        )
        native_response = (
            {
                key: value
                for key, value in refreshed.items()
                if key != "pythonObservedDurationMs"
            }
            if isinstance(refreshed, dict)
            else {}
        )
        # The production transport adds one local timing field after validating
        # the signed PowerShell response.  It is not part of the native result
        # schema, so validate it separately instead of falsely treating every
        # successful production post-probe as an unsigned extra field.  No
        # other transport or native extras are accepted.
        if (
            not isinstance(refreshed, dict)
            or set(native_response) != native_response_keys
            or (
                "pythonObservedDurationMs" in refreshed
                and (
                    type(transport_duration) is not int
                    or transport_duration < 0
                    or transport_duration > 120_000
                )
            )
            or refreshed.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or refreshed.get("ok") is not True
            or refreshed.get("action") != "post_probe"
            or refreshed.get("operationId") != operation_id
            or refreshed.get("testerStartState") != "Start"
        ):
            raise VisibleTerminalAdapterError(
                "mt5_tester_post_process_probe_invalid"
            )
        terminal_probe = _validate_probe(refreshed.get("terminalProbe"), target)
        self._assert_probe(process_binding, terminal_probe)
        raw_binding = refreshed.get("processBinding")
        fresh_binding = _validate_binding(
            raw_binding,
            target=target,
            stage_id=stage_id,
        )
        if (
            not isinstance(raw_binding, dict)
            or raw_binding.get("autoTradingState") is not auto_trading_state
            or _parse_utc(fresh_binding.get("observedAt"))
            < _parse_utc(prior_post_binding.get("observedAt"))
        ):
            raise VisibleTerminalAdapterError("process_binding_drift")
        identity_keys = tuple(
            key
            for key in process_binding
            if key not in {"observedAt", "processBindingDigest"}
        )
        if any(
            fresh_binding.get(key) != process_binding.get(key)
            for key in identity_keys
        ):
            raise VisibleTerminalAdapterError("process_binding_drift")
        return fresh_binding

    @staticmethod
    def _evidence_folders(workspace: Path) -> dict[str, Path]:
        result: dict[str, Path] = {}
        for name in ("EA_Versions", "Reports", "Screenshots", "Summaries", "Sets"):
            path = workspace / name
            try:
                path.mkdir(exist_ok=True)
                resolved = path.resolve(strict=True)
            except (OSError, RuntimeError, ValueError) as error:
                raise VisibleTerminalAdapterError("evidence_directory_invalid") from error
            if _path_has_reparse_component(resolved) or not _is_relative_to(resolved, workspace):
                raise VisibleTerminalAdapterError("evidence_directory_unsafe")
            result[name] = resolved
        return result

    def compile_handler(self, *, request: dict) -> dict:
        context = _validate_request(request, "compile_validate")
        target = self._target(request, context)
        probe = self._operation_probe(context, target)
        if not callable(self._compile_verifier):
            raise VisibleTerminalAdapterError("compile_verifier_not_connected")
        workspace = context["workspace"]
        folders = self._evidence_folders(workspace)
        source = context["source"]["path"]
        source_digest = context["source"]["digest"]
        operation_id = context["operation"]["operationId"]
        binary = source.with_suffix(".ex5")
        experts_root = (target["dataPath"] / "MQL5" / "Experts").resolve(strict=True)
        work_root = _safe_tree(
            experts_root,
            ("Metafxclub", "AgentHQ", operation_id),
            "compile_working_copy_path_unsafe",
        )
        token = operation_id.removeprefix("ea-visible-")
        working_source = work_root / f"agenthq_{token}.mq5"
        working_binary = working_source.with_suffix(".ex5")
        screenshot = folders["Screenshots"] / f"{operation_id}-metaeditor64.png"
        compile_log = folders["Reports"] / f"{operation_id}-compile-mt5.txt"
        intent_path = folders["Summaries"] / f"{operation_id}-compile-intent.json"
        receipt_path = folders["Summaries"] / f"{operation_id}-compile-receipt.json"
        response_path = folders["Summaries"] / f"{operation_id}-compile-ui.json"
        expected_intent = {
            "schemaVersion": ACTION_INTENT_SCHEMA,
            "operationId": operation_id,
            "stageId": "compile_validate",
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "sourceDigest": source_digest,
            "platform": "mt5",
        }
        if receipt_path.exists():
            if _read_json_object(intent_path, "visible_action_intent_invalid") != expected_intent:
                raise VisibleTerminalAdapterError("visible_action_intent_mismatch")
            receipt = _read_json_object(receipt_path, "visible_receipt_invalid")
            screenshot_digest, _ = _validate_png(screenshot)
            log_digest, _ = _stable_digest(compile_log, maximum_bytes=MAX_EVIDENCE_BYTES)
            binary_digest, _ = _stable_digest(binary, maximum_bytes=MAX_BINARY_BYTES)
            if (
                receipt.get("schemaVersion") != RECEIPT_SCHEMA
                or receipt.get("operationId") != operation_id
                or receipt.get("stageId") != "compile_validate"
                or receipt.get("sourceDigest") != source_digest
                or receipt.get("compiledBinarySha256") != binary_digest
                or receipt.get("visibleWindowSha256") != screenshot_digest
                or receipt.get("compileLogSha256") != log_digest
                or receipt.get("processBindingDigest")
                != (receipt.get("processBinding") or {}).get("processBindingDigest")
                or receipt.get("postProcessBindingDigest")
                != (receipt.get("postProcessBinding") or {}).get("processBindingDigest")
                or ZERO_COMPILE_RESULT.fullmatch(
                    str(receipt.get("resultLine") or "")
                )
                is None
                or SHA256.fullmatch(
                    str(receipt.get("compileResultBeforeSha256") or "")
                )
                is None
                or SHA256.fullmatch(
                    str(receipt.get("compileResultAfterSha256") or "")
                )
                is None
                or secrets.compare_digest(
                    str(receipt.get("compileResultBeforeSha256")),
                    str(receipt.get("compileResultAfterSha256")),
                )
                or isinstance(receipt.get("compileResultRowCount"), bool)
                or not isinstance(receipt.get("compileResultRowCount"), int)
                or receipt.get("compileResultRowCount") < 1
                or not isinstance(receipt.get("recoveryRecompile"), bool)
                or receipt.get("zeroErrors") is not True
                or receipt.get("zeroWarnings") is not True
                or not isinstance(receipt.get("autoTradingStateBefore"), bool)
                or receipt.get("autoTradingStateAfter")
                is not receipt.get("autoTradingStateBefore")
            ):
                raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")
            return self._compile_result(
                context,
                target,
                receipt,
                binary,
                screenshot,
                compile_log,
                receipt_path,
                recovered=True,
            )
        recovering = intent_path.exists()
        if recovering:
            if _read_json_object(intent_path, "visible_action_intent_invalid") != expected_intent:
                raise VisibleTerminalAdapterError("visible_action_intent_mismatch")
            # A fail-closed readiness error can happen before F7 and therefore
            # before any EX5 exists.  The durable intent plus the exact working
            # source is sufficient to enter recover_compile: PowerShell deletes
            # any partial/stale EX5 and visibly recompiles from this source.
            if not working_source.is_file():
                raise VisibleTerminalAdapterError("visible_compile_recovery_incomplete")
            working_digest, _ = _stable_digest(working_source, maximum_bytes=MAX_SOURCE_BYTES)
            if not secrets.compare_digest(working_digest, source_digest):
                raise VisibleTerminalAdapterError("compile_working_source_changed")
            action = "recover_compile"
        else:
            if any(path.exists() for path in (working_source, working_binary, screenshot, compile_log)):
                raise VisibleTerminalAdapterError("visible_action_state_uncertain")
            working_digest, _size, _reused = _copy_exclusive_or_verify(
                source,
                working_source,
                maximum_bytes=MAX_SOURCE_BYTES,
                code="compile_working_source_copy_failed",
            )
            if working_digest != source_digest:
                raise VisibleTerminalAdapterError("compile_working_source_digest_mismatch")
            _write_exclusive(
                intent_path,
                _canonical_json(expected_intent),
                "visible_action_intent_exists",
            )
            action = "compile"
        ui = self._powershell_runner(
            {
                "schemaVersion": POWERSHELL_REQUEST_SCHEMA,
                "action": action,
                "platform": "mt5",
                "stageId": "compile_validate",
                "operationId": operation_id,
                "terminalPath": str(target["terminalPath"]),
                "compilerPath": str(target["compilerPath"]),
                "dataPath": str(target["dataPath"]),
                "sourcePath": str(working_source),
                "expectedSourceDigest": source_digest,
                "binaryPath": str(working_binary),
                "screenshotPath": str(screenshot),
                "timeoutSeconds": DEFAULT_UI_TIMEOUT_SECONDS,
                "expectedTerminalProcessId": probe["processId"],
                "expectedTerminalWindowHandle": probe["windowHandle"],
            },
            response_path=response_path,
            timeout_seconds=DEFAULT_UI_TIMEOUT_SECONDS,
        )
        if (
            not isinstance(ui, dict)
            or ui.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or ui.get("action") != action
            or ui.get("operationId") != operation_id
            or ui.get("exactSourceWindowVerified") is not True
            or ui.get("compileWorkingCopyVerified") is not True
            or ui.get("workingSourceSha256") != source_digest
            or ui.get("compileInvoked") is not True
            or ui.get("recoveryRecompile") is not recovering
            or ui.get("freshBinaryObserved") is not True
            or SHA256.fullmatch(str(ui.get("compileResultBeforeSha256") or "")) is None
            or SHA256.fullmatch(str(ui.get("compileResultAfterSha256") or "")) is None
            or secrets.compare_digest(
                str(ui.get("compileResultBeforeSha256")),
                str(ui.get("compileResultAfterSha256")),
            )
            or isinstance(ui.get("compileResultRowCount"), bool)
            or not isinstance(ui.get("compileResultRowCount"), int)
            or ui.get("compileResultRowCount") < 1
        ):
            raise VisibleTerminalAdapterError("visible_compile_result_invalid")
        process_binding, post_binding, auto_before, auto_after = _binding_pair(
            ui, target=target, stage_id="compile_validate"
        )
        self._assert_probe(process_binding, probe)
        source_after, _ = _stable_digest(source, maximum_bytes=MAX_SOURCE_BYTES)
        if source_after != source_digest:
            raise VisibleTerminalAdapterError("immutable_source_changed_during_visible_compile")
        working_binary_digest, _ = _stable_digest(
            working_binary, maximum_bytes=MAX_BINARY_BYTES
        )
        if ui.get("workingBinarySha256") != working_binary_digest:
            raise VisibleTerminalAdapterError("compile_working_binary_digest_mismatch")
        _copy_exclusive_or_verify(
            working_binary,
            binary,
            maximum_bytes=MAX_BINARY_BYTES,
            code="compiled_binary_publication_failed",
        )
        binary_digest, _ = _stable_digest(binary, maximum_bytes=MAX_BINARY_BYTES)
        screenshot_digest, _ = _validate_png(screenshot)
        verified = self._compile_verifier(
            {
                "platform": "mt5",
                "sourcePath": working_source,
                "binaryPath": working_binary,
                "sourceDigest": source_digest,
                "compiledDigest": working_binary_digest,
                "visibleUiResult": copy.deepcopy(ui),
            }
        )
        if not isinstance(verified, dict) or verified.get("compileVerified") is not True:
            raise VisibleTerminalAdapterError("compile_verifier_result_invalid")
        log_bytes = (
            "MetaEditor64 verified compile result\n"
            f"Source: {source.name}\n"
            f"sourceDigest: {source_digest}\n"
            f"Compiled binary: {binary.name}\n"
            f"compiledBinarySha256: {binary_digest}\n"
            "immutableSourcePreserved: true\n"
            f"{verified['compileResultLine']}\n"
            + (
                f"MetaEditor detail: {verified['nativeCompileResultLine']}\n"
                if verified.get("nativeCompileResultLine")
                != verified.get("compileResultLine")
                else ""
            )
        ).encode("utf-8")
        _write_exclusive(compile_log, log_bytes, "compile_log_exists")
        compile_log_digest, _ = _stable_digest(
            compile_log, maximum_bytes=MAX_EVIDENCE_BYTES
        )
        receipt = {
            "schemaVersion": RECEIPT_SCHEMA,
            "operationId": operation_id,
            "stageId": "compile_validate",
            "platform": "mt5",
            "terminalCandidateId": target["candidateId"],
            "status": "verified",
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary_digest,
            "compileWorkingBinarySha256": working_binary_digest,
            "visibleWindowSha256": screenshot_digest,
            "compileLogSha256": compile_log_digest,
            "resultLine": verified["compileResultLine"],
            "compileResultBeforeSha256": ui["compileResultBeforeSha256"],
            "compileResultAfterSha256": ui["compileResultAfterSha256"],
            "compileResultRowCount": ui["compileResultRowCount"],
            "recoveryRecompile": recovering,
            "processBinding": process_binding,
            "postProcessBinding": post_binding,
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "autoTradingStateBefore": auto_before,
            "autoTradingStateAfter": auto_after,
            "zeroErrors": True,
            "zeroWarnings": True,
            "immutableSourcePreserved": True,
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "chartAttached": False,
            "terminalClosedByAdapter": False,
        }
        _write_exclusive(
            receipt_path, _canonical_json(receipt), "visible_receipt_already_exists"
        )
        return self._compile_result(
            context,
            target,
            receipt,
            binary,
            screenshot,
            compile_log,
            receipt_path,
            recovered=False,
        )

    def _compile_result(
        self,
        context: dict,
        target: dict,
        receipt: dict,
        binary: Path,
        screenshot: Path,
        compile_log: Path,
        receipt_path: Path,
        *,
        recovered: bool,
    ) -> dict:
        workspace = context["workspace"]
        metrics = {
            "evidenceMode": EVIDENCE_MODE,
            "operationId": context["operation"]["operationId"],
            "eaFactoryStage": "compile_validate",
            "platform": "mt5",
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "processBinding": copy.deepcopy(receipt["processBinding"]),
            "processBindingDigest": receipt["processBinding"]["processBindingDigest"],
            "postProcessBinding": copy.deepcopy(receipt["postProcessBinding"]),
            "postProcessBindingDigest": receipt["postProcessBinding"]["processBindingDigest"],
            "processId": receipt["processBinding"]["frontOfficeProcessId"],
            "windowHandle": receipt["processBinding"]["frontOfficeWindowHandle"],
            "compiledBinarySha256": receipt["compiledBinarySha256"],
            "sourceDigest": receipt["sourceDigest"],
            "compiledBinaryArtifactAlias": "compiled_binary",
            "visibleWindowEvidenceArtifactAlias": "visible_window",
            "visibleWindowEvidenceSha256": receipt["visibleWindowSha256"],
            "compileLogArtifactAlias": "compile_log",
            "compileLogSha256": receipt["compileLogSha256"],
            "adapterReceiptArtifactAlias": "adapter_receipt",
            "compileExecuted": True,
            "recoveryRecompile": receipt.get("recoveryRecompile") is True,
            "compileVerified": True,
            "visibleMetaEditor": True,
            "visibleMetaEditorCompile": True,
            "resultLine": receipt["resultLine"],
            "zeroErrors": True,
            "zeroWarnings": True,
            "backtestExecuted": False,
            "immutableSourcePreserved": True,
            "recoveredExistingReceipt": recovered,
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": receipt["autoTradingStateBefore"],
            "autoTradingStateAfter": receipt["autoTradingStateAfter"],
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
        }
        return {
            "schemaVersion": RESULT_SCHEMA,
            "operationId": context["operation"]["operationId"],
            "metrics": metrics,
            "artifactSpecifications": [
                _artifact("compiled_binary", binary, workspace, artifact_kind="compile_evidence"),
                _artifact("visible_window", screenshot, workspace, artifact_kind="screenshot_evidence"),
                _artifact("compile_log", compile_log, workspace, artifact_kind="compile_evidence"),
                _artifact("adapter_receipt", receipt_path, workspace, artifact_kind="compile_evidence"),
            ],
        }

    def backtest_handler(self, *, request: dict) -> dict:
        return self._tester_handler(request=request, stage_id="backtest_recheck")

    def optimization_handler(self, *, request: dict) -> dict:
        return self._tester_handler(request=request, stage_id="optimize")

    def _tester_handler(self, *, request: dict, stage_id: str) -> dict:
        context = _validate_request(request, stage_id)
        target = self._target(request, context)
        probe = self._operation_probe(context, target)
        verifier = (
            self._backtest_verifier
            if stage_id == "backtest_recheck"
            else self._optimization_verifier
        )
        if not callable(verifier):
            raise VisibleTerminalAdapterError(
                "backtest_verifier_not_connected"
                if stage_id == "backtest_recheck"
                else "optimization_verifier_not_connected"
            )
        workspace = context["workspace"]
        folders = self._evidence_folders(workspace)
        source = context["source"]["path"]
        source_digest = context["source"]["digest"]
        strategy_execution_profile = context.get("strategyExecutionProfile")
        compiled_deployment = _validate_compiled_deployment(
            request.get("compiledDeployment"),
            workspace=workspace,
            source=context["source"],
            target=target,
        )
        binary = compiled_deployment["binaryPath"]
        binary_digest = compiled_deployment["binarySha256"]
        policy = _validate_tester_settings(
            request.get("testerSettings"), stage_id=stage_id, binary_name=binary.name
        )
        optimization_intent = None
        if stage_id == "optimize":
            source_payload, stable_source_digest, _source_size = (
                _stable_single_link_bytes(
                    source,
                    maximum_bytes=MAX_SOURCE_BYTES,
                    code="source_changed_during_tester_binding",
                )
            )
            if not secrets.compare_digest(stable_source_digest, source_digest):
                raise VisibleTerminalAdapterError(
                    "source_changed_during_tester_binding"
                )
            try:
                optimization_source_code = source_payload.decode(
                    "utf-8-sig", errors="strict"
                )
            except UnicodeDecodeError as error:
                raise VisibleTerminalAdapterError(
                    "source_changed_during_tester_binding"
                ) from error
            optimization_intent = _validate_optimization_intent(
                request.get("optimizationIntent"),
                workspace,
                source_digest,
                optimization_source_code,
            )
        input_binding = None
        input_manifest = None
        tester_input_preset = None
        if stage_id == "backtest_recheck":
            input_binding, _embedded_manifest = _validate_backtest_set_reference(
                request.get("mt5InputBinding"), workspace=workspace
            )
            source_payload, stable_source_digest, _source_size = _stable_single_link_bytes(
                source,
                maximum_bytes=MAX_SOURCE_BYTES,
                code="source_changed_during_tester_binding",
            )
            if not secrets.compare_digest(stable_source_digest, source_digest):
                raise VisibleTerminalAdapterError("source_changed_during_tester_binding")
            try:
                source_code = source_payload.decode("utf-8-sig", errors="strict")
            except UnicodeDecodeError as error:
                raise VisibleTerminalAdapterError(
                    "source_changed_during_tester_binding"
                ) from error
            input_manifest = _validate_input_manifest(
                request.get("mt5InputManifest"),
                source_digest,
                source_code,
            )
            tester_input_preset = _validate_tester_input_preset(
                policy.get("testerInputPreset"), input_manifest, source_code
            )
            _validate_backtest_binding_against_manifest_and_preset(
                input_binding,
                input_manifest,
                tester_input_preset,
            )
        operation_id = context["operation"]["operationId"]
        experts_root = (target["dataPath"] / "MQL5" / "Experts").resolve(strict=True)
        deploy_root = _safe_tree(
            experts_root,
            (
                "Metafxclub",
                "AgentHQ",
                "Deployments",
                compiled_deployment["deploymentRef"],
            ),
            "expert_deployment_path_unsafe",
        )
        deployed = deploy_root / binary.name
        _copy_exclusive_or_verify(
            binary, deployed, maximum_bytes=MAX_BINARY_BYTES, code="expert_deployment_failed"
        )
        expert_ui_path = (
            Path("Metafxclub")
            / "AgentHQ"
            / "Deployments"
            / compiled_deployment["deploymentRef"]
            / binary.stem
        ).as_posix().replace("/", "\\")
        stage_token = "backtest" if stage_id == "backtest_recheck" else "optimization"
        settings_screenshot = folders["Screenshots"] / f"{operation_id}-{stage_token}-settings.png"
        result_screenshot = folders["Screenshots"] / f"{operation_id}-{stage_token}-result.png"
        report_screenshot = folders["Screenshots"] / f"{operation_id}-{stage_token}-report.png"
        report_extension = ".xml" if stage_id == "optimize" else ".htm"
        report = folders["Reports"] / f"{operation_id}-{stage_token}-mt5{report_extension}"
        # MT5 launches the system viewer after report export (Excel for XML),
        # which can hold the exported file with an exclusive share mode.  Save
        # visibly to a viewer staging path and have the PowerShell adapter copy
        # the already-verified bytes into the immutable evidence artifact before
        # that viewer lock can affect receipt replay.
        report_export = (
            folders["Reports"]
            / f"{operation_id}-{stage_token}-mt5-viewer{report_extension}"
        )
        preset_screenshot = (
            folders["Screenshots"] / f"{operation_id}-tester-input-preset.png"
            if stage_id == "backtest_recheck"
            else None
        )
        input_readback_set = (
            folders["Sets"] / f"{operation_id}-tester-input-readback.set"
            if stage_id == "backtest_recheck"
            else None
        )
        baseline_readback_set = (
            folders["Sets"] / f"{operation_id}-optimization-baseline-readback.set"
            if stage_id == "optimize"
            else None
        )
        readback_set = (
            folders["Sets"] / f"{operation_id}-optimization-readback.set"
            if stage_id == "optimize"
            else None
        )
        intent_path = folders["Summaries"] / f"{operation_id}-{stage_token}-intent.json"
        action_request_path = folders["Summaries"] / f"{operation_id}-{stage_token}-action.json"
        boundary_path = folders["Summaries"] / f"{operation_id}-{stage_token}-start-boundary.json"
        expert_catalog_refresh_boundary_path = (
            folders["Summaries"]
            / f"{operation_id}-{stage_token}-expert-catalog-refresh-boundary.json"
        )
        dispatch_path = _dispatch_confirmation_path(boundary_path)
        completion_checkpoint_path = (
            folders["Summaries"]
            / f"{operation_id}-{stage_token}-completion-checkpoint.json"
        )
        tester_completion_evidence_checkpoint_path = (
            folders["Summaries"]
            / f"{operation_id}-{stage_token}-tester-completion-evidence.json"
        )
        receipt_path = folders["Summaries"] / f"{operation_id}-{stage_token}-receipt.json"
        response_path = folders["Summaries"] / f"{operation_id}-{stage_token}-ui.json"
        expected_intent = {
            "schemaVersion": ACTION_INTENT_SCHEMA,
            "operationId": operation_id,
            "stageId": stage_id,
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary_digest,
            "compiledDeploymentRef": compiled_deployment["deploymentRef"],
            "compiledDeploymentDigest": compiled_deployment["bindingDigest"],
            "inputBindingRefDigest": input_binding["refDigest"] if input_binding else None,
            "optimizationSetRefDigest": (
                optimization_intent["setRef"]["refDigest"] if optimization_intent else None
            ),
            "baselinePresetRefDigest": (
                optimization_intent["baselinePresetRef"]["refDigest"]
                if optimization_intent
                else None
            ),
            "optimizationMode": (
                optimization_intent["mode"] if optimization_intent else None
            ),
            "optimizationCriterion": (
                optimization_intent["criterion"] if optimization_intent else None
            ),
            "platform": "mt5",
        }
        if strategy_execution_profile is not None:
            expected_intent["strategyExecutionProfileDigest"] = (
                strategy_execution_profile["profileDigest"]
            )
        unsigned_action_request = {
            "schemaVersion": ACTION_REQUEST_SCHEMA,
            "operationId": operation_id,
            "stageId": stage_id,
            "buildId": request["buildId"],
            "missionId": request["missionId"],
            "reportId": request["reportId"],
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary_digest,
            "testerSettingsDigest": _sha256_bytes(_canonical_json(policy)),
            "optimizationRangesDigest": (
                optimization_intent["rangesDigest"] if optimization_intent else None
            ),
            "optimizationSetDigest": (
                optimization_intent["setDigest"] if optimization_intent else None
            ),
            "compiledDeploymentDigest": compiled_deployment["bindingDigest"],
            "inputBindingRefDigest": input_binding["refDigest"] if input_binding else None,
            "optimizationSetRefDigest": (
                optimization_intent["setRef"]["refDigest"] if optimization_intent else None
            ),
            "baselinePresetRefDigest": (
                optimization_intent["baselinePresetRef"]["refDigest"]
                if optimization_intent
                else None
            ),
            "optimizationMode": (
                optimization_intent["mode"] if optimization_intent else None
            ),
            "optimizationCriterion": (
                optimization_intent["criterion"] if optimization_intent else None
            ),
            # Per-invocation recovery directives must not rewrite the durable
            # action identity.  Every substantive safety field remains bound;
            # only serviceAction/neverStart are validated above and enforced
            # afresh for each call.
            "safetyPolicyDigest": _sha256_bytes(
                _canonical_json(
                    {
                        key: value
                        for key, value in request["safety"].items()
                        if key not in {"serviceAction", "neverStart"}
                    }
                )
            ),
        }
        if strategy_execution_profile is not None:
            unsigned_action_request["strategyExecutionProfileDigest"] = (
                strategy_execution_profile["profileDigest"]
            )
        action_digest = _sha256_bytes(_canonical_json(unsigned_action_request))
        tester_settings_request_digest = _bridge_payload_digest(
            "ea-factory-tester-settings-request-v1", policy
        )
        expected_action_request = {
            **unsigned_action_request,
            "actionRequestDigest": action_digest,
        }
        expected_boundary = {
            "schemaVersion": START_BOUNDARY_SCHEMA,
            "operationId": operation_id,
            "stageId": stage_id,
            "actionRequestDigest": action_digest,
        }
        boundary_bytes = _canonical_json(expected_boundary)
        boundary_digest = _sha256_bytes(boundary_bytes)
        expected_expert_catalog_refresh_boundary = {
            "schemaVersion": EXPERT_CATALOG_REFRESH_BOUNDARY_SCHEMA,
            "operationId": operation_id,
            "stageId": stage_id,
            "actionRequestDigest": action_digest,
            "expertUiPath": expert_ui_path,
            "deployedExpertSha256": binary_digest,
        }
        expert_catalog_refresh_boundary_bytes = _canonical_json(
            expected_expert_catalog_refresh_boundary
        )
        expert_catalog_refresh_boundary_digest = _sha256_bytes(
            expert_catalog_refresh_boundary_bytes
        )
        if receipt_path.exists():
            if _read_json_object(intent_path, "visible_action_intent_invalid") != expected_intent:
                raise VisibleTerminalAdapterError("visible_action_intent_mismatch")
            if _read_json_object(action_request_path, "visible_action_request_invalid") != expected_action_request:
                raise VisibleTerminalAdapterError("visible_action_request_mismatch")
            _validate_start_boundary_checkpoint(
                boundary_path,
                expected_bytes=boundary_bytes,
                expected_payload=expected_boundary,
                expected_digest=boundary_digest,
            )
            receipt = _read_json_object(receipt_path, "visible_receipt_invalid")
            reverified_report = self._validate_tester_receipt(
                receipt,
                operation_id=operation_id,
                stage_id=stage_id,
                source_digest=source_digest,
                binary_digest=binary_digest,
                settings_screenshot=settings_screenshot,
                result_screenshot=result_screenshot,
                report_screenshot=report_screenshot,
                report=report,
                boundary_digest=boundary_digest,
                dispatch_path=dispatch_path,
                action_digest=action_digest,
                optimization_intent=optimization_intent,
                readback_set=readback_set,
                tester_settings_request_digest=tester_settings_request_digest,
                compiled_deployment=compiled_deployment,
                input_binding=input_binding,
                tester_input_preset=tester_input_preset,
                preset_screenshot=preset_screenshot,
                input_readback_set=input_readback_set,
                baseline_readback_set=baseline_readback_set,
                expert_catalog_refresh_boundary_path=(
                    expert_catalog_refresh_boundary_path
                ),
                expected_expert_catalog_refresh_boundary=(
                    expected_expert_catalog_refresh_boundary
                ),
                expected_terminal_process_id=probe["processId"],
                expected_terminal_window_handle=probe["windowHandle"],
                completion_checkpoint_path=completion_checkpoint_path,
                tester_completion_evidence_checkpoint_path=(
                    tester_completion_evidence_checkpoint_path
                ),
                data_path=target["dataPath"],
                policy=policy,
                expert_ui_path=expert_ui_path,
                expert_file_name=binary.name,
                deployed_expert_path=deployed,
                report_verifier=verifier,
                strategy_execution_profile=strategy_execution_profile,
            )
            return self._tester_result(
                context,
                target,
                receipt,
                settings_screenshot,
                result_screenshot,
                report_screenshot,
                report,
                receipt_path,
                readback_set,
                preset_screenshot,
                Path(input_binding["path"]) if input_binding else None,
                input_readback_set,
                baseline_readback_set,
                completion_checkpoint_path,
                recovered=True,
                verified_report=reverified_report,
            )
        if intent_path.exists():
            if _read_json_object(intent_path, "visible_action_intent_invalid") != expected_intent:
                raise VisibleTerminalAdapterError("visible_action_intent_mismatch")
        else:
            _write_exclusive(intent_path, _canonical_json(expected_intent), "visible_action_intent_exists")
        if action_request_path.exists():
            if _read_json_object(action_request_path, "visible_action_request_invalid") != expected_action_request:
                raise VisibleTerminalAdapterError("visible_action_request_mismatch")
        else:
            _write_exclusive(
                action_request_path,
                _canonical_json(expected_action_request),
                "visible_action_request_exists",
            )
        never_start = request["safety"].get("neverStart", False) is True
        if never_start and not boundary_path.exists():
            # A service-level collect/recovery request must never create a new
            # local start boundary.  Without the committed boundary there is
            # no proof that this operation ever reached Start, so recovery is
            # intentionally uncertain and no Start-capable action is sent.
            raise VisibleTerminalAdapterError("mt5_tester_recovery_state_uncertain")
        collecting = boundary_path.exists() or never_start
        recovery_checkpoints = None
        completion_checkpoint = None
        completion_checkpoint_digest = None
        if collecting:
            _validate_start_boundary_checkpoint(
                boundary_path,
                expected_bytes=boundary_bytes,
                expected_payload=expected_boundary,
                expected_digest=boundary_digest,
            )
            dispatch_present = _dispatch_confirmation_entry_present(dispatch_path)
            if dispatch_present:
                dispatch_digest = _validate_dispatch_confirmation(
                    dispatch_path,
                    operation_id=operation_id,
                    action_digest=action_digest,
                    boundary_digest=boundary_digest,
                )
            else:
                raise VisibleTerminalAdapterError(
                    "tester_start_dispatch_unconfirmed"
                )
            recovery_checkpoints = _classify_tester_recovery_checkpoints(
                settings_screenshot=settings_screenshot,
                result_screenshot=result_screenshot,
                report_screenshot=report_screenshot,
                report=report,
                boundary_path=boundary_path,
                dispatch_path=dispatch_path,
                expert_catalog_refresh_boundary_path=(
                    expert_catalog_refresh_boundary_path
                ),
            )
            recovery_state = recovery_checkpoints["state"]
            if stage_id == "optimize":
                if recovery_state in {"completed", "collected"}:
                    completion_checkpoint, completion_checkpoint_digest = (
                        _ensure_optimization_completion_checkpoint(
                            checkpoint_path=completion_checkpoint_path,
                            allow_create=True,
                            operation_id=operation_id,
                            action_digest=action_digest,
                            boundary_digest=boundary_digest,
                            dispatch_digest=dispatch_digest,
                            data_path=target["dataPath"],
                            expert_file_name=binary.name,
                            expert_ui_path=expert_ui_path,
                            deployed_expert_sha256=binary_digest,
                            policy=policy,
                            dispatch_path=dispatch_path,
                            tester_settings_sha256=recovery_checkpoints[
                                "testerSettingsSha256"
                            ],
                            tester_result_sha256=recovery_checkpoints[
                                "testerResultSha256"
                            ],
                        )
                    )
                elif completion_checkpoint_path.exists():
                    raise VisibleTerminalAdapterError(
                        "mt5_tester_recovery_checkpoint_invalid"
                    )
                action = {
                    "in_flight": "collect_optimization",
                    "completed": "recover_completed_optimization",
                    "collected": "recover_collected_optimization",
                }[recovery_state]
            else:
                action = {
                    "in_flight": "collect_backtest",
                    "completed": "recover_completed_backtest",
                    "collected": "recover_collected_backtest",
                }[recovery_state]
        else:
            dispatch_digest = None
            recovery_state = "none"
            action = "backtest" if stage_id == "backtest_recheck" else "optimize"
        # Once the durable boundary exists every native retry is downgraded to
        # collection-only, even when the caller replays the original
        # start_round request.  The native process therefore cannot issue a
        # second Start after a transport/report-export failure.
        native_never_start = collecting
        service_action = (
            "collect_round"
            if recovery_state == "in_flight"
            else ("recover_round" if collecting else "start_round")
        )
        required_automation_ids = copy.deepcopy(
            OPTIMIZATION_TESTER_AUTOMATION_IDS
            if stage_id == "optimize"
            else BACKTEST_TESTER_AUTOMATION_IDS
        )
        expected_verified_automation_ids = copy.deepcopy(required_automation_ids)
        if stage_id == "optimize":
            expected_verified_automation_ids["criterion"] = (
                REQUIRED_TESTER_AUTOMATION_IDS["criterion"]
            )
        payload = {
            "schemaVersion": POWERSHELL_REQUEST_SCHEMA,
            "action": action,
            "platform": "mt5",
            "stageId": stage_id,
            "operationId": operation_id,
            "terminalPath": str(target["terminalPath"]),
            "compilerPath": str(target["compilerPath"]),
            "dataPath": str(target["dataPath"]),
            "deployedExpertPath": str(deployed),
            "expectedDeployedExpertSha256": binary_digest,
            "expertFileName": binary.name,
            "expertUiPath": expert_ui_path,
            "testerSettings": policy,
            "optimizationIntent": optimization_intent,
            "strategyExecutionProfile": copy.deepcopy(
                strategy_execution_profile
            ),
            "inputPresetRef": input_binding,
            "inputPresetScreenshotPath": str(preset_screenshot) if preset_screenshot else None,
            "inputPresetReadbackSetPath": str(input_readback_set) if input_readback_set else None,
            "baselineInputReadbackSetPath": (
                str(baseline_readback_set) if baseline_readback_set else None
            ),
            "settingsScreenshotPath": str(settings_screenshot),
            "resultScreenshotPath": str(result_screenshot),
            "reportScreenshotPath": str(report_screenshot),
            "testerReportExportPath": str(report_export),
            "testerReportPath": str(report),
            "inputReadbackSetPath": str(readback_set) if readback_set else None,
            "startBoundaryPath": str(boundary_path),
            "startBoundaryJson": boundary_bytes.decode("utf-8"),
            "startBoundarySha256": boundary_digest,
            "expertCatalogRefreshBoundaryPath": str(
                expert_catalog_refresh_boundary_path
            ),
            "expertCatalogRefreshBoundaryJson": (
                expert_catalog_refresh_boundary_bytes.decode("utf-8")
            ),
            "expertCatalogRefreshBoundarySha256": (
                expert_catalog_refresh_boundary_digest
            ),
            "actionRequestDigest": action_digest,
            "requiredAutomationIds": required_automation_ids,
            "optimizationCriterionAutomationId": (
                REQUIRED_TESTER_AUTOMATION_IDS["criterion"]
                if stage_id == "optimize"
                else None
            ),
            "timeoutSeconds": DEFAULT_TESTER_TIMEOUT_SECONDS,
            "expectedTerminalProcessId": probe["processId"],
            "expectedTerminalWindowHandle": probe["windowHandle"],
            "optimizationCompletionCheckpointPath": (
                str(completion_checkpoint_path) if stage_id == "optimize" else None
            ),
            "optimizationCompletionCheckpointSha256": (
                completion_checkpoint_digest if stage_id == "optimize" else None
            ),
            "testerSettingsSha256": (
                recovery_checkpoints["testerSettingsSha256"]
                if recovery_checkpoints
                else None
            ),
            "testerResultSha256": (
                recovery_checkpoints["testerResultSha256"]
                if recovery_checkpoints
                else None
            ),
            "testerReportSha256": (
                recovery_checkpoints["testerReportSha256"]
                if recovery_checkpoints
                else None
            ),
            "testerReportScreenshotSha256": (
                recovery_checkpoints["testerReportScreenshotSha256"]
                if recovery_checkpoints
                else None
            ),
            "neverStart": native_never_start,
            "serviceAction": service_action,
        }
        cached_start_response = None
        cached_start_response_digest = None
        cached_start_response_path = None
        if collecting:
            start_action = "backtest" if stage_id == "backtest_recheck" else "optimize"
            cached = _read_cached_start_response(
                response_path,
                action=start_action,
                operation_id=operation_id,
                boundary_path=boundary_path,
                dispatch_path=dispatch_path,
            )
            if cached is not None:
                cached_start_response, cached_start_response_digest, cached_start_response_path = cached
        if cached_start_response is not None:
            ui = cached_start_response
            action = "backtest" if stage_id == "backtest_recheck" else "optimize"
            expected_start = True
            collect_invoked = False
        else:
            ui = self._powershell_runner(
                payload,
                response_path=response_path,
                timeout_seconds=DEFAULT_TESTER_TIMEOUT_SECONDS,
            )
            expected_start = not collecting
            collect_invoked = collecting
        start_response_path = cached_start_response_path
        start_response_digest = cached_start_response_digest
        if expected_start and start_response_path is None:
            candidate_response_path = _powershell_action_response_path(response_path, action)
            if candidate_response_path.is_file():
                start_response_digest, _ = _stable_digest(
                    candidate_response_path, maximum_bytes=256 * 1024
                )
                start_response_path = candidate_response_path
            elif self._powershell_runner is _default_powershell_runner:
                raise VisibleTerminalAdapterError("visible_ui_response_missing")
        recovery_completion_observation = {
            "in_flight": "recovery_stop_transition_observed",
            "completed": "recovery_completed_checkpoint_observed",
            "collected": "recovery_collected_checkpoint_observed",
        }.get(recovery_state)
        recovery_transition_evidence = {
            "in_flight": None,
            "completed": "completed_result_checkpoint_after_dispatch",
            "collected": "collected_report_checkpoint_after_dispatch",
        }.get(recovery_state)
        recovery_contract_invalid = bool(
            collect_invoked
            and (
                not isinstance(ui, dict)
                or ui.get("executionObservedRunning")
                is not (recovery_state == "in_flight")
                or ui.get("completedResultCheckpointReused")
                is not (recovery_state in {"completed", "collected"})
                or ui.get("completedReportCheckpointReused")
                is not (recovery_state == "collected")
                or ui.get("testerCompletionObservation")
                != recovery_completion_observation
                or (
                    recovery_transition_evidence is not None
                    and ui.get("testerRunTransitionEvidence")
                    != recovery_transition_evidence
                )
                or (
                    recovery_state == "in_flight"
                    and ui.get("testerRunTransitionEvidence")
                    not in {
                        "native_event_stop_then_start",
                        "polled_stop_then_start",
                        "idle_after_dispatch_clean_log_completion",
                    }
                )
            )
        )
        start_contract_invalid = bool(
            not collecting
            and (
                not isinstance(ui, dict)
                or ui.get("executionObservedRunning") is not True
                or ui.get("completedResultCheckpointReused") is not False
                or ui.get("completedReportCheckpointReused") is not False
                or ui.get("testerCompletionObservation")
                != "start_stop_transition_observed"
            )
        )
        if (
            not isinstance(ui, dict)
            or ui.get("schemaVersion") != POWERSHELL_RESULT_SCHEMA
            or ui.get("action") != action
            or ui.get("operationId") != operation_id
            or ui.get("startInvoked") is not expected_start
            or (collect_invoked and ui.get("recoveredWithoutStart") is not True)
            or recovery_contract_invalid
            or start_contract_invalid
            or ui.get("testerCompleted") is not True
            or ui.get("freshResultEvidenceCaptured") is not True
            or ui.get("testerRunTransitionObserved") is not True
            or ui.get("testerRunTransitionEvidence")
            not in {
                "native_event_stop_then_start",
                "polled_stop_then_start",
                "fresh_exact_log_completion_after_dispatch",
                "idle_after_dispatch_clean_log_completion",
                "completed_result_checkpoint_after_dispatch",
                "collected_report_checkpoint_after_dispatch",
            }
            or ui.get("reportFormat")
            != ("spreadsheetml" if stage_id == "optimize" else "html")
            or (
                stage_id == "optimize"
                and ui.get("reportTabName") != "Optimization Results"
            )
            or (
                stage_id == "backtest_recheck"
                and ui.get("reportTabName") not in {"Backtest", "Results"}
            )
            or ui.get("exactExpertVerified") is not True
            or ui.get("selectedExpertReadback", "").replace("/", "\\").casefold()
            not in {expert_ui_path.casefold(), (expert_ui_path + ".ex5").casefold()}
            or ui.get("deployedExpertSha256") != binary_digest
            or ui.get("startBoundaryCommitted") is not True
            or ui.get("startBoundarySha256") != boundary_digest
            or ui.get("actionRequestDigest") != action_digest
            or ui.get("autoTradingToggled") is not False
            or ui.get("chartAttached") is not False
            or ui.get("liveTradingExecuted") is not False
            or ui.get("terminalClosedByAdapter") is not False
            or ui.get("automationControlsVerified")
            != expected_verified_automation_ids
            or (
                start_response_digest is not None
                and ui.get("durableStartResponseSha256") != start_response_digest
            )
        ):
            raise VisibleTerminalAdapterError(
                "visible_backtest_result_invalid"
                if stage_id == "backtest_recheck"
                else "visible_optimization_result_invalid"
            )
        expert_catalog_refresh_evidence, expert_catalog_refresh_evidence_digest = (
            _validate_expert_catalog_refresh_evidence(
                ui.get("expertCatalogRefreshEvidence"),
                expert_ui_path,
                expected_process_id=probe["processId"],
                expected_window_handle=probe["windowHandle"],
            )
        )
        expert_catalog_refresh_boundary_sha256 = (
            _validate_expert_catalog_refresh_boundary(
                expert_catalog_refresh_boundary_path,
                expected_expert_catalog_refresh_boundary,
                expert_catalog_refresh_evidence,
            )
        )
        _validate_start_boundary_checkpoint(
            boundary_path,
            expected_bytes=boundary_bytes,
            expected_payload=expected_boundary,
            expected_digest=boundary_digest,
        )
        dispatch_digest = _validate_dispatch_confirmation(
            dispatch_path,
            operation_id=operation_id,
            action_digest=action_digest,
            boundary_digest=boundary_digest,
        )
        if ui.get("dispatchConfirmationSha256") != dispatch_digest:
            raise VisibleTerminalAdapterError("tester_start_dispatch_unconfirmed")
        process_binding, post_binding, auto_before, auto_after = _binding_pair(
            ui, target=target, stage_id=stage_id
        )
        self._assert_probe(process_binding, probe)
        resolved = json.loads(
            _canonical_json(
                self._validate_resolved_settings(
                    ui.get("resolvedTesterSettings"),
                    policy=policy,
                    binary_name=binary.name,
                    stage_id=stage_id,
                )
            ).decode("utf-8")
        )
        tester_completion_evidence, tester_completion_evidence_digest = (
            _validate_tester_completion_evidence(
                ui.get("testerCompletionEvidence"),
                expected_marker=(
                    "optimization_finished"
                    if stage_id == "optimize"
                    else "thread_finished"
                ),
                expected_operation_id=operation_id,
                expected_expert_file_name=binary.name,
                expected_expert_ui_path=expert_ui_path,
                expected_deployed_expert_sha256=binary_digest,
                expected_symbol=resolved["symbol"],
                expected_period=resolved["period"],
            )
        )
        tester_completion_evidence_checkpoint_digest = (
            _ensure_tester_completion_evidence_checkpoint(
                tester_completion_evidence_checkpoint_path,
                tester_completion_evidence,
                allow_create=True,
            )
        )
        strategy_execution_proof, strategy_execution_proof_digest = (
            _validate_strategy_execution_proof(
                ui.get("strategyExecutionProof"),
                profile=strategy_execution_profile,
                operation_id=operation_id,
                symbol=resolved["symbol"],
                period=resolved["period"],
            )
        )
        resolved_digest = _bridge_payload_digest(
            RESOLVED_TESTER_SCHEMA, resolved
        )
        settings_digest, _ = _validate_png(settings_screenshot)
        result_digest, _ = _validate_png(result_screenshot)
        report_screenshot_digest, _ = _validate_png(report_screenshot)
        report_digest, _ = _stable_digest(
            report, maximum_bytes=_report_maximum_bytes(report)
        )
        if recovery_checkpoints and (
            settings_digest != recovery_checkpoints["testerSettingsSha256"]
            or (
                recovery_checkpoints["testerResultSha256"] is not None
                and result_digest != recovery_checkpoints["testerResultSha256"]
            )
            or (
                recovery_checkpoints["testerReportSha256"] is not None
                and report_digest != recovery_checkpoints["testerReportSha256"]
            )
            or (
                recovery_checkpoints["testerReportScreenshotSha256"] is not None
                and report_screenshot_digest
                != recovery_checkpoints["testerReportScreenshotSha256"]
            )
        ):
            raise VisibleTerminalAdapterError(
                "mt5_tester_recovery_checkpoint_mismatch"
            )
        if stage_id == "optimize":
            completion_checkpoint, completion_checkpoint_digest = (
                _ensure_optimization_completion_checkpoint(
                    checkpoint_path=completion_checkpoint_path,
                    allow_create=False,
                    operation_id=operation_id,
                    action_digest=action_digest,
                    boundary_digest=boundary_digest,
                    dispatch_digest=dispatch_digest,
                    data_path=target["dataPath"],
                    expert_file_name=binary.name,
                    expert_ui_path=expert_ui_path,
                    deployed_expert_sha256=binary_digest,
                    policy=policy,
                    dispatch_path=dispatch_path,
                    tester_settings_sha256=settings_digest,
                    tester_result_sha256=result_digest,
                )
            )
            if (
                cached_start_response is None
                and ui.get("optimizationCompletionCheckpointSha256")
                != completion_checkpoint_digest
            ):
                raise VisibleTerminalAdapterError(
                    "mt5_optimization_completion_checkpoint_mismatch"
                )
        report_size = report.stat(follow_symlinks=False).st_size
        if (
            ui.get("reportCreatedFresh") is not True
            or ui.get("reportSha256") != report_digest
            or ui.get("reportByteSize") != report_size
        ):
            raise VisibleTerminalAdapterError("mt5_report_freshness_unverified")
        report_created_at = _parse_utc(ui.get("reportCreatedAt"))
        report_last_write_at = _parse_utc(ui.get("reportLastWriteAt"))
        report_stat = report.stat(follow_symlinks=False)
        if (
            report_last_write_at < report_created_at
            or (report_created_at - datetime.now(timezone.utc)).total_seconds() > 300
            or abs(report_stat.st_ctime - report_created_at.timestamp()) > 3
            or abs(report_stat.st_mtime - report_last_write_at.timestamp()) > 3
        ):
            raise VisibleTerminalAdapterError("mt5_report_freshness_unverified")
        if cached_start_response_path is not None:
            try:
                if cached_start_response_path.stat(follow_symlinks=False).st_mtime_ns < report.stat(follow_symlinks=False).st_mtime_ns:
                    raise VisibleTerminalAdapterError("visible_ui_response_invalid")
            except OSError as error:
                raise VisibleTerminalAdapterError("visible_ui_response_invalid") from error
        verifier_context = {
            "platform": "mt5",
            "operationId": operation_id,
            "sourceDigest": source_digest,
            "compiledDigest": binary_digest,
            "deployedExpertPath": deployed,
            "resolvedTesterSettings": copy.deepcopy(resolved),
            "visibleUiResult": copy.deepcopy(ui),
        }
        if stage_id == "backtest_recheck":
            verifier_context["testerReportPath"] = report
            verifier_context["testerInputPreset"] = copy.deepcopy(tester_input_preset)
        else:
            verifier_context["optimizationReportPath"] = report
            verifier_context["optimizationIntent"] = copy.deepcopy(optimization_intent)
        verified = verifier(verifier_context)
        if not isinstance(verified, dict) or verified.get(
            "backtestVerified" if stage_id == "backtest_recheck" else "optimizationVerified"
        ) is not True:
            raise VisibleTerminalAdapterError("tester_report_verifier_result_invalid")
        if (
            verified.get("reportSha256") != report_digest
            or (
                stage_id == "optimize"
                and verified.get("optimizationPassCount")
                != tester_completion_evidence.get("completionPassCount")
            )
        ):
            raise VisibleTerminalAdapterError("tester_report_verifier_result_invalid")
        if strategy_execution_proof is not None and (
            verified.get("tradeCount")
            != strategy_execution_proof["entryCount"]
            or verified.get("buyTradeCount")
            != strategy_execution_proof["buyEntryCount"]
            or verified.get("sellTradeCount")
            != strategy_execution_proof["sellEntryCount"]
        ):
            raise VisibleTerminalAdapterError("strategy_execution_report_mismatch")
        readback_set_digest = None
        baseline_readback_digest = None
        baseline_readback_entries_digest = None
        input_preset_screenshot_digest = None
        input_preset_set_digest = None
        input_readback_digest = None
        resolved_tester_input_preset = None
        resolved_tester_input_preset_digest = None
        if stage_id == "backtest_recheck":
            if (
                preset_screenshot is None
                or input_readback_set is None
                or input_binding is None
                or tester_input_preset is None
            ):
                raise VisibleTerminalAdapterError("tester_input_preset_evidence_missing")
            input_preset_screenshot_digest, _ = _validate_png(preset_screenshot)
            input_preset_path = Path(input_binding["path"])
            input_preset_set_digest, _ = _stable_digest(
                input_preset_path, maximum_bytes=MAX_SET_BYTES
            )
            input_readback_digest, _ = _stable_digest(
                input_readback_set, maximum_bytes=MAX_SET_BYTES
            )
            input_readback_entries_digest = _assert_set_matches_expected(
                input_readback_set,
                input_binding["expectedReadbackEntries"],
                allow_native_disabled_bool_range=True,
            )
            if (
                input_preset_set_digest != input_binding["sha256"]
                or input_readback_entries_digest
                != input_binding["expectedReadbackEntriesDigest"]
                or ui.get("inputPresetSetSha256") != input_preset_set_digest
                or ui.get("inputPresetReadbackSetSha256") != input_readback_digest
                or ui.get("inputPresetReadbackEntriesDigest")
                != input_readback_entries_digest
                or verified.get("testerInputPresetReportVerified") is not True
            ):
                raise VisibleTerminalAdapterError("tester_input_preset_evidence_mismatch")
            resolved_tester_input_preset = json.loads(_canonical_json({
                "schemaVersion": RESOLVED_TESTER_INPUT_PRESET_SCHEMA,
                "presetDigest": tester_input_preset["presetDigest"],
                "sourceDigest": tester_input_preset["sourceDigest"],
                "mode": tester_input_preset["mode"],
                "scope": tester_input_preset["scope"],
                "readback": [
                    {**copy.deepcopy(item), "observedValue": item["testerValue"]}
                    for item in tester_input_preset["assumptions"]
                ],
                "visibleExpertProperties": True,
                "inputsTabSelected": True,
                "sourceDefaultsPreserved": True,
                "appliedOnlyToStrategyTester": True,
                "notAppliedToLiveChart": True,
                "readbackVerified": True,
            }).decode("utf-8"))
            resolved_tester_input_preset_digest = _bridge_payload_digest(
                RESOLVED_TESTER_INPUT_PRESET_SCHEMA, resolved_tester_input_preset
            )
        if stage_id == "optimize":
            if (
                ui.get("optimizationRangesApplied") is not True
                or ui.get("optimizationRangesReadbackVerified") is not True
                or readback_set is None
            ):
                raise VisibleTerminalAdapterError("optimization_ranges_not_verified")
            readback_set_digest, _ = _stable_digest(readback_set, maximum_bytes=MAX_SET_BYTES)
            if baseline_readback_set is None or optimization_intent is None:
                raise VisibleTerminalAdapterError("optimization_baseline_readback_missing")
            baseline_readback_digest, _ = _stable_digest(
                baseline_readback_set, maximum_bytes=MAX_SET_BYTES
            )
            baseline_readback_entries_digest = _assert_set_matches_expected(
                baseline_readback_set,
                optimization_intent["baselinePresetRef"]["expectedReadbackEntries"],
                allow_native_disabled_bool_range=True,
            )
            optimization_readback_entries_digest = _assert_set_matches_expected(
                readback_set,
                optimization_intent["setRef"]["expectedReadbackEntries"],
                allow_native_disabled_bool_range=True,
            )
            if (
                ui.get("inputReadbackSetSha256") != readback_set_digest
                or ui.get("optimizationReadbackEntriesDigest")
                != optimization_readback_entries_digest
                or ui.get("baselineReadbackSetSha256") != baseline_readback_digest
                or ui.get("baselineReadbackEntriesDigest")
                != baseline_readback_entries_digest
            ):
                raise VisibleTerminalAdapterError("optimization_readback_set_mismatch")
        post_binding = self._refresh_tester_post_process_binding(
            context=context,
            target=target,
            process_binding=process_binding,
            prior_post_binding=post_binding,
            auto_trading_state=auto_before,
        )
        auto_after = auto_before
        recovered_without_start = collecting
        if recovered_without_start:
            execution_observed_running = recovery_state == "in_flight"
            completed_result_checkpoint_reused = recovery_state in {
                "completed",
                "collected",
            }
            completed_report_checkpoint_reused = recovery_state == "collected"
            tester_completion_observation = recovery_completion_observation
            tester_transition_evidence = (
                ui["testerRunTransitionEvidence"]
                if recovery_state == "in_flight"
                else recovery_transition_evidence
            )
        else:
            execution_observed_running = True
            completed_result_checkpoint_reused = False
            completed_report_checkpoint_reused = False
            tester_completion_observation = "start_stop_transition_observed"
            tester_transition_evidence = ui["testerRunTransitionEvidence"]
        receipt = {
            "schemaVersion": RECEIPT_SCHEMA,
            "operationId": operation_id,
            "stageId": stage_id,
            "platform": "mt5",
            "terminalCandidateId": target["candidateId"],
            "status": "verified",
            "sourceDigest": source_digest,
            "compiledBinarySha256": binary_digest,
            "testerSettingsSha256": settings_digest,
            "testerResultSha256": result_digest,
            "testerReportScreenshotSha256": report_screenshot_digest,
            "testerReportSha256": report_digest,
            "actionRequestDigest": action_digest,
            "startBoundarySha256": boundary_digest,
            "dispatchConfirmationSha256": dispatch_digest,
            "optimizationCompletionCheckpointSha256": (
                completion_checkpoint_digest if stage_id == "optimize" else None
            ),
            "optimizationCacheLineage": (
                copy.deepcopy(completion_checkpoint["optimizationCacheLineage"])
                if completion_checkpoint is not None
                else None
            ),
            "optimizationCacheLineageDigest": (
                completion_checkpoint["optimizationCacheLineageDigest"]
                if completion_checkpoint is not None
                else None
            ),
            "expertCatalogRefreshEvidence": expert_catalog_refresh_evidence,
            "expertCatalogRefreshEvidenceDigest": expert_catalog_refresh_evidence_digest,
            "expertCatalogRefreshBoundarySha256": (
                expert_catalog_refresh_boundary_sha256
            ),
            "reportCreatedFresh": True,
            "reportCreatedAt": ui["reportCreatedAt"],
            "reportLastWriteAt": ui["reportLastWriteAt"],
            "reportFormat": ui["reportFormat"],
            "reportTabName": ui["reportTabName"],
            "testerCompletionEvidence": tester_completion_evidence,
            "testerCompletionEvidenceDigest": tester_completion_evidence_digest,
            "testerCompletionEvidenceCheckpointSha256": (
                tester_completion_evidence_checkpoint_digest
            ),
            "strategyExecutionProfile": copy.deepcopy(
                strategy_execution_profile
            ),
            "strategyExecutionProof": copy.deepcopy(
                strategy_execution_proof
            ),
            "strategyExecutionProofDigest": strategy_execution_proof_digest,
            "recoveredPowerShellStartResponse": cached_start_response is not None,
            "cachedStartResponseSha256": cached_start_response_digest,
            "startResponseSha256": start_response_digest,
            "resolvedTesterSettings": resolved,
            "resolvedTesterSettingsDigest": resolved_digest,
            "testerSettingsRequestDigest": tester_settings_request_digest,
            "processBinding": process_binding,
            "postProcessBinding": post_binding,
            "processBindingDigest": process_binding["processBindingDigest"],
            "postProcessBindingDigest": post_binding["processBindingDigest"],
            "autoTradingStateBefore": auto_before,
            "autoTradingStateAfter": auto_after,
            "testerInputPresetDigest": (
                tester_input_preset["presetDigest"] if tester_input_preset else None
            ),
            "resolvedTesterInputPreset": resolved_tester_input_preset,
            "resolvedTesterInputPresetDigest": resolved_tester_input_preset_digest,
            "testerInputPresetScreenshotSha256": input_preset_screenshot_digest,
            "testerInputPresetSetSha256": input_preset_set_digest,
            "testerInputReadbackSetSha256": input_readback_digest,
            "testerInputPresetReportVerified": stage_id == "backtest_recheck",
            "testerInputManifestDigest": (
                input_binding["inputManifestDigest"] if input_binding else None
            ),
            "testerInputPresetRefDigest": (
                input_binding["refDigest"] if input_binding else None
            ),
            "testerInputExpectedReadbackEntriesDigest": (
                input_binding["expectedReadbackEntriesDigest"] if input_binding else None
            ),
            "testerInputReadbackEntriesDigest": (
                input_binding["expectedReadbackEntriesDigest"] if input_binding else None
            ),
            "compiledDeploymentRef": compiled_deployment["deploymentRef"],
            "compiledDeploymentDigest": compiled_deployment["bindingDigest"],
            "optimizationSetSha256": (
                optimization_intent["setDigest"] if optimization_intent else None
            ),
            "optimizationRangesDigest": (
                optimization_intent["rangesDigest"] if optimization_intent else None
            ),
            "optimizationReadbackSetSha256": readback_set_digest,
            "inputManifestDigest": (
                optimization_intent["inputManifestDigest"] if optimization_intent else None
            ),
            "optimizationSetRefDigest": (
                optimization_intent["setRef"]["refDigest"] if optimization_intent else None
            ),
            "optimizationExpectedReadbackEntriesDigest": (
                optimization_intent["setRef"]["expectedReadbackEntriesDigest"]
                if optimization_intent
                else None
            ),
            "baselinePresetRefDigest": (
                optimization_intent["baselinePresetRef"]["refDigest"]
                if optimization_intent
                else None
            ),
            "baselineExpectedReadbackEntriesDigest": (
                optimization_intent["baselinePresetRef"]["expectedReadbackEntriesDigest"]
                if optimization_intent
                else None
            ),
            "baselineReadbackSetSha256": baseline_readback_digest,
            "baselineReadbackEntriesDigest": baseline_readback_entries_digest,
            "tradeCount": verified.get("tradeCount") if stage_id == "backtest_recheck" else None,
            "tradeRowCount": verified.get("tradeRowCount") if stage_id == "backtest_recheck" else None,
            "buyTradeCount": verified.get("buyTradeCount") if stage_id == "backtest_recheck" else None,
            "sellTradeCount": verified.get("sellTradeCount") if stage_id == "backtest_recheck" else None,
            "zeroTrade": verified.get("zeroTrade") if stage_id == "backtest_recheck" else None,
            "testerTradeRowsVerified": verified.get("testerTradeRowsVerified") if stage_id == "backtest_recheck" else None,
            "mismatchedChartErrors": verified.get("mismatchedChartErrors") if stage_id == "backtest_recheck" else None,
            "historyQualityIssue": verified.get("historyQualityIssue") if stage_id == "backtest_recheck" else None,
            "historyQualityVerified": verified.get("historyQualityVerified") if stage_id == "backtest_recheck" else None,
            "attentionRequired": verified.get("attentionRequired") if stage_id == "backtest_recheck" else None,
            "attentionReasonCode": verified.get("attentionReasonCode") if stage_id == "backtest_recheck" else None,
            "performanceEvaluationAvailable": verified.get("performanceEvaluationAvailable") if stage_id == "backtest_recheck" else None,
            "executionOutcome": verified.get("executionOutcome") if stage_id == "backtest_recheck" else None,
            "optimizationPassCount": (
                verified.get("optimizationPassCount") if stage_id == "optimize" else None
            ),
            "optimizationReturnedPassCount": (
                verified.get("optimizationReturnedPassCount")
                if stage_id == "optimize"
                else None
            ),
            "optimizationRowsTruncated": (
                verified.get("optimizationRowsTruncated")
                if stage_id == "optimize"
                else None
            ),
            "optimizationResultRows": (
                copy.deepcopy(verified.get("optimizationResultRows"))
                if stage_id == "optimize"
                else None
            ),
            "optimizationSymbolUniverse": (
                copy.deepcopy(verified.get("optimizationSymbolUniverse"))
                if stage_id == "optimize"
                else None
            ),
            "optimizationSymbolUniverseDigest": (
                verified.get("optimizationSymbolUniverseDigest")
                if stage_id == "optimize"
                else None
            ),
            "visualMode": stage_id == "backtest_recheck",
            "optimizationEnabled": stage_id == "optimize",
            "shutdownTerminalAfterTest": False,
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "recoveredWithoutStart": recovered_without_start,
            "startInvoked": not recovered_without_start,
            "executionObservedRunning": execution_observed_running,
            "completedResultCheckpointReused": completed_result_checkpoint_reused,
            "completedReportCheckpointReused": completed_report_checkpoint_reused,
            "testerCompletionObservation": tester_completion_observation,
            "testerRunTransitionObserved": True,
            "testerRunTransitionEvidence": tester_transition_evidence,
            "recoveryIssuedStart": False,
        }
        final_report_digest, final_report_size = _stable_digest(
            report, maximum_bytes=_report_maximum_bytes(report)
        )
        if final_report_size != report_size or not secrets.compare_digest(
            final_report_digest, report_digest
        ):
            raise VisibleTerminalAdapterError(
                "tester_report_verifier_result_invalid"
            )
        _write_exclusive(receipt_path, _canonical_json(receipt), "visible_receipt_already_exists")
        if start_response_path is not None:
            try:
                start_response_path.unlink(missing_ok=True)
            except OSError:
                # The durable receipt is already authoritative.  A stale
                # transport copy cannot cause another Start and is harmless.
                pass
        return self._tester_result(
            context,
            target,
            receipt,
            settings_screenshot,
            result_screenshot,
            report_screenshot,
            report,
            receipt_path,
            readback_set,
            preset_screenshot,
            Path(input_binding["path"]) if input_binding else None,
            input_readback_set,
            baseline_readback_set,
            completion_checkpoint_path,
            recovered=False,
            verified_report=verified,
        )

    @staticmethod
    def _validate_resolved_settings(
        raw: object, *, policy: dict, binary_name: str, stage_id: str
    ) -> dict:
        required = {
            "schemaVersion",
            "expertFileName",
            "symbol",
            "period",
            "model",
            "spread",
            "useDate",
            "fromDate",
            "toDate",
            "deposit",
            "visualMode",
            "optimizationEnabled",
            "shutdownTerminalAfterTest",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise VisibleTerminalAdapterError("tester_settings_readback_invalid")
        if (
            raw.get("schemaVersion") != RESOLVED_TESTER_SCHEMA
            or raw.get("expertFileName") != binary_name
            or SAFE_SYMBOL.fullmatch(str(raw.get("symbol") or "")) is None
            or raw.get("period") != policy["period"]
            or raw.get("model") != policy["model"]
            or not str(raw.get("spread") or "").strip()
            or raw.get("useDate") is not policy["useDate"]
            or raw.get("fromDate") != policy["fromDate"]
            or raw.get("toDate") != policy["toDate"]
            or isinstance(raw.get("deposit"), bool)
            or not isinstance(raw.get("deposit"), (int, float))
            or not (0 < float(raw["deposit"]) <= 1_000_000_000)
            or raw.get("visualMode") is not (stage_id == "backtest_recheck")
            or raw.get("optimizationEnabled") is not (stage_id == "optimize")
            or raw.get("shutdownTerminalAfterTest") is not False
        ):
            raise VisibleTerminalAdapterError("tester_settings_readback_invalid")
        if policy.get("symbol") is not None and raw.get("symbol") != policy["symbol"]:
            raise VisibleTerminalAdapterError("tester_symbol_readback_mismatch")
        return copy.deepcopy(raw)

    @staticmethod
    def _validate_tester_receipt(
        receipt: dict,
        *,
        operation_id: str,
        stage_id: str,
        source_digest: str,
        binary_digest: str,
        settings_screenshot: Path,
        result_screenshot: Path,
        report_screenshot: Path,
        report: Path,
        boundary_digest: str,
        dispatch_path: Path,
        action_digest: str,
        optimization_intent: dict | None,
        readback_set: Path | None,
        tester_settings_request_digest: str,
        compiled_deployment: dict,
        input_binding: dict | None,
        tester_input_preset: dict | None,
        preset_screenshot: Path | None,
        input_readback_set: Path | None,
        baseline_readback_set: Path | None,
        expert_catalog_refresh_boundary_path: Path,
        expected_expert_catalog_refresh_boundary: dict,
        expected_terminal_process_id: int,
        expected_terminal_window_handle: int,
        completion_checkpoint_path: Path,
        tester_completion_evidence_checkpoint_path: Path,
        data_path: Path,
        policy: dict,
        expert_ui_path: str,
        expert_file_name: str,
        deployed_expert_path: Path,
        report_verifier: Callable[[dict], dict],
        strategy_execution_profile: dict | None,
    ) -> dict:
        settings_digest, _ = _validate_png(settings_screenshot)
        result_digest, _ = _validate_png(result_screenshot)
        report_screenshot_digest, _ = _validate_png(report_screenshot)
        report_digest, report_size = _stable_digest(
            report, maximum_bytes=_report_maximum_bytes(report)
        )
        dispatch_digest = _validate_dispatch_confirmation(
            dispatch_path,
            operation_id=operation_id,
            action_digest=action_digest,
            boundary_digest=boundary_digest,
        )
        completion_checkpoint = None
        completion_checkpoint_digest = None
        if stage_id == "optimize":
            completion_checkpoint, completion_checkpoint_digest = (
                _ensure_optimization_completion_checkpoint(
                    checkpoint_path=completion_checkpoint_path,
                    allow_create=False,
                    operation_id=operation_id,
                    action_digest=action_digest,
                    boundary_digest=boundary_digest,
                    dispatch_digest=dispatch_digest,
                    data_path=data_path,
                    expert_file_name=expert_file_name,
                    expert_ui_path=expert_ui_path,
                    deployed_expert_sha256=binary_digest,
                    policy=policy,
                    dispatch_path=dispatch_path,
                    tester_settings_sha256=settings_digest,
                    tester_result_sha256=result_digest,
                )
            )
        readback_digest = (
            _stable_digest(readback_set, maximum_bytes=MAX_SET_BYTES)[0]
            if readback_set is not None
            else None
        )
        baseline_readback_digest = (
            _stable_digest(baseline_readback_set, maximum_bytes=MAX_SET_BYTES)[0]
            if baseline_readback_set is not None
            else None
        )
        input_readback_digest = (
            _stable_digest(input_readback_set, maximum_bytes=MAX_SET_BYTES)[0]
            if input_readback_set is not None
            else None
        )
        preset_screenshot_digest = (
            _validate_png(preset_screenshot)[0]
            if preset_screenshot is not None
            else None
        )
        input_preset_set_digest = (
            _stable_digest(Path(input_binding["path"]), maximum_bytes=MAX_SET_BYTES)[0]
            if input_binding is not None
            else None
        )
        expected_expert_ui_path = (
            Path("Metafxclub")
            / "AgentHQ"
            / "Deployments"
            / compiled_deployment["deploymentRef"]
            / Path(compiled_deployment["expertFileName"]).stem
        ).as_posix().replace("/", "\\")
        expert_catalog_refresh_evidence, expert_catalog_refresh_evidence_digest = (
            _validate_expert_catalog_refresh_evidence(
                receipt.get("expertCatalogRefreshEvidence"),
                expected_expert_ui_path,
                expected_process_id=expected_terminal_process_id,
                expected_window_handle=expected_terminal_window_handle,
            )
        )
        expert_catalog_refresh_boundary_sha256 = (
            _validate_expert_catalog_refresh_boundary(
                expert_catalog_refresh_boundary_path,
                expected_expert_catalog_refresh_boundary,
                expert_catalog_refresh_evidence,
            )
        )
        process_binding = receipt.get("processBinding")
        post_binding = receipt.get("postProcessBinding")
        resolved = VisibleFrontOfficeAdapterMt5._validate_resolved_settings(
            receipt.get("resolvedTesterSettings"),
            policy=policy,
            binary_name=expert_file_name,
            stage_id=stage_id,
        )
        expected_resolved_digest = _bridge_payload_digest(
            RESOLVED_TESTER_SCHEMA, resolved
        )
        resolved_preset = receipt.get("resolvedTesterInputPreset")
        expected_resolved_preset_digest = (
            _bridge_payload_digest(RESOLVED_TESTER_INPUT_PRESET_SCHEMA, resolved_preset)
            if isinstance(resolved_preset, dict)
            else None
        )
        report_created_at = _parse_utc(receipt.get("reportCreatedAt"))
        report_last_write_at = _parse_utc(receipt.get("reportLastWriteAt"))
        tester_completion_evidence, tester_completion_evidence_digest = (
            _validate_tester_completion_evidence(
                receipt.get("testerCompletionEvidence"),
                expected_marker=(
                    "optimization_finished"
                    if stage_id == "optimize"
                    else "thread_finished"
                ),
                expected_operation_id=operation_id,
                expected_expert_file_name=expert_file_name,
                expected_expert_ui_path=expert_ui_path,
                expected_deployed_expert_sha256=binary_digest,
                expected_symbol=resolved["symbol"],
                expected_period=resolved["period"],
            )
        )
        tester_completion_evidence_checkpoint_digest = (
            _ensure_tester_completion_evidence_checkpoint(
                tester_completion_evidence_checkpoint_path,
                tester_completion_evidence,
                allow_create=False,
            )
        )
        strategy_execution_proof, strategy_execution_proof_digest = (
            _validate_strategy_execution_proof(
                receipt.get("strategyExecutionProof"),
                profile=strategy_execution_profile,
                operation_id=operation_id,
                symbol=resolved["symbol"],
                period=resolved["period"],
            )
        )
        verifier_context = {
            "platform": "mt5",
            "operationId": operation_id,
            "sourceDigest": source_digest,
            "compiledDigest": binary_digest,
            "deployedExpertPath": deployed_expert_path,
            "resolvedTesterSettings": copy.deepcopy(resolved),
            "visibleUiResult": copy.deepcopy(receipt),
        }
        if stage_id == "backtest_recheck":
            verifier_context["testerReportPath"] = report
            verifier_context["testerInputPreset"] = copy.deepcopy(
                tester_input_preset
            )
        else:
            verifier_context["optimizationReportPath"] = report
            verifier_context["optimizationIntent"] = copy.deepcopy(
                optimization_intent
            )
        reverified_report = report_verifier(verifier_context)
        expected_verified_flag = (
            "backtestVerified"
            if stage_id == "backtest_recheck"
            else "optimizationVerified"
        )
        if (
            not isinstance(reverified_report, dict)
            or reverified_report.get(expected_verified_flag) is not True
            or reverified_report.get("reportSha256") != report_digest
            or (
                stage_id == "optimize"
                and reverified_report.get("optimizationPassCount")
                != tester_completion_evidence.get("completionPassCount")
            )
        ):
            raise VisibleTerminalAdapterError(
                "visible_receipt_report_reverification_failed"
            )
        report_stat = report.stat(follow_symlinks=False)
        if (
            report_last_write_at < report_created_at
            or abs(report_stat.st_ctime - report_created_at.timestamp()) > 3
            or abs(report_stat.st_mtime - report_last_write_at.timestamp()) > 3
        ):
            raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")
        transition_evidence = receipt.get("testerRunTransitionEvidence")
        execution_contract_valid = any(
            (
                receipt.get("recoveredWithoutStart") is recovered_without_start
                and receipt.get("startInvoked") is start_invoked
                and receipt.get("executionObservedRunning") is observed_running
                and receipt.get("completedResultCheckpointReused")
                is result_reused
                and receipt.get("completedReportCheckpointReused")
                is report_reused
                and receipt.get("testerCompletionObservation") == observation
                and transition_evidence in allowed_transition
            )
            for (
                recovered_without_start,
                start_invoked,
                observed_running,
                result_reused,
                report_reused,
                observation,
                allowed_transition,
            ) in (
                (
                    False,
                    True,
                    True,
                    False,
                    False,
                    "start_stop_transition_observed",
                    {
                        "native_event_stop_then_start",
                        "polled_stop_then_start",
                        "fresh_exact_log_completion_after_dispatch",
                    },
                ),
                (
                    True,
                    False,
                    True,
                    False,
                    False,
                    "recovery_stop_transition_observed",
                    {
                        "native_event_stop_then_start",
                        "polled_stop_then_start",
                        "idle_after_dispatch_clean_log_completion",
                    },
                ),
                (
                    True,
                    False,
                    False,
                    True,
                    False,
                    "recovery_completed_checkpoint_observed",
                    {"completed_result_checkpoint_after_dispatch"},
                ),
                (
                    True,
                    False,
                    False,
                    True,
                    True,
                    "recovery_collected_checkpoint_observed",
                    {"collected_report_checkpoint_after_dispatch"},
                ),
            )
        )
        if (
            receipt.get("schemaVersion") != RECEIPT_SCHEMA
            or receipt.get("operationId") != operation_id
            or receipt.get("stageId") != stage_id
            or receipt.get("sourceDigest") != source_digest
            or receipt.get("compiledBinarySha256") != binary_digest
            or receipt.get("testerSettingsSha256") != settings_digest
            or receipt.get("testerResultSha256") != result_digest
            or receipt.get("testerReportScreenshotSha256") != report_screenshot_digest
            or receipt.get("testerReportSha256") != report_digest
            or receipt.get("testerCompletionEvidence")
            != tester_completion_evidence
            or receipt.get("testerCompletionEvidenceDigest")
            != tester_completion_evidence_digest
            or receipt.get("testerCompletionEvidenceCheckpointSha256")
            != tester_completion_evidence_checkpoint_digest
            or receipt.get("strategyExecutionProfile")
            != strategy_execution_profile
            or receipt.get("strategyExecutionProof")
            != strategy_execution_proof
            or receipt.get("strategyExecutionProofDigest")
            != strategy_execution_proof_digest
            or receipt.get("startBoundarySha256") != boundary_digest
            or receipt.get("dispatchConfirmationSha256") != dispatch_digest
            or receipt.get("optimizationCompletionCheckpointSha256")
            != completion_checkpoint_digest
            or receipt.get("optimizationCacheLineage")
            != (
                completion_checkpoint["optimizationCacheLineage"]
                if completion_checkpoint is not None
                else None
            )
            or receipt.get("optimizationCacheLineageDigest")
            != (
                completion_checkpoint["optimizationCacheLineageDigest"]
                if completion_checkpoint is not None
                else None
            )
            or receipt.get("actionRequestDigest") != action_digest
            or receipt.get("expertCatalogRefreshEvidenceDigest")
            != expert_catalog_refresh_evidence_digest
            or receipt.get("expertCatalogRefreshBoundarySha256")
            != expert_catalog_refresh_boundary_sha256
            or receipt.get("reportCreatedFresh") is not True
            or receipt.get("reportFormat")
            != ("spreadsheetml" if stage_id == "optimize" else "html")
            or (
                stage_id == "optimize"
                and receipt.get("reportTabName") != "Optimization Results"
            )
            or (
                stage_id == "backtest_recheck"
                and receipt.get("reportTabName") not in {"Backtest", "Results"}
            )
            or receipt.get("compiledDeploymentRef")
            != compiled_deployment["deploymentRef"]
            or receipt.get("compiledDeploymentDigest")
            != compiled_deployment["bindingDigest"]
            or (
                receipt.get("startResponseSha256") is not None
                and SHA256.fullmatch(str(receipt.get("startResponseSha256"))) is None
            )
            or not isinstance(receipt.get("recoveredPowerShellStartResponse"), bool)
            or (
                receipt.get("recoveredPowerShellStartResponse") is True
                and SHA256.fullmatch(
                    str(receipt.get("cachedStartResponseSha256") or "")
                )
                is None
            )
            or (
                receipt.get("recoveredPowerShellStartResponse") is False
                and receipt.get("cachedStartResponseSha256") is not None
            )
            or not isinstance(process_binding, dict)
            or not isinstance(post_binding, dict)
            or receipt.get("processBindingDigest")
            != process_binding.get("processBindingDigest")
            or receipt.get("postProcessBindingDigest")
            != post_binding.get("processBindingDigest")
            or receipt.get("resolvedTesterSettingsDigest")
            != expected_resolved_digest
            or receipt.get("resolvedTesterInputPresetDigest")
            != expected_resolved_preset_digest
            or receipt.get("testerSettingsRequestDigest")
            != tester_settings_request_digest
            or not isinstance(receipt.get("autoTradingStateBefore"), bool)
            or receipt.get("autoTradingStateAfter")
            is not receipt.get("autoTradingStateBefore")
            or receipt.get("liveTradingExecuted") is not False
            or receipt.get("autoTradingToggled") is not False
            or receipt.get("chartAttached") is not False
            or receipt.get("terminalClosedByAdapter") is not False
            or receipt.get("testerRunTransitionObserved") is not True
            or receipt.get("recoveryIssuedStart") is not False
            or not execution_contract_valid
            or receipt.get("optimizationSetSha256")
            != (optimization_intent["setDigest"] if optimization_intent else None)
            or receipt.get("optimizationRangesDigest")
            != (optimization_intent["rangesDigest"] if optimization_intent else None)
            or receipt.get("optimizationReadbackSetSha256") != readback_digest
            or receipt.get("visualMode") is not (stage_id == "backtest_recheck")
            or receipt.get("optimizationEnabled") is not (stage_id == "optimize")
            or receipt.get("shutdownTerminalAfterTest") is not False
        ):
            raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")
        if stage_id == "backtest_recheck":
            report_fields = (
                "testerTradeRowsVerified",
                "testerInputPresetReportVerified",
                "tradeCount",
                "tradeRowCount",
                "buyTradeCount",
                "sellTradeCount",
                "zeroTrade",
                "mismatchedChartErrors",
                "historyQualityIssue",
                "historyQualityVerified",
                "attentionRequired",
                "attentionReasonCode",
                "performanceEvaluationAvailable",
                "executionOutcome",
            )
            counts = (
                receipt.get("tradeCount"),
                receipt.get("tradeRowCount"),
                receipt.get("buyTradeCount"),
                receipt.get("sellTradeCount"),
            )
            if (
                any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts)
                or counts[0] != counts[1]
                or counts[2] + counts[3] != counts[0]
                or input_binding is None
                or tester_input_preset is None
                or receipt.get("testerInputPresetDigest")
                != tester_input_preset["presetDigest"]
                or receipt.get("testerInputPresetScreenshotSha256")
                != preset_screenshot_digest
                or receipt.get("testerInputPresetSetSha256")
                != input_preset_set_digest
                or receipt.get("testerInputReadbackSetSha256")
                != input_readback_digest
                or receipt.get("testerInputPresetReportVerified") is not True
                or receipt.get("testerInputManifestDigest")
                != input_binding["inputManifestDigest"]
                or receipt.get("testerInputPresetRefDigest")
                != input_binding["refDigest"]
                or receipt.get("testerInputExpectedReadbackEntriesDigest")
                != input_binding["expectedReadbackEntriesDigest"]
                or receipt.get("testerInputReadbackEntriesDigest")
                != input_binding["expectedReadbackEntriesDigest"]
                or input_readback_set is None
                or _assert_set_matches_expected(
                    input_readback_set,
                    input_binding["expectedReadbackEntries"],
                    allow_native_disabled_bool_range=True,
                )
                != input_binding["expectedReadbackEntriesDigest"]
                or not isinstance(resolved_preset, dict)
                or any(
                    receipt.get(field) != reverified_report.get(field)
                    for field in report_fields
                )
                or (
                    strategy_execution_proof is not None
                    and (
                        counts[0]
                        != strategy_execution_proof["entryCount"]
                        or counts[2]
                        != strategy_execution_proof["buyEntryCount"]
                        or counts[3]
                        != strategy_execution_proof["sellEntryCount"]
                    )
                )
            ):
                raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")
            attention = _backtest_attention_fields(
                counts[0] == 0, receipt.get("mismatchedChartErrors")
            ) if (
                isinstance(receipt.get("mismatchedChartErrors"), int)
                and not isinstance(receipt.get("mismatchedChartErrors"), bool)
                and receipt.get("mismatchedChartErrors") >= 0
            ) else None
            if attention is None or any(
                receipt.get(key) != value for key, value in attention.items()
            ):
                raise VisibleTerminalAdapterError("visible_receipt_evidence_mismatch")
        else:
            report_fields = (
                "optimizationPassCount",
                "optimizationReturnedPassCount",
                "optimizationRowsTruncated",
                "optimizationResultRows",
                "optimizationSymbolUniverse",
                "optimizationSymbolUniverseDigest",
            )
            pass_count = receipt.get("optimizationPassCount")
            returned = receipt.get("optimizationReturnedPassCount")
            rows = receipt.get("optimizationResultRows")
            _validate_optimization_symbol_universe(
                receipt.get("optimizationSymbolUniverse"),
                receipt.get("optimizationSymbolUniverseDigest"),
                required=bool(
                    optimization_intent is not None
                    and optimization_intent.get("mode")
                    == "all_symbols_market_watch"
                ),
                result_rows=rows,
                complete_result_rows=bool(
                    isinstance(returned, int)
                    and not isinstance(returned, bool)
                    and isinstance(pass_count, int)
                    and not isinstance(pass_count, bool)
                    and returned == pass_count
                ),
            )
            if (
                isinstance(pass_count, bool)
                or not isinstance(pass_count, int)
                or pass_count < 2
                or isinstance(returned, bool)
                or not isinstance(returned, int)
                or returned < 2
                or returned > pass_count
                or not isinstance(rows, list)
                or len(rows) != returned
                or any(not isinstance(row, dict) or not row for row in rows)
                or receipt.get("optimizationRowsTruncated")
                is not (returned < pass_count)
                or optimization_intent is None
                or receipt.get("inputManifestDigest")
                != optimization_intent["inputManifestDigest"]
                or receipt.get("optimizationSetRefDigest")
                != optimization_intent["setRef"]["refDigest"]
                or receipt.get("optimizationExpectedReadbackEntriesDigest")
                != optimization_intent["setRef"]["expectedReadbackEntriesDigest"]
                or receipt.get("baselinePresetRefDigest")
                != optimization_intent["baselinePresetRef"]["refDigest"]
                or receipt.get("baselineExpectedReadbackEntriesDigest")
                != optimization_intent["baselinePresetRef"][
                    "expectedReadbackEntriesDigest"
                ]
                or receipt.get("baselineReadbackSetSha256")
                != baseline_readback_digest
                or receipt.get("baselineReadbackEntriesDigest")
                != optimization_intent["baselinePresetRef"][
                    "expectedReadbackEntriesDigest"
                ]
                or baseline_readback_set is None
                or _assert_set_matches_expected(
                    baseline_readback_set,
                    optimization_intent["baselinePresetRef"][
                        "expectedReadbackEntries"
                    ],
                    allow_native_disabled_bool_range=True,
                )
                != optimization_intent["baselinePresetRef"][
                    "expectedReadbackEntriesDigest"
                ]
                or readback_set is None
                or _assert_set_matches_expected(
                    readback_set,
                    optimization_intent["setRef"]["expectedReadbackEntries"],
                    allow_native_disabled_bool_range=True,
                )
                != optimization_intent["setRef"][
                    "expectedReadbackEntriesDigest"
                ]
                or any(
                    receipt.get(field) != reverified_report.get(field)
                    for field in report_fields
                )
            ):
                raise VisibleTerminalAdapterError(
                    "visible_receipt_optimization_evidence_mismatch"
                )
        final_report_digest, final_report_size = _stable_digest(
            report, maximum_bytes=_report_maximum_bytes(report)
        )
        if final_report_size != report_size or not secrets.compare_digest(
            final_report_digest, report_digest
        ):
            raise VisibleTerminalAdapterError(
                "visible_receipt_report_reverification_failed"
            )
        return copy.deepcopy(reverified_report)

    @staticmethod
    def _tester_result(
        context: dict,
        target: dict,
        receipt: dict,
        settings_screenshot: Path,
        result_screenshot: Path,
        report_screenshot: Path,
        report: Path,
        receipt_path: Path,
        readback_set: Path | None,
        preset_screenshot: Path | None,
        input_preset_set: Path | None,
        input_readback_set: Path | None,
        baseline_readback_set: Path | None,
        completion_checkpoint_path: Path,
        *,
        recovered: bool,
        verified_report: dict,
    ) -> dict:
        stage_id = context["stageId"]
        optimize = stage_id == "optimize"
        workspace = context["workspace"]
        metrics = {
            "evidenceMode": EVIDENCE_MODE,
            "operationId": context["operation"]["operationId"],
            "eaFactoryStage": stage_id,
            "platform": "mt5",
            "terminalCandidateId": target["candidateId"],
            "terminalSelectionRevision": target["selectionRevision"],
            "terminalBindingDigest": target["bindingDigest"],
            "processBinding": copy.deepcopy(receipt["processBinding"]),
            "processBindingDigest": receipt["processBinding"]["processBindingDigest"],
            "postProcessBinding": copy.deepcopy(receipt["postProcessBinding"]),
            "postProcessBindingDigest": receipt["postProcessBinding"]["processBindingDigest"],
            "processId": receipt["processBinding"]["frontOfficeProcessId"],
            "windowHandle": receipt["processBinding"]["frontOfficeWindowHandle"],
            "compiledBinarySha256": receipt["compiledBinarySha256"],
            "compiledBinaryArtifactAlias": "compiled_binary",
            "compiledDeploymentRef": receipt.get("compiledDeploymentRef"),
            "compiledDeploymentDigest": receipt.get("compiledDeploymentDigest"),
            "sourceDigest": receipt["sourceDigest"],
            "expertFileName": receipt["resolvedTesterSettings"]["expertFileName"],
            "resolvedTesterSettings": copy.deepcopy(receipt["resolvedTesterSettings"]),
            "resolvedTesterSettingsDigest": receipt["resolvedTesterSettingsDigest"],
            "testerSettingsRequestDigest": receipt["testerSettingsRequestDigest"],
            "expertCatalogRefreshEvidence": copy.deepcopy(
                receipt["expertCatalogRefreshEvidence"]
            ),
            "expertCatalogRefreshEvidenceDigest": receipt[
                "expertCatalogRefreshEvidenceDigest"
            ],
            "testerInputPresetApplied": not optimize,
            "testerInputPresetReadbackVerified": not optimize,
            "testerInputPresetReportVerified": (
                verified_report.get("testerInputPresetReportVerified") is True
            ),
            "simulationAssumptionsExplicit": not optimize,
            "testerInputPresetDigest": receipt.get("testerInputPresetDigest"),
            "resolvedTesterInputPreset": copy.deepcopy(
                receipt.get("resolvedTesterInputPreset")
            ),
            "resolvedTesterInputPresetDigest": receipt.get(
                "resolvedTesterInputPresetDigest"
            ),
            "inputPresetScreenshotArtifactAlias": (
                "tester_input_preset" if not optimize else None
            ),
            "inputPresetScreenshotSha256": receipt.get(
                "testerInputPresetScreenshotSha256"
            ),
            "inputPresetSetArtifactAlias": (
                "tester_input_preset_set" if not optimize else None
            ),
            "inputPresetSetSha256": receipt.get("testerInputPresetSetSha256"),
            "inputReadbackSetArtifactAlias": (
                "tester_input_readback_set" if not optimize else None
            ),
            "inputReadbackSetSha256": receipt.get("testerInputReadbackSetSha256"),
            "testerInputManifestDigest": receipt.get("testerInputManifestDigest"),
            "testerInputPresetRefDigest": receipt.get("testerInputPresetRefDigest"),
            "testerInputExpectedReadbackEntriesDigest": receipt.get(
                "testerInputExpectedReadbackEntriesDigest"
            ),
            "testerInputReadbackEntriesDigest": receipt.get(
                "testerInputReadbackEntriesDigest"
            ),
            "settingsScreenshotArtifactAlias": "tester_settings",
            "settingsScreenshotSha256": receipt["testerSettingsSha256"],
            "resultScreenshotArtifactAlias": "tester_result",
            "resultScreenshotSha256": receipt["testerResultSha256"],
            "visibleWindowEvidenceArtifactAlias": "tester_result",
            "visibleWindowEvidenceSha256": receipt["testerResultSha256"],
            "reportScreenshotArtifactAlias": "tester_report_proof",
            "reportScreenshotSha256": receipt["testerReportScreenshotSha256"],
            "testerReportArtifactAlias": "optimization_report" if optimize else "tester_report",
            "testerReportSha256": receipt["testerReportSha256"],
            "testerReportFormat": receipt["reportFormat"],
            "testerReportTabName": receipt["reportTabName"],
            "visibleStrategyTester": True,
            "visibleOptimization": optimize,
            "visualMode": not optimize,
            "optimizationEnabled": optimize,
            "backtestVerified": not optimize,
            "optimizationVerified": optimize,
            # These fields describe whether this invocation actually pressed Start.
            # A recovery/receipt replay can still return verified results, but must
            # never imply that it launched a second tester run.
            "backtestExecuted": (
                not optimize
                and not recovered
                and receipt.get("startInvoked") is True
            ),
            "optimizationExecuted": (
                optimize
                and not recovered
                and receipt.get("startInvoked") is True
            ),
            "testerTradeRowsVerified": verified_report.get("testerTradeRowsVerified") if not optimize else None,
            "tradeCount": verified_report.get("tradeCount") if not optimize else None,
            "tradeRowCount": verified_report.get("tradeRowCount") if not optimize else None,
            "buyTradeCount": verified_report.get("buyTradeCount") if not optimize else None,
            "sellTradeCount": verified_report.get("sellTradeCount") if not optimize else None,
            "zeroTrade": verified_report.get("zeroTrade") if not optimize else None,
            "mismatchedChartErrors": verified_report.get("mismatchedChartErrors") if not optimize else None,
            "historyQualityIssue": verified_report.get("historyQualityIssue") if not optimize else None,
            "historyQualityVerified": verified_report.get("historyQualityVerified") if not optimize else None,
            "attentionRequired": verified_report.get("attentionRequired") if not optimize else None,
            "attentionReasonCode": verified_report.get("attentionReasonCode") if not optimize else None,
            "performanceEvaluationAvailable": verified_report.get("performanceEvaluationAvailable") if not optimize else None,
            "executionOutcome": verified_report.get("executionOutcome") if not optimize else None,
            "fullDynamicSixGroupVerified": False,
            "optimizationPassCount": verified_report.get("optimizationPassCount") if optimize else None,
            "optimizationReturnedPassCount": verified_report.get(
                "optimizationReturnedPassCount"
            ) if optimize else None,
            "optimizationRowsTruncated": verified_report.get(
                "optimizationRowsTruncated"
            ) if optimize else None,
            "optimizationResultRows": copy.deepcopy(
                verified_report.get("optimizationResultRows")
            ) if optimize else None,
            "optimizationSymbolUniverse": copy.deepcopy(
                verified_report.get("optimizationSymbolUniverse")
            ) if optimize else None,
            "optimizationSymbolUniverseDigest": verified_report.get(
                "optimizationSymbolUniverseDigest"
            ) if optimize else None,
            "inputManifestDigest": receipt.get("inputManifestDigest"),
            "optimizationSetRefDigest": receipt.get("optimizationSetRefDigest"),
            "optimizationExpectedReadbackEntriesDigest": receipt.get(
                "optimizationExpectedReadbackEntriesDigest"
            ),
            "baselinePresetRefDigest": receipt.get("baselinePresetRefDigest"),
            "baselineExpectedReadbackEntriesDigest": receipt.get(
                "baselineExpectedReadbackEntriesDigest"
            ),
            "baselineReadbackSetSha256": receipt.get("baselineReadbackSetSha256"),
            "baselineReadbackEntriesDigest": receipt.get(
                "baselineReadbackEntriesDigest"
            ),
            "optimizationCompletionCheckpointSha256": receipt.get(
                "optimizationCompletionCheckpointSha256"
            ),
            "optimizationCompletionCheckpointArtifactAlias": (
                "optimization_completion_checkpoint" if optimize else None
            ),
            "optimizationCacheLineage": copy.deepcopy(
                receipt.get("optimizationCacheLineage")
            ),
            "optimizationCacheLineageDigest": receipt.get(
                "optimizationCacheLineageDigest"
            ),
            "recoveredExistingReceipt": recovered,
            "recoveredWithoutStart": receipt.get("recoveredWithoutStart") is True,
            "startInvoked": receipt.get("startInvoked") is True,
            "executionObservedRunning": receipt.get("executionObservedRunning")
            is True,
            "completedResultCheckpointReused": receipt.get(
                "completedResultCheckpointReused"
            )
            is True,
            "completedReportCheckpointReused": receipt.get(
                "completedReportCheckpointReused"
            )
            is True,
            "testerCompletionObservation": receipt["testerCompletionObservation"],
            "testerCompletionEvidence": copy.deepcopy(
                receipt["testerCompletionEvidence"]
            ),
            "testerCompletionEvidenceDigest": receipt[
                "testerCompletionEvidenceDigest"
            ],
            "testerCompletionEvidenceCheckpointSha256": receipt[
                "testerCompletionEvidenceCheckpointSha256"
            ],
            "strategyExecutionProfile": copy.deepcopy(
                receipt.get("strategyExecutionProfile")
            ),
            "strategyExecutionProof": copy.deepcopy(
                receipt.get("strategyExecutionProof")
            ),
            "strategyExecutionProofDigest": receipt.get(
                "strategyExecutionProofDigest"
            ),
            "testerRunTransitionObserved": receipt.get(
                "testerRunTransitionObserved"
            )
            is True,
            "testerRunTransitionEvidence": receipt["testerRunTransitionEvidence"],
            "recoveryIssuedStart": False,
            "liveTradingExecuted": False,
            "autoTradingToggled": False,
            "autoTradingStateBefore": receipt["autoTradingStateBefore"],
            "autoTradingStateAfter": receipt["autoTradingStateAfter"],
            "chartAttached": False,
            "terminalClosedByAdapter": False,
            "terminalStillRunning": True,
            "terminalStillOpen": True,
            "adapterReceiptArtifactAlias": "adapter_receipt",
        }
        artifacts = [
            _artifact("tester_settings", settings_screenshot, workspace, artifact_kind="screenshot_evidence"),
            _artifact("tester_result", result_screenshot, workspace, artifact_kind="screenshot_evidence"),
            _artifact("tester_report_proof", report_screenshot, workspace, artifact_kind="screenshot_evidence"),
            _artifact(
                "optimization_report" if optimize else "tester_report",
                report,
                workspace,
                artifact_kind="optimization_evidence" if optimize else "backtest_evidence",
            ),
            _artifact(
                "adapter_receipt",
                receipt_path,
                workspace,
                artifact_kind="optimization_evidence" if optimize else "backtest_evidence",
            ),
        ]
        if optimize:
            artifacts.insert(
                1,
                _artifact(
                    "optimization_completion_checkpoint",
                    completion_checkpoint_path,
                    workspace,
                    artifact_kind="optimization_evidence",
                ),
            )
        if readback_set is not None:
            artifacts.insert(
                1,
                _artifact(
                    "optimization_input_readback",
                    readback_set,
                    workspace,
                    artifact_kind="set_file",
                ),
            )
        if baseline_readback_set is not None:
            artifacts.insert(
                1,
                _artifact(
                    "baseline_input_readback",
                    baseline_readback_set,
                    workspace,
                    artifact_kind="set_file",
                ),
            )
        if not optimize:
            if (
                preset_screenshot is None
                or input_preset_set is None
                or input_readback_set is None
            ):
                raise VisibleTerminalAdapterError("tester_input_preset_evidence_missing")
            artifacts[1:1] = [
                _artifact(
                    "tester_input_preset",
                    preset_screenshot,
                    workspace,
                    artifact_kind="screenshot_evidence",
                ),
                _artifact(
                    "tester_input_preset_set",
                    input_preset_set,
                    workspace,
                    artifact_kind="set_file",
                ),
                _artifact(
                    "tester_input_readback_set",
                    input_readback_set,
                    workspace,
                    artifact_kind="set_file",
                ),
            ]
        return {
            "schemaVersion": RESULT_SCHEMA,
            "operationId": context["operation"]["operationId"],
            "metrics": metrics,
            "artifactSpecifications": artifacts,
        }


def create_production_visible_front_office_adapter_mt5(
    *,
    target_resolver: Callable[..., dict],
    powershell_runner: Callable[..., dict] | None = None,
    compile_verifier: Callable[[dict], dict] | None = verify_visible_metaeditor_compile_mt5,
    backtest_verifier: Callable[[dict], dict] | None = verify_mt5_tester_report,
    optimization_verifier: Callable[[dict], dict] | None = verify_mt5_optimization_report,
) -> VisibleFrontOfficeAdapterMt5:
    """Create the production MT5 adapter for future bridge integration.

    ``powershell_runner`` and verifier parameters exist only for deterministic
    tests.  Production callers normally pass only the backend-owned
    ``target_resolver``.
    """

    return VisibleFrontOfficeAdapterMt5(
        target_resolver=target_resolver,
        powershell_runner=powershell_runner,
        compile_verifier=compile_verifier,
        backtest_verifier=backtest_verifier,
        optimization_verifier=optimization_verifier,
    )


__all__ = [
    "REQUIRED_TESTER_AUTOMATION_IDS",
    "VisibleFrontOfficeAdapterMt5",
    "VisibleTerminalAdapterError",
    "create_production_visible_front_office_adapter_mt5",
    "verify_mt5_optimization_report",
    "verify_mt5_tester_report",
    "verify_mt5_tester_report_payload",
    "verify_visible_metaeditor_compile_mt5",
]
