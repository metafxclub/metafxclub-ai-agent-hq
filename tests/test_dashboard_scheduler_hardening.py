from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "metafx_dashboard_scheduler_hardening_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DashboardSchedulerHardeningTests(unittest.TestCase):
    """Regression requirements for trusted, restart-safe dashboard scheduling."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    @staticmethod
    def _queued_result(mission_id: str = "mission-scheduled-hardening-1") -> dict:
        return {
            "ok": True,
            "kind": "mission_auto_queued",
            "mission": {"id": mission_id, "status": "queued"},
            "idempotentReplay": False,
        }

    def test_disabling_schedule_after_pending_capture_cancels_dispatch(self) -> None:
        """A stale pending snapshot must not run after the user disables its schedule."""

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "dashboard-workflow-settings.json"

            def disable_during_gate(*, refresh_quota: bool) -> dict:
                self.assertFalse(refresh_quota)
                self.bridge.save_dashboard_discovery_schedule(
                    {"enabled": False, "times": ["09:00"]}
                )
                return {"allowed": True, "reason": "ready"}

            with (
                mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SETTINGS_PATH", settings_path),
                mock.patch.object(self.bridge, "load_missions", return_value=[]),
                mock.patch.object(self.bridge, "append_audit"),
                mock.patch.object(
                    self.bridge,
                    "_dashboard_workflow_scheduler_gate",
                    side_effect=disable_during_gate,
                ),
                mock.patch.object(
                    self.bridge,
                    "run_dashboard_workflow_action",
                    return_value=self._queued_result(),
                ) as runner,
            ):
                self.bridge.save_direct_daily_fx_news_schedule(
                    {"enabled": False, "times": ["00:00", "12:00"]}
                )
                self.bridge.save_dashboard_discovery_schedule(
                    {"enabled": True, "times": ["09:00"]}
                )
                result = self.bridge.dashboard_workflow_scheduler_tick(
                    datetime(2026, 8, 9, 9, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()

        self.assertFalse(result["dispatched"])
        runner.assert_not_called()
        self.assertFalse(stored["discoverySchedule"]["requestedEnabled"])
        self.assertIsNone(stored["discoverySchedule"]["pendingSlotKey"])

    def test_frontend_cannot_use_reserved_dashboard_schedule_idempotency_prefix(self) -> None:
        """Predictable scheduler keys are an internal namespace, never frontend input."""

        captured: list[dict] = []

        def fake_bridge_task(payload: dict, **_kwargs) -> dict:
            captured.append(payload)
            return self._queued_result()

        with (
            mock.patch.object(
                self.bridge,
                "find_room_prop",
                return_value={"id": "codex_mcp_portal"},
            ),
            mock.patch.object(
                self.bridge,
                "_workflow_action_contract_gate",
                return_value={"allowed": True},
            ),
            mock.patch.object(
                self.bridge,
                "_trusted_workflow_plugin_profile",
                return_value={"contractVersion": "test", "procedureKind": "builtin_test"},
            ),
            mock.patch.object(self.bridge, "_workflow_prompt", return_value="safe public research"),
            mock.patch.object(self.bridge, "find_mission_by_idempotency", return_value=None),
            mock.patch.object(self.bridge, "run_bridge_task", side_effect=fake_bridge_task),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            with self.assertRaises(self.bridge.RequestError) as context:
                self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "discover_trading_systems",
                        "form": {},
                        "idempotencyKey": (
                            "dashboard-schedule:discoverySchedule:2026-08-09:0900"
                        ),
                    },
                )

        self.assertIn(context.exception.status, {403, 422})
        self.assertEqual(captured, [])

    def test_completed_idempotent_mission_replay_does_not_return_approval_required(self) -> None:
        """A terminal replay is a terminal result, not a new approval wait loop."""

        plugin_profile = self.bridge.equipment_action_profile(
            "codex_mcp_portal",
            "discover_trading_systems",
        )
        trusted_schedule_context = self.bridge._dashboard_workflow_lineage(
            "codex_mcp_portal",
            "discover_trading_systems",
            {},
            None,
            trigger_source="schedule",
            plugin_profile=plugin_profile,
        )
        completed = {
            "id": "mission-completed-replay-1",
            "owner": "codex_mcp_operator",
            "toolId": "codex_web_research",
            "targetId": "codex_mcp_portal",
            "status": "completed",
            "autoEligible": True,
            "executionMode": "auto_guarded",
            "requiresHumanApproval": False,
            "approval": {"required": True, "state": "approved"},
        }
        with (
            mock.patch.object(
                self.bridge,
                "evaluate_tool_permission",
                return_value={
                    "allowed": True,
                    "policy": {"risk": "low", "adapterStatus": "runtime_detected"},
                },
            ),
            mock.patch.object(
                self.bridge,
                "tool_execution_capability_unavailable",
                return_value=False,
            ),
            mock.patch.object(
                self.bridge,
                "find_room_prop",
                return_value={"id": "codex_mcp_portal"},
            ),
            mock.patch.object(
                self.bridge,
                "load_agent_contracts",
                return_value=[{"id": "codex_mcp_operator"}],
            ),
            mock.patch.object(
                self.bridge,
                "load_report_contract",
                return_value={"report_targets": {"trading_system_discovery_report": {}}},
            ),
            mock.patch.object(self.bridge, "create_mission", return_value=completed),
            mock.patch.object(
                self.bridge,
                "bridge_status",
                return_value={"codex": {"status": "ready_guarded"}},
            ),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_bridge_task(
                {
                    "toolId": "codex_web_research",
                    "agentId": "codex_mcp_operator",
                    "requester": "codex_mcp_operator",
                    "targetId": "codex_mcp_portal",
                    "reportType": "trading_system_discovery_report",
                    "prompt": "Read-only public research",
                    "idempotencyKey": "dashboard-schedule:test-completed-replay",
                },
                trusted_workflow_context=trusted_schedule_context,
            )

        self.assertTrue(result["ok"])
        self.assertNotEqual(result["kind"], "approval_required")
        self.assertEqual(result["mission"]["id"], completed["id"])
        self.assertEqual(result["mission"]["status"], "completed")

    def test_scheduled_action_propagates_saved_model_and_budget_preferences(self) -> None:
        """Backend-owned schedule controls must reach mission creation, not remain cosmetic."""

        captured: dict = {}

        def fake_bridge_task(payload: dict, **kwargs) -> dict:
            captured["payload"] = payload
            captured["workflowContext"] = kwargs.get("trusted_workflow_context")
            return self._queued_result("mission-budget-propagation-1")

        preferences = {
            "language": "th",
            "modelTier": "specialist_balanced",
            "tokenBudget": 5432,
            "timeoutSeconds": 321,
            "outputLimitChars": 4321,
            "rateReservePercent": 35,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "dashboard-workflow-settings.json"
            with (
                mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SETTINGS_PATH", settings_path),
                mock.patch.object(
                    self.bridge,
                    "find_room_prop",
                    return_value={"id": "codex_mcp_portal"},
                ),
                mock.patch.object(
                    self.bridge,
                    "_workflow_action_contract_gate",
                    return_value={"allowed": True},
                ),
                mock.patch.object(
                    self.bridge,
                    "_trusted_workflow_plugin_profile",
                    return_value={"contractVersion": "test", "procedureKind": "builtin_test"},
                ),
                mock.patch.object(self.bridge, "_workflow_prompt", return_value="safe public research"),
                mock.patch.object(self.bridge, "find_mission_by_idempotency", return_value=None),
                mock.patch.object(self.bridge, "run_bridge_task", side_effect=fake_bridge_task),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                saved = self.bridge._save_dashboard_agent_preferences(preferences)
                result = self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "discover_trading_systems",
                        "form": {},
                        "idempotencyKey": "dashboard-schedule:budget-propagation-test",
                    },
                    trusted_trigger_source="schedule",
                )

        self.assertTrue(result["ok"])
        self.assertEqual(saved["modelTier"], preferences["modelTier"])
        self.assertEqual(captured["payload"].get("modelTier"), preferences["modelTier"])
        self.assertEqual(
            captured["payload"].get("budget"),
            {
                "tokenBudget": preferences["tokenBudget"],
                "timeoutSeconds": preferences["timeoutSeconds"],
                "outputLimitChars": preferences["outputLimitChars"],
            },
        )

    def test_rate_reserve_is_clamped_to_same_10_80_range_everywhere(self) -> None:
        """Stored/read and submitted reserve values must match the quota gate range."""

        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["save_agent_preferences"]
        low_model = self.bridge._dashboard_agent_preferences_read_model(
            {"agentPreferences": {"rateReservePercent": -999}}
        )
        high_model = self.bridge._dashboard_agent_preferences_read_model(
            {"agentPreferences": {"rateReservePercent": 999}}
        )
        low_form = self.bridge._sanitize_dashboard_workflow_form(
            action,
            {"rateReservePercent": -999},
        )
        high_form = self.bridge._sanitize_dashboard_workflow_form(
            action,
            {"rateReservePercent": 999},
        )

        self.assertEqual(low_model["rateReservePercent"], 10)
        self.assertEqual(high_model["rateReservePercent"], 80)
        self.assertEqual(low_form["rateReservePercent"], 10)
        self.assertEqual(high_form["rateReservePercent"], 80)

    def test_news_pending_slot_expires_at_midnight_without_researching_prior_date(self) -> None:
        """A prior Bangkok-day slot must expire, never run as today's news."""

        captured: list[dict] = []

        def fake_action(_prop_id: str, payload: dict, *, trusted_trigger_source: str) -> dict:
            self.assertEqual(trusted_trigger_source, "schedule")
            captured.append(payload)
            return self._queued_result("mission-news-midnight-retry-1")

        slot_time = datetime(
            2026,
            8,
            9,
            23,
            59,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        retry_time = datetime(
            2026,
            8,
            10,
            0,
            5,
            tzinfo=self.bridge.THAILAND_TIMEZONE,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "dashboard-workflow-settings.json"
            with (
                mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SETTINGS_PATH", settings_path),
                mock.patch.object(self.bridge, "load_missions", return_value=[]),
                mock.patch.object(self.bridge, "append_audit"),
                mock.patch.object(
                    self.bridge,
                    "_dashboard_workflow_scheduler_gate",
                    return_value={"allowed": True, "reason": "ready"},
                ),
                mock.patch.object(
                    self.bridge,
                    "run_dashboard_workflow_action",
                    side_effect=fake_action,
                ),
            ):
                self.bridge._save_dashboard_schedule_preference(
                    "newsBiasSchedule",
                    {
                        "enabled": True,
                        "times": ["23:59"],
                        "minimumImpact": "high",
                    },
                )
                captured_slots = self.bridge._dashboard_workflow_capture_due_slots(slot_time)
                result = self.bridge.dashboard_workflow_scheduler_tick(
                    retry_time,
                    refresh_quota=False,
                )
                stored = self.bridge.load_dashboard_workflow_settings()["newsBiasSchedule"]

        self.assertEqual(len(captured_slots), 1)
        self.assertFalse(result["dispatched"])
        self.assertEqual(result["kind"], "scheduler_idle")
        self.assertEqual(captured, [])
        self.assertIsNone(stored["pendingSlotKey"])
        self.assertIsNone(stored["pendingScheduledAt"])
        self.assertEqual(stored["dailyExecutionDate"], "2026-08-10")
        self.assertEqual(stored["dailyExecutionCount"], 0)
        self.assertEqual(
            stored["lastResultKind"],
            "pending_expired_at_bangkok_day_boundary",
        )


if __name__ == "__main__":
    unittest.main()
