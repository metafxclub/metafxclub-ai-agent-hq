from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(name: str = "radar_daily_batch_corrective_retry_bridge"):
    spec = importlib.util.spec_from_file_location(name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarDailyBatchCorrectiveRetryTests(unittest.TestCase):
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
        stack.enter_context(mock.patch.object(self.bridge, "MISSIONS_PATH", runtime / "missions.json"))
        stack.enter_context(mock.patch.object(self.bridge, "AUDIT_PATH", runtime / "audit.jsonl"))
        stack.enter_context(mock.patch.object(self.bridge, "OPERATOR_MODE_PATH", runtime / "operator.json"))
        stack.enter_context(
            mock.patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SETTINGS_PATH",
                runtime / "dashboard-workflow-settings.json",
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

    def prior_day_scheduled_radar_completion_retry(
        self,
    ) -> tuple[dict, str, str]:
        current_day = datetime.now(self.bridge.THAILAND_TIMEZONE).date()
        prior_day = (current_day - timedelta(days=1)).isoformat()
        slot_key = f"indicatorScoutSchedule:{prior_day}:0900"
        response = self.bridge.run_dashboard_workflow_action(
            "left_audit_crystals",
            {
                "actionId": "discover_new_indicators",
                "form": {},
                "idempotencyKey": f"dashboard-schedule:{slot_key}",
            },
            trusted_trigger_source="schedule",
        )
        mission = response["mission"]
        self.bridge._dashboard_workflow_update_schedule_state(
            "indicatorScoutSchedule",
            {
                "lastMissionId": mission["id"],
                "lastSlotKey": slot_key,
                "lastAttemptSlotKey": slot_key,
                "dailyExecutionDate": prior_day,
                "dailyExecutionCount": 1,
                "dailyExecutionSlotKeys": [slot_key],
            },
        )
        applied = self.bridge._apply_scheduled_public_research_completion_retry(
            mission,
            failure_code="invalid_output",
            failure_summary="Scheduled Radar has no verified final artifact yet.",
        )
        self.assertTrue(applied)
        retry = mission["scheduledCompletionRetry"]
        retry["lastFailedAt"] = "2000-01-01T00:00:00+00:00"
        retry["nextAttemptAt"] = "2000-01-01T00:01:00+00:00"
        mission["execution"]["nextAttemptAt"] = retry["nextAttemptAt"]
        self.bridge._issue_backend_auto_safe_authorization(
            mission,
            issued_at=self.bridge.utc_now(),
        )
        self.bridge.replace_mission(mission)
        return mission, slot_key, current_day.isoformat()

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

    def runner_result(self, entries: list[dict], urls: list[str]) -> dict:
        return {
            "ok": True,
            "status": "completed",
            "workStatus": "completed",
            "webSearchUsed": True,
            "webSearchEvidenceVerified": True,
            "contractFields": [
                {
                    "field": "entries",
                    "value": json.dumps(entries, ensure_ascii=False),
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
        }

    @staticmethod
    def quota(remaining: int = 80) -> dict:
        return {
            "ok": True,
            "status": "ready",
            "stale": False,
            "limitReached": False,
            "primary": {"remainingPercent": remaining},
        }

    def write_source_artifact(
        self,
        temp_dir: str,
        urls: list[str],
        *,
        name: str = "radar-failed.final.md",
    ) -> str:
        reference = f"data/runtime/codex-runs/{name}"
        path = Path(temp_dir) / reference
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "status": "completed",
                    "summary": "sanitized result",
                    "evidence": [
                        {
                            "label": f"source-{index}",
                            "url": url,
                            "note": "public",
                        }
                        for index, url in enumerate(urls, start=1)
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return reference

    def add_verification_manifest(
        self,
        temp_dir: str,
        result: dict,
        urls: list[str],
        *,
        main_open_count: int,
        run_id: str = "run-radar-backend-receipt",
    ) -> dict:
        child_urls = urls[main_open_count:]
        rows = [
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
            for index, url in enumerate(child_urls, start=main_open_count)
        ]
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
            "mainRequiredOpenCount": main_open_count,
            "mainRequiredOpenIndexes": list(range(main_open_count)),
            "posthocVerificationCount": len(rows),
            "rows": rows,
        }
        manifest_bytes = json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        reference = (
            f"data/runtime/codex-runs/{run_id}.url-open-verification.json"
        )
        path = Path(temp_dir) / reference
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(manifest_bytes)
        enriched = copy.deepcopy(result)
        enriched.update(
            {
                "correctiveOpenVerificationCount": len(rows),
                "correctiveOpenVerifications": rows,
                "correctiveOpenVerificationArtifact": reference,
                "correctiveOpenVerificationDigest": hashlib.sha256(
                    manifest_bytes
                ).hexdigest(),
            }
        )
        return enriched

    def requeue_v2_radar_retry(
        self,
        temp_dir: str,
        mission: dict,
        slot_key: str,
    ) -> dict:
        artifact_reference = self.write_source_artifact(temp_dir, self.urls())
        output_contract = self.bridge.validate_dashboard_workflow_output_contract(
            mission,
            {"contractFields": [], "evidence": [], "evidenceKinds": []},
        )
        failed = copy.deepcopy(mission)
        failed.update(
            {
                "status": "failed",
                "phase": "auto_guarded_invalid_output",
                "workStatus": "invalid_output",
                "errorCode": "invalid_output",
                "structuredOutputError": self.bridge.RADAR_EVIDENCE_OPEN_ERROR,
                "artifactPath": artifact_reference,
                "reportIds": ["auto-report-before-v2-retry"],
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
                "workflowOutputContract": output_contract,
            }
        )
        failed["execution"].update(
            {
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
            }
        )
        self.bridge.replace_mission(failed)
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
        self.assertEqual(
            self.bridge.reconcile_current_day_public_research_output_repairs(),
            1,
        )
        recovered = self.bridge.find_mission(mission["id"])
        self.assertEqual(recovered["correctiveRetry"]["version"], 2)
        return recovered

    def test_scheduled_daily_round_requires_exactly_six_entries_and_six_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            complete = self.bridge.validate_dashboard_workflow_output_contract(
                mission,
                self.runner_result(self.entries(), self.urls()),
            )
            five_entries = self.bridge.validate_dashboard_workflow_output_contract(
                mission,
                self.runner_result(self.entries()[:5], self.urls()[:5]),
            )
            five_evidence_urls = self.bridge.validate_dashboard_workflow_output_contract(
                mission,
                self.runner_result(self.entries(), self.urls()[:5]),
            )
            normalized_urls = ["https://root.example.com/", *self.urls()[1:]]
            normalized_entries = self.entries()
            normalized_entries[0]["sourceUrl"] = (
                "HTTPS://ROOT.EXAMPLE.COM:443#ignored-fragment"
            )
            normalized_complete = (
                self.bridge.validate_dashboard_workflow_output_contract(
                    mission,
                    self.runner_result(normalized_entries, normalized_urls),
                )
            )

        self.assertTrue(complete["valid"], complete)
        self.assertTrue(normalized_complete["valid"], normalized_complete)
        self.assertEqual(complete["sourceUrlCount"], 6)
        self.assertFalse(five_entries["valid"])
        self.assertIn(
            "daily_batch_requires_exactly_6_entries",
            five_entries["entryErrors"],
        )
        self.assertFalse(five_evidence_urls["valid"])
        self.assertIn(
            "daily_batch_requires_exactly_6_evidence_urls",
            five_evidence_urls["entryErrors"],
        )

    def test_canonical_source_key_ignores_transport_and_tracking_aliases(self) -> None:
        first = self.bridge._radar_source_key(
            "HTTP://WWW.Example.com:80/tools/radar/?utm_source=newsletter#hero"
        )
        second = self.bridge._radar_source_key(
            "https://example.com/tools/radar?fbclid=tracking"
        )
        distinct_product = self.bridge._radar_source_key(
            "https://example.com/tools/radar?product=2&utm_campaign=test"
        )

        self.assertEqual(first, "example.com/tools/radar")
        self.assertEqual(first, second)
        self.assertEqual(distinct_product, "example.com/tools/radar?product=2")

    def test_scheduled_batch_rejects_historic_and_same_run_source_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            historical_key = self.bridge._radar_source_key(self.urls()[0])
            historical_entries = self.entries()
            historical_entries[0]["sourceUrl"] = (
                "https://www.alpha.example.com/radar-one/?utm_source=radar#top"
            )
            historical_urls = [
                historical_entries[0]["sourceUrl"],
                *self.urls()[1:],
            ]
            with mock.patch.object(
                self.bridge,
                "_radar_existing_catalog_identities",
                return_value=(set(), {historical_key}),
            ):
                historical = self.bridge.validate_dashboard_workflow_output_contract(
                    mission,
                    self.runner_result(historical_entries, historical_urls),
                )

            same_run_entries = self.entries()
            same_run_entries[0]["sourceUrl"] = (
                "https://duplicate.example.com/tool?utm_source=first"
            )
            same_run_entries[1]["sourceUrl"] = (
                "http://www.duplicate.example.com:80/tool/#second"
            )
            same_run_urls = [entry["sourceUrl"] for entry in same_run_entries]
            with mock.patch.object(
                self.bridge,
                "_radar_existing_catalog_identities",
                return_value=(set(), set()),
            ):
                same_run = self.bridge.validate_dashboard_workflow_output_contract(
                    mission,
                    self.runner_result(same_run_entries, same_run_urls),
                )

        self.assertFalse(historical["valid"])
        self.assertIn(
            "entry_1_historical_source_duplicate",
            historical["entryErrors"],
        )
        self.assertFalse(same_run["valid"])
        self.assertIn(
            "entry_2_duplicate_source_in_batch",
            same_run["entryErrors"],
        )

    def test_scheduled_batch_fails_closed_when_history_catalog_cannot_be_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            with mock.patch.object(
                self.bridge,
                "_radar_existing_catalog_identities",
                side_effect=OSError("catalog unavailable"),
            ):
                contract = self.bridge.validate_dashboard_workflow_output_contract(
                    mission,
                    self.runner_result(self.entries(), self.urls()),
                )

        self.assertFalse(contract["valid"])
        self.assertEqual(
            contract["entryErrors"],
            ["daily_batch_history_catalog_unavailable"],
        )

    def test_persisted_unverified_duplicate_batch_remains_hidden_until_full_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            with mock.patch.object(
                self.bridge,
                "_radar_existing_catalog_identities",
                return_value=(set(), set()),
            ):
                contract = self.bridge.validate_dashboard_workflow_output_contract(
                    mission,
                    self.runner_result(self.entries(), self.urls()),
                )
            self.assertTrue(contract["valid"], contract)
            entries = self.bridge.dashboard_workflow_output_metrics(contract)["entries"]
            entries[-1]["duplicateStatus"] = "duplicate"
            entries[-1]["duplicateScope"] = "local_report_catalog"
            report = {
                "id": "report-radar-persisted-duplicate",
                "type": "indicator_scout_report",
                "status": "ready",
                "linkedMissionId": mission["id"],
                "linkedPropId": "left_audit_crystals",
                "workflowContext": copy.deepcopy(mission["workflowContext"]),
                "createdAt": self.bridge.utc_now(),
                "updatedAt": self.bridge.utc_now(),
                "evidence": self.runner_result(self.entries(), self.urls())["evidence"],
                "metrics": {
                    "entries": entries,
                    "workflowOutput": contract,
                },
            }
            with mock.patch.object(
                self.bridge,
                "_research_sheet_cached_rows",
                return_value=[],
            ):
                model = self.bridge._radar_website_tool_read_model(
                    [report],
                    settings={},
                    now_local=datetime.now(self.bridge.THAILAND_TIMEZONE),
                    bridge={"codex": {"status": "ready"}, "time": self.bridge.utc_now()},
                    missions=[mission],
                    schedule={"lastRunStatus": "completed"},
                )

        self.assertEqual(model["today"]["runCount"], 0)
        self.assertEqual(model["today"]["itemCount"], 0)
        self.assertEqual(model["today"]["uniqueCount"], 0)
        self.assertEqual(model["today"]["duplicateCount"], 0)
        self.assertEqual(model["todayEntries"], [])
        self.assertEqual(model["verifiedReadyBatchCount"], 0)
        self.assertEqual(len(report["metrics"]["entries"]), 6)

    def test_verified_batch_with_late_catalog_duplicate_is_hidden_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            with mock.patch.object(
                self.bridge,
                "_radar_existing_catalog_identities",
                return_value=(set(), set()),
            ):
                contract = self.bridge.validate_dashboard_workflow_output_contract(
                    mission,
                    self.runner_result(self.entries(), self.urls()),
                )
            self.assertTrue(contract["valid"], contract)
            entries = self.bridge.dashboard_workflow_output_metrics(contract)["entries"]
            report = {
                "id": "report-radar-late-sheet-duplicate",
                "type": "indicator_scout_report",
                "status": "ready",
                "linkedMissionId": mission["id"],
                "linkedPropId": "left_audit_crystals",
                "workflowContext": copy.deepcopy(mission["workflowContext"]),
                "createdAt": self.bridge.utc_now(),
                "updatedAt": self.bridge.utc_now(),
                "evidence": self.runner_result(self.entries(), self.urls())["evidence"],
                "metrics": {
                    "entries": entries,
                    "workflowOutput": contract,
                },
            }
            late_duplicate_row = {
                "duplicate_fingerprint": entries[-1]["duplicateFingerprint"],
                "normalized_source_url": entries[-1]["sourceUrl"],
                "first_report_id": "different-report",
                "latest_report_id": "different-report",
            }
            with mock.patch.object(
                self.bridge,
                "_research_sheet_cached_rows",
                return_value=[late_duplicate_row],
            ):
                model = self.bridge._radar_website_tool_read_model(
                    [report],
                    settings={},
                    now_local=datetime.now(self.bridge.THAILAND_TIMEZONE),
                    bridge={"codex": {"status": "ready"}, "time": self.bridge.utc_now()},
                    missions=[mission],
                    schedule={"lastRunStatus": "completed"},
                )

        self.assertEqual(model["today"]["runCount"], 0)
        self.assertEqual(model["today"]["itemCount"], 0)
        self.assertEqual(model["todayEntries"], [])
        self.assertEqual(model["verifiedReadyBatchCount"], 0)
        self.assertTrue(
            all(entry["duplicateStatus"] == "unique" for entry in report["metrics"]["entries"])
        )

    def test_restart_recovers_same_current_day_mission_without_new_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            artifact_reference = "data/runtime/codex-runs/radar-failed.final.md"
            artifact_path = Path(temp_dir) / artifact_reference
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "summary": "sanitized result",
                        "evidence": [
                            {"label": f"source-{index}", "url": url, "note": "public"}
                            for index, url in enumerate(self.urls(), start=1)
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            expected_evidence = [
                "source_url",
                "source_title",
                "checked_at",
                "ea_readiness",
                "public_availability_status",
            ]
            failed = copy.deepcopy(mission)
            failed.update(
                {
                    "status": "failed",
                    "phase": "auto_guarded_invalid_output",
                    "workStatus": "invalid_output",
                    "errorCode": "invalid_output",
                    "structuredOutputError": self.bridge.RADAR_EVIDENCE_OPEN_ERROR,
                    "artifactPath": artifact_reference,
                    "reportIds": ["blocked-report-before-retry"],
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": False,
                    "workflowOutputContract": {
                        "applicable": True,
                        "valid": False,
                        "failureCode": "radar_output_contract_invalid",
                        "procedureId": self.bridge.RADAR_WORKFLOW_PROCEDURE_ID,
                        "expectedFields": ["entries"],
                        "providedFields": [],
                        "missingFields": ["entries"],
                        "expectedEvidenceKinds": expected_evidence,
                        "providedEvidenceKinds": [],
                        "missingEvidenceKinds": expected_evidence,
                        "entryErrors": ["entries_not_array"],
                        "oversizedFields": [],
                        "contractValueChars": 0,
                        "sourceUrlCount": 0,
                    },
                }
            )
            failed["execution"].update(
                {
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": False,
                    "automaticRetry": False,
                }
            )
            self.bridge.replace_mission(failed)
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "lastMissionId": mission["id"],
                    "lastSlotKey": slot_key,
                    "lastAttemptSlotKey": slot_key,
                    "dailyExecutionDate": datetime.now(
                        self.bridge.THAILAND_TIMEZONE
                    ).date().isoformat(),
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            workflow_settings = self.bridge.load_dashboard_workflow_settings()
            self.assertTrue(self.bridge._radar_complete_daily_batch_required(failed))
            self.assertIsNotNone(self.bridge._trusted_workflow_guard_intent(failed))
            self.assertTrue(
                self.bridge._current_day_scheduled_workflow_recovery_matches(
                    failed,
                    self.bridge._workflow_context_storage(failed["workflowContext"]),
                    workflow_settings,
                    datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat(),
                )
            )
            self.assertEqual(
                self.bridge._trading_system_evidence_retry_urls_from_artifact(
                    artifact_reference
                ),
                self.urls(),
            )
            self.assertIsNotNone(
                self.bridge._scheduled_radar_evidence_open_retry_candidate(
                    failed,
                    workflow_settings,
                    datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat(),
                ),
                failed,
            )
            before = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            first_count = self.bridge.reconcile_current_day_public_research_output_repairs()
            recovered = self.bridge.find_mission(mission["id"])
            after = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            second_count = self.bridge.reconcile_current_day_public_research_output_repairs()

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 0)
        self.assertEqual(recovered["id"], mission["id"])
        self.assertEqual(recovered["status"], "queued")
        self.assertEqual(recovered["idempotencyKey"], mission["idempotencyKey"])
        self.assertEqual(recovered["reportIds"], [])
        self.assertEqual(recovered["correctiveRetry"]["attemptCount"], 1)
        self.assertEqual(recovered["correctiveRetry"]["remainingAttempts"], 0)
        self.assertEqual(recovered["correctiveRetry"]["status"], "queued")
        self.assertTrue(recovered["correctiveRetry"]["automaticRetry"])
        self.assertFalse(recovered["correctiveRetry"]["newDailyReservation"])
        self.assertEqual(
            recovered["detail"].count(
                self.bridge.RADAR_EVIDENCE_CANDIDATE_BLOCK_START
            ),
            1,
        )
        self.assertEqual(before["dailyExecutionCount"], 1)
        self.assertEqual(after["dailyExecutionCount"], 1)
        self.assertEqual(after["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(after["lastMissionId"], mission["id"])

    def test_live_v1_preprocess_block_recovers_once_and_rebinds_source_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            artifact_reference = self.write_source_artifact(temp_dir, self.urls())
            empty_contract = self.bridge.validate_dashboard_workflow_output_contract(
                mission,
                {"contractFields": [], "evidence": [], "evidenceKinds": []},
            )
            failed = copy.deepcopy(mission)
            failed.update(
                {
                    "status": "failed",
                    "phase": "auto_guarded_invalid_output",
                    "workStatus": "invalid_output",
                    "errorCode": "invalid_output",
                    "structuredOutputError": self.bridge.RADAR_EVIDENCE_OPEN_ERROR,
                    "artifactPath": artifact_reference,
                    "reportIds": ["auto-report-before-radar-retry"],
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": False,
                    "workflowOutputContract": empty_contract,
                }
            )
            failed["execution"].update(
                {
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": False,
                }
            )
            self.bridge.replace_mission(failed)
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
            settings = self.bridge.load_dashboard_workflow_settings()
            candidate = self.bridge._scheduled_radar_evidence_open_retry_candidate(
                failed,
                settings,
                today,
            )
            self.assertIsNotNone(candidate)
            live_v1 = copy.deepcopy(failed)
            self.assertTrue(
                self.bridge._apply_scheduled_radar_evidence_open_retry(
                    live_v1,
                    candidate,
                    requeued_at=self.bridge.utc_now(),
                    failure_snapshot=failed,
                )
            )
            # Exact live failure shape: the old classifier blocked before the
            # Runner process, then terminalized the one Radar retry as trading.
            live_v1.update(
                {
                    "status": "blocked",
                    "phase": "auto_guarded_blocked",
                    "workStatus": "blocked",
                    "errorCode": "trading_system_required_open_urls_invalid",
                    "blockedCapability": "trading_system_required_open_urls_invalid",
                    "result": "ข้อมูล URL สำหรับ corrective research ไม่ตรง",
                    "artifactPath": None,
                    "reportIds": ["auto-report-classifier-block"],
                    "workflowOutputContract": copy.deepcopy(empty_contract),
                    "structuredOutputError": "",
                    "webSearchUsed": False,
                    "webSearchEvidenceVerified": False,
                }
            )
            live_v1["correctiveRetry"].update(
                {
                    "version": 1,
                    "status": "exhausted",
                    "completedAt": self.bridge.utc_now(),
                    "terminalFailureReasonCode": (
                        "trading_system_required_open_urls_invalid"
                    ),
                }
            )
            live_v1["execution"].update(
                {
                    "dispatchState": "blocked",
                    "processStarted": False,
                    "workingDirectory": "",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchMode": "disabled",
                    "webSearchUsed": False,
                    "webSearchEvidenceVerified": False,
                    "automaticRetry": False,
                    "correctiveRetryKind": (
                        self.bridge.RADAR_EVIDENCE_CORRECTIVE_RETRY_KIND
                    ),
                }
            )
            self.bridge.replace_mission(live_v1)
            before = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            probe = self.bridge._scheduled_radar_v1_classification_repair_candidate(
                live_v1,
                self.bridge.load_dashboard_workflow_settings(),
                today,
            )
            self.assertIsNotNone(probe, live_v1)
            first_count = self.bridge.reconcile_current_day_public_research_output_repairs()
            repaired = self.bridge.find_mission(mission["id"])
            after = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            second_count = self.bridge.reconcile_current_day_public_research_output_repairs()
            rebound_urls, rebound_error = (
                self.bridge._radar_corrective_candidate_urls_for_mission(repaired)
            )
            alternate_reference = self.write_source_artifact(
                temp_dir,
                self.urls(),
                name="radar-alternate-same-urls.final.md",
            )
            rebound_to_other_artifact = copy.deepcopy(repaired)
            rebound_to_other_artifact["correctiveRetry"][
                "sourceArtifact"
            ] = alternate_reference
            other_artifact_urls, other_artifact_error = (
                self.bridge._radar_corrective_candidate_urls_for_mission(
                    rebound_to_other_artifact
                )
            )
            malformed_classification = copy.deepcopy(repaired)
            malformed_classification["correctiveRetry"][
                "classificationRepair"
            ] = "not-a-dict"
            malformed_urls, malformed_error = (
                self.bridge._radar_corrective_candidate_urls_for_mission(
                    malformed_classification
                )
            )
            self.write_source_artifact(
                temp_dir,
                [*self.urls()[:5], "https://changed.example.com/radar-six"],
            )
            tampered_urls, tampered_error = (
                self.bridge._radar_corrective_candidate_urls_for_mission(repaired)
            )

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 0)
        self.assertEqual(repaired["id"], mission["id"])
        self.assertEqual(repaired["status"], "queued")
        self.assertEqual(repaired["correctiveRetry"]["version"], 2)
        self.assertEqual(
            repaired["correctiveRetry"]["classificationRepair"]["version"],
            2,
        )
        self.assertFalse(
            repaired["correctiveRetry"]["classificationRepair"][
                "runnerProcessPreviouslyStarted"
            ]
        )
        self.assertEqual(rebound_urls, self.urls())
        self.assertIsNone(rebound_error)
        self.assertEqual(other_artifact_urls, [])
        self.assertEqual(
            other_artifact_error,
            "radar_corrective_candidate_urls_invalid",
        )
        self.assertEqual(malformed_urls, [])
        self.assertEqual(
            malformed_error,
            "radar_corrective_candidate_urls_invalid",
        )
        self.assertEqual(tampered_urls, [])
        self.assertEqual(tampered_error, "radar_corrective_candidate_urls_invalid")
        self.assertEqual(before["dailyExecutionCount"], 1)
        self.assertEqual(after["dailyExecutionCount"], 1)
        self.assertEqual(after["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(after["lastMissionId"], mission["id"])

    def test_live_finish_requeues_same_mission_before_publishing_partial_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            artifact_reference = "data/runtime/codex-runs/radar-live-failed.final.md"
            artifact_path = Path(temp_dir) / artifact_reference
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "evidence": [
                            {"label": f"source-{index}", "url": url, "note": "public"}
                            for index, url in enumerate(self.urls(), start=1)
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            lease_id = "lease-radar-live-retry"
            running = copy.deepcopy(mission)
            running.update(
                {
                    "status": "running",
                    "phase": "auto_guarded_running",
                    "workStatus": None,
                    "errorCode": None,
                    "attemptCount": 1,
                }
            )
            running["execution"].update(
                {
                    "dispatchState": "running",
                    "workerId": "worker-radar-live-retry",
                    "leaseId": lease_id,
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": False,
                }
            )
            self.bridge.replace_mission(running)
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "lastMissionId": mission["id"],
                    "lastSlotKey": slot_key,
                    "lastAttemptSlotKey": slot_key,
                    "dailyExecutionDate": datetime.now(
                        self.bridge.THAILAND_TIMEZONE
                    ).date().isoformat(),
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            runner_result = {
                "ok": False,
                "status": "invalid_output",
                "workStatus": "invalid_output",
                "finalMessage": "ผลไม่ผ่านการตรวจหลักฐาน",
                "structuredOutputError": self.bridge.RADAR_EVIDENCE_OPEN_ERROR,
                "contractFields": [],
                "evidence": [],
                "evidenceKinds": [],
                "artifacts": {"final": artifact_reference},
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
            }
            with mock.patch.object(self.bridge, "create_report") as create_report:
                requeued = self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    runner_result,
                )
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        create_report.assert_not_called()
        self.assertEqual(requeued["id"], mission["id"])
        self.assertEqual(requeued["status"], "queued")
        self.assertEqual(requeued["radarBatchRepair"]["totalAttemptCount"], 1)
        self.assertEqual(requeued["radarBatchRepair"]["burstAttemptCount"], 1)
        self.assertEqual(requeued["radarBatchRepair"]["lastObservedItemCount"], 0)
        self.assertEqual(requeued["modelTier"], "specialist_balanced")
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])

    def test_missing_artifact_invalid_output_retries_same_daily_mission_across_backoff_rounds_without_report(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission["id"],
                    "lastSlotKey": slot_key,
                    "lastAttemptSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            runner_result = {
                "ok": False,
                "status": "invalid_output",
                "workStatus": "invalid_output",
                "finalMessage": "ผลลัพธ์ยังไม่มี final artifact ที่ตรวจสอบได้",
                "structuredOutputError": "entries missing",
                "contractFields": [],
                "evidence": [],
                "evidenceKinds": [],
                "artifacts": {},
                "processStarted": True,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchUsed": True,
                "webSearchEvidenceVerified": False,
            }

            def mark_running(row: dict, lease_id: str) -> dict:
                running = copy.deepcopy(row)
                running.update(
                    {
                        "status": "running",
                        "phase": "auto_guarded_running",
                        "workStatus": None,
                        "errorCode": None,
                        "attemptCount": int(running.get("attemptCount") or 0) + 1,
                    }
                )
                running["execution"].update(
                    {
                        "dispatchState": "running",
                        "workerId": "worker-radar-missing-artifact",
                        "leaseId": lease_id,
                        "processStarted": True,
                    }
                )
                self.bridge.replace_mission(running)
                return running

            first_running = mark_running(mission, "lease-radar-missing-artifact-1")
            with mock.patch.object(self.bridge, "create_report") as create_report:
                first = self.bridge.finish_auto_mission(
                    mission["id"],
                    first_running["execution"]["leaseId"],
                    {"processStarted": True},
                    runner_result,
                )
                second_running = mark_running(
                    first,
                    "lease-radar-missing-artifact-2",
                )
                second = self.bridge.finish_auto_mission(
                    mission["id"],
                    second_running["execution"]["leaseId"],
                    {"processStarted": True},
                    runner_result,
                )
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        create_report.assert_not_called()
        self.assertEqual(first["id"], mission["id"])
        self.assertEqual(first["idempotencyKey"], mission["idempotencyKey"])
        self.assertEqual(first["status"], "queued")
        self.assertEqual(
            first["phase"],
            "auto_guarded_scheduled_completion_retry_deferred",
        )
        self.assertEqual(first["reportIds"], [])
        self.assertEqual(first["scheduledCompletionRetry"]["attemptCount"], 1)
        self.assertEqual(
            first["scheduledCompletionRetry"]["lastFailureCode"],
            "invalid_output",
        )
        self.assertTrue(first["scheduledCompletionRetry"]["sameMission"])
        self.assertTrue(first["scheduledCompletionRetry"]["sameDailyReservation"])
        self.assertFalse(first["scheduledCompletionRetry"]["newDailyReservation"])
        self.assertEqual(first["execution"]["dispatchState"], "deferred")
        self.assertTrue(first["execution"]["automaticRetry"])
        self.assertEqual(second["id"], mission["id"])
        self.assertEqual(second["status"], "queued")
        self.assertEqual(second["reportIds"], [])
        self.assertEqual(second["scheduledCompletionRetry"]["attemptCount"], 2)
        self.assertGreater(
            self.bridge.parse_iso(
                second["scheduledCompletionRetry"]["nextAttemptAt"]
            ),
            self.bridge.parse_iso(first["scheduledCompletionRetry"]["nextAttemptAt"]),
        )
        self.assertEqual(schedule["lastRunStatus"], "deferred")
        self.assertEqual(
            schedule["lastResultKind"],
            "scheduled_completion_retry_deferred",
        )
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])

    def test_new_retry_packet_is_digest_bound_without_invalidating_legacy_mission_digest(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            baseline_digest = self.bridge.mission_payload_digest(mission)
            legacy = copy.deepcopy(mission)
            legacy["scheduledCompletionRetry"] = {
                "schemaVersion": "scheduled-public-research-completion-retry-v1",
                "attemptCount": 1,
            }
            modern = copy.deepcopy(legacy)
            modern["scheduledCompletionRetry"]["originalSlotKey"] = slot_key

        self.assertEqual(
            self.bridge.mission_payload_digest(legacy),
            baseline_digest,
        )
        self.assertNotEqual(
            self.bridge.mission_payload_digest(modern),
            baseline_digest,
        )

    def test_interrupted_running_scheduled_radar_requeues_after_restart_without_new_slot(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            today = datetime.now(self.bridge.THAILAND_TIMEZONE).date().isoformat()
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "requestedEnabled": True,
                    "lastMissionId": mission["id"],
                    "lastSlotKey": slot_key,
                    "lastAttemptSlotKey": slot_key,
                    "dailyExecutionDate": today,
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            running = copy.deepcopy(mission)
            running.update(
                {
                    "status": "running",
                    "phase": "auto_guarded_running",
                    "workStatus": None,
                    "errorCode": None,
                    "attemptCount": 1,
                }
            )
            running["execution"].update(
                {
                    "dispatchState": "running",
                    "workerId": "worker-radar-before-restart",
                    "leaseId": "lease-radar-before-restart",
                    "processStarted": True,
                }
            )
            self.bridge.replace_mission(running)
            self.bridge.MISSION_WORKER_WAKE.clear()

            first_count = self.bridge.recover_interrupted_missions()
            recovered = self.bridge.find_mission(mission["id"])
            second_count = self.bridge.recover_interrupted_missions()
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 0)
        self.assertEqual(recovered["id"], mission["id"])
        self.assertEqual(recovered["idempotencyKey"], mission["idempotencyKey"])
        self.assertEqual(recovered["status"], "queued")
        self.assertEqual(
            recovered["phase"],
            "auto_guarded_scheduled_completion_retry_deferred",
        )
        self.assertEqual(recovered["reportIds"], [])
        self.assertEqual(recovered["execution"]["dispatchState"], "deferred")
        self.assertFalse(recovered["execution"]["processStarted"])
        self.assertTrue(recovered["execution"]["automaticRetry"])
        self.assertEqual(
            recovered["scheduledCompletionRetry"]["lastFailureCode"],
            "auto_worker_interrupted",
        )
        self.assertEqual(recovered["scheduledCompletionRetry"]["attemptCount"], 1)
        self.assertTrue(recovered["scheduledCompletionRetry"]["sameMission"])
        self.assertTrue(
            recovered["scheduledCompletionRetry"]["sameDailyReservation"]
        )
        self.assertFalse(
            recovered["scheduledCompletionRetry"]["newDailyReservation"]
        )
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])
        self.assertEqual(schedule["lastMissionId"], mission["id"])
        self.assertEqual(schedule["lastRunStatus"], "deferred")
        self.assertTrue(self.bridge.MISSION_WORKER_WAKE.is_set())
        restart_audit = [
            row
            for row in audit
            if row.get("type") == "mission.scheduled_radar_restart_requeued"
        ]
        self.assertEqual(len(restart_audit), 1)
        self.assertTrue(restart_audit[0]["automaticRetry"])
        self.assertTrue(restart_audit[0]["sameDailyReservation"])
        self.assertTrue(restart_audit[0]["realToolExecuted"])

    def test_prior_day_valid_scheduled_completion_retry_carries_forward_same_slot(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key, current_day = (
                self.prior_day_scheduled_radar_completion_retry()
            )
            original_idempotency_key = mission["idempotencyKey"]
            self.bridge.MISSION_WORKER_WAKE.clear()

            carried = self.bridge._expire_prior_day_radar_mission(mission)
            stored = self.bridge.find_mission(mission["id"])
            duplicate_expiry = self.bridge._expire_prior_day_radar_mission(stored)
            due = self.bridge._find_next_auto_mission_unlocked(council_only=False)
            indicator_job = tuple(
                job
                for job in self.bridge.DASHBOARD_WORKFLOW_SCHEDULE_JOBS
                if job.get("settingsKey") == "indicatorScoutSchedule"
            )
            current_local = datetime.combine(
                datetime.strptime(current_day, "%Y-%m-%d").date(),
                datetime.min.time(),
                tzinfo=self.bridge.THAILAND_TIMEZONE,
            ).replace(hour=9, minute=1)
            with mock.patch.object(
                self.bridge,
                "DASHBOARD_WORKFLOW_SCHEDULE_JOBS",
                indicator_job,
            ):
                captured = self.bridge._dashboard_workflow_capture_due_slots(
                    current_local
                )
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]
            audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)

        self.assertTrue(carried)
        self.assertFalse(duplicate_expiry)
        self.assertIsNotNone(due)
        self.assertEqual(due["id"], mission["id"])
        self.assertEqual(stored["id"], mission["id"])
        self.assertEqual(stored["idempotencyKey"], original_idempotency_key)
        self.assertEqual(stored["status"], "queued")
        self.assertIsNone(stored["errorCode"])
        self.assertEqual(stored["reportIds"], [])
        self.assertEqual(
            stored["phase"],
            "auto_guarded_scheduled_completion_retry_overdue",
        )
        retry = stored["scheduledCompletionRetry"]
        self.assertEqual(retry["attemptCount"], 1)
        self.assertTrue(retry["overdueCarryForward"])
        self.assertEqual(retry["overdueSinceBangkokDate"], current_day)
        self.assertEqual(retry["originalSlotKey"], slot_key)
        reservation = stored["workflowContext"]["executionReservation"]
        self.assertEqual(reservation["slotKey"], slot_key)
        self.assertEqual(reservation["bangkokDate"], slot_key.split(":")[1])
        self.assertEqual(stored["execution"]["dispatchState"], "deferred")
        self.assertTrue(stored["execution"]["automaticRetry"])
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertEqual(captured, [])
        self.assertEqual(schedule["dailyExecutionDate"], current_day)
        self.assertEqual(schedule["dailyExecutionCount"], 0)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [])
        self.assertEqual(schedule["carryForwardBlockDate"], current_day)
        self.assertEqual(schedule["carryForwardMissionId"], mission["id"])
        overdue_audit = [
            row
            for row in audit
            if row.get("type") == "mission.scheduled_radar_completion_overdue"
        ]
        self.assertEqual(len(overdue_audit), 1)
        self.assertTrue(overdue_audit[0]["sameDailyReservation"])
        self.assertFalse(overdue_audit[0]["newDailyReservation"])
        self.assertFalse(overdue_audit[0]["dailyReservationCountIncremented"])
        self.assertTrue(self.bridge.MISSION_WORKER_WAKE.is_set())

    def test_prior_day_invalid_scheduled_completion_retry_expires_fail_closed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _slot_key, _current_day = (
                self.prior_day_scheduled_radar_completion_retry()
            )
            mission["scheduledCompletionRetry"]["sameDailyReservation"] = False
            self.bridge._issue_backend_auto_safe_authorization(
                mission,
                issued_at=self.bridge.utc_now(),
            )
            self.bridge.replace_mission(mission)

            expired = self.bridge._expire_prior_day_radar_mission(mission)
            stored = self.bridge.find_mission(mission["id"])
            audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)

        self.assertTrue(expired)
        self.assertEqual(stored["status"], "blocked")
        self.assertEqual(stored["phase"], "scheduled_radar_slot_expired")
        self.assertEqual(stored["errorCode"], "scheduled_radar_slot_expired")
        self.assertEqual(stored["execution"]["dispatchState"], "blocked")
        self.assertFalse(stored["execution"]["automaticRetry"])
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertIsNone(stored["execution"]["nextAttemptAt"])
        self.assertIsNone(
            self.bridge._find_next_auto_mission_unlocked(council_only=False)
        )
        self.assertFalse(
            any(
                row.get("type")
                == "mission.scheduled_radar_completion_overdue"
                for row in audit
            )
        )
        self.assertTrue(
            any(
                row.get("type")
                == "dashboard.radar_daily_reservation_expired"
                for row in audit
            )
        )

    def test_historical_duplicate_finish_requeues_same_mission_at_five_of_six(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            artifact_reference = self.write_source_artifact(
                temp_dir,
                self.urls(),
                name="radar-historical-duplicate.final.md",
            )
            lease_id = "lease-radar-historical-duplicate"
            running = copy.deepcopy(mission)
            running.update(
                {
                    "status": "running",
                    "phase": "auto_guarded_running",
                    "workStatus": None,
                    "errorCode": None,
                    "attemptCount": 1,
                }
            )
            running["execution"].update(
                {
                    "dispatchState": "running",
                    "workerId": "worker-radar-historical-duplicate",
                    "leaseId": lease_id,
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                    "webSearchUsed": True,
                    "webSearchEvidenceVerified": True,
                }
            )
            self.bridge.replace_mission(running)
            self.bridge._dashboard_workflow_update_schedule_state(
                "indicatorScoutSchedule",
                {
                    "lastMissionId": mission["id"],
                    "lastSlotKey": slot_key,
                    "lastAttemptSlotKey": slot_key,
                    "dailyExecutionDate": datetime.now(
                        self.bridge.THAILAND_TIMEZONE
                    ).date().isoformat(),
                    "dailyExecutionCount": 1,
                    "dailyExecutionSlotKeys": [slot_key],
                },
            )
            result = self.add_verification_manifest(
                temp_dir,
                self.runner_result(self.entries(), self.urls()),
                self.urls(),
                main_open_count=6,
                run_id="run-radar-historical-duplicate",
            )
            result.update(
                {
                    "finalMessage": "พบหกรายการและเปิดหลักฐานครบ",
                    "artifacts": {"final": artifact_reference},
                    "processStarted": True,
                    "workingDirectory": "workspace",
                    "writeRoots": [],
                    "controlPlaneWritable": False,
                    "webSearchEnabled": True,
                }
            )
            historical_source_key = self.bridge._radar_source_key(self.urls()[0])
            with (
                mock.patch.object(
                    self.bridge,
                    "_radar_existing_catalog_identities",
                    return_value=(set(), {historical_source_key}),
                ),
                mock.patch.object(self.bridge, "create_report") as create_report,
            ):
                requeued = self.bridge.finish_auto_mission(
                    mission["id"],
                    lease_id,
                    {"processStarted": True},
                    result,
                )
            schedule = self.bridge.load_dashboard_workflow_settings()[
                "indicatorScoutSchedule"
            ]

        create_report.assert_not_called()
        self.assertEqual(requeued["id"], mission["id"])
        self.assertEqual(requeued["status"], "queued")
        repair = requeued["radarBatchRepair"]
        self.assertEqual(repair["lastObservedItemCount"], 5)
        self.assertEqual(repair["originalSlotKey"], slot_key)
        self.assertTrue(repair["scheduleSlotPreserved"])
        self.assertFalse(repair["newDailyReservation"])
        self.assertFalse(repair["dailyReservationCountIncremented"])
        self.assertEqual(schedule["dailyExecutionCount"], 1)
        self.assertEqual(schedule["dailyExecutionSlotKeys"], [slot_key])

    def test_fresh_and_v2_worker_reserve_six_slots_without_trading_cli_urls(
        self,
    ) -> None:
        for case_name in ("fresh", "v2"):
            with (
                self.subTest(case=case_name),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                with self.bridge.RATE_LIMIT_LOCK:
                    self.bridge.RATE_LIMIT_STATE.clear()
                mission, slot_key = self.scheduled_radar()
                if case_name == "v2":
                    mission = self.requeue_v2_radar_retry(
                        temp_dir,
                        mission,
                        slot_key,
                    )
                captured_command: list[str] = []

                def fake_runner(command, **_kwargs):
                    captured_command.extend(str(item) for item in command)
                    return {
                        "ok": False,
                        "exitCode": 1,
                        "processStarted": False,
                        "output": json.dumps(
                            {"ok": False, "status": "failed"}
                        ),
                    }

                real_reserve = self.bridge.reserve_rate_limit_slots
                bulk_reserve = mock.Mock(side_effect=real_reserve)
                single_slot_check = mock.Mock(return_value=(True, 0))
                finish = mock.Mock()
                with (
                    mock.patch.object(
                        self.bridge,
                        "bridge_status",
                        return_value={"codex": {"status": "ready"}},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "codex_rate_limits",
                        return_value=self.quota(),
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_collaboration_quota_gate",
                        return_value={"allowed": True, "reason": "ready"},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "check_rate_limit",
                        single_slot_check,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "reserve_rate_limit_slots",
                        bulk_reserve,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "run_safe_command",
                        side_effect=fake_runner,
                    ),
                    mock.patch.object(
                        self.bridge,
                        "finish_auto_mission",
                        finish,
                    ),
                    mock.patch.object(self.bridge, "heartbeat_auto_mission"),
                    mock.patch.object(self.bridge, "update_mission_worker_state"),
                    mock.patch.object(
                        self.bridge,
                        "invalidate_codex_rate_limit_cache",
                    ),
                ):
                    self.bridge.process_auto_mission(
                        f"worker-radar-{case_name}",
                        mission,
                    )
                stored = self.bridge.find_mission(mission["id"])
                rate_key = (
                    f"real:{mission['owner']}:{mission['toolId']}:"
                    f"{mission['modelTier']}"
                )
                with self.bridge.RATE_LIMIT_LOCK:
                    rate_rows = self.bridge._load_persisted_rate_limits_unlocked()[
                        rate_key
                    ]

                self.assertEqual(len(bulk_reserve.call_args_list), 2)
                self.assertEqual(
                    [call.args[2] for call in bulk_reserve.call_args_list],
                    [6, 6],
                )
                self.assertEqual(
                    [call.kwargs["consume"] for call in bulk_reserve.call_args_list],
                    [False, True],
                )
                single_slot_check.assert_not_called()
                self.assertIn("--result-profile", captured_command)
                self.assertEqual(
                    captured_command[
                        captured_command.index("--result-profile") + 1
                    ],
                    "radar_website_tool",
                )
                self.assertNotIn("--required-open-url", captured_command)
                finish.assert_called_once()
                reservation = stored["execution"][
                    "correctiveOpenHourlyReservation"
                ]
                self.assertEqual(reservation["reservedRunCount"], 6)
                self.assertEqual(reservation["maximumChildRunCount"], 5)
                self.assertEqual(len(rate_rows), 6)

    def test_radar_manifest_is_fail_closed_and_settlement_releases_only_unused_slots(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            normalized_urls = [
                "https://root.example.com/",
                *self.urls()[1:],
            ]
            result = self.runner_result(self.entries(), normalized_urls)
            # The Backend normalizes scheme/host case and strips fragments
            # and default ports before comparing evidence to the Runner manifest.
            result["evidence"][0]["url"] = (
                "HTTPS://ROOT.EXAMPLE.COM:443#untrusted-fragment"
            )
            result = self.add_verification_manifest(
                temp_dir,
                result,
                normalized_urls,
                main_open_count=2,
            )
            receipt = self.bridge._bounded_radar_corrective_open_verification_receipt(
                mission,
                result,
            )
            self.assertTrue(receipt["valid"], receipt)
            self.assertEqual(receipt["missingUrlVerificationCount"], 4)

            boolean_count_result = copy.deepcopy(result)
            boolean_count_result["correctiveOpenVerificationCount"] = True
            boolean_count_receipt = (
                self.bridge._bounded_radar_corrective_open_verification_receipt(
                    mission,
                    boolean_count_result,
                )
            )
            self.assertFalse(boolean_count_receipt["valid"])

            manifest_path = Path(temp_dir) / result[
                "correctiveOpenVerificationArtifact"
            ]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mainRequiredOpenCount"] = True
            tampered_bytes = json.dumps(
                manifest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            manifest_path.write_bytes(tampered_bytes)
            tampered_result = copy.deepcopy(result)
            tampered_result["correctiveOpenVerificationDigest"] = hashlib.sha256(
                tampered_bytes
            ).hexdigest()
            tampered_receipt = (
                self.bridge._bounded_radar_corrective_open_verification_receipt(
                    mission,
                    tampered_result,
                )
            )
            self.assertFalse(tampered_receipt["valid"])

            # Restore the exact valid manifest before testing durable hourly
            # settlement and its idempotent release identity.
            result = self.add_verification_manifest(
                temp_dir,
                self.runner_result(self.entries(), normalized_urls),
                normalized_urls,
                main_open_count=6,
            )
            receipt = self.bridge._bounded_radar_corrective_open_verification_receipt(
                mission,
                result,
            )
            reservation_digest, reservation_error, is_dynamic = (
                self.bridge._radar_dynamic_open_reservation_digest(mission)
            )
            self.assertIsNone(reservation_error)
            self.assertTrue(is_dynamic)
            tier = (
                self.bridge.load_orchestration_contract().get("modelTiers", {}).get(
                    mission["modelTier"],
                    {},
                )
            )
            max_runs = self.bridge.clamp_int(
                tier.get("maxRunsPerHour"),
                12,
                1,
                200,
            )
            rate_key = (
                f"real:{mission['owner']}:{mission['toolId']}:"
                f"{mission['modelTier']}"
            )
            allowed, _retry_after, stamps = self.bridge.reserve_rate_limit_slots(
                rate_key,
                max_runs,
                6,
                consume=True,
            )
            self.assertTrue(allowed)
            lease_id = "lease-radar-settlement"
            reservation = self.bridge._corrective_open_hourly_reservation_record(
                rate_key,
                mission["modelTier"],
                max_runs,
                mission["id"],
                lease_id,
                reservation_digest,
                stamps,
            )
            self.assertIsNotNone(reservation)
            completed = copy.deepcopy(mission)
            completed.update(
                {
                    "status": "completed",
                    "phase": "completed",
                    "workStatus": "completed",
                    "correctiveOpenVerificationReceipt": copy.deepcopy(receipt),
                }
            )
            completed["execution"].update(
                {
                    "leaseId": lease_id,
                    "processStarted": True,
                    "correctiveOpenHourlyReservation": reservation,
                    "correctiveOpenVerificationReceipt": copy.deepcopy(receipt),
                }
            )
            release_plan = self.bridge._corrective_open_hourly_release_plan(
                completed,
                receipt,
            )
            self.assertIsNotNone(
                release_plan,
                json.dumps(
                    {
                        "reservation": reservation,
                        "receipt": receipt,
                        "radarDigest": (
                            self.bridge._radar_dynamic_open_reservation_digest(
                                completed
                            )
                        ),
                        "trusted": bool(
                            self.bridge._trusted_workflow_guard_intent(completed)
                        ),
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            )
            self.bridge.replace_mission(completed)
            settled = self.bridge._settle_corrective_open_hourly_reservation(
                mission["id"],
                lease_id,
            )
            settled_again = self.bridge._settle_corrective_open_hourly_reservation(
                mission["id"],
                lease_id,
            )
            stored = self.bridge.find_mission(mission["id"])
            with self.bridge.RATE_LIMIT_LOCK:
                rate_rows = self.bridge._load_persisted_rate_limits_unlocked()[
                    rate_key
                ]

        self.assertIsNotNone(settled)
        self.assertIsNone(settled_again)
        stored_reservation = stored["execution"][
            "correctiveOpenHourlyReservation"
        ]
        self.assertEqual(stored_reservation["state"], "reconciled")
        self.assertEqual(stored_reservation["actualChildRunCount"], 0)
        self.assertEqual(stored_reservation["releasedUnusedChildRunCount"], 5)
        self.assertEqual(len(rate_rows), 1)

    def test_v2_receipt_requires_exact_candidate_evidence_set(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, slot_key = self.scheduled_radar()
            retry = self.requeue_v2_radar_retry(
                temp_dir,
                mission,
                slot_key,
            )
            result = self.add_verification_manifest(
                temp_dir,
                self.runner_result(self.entries(), self.urls()),
                self.urls(),
                main_open_count=1,
                run_id="run-radar-v2-receipt",
            )
            valid_receipt = (
                self.bridge._bounded_radar_corrective_open_verification_receipt(
                    retry,
                    result,
                )
            )
            wrong_evidence = copy.deepcopy(result)
            wrong_evidence["evidence"][-1]["url"] = (
                "https://wrong.example.com/not-the-candidate"
            )
            invalid_receipt = (
                self.bridge._bounded_radar_corrective_open_verification_receipt(
                    retry,
                    wrong_evidence,
                )
            )

        self.assertTrue(valid_receipt["valid"], valid_receipt)
        self.assertTrue(valid_receipt["candidateUrlSetMatched"])
        self.assertFalse(invalid_receipt["valid"])
        self.assertFalse(invalid_receipt["candidateUrlSetMatched"])

    def test_fresh_and_v2_defer_atomically_when_only_five_slots_remain(
        self,
    ) -> None:
        for case_name in ("fresh", "v2"):
            with (
                self.subTest(case=case_name),
                tempfile.TemporaryDirectory() as temp_dir,
                self.runtime(temp_dir),
            ):
                with self.bridge.RATE_LIMIT_LOCK:
                    self.bridge.RATE_LIMIT_STATE.clear()
                mission, slot_key = self.scheduled_radar()
                if case_name == "v2":
                    mission = self.requeue_v2_radar_retry(
                        temp_dir,
                        mission,
                        slot_key,
                    )
                tier = (
                    self.bridge.load_orchestration_contract()
                    .get("modelTiers", {})
                    .get(mission["modelTier"], {})
                )
                max_runs = self.bridge.clamp_int(
                    tier.get("maxRunsPerHour"), 12, 1, 200
                )
                rate_key = (
                    f"real:{mission['owner']}:{mission['toolId']}:"
                    f"{mission['modelTier']}"
                )
                existing_count = max_runs - 5
                allowed, _retry, existing = self.bridge.reserve_rate_limit_slots(
                    rate_key,
                    max_runs,
                    existing_count,
                    consume=True,
                )
                self.assertTrue(allowed)
                runner = mock.Mock()
                finish = mock.Mock()
                with (
                    mock.patch.object(
                        self.bridge,
                        "bridge_status",
                        return_value={"codex": {"status": "ready"}},
                    ),
                    mock.patch.object(
                        self.bridge,
                        "codex_rate_limits",
                        return_value=self.quota(),
                    ),
                    mock.patch.object(
                        self.bridge,
                        "_collaboration_quota_gate",
                        return_value={"allowed": True, "reason": "ready"},
                    ),
                    mock.patch.object(self.bridge, "run_safe_command", runner),
                    mock.patch.object(self.bridge, "finish_auto_mission", finish),
                ):
                    self.bridge.process_auto_mission(
                        f"worker-radar-capacity-{case_name}",
                        mission,
                    )
                stored = self.bridge.find_mission(mission["id"])
                with self.bridge.RATE_LIMIT_LOCK:
                    rate_rows = self.bridge._load_persisted_rate_limits_unlocked()[
                        rate_key
                    ]

                runner.assert_not_called()
                finish.assert_not_called()
                self.assertEqual(stored["status"], "queued")
                self.assertEqual(stored["phase"], "auto_guarded_deferred")
                self.assertEqual(stored["attemptCount"], 0)
                self.assertEqual(
                    stored["execution"]["lastDeferredReason"],
                    "corrective_open_hourly_capacity_insufficient",
                )
                self.assertEqual(len(existing), existing_count)
                self.assertEqual(len(rate_rows), existing_count)

    def test_claim_time_radar_digest_mutation_fails_before_consuming_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.runtime(temp_dir):
            mission, _ = self.scheduled_radar()
            claimed = copy.deepcopy(mission)
            claimed["status"] = "running"
            claimed["workflowContext"]["inputDigest"] = "f" * 64
            claimed["execution"].update(
                {
                    "leaseId": "lease-radar-claim-mutation",
                    "workerId": "worker-radar-claim-mutation",
                    "dispatchState": "running",
                }
            )
            real_reserve = self.bridge.reserve_rate_limit_slots
            reserve = mock.Mock(side_effect=real_reserve)
            runner = mock.Mock()
            finish = mock.Mock()
            with (
                mock.patch.object(
                    self.bridge,
                    "bridge_status",
                    return_value={"codex": {"status": "ready"}},
                ),
                mock.patch.object(
                    self.bridge,
                    "codex_rate_limits",
                    return_value=self.quota(),
                ),
                mock.patch.object(
                    self.bridge,
                    "_collaboration_quota_gate",
                    return_value={"allowed": True, "reason": "ready"},
                ),
                mock.patch.object(
                    self.bridge,
                    "reserve_rate_limit_slots",
                    reserve,
                ),
                mock.patch.object(
                    self.bridge,
                    "claim_auto_mission",
                    return_value=claimed,
                ),
                mock.patch.object(self.bridge, "run_safe_command", runner),
                mock.patch.object(self.bridge, "finish_auto_mission", finish),
                mock.patch.object(self.bridge, "update_mission_worker_state"),
                mock.patch.object(
                    self.bridge,
                    "invalidate_codex_rate_limit_cache",
                ),
            ):
                self.bridge.process_auto_mission(
                    "worker-radar-claim-mutation",
                    mission,
                )

        runner.assert_not_called()
        self.assertEqual(len(reserve.call_args_list), 1)
        self.assertFalse(reserve.call_args.kwargs["consume"])
        finish.assert_called_once()
        process_receipt = finish.call_args.args[2]
        result = finish.call_args.args[3]
        self.assertFalse(process_receipt["processStarted"])
        self.assertIn(
            result["status"],
            {
                "radar_dynamic_open_reservation_invalid",
                "trading_system_required_open_urls_changed",
            },
        )

    def test_read_model_exposes_sanitized_retry_failure_and_remaining_status(self) -> None:
        mission = {
            "id": "mission-radar-retry",
            "status": "failed",
            "targetId": "left_audit_crystals",
            "reportType": "indicator_scout_report",
            "errorCode": "radar_evidence_open_verification_failed",
            "workflowContext": {
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
            },
            "correctiveRetry": {
                "kind": self.bridge.RADAR_EVIDENCE_CORRECTIVE_RETRY_KIND,
                "attemptCount": 1,
                "maximumAttempts": 1,
                "remainingAttempts": 0,
                "status": "exhausted",
                "failureReasonCode": "radar_evidence_urls_not_all_opened",
                "terminalFailureReasonCode": "radar_evidence_open_verification_failed",
            },
        }
        health = self.bridge._radar_website_tool_read_model(
            [],
            settings={},
            bridge={"codex": {"status": "ready"}, "time": self.bridge.utc_now()},
            missions=[mission],
            schedule={"lastRunStatus": "failed", "lastError": "invalid_output"},
        )["serviceHealth"]

        self.assertEqual(
            health["lastFailureReasonCode"],
            "radar_evidence_open_verification_failed",
        )
        self.assertEqual(health["automaticCorrectiveRetry"]["status"], "exhausted")
        self.assertEqual(health["automaticCorrectiveRetry"]["attempted"], 1)
        self.assertEqual(health["automaticCorrectiveRetry"]["remaining"], 0)
        self.assertFalse(health["automaticCorrectiveRetry"]["newDailyReservation"])


if __name__ == "__main__":
    unittest.main()
