"""Adversarial worker persistence/transport checks; no native runner is started."""
import json
import unittest
from contextlib import ExitStack
from unittest import mock

import test_council_worker_lease_budget as fixtures
import test_manager_parallel_missions as manager_fixtures


class CouncilWorkerNegativePathTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.CouncilWorkerLeaseBudgetTests()
        self.f.setUp()
        self.b = self.f.b
        self.base = self.f.f

    def tearDown(self):
        self.f.tearDown()

    def test_transient_completion_store_failure_preserves_actual_spawn_receipt(self):
        original_save = self.b.save_missions
        failed_once = False

        def fail_completed_write_once(rows):
            nonlocal failed_once
            if not failed_once and any(row.get("id") == self.base.child["id"]
                                       and row.get("status") == "completed" for row in rows):
                failed_once = True
                raise PermissionError("synthetic transient finalization replacement failure")
            return original_save(rows)

        def inert_runner(_command, **_kwargs):
            # Model the durable receipt written by the real guarded Popen path.
            current = self.base.stored()
            current["execution"].update(processStarted=True, processStartedAt=self.b.utc_now())
            self.b.replace_mission(current)
            return {"ok": True, "processStarted": True, "exitCode": 0,
                    "output": json.dumps(self.base.successful_result(current))}

        self.base.runner.side_effect = inert_runner
        with mock.patch.object(self.b, "save_missions", side_effect=fail_completed_write_once):
            self.b.process_auto_mission("finalization-failure", self.base.child)
        self.assertTrue(failed_once)
        stored = self.base.stored()
        self.assertEqual(stored["status"], "failed")
        self.assertEqual(stored["errorCode"], "internal_worker_error")
        self.assertTrue(stored["execution"]["processStarted"], "A known spawn must not be rewritten as never started")
        self.assertTrue(stored["execution"]["processStartedAt"])
        self.assertIsNone(self.b.claim_auto_mission(stored["id"], "must-not-retry"))
        self.base.dispatch.assert_not_called()

    def test_permission_failure_after_spawn_preserves_receipt_and_stops_exact_process(self):
        claimed, lease = self.f.claim()
        self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        process, patches = self.f.fake_process_patches()
        process.poll.return_value = None
        process.communicate.side_effect = PermissionError("synthetic pipe read failure")
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            kill = stack.enter_context(mock.patch.object(self.b, "_terminate_command_process_tree", return_value=True))
            result = self.f.run_fake_process(claimed["id"], lease)
        self.assertTrue(self.base.stored()["execution"]["processStarted"])
        self.assertTrue(result["processStarted"], "Transport errors after Popen are not prelaunch failures")
        self.assertTrue(result["processTreeTerminated"])
        kill.assert_called_once_with(process, {"fake": True})
        self.base.runner.assert_not_called()
        self.base.dispatch.assert_not_called()

    def test_general_transport_distinguishes_both_prelaunch_errors_from_postspawn_errors(self):
        for error_type, code in ((PermissionError, "permission_denied"), (FileNotFoundError, "not_found")):
            for after_spawn in (False, True):
                with self.subTest(error=error_type.__name__, after_spawn=after_spawn):
                    process, patches = self.f.fake_process_patches()
                    process.poll.return_value = None
                    with ExitStack() as stack:
                        popen = stack.enter_context(patches[0])
                        for patch in patches[1:]:
                            stack.enter_context(patch)
                        if after_spawn:
                            process.communicate.side_effect = error_type("synthetic postspawn transport failure")
                        else:
                            popen.side_effect = error_type("synthetic executable failure")
                        kill = stack.enter_context(mock.patch.object(self.b, "_terminate_command_process_tree", return_value=True))
                        result = self.b._run_safe_command_with_tree_timeout(
                            ["never-launch"], 90, 1000, None, structured_json_output=True)
                    self.assertEqual(result["exitCode"], code)
                    self.assertEqual(result["processStarted"], after_spawn)
                    self.assertEqual(result["processTreeTerminated"], after_spawn)
                    if after_spawn:
                        kill.assert_called_once_with(process, {"fake": True})
                    else:
                        kill.assert_not_called()

    def test_failed_postspawn_cleanup_is_not_reported_as_terminated(self):
        process, patches = self.f.fake_process_patches()
        process.poll.return_value = None
        process.communicate.side_effect = PermissionError("synthetic pipe failure")
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            kill = stack.enter_context(mock.patch.object(self.b, "_terminate_command_process_tree", return_value=False))
            result = self.b._run_safe_command_with_tree_timeout(
                ["never-launch"], 90, 1000, None, structured_json_output=True)
        self.assertTrue(result["processStarted"])
        self.assertFalse(result["processTreeTerminated"])
        kill.assert_called_once_with(process, {"fake": True})

    def test_permanent_completion_store_failure_releases_capacity_without_retry_or_success(self):
        original_save = self.b.save_missions

        def fail_terminal_writes(rows):
            if any(row.get("id") == self.base.child["id"]
                   and row.get("status") in {"completed", "failed"} for row in rows):
                raise PermissionError("synthetic persistent finalization failure")
            return original_save(rows)

        def inert_runner(_command, **_kwargs):
            current = self.base.stored()
            current["execution"].update(processStarted=True, processStartedAt=self.b.utc_now())
            self.b.replace_mission(current)
            return {"ok": True, "processStarted": True, "exitCode": 0,
                    "output": json.dumps(self.base.successful_result(current))}

        self.base.runner.side_effect = inert_runner
        with mock.patch.object(self.b, "save_missions", side_effect=fail_terminal_writes):
            with self.assertRaises(PermissionError):
                self.b.process_auto_mission("persistent-finalization-failure", self.base.child)
        stored = self.base.stored()
        self.assertEqual(stored["status"], "running")
        self.assertTrue(stored["execution"]["processStarted"])
        self.assertEqual(stored["attemptCount"], 1)
        self.assertNotIn("councilVote", stored)
        self.assertIsNone(self.b.claim_auto_mission(stored["id"], "must-not-retry"))
        acquired = []
        try:
            acquired = [self.b.AI_TRADE_COUNCIL_RUN_SEMAPHORE.acquire(blocking=False) for _ in range(3)]
            self.assertEqual(acquired, [True, True, True])
        finally:
            for held in acquired:
                if held:
                    self.b.AI_TRADE_COUNCIL_RUN_SEMAPHORE.release()
        self.base.runner.assert_called_once()
        self.base.dispatch.assert_not_called()

    def test_late_exception_cannot_finish_replacement_lease(self):
        # Manual Council runs retain their original worker path. Simulate a
        # newer durable lease appearing while the old transport is unwinding.
        self.base.child["analysisContext"].pop("automation")
        self.base.save_child()
        replacement = []

        def late_failure(_command, **_kwargs):
            current = self.base.stored()
            current["execution"].update(leaseId="lease-replacement", workerId="new-worker")
            self.b.replace_mission(current)
            replacement.append(self.base.stored())
            raise RuntimeError("old worker transport exception after lease replacement")

        self.base.runner.side_effect = late_failure
        self.b.process_auto_mission("old-worker", self.base.child)
        self.base.runner.assert_called_once()
        self.assertEqual(self.base.stored(), replacement[0])
        self.base.dispatch.assert_not_called()

    def test_claim_exception_cannot_finish_another_worker(self):
        winner = self.b.claim_auto_mission(self.base.child["id"], "winner-worker")
        self.assertIsNotNone(winner)
        before = self.base.stored()
        with mock.patch.object(self.b, "claim_auto_mission", side_effect=PermissionError("synthetic claim read failure")):
            self.b.process_auto_mission("losing-worker", self.base.child)
        self.assertEqual(self.base.stored(), before)
        self.base.runner.assert_not_called()
        self.base.dispatch.assert_not_called()

    def test_claim_receipt_exception_remains_bounded_without_launch_or_local_run_debit(self):
        original_audit = self.b.append_audit

        def fail_claim_audit(event):
            if event.get("type") == "mission.auto_claimed":
                raise PermissionError("synthetic claim audit write failure")
            return original_audit(event)

        with (mock.patch.object(self.b, "append_audit", side_effect=fail_claim_audit),
              mock.patch.object(self.b, "check_rate_limit", return_value=(True, 0)) as rate):
            self.b.process_auto_mission("claim-receipt-failure", self.base.child)
        stored = self.base.stored()
        self.assertEqual(stored["status"], "running")
        self.assertEqual(stored["execution"]["leasePhase"], "preparing")
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertTrue(all(call.kwargs.get("consume") is False for call in rate.call_args_list))
        self.f.advance(205)
        self.assertEqual(self.b.reconcile_timed_out_running_missions(), 1)
        self.assertEqual(self.base.stored()["status"], "failed")
        self.assertIsNone(self.b.claim_auto_mission(stored["id"], "must-not-retry"))
        self.base.runner.assert_not_called()
        self.base.dispatch.assert_not_called()


class ManagerWorkerNegativePathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manager_fixtures.ManagerParallelMissionTests.setUpClass()

    def setUp(self):
        self.f = manager_fixtures.ManagerParallelMissionTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.b = self.f.bridge

    def test_manager_late_exception_cannot_finish_replacement_lease(self):
        child = self.f.delegate(("risk_guard",))["subtasks"][0]
        replacement = []

        def late_failure(_command, **_kwargs):
            current = self.b.find_mission(child["id"])
            current["execution"].update(leaseId="lease-manager-replacement", workerId="new-manager-worker")
            self.b.replace_mission(current)
            replacement.append(self.b.find_mission(child["id"]))
            raise RuntimeError("old Manager worker transport exception")

        with mock.patch.object(self.b, "run_safe_command", side_effect=late_failure) as runner:
            self.f.process(child, "old-manager-worker")
        runner.assert_called_once()
        self.assertEqual(self.b.find_mission(child["id"]), replacement[0])
        self.f.assert_general_lease_available()


if __name__ == "__main__":
    unittest.main()
