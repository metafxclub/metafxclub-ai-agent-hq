"""Automatic Council lease clocks; all stores and runners are temporary/fake."""
from __future__ import annotations

import copy
import json
import threading
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import test_council_newbar_worker as fixtures


class CouncilWorkerLeaseBudgetTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.CouncilNewBarWorkerTests()
        self.f.setUp()
        self.b = self.f.b
        self.start = datetime.now(timezone.utc)

        class Clock(datetime):
            instant = self.start

            @classmethod
            def now(cls, tz=None):
                return cls.instant.astimezone(tz) if tz else cls.instant.replace(tzinfo=None)

        self.clock = Clock
        self.f.stack.enter_context(mock.patch.object(self.b, "datetime", Clock))
        context = self.f.child["analysisContext"]
        context.update(roundStartedAt=self.start.isoformat(),
                       roundDeadlineAt=(self.start + timedelta(seconds=300)).isoformat())
        context["automation"].update(quotaAdmittedAt=self.start.isoformat(),
                                     triggerExpiresAt=context["roundDeadlineAt"])
        self.f.save_child()

    def tearDown(self):
        self.f.tearDown()

    def advance(self, seconds):
        self.clock.instant = self.start + timedelta(seconds=seconds)

    def claim(self):
        claimed = self.b.claim_auto_mission(self.f.child["id"], "lease-clock-test")
        self.assertIsNotNone(claimed)
        return claimed, claimed["execution"]["leaseId"]

    def test_slow_preparation_does_not_consume_role_execution_timeout(self):
        claimed, lease = self.claim()
        self.assertEqual(claimed["budget"]["timeoutSeconds"], 60)
        self.assertEqual(self.b.parse_iso(claimed["execution"]["timeoutAt"]),
                         self.start + timedelta(seconds=205))
        self.advance(110)  # Beyond the former 60s lease + 45s watchdog grace.
        self.assertEqual(self.b.reconcile_timed_out_running_missions(), 0)
        started = self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        self.assertEqual(self.b.parse_iso(started["execution"]["runnerStartedAt"]), self.clock.instant)
        self.assertEqual(self.b.parse_iso(started["execution"]["timeoutAt"]),
                         self.start + timedelta(seconds=200))
        self.assertLess(self.b.parse_iso(started["execution"]["timeoutAt"]),
                        self.b.parse_iso(started["analysisContext"]["roundDeadlineAt"]))
        self.f.runner.assert_not_called()
        self.f.dispatch.assert_not_called()

    def test_preparation_timeout_is_fixed_and_cannot_be_restarted(self):
        claimed, lease = self.claim()
        self.advance(205)
        self.assertIsNone(self.b._begin_council_runner_lease(claimed["id"], lease, 60))
        self.assertEqual(self.b.reconcile_timed_out_running_missions(), 1)
        stored = self.f.stored()
        self.assertEqual(stored["status"], "failed")
        self.assertFalse(stored["execution"]["processStarted"])
        self.assertFalse(stored["execution"]["automaticRetry"])
        self.assertIsNone(self.b.claim_auto_mission(claimed["id"], "retry"))
        self.f.runner.assert_not_called()

    def test_news_keeps_90_seconds_and_finishes_inside_shared_round(self):
        news = next(row for row in self.b.load_missions()
                    if (row.get("analysisContext") or {}).get("roleId") == "news")
        news["analysisContext"].update({
            key: copy.deepcopy(self.f.child["analysisContext"][key])
            for key in ("automation", "roundStartedAt", "roundDeadlineAt")
        })
        self.b._issue_backend_auto_safe_authorization(news)
        self.b.replace_mission(news)
        claimed = self.b.claim_auto_mission(news["id"], "news-clock-test")
        self.assertEqual(claimed["budget"]["timeoutSeconds"], 90)
        self.assertEqual(self.b.parse_iso(claimed["execution"]["preparationDeadlineAt"]),
                         self.start + timedelta(seconds=175))
        self.advance(174)
        started = self.b._begin_council_runner_lease(news["id"], claimed["execution"]["leaseId"], 90)
        self.assertEqual(self.b.parse_iso(started["execution"]["timeoutAt"]),
                         self.start + timedelta(seconds=294))
        self.assertEqual(self.b._auto_mission_watchdog_deadline(started, 45),
                         self.start + timedelta(seconds=294))

    def test_heartbeat_and_second_start_cannot_extend_execution_deadline(self):
        claimed, lease = self.claim()
        self.advance(110)
        started = self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        timeout_at = started["execution"]["timeoutAt"]
        self.advance(150)
        self.assertIsNone(self.b._begin_council_runner_lease(claimed["id"], lease, 60))
        stop = mock.Mock()
        stop.wait.side_effect = [False, True]
        self.b.heartbeat_auto_mission(claimed["id"], lease, stop, 1)
        self.assertEqual(self.f.stored()["execution"]["timeoutAt"], timeout_at)
        self.advance(200)
        self.assertEqual(self.b.reconcile_timed_out_running_missions(), 1)
        before = self.f.stored()
        result = self.b.finish_auto_mission(claimed["id"], lease,
                                           {"ok": True, "processStarted": True},
                                           self.f.successful_result(claimed))
        self.assertIsNone(result)
        self.assertEqual(self.f.stored(), before)
        self.f.dispatch.assert_not_called()

    def test_worker_serialization_delay_starts_execution_clock_at_runner_handoff(self):
        original = self.b._radar_worker_prompt
        # The terminal keeps publishing a fresh heartbeat of the same bar while
        # local preparation runs; no real terminal is queried by this fixture.
        current_snapshot = self.b.metatrader_snapshot_read_model(self.b.AI_TRADE_COUNCIL_PROP_ID)
        calls = 0

        def slow_preparation(mission):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.advance(110)
            return original(mission)

        def runner(_command, **kwargs):
            stored = self.f.stored()
            self.assertEqual(kwargs["council_start_lease"], stored["execution"]["leaseId"])
            self.assertEqual(self.b.parse_iso(stored["execution"]["runnerStartedAt"]), self.clock.instant)
            self.assertEqual(self.b.parse_iso(stored["execution"]["timeoutAt"]),
                             self.start + timedelta(seconds=200))
            return {"ok": True, "exitCode": 0, "processStarted": True,
                    "output": json.dumps(self.f.successful_result(stored))}

        self.f.runner.side_effect = runner
        with (mock.patch.object(self.b, "_radar_worker_prompt", side_effect=slow_preparation),
              mock.patch.object(self.b, "metatrader_snapshot_read_model", return_value=current_snapshot)):
            self.b.process_auto_mission("delayed-preparation", self.f.child)
        self.f.runner.assert_called_once()
        self.assertEqual(self.f.stored()["status"], "completed")

    def test_cancel_or_deadline_during_handoff_never_opens_process(self):
        claimed, lease = self.claim()
        started = self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        for mode in ("cancel", "expired"):
            with self.subTest(mode=mode):
                current = copy.deepcopy(started)
                if mode == "cancel":
                    current.update(status="blocked")
                    current["execution"]["dispatchState"] = "blocked"
                else:
                    self.advance(90)
                self.b.replace_mission(current)
                with mock.patch.object(self.b.subprocess, "Popen") as popen:
                    result = self.b._run_safe_command_with_tree_timeout(
                        ["never-launch"], 90, 1000, None,
                        tracking_key=claimed["id"], council_start_lease=lease,
                        structured_json_output=True)
                popen.assert_not_called()
                self.assertFalse(result["processStarted"])
                self.assertEqual(result["exitCode"], "cancelled")

    def test_stale_watchdog_scan_cannot_kill_transitioned_execution_lease(self):
        claimed, lease = self.claim()
        stale = self.b.load_missions()
        self.advance(200)
        self.assertIsNotNone(self.b._begin_council_runner_lease(claimed["id"], lease, 60))
        current = self.b.load_missions()
        self.advance(210)

        class FakeProcess:
            def poll(self):
                return None

        self.b.MISSION_WORKER_PROCESSES[claimed["id"]] = {
            "process": FakeProcess(), "jobHolder": {}, "leaseId": lease}
        with (mock.patch.object(self.b, "load_missions", side_effect=[stale, current]),
              mock.patch.object(self.b.subprocess, "Popen", FakeProcess),
              mock.patch.object(self.b, "_terminate_command_process_tree") as kill):
            self.assertEqual(self.b.reconcile_timed_out_running_missions(), 0)
        kill.assert_not_called()

    def run_fake_process(self, mission_id, lease):
        return self.b._run_safe_command_with_tree_timeout(
            ["never-launch-real-process"], 90, 1000, None,
            tracking_key=mission_id, council_start_lease=lease,
            structured_json_output=True)

    def fake_process_patches(self):
        process = mock.Mock(pid=7654321, returncode=0)
        process.poll.return_value = 0
        process.communicate.return_value = ('{"ok":true}', "")
        return process, [
            mock.patch.object(self.b.subprocess, "Popen", return_value=process),
            mock.patch.object(self.b, "_create_windows_kill_job", return_value={"fake": True}),
            mock.patch.object(self.b, "_resume_windows_process", return_value=True),
            mock.patch.object(self.b, "_close_windows_kill_job", return_value=True),
        ]

    def test_actual_spawn_receipt_prevents_second_launch_with_same_lease(self):
        claimed, lease = self.claim()
        self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        process, patches = self.fake_process_patches()
        with fixtures.ExitStack() as stack:
            popen = stack.enter_context(patches[0])
            for patch in patches[1:]:
                stack.enter_context(patch)
            first = self.run_fake_process(claimed["id"], lease)
            second = self.run_fake_process(claimed["id"], lease)
        self.assertTrue(first["ok"])
        self.assertTrue(first["processStarted"])
        self.assertFalse(second["processStarted"])
        self.assertEqual(second["exitCode"], "cancelled")
        popen.assert_called_once()
        self.assertTrue(self.f.stored()["execution"]["processStarted"])
        self.assertEqual(self.b.parse_iso(self.f.stored()["execution"]["processStartedAt"]),
                         self.start)
        process.communicate.assert_called_once()

    def test_three_role_processes_enter_communicate_before_any_returns_and_cleanup_is_owned(self):
        children = self.f.automatic_children()
        leases = {}
        for child in children:
            child["analysisContext"].update({
                key: self.f.child["analysisContext"][key]
                for key in ("roundStartedAt", "roundDeadlineAt")
            })
            self.b._issue_backend_auto_safe_authorization(child)
            self.b.replace_mission(child)
            claimed = self.b.claim_auto_mission(child["id"], "parallel-" + child["owner"])
            lease = claimed["execution"]["leaseId"]
            leases[child["id"]] = lease
            self.assertIsNotNone(self.b._begin_council_runner_lease(
                child["id"], lease, claimed["budget"]["timeoutSeconds"]))

        all_entered = threading.Event()
        barrier = threading.Barrier(3, action=all_entered.set)
        release = {mission_id: threading.Event() for mission_id in leases}
        observation_lock = threading.Lock()
        processes = {}
        spawn_order = []
        entered = []
        returned = []
        results = {}
        case = self

        class FakeProcess:
            def __init__(self, command, **_kwargs):
                self.mission_id = command[1]
                self.returncode = None
                with observation_lock:
                    self.pid = 7654300 + len(spawn_order)
                    spawn_order.append(self.mission_id)
                    processes[self.mission_id] = self

            def poll(self):
                return self.returncode

            def communicate(self, input=None, timeout=None):
                stored = case.b.find_mission(self.mission_id)
                case.assertTrue(stored["execution"]["processStarted"])
                case.assertEqual(stored["execution"]["leaseId"], leases[self.mission_id])
                case.assertIsNotNone(case.b.parse_iso(stored["execution"]["processStartedAt"]))
                with observation_lock:
                    entered.append(self.mission_id)
                    case.assertEqual(returned, [])
                barrier.wait(10)
                case.assertTrue(release[self.mission_id].wait(10), "fake process was not released")
                with observation_lock:
                    case.assertEqual(set(entered), set(leases))
                    returned.append(self.mission_id)
                self.returncode = 0
                return '{"ok":true}', ""

        def run(mission_id):
            results[mission_id] = self.b._run_safe_command_with_tree_timeout(
                ["never-launch-real-process", mission_id], 120, 1000, None,
                cancel_event=self.b.MISSION_WORKER_STOP,
                tracking_key=mission_id, council_start_lease=leases[mission_id],
                structured_json_output=True)

        def terminate_fake(process, _job):
            process.returncode = -9
            return True

        threads = {mission_id: threading.Thread(target=run, args=(mission_id,)) for mission_id in leases}
        self.b.MISSION_WORKER_STOP.clear()
        with (mock.patch.object(self.b.subprocess, "Popen", FakeProcess),
              mock.patch.object(self.b, "_create_windows_kill_job", side_effect=lambda p: {"missionId": p.mission_id}),
              mock.patch.object(self.b, "_resume_windows_process", return_value=True),
              mock.patch.object(self.b, "_close_windows_kill_job", return_value=True),
              mock.patch.object(self.b, "_terminate_command_process_tree", side_effect=terminate_fake) as kill):
            try:
                for thread in threads.values():
                    thread.start()
                self.assertTrue(all_entered.wait(10), "three guarded launches could not enter communicate concurrently")
                self.assertEqual(len(set(spawn_order)), 3)
                with self.b.MISSION_WORKER_PROCESS_LOCK:
                    self.assertEqual(set(self.b.MISSION_WORKER_PROCESSES), set(leases))
                    for mission_id, tracked in self.b.MISSION_WORKER_PROCESSES.items():
                        self.assertIs(tracked["process"], processes[mission_id])
                        self.assertEqual(tracked["leaseId"], leases[mission_id])

                # Complete the first-spawned worker while its two peers remain
                # inside communicate. Its finally block must leave both intact.
                first = spawn_order[0]
                release[first].set()
                threads[first].join(10)
                self.assertFalse(threads[first].is_alive())
                self.assertTrue(results[first]["ok"], results[first])
                remaining = set(leases) - {first}
                with self.b.MISSION_WORKER_PROCESS_LOCK:
                    self.assertEqual(set(self.b.MISSION_WORKER_PROCESSES), remaining)
                    for mission_id in remaining:
                        self.assertIs(self.b.MISSION_WORKER_PROCESSES[mission_id]["process"], processes[mission_id])
                    self.assertIs(self.b.MISSION_WORKER_PROCESS, processes[spawn_order[-1]])

                for mission_id in remaining:
                    release[mission_id].set()
                for thread in threads.values():
                    thread.join(10)
                self.assertFalse(any(thread.is_alive() for thread in threads.values()))
                self.assertTrue(all(result["ok"] and result["processStarted"] for result in results.values()), results)
                self.assertEqual(set(results), set(leases))
                self.assertEqual(self.b.MISSION_WORKER_PROCESSES, {})
                self.assertIsNone(self.b.MISSION_WORKER_PROCESS)
                kill.assert_not_called()
            finally:
                for event in release.values():
                    event.set()
                barrier.abort()
                self.b.MISSION_WORKER_STOP.set()
                for thread in threads.values():
                    thread.join(10)
        self.f.runner.assert_not_called()
        self.f.dispatch.assert_not_called()

    def test_start_receipt_store_failure_stops_exact_spawned_process(self):
        claimed, lease = self.claim()
        self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        process, patches = self.fake_process_patches()
        with fixtures.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(mock.patch.object(self.b, "save_missions", side_effect=PermissionError("fixture")))
            kill = stack.enter_context(mock.patch.object(self.b, "_terminate_command_process_tree", return_value=True))
            result = self.run_fake_process(claimed["id"], lease)
        self.assertEqual(result["exitCode"], "council_process_start_receipt_failed")
        self.assertTrue(result["processStarted"])
        self.assertTrue(result["processTreeTerminated"])
        kill.assert_called_once_with(process, {"fake": True})
        process.communicate.assert_not_called()
        self.f.dispatch.assert_not_called()

    def test_slow_receipt_storage_never_extends_process_timeout(self):
        claimed, lease = self.claim()
        started = self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        timeout_at = started["execution"]["timeoutAt"]
        process, patches = self.fake_process_patches()
        original_save = self.b.save_missions

        def slow_save(rows):
            original_save(rows)
            self.advance(30)

        with fixtures.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(mock.patch.object(self.b, "save_missions", side_effect=slow_save))
            result = self.run_fake_process(claimed["id"], lease)
        self.assertTrue(result["ok"])
        self.assertEqual(process.communicate.call_args.kwargs["timeout"], 60)
        self.assertEqual(self.f.stored()["execution"]["timeoutAt"], timeout_at)

    def test_watchdog_marks_terminal_before_kill_and_releases_store_lock(self):
        claimed, lease = self.claim()
        self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        self.advance(90)

        class FakeProcess:
            pass

        process = FakeProcess()
        self.b.MISSION_WORKER_PROCESSES[claimed["id"]] = {
            "process": process, "jobHolder": {"fake": True}, "leaseId": lease}

        def kill(captured, _job):
            self.assertIs(captured, process)
            self.assertEqual(self.f.stored()["status"], "failed")
            acquired = threading.Event()

            def peer():
                with self.b.MISSIONS_LOCK:
                    acquired.set()

            thread = threading.Thread(target=peer)
            thread.start()
            self.assertTrue(acquired.wait(2), "watchdog held the store lock during process shutdown")
            thread.join(2)
            return True

        with (mock.patch.object(self.b.subprocess, "Popen", FakeProcess),
              mock.patch.object(self.b, "_terminate_command_process_tree", side_effect=kill)):
            self.assertEqual(self.b.reconcile_timed_out_running_missions(), 1)
        self.assertTrue(self.f.stored()["execution"]["processTreeTerminated"])

    def test_watchdog_never_terminates_process_reference_from_different_lease(self):
        claimed, lease = self.claim()
        self.b._begin_council_runner_lease(claimed["id"], lease, 60)
        self.advance(90)

        class FakeProcess:
            pass

        self.b.MISSION_WORKER_PROCESSES[claimed["id"]] = {
            "process": FakeProcess(), "jobHolder": {}, "leaseId": "different-lease"}
        with (mock.patch.object(self.b.subprocess, "Popen", FakeProcess),
              mock.patch.object(self.b, "_terminate_command_process_tree") as kill):
            self.assertEqual(self.b.reconcile_timed_out_running_missions(), 1)
        kill.assert_not_called()

    def test_claim_updates_parent_progress_once_without_synthesis(self):
        with (mock.patch.object(self.b, "refresh_parent_mission") as refresh,
              mock.patch.object(self.b, "ai_trade_council_consensus") as consensus):
            claimed, _lease = self.claim()
        refresh.assert_not_called()
        consensus.assert_not_called()
        parent = self.b.find_mission(claimed["parentMissionId"])
        self.assertEqual(parent["status"], "running")
        self.assertEqual(parent["delegation"]["subtaskStatusCounts"]["running"], 1)
        self.assertEqual(parent["delegation"]["subtaskStatusCounts"]["queued"], 2)
        self.f.dispatch.assert_not_called()

    def test_manual_council_retains_original_claim_timeout_and_grace(self):
        self.f.child["analysisContext"].pop("automation")
        self.f.save_child()
        claimed, _lease = self.claim()
        self.assertNotIn("leasePhase", claimed["execution"])
        self.assertEqual(self.b.parse_iso(claimed["execution"]["timeoutAt"]),
                         self.start + timedelta(seconds=60))
        self.assertEqual(self.b._auto_mission_watchdog_deadline(claimed, 45),
                         self.start + timedelta(seconds=105))


if __name__ == "__main__":
    unittest.main()
