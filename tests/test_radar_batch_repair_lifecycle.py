from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarBatchRepairLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module(
            "radar_batch_repair_lifecycle_bridge",
            BRIDGE_PATH,
        )
        cls.runner = load_module(
            "radar_batch_repair_lifecycle_runner",
            RUNNER_PATH,
        )

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
            mock.patch.object(self.bridge, "PROJECT_RUNTIME_DIR", runtime)
        )
        stack.enter_context(
            mock.patch.object(self.bridge, "MISSIONS_PATH", runtime / "missions.json")
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
        self.bridge._invalidate_missions_read_cache()
        return stack

    def scheduled_radar(self) -> tuple[dict, str]:
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
        return response["mission"], slot_key

    def prime_daily_schedule(self, mission: dict, slot_key: str) -> None:
        today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
        self.bridge._dashboard_workflow_update_schedule_state(
            "indicatorScoutSchedule",
            {
                "lastMissionId": mission["id"],
                "lastSlotKey": slot_key,
                "lastAttemptSlotKey": slot_key,
                "dailyExecutionDate": today,
                "dailyExecutionCount": 1,
                "dailyExecutionSlotKeys": [slot_key],
            },
        )

    @staticmethod
    def urls() -> list[str]:
        return [
            "https://alpha.example.com/radar-one",
            "https://bravo.example.org/radar-two",
            "https://charlie.example.net/radar-three",
            "https://delta.example.com/radar-four",
            "https://echo.example.org/radar-five",
            "https://foxtrot.example.net/radar-six",
        ]

    def entries(self) -> list[dict]:
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
            for index, url in enumerate(self.urls(), start=1)
        ]

    def write_artifact(
        self,
        temp_dir: str,
        name: str,
        payload: object,
    ) -> str:
        reference = f"data/runtime/codex-runs/{name}"
        path = Path(temp_dir) / reference
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        return reference

    def make_running(self, mission: dict, lease_id: str) -> dict:
        running = copy.deepcopy(mission)
        running.update({
            "status": "running",
            "phase": "auto_guarded_running",
            "workStatus": None,
            "errorCode": None,
            "attemptCount": 1,
        })
        execution = (
            copy.deepcopy(running.get("execution"))
            if isinstance(running.get("execution"), dict)
            else {}
        )
        execution.update({
            "dispatchState": "running",
            "workerId": f"worker-{lease_id}",
            "leaseId": lease_id,
            "processStarted": True,
            "workingDirectory": "workspace",
            "writeRoots": [],
            "controlPlaneWritable": False,
            "webSearchEnabled": True,
            "webSearchUsed": True,
            "webSearchEvidenceVerified": False,
        })
        running["execution"] = execution
        self.bridge.replace_mission(running)
        return running

    def invalid_zero_result(self, artifact_reference: str) -> dict:
        return {
            "ok": False,
            "status": "invalid_output",
            "workStatus": "invalid_output",
            "finalMessage": "Radar strict-six result was incomplete.",
            "structuredOutputError": (
                "completed daily Radar result requires exactly six unique "
                "public evidence URLs"
            ),
            "contractFields": [],
            "evidence": [],
            "evidenceKinds": [],
            "artifacts": {"final": artifact_reference},
            "processStarted": True,
            "processTreeTerminated": True,
            "workingDirectory": "workspace",
            "writeRoots": [],
            "controlPlaneWritable": False,
            "webSearchEnabled": True,
            "webSearchMode": "live",
            "webSearchUsed": True,
            "webSearchEvidenceVerified": False,
        }

    def apply_batch_repair(
        self,
        mission: dict,
        artifact_reference: str,
    ) -> dict:
        artifact_path = self.bridge.PROJECT_ROOT / artifact_reference
        candidate = {
            "artifactPath": artifact_reference,
            "artifactDigest": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            "observedItemCount": 0,
            "failureReasonCode": "radar_batch_attempt_incomplete",
        }
        applied = self.bridge._apply_scheduled_radar_batch_completion_repair(
            mission,
            candidate,
            requeued_at=self.bridge.utc_now(),
        )
        self.assertTrue(applied)
        return mission

    def apply_v2_retry(
        self,
        mission: dict,
        artifact_reference: str,
    ) -> dict:
        urls = self.urls()
        candidate = {
            "artifactPath": artifact_reference,
            "urls": urls,
            "candidateBlock": self.bridge._radar_evidence_candidate_block(urls),
        }
        applied = self.bridge._apply_scheduled_radar_evidence_open_retry(
            mission,
            candidate,
            requeued_at=self.bridge.utc_now(),
        )
        self.assertTrue(applied)
        return mission

    def valid_six_result(
        self,
        temp_dir: str,
        *,
        final_name: str,
        run_id: str,
    ) -> dict:
        urls = self.urls()
        final_reference = self.write_artifact(
            temp_dir,
            final_name,
            {"status": "completed", "evidence": urls},
        )
        manifest = {
            "schemaVersion": "metafx-radar-url-open-verification-v1",
            "verificationType": "posthoc_open_verification",
            "resultProfile": "radar_website_tool",
            "runId": run_id,
            "requiredUrlCount": 6,
            "requiredUrlDigest": hashlib.sha256(
                json.dumps(
                    urls,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            "mainRequiredOpenCount": 6,
            "mainRequiredOpenIndexes": list(range(6)),
            "posthocVerificationCount": 0,
            "rows": [],
        }
        manifest_bytes = json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        manifest_reference = (
            f"data/runtime/codex-runs/{run_id}.url-open-verification.json"
        )
        manifest_path = Path(temp_dir) / manifest_reference
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(manifest_bytes)
        return {
            "ok": True,
            "status": "completed",
            "workStatus": "completed",
            "finalMessage": "Radar completed six verified public entries.",
            "contractFields": [{
                "field": "entries",
                "value": json.dumps(self.entries(), ensure_ascii=False),
            }],
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
            "artifacts": {"final": final_reference},
            "processStarted": True,
            "processTreeTerminated": True,
            "workingDirectory": "workspace",
            "writeRoots": [],
            "controlPlaneWritable": False,
            "webSearchEnabled": True,
            "webSearchMode": "live",
            "webSearchUsed": True,
            "webSearchEvidenceVerified": True,
            "correctiveOpenVerificationCount": 0,
            "correctiveOpenVerifications": [],
            "correctiveOpenVerificationArtifact": manifest_reference,
            "correctiveOpenVerificationDigest": hashlib.sha256(
                manifest_bytes
            ).hexdigest(),
        }

    def test_fresh_strict_six_zero_evidence_seeds_same_mission_batch_repair(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            failure_reference = self.write_artifact(
                temp_dir,
                "fresh-zero.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            lease_id = "lease-fresh-zero"
            self.make_running(mission, lease_id)
            with mock.patch.object(self.bridge, "create_report") as create_report:
                requeued = self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    self.invalid_zero_result(failure_reference),
                )

            stored = self.bridge.find_mission(mission["id"])

        create_report.assert_not_called()
        self.assertIsNotNone(requeued)
        self.assertEqual(stored["id"], mission["id"])
        self.assertEqual(stored["idempotencyKey"], mission["idempotencyKey"])
        self.assertEqual(stored["status"], "queued")
        self.assertEqual(stored["reportIds"], [])
        self.assertEqual(stored["radarBatchRepair"]["lastObservedItemCount"], 0)
        self.assertFalse(stored["radarBatchRepair"]["newDailyReservation"])
        self.assertEqual(
            stored["radarBatchRepair"]["originalSlotKey"],
            slot_key,
        )

    def test_exhausted_v2_zero_evidence_transitions_to_batch_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            source_reference = self.write_artifact(
                temp_dir,
                "v2-source.final.md",
                {
                    "status": "completed",
                    "evidence": [
                        {"url": url} for url in self.urls()
                    ],
                },
            )
            mission = self.apply_v2_retry(mission, source_reference)
            self.bridge.replace_mission(mission)
            failure_reference = self.write_artifact(
                temp_dir,
                "v2-zero.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            lease_id = "lease-v2-zero"
            self.make_running(mission, lease_id)
            with mock.patch.object(self.bridge, "create_report") as create_report:
                requeued = self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    self.invalid_zero_result(failure_reference),
                )
            stored = self.bridge.find_mission(mission["id"])

        create_report.assert_not_called()
        self.assertIsNotNone(requeued)
        self.assertEqual(stored["id"], mission["id"])
        self.assertEqual(stored["status"], "queued")
        self.assertEqual(stored["correctiveRetry"]["attemptCount"], 1)
        self.assertEqual(stored["correctiveRetry"]["remainingAttempts"], 0)
        self.assertEqual(stored["radarBatchRepair"]["lastObservedItemCount"], 0)
        self.assertEqual(
            stored["detail"].count(
                self.bridge.RADAR_EVIDENCE_CANDIDATE_BLOCK_START
            ),
            1,
        )

    def test_report_persist_failure_halts_batch_without_duplicate_rerun(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            failure_reference = self.write_artifact(
                temp_dir,
                "batch-source.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            self.bridge.replace_mission(mission)
            lease_id = "lease-report-failure"
            self.make_running(mission, lease_id)
            valid_result = self.valid_six_result(
                temp_dir,
                final_name="batch-success-before-report-failure.final.md",
                run_id="run-batch-report-failure",
            )
            create_report = mock.Mock(side_effect=OSError("disk unavailable"))
            with mock.patch.object(
                self.bridge,
                "create_report",
                create_report,
            ), mock.patch.object(
                self.bridge,
                "queue_radar_publisher_image_enrichment",
            ):
                failed = self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    valid_result,
                )
                duplicate_finish = self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    valid_result,
                )
                recovered_count = (
                    self.bridge.reconcile_current_day_public_research_output_repairs()
                )
            stored = self.bridge.find_mission(mission["id"])

        self.assertEqual(create_report.call_count, 1)
        self.assertIsNone(duplicate_finish)
        self.assertEqual(recovered_count, 0)
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(stored["status"], "failed")
        self.assertEqual(stored["errorCode"], "report_persist_failed")
        self.assertEqual(stored["reportIds"], [])
        self.assertEqual(stored["radarBatchRepair"]["status"], "halted")
        self.assertIsNone(
            stored["radarBatchRepair"].get("successfulReportId")
        )
        self.assertIsNone(
            stored["radarBatchRepair"].get("successfulBatchArtifact")
        )
        self.assertFalse(stored["execution"]["automaticRetry"])

    def test_missing_batch_artifact_is_rejected_without_crash_or_duplicate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            failure_reference = self.write_artifact(
                temp_dir,
                "missing-after-queue.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            mission["status"] = "failed"
            mission["phase"] = "auto_guarded_invalid_output"
            mission["workStatus"] = "invalid_output"
            mission["execution"].update({
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
            })
            self.bridge.replace_mission(mission)
            (Path(temp_dir) / failure_reference).unlink()

            state, state_error = self.bridge._radar_batch_completion_repair_state(
                mission
            )
            repaired_count = (
                self.bridge.reconcile_current_day_public_research_output_repairs()
            )
            stored = self.bridge.find_mission(mission["id"])

        self.assertIsNone(state)
        self.assertEqual(state_error, "radar_batch_completion_repair_invalid")
        self.assertEqual(repaired_count, 0)
        self.assertEqual(stored["id"], mission["id"])
        self.assertEqual(stored["status"], "failed")

    def test_live_sized_batch_repair_prompt_stays_below_runner_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _slot_key = self.scheduled_radar()
            base_detail = str(mission.get("detail") or "").rstrip()
            live_detail_chars = 7_286
            self.assertLess(len(base_detail), live_detail_chars)
            mission["detail"] = (
                f"{base_detail}\n"
                + "x" * (live_detail_chars - len(base_detail) - 1)
            )
            failure_reference = self.write_artifact(
                temp_dir,
                "live-sized-prompt.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)

            bounded = self.runner.bound_mission_prompt(
                mission["detail"],
                "radar_website_tool",
                execution_mode="auto_guarded",
                radar_required_open_urls=[],
            )

        self.assertEqual(bounded, mission["detail"])
        self.assertEqual(
            self.runner.radar_daily_batch_target_count(mission["detail"]),
            6,
        )
        self.assertLess(
            len(mission["detail"]),
            self.runner.MISSION_PROMPT_MAX_CHARS,
        )

    def test_successful_report_commit_marks_batch_and_mission_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            failure_reference = self.write_artifact(
                temp_dir,
                "success-source.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            self.bridge.replace_mission(mission)
            lease_id = "lease-successful-commit"
            self.make_running(mission, lease_id)
            valid_result = self.valid_six_result(
                temp_dir,
                final_name="successful-batch.final.md",
                run_id="run-successful-batch",
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
            stored = self.bridge.find_mission(mission["id"])
            report_path = (
                self.bridge.RUNTIME_REPORTS_DIR
                / f"{stored['reportIds'][0]}.json"
            )
            report_exists = report_path.is_file()

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(stored["status"], "completed")
        self.assertEqual(stored["workStatus"], "completed")
        self.assertEqual(stored["radarBatchRepair"]["status"], "completed")
        self.assertEqual(len(stored["reportIds"]), 1)
        self.assertEqual(
            stored["radarBatchRepair"]["successfulReportId"],
            stored["reportIds"][0],
        )
        self.assertEqual(
            stored["radarBatchRepair"]["successfulBatchArtifact"],
            valid_result["artifacts"]["final"],
        )
        self.assertTrue(report_exists)

    def test_system_exit_after_report_write_recovers_same_mission_commit(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            before_schedule = copy.deepcopy(
                self.bridge.load_dashboard_workflow_settings()[
                    "indicatorScoutSchedule"
                ]
            )
            failure_reference = self.write_artifact(
                temp_dir,
                "crash-source.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            self.bridge.replace_mission(mission)
            lease_id = "lease-crash-after-report"
            self.make_running(mission, lease_id)
            valid_result = self.valid_six_result(
                temp_dir,
                final_name="crash-successful-batch.final.md",
                run_id="run-crash-successful-batch",
            )
            real_create_report = self.bridge.create_report

            def persist_then_exit(payload: dict) -> dict:
                real_create_report(payload)
                raise SystemExit("simulated process exit after Report persistence")

            with mock.patch.object(
                self.bridge,
                "create_report",
                side_effect=persist_then_exit,
            ), self.assertRaises(SystemExit):
                self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    valid_result,
                )
            pending = self.bridge.find_mission(mission["id"])
            pending_packet, pending_error = (
                self.bridge._pending_radar_batch_report_commit(pending)
            )
            report_id = pending["reportIds"][0]
            orphan_report_path = (
                self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json"
            )
            orphan_report_exists = orphan_report_path.is_file()

            recovered_count = (
                self.bridge.reconcile_pending_radar_batch_report_commits()
            )
            duplicate_recovery_count = (
                self.bridge.reconcile_pending_radar_batch_report_commits()
            )
            completed = self.bridge.find_mission(mission["id"])
            after_schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            reports = list(self.bridge.RUNTIME_REPORTS_DIR.glob("*.json"))

        self.assertIsNone(pending_error)
        self.assertIsNotNone(pending_packet)
        self.assertEqual(pending["status"], "running")
        self.assertEqual(
            pending["phase"],
            self.bridge.RADAR_BATCH_REPORT_COMMIT_PENDING_PHASE,
        )
        self.assertNotEqual(
            pending["radarBatchRepair"]["status"],
            "completed",
        )
        self.assertTrue(orphan_report_exists)
        self.assertEqual(recovered_count, 1)
        self.assertEqual(duplicate_recovery_count, 0)
        self.assertEqual(completed["id"], mission["id"])
        self.assertEqual(completed["idempotencyKey"], mission["idempotencyKey"])
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(
            completed["radarBatchRepair"]["status"],
            "completed",
        )
        self.assertEqual(
            completed["radarBatchRepair"]["successfulReportId"],
            report_id,
        )
        self.assertEqual(len(reports), 1)
        self.assertEqual(
            before_schedule["dailyExecutionCount"],
            after_schedule["dailyExecutionCount"],
        )
        self.assertEqual(
            before_schedule["dailyExecutionSlotKeys"],
            after_schedule["dailyExecutionSlotKeys"],
        )

    def test_system_exit_before_report_write_never_persists_false_completion(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            failure_reference = self.write_artifact(
                temp_dir,
                "pre-report-crash-source.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            self.bridge.replace_mission(mission)
            lease_id = "lease-crash-before-report"
            self.make_running(mission, lease_id)
            valid_result = self.valid_six_result(
                temp_dir,
                final_name="pre-report-crash-batch.final.md",
                run_id="run-pre-report-crash-batch",
            )
            with mock.patch.object(
                self.bridge,
                "create_report",
                side_effect=SystemExit("simulated pre-Report process exit"),
            ), self.assertRaises(SystemExit):
                self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    valid_result,
                )
            pending = self.bridge.find_mission(mission["id"])
            report_id = pending["reportIds"][0]
            report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json"
            report_missing_while_pending = not report_path.exists()

            recovered_count = (
                self.bridge.reconcile_pending_radar_batch_report_commits()
            )
            completed = self.bridge.find_mission(mission["id"])
            report_exists_after_recovery = report_path.is_file()

        self.assertTrue(report_missing_while_pending)
        self.assertEqual(pending["status"], "running")
        self.assertEqual(
            pending["workStatus"],
            self.bridge.RADAR_BATCH_REPORT_COMMIT_PENDING_STATUS,
        )
        self.assertNotEqual(
            pending["radarBatchRepair"]["status"],
            "completed",
        )
        self.assertEqual(recovered_count, 1)
        self.assertTrue(report_exists_after_recovery)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["id"], mission["id"])
        self.assertEqual(
            completed["radarBatchReportCommit"]["status"],
            "completed",
        )

    def test_concurrent_reconcilers_write_and_finalize_one_canonical_report(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            before_schedule = copy.deepcopy(
                self.bridge.load_dashboard_workflow_settings()[
                    "indicatorScoutSchedule"
                ]
            )
            failure_reference = self.write_artifact(
                temp_dir,
                "concurrent-commit-source.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            self.bridge.replace_mission(mission)
            lease_id = "lease-concurrent-report-commit"
            self.make_running(mission, lease_id)
            valid_result = self.valid_six_result(
                temp_dir,
                final_name="concurrent-successful-batch.final.md",
                run_id="run-concurrent-successful-batch",
            )
            with mock.patch.object(
                self.bridge,
                "create_report",
                side_effect=SystemExit("leave a durable pending commit"),
            ), self.assertRaises(SystemExit):
                self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    valid_result,
                )

            pending = self.bridge.find_mission(mission["id"])
            report_id = pending["reportIds"][0]
            report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json"
            real_create_report = self.bridge.create_report
            real_finalize = (
                self.bridge._finalize_pending_radar_batch_report_commit
            )
            real_commit = (
                self.bridge._persist_and_finalize_pending_radar_batch_report_commit
            )
            entry_barrier = threading.Barrier(2)
            counter_lock = threading.Lock()
            counters = {"create": 0, "finalize": 0}

            def counted_create(payload: dict) -> dict:
                with counter_lock:
                    counters["create"] += 1
                return real_create_report(payload)

            def counted_finalize(
                candidate_mission_id: str,
                candidate_lease_id: str,
                report: object,
            ) -> dict | None:
                with counter_lock:
                    counters["finalize"] += 1
                return real_finalize(
                    candidate_mission_id,
                    candidate_lease_id,
                    report,
                )

            def synchronized_commit(
                candidate_mission_id: str,
                candidate_lease_id: str,
            ) -> tuple[dict, dict, bool]:
                entry_barrier.wait(timeout=5)
                return real_commit(candidate_mission_id, candidate_lease_id)

            with mock.patch.object(
                self.bridge,
                "create_report",
                side_effect=counted_create,
            ), mock.patch.object(
                self.bridge,
                "_finalize_pending_radar_batch_report_commit",
                side_effect=counted_finalize,
            ), mock.patch.object(
                self.bridge,
                "_persist_and_finalize_pending_radar_batch_report_commit",
                side_effect=synchronized_commit,
            ), mock.patch.object(
                self.bridge,
                "queue_radar_publisher_image_enrichment",
            ):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures = [
                        pool.submit(
                            self.bridge.reconcile_pending_radar_batch_report_commits
                        )
                        for _index in range(2)
                    ]
                    results = [future.result(timeout=10) for future in futures]
                duplicate_count = (
                    self.bridge.reconcile_pending_radar_batch_report_commits()
                )

            completed = self.bridge.find_mission(mission["id"])
            after_schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            current_report_digest = hashlib.sha256(
                report_path.read_bytes()
            ).hexdigest()
            reports = list(self.bridge.RUNTIME_REPORTS_DIR.glob("*.json"))

        self.assertEqual(sorted(results), [0, 1])
        self.assertEqual(duplicate_count, 0)
        self.assertEqual(counters, {"create": 1, "finalize": 1})
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["reportIds"], [report_id])
        self.assertEqual(
            completed["radarBatchReportCommit"]["status"],
            "completed",
        )
        self.assertEqual(
            completed["radarBatchReportCommit"]["reportDigest"],
            current_report_digest,
        )
        self.assertEqual(len(reports), 1)
        self.assertEqual(
            before_schedule["dailyExecutionCount"],
            after_schedule["dailyExecutionCount"],
        )
        self.assertEqual(
            before_schedule["dailyExecutionSlotKeys"],
            after_schedule["dailyExecutionSlotKeys"],
        )

    def test_enrichment_and_startup_refresh_current_large_report_digest_fail_closed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            failure_reference = self.write_artifact(
                temp_dir,
                "enrichment-digest-source.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            self.bridge.replace_mission(mission)
            lease_id = "lease-enrichment-digest"
            self.make_running(mission, lease_id)
            valid_result = self.valid_six_result(
                temp_dir,
                final_name="enrichment-digest-success.final.md",
                run_id="run-enrichment-digest-success",
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
            report_id = completed["reportIds"][0]
            report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json"

            # Exercise the real publisher-enrichment report rewrite. Returning
            # no capture is valid optional enrichment and keeps all six source
            # entries while recording deterministic diagnostics.
            with mock.patch.object(
                self.bridge,
                "capture_publisher_og_image",
                return_value=None,
            ):
                self.bridge._run_radar_publisher_image_enrichment(report_id)
            enriched = self.bridge.find_mission(mission["id"])
            enriched_report = json.loads(report_path.read_text(encoding="utf-8"))
            enriched_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()

            # The live Report is already close to the former 40KB ceiling.
            # Valid JSON trailing whitespace preserves the exact parsed Report
            # while proving startup recovery accepts the dedicated 256KiB cap.
            report_bytes = report_path.read_bytes()
            minimum_large_size = 45_000
            report_path.write_bytes(
                report_bytes
                + b" " * max(1, minimum_large_size - len(report_bytes))
            )
            large_size = report_path.stat().st_size
            large_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
            stale_before_startup = self.bridge.find_mission(mission["id"])
            refreshed_count = (
                self.bridge.reconcile_completed_radar_batch_report_digests()
            )
            duplicate_refresh_count = (
                self.bridge.reconcile_completed_radar_batch_report_digests()
            )
            refreshed = self.bridge.find_mission(mission["id"])

            # A late duplicate worker completion must not demote the already
            # committed/enriched Mission or rewrite its deterministic Report.
            duplicate_finish = self.bridge.finish_auto_mission(
                mission["id"],
                lease_id,
                {"processStarted": True},
                valid_result,
            )
            after_duplicate = self.bridge.find_mission(mission["id"])

            # Startup sync rejects a semantically changed Report even when the
            # ID and filesystem path remain the same.
            tampered_report = copy.deepcopy(enriched_report)
            tampered_report["summary"] = "tampered summary"
            report_path.write_text(
                json.dumps(tampered_report, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            tampered_digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
            tampered_refresh_count = (
                self.bridge.reconcile_completed_radar_batch_report_digests()
            )
            after_tamper = self.bridge.find_mission(mission["id"])

        self.assertEqual(enriched["status"], "completed")
        self.assertEqual(
            enriched["radarBatchReportCommit"]["reportDigest"],
            enriched_digest,
        )
        self.assertGreater(large_size, 40_000)
        self.assertNotEqual(
            stale_before_startup["radarBatchReportCommit"]["reportDigest"],
            large_digest,
        )
        self.assertEqual(refreshed_count, 1)
        self.assertEqual(duplicate_refresh_count, 0)
        self.assertEqual(
            refreshed["radarBatchReportCommit"]["reportDigest"],
            large_digest,
        )
        self.assertIsNone(duplicate_finish)
        self.assertEqual(after_duplicate["status"], "completed")
        self.assertEqual(
            after_duplicate["radarBatchReportCommit"]["reportDigest"],
            large_digest,
        )
        self.assertNotEqual(tampered_digest, large_digest)
        self.assertEqual(tampered_refresh_count, 0)
        self.assertEqual(after_tamper["status"], "completed")
        self.assertEqual(
            after_tamper["radarBatchReportCommit"]["reportDigest"],
            large_digest,
        )

    def test_prior_day_active_batch_repair_blocks_new_daily_radar_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            self.prime_daily_schedule(mission, slot_key)
            failure_reference = self.write_artifact(
                temp_dir,
                "prior-day-active-repair.final.md",
                {"status": "invalid_output", "evidence": []},
            )
            mission = self.apply_batch_repair(mission, failure_reference)
            self.bridge.replace_mission(mission)
            self.bridge._save_dashboard_schedule_preference(
                "indicatorScoutSchedule",
                {
                    "enabled": True,
                    "times": ["09:00"],
                    "timezone": "Asia/Bangkok",
                },
            )
            old_day = datetime.strptime(
                slot_key.split(":")[1],
                "%Y-%m-%d",
            ).date()
            next_day_after_slot = datetime.combine(
                old_day + timedelta(days=1),
                datetime.min.time(),
                tzinfo=self.bridge.THAILAND_TIMEZONE,
            ).replace(hour=9, minute=1)
            indicator_job = tuple(
                job
                for job in self.bridge.DASHBOARD_WORKFLOW_SCHEDULE_JOBS
                if job.get("settingsKey") == "indicatorScoutSchedule"
            )
            with mock.patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SCHEDULE_JOBS",
                indicator_job,
            ):
                captured = self.bridge._dashboard_workflow_capture_due_slots(
                    next_day_after_slot
                )
            stored_settings = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            stored_missions = self.bridge.load_missions()

        self.assertEqual(captured, [])
        self.assertIsNone(stored_settings["pendingSlotKey"])
        self.assertEqual(
            stored_settings["dailyExecutionDate"],
            next_day_after_slot.date().isoformat(),
        )
        self.assertEqual(stored_settings["dailyExecutionCount"], 0)
        self.assertEqual(stored_settings["dailyExecutionSlotKeys"], [])
        self.assertEqual(
            stored_settings["carryForwardBlockDate"],
            next_day_after_slot.date().isoformat(),
        )
        self.assertEqual(
            stored_settings["carryForwardMissionId"],
            mission["id"],
        )
        self.assertEqual(len(stored_missions), 1)
        self.assertEqual(stored_missions[0]["id"], mission["id"])


if __name__ == "__main__":
    unittest.main()
