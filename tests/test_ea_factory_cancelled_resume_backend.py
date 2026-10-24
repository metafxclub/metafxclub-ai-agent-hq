"""Explicit continuation preserves the Build and never allocates duplicate AI work."""
import copy
import json
import threading
import unittest
from contextlib import ExitStack
from unittest import mock

import test_ea_factory_one_click_backend as support


class EaFactoryCancelledResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = support.load_bridge()

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        template = support.EaFactoryOneClickBackendTests()
        template.bridge = self.bridge
        self.build = template.build()
        self.build.update(sourceReportId="report-strategy", workspace={"strategySpecDigest": "c" * 64})
        now = "2026-10-18T01:00:00Z"
        self.build["oneClickRun"] = {
            "schemaVersion": self.bridge.EA_FACTORY_ONE_CLICK_SCHEMA_VERSION,
            "runId": "ea-run-cancelled-original", "idempotencyKey": "old-run-key",
            "requestDigest": self.bridge._ea_factory_one_click_request_digest(self.build),
            "status": "cancelled", "currentStageId": "generate_source",
            "terminalBinding": {"platform": "mt4", "candidateId": "mtc-original", "selectionRevision": 1, "bindingDigest": "d" * 64},
            "failureCode": "operator_cancelled", "messageTh": "Stopped", "startedAt": now,
            "updatedAt": now, "completedAt": now,
        }
        self.stage = self.bridge._ea_factory_stage_row(self.build, "generate_source")
        self.state = template.state(self.build)
        self.missions = []
        self.commits = []
        self.patch("_load_ea_factory_state_unlocked", return_value=self.state)
        self.patch("load_missions", side_effect=lambda **kw: self.missions)
        self.sync = self.patch("_ea_factory_sync_build_status", return_value=False)
        self.write = self.patch("_write_ea_factory_state_unlocked", side_effect=lambda state: self.commits.append(copy.deepcopy(state)))
        self.start = self.patch("_start_ea_factory_one_click_thread", return_value=True)
        self.dispatch = self.patch("run_dashboard_workflow_action", side_effect=AssertionError("Resume must not dispatch AI work directly"))
        self.patch("append_audit")
        self.patch("EA_FACTORY_ONE_CLICK_THREADS", {})
        self.patch("EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS", {})
        self.patch("MISSION_WORKER_PROCESSES", {})
        self.busy = self.patch("_ea_factory_active_worker_payload", return_value=None)
        self.locks = self.patch("_ea_factory_require_top_header_locks")
        self.terminal = self.patch("_ea_factory_one_click_terminal_binding_current", return_value=True)
        self.patch("_ea_factory_stage_can_advance", return_value=True)
        self.patch("_ea_factory_generation_receipt_brief", side_effect=lambda build, value: "bound-brief" if value == "bound-brief" else None)
        self.patch("_ea_factory_review_brief", return_value="bound-review")
        self.patch("_workflow_context_storage", side_effect=lambda value: value)
        self.sandbox = self.patch("_trusted_backend_ea_factory_worker_sandbox", side_effect=lambda mission: {"buildId": self.build["id"], "stageId": "generate_source"})
        self.source_exists = self.patch("_ea_factory_source_program_exists", return_value=False)
        self.request = {"previousRunId": self.build["oneClickRun"]["runId"],
                        "previousRunDigest": self.bridge._ea_factory_cancelled_run_digest(self.build["oneClickRun"]),
                        "idempotencyKey": "explicit-continue-key"}

    def patch(self, name, *args, **kwargs):
        return self.stack.enter_context(mock.patch.object(self.bridge, name, *args, **kwargs))

    def submit(self, payload=None):
        return self.bridge.resume_cancelled_ea_factory_build_one_click(self.build["id"], payload or self.request)

    def queued(self, status="queued"):
        key = "existing-source-request"
        self.stage.update(status=status, missionId="mission-existing-source", requestIdempotencyKey=key,
            requestDigest=self.bridge._ea_factory_advance_request_digest(self.build, "generate_source"),
            missionIdempotencyKey=self.bridge._ea_factory_stage_mission_idempotency_key(self.build["id"], "generate_source", key),
            startedAt="2026-10-18T01:01:00Z", manualRetryCount=3,
            manualRetryHistory=[{"attempt": n, "prior": "preserved"} for n in range(1, 4)])
        inputs = {"sourceReportId": "report-strategy", "platform": "mt4", "brief": "bound-brief"}
        context = {"propId": "right_server_racks", "actionId": "build_strategy_code", "triggerSource": "backend",
            "source": {"reportId": "report-strategy"}, "inputs": inputs,
            "inputDigest": self.bridge.payload_digest("dashboard-workflow-input-v1", "right_server_racks", "build_strategy_code", json.dumps(inputs, ensure_ascii=False, sort_keys=True))}
        mission = {"id": self.stage["missionId"], "status": status, "idempotencyKey": self.stage["missionIdempotencyKey"],
            "owner": "ea_developer", "requester": "human", "toolId": "codex_cli_task", "targetId": "right_server_racks",
            "reportType": "ea_build_report", "executionMode": "auto_guarded", "autoEligible": True,
            "requiresHumanApproval": False, "workflowContext": context, "attemptCount": 0,
            "execution": {"processStarted": False, "dispatchState": "deferred"}, "startedAt": None}
        self.missions.append(mission)
        return mission

    def stopped(self, *, started=False):
        mission = self.queued()
        self.stage.update(status="blocked", blockedReasonCode="ea_factory_cancelled_by_operator", manualRetryCount=1, manualRetryHistory=self.stage["manualRetryHistory"][:1])
        when = "2026-10-18T01:02:00Z"
        mission.update(status="blocked", phase="ea_factory_cancelled_by_operator", errorCode="ea_factory_cancelled_by_operator", completedAt=when)
        mission["execution"].update(dispatchState="blocked", automaticRetry=False, cancelRequestedAt=when, completedAt=when)
        if started:
            mission.update(attemptCount=1, startedAt="2026-10-18T01:01:30Z")
            mission["execution"].update(processStarted=True, processTreeTerminated=True)
        return mission

    def test_queued_quota_deferred_exact_mission_is_adopted_without_counter_or_stage_changes(self):
        self.queued()
        before = copy.deepcopy(self.build)
        response = self.submit()
        self.assertEqual(self.build["stages"], before["stages"])
        self.assertEqual(self.build["versions"], [])
        self.assertEqual(response["adoptedMissionId"], "mission-existing-source")
        self.assertEqual(self.build["oneClickContinuationHistory"][0]["previousRun"], before["oneClickRun"])
        self.assertNotEqual(response["runId"], before["oneClickRun"]["runId"])
        self.assertFalse(response["eaFactoryReadResult"]["readinessConfirmed"])
        self.assertNotIn("oneClickRun", response)
        self.dispatch.assert_not_called()
        self.bridge._ea_factory_revalidated_continuation_history(self.build)

    def test_running_exact_mission_is_adopted(self):
        self.queued("running")
        self.assertEqual(self.submit()["adoptedMissionId"], "mission-existing-source")

    def test_http_route_returns_sanitized_exact_committed_receipt(self):
        self.queued()
        projection = self.patch("ea_factory_read_model", side_effect=AssertionError("No expensive authority projection in receipt"))
        handler = object.__new__(self.bridge.BridgeHandler)
        handler.path = f"/api/props/right_server_racks/ea-factory/builds/{self.build['id']}/resume-cancelled"
        handler.validate_local_request = mock.Mock()
        handler.validate_full_agent_mutation_request = mock.Mock()
        handler.read_payload = mock.Mock(return_value=copy.deepcopy(self.request))
        handler.send_preencoded_json = mock.Mock()
        handler.do_POST()
        call = handler.send_preencoded_json.call_args
        self.assertEqual(call.kwargs.get("status", 200), 200)
        body = json.loads(call.args[0])
        self.assertEqual(body["previousRunId"], self.request["previousRunId"])
        self.assertEqual(body["previousRunDigest"], self.request["previousRunDigest"])
        self.assertEqual(body["requestIdempotencyKey"], self.request["idempotencyKey"])
        self.assertEqual(body["runId"], self.build["oneClickRun"]["runId"])
        self.assertEqual(body["continuationArchiveDigest"], self.build["oneClickContinuationHistory"][0]["archiveDigest"])
        self.assertEqual(body["adoptedMissionId"], self.stage["missionId"])
        self.assertFalse(body["eaFactoryReadResult"]["readinessConfirmed"])
        self.assertNotIn("eaFactory", body)
        self.assertNotIn("oneClickRun", body)
        projection.assert_not_called()

    def test_duplicate_request_has_one_successor_and_archive_and_no_work_redispatch(self):
        self.queued()
        first = self.submit()
        worker = mock.Mock()
        worker.is_alive.return_value = True
        self.bridge.EA_FACTORY_ONE_CLICK_THREADS[self.build["id"]] = worker
        replay = self.submit()
        self.assertEqual(first["runId"], replay["runId"])
        self.assertTrue(replay["idempotentReplay"])
        self.assertEqual(len(self.build["oneClickContinuationHistory"]), 1)
        self.start.assert_called_once()
        self.dispatch.assert_not_called()

    def test_thread_start_failure_is_recoverable_with_same_key_and_no_new_archive(self):
        self.queued()
        self.start.side_effect = [RuntimeError("thread unavailable"), True]
        first = self.submit()
        self.assertFalse(first["workerStarted"])
        replay = self.submit()
        self.assertTrue(replay["workerStarted"])
        self.assertEqual(first["runId"], replay["runId"])
        self.assertEqual(len(self.commits), 1)
        self.assertEqual(self.stage["manualRetryCount"], 3)

    def test_two_simultaneous_same_key_requests_commit_and_start_only_once(self):
        self.queued()
        rendezvous = threading.Barrier(3)
        results, errors = [], []
        def register(build_id, **kwargs):
            self.bridge.EA_FACTORY_ONE_CLICK_THREADS[build_id] = mock.Mock(is_alive=lambda: True)
            return True
        self.start.side_effect = register
        def submit():
            try:
                rendezvous.wait(timeout=5)
                results.append(self.submit())
            except BaseException as error:
                errors.append(error)
        workers = [threading.Thread(target=submit) for _ in range(2)]
        for worker in workers:
            worker.start()
        rendezvous.wait(timeout=5)
        for worker in workers:
            worker.join(timeout=10)
        self.assertFalse(any(worker.is_alive() for worker in workers))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["runId"], results[1]["runId"])
        self.assertEqual(sorted(row["idempotentReplay"] for row in results), [False, True])
        self.assertEqual(len(self.commits), 1)
        self.assertEqual(len(self.build["oneClickContinuationHistory"]), 1)
        self.start.assert_called_once()
        self.dispatch.assert_not_called()

    def test_stale_identity_and_changed_idempotency_reject_without_commit(self):
        for field, value in (("previousRunId", "ea-run-foreign"), ("previousRunDigest", "f" * 64)):
            with self.subTest(field=field), self.assertRaises(self.bridge.RequestError):
                self.submit({**self.request, field: value})
        self.write.assert_not_called()
        self.sync.assert_not_called()
        self.submit()
        with self.assertRaises(self.bridge.RequestError):
            self.submit({**self.request, "idempotencyKey": "different-resume-key"})

    def test_header_terminal_and_stale_stop_context_block_before_ingestion(self):
        cases = ("header", "terminal", "stop_context", "coordinator")
        for case in cases:
            with self.subTest(case=case):
                with ExitStack() as stack:
                    if case == "header":
                        stack.enter_context(mock.patch.object(self.bridge, "_ea_factory_require_top_header_locks", side_effect=self.bridge.RequestError("locked", 409)))
                    elif case == "terminal":
                        stack.enter_context(mock.patch.object(self.bridge, "_ea_factory_one_click_terminal_binding_current", return_value=False))
                    elif case == "stop_context":
                        stack.enter_context(mock.patch.object(self.bridge, "EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS", {self.build["id"]: {"pending": True}}))
                    else:
                        worker = mock.Mock(); worker.is_alive.return_value = True
                        stack.enter_context(mock.patch.object(self.bridge, "EA_FACTORY_ONE_CLICK_THREADS", {"ea-build-other": worker}))
                    with self.assertRaises(self.bridge.RequestError):
                        self.submit()
        self.sync.assert_not_called()
        self.write.assert_not_called()

    def test_foreign_mission_identity_inputs_or_sandbox_rejects(self):
        original = self.queued()
        for field, value in (("idempotencyKey", "foreign-key"), ("owner", "ceo"), ("targetId", "other")):
            previous = original[field]; original[field] = value
            with self.subTest(field=field), self.assertRaises(self.bridge.RequestError):
                self.submit()
            original[field] = previous
        original["workflowContext"]["inputs"]["brief"] = "different strategy"
        with self.assertRaises(self.bridge.RequestError):
            self.submit()
        self.write.assert_not_called()

    def test_old_cancel_and_old_finalizer_cannot_touch_successor(self):
        old = copy.deepcopy(self.build["oneClickRun"])
        response = self.submit()
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.cancel_ea_factory_build_one_click(self.build["id"], {"runId": old["runId"], "idempotencyKey": old["idempotencyKey"]})
        self.assertFalse(self.bridge._ea_factory_finalize_one_click_cancel_after_worker(self.build["id"], old["runId"], coordinator_returned=True, owned_process_stop_confirmed=True))
        self.assertEqual(self.build["oneClickRun"]["runId"], response["runId"])

    def test_never_started_stopped_source_reserves_one_bounded_replacement(self):
        mission = self.stopped()
        original_mission = copy.deepcopy(mission)
        response = self.submit()
        self.assertIsNone(response["adoptedMissionId"])
        self.assertEqual(mission, original_mission)
        self.assertEqual(self.stage["status"], "pending")
        self.assertIsNone(self.stage["missionId"])
        self.assertEqual(self.stage["manualRetryCount"], 2)
        self.assertEqual(self.stage["manualRetryHistory"][-1]["failedMissionId"], mission["id"])
        self.assertTrue(self.bridge._ea_factory_cancelled_retry_history_valid(self.build, self.stage["manualRetryHistory"][-1]))
        self.assertNotIn("ea_factory_cancelled_by_operator", self.bridge.EA_FACTORY_RETRYABLE_SOURCE_ERROR_CODES)
        self.dispatch.assert_not_called()
        self.bridge._ea_factory_revalidated_continuation_history(self.build)

    def test_missing_stop_proof_existing_source_or_retry_limit_never_replaces(self):
        mission = self.stopped()
        for case in ("unknown_process", "source", "limit", "registered_process"):
            with self.subTest(case=case), ExitStack() as stack:
                if case == "unknown_process":
                    stack.enter_context(mock.patch.dict(mission["execution"], {"processStarted": None}))
                elif case == "source":
                    stack.enter_context(mock.patch.object(self.bridge, "_ea_factory_source_program_exists", return_value=True))
                elif case == "limit":
                    stack.enter_context(mock.patch.dict(self.stage, {"manualRetryCount": 3}))
                else:
                    stack.enter_context(mock.patch.object(self.bridge, "MISSION_WORKER_PROCESSES", {mission["id"]: {}}))
                with self.assertRaises(self.bridge.RequestError):
                    self.submit()
        self.write.assert_not_called()
        self.assertEqual(self.stage["manualRetryCount"], 1)

    def test_archive_digest_identity_and_terminal_tampering_reject(self):
        self.submit()
        saved = copy.deepcopy(self.build)
        for field, value in (("startedAt", "invalid"), ("currentStageId", "foreign_stage")):
            entry = self.build["oneClickContinuationHistory"][0]
            entry["previousRun"][field] = value
            entry["previousRunDigest"] = self.bridge._ea_factory_cancelled_run_digest(entry["previousRun"])
            entry["archiveDigest"] = self.bridge._ea_factory_continuation_archive_digest(entry)
            with self.subTest(field=field), self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge._ea_factory_revalidated_continuation_history(self.build)
            self.build.clear(); self.build.update(copy.deepcopy(saved))

    def test_started_source_requires_exact_durable_stop_audits(self):
        mission = self.stopped(started=True)
        common = {"time": "2026-10-18T01:02:01Z", "buildId": self.build["id"],
                  "runId": self.request["previousRunId"], "stageId": "generate_source"}
        stopped = {**common, "type": "ea_factory.one_click_cancelled", "missionId": mission["id"],
                   "missionCancellationPersisted": True, "missionProcessFound": True,
                   "missionProcessTerminated": True, "missionProcessStopConfirmed": True}
        final = {**common, "type": "ea_factory.one_click_cancel_finalized", "ownedProcessStopConfirmed": True}
        audits = self.patch("tail_jsonl", return_value=[stopped, final])
        for field, wrong in (("missionId", "mission-other"), ("stageId", "compile_validate"),
                             ("missionProcessTerminated", False), ("missionCancellationPersisted", False),
                             ("time", "2026-10-18T01:00:00Z")):
            with self.subTest(field=field), mock.patch.dict(stopped, {field: wrong}), self.assertRaises(self.bridge.RequestError):
                self.submit()
        self.write.assert_not_called()
        response = self.submit()
        self.assertIsNone(response["adoptedMissionId"])
        self.assertEqual(self.stage["manualRetryCount"], 2)
        self.assertEqual(self.build["oneClickContinuationHistory"][0]["replacement"]["stopProof"]["kind"], "terminated_owned_process")
        self.assertTrue(audits.call_args.kwargs["include_archives"])
        self.bridge._ea_factory_revalidated_continuation_history(self.build)

    def test_resealed_stop_proof_and_lost_retry_reservation_fail_history_validation(self):
        mission = self.stopped()
        self.submit()
        saved = copy.deepcopy(self.build)
        entry = self.build["oneClickContinuationHistory"][0]
        entry["replacement"]["stopProof"]["completedAt"] = "2026-10-18T01:02:03Z"
        entry["archiveDigest"] = self.bridge._ea_factory_continuation_archive_digest(entry)
        self.build["oneClickRun"]["continuationArchiveDigest"] = entry["archiveDigest"]
        self.stage["manualRetryHistory"][-1]["continuationArchiveDigest"] = entry["archiveDigest"]
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_revalidated_continuation_history(self.build)
        self.build.clear(); self.build.update(saved)
        current = self.bridge._ea_factory_stage_row(self.build, "generate_source")
        current["manualRetryHistory"].pop(); current["manualRetryCount"] -= 1
        with self.assertRaises(self.bridge.DataIntegrityError):
            self.bridge._ea_factory_revalidated_continuation_history(self.build)

    def test_boolean_attempt_and_visible_stage_mutation_reject_before_commit(self):
        mission = self.stopped()
        mission["attemptCount"] = False
        with self.assertRaises(self.bridge.RequestError):
            self.submit()
        mission["attemptCount"] = 0
        self.sync.reset_mock()
        self.bridge._ea_factory_stage_row(self.build, "compile_validate")["requestIdempotencyKey"] = "uncertain-compile"
        with self.assertRaises(self.bridge.RequestError):
            self.submit()
        self.sync.assert_not_called()
        self.write.assert_not_called()

    def test_backtest_restart_after_continuation_is_rejected_before_mutation(self):
        self.submit()
        before = copy.deepcopy(self.state)
        self.assertFalse(self.bridge._ea_factory_backtest_stage_restartable(self.build))
        self.write.reset_mock()
        with self.assertRaises(self.bridge.RequestError) as caught:
            self.bridge.restart_ea_factory_build_backtest_only(self.build["id"], {
                "runId": self.build["oneClickRun"]["runId"], "idempotencyKey": "new-backtest-key"})
        self.assertEqual(caught.exception.code, "backtest_restart_continuation_history_unsupported")
        self.assertEqual(self.state, before)
        self.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
