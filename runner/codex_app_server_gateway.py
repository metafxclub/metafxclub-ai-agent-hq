"""Safety boundary between Metafx HQ and the local Codex app-server.

The module is deliberately standalone.  It contains no HTTP routes and does
not depend on the large legacy runner.  A backend can import
``CodexAppServerGateway`` and keep one instance alive, or invoke this file as a
bounded JSON-stdin/JSON-stdout helper.

Important security properties:

* only stdio or an authenticated 127.0.0.1 websocket may be launched;
* ``danger-full-access`` and automatic external effects are never accepted;
* every SDK client receives an explicit approval handler (the SDK default
  currently accepts command/file approvals, so relying on it is unsafe);
* the default approval handler denies every server-initiated action;
* account credentials, environment secrets and raw authentication material
  are never included in public projections;
* model, MCP and plugin discovery is read-only and allowlist projected.

The gateway does not make a live model request during import or discovery.
Tests inject a mock SDK client, so no external tool or model is invoked.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence


JSON_MAX_BYTES = 512_000
PROMPT_MAX_CHARS = 64_000
EVENT_MAX_CHARS = 128_000
MAX_COLLECTION_ITEMS = 200
MAX_SANITIZE_DEPTH = 10
MAX_TURN_INPUT_ITEMS = 12
MAX_TURN_INPUT_IMAGES = 6
MAX_LOCAL_IMAGE_BYTES = 20 * 1024 * 1024
MAX_INLINE_IMAGE_BYTES = 5 * 1024 * 1024
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_ARTIFACTS = 200
MAX_APPROVAL_FILE_CHANGES = 16
MAX_APPROVAL_DIFF_BYTES = 32 * 1024
MAX_APPROVAL_DIFF_BYTES_PER_FILE = 16 * 1024
MAX_APPROVAL_RELATIVE_PATH_CHARS = 512
APPROVAL_PATCH_CACHE_TTL_SECONDS = 300.0
APPROVAL_PATCH_CACHE_MAX_ITEMS = 64

_INTERNAL_FILE_CHANGE_PROJECTION = "_hqTrustedFileChangeProjection"
_BIDI_OR_ZERO_WIDTH_RE = re.compile(
    r"[\u061c\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]"
)

SAFE_IMAGE_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
SAFE_IMAGE_SUFFIXES = {
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
SAFE_IMAGE_DETAILS = frozenset({"auto", "low", "high", "original"})
SAFE_ARTIFACT_MEDIA_TYPES = {
    **SAFE_IMAGE_SUFFIXES,
    ".csv": "text/csv",
    ".css": "text/css",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".gif": "image/gif",
    ".html": "text/html",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".js": "text/javascript",
    ".json": "application/json",
    ".md": "text/markdown",
    ".mp3": "audio/mpeg",
    ".mp4": "video/mp4",
    ".mq4": "text/plain",
    ".mq5": "text/plain",
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".py": "text/x-python",
    ".txt": "text/plain",
    ".webp": "image/webp",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".zip": "application/zip",
}

TERMINAL_TURN_STATUSES = frozenset({"completed", "failed", "interrupted"})
SAFE_ACCOUNT_TYPES = frozenset({"apiKey", "chatgpt", "amazonBedrock"})

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
SAFE_FEATURE_RE = re.compile(r"^[a-z][a-z0-9_]{0,95}$")
SAFE_VERSION_RE = re.compile(r"(?:codex-cli\s+)?([0-9]+(?:\.[0-9A-Za-z-]+){1,5})")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")

_SENSITIVE_KEY_PARTS = (
    "access_token",
    "accesstoken",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "clientsecret",
    "cookie",
    "credential",
    "id_token",
    "idtoken",
    "password",
    "private_key",
    "privatekey",
    "refresh_token",
    "refreshtoken",
    "secret",
    "session_token",
    "sessiontoken",
)

_SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?<![A-Za-z0-9])\d{6,12}:[A-Za-z0-9_-]{30,100}(?![A-Za-z0-9_-])"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|password)\s*[:=]\s*[^\s,;]{4,}"
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class GatewayError(RuntimeError):
    """Structured, frontend-safe gateway failure."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = sanitize_value(dict(details or {}), max_string=1000)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "status": self.code,
            "message": sanitize_text(self.message, 1000),
        }
        if self.details:
            payload["details"] = self.details
        return payload


class PolicyViolation(GatewayError):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(code, message, details=details)


class AgentMode(str, Enum):
    CHAT = "chat"
    WORKSPACE = "workspace"
    COMPUTER_USE = "computer_use"
    FULL_AGENT = "full_agent"


class ApprovalMode(str, Enum):
    """There is intentionally no auto-approve mode."""

    DENY_ALL = "deny_all"
    EXPLICIT = "explicit"


class Transport(str, Enum):
    STDIO = "stdio"
    LOOPBACK_WS = "loopback_ws"


class ProcessStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    STOPPING = "stopping"
    FAILED = "failed"


class SessionStatus(str, Enum):
    CREATING = "creating"
    IDLE = "idle"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"


CAPABILITIES = frozenset(
    {
        "conversation",
        "history",
        "model_selection",
        "workspace_read",
        "workspace_write",
        "shell",
        "web_search",
        "browser",
        "computer_use",
        "mcp",
        "plugins",
        "multi_agent",
        "external_actions",
    }
)

BASE_CAPABILITIES = frozenset({"conversation", "history", "model_selection"})
WRITE_OR_EFFECT_CAPABILITIES = frozenset(
    {
        "workspace_write",
        "shell",
        "browser",
        "computer_use",
        "mcp",
        "plugins",
        "multi_agent",
        "external_actions",
    }
)


@dataclass(frozen=True)
class ModeProfile:
    mode: AgentMode
    enabled_capabilities: frozenset[str]
    default_sandbox: str
    feature_overrides: Mapping[str, bool]

    @property
    def disabled_capabilities(self) -> frozenset[str]:
        return CAPABILITIES - self.enabled_capabilities

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "enabledCapabilities": sorted(self.enabled_capabilities),
            "disabledCapabilities": sorted(self.disabled_capabilities),
            "defaultSandbox": self.default_sandbox,
            "featureOverrides": dict(sorted(self.feature_overrides.items())),
        }


def _feature_overrides_for(capabilities: frozenset[str]) -> dict[str, bool]:
    """Translate product capabilities into Codex feature gates.

    These feature flags are defense in depth.  The sandbox and approval
    handler remain authoritative because availability of a feature flag is not
    itself authorization to invoke a tool.
    """

    return {
        "apps": "mcp" in capabilities,
        "browser_use": "browser" in capabilities,
        "browser_use_external": "external_actions" in capabilities,
        "computer_use": "computer_use" in capabilities,
        "guardian_approval": True,
        "in_app_browser": "browser" in capabilities,
        "multi_agent": "multi_agent" in capabilities,
        "plugins": "plugins" in capabilities,
        "shell_tool": "shell" in capabilities,
        "skill_search": "plugins" in capabilities,
    }


_CHAT_CAPS = BASE_CAPABILITIES
_WORKSPACE_CAPS = _CHAT_CAPS | frozenset(
    {"workspace_read", "workspace_write", "shell"}
)
_COMPUTER_CAPS = _WORKSPACE_CAPS | frozenset(
    {"web_search", "browser", "computer_use"}
)
_FULL_CAPS = _COMPUTER_CAPS | frozenset(
    {"mcp", "plugins", "multi_agent", "external_actions"}
)

MODE_PROFILES: Mapping[AgentMode, ModeProfile] = {
    AgentMode.CHAT: ModeProfile(
        AgentMode.CHAT,
        _CHAT_CAPS,
        "read-only",
        _feature_overrides_for(_CHAT_CAPS),
    ),
    AgentMode.WORKSPACE: ModeProfile(
        AgentMode.WORKSPACE,
        _WORKSPACE_CAPS,
        "workspace-write",
        _feature_overrides_for(_WORKSPACE_CAPS),
    ),
    AgentMode.COMPUTER_USE: ModeProfile(
        AgentMode.COMPUTER_USE,
        _COMPUTER_CAPS,
        "workspace-write",
        _feature_overrides_for(_COMPUTER_CAPS),
    ),
    AgentMode.FULL_AGENT: ModeProfile(
        AgentMode.FULL_AGENT,
        _FULL_CAPS,
        "workspace-write",
        _feature_overrides_for(_FULL_CAPS),
    ),
}


def get_mode_profile(mode: AgentMode | str) -> ModeProfile:
    try:
        normalized = mode if isinstance(mode, AgentMode) else AgentMode(str(mode))
    except ValueError as exc:
        raise PolicyViolation("invalid_mode", "Unknown Full Agent mode.") from exc
    return MODE_PROFILES[normalized]


def sanitize_text(value: object, limit: int = EVENT_MAX_CHARS) -> str:
    text = str(value or "").replace("\x00", "")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    if len(text) > limit:
        text = text[:limit] + "...[truncated]"
    return text


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def is_sensitive_key(value: object) -> bool:
    normalized = _normalized_key(value)
    return any(_normalized_key(part) in normalized for part in _SENSITIVE_KEY_PARTS)


def sanitize_value(
    value: Any,
    *,
    depth: int = 0,
    max_string: int = EVENT_MAX_CHARS,
) -> Any:
    if depth >= MAX_SANITIZE_DEPTH:
        return "[DEPTH_LIMIT]"
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            return None
        return value
    if isinstance(value, str):
        return sanitize_text(value, max_string)
    if isinstance(value, Enum):
        return sanitize_value(value.value, depth=depth + 1, max_string=max_string)
    if hasattr(value, "model_dump"):
        try:
            value = value.model_dump(by_alias=True, mode="json")
        except TypeError:
            value = value.model_dump(by_alias=True)
    elif hasattr(value, "__dataclass_fields__"):
        return sanitize_value(
            value.to_dict() if hasattr(value, "to_dict") else vars(value),
            depth=depth + 1,
            max_string=max_string,
        )
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for index, (raw_key, item) in enumerate(value.items()):
            if index >= MAX_COLLECTION_ITEMS:
                output["_truncated"] = True
                break
            key = sanitize_text(raw_key, 120)
            if is_sensitive_key(key):
                output[key] = "[REDACTED]"
                continue
            # Paths to auth stores and raw process environments are not
            # frontend data, even when they do not contain a token inline.
            if _normalized_key(key) in {
                "environment",
                "env",
                "headers",
                "authfile",
                "tokenfile",
            }:
                output[key] = "[REDACTED]"
                continue
            output[key] = sanitize_value(
                item,
                depth=depth + 1,
                max_string=max_string,
            )
        return output
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)
        projected = [
            sanitize_value(item, depth=depth + 1, max_string=max_string)
            for item in items[:MAX_COLLECTION_ITEMS]
        ]
        if len(items) > MAX_COLLECTION_ITEMS:
            projected.append("[TRUNCATED]")
        return projected
    return sanitize_text(value, max_string)


def contains_potential_secret(value: object) -> bool:
    text = str(value or "")
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS)


def _normalize_attachment_roots(
    values: Sequence[str | os.PathLike[str]] | None,
) -> tuple[Path, ...]:
    """Resolve explicit managed attachment roots.

    Local image input and downloadable output are disabled when no roots are
    configured.  A root is configuration supplied by the trusted backend,
    never a path selected by a frontend request.
    """

    if values is None:
        return ()
    if isinstance(values, (str, bytes, os.PathLike)):
        raise PolicyViolation(
            "invalid_attachment_roots",
            "Attachment roots must be a sequence of absolute directories.",
        )
    roots: list[Path] = []
    for raw in values:
        candidate = Path(raw)
        if not candidate.is_absolute():
            raise PolicyViolation(
                "invalid_attachment_root",
                "Attachment roots must be absolute directories.",
            )
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise PolicyViolation(
                "invalid_attachment_root",
                "An attachment root is unavailable.",
            ) from exc
        if not resolved.is_dir() or resolved == Path(resolved.anchor):
            raise PolicyViolation(
                "invalid_attachment_root",
                "Attachment roots must be bounded directories.",
            )
        if resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def _is_link_or_reparse(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except OSError:
        return True
    attributes = int(getattr(info, "st_file_attributes", 0) or 0)
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return stat.S_ISLNK(info.st_mode) or bool(attributes & reparse_flag)


def _managed_file_path(
    raw_path: object,
    roots: Sequence[Path],
    *,
    unavailable_code: str,
) -> Path:
    if not roots:
        raise PolicyViolation(
            "attachments_not_configured",
            "Managed attachment storage is not configured.",
        )
    text = str(raw_path or "")
    if (
        not text
        or len(text) > 4096
        or "\x00" in text
        or contains_potential_secret(text)
    ):
        raise PolicyViolation(unavailable_code, "Attachment path is invalid.")
    candidate = Path(text)
    if not candidate.is_absolute():
        raise PolicyViolation(unavailable_code, "Attachment path must be absolute.")
    lexical = Path(os.path.abspath(str(candidate)))
    selected_root: Path | None = None
    relative: Path | None = None
    for root in roots:
        try:
            relative = lexical.relative_to(root)
            selected_root = root
            break
        except ValueError:
            continue
    if selected_root is None or relative is None or not relative.parts:
        raise PolicyViolation(unavailable_code, "Attachment path is outside managed storage.")

    # Reject links/junctions at every request-controlled component.  Checking
    # only the final resolved path would allow an in-root alias to change
    # between validation and the app-server opening the file.
    cursor = selected_root
    for part in relative.parts:
        cursor = cursor / part
        if _is_link_or_reparse(cursor):
            raise PolicyViolation(unavailable_code, "Linked attachment paths are not allowed.")
    try:
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(selected_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise PolicyViolation(unavailable_code, "Attachment path is unavailable.") from exc
    if not resolved.is_file():
        raise PolicyViolation(unavailable_code, "Attachment must be a regular file.")
    return resolved


def _sniff_image_media_type(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError:
        return None
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def _validate_local_image(path_value: object, roots: Sequence[Path]) -> Path:
    path = _managed_file_path(
        path_value,
        roots,
        unavailable_code="invalid_local_image",
    )
    try:
        byte_size = path.stat().st_size
    except OSError as exc:
        raise PolicyViolation("invalid_local_image", "Local image is unavailable.") from exc
    if byte_size <= 0 or byte_size > MAX_LOCAL_IMAGE_BYTES:
        raise PolicyViolation(
            "invalid_local_image_size",
            "Local image exceeded the safe size limit.",
        )
    expected_media_type = SAFE_IMAGE_SUFFIXES.get(path.suffix.lower())
    actual_media_type = _sniff_image_media_type(path)
    if expected_media_type is None or actual_media_type != expected_media_type:
        raise PolicyViolation(
            "invalid_local_image_type",
            "Local image type is unsupported or does not match its contents.",
        )
    return path


def _validate_inline_image(url_value: object) -> str:
    url = str(url_value or "")
    match = re.fullmatch(
        r"data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/]*={0,2})",
        url,
        flags=re.IGNORECASE,
    )
    if match is None:
        raise PolicyViolation(
            "remote_image_blocked",
            "Image input must be a supported base64 data URL.",
        )
    media_type = match.group(1).lower()
    if media_type not in SAFE_IMAGE_MEDIA_TYPES:
        raise PolicyViolation("invalid_inline_image_type", "Inline image type is unsupported.")
    encoded = match.group(2)
    if len(encoded) > ((MAX_INLINE_IMAGE_BYTES + 2) // 3) * 4:
        raise PolicyViolation(
            "invalid_inline_image_size",
            "Inline image exceeded the safe size limit.",
        )
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise PolicyViolation("invalid_inline_image", "Inline image data is invalid.") from exc
    if not payload or len(payload) > MAX_INLINE_IMAGE_BYTES:
        raise PolicyViolation(
            "invalid_inline_image_size",
            "Inline image exceeded the safe size limit.",
        )
    if media_type == "image/png" and not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise PolicyViolation("invalid_inline_image_type", "Inline image contents are invalid.")
    if media_type == "image/jpeg" and not payload.startswith(b"\xff\xd8\xff"):
        raise PolicyViolation("invalid_inline_image_type", "Inline image contents are invalid.")
    if media_type == "image/webp" and not (
        len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP"
    ):
        raise PolicyViolation("invalid_inline_image_type", "Inline image contents are invalid.")
    return url


def _validated_image_detail(value: object) -> str | None:
    if value is None or value == "":
        return None
    detail = str(value)
    if detail not in SAFE_IMAGE_DETAILS:
        raise PolicyViolation("invalid_image_detail", "Image detail level is invalid.")
    return detail


def validate_turn_input(
    prompt: object,
    input_items: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None,
    *,
    attachment_roots: Sequence[Path],
) -> tuple[str | list[dict[str, Any]], int]:
    """Return SDK-ready input and the number of image parts.

    The legacy string form is preserved when no structured items are supplied.
    Structured requests have a small allowlisted schema so arbitrary SDK input
    variants (skills, mentions, audio, remote URLs) cannot be smuggled through.
    """

    prompt_text = str(prompt or "").strip()
    if not prompt_text or len(prompt_text) > PROMPT_MAX_CHARS:
        raise PolicyViolation("invalid_prompt", "Prompt is empty or too long.")
    if contains_potential_secret(prompt_text):
        raise PolicyViolation(
            "secret_blocked",
            "Prompt appears to contain authentication material.",
        )
    if input_items is None:
        return prompt_text, 0
    if isinstance(input_items, Mapping):
        raw_items: list[Mapping[str, Any]] = [input_items]
    elif isinstance(input_items, Sequence) and not isinstance(input_items, (str, bytes)):
        raw_items = list(input_items)
    else:
        raise PolicyViolation("invalid_turn_input", "Structured turn input is invalid.")
    if len(raw_items) + 1 > MAX_TURN_INPUT_ITEMS:
        raise PolicyViolation("too_many_input_items", "Turn input has too many items.")

    output: list[dict[str, Any]] = [{"type": "text", "text": prompt_text}]
    image_count = 0
    total_text_chars = len(prompt_text)
    for raw in raw_items:
        if not isinstance(raw, Mapping):
            raise PolicyViolation("invalid_turn_input", "Turn input item is invalid.")
        item_type = str(raw.get("type") or "")
        if item_type == "text":
            if set(raw) - {"type", "text"}:
                raise PolicyViolation("invalid_turn_input", "Text input contains unsupported fields.")
            text_value = str(raw.get("text") or "").strip()
            total_text_chars += len(text_value)
            if (
                not text_value
                or total_text_chars > PROMPT_MAX_CHARS
                or contains_potential_secret(text_value)
            ):
                raise PolicyViolation("invalid_prompt", "Text input is empty, unsafe, or too long.")
            output.append({"type": "text", "text": text_value})
            continue
        if item_type == "localImage":
            if set(raw) - {"type", "path", "detail"}:
                raise PolicyViolation(
                    "invalid_turn_input",
                    "Local image input contains unsupported fields.",
                )
            path = _validate_local_image(raw.get("path"), attachment_roots)
            item: dict[str, Any] = {"type": "localImage", "path": str(path)}
        elif item_type == "image":
            if set(raw) - {"type", "url", "detail"}:
                raise PolicyViolation(
                    "invalid_turn_input",
                    "Image input contains unsupported fields.",
                )
            item = {"type": "image", "url": _validate_inline_image(raw.get("url"))}
        else:
            raise PolicyViolation(
                "unsupported_turn_input",
                "Only text and managed image input are supported.",
            )
        image_count += 1
        if image_count > MAX_TURN_INPUT_IMAGES:
            raise PolicyViolation("too_many_input_images", "Turn input has too many images.")
        detail = _validated_image_detail(raw.get("detail"))
        if detail is not None:
            item["detail"] = detail
        output.append(item)
    return output, image_count


def parse_app_server_event(raw: str | bytes | Mapping[str, Any] | Any) -> dict[str, Any]:
    """Parse and redact one app-server message without trusting its shape."""

    if isinstance(raw, bytes):
        if len(raw) > JSON_MAX_BYTES:
            raise GatewayError("event_too_large", "App-server event exceeded the safe limit.")
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        if len(raw.encode("utf-8", errors="replace")) > JSON_MAX_BYTES:
            raise GatewayError("event_too_large", "App-server event exceeded the safe limit.")
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GatewayError("invalid_event", "App-server returned invalid JSON.") from exc
    if hasattr(raw, "method") and hasattr(raw, "payload"):
        raw = {"method": raw.method, "params": raw.payload}
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump(by_alias=True, mode="json")
    if not isinstance(raw, Mapping):
        raise GatewayError("invalid_event", "App-server event must be a JSON object.")

    projected: dict[str, Any] = {}
    if "method" in raw:
        method = str(raw.get("method") or "")
        if not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,160}", method):
            raise GatewayError("invalid_event", "App-server event method is invalid.")
        projected["method"] = method
    if "id" in raw and isinstance(raw.get("id"), (str, int)):
        projected["id"] = sanitize_text(raw.get("id"), 128)
    for key in ("params", "result", "error"):
        if key in raw:
            projected[key] = sanitize_value(raw.get(key))
    if not projected:
        raise GatewayError("invalid_event", "App-server event had no supported fields.")
    return projected


def _plain(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True, mode="json")
    if isinstance(value, Mapping):
        return dict(value)
    raise GatewayError("invalid_sdk_response", "Codex returned an invalid response.")


def project_model_catalog(value: Any) -> list[dict[str, Any]]:
    payload = _plain(value) if not isinstance(value, list) else {"data": value}
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    models: list[dict[str, Any]] = []
    for item in data[:MAX_COLLECTION_ITEMS]:
        if not isinstance(item, Mapping):
            if hasattr(item, "model_dump"):
                item = item.model_dump(by_alias=True, mode="json")
            else:
                continue
        model_id = str(item.get("model") or item.get("id") or "")
        if not SAFE_MODEL_RE.fullmatch(model_id):
            continue
        efforts: list[str] = []
        raw_efforts = item.get("supportedReasoningEfforts") or []
        if isinstance(raw_efforts, list):
            for effort in raw_efforts:
                if isinstance(effort, Mapping):
                    effort = effort.get("reasoningEffort") or effort.get("effort")
                effort_value = str(effort or "")
                if effort_value in {"none", "minimal", "low", "medium", "high", "xhigh"}:
                    efforts.append(effort_value)
        default_effort = str(item.get("defaultReasoningEffort") or "")
        if default_effort and default_effort not in efforts:
            efforts.append(default_effort)
        models.append(
            {
                "id": sanitize_text(item.get("id") or model_id, 128),
                "model": model_id,
                "displayName": sanitize_text(item.get("displayName") or model_id, 160),
                "description": sanitize_text(item.get("description") or "", 1000),
                "isDefault": bool(item.get("isDefault", False)),
                "hidden": bool(item.get("hidden", False)),
                "defaultReasoningEffort": default_effort or None,
                "supportedReasoningEfforts": sorted(set(efforts)),
                "inputModalities": [
                    sanitize_text(entry, 32)
                    for entry in (item.get("inputModalities") or [])[:10]
                    if str(entry) in {"text", "image", "audio"}
                ],
                "supportsPersonality": bool(item.get("supportsPersonality", False)),
            }
        )
    return models


def project_account_authentication(value: Any) -> dict[str, Any]:
    """Return the minimum account state needed for readiness decisions.

    ``account/read`` may contain a ChatGPT email or provider-specific account
    details.  None of those values cross the gateway boundary.  Unknown or
    malformed account variants fail closed unless the server explicitly says
    that OpenAI authentication is not required.
    """

    payload = _plain(value)
    requires_openai_auth = payload.get("requiresOpenaiAuth") is not False
    account = payload.get("account")
    raw_account_type = str(account.get("type") or "") if isinstance(account, Mapping) else ""
    account_type = raw_account_type if raw_account_type in SAFE_ACCOUNT_TYPES else None
    authenticated = bool(account_type is not None or not requires_openai_auth)
    return {
        "authenticated": authenticated,
        "requiresOpenaiAuth": requires_openai_auth,
        "accountType": account_type,
    }


def _project_tool(tool_name: str, value: Any) -> dict[str, Any]:
    item = value if isinstance(value, Mapping) else {}
    return {
        "name": sanitize_text(tool_name, 160),
        "title": sanitize_text(item.get("title") or tool_name, 200),
        "description": sanitize_text(item.get("description") or "", 1000),
    }


def project_mcp_status(value: Any) -> list[dict[str, Any]]:
    payload = _plain(value)
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    servers: list[dict[str, Any]] = []
    for raw in data[:MAX_COLLECTION_ITEMS]:
        if hasattr(raw, "model_dump"):
            raw = raw.model_dump(by_alias=True, mode="json")
        if not isinstance(raw, Mapping):
            continue
        tools = raw.get("tools") if isinstance(raw.get("tools"), Mapping) else {}
        servers.append(
            {
                "name": sanitize_text(raw.get("name") or "", 160),
                "authStatus": sanitize_text(raw.get("authStatus") or "unknown", 60),
                "toolCount": len(tools),
                "tools": [
                    _project_tool(str(name), tool)
                    for name, tool in list(tools.items())[:MAX_COLLECTION_ITEMS]
                ],
                "resourceCount": len(raw.get("resources") or [])
                if isinstance(raw.get("resources"), list)
                else 0,
                "resourceTemplateCount": len(raw.get("resourceTemplates") or [])
                if isinstance(raw.get("resourceTemplates"), list)
                else 0,
            }
        )
    return servers


def project_plugin_catalog(value: Any) -> list[dict[str, Any]]:
    payload = _plain(value)
    marketplaces = payload.get("marketplaces")
    if not isinstance(marketplaces, list):
        return []
    plugins: list[dict[str, Any]] = []
    for marketplace in marketplaces[:MAX_COLLECTION_ITEMS]:
        if hasattr(marketplace, "model_dump"):
            marketplace = marketplace.model_dump(by_alias=True, mode="json")
        if not isinstance(marketplace, Mapping):
            continue
        market_name = sanitize_text(marketplace.get("name") or "local", 160)
        entries = marketplace.get("plugins")
        if not isinstance(entries, list):
            continue
        for entry in entries[:MAX_COLLECTION_ITEMS]:
            if hasattr(entry, "model_dump"):
                entry = entry.model_dump(by_alias=True, mode="json")
            if not isinstance(entry, Mapping):
                continue
            plugins.append(
                {
                    "id": sanitize_text(entry.get("id") or "", 160),
                    "name": sanitize_text(entry.get("name") or "", 200),
                    "version": sanitize_text(entry.get("version") or entry.get("localVersion") or "", 80),
                    "enabled": bool(entry.get("enabled", False)),
                    "installed": bool(entry.get("installed", False)),
                    "availability": sanitize_text(entry.get("availability") or "unknown", 80),
                    "authPolicy": sanitize_text(entry.get("authPolicy") or "unknown", 80),
                    "marketplace": market_name,
                }
            )
    return plugins


ArtifactProjector = Callable[[object, str], dict[str, Any] | None]


def _project_thread_item(
    value: Any,
    *,
    artifact_projector: ArtifactProjector | None = None,
) -> dict[str, Any]:
    """Project transcript text while omitting raw tool inputs/outputs and paths."""

    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True, mode="json")
    if not isinstance(value, Mapping):
        return {}
    item_type = sanitize_text(value.get("type") or "unknown", 80)
    output: dict[str, Any] = {
        "id": sanitize_text(value.get("id") or "", 128),
        "type": item_type,
    }
    if item_type == "agentMessage":
        output["text"] = sanitize_text(value.get("text") or "", 40_000)
        output["phase"] = sanitize_text(value.get("phase") or "", 60) or None
    elif item_type == "userMessage":
        content = value.get("content")
        safe_text: list[str] = []
        if isinstance(content, list):
            for part in content[:20]:
                if not isinstance(part, Mapping):
                    continue
                if str(part.get("type") or "") in {"text", "inputText"}:
                    safe_text.append(sanitize_text(part.get("text") or "", 4000))
        output["text"] = sanitize_text("\n".join(safe_text), 8000)
    elif item_type == "reasoning":
        summary = value.get("summary")
        output["summary"] = sanitize_text(
            "\n".join(str(part) for part in summary[:20])
            if isinstance(summary, list)
            else "",
            8000,
        )
    elif item_type == "imageView":
        artifact = (
            artifact_projector(value.get("path"), "image")
            if artifact_projector is not None
            else None
        )
        output["artifact"] = artifact
        output["pathHidden"] = artifact is None
    elif item_type == "imageGeneration":
        output["status"] = sanitize_text(value.get("status") or "unknown", 60)
        output["transparentBackground"] = bool(
            value.get("transparentBackground", False)
        )
        artifact = (
            artifact_projector(value.get("savedPath"), "image")
            if artifact_projector is not None and value.get("savedPath")
            else None
        )
        output["artifact"] = artifact
        output["pathHidden"] = artifact is None
    elif item_type in {"artifact", "artifactOutput", "file", "fileOutput"}:
        path_value = next(
            (
                value.get(key)
                for key in ("savedPath", "outputPath", "filePath", "path")
                if value.get(key)
            ),
            None,
        )
        artifact = (
            artifact_projector(path_value, "file")
            if artifact_projector is not None and path_value
            else None
        )
        output["status"] = sanitize_text(value.get("status") or "unknown", 60)
        output["artifact"] = artifact
        output["pathHidden"] = artifact is None
    else:
        # Tool output, commands, arguments, paths, patches and MCP resources
        # are deliberately absent.  UI history receives only lifecycle data.
        for key in ("status", "name", "title", "tool", "server", "pluginId", "durationMs"):
            if key in value:
                output[key] = sanitize_value(value.get(key), max_string=300)
        raw_error = value.get("error")
        if isinstance(raw_error, Mapping):
            output["error"] = {
                "code": sanitize_text(raw_error.get("code") or "tool_error", 100),
                "message": sanitize_text(raw_error.get("message") or "Tool failed.", 1000),
            }
    return output


def _project_turn(
    value: Any,
    *,
    artifact_projector: ArtifactProjector | None = None,
) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True, mode="json")
    if not isinstance(value, Mapping):
        return {}
    raw_items_value = value.get("items")
    items_shape_valid = raw_items_value is None or isinstance(raw_items_value, list)
    raw_items = raw_items_value if isinstance(raw_items_value, list) else []
    projected_sources = raw_items[:MAX_COLLECTION_ITEMS]
    items = [
        projected
        for projected in (
            _project_thread_item(item, artifact_projector=artifact_projector)
            for item in projected_sources
        )
        if projected
    ]
    assistant_parts = [
        str(item.get("text") or "")
        for item in items
        if item.get("type") == "agentMessage" and item.get("text")
    ]
    raw_error = value.get("error")
    if isinstance(raw_error, Mapping):
        error = {
            "code": sanitize_text(raw_error.get("code") or "turn_failed", 100),
            "message": sanitize_text(raw_error.get("message") or "Turn failed.", 2000),
        }
    elif raw_error:
        error = {"code": "turn_failed", "message": sanitize_text(raw_error, 2000)}
    else:
        error = None
    return {
        "id": sanitize_text(value.get("id") or "", 128),
        "status": sanitize_text(value.get("status") or "unknown", 60),
        "startedAt": value.get("startedAt"),
        "completedAt": value.get("completedAt"),
        "durationMs": value.get("durationMs"),
        "error": error,
        "assistantText": sanitize_text("\n".join(assistant_parts), 40_000),
        "items": items,
        "itemCount": len(raw_items),
        "itemsTruncated": bool(
            not items_shape_valid
            or len(raw_items) > MAX_COLLECTION_ITEMS
            or len(items) != len(projected_sources)
        ),
    }


def project_thread(
    value: Any,
    *,
    include_turns: bool = True,
    artifact_projector: ArtifactProjector | None = None,
) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True, mode="json")
    if not isinstance(value, Mapping):
        return {}
    output = {
        "id": sanitize_text(value.get("id") or "", 128),
        "name": sanitize_text(value.get("name") or "", 300),
        "preview": sanitize_text(value.get("preview") or "", 2000),
        "status": sanitize_text(value.get("status") or "unknown", 60),
        "createdAt": value.get("createdAt"),
        "updatedAt": value.get("updatedAt"),
        "recencyAt": value.get("recencyAt"),
        "modelProvider": sanitize_text(value.get("modelProvider") or "", 80),
        "ephemeral": bool(value.get("ephemeral", False)),
        "agentNickname": sanitize_text(value.get("agentNickname") or "", 160),
        "agentRole": sanitize_text(value.get("agentRole") or "", 160),
        "parentThreadId": sanitize_text(value.get("parentThreadId") or "", 128),
        "forkedFromId": sanitize_text(value.get("forkedFromId") or "", 128),
    }
    if include_turns:
        raw_turns = value.get("turns") or []
        output["turns"] = [
            _project_turn(turn, artifact_projector=artifact_projector)
            for turn in raw_turns[:MAX_COLLECTION_ITEMS]
        ] if isinstance(raw_turns, list) else []
    return output


@dataclass(frozen=True)
class ThreadPolicyRequest:
    agent_id: str
    mode: AgentMode | str
    model: str
    reasoning_effort: str = "medium"
    requested_capabilities: frozenset[str] | None = None
    sandbox: str | None = None
    approval_mode: ApprovalMode | str = ApprovalMode.DENY_ALL
    workspace_roots: tuple[str, ...] = ()
    external_effects: str = "approval-required"
    auto_external_effects: bool = False

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ThreadPolicyRequest":
        capabilities = value.get("requestedCapabilities", value.get("capabilities"))
        if capabilities is None:
            normalized_caps = None
        elif isinstance(capabilities, (list, tuple, set, frozenset)):
            normalized_caps = frozenset(str(item) for item in capabilities)
        else:
            raise PolicyViolation(
                "invalid_capabilities",
                "Requested capabilities must be a list.",
            )
        roots = value.get("workspaceRoots") or (
            [value.get("cwd")] if value.get("cwd") else ()
        )
        if not isinstance(roots, (list, tuple)):
            raise PolicyViolation("invalid_workspace", "Workspace roots must be a list.")
        return cls(
            agent_id=str(value.get("agentId") or ""),
            mode=str(value.get("mode") or AgentMode.CHAT.value),
            model=str(value.get("model") or ""),
            reasoning_effort=str(value.get("reasoningEffort") or "medium"),
            requested_capabilities=normalized_caps,
            sandbox=str(value.get("sandbox")) if value.get("sandbox") is not None else None,
            approval_mode=str(value.get("approvalMode") or ApprovalMode.DENY_ALL.value),
            workspace_roots=tuple(str(item) for item in roots),
            external_effects=str(value.get("externalEffects") or "approval-required"),
            auto_external_effects=bool(value.get("autoExternalEffects", False)),
        )


@dataclass(frozen=True)
class ValidatedThreadPolicy:
    agent_id: str
    mode: AgentMode
    model: str
    reasoning_effort: str
    capabilities: frozenset[str]
    sandbox: str
    approval_mode: ApprovalMode
    approval_policy: str
    workspace_roots: tuple[str, ...]
    external_effects: str
    feature_overrides: Mapping[str, bool]

    @property
    def cwd(self) -> str | None:
        return self.workspace_roots[0] if self.workspace_roots else None

    def to_dict(self) -> dict[str, Any]:
        profile = MODE_PROFILES[self.mode]
        return {
            "agentId": self.agent_id,
            "mode": self.mode.value,
            "model": self.model,
            "reasoningEffort": self.reasoning_effort,
            "enabledCapabilities": sorted(self.capabilities),
            "disabledCapabilities": sorted(CAPABILITIES - self.capabilities),
            "modeDisabledCapabilities": sorted(profile.disabled_capabilities),
            "sandbox": self.sandbox,
            "approvalMode": self.approval_mode.value,
            "approvalPolicy": self.approval_policy,
            "workspaceRoots": list(self.workspace_roots),
            "externalEffects": self.external_effects,
            "autoExternalEffects": False,
            "featureOverrides": dict(sorted(self.feature_overrides.items())),
        }

    def thread_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            "model_reasoning_effort": self.reasoning_effort,
            "features": dict(self.feature_overrides),
        }
        if "mcp" not in self.capabilities:
            config["mcp_servers"] = {}
        return config

    def sandbox_policy(self) -> dict[str, Any]:
        network = bool({"web_search", "browser", "computer_use"} & self.capabilities)
        if self.sandbox == "read-only":
            return {"type": "readOnly", "networkAccess": network}
        return {
            "type": "workspaceWrite",
            "writableRoots": list(self.workspace_roots),
            "networkAccess": network,
            "excludeSlashTmp": True,
            "excludeTmpdirEnvVar": True,
        }


def _normalize_workspace_root(value: str) -> str:
    if not value or "\x00" in value:
        raise PolicyViolation("invalid_workspace", "Workspace root is invalid.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise PolicyViolation("invalid_workspace", "Workspace root must be absolute.")
    normalized = path.resolve(strict=False)
    if normalized == Path(normalized.anchor):
        raise PolicyViolation(
            "workspace_too_broad",
            "A filesystem or drive root cannot be used as an Agent workspace.",
        )
    return str(normalized)


def _catalog_model_efforts(
    model_catalog: Sequence[Mapping[str, Any]] | None,
) -> dict[str, frozenset[str]]:
    output: dict[str, frozenset[str]] = {}
    for item in model_catalog or ():
        name = str(item.get("model") or item.get("id") or "")
        efforts = item.get("supportedReasoningEfforts") or ()
        if name:
            output[name] = frozenset(str(effort) for effort in efforts)
    return output


def validate_thread_policy(
    request: ThreadPolicyRequest | Mapping[str, Any],
    *,
    model_catalog: Sequence[Mapping[str, Any]] | None = None,
    runtime_capabilities: Iterable[str] | None = None,
) -> ValidatedThreadPolicy:
    if isinstance(request, Mapping):
        request = ThreadPolicyRequest.from_dict(request)
    if not SAFE_ID_RE.fullmatch(request.agent_id):
        raise PolicyViolation("invalid_agent", "Agent ID is invalid.")
    profile = get_mode_profile(request.mode)
    if not SAFE_MODEL_RE.fullmatch(request.model):
        raise PolicyViolation("invalid_model", "Model identifier is invalid.")

    valid_efforts = {"none", "minimal", "low", "medium", "high", "xhigh"}
    if request.reasoning_effort not in valid_efforts:
        raise PolicyViolation("invalid_reasoning", "Reasoning effort is invalid.")
    catalog = _catalog_model_efforts(model_catalog)
    if catalog:
        if request.model not in catalog:
            raise PolicyViolation("model_unavailable", "Selected model is unavailable.")
        supported = catalog[request.model]
        if supported and request.reasoning_effort not in supported:
            raise PolicyViolation(
                "reasoning_unavailable",
                "Selected model does not support this reasoning effort.",
            )

    capabilities = request.requested_capabilities
    if capabilities is None:
        capabilities = profile.enabled_capabilities
    unknown = capabilities - CAPABILITIES
    if unknown:
        raise PolicyViolation(
            "unknown_capability",
            "One or more requested capabilities are unknown.",
            capabilities=sorted(unknown),
        )
    outside_mode = capabilities - profile.enabled_capabilities
    if outside_mode:
        raise PolicyViolation(
            "capability_not_allowed",
            "Capability is not allowed in the selected mode.",
            capabilities=sorted(outside_mode),
        )
    if not BASE_CAPABILITIES.issubset(capabilities):
        raise PolicyViolation(
            "missing_base_capability",
            "Conversation, history and model selection are required.",
        )
    if runtime_capabilities is not None:
        missing = capabilities - frozenset(str(item) for item in runtime_capabilities)
        if missing:
            raise PolicyViolation(
                "runtime_capability_unavailable",
                "Runtime does not currently provide every requested capability.",
                capabilities=sorted(missing),
            )

    sandbox = request.sandbox or profile.default_sandbox
    if sandbox == "danger-full-access":
        raise PolicyViolation(
            "danger_full_access_denied",
            "danger-full-access is prohibited by HQ policy.",
        )
    if sandbox not in {"read-only", "workspace-write"}:
        raise PolicyViolation("invalid_sandbox", "Sandbox mode is invalid.")
    if profile.mode is AgentMode.CHAT and sandbox != "read-only":
        raise PolicyViolation("sandbox_not_allowed", "Chat mode must be read-only.")

    try:
        approval_mode = (
            request.approval_mode
            if isinstance(request.approval_mode, ApprovalMode)
            else ApprovalMode(str(request.approval_mode))
        )
    except ValueError as exc:
        raise PolicyViolation(
            "invalid_approval_mode",
            "Approval mode must be deny_all or explicit.",
        ) from exc
    if request.auto_external_effects:
        raise PolicyViolation(
            "automatic_external_effects_denied",
            "Automatic external effects are prohibited.",
        )
    if request.external_effects != "approval-required":
        raise PolicyViolation(
            "external_effect_policy_denied",
            "External effects must always require explicit approval.",
        )
    if "external_actions" in capabilities and approval_mode is not ApprovalMode.EXPLICIT:
        raise PolicyViolation(
            "explicit_approval_required",
            "Full external actions require explicit approval mode.",
        )

    roots = tuple(dict.fromkeys(_normalize_workspace_root(root) for root in request.workspace_roots))
    if len(roots) > 8:
        raise PolicyViolation("too_many_workspaces", "At most eight workspace roots are allowed.")
    if ("workspace_read" in capabilities or "workspace_write" in capabilities) and not roots:
        raise PolicyViolation(
            "workspace_required",
            "This mode requires an explicitly scoped workspace root.",
        )
    if sandbox == "workspace-write" and "workspace_write" not in capabilities:
        raise PolicyViolation(
            "workspace_write_not_allowed",
            "Writable sandbox requires workspace_write capability.",
        )

    feature_overrides = _feature_overrides_for(capabilities)
    approval_policy = "never" if approval_mode is ApprovalMode.DENY_ALL else "on-request"
    return ValidatedThreadPolicy(
        agent_id=request.agent_id,
        mode=profile.mode,
        model=request.model,
        reasoning_effort=request.reasoning_effort,
        capabilities=frozenset(capabilities),
        sandbox=sandbox,
        approval_mode=approval_mode,
        approval_policy=approval_policy,
        workspace_roots=roots,
        external_effects="approval-required",
        feature_overrides=feature_overrides,
    )


def _sensitive_environment_name(name: str) -> bool:
    upper = name.upper()
    return any(
        marker in upper
        for marker in (
            "API_KEY",
            "APIKEY",
            "TOKEN",
            "SECRET",
            "PASSWORD",
            "PRIVATE_KEY",
            "COOKIE",
        )
    )


def sanitized_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return SDK overrides that blank inherited secret-like variables.

    The Python SDK merges the supplied mapping into ``os.environ``.  Therefore
    sensitive inherited names must be explicitly overwritten with an empty
    value instead of merely being omitted.
    """

    source = dict(os.environ if source is None else source)
    output: dict[str, str] = {}
    allowed = {
        "APPDATA",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LOCALAPPDATA",
        "PATH",
        "Path",
        "PROGRAMDATA",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "WINDIR",
    }
    for key, value in source.items():
        if _sensitive_environment_name(key):
            output[key] = ""
        elif key in allowed:
            output[key] = str(value)
    for canonical in (
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "GOOGLE_CLIENT_SECRET",
        "TELEGRAM_BOT_TOKEN",
    ):
        output[canonical] = ""
    output["PYTHONIOENCODING"] = "utf-8"
    return output


@dataclass(frozen=True)
class AppServerLaunchSpec:
    argv: tuple[str, ...]
    transport: Transport
    endpoint: str
    auth_mode: str
    environment: Mapping[str, str]
    cwd: str | None = None

    def to_dict(self, *, include_environment: bool = False) -> dict[str, Any]:
        value: dict[str, Any] = {
            "argv": list(self.argv),
            "transport": self.transport.value,
            "endpoint": self.endpoint,
            "authMode": self.auth_mode,
            "cwd": self.cwd,
            "environmentSanitized": True,
        }
        if include_environment:
            value["environment"] = dict(self.environment)
        else:
            value["environmentKeys"] = sorted(self.environment)
        return value


def build_app_server_launch_spec(
    codex_bin: str | os.PathLike[str],
    *,
    transport: Transport | str = Transport.STDIO,
    host: str = "127.0.0.1",
    port: int | None = None,
    token_file: str | os.PathLike[str] | None = None,
    token_sha256: str | None = None,
    cwd: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> AppServerLaunchSpec:
    binary = str(codex_bin)
    if not binary or "\x00" in binary:
        raise PolicyViolation("invalid_codex_binary", "Codex binary path is invalid.")
    try:
        transport_value = transport if isinstance(transport, Transport) else Transport(str(transport))
    except ValueError as exc:
        raise PolicyViolation("invalid_transport", "Only stdio or loopback websocket is allowed.") from exc

    args = [
        binary,
        "app-server",
        "--strict-config",
        "--config",
        'sandbox_mode="read-only"',
        "--config",
        'approval_policy="on-request"',
        "--config",
        "features.guardian_approval=true",
    ]
    if transport_value is Transport.STDIO:
        if port is not None or token_file is not None or token_sha256 is not None:
            raise PolicyViolation(
                "invalid_stdio_options",
                "stdio transport does not accept network authentication options.",
            )
        endpoint = "stdio://"
        auth_mode = "process_stdio"
        args.extend(["--listen", endpoint])
    else:
        if host != "127.0.0.1":
            raise PolicyViolation(
                "public_bind_denied",
                "App Server may listen only on 127.0.0.1.",
            )
        if not isinstance(port, int) or not 1024 <= port <= 65535:
            raise PolicyViolation("invalid_port", "Loopback App Server port is invalid.")
        if token_file is None:
            raise PolicyViolation(
                "authentication_required",
                "Loopback websocket requires a capability-token file.",
            )
        token_path = Path(token_file)
        if not token_path.is_absolute() or token_path == Path(token_path.anchor):
            raise PolicyViolation("invalid_token_file", "Capability-token path is invalid.")
        if token_sha256 is None or not SHA256_RE.fullmatch(token_sha256):
            raise PolicyViolation(
                "invalid_token_digest",
                "Capability-token SHA-256 is required.",
            )
        endpoint = f"ws://127.0.0.1:{port}"
        auth_mode = "capability-token"
        args.extend(
            [
                "--listen",
                endpoint,
                "--ws-auth",
                "capability-token",
                "--ws-token-file",
                str(token_path.resolve(strict=False)),
                "--ws-token-sha256",
                token_sha256.lower(),
            ]
        )

    normalized_cwd = _normalize_workspace_root(str(cwd)) if cwd is not None else None
    return AppServerLaunchSpec(
        argv=tuple(args),
        transport=transport_value,
        endpoint=endpoint,
        auth_mode=auth_mode,
        environment=sanitized_environment(environment),
        cwd=normalized_cwd,
    )


@dataclass(frozen=True)
class ProbeResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


ProbeRunner = Callable[[tuple[str, ...], int], ProbeResult | subprocess.CompletedProcess[str] | Mapping[str, Any]]


def _default_probe_runner(command: tuple[str, ...], timeout: int) -> ProbeResult:
    completed = subprocess.run(
        list(command),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        timeout=timeout,
        env={**os.environ, **sanitized_environment()},
        check=False,
    )
    return ProbeResult(completed.returncode, completed.stdout or "", completed.stderr or "")


def _coerce_probe_result(value: Any) -> ProbeResult:
    if isinstance(value, ProbeResult):
        return value
    if isinstance(value, subprocess.CompletedProcess):
        return ProbeResult(value.returncode, value.stdout or "", value.stderr or "")
    if isinstance(value, Mapping):
        return ProbeResult(
            int(value.get("returncode", value.get("exitCode", 1))),
            str(value.get("stdout") or ""),
            str(value.get("stderr") or ""),
        )
    raise GatewayError("invalid_probe", "Codex probe returned an invalid result.")


def parse_feature_listing(text: str) -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {}
    for line in str(text or "").splitlines()[:1000]:
        match = re.match(
            r"^([a-z][a-z0-9_]*)\s+(stable|experimental|under development|deprecated|removed)\s+(true|false)\s*$",
            line.strip(),
        )
        if not match:
            continue
        name, stage, enabled = match.groups()
        if SAFE_FEATURE_RE.fullmatch(name):
            features[name] = {"stage": stage, "enabled": enabled == "true"}
    return features


@dataclass(frozen=True)
class RuntimeDiscovery:
    ok: bool
    status: str
    version: str | None
    app_server_supported: bool
    stdio_supported: bool
    loopback_ws_supported: bool
    capability_token_auth_supported: bool
    features: Mapping[str, Mapping[str, Any]]
    tool_capabilities: Mapping[str, bool]
    models: tuple[Mapping[str, Any], ...]
    checked_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "version": self.version,
            "appServerSupported": self.app_server_supported,
            "transports": {
                "stdio": self.stdio_supported,
                "loopbackWebsocket": self.loopback_ws_supported,
                "capabilityTokenAuth": self.capability_token_auth_supported,
            },
            # Feature names and values came from the strict parser above, not
            # from an arbitrary server payload.  Preserve truthful names such
            # as ``api_key_model_discovery`` without treating the name itself
            # as authentication material.
            "features": {
                name: {
                    "stage": str(value.get("stage") or "unknown"),
                    "enabled": bool(value.get("enabled", False)),
                }
                for name, value in sorted(self.features.items())
                if SAFE_FEATURE_RE.fullmatch(name)
            },
            "toolCapabilities": dict(sorted(self.tool_capabilities.items())),
            "models": [dict(item) for item in self.models],
            "checkedAt": self.checked_at,
            "secretsRead": False,
        }


def discover_codex_runtime(
    codex_bin: str | os.PathLike[str],
    *,
    probe_runner: ProbeRunner | None = None,
    model_payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    timeout: int = 5,
) -> RuntimeDiscovery:
    """Run only fixed, read-only CLI probes and return a sanitized snapshot."""

    binary = str(codex_bin)
    if not binary or "\x00" in binary:
        raise PolicyViolation("invalid_codex_binary", "Codex binary path is invalid.")
    runner = probe_runner or _default_probe_runner
    timeout = max(1, min(int(timeout), 15))
    commands = (
        (binary, "--version"),
        (binary, "app-server", "--help"),
        (binary, "features", "list"),
    )
    results: list[ProbeResult] = []
    try:
        for command in commands:
            results.append(_coerce_probe_result(runner(command, timeout)))
    except (OSError, subprocess.SubprocessError, GatewayError):
        return RuntimeDiscovery(
            False,
            "unavailable",
            None,
            False,
            False,
            False,
            False,
            {},
            {},
            tuple(),
            utc_now(),
        )

    version_match = SAFE_VERSION_RE.search(results[0].stdout) if results[0].returncode == 0 else None
    version = version_match.group(1) if version_match else None
    help_text = results[1].stdout if results[1].returncode == 0 else ""
    features = parse_feature_listing(results[2].stdout) if results[2].returncode == 0 else {}
    app_server_supported = bool(help_text and "Usage: codex app-server" in help_text)
    stdio_supported = "stdio://" in help_text or "--stdio" in help_text
    loopback_ws_supported = "ws://IP:PORT" in help_text or "--listen" in help_text
    token_auth = "capability-token" in help_text and "--ws-token-file" in help_text

    capability_features = {
        "shell": "shell_tool",
        "browser": "browser_use",
        "computer_use": "computer_use",
        "mcp": "apps",
        "plugins": "plugins",
        "multi_agent": "multi_agent",
    }
    tool_capabilities = {
        capability: bool(features.get(feature, {}).get("enabled", False))
        for capability, feature in capability_features.items()
    }
    tool_capabilities.update(
        {
            "conversation": app_server_supported,
            "history": app_server_supported,
            "model_selection": app_server_supported,
            "workspace_read": app_server_supported,
            "workspace_write": bool(features.get("shell_tool", {}).get("enabled", False)),
            "web_search": bool(features.get("browser_use", {}).get("enabled", False)),
            "external_actions": False,
        }
    )
    models = tuple(project_model_catalog(model_payload or []))
    ready = bool(version and app_server_supported and stdio_supported)
    return RuntimeDiscovery(
        ready,
        "ready" if ready else "incompatible",
        version,
        app_server_supported,
        stdio_supported,
        loopback_ws_supported,
        token_auth,
        features,
        tool_capabilities,
        models,
        utc_now(),
    )


_PROCESS_TRANSITIONS: Mapping[ProcessStatus, frozenset[ProcessStatus]] = {
    ProcessStatus.STOPPED: frozenset({ProcessStatus.STARTING}),
    ProcessStatus.STARTING: frozenset({ProcessStatus.READY, ProcessStatus.FAILED, ProcessStatus.STOPPING}),
    ProcessStatus.READY: frozenset({ProcessStatus.STOPPING, ProcessStatus.FAILED}),
    ProcessStatus.STOPPING: frozenset({ProcessStatus.STOPPED, ProcessStatus.FAILED}),
    ProcessStatus.FAILED: frozenset({ProcessStatus.STARTING, ProcessStatus.STOPPED}),
}


@dataclass(frozen=True)
class GatewayProcessState:
    status: ProcessStatus = ProcessStatus.STOPPED
    pid: int | None = None
    transport: str = "stdio"
    endpoint: str = "stdio://"
    started_at: str | None = None
    updated_at: str = field(default_factory=utc_now)
    failure_code: str | None = None
    failure_message: str | None = None

    def transition(
        self,
        status: ProcessStatus | str,
        *,
        pid: int | None = None,
        failure_code: str | None = None,
        failure_message: str | None = None,
    ) -> "GatewayProcessState":
        target = status if isinstance(status, ProcessStatus) else ProcessStatus(str(status))
        if target not in _PROCESS_TRANSITIONS[self.status]:
            raise GatewayError("invalid_process_transition", "Invalid App Server state transition.")
        return replace(
            self,
            status=target,
            pid=pid if pid is not None else self.pid,
            started_at=utc_now() if target is ProcessStatus.STARTING else self.started_at,
            updated_at=utc_now(),
            failure_code=sanitize_text(failure_code, 100) if failure_code else None,
            failure_message=sanitize_text(failure_message, 1000) if failure_message else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "pid": self.pid,
            "transport": self.transport,
            "endpoint": self.endpoint,
            "startedAt": self.started_at,
            "updatedAt": self.updated_at,
            "failureCode": self.failure_code,
            "failureMessage": self.failure_message,
        }


_SESSION_TRANSITIONS: Mapping[SessionStatus, frozenset[SessionStatus]] = {
    SessionStatus.CREATING: frozenset({SessionStatus.IDLE, SessionStatus.FAILED}),
    SessionStatus.IDLE: frozenset({SessionStatus.RUNNING, SessionStatus.COMPLETED, SessionStatus.FAILED}),
    SessionStatus.RUNNING: frozenset(
        {SessionStatus.IDLE, SessionStatus.WAITING_APPROVAL, SessionStatus.STOPPING, SessionStatus.COMPLETED, SessionStatus.FAILED}
    ),
    SessionStatus.WAITING_APPROVAL: frozenset(
        {SessionStatus.RUNNING, SessionStatus.STOPPING, SessionStatus.FAILED}
    ),
    SessionStatus.STOPPING: frozenset({SessionStatus.IDLE, SessionStatus.COMPLETED, SessionStatus.FAILED}),
    SessionStatus.COMPLETED: frozenset({SessionStatus.RUNNING}),
    SessionStatus.FAILED: frozenset({SessionStatus.RUNNING, SessionStatus.COMPLETED}),
}


@dataclass(frozen=True)
class ThreadSessionState:
    thread_id: str
    agent_id: str
    status: SessionStatus
    policy: ValidatedThreadPolicy
    active_turn_id: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    last_event_sequence: int = 0

    def transition(
        self,
        status: SessionStatus | str,
        *,
        active_turn_id: str | None = None,
        event_sequence: int | None = None,
    ) -> "ThreadSessionState":
        target = status if isinstance(status, SessionStatus) else SessionStatus(str(status))
        if target not in _SESSION_TRANSITIONS[self.status]:
            raise GatewayError("invalid_session_transition", "Invalid thread state transition.")
        if event_sequence is not None and event_sequence <= self.last_event_sequence:
            raise GatewayError("stale_event", "Thread event sequence must increase.")
        return replace(
            self,
            status=target,
            active_turn_id=active_turn_id,
            updated_at=utc_now(),
            last_event_sequence=event_sequence
            if event_sequence is not None
            else self.last_event_sequence,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "threadId": self.thread_id,
            "agentId": self.agent_id,
            "status": self.status.value,
            "activeTurnId": self.active_turn_id,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "lastEventSequence": self.last_event_sequence,
            "policy": self.policy.to_dict(),
        }


def fail_closed_approval_handler(method: str, params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Never rely on the SDK's permissive default approval handler."""

    del params
    if method in {
        "item/commandExecution/requestApproval",
        "item/fileChange/requestApproval",
    }:
        return {"decision": "decline"}
    if method == "item/permissions/requestApproval":
        return {"permissions": {}, "scope": "turn"}
    if method == "mcpServer/elicitation/request":
        return {"action": "decline", "content": None}
    if method == "item/tool/requestUserInput":
        return {"answers": {}}
    if method == "item/tool/call":
        return {
            "success": False,
            "contentItems": [
                {"type": "inputText", "text": "Blocked by HQ approval policy"}
            ],
        }
    # An empty object can accidentally be interpreted as a method's default
    # response by a future SDK schema.  Unknown server requests are protocol
    # violations and must fail the request instead of receiving an ambiguous
    # response.
    raise PolicyViolation(
        "unsupported_server_request",
        "Unknown server-initiated request was denied by HQ policy.",
    )


def _contains_absolute_or_unc_path_text(value: str) -> bool:
    patterns = (
        r"(?i)(?:^|[\s\"'=(:,;])(?:\\\\\?\\)?[A-Z]:[\\/]",
        r"(?:^|[\s\"'=(:,;])(?:\\\\|//)[^\\/\s\"']+[\\/]",
        r"(?i)\bfile://(?:/|localhost/)",
        r"(?:^|[\s\"'=(:,;])/(?![/?])(?:[^\s\"']|\s)+",
    )
    return any(re.search(pattern, value) for pattern in patterns)


def _reviewable_text_exact(
    value: object,
    *,
    maximum_chars: int,
    maximum_bytes: int,
    allow_layout_controls: bool,
) -> str:
    if not isinstance(value, str):
        raise PolicyViolation(
            "invalid_file_change_projection",
            "File-change review text is invalid.",
        )
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise PolicyViolation(
            "file_change_not_fully_reviewable",
            "File-change approval cannot be displayed completely and exactly.",
        ) from exc
    if (
        len(value) > maximum_chars
        or len(encoded) > maximum_bytes
        or sanitize_text(value, maximum_chars) != value
        or _BIDI_OR_ZERO_WIDTH_RE.search(value)
    ):
        raise PolicyViolation(
            "file_change_not_fully_reviewable",
            "File-change approval cannot be displayed completely and exactly.",
        )
    allowed = {9, 10, 13} if allow_layout_controls else set()
    if any(
        (ord(character) < 32 and ord(character) not in allowed)
        or 127 <= ord(character) <= 159
        for character in value
    ):
        raise PolicyViolation(
            "file_change_not_fully_reviewable",
            "File-change approval contains hidden control characters.",
        )
    return value


def _approval_relative_path(value: object) -> str:
    text = _reviewable_text_exact(
        value,
        maximum_chars=MAX_APPROVAL_RELATIVE_PATH_CHARS,
        maximum_bytes=MAX_APPROVAL_RELATIVE_PATH_CHARS * 4,
        allow_layout_controls=False,
    ).replace("\\", "/")
    if (
        not text
        or text.startswith("/")
        or text.endswith("/")
        or re.match(r"(?i)^[A-Z]:", text)
        or ":" in text
    ):
        raise PolicyViolation(
            "invalid_file_change_path",
            "File-change target must be a relative Workspace path.",
        )
    parts = text.split("/")
    if any(
        not part or part in {".", ".."} or len(part) > 255
        for part in parts
    ):
        raise PolicyViolation(
            "invalid_file_change_path",
            "File-change target must be a canonical relative Workspace path.",
        )
    return "/".join(parts)


@dataclass(frozen=True)
class _TrustedFileChangeProjection:
    """Transport-only immutable snapshot of one prior patchUpdated event.

    Instances cannot be supplied by JSON from the app-server.  The exact JSON
    stays in memory only; the durable journal receives only the combined hash.
    """

    thread_id: str
    turn_id: str
    item_id: str
    canonical_json: str
    projection_digest: str


def _trusted_file_change_projection(
    params: Mapping[str, Any] | None,
) -> _TrustedFileChangeProjection:
    raw = dict(params or {})
    identifiers: dict[str, str] = {}
    for name in ("threadId", "turnId", "itemId"):
        value = str(raw.get(name) or "")
        if not SAFE_ID_RE.fullmatch(value):
            raise PolicyViolation(
                "invalid_file_change_projection",
                "File-change notification binding is invalid.",
            )
        identifiers[name] = value
    raw_changes = raw.get("changes")
    if (
        not isinstance(raw_changes, list)
        or not raw_changes
        or len(raw_changes) > MAX_APPROVAL_FILE_CHANGES
    ):
        raise PolicyViolation(
            "invalid_file_change_projection",
            "File-change notification has an invalid change count.",
        )

    total_diff_bytes = 0
    changes: list[dict[str, Any]] = []
    for raw_change in raw_changes:
        if not isinstance(raw_change, Mapping):
            raise PolicyViolation(
                "invalid_file_change_projection",
                "File-change notification contains an invalid change.",
            )
        path = _approval_relative_path(raw_change.get("path"))
        raw_kind = raw_change.get("kind")
        if not isinstance(raw_kind, Mapping):
            raise PolicyViolation(
                "invalid_file_change_projection",
                "File-change notification kind is invalid.",
            )
        kind = str(raw_kind.get("type") or "")
        if kind not in {"add", "delete", "update"}:
            raise PolicyViolation(
                "invalid_file_change_projection",
                "File-change notification kind is unsupported.",
            )
        has_snake_move = "move_path" in raw_kind
        has_camel_move = "movePath" in raw_kind
        if has_snake_move and has_camel_move and raw_kind.get("move_path") != raw_kind.get("movePath"):
            raise PolicyViolation(
                "invalid_file_change_projection",
                "File-change move target is ambiguous.",
            )
        move_value = raw_kind.get("move_path") if has_snake_move else raw_kind.get("movePath")
        move_path = None
        if move_value not in (None, ""):
            if kind != "update":
                raise PolicyViolation(
                    "invalid_file_change_projection",
                    "Only update changes may contain a move target.",
                )
            move_path = _approval_relative_path(move_value)
        diff = _reviewable_text_exact(
            raw_change.get("diff"),
            maximum_chars=MAX_APPROVAL_DIFF_BYTES_PER_FILE,
            maximum_bytes=MAX_APPROVAL_DIFF_BYTES_PER_FILE,
            allow_layout_controls=True,
        )
        diff_bytes = diff.encode("utf-8")
        total_diff_bytes += len(diff_bytes)
        if total_diff_bytes > MAX_APPROVAL_DIFF_BYTES:
            raise PolicyViolation(
                "file_change_not_fully_reviewable",
                "File-change approval exceeds the bounded review size.",
            )
        if contains_potential_secret(diff) or _contains_absolute_or_unc_path_text(diff):
            raise PolicyViolation(
                "file_change_sensitive_content_blocked",
                "File-change review contains unsupported sensitive content.",
            )
        change: dict[str, Any] = {
            "path": path,
            "kind": kind,
            "diff": diff,
            "diffSha256": hashlib.sha256(diff_bytes).hexdigest(),
        }
        if move_path is not None:
            change["movePath"] = move_path
        changes.append(change)

    projection = {
        "threadId": identifiers["threadId"],
        "turnId": identifiers["turnId"],
        "itemId": identifiers["itemId"],
        "changes": changes,
    }
    canonical = json.dumps(
        projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return _TrustedFileChangeProjection(
        thread_id=identifiers["threadId"],
        turn_id=identifiers["turnId"],
        item_id=identifiers["itemId"],
        canonical_json=canonical,
        projection_digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


@dataclass
class _PendingApproval:
    request_id: str
    method: str
    thread_id: str
    turn_id: str
    item_id: str
    request_digest: str
    decision_nonce: str
    public_request: Mapping[str, Any]
    created_at: str
    expires_at: str
    expires_epoch: float
    expires_monotonic: float
    event: threading.Event = field(default_factory=threading.Event)
    completed_event: threading.Event = field(default_factory=threading.Event)
    decision: str | None = None
    idempotency_key: str | None = None
    resolution_reason: str | None = None
    resolved_monotonic: float | None = None


@dataclass
class _ResolvedApproval:
    request_id: str
    thread_id: str
    turn_id: str
    item_id: str
    request_digest: str
    decision_nonce: str
    requested_decision: str
    idempotency_key: str
    completed_event: threading.Event
    resolved_monotonic: float
    outcome_success: bool | None = None
    effective_decision: str | None = None


class ExplicitApprovalBroker:
    """One-shot approval broker for an in-process backend.

    Only ``accept_once`` maps to SDK ``accept``.  There is no session-wide or
    automatic approval.  A timeout always declines the request.
    """

    _SUPPORTED_METHODS = frozenset(
        {
            "item/commandExecution/requestApproval",
            "item/fileChange/requestApproval",
        }
    )

    def __init__(
        self,
        timeout_seconds: float = 60.0,
        *,
        resolution_wait_seconds: float = 5.0,
        on_pending: Callable[[Mapping[str, Any]], Any] | None = None,
        on_resolved: Callable[[Mapping[str, Any], Mapping[str, Any]], Any] | None = None,
        approval_journal: Any | None = None,
    ) -> None:
        self.timeout_seconds = max(1.0, min(float(timeout_seconds), 300.0))
        self.resolution_wait_seconds = max(
            0.05,
            min(float(resolution_wait_seconds), 30.0),
        )
        self._on_pending = on_pending
        self._on_resolved = on_resolved
        self._approval_journal = approval_journal
        self._lock = threading.Lock()
        self._pending: MutableMapping[str, _PendingApproval] = {}
        self._resolved: MutableMapping[str, _ResolvedApproval] = {}
        self._thread_workspace_roots: MutableMapping[str, Path] = {}

    @property
    def durable_replay_enabled(self) -> bool:
        return self._approval_journal is not None

    def bind_thread_workspace(
        self,
        thread_id: str,
        workspace_roots: Sequence[str],
    ) -> None:
        """Bind file-change review to one immutable, real Workspace root."""

        normalized_thread = self._safe_id(thread_id, field_name="threadId")
        if len(workspace_roots) != 1:
            raise PolicyViolation(
                "invalid_workspace_binding",
                "Interactive file approval requires exactly one Workspace root.",
            )
        try:
            root = Path(_normalize_workspace_root(str(workspace_roots[0]))).resolve(strict=True)
        except (OSError, RuntimeError, PolicyViolation) as exc:
            raise PolicyViolation(
                "invalid_workspace_binding",
                "Interactive file approval requires an available Workspace root.",
            ) from exc
        if not root.is_dir() or _is_link_or_reparse(root):
            raise PolicyViolation(
                "invalid_workspace_binding",
                "Interactive file approval requires a regular Workspace directory.",
            )
        with self._lock:
            existing = self._thread_workspace_roots.get(normalized_thread)
            if existing is not None and existing != root:
                raise PolicyViolation(
                    "approval_binding_mismatch",
                    "Thread Workspace binding cannot change during its lifetime.",
                )
            self._thread_workspace_roots[normalized_thread] = root

    def _review_file_change_paths(
        self,
        thread_id: str,
        changes: Sequence[Mapping[str, Any]],
    ) -> None:
        with self._lock:
            root = self._thread_workspace_roots.get(thread_id)
        if root is None:
            raise PolicyViolation(
                "workspace_binding_missing",
                "File-change approval is not bound to a Workspace root.",
            )
        if not root.is_dir() or _is_link_or_reparse(root):
            raise PolicyViolation(
                "workspace_binding_invalid",
                "The bound Workspace root is no longer safe.",
            )
        for change in changes:
            relative_values = [str(change.get("path") or "")]
            if change.get("movePath"):
                relative_values.append(str(change.get("movePath")))
            for relative_value in relative_values:
                relative = _approval_relative_path(relative_value)
                candidate = Path(os.path.abspath(str(root.joinpath(*relative.split("/")))))
                try:
                    candidate.relative_to(root)
                except ValueError as exc:
                    raise PolicyViolation(
                        "file_change_outside_workspace",
                        "File-change target is outside the bound Workspace.",
                    ) from exc
                cursor = root
                for part in relative.split("/"):
                    cursor = cursor / part
                    if os.path.lexists(str(cursor)) and _is_link_or_reparse(cursor):
                        raise PolicyViolation(
                            "linked_file_change_blocked",
                            "File-change targets may not traverse links or reparse points.",
                        )

    @staticmethod
    def _journal_failure(error: Exception) -> PolicyViolation:
        code = str(getattr(error, "code", "") or "")
        allowed = {
            "approval_binding_mismatch",
            "approval_decision_conflict",
            "approval_expired",
            "approval_not_pending",
            "approval_store_full",
            "invalid_approval_decision",
            "invalid_approval_request",
            "store_busy",
            "store_corrupt",
            "store_too_large",
            "unsafe_storage_path",
        }
        safe_code = code if code in allowed else "approval_journal_unavailable"
        return PolicyViolation(
            safe_code,
            "Durable approval state failed closed.",
        )

    def _register_durable_pending(self, pending: _PendingApproval) -> None:
        if self._approval_journal is None:
            return
        try:
            self._approval_journal.register_pending(
                dict(pending.public_request),
                expires_epoch=pending.expires_epoch,
            )
        except Exception as error:
            raise self._journal_failure(error) from error

    def _claim_durable_decision(
        self,
        pending: _PendingApproval,
        *,
        decision: str,
        idempotency_key: str,
    ) -> Mapping[str, Any] | None:
        if self._approval_journal is None:
            return None
        try:
            result = self._approval_journal.claim_decision(
                pending.request_id,
                decision=decision,
                idempotency_key=idempotency_key,
                thread_id=pending.thread_id,
                turn_id=pending.turn_id,
                item_id=pending.item_id,
                payload_hash=pending.request_digest,
                decision_nonce=pending.decision_nonce,
            )
        except Exception as error:
            raise self._journal_failure(error) from error
        if not isinstance(result, Mapping):
            raise PolicyViolation(
                "approval_journal_unavailable",
                "Durable approval state failed closed.",
            )
        return result

    def _claim_durable_replay(
        self,
        request_id: str,
        *,
        decision: str,
        idempotency_key: str,
        thread_id: str,
        turn_id: str,
        item_id: str,
        request_digest: str,
        decision_nonce: str,
    ) -> Mapping[str, Any] | None:
        if self._approval_journal is None:
            return None
        try:
            result = self._approval_journal.claim_decision(
                request_id,
                decision=decision,
                idempotency_key=idempotency_key,
                thread_id=thread_id,
                turn_id=turn_id,
                item_id=item_id,
                payload_hash=request_digest,
                decision_nonce=decision_nonce,
            )
        except Exception as error:
            raise self._journal_failure(error) from error
        if not isinstance(result, Mapping):
            raise PolicyViolation(
                "approval_journal_unavailable",
                "Durable approval state failed closed.",
            )
        return result

    def _commit_durable_resolution(
        self,
        pending: _PendingApproval,
        *,
        requested_decision: str,
        effective_decision: str,
        outcome_success: bool,
        terminal_reason: str,
    ) -> bool:
        if self._approval_journal is None:
            return True
        try:
            result = self._approval_journal.commit_resolution(
                pending.request_id,
                requested_decision=requested_decision,
                effective_decision=effective_decision,
                outcome_success=bool(outcome_success),
                terminal_reason=terminal_reason,
            )
            return isinstance(result, Mapping) and result.get("state") == "committed"
        except Exception:
            return False

    @staticmethod
    def _safe_id(value: object, *, field_name: str) -> str:
        normalized = str(value or "")
        if not SAFE_ID_RE.fullmatch(normalized):
            raise PolicyViolation(
                "invalid_approval_request",
                f"Approval {field_name} is invalid.",
            )
        return normalized

    @staticmethod
    def _canonical_digest(method: str, params: Mapping[str, Any]) -> str:
        # The digest is the immutable binding for the *exact* SDK request.
        # Never derive it from the redacted/truncated browser projection:
        # doing so would let distinct raw requests collide.  The canonical
        # bytes are used only in-memory for hashing and are never persisted.
        def validate_json_shape(value: Any, *, depth: int = 0) -> None:
            if depth > MAX_SANITIZE_DEPTH:
                raise PolicyViolation(
                    "invalid_approval_request",
                    "Approval request exceeds the canonical JSON depth limit.",
                )
            if value is None or isinstance(value, (str, bool, int)):
                return
            if isinstance(value, float):
                if value != value or value in {float("inf"), float("-inf")}:
                    raise PolicyViolation(
                        "invalid_approval_request",
                        "Approval request contains a non-finite number.",
                    )
                return
            if isinstance(value, Mapping):
                for key, item in value.items():
                    if not isinstance(key, str):
                        raise PolicyViolation(
                            "invalid_approval_request",
                            "Approval request contains a non-string JSON key.",
                        )
                    validate_json_shape(item, depth=depth + 1)
                return
            if isinstance(value, (list, tuple)):
                for item in value:
                    validate_json_shape(item, depth=depth + 1)
                return
            raise PolicyViolation(
                "invalid_approval_request",
                "Approval request is not canonical JSON.",
            )

        exact = {"method": method, "params": dict(params)}
        validate_json_shape(exact)
        try:
            encoded = json.dumps(
                exact,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError, RecursionError) as exc:
            raise PolicyViolation(
                "invalid_approval_request",
                "Approval request is not canonical JSON.",
            ) from exc
        if len(encoded) > JSON_MAX_BYTES:
            raise PolicyViolation(
                "approval_request_too_large",
                "Approval request exceeded the safe canonical size limit.",
            )
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _path_label(value: object) -> str | None:
        raw = str(value or "").strip().replace("\\", "/").rstrip("/")
        if not raw:
            return None
        return sanitize_text(raw.rsplit("/", 1)[-1], 160)

    @staticmethod
    def _command_summary(value: str) -> str:
        summary = sanitize_text(value, 2_000)
        # Redacting only the matching token is unsafe for quoted Windows/UNC
        # paths containing spaces: a regex can hide the prefix while leaving
        # the rest of the private path visible.  If any absolute-path prefix is
        # present, publish no part of the command.  The exact raw command stays
        # in-memory and remains bound by requestDigest for the one-shot
        # decision; it is never sent to the browser or persisted by HQ.
        absolute_path_patterns = (
            r"(?i)(?:^|[\s\"'=(:,;])(?:\\\\\?\\)?[A-Z]:[\\/]",
            r"(?:^|[\s\"'=(:,;])(?:\\\\|//)[^\\/\s\"']+[\\/]",
            r"(?i)\bfile://(?:/|localhost/)",
            r"(?:^|[\s\"'=(:,;])/(?![/?])(?:[^\s\"']|\s)+",
        )
        if any(re.search(pattern, summary) for pattern in absolute_path_patterns):
            return "[COMMAND_REDACTED_ABSOLUTE_PATH]"
        return summary

    @staticmethod
    def _blocked_command_reason(value: str) -> str | None:
        """Conservatively reject obvious high-impact shell requests.

        This is defense in depth, not proof that Workspace is safe.  The
        product gate remains disabled until a live sentinel establishes the
        app-server's complete approval semantics.
        """

        checks = (
            # Shells and general-purpose interpreters can hide a second command
            # behind /c, -Command, -c, eval/import, a script file, or an
            # encoded payload.  Parsing every dialect correctly is not a safe
            # approval boundary, so the dormant broker rejects them wholesale.
            (
                "indirect_command",
                r"(?i)(?:^|[\s;&|()\\/])(?:cmd(?:\.exe)?|command\.com|powershell(?:\.exe)?|pwsh(?:\.exe)?|bash|dash|zsh|ksh|sh|wsl(?:\.exe)?|python(?:\d+(?:\.\d+)*)?(?:\.exe)?|py(?:\.exe)?|node(?:\.exe)?|deno(?:\.exe)?|bun(?:\.exe)?|perl(?:\.exe)?|ruby(?:\.exe)?|php(?:\.exe)?|cscript(?:\.exe)?|wscript(?:\.exe)?)(?=$|[\s;&|()])",
            ),
            (
                "shell_metacharacter",
                r"(?:&&|\|\||[;|<>`]|\$\()",
            ),
            (
                "network_command",
                r"(?i)\b(?:curl|wget|ssh|scp|sftp|ftp|tftp|nc|ncat|netcat|telnet|invoke-webrequest|invoke-restmethod|start-bitstransfer|bitsadmin|certutil)\b",
            ),
            (
                "destructive_command",
                r"(?i)\b(?:rm|del|erase|rmdir|remove-item|clear-content|set-content|format|diskpart|shutdown|restart-computer|stop-computer|taskkill|stop-process|reg\s+(?:delete|add)|sc\s+(?:delete|stop)|robocopy|xcopy)\b",
            ),
            (
                "destructive_git",
                r"(?is)\bgit\b[^\r\n;&|]{0,512}\b(?:push|clean|rebase|commit|merge|reset\s+--hard|checkout\s+--|restore|switch)\b",
            ),
            (
                "dynamic_code_execution",
                r"(?i)\b(?:invoke-expression|iex|start-process|os\.(?:remove|unlink|rmdir|removedirs|rename|replace|system)|shutil\.(?:rmtree|move)|subprocess\.|pathlib\.|(?:open|eval|exec)\s*\()",
            ),
            ("credential_access", r"(?i)(?:\$env:|\benv:|\bprintenv\b|\b(?:token|secret|password|private[_-]?key|api[_-]?key)\b)"),
            ("live_trade_command", r"(?i)\b(?:ordersend|order_send|positionopen|trade\.(?:buy|sell)|live[_-]?trade)\b"),
        )
        for reason, pattern in checks:
            if re.search(pattern, value):
                return reason
        return None

    def _prune_resolved_locked(self) -> None:
        now = time.monotonic()
        stale = [
            key
            for key, resolved in self._resolved.items()
            if now - resolved.resolved_monotonic > 600.0
        ]
        for key in stale:
            self._resolved.pop(key, None)
        while len(self._resolved) > 512:
            oldest = next(iter(self._resolved))
            self._resolved.pop(oldest, None)

    def _remember_resolved_locked(
        self,
        pending: _PendingApproval,
        *,
        decision: str,
        idempotency_key: str,
    ) -> _ResolvedApproval:
        existing = self._resolved.get(pending.request_id)
        if existing is not None:
            return existing
        resolved = _ResolvedApproval(
            request_id=pending.request_id,
            thread_id=pending.thread_id,
            turn_id=pending.turn_id,
            item_id=pending.item_id,
            request_digest=pending.request_digest,
            decision_nonce=pending.decision_nonce,
            requested_decision=decision,
            idempotency_key=idempotency_key,
            completed_event=pending.completed_event,
            resolved_monotonic=time.monotonic(),
        )
        self._resolved[pending.request_id] = resolved
        self._prune_resolved_locked()
        return resolved

    @staticmethod
    def _assert_replay_binding(
        resolved: _ResolvedApproval,
        *,
        decision: str,
        idempotency_key: str,
        thread_id: str,
        turn_id: str,
        item_id: str,
        request_digest: str,
        decision_nonce: str,
    ) -> None:
        if (
            resolved.thread_id != thread_id
            or resolved.turn_id != turn_id
            or resolved.item_id != item_id
            or resolved.request_digest != request_digest
            or resolved.decision_nonce != decision_nonce
        ):
            raise PolicyViolation(
                "approval_binding_mismatch",
                "Approval request is not bound to this exact thread and turn.",
            )
        if (
            resolved.requested_decision != decision
            or resolved.idempotency_key != idempotency_key
        ):
            raise PolicyViolation(
                "approval_decision_conflict",
                "Approval request already received a different decision.",
            )

    def _build_pending(
        self,
        method: str,
        params: Mapping[str, Any] | None,
    ) -> _PendingApproval:
        raw = dict(params or {})
        trusted_file_projection = raw.pop(_INTERNAL_FILE_CHANGE_PROJECTION, None)
        thread_id = self._safe_id(raw.get("threadId"), field_name="threadId")
        turn_id = self._safe_id(raw.get("turnId"), field_name="turnId")
        item_id = self._safe_id(raw.get("itemId"), field_name="itemId")
        started_at_ms = raw.get("startedAtMs")
        if (
            not isinstance(started_at_ms, int)
            or isinstance(started_at_ms, bool)
            or started_at_ms < 0
        ):
            raise PolicyViolation(
                "invalid_approval_request",
                "Approval startedAtMs is invalid.",
            )

        action_type = "command" if method.endswith("commandExecution/requestApproval") else "file_change"
        # The SDK reason may contain a target path, patch excerpt, or file
        # content.  Browser/audit projections deliberately use fixed copy;
        # exact raw params are represented only by requestDigest.
        reason = (
            "Codex requests one command execution approval."
            if action_type == "command"
            else "Codex requests one file-change approval."
        )
        command: str | None = None
        cwd_label: str | None = None
        file_changes: list[dict[str, Any]] | None = None
        projection_digest: str | None = None
        if action_type == "command":
            if trusted_file_projection is not None:
                raise PolicyViolation(
                    "invalid_approval_request",
                    "Command approval contained an invalid internal projection.",
                )
            # Permission, network and policy amendments are different grants,
            # not a one-shot command approval.  This broker deliberately has
            # no UI or decision path that can authorize them.
            if str(raw.get("kind") or "command") != "command":
                raise PolicyViolation(
                    "unsupported_approval_request",
                    "Only command execution approvals are supported.",
                )
            escalation_fields = (
                "additionalPermissions",
                "networkApprovalContext",
                "proposedExecpolicyAmendment",
                "proposedNetworkPolicyAmendments",
            )
            if any(
                raw.get(field_name) not in (None, False, "", ())
                and raw.get(field_name) != []
                for field_name in escalation_fields
            ):
                raise PolicyViolation(
                    "approval_escalation_blocked",
                    "Permission and policy escalation requests are blocked.",
                )
            available = raw.get("availableDecisions")
            if available is not None and (
                not isinstance(available, list) or "accept" not in available
            ):
                raise PolicyViolation(
                    "unsupported_approval_request",
                    "The request does not support a one-shot accept decision.",
                )
            raw_command = raw.get("command")
            if not isinstance(raw_command, str) or not raw_command.strip():
                raise PolicyViolation(
                    "unsupported_approval_request",
                    "Command approval is missing a reviewable command summary.",
                )
            command_actions = raw.get("commandActions")
            # Informed consent requires the browser projection to represent the
            # whole executable request.  Never make a truncated, normalized,
            # bidi/control-obscured command or hidden structured action
            # approvable.  The immutable digest alone does not let a human
            # review an unseen suffix.
            try:
                raw_command_bytes = raw_command.encode("utf-8", errors="strict")
            except UnicodeEncodeError as exc:
                raise PolicyViolation(
                    "command_not_fully_reviewable",
                    "Command approval cannot be displayed completely and exactly.",
                ) from exc
            if (
                len(raw_command) > 2_000
                or len(raw_command_bytes) > 2_000
                or sanitize_text(raw_command, 2_000) != raw_command
                or any(
                    ord(character) < 32 or 127 <= ord(character) <= 159
                    for character in raw_command
                )
                or re.search(
                    r"[\u061c\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]",
                    raw_command,
                )
                or command_actions not in (None, [], {})
            ):
                raise PolicyViolation(
                    "command_not_fully_reviewable",
                    "Command approval cannot be displayed completely and exactly.",
                )
            try:
                command_guard = raw_command + "\n" + json.dumps(
                    command_actions,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            except (TypeError, ValueError, RecursionError) as exc:
                raise PolicyViolation(
                    "invalid_approval_request",
                    "Command approval metadata is invalid.",
                ) from exc
            if len(command_guard.encode("utf-8", errors="replace")) > 64_000:
                raise PolicyViolation(
                    "approval_request_too_large",
                    "Command approval metadata exceeded the safe limit.",
                )
            if contains_potential_secret(command_guard):
                raise PolicyViolation(
                    "secret_blocked",
                    "Approval command contains unsupported or sensitive content.",
                )
            blocked_reason = self._blocked_command_reason(command_guard)
            if blocked_reason:
                raise PolicyViolation(
                    "high_risk_approval_blocked",
                    "Approval command is outside the safe Workspace subset.",
                    reason=blocked_reason,
                )
            if self._command_summary(command_guard) == "[COMMAND_REDACTED_ABSOLUTE_PATH]":
                raise PolicyViolation(
                    "absolute_path_command_blocked",
                    "Commands containing absolute or UNC paths cannot be approved.",
                )
            command = self._command_summary(raw_command)
            cwd_label = "Workspace"
        else:
            if raw.get("grantRoot") not in {None, ""}:
                raise PolicyViolation(
                    "approval_escalation_blocked",
                    "Workspace root grants are blocked by the one-shot broker.",
                )
            if not isinstance(trusted_file_projection, _TrustedFileChangeProjection):
                raise PolicyViolation(
                    "unsupported_approval_request",
                    "File-change approval lacks a bounded reviewable target.",
                )
            if (
                trusted_file_projection.thread_id != thread_id
                or trusted_file_projection.turn_id != turn_id
                or trusted_file_projection.item_id != item_id
            ):
                raise PolicyViolation(
                    "approval_binding_mismatch",
                    "File-change review is not bound to this exact item and turn.",
                )
            try:
                projection = json.loads(trusted_file_projection.canonical_json)
            except (TypeError, ValueError) as exc:
                raise PolicyViolation(
                    "invalid_file_change_projection",
                    "File-change review projection is invalid.",
                ) from exc
            if not isinstance(projection, Mapping) or not isinstance(
                projection.get("changes"), list
            ):
                raise PolicyViolation(
                    "invalid_file_change_projection",
                    "File-change review projection is invalid.",
                )
            canonical_projection = json.dumps(
                projection,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            if (
                canonical_projection != trusted_file_projection.canonical_json
                or hashlib.sha256(canonical_projection.encode("utf-8")).hexdigest()
                != trusted_file_projection.projection_digest
            ):
                raise PolicyViolation(
                    "approval_binding_mismatch",
                    "File-change review projection changed before approval.",
                )
            file_changes = [dict(change) for change in projection["changes"]]
            self._review_file_change_paths(thread_id, file_changes)
            projection_digest = trusted_file_projection.projection_digest

        if reason and contains_potential_secret(reason):
            raise PolicyViolation(
                "secret_blocked",
                "Approval reason contains sensitive content.",
            )
        request_id = str(uuid.uuid4())
        sdk_request_digest = self._canonical_digest(method, raw)
        request_digest = sdk_request_digest
        if projection_digest is not None:
            request_digest = hashlib.sha256(
                (
                    "hq-file-approval-v1\x00"
                    + sdk_request_digest
                    + "\x00"
                    + projection_digest
                ).encode("ascii")
            ).hexdigest()
        decision_nonce = uuid.uuid4().hex
        created_epoch = time.time()
        created_at = datetime.fromtimestamp(created_epoch, timezone.utc).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")
        expires_at = datetime.fromtimestamp(
            created_epoch + self.timeout_seconds, timezone.utc
        ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        expires_epoch = created_epoch + self.timeout_seconds
        public_request = {
            "requestId": request_id,
            "requestDigest": request_digest,
            "decisionNonce": decision_nonce,
            "method": method,
            "actionType": action_type,
            "threadId": thread_id,
            "turnId": turn_id,
            "itemId": item_id,
            "createdAt": created_at,
            "expiresAt": expires_at,
            "commandSummary": command,
            "cwdLabel": cwd_label,
            "reason": reason,
        }
        if file_changes is not None:
            public_request["fileChanges"] = file_changes
            public_request["sdkRequestDigest"] = sdk_request_digest
            public_request["reviewDigest"] = projection_digest
        return _PendingApproval(
            request_id=request_id,
            method=method,
            thread_id=thread_id,
            turn_id=turn_id,
            item_id=item_id,
            request_digest=request_digest,
            decision_nonce=decision_nonce,
            public_request=public_request,
            created_at=created_at,
            expires_at=expires_at,
            expires_epoch=expires_epoch,
            expires_monotonic=time.monotonic() + self.timeout_seconds,
        )

    def _notify_resolved(
        self,
        pending: _PendingApproval,
        *,
        decision: str,
        reason: str,
    ) -> bool | None:
        if self._on_resolved is None:
            return True
        outcome = {
            "decision": decision,
            "idempotencyKey": pending.idempotency_key,
            "reason": reason,
            "resolvedAt": utc_now(),
        }
        try:
            result = self._on_resolved(dict(pending.public_request), outcome)
            return result is not False
        except Exception:
            return False

    def handler(self, method: str, params: Mapping[str, Any] | None) -> dict[str, Any]:
        if method not in self._SUPPORTED_METHODS:
            return fail_closed_approval_handler(method, params)
        try:
            pending = self._build_pending(method, params)
            # Crash recovery must know the immutable binding before the
            # request is visible to any UI callback.
            self._register_durable_pending(pending)
        except GatewayError:
            return {"decision": "decline"}
        with self._lock:
            self._pending[pending.request_id] = pending
        if self._on_pending is not None:
            try:
                callback_result = self._on_pending(dict(pending.public_request))
                if callback_result is False:
                    raise RuntimeError("approval_request_not_persisted")
            except Exception:
                with self._lock:
                    self._pending.pop(pending.request_id, None)
                    pending.decision = "decline"
                    pending.idempotency_key = f"system:persistence:{pending.request_id}"
                    pending.resolution_reason = "request_persistence_failed"
                    pending.resolved_monotonic = time.monotonic()
                    try:
                        self._claim_durable_decision(
                            pending,
                            decision="decline",
                            idempotency_key=pending.idempotency_key,
                        )
                    except GatewayError:
                        pass
                    resolved = self._remember_resolved_locked(
                        pending,
                        decision="decline",
                        idempotency_key=pending.idempotency_key,
                    )
                self._notify_resolved(
                    pending,
                    decision="decline",
                    reason="request_persistence_failed",
                )
                self._commit_durable_resolution(
                    pending,
                    requested_decision="decline",
                    effective_decision="decline",
                    outcome_success=False,
                    terminal_reason="request_persistence_failed",
                )
                with self._lock:
                    resolved.effective_decision = "decline"
                    resolved.outcome_success = False
                    resolved.resolved_monotonic = time.monotonic()
                pending.completed_event.set()
                return {"decision": "decline"}
        pending.event.wait(self.timeout_seconds)
        with self._lock:
            if pending.decision is None:
                timeout_key = f"system:timeout:{pending.request_id}"
                try:
                    self._claim_durable_decision(
                        pending,
                        decision="decline",
                        idempotency_key=timeout_key,
                    )
                except GatewayError:
                    # A journal failure can never become permission.  The
                    # SDK receives decline and restart recovery tombstones the
                    # unfinished durable row.
                    pass
                pending.decision = "decline"
                pending.idempotency_key = timeout_key
                pending.resolution_reason = "timeout"
                pending.resolved_monotonic = time.monotonic()
                self._remember_resolved_locked(
                    pending,
                    decision="decline",
                    idempotency_key=pending.idempotency_key,
                )
            self._pending.pop(pending.request_id, None)
            requested_decision = pending.decision
            resolution_reason = pending.resolution_reason
            resolved_monotonic = pending.resolved_monotonic
            resolved = self._remember_resolved_locked(
                pending,
                decision=requested_decision,
                idempotency_key=str(pending.idempotency_key or f"system:unknown:{pending.request_id}"),
            )
        if (
            requested_decision == "accept_once"
            and (
                resolved_monotonic is None
                or resolved_monotonic >= pending.expires_monotonic
            )
        ):
            requested_decision = "decline"
            resolution_reason = "timeout"
        if requested_decision is None:
            requested_decision = "decline"
            resolution_reason = "timeout"
        decision = "accept_once" if requested_decision == "accept_once" else "decline"
        reason = resolution_reason or ("user_approved_once" if decision == "accept_once" else "user_declined")
        persisted = self._notify_resolved(pending, decision=decision, reason=reason)
        effective_decision = decision
        outcome_success = persisted is True
        if decision == "accept_once" and not persisted:
            # A tool must never run if its approval decision cannot be tied to
            # durable HQ evidence.  Best-effort record the forced decline.
            self._notify_resolved(
                pending,
                decision="decline",
                reason="decision_persistence_failed",
            )
            effective_decision = "decline"
            outcome_success = False
            reason = "decision_persistence_failed"
        journal_committed = self._commit_durable_resolution(
            pending,
            requested_decision=decision,
            effective_decision=effective_decision,
            outcome_success=outcome_success,
            terminal_reason=reason,
        )
        if not journal_committed:
            if effective_decision == "accept_once":
                self._notify_resolved(
                    pending,
                    decision="decline",
                    reason="approval_journal_commit_failed",
                )
            effective_decision = "decline"
            outcome_success = False
            self._commit_durable_resolution(
                pending,
                requested_decision=decision,
                effective_decision="decline",
                outcome_success=False,
                terminal_reason="approval_journal_commit_failed",
            )
        with self._lock:
            resolved.effective_decision = effective_decision
            resolved.outcome_success = outcome_success
            resolved.resolved_monotonic = time.monotonic()
        pending.completed_event.set()
        return {
            "decision": "accept"
            if effective_decision == "accept_once" and outcome_success
            else "decline"
        }

    def list_pending(
        self,
        *,
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if thread_id is not None:
            thread_id = self._safe_id(thread_id, field_name="threadId")
        if turn_id is not None:
            turn_id = self._safe_id(turn_id, field_name="turnId")
        with self._lock:
            values = [
                item
                for item in self._pending.values()
                if item.decision is None
                and (thread_id is None or item.thread_id == thread_id)
                and (turn_id is None or item.turn_id == turn_id)
            ]
        values.sort(key=lambda item: (item.created_at, item.request_id))
        return [dict(item.public_request) for item in values]

    def resolve(
        self,
        request_id: str,
        decision: str,
        *,
        idempotency_key: str,
        thread_id: str,
        turn_id: str,
        request_digest: str,
        item_id: str,
        decision_nonce: str,
    ) -> bool | None:
        if decision not in {"accept_once", "decline"}:
            raise PolicyViolation(
                "invalid_approval_decision",
                "Approval decision must be accept_once or decline.",
            )
        if not SAFE_ID_RE.fullmatch(str(request_id or "")):
            raise PolicyViolation("invalid_approval_request", "Approval request ID is invalid.")
        if not SAFE_ID_RE.fullmatch(str(idempotency_key or "")):
            raise PolicyViolation(
                "invalid_approval_request",
                "Approval idempotency key is invalid.",
            )
        thread_id = self._safe_id(thread_id, field_name="threadId")
        turn_id = self._safe_id(turn_id, field_name="turnId")
        item_id = self._safe_id(item_id, field_name="itemId")
        if not SHA256_RE.fullmatch(str(request_digest or "")):
            raise PolicyViolation("invalid_approval_request", "Approval digest is invalid.")
        if not re.fullmatch(r"[a-f0-9]{32}", str(decision_nonce or "")):
            raise PolicyViolation("invalid_approval_request", "Approval nonce is invalid.")
        with self._lock:
            pending = self._pending.get(request_id)
            if pending is None:
                resolved = self._resolved.get(request_id)
                if resolved is None:
                    durable_replay = self._claim_durable_replay(
                        request_id,
                        decision=decision,
                        idempotency_key=idempotency_key,
                        thread_id=thread_id,
                        turn_id=turn_id,
                        item_id=item_id,
                        request_digest=request_digest,
                        decision_nonce=decision_nonce,
                    )
                    if durable_replay is None:
                        return False
                    if durable_replay.get("state") == "decision_recorded":
                        return None
                    if durable_replay.get("state") != "committed":
                        return False
                    return durable_replay.get("outcomeSuccess") is True
                if self._approval_journal is not None:
                    self._claim_durable_replay(
                        request_id,
                        decision=decision,
                        idempotency_key=idempotency_key,
                        thread_id=thread_id,
                        turn_id=turn_id,
                        item_id=item_id,
                        request_digest=request_digest,
                        decision_nonce=decision_nonce,
                    )
                self._assert_replay_binding(
                    resolved,
                    decision=decision,
                    idempotency_key=idempotency_key,
                    thread_id=thread_id,
                    turn_id=turn_id,
                    item_id=item_id,
                    request_digest=request_digest,
                    decision_nonce=decision_nonce,
                )
                completed_event = resolved.completed_event
            else:
                if (
                    pending.thread_id != thread_id
                    or pending.turn_id != turn_id
                    or pending.item_id != item_id
                    or pending.request_digest != request_digest
                    or pending.decision_nonce != decision_nonce
                ):
                    raise PolicyViolation(
                        "approval_binding_mismatch",
                        "Approval request is not bound to this exact thread and turn.",
                    )
                if pending.decision is not None:
                    resolved = self._resolved.get(request_id)
                    if resolved is None:
                        raise PolicyViolation(
                            "approval_decision_conflict",
                            "Approval request already received a decision.",
                        )
                    self._assert_replay_binding(
                        resolved,
                        decision=decision,
                        idempotency_key=idempotency_key,
                        thread_id=thread_id,
                        turn_id=turn_id,
                        item_id=item_id,
                        request_digest=request_digest,
                        decision_nonce=decision_nonce,
                    )
                    self._claim_durable_decision(
                        pending,
                        decision=decision,
                        idempotency_key=idempotency_key,
                    )
                    completed_event = resolved.completed_event
                elif time.monotonic() >= pending.expires_monotonic:
                    timeout_key = f"system:timeout:{pending.request_id}"
                    try:
                        self._claim_durable_decision(
                            pending,
                            decision="decline",
                            idempotency_key=timeout_key,
                        )
                    except GatewayError:
                        pass
                    pending.decision = "decline"
                    pending.idempotency_key = timeout_key
                    pending.resolution_reason = "timeout"
                    pending.resolved_monotonic = time.monotonic()
                    self._remember_resolved_locked(
                        pending,
                        decision="decline",
                        idempotency_key=pending.idempotency_key,
                    )
                    pending.event.set()
                    raise PolicyViolation(
                        "approval_expired",
                        "Approval request has expired.",
                    )
                else:
                    # Persist the single-use claim before waking the SDK
                    # handler.  If this fails, no in-memory decision exists
                    # and no command can receive accept.
                    self._claim_durable_decision(
                        pending,
                        decision=decision,
                        idempotency_key=idempotency_key,
                    )
                    pending.decision = decision
                    pending.idempotency_key = idempotency_key
                    pending.resolution_reason = (
                        "user_approved_once" if decision == "accept_once" else "user_declined"
                    )
                    pending.resolved_monotonic = time.monotonic()
                    resolved = self._remember_resolved_locked(
                        pending,
                        decision=decision,
                        idempotency_key=idempotency_key,
                    )
                    pending.event.set()
                    completed_event = pending.completed_event
        # Resolution is not acknowledged to the caller until the SDK handler
        # has committed its lifecycle callback and produced the protocol
        # response. This also guarantees Stop can unblock the app-server reader
        # before attempting turn/interrupt.
        # Never return False while the SDK handler can still commit accept.
        # A bounded wait protects HTTP worker capacity; None is an explicit
        # non-terminal "resolution_pending" result that clients may replay with
        # the same idempotency key.  Stop wakes the handler by resolving decline
        # before it sends turn/interrupt.
        if not completed_event.wait(timeout=self.resolution_wait_seconds):
            return None
        with self._lock:
            resolved = self._resolved.get(request_id)
            if resolved is None:
                return False
            self._assert_replay_binding(
                resolved,
                decision=decision,
                idempotency_key=idempotency_key,
                thread_id=thread_id,
                turn_id=turn_id,
                item_id=item_id,
                request_digest=request_digest,
                decision_nonce=decision_nonce,
            )
            return resolved.outcome_success is True

    def decline_all(self, *, reason: str = "broker_closed") -> int:
        with self._lock:
            values = [item for item in self._pending.values() if item.decision is None]
            resolved_count = 0
            for pending in values:
                key = f"system:{sanitize_text(reason, 40) or 'broker_closed'}:{pending.request_id}"
                try:
                    self._claim_durable_decision(
                        pending,
                        decision="decline",
                        idempotency_key=key,
                    )
                except GatewayError:
                    # Do not wake a blocked handler when its durable decline
                    # could not be recorded.  Gateway close/quarantine must
                    # terminate the SDK process instead.
                    if self._approval_journal is not None:
                        continue
                pending.decision = "decline"
                pending.idempotency_key = key
                pending.resolution_reason = sanitize_text(reason, 80) or "broker_closed"
                pending.resolved_monotonic = time.monotonic()
                self._remember_resolved_locked(
                    pending,
                    decision="decline",
                    idempotency_key=pending.idempotency_key,
                )
                pending.event.set()
                resolved_count += 1
        return resolved_count

    def wait_for_settlement(self, *, timeout_seconds: float | None = None) -> bool:
        """Wait boundedly for already-woken handlers to commit tombstones."""

        timeout = self.resolution_wait_seconds if timeout_seconds is None else max(
            0.0, min(float(timeout_seconds), 30.0)
        )
        deadline = time.monotonic() + timeout
        with self._lock:
            events = [item.completed_event for item in self._pending.values()]
        for event in events:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not event.wait(remaining):
                return False
        return True


def _sdk_response_model(name: str) -> type[Any]:
    try:
        from openai_codex.generated import v2_all
    except ImportError as exc:
        raise GatewayError(
            "sdk_missing",
            "Pinned openai_codex SDK is not installed in this runtime.",
        ) from exc
    model = getattr(v2_all, name, None)
    if model is None:
        raise GatewayError("sdk_incompatible", "Pinned Codex SDK is incompatible.")
    return model


class _DeferredServerRequestReaderMixin:
    """Bounded JSON-RPC server-request dispatch for the pinned sync SDK.

    ``openai_codex==0.147.0`` calls approval handlers inline on its only
    stdout reader.  While a human decision is pending that reader cannot route
    ``turn/interrupt`` responses, which is a deadlock.  This maintained mixin
    changes only server-initiated *request* dispatch: the sole reader retains
    exclusive stdout ownership, captures the JSON-RPC id, and a bounded daemon
    worker writes exactly one response through the SDK's existing write lock.

    Notifications and client-request responses remain on the reader thread.
    Any handler exception becomes a fixed JSON-RPC error with no private
    details.  Worker capacity is fail-closed rather than queued without bound.
    """

    _MAX_SERVER_REQUEST_WORKERS = 4

    def _ensure_server_request_dispatch_state(self) -> None:
        if getattr(self, "_server_request_slots", None) is not None:
            return
        self._server_request_slots = threading.BoundedSemaphore(
            value=self._MAX_SERVER_REQUEST_WORKERS
        )
        self._server_request_threads_lock = threading.Lock()
        self._server_request_threads: set[threading.Thread] = set()
        self._file_change_patch_lock = threading.Lock()
        self._file_change_patch_cache: dict[
            tuple[str, str, str], tuple[float, _TrustedFileChangeProjection | None]
        ] = {}

    def _prune_file_change_patch_cache_locked(self) -> None:
        now = time.monotonic()
        for key, (expires, _projection) in list(self._file_change_patch_cache.items()):
            if expires <= now:
                self._file_change_patch_cache.pop(key, None)
        while len(self._file_change_patch_cache) > APPROVAL_PATCH_CACHE_MAX_ITEMS:
            self._file_change_patch_cache.pop(next(iter(self._file_change_patch_cache)), None)

    @staticmethod
    def _file_change_binding(params: Mapping[str, Any]) -> tuple[str, str, str] | None:
        values = tuple(str(params.get(name) or "") for name in ("threadId", "turnId", "itemId"))
        if not all(SAFE_ID_RE.fullmatch(value) for value in values):
            return None
        return values  # type: ignore[return-value]

    def _capture_file_change_patch(self, params: object) -> None:
        """Cache only a bounded exact projection; malformed updates poison the key."""

        self._ensure_server_request_dispatch_state()
        raw = dict(params) if isinstance(params, Mapping) else {}
        binding = self._file_change_binding(raw)
        if binding is None:
            return
        try:
            projection: _TrustedFileChangeProjection | None = _trusted_file_change_projection(raw)
        except (GatewayError, TypeError, ValueError, UnicodeError):
            projection = None
        with self._file_change_patch_lock:
            self._file_change_patch_cache.pop(binding, None)
            self._file_change_patch_cache[binding] = (
                time.monotonic() + APPROVAL_PATCH_CACHE_TTL_SECONDS,
                projection,
            )
            self._prune_file_change_patch_cache_locked()

    def _take_file_change_patch(
        self,
        params: Mapping[str, Any],
    ) -> _TrustedFileChangeProjection | None:
        self._ensure_server_request_dispatch_state()
        binding = self._file_change_binding(params)
        if binding is None:
            return None
        with self._file_change_patch_lock:
            self._prune_file_change_patch_cache_locked()
            cached = self._file_change_patch_cache.pop(binding, None)
        if cached is None:
            return None
        expires, projection = cached
        return projection if expires > time.monotonic() else None

    def _server_request_with_projection(self, msg: Mapping[str, Any]) -> dict[str, Any]:
        prepared = dict(msg)
        params_value = prepared.get("params")
        if not isinstance(params_value, Mapping):
            return prepared
        params = dict(params_value)
        # JSON input must never be able to synthesize this transport-only type.
        params.pop(_INTERNAL_FILE_CHANGE_PROJECTION, None)
        if prepared.get("method") == "item/fileChange/requestApproval":
            projection = self._take_file_change_patch(params)
            if projection is not None:
                params[_INTERNAL_FILE_CHANGE_PROJECTION] = projection
        prepared["params"] = params
        return prepared

    def _start_reader_thread(self) -> None:
        """Start one stdout reader; only approval handling leaves that thread."""

        if self._proc is None or self._proc.stdout is None:
            return
        self._ensure_server_request_dispatch_state()
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _dispatch_server_request(self, msg: Mapping[str, Any]) -> None:
        current = threading.current_thread()
        try:
            try:
                response = self._handle_server_request(
                    self._server_request_with_projection(msg)
                )
                payload: dict[str, Any] = {"id": msg.get("id"), "result": response}
            except BaseException:
                # Unknown or malformed server requests never inherit an SDK
                # default.  Do not expose exception text, parameters or paths.
                payload = {
                    "id": msg.get("id"),
                    "error": {
                        "code": -32601,
                        "message": "Server request denied by HQ policy.",
                    },
                }
            try:
                self._write_message(payload)
            except BaseException:
                # Closing/quarantining the process can race a worker response.
                # No response is safer than retrying or synthesizing approval.
                pass
        finally:
            with self._server_request_threads_lock:
                self._server_request_threads.discard(current)
            self._server_request_slots.release()

    def _reader_loop(self) -> None:
        """Route stdout continuously while bounded workers answer requests."""

        try:
            while True:
                msg = self._read_message()
                if "method" in msg and "id" in msg:
                    self._ensure_server_request_dispatch_state()
                    if not self._server_request_slots.acquire(blocking=False):
                        self._write_message(
                            {
                                "id": msg.get("id"),
                                "error": {
                                    "code": -32001,
                                    "message": "Server request capacity unavailable; denied.",
                                },
                            }
                        )
                        continue
                    worker = threading.Thread(
                        target=self._dispatch_server_request,
                        args=(dict(msg),),
                        daemon=True,
                    )
                    with self._server_request_threads_lock:
                        self._server_request_threads.add(worker)
                    try:
                        worker.start()
                    except BaseException:
                        with self._server_request_threads_lock:
                            self._server_request_threads.discard(worker)
                        self._server_request_slots.release()
                        self._write_message(
                            {
                                "id": msg.get("id"),
                                "error": {
                                    "code": -32001,
                                    "message": "Server request worker unavailable; denied.",
                                },
                            }
                        )
                    continue
                if "method" in msg and "id" not in msg:
                    method = msg["method"]
                    if isinstance(method, str):
                        if method == "item/fileChange/patchUpdated":
                            self._capture_file_change_patch(msg.get("params"))
                        self._router.route_notification(
                            self._coerce_notification(method, msg.get("params"))
                        )
                    continue
                self._router.route_response(msg)
        except BaseException as exc:
            self._router.fail_all(exc)


def _deferred_client_class(base: type[Any]) -> type[Any]:
    """Create the narrow pinned-SDK adapter without importing SDK at module load."""

    return type(
        "HQDeferredServerRequestCodexClient",
        (_DeferredServerRequestReaderMixin, base),
        {"__module__": __name__},
    )


def _default_client_factory(
    *,
    approval_handler: Callable[[str, Mapping[str, Any] | None], Mapping[str, Any]],
    codex_bin: str | None,
    cwd: str | None,
    environment: Mapping[str, str],
    deferred_server_requests_supported: bool = False,
) -> Any:
    try:
        from openai_codex import CodexConfig
        from openai_codex.client import CodexClient
    except ImportError as exc:
        raise GatewayError(
            "sdk_missing",
            "Pinned openai_codex SDK is not installed in this runtime.",
        ) from exc
    config = CodexConfig(
        codex_bin=codex_bin,
        cwd=cwd,
        env=dict(environment),
        client_name="metafx_hq_full_agent_gateway",
        client_title="Metafxclub AI Agent HQ Full Agent Gateway",
        experimental_api=True,
    )
    # Passing approval_handler is non-optional.  CodexClient's default accepts
    # command and file approvals and must never be used by this product.
    client_class = (
        _deferred_client_class(CodexClient)
        if deferred_server_requests_supported
        else CodexClient
    )
    return client_class(config, approval_handler=approval_handler)


ClientFactory = Callable[..., Any]


class CodexAppServerGateway:
    """Long-lived, policy-checked facade over ``openai_codex.CodexClient``."""

    def __init__(
        self,
        *,
        codex_bin: str | None = None,
        cwd: str | None = None,
        client_factory: ClientFactory | None = None,
        approval_handler: Callable[[str, Mapping[str, Any] | None], Mapping[str, Any]] | None = None,
        approval_broker: ExplicitApprovalBroker | None = None,
        model_catalog: Sequence[Mapping[str, Any]] | None = None,
        runtime_capabilities: Iterable[str] | None = None,
        environment: Mapping[str, str] | None = None,
        attachment_roots: Sequence[str | os.PathLike[str]] | None = None,
        deferred_server_requests_supported: bool = False,
    ) -> None:
        if approval_handler is not None and approval_broker is not None:
            raise PolicyViolation(
                "invalid_approval_configuration",
                "Configure either approval_handler or approval_broker, not both.",
            )
        self.codex_bin = codex_bin
        self.cwd = _normalize_workspace_root(cwd) if cwd else None
        self._client_factory = client_factory or _default_client_factory
        self._approval_broker = approval_broker
        # openai-codex 0.147.0 invokes approval callbacks inline on its sole
        # reader thread and exposes no public deferred-response handle.  A
        # blocking broker wired to that client deadlocks turn/interrupt RPCs.
        # Interactive approval is available only when the caller explicitly
        # enables the maintained deferred reader adapter and durable replay
        # state is present.  With the flag off, even a broker object cannot
        # replace the immediate fail-closed handler.
        self._deferred_server_requests_supported = bool(
            deferred_server_requests_supported
        )
        self._interactive_approval_ready = bool(
            approval_broker is not None
            and approval_broker.durable_replay_enabled
            and self._deferred_server_requests_supported
        )
        self._approval_handler = (
            approval_broker.handler
            if self._interactive_approval_ready
            else approval_handler or fail_closed_approval_handler
        )
        self._model_catalog = list(model_catalog or [])
        self._runtime_capabilities = frozenset(runtime_capabilities) if runtime_capabilities is not None else None
        self._environment = sanitized_environment(environment)
        self._attachment_roots = _normalize_attachment_roots(attachment_roots)
        self._client: Any = None
        self._initialized: dict[str, Any] | None = None
        self._lock = threading.RLock()
        self._session_lock = threading.RLock()
        self._artifact_lock = threading.RLock()
        self._artifact_registry: dict[str, dict[str, Any]] = {}
        self._artifact_path_refs: dict[tuple[str, str, int], str] = {}
        self.sessions: dict[str, ThreadSessionState] = {}
        self.process_state = GatewayProcessState()

    def _create_client(self) -> Any:
        # The keyword is intentionally explicit and covered by regression
        # tests.  A factory that ignores it is outside this module's trust
        # boundary; the production factory passes it to CodexClient.
        return self._client_factory(
            approval_handler=self._approval_handler,
            codex_bin=self.codex_bin,
            cwd=self.cwd,
            environment=self._environment,
            deferred_server_requests_supported=self._interactive_approval_ready,
        )

    def _ensure_client(self) -> Any:
        with self._lock:
            if self._client is not None:
                return self._client
            self.process_state = self.process_state.transition(ProcessStatus.STARTING)
            client: Any = None
            try:
                client = self._create_client()
                client.start()
                initialized = client.initialize()
                self._client = client
                self._initialized = sanitize_value(_plain(initialized), max_string=1000)
                self.process_state = self.process_state.transition(ProcessStatus.READY)
                return client
            except Exception as exc:
                if isinstance(exc, GatewayError):
                    safe_message = exc.message
                    code = exc.code
                else:
                    safe_message = sanitize_text(str(exc), 1000)
                    code = "app_server_start_failed"
                if client is not None:
                    try:
                        client.close()
                    except Exception:
                        pass
                self.process_state = self.process_state.transition(
                    ProcessStatus.FAILED,
                    failure_code=code,
                    failure_message=safe_message,
                )
                raise GatewayError(code, safe_message) from exc

    def close(self) -> None:
        if self._approval_broker is not None:
            self._approval_broker.decline_all(reason="gateway_closed")
            self._approval_broker.wait_for_settlement()
        with self._lock:
            if self._client is None:
                return
            if self.process_state.status is ProcessStatus.READY:
                self.process_state = self.process_state.transition(ProcessStatus.STOPPING)
            try:
                self._client.close()
            finally:
                self._client = None
                self._initialized = None
                if self.process_state.status is ProcessStatus.STOPPING:
                    self.process_state = self.process_state.transition(ProcessStatus.STOPPED)

    @staticmethod
    def _artifact_bytes(path: Path) -> tuple[int, str, bytes]:
        digest = hashlib.sha256()
        total = 0
        head = b""
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                if not head:
                    head = chunk[:32]
                total += len(chunk)
                if total > MAX_ARTIFACT_BYTES:
                    raise PolicyViolation(
                        "artifact_too_large",
                        "Artifact exceeded the safe size limit.",
                    )
                digest.update(chunk)
        if total <= 0:
            raise PolicyViolation("invalid_artifact", "Artifact is empty.")
        return total, digest.hexdigest(), head

    @staticmethod
    def _artifact_type_matches(suffix: str, media_type: str, head: bytes) -> bool:
        if media_type in SAFE_IMAGE_MEDIA_TYPES:
            if media_type == "image/png":
                return head.startswith(b"\x89PNG\r\n\x1a\n")
            if media_type == "image/jpeg":
                return head.startswith(b"\xff\xd8\xff")
            return len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP"
        if suffix == ".gif":
            return head.startswith((b"GIF87a", b"GIF89a"))
        if suffix == ".pdf":
            return head.startswith(b"%PDF-")
        if suffix in {".docx", ".pptx", ".xlsx", ".zip"}:
            return head.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
        if suffix == ".mp3":
            return head.startswith(b"ID3") or (
                len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0
            )
        if suffix == ".mp4":
            return len(head) >= 12 and head[4:8] == b"ftyp"
        # Text/code formats must not masquerade as binary payloads.  Metadata
        # projection never includes these bytes; this is only a type check.
        return b"\x00" not in head

    def _project_artifact(self, path_value: object, kind: str) -> dict[str, Any] | None:
        try:
            path = _managed_file_path(
                path_value,
                self._attachment_roots,
                unavailable_code="invalid_artifact",
            )
            suffix = path.suffix.lower()
            media_type = SAFE_ARTIFACT_MEDIA_TYPES.get(suffix)
            if media_type is None:
                return None
            byte_size, digest, head = self._artifact_bytes(path)
            if not self._artifact_type_matches(suffix, media_type, head):
                return None
            raw_name = sanitize_text(path.name, 240)
            basename = f"artifact{suffix}" if is_sensitive_key(path.stem) else raw_name
            key = (str(path), digest, byte_size)
            with self._artifact_lock:
                artifact_ref = self._artifact_path_refs.get(key)
                if artifact_ref is None:
                    if len(self._artifact_registry) >= MAX_ARTIFACTS:
                        return None
                    artifact_ref = f"artifact-{uuid.uuid4().hex}"
                    self._artifact_path_refs[key] = artifact_ref
                    self._artifact_registry[artifact_ref] = {
                        "path": path,
                        "sha256": digest,
                        "byteSize": byte_size,
                    }
            return {
                "artifactRef": artifact_ref,
                "basename": basename,
                "mediaType": media_type,
                "byteSize": byte_size,
                "sha256": digest,
                "kind": "image" if kind == "image" else "file",
            }
        except (OSError, PolicyViolation):
            return None

    def resolve_artifact(self, artifact_ref: str) -> Path:
        """Resolve an opaque artifact reference for a trusted backend caller.

        This method is intentionally not exposed by ``process_json_request``.
        The caller still owns authorization and response streaming policy.
        """

        if not SAFE_ID_RE.fullmatch(str(artifact_ref or "")):
            raise PolicyViolation("invalid_artifact_ref", "Artifact reference is invalid.")
        with self._artifact_lock:
            entry = self._artifact_registry.get(artifact_ref)
        if not isinstance(entry, Mapping):
            raise GatewayError("artifact_not_found", "Artifact is unavailable.")
        path = _managed_file_path(
            entry.get("path"),
            self._attachment_roots,
            unavailable_code="artifact_not_found",
        )
        try:
            byte_size, digest, _head = self._artifact_bytes(path)
        except (OSError, PolicyViolation) as exc:
            raise GatewayError("artifact_not_found", "Artifact is unavailable.") from exc
        if byte_size != entry.get("byteSize") or digest != entry.get("sha256"):
            raise GatewayError("artifact_stale", "Artifact changed after it was projected.")
        return path

    def __enter__(self) -> "CodexAppServerGateway":
        self._ensure_client()
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        self.close()

    def status(self) -> dict[str, Any]:
        with self._lock:
            client = self._ensure_client()
            authentication = project_account_authentication(client.account_read())
            initialized = dict(self._initialized or {})
            process = self.process_state.to_dict()
        authenticated = authentication["authenticated"] is True
        server_info = initialized.get("serverInfo")
        if not isinstance(server_info, Mapping):
            server_info = {}
        return {
            "ok": authenticated,
            "status": "ready" if authenticated else "auth_required",
            "source": "codex_app_server",
            "process": process,
            "server": {
                "name": sanitize_text(server_info.get("name") or "codex", 120),
                "version": sanitize_text(server_info.get("version") or "", 80),
                "platformFamily": sanitize_text(initialized.get("platformFamily") or "", 80),
                "platformOs": sanitize_text(initialized.get("platformOs") or "", 80),
            },
            "authentication": authentication,
            "approvalHandler": (
                "explicit_one_shot"
                if self._interactive_approval_ready
                else "explicit_fail_closed"
            ),
            "approvalBrokerReady": self._interactive_approval_ready,
            "approvalReplayDurable": bool(
                self._approval_broker is not None
                and self._approval_broker.durable_replay_enabled
            ),
            "deferredServerRequestsSupported": self._interactive_approval_ready,
            "automaticExternalEffects": False,
            "secretsRead": False,
            "attachments": {
                "configured": bool(self._attachment_roots),
                "inputTypes": ["text", "image"]
                + (["localImage"] if self._attachment_roots else []),
                "maxImagesPerTurn": MAX_TURN_INPUT_IMAGES,
                "maxLocalImageBytes": MAX_LOCAL_IMAGE_BYTES,
                "maxInlineImageBytes": MAX_INLINE_IMAGE_BYTES,
                "artifactProjection": bool(self._attachment_roots),
            },
        }

    def approval_list(
        self,
        *,
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> dict[str, Any]:
        if not self._interactive_approval_ready:
            raise PolicyViolation(
                "approval_broker_required",
                "Interactive approval broker is not configured.",
            )
        approvals = self._approval_broker.list_pending(
            thread_id=thread_id,
            turn_id=turn_id,
        )
        return {
            "ok": True,
            "status": "waiting_approval" if approvals else "ready",
            "approvals": approvals,
        }

    def approval_resolve(
        self,
        request_id: str,
        decision: str,
        *,
        idempotency_key: str,
        thread_id: str,
        turn_id: str,
        item_id: str,
        request_digest: str,
        decision_nonce: str,
    ) -> dict[str, Any]:
        if not self._interactive_approval_ready:
            raise PolicyViolation(
                "approval_broker_required",
                "Interactive approval broker is not configured.",
            )
        resolved = self._approval_broker.resolve(
            request_id,
            decision,
            idempotency_key=idempotency_key,
            thread_id=thread_id,
            turn_id=turn_id,
            item_id=item_id,
            request_digest=request_digest,
            decision_nonce=decision_nonce,
        )
        return {
            "ok": resolved is not False,
            "status": (
                "resolution_accepted"
                if resolved is True
                else "resolution_pending"
                if resolved is None
                else "approval_not_pending"
            ),
            "committed": resolved is True,
            "requestId": request_id,
        }

    def models(self) -> dict[str, Any]:
        response = self._ensure_client().model_list(include_hidden=False)
        models = project_model_catalog(response)
        self._model_catalog = models
        return {"ok": True, "status": "ready", "models": models}

    def mcp_status(self, *, thread_id: str | None = None) -> dict[str, Any]:
        if thread_id is not None and not SAFE_ID_RE.fullmatch(thread_id):
            raise PolicyViolation("invalid_thread", "Thread ID is invalid.")
        params: dict[str, Any] = {"limit": 100, "detail": "toolsAndAuthOnly"}
        if thread_id:
            params["threadId"] = thread_id
        response = self._ensure_client().request(
            "mcpServerStatus/list",
            params,
            response_model=_sdk_response_model("ListMcpServerStatusResponse"),
        )
        servers = project_mcp_status(response)
        return {
            "ok": True,
            "status": "ready" if servers else "not_configured",
            "servers": servers,
        }

    def plugins(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "forceRefetch": False,
            "marketplaceKinds": ["local", "workspace-directory"],
        }
        if self.cwd:
            params["cwds"] = [self.cwd]
        response = self._ensure_client().request(
            "plugin/list",
            params,
            response_model=_sdk_response_model("PluginListResponse"),
        )
        plugins = project_plugin_catalog(response)
        return {
            "ok": True,
            "status": "ready" if plugins else "not_configured",
            "plugins": plugins,
        }

    def _validate_policy(self, value: ThreadPolicyRequest | Mapping[str, Any]) -> ValidatedThreadPolicy:
        if not self._model_catalog:
            # Model selection is never trusted solely from frontend input.
            # The read-only catalog call does not create a turn or consume a
            # model request.
            try:
                self.models()
            except Exception as exc:
                raise GatewayError(
                    "model_catalog_unavailable",
                    "Codex model catalog is unavailable; no thread was created.",
                ) from exc
        if not self._model_catalog:
            # An empty or wholly malformed catalog cannot prove that the
            # requested model exists. Keep the direct Gateway API fail-closed
            # even when callers bypass the Local Bridge preflight.
            raise PolicyViolation(
                "model_catalog_unavailable",
                "Codex model catalog is empty; no thread was created.",
            )
        return validate_thread_policy(
            value,
            model_catalog=self._model_catalog,
            runtime_capabilities=self._runtime_capabilities,
        )

    def thread_start(self, policy_value: ThreadPolicyRequest | Mapping[str, Any]) -> dict[str, Any]:
        policy = self._validate_policy(policy_value)
        params = {
            "approvalPolicy": policy.approval_policy,
            "cwd": policy.cwd,
            "ephemeral": False,
            "model": policy.model,
            "sandbox": policy.sandbox,
            "serviceName": "metafx_hq_full_agent",
            "config": policy.thread_config(),
            "developerInstructions": (
                "Metafx HQ capability policy is authoritative. Never perform an external "
                "side effect without a fresh user approval routed by the HQ gateway."
            ),
        }
        response = self._ensure_client().thread_start(params)
        plain = _plain(response)
        thread = project_thread(
            plain.get("thread") or {},
            include_turns=True,
            artifact_projector=self._project_artifact,
        )
        thread_id = str(thread.get("id") or "")
        if not SAFE_ID_RE.fullmatch(thread_id):
            raise GatewayError("invalid_thread_response", "Codex returned an invalid thread ID.")
        if (
            self._interactive_approval_ready
            and self._approval_broker is not None
            and policy.mode is AgentMode.WORKSPACE
            and policy.approval_mode is ApprovalMode.EXPLICIT
        ):
            self._approval_broker.bind_thread_workspace(
                thread_id,
                policy.workspace_roots,
            )
        with self._session_lock:
            self.sessions[thread_id] = ThreadSessionState(
                thread_id=thread_id,
                agent_id=policy.agent_id,
                status=SessionStatus.IDLE,
                policy=policy,
            )
        return {"ok": True, "status": "created", "thread": thread, "policy": policy.to_dict()}

    def thread_resume(
        self,
        thread_id: str,
        policy_value: ThreadPolicyRequest | Mapping[str, Any],
    ) -> dict[str, Any]:
        if not SAFE_ID_RE.fullmatch(thread_id):
            raise PolicyViolation("invalid_thread", "Thread ID is invalid.")
        policy = self._validate_policy(policy_value)
        params = {
            "approvalPolicy": policy.approval_policy,
            "cwd": policy.cwd,
            "model": policy.model,
            "sandbox": policy.sandbox,
            "config": policy.thread_config(),
            "developerInstructions": (
                "Metafx HQ capability policy is authoritative. Never perform an external "
                "side effect without a fresh user approval routed by the HQ gateway."
            ),
        }
        with self._session_lock:
            existing = self.sessions.get(thread_id)
            if existing is not None and existing.status in {
                SessionStatus.RUNNING,
                SessionStatus.WAITING_APPROVAL,
                SessionStatus.STOPPING,
            }:
                raise GatewayError("thread_busy", "Thread already has an active turn.")
            if existing is not None and existing.agent_id != policy.agent_id:
                raise PolicyViolation(
                    "thread_owner_mismatch",
                    "Thread belongs to a different Agent.",
                )
            # Hold the session lock across the resume RPC so a concurrent
            # turn_start cannot pass its idle check and then be overwritten by
            # the resumed IDLE state.
            response = self._ensure_client().thread_resume(thread_id, params)
            plain = _plain(response)
            thread = project_thread(
                plain.get("thread") or {},
                include_turns=True,
                artifact_projector=self._project_artifact,
            )
            if (
                self._interactive_approval_ready
                and self._approval_broker is not None
                and policy.mode is AgentMode.WORKSPACE
                and policy.approval_mode is ApprovalMode.EXPLICIT
            ):
                self._approval_broker.bind_thread_workspace(
                    thread_id,
                    policy.workspace_roots,
                )
            self.sessions[thread_id] = ThreadSessionState(
                thread_id=thread_id,
                agent_id=policy.agent_id,
                status=SessionStatus.IDLE,
                policy=policy,
            )
        return {"ok": True, "status": "resumed", "thread": thread, "policy": policy.to_dict()}

    def thread_read(self, thread_id: str, *, include_turns: bool = True) -> dict[str, Any]:
        if not SAFE_ID_RE.fullmatch(thread_id):
            raise PolicyViolation("invalid_thread", "Thread ID is invalid.")
        response = self._ensure_client().thread_read(thread_id, include_turns=include_turns)
        plain = _plain(response)
        return {
            "ok": True,
            "status": "ready",
            "thread": project_thread(
                plain.get("thread") or {},
                include_turns=include_turns,
                artifact_projector=self._project_artifact,
            ),
        }

    def thread_list(
        self,
        *,
        limit: int = 20,
        cursor: str | None = None,
        archived: bool = False,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit), 100))
        if cursor is not None and (not cursor or len(cursor) > 1000 or contains_potential_secret(cursor)):
            raise PolicyViolation("invalid_cursor", "Thread cursor is invalid.")
        params: dict[str, Any] = {
            "limit": limit,
            "archived": bool(archived),
            "sortKey": "updated_at",
            "sortDirection": "desc",
            "useStateDbOnly": True,
        }
        if cursor:
            params["cursor"] = cursor
        if self.cwd:
            params["cwd"] = [self.cwd]
        response = self._ensure_client().thread_list(params)
        plain = _plain(response)
        data = plain.get("data")
        threads = [
            project_thread(
                thread,
                include_turns=False,
                artifact_projector=self._project_artifact,
            )
            for thread in (data[:limit] if isinstance(data, list) else [])
        ]
        return {
            "ok": True,
            "status": "ready",
            "threads": threads,
            "nextCursor": sanitize_text(plain.get("nextCursor") or "", 1000) or None,
        }

    def _session_policy(
        self,
        thread_id: str,
        policy_value: ThreadPolicyRequest | Mapping[str, Any] | None,
    ) -> ValidatedThreadPolicy:
        with self._session_lock:
            if policy_value is not None:
                policy = self._validate_policy(policy_value)
                existing = self.sessions.get(thread_id)
                if existing is not None and existing.agent_id != policy.agent_id:
                    raise PolicyViolation(
                        "thread_owner_mismatch",
                        "Thread belongs to a different Agent.",
                    )
                return policy
            existing = self.sessions.get(thread_id)
            if existing is None:
                raise PolicyViolation(
                    "thread_policy_required",
                    "A validated policy is required for this thread.",
                )
            return existing.policy

    def _model_supports_image_input(self, model: str) -> bool:
        for entry in self._model_catalog:
            if str(entry.get("model") or entry.get("id") or "") != model:
                continue
            modalities = entry.get("inputModalities")
            return isinstance(modalities, list) and "image" in modalities
        return False

    def turn_start(
        self,
        thread_id: str,
        prompt: str,
        *,
        input_items: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        policy_value: ThreadPolicyRequest | Mapping[str, Any] | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        if not SAFE_ID_RE.fullmatch(thread_id):
            raise PolicyViolation("invalid_thread", "Thread ID is invalid.")
        sdk_input, image_count = validate_turn_input(
            prompt,
            input_items,
            attachment_roots=self._attachment_roots,
        )
        policy = self._session_policy(thread_id, policy_value)
        if image_count and not self._model_supports_image_input(policy.model):
            raise PolicyViolation(
                "unsupported_model_modality",
                "Selected model does not advertise image input support.",
            )
        if policy.approval_mode is ApprovalMode.EXPLICIT and not self._interactive_approval_ready:
            raise PolicyViolation(
                "approval_broker_required",
                "Explicit approval mode requires an interactive approval broker.",
            )
        params = {
            "approvalPolicy": policy.approval_policy,
            "cwd": policy.cwd,
            "effort": policy.reasoning_effort,
            "model": policy.model,
            "sandboxPolicy": policy.sandbox_policy(),
        }
        with self._session_lock:
            current = self.sessions.get(thread_id) or ThreadSessionState(
                thread_id=thread_id,
                agent_id=policy.agent_id,
                status=SessionStatus.IDLE,
                policy=policy,
            )
            if current.agent_id != policy.agent_id:
                raise PolicyViolation(
                    "thread_owner_mismatch",
                    "Thread belongs to a different Agent.",
                )
            if current.status not in {SessionStatus.IDLE, SessionStatus.COMPLETED, SessionStatus.FAILED}:
                raise GatewayError("thread_busy", "Thread already has an active turn.")
            # Keep resume and start mutually exclusive through the SDK request;
            # otherwise resume can replace a freshly RUNNING local session.
            response = self._ensure_client().turn_start(thread_id, sdk_input, params)
            plain = _plain(response)
            turn = _project_turn(
                plain.get("turn") or {},
                artifact_projector=self._project_artifact,
            )
            turn_id = str(turn.get("id") or "")
            if not SAFE_ID_RE.fullmatch(turn_id):
                raise GatewayError("invalid_turn_response", "Codex returned an invalid turn ID.")
            self.sessions[thread_id] = current.transition(
                SessionStatus.RUNNING,
                active_turn_id=turn_id,
            )
        output: dict[str, Any] = {
            "ok": True,
            "status": "running",
            "threadId": thread_id,
            "turn": turn,
            "policy": policy.to_dict(),
        }
        if wait:
            completed = self.turn_wait(turn_id, thread_id=thread_id)
            output["status"] = completed["status"]
            output["completed"] = completed
        return output

    def turn_wait(self, turn_id: str, *, thread_id: str | None = None) -> dict[str, Any]:
        if not SAFE_ID_RE.fullmatch(turn_id):
            raise PolicyViolation("invalid_turn", "Turn ID is invalid.")
        if thread_id is not None and not SAFE_ID_RE.fullmatch(thread_id):
            raise PolicyViolation("invalid_thread", "Thread ID is invalid.")
        resolved_thread_id = str(thread_id or "")
        if not resolved_thread_id:
            with self._session_lock:
                matches = [
                    session.thread_id
                    for session in self.sessions.values()
                    if session.active_turn_id == turn_id
                ]
            if len(matches) == 1:
                resolved_thread_id = matches[0]
        if not resolved_thread_id:
            raise PolicyViolation(
                "thread_required_for_wait",
                "Thread ID is required to reconcile a terminal turn safely.",
            )

        # SDK 0.147 drops an unregistered turn/completed notification. Register
        # first, then reconcile authoritative thread state. If the turn was
        # already dropped, thread/read recovers it; if it completes during the
        # read, the registered queue retains the notification for the SDK wait.
        client = self._ensure_client()
        turn: dict[str, Any] = {}
        client.register_turn_notifications(turn_id)
        try:
            # A brand-new persistent Codex thread can briefly have an empty
            # rollout file.  In that window thread/read may fail even though
            # the already-registered completion queue is healthy.  A snapshot
            # read is only a recovery optimization, so its failure must fall
            # through to the authoritative terminal notification rather than
            # falsely failing an otherwise healthy turn.
            try:
                response = client.thread_read(resolved_thread_id, include_turns=True)
                plain = _plain(response)
                raw_thread = plain.get("thread")
                raw_turns = raw_thread.get("turns") if isinstance(raw_thread, Mapping) else None
            except Exception:
                raw_turns = None
            if isinstance(raw_turns, list):
                for raw_turn in reversed(raw_turns):
                    if hasattr(raw_turn, "model_dump"):
                        raw_turn = raw_turn.model_dump(by_alias=True, mode="json")
                    if not isinstance(raw_turn, Mapping):
                        continue
                    if str(raw_turn.get("id") or "") != turn_id:
                        continue
                    projected = _project_turn(
                        raw_turn,
                        artifact_projector=self._project_artifact,
                    )
                    if str(projected.get("status") or "") in TERMINAL_TURN_STATUSES:
                        turn = projected
                    break
            if not turn:
                response = client.wait_for_turn_completed(turn_id)
                plain = _plain(response)
                response_thread_id = str(plain.get("threadId") or "")
                if response_thread_id and response_thread_id != resolved_thread_id:
                    raise GatewayError(
                        "turn_thread_mismatch",
                        "Codex completed the turn on an unexpected thread.",
                    )
                turn = _project_turn(
                    plain.get("turn") or {},
                    artifact_projector=self._project_artifact,
                )
        finally:
            # wait_for_turn_completed also unregisters in SDK 0.147. The
            # router treats a second unregister as a safe no-op.
            client.unregister_turn_notifications(turn_id)

        status = str(turn.get("status") or "")
        if status not in TERMINAL_TURN_STATUSES:
            raise GatewayError(
                "invalid_turn_response",
                "Codex did not return a terminal turn state.",
            )
        with self._session_lock:
            current = self.sessions.get(resolved_thread_id)
            target = SessionStatus.FAILED if status == "failed" else SessionStatus.IDLE
            # A late waiter from an older turn must never clear a newer active
            # turn on the same Codex thread.
            if (
                current is not None
                and current.active_turn_id == turn_id
                and current.status in {SessionStatus.RUNNING, SessionStatus.STOPPING}
            ):
                self.sessions[resolved_thread_id] = current.transition(target, active_turn_id=None)
        return {
            "ok": status == "completed",
            "status": status,
            "threadId": resolved_thread_id or None,
            "turn": turn,
        }

    def turn_interrupt(self, thread_id: str, turn_id: str) -> dict[str, Any]:
        if not SAFE_ID_RE.fullmatch(thread_id) or not SAFE_ID_RE.fullmatch(turn_id):
            raise PolicyViolation("invalid_turn", "Thread or turn ID is invalid.")
        with self._session_lock:
            current = self.sessions.get(thread_id)
            if (
                current is not None
                and current.active_turn_id is not None
                and current.active_turn_id != turn_id
            ):
                raise GatewayError("turn_mismatch", "Turn is not active on this thread.")
            if current is not None and current.status in {
                SessionStatus.RUNNING,
                SessionStatus.WAITING_APPROVAL,
            }:
                self.sessions[thread_id] = current.transition(
                    SessionStatus.STOPPING,
                    active_turn_id=turn_id,
                )
        response = self._ensure_client().turn_interrupt(thread_id, turn_id)
        return {
            "ok": True,
            "status": "interrupt_requested",
            "threadId": thread_id,
            "turnId": turn_id,
            "result": sanitize_value(_plain(response), max_string=1000),
        }


def process_json_request(
    request: Mapping[str, Any],
    gateway: CodexAppServerGateway,
) -> dict[str, Any]:
    operation = str(request.get("operation") or "")
    if operation == "status":
        return gateway.status()
    if operation == "models":
        return gateway.models()
    if operation == "mcp":
        thread_id = request.get("threadId")
        return gateway.mcp_status(thread_id=str(thread_id) if thread_id else None)
    if operation == "plugins":
        return gateway.plugins()
    if operation == "approval_pending":
        return gateway.approval_list(
            thread_id=str(request.get("threadId")) if request.get("threadId") else None,
            turn_id=str(request.get("turnId")) if request.get("turnId") else None,
        )
    if operation == "approval_resolve":
        return gateway.approval_resolve(
            str(request.get("requestId") or ""),
            str(request.get("decision") or ""),
            idempotency_key=str(request.get("idempotencyKey") or ""),
            thread_id=str(request.get("threadId") or ""),
            turn_id=str(request.get("turnId") or ""),
            item_id=str(request.get("itemId") or ""),
            request_digest=str(request.get("requestDigest") or ""),
            decision_nonce=str(request.get("decisionNonce") or ""),
        )
    if operation == "thread_start":
        policy = request.get("policy")
        if not isinstance(policy, Mapping):
            raise PolicyViolation("policy_required", "Thread policy is required.")
        return gateway.thread_start(policy)
    if operation == "thread_resume":
        policy = request.get("policy")
        if not isinstance(policy, Mapping):
            raise PolicyViolation("policy_required", "Thread policy is required.")
        return gateway.thread_resume(str(request.get("threadId") or ""), policy)
    if operation == "thread_read":
        return gateway.thread_read(
            str(request.get("threadId") or ""),
            include_turns=bool(request.get("includeTurns", True)),
        )
    if operation == "thread_list":
        return gateway.thread_list(
            limit=int(request.get("limit") or 20),
            cursor=str(request.get("cursor")) if request.get("cursor") else None,
            archived=bool(request.get("archived", False)),
        )
    if operation == "turn_start":
        policy = request.get("policy")
        if policy is not None and not isinstance(policy, Mapping):
            raise PolicyViolation("invalid_policy", "Thread policy is invalid.")
        input_items = request.get("inputItems")
        if input_items is not None and not (
            isinstance(input_items, Mapping)
            or (
                isinstance(input_items, Sequence)
                and not isinstance(input_items, (str, bytes))
            )
        ):
            raise PolicyViolation("invalid_turn_input", "Structured turn input is invalid.")
        return gateway.turn_start(
            str(request.get("threadId") or ""),
            str(request.get("prompt") or ""),
            input_items=input_items,
            policy_value=policy,
            wait=bool(request.get("wait", False)),
        )
    if operation == "turn_wait":
        return gateway.turn_wait(
            str(request.get("turnId") or ""),
            thread_id=str(request.get("threadId")) if request.get("threadId") else None,
        )
    if operation == "turn_interrupt":
        return gateway.turn_interrupt(
            str(request.get("threadId") or ""),
            str(request.get("turnId") or ""),
        )
    raise GatewayError("unsupported_operation", "Gateway operation is unsupported.")


def _read_json_stdin() -> Mapping[str, Any]:
    raw = sys.stdin.buffer.read(JSON_MAX_BYTES + 1)
    if len(raw) > JSON_MAX_BYTES:
        raise GatewayError("request_too_large", "Gateway request exceeded the safe limit.")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GatewayError("invalid_request", "Gateway request must be UTF-8 JSON.") from exc
    if not isinstance(value, Mapping):
        raise GatewayError("invalid_request", "Gateway request must be a JSON object.")
    return value


def _write_json_response(outstream: Any, response: Mapping[str, Any]) -> None:
    """Write one portable JSON response and flush it immediately.

    JSON string escapes are deliberately ASCII-only at this process boundary.
    A JSON decoder reconstructs the original Unicode text exactly, while the
    wire representation remains writable through legacy Windows code pages
    such as cp1252.  This avoids making correctness depend on
    ``PYTHONIOENCODING`` or the console's active code page.
    """

    outstream.write(
        json.dumps(response, ensure_ascii=True, separators=(",", ":")) + "\n"
    )
    outstream.flush()


def serve_json_lines(
    instream: Any,
    outstream: Any,
    gateway: CodexAppServerGateway,
) -> int:
    """Serve multiple requests on one process/client using bounded JSONL.

    This is the CLI form to use for asynchronous ``turn_start``, ``turn_wait``
    and ``turn_interrupt``.  Keeping the SDK client alive is required for turn
    notifications; a new one-shot process must not pretend it owns an active
    turn from a previous process.
    """

    for raw_line in instream:
        if isinstance(raw_line, bytes):
            line_size = len(raw_line)
            raw_text = raw_line.decode("utf-8", errors="replace")
        else:
            raw_text = str(raw_line)
            line_size = len(raw_text.encode("utf-8", errors="replace"))
        if not raw_text.strip():
            continue
        try:
            if line_size > JSON_MAX_BYTES:
                raise GatewayError(
                    "request_too_large",
                    "Gateway request exceeded the safe limit.",
                )
            request = json.loads(raw_text)
            if not isinstance(request, Mapping):
                raise GatewayError(
                    "invalid_request",
                    "Gateway request must be a JSON object.",
                )
            response = process_json_request(request, gateway)
        except json.JSONDecodeError:
            response = GatewayError(
                "invalid_request",
                "Gateway request must be UTF-8 JSON.",
            ).to_dict()
        except GatewayError as exc:
            response = exc.to_dict()
        except Exception as exc:  # pragma: no cover - last-resort process boundary
            response = {
                "ok": False,
                "status": "gateway_error",
                "message": sanitize_text(str(exc), 1000),
            }
        _write_json_response(outstream, response)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Metafx HQ Codex app-server gateway")
    parser.add_argument("--codex-bin", default=None)
    parser.add_argument("--cwd", default=None)
    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Keep one SDK client alive and process newline-delimited JSON requests.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    gateway: CodexAppServerGateway | None = None
    try:
        gateway = CodexAppServerGateway(codex_bin=args.codex_bin, cwd=args.cwd)
        if args.jsonl:
            # Read bytes when the real stdio buffer is available so UTF-8
            # requests cannot be decoded through a legacy Windows code page.
            instream = getattr(sys.stdin, "buffer", sys.stdin)
            return serve_json_lines(instream, sys.stdout, gateway)
        request = _read_json_stdin()
        operation = str(request.get("operation") or "")
        if operation in {"turn_wait", "turn_interrupt"}:
            raise GatewayError(
                "persistent_gateway_required",
                "Use --jsonl or an imported long-lived gateway for active-turn operations.",
            )
        if operation == "turn_start" and not bool(request.get("wait", False)):
            raise GatewayError(
                "persistent_gateway_required",
                "One-shot turn_start must set wait=true; use --jsonl for asynchronous turns.",
            )
        response = process_json_request(request, gateway)
        exit_code = 0
    except GatewayError as exc:
        response = exc.to_dict()
        exit_code = 2
    except Exception as exc:  # pragma: no cover - last-resort process boundary
        response = {
            "ok": False,
            "status": "gateway_error",
            "message": sanitize_text(str(exc), 1000),
        }
        exit_code = 3
    finally:
        if gateway is not None:
            gateway.close()
    _write_json_response(sys.stdout, response)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
