from __future__ import annotations

import csv
import http.client
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DashboardWorkflowBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("metafx_dashboard_workflow_bridge", BRIDGE_PATH)

    def ready_bridge(self) -> dict:
        return {"codex": {"status": "ready_guarded"}}

    def test_ready_guarded_codex_is_connected_in_dashboard_checklists(self) -> None:
        freshness = {
            "bridge": self.bridge._connection_probe_freshness({}),
            "codexQuota": self.bridge._connection_probe_freshness({}),
            "metatrader": self.bridge._connection_probe_freshness({}),
        }
        item = self.bridge._connection_item_status(
            {
                "id": "codex_runner",
                "labelTh": "Codex CLI",
                "required": True,
                "adapterStatus": "runtime_detected",
            },
            self.ready_bridge(),
            {},
            {},
            False,
            freshness,
        )
        self.assertEqual(item["status"], "connected")
        self.assertNotIn("ยังไม่พบ", item["detailTh"])

    def test_action_whitelist_is_prop_scoped_and_intent_only(self) -> None:
        expected = {
            "codex_mcp_portal": {
                "discover_trading_systems",
                "discover_ea_updates",
                "save_discovery_schedule",
            },
            "left_server_racks": {"deep_research_system"},
            "right_server_racks": {"build_strategy_code", "review_source_code"},
            "right_tool_console": {
                "prepare_backtest_plan",
                "prepare_optimization_plan",
                "prepare_ea_discovery_plan",
            },
            "left_audit_crystals": {
                "discover_new_indicators",
                "save_indicator_scout_schedule",
            },
            "left_signal_cube": {
                "analyze_daily_market_news",
                "build_fx_pair_bias",
                "save_news_bias_schedule",
            },
            "terminal_workstation": {
                "inspect_ea_source",
                "develop_ea_source",
                "propose_ea_performance_improvements",
            },
            "right_status_crystals": {
                "refresh_vps_hq_status",
                "save_agent_preferences",
            },
        }
        actual = {prop_id: set() for prop_id in expected}
        for action_id, action in self.bridge.DASHBOARD_WORKFLOW_ACTIONS.items():
            actual[action["propId"]].add(action_id)
            self.assertTrue(action["analysisOnly"])
            self.assertIn(action.get("toolId"), {None, "codex_cli_task", "codex_web_research"})
        self.assertEqual(actual, expected)

    def test_tabs_reference_only_actions_owned_by_the_same_prop(self) -> None:
        for prop_id, tabs in self.bridge.DASHBOARD_WORKFLOW_TABS.items():
            self.assertEqual(len(tabs), 4, prop_id)
            for tab in tabs:
                for action_id in tab["actionIds"]:
                    self.assertEqual(
                        self.bridge.DASHBOARD_WORKFLOW_ACTIONS[action_id]["propId"],
                        prop_id,
                    )

    def test_read_model_exposes_only_agent_delivered_sources_without_local_paths(self) -> None:
        reports = [
            {
                "id": "portal-report-1",
                "linkedPropId": "codex_mcp_portal",
                "linkedMissionId": "mission-source-1",
                "title": "Public trading system",
                "summary": "Read-only public research",
                "type": "trading_system_discovery_report",
                "ownerAgentId": "codex_mcp_operator",
                "status": "ready",
                "artifactPath": "C:\\Users\\META\\private\\report.json",
                "updatedAt": "2026-08-08T01:00:00+00:00",
            },
            {
                "id": "unrelated-report-1",
                "linkedPropId": "left_analytics_console",
                "title": "Unrelated",
                "summary": "Must not be selectable",
            },
        ]
        source_mission = {
            "id": "mission-source-1",
            "owner": "codex_mcp_operator",
            "targetId": "codex_mcp_portal",
            "status": "completed",
            "reportIds": ["portal-report-1"],
        }
        transfer = {
            "mode": "agent_mission_report",
            "sourceReportId": "portal-report-1",
            "sourcePropId": "codex_mcp_portal",
            "sourceMissionId": "mission-source-1",
            "transferAgentId": "ea_developer",
            "sourceOwnerAgentId": "codex_mcp_operator",
            "targetPropId": "right_server_racks",
            "handoffMissionId": "mission-handoff-1",
            "status": "recorded",
        }
        handoff_mission = {
            "id": "mission-handoff-1",
            "owner": "ea_developer",
            "targetId": "right_server_racks",
            "toolId": "agent_report_transfer",
            "status": "completed",
            "agentTransfer": transfer,
        }
        with (
            mock.patch.object(self.bridge, "find_property_role", return_value={}),
            mock.patch.object(self.bridge, "load_missions", return_value=[source_mission]),
        ):
            model = self.bridge.workflow_dashboard_read_model(
                "right_server_racks",
                reports=reports,
                bridge=self.ready_bridge(),
            )
        self.assertEqual(model["schemaVersion"], "dashboard-workflow-v2")
        self.assertTrue(model["independent"])
        self.assertEqual(model["coordinationMode"], "agent_mission_only")
        self.assertTrue(model["agentTransferOnly"])
        self.assertFalse(model["directDashboardDependency"])
        self.assertEqual(model["agentDeliveredSources"], [])
        self.assertNotIn("upstreamSources", model)
        self.assertNotIn("pipelineId", model)
        self.assertNotIn("pipelineStage", model)
        self.assertNotIn("pipelineOrder", model)

        with (
            mock.patch.object(self.bridge, "find_property_role", return_value={}),
            mock.patch.object(self.bridge, "load_missions", return_value=[source_mission, handoff_mission]),
        ):
            delivered_model = self.bridge.workflow_dashboard_read_model(
                "right_server_racks",
                reports=reports,
                bridge=self.ready_bridge(),
            )
        delivered = delivered_model["agentDeliveredSources"]
        self.assertEqual([row["reportId"] for row in delivered], ["portal-report-1"])
        self.assertNotIn("artifactPath", delivered[0])
        self.assertNotIn("sourcePath", delivered[0])
        self.assertEqual(
            delivered[0]["agentTransfersByActionId"]["build_strategy_code"]["handoffMissionId"],
            "mission-handoff-1",
        )

    def test_read_model_exposes_safe_transfer_destinations_without_report_contents(self) -> None:
        with (
            mock.patch.object(self.bridge, "find_property_role", return_value={}),
            mock.patch.object(self.bridge, "load_missions", return_value=[]),
        ):
            model = self.bridge.workflow_dashboard_read_model(
                "codex_mcp_portal",
                reports=[],
                bridge=self.ready_bridge(),
            )
        destinations = model["agentTransferDestinations"]
        self.assertTrue(destinations)
        self.assertIn(
            {
                "targetPropId": "left_server_racks",
                "actionId": "deep_research_system",
                "labelTh": self.bridge.DASHBOARD_WORKFLOW_ACTIONS["deep_research_system"]["labelTh"],
                "transferAgentId": "mission_archivist",
            },
            destinations,
        )
        self.assertTrue(all(set(row) == {
            "targetPropId", "actionId", "labelTh", "transferAgentId",
        } for row in destinations))
        self.assertNotIn("reports", model)
        self.assertEqual(model["agentDeliveredSources"], [])

    def test_report_transfer_endpoint_creates_one_completed_handoff_and_replays_idempotently(self) -> None:
        source_report = {
            "id": "portal-report-transfer-1",
            "linkedPropId": "codex_mcp_portal",
            "linkedMissionId": "mission-source-transfer-1",
            "ownerAgentId": "codex_mcp_operator",
            "type": "trading_system_discovery_report",
            "status": "ready",
            "title": "Public system",
        }
        source_mission = {
            "id": "mission-source-transfer-1",
            "owner": "codex_mcp_operator",
            "targetId": "codex_mcp_portal",
            "status": "completed",
            "reportIds": ["portal-report-transfer-1"],
        }
        captured: dict = {}

        def fake_create_mission(payload: dict, status: str = "queued", **kwargs) -> dict:
            mission = {
                "id": payload["id"],
                "title": payload["title"],
                "detail": payload["prompt"],
                "owner": payload["agentId"],
                "requester": payload["requester"],
                "toolId": payload["toolId"],
                "targetId": payload["targetId"],
                "reportType": payload["reportType"],
                "risk": payload["risk"],
                "status": status,
                "workflowContext": kwargs["workflow_context"],
                "agentTransfer": kwargs["workflow_context"]["agentTransfer"],
                "reportIds": [],
                "createdAt": "2026-08-08T00:00:00Z",
                "updatedAt": "2026-08-08T00:00:00Z",
            }
            captured["mission"] = mission
            return mission

        def find_existing(_key: str) -> dict | None:
            return captured.get("mission")

        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "left_server_racks"}),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[source_report]),
            mock.patch.object(self.bridge, "load_missions", return_value=[source_mission]),
            mock.patch.object(self.bridge, "find_mission_by_idempotency", side_effect=find_existing),
            mock.patch.object(self.bridge, "create_mission", side_effect=fake_create_mission) as create_mission,
            mock.patch.object(self.bridge, "replace_mission") as replace_mission,
            mock.patch.object(self.bridge, "append_agent_event"),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            first = self.bridge.deliver_dashboard_report(
                "left_server_racks",
                {
                    "actionId": "deep_research_system",
                    "sourceReportId": "portal-report-transfer-1",
                    "idempotencyKey": "handoff-click-1",
                },
            )
            second = self.bridge.deliver_dashboard_report(
                "left_server_racks",
                {
                    "actionId": "deep_research_system",
                    "sourceReportId": "portal-report-transfer-1",
                    "idempotencyKey": "handoff-click-1",
                },
            )
        self.assertFalse(first["idempotentReplay"])
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(first["mission"]["id"], second["mission"]["id"])
        self.assertEqual(first["mission"]["status"], "completed")
        self.assertEqual(first["mission"]["toolId"], "agent_report_transfer")
        self.assertEqual(first["agentTransfer"]["sourceMissionId"], "mission-source-transfer-1")
        self.assertEqual(first["agentTransfer"]["transferAgentId"], "mission_archivist")
        self.assertEqual(first["agentTransfer"]["targetPropId"], "left_server_racks")
        self.assertEqual(first["agentTransfer"]["handoffMissionId"], first["mission"]["id"])
        create_mission.assert_called_once()
        replace_mission.assert_called_once()

    def test_report_transfer_rejects_arbitrary_report_without_completed_source_mission(self) -> None:
        source_report = {
            "id": "unbound-report-1",
            "linkedPropId": "codex_mcp_portal",
            "linkedMissionId": "mission-still-running",
            "ownerAgentId": "codex_mcp_operator",
            "type": "trading_system_discovery_report",
            "status": "ready",
        }
        running_mission = {
            "id": "mission-still-running",
            "owner": "codex_mcp_operator",
            "targetId": "codex_mcp_portal",
            "status": "running",
            "reportIds": ["unbound-report-1"],
        }
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "left_server_racks"}),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[source_report]),
            mock.patch.object(self.bridge, "load_missions", return_value=[running_mission]),
            mock.patch.object(self.bridge, "create_mission") as create_mission,
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge.deliver_dashboard_report(
                    "left_server_racks",
                    {
                        "actionId": "deep_research_system",
                        "sourceReportId": "unbound-report-1",
                    },
                )
        create_mission.assert_not_called()

    def test_workflow_prop_report_does_not_leak_keyword_participant_or_unlinked_memory(self) -> None:
        local_mission = {
            "id": "mission-portal-local",
            "title": "Portal discovery",
            "owner": "codex_mcp_operator",
            "targetId": "codex_mcp_portal",
            "reportType": "trading_system_discovery_report",
            "status": "completed",
        }
        keyword_only_mission = {
            "id": "mission-keyword-leak",
            "title": "Codex MCP portal discovery",
            "owner": "codex_mcp_operator",
            "targetId": "left_server_racks",
            "reportType": "trading_system_discovery_report",
            "status": "completed",
        }
        meetings = [
            {"id": "meeting-prop", "linkedPropId": "codex_mcp_portal"},
            {"id": "meeting-mission", "linkedMissionId": "mission-portal-local"},
            {
                "id": "meeting-participant-leak",
                "participants": ["codex_mcp_operator"],
                "title": "Unrelated work",
            },
            {"id": "meeting-keyword-leak", "title": "Codex MCP portal discovery"},
        ]
        memory_index = {
            "items": [
                {"id": "memory-prop", "title": "Explicit prop", "linkedPropIds": ["codex_mcp_portal"]},
                {"id": "memory-mission", "title": "Explicit mission", "linkedMissionId": "mission-portal-local"},
                {"id": "memory-keyword-leak", "title": "Codex MCP portal discovery"},
                {"id": "memory-wrong-prop", "title": "Wrong prop", "linkedPropIds": ["left_server_racks"]},
            ],
        }
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "codex_mcp_portal", "label": "Portal"}),
            mock.patch.object(self.bridge, "find_property_role", return_value={}),
            mock.patch.object(self.bridge, "routing_keywords_for_prop", return_value=["codex", "portal"]),
            mock.patch.object(self.bridge, "load_missions", return_value=[local_mission, keyword_only_mission]),
            mock.patch.object(self.bridge, "load_agent_events", return_value=[
                {"id": "event-local", "missionId": "mission-portal-local"},
                {"id": "event-target", "targetId": "codex_mcp_portal"},
                {"id": "event-keyword-leak", "title": "Codex portal", "targetId": "left_server_racks"},
            ]),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[]),
            mock.patch.object(self.bridge, "load_meeting_records", return_value=meetings),
            mock.patch.object(self.bridge, "load_memory_index", return_value=memory_index),
            mock.patch.object(self.bridge, "search_memory_items") as keyword_memory_search,
            mock.patch.object(self.bridge, "bridge_status", return_value={"codex": {"status": "ready_guarded"}}),
            mock.patch.object(self.bridge, "capability_registry", return_value={"capabilities": [], "bridge": {}}),
            mock.patch.object(self.bridge, "find_dashboard_connection_profile", return_value={}),
            mock.patch.object(self.bridge, "workflow_dashboard_read_model", return_value={}),
        ):
            model = self.bridge.prop_report("codex_mcp_portal")

        self.assertEqual([row["id"] for row in model["missions"]], ["mission-portal-local"])
        self.assertEqual([row["id"] for row in model["events"]], ["event-local", "event-target"])
        self.assertEqual([row["id"] for row in model["meetings"]], ["meeting-prop", "meeting-mission"])
        self.assertEqual([row["id"] for row in model["memory"]], ["memory-prop", "memory-mission"])
        keyword_memory_search.assert_not_called()

    def test_portal_sheet_template_is_unconnected_and_never_accepts_frontend_credentials(self) -> None:
        with (
            mock.patch.object(self.bridge, "find_property_role", return_value={}),
            mock.patch.object(
                self.bridge,
                "load_dashboard_workflow_settings",
                return_value=self.bridge._default_dashboard_workflow_settings(),
            ),
        ):
            model = self.bridge.workflow_dashboard_read_model(
                "codex_mcp_portal",
                reports=[],
                bridge=self.ready_bridge(),
            )
        self.assertEqual(model["sheetTemplate"]["connectionStatus"], "not_connected")
        self.assertFalse(model["sheetTemplate"]["credentialsAcceptedByFrontend"])
        self.assertIn("source_url", model["sheetTemplate"]["columns"])
        template_path = PROJECT_ROOT / "contracts" / "research" / "trading-system-sheet-template.csv"
        with template_path.open("r", encoding="utf-8", newline="") as handle:
            bilingual_headers = next(csv.reader(handle))
        template_field_ids = [header.split("/", 1)[0] for header in bilingual_headers]
        self.assertEqual(len(template_field_ids), 42)
        self.assertEqual(model["sheetTemplate"]["columns"], template_field_ids)
        self.assertFalse(model["schedule"]["enabled"])
        self.assertFalse(model["schedule"]["automaticRunsImplemented"])

    def test_schedule_persists_user_request_but_effective_scheduler_stays_off(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "dashboard-workflow-settings.json"
            with (
                mock.patch.object(self.bridge, "DASHBOARD_WORKFLOW_SETTINGS_PATH", settings_path),
                mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "codex_mcp_portal"}),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                result = self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "save_discovery_schedule",
                        "form": {"enabled": True, "times": ["09:00", "18:30"]},
                    },
                )
                stored = self.bridge.read_json(settings_path, {})
        self.assertTrue(result["ok"])
        self.assertTrue(result["schedule"]["requestedEnabled"])
        self.assertFalse(result["schedule"]["enabled"])
        self.assertFalse(result["schedule"]["automaticExternalActions"])
        self.assertEqual(stored["discoverySchedule"]["times"], ["09:00", "18:30"])

    def test_schedule_rejects_invalid_time_instead_of_silently_enabling(self) -> None:
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "codex_mcp_portal"}),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "save_discovery_schedule",
                        "form": {"enabled": True, "times": ["25:99"]},
                    },
                )

    def test_build_action_dispatches_source_only_prompt_and_no_mt_execution(self) -> None:
        captured: dict = {}

        def fake_run_bridge_task(payload: dict, **kwargs) -> dict:
            captured.update(payload)
            captured["trustedWorkflowContext"] = kwargs.get("trusted_workflow_context")
            return {
                "ok": True,
                "kind": "mission_auto_queued",
                "mission": {"id": "mission-source-only-1"},
            }

        transfer = {
            "mode": "agent_mission_report",
            "sourceReportId": "research-report-1",
            "sourcePropId": "left_server_racks",
            "sourceMissionId": "mission-research-1",
            "transferAgentId": "ea_developer",
            "sourceOwnerAgentId": "mission_archivist",
            "targetPropId": "right_server_racks",
            "handoffMissionId": "mission-handoff-build-1",
            "status": "recorded",
        }
        delivered = [{
            "reportId": "research-report-1",
            "sourcePropId": "left_server_racks",
            "title": "Verified system",
            "summary": "Evidence-backed rules",
            "type": "trading_system_research_report",
            "status": "ready",
            "agentTransfer": transfer,
        }]
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "right_server_racks"}),
            mock.patch.object(self.bridge, "_workflow_transfer_sources", return_value=delivered),
            mock.patch.object(self.bridge, "run_bridge_task", side_effect=fake_run_bridge_task),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            result = self.bridge.run_dashboard_workflow_action(
                "right_server_racks",
                {
                    "actionId": "build_strategy_code",
                    "form": {
                        "sourceReportId": "research-report-1",
                        "platform": "mt4",
                        "brief": "Use fixed lot input",
                    },
                },
            )
        self.assertTrue(result["ok"])
        self.assertEqual(captured["toolId"], "codex_cli_task")
        self.assertEqual(captured["agentId"], "ea_developer")
        self.assertEqual(captured["targetId"], "right_server_racks")
        self.assertIn("SOURCE-ONLY / UNCOMPILED", captured["prompt"])
        self.assertIn("ห้าม Compile, Backtest, Optimize", captured["prompt"])
        self.assertIn("project-relative", captured["prompt"])
        lineage = captured["trustedWorkflowContext"]
        self.assertEqual(lineage["schemaVersion"], "dashboard-workflow-lineage-v1")
        self.assertEqual(lineage["propId"], "right_server_racks")
        self.assertEqual(lineage["actionId"], "build_strategy_code")
        self.assertEqual(lineage["source"]["reportId"], "research-report-1")
        self.assertEqual(lineage["source"]["missionId"], "mission-research-1")
        self.assertEqual(lineage["source"]["transferAgentId"], "ea_developer")
        self.assertEqual(lineage["agentTransfer"]["handoffMissionId"], "mission-handoff-build-1")
        self.assertRegex(lineage["inputDigest"], r"^[0-9a-f]{64}$")

    def test_public_discovery_uses_web_research_and_forbids_external_submission(self) -> None:
        captured: dict = {}

        def fake_run_bridge_task(payload: dict, **kwargs) -> dict:
            captured.update(payload)
            return {"ok": True, "kind": "mission_auto_queued", "mission": {"id": "mission-web-1"}}

        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "codex_mcp_portal"}),
            mock.patch.object(self.bridge, "run_bridge_task", side_effect=fake_run_bridge_task),
            mock.patch.object(self.bridge, "append_audit"),
        ):
            self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {"query": "public trend following systems", "market": "Forex"},
                },
            )
        self.assertEqual(captured["toolId"], "codex_web_research")
        self.assertEqual(captured["agentId"], "codex_mcp_operator")
        self.assertIn("ห้าม Sign in", captured["prompt"])
        self.assertIn("ห้ามกรอกฟอร์ม", captured["prompt"])
        self.assertIn("ยังไม่มี Adapter", captured["prompt"])

    def test_unknown_form_fields_and_secrets_are_rejected_before_dispatch(self) -> None:
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "codex_mcp_portal"}),
            mock.patch.object(self.bridge, "run_bridge_task") as runner,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "discover_trading_systems",
                        "form": {"apiToken": "do-not-accept"},
                    },
                )
            with self.assertRaises(self.bridge.RequestError):
                self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "discover_trading_systems",
                        "form": {"query": "api_key=abcdefghijklmnop"},
                    },
                )
        runner.assert_not_called()

    def test_source_report_must_have_completed_agent_handoff(self) -> None:
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "left_server_racks"}),
            mock.patch.object(self.bridge, "_workflow_transfer_sources", return_value=[]),
            mock.patch.object(self.bridge, "run_bridge_task") as runner,
            mock.patch.object(self.bridge, "append_audit"),
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge.run_dashboard_workflow_action(
                    "left_server_racks",
                    {
                        "actionId": "deep_research_system",
                        "form": {"sourceReportId": "unrelated-report-1"},
                    },
                )
        runner.assert_not_called()

    def test_dashboard_identity_is_independent_and_has_no_pipeline_fields(self) -> None:
        with mock.patch.object(self.bridge, "find_property_role", return_value={
            "workflowDashboard": {"id": "ea_indicator_builder", "displayOrder": 3},
        }):
            model = self.bridge.workflow_dashboard_read_model(
                "right_server_racks",
                reports=[],
                bridge=self.ready_bridge(),
            )
        self.assertEqual(model["dashboardId"], "ea_indicator_builder")
        self.assertEqual(model["displayOrder"], 3)
        self.assertTrue(model["independent"])
        self.assertEqual(model["coordinationMode"], "agent_mission_only")
        self.assertTrue(model["agentTransferOnly"])
        self.assertFalse(model["directDashboardDependency"])
        self.assertNotIn("pipelineId", model)
        self.assertNotIn("pipelineStage", model)
        self.assertNotIn("pipelineOrder", model)
        self.assertNotIn("upstreamSources", model)

    def test_blocked_or_wrong_type_reports_are_not_selectable(self) -> None:
        reports = [
            {
                "id": "blocked-discovery",
                "linkedPropId": "codex_mcp_portal",
                "type": "trading_system_discovery_report",
                "status": "blocked",
            },
            {
                "id": "wrong-type",
                "linkedPropId": "codex_mcp_portal",
                "type": "dashboard_connection_report",
                "status": "ready",
            },
            {
                "id": "ready-discovery",
                "linkedPropId": "codex_mcp_portal",
                "linkedMissionId": "mission-ready-discovery",
                "type": "trading_system_discovery_report",
                "ownerAgentId": "codex_mcp_operator",
                "status": "ready",
                "title": "Ready",
            },
        ]
        source_mission = {
            "id": "mission-ready-discovery",
            "owner": "codex_mcp_operator",
            "targetId": "codex_mcp_portal",
            "status": "completed",
            "reportIds": ["ready-discovery"],
        }
        transfer = {
            "mode": "agent_mission_report",
            "sourceReportId": "ready-discovery",
            "sourcePropId": "codex_mcp_portal",
            "sourceMissionId": "mission-ready-discovery",
            "transferAgentId": "mission_archivist",
            "sourceOwnerAgentId": "codex_mcp_operator",
            "targetPropId": "left_server_racks",
            "handoffMissionId": "mission-handoff-research",
            "status": "recorded",
        }
        handoff_mission = {
            "id": "mission-handoff-research",
            "owner": "mission_archivist",
            "targetId": "left_server_racks",
            "toolId": "agent_report_transfer",
            "status": "completed",
            "agentTransfer": transfer,
        }
        rows_without_handoff = self.bridge._workflow_transfer_sources(
            "left_server_racks",
            reports=reports,
            action_id="deep_research_system",
            missions=[source_mission],
        )
        self.assertEqual(rows_without_handoff, [])
        rows = self.bridge._workflow_transfer_sources(
            "left_server_racks",
            reports=reports,
            action_id="deep_research_system",
            missions=[source_mission, handoff_mission],
        )
        self.assertEqual([row["reportId"] for row in rows], ["ready-discovery"])
        self.assertEqual(rows[0]["agentTransfer"]["handoffMissionId"], "mission-handoff-research")

    def test_report_projection_preserves_safe_workflow_lineage_without_inputs(self) -> None:
        context = {
            "schemaVersion": "dashboard-workflow-lineage-v1",
            "propId": "right_tool_console",
            "actionId": "prepare_backtest_plan",
            "source": {
                "reportId": "build-1",
                "propId": "right_server_racks",
                "missionId": "mission-build-1",
                "transferAgentId": "backtest_analyst",
                "type": "ea_build_report",
                "status": "ready",
            },
            "agentTransfer": {
                "mode": "agent_mission_report",
                "sourceReportId": "build-1",
                "sourcePropId": "right_server_racks",
                "sourceMissionId": "mission-build-1",
                "transferAgentId": "backtest_analyst",
                "sourceOwnerAgentId": "ea_developer",
                "targetPropId": "right_tool_console",
                "handoffMissionId": "mission-handoff-backtest-1",
                "status": "recorded",
            },
            "inputs": {"market": "XAUUSD", "brief": "private local intent"},
            "inputDigest": "a" * 64,
            "submittedAt": "2026-08-08T00:00:00+00:00",
        }
        model = self.bridge.report_read_model_item({
            "id": "report-1",
            "type": "ea_experiment_report",
            "workflowContext": context,
        })
        self.assertEqual(model["workflowContext"]["actionId"], "prepare_backtest_plan")
        self.assertEqual(model["workflowContext"]["source"]["reportId"], "build-1")
        self.assertEqual(model["agentTransfer"]["handoffMissionId"], "mission-handoff-backtest-1")
        self.assertNotIn("inputs", model["workflowContext"])
        self.assertEqual(model["workflowContext"]["inputFields"], ["brief", "market"])

    def test_validation_failures_are_audited_without_form_values(self) -> None:
        events = []
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "codex_mcp_portal"}),
            mock.patch.object(self.bridge, "append_audit", side_effect=events.append),
        ):
            with self.assertRaises(self.bridge.RequestError):
                self.bridge.run_dashboard_workflow_action(
                    "codex_mcp_portal",
                    {
                        "actionId": "discover_trading_systems",
                        "form": {"query": "api_key=abcdefghijklmnop"},
                    },
                )
        rejected = [event for event in events if event.get("type") == "dashboard.workflow_action_rejected"]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reason"], "invalid_form")
        self.assertNotIn("api_key", str(rejected[0]))

    def test_workflow_idempotency_replay_returns_the_existing_mission(self) -> None:
        events = []
        existing = {"id": "mission-existing-1"}

        def fake_run_bridge_task(payload: dict, **kwargs) -> dict:
            self.assertEqual(payload["idempotencyKey"], "workflow-click-1")
            self.assertEqual(kwargs["trusted_workflow_context"]["actionId"], "discover_trading_systems")
            return {"ok": True, "kind": "mission_auto_queued", "mission": existing}

        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "codex_mcp_portal"}),
            mock.patch.object(self.bridge, "find_mission_by_idempotency", return_value=existing),
            mock.patch.object(self.bridge, "run_bridge_task", side_effect=fake_run_bridge_task),
            mock.patch.object(self.bridge, "append_audit", side_effect=events.append),
        ):
            result = self.bridge.run_dashboard_workflow_action(
                "codex_mcp_portal",
                {
                    "actionId": "discover_trading_systems",
                    "form": {"query": "public trend systems"},
                    "idempotencyKey": "workflow-click-1",
                },
            )
        self.assertTrue(result["idempotentReplay"])
        self.assertEqual(result["mission"]["id"], "mission-existing-1")
        self.assertTrue(any(event.get("type") == "dashboard.workflow_action_replayed" for event in events))

    def test_memory_frontend_projection_never_exposes_source_path(self) -> None:
        model = self.bridge.memory_read_model_item({
            "id": "memory-1",
            "kind": "report",
            "title": "Private artifact",
            "summary": "Safe summary",
            "sourcePath": "C:\\Users\\META\\private\\report.json",
            "agents": ["mission_archivist"],
            "tags": ["research"],
        })
        self.assertNotIn("sourcePath", model)
        self.assertNotIn("C:\\Users", str(model))
        self.assertTrue(model["hasLocalSource"])
        self.assertFalse(model["safety"]["localPathExposed"])

    def test_new_dashboard_tabs_actions_and_agent_preferences_are_canonical(self) -> None:
        expected_tabs = {
            "left_audit_crystals": ["discoveries", "evidence", "schedule", "archive"],
            "left_signal_cube": ["today", "pair_bias", "horizons", "schedule_history"],
            "terminal_workstation": ["source", "development_brief", "performance_goals", "outputs"],
            "right_status_crystals": ["vps", "hq_bridge", "agent_settings", "activity_history"],
        }
        for prop_id, tab_ids in expected_tabs.items():
            self.assertEqual(
                [tab["id"] for tab in self.bridge.DASHBOARD_WORKFLOW_TABS[prop_id]],
                tab_ids,
            )
        preference_fields = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["save_agent_preferences"]["formFields"]
        self.assertEqual(
            [field["id"] for field in preference_fields],
            [
                "language",
                "modelTier",
                "tokenBudget",
                "timeoutSeconds",
                "outputLimitChars",
                "rateReservePercent",
            ],
        )
        preferences = self.bridge._dashboard_agent_preferences_read_model({
            "agentPreferences": {
                "language": "en",
                "modelTier": "risk_quality",
                "tokenBudget": 999999,
                "timeoutSeconds": 999999,
                "outputLimitChars": 999999,
                "rateReservePercent": 999,
                "providerModelId": "must-not-pass",
            },
        })
        self.assertEqual(preferences["language"], "en")
        self.assertEqual(preferences["modelTier"], "risk_quality")
        self.assertEqual(preferences["tokenBudget"], 100000)
        self.assertEqual(preferences["timeoutSeconds"], 1800)
        self.assertEqual(preferences["outputLimitChars"], 100000)
        self.assertEqual(preferences["rateReservePercent"], 90)
        self.assertNotIn("providerModelId", preferences)
        self.assertFalse(preferences["providerModelIdAccepted"])

    def test_http_sanitization_preserves_nested_workflow_select_options(self) -> None:
        """The final send_json projection must not turn safe options into placeholders."""
        model = self.bridge.workflow_dashboard_read_model(
            "left_audit_crystals",
            reports=[],
            bridge={
                "status": "guarded",
                "codex": {"status": "ready_guarded"},
                "actionPolicy": {"ready": True},
            },
        )
        projected = self.bridge.sanitize_json_value(
            {"workflowDashboard": model},
            collection_limit=1000,
            string_limit=20000,
        )
        action = next(
            item
            for item in projected["workflowDashboard"]["actions"]
            if item["id"] == "discover_new_indicators"
        )
        platform = next(field for field in action["formFields"] if field["id"] == "platform")
        self.assertEqual(platform["options"], ["any", "mt4", "mt5", "tradingview"])
        self.assertNotIn("[TRUNCATED]", json.dumps(action))

    def test_fx_bias_always_has_exactly_28_pairs_and_never_fabricates_missing_rows(self) -> None:
        empty = self.bridge._fx_bias_read_model([])
        self.assertEqual(empty["pairCount"], 28)
        self.assertEqual([row["pair"] for row in empty["pairs"]], list(self.bridge.FX_BIAS_PAIRS))
        self.assertEqual(empty["verifiedPairCount"], 0)
        self.assertTrue(all(row["shortBias"] == "unknown" for row in empty["pairs"]))
        self.assertFalse(empty["fabricatedData"])

        report = {
            "id": "fx-bias-1",
            "linkedPropId": "left_signal_cube",
            "type": "fx_news_bias_report",
            "status": "ready",
            "workflowContext": {
                "propId": "left_signal_cube",
                "actionId": "build_fx_pair_bias",
            },
            "metrics": {
                "pairBias": [
                    {
                        "pair": "EURUSD",
                        "short": "buy",
                        "medium": "neutral",
                        "long": "sell",
                        "confidence": 77,
                        "sourceLinks": [{"label": "Public source", "url": "https://example.com/fx"}],
                    },
                    {
                        "pair": "GBPUSD",
                        "short": "bullish",
                        "sourceLinks": [],
                    },
                ],
            },
        }
        model = self.bridge._fx_bias_read_model([report])
        eurusd = next(row for row in model["pairs"] if row["pair"] == "EURUSD")
        gbpusd = next(row for row in model["pairs"] if row["pair"] == "GBPUSD")
        self.assertEqual((eurusd["shortBias"], eurusd["mediumBias"], eurusd["longBias"]), ("bullish", "neutral", "bearish"))
        self.assertEqual(eurusd["status"], "verified")
        self.assertEqual(gbpusd["status"], "pending")
        self.assertEqual(gbpusd["shortBias"], "unknown")
        self.assertEqual(model["verifiedPairCount"], 1)
        self.assertFalse(model["complete28"])

    def test_indicator_news_and_terminal_actions_dispatch_only_the_canonical_guarded_tools(self) -> None:
        captured: list[dict] = []

        def fake_run(payload: dict, **kwargs) -> dict:
            captured.append({**payload, "workflowContext": kwargs.get("trusted_workflow_context")})
            return {"ok": True, "kind": "mission_auto_queued", "mission": {"id": f"mission-{len(captured)}"}}

        source_transfer = {
            "mode": "agent_mission_report",
            "sourceReportId": "news-report-1",
            "sourcePropId": "left_signal_cube",
            "sourceMissionId": "mission-news-source",
            "transferAgentId": "codex_mcp_operator",
            "sourceOwnerAgentId": "codex_mcp_operator",
            "targetPropId": "left_signal_cube",
            "handoffMissionId": "mission-news-handoff",
            "status": "recorded",
        }
        source_rows = [{
            "reportId": "news-report-1",
            "sourcePropId": "left_signal_cube",
            "type": "fx_news_bias_report",
            "status": "ready",
            "title": "Daily news",
            "summary": "Evidence-backed news",
            "platforms": [],
            "agentTransfer": source_transfer,
        }]
        workspace_rows = [{
            "id": "workspace-source-1",
            "sourceId": "workspace-source-1",
            "label": "Expert.mq4",
            "platform": "mql4",
            "storageRef": "workspace/Expert.mq4",
            "byteSize": 120,
        }]
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "any"}),
            mock.patch.object(self.bridge, "_workflow_action_contract_gate", return_value={"allowed": True}),
            mock.patch.object(self.bridge, "run_bridge_task", side_effect=fake_run),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[{
                "id": "news-report-1",
                "linkedPropId": "left_signal_cube",
                "type": "fx_news_bias_report",
                "status": "ready",
                "title": "Daily news",
                "summary": "Evidence-backed news",
            }]),
            mock.patch.object(self.bridge, "_workspace_source_catalog", return_value=workspace_rows),
        ):
            self.bridge.run_dashboard_workflow_action(
                "left_audit_crystals",
                {"actionId": "discover_new_indicators", "form": {"query": "public trend indicator"}},
            )
            with mock.patch.object(self.bridge, "_workflow_transfer_sources", return_value=source_rows):
                self.bridge.run_dashboard_workflow_action(
                    "left_signal_cube",
                    {"actionId": "build_fx_pair_bias", "form": {"sourceReportId": "news-report-1"}},
                )
            self.bridge.run_dashboard_workflow_action(
                "terminal_workstation",
                {
                    "actionId": "inspect_ea_source",
                    "form": {"workspaceSourceId": "workspace-source-1", "platform": "mql4"},
                },
            )
        self.assertEqual([item["toolId"] for item in captured], ["codex_web_research", "codex_web_research", "codex_cli_task"])
        self.assertEqual([item["targetId"] for item in captured], ["left_audit_crystals", "left_signal_cube", "terminal_workstation"])
        self.assertIn("ห้าม Sign in", captured[0]["prompt"])
        self.assertIn("28 คู่เงิน", captured[1]["prompt"])
        self.assertEqual(captured[1]["prompt"].count("EURUSD"), 1)
        self.assertIn("SOURCE-ONLY", captured[2]["prompt"])
        self.assertEqual(captured[2]["workflowContext"]["source"]["artifactId"], "workspace-source-1")

    def test_terminal_source_selection_requires_exactly_one_backend_approved_source(self) -> None:
        workspace_rows = [{
            "id": "workspace-source-1",
            "sourceId": "workspace-source-1",
            "label": "Expert.mq4",
            "platform": "mql4",
            "storageRef": "workspace/Expert.mq4",
            "byteSize": 120,
        }]
        with mock.patch.object(self.bridge, "_workspace_source_catalog", return_value=workspace_rows):
            selected = self.bridge._workflow_selected_source(
                "terminal_workstation",
                "inspect_ea_source",
                {"workspaceSourceId": "workspace-source-1", "platform": "mql4"},
            )
            self.assertEqual(selected["artifactId"], "workspace-source-1")
            self.assertEqual(selected["structuredPayload"]["workspaceReference"], "workspace/Expert.mq4")
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._workflow_selected_source(
                    "terminal_workstation",
                    "inspect_ea_source",
                    {"workspaceSourceId": "workspace-source-1", "platform": "mql5"},
                )
            with self.assertRaises(self.bridge.RequestError):
                self.bridge._workflow_selected_source(
                    "terminal_workstation",
                    "inspect_ea_source",
                    {"workspaceSourceId": "workspace-source-1", "sourceReportId": "report-1", "platform": "mql4"},
                )
            self.assertIsNone(self.bridge._workflow_selected_source(
                "terminal_workstation",
                "inspect_ea_source",
                {"workspaceSourceId": "../Expert.mq4", "platform": "mql4"},
            ))

    def test_terminal_source_required_error_is_generic_for_report_or_workspace(self) -> None:
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "terminal_workstation"}),
            mock.patch.object(self.bridge, "_workflow_action_contract_gate", return_value={"allowed": True}),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge, "run_bridge_task") as runner,
        ):
            with self.assertRaisesRegex(self.bridge.RequestError, "Source ต้นทาง"):
                self.bridge.run_dashboard_workflow_action(
                    "terminal_workstation",
                    {"actionId": "inspect_ea_source", "form": {"platform": "mql4"}},
                )
        runner.assert_not_called()

    def test_agent_preferences_local_action_is_idempotent_and_never_calls_codex(self) -> None:
        mission = {"id": "mission-pref-1", "reportIds": []}
        report = {"id": "report-pref-1", "type": "ops_overview_report"}
        saved = {
            "language": "th",
            "modelTier": "specialist_fast",
            "tokenBudget": 8000,
            "timeoutSeconds": 90,
            "outputLimitChars": 6000,
            "rateReservePercent": 25,
        }
        existing = [None, mission]
        with (
            mock.patch.object(self.bridge, "find_room_prop", return_value={"id": "right_status_crystals"}),
            mock.patch.object(self.bridge, "_workflow_action_contract_gate", return_value={"allowed": True}),
            mock.patch.object(self.bridge, "find_mission_by_idempotency", side_effect=lambda _key: existing.pop(0)),
            mock.patch.object(self.bridge, "create_mission", return_value=mission),
            mock.patch.object(self.bridge, "create_report", return_value=report) as create_report,
            mock.patch.object(self.bridge, "replace_mission"),
            mock.patch.object(self.bridge, "load_runtime_reports", return_value=[report]),
            mock.patch.object(self.bridge, "_save_dashboard_agent_preferences", return_value=saved) as saver,
            mock.patch.object(self.bridge, "append_agent_event"),
            mock.patch.object(self.bridge, "append_audit"),
            mock.patch.object(self.bridge, "run_bridge_task") as runner,
        ):
            payload = {
                "actionId": "save_agent_preferences",
                "idempotencyKey": "prefs-click-1",
                "form": saved,
            }
            first = self.bridge.run_dashboard_workflow_action("right_status_crystals", payload)
            second = self.bridge.run_dashboard_workflow_action("right_status_crystals", payload)
        self.assertFalse(first["idempotentReplay"])
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(saver.call_count, 1)
        self.assertEqual(create_report.call_count, 1)
        runner.assert_not_called()

    def test_vps_health_is_local_truth_and_unobserved_metrics_remain_null(self) -> None:
        health = self.bridge._safe_vps_hq_health_snapshot({
            "status": "ready",
            "mode": "local",
            "codex": {"status": "ready_guarded"},
            "mcp": {"status": "configured", "configPresent": True},
        })
        self.assertEqual(health["localBridge"]["status"], "ready")
        self.assertEqual(health["vpsMetrics"]["status"], "not_observed")
        self.assertIsNone(health["vpsMetrics"]["cpuPercent"])
        self.assertIsNone(health["vpsMetrics"]["memoryPercent"])
        self.assertFalse(health["credentialsExposed"])
        self.assertFalse(health["rateLimitDetailsIncluded"])

    def test_workspace_source_catalog_is_opaque_and_rejects_wrong_extension_and_secret_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            memory = root / "data" / "memory"
            workspace.mkdir(parents=True)
            memory.mkdir(parents=True)
            (workspace / "GoodExpert.mq4").write_text("int OnInit(){ return(0); }", encoding="utf-8")
            (workspace / "Ignore.txt").write_text("not MQL", encoding="utf-8")
            (workspace / "CredentialEA.mq5").write_text('string api_key="abcdefghijklmnop";', encoding="utf-8")
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "MEMORY_DIR", memory),
            ):
                rows = self.bridge._workspace_source_read_model()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["displayName"], "GoodExpert.mq4")
        self.assertEqual(rows[0]["platform"], "mql4")
        self.assertRegex(rows[0]["sourceId"], r"^workspace-[0-9a-f]{20}$")
        self.assertNotIn("storageRef", rows[0])
        self.assertNotIn("workspaceRelative", rows[0])
        self.assertNotIn(temp_dir, json.dumps(rows))

    def test_report_download_endpoint_and_projection_are_allowlisted_and_path_opaque(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            reports_dir = root / "data" / "runtime" / "reports"
            workspace.mkdir(parents=True)
            reports_dir.mkdir(parents=True)
            source = workspace / "Expert.mq4"
            source_bytes = b"int OnInit(){ return(0); }"
            source.write_bytes(source_bytes)
            report = {
                "id": "terminal-report-1",
                "type": "ea_development_report",
                "linkedPropId": "terminal_workstation",
                "status": "ready",
                "workflowContext": {"propId": "terminal_workstation", "actionId": "develop_ea_source"},
                "artifacts": [{"storageRef": "workspace/Expert.mq4", "label": "Expert source"}],
            }
            (reports_dir / "terminal-report-1.json").write_text(json.dumps(report), encoding="utf-8")
            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "MEMORY_DIR", root / "data" / "memory"),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", reports_dir),
                mock.patch.object(self.bridge, "append_audit"),
            ):
                projected = self.bridge.report_read_model_item(report)
                self.assertEqual(projected["downloadCount"], 1)
                download = projected["downloads"][0]
                self.assertTrue(download["available"])
                self.assertEqual(download["fileName"], "source-output.mq4")
                self.assertEqual(download["contentType"], "text/plain")
                self.assertEqual(download["contentType"], download["mediaType"])
                self.assertNotIn(temp_dir, json.dumps(download))

                server = self.bridge.BridgeHTTPServer(("127.0.0.1", 0), self.bridge.BridgeHandler)
                worker = threading.Thread(target=server.serve_forever, daemon=True)
                worker.start()
                try:
                    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    connection.request("GET", download["url"])
                    response = connection.getresponse()
                    body = response.read()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.getheader("Content-Type"), "text/plain; charset=utf-8")
                    self.assertEqual(response.getheader("Content-Disposition"), 'attachment; filename="source-output.mq4"')
                    self.assertEqual(body, source_bytes)
                    connection.close()
                finally:
                    server.shutdown()
                    server.server_close()
                    worker.join(timeout=5)

    def test_report_download_rejects_traversal_secret_extension_oversize_and_unknown_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir(parents=True)
            (root / "outside.mq4").write_text("int OnInit(){return(0);}", encoding="utf-8")
            (workspace / "config.env").write_text("VALUE=public", encoding="utf-8")
            oversized = workspace / "oversized.mq4"
            with oversized.open("wb") as handle:
                handle.truncate(self.bridge.MAX_REPORT_DOWNLOAD_BYTES + 1)
            unsafe = workspace / "Unsafe.mq4"
            unsafe.write_text('string token="abcdefghijklmnop";', encoding="utf-8")

            def report_for(storage_ref: str) -> dict:
                return {
                    "id": "terminal-report-unsafe",
                    "type": "ea_development_report",
                    "linkedPropId": "terminal_workstation",
                    "status": "ready",
                    "workflowContext": {"propId": "terminal_workstation", "actionId": "develop_ea_source"},
                    "artifacts": [{"storageRef": storage_ref}],
                }

            with (
                mock.patch.object(self.bridge, "PROJECT_ROOT", root),
                mock.patch.object(self.bridge, "MEMORY_DIR", root / "data" / "memory"),
                mock.patch.object(self.bridge, "RUNTIME_REPORTS_DIR", root / "reports"),
            ):
                self.assertEqual(self.bridge.report_download_read_model(report_for("workspace/../outside.mq4")), [])
                self.assertEqual(self.bridge.report_download_read_model(report_for("workspace/config.env")), [])
                self.assertEqual(self.bridge.report_download_read_model(report_for("workspace/oversized.mq4")), [])
                self.assertEqual(self.bridge.report_download_read_model(report_for("workspace/Unsafe.mq4")), [])
                self.assertIsNone(self.bridge.resolve_report_download("missing-report", "artifact-deadbeef"))

    def test_repurposed_props_do_not_receive_legacy_risk_auto_trade_or_mt_snapshot_routes(self) -> None:
        self.assertFalse(self.bridge._workflow_record_matches_prop(
            {"type": "risk_review", "linkedPropId": "left_audit_crystals"},
            "left_audit_crystals",
        ))
        self.assertFalse(self.bridge._workflow_record_matches_prop(
            {"type": "auto_trading_status_report", "linkedPropId": "left_signal_cube"},
            "left_signal_cube",
        ))
        self.assertFalse(self.bridge._workflow_record_matches_prop(
            {"type": "indicator_scout_report", "linkedPropId": "left_audit_crystals"},
            "left_audit_crystals",
        ))
        self.assertTrue(self.bridge._workflow_record_matches_prop(
            {
                "type": "indicator_scout_report",
                "linkedPropId": "left_audit_crystals",
                "workflowContext": {"propId": "left_audit_crystals", "actionId": "discover_new_indicators"},
            },
            "left_audit_crystals",
        ))
        self.assertNotIn("left_signal_cube", self.bridge.METATRADER_TARGET_PROP_IDS)
        self.assertEqual(self.bridge.AUTO_TRADING_STATUS_PROP_ID, self.bridge.AI_TRADE_COUNCIL_PROP_ID)
        self.assertNotIn("risk_review", self.bridge.DASHBOARD_WORKFLOW_REPORT_TYPES["right_status_crystals"])
        self.assertNotIn("auto_trading_status_report", self.bridge.DASHBOARD_WORKFLOW_REPORT_TYPES["right_status_crystals"])

    def test_legacy_specialist_routes_are_canonicalized_before_mission_and_event_routing(self) -> None:
        stale_contract = {
            "managerAutoDelegation": {
                "specialistRules": [
                    {
                        "id": "risk_review",
                        "priority": 100,
                        "keywords": ["risk", "approval"],
                        "agentId": "risk_guard",
                        "targetPropId": "left_audit_crystals",
                        "reportType": "risk_review",
                    },
                    {
                        "id": "ea_runtime_status",
                        "priority": 95,
                        "keywords": ["terminal status", "mt4 status"],
                        "agentId": "vps_watch",
                        "targetPropId": "left_signal_cube",
                        "reportType": "auto_trading_status_report",
                    },
                    {
                        "id": "telegram_draft_old",
                        "priority": 70,
                        "keywords": ["telegram", "alert"],
                        "agentId": "telegram_ops",
                        "targetPropId": "right_tool_console",
                        "reportType": "telegram_tool_report",
                    },
                ]
            }
        }
        with mock.patch.object(self.bridge, "load_orchestration_contract", return_value=stale_contract):
            self.assertEqual(
                self.bridge.target_for_agent_goal("risk_guard", "risk approval"),
                "mission_strategy_table",
            )
            self.assertEqual(
                self.bridge.target_for_agent_goal("vps_watch", "check MT4 terminal status"),
                self.bridge.AI_TRADE_COUNCIL_PROP_ID,
            )
            self.assertEqual(
                self.bridge.target_for_agent_goal("telegram_ops", "prepare Telegram alert"),
                "mission_strategy_table",
            )
            self.assertNotIn("left_audit_crystals", self.bridge.allowed_targets_for_agent("risk_guard"))
            self.assertNotIn("left_signal_cube", self.bridge.allowed_targets_for_agent("vps_watch"))
            self.assertNotIn("right_tool_console", self.bridge.allowed_targets_for_agent("telegram_ops"))

        self.assertEqual(self.bridge.role_default_target_id("risk_guard"), "mission_strategy_table")
        self.assertEqual(self.bridge.role_default_target_id("vps_watch"), "right_status_crystals")
        self.assertEqual(self.bridge.role_default_target_id("telegram_ops"), "mission_strategy_table")
        self.assertEqual(self.bridge.pick_target_for_task("review risk approval secret"), "mission_strategy_table")
        self.assertEqual(
            self.bridge.pick_target_for_task("check MT4 terminal status"),
            self.bridge.AI_TRADE_COUNCIL_PROP_ID,
        )
        self.assertEqual(self.bridge.pick_target_for_task("prepare Telegram alert"), "mission_strategy_table")

        # Direct mission creation is the last backend boundary used by mission
        # events/reports.  Even an old caller cannot persist a repurposed prop.
        mission_payloads = [
            ("risk_guard", "left_audit_crystals", "risk_review", "mission_strategy_table"),
            (
                "vps_watch",
                "left_signal_cube",
                "auto_trading_status_report",
                self.bridge.AI_TRADE_COUNCIL_PROP_ID,
            ),
            ("telegram_ops", "right_tool_console", "telegram_tool_report", "mission_strategy_table"),
        ]
        for agent_id, stale_target, report_type, expected_target in mission_payloads:
            with self.subTest(agent_id=agent_id):
                with (
                    mock.patch.object(self.bridge, "get_tool_policy", return_value={}),
                    mock.patch.object(self.bridge, "resolve_budget", return_value=("specialist_fast", {})),
                    mock.patch.object(self.bridge, "find_mission_by_idempotency", return_value=None),
                    mock.patch.object(self.bridge, "load_missions", return_value=[]),
                    mock.patch.object(self.bridge, "save_missions"),
                    mock.patch.object(self.bridge, "append_audit"),
                ):
                    mission = self.bridge.create_mission({
                        "prompt": f"route check for {agent_id}",
                        "agentId": agent_id,
                        "toolId": "manager_mission",
                        "targetId": stale_target,
                        "reportType": report_type,
                    })
                self.assertEqual(mission["targetId"], expected_target)

    def test_metatrader_discovery_preserves_existing_prop_and_adds_experiment_lab(self) -> None:
        self.assertIn("right_server_racks", self.bridge.METATRADER_TARGET_PROP_IDS)
        self.assertIn("right_tool_console", self.bridge.METATRADER_TARGET_PROP_IDS)


if __name__ == "__main__":
    unittest.main()
