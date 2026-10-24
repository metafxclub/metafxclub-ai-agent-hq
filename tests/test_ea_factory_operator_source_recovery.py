"""Real temporary Source/spec/receipt stores; no AI or terminal is executed."""
import copy
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

import test_ea_factory_compact_v3 as compact
import test_ea_factory_followup_hardening as support


class OperatorSourceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = support.load_bridge()

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.reports = self.root / "data" / "runtime" / "reports"
        self.reports.mkdir(parents=True)
        self.real_append_audit_once = self.bridge.append_audit_once
        for name, value in (("PROJECT_ROOT", self.root), ("RUNTIME_REPORTS_DIR", self.reports),
                            ("RUNTIME_DIR", self.reports.parent), ("AUDIT_PATH", self.reports.parent / "bridge-audit.jsonl"),
                            ("MISSIONS_PATH", self.reports.parent / "missions.json"),
                            ("EA_FACTORY_STATE_PATH", self.reports.parent / "ea-factory-state.json")):
            self.patch(name, new=value)
        for name in ("append_audit", "append_audit_once", "ensure_runtime_dir"):
            self.patch(name)
        self.patch("_ea_factory_require_top_header_locks", return_value={})
        self.patch("_ea_factory_one_click_terminal_binding_current", return_value=True)
        self.dispatch = self.patch("run_dashboard_workflow_action", side_effect=AssertionError("No AI dispatch during recovery"))
        self.start = self.patch("_start_ea_factory_one_click_thread", side_effect=AssertionError("No coordinator during recovery"))
        for name in ("EA_FACTORY_ONE_CLICK_THREADS", "MISSION_WORKER_PROCESSES"):
            self.stack.enter_context(mock.patch.dict(getattr(self.bridge, name), {}, clear=True))
        fixture = compact.EAFactoryCompactV3IntegrationTests()
        fixture.bridge = self.bridge
        self.record, self.build = fixture._create_initial_build(self.root, "expert_advisor")
        self.build["coverageStatus"] = "compact_current"
        self.stage = self.bridge._ea_factory_stage_row(self.build, "generate_source")
        self.stage.update(status="failed", blockedReasonCode="invalid_output",
                          missionId="mission-recovery-original-failed", evidenceVerified=False,
                          requestIdempotencyKey="original-source-request", startedAt=self.bridge.utc_now())
        self.stage["requestDigest"] = self.bridge._ea_factory_advance_request_digest(self.build, "generate_source")
        self.stage["missionIdempotencyKey"] = self.bridge._ea_factory_stage_mission_idempotency_key(
            self.build["id"], "generate_source", self.stage["requestIdempotencyKey"])
        self.stage["manualRetryCount"] = 3
        self.stage["manualRetryHistory"] = [{"attempt": n, "idempotencyKey": f"retry-key-{n}",
            "failedMissionId": f"mission-old-failed-{n}", "failureCode": "invalid_output",
            "previousStatus": "failed", "requestedAt": self.bridge.utc_now(),
            "advanceIdempotencyKey": self.bridge._ea_factory_source_retry_advance_key(
                self.build["id"], f"mission-old-failed-{n}", f"retry-key-{n}")}
            for n in range(1, 4)]
        other = support.EaFactoryFollowupHardeningTests()
        other.bridge = self.bridge
        _b, _s, _brief, context = other.factory_generation_fixture(self.build["id"])
        inputs = {"sourceReportId": self.build["sourceReportId"], "platform": self.build["platform"],
                  "brief": self.bridge._ea_factory_generation_brief(self.build)}
        source, transfer = context["source"], context["agentTransfer"]
        transfer["sourceReportId"] = self.build["sourceReportId"]
        raw = {"reportId": self.build["sourceReportId"], "sourceKind": "report", "sourcePropId": source["propId"],
               "sourceMissionId": source["missionId"], "transferAgentId": source["transferAgentId"],
               "type": source["type"], "status": source["status"], "agentTransfer": transfer}
        context = self.bridge._dashboard_workflow_lineage("right_server_racks", "build_strategy_code", inputs, raw,
            trigger_source="backend", plugin_profile=self.bridge._trusted_workflow_plugin_profile("right_server_racks", "build_strategy_code", inputs))
        self.mission = {"id": self.stage["missionId"], "idempotencyKey": self.stage["missionIdempotencyKey"],
            "status": "failed", "errorCode": "invalid_output", "owner": "ea_developer", "requester": "human",
            "toolId": "codex_cli_task", "targetId": "right_server_racks", "reportType": "ea_build_report",
            "executionMode": "auto_guarded", "autoEligible": True, "requiresHumanApproval": False,
            "workflowContext": context, "attemptCount": 1, "completedAt": self.bridge.utc_now(),
            "reportIds": ["report-recovery-original-failed"], "execution": {"processStarted": True, "exitCode": 1}}
        self.bridge.save_missions([self.mission])
        self.failure = {"id": self.mission["reportIds"][0], "type": "ea_build_report", "status": "blocked",
                        "linkedMissionId": self.mission["id"], "linkedPropId": "right_server_racks", "workflowContext": context}
        self.bridge.write_json(self.reports / f"{self.failure['id']}.json", self.failure)
        self.run = {"schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION, "runId": "ea-run-recovery-failed",
                    "idempotencyKey": "original-one-click-key", "requestDigest": self.bridge._ea_factory_one_click_request_digest(self.build),
                    "status": "failed", "currentStageId": "generate_source", "failureCode": "invalid_output",
                    "startedAt": self.bridge.utc_now(), "updatedAt": self.bridge.utc_now(), "completedAt": self.bridge.utc_now(),
                    "terminalBinding": {"platform": "mt4", "candidateId": "mtc-recovery-terminal", "selectionRevision": 7, "bindingDigest": "c" * 64}}
        self.build["oneClickRun"] = copy.deepcopy(self.run)
        self.state = {"schemaVersion": self.bridge.EA_FACTORY_STATE_SCHEMA_VERSION, "sourceSnapshots": [],
                      "customSources": [], "builds": [self.build], "createReservations": []}
        self.bridge._write_ea_factory_state_unlocked(self.state)
        self.content = fixture._compact_ea_source(self.record["strategyBriefDigest"])
        self.payload = {"idempotencyKey": "operator-source-recovery-test", "strategySpecDigest": self.build["workspace"]["strategySpecDigest"],
                        "failedMissionId": self.mission["id"], "failureReportId": self.failure["id"],
                        "fileName": "OperatorRecovered.mq4", "content": self.content}

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(self.bridge, name, **kwargs))

    def submit(self, payload=None):
        return self.bridge.recover_ea_factory_build_source(self.build["id"], payload or self.payload)

    def reload(self):
        self.bridge._invalidate_ea_factory_state_cache()
        return self.bridge._load_ea_factory_state_unlocked()["builds"][0]

    def test_valid_source_is_immutable_and_original_failure_retry_and_run_are_preserved(self):
        result = self.submit()
        self.assertFalse(result["workerStarted"])
        build = self.reload()
        self.assertEqual(build["oneClickRun"], self.run)
        self.assertEqual(build["sourceRecoveryHistory"][0]["reservation"]["previousStage"], self.stage)
        source = self.bridge._ea_factory_stage_row(build, "generate_source")
        self.assertEqual(source["manualRetryCount"], 3)
        self.assertEqual(source["manualRetryHistory"], self.stage["manualRetryHistory"])
        self.assertEqual(source["status"], "completed")
        self.assertEqual(self.bridge._ea_factory_build_current_stage_id(build), "source_review")
        missions = self.bridge.load_missions()
        self.assertEqual(next(row for row in missions if row["id"] == self.mission["id"]), self.mission)
        self.assertEqual(len(missions), 2)
        recovery = next(row for row in missions if row["id"] == result["recoveryMissionId"])
        self.assertEqual(recovery["toolId"], "manager_mission")
        self.assertFalse(recovery["autoEligible"])
        self.assertEqual(recovery["attemptCount"], 0)
        report = self.bridge.read_json(self.reports / f"{result['reportId']}.json", None)
        self.assertIsNotNone(self.bridge._workflow_source_binding("right_server_racks", "review_source_code", report, missions))
        self.assertIsNone(self.bridge._trusted_backend_ea_factory_worker_sandbox(recovery))
        self.bridge._ea_factory_sync_build_status(build, missions=missions, reports=[report], ingest_sources=True)
        self.assertEqual(self.bridge._ea_factory_stage_row(build, "generate_source")["status"], "completed")
        self.dispatch.assert_not_called()
        self.start.assert_not_called()

    def test_idempotent_replay_preserves_all_evidence_and_second_recovery_conflicts(self):
        first = self.submit()
        build, missions = self.reload(), self.bridge.load_missions()
        replay = self.submit()
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(first["reportId"], replay["reportId"])
        self.assertEqual(self.reload(), build)
        self.assertEqual(self.bridge.load_missions(), missions)
        for change in ({"idempotencyKey": "other-key"}, {"content": self.content + "\n"}):
            with self.subTest(change=list(change)), self.assertRaises(self.bridge.RequestError):
                self.submit({**self.payload, **change})

    def test_invalid_source_does_not_create_reservation_mission_or_program(self):
        with self.assertRaises(self.bridge.RequestError) as caught:
            self.submit({**self.payload, "content": "#property strict\nvoid OnTick(){}"})
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(self.bridge.load_missions(), [self.mission])
        self.assertFalse(any(path.exists() for path in self.bridge._ea_factory_source_recovery_files(self.build)))
        self.assertFalse(self.bridge._ea_factory_source_program_exists(self.build))

    def test_identity_and_filename_and_size_rejected_before_writes(self):
        for change in ({"strategySpecDigest": "f" * 64}, {"failedMissionId": "mission-other"},
                       {"failureReportId": "report-other"}, {"fileName": "../outside.mq4"},
                       {"fileName": "wrong.mq5"}, {"content": "a" * (48 * 1024 + 1)}, {"allowUnsafe": True}):
            with self.subTest(change=list(change)), self.assertRaises((self.bridge.RequestError, ValueError)):
                self.submit({**self.payload, **change})
        self.assertFalse(any(path.exists() for path in self.bridge._ea_factory_source_recovery_files(self.build)))

    def test_tampered_receipt_original_failure_source_or_retry_fails_after_reload(self):
        self.submit()
        build = self.reload()
        for mutate in (lambda row: row["sourceRecoveryHistory"][0]["reservation"]["previousRun"].update(status="completed"),
                       lambda row: self.bridge._ea_factory_stage_row(row, "generate_source").update(manualRetryCount=0, manualRetryHistory=[]),
                       lambda row: row.update(sourceRecoveryHistory=[])):
            candidate = copy.deepcopy(build)
            mutate(candidate)
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_build(candidate)
        original = self.bridge.load_missions()
        changed = copy.deepcopy(original)
        next(row for row in changed if row["id"] == self.mission["id"])["status"] = "completed"
        self.bridge.save_missions(changed)
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.reload()
        self.bridge.save_missions(original)
        source = self.root / "workspace" / "ea-factory" / self.build["id"] / "Source" / self.payload["fileName"]
        source.write_text(self.content + "\n// changed", encoding="utf-8")
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.reload()

    def test_original_run_resumes_only_at_review_with_archived_failure_intact(self):
        b = self.bridge
        spec_stage = b._ea_factory_stage_row(self.build, "strategy_spec")
        spec_mission = {"id": spec_stage["missionId"], "status": "completed", "owner": "mission_archivist",
                        "reportIds": [spec_stage["reportId"]], "updatedAt": b.utc_now()}
        b.save_missions(b.load_missions() + [spec_mission])
        b.write_json(self.reports / f"{spec_stage['reportId']}.json", {
            "id": spec_stage["reportId"], "status": "ready", "linkedMissionId": spec_stage["missionId"]})
        result = self.submit()
        before = self.reload()
        self.start.side_effect = None
        self.start.return_value = True
        self.patch("_ea_factory_one_click_read_model", side_effect=lambda row: copy.deepcopy(row["oneClickRun"]))
        resumed = b.run_ea_factory_build_one_click(self.build["id"], {"idempotencyKey": self.run["idempotencyKey"]})
        self.assertEqual(resumed["kind"], "ea_factory_one_click_resumed")
        self.assertTrue(resumed["workerStarted"])
        current = self.reload()
        self.assertEqual(current["oneClickRun"]["runId"], self.run["runId"])
        self.assertEqual(current["oneClickRun"]["currentStageId"], "source_review")
        self.assertEqual(current["sourceRecoveryHistory"], before["sourceRecoveryHistory"])
        self.assertEqual(current["sourceRecoveryHistory"][0]["reservation"]["previousRun"], self.run)
        self.assertEqual(b._ea_factory_one_click_next_action(self.build["id"])["stageId"], "source_review")
        self.assertEqual(b._ea_factory_stage_row(current, "generate_source")["reportId"], result["reportId"])
        self.dispatch.assert_not_called()

    def audit_rows(self):
        path = self.bridge.AUDIT_PATH
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_real_audit_event_is_written_once_and_exact_replay_preserves_evidence(self):
        self.patch("append_audit_once", new=self.real_append_audit_once)
        result = self.submit()
        before, missions = self.reload(), self.bridge.load_missions()
        events = self.audit_rows()
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0]["eventId"].startswith("ea-source-recovered-"))
        self.assertEqual(events[0]["recoveryId"], result["recoveryId"])
        self.assertEqual(events[0]["manualRetryCount"], 3)
        self.assertFalse(events[0]["aiExecuted"])
        self.assertTrue(self.submit()["idempotentReplay"])
        self.assertEqual(self.audit_rows(), events)
        self.assertEqual(self.reload(), before)
        self.assertEqual(self.bridge.load_missions(), missions)

    def test_real_audit_failure_after_commit_is_repaired_by_same_intent_without_duplicate_work(self):
        audit = self.patch("append_audit_once", side_effect=self.bridge.DataIntegrityError("Injected audit interruption"))
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.submit()
        committed, missions = self.reload(), self.bridge.load_missions()
        receipt = committed["sourceRecoveryHistory"][0]
        self.assertEqual(self.audit_rows(), [])
        audit.side_effect = self.real_append_audit_once
        result = self.submit()
        self.assertTrue(result["idempotentReplay"])
        self.assertEqual(result["reportId"], receipt["reportId"])
        self.assertEqual(self.reload(), committed)
        self.assertEqual(self.bridge.load_missions(), missions)
        self.assertEqual(len(self.audit_rows()), 1)
        self.assertFalse(result["workerStarted"])
        self.dispatch.assert_not_called()
        self.start.assert_not_called()

    def test_real_audit_event_collision_is_rejected_without_changing_committed_recovery(self):
        self.patch("append_audit_once", new=self.real_append_audit_once)
        self.submit()
        committed, missions = self.reload(), self.bridge.load_missions()
        events = self.audit_rows()
        events[0]["sourceDigest"] = "f" * 64
        self.bridge.AUDIT_PATH.write_text(json.dumps(events[0]) + "\n", encoding="utf-8")
        before = self.bridge.AUDIT_PATH.read_bytes()
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.submit()
        self.assertEqual(self.bridge.AUDIT_PATH.read_bytes(), before)
        self.assertEqual(self.reload(), committed)
        self.assertEqual(self.bridge.load_missions(), missions)


if __name__ == "__main__":
    unittest.main()
