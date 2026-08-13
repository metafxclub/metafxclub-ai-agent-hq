from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadarScheduleHardDailyCapTests(unittest.TestCase):
    """The Radar runtime, not merely its form, enforces two Bangkok runs/day."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge("radar_schedule_hard_cap_bridge")

    def setUp(self) -> None:
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_STOP.clear()
        self.bridge.DASHBOARD_WORKFLOW_SCHEDULER_WAKE.clear()

    @staticmethod
    def _queued_result(index: int) -> dict:
        return {
            "ok": True,
            "kind": "mission_auto_queued",
            "mission": {"id": f"mission-radar-cap-{index}", "status": "queued"},
            "idempotentReplay": False,
        }

    def _runtime_patches(self, bridge, settings_path: Path, runner):
        return (
            mock.patch.object(bridge, "DASHBOARD_WORKFLOW_SETTINGS_PATH", settings_path),
            mock.patch.object(bridge, "load_missions", return_value=[]),
            mock.patch.object(bridge, "append_audit"),
            mock.patch.object(
                bridge,
                "_dashboard_workflow_scheduler_gate",
                return_value={"allowed": True, "reason": "ready"},
            ),
            mock.patch.object(bridge, "run_dashboard_workflow_action", side_effect=runner),
            mock.patch.object(bridge, "utc_now", return_value="2026-08-12T01:00:00Z"),
        )

    def test_schedule_edits_cannot_create_a_third_execution_same_bangkok_day(self) -> None:
        calls: list[dict] = []

        def runner(_prop_id: str, payload: dict, *, trusted_trigger_source: str) -> dict:
            self.assertEqual(trusted_trigger_source, "schedule")
            calls.append(payload)
            return self._queued_result(len(calls))

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            patches = self._runtime_patches(self.bridge, settings_path, runner)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["09:00", "10:00"]},
                )
                first = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                second = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 10, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["11:00", "12:00"]},
                )
                third = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 12, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]

        self.assertTrue(first["dispatched"])
        self.assertTrue(second["dispatched"])
        self.assertFalse(third["dispatched"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(stored["dailyExecutionDate"], "2026-08-12")
        self.assertEqual(stored["dailyExecutionCount"], 2)
        self.assertEqual(len(stored["dailyExecutionSlotKeys"]), 2)

    def test_execution_ledger_survives_bridge_restart(self) -> None:
        calls: list[dict] = []

        def runner(_prop_id: str, payload: dict, *, trusted_trigger_source: str) -> dict:
            calls.append(payload)
            return self._queued_result(len(calls))

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            patches = self._runtime_patches(self.bridge, settings_path, runner)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["09:00", "10:00"]},
                )
                self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )

            restarted = load_bridge("radar_schedule_hard_cap_restarted_bridge")
            restarted.DASHBOARD_WORKFLOW_SCHEDULER_STOP.clear()
            patches = self._runtime_patches(restarted, settings_path, runner)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                second = restarted.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 10, 0, tzinfo=restarted.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                restarted._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["11:00", "12:00"]},
                )
                third = restarted.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 12, 0, tzinfo=restarted.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )

        self.assertTrue(second["dispatched"])
        self.assertFalse(third["dispatched"])
        self.assertEqual(len(calls), 2)

    def test_previous_day_pending_slot_expires_without_dispatch(self) -> None:
        runner = mock.Mock(return_value=self._queued_result(1))
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            patches = self._runtime_patches(self.bridge, settings_path, runner)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["23:59"]},
                )
                captured = self.bridge._dashboard_workflow_capture_due_slots(
                    datetime(2026, 8, 12, 23, 59, tzinfo=self.bridge.THAILAND_TIMEZONE)
                )
                result = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 13, 0, 5, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]

        self.assertEqual(len(captured), 1)
        self.assertFalse(result["dispatched"])
        runner.assert_not_called()
        self.assertIsNone(stored["pendingSlotKey"])
        self.assertEqual(stored["dailyExecutionDate"], "2026-08-13")
        self.assertEqual(stored["dailyExecutionCount"], 0)
        self.assertEqual(
            stored["lastResultKind"],
            "pending_expired_at_bangkok_day_boundary",
        )

    def test_daily_capacity_resets_only_on_next_bangkok_calendar_day(self) -> None:
        calls: list[dict] = []

        def runner(_prop_id: str, payload: dict, *, trusted_trigger_source: str) -> dict:
            calls.append(payload)
            return self._queued_result(len(calls))

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            patches = self._runtime_patches(self.bridge, settings_path, runner)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["09:00", "10:00"]},
                )
                self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 10, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                next_day = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 13, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]

        self.assertTrue(next_day["dispatched"])
        self.assertEqual(len(calls), 3)
        self.assertEqual(stored["dailyExecutionDate"], "2026-08-13")
        self.assertEqual(stored["dailyExecutionCount"], 1)

    def test_latest_due_slot_does_not_backfill_older_slot_on_next_tick(self) -> None:
        calls: list[dict] = []

        def runner(_prop_id: str, payload: dict, *, trusted_trigger_source: str) -> dict:
            calls.append(payload)
            return self._queued_result(len(calls))

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            patches = self._runtime_patches(self.bridge, settings_path, runner)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["09:00", "10:00"]},
                )
                first = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 10, 30, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                second = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 10, 31, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )

        self.assertTrue(first["dispatched"])
        self.assertEqual(first["slotKey"], "indicatorScoutSchedule:2026-08-12:1000")
        self.assertFalse(second["dispatched"])
        self.assertEqual(len(calls), 1)

    def test_dispatch_exception_consumes_fail_closed_reservation(self) -> None:
        runner = mock.Mock(side_effect=RuntimeError("ambiguous dispatch boundary"))
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            patches = self._runtime_patches(self.bridge, settings_path, runner)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                self.bridge._save_dashboard_schedule_preference(
                    "indicatorScoutSchedule",
                    {"enabled": True, "times": ["09:00"]},
                )
                first = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                second = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 12, 9, 10, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()["indicatorScoutSchedule"]

        self.assertFalse(first["dispatched"])
        self.assertFalse(second["dispatched"])
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(stored["dailyExecutionCount"], 1)
        self.assertIsNone(stored["pendingSlotKey"])
        self.assertEqual(stored["lastResultKind"], "pending_slot_already_reserved")

    def test_contracts_declare_runtime_cap_restart_and_midnight_policies(self) -> None:
        compatibility = json.loads(
            (PROJECT_ROOT / "contracts" / "research" / "radar-website-tool-compatibility-v1.json")
            .read_text(encoding="utf-8")
        )
        connection = json.loads(
            (PROJECT_ROOT / "contracts" / "connections" / "dashboard-connection-contract.json")
            .read_text(encoding="utf-8")
        )
        schedule = compatibility["settings"]["schedule"]
        operation = connection["profiles"]["left_audit_crystals"]["operation"]

        self.assertEqual(schedule["maximumRunsPerDay"], 2)
        self.assertTrue(schedule["hardRuntimeEnforced"])
        self.assertEqual(schedule["counterPersistence"], "backend_local_settings")
        self.assertEqual(schedule["countingPolicy"], "pre_dispatch_fail_closed_reservation")
        self.assertEqual(schedule["stalePendingPolicy"], "expire_at_bangkok_day_boundary")
        self.assertEqual(schedule["catchUpPolicy"], "latest_same_day_slot_only")
        self.assertTrue(operation["scheduleHardMaximumRuntimeEnforced"])
        self.assertEqual(operation["scheduleHardMaximumRunsPerDay"], 2)


if __name__ == "__main__":
    unittest.main()
