from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECOVERY_PATH = PROJECT_ROOT / "scripts" / "recover-radar-contract-result.py"
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


class RadarContractRecoveryToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.recovery = load_module("radar_contract_recovery_tests", RECOVERY_PATH)
        cls.bridge = load_module("radar_contract_recovery_bridge_tests", BRIDGE_PATH)
        cls.runner = load_module("radar_contract_recovery_runner_tests", RUNNER_PATH)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.runtime = self.root / "data" / "runtime"
        self.runs = self.runtime / "codex-runs"
        self.reports = self.runtime / "reports"
        self.runs.mkdir(parents=True)
        self.reports.mkdir(parents=True)
        self.original_runtime_reports_dir = self.bridge.RUNTIME_REPORTS_DIR
        self.bridge.RUNTIME_REPORTS_DIR = self.reports
        self.mission_id = "mission-radar-recovery-test"
        self.report_id = "auto-report-radar-recovery-test"
        self.slot_key = "indicatorScoutSchedule:2026-08-14:manual-0123456789abcdef"
        self.workflow_inputs = {"maxItems": 1}
        self.input_digest = self.bridge.payload_digest(
            "dashboard-workflow-input-v1",
            "left_audit_crystals",
            "discover_new_indicators",
            json.dumps(self.workflow_inputs, ensure_ascii=False, sort_keys=True),
        )
        self.artifact_ref = "data/runtime/codex-runs/run-recovery-test.final.md"
        self.final_path = self.root / self.artifact_ref
        self.stdout_path = self.runs / "run-recovery-test.stdout.log"
        self.url = "https://example.com/public-radar-recovery-fixture"
        self.entry = {
            "toolName": "Recovery Fixture EA",
            "toolKind": "ea",
            "platform": "MetaTrader 4",
            "category": "ea converter",
            "version": "1.0",
            "summaryTh": "รายการทดสอบจากหน้าสาธารณะที่มีหลักฐานตรงกับผล Radar",
            "sourceTitle": "Recovery Fixture EA public page",
            "sourceUrl": self.url,
            "publishedAt": None,
            "checkedAt": datetime.now(timezone.utc).isoformat(),
            "verificationStatus": "verified_public_source",
            "availability": "public_page_free_download",
            "eaReadiness": "needs_clarification",
            "missingRules": ["ยังไม่ได้ compile หรือ backtest"],
            "sourceLimitations": ["ตรวจเฉพาะหน้าสาธารณะ"],
            "screenshot": {
                "available": False,
                "status": "not_available",
                "attachmentId": None,
                "artifactRef": None,
            },
        }
        self.payload = self._payload(self.entry)
        self._write_artifacts(self.payload)
        procedure = self.bridge._plugin_procedure_storage(
            self.bridge.equipment_action_profile(
                "left_audit_crystals", "discover_new_indicators"
            )
        )
        self.mission = {
            "id": self.mission_id,
            "title": "Radar recovery fixture",
            "detail": "read-only Radar fixture",
            "owner": "codex_mcp_operator",
            "toolId": "codex_web_research",
            "targetId": "left_audit_crystals",
            "status": "blocked",
            "phase": "auto_guarded_radar_output_contract_invalid",
            "workStatus": "radar_output_contract_invalid",
            "errorCode": "radar_output_contract_invalid",
            "reportType": "indicator_scout_report",
            "executionMode": "auto_guarded",
            "autoEligible": True,
            "requiresHumanApproval": False,
            "autoQueuedAt": "2026-08-14T12:00:00+00:00",
            "budget": {"outputLimitChars": 20000},
            "result": "old blocked summary",
            "artifactPath": self.artifact_ref,
            "reportIds": [self.report_id],
            "createdAt": "2026-08-14T12:00:00+00:00",
            "updatedAt": "2026-08-14T12:01:00+00:00",
            "completedAt": "2026-08-14T12:01:00+00:00",
            "approval": {
                "required": False,
                "state": "not_required",
                "gateMode": "not_required",
            },
            "execution": {
                "schema": "auto-guarded-execution-v1",
                "authorizationSource": "backend_auto_policy",
                "authorizationDecision": "allowed",
                "authorizationPolicyVersion": "backend-auto-safe-v1",
                "authorizationReason": "routine_internal_or_read_only",
                "authorizationId": "authorization-radar-recovery-test",
                "autoQueuedAt": "2026-08-14T12:00:00+00:00",
                "authorizationIssuedAt": "2026-08-14T12:00:00+00:00",
                "dispatchState": "blocked",
                "processStarted": True,
                "webSearchEnabled": True,
                "webSearchMode": "live",
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
                "controlPlaneWritable": False,
                "writeRoots": [],
                "automaticRetry": False,
                "completedAt": "2026-08-14T12:01:00+00:00",
            },
            "workflowContext": {
                "schemaVersion": "dashboard-workflow-lineage-v1",
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
                "coordinationMode": self.bridge.DASHBOARD_WORKFLOW_COORDINATION_MODE,
                "source": None,
                "agentTransfer": None,
                "inputs": copy.deepcopy(self.workflow_inputs),
                "inputDigest": self.input_digest,
                "submittedAt": "2026-08-14T12:00:00+00:00",
                "triggerSource": "backend",
                "executionReservation": {
                    "settingsKey": "indicatorScoutSchedule",
                    "bangkokDate": "2026-08-14",
                    "slotKey": self.slot_key,
                    "maximumRunsPerDay": 1,
                    "source": "manual_or_backend",
                },
                "pluginProcedure": procedure,
            },
            "workflowOutputContract": {
                "valid": False,
                "failureCode": "radar_output_contract_invalid",
            },
            "webSearchUsed": True,
            "webSearchEvidenceVerified": True,
        }
        self.mission["execution"]["authorizationPayloadDigest"] = (
            self.bridge.mission_payload_digest(self.mission)
        )
        raw_result = json.dumps(self.payload, ensure_ascii=False, separators=(",", ":"))
        parsed_result = self.runner.parse_work_result(
            raw_result, 20000, "radar_website_tool"
        )
        current_receipt = self.bridge.validate_dashboard_workflow_output_contract(
            self.mission, parsed_result
        )
        old_receipt = copy.deepcopy(current_receipt)
        old_receipt.update({
            "valid": False,
            "failureCode": "radar_output_contract_invalid",
            "providedFields": [],
            "values": {},
            "missingFields": ["entries"],
            "missingEvidenceKinds": [
                kind
                for kind in current_receipt["expectedEvidenceKinds"]
                if kind != "source_url"
            ],
            "entryErrors": ["entry_1_invalid_enum"],
        })
        old_receipt.pop("enumNormalizations", None)
        self.mission["workflowOutputContract"] = old_receipt
        self.report = {
            "id": self.report_id,
            "type": "indicator_scout_report",
            "title": "Radar recovery fixture",
            "summary": "old blocked summary",
            "ownerAgentId": "codex_mcp_operator",
            "linkedMissionId": self.mission_id,
            "linkedPropId": "left_audit_crystals",
            "status": "blocked",
            "findings": ["old finding"],
            "metrics": {"workflowOutput": copy.deepcopy(old_receipt)},
            "risks": ["radar_output_contract_invalid"],
            "nextActions": ["old action"],
            "evidence": [{"label": "fixture", "url": self.url, "note": "public"}],
            "artifacts": [self.artifact_ref],
            "workflowContext": copy.deepcopy(self.mission["workflowContext"]),
            "createdAt": "2026-08-14T12:01:00+00:00",
            "updatedAt": "2026-08-14T12:01:00+00:00",
        }
        self.settings = {
            "version": "dashboard-workflow-settings-v1",
            "indicatorScoutSchedule": {
                "requestedEnabled": True,
                "times": ["09:00"],
                "timezone": "Asia/Bangkok",
                "automaticDailyRadarVersion": 1,
                "lastAttemptAt": "2026-08-14T12:00:01+00:00",
                "lastAttemptSlotKey": self.slot_key,
                "lastRunAt": "2026-08-14T12:00:01+00:00",
                "lastMissionId": self.mission_id,
                "lastSnapshotId": None,
                "lastSlotKey": self.slot_key,
                "lastRunStatus": "blocked",
                "lastResultKind": "mission_auto_queued",
                "lastIdempotentReplay": False,
                "lastError": "radar_output_contract_invalid",
                "lastErrorAt": "2026-08-14T12:01:00+00:00",
                "pendingSlotKey": None,
                "pendingScheduledAt": None,
                "dailyExecutionDate": "2026-08-14",
                "dailyExecutionCount": 1,
                "dailyExecutionSlotKeys": [self.slot_key],
                "dailyExecutionLastReservedAt": "2026-08-14T12:00:00Z",
            },
        }
        self._write_stores()

    def tearDown(self) -> None:
        self.bridge.RUNTIME_REPORTS_DIR = self.original_runtime_reports_dir
        self.temporary.cleanup()

    def _payload(self, entry: dict) -> dict:
        return {
            "status": "completed",
            "summary": "พบรายการ Radar สาธารณะที่ตรวจหลักฐานแล้วหนึ่งรายการ",
            "findings": ["ผลมาจากหน้าสาธารณะ"],
            "nextSteps": ["ให้ Backend คำนวณข้อมูลรายการซ้ำ"],
            "evidence": [{"label": "fixture", "url": self.url, "note": "public"}],
            "blockedCapability": "",
            "contractFields": [
                {
                    "field": "entries",
                    "value": json.dumps([entry], ensure_ascii=False, separators=(",", ":")),
                }
            ],
            "evidenceKinds": [
                "source_url",
                "source_title",
                "checked_at",
                "ea_readiness",
                "public_availability_status",
            ],
        }

    def _write_artifacts(self, payload: dict, *, terminal: bool = True) -> None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        parsed = self.runner.parse_work_result(raw, 20000, "radar_website_tool")
        final = self.runner.format_work_report(parsed, 20000)
        self.final_path.write_text(final, encoding="utf-8", newline="")
        events = [
            {"type": "thread.started", "thread_id": "fixture-thread"},
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {
                    "id": "ws_fixture",
                    "type": "web_search",
                    "query": "public Radar fixture",
                },
            },
            {
                "type": "item.completed",
                "item": {"id": "message_fixture", "type": "agent_message", "text": raw},
            },
        ]
        if terminal:
            events.append({"type": "turn.completed", "usage": {"output_tokens": 1}})
        self.stdout_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in events) + "\n",
            encoding="utf-8",
            newline="",
        )

    def _write_stores(self) -> None:
        (self.runtime / "missions.json").write_bytes(
            json_bytes({"updatedAt": "2026-08-14T12:01:00+00:00", "missions": [self.mission]})
        )
        (self.reports / f"{self.report_id}.json").write_bytes(json_bytes(self.report))
        (self.runtime / "dashboard-workflow-settings.json").write_bytes(json_bytes(self.settings))
        (self.runtime / "bridge-audit.jsonl").write_text(
            json.dumps({"time": "2026-08-14T12:00:00Z", "type": "fixture.start"}) + "\n",
            encoding="utf-8",
            newline="",
        )

    def _recover(self, *, apply: bool = False, expected=None, fault=None):
        return self.recovery.recover_radar_contract_result(
            self.root,
            self.mission_id,
            apply=apply,
            expected_hashes=expected,
            bridge=self.bridge,
            runner=self.runner,
            fault_injector=fault,
        )

    def _stored_mission(self) -> dict:
        return json.loads((self.runtime / "missions.json").read_text(encoding="utf-8"))["missions"][0]

    def _stored_report(self) -> dict:
        return json.loads((self.reports / f"{self.report_id}.json").read_text(encoding="utf-8"))

    def _stored_schedule(self) -> dict:
        return json.loads(
            (self.runtime / "dashboard-workflow-settings.json").read_text(encoding="utf-8")
        )["indicatorScoutSchedule"]

    def _primary_paths(self) -> dict[str, Path]:
        return {
            "missions": self.runtime / "missions.json",
            "report": self.reports / f"{self.report_id}.json",
            "settings": self.runtime / "dashboard-workflow-settings.json",
            "audit": self.runtime / "bridge-audit.jsonl",
        }

    def _leave_prepared_journal(self, stage_name: str) -> dict:
        dry = self._recover()

        class HardCrash(BaseException):
            pass

        def crash(stage: str) -> None:
            if stage == stage_name:
                raise HardCrash()

        with self.assertRaises(HardCrash):
            self._recover(
                apply=True,
                expected=dry["expectedHashes"],
                fault=crash,
            )
        return dry

    def _assert_prepared_divergence_is_preserved(
        self,
        stage_name: str,
        target_name: str,
        mutate,
    ) -> None:
        dry = self._leave_prepared_journal(stage_name)
        paths = self._primary_paths()
        mutate(paths[target_name])
        before_retry = {name: path.read_bytes() for name, path in paths.items()}
        with self.assertRaisesRegex(
            self.recovery.RecoveryError,
            rf"prepared_recovery_external_divergence:.*{target_name}",
        ):
            self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertEqual(
            {name: path.read_bytes() for name, path in paths.items()},
            before_retry,
        )

    def test_dry_run_validates_exact_artifacts_without_mutation(self) -> None:
        before = {
            path: path.read_bytes()
            for path in (
                self.runtime / "missions.json",
                self.reports / f"{self.report_id}.json",
                self.runtime / "dashboard-workflow-settings.json",
                self.runtime / "bridge-audit.jsonl",
            )
        }
        result = self._recover()
        self.assertEqual(result["status"], "ready_to_apply")
        self.assertFalse(result["applied"])
        self.assertEqual(result["entriesCount"], 1)
        self.assertEqual(len(result["enumNormalizations"]), 3)
        self.assertTrue(result["reservation"]["preserved"])
        self.assertTrue(all(len(value) == 64 for value in result["expectedHashes"].values()))
        for path, payload in before.items():
            self.assertEqual(path.read_bytes(), payload)
        self.assertEqual(
            list((self.runtime / "recoveries").glob("*.journal.json")), []
        )

    def test_apply_updates_truth_preserves_reservation_and_is_idempotent(self) -> None:
        dry = self._recover()
        reservation_before = self.recovery._reservation_projection(
            self.settings["indicatorScoutSchedule"]
        )
        result = self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertEqual(result["status"], "recovered")
        self.assertTrue(result["applied"])
        mission = self._stored_mission()
        report = self._stored_report()
        schedule = self._stored_schedule()
        self.assertEqual(mission["status"], "completed")
        self.assertEqual(
            mission["phase"], "auto_guarded_completed_recovered_contract_revalidation"
        )
        self.assertIsNone(mission["errorCode"])
        self.assertEqual(mission["execution"]["dispatchState"], "completed")
        self.assertEqual(mission["createdAt"], "2026-08-14T12:00:00+00:00")
        self.assertEqual(mission["updatedAt"], "2026-08-14T12:01:00+00:00")
        self.assertEqual(mission["completedAt"], "2026-08-14T12:01:00+00:00")
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["createdAt"], "2026-08-14T12:01:00+00:00")
        self.assertEqual(report["updatedAt"], "2026-08-14T12:01:00+00:00")
        self.assertEqual(report["metrics"]["entries"][0]["platform"], "mt4")
        self.assertEqual(report["metrics"]["entries"][0]["verificationStatus"], "verified")
        self.assertEqual(report["metrics"]["entries"][0]["availability"], "public")
        self.assertEqual(len(self.bridge._radar_report_entries(report)), 1)
        self.assertEqual(self.bridge.mission_read_model_item(mission)["status"], "completed")
        self.assertEqual(schedule["lastRunStatus"], "completed")
        self.assertEqual(schedule["lastResultKind"], "recovered_contract_revalidation")
        self.assertIsNone(schedule["lastError"])
        self.assertEqual(
            self.recovery._reservation_projection(schedule), reservation_before
        )
        common = mission["recovery"]
        self.assertFalse(common["runnerInvoked"])
        self.assertFalse(common["webSearchInvoked"])
        self.assertFalse(common["mt4Actions"])
        self.assertFalse(common["googleSheetWrites"])
        self.assertTrue(common["reservationPreserved"])
        journal = json.loads((self.root / result["journalPath"]).read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "committed")
        with (self.runtime / "bridge-audit.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"time": "later", "type": "unrelated.event"}) + "\n")
        audit_before_replay = (self.runtime / "bridge-audit.jsonl").read_bytes()
        replay = self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertEqual(replay["status"], "already_recovered")
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual((self.runtime / "bridge-audit.jsonl").read_bytes(), audit_before_replay)

    def test_apply_rejects_stale_compare_and_swap_hash(self) -> None:
        dry = self._recover()
        settings_path = self.runtime / "dashboard-workflow-settings.json"
        original_missions = (self.runtime / "missions.json").read_bytes()
        settings_path.write_bytes(settings_path.read_bytes() + b" ")
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "compare_and_swap_mismatch:settings"
        ):
            self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertEqual((self.runtime / "missions.json").read_bytes(), original_missions)
        self.assertEqual(
            list((self.runtime / "recoveries").glob("*.journal.json")), []
        )

    def test_exact_prestate_rejects_non_auto_safe_mission(self) -> None:
        self.mission["approval"]["required"] = True
        self.mission["approval"]["state"] = "approved"
        self._write_stores()
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "mission_approval_not_auto_safe"
        ):
            self._recover()

    def test_exact_prestate_rejects_wrong_radar_record_bindings(self) -> None:
        mission_path = self.runtime / "missions.json"
        report_path = self.reports / f"{self.report_id}.json"
        original_mission = mission_path.read_bytes()
        original_report = report_path.read_bytes()
        cases = (
            ("target", "mission", lambda value: value.__setitem__("targetId", "other")),
            ("report_type", "mission", lambda value: value.__setitem__("reportType", "other")),
            ("owner", "mission", lambda value: value.__setitem__("owner", "other")),
            (
                "report_context",
                "report",
                lambda value: value["workflowContext"].__setitem__(
                    "actionId", "analyze_daily_market_news"
                ),
            ),
        )
        for label, target, mutate in cases:
            with self.subTest(label=label):
                mission_path.write_bytes(original_mission)
                report_path.write_bytes(original_report)
                path = mission_path if target == "mission" else report_path
                value = json.loads(path.read_text(encoding="utf-8"))
                if target == "mission":
                    value = value["missions"][0]
                    mutate(value)
                    container = json.loads(original_mission.decode("utf-8"))
                    container["missions"][0] = value
                    path.write_bytes(json_bytes(container))
                else:
                    mutate(value)
                    path.write_bytes(json_bytes(value))
                with self.assertRaises(self.recovery.RecoveryError):
                    self._recover()
        mission_path.write_bytes(original_mission)
        report_path.write_bytes(original_report)

    def test_prestate_rejects_noncanonical_or_untrusted_input_digest(self) -> None:
        mission_store = json.loads(
            (self.runtime / "missions.json").read_text(encoding="utf-8")
        )
        mission = mission_store["missions"][0]
        mission["workflowContext"]["inputDigest"] = "f" * 64
        mission["execution"]["authorizationPayloadDigest"] = (
            self.bridge.mission_payload_digest(mission)
        )
        report = self._stored_report()
        report["workflowContext"] = copy.deepcopy(mission["workflowContext"])
        (self.runtime / "missions.json").write_bytes(json_bytes(mission_store))
        (self.reports / f"{self.report_id}.json").write_bytes(json_bytes(report))
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "backend_workflow_binding_invalid"
        ):
            self._recover()

    def test_prestate_rejects_a_fabricated_non_enum_validator_failure(self) -> None:
        receipt = copy.deepcopy(self.mission["workflowOutputContract"])
        receipt["entryErrors"] = ["entry_1_source_url_invalid"]
        self.mission["workflowOutputContract"] = receipt
        self.report["metrics"]["workflowOutput"] = copy.deepcopy(receipt)
        self._write_stores()
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "blocked_receipt_not_enum_only"
        ):
            self._recover()

    def test_artifact_path_escape_is_rejected(self) -> None:
        escaped_final = self.reports / "escaped.final.md"
        escaped_stdout = self.reports / "escaped.stdout.log"
        escaped_final.write_bytes(self.final_path.read_bytes())
        escaped_stdout.write_bytes(self.stdout_path.read_bytes())
        escaped_ref = "data/runtime/codex-runs/../reports/escaped.final.md"
        self.mission["artifactPath"] = escaped_ref
        self.report["artifacts"] = [escaped_ref]
        self._write_stores()
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "final_artifact_outside_codex_runs"
        ):
            self._recover()

    def test_unknown_enum_alias_fails_closed(self) -> None:
        unknown = copy.deepcopy(self.entry)
        unknown["platform"] = "MetaTrader 6"
        self._write_artifacts(self._payload(unknown))
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "backend_contract_still_invalid"
        ):
            self._recover()

    def test_valid_canonical_result_without_alias_receipt_is_not_recoverable(self) -> None:
        canonical = copy.deepcopy(self.entry)
        canonical.update({
            "platform": "mt4",
            "verificationStatus": "verified",
            "availability": "public",
        })
        self._write_artifacts(self._payload(canonical))
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "canonical_alias_normalizations_required"
        ):
            self._recover()

    def test_missing_terminal_turn_completed_is_rejected(self) -> None:
        self._write_artifacts(self.payload, terminal=False)
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "stdout_missing_terminal_turn_completed"
        ):
            self._recover()

    def test_transaction_failure_after_audit_rolls_back_all_primary_bytes(self) -> None:
        dry = self._recover()
        paths = {
            "missions": self.runtime / "missions.json",
            "report": self.reports / f"{self.report_id}.json",
            "settings": self.runtime / "dashboard-workflow-settings.json",
            "audit": self.runtime / "bridge-audit.jsonl",
        }
        before = {name: path.read_bytes() for name, path in paths.items()}

        def fail_after_audit(stage: str) -> None:
            if stage == "audit_appended":
                raise RuntimeError("injected")

        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "recovery_transaction_rolled_back:RuntimeError"
        ):
            self._recover(
                apply=True,
                expected=dry["expectedHashes"],
                fault=fail_after_audit,
            )
        for name, path in paths.items():
            self.assertEqual(path.read_bytes(), before[name], name)
        recovery_id = dry["recoveryId"]
        archived_journals = list(
            (self.runtime / "recoveries" / "rolled-back").glob(
                f"{recovery_id}-*.journal.json"
            )
        )
        self.assertEqual(len(archived_journals), 1)
        journal = json.loads(archived_journals[0].read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "rolled_back")
        backup_missions = self.root / journal["backupPaths"]["missions"]
        self.assertTrue(backup_missions.is_file())

    def test_hard_crash_prepared_journal_restores_then_retries_once(self) -> None:
        dry = self._recover()

        class HardCrash(BaseException):
            pass

        def crash_after_first_store(stage: str) -> None:
            if stage == "missions_written":
                raise HardCrash()

        with self.assertRaises(HardCrash):
            self._recover(
                apply=True,
                expected=dry["expectedHashes"],
                fault=crash_after_first_store,
            )
        prepared = json.loads(
            (
                self.runtime
                / "recoveries"
                / f"{dry['recoveryId']}.journal.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(prepared["status"], "prepared")
        self.assertEqual(self._stored_mission()["status"], "completed")
        recovered = self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertTrue(recovered["preparedJournalRolledBack"])
        self.assertEqual(recovered["status"], "recovered")
        self.assertEqual(self._stored_mission()["status"], "completed")
        committed = json.loads(
            (self.runtime / "recoveries" / f"{dry['recoveryId']}.journal.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(committed["status"], "committed")

    def test_hard_crash_after_audit_removes_partial_audit_before_retry(self) -> None:
        dry = self._recover()

        class HardCrash(BaseException):
            pass

        def crash_after_audit(stage: str) -> None:
            if stage == "audit_appended":
                raise HardCrash()

        with self.assertRaises(HardCrash):
            self._recover(
                apply=True,
                expected=dry["expectedHashes"],
                fault=crash_after_audit,
            )
        prepared = json.loads(
            (
                self.runtime / "recoveries" / f"{dry['recoveryId']}.journal.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            hashlib.sha256(
                (self.runtime / "bridge-audit.jsonl").read_bytes()
            ).hexdigest(),
            prepared["intendedHashes"]["audit"],
        )
        recovered = self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertTrue(recovered["preparedJournalRolledBack"])
        audit_events = [
            json.loads(line)
            for line in (self.runtime / "bridge-audit.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
        matching = [
            row
            for row in audit_events
            if row.get("type") == "radar.contract_result_recovered"
            and row.get("recoveryId") == dry["recoveryId"]
        ]
        self.assertEqual(len(matching), 1)

    def test_prepared_crash_preserves_unknown_missions_divergence(self) -> None:
        def mutate(path: Path) -> None:
            value = json.loads(path.read_text(encoding="utf-8"))
            value["missions"].append({"id": "unrelated-later-mission"})
            path.write_bytes(json_bytes(value))

        self._assert_prepared_divergence_is_preserved(
            "missions_written", "missions", mutate
        )

    def test_prepared_crash_preserves_unknown_report_divergence(self) -> None:
        def mutate(path: Path) -> None:
            value = json.loads(path.read_text(encoding="utf-8"))
            value["unrelatedLaterField"] = True
            path.write_bytes(json_bytes(value))

        self._assert_prepared_divergence_is_preserved(
            "report_written", "report", mutate
        )

    def test_prepared_crash_preserves_unknown_settings_divergence(self) -> None:
        def mutate(path: Path) -> None:
            value = json.loads(path.read_text(encoding="utf-8"))
            value["unrelatedLaterSetting"] = True
            path.write_bytes(json_bytes(value))

        self._assert_prepared_divergence_is_preserved(
            "settings_written", "settings", mutate
        )

    def test_prepared_crash_preserves_unknown_audit_suffix(self) -> None:
        def mutate(path: Path) -> None:
            with path.open("ab") as handle:
                handle.write(b'{"time":"later","type":"unrelated.event"}\n')

        self._assert_prepared_divergence_is_preserved(
            "audit_appended", "audit", mutate
        )

    def test_in_process_failure_does_not_erase_external_divergence(self) -> None:
        dry = self._recover()
        paths = self._primary_paths()
        observed: dict[str, bytes] = {}

        def diverge_then_fail(stage: str) -> None:
            if stage != "audit_appended":
                return
            value = json.loads(paths["settings"].read_text(encoding="utf-8"))
            value["unrelatedConcurrentSetting"] = True
            paths["settings"].write_bytes(json_bytes(value))
            observed.update({name: path.read_bytes() for name, path in paths.items()})
            raise RuntimeError("injected-after-divergence")

        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "recovery_failed_rollback_incomplete"
        ):
            self._recover(
                apply=True,
                expected=dry["expectedHashes"],
                fault=diverge_then_fail,
            )
        self.assertEqual(
            {name: path.read_bytes() for name, path in paths.items()}, observed
        )
        journal = json.loads(
            (
                self.runtime / "recoveries" / f"{dry['recoveryId']}.journal.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(journal["status"], "rollback_incomplete")
        self.assertIn("external_divergence:settings", journal["rollbackErrors"])

    def test_foreign_prepared_journal_blocks_global_store_mutation(self) -> None:
        dry = self._recover()
        recovery_dir = self.runtime / "recoveries"
        recovery_dir.mkdir(parents=True, exist_ok=True)
        foreign_path = recovery_dir / "foreign.journal.json"
        foreign_path.write_bytes(
            json_bytes({
                "schemaVersion": self.recovery.RECOVERY_SCHEMA,
                "recoveryId": "radar-recovery-" + "a" * 32,
                "status": "prepared",
                "missionId": "mission-foreign-recovery",
            })
        )
        foreign_before = foreign_path.read_bytes()
        before = {
            name: path.read_bytes() for name, path in self._primary_paths().items()
        }
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "foreign_incomplete_recovery_journal"
        ):
            self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertEqual(foreign_path.read_bytes(), foreign_before)
        self.assertEqual(
            {name: path.read_bytes() for name, path in self._primary_paths().items()},
            before,
        )

    def test_idempotent_replay_rejects_altered_committed_poststate(self) -> None:
        dry = self._recover()
        self._recover(apply=True, expected=dry["expectedHashes"])
        report_path = self.reports / f"{self.report_id}.json"
        altered = self._stored_report()
        altered["status"] = "blocked"
        report_path.write_bytes(json_bytes(altered))
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "recovered_report_state_invalid"
        ):
            self._recover()

    def test_idempotent_replay_rejects_every_critical_projection_tamper(self) -> None:
        dry = self._recover()
        self._recover(apply=True, expected=dry["expectedHashes"])
        paths = self._primary_paths()
        baseline = {name: path.read_bytes() for name, path in paths.items()}

        def tamper_mission(mutate) -> None:
            store = json.loads(baseline["missions"].decode("utf-8"))
            mutate(store["missions"][0])
            paths["missions"].write_bytes(json_bytes(store))

        def tamper_report(mutate) -> None:
            value = json.loads(baseline["report"].decode("utf-8"))
            mutate(value)
            paths["report"].write_bytes(json_bytes(value))

        def tamper_settings(mutate) -> None:
            value = json.loads(baseline["settings"].decode("utf-8"))
            mutate(value["indicatorScoutSchedule"])
            paths["settings"].write_bytes(json_bytes(value))

        def tamper_audit() -> None:
            events = [
                json.loads(line)
                for line in baseline["audit"].decode("utf-8").splitlines()
                if line.strip()
            ]
            for event in events:
                if event.get("type") == "radar.contract_result_recovered":
                    event["time"] = "tampered"
            paths["audit"].write_bytes(
                ("\n".join(json.dumps(row, separators=(",", ":")) for row in events) + "\n").encode("utf-8")
            )

        cases = (
            (
                "approval",
                lambda: tamper_mission(
                    lambda row: row.__setitem__(
                        "approval",
                        {"required": True, "state": "approved", "gateMode": "manual"},
                    )
                ),
            ),
            (
                "process_started",
                lambda: tamper_mission(
                    lambda row: row["execution"].__setitem__("processStarted", False)
                ),
            ),
            (
                "report_context",
                lambda: tamper_report(
                    lambda row: row["workflowContext"].__setitem__(
                        "actionId", "analyze_daily_market_news"
                    )
                ),
            ),
            (
                "report_findings",
                lambda: tamper_report(lambda row: row.__setitem__("findings", [])),
            ),
            (
                "report_metrics_extra",
                lambda: tamper_report(
                    lambda row: row["metrics"].__setitem__("unexpected", True)
                ),
            ),
            (
                "mission_evidence",
                lambda: tamper_mission(lambda row: row.__setitem__("evidence", [])),
            ),
            (
                "daily_reservation",
                lambda: tamper_settings(
                    lambda row: row.__setitem__(
                        "dailyExecutionLastReservedAt", "tampered"
                    )
                ),
            ),
            ("audit_event_time", tamper_audit),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                for name, path in paths.items():
                    path.write_bytes(baseline[name])
                mutate()
                with self.assertRaises(self.recovery.RecoveryError):
                    self._recover()
        for name, path in paths.items():
            path.write_bytes(baseline[name])

    def test_bound_report_exclusion_keeps_an_older_matching_duplicate(self) -> None:
        older_entry = copy.deepcopy(self.entry)
        older_entry.update({
            "platform": "mt4",
            "verificationStatus": "verified",
            "availability": "public",
        })
        older_report = {
            "id": "older-radar-report",
            "type": "indicator_scout_report",
            "linkedPropId": "left_audit_crystals",
            "status": "ready",
            "metrics": {"entries": [older_entry]},
            "workflowContext": {
                "propId": "left_audit_crystals",
                "actionId": "discover_new_indicators",
            },
            "createdAt": "2026-08-13T00:00:00+00:00",
            "updatedAt": "2026-08-13T00:00:00+00:00",
            "artifacts": [],
        }
        (self.reports / "older-radar-report.json").write_bytes(json_bytes(older_report))
        dry = self._recover()
        applied = self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertEqual(applied["status"], "recovered")
        stored_entry = self._stored_report()["metrics"]["entries"][0]
        self.assertEqual(stored_entry["duplicateStatus"], "duplicate")
        self.assertEqual(stored_entry["duplicateScope"], "local_report_catalog")
        replay = self._recover()
        self.assertEqual(replay["status"], "already_recovered")

    def test_apply_refuses_bridge_control_file(self) -> None:
        dry = self._recover()
        (self.runtime / "bridge-control.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(
            self.recovery.RecoveryError, "bridge_control_present_stop_bridge_before_apply"
        ):
            self._recover(apply=True, expected=dry["expectedHashes"])

    def test_true_process_death_releases_lock_and_recovers_prepared_journal(self) -> None:
        dry = self._recover()
        code = (
            "import importlib.util,json,os,sys\n"
            "from pathlib import Path\n"
            "def load(n,p):\n"
            " s=importlib.util.spec_from_file_location(n,Path(p)); m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m\n"
            "rec=load('recovery_child',sys.argv[1]); bridge=load('bridge_child',sys.argv[2]); runner=load('runner_child',sys.argv[3])\n"
            "root=Path(sys.argv[4]); bridge.RUNTIME_REPORTS_DIR=root/'data'/'runtime'/'reports'\n"
            "def crash(stage):\n"
            " if stage=='missions_written': os._exit(91)\n"
            "rec.recover_radar_contract_result(root,sys.argv[5],apply=True,expected_hashes=json.loads(sys.argv[6]),bridge=bridge,runner=runner,fault_injector=crash)\n"
        )
        child = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                str(RECOVERY_PATH),
                str(BRIDGE_PATH),
                str(RUNNER_PATH),
                str(self.root),
                self.mission_id,
                json.dumps(dry["expectedHashes"], separators=(",", ":")),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(child.returncode, 91, child.stderr)
        lock_path = self.runtime / "recoveries" / ".radar-contract-recovery.lock"
        self.assertTrue(lock_path.exists())
        prepared_path = (
            self.runtime / "recoveries" / f"{dry['recoveryId']}.journal.json"
        )
        self.assertEqual(
            json.loads(prepared_path.read_text(encoding="utf-8"))["status"],
            "prepared",
        )
        recovered = self._recover(apply=True, expected=dry["expectedHashes"])
        self.assertTrue(recovered["preparedJournalRolledBack"])
        self.assertEqual(recovered["status"], "recovered")

    def test_recovery_lock_still_blocks_a_live_owner(self) -> None:
        code = (
            "import importlib.util,sys\n"
            "from pathlib import Path\n"
            "p=Path(sys.argv[1]); s=importlib.util.spec_from_file_location('lock_child_live',p); "
            "m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m)\n"
            "with m._exclusive_recovery_lock(Path(sys.argv[2])):\n"
            " print('READY',flush=True)\n"
            " sys.stdin.buffer.read(1)\n"
        )
        child = subprocess.Popen(
            [sys.executable, "-c", code, str(RECOVERY_PATH), str(self.runtime)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(child.stdout.readline().strip(), "READY")
            with self.assertRaisesRegex(
                self.recovery.RecoveryError, "recovery_lock_already_held"
            ):
                with self.recovery._exclusive_recovery_lock(self.runtime):
                    pass
        finally:
            if child.stdin:
                child.stdin.write("x")
                child.stdin.close()
            child.wait(timeout=10)
            if child.stdout:
                child.stdout.close()
            if child.stderr:
                child.stderr.close()


if __name__ == "__main__":
    unittest.main()
