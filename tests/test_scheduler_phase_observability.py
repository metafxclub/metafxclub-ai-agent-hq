from __future__ import annotations

import copy
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


BRIDGE_PATH = Path(__file__).resolve().parents[1] / "backend" / "local-runner" / "bridge_server.py"


class SchedulerPhaseObservabilityTests(unittest.TestCase):
    """Pure fake-clock diagnostics: no threads, providers, Sheet writes or runtime files."""

    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("metafx_scheduler_phase_test", BRIDGE_PATH)
        assert spec is not None and spec.loader is not None
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)
        cls.initial_runtime = copy.deepcopy(cls.bridge.DASHBOARD_WORKFLOW_SCHEDULER_RUNTIME)

    def setUp(self) -> None:
        self.clock = 100.0
        self.wall = self.bridge.utc_now()
        self.stop = mock.Mock()
        self.stop.is_set.return_value = False
        self.wake = mock.Mock()
        self.thread = mock.Mock()
        self.thread.is_alive.return_value = True
        patches = [
            mock.patch.dict(self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_RUNTIME, self.initial_runtime, clear=True),
            mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SCHEDULER_PHASE_STARTED_MONOTONIC", None),
            mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SCHEDULER_STOP", self.stop),
            mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SCHEDULER_WAKE", self.wake),
            mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SCHEDULER_THREAD", self.thread),
            mock.patch.object(self.bridge, "FX_TREND_THREAD", None),
            mock.patch.object(self.bridge.time, "monotonic", side_effect=lambda: self.clock),
            mock.patch.object(self.bridge, "utc_now", side_effect=lambda: self.wall),
            mock.patch.object(self.bridge, "append_audit"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def _state(self) -> dict:
        return self.bridge.dashboard_workflow_scheduler_read_model()

    def _stop_after_wait(self, timeout: float) -> None:
        self.assertEqual(timeout, self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_POLL_SECONDS)
        self.assertEqual(self._state()["phase"], "waiting")
        self.stop.is_set.return_value = True

    def test_phase_elapsed_uses_monotonic_without_updating_heartbeat_or_success(self) -> None:
        heartbeat = self.wall
        self.bridge._dashboard_workflow_scheduler_runtime_update(
            status="running", lastHeartbeatAt=heartbeat, lastSuccessAt=heartbeat,
        )
        self.bridge._dashboard_workflow_scheduler_runtime_update(phase="sheet_flush")
        self.clock += 17.25
        self.wall = "2000-01-01T00:00:00Z"  # Wall-clock correction cannot reset duration.
        state = self._state()
        self.assertEqual(state["phaseStartedAt"], heartbeat)
        self.assertEqual(state["phaseElapsedSeconds"], 17.2)
        self.assertEqual(state["lastHeartbeatAt"], heartbeat)
        self.assertEqual(state["lastSuccessAt"], heartbeat)
        self.assertNotIn("phaseStartedMonotonic", state)
        self.bridge._dashboard_workflow_scheduler_runtime_update(phase="sheet_backfill")
        self.clock += 2
        state = self._state()
        self.assertEqual(state["phaseStartedAt"], self.wall)
        self.assertEqual(state["phaseElapsedSeconds"], 2.0)
        self.assertEqual(state["lastHeartbeatAt"], heartbeat)

    def test_inflight_phase_does_not_mask_stale_heartbeat(self) -> None:
        now = datetime.now(timezone.utc)
        heartbeat = (now - timedelta(seconds=196)).isoformat()
        self.bridge._dashboard_workflow_scheduler_runtime_update(
            status="running", lastHeartbeatAt=heartbeat, phase="sheet_flush",
        )
        self.clock += 196
        state = self.bridge._dashboard_workflow_scheduler_operational_state(now_utc=now)
        self.assertTrue(state["alive"])
        self.assertFalse(state["operational"])
        self.assertEqual(state["operationalReason"], "heartbeat_stale")
        self.assertEqual(state["maxHeartbeatAgeSeconds"], 120)
        self.assertEqual(state["runtime"]["phaseElapsedSeconds"], 196.0)
        self.assertEqual(state["runtime"]["lastHeartbeatAt"], heartbeat)

    def test_existing_loop_exposes_each_inflight_phase_and_preserves_call_order(self) -> None:
        observed = []

        def capture(phase: str) -> None:
            state = self._state()
            self.assertEqual(state["phase"], phase)
            self.assertEqual(state["phaseElapsedSeconds"], 0.0)
            heartbeat = state["lastHeartbeatAt"]
            self.clock += 4.5
            observed.append(phase)
            state = self._state()
            self.assertEqual(state["phaseElapsedSeconds"], 4.5)
            self.assertEqual(state["lastHeartbeatAt"], heartbeat)

        def tick(*, refresh_quota: bool) -> dict:
            self.assertTrue(refresh_quota)
            capture("scheduler_tick")
            return {"ok": True, "kind": "scheduler_idle"}

        def flush(*, max_items: int) -> None:
            self.assertEqual(max_items, 20)
            capture("sheet_flush")

        def wait(timeout: float) -> None:
            capture("waiting")
            self._stop_after_wait(timeout)

        self.wake.wait.side_effect = wait
        with (
            mock.patch.object(self.bridge, "RESEARCH_SHEET_AUTO_SYNC_ENABLED", True),
            mock.patch.object(self.bridge, "dashboard_workflow_scheduler_tick", side_effect=tick) as tick_mock,
            mock.patch.object(self.bridge, "_flush_research_sheet_outbox", side_effect=flush) as flush_mock,
            mock.patch.object(self.bridge, "_research_sheet_backfill_recent_reports", side_effect=lambda: capture("sheet_backfill")) as backfill_mock,
        ):
            self.bridge.dashboard_workflow_scheduler_loop()
        self.assertEqual(observed, ["scheduler_tick", "sheet_flush", "sheet_backfill", "waiting"])
        tick_mock.assert_called_once_with(refresh_quota=True)
        flush_mock.assert_called_once_with(max_items=20)
        backfill_mock.assert_called_once_with()
        self.wake.clear.assert_called_once_with()
        self.clock += 500
        state = self._state()
        self.assertEqual((state["status"], state["phase"], state["phaseElapsedSeconds"]), ("stopped", "stopped", 0.0))

    def test_handled_exceptions_advance_to_waiting_then_stopped(self) -> None:
        cases = [
            ("scheduler_tick", RuntimeError("tick fixture"), "scheduler_exception"),
            ("scheduler_tick", self.bridge.DataIntegrityError("fixture"), "data_integrity_error"),
            ("sheet_flush", RuntimeError("flush fixture"), "scheduler_idle"),
            ("sheet_backfill", RuntimeError("backfill fixture"), "scheduler_idle"),
        ]
        for failed_phase, error, expected_kind in cases:
            with self.subTest(phase=failed_phase, error=type(error).__name__):
                self.stop.is_set.return_value = False
                self.wake.wait.side_effect = self._stop_after_wait

                def operation(phase: str):
                    self.assertEqual(self._state()["phase"], phase)
                    if phase == failed_phase:
                        raise error
                    return {"ok": True, "kind": "scheduler_idle"}

                with (
                    mock.patch.object(self.bridge, "RESEARCH_SHEET_AUTO_SYNC_ENABLED", True),
                    mock.patch.object(self.bridge, "dashboard_workflow_scheduler_tick", side_effect=lambda **_: operation("scheduler_tick")),
                    mock.patch.object(self.bridge, "_flush_research_sheet_outbox", side_effect=lambda **_: operation("sheet_flush")),
                    mock.patch.object(self.bridge, "_research_sheet_backfill_recent_reports", side_effect=lambda: operation("sheet_backfill")),
                ):
                    self.bridge.dashboard_workflow_scheduler_loop()
                state = self._state()
                self.assertEqual(state["phase"], "stopped")
                self.assertEqual(state["phaseElapsedSeconds"], 0.0)
                self.assertEqual(state["lastTickKind"], expected_kind)

    def test_stop_keeps_inflight_phase_until_thread_has_stopped(self) -> None:
        self.bridge._dashboard_workflow_scheduler_runtime_update(status="running", phase="sheet_flush")
        self.clock += 8
        self.bridge.stop_dashboard_workflow_scheduler()
        self.thread.join.assert_called_once_with(timeout=15)
        state = self._state()
        self.assertEqual(state["status"], "stopping")
        self.assertEqual(state["phase"], "sheet_flush")
        self.assertEqual(state["phaseElapsedSeconds"], 8.0)
        self.thread.is_alive.return_value = False
        self.bridge.stop_dashboard_workflow_scheduler()
        self.clock += 50
        state = self._state()
        self.assertEqual((state["status"], state["phase"], state["phaseElapsedSeconds"]), ("stopped", "stopped", 0.0))
        self.assertFalse(state["operational"])

    def test_capability_matches_flag_without_loading_or_authorizing_configuration(self) -> None:
        for enabled in (False, True):
            with (
                self.subTest(enabled=enabled),
                mock.patch.object(self.bridge, "RESEARCH_SHEET_AUTO_SYNC_ENABLED", enabled),
                mock.patch.object(self.bridge, "_flush_research_sheet_outbox") as flush,
                mock.patch.object(self.bridge, "_research_sheet_backfill_recent_reports") as backfill,
            ):
                state = self._state()
                self.assertEqual(state["externalWrites"], enabled)
                self.assertEqual(state["googleSheetExternalWritesEnabled"], enabled)
                self.assertEqual(state["externalWriteScopes"], ["google_sheets"] if enabled else [])
                self.assertTrue(state["googleSheetExternalWritesRequireActiveConfiguration"])
                self.assertFalse(state["otherExternalWrites"])
                self.assertFalse(state["metaTraderActions"])
                flush.assert_not_called()
                backfill.assert_not_called()

    def test_disabled_sheet_capability_does_not_add_maintenance_calls(self) -> None:
        self.wake.wait.side_effect = self._stop_after_wait
        with (
            mock.patch.object(self.bridge, "RESEARCH_SHEET_AUTO_SYNC_ENABLED", False),
            mock.patch.object(self.bridge, "dashboard_workflow_scheduler_tick", return_value={"ok": True, "kind": "scheduler_idle"}) as tick,
            mock.patch.object(self.bridge, "_flush_research_sheet_outbox") as flush,
            mock.patch.object(self.bridge, "_research_sheet_backfill_recent_reports") as backfill,
        ):
            self.bridge.dashboard_workflow_scheduler_loop()
        tick.assert_called_once_with(refresh_quota=True)
        flush.assert_not_called()
        backfill.assert_not_called()


if __name__ == "__main__":
    unittest.main()
