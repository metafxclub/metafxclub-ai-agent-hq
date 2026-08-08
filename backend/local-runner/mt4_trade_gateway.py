"""Backend-owned FILE_COMMON publisher for MetafxHQTradeGateway.mq4.

The EA is the sole owner of GatewayMode, LiveArmed, FixedLot, spread,
slippage, MagicNumber, broker/account checks, and OrderSend.  This module
cannot receive or publish sizing/risk policy.  It publishes exactly one
contract-compatible command slot plus its heartbeat, then waits for a
schema-separated ACK bound to the command and its snapshot/bar evidence.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import secrets
import stat
import threading
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable


LEDGER_SCHEMA_VERSION = "metafx-mt4-trade-ledger-v3"
LEGACY_LEDGER_SCHEMA_VERSION = "metafx-mt4-trade-ledger-v2"
COMMAND_SCHEMA_VERSION = "metafx-hq-mt4-command-v2"
HEARTBEAT_SCHEMA_VERSION = "metafx-hq-mt4-heartbeat-v1"
ACK_SCHEMA_VERSION = "metafx-hq-mt4-ack-v3"
OUTCOME_SCHEMA_VERSION = "metafx-hq-mt4-outcome-v1"
SIGNED_ENVELOPE_SCHEMA_VERSION = "metafx-hq-mt4-signed-envelope-v1"
SIGNATURE_ALGORITHM = "HMAC-SHA256"
SIGNING_KEY_BYTES = 32
MAX_SIGNED_PAYLOAD_BYTES = 64 * 1024
# MT4 bar timestamps come from the broker-server clock (iTime), while
# snapshotObservedAt is UTC (TimeGMT/backend UTC).  Preserve the raw broker
# timestamp because the EA must compare it exactly with iTime(..., 1), but
# reject leads beyond the largest real-world UTC offset.
MAX_BROKER_CLOCK_LEAD_SECONDS = 14 * 60 * 60
ACK_REFERENCE_PRICE_PATTERN = re.compile(
    r'"referencePrice"\s*:\s*'
    r'(-?(?:0|[1-9][0-9]*)(?:\.([0-9]{1,8}))?)'
    r'(?=\s*[,}])'
)

SIGNED_ENVELOPE_FIELDS = (
    "schemaVersion",
    "algorithm",
    "keyId",
    "payloadHex",
    "signatureHex",
)

COMMAND_FIELDS = (
    "schemaVersion",
    "commandId",
    "idempotencyKey",
    "channelId",
    "missionId",
    "councilDecisionId",
    "ownerAgentId",
    "snapshotId",
    "snapshotObservedAt",
    "barTime",
    "referencePrice",
    "action",
    "symbol",
    "timeframe",
    "stopLoss",
    "takeProfit",
    "issuedAt",
    "expiresAt",
    "heartbeatId",
)
HEARTBEAT_FIELDS = (
    "schemaVersion",
    "channelId",
    "heartbeatId",
    "issuedAt",
    "expiresAt",
)
INTENT_ALLOWED_FIELDS = frozenset({
    "channelId",
    "streamKey",
    "snapshotId",
    "snapshotObservedAt",
    "barTime",
    "referencePrice",
    "missionId",
    "councilDecisionId",
    "ownerAgentId",
    "action",
    "symbol",
    "timeframe",
    "stopLoss",
    "takeProfit",
})
ACK_ALLOWED_FIELDS = frozenset({
    "schemaVersion",
    "profile",
    "commandId",
    "idempotencyKey",
    "channelId",
    "missionId",
    "councilDecisionId",
    "ownerAgentId",
    "snapshotId",
    "snapshotObservedAt",
    "barTime",
    "referencePrice",
    "eaClosedBarTime",
    "status",
    "reasonCode",
    "mode",
    "action",
    "symbol",
    "timeframe",
    "fixedLot",
    "observedAt",
    "ticket",
    "filledPrice",
    "filledSlippagePoints",
    "actualStopLoss",
    "actualTakeProfit",
    "actualMagicNumber",
    "actualComment",
    "signatureVerificationStatus",
    "verificationStatus",
    "executionState",
    "closedAt",
    "closedPnl",
    "errorCode",
    "statePersisted",
})
OUTCOME_FIELDS = (
    "schemaVersion",
    "channelId",
    "commandId",
    "executionState",
    "observedAt",
    "ticket",
    "symbol",
    "action",
    "openedAt",
    "closedAt",
    "openPrice",
    "stopLoss",
    "takeProfit",
    "lots",
    "magicNumber",
    "comment",
    "closedPnl",
)
FORBIDDEN_POLICY_NAMES = frozenset({
    "lot",
    "lots",
    "volume",
    "fixedlot",
    "risk",
    "riskpercent",
    "riskamount",
    "moneymanagement",
    "mode",
    "gatewaymode",
    "livearmed",
    "spread",
    "slippage",
    "magicnumber",
})
ALLOWED_ACTIONS = frozenset({"BUY", "SELL"})
ALLOWED_TIMEFRAMES = frozenset({
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
    "W1",
    "MN1",
})
ACK_STATUSES = frozenset({
    "SHADOWED",
    "EXECUTING",
    "EXECUTION_UNKNOWN",
    "EXECUTED",
    "REJECTED",
    "DUPLICATE",
    "FAILED_FINAL",
})
TERMINAL_ACK_STATUSES = ACK_STATUSES - {"EXECUTING", "EXECUTION_UNKNOWN"}
EA_MODES = frozenset({"shadow", "demo", "live"})
ACK_VERIFICATION_STATUSES = frozenset({
    "NOT_APPLICABLE",
    "SELECT_FAILED",
    "MISMATCH",
    "VERIFIED_OPEN",
    "VERIFIED_CLOSED",
})
ACK_EXECUTION_STATES = frozenset({"NONE", "UNKNOWN", "OPEN", "CLOSED"})

SAFE_CHANNEL_PATTERN = re.compile(r"mtc-[A-Za-z0-9_-]{1,116}")
SAFE_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}")
SAFE_SYMBOL_PATTERN = re.compile(r"[A-Z0-9._-]{2,24}")
SAFE_REASON_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9_]{0,119}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
COMMAND_ID_PATTERN = re.compile(r"cmd-[0-9a-f]{24}")
IDEMPOTENCY_KEY_PATTERN = re.compile(r"idem-[0-9a-f]{32}")
HEARTBEAT_ID_PATTERN = re.compile(r"hb-[0-9a-f]{24}")
SIGNING_KEY_ID_PATTERN = re.compile(r"hk-[0-9a-f]{64}")
LOWER_HEX_PATTERN = re.compile(r"[0-9a-f]+")


class TradeGatewayError(RuntimeError):
    """Base gateway exception with a stable machine-readable code."""

    code = "trade_gateway_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class GatewayValidationError(TradeGatewayError):
    code = "invalid_trade_intent"


class GatewaySafetyError(TradeGatewayError):
    code = "trade_safety_gate_blocked"


class OneOrderPerBarError(TradeGatewayError):
    code = "one_order_per_bar"


class OutstandingCommandError(TradeGatewayError):
    code = "single_outstanding_command"


class LedgerIntegrityError(TradeGatewayError):
    code = "trade_ledger_integrity_error"


class AckValidationError(TradeGatewayError):
    code = "invalid_trade_ack"


class AckConflictError(TradeGatewayError):
    code = "trade_ack_conflict"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise GatewayValidationError("Clock must return datetime.", code="invalid_clock")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _now_epoch(value: datetime) -> int:
    epoch = int(_as_utc(value).timestamp())
    if not 946684800 <= epoch <= 2_147_483_647:
        raise GatewayValidationError("Clock is outside the MT4 integer range.", code="invalid_clock")
    return epoch


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _strict_json_object(text: str) -> dict[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(text, object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object.")
    return value


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("ascii")).hexdigest()


def _contract_digest(schema_version: str, value: object) -> str:
    """Domain-separate durable identities across incompatible wire schemas."""
    return _digest({
        "schemaVersionSalt": schema_version,
        "payload": value,
    })


def _signing_key_id(key: bytes) -> str:
    if not isinstance(key, bytes) or len(key) != SIGNING_KEY_BYTES:
        raise GatewaySafetyError(
            "The MT4 signing key must contain exactly 32 bytes.",
            code="signing_key_invalid",
        )
    return f"hk-{hashlib.sha256(key).hexdigest()}"


def _signed_envelope_preimage(
    *,
    kind: str,
    key_id: str,
    channel_id: str,
    payload_hex: str,
) -> bytes:
    normalized_kind = str(kind or "").strip().lower()
    if normalized_kind not in {"command", "heartbeat"}:
        raise GatewayValidationError(
            "Signed envelope kind must be command or heartbeat.",
            code="invalid_signed_envelope_kind",
        )
    if not SIGNING_KEY_ID_PATTERN.fullmatch(str(key_id or "")):
        raise GatewaySafetyError(
            "Signed envelope key id is invalid.",
            code="signing_key_id_invalid",
        )
    if not SAFE_CHANNEL_PATTERN.fullmatch(str(channel_id or "")):
        raise GatewayValidationError("Invalid channelId.", code="invalid_channel_id")
    if (
        not isinstance(payload_hex, str)
        or not payload_hex
        or len(payload_hex) % 2 != 0
        or len(payload_hex) > MAX_SIGNED_PAYLOAD_BYTES * 2
        or not LOWER_HEX_PATTERN.fullmatch(payload_hex)
    ):
        raise GatewayValidationError(
            "Signed envelope payload hex is invalid.",
            code="invalid_signed_payload_hex",
        )
    return (
        f"METAFXHQ|MT4|{normalized_kind.upper()}|HMAC-SHA256|V1\n"
        f"{key_id}\n{channel_id}\n{payload_hex}"
    ).encode("ascii")


def _hmac_sha256_hex(key: bytes, payload: bytes) -> str:
    if not isinstance(key, bytes) or not isinstance(payload, bytes):
        raise GatewaySafetyError(
            "HMAC inputs must be bytes.",
            code="signing_input_invalid",
        )
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def _signed_envelope_signature(
    *,
    kind: str,
    key: bytes,
    key_id: str,
    channel_id: str,
    payload_hex: str,
) -> str:
    if _signing_key_id(key) != key_id:
        raise GatewaySafetyError(
            "Signing key fingerprint does not match its key id.",
            code="signing_key_id_mismatch",
        )
    return _hmac_sha256_hex(
        key,
        _signed_envelope_preimage(
            kind=kind,
            key_id=key_id,
            channel_id=channel_id,
            payload_hex=payload_hex,
        ),
    )


def _build_signed_envelope(
    *,
    kind: str,
    channel_id: str,
    payload: bytes,
    key: bytes,
) -> dict[str, str]:
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_SIGNED_PAYLOAD_BYTES:
        raise GatewayValidationError(
            "Signed envelope payload size is invalid.",
            code="invalid_signed_payload_size",
        )
    try:
        payload.decode("ascii")
    except UnicodeDecodeError as error:
        raise GatewayValidationError(
            "Signed envelope payload must be ASCII.",
            code="non_ascii_signed_payload",
        ) from error
    key_id = _signing_key_id(key)
    payload_hex = payload.hex()
    return {
        "schemaVersion": SIGNED_ENVELOPE_SCHEMA_VERSION,
        "algorithm": SIGNATURE_ALGORITHM,
        "keyId": key_id,
        "payloadHex": payload_hex,
        "signatureHex": _signed_envelope_signature(
            kind=kind,
            key=key,
            key_id=key_id,
            channel_id=channel_id,
            payload_hex=payload_hex,
        ),
    }


def _policy_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _number(
    value: object,
    *,
    field: str,
    maximum: Decimal = Decimal("1000000000"),
) -> Decimal:
    if isinstance(value, bool):
        raise GatewayValidationError(f"{field} must be numeric.", code=f"invalid_{field}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise GatewayValidationError(
            f"{field} must be numeric.",
            code=f"invalid_{field}",
        ) from error
    if not number.is_finite() or number <= 0 or number > maximum:
        raise GatewayValidationError(
            f"{field} is outside the allowed range.",
            code=f"invalid_{field}",
        )
    return number.normalize()


def _json_number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    return int(integral) if value == integral else float(value)


def _flat_json(payload: Mapping[str, object], *, exact_fields: tuple[str, ...] | None = None) -> None:
    if exact_fields is not None and set(payload) != set(exact_fields):
        raise GatewayValidationError("Flat JSON fields do not match the EA contract.", code="wire_contract_mismatch")
    for key, value in payload.items():
        if not isinstance(key, str) or isinstance(value, (dict, list, tuple, set)):
            raise GatewayValidationError("Nested JSON is not allowed.", code="non_flat_json")
        if isinstance(value, float) and not math.isfinite(value):
            raise GatewayValidationError("Non-finite JSON number.", code="non_finite_json")
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise GatewayValidationError("Only JSON scalars are allowed.", code="non_flat_json")
        if isinstance(value, str):
            try:
                value.encode("ascii")
            except UnicodeEncodeError as error:
                raise GatewayValidationError(
                    "EA wire strings must be ASCII.",
                    code="non_ascii_wire_value",
                ) from error


def _ordered_packet(
    payload: Mapping[str, object],
    fields: tuple[str, ...],
) -> dict[str, object]:
    """Restore the public wire order after the durable store sorts JSON keys."""
    if set(payload) != set(fields):
        raise GatewayValidationError(
            "Flat JSON fields do not match the EA contract.",
            code="wire_contract_mismatch",
        )
    return {field: payload[field] for field in fields}


def _atomic_write_json(path: Path, payload: Mapping[str, object], *, temporary: Path) -> None:
    _flat_json(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        dict(payload),
        ensure_ascii=True,
        allow_nan=False,
        indent=2,
    )
    try:
        with temporary.open("w", encoding="ascii", newline="\n") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _atomic_write_private_bytes(path: Path, payload: bytes) -> None:
    """Create or replace one local secret without ever serializing it as text."""
    if not isinstance(payload, bytes) or not payload:
        raise GatewaySafetyError(
            "Private signing material is invalid.",
            code="signing_key_invalid",
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    try:
        try:
            temporary.unlink(missing_ok=True)
        except OSError as error:
            raise GatewaySafetyError(
                "Unable to prepare the signing key file.",
                code="signing_key_write_failed",
            ) from error
        try:
            descriptor = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        except OSError as error:
            raise GatewaySafetyError(
                "Unable to persist the signing key file.",
                code="signing_key_write_failed",
            ) from error
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _atomic_write_store(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    serialized = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    )
    try:
        with temporary.open("w", encoding="ascii", newline="\n") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _empty_ledger(now: datetime) -> dict[str, Any]:
    return {
        "schemaVersion": LEDGER_SCHEMA_VERSION,
        "revision": 0,
        "activeCommandId": None,
        "commands": {},
        "idempotency": {},
        "barClaims": {},
        "updatedAt": _iso(now),
    }


def _is_safe_empty_legacy_ledger(value: object) -> bool:
    """Only an entirely empty v2 ledger may cross the v1 -> v2 wire boundary."""
    if not isinstance(value, dict):
        return False
    if set(value) != {
        "schemaVersion",
        "revision",
        "activeCommandId",
        "commands",
        "idempotency",
        "barClaims",
        "updatedAt",
    }:
        return False
    revision = value.get("revision")
    return (
        value.get("schemaVersion") == LEGACY_LEDGER_SCHEMA_VERSION
        and isinstance(revision, int)
        and not isinstance(revision, bool)
        and revision >= 0
        and value.get("activeCommandId") is None
        and value.get("commands") == {}
        and value.get("idempotency") == {}
        and value.get("barClaims") == {}
        and isinstance(value.get("updatedAt"), str)
    )


class MT4TradeGateway:
    """Single-slot backend publisher compatible with the EA v2 contract."""

    def __init__(
        self,
        *,
        file_common_root: str | Path,
        state_root: str | Path,
        command_ttl_seconds: int = 30,
        heartbeat_ttl_seconds: int = 30,
        clock: Callable[[], datetime] = _utc_now,
    ):
        if (
            isinstance(command_ttl_seconds, bool)
            or not isinstance(command_ttl_seconds, int)
            or not 1 <= command_ttl_seconds <= 120
        ):
            raise GatewayValidationError("Command TTL must be 1-120 seconds.", code="invalid_ttl")
        if (
            isinstance(heartbeat_ttl_seconds, bool)
            or not isinstance(heartbeat_ttl_seconds, int)
            or not 1 <= heartbeat_ttl_seconds <= 60
        ):
            raise GatewayValidationError(
                "Heartbeat TTL must be 1-60 seconds.",
                code="invalid_heartbeat_ttl",
            )
        self.file_common_root = Path(file_common_root)
        self.state_root = Path(state_root)
        self.command_ttl_seconds = command_ttl_seconds
        self.heartbeat_ttl_seconds = heartbeat_ttl_seconds
        self.clock = clock
        self._lock = threading.RLock()
        self._ledger_path = self.state_root / "mt4-trade-gateway-ledger.json"
        self._ledger_backup_path = self.state_root / "mt4-trade-gateway-ledger.json.bak"

    def _now(self) -> datetime:
        return _as_utc(self.clock())

    def _base_path(self, channel_id: str) -> Path:
        return self.file_common_root / "MetafxHQ" / channel_id / "trade-gateway"

    def _command_path(self, channel_id: str) -> Path:
        return self._base_path(channel_id) / "command.json"

    def _heartbeat_path(self, channel_id: str) -> Path:
        return self._base_path(channel_id) / "heartbeat.json"

    def _kill_switch_path(self, channel_id: str) -> Path:
        return self._base_path(channel_id) / "kill.switch"

    def _ack_path(self, channel_id: str, command_id: str) -> Path:
        return self._base_path(channel_id) / "acks" / f"{command_id}.json"

    def _outcome_path(self, channel_id: str, command_id: str) -> Path:
        return self._base_path(channel_id) / "outcomes" / f"{command_id}.json"

    def _keys_path(self, channel_id: str) -> Path:
        return self._base_path(channel_id) / "keys"

    def _active_key_id_path(self, channel_id: str) -> Path:
        return self._keys_path(channel_id) / "active-key.id"

    def _signing_key_path(self, channel_id: str, key_id: str) -> Path:
        return self._keys_path(channel_id) / f"{key_id}.key"

    @staticmethod
    def _validated_channel_id(channel_id: object) -> str:
        value = str(channel_id or "")
        if not SAFE_CHANNEL_PATTERN.fullmatch(value):
            raise GatewayValidationError("Invalid channelId.", code="invalid_channel_id")
        return value

    def _load_active_signing_key(self, channel_id: object) -> tuple[str, bytes]:
        channel = self._validated_channel_id(channel_id)
        active_path = self._active_key_id_path(channel)
        if active_path.is_symlink() or not active_path.is_file():
            raise GatewaySafetyError(
                "The active MT4 signing key id is missing.",
                code="signing_key_missing",
            )
        try:
            if active_path.stat().st_size > 96:
                raise GatewaySafetyError(
                    "The active MT4 signing key id is invalid.",
                    code="signing_key_state_invalid",
                )
            key_id = active_path.read_text(encoding="ascii")
        except (OSError, UnicodeError) as error:
            raise GatewaySafetyError(
                "The active MT4 signing key id is unreadable.",
                code="signing_key_state_invalid",
            ) from error
        if not SIGNING_KEY_ID_PATTERN.fullmatch(key_id):
            raise GatewaySafetyError(
                "The active MT4 signing key id is invalid.",
                code="signing_key_state_invalid",
            )
        key_path = self._signing_key_path(channel, key_id)
        if key_path.is_symlink() or not key_path.is_file():
            raise GatewaySafetyError(
                "The active MT4 signing key is missing.",
                code="signing_key_missing",
            )
        try:
            key_stat = key_path.stat()
            if key_stat.st_size != SIGNING_KEY_BYTES:
                raise GatewaySafetyError(
                    "The active MT4 signing key has an invalid size.",
                    code="signing_key_invalid",
                )
            if os.name == "posix" and stat.S_IMODE(key_stat.st_mode) & 0o077:
                raise GatewaySafetyError(
                    "The active MT4 signing key permissions are too broad.",
                    code="signing_key_permissions_invalid",
                )
            key = key_path.read_bytes()
        except OSError as error:
            raise GatewaySafetyError(
                "The active MT4 signing key is unreadable.",
                code="signing_key_invalid",
            ) from error
        if len(key) != SIGNING_KEY_BYTES or _signing_key_id(key) != key_id:
            raise GatewaySafetyError(
                "The active MT4 signing key fingerprint is invalid.",
                code="signing_key_id_mismatch",
            )
        return key_id, key

    def ensure_signing_key(self, channel_id: object) -> dict[str, object]:
        """Provision one per-channel key and return only non-secret metadata."""
        channel = self._validated_channel_id(channel_id)
        with self._lock:
            active_path = self._active_key_id_path(channel)
            if active_path.exists() or active_path.is_symlink():
                key_id, _ = self._load_active_signing_key(channel)
                return {
                    "ok": True,
                    "channelId": channel,
                    "keyId": key_id,
                    "algorithm": SIGNATURE_ALGORITHM,
                    "envelopeSchemaVersion": SIGNED_ENVELOPE_SCHEMA_VERSION,
                    "created": False,
                }

            keys_path = self._keys_path(channel)
            try:
                existing = list(keys_path.iterdir()) if keys_path.exists() else []
            except OSError as error:
                raise GatewaySafetyError(
                    "The MT4 signing key directory is unreadable.",
                    code="signing_key_state_invalid",
                ) from error
            if existing:
                raise GatewaySafetyError(
                    "Signing key files exist without an active key id.",
                    code="signing_key_state_incomplete",
                )

            key = secrets.token_bytes(SIGNING_KEY_BYTES)
            key_id = _signing_key_id(key)
            key_path = self._signing_key_path(channel, key_id)
            _atomic_write_private_bytes(key_path, key)
            try:
                _atomic_write_private_bytes(active_path, key_id.encode("ascii"))
            except Exception:
                try:
                    key_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            loaded_key_id, _ = self._load_active_signing_key(channel)
            if loaded_key_id != key_id:
                raise GatewaySafetyError(
                    "The MT4 signing key could not be verified after creation.",
                    code="signing_key_write_failed",
                )
            return {
                "ok": True,
                "channelId": channel,
                "keyId": key_id,
                "algorithm": SIGNATURE_ALGORITHM,
                "envelopeSchemaVersion": SIGNED_ENVELOPE_SCHEMA_VERSION,
                "created": True,
            }

    @staticmethod
    def _compact_inner_payload(
        payload: Mapping[str, object],
        fields: tuple[str, ...],
    ) -> bytes:
        _flat_json(payload, exact_fields=fields)
        serialized = json.dumps(
            _ordered_packet(payload, fields),
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        encoded = serialized.encode("ascii")
        if not 0 < len(encoded) <= MAX_SIGNED_PAYLOAD_BYTES:
            raise GatewayValidationError(
                "Signed inner payload size is invalid.",
                code="invalid_signed_payload_size",
            )
        return encoded

    def _sign_inner_packet(
        self,
        *,
        kind: str,
        payload: Mapping[str, object],
        fields: tuple[str, ...],
    ) -> dict[str, str]:
        channel_id = self._validated_channel_id(payload.get("channelId"))
        _, key = self._load_active_signing_key(channel_id)
        envelope = _build_signed_envelope(
            kind=kind,
            channel_id=channel_id,
            payload=self._compact_inner_payload(payload, fields),
            key=key,
        )
        _flat_json(envelope, exact_fields=SIGNED_ENVELOPE_FIELDS)
        return envelope

    def _verify_signed_envelope(
        self,
        envelope: Mapping[str, object],
        *,
        kind: str,
        channel_id: str,
        fields: tuple[str, ...],
        inner_schema: str,
    ) -> dict[str, object]:
        try:
            _flat_json(envelope, exact_fields=SIGNED_ENVELOPE_FIELDS)
        except GatewayValidationError as error:
            raise GatewaySafetyError(
                "Signed envelope fields are invalid.",
                code="signed_envelope_invalid",
            ) from error
        if (
            envelope.get("schemaVersion") != SIGNED_ENVELOPE_SCHEMA_VERSION
            or envelope.get("algorithm") != SIGNATURE_ALGORITHM
        ):
            raise GatewaySafetyError(
                "Signed envelope contract is unsupported.",
                code="signed_envelope_invalid",
            )
        key_id = str(envelope.get("keyId") or "")
        payload_hex = str(envelope.get("payloadHex") or "")
        signature_hex = str(envelope.get("signatureHex") or "")
        if (
            not SIGNING_KEY_ID_PATTERN.fullmatch(key_id)
            or not SHA256_PATTERN.fullmatch(signature_hex)
            or not payload_hex
            or len(payload_hex) % 2 != 0
            or len(payload_hex) > MAX_SIGNED_PAYLOAD_BYTES * 2
            or not LOWER_HEX_PATTERN.fullmatch(payload_hex)
        ):
            raise GatewaySafetyError(
                "Signed envelope values are invalid.",
                code="signed_envelope_invalid",
            )
        active_key_id, key = self._load_active_signing_key(channel_id)
        if key_id != active_key_id:
            raise GatewaySafetyError(
                "Signed envelope uses a non-active key.",
                code="signed_envelope_key_mismatch",
            )
        expected = _signed_envelope_signature(
            kind=kind,
            key=key,
            key_id=key_id,
            channel_id=channel_id,
            payload_hex=payload_hex,
        )
        if not hmac.compare_digest(signature_hex, expected):
            raise GatewaySafetyError(
                "Signed envelope authentication failed.",
                code="signed_envelope_signature_invalid",
            )
        try:
            payload_bytes = bytes.fromhex(payload_hex)
            payload_text = payload_bytes.decode("ascii")
            inner = _strict_json_object(payload_text)
        except (ValueError, UnicodeError, json.JSONDecodeError) as error:
            raise GatewaySafetyError(
                "Signed envelope payload is unreadable.",
                code="signed_envelope_payload_invalid",
            ) from error
        if (
            not isinstance(inner, dict)
            or inner.get("schemaVersion") != inner_schema
            or inner.get("channelId") != channel_id
        ):
            raise GatewaySafetyError(
                "Signed envelope inner contract is invalid.",
                code="signed_envelope_payload_invalid",
            )
        try:
            if self._compact_inner_payload(inner, fields) != payload_bytes:
                raise GatewaySafetyError(
                    "Signed envelope payload is not canonical.",
                    code="signed_envelope_payload_not_canonical",
                )
        except GatewayValidationError as error:
            raise GatewaySafetyError(
                "Signed envelope inner fields are invalid.",
                code="signed_envelope_payload_invalid",
            ) from error
        return _ordered_packet(inner, fields)

    def _load_ledger(self) -> dict[str, Any]:
        if not self._ledger_path.exists():
            return _empty_ledger(self._now())
        try:
            ledger = json.loads(self._ledger_path.read_text(encoding="ascii"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise LedgerIntegrityError(
                "Trade ledger is unreadable; restore its backup before continuing."
            ) from error
        if (
            isinstance(ledger, dict)
            and ledger.get("schemaVersion") == LEGACY_LEDGER_SCHEMA_VERSION
        ):
            if not _is_safe_empty_legacy_ledger(ledger):
                raise LedgerIntegrityError(
                    "A non-empty ledger-v2 cannot be migrated to ledger-v3/command-v2. "
                    "Reconcile or archive it explicitly before continuing."
                )
            migrated = _empty_ledger(self._now())
            migrated["revision"] = int(ledger["revision"])
            return self._save_ledger(migrated)
        if (
            not isinstance(ledger, dict)
            or ledger.get("schemaVersion") != LEDGER_SCHEMA_VERSION
            or not isinstance(ledger.get("commands"), dict)
            or not isinstance(ledger.get("idempotency"), dict)
            or not isinstance(ledger.get("barClaims"), dict)
            or isinstance(ledger.get("revision"), bool)
            or not isinstance(ledger.get("revision"), int)
            or (
                ledger.get("activeCommandId") is not None
                and ledger.get("activeCommandId") not in ledger["commands"]
            )
        ):
            raise LedgerIntegrityError("Trade ledger has an invalid schema.")
        outstanding_ids: list[str] = []
        for command_id, entry in ledger["commands"].items():
            command = entry.get("command") if isinstance(entry, dict) else None
            backend_identity = entry.get("backendIdentity") if isinstance(entry, dict) else None
            if (
                not COMMAND_ID_PATTERN.fullmatch(str(command_id))
                or not isinstance(command, dict)
                or set(command) != set(COMMAND_FIELDS)
                or command.get("schemaVersion") != COMMAND_SCHEMA_VERSION
                or command.get("commandId") != command_id
                or entry.get("wireSchemaVersion") != COMMAND_SCHEMA_VERSION
                or not isinstance(backend_identity, dict)
                or set(backend_identity) != {
                    "snapshotId",
                    "streamKey",
                    "snapshotObservedAt",
                    "barTime",
                    "referencePrice",
                    "barKey",
                }
                or any(
                    backend_identity.get(field) != command.get(field)
                    for field in (
                        "snapshotId",
                        "snapshotObservedAt",
                        "barTime",
                        "referencePrice",
                    )
                )
                or backend_identity.get("barKey") != entry.get("barKey")
                or not SHA256_PATTERN.fullmatch(
                    str(backend_identity.get("streamKey") or "")
                )
                or not SHA256_PATTERN.fullmatch(str(entry.get("requestDigest") or ""))
                or not SHA256_PATTERN.fullmatch(str(entry.get("barKey") or ""))
                or ledger["idempotency"].get(entry.get("requestDigest")) != command_id
                or ledger["barClaims"].get(entry.get("barKey")) != command_id
            ):
                raise LedgerIntegrityError("Trade ledger indexes are inconsistent.")
            try:
                _flat_json(command, exact_fields=COMMAND_FIELDS)
            except GatewayValidationError as error:
                raise LedgerIntegrityError(
                    "Trade ledger contains a command outside the EA wire contract."
                ) from error
            if not isinstance(entry.get("outstanding"), bool):
                raise LedgerIntegrityError("Trade ledger outstanding state is invalid.")
            if entry["outstanding"]:
                outstanding_ids.append(command_id)
            stored_ack = entry.get("ack")
            if isinstance(stored_ack, dict) and "fixedLot" in stored_ack:
                raise LedgerIntegrityError(
                    "Trade ledger contains unsanitized EA sizing data."
                )
        active_id = ledger.get("activeCommandId")
        if len(outstanding_ids) > 1 or (
            outstanding_ids and active_id != outstanding_ids[0]
        ) or (
            not outstanding_ids and active_id is not None
        ):
            raise LedgerIntegrityError(
                "Trade ledger violates the single-outstanding-command invariant."
            )
        return ledger

    def _save_ledger(self, ledger: dict[str, Any]) -> dict[str, Any]:
        ledger = dict(ledger)
        ledger["schemaVersion"] = LEDGER_SCHEMA_VERSION
        ledger["revision"] = int(ledger.get("revision") or 0) + 1
        ledger["updatedAt"] = _iso(self._now())
        self.state_root.mkdir(parents=True, exist_ok=True)
        if self._ledger_path.exists():
            try:
                existing = json.loads(self._ledger_path.read_text(encoding="ascii"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise LedgerIntegrityError(
                    "Refusing to overwrite a corrupt trade ledger."
                ) from error
            _atomic_write_store(self._ledger_backup_path, existing)
        _atomic_write_store(self._ledger_path, ledger)
        return ledger

    def _normalize_identifier(self, value: object, *, field: str, required: bool) -> str:
        text = str(value or "").strip()
        if not text and not required:
            return ""
        if not SAFE_IDENTIFIER_PATTERN.fullmatch(text):
            raise GatewayValidationError(f"Invalid {field}.", code=f"invalid_{field}")
        return text

    def _normalize_ack_identifier(self, value: object, *, field: str) -> str:
        try:
            return self._normalize_identifier(value, field=field, required=False)
        except GatewayValidationError as error:
            raise AckValidationError(str(error), code=error.code) from error

    def _normalize_intent(self, intent: Mapping[str, object]) -> dict[str, object]:
        if not isinstance(intent, Mapping):
            raise GatewayValidationError("Trade intent must be an object.")
        forbidden = sorted(
            str(field)
            for field in intent
            if _policy_name(field) in FORBIDDEN_POLICY_NAMES
        )
        if forbidden:
            raise GatewayValidationError(
                f"EA-owned policy fields are forbidden: {', '.join(forbidden)}",
                code="ea_policy_field_forbidden",
            )
        unknown = sorted(set(intent) - INTENT_ALLOWED_FIELDS)
        if unknown:
            raise GatewayValidationError(
                f"Unknown trade intent fields: {', '.join(unknown)}",
                code="unknown_trade_intent_field",
            )
        required = {
            "channelId",
            "snapshotId",
            "snapshotObservedAt",
            "barTime",
            "referencePrice",
            "action",
            "symbol",
            "timeframe",
            "stopLoss",
            "takeProfit",
        }
        missing = sorted(field for field in required if field not in intent)
        if missing:
            raise GatewayValidationError(
                f"Missing trade intent fields: {', '.join(missing)}",
                code="missing_trade_intent_field",
            )
        channel_id = str(intent.get("channelId") or "").strip()
        if not SAFE_CHANNEL_PATTERN.fullmatch(channel_id):
            raise GatewayValidationError("Invalid channelId.", code="invalid_channel_id")
        snapshot_id = str(intent.get("snapshotId") or "").strip().lower()
        if not SHA256_PATTERN.fullmatch(snapshot_id):
            raise GatewayValidationError("Invalid snapshotId.", code="invalid_snapshot_id")
        snapshot_observed_at = intent.get("snapshotObservedAt")
        if (
            isinstance(snapshot_observed_at, bool)
            or not isinstance(snapshot_observed_at, int)
            or not 946684800 <= snapshot_observed_at <= 2_147_483_647
        ):
            raise GatewayValidationError(
                "Invalid snapshot observation time.",
                code="invalid_snapshot_observed_at",
            )
        stream_key = str(intent.get("streamKey") or "").strip().lower()
        if stream_key and not SHA256_PATTERN.fullmatch(stream_key):
            raise GatewayValidationError("Invalid streamKey.", code="invalid_stream_key")
        if not stream_key:
            stream_key = _digest({
                "channelId": channel_id,
                "symbol": str(intent.get("symbol") or "").upper(),
                "timeframe": str(intent.get("timeframe") or "").upper(),
            })
        bar_time = intent.get("barTime")
        if (
            isinstance(bar_time, bool)
            or not isinstance(bar_time, int)
            or not 946684800 <= bar_time <= 2_147_483_647
        ):
            raise GatewayValidationError("Invalid closed bar time.", code="invalid_bar_time")
        if bar_time - snapshot_observed_at > MAX_BROKER_CLOCK_LEAD_SECONDS:
            raise GatewayValidationError(
                "Closed bar time is implausibly far ahead of the UTC snapshot observation.",
                code="invalid_snapshot_bar_order",
            )
        action = str(intent.get("action") or "").strip().upper()
        if action not in ALLOWED_ACTIONS:
            raise GatewayValidationError("Action must be BUY or SELL.", code="invalid_action")
        symbol = str(intent.get("symbol") or "").strip().upper()
        if not SAFE_SYMBOL_PATTERN.fullmatch(symbol):
            raise GatewayValidationError("Invalid symbol.", code="invalid_symbol")
        timeframe = str(intent.get("timeframe") or "").strip().upper()
        if timeframe not in ALLOWED_TIMEFRAMES:
            raise GatewayValidationError(
                "Timeframe must be M5 or higher and supported by the EA.",
                code="invalid_timeframe",
            )
        stop_loss = _number(intent.get("stopLoss"), field="stop_loss")
        take_profit = _number(intent.get("takeProfit"), field="take_profit")
        reference_price = _number(
            intent.get("referencePrice"),
            field="reference_price",
        )
        if (
            action == "BUY"
            and not stop_loss < reference_price < take_profit
        ) or (
            action == "SELL"
            and not take_profit < reference_price < stop_loss
        ):
            raise GatewayValidationError(
                "SL/TP must straddle the snapshot reference price for the action.",
                code="invalid_sl_tp_direction",
            )
        return {
            "channelId": channel_id,
            "streamKey": stream_key,
            "snapshotId": snapshot_id,
            "snapshotObservedAt": snapshot_observed_at,
            "barTime": bar_time,
            "referencePrice": _json_number(reference_price),
            "missionId": self._normalize_identifier(
                intent.get("missionId"),
                field="mission_id",
                required=False,
            ),
            "councilDecisionId": self._normalize_identifier(
                intent.get("councilDecisionId"),
                field="council_decision_id",
                required=False,
            ),
            "ownerAgentId": self._normalize_identifier(
                intent.get("ownerAgentId"),
                field="owner_agent_id",
                required=False,
            ),
            "action": action,
            "symbol": symbol,
            "timeframe": timeframe,
            "stopLoss": _json_number(stop_loss),
            "takeProfit": _json_number(take_profit),
        }

    def _build_packets(
        self,
        intent: Mapping[str, object],
        *,
        now: datetime,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object], str, str]:
        issued_at = _now_epoch(now)
        expires_at = issued_at + self.command_ttl_seconds
        bar_key = _contract_digest(COMMAND_SCHEMA_VERSION, {
            "channelId": intent["channelId"],
            "symbol": intent["symbol"],
            "timeframe": intent["timeframe"],
            "barTime": intent["barTime"],
        })
        request_packet = {
            **intent,
            "commandTtlSeconds": self.command_ttl_seconds,
            "barKey": bar_key,
        }
        request_digest = _contract_digest(COMMAND_SCHEMA_VERSION, request_packet)
        command_id = f"cmd-{request_digest[:24]}"
        idempotency_key = f"idem-{request_digest[:32]}"
        heartbeat_id = f"hb-{request_digest[32:56]}"
        command = {
            "schemaVersion": COMMAND_SCHEMA_VERSION,
            "commandId": command_id,
            "idempotencyKey": idempotency_key,
            "channelId": intent["channelId"],
            "missionId": intent["missionId"],
            "councilDecisionId": intent["councilDecisionId"],
            "ownerAgentId": intent["ownerAgentId"],
            "snapshotId": intent["snapshotId"],
            "snapshotObservedAt": intent["snapshotObservedAt"],
            "barTime": intent["barTime"],
            "referencePrice": intent["referencePrice"],
            "action": intent["action"],
            "symbol": intent["symbol"],
            "timeframe": intent["timeframe"],
            "stopLoss": intent["stopLoss"],
            "takeProfit": intent["takeProfit"],
            "issuedAt": issued_at,
            "expiresAt": expires_at,
            "heartbeatId": heartbeat_id,
        }
        heartbeat = {
            "schemaVersion": HEARTBEAT_SCHEMA_VERSION,
            "channelId": intent["channelId"],
            "heartbeatId": heartbeat_id,
            "issuedAt": issued_at,
            "expiresAt": min(
                expires_at,
                issued_at + self.heartbeat_ttl_seconds,
            ),
        }
        backend_identity = {
            "snapshotId": intent["snapshotId"],
            "streamKey": intent["streamKey"],
            "snapshotObservedAt": intent["snapshotObservedAt"],
            "barTime": intent["barTime"],
            "referencePrice": intent["referencePrice"],
            "barKey": bar_key,
        }
        _flat_json(command, exact_fields=COMMAND_FIELDS)
        _flat_json(heartbeat, exact_fields=HEARTBEAT_FIELDS)
        return command, heartbeat, backend_identity, request_digest, bar_key

    def _fresh_heartbeat(self, command: Mapping[str, object], now: datetime) -> dict[str, object]:
        issued_at = _now_epoch(now)
        heartbeat = {
            "schemaVersion": HEARTBEAT_SCHEMA_VERSION,
            "channelId": command["channelId"],
            "heartbeatId": command["heartbeatId"],
            "issuedAt": issued_at,
            "expiresAt": min(
                int(command["expiresAt"]),
                issued_at + self.heartbeat_ttl_seconds,
            ),
        }
        _flat_json(heartbeat, exact_fields=HEARTBEAT_FIELDS)
        return heartbeat

    def _write_heartbeat(self, heartbeat: Mapping[str, object]) -> None:
        path = self._heartbeat_path(str(heartbeat["channelId"]))
        envelope = self._sign_inner_packet(
            kind="heartbeat",
            payload=heartbeat,
            fields=HEARTBEAT_FIELDS,
        )
        _atomic_write_json(
            path,
            _ordered_packet(envelope, SIGNED_ENVELOPE_FIELDS),
            temporary=path.with_name("heartbeat.json.tmp"),
        )

    def _write_command(self, command: Mapping[str, object]) -> None:
        _flat_json(command, exact_fields=COMMAND_FIELDS)
        path = self._command_path(str(command["channelId"]))
        envelope = self._sign_inner_packet(
            kind="command",
            payload=command,
            fields=COMMAND_FIELDS,
        )
        _atomic_write_json(
            path,
            _ordered_packet(envelope, SIGNED_ENVELOPE_FIELDS),
            temporary=path.with_name("command.json.tmp"),
        )

    def _read_command_slot_record(
        self,
        channel_id: str,
        *,
        allow_legacy_plain: bool,
    ) -> tuple[dict[str, object] | None, bool]:
        """Return the verified inner command and whether it was legacy plain JSON."""
        path = self._command_path(channel_id)
        if not path.exists():
            return None, False
        if not path.is_file():
            raise OutstandingCommandError(
                "The EA command slot is not a regular file."
            )
        try:
            raw = _strict_json_object(path.read_text(encoding="ascii"))
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            raise OutstandingCommandError(
                "The existing command.json is unreadable; reconcile it first."
            ) from error
        if not isinstance(raw, dict):
            raise OutstandingCommandError("The existing command.json is not an object.")
        if raw.get("schemaVersion") == SIGNED_ENVELOPE_SCHEMA_VERSION:
            try:
                command = self._verify_signed_envelope(
                    raw,
                    kind="command",
                    channel_id=channel_id,
                    fields=COMMAND_FIELDS,
                    inner_schema=COMMAND_SCHEMA_VERSION,
                )
            except TradeGatewayError as error:
                raise OutstandingCommandError(
                    "The existing signed command.json failed authentication.",
                    code=error.code,
                ) from error
            return command, False
        if not allow_legacy_plain:
            raise OutstandingCommandError(
                "The existing command.json is not a signed envelope.",
                code="signed_envelope_required",
            )
        if set(raw) != set(COMMAND_FIELDS) or raw.get("schemaVersion") != COMMAND_SCHEMA_VERSION:
            raise OutstandingCommandError(
                "The existing command.json is not owned by this EA contract."
            )
        try:
            _flat_json(raw, exact_fields=COMMAND_FIELDS)
        except GatewayValidationError as error:
            raise OutstandingCommandError(
                "The existing command.json is not a safe flat EA command."
            ) from error
        return _ordered_packet(raw, COMMAND_FIELDS), True

    def _read_command_slot(self, channel_id: str) -> dict[str, object] | None:
        command, _ = self._read_command_slot_record(
            channel_id,
            allow_legacy_plain=False,
        )
        return command

    def _owned_command_slot(
        self,
        ledger: Mapping[str, object],
        channel_id: str,
    ) -> str | None:
        """Return the matching durable command ID or reject an orphan slot."""
        raw, legacy_plain = self._read_command_slot_record(
            channel_id,
            allow_legacy_plain=True,
        )
        if raw is None:
            return None
        command_id = str(raw.get("commandId") or "")
        commands = ledger.get("commands")
        entry = commands.get(command_id) if isinstance(commands, dict) else None
        if (
            not isinstance(entry, dict)
            or entry.get("command") != raw
            or raw.get("channelId") != channel_id
        ):
            raise OutstandingCommandError(
                "An unowned command.json already exists; reconcile it before publishing."
            )
        if legacy_plain and entry.get("outstanding") is not False:
            raise OutstandingCommandError(
                "An outstanding legacy command cannot be upgraded automatically.",
                code="legacy_unsigned_command_outstanding",
            )
        return command_id

    def _result(self, entry: Mapping[str, object], *, replay: bool) -> dict[str, object]:
        return {
            "ok": True,
            "kind": (
                "mt4_trade_command_existing"
                if replay
                else "mt4_trade_command_published"
            ),
            "idempotentReplay": replay,
            "command": _ordered_packet(entry["command"], COMMAND_FIELDS),
            "heartbeat": _ordered_packet(entry["heartbeat"], HEARTBEAT_FIELDS),
            "ledgerStatus": str(entry.get("status") or "unknown"),
            "outstanding": bool(entry.get("outstanding", True)),
            "queueFileName": "command.json",
        }

    def queue_trade_intent(self, intent: Mapping[str, object]) -> dict[str, object]:
        """Publish one command slot; never accept EA-owned sizing/risk policy."""
        normalized = self._normalize_intent(intent)
        self.ensure_signing_key(normalized["channelId"])
        now = self._now()
        command, heartbeat, backend_identity, request_digest, bar_key = self._build_packets(
            normalized,
            now=now,
        )
        command_id = str(command["commandId"])
        channel_id = str(command["channelId"])
        with self._lock:
            ledger = self._load_ledger()
            existing_id = ledger["idempotency"].get(request_digest)
            if existing_id:
                entry = ledger["commands"].get(existing_id)
                if not isinstance(entry, dict):
                    raise LedgerIntegrityError("Idempotency index points to no command.")
                if entry.get("outstanding"):
                    expires_at = int(entry["command"]["expiresAt"])
                    if expires_at <= _now_epoch(now):
                        entry["status"] = "expired_waiting_ack"
                        entry["updatedAt"] = _iso(now)
                        ledger = self._save_ledger(ledger)
                        entry = ledger["commands"][existing_id]
                    else:
                        fresh = self._fresh_heartbeat(entry["command"], now)
                        self._write_heartbeat(fresh)
                        slot = self._read_command_slot(channel_id)
                        if slot is None:
                            self._write_command(entry["command"])
                        elif slot != entry["command"]:
                            raise OutstandingCommandError(
                                "The EA command slot no longer matches its durable command."
                            )
                        entry["heartbeat"] = fresh
                        entry["updatedAt"] = _iso(now)
                        ledger = self._save_ledger(ledger)
                        entry = ledger["commands"][existing_id]
                return self._result(entry, replay=True)

            active_id = ledger.get("activeCommandId")
            if active_id:
                active = ledger["commands"].get(active_id)
                if not isinstance(active, dict):
                    raise LedgerIntegrityError("Active command points to no ledger entry.")
                raise OutstandingCommandError(
                    "Wait for a persisted terminal ACK before publishing another command."
                )
            # The EA intentionally keeps command.json after writing its ACK.
            # A terminal command that exactly matches the durable ledger is an
            # owned slot and may be atomically replaced by the next command.
            self._owned_command_slot(ledger, channel_id)
            if self._kill_switch_path(channel_id).exists():
                raise GatewaySafetyError(
                    "The EA kill switch marker is active.",
                    code="kill_switch_active",
                )
            claimed_id = ledger["barClaims"].get(bar_key)
            if claimed_id:
                if claimed_id not in ledger["commands"]:
                    raise LedgerIntegrityError("Bar claim points to no command.")
                raise OneOrderPerBarError(
                    "This channel, symbol, timeframe and closed bar is already claimed."
                )

            created_at = _iso(now)
            entry = {
                "wireSchemaVersion": COMMAND_SCHEMA_VERSION,
                "command": command,
                "heartbeat": heartbeat,
                "backendIdentity": backend_identity,
                "requestDigest": request_digest,
                "barKey": bar_key,
                "status": "writing",
                "outstanding": True,
                "createdAt": created_at,
                "updatedAt": created_at,
                "ack": None,
                "ackDigests": [],
                "eaSizingReported": False,
            }
            ledger["commands"][command_id] = entry
            ledger["idempotency"][request_digest] = command_id
            ledger["barClaims"][bar_key] = command_id
            ledger["activeCommandId"] = command_id
            ledger = self._save_ledger(ledger)
            self._write_heartbeat(heartbeat)
            self._write_command(command)
            ledger = self._load_ledger()
            entry = ledger["commands"][command_id]
            entry["status"] = "published"
            entry["updatedAt"] = _iso(self._now())
            ledger = self._save_ledger(ledger)
            return self._result(ledger["commands"][command_id], replay=False)

    def refresh_heartbeat(self) -> dict[str, object]:
        """Refresh the active command heartbeat without changing its identity."""
        now = self._now()
        with self._lock:
            ledger = self._load_ledger()
            active_id = ledger.get("activeCommandId")
            if not active_id:
                raise OutstandingCommandError("There is no outstanding command.")
            entry = ledger["commands"].get(active_id)
            if not isinstance(entry, dict) or not entry.get("outstanding"):
                raise LedgerIntegrityError("Active command state is inconsistent.")
            if int(entry["command"]["expiresAt"]) <= _now_epoch(now):
                entry["status"] = "expired_waiting_ack"
                entry["updatedAt"] = _iso(now)
                self._save_ledger(ledger)
                raise GatewaySafetyError(
                    "Cannot refresh an expired command.",
                    code="command_expired",
                )
            heartbeat = self._fresh_heartbeat(entry["command"], now)
            self._write_heartbeat(heartbeat)
            entry["heartbeat"] = heartbeat
            entry["updatedAt"] = _iso(now)
            ledger = self._save_ledger(ledger)
            return {
                "ok": True,
                "kind": "mt4_trade_heartbeat_refreshed",
                "commandId": active_id,
                "heartbeat": dict(ledger["commands"][active_id]["heartbeat"]),
            }

    def _ack_number(self, value: object, *, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise AckValidationError(f"ACK {field} must be an integer.", code=f"invalid_ack_{field}")
        if not -2_147_483_648 <= value <= 2_147_483_647:
            raise AckValidationError(f"ACK {field} is out of range.", code=f"invalid_ack_{field}")
        return value

    def _ack_optional_number(
        self,
        value: object,
        *,
        field: str,
        minimum: Decimal | None = None,
        maximum: Decimal = Decimal("1000000000"),
    ) -> int | float | None:
        if value is None:
            return None
        if isinstance(value, bool):
            raise AckValidationError(
                f"ACK {field} must be numeric or null.",
                code=f"invalid_ack_{field}",
            )
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise AckValidationError(
                f"ACK {field} must be numeric or null.",
                code=f"invalid_ack_{field}",
            ) from error
        if (
            not number.is_finite()
            or number > maximum
            or number < -maximum
            or (minimum is not None and number < minimum)
        ):
            raise AckValidationError(
                f"ACK {field} is outside the allowed range.",
                code=f"invalid_ack_{field}",
            )
        return _json_number(number.normalize())

    def _ack_optional_integer(self, value: object, *, field: str) -> int | None:
        if value is None:
            return None
        return self._ack_number(value, field=field)

    def _ack_ascii_text(self, value: object, *, field: str, maximum: int = 64) -> str:
        if not isinstance(value, str) or len(value) > maximum:
            raise AckValidationError(
                f"ACK {field} must be a short ASCII string.",
                code=f"invalid_ack_{field}",
            )
        try:
            value.encode("ascii")
        except UnicodeEncodeError as error:
            raise AckValidationError(
                f"ACK {field} must be a short ASCII string.",
                code=f"invalid_ack_{field}",
            ) from error
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise AckValidationError(
                f"ACK {field} contains control characters.",
                code=f"invalid_ack_{field}",
            )
        return value

    def _normalize_ack(
        self,
        ack: Mapping[str, object],
    ) -> tuple[dict[str, object], bool]:
        if not isinstance(ack, Mapping):
            raise AckValidationError("ACK must be an object.")
        unknown = sorted(set(ack) - ACK_ALLOWED_FIELDS)
        if unknown:
            raise AckValidationError(
                f"Unknown ACK fields: {', '.join(unknown)}",
                code="unknown_ack_field",
            )
        required = set(ACK_ALLOWED_FIELDS)
        missing = sorted(required - set(ack))
        if missing:
            raise AckValidationError(
                f"Missing ACK fields: {', '.join(missing)}",
                code="missing_ack_field",
            )
        if ack.get("schemaVersion") != ACK_SCHEMA_VERSION:
            raise AckValidationError("Unsupported ACK schema.", code="invalid_ack_schema")
        if ack.get("profile") != "special":
            raise AckValidationError("ACK profile mismatch.", code="invalid_ack_profile")
        command_id = str(ack.get("commandId") or "")
        idempotency_key = str(ack.get("idempotencyKey") or "")
        channel_id = str(ack.get("channelId") or "")
        if not COMMAND_ID_PATTERN.fullmatch(command_id):
            raise AckValidationError("Invalid ACK commandId.", code="invalid_ack_command_id")
        if not IDEMPOTENCY_KEY_PATTERN.fullmatch(idempotency_key):
            raise AckValidationError(
                "Invalid ACK idempotencyKey.",
                code="invalid_ack_idempotency_key",
            )
        if not SAFE_CHANNEL_PATTERN.fullmatch(channel_id):
            raise AckValidationError("Invalid ACK channelId.", code="invalid_ack_channel_id")
        snapshot_id = str(ack.get("snapshotId") or "").strip().lower()
        if not SHA256_PATTERN.fullmatch(snapshot_id):
            raise AckValidationError(
                "Invalid ACK snapshotId.",
                code="invalid_ack_snapshot_id",
            )
        snapshot_observed_at = self._ack_number(
            ack.get("snapshotObservedAt"),
            field="snapshot_observed_at",
        )
        bar_time = self._ack_number(ack.get("barTime"), field="bar_time")
        ea_closed_bar_time = self._ack_number(
            ack.get("eaClosedBarTime"),
            field="ea_closed_bar_time",
        )
        if min(snapshot_observed_at, bar_time, ea_closed_bar_time) < 946684800:
            raise AckValidationError(
                "Invalid ACK snapshot/bar time.",
                code="invalid_ack_snapshot_time",
            )
        try:
            reference_price = _number(
                ack.get("referencePrice"),
                field="ack_reference_price",
            )
        except GatewayValidationError as error:
            raise AckValidationError(
                "Invalid ACK referencePrice.",
                code="invalid_ack_reference_price",
            ) from error
        status = str(ack.get("status") or "").upper()
        if status not in ACK_STATUSES:
            raise AckValidationError("Invalid ACK status.", code="invalid_ack_status")
        reason_code = str(ack.get("reasonCode") or "").upper()
        if not SAFE_REASON_PATTERN.fullmatch(reason_code):
            raise AckValidationError("Invalid ACK reasonCode.", code="invalid_ack_reason")
        mode = str(ack.get("mode") or "").lower()
        if mode not in EA_MODES:
            raise AckValidationError("Invalid read-only EA mode.", code="invalid_ack_mode")
        observed_at = self._ack_number(ack.get("observedAt"), field="observed_at")
        if observed_at < 946684800:
            raise AckValidationError("Invalid ACK observedAt.", code="invalid_ack_observed_at")
        ticket_value = ack.get("ticket")
        ticket = None if ticket_value is None else self._ack_number(ticket_value, field="ticket")
        if ticket is not None and ticket <= 0:
            raise AckValidationError("ACK ticket must be positive.", code="invalid_ack_ticket")
        filled_price = self._ack_optional_number(
            ack.get("filledPrice"),
            field="filled_price",
            minimum=Decimal("0.00000001"),
        )
        filled_slippage_points = self._ack_optional_number(
            ack.get("filledSlippagePoints"),
            field="filled_slippage_points",
            minimum=Decimal("0"),
        )
        actual_stop_loss = self._ack_optional_number(
            ack.get("actualStopLoss"),
            field="actual_stop_loss",
            minimum=Decimal("0"),
        )
        actual_take_profit = self._ack_optional_number(
            ack.get("actualTakeProfit"),
            field="actual_take_profit",
            minimum=Decimal("0"),
        )
        actual_magic_number = self._ack_optional_integer(
            ack.get("actualMagicNumber"),
            field="actual_magic_number",
        )
        if actual_magic_number is not None and actual_magic_number <= 0:
            raise AckValidationError(
                "ACK actualMagicNumber must be positive.",
                code="invalid_ack_actual_magic_number",
            )
        actual_comment = self._ack_ascii_text(
            ack.get("actualComment"),
            field="actual_comment",
        )
        signature_verification_status = str(
            ack.get("signatureVerificationStatus") or ""
        ).upper()
        if signature_verification_status != "VERIFIED":
            raise AckValidationError(
                "ACK does not prove signed-envelope verification.",
                code="invalid_ack_signature_verification_status",
            )
        verification_status = str(ack.get("verificationStatus") or "").upper()
        if verification_status not in ACK_VERIFICATION_STATUSES:
            raise AckValidationError(
                "ACK verificationStatus is invalid.",
                code="invalid_ack_verification_status",
            )
        execution_state = str(ack.get("executionState") or "").upper()
        if execution_state not in ACK_EXECUTION_STATES:
            raise AckValidationError(
                "ACK executionState is invalid.",
                code="invalid_ack_execution_state",
            )
        closed_at = self._ack_optional_integer(ack.get("closedAt"), field="closed_at")
        if closed_at is not None and closed_at < 946684800:
            raise AckValidationError("ACK closedAt is invalid.", code="invalid_ack_closed_at")
        closed_pnl = self._ack_optional_number(ack.get("closedPnl"), field="closed_pnl")
        error_code = self._ack_number(ack.get("errorCode"), field="error_code")
        if not isinstance(ack.get("statePersisted"), bool):
            raise AckValidationError(
                "ACK statePersisted must be boolean.",
                code="invalid_ack_state_persisted",
            )
        # The EA reports its own FixedLot. Validate that it is a finite
        # positive scalar, then deliberately discard the value. It can only
        # become a read-only "reported" status and can never enter a command.
        try:
            ea_lot = Decimal(str(ack.get("fixedLot")))
        except (InvalidOperation, ValueError) as error:
            raise AckValidationError(
                "ACK EA sizing status is invalid.",
                code="invalid_ack_ea_sizing",
            ) from error
        if not ea_lot.is_finite() or ea_lot <= 0:
            raise AckValidationError(
                "ACK EA sizing status is invalid.",
                code="invalid_ack_ea_sizing",
            )
        execution_evidence = (
            filled_price,
            filled_slippage_points,
            actual_stop_loss,
            actual_take_profit,
            actual_magic_number,
        )
        if status == "EXECUTED":
            if (
                ticket is None
                or any(value is None for value in execution_evidence)
                or not actual_comment.startswith(f"HQ:{command_id}")
                or verification_status not in {"VERIFIED_OPEN", "VERIFIED_CLOSED"}
                or execution_state not in {"OPEN", "CLOSED"}
            ):
                raise AckValidationError(
                    "EXECUTED ACK lacks verified MT4 execution evidence.",
                    code="unverified_executed_ack",
                )
        elif status == "EXECUTION_UNKNOWN":
            if verification_status == "NOT_APPLICABLE" or execution_state == "NONE":
                raise AckValidationError(
                    "EXECUTION_UNKNOWN ACK must explain its verification state.",
                    code="invalid_execution_unknown_evidence",
                )
        elif (
            ticket is not None
            or any(value is not None for value in execution_evidence)
            or actual_comment
            or verification_status != "NOT_APPLICABLE"
            or execution_state != "NONE"
            or closed_at is not None
            or closed_pnl is not None
        ):
            raise AckValidationError(
                "Non-execution ACK cannot report execution evidence.",
                code="unexpected_ack_execution_evidence",
            )
        if execution_state == "CLOSED":
            if closed_at is None or closed_pnl is None:
                raise AckValidationError(
                    "CLOSED ACK requires close time and closed PnL.",
                    code="incomplete_ack_closed_outcome",
                )
        elif closed_at is not None or closed_pnl is not None:
            raise AckValidationError(
                "Only CLOSED ACK may report close outcome.",
                code="unexpected_ack_closed_outcome",
            )
        normalized = {
            "schemaVersion": ACK_SCHEMA_VERSION,
            "profile": "special",
            "commandId": command_id,
            "idempotencyKey": idempotency_key,
            "channelId": channel_id,
            "missionId": self._normalize_ack_identifier(
                ack.get("missionId"),
                field="ack_mission_id",
            ),
            "councilDecisionId": self._normalize_ack_identifier(
                ack.get("councilDecisionId"),
                field="ack_council_decision_id",
            ),
            "ownerAgentId": self._normalize_ack_identifier(
                ack.get("ownerAgentId"),
                field="ack_owner_agent_id",
            ),
            "snapshotId": snapshot_id,
            "snapshotObservedAt": snapshot_observed_at,
            "barTime": bar_time,
            "referencePrice": _json_number(reference_price),
            "eaClosedBarTime": ea_closed_bar_time,
            "status": status,
            "reasonCode": reason_code,
            "mode": mode,
            "action": str(ack.get("action") or "").upper(),
            "symbol": str(ack.get("symbol") or "").upper(),
            "timeframe": str(ack.get("timeframe") or "").upper(),
            "observedAt": observed_at,
            "ticket": ticket,
            "filledPrice": filled_price,
            "filledSlippagePoints": filled_slippage_points,
            "actualStopLoss": actual_stop_loss,
            "actualTakeProfit": actual_take_profit,
            "actualMagicNumber": actual_magic_number,
            "actualComment": actual_comment,
            "signatureVerificationStatus": signature_verification_status,
            "verificationStatus": verification_status,
            "executionState": execution_state,
            "closedAt": closed_at,
            "closedPnl": closed_pnl,
            "errorCode": error_code,
            "statePersisted": ack["statePersisted"],
        }
        _flat_json(normalized)
        return normalized, True

    def _bind_ack(
        self,
        entry: Mapping[str, object],
        ack: Mapping[str, object],
        *,
        reference_price_wire_decimals: int | None = None,
    ) -> str:
        command = entry["command"]
        for field in ("commandId", "idempotencyKey", "channelId"):
            if ack.get(field) != command.get(field):
                raise AckValidationError(
                    f"ACK {field} does not match the command.",
                    code=f"ack_{field}_mismatch",
                )
        for field in (
            "missionId",
            "councilDecisionId",
            "ownerAgentId",
            "snapshotId",
            "snapshotObservedAt",
            "barTime",
            "action",
            "symbol",
            "timeframe",
        ):
            if ack.get(field) != command.get(field):
                raise AckValidationError(
                    f"ACK {field} does not match the command.",
                    code=f"ack_{field}_mismatch",
                )
        price_binding = "exact"
        if ack.get("referencePrice") != command.get("referencePrice"):
            # Gateway EA <= 2.11 wrote the echoed command reference price with
            # the broker's display Digits.  A midpoint such as 4347.895 was
            # therefore written as 4347.90 and a safely rejected command could
            # remain outstanding forever.  Compatibility is intentionally
            # narrow: only a persisted REJECTED/no-execution ACK read from its
            # wire file may use the decimal precision present in that file.
            # Executed/unknown ACKs still require exact identity.
            compatible_rejected_ack = (
                reference_price_wire_decimals is not None
                and 0 <= reference_price_wire_decimals <= 8
                and ack.get("status") == "REJECTED"
                and ack.get("statePersisted") is True
                and ack.get("executionState") == "NONE"
                and ack.get("ticket") is None
                and ack.get("signatureVerificationStatus") == "VERIFIED"
            )
            try:
                quantum = Decimal(1).scaleb(-int(reference_price_wire_decimals or 0))
                rounded_command_price = Decimal(
                    str(command.get("referencePrice"))
                ).quantize(quantum, rounding=ROUND_HALF_UP)
                ack_reference_price = Decimal(str(ack.get("referencePrice")))
            except (InvalidOperation, TypeError, ValueError):
                compatible_rejected_ack = False
                rounded_command_price = Decimal(0)
                ack_reference_price = Decimal(1)
            if not compatible_rejected_ack or rounded_command_price != ack_reference_price:
                raise AckValidationError(
                    "ACK referencePrice does not match the command.",
                    code="ack_referencePrice_mismatch",
                )
            price_binding = "legacy_rejected_wire_rounding"
        if ack.get("eaClosedBarTime") != command.get("barTime"):
            raise AckValidationError(
                "ACK EA closed bar does not match the command bar.",
                code="ack_ea_closed_bar_time_mismatch",
            )
        return price_binding

    def ingest_ack(
        self,
        ack: Mapping[str, object],
        *,
        reference_price_wire_decimals: int | None = None,
    ) -> dict[str, object]:
        """Ingest one EA ACK and release the slot only on persisted final ACK."""
        normalized, ea_sizing_reported = self._normalize_ack(ack)
        ack_digest = _contract_digest(ACK_SCHEMA_VERSION, normalized)
        command_id = str(normalized["commandId"])
        with self._lock:
            ledger = self._load_ledger()
            entry = ledger["commands"].get(command_id)
            if not isinstance(entry, dict):
                raise AckValidationError(
                    "ACK references an unknown command.",
                    code="unknown_ack_command",
                )
            reference_price_binding = self._bind_ack(
                entry,
                normalized,
                reference_price_wire_decimals=reference_price_wire_decimals,
            )
            ack_digests = entry.get("ackDigests")
            if not isinstance(ack_digests, list):
                raise LedgerIntegrityError("ACK digest history is invalid.")
            if ack_digest in ack_digests:
                return {
                    "ok": True,
                    "kind": "mt4_trade_ack_existing",
                    "idempotentReplay": True,
                    "commandId": command_id,
                    "status": str(entry.get("status") or "unknown"),
                    "outstandingReleased": not bool(entry.get("outstanding")),
                    "ack": dict(entry.get("ack") or normalized),
                    "eaSizingStatus": "reported_read_only",
                    "referencePriceBinding": reference_price_binding,
                }
            current_status = str(entry.get("status") or "")
            next_status = str(normalized["status"])
            current_ack = entry.get("ack")
            persisted_upgrade = False
            if (
                isinstance(current_ack, dict)
                and current_status == f"ack_{next_status}"
                and next_status in TERMINAL_ACK_STATUSES
                and current_ack.get("statePersisted") is False
                and normalized.get("statePersisted") is True
            ):
                old_identity = {
                    key: value
                    for key, value in current_ack.items()
                    if key not in {"observedAt", "statePersisted"}
                }
                new_identity = {
                    key: value
                    for key, value in normalized.items()
                    if key not in {"observedAt", "statePersisted"}
                }
                persisted_upgrade = old_identity == new_identity
            if (
                current_status.startswith("ack_")
                and not entry.get("outstanding")
                and not persisted_upgrade
            ):
                raise AckConflictError("Command already has a different terminal ACK.")
            if current_status == "ack_EXECUTING" and next_status == "EXECUTING":
                raise AckConflictError("A different EXECUTING ACK already exists.")
            if (
                current_status.startswith("ack_")
                and current_status != "ack_EXECUTING"
                and not persisted_upgrade
            ):
                raise AckConflictError("Command already has a terminal ACK.")

            terminal = next_status in TERMINAL_ACK_STATUSES
            persisted_terminal = terminal and normalized["statePersisted"] is True
            entry["status"] = f"ack_{next_status}"
            entry["updatedAt"] = _iso(self._now())
            entry["ack"] = normalized
            entry["eaSizingReported"] = ea_sizing_reported
            ack_digests.append(ack_digest)
            if persisted_terminal:
                entry["outstanding"] = False
                if ledger.get("activeCommandId") == command_id:
                    ledger["activeCommandId"] = None
            else:
                entry["outstanding"] = True
            ledger = self._save_ledger(ledger)
            persisted = ledger["commands"][command_id]
            return {
                "ok": True,
                "kind": "mt4_trade_ack_ingested",
                "idempotentReplay": False,
                "commandId": command_id,
                "status": persisted["status"],
                "outstandingReleased": not bool(persisted["outstanding"]),
                "ack": dict(persisted["ack"]),
                "eaSizingStatus": (
                    "reported_read_only"
                    if persisted.get("eaSizingReported")
                    else "not_reported"
                ),
                "referencePriceBinding": reference_price_binding,
            }

    def _validate_ack_path(self, path: Path) -> tuple[str, str]:
        try:
            relative = path.resolve().relative_to(self.file_common_root.resolve())
        except (OSError, ValueError) as error:
            raise AckValidationError("ACK path is outside FILE_COMMON.", code="unsafe_ack_path") from error
        parts = relative.parts
        if (
            len(parts) != 5
            or parts[0] != "MetafxHQ"
            or parts[2] != "trade-gateway"
            or parts[3] != "acks"
            or not SAFE_CHANNEL_PATTERN.fullmatch(parts[1])
            or not parts[4].endswith(".json")
        ):
            raise AckValidationError("ACK path is not an EA ACK path.", code="unsafe_ack_path")
        return parts[1], parts[4][:-5]

    def ingest_ack_file(self, path: str | Path) -> dict[str, object]:
        ack_path = Path(path)
        channel_id, file_command_id = self._validate_ack_path(ack_path)
        try:
            raw_text = ack_path.read_text(encoding="ascii")
            raw = json.loads(raw_text)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AckValidationError("ACK file is unreadable.", code="invalid_ack_json") from error
        if not isinstance(raw, dict):
            raise AckValidationError("ACK file must contain an object.", code="invalid_ack_json")
        if raw.get("channelId") != channel_id or raw.get("commandId") != file_command_id:
            raise AckValidationError(
                "ACK file path identity does not match its payload.",
                code="ack_path_identity_mismatch",
            )
        reference_price_matches = list(ACK_REFERENCE_PRICE_PATTERN.finditer(raw_text))
        reference_price_wire_decimals = None
        if len(reference_price_matches) == 1:
            fraction = reference_price_matches[0].group(2)
            reference_price_wire_decimals = len(fraction or "")
        return self.ingest_ack(
            raw,
            reference_price_wire_decimals=reference_price_wire_decimals,
        )

    def ingest_pending_acks(self) -> list[dict[str, object]]:
        """Ingest only the current outstanding ACK; ignore last-invalid.json."""
        with self._lock:
            ledger = self._load_ledger()
            active_id = ledger.get("activeCommandId")
            if not active_id:
                return []
            entry = ledger["commands"].get(active_id)
            if not isinstance(entry, dict):
                raise LedgerIntegrityError("Active command points to no ledger entry.")
            path = self._ack_path(entry["command"]["channelId"], active_id)
        if not path.is_file():
            return []
        try:
            return [self.ingest_ack_file(path)]
        except TradeGatewayError as error:
            return [{
                "ok": False,
                "kind": "mt4_trade_ack_rejected",
                "code": error.code,
                "fileName": path.name,
            }]

    def expire_pending(self) -> dict[str, object]:
        """Mark an expired slot but retain it until a persisted terminal ACK."""
        now = self._now()
        expired_ids: list[str] = []
        with self._lock:
            ledger = self._load_ledger()
            active_id = ledger.get("activeCommandId")
            if active_id:
                entry = ledger["commands"].get(active_id)
                if not isinstance(entry, dict):
                    raise LedgerIntegrityError("Active command points to no ledger entry.")
                if (
                    entry.get("outstanding")
                    and int(entry["command"]["expiresAt"]) <= _now_epoch(now)
                    and entry.get("status") != "expired_waiting_ack"
                ):
                    entry["status"] = "expired_waiting_ack"
                    entry["updatedAt"] = _iso(now)
                    expired_ids.append(active_id)
                    ledger = self._save_ledger(ledger)
        return {
            "ok": True,
            "kind": "mt4_trade_commands_expired",
            "expiredCount": len(expired_ids),
            "commandIds": expired_ids,
            "slotReleased": False,
        }

    def read_heartbeat(self, channel_id: str) -> dict[str, object] | None:
        channel_id = self._validated_channel_id(channel_id)
        path = self._heartbeat_path(channel_id)
        if not path.is_file():
            return None
        try:
            value = _strict_json_object(path.read_text(encoding="ascii"))
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            raise GatewayValidationError(
                "Heartbeat file is unreadable.",
                code="invalid_heartbeat_file",
            ) from error
        if not isinstance(value, dict):
            raise GatewayValidationError(
                "Heartbeat file does not match the EA contract.",
                code="invalid_heartbeat_file",
            )
        try:
            return self._verify_signed_envelope(
                value,
                kind="heartbeat",
                channel_id=channel_id,
                fields=HEARTBEAT_FIELDS,
                inner_schema=HEARTBEAT_SCHEMA_VERSION,
            )
        except TradeGatewayError as error:
            raise GatewayValidationError(
                "Heartbeat signed envelope failed authentication.",
                code=error.code,
            ) from error

    def read_command(self, command_id: str) -> dict[str, object] | None:
        if not COMMAND_ID_PATTERN.fullmatch(str(command_id or "")):
            raise GatewayValidationError("Invalid commandId.", code="invalid_command_id")
        with self._lock:
            entry = self._load_ledger()["commands"].get(command_id)
            if not isinstance(entry, dict):
                return None
            return {
                "wireSchemaVersion": str(entry["wireSchemaVersion"]),
                "command": _ordered_packet(entry["command"], COMMAND_FIELDS),
                "heartbeat": _ordered_packet(entry["heartbeat"], HEARTBEAT_FIELDS),
                "backendIdentity": dict(entry["backendIdentity"]),
                "status": str(entry.get("status") or "unknown"),
                "outstanding": bool(entry.get("outstanding")),
                "ack": dict(entry["ack"]) if isinstance(entry.get("ack"), dict) else None,
                "eaSizingStatus": (
                    "reported_read_only"
                    if entry.get("eaSizingReported")
                    else "not_reported"
                ),
                "createdAt": entry.get("createdAt"),
                "updatedAt": entry.get("updatedAt"),
            }

    def read_outcome(self, command_id: str) -> dict[str, object] | None:
        """Read the EA's independently refreshed OPEN/CLOSED outcome artifact."""
        if not COMMAND_ID_PATTERN.fullmatch(str(command_id or "")):
            raise GatewayValidationError("Invalid commandId.", code="invalid_command_id")
        with self._lock:
            ledger = self._load_ledger()
            entry = ledger["commands"].get(command_id)
            if not isinstance(entry, dict):
                return None
            command = dict(entry["command"])
            channel_id = str(command["channelId"])
        path = self._outcome_path(channel_id, command_id)
        if not path.is_file():
            return None
        try:
            outcome = json.loads(path.read_text(encoding="ascii"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise GatewayValidationError(
                "MT4 outcome file is unreadable.",
                code="invalid_mt4_outcome",
            ) from error
        if (
            not isinstance(outcome, dict)
            or set(outcome) != set(OUTCOME_FIELDS)
            or outcome.get("schemaVersion") != OUTCOME_SCHEMA_VERSION
            or outcome.get("channelId") != channel_id
            or outcome.get("commandId") != command_id
            or outcome.get("executionState") not in {"OPEN", "CLOSED"}
        ):
            raise GatewayValidationError(
                "MT4 outcome file does not match the command.",
                code="invalid_mt4_outcome",
            )
        try:
            _flat_json(outcome, exact_fields=OUTCOME_FIELDS)
        except GatewayValidationError as error:
            raise GatewayValidationError(
                "MT4 outcome file is outside the outcome contract.",
                code="invalid_mt4_outcome",
            ) from error
        if (
            outcome["executionState"] == "CLOSED"
            and (outcome.get("closedAt") is None or outcome.get("closedPnl") is None)
        ) or (
            outcome["executionState"] == "OPEN"
            and (outcome.get("closedAt") is not None or outcome.get("closedPnl") is not None)
        ):
            raise GatewayValidationError(
                "MT4 outcome lifecycle fields are inconsistent.",
                code="invalid_mt4_outcome",
            )
        integer_fields = ("observedAt", "ticket", "openedAt", "magicNumber")
        if any(
            isinstance(outcome.get(field), bool)
            or not isinstance(outcome.get(field), int)
            or int(outcome[field]) <= 0
            for field in integer_fields
        ):
            raise GatewayValidationError(
                "MT4 outcome integer evidence is invalid.",
                code="invalid_mt4_outcome",
            )
        numeric_fields = ("openPrice", "stopLoss", "takeProfit", "lots")
        if any(
            isinstance(outcome.get(field), bool)
            or not isinstance(outcome.get(field), (int, float))
            or not math.isfinite(float(outcome[field]))
            or float(outcome[field]) <= 0
            for field in numeric_fields
        ):
            raise GatewayValidationError(
                "MT4 outcome price/lot evidence is invalid.",
                code="invalid_mt4_outcome",
            )
        if (
            outcome.get("symbol") != command.get("symbol")
            or outcome.get("action") != command.get("action")
            or outcome.get("comment") != f"HQ:{command_id}"
        ):
            raise GatewayValidationError(
                "MT4 outcome identity is invalid.",
                code="invalid_mt4_outcome",
            )
        if outcome["executionState"] == "CLOSED" and (
            isinstance(outcome.get("closedAt"), bool)
            or not isinstance(outcome.get("closedAt"), int)
            or int(outcome["closedAt"]) < int(outcome["openedAt"])
            or isinstance(outcome.get("closedPnl"), bool)
            or not isinstance(outcome.get("closedPnl"), (int, float))
            or not math.isfinite(float(outcome["closedPnl"]))
        ):
            raise GatewayValidationError(
                "MT4 closed outcome evidence is invalid.",
                code="invalid_mt4_outcome",
            )
        return _ordered_packet(outcome, OUTCOME_FIELDS)

    def quarantine_execution_unknown(
        self,
        command_id: str,
        *,
        expected_ledger_revision: int,
    ) -> dict[str, object]:
        """Fail closed, retain the bar claim, and release only the durable slot.

        This cannot turn an uncertain execution into EXECUTED/FAILED.  It first
        creates the channel kill switch, then marks the exact outstanding
        EXECUTION_UNKNOWN command as quarantined using optimistic concurrency.
        """
        if not COMMAND_ID_PATTERN.fullmatch(str(command_id or "")):
            raise GatewayValidationError("Invalid commandId.", code="invalid_command_id")
        if (
            isinstance(expected_ledger_revision, bool)
            or not isinstance(expected_ledger_revision, int)
            or expected_ledger_revision < 0
        ):
            raise GatewayValidationError(
                "Expected ledger revision is invalid.",
                code="invalid_ledger_revision",
            )
        with self._lock:
            ledger = self._load_ledger()
            if ledger["revision"] != expected_ledger_revision:
                raise GatewaySafetyError(
                    "Trade ledger changed; refresh before quarantining.",
                    code="stale_ledger_revision",
                )
            if ledger.get("activeCommandId") != command_id:
                raise GatewaySafetyError(
                    "Only the active uncertain command can be quarantined.",
                    code="execution_unknown_not_active",
                )
            entry = ledger["commands"].get(command_id)
            if (
                not isinstance(entry, dict)
                or entry.get("status") != "ack_EXECUTION_UNKNOWN"
                or entry.get("outstanding") is not True
                or not isinstance(entry.get("ack"), dict)
                or entry["ack"].get("status") != "EXECUTION_UNKNOWN"
            ):
                raise GatewaySafetyError(
                    "Command is not a durable EXECUTION_UNKNOWN state.",
                    code="execution_unknown_not_confirmed",
                )
            channel_id = str(entry["command"]["channelId"])
            kill_path = self._kill_switch_path(channel_id)
            if not kill_path.exists():
                _atomic_write_store(kill_path, {
                    "schemaVersion": "metafx-hq-mt4-kill-switch-v1",
                    "reasonCode": "EXECUTION_UNKNOWN_QUARANTINED",
                    "commandId": command_id,
                    "createdAt": _iso(self._now()),
                })
            entry["status"] = "quarantined_execution_unknown"
            entry["outstanding"] = False
            entry["updatedAt"] = _iso(self._now())
            entry["recovery"] = {
                "action": "quarantine",
                "reasonCode": "EXECUTION_UNKNOWN_REQUIRES_OPERATOR_RECONCILIATION",
                "killSwitchActive": True,
                "barClaimRetained": True,
                "recoveredAt": _iso(self._now()),
            }
            ledger["activeCommandId"] = None
            ledger = self._save_ledger(ledger)
            return {
                "ok": True,
                "kind": "mt4_execution_unknown_quarantined",
                "commandId": command_id,
                "status": ledger["commands"][command_id]["status"],
                "killSwitchActive": True,
                "barClaimRetained": (
                    ledger["barClaims"].get(entry["barKey"]) == command_id
                ),
                "slotReleased": True,
                "ledgerRevision": ledger["revision"],
            }

    def status(self) -> dict[str, object]:
        with self._lock:
            ledger = self._load_ledger()
            counts: dict[str, int] = {}
            for entry in ledger["commands"].values():
                status = str(entry.get("status") or "unknown")
                counts[status] = counts.get(status, 0) + 1
            latest_command_id = None
            if ledger["commands"]:
                latest_command_id = max(
                    ledger["commands"],
                    key=lambda command_id: str(
                        ledger["commands"][command_id].get("updatedAt")
                        or ledger["commands"][command_id].get("createdAt")
                        or ""
                    ),
                )
            return {
                "schemaVersion": "metafx-mt4-trade-gateway-status-v2",
                "ledgerSchemaVersion": LEDGER_SCHEMA_VERSION,
                "commandSchemaVersion": COMMAND_SCHEMA_VERSION,
                "heartbeatSchemaVersion": HEARTBEAT_SCHEMA_VERSION,
                "ackSchemaVersion": ACK_SCHEMA_VERSION,
                "signedEnvelopeSchemaVersion": SIGNED_ENVELOPE_SCHEMA_VERSION,
                "signatureAlgorithm": SIGNATURE_ALGORITHM,
                "commandTtlSeconds": self.command_ttl_seconds,
                "heartbeatTtlSeconds": self.heartbeat_ttl_seconds,
                "commandCount": len(ledger["commands"]),
                "activeCommandId": ledger.get("activeCommandId"),
                "latestCommandId": latest_command_id,
                "singleOutstanding": True,
                "eaOwnsExecutionPolicy": True,
                "eaSizingPolicy": "ea_input_only",
                "signedCommandRequiredForLive": True,
                "signedCommandVerificationAvailable": True,
                "liveExecutionAvailable": True,
                "liveBlockReason": None,
                "executionUnknownQuarantineAvailable": True,
                "outcomeTrackingAvailable": True,
                "byStatus": counts,
                "ledgerRevision": ledger["revision"],
            }


def queue_trade_intent(
    gateway: MT4TradeGateway,
    intent: Mapping[str, object],
) -> dict[str, object]:
    """Import-friendly adapter without module-global state."""
    return gateway.queue_trade_intent(intent)


def ingest_trade_ack(
    gateway: MT4TradeGateway,
    ack: Mapping[str, object],
) -> dict[str, object]:
    """Import-friendly ACK adapter without module-global state."""
    return gateway.ingest_ack(ack)


def read_trade_outcome(
    gateway: MT4TradeGateway,
    command_id: str,
) -> dict[str, object] | None:
    """Import-friendly read-only outcome adapter."""
    return gateway.read_outcome(command_id)


def quarantine_trade_execution_unknown(
    gateway: MT4TradeGateway,
    command_id: str,
    *,
    expected_ledger_revision: int,
) -> dict[str, object]:
    """Backend-only fail-closed recovery adapter; never retries an order."""
    return gateway.quarantine_execution_unknown(
        command_id,
        expected_ledger_revision=expected_ledger_revision,
    )
