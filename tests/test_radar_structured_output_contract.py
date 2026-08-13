from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("radar_structured_contract_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("bridge module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarStructuredOutputContractTests(unittest.TestCase):
    FIXED_CHECKED_AT = "2026-08-12T04:00:00Z"

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()
        cls.procedure = cls.bridge.equipment_action_profile(
            "left_audit_crystals",
            "discover_new_indicators",
        )

    def mission(self, *, max_items: int = 6) -> dict:
        return {
            "id": "mission-radar-structured",
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
                "coordinationMode": self.bridge.DASHBOARD_WORKFLOW_COORDINATION_MODE,
                "source": None,
                "agentTransfer": None,
                "inputs": {"maxItems": max_items},
                "inputDigest": "0" * 64,
                "submittedAt": "2026-08-12T01:00:00Z",
                "triggerSource": "manual",
                "pluginProcedure": self.procedure,
            },
        }

    @staticmethod
    def entry(
        *,
        name: str = "Example Trend Tool",
        source_url: str = "https://example.com/tools/trend",
        screenshot: dict | None = None,
    ) -> dict:
        return {
            "toolName": name,
            "toolKind": "indicator",
            "platform": "mt4",
            "category": "trend",
            "version": "1.0",
            "summaryTh": "สรุปจากเอกสารสาธารณะที่ตรวจแล้ว",
            "sourceTitle": "Public tool documentation",
            "sourceUrl": source_url,
            "publishedAt": None,
            # Keep the evidence timestamp inside the read model's pinned
            # Bangkok day. Wall-clock time makes this regression start failing
            # once the real clock moves past the fixture's fixed now_local.
            "checkedAt": RadarStructuredOutputContractTests.FIXED_CHECKED_AT,
            "verificationStatus": "partially_verified",
            "availability": "public",
            "eaReadiness": "not_ea_ready",
            "missingRules": [],
            "sourceLimitations": ["ยังไม่มีผลทดสอบที่ทำซ้ำได้"],
            "screenshot": screenshot
            or {
                "available": False,
                "status": "not_available",
                "attachmentId": None,
                "artifactRef": None,
            },
        }

    def result(self, entries: list[dict], *, evidence_urls: list[str] | None = None) -> dict:
        urls = evidence_urls or sorted({entry["sourceUrl"] for entry in entries})
        return {
            "contractFields": [
                {
                    "field": "entries",
                    "value": json.dumps(entries, ensure_ascii=False, sort_keys=True),
                }
            ],
            "evidenceKinds": list(self.procedure["evidenceRequired"]),
            "evidence": [
                {"label": f"Source {index}", "url": url, "note": "Read-only check"}
                for index, url in enumerate(urls, start=1)
            ],
        }

    def validate(self, entries: list[dict], *, max_items: int = 6, evidence_urls=None) -> dict:
        with mock.patch.object(self.bridge, "_radar_existing_catalog_fingerprints", return_value=set()):
            return self.bridge.validate_dashboard_workflow_output_contract(
                self.mission(max_items=max_items),
                self.result(entries, evidence_urls=evidence_urls),
            )

    def test_valid_multi_item_result_is_persistable_as_metrics_entries(self) -> None:
        first = self.entry()
        first.update({
            "recordId": "worker-spoof",
            "duplicateFingerprint": "f" * 24,
            "duplicateStatus": "duplicate",
            "duplicateScope": "local_report_catalog",
        })
        second = self.entry(
            name="Example EA Tool",
            source_url="https://example.com/tools/ea",
        )
        second["toolKind"] = "ea"
        second["eaReadiness"] = "needs_clarification"
        contract = self.validate([first, second])
        self.assertTrue(contract["valid"], contract)
        metrics = self.bridge.dashboard_workflow_output_metrics(contract)
        self.assertEqual(len(metrics["entries"]), 2)
        normalized = metrics["entries"][0]
        self.assertNotEqual(normalized["recordId"], "worker-spoof")
        self.assertNotEqual(normalized["duplicateFingerprint"], "f" * 24)
        self.assertEqual(normalized["duplicateStatus"], "unique")
        self.assertEqual(normalized["duplicateScope"], "none")

    def test_same_result_duplicate_is_computed_by_backend(self) -> None:
        contract = self.validate([self.entry(), self.entry()])
        self.assertTrue(contract["valid"], contract)
        entries = self.bridge.dashboard_workflow_output_metrics(contract)["entries"]
        self.assertEqual(entries[0]["duplicateStatus"], "unique")
        self.assertEqual(entries[0]["duplicateScope"], "none")
        self.assertEqual(entries[1]["duplicateStatus"], "duplicate")
        self.assertEqual(entries[1]["duplicateScope"], "current_result_batch")

        read_model = self.bridge._radar_website_tool_read_model(
            [{
                "id": "report-radar-same-batch",
                "type": "indicator_scout_report",
                "linkedPropId": "left_audit_crystals",
                "workflowContext": {
                    "propId": "left_audit_crystals",
                    "actionId": "discover_new_indicators",
                },
                "createdAt": "2026-08-12T01:00:00Z",
                "metrics": {"entries": entries},
            }],
            settings={},
            now_local=self.bridge.datetime(2026, 8, 12, 12, 0),
        )
        self.assertEqual(
            read_model["todayEntries"][1]["duplicateScope"],
            "current_result_batch",
        )

    def test_existing_catalog_duplicate_is_computed_by_backend(self) -> None:
        entry = self.entry()
        fingerprint = self.bridge._radar_entry_fingerprint(
            entry["sourceUrl"], entry["toolName"], entry["platform"], entry["version"]
        )
        with mock.patch.object(
            self.bridge,
            "_radar_existing_catalog_fingerprints",
            return_value={fingerprint},
        ):
            contract = self.bridge.validate_dashboard_workflow_output_contract(
                self.mission(), self.result([entry])
            )
        self.assertTrue(contract["valid"], contract)
        normalized = self.bridge.dashboard_workflow_output_metrics(contract)["entries"][0]
        self.assertEqual(normalized["duplicateStatus"], "duplicate")
        self.assertEqual(normalized["duplicateScope"], "local_report_catalog")

    def test_count_public_url_enums_and_lists_fail_closed_per_entry(self) -> None:
        self.assertFalse(self.validate([], max_items=6)["valid"])
        self.assertFalse(self.validate([self.entry(), self.entry()], max_items=1)["valid"])

        cases = {
            "private_url": {"sourceUrl": "http://127.0.0.1/tool"},
            "evidence_mismatch": {"sourceUrl": "https://example.com/not-cited"},
            "invalid_enum": {"toolKind": "robot"},
            "scalar_limitations": {"sourceLimitations": "not an array"},
        }
        for name, updates in cases.items():
            entry = self.entry()
            entry.update(updates)
            evidence_urls = (
                ["https://example.com/tools/trend"]
                if name == "evidence_mismatch"
                else None
            )
            with self.subTest(name=name):
                contract = self.validate([entry], evidence_urls=evidence_urls)
                self.assertFalse(contract["valid"])
                self.assertTrue(contract["entryErrors"])

    def test_future_checked_at_is_rejected_before_persistence(self) -> None:
        entry = self.entry()
        entry["checkedAt"] = "2999-01-01T00:00:00Z"
        contract = self.validate([entry])
        self.assertFalse(contract["valid"])
        self.assertIn("entry_1_invalid_timestamp", contract["entryErrors"])

    def test_report_screenshot_requires_explicit_matching_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "radar.png"
            image_path.write_bytes(b"image-test")
            report = {
                "id": "report-radar-image",
                "type": "indicator_scout_report",
                "linkedPropId": "left_audit_crystals",
                "workflowContext": {
                    "propId": "left_audit_crystals",
                    "actionId": "discover_new_indicators",
                },
                "createdAt": "2026-08-12T01:00:00Z",
                "artifacts": ["data/runtime/codex-runs/radar.png"],
                "metrics": {"entries": [self.entry()]},
            }
            with mock.patch.object(
                self.bridge,
                "resolve_report_image_artifact",
                return_value=(image_path, "image/png", "Radar image"),
            ):
                unmatched = self.bridge._radar_report_entries(report)[0]
                report["metrics"]["entries"][0]["screenshot"] = {
                    "available": True,
                    "status": "verified_result_artifact",
                    "attachmentId": None,
                    "artifactRef": "data/runtime/codex-runs/radar.png",
                }
                matched = self.bridge._radar_report_entries(report)[0]
        self.assertFalse(unmatched["screenshot"]["available"])
        self.assertIsNone(unmatched["screenshot"]["attachmentId"])
        self.assertEqual(unmatched["screenshotStatus"], "not_available")
        self.assertTrue(matched["screenshot"]["available"])
        self.assertRegex(matched["screenshot"]["attachmentId"], r"^image-[0-9a-f]{20}$")
        self.assertEqual(matched["screenshotStatus"], "verified_report_attachment")

    def test_prompt_and_input_contract_require_entries_and_cap_max_items_at_six(self) -> None:
        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["discover_new_indicators"]
        form = self.bridge._sanitize_dashboard_workflow_form(action, {"maxItems": 999})
        prompt = self.bridge._workflow_prompt(
            "discover_new_indicators",
            form,
            None,
            self.procedure,
        )
        self.assertEqual(form["maxItems"], 6)
        self.assertIn("เพียงหนึ่งรายการชื่อ entries", prompt)
        self.assertIn("Backend จะคำนวณ", prompt)
        self.assertIn("ห้ามนำภาพของรายการหนึ่งไปใช้กับอีกรายการ", prompt)


if __name__ == "__main__":
    unittest.main()
