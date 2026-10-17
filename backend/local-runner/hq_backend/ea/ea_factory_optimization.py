"""Durable, fail-closed EA Factory optimization session orchestration.

The service in this module deliberately does not know how to click MetaTrader.
It owns the safety-critical state around a visible front-office adapter:

* one active optimization session at a time;
* exact binding to a selected MT4/MT5 terminal revision and digest;
* an immutable start intent committed before an adapter may press Start;
* receipt-only recovery after that boundary, so Start is never replayed;
* bounded numeric/categorical optimization ranges and result payloads; and
* immutable report/manifest evidence before a session can complete.

All filesystem locations are backend-owned.  Frontend requests and adapter
messages contain opaque references only; paths, credentials and live-trading
controls are rejected.  The adapter is also explicitly told that it may not
trade live, close the terminal, or press Start during recovery/collection.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import math
import os
import re
import secrets
import stat
import threading
import time
import unicodedata
import uuid
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
ANALYSIS_POLICY_VERSION = 2
EXECUTION_IDENTITY_SCHEMA = "optimization-execution-identity-v1"
STORE_FILENAME = "ea-factory-optimization-v1.json"
LOCK_FILENAME = ".ea-factory-optimization.lock"
WORKSPACES_DIRECTORY = "optimization-workspaces"

SESSION_STATES = frozenset(
    {
        "queued",
        "running",
        "awaiting_visible_terminal",
        "collecting",
        "completed",
        "failed",
        "cancelled",
    }
)
ACTIVE_STATES = frozenset(
    {"queued", "running", "awaiting_visible_terminal", "collecting"}
)
TERMINAL_STATES = frozenset({"completed", "failed", "cancelled"})
STAGES = (
    "validate_baseline",
    "prepare_ranges",
    "run_round",
    "verify_report",
    "analyze",
    "complete",
)

MAX_SESSIONS = 128
MAX_ROUNDS = 8
MAX_INPUTS_PER_ROUND = 64
MAX_CATEGORICAL_VALUES = 64
MAX_COMBINATIONS_PER_ROUND = 100_000
MAX_TOTAL_COMBINATIONS = 250_000
MAX_RESULT_ROWS = 5_000
# Public result rows are sourced only from the hash-verified immutable result
# document.  Keep the explicit cap even though it currently matches the
# adapter cap so a future adapter expansion cannot silently make read models
# unbounded.
MAX_PUBLIC_RESULT_ROWS = MAX_RESULT_ROWS
MAX_RESULT_ROW_FIELDS = 32
MAX_WARNINGS = 128
MAX_ANALYSIS_CANDIDATES_PER_GROUP = 3
MAX_EVENTS = 192
MAX_START_ATTEMPTS = 3
MAX_REQUEST_BYTES = 256 * 1024
MAX_HANDLER_RESULT_BYTES = 2 * 1024 * 1024
MAX_STORE_BYTES = 8 * 1024 * 1024
MAX_DOCUMENT_BYTES = 3 * 1024 * 1024
DEFAULT_HEARTBEAT_TIMEOUT_SECONDS = 300.0
DEFAULT_SESSION_DEADLINE_SECONDS = 4 * 60 * 60.0
MIN_SESSION_DEADLINE_SECONDS = 60.0
MAX_SESSION_DEADLINE_SECONDS = 24 * 60 * 60.0

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_INPUT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]{0,79}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._#-]{0,31}$")
_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{7,191}$")
_OPAQUE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{7,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BIDI_RE = re.compile(r"[\u202a-\u202e\u2066-\u2069]")
_WINDOWS_PATH_RE = re.compile(r"(?i)(?:^[a-z]:[\\/]|^\\\\|^//|[\\/]{2,})")
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?<![A-Za-z0-9])\d{6,12}:[A-Za-z0-9_-]{30,100}(?![A-Za-z0-9_-])"),
)
_FORBIDDEN_KEY_PARTS = (
    "path",
    "directory",
    "folder",
    "secret",
    "password",
    "credential",
    "authorization",
    "cookie",
    "privatekey",
    "accesstoken",
    "refreshtoken",
)
_PERIODS = frozenset(
    {
        "M1",
        "M2",
        "M3",
        "M4",
        "M5",
        "M6",
        "M10",
        "M12",
        "M15",
        "M20",
        "M30",
        "H1",
        "H2",
        "H3",
        "H4",
        "H6",
        "H8",
        "H12",
        "D1",
        "W1",
        "MN1",
    }
)
_TEST_MODELS = frozenset(
    {
        "every_tick_based_on_real_ticks",
        "every_tick",
        "one_minute_ohlc",
        "control_points",
        "open_prices_only",
        "math_calculations",
    }
)
_OPTIMIZATION_MODES = frozenset(
    {"slow_complete", "fast_genetic", "all_symbols_market_watch"}
)
_OPTIMIZATION_CRITERIA = frozenset(
    {
        "balance_max",
        "profit_factor_max",
        "expected_payoff_max",
        "drawdown_min",
        "recovery_factor_max",
        "sharpe_ratio_max",
        "custom_max",
    }
)


class OptimizationDomainError(RuntimeError):
    """Stable, frontend-safe domain failure."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int = 400,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = dict(details or {})

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": False,
            "error": {"code": self.code, "message": str(self)},
        }
        if self.details:
            result["error"]["details"] = copy.deepcopy(self.details)
        return result


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _iso_timestamp(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def _safe_text(
    value: Any,
    *,
    field: str,
    maximum: int,
    allow_empty: bool = False,
    reject_path: bool = True,
) -> str:
    if not isinstance(value, str):
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be text.", status=422
        )
    normalized = unicodedata.normalize("NFC", value).strip()
    normalized = _BIDI_RE.sub("", _CONTROL_RE.sub("", normalized))
    if not normalized and not allow_empty:
        raise OptimizationDomainError(
            "invalid_request", f"{field} is required.", status=422
        )
    if len(normalized) > maximum:
        raise OptimizationDomainError(
            "request_too_large", f"{field} exceeds the allowed size.", status=413
        )
    if reject_path and (
        _WINDOWS_PATH_RE.search(normalized)
        or normalized.startswith(("/", "~", "file:", "http:", "https:"))
    ):
        raise OptimizationDomainError(
            "path_not_allowed",
            f"{field} must be an opaque value, not a path or URL.",
            status=422,
        )
    for pattern in _SECRET_PATTERNS:
        if pattern.search(normalized):
            raise OptimizationDomainError(
                "secret_not_allowed",
                f"{field} contains credential-like material.",
                status=422,
            )
    return normalized


def _identifier(value: Any, *, field: str, pattern: re.Pattern[str] = _IDENTIFIER_RE) -> str:
    text = _safe_text(value, field=field, maximum=192)
    if pattern.fullmatch(text) is None:
        raise OptimizationDomainError(
            "invalid_request", f"{field} is invalid.", status=422
        )
    return text


def _opaque_ref(value: Any, *, field: str) -> str:
    return _identifier(value, field=field, pattern=_OPAQUE_REF_RE)


def _sha256(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be a lowercase SHA-256 digest.", status=422
        )
    return value


def _positive_int(value: Any, *, field: str, minimum: int = 1, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be an integer.", status=422
        )
    if value < minimum or value > maximum:
        raise OptimizationDomainError(
            "invalid_request",
            f"{field} must be between {minimum} and {maximum}.",
            status=422,
        )
    return value


def _exact_keys(
    value: Any,
    *,
    field: str,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be an object.", status=422
        )
    optional = optional or set()
    keys = set(value)
    missing = sorted(required - keys)
    unexpected = sorted(keys - required - optional)
    if missing or unexpected:
        raise OptimizationDomainError(
            "invalid_request",
            f"{field} has an invalid schema.",
            status=422,
            details={"missing": missing, "unexpected": unexpected},
        )
    return value


def _reject_forbidden_keys(value: Any, *, field: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            folded = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if any(part in folded for part in _FORBIDDEN_KEY_PARTS):
                raise OptimizationDomainError(
                    "unsafe_field",
                    f"{field} contains a path or secret field.",
                    status=422,
                )
            _reject_forbidden_keys(child, field=field)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_keys(child, field=field)
    elif isinstance(value, str):
        # This recursive pass is a safety scan, not the field's semantic
        # validator.  Native MT5 reports legitimately encode undefined metrics
        # (for example Profit Factor on a zero-trade pass) as an empty cell.
        # Required identifiers/digests are still rejected later by their exact
        # schema validators, while an empty report metric can reach the
        # result-row validator without being mistaken for a malformed request.
        _safe_text(value, field=field, maximum=2048, allow_empty=True)


def _decimal_string(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be numeric.", status=422
        )
    if isinstance(value, str):
        value = _safe_text(value, field=field, maximum=64)
    if isinstance(value, float) and not math.isfinite(value):
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be finite.", status=422
        )
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be numeric.", status=422
        ) from error
    if not number.is_finite():
        raise OptimizationDomainError(
            "invalid_request", f"{field} must be finite.", status=422
        )
    digits = number.as_tuple().digits
    exponent = number.as_tuple().exponent
    if len(digits) > 32 or number.adjusted() > 18 or exponent < -18:
        raise OptimizationDomainError(
            "invalid_request", f"{field} is outside the supported range.", status=422
        )
    normalized = format(number.normalize(), "f")
    if normalized == "-0":
        normalized = "0"
    if len(normalized) > 64:
        raise OptimizationDomainError(
            "invalid_request", f"{field} is outside the supported range.", status=422
        )
    return normalized


def _normalize_scalar(value: Any, *, field: str) -> str | int | bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) > 2**53:
            raise OptimizationDomainError(
                "invalid_request", f"{field} integer is too large.", status=422
            )
        return value
    if isinstance(value, str):
        return _safe_text(value, field=field, maximum=128)
    raise OptimizationDomainError(
        "invalid_request",
        f"{field} must be a string, integer, or boolean.",
        status=422,
    )


def _normalize_range(value: Any, *, round_index: int, input_index: int) -> dict[str, Any]:
    field = f"rounds[{round_index}].ranges[{input_index}]"
    row = _exact_keys(
        value,
        field=field,
        required={"name", "kind"},
        optional={"start", "step", "stop", "values"},
    )
    name = _identifier(row["name"], field=f"{field}.name", pattern=_INPUT_NAME_RE)
    kind = _safe_text(row["kind"], field=f"{field}.kind", maximum=32).casefold()
    if kind not in {"numeric", "categorical"}:
        raise OptimizationDomainError(
            "invalid_request", f"{field}.kind is unsupported.", status=422
        )
    if name.casefold().endswith("mode") and kind != "categorical":
        raise OptimizationDomainError(
            "mode_range_must_be_categorical",
            f"{name} must use a categorical range.",
            status=422,
        )
    if kind == "numeric":
        if set(row) != {"name", "kind", "start", "step", "stop"}:
            raise OptimizationDomainError(
                "invalid_request",
                f"{field} numeric range requires exactly start, step and stop.",
                status=422,
            )
        start = Decimal(_decimal_string(row["start"], field=f"{field}.start"))
        step = Decimal(_decimal_string(row["step"], field=f"{field}.step"))
        stop = Decimal(_decimal_string(row["stop"], field=f"{field}.stop"))
        if step <= 0 or stop < start:
            raise OptimizationDomainError(
                "invalid_range",
                f"{field} requires step > 0 and stop >= start.",
                status=422,
            )
        count_decimal = ((stop - start) / step).to_integral_value(rounding=ROUND_FLOOR) + 1
        count = int(count_decimal)
        if count < 1 or count > MAX_COMBINATIONS_PER_ROUND:
            raise OptimizationDomainError(
                "range_too_large", f"{field} produces too many values.", status=422
            )
        return {
            "name": name,
            "kind": "numeric",
            "start": _decimal_string(start, field=f"{field}.start"),
            "step": _decimal_string(step, field=f"{field}.step"),
            "stop": _decimal_string(stop, field=f"{field}.stop"),
            "valueCount": count,
        }

    if set(row) != {"name", "kind", "values"}:
        raise OptimizationDomainError(
            "invalid_request",
            f"{field} categorical range requires exactly values.",
            status=422,
        )
    values = row["values"]
    if not isinstance(values, list) or not values or len(values) > MAX_CATEGORICAL_VALUES:
        raise OptimizationDomainError(
            "invalid_range",
            f"{field}.values must contain 1-{MAX_CATEGORICAL_VALUES} values.",
            status=422,
        )
    normalized_values: list[str | int | bool] = []
    seen: set[bytes] = set()
    for value_index, item in enumerate(values):
        normalized = _normalize_scalar(item, field=f"{field}.values[{value_index}]")
        encoded = _canonical_bytes(normalized)
        if encoded in seen:
            raise OptimizationDomainError(
                "duplicate_range_value",
                f"{field}.values contains a duplicate.",
                status=422,
            )
        seen.add(encoded)
        normalized_values.append(normalized)
    return {
        "name": name,
        "kind": "categorical",
        "values": normalized_values,
        "valueCount": len(normalized_values),
    }


def _normalize_rounds(value: Any) -> tuple[list[dict[str, Any]], int]:
    if not isinstance(value, list) or not value or len(value) > MAX_ROUNDS:
        raise OptimizationDomainError(
            "invalid_request",
            f"rounds must contain 1-{MAX_ROUNDS} rounds.",
            status=422,
        )
    rounds: list[dict[str, Any]] = []
    total_combinations = 0
    for round_index, raw_round in enumerate(value):
        row = _exact_keys(
            raw_round,
            field=f"rounds[{round_index}]",
            required={"ranges"},
            optional={"label"},
        )
        ranges = row["ranges"]
        if (
            not isinstance(ranges, list)
            or not ranges
            or len(ranges) > MAX_INPUTS_PER_ROUND
        ):
            raise OptimizationDomainError(
                "invalid_request",
                f"rounds[{round_index}].ranges must contain 1-{MAX_INPUTS_PER_ROUND} inputs.",
                status=422,
            )
        normalized_ranges = [
            _normalize_range(item, round_index=round_index, input_index=input_index)
            for input_index, item in enumerate(ranges)
        ]
        names = [item["name"].casefold() for item in normalized_ranges]
        if len(names) != len(set(names)):
            raise OptimizationDomainError(
                "duplicate_input_name",
                f"rounds[{round_index}] contains duplicate input names.",
                status=422,
            )
        combinations = 1
        for item in normalized_ranges:
            combinations *= item["valueCount"]
            if combinations > MAX_COMBINATIONS_PER_ROUND:
                raise OptimizationDomainError(
                    "round_combination_limit",
                    f"rounds[{round_index}] exceeds the combination limit.",
                    status=422,
                )
        if combinations < 2:
            raise OptimizationDomainError(
                "optimization_requires_multiple_combinations",
                f"rounds[{round_index}] must plan at least two parameter combinations.",
                status=422,
            )
        total_combinations += combinations
        if total_combinations > MAX_TOTAL_COMBINATIONS:
            raise OptimizationDomainError(
                "total_combination_limit",
                "The optimization request exceeds the total combination limit.",
                status=422,
            )
        label = (
            _safe_text(row["label"], field=f"rounds[{round_index}].label", maximum=80)
            if "label" in row
            else f"Round {round_index + 1}"
        )
        rounds.append(
            {
                "roundId": f"round-{round_index + 1:02d}",
                "label": label,
                "ranges": normalized_ranges,
                "combinationCount": combinations,
            }
        )
    return rounds, total_combinations


def _iso_date(value: Any, *, field: str) -> str:
    text = _safe_text(value, field=field, maximum=10)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d")
    except ValueError as error:
        raise OptimizationDomainError(
            "invalid_tester_settings",
            f"{field} must use YYYY-MM-DD.",
            status=422,
        ) from error
    if parsed.strftime("%Y-%m-%d") != text:
        raise OptimizationDomainError(
            "invalid_tester_settings",
            f"{field} must use YYYY-MM-DD.",
            status=422,
        )
    return text


def _normalize_tester_settings(value: Any) -> dict[str, Any]:
    row = _exact_keys(
        value,
        field="testerSettings",
        required={
            "symbol",
            "period",
            "model",
            "useDate",
            "fromDate",
            "toDate",
            "optimizationMode",
            "criterion",
        },
    )
    symbol = _identifier(row["symbol"], field="testerSettings.symbol", pattern=_SYMBOL_RE)
    period = _safe_text(row["period"], field="testerSettings.period", maximum=4).upper()
    model = _safe_text(row["model"], field="testerSettings.model", maximum=48).casefold()
    optimization_mode = _safe_text(
        row["optimizationMode"], field="testerSettings.optimizationMode", maximum=48
    ).casefold()
    criterion = _safe_text(
        row["criterion"], field="testerSettings.criterion", maximum=48
    ).casefold()
    if period not in _PERIODS:
        raise OptimizationDomainError(
            "invalid_tester_settings", "testerSettings.period is unsupported.", status=422
        )
    if model not in _TEST_MODELS:
        raise OptimizationDomainError(
            "invalid_tester_settings", "testerSettings.model is unsupported.", status=422
        )
    if optimization_mode not in _OPTIMIZATION_MODES:
        raise OptimizationDomainError(
            "invalid_tester_settings",
            "testerSettings.optimizationMode is unsupported.",
            status=422,
        )
    if criterion not in _OPTIMIZATION_CRITERIA:
        raise OptimizationDomainError(
            "invalid_tester_settings",
            "testerSettings.criterion is unsupported.",
            status=422,
        )
    if not isinstance(row["useDate"], bool):
        raise OptimizationDomainError(
            "invalid_tester_settings", "testerSettings.useDate must be boolean.", status=422
        )
    use_date = row["useDate"]
    if use_date:
        if row["fromDate"] is None or row["toDate"] is None:
            raise OptimizationDomainError(
                "invalid_tester_settings",
                "Date-bounded testing requires fromDate and toDate.",
                status=422,
            )
        from_date = _iso_date(row["fromDate"], field="testerSettings.fromDate")
        to_date = _iso_date(row["toDate"], field="testerSettings.toDate")
        if from_date > to_date:
            raise OptimizationDomainError(
                "invalid_tester_settings",
                "testerSettings.fromDate must not be after toDate.",
                status=422,
            )
    else:
        if row["fromDate"] is not None or row["toDate"] is not None:
            raise OptimizationDomainError(
                "invalid_tester_settings",
                "fromDate and toDate must be null when useDate is false.",
                status=422,
            )
        from_date = None
        to_date = None
    return {
        "symbol": symbol,
        "period": period,
        "model": model,
        "useDate": use_date,
        "fromDate": from_date,
        "toDate": to_date,
        "optimizationMode": optimization_mode,
        "criterion": criterion,
    }


def _normalize_risk_thresholds(value: Any) -> dict[str, Any]:
    """Normalize the optional, analysis-only risk objectives.

    These values never authorize trading or alter managed filesystem inputs.
    Keeping an exact numeric-only schema lets the bridge preserve the user's
    analysis intent without creating another generic payload channel.
    """

    row = _exact_keys(
        value,
        field="riskThresholds",
        required={"targetProfitPercent", "maxDrawdownPercent", "minimumTrades"},
    )

    def optional_number(
        raw: Any, *, field: str, minimum: float, maximum: float
    ) -> float | None:
        if raw is None:
            return None
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise OptimizationDomainError(
                "invalid_request", f"{field} must be a finite number or null.", status=422
            )
        number = float(raw)
        if not math.isfinite(number) or not minimum <= number <= maximum:
            raise OptimizationDomainError(
                "invalid_request",
                f"{field} is outside the supported range.",
                status=422,
            )
        return number

    minimum_trades = row["minimumTrades"]
    if minimum_trades is not None:
        minimum_trades = _positive_int(
            minimum_trades,
            field="riskThresholds.minimumTrades",
            maximum=MAX_TOTAL_COMBINATIONS,
        )
    return {
        "targetProfitPercent": optional_number(
            row["targetProfitPercent"],
            field="riskThresholds.targetProfitPercent",
            minimum=0.0,
            maximum=1_000_000.0,
        ),
        "maxDrawdownPercent": optional_number(
            row["maxDrawdownPercent"],
            field="riskThresholds.maxDrawdownPercent",
            minimum=0.0,
            maximum=100.0,
        ),
        "minimumTrades": minimum_trades,
    }


def _normalize_request(value: Any) -> tuple[dict[str, Any], str]:
    if not isinstance(value, dict):
        raise OptimizationDomainError(
            "invalid_request", "Optimization request must be an object.", status=422
        )
    try:
        encoded = _canonical_bytes(value)
    except (TypeError, ValueError) as error:
        raise OptimizationDomainError(
            "invalid_request", "Optimization request is not valid JSON data.", status=422
        ) from error
    if len(encoded) > MAX_REQUEST_BYTES:
        raise OptimizationDomainError(
            "request_too_large", "Optimization request is too large.", status=413
        )
    forbidden_live_fields = {
        "liveTrading",
        "allowLiveTrading",
        "tradeMode",
        "closeTerminal",
        "testShutdownTerminal",
    }
    if forbidden_live_fields.intersection(value):
        raise OptimizationDomainError(
            "live_trading_forbidden",
            "Optimization sessions cannot enable trading or close MetaTrader.",
            status=422,
        )
    row = _exact_keys(
        value,
        field="request",
        required={
            "idempotencyKey",
            "buildId",
            "sourceDigest",
            "baselineReportSha256",
            "platform",
            "terminalCandidateId",
            "terminalSelectionRevision",
            "terminalBindingDigest",
            "testerSettings",
            "rounds",
        },
        optional={"riskThresholds"},
    )
    idempotency_key = _identifier(
        row["idempotencyKey"], field="idempotencyKey", pattern=_IDEMPOTENCY_RE
    )
    build_id = _identifier(row["buildId"], field="buildId")
    source_digest = _sha256(row["sourceDigest"], field="sourceDigest")
    baseline_digest = _sha256(
        row["baselineReportSha256"], field="baselineReportSha256"
    )
    platform = _safe_text(row["platform"], field="platform", maximum=8).casefold()
    if platform not in {"mt4", "mt5"}:
        raise OptimizationDomainError(
            "unsupported_platform", "platform must be mt4 or mt5.", status=422
        )
    candidate_id = _identifier(row["terminalCandidateId"], field="terminalCandidateId")
    revision = _positive_int(
        row["terminalSelectionRevision"],
        field="terminalSelectionRevision",
        maximum=2**31 - 1,
    )
    binding_digest = _sha256(
        row["terminalBindingDigest"], field="terminalBindingDigest"
    )
    rounds, total_combinations = _normalize_rounds(row["rounds"])
    tester_settings = _normalize_tester_settings(row["testerSettings"])
    normalized = {
        "buildId": build_id,
        "sourceDigest": source_digest,
        "baselineReportSha256": baseline_digest,
        "platform": platform,
        "terminalCandidateId": candidate_id,
        "terminalSelectionRevision": revision,
        "terminalBindingDigest": binding_digest,
        "testerSettings": tester_settings,
        "rounds": rounds,
        "totalCombinationCount": total_combinations,
    }
    if "riskThresholds" in row:
        normalized["riskThresholds"] = _normalize_risk_thresholds(
            row["riskThresholds"]
        )
    return normalized, idempotency_key


def _validate_normalized_request_record(value: Any) -> dict[str, Any]:
    """Validate the exact backend-owned request representation loaded from disk."""

    row = _exact_keys(
        value,
        field="storedRequest",
        required={
            "buildId",
            "sourceDigest",
            "baselineReportSha256",
            "platform",
            "terminalCandidateId",
            "terminalSelectionRevision",
            "terminalBindingDigest",
            "testerSettings",
            "rounds",
            "totalCombinationCount",
        },
        optional={"riskThresholds"},
    )
    _identifier(row["buildId"], field="storedRequest.buildId")
    _sha256(row["sourceDigest"], field="storedRequest.sourceDigest")
    _sha256(
        row["baselineReportSha256"], field="storedRequest.baselineReportSha256"
    )
    platform = _safe_text(
        row["platform"], field="storedRequest.platform", maximum=8
    ).casefold()
    if platform not in {"mt4", "mt5"} or platform != row["platform"]:
        raise OptimizationDomainError(
            "invalid_request", "Stored platform is invalid.", status=422
        )
    _identifier(
        row["terminalCandidateId"], field="storedRequest.terminalCandidateId"
    )
    _positive_int(
        row["terminalSelectionRevision"],
        field="storedRequest.terminalSelectionRevision",
        maximum=2**31 - 1,
    )
    _sha256(
        row["terminalBindingDigest"], field="storedRequest.terminalBindingDigest"
    )
    if _normalize_tester_settings(row["testerSettings"]) != row["testerSettings"]:
        raise OptimizationDomainError(
            "invalid_request", "Stored tester settings are not canonical.", status=422
        )
    if "riskThresholds" in row and (
        _normalize_risk_thresholds(row["riskThresholds"])
        != row["riskThresholds"]
    ):
        raise OptimizationDomainError(
            "invalid_request", "Stored risk thresholds are not canonical.", status=422
        )
    rounds = row["rounds"]
    if not isinstance(rounds, list) or not 1 <= len(rounds) <= MAX_ROUNDS:
        raise OptimizationDomainError(
            "invalid_request", "Stored optimization rounds are invalid.", status=422
        )
    total = 0
    for round_index, raw_round in enumerate(rounds):
        round_row = _exact_keys(
            raw_round,
            field=f"storedRequest.rounds[{round_index}]",
            required={"roundId", "label", "ranges", "combinationCount"},
        )
        if round_row["roundId"] != f"round-{round_index + 1:02d}":
            raise OptimizationDomainError(
                "invalid_request", "Stored round identity is invalid.", status=422
            )
        _safe_text(
            round_row["label"],
            field=f"storedRequest.rounds[{round_index}].label",
            maximum=80,
        )
        ranges = round_row["ranges"]
        if not isinstance(ranges, list) or not 1 <= len(ranges) <= MAX_INPUTS_PER_ROUND:
            raise OptimizationDomainError(
                "invalid_request", "Stored ranges are invalid.", status=422
            )
        names: set[str] = set()
        combinations = 1
        for input_index, stored_range in enumerate(ranges):
            if not isinstance(stored_range, dict):
                raise OptimizationDomainError(
                    "invalid_request", "Stored range is invalid.", status=422
                )
            kind = stored_range.get("kind")
            raw_range = {
                key: copy.deepcopy(value)
                for key, value in stored_range.items()
                if key != "valueCount"
            }
            normalized_range = _normalize_range(
                raw_range, round_index=round_index, input_index=input_index
            )
            if normalized_range != stored_range or kind not in {
                "numeric",
                "categorical",
            }:
                raise OptimizationDomainError(
                    "invalid_request", "Stored range is not canonical.", status=422
                )
            folded_name = normalized_range["name"].casefold()
            if folded_name in names:
                raise OptimizationDomainError(
                    "invalid_request", "Stored ranges contain duplicate inputs.", status=422
                )
            names.add(folded_name)
            combinations *= normalized_range["valueCount"]
        if (
            isinstance(round_row["combinationCount"], bool)
            or not isinstance(round_row["combinationCount"], int)
            or round_row["combinationCount"] != combinations
            or combinations < 2
            or combinations > MAX_COMBINATIONS_PER_ROUND
        ):
            raise OptimizationDomainError(
                "invalid_request", "Stored combination count is invalid.", status=422
            )
        total += combinations
    if (
        isinstance(row["totalCombinationCount"], bool)
        or not isinstance(row["totalCombinationCount"], int)
        or row["totalCombinationCount"] != total
        or total > MAX_TOTAL_COMBINATIONS
    ):
        raise OptimizationDomainError(
            "invalid_request", "Stored total combination count is invalid.", status=422
        )
    return row


def _unsafe_path(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse)


class _InterprocessFileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: Any = None

    def __enter__(self) -> "_InterprocessFileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if _unsafe_path(self.path.parent) or _unsafe_path(self.path):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization lock path is unsafe.", status=409
            )
        self.handle = self.path.open("a+b")
        self.handle.seek(0)
        if self.handle.read(1) == b"":
            self.handle.write(b"0")
            self.handle.flush()
        self.handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self.handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        if self.handle is None:
            return
        self.handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()
        self.handle = None


class EaFactoryOptimizationService:
    """Own durable optimization state while an injected adapter owns the UI."""

    def __init__(
        self,
        storage_root: str | os.PathLike[str],
        *,
        target_resolver: Callable[[dict[str, Any]], Mapping[str, Any]],
        capability_provider: Callable[[dict[str, Any]], Mapping[str, Any]],
        optimization_handler: Callable[[dict[str, Any]], Mapping[str, Any]],
        execution_stop_prover: Callable[[dict[str, Any]], Mapping[str, Any]]
        | None = None,
        audit_callback: Callable[[dict[str, Any]], None] | None = None,
        clock: Callable[[], float] | None = None,
        heartbeat_timeout_seconds: float = DEFAULT_HEARTBEAT_TIMEOUT_SECONDS,
        session_deadline_seconds: float = DEFAULT_SESSION_DEADLINE_SECONDS,
    ) -> None:
        if not callable(target_resolver) or not callable(capability_provider):
            raise TypeError("target_resolver and capability_provider must be callable")
        if not callable(optimization_handler):
            raise TypeError("optimization_handler must be callable")
        if execution_stop_prover is not None and not callable(execution_stop_prover):
            raise TypeError("execution_stop_prover must be callable")
        if audit_callback is not None and not callable(audit_callback):
            raise TypeError("audit_callback must be callable")
        self._root = Path(storage_root).expanduser().resolve()
        self._store_path = self._root / STORE_FILENAME
        self._lock_path = self._root / LOCK_FILENAME
        self._workspaces_root = self._root / WORKSPACES_DIRECTORY
        self._target_resolver = target_resolver
        self._capability_provider = capability_provider
        self._handler = optimization_handler
        self._execution_stop_prover = execution_stop_prover
        self._audit_callback = audit_callback or (lambda _event: None)
        self._clock = clock or time.time
        self._heartbeat_timeout = float(heartbeat_timeout_seconds)
        self._deadline_seconds = float(session_deadline_seconds)
        if not math.isfinite(self._heartbeat_timeout) or self._heartbeat_timeout <= 0:
            raise ValueError("heartbeat_timeout_seconds must be positive")
        if (
            not math.isfinite(self._deadline_seconds)
            or self._deadline_seconds < MIN_SESSION_DEADLINE_SECONDS
            or self._deadline_seconds > MAX_SESSION_DEADLINE_SECONDS
        ):
            raise ValueError("session_deadline_seconds is outside the safe range")
        self._thread_lock = threading.RLock()
        self._initialize_storage()

    @contextmanager
    def _locked(self):
        with self._thread_lock:
            with _InterprocessFileLock(self._lock_path):
                yield

    def _now(self) -> float:
        value = float(self._clock())
        if not math.isfinite(value) or value < 0:
            raise OptimizationDomainError(
                "clock_invalid", "Optimization clock returned an invalid value.", status=500
            )
        return value

    def _initialize_storage(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        if _unsafe_path(self._root):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization storage root is unsafe.", status=409
            )
        self._workspaces_root.mkdir(exist_ok=True)
        if _unsafe_path(self._workspaces_root):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization workspace root is unsafe.", status=409
            )
        with self._locked():
            if not self._store_path.exists():
                self._write_store_unlocked(
                    {"schemaVersion": SCHEMA_VERSION, "revision": 0, "sessions": []}
                )
            else:
                self._load_store_unlocked()

    @staticmethod
    def _store_integrity(store: Mapping[str, Any]) -> str:
        unsigned = {key: value for key, value in store.items() if key != "integritySha256"}
        return _sha256_json(unsigned)

    def _write_store_unlocked(self, store: dict[str, Any]) -> None:
        payload = copy.deepcopy(store)
        payload["integritySha256"] = self._store_integrity(payload)
        encoded = _canonical_bytes(payload) + b"\n"
        if len(encoded) > MAX_STORE_BYTES:
            raise OptimizationDomainError(
                "store_too_large", "Optimization state exceeds its size limit.", status=409
            )
        if _unsafe_path(self._root) or _unsafe_path(self._store_path):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization state path is unsafe.", status=409
            )
        temporary = self._root / f".{STORE_FILENAME}.{secrets.token_hex(8)}.tmp"
        descriptor: int | None = None
        try:
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(temporary, flags, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            if _unsafe_path(temporary):
                raise OptimizationDomainError(
                    "unsafe_storage_path", "Temporary optimization state is unsafe.", status=409
                )
            os.replace(temporary, self._store_path)
            with contextlib.suppress(OSError):
                os.chmod(self._store_path, 0o600)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            with contextlib.suppress(FileNotFoundError):
                temporary.unlink()

    def _load_store_unlocked(self) -> dict[str, Any]:
        if _unsafe_path(self._store_path):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization state path is unsafe.", status=409
            )
        try:
            raw = self._store_path.read_bytes()
        except FileNotFoundError as error:
            raise OptimizationDomainError(
                "store_missing", "Optimization state is missing.", status=500
            ) from error
        if len(raw) > MAX_STORE_BYTES:
            raise OptimizationDomainError(
                "store_too_large", "Optimization state exceeds its size limit.", status=500
            )
        try:
            store = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization state is not valid JSON.", status=500
            ) from error
        if not isinstance(store, dict) or set(store) != {
            "schemaVersion",
            "revision",
            "sessions",
            "integritySha256",
        }:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization state schema is invalid.", status=500
            )
        if store.get("schemaVersion") != SCHEMA_VERSION:
            raise OptimizationDomainError(
                "store_version_unsupported", "Optimization state version is unsupported.", status=500
            )
        if store.get("integritySha256") != self._store_integrity(store):
            raise OptimizationDomainError(
                "store_tampered", "Optimization state integrity check failed.", status=500
            )
        if (
            isinstance(store.get("revision"), bool)
            or not isinstance(store.get("revision"), int)
            or store["revision"] < 0
            or not isinstance(store.get("sessions"), list)
            or len(store["sessions"]) > MAX_SESSIONS
        ):
            raise OptimizationDomainError(
                "store_corrupt", "Optimization state metadata is invalid.", status=500
            )
        ids: set[str] = set()
        active = 0
        for session in store["sessions"]:
            self._validate_session_record(session)
            if session["id"] in ids:
                raise OptimizationDomainError(
                    "store_corrupt", "Optimization state contains duplicate sessions.", status=500
                )
            ids.add(session["id"])
            if session["state"] in ACTIVE_STATES:
                active += 1
            self._validate_workspace_documents(session)
        if active > 1:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization state contains multiple active sessions.", status=500
            )
        return store

    def _validate_session_record(self, session: Any) -> None:
        required = {
            "schemaVersion",
            "id",
            "requestDigest",
            "idempotencyKeyDigest",
            "request",
            "buildId",
            "sourceDigest",
            "baselineReportSha256",
            "platform",
            "terminalBinding",
            "workspaceRef",
            "state",
            "stage",
            "roundIndex",
            "roundCount",
            "attemptsByRound",
            "progress",
            "currentOperation",
            "roundResults",
            "cancelRequested",
            "cancelReason",
            "failure",
            "createdAt",
            "updatedAt",
            "heartbeatAt",
            "deadlineAt",
            "eventLog",
        }
        if not isinstance(session, dict) or set(session) != required:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization session schema is invalid.", status=500
            )
        try:
            _opaque_ref(session["id"], field="session.id")
            _sha256(session["requestDigest"], field="session.requestDigest")
            _sha256(session["idempotencyKeyDigest"], field="session.idempotencyKeyDigest")
            _opaque_ref(session["workspaceRef"], field="session.workspaceRef")
        except OptimizationDomainError as error:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization session identity is invalid.", status=500
            ) from error
        if session["schemaVersion"] != SCHEMA_VERSION:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization session version is invalid.", status=500
            )
        try:
            stored_request = _validate_normalized_request_record(session["request"])
            if _sha256_json(stored_request) != session["requestDigest"]:
                raise OptimizationDomainError(
                    "invalid_request", "Stored request digest is invalid.", status=422
                )
            if (
                session["buildId"] != stored_request["buildId"]
                or session["sourceDigest"] != stored_request["sourceDigest"]
                or session["baselineReportSha256"]
                != stored_request["baselineReportSha256"]
                or session["platform"] != stored_request["platform"]
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Stored session metadata is inconsistent.", status=422
                )
            _identifier(session["buildId"], field="session.buildId")
            _sha256(session["sourceDigest"], field="session.sourceDigest")
            _sha256(
                session["baselineReportSha256"],
                field="session.baselineReportSha256",
            )
        except OptimizationDomainError as error:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization stored request is invalid.", status=500
            ) from error
        if session["state"] not in SESSION_STATES or session["stage"] not in STAGES:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization session state is invalid.", status=500
            )
        if session["platform"] not in {"mt4", "mt5"}:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization session platform is invalid.", status=500
            )
        if not isinstance(session["roundCount"], int) or not 1 <= session["roundCount"] <= MAX_ROUNDS:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization session round count is invalid.", status=500
            )
        if not isinstance(session["roundIndex"], int) or not 0 <= session["roundIndex"] < session["roundCount"]:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization session round index is invalid.", status=500
            )
        if (
            not isinstance(session["attemptsByRound"], list)
            or len(session["attemptsByRound"]) != session["roundCount"]
            or any(not isinstance(item, int) or item < 0 for item in session["attemptsByRound"])
        ):
            raise OptimizationDomainError(
                "store_corrupt", "Optimization attempt counters are invalid.", status=500
            )
        if not isinstance(session["roundResults"], list) or len(session["roundResults"]) > session["roundCount"]:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization results are invalid.", status=500
            )
        progress = session["progress"]
        if not isinstance(progress, dict) or set(progress) != {
            "roundNumber",
            "roundCount",
            "passCount",
            "returnedPassCount",
            "percent",
            "rowsTruncated",
        }:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization progress is invalid.", status=500
            )
        if (
            progress["roundNumber"] != session["roundIndex"] + 1
            or progress["roundCount"] != session["roundCount"]
            or isinstance(progress["passCount"], bool)
            or not isinstance(progress["passCount"], int)
            or progress["passCount"] < 0
            or isinstance(progress["returnedPassCount"], bool)
            or not isinstance(progress["returnedPassCount"], int)
            or progress["returnedPassCount"] < 0
            or progress["returnedPassCount"] > progress["passCount"]
            or isinstance(progress["percent"], bool)
            or not isinstance(progress["percent"], (int, float))
            or not math.isfinite(progress["percent"])
            or not 0 <= progress["percent"] <= 100
            or not isinstance(progress["rowsTruncated"], bool)
        ):
            raise OptimizationDomainError(
                "store_corrupt", "Optimization progress is invalid.", status=500
            )
        if not isinstance(session["cancelRequested"], bool):
            raise OptimizationDomainError(
                "store_corrupt", "Optimization cancellation state is invalid.", status=500
            )
        if session["cancelReason"] is not None:
            try:
                _identifier(session["cancelReason"], field="session.cancelReason")
            except OptimizationDomainError as error:
                raise OptimizationDomainError(
                    "store_corrupt", "Optimization cancellation state is invalid.", status=500
                ) from error
        if session["failure"] is not None:
            failure = session["failure"]
            if not isinstance(failure, dict) or set(failure) != {
                "code",
                "message",
                "executionMayStillBeRunning",
            }:
                raise OptimizationDomainError(
                    "store_corrupt", "Optimization failure state is invalid.", status=500
                )
            try:
                _identifier(failure["code"], field="session.failure.code")
                _safe_text(
                    failure["message"],
                    field="session.failure.message",
                    maximum=512,
                )
            except OptimizationDomainError as error:
                raise OptimizationDomainError(
                    "store_corrupt", "Optimization failure state is invalid.", status=500
                ) from error
            if not isinstance(failure["executionMayStillBeRunning"], bool):
                raise OptimizationDomainError(
                    "store_corrupt", "Optimization failure state is invalid.", status=500
                )
        elif session["state"] == "failed":
            raise OptimizationDomainError(
                "store_corrupt", "Failed optimization is missing its failure.", status=500
            )
        if not isinstance(session["eventLog"], list) or len(session["eventLog"]) > MAX_EVENTS:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization event log is invalid.", status=500
            )
        for field in ("createdAt", "updatedAt", "heartbeatAt", "deadlineAt"):
            value = session[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise OptimizationDomainError(
                    "store_corrupt", f"Optimization {field} is invalid.", status=500
                )
        try:
            binding = self._validate_terminal_binding(
                session["terminalBinding"], session["platform"]
            )
            if (
                binding["candidateId"] != stored_request["terminalCandidateId"]
                or binding["selectionRevision"]
                != stored_request["terminalSelectionRevision"]
                or binding["bindingDigest"]
                != stored_request["terminalBindingDigest"]
            ):
                raise OptimizationDomainError(
                    "terminal_binding_changed", "Stored binding is inconsistent.", status=409
                )
            self._validate_operation_record(session)
            self._validate_round_result_records(session)
        except OptimizationDomainError as error:
            raise OptimizationDomainError(
                "store_corrupt", "Optimization durable state is invalid.", status=500
            ) from error

    def _validate_operation_record(self, session: Mapping[str, Any]) -> None:
        operation = session["currentOperation"]
        if operation is None:
            return
        row = _exact_keys(
            operation,
            field="currentOperation",
            required={
                "operationId",
                "roundId",
                "attempt",
                "boundaryRef",
                "boundaryDocumentSha256",
                "recoveryRequired",
                "safeBeforeStartRetry",
                "notStartedProofSha256",
                "receipt",
                "handlerInvocation",
            },
            optional={"executionIdentity", "executionStopProof"},
        )
        operation_id = _opaque_ref(row["operationId"], field="operation.operationId")
        round_spec = session["request"]["rounds"][session["roundIndex"]]
        if row["roundId"] != round_spec["roundId"]:
            raise OptimizationDomainError(
                "invalid_request", "Operation round is inconsistent.", status=422
            )
        attempt = _positive_int(
            row["attempt"], field="operation.attempt", maximum=MAX_START_ATTEMPTS
        )
        if attempt != session["attemptsByRound"][session["roundIndex"]]:
            raise OptimizationDomainError(
                "invalid_request", "Operation attempt is inconsistent.", status=422
            )
        expected_suffix = operation_id[3:]
        if row["boundaryRef"] != "boundary_" + expected_suffix:
            raise OptimizationDomainError(
                "invalid_request", "Operation boundary is inconsistent.", status=422
            )
        _opaque_ref(row["boundaryRef"], field="operation.boundaryRef")
        _sha256(
            row["boundaryDocumentSha256"],
            field="operation.boundaryDocumentSha256",
        )
        if not isinstance(row["recoveryRequired"], bool) or not isinstance(
            row["safeBeforeStartRetry"], bool
        ):
            raise OptimizationDomainError(
                "invalid_request", "Operation recovery flags are invalid.", status=422
            )
        if row["notStartedProofSha256"] is not None:
            _sha256(
                row["notStartedProofSha256"],
                field="operation.notStartedProofSha256",
            )
        if row["safeBeforeStartRetry"] and (
            row["notStartedProofSha256"] is None
            or row["recoveryRequired"]
            or row["receipt"] is not None
        ):
            raise OptimizationDomainError(
                "invalid_request", "Before-Start recovery state is inconsistent.", status=422
            )
        execution_identity = row.get("executionIdentity")
        if execution_identity is not None:
            self._validate_execution_identity(
                execution_identity, session["terminalBinding"]
            )
        execution_stop_proof = row.get("executionStopProof")
        if execution_stop_proof is not None:
            proof_row = _exact_keys(
                execution_stop_proof,
                field="operation.executionStopProof",
                required={
                    "reasonCode",
                    "proofSha256",
                    "observedAt",
                    "identitySha256",
                },
            )
            _identifier(
                proof_row["reasonCode"],
                field="operation.executionStopProof.reasonCode",
            )
            _sha256(
                proof_row["proofSha256"],
                field="operation.executionStopProof.proofSha256",
            )
            _sha256(
                proof_row["identitySha256"],
                field="operation.executionStopProof.identitySha256",
            )
            observed_at = proof_row["observedAt"]
            if (
                isinstance(observed_at, bool)
                or not isinstance(observed_at, (int, float))
                or not math.isfinite(float(observed_at))
                or float(observed_at) < 0
                or execution_identity is None
                or proof_row["identitySha256"]
                != execution_identity.get("identitySha256")
            ):
                raise OptimizationDomainError(
                    "invalid_request",
                    "Execution-stop proof is inconsistent.",
                    status=422,
                )
        receipt = row["receipt"]
        if receipt is not None:
            receipt_row = _exact_keys(
                receipt,
                field="operation.receipt",
                required={
                    "receiptRef",
                    "startedAt",
                    "documentRef",
                    "documentSha256",
                },
            )
            expected_receipt_ref = "receipt_" + expected_suffix
            if (
                receipt_row["receiptRef"] != expected_receipt_ref
                or receipt_row["documentRef"] != expected_receipt_ref
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Operation receipt is inconsistent.", status=422
                )
            _opaque_ref(receipt_row["receiptRef"], field="operation.receipt.receiptRef")
            _opaque_ref(
                receipt_row["documentRef"], field="operation.receipt.documentRef"
            )
            _sha256(
                receipt_row["documentSha256"],
                field="operation.receipt.documentSha256",
            )
            started_at = receipt_row["startedAt"]
            if (
                isinstance(started_at, bool)
                or not isinstance(started_at, (int, float))
                or not math.isfinite(started_at)
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Operation receipt time is invalid.", status=422
                )
        invocation = row["handlerInvocation"]
        if invocation is not None:
            invocation_row = _exact_keys(
                invocation,
                field="operation.handlerInvocation",
                required={"invocationId", "action", "claimedAt"},
            )
            _opaque_ref(
                invocation_row["invocationId"],
                field="operation.handlerInvocation.invocationId",
            )
            if invocation_row["action"] not in {
                "start_round",
                "recover_round",
                "collect_round",
            }:
                raise OptimizationDomainError(
                    "invalid_request", "Handler invocation action is invalid.", status=422
                )
            claimed_at = invocation_row["claimedAt"]
            if (
                isinstance(claimed_at, bool)
                or not isinstance(claimed_at, (int, float))
                or not math.isfinite(claimed_at)
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Handler invocation time is invalid.", status=422
                )
            if invocation_row["action"] == "start_round" and receipt is not None:
                raise OptimizationDomainError(
                    "invalid_request", "Start invocation already has a receipt.", status=422
                )
            if invocation_row["action"] == "collect_round" and receipt is None:
                raise OptimizationDomainError(
                    "invalid_request", "Collection invocation is missing a receipt.", status=422
                )

    def _validate_round_result_records(self, session: Mapping[str, Any]) -> None:
        seen_rounds: set[str] = set()
        expected_tester_digest = _sha256_json(
            session["request"]["testerSettings"]
        )
        for result in session["roundResults"]:
            row = _exact_keys(
                result,
                field="roundResult",
                required={
                    "roundId",
                    "roundIndex",
                    "combinationCount",
                    "passCount",
                    "returnedPassCount",
                    "rowsTruncated",
                    "report",
                    "manifest",
                    "testerSettingsSha256",
                    "visibleEvidenceSha256",
                    "warnings",
                    "documentRef",
                    "documentSha256",
                    "analyzed",
                },
                optional={"initialDeposit", "analysisRef", "analysisSha256"},
            )
            round_index = row["roundIndex"]
            if (
                isinstance(round_index, bool)
                or not isinstance(round_index, int)
                or not 0 <= round_index < session["roundCount"]
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Stored result round is invalid.", status=422
                )
            round_spec = session["request"]["rounds"][round_index]
            if (
                row["roundId"] != round_spec["roundId"]
                or row["roundId"] in seen_rounds
                or row["combinationCount"] != round_spec["combinationCount"]
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Stored result identity is invalid.", status=422
                )
            seen_rounds.add(row["roundId"])
            pass_count = _positive_int(
                row["passCount"],
                field="roundResult.passCount",
                maximum=round_spec["combinationCount"],
            )
            if pass_count < 2:
                raise OptimizationDomainError(
                    "invalid_request",
                    "Stored optimization result must contain at least two passes.",
                    status=422,
                )
            returned = _positive_int(
                row["returnedPassCount"],
                field="roundResult.returnedPassCount",
                maximum=min(pass_count, MAX_RESULT_ROWS),
            )
            if (
                not isinstance(row["rowsTruncated"], bool)
                or row["rowsTruncated"] != (returned < pass_count)
                or not isinstance(row["analyzed"], bool)
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Stored result progress is invalid.", status=422
                )
            self._artifact(row["report"], field="roundResult.report")
            self._artifact(row["manifest"], field="roundResult.manifest")
            if (
                _sha256(
                    row["testerSettingsSha256"],
                    field="roundResult.testerSettingsSha256",
                )
                != expected_tester_digest
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Stored tester settings digest is invalid.", status=422
                )
            _sha256(
                row["visibleEvidenceSha256"],
                field="roundResult.visibleEvidenceSha256",
            )
            if "initialDeposit" in row and (
                isinstance(row["initialDeposit"], bool)
                or not isinstance(row["initialDeposit"], (int, float))
                or not math.isfinite(float(row["initialDeposit"]))
                or float(row["initialDeposit"]) <= 0
            ):
                raise OptimizationDomainError(
                    "invalid_request", "Stored initial deposit is invalid.", status=422
                )
            if not isinstance(row["warnings"], list) or len(row["warnings"]) > MAX_WARNINGS:
                raise OptimizationDomainError(
                    "invalid_request", "Stored result warnings are invalid.", status=422
                )
            for index, warning in enumerate(row["warnings"]):
                _safe_text(
                    warning,
                    field=f"roundResult.warnings[{index}]",
                    maximum=256,
                )
            expected_ref = "result_" + row["roundId"].replace("-", "_")
            if row["documentRef"] != expected_ref:
                raise OptimizationDomainError(
                    "invalid_request", "Stored result document is invalid.", status=422
                )
            _opaque_ref(row["documentRef"], field="roundResult.documentRef")
            _sha256(
                row["documentSha256"], field="roundResult.documentSha256"
            )
            analysis_ref = row.get("analysisRef")
            analysis_digest = row.get("analysisSha256")
            if (analysis_ref is None) != (analysis_digest is None):
                raise OptimizationDomainError(
                    "invalid_request", "Stored analysis binding is incomplete.", status=422
                )
            if analysis_ref is not None:
                expected_analysis_ref = "analysis_" + row["roundId"].replace("-", "_")
                if analysis_ref != expected_analysis_ref or row["analyzed"] is not True:
                    raise OptimizationDomainError(
                        "invalid_request", "Stored analysis binding is invalid.", status=422
                    )
                _opaque_ref(analysis_ref, field="roundResult.analysisRef")
                _sha256(analysis_digest, field="roundResult.analysisSha256")

    def _workspace_path(self, workspace_ref: str) -> Path:
        ref = _opaque_ref(workspace_ref, field="workspaceRef")
        workspace = self._workspaces_root / ref
        if workspace.parent != self._workspaces_root or _unsafe_path(workspace):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization workspace is unsafe.", status=409
            )
        return workspace

    def _document_path(self, workspace_ref: str, document_ref: str) -> Path:
        workspace = self._workspace_path(workspace_ref)
        ref = _opaque_ref(document_ref, field="documentRef")
        path = workspace / f"{ref}.json"
        if path.parent != workspace or _unsafe_path(path):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization document path is unsafe.", status=409
            )
        return path

    def _write_immutable_document(
        self, workspace_ref: str, document_ref: str, payload: Mapping[str, Any]
    ) -> str:
        encoded = _canonical_bytes(payload) + b"\n"
        if len(encoded) > MAX_DOCUMENT_BYTES:
            raise OptimizationDomainError(
                "document_too_large", "Optimization evidence document is too large.", status=413
            )
        path = self._document_path(workspace_ref, document_ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        if _unsafe_path(path.parent):
            raise OptimizationDomainError(
                "unsafe_storage_path", "Optimization workspace is unsafe.", status=409
            )
        digest = _sha256_bytes(encoded)
        try:
            descriptor = os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except FileExistsError:
            existing = path.read_bytes()
            if existing != encoded:
                raise OptimizationDomainError(
                    "immutable_document_conflict",
                    "An immutable optimization document changed.",
                    status=409,
                )
            return digest
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        with contextlib.suppress(OSError):
            os.chmod(path, 0o400)
        return digest

    def _read_document(
        self, workspace_ref: str, document_ref: str, expected_digest: str
    ) -> dict[str, Any]:
        path = self._document_path(workspace_ref, document_ref)
        try:
            raw = path.read_bytes()
        except FileNotFoundError as error:
            raise OptimizationDomainError(
                "evidence_missing", "Optimization evidence document is missing.", status=500
            ) from error
        if len(raw) > MAX_DOCUMENT_BYTES or _sha256_bytes(raw) != expected_digest:
            raise OptimizationDomainError(
                "evidence_tampered", "Optimization evidence integrity check failed.", status=500
            )
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise OptimizationDomainError(
                "evidence_tampered", "Optimization evidence is invalid.", status=500
            ) from error
        if not isinstance(value, dict):
            raise OptimizationDomainError(
                "evidence_tampered", "Optimization evidence is invalid.", status=500
            )
        return value

    def _validate_workspace_documents(self, session: Mapping[str, Any]) -> None:
        operation = session.get("currentOperation")
        if isinstance(operation, dict):
            boundary = self._read_document(
                session["workspaceRef"],
                operation["boundaryRef"],
                operation["boundaryDocumentSha256"],
            )
            if boundary.get("operationId") != operation.get("operationId"):
                raise OptimizationDomainError(
                    "evidence_tampered", "Optimization start boundary does not match state.", status=500
                )
            receipt = operation.get("receipt")
            if isinstance(receipt, dict):
                stored = self._read_document(
                    session["workspaceRef"],
                    receipt["documentRef"],
                    receipt["documentSha256"],
                )
                if stored.get("operationId") != operation.get("operationId"):
                    raise OptimizationDomainError(
                        "evidence_tampered", "Optimization receipt does not match state.", status=500
                    )
        for result in session.get("roundResults", []):
            stored = self._read_document(
                session["workspaceRef"], result["documentRef"], result["documentSha256"]
            )
            if stored.get("roundId") != result.get("roundId"):
                raise OptimizationDomainError(
                    "evidence_tampered", "Optimization result does not match state.", status=500
                )

    def _save_unlocked(self, store: dict[str, Any]) -> None:
        store["revision"] += 1
        self._write_store_unlocked(store)

    def _audit(self, event: Mapping[str, Any]) -> None:
        try:
            self._audit_callback(copy.deepcopy(dict(event)))
        except Exception as error:
            raise OptimizationDomainError(
                "audit_callback_failed",
                "Optimization state was saved but audit publication failed.",
                status=503,
            ) from error

    def _rollback_undispatched_operation_after_audit_failure(
        self,
        store: dict[str, Any],
        session: dict[str, Any],
        operation: dict[str, Any],
        *,
        failed_event_type: str,
    ) -> None:
        """Make a pre-dispatch audit failure retryable without inventing success.

        The caller invokes this only on the synchronous path before the
        adapter function is called.  The durable event log remains the
        mandatory local audit record even when the external audit sink is
        transiently unavailable.
        """

        now = self._now()
        invocation = operation.get("handlerInvocation")
        undispatched_action = (
            invocation.get("action") if isinstance(invocation, dict) else None
        )
        start_was_not_dispatched = bool(
            failed_event_type == "start_boundary_committed"
            or undispatched_action == "start_round"
        )
        operation["handlerInvocation"] = None
        if start_was_not_dispatched:
            proof = _sha256_json(
                {
                    "kind": "optimization_start_not_dispatched",
                    "sessionId": session["id"],
                    "operationId": operation["operationId"],
                    "failedEventType": failed_event_type,
                    "recordedAt": now,
                }
            )
            operation["recoveryRequired"] = False
            operation["safeBeforeStartRetry"] = True
            operation["notStartedProofSha256"] = proof
            session["state"] = "awaiting_visible_terminal"
        else:
            # collect/recover audit failure occurs after a previous Start may
            # already be executing. Clearing only this undispatched claim is
            # safe; granting a new Start here would allow overlapping testers.
            proof = None
            operation["recoveryRequired"] = True
            operation["safeBeforeStartRetry"] = False
            operation["notStartedProofSha256"] = None
            session["state"] = (
                "collecting"
                if isinstance(operation.get("receipt"), dict)
                else "awaiting_visible_terminal"
            )
        session["updatedAt"] = now
        session["heartbeatAt"] = now
        self._event(
            session,
            "undispatched_handler_claim_rolled_back",
            now,
            operationId=operation["operationId"],
            failedEventType=failed_event_type,
            undispatchedAction=undispatched_action,
            startWasNotDispatched=start_was_not_dispatched,
            **(
                {"notStartedProofSha256": proof}
                if proof is not None
                else {}
            ),
        )
        self._save_unlocked(store)

    def _event(
        self,
        session: dict[str, Any],
        event_type: str,
        now: float,
        **fields: Any,
    ) -> dict[str, Any]:
        event = {
            "type": _identifier(event_type, field="eventType"),
            "at": now,
            "sessionId": session["id"],
            "state": session["state"],
            "stage": session["stage"],
        }
        for key, value in fields.items():
            if value is not None:
                event[key] = value
        session["eventLog"].append(event)
        if len(session["eventLog"]) > MAX_EVENTS:
            session["eventLog"] = session["eventLog"][-MAX_EVENTS:]
        return event

    @staticmethod
    def _session(store: Mapping[str, Any], session_id: str) -> dict[str, Any]:
        safe_id = _opaque_ref(session_id, field="sessionId")
        for session in store["sessions"]:
            if session["id"] == safe_id:
                return session
        raise OptimizationDomainError(
            "session_not_found", "Optimization session was not found.", status=404
        )

    @staticmethod
    def _execution_quarantined(session: Mapping[str, Any]) -> bool:
        failure = session.get("failure")
        return bool(
            session.get("state") in ACTIVE_STATES
            and isinstance(failure, dict)
            and failure.get("executionMayStillBeRunning") is True
        )

    def _late_completed_discard_recovery_proof(
        self, session: Mapping[str, Any]
    ) -> str | None:
        """Return the legacy discard proof only for one exact recoverable operation.

        Older service revisions deliberately converted a fully validated
        ``recover_round``/``collect_round`` completion into terminal failure.
        Reopening that state is safe only when the durable operation, immutable
        boundary, immutable receipt, and local event trail all still describe
        the same execution.  This helper is intentionally read-only.
        """

        failure = session.get("failure")
        operation = session.get("currentOperation")
        if (
            session.get("state") != "failed"
            or session.get("stage") != "run_round"
            or session.get("cancelRequested") is True
            or not isinstance(failure, dict)
            or failure.get("executionMayStillBeRunning") is not False
            or not isinstance(operation, dict)
            or not isinstance(operation.get("receipt"), dict)
            or operation.get("handlerInvocation") is not None
            or operation.get("recoveryRequired") is not False
            or operation.get("safeBeforeStartRetry") is True
            or any(
                item.get("roundId") == operation.get("roundId")
                for item in session.get("roundResults", [])
                if isinstance(item, dict)
            )
        ):
            return None

        round_spec = session["request"]["rounds"][session["roundIndex"]]
        attempt = operation.get("attempt")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            return None
        expected_operation_id = "op_" + hashlib.sha256(
            f"{session['id']}:{round_spec['roundId']}:{attempt}".encode("utf-8")
        ).hexdigest()[:40]
        if (
            operation.get("operationId") != expected_operation_id
            or operation.get("roundId") != round_spec["roundId"]
            or operation.get("boundaryRef")
            != "boundary_" + expected_operation_id[3:]
        ):
            return None

        try:
            boundary = self._read_document(
                session["workspaceRef"],
                operation["boundaryRef"],
                operation["boundaryDocumentSha256"],
            )
            expected_boundary = {
                "schemaVersion": SCHEMA_VERSION,
                "kind": "optimization_start_boundary",
                "sessionId": session["id"],
                "operationId": expected_operation_id,
                "roundId": round_spec["roundId"],
                "roundIndex": session["roundIndex"],
                "attempt": attempt,
                "requestDigest": session["requestDigest"],
                "buildId": session["buildId"],
                "sourceDigest": session["sourceDigest"],
                "platform": session["platform"],
                "terminalCandidateId": session["terminalBinding"]["candidateId"],
                "terminalSelectionRevision": session["terminalBinding"][
                    "selectionRevision"
                ],
                "terminalBindingDigest": session["terminalBinding"]["bindingDigest"],
                "combinationCount": round_spec["combinationCount"],
                "startMustBeVisible": True,
                "startExactlyOnce": True,
                "liveTradingAllowed": False,
                "testShutdownTerminal": False,
            }
            created_at = boundary.get("createdAt")
            if (
                set(boundary) != set(expected_boundary) | {"createdAt"}
                or any(boundary.get(key) != value for key, value in expected_boundary.items())
                or isinstance(created_at, bool)
                or not isinstance(created_at, (int, float))
                or not math.isfinite(float(created_at))
            ):
                return None

            receipt_summary = operation["receipt"]
            stored_receipt = self._read_document(
                session["workspaceRef"],
                receipt_summary["documentRef"],
                receipt_summary["documentSha256"],
            )
            receipt_row = _exact_keys(
                stored_receipt,
                field="operation.receipt",
                required={
                    "schemaVersion",
                    "operationId",
                    "roundId",
                    "receiptRef",
                    "startBoundarySha256",
                    "platform",
                    "terminalCandidateId",
                    "terminalSelectionRevision",
                    "terminalBindingDigest",
                    "startedAt",
                },
            )
            expected_receipt_ref = "receipt_" + expected_operation_id[3:]
            started_at = receipt_row["startedAt"]
            if (
                receipt_row["schemaVersion"] != SCHEMA_VERSION
                or receipt_row["operationId"] != expected_operation_id
                or receipt_row["roundId"] != round_spec["roundId"]
                or receipt_row["receiptRef"] != expected_receipt_ref
                or receipt_row["startBoundarySha256"]
                != operation["boundaryDocumentSha256"]
                or receipt_row["platform"] != session["platform"]
                or receipt_row["terminalCandidateId"]
                != session["terminalBinding"]["candidateId"]
                or receipt_row["terminalSelectionRevision"]
                != session["terminalBinding"]["selectionRevision"]
                or receipt_row["terminalBindingDigest"]
                != session["terminalBinding"]["bindingDigest"]
                or isinstance(started_at, bool)
                or not isinstance(started_at, (int, float))
                or not math.isfinite(float(started_at))
                or receipt_summary
                != {
                    "receiptRef": expected_receipt_ref,
                    "startedAt": started_at,
                    "documentRef": expected_receipt_ref,
                    "documentSha256": operation["receipt"]["documentSha256"],
                }
            ):
                return None
        except (KeyError, OSError, TypeError, ValueError, OptimizationDomainError):
            return None

        events = session.get("eventLog")
        if not isinstance(events, list):
            return None
        release_rows = [
            (index, event)
            for index, event in enumerate(events)
            if isinstance(event, dict)
            and event.get("type") == "execution_quarantine_released"
            and event.get("recoveryProof")
            in {"completed_late_discarded", "orphan_completed_late_discarded"}
        ]
        if len(release_rows) != 1:
            return None
        release_index, release = release_rows[0]
        proof = str(release["recoveryProof"])
        failure_code = failure.get("code")
        if (
            release.get("sessionId") != session["id"]
            or release.get("state") != "failed"
            or release.get("stage") != "run_round"
            or release.get("reasonCode") != failure_code
        ):
            return None
        quarantine_indexes = [
            index
            for index, event in enumerate(events[:release_index])
            if isinstance(event, dict)
            and event.get("type") == "execution_quarantine_started"
            and event.get("sessionId") == session["id"]
            and event.get("reasonCode") == failure_code
        ]
        if not quarantine_indexes:
            return None
        quarantine_index = quarantine_indexes[-1]
        later_events = events[release_index + 1 :]
        if any(
            isinstance(event, dict)
            and event.get("type") not in {"restart_recovered"}
            for event in later_events
        ):
            return None
        if proof == "completed_late_discarded":
            recovery_claims = [
                event
                for event in events[quarantine_index + 1 : release_index]
                if isinstance(event, dict)
                and event.get("type") == "handler_invocation_claimed"
                and event.get("operationId") == expected_operation_id
                and event.get("action") in {"recover_round", "collect_round"}
            ]
            # A parser defect may have produced one or more failed recovery
            # attempts before the corrected receipt-only collector returned the
            # terminal evidence.  Multiple recover/collect claims are safe: all
            # are bound to the same committed operation and none can press
            # Start.  What remains forbidden is any later start claim.
            if not recovery_claims:
                return None
            if any(
                isinstance(event, dict)
                and event.get("type") == "handler_invocation_claimed"
                and event.get("action") == "start_round"
                for event in events[quarantine_index + 1 :]
            ):
                return None
        else:
            result_ref = "result_" + str(operation["roundId"]).replace("-", "_")
            try:
                if not self._document_path(
                    session["workspaceRef"], result_ref
                ).exists():
                    return None
            except (OSError, OptimizationDomainError):
                return None
        return proof

    def _restore_late_completed_discard_for_revalidation(
        self, session: dict[str, Any]
    ) -> dict[str, Any] | None:
        proof = self._late_completed_discard_recovery_proof(session)
        if proof is None:
            return None
        operation = session["currentOperation"]
        failure_code = session["failure"]["code"]
        operation["handlerInvocation"] = None
        operation["recoveryRequired"] = True
        operation["safeBeforeStartRetry"] = False
        session["state"] = "collecting"
        session["failure"] = {
            "code": failure_code,
            "message": (
                "The exact late completed result is being revalidated against its "
                "immutable operation boundary and receipt."
            ),
            "executionMayStillBeRunning": True,
        }
        now = self._now()
        session["updatedAt"] = now
        session["heartbeatAt"] = now
        return self._event(
            session,
            "late_completed_result_revalidation_started",
            now,
            operationId=operation["operationId"],
            recoveryProof=proof,
            reasonCode=failure_code,
        )

    @staticmethod
    def _visible_execution_may_be_running(session: Mapping[str, Any]) -> bool:
        """Return true only while a committed round may still own MT tester work."""

        operation = session.get("currentOperation")
        return bool(
            session.get("stage") == "run_round"
            and isinstance(operation, dict)
            and operation.get("safeBeforeStartRetry") is not True
        )

    def _finalize_quarantined_failure_record(
        self,
        session: dict[str, Any],
        now: float,
        *,
        proof: str,
    ) -> dict[str, Any]:
        """Release an execution quarantine only after terminal/not-started proof."""

        operation = session.get("currentOperation")
        if isinstance(operation, dict):
            operation["handlerInvocation"] = None
            operation["recoveryRequired"] = False
        failure = session.get("failure")
        failure_code = (
            failure.get("code")
            if isinstance(failure, dict) and isinstance(failure.get("code"), str)
            else "visible_execution_state_uncertain"
        )
        session["state"] = "failed"
        session["failure"] = {
            "code": failure_code,
            "message": (
                "Optimization failed; recovery proved that "
                "the visible operation is no longer running. Late results were discarded."
            ),
            "executionMayStillBeRunning": False,
        }
        session["updatedAt"] = now
        session["heartbeatAt"] = now
        return self._event(
            session,
            "execution_quarantine_released",
            now,
            reasonCode=failure_code,
            recoveryProof=proof,
        )

    def _expire_active_unlocked(
        self, store: dict[str, Any], now: float
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        changed = False
        for session in store["sessions"]:
            if session["state"] not in ACTIVE_STATES:
                continue
            operation = session.get("currentOperation")
            adapter_call_in_flight = bool(
                isinstance(operation, dict)
                and isinstance(operation.get("handlerInvocation"), dict)
            )
            if self._execution_quarantined(session):
                # The timeout is already durable.  The active slot must
                # remain owned until receipt-only recovery proves that the visible
                # tester stopped or that Start never occurred.
                continue
            post_execution_finalization = bool(
                session.get("stage") in {"verify_report", "analyze", "complete"}
                and isinstance(session.get("roundResults"), list)
                and bool(session.get("roundResults"))
            )
            # Once the native execution has produced an immutable,
            # receipt-bound result document, the original tester deadline must
            # not turn deterministic local verification/analysis into a false
            # timeout (especially after accepting a late exact recovery).  The
            # heartbeat lease remains authoritative below, so a crashed local
            # finalizer still releases the single slot.
            reason: str | None = None
            if not post_execution_finalization and now >= session["deadlineAt"]:
                reason = "session_deadline_exceeded"
            elif (
                not adapter_call_in_flight
                and now - session["heartbeatAt"] >= self._heartbeat_timeout
            ):
                reason = "session_heartbeat_timeout"
            if reason is None:
                continue
            if self._visible_execution_may_be_running(session):
                operation["recoveryRequired"] = True
                session["state"] = (
                    "collecting"
                    if isinstance(operation.get("receipt"), dict)
                    else "awaiting_visible_terminal"
                )
                session["failure"] = {
                    "code": reason,
                    "message": (
                        "Optimization timed out. The visible "
                        "operation is quarantined until recovery proves it is terminal."
                    ),
                    "executionMayStillBeRunning": True,
                }
                event_type = "execution_quarantine_started"
            else:
                session["state"] = "failed"
                session["failure"] = {
                    "code": reason,
                    "message": "Optimization session expired and released the active slot.",
                    "executionMayStillBeRunning": False,
                }
                event_type = "session_timed_out"
            session["updatedAt"] = now
            changed = True
            events.append(self._event(session, event_type, now, reasonCode=reason))
        if changed:
            self._save_unlocked(store)
        return events

    def _validate_terminal_binding(
        self, value: Any, expected_platform: str
    ) -> dict[str, Any]:
        row = _exact_keys(
            value,
            field="terminalBinding",
            required={
                "candidateId",
                "platform",
                "selectionRevision",
                "bindingDigest",
                "terminalRef",
            },
        )
        candidate_id = _identifier(row["candidateId"], field="terminalBinding.candidateId")
        platform = _safe_text(row["platform"], field="terminalBinding.platform", maximum=8).casefold()
        revision = _positive_int(
            row["selectionRevision"],
            field="terminalBinding.selectionRevision",
            maximum=2**31 - 1,
        )
        binding_digest = _sha256(
            row["bindingDigest"], field="terminalBinding.bindingDigest"
        )
        terminal_ref = _opaque_ref(row["terminalRef"], field="terminalBinding.terminalRef")
        if platform != expected_platform:
            raise OptimizationDomainError(
                "terminal_platform_mismatch",
                "Resolved terminal platform does not match the optimization session.",
                status=409,
            )
        return {
            "candidateId": candidate_id,
            "platform": platform,
            "selectionRevision": revision,
            "bindingDigest": binding_digest,
            "terminalRef": terminal_ref,
        }

    @staticmethod
    def _validate_execution_identity(
        value: Any, terminal_binding: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Validate a private, path-free process identity captured before Start.

        This record is never projected to the browser.  It exists solely so a
        trusted Backend prover can distinguish the original terminal process
        from a restarted/replaced process before releasing the single active
        optimization slot.
        """

        row = _exact_keys(
            value,
            field="executionIdentity",
            required={
                "schemaVersion",
                "terminalCandidateId",
                "terminalSelectionRevision",
                "terminalBindingDigest",
                "terminalProcessId",
                "terminalProcessCreatedAt100ns",
                "terminalWindowHandle",
                "terminalExecutablePathDigest",
                "terminalExecutableSha256",
                "capturedAt",
                "identitySha256",
            },
        )
        if row["schemaVersion"] != EXECUTION_IDENTITY_SCHEMA:
            raise OptimizationDomainError(
                "execution_identity_invalid",
                "Optimization execution identity schema is invalid.",
                status=502,
            )
        candidate_id = _identifier(
            row["terminalCandidateId"], field="executionIdentity.terminalCandidateId"
        )
        revision = _positive_int(
            row["terminalSelectionRevision"],
            field="executionIdentity.terminalSelectionRevision",
            maximum=2**31 - 1,
        )
        binding_digest = _sha256(
            row["terminalBindingDigest"],
            field="executionIdentity.terminalBindingDigest",
        )
        process_id = _positive_int(
            row["terminalProcessId"],
            field="executionIdentity.terminalProcessId",
            maximum=2**31 - 1,
        )
        process_created = row["terminalProcessCreatedAt100ns"]
        window_handle = row["terminalWindowHandle"]
        if (
            isinstance(process_created, bool)
            or not isinstance(process_created, int)
            or process_created <= 0
            or isinstance(window_handle, bool)
            or not isinstance(window_handle, int)
            or window_handle <= 0
        ):
            raise OptimizationDomainError(
                "execution_identity_invalid",
                "Optimization execution process identity is invalid.",
                status=502,
            )
        executable_digest = _sha256(
            row["terminalExecutableSha256"],
            field="executionIdentity.terminalExecutableSha256",
        )
        executable_path_digest = _sha256(
            row["terminalExecutablePathDigest"],
            field="executionIdentity.terminalExecutablePathDigest",
        )
        captured_at = row["capturedAt"]
        if (
            isinstance(captured_at, bool)
            or not isinstance(captured_at, (int, float))
            or not math.isfinite(float(captured_at))
            or float(captured_at) < 0
        ):
            raise OptimizationDomainError(
                "execution_identity_invalid",
                "Optimization execution identity time is invalid.",
                status=502,
            )
        identity = {
            "schemaVersion": EXECUTION_IDENTITY_SCHEMA,
            "terminalCandidateId": candidate_id,
            "terminalSelectionRevision": revision,
            "terminalBindingDigest": binding_digest,
            "terminalProcessId": process_id,
            "terminalProcessCreatedAt100ns": process_created,
            "terminalWindowHandle": window_handle,
            "terminalExecutablePathDigest": executable_path_digest,
            "terminalExecutableSha256": executable_digest,
            "capturedAt": float(captured_at),
        }
        identity_digest = _sha256(
            row["identitySha256"], field="executionIdentity.identitySha256"
        )
        if (
            candidate_id != terminal_binding.get("candidateId")
            or revision != terminal_binding.get("selectionRevision")
            or binding_digest != terminal_binding.get("bindingDigest")
            or not secrets.compare_digest(identity_digest, _sha256_json(identity))
        ):
            raise OptimizationDomainError(
                "execution_identity_invalid",
                "Optimization execution identity does not match the terminal binding.",
                status=502,
            )
        return {**identity, "identitySha256": identity_digest}

    def _resolve_exact_target(self, request: Mapping[str, Any]) -> dict[str, Any]:
        expected = {
            "candidateId": request["terminalCandidateId"],
            "platform": request["platform"],
            "selectionRevision": request["terminalSelectionRevision"],
            "bindingDigest": request["terminalBindingDigest"],
        }
        try:
            resolved = self._target_resolver(copy.deepcopy(expected))
        except OptimizationDomainError:
            raise
        except Exception as error:
            raise OptimizationDomainError(
                "terminal_resolution_failed",
                "The selected MetaTrader terminal could not be resolved.",
                status=503,
            ) from error
        binding = self._validate_terminal_binding(resolved, request["platform"])
        if (
            binding["candidateId"] != expected["candidateId"]
            or binding["selectionRevision"] != expected["selectionRevision"]
            or binding["bindingDigest"] != expected["bindingDigest"]
        ):
            raise OptimizationDomainError(
                "terminal_binding_changed",
                "The selected MetaTrader binding changed.",
                status=409,
            )
        return binding

    def _capability(
        self, session: Mapping[str, Any]
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        request = {
            "schemaVersion": SCHEMA_VERSION,
            "operation": "optimization",
            "platform": session["platform"],
            "terminalBinding": copy.deepcopy(session["terminalBinding"]),
            "requiresVisibleTerminal": True,
            "requiresVisibleStrategyTester": True,
            "liveTradingAllowed": False,
            "testShutdownTerminal": False,
            "closeTerminalAllowed": False,
        }
        try:
            raw = self._capability_provider(request)
        except Exception as error:
            raise OptimizationDomainError(
                "capability_check_failed",
                "Visible-terminal capability could not be checked.",
                status=503,
            ) from error
        row = _exact_keys(
            raw,
            field="capability",
            required={"ready", "platform", "candidateId", "selectionRevision", "bindingDigest"},
            optional={"reasonCode", "executionIdentity"},
        )
        if not isinstance(row["ready"], bool):
            raise OptimizationDomainError(
                "capability_invalid", "Capability response is invalid.", status=502
            )
        if (
            row["platform"] != session["platform"]
            or row["candidateId"] != session["terminalBinding"]["candidateId"]
            or row["selectionRevision"] != session["terminalBinding"]["selectionRevision"]
            or row["bindingDigest"] != session["terminalBinding"]["bindingDigest"]
        ):
            raise OptimizationDomainError(
                "terminal_binding_changed",
                "Visible-terminal capability is bound to a different terminal.",
                status=409,
            )
        reason = None
        if "reasonCode" in row and row["reasonCode"] is not None:
            reason = _identifier(row["reasonCode"], field="capability.reasonCode")
        execution_identity = None
        if row.get("executionIdentity") is not None:
            execution_identity = self._validate_execution_identity(
                row["executionIdentity"], session["terminalBinding"]
            )
        return row["ready"], reason, execution_identity

    def _fail_session(
        self,
        store: dict[str, Any],
        session: dict[str, Any],
        *,
        code: str,
        message: str,
        status: int = 409,
    ) -> OptimizationDomainError:
        now = self._now()
        operation = session.get("currentOperation")
        execution_may_still_run = self._visible_execution_may_be_running(session)
        if execution_may_still_run:
            operation["recoveryRequired"] = True
            session["state"] = (
                "collecting"
                if isinstance(operation.get("receipt"), dict)
                else "awaiting_visible_terminal"
            )
            event_type = "execution_quarantine_started"
        else:
            session["state"] = "failed"
            event_type = "session_failed"
        session["failure"] = {
            "code": code,
            "message": message,
            "executionMayStillBeRunning": execution_may_still_run,
        }
        session["updatedAt"] = now
        session["heartbeatAt"] = now
        event = self._event(session, event_type, now, reasonCode=code)
        self._save_unlocked(store)
        self._audit(event)
        return OptimizationDomainError(code, message, status=status)

    def create(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Create or replay a strictly idempotent optimization session."""

        normalized, idempotency_key = _normalize_request(dict(request))
        request_digest = _sha256_json(normalized)
        key_digest = _sha256_bytes(idempotency_key.encode("utf-8"))
        preliminary_events: list[dict[str, Any]] = []
        with self._locked():
            store = self._load_store_unlocked()
            preliminary_events.extend(
                self._expire_active_unlocked(store, self._now())
            )
            if preliminary_events:
                store = self._load_store_unlocked()
            for existing in store["sessions"]:
                if existing["idempotencyKeyDigest"] != key_digest:
                    continue
                if existing["requestDigest"] != request_digest:
                    raise OptimizationDomainError(
                        "idempotency_conflict",
                        "The idempotency key is already bound to a different request.",
                        status=409,
                    )
                response = self._public(existing)
                response["replayed"] = True
                break
            else:
                response = None
        for event in preliminary_events:
            self._audit(event)
        if response is not None:
            return response

        binding = self._resolve_exact_target(normalized)
        events: list[dict[str, Any]] = []
        with self._locked():
            store = self._load_store_unlocked()
            now = self._now()
            events.extend(self._expire_active_unlocked(store, now))
            if events:
                store = self._load_store_unlocked()
            for existing in store["sessions"]:
                if existing["idempotencyKeyDigest"] != key_digest:
                    continue
                if existing["requestDigest"] != request_digest:
                    raise OptimizationDomainError(
                        "idempotency_conflict",
                        "The idempotency key is already bound to a different request.",
                        status=409,
                    )
                response = self._public(existing)
                response["replayed"] = True
                for event in events:
                    self._audit(event)
                return response
            active = next(
                (item for item in store["sessions"] if item["state"] in ACTIVE_STATES),
                None,
            )
            if active is not None:
                raise OptimizationDomainError(
                    "optimization_busy",
                    "Another optimization session is active.",
                    status=409,
                    details={"activeSessionId": active["id"]},
                )
            if len(store["sessions"]) >= MAX_SESSIONS:
                terminal = [item for item in store["sessions"] if item["state"] in TERMINAL_STATES]
                if not terminal:
                    raise OptimizationDomainError(
                        "session_limit", "Optimization session limit reached.", status=409
                    )
                oldest = min(terminal, key=lambda item: item["updatedAt"])
                store["sessions"].remove(oldest)
            session_id = "opts_" + uuid.uuid4().hex
            workspace_ref = "optw_" + uuid.uuid4().hex
            self._workspace_path(workspace_ref).mkdir(parents=True, exist_ok=False)
            session = {
                "schemaVersion": SCHEMA_VERSION,
                "id": session_id,
                "requestDigest": request_digest,
                "idempotencyKeyDigest": key_digest,
                "request": normalized,
                "buildId": normalized["buildId"],
                "sourceDigest": normalized["sourceDigest"],
                "baselineReportSha256": normalized["baselineReportSha256"],
                "platform": normalized["platform"],
                "terminalBinding": binding,
                "workspaceRef": workspace_ref,
                "state": "queued",
                "stage": "validate_baseline",
                "roundIndex": 0,
                "roundCount": len(normalized["rounds"]),
                "attemptsByRound": [0 for _ in normalized["rounds"]],
                "progress": {
                    "roundNumber": 1,
                    "roundCount": len(normalized["rounds"]),
                    "passCount": 0,
                    "returnedPassCount": 0,
                    "percent": 0.0,
                    "rowsTruncated": False,
                },
                "currentOperation": None,
                "roundResults": [],
                "cancelRequested": False,
                "cancelReason": None,
                "failure": None,
                "createdAt": now,
                "updatedAt": now,
                "heartbeatAt": now,
                "deadlineAt": now + self._deadline_seconds,
                "eventLog": [],
            }
            event = self._event(session, "session_created", now)
            store["sessions"].append(session)
            self._save_unlocked(store)
            events.append(event)
            response = self._public(session)
            response["replayed"] = False
        for event in events:
            self._audit(event)
        return response

    def read(self, session_id: str) -> dict[str, Any]:
        """Return a bounded public read model and verify durable evidence."""

        events: list[dict[str, Any]] = []
        with self._locked():
            store = self._load_store_unlocked()
            events.extend(self._expire_active_unlocked(store, self._now()))
            if events:
                store = self._load_store_unlocked()
            response = self._public(self._session(store, session_id))
        for event in events:
            self._audit(event)
        return response

    def list(self) -> list[dict[str, Any]]:
        """Return validated public sessions, newest update first."""

        events: list[dict[str, Any]] = []
        with self._locked():
            store = self._load_store_unlocked()
            events.extend(self._expire_active_unlocked(store, self._now()))
            if events:
                store = self._load_store_unlocked()
            ordered = sorted(
                store["sessions"],
                key=lambda item: (item["updatedAt"], item["createdAt"], item["id"]),
                reverse=True,
            )
            response = [self._public(item) for item in ordered]
        for event in events:
            self._audit(event)
        return response

    def _verify_binding_or_fail(
        self, store: dict[str, Any], session: dict[str, Any]
    ) -> None:
        try:
            binding = self._resolve_exact_target(session["request"])
        except OptimizationDomainError as error:
            raise self._fail_session(
                store,
                session,
                code="terminal_binding_changed",
                message="The selected MetaTrader terminal changed during optimization.",
            ) from error
        if binding != session["terminalBinding"]:
            raise self._fail_session(
                store,
                session,
                code="terminal_binding_changed",
                message="The selected MetaTrader terminal changed during optimization.",
            )

    def _prepare_start_boundary(
        self,
        store: dict[str, Any],
        session: dict[str, Any],
        execution_identity: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        index = session["roundIndex"]
        attempt = session["attemptsByRound"][index] + 1
        if attempt > MAX_START_ATTEMPTS:
            raise self._fail_session(
                store,
                session,
                code="start_retry_limit",
                message="Visible Start could not be safely reached within the retry limit.",
            )
        session["attemptsByRound"][index] = attempt
        round_spec = session["request"]["rounds"][index]
        operation_id = "op_" + hashlib.sha256(
            f"{session['id']}:{round_spec['roundId']}:{attempt}".encode("utf-8")
        ).hexdigest()[:40]
        boundary_ref = "boundary_" + operation_id[3:]
        boundary_base = {
            "schemaVersion": SCHEMA_VERSION,
            "kind": "optimization_start_boundary",
            "sessionId": session["id"],
            "operationId": operation_id,
            "roundId": round_spec["roundId"],
            "roundIndex": index,
            "attempt": attempt,
            "requestDigest": session["requestDigest"],
            "buildId": session["buildId"],
            "sourceDigest": session["sourceDigest"],
            "platform": session["platform"],
            "terminalCandidateId": session["terminalBinding"]["candidateId"],
            "terminalSelectionRevision": session["terminalBinding"]["selectionRevision"],
            "terminalBindingDigest": session["terminalBinding"]["bindingDigest"],
            "combinationCount": round_spec["combinationCount"],
            "startMustBeVisible": True,
            "startExactlyOnce": True,
            "liveTradingAllowed": False,
            "testShutdownTerminal": False,
        }
        path = self._document_path(session["workspaceRef"], boundary_ref)
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (UnicodeError, json.JSONDecodeError) as error:
                raise OptimizationDomainError(
                    "evidence_tampered", "Start boundary is invalid.", status=500
                ) from error
            created_at = existing.get("createdAt") if isinstance(existing, dict) else None
            if (
                not isinstance(existing, dict)
                or set(existing) != set(boundary_base) | {"createdAt"}
                or any(existing.get(key) != value for key, value in boundary_base.items())
                or isinstance(created_at, bool)
                or not isinstance(created_at, (int, float))
                or not math.isfinite(created_at)
            ):
                raise OptimizationDomainError(
                    "evidence_tampered", "Start boundary is invalid.", status=500
                )
            boundary = existing
        else:
            boundary = {**boundary_base, "createdAt": self._now()}
        boundary_digest = self._write_immutable_document(
            session["workspaceRef"], boundary_ref, boundary
        )
        operation = {
            "operationId": operation_id,
            "roundId": round_spec["roundId"],
            "attempt": attempt,
            "boundaryRef": boundary_ref,
            "boundaryDocumentSha256": boundary_digest,
            "recoveryRequired": True,
            "safeBeforeStartRetry": False,
            "notStartedProofSha256": None,
            "receipt": None,
            "handlerInvocation": None,
            "executionIdentity": (
                copy.deepcopy(dict(execution_identity))
                if execution_identity is not None
                else None
            ),
            "executionStopProof": None,
        }
        session["currentOperation"] = operation
        session["state"] = "running"
        session["updatedAt"] = self._now()
        session["heartbeatAt"] = session["updatedAt"]
        event = self._event(
            session,
            "start_boundary_committed",
            session["updatedAt"],
            operationId=operation_id,
            roundId=round_spec["roundId"],
            attempt=attempt,
        )
        # This durable save is the exact boundary before the handler may press Start.
        self._save_unlocked(store)
        try:
            self._audit(event)
        except OptimizationDomainError as error:
            if error.code != "audit_callback_failed":
                raise
            self._rollback_undispatched_operation_after_audit_failure(
                store,
                session,
                operation,
                failed_event_type="start_boundary_committed",
            )
            raise
        return operation, round_spec

    def _handler_request(
        self,
        session: Mapping[str, Any],
        action: str,
    ) -> dict[str, Any]:
        operation = session["currentOperation"]
        if not isinstance(operation, dict):
            raise OptimizationDomainError(
                "state_invalid", "Optimization operation is missing.", status=500
            )
        round_spec = session["request"]["rounds"][session["roundIndex"]]
        receipt = operation.get("receipt")
        request = {
            "schemaVersion": SCHEMA_VERSION,
            "action": action,
            "sessionId": session["id"],
            "buildId": session["buildId"],
            "sourceDigest": session["sourceDigest"],
            "baselineReportSha256": session["baselineReportSha256"],
            "requestDigest": session["requestDigest"],
            "platform": session["platform"],
            "terminalBinding": copy.deepcopy(session["terminalBinding"]),
            "workspaceRef": session["workspaceRef"],
            "round": copy.deepcopy(round_spec),
            "testerSettings": copy.deepcopy(session["request"]["testerSettings"]),
            "operation": {
                "operationId": operation["operationId"],
                "attempt": operation["attempt"],
                "boundaryRef": operation["boundaryRef"],
                "boundaryDocumentSha256": operation["boundaryDocumentSha256"],
                "receiptRef": receipt["receiptRef"] if isinstance(receipt, dict) else None,
                "receiptDocumentSha256": (
                    receipt["documentSha256"] if isinstance(receipt, dict) else None
                ),
            },
            "safety": {
                "startAllowed": action == "start_round",
                "startExactlyOnce": True,
                "neverStart": action != "start_round",
                "liveTradingAllowed": False,
                "closeTerminalAllowed": False,
                "testShutdownTerminal": False,
            },
            "deadlineAt": session["deadlineAt"],
        }
        if "riskThresholds" in session["request"]:
            request["riskThresholds"] = copy.deepcopy(
                session["request"]["riskThresholds"]
            )
        _reject_forbidden_keys(
            {key: value for key, value in request.items() if key not in {"sourceDigest"}},
            field="handlerRequest",
        )
        return request

    def _invoke_handler(self, request: Mapping[str, Any]) -> Any:
        """Invoke the potentially long-running adapter without holding state locks."""

        return self._handler(copy.deepcopy(dict(request)))

    def _validate_handler_result_shape(self, raw: Any) -> dict[str, Any]:
        try:
            encoded = _canonical_bytes(raw)
        except (TypeError, ValueError) as error:
            raise OptimizationDomainError(
                "handler_result_invalid",
                "Visible optimization adapter returned non-JSON data.",
                status=502,
            ) from error
        if len(encoded) > MAX_HANDLER_RESULT_BYTES:
            raise OptimizationDomainError(
                "handler_result_too_large",
                "Visible optimization result exceeded its size limit.",
                status=502,
            )
        if not isinstance(raw, dict):
            raise OptimizationDomainError(
                "handler_result_invalid",
                "Visible optimization adapter returned an invalid result.",
                status=502,
            )
        _reject_forbidden_keys(raw, field="handlerResult")
        return raw

    def _validate_receipt(
        self, session: Mapping[str, Any], raw: Any
    ) -> tuple[dict[str, Any], str, str]:
        row = _exact_keys(
            raw,
            field="receipt",
            required={
                "schemaVersion",
                "operationId",
                "roundId",
                "receiptRef",
                "startBoundarySha256",
                "platform",
                "terminalCandidateId",
                "terminalSelectionRevision",
                "terminalBindingDigest",
                "startedAt",
            },
        )
        operation = session["currentOperation"]
        binding = session["terminalBinding"]
        receipt_ref = _opaque_ref(row["receiptRef"], field="receipt.receiptRef")
        expected_ref = "receipt_" + operation["operationId"][3:]
        if row["schemaVersion"] != SCHEMA_VERSION or receipt_ref != expected_ref:
            raise OptimizationDomainError(
                "receipt_invalid", "Optimization receipt identity is invalid.", status=502
            )
        if (
            row["operationId"] != operation["operationId"]
            or row["roundId"] != operation["roundId"]
            or row["startBoundarySha256"] != operation["boundaryDocumentSha256"]
            or row["platform"] != session["platform"]
            or row["terminalCandidateId"] != binding["candidateId"]
            or row["terminalSelectionRevision"] != binding["selectionRevision"]
            or row["terminalBindingDigest"] != binding["bindingDigest"]
        ):
            raise OptimizationDomainError(
                "receipt_binding_mismatch",
                "Optimization receipt is bound to a different operation or terminal.",
                status=409,
            )
        started_at = row["startedAt"]
        if isinstance(started_at, bool) or not isinstance(started_at, (int, float)) or not math.isfinite(started_at):
            raise OptimizationDomainError(
                "receipt_invalid", "Optimization receipt timestamp is invalid.", status=502
            )
        normalized = copy.deepcopy(row)
        digest = self._write_immutable_document(
            session["workspaceRef"], receipt_ref, normalized
        )
        return normalized, receipt_ref, digest

    def _attach_receipt(self, session: dict[str, Any], raw: Any) -> None:
        receipt, document_ref, digest = self._validate_receipt(session, raw)
        operation = session["currentOperation"]
        existing = operation.get("receipt")
        summary = {
            "receiptRef": receipt["receiptRef"],
            "startedAt": receipt["startedAt"],
            "documentRef": document_ref,
            "documentSha256": digest,
        }
        if existing is not None and existing != summary:
            raise OptimizationDomainError(
                "receipt_tampered", "Optimization receipt changed after publication.", status=409
            )
        operation["receipt"] = summary
        operation["recoveryRequired"] = False
        operation["safeBeforeStartRetry"] = False

    def _normalize_result_row(self, raw: Any, *, index: int) -> dict[str, Any]:
        if not isinstance(raw, dict) or not raw or len(raw) > MAX_RESULT_ROW_FIELDS:
            raise OptimizationDomainError(
                "optimization_result_invalid",
                f"resultRows[{index}] is invalid.",
                status=502,
            )
        result: dict[str, Any] = {}
        for key, value in raw.items():
            name = _identifier(key, field=f"resultRows[{index}].key", pattern=_INPUT_NAME_RE)
            if isinstance(value, float):
                if not math.isfinite(value):
                    raise OptimizationDomainError(
                        "optimization_result_invalid",
                        f"resultRows[{index}].{name} must be finite.",
                        status=502,
                    )
                result[name] = value
            elif isinstance(value, str):
                # Preserve an empty native report cell as explicit unavailable
                # data.  Do not coerce it to zero: downstream analysis already
                # treats non-numeric metrics as unavailable and fails closed.
                result[name] = _safe_text(
                    value,
                    field=f"resultRows[{index}].{name}",
                    maximum=128,
                    allow_empty=True,
                )
            else:
                result[name] = _normalize_scalar(
                    value, field=f"resultRows[{index}].{name}"
                )
        return result

    @staticmethod
    def _analysis_number(row: Mapping[str, Any], *aliases: str) -> float | None:
        """Read one explicit finite metric without deriving a replacement."""

        values: list[float] = []
        for alias in aliases:
            if alias not in row:
                continue
            value = row.get(alias)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
            number = float(value)
            if not math.isfinite(number):
                return None
            values.append(number)
        if not values:
            return None
        # Multiple MT5 report aliases are allowed only when they agree.  Taking
        # the first value would make a conflicting report column silently win.
        if any(value != values[0] for value in values[1:]):
            return None
        return values[0]

    @staticmethod
    def _analysis_scalar_id(row: Mapping[str, Any], index: int) -> Any:
        for alias in ("passNumber", "pass", "id"):
            value = row.get(alias)
            if isinstance(value, str) and value.strip():
                return value
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return value
            if (
                isinstance(value, float)
                and math.isfinite(value)
                and value >= 0
                and value.is_integer()
            ):
                return value
        return None

    def _analysis_candidate(
        self,
        row: Mapping[str, Any],
        *,
        index: int,
        ranges: Sequence[Mapping[str, Any]],
        initial_deposit: float | None,
    ) -> dict[str, Any]:
        parameters = {
            str(item["name"]): copy.deepcopy(row.get(str(item["name"])))
            for item in ranges
            if str(item["name"]) in row
        }
        stability = self._analysis_number(
            row, "stability", "stabilityScore", "sharpeRatio"
        )
        stability_metric = (
            "stability"
            if self._analysis_number(row, "stability") is not None
            else "stabilityScore"
            if self._analysis_number(row, "stabilityScore") is not None
            else "sharpeRatio"
            if self._analysis_number(row, "sharpeRatio") is not None
            else None
        )
        net_profit = self._analysis_number(row, "profit", "netProfit")
        return {
            "pass": self._analysis_scalar_id(row, index),
            "netProfit": net_profit,
            "profitPercent": (
                (net_profit / initial_deposit) * 100
                if net_profit is not None and initial_deposit is not None
                else None
            ),
            "drawdownPercent": self._analysis_number(
                row,
                "drawdownPercent",
                "equityDrawdownPercent",
                "maxDrawdownPercent",
            ),
            "trades": self._analysis_number(row, "trades", "tradeCount"),
            "profitFactor": self._analysis_number(row, "profitFactor"),
            "stability": stability,
            "stabilityMetric": stability_metric,
            "parameters": parameters,
        }

    def _build_round_analysis(
        self,
        session: Mapping[str, Any],
        result: Mapping[str, Any],
        verified: Mapping[str, Any],
        *,
        analysis_policy_version: int = ANALYSIS_POLICY_VERSION,
    ) -> dict[str, Any]:
        """Deterministically analyze only the exact hash-verified full row set."""

        if analysis_policy_version not in {1, ANALYSIS_POLICY_VERSION}:
            raise OptimizationDomainError(
                "analysis_tampered",
                "Optimization analysis policy version is unsupported.",
                status=500,
            )

        rows = verified["resultRows"]
        ranges = session["request"]["rounds"][result["roundIndex"]]["ranges"]
        thresholds = copy.deepcopy(
            session["request"].get("riskThresholds")
            or {
                "targetProfitPercent": None,
                "maxDrawdownPercent": None,
                "minimumTrades": None,
            }
        )
        initial_deposit_raw = verified.get("initialDeposit", result.get("initialDeposit"))
        initial_deposit = (
            float(initial_deposit_raw)
            if not isinstance(initial_deposit_raw, bool)
            and isinstance(initial_deposit_raw, (int, float))
            and math.isfinite(float(initial_deposit_raw))
            and float(initial_deposit_raw) > 0
            else None
        )
        base = {
            "schemaVersion": SCHEMA_VERSION,
            "kind": "optimization_round_analysis",
            "sessionId": session["id"],
            "roundId": result["roundId"],
            "requestDigest": session["requestDigest"],
            "sourceResultDocumentSha256": result["documentSha256"],
            "sourceResultRowsSha256": _sha256_json(rows),
            "passCount": result["passCount"],
            "returnedPassCount": result["returnedPassCount"],
            "rowsTruncated": result["rowsTruncated"],
            "riskThresholds": thresholds,
            "initialDeposit": initial_deposit,
            "currentBands": copy.deepcopy(ranges),
        }
        if analysis_policy_version >= 2:
            base["analysisPolicyVersion"] = ANALYSIS_POLICY_VERSION

        def unavailable(*reasons: str, profitable_pass_count: int | None = None):
            unique_reasons = list(dict.fromkeys(reason for reason in reasons if reason))
            return {
                **base,
                "status": "unavailable",
                "reasonCode": unique_reasons[0] if unique_reasons else "analysis_unavailable",
                "unavailableReasons": unique_reasons or ["analysis_unavailable"],
                "profitablePassCount": profitable_pass_count,
                "eligiblePassCount": None,
                "candidateGroups": {
                    "maxProfit": [],
                    "lowestDrawdown": [],
                    "mostStable": [],
                },
                "nextParameterPlan": [],
                "nextParameterPlanAvailable": False,
                "nextParameterPlanReasonCode": (
                    unique_reasons[0] if unique_reasons else "analysis_unavailable"
                ),
            }

        if (
            result["rowsTruncated"] is True
            or result["returnedPassCount"] != result["passCount"]
            or len(rows) != result["passCount"]
        ):
            return unavailable("verified_result_rows_truncated")

        scalar_pass_ids = [
            self._analysis_scalar_id(row, index) for index, row in enumerate(rows)
        ]
        pass_ids = [_canonical_bytes(value) for value in scalar_pass_ids]
        if any(value is None for value in scalar_pass_ids) or len(set(pass_ids)) != len(pass_ids):
            return unavailable("pass_identity_invalid")

        # Every optimized value must still belong to the immutable declared
        # search grid.  Candidate grouping and a next plan are unsafe if a
        # report row cannot be joined back to that exact grid.
        for item in ranges:
            name = str(item["name"])
            if any(name not in row for row in rows):
                return unavailable("optimized_parameter_metric_missing")
            values = [row[name] for row in rows]
            if item["kind"] == "numeric":
                if any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    for value in values
                ):
                    return unavailable("optimized_parameter_metric_invalid")
                start = Decimal(item["start"])
                step = Decimal(item["step"])
                stop = Decimal(item["stop"])
                for value in values:
                    numeric_value = Decimal(str(value))
                    if (
                        numeric_value < start
                        or numeric_value > stop
                        or (numeric_value - start) % step != 0
                    ):
                        return unavailable("optimized_parameter_value_out_of_range")
            else:
                allowed = {_canonical_bytes(value) for value in item["values"]}
                if any(_canonical_bytes(value) not in allowed for value in values):
                    return unavailable("optimized_parameter_value_out_of_range")

        profits = [
            self._analysis_number(row, "profit", "netProfit") for row in rows
        ]
        if any(value is None for value in profits):
            return unavailable("profit_metric_missing")
        profitable_pass_count = sum(1 for value in profits if value is not None and value > 0)

        profit_percentages = [
            ((float(value) / initial_deposit) * 100 if initial_deposit is not None else None)
            for value in profits
        ]
        drawdowns = [
            self._analysis_number(
                row,
                "drawdownPercent",
                "equityDrawdownPercent",
                "maxDrawdownPercent",
            )
            for row in rows
        ]
        trades = [self._analysis_number(row, "trades", "tradeCount") for row in rows]
        reasons: list[str] = []
        if analysis_policy_version >= 2 and any(
            value is None or value < 0 or not value.is_integer() for value in trades
        ):
            reasons.append("trades_metric_missing_or_invalid")
        if thresholds["targetProfitPercent"] is not None and any(
            value is None for value in profit_percentages
        ):
            reasons.append("initial_deposit_missing_for_target_profit_percent")
        if thresholds["maxDrawdownPercent"] is not None:
            if any(value is None for value in drawdowns):
                reasons.append("drawdown_percent_metric_missing")
            elif any(value < 0 or value > 100 for value in drawdowns):
                reasons.append("drawdown_percent_metric_invalid")
        if (
            analysis_policy_version == 1
            and thresholds["minimumTrades"] is not None
            and any(
                value is None or value < 0 or not value.is_integer()
                for value in trades
            )
        ):
            reasons.append("trades_metric_missing_or_invalid")
        if reasons:
            return unavailable(*reasons, profitable_pass_count=profitable_pass_count)
        if analysis_policy_version >= 2 and all(value == 0 for value in trades):
            # A zero-trade Tester result proves that MT5 completed the run, but
            # it contains no strategy-performance evidence.  Never rank such
            # rows or recommend another parameter band as if they were viable.
            return unavailable(
                "backtest_zero_trades",
                profitable_pass_count=profitable_pass_count,
            )

        eligible_indices: list[int] = []
        for index in range(len(rows)):
            # Mixed reports may contain dormant parameter combinations.  They
            # remain immutable evidence, but cannot become candidates or drive
            # the next optimization plan without at least one executed trade.
            if analysis_policy_version >= 2 and trades[index] <= 0:
                continue
            if (
                thresholds["targetProfitPercent"] is not None
                and profit_percentages[index] < thresholds["targetProfitPercent"]
            ):
                continue
            if (
                thresholds["maxDrawdownPercent"] is not None
                and drawdowns[index] > thresholds["maxDrawdownPercent"]
            ):
                continue
            if (
                thresholds["minimumTrades"] is not None
                and trades[index] < thresholds["minimumTrades"]
            ):
                continue
            eligible_indices.append(index)

        candidates = {
            index: self._analysis_candidate(
                rows[index],
                index=index,
                ranges=ranges,
                initial_deposit=initial_deposit,
            )
            for index in eligible_indices
        }
        if eligible_indices:
            if any(drawdowns[index] is None for index in eligible_indices):
                reasons.append("candidate_drawdown_metric_missing")
            elif any(
                drawdowns[index] < 0 or drawdowns[index] > 100
                for index in eligible_indices
            ):
                reasons.append("candidate_drawdown_metric_invalid")
            stabilities = {
                index: self._analysis_number(
                    rows[index], "stability", "stabilityScore", "sharpeRatio"
                )
                for index in eligible_indices
            }
            if any(value is None for value in stabilities.values()):
                reasons.append("candidate_stability_metric_missing")
            if reasons:
                return unavailable(*reasons, profitable_pass_count=profitable_pass_count)
        else:
            stabilities = {}

        max_profit_indices = sorted(
            eligible_indices,
            key=lambda index: (-float(profits[index]), index),
        )[:MAX_ANALYSIS_CANDIDATES_PER_GROUP]
        lowest_drawdown_indices = sorted(
            eligible_indices,
            key=lambda index: (float(drawdowns[index]), -float(profits[index]), index),
        )[:MAX_ANALYSIS_CANDIDATES_PER_GROUP]
        most_stable_indices = sorted(
            eligible_indices,
            key=lambda index: (
                -float(stabilities[index]),
                -float(profits[index]),
                index,
            ),
        )[:MAX_ANALYSIS_CANDIDATES_PER_GROUP]
        candidate_groups = {
            "maxProfit": [copy.deepcopy(candidates[index]) for index in max_profit_indices],
            "lowestDrawdown": [
                copy.deepcopy(candidates[index]) for index in lowest_drawdown_indices
            ],
            "mostStable": [
                copy.deepcopy(candidates[index]) for index in most_stable_indices
            ],
        }

        next_plan: list[dict[str, Any]] = []
        next_plan_reason = None
        if not eligible_indices:
            next_plan_reason = "no_passes_meet_risk_thresholds"
        else:
            for item in ranges:
                name = str(item["name"])
                values = [rows[index][name] for index in eligible_indices]
                if item["kind"] == "numeric":
                    next_plan.append({
                        "name": name,
                        "kind": "numeric",
                        "start": min(float(value) for value in values),
                        "step": item["step"],
                        "stop": max(float(value) for value in values),
                        "reason": "Range of verified passes that meet every risk threshold.",
                    })
                else:
                    unique_values = {
                        _canonical_bytes(value): copy.deepcopy(value) for value in values
                    }
                    next_plan.append({
                        "name": name,
                        "kind": "categorical",
                        "values": [
                            unique_values[key] for key in sorted(unique_values)
                        ],
                        "reason": "Values from verified passes that meet every risk threshold.",
                    })

        return {
            **base,
            "status": "available",
            "reasonCode": None,
            "unavailableReasons": [],
            "profitablePassCount": profitable_pass_count,
            "eligiblePassCount": len(eligible_indices),
            "candidateGroups": candidate_groups,
            "nextParameterPlan": next_plan,
            "nextParameterPlanAvailable": next_plan_reason is None,
            "nextParameterPlanReasonCode": next_plan_reason,
        }

    def _store_round_analysis(
        self,
        session: Mapping[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        verified = self._verified_result_document(session, result)
        analysis = self._build_round_analysis(session, result, verified)
        analysis_ref = "analysis_" + str(result["roundId"]).replace("-", "_")
        analysis_digest = self._write_immutable_document(
            session["workspaceRef"], analysis_ref, analysis
        )
        existing_ref = result.get("analysisRef")
        existing_digest = result.get("analysisSha256")
        if (
            (existing_ref is not None and existing_ref != analysis_ref)
            or (existing_digest is not None and existing_digest != analysis_digest)
        ):
            raise OptimizationDomainError(
                "analysis_tampered",
                "Optimization analysis changed after publication.",
                status=409,
            )
        result["analysisRef"] = analysis_ref
        result["analysisSha256"] = analysis_digest
        result["analyzed"] = True
        return analysis

    def _artifact(self, raw: Any, *, field: str) -> dict[str, Any]:
        row = _exact_keys(
            raw,
            field=field,
            required={"ref", "sha256", "byteSize"},
        )
        return {
            "ref": _opaque_ref(row["ref"], field=f"{field}.ref"),
            "sha256": _sha256(row["sha256"], field=f"{field}.sha256"),
            "byteSize": _positive_int(
                row["byteSize"], field=f"{field}.byteSize", maximum=2**40
            ),
        }

    def _validate_evidence(self, session: Mapping[str, Any], raw: Any) -> dict[str, Any]:
        row = _exact_keys(
            raw,
            field="evidence",
            required={
                "schemaVersion",
                "operationId",
                "roundId",
                "receiptRef",
                "platform",
                "terminalCandidateId",
                "terminalSelectionRevision",
                "terminalBindingDigest",
                "passCount",
                "returnedPassCount",
                "rowsTruncated",
                "resultRows",
                "report",
                "manifest",
                "testerSettingsSha256",
                "visibleEvidenceSha256",
                "initialDeposit",
                "testShutdownTerminal",
                "liveTrading",
                "warnings",
            },
        )
        operation = session["currentOperation"]
        receipt = operation.get("receipt")
        binding = session["terminalBinding"]
        if not isinstance(receipt, dict):
            raise OptimizationDomainError(
                "receipt_required", "Completed evidence requires a Start receipt.", status=502
            )
        if row["schemaVersion"] != SCHEMA_VERSION:
            raise OptimizationDomainError(
                "optimization_result_invalid", "Evidence version is invalid.", status=502
            )
        if (
            row["operationId"] != operation["operationId"]
            or row["roundId"] != operation["roundId"]
            or row["receiptRef"] != receipt["receiptRef"]
            or row["platform"] != session["platform"]
            or row["terminalCandidateId"] != binding["candidateId"]
            or row["terminalSelectionRevision"] != binding["selectionRevision"]
            or row["terminalBindingDigest"] != binding["bindingDigest"]
        ):
            raise OptimizationDomainError(
                "evidence_binding_mismatch",
                "Optimization evidence is bound to a different operation or terminal.",
                status=409,
            )
        if row["testShutdownTerminal"] is not False or row["liveTrading"] is not False:
            raise OptimizationDomainError(
                "unsafe_optimization_evidence",
                "Optimization evidence attempted to enable trading or close MetaTrader.",
                status=409,
            )
        initial_deposit = row["initialDeposit"]
        if (
            isinstance(initial_deposit, bool)
            or not isinstance(initial_deposit, (int, float))
            or not math.isfinite(float(initial_deposit))
            or not 0 < float(initial_deposit) <= 1_000_000_000
        ):
            raise OptimizationDomainError(
                "optimization_result_invalid",
                "Evidence initial deposit is invalid.",
                status=502,
            )
        expected_combinations = session["request"]["rounds"][session["roundIndex"]][
            "combinationCount"
        ]
        if row["passCount"] == 0 or row["returnedPassCount"] == 0:
            raise OptimizationDomainError(
                "optimization_zero_pass",
                "A completed optimization must contain at least one verified pass.",
                status=502,
            )
        pass_count = _positive_int(
            row["passCount"], field="evidence.passCount", maximum=expected_combinations
        )
        returned = _positive_int(
            row["returnedPassCount"],
            field="evidence.returnedPassCount",
            maximum=min(pass_count, MAX_RESULT_ROWS),
        )
        if not isinstance(row["rowsTruncated"], bool):
            raise OptimizationDomainError(
                "optimization_result_invalid", "rowsTruncated must be boolean.", status=502
            )
        rows = row["resultRows"]
        if not isinstance(rows, list) or len(rows) != returned:
            raise OptimizationDomainError(
                "optimization_result_invalid",
                "returnedPassCount must match the returned result rows.",
                status=502,
            )
        if pass_count < 2:
            raise OptimizationDomainError(
                "optimization_insufficient_passes",
                "A completed optimization must contain at least two verified passes.",
                status=502,
            )
        truncated_required = returned < pass_count
        if row["rowsTruncated"] != truncated_required:
            raise OptimizationDomainError(
                "optimization_truncation_invalid",
                "rowsTruncated does not match passCount and returnedPassCount.",
                status=502,
            )
        normalized_rows = [
            self._normalize_result_row(item, index=index) for index, item in enumerate(rows)
        ]
        warnings = row["warnings"]
        if not isinstance(warnings, list) or len(warnings) > MAX_WARNINGS:
            raise OptimizationDomainError(
                "optimization_result_invalid", "Evidence warnings are invalid.", status=502
            )
        normalized_warnings = [
            _safe_text(item, field=f"evidence.warnings[{index}]", maximum=256)
            for index, item in enumerate(warnings)
        ]
        tester_settings_digest = _sha256(
            row["testerSettingsSha256"], field="evidence.testerSettingsSha256"
        )
        if tester_settings_digest != _sha256_json(
            session["request"]["testerSettings"]
        ):
            raise OptimizationDomainError(
                "tester_settings_mismatch",
                "Optimization evidence used different tester settings.",
                status=409,
            )
        return {
            "schemaVersion": SCHEMA_VERSION,
            "kind": "optimization_round_result",
            "sessionId": session["id"],
            "operationId": operation["operationId"],
            "roundId": operation["roundId"],
            "receiptRef": receipt["receiptRef"],
            "platform": session["platform"],
            "terminalCandidateId": binding["candidateId"],
            "terminalSelectionRevision": binding["selectionRevision"],
            "terminalBindingDigest": binding["bindingDigest"],
            "passCount": pass_count,
            "returnedPassCount": returned,
            "rowsTruncated": row["rowsTruncated"],
            "resultRows": normalized_rows,
            "report": self._artifact(row["report"], field="evidence.report"),
            "manifest": self._artifact(row["manifest"], field="evidence.manifest"),
            "testerSettingsSha256": tester_settings_digest,
            "visibleEvidenceSha256": _sha256(
                row["visibleEvidenceSha256"], field="evidence.visibleEvidenceSha256"
            ),
            "initialDeposit": float(initial_deposit),
            "testShutdownTerminal": False,
            "liveTrading": False,
            "warnings": normalized_warnings,
        }

    def _accept_evidence(
        self, store: dict[str, Any], session: dict[str, Any], raw: Any
    ) -> None:
        try:
            evidence = self._validate_evidence(session, raw)
        except OptimizationDomainError as error:
            raise self._fail_session(
                store,
                session,
                code=error.code,
                message=str(error),
                status=error.status,
            ) from error
        round_id = evidence["roundId"]
        existing = next(
            (item for item in session["roundResults"] if item["roundId"] == round_id),
            None,
        )
        document_ref = "result_" + round_id.replace("-", "_")
        document_digest = self._write_immutable_document(
            session["workspaceRef"], document_ref, evidence
        )
        summary = {
            "roundId": round_id,
            "roundIndex": session["roundIndex"],
            "combinationCount": session["request"]["rounds"][session["roundIndex"]][
                "combinationCount"
            ],
            "passCount": evidence["passCount"],
            "returnedPassCount": evidence["returnedPassCount"],
            "rowsTruncated": evidence["rowsTruncated"],
            "report": copy.deepcopy(evidence["report"]),
            "manifest": copy.deepcopy(evidence["manifest"]),
            "testerSettingsSha256": evidence["testerSettingsSha256"],
            "visibleEvidenceSha256": evidence["visibleEvidenceSha256"],
            "initialDeposit": evidence["initialDeposit"],
            "warnings": copy.deepcopy(evidence["warnings"]),
            "documentRef": document_ref,
            "documentSha256": document_digest,
            "analyzed": False,
        }
        if existing is not None:
            comparable_existing = {
                key: existing.get(key)
                for key in summary
                if key != "analyzed"
            }
            comparable_summary = {
                key: value for key, value in summary.items() if key != "analyzed"
            }
            if comparable_existing != comparable_summary:
                raise self._fail_session(
                    store,
                    session,
                    code="evidence_tampered",
                    message="Optimization evidence changed after publication.",
                )
        else:
            session["roundResults"].append(summary)
        session["progress"] = {
            "roundNumber": session["roundIndex"] + 1,
            "roundCount": session["roundCount"],
            "passCount": evidence["passCount"],
            "returnedPassCount": evidence["returnedPassCount"],
            "percent": 100.0,
            "rowsTruncated": evidence["rowsTruncated"],
        }
        session["stage"] = "verify_report"
        session["state"] = "running"
        session["updatedAt"] = self._now()
        session["heartbeatAt"] = session["updatedAt"]

    def _safe_before_start(
        self,
        store: dict[str, Any],
        session: dict[str, Any],
        result: Mapping[str, Any],
    ) -> None:
        row = _exact_keys(
            dict(result),
            field="handlerResult",
            required={"status", "notStartedProofSha256"},
            optional={"reasonCode"},
        )
        proof = _sha256(row["notStartedProofSha256"], field="notStartedProofSha256")
        operation = session["currentOperation"]
        operation["safeBeforeStartRetry"] = True
        operation["recoveryRequired"] = False
        operation["notStartedProofSha256"] = proof
        session["state"] = "awaiting_visible_terminal"
        session["updatedAt"] = self._now()
        session["heartbeatAt"] = session["updatedAt"]
        event = self._event(
            session,
            "before_start_retry_allowed",
            session["updatedAt"],
            operationId=operation["operationId"],
            reasonCode=row.get("reasonCode"),
        )
        self._save_unlocked(store)
        self._audit(event)

    def _process_handler_result(
        self,
        store: dict[str, Any],
        session: dict[str, Any],
        action: str,
        result: dict[str, Any],
    ) -> None:
        status = result.get("status")
        if not isinstance(status, str):
            raise self._fail_session(
                store,
                session,
                code="handler_result_invalid",
                message="Visible optimization adapter omitted its status.",
                status=502,
            )
        if status in {"before_start_retryable", "not_started"}:
            if action == "collect_round":
                raise self._fail_session(
                    store,
                    session,
                    code="handler_result_invalid",
                    message="Collection cannot return a before-Start result.",
                    status=502,
                )
            self._safe_before_start(store, session, result)
            if session["cancelRequested"]:
                now = self._now()
                session["state"] = "cancelled"
                session["updatedAt"] = now
                event = self._event(session, "session_cancelled", now)
                self._save_unlocked(store)
                self._audit(event)
            return
        if status == "unknown":
            _exact_keys(result, field="handlerResult", required={"status"}, optional={"reasonCode"})
            session["state"] = "awaiting_visible_terminal"
            session["currentOperation"]["recoveryRequired"] = True
            session["updatedAt"] = self._now()
            session["heartbeatAt"] = session["updatedAt"]
            event = self._event(
                session,
                "receipt_recovery_pending",
                session["updatedAt"],
                operationId=session["currentOperation"]["operationId"],
            )
            self._save_unlocked(store)
            self._audit(event)
            return
        if status == "failed":
            row = _exact_keys(
                result,
                field="handlerResult",
                required={"status", "reasonCode"},
                optional={"receipt"},
            )
            if "receipt" in row:
                self._attach_receipt(session, row["receipt"])
            reason = _identifier(row["reasonCode"], field="handlerResult.reasonCode")
            raise self._fail_session(
                store,
                session,
                code=reason,
                message="Visible optimization adapter reported a failure.",
            )
        if status not in {"started", "in_progress", "completed"}:
            raise self._fail_session(
                store,
                session,
                code="handler_result_invalid",
                message="Visible optimization adapter returned an unsupported status.",
                status=502,
            )
        required = {"status", "receipt"}
        optional = {"progressPercent", "passCount", "evidence"}
        row = _exact_keys(result, field="handlerResult", required=required, optional=optional)
        try:
            self._attach_receipt(session, row["receipt"])
        except OptimizationDomainError as error:
            raise self._fail_session(
                store,
                session,
                code=error.code,
                message=str(error),
                status=error.status,
            ) from error
        if status == "completed":
            if "evidence" not in row:
                raise self._fail_session(
                    store,
                    session,
                    code="completed_evidence_required",
                    message="Completed optimization requires verified evidence.",
                    status=502,
                )
            self._accept_evidence(store, session, row["evidence"])
        else:
            if "evidence" in row:
                raise self._fail_session(
                    store,
                    session,
                    code="handler_result_invalid",
                    message="Incomplete optimization cannot publish final evidence.",
                    status=502,
                )
            percent = row.get("progressPercent", 0.0)
            if (
                isinstance(percent, bool)
                or not isinstance(percent, (int, float))
                or not math.isfinite(float(percent))
                or not 0 <= float(percent) < 100
            ):
                raise self._fail_session(
                    store,
                    session,
                    code="handler_result_invalid",
                    message="Optimization progress is invalid.",
                    status=502,
                )
            pass_count = row.get("passCount", 0)
            if isinstance(pass_count, bool) or not isinstance(pass_count, int) or pass_count < 0:
                raise self._fail_session(
                    store,
                    session,
                    code="handler_result_invalid",
                    message="Optimization pass count is invalid.",
                    status=502,
                )
            combinations = session["request"]["rounds"][session["roundIndex"]][
                "combinationCount"
            ]
            if pass_count > combinations:
                raise self._fail_session(
                    store,
                    session,
                    code="handler_result_invalid",
                    message="Optimization pass count exceeds the planned combinations.",
                    status=502,
                )
            session["state"] = "collecting"
            session["progress"].update(
                {"passCount": pass_count, "percent": float(percent)}
            )
        now = self._now()
        session["updatedAt"] = now
        session["heartbeatAt"] = now
        event = self._event(
            session,
            "handler_result_recorded",
            now,
            action=action,
            handlerStatus=status,
            operationId=session["currentOperation"]["operationId"],
        )
        self._save_unlocked(store)
        self._audit(event)

    def _keep_execution_quarantined(
        self,
        store: dict[str, Any],
        session: dict[str, Any],
        *,
        code: str,
        message: str,
        status: int = 502,
    ) -> OptimizationDomainError:
        """Record an invalid/ambiguous recovery without releasing the active slot."""

        operation = session.get("currentOperation")
        if isinstance(operation, dict):
            operation["handlerInvocation"] = None
            operation["recoveryRequired"] = True
        session["state"] = (
            "collecting"
            if isinstance(operation, dict)
            and isinstance(operation.get("receipt"), dict)
            else "awaiting_visible_terminal"
        )
        now = self._now()
        session["updatedAt"] = now
        session["heartbeatAt"] = now
        event = self._event(
            session,
            "execution_quarantine_recovery_rejected",
            now,
            reasonCode=code,
        )
        self._save_unlocked(store)
        self._audit(event)
        return OptimizationDomainError(code, message, status=status)

    def _process_execution_quarantine_result(
        self,
        store: dict[str, Any],
        session: dict[str, Any],
        action: str,
        result: dict[str, Any],
    ) -> None:
        """Accept only an identity-exact receipt-only terminal recovery."""

        operation = session.get("currentOperation")
        if not isinstance(operation, dict):
            raise self._keep_execution_quarantined(
                store,
                session,
                code="state_invalid",
                message="Deadline recovery is missing its committed operation.",
                status=500,
            )
        status = result.get("status")
        if not isinstance(status, str):
            raise self._keep_execution_quarantined(
                store,
                session,
                code="handler_result_invalid",
                message="Deadline recovery omitted its status.",
            )
        try:
            if status in {"before_start_retryable", "not_started"}:
                if action == "collect_round" or isinstance(operation.get("receipt"), dict):
                    raise OptimizationDomainError(
                        "handler_result_invalid",
                        "A started optimization cannot later claim it never started.",
                        status=502,
                    )
                row = _exact_keys(
                    result,
                    field="handlerResult",
                    required={"status", "notStartedProofSha256"},
                    optional={"reasonCode"},
                )
                operation["notStartedProofSha256"] = _sha256(
                    row["notStartedProofSha256"], field="notStartedProofSha256"
                )
                operation["safeBeforeStartRetry"] = True
                event = self._finalize_quarantined_failure_record(
                    session, self._now(), proof="not_started"
                )
                self._save_unlocked(store)
                self._audit(event)
                return

            if status == "failed":
                row = _exact_keys(
                    result,
                    field="handlerResult",
                    required={"status", "reasonCode"},
                    optional={"receipt"},
                )
                _identifier(row["reasonCode"], field="handlerResult.reasonCode")
                if "receipt" in row:
                    self._attach_receipt(session, row["receipt"])
                # Adapter failure alone is not proof that MetaTrader stopped.  Keep
                # ownership quarantined and require a later completed/not-started
                # recovery result before a replacement may be admitted.
                operation["recoveryRequired"] = True
                session["state"] = (
                    "collecting"
                    if isinstance(operation.get("receipt"), dict)
                    else "awaiting_visible_terminal"
                )
                now = self._now()
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "execution_quarantine_recovery_pending",
                    now,
                    operationId=operation["operationId"],
                    reasonCode=row["reasonCode"],
                )
                self._save_unlocked(store)
                self._audit(event)
                return

            if status == "completed":
                row = _exact_keys(
                    result,
                    field="handlerResult",
                    required={"status", "receipt", "evidence"},
                )
                self._attach_receipt(session, row["receipt"])
                # A response from the original Start invocation can arrive after
                # the absolute deadline.  It proves terminal state but is not a
                # receipt-only recovery and therefore remains ineligible as a
                # successful result.  Only recover/collect are allowed below;
                # neither action is permitted to press Start.
                if action not in {"recover_round", "collect_round"}:
                    self._validate_evidence(session, row["evidence"])
                    event = self._finalize_quarantined_failure_record(
                        session, self._now(), proof="completed_late_discarded"
                    )
                    self._save_unlocked(store)
                    self._audit(event)
                    return

                # Validate before mutating the terminal outcome.  A stale receipt,
                # changed boundary, different operation/terminal, malformed rows,
                # or conflicting immutable document falls through to the
                # quarantine rejection path below and never becomes success.
                self._validate_evidence(session, row["evidence"])
                if session.get("cancelRequested") is True:
                    operation["handlerInvocation"] = None
                    operation["recoveryRequired"] = False
                    session["state"] = "cancelled"
                    session["failure"] = None
                    now = self._now()
                    session["updatedAt"] = now
                    session["heartbeatAt"] = now
                    event = self._event(
                        session,
                        "execution_quarantine_released",
                        now,
                        operationId=operation["operationId"],
                        reasonCode=session.get("cancelReason") or "user_cancelled",
                        recoveryProof="completed_after_cancel",
                    )
                    self._save_unlocked(store)
                    self._audit(event)
                    return

                self._accept_evidence(store, session, row["evidence"])
                operation["handlerInvocation"] = None
                operation["recoveryRequired"] = False
                session["failure"] = None
                now = self._now()
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "execution_quarantine_completed_accepted",
                    now,
                    operationId=operation["operationId"],
                    recoveryProof="completed_exact_recovery",
                )
                self._save_unlocked(store)
                self._audit(event)
                return

            if status in {"started", "in_progress"}:
                row = _exact_keys(
                    result,
                    field="handlerResult",
                    required={"status", "receipt"},
                    optional={"progressPercent", "passCount"},
                )
                self._attach_receipt(session, row["receipt"])
                percent = row.get("progressPercent", 0.0)
                pass_count = row.get("passCount", 0)
                combinations = session["request"]["rounds"][session["roundIndex"]][
                    "combinationCount"
                ]
                if (
                    isinstance(percent, bool)
                    or not isinstance(percent, (int, float))
                    or not math.isfinite(float(percent))
                    or not 0 <= float(percent) < 100
                    or isinstance(pass_count, bool)
                    or not isinstance(pass_count, int)
                    or not 0 <= pass_count <= combinations
                ):
                    raise OptimizationDomainError(
                        "handler_result_invalid",
                        "Deadline recovery progress is invalid.",
                        status=502,
                    )
                operation["recoveryRequired"] = True
                session["state"] = "collecting"
                session["progress"].update(
                    {"passCount": pass_count, "percent": float(percent)}
                )
                now = self._now()
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "execution_quarantine_recovery_pending",
                    now,
                    operationId=operation["operationId"],
                )
                self._save_unlocked(store)
                self._audit(event)
                return

            if status == "unknown":
                _exact_keys(
                    result,
                    field="handlerResult",
                    required={"status"},
                    optional={"reasonCode"},
                )
                operation["recoveryRequired"] = True
                session["state"] = (
                    "collecting"
                    if isinstance(operation.get("receipt"), dict)
                    else "awaiting_visible_terminal"
                )
                now = self._now()
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "execution_quarantine_recovery_pending",
                    now,
                    operationId=operation["operationId"],
                )
                self._save_unlocked(store)
                self._audit(event)
                return

            raise OptimizationDomainError(
                "handler_result_invalid",
                "Deadline recovery returned an unsupported status.",
                status=502,
            )
        except OptimizationDomainError as error:
            if not self._execution_quarantined(session):
                raise
            raise self._keep_execution_quarantined(
                store,
                session,
                code=error.code,
                message=str(error),
                status=error.status,
            ) from error

    def prepare_late_completed_recovery(self, session_id: str) -> dict[str, Any]:
        """Durably reopen one exact legacy discard without invoking the adapter.

        The bridge uses this bounded transition before restarting the existing
        optimizer worker for an explicit same-key one-click retry.  It performs
        no terminal/UI action; the next ``resume`` can issue only
        ``collect_round``/``recover_round`` for the already committed operation.
        """

        audit_event: dict[str, Any] | None = None
        with self._locked():
            store = self._load_store_unlocked()
            session = self._session(store, session_id)
            other_active = next(
                (
                    item
                    for item in store["sessions"]
                    if item.get("id") != session.get("id")
                    and item.get("state") in ACTIVE_STATES
                ),
                None,
            )
            if isinstance(other_active, dict):
                raise OptimizationDomainError(
                    "optimization_busy",
                    "Another optimization session owns the active slot.",
                    status=409,
                )
            if session["state"] in ACTIVE_STATES and any(
                isinstance(event, dict)
                and event.get("type") == "late_completed_result_revalidation_started"
                and event.get("operationId")
                == (session.get("currentOperation") or {}).get("operationId")
                for event in session.get("eventLog", [])
            ):
                return self._public(session)
            audit_event = self._restore_late_completed_discard_for_revalidation(
                session
            )
            if audit_event is None:
                raise OptimizationDomainError(
                    "late_completed_recovery_not_available",
                    "This optimization session has no exact discarded completion to recover.",
                    status=409,
                )
            self._save_unlocked(store)
            response = self._public(session)
        self._audit(audit_event)
        return response

    def resume(self, session_id: str) -> dict[str, Any]:
        """Advance one durable transition without ever replaying visible Start."""

        events: list[dict[str, Any]] = []
        invocation_work: dict[str, Any] | None = None
        with self._locked():
            store = self._load_store_unlocked()
            now = self._now()
            events.extend(self._expire_active_unlocked(store, now))
            if events:
                store = self._load_store_unlocked()
            session = self._session(store, session_id)
            if session["state"] in TERMINAL_STATES:
                # Legacy terminal-discard repair is deliberately not implicit
                # on the generic optimizer resume surface.  The owning bridge
                # must first prove the exact one-click build/run/session handoff
                # and call ``prepare_late_completed_recovery``.  This prevents a
                # stale standalone request from reopening a published failure.
                response = self._public(session)
                for event in events:
                    self._audit(event)
                return response
            execution_quarantined = self._execution_quarantined(session)
            operation = session.get("currentOperation")
            if (
                execution_quarantined
                and isinstance(operation, dict)
                and isinstance(operation.get("handlerInvocation"), dict)
            ):
                response = self._public(session)
                for event in events:
                    self._audit(event)
                return response
            if execution_quarantined:
                try:
                    binding = self._resolve_exact_target(session["request"])
                except OptimizationDomainError as error:
                    raise self._keep_execution_quarantined(
                        store,
                        session,
                        code="terminal_binding_changed",
                        message=(
                            "The selected MetaTrader terminal changed while execution "
                            "recovery is still required."
                        ),
                        status=error.status,
                    ) from error
                if binding != session["terminalBinding"]:
                    raise self._keep_execution_quarantined(
                        store,
                        session,
                        code="terminal_binding_changed",
                        message=(
                            "The selected MetaTrader terminal changed while execution "
                            "recovery is still required."
                        ),
                        status=409,
                    )
            else:
                self._verify_binding_or_fail(store, session)
            try:
                ready, reason, execution_identity = self._capability(session)
            except OptimizationDomainError as error:
                if error.code == "terminal_binding_changed":
                    if execution_quarantined:
                        raise self._keep_execution_quarantined(
                            store,
                            session,
                            code=error.code,
                            message=str(error),
                            status=error.status,
                        ) from error
                    raise self._fail_session(
                        store,
                        session,
                        code=error.code,
                        message=str(error),
                    ) from error
                raise
            if not ready:
                session["state"] = "awaiting_visible_terminal"
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "visible_terminal_unavailable",
                    now,
                    reasonCode=reason or "visible_terminal_not_ready",
                )
                self._save_unlocked(store)
                self._audit(event)
                return self._public(session)

            if session["stage"] == "validate_baseline":
                session["state"] = "running"
                session["stage"] = "prepare_ranges"
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(session, "baseline_validated", now)
                self._save_unlocked(store)
                self._audit(event)
                return self._public(session)

            if session["stage"] == "prepare_ranges":
                session["state"] = "running"
                session["stage"] = "run_round"
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "ranges_prepared",
                    now,
                    roundId=session["request"]["rounds"][session["roundIndex"]]["roundId"],
                )
                self._save_unlocked(store)
                self._audit(event)
                return self._public(session)

            if session["stage"] == "run_round":
                operation = session["currentOperation"]
                if execution_quarantined:
                    if not isinstance(operation, dict):
                        raise self._keep_execution_quarantined(
                            store,
                            session,
                            code="state_invalid",
                            message="Deadline recovery is missing its committed operation.",
                            status=500,
                        )
                    if isinstance(operation.get("receipt"), dict):
                        action = "collect_round"
                        session["state"] = "collecting"
                    else:
                        action = "recover_round"
                        session["state"] = "awaiting_visible_terminal"
                elif operation is None or operation.get("safeBeforeStartRetry") is True:
                    if session["cancelRequested"]:
                        session["state"] = "cancelled"
                        session["updatedAt"] = now
                        event = self._event(session, "session_cancelled", now)
                        self._save_unlocked(store)
                        self._audit(event)
                        return self._public(session)
                    operation, _round_spec = self._prepare_start_boundary(
                        store, session, execution_identity
                    )
                    action = "start_round"
                elif isinstance(operation.get("receipt"), dict):
                    action = "collect_round"
                    session["state"] = "collecting"
                else:
                    action = "recover_round"
                    session["state"] = "awaiting_visible_terminal"
                if isinstance(operation.get("handlerInvocation"), dict):
                    response = self._public(session)
                    for event in events:
                        self._audit(event)
                    return response
                invocation_id = "invoke_" + uuid.uuid4().hex
                operation["handlerInvocation"] = {
                    "invocationId": invocation_id,
                    "action": action,
                    "claimedAt": now,
                }
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "handler_invocation_claimed",
                    now,
                    action=action,
                    operationId=operation["operationId"],
                    invocationId=invocation_id,
                )
                self._save_unlocked(store)
                try:
                    self._audit(event)
                except OptimizationDomainError as error:
                    if error.code != "audit_callback_failed":
                        raise
                    self._rollback_undispatched_operation_after_audit_failure(
                        store,
                        session,
                        operation,
                        failed_event_type="handler_invocation_claimed",
                    )
                    raise
                invocation_work = {
                    "sessionId": session["id"],
                    "operationId": operation["operationId"],
                    "invocationId": invocation_id,
                    "action": action,
                    "request": self._handler_request(session, action),
                }

            elif session["stage"] == "verify_report":
                result = next(
                    (
                        item
                        for item in session["roundResults"]
                        if item["roundIndex"] == session["roundIndex"]
                    ),
                    None,
                )
                if result is None:
                    raise self._fail_session(
                        store,
                        session,
                        code="completed_evidence_required",
                        message="Optimization report evidence is missing.",
                    )
                self._read_document(
                    session["workspaceRef"], result["documentRef"], result["documentSha256"]
                )
                if session["cancelRequested"]:
                    session["state"] = "cancelled"
                    session["updatedAt"] = now
                    event = self._event(session, "session_cancelled", now)
                else:
                    session["stage"] = "analyze"
                    session["state"] = "running"
                    session["updatedAt"] = now
                    session["heartbeatAt"] = now
                    event = self._event(
                        session, "report_verified", now, roundId=result["roundId"]
                    )
                self._save_unlocked(store)
                self._audit(event)
                return self._public(session)

            elif session["stage"] == "analyze":
                result = next(
                    item
                    for item in session["roundResults"]
                    if item["roundIndex"] == session["roundIndex"]
                )
                analysis = self._store_round_analysis(session, result)
                session["currentOperation"] = None
                if session["roundIndex"] + 1 < session["roundCount"]:
                    session["roundIndex"] += 1
                    session["stage"] = "prepare_ranges"
                    session["progress"] = {
                        "roundNumber": session["roundIndex"] + 1,
                        "roundCount": session["roundCount"],
                        "passCount": 0,
                        "returnedPassCount": 0,
                        "percent": 0.0,
                        "rowsTruncated": False,
                    }
                else:
                    session["stage"] = "complete"
                session["state"] = "running"
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(
                    session,
                    "round_analyzed",
                    now,
                    roundId=result["roundId"],
                    analysisStatus=analysis["status"],
                    analysisSha256=result["analysisSha256"],
                )
                self._save_unlocked(store)
                self._audit(event)
                return self._public(session)

            elif session["stage"] == "complete":
                if (
                    len(session["roundResults"]) != session["roundCount"]
                    or not all(item["analyzed"] for item in session["roundResults"])
                ):
                    raise self._fail_session(
                        store,
                        session,
                        code="completed_evidence_required",
                        message="Every optimization round requires verified evidence.",
                    )
                session["state"] = "completed"
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                event = self._event(session, "session_completed", now)
                self._save_unlocked(store)
                self._audit(event)
                return self._public(session)

            elif invocation_work is None:
                raise self._fail_session(
                    store,
                    session,
                    code="state_invalid",
                    message="Optimization state cannot be resumed.",
                    status=500,
                )

        for event in events:
            self._audit(event)
        if invocation_work is None:  # pragma: no cover - guarded above
            raise OptimizationDomainError(
                "state_invalid", "Optimization invocation was not prepared.", status=500
            )

        try:
            raw_result = self._invoke_handler(invocation_work["request"])
        except BaseException as error:
            # A process-level interruption deliberately leaves the invocation lease
            # durable. Restart recovery will convert it to receipt-only recovery and
            # therefore can never replay Start.
            if not isinstance(error, Exception):
                raise
            audit_event: dict[str, Any] | None = None
            with self._locked():
                store = self._load_store_unlocked()
                post_error_events = self._expire_active_unlocked(store, self._now())
                if post_error_events:
                    store = self._load_store_unlocked()
                session = self._session(store, invocation_work["sessionId"])
                operation = session.get("currentOperation")
                invocation = (
                    operation.get("handlerInvocation")
                    if isinstance(operation, dict)
                    else None
                )
                if not (
                    isinstance(operation, dict)
                    and operation.get("operationId") == invocation_work["operationId"]
                    and isinstance(invocation, dict)
                    and invocation.get("invocationId") == invocation_work["invocationId"]
                ):
                    response = self._public(session)
                    for event in post_error_events:
                        self._audit(event)
                    return response
                operation["handlerInvocation"] = None
                if session["state"] in TERMINAL_STATES:
                    self._save_unlocked(store)
                    response = self._public(session)
                    for event in post_error_events:
                        self._audit(event)
                    return response
                operation["recoveryRequired"] = True
                operation["safeBeforeStartRetry"] = False
                session["state"] = (
                    "collecting"
                    if isinstance(operation.get("receipt"), dict)
                    else "awaiting_visible_terminal"
                )
                now = self._now()
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                audit_event = self._event(
                    session,
                    "handler_interrupted",
                    now,
                    action=invocation_work["action"],
                    recoveryRequired=True,
                )
                self._save_unlocked(store)
            if audit_event is not None:
                self._audit(audit_event)
            raise OptimizationDomainError(
                "handler_interrupted",
                "The visible optimization adapter was interrupted; receipt recovery is required.",
                status=503,
            ) from error

        with self._locked():
            store = self._load_store_unlocked()
            post_invoke_events = self._expire_active_unlocked(store, self._now())
            if post_invoke_events:
                # In-flight calls are exempt only from the heartbeat lease.  The
                # absolute session deadline remains authoritative, so a late
                # adapter response is never accepted as fresh evidence.
                store = self._load_store_unlocked()
            session = self._session(store, invocation_work["sessionId"])
            operation = session.get("currentOperation")
            invocation = (
                operation.get("handlerInvocation")
                if isinstance(operation, dict)
                else None
            )
            if not (
                isinstance(operation, dict)
                and operation.get("operationId") == invocation_work["operationId"]
                and isinstance(invocation, dict)
                and invocation.get("invocationId") == invocation_work["invocationId"]
            ):
                response = self._public(session)
                for event in post_invoke_events:
                    self._audit(event)
                return response
            operation["handlerInvocation"] = None
            if session["state"] in TERMINAL_STATES:
                self._save_unlocked(store)
                response = self._public(session)
                for event in post_invoke_events:
                    self._audit(event)
                return response
            try:
                result = self._validate_handler_result_shape(raw_result)
            except OptimizationDomainError as error:
                if self._execution_quarantined(session):
                    raise self._keep_execution_quarantined(
                        store,
                        session,
                        code=error.code,
                        message=str(error),
                        status=error.status,
                    ) from error
                raise self._fail_session(
                    store,
                    session,
                    code=error.code,
                    message=str(error),
                    status=error.status,
                ) from error
            try:
                if self._execution_quarantined(session):
                    self._process_execution_quarantine_result(
                        store, session, invocation_work["action"], result
                    )
                else:
                    self._process_handler_result(
                        store, session, invocation_work["action"], result
                    )
            except OptimizationDomainError as error:
                if session["state"] == "failed":
                    raise
                if self._execution_quarantined(session):
                    raise
                raise self._fail_session(
                    store,
                    session,
                    code=error.code,
                    message=str(error),
                    status=error.status,
                ) from error
            response = self._public(session)
            for event in post_invoke_events:
                self._audit(event)
            return response

    def _prove_execution_stopped(
        self, session: Mapping[str, Any], operation: Mapping[str, Any]
    ) -> tuple[dict[str, Any] | None, str]:
        identity = operation.get("executionIdentity")
        if identity is None or self._execution_stop_prover is None:
            return None, "execution_stop_proof_unavailable"
        validated_identity = self._validate_execution_identity(
            identity, session["terminalBinding"]
        )
        request = {
            "schemaVersion": SCHEMA_VERSION,
            "action": "prove_execution_stopped",
            "sessionId": session["id"],
            "operationId": operation["operationId"],
            "terminalBinding": copy.deepcopy(session["terminalBinding"]),
            "executionIdentity": copy.deepcopy(validated_identity),
            "liveTradingAllowed": False,
            "closeTerminalAllowed": False,
            "testShutdownTerminal": False,
        }
        try:
            raw = self._execution_stop_prover(request)
            row = _exact_keys(
                raw,
                field="executionStopProof",
                required={"status", "reasonCode", "observedAt", "identitySha256"},
                optional={"proofSha256"},
            )
            status = _identifier(row["status"], field="executionStopProof.status")
            reason = _identifier(
                row["reasonCode"], field="executionStopProof.reasonCode"
            )
            observed_at = row["observedAt"]
            identity_digest = _sha256(
                row["identitySha256"],
                field="executionStopProof.identitySha256",
            )
            if (
                status not in {
                    "execution_stopped",
                    "execution_still_running",
                    "execution_state_unknown",
                }
                or isinstance(observed_at, bool)
                or not isinstance(observed_at, (int, float))
                or not math.isfinite(float(observed_at))
                or float(observed_at) < 0
                or not secrets.compare_digest(
                    identity_digest, validated_identity["identitySha256"]
                )
            ):
                raise OptimizationDomainError(
                    "execution_stop_proof_invalid",
                    "Execution-stop proof is invalid.",
                    status=502,
                )
            if status != "execution_stopped":
                if row.get("proofSha256") is not None:
                    raise OptimizationDomainError(
                        "execution_stop_proof_invalid",
                        "A non-terminal observation cannot contain release proof.",
                        status=502,
                    )
                return None, reason
            proof_digest = _sha256(
                row.get("proofSha256"),
                field="executionStopProof.proofSha256",
            )
            return {
                "reasonCode": reason,
                "proofSha256": proof_digest,
                "observedAt": float(observed_at),
                "identitySha256": identity_digest,
            }, reason
        except OptimizationDomainError:
            raise
        except Exception as error:
            raise OptimizationDomainError(
                "execution_stop_proof_failed",
                "The Backend could not prove that the original optimization stopped.",
                status=503,
            ) from error

    def cancel(
        self,
        session_id: str,
        *,
        reason: str = "user_cancelled",
        confirm_execution_stopped: bool = False,
    ) -> dict[str, Any]:
        """Cancel safely; release an ambiguous slot only after trusted proof."""

        safe_reason = _identifier(reason, field="cancelReason")
        if not isinstance(confirm_execution_stopped, bool):
            raise OptimizationDomainError(
                "invalid_request", "Cancel confirmation flag is invalid.", status=422
            )
        events: list[dict[str, Any]] = []
        with self._locked():
            store = self._load_store_unlocked()
            now = self._now()
            events.extend(self._expire_active_unlocked(store, now))
            if events:
                store = self._load_store_unlocked()
            session = self._session(store, session_id)
            if session["state"] in TERMINAL_STATES:
                response = self._public(session)
            else:
                operation = session["currentOperation"]
                session["cancelRequested"] = True
                session["cancelReason"] = safe_reason
                if operation is None or operation.get("safeBeforeStartRetry") is True:
                    session["state"] = "cancelled"
                elif isinstance(operation.get("receipt"), dict):
                    session["state"] = "collecting"
                else:
                    session["state"] = "awaiting_visible_terminal"
                    operation["recoveryRequired"] = True
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                events.append(
                    self._event(
                        session,
                        (
                            "cancel_requested"
                            if session["state"] != "cancelled"
                            else "session_cancelled"
                        ),
                        now,
                        reasonCode=safe_reason,
                    )
                )

                if (
                    confirm_execution_stopped
                    and session["state"] in ACTIVE_STATES
                    and isinstance(operation, dict)
                    and operation.get("safeBeforeStartRetry") is not True
                ):
                    try:
                        proof, proof_reason = self._prove_execution_stopped(
                            session, operation
                        )
                    except OptimizationDomainError as error:
                        proof = None
                        proof_reason = error.code
                    proof_now = self._now()
                    session["updatedAt"] = proof_now
                    session["heartbeatAt"] = proof_now
                    if proof is not None:
                        operation["executionStopProof"] = proof
                        operation["handlerInvocation"] = None
                        operation["recoveryRequired"] = False
                        failure = session.get("failure")
                        if isinstance(failure, dict):
                            failure["executionMayStillBeRunning"] = False
                        session["state"] = "cancelled"
                        events.append(
                            self._event(
                                session,
                                "execution_stopped_proven",
                                proof_now,
                                reasonCode=proof_reason,
                                proofSha256=proof["proofSha256"],
                            )
                        )
                    else:
                        events.append(
                            self._event(
                                session,
                                "execution_stop_proof_pending",
                                proof_now,
                                reasonCode=proof_reason,
                            )
                        )
                self._save_unlocked(store)
                response = self._public(session)
        for event in events:
            self._audit(event)
        return response

    def _recover_orphan_documents(
        self, session: dict[str, Any]
    ) -> tuple[bool, list[dict[str, Any]]]:
        operation = session.get("currentOperation")
        if not isinstance(operation, dict):
            return False, []
        changed = False
        events: list[dict[str, Any]] = []
        if not isinstance(operation.get("receipt"), dict):
            receipt_ref = "receipt_" + operation["operationId"][3:]
            path = self._document_path(session["workspaceRef"], receipt_ref)
            if path.exists():
                raw = json.loads(path.read_text(encoding="utf-8"))
                self._attach_receipt(session, raw)
                changed = True
        result_ref = "result_" + operation["roundId"].replace("-", "_")
        result_path = self._document_path(session["workspaceRef"], result_ref)
        if result_path.exists() and not any(
            item["roundId"] == operation["roundId"] for item in session["roundResults"]
        ):
            raw = json.loads(result_path.read_text(encoding="utf-8"))
            handler_evidence = {
                key: value
                for key, value in raw.items()
                if key not in {"kind", "sessionId"}
            }
            evidence = self._validate_evidence(session, handler_evidence)
            if evidence != raw:
                raise OptimizationDomainError(
                    "evidence_tampered",
                    "Recovered optimization evidence is not canonical.",
                    status=500,
                )
            was_quarantined = self._execution_quarantined(session)
            if was_quarantined:
                operation["handlerInvocation"] = None
                operation["recoveryRequired"] = False
                now = self._now()
                session["updatedAt"] = now
                session["heartbeatAt"] = now
                if session.get("cancelRequested") is True:
                    session["state"] = "cancelled"
                    session["failure"] = None
                    events.append(
                        self._event(
                            session,
                            "execution_quarantine_released",
                            now,
                            operationId=operation["operationId"],
                            reasonCode=session.get("cancelReason") or "user_cancelled",
                            recoveryProof="orphan_completed_after_cancel",
                        )
                    )
                    changed = True
                    return changed, events
                # The immutable result file is created only after exact receipt
                # and evidence validation.  Revalidate it above, then publish the
                # same canonical summary instead of discarding a completed run
                # merely because the state save crashed after the deadline.
                session["failure"] = None
            document_digest = _sha256_bytes(result_path.read_bytes())
            session["roundResults"].append(
                {
                    "roundId": evidence["roundId"],
                    "roundIndex": session["roundIndex"],
                    "combinationCount": session["request"]["rounds"][session["roundIndex"]]["combinationCount"],
                    "passCount": evidence["passCount"],
                    "returnedPassCount": evidence["returnedPassCount"],
                    "rowsTruncated": evidence["rowsTruncated"],
                    "report": copy.deepcopy(evidence["report"]),
                    "manifest": copy.deepcopy(evidence["manifest"]),
                    "testerSettingsSha256": evidence["testerSettingsSha256"],
                    "visibleEvidenceSha256": evidence["visibleEvidenceSha256"],
                    "initialDeposit": evidence["initialDeposit"],
                    "warnings": copy.deepcopy(evidence["warnings"]),
                    "documentRef": result_ref,
                    "documentSha256": document_digest,
                    "analyzed": False,
                }
            )
            session["stage"] = "verify_report"
            session["state"] = "running"
            session["progress"] = {
                "roundNumber": session["roundIndex"] + 1,
                "roundCount": session["roundCount"],
                "passCount": evidence["passCount"],
                "returnedPassCount": evidence["returnedPassCount"],
                "percent": 100.0,
                "rowsTruncated": evidence["rowsTruncated"],
            }
            if self._execution_quarantined(session):
                # Defensive only: failure was cleared above for a quarantined
                # orphan, so this should not remain true.
                raise OptimizationDomainError(
                    "state_invalid",
                    "Recovered optimization result remained quarantined.",
                    status=500,
                )
            if was_quarantined and isinstance(operation, dict):
                events.append(
                    self._event(
                        session,
                        "execution_quarantine_completed_accepted",
                        session["updatedAt"],
                        operationId=operation["operationId"],
                        recoveryProof="orphan_completed_exact",
                    )
                )
            changed = True
        return changed, events

    def recover_after_restart(self) -> list[dict[str, Any]]:
        """Reconcile durable boundaries; never call Start from restart recovery."""

        audits: list[dict[str, Any]] = []
        with self._locked():
            store = self._load_store_unlocked()
            now = self._now()
            audits.extend(self._expire_active_unlocked(store, now))
            if audits:
                store = self._load_store_unlocked()
            changed = False
            for session in store["sessions"]:
                if session["state"] not in ACTIVE_STATES:
                    continue
                operation = session.get("currentOperation")
                interrupted_invocation = bool(
                    isinstance(operation, dict)
                    and isinstance(operation.get("handlerInvocation"), dict)
                )
                if interrupted_invocation:
                    operation["handlerInvocation"] = None
                    operation["recoveryRequired"] = True
                recovered_documents, recovered_events = self._recover_orphan_documents(
                    session
                )
                audits.extend(recovered_events)
                session_changed = recovered_documents or interrupted_invocation
                operation = session.get("currentOperation")
                if session["state"] in TERMINAL_STATES:
                    session_changed = True
                elif isinstance(operation, dict) and session["stage"] == "run_round":
                    if isinstance(operation.get("receipt"), dict):
                        session["state"] = "collecting"
                    elif operation.get("safeBeforeStartRetry") is True:
                        session["state"] = "awaiting_visible_terminal"
                    else:
                        operation["recoveryRequired"] = True
                        session["state"] = "awaiting_visible_terminal"
                    session_changed = True
                elif session["state"] == "running" and session["stage"] in {
                    "validate_baseline",
                    "prepare_ranges",
                }:
                    session["state"] = "queued"
                    session_changed = True
                if session_changed:
                    changed = True
                    session["updatedAt"] = now
                    session["heartbeatAt"] = now
                    event = self._event(
                        session,
                        "restart_recovered",
                        now,
                        receiptRecoveryRequired=bool(
                            isinstance(operation, dict)
                            and operation.get("recoveryRequired")
                        ),
                    )
                    audits.append(event)
            if changed:
                self._save_unlocked(store)
            response = [
                self._public(item)
                for item in store["sessions"]
                if item["state"] in ACTIVE_STATES
            ]
        for event in audits:
            self._audit(event)
        return response

    def _verified_result_document(
        self, session: Mapping[str, Any], result: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Load and revalidate immutable evidence before exposing result rows."""

        document = self._read_document(
            session["workspaceRef"], result["documentRef"], result["documentSha256"]
        )
        expected_keys = {
            "schemaVersion",
            "kind",
            "sessionId",
            "operationId",
            "roundId",
            "receiptRef",
            "platform",
            "terminalCandidateId",
            "terminalSelectionRevision",
            "terminalBindingDigest",
            "passCount",
            "returnedPassCount",
            "rowsTruncated",
            "resultRows",
            "report",
            "manifest",
            "testerSettingsSha256",
            "visibleEvidenceSha256",
            "testShutdownTerminal",
            "liveTrading",
            "warnings",
        }
        try:
            if set(document) not in (expected_keys, expected_keys | {"initialDeposit"}):
                raise OptimizationDomainError(
                    "evidence_tampered", "Optimization evidence schema changed.", status=500
                )
            binding = session["terminalBinding"]
            if (
                document["schemaVersion"] != SCHEMA_VERSION
                or document["kind"] != "optimization_round_result"
                or document["sessionId"] != session["id"]
                or document["roundId"] != result["roundId"]
                or document["platform"] != session["platform"]
                or document["terminalCandidateId"] != binding["candidateId"]
                or document["terminalSelectionRevision"]
                != binding["selectionRevision"]
                or document["terminalBindingDigest"] != binding["bindingDigest"]
                or document["passCount"] != result["passCount"]
                or document["returnedPassCount"] != result["returnedPassCount"]
                or document["rowsTruncated"] != result["rowsTruncated"]
                or document["report"] != result["report"]
                or document["manifest"] != result["manifest"]
                or document["testerSettingsSha256"]
                != result["testerSettingsSha256"]
                or document["visibleEvidenceSha256"]
                != result["visibleEvidenceSha256"]
                or (
                    "initialDeposit" in result
                    and document.get("initialDeposit") != result["initialDeposit"]
                )
                or document["warnings"] != result["warnings"]
                or document["testShutdownTerminal"] is not False
                or document["liveTrading"] is not False
            ):
                raise OptimizationDomainError(
                    "evidence_tampered",
                    "Optimization evidence no longer matches durable state.",
                    status=500,
                )
            _opaque_ref(document["operationId"], field="evidence.operationId")
            _opaque_ref(document["receiptRef"], field="evidence.receiptRef")
            self._artifact(document["report"], field="evidence.report")
            self._artifact(document["manifest"], field="evidence.manifest")
            _sha256(
                document["testerSettingsSha256"],
                field="evidence.testerSettingsSha256",
            )
            _sha256(
                document["visibleEvidenceSha256"],
                field="evidence.visibleEvidenceSha256",
            )
            rows = document["resultRows"]
            if (
                not isinstance(rows, list)
                or len(rows) != result["returnedPassCount"]
                or len(rows) > MAX_RESULT_ROWS
            ):
                raise OptimizationDomainError(
                    "evidence_tampered", "Optimization result rows are invalid.", status=500
                )
            normalized_rows = [
                self._normalize_result_row(item, index=index)
                for index, item in enumerate(rows)
            ]
            if normalized_rows != rows:
                raise OptimizationDomainError(
                    "evidence_tampered",
                    "Optimization result rows are not canonical.",
                    status=500,
                )
        except OptimizationDomainError as error:
            if error.code in {"evidence_missing", "evidence_tampered"}:
                raise
            raise OptimizationDomainError(
                "evidence_tampered",
                "Optimization evidence failed public verification.",
                status=500,
            ) from error
        return document

    def _verified_analysis_document(
        self,
        session: Mapping[str, Any],
        result: Mapping[str, Any],
        verified_result: Mapping[str, Any],
    ) -> dict[str, Any]:
        analysis_ref = result.get("analysisRef")
        analysis_digest = result.get("analysisSha256")
        if analysis_ref is None and analysis_digest is None:
            # Legacy completed sessions remain readable, but every new analyze
            # transition stores the same timestamp-free deterministic document.
            return self._build_round_analysis(session, result, verified_result)
        if not isinstance(analysis_ref, str) or not isinstance(analysis_digest, str):
            raise OptimizationDomainError(
                "analysis_tampered", "Optimization analysis binding is invalid.", status=500
            )
        document = self._read_document(
            session["workspaceRef"], analysis_ref, analysis_digest
        )
        raw_policy_version = document.get("analysisPolicyVersion")
        if raw_policy_version is None:
            analysis_policy_version = 1
        elif (
            isinstance(raw_policy_version, int)
            and not isinstance(raw_policy_version, bool)
            and raw_policy_version == ANALYSIS_POLICY_VERSION
        ):
            analysis_policy_version = raw_policy_version
        else:
            raise OptimizationDomainError(
                "analysis_tampered",
                "Optimization analysis policy version is invalid.",
                status=500,
            )
        expected = self._build_round_analysis(
            session,
            result,
            verified_result,
            analysis_policy_version=analysis_policy_version,
        )
        if document != expected:
            raise OptimizationDomainError(
                "analysis_tampered",
                "Optimization analysis no longer matches verified result rows.",
                status=500,
            )
        return document

    def _public(self, session: Mapping[str, Any]) -> dict[str, Any]:
        operation = session.get("currentOperation")
        accepted_late_completed_proof: str | None = None
        accepted_late_completed_failure_code: str | None = None
        events = session.get("eventLog")
        if isinstance(events, list):
            revalidation_rows = [
                (index, event)
                for index, event in enumerate(events)
                if isinstance(event, dict)
                and event.get("type")
                == "late_completed_result_revalidation_started"
                and isinstance(event.get("operationId"), str)
                and event.get("recoveryProof")
                in {"completed_late_discarded", "orphan_completed_late_discarded"}
            ]
            if revalidation_rows:
                revalidation_index, revalidation_event = revalidation_rows[-1]
                recovered_operation_id = revalidation_event.get("operationId")
                if any(
                    isinstance(event, dict)
                    and event.get("type")
                    == "execution_quarantine_completed_accepted"
                    and event.get("operationId") == recovered_operation_id
                    for event in events[revalidation_index + 1 :]
                ):
                    accepted_late_completed_proof = str(
                        revalidation_event["recoveryProof"]
                    )
                    accepted_late_completed_failure_code = str(
                        revalidation_event.get("reasonCode") or ""
                    ) or None
        late_completed_recovery_available = (
            self._late_completed_discard_recovery_proof(session) is not None
        )
        late_completed_recovery_pending = bool(
            session.get("state") in ACTIVE_STATES
            and isinstance(operation, dict)
            and operation.get("recoveryRequired") is True
            and isinstance(operation.get("receipt"), dict)
            and any(
                isinstance(event, dict)
                and event.get("type")
                == "late_completed_result_revalidation_started"
                and event.get("operationId") == operation.get("operationId")
                for event in session.get("eventLog", [])[-8:]
            )
        )
        evidence = []
        for result in session["roundResults"]:
            verified = self._verified_result_document(session, result)
            analysis = (
                self._verified_analysis_document(session, result, verified)
                if result["analyzed"] is True
                else None
            )
            all_rows = verified["resultRows"]
            public_rows = all_rows[:MAX_PUBLIC_RESULT_ROWS]
            evidence.append(
                {
                    "roundId": result["roundId"],
                    "roundNumber": result["roundIndex"] + 1,
                    "combinationCount": result["combinationCount"],
                    "passCount": result["passCount"],
                    "returnedPassCount": result["returnedPassCount"],
                    "rowsTruncated": result["rowsTruncated"],
                    "report": copy.deepcopy(result["report"]),
                    "manifest": copy.deepcopy(result["manifest"]),
                    "testerSettingsSha256": result["testerSettingsSha256"],
                    "visibleEvidenceSha256": result["visibleEvidenceSha256"],
                    "initialDeposit": verified.get("initialDeposit"),
                    "warnings": copy.deepcopy(result["warnings"]),
                    "analyzed": result["analyzed"],
                    "analysis": copy.deepcopy(analysis),
                    "analysisSha256": (
                        result.get("analysisSha256")
                        or (_sha256_json(analysis) if isinstance(analysis, dict) else None)
                    ),
                    "resultRows": copy.deepcopy(public_rows),
                    "resultRowsSha256": _sha256_json(all_rows),
                    "publicResultRowsTruncated": len(public_rows) < len(all_rows),
                    "evidenceDocumentSha256": result["documentSha256"],
                }
            )
        return {
            "schemaVersion": SCHEMA_VERSION,
            "id": session["id"],
            "state": session["state"],
            "stage": session["stage"],
            "buildId": session["buildId"],
            "sourceDigest": session["sourceDigest"],
            "baselineReportSha256": session["baselineReportSha256"],
            "platform": session["platform"],
            "terminalBinding": copy.deepcopy(session["terminalBinding"]),
            "requestDigest": session["requestDigest"],
            "round": {
                "index": session["roundIndex"],
                "number": session["roundIndex"] + 1,
                "count": session["roundCount"],
                "id": session["request"]["rounds"][session["roundIndex"]]["roundId"],
                "combinationCount": session["request"]["rounds"][session["roundIndex"]]["combinationCount"],
            },
            "testerSettings": copy.deepcopy(session["request"]["testerSettings"]),
            "riskThresholds": copy.deepcopy(
                session["request"].get("riskThresholds")
            ),
            "progress": copy.deepcopy(session["progress"]),
            "heartbeatAt": _iso_timestamp(session["heartbeatAt"]),
            "deadlineAt": _iso_timestamp(session["deadlineAt"]),
            "cancelRequested": session["cancelRequested"],
            "cancelReason": session["cancelReason"],
            "failure": copy.deepcopy(session["failure"]),
            "recovery": {
                "startBoundaryCommitted": isinstance(operation, dict),
                "operationId": (
                    operation.get("operationId")
                    if isinstance(operation, dict)
                    else None
                ),
                "receiptPresent": bool(
                    isinstance(operation, dict)
                    and isinstance(operation.get("receipt"), dict)
                ),
                "receiptRef": (
                    operation.get("receipt", {}).get("receiptRef")
                    if isinstance(operation, dict)
                    and isinstance(operation.get("receipt"), dict)
                    else None
                ),
                "receiptRecoveryRequired": bool(
                    isinstance(operation, dict) and operation.get("recoveryRequired")
                ),
                "beforeStartRetryAllowed": bool(
                    isinstance(operation, dict)
                    and operation.get("safeBeforeStartRetry")
                ),
                "adapterCallInFlight": bool(
                    isinstance(operation, dict)
                    and isinstance(operation.get("handlerInvocation"), dict)
                ),
                "executionIdentityCaptured": bool(
                    isinstance(operation, dict)
                    and isinstance(operation.get("executionIdentity"), dict)
                ),
                "executionStopProofPresent": bool(
                    isinstance(operation, dict)
                    and isinstance(operation.get("executionStopProof"), dict)
                ),
                "lateCompletedResultRecoveryAvailable": (
                    late_completed_recovery_available
                ),
                "lateCompletedResultRecoveryPending": (
                    late_completed_recovery_pending
                ),
                "lateCompletedResultRecovered": bool(
                    accepted_late_completed_proof is not None
                ),
                "lateCompletedResultRecoveryProof": (
                    accepted_late_completed_proof
                ),
                "lateCompletedResultRecoveryFailureCode": (
                    accepted_late_completed_failure_code
                ),
            },
            "evidence": evidence,
            "liveTradingAllowed": False,
            "testShutdownTerminal": False,
        }


__all__ = [
    "EaFactoryOptimizationService",
    "OptimizationDomainError",
    "SCHEMA_VERSION",
    "ANALYSIS_POLICY_VERSION",
    "SESSION_STATES",
    "STAGES",
    "MAX_ROUNDS",
    "MAX_INPUTS_PER_ROUND",
    "MAX_COMBINATIONS_PER_ROUND",
    "MAX_RESULT_ROWS",
    "MAX_PUBLIC_RESULT_ROWS",
]
