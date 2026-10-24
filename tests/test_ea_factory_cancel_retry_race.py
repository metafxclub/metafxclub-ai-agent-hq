"""Deterministic cancellation boundaries; no Runtime or native process access."""
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import test_ea_factory_cancelled_resume_backend as support


class FactoryCancelRetryRaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = support.support.load_bridge()

    def setUp(self):
        self.fx = support.EaFactoryCancelledResumeTests()
        self.fx.bridge = self.bridge
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.build, self.stage, self.state = self.fx.build, self.fx.stage, self.fx.state
        self.run = self.build["oneClickRun"]
        self.patch = self.fx.patch
        self.save = self.patch("save_missions")
        self.process = self.patch("_ea_factory_terminate_owned_mission_process", return_value={
            "missionProcessFound": False, "missionProcessTerminated": None})
        self.patch("EA_FACTORY_ONE_CLICK_CANCEL_EVENTS", {})

    def cancel(self):
        return self.bridge.cancel_ea_factory_build_one_click(self.build["id"], {
            "runId": self.run["runId"], "idempotencyKey": self.run["idempotencyKey"]})

    def failed(self):
        mission = self.fx.queued()
        mission.update(status="failed", errorCode="invalid_output")
        self.stage.update(status="failed", blockedReasonCode="invalid_output", manualRetryCount=0, manualRetryHistory=[])
        self.build["coverageStatus"] = "compact_current"
        self.run["status"] = "waiting_ai"
        return {"stageId": "generate_source", "failedMissionId": mission["id"], "idempotencyKey": "same-retry-intent"}

    def test_cancel_wins_before_retry_reservation_without_history_or_dispatch(self):
        payload = self.failed()
        self.run["status"] = "cancelling"
        before = copy.deepcopy(self.build)
        with self.assertRaises(self.bridge.RequestError):
            self.bridge.retry_ea_factory_build_stage(self.build["id"], payload, expected_run_id=self.run["runId"])
        self.assertEqual(self.build, before)
        self.fx.write.assert_not_called()
        self.fx.dispatch.assert_not_called()

    def test_cancel_between_retry_reservation_and_advance_preserves_reserved_retry(self):
        payload = self.failed()
        reserved, release = threading.Event(), threading.Event()
        advance = self.bridge.advance_ea_factory_build
        errors = []

        def pause(*args, **kwargs):
            reserved.set()
            self.assertTrue(release.wait(5))
            return advance(*args, **kwargs)

        def retry():
            try:
                self.bridge.retry_ea_factory_build_stage(self.build["id"], payload, expected_run_id=self.run["runId"])
            except BaseException as error:
                errors.append(error)

        with mock.patch.object(self.bridge, "advance_ea_factory_build", side_effect=pause):
            worker = threading.Thread(target=retry)
            worker.start()
            try:
                self.assertTrue(reserved.wait(5))
                self.assertEqual(self.stage["manualRetryCount"], 1)
                history = copy.deepcopy(self.stage["manualRetryHistory"])
                self.cancel()
            finally:
                release.set()
                worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], self.bridge.RequestError)
        self.assertEqual(self.run["status"], "cancelled")
        self.assertEqual(self.stage["manualRetryCount"], 1)
        self.assertEqual(self.stage["manualRetryHistory"], history)
        self.assertIsNone(self.stage["missionId"])
        self.fx.dispatch.assert_not_called()

    def test_stale_coordinator_cannot_dispatch_into_successor_run(self):
        payload = self.failed()
        old_id = self.run["runId"]
        self.run["runId"] = "ea-run-successor"
        before = copy.deepcopy(self.build)
        for method, request in [(self.bridge.retry_ea_factory_build_stage, payload),
                                (self.bridge.advance_ea_factory_build, {"stageId": "generate_source", "idempotencyKey": "old-advance"})]:
            with self.assertRaises(self.bridge.RequestError):
                method(self.build["id"], request, expected_run_id=old_id)
        self.assertEqual(self.build, before)
        self.fx.dispatch.assert_not_called()

    def test_cancelled_replay_drains_exact_queued_orphan_once_preserving_run_and_history(self):
        orphan = self.fx.queued()
        unrelated = copy.deepcopy(orphan)
        unrelated.update(id="mission-unrelated", idempotencyKey="other-request")
        self.fx.missions.append(unrelated)
        before_run, before_stage = copy.deepcopy(self.run), copy.deepcopy(self.stage)
        first = self.cancel()
        self.assertFalse(first["cancelPending"])
        self.assertEqual(orphan["status"], "blocked")
        self.assertEqual(orphan["errorCode"], "ea_factory_cancelled_by_operator")
        self.assertFalse(orphan["execution"]["automaticRetry"])
        self.assertEqual(orphan["attemptCount"], 0)
        self.assertEqual(unrelated["status"], "queued")
        after_missions = copy.deepcopy(self.fx.missions)
        second = self.cancel()
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(self.fx.missions, after_missions)
        self.assertEqual(self.run, before_run)
        self.assertEqual(self.stage, before_stage)
        self.fx.write.assert_not_called()
        self.process.assert_called_once_with(orphan["id"])
        self.save.assert_called_once()

    def test_finalizer_rechecks_late_mission_instead_of_stale_stop_confirmation(self):
        orphan = self.fx.queued()
        self.run["status"] = "cancelling"
        result = self.bridge._ea_factory_finalize_one_click_cancel_after_worker(
            self.build["id"], self.run["runId"], coordinator_returned=True, owned_process_stop_confirmed=True)
        self.assertTrue(result)
        self.assertEqual(orphan["status"], "blocked")
        self.assertEqual(self.run["status"], "cancelled")
        self.assertEqual(orphan["attemptCount"], 0)

    def test_untracked_running_orphan_does_not_claim_confirmed_stop(self):
        orphan = self.fx.queued("running")
        orphan.update(attemptCount=1, startedAt="2026-10-19T01:00:00Z")
        orphan["execution"]["processStarted"] = True
        self.run["status"] = "cancelling"
        self.assertFalse(self.bridge._ea_factory_finalize_one_click_cancel_after_worker(
            self.build["id"], self.run["runId"], coordinator_returned=True, owned_process_stop_confirmed=True))
        self.assertEqual(self.run["status"], "cancelling")
        self.assertFalse(self.bridge._ea_factory_finalize_one_click_cancel_after_worker(
            self.build["id"], self.run["runId"], coordinator_returned=True, owned_process_stop_confirmed=True))

    def test_cancelled_replay_reports_pending_if_legacy_running_process_unconfirmed(self):
        orphan = self.fx.queued("running")
        orphan.update(attemptCount=1, startedAt="2026-10-19T01:00:00Z")
        orphan["execution"]["processStarted"] = True
        before = copy.deepcopy(self.run)
        self.assertTrue(self.cancel()["cancelPending"])
        self.assertEqual(self.run, before)

    def test_requeued_previously_claimed_mission_is_not_never_started_stop_evidence(self):
        orphan = self.fx.queued()
        orphan.update(attemptCount=1, startedAt="2026-10-19T01:00:00Z")
        self.assertTrue(self.cancel()["cancelPending"])
        self.assertFalse(orphan["execution"].get("processTreeTerminated", False))

    def test_stale_cancel_cannot_signal_or_replace_successor_coordinator(self):
        self.run["status"] = "waiting_ai"
        successor_event = threading.Event()
        successor_context = {"runId": "ea-run-successor", "ownedProcessStopConfirmed": False}
        reads = 0

        def state():
            nonlocal reads
            reads += 1
            if reads == 2:
                # Another cancellation finished, then explicit resume adopted a successor
                # while this request was between the intent commit and event lookup.
                self.build["oneClickRun"] = {**self.run, "runId": "ea-run-successor", "status": "queued"}
                self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_EVENTS[self.build["id"]] = successor_event
                self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS[self.build["id"]] = successor_context
            return self.state

        self.patch("_load_ea_factory_state_unlocked", side_effect=state)
        with self.assertRaises(self.bridge.RequestError):
            self.cancel()
        self.assertFalse(successor_event.is_set())
        self.assertIs(self.bridge.EA_FACTORY_ONE_CLICK_CANCEL_CONTEXTS[self.build["id"]], successor_context)
        self.save.assert_not_called()

    def test_factory_process_start_rechecks_current_lease_and_cancellation(self):
        mission = self.fx.queued("running")
        mission["execution"]["leaseId"] = "lease-current"
        self.patch("find_mission", return_value=mission)
        with mock.patch.object(self.bridge.subprocess, "Popen") as spawn:
            for lease, status in [("lease-old", "running"), ("lease-current", "blocked")]:
                mission["status"] = status
                result = self.bridge._run_safe_command_with_tree_timeout(
                    ["never-spawn"], 1, 1000, None, tracking_key=mission["id"], factory_start_lease=lease)
                self.assertFalse(result["processStarted"])
            mission["status"] = "running"
            self.patch("_ea_factory_mission_dispatch_denied", return_value=True)
            result = self.bridge._run_safe_command_with_tree_timeout(
                ["never-spawn"], 1, 1000, None, tracking_key=mission["id"], factory_start_lease="lease-current")
            self.assertFalse(result["processStarted"])
            spawn.assert_not_called()

    def test_process_winning_launch_race_is_registered_before_cancel_can_drain(self):
        mission = self.fx.queued("running")
        mission.update(attemptCount=1, startedAt="2026-10-19T01:00:00Z")
        mission["execution"]["leaseId"] = "lease-current"
        self.run["status"] = "waiting_ai"
        entered, release, stopped, intent = (threading.Event() for _ in range(4))
        results, errors = [], []
        self.patch("find_mission", return_value=mission)
        self.patch("_ea_factory_mission_dispatch_denied", return_value=False)
        self.patch("_create_windows_kill_job", return_value={"test": True})
        self.patch("_close_windows_kill_job")
        self.patch("MISSION_WORKER_STOP", threading.Event())
        self.fx.write.side_effect = lambda value: intent.set() if self.run["status"] == "cancelling" else None

        class Process:
            pid = 1234
            returncode = 0
            def __init__(self, *args, **kwargs):
                entered.set()
                if not release.wait(5):
                    raise AssertionError("release launch")
            def poll(self):
                return 0 if stopped.is_set() else None
            def communicate(self, **kwargs):
                if not stopped.wait(5):
                    raise AssertionError("cancel exact process")
                return "done", ""

        def terminate(mission_id):
            self.assertEqual(mission_id, mission["id"])
            self.assertIsInstance(self.bridge.MISSION_WORKER_PROCESSES[mission_id]["process"], Process)
            stopped.set()
            return {"missionProcessFound": True, "missionProcessTerminated": True}

        self.process.side_effect = terminate
        self.patch("_resume_windows_process", side_effect=lambda process: self.bridge.MISSION_WORKER_PROCESSES[mission["id"]]["process"] is process)

        def launch():
            try:
                results.append(self.bridge._run_safe_command_with_tree_timeout(
                    ["fake-only"], 1, 1000, None, cancel_event=self.bridge.MISSION_WORKER_STOP,
                    tracking_key=mission["id"], factory_start_lease="lease-current"))
            except BaseException as error:
                errors.append(error)

        def cancel():
            try:
                results.append(self.cancel())
            except BaseException as error:
                errors.append(error)

        with mock.patch.object(self.bridge.subprocess, "Popen", Process):
            worker = threading.Thread(target=launch)
            worker.start()
            self.assertTrue(entered.wait(5))
            cancellation = threading.Thread(target=cancel)
            cancellation.start()
            try:
                self.assertTrue(intent.wait(5))
            finally:
                release.set()
                worker.join(7)
                cancellation.join(7)
        self.assertFalse(worker.is_alive())
        self.assertFalse(cancellation.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(self.run["status"], "cancelled")
        self.assertTrue(mission["execution"]["processTreeTerminated"])
        self.assertTrue(mission["execution"]["processStarted"])
        self.assertEqual(mission["attemptCount"], 1)

    def test_cancelled_mission_late_result_cannot_restore_running_or_append_report(self):
        mission = self.fx.queued()
        self.cancel()
        before = copy.deepcopy(mission)
        self.patch("find_mission", return_value=mission)
        self.assertIsNone(self.bridge.finish_auto_mission(mission["id"], "obsolete-lease",
            {"processStarted": True}, {"ok": True, "status": "completed"}))
        self.assertEqual(mission, before)

    def test_dispatch_preclaim_denies_cancelled_store_without_mutating_receipt(self):
        mission = self.fx.queued()
        before = copy.deepcopy(mission)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "factory.json"
            path.write_text(json.dumps(self.state), encoding="utf-8")
            with mock.patch.object(self.bridge, "_ea_factory_state_path", return_value=path):
                self.assertTrue(self.bridge._ea_factory_mission_dispatch_denied(mission))
                self.assertIsNone(self.bridge._claim_auto_mission_unlocked(mission["id"], "test-worker"))
        self.assertEqual(mission, before)
        self.save.assert_not_called()

    def test_preclaim_allows_adopted_successor_but_keeps_normal_authorization(self):
        mission = self.fx.queued()
        self.run.update(runId="ea-run-successor", status="waiting_ai")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "factory.json"
            path.write_text(json.dumps(self.state), encoding="utf-8")
            with (mock.patch.object(self.bridge, "_ea_factory_state_path", return_value=path),
                  mock.patch.object(self.bridge, "auto_execution_authorization_error", return_value="permission_denied") as auth,
                  mock.patch.object(self.bridge, "block_auto_mission") as blocked):
                self.assertFalse(self.bridge._ea_factory_mission_dispatch_denied(mission))
                self.assertIsNone(self.bridge._claim_auto_mission_unlocked(mission["id"], "test-worker"))
                auth.assert_called_once()
                blocked.assert_called_once_with(mission["id"], "permission_denied")
        self.assertEqual(mission["attemptCount"], 0)

    def test_preclaim_unreadable_missing_duplicate_or_mismatched_owner_fails_closed(self):
        mission = self.fx.queued()
        self.run["status"] = "waiting_ai"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "factory.json"
            with mock.patch.object(self.bridge, "_ea_factory_state_path", return_value=path):
                self.assertTrue(self.bridge._ea_factory_mission_dispatch_denied(mission))
                for data in ['{', '{"schemaVersion":"x","schemaVersion":"y"}', '{}']:
                    path.write_text(data, encoding="utf-8")
                    self.assertTrue(self.bridge._ea_factory_mission_dispatch_denied(mission))
                self.stage["missionId"] = "mission-other"
                path.write_text(json.dumps(self.state), encoding="utf-8")
                self.assertTrue(self.bridge._ea_factory_mission_dispatch_denied(mission))

    def test_preclaim_does_not_acquire_factory_lock_or_touch_nonfactory_mission(self):
        mission = self.fx.queued()
        self.patch("EA_FACTORY_LOCK", mock.Mock(side_effect=AssertionError("Lock inversion")))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "factory.json"
            path.write_text(json.dumps(self.state), encoding="utf-8")
            with mock.patch.object(self.bridge, "_ea_factory_state_path", return_value=path):
                self.assertTrue(self.bridge._ea_factory_mission_dispatch_denied(mission))
            with mock.patch.object(self.bridge, "_trusted_backend_ea_factory_worker_sandbox", return_value=None):
                self.assertFalse(self.bridge._ea_factory_mission_dispatch_denied({"id": "ordinary"}))


if __name__ == "__main__":
    unittest.main()
