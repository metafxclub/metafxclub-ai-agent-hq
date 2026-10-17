from __future__ import annotations

import importlib.util
import unittest
from unittest import mock
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "mission_metatrader_dual_lock_gate_bridge",
        BRIDGE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MissionMetatraderDualLockGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()

    def test_scope_uses_route_metadata_when_prompt_is_vague(self) -> None:
        scope = self.bridge.metatrader_mission_lock_scope(
            detail="Implement the requested crossover logic.",
            target_id="terminal_workstation",
            owner_agent_id="ea_developer",
            tool_id="codex_cli_task",
        )

        self.assertTrue(scope["required"])
        self.assertIn("target:terminal_workstation", scope["signals"])
        self.assertIn("owner:ea_developer", scope["signals"])

    def test_pure_existing_report_analysis_is_exempt_but_followup_is_not(self) -> None:
        analysis_scope = self.bridge.metatrader_mission_lock_scope(
            detail="Analyze the existing MT5 backtest report and summarize it.",
            target_id="left_analytics_console",
            owner_agent_id="backtest_analyst",
            tool_id="codex_cli_task",
        )
        execution_scope = self.bridge.metatrader_mission_lock_scope(
            detail="Analyze the existing MT5 backtest report, then compile the EA.",
            target_id="left_analytics_console",
            owner_agent_id="backtest_analyst",
            tool_id="codex_cli_task",
        )

        self.assertFalse(analysis_scope["required"])
        self.assertEqual(analysis_scope["reason"], "analysis_only_intent")
        self.assertTrue(execution_scope["required"])

    def test_mixed_report_and_authoring_intent_cannot_bypass_route_gate(self) -> None:
        english_scope = self.bridge.metatrader_mission_lock_scope(
            detail="Review the existing report; write an MQL5 indicator.",
            target_id="terminal_workstation",
            owner_agent_id="ea_developer",
            tool_id="codex_cli_task",
        )
        thai_scope = self.bridge.metatrader_mission_lock_scope(
            detail="วิเคราะห์รายงานและเขียน EA สำหรับ MT4",
            target_id="terminal_workstation",
            owner_agent_id="ea_developer",
            tool_id="codex_cli_task",
        )
        generic_followup_scope = self.bridge.metatrader_mission_lock_scope(
            detail="Analyze the existing MT5 backtest report, then run it.",
            target_id="left_analytics_console",
            owner_agent_id="backtest_analyst",
            tool_id="codex_cli_task",
        )

        self.assertTrue(english_scope["required"])
        self.assertTrue(thai_scope["required"])
        self.assertTrue(generic_followup_scope["required"])

    def test_explicit_platform_fails_closed_for_unknown_authoring_synonyms(self) -> None:
        for detail in (
            "Produce a trading robot for MetaTrader 5",
            "ผลิตบอทเทรดสำหรับ MetaTrader 5",
            "Program a custom robot on MT4",
        ):
            with self.subTest(detail=detail):
                scope = self.bridge.metatrader_mission_lock_scope(
                    detail=detail,
                    owner_agent_id="codex_mcp_operator",
                    target_id="codex_mcp_portal",
                    tool_id="codex_cli_task",
                    execution_mode="workspace",
                )
                self.assertTrue(scope["required"])
                self.assertIn(f"platform:{scope['platform']}", scope["signals"])

        pure_report = self.bridge.metatrader_mission_lock_scope(
            detail="Analyze the attached existing MT5 backtest report only",
            owner_agent_id="codex_mcp_operator",
            target_id="codex_mcp_portal",
            tool_id="codex_cli_task",
            execution_mode="workspace",
        )
        self.assertFalse(pure_report["required"])

    def test_required_analysis_named_workflow_still_requires_dual_lock(self) -> None:
        context = {
            "schemaVersion": "dashboard-workflow-lineage-v1",
            "propId": "right_tool_console",
            "actionId": "prepare_backtest_plan",
            "inputs": {"platform": "mt5"},
            "inputDigest": "a" * 64,
        }

        scope = self.bridge.metatrader_mission_lock_scope(
            detail="Prepare the test plan.",
            target_id="right_tool_console",
            owner_agent_id="backtest_analyst",
            tool_id="codex_cli_task",
            workflow_context=context,
        )

        self.assertTrue(scope["required"])
        self.assertEqual(scope["platform"], "mt5")
        self.assertIn("workflow:prepare_backtest_plan", scope["signals"])

    def test_public_web_research_is_exempt_but_mixed_mt_execution_is_not(self) -> None:
        research_context = {
            "schemaVersion": "dashboard-workflow-lineage-v1",
            "propId": "left_audit_crystals",
            "actionId": "discover_new_indicators",
            "inputs": {"platform": "mt5", "query": "public EA sources"},
            "inputDigest": "b" * 64,
        }

        research_scope = self.bridge.metatrader_mission_lock_scope(
            detail=(
                "Search public websites for MT4/MT5 EA and indicator sources, "
                "then return a read-only evidence report."
            ),
            target_id="left_audit_crystals",
            owner_agent_id="codex_mcp_operator",
            tool_id="codex_web_research",
            workflow_context=research_context,
        )
        mixed_execution_scope = self.bridge.metatrader_mission_lock_scope(
            detail=(
                "Research the existing EA report, then compile and backtest "
                "the MQL5 source."
            ),
            target_id="terminal_workstation",
            owner_agent_id="ea_developer",
            tool_id="codex_cli_task",
        )

        self.assertFalse(research_scope["required"])
        self.assertEqual(research_scope["platform"], "mt5")
        self.assertEqual(research_scope["reason"], "analysis_only_workflow")
        self.assertTrue(mixed_execution_scope["required"])
        self.assertIn("intent:metatrader_execution", mixed_execution_scope["signals"])

    def test_tradingview_and_chat_only_paths_are_exempt(self) -> None:
        tradingview_scope = self.bridge.metatrader_mission_lock_scope(
            detail="Write a Pine Script indicator for TradingView.",
            target_id="terminal_workstation",
            owner_agent_id="ea_developer",
            tool_id="codex_cli_task",
        )
        chat_scope = self.bridge.metatrader_mission_lock_scope(
            detail="Write an MT5 EA.",
            target_id="terminal_workstation",
            owner_agent_id="ea_developer",
            tool_id="codex_cli_task",
            execution_mode="chat",
        )

        self.assertFalse(tradingview_scope["required"])
        self.assertEqual(tradingview_scope["reason"], "tradingview_only")
        self.assertFalse(chat_scope["required"])
        self.assertEqual(chat_scope["reason"], "chat_only")

    def test_manager_route_is_rejected_before_parent_creation(self) -> None:
        contract = {
            "managerAutoDelegation": {
                "defaultSubtaskToolId": "codex_cli_task",
                "summaryTargetPropId": "mission_strategy_table",
                "maxSubtasks": 6,
                "specialistRules": [],
            },
            "costRateGuard": {},
        }
        with (
            mock.patch.object(
                self.bridge,
                "evaluate_tool_permission",
                return_value={"allowed": True, "policy": {}},
            ),
            mock.patch.object(
                self.bridge,
                "load_agent_contracts",
                return_value=[{"id": "manager"}, {"id": "ea_developer"}],
            ),
            mock.patch.object(
                self.bridge,
                "allowed_targets_for_agent",
                return_value={"terminal_workstation"},
            ),
            mock.patch.object(self.bridge, "load_orchestration_contract", return_value=contract),
            mock.patch.object(self.bridge, "find_mission_by_idempotency", return_value=None),
            mock.patch.object(self.bridge, "_active_global_metatrader_context", return_value=None),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge, "create_mission") as create_mission,
        ):
            result = self.bridge.manager_delegate(
                {
                    "agentId": "manager",
                    "goal": "Implement the requested crossover logic.",
                    "requestedOwnerAgentId": "ea_developer",
                    "requestedTargetId": "terminal_workstation",
                    "idempotencyKey": "manager-mt-lock-test",
                }
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "global_metatrader_locks_incomplete")
        self.assertFalse(result["missionCreated"])
        create_mission.assert_not_called()

    def test_bridge_route_is_rejected_before_mission_creation(self) -> None:
        with (
            mock.patch.object(
                self.bridge,
                "evaluate_tool_permission",
                return_value={"allowed": True, "policy": {"risk": "medium"}},
            ),
            mock.patch.object(self.bridge, "tool_execution_capability_unavailable", return_value=False),
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "terminal_workstation"}),
            mock.patch.object(
                self.bridge,
                "load_agent_contracts",
                return_value=[{"id": "ea_developer"}],
            ),
            mock.patch.object(self.bridge, "_active_global_metatrader_context", return_value=None),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge, "create_mission") as create_mission,
        ):
            result = self.bridge.run_bridge_task(
                {
                    "toolId": "codex_cli_task",
                    "agentId": "ea_developer",
                    "targetId": "terminal_workstation",
                    "prompt": "Implement the requested crossover logic.",
                }
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "global_metatrader_locks_incomplete")
        create_mission.assert_not_called()

    def test_execute_revalidates_without_consuming_approval(self) -> None:
        mission = {
            "id": "mission-mt-lock-test",
            "detail": "Implement the requested crossover logic.",
            "owner": "ea_developer",
            "toolId": "codex_cli_task",
            "targetId": "terminal_workstation",
            "status": "waiting_approval",
            "approval": {"required": True, "state": "approved"},
        }
        with (
            mock.patch.object(self.bridge, "find_mission", return_value=mission),
            mock.patch.object(self.bridge, "_active_global_metatrader_context", return_value=None),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge, "replace_mission") as replace_mission,
        ):
            result = self.bridge.execute_mission(
                mission["id"],
                {"confirmMissionId": mission["id"]},
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "global_metatrader_locks_incomplete")
        self.assertEqual(mission["approval"]["state"], "approved")
        replace_mission.assert_not_called()

    def test_auto_claim_defers_before_authorization_consumption(self) -> None:
        mission = {
            "id": "mission-auto-mt-lock-test",
            "detail": "Implement the requested crossover logic.",
            "owner": "ea_developer",
            "toolId": "codex_cli_task",
            "targetId": "terminal_workstation",
            "status": "queued",
            "approval": {"required": False, "state": "not_required"},
            "execution": {"dispatchState": "queued"},
        }
        with (
            mock.patch.object(self.bridge, "load_missions", return_value=[mission]),
            mock.patch.object(self.bridge, "_council_vote_parent_state_error", return_value=None),
            mock.patch.object(self.bridge, "auto_execution_authorization_error", return_value=None),
            mock.patch.object(self.bridge, "_active_global_metatrader_context", return_value=None),
            mock.patch.object(self.bridge, "defer_auto_mission") as defer_auto,
            mock.patch.object(self.bridge, "save_missions") as save_missions,
        ):
            claimed = self.bridge._claim_auto_mission_unlocked(
                mission["id"],
                "worker-test",
            )

        self.assertIsNone(claimed)
        defer_auto.assert_called_once_with(
            mission["id"],
            "global_metatrader_locks_incomplete",
            30,
        )
        save_missions.assert_not_called()
        self.assertEqual(mission["status"], "queued")

    def test_auto_process_defers_before_runner_or_quota_checks(self) -> None:
        mission = {
            "id": "mission-process-mt-lock-test",
            "detail": "Implement the requested crossover logic.",
            "owner": "ea_developer",
            "toolId": "codex_cli_task",
            "targetId": "terminal_workstation",
            "status": "queued",
            "budget": {},
        }
        with (
            mock.patch.object(
                self.bridge,
                "mission_worker_config",
                return_value={"runnerUnavailableBackoffSeconds": 17},
            ),
            mock.patch.object(self.bridge, "_ai_trade_council_round_remaining_seconds", return_value=None),
            mock.patch.object(self.bridge, "_is_ai_trade_council_vote_mission", return_value=False),
            mock.patch.object(self.bridge, "_expire_prior_day_radar_mission", return_value=False),
            mock.patch.object(self.bridge, "_active_global_metatrader_context", return_value=None),
            mock.patch.object(self.bridge, "_defer_auto_mission_with_round_deadline") as defer_auto,
            mock.patch.object(self.bridge, "bridge_status") as bridge_status,
        ):
            self.bridge.process_auto_mission("worker-test", mission)

        defer_auto.assert_called_once_with(
            mission,
            "global_metatrader_locks_incomplete",
            17,
        )
        bridge_status.assert_not_called()

    def test_full_agent_workspace_rejects_before_durable_turn_creation(self) -> None:
        class RuntimeDouble:
            request_turn_called = False

            def get_thread(self, thread_id, include_events=False):
                return {
                    "id": thread_id,
                    "agentId": "ea_developer",
                    "mode": "workspace",
                }

            def request_turn(self, *args, **kwargs):
                self.request_turn_called = True
                raise AssertionError("request_turn must not be reached")

        runtime = RuntimeDouble()
        with (
            mock.patch.object(self.bridge, "_full_agent_runtime", return_value=runtime),
            mock.patch.object(self.bridge, "role_default_target_id", return_value="terminal_workstation"),
            mock.patch.object(self.bridge, "_active_global_metatrader_context", return_value=None),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            with self.assertRaises(self.bridge.RequestError) as caught:
                self.bridge.full_agent_request_turn(
                    "thread-mt-lock-test",
                    {
                        "message": "Implement the requested crossover logic.",
                        "idempotencyKey": "full-agent-mt-lock-test",
                    },
                )

        self.assertEqual(caught.exception.status, 409)
        self.assertFalse(runtime.request_turn_called)


if __name__ == "__main__":
    unittest.main()
