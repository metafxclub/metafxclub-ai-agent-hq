from __future__ import annotations

import binascii
import copy
import importlib.util
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "local-runner" / "radar_image_adapter.py"
SPEC = importlib.util.spec_from_file_location("radar_image_adapter_adversarial", MODULE_PATH)
radar = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = radar
SPEC.loader.exec_module(radar)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def valid_png(width: int = 1200, height: int = 630) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(b"\x00"))
        + png_chunk(b"IEND", b"")
    )


def valid_jpeg(width: int = 1200, height: int = 630) -> bytes:
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


def webp_chunk(kind: bytes, payload: bytes, *, pad: bytes = b"\x00") -> bytes:
    return kind + struct.pack("<I", len(payload)) + payload + (pad if len(payload) & 1 else b"")


def valid_webp(width: int = 1200, height: int = 630) -> bytes:
    extended = b"\x00\x00\x00\x00" + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
    frame = b"\x00\x00\x00\x9d\x01\x2a" + struct.pack("<HH", width, height)
    body = b"WEBP" + webp_chunk(b"VP8X", extended) + webp_chunk(b"VP8 ", frame)
    return b"RIFF" + struct.pack("<I", len(body)) + body


class ScriptedRequester:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def __call__(self, target, _headers, _maximum, _timeout):
        self.calls.append(target.normalized_url)
        response = self.responses.get(target.normalized_url)
        if response is None:
            raise AssertionError(f"unexpected request {target.normalized_url}")
        return response


def response(status: int, headers: dict[str, str] | None = None, body: bytes = b""):
    return radar.HttpResponse(status=status, headers=headers or {}, body=body)


class RadarImageAdapterAdversarialTests(unittest.TestCase):
    @staticmethod
    def public_resolver(_hostname: str, _port: int):
        return ("93.184.216.34",)

    def assert_code(self, expected: str, callback) -> None:
        with self.assertRaises(radar.RadarImageError) as captured:
            callback()
        self.assertEqual(expected, captured.exception.code)

    def test_url_parser_rejects_whitespace_controls_bad_escapes_and_invalid_hosts_before_dns(self) -> None:
        cases = (
            ("https://example.com/a b", "invalid_url"),
            ("https://example.com/%00", "invalid_url"),
            ("https://example.com/%0d%0aX-Test:yes", "invalid_url"),
            ("https://example.com/%zz", "invalid_url"),
            ("https://bad_host.example/path", "invalid_hostname"),
            ("https://-bad.example/path", "invalid_hostname"),
            ("https://example.com:444/path", "https_port_rejected"),
        )
        for url, expected in cases:
            with self.subTest(url=url):
                resolver_calls: list[str] = []

                def resolver(hostname: str, _port: int):
                    resolver_calls.append(hostname)
                    return ("93.184.216.34",)

                self.assert_code(
                    expected,
                    lambda value=url: radar.fetch_https_resource(
                        value,
                        accept="text/html",
                        max_bytes=100,
                        resolver=resolver,
                        request_once=lambda *_args: (_ for _ in ()).throw(AssertionError("network")),
                    ),
                )
                self.assertEqual([], resolver_calls)

    def test_redirect_ambiguity_and_encoded_control_are_rejected_before_next_hop(self) -> None:
        source = "https://publisher.example/start"
        ambiguous = ScriptedRequester(
            {
                source: response(
                    302,
                    {
                        "Location": "https://one.example/final",
                        "location": "https://two.example/final",
                    },
                )
            }
        )
        self.assert_code(
            "ambiguous_response_header",
            lambda: radar.fetch_https_resource(
                source,
                accept="text/html",
                max_bytes=100,
                resolver=self.public_resolver,
                request_once=ambiguous,
            ),
        )
        self.assertEqual([source], ambiguous.calls)

        encoded_control = ScriptedRequester(
            {source: response(302, {"Location": "https://next.example/%0aInjected"})}
        )
        self.assert_code(
            "invalid_url",
            lambda: radar.fetch_https_resource(
                source,
                accept="text/html",
                max_bytes=100,
                resolver=self.public_resolver,
                request_once=encoded_control,
            ),
        )
        self.assertEqual([source], encoded_control.calls)

    def test_multicast_addresses_are_not_treated_as_public_destinations(self) -> None:
        for address in ("224.0.0.1", "239.1.1.1", "ff02::1", "ff0e::1"):
            with self.subTest(address=address):
                requester_calls: list[object] = []
                self.assert_code(
                    "non_public_address_rejected",
                    lambda value=address: radar.fetch_https_resource(
                        "https://publisher.example/page",
                        accept="text/html",
                        max_bytes=100,
                        resolver=lambda _host, _port: (value,),
                        request_once=lambda *args: requester_calls.append(args),
                    ),
                )
                self.assertEqual([], requester_calls)

    def test_response_length_and_transport_shapes_fail_closed(self) -> None:
        source = "https://publisher.example/page"
        mismatch = ScriptedRequester(
            {source: response(200, {"Content-Length": "2", "Content-Type": "text/html"}, b"x")}
        )
        self.assert_code(
            "content_length_mismatch",
            lambda: radar.fetch_https_resource(
                source,
                accept="text/html",
                max_bytes=100,
                resolver=self.public_resolver,
                request_once=mismatch,
            ),
        )
        self.assert_code(
            "invalid_transport_response",
            lambda: radar.fetch_https_resource(
                source,
                accept="text/html",
                max_bytes=100,
                resolver=self.public_resolver,
                request_once=lambda *_args: {"status": 200, "body": b"x"},
            ),
        )

        duplicate_encoding = ScriptedRequester(
            {
                source: response(
                    200,
                    {
                        "Content-Type": "text/html",
                        "Content-Encoding": "identity",
                        "content-encoding": "gzip",
                    },
                    b"<html></html>",
                )
            }
        )
        self.assert_code(
            "ambiguous_response_header",
            lambda: radar.fetch_https_resource(
                source,
                accept="text/html",
                max_bytes=100,
                resolver=self.public_resolver,
                request_once=duplicate_encoding,
            ),
        )

    def test_future_checked_at_is_rejected_before_dns_or_network(self) -> None:
        resolver_calls: list[str] = []
        requester_calls: list[object] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = radar.capture_publisher_og_image(
                "https://publisher.example/page",
                checked_at="2026-08-22T02:10:01Z",
                source_record_id="radar-entry-a",
                output_dir=Path(temp_dir),
                resolver=lambda host, _port: resolver_calls.append(host) or ("93.184.216.34",),
                request_once=lambda *args: requester_calls.append(args),
                clock=lambda: datetime(2026, 8, 22, 2, 0, 0, tzinfo=timezone.utc),
            )
        self.assertFalse(outcome.ok)
        self.assertEqual("invalid_checked_at", outcome.reason_code)
        self.assertEqual([], resolver_calls)
        self.assertEqual([], requester_calls)

    def test_duplicate_invalid_metadata_candidate_falls_through_to_next_safe_candidate(self) -> None:
        html = (
            b'<meta property="og:image" content="http://private.example/not-allowed.png">'
            b'<meta property="og:image" content="https://cdn.example/card.png">'
        )
        url, selector = radar.discover_publisher_image_url(
            html,
            "https://publisher.example/page",
        )
        self.assertEqual("https://cdn.example/card.png", url)
        self.assertEqual("og:image", selector)

    def test_png_jpeg_and_webp_require_complete_bounded_container_structure(self) -> None:
        samples = (
            (valid_png(), "image/png"),
            (valid_jpeg(), "image/jpeg"),
            (valid_webp(), "image/webp"),
        )
        for image, mime_type in samples:
            with self.subTest(valid=mime_type):
                self.assertEqual((1200, 630), radar.validate_image_bytes(image, mime_type)[2:])

        png = valid_png()
        invalid_pngs = (
            png[:24],
            png[:-12],
            png + b"<script>alert(1)</script>",
            png[:-1] + bytes([png[-1] ^ 1]),
        )
        for index, image in enumerate(invalid_pngs):
            with self.subTest(kind="png", index=index):
                self.assert_code(
                    "image_dimensions_invalid",
                    lambda value=image: radar.validate_image_bytes(value, "image/png"),
                )

        jpeg = valid_jpeg()
        for index, image in enumerate((jpeg[:-2], jpeg + b"trailing", jpeg[:12] + b"\xff\xd9")):
            with self.subTest(kind="jpeg", index=index):
                self.assert_code(
                    "image_dimensions_invalid",
                    lambda value=image: radar.validate_image_bytes(value, "image/jpeg"),
                )

        webp = valid_webp()
        vp8x_only_body = webp[8:38]
        vp8x_only = b"RIFF" + struct.pack("<I", len(vp8x_only_body)) + vp8x_only_body
        malformed_webps = (
            webp[:4] + struct.pack("<I", len(webp) + 100) + webp[8:],
            vp8x_only,
            webp + b"extra",
        )
        for index, image in enumerate(malformed_webps):
            with self.subTest(kind="webp", index=index):
                self.assert_code(
                    "image_dimensions_invalid",
                    lambda value=image: radar.validate_image_bytes(value, "image/webp"),
                )

    def test_fuzz_like_critical_byte_mutations_never_promote_an_image(self) -> None:
        for mime_type, original, offsets in (
            ("image/png", valid_png(), (8, 16, 24, -1)),
            ("image/jpeg", valid_jpeg(), (0, 2, 4, -1)),
            ("image/webp", valid_webp(), (4, 16, 20, 30)),
        ):
            for offset in offsets:
                with self.subTest(mime=mime_type, offset=offset):
                    mutated = bytearray(original)
                    mutated[offset] ^= 0x01
                    with self.assertRaises(radar.RadarImageError):
                        radar.validate_image_bytes(bytes(mutated), mime_type)

    def test_untrusted_descriptor_is_prevalidated_before_artifact_loader(self) -> None:
        image = valid_png()
        html = b'<meta property="og:image" content="/card.png">'
        requester = ScriptedRequester(
            {
                "https://publisher.example/article": response(
                    200,
                    {"Content-Type": "text/html", "Content-Length": str(len(html))},
                    html,
                ),
                "https://publisher.example/card.png": response(
                    200,
                    {"Content-Type": "image/png", "Content-Length": str(len(image))},
                    image,
                ),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            captured = radar.capture_publisher_og_image(
                "https://publisher.example/article",
                checked_at="2026-08-22T02:00:00Z",
                source_record_id="radar-entry-a",
                output_dir=Path(temp_dir),
                resolver=self.public_resolver,
                request_once=requester,
                clock=lambda: datetime(2026, 8, 22, 2, 0, 5, tzinfo=timezone.utc),
            )
        self.assertTrue(captured.ok, captured.reason_code)
        malicious = copy.deepcopy(captured.descriptor or {})
        malicious["storageRef"] = "../../outside.png"
        malicious["evidenceSha256"] = radar._descriptor_evidence_sha256(malicious)
        loader_calls: list[dict] = []
        report = {
            "metrics": {
                "entries": [
                    {
                        "recordId": "radar-entry-a",
                        "sourceUrl": "https://publisher.example/article",
                        "checkedAt": "2026-08-22T02:00:00Z",
                    }
                ]
            },
            "artifacts": [],
        }
        enriched = radar.enrich_radar_report_with_publisher_images(
            report,
            capture_entry=lambda _entry: radar.CaptureOutcome(True, "captured", malicious),
            load_artifact=lambda descriptor: loader_calls.append(descriptor) or image,
        )
        self.assertEqual([], loader_calls)
        self.assertEqual(0, enriched.attached_count)
        self.assertEqual("invalid_artifact_descriptor", enriched.diagnostics[0]["status"])
        self.assertFalse(enriched.report["metrics"]["entries"][0]["screenshot"]["available"])


if __name__ == "__main__":
    unittest.main()
