from __future__ import annotations

import copy
import binascii
import importlib.util
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = PROJECT_ROOT / "backend" / "local-runner" / "radar_image_adapter.py"


def load_adapter():
    name = "metafx_radar_image_report_integration_adapter"
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {ADAPTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
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


def http_response(status: int, content_type: str | None, body: bytes, **headers: str):
    values = dict(headers)
    if content_type:
        values["Content-Type"] = content_type
    if status == 200:
        values.setdefault("Content-Length", str(len(body)))
    return adapter.HttpResponse(status=status, headers=values, body=body)


class ScriptedRequester:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def __call__(self, target, _headers, _max_bytes, _timeout):
        self.calls.append(target.normalized_url)
        if target.normalized_url not in self.responses:
            raise AssertionError(f"unexpected network request: {target.normalized_url}")
        return self.responses[target.normalized_url]


class RadarImageReportIntegrationTests(unittest.TestCase):
    source_url = "https://publisher.example/article"
    image_url = "https://publisher.example/card.png"
    record_id = "radar-entry-a"
    checked_at = "2026-08-22T09:00:00+07:00"

    @staticmethod
    def resolver(_hostname: str, _port: int):
        return ("93.184.216.34",)

    def requester(self, image: bytes | None = None):
        image_bytes = image or png_header()
        html = b'<meta property="og:image" content="/card.png">'
        return ScriptedRequester(
            {
                self.source_url: http_response(200, "text/html", html),
                self.image_url: http_response(200, "image/png", image_bytes),
            }
        )

    def entry(self, *, record_id: str | None = None, source_url: str | None = None):
        return {
            "recordId": record_id or self.record_id,
            "toolName": "Publisher Tool",
            "sourceUrl": source_url or self.source_url,
            "checkedAt": self.checked_at,
        }

    def report(self, entries: list[dict] | None = None):
        return {
            "id": "report-radar-binding",
            "type": "indicator_scout_report",
            "metrics": {"entries": entries or [self.entry()]},
            "artifacts": [],
        }

    def capture(self, directory: Path, *, record_id: object = record_id, source_url: object = source_url):
        return adapter.capture_publisher_og_image(
            source_url,
            checked_at=self.checked_at,
            source_record_id=record_id,
            output_dir=directory,
            resolver=self.resolver,
            request_once=self.requester(),
            clock=lambda: datetime(2026, 8, 22, 2, 0, 5, tzinfo=timezone.utc),
        )

    @staticmethod
    def load_from(directory: Path, descriptor: dict[str, object]) -> bytes:
        return (directory / PureName(descriptor["storageRef"])).read_bytes()

    def test_capture_and_report_enrichment_require_exact_three_way_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            source_report = self.report()

            def capture_entry(entry):
                return self.capture(
                    directory,
                    record_id=entry["recordId"],
                    source_url=entry["sourceUrl"],
                )

            enriched = adapter.enrich_radar_report_with_publisher_images(
                source_report,
                capture_entry=capture_entry,
                load_artifact=lambda descriptor: self.load_from(directory, descriptor),
            )
            reenriched = adapter.enrich_radar_report_with_publisher_images(
                enriched.report,
                capture_entry=capture_entry,
                load_artifact=lambda descriptor: self.load_from(directory, descriptor),
            )

        self.assertEqual(1, enriched.attached_count)
        self.assertEqual("attached", enriched.diagnostics[0]["status"])
        self.assertNotIn("screenshot", source_report["metrics"]["entries"][0])
        result_entry = enriched.report["metrics"]["entries"][0]
        self.assertTrue(result_entry["screenshot"]["available"])
        self.assertEqual("verified_publisher_image", result_entry["screenshot"]["status"])
        self.assertEqual(self.record_id, enriched.report["artifacts"][0]["sourceRecordId"])
        self.assertEqual(self.source_url, enriched.report["artifacts"][0]["sourceUrl"])
        self.assertEqual(
            enriched.report["artifacts"][0]["sha256"],
            result_entry["screenshot"]["sha256"],
        )
        self.assertEqual(1, len(reenriched.report["artifacts"]))

    def test_record_url_hash_or_descriptor_tampering_is_fail_closed(self) -> None:
        image = png_header()
        with tempfile.TemporaryDirectory() as temp_dir:
            captured = self.capture(Path(temp_dir))
        self.assertTrue(captured.ok, captured.reason_code)
        descriptor = captured.descriptor or {}
        entry = self.entry()

        cases: list[tuple[str, dict[str, object], bytes, str]] = []
        wrong_record = copy.deepcopy(descriptor)
        wrong_record["sourceRecordId"] = "radar-entry-b"
        cases.append(("record", wrong_record, image, "source_record_mismatch"))

        wrong_url = copy.deepcopy(descriptor)
        wrong_url["sourceUrl"] = "https://publisher.example/another-article"
        cases.append(("url", wrong_url, image, "source_url_mismatch"))

        wrong_hash = copy.deepcopy(descriptor)
        wrong_hash["sha256"] = "0" * 64
        cases.append(("descriptor-hash", wrong_hash, image, "artifact_storage_mismatch"))

        changed_binding = copy.deepcopy(descriptor)
        changed_binding["sourceFetchedAt"] = "2026-08-22T02:00:06Z"
        cases.append(("binding", changed_binding, image, "invalid_artifact_descriptor"))

        cases.append(("artifact-bytes", copy.deepcopy(descriptor), png_header(1000, 600), "artifact_hash_mismatch"))

        for label, candidate, artifact_bytes, expected in cases:
            with self.subTest(label=label):
                verified = adapter.verify_radar_entry_artifact(
                    entry,
                    candidate,
                    artifact_bytes,
                )
                self.assertFalse(verified.ok)
                self.assertEqual(expected, verified.reason_code)
                self.assertIsNone(verified.descriptor)
                if label in {"record", "url", "descriptor-hash"}:
                    enriched = adapter.enrich_radar_report_with_publisher_images(
                        self.report(),
                        capture_entry=lambda _entry, value=candidate: adapter.CaptureOutcome(
                            ok=True,
                            reason_code="captured",
                            descriptor=value,
                        ),
                        load_artifact=lambda _descriptor, value=artifact_bytes: value,
                    )
                    self.assertEqual(0, enriched.attached_count)
                    self.assertEqual(expected, enriched.diagnostics[0]["status"])
                    self.assertFalse(
                        enriched.report["metrics"]["entries"][0]["screenshot"]["available"]
                    )
                    self.assertEqual([], enriched.report["artifacts"])

        wrong_time_entry = self.entry()
        wrong_time_entry["checkedAt"] = "2026-08-22T09:01:00+07:00"
        wrong_time = adapter.verify_radar_entry_artifact(
            wrong_time_entry,
            descriptor,
            image,
        )
        self.assertFalse(wrong_time.ok)
        self.assertEqual("source_checked_at_mismatch", wrong_time.reason_code)

    def test_unbound_capture_descriptor_never_becomes_displayable(self) -> None:
        image = png_header()
        with tempfile.TemporaryDirectory() as temp_dir:
            captured = self.capture(Path(temp_dir), record_id=None)
        self.assertTrue(captured.ok)
        self.assertIsNone((captured.descriptor or {}).get("sourceRecordId"))
        verified = adapter.verify_radar_entry_artifact(
            self.entry(),
            captured.descriptor,
            image,
        )
        self.assertFalse(verified.ok)
        self.assertEqual("invalid_source_record_id", verified.reason_code)

    def test_capture_or_load_failure_isolated_per_entry_and_report_survives(self) -> None:
        first = self.entry()
        second = self.entry(
            record_id="radar-entry-b",
            source_url="https://publisher.example/second-article",
        )
        source_report = self.report([first, second])
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)

            def capture_entry(entry):
                if entry["recordId"] == "radar-entry-b":
                    raise RuntimeError("simulated adapter outage")
                return self.capture(
                    directory,
                    record_id=entry["recordId"],
                    source_url=entry["sourceUrl"],
                )

            enriched = adapter.enrich_radar_report_with_publisher_images(
                source_report,
                capture_entry=capture_entry,
                load_artifact=lambda descriptor: self.load_from(directory, descriptor),
            )

        self.assertEqual("report-radar-binding", enriched.report["id"])
        self.assertEqual(1, enriched.attached_count)
        self.assertTrue(enriched.report["metrics"]["entries"][0]["screenshot"]["available"])
        self.assertFalse(enriched.report["metrics"]["entries"][1]["screenshot"]["available"])
        self.assertEqual("capture_callback_failed", enriched.diagnostics[1]["status"])
        self.assertEqual(1, len(enriched.report["artifacts"]))

        captured = adapter.CaptureOutcome(
            ok=True,
            reason_code="captured",
            descriptor=enriched.report["artifacts"][0],
        )
        load_failed = adapter.enrich_radar_report_with_publisher_images(
            self.report(),
            capture_entry=lambda _entry: captured,
            load_artifact=lambda _descriptor: (_ for _ in ()).throw(OSError("unavailable")),
        )
        self.assertEqual(0, load_failed.attached_count)
        self.assertEqual("artifact_load_failed", load_failed.diagnostics[0]["status"])
        self.assertFalse(load_failed.report["metrics"]["entries"][0]["screenshot"]["available"])

    def test_invalid_capture_result_does_not_raise_or_promote_worker_claim(self) -> None:
        source_report = self.report()
        source_report["metrics"]["entries"][0]["screenshot"] = {
            "available": True,
            "artifactRef": "untrusted.png",
        }
        enriched = adapter.enrich_radar_report_with_publisher_images(
            source_report,
            capture_entry=lambda _entry: adapter.CaptureOutcome(
                ok=False,
                reason_code="publisher_image_not_found",
                descriptor=None,
            ),
            load_artifact=lambda _descriptor: b"should-not-load",
        )
        self.assertEqual(0, enriched.attached_count)
        self.assertEqual("publisher_image_not_found", enriched.diagnostics[0]["status"])
        claim = enriched.report["metrics"]["entries"][0]["screenshot"]
        self.assertFalse(claim["available"])
        self.assertIsNone(claim["artifactRef"])


def PureName(storage_ref: object) -> str:
    return str(storage_ref).replace("\\", "/").rsplit("/", 1)[-1]


if __name__ == "__main__":
    unittest.main()
