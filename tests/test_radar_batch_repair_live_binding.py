from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(name: str = "radar_batch_repair_live_binding_bridge"):
    spec = importlib.util.spec_from_file_location(name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarBatchRepairLiveBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.bridge._invalidate_missions_read_cache()
        with self.bridge.RATE_LIMIT_LOCK:
            self.bridge.RATE_LIMIT_STATE.clear()

    def runtime(self, temp_dir: str) -> ExitStack:
        root = Path(temp_dir)
        runtime = root / "data" / "runtime"
        stack = ExitStack()
        stack.enter_context(mock.patch.object(self.bridge, "PROJECT_ROOT", root))
        stack.enter_context(mock.patch.object(self.bridge, "RUNTIME_DIR", runtime))
        stack.enter_context(
            mock.patch.object(self.bridge, "MISSIONS_PATH", runtime / "missions.json")
        )
        stack.enter_context(
            mock.patch.object(self.bridge, "AUDIT_PATH", runtime / "audit.jsonl")
        )
        stack.enter_context(
            mock.patch.object(self.bridge, "OPERATOR_MODE_PATH", runtime / "operator.json")
        )
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                runtime / "dashboard-workflow-settings.json",
            )
        )
        stack.enter_context(
            mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", runtime / "reports")
        )
        self.bridge._invalidate_missions_read_cache()
        return stack

    @staticmethod
    def urls() -> list[str]:
        return [
            "https://alpha.example.com/radar-one",
            "https://bravo.example.org/radar-two",
            "https://charlie.example.net/radar-three",
            "https://delta.example.com/radar-four",
            "https://echo.example.org/radar-five",
        ]

    def entries(self, urls: list[str] | None = None) -> list[dict]:
        selected = list(urls or self.urls())
        checked_at = self.bridge.utc_now()
        return [
            {
                "toolName": f"Radar Tool {index}",
                "toolKind": "indicator",
                "platform": "mt5",
                "category": "trend",
                "version": "1.0",
                "summaryTh": f"เครื่องมือทดสอบหมายเลข {index}",
                "sourceTitle": f"Public source {index}",
                "sourceUrl": url,
                "publishedAt": None,
                "checkedAt": checked_at,
                "verificationStatus": "verified",
                "availability": "public",
                "eaReadiness": "needs_clarification",
                "missingRules": ["ต้องทดสอบก่อนใช้งาน"],
                "sourceLimitations": ["ข้อมูลจากหน้าสาธารณะ"],
                "screenshot": {
                    "available": False,
                    "status": "not_available",
                    "attachmentId": None,
                    "artifactRef": None,
                },
            }
            for index, url in enumerate(selected, start=1)
        ]

    def scheduled_radar(self) -> tuple[dict, str, str]:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        slot_key = f"indicatorScoutSchedule:{today}:0900"
        response = self.bridge.run_dashboard_workflow_action(
            "left_audit_crystals",
            {
                "actionId": "discover_new_indicators",
                "form": {},
                "idempotencyKey": f"dashboard-schedule:{slot_key}",
            },
            trusted_trigger_source="schedule",
        )
        return response["mission"], slot_key, today

    def write_final_and_manifest(
        self,
        temp_dir: str,
        urls: list[str],
        *,
        run_id: str = "run-radar-live-binding",
    ) -> tuple[str, str]:
        artifact_reference = f"data/runtime/codex-runs/{run_id}.final.md"
        artifact_path = Path(temp_dir) / artifact_reference
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        entries_text = json.dumps(
            self.entries(urls),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        artifact_path.write_text(
            "\n".join(("# Radar result", "สำเร็จ", f"- entries: {entries_text}")),
            encoding="utf-8",
        )

        child_rows = [
            {
                "url": url,
                "durationMs": 10 + index,
                "exitCode": 0,
                "completedEventId": f"radar-open-{index}",
                "completedEventDigest": hashlib.sha256(
                    f"radar-open-{index}:{url}".encode("utf-8")
                ).hexdigest(),
                "source": "posthoc_open_verification",
            }
            for index, url in enumerate(urls[1:], start=1)
        ]
        required_url_digest = hashlib.sha256(
            json.dumps(
                urls,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        manifest = {
            "schemaVersion": "metafx-radar-url-open-verification-v1",
            "verificationType": "posthoc_open_verification",
            "resultProfile": "radar_website_tool",
            "runId": run_id,
            "requiredUrlCount": len(urls),
            "requiredUrlDigest": required_url_digest,
            "mainRequiredOpenCount": 1,
            "mainRequiredOpenIndexes": [0],
            "posthocVerificationCount": len(child_rows),
            "rows": child_rows,
        }
        manifest_reference = (
            f"data/runtime/codex-runs/{run_id}.url-open-verification.json"
        )
        (Path(temp_dir) / manifest_reference).write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        return artifact_reference, manifest_reference

    def failed_live_record(self, temp_dir: str) -> tuple[dict, str, str, str, str]:
        mission, slot_key, today = self.scheduled_radar()
        urls = self.urls()
        artifact_reference, manifest_reference = self.write_final_and_manifest(
            temp_dir,
            urls,
        )
        result = {
            "ok": True,
            "status": "completed",
            "workStatus": "completed",
            "contractFields": [
                {
                    "field": "entries",
                    "value": json.dumps(self.entries(urls), ensure_ascii=False),
                }
            ],
            "evidence": [
                {"label": f"source-{index}", "url": url, "note": "opened"}
                for index, url in enumerate(urls, start=1)
            ],
            "evidenceKinds": [
                "source_url",
                "source_title",
                "checked_at",
                "ea_readiness",
                "public_availability_status",
            ],
            "webSearchUsed": True,
            "webSearchEvidenceVerified": True,
        }
        output_receipt = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            result,
        )
        self.assertFalse(output_receipt["valid"], output_receipt)
        self.assertEqual(
            output_receipt["entryErrors"],
            ["daily_batch_requires_exactly_6_entries"],
        )

        manifest_required_digest = hashlib.sha256(
            json.dumps(
                urls,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        open_receipt = {
            "schemaVersion": "radar-corrective-open-verification-receipt-v1",
            "applicable": True,
            "valid": False,
            "failureCode": "radar_corrective_open_verification_invalid",
            "requiredUrlCount": len(urls),
            "requiredUrlDigest": self.bridge.payload_digest(urls),
            "manifestRequiredUrlDigest": manifest_required_digest,
            "candidateUrlSetMatched": True,
            "missingUrlVerificationCount": len(urls) - 1,
            "mainRequiredOpenIndexes": [],
            "manifestArtifact": None,
            "manifestDigest": None,
            "manifestVerified": False,
            "requiredUrlCoverageVerified": False,
            "verifications": [],
        }
        report_id = "auto-report-radar-live-binding"
        failed = copy.deepcopy(mission)
        failed.update(
            {
                "status": "failed",
                "phase": "auto_guarded_radar_corrective_open_verification_invalid",
                "workStatus": "radar_corrective_open_verification_invalid",
                "errorCode": "radar_corrective_open_verification_invalid",
                "artifactPath": artifact_reference,
                "reportIds": [report_id],
                "evidence": copy.deepcopy(result["evidence"]),
                "workflowOutputContract": output_receipt,
                "correctiveOpenVerificationReceipt": copy.deepcopy(open_receipt),
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
            }
        )
        failed["execution"].update(
            {
                "dispatchState": "failed",
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
                "correctiveOpenVerificationReceipt": copy.deepcopy(open_receipt),
            }
        )
        self.bridge.replace_mission(failed)
        self.bridge.create_report(
            {
                "id": report_id,
                "type": "indicator_scout_report",
                "title": "Blocked Radar live-style batch",
                "summary": "Five verified items are not a completed daily batch.",
                "ownerAgentId": failed.get("owner"),
                "linkedMissionId": failed["id"],
                "linkedPropId": "left_audit_crystals",
                "status": "blocked",
                "metrics": {"workflowOutput": output_receipt},
                "evidence": copy.deepcopy(result["evidence"]),
                "artifacts": [artifact_reference],
                "risks": ["radar_corrective_open_verification_invalid"],
                "workflowContext": failed.get("workflowContext"),
            }
        )
        self.bridge._dashboard_workflow_update_schedule_state(
            "indicatorScoutSchedule",
            {
                "lastMissionId": failed["id"],
                "lastSlotKey": slot_key,
                "lastAttemptSlotKey": slot_key,
                "dailyExecutionDate": today,
                "dailyExecutionCount": 1,
                "dailyExecutionSlotKeys": [slot_key],
            },
        )
        return failed, slot_key, today, artifact_reference, manifest_reference

    def candidate(self, mission: dict, today: str) -> dict | None:
        return self.bridge._scheduled_radar_batch_completion_repair_candidate(
            mission,
            self.bridge.load_dashboard_workflow_settings(),
            today,
        )

    def test_exact_live_style_record_requeues_same_mission_and_daily_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            failed, slot_key, today, _artifact, _manifest = self.failed_live_record(
                temp_dir
            )
            candidate = self.candidate(failed, today)
            before = copy.deepcopy(
                self.bridge.load_dashboard_workflow_settings()[
                    "indicatorScoutSchedule"
                ]
            )
            repaired_count = (
                self.bridge.reconcile_current_day_public_research_output_repairs()
            )
            repaired = self.bridge.find_mission(failed["id"])
            after = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        self.assertIsNotNone(candidate)
        self.assertEqual(repaired_count, 1)
        self.assertEqual(repaired["id"], failed["id"])
        self.assertEqual(repaired["idempotencyKey"], failed["idempotencyKey"])
        self.assertEqual(
            repaired["workflowContext"]["executionReservation"],
            failed["workflowContext"]["executionReservation"],
        )
        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(repaired["radarBatchRepair"]["originalSlotKey"], slot_key)
        self.assertFalse(
            repaired["radarBatchRepair"]["dailyReservationCountIncremented"]
        )
        self.assertFalse(repaired["radarBatchRepair"]["newDailyReservation"])
        self.assertEqual(before["dailyExecutionCount"], 1)
        self.assertEqual(after["dailyExecutionCount"], 1)
        self.assertEqual(before["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(after["dailyExecutionSlotKeys"], [slot_key])

    def test_missing_or_tampered_report_is_rejected(self) -> None:
        cases = ("missing", "wrong_mission", "wrong_artifact", "ready_status")
        for case in cases:
            with (
                self.subTest(case=case),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                failed, _slot, today, artifact_reference, _manifest = (
                    self.failed_live_record(temp_dir)
                )
                report_id = failed["reportIds"][0]
                report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json"
                if case == "missing":
                    report_path.unlink()
                else:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    if case == "wrong_mission":
                        report["linkedMissionId"] = "mission-other"
                    elif case == "wrong_artifact":
                        report["artifacts"] = [
                            "data/runtime/codex-runs/run-other.final.md"
                        ]
                    else:
                        report["status"] = "ready"
                    report_path.write_text(
                        json.dumps(
                            report,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        encoding="utf-8",
                    )

                candidate = self.candidate(failed, today)

            self.assertIsNone(
                candidate,
                f"{case} report must not authorize recovery for {artifact_reference}",
            )

    def test_tampered_artifact_url_order_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            failed, _slot, today, artifact_reference, _manifest = (
                self.failed_live_record(temp_dir)
            )
            swapped = self.urls()
            swapped[0], swapped[1] = swapped[1], swapped[0]
            artifact_path = Path(temp_dir) / artifact_reference
            entries_text = json.dumps(
                self.entries(swapped),
                ensure_ascii=False,
                separators=(",", ":"),
            )
            artifact_path.write_text(
                "\n".join(("# Radar result", "สำเร็จ", f"- entries: {entries_text}")),
                encoding="utf-8",
            )

            candidate = self.candidate(failed, today)

        self.assertIsNone(candidate)

    def test_requeued_source_artifact_digest_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            failed, _slot, today, artifact_reference, _manifest = (
                self.failed_live_record(temp_dir)
            )
            candidate = self.candidate(failed, today)
            self.assertIsNotNone(candidate)
            repaired = copy.deepcopy(failed)
            self.assertTrue(
                self.bridge._apply_scheduled_radar_batch_completion_repair(
                    repaired,
                    candidate,
                    requeued_at=self.bridge.utc_now(),
                    failure_snapshot=failed,
                )
            )
            valid_state, valid_error = (
                self.bridge._radar_batch_completion_repair_state(repaired)
            )
            artifact_path = Path(temp_dir) / artifact_reference
            artifact_path.write_text(
                artifact_path.read_text(encoding="utf-8") + "\n# tampered",
                encoding="utf-8",
            )
            tampered_state, tampered_error = (
                self.bridge._radar_batch_completion_repair_state(repaired)
            )

        self.assertIsNotNone(valid_state)
        self.assertIsNone(valid_error)
        self.assertIsNone(tampered_state)
        self.assertEqual(
            tampered_error,
            "radar_batch_completion_repair_invalid",
        )

    def test_tampered_manifest_digest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            failed, _slot, today, _artifact, manifest_reference = (
                self.failed_live_record(temp_dir)
            )
            manifest_path = Path(temp_dir) / manifest_reference
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["requiredUrlDigest"] = "0" * 64
            manifest_path.write_text(
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )

            candidate = self.candidate(failed, today)

        self.assertIsNone(candidate)


if __name__ == "__main__":
    unittest.main()
