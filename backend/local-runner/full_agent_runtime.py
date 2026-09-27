"""Persistent, secret-free conversation state for the Full Agent runtime.

This module deliberately does *not* execute tools.  It owns the durable state
that a later bridge/orchestrator can use: agent threads, bounded history,
model/reasoning/mode settings, idempotent turn requests, interrupt markers and
approval classification.  The JSON store is local, atomically replaced and
must never contain credentials or authentication material.

The public read models are safe to return to the frontend.  Internal
idempotency digests and storage paths are never exposed.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import secrets
import stat
import threading
import time
import unicodedata
import uuid
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STORE_FILENAME = "full-agent-runtime-v1.json"
LOCK_FILENAME = ".full-agent-runtime.lock"
APPROVAL_JOURNAL_SCHEMA_VERSION = 1
APPROVAL_JOURNAL_FILENAME = "full-agent-approval-v1.json"
APPROVAL_JOURNAL_LOCK_FILENAME = ".full-agent-approval.lock"

DEFAULT_MODEL_ALLOWLIST = (
    "gpt-6-astra",
    "gpt-6-sol",
    "gpt-6-luna",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "gpt-5.5",
)
DEFAULT_REASONING_ALLOWLIST = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
    "ultra",
)
CAPABILITY_MODES: dict[str, tuple[str, ...]] = {
    "chat": ("conversation",),
    "workspace": (
        "conversation",
        "workspace_read",
        "workspace_write",
        "shell",
        "git",
    ),
    "computer": (
        "conversation",
        "browser",
        "computer_use",
    ),
    "full": (
        "conversation",
        "workspace_read",
        "workspace_write",
        "shell",
        "git",
        "browser",
        "computer_use",
        "mcp",
        "plugin",
        "external_action",
    ),
}

EVENT_ROLES = frozenset({"user", "assistant", "system", "tool"})
EVENT_TYPES = frozenset(
    {
        "message",
        "system_notice",
        "tool_request",
        "tool_result",
        "approval_request",
        "approval_decision",
        "error",
    }
)
TURN_STATES = frozenset(
    {"queued", "running", "interrupt_requested", "completed", "failed", "cancelled"}
)
TERMINAL_TURN_STATES = frozenset({"completed", "failed", "cancelled"})

MAX_THREADS = 256
MAX_THREADS_PER_AGENT = 64
MAX_EVENTS_PER_THREAD = 500
# A newly admitted Turn must be able to durably record its user prompt, the
# runner's started marker and exactly one terminal assistant/error event.
TURN_EVENT_RESERVE = 3
MAX_TURNS_PER_THREAD = 250
MAX_INTERRUPT_KEYS_PER_THREAD = 250
MAX_CONTENT_CHARS = 32_768
MAX_TITLE_CHARS = 160
MAX_METADATA_BYTES = 8_192
MAX_STORE_BYTES = 16 * 1024 * 1024
MAX_LIST_LIMIT = 200
MAX_APPROVAL_JOURNAL_BYTES = 4 * 1024 * 1024
MAX_APPROVAL_RECORDS = 4096
# Committed/aborted tombstones remain replayable for at least 24 hours. Once
# this window has elapsed they may be compacted on startup or immediately
# before admitting a new approval request. Pending and decision_recorded
# entries are never eligible for compaction.
APPROVAL_REPLAY_RETENTION_SECONDS = 24 * 60 * 60

_AGENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_BACKEND_THREAD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$")
_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{7,191}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BIDI_CONTROL_RE = re.compile(r"[\u202a-\u202e\u2066-\u2069]")

_SENSITIVE_METADATA_KEYS = frozenset(
    {
        "password",
        "passwd",
        "apikey",
        "accesstoken",
        "refreshtoken",
        "idtoken",
        "clientsecret",
        "authorization",
        "cookie",
        "sessioncookie",
        "credential",
        "credentials",
        "brokerpassword",
        "telegramtoken",
        "privatekey",
    }
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|"
    r"client[_-]?secret|password|passwd|authorization|cookie|telegram[_-]?token|"
    r"broker[_-]?password|private[_-]?key)\b\s*[:=]\s*[\"']?([^\s\"',;]{8,})"
)
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bya29\.[A-Za-z0-9_-]{20,}\b"),
    # Google OAuth desktop-client secrets and Telegram bot tokens can be
    # pasted without a ``client_secret=`` / ``telegram_token=`` label.  Match
    # their provider-defined shapes before any event reaches durable history.
    re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?<![A-Za-z0-9])\d{6,12}:[A-Za-z0-9_-]{30,100}(?![A-Za-z0-9_-])"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
    ),
)
_PLACEHOLDER_MARKERS = ("redacted", "example", "placeholder", "your_", "<", "***")


class FullAgentRuntimeError(RuntimeError):
    """Fail-closed error with a stable, frontend-safe code."""

    def __init__(self, code: str, message: str, *, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status

    def as_dict(self) -> dict[str, Any]:
        return {"ok": False, "error": {"code": self.code, "message": str(self)}}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _canonical_metadata_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _is_placeholder(value: str) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def _reject_secret_text(value: str) -> None:
    for pattern in _SECRET_PATTERNS:
        if pattern.search(value):
            raise FullAgentRuntimeError(
                "secret_rejected",
                "Authentication or secret material cannot be stored in Agent history.",
                status=422,
            )
    for match in _SECRET_ASSIGNMENT_RE.finditer(value):
        if not _is_placeholder(match.group(2)):
            raise FullAgentRuntimeError(
                "secret_rejected",
                "Authentication or secret material cannot be stored in Agent history.",
                status=422,
            )


def _plain_text(value: Any, *, field: str, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise FullAgentRuntimeError("invalid_request", f"{field} must be text.", status=422)
    normalized = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    normalized = _BIDI_CONTROL_RE.sub("", _CONTROL_RE.sub("", normalized)).strip()
    if not normalized and not allow_empty:
        raise FullAgentRuntimeError("invalid_request", f"{field} is required.", status=422)
    if len(normalized) > maximum:
        raise FullAgentRuntimeError(
            "request_too_large", f"{field} exceeds the allowed size.", status=413
        )
    try:
        normalized.encode("utf-8")
    except UnicodeEncodeError as error:
        raise FullAgentRuntimeError(
            "invalid_request", f"{field} contains invalid Unicode.", status=422
        ) from error
    _reject_secret_text(normalized)
    return normalized


def _identifier(value: Any, *, field: str, pattern: re.Pattern[str] = _IDENTIFIER_RE) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value.strip()) is None:
        raise FullAgentRuntimeError("invalid_request", f"{field} is invalid.", status=422)
    return value.strip()


def _idempotency_key(value: Any, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or _IDEMPOTENCY_RE.fullmatch(value.strip()) is None:
        raise FullAgentRuntimeError(
            "invalid_idempotency_key",
            "A stable idempotency key of 8-192 safe characters is required.",
            status=422,
        )
    _reject_secret_text(value)
    return value.strip()


def _key_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request_digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_metadata(value: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        raise FullAgentRuntimeError(
            "invalid_metadata", "Event metadata is nested too deeply.", status=422
        )
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            raise FullAgentRuntimeError(
                "invalid_metadata", "Event metadata must contain finite values.", status=422
            )
        return value
    if isinstance(value, str):
        return _plain_text(value, field="metadata value", maximum=2_048, allow_empty=True)
    if isinstance(value, list):
        if len(value) > 64:
            raise FullAgentRuntimeError(
                "invalid_metadata", "Event metadata contains too many items.", status=422
            )
        return [_safe_metadata(item, depth=depth + 1) for item in value]
    if isinstance(value, Mapping):
        if len(value) > 64:
            raise FullAgentRuntimeError(
                "invalid_metadata", "Event metadata contains too many fields.", status=422
            )
        result: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            if not isinstance(raw_key, str) or not raw_key or len(raw_key) > 80:
                raise FullAgentRuntimeError(
                    "invalid_metadata", "Event metadata contains an invalid field.", status=422
                )
            safe_key = _plain_text(
                raw_key, field="metadata field", maximum=80, allow_empty=False
            )
            if safe_key != raw_key or safe_key in result:
                raise FullAgentRuntimeError(
                    "invalid_metadata", "Event metadata contains an invalid field.", status=422
                )
            if _canonical_metadata_key(safe_key) in _SENSITIVE_METADATA_KEYS:
                raise FullAgentRuntimeError(
                    "secret_rejected",
                    "Authentication or secret fields cannot be stored in Agent history.",
                    status=422,
                )
            result[safe_key] = _safe_metadata(raw_value, depth=depth + 1)
        return result
    raise FullAgentRuntimeError(
        "invalid_metadata", "Event metadata must be JSON-safe.", status=422
    )


def _sanitize_metadata(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise FullAgentRuntimeError(
            "invalid_metadata", "Event metadata must be an object.", status=422
        )
    result = _safe_metadata(value)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_METADATA_BYTES:
        raise FullAgentRuntimeError(
            "request_too_large", "Event metadata exceeds the allowed size.", status=413
        )
    return result


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & reparse_flag)
    except FileNotFoundError:
        return False


def _validate_existing_chain(path: Path) -> None:
    for candidate in reversed((path, *path.parents)):
        if not candidate.exists():
            continue
        if _is_reparse_or_symlink(candidate):
            raise FullAgentRuntimeError(
                "unsafe_storage_path",
                "Agent storage cannot use symbolic links or reparse points.",
                status=409,
            )


def _secure_storage_root(storage_root: str | os.PathLike[str]) -> Path:
    raw = Path(storage_root).expanduser()
    if not raw.is_absolute() or ".." in raw.parts:
        raise FullAgentRuntimeError(
            "unsafe_storage_path", "Agent storage must be an absolute local path.", status=422
        )
    _validate_existing_chain(raw)
    raw.mkdir(parents=True, exist_ok=True, mode=0o700)
    _validate_existing_chain(raw)
    if not raw.is_dir():
        raise FullAgentRuntimeError(
            "unsafe_storage_path", "Agent storage path is not a directory.", status=409
        )
    resolved = raw.resolve(strict=True)
    if resolved != raw.resolve(strict=False):
        raise FullAgentRuntimeError(
            "unsafe_storage_path", "Agent storage path escaped its local boundary.", status=409
        )
    with contextlib.suppress(OSError):
        os.chmod(resolved, 0o700)
    return resolved


class _InterprocessLock:
    def __init__(self, path: Path, timeout_seconds: float = 10.0) -> None:
        self.path = path
        self.timeout_seconds = max(0.1, min(float(timeout_seconds), 30.0))
        self.handle: Any = None
        self._unlock: Callable[[], None] | None = None

    def __enter__(self) -> "_InterprocessLock":
        if _is_reparse_or_symlink(self.path):
            raise FullAgentRuntimeError(
                "unsafe_storage_path", "Agent storage lock is unsafe.", status=409
            )
        flags = os.O_CREAT | os.O_RDWR
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(self.path, flags, 0o600)
        self.handle = os.fdopen(descriptor, "r+b", buffering=0)
        if self.handle.seek(0, os.SEEK_END) == 0:
            self.handle.write(b"\0")
            self.handle.flush()
            os.fsync(self.handle.fileno())
        deadline = time.monotonic() + self.timeout_seconds
        if os.name == "nt":
            import msvcrt

            while True:
                self.handle.seek(0)
                try:
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
                    self._unlock = lambda: msvcrt.locking(
                        self.handle.fileno(), msvcrt.LK_UNLCK, 1
                    )
                    break
                except OSError as error:
                    if time.monotonic() >= deadline:
                        self.handle.close()
                        self.handle = None
                        raise FullAgentRuntimeError(
                            "store_busy", "Agent history is busy. Please retry.", status=409
                        ) from error
                    time.sleep(0.025)
        else:
            import fcntl

            while True:
                try:
                    fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._unlock = lambda: fcntl.flock(
                        self.handle.fileno(), fcntl.LOCK_UN
                    )
                    break
                except BlockingIOError as error:
                    if time.monotonic() >= deadline:
                        self.handle.close()
                        self.handle = None
                        raise FullAgentRuntimeError(
                            "store_busy", "Agent history is busy. Please retry.", status=409
                        ) from error
                    time.sleep(0.025)
        if _is_reparse_or_symlink(self.path):
            self.__exit__(None, None, None)
            raise FullAgentRuntimeError(
                "unsafe_storage_path", "Agent storage lock is unsafe.", status=409
            )
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> bool:
        try:
            if self.handle is not None and self._unlock is not None:
                self.handle.seek(0)
                self._unlock()
        finally:
            if self.handle is not None:
                self.handle.close()
            self.handle = None
            self._unlock = None
        return False


class FullAgentApprovalJournal:
    """Durable, secret-free one-shot approval claims and tombstones.

    This store is deliberately separate from the conversation store so adding
    approval crash recovery cannot invalidate existing thread history.  It
    never stores raw SDK parameters, commands, paths, decision nonces or
    idempotency keys.  A newly constructed owner fail-closes every unfinished
    record because the original SDK request cannot be resumed after restart.
    Terminal tombstones remain replayable for at least
    ``APPROVAL_REPLAY_RETENTION_SECONDS`` and may be compacted only after that
    window. Pending and decision-recorded entries are never compacted.

    The current pinned SDK still has no deferred server-request response API;
    this journal is therefore an activation prerequisite, not permission to
    enable Workspace execution by itself.
    """

    _STATES = frozenset({"pending", "decision_recorded", "committed", "aborted"})
    _DECISIONS = frozenset({"accept_once", "decline"})

    def __init__(
        self,
        storage_root: str | os.PathLike[str],
        *,
        now: Callable[[], str] = _utc_now,
        now_epoch: Callable[[], float] = time.time,
    ) -> None:
        self._root = _secure_storage_root(storage_root)
        self._store_path = self._root / APPROVAL_JOURNAL_FILENAME
        self._lock_path = self._root / APPROVAL_JOURNAL_LOCK_FILENAME
        self._lock = threading.RLock()
        self._now = now
        self._now_epoch = now_epoch
        self._recover_unfinished()

    @property
    def storage_kind(self) -> str:
        return "local_secret_free_atomic_json"

    @staticmethod
    def _digest_secret(value: Any, *, field: str) -> str:
        if not isinstance(value, str) or not value or len(value) > 512:
            raise FullAgentRuntimeError(
                "invalid_approval_request", f"{field} is invalid.", status=422
            )
        try:
            encoded = value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise FullAgentRuntimeError(
                "invalid_approval_request", f"{field} is invalid.", status=422
            ) from error
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _sha256(value: Any, *, field: str) -> str:
        normalized = str(value or "").lower()
        if re.fullmatch(r"[a-f0-9]{64}", normalized) is None:
            raise FullAgentRuntimeError(
                "invalid_approval_request", f"{field} is invalid.", status=422
            )
        return normalized

    @staticmethod
    def _approval_id(value: Any, *, field: str) -> str:
        return _identifier(value, field=field)

    @staticmethod
    def _epoch(value: Any, *, field: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise FullAgentRuntimeError(
                "invalid_approval_request", f"{field} is invalid.", status=422
            )
        normalized = float(value)
        if normalized <= 0 or normalized != normalized or normalized in {
            float("inf"),
            float("-inf"),
        }:
            raise FullAgentRuntimeError(
                "invalid_approval_request", f"{field} is invalid.", status=422
            )
        return normalized

    def register_pending(self, request: Mapping[str, Any], *, expires_epoch: float) -> dict[str, Any]:
        """Persist the immutable request binding before it is published."""

        if not isinstance(request, Mapping):
            raise FullAgentRuntimeError(
                "invalid_approval_request", "Approval request is invalid.", status=422
            )
        request_id = self._approval_id(request.get("requestId"), field="requestId")
        method = self._approval_id(request.get("method"), field="method")
        action_type = self._approval_id(request.get("actionType"), field="actionType")
        thread_id = self._approval_id(request.get("threadId"), field="threadId")
        turn_id = self._approval_id(request.get("turnId"), field="turnId")
        item_id = self._approval_id(request.get("itemId"), field="itemId")
        payload_hash = self._sha256(request.get("requestDigest"), field="requestDigest")
        nonce_hash = self._digest_secret(request.get("decisionNonce"), field="decisionNonce")
        created_at = _plain_text(
            request.get("createdAt"), field="createdAt", maximum=64
        )
        expires_at = _plain_text(
            request.get("expiresAt"), field="expiresAt", maximum=64
        )
        expiry = self._epoch(expires_epoch, field="expiresEpoch")
        now_epoch = self._now_epoch()
        if expiry <= now_epoch:
            raise FullAgentRuntimeError(
                "approval_expired", "Approval request has expired.", status=409
            )
        record = {
            "requestId": request_id,
            "method": method,
            "actionType": action_type,
            "threadId": thread_id,
            "turnId": turn_id,
            "itemId": item_id,
            "payloadHash": payload_hash,
            "decisionNonceHash": nonce_hash,
            "createdAt": created_at,
            "expiresAt": expires_at,
            "expiresEpoch": expiry,
            "singleUse": True,
            "singleUseConsumed": False,
            "state": "pending",
            "requestedDecision": None,
            "idempotencyKeyHash": None,
            "effectiveDecision": None,
            "outcomeSuccess": None,
            "terminalReason": None,
            "resolvedAt": None,
        }
        with self._mutation() as store:
            if request_id in store["records"]:
                raise FullAgentRuntimeError(
                    "approval_decision_conflict",
                    "Approval request ID has already been used.",
                    status=409,
                )
            self._compact_expired_terminal_records(store, now_epoch=now_epoch)
            if len(store["records"]) >= MAX_APPROVAL_RECORDS:
                raise FullAgentRuntimeError(
                    "approval_store_full",
                    "Approval journal is full and failed closed.",
                    status=409,
                )
            store["records"][request_id] = record
            self._touch(store)
        return dict(record)

    def claim_decision(
        self,
        request_id: str,
        *,
        decision: str,
        idempotency_key: str,
        thread_id: str,
        turn_id: str,
        item_id: str,
        payload_hash: str,
        decision_nonce: str,
    ) -> dict[str, Any]:
        """Atomically enforce first-decision-wins and exact replay binding."""

        request_id = self._approval_id(request_id, field="requestId")
        thread_id = self._approval_id(thread_id, field="threadId")
        turn_id = self._approval_id(turn_id, field="turnId")
        item_id = self._approval_id(item_id, field="itemId")
        payload_hash = self._sha256(payload_hash, field="requestDigest")
        nonce_hash = self._digest_secret(decision_nonce, field="decisionNonce")
        key_hash = self._digest_secret(idempotency_key, field="idempotencyKey")
        if decision not in self._DECISIONS:
            raise FullAgentRuntimeError(
                "invalid_approval_decision", "Approval decision is invalid.", status=422
            )
        expired = False
        with self._mutation() as store:
            record = store["records"].get(request_id)
            if record is None:
                raise FullAgentRuntimeError(
                    "approval_not_pending", "Approval request is not pending.", status=409
                )
            self._assert_binding(
                record,
                thread_id=thread_id,
                turn_id=turn_id,
                item_id=item_id,
                payload_hash=payload_hash,
                nonce_hash=nonce_hash,
            )
            if record["state"] == "pending":
                if self._now_epoch() >= float(record["expiresEpoch"]):
                    self._abort_record(record, reason="approval_expired")
                    self._touch(store)
                    expired = True
                else:
                    record.update(
                        {
                            "state": "decision_recorded",
                            "singleUseConsumed": True,
                            "requestedDecision": decision,
                            "idempotencyKeyHash": key_hash,
                            "resolvedAt": self._now(),
                        }
                    )
                    self._touch(store)
                    return {
                        "idempotentReplay": False,
                        "committed": False,
                        "outcomeSuccess": None,
                        "effectiveDecision": None,
                        "state": "decision_recorded",
                    }
            if expired:
                pass
            elif record["state"] == "aborted":
                # Restart/expiry recovery is a permanent decline tombstone.
                # It can prove this request is consumed, but can never revive
                # the original SDK action or become an approval.
                return {
                    "idempotentReplay": True,
                    "committed": False,
                    "outcomeSuccess": False,
                    "effectiveDecision": "decline",
                    "state": "aborted",
                }
            else:
                self._assert_decision_replay(
                    record, decision=decision, idempotency_key_hash=key_hash
                )
                return {
                    "idempotentReplay": True,
                    "committed": record["state"] == "committed",
                    "outcomeSuccess": record.get("outcomeSuccess"),
                    "effectiveDecision": record.get("effectiveDecision"),
                    "state": record["state"],
                }
        if expired:
            raise FullAgentRuntimeError(
                "approval_expired", "Approval request has expired.", status=409
            )
        raise FullAgentRuntimeError(
            "approval_not_pending", "Approval request is not pending.", status=409
        )

    def commit_resolution(
        self,
        request_id: str,
        *,
        requested_decision: str,
        effective_decision: str,
        outcome_success: bool,
        terminal_reason: str,
    ) -> dict[str, Any]:
        """Commit a terminal tombstone before an SDK accept can be returned."""

        request_id = self._approval_id(request_id, field="requestId")
        if requested_decision not in self._DECISIONS or effective_decision not in self._DECISIONS:
            raise FullAgentRuntimeError(
                "invalid_approval_decision", "Approval decision is invalid.", status=422
            )
        if not isinstance(outcome_success, bool):
            raise FullAgentRuntimeError(
                "invalid_approval_request", "Approval outcome is invalid.", status=422
            )
        reason = _plain_text(
            terminal_reason, field="terminalReason", maximum=96
        )
        with self._mutation() as store:
            record = store["records"].get(request_id)
            if record is None:
                raise FullAgentRuntimeError(
                    "approval_not_pending", "Approval request is not pending.", status=409
                )
            if record["state"] == "committed":
                if (
                    record.get("requestedDecision") == requested_decision
                    and record.get("effectiveDecision") == effective_decision
                    and record.get("outcomeSuccess") is outcome_success
                    and record.get("terminalReason") == reason
                ):
                    return {"idempotentReplay": True, **dict(record)}
                raise FullAgentRuntimeError(
                    "approval_decision_conflict",
                    "Approval request already has a different terminal outcome.",
                    status=409,
                )
            if record["state"] != "decision_recorded" or record.get(
                "requestedDecision"
            ) != requested_decision:
                raise FullAgentRuntimeError(
                    "approval_decision_conflict",
                    "Approval request cannot be committed with this decision.",
                    status=409,
                )
            record.update(
                {
                    "state": "committed",
                    "singleUseConsumed": True,
                    "effectiveDecision": effective_decision,
                    "outcomeSuccess": outcome_success,
                    "terminalReason": reason,
                    "resolvedAt": self._now(),
                }
            )
            self._touch(store)
            return {"idempotentReplay": False, **dict(record)}

    def get_record(self, request_id: str) -> dict[str, Any] | None:
        """Return backend-only hashed state for diagnostics and tests."""

        request_id = self._approval_id(request_id, field="requestId")
        record = self._load()["records"].get(request_id)
        return dict(record) if isinstance(record, dict) else None

    @staticmethod
    def _assert_binding(
        record: Mapping[str, Any],
        *,
        thread_id: str,
        turn_id: str,
        item_id: str,
        payload_hash: str,
        nonce_hash: str,
    ) -> None:
        if (
            record.get("threadId") != thread_id
            or record.get("turnId") != turn_id
            or record.get("itemId") != item_id
            or record.get("payloadHash") != payload_hash
            or record.get("decisionNonceHash") != nonce_hash
        ):
            raise FullAgentRuntimeError(
                "approval_binding_mismatch",
                "Approval request binding does not match.",
                status=409,
            )

    @staticmethod
    def _assert_decision_replay(
        record: Mapping[str, Any], *, decision: str, idempotency_key_hash: str
    ) -> None:
        if (
            record.get("requestedDecision") != decision
            or record.get("idempotencyKeyHash") != idempotency_key_hash
        ):
            raise FullAgentRuntimeError(
                "approval_decision_conflict",
                "Approval request already received a different decision.",
                status=409,
            )

    def _abort_record(self, record: dict[str, Any], *, reason: str) -> None:
        record.update(
            {
                "state": "aborted",
                "singleUseConsumed": True,
                "effectiveDecision": "decline",
                "outcomeSuccess": False,
                "terminalReason": reason,
                "resolvedAt": self._now(),
            }
        )

    @staticmethod
    def _resolved_epoch(value: Any) -> float | None:
        """Parse an aware ISO-8601 tombstone time; malformed values fail closed."""

        if not isinstance(value, str) or not value:
            return None
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        try:
            return parsed.timestamp()
        except (OverflowError, OSError, ValueError):
            return None

    def _compact_expired_terminal_records(
        self, store: dict[str, Any], *, now_epoch: float
    ) -> int:
        """Remove only terminal tombstones older than the replay window."""

        cutoff = float(now_epoch) - APPROVAL_REPLAY_RETENTION_SECONDS
        expired_ids = [
            request_id
            for request_id, record in store["records"].items()
            if record.get("state") in {"committed", "aborted"}
            and (resolved_epoch := self._resolved_epoch(record.get("resolvedAt")))
            is not None
            and resolved_epoch < cutoff
        ]
        for request_id in expired_ids:
            del store["records"][request_id]
        return len(expired_ids)

    def _recover_unfinished(self) -> None:
        with self._mutation() as store:
            changed = False
            for record in store["records"].values():
                if record.get("state") in {"pending", "decision_recorded"}:
                    self._abort_record(record, reason="broker_restarted")
                    changed = True
            if self._compact_expired_terminal_records(
                store, now_epoch=self._now_epoch()
            ):
                changed = True
            if changed:
                self._touch(store)

    def _empty_store(self) -> dict[str, Any]:
        now = self._now()
        return {
            "schemaVersion": APPROVAL_JOURNAL_SCHEMA_VERSION,
            "revision": 0,
            "createdAt": now,
            "updatedAt": now,
            "records": {},
        }

    def _touch(self, store: dict[str, Any]) -> None:
        store["updatedAt"] = self._now()
        store["revision"] += 1

    @contextlib.contextmanager
    def _mutation(self):
        with self._lock:
            _validate_existing_chain(self._root)
            with _InterprocessLock(self._lock_path):
                store = self._load_unlocked()
                yield store
                self._write_unlocked(store)

    def _load(self) -> dict[str, Any]:
        with self._lock:
            return self._load_unlocked()

    def _load_unlocked(self) -> dict[str, Any]:
        if not self._store_path.exists():
            return self._empty_store()
        if _is_reparse_or_symlink(self._store_path):
            raise FullAgentRuntimeError(
                "unsafe_storage_path", "Approval journal path is unsafe.", status=409
            )
        try:
            size = self._store_path.stat(follow_symlinks=False).st_size
            if size > MAX_APPROVAL_JOURNAL_BYTES:
                raise FullAgentRuntimeError(
                    "store_too_large", "Approval journal is too large.", status=409
                )
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(self._store_path, flags)
            with os.fdopen(descriptor, "rb") as handle:
                raw = handle.read(MAX_APPROVAL_JOURNAL_BYTES + 1)
            if len(raw) > MAX_APPROVAL_JOURNAL_BYTES:
                raise FullAgentRuntimeError(
                    "store_too_large", "Approval journal is too large.", status=409
                )
            store = json.loads(raw.decode("utf-8"))
            self._validate_store(store)
            return store
        except FullAgentRuntimeError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise FullAgentRuntimeError(
                "store_corrupt", "Approval journal could not be read safely.", status=500
            ) from error

    def _validate_store(self, store: Any) -> None:
        if (
            not isinstance(store, dict)
            or store.get("schemaVersion") != APPROVAL_JOURNAL_SCHEMA_VERSION
            or not isinstance(store.get("revision"), int)
            or isinstance(store.get("revision"), bool)
            or store.get("revision", -1) < 0
            or not isinstance(store.get("records"), dict)
            or len(store["records"]) > MAX_APPROVAL_RECORDS
        ):
            raise FullAgentRuntimeError(
                "store_corrupt", "Approval journal schema is invalid.", status=500
            )
        required = {
            "requestId",
            "method",
            "actionType",
            "threadId",
            "turnId",
            "itemId",
            "payloadHash",
            "decisionNonceHash",
            "createdAt",
            "expiresAt",
            "expiresEpoch",
            "singleUse",
            "singleUseConsumed",
            "state",
            "requestedDecision",
            "idempotencyKeyHash",
            "effectiveDecision",
            "outcomeSuccess",
            "terminalReason",
            "resolvedAt",
        }
        for request_id, record in store["records"].items():
            if (
                not isinstance(record, dict)
                or not required.issubset(record)
                or request_id != record.get("requestId")
                or record.get("state") not in self._STATES
                or record.get("singleUse") is not True
                or not isinstance(record.get("singleUseConsumed"), bool)
            ):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid record.", status=500
                )
            for field_name in (
                "requestId",
                "method",
                "actionType",
                "threadId",
                "turnId",
                "itemId",
            ):
                self._approval_id(record.get(field_name), field=field_name)
            self._sha256(record.get("payloadHash"), field="payloadHash")
            self._sha256(record.get("decisionNonceHash"), field="decisionNonceHash")
            self._epoch(record.get("expiresEpoch"), field="expiresEpoch")
            for field_name in ("createdAt", "expiresAt"):
                if _plain_text(
                    record.get(field_name), field=field_name, maximum=64
                ) != record.get(field_name):
                    raise FullAgentRuntimeError(
                        "store_corrupt",
                        "Approval journal contains an invalid timestamp.",
                        status=500,
                    )
            if record.get("requestedDecision") not in {None, *self._DECISIONS}:
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid decision.", status=500
                )
            if record.get("effectiveDecision") not in {None, *self._DECISIONS}:
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid outcome.", status=500
                )
            key_hash = record.get("idempotencyKeyHash")
            if key_hash is not None:
                self._sha256(key_hash, field="idempotencyKeyHash")
            outcome = record.get("outcomeSuccess")
            if outcome is not None and not isinstance(outcome, bool):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid outcome.", status=500
                )
            terminal_reason = record.get("terminalReason")
            if terminal_reason is not None and (
                _plain_text(
                    terminal_reason, field="terminalReason", maximum=96
                )
                != terminal_reason
            ):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid reason.", status=500
                )
            state = record["state"]
            if state == "pending" and (
                record["singleUseConsumed"]
                or record.get("requestedDecision") is not None
                or key_hash is not None
                or record.get("effectiveDecision") is not None
                or outcome is not None
                or terminal_reason is not None
                or record.get("resolvedAt") is not None
            ):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid pending record.", status=500
                )
            if state in {"decision_recorded", "committed"} and (
                record["singleUseConsumed"] is not True
                or record.get("requestedDecision") not in self._DECISIONS
                or key_hash is None
            ):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid decision record.", status=500
                )
            if state == "committed" and (
                record.get("effectiveDecision") not in self._DECISIONS
                or not isinstance(outcome, bool)
                or terminal_reason is None
            ):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid tombstone.", status=500
                )
            if state == "aborted" and (
                record["singleUseConsumed"] is not True
                or record.get("effectiveDecision") != "decline"
                or outcome is not False
                or terminal_reason is None
            ):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Approval journal contains an invalid abort tombstone.", status=500
                )

    def _write_unlocked(self, store: Mapping[str, Any]) -> None:
        encoded = (
            json.dumps(store, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        if len(encoded) > MAX_APPROVAL_JOURNAL_BYTES:
            raise FullAgentRuntimeError(
                "store_too_large", "Approval journal is too large.", status=409
            )
        _validate_existing_chain(self._root)
        if self._store_path.exists() and _is_reparse_or_symlink(self._store_path):
            raise FullAgentRuntimeError(
                "unsafe_storage_path", "Approval journal path is unsafe.", status=409
            )
        temporary = self._root / (
            f".{APPROVAL_JOURNAL_FILENAME}.{secrets.token_hex(8)}.tmp"
        )
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor: int | None = None
        try:
            descriptor = os.open(temporary, flags, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            if _is_reparse_or_symlink(temporary):
                raise FullAgentRuntimeError(
                    "unsafe_storage_path", "Approval journal temporary file is unsafe.", status=409
                )
            os.replace(temporary, self._store_path)
            with contextlib.suppress(OSError):
                os.chmod(self._store_path, 0o600)
            if hasattr(os, "O_DIRECTORY"):
                with contextlib.suppress(OSError):
                    directory_fd = os.open(self._root, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            with contextlib.suppress(FileNotFoundError):
                temporary.unlink()


class FullAgentRuntime:
    """Atomic local state store for persistent Full Agent conversations."""

    def __init__(
        self,
        storage_root: str | os.PathLike[str],
        *,
        allowed_agents: Iterable[str] | None = None,
        model_allowlist: Iterable[str] = DEFAULT_MODEL_ALLOWLIST,
        reasoning_allowlist: Iterable[str] = DEFAULT_REASONING_ALLOWLIST,
        default_model: str = "gpt-6-sol",
        default_reasoning: str = "medium",
        default_mode: str = "chat",
        now: Callable[[], str] = _utc_now,
    ) -> None:
        self._root = _secure_storage_root(storage_root)
        self._store_path = self._root / STORE_FILENAME
        self._lock_path = self._root / LOCK_FILENAME
        self._lock = threading.RLock()
        self._now = now
        self._models = tuple(dict.fromkeys(model_allowlist))
        self._reasoning = tuple(dict.fromkeys(reasoning_allowlist))
        if not self._models or not self._reasoning:
            raise FullAgentRuntimeError(
                "invalid_configuration", "Model and reasoning allowlists cannot be empty."
            )
        for model in self._models:
            _identifier(model, field="model")
        for effort in self._reasoning:
            _identifier(effort, field="reasoning")
        if default_model not in self._models:
            raise FullAgentRuntimeError(
                "invalid_configuration", "Default model is not allowlisted."
            )
        if default_reasoning not in self._reasoning:
            raise FullAgentRuntimeError(
                "invalid_configuration", "Default reasoning is not allowlisted."
            )
        if default_mode not in CAPABILITY_MODES:
            raise FullAgentRuntimeError(
                "invalid_configuration", "Default capability mode is invalid."
            )
        self._default_model = default_model
        self._default_reasoning = default_reasoning
        self._default_mode = default_mode
        if allowed_agents is None:
            self._allowed_agents: frozenset[str] | None = None
        else:
            self._allowed_agents = frozenset(
                _identifier(agent, field="agentId", pattern=_AGENT_ID_RE)
                for agent in allowed_agents
            )

    @property
    def storage_kind(self) -> str:
        return "local_secret_free_atomic_json"

    def runtime_status(self, agent_id: str | None = None) -> dict[str, Any]:
        if agent_id is not None:
            self._validate_agent(agent_id)
        return {
            "available": True,
            "executionEnabled": False,
            "toolExecutionState": "not_connected",
            "persistenceEnabled": True,
            "storageKind": self.storage_kind,
            "secretStorageAllowed": False,
            "encryptionAtRest": False,
            "modelOptions": list(self._models),
            "reasoningOptions": list(self._reasoning),
            "capabilityModes": [
                {
                    "id": mode,
                    "capabilities": list(capabilities),
                    "toolExecutionEnabled": False,
                }
                for mode, capabilities in CAPABILITY_MODES.items()
            ],
        }

    def create_thread(
        self,
        agent_id: str,
        *,
        title: str = "New conversation",
        model: str | None = None,
        reasoning: str | None = None,
        mode: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        agent_id = self._validate_agent(agent_id)
        title = _plain_text(title, field="title", maximum=MAX_TITLE_CHARS)
        model = self._validate_model(model or self._default_model)
        reasoning = self._validate_reasoning(reasoning or self._default_reasoning)
        mode = self._validate_mode(mode or self._default_mode)
        key = _idempotency_key(idempotency_key)
        request = {
            "agentId": agent_id,
            "title": title,
            "model": model,
            "reasoning": reasoning,
            "mode": mode,
        }
        request_hash = _request_digest(request)
        with self._mutation() as store:
            if key is not None:
                prior = store["createIdempotency"].get(_key_digest(key))
                if prior is not None:
                    if prior.get("requestDigest") != request_hash:
                        raise FullAgentRuntimeError(
                            "idempotency_conflict",
                            "That idempotency key was already used for a different request.",
                            status=409,
                        )
                    thread = store["threads"].get(prior.get("threadId"))
                    if thread is None:
                        raise FullAgentRuntimeError(
                            "store_corrupt", "Agent history could not be read safely.", status=500
                        )
                    return {
                        "thread": self._thread_read_model(thread, include_events=True),
                        "idempotentReplay": True,
                    }
            if len(store["threads"]) >= MAX_THREADS:
                raise FullAgentRuntimeError(
                    "thread_limit_reached", "The Agent thread limit has been reached.", status=409
                )
            agent_count = sum(
                1 for thread in store["threads"].values() if thread["agentId"] == agent_id
            )
            if agent_count >= MAX_THREADS_PER_AGENT:
                raise FullAgentRuntimeError(
                    "agent_thread_limit_reached",
                    "This Agent has reached its thread limit.",
                    status=409,
                )
            now = self._now()
            thread_id = f"fat_{uuid.uuid4().hex}"
            thread = {
                "id": thread_id,
                **request,
                "status": "idle",
                "archived": False,
                "createdAt": now,
                "updatedAt": now,
                "revision": 1,
                "events": [],
                "eventIdempotency": {},
                "turns": [],
                "turnIdempotency": {},
                "interruptIdempotency": {},
                "activeTurnId": None,
                "backendThreadId": None,
            }
            store["threads"][thread_id] = thread
            if key is not None:
                store["createIdempotency"][_key_digest(key)] = {
                    "threadId": thread_id,
                    "requestDigest": request_hash,
                }
            self._touch_store(store, now)
            return {
                "thread": self._thread_read_model(thread, include_events=True),
                "idempotentReplay": False,
            }

    def list_threads(
        self,
        *,
        agent_id: str | None = None,
        include_archived: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if agent_id is not None:
            agent_id = self._validate_agent(agent_id)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_LIST_LIMIT:
            raise FullAgentRuntimeError(
                "invalid_request", f"limit must be between 1 and {MAX_LIST_LIMIT}.", status=422
            )
        store = self._load_store()
        rows = [
            thread
            for thread in store["threads"].values()
            if (agent_id is None or thread["agentId"] == agent_id)
            and (include_archived or not thread["archived"])
        ]
        rows.sort(key=lambda item: (item["updatedAt"], item["id"]), reverse=True)
        return [self._thread_read_model(row, include_events=False) for row in rows[:limit]]

    def get_thread(
        self,
        thread_id: str,
        *,
        include_events: bool = True,
        event_limit: int = 200,
    ) -> dict[str, Any]:
        thread_id = _identifier(thread_id, field="threadId")
        if not isinstance(event_limit, int) or isinstance(event_limit, bool) or not 1 <= event_limit <= MAX_EVENTS_PER_THREAD:
            raise FullAgentRuntimeError(
                "invalid_request",
                f"event_limit must be between 1 and {MAX_EVENTS_PER_THREAD}.",
                status=422,
            )
        thread = self._get_thread(self._load_store(), thread_id)
        return self._thread_read_model(
            thread, include_events=include_events, event_limit=event_limit
        )

    def update_settings(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        model: str | None = None,
        reasoning: str | None = None,
        mode: str | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        thread_id = _identifier(thread_id, field="threadId")
        changes: dict[str, Any] = {}
        if title is not None:
            changes["title"] = _plain_text(title, field="title", maximum=MAX_TITLE_CHARS)
        if model is not None:
            changes["model"] = self._validate_model(model)
        if reasoning is not None:
            changes["reasoning"] = self._validate_reasoning(reasoning)
        if mode is not None:
            changes["mode"] = self._validate_mode(mode)
        if not changes:
            raise FullAgentRuntimeError(
                "invalid_request", "At least one thread setting is required.", status=422
            )
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._check_revision(thread, expected_revision)
            if thread["archived"]:
                raise FullAgentRuntimeError(
                    "thread_archived", "Archived threads cannot be changed.", status=409
                )
            if thread["activeTurnId"] is not None:
                raise FullAgentRuntimeError(
                    "thread_busy",
                    "Thread settings cannot change while a turn is active.",
                    status=409,
                )
            thread.update(changes)
            self._touch_thread(store, thread)
            return self._thread_read_model(thread, include_events=True)

    def update_thread(self, thread_id: str, **changes: Any) -> dict[str, Any]:
        """Compatibility alias for callers that name this operation generically."""

        return self.update_settings(thread_id, **changes)

    def archive_thread(
        self,
        thread_id: str,
        *,
        archived: bool = True,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        thread_id = _identifier(thread_id, field="threadId")
        if not isinstance(archived, bool):
            raise FullAgentRuntimeError(
                "invalid_request", "archived must be true or false.", status=422
            )
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._check_revision(thread, expected_revision)
            if archived and thread["activeTurnId"] is not None:
                raise FullAgentRuntimeError(
                    "thread_busy", "An active turn must finish before archiving.", status=409
                )
            if thread["archived"] != archived:
                thread["archived"] = archived
                thread["status"] = "archived" if archived else "idle"
                self._touch_thread(store, thread)
            return self._thread_read_model(thread, include_events=True)

    def set_backend_thread_id(
        self, thread_id: str, backend_thread_id: str
    ) -> dict[str, Any]:
        """Bind a local thread to one opaque backend session identifier.

        The binding is backend-only and is intentionally absent from every
        frontend read model.  Rebinding to a different session fails closed so
        history cannot silently cross between Codex conversations.
        """

        thread_id = _identifier(thread_id, field="threadId")
        backend_thread_id = _identifier(
            backend_thread_id,
            field="backendThreadId",
            pattern=_BACKEND_THREAD_ID_RE,
        )
        _reject_secret_text(backend_thread_id)
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._ensure_thread_writable(thread)
            existing = thread.get("backendThreadId")
            if existing is not None and existing != backend_thread_id:
                raise FullAgentRuntimeError(
                    "backend_thread_conflict",
                    "This Agent thread is already bound to another backend session.",
                    status=409,
                )
            if existing is None:
                thread["backendThreadId"] = backend_thread_id
                self._touch_thread(store, thread)
            return self._thread_read_model(thread, include_events=False)

    def get_backend_thread_id(self, thread_id: str) -> str | None:
        """Return the backend-only session binding to trusted bridge code."""

        thread_id = _identifier(thread_id, field="threadId")
        thread = self._get_thread(self._load_store(), thread_id)
        value = thread.get("backendThreadId")
        if value is None:
            return None
        return _identifier(
            value, field="backendThreadId", pattern=_BACKEND_THREAD_ID_RE
        )

    def clear_backend_thread_id(
        self,
        thread_id: str,
        *,
        expected_backend_thread_id: str,
    ) -> dict[str, Any]:
        """Detach an exact quarantined backend session without exposing it.

        This is intentionally compare-and-clear.  A stale timeout worker must
        never detach a newer session that another trusted bridge path bound in
        the meantime.
        """

        thread_id = _identifier(thread_id, field="threadId")
        expected = _identifier(
            expected_backend_thread_id,
            field="backendThreadId",
            pattern=_BACKEND_THREAD_ID_RE,
        )
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._ensure_thread_writable(thread)
            existing = thread.get("backendThreadId")
            if existing not in {None, expected}:
                raise FullAgentRuntimeError(
                    "backend_thread_conflict",
                    "The backend session changed before quarantine completed.",
                    status=409,
                )
            if existing == expected:
                thread["backendThreadId"] = None
                self._touch_thread(store, thread)
            return self._thread_read_model(thread, include_events=False)

    def append_event(
        self,
        thread_id: str,
        *,
        role: str,
        content: str,
        event_type: str = "message",
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        thread_id = _identifier(thread_id, field="threadId")
        event_input = self._event_input(
            role=role,
            content=content,
            event_type=event_type,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            metadata=metadata,
        )
        key = _idempotency_key(idempotency_key)
        request_hash = _request_digest(event_input)
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._ensure_thread_writable(thread)
            prior = None
            if key is not None:
                prior = thread["eventIdempotency"].get(_key_digest(key))
            if prior is not None:
                if prior.get("requestDigest") != request_hash:
                    raise FullAgentRuntimeError(
                        "idempotency_conflict",
                        "That idempotency key was already used for a different event.",
                        status=409,
                    )
                event = self._find_event(thread, prior.get("eventId"))
                return {
                    "event": self._event_read_model(event),
                    "thread": self._thread_read_model(thread, include_events=False),
                    "idempotentReplay": True,
                }
            event = self._append_event_record(thread, event_input)
            if key is not None:
                thread["eventIdempotency"][_key_digest(key)] = {
                    "eventId": event["id"],
                    "requestDigest": request_hash,
                }
            self._touch_thread(store, thread, now=event["createdAt"])
            return {
                "event": self._event_read_model(event),
                "thread": self._thread_read_model(thread, include_events=False),
                "idempotentReplay": False,
            }

    def request_turn(
        self,
        thread_id: str,
        *,
        content: str,
        idempotency_key: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist one user turn request without executing a model or tool."""

        thread_id = _identifier(thread_id, field="threadId")
        key = _idempotency_key(idempotency_key, required=True)
        assert key is not None
        event_input = self._event_input(
            role="user", content=content, event_type="message", metadata=metadata
        )
        request_hash = _request_digest(event_input)
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._ensure_thread_writable(thread)
            digest = _key_digest(key)
            prior = thread["turnIdempotency"].get(digest)
            if prior is not None:
                if prior.get("requestDigest") != request_hash:
                    raise FullAgentRuntimeError(
                        "idempotency_conflict",
                        "That idempotency key was already used for a different turn.",
                        status=409,
                    )
                turn = self._find_turn(thread, prior.get("turnId"))
                return {
                    "turn": self._turn_read_model(turn),
                    "thread": self._thread_read_model(thread, include_events=True),
                    # Keep replay evidence bound to the exact Turn even when
                    # the general thread read window has rolled past it.
                    "turnEvents": [
                        self._event_read_model(event)
                        for event in thread["events"]
                        if isinstance(event.get("metadata"), Mapping)
                        and event["metadata"].get("turnId") == turn["id"]
                    ],
                    "idempotentReplay": True,
                }
            if thread["activeTurnId"] is not None:
                raise FullAgentRuntimeError(
                    "thread_busy", "This Agent is already handling another turn.", status=409
                )
            if len(thread["turns"]) >= MAX_TURNS_PER_THREAD:
                raise FullAgentRuntimeError(
                    "turn_limit_reached", "This thread has reached its turn limit.", status=409
                )
            if len(thread["events"]) + TURN_EVENT_RESERVE > MAX_EVENTS_PER_THREAD:
                raise FullAgentRuntimeError(
                    "history_limit_reached",
                    "This thread does not have enough history capacity to safely complete another turn.",
                    status=409,
                )
            event = self._append_event_record(thread, event_input)
            now = event["createdAt"]
            turn = {
                "id": f"turn_{uuid.uuid4().hex}",
                "status": "queued",
                "promptEventId": event["id"],
                "requestedAt": now,
                "startedAt": None,
                "completedAt": None,
                "interruptRequested": False,
                "interruptRequestedAt": None,
                "errorCode": None,
            }
            thread["turns"].append(turn)
            thread["activeTurnId"] = turn["id"]
            thread["status"] = "queued"
            thread["turnIdempotency"][digest] = {
                "turnId": turn["id"],
                "requestDigest": request_hash,
            }
            self._touch_thread(store, thread, now=now)
            return {
                "turn": self._turn_read_model(turn),
                "thread": self._thread_read_model(thread, include_events=True),
                "idempotentReplay": False,
            }

    def update_turn_state(
        self,
        thread_id: str,
        turn_id: str,
        *,
        status: str,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        """Update orchestration state; this method never starts execution."""

        thread_id = _identifier(thread_id, field="threadId")
        turn_id = _identifier(turn_id, field="turnId")
        if status not in TURN_STATES:
            raise FullAgentRuntimeError(
                "invalid_turn_state", "Turn status is not allowlisted.", status=422
            )
        if error_code is not None:
            error_code = _identifier(error_code, field="errorCode")
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._ensure_thread_writable(thread)
            turn = self._find_turn(thread, turn_id)
            current = turn["status"]
            allowed = {
                "queued": {"running", "cancelled", "failed"},
                "running": {"interrupt_requested", "completed", "failed", "cancelled"},
                "interrupt_requested": {"completed", "failed", "cancelled"},
                "completed": set(),
                "failed": set(),
                "cancelled": set(),
            }
            if status != current and status not in allowed[current]:
                raise FullAgentRuntimeError(
                    "invalid_turn_transition",
                    f"Turn cannot transition from {current} to {status}.",
                    status=409,
                )
            now = self._now()
            if status == "running" and turn["startedAt"] is None:
                turn["startedAt"] = now
            if status == "failed" and error_code is None:
                raise FullAgentRuntimeError(
                    "invalid_request", "A failed turn requires a safe error code.", status=422
                )
            if status != "failed" and error_code is not None:
                raise FullAgentRuntimeError(
                    "invalid_request", "errorCode is only valid for a failed turn.", status=422
                )
            turn["status"] = status
            turn["errorCode"] = error_code
            if status in TERMINAL_TURN_STATES:
                turn["completedAt"] = now
                if thread["activeTurnId"] == turn_id:
                    thread["activeTurnId"] = None
                thread["status"] = "idle"
            else:
                thread["status"] = status
            self._touch_thread(store, thread, now=now)
            return {
                "turn": self._turn_read_model(turn),
                "thread": self._thread_read_model(thread, include_events=False),
            }

    def update_turn_prompt_metadata(
        self,
        thread_id: str,
        turn_id: str,
        *,
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Replace backend-owned prompt metadata after attachment rebinding.

        The original idempotency request digest intentionally remains bound to
        the caller's stable request metadata; only the persisted/read-model
        event is upgraded from draft-free descriptors to exact Turn-owned IDs.
        """

        thread_id = _identifier(thread_id, field="threadId")
        turn_id = _identifier(turn_id, field="turnId")
        safe_metadata = _sanitize_metadata(metadata)
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._ensure_thread_writable(thread)
            turn = self._find_turn(thread, turn_id)
            event = self._find_event(thread, turn["promptEventId"])
            if event.get("role") != "user" or event.get("type") != "message":
                raise FullAgentRuntimeError(
                    "store_corrupt", "Turn prompt event is invalid.", status=500
                )
            event["metadata"] = safe_metadata
            self._touch_thread(store, thread)
            return {
                "event": self._event_read_model(event),
                "turn": self._turn_read_model(turn),
                "thread": self._thread_read_model(thread, include_events=True),
            }

    def request_interrupt(
        self,
        thread_id: str,
        *,
        turn_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Persist an interrupt request for the external runner to observe."""

        thread_id = _identifier(thread_id, field="threadId")
        if turn_id is not None:
            turn_id = _identifier(turn_id, field="turnId")
        key = _idempotency_key(idempotency_key)
        with self._mutation() as store:
            thread = self._get_thread(store, thread_id)
            self._ensure_thread_writable(thread)
            selected_id = turn_id or thread["activeTurnId"]
            if selected_id is None:
                raise FullAgentRuntimeError(
                    "no_active_turn", "This thread has no active turn to interrupt.", status=409
                )
            turn = self._find_turn(thread, selected_id)
            request_hash = _request_digest({"turnId": selected_id})
            if key is not None:
                prior = thread["interruptIdempotency"].get(_key_digest(key))
                if prior is not None:
                    if prior.get("requestDigest") != request_hash:
                        raise FullAgentRuntimeError(
                            "idempotency_conflict",
                            "That idempotency key was already used for another interrupt.",
                            status=409,
                        )
                    return {
                        "turn": self._turn_read_model(turn),
                        "thread": self._thread_read_model(thread, include_events=False),
                        "idempotentReplay": True,
                    }
            if turn["status"] in TERMINAL_TURN_STATES:
                raise FullAgentRuntimeError(
                    "turn_already_finished", "The selected turn has already finished.", status=409
                )
            now = self._now()
            turn["interruptRequested"] = True
            turn["interruptRequestedAt"] = turn["interruptRequestedAt"] or now
            turn["status"] = "interrupt_requested"
            thread["status"] = "interrupt_requested"
            if key is not None:
                if (
                    _key_digest(key) not in thread["interruptIdempotency"]
                    and len(thread["interruptIdempotency"])
                    >= MAX_INTERRUPT_KEYS_PER_THREAD
                ):
                    raise FullAgentRuntimeError(
                        "idempotency_limit_reached",
                        "This thread has reached its interrupt request limit.",
                        status=409,
                    )
                thread["interruptIdempotency"][_key_digest(key)] = {
                    "turnId": selected_id,
                    "requestDigest": request_hash,
                }
            self._touch_thread(store, thread, now=now)
            return {
                "turn": self._turn_read_model(turn),
                "thread": self._thread_read_model(thread, include_events=False),
                "idempotentReplay": False,
            }

    def classify_action(
        self, action: Mapping[str, Any], *, mode: str
    ) -> dict[str, Any]:
        """Classify an intended action without dispatching it."""

        mode = self._validate_mode(mode)
        if not isinstance(action, Mapping):
            raise FullAgentRuntimeError(
                "invalid_request", "Action must be an object.", status=422
            )
        capability = _identifier(action.get("capability"), field="capability")
        all_capabilities = {item for values in CAPABILITY_MODES.values() for item in values}
        if capability not in all_capabilities:
            raise FullAgentRuntimeError(
                "unknown_capability", "Action capability is not allowlisted.", status=422
            )
        operation = _plain_text(
            action.get("operation", "unknown"),
            field="operation",
            # A workspace Turn accepts a bounded multi-line prompt.  Risk
            # classification must inspect that complete prompt; truncating or
            # rejecting it after the Turn has been persisted can strand the
            # thread in a queued state and can miss a dangerous suffix.
            maximum=MAX_CONTENT_CHARS,
        ).casefold()
        flags: dict[str, bool] = {}
        for name in (
            "externalSideEffect",
            "destructive",
            "credentialAccess",
            "financialOrLiveTrade",
        ):
            raw_flag = action.get(name, False)
            if not isinstance(raw_flag, bool):
                raise FullAgentRuntimeError(
                    "invalid_request", f"{name} must be true or false.", status=422
                )
            flags[name] = raw_flag
        reasons: list[str] = []
        if flags["credentialAccess"] or any(
            token in operation
            for token in (
                "password",
                "credential",
                "access token",
                "access_token",
                "refresh token",
                "refresh_token",
                "private key",
                "private_key",
            )
        ):
            reasons.append("credential_access_blocked")
        if flags["financialOrLiveTrade"] or any(
            token in operation for token in ("live trade", "live_trade", "place order", "trade order")
        ):
            reasons.append("financial_or_live_trade")
        if flags["destructive"] or any(
            token in operation
            for token in (
                "delete",
                "remove",
                "overwrite",
                "reset",
                "format",
                "drop ",
                "rm ",
                "rmdir",
                "truncate",
            )
        ):
            reasons.append("destructive_action")
        if flags["externalSideEffect"] or capability == "external_action" or any(
            token in operation
            for token in ("send", "publish", "deploy", "push", "post", "upload", "purchase")
        ):
            reasons.append("external_side_effect")
        if capability == "computer_use" and operation not in {
            "view",
            "inspect",
            "screenshot",
            "read screen",
        }:
            reasons.append("interactive_computer_control")
        reasons = list(dict.fromkeys(reasons))
        policy_blocked = "credential_access_blocked" in reasons
        approval_required = bool(reasons)
        if policy_blocked or "financial_or_live_trade" in reasons:
            risk = "critical"
        elif "destructive_action" in reasons or "external_side_effect" in reasons:
            risk = "high"
        elif "interactive_computer_control" in reasons:
            risk = "medium"
        else:
            risk = "low"
        return {
            "capability": capability,
            "mode": mode,
            "modeAllowsCapability": capability in CAPABILITY_MODES[mode],
            "approvalRequired": approval_required,
            "policyBlocked": policy_blocked,
            "riskLevel": risk,
            "reasonCodes": reasons,
            "executionEnabled": False,
            "executionAllowed": False,
        }

    def execute_tool(self, *_args: Any, **_kwargs: Any) -> None:
        raise FullAgentRuntimeError(
            "tool_execution_unavailable",
            "This state core cannot execute tools. Connect an approved runner first.",
            status=503,
        )

    def _validate_agent(self, agent_id: Any) -> str:
        value = _identifier(agent_id, field="agentId", pattern=_AGENT_ID_RE)
        if self._allowed_agents is not None and value not in self._allowed_agents:
            raise FullAgentRuntimeError(
                "unknown_agent", "Agent is not in the configured roster.", status=404
            )
        return value

    def _validate_model(self, value: Any) -> str:
        value = _identifier(value, field="model")
        if value not in self._models:
            raise FullAgentRuntimeError(
                "model_not_allowed", "Selected model is not allowlisted.", status=422
            )
        return value

    def _validate_reasoning(self, value: Any) -> str:
        value = _identifier(value, field="reasoning")
        if value not in self._reasoning:
            raise FullAgentRuntimeError(
                "reasoning_not_allowed", "Selected reasoning is not allowlisted.", status=422
            )
        return value

    @staticmethod
    def _validate_mode(value: Any) -> str:
        value = _identifier(value, field="mode")
        if value not in CAPABILITY_MODES:
            raise FullAgentRuntimeError(
                "mode_not_allowed", "Selected capability mode is not allowlisted.", status=422
            )
        return value

    @staticmethod
    def _check_revision(thread: Mapping[str, Any], expected_revision: int | None) -> None:
        if expected_revision is None:
            return
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool):
            raise FullAgentRuntimeError(
                "invalid_request", "expected_revision must be an integer.", status=422
            )
        if thread["revision"] != expected_revision:
            raise FullAgentRuntimeError(
                "revision_conflict", "Thread changed since it was read.", status=409
            )

    @staticmethod
    def _ensure_thread_writable(thread: Mapping[str, Any]) -> None:
        if thread["archived"]:
            raise FullAgentRuntimeError(
                "thread_archived", "Archived threads are read-only.", status=409
            )

    def _event_input(
        self,
        *,
        role: Any,
        content: Any,
        event_type: Any,
        tool_name: Any = None,
        tool_call_id: Any = None,
        metadata: Any = None,
    ) -> dict[str, Any]:
        if role not in EVENT_ROLES:
            raise FullAgentRuntimeError(
                "invalid_event_role", "Event role is not allowlisted.", status=422
            )
        if event_type not in EVENT_TYPES:
            raise FullAgentRuntimeError(
                "invalid_event_type", "Event type is not allowlisted.", status=422
            )
        if event_type.startswith("tool_") and not tool_name:
            raise FullAgentRuntimeError(
                "invalid_request", "Tool events require a tool name.", status=422
            )
        return {
            "role": role,
            "type": event_type,
            "content": _plain_text(content, field="content", maximum=MAX_CONTENT_CHARS),
            "toolName": _identifier(tool_name, field="toolName") if tool_name else None,
            "toolCallId": (
                _identifier(tool_call_id, field="toolCallId") if tool_call_id else None
            ),
            "metadata": _sanitize_metadata(metadata),
        }

    def _append_event_record(
        self, thread: dict[str, Any], event_input: Mapping[str, Any]
    ) -> dict[str, Any]:
        if len(thread["events"]) >= MAX_EVENTS_PER_THREAD:
            raise FullAgentRuntimeError(
                "history_limit_reached", "This thread has reached its history limit.", status=409
            )
        event = {
            "id": f"evt_{uuid.uuid4().hex}",
            **event_input,
            "createdAt": self._now(),
        }
        thread["events"].append(event)
        return event

    @staticmethod
    def _find_event(thread: Mapping[str, Any], event_id: Any) -> dict[str, Any]:
        for event in thread["events"]:
            if event["id"] == event_id:
                return event
        raise FullAgentRuntimeError(
            "store_corrupt", "Agent history could not be read safely.", status=500
        )

    @staticmethod
    def _find_turn(thread: Mapping[str, Any], turn_id: Any) -> dict[str, Any]:
        for turn in thread["turns"]:
            if turn["id"] == turn_id:
                return turn
        raise FullAgentRuntimeError("turn_not_found", "Turn was not found.", status=404)

    @staticmethod
    def _get_thread(store: Mapping[str, Any], thread_id: str) -> dict[str, Any]:
        thread = store["threads"].get(thread_id)
        if thread is None:
            raise FullAgentRuntimeError("thread_not_found", "Thread was not found.", status=404)
        return thread

    def _touch_thread(
        self, store: dict[str, Any], thread: dict[str, Any], *, now: str | None = None
    ) -> None:
        now = now or self._now()
        thread["updatedAt"] = now
        thread["revision"] += 1
        self._touch_store(store, now)

    @staticmethod
    def _touch_store(store: dict[str, Any], now: str) -> None:
        store["updatedAt"] = now
        store["revision"] += 1

    @contextlib.contextmanager
    def _mutation(self):
        with self._lock:
            _validate_existing_chain(self._root)
            with _InterprocessLock(self._lock_path):
                store = self._load_store_unlocked()
                yield store
                self._write_store_unlocked(store)

    def _load_store(self) -> dict[str, Any]:
        with self._lock:
            return self._load_store_unlocked()

    def _load_store_unlocked(self) -> dict[str, Any]:
        if not self._store_path.exists():
            now = self._now()
            return {
                "schemaVersion": SCHEMA_VERSION,
                "revision": 0,
                "createdAt": now,
                "updatedAt": now,
                "threads": {},
                "createIdempotency": {},
            }
        if _is_reparse_or_symlink(self._store_path):
            raise FullAgentRuntimeError(
                "unsafe_storage_path", "Agent history store is unsafe.", status=409
            )
        try:
            size = self._store_path.stat(follow_symlinks=False).st_size
            if size > MAX_STORE_BYTES:
                raise FullAgentRuntimeError(
                    "store_too_large", "Agent history exceeds the safe storage limit.", status=409
                )
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(self._store_path, flags)
            with os.fdopen(descriptor, "rb") as handle:
                raw = handle.read(MAX_STORE_BYTES + 1)
            if len(raw) > MAX_STORE_BYTES:
                raise FullAgentRuntimeError(
                    "store_too_large", "Agent history exceeds the safe storage limit.", status=409
                )
            store = json.loads(raw.decode("utf-8"))
            self._validate_store(store)
            return store
        except FullAgentRuntimeError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise FullAgentRuntimeError(
                "store_corrupt", "Agent history could not be read safely.", status=500
            ) from error

    def _validate_store(self, store: Any) -> None:
        if not isinstance(store, dict) or store.get("schemaVersion") != SCHEMA_VERSION:
            raise FullAgentRuntimeError(
                "store_corrupt", "Agent history schema is invalid.", status=500
            )
        if not isinstance(store.get("threads"), dict) or not isinstance(
            store.get("createIdempotency"), dict
        ):
            raise FullAgentRuntimeError(
                "store_corrupt", "Agent history schema is invalid.", status=500
            )
        if len(store["threads"]) > MAX_THREADS:
            raise FullAgentRuntimeError(
                "store_corrupt", "Agent history contains too many threads.", status=500
            )
        required = {
            "id",
            "agentId",
            "title",
            "model",
            "reasoning",
            "mode",
            "status",
            "archived",
            "createdAt",
            "updatedAt",
            "revision",
            "events",
            "eventIdempotency",
            "turns",
            "turnIdempotency",
            "interruptIdempotency",
            "activeTurnId",
        }
        for thread_id, thread in store["threads"].items():
            if not isinstance(thread, dict) or not required.issubset(thread):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Agent history contains an invalid thread.", status=500
                )
            if (
                thread_id != thread["id"]
                or not isinstance(thread["events"], list)
                or len(thread["events"]) > MAX_EVENTS_PER_THREAD
                or not isinstance(thread["turns"], list)
                or len(thread["turns"]) > MAX_TURNS_PER_THREAD
                or not isinstance(thread["eventIdempotency"], dict)
                or not isinstance(thread["turnIdempotency"], dict)
                or not isinstance(thread["interruptIdempotency"], dict)
                or len(thread["interruptIdempotency"])
                > MAX_INTERRUPT_KEYS_PER_THREAD
                or not isinstance(thread["archived"], bool)
                or not isinstance(thread["revision"], int)
                or isinstance(thread["revision"], bool)
                or thread["revision"] < 1
            ):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Agent history contains an invalid thread.", status=500
                )
            if thread["status"] not in {
                "idle",
                "queued",
                "running",
                "interrupt_requested",
                "archived",
            }:
                raise FullAgentRuntimeError(
                    "store_corrupt", "Agent history contains an invalid thread.", status=500
                )
            if thread["archived"] != (thread["status"] == "archived"):
                raise FullAgentRuntimeError(
                    "store_corrupt", "Agent history contains an invalid thread.", status=500
                )
            self._validate_agent(thread["agentId"])
            self._validate_model(thread["model"])
            self._validate_reasoning(thread["reasoning"])
            self._validate_mode(thread["mode"])
            if _plain_text(
                thread["title"], field="title", maximum=MAX_TITLE_CHARS
            ) != thread["title"]:
                raise FullAgentRuntimeError(
                    "store_corrupt", "Agent history contains an invalid thread.", status=500
                )
            backend_thread_id = thread.get("backendThreadId")
            if backend_thread_id is not None:
                _identifier(
                    backend_thread_id,
                    field="backendThreadId",
                    pattern=_BACKEND_THREAD_ID_RE,
                )
                _reject_secret_text(backend_thread_id)
            event_ids: set[str] = set()
            for event in thread["events"]:
                if (
                    not isinstance(event, dict)
                    or not {
                        "id",
                        "role",
                        "type",
                        "content",
                        "toolName",
                        "toolCallId",
                        "metadata",
                        "createdAt",
                    }.issubset(event)
                    or event["role"] not in EVENT_ROLES
                    or event["type"] not in EVENT_TYPES
                    or event["id"] in event_ids
                ):
                    raise FullAgentRuntimeError(
                        "store_corrupt", "Agent history contains an invalid event.", status=500
                    )
                _identifier(event["id"], field="eventId")
                event_ids.add(event["id"])
                if _plain_text(
                    event["content"], field="content", maximum=MAX_CONTENT_CHARS
                ) != event["content"]:
                    raise FullAgentRuntimeError(
                        "store_corrupt", "Agent history contains an invalid event.", status=500
                    )
                if event["type"].startswith("tool_") and not event["toolName"]:
                    raise FullAgentRuntimeError(
                        "store_corrupt", "Agent history contains an invalid event.", status=500
                    )
                if event["toolName"] is not None:
                    _identifier(event["toolName"], field="toolName")
                if event["toolCallId"] is not None:
                    _identifier(event["toolCallId"], field="toolCallId")
                _sanitize_metadata(event["metadata"])
            turn_ids: set[str] = set()
            for turn in thread["turns"]:
                if (
                    not isinstance(turn, dict)
                    or not {
                        "id",
                        "status",
                        "promptEventId",
                        "requestedAt",
                        "startedAt",
                        "completedAt",
                        "interruptRequested",
                        "interruptRequestedAt",
                        "errorCode",
                    }.issubset(turn)
                    or turn["status"] not in TURN_STATES
                    or turn["id"] in turn_ids
                    or turn["promptEventId"] not in event_ids
                    or not isinstance(turn["interruptRequested"], bool)
                ):
                    raise FullAgentRuntimeError(
                        "store_corrupt", "Agent history contains an invalid turn.", status=500
                    )
                _identifier(turn["id"], field="turnId")
                turn_ids.add(turn["id"])
            active_turn_id = thread["activeTurnId"]
            if active_turn_id is not None:
                if active_turn_id not in turn_ids:
                    raise FullAgentRuntimeError(
                        "store_corrupt", "Agent history contains an invalid turn.", status=500
                    )
                active_turn = self._find_turn(thread, active_turn_id)
                if active_turn["status"] in TERMINAL_TURN_STATES:
                    raise FullAgentRuntimeError(
                        "store_corrupt", "Agent history contains an invalid turn.", status=500
                    )

    def _write_store_unlocked(self, store: Mapping[str, Any]) -> None:
        encoded = (
            json.dumps(
                store,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        if len(encoded) > MAX_STORE_BYTES:
            raise FullAgentRuntimeError(
                "store_too_large", "Agent history exceeds the safe storage limit.", status=409
            )
        _validate_existing_chain(self._root)
        if self._store_path.exists() and _is_reparse_or_symlink(self._store_path):
            raise FullAgentRuntimeError(
                "unsafe_storage_path", "Agent history store is unsafe.", status=409
            )
        temporary = self._root / f".{STORE_FILENAME}.{secrets.token_hex(8)}.tmp"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor: int | None = None
        try:
            descriptor = os.open(temporary, flags, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            if _is_reparse_or_symlink(temporary):
                raise FullAgentRuntimeError(
                    "unsafe_storage_path", "Agent history temporary file is unsafe.", status=409
                )
            os.replace(temporary, self._store_path)
            with contextlib.suppress(OSError):
                os.chmod(self._store_path, 0o600)
            if hasattr(os, "O_DIRECTORY"):
                with contextlib.suppress(OSError):
                    directory_fd = os.open(self._root, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            with contextlib.suppress(FileNotFoundError):
                temporary.unlink()

    def _thread_read_model(
        self,
        thread: Mapping[str, Any],
        *,
        include_events: bool,
        event_limit: int = 200,
    ) -> dict[str, Any]:
        events = thread["events"]
        event_offset = max(0, len(events) - event_limit)
        active_turn = None
        if thread["activeTurnId"] is not None:
            active_turn = self._turn_read_model(
                self._find_turn(thread, thread["activeTurnId"])
            )
        result: dict[str, Any] = {
            "id": thread["id"],
            "agentId": thread["agentId"],
            "title": thread["title"],
            "model": thread["model"],
            "reasoning": thread["reasoning"],
            "mode": thread["mode"],
            "status": thread["status"],
            "archived": thread["archived"],
            "createdAt": thread["createdAt"],
            "updatedAt": thread["updatedAt"],
            "revision": thread["revision"],
            "eventCount": len(events),
            "turnCount": len(thread["turns"]),
            "activeTurn": active_turn,
            "capabilities": list(CAPABILITY_MODES[thread["mode"]]),
            "toolExecutionEnabled": False,
            "canInterrupt": bool(
                active_turn is not None
                and active_turn["status"] in {"queued", "running"}
            ),
            # A connected executor must explicitly attest that resume is
            # supported before the frontend enables Continue.
            "canContinue": False,
            "canArchive": bool(not thread["archived"] and active_turn is None),
            "canUpdateSettings": bool(
                not thread["archived"] and active_turn is None
            ),
        }
        if include_events:
            result["events"] = [
                self._event_read_model(event) for event in events[event_offset:]
            ]
            result["eventOffset"] = event_offset
            result["hasEarlierEvents"] = event_offset > 0
        return result

    @staticmethod
    def _event_read_model(event: Mapping[str, Any]) -> dict[str, Any]:
        result = {
            "id": event["id"],
            "role": event["role"],
            "type": event["type"],
            "content": event["content"],
            "contentFormat": "plain_text",
            "createdAt": event["createdAt"],
            "metadata": event["metadata"],
        }
        if event.get("toolName"):
            result["toolName"] = event["toolName"]
        if event.get("toolCallId"):
            result["toolCallId"] = event["toolCallId"]
        return result

    @staticmethod
    def _turn_read_model(turn: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": turn["id"],
            "status": turn["status"],
            "promptEventId": turn["promptEventId"],
            "requestedAt": turn["requestedAt"],
            "startedAt": turn["startedAt"],
            "completedAt": turn["completedAt"],
            "interruptRequested": turn["interruptRequested"],
            "interruptRequestedAt": turn["interruptRequestedAt"],
            "errorCode": turn["errorCode"],
        }


__all__ = [
    "CAPABILITY_MODES",
    "DEFAULT_MODEL_ALLOWLIST",
    "DEFAULT_REASONING_ALLOWLIST",
    "FullAgentRuntime",
    "FullAgentRuntimeError",
]
