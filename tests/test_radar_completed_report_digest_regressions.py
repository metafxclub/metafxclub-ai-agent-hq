from __future__ import annotations

import binascii
import copy
import hashlib
import importlib.util
import json
import struct
import tempfile
import types
import unittest
import zlib
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
LIFECYCLE_TEST_PATH = (
    PROJECT_ROOT / "tests" / "test_radar_batch_repair_lifecycle.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_lifecycle_helpers = load_module(
    "radar_completed_digest_lifecycle_helpers",
    LIFECYCLE_TEST_PATH,
)


def png_bytes(width: int = 1200, height: int = 630) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b"\x00"))
        + chunk(b"IEND", b"")
    )


class RadarCompletedReportDigestRegressions(unittest.TestCase):
    """Fail-closed coverage for mutable optional Radar image enrichment."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module(
            "radar_completed_report_digest_bridge",
            BRIDGE_PATH,
        )

    def setUp(self) -> None:
        self.bridge._invalidate_missions_read_cache()
        with self.bridge.RATE_LIMIT_LOCK:
            self.bridge.RATE_LIMIT_STATE.clear()

    # Reuse the strict-six Mission builders without inheriting their tests.
    scheduled_radar = (
        _lifecycle_helpers.RadarBatchRepairLifecycleTests.scheduled_radar
    )
    prime_daily_schedule = (
        _lifecycle_helpers.RadarBatchRepairLifecycleTests.prime_daily_schedule
    )
    urls = staticmethod(
        _lifecycle_helpers.RadarBatchRepairLifecycleTests.urls
    )
    write_artifact = (
        _lifecycle_helpers.RadarBatchRepairLifecycleTests.write_artifact
    )
    apply_batch_repair = (
        _lifecycle_helpers.RadarBatchRepairLifecycleTests.apply_batch_repair
    )
    make_running = (
        _lifecycle_helpers.RadarBatchRepairLifecycleTests.make_running
    )
    valid_six_result = (
        _lifecycle_helpers.RadarBatchRepairLifecycleTests.valid_six_result
    )

    def entries(self) -> list[dict]:
        # Publisher-image bindings intentionally canonicalize timestamps to
        # whole UTC seconds, matching real Radar structured output.
        rows = (
            _lifecycle_helpers.RadarBatchRepairLifecycleTests.entries(self)
        )
        checked_at = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
        for row in rows:
            row["checkedAt"] = checked_at
        return rows

    def runtime(self, temp_dir: str) -> ExitStack:
        root = Path(temp_dir)
        runtime = root / "data" / "runtime"
        stack = ExitStack()
        stack.enter_context(mock.patch.object(self.bridge, "PROJECT_ROOT", root))
        stack.enter_context(mock.patch.object(self.bridge, "RUNTIME_DIR", runtime))
        stack.enter_context(
            mock.patch.object(self.bridge, "PROJECT_RUNTIME_DIR", runtime)
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "MISSIONS_PATH",
                runtime / "missions.json",
            )
        )
        stack.enter_context(
            mock.patch.object(self.bridge, "AUDIT_PATH", runtime / "audit.jsonl")
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "OPERATOR_MODE_PATH",
                runtime / "operator.json",
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                runtime / "dashboard-workflow-settings.json",
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "RUNTIME_REPORTS_DIR",
                runtime / "reports",
            )
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "MEMORY_DIR",
                root / "data" / "memory",
            )
        )
        self.bridge._invalidate_missions_read_cache()
        return stack

    def complete_batch(
        self,
        temp_dir: str,
        *,
        label: str,
    ) -> tuple[dict, dict, Path, str, dict]:
        mission, slot_key = self.scheduled_radar()
        self.prime_daily_schedule(mission, slot_key)
        failure_reference = self.write_artifact(
            temp_dir,
            f"{label}-source.final.md",
            {"status": "invalid_output", "evidence": []},
        )
        mission = self.apply_batch_repair(mission, failure_reference)
        self.bridge.replace_mission(mission)
        lease_id = f"lease-{label}"
        self.make_running(mission, lease_id)
        valid_result = self.valid_six_result(
            temp_dir,
            final_name=f"{label}-success.final.md",
            run_id=f"run-{label}",
        )
        with mock.patch.object(
            self.bridge,
            "queue_radar_publisher_image_enrichment",
        ):
            completed = self.bridge.finish_auto_mission(
                mission["id"],
                lease_id,
                {"processStarted": True},
                valid_result,
            )
        self.assertIsInstance(completed, dict)
        self.assertEqual("completed", completed["status"])
        report_id = completed["reportIds"][0]
        report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return completed, report, report_path, lease_id, valid_result

    def capture_first_publisher_image(self, report: dict):
        entry = report["metrics"]["entries"][0]
        source_url = entry["sourceUrl"]
        image_url = source_url.rsplit("/", 1)[0] + "/publisher-card.png"
        image = png_bytes()
        html = b'<meta property="og:image" content="publisher-card.png">'
        response_type = self.bridge.capture_publisher_og_image.__globals__[
            "HttpResponse"
        ]

        def response(content_type: str, body: bytes):
            return response_type(
                status=200,
                headers={
                    "Content-Type": content_type,
                    "Content-Length": str(len(body)),
                },
                body=body,
            )

        def request_once(target, _headers, _maximum_bytes, _timeout):
            if target.normalized_url == source_url:
                return response("text/html; charset=utf-8", html)
            if target.normalized_url == image_url:
                return response("image/png", image)
            raise AssertionError(f"unexpected image request: {target.normalized_url}")

        checked_at = self.bridge.parse_iso(entry["checkedAt"])
        self.assertIsNotNone(checked_at)
        captured = self.bridge.capture_publisher_og_image(
            source_url,
            checked_at=entry["checkedAt"],
            source_record_id=entry["recordId"],
            output_dir=self.bridge.MEMORY_DIR / "screenshots" / "radar",
            resolver=lambda _hostname, _port: ("93.184.216.34",),
            request_once=request_once,
            clock=lambda: checked_at.astimezone(timezone.utc) + timedelta(seconds=1),
        )
        self.assertTrue(captured.ok, captured.reason_code)
        return captured, image

    def run_one_image_enrichment(self, report: dict) -> None:
        captured, _image = self.capture_first_publisher_image(report)
        first_url = report["metrics"]["entries"][0]["sourceUrl"]

        def capture(source_url, **_kwargs):
            if source_url == first_url:
                return captured
            return types.SimpleNamespace(
                ok=False,
                reason_code="publisher_image_not_available",
                descriptor=None,
            )

        with mock.patch.object(
            self.bridge,
            "capture_publisher_og_image",
            side_effect=capture,
        ):
            self.bridge._run_radar_publisher_image_enrichment(report["id"])

    def test_optional_image_enrichment_updates_exact_digest_and_late_finish_is_safe(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            completed, report, report_path, lease_id, valid_result = (
                self.complete_batch(temp_dir, label="image-success")
            )
            original_digest = completed["radarBatchReportCommit"]["reportDigest"]

            self.run_one_image_enrichment(report)

            enriched_report = json.loads(report_path.read_text(encoding="utf-8"))
            enriched_mission = self.bridge.find_mission(completed["id"])
            exact_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
            duplicate_reconcile = (
                self.bridge.reconcile_completed_radar_batch_report_digests()
            )
            late_finish = self.bridge.finish_auto_mission(
                completed["id"],
                lease_id,
                {"processStarted": True},
                valid_result,
            )
            after_late_finish = self.bridge.find_mission(completed["id"])

        self.assertNotEqual(original_digest, exact_digest)
        self.assertEqual("completed", enriched_mission["status"])
        self.assertEqual(
            exact_digest,
            enriched_mission["radarBatchReportCommit"]["reportDigest"],
        )
        self.assertEqual(
            1,
            enriched_report["metrics"]["publisherImageAdapter"]["attachedCount"],
        )
        self.assertEqual(1, len(enriched_report["artifacts"]) - 1)
        self.assertEqual(0, duplicate_reconcile)
        self.assertIsNone(late_finish)
        self.assertEqual("completed", after_late_finish["status"])
        self.assertEqual(
            exact_digest,
            after_late_finish["radarBatchReportCommit"]["reportDigest"],
        )

    def test_startup_reconcile_heals_large_stale_digest_once_and_rejects_oversize(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            completed, report, report_path, _lease_id, _valid_result = (
                self.complete_batch(temp_dir, label="startup-large")
            )
            with mock.patch.object(
                self.bridge,
                "capture_publisher_og_image",
                return_value=None,
            ), mock.patch.object(
                self.bridge,
                "_refresh_completed_radar_batch_report_digest",
                return_value=(None, False),
            ):
                self.bridge._run_radar_publisher_image_enrichment(report["id"])

            enriched_bytes = report_path.read_bytes()
            large_target = 80_000
            report_path.write_bytes(
                enriched_bytes
                + b" " * max(1, large_target - len(enriched_bytes))
            )
            self.assertGreater(report_path.stat().st_size, 40_000)
            self.assertLess(
                report_path.stat().st_size,
                self.bridge.RADAR_BATCH_REPORT_MAX_BYTES,
            )
            exact_large_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
            stale = self.bridge.find_mission(completed["id"])

            first = self.bridge.reconcile_completed_radar_batch_report_digests()
            second = self.bridge.reconcile_completed_radar_batch_report_digests()
            healed = self.bridge.find_mission(completed["id"])

            valid_large_bytes = report_path.read_bytes()
            report_path.write_bytes(
                valid_large_bytes
                + b" "
                * (
                    self.bridge.RADAR_BATCH_REPORT_MAX_BYTES
                    + 1
                    - len(valid_large_bytes)
                )
            )
            oversize_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
            oversize_refresh = (
                self.bridge.reconcile_completed_radar_batch_report_digests()
            )
            after_oversize = self.bridge.find_mission(completed["id"])

        self.assertNotEqual(
            exact_large_digest,
            stale["radarBatchReportCommit"]["reportDigest"],
        )
        self.assertEqual(1, first)
        self.assertEqual(0, second)
        self.assertEqual(
            exact_large_digest,
            healed["radarBatchReportCommit"]["reportDigest"],
        )
        self.assertNotEqual(exact_large_digest, oversize_digest)
        self.assertEqual(0, oversize_refresh)
        self.assertEqual(
            exact_large_digest,
            after_oversize["radarBatchReportCommit"]["reportDigest"],
        )

    def test_core_evidence_and_forged_image_tampering_never_refresh_digest(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            completed, report, report_path, _lease_id, _valid_result = (
                self.complete_batch(temp_dir, label="tamper-guard")
            )
            self.run_one_image_enrichment(report)
            baseline_bytes = report_path.read_bytes()
            baseline_report = json.loads(baseline_bytes.decode("utf-8"))
            baseline_digest = hashlib.sha256(baseline_bytes).hexdigest()
            baseline_mission = self.bridge.find_mission(completed["id"])
            self.assertEqual(
                baseline_digest,
                baseline_mission["radarBatchReportCommit"]["reportDigest"],
            )

            def rejected(candidate: dict) -> None:
                report_path.write_text(
                    json.dumps(
                        candidate,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    encoding="utf-8",
                )
                self.assertNotEqual(
                    baseline_digest,
                    hashlib.sha256(report_path.read_bytes()).hexdigest(),
                )
                self.assertEqual(
                    0,
                    self.bridge.reconcile_completed_radar_batch_report_digests(),
                )
                stored = self.bridge.find_mission(completed["id"])
                self.assertEqual(
                    baseline_digest,
                    stored["radarBatchReportCommit"]["reportDigest"],
                )
                report_path.write_bytes(baseline_bytes)

            core_tamper = copy.deepcopy(baseline_report)
            core_tamper["summary"] = "forged completed summary"
            rejected(core_tamper)

            evidence_tamper = copy.deepcopy(baseline_report)
            evidence_tamper["evidence"][0]["url"] = (
                "https://attacker.example/forged-source"
            )
            rejected(evidence_tamper)

            image_descriptor = next(
                item
                for item in baseline_report["artifacts"]
                if isinstance(item, dict)
                and item.get("captureKind")
                == self.bridge.RADAR_PUBLISHER_IMAGE_KIND
            )
            image_path = self.bridge.PROJECT_ROOT / image_descriptor["storageRef"]
            original_image = image_path.read_bytes()
            forged = bytearray(original_image)
            forged[-1] ^= 1
            image_path.write_bytes(bytes(forged))
            report_path.write_bytes(baseline_bytes + b" ")
            forged_report_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
            forged_refresh = (
                self.bridge.reconcile_completed_radar_batch_report_digests()
            )
            after_forgery = self.bridge.find_mission(completed["id"])

        self.assertNotEqual(baseline_digest, forged_report_digest)
        self.assertEqual(0, forged_refresh)
        self.assertEqual(
            baseline_digest,
            after_forgery["radarBatchReportCommit"]["reportDigest"],
        )


if __name__ == "__main__":
    unittest.main()
