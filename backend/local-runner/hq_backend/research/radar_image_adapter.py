"""Fail-closed publisher image capture for the read-only Radar workflow.

The adapter deliberately does not render pages or execute publisher code.  It
fetches a public HTTPS document, discovers a publisher-declared Open Graph (or
Twitter) image, validates the image bytes, and stores a content-addressed copy.

Network access is isolated behind ``request_once`` and ``resolver`` callables so
the policy can be tested without a live network.  The default requester pins a
public IP selected from the validated DNS answer while retaining the original
hostname for TLS SNI and certificate verification.  Every redirect is resolved
and validated again before it is followed.
"""

from __future__ import annotations

import copy
import binascii
import hashlib
import hmac
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping, Sequence
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit


SCHEMA_VERSION = "radar-publisher-image-v1"
CAPTURE_KIND = "publisher_open_graph"
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_IMAGE_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})
_IMAGE_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
_HTML_TYPES = frozenset({"text/html", "application/xhtml+xml"})
_SENSITIVE_QUERY_KEY = re.compile(
    r"(?:^|[_-])(?:api[_-]?key|auth(?:orization)?|cookie|credential|pass(?:word|wd)?|secret|session|sig(?:nature)?|token)(?:$|[_-])",
    re.IGNORECASE,
)
_ENCODED_CONTROL = re.compile(r"%(?:0[0-9a-f]|1[0-9a-f]|7f)", re.IGNORECASE)
_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9a-f]{2})", re.IGNORECASE)
_JPEG_SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)
_SAFE_RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
_DESCRIPTOR_BINDING_FIELDS = (
    "schemaVersion",
    "captureKind",
    "sourceRecordId",
    "sourceUrl",
    "finalSourceUrl",
    "sourceCheckedAt",
    "sourceFetchedAt",
    "sourceDocumentSha256",
    "publisherImageSelector",
    "publisherImageUrl",
    "finalPublisherImageUrl",
    "capturedAt",
    "storageRef",
    "sha256",
    "mimeType",
    "byteSize",
    "width",
    "height",
)


class RadarImageError(RuntimeError):
    """Expected, externally safe capture failure identified by a stable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CaptureLimits:
    max_url_chars: int = 2048
    max_redirects: int = 3
    max_html_bytes: int = 1_000_000
    max_image_bytes: int = 5_000_000
    timeout_seconds: float = 10.0
    max_resolved_addresses: int = 8
    min_width: int = 200
    min_height: int = 100
    max_width: int = 4096
    max_height: int = 4096
    max_pixels: int = 12_000_000


DEFAULT_LIMITS = CaptureLimits()


@dataclass(frozen=True)
class HttpsTarget:
    normalized_url: str
    hostname: str
    port: int
    path_and_query: str
    host_header: str
    addresses: tuple[str, ...]


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class FetchedResource:
    requested_url: str
    final_url: str
    headers: Mapping[str, str]
    body: bytes
    redirect_count: int


@dataclass(frozen=True)
class CaptureOutcome:
    ok: bool
    reason_code: str
    descriptor: dict[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "reasonCode": self.reason_code,
            "descriptor": self.descriptor,
        }


@dataclass(frozen=True)
class ReportEnrichmentOutcome:
    report: dict[str, object]
    attached_count: int
    diagnostics: tuple[dict[str, object], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "report": self.report,
            "attachedCount": self.attached_count,
            "diagnostics": list(self.diagnostics),
        }


Resolver = Callable[[str, int], Sequence[str]]
RequestOnce = Callable[[HttpsTarget, Mapping[str, str], int, float], HttpResponse]
Clock = Callable[[], datetime]
CaptureEntry = Callable[[dict[str, object]], CaptureOutcome]
ArtifactLoader = Callable[[dict[str, object]], bytes]


def _default_resolver(hostname: str, port: int) -> Sequence[str]:
    try:
        answers = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise RadarImageError("dns_resolution_failed") from exc
    return tuple(answer[4][0] for answer in answers if answer and answer[4])


def _is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value.split("%", 1)[0])
        return bool(
            address.is_global
            and not address.is_multicast
            and not address.is_unspecified
            and not address.is_reserved
            and not address.is_loopback
            and not address.is_link_local
            and not address.is_private
        )
    except ValueError:
        return False


def _normalize_https_url(value: object, limits: CaptureLimits) -> tuple[str, str, int, str, str]:
    if not isinstance(value, str):
        raise RadarImageError("invalid_url")
    candidate = value.strip()
    if not candidate or len(candidate) > limits.max_url_chars:
        raise RadarImageError("invalid_url")
    if any(ord(char) < 0x20 or ord(char) == 0x7F or char.isspace() for char in candidate):
        raise RadarImageError("invalid_url")
    if "\\" in candidate or _ENCODED_CONTROL.search(candidate) or _INVALID_PERCENT_ESCAPE.search(candidate):
        raise RadarImageError("invalid_url")

    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise RadarImageError("invalid_url") from exc
    if parsed.scheme.lower() != "https":
        raise RadarImageError("https_required")
    if parsed.username is not None or parsed.password is not None:
        raise RadarImageError("embedded_credentials_rejected")
    if parsed.fragment:
        raise RadarImageError("url_fragment_rejected")
    if not parsed.hostname:
        raise RadarImageError("invalid_url")
    if port not in (None, 443):
        raise RadarImageError("https_port_rejected")

    raw_hostname = parsed.hostname.rstrip(".")
    if raw_hostname != parsed.hostname or not raw_hostname:
        raise RadarImageError("invalid_hostname")
    try:
        hostname = raw_hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise RadarImageError("invalid_hostname") from exc
    if len(hostname) > 253 or any(len(label) > 63 or not label for label in hostname.split(".")):
        raise RadarImageError("invalid_hostname")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        if any(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) is None
            for label in hostname.split(".")
        ):
            raise RadarImageError("invalid_hostname")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal", ".lan")):
        raise RadarImageError("private_host_rejected")

    try:
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=False)
    except ValueError as exc:
        raise RadarImageError("invalid_url") from exc
    if any(_SENSITIVE_QUERY_KEY.search(key) for key, _value in query_pairs):
        raise RadarImageError("sensitive_query_rejected")

    path = parsed.path or "/"
    if not path.startswith("/"):
        raise RadarImageError("invalid_url")
    is_ipv6 = ":" in hostname
    authority = f"[{hostname}]" if is_ipv6 else hostname
    normalized = urlunsplit(("https", authority, path, parsed.query, ""))
    if len(normalized) > limits.max_url_chars:
        raise RadarImageError("invalid_url")
    path_and_query = path + (f"?{parsed.query}" if parsed.query else "")
    host_header = authority
    return normalized, hostname, 443, path_and_query, host_header


def _validated_target(value: object, limits: CaptureLimits, resolver: Resolver) -> HttpsTarget:
    normalized, hostname, port, path_and_query, host_header = _normalize_https_url(value, limits)
    try:
        resolved = resolver(hostname, port)
    except RadarImageError:
        raise
    except Exception as exc:
        raise RadarImageError("dns_resolution_failed") from exc
    addresses = tuple(sorted({str(address).split("%", 1)[0] for address in resolved if address}))
    if not addresses:
        raise RadarImageError("dns_resolution_failed")
    if len(addresses) > limits.max_resolved_addresses:
        raise RadarImageError("dns_answer_too_large")
    if not all(_is_public_ip(address) for address in addresses):
        raise RadarImageError("non_public_address_rejected")
    return HttpsTarget(
        normalized_url=normalized,
        hostname=hostname,
        port=port,
        path_and_query=path_and_query,
        host_header=host_header,
        addresses=addresses,
    )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection whose TCP endpoint is a prevalidated literal IP."""

    def __init__(self, hostname: str, pinned_ip: str, timeout: float) -> None:
        super().__init__(
            hostname,
            port=443,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self._pinned_ip = pinned_ip

    def connect(self) -> None:
        if self._tunnel_host:
            raise RadarImageError("proxy_tunnel_rejected")
        raw_socket = self._create_connection(
            (self._pinned_ip, self.port),
            self.timeout,
            self.source_address,
        )
        try:
            self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
        except Exception:
            raw_socket.close()
            raise


def _read_bounded(response: http.client.HTTPResponse, max_bytes: int) -> bytes:
    content_length = response.getheader("Content-Length")
    if content_length is not None:
        try:
            declared = int(content_length, 10)
        except ValueError as exc:
            raise RadarImageError("invalid_content_length") from exc
        if declared < 0 or declared > max_bytes:
            raise RadarImageError("response_too_large")

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(min(64 * 1024, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise RadarImageError("response_too_large")
    return b"".join(chunks)


def _default_request_once(
    target: HttpsTarget,
    headers: Mapping[str, str],
    max_bytes: int,
    timeout_seconds: float,
) -> HttpResponse:
    last_error: Exception | None = None
    for address in target.addresses:
        connection = _PinnedHTTPSConnection(target.hostname, address, timeout_seconds)
        try:
            connection.putrequest(
                "GET",
                target.path_and_query,
                skip_host=True,
                skip_accept_encoding=True,
            )
            connection.putheader("Host", target.host_header)
            for name, value in headers.items():
                connection.putheader(name, value)
            connection.endheaders()
            response = connection.getresponse()
            response_headers: dict[str, str] = {}
            for name in {name for name, _value in response.getheaders()}:
                values = response.headers.get_all(name, failobj=[])
                response_headers[name] = ",".join(values)
            body = b"" if response.status in _REDIRECT_STATUSES else _read_bounded(response, max_bytes)
            return HttpResponse(status=response.status, headers=response_headers, body=body)
        except RadarImageError:
            raise
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            last_error = exc
        finally:
            connection.close()
    raise RadarImageError("https_request_failed") from last_error


def _header(headers: Mapping[str, str], name: str) -> str | None:
    wanted = name.casefold()
    matches = [str(value).strip() for key, value in headers.items() if str(key).casefold() == wanted]
    if len(matches) > 1:
        raise RadarImageError("ambiguous_response_header")
    if not matches:
        return None
    return matches[0]


def fetch_https_resource(
    url: object,
    *,
    accept: str,
    max_bytes: int,
    limits: CaptureLimits = DEFAULT_LIMITS,
    resolver: Resolver = _default_resolver,
    request_once: RequestOnce = _default_request_once,
) -> FetchedResource:
    """Fetch one bounded HTTPS resource after validating every redirect hop."""

    if max_bytes < 1:
        raise RadarImageError("invalid_size_limit")
    initial_normalized = _normalize_https_url(url, limits)[0]
    current_url = initial_normalized
    seen: set[str] = set()
    headers = {
        "Accept": accept,
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
        "User-Agent": "Metafxclub-Radar-Evidence/1.0",
    }

    for redirect_count in range(limits.max_redirects + 1):
        target = _validated_target(current_url, limits, resolver)
        if target.normalized_url in seen:
            raise RadarImageError("redirect_loop")
        seen.add(target.normalized_url)
        try:
            response = request_once(target, headers, max_bytes, limits.timeout_seconds)
        except RadarImageError:
            raise
        except Exception as exc:
            raise RadarImageError("https_request_failed") from exc
        if not isinstance(response, HttpResponse) or not isinstance(response.body, bytes):
            raise RadarImageError("invalid_transport_response")
        if len(response.body) > max_bytes:
            raise RadarImageError("response_too_large")

        content_encoding = _header(response.headers, "Content-Encoding")
        if content_encoding and content_encoding.casefold() != "identity":
            raise RadarImageError("encoded_response_rejected")
        declared_length = _header(response.headers, "Content-Length")
        if declared_length is not None:
            try:
                declared_size = int(declared_length, 10)
            except ValueError as exc:
                raise RadarImageError("invalid_content_length") from exc
            if declared_size < 0 or declared_size > max_bytes:
                raise RadarImageError("response_too_large")
            if response.status == 200 and declared_size != len(response.body):
                raise RadarImageError("content_length_mismatch")

        if response.status in _REDIRECT_STATUSES:
            if redirect_count >= limits.max_redirects:
                raise RadarImageError("redirect_limit_exceeded")
            location = _header(response.headers, "Location")
            if not location or "," in location:
                raise RadarImageError("invalid_redirect")
            next_url = urljoin(target.normalized_url, location.strip())
            current_url = _normalize_https_url(next_url, limits)[0]
            continue
        if response.status != 200:
            raise RadarImageError("http_status_rejected")
        return FetchedResource(
            requested_url=initial_normalized,
            final_url=target.normalized_url,
            headers=dict(response.headers),
            body=response.body,
            redirect_count=redirect_count,
        )
    raise RadarImageError("redirect_limit_exceeded")


class _PublisherImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.candidates: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.casefold(): value for name, value in attrs if value is not None}
        if tag.casefold() == "meta":
            key = (values.get("property") or values.get("name") or "").strip().casefold()
            content = (values.get("content") or "").strip()
            if key in {"og:image:secure_url", "og:image", "twitter:image", "twitter:image:src"} and content:
                candidates = self.candidates.setdefault(key, [])
                if len(candidates) < 8:
                    candidates.append(content)
        elif tag.casefold() == "link":
            rel_tokens = {token.casefold() for token in (values.get("rel") or "").split()}
            href = (values.get("href") or "").strip()
            if "image_src" in rel_tokens and href:
                candidates = self.candidates.setdefault("image_src", [])
                if len(candidates) < 8:
                    candidates.append(href)


def discover_publisher_image_url(html_bytes: bytes, document_url: str, limits: CaptureLimits = DEFAULT_LIMITS) -> tuple[str, str]:
    """Return ``(absolute_image_url, selector)`` from publisher metadata."""

    if not isinstance(html_bytes, bytes) or len(html_bytes) > limits.max_html_bytes:
        raise RadarImageError("invalid_html_body")
    parser = _PublisherImageParser()
    try:
        parser.feed(html_bytes.decode("utf-8", errors="replace"))
        parser.close()
    except Exception as exc:
        raise RadarImageError("invalid_html_body") from exc

    for selector in ("og:image:secure_url", "og:image", "twitter:image", "twitter:image:src", "image_src"):
        for candidate in parser.candidates.get(selector, []):
            joined = urljoin(document_url, candidate)
            try:
                normalized = _normalize_https_url(joined, limits)[0]
            except RadarImageError:
                continue
            return normalized, selector
    raise RadarImageError("publisher_image_not_found")


def _media_type(headers: Mapping[str, str]) -> str:
    value = _header(headers, "Content-Type")
    if not value:
        raise RadarImageError("content_type_required")
    return value.split(";", 1)[0].strip().casefold()


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 57 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    offset = 8
    dimensions: tuple[int, int] | None = None
    color_type: int | None = None
    saw_palette = False
    saw_image_data = False
    image_data_ended = False
    allowed_critical = {b"IHDR", b"PLTE", b"IDAT", b"IEND"}
    while offset < len(data):
        if offset + 12 > len(data):
            return None
        chunk_size = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + chunk_size
        chunk_end = payload_end + 4
        if payload_end < payload_start or chunk_end > len(data):
            return None
        expected_crc = struct.unpack(">I", data[payload_end:chunk_end])[0]
        actual_crc = binascii.crc32(chunk_type + data[payload_start:payload_end]) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            return None
        if not chunk_type.isalpha() or len(chunk_type) != 4:
            return None
        if chunk_type[0] & 0x20 == 0 and chunk_type not in allowed_critical:
            return None

        if dimensions is None and chunk_type != b"IHDR":
            return None
        if chunk_type == b"IHDR":
            if dimensions is not None or chunk_size != 13:
                return None
            width, height, bit_depth, color_type_value, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB",
                data[payload_start:payload_end],
            )
            allowed_depths = {
                0: {1, 2, 4, 8, 16},
                2: {8, 16},
                3: {1, 2, 4, 8},
                4: {8, 16},
                6: {8, 16},
            }
            if (
                width == 0
                or height == 0
                or color_type_value not in allowed_depths
                or bit_depth not in allowed_depths[color_type_value]
                or compression != 0
                or filtering != 0
                or interlace not in {0, 1}
            ):
                return None
            dimensions = (width, height)
            color_type = color_type_value
        elif chunk_type == b"PLTE":
            if saw_image_data or saw_palette or chunk_size == 0 or chunk_size % 3 or chunk_size > 768:
                return None
            saw_palette = True
        elif chunk_type == b"IDAT":
            if image_data_ended or (color_type == 3 and not saw_palette):
                return None
            saw_image_data = True
        elif chunk_type == b"IEND":
            if chunk_size != 0 or not saw_image_data or chunk_end != len(data):
                return None
            return dimensions
        elif saw_image_data:
            image_data_ended = True
        offset = chunk_end
    return None


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 18 or data[:2] != b"\xff\xd8" or data[-2:] != b"\xff\xd9":
        return None
    offset = 2
    dimensions: tuple[int, int] | None = None
    while offset < len(data) - 2:
        if data[offset] != 0xFF:
            return None
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            return None
        marker = data[offset]
        offset += 1
        if marker in {0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if marker in {0xD8, 0xD9} or offset + 2 > len(data) - 2:
            return None
        segment_length = struct.unpack(">H", data[offset : offset + 2])[0]
        if segment_length < 2 or offset + segment_length > len(data) - 2:
            return None
        if marker == 0xDA:
            if dimensions is None or segment_length < 6:
                return None
            component_count = data[offset + 2]
            if component_count == 0 or segment_length != 6 + 2 * component_count:
                return None
            return dimensions
        if marker in _JPEG_SOF_MARKERS:
            if dimensions is not None or segment_length < 11:
                return None
            component_count = data[offset + 7]
            if component_count == 0 or segment_length != 8 + 3 * component_count:
                return None
            height = struct.unpack(">H", data[offset + 3 : offset + 5])[0]
            width = struct.unpack(">H", data[offset + 5 : offset + 7])[0]
            if width == 0 or height == 0:
                return None
            dimensions = (width, height)
        offset += segment_length
    return None


def _webp_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 20 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    declared_size = struct.unpack("<I", data[4:8])[0] + 8
    if declared_size != len(data):
        return None
    offset = 12
    dimensions: tuple[int, int] | None = None
    saw_extended_header = False
    saw_image_payload = False
    while offset < len(data):
        if offset + 8 > len(data):
            return None
        chunk = data[offset : offset + 4]
        chunk_size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
        payload = offset + 8
        payload_end = payload + chunk_size
        padded_end = payload_end + (chunk_size & 1)
        if payload_end < payload or padded_end > len(data):
            return None
        if chunk_size & 1 and data[payload_end:padded_end] != b"\x00":
            return None
        if chunk == b"VP8X":
            if offset != 12 or saw_extended_header or chunk_size != 10:
                return None
            flags = data[payload]
            if flags & 0xC1 or data[payload + 1 : payload + 4] != b"\x00\x00\x00":
                return None
            dimensions = (
                int.from_bytes(data[payload + 4 : payload + 7], "little") + 1,
                int.from_bytes(data[payload + 7 : payload + 10], "little") + 1,
            )
            saw_extended_header = True
        elif chunk == b"VP8 ":
            if chunk_size < 10 or data[payload + 3 : payload + 6] != b"\x9d\x01\x2a":
                return None
            frame_dimensions = (
                struct.unpack("<H", data[payload + 6 : payload + 8])[0] & 0x3FFF,
                struct.unpack("<H", data[payload + 8 : payload + 10])[0] & 0x3FFF,
            )
            if not saw_extended_header:
                dimensions = frame_dimensions
            saw_image_payload = True
        elif chunk == b"VP8L":
            if chunk_size < 5 or data[payload] != 0x2F:
                return None
            bits = int.from_bytes(data[payload + 1 : payload + 5], "little")
            frame_dimensions = ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
            if not saw_extended_header:
                dimensions = frame_dimensions
            saw_image_payload = True
        elif chunk == b"ANMF":
            if not saw_extended_header or chunk_size < 16:
                return None
            saw_image_payload = True
        offset = padded_end
    return dimensions if offset == len(data) and saw_image_payload else None


def validate_image_bytes(
    data: bytes,
    declared_media_type: str,
    limits: CaptureLimits = DEFAULT_LIMITS,
) -> tuple[str, str, int, int]:
    """Validate magic and dimensions; return ``(mime, extension, width, height)``."""

    if not isinstance(data, bytes) or not data or len(data) > limits.max_image_bytes:
        raise RadarImageError("invalid_image_body")
    if declared_media_type not in _IMAGE_TYPES:
        raise RadarImageError("image_content_type_rejected")

    detected: tuple[str, str, tuple[int, int] | None]
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        detected = ("image/png", "png", _png_dimensions(data))
    elif data.startswith(b"\xff\xd8"):
        detected = ("image/jpeg", "jpg", _jpeg_dimensions(data))
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        detected = ("image/webp", "webp", _webp_dimensions(data))
    else:
        raise RadarImageError("image_magic_rejected")
    mime_type, extension, dimensions = detected
    if mime_type != declared_media_type:
        raise RadarImageError("image_type_mismatch")
    if dimensions is None:
        raise RadarImageError("image_dimensions_invalid")
    width, height = dimensions
    if (
        width < limits.min_width
        or height < limits.min_height
        or width > limits.max_width
        or height > limits.max_height
        or width * height > limits.max_pixels
    ):
        raise RadarImageError("image_dimensions_rejected")
    return mime_type, extension, width, height


def _as_aware_datetime(value: object, error_code: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise RadarImageError(error_code) from exc
    else:
        raise RadarImageError(error_code)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RadarImageError(error_code)
    return parsed.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _source_record_id(value: object, *, optional: bool) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise RadarImageError("invalid_source_record_id")
    candidate = value.strip()
    if not _SAFE_RECORD_ID.fullmatch(candidate):
        raise RadarImageError("invalid_source_record_id")
    return candidate


def _descriptor_evidence_sha256(descriptor: Mapping[str, object]) -> str:
    try:
        binding_fields = {key: descriptor[key] for key in _DESCRIPTOR_BINDING_FIELDS}
        serialized = json.dumps(
            binding_fields,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (KeyError, TypeError, ValueError) as exc:
        raise RadarImageError("invalid_artifact_descriptor") from exc
    return hashlib.sha256(serialized).hexdigest()


def _safe_storage_prefix(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise RadarImageError("invalid_storage_prefix")
    raw = value.strip()
    if raw.startswith("/"):
        raise RadarImageError("invalid_storage_prefix")
    path = PurePosixPath(raw.rstrip("/"))
    if (
        path.is_absolute()
        or not path.parts
        or any(
            part in {"", ".", ".."} or re.fullmatch(r"[A-Za-z0-9._-]+", part) is None
            for part in path.parts
        )
    ):
        raise RadarImageError("invalid_storage_prefix")
    return path.as_posix()


def _store_content_addressed(output_dir: Path, filename: str, data: bytes) -> Path:
    try:
        directory = Path(output_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
    except (OSError, RuntimeError) as exc:
        raise RadarImageError("storage_unavailable") from exc
    destination = directory / filename
    if destination.parent != directory or destination.is_symlink():
        raise RadarImageError("storage_path_rejected")
    try:
        descriptor = os.open(str(destination), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            if destination.stat().st_size != len(data):
                raise RadarImageError("storage_collision")
            with destination.open("rb") as handle:
                existing = handle.read(len(data) + 1)
        except RadarImageError:
            raise
        except OSError as exc:
            raise RadarImageError("storage_collision") from exc
        if existing != data:
            raise RadarImageError("storage_collision")
        return destination
    except OSError as exc:
        raise RadarImageError("storage_write_failed") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception as exc:
        try:
            destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise RadarImageError("storage_write_failed") from exc
    return destination


def capture_publisher_og_image(
    source_url: object,
    *,
    checked_at: object,
    output_dir: Path,
    source_record_id: object | None = None,
    storage_prefix: str = "data/memory/screenshots/radar",
    limits: CaptureLimits = DEFAULT_LIMITS,
    resolver: Resolver = _default_resolver,
    request_once: RequestOnce = _default_request_once,
    clock: Clock = lambda: datetime.now(timezone.utc),
) -> CaptureOutcome:
    """Capture a publisher metadata image and return a bound evidence descriptor.

    Ordinary policy, transport, parsing, and storage failures are converted to a
    stable ``CaptureOutcome``.  No partial descriptor is returned on failure.
    """

    try:
        checked = _as_aware_datetime(checked_at, "invalid_checked_at")
        fetch_started = _as_aware_datetime(clock(), "invalid_capture_time")
        if checked > fetch_started + timedelta(minutes=5):
            raise RadarImageError("invalid_checked_at")
        record_id = _source_record_id(source_record_id, optional=True)
        prefix = _safe_storage_prefix(storage_prefix)
        source = fetch_https_resource(
            source_url,
            accept="text/html,application/xhtml+xml;q=0.9",
            max_bytes=limits.max_html_bytes,
            limits=limits,
            resolver=resolver,
            request_once=request_once,
        )
        source_type = _media_type(source.headers)
        if source_type not in _HTML_TYPES:
            raise RadarImageError("html_content_type_rejected")
        image_url, selector = discover_publisher_image_url(source.body, source.final_url, limits)
        image = fetch_https_resource(
            image_url,
            accept="image/png,image/jpeg,image/webp",
            max_bytes=limits.max_image_bytes,
            limits=limits,
            resolver=resolver,
            request_once=request_once,
        )
        image_type = _media_type(image.headers)
        mime_type, extension, width, height = validate_image_bytes(image.body, image_type, limits)
        captured = _as_aware_datetime(clock(), "invalid_capture_time")
        if captured < fetch_started:
            raise RadarImageError("invalid_capture_time")

        source_hash = hashlib.sha256(source.body).hexdigest()
        image_hash = hashlib.sha256(image.body).hexdigest()
        filename = f"{image_hash}.{extension}"
        _store_content_addressed(Path(output_dir), filename, image.body)
        storage_ref = f"{prefix}/{filename}"

        descriptor: dict[str, object] = {
            "schemaVersion": SCHEMA_VERSION,
            "captureKind": CAPTURE_KIND,
            "sourceRecordId": record_id,
            "sourceUrl": source.requested_url,
            "finalSourceUrl": source.final_url,
            "sourceCheckedAt": _iso_z(checked),
            "sourceFetchedAt": _iso_z(fetch_started),
            "sourceDocumentSha256": source_hash,
            "publisherImageSelector": selector,
            "publisherImageUrl": image.requested_url,
            "finalPublisherImageUrl": image.final_url,
            "capturedAt": _iso_z(captured),
            "storageRef": storage_ref,
            "sha256": image_hash,
            "mimeType": mime_type,
            "byteSize": len(image.body),
            "width": width,
            "height": height,
        }
        descriptor["evidenceSha256"] = _descriptor_evidence_sha256(descriptor)
        return CaptureOutcome(ok=True, reason_code="captured", descriptor=descriptor)
    except RadarImageError as exc:
        return CaptureOutcome(ok=False, reason_code=exc.code, descriptor=None)
    except Exception:
        return CaptureOutcome(ok=False, reason_code="internal_error", descriptor=None)


def _prevalidate_radar_entry_descriptor(
    entry: object,
    descriptor: object,
    limits: CaptureLimits,
) -> tuple[str, str, int, int, int]:
    """Validate all descriptor fields before a caller is allowed to resolve its path."""

    if not isinstance(entry, dict):
        raise RadarImageError("invalid_radar_entry")
    if not isinstance(descriptor, dict):
        raise RadarImageError("invalid_artifact_descriptor")
    allowed_fields = set(_DESCRIPTOR_BINDING_FIELDS) | {"evidenceSha256"}
    if set(descriptor) != allowed_fields:
        raise RadarImageError("invalid_artifact_descriptor")

    entry_record_id = _source_record_id(entry.get("recordId"), optional=False)
    descriptor_record_id = _source_record_id(descriptor.get("sourceRecordId"), optional=False)
    if descriptor_record_id != entry_record_id:
        raise RadarImageError("source_record_mismatch")

    entry_source_url = entry.get("sourceUrl")
    descriptor_source_url = descriptor.get("sourceUrl")
    if not isinstance(entry_source_url, str) or entry_source_url != entry_source_url.strip():
        raise RadarImageError("invalid_entry_source_url")
    if not isinstance(descriptor_source_url, str):
        raise RadarImageError("invalid_artifact_descriptor")
    if descriptor_source_url != entry_source_url:
        raise RadarImageError("source_url_mismatch")
    _normalize_https_url(entry_source_url, limits)

    if descriptor.get("schemaVersion") != SCHEMA_VERSION or descriptor.get("captureKind") != CAPTURE_KIND:
        raise RadarImageError("invalid_artifact_descriptor")
    for url_field in ("finalSourceUrl", "publisherImageUrl", "finalPublisherImageUrl"):
        if not isinstance(descriptor.get(url_field), str):
            raise RadarImageError("invalid_artifact_descriptor")
        _normalize_https_url(descriptor[url_field], limits)
    if descriptor.get("publisherImageSelector") not in {
        "og:image:secure_url",
        "og:image",
        "twitter:image",
        "twitter:image:src",
        "image_src",
    }:
        raise RadarImageError("invalid_artifact_descriptor")

    entry_checked_at = _as_aware_datetime(entry.get("checkedAt"), "invalid_entry_checked_at")
    descriptor_checked_at = _as_aware_datetime(
        descriptor.get("sourceCheckedAt"),
        "invalid_artifact_descriptor",
    )
    if descriptor_checked_at != entry_checked_at:
        raise RadarImageError("source_checked_at_mismatch")
    source_fetched_at = _as_aware_datetime(
        descriptor.get("sourceFetchedAt"),
        "invalid_artifact_descriptor",
    )
    captured_at = _as_aware_datetime(
        descriptor.get("capturedAt"),
        "invalid_artifact_descriptor",
    )
    if descriptor_checked_at > source_fetched_at + timedelta(minutes=5) or captured_at < source_fetched_at:
        raise RadarImageError("invalid_artifact_descriptor")

    source_hash = descriptor.get("sourceDocumentSha256")
    image_hash = descriptor.get("sha256")
    evidence_hash = descriptor.get("evidenceSha256")
    if not isinstance(source_hash, str) or re.fullmatch(r"[0-9a-f]{64}", source_hash) is None:
        raise RadarImageError("invalid_artifact_descriptor")
    if not isinstance(image_hash, str) or re.fullmatch(r"[0-9a-f]{64}", image_hash) is None:
        raise RadarImageError("invalid_artifact_descriptor")
    if not isinstance(evidence_hash, str) or re.fullmatch(r"[0-9a-f]{64}", evidence_hash) is None:
        raise RadarImageError("invalid_artifact_descriptor")

    mime_type = descriptor.get("mimeType")
    byte_size = descriptor.get("byteSize")
    width = descriptor.get("width")
    height = descriptor.get("height")
    if mime_type not in _IMAGE_EXTENSIONS:
        raise RadarImageError("invalid_artifact_descriptor")
    if (
        not isinstance(byte_size, int)
        or isinstance(byte_size, bool)
        or byte_size < 1
        or byte_size > limits.max_image_bytes
        or not isinstance(width, int)
        or isinstance(width, bool)
        or not isinstance(height, int)
        or isinstance(height, bool)
        or width < limits.min_width
        or height < limits.min_height
        or width > limits.max_width
        or height > limits.max_height
        or width * height > limits.max_pixels
    ):
        raise RadarImageError("invalid_artifact_descriptor")

    storage_ref = descriptor.get("storageRef")
    if not isinstance(storage_ref, str) or not storage_ref or "\\" in storage_ref:
        raise RadarImageError("invalid_artifact_descriptor")
    storage_path = PurePosixPath(storage_ref)
    if (
        storage_path.is_absolute()
        or len(storage_path.parts) < 2
        or any(part in {"", ".", ".."} for part in storage_path.parts)
    ):
        raise RadarImageError("invalid_artifact_descriptor")
    _safe_storage_prefix(PurePosixPath(*storage_path.parts[:-1]).as_posix())
    if storage_path.name != f"{image_hash}.{_IMAGE_EXTENSIONS[mime_type]}":
        raise RadarImageError("artifact_storage_mismatch")

    expected_evidence_hash = _descriptor_evidence_sha256(descriptor)
    if not hmac.compare_digest(expected_evidence_hash, evidence_hash):
        raise RadarImageError("descriptor_integrity_mismatch")
    return image_hash, mime_type, byte_size, width, height


def verify_radar_entry_artifact(
    entry: object,
    descriptor: object,
    artifact_bytes: object,
    *,
    limits: CaptureLimits = DEFAULT_LIMITS,
) -> CaptureOutcome:
    """Verify that one artifact is cryptographically and exactly bound to an entry."""

    try:
        image_hash, mime_type, byte_size, expected_width, expected_height = (
            _prevalidate_radar_entry_descriptor(entry, descriptor, limits)
        )
        if not isinstance(artifact_bytes, bytes):
            raise RadarImageError("invalid_artifact_bytes")
        actual_hash = hashlib.sha256(artifact_bytes).hexdigest()
        if not hmac.compare_digest(actual_hash, image_hash):
            raise RadarImageError("artifact_hash_mismatch")
        verified_mime, _extension, width, height = validate_image_bytes(
            artifact_bytes,
            mime_type,
            limits,
        )
        if (
            verified_mime != mime_type
            or byte_size != len(artifact_bytes)
            or expected_width != width
            or expected_height != height
        ):
            raise RadarImageError("artifact_metadata_mismatch")
        return CaptureOutcome(
            ok=True,
            reason_code="artifact_bound",
            descriptor=copy.deepcopy(descriptor),
        )
    except RadarImageError as exc:
        return CaptureOutcome(ok=False, reason_code=exc.code, descriptor=None)
    except Exception:
        return CaptureOutcome(ok=False, reason_code="artifact_verification_failed", descriptor=None)


def _unavailable_image_claim() -> dict[str, object]:
    return {
        "available": False,
        "status": "not_available",
        "attachmentId": None,
        "artifactRef": None,
    }


def enrich_radar_report_with_publisher_images(
    report: object,
    *,
    capture_entry: CaptureEntry,
    load_artifact: ArtifactLoader,
    limits: CaptureLimits = DEFAULT_LIMITS,
    maximum_entries: int = 6,
) -> ReportEnrichmentOutcome:
    """Best-effort report enrichment that never promotes unbound image claims.

    Capture and storage resolution are supplied by Backend-owned callbacks.  A
    failure is isolated to its entry, recorded in diagnostics, and returned with
    the report instead of being raised into Mission completion.
    """

    try:
        working = copy.deepcopy(report) if isinstance(report, dict) else {}
    except Exception:
        working = {}
    diagnostics: list[dict[str, object]] = []
    attached_count = 0
    if not isinstance(report, dict):
        return ReportEnrichmentOutcome(
            report=working,
            attached_count=0,
            diagnostics=({"entryIndex": None, "recordId": None, "status": "invalid_report"},),
        )
    metrics = working.get("metrics") if isinstance(working.get("metrics"), dict) else None
    entries = metrics.get("entries") if isinstance(metrics, dict) and isinstance(metrics.get("entries"), list) else None
    if entries is None:
        return ReportEnrichmentOutcome(
            report=working,
            attached_count=0,
            diagnostics=({"entryIndex": None, "recordId": None, "status": "entries_not_found"},),
        )
    artifacts = working.get("artifacts") if isinstance(working.get("artifacts"), list) else []
    working["artifacts"] = artifacts
    effective_limit = (
        max(0, min(maximum_entries, 50))
        if isinstance(maximum_entries, int) and not isinstance(maximum_entries, bool)
        else 0
    )

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            diagnostics.append({"entryIndex": index, "recordId": None, "status": "invalid_radar_entry"})
            continue
        record_id = entry.get("recordId") if isinstance(entry.get("recordId"), str) else None
        entry["screenshot"] = _unavailable_image_claim()
        if index >= effective_limit:
            diagnostics.append({"entryIndex": index, "recordId": record_id, "status": "entry_limit_exceeded"})
            continue
        try:
            captured = capture_entry(copy.deepcopy(entry))
        except Exception:
            diagnostics.append({"entryIndex": index, "recordId": record_id, "status": "capture_callback_failed"})
            continue
        if not isinstance(captured, CaptureOutcome):
            diagnostics.append({"entryIndex": index, "recordId": record_id, "status": "invalid_capture_outcome"})
            continue
        if not captured.ok or not isinstance(captured.descriptor, dict):
            diagnostics.append({
                "entryIndex": index,
                "recordId": record_id,
                "status": captured.reason_code or "capture_failed",
            })
            continue
        try:
            _prevalidate_radar_entry_descriptor(entry, captured.descriptor, limits)
        except RadarImageError as exc:
            diagnostics.append({"entryIndex": index, "recordId": record_id, "status": exc.code})
            continue
        except Exception:
            diagnostics.append({
                "entryIndex": index,
                "recordId": record_id,
                "status": "artifact_verification_failed",
            })
            continue
        try:
            artifact_bytes = load_artifact(copy.deepcopy(captured.descriptor))
        except Exception:
            diagnostics.append({"entryIndex": index, "recordId": record_id, "status": "artifact_load_failed"})
            continue
        verified = verify_radar_entry_artifact(
            entry,
            captured.descriptor,
            artifact_bytes,
            limits=limits,
        )
        if not verified.ok or not isinstance(verified.descriptor, dict):
            diagnostics.append({"entryIndex": index, "recordId": record_id, "status": verified.reason_code})
            continue
        bound_descriptor = verified.descriptor
        if bound_descriptor not in artifacts:
            artifacts.append(copy.deepcopy(bound_descriptor))
        entry["screenshot"] = {
            "available": True,
            "status": "verified_publisher_image",
            "attachmentId": None,
            "artifactRef": bound_descriptor["storageRef"],
            "mimeType": bound_descriptor["mimeType"],
            "byteSize": bound_descriptor["byteSize"],
            "sha256": bound_descriptor["sha256"],
            "capturedAt": bound_descriptor["capturedAt"],
        }
        attached_count += 1
        diagnostics.append({"entryIndex": index, "recordId": record_id, "status": "attached"})

    return ReportEnrichmentOutcome(
        report=working,
        attached_count=attached_count,
        diagnostics=tuple(diagnostics),
    )


__all__ = [
    "CAPTURE_KIND",
    "SCHEMA_VERSION",
    "CaptureLimits",
    "CaptureOutcome",
    "DEFAULT_LIMITS",
    "FetchedResource",
    "HttpResponse",
    "HttpsTarget",
    "RadarImageError",
    "ReportEnrichmentOutcome",
    "capture_publisher_og_image",
    "discover_publisher_image_url",
    "enrich_radar_report_with_publisher_images",
    "fetch_https_resource",
    "validate_image_bytes",
    "verify_radar_entry_artifact",
]
