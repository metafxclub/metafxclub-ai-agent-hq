"""Bounded HTTP reads retain complete validation without blocking commands."""
import copy
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from unittest import mock

from test_ea_factory_followup_hardening import load_bridge


class BoundedFactoryHttpReadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = load_bridge()
        cls.production_http_wait = cls.bridge.EA_FACTORY_HTTP_READ_WAIT_SECONDS

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.b = self.bridge
        self.patch("EA_FACTORY_HTTP_READ_INFLIGHT", new=None)
        self.patch("EA_FACTORY_HTTP_READ_WAIT_SECONDS", new=0.06)
        self.patch("EA_FACTORY_READ_MODEL_CACHE", new={
            "signature": None, "value": None, "refreshing": False, "generation": 0,
        })
        self.patch("EA_FACTORY_STATE_CACHE", new={"signature": None, "value": None})
        self.patch("_ea_factory_state_validation_signature", return_value=("unchanged",))

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(self.b, name, **kwargs))

    def deferred(self, result):
        self.assertEqual(result["_httpStatus"], 202)
        self.assertEqual(result["kind"], "ea_factory_refresh_deferred")
        self.assertFalse(result["readinessConfirmed"])
        self.assertNotIn("eaFactory", result)
        self.assertNotIn("builds", result)

    def volatile_inputs(self):
        self.patch("peek_metatrader_status", return_value={})
        self.patch("_metatrader_selection_read_model", return_value={})
        self.patch("_ea_factory_terminal_gate", return_value={})
        self.patch("research_sheet_hub_read_model", return_value={})
        self.patch("_ea_factory_front_office_supported_platforms", return_value=())
        self.patch("load_missions", return_value=[])

    def test_many_http_polls_share_one_slow_check_and_return_bounded_deferred(self):
        entered, release = threading.Event(), threading.Event()

        def slow_read(**kwargs):
            self.assertTrue(kwargs["http_read"])
            entered.set()
            if not release.wait(3):
                raise AssertionError("test did not release read")
            return {"schemaVersion": "ea-factory-v1", "builds": []}

        model = self.patch("ea_factory_read_model", side_effect=slow_read)
        try:
            start = time.monotonic()
            with ThreadPoolExecutor(max_workers=8) as pool:
                responses = list(pool.map(lambda _: self.b.ea_factory_read_result(), range(8)))
            self.assertLess(time.monotonic() - start, 1.0)
            self.assertTrue(entered.is_set())
            for result in responses:
                self.deferred(result)
            self.assertEqual(model.call_count, 1)
        finally:
            release.set()
            self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(2))

    def test_fast_http_result_checks_fresh_signature_again_on_next_poll(self):
        model = self.patch("ea_factory_read_model", side_effect=[
            {"schemaVersion": "ea-factory-v1", "revision": 1},
            {"schemaVersion": "ea-factory-v1", "revision": 2},
        ])
        first = self.b.ea_factory_read_result()
        second = self.b.ea_factory_read_result()
        self.assertEqual(first["eaFactory"]["revision"], 1)
        self.assertEqual(second["eaFactory"]["revision"], 2)
        self.assertEqual(model.call_args_list, [mock.call(http_read=True)] * 2)

    def test_warm_check_past_old_two_second_deadline_is_delivered_fresh(self):
        self.patch("EA_FACTORY_HTTP_READ_WAIT_SECONDS", new=self.production_http_wait)
        self.assertEqual(self.production_http_wait, 4.0)
        release = threading.Event()

        def contended_warm_read(**_kwargs):
            # Reproduce the measured warm-cache delay while other UI polls run.
            release.wait(2.25)
            return self.status_model()

        model = self.patch("ea_factory_read_model", side_effect=contended_warm_read)
        try:
            started = time.monotonic()
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: self.b.ea_factory_read_result(), range(4)))
            self.assertGreater(time.monotonic() - started, 2.0)
            self.assertLess(time.monotonic() - started, self.production_http_wait)
            self.assertEqual(model.call_count, 1)
            for result in results:
                self.assertFalse(result["eaFactory"]["snapshotStale"])
                self.assertTrue(result["eaFactory"]["oneClick"]["canRun"])
                self.assertNotIn("_httpStatus", result)
            self.assertIsNone(self.b.EA_FACTORY_STATE_CACHE["value"])
        finally:
            release.set()
            self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))

    def test_production_cold_read_still_returns_bounded_deferred(self):
        self.patch("EA_FACTORY_HTTP_READ_WAIT_SECONDS", new=self.production_http_wait)
        release = threading.Event()

        def cold_read(**_kwargs):
            if not release.wait(6):
                raise AssertionError("test did not release cold projection")
            return self.status_model()

        self.patch("ea_factory_read_model", side_effect=cold_read)
        try:
            started = time.monotonic()
            self.deferred(self.b.ea_factory_read_result())
            elapsed = time.monotonic() - started
            self.assertGreaterEqual(elapsed, self.production_http_wait - 0.1)
            self.assertLess(elapsed, self.production_http_wait + 1.0)
            self.assertFalse(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].is_set())
            self.assertIsNone(self.b.EA_FACTORY_STATE_CACHE["value"])
        finally:
            release.set()
            self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))

    def status_model(self, revision=1):
        return {
            "schemaVersion": "ea-factory-v1", "snapshotStale": False, "revision": revision,
            "oneClick": {"enabled": True, "canRun": True, "canCreateAndRun": True},
            "sourceCatalog": {"googleSheets": {"canSync": True}},
            "terminalSelection": {"terminalExecutionAllowed": True},
            "builds": [{
                "id": "ea-build-same", "status": "awaiting_visible_terminal",
                "oneClickRun": {"canCancel": True, "canResume": True, "canRetry": True,
                                "canResumeCancelled": True, "canRestartBacktest": True,
                                "attemptCount": 3, "missionId": "mission-original"},
                "stages": [{"id": "compile", "canAdvance": True, "canRetry": True,
                            "status": "blocked", "reportId": "report-original"}],
                "sourceRecovery": {"eligible": True, "history": [{"id": "recovery-original"}]},
                "admission": {"canSubmit": True, "allowed": True, "available": True,
                              "commandsAllowed": True, "retryAvailable": True},
            }],
        }

    def completed_task(self, *, result=None, error=None, age=0, generation=0):
        done = threading.Event()
        done.set()
        task = {"done": done, "result": result, "error": error,
                "generation": generation, "completedAt": time.monotonic() - age,
                "fallback": None}
        self.b.EA_FACTORY_HTTP_READ_INFLIGHT = task
        return task

    def test_completed_slow_check_is_harvested_as_status_only_while_fresh_check_runs(self):
        first_release, second_release = threading.Event(), threading.Event()
        original = self.status_model()
        count = 0

        def slow_read(**_kwargs):
            nonlocal count
            count += 1
            release = first_release if count == 1 else second_release
            if not release.wait(3):
                raise AssertionError("test did not release read")
            return original if count == 1 else self.status_model(2)

        model = self.patch("ea_factory_read_model", side_effect=slow_read)
        try:
            self.deferred(self.b.ea_factory_read_result())
            first_release.set()
            self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))
            first_completed_at = self.b.EA_FACTORY_HTTP_READ_INFLIGHT["completedAt"]
            result = self.b.ea_factory_read_result()
            stale = result["eaFactory"]
            self.assertTrue(stale["snapshotStale"])
            self.assertFalse(result["readinessConfirmed"])
            self.assertNotIn("_httpStatus", result)
            self.assertEqual(stale["revision"], 1)
            self.assertEqual(stale["builds"][0]["oneClickRun"]["attemptCount"], 3)
            self.assertEqual(stale["builds"][0]["oneClickRun"]["missionId"], "mission-original")
            self.assertEqual(stale["builds"][0]["stages"][0]["reportId"], "report-original")
            self.assertEqual(stale["builds"][0]["sourceRecovery"]["history"], [{"id": "recovery-original"}])
            for flag in ("enabled", "canRun", "canCreateAndRun", "commandsAllowed"):
                self.assertFalse(stale["oneClick"][flag])
            for flag in ("canCancel", "canResume", "canRetry", "canResumeCancelled", "canRestartBacktest"):
                self.assertFalse(stale["builds"][0]["oneClickRun"][flag])
            self.assertFalse(stale["builds"][0]["stages"][0]["canAdvance"])
            self.assertFalse(stale["builds"][0]["sourceRecovery"]["eligible"])
            self.assertTrue(all(value is False for value in stale["builds"][0]["admission"].values()))
            self.assertFalse(stale["sourceCatalog"]["googleSheets"]["canSync"])
            self.assertFalse(stale["terminalSelection"]["terminalExecutionAllowed"])
            self.assertEqual(original, self.status_model(), "display fallback must not alter checked evidence")
            stale["builds"].clear()
            again = self.b.ea_factory_read_result()
            self.assertEqual(len(again["eaFactory"]["builds"]), 1)
            self.assertEqual(model.call_count, 2, "polls must still share the fresh worker")
            self.assertEqual(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["fallback"]["completedAt"], first_completed_at)
            self.assertIsNone(self.b.EA_FACTORY_STATE_CACHE["value"])
            self.assertIsNone(self.b.EA_FACTORY_READ_MODEL_CACHE["value"])
        finally:
            first_release.set()
            second_release.set()
            self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))

    def test_completed_old_snapshot_expires_without_renewal_during_refresh(self):
        original = self.completed_task(result={"ok": True, "eaFactory": self.status_model()})
        release = threading.Event()
        self.patch("ea_factory_read_model", side_effect=lambda **_kwargs: (
            release.wait(3) and self.status_model(2)))
        try:
            self.assertTrue(self.b.ea_factory_read_result()["eaFactory"]["snapshotStale"])
            task = self.b.EA_FACTORY_HTTP_READ_INFLIGHT
            self.assertEqual(task["fallback"]["completedAt"], original["completedAt"])
            task["fallback"]["completedAt"] -= self.b.EA_FACTORY_HTTP_STATUS_SNAPSHOT_MAX_AGE_SECONDS + 1
            self.deferred(self.b.ea_factory_read_result())
        finally:
            release.set()
            self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))

    def test_changed_generation_discards_status_fallback_while_check_is_running(self):
        self.completed_task(result={"ok": True, "eaFactory": self.status_model()})
        release = threading.Event()
        self.patch("ea_factory_read_model", side_effect=lambda **_kwargs: (
            release.wait(3) and self.status_model(2)))
        try:
            self.assertTrue(self.b.ea_factory_read_result()["eaFactory"]["snapshotStale"])
            self.b._invalidate_ea_factory_read_model_cache()
            self.deferred(self.b.ea_factory_read_result())
        finally:
            release.set()
            self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))

    def test_ineligible_completed_results_do_not_revive_an_older_fallback(self):
        cases = [
            {"result": {"ok": True, "eaFactory": self.status_model()}, "age": 31},
            {"result": {"ok": True, "eaFactory": self.status_model()}, "generation": -1},
            {"result": {"ok": True, "eaFactory": dict(self.status_model(), snapshotStale=True)}},
            {"result": self.b._ea_factory_deferred_read_result()},
            {"result": {"ok": False, "_httpStatus": 409}},
            {"error": OSError("unavailable")},
        ]
        for options in cases:
            with self.subTest(options=options):
                previous = self.completed_task(**options)
                previous["fallback"] = {"result": {"ok": True, "eaFactory": self.status_model()},
                                        "completedAt": time.monotonic(), "generation": 0}
                release = threading.Event()
                with mock.patch.object(self.b, "ea_factory_read_model", side_effect=lambda **_kwargs: (
                        release.wait(3) and self.status_model(2))):
                    try:
                        self.deferred(self.b.ea_factory_read_result())
                        self.assertIsNone(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["fallback"])
                    finally:
                        release.set()
                        self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))

    def test_latest_error_or_instability_overrides_and_discards_status_fallback(self):
        for failure in (self.b.DataIntegrityError("changed Source"),
                        self.b._EAFactoryReadDeferred(), OSError("read unavailable")):
            with self.subTest(failure=type(failure).__name__):
                self.completed_task(result={"ok": True, "eaFactory": self.status_model()})
                release = threading.Event()

                def failing_read(**_kwargs):
                    if not release.wait(3):
                        raise AssertionError("test did not release read")
                    raise failure

                with mock.patch.object(self.b, "ea_factory_read_model", side_effect=failing_read):
                    try:
                        self.assertTrue(self.b.ea_factory_read_result()["eaFactory"]["snapshotStale"])
                        with ThreadPoolExecutor(max_workers=1) as pool:
                            pending = pool.submit(self.b.ea_factory_read_result)
                            release.set()
                            if isinstance(failure, OSError):
                                with self.assertRaises(OSError):
                                    pending.result(1)
                            else:
                                result = pending.result(1)
                                if isinstance(failure, self.b.DataIntegrityError):
                                    self.assertEqual(result["_httpStatus"], 409)
                                    self.assertNotIn("eaFactory", result)
                                else:
                                    self.deferred(result)
                        self.assertIsNone(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["fallback"])
                    finally:
                        release.set()
                        self.assertTrue(self.b.EA_FACTORY_HTTP_READ_INFLIGHT["done"].wait(1))

    def test_next_fast_fresh_check_restores_normal_verified_model(self):
        self.completed_task(result={"ok": True, "eaFactory": self.status_model()})
        self.patch("ea_factory_read_model", return_value=self.status_model(2))
        result = self.b.ea_factory_read_result()
        self.assertEqual(result["eaFactory"]["revision"], 2)
        self.assertFalse(result["eaFactory"]["snapshotStale"])
        self.assertTrue(result["eaFactory"]["oneClick"]["canRun"])
        self.assertNotIn("readinessConfirmed", result)

    def test_http_mutation_invalidation_never_publishes_completed_old_snapshot(self):
        def invalidated_read(**_kwargs):
            self.b._invalidate_ea_factory_read_model_cache()
            return {"schemaVersion": "ea-factory-v1", "oneClick": {"canRun": True}}

        self.patch("ea_factory_read_model", side_effect=invalidated_read)
        self.deferred(self.b.ea_factory_read_result())

    def test_http_integrity_failure_is_blocked_and_next_read_can_recover(self):
        self.patch("ea_factory_read_model", side_effect=[
            self.b.DataIntegrityError("changed Source"),
            {"schemaVersion": "ea-factory-v1", "builds": []},
        ])
        blocked = self.b.ea_factory_read_result()
        self.assertEqual(blocked["_httpStatus"], 409)
        self.assertEqual(blocked["code"], "ea_factory_artifact_integrity_failed")
        self.assertFalse(blocked["oneClick"]["commandsAllowed"])
        self.assertNotIn("eaFactory", blocked)
        self.assertTrue(self.b.ea_factory_read_result()["ok"])

    def test_unexpected_background_failure_is_propagated_without_stuck_single_flight(self):
        self.patch("ea_factory_read_model", side_effect=[
            OSError("read unavailable"), {"schemaVersion": "ea-factory-v1"},
        ])
        with self.assertRaisesRegex(OSError, "read unavailable"):
            self.b.ea_factory_read_result()
        self.assertTrue(self.b.ea_factory_read_result()["ok"])

    def test_cold_projection_validates_all_builds_without_holding_command_locks(self):
        entered, release = threading.Event(), threading.Event()
        state = {"builds": [{"id": f"ea-build-{index}"} for index in range(30)]}
        result, errors = [], []

        def validate():
            entered.set()
            if not release.wait(3):
                raise AssertionError("test did not release validation")
            return copy.deepcopy(state)

        validator = self.patch("_load_ea_factory_state_uncached", side_effect=validate)
        writer = self.patch("_write_ea_factory_state_unlocked", side_effect=AssertionError("GET cannot write"))

        def read():
            try:
                result.append(self.b._ea_factory_projection_state())
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=read)
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            for lock in (self.b.EA_FACTORY_LOCK, self.b.EA_FACTORY_STATE_CACHE_LOCK):
                acquired = lock.acquire(timeout=0.1)
                self.assertTrue(acquired, "read validation must not block command locks")
                if acquired:
                    lock.release()
        finally:
            release.set()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result, [state])
        validator.assert_called_once_with()
        writer.assert_not_called()
        self.assertIsNone(self.b.EA_FACTORY_STATE_CACHE["value"])

    def test_busy_command_cache_lock_does_not_queue_projection(self):
        state = {"builds": []}
        self.patch("_load_ea_factory_state_uncached", return_value=state)
        result = []
        with self.b.EA_FACTORY_STATE_CACHE_LOCK:
            reader = threading.Thread(target=lambda: result.append(self.b._ea_factory_projection_state()))
            reader.start()
            reader.join(0.5)
            self.assertFalse(reader.is_alive())
        reader.join(1)
        self.assertEqual(result, [state])

    def test_validated_cache_is_copied_and_recovery_missions_are_rechecked(self):
        state = {"builds": [{"id": "ea-build-recovered", "sourceRecoveryHistory": [{"receipt": "bound"}]}]}
        self.b.EA_FACTORY_STATE_CACHE.update(signature=("unchanged",), value=state)
        validator = self.patch("_load_ea_factory_state_uncached", side_effect=AssertionError("cached state was already checked"))
        recovery = self.patch("_ea_factory_revalidated_source_recovery", return_value=[])
        result = self.b._ea_factory_projection_state()
        recovery.assert_called_once_with(state["builds"][0])
        result["builds"][0]["id"] = "mutated"
        self.assertEqual(state["builds"][0]["id"], "ea-build-recovered")
        validator.assert_not_called()

    def test_changed_dependencies_during_validation_defer_without_cache_publication(self):
        self.patch("_ea_factory_state_validation_signature", side_effect=[("before",), ("after",)])
        self.patch("_load_ea_factory_state_uncached", return_value={"builds": [{"id": "mixed"}]})
        with self.assertRaises(self.b._EAFactoryReadDeferred):
            self.b._ea_factory_projection_state()
        self.assertIsNone(self.b.EA_FACTORY_STATE_CACHE["value"])

    def test_stable_integrity_failure_is_not_downgraded_to_deferred(self):
        self.patch("_load_ea_factory_state_uncached", side_effect=self.b.DataIntegrityError("tampered Source"))
        with self.assertRaises(self.b.DataIntegrityError):
            self.b._ea_factory_projection_state()

    def test_integrity_error_during_concurrent_mutation_defers_for_fresh_validation(self):
        self.patch("_ea_factory_state_validation_signature", side_effect=[("before",), ("after",)])
        self.patch("_load_ea_factory_state_uncached", side_effect=self.b.DataIntegrityError("receipt changing"))
        with self.assertRaises(self.b._EAFactoryReadDeferred):
            self.b._ea_factory_projection_state()

    def test_http_model_never_returns_authority_when_both_full_signatures_change(self):
        self.volatile_inputs()
        self.patch("_ea_factory_read_model_signature", side_effect=[("a",), ("b",), ("c",), ("d",)])
        projection = self.patch("_ea_factory_read_model_uncached", return_value={
            "schemaVersion": "ea-factory-v1", "oneClick": {"canRun": True},
        })
        result = self.b.ea_factory_read_result()
        self.deferred(result)
        self.assertEqual(projection.call_count, 2)
        self.assertTrue(all(call.kwargs["projection_only"] for call in projection.call_args_list))
        self.assertIsNone(self.b.EA_FACTORY_READ_MODEL_CACHE["value"])
        self.assertFalse(self.b.EA_FACTORY_READ_MODEL_CACHE["refreshing"])

    def test_terminal_recovery_mission_full_snapshot_change_invalidates_warm_get(self):
        self.volatile_inputs()
        mission = {"id": "mission-eaf-recovery-proof", "status": "completed", "toolId": "manager_mission",
                   "targetId": "right_server_racks", "reportType": "ea_build_report", "attemptCount": 0,
                   "updatedAt": "2026-10-18T00:00:00Z"}
        self.patch("load_missions", side_effect=lambda **_kwargs: [copy.deepcopy(mission)])
        self.patch("_ea_factory_read_model_signature", side_effect=lambda *_args, missions=None:
                   self.b._ea_factory_mission_projection_signature(missions))

        def verified_projection(**_kwargs):
            if mission["attemptCount"] != 0:
                raise self.b.DataIntegrityError("recovery Mission no longer matches receipt")
            return {"schemaVersion": "ea-factory-v1", "builds": []}

        projection = self.patch("_ea_factory_read_model_uncached", side_effect=verified_projection)
        self.assertTrue(self.b._ea_factory_checked_read_result()["ok"])
        self.assertTrue(self.b._ea_factory_checked_read_result()["ok"])
        self.assertEqual(projection.call_count, 1)
        mission["attemptCount"] = 1
        result = self.b._ea_factory_checked_read_result()
        self.assertEqual(result["_httpStatus"], 409)
        self.assertFalse(result["oneClick"]["commandsAllowed"])
        self.assertEqual(projection.call_count, 2)

    def test_full_terminal_signature_preserves_active_heartbeat_cache_reuse(self):
        for status in ("failed", "blocked", "completed", "archived"):
            mission = {"id": "mission-old-factory", "status": status, "targetId": "right_server_racks",
                       "reportType": "ea_build_report", "title": "original", "updatedAt": "2026-10-18T00:00:00Z"}
            before = self.b._ea_factory_mission_projection_signature([mission])
            mission["title"] = "changed terminal evidence"
            with self.subTest(status=status):
                self.assertNotEqual(before, self.b._ea_factory_mission_projection_signature([mission]))
        active = {"id": "mission-active", "status": "running", "targetId": "right_server_racks",
                  "reportType": "ea_build_report", "updatedAt": "first", "execution": {"heartbeatAt": "first"}}
        before = self.b._ea_factory_mission_projection_signature([active])
        active["updatedAt"] = "second"
        active["execution"]["heartbeatAt"] = "second"
        self.assertEqual(before, self.b._ea_factory_mission_projection_signature([active]))

    def test_mission_prefilter_preserves_projection_without_copying_unrelated_contexts(self):
        factory = {"id": "factory", "targetId": "right_server_racks", "reportType": "ea_build_report",
                   "status": "completed", "workflowContext": {"actionId": "generate_source"},
                   "attemptCount": 3, "recoveryEvidence": {"unchanged": True}}
        research = {"id": "research", "targetId": "left_server_racks",
                    "reportType": "trading_system_research_report",
                    "workflowContext": {"actionId": "deep_research_system"}}
        wrong_action = {**research, "id": "unrelated-research", "workflowContext": {"actionId": "other"}}
        unrelated = [
            {"id": f"unrelated-{index}", "targetId": target, "reportType": report,
             "workflowContext": {"actionId": "deep_research_system", "detail": "not Factory evidence"}}
            for index, (target, report) in enumerate([
                ("manager", "ea_build_report"), ("right_server_racks", "mission_report"),
                ("left_server_racks", "ea_build_report"), (None, "trading_system_research_report"),
            ])
        ]
        expected = self.b._ea_factory_mission_projection_signature([factory, research])
        context = self.patch("_workflow_context_storage", wraps=self.b._workflow_context_storage)
        actual = self.b._ea_factory_mission_projection_signature([None, *unrelated, factory, wrong_action, research])
        self.assertEqual(actual, expected)
        self.assertEqual(context.call_args_list, [
            mock.call(factory["workflowContext"]), mock.call(wrong_action["workflowContext"]),
            mock.call(research["workflowContext"]),
        ])
        factory["recoveryEvidence"]["unchanged"] = False
        self.assertNotEqual(expected, self.b._ea_factory_mission_projection_signature([factory, research]))


if __name__ == "__main__":
    unittest.main()
