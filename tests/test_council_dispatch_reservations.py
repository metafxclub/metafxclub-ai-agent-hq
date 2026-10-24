"""Exercise real finder/worker/claim code with temporary stores and inert runners."""
from __future__ import annotations

import ast
import copy
import threading
import unittest
from pathlib import Path
from unittest import mock

import test_council_newbar_worker as fixtures

BASELINE = Path(__file__).resolve().parent / "fixtures/council_worker_before_reservation.py"


class CouncilDispatchReservationTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.CouncilNewBarWorkerTests()
        self.f.setUp()
        self.b = self.f.b
        self.children = self.f.automatic_children()
        self.b.MISSION_WORKER_STOP.clear()
        self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS.clear()

    def tearDown(self):
        self.b.MISSION_WORKER_STOP.set()
        self.f.tearDown()

    def _concurrent_preclaim_selection(self, worker):
        selected = []
        lock = threading.Lock()
        all_selected = threading.Event()
        unblock = threading.Event()

        def slow_preflight(worker_id, mission):
            # The actual process function performs slow readiness/quota reads
            # before claim. Keep every row queued until all workers selected.
            with lock:
                selected.append((worker_id, mission["id"], mission["analysisContext"]["roleId"]))
                if len(selected) == 3:
                    all_selected.set()
            unblock.wait(10)

        threads = [threading.Thread(target=worker, args=(f"test-{i}",)) for i in range(3)]
        with mock.patch.object(self.b, "process_auto_mission", side_effect=slow_preflight):
            try:
                for thread in threads:
                    thread.start()
                self.assertTrue(all_selected.wait(10), "three workers did not reach preflight")
                return list(selected)
            finally:
                self.b.MISSION_WORKER_STOP.set()
                unblock.set()
                self.b.MISSION_WORKER_WAKE.set()
                for thread in threads:
                    thread.join(10)
                self.assertFalse(any(thread.is_alive() for thread in threads))

    def test_baseline_reproduces_three_workers_selecting_same_technical_vote(self):
        tree = ast.parse(BASELINE.read_text(encoding="utf-8"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "ai_trade_council_worker_loop")
        self.assertIn("find_next_auto_mission(council_only=True)", ast.unparse(function))
        function.name = "baseline_worker_loop"
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<baseline-worker>", "exec"), self.b.__dict__)
        selected = self._concurrent_preclaim_selection(self.b.baseline_worker_loop)
        self.assertEqual(len({row[1] for row in selected}), 1)
        self.assertEqual({row[2] for row in selected}, {"technical"})

    def test_three_actual_workers_reserve_three_roles_before_any_claim(self):
        selected = self._concurrent_preclaim_selection(self.b.ai_trade_council_worker_loop)
        self.assertEqual(len({row[1] for row in selected}), 3)
        self.assertEqual({row[2] for row in selected}, {"technical", "price_action", "news"})
        self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS, {})
        self.f.runner.assert_not_called()
        self.f.dispatch.assert_not_called()
        for child in self.children:
            stored = self.b.find_mission(child["id"])
            self.assertEqual(stored["status"], "queued")
            self.assertEqual(stored["attemptCount"], 0)

    def test_reservation_has_no_quota_lease_or_store_side_effect_and_mixed_finder_skips_it(self):
        before = copy.deepcopy(self.b.load_missions())
        with (mock.patch.object(self.b, "codex_rate_limits") as quota,
              mock.patch.object(self.b, "check_rate_limit") as budget,
              mock.patch.object(self.b, "claim_auto_mission") as claim):
            mission = self.b._reserve_next_ai_trade_council_mission("owner")
            self.assertIsNotNone(mission)
            next_mission = self.b.find_next_auto_mission()
            self.assertNotEqual(next_mission["id"], mission["id"])
        quota.assert_not_called()
        budget.assert_not_called()
        claim.assert_not_called()
        self.assertEqual(self.b.load_missions(), before)

    def test_bound_and_release_only_by_owning_worker(self):
        reserved = [self.b._reserve_next_ai_trade_council_mission(f"w{i}") for i in range(3)]
        self.assertEqual(len({row["id"] for row in reserved}), 3)
        self.assertIsNone(self.b._reserve_next_ai_trade_council_mission("fourth"))
        first = reserved[0]["id"]
        self.b._release_ai_trade_council_dispatch_reservation(first, "wrong-owner")
        self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS[first], "w0")
        self.assertIsNone(self.b._reserve_next_ai_trade_council_mission("fourth"))
        self.b._release_ai_trade_council_dispatch_reservation(first, "w0")
        self.assertEqual(self.b._reserve_next_ai_trade_council_mission("replacement")["id"], first)
        self.b._release_ai_trade_council_dispatch_reservation(first, "w0")
        self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS[first], "replacement")

    def test_stop_after_reservation_releases_without_process(self):
        original = self.b._reserve_next_ai_trade_council_mission

        def stopping(worker_id):
            result = original(worker_id)
            self.b.MISSION_WORKER_STOP.set()
            return result

        with (mock.patch.object(self.b, "_reserve_next_ai_trade_council_mission", side_effect=stopping),
              mock.patch.object(self.b, "process_auto_mission") as process):
            self.b.ai_trade_council_worker_loop("stopping")
        process.assert_not_called()
        self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS, {})

    def test_failed_process_always_releases_owned_reservation(self):
        for exception in (RuntimeError("test"), self.b.DataIntegrityError("test")):
            with self.subTest(exception=type(exception).__name__):
                self.b.MISSION_WORKER_STOP.clear()

                def fail(worker_id, mission):
                    self.b.MISSION_WORKER_STOP.set()
                    raise exception

                with mock.patch.object(self.b, "process_auto_mission", side_effect=fail):
                    self.b.ai_trade_council_worker_loop("failure")
                self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS, {})

    def test_cancellation_after_reservation_cannot_claim_or_launch(self):
        def cancelled_before_claim(worker_id, mission):
            latest = self.b.find_mission(mission["id"])
            latest["status"] = "cancelled"
            self.b.replace_mission(latest)
            self.assertIsNone(self.b.claim_auto_mission(mission["id"], worker_id))
            self.b.MISSION_WORKER_STOP.set()

        with mock.patch.object(self.b, "process_auto_mission", side_effect=cancelled_before_claim):
            self.b.ai_trade_council_worker_loop("cancel-race")
        self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS, {})
        self.f.runner.assert_not_called()
        self.f.dispatch.assert_not_called()

    def test_successful_claim_still_rejects_second_claim(self):
        mission = self.b._reserve_next_ai_trade_council_mission("owner")
        claimed = self.b.claim_auto_mission(mission["id"], "owner")
        self.assertEqual(claimed["status"], "running")
        self.assertIsNone(self.b.claim_auto_mission(mission["id"], "other"))
        self.b._release_ai_trade_council_dispatch_reservation(mission["id"], "owner")
        self.assertNotEqual(self.b._reserve_next_ai_trade_council_mission("other")["id"], mission["id"])
        self.f.runner.assert_not_called()
        self.f.dispatch.assert_not_called()

    def test_stopping_pool_does_not_reserve(self):
        self.b.MISSION_WORKER_STOP.set()
        with mock.patch.object(self.b, "_find_next_auto_mission_unlocked") as finder:
            self.assertIsNone(self.b._reserve_next_ai_trade_council_mission("stopped"))
        finder.assert_not_called()
        self.assertEqual(self.b.AI_TRADE_COUNCIL_DISPATCH_RESERVATIONS, {})


if __name__ == "__main__":
    unittest.main()
