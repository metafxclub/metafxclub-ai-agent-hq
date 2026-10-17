from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("manager_parallel_test_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Bridge")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ManagerParallelMissionTests(unittest.TestCase):
    """Exercise real queue/lease/report code with isolated stores and fake runners."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def setUp(self) -> None:
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.root = Path(self.temp)
        for name, relative in {
            "RUNTIME_DIR": "runtime",
            "MISSIONS_PATH": "runtime/missions.json",
            "RUNTIME_REPORTS_DIR": "runtime/reports",
            "AUDIT_PATH": "runtime/audit.jsonl",
            "AGENT_EVENTS_PATH": "runtime/events.jsonl",
            "OPERATOR_MODE_PATH": "runtime/operator.json",
            "DASHBOARD_WORKFLOW_SETTINGS_PATH": "runtime/dashboard-settings.json",
        }.items():
            self.stack.enter_context(mock.patch.object(self.bridge, name, self.root / relative))
        self.stack.enter_context(mock.patch.object(self.bridge, "CODEX_RUNNER_PYTHON", Path(__file__)))
        self.stack.enter_context(mock.patch.object(self.bridge, "CODEX_RUNNER_SCRIPT", Path(__file__)))
        self.stack.enter_context(mock.patch.object(
            self.bridge, "bridge_status", return_value={"codex": {"status": "ready_guarded"}}
        ))
        self.quota = self.stack.enter_context(mock.patch.object(
            self.bridge, "codex_rate_limits", return_value={
                "ok": True, "stale": False, "limitReached": False,
                "primary": {"remainingPercent": 90},
                "secondary": {"remainingPercent": 90},
            }
        ))
        self.stack.enter_context(mock.patch.object(self.bridge, "automation_min_remaining_percent", return_value=30))
        self.stack.enter_context(mock.patch.object(self.bridge, "check_rate_limit", return_value=(True, 0)))
        self.stack.enter_context(mock.patch.object(self.bridge, "REAL_RUN_SEMAPHORE", threading.BoundedSemaphore(1)))
        self.stack.enter_context(mock.patch.object(
            self.bridge, "MANAGER_READ_ONLY_COHORT", self.bridge.ManagerReadOnlyCohort(3)
        ))
        self.stack.enter_context(mock.patch.object(self.bridge, "MISSION_WORKER_STOP", threading.Event()))
        self.stack.enter_context(mock.patch.object(self.bridge, "MISSION_WORKER_WAKE", threading.Event()))
        self.stack.enter_context(mock.patch.object(self.bridge, "MISSION_WORKER_STATE", {}))
        self.stack.enter_context(mock.patch.object(self.bridge, "MISSION_WORKER_ACTIVE_MISSIONS", {}))
        self.stack.enter_context(mock.patch.object(self.bridge, "MANAGER_DISPATCH_RESERVATIONS", {}))
        self.stack.enter_context(mock.patch.object(self.bridge, "MISSION_WORKER_PROCESSES", {}))
        self.bridge._invalidate_missions_read_cache()
        self.assertTrue(self.bridge.set_operator_mode({"mode": "auto_guarded"})["ok"])

    @staticmethod
    def runner_result(owner: str = "agent") -> dict:
        return {
            "ok": True, "exitCode": 0, "durationMs": 1,
            "processStarted": True, "processTreeTerminated": True,
            "output": json.dumps({
                "ok": True, "status": "completed", "message": "Completed read-only task",
                "finalMessage": f"Verified result from {owner}", "artifacts": {}, "usage": {},
            }),
        }

    def delegate(
        self, owners: tuple[str, ...] = ("risk_guard", "vps_watch", "mission_archivist"),
        *, expected_count: int | None = None,
    ) -> dict:
        contract = copy.deepcopy(self.bridge.load_orchestration_contract())
        contract["managerAutoDelegation"]["specialistRules"] = [
            {
                "id": f"parallel-test-{index}", "priority": 100 - index,
                "keywords": ["bounded explanatory packet"], "agentId": owner,
                "targetPropId": "mission_strategy_table", "reportType": "mission_plan",
                "modelTier": self.bridge.role_default_model_tier(owner),
            }
            for index, owner in enumerate(owners)
        ]
        with mock.patch.object(self.bridge, "load_orchestration_contract", return_value=contract):
            result = self.bridge.manager_delegate({
                "agentId": "manager",
                "goal": "Read-only text-only: Summarize this bounded explanatory packet in three short sentences.",
                "idempotencyKey": f"parallel-test-{len(self.bridge.load_missions())}",
            })
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(result["subtasks"]), len(owners) if expected_count is None else expected_count)
        return result

    def process(self, mission: dict, worker: str = "test-worker") -> None:
        self.bridge.process_auto_mission(worker, copy.deepcopy(mission))

    def assert_general_lease_available(self) -> None:
        self.assertEqual(self.bridge.MANAGER_READ_ONLY_COHORT.snapshot()["activeCount"], 0)
        self.assertTrue(self.bridge.REAL_RUN_SEMAPHORE.acquire(blocking=False))
        self.bridge.REAL_RUN_SEMAPHORE.release()

    def test_three_runners_overlap_fourth_waits_and_final_parent_contains_all_results(self) -> None:
        delegated = self.delegate(("risk_guard", "vps_watch", "mission_archivist", "telegram_ops"))
        children = delegated["subtasks"]
        entered = threading.Event()
        releases = {child["id"]: threading.Event() for child in children}
        calls = []
        lock = threading.Lock()

        def fake_runner(command, **kwargs):
            mission_id = command[command.index("--mission-id") + 1]
            owner = command[command.index("--agent-id") + 1]
            self.assertIn("--read-only-work", command)
            self.assertTrue(kwargs["kill_process_tree_on_timeout"])
            self.assertTrue(kwargs["structured_json_output"])
            self.assertIs(kwargs["cancel_event"], self.bridge.MISSION_WORKER_STOP)
            self.assertEqual(kwargs["tracking_key"], mission_id)
            with lock:
                calls.append(mission_id)
                if len(calls) == 3:
                    entered.set()
            if not releases[mission_id].wait(8):
                raise TimeoutError("Test did not release fake runner")
            return self.runner_result(owner)

        with mock.patch.object(self.bridge, "run_safe_command", side_effect=fake_runner):
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [pool.submit(self.process, child, f"worker-{index}") for index, child in enumerate(children[:3])]
                try:
                    self.assertTrue(entered.wait(5), "All three processes must enter before any is released")
                    self.assertEqual(len(set(calls)), 3)
                    self.assertEqual(self.bridge.MANAGER_READ_ONLY_COHORT.snapshot()["activeCount"], 3)
                    worker_state = self.bridge.mission_worker_read_model()
                    self.assertEqual(set(worker_state["activeMissionIds"]), {child["id"] for child in children[:3]})
                    self.assertEqual(worker_state["managerReadOnlyActiveCount"], 3)
                    self.assertTrue(all(self.bridge.find_mission(child["id"])["status"] == "running" for child in children[:3]))
                    self.assertFalse(self.bridge.REAL_RUN_SEMAPHORE.acquire(blocking=False))
                    self.process(children[3], "worker-fourth")
                    waiting = self.bridge.find_mission(children[3]["id"])
                    self.assertEqual(waiting["status"], "queued")
                    self.assertEqual(waiting.get("attemptCount", 0), 0)
                    self.assertEqual(len(calls), 3)
                    for index in (0, 1):
                        releases[children[index]["id"]].set()
                        futures[index].result(timeout=5)
                        parent = self.bridge.find_mission(delegated["parent"]["id"])
                        self.assertNotEqual(parent["status"], "completed")
                        self.assertFalse((parent.get("delegation") or {}).get("finalReportId"))
                finally:
                    for release in releases.values():
                        release.set()
                for future in futures:
                    future.result(timeout=5)
                fourth = self.bridge.find_mission(children[3]["id"])
                fourth["execution"]["nextAttemptAt"] = None
                self.bridge.replace_mission(fourth)
                self.process(fourth, "worker-fourth-retry")
        self.assertEqual(len(set(calls)), 4)
        parent = self.bridge.find_mission(delegated["parent"]["id"])
        self.assertEqual(parent["status"], "completed")
        self.assertEqual(parent["phase"], "synthesized")
        self.assertEqual(parent["delegation"]["subtaskStatusCounts"].get("completed"), 4)
        final_id = parent["delegation"]["finalReportId"]
        report = json.loads((self.bridge.RUNTIME_REPORTS_DIR / f"{final_id}.json").read_text(encoding="utf-8"))
        report_text = json.dumps(report)
        for child in children:
            self.assertIn(child["owner"], report_text)
        self.assert_general_lease_available()

    def test_assembling_delegation_is_not_visible_to_either_worker_lane(self) -> None:
        first_child_saved = threading.Event()
        finish_assembly = threading.Event()
        real_create = self.bridge.create_mission
        observed = []

        def paused_create(payload, *args, **kwargs):
            created = real_create(payload, *args, **kwargs)
            if payload.get("parentMissionId") and not observed:
                observed.append(created)
                first_child_saved.set()
                if not finish_assembly.wait(8):
                    raise TimeoutError("Test did not release delegation assembly")
            return created

        with mock.patch.object(self.bridge, "create_mission", side_effect=paused_create):
            with ThreadPoolExecutor(max_workers=1) as pool:
                delegated = pool.submit(self.delegate)
                try:
                    self.assertTrue(first_child_saved.wait(5))
                    for lane in (False, True):
                        self.assertIsNone(self.bridge.find_next_auto_mission(council_only=False, manager_parallel_only=lane))
                    self.assertIsNone(self.bridge.claim_auto_mission(observed[0]["id"], "premature-worker"))
                    self.assertEqual(self.bridge.find_mission(observed[0]["id"])["status"], "queued")
                finally:
                    finish_assembly.set()
                result = delegated.result(timeout=5)
        self.assertEqual(len(result["subtasks"]), 3)
        self.assertIsNotNone(self.bridge.find_next_auto_mission(council_only=False, manager_parallel_only=True))

    def test_claim_context_change_cannot_fall_through_to_workspace_write(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        original_claim = self.bridge.claim_auto_mission

        def changed_claim(*args, **kwargs):
            claimed = original_claim(*args, **kwargs)
            self.assertIsNotNone(claimed)
            claimed["detail"] += " Modified scope."
            self.bridge.replace_mission(claimed)
            return claimed

        with mock.patch.object(self.bridge, "claim_auto_mission", side_effect=changed_claim), mock.patch.object(
            self.bridge, "run_safe_command"
        ) as runner:
            self.process(mission)
        runner.assert_not_called()
        current = self.bridge.find_mission(mission["id"])
        self.assertEqual(current["status"], "blocked")
        self.assertEqual(current["errorCode"], "manager_parallel_claim_context_invalid")
        self.assert_general_lease_available()

    def test_duplicate_dispatch_claims_and_debits_only_once(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        barrier = threading.Barrier(8)
        rate_calls = []

        def fake_rate(*args, **kwargs):
            rate_calls.append(kwargs.get("consume", True))
            return True, 0

        def dispatch(index):
            barrier.wait(timeout=5)
            self.process(mission, f"duplicate-{index}")

        with mock.patch.object(self.bridge, "run_safe_command", return_value=self.runner_result()) as runner, mock.patch.object(
            self.bridge, "check_rate_limit", side_effect=fake_rate
        ):
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(dispatch, range(8)))
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(rate_calls.count(True), 1)
        current = self.bridge.find_mission(mission["id"])
        self.assertEqual(current["attemptCount"], 1)
        events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=100)
        self.assertEqual(sum(row.get("type") == "mission.auto_claimed" and row.get("missionId") == mission["id"] for row in events), 1)
        self.assert_general_lease_available()

    def test_cohort_rejects_same_owner_other_parent_duplicate_and_fourth(self) -> None:
        cohort = self.bridge.MANAGER_READ_ONLY_COHORT
        sem = self.bridge.REAL_RUN_SEMAPHORE
        self.assertTrue(cohort.acquire("one", "risk_guard", "mission_strategy_table", "parent", sem))
        self.assertFalse(cohort.acquire("one", "vps_watch", "mission_strategy_table", "parent", sem))
        self.assertFalse(cohort.acquire("two", "risk_guard", "mission_strategy_table", "parent", sem))
        self.assertFalse(cohort.acquire("two", "vps_watch", "mission_strategy_table", "another-parent", sem))
        self.assertTrue(cohort.acquire("two", "vps_watch", "mission_strategy_table", "parent", sem))
        self.assertTrue(cohort.acquire("three", "mission_archivist", "mission_strategy_table", "parent", sem))
        self.assertFalse(cohort.acquire("four", "telegram_ops", "mission_strategy_table", "parent", sem))
        cohort.release("one")
        self.assertFalse(sem.acquire(blocking=False), "An unfinished sibling still owns the exclusive resource")
        cohort.release("two")
        self.assertFalse(sem.acquire(blocking=False))
        cohort.release("three")
        cohort.release("three")
        self.assert_general_lease_available()

    def test_exclusive_general_run_prevents_read_only_cohort_start(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        self.assertTrue(self.bridge.REAL_RUN_SEMAPHORE.acquire(blocking=False))
        try:
            with mock.patch.object(self.bridge, "run_safe_command") as runner:
                self.process(mission)
            runner.assert_not_called()
            self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "queued")
        finally:
            self.bridge.REAL_RUN_SEMAPHORE.release()
        self.assert_general_lease_available()

    def test_quota_guards_reject_before_claim_and_leave_capacity_available(self) -> None:
        for reason, quota in (
            ("stale", {"ok": True, "stale": True, "limitReached": False}),
            ("unavailable", {"ok": False, "stale": False}),
            ("limit", {"ok": True, "stale": False, "limitReached": True}),
            ("reserve", {"ok": True, "stale": False, "limitReached": False, "primary": {"remainingPercent": 29}}),
        ):
            with self.subTest(reason=reason):
                mission = self.delegate(("risk_guard",))["subtasks"][0]
                self.quota.return_value = quota
                with mock.patch.object(self.bridge, "run_safe_command") as runner:
                    self.process(mission)
                runner.assert_not_called()
                current = self.bridge.find_mission(mission["id"])
                self.assertEqual(current["status"], "queued")
                self.assertEqual(current.get("attemptCount", 0), 0)
                self.assertFalse(current["execution"].get("authorizationConsumedAt"))
                self.assert_general_lease_available()

    def test_modified_authorization_never_launches_runner(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        mission["detail"] += " Changed after authorization."
        self.bridge.replace_mission(mission)
        with mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.process(mission)
        runner.assert_not_called()
        self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "blocked")
        self.assert_general_lease_available()

    def test_pending_approval_cannot_use_parallel_lane(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        mission["approval"].update(required=True, state="pending", gateMode="human")
        mission["status"] = "waiting_approval"
        self.bridge.replace_mission(mission)
        self.assertFalse(self.bridge._manager_parallel_read_only_candidate(mission))
        with mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.process(mission)
        runner.assert_not_called()
        self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "waiting_approval")
        self.assert_general_lease_available()

    def test_shutdown_before_dispatch_does_not_claim_or_consume(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        self.bridge.MISSION_WORKER_STOP.set()
        with mock.patch.object(self.bridge, "run_safe_command") as runner:
            self.process(mission)
        runner.assert_not_called()
        current = self.bridge.find_mission(mission["id"])
        self.assertEqual(current["status"], "queued")
        self.assertEqual(current.get("attemptCount", 0), 0)
        self.assert_general_lease_available()

    def test_runner_exception_releases_cohort_and_keeps_failure_terminal(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        with mock.patch.object(self.bridge, "run_safe_command", side_effect=OSError("simulated runner start failure")) as runner:
            self.process(mission)
            self.process(mission)
        self.assertEqual(runner.call_count, 1)
        current = self.bridge.find_mission(mission["id"])
        self.assertIn(current["status"], {"blocked", "failed"})
        self.assertFalse(current["execution"]["automaticRetry"])
        self.assert_general_lease_available()

    def test_shutdown_event_reaches_every_running_child(self) -> None:
        children = self.delegate()["subtasks"]
        barrier = threading.Barrier(4)

        def cancelled_runner(command, **kwargs):
            barrier.wait(timeout=5)
            self.assertTrue(kwargs["cancel_event"].wait(5))
            return {"ok": False, "exitCode": "cancelled", "output": "", "processStarted": True, "processTreeTerminated": True}

        with mock.patch.object(self.bridge, "run_safe_command", side_effect=cancelled_runner):
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [pool.submit(self.process, child) for child in children]
                try:
                    barrier.wait(timeout=5)
                finally:
                    self.bridge.MISSION_WORKER_STOP.set()
                for future in futures:
                    future.result(timeout=5)
        for child in children:
            current = self.bridge.find_mission(child["id"])
            self.assertIn(current["status"], {"blocked", "failed"})
            self.assertTrue(current["execution"]["processTreeTerminated"])
            self.assertFalse(current["execution"]["automaticRetry"])
        self.assert_general_lease_available()

    def test_watchdog_timeout_cannot_be_resurrected_by_late_success(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        claimed = self.bridge.claim_auto_mission(mission["id"], "timeout-worker")
        self.assertIsNotNone(claimed)
        claimed["execution"]["timeoutAt"] = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        self.bridge.replace_mission(claimed)
        self.assertEqual(self.bridge.reconcile_timed_out_running_missions(), 1)
        self.assertIsNone(self.bridge.finish_auto_mission(
            mission["id"], claimed["execution"]["leaseId"], self.runner_result(),
            {"ok": True, "status": "completed", "finalMessage": "Late result must not overwrite timeout"},
        ))
        current = self.bridge.find_mission(mission["id"])
        self.assertEqual(current["status"], "failed")
        self.assertEqual(current["errorCode"], "auto_worker_timeout")

    def test_parent_waits_for_child_report_commit_and_synthesizes_once(self) -> None:
        delegated = self.delegate()
        children = delegated["subtasks"]
        parent_id = delegated["parent"]["id"]
        report_entered = threading.Event()
        release_report = threading.Event()
        real_report = self.bridge.create_report

        def held_report(payload, *args, **kwargs):
            if payload.get("linkedMissionId") == children[0]["id"]:
                report_entered.set()
                if not release_report.wait(8):
                    raise TimeoutError("Test did not release child report")
            return real_report(payload, *args, **kwargs)

        with mock.patch.object(self.bridge, "run_safe_command", return_value=self.runner_result()), mock.patch.object(
            self.bridge, "create_report", side_effect=held_report
        ):
            with ThreadPoolExecutor(max_workers=4) as pool:
                first = pool.submit(self.process, children[0])
                try:
                    self.assertTrue(report_entered.wait(5))
                    remaining = [pool.submit(self.process, child) for child in children[1:]]
                    # Aggregation must wait for the report transaction, even if
                    # a polling request races the unfinished report write.
                    refresh = pool.submit(self.bridge.refresh_parent_mission, parent_id)
                    with self.assertRaises(FutureTimeoutError):
                        refresh.result(timeout=0.25)
                    parent = self.bridge.find_mission(parent_id)
                    self.assertNotEqual(parent["status"], "completed")
                    self.assertFalse((parent.get("delegation") or {}).get("finalReportId"))
                finally:
                    release_report.set()
                first.result(timeout=5)
                for future in remaining:
                    future.result(timeout=5)
                refresh.result(timeout=5)
            with ThreadPoolExecutor(max_workers=3) as pool:
                parents = list(pool.map(lambda _: self.bridge.refresh_parent_mission(parent_id), range(3)))
        final_ids = {row["delegation"]["finalReportId"] for row in parents}
        self.assertEqual(len(final_ids), 1)
        self.assertTrue(all(row["status"] == "completed" for row in parents))
        reports = [json.loads(path.read_text(encoding="utf-8")) for path in self.bridge.RUNTIME_REPORTS_DIR.glob("*.json")]
        final_reports = [row for row in reports if row.get("linkedMissionId") == parent_id and row.get("type") == "executive_summary"]
        self.assertEqual(len(final_reports), 1)
        events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=200)
        self.assertEqual(sum(row.get("type") == "manager.parent_refreshed" and row.get("missionId") == parent_id and row.get("phase") == "synthesized" for row in events), 1)
        self.assert_general_lease_available()

    def test_child_report_storage_failure_never_produces_successful_parent(self) -> None:
        delegated = self.delegate()
        children = delegated["subtasks"]
        real_report = self.bridge.create_report

        def failing_report(payload, *args, **kwargs):
            if payload.get("linkedMissionId") == children[0]["id"]:
                raise OSError("simulated report storage failure")
            return real_report(payload, *args, **kwargs)

        with mock.patch.object(self.bridge, "run_safe_command", return_value=self.runner_result()), mock.patch.object(
            self.bridge, "create_report", side_effect=failing_report
        ):
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(self.process, children))
        parent = self.bridge.find_mission(delegated["parent"]["id"])
        self.assertEqual(parent["status"], "blocked")
        self.assertEqual(parent["phase"], "review_required")
        failed = self.bridge.find_mission(children[0]["id"])
        self.assertNotEqual(failed["status"], "completed")
        self.assert_general_lease_available()

    def test_worker_start_is_idempotent_and_shutdown_joins_all_three_manager_workers(self) -> None:
        for name, value in (
            ("MISSION_WORKER_THREAD", None), ("MISSION_WORKER_WATCHDOG_THREAD", None),
            ("MANAGER_MISSION_WORKER_THREADS", []), ("AI_TRADE_COUNCIL_WORKER_THREADS", []),
            ("MISSION_WORKER_PROCESS", None), ("MISSION_WORKER_JOB_HOLDER", None),
        ):
            self.stack.enter_context(mock.patch.object(self.bridge, name, value))

        def held_loop(*_args):
            self.bridge.MISSION_WORKER_STOP.wait(8)

        for name in ("mission_worker_loop", "manager_read_only_worker_loop", "ai_trade_council_worker_loop", "mission_timeout_watchdog_loop"):
            self.stack.enter_context(mock.patch.object(self.bridge, name, side_effect=held_loop))
        try:
            first = self.bridge.start_mission_worker()
            manager_threads = list(self.bridge.MANAGER_MISSION_WORKER_THREADS)
            self.assertEqual(len(manager_threads), 3)
            self.assertTrue(all(thread.is_alive() for thread in manager_threads))
            self.assertIs(self.bridge.start_mission_worker(), first)
            self.assertEqual(self.bridge.MANAGER_MISSION_WORKER_THREADS, manager_threads)
        finally:
            self.bridge.stop_mission_worker()
        self.assertTrue(self.bridge.MISSION_WORKER_STOP.is_set())
        self.assertTrue(all(not thread.is_alive() for thread in manager_threads))
        self.assertFalse(first.is_alive())

    def test_completed_child_without_durable_report_after_crash_cannot_complete_parent(self) -> None:
        delegated = self.delegate()
        children = delegated["subtasks"]
        with mock.patch.object(self.bridge, "run_safe_command", return_value=self.runner_result()):
            self.process(children[0])
            self.process(children[1])
        interrupted = self.bridge.claim_auto_mission(children[2]["id"], "crashed-worker")
        self.assertIsNotNone(interrupted)
        interrupted.update({
            "status": "completed", "phase": "auto_guarded_completed", "result": "Uncommitted worker result",
            "completedAt": self.bridge.utc_now(), "updatedAt": self.bridge.utc_now(), "reportIds": [],
        })
        interrupted["execution"].update({
            "dispatchState": "completed", "concurrencyGroup": "manager_read_only_parallel_3",
            "processStarted": True, "automaticRetry": False,
        })
        # Simulate the durable state left by a crash after result persistence
        # but before the child's report was created and linked.
        self.bridge.replace_mission(interrupted)
        parent = self.bridge.refresh_parent_mission(delegated["parent"]["id"])
        self.assertEqual(parent["status"], "blocked")
        self.assertEqual(parent["phase"], "review_required")
        recovered = self.bridge.find_mission(interrupted["id"])
        self.assertEqual(recovered["status"], "failed")
        self.assertEqual(recovered["errorCode"], "manager_child_report_missing")
        self.assertFalse(recovered["execution"]["automaticRetry"])
        events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=200)
        self.assertFalse(any(row.get("type") == "manager.parent_refreshed" and row.get("missionId") == parent["id"] and row.get("phase") == "synthesized" for row in events))

    def test_stop_after_run_start_audit_still_prevents_process_launch(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        real_audit = self.bridge.append_audit

        def stop_at_audit(payload, *args, **kwargs):
            result = real_audit(payload, *args, **kwargs)
            if payload.get("type") == "mission.auto_run_start":
                self.bridge.MISSION_WORKER_STOP.set()
            return result

        with mock.patch.object(self.bridge, "append_audit", side_effect=stop_at_audit), mock.patch.object(
            self.bridge, "run_safe_command"
        ) as runner:
            self.process(mission)
        runner.assert_not_called()
        current = self.bridge.find_mission(mission["id"])
        self.assertIn(current["status"], {"blocked", "failed"})
        self.assertFalse(current["execution"]["processStarted"])
        self.assertFalse(current["execution"]["automaticRetry"])
        self.assert_general_lease_available()

    def test_denied_first_delegation_rule_does_not_block_later_children(self) -> None:
        real_permission = self.bridge.evaluate_tool_permission

        def deny_first(agent_id, tool_id, *args, **kwargs):
            if agent_id == "risk_guard" and tool_id == "codex_cli_task":
                return {"allowed": False, "reason": "test_role_policy_denied"}
            return real_permission(agent_id, tool_id, *args, **kwargs)

        with mock.patch.object(self.bridge, "evaluate_tool_permission", side_effect=deny_first):
            delegated = self.delegate(expected_count=2)
        self.assertEqual({child["owner"] for child in delegated["subtasks"]}, {"vps_watch", "mission_archivist"})
        self.assertIsNotNone(self.bridge.find_next_auto_mission(council_only=False, manager_parallel_only=True))
        with mock.patch.object(self.bridge, "run_safe_command", return_value=self.runner_result()) as runner:
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(self.process, delegated["subtasks"]))
        self.assertEqual(runner.call_count, 2)
        parent = self.bridge.find_mission(delegated["parent"]["id"])
        self.assertEqual(parent["status"], "completed")
        self.assertEqual(parent["delegation"]["subtaskStatusCounts"].get("completed"), 2)
        self.assert_general_lease_available()

    def test_read_only_subject_or_negated_mode_never_selects_parallel_write_task(self) -> None:
        for index, goal in enumerate((
            "Create README describing read-only dashboard.",
            "Not read-only: update the README with this dashboard description.",
            "Read-only text-only: create README with this explanation.",
        )):
            with self.subTest(goal=goal):
                delegated = self.bridge.manager_delegate({
                    "agentId": "manager", "goal": goal,
                    "requestedOwnerAgentId": "risk_guard", "requestedTargetId": "mission_strategy_table",
                    "idempotencyKey": f"intent-boundary-{index}",
                })
                self.assertTrue(delegated["ok"], delegated)
                self.assertEqual(len(delegated["subtasks"]), 1)
                mission = delegated["subtasks"][0]
                self.assertFalse(self.bridge._manager_parallel_read_only_candidate(mission))
                self.assertIsNone(self.bridge.find_next_auto_mission(council_only=False, manager_parallel_only=True))
                # These existing workspace requests retain their serial route;
                # a mention of read-only must not silently change execution.
                with mock.patch.object(self.bridge, "run_safe_command", return_value=self.runner_result()) as runner:
                    self.process(mission)
                self.assertEqual(runner.call_count, 1)
                self.assertNotIn("--read-only-work", runner.call_args.args[0])
                self.assert_general_lease_available()

    def test_losing_council_claim_preserves_winner_active_state_and_capacity(self) -> None:
        mission = {
            "id": "mission-council-duplicate-claim", "owner": "optimization_agent",
            "toolId": "codex_cli_task", "modelTier": "specialist_balanced", "status": "queued",
            "budget": {"timeoutSeconds": 60, "outputLimitChars": 7000},
            "analysisContext": {
                "kind": "ai_trade_council_vote", "agentId": "optimization_agent", "roleId": "technical",
                "readOnly": True,
                "roundDeadlineAt": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            },
        }
        semaphore = threading.BoundedSemaphore(3)
        self.assertTrue(semaphore.acquire(blocking=False))  # The winning runner already holds one slot.
        self.bridge._set_mission_worker_active(mission["id"], "winning-worker", "ai_trade_council_parallel_3")
        winning_record = copy.deepcopy(self.bridge.MISSION_WORKER_ACTIVE_MISSIONS[mission["id"]])
        with mock.patch.object(self.bridge, "AI_TRADE_COUNCIL_RUN_SEMAPHORE", semaphore), mock.patch.object(
            self.bridge, "_metatrader_scope_header_locks_ready", return_value=True
        ), mock.patch.object(self.bridge, "claim_auto_mission", return_value=None) as claim, mock.patch.object(
            self.bridge, "run_safe_command"
        ) as runner:
            self.process(mission, "losing-worker")
        claim.assert_called_once_with(mission["id"], "losing-worker")
        runner.assert_not_called()
        self.assertEqual(self.bridge.MISSION_WORKER_ACTIVE_MISSIONS[mission["id"]], winning_record)
        self.assertEqual(self.bridge.mission_worker_read_model()["activeMissionIds"], [mission["id"]])
        self.assertTrue(semaphore.acquire(blocking=False))
        self.assertTrue(semaphore.acquire(blocking=False))
        self.assertFalse(semaphore.acquire(blocking=False), "Losing claim must not release the winner's slot")
        for _ in range(3):
            semaphore.release()

    def test_duplicate_cohort_reservation_does_not_defer_winning_claim(self) -> None:
        mission = self.delegate(("risk_guard",))["subtasks"][0]
        cohort = self.bridge.MANAGER_READ_ONLY_COHORT
        self.assertTrue(cohort.acquire(mission["id"], mission["owner"], mission["targetId"], mission["parentMissionId"], self.bridge.REAL_RUN_SEMAPHORE))
        try:
            with mock.patch.object(self.bridge, "run_safe_command") as runner:
                self.process(mission, "losing-worker")
            runner.assert_not_called()
            current = self.bridge.find_mission(mission["id"])
            self.assertEqual(current["status"], "queued")
            self.assertEqual(current["execution"]["dispatchState"], "queued")
            self.assertIsNone(current["execution"].get("nextAttemptAt"))
            self.assertIsNotNone(self.bridge.claim_auto_mission(mission["id"], "winning-worker"))
        finally:
            cohort.release(mission["id"])
        self.assert_general_lease_available()

    def test_real_manager_loops_select_three_distinct_jobs_before_slow_preflight(self) -> None:
        children = self.delegate()["subtasks"]
        expected = {child["id"] for child in children}
        preflight_entered = threading.Event()
        runners_entered = threading.Event()
        release_preflight = threading.Event()
        release_runners = threading.Event()
        preflight_threads = []
        runner_ids = []
        lock = threading.Lock()

        def slow_preflight():
            with lock:
                preflight_threads.append(threading.get_ident())
                if len(preflight_threads) == 3:
                    preflight_entered.set()
            if not release_preflight.wait(8):
                raise TimeoutError("Test did not release readiness check")
            return {"codex": {"status": "ready_guarded"}}

        def held_runner(command, **_kwargs):
            mission_id = command[command.index("--mission-id") + 1]
            with lock:
                runner_ids.append(mission_id)
                if len(runner_ids) == 3:
                    runners_entered.set()
            if not release_runners.wait(8):
                raise TimeoutError("Test did not release parallel runners")
            return self.runner_result()

        workers = [threading.Thread(target=self.bridge.manager_read_only_worker_loop, args=(f"actual-loop-{index}",), daemon=True) for index in range(3)]
        with mock.patch.object(self.bridge, "bridge_status", side_effect=slow_preflight), mock.patch.object(
            self.bridge, "run_safe_command", side_effect=held_runner
        ):
            try:
                for worker in workers:
                    worker.start()
                self.assertTrue(preflight_entered.wait(5), "Three real worker loops must reach preflight independently")
                self.assertEqual(len(set(preflight_threads)), 3)
                self.assertEqual(set(self.bridge.MANAGER_DISPATCH_RESERVATIONS), expected)
                self.assertEqual(runner_ids, [])
                self.assertTrue(all(self.bridge.find_mission(child["id"])["status"] == "queued" for child in children))
                release_preflight.set()
                self.assertTrue(runners_entered.wait(5), "All three runners must start before any is released")
                self.assertEqual(set(runner_ids), expected)
                self.assertEqual(len(runner_ids), 3)
                self.assertEqual(set(self.bridge.mission_worker_read_model()["activeMissionIds"]), expected)
                self.assertTrue(all(self.bridge.find_mission(child["id"])["status"] == "running" for child in children))
            finally:
                self.bridge.MISSION_WORKER_STOP.set()
                self.bridge.MISSION_WORKER_WAKE.set()
                release_preflight.set()
                release_runners.set()
                for worker in workers:
                    worker.join(timeout=5)
        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(self.bridge.MANAGER_DISPATCH_RESERVATIONS, {})
        self.assert_general_lease_available()

    def test_selection_reservations_are_unique_bounded_and_release_only_by_owner(self) -> None:
        children = self.delegate(("risk_guard", "vps_watch", "mission_archivist", "telegram_ops"))["subtasks"]
        barrier = threading.Barrier(3)

        def reserve(index):
            barrier.wait(timeout=5)
            return self.bridge._reserve_next_manager_auto_mission(f"selector-{index}")

        with ThreadPoolExecutor(max_workers=3) as pool:
            selected = list(pool.map(reserve, range(3)))
        self.assertTrue(all(selected))
        self.assertEqual(len({row["id"] for row in selected}), 3)
        self.assertIsNone(self.bridge._reserve_next_manager_auto_mission("selector-fourth"))
        first = selected[0]
        self.bridge._release_manager_dispatch_reservation(first["id"], "wrong-worker")
        self.assertIn(first["id"], self.bridge.MANAGER_DISPATCH_RESERVATIONS)
        self.bridge._release_manager_dispatch_reservation(first["id"], "selector-0")
        self.assertIsNotNone(self.bridge._reserve_next_manager_auto_mission("replacement-worker"))
        for mission_id, row in list(self.bridge.MANAGER_DISPATCH_RESERVATIONS.items()):
            self.bridge._release_manager_dispatch_reservation(mission_id, row["workerId"])
        self.assertEqual(self.bridge.MANAGER_DISPATCH_RESERVATIONS, {})
        for child in children:
            current = self.bridge.find_mission(child["id"])
            self.assertEqual(current.get("attemptCount", 0), 0)
            self.assertFalse(current["execution"].get("authorizationConsumedAt"))
        self.assert_general_lease_available()

    def test_manager_loop_releases_selection_if_preflight_raises(self) -> None:
        self.delegate()

        def failing_preflight():
            self.bridge.MISSION_WORKER_STOP.set()
            self.bridge.MISSION_WORKER_WAKE.set()
            raise OSError("simulated readiness failure")

        with mock.patch.object(self.bridge, "bridge_status", side_effect=failing_preflight), mock.patch.object(
            self.bridge, "run_safe_command"
        ) as runner:
            self.bridge.manager_read_only_worker_loop("failing-selector")
        runner.assert_not_called()
        self.assertEqual(self.bridge.MANAGER_DISPATCH_RESERVATIONS, {})
        self.assert_general_lease_available()

    def test_manager_loop_releases_selection_when_stop_arrives_after_selection(self) -> None:
        self.delegate()
        real_reserve = self.bridge._reserve_next_manager_auto_mission

        def stop_after_reserve(worker_id):
            mission = real_reserve(worker_id)
            self.assertIsNotNone(mission)
            self.bridge.MISSION_WORKER_STOP.set()
            return mission

        with mock.patch.object(self.bridge, "_reserve_next_manager_auto_mission", side_effect=stop_after_reserve), mock.patch.object(
            self.bridge, "process_auto_mission"
        ) as process:
            self.bridge.manager_read_only_worker_loop("stopping-selector")
        process.assert_not_called()
        self.assertEqual(self.bridge.MANAGER_DISPATCH_RESERVATIONS, {})
        self.assert_general_lease_available()

    def test_parallel_claim_persists_child_group_and_parent_counts_in_one_commit(self) -> None:
        delegated = self.delegate()
        mission = delegated["subtasks"][0]
        cohort = self.bridge.MANAGER_READ_ONLY_COHORT
        self.assertTrue(cohort.acquire(mission["id"], mission["owner"], mission["targetId"], mission["parentMissionId"], self.bridge.REAL_RUN_SEMAPHORE))
        try:
            with mock.patch.object(self.bridge, "save_missions", wraps=self.bridge.save_missions) as save, mock.patch.object(
                self.bridge, "refresh_parent_mission", wraps=self.bridge.refresh_parent_mission
            ) as refresh:
                claimed = self.bridge.claim_auto_mission(mission["id"], "atomic-claim-worker")
            self.assertIsNotNone(claimed)
            self.assertEqual(save.call_count, 1, "Parallel claim must not repeatedly serialize the full Mission store")
            refresh.assert_not_called()
            current = self.bridge.find_mission(mission["id"])
            self.assertEqual(current["execution"]["concurrencyGroup"], "manager_read_only_parallel_3")
            self.assertEqual(claimed["execution"]["concurrencyGroup"], "manager_read_only_parallel_3")
            parent = self.bridge.find_mission(delegated["parent"]["id"])
            self.assertEqual(parent["status"], "running")
            self.assertEqual(parent["phase"], "specialists_running")
            self.assertEqual(parent["delegation"]["subtaskStatusCounts"]["running"], 1)
            self.assertEqual(parent["delegation"]["subtaskStatusCounts"]["queued"], 2)
        finally:
            cohort.release(mission["id"])
        self.assert_general_lease_available()

    def test_completed_parent_verifies_exact_child_reports_outside_recent_report_window(self) -> None:
        delegated = self.delegate()
        with mock.patch.object(self.bridge, "run_safe_command", return_value=self.runner_result()):
            for child in delegated["subtasks"]:
                self.process(child)
        parent_id = delegated["parent"]["id"]
        before = self.bridge.find_mission(parent_id)
        self.assertEqual(before["status"], "completed")
        report_id = before["delegation"]["finalReportId"]
        # A bounded recent-report index may omit these durable older reports.
        # Their exact filenames remain authoritative for the parent binding.
        with mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]):
            after = self.bridge.refresh_parent_mission(parent_id)
        self.assertEqual(after["status"], "completed")
        self.assertEqual(after["phase"], "synthesized")
        self.assertEqual(after["delegation"]["finalReportId"], report_id)
        for child in delegated["subtasks"]:
            self.assertEqual(self.bridge.find_mission(child["id"])["status"], "completed")


if __name__ == "__main__":
    unittest.main()
