from __future__ import annotations

import hashlib
import importlib.util
import binascii
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = PROJECT_ROOT / "backend" / "local-runner" / "radar_image_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("metafx_radar_image_adapter", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {ADAPTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapter = load_adapter()


def png_header(width: int = 1200, height: int = 630) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"\x00")) + chunk(b"IEND", b"")


def jpeg_header(width: int = 1200, height: int = 630) -> bytes:
    sof_payload = b"\x08" + struct.pack(">HH", height, width) + b"\x01\x01\x11\x00"
    sos_payload = b"\x01\x01\x00\x00\x3f\x00"
    return (
        b"\xff\xd8\xff\xc0"
        + struct.pack(">H", len(sof_payload) + 2)
        + sof_payload
        + b"\xff\xda"
        + struct.pack(">H", len(sos_payload) + 2)
        + sos_payload
        + b"\x00\xff\xd9"
    )


def webp_vp8x_header(width: int = 1200, height: int = 630) -> bytes:
    payload = b"\x00\x00\x00\x00" + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
    frame = b"\x00\x00\x00\x9d\x01\x2a" + struct.pack("<HH", width, height)
    body = (
        b"WEBP"
        + b"VP8X"
        + struct.pack("<I", len(payload))
        + payload
        + b"VP8 "
        + struct.pack("<I", len(frame))
        + frame
    )
    return b"RIFF" + struct.pack("<I", len(body)) + body


class ScriptedRequester:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[object] = []

    def __call__(self, target, headers, max_bytes, timeout_seconds):
        self.calls.append(target)
        if "Authorization" in headers or "Cookie" in headers:
            raise AssertionError("credential-bearing header was sent")
        if headers.get("Accept-Encoding") != "identity":
            raise AssertionError("compressed response was requested")
        response = self.responses.get(target.normalized_url)
        if response is None:
            raise AssertionError(f"unexpected request: {target.normalized_url}")
        return response


def response(status: int, content_type: str | None, body: bytes, **headers: str):
    response_headers = dict(headers)
    if content_type is not None:
        response_headers["Content-Type"] = content_type
    if status == 200 and "Content-Length" not in response_headers:
        response_headers["Content-Length"] = str(len(body))
    return adapter.HttpResponse(status=status, headers=response_headers, body=body)


class RadarImageAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.public_resolutions: list[tuple[str, int]] = []

    def public_resolver(self, hostname: str, port: int):
        self.public_resolutions.append((hostname, port))
        return ("93.184.216.34",)

    def test_pinned_connection_uses_literal_ip_but_hostname_for_tls_sni(self) -> None:
        observations: dict[str, object] = {}

        class RawSocket:
            def close(self):
                observations["raw_closed"] = True

        class WrappedSocket:
            pass

        class FakeContext:
            # Python 3.11 inspects these SSLContext attributes while
            # constructing HTTPSConnection. Mirror the secure defaults used
            # by ssl.create_default_context() so this test double satisfies
            # the same contract on every supported Python version.
            verify_mode = adapter.ssl.CERT_REQUIRED
            check_hostname = True

            def wrap_socket(self, raw_socket, *, server_hostname):
                observations["wrapped_raw"] = raw_socket
                observations["server_hostname"] = server_hostname
                return WrappedSocket()

        context = FakeContext()
        raw_socket = RawSocket()
        with mock.patch.object(adapter.ssl, "create_default_context", return_value=context):
            connection = adapter._PinnedHTTPSConnection(
                "publisher.example",
                "93.184.216.34",
                2.5,
            )
        connection._create_connection = lambda endpoint, timeout, source: observations.update(
            endpoint=endpoint,
            timeout=timeout,
            source=source,
        ) or raw_socket
        connection.connect()
        self.assertEqual(("93.184.216.34", 443), observations["endpoint"])
        self.assertEqual("publisher.example", observations["server_hostname"])
        self.assertIs(raw_socket, observations["wrapped_raw"])
        self.assertIsInstance(connection.sock, WrappedSocket)

    def capture(self, requester, directory: Path, **overrides):
        arguments = {
            "source_url": "https://publisher.example/article",
            "checked_at": "2026-08-22T09:00:00+07:00",
            "output_dir": directory,
            "resolver": self.public_resolver,
            "request_once": requester,
            "clock": lambda: datetime(2026, 8, 22, 2, 0, 5, tzinfo=timezone.utc),
        }
        arguments.update(overrides)
        return adapter.capture_publisher_og_image(**arguments)

    def test_success_is_content_addressed_and_descriptor_is_bound(self) -> None:
        image = png_header()
        html = b'<html><head><meta property="og:image" content="/media/card.png"></head></html>'
        requester = ScriptedRequester(
            {
                "https://publisher.example/article": response(200, "text/html; charset=utf-8", html),
                "https://publisher.example/media/card.png": response(200, "image/png", image),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = self.capture(requester, Path(temp_dir))
            self.assertTrue(outcome.ok, outcome.reason_code)
            self.assertEqual("captured", outcome.reason_code)
            descriptor = outcome.descriptor or {}
            image_hash = hashlib.sha256(image).hexdigest()
            self.assertEqual("radar-publisher-image-v1", descriptor["schemaVersion"])
            self.assertEqual("publisher_open_graph", descriptor["captureKind"])
            self.assertEqual("https://publisher.example/article", descriptor["sourceUrl"])
            self.assertEqual("2026-08-22T02:00:00Z", descriptor["sourceCheckedAt"])
            self.assertEqual("2026-08-22T02:00:05Z", descriptor["capturedAt"])
            self.assertEqual("og:image", descriptor["publisherImageSelector"])
            self.assertEqual(image_hash, descriptor["sha256"])
            self.assertEqual(1200, descriptor["width"])
            self.assertEqual(630, descriptor["height"])
            self.assertEqual(64, len(str(descriptor["evidenceSha256"])))
            self.assertEqual(image, (Path(temp_dir) / f"{image_hash}.png").read_bytes())
            self.assertEqual(
                f"data/memory/screenshots/radar/{image_hash}.png",
                descriptor["storageRef"],
            )
            self.assertEqual(2, len(requester.calls))
            self.assertTrue(all(call.addresses == ("93.184.216.34",) for call in requester.calls))

    def test_redirects_are_resolved_and_public_ip_revalidated_per_hop(self) -> None:
        image = png_header()
        html = b'<meta property="og:image:secure_url" content="https://cdn.example/card.png">'
        requester = ScriptedRequester(
            {
                "https://publisher.example/article": response(
                    302,
                    None,
                    b"",
                    Location="https://news.example/final",
                ),
                "https://news.example/final": response(200, "text/html", html),
                "https://cdn.example/card.png": response(
                    307,
                    None,
                    b"",
                    Location="https://images.example/card.png",
                ),
                "https://images.example/card.png": response(200, "image/png", image),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = self.capture(requester, Path(temp_dir))
        self.assertTrue(outcome.ok, outcome.reason_code)
        self.assertEqual(
            [
                ("publisher.example", 443),
                ("news.example", 443),
                ("cdn.example", 443),
                ("images.example", 443),
            ],
            self.public_resolutions,
        )
        descriptor = outcome.descriptor or {}
        self.assertEqual("https://news.example/final", descriptor["finalSourceUrl"])
        self.assertEqual("https://images.example/card.png", descriptor["finalPublisherImageUrl"])

    def test_private_or_mixed_dns_answer_is_rejected_before_request(self) -> None:
        requester = ScriptedRequester({})

        def mixed_resolver(_hostname: str, _port: int):
            return ("93.184.216.34", "127.0.0.1")

        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = self.capture(requester, Path(temp_dir), resolver=mixed_resolver)
        self.assertFalse(outcome.ok)
        self.assertEqual("non_public_address_rejected", outcome.reason_code)
        self.assertEqual([], requester.calls)

    def test_unbounded_dns_answer_is_rejected_before_request(self) -> None:
        requester = ScriptedRequester({})

        def many_answers(_hostname: str, _port: int):
            return tuple(f"8.8.8.{index}" for index in range(1, 10))

        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = self.capture(requester, Path(temp_dir), resolver=many_answers)
        self.assertFalse(outcome.ok)
        self.assertEqual("dns_answer_too_large", outcome.reason_code)
        self.assertEqual([], requester.calls)

    def test_redirect_to_private_host_is_rejected_before_second_request(self) -> None:
        requester = ScriptedRequester(
            {
                "https://publisher.example/article": response(
                    302,
                    None,
                    b"",
                    Location="https://private.example/final",
                )
            }
        )

        def resolver(hostname: str, _port: int):
            return ("10.0.0.8",) if hostname == "private.example" else ("93.184.216.34",)

        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = self.capture(requester, Path(temp_dir), resolver=resolver)
        self.assertFalse(outcome.ok)
        self.assertEqual("non_public_address_rejected", outcome.reason_code)
        self.assertEqual(1, len(requester.calls))

    def test_http_metadata_candidate_is_ignored_and_nothing_is_written(self) -> None:
        html = b'<meta property="og:image" content="http://cdn.example/card.png">'
        requester = ScriptedRequester(
            {"https://publisher.example/article": response(200, "text/html", html)}
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            outcome = self.capture(requester, directory)
            self.assertEqual([], list(directory.iterdir()))
        self.assertFalse(outcome.ok)
        self.assertEqual("publisher_image_not_found", outcome.reason_code)

    def test_oversized_or_encoded_resource_fails_closed(self) -> None:
        cases = (
            (
                response(200, "text/html", b"x" * 11),
                adapter.CaptureLimits(max_html_bytes=10),
                "response_too_large",
            ),
            (
                response(200, "text/html", b"x", **{"Content-Encoding": "gzip"}),
                adapter.DEFAULT_LIMITS,
                "encoded_response_rejected",
            ),
        )
        for source_response, limits, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                requester = ScriptedRequester(
                    {"https://publisher.example/article": source_response}
                )
                outcome = self.capture(requester, Path(temp_dir), limits=limits)
                self.assertFalse(outcome.ok)
                self.assertEqual(expected, outcome.reason_code)
                self.assertEqual([], list(Path(temp_dir).iterdir()))

    def test_image_magic_type_and_dimensions_are_strict(self) -> None:
        valid_samples = (
            (png_header(), "image/png", "png"),
            (jpeg_header(), "image/jpeg", "jpg"),
            (webp_vp8x_header(), "image/webp", "webp"),
        )
        for image, mime_type, extension in valid_samples:
            with self.subTest(mime_type=mime_type):
                self.assertEqual(
                    (mime_type, extension, 1200, 630),
                    adapter.validate_image_bytes(image, mime_type),
                )
        invalid_samples = (
            (png_header(), "image/jpeg", "image_type_mismatch"),
            (b"not an image", "image/png", "image_magic_rejected"),
            (png_header(50, 50), "image/png", "image_dimensions_rejected"),
        )
        for image, mime_type, expected in invalid_samples:
            with self.subTest(expected=expected):
                with self.assertRaises(adapter.RadarImageError) as captured:
                    adapter.validate_image_bytes(image, mime_type)
                self.assertEqual(expected, captured.exception.code)

    def test_redirect_loop_and_redirect_limit_fail_closed(self) -> None:
        loop_requester = ScriptedRequester(
            {
                "https://publisher.example/article": response(
                    302,
                    None,
                    b"",
                    Location="https://publisher.example/other",
                ),
                "https://publisher.example/other": response(
                    302,
                    None,
                    b"",
                    Location="https://publisher.example/article",
                ),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = self.capture(loop_requester, Path(temp_dir))
        self.assertEqual("redirect_loop", loop.reason_code)

        limit_requester = ScriptedRequester(
            {
                "https://publisher.example/article": response(302, None, b"", Location="/one"),
                "https://publisher.example/one": response(302, None, b"", Location="/two"),
            }
        )
        limits = adapter.CaptureLimits(max_redirects=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            limited = self.capture(limit_requester, Path(temp_dir), limits=limits)
        self.assertEqual("redirect_limit_exceeded", limited.reason_code)

    def test_sensitive_query_credentials_and_naive_time_are_rejected_without_network(self) -> None:
        cases = (
            ("https://publisher.example/article?api_key=hidden", "sensitive_query_rejected"),
            ("https://publisher.example/article?X-Amz-Signature=hidden", "sensitive_query_rejected"),
            ("https://user:pass@publisher.example/article", "embedded_credentials_rejected"),
            ("http://publisher.example/article", "https_required"),
        )
        for source_url, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                requester = ScriptedRequester({})
                outcome = self.capture(requester, Path(temp_dir), source_url=source_url)
                self.assertEqual(expected, outcome.reason_code)
                self.assertEqual([], requester.calls)
        with tempfile.TemporaryDirectory() as temp_dir:
            requester = ScriptedRequester({})
            outcome = self.capture(
                requester,
                Path(temp_dir),
                checked_at="2026-08-22T09:00:00",
            )
        self.assertEqual("invalid_checked_at", outcome.reason_code)
        self.assertEqual([], requester.calls)

    def test_absolute_or_unsafe_storage_prefix_is_rejected_without_network(self) -> None:
        for prefix in ("/absolute/radar", "../radar", "C:/radar", "radar/has space"):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as temp_dir:
                requester = ScriptedRequester({})
                outcome = self.capture(requester, Path(temp_dir), storage_prefix=prefix)
                self.assertEqual("invalid_storage_prefix", outcome.reason_code)
                self.assertEqual([], requester.calls)

    def test_existing_content_is_idempotent_but_collision_is_rejected(self) -> None:
        image = png_header()
        image_hash = hashlib.sha256(image).hexdigest()
        html = b'<meta property="og:image" content="https://cdn.example/card.png">'

        def requester():
            return ScriptedRequester(
                {
                    "https://publisher.example/article": response(200, "text/html", html),
                    "https://cdn.example/card.png": response(200, "image/png", image),
                }
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            first = self.capture(requester(), directory)
            second = self.capture(requester(), directory)
            self.assertTrue(first.ok)
            self.assertTrue(second.ok)
            self.assertEqual(1, len(list(directory.iterdir())))

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / f"{image_hash}.png").write_bytes(b"tampered")
            collision = self.capture(requester(), directory)
            self.assertFalse(collision.ok)
            self.assertEqual("storage_collision", collision.reason_code)

    def test_invalid_content_types_and_missing_metadata_do_not_write(self) -> None:
        cases = (
            (response(200, "application/json", b"{}"), "html_content_type_rejected"),
            (response(200, "text/html", b"<html></html>"), "publisher_image_not_found"),
        )
        for source_response, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                directory = Path(temp_dir)
                requester = ScriptedRequester(
                    {"https://publisher.example/article": source_response}
                )
                outcome = self.capture(requester, directory)
                self.assertEqual(expected, outcome.reason_code)
                self.assertEqual([], list(directory.iterdir()))


if __name__ == "__main__":
    unittest.main()
