from __future__ import annotations

import csv
import importlib.util
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"

FX_PAIR_UNIVERSE = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD", "CADCHF", "CADJPY",
    "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD",
    "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
]

WORKFLOW_DEVICE_TAB_IDS = {
    "codex_mcp_portal": ["systems", "ea_updates", "schedule", "catalog"],
    "left_server_racks": ["research_queue", "verified_archive", "application", "evidence"],
    "right_server_racks": ["builder", "code_review", "compile", "outputs"],
    "right_tool_console": ["backtest", "optimization", "ea_discovery", "history"],
    "left_audit_crystals": ["discoveries", "evidence", "schedule", "archive"],
    "left_signal_cube": ["pair_bias", "today", "history"],
    "terminal_workstation": ["source", "development_brief", "performance_goals", "outputs"],
    "right_status_crystals": ["connections"],
}

WORKFLOW_DEVICE_LEFT_RAIL_IDS = {
    "codex_mcp_portal": ["schedule", "quota", "agent_handoff"],
    "left_server_racks": ["quota", "agent_handoff"],
    "right_server_racks": ["quota", "agent_handoff"],
    "right_tool_console": ["quota", "agent_handoff"],
    "left_audit_crystals": ["schedule", "quota"],
    "left_signal_cube": ["schedule", "refresh", "source_status"],
    "terminal_workstation": ["quota", "agent_handoff"],
    "right_status_crystals": ["settings", "quota"],
}

WORKFLOW_DEVICE_SCHEDULE_ACTIONS = {
    "codex_mcp_portal": "save_discovery_schedule",
    "left_audit_crystals": "save_indicator_scout_schedule",
}

NEW_DEVICE_ACTIONS = {
    "left_audit_crystals": {
        "discover_new_indicators": ("codex_mcp_operator", "indicator_scout_report"),
        "save_indicator_scout_schedule": ("codex_mcp_operator", "indicator_scout_report"),
    },
    "terminal_workstation": {
        "inspect_ea_source": ("ea_developer", "ea_development_report"),
        "develop_ea_source": ("ea_developer", "ea_development_report"),
        "propose_ea_performance_improvements": ("ea_developer", "ea_development_report"),
    },
    "right_status_crystals": {
        "refresh_vps_hq_status": ("vps_watch", "ops_overview_report"),
        "save_agent_preferences": ("manager", "ops_overview_report"),
    },
}


def load_json(relative_path: str) -> dict:
    return json.loads((PROJECT_ROOT / relative_path).read_text(encoding="utf-8"))


def load_bridge():
    spec = importlib.util.spec_from_file_location("metafx_workflow_contract_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DashboardWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_bridge()
        cls.role_map = load_json("contracts/props/property-role-map.json")
        cls.connections = load_json("contracts/connections/dashboard-connection-contract.json")
        cls.reports = load_json("contracts/reports/report-contract.json")
        cls.permissions = load_json("contracts/tools/tool-permission-contract.json")
        cls.missions = load_json("contracts/missions/mission-contract.json")
        cls.room = load_json("contracts/rooms/command-room.json")
        cls.agents = load_json("contracts/agents/agents.json")
        cls.orchestration = load_json("contracts/orchestration/orchestration-contract.json")

    def test_workflow_devices_have_their_canonical_tabs(self) -> None:
        for prop_id, tab_ids in WORKFLOW_DEVICE_TAB_IDS.items():
            role = self.role_map["properties"][prop_id]
            connection = self.connections["profiles"][prop_id]
            backend_tabs = self.bridge.DASHBOARD_WORKFLOW_TABS[prop_id]
            self.assertEqual([item["id"] for item in role["localTabs"]], tab_ids)
            self.assertEqual([item["id"] for item in connection["localTabs"]], tab_ids)
            self.assertEqual([item["id"] for item in backend_tabs], tab_ids)
            self.assertEqual(role["defaultTab"], tab_ids[0])
            self.assertEqual(len(set(tab_ids)), len(tab_ids))
            expected_count = 3 if prop_id == "left_signal_cube" else 1 if prop_id == "right_status_crystals" else 4
            self.assertEqual(len(tab_ids), expected_count)

    def test_workflow_devices_open_on_main_work_and_only_legacy_devices_end_with_history(self) -> None:
        self.assertEqual(self.role_map["version"], "property-role-map-v002")
        for prop_id, tab_ids in WORKFLOW_DEVICE_TAB_IDS.items():
            role = self.role_map["properties"][prop_id]
            tabs = role["localTabs"]
            ux = role["dashboardUx"]

            self.assertEqual(role["defaultTab"], tab_ids[0])
            self.assertEqual(ux["mainWorkTabId"], tab_ids[0])
            if prop_id == "right_status_crystals":
                self.assertIsNone(ux["historyReportTabId"])
                self.assertIsNone(ux["historyReportTabPosition"])
                self.assertNotIn("ประวัติ", " ".join(item["labelTh"] for item in tabs))
            elif prop_id == "left_signal_cube":
                self.assertEqual(tabs[-1]["labelTh"], "ประวัติข่าว")
            else:
                self.assertEqual(ux["historyReportTabId"], tab_ids[-1])
                self.assertEqual(ux["historyReportTabPosition"], "last")
                self.assertEqual(tabs[-1]["labelTh"], "ประวัติและรายงาน")
            if prop_id == "left_signal_cube":
                self.assertEqual(tabs[0]["actionIds"], [])
            else:
                self.assertTrue(tabs[0]["actionIds"], prop_id)
            self.assertLessEqual(len(tabs[0]["labelTh"]), 24)
            for tab in tabs:
                self.assertLessEqual(len(tab["labelTh"]), 24)
                self.assertLessEqual(len(tab["purpose"]), 80)
                plain_text = f"{tab['labelTh']} {tab['purpose']}".lower()
                for forbidden in ("pipeline", "upstream", "downstream", "auto pull"):
                    self.assertNotIn(forbidden, plain_text)

    def test_left_rail_metadata_only_exposes_relevant_safe_sections(self) -> None:
        supported_sections = {"settings", "schedule", "refresh", "quota", "agent_handoff", "workflow_method", "source_status"}
        handoff_props = {
            "codex_mcp_portal",
            "left_server_racks",
            "right_server_racks",
            "right_tool_console",
            "terminal_workstation",
        }
        for prop_id, expected_ids in WORKFLOW_DEVICE_LEFT_RAIL_IDS.items():
            role = self.role_map["properties"][prop_id]
            ux = role["dashboardUx"]
            sections = ux["leftRailSections"]
            section_ids = [item["id"] for item in sections]

            self.assertEqual(section_ids, expected_ids)
            self.assertTrue(set(section_ids).issubset(supported_sections))
            self.assertEqual(len(section_ids), len(set(section_ids)))
            if prop_id == "left_signal_cube":
                self.assertEqual(ux["crossDevicePolicy"], "direct_local_service_only")
                self.assertTrue(ux["directDashboardPipeline"])
                self.assertIsNone(ux["missionStrategyTableRole"])
                by_id = {item["id"]: item for item in sections}
                self.assertEqual(by_id["schedule"]["mode"], "direct_backend_preference")
                self.assertEqual(
                    by_id["schedule"]["endpoint"],
                    "/api/props/left_signal_cube/news/schedule",
                )
                self.assertEqual(by_id["schedule"]["fields"], ["enabled", "times"])
                self.assertEqual(by_id["refresh"]["mode"], "direct_backend_action")
                self.assertEqual(
                    by_id["refresh"]["endpoint"],
                    "/api/props/left_signal_cube/news/refresh",
                )
                self.assertEqual(by_id["source_status"]["mode"], "backend_read_only")
                self.assertNotIn("quota", by_id)
                self.assertNotIn("agent_handoff", by_id)
                continue
            self.assertEqual(ux["crossDevicePolicy"], "agent_mission_report_only")
            self.assertFalse(ux["directDashboardPipeline"])
            self.assertEqual(ux["missionStrategyTableRole"], "global_ledger_only")

            by_id = {item["id"]: item for item in sections}
            self.assertEqual(by_id["quota"]["mode"], "backend_read_only")
            self.assertLessEqual(len(by_id["quota"]["purpose"]), 80)

            if prop_id in WORKFLOW_DEVICE_SCHEDULE_ACTIONS:
                schedule = by_id["schedule"]
                self.assertEqual(schedule["mode"], "backend_preference")
                self.assertEqual(
                    schedule["actionIds"],
                    [WORKFLOW_DEVICE_SCHEDULE_ACTIONS[prop_id]],
                )
                self.assertIn(schedule["actionIds"][0], role["allowedDashboardActions"])
            else:
                self.assertNotIn("schedule", by_id)

            if prop_id == "right_status_crystals":
                settings = by_id["settings"]
                self.assertEqual(settings["mode"], "backend_validated")
                self.assertEqual(settings["actionIds"], ["save_agent_preferences"])
            else:
                self.assertNotIn("settings", by_id)

            if prop_id in handoff_props:
                handoff = by_id["agent_handoff"]
                self.assertEqual(handoff["mode"], "mission_report_only")
                self.assertIn(
                    handoff["direction"],
                    {"send_receive", "receive_only", "internal_only", "receive_and_internal"},
                )
            else:
                self.assertNotIn("agent_handoff", by_id)

    def test_eight_workflow_devices_are_independent_and_agent_coordinated(self) -> None:
        ordered_prop_ids = [
            "codex_mcp_portal",
            "left_server_racks",
            "right_server_racks",
            "right_tool_console",
            "left_audit_crystals",
            "left_signal_cube",
            "terminal_workstation",
            "right_status_crystals",
        ]
        for expected_order, prop_id in enumerate(ordered_prop_ids, start=1):
            workflow = self.role_map["properties"][prop_id]["workflow"]
            self.assertEqual(workflow["displayOrder"], expected_order)
            self.assertTrue(workflow["independent"])
            if prop_id == "left_signal_cube":
                self.assertEqual(workflow["coordinationMode"], "deterministic_backend_direct")
                self.assertFalse(workflow["agentTransferOnly"])
                self.assertFalse(workflow["directDashboardDependency"])
                self.assertEqual(workflow["transferPolicy"]["mode"], "none")
                self.assertFalse(workflow["transferPolicy"]["missionCreated"])
                self.assertFalse(workflow["transferPolicy"]["agentUsed"])
                self.assertFalse(workflow["transferPolicy"]["aiUsed"])
                continue
            self.assertEqual(workflow["coordinationMode"], "agent_mission_only")
            self.assertTrue(workflow["agentTransferOnly"])
            self.assertFalse(workflow["directDashboardDependency"])
            self.assertNotIn("stage", workflow)
            self.assertNotIn("upstreamPropIds", workflow)
            self.assertNotIn("downstreamPropIds", workflow)
            policy = workflow["transferPolicy"]
            self.assertEqual(policy["mode"], "agent_mission_only")
            self.assertEqual(policy["frontendMaySubmitFields"], ["sourceReportId"])
            self.assertTrue(policy["backendDerivesLineage"])
            self.assertEqual(policy["missionStrategyTableRole"], "global_ledger_only")

        self.assertIn("mission_strategy_table", self.role_map["properties"])

    def test_four_new_devices_have_exact_actions_owners_and_report_types(self) -> None:
        tool_rows = {item["id"]: item for item in self.permissions["tools"] if item.get("id")}
        for prop_id, expected_actions in NEW_DEVICE_ACTIONS.items():
            role = self.role_map["properties"][prop_id]
            self.assertEqual(set(role["allowedDashboardActions"]), set(expected_actions))
            backend_actions = {
                action_id: action
                for action_id, action in self.bridge.DASHBOARD_WORKFLOW_ACTIONS.items()
                if action.get("propId") == prop_id
            }
            self.assertEqual(set(backend_actions), set(expected_actions))
            for action_id, (owner_id, report_type) in expected_actions.items():
                backend_action = backend_actions[action_id]
                tool = tool_rows[action_id]
                self.assertEqual(backend_action["ownerAgentId"], owner_id)
                self.assertEqual(backend_action["reportType"], report_type)
                self.assertEqual(tool["reportType"], report_type)
                self.assertEqual(tool["reportTargetPropId"], prop_id)
                self.assertTrue(tool["requiresMission"])
                self.assertTrue(tool["requiresAuditLog"])
                self.assertTrue(tool["workflowEnvelopeRequired"])

        direct_role = self.role_map["properties"]["left_signal_cube"]
        self.assertEqual(direct_role["allowedDashboardActions"], [])
        self.assertEqual(direct_role["ownerAgents"], [])
        self.assertEqual(direct_role["workflow"]["coordinationMode"], "deterministic_backend_direct")

    def test_google_sheet_template_and_backend_projection_are_exactly_42_fields(self) -> None:
        template = PROJECT_ROOT / "contracts" / "research" / "trading-system-sheet-template.csv"
        with template.open("r", encoding="utf-8", newline="") as handle:
            bilingual_headers = next(csv.reader(handle))
        field_ids = [header.split("/", 1)[0] for header in bilingual_headers]
        self.assertEqual(len(field_ids), 42)
        self.assertEqual(len(set(field_ids)), 42)
        self.assertTrue(all("/" in header for header in bilingual_headers))
        self.assertEqual(list(self.bridge.DASHBOARD_DISCOVERY_SHEET_COLUMNS), field_ids)

    def test_every_workflow_action_is_allowed_by_prop_and_has_a_tool_contract(self) -> None:
        tool_rows = {
            item["id"]: item
            for item in self.permissions["tools"]
            if isinstance(item, dict) and item.get("id")
        }
        for action_id, action in self.bridge.DASHBOARD_WORKFLOW_ACTIONS.items():
            prop_id = action["propId"]
            role = self.role_map["properties"][prop_id]
            if prop_id == "left_signal_cube":
                self.assertNotIn(action_id, role["allowedDashboardActions"])
                self.assertIn(action_id, role["legacyGenericActionIdsRejected"])
                continue
            self.assertIn(action_id, role["allowedDashboardActions"])
            self.assertIn(action_id, tool_rows)
            self.assertIn(prop_id, tool_rows[action_id]["linkedPropIds"])
            self.assertEqual(action.get("reportType"), tool_rows[action_id].get("reportType"))
            field_ids = {item["id"].lower() for item in action.get("formFields", ())}
            for forbidden in ("token", "api_key", "cookie", "password", "secret"):
                self.assertNotIn(forbidden, field_ids)

        self.assertEqual(
            self.bridge.DASHBOARD_WORKFLOW_ACTIONS["refresh_vps_hq_status"]["tabId"],
            "connections",
        )
        self.assertEqual(
            self.bridge.DASHBOARD_WORKFLOW_ACTIONS["save_agent_preferences"]["tabId"],
            "connections",
        )

    def test_unavailable_external_adapters_remain_explicitly_disabled(self) -> None:
        tools = {
            item["id"]: item
            for item in self.permissions["tools"]
            if isinstance(item, dict) and item.get("id")
        }
        for tool_id in (
            "google_sheet_catalog_sync",
            "compile_strategy_code",
            "run_strategy_tester",
            "run_optimization",
            "run_ea_discovery_plugin",
        ):
            self.assertEqual(tools[tool_id]["adapterStatus"], "coming_soon")
            self.assertFalse(tools[tool_id]["realExecutionAvailable"])

    def test_report_types_route_back_to_the_workflow_device(self) -> None:
        targets = self.reports["report_targets"]
        expected = {
            "trading_system_discovery_report": "codex_mcp_portal",
            "trading_system_research_report": "left_server_racks",
            "ea_build_report": "right_server_racks",
            "ea_experiment_report": "right_tool_console",
            "ea_discovery_report": "right_tool_console",
            "indicator_scout_report": "left_audit_crystals",
            "fx_news_bias_report": "left_signal_cube",
            "ea_development_report": "terminal_workstation",
            "ops_overview_report": "right_status_crystals",
        }
        for report_type, prop_id in expected.items():
            self.assertIn(prop_id, targets[report_type])

    def test_legacy_risk_and_auto_trading_reports_do_not_mix_with_new_devices(self) -> None:
        targets = self.reports["report_targets"]
        self.assertIn("mission_strategy_table", targets["risk_review"])
        self.assertIn(
            "risk_review",
            self.role_map["properties"]["mission_strategy_table"]["acceptedReportTypes"],
        )
        self.assertNotIn("left_audit_crystals", targets["risk_review"])
        self.assertNotIn("right_status_crystals", targets["risk_review"])
        self.assertIn("left_analytics_console", targets["auto_trading_status_report"])
        self.assertIn(
            "auto_trading_status_report",
            self.role_map["properties"]["left_analytics_console"]["acceptedReportTypes"],
        )
        self.assertNotIn("left_signal_cube", targets["auto_trading_status_report"])
        self.assertNotIn("right_status_crystals", targets["auto_trading_status_report"])
        accepted = set(self.role_map["properties"]["right_status_crystals"]["acceptedReportTypes"])
        self.assertNotIn("risk_review", accepted)
        self.assertNotIn("auto_trading_status_report", accepted)
        right_status_rule = next(
            item for item in self.role_map["routingRules"]
            if item["targetPropId"] == "right_status_crystals"
        )
        legacy_keywords = {"auto trade status", "ea status", "risk status", "approval status"}
        self.assertTrue(legacy_keywords.isdisjoint(set(right_status_rule["keywords"])))

    def test_orchestration_and_agent_surfaces_follow_canonical_legacy_routes(self) -> None:
        rules = {
            item["id"]: item
            for item in self.orchestration["managerAutoDelegation"]["specialistRules"]
        }
        self.assertEqual(rules["risk_review"]["targetPropId"], "mission_strategy_table")
        self.assertEqual(rules["ea_runtime_status"]["targetPropId"], "left_analytics_console")

        agents = {item["id"]: item for item in self.agents["agents"]}
        risk = agents["risk_guard"]
        self.assertEqual(risk["visual"]["default_target"], "mission_strategy_table")
        self.assertEqual(risk["allowed_surfaces"], ["mission_strategy_table"])
        self.assertNotIn("left_signal_cube", agents["vps_watch"]["allowed_surfaces"])
        self.assertEqual(agents["telegram_ops"]["allowed_surfaces"], ["mission_strategy_table"])
        self.assertIn("left_audit_crystals", agents["codex_mcp_operator"]["allowed_surfaces"])
        self.assertIn("left_audit_crystals", agents["mission_archivist"]["allowed_surfaces"])

        right_status = self.role_map["properties"]["right_status_crystals"]
        self.assertNotIn("legacy_safety_status", right_status["dashboardSections"])
        self.assertNotIn(
            "legacy",
            " ".join(item.get("purpose", "") for item in right_status["localTabs"]).lower(),
        )

    def test_fx_bias_contract_uses_exact_28_pair_universe_and_three_horizons(self) -> None:
        role_workflow = self.role_map["properties"]["left_signal_cube"]["workflow"]
        report_schema = self.reports["typed_report_schemas"]["fx_news_bias_report"]
        tool = next(item for item in self.permissions["tools"] if item.get("id") == "build_fx_pair_bias")
        self.assertEqual(role_workflow["fxPairs"], FX_PAIR_UNIVERSE)
        self.assertEqual(report_schema["fxPairUniverse"], FX_PAIR_UNIVERSE)
        self.assertEqual(list(self.bridge.FX_BIAS_PAIRS), FX_PAIR_UNIVERSE)
        self.assertEqual(role_workflow["horizons"], ["short", "medium", "long"])
        self.assertEqual(tool["supportedHorizons"], ["short", "medium", "long"])
        self.assertEqual(tool["fxPairCount"], 28)
        self.assertFalse(tool["orderSubmissionAllowed"])

    def test_adapter_readiness_is_truthful_for_new_devices(self) -> None:
        expected_unavailable = {
            "left_audit_crystals": {"screenshot_adapter": "not_connected"},
            "terminal_workstation": {"metaeditor_compiler": "coming_soon", "artifact_download": "coming_soon"},
            "right_status_crystals": {"external_vps_api": "coming_soon"},
        }
        for prop_id, adapter_statuses in expected_unavailable.items():
            connections = {
                item["id"]: item for item in self.connections["profiles"][prop_id]["connections"]
            }
            for adapter_id, expected_status in adapter_statuses.items():
                self.assertEqual(connections[adapter_id]["adapterStatus"], expected_status)
        news_connections = {
            item["id"]: item
            for item in self.connections["profiles"]["left_signal_cube"]["connections"]
        }
        self.assertEqual(news_connections["official_structured_sources"]["adapterStatus"], "implemented_allowlist")
        self.assertEqual(news_connections["fx_bias_analysis"]["adapterStatus"], "implemented")
        self.assertEqual(news_connections["direct_news_store"]["adapterStatus"], "implemented_atomic_local_store")
        self.assertEqual(news_connections["backend_scheduler"]["adapterStatus"], "implemented_direct_backend")
        eligible = self.connections["discoveryLabMt4Readiness"]["eligibleDashboardIds"]
        self.assertNotIn("terminal_workstation", eligible)
        terminal_tools = {
            item["id"]: item for item in self.permissions["tools"]
            if item.get("id") in {"inspect_ea_source", "develop_ea_source", "propose_ea_performance_improvements"}
        }
        self.assertTrue(all(not item["compileIncluded"] for item in terminal_tools.values()))
        self.assertFalse(terminal_tools["propose_ea_performance_improvements"]["backtestIncluded"])

    def test_three_read_only_schedulers_are_ready_without_overclaiming_follow_up_work(self) -> None:
        expected = {
            "codex_mcp_portal": {
                "toolId": "save_discovery_schedule",
                "scheduled": ["discover_trading_systems"],
                "manual": ["discover_ea_updates"],
                "defaultEnabled": False,
            },
            "left_audit_crystals": {
                "toolId": "save_indicator_scout_schedule",
                "scheduled": ["discover_new_indicators"],
                "manual": [],
                "defaultEnabled": True,
            },
        }
        tools = {
            item["id"]: item
            for item in self.permissions["tools"]
            if isinstance(item, dict) and item.get("id")
        }
        for prop_id, spec in expected.items():
            role_workflow = self.role_map["properties"][prop_id]["workflow"]
            connection = self.connections["profiles"][prop_id]
            operation = connection["operation"]
            backend_scheduler = next(
                item for item in connection["connections"]
                if item["id"] == "backend_scheduler"
            )
            tool = tools[spec["toolId"]]

            self.assertEqual(
                role_workflow["schedule"]["defaultEnabled"],
                spec["defaultEnabled"],
            )
            self.assertEqual(
                role_workflow["schedule"]["recurringSchedulerAdapterStatus"],
                "implemented_guarded_read_only",
            )
            self.assertEqual(
                role_workflow["readiness"]["recurringScheduler"],
                "ready_guarded_read_only",
            )
            self.assertEqual(
                backend_scheduler["adapterStatus"],
                "implemented_guarded_read_only",
            )
            self.assertEqual(
                operation["scheduleExecutionAdapterStatus"],
                "implemented_guarded_read_only",
            )
            self.assertEqual(operation["scheduledActionIds"], spec["scheduled"])
            self.assertEqual(
                operation.get("manualOrAgentHandoffActionIds", []),
                spec["manual"],
            )
            self.assertTrue(tool["recurringSchedulerAvailable"])
            self.assertEqual(tool["readiness"], "ready_guarded_read_only")
            self.assertEqual(tool["scheduledActionIds"], spec["scheduled"])
            self.assertEqual(
                tool.get("manualOrAgentHandoffActionIds", []),
                spec["manual"],
            )

        news_role = self.role_map["properties"]["left_signal_cube"]
        news_schedule = news_role["workflow"]["schedule"]
        news_operation = self.connections["profiles"]["left_signal_cube"]["operation"]
        self.assertTrue(news_schedule["defaultEnabled"])
        self.assertEqual(news_schedule["defaultTimes"], ["00:00", "12:00"])
        self.assertEqual(news_schedule["recurringSchedulerAdapterStatus"], "implemented_direct_backend")
        self.assertEqual(news_role["workflow"]["readiness"]["recurringScheduler"], "ready_direct_backend")
        self.assertEqual(news_operation["scheduleExecutionAdapterStatus"], "implemented_direct_backend")
        self.assertEqual(news_operation["scheduledActionIds"], [])
        self.assertEqual(news_operation["manualOrAgentHandoffActionIds"], [])
        self.assertEqual(
            news_operation["refreshEndpoint"],
            "/api/props/left_signal_cube/news/refresh",
        )

        portal_connections = {
            item["id"]: item
            for item in self.connections["profiles"]["codex_mcp_portal"]["connections"]
        }
        self.assertEqual(
            portal_connections["google_sheets_adapter"]["adapterStatus"],
            "coming_soon",
        )
        self.assertTrue(
            portal_connections["google_sheets_adapter"]["externalWriteRequiresUserConfirmation"]
        )
        self.assertTrue(tools["google_sheet_catalog_sync"]["externalWriteRequiresUserConfirmation"])

    def test_agent_settings_accept_only_six_safe_fields(self) -> None:
        safe_fields = {
            "language", "modelTier", "tokenBudget", "timeoutSeconds",
            "outputLimitChars", "rateReservePercent",
        }
        role = self.role_map["properties"]["right_status_crystals"]
        connection = self.connections["profiles"]["right_status_crystals"]
        report = self.reports["typed_report_schemas"]["ops_overview_report"]
        tool = next(item for item in self.permissions["tools"] if item.get("id") == "save_agent_preferences")
        action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS["save_agent_preferences"]
        self.assertEqual(set(role["agentPreferenceContract"]["fields"]), safe_fields)
        self.assertEqual(set(connection["agentPreferenceSafety"]["allowedFields"]), safe_fields)
        self.assertEqual(set(report["agentPreferences"]), safe_fields | {"updatedAt", "updatedBy"})
        self.assertEqual(set(tool["safePreferenceFields"]), safe_fields)
        self.assertEqual({item["id"] for item in action["formFields"]}, safe_fields)
        self.assertFalse(role["agentPreferenceContract"]["providerModelIdAccepted"])
        self.assertFalse(tool["providerModelIdAllowed"])
        self.assertFalse(tool["frontendSelectedCredentialsAllowed"])

    def test_terminal_source_contract_uses_opaque_source_ids_not_paths(self) -> None:
        for action_id in NEW_DEVICE_ACTIONS["terminal_workstation"]:
            action = self.bridge.DASHBOARD_WORKFLOW_ACTIONS[action_id]
            field_ids = {item["id"] for item in action["formFields"]}
            self.assertIn("sourceReportId", field_ids)
            self.assertIn("workspaceSourceId", field_ids)
            self.assertFalse(any("path" in field_id.lower() for field_id in field_ids))
        report = self.reports["typed_report_schemas"]["ea_development_report"]
        self.assertIn("workspaceSourceId", report["sourceReference"])
        self.assertNotIn("sourcePath", report["sourceReference"])
        policy = next(
            item for item in self.permissions["tools"] if item.get("id") == "develop_ea_source"
        )["sourceReferencePolicy"]
        self.assertEqual(policy, "opaque_workspace_artifact_or_linked_report_only")

    def test_mission_report_and_tool_contracts_share_required_workflow_envelope(self) -> None:
        required_fields = {
            "missionId", "targetPropId", "ownerAgentId", "sourceLineage",
            "agentTransfer", "timestamps", "status", "reportRoute",
        }
        agent_transfer_fields = {
            "sourceReportId", "sourcePropId", "sourceMissionId", "transferAgentId",
            "sourceOwnerAgentId", "targetPropId", "handoffMissionId", "status",
        }
        envelope = self.permissions["workflowExecutionEnvelope"]
        self.assertTrue(envelope["requiredForEveryDashboardAction"])
        self.assertEqual(set(envelope["fields"]), required_fields)
        self.assertEqual(set(envelope["agentTransferFields"]), agent_transfer_fields)
        self.assertEqual(envelope["coordinationMode"], "agent_mission_only")
        self.assertTrue(envelope["independentDashboards"])
        self.assertTrue(envelope["agentTransferOnly"])
        self.assertFalse(envelope["directDashboardDependency"])
        self.assertEqual(envelope["missionStrategyTableRole"], "global_ledger_only")
        self.assertTrue(envelope["frontendMaySendIntentOnly"])
        self.assertFalse(envelope["frontendMaySendSecrets"])
        self.assertTrue(required_fields.issubset(self.missions["schema"]))
        self.assertTrue(required_fields.issubset(self.reports["base_report_schema"]))
        self.assertEqual(set(self.missions["schema"]["agentTransfer"]), agent_transfer_fields | {"mode"})
        self.assertEqual(set(self.reports["base_report_schema"]["agentTransfer"]), agent_transfer_fields | {"mode"})
        self.assertEqual(
            set(self.reports["base_report_schema"]["sourceLineage"]),
            {"sourcePropIds", "sourceMissionIds", "sourceReportIds", "sourceArtifactIds"},
        )

    def test_agent_report_transfer_is_backend_only_and_cannot_assert_lineage(self) -> None:
        tool = next(
            item for item in self.permissions["tools"] if item.get("id") == "agent_report_transfer"
        )
        self.assertEqual(tool["defaultMode"], "backend_lineage_record_only")
        self.assertEqual(tool["adapterStatus"], "implemented_backend_record_only")
        self.assertFalse(tool["realExecutionAvailable"])
        self.assertFalse(tool["externalExecution"])
        self.assertFalse(tool["consumesCodexQuota"])
        self.assertFalse(tool["frontendMayAssertLineage"])
        self.assertEqual(
            tool["frontendIntentFields"],
            ["actionId", "sourceReportId", "idempotencyKey"],
        )
        self.assertEqual(tool["missionStrategyTableRole"], "global_ledger_only")

    def test_room_labels_describe_the_new_device_roles(self) -> None:
        room_props = {item["id"]: item for item in self.room["props"]}
        expected_terms = {
            "left_audit_crystals": "Indicator",
            "left_signal_cube": "28 คู่เงิน",
            "terminal_workstation": "พัฒนา EA",
            "right_status_crystals": "เชื่อมต่อ",
        }
        for prop_id, term in expected_terms.items():
            combined = f"{room_props[prop_id]['label']} {room_props[prop_id]['summary']}"
            self.assertIn(term, combined)

    def test_radar_website_tool_contract_is_truthful_and_backwards_compatible(self) -> None:
        prop_id = "left_audit_crystals"
        role = self.role_map["properties"][prop_id]
        connection = self.connections["profiles"][prop_id]
        report = self.reports["typed_report_schemas"]["indicator_scout_report"]
        plugin = load_json("contracts/workflows/equipment-plugin-map.json")["equipment"][prop_id]
        room_prop = next(item for item in self.room["props"] if item["id"] == prop_id)

        self.assertEqual(role["functionName"], "Radar Website Tool")
        self.assertEqual(room_prop["label"], "Radar Website Tool")
        self.assertEqual(connection["moduleNameTh"], "Radar Website Tool")
        self.assertEqual(plugin["schedule"]["maximumRunsPerDay"], 1)
        self.assertEqual(connection["operation"]["scheduleHardMaximumRunsPerDay"], 1)
        self.assertEqual(role["workflow"]["readModel"]["historyWindowDays"], 7)
        self.assertEqual(report["readModel"]["primaryViews"], ["today", "history_7_days"])
        self.assertFalse(report["googleSheet"]["privateSheetDefaultIncluded"])
        self.assertFalse(report["googleSheet"]["externalWriteEnabled"])
        self.assertEqual(report["runtimeReadiness"]["googleSheetsAdapter"], "not_connected")
        self.assertEqual(report["runtimeReadiness"]["screenshotAdapter"], "not_connected")
        fields = plugin["actions"]["discover_new_indicators"]["outputFields"]
        self.assertEqual(fields, ["entries"])
        entry_contract = plugin["actions"]["discover_new_indicators"]["entryContract"]
        self.assertEqual(entry_contract["containerField"], "entries")
        self.assertEqual(entry_contract["minimumItemsPerRun"], 1)
        self.assertEqual(entry_contract["maximumItemsPerRun"], 6)
        self.assertEqual(
            set(entry_contract["backendComputedFields"]),
            {"recordId", "duplicateFingerprint", "duplicateStatus", "duplicateScope"},
        )


if __name__ == "__main__":
    unittest.main()
