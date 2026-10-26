"""End-to-end local Council scheduling with inert model runners and a fake clock.

Uses the real queue builder, store, worker selector, claim, and finish paths.
All missions/history/terminal channels are synthetic and inside TemporaryDirectory;
no Codex process, network request, installed runtime or real Common Files is used.
"""
from __future__ import annotations

import copy
import json
import threading
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import test_ai_trade_council_failure_injection as fixtures
import test_council_newbar_worker as worker_fixtures


class CouncilParallelRoundBudgetTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.AiTradeCouncilFailureInjectionTests()
        self.f.setUp()
        self.b = self.f.bridge
        self.stack = ExitStack()
        self.addCleanup(self.f.tearDown)
        self.addCleanup(self.stack.close)
        self.addCleanup(self.b.MISSION_WORKER_STOP.set)
        for patch in self.f._analysis_patches():
            self.stack.enter_context(patch)
        self.stack.enter_context(mock.patch.object(
            self.b, "_metatrader_scope_header_locks_ready", return_value=True))
        self.stack.enter_context(mock.patch.object(self.b, "CODEX_RUNNER_PYTHON", Path(__file__)))
        self.stack.enter_context(mock.patch.object(self.b, "CODEX_RUNNER_SCRIPT", Path(__file__)))
        self.stack.enter_context(mock.patch.object(
            self.b, "_read_mt4_trade_gateway_ea_status",
            return_value=({"maxSnapshotAgeSeconds": 900}, None)))
        self.runner = self.stack.enter_context(mock.patch.object(self.b, "run_safe_command"))
        self.dispatch = self.stack.enter_context(mock.patch.object(
            self.b, "dispatch_ai_trade_council_trade_plan", return_value={
                "status": "no_trade", "reasonCode": "consensus_threshold_not_met",
                "commandPublished": False}))
        self.candidate_id = self.f._configure_selected_mt4()
        self.snapshot = self.b.metatrader_snapshot_read_model(self.b.AI_TRADE_COUNCIL_PROP_ID)
        self.now = datetime.now(timezone.utc)
        self.detected_at = self.now
        test_case = self

        class ControlledDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                value = test_case.now
                return value.astimezone(tz) if tz else value.replace(tzinfo=None)

        self.stack.enter_context(mock.patch.object(self.b, "datetime", ControlledDateTime))
        self.b.MISSION_WORKER_STOP.clear()
        self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS.clear()

    def automation_context(self):
        identity, _ = self.b._ai_trade_council_closed_bar_identity(self.snapshot)
        return {
            "triggerMode": "last_closed_candle_time_change",
            "triggerPolicy": "new_closed_bar_only_no_backfill",
            "triggerStartupId": self.b.SERVER_STARTED_AT,
            "quotaAdmittedAt": self.detected_at.isoformat(),
            "triggerExpiresAt": (self.detected_at + timedelta(seconds=300)).isoformat(),
            "streamKey": identity["streamKey"], "symbol": identity["symbol"],
            "timeframe": identity["timeframe"], "closedBarTime": identity["lastClosedBarTime"],
            "analysisBarCount": self.b.AI_TRADE_COUNCIL_DEFAULT_ANALYSIS_BAR_COUNT,
            "dayKey": self.b._automation_day_key(), "executionPolicy": "current_exact_snapshot",
            "tradeCommandAllowed": True,
        }

    def queue(self):
        result = self.b.run_ai_trade_council_analysis(
            {"snapshotId": self.snapshot["chartSnapshot"]["snapshotId"]},
            automation_context=self.automation_context(), _snapshot_model=copy.deepcopy(self.snapshot))
        parent_id = result["parent"]["id"]
        parent = self.b.find_mission(parent_id)
        children = [row for row in self.b.load_missions() if row.get("parentMissionId") == parent_id]
        return parent, children

    def add_synthetic_history(self, count=1200):
        """~3 MiB historical payload; never read/copy a real missions store."""
        rows = [{
            "id": f"mission-synthetic-history-{index:05d}", "status": "completed",
            "owner": "manager", "title": "Synthetic completed history",
            "createdAt": "2026-01-01T00:00:00Z", "completedAt": "2026-01-01T00:00:01Z",
            "result": "synthetic fixture only " * 100,
            "analysisContext": {"kind": "synthetic_history"},
        } for index in range(count)]
        self.b.save_missions(rows + self.b.load_missions())
        return rows

    def successful_result(self, child):
        return worker_fixtures.CouncilNewBarWorkerTests.successful_result(self, child)

    def run_three_workers(self, *, fail_role=None, advance_at_result=0):
        starts, returns, failures, captured = [], [], [], []
        mutex = threading.Lock()
        launched = threading.Barrier(3, timeout=20)
        finished = threading.Event()
        real_process = self.b.process_auto_mission

        def inert_runner(command, **kwargs):
            mission_id = command[command.index("--mission-id") + 1]
            child = self.b.find_mission(mission_id)
            context = child["analysisContext"]
            with mutex:
                starts.append(context["roleId"])
                captured.append((copy.deepcopy(context), kwargs["timeout"],
                                 int(command[command.index("--timeout") + 1])))
            launched.wait()
            with mutex:
                # No role is allowed to finish before all three actually reached
                # run_safe_command through their real claim/preparation paths.
                self.assertEqual(set(starts), {"technical", "price_action", "news"})
                if advance_at_result:
                    self.now = self.detected_at + timedelta(seconds=advance_at_result)
            if context["roleId"] == fail_role:
                payload = {"ok": False, "status": "failed", "workStatus": "failed",
                           "processStarted": True, "message": "synthetic model failure"}
            else:
                payload = self.successful_result(child)
            return {"ok": True, "processStarted": True, "exitCode": 0,
                    "output": json.dumps(payload)}

        def real_process_and_record(worker_id, mission):
            try:
                real_process(worker_id, mission)
            except BaseException as exc:
                with mutex:
                    failures.append(exc)
                raise
            finally:
                with mutex:
                    returns.append(mission["id"])
                    if len(returns) >= 3:
                        self.b.MISSION_WORKER_STOP.set()
                        self.b.MISSION_WORKER_WAKE.set()
                        finished.set()

        threads = [threading.Thread(target=self.b.ai_trade_council_worker_loop,
                                    args=(f"parallel-integration-{index}",), daemon=True)
                   for index in range(3)]
        self.runner.side_effect = inert_runner
        with mock.patch.object(self.b, "process_auto_mission", side_effect=real_process_and_record):
            try:
                for thread in threads:
                    thread.start()
                self.assertTrue(finished.wait(30), "three real workers failed to finish their admitted roles")
            finally:
                self.b.MISSION_WORKER_STOP.set()
                self.b.MISSION_WORKER_WAKE.set()
                launched.abort()
                for thread in threads:
                    thread.join(10)
                self.assertFalse(any(thread.is_alive() for thread in threads), "worker leaked after fixture")
        self.assertEqual(failures, [])
        self.assertEqual(len(starts), 3)
        self.assertEqual(len(set(returns)), 3)
        self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS, {})
        return captured

    def test_preparation_and_large_history_share_original_300_second_deadline(self):
        history = self.add_synthetic_history()
        render = self.b._render_ai_trade_council_prompt

        def expensive_preparation(*args, **kwargs):
            self.now += timedelta(seconds=35)
            return render(*args, **kwargs)

        with mock.patch.object(self.b, "_render_ai_trade_council_prompt", side_effect=expensive_preparation):
            parent, children = self.queue()
        self.assertEqual(len(children), 3)
        deadline = self.detected_at + timedelta(seconds=300)
        self.assertGreater(self.now, self.detected_at)
        for mission in [parent, *children]:
            context = mission["analysisContext"]
            self.assertEqual(self.b.parse_iso(context["roundStartedAt"]), self.detected_at)
            self.assertEqual(self.b.parse_iso(context["roundDeadlineAt"]), deadline)
        self.assertLess(self.b._ai_trade_council_round_remaining_seconds(children[0]), 300)
        self.assertEqual([row for row in self.b.load_missions()
                          if row["id"].startswith("mission-synthetic-history-")], history)
        again, second_children = self.queue()
        self.assertEqual(again["id"], parent["id"])
        self.assertEqual({row["id"] for row in second_children}, {row["id"] for row in children})
        self.runner.assert_not_called()

    def test_queue_is_one_durable_write_and_external_reader_never_sees_partial_cohort(self):
        history = self.add_synthetic_history(40)
        created_one_child = threading.Event()
        allow_assembly = threading.Event()
        result, errors, observations = [], [], []
        observer_started = threading.Event()
        observer_finished = threading.Event()
        original_create = self.b.create_mission
        child_calls = 0

        def paused_create(payload, **kwargs):
            nonlocal child_calls
            created = original_create(payload, **kwargs)
            if (payload.get("analysisContext") or {}).get("kind") == "ai_trade_council_vote":
                child_calls += 1
                if child_calls == 1:
                    created_one_child.set()
                    if not allow_assembly.wait(10):
                        raise AssertionError("test observer failed to release queue assembly")
            return created

        def assemble():
            try:
                result.append(self.queue())
            except BaseException as exc:
                errors.append(exc)

        def observe():
            observer_started.set()
            observations.append(self.b.load_missions())
            observer_finished.set()

        thread = threading.Thread(target=assemble, daemon=True)
        observer = threading.Thread(target=observe, daemon=True)
        with (mock.patch.object(self.b, "create_mission", side_effect=paused_create),
              mock.patch.object(self.b, "write_json", wraps=self.b.write_json) as writes):
            try:
                thread.start()
                self.assertTrue(created_one_child.wait(10))
                # A reader can either return the previous committed snapshot or
                # wait for the complete transaction. Both are coherent; avoid
                # requiring lock-free reads as an implementation detail.
                observer.start()
                self.assertTrue(observer_started.wait(5))
                # Let an unlocked reader finish while assembly is paused. A
                # locked reader is equally valid and proceeds after release.
                observer_finished.wait(0.1)
            finally:
                allow_assembly.set()
                thread.join(15)
                if observer.ident is not None:
                    observer.join(15)
            self.assertFalse(thread.is_alive())
            self.assertFalse(observer.is_alive())
            self.assertEqual(errors, [])
            archive_writes = [call for call in writes.call_args_list
                              if Path(call.args[0]) == self.b.MISSIONS_PATH]
            self.assertEqual(len(archive_writes), 1)
        self.assertEqual(len(result), 1)
        parent, children = result[0]
        self.assertEqual(len(children), 3)
        published = self.b.load_missions()
        self.assertEqual(sum(row["id"] == parent["id"] for row in published), 1)
        self.assertEqual(sum(row.get("parentMissionId") == parent["id"] for row in published), 3)
        self.assertEqual(len(observations), 1)
        observed_cohort = [row for row in observations[0]
                           if not row["id"].startswith("mission-synthetic-history-")]
        self.assertIn(len(observed_cohort), {0, 4})
        self.assertEqual([row for row in observations[0]
                          if row["id"].startswith("mission-synthetic-history-")], history)
        self.runner.assert_not_called()

    def test_mid_assembly_failure_never_publishes_runnable_partial_round(self):
        history = self.add_synthetic_history(40)
        original_create = self.b.create_mission
        child_calls = 0

        def fail_second_child(payload, **kwargs):
            nonlocal child_calls
            if (payload.get("analysisContext") or {}).get("kind") == "ai_trade_council_vote":
                child_calls += 1
                if child_calls == 2:
                    raise RuntimeError("synthetic queue assembly failure")
            return original_create(payload, **kwargs)

        with (mock.patch.object(self.b, "create_mission", side_effect=fail_second_child),
              mock.patch.object(self.b, "write_json", wraps=self.b.write_json) as writes):
            with self.assertRaises(RuntimeError):
                self.queue()
            archive_writes = [call for call in writes.call_args_list
                              if Path(call.args[0]) == self.b.MISSIONS_PATH]
            self.assertEqual(len(archive_writes), 1)
        stored = self.b.load_missions()
        new_rows = [row for row in stored if not row["id"].startswith("mission-synthetic-history-")]
        self.assertEqual(len(new_rows), 2)
        self.assertTrue(all(row["status"] == "blocked" for row in new_rows))
        self.assertEqual([row for row in stored if row["id"].startswith("mission-synthetic-history-")], history)
        self.assertIsNone(self.b._active_ai_trade_council_parent())
        self.assertIsNone(self.b.find_next_auto_mission(council_only=True))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_final_parent_replace_failure_blocks_all_staged_roles_without_cache_leak(self):
        history = self.add_synthetic_history(40)
        previous_cache = self.b.load_missions(shared_snapshot=True)
        original_replace = self.b.replace_mission
        staged_roles = []

        def fail_final_parent(updated):
            context = updated.get("analysisContext") or {}
            if (context.get("kind") == "ai_trade_council_parent"
                    and updated.get("phase") == "council_specialists_queued"):
                staged_roles.extend(row["analysisContext"]["roleId"]
                                    for row in self.b.load_missions()
                                    if row.get("parentMissionId") == updated["id"])
                raise RuntimeError("synthetic final parent replacement failure")
            return original_replace(updated)

        with (mock.patch.object(self.b, "replace_mission", side_effect=fail_final_parent),
              mock.patch.object(self.b, "write_json", wraps=self.b.write_json) as writes):
            with self.assertRaisesRegex(RuntimeError, "final parent replacement"):
                self.queue()
            archive_writes = [call for call in writes.call_args_list
                              if Path(call.args[0]) == self.b.MISSIONS_PATH]
            self.assertEqual(len(archive_writes), 1)
        self.assertEqual(set(staged_roles), {"technical", "price_action", "news"})
        self.assertEqual(previous_cache, history, "assembly mutated the old shared read cache")
        self.assertIsNone(getattr(self.b.COUNCIL_MISSION_BATCH, "state", None))
        stored = self.b.load_missions(shared_snapshot=True)
        cohort = [row for row in stored if not row["id"].startswith("mission-synthetic-history-")]
        self.assertEqual(len(cohort), 4)
        self.assertEqual({row["status"] for row in cohort}, {"blocked"})
        self.assertEqual({row["phase"] for row in cohort}, {"council_queue_incomplete"})
        self.assertEqual([row for row in stored if row["id"].startswith("mission-synthetic-history-")], history)
        self.assertIsNone(self.b._active_ai_trade_council_parent())
        self.assertIsNone(self.b._reserve_next_ai_trade_council_mission("no-partial-work"))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_final_archive_replace_failure_preserves_store_cache_and_allows_clean_reassembly(self):
        history = self.add_synthetic_history(40)
        previous_bytes = self.b.MISSIONS_PATH.read_bytes()
        previous_cache = self.b.load_missions(shared_snapshot=True)
        original_atomic_replace = self.b._bounded_atomic_replace
        attempted_cohorts = []

        def fail_archive_commit(source, destination, **kwargs):
            if Path(destination) == self.b.MISSIONS_PATH:
                # Fail after real JSON serialization, backup and fsync, at the
                # final destination replacement inside the temporary fixture.
                attempted_cohorts.extend(json.loads(Path(source).read_text(encoding="utf-8"))["missions"])
                raise PermissionError("synthetic final archive replacement denied")
            return original_atomic_replace(source, destination, **kwargs)

        with (mock.patch.object(self.b, "_bounded_atomic_replace", side_effect=fail_archive_commit),
              mock.patch.object(self.b, "write_json", wraps=self.b.write_json) as writes):
            with self.assertRaisesRegex(PermissionError, "final archive replacement"):
                self.queue()
            archive_writes = [call for call in writes.call_args_list
                              if Path(call.args[0]) == self.b.MISSIONS_PATH]
            self.assertEqual(len(archive_writes), 1)
        staged = [row for row in attempted_cohorts if not row["id"].startswith("mission-synthetic-history-")]
        self.assertEqual(len(staged), 4, "failure must occur at the final complete cohort flush")
        self.assertEqual(self.b.MISSIONS_PATH.read_bytes(), previous_bytes)
        self.assertEqual(self.b.MISSIONS_PATH.with_name("missions.json.bak").read_bytes(), previous_bytes)
        self.assertEqual(previous_cache, history)
        self.assertEqual(self.b.load_missions(shared_snapshot=True), history)
        self.assertIsNone(getattr(self.b.COUNCIL_MISSION_BATCH, "state", None))
        self.assertEqual(list(self.b.MISSIONS_PATH.parent.glob(".missions.json.*.tmp")), [])
        self.assertIsNone(self.b._active_ai_trade_council_parent())
        self.assertIsNone(self.b._reserve_next_ai_trade_council_mission("no-failed-commit-work"))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

        parent, children = self.queue()
        self.assertEqual(len(children), 3)
        stored = self.b.load_missions()
        self.assertEqual(sum(row["id"] == parent["id"] for row in stored), 1)
        self.assertEqual(sum(row.get("parentMissionId") == parent["id"] for row in stored), 3)
        self.assertEqual([row for row in stored if row["id"].startswith("mission-synthetic-history-")], history)
        self.assertIsNone(getattr(self.b.COUNCIL_MISSION_BATCH, "state", None))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_three_real_workers_start_before_first_result_on_one_frozen_snapshot(self):
        self.add_synthetic_history()
        parent, children = self.queue()
        captured = self.run_three_workers()
        identity_fields = ("snapshotId", "snapshotArtifact", "snapshotArtifactDigest",
                           "roundStartedAt", "roundDeadlineAt")
        for field in identity_fields:
            self.assertEqual({context[field] for context, _, _ in captured},
                             {parent["analysisContext"][field]})
        for context, outer_timeout, runner_timeout in captured:
            self.assertLessEqual(outer_timeout, 300)
            self.assertLessEqual(runner_timeout, outer_timeout)
        stored = [self.b.find_mission(row["id"]) for row in children]
        self.assertEqual({row["status"] for row in stored}, {"completed"})
        self.assertEqual({row["attemptCount"] for row in stored}, {1})
        self.assertEqual(self.runner.call_count, 3)
        self.assertEqual(self.b.find_mission(parent["id"])["councilDecision"]["voteCount"], 3)
        self.dispatch.assert_called_once()
        self.assertFalse(any(self.f.root.joinpath("common").rglob("command.json")))

    def test_expiry_after_claim_starts_no_model_and_consumes_no_run_budget(self):
        _, children = self.queue()
        original_claim = self.b.claim_auto_mission

        def slow_claim(*args, **kwargs):
            result = original_claim(*args, **kwargs)
            self.now = self.detected_at + timedelta(seconds=300)
            return result

        with (mock.patch.object(self.b, "claim_auto_mission", side_effect=slow_claim),
              mock.patch.object(self.b, "check_rate_limit", return_value=(True, 0)) as rate):
            self.b.process_auto_mission("deadline-after-claim", children[0])
        stored = self.b.find_mission(children[0]["id"])
        self.assertEqual(stored["status"], "blocked")
        self.assertFalse(stored["execution"].get("automaticRetry", False))
        self.assertFalse(stored["execution"].get("processStarted", False))
        self.assertTrue(all(call.kwargs.get("consume") is False for call in rate.call_args_list))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_all_late_results_fail_round_quality_without_trade_publication(self):
        parent, _ = self.queue()
        self.run_three_workers(advance_at_result=301)
        stored = self.b.find_mission(parent["id"])
        quality = stored.get("councilDecision", {}).get("qualityGate", {})
        self.assertFalse(quality.get("passed", False))
        if self.dispatch.called:
            self.assertFalse(self.dispatch.call_args.args[0].get("councilDecision", {})
                             .get("qualityGate", {}).get("passed", False))
        self.assertFalse(any(self.f.root.joinpath("common").rglob("command.json")))

    def test_partial_model_failure_does_not_restart_failed_role_or_publish(self):
        parent, children = self.queue()
        self.run_three_workers(fail_role="news")
        stored = [self.b.find_mission(row["id"]) for row in children]
        failed = next(row for row in stored if row["analysisContext"]["roleId"] == "news")
        self.assertIn(failed["status"], {"failed", "blocked"})
        self.assertFalse(failed["execution"].get("automaticRetry", False))
        self.assertIsNone(failed["execution"].get("nextAttemptAt"))
        self.assertEqual(self.runner.call_count, 3)
        self.b.MISSION_WORKER_STOP.clear()
        self.b.process_auto_mission("no-replay", failed)
        self.assertEqual(self.runner.call_count, 3)
        self.assertFalse(self.b.find_mission(parent["id"]).get("councilDecision", {})
                         .get("qualityGate", {}).get("passed", False))
        self.assertFalse(any(self.f.root.joinpath("common").rglob("command.json")))

    def test_restart_retires_admitted_round_without_creating_backlog(self):
        _, children = self.queue()
        with mock.patch.object(self.b, "SERVER_STARTED_AT", "synthetic-new-startup"):
            for child in children:
                self.b.process_auto_mission("post-restart", child)
        for child in children:
            stored = self.b.find_mission(child["id"])
            self.assertEqual(stored["status"], "blocked")
            self.assertEqual(stored["errorCode"], "council_new_bar_previous_startup_skipped")
            self.assertIsNone(stored["execution"].get("nextAttemptAt"))
        self.assertIsNone(self.b.find_next_auto_mission(council_only=True))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()

    def test_new_bar_retires_old_role_instead_of_spending_model_budget(self):
        _, children = self.queue()
        newer = copy.deepcopy(self.snapshot)
        newer["chartSnapshot"]["bars"][-1]["time"] += 300
        with mock.patch.object(self.b, "metatrader_snapshot_read_model", return_value=newer):
            for child in children:
                self.b.process_auto_mission("bar-replaced", child)
        for child in children:
            stored = self.b.find_mission(child["id"])
            self.assertEqual(stored["errorCode"], "council_new_bar_no_longer_current")
            self.assertFalse(stored["execution"].get("automaticRetry", False))
        self.runner.assert_not_called()
        self.dispatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
