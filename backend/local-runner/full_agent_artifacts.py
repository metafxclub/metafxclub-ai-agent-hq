"""Thread-bound, path-opaque media storage for the Full Agent surface.

The browser never supplies or receives a filesystem path.  Uploads are
validated from bytes, stored below one backend-owned root, and addressed by
unguessable IDs.  Generated artifacts can be copied into the same immutable
store before a same-origin download URL is published to the frontend.

This module deliberately does not execute files, unpack Office documents, or
grant a model access to arbitrary local paths.
"""

from __future__ import annotations

import base64
import binascii
import contextlib
import hashlib
import json
import os
import re
import secrets
import stat
import struct
import threading
import time
import unicodedata
import urllib.parse
import zipfile
import zlib
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
MAX_ATTACHMENTS_PER_TURN = 4
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_UPLOAD_REQUEST_BYTES = 12 * 1024 * 1024
MAX_OUTPUT_BYTES = 50 * 1024 * 1024
MAX_STORE_ITEMS = 512
MAX_FILE_NAME_CHARS = 180
MAX_IMAGE_EDGE = 16_384
MAX_IMAGE_PIXELS = 40_000_000
DEFAULT_TTL_SECONDS = 24 * 60 * 60
MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 7 * 24 * 60 * 60
MAX_ARCHIVE_ITEMS = 2_000
MAX_ARCHIVE_EXPANDED_BYTES = 128 * 1024 * 1024
STAGING_DIRECTORY = ".staging"
QUARANTINE_DIRECTORY = ".quarantine"

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,191}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_BIDI_CONTROL_RE = re.compile(r"[\u202a-\u202e\u2066-\u2069]")
_SECRET_RE = re.compile(
    r"(?i)(?:\bBearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"\bsk-[A-Za-z0-9_-]{16,}|\bGOCSPX-[A-Za-z0-9_-]{16,}|"
    r"\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|"
    r"password|private[_-]?key)\b\s*[:=]\s*[^\s,;]{8,})"
)

_TYPE_BY_SUFFIX: dict[str, tuple[str, str]] = {
    ".png": ("image/png", "image"),
    ".jpg": ("image/jpeg", "image"),
    ".jpeg": ("image/jpeg", "image"),
    ".webp": ("image/webp", "image"),
    ".pdf": ("application/pdf", "document"),
    ".pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "presentation",
    ),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "document",
    ),
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "spreadsheet",
    ),
    ".txt": ("text/plain", "text"),
    ".md": ("text/markdown", "text"),
    ".csv": ("text/csv", "text"),
    ".json": ("application/json", "text"),
    ".html": ("text/html", "text"),
    ".css": ("text/css", "text"),
    ".js": ("text/javascript", "source"),
    ".ts": ("text/typescript", "source"),
    ".py": ("text/x-python", "source"),
    ".mq4": ("text/plain", "source"),
    ".mq5": ("text/plain", "source"),
    ".zip": ("application/zip", "archive"),
}

_OOXML_MARKERS = {
    ".pptx": "ppt/presentation.xml",
    ".docx": "word/document.xml",
    ".xlsx": "xl/workbook.xml",
}


class FullAgentArtifactError(RuntimeError):
    def __init__(self, code: str, message: str, *, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _utc_from_epoch(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def _epoch_from_utc(value: object) -> float:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise FullAgentArtifactError(
            "artifact_metadata_invalid", "Artifact expiry metadata is invalid.", status=404
        )
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").timestamp()
    except ValueError as error:
        raise FullAgentArtifactError(
            "artifact_metadata_invalid", "Artifact expiry metadata is invalid.", status=404
        ) from error


def _ttl_seconds(value: object | None, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise FullAgentArtifactError("invalid_ttl", "Artifact TTL is invalid.")
    if value < MIN_TTL_SECONDS or value > MAX_TTL_SECONDS:
        raise FullAgentArtifactError("invalid_ttl", "Artifact TTL is outside the safe range.")
    return value


def _is_link(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & flag)
    except FileNotFoundError:
        return False


def _safe_root(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or ".." in path.parts:
        raise FullAgentArtifactError(
            "unsafe_artifact_root", "Artifact storage must be an absolute local path."
        )
    for candidate in reversed((path, *path.parents)):
        if candidate.exists() and _is_link(candidate):
            raise FullAgentArtifactError(
                "unsafe_artifact_root", "Artifact storage cannot use links."
            )
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    resolved = path.resolve(strict=True)
    if (
        _is_link(resolved)
        or not resolved.is_dir()
        or resolved == Path(resolved.anchor)
    ):
        raise FullAgentArtifactError(
            "unsafe_artifact_root", "Artifact storage is unavailable."
        )
    with contextlib.suppress(OSError):
        os.chmod(resolved, 0o700)
    return resolved


def _safe_output_source(
    value: str | os.PathLike[str],
    allowed_roots: Sequence[str | os.PathLike[str]],
) -> Path:
    """Resolve one generated file below an explicit backend-owned root.

    Output publication must never become an arbitrary local-file download
    primitive.  The caller therefore has to name at least one absolute root,
    and every existing path component from that root to the file must be a
    regular, non-link path.
    """

    roots = tuple(allowed_roots or ())
    if not roots:
        raise FullAgentArtifactError(
            "unsafe_output_source", "Generated artifact roots are not configured."
        )
    source = Path(value).expanduser()
    if not source.is_absolute() or ".." in source.parts:
        raise FullAgentArtifactError(
            "unsafe_output_source", "Generated artifact source is outside the allowed roots."
        )
    try:
        resolved_source = source.resolve(strict=True)
    except OSError as error:
        raise FullAgentArtifactError(
            "artifact_unavailable", "Generated artifact is unavailable.", status=404
        ) from error
    if not resolved_source.is_file() or _is_link(source) or _is_link(resolved_source):
        raise FullAgentArtifactError(
            "artifact_unavailable", "Generated artifact is unavailable.", status=404
        )
    for root_value in roots:
        root = Path(root_value).expanduser()
        if not root.is_absolute() or ".." in root.parts:
            continue
        if any(
            candidate.exists() and _is_link(candidate)
            for candidate in (root, *root.parents)
        ):
            continue
        try:
            resolved_root = root.resolve(strict=True)
            resolved_source.relative_to(resolved_root)
        except (OSError, ValueError):
            continue
        if (
            not resolved_root.is_dir()
            or resolved_root == Path(resolved_root.anchor)
            or _is_link(root)
            or _is_link(resolved_root)
        ):
            continue
        current = source
        safe = True
        while current != root and current != current.parent:
            if _is_link(current):
                safe = False
                break
            current = current.parent
        if safe and current == root:
            return resolved_source
    raise FullAgentArtifactError(
        "unsafe_output_source", "Generated artifact source is outside the allowed roots."
    )


def _safe_id(value: object, field: str) -> str:
    text = str(value or "").strip()
    if _SAFE_ID_RE.fullmatch(text) is None:
        raise FullAgentArtifactError("invalid_request", f"{field} is invalid.")
    return text


def _safe_file_name(value: object) -> tuple[str, str]:
    text = unicodedata.normalize("NFC", str(value or "")).strip()
    text = _BIDI_CONTROL_RE.sub("", _CONTROL_RE.sub("", text))
    if (
        not text
        or len(text) > MAX_FILE_NAME_CHARS
        or text in {".", ".."}
        or Path(text).name != text
        or any(character in text for character in ("/", "\\", ":"))
    ):
        raise FullAgentArtifactError("invalid_file_name", "File name is invalid.")
    suffix = Path(text).suffix.lower()
    if suffix not in _TYPE_BY_SUFFIX:
        raise FullAgentArtifactError(
            "unsupported_file_type", "This file type is not supported."
        )
    return text, suffix


def _decode_base64(value: object) -> bytes:
    if not isinstance(value, str) or not value:
        raise FullAgentArtifactError("invalid_upload", "File data is required.")
    if len(value) > ((MAX_UPLOAD_BYTES + 2) // 3) * 4 + 8:
        raise FullAgentArtifactError("upload_too_large", "File is too large.", status=413)
    try:
        payload = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise FullAgentArtifactError(
            "invalid_upload", "File data must be strict base64."
        ) from error
    if not payload:
        raise FullAgentArtifactError("invalid_upload", "File is empty.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise FullAgentArtifactError("upload_too_large", "File is too large.", status=413)
    return payload


def _validate_text(payload: bytes, suffix: str) -> None:
    if b"\x00" in payload:
        raise FullAgentArtifactError("invalid_file_content", "Text file contains NUL bytes.")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise FullAgentArtifactError(
            "invalid_file_content", "Text files must use UTF-8."
        ) from error
    if suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as error:
            raise FullAgentArtifactError(
                "invalid_file_content", "JSON attachment is malformed."
            ) from error
    if _SECRET_RE.search(text):
        raise FullAgentArtifactError(
            "secret_rejected", "Text artifact appears to contain authentication material."
        )


def _validate_archive(path: Path) -> None:
    """Validate a ZIP container without extracting or executing it."""

    blocked_suffixes = {
        ".bat",
        ".cmd",
        ".com",
        ".dll",
        ".exe",
        ".hta",
        ".jar",
        ".lnk",
        ".msi",
        ".ps1",
        ".scr",
        ".vbs",
    }
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_ARCHIVE_ITEMS:
                raise FullAgentArtifactError(
                    "invalid_file_content", "ZIP archive has an unsafe layout."
                )
            expanded = 0
            for info in infos:
                normalized = info.filename.replace("\\", "/")
                parts = [part for part in normalized.split("/") if part]
                mode = (int(info.external_attr) >> 16) & 0xFFFF
                if (
                    normalized.startswith("/")
                    or not parts
                    or any(part in {".", ".."} for part in parts)
                    or bool(info.flag_bits & 0x1)
                    or stat.S_ISLNK(mode)
                    or Path(parts[-1]).suffix.casefold() in blocked_suffixes
                ):
                    raise FullAgentArtifactError(
                        "invalid_file_content", "ZIP archive contains an unsafe entry."
                    )
                expanded += int(info.file_size)
                if expanded > MAX_ARCHIVE_EXPANDED_BYTES:
                    raise FullAgentArtifactError(
                        "invalid_file_content", "ZIP archive expands beyond the safe limit."
                    )
                if (
                    info.file_size > 1_048_576
                    and info.compress_size > 0
                    and info.file_size / info.compress_size > 1_000
                ):
                    raise FullAgentArtifactError(
                        "invalid_file_content", "ZIP archive has an unsafe compression ratio."
                    )
            bad_entry = archive.testzip()
            if bad_entry is not None:
                raise FullAgentArtifactError(
                    "invalid_file_content", "ZIP archive integrity validation failed."
                )
    except (zipfile.BadZipFile, OSError) as error:
        raise FullAgentArtifactError(
            "invalid_file_content", "ZIP archive is invalid."
        ) from error


def _validate_ooxml(path: Path, suffix: str) -> None:
    marker = _OOXML_MARKERS[suffix]
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            if not infos or len(infos) > 2_000:
                raise FullAgentArtifactError(
                    "invalid_file_content", "Office document has an unsafe archive layout."
                )
            total = 0
            names: set[str] = set()
            for info in infos:
                normalized = info.filename.replace("\\", "/")
                lowered = normalized.lower()
                parts = [part for part in normalized.split("/") if part]
                if (
                    normalized.startswith("/")
                    or any(part == ".." for part in parts)
                    or info.file_size < 0
                    or bool(info.flag_bits & 0x1)
                    or "vbaproject.bin" in lowered
                    or "/activex/" in f"/{lowered}"
                    or "/embeddings/" in f"/{lowered}"
                    or "/externallinks/" in f"/{lowered}"
                ):
                    raise FullAgentArtifactError(
                        "invalid_file_content", "Office document contains unsafe active content."
                    )
                if (
                    info.file_size > 1_048_576
                    and info.compress_size > 0
                    and info.file_size / info.compress_size > 1_000
                ):
                    raise FullAgentArtifactError(
                        "invalid_file_content", "Office document has an unsafe compression ratio."
                    )
                total += int(info.file_size)
                if total > 128 * 1024 * 1024:
                    raise FullAgentArtifactError(
                        "invalid_file_content", "Office document expands beyond the safe limit."
                    )
                names.add(normalized)
                if lowered.endswith(".rels") and info.file_size <= 2 * 1024 * 1024:
                    relationship_xml = archive.read(info)
                    if re.search(
                        rb"targetmode\s*=\s*(['\"])external\1",
                        relationship_xml,
                        flags=re.IGNORECASE,
                    ):
                        raise FullAgentArtifactError(
                            "invalid_file_content", "Office document contains an external relationship."
                        )
            if "[Content_Types].xml" not in names or marker not in names:
                raise FullAgentArtifactError(
                    "invalid_file_content", "Office document does not match its extension."
                )
            if archive.testzip() is not None:
                raise FullAgentArtifactError(
                    "invalid_file_content", "Office document integrity validation failed."
                )
    except (zipfile.BadZipFile, OSError) as error:
        raise FullAgentArtifactError(
            "invalid_file_content", "Office document is not a valid OOXML file."
        ) from error


def _validate_image_dimensions(width: int, height: int) -> None:
    if (
        width <= 0
        or height <= 0
        or width > MAX_IMAGE_EDGE
        or height > MAX_IMAGE_EDGE
        or width * height > MAX_IMAGE_PIXELS
    ):
        raise FullAgentArtifactError(
            "invalid_file_content", "Image dimensions exceed the safe limit."
        )


def _validate_png(payload: bytes) -> None:
    if len(payload) < 45 or not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise FullAgentArtifactError("invalid_file_content", "PNG signature is invalid.")
    offset = 8
    width = height = 0
    saw_idat = False
    saw_iend = False
    while offset + 12 <= len(payload):
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        chunk_type = payload[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if length > MAX_UPLOAD_BYTES or crc_end > len(payload):
            raise FullAgentArtifactError("invalid_file_content", "PNG chunk is invalid.")
        expected_crc = struct.unpack(">I", payload[data_end:crc_end])[0]
        if zlib.crc32(chunk_type + payload[data_start:data_end]) & 0xFFFFFFFF != expected_crc:
            raise FullAgentArtifactError("invalid_file_content", "PNG checksum is invalid.")
        if chunk_type == b"IHDR":
            if offset != 8 or length != 13:
                raise FullAgentArtifactError("invalid_file_content", "PNG header is invalid.")
            width, height = struct.unpack(">II", payload[data_start : data_start + 8])
            _validate_image_dimensions(width, height)
        elif chunk_type == b"IDAT":
            saw_idat = True
        elif chunk_type == b"IEND":
            if length != 0 or crc_end != len(payload):
                raise FullAgentArtifactError("invalid_file_content", "PNG terminator is invalid.")
            saw_iend = True
            break
        offset = crc_end
    if not width or not height or not saw_idat or not saw_iend:
        raise FullAgentArtifactError("invalid_file_content", "PNG structure is incomplete.")


def _validate_jpeg(payload: bytes) -> None:
    if len(payload) < 16 or not payload.startswith(b"\xff\xd8") or not payload.endswith(b"\xff\xd9"):
        raise FullAgentArtifactError("invalid_file_content", "JPEG structure is invalid.")
    offset = 2
    dimensions: tuple[int, int] | None = None
    standalone = {0x01, *range(0xD0, 0xD9)}
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset < len(payload) - 1:
        if payload[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(payload) and payload[offset] == 0xFF:
            offset += 1
        if offset >= len(payload):
            break
        marker = payload[offset]
        offset += 1
        if marker in standalone:
            continue
        if offset + 2 > len(payload):
            break
        segment_length = struct.unpack(">H", payload[offset : offset + 2])[0]
        if segment_length < 2 or offset + segment_length > len(payload):
            raise FullAgentArtifactError("invalid_file_content", "JPEG segment is invalid.")
        if marker in sof_markers:
            if segment_length < 7:
                raise FullAgentArtifactError("invalid_file_content", "JPEG frame is invalid.")
            height, width = struct.unpack(">HH", payload[offset + 3 : offset + 7])
            _validate_image_dimensions(width, height)
            dimensions = (width, height)
        if marker == 0xDA:
            break
        offset += segment_length
    if dimensions is None:
        raise FullAgentArtifactError("invalid_file_content", "JPEG dimensions are unavailable.")


def _validate_webp(payload: bytes) -> None:
    if not (
        len(payload) >= 30
        and payload[:4] == b"RIFF"
        and payload[8:12] == b"WEBP"
        and struct.unpack("<I", payload[4:8])[0] + 8 == len(payload)
    ):
        raise FullAgentArtifactError("invalid_file_content", "WebP structure is invalid.")
    kind = payload[12:16]
    if kind == b"VP8X" and len(payload) >= 30:
        width = 1 + int.from_bytes(payload[24:27], "little")
        height = 1 + int.from_bytes(payload[27:30], "little")
    elif kind == b"VP8L" and len(payload) >= 25 and payload[20] == 0x2F:
        bits = int.from_bytes(payload[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
    elif kind == b"VP8 " and len(payload) >= 30 and payload[23:26] == b"\x9d\x01\x2a":
        width = struct.unpack("<H", payload[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", payload[28:30])[0] & 0x3FFF
    else:
        raise FullAgentArtifactError("invalid_file_content", "WebP dimensions are unavailable.")
    _validate_image_dimensions(width, height)


def _validate_payload(path: Path, payload: bytes, suffix: str) -> tuple[str, str]:
    media_type, kind = _TYPE_BY_SUFFIX[suffix]
    if suffix == ".png":
        _validate_png(payload)
    if suffix in {".jpg", ".jpeg"}:
        _validate_jpeg(payload)
    if suffix == ".webp":
        _validate_webp(payload)
    if suffix == ".pdf":
        lowered = payload.lower()
        if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-2048:]:
            raise FullAgentArtifactError("invalid_file_content", "PDF structure is invalid.")
        if any(
            marker in lowered
            for marker in (
                b"/javascript",
                b"/launch",
                b"/embeddedfile",
                b"/openaction",
            )
        ):
            raise FullAgentArtifactError(
                "invalid_file_content", "PDF contains unsupported active content."
            )
    if suffix in _OOXML_MARKERS:
        _validate_ooxml(path, suffix)
    elif suffix == ".zip":
        _validate_archive(path)
    elif kind in {"text", "source"}:
        _validate_text(payload, suffix)
    return media_type, kind


class FullAgentArtifactStore:
    """Immutable attachment/artifact store bound to durable HQ thread IDs."""

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        default_ttl_seconds: int = DEFAULT_TTL_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.root = _safe_root(root)
        self.staging_root = _safe_root(self.root / STAGING_DIRECTORY)
        self.quarantine_root = _safe_root(self.root / QUARANTINE_DIRECTORY)
        self.default_ttl_seconds = _ttl_seconds(
            default_ttl_seconds, DEFAULT_TTL_SECONDS
        )
        self._clock = clock or time.time
        self._lock = threading.RLock()

    @staticmethod
    def accepted_extensions() -> list[str]:
        return sorted(_TYPE_BY_SUFFIX)

    def _metadata_path(self, artifact_id: str) -> Path:
        return self.root / f"{artifact_id}.meta.json"

    def _stage_metadata_path(self, stage_id: str) -> Path:
        return self.staging_root / f"{stage_id}.meta.json"

    def _now(self) -> float:
        value = float(self._clock())
        if value < 0 or value != value:
            raise FullAgentArtifactError(
                "artifact_clock_invalid", "Artifact clock is unavailable.", status=500
            )
        return value

    def _expiry(self, ttl_seconds: object | None = None) -> str:
        ttl = _ttl_seconds(ttl_seconds, self.default_ttl_seconds)
        return _utc_from_epoch(self._now() + ttl)

    def _write_bytes(self, destination: Path, payload: bytes) -> None:
        flags = (
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_BINARY", 0)
        )
        descriptor = os.open(destination, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        flags = getattr(os, "O_DIRECTORY", 0) | os.O_RDONLY
        try:
            descriptor = os.open(path, flags)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        except OSError:
            pass
        finally:
            os.close(descriptor)

    def _write_json_atomic(
        self,
        destination: Path,
        metadata: Mapping[str, Any],
    ) -> None:
        encoded = (
            json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        temporary = destination.parent / f".{destination.name}.{secrets.token_hex(8)}.tmp"
        try:
            self._write_bytes(temporary, encoded)
            os.replace(temporary, destination)
            self._fsync_directory(destination.parent)
        finally:
            with contextlib.suppress(OSError):
                temporary.unlink()

    def _write_metadata(self, metadata: Mapping[str, Any]) -> None:
        self._write_json_atomic(
            self._metadata_path(str(metadata["id"])),
            metadata,
        )

    @staticmethod
    def _read_json(path: Path, *, code: str) -> dict[str, Any]:
        if not path.is_file() or _is_link(path):
            raise FullAgentArtifactError(code, "Artifact record was not found.", status=404)
        try:
            if path.stat().st_size > 64 * 1024:
                raise OSError("metadata too large")
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise FullAgentArtifactError(
                code, "Artifact record is unavailable.", status=404
            ) from error
        if not isinstance(value, dict):
            raise FullAgentArtifactError(code, "Artifact record is invalid.", status=404)
        return value

    @staticmethod
    def _assert_owner(
        metadata: Mapping[str, Any],
        thread: str,
        turn: str,
        *,
        code: str,
    ) -> None:
        if metadata.get("threadId") != thread or metadata.get("turnId") != turn:
            # Return the same 404 for a missing item and an ownership mismatch
            # so opaque identifiers cannot be used as an enumeration oracle.
            raise FullAgentArtifactError(code, "Artifact was not found.", status=404)

    def _store_item_count(self) -> int:
        count = 0
        for path in self.root.glob("*.meta.json"):
            if not path.is_file() or _is_link(path):
                continue
            try:
                metadata = self._read_json(path, code="artifact_not_found")
            except FullAgentArtifactError:
                # Corrupt records remain capacity-bearing until an operator
                # removes them; silently ignoring them would weaken the cap.
                count += 1
                continue
            if metadata.get("state") in {"consumed", "revoked"}:
                continue
            count += 1
        return count

    def _input_count(self, thread: str, turn: str) -> int:
        count = 0
        for directory in (self.root, self.staging_root):
            for path in directory.glob("*.meta.json"):
                try:
                    metadata = self._read_json(path, code="artifact_not_found")
                except FullAgentArtifactError:
                    continue
                if (
                    metadata.get("threadId") == thread
                    and metadata.get("turnId") == turn
                    and metadata.get("direction") == "input"
                    and metadata.get("state") in {"ready", "staged"}
                ):
                    count += 1
        return count

    def _begin_stage(
        self,
        thread_id: object,
        turn_id: object,
        *,
        file_name: object,
        media_type: object,
        direction: str,
        ttl_seconds: object | None,
    ) -> dict[str, Any]:
        thread = _safe_id(thread_id, "threadId")
        turn = _safe_id(turn_id, "turnId")
        name, suffix = _safe_file_name(file_name)
        expected_media_type, _kind = _TYPE_BY_SUFFIX[suffix]
        claimed = str(media_type or "").strip().lower()
        if claimed and claimed not in {expected_media_type, "application/octet-stream"}:
            raise FullAgentArtifactError(
                "media_type_mismatch", "Declared media type does not match the file."
            )
        with self._lock:
            # Reclaim expired records before enforcing the hard capacity cap.
            # The lock is re-entrant and cleanup never exposes a read model.
            self.cleanup_expired()
            staged_count = sum(
                1
                for path in self.staging_root.glob("*.meta.json")
                if path.is_file() and not _is_link(path)
            )
            if self._store_item_count() + staged_count >= MAX_STORE_ITEMS:
                raise FullAgentArtifactError(
                    "artifact_store_full",
                    "Artifact storage reached its safe item limit.",
                    status=409,
                )
            if direction == "input" and self._input_count(thread, turn) >= MAX_ATTACHMENTS_PER_TURN:
                raise FullAgentArtifactError(
                    "too_many_attachments",
                    "This turn has reached the attachment limit.",
                    status=409,
                )
            stage_id = f"stage_{secrets.token_hex(16)}"
            now = self._now()
            metadata = {
                "schemaVersion": SCHEMA_VERSION,
                "stageId": stage_id,
                "threadId": thread,
                "turnId": turn,
                "name": name,
                "suffix": suffix,
                "mediaType": expected_media_type,
                "direction": direction,
                "createdAt": _utc_from_epoch(now),
                "expiresAt": _utc_from_epoch(
                    now + _ttl_seconds(ttl_seconds, self.default_ttl_seconds)
                ),
                "state": "staged",
            }
            self._write_json_atomic(self._stage_metadata_path(stage_id), metadata)
            return metadata

    def begin_output(
        self,
        thread_id: object,
        turn_id: object,
        *,
        file_name: object,
        media_type: object = "",
        ttl_seconds: object | None = None,
    ) -> dict[str, Any]:
        """Reserve a backend-owned staging slot without exposing its path."""

        metadata = self._begin_stage(
            thread_id,
            turn_id,
            file_name=file_name,
            media_type=media_type,
            direction="output",
            ttl_seconds=ttl_seconds,
        )
        return {
            "stageId": metadata["stageId"],
            "name": metadata["name"],
            "mediaType": metadata["mediaType"],
            "expiresAt": metadata["expiresAt"],
        }

    def _load_stage(self, stage_id: object) -> dict[str, Any]:
        identifier = _safe_id(stage_id, "stageId")
        metadata = self._read_json(
            self._stage_metadata_path(identifier), code="stage_not_found"
        )
        if metadata.get("stageId") != identifier or metadata.get("state") != "staged":
            raise FullAgentArtifactError(
                "stage_not_found", "Artifact stage was not found.", status=404
            )
        return metadata

    def _stage_file_path(self, metadata: Mapping[str, Any]) -> Path:
        stage_id = _safe_id(metadata.get("stageId"), "stageId")
        suffix = str(metadata.get("suffix") or "")
        if suffix not in _TYPE_BY_SUFFIX:
            raise FullAgentArtifactError(
                "stage_not_found", "Artifact stage is invalid.", status=404
            )
        return self.staging_root / f"{stage_id}{suffix}"

    def staging_path(
        self,
        thread_id: object,
        turn_id: object,
        stage_id: object,
    ) -> Path:
        """Return a path only to a trusted backend worker, never a read model."""

        thread = _safe_id(thread_id, "threadId")
        turn = _safe_id(turn_id, "turnId")
        with self._lock:
            metadata = self._load_stage(stage_id)
            self._assert_owner(metadata, thread, turn, code="stage_not_found")
            if self._now() >= _epoch_from_utc(metadata.get("expiresAt")):
                self._quarantine_stage(metadata, "stage_expired")
                raise FullAgentArtifactError(
                    "stage_expired", "Artifact stage expired.", status=410
                )
            return self._stage_file_path(metadata)

    def _quarantine_stage(
        self,
        metadata: Mapping[str, Any],
        reason: str,
        *,
        source_path: Path | None = None,
    ) -> None:
        try:
            stage_id = _safe_id(metadata.get("stageId"), "stageId")
        except FullAgentArtifactError:
            return
        suffix = str(metadata.get("suffix") or "")
        if suffix not in _TYPE_BY_SUFFIX:
            return
        source = source_path or self.staging_root / f"{stage_id}{suffix}"
        try:
            source_parent = source.parent.resolve(strict=True)
        except OSError:
            source_parent = source.parent
        if source_parent not in {self.root, self.staging_root}:
            source = self.staging_root / f"{stage_id}{suffix}"
        quarantine_id = f"q_{secrets.token_hex(16)}"
        stored_name: str | None = None
        if source.is_file() and not _is_link(source):
            destination = self.quarantine_root / f"{quarantine_id}{suffix}"
            try:
                os.replace(source, destination)
                with contextlib.suppress(OSError):
                    os.chmod(destination, 0o600)
                stored_name = destination.name
            except OSError:
                with contextlib.suppress(OSError):
                    source.unlink()
        record = {
            "schemaVersion": SCHEMA_VERSION,
            "quarantineId": quarantine_id,
            "stageId": stage_id,
            "threadId": metadata.get("threadId"),
            "turnId": metadata.get("turnId"),
            "name": metadata.get("name"),
            "suffix": suffix,
            "reason": re.sub(r"[^a-z0-9_:-]", "_", str(reason).casefold())[:80],
            "storedName": stored_name,
            "createdAt": _utc_from_epoch(self._now()),
            "expiresAt": _utc_from_epoch(self._now() + self.default_ttl_seconds),
            "state": "quarantined",
        }
        with contextlib.suppress(OSError):
            self._write_json_atomic(
                self.quarantine_root / f"{quarantine_id}.meta.json", record
            )
        with contextlib.suppress(OSError):
            self._stage_metadata_path(stage_id).unlink()

    def _write_stage_payload(self, metadata: Mapping[str, Any], payload: bytes) -> None:
        self._write_bytes(self._stage_file_path(metadata), payload)

    def _finalize_stage(
        self,
        thread_id: object,
        turn_id: object,
        stage_id: object,
        *,
        expected_direction: str,
    ) -> dict[str, Any]:
        thread = _safe_id(thread_id, "threadId")
        turn = _safe_id(turn_id, "turnId")
        with self._lock:
            metadata = self._load_stage(stage_id)
            self._assert_owner(metadata, thread, turn, code="stage_not_found")
            if metadata.get("direction") != expected_direction:
                raise FullAgentArtifactError(
                    "stage_not_found", "Artifact stage was not found.", status=404
                )
            if self._now() >= _epoch_from_utc(metadata.get("expiresAt")):
                self._quarantine_stage(metadata, "stage_expired")
                raise FullAgentArtifactError(
                    "stage_expired", "Artifact stage expired.", status=410
                )
            staged_path = self._stage_file_path(metadata)
            if (
                not staged_path.is_file()
                or _is_link(staged_path)
                or staged_path.parent.resolve() != self.staging_root
            ):
                self._quarantine_stage(metadata, "stage_file_unavailable")
                raise FullAgentArtifactError(
                    "stage_file_unavailable", "Staged artifact is unavailable.", status=404
                )
            limit = MAX_UPLOAD_BYTES if expected_direction == "input" else MAX_OUTPUT_BYTES
            try:
                size = int(staged_path.stat().st_size)
                if size <= 0 or size > limit:
                    raise FullAgentArtifactError(
                        "artifact_too_large", "Artifact exceeds the safe limit.", status=413
                    )
                payload = staged_path.read_bytes()
                if len(payload) != size:
                    raise FullAgentArtifactError(
                        "artifact_changed", "Artifact changed during validation.", status=409
                    )
                media_type, kind = _validate_payload(
                    staged_path, payload, str(metadata["suffix"])
                )
            except FullAgentArtifactError as error:
                self._quarantine_stage(metadata, error.code)
                raise
            except OSError as error:
                self._quarantine_stage(metadata, "artifact_unavailable")
                raise FullAgentArtifactError(
                    "artifact_unavailable",
                    "Staged artifact could not be validated.",
                    status=404,
                ) from error

            prefix = "att" if expected_direction == "input" else "art"
            artifact_id = f"{prefix}_{secrets.token_hex(16)}"
            destination = self.root / f"{artifact_id}{metadata['suffix']}"
            final_metadata = {
                "schemaVersion": SCHEMA_VERSION,
                "id": artifact_id,
                "threadId": thread,
                "turnId": turn,
                "name": metadata["name"],
                "suffix": metadata["suffix"],
                "mediaType": media_type,
                "kind": kind,
                "byteSize": size,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "direction": expected_direction,
                "modelInputReady": expected_direction == "input" and kind == "image",
                "createdAt": metadata["createdAt"],
                "finalizedAt": _utc_from_epoch(self._now()),
                "expiresAt": metadata["expiresAt"],
                "state": "ready",
            }
            try:
                os.replace(staged_path, destination)
                with contextlib.suppress(OSError):
                    os.chmod(destination, 0o600)
                self._fsync_directory(self.root)
                self._write_metadata(final_metadata)
            except Exception as error:
                self._quarantine_stage(
                    metadata, "atomic_finalize_failed", source_path=destination
                )
                if isinstance(error, FullAgentArtifactError):
                    raise
                raise FullAgentArtifactError(
                    "atomic_finalize_failed",
                    "Artifact could not be finalized atomically.",
                    status=500,
                ) from error
            with contextlib.suppress(OSError):
                self._stage_metadata_path(str(metadata["stageId"])).unlink()
            return self.read_model(final_metadata)

    def finalize_output(
        self,
        thread_id: object,
        turn_id: object,
        stage_id: object,
    ) -> dict[str, Any]:
        return self._finalize_stage(
            thread_id, turn_id, stage_id, expected_direction="output"
        )

    def save_upload(
        self,
        thread_id: object,
        turn_id: object,
        *,
        file_name: object,
        media_type: object,
        data_base64: object,
        ttl_seconds: object | None = None,
    ) -> dict[str, Any]:
        payload = _decode_base64(data_base64)
        with self._lock:
            stage = self._begin_stage(
                thread_id,
                turn_id,
                file_name=file_name,
                media_type=media_type,
                direction="input",
                ttl_seconds=ttl_seconds,
            )
            try:
                self._write_stage_payload(stage, payload)
            except Exception:
                self._quarantine_stage(stage, "stage_write_failed")
                raise
            return self._finalize_stage(
                thread_id,
                turn_id,
                stage["stageId"],
                expected_direction="input",
            )

    def _copy_source_to_stage(self, source: Path, destination: Path) -> None:
        source_flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_BINARY", 0)
        )
        source_descriptor = os.open(source, source_flags)
        destination_flags = (
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_BINARY", 0)
        )
        destination_descriptor = -1
        try:
            before = os.fstat(source_descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
                raise FullAgentArtifactError(
                    "artifact_unavailable", "Generated artifact is unavailable.", status=404
                )
            if before.st_size > MAX_OUTPUT_BYTES:
                raise FullAgentArtifactError(
                    "artifact_too_large", "Generated artifact exceeds the safe limit.", status=413
                )
            destination_descriptor = os.open(destination, destination_flags, 0o600)
            total = 0
            copied_digest = hashlib.sha256()
            while True:
                chunk = os.read(source_descriptor, 1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_OUTPUT_BYTES:
                    raise FullAgentArtifactError(
                        "artifact_too_large", "Generated artifact exceeds the safe limit.", status=413
                    )
                copied_digest.update(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(destination_descriptor, view)
                    if written <= 0:
                        raise OSError("short artifact write")
                    view = view[written:]
            os.fsync(destination_descriptor)

            # Verify a second snapshot from the same open descriptor.  This is
            # stronger than trusting only mtime, and avoids false positives on
            # Windows filesystems where timestamp metadata may settle after a
            # newly-created file is first opened (observed on hosted runners).
            os.lseek(source_descriptor, 0, os.SEEK_SET)
            verified_total = 0
            verified_digest = hashlib.sha256()
            while True:
                chunk = os.read(source_descriptor, 1024 * 1024)
                if not chunk:
                    break
                verified_total += len(chunk)
                if verified_total > MAX_OUTPUT_BYTES:
                    raise FullAgentArtifactError(
                        "artifact_too_large", "Generated artifact exceeds the safe limit.", status=413
                    )
                verified_digest.update(chunk)
            after = os.fstat(source_descriptor)
            if (
                total != before.st_size
                or verified_total != before.st_size
                or after.st_size != before.st_size
                or after.st_mode != before.st_mode
                or after.st_dev != before.st_dev
                or after.st_ino != before.st_ino
                or verified_digest.digest() != copied_digest.digest()
            ):
                raise FullAgentArtifactError(
                    "artifact_changed", "Generated artifact changed during staging.", status=409
                )
        finally:
            os.close(source_descriptor)
            if destination_descriptor >= 0:
                os.close(destination_descriptor)

    def publish_output(
        self,
        thread_id: object,
        turn_id: object,
        source_path: str | os.PathLike[str],
        *,
        file_name: object | None = None,
        media_type: object = "",
        allowed_roots: Sequence[str | os.PathLike[str]],
        ttl_seconds: object | None = None,
    ) -> dict[str, Any]:
        return self.publish_outputs(
            thread_id,
            turn_id,
            (source_path,),
            file_names=(file_name,),
            media_types=(media_type,),
            allowed_roots=allowed_roots,
            ttl_seconds=ttl_seconds,
        )[0]

    def publish_outputs(
        self,
        thread_id: object,
        turn_id: object,
        source_paths: Sequence[str | os.PathLike[str]],
        *,
        file_names: Sequence[object | None] | None = None,
        media_types: Sequence[object] | None = None,
        allowed_roots: Sequence[str | os.PathLike[str]],
        ttl_seconds: object | None = None,
    ) -> list[dict[str, Any]]:
        """Publish a backend-selected output batch or leave no resolvable prefix."""

        sources = [_safe_output_source(value, allowed_roots) for value in source_paths]
        names = list(file_names) if file_names is not None else [None] * len(sources)
        types = list(media_types) if media_types is not None else [""] * len(sources)
        if len(names) != len(sources) or len(types) != len(sources):
            raise FullAgentArtifactError(
                "invalid_request", "Artifact batch metadata length is invalid.", status=422
            )
        stages: list[dict[str, Any]] = []
        published: list[dict[str, Any]] = []
        with self._lock:
            try:
                # Copy every bounded source before exposing any ready artifact.
                for source, name, media_type in zip(sources, names, types):
                    stage = self._begin_stage(
                        thread_id,
                        turn_id,
                        file_name=name or source.name,
                        media_type=media_type,
                        direction="output",
                        ttl_seconds=ttl_seconds,
                    )
                    stages.append(stage)
                    try:
                        self._copy_source_to_stage(
                            source, self._stage_file_path(stage)
                        )
                    except Exception as error:
                        reason = (
                            error.code
                            if isinstance(error, FullAgentArtifactError)
                            else "stage_copy_failed"
                        )
                        self._quarantine_stage(stage, reason)
                        raise
                for stage in stages:
                    published.append(
                        self.finalize_output(
                            thread_id, turn_id, stage["stageId"]
                        )
                    )
                return published
            except Exception:
                # IDs are not returned or audited until the whole batch
                # succeeds. Revoke any ready prefix before propagating error.
                for artifact in reversed(published):
                    try:
                        self.revoke_artifact(
                            thread_id,
                            turn_id,
                            artifact.get("id"),
                            direction="output",
                        )
                    except FullAgentArtifactError:
                        pass
                for stage in stages:
                    try:
                        metadata = self._load_stage(stage.get("stageId"))
                    except FullAgentArtifactError:
                        continue
                    self._quarantine_stage(metadata, "batch_rollback")
                raise

    def _load_metadata(self, artifact_id: object) -> dict[str, Any]:
        identifier = _safe_id(artifact_id, "artifactId")
        metadata = self._read_json(
            self._metadata_path(identifier), code="artifact_not_found"
        )
        if (
            metadata.get("id") != identifier
            or metadata.get("state") != "ready"
            or metadata.get("suffix") not in _TYPE_BY_SUFFIX
        ):
            raise FullAgentArtifactError(
                "artifact_not_found", "Artifact metadata is invalid.", status=404
            )
        return metadata

    def resolve(
        self,
        thread_id: object,
        turn_id: object,
        artifact_id: object,
    ) -> tuple[Path, dict[str, Any]]:
        thread = _safe_id(thread_id, "threadId")
        turn = _safe_id(turn_id, "turnId")
        with self._lock:
            metadata = self._load_metadata(artifact_id)
            self._assert_owner(metadata, thread, turn, code="artifact_not_found")
            if self._now() >= _epoch_from_utc(metadata.get("expiresAt")):
                self._delete_artifact(metadata)
                raise FullAgentArtifactError(
                    "artifact_expired", "Artifact expired.", status=410
                )
            suffix = str(metadata["suffix"])
            path = self.root / f"{metadata['id']}{suffix}"
            if not path.is_file() or _is_link(path) or path.parent.resolve() != self.root:
                raise FullAgentArtifactError(
                    "artifact_not_found", "Artifact file is unavailable.", status=404
                )
            size = int(path.stat().st_size)
            limit = MAX_UPLOAD_BYTES if metadata.get("direction") == "input" else MAX_OUTPUT_BYTES
            if size <= 0 or size > limit:
                raise FullAgentArtifactError(
                    "artifact_integrity_failed", "Artifact integrity check failed.", status=409
                )
            payload = path.read_bytes()
            if (
                len(payload) != int(metadata.get("byteSize") or -1)
                or hashlib.sha256(payload).hexdigest() != metadata.get("sha256")
            ):
                raise FullAgentArtifactError(
                    "artifact_integrity_failed", "Artifact integrity check failed.", status=409
                )
            media_type, kind = _validate_payload(path, payload, suffix)
            if (
                metadata.get("mediaType") != media_type
                or metadata.get("kind") != kind
                or metadata.get("direction") not in {"input", "output"}
            ):
                raise FullAgentArtifactError(
                    "artifact_integrity_failed", "Artifact metadata integrity failed.", status=409
                )
            return path, metadata

    def model_input_path(
        self,
        thread_id: object,
        turn_id: object,
        artifact_id: object,
    ) -> Path:
        path, metadata = self.resolve(thread_id, turn_id, artifact_id)
        if metadata.get("direction") != "input" or metadata.get("modelInputReady") is not True:
            raise FullAgentArtifactError(
                "artifact_not_model_input", "Artifact cannot be used as model image input."
            )
        return path

    def consume_input(
        self,
        thread_id: object,
        turn_id: object,
        artifact_id: object,
    ) -> dict[str, Any]:
        """Durably tombstone a one-shot upload after it is rebound to a Turn.

        The consumed metadata remains until its normal TTL so a process restart
        cannot make the draft reusable.  The payload is removed only after the
        tombstone has been atomically committed.
        """

        return self.consume_inputs(((thread_id, turn_id, artifact_id),))[0]

    def consume_inputs(
        self,
        bindings: Sequence[tuple[object, object, object]],
    ) -> list[dict[str, Any]]:
        """Consume a validated draft batch without a reusable partial prefix."""

        normalized = [
            (
                _safe_id(thread_id, "threadId"),
                _safe_id(turn_id, "turnId"),
                _safe_id(artifact_id, "artifactId"),
            )
            for thread_id, turn_id, artifact_id in bindings
        ]
        if len({artifact_id for _thread, _turn, artifact_id in normalized}) != len(
            normalized
        ):
            raise FullAgentArtifactError(
                "invalid_request", "Attachment batch contains duplicates.", status=422
            )
        with self._lock:
            originals: list[tuple[dict[str, Any], Path]] = []
            for thread, turn, artifact_id in normalized:
                metadata = self._load_metadata(artifact_id)
                self._assert_owner(metadata, thread, turn, code="artifact_not_found")
                if metadata.get("direction") != "input":
                    raise FullAgentArtifactError(
                        "artifact_not_found", "Artifact was not found.", status=404
                    )
                if self._now() >= _epoch_from_utc(metadata.get("expiresAt")):
                    self._delete_artifact(metadata)
                    raise FullAgentArtifactError(
                        "artifact_expired", "Artifact expired.", status=410
                    )
                path = self.root / f"{metadata['id']}{metadata['suffix']}"
                if (
                    not path.is_file()
                    or _is_link(path)
                    or path.parent.resolve() != self.root
                ):
                    raise FullAgentArtifactError(
                        "artifact_not_found", "Artifact file is unavailable.", status=404
                    )
                originals.append((metadata, path))

            consumed_at = _utc_from_epoch(self._now())
            written: list[dict[str, Any]] = []
            try:
                for metadata, _path in originals:
                    tombstone = {
                        **metadata,
                        "state": "consumed",
                        "modelInputReady": False,
                        "consumedAt": consumed_at,
                    }
                    self._write_metadata(tombstone)
                    written.append(metadata)
            except Exception as error:
                restore_failed = False
                for metadata in written:
                    try:
                        self._write_metadata(metadata)
                    except Exception:
                        restore_failed = True
                raise FullAgentArtifactError(
                    "artifact_cleanup_failed",
                    (
                        "Attachment batch could not be consumed safely."
                        if not restore_failed
                        else "Attachment batch entered a fail-closed recovery state."
                    ),
                    status=500,
                ) from error

            cleanup_complete = True
            for _metadata, path in originals:
                try:
                    path.unlink()
                except OSError:
                    # Every metadata record is already a durable tombstone, so
                    # an orphaned payload cannot be resolved or downloaded.
                    cleanup_complete = False
            self._fsync_directory(self.root)
            return [
                {
                    "id": str(metadata["id"]),
                    "threadId": str(metadata["threadId"]),
                    "turnId": str(metadata["turnId"]),
                    "consumedAt": consumed_at,
                    "state": "consumed",
                    "payloadCleanupComplete": cleanup_complete,
                }
                for metadata, _path in originals
            ]

    def revoke_artifact(
        self,
        thread_id: object,
        turn_id: object,
        artifact_id: object,
        *,
        direction: str,
    ) -> None:
        """Fail closed and remove an unpublished artifact during rollback."""

        thread = _safe_id(thread_id, "threadId")
        turn = _safe_id(turn_id, "turnId")
        with self._lock:
            metadata = self._load_metadata(artifact_id)
            self._assert_owner(metadata, thread, turn, code="artifact_not_found")
            if metadata.get("direction") != direction:
                raise FullAgentArtifactError(
                    "artifact_not_found", "Artifact was not found.", status=404
                )
            tombstone = {
                **metadata,
                "state": "revoked",
                "modelInputReady": False,
                "revokedAt": _utc_from_epoch(self._now()),
            }
            self._write_metadata(tombstone)
            path = self.root / f"{metadata['id']}{metadata['suffix']}"
            try:
                if path.exists():
                    path.unlink()
                self._metadata_path(str(metadata["id"])).unlink()
                self._fsync_directory(self.root)
            except OSError as error:
                raise FullAgentArtifactError(
                    "artifact_cleanup_failed",
                    "Rolled-back artifact could not be removed completely.",
                    status=500,
                ) from error

    def download_metadata(
        self,
        thread_id: object,
        turn_id: object,
        artifact_id: object,
    ) -> dict[str, Any]:
        _path, metadata = self.resolve(thread_id, turn_id, artifact_id)
        name = str(metadata["name"])
        ascii_name = name.encode("ascii", errors="ignore").decode("ascii")
        ascii_name = ascii_name.replace('"', "_") or f"download{metadata['suffix']}"
        encoded_name = urllib.parse.quote(name, safe="")
        return {
            "artifact": self.read_model(metadata),
            "downloadName": name,
            "contentType": metadata["mediaType"],
            "contentLength": metadata["byteSize"],
            "contentDisposition": (
                f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded_name}'
            ),
            "cacheControl": "private, no-store",
            "contentTypeOptions": "nosniff",
        }

    def _delete_artifact(self, metadata: Mapping[str, Any]) -> None:
        suffix = str(metadata.get("suffix") or "")
        if suffix not in _TYPE_BY_SUFFIX:
            return
        try:
            artifact_id = _safe_id(metadata.get("id"), "artifactId")
        except FullAgentArtifactError:
            return
        with contextlib.suppress(OSError):
            (self.root / f"{artifact_id}{suffix}").unlink()
        with contextlib.suppress(OSError):
            self._metadata_path(artifact_id).unlink()

    def cleanup_expired(self) -> dict[str, int]:
        """Delete expired ready, staged, and quarantined records."""

        now = self._now()
        removed = {"artifacts": 0, "stages": 0, "quarantine": 0}
        with self._lock:
            for path in list(self.root.glob("*.meta.json")):
                try:
                    metadata = self._read_json(path, code="artifact_not_found")
                    if now < _epoch_from_utc(metadata.get("expiresAt")):
                        continue
                    self._delete_artifact(metadata)
                    with contextlib.suppress(OSError):
                        path.unlink()
                    removed["artifacts"] += 1
                except FullAgentArtifactError:
                    continue
            for path in list(self.staging_root.glob("*.meta.json")):
                try:
                    metadata = self._read_json(path, code="stage_not_found")
                    if now < _epoch_from_utc(metadata.get("expiresAt")):
                        continue
                    self._quarantine_stage(metadata, "stage_expired")
                    with contextlib.suppress(OSError):
                        path.unlink()
                    removed["stages"] += 1
                except FullAgentArtifactError:
                    continue
            for path in list(self.quarantine_root.glob("*.meta.json")):
                try:
                    metadata = self._read_json(path, code="artifact_not_found")
                    if now < _epoch_from_utc(metadata.get("expiresAt")):
                        continue
                    stored_name = metadata.get("storedName")
                    if isinstance(stored_name, str) and Path(stored_name).name == stored_name:
                        with contextlib.suppress(OSError):
                            (self.quarantine_root / stored_name).unlink()
                    path.unlink()
                    removed["quarantine"] += 1
                except (FullAgentArtifactError, OSError):
                    continue
        return removed

    def quarantine_summary(self) -> dict[str, int]:
        with self._lock:
            count = sum(
                1
                for path in self.quarantine_root.glob("*.meta.json")
                if path.is_file() and not _is_link(path)
            )
        return {"count": count}

    @staticmethod
    def read_model(metadata: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": str(metadata.get("id") or ""),
            "name": str(metadata.get("name") or ""),
            "mediaType": str(metadata.get("mediaType") or "application/octet-stream"),
            "kind": str(metadata.get("kind") or "file"),
            "byteSize": int(metadata.get("byteSize") or 0),
            "sha256": str(metadata.get("sha256") or ""),
            "direction": str(metadata.get("direction") or "input"),
            "modelInputReady": bool(metadata.get("modelInputReady")),
            "createdAt": metadata.get("createdAt"),
            "finalizedAt": metadata.get("finalizedAt"),
            "expiresAt": metadata.get("expiresAt"),
        }


__all__ = [
    "FullAgentArtifactError",
    "FullAgentArtifactStore",
    "MAX_ATTACHMENTS_PER_TURN",
    "MAX_OUTPUT_BYTES",
    "MAX_UPLOAD_BYTES",
    "MAX_UPLOAD_REQUEST_BYTES",
]
