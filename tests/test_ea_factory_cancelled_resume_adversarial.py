"""Independent adversarial checks for pre-visible same-Build continuation.

Persistent stores and external dispatch are replaced, while continuation identity,
workflow lineage, archive validation and coordinator phase selection stay real.
"""
import copy
import json
import unittest
from contextlib import ExitStack
from unittest import mock

import test_ea_factory_followup_hardening as workflow_support


class EaFactoryCancelledResumeAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = workflow_support.load_bridge()

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        fixture = workflow_support.EaFactoryFollowupHardeningTests()
        fixture.bridge = self.bridge
        self.build, self.source, _brief, lineage = fixture.factory_generation_fixture(
            "ea-build-continuation-adversarial"
        )
        self.build.update(platform="mt5", artifactKind="expert_advisor", versions=[],
                          createRequestDigest="b" * 64,
                          createdAt="2026-10-18T01:00:00+00:00")
        self.source.update(status="queued", missionId="mission-exact-last-source",
                           manualRetryCount=3, manualRetryHistory=[{"attempt": 1}, {"attempt": 2}, {"attempt": 3}])
        self.source["requestDigest"] = self.bridge._ea_factory_advance_request_digest(self.build, "generate_source")
        inputs = {"sourceReportId": self.build["sourceReportId"], "platform": "mt5",
                  "brief": self.bridge._ea_factory_generation_brief(self.build)}
        previous_source = lineage["source"]
        raw_source = {"reportId": previous_source["reportId"], "sourceKind": previous_source["kind"],
                      "sourcePropId": previous_source["propId"], "sourceMissionId": previous_source["missionId"],
                      "transferAgentId": previous_source["transferAgentId"], "type": previous_source["type"],
                      "status": previous_source["status"], "agentTransfer": lineage["agentTransfer"]}
        lineage = self.bridge._dashboard_workflow_lineage(
            "right_server_racks", "build_strategy_code", inputs, raw_source,
            trigger_source="backend", plugin_profile=self.bridge._trusted_workflow_plugin_profile(
                "right_server_racks", "build_strategy_code", inputs))
        self.mission = {"id": self.source["missionId"], "idempotencyKey": self.source["missionIdempotencyKey"],
                        "status": "queued", "owner": "ea_developer", "requester": "human",
                        "toolId": "codex_cli_task", "targetId": "right_server_racks", "reportType": "ea_build_report",
                        "executionMode": "auto_guarded", "autoEligible": True, "requiresHumanApproval": False,
                        "workflowContext": lineage, "attemptCount": 0, "startedAt": None,
                        "execution": {"processStarted": False, "dispatchState": "deferred"}}
        self.missions = [self.mission]
        self.old_run = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-cancelled-adversarial", "idempotencyKey": "cancelled-original-run-key",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(self.build),
            "status": "cancelled", "currentStageId": "generate_source", "failureCode": "operator_cancelled",
            "messageTh": "Stopped before visible work", "startedAt": "2026-10-18T01:00:00+00:00",
            "updatedAt": "2026-10-18T01:01:00+00:00", "completedAt": "2026-10-18T01:01:00+00:00",
            "terminalBinding": {"platform": "mt5", "candidateId": "mtc-fixed-terminal", "selectionRevision": 7,
                                "bindingDigest": "c" * 64},
        }
        self.build["oneClickRun"] = copy.deepcopy(self.old_run)
        self.state = {"builds": [self.build], "sourceSnapshots": [], "createReservations": []}
        self.payload = {"previousRunId": self.old_run["runId"],
                        "previousRunDigest": self.bridge._ea_factory_cancelled_run_digest(self.old_run),
                        "idempotencyKey": "explicit-continuation-adversarial-key"}
        for name in ("EA_FACTORY_ONE_CLICK_THREADS", "EA_FACTORY_ONE_CLICK_CANCEL_EVENTS",
                     "EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS", "MISSION_WORKER_PROCESSES"):
            self.stack.enter_context(mock.patch.dict(getattr(self.bridge, name), {}, clear=True))
        self.patch("_load_ea_factory_state_unlocked", return_value=self.state)
        self.patch("load_missions", side_effect=lambda **_kw: self.missions)
        self.patch("_ea_factory_report_rows_snapshot", return_value=[])
        self.sync = self.patch("_ea_factory_sync_build_status", return_value=False)
        self.write = self.patch("_write_ea_factory_state_unlocked")
        self.patch("append_audit")
        self.locks = self.patch("_ea_factory_require_top_header_locks", return_value={})
        self.patch("_ea_factory_one_click_terminal_binding_current", return_value=True)
        self.patch("_ea_factory_source_program_exists", return_value=False)
        self.dispatch = self.patch("run_dashboard_workflow_action", side_effect=AssertionError("No new Mission at continuation"))
        self.retry = self.patch("retry_ea_factory_build_stage", side_effect=AssertionError("No additional source retry"))
        self.projection = self.patch("ea_factory_read_model", side_effect=AssertionError("Receipt must not await projection"))
        self.start = self.patch("_start_ea_factory_one_click_thread", side_effect=self._register_coordinator)

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(self.bridge, name, **kwargs))

    def _register_coordinator(self, build_id, **_kwargs):
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS[build_id] = mock.Mock(is_alive=lambda: True)
        return True

    def submit(self, payload=None):
        return self.bridge.resume_cancelled_ea_factory_build_one_click(self.build["id"], payload or self.payload)

    def stage(self, stage_id):
        return self.bridge._ea_factory_stage_row(self.build, stage_id)

    def complete_source(self):
        """Simulate the existing verifier's committed output, not source admission."""
        self.source.update(status="completed", evidenceVerified=True, reportId="report-source-verified")
        self.mission["status"] = "completed"
        self.build["versions"] = [{"versionId": "v01", "sourceDigest": "d" * 64}]
        self.build["selectedSourceVersion"] = "v01"

    def queued_review(self):
        self.complete_source()
        self.patch("_ea_factory_review_strategy_spec", return_value={"schemaVersion": "ea-factory-strategy-spec-v3"})
        review = self.stage("source_review")
        review.update(status="queued", missionId="mission-exact-review",
                      requestIdempotencyKey="explicit-review-key",
                      requestDigest=self.bridge._ea_factory_advance_request_digest(self.build, "source_review"))
        review["missionIdempotencyKey"] = self.bridge._ea_factory_stage_mission_idempotency_key(
            self.build["id"], "source_review", review["requestIdempotencyKey"])
        inputs = {"sourceReportId": self.source["reportId"], "platform": "mt5",
                  "brief": self.bridge._ea_factory_review_brief(self.build)}
        previous = self.mission["workflowContext"]
        src = previous["source"]
        transfer = {**previous["agentTransfer"], "sourceReportId": self.source["reportId"],
                    "sourcePropId": "right_server_racks", "sourceMissionId": self.source["missionId"],
                    "sourceOwnerAgentId": "ea_developer"}
        raw = {"reportId": self.source["reportId"], "sourceKind": src["kind"],
               "sourcePropId": "right_server_racks", "sourceMissionId": self.source["missionId"],
               "transferAgentId": src["transferAgentId"], "type": "ea_build_report",
               "status": src["status"], "agentTransfer": transfer}
        context = self.bridge._dashboard_workflow_lineage(
            "right_server_racks", "review_source_code", inputs, raw, trigger_source="backend",
            plugin_profile=self.bridge._trusted_workflow_plugin_profile("right_server_racks", "review_source_code", inputs))
        mission = {**copy.deepcopy(self.mission), "id": review["missionId"], "status": "queued",
                   "idempotencyKey": review["missionIdempotencyKey"], "workflowContext": context}
        self.missions.append(mission)
        return review, mission

    def test_adopts_exact_last_attempt_and_waits_without_duplicate_source(self):
        stages, missions = copy.deepcopy(self.build["stages"]), copy.deepcopy(self.missions)
        result = self.submit()
        self.assertEqual(result["adoptedMissionId"], self.mission["id"])
        self.assertNotEqual(result["runId"], self.old_run["runId"])
        self.assertEqual(self.build["stages"], stages)
        self.assertEqual(self.missions, missions)
        self.assertEqual(self.build["oneClickContinuationHistory"][0]["previousRun"], self.old_run)
        self.assertEqual(self.bridge._ea_factory_one_click_next_action(self.build["id"])["kind"], "wait")
        self.assertEqual(self.source["manualRetryCount"], 3)
        self.dispatch.assert_not_called()
        self.retry.assert_not_called()

    def test_replay_with_live_coordinator_never_creates_second_run_or_thread(self):
        first = self.submit()
        before = copy.deepcopy(self.state)
        replay = self.submit()
        self.assertTrue(replay["idempotentReplay"])
        self.assertFalse(replay["workerStarted"])
        self.assertEqual(replay["runId"], first["runId"])
        self.assertEqual(self.state, before)
        self.start.assert_called_once()
        with self.assertRaises(self.bridge.RequestError):
            self.submit({**self.payload, "idempotencyKey": "different-continuation-key"})
        self.assertEqual(self.state, before)

    def test_late_cancel_finalize_and_finish_cannot_touch_successor(self):
        self.submit()
        before = copy.deepcopy(self.state)
        writes_before = self.write.call_count
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.cancel_ea_factory_build_one_click(self.build["id"], {
                "runId": self.old_run["runId"], "idempotencyKey": self.old_run["idempotencyKey"]})
        self.assertFalse(self.bridge._ea_factory_finalize_one_click_cancel_after_worker(
            self.build["id"], self.old_run["runId"], coordinator_returned=True, owned_process_stop_confirmed=True))
        self.bridge._ea_factory_one_click_finish(self.build["id"], expected_run_snapshot=self.old_run,
            status="failed", current_stage_id="generate_source", failure_code="late_old_worker", message_th="Late old callback")
        self.assertEqual(self.state, before)
        self.assertEqual(self.write.call_count, writes_before)

    def test_missing_header_locks_reject_before_ingestion_or_persist(self):
        self.locks.side_effect = self.bridge.RequestError("Locks changed", 409)
        before = copy.deepcopy(self.state)
        with self.assertRaises(self.bridge.RequestError):
            self.submit()
        self.sync.assert_not_called()
        self.start.assert_not_called()
        self.write.assert_not_called()
        self.assertEqual(self.state, before)

    def test_foreign_active_build_cannot_hide_behind_adopted_first_build(self):
        foreign = copy.deepcopy(self.build)
        foreign["id"] = "ea-build-other-active"
        foreign.pop("oneClickRun")
        next(row for row in foreign["stages"] if row["id"] == "generate_source")["missionId"] = "mission-other-active"
        self.state["builds"].append(foreign)
        self.missions.append({"id": "mission-other-active", "status": "running"})
        before = copy.deepcopy(self.state)
        with self.assertRaises(self.bridge.RequestError):
            self.submit()
        self.start.assert_not_called()
        self.write.assert_not_called()
        self.assertEqual(self.state, before)

    def test_coherently_rebound_foreign_workflow_cannot_be_adopted(self):
        bad = self.mission["workflowContext"]
        bad["inputs"]["brief"] = bad["inputs"]["brief"].replace(self.build["id"], "ea-build-foreign")
        bad["inputDigest"] = self.bridge.payload_digest("dashboard-workflow-input-v1", "right_server_racks",
            "build_strategy_code", json.dumps(bad["inputs"], ensure_ascii=False, sort_keys=True))
        before = copy.deepcopy(self.state)
        with self.assertRaises(self.bridge.RequestError):
            self.submit()
        self.assertEqual(self.state, before)
        self.start.assert_not_called()
        self.write.assert_not_called()

    def test_thread_start_failure_replay_attaches_only_same_durable_successor(self):
        self.start.side_effect = RuntimeError("Simulated native thread allocation failure")
        first = self.submit()
        self.assertFalse(first["workerStarted"])
        before_stages = copy.deepcopy(self.build["stages"])
        self.start.side_effect = self._register_coordinator
        replay = self.submit()
        self.assertTrue(replay["idempotentReplay"])
        self.assertTrue(replay["workerStarted"])
        self.assertEqual(replay["runId"], first["runId"])
        self.assertEqual(len(self.build["oneClickContinuationHistory"]), 1)
        self.assertEqual(self.build["stages"], before_stages)
        self.dispatch.assert_not_called()
        self.retry.assert_not_called()

    def test_source_completion_advances_review_without_replaying_source_or_spec(self):
        spec_before = copy.deepcopy(self.stage("strategy_spec"))
        retry_before = copy.deepcopy(self.source["manualRetryHistory"])
        self.submit()
        self.assertEqual(self.bridge._ea_factory_one_click_next_action(self.build["id"])["kind"], "wait")
        self.complete_source()
        self.bridge._ea_factory_revalidated_continuation_history(self.build)
        action = self.bridge._ea_factory_one_click_next_action(self.build["id"])
        self.assertEqual((action["kind"], action["stageId"]), ("advance", "source_review"))
        self.assertEqual(self.stage("strategy_spec"), spec_before)
        self.assertEqual(self.source["manualRetryHistory"], retry_before)
        self.assertEqual(self.source["manualRetryCount"], 3)
        self.assertEqual(self.build["oneClickRun"]["terminalBinding"], self.old_run["terminalBinding"])
        self.patch("_ea_factory_current_thread_owns_active_stage", return_value=True)
        self.patch("deliver_dashboard_report", return_value={"mission": {"id": "mission-review-transfer"}})
        self.patch("_ea_factory_review_strategy_spec", return_value={"schemaVersion": "ea-factory-strategy-spec-v3"})
        self.patch("_ea_factory_recover_false_approval_stage_mission", return_value=None)
        def dispatch_review(prop, payload, **kwargs):
            self.assertEqual(prop, "right_server_racks")
            self.assertEqual(payload["actionId"], "review_source_code")
            self.assertEqual(payload["form"]["sourceReportId"], "report-source-verified")
            self.assertEqual(payload["form"]["brief"], self.bridge._ea_factory_review_brief(self.build))
            self.assertEqual(kwargs, {"trusted_trigger_source": "backend"})
            mission = {"id": "mission-once-only-review", "status": "queued", "requiresHumanApproval": False}
            self.missions.append(mission)
            return {"ok": True, "mission": mission}
        self.dispatch.side_effect = dispatch_review
        args = {"stageId": "source_review", "idempotencyKey": "resumed-review-dispatch"}
        self.bridge.advance_ea_factory_build(self.build["id"], args, include_read_model=False)
        self.bridge.advance_ea_factory_build(self.build["id"], args, include_read_model=False)
        self.dispatch.assert_called_once()
        follow = self.bridge._ea_factory_one_click_next_action(self.build["id"])
        self.assertEqual((follow["kind"], follow["stageId"]), ("wait", "source_review"))
        self.bridge._ea_factory_revalidated_continuation_history(self.build)
        self.retry.assert_not_called()

    def test_verified_source_and_review_use_successor_visible_compile_path(self):
        self.complete_source()
        self.stage("source_review").update(status="completed", evidenceVerified=True, reportId="report-review-verified")
        result = self.submit()
        self.patch("EA_FACTORY_FRONT_OFFICE_CAPABILITY_PROVIDER", new=lambda *_a: {})
        self.patch("EA_FACTORY_VISIBLE_METAEDITOR_COMPILE_HANDLER", new=lambda *_a: {})
        self.patch("_ea_factory_current_thread_owns_active_stage", return_value=True)
        legacy = self.patch("_ea_factory_complete_metaeditor_compile", side_effect=AssertionError("Legacy compile must not run"))
        action = self.bridge._ea_factory_one_click_next_action(self.build["id"])
        self.assertEqual((action["kind"], action["stageId"]), ("advance", "compile_validate"))
        self.assertEqual(self.build["oneClickRun"]["runId"], result["runId"])
        self.assertEqual(self.build["oneClickRun"]["terminalBinding"], self.old_run["terminalBinding"])
        self.assertEqual(self.build["oneClickRun"]["visibleAction"]["attemptCount"], 1)
        # Stop at the existing visible-adapter preparation boundary. Its own
        # evidence/terminal tests cover external execution; this test must not
        # launch MetaEditor or falsely claim real compilation succeeded.
        class VisibleBoundaryReached(Exception):
            pass
        prepare = self.patch("_ea_factory_prepare_visible_front_office_request", side_effect=VisibleBoundaryReached)
        with self.assertRaises(VisibleBoundaryReached):
            self.bridge.advance_ea_factory_build(self.build["id"],
                {"stageId": "compile_validate", "idempotencyKey": "resumed-visible-compile"}, include_read_model=False)
        prepare.assert_called_once_with(self.build, self.stage("compile_validate"))
        self.assertTrue(self.bridge._ea_factory_one_click_front_office_active(self.build, "compile_validate"))
        legacy.assert_not_called()
        self.dispatch.assert_not_called()
        self.retry.assert_not_called()

    def test_archived_review_identity_survives_later_verified_source_version(self):
        review, mission = self.queued_review()
        self.submit()
        self.bridge._ea_factory_revalidated_continuation_history(self.build)
        review.update(status="completed", evidenceVerified=True, reportId="report-review-verified")
        mission["status"] = "completed"
        # A later legitimate repair adds an immutable version. Historical review
        # adoption must remain bound to its own v01 snapshot, not all future bytes.
        self.build["versions"].append({"versionId": "v02", "sourceDigest": "e" * 64})
        self.build["selectedSourceVersion"] = "v02"
        self.bridge._ea_factory_revalidated_continuation_history(self.build)
        self.build["versions"][0]["sourceDigest"] = "f" * 64
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_revalidated_continuation_history(self.build)

    def test_resealed_noncanonical_cancelled_run_is_rejected(self):
        self.submit()
        original = copy.deepcopy(self.build)
        mutations = [
            lambda old: old.update(startedAt="not-a-timestamp"),
            lambda old: old.update(schemaVersion="unrecognized-run-schema"),
            lambda old: old.update(currentStageId="backtest_recheck"),
            lambda old: old["terminalBinding"].update(selectionRevision=-1),
            lambda old: old.update(visibleAction={"state": "reserved"}),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                candidate = copy.deepcopy(original)
                entry = candidate["oneClickContinuationHistory"][0]
                mutate(entry["previousRun"])
                # Recompute all unkeyed linkage digests deliberately. Canonical
                # run/phase/terminal validation must still reject bad evidence.
                entry["previousRunDigest"] = self.bridge._ea_factory_cancelled_run_digest(entry["previousRun"])
                entry["newRunId"] = self.bridge._ea_factory_continuation_run_id(
                    candidate["id"], entry["previousRunId"], entry["idempotencyKey"], entry["previousRunDigest"])
                entry["archiveDigest"] = self.bridge._ea_factory_continuation_archive_digest(entry)
                candidate["oneClickRun"].update(runId=entry["newRunId"],
                    continuationArchiveDigest=entry["archiveDigest"], terminalBinding=entry["previousRun"]["terminalBinding"])
                with self.assertRaises(self.bridge.DataIntegrityError):
                    self.bridge._ea_factory_revalidated_continuation_history(candidate)

    def test_backtest_restart_cannot_commit_mixed_continuation_history(self):
        self.submit()
        before = copy.deepcopy(self.state)
        self.write.reset_mock()
        self.locks.reset_mock()
        with self.assertRaises(self.bridge.RequestError) as caught:
            self.bridge.restart_ea_factory_build_backtest_only(self.build["id"], {
                "runId": self.build["oneClickRun"]["runId"], "idempotencyKey": "unsupported-mixed-restart"})
        self.assertEqual(caught.exception.code, "backtest_restart_continuation_history_unsupported")
        self.assertEqual(self.state, before)
        self.write.assert_not_called()
        self.locks.assert_not_called()


if __name__ == "__main__":
    unittest.main()
