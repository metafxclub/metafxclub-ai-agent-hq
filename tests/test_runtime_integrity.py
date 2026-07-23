from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"
FRONTEND_INDEX_PATH = PROJECT_ROOT / "frontend" / "index.html"
FRONTEND_MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
FRONTEND_STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"
LIFECYCLE_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "start-local-bridge.ps1"
INSTALLER_SCRIPT_PATH = PROJECT_ROOT / "installer" / "install.ps1"
CODEX_READINESS_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "check-codex-readiness.ps1"
DASHBOARD_CONNECTION_PATH = PROJECT_ROOT / "contracts" / "connections" / "dashboard-connection-contract.json"
AGENT_CHAT_CONTRACT_PATH = PROJECT_ROOT / "contracts" / "agents" / "agent-chat-contract.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("metafx_bridge_server", BRIDGE_PATH)
        cls.runner = load_module("metafx_codex_runner", RUNNER_PATH)

    def test_all_contracts_are_valid_json(self) -> None:
        contract_paths = sorted((PROJECT_ROOT / "contracts").rglob("*.json"))
        self.assertGreater(len(contract_paths), 0)
        for path in contract_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_canonical_agent_roster_has_ten_unique_agents(self) -> None:
        payload = json.loads(
            (PROJECT_ROOT / "contracts" / "agents" / "agents.json").read_text(encoding="utf-8")
        )
        agent_ids = [str(agent.get("id")) for agent in payload.get("agents", [])]
        self.assertEqual(len(agent_ids), 10)
        self.assertEqual(len(set(agent_ids)), 10)
        self.assertIn("manager", agent_ids)
        self.assertIn("risk_guard", agent_ids)

    def test_room_declares_nine_dashboards_and_one_mission_kanban(self) -> None:
        room = json.loads((PROJECT_ROOT / "contracts" / "rooms" / "command-room.json").read_text(encoding="utf-8"))
        roles = json.loads((PROJECT_ROOT / "contracts" / "props" / "property-role-map.json").read_text(encoding="utf-8"))["properties"]
        prop_ids = {str(item["id"]) for item in room["props"]}
        dashboards = {prop_id for prop_id, role in roles.items() if role.get("interactionMode") == "dashboard"}
        kanban = {prop_id for prop_id, role in roles.items() if role.get("interactionMode") == "kanban"}
        self.assertEqual(len(prop_ids), 10)
        self.assertEqual(len(dashboards), 9)
        self.assertEqual(kanban, {"mission_strategy_table"})

    def test_agent_chat_contract_uses_real_codex_and_backend_owned_structured_task_intent(self) -> None:
        agents = json.loads(
            (PROJECT_ROOT / "contracts" / "agents" / "agents.json").read_text(encoding="utf-8")
        )["agents"]
        chat = json.loads(AGENT_CHAT_CONTRACT_PATH.read_text(encoding="utf-8"))
        tools = json.loads(
            (PROJECT_ROOT / "contracts" / "tools" / "tool-permission-contract.json").read_text(encoding="utf-8")
        )["tools"]
        orchestration = json.loads(
            (PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json").read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (PROJECT_ROOT / "contracts" / "bridge" / "bridge-contract.json").read_text(encoding="utf-8")
        )

        self.assertEqual(chat["endpoint"], "POST /api/agents/chat")
        self.assertEqual(
            chat["request"]["allowedFields"],
            ["agentId", "message", "sessionId", "idempotencyKey"],
        )
        self.assertEqual(
            chat["request"]["requiredFields"],
            ["agentId", "message", "sessionId", "idempotencyKey"],
        )
        self.assertIn("quotaConsumptionStatus", chat["response"]["usageFields"])
        self.assertEqual(
            chat["response"]["quotaConsumptionStatusValues"],
            ["none", "possible", "confirmed"],
        )
        self.assertTrue(chat["execution"]["consumesCodexQuota"])
        self.assertFalse(chat["execution"]["toolsEnabled"])
        self.assertFalse(chat["execution"]["computerUseEnabled"])
        self.assertEqual(
            chat["execution"]["createsTask"],
            "only_when_intent_is_task_request",
        )
        self.assertEqual(
            chat["execution"]["outputSchema"]["intentValues"],
            ["conversation", "task_request"],
        )
        self.assertTrue(chat["execution"]["outputSchema"]["conversationTaskGoalMustBeEmpty"])
        self.assertEqual(chat["execution"]["taskRouting"]["managerAndCeo"], "manager_delegate")
        self.assertEqual(chat["execution"]["taskRouting"]["specialist"], "one direct codex_cli_task")
        self.assertFalse(chat["execution"]["taskRouting"]["frontendMaySelectToolModelBudgetRiskOrApproval"])
        self.assertEqual(
            chat["execution"]["highImpactTask"],
            "Backend checks both the raw user message and model taskGoal; waiting_approval_or_blocked_never_auto_execute",
        )
        self.assertEqual(chat["execution"]["sandbox"], "read-only")
        self.assertEqual(chat["execution"]["conversationContext"]["key"], "agentId + sessionId")
        self.assertGreaterEqual(chat["execution"]["conversationContext"]["recentTurns"], 6)
        self.assertFalse(chat["execution"]["conversationContext"]["crossAgentContext"])
        self.assertFalse(chat["execution"]["conversationContext"]["idempotentReplayConsumesQuota"])
        chat_endpoint = bridge["endpoints"]["POST /api/agents/chat"]
        self.assertIn("task_request", chat_endpoint)
        self.assertNotIn("cannot execute tools or create a task", chat_endpoint)

        chat_tool = next(item for item in tools if item["id"] == "agent_chat")
        self.assertEqual(set(chat_tool["allowedAgents"]), {item["id"] for item in agents})
        self.assertTrue(chat_tool["realExecutionAvailable"])
        self.assertTrue(chat_tool["consumesCodexQuota"])
        self.assertFalse(chat_tool["approvalRequired"])
        self.assertFalse(chat_tool["toolsEnabled"])
        self.assertEqual(
            chat_tool["createsMissionTask"],
            "only_when_backend_validated_intent_is_task_request",
        )

        guard = orchestration["costRateGuard"]
        self.assertGreater(guard["agentChatRunsPerHour"], 0)
        self.assertGreaterEqual(guard["agentChatCooldownSeconds"], 1)
        self.assertLessEqual(guard["agentChatMaxMessageChars"], 4000)
        self.assertLessEqual(guard["agentChatMaxOutputChars"], 5000)

    def test_prop_dashboards_have_connection_task_and_result_tabs(self) -> None:
        contract = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))
        ui = contract["dashboardUi"]
        self.assertEqual(ui["dashboardCount"], 9)
        self.assertTrue(ui["missionStrategyTableIsKanban"])
        self.assertTrue(ui["missionStrategyTableExcludedFromDashboardTabs"])
        self.assertEqual(ui["defaultTab"], "connections")
        self.assertEqual(
            [(item["id"], item["labelTh"]) for item in ui["tabs"]],
            [
                ("connections", "การเชื่อมต่อ"),
                ("tasks", "งานของอุปกรณ์"),
                ("results", "ผลลัพธ์งาน"),
            ],
        )
        self.assertFalse(ui["propChatEnabled"])
        self.assertTrue(ui["taskCardsOpenDetails"])
        self.assertTrue(ui["reportCardsOpenDetails"])

    def test_every_dashboard_has_backend_owned_connection_profile(self) -> None:
        roles = json.loads((PROJECT_ROOT / "contracts" / "props" / "property-role-map.json").read_text(encoding="utf-8"))["properties"]
        contract = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))
        profiles = contract["profiles"]
        dashboards = {prop_id: role for prop_id, role in roles.items() if role.get("interactionMode") == "dashboard"}
        self.assertEqual(set(profiles), set(dashboards))
        for prop_id, role in dashboards.items():
            with self.subTest(prop=prop_id):
                self.assertEqual(role.get("connectionProfileId"), prop_id)
                profile = profiles[prop_id]
                self.assertTrue(profile.get("moduleNameTh"))
                self.assertTrue(profile.get("connections"))
                self.assertEqual(profile["operation"]["defaultMode"], "manual")
                self.assertTrue(profile["operation"]["scheduleBackendOwned"])
                self.assertFalse(profile["operation"]["scheduleDefaultEnabled"])
                self.assertEqual(profile["reportRoute"]["targetPropId"], prop_id)
                for item in profile["connections"]:
                    self.assertIn(item["adapterStatus"], {"implemented", "runtime_detected", "coming_soon", "disabled"})
                    if item["adapterStatus"] in {"coming_soon", "disabled"}:
                        self.assertNotEqual(item["adapterStatus"], "implemented")

        self.assertTrue({"partial", "needs_attention"}.issubset(set(contract["statusVocabulary"])))
        mt_any_of_dashboards = {"right_server_racks", "left_analytics_console", "terminal_workstation"}
        for prop_id in mt_any_of_dashboards:
            profile = profiles[prop_id]
            connection_ids = {item["id"] for item in profile["connections"]}
            any_of = profile.get("connectionRequirements", {}).get("anyOf")
            self.assertEqual(any_of, ["mt4_terminal", "mt5_terminal"])
            self.assertTrue(set(any_of).issubset(connection_ids))

    def test_specialist_home_targets_match_dashboard_report_routing(self) -> None:
        agents = json.loads((PROJECT_ROOT / "contracts" / "agents" / "agents.json").read_text(encoding="utf-8"))["agents"]
        agent_map = {item["id"]: item for item in agents}
        orchestration = json.loads((PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json").read_text(encoding="utf-8"))
        rules = {item["id"]: item for item in orchestration["managerAutoDelegation"]["specialistRules"]}
        reports = json.loads((PROJECT_ROOT / "contracts" / "reports" / "report-contract.json").read_text(encoding="utf-8"))["report_targets"]
        self.assertEqual(rules["backtest_review"]["targetPropId"], "left_analytics_console")
        self.assertEqual(rules["optimization_review"]["targetPropId"], "right_server_racks")
        self.assertEqual(rules["vps_status"]["targetPropId"], "right_status_crystals")
        self.assertEqual(agent_map["optimization_agent"]["visual"]["default_target"], "right_server_racks")
        self.assertEqual(agent_map["vps_watch"]["visual"]["default_target"], "right_status_crystals")
        self.assertIn("left_analytics_console", reports["backtest_report"])
        self.assertIn("right_server_racks", reports["optimization_report"])
        self.assertIn("right_status_crystals", reports["vps_report"])

    def test_primary_report_routes_agent_homes_and_specialist_routes_are_semantically_aligned(self) -> None:
        contracts = PROJECT_ROOT / "contracts"
        agents = json.loads((contracts / "agents" / "agents.json").read_text(encoding="utf-8"))["agents"]
        role_map = json.loads((contracts / "props" / "property-role-map.json").read_text(encoding="utf-8"))["properties"]
        profiles = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))["profiles"]
        report_targets = json.loads((contracts / "reports" / "report-contract.json").read_text(encoding="utf-8"))["report_targets"]
        orchestration = json.loads((contracts / "orchestration" / "orchestration-contract.json").read_text(encoding="utf-8"))

        canonical_agent_targets = {
            "manager": "mission_strategy_table",
            "ceo": "mission_strategy_table",
            "ea_developer": "terminal_workstation",
            "backtest_analyst": "left_analytics_console",
            "optimization_agent": "right_server_racks",
            "vps_watch": "right_status_crystals",
            "telegram_ops": "right_tool_console",
            "risk_guard": "left_audit_crystals",
            "codex_mcp_operator": "codex_mcp_portal",
            "mission_archivist": "left_server_racks",
        }
        self.assertEqual(
            {agent["id"]: agent["visual"]["default_target"] for agent in agents},
            canonical_agent_targets,
        )

        for prop_id, profile in profiles.items():
            with self.subTest(prop=prop_id):
                role = role_map[prop_id]
                primary_type = profile["reportRoute"]["primaryReportType"]
                self.assertEqual(profile["reportRoute"]["targetPropId"], prop_id)
                self.assertEqual(primary_type, role["primaryReportType"])
                self.assertIn(primary_type, role["acceptedReportTypes"])
                self.assertIn(prop_id, report_targets[primary_type])

        manager_rules = orchestration["managerAutoDelegation"]
        for rule in [*(manager_rules.get("specialistRules") or []), manager_rules["fallback"]]:
            with self.subTest(rule=rule.get("id", "fallback")):
                target_prop = rule["targetPropId"]
                report_type = rule["reportType"]
                self.assertIn(target_prop, report_targets[report_type])
                self.assertIn(report_type, role_map[target_prop]["acceptedReportTypes"])

        self.assertEqual(
            role_map["right_server_racks"]["acceptedReportTypes"],
            ["optimization_report", "dashboard_connection_report", "terminal_discovery_report", "terminal_selection_report"],
        )
        self.assertEqual(
            role_map["left_analytics_console"]["acceptedReportTypes"],
            ["backtest_report", "backtest_optimization_report", "dashboard_connection_report", "terminal_discovery_report", "terminal_selection_report"],
        )

    def test_terminal_target_selection_contract_is_fail_closed_and_frontend_safe(self) -> None:
        contracts = PROJECT_ROOT / "contracts"
        connection_contract = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))
        tool_contract = json.loads((contracts / "tools" / "tool-permission-contract.json").read_text(encoding="utf-8"))
        report_contract = json.loads((contracts / "reports" / "report-contract.json").read_text(encoding="utf-8"))
        role_map = json.loads((contracts / "props" / "property-role-map.json").read_text(encoding="utf-8"))["properties"]
        bridge_contract = json.loads((contracts / "bridge" / "bridge-contract.json").read_text(encoding="utf-8"))

        expected_props = {"right_server_racks", "left_analytics_console", "terminal_workstation", "left_signal_cube"}
        selection = connection_contract["terminalTargetSelection"]
        self.assertEqual(selection["intent"], "select_metatrader_target")
        self.assertEqual(selection["endpoint"], "POST /api/integrations/metatrader/select")
        self.assertEqual(set(selection["eligibleDashboardIds"]), expected_props)
        self.assertEqual(selection["requestFields"], ["propId", "candidateId"])
        self.assertEqual(
            set(selection["candidateFrontendSafeFields"]),
            {"candidateId", "platform", "labelTh", "detected", "runningState"},
        )
        self.assertEqual(
            set(selection["selectedCandidateFrontendSafeFields"]),
            {"candidateId", "platform", "labelTh", "detected", "runningState"},
        )
        self.assertEqual(
            set(selection["selectionFrontendSafeFields"]),
            {
                "propId", "required", "detectedStatus", "status", "configurationStatus",
                "candidateCount", "candidates", "selectedCandidate", "selectedAt",
                "staleSelection", "adapterConnection", "adapterReady", "canSelect", "detailTh",
            },
        )
        self.assertTrue({"path", "terminal_path", "pid", "process_id", "account", "account_number", "broker", "broker_server"}.issubset(set(selection["forbiddenFrontendFields"])))
        self.assertEqual(selection["stateSemantics"]["checklistTerminal"], "detected")
        self.assertEqual(selection["stateSemantics"]["targetConfiguration"], "configured")
        self.assertEqual(selection["stateSemantics"]["adapterConnection"], "coming_soon")
        self.assertEqual(selection["stateSemantics"]["liveTrading"], "disabled")
        self.assertEqual(selection["selectionSubstateVocabulary"], ["selected", "not_selected", "not_required"])
        self.assertEqual(selection["configurationSubstateVocabulary"], ["configured", "not_configured", "not_required"])
        self.assertFalse(selection["selectionSubstateIsOverallStatus"])
        self.assertFalse(selection["selectionIsConnection"])
        self.assertFalse(selection["selectionEnablesLiveTrading"])

        tools = {tool["id"]: tool for tool in tool_contract["tools"]}
        select_tool = tools["terminal_target_select"]
        self.assertEqual(set(select_tool["linkedPropIds"]), expected_props)
        self.assertEqual(select_tool["frontendIntentFields"], ["propId", "candidateId"])
        self.assertFalse(select_tool["realExecutionAvailable"])
        self.assertFalse(select_tool["autoRunnable"])
        self.assertFalse(select_tool["approvalRequired"])
        self.assertEqual(tools["live_trading"]["adapterStatus"], "disabled")
        self.assertFalse(tools["live_trading"]["realExecutionAvailable"])

        self.assertEqual(set(report_contract["report_targets"]["terminal_selection_report"]), expected_props)
        for prop_id in expected_props:
            with self.subTest(prop=prop_id):
                self.assertIn("terminal_selection_report", role_map[prop_id]["acceptedReportTypes"])
                self.assertIn("select_metatrader_target", role_map[prop_id]["allowedDashboardActions"])
        self.assertIn("POST /api/integrations/metatrader/select", bridge_contract["endpoints"])

    def test_report_read_model_recursively_redacts_terminal_and_account_metadata(self) -> None:
        report = self.bridge.report_read_model_item({
            "id": "report-sensitive-metadata",
            "type": "ops_overview_report",
            "title": "Nested metadata regression",
            "findings": [{
                "account_number": "12345678",
                "nested": [{"Broker Server": "Broker-Live"}],
            }],
            "metrics": {
                "terminal.path": r"D:\MetaTrader 5\terminal64.exe",
                "Process-ID": 4321,
            },
        })

        self.assertEqual(report["findings"][0]["account_number"], "[REDACTED_SECRET]")
        self.assertEqual(report["findings"][0]["nested"][0]["Broker Server"], "[REDACTED_SECRET]")
        self.assertEqual(report["metrics"]["terminal.path"], "[REDACTED_SECRET]")
        self.assertEqual(report["metrics"]["Process-ID"], "[REDACTED_SECRET]")
        serialized = json.dumps(report, ensure_ascii=False)
        for forbidden in ("12345678", "Broker-Live", "MetaTrader 5", "4321"):
            self.assertNotIn(forbidden, serialized)

        free_text = self.bridge.report_read_model_item({
            "id": "report-sensitive-free-text",
            "type": "ops_overview_report",
            "title": "Privacy regression",
            "summary": "Account number is 778899; broker server=Broker-Live; terminal path: D:\\MT5\\terminal64.exe; PID 9876",
        })
        free_text_serialized = json.dumps(free_text, ensure_ascii=False)
        for forbidden in ("778899", "Broker-Live", "D:\\MT5", "9876"):
            self.assertNotIn(forbidden, free_text_serialized)

    def test_visual_routing_matches_optimization_and_vps_contracts(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        optimization_start = main.index('id: "optimization_agent"')
        vps_start = main.index('id: "vps_watch"', optimization_start)
        telegram_start = main.index('id: "telegram_ops"', vps_start)
        optimization_block = main[optimization_start:vps_start]
        vps_block = main[vps_start:telegram_start]
        target_start = main.index("function pickTargetForTask(text)")
        target_end = main.index("\nfunction pickAgentForTask(text)", target_start)
        target_block = main[target_start:target_end]

        self.assertIn('right_server_racks: "ตู้ Optimization Lab MT4/MT5"', main)
        self.assertIn('right_status_crystals: "คริสตัลสถานะ VPS และภาพรวม HQ"', main)
        self.assertIn('defaultTarget: "right_server_racks"', optimization_block)
        self.assertIn('homeTarget: "right_server_racks"', optimization_block)
        self.assertIn('defaultTarget: "right_status_crystals"', vps_block)
        self.assertIn('homeTarget: "right_status_crystals"', vps_block)
        self.assertIn('taskKeywords.optimization)) return "right_server_racks"', target_block)
        self.assertIn('taskKeywords.vps)) return "right_status_crystals"', target_block)

        original_role_loader = self.bridge.load_property_role_map
        try:
            self.bridge.load_property_role_map = lambda: {"routingRules": []}
            self.assertEqual(self.bridge.pick_target_for_task("check VPS latency and uptime"), "right_status_crystals")
        finally:
            self.bridge.load_property_role_map = original_role_loader

    def test_generic_report_rendering_uses_frontend_redaction_defense(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        board_start = main.index("function createBoardCard(item = {})")
        board_end = main.index("\nfunction renderCardList", board_start)
        board_block = main[board_start:board_end]
        structured_start = main.index("function structuredDashboardItems")
        structured_end = main.index("\nfunction capabilityDashboardItems", structured_start)
        structured_block = main[structured_start:structured_end]

        self.assertIn("const rawTitle = safeDashboardDisplayText", board_block)
        self.assertIn("const rawDetail = safeDashboardDisplayText", board_block)
        self.assertIn("detail: safeDashboardDisplayText(formatDashboardValue", structured_block)
        for field_name in ("account", "broker", "terminal", "process"):
            self.assertIn(field_name, main[main.index("function safeDashboardDisplayText"):structured_start])
        self.assertIn('diagnosticstatus: "สถานะการตรวจ"', main)
        self.assertIn('mt4installedcount: "MT4 ที่ตรวจพบ"', main)
        self.assertIn("dashboardFieldLabel(name)", main)
        self.assertIn("dashboardMetricValue(name, value)", main)

    def test_metatrader_discovery_is_read_only_and_frontend_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            terminal_root = root / "terminals"
            (terminal_root / "profile-four" / "MQL4").mkdir(parents=True)
            (terminal_root / "profile-five" / "MQL5").mkdir(parents=True)
            original_runtime = self.bridge.RUNTIME_DIR
            original_cache = dict(self.bridge.METATRADER_CACHE)
            try:
                self.bridge.RUNTIME_DIR = root / "runtime"
                self.bridge.METATRADER_CACHE.update({"payload": None, "fetchedMonotonic": 0.0})
                payload = self.bridge.metatrader_status(
                    force=True,
                    roots=[terminal_root],
                    process_rows=['"terminal.exe","111","Console"', '"terminal64.exe","222","Console"'],
                )
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.METATRADER_CACHE.clear()
                self.bridge.METATRADER_CACHE.update(original_cache)
        self.assertEqual(payload["mode"], "read_only")
        self.assertFalse(payload["sideEffects"])
        self.assertEqual(payload["adapterConnection"], "coming_soon")
        self.assertFalse(payload["adapterReady"])
        self.assertEqual(payload["platforms"]["mt4"]["installedCount"], 1)
        self.assertEqual(payload["platforms"]["mt5"]["installedCount"], 1)
        self.assertEqual(payload["platforms"]["mt4"]["runningCount"], 1)
        self.assertEqual(payload["platforms"]["mt5"]["runningCount"], 1)
        self.assertEqual(payload["candidateCount"], 2)
        for candidate in payload["candidates"]:
            self.assertEqual(set(candidate), {"candidateId", "platform", "labelTh", "detected", "runningState"})
            self.assertTrue(candidate["candidateId"].startswith("mtc-"))
            self.assertIn(candidate["platform"], {"mt4", "mt5"})
            self.assertTrue(candidate["detected"])
            self.assertIn(candidate["runningState"], {"unknown", "platform_running_detected", "not_running_detected"})
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn(str(terminal_root).lower(), serialized)
        for forbidden in ("account", "broker_server", "terminal_path", "process_id"):
            self.assertNotIn(forbidden, serialized)

    def test_unknown_metatrader_candidate_is_rejected_before_mission_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            originals = {
                "RUNTIME_DIR": self.bridge.RUNTIME_DIR,
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "AGENT_EVENTS_PATH": self.bridge.AGENT_EVENTS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
            }
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                with self.assertRaises(self.bridge.RequestError) as raised:
                    self.bridge.select_metatrader_target("right_server_racks", f"mtc-{'0' * 32}")
                self.assertEqual(raised.exception.status, 404)
                self.assertEqual(self.bridge.load_missions(), [])
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)

    def test_stale_metatrader_candidate_is_rejected_without_selection_or_mission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            terminal_root = root / "terminals"
            profile = terminal_root / "profile-four"
            (profile / "MQL4").mkdir(parents=True)
            originals = {
                "RUNTIME_DIR": self.bridge.RUNTIME_DIR,
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "AGENT_EVENTS_PATH": self.bridge.AGENT_EVENTS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
            }
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                discovered = self.bridge.metatrader_status(
                    force=True,
                    roots=[terminal_root],
                    process_rows=[],
                )
                candidate_id = discovered["candidates"][0]["candidateId"]
                profile.rename(terminal_root / "profile-four-removed")
                with self.assertRaises(self.bridge.RequestError) as raised:
                    self.bridge.select_metatrader_target("right_server_racks", candidate_id)
                self.assertEqual(raised.exception.status, 409)
                self.assertEqual(self.bridge.load_missions(), [])
                persisted = json.loads((runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(encoding="utf-8"))
                self.assertEqual(persisted["selections"], {})
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)

    def test_terminal_target_selection_persists_per_prop_with_mission_report_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            terminal_root = root / "terminals"
            (terminal_root / "profile-four" / "MQL4").mkdir(parents=True)
            originals = {
                "RUNTIME_DIR": self.bridge.RUNTIME_DIR,
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "AGENT_EVENTS_PATH": self.bridge.AGENT_EVENTS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
                "check_rate_limit": self.bridge.check_rate_limit,
                "bridge_status": self.bridge.bridge_status,
            }
            original_cache = dict(self.bridge.METATRADER_CACHE)
            fake_bridge = {
                "mode": "Codex Runner Ready",
                "status": "guarded",
                "codex": {"status": "ready"},
                "mcp": {"status": "config_present", "configPresent": True},
                "time": "2026-07-23T00:00:00+00:00",
            }
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.check_rate_limit = lambda *args, **kwargs: (True, 0)
                self.bridge.bridge_status = lambda: fake_bridge
                self.bridge.METATRADER_CACHE.update({"payload": None, "fetchedMonotonic": 0.0})
                discovered = self.bridge.metatrader_status(
                    force=True,
                    roots=[terminal_root],
                    process_rows=['"terminal.exe","111","Console"'],
                )
                with self.bridge.METATRADER_CACHE_LOCK:
                    self.bridge.METATRADER_CACHE.update({"payload": discovered, "fetchedMonotonic": time.monotonic()})
                candidate = discovered["candidates"][0]
                results = [
                    self.bridge.select_metatrader_target("right_server_racks", candidate["candidateId"]),
                    self.bridge.select_metatrader_target("terminal_workstation", candidate["candidateId"]),
                ]

                for result, prop_id in zip(results, ("right_server_racks", "terminal_workstation")):
                    self.assertTrue(result["ok"])
                    self.assertEqual(result["status"], "completed")
                    self.assertEqual(result["selection"]["propId"], prop_id)
                    self.assertEqual(result["selection"]["status"], "selected")
                    self.assertEqual(result["selection"]["configurationStatus"], "configured")
                    self.assertEqual(result["selection"]["adapterConnection"], "coming_soon")
                    self.assertFalse(result["selection"]["adapterReady"])
                    self.assertEqual(set(result["selection"]["selectedCandidate"]), {"candidateId", "platform", "labelTh", "detected", "runningState"})
                    self.assertEqual(result["report"]["type"], "terminal_selection_report")
                    self.assertEqual(result["report"]["linkedPropId"], prop_id)
                    selection_model = result["connectionChecklist"]["metatraderSelection"]
                    self.assertEqual(selection_model["configurationStatus"], "configured")
                    self.assertEqual(selection_model["adapterConnection"], "coming_soon")
                    selected_item = next(
                        item for item in result["connectionChecklist"]["items"]
                        if item["id"] == "mt4_terminal"
                    )
                    self.assertEqual(selected_item["detectionStatus"], "detected")
                    self.assertEqual(selected_item["configurationStatus"], "configured")
                    self.assertEqual(selected_item["executionAdapterStatus"], "coming_soon")
                    self.assertFalse(selected_item["adapterReady"])

                persisted = json.loads((runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(encoding="utf-8"))
                self.assertEqual(set(persisted["selections"]), {"right_server_racks", "terminal_workstation"})
                self.assertEqual(persisted["selections"]["right_server_racks"]["candidateId"], candidate["candidateId"])
                self.assertEqual(persisted["selections"]["terminal_workstation"]["candidateId"], candidate["candidateId"])

                missions = self.bridge.load_missions()
                self.assertEqual(len(missions), 2)
                self.assertTrue(all(mission["toolId"] == "terminal_target_select" for mission in missions))
                self.assertTrue(all(mission["status"] == "completed" for mission in missions))
                reports = [report for report in self.bridge.load_runtime_reports() if report["type"] == "terminal_selection_report"]
                self.assertEqual({report["linkedPropId"] for report in reports}, {"right_server_racks", "terminal_workstation"})
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                selected_events = [item for item in audit if item.get("type") == "terminal.target_selected"]
                self.assertEqual({item["dashboardId"] for item in selected_events}, {"right_server_racks", "terminal_workstation"})
                self.assertTrue(all(item["adapterConnection"] == "coming_soon" and item["adapterReady"] is False for item in selected_events))

                serialized_public = json.dumps(results, ensure_ascii=False).lower()
                self.assertNotIn(str(terminal_root).lower(), serialized_public)
                for forbidden in ("terminal_path", "process_id", "account_number", "broker_server", "password=", "password:"):
                    self.assertNotIn(forbidden, serialized_public)
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)
                self.bridge.METATRADER_CACHE.clear()
                self.bridge.METATRADER_CACHE.update(original_cache)

    def test_dashboard_checklist_keeps_detected_terminal_distinct_from_connected_adapter(self) -> None:
        fake_bridge = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-23T00:00:00+00:00",
        }
        terminals = self.bridge.metatrader_status_read_model(
            {"mt4": 1, "mt5": 1},
            {"supported": True, "mt4": 1, "mt5": 1},
        )
        checklist = self.bridge.dashboard_connection_checklist(
            "right_server_racks",
            bridge=fake_bridge,
            quota={"ok": True, "status": "ready", "primary": {"usedPercent": 15, "remainingPercent": 85}},
            terminals=terminals,
        )
        items = {item["id"]: item for item in checklist["items"]}
        self.assertEqual(items["mt4_terminal"]["status"], "detected")
        self.assertEqual(items["mt5_terminal"]["status"], "detected")
        self.assertEqual(items["mt4_terminal"]["adapterStatus"], "runtime_detected")
        self.assertEqual(items["mt4_terminal"]["executionAdapterStatus"], "coming_soon")
        self.assertEqual(items["optimization_adapter"]["status"], "coming_soon")
        self.assertEqual(checklist["connectionRequirements"]["anyOf"], ["mt4_terminal", "mt5_terminal"])
        self.assertTrue(checklist["connectionRequirements"]["anyOfSatisfied"])
        self.assertEqual(checklist["overallStatus"], "partial")
        self.assertEqual(checklist["operationMode"]["aiEveryTwoHours"]["status"], "coming_soon")
        self.assertFalse(checklist["operationMode"]["aiEveryTwoHours"]["enabled"])

    def test_mt_any_of_requirement_accepts_one_platform_and_rejects_none(self) -> None:
        fake_bridge = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-23T00:00:00+00:00",
        }
        mt4_only = self.bridge.metatrader_status_read_model(
            {"mt4": 1, "mt5": 0},
            {"supported": True, "mt4": 0, "mt5": 0},
        )
        one_found = self.bridge.dashboard_connection_checklist(
            "right_server_racks",
            bridge=fake_bridge,
            terminals=mt4_only,
        )
        self.assertTrue(one_found["connectionRequirements"]["anyOfSatisfied"])
        self.assertEqual(one_found["connectionRequirements"]["status"], "ready")
        self.assertEqual(one_found["overallStatus"], "partial")

        none_found = self.bridge.metatrader_status_read_model(
            {"mt4": 0, "mt5": 0},
            {"supported": True, "mt4": 0, "mt5": 0},
        )
        missing = self.bridge.dashboard_connection_checklist(
            "right_server_racks",
            bridge=fake_bridge,
            terminals=none_found,
        )
        self.assertFalse(missing["connectionRequirements"]["anyOfSatisfied"])
        self.assertEqual(missing["connectionRequirements"]["status"], "needs_attention")
        self.assertEqual(missing["overallStatus"], "needs_attention")

    def test_optional_coming_soon_adapter_keeps_dashboard_truthfully_partial(self) -> None:
        fake_bridge = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-23T00:00:00+00:00",
        }
        checklist = self.bridge.dashboard_connection_checklist(
            "left_server_racks",
            bridge=fake_bridge,
        )
        self.assertTrue(any(not item["required"] and item["status"] == "coming_soon" for item in checklist["items"]))
        self.assertEqual(checklist["overallStatus"], "partial")

    def test_checklist_overall_checked_at_is_null_until_every_relevant_probe_has_run(self) -> None:
        fake_bridge = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-23T00:00:00+00:00",
        }
        terminals_not_checked = {
            "status": "not_checked",
            "mode": "read_only",
            "sideEffects": False,
            "adapterConnection": "coming_soon",
            "platforms": {
                "mt4": {"status": "not_checked", "detailTh": "ยังไม่ได้ตรวจ"},
                "mt5": {"status": "not_checked", "detailTh": "ยังไม่ได้ตรวจ"},
            },
            "checkedAt": None,
            "cacheHit": False,
            "cacheAgeSeconds": None,
        }
        checklist = self.bridge.dashboard_connection_checklist(
            "right_server_racks",
            bridge=fake_bridge,
            terminals=terminals_not_checked,
        )
        items = {item["id"]: item for item in checklist["items"]}
        self.assertEqual(items["local_bridge"]["checkedAt"], "2026-07-23T00:00:00Z")
        self.assertIsNone(items["mt4_terminal"]["checkedAt"])
        self.assertFalse(checklist["freshnessComplete"])
        self.assertIsNone(checklist["checkedAt"])
        self.assertEqual(checklist["overallStatus"], "not_checked")

    def test_metatrader_discovery_action_has_mission_audit_and_routed_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            originals = {
                "RUNTIME_DIR": self.bridge.RUNTIME_DIR,
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "AGENT_EVENTS_PATH": self.bridge.AGENT_EVENTS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
                "metatrader_status": self.bridge.metatrader_status,
            }
            terminal_state = self.bridge.metatrader_status_read_model(
                {"mt4": 1, "mt5": 0},
                {"supported": True, "mt4": 1, "mt5": 0},
            )
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.metatrader_status = lambda force=False: terminal_state
                result = self.bridge.run_metatrader_discovery("terminal_workstation")
                self.assertTrue(result["ok"])
                self.assertEqual(result["status"], "completed")
                self.assertTrue(result["missionId"].startswith("mission-"))
                missions = self.bridge.load_missions()
                mission = next(item for item in missions if item["id"] == result["missionId"])
                self.assertEqual(mission["toolId"], "terminal_discovery")
                self.assertEqual(mission["status"], "completed")
                reports = self.bridge.load_runtime_reports()
                report = next(item for item in reports if item["linkedMissionId"] == mission["id"])
                self.assertEqual(report["linkedPropId"], "terminal_workstation")
                allowed_report_statuses = set(
                    json.loads((PROJECT_ROOT / "contracts" / "reports" / "report-contract.json").read_text(encoding="utf-8"))["base_report_schema"]["status"].split("|")
                )
                self.assertIn(report["status"], allowed_report_statuses)
                self.assertEqual(report["status"], "ready")
                self.assertEqual(report["metrics"]["diagnosticStatus"], "detected")
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertTrue(any(item.get("type") == "terminal.discovery" and item.get("missionId") == mission["id"] for item in audit))
                serialized = json.dumps(result, ensure_ascii=False).lower()
                for forbidden in ("processid", "terminal_path", "broker_server", "password="):
                    self.assertNotIn(forbidden, serialized)
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)

    def test_diagnostic_exceptions_fail_the_created_mission_and_write_audit(self) -> None:
        scenarios = (
            (
                "dashboard_connection",
                "bridge_status",
                lambda: self.bridge.refresh_dashboard_connections("right_server_racks"),
                "dashboard.connection_check_failed",
                "dashboard_connection_check_failed",
            ),
            (
                "terminal_discovery",
                "metatrader_status",
                lambda: self.bridge.run_metatrader_discovery("terminal_workstation"),
                "terminal.discovery_failed",
                "terminal_discovery_failed",
            ),
        )
        for scenario, failing_probe, invoke, audit_type, error_code in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                runtime = Path(directory) / "runtime"
                originals = {
                    "RUNTIME_DIR": self.bridge.RUNTIME_DIR,
                    "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                    "AUDIT_PATH": self.bridge.AUDIT_PATH,
                    "AGENT_EVENTS_PATH": self.bridge.AGENT_EVENTS_PATH,
                    "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
                    "check_rate_limit": self.bridge.check_rate_limit,
                    failing_probe: getattr(self.bridge, failing_probe),
                }

                def fail_probe(*args, **kwargs):
                    raise RuntimeError("synthetic diagnostic probe failure")

                try:
                    self.bridge.RUNTIME_DIR = runtime
                    self.bridge.MISSIONS_PATH = runtime / "missions.json"
                    self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                    self.bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
                    self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                    self.bridge.check_rate_limit = lambda *args, **kwargs: (True, 0)
                    setattr(self.bridge, failing_probe, fail_probe)
                    with self.assertRaises(RuntimeError):
                        invoke()
                    missions = self.bridge.load_missions()
                    self.assertEqual(len(missions), 1)
                    self.assertEqual(missions[0]["status"], "failed")
                    self.assertEqual(missions[0]["phase"], "diagnostic_failed")
                    self.assertEqual(missions[0]["errorCode"], error_code)
                    self.assertEqual(missions[0]["reportIds"], [])
                    audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                    failure_event = next(item for item in audit if item.get("type") == audit_type)
                    self.assertEqual(failure_event["missionId"], missions[0]["id"])
                    self.assertFalse(failure_event["automaticRetry"])
                    self.assertFalse(failure_event["sideEffects"])
                finally:
                    for name, value in originals.items():
                        setattr(self.bridge, name, value)

    def test_mission_table_aggregates_dashboard_summary_reports_once(self) -> None:
        fake_status = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready", "version": "codex-cli 1", "runner": "project_sdk"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-23T00:00:00+00:00",
        }
        reports = [
            {"id": "report-opt", "type": "optimization_report", "title": "Optimization", "linkedPropId": "right_server_racks", "status": "ready"},
            {"id": "report-backtest", "type": "backtest_report", "title": "Backtest", "linkedPropId": "left_analytics_console", "status": "ready"},
            {"id": "report-plan", "type": "mission_plan", "title": "Plan", "linkedPropId": "mission_strategy_table", "status": "ready"},
            {"id": "report-opt", "type": "optimization_report", "title": "Duplicate", "linkedPropId": "right_server_racks", "status": "ready"},
            {"id": "report-foreign", "type": "prop_report", "title": "Foreign", "linkedPropId": "unknown_prop", "status": "ready"},
        ]
        originals = {
            "bridge_status": self.bridge.bridge_status,
            "load_missions": self.bridge.load_missions,
            "load_agent_events": self.bridge.load_agent_events,
            "load_runtime_reports": self.bridge.load_runtime_reports,
            "load_meeting_records": self.bridge.load_meeting_records,
            "search_memory_items": self.bridge.search_memory_items,
        }
        try:
            self.bridge.bridge_status = lambda: fake_status
            self.bridge.load_missions = lambda: []
            self.bridge.load_agent_events = lambda limit=120: []
            self.bridge.load_runtime_reports = lambda limit=120: reports
            self.bridge.load_meeting_records = lambda limit=120: []
            self.bridge.search_memory_items = lambda query="", limit=12: []
            table = self.bridge.prop_report("mission_strategy_table")
            report_ids = [report["id"] for report in table["reports"]]
            self.assertEqual(report_ids, ["report-opt", "report-backtest", "report-plan"])
            self.assertEqual(table["reportScope"], "dashboard_summaries")
            self.assertEqual(table["reportSummary"]["total"], 3)
            self.assertIn("right_server_racks", table["summarySourcePropIds"])
            self.assertIn("left_analytics_console", table["summarySourcePropIds"])
            self.assertNotIn("report-foreign", report_ids)
        finally:
            for name, value in originals.items():
                setattr(self.bridge, name, value)

    def test_cross_contract_agent_prop_tool_and_report_routes_are_consistent(self) -> None:
        contracts = PROJECT_ROOT / "contracts"
        agents_payload = json.loads((contracts / "agents" / "agents.json").read_text(encoding="utf-8"))
        room_payload = json.loads((contracts / "rooms" / "command-room.json").read_text(encoding="utf-8"))
        role_payload = json.loads((contracts / "props" / "property-role-map.json").read_text(encoding="utf-8"))
        tool_payload = json.loads((contracts / "tools" / "tool-permission-contract.json").read_text(encoding="utf-8"))
        report_payload = json.loads((contracts / "reports" / "report-contract.json").read_text(encoding="utf-8"))
        orchestration_payload = json.loads((contracts / "orchestration" / "orchestration-contract.json").read_text(encoding="utf-8"))

        agent_ids = {str(item["id"]) for item in agents_payload["agents"]}
        prop_ids = {str(item["id"]) for item in room_payload["props"]}
        role_map = role_payload.get("properties") or {}
        report_types = set((report_payload.get("report_targets") or {}).keys())

        self.assertEqual(set(role_map.keys()), prop_ids)
        for agent in agents_payload["agents"]:
            with self.subTest(agent=agent["id"]):
                self.assertIn(agent["visual"]["default_target"], prop_ids)

        for prop_id, role in role_map.items():
            with self.subTest(prop=prop_id):
                actor_fields = (
                    "primaryOwnerAgentId",
                    "contributorAgentIds",
                    "reviewerAgentIds",
                    "approverAgentIds",
                    "ownerAgents",
                )
                referenced_agents = set()
                for field in actor_fields:
                    value = role.get(field)
                    referenced_agents.update(value if isinstance(value, list) else ([value] if value else []))
                self.assertTrue(referenced_agents.issubset(agent_ids))
                self.assertTrue(set(role.get("acceptedReportTypes") or []).issubset(report_types))

        for tool in tool_payload["tools"]:
            with self.subTest(tool=tool["id"]):
                self.assertTrue(set(tool.get("allowedAgents") or []).issubset(agent_ids))
                self.assertTrue(set(tool.get("linkedPropIds") or []).issubset(prop_ids))

        for report_type, targets in report_payload["report_targets"].items():
            with self.subTest(report=report_type):
                self.assertTrue(set(targets).issubset(agent_ids | prop_ids))

        manager_rules = orchestration_payload["managerAutoDelegation"]
        for rule in [*(manager_rules.get("specialistRules") or []), manager_rules.get("fallback") or {}]:
            with self.subTest(rule=rule.get("id", "fallback")):
                self.assertIn(rule["agentId"], agent_ids)
                self.assertIn(rule["targetPropId"], prop_ids)
                self.assertIn(rule["reportType"], report_types)

    def test_frontend_execution_requires_a_separate_exact_mission_confirmation(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.assertIn('id="modalKanbanExecuteMissionId"', html)
        self.assertIn('id="modalKanbanExecute"', html)

        readiness_start = main.index("function isMissionReadyForExplicitExecution(mission)")
        readiness_end = main.index("\nfunction setMissionExecuteStatus", readiness_start)
        readiness_block = main[readiness_start:readiness_end]
        self.assertIn("return mission.readyToExecute === true;", readiness_block)
        self.assertNotIn('getMissionApprovalState(mission) === "approved"', readiness_block)

        execute_start = main.index("async function executeApprovedKanbanMission()")
        execute_end = main.index("\nfunction setModalTab", execute_start)
        execute_block = main[execute_start:execute_end]
        confirmation_check = execute_block.index("confirmation !== mission.id")
        guarded_post = execute_block.index("postJson(`/api/missions/${encodeURIComponent(mission.id)}/execute`")
        self.assertLess(confirmation_check, guarded_post)
        self.assertIn("confirmMissionId: mission.id", execute_block)
        self.assertIn("No automatic retry", execute_block)

        approval_start = main.index("async function recordKanbanApprovalDecision(decision)")
        approval_end = main.index("async function executeApprovedKanbanMission()", approval_start)
        self.assertNotIn("/execute", main[approval_start:approval_end])

    def test_frontend_prefers_allowed_surfaces_with_legacy_tool_fallback(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        preferred = main.index("Array.isArray(contract.allowed_surfaces)")
        legacy = main.index("Array.isArray(contract.allowed_tools)", preferred)
        assignment = main.index("allowedSurfaces,", legacy)
        self.assertLess(preferred, legacy)
        self.assertLess(legacy, assignment)

    def test_codex_rate_widget_is_backend_only_nonblocking_and_not_persisted(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        for element_id in (
            "codexRateWidget",
            "codexRateSummary",
            "codexRateProgress",
            "codexRateReset",
            "codexRateFreshness",
            "codexRateRefreshButton",
        ):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn('const CODEX_RATE_LIMIT_ENDPOINT = "/api/codex/rate-limits";', main)
        self.assertIn("const CODEX_RATE_LIMIT_POLL_MS = 60000;", main)
        self.assertIn('document.visibilityState === "visible"', main)
        self.assertIn("window.setTimeout(startCodexRateLimitPolling, 0);", main)
        self.assertIn('state.codexRate.inFlight', main)
        self.assertIn('["auth_required", "config_error", "missing"]', main)
        save_start = main.index("function saveSessionSnapshot()")
        save_end = main.index("\nfunction clearSessionSnapshot()", save_start)
        self.assertNotIn("codexRate", main[save_start:save_end])

    def test_frontend_dashboard_connection_controls_are_backend_intents_only(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")
        for element_id in (
            "modalDashboardConnectionList",
            "modalDashboardRefreshConnections",
            "modalDashboardDiscoverMetatrader",
            "modalDashboardOperationMode",
            "modalDashboardScheduleStatus",
        ):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn("/connections/refresh`, { propId })", main)
        self.assertNotIn("/connections?refresh=1", main)
        self.assertIn('postJson("/api/integrations/metatrader/discover", { propId })', main)
        self.assertIn('item?.action === "discover_metatrader"', main)
        update_start = main.index("async function updatePropReportFromDashboardAction")
        update_end = main.index("\nasync function refreshDashboardConnections", update_start)
        update_block = main[update_start:update_end]
        self.assertNotIn("...response.report", update_block)
        self.assertIn("loadPropReport(propId)", update_block)
        self.assertIn('.connection-badge[data-status="coming_soon"]', styles)
        for forbidden in ("terminal.exe", "terminal64.exe", "tasklist", "Get-Process"):
            self.assertNotIn(forbidden, main)

    def test_frontend_terminal_selection_posts_only_opaque_intent_and_uses_thai_controls(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        for element_id in (
            "modalDashboardMetatraderSelection",
            "modalDashboardMetatraderSummary",
            "modalDashboardMetatraderCandidates",
            "modalDashboardConfirmMetatrader",
        ):
            self.assertIn(f'id="{element_id}"', html)
        for thai_copy in ("เลือก Terminal เป้าหมาย", "Adapter ยังไม่พร้อม", "ยืนยัน Terminal ที่เลือก"):
            self.assertIn(thai_copy, html)
        self.assertIn('id="modalDashboardConfirmMetatrader" type="button" disabled', html)

        normalize_start = main.index("function normalizeMetatraderCandidate(candidate)")
        normalize_end = main.index("\nfunction getMetatraderSelectionModel", normalize_start)
        normalize_block = main[normalize_start:normalize_end]
        for safe_field in ("candidateId", "platform", "labelTh", "detected", "runningState"):
            self.assertIn(safe_field, normalize_block)
        for forbidden in ("candidate.path", "candidate.pid", "candidate.processId", "candidate.account", "candidate.broker", "candidate.status"):
            self.assertNotIn(forbidden, normalize_block)

        render_start = main.index("function renderMetatraderSelection(subject, checklist, canDiscoverMetatrader)")
        render_end = main.index("\nfunction renderDashboardConnectionPanel", render_start)
        render_block = main[render_start:render_end]
        self.assertIn("hidden = !canDiscoverMetatrader", render_block)
        self.assertIn("modalDashboardConfirmMetatrader.disabled", render_block)

        confirm_start = main.index("async function confirmMetatraderSelection(propId)")
        confirm_end = main.index("\nfunction isMetatraderDiscoveryIntent", confirm_start)
        confirm_block = main[confirm_start:confirm_end]
        exact_post = 'postJson("/api/integrations/metatrader/select", { propId, candidateId })'
        self.assertEqual(confirm_block.count(exact_post), 1)
        self.assertIn("await loadPropReport(propId)", confirm_block)
        self.assertNotIn("...response", confirm_block)
        for forbidden in ("terminalPath", "processId", "accountNumber", "brokerServer", "password"):
            self.assertNotIn(forbidden, confirm_block)

    def test_visual_office_polls_missions_preserves_active_workers_and_renders_report_truth(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        self.assertIn("const MISSION_POLL_MS = 12000;", main)
        self.assertIn("window.setTimeout(startMissionPolling, 0);", main)
        self.assertIn("function reconcileAgentMissionState()", main)
        self.assertIn("&& !agent.activeMissionId", main)
        self.assertIn("structuredReportItems", main)
        self.assertIn("capabilityDashboardItems", main)
        self.assertIn("report?.meetings", main)
        self.assertIn("report?.bridge", main)
        for status in ("queued", "running", "waiting_approval", "blocked", "completed", "failed", "archived"):
            self.assertIn(f".kanban-column.status-{status}", styles)

    def test_operational_sidebars_replace_visible_legacy_controls(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        for element_id in (
            "agentStatusPanel",
            "agentStatusList",
            "todayWorkPanel",
            "todayWorkDate",
            "todayRunningList",
            "todayRunningCount",
            "todayCompletedList",
            "todayCompletedCount",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'document.getElementById("{element_id}")', main)

        self.assertIn('id="legacySidebarBindings" hidden aria-hidden="true"', html)
        for removed_visible_class in ("layer-panel", "report-panel", "command-console", "status-strip"):
            self.assertNotIn(f'class="{removed_visible_class}"', html)

        all_ids = re.findall(r'\bid="([^"]+)"', html)
        self.assertEqual(len(all_ids), len(set(all_ids)), "Frontend element IDs must remain unique.")
        self.assertGreaterEqual(main.count("renderOperationalSidebars();"), 2)

        desktop_compact = styles[styles.index("@media (max-width: 1180px)"):]
        mobile = styles[styles.index("@media (max-width: 720px)"):]
        for responsive_block in (desktop_compact, mobile):
            self.assertIn(".agent-status-panel", responsive_block)
            self.assertIn(".today-work-panel", responsive_block)

    def test_agent_status_sidebar_reserves_red_for_confirmed_runtime_unavailability(self) -> None:
        agents = json.loads(
            (PROJECT_ROOT / "contracts" / "agents" / "agents.json").read_text(encoding="utf-8")
        )["agents"]
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        def function_block(name: str) -> str:
            start = main.index(f"function {name}(")
            next_function = main.find("\nfunction ", start + 1)
            next_async_function = main.find("\nasync function ", start + 1)
            candidates = [value for value in (next_function, next_async_function) if value >= 0]
            return main[start:min(candidates) if candidates else len(main)]

        self.assertEqual(len(agents), 10)
        status_block = function_block("getAgentSidebarState")
        card_block = function_block("createAgentStatusCard")
        render_block = function_block("renderAgentStatusPanel")

        for state_key in ("available", "busy", "unavailable"):
            self.assertIn(f'key: "{state_key}"', status_block)
            self.assertIn(f".agent-state-dot.{state_key}", styles)
            self.assertIn(f".agent-status-card.{state_key}", styles)
        self.assertIn('label: "ว่าง"', status_block)
        self.assertIn('label: "ติดต่อไม่ได้"', status_block)
        self.assertNotIn('key: "blocked"', status_block)
        self.assertNotIn('label: "ติดขัด"', status_block)
        self.assertIn('getMissionPresentationStatus(item) === "running"', status_block)
        for inactive_status in ("waiting_approval", "queued", "blocked"):
            self.assertNotIn(f'getMissionPresentationStatus(item) === "{inactive_status}"', status_block)
        self.assertNotIn("taskLabelByStatus", status_block)
        self.assertNotIn("missionStatus", status_block)
        self.assertRegex(status_block, r'return\s*\{\s*key:\s*"busy"')
        self.assertIn('state.bridge.status === "Backend ออฟไลน์"', status_block)
        self.assertNotIn("if (!state.bridge.apiOnline)", status_block)
        self.assertLess(
            status_block.index('key: "unavailable"'),
            status_block.index("if (mission)"),
            "Confirmed runtime unavailability must be evaluated independently from Mission status.",
        )
        self.assertIn("state.officeAgents.forEach", render_block)
        self.assertIn("createAgentStatusCard(agent)", render_block)
        self.assertNotIn(".slice(", render_block)

        self.assertIn('document.createElement("button")', card_block)
        self.assertIn("card.dataset.agentId = agent.id", card_block)
        self.assertIn("mission?.title", card_block)
        self.assertIn("displayPropName(targetId", card_block)
        self.assertIn("openTaskDetail(mission.id", card_block)
        self.assertIn("openAgentDialog(agent.id)", card_block)
        self.assertIn("openPropReport(targetId)", card_block)

        for state_key, color in (("available", "--green"), ("busy", "--amber"), ("unavailable", "--red")):
            start = styles.index(f".agent-state-dot.{state_key} {{")
            end = styles.index("\n}", start)
            self.assertIn(f"var({color})", styles[start:end])
        self.assertIn('<i class="agent-state-dot unavailable" aria-hidden="true"></i>ติดต่อไม่ได้', html)
        self.assertNotIn('<i class="agent-state-dot blocked" aria-hidden="true"></i>ติดขัด', html)

    def test_today_work_sidebar_filters_completed_by_local_day_and_opens_task_details(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        def function_block(name: str) -> str:
            start = main.index(f"function {name}(")
            next_function = main.find("\nfunction ", start + 1)
            next_async_function = main.find("\nasync function ", start + 1)
            candidates = [value for value in (next_function, next_async_function) if value >= 0]
            return main[start:min(candidates) if candidates else len(main)]

        today_filter = function_block("isMissionCompletedToday")
        today_card = function_block("createTodayWorkCard")
        today_panel = function_block("renderTodayWorkPanel")

        self.assertIn('getMissionPresentationStatus(mission) !== "completed"', today_filter)
        self.assertIn("mission.completedAt || mission.updatedAt", today_filter)
        for local_date_part in ("getFullYear()", "getMonth()", "getDate()"):
            self.assertIn(local_date_part, today_filter)
        self.assertNotIn("toISOString()", today_filter)

        self.assertIn('getMissionPresentationStatus(mission) === "running"', today_panel)
        for inactive_status in ("waiting_approval", "blocked"):
            self.assertNotIn(f'"{inactive_status}"', today_panel)
        self.assertIn("isMissionCompletedToday(mission)", today_panel)
        self.assertIn("todayRunningCount", today_panel)
        self.assertIn("todayCompletedCount", today_panel)
        self.assertIn("renderTodayWorkList(els.todayRunningList", today_panel)
        self.assertIn("renderTodayWorkList(els.todayCompletedList", today_panel)

        self.assertIn('document.createElement("button")', today_card)
        self.assertIn('setAttribute("aria-haspopup", "dialog")', today_card)
        self.assertIn("displayPropName(mission.targetId", today_card)
        self.assertIn("openTaskDetail(mission.id", today_card)
        self.assertIn('id="modalKanbanOpenTargetProp"', html)
        self.assertIn("openPropDialog(targetId)", main)

        # The side-panel redesign must not replace the existing Agent chat,
        # nine-dashboard tabs, Mission Kanban, or shared detail dialogs.
        for preserved_id in (
            "gameModal",
            "modalChatPanel",
            "modalDashboardPanel",
            "modalKanbanPanel",
            "taskDetailDialog",
            "dashboardResultDialog",
        ):
            self.assertIn(f'id="{preserved_id}"', html)
        self.assertIn('agent: ["chat", "tasks"]', main)
        self.assertIn('dashboard: ["connections", "tasks", "results"]', main)
        self.assertIn('kanban: ["kanban"]', main)
        self.assertIn("postJson(AGENT_CHAT_ENDPOINT", main)

    def test_modal_layers_fill_the_usable_viewport_and_keep_actions_visible(self) -> None:
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        modal_start = styles.index(".game-modal {")
        modal_end = styles.index("\n.game-modal.open", modal_start)
        modal_rule = styles[modal_start:modal_end]
        self.assertIn("top: 104px;", modal_rule)
        self.assertIn("bottom: 14px;", modal_rule)
        self.assertIn("max-height: none;", modal_rule)

        body_start = styles.index(".game-modal-body {")
        body_end = styles.index("\n.modal-portrait-panel", body_start)
        body_rule = styles[body_start:body_end]
        self.assertIn("height: 100%;", body_rule)
        self.assertIn("min-height: 0;", body_rule)

        self.assertIn(".game-modal.dashboard-modal #modalDashboardPanel.active", styles)
        self.assertIn("grid-template-rows: auto minmax(0, 1fr) auto;", styles)
        self.assertIn(".game-modal.kanban-modal #modalKanbanPanel.active", styles)
        self.assertIn(".kanban-detail-body", styles)
        self.assertIn("height: 100%;\n  max-height: none;\n  overflow: auto;", styles)

    def test_completed_kanban_cards_remain_readable_scrollable_detail_buttons(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        def function_block(name: str) -> str:
            start = main.index(f"function {name}(")
            next_function = main.find("\nfunction ", start + 1)
            next_async_function = main.find("\nasync function ", start + 1)
            candidates = [value for value in (next_function, next_async_function) if value >= 0]
            return main[start:min(candidates) if candidates else len(main)]

        def css_rule(selector: str) -> str:
            start = styles.index(f"{selector} {{")
            end = styles.index("\n}", start)
            return styles[start:end]

        list_rule = css_rule(".kanban-column-list")
        self.assertIn("display: flex;", list_rule)
        self.assertIn("flex-direction: column;", list_rule)
        self.assertIn("min-height: 0;", list_rule)
        self.assertIn("overflow-y: auto;", list_rule)
        self.assertIn("overflow-x: hidden;", list_rule)
        self.assertIn("scrollbar-gutter: stable;", list_rule)

        card_layout_rule = css_rule(".kanban-column-list > .task-card")
        self.assertIn("flex: 0 0 auto;", card_layout_rule)
        self.assertRegex(card_layout_rule, r"min-height:\s*[1-9]\d*px;")
        for collapsed_style in (
            "display: none",
            "height: 0",
            "font-size: 0",
            "opacity: 0",
            "visibility: hidden",
        ):
            self.assertNotIn(collapsed_style, card_layout_rule)

        completed_rule = css_rule(".task-card.completed")
        self.assertIn("--task-accent:", completed_rule)
        for collapsed_style in (
            "display: none",
            "height: 0",
            "font-size: 0",
            "opacity: 0",
            "visibility: hidden",
        ):
            self.assertNotIn(collapsed_style, completed_rule)

        task_card_block = function_block("createTaskCard")
        self.assertIn('document.createElement("button")', task_card_block)
        self.assertIn('card.setAttribute("aria-haspopup", "dialog")', task_card_block)
        self.assertIn("card.append(topline, title)", task_card_block)
        self.assertIn('if (source === "kanban") card.appendChild(destination)', task_card_block)
        self.assertIn("card.appendChild(hint)", task_card_block)
        self.assertIn("mission.title || mission.id", task_card_block)
        self.assertIn('destination.className = "task-card-destination"', task_card_block)
        self.assertIn("displayPropName(mission.targetId", task_card_block)
        self.assertIn("เปิดดูผลลัพธ์และรายงาน", task_card_block)
        self.assertIn("openTaskDetail(mission.id", task_card_block)

        kanban_block = function_block("renderMissionKanban")
        self.assertIn("columnMissions.forEach", kanban_block)
        self.assertIn(
            'createTaskCard(mission, { variant: "kanban-card", source: "kanban" })',
            kanban_block,
        )
        self.assertIn("preserveScroll = true", kanban_block)
        self.assertIn("state.modal.kanbanScrollTop[status] = list.scrollTop", kanban_block)
        self.assertIn("list.scrollTop = Math.max", kanban_block)
        self.assertIn('list.addEventListener("scroll"', kanban_block)
        self.assertIn('id: "completed"', main)

    def test_task_detail_dialog_uses_task_only_renderers_without_raw_payload_dump(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        self.assertIn('id="taskDetailDialog"', html)
        self.assertIn('class="task-detail-dialog"', html)
        self.assertIn("taskDetailMissionId: null", main)
        self.assertIn('taskDetailDialog: document.getElementById("taskDetailDialog")', main)
        self.assertIn("function createTaskCard(", main)
        self.assertIn("function renderTaskList(", main)

        def function_block(name: str) -> str:
            start = main.index(f"function {name}(")
            next_function = main.find("\nfunction ", start + 1)
            next_async_function = main.find("\nasync function ", start + 1)
            candidates = [value for value in (next_function, next_async_function) if value >= 0]
            return main[start:min(candidates) if candidates else len(main)]

        task_card_block = function_block("createTaskCard")
        self.assertIn('document.createElement("button")', task_card_block)
        self.assertTrue(
            'type = "button"' in task_card_block or 'setAttribute("type", "button")' in task_card_block,
        )
        self.assertIn("aria-haspopup", task_card_block)
        self.assertIn('"dialog"', task_card_block)
        self.assertTrue(
            'addEventListener("click"' in task_card_block or ".onclick" in task_card_block,
        )

        modal_block = function_block("renderGameModal")
        prop_dashboard_block = function_block("renderPropDashboard")
        kanban_block = function_block("renderMissionKanban")
        self.assertIn("renderTaskList(els.modalTaskBoard", modal_block)
        self.assertIn("renderTaskList(els.modalDashboardWork", prop_dashboard_block)
        self.assertTrue(
            "renderTaskList(" in kanban_block or "createTaskCard(" in kanban_block,
            "Kanban must use the same task-card renderer as the Agent and Current Work surfaces.",
        )
        self.assertNotIn("renderTaskList(els.modalDashboardReports", main)
        self.assertNotIn("renderTaskList(els.modalDashboardStatus", main)
        self.assertIn("renderCardList(els.modalDashboardReports", prop_dashboard_block)
        self.assertIn("renderCardList(els.modalDashboardStatus", prop_dashboard_block)

        detail_block = function_block("renderMissionDetail")
        has_details_disclosure = '<details' in html.lower() or 'createElement("details")' in detail_block
        self.assertTrue(has_details_disclosure)
        self.assertIn('const facts = document.createElement("div")', detail_block)
        self.assertIn("ดูข้อมูลระบบ", f"{html}\n{detail_block}")
        self.assertIn("textContent", detail_block)
        self.assertNotIn("payloadDigest", detail_block)
        self.assertNotIn("JSON.stringify(mission", detail_block)
        self.assertNotIn("JSON.stringify(item", detail_block)
        self.assertIn("function restoreTaskDetailReturnFocus()", main)
        self.assertIn("taskDetailReturnMissionId", main)
        self.assertIn("taskDetailInUse", main)
        self.assertIn("!userIsEditing && !taskDetailInUse", main)

    def test_thai_localization_keeps_machine_statuses_and_utf8_integrity(self) -> None:
        frontend_paths = (FRONTEND_INDEX_PATH, FRONTEND_MAIN_PATH, FRONTEND_STYLES_PATH)
        for path in frontend_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                decoded = path.read_bytes().decode("utf-8")
                self.assertNotIn("\ufffd", decoded)

        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.assertIn('<html lang="th">', html)
        self.assertIn('<meta charset="utf-8"', html)

        normalize_start = main.index('function normalizeMissionStatus(status = "queued")')
        normalize_end = main.index("\nfunction getAgentIdFromOwner", normalize_start)
        normalize_block = main[normalize_start:normalize_end]
        for status in ("queued", "running", "waiting_approval", "blocked", "completed", "failed", "archived"):
            self.assertIn(f'"{status}"', normalize_block)

        # Localization is presentation-only: these backend protocol values and
        # exact-ID execution guards must remain machine-readable and unchanged.
        self.assertIn('actorId: "human"', main)
        self.assertIn('recordKanbanApprovalDecision("approved")', main)
        self.assertIn('recordKanbanApprovalDecision("rejected")', main)
        self.assertIn("confirmation !== mission.id", main)
        self.assertIn("confirmMissionId: mission.id", main)

    def test_agent_chat_calls_dedicated_backend_without_tool_fallback(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        start = main.index("async function handleModalSend()")
        end = main.index("async function handleModalAssignTask()", start)
        block = main[start:end]
        self.assertIn("postJson(AGENT_CHAT_ENDPOINT", block)
        self.assertIn("agentId: subject.id", block)
        self.assertIn("message: prompt", block)
        self.assertIn("sessionId: getAgentChatSessionId(subject.id)", block)
        self.assertIn('idempotencyKey: createAgentChatOpaqueId("visual-agent-chat")', block)
        self.assertIn("validateAgentChatResponse", block)
        self.assertIn("quotaConsumptionStatus", main)
        self.assertIn("ใช้โควตา Codex", block)
        self.assertIn("ไม่ใช้โควตา Codex ซ้ำ", block)
        self.assertIn("validated.taskCreated", block)
        self.assertIn("syncAgentChatCreatedTasks(subject, validated)", block)
        self.assertIn("ยังไม่มี Task ใหม่จากข้อความนี้", block)
        self.assertNotIn("runBridgeTask", block)
        self.assertNotIn("submitManagerCommand", block)

    def test_agent_chat_runtime_version_and_executive_tiers(self) -> None:
        self.assertEqual(self.bridge.BRIDGE_RUNTIME_VERSION, "0.9.0")
        self.assertEqual(self.bridge.role_default_model_tier("ceo"), "manager_quality")
        self.assertEqual(self.bridge.role_default_model_tier("manager"), "manager_quality")
        self.assertEqual(self.bridge.role_default_model_tier("risk_guard"), "risk_quality")

    def test_agent_chat_runner_is_ephemeral_tool_free_and_keeps_eight_exchanges(self) -> None:
        original_status = self.runner.chat_status
        original_run = self.runner.run_chat_command
        captured = {}

        def fake_chat_status():
            return {"ok": True, "status": "ready"}

        def fake_chat_command(command, timeout, stdin, cwd, output_limit=60000):
            captured.update({
                "command": list(command),
                "timeout": timeout,
                "stdin": stdin,
                "cwd": Path(cwd),
                "outputLimit": output_limit,
            })
            final_index = command.index("--output-last-message") + 1
            Path(command[final_index]).write_text(
                json.dumps({
                    "status": "completed",
                    "reply": "สวัสดีครับ ผมคือ CEO พร้อมช่วยคิดภาพรวม",
                    "intent": "conversation",
                    "taskGoal": "",
                }),
                encoding="utf-8",
            )
            return {
                "ok": True,
                "exitCode": 0,
                "stdout": "",
                "stderr": "",
                "durationMs": 9,
                "processStarted": True,
            }

        history = [
            {"role": "user" if index % 2 == 0 else "assistant", "content": f"ข้อความ {index}"}
            for index in range(20)
        ]
        try:
            self.runner.chat_status = fake_chat_status
            self.runner.run_chat_command = fake_chat_command
            result = self.runner.run_agent_chat(
                "สวัสดีครับ",
                "ceo",
                "session-runner-test",
                history=history,
                timeout=120,
                model_tier="manager_quality",
                output_limit=5000,
            )
        finally:
            self.runner.chat_status = original_status
            self.runner.run_chat_command = original_run

        self.assertTrue(result["ok"])
        self.assertEqual(result["model"], "gpt-5.5")
        self.assertEqual(result["modelTier"], "manager_quality")
        self.assertEqual(result["usage"]["contextTurns"], 16)
        self.assertTrue(result["quotaAttempted"])
        self.assertEqual(result["quotaConsumption"], "confirmed")
        self.assertFalse(result["guardrails"]["toolsEnabled"])
        self.assertFalse(result["guardrails"]["computerUseEnabled"])
        self.assertFalse(result["guardrails"]["projectWorkspaceExposed"])
        self.assertTrue(result["guardrails"]["ephemeral"])
        self.assertEqual(result["intent"], "conversation")
        self.assertEqual(result["taskGoal"], "")
        self.assertNotEqual(captured["cwd"].resolve(), PROJECT_ROOT.resolve())
        self.assertIn("--ephemeral", captured["command"])
        self.assertIn("--ignore-user-config", captured["command"])
        self.assertIn("--strict-config", captured["command"])
        self.assertIn("read-only", captured["command"])
        self.assertIn("gpt-5.5", captured["command"])
        for feature in self.runner.CHAT_DISABLED_FEATURES:
            self.assertIn(feature, captured["command"])
        self.assertIn("ชื่อ: CEO", captured["stdin"])
        self.assertIn("Owner / Executive Approver", captured["stdin"])
        self.assertIn("ห้ามใช้ Tool, Shell, Computer Use, Browser, Plugin, MCP", captured["stdin"])
        self.assertIn("intent = task_request", captured["stdin"])
        self.assertIn("Backend จะเป็นผู้สร้าง Mission หลัง Chat จบ", captured["stdin"])

    def test_agent_chat_status_uses_guarded_exec_as_auth_authority(self) -> None:
        original_bin = self.runner.CODEX_BIN
        original_command = self.runner.run_command
        calls = []

        def fake_command(command, timeout=30, stdin=None):
            calls.append(list(command))
            return {
                "ok": True,
                "exitCode": 0,
                "stdout": "codex-cli 0.test",
                "stderr": "",
                "durationMs": 1,
            }

        try:
            self.runner.CODEX_BIN = RUNNER_PATH
            self.runner.run_command = fake_command
            status = self.runner.chat_status()
        finally:
            self.runner.CODEX_BIN = original_bin
            self.runner.run_command = original_command

        self.assertTrue(status["ok"])
        self.assertEqual(status["status"], "runtime_ready")
        self.assertFalse(status["authChecked"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], [str(RUNNER_PATH), "--version"])
        self.assertNotIn("login", calls[0])
        self.assertNotIn("--ignore-user-config", calls[0])

    def test_agent_chat_runner_returns_structured_task_intent_and_rejects_secret_goal(self) -> None:
        original_status = self.runner.chat_status
        original_run = self.runner.run_chat_command
        queued_outputs = [
            {
                "status": "completed",
                "reply": "รับทราบครับ ผมจะส่งงานวิเคราะห์ไปยัง Backend",
                "intent": "task_request",
                "taskGoal": "วิเคราะห์ผล Backtest ในเครื่อง โดยสรุป Drawdown และ Profit Factor",
            },
            {
                "status": "completed",
                "reply": "รับทราบครับ",
                "intent": "task_request",
                "taskGoal": "วิเคราะห์รายงานด้วย token sk-" + ("a" * 24),
            },
        ]

        def fake_chat_command(command, timeout, stdin, cwd, output_limit=60000):
            final_index = command.index("--output-last-message") + 1
            Path(command[final_index]).write_text(
                json.dumps(queued_outputs.pop(0), ensure_ascii=False),
                encoding="utf-8",
            )
            return {
                "ok": True,
                "exitCode": 0,
                "stdout": "",
                "stderr": "",
                "durationMs": 4,
                "processStarted": True,
            }

        try:
            self.runner.chat_status = lambda: {"ok": True, "status": "ready"}
            self.runner.run_chat_command = fake_chat_command
            task = self.runner.run_agent_chat(
                "ช่วยวิเคราะห์ Backtest ให้หน่อย",
                "backtest_analyst",
                "session-task-intent",
            )
            secret_goal = self.runner.run_agent_chat(
                "ช่วยวิเคราะห์ไฟล์นี้ให้หน่อย",
                "backtest_analyst",
                "session-secret-goal",
            )
        finally:
            self.runner.chat_status = original_status
            self.runner.run_chat_command = original_run

        self.assertTrue(task["ok"])
        self.assertEqual(task["intent"], "task_request")
        self.assertIn("Backtest", task["taskGoal"])
        self.assertFalse(secret_goal["ok"])
        self.assertEqual(secret_goal["status"], "invalid_task_goal")
        self.assertNotIn("taskGoal", secret_goal)

    def test_agent_chat_runner_timeout_fallback_reports_unconfirmed_tree_kill(self) -> None:
        original_popen = self.runner.subprocess.Popen
        original_terminate = self.runner._terminate_process_tree
        original_create_job = self.runner._create_windows_kill_job
        original_resume = self.runner._resume_windows_process
        original_close_job = self.runner._close_windows_kill_job

        class HungProcess:
            pid = 4242

            def __init__(self):
                self.returncode = None
                self.killed = False
                self.communicate_calls = 0

            def communicate(self, input=None, timeout=None):
                self.communicate_calls += 1
                raise HungProcess.runner_timeout_type(["fake-codex"], timeout)

            def poll(self):
                return self.returncode

            def kill(self):
                self.killed = True
                self.returncode = -9

            def wait(self, timeout=None):
                if self.returncode is None:
                    raise HungProcess.runner_timeout_type(["fake-codex"], timeout)
                return self.returncode

        HungProcess.runner_timeout_type = self.runner.subprocess.TimeoutExpired
        process = HungProcess()
        try:
            self.runner.subprocess.Popen = lambda *args, **kwargs: process
            self.runner._create_windows_kill_job = lambda target: {"fake": True}
            self.runner._resume_windows_process = lambda target: True
            self.runner._close_windows_kill_job = (
                lambda holder: True if holder else None
            )
            self.runner._terminate_process_tree = lambda target, job_holder=None: False
            result = self.runner.run_chat_command(
                ["fake-codex"],
                timeout=1,
                stdin="hello",
                cwd=PROJECT_ROOT,
            )
        finally:
            self.runner.subprocess.Popen = original_popen
            self.runner._terminate_process_tree = original_terminate
            self.runner._create_windows_kill_job = original_create_job
            self.runner._resume_windows_process = original_resume
            self.runner._close_windows_kill_job = original_close_job

        self.assertFalse(result["ok"])
        self.assertEqual(result["exitCode"], "timeout")
        self.assertTrue(result["processStarted"])
        self.assertFalse(result["processTreeTerminated"])
        self.assertTrue(process.killed)
        self.assertEqual(process.communicate_calls, 2)

    @unittest.skipUnless(__import__("os").name == "nt", "Windows taskkill behavior")
    def test_agent_chat_runner_taskkill_nonzero_falls_back_without_false_confirmation(self) -> None:
        original_run = self.runner.subprocess.run

        class FailedTaskkill:
            returncode = 1

        class FakeProcess:
            pid = 31337

            def __init__(self):
                self.returncode = None
                self.killed = False

            def poll(self):
                return self.returncode

            def kill(self):
                self.killed = True
                self.returncode = -9

            def wait(self, timeout=None):
                return self.returncode

        process = FakeProcess()
        try:
            self.runner.subprocess.run = lambda *args, **kwargs: FailedTaskkill()
            confirmed = self.runner._terminate_process_tree(process)
        finally:
            self.runner.subprocess.run = original_run

        self.assertFalse(confirmed)
        self.assertTrue(process.killed)
        self.assertIsNotNone(process.poll())

    def test_agent_chat_backend_idempotency_context_and_no_task_creation(self) -> None:
        original_runtime = self.bridge.RUNTIME_DIR
        original_audit = self.bridge.AUDIT_PATH
        original_missions = self.bridge.MISSIONS_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_runner_script = self.bridge.CODEX_RUNNER_SCRIPT
        original_codex_limits = self.bridge.codex_rate_limits
        original_peek_limits = self.bridge.peek_codex_rate_limits
        original_rate_check = self.bridge.check_rate_limit
        original_command = self.bridge.run_safe_command
        calls = []
        quota = {
            "ok": True,
            "status": "ready",
            "limitReached": False,
            "stale": False,
            "primary": {"remainingPercent": 72},
        }

        def fake_command(
            command,
            timeout=8,
            output_limit=1200,
            input_text=None,
            *,
            kill_process_tree_on_timeout=False,
        ):
            request = json.loads(input_text)
            calls.append({
                "command": list(command),
                "request": request,
                "treeKill": kill_process_tree_on_timeout,
            })
            agent_id = command[command.index("--agent-id") + 1]
            model_tier = command[command.index("--model-tier") + 1]
            payload = {
                "ok": True,
                "status": "completed",
                "finalMessage": f"คำตอบจาก {agent_id} ครั้งที่ {len(calls)}",
                "intent": "conversation",
                "taskGoal": "",
                "agentName": agent_id,
                "durationMs": 11,
                "modelTier": model_tier,
                "model": "gpt-5.5",
                "reasoningEffort": "high" if model_tier == "manager_quality" else "low",
                "quotaAttempted": True,
                "quotaConsumption": "confirmed",
                "usage": {
                    "outputChars": 20,
                    "timeoutSeconds": 120,
                    "outputLimitChars": 5000,
                    "contextTurns": len(request["history"]),
                    "secretRedacted": False,
                },
                "guardrails": {
                    "toolsEnabled": False,
                    "computerUseEnabled": False,
                    "projectWorkspaceExposed": False,
                    "ephemeral": True,
                },
            }
            return {
                "ok": True,
                "exitCode": 0,
                "output": json.dumps(payload, ensure_ascii=False),
                "durationMs": 11,
                "processStarted": True,
            }

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.CODEX_RUNNER_PYTHON = RUNNER_PATH
                self.bridge.CODEX_RUNNER_SCRIPT = RUNNER_PATH
                self.bridge.codex_rate_limits = lambda: quota
                self.bridge.peek_codex_rate_limits = lambda: quota
                self.bridge.check_rate_limit = lambda *args, **kwargs: (True, 0)
                self.bridge.run_safe_command = fake_command
                self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge.AGENT_CHAT_INFLIGHT.clear()

                first_payload = {
                    "agentId": "ceo",
                    "message": "ช่วยอธิบายภาพรวมระบบ",
                    "sessionId": "session-main",
                    "idempotencyKey": "idem-ceo-1",
                }
                first = self.bridge.run_agent_chat_request(first_payload)
                replay = self.bridge.run_agent_chat_request(first_payload)
                second = self.bridge.run_agent_chat_request({
                    **first_payload,
                    "message": "แล้วขั้นต่อไปควรคิดเรื่องอะไร",
                    "idempotencyKey": "idem-ceo-2",
                })
                cross_agent = self.bridge.run_agent_chat_request({
                    "agentId": "manager",
                    "message": "สวัสดีครับ",
                    "sessionId": "session-main",
                    "idempotencyKey": "idem-manager-1",
                })

                self.assertTrue(first["ok"])
                self.assertEqual(first["kind"], "agent_chat")
                self.assertEqual(first["modelTier"], "manager_quality")
                self.assertTrue(first["consumesCodexQuota"])
                self.assertEqual(first["usage"]["quotaConsumptionStatus"], "confirmed")
                self.assertFalse(first["toolsExecuted"])
                self.assertFalse(first["taskCreated"])
                self.assertFalse(first["usage"]["idempotentReplay"])
                self.assertEqual(replay["turnId"], first["turnId"])
                self.assertFalse(replay["consumesCodexQuota"])
                self.assertTrue(replay["usage"]["idempotentReplay"])
                self.assertEqual(replay["usage"]["quotaConsumptionStatus"], "none")
                self.assertEqual(len(calls), 3)
                self.assertEqual(calls[0]["request"]["history"], [])
                self.assertEqual(len(calls[1]["request"]["history"]), 2)
                self.assertEqual(calls[1]["request"]["history"][0]["content"], first_payload["message"])
                self.assertEqual(calls[2]["request"]["history"], [])
                self.assertTrue(all(item["treeKill"] for item in calls))
                self.assertIn("manager_quality", calls[0]["command"])
                self.assertTrue(second["ok"])
                self.assertTrue(cross_agent["ok"])
                self.assertFalse(self.bridge.MISSIONS_PATH.exists())

                transcript_path = runtime / self.bridge.AGENT_CHAT_TRANSCRIPT_FILENAME
                transcripts = [
                    json.loads(line)
                    for line in transcript_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                self.assertEqual(len(transcripts), 3)
                self.assertTrue(all(item["toolsExecuted"] is False for item in transcripts))
                self.assertTrue(all(item["taskCreated"] is False for item in transcripts))
                self.assertTrue(all(item["quotaConsumptionStatus"] == "confirmed" for item in transcripts))
                persisted_text = "\n".join(
                    path.read_text(encoding="utf-8")
                    for path in runtime.rglob("*")
                    if path.is_file()
                )
                self.assertNotIn("idem-ceo-1", persisted_text)
                self.assertNotIn("idem-ceo-2", persisted_text)
                self.assertNotIn("idem-manager-1", persisted_text)
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RUNNER_SCRIPT = original_runner_script
                self.bridge.codex_rate_limits = original_codex_limits
                self.bridge.peek_codex_rate_limits = original_peek_limits
                self.bridge.check_rate_limit = original_rate_check
                self.bridge.run_safe_command = original_command
                self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge.AGENT_CHAT_INFLIGHT.clear()

    def test_agent_chat_validation_secret_ids_and_quota_flags_are_truthful(self) -> None:
        original_runtime = self.bridge.RUNTIME_DIR
        original_audit = self.bridge.AUDIT_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_runner_script = self.bridge.CODEX_RUNNER_SCRIPT
        original_codex_limits = self.bridge.codex_rate_limits
        original_peek_limits = self.bridge.peek_codex_rate_limits
        original_rate_check = self.bridge.check_rate_limit
        original_command = self.bridge.run_safe_command
        calls = []
        quota = {
            "ok": True,
            "status": "ready",
            "limitReached": False,
            "stale": False,
            "primary": {"remainingPercent": 72},
        }

        def fake_command(
            command,
            timeout=8,
            output_limit=1200,
            input_text=None,
            *,
            kill_process_tree_on_timeout=False,
        ):
            calls.append(json.loads(input_text))
            if calls[-1]["message"] == "auth":
                payload = {
                    "ok": False,
                    "status": "auth_required",
                    "message": "กรุณา Login Codex",
                    "quotaAttempted": False,
                    "quotaConsumption": "none",
                }
                return {
                    "ok": True,
                    "exitCode": 0,
                    "output": json.dumps(payload, ensure_ascii=False),
                    "durationMs": 2,
                    "processStarted": True,
                }
            if calls[-1]["message"] == "timeout-unconfirmed":
                payload = {
                    "ok": False,
                    "status": "timeout",
                    "message": "หมดเวลา",
                    "durationMs": 120000,
                    "quotaAttempted": True,
                    "quotaConsumption": "possible",
                    "processTreeTerminated": False,
                }
                return {
                    "ok": True,
                    "exitCode": 0,
                    "output": json.dumps(payload, ensure_ascii=False),
                    "durationMs": 120000,
                    "processStarted": True,
                }
            return {
                "ok": True,
                "exitCode": 0,
                "output": "{not-json",
                "durationMs": 2,
                "processStarted": True,
            }

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.CODEX_RUNNER_PYTHON = RUNNER_PATH
                self.bridge.CODEX_RUNNER_SCRIPT = RUNNER_PATH
                self.bridge.codex_rate_limits = lambda: quota
                self.bridge.peek_codex_rate_limits = lambda: quota
                self.bridge.check_rate_limit = lambda *args, **kwargs: (True, 0)
                self.bridge.run_safe_command = fake_command
                self.bridge.AGENT_CHAT_INFLIGHT.clear()

                missing = self.bridge.run_agent_chat_request({"agentId": "ceo", "message": "สวัสดี"})
                secret_session = "sk-" + ("a" * 20)
                secret_idempotency = "sk-" + ("b" * 20)
                blocked_session = self.bridge.run_agent_chat_request({
                    "agentId": "ceo",
                    "message": "สวัสดี",
                    "sessionId": secret_session,
                    "idempotencyKey": "idem-safe-1",
                })
                blocked_idempotency = self.bridge.run_agent_chat_request({
                    "agentId": "ceo",
                    "message": "สวัสดี",
                    "sessionId": "session-safe",
                    "idempotencyKey": secret_idempotency,
                })
                auth = self.bridge.run_agent_chat_request({
                    "agentId": "ceo",
                    "message": "auth",
                    "sessionId": "session-auth",
                    "idempotencyKey": "idem-auth-1",
                })
                auth_replay = self.bridge.run_agent_chat_request({
                    "agentId": "ceo",
                    "message": "auth",
                    "sessionId": "session-auth",
                    "idempotencyKey": "idem-auth-1",
                })
                malformed = self.bridge.run_agent_chat_request({
                    "agentId": "ceo",
                    "message": "malformed",
                    "sessionId": "session-malformed",
                    "idempotencyKey": "idem-malformed-1",
                })
                unconfirmed_timeout = self.bridge.run_agent_chat_request({
                    "agentId": "ceo",
                    "message": "timeout-unconfirmed",
                    "sessionId": "session-timeout",
                    "idempotencyKey": "idem-timeout-1",
                })

                self.assertEqual(missing["kind"], "invalid_request")
                self.assertFalse(missing["consumesCodexQuota"])
                self.assertEqual(blocked_session["kind"], "secret_blocked")
                self.assertEqual(blocked_idempotency["kind"], "secret_blocked")
                self.assertFalse(blocked_session["consumesCodexQuota"])
                self.assertFalse(blocked_idempotency["consumesCodexQuota"])
                self.assertEqual(len(calls), 3)
                self.assertEqual(auth["status"], "auth_required")
                self.assertFalse(auth["consumesCodexQuota"])
                self.assertEqual(auth["usage"]["quotaConsumptionStatus"], "none")
                self.assertFalse(auth_replay["consumesCodexQuota"])
                self.assertTrue(auth_replay["usage"]["idempotentReplay"])
                self.assertEqual(auth_replay["usage"]["quotaConsumptionStatus"], "none")
                self.assertEqual(malformed["status"], "invalid_runner_output")
                self.assertTrue(malformed["consumesCodexQuota"])
                self.assertEqual(malformed["usage"]["quotaConsumptionStatus"], "possible")
                self.assertEqual(unconfirmed_timeout["status"], "guard_cleanup_unconfirmed")
                self.assertTrue(unconfirmed_timeout["consumesCodexQuota"])
                self.assertEqual(unconfirmed_timeout["usage"]["quotaConsumptionStatus"], "possible")

                runtime_text = "\n".join(
                    path.read_text(encoding="utf-8")
                    for path in runtime.rglob("*")
                    if path.is_file()
                )
                self.assertNotIn(secret_session, runtime_text)
                self.assertNotIn(secret_idempotency, runtime_text)
                audit_records = [
                    json.loads(line)
                    for line in self.bridge.AUDIT_PATH.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                blocked_reasons = {
                    item.get("reason")
                    for item in audit_records
                    if item.get("type") == "agent.chat_blocked"
                }
                self.assertIn("missing_required_fields", blocked_reasons)
                self.assertIn("potential_secret_session", blocked_reasons)
                self.assertIn("potential_secret_idempotency", blocked_reasons)
                malformed_end = next(
                    item
                    for item in reversed(audit_records)
                    if item.get("type") == "agent.chat_end"
                    and item.get("status") == "invalid_runner_output"
                )
                self.assertEqual(malformed_end["quotaConsumptionStatus"], "possible")
                self.assertFalse(malformed_end["consumedCodexQuota"])
                self.assertTrue(malformed_end["mayHaveConsumedCodexQuota"])
                timeout_end = next(
                    item
                    for item in reversed(audit_records)
                    if item.get("type") == "agent.chat_end"
                    and item.get("status") == "guard_cleanup_unconfirmed"
                )
                self.assertFalse(timeout_end["processTreeTerminated"])
                self.assertTrue(timeout_end["mayHaveConsumedCodexQuota"])
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RUNNER_SCRIPT = original_runner_script
                self.bridge.codex_rate_limits = original_codex_limits
                self.bridge.peek_codex_rate_limits = original_peek_limits
                self.bridge.check_rate_limit = original_rate_check
                self.bridge.run_safe_command = original_command
                self.bridge.AGENT_CHAT_INFLIGHT.clear()

    def test_agent_chat_structured_task_routing_is_idempotent_and_high_impact_fails_closed(self) -> None:
        original_runtime = self.bridge.RUNTIME_DIR
        original_missions = self.bridge.MISSIONS_PATH
        original_operator_mode = self.bridge.OPERATOR_MODE_PATH
        original_audit = self.bridge.AUDIT_PATH
        original_agent_events = self.bridge.AGENT_EVENTS_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_runner_script = self.bridge.CODEX_RUNNER_SCRIPT
        original_codex_limits = self.bridge.codex_rate_limits
        original_peek_limits = self.bridge.peek_codex_rate_limits
        original_rate_check = self.bridge.check_rate_limit
        original_command = self.bridge.run_safe_command
        original_semaphore = self.bridge.REAL_RUN_SEMAPHORE
        calls = []
        quota = {
            "ok": True,
            "status": "ready",
            "limitReached": False,
            "stale": False,
            "primary": {"remainingPercent": 80},
        }
        classifications = {
            "conversation": ("conversation", ""),
            "specialist-task": (
                "task_request",
                "วิเคราะห์ผล Backtest ในเครื่อง สรุป Drawdown และ Profit Factor",
            ),
            "manager-task": (
                "task_request",
                "วิเคราะห์ Backtest และสรุป Drawdown จากรายงานในเครื่อง",
            ),
            "ceo-task": (
                "task_request",
                "ตรวจสถานะ VPS และสรุป Uptime จากข้อมูลในเครื่อง",
            ),
            "high-impact": (
                "task_request",
                "ลบไฟล์ระบบ ส่ง Telegram จริง และเปิดคำสั่ง Live Trading",
            ),
        }

        def fake_command(
            command,
            timeout=8,
            output_limit=1200,
            input_text=None,
            *,
            kill_process_tree_on_timeout=False,
            **kwargs,
        ):
            request = json.loads(input_text)
            intent, task_goal = classifications[request["message"]]
            calls.append({
                "message": request["message"],
                "command": list(command),
                "treeKill": kill_process_tree_on_timeout,
            })
            agent_id = command[command.index("--agent-id") + 1]
            model_tier = command[command.index("--model-tier") + 1]
            result = {
                "ok": True,
                "status": "completed",
                "finalMessage": f"ตอบโดย {agent_id}",
                "intent": intent,
                "taskGoal": task_goal,
                "durationMs": 5,
                "modelTier": model_tier,
                "model": "gpt-5.5",
                "quotaAttempted": True,
                "quotaConsumption": "confirmed",
                "usage": {"outputChars": 20, "contextTurns": 0},
                "guardrails": {
                    "toolsEnabled": False,
                    "computerUseEnabled": False,
                    "projectWorkspaceExposed": False,
                    "ephemeral": True,
                },
            }
            return {
                "ok": True,
                "exitCode": 0,
                "output": json.dumps(result, ensure_ascii=False),
                "durationMs": 5,
                "processStarted": True,
            }

        def chat(agent_id, message, suffix):
            return self.bridge.run_agent_chat_request({
                "agentId": agent_id,
                "message": message,
                "sessionId": f"session-{suffix}",
                "idempotencyKey": f"idem-{suffix}",
            })

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.AGENT_EVENTS_PATH = runtime / "agent-events.jsonl"
                self.bridge.CODEX_RUNNER_PYTHON = RUNNER_PATH
                self.bridge.CODEX_RUNNER_SCRIPT = RUNNER_PATH
                self.bridge.codex_rate_limits = lambda: quota
                self.bridge.peek_codex_rate_limits = lambda: quota
                self.bridge.check_rate_limit = lambda *args, **kwargs: (True, 0)
                self.bridge.run_safe_command = fake_command
                self.bridge.REAL_RUN_SEMAPHORE = threading.BoundedSemaphore(value=1)
                self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge.AGENT_CHAT_INFLIGHT.clear()
                self.bridge.MISSION_WORKER_WAKE.clear()
                self.assertEqual(
                    self.bridge.set_operator_mode({"mode": "auto_guarded"})["mode"],
                    "auto_guarded",
                )

                conversation = chat("backtest_analyst", "conversation", "conversation")
                self.assertTrue(conversation["ok"])
                self.assertEqual(conversation["intent"], "conversation")
                self.assertFalse(conversation["taskCreated"])
                self.assertEqual(conversation["taskMissionIds"], [])
                self.assertEqual(conversation["taskStatus"], "not_requested")
                self.assertFalse(conversation["autoExecute"])
                self.assertFalse(self.bridge.MISSIONS_PATH.exists())

                specialist = chat("backtest_analyst", "specialist-task", "specialist")
                replay = chat("backtest_analyst", "specialist-task", "specialist")
                self.assertTrue(specialist["taskCreated"])
                self.assertEqual(specialist["intent"], "task_request")
                self.assertEqual(len(specialist["taskMissionIds"]), 1)
                self.assertEqual(replay["taskMissionIds"], specialist["taskMissionIds"])
                self.assertTrue(replay["usage"]["idempotentReplay"])
                self.assertFalse(replay["consumesCodexQuota"])
                self.assertEqual(
                    [item["message"] for item in calls].count("specialist-task"),
                    1,
                )
                specialist_mission = self.bridge.find_mission(specialist["taskMissionIds"][0])
                self.assertEqual(specialist_mission["owner"], "backtest_analyst")
                self.assertEqual(specialist_mission["targetId"], "left_analytics_console")
                self.assertEqual(specialist_mission["status"], "queued")
                self.assertTrue(specialist_mission["autoEligible"])
                self.assertEqual(specialist_mission["executionMode"], "auto_guarded")
                self.assertTrue(specialist["autoExecute"])

                for executive, message, suffix in (
                    ("manager", "manager-task", "manager"),
                    ("ceo", "ceo-task", "ceo"),
                ):
                    response = chat(executive, message, suffix)
                    self.assertTrue(response["taskCreated"])
                    self.assertGreaterEqual(len(response["taskMissionIds"]), 2)
                    created = [
                        self.bridge.find_mission(mission_id)
                        for mission_id in response["taskMissionIds"]
                    ]
                    parent = next(
                        item
                        for item in created
                        if item.get("reportType") == "mission_plan"
                        and not item.get("parentMissionId")
                    )
                    children = [item for item in created if item.get("parentMissionId") == parent["id"]]
                    self.assertEqual(parent["owner"], "manager")
                    self.assertGreaterEqual(len(children), 1)
                    self.assertTrue(all(item["owner"] != "manager" for item in children))

                risky = chat("backtest_analyst", "high-impact", "high-impact")
                self.assertTrue(risky["taskCreated"])
                self.assertEqual(len(risky["taskMissionIds"]), 1)
                self.assertFalse(risky["autoExecute"])
                self.assertEqual(risky["taskStatus"], "waiting_approval")
                risky_mission = self.bridge.find_mission(risky["taskMissionIds"][0])
                self.assertEqual(risky_mission["risk"], "high")
                self.assertEqual(risky_mission["status"], "waiting_approval")
                self.assertEqual(risky_mission["executionMode"], "manual_guarded")
                self.assertFalse(risky_mission["autoEligible"])
                self.assertTrue(risky_mission["requiresHumanApproval"])
                self.assertIn("human", risky_mission["approval"]["requiredActors"])
                self.assertIn("risk_guard", risky_mission["approval"]["requiredActors"])

                events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=500)
                risky_events = [
                    item
                    for item in events
                    if item.get("missionId") == risky_mission["id"]
                ]
                self.assertFalse(any(item.get("type") == "mission.auto_enqueued" for item in risky_events))
                self.assertFalse(any(item.get("type") == "mission.auto_run_start" for item in risky_events))
                transcripts = [
                    json.loads(line)
                    for line in (runtime / self.bridge.AGENT_CHAT_TRANSCRIPT_FILENAME)
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                specialist_turn = next(
                    item for item in transcripts if item.get("userMessage") == "specialist-task"
                )
                self.assertEqual(specialist_turn["intent"], "task_request")
                self.assertTrue(specialist_turn["taskCreated"])
                self.assertEqual(
                    specialist_turn["taskMissionIds"],
                    specialist["taskMissionIds"],
                )
                self.assertTrue(all(item["treeKill"] for item in calls))
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.OPERATOR_MODE_PATH = original_operator_mode
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.AGENT_EVENTS_PATH = original_agent_events
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RUNNER_SCRIPT = original_runner_script
                self.bridge.codex_rate_limits = original_codex_limits
                self.bridge.peek_codex_rate_limits = original_peek_limits
                self.bridge.check_rate_limit = original_rate_check
                self.bridge.run_safe_command = original_command
                self.bridge.REAL_RUN_SEMAPHORE = original_semaphore
                self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge.AGENT_CHAT_INFLIGHT.clear()
                self.bridge.MISSION_WORKER_WAKE.clear()

    def test_agent_chat_history_keeps_last_eight_full_exchanges_per_agent_session(self) -> None:
        original_runtime = self.bridge.RUNTIME_DIR
        with tempfile.TemporaryDirectory() as directory:
            try:
                self.bridge.RUNTIME_DIR = Path(directory)
                for index in range(10):
                    self.bridge.append_agent_chat_transcript({
                        "turnId": f"turn-{index}",
                        "sessionId": "session-history",
                        "agentId": "backtest_analyst",
                        "agentName": "Backtest Analyst",
                        "idempotencyDigest": f"digest-{index}",
                        "userMessage": f"คำถาม {index}",
                        "assistantReply": f"คำตอบ {index}",
                        "status": "completed",
                        "modelTier": "specialist_balanced",
                        "consumesCodexQuota": True,
                        "quotaConsumptionStatus": "confirmed",
                        "usage": {},
                    })
                history = self.bridge.load_agent_chat_history(
                    "backtest_analyst",
                    "session-history",
                    recent_turns=8,
                    max_chars=12000,
                )
                self.assertEqual(len(history), 16)
                self.assertEqual(history[0], {"role": "user", "content": "คำถาม 2"})
                self.assertEqual(history[-1], {"role": "assistant", "content": "คำตอบ 9"})
                self.assertEqual(
                    self.bridge.load_agent_chat_history("manager", "session-history"),
                    [],
                )
                self.assertLessEqual(sum(len(item["content"]) for item in history), 12000)

                for index in range(3):
                    self.bridge.append_agent_chat_transcript({
                        "turnId": f"long-turn-{index}",
                        "sessionId": "session-long-history",
                        "agentId": "backtest_analyst",
                        "agentName": "Backtest Analyst",
                        "idempotencyDigest": f"long-digest-{index}",
                        "userMessage": f"คำถามยาว {index} " + ("ก" * 3500),
                        "assistantReply": f"คำตอบยาว {index} " + ("ข" * 3500),
                        "status": "completed",
                        "modelTier": "specialist_balanced",
                        "consumesCodexQuota": True,
                        "quotaConsumptionStatus": "confirmed",
                        "usage": {},
                    })
                long_history = self.bridge.load_agent_chat_history(
                    "backtest_analyst",
                    "session-long-history",
                    recent_turns=8,
                    max_chars=12000,
                )
                self.assertEqual(len(long_history), 2)
                self.assertEqual([item["role"] for item in long_history], ["user", "assistant"])
                self.assertTrue(long_history[0]["content"].startswith("คำถามยาว 2"))
                self.assertTrue(long_history[1]["content"].startswith("คำตอบยาว 2"))
                self.assertLessEqual(sum(len(item["content"]) for item in long_history), 12000)
            finally:
                self.bridge.RUNTIME_DIR = original_runtime

    def test_health_check_is_fast_and_side_effect_free(self) -> None:
        health = self.bridge.runtime_health()
        self.assertTrue(health["ok"])
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["agentCount"], 10)
        self.assertEqual(health["expectedAgentCount"], 10)
        self.assertTrue(health["agentRosterComplete"])
        self.assertTrue(all(health["criticalFiles"].values()))
        self.assertTrue(health["assetIntegrity"]["roomImage"])
        self.assertTrue(health["assetIntegrity"]["walkableMask"])
        self.assertTrue(all(health["assetIntegrity"]["agentImages"].values()))
        self.assertTrue(all(health["assetIntegrity"]["propImages"].values()))
        self.assertFalse(health["policy"]["frontendSecrets"])
        self.assertEqual(health["policy"]["realExecution"], "guarded")

    def test_http_server_is_restart_friendly(self) -> None:
        self.assertTrue(self.bridge.BridgeHTTPServer.allow_reuse_address)
        self.assertTrue(self.bridge.BridgeHTTPServer.daemon_threads)

    def test_windows_venv_launcher_does_not_break_bridge_lifecycle_identity(self) -> None:
        lifecycle = LIFECYCLE_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        installer = INSTALLER_SCRIPT_PATH.read_text(encoding="utf-8-sig")

        self.assertIn("sys._base_executable", lifecycle)
        self.assertIn("$candidates = @(Get-BridgeProcesses)", lifecycle)
        self.assertIn("$healthyProcessResult = Wait-ForBridgeHealth", lifecycle)
        self.assertIn("$healthyProcessId = [int]$healthyProcessResult.ProcessId", lifecycle)
        self.assertIn("Write-BridgeEndpoint -Health $healthyProcessResult.Health", lifecycle)
        self.assertIn('Write-LifecycleState -Status "running" -ProcessId $healthyProcessId', lifecycle)
        self.assertIn('$bridgeHost = "127.0.0.1"', lifecycle)
        self.assertIn("Select-RandomAvailableBridgePort", lifecycle)
        self.assertIn("42000 -Maximum 50000", lifecycle)
        self.assertIn("foreign_port_preserved", lifecycle)
        self.assertIn("Get-AllBridgeProcessIdentities", lifecycle)
        self.assertIn("Multiple exact Metafx bridge processes were found", lifecycle)
        self.assertIn("Wait-ForBridgeHealth -ProcessId $startedId", lifecycle)
        self.assertIn("for ($attempt = 1; $attempt -le 3; $attempt++)", lifecycle)
        self.assertIn("persistence_failed_process_stopped", lifecycle)
        self.assertNotIn("MetafxclubAgentHQBridge4186Lifecycle", lifecycle)
        self.assertIn("& $FilePath @Arguments | Out-Host", installer)
        self.assertIn("$nativeExitCode = $LASTEXITCODE", installer)
        self.assertIn("$statusExitCode -notin @(3, 4)", installer)

    def test_student_installer_requires_confirmed_loopback_endpoint_and_checks_codex_quota(self) -> None:
        lifecycle = LIFECYCLE_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        installer = INSTALLER_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        readiness = CODEX_READINESS_SCRIPT_PATH.read_text(encoding="utf-8-sig")

        self.assertIn("[switch]$ListAvailableEndpoints", installer)
        self.assertIn("[switch]$EndpointConfirmed", installer)
        self.assertIn("Get-AvailableBridgeEndpointCandidates -Count 3", installer)
        self.assertIn('host = "127.0.0.1"', installer)
        self.assertIn("ระบบยังไม่ได้ติดตั้งหรือปิดโปรแกรมอื่น", installer)
        self.assertIn("$selectedBridgePort = Confirm-BridgeEndpoint", installer)
        main_start = installer.rindex("\ntry {")
        self.assertLess(
            installer.index("$selectedBridgePort = Confirm-BridgeEndpoint", main_start),
            installer.index("\n    Stop-ExistingBridge", main_start),
        )
        self.assertIn("-Port $ConfirmedPort", installer)
        self.assertIn("api/codex/rate-limits?refresh=true", installer)
        self.assertIn("account_identity_stored = $false", installer)
        self.assertNotIn("& $codex login", installer)

        self.assertIn("$confirmedEndpointRequired", lifecycle)
        self.assertIn("ระบบหยุดโดยไม่เปลี่ยนไปใช้ URL อื่น", lifecycle)
        self.assertIn("user_confirmed", lifecycle)
        self.assertIn("api/codex/rate-limits", readiness)
        self.assertIn("127.0.0.1", readiness)
        self.assertNotIn("auth.json", readiness.lower())

    def test_release_version_and_asset_registry_are_portable(self) -> None:
        version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()
        registry_path = (
            PROJECT_ROOT
            / "frontend"
            / "public"
            / "assets"
            / "agents"
            / "male-roster-set-a-core-command-operators-v001"
            / "registry"
            / "asset-registry.json"
        )
        registry_text = registry_path.read_text(encoding="utf-8-sig")
        self.assertEqual(version, "0.9.0")
        self.assertNotRegex(registry_text, r"(?i)[a-z]:\\\\users\\\\")

    def test_durable_json_write_keeps_last_valid_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missions.json"
            self.bridge.write_json(path, {"missions": [{"id": "first"}]}, keep_backup=True)
            self.bridge.write_json(path, {"missions": [{"id": "second"}]}, keep_backup=True)
            backup = path.with_name("missions.json.bak")
            self.assertTrue(backup.is_file())
            self.assertEqual(json.loads(backup.read_text(encoding="utf-8"))["missions"][0]["id"], "first")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["missions"][0]["id"], "second")

    def test_corrupt_json_fails_closed_instead_of_returning_empty_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missions.json"
            path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge.read_json(path, {"missions": []})
            with self.assertRaises(self.bridge.DataIntegrityError):
                self.bridge.write_json(path, {"missions": []}, keep_backup=True)
            self.assertEqual(path.read_text(encoding="utf-8"), "{not valid json")

    def test_append_only_log_rotation_archives_without_deleting_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original_runtime = self.bridge.RUNTIME_DIR
            try:
                self.bridge.RUNTIME_DIR = Path(directory) / "runtime"
                path = self.bridge.RUNTIME_DIR / "agent-events.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                original = '{"kind":"historic","detail":"preserve me"}\n'
                path.write_text(original, encoding="utf-8")
                archived = self.bridge.rotate_jsonl_segment(path, max_bytes=1)
                self.assertIsNotNone(archived)
                self.assertFalse(path.exists())
                self.assertEqual(archived.read_text(encoding="utf-8"), original)
                self.assertTrue(str(archived).startswith(str(self.bridge.RUNTIME_DIR / "archive")))
            finally:
                self.bridge.RUNTIME_DIR = original_runtime

    def test_codex_raw_output_is_sanitized_before_project_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_directory = Path(directory) / "codex-runs"
            raw_output_paths = []
            original_runs_dir = self.runner.CODEX_RUNS_DIR
            original_status = self.runner.status
            original_run_chat_command = self.runner.run_chat_command

            def fake_run_chat_command(command, timeout, stdin, cwd, output_limit=60000):
                raw_path = Path(command[command.index("-o") + 1])
                raw_output_paths.append(raw_path)
                self.assertNotEqual(raw_path.parent.resolve(), run_directory.resolve())
                raw_path.write_text("token=supersecretvalue\nSafe report body", encoding="utf-8")
                return {
                    "ok": True,
                    "exitCode": 0,
                    "stdout": "token=supersecretvalue",
                    "stderr": "",
                    "durationMs": 1,
                    "processStarted": True,
                    "processTreeTerminated": False,
                }

            try:
                self.runner.CODEX_RUNS_DIR = run_directory
                self.runner.status = lambda: {"status": "ready"}
                self.runner.run_chat_command = fake_run_chat_command
                result = self.runner.run_codex("Review this report", "manager", "mission-test")
            finally:
                self.runner.CODEX_RUNS_DIR = original_runs_dir
                self.runner.status = original_status
                self.runner.run_chat_command = original_run_chat_command

            self.assertTrue(result["ok"])
            self.assertTrue(result["usage"]["secretRedacted"])
            for path in run_directory.glob("*"):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("supersecretvalue", content)
            self.assertTrue(raw_output_paths)
            self.assertFalse(raw_output_paths[0].exists())

    def test_codex_rate_limit_runner_drops_account_and_secret_fields(self) -> None:
        payload = self.runner.sanitize_rate_limits_response({
            "rateLimits": {"primary": {"usedPercent": 8, "windowDurationMins": 60, "resetsAt": 1780000000}},
            "rateLimitsByLimitId": {
                "codex": {
                    "planType": "private-plan",
                    "credits": {"balance": "private-credit"},
                    "account": {"email": "private@example.test", "token": "secret-token-value"},
                    "primary": {"usedPercent": 123, "windowDurationMins": 10080, "resetsAt": 1784531255},
                    "secondary": {"usedPercent": -5, "windowDurationMins": 300, "resetsAt": 1784530000},
                    "rateLimitReachedType": None,
                },
            },
            "codexHome": "C:/private/path",
        })
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["primary"]["usedPercent"], 100)
        self.assertEqual(payload["primary"]["remainingPercent"], 0)
        self.assertEqual(payload["secondary"]["usedPercent"], 0)
        serialized = json.dumps(payload).lower()
        for forbidden in ("plan", "credit", "balance", "email", "token", "codexhome", "private"):
            self.assertNotIn(forbidden, serialized)

    def test_bridge_rate_limit_cache_stale_fallback_and_auth_invalidation(self) -> None:
        good = {
            "ok": True,
            "status": "ready",
            "source": "codex_app_server",
            "meter": {"id": "codex", "name": "Codex", "planType": "must-drop"},
            "primary": {
                "usedPercent": 37,
                "remainingPercent": 999,
                "windowDurationMinutes": 10080,
                "resetsAt": "2026-07-20T07:07:35Z",
                "token": "must-drop",
            },
            "secondary": None,
            "limitReached": False,
            "checkedAt": "2026-07-14T16:00:00Z",
            "credits": {"balance": "must-drop"},
        }
        calls = []
        responses = [good, {"ok": False, "status": "timeout"}, {"ok": False, "status": "auth_required"}]
        original_command = self.bridge.run_safe_command
        original_audit = self.bridge.AUDIT_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_cache = dict(self.bridge.CODEX_RATE_LIMIT_CACHE)

        def fake_command(command, timeout=8, output_limit=1200, input_text=None):
            calls.append(command)
            payload = responses.pop(0)
            return {"ok": True, "exitCode": 0, "output": json.dumps(payload), "durationMs": 1}

        with tempfile.TemporaryDirectory() as directory:
            try:
                self.bridge.run_safe_command = fake_command
                self.bridge.AUDIT_PATH = Path(directory) / "bridge-audit.jsonl"
                # The clean repository intentionally excludes runner/.venv.
                # Point the mocked runner gate at an existing local file so
                # this unit test remains independent from installation state.
                self.bridge.CODEX_RUNNER_PYTHON = Path(__file__)
                self.bridge.CODEX_RATE_LIMIT_CACHE.update({"payload": None, "fetchedMonotonic": 0.0, "invalidated": False})

                fresh = self.bridge.codex_rate_limits(force=True)
                audit_after_refresh = self.bridge.AUDIT_PATH.read_text(encoding="utf-8").count("\n")
                cached = self.bridge.codex_rate_limits()
                self.assertEqual(len(calls), 1)
                self.assertEqual(self.bridge.AUDIT_PATH.read_text(encoding="utf-8").count("\n"), audit_after_refresh)
                self.assertEqual(fresh["primary"]["remainingPercent"], 63)
                self.assertTrue(cached["cacheHit"])
                serialized = json.dumps(fresh).lower()
                for forbidden in ("plantype", "credits", "balance", "token", "must-drop"):
                    self.assertNotIn(forbidden, serialized)

                self.bridge.CODEX_RATE_LIMIT_CACHE["fetchedMonotonic"] = time.monotonic() - 80
                stale = self.bridge.codex_rate_limits()
                self.assertTrue(stale["stale"])
                self.assertEqual(len(calls), 2)

                auth = self.bridge.codex_rate_limits(force=True)
                self.assertFalse(auth["ok"])
                self.assertEqual(auth["status"], "auth_required")
                self.assertIsNone(self.bridge.CODEX_RATE_LIMIT_CACHE["payload"])
                self.assertEqual(len(calls), 3)

                audit_text = self.bridge.AUDIT_PATH.read_text(encoding="utf-8").lower()
                self.assertIn("system-codex-rate-monitor", audit_text)
                self.assertIn("codex_mcp_operator", audit_text)
                self.assertNotIn("must-drop", audit_text)
            finally:
                self.bridge.run_safe_command = original_command
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RATE_LIMIT_CACHE.clear()
                self.bridge.CODEX_RATE_LIMIT_CACHE.update(original_cache)

    def test_concurrent_codex_rate_limit_reads_use_one_runner_refresh(self) -> None:
        good = {
            "ok": True,
            "status": "ready",
            "primary": {
                "usedPercent": 42,
                "windowDurationMinutes": 10080,
                "resetsAt": "2026-07-20T07:07:35Z",
            },
            "secondary": None,
            "checkedAt": "2026-07-14T16:00:00Z",
        }
        call_count = 0
        count_lock = threading.Lock()
        original_command = self.bridge.run_safe_command
        original_audit = self.bridge.AUDIT_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_cache = dict(self.bridge.CODEX_RATE_LIMIT_CACHE)

        def fake_command(command, timeout=8, output_limit=1200, input_text=None):
            nonlocal call_count
            with count_lock:
                call_count += 1
            time.sleep(0.05)
            return {"ok": True, "exitCode": 0, "output": json.dumps(good), "durationMs": 50}

        with tempfile.TemporaryDirectory() as directory:
            try:
                self.bridge.run_safe_command = fake_command
                self.bridge.AUDIT_PATH = Path(directory) / "bridge-audit.jsonl"
                self.bridge.CODEX_RUNNER_PYTHON = Path(__file__)
                self.bridge.CODEX_RATE_LIMIT_CACHE.update({"payload": None, "fetchedMonotonic": 0.0, "invalidated": False})
                with ThreadPoolExecutor(max_workers=10) as pool:
                    results = list(pool.map(lambda _: self.bridge.codex_rate_limits(), range(10)))
                self.assertEqual(call_count, 1)
                self.assertTrue(all(item["ok"] for item in results))
                self.assertEqual({item["primary"]["remainingPercent"] for item in results}, {58})
            finally:
                self.bridge.run_safe_command = original_command
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RATE_LIMIT_CACHE.clear()
                self.bridge.CODEX_RATE_LIMIT_CACHE.update(original_cache)

    def test_manager_delegation_creates_auto_guarded_backend_approved_specialist_missions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_operator_mode = self.bridge.OPERATOR_MODE_PATH
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.RATE_LIMIT_STATE.clear()
                self.assertTrue(self.bridge.set_operator_mode({"mode": "auto_guarded"})["ok"])
                result = self.bridge.manager_delegate({
                    "agentId": "manager",
                    "goal": "Analyze this backtest drawdown and optimize the parameter range",
                    "idempotencyKey": "delegation-regression-test",
                })
                self.assertTrue(result["ok"])
                self.assertEqual(result["parent"]["status"], "queued")
                self.assertGreaterEqual(len(result["subtasks"]), 2)
                for subtask in result["subtasks"]:
                    self.assertEqual(subtask["toolId"], "codex_cli_task")
                    self.assertEqual(subtask["status"], "queued")
                    self.assertEqual(subtask["executionMode"], "auto_guarded")
                    self.assertTrue(subtask["autoEligible"])
                    self.assertFalse(subtask["requiresHumanApproval"])
                    self.assertTrue(subtask["approval"]["required"])
                    self.assertEqual(subtask["approval"]["state"], "approved")
                    self.assertEqual(subtask["approval"]["gateMode"], "backend_auto_review")
                    self.assertEqual(subtask["approval"]["requiredActors"], ["risk_guard"])
                    self.assertTrue(subtask["approval"]["payloadDigest"])

                for subtask in result["subtasks"]:
                    subtask["status"] = "completed"
                    subtask["result"] = f"Structured result from {subtask['owner']}"
                    subtask["completedAt"] = self.bridge.utc_now()
                    self.bridge.replace_mission(subtask)
                refreshed = self.bridge.refresh_parent_mission(result["parent"]["id"])
                self.assertEqual(refreshed["status"], "completed")
                self.assertEqual(refreshed["phase"], "synthesized")
                self.assertTrue(refreshed["delegation"]["finalReportId"])
            finally:
                self.bridge.OPERATOR_MODE_PATH = original_operator_mode
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge.MISSION_WORKER_WAKE.clear()

    def test_approval_digest_binds_every_execution_relevant_field(self) -> None:
        mission = {
            "owner": "backtest_analyst",
            "toolId": "codex_cli_task",
            "targetId": "left_analytics_console",
            "detail": "Analyze this bounded report",
            "modelTier": "specialist_balanced",
            "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000, "maxRuns": 1},
            "risk": "medium",
            "reportType": "backtest_report",
        }
        digest = self.bridge.mission_payload_digest(mission)
        for field, changed in {
            "owner": "manager",
            "toolId": "mcp_tool_run",
            "targetId": "codex_mcp_portal",
            "detail": "Changed detail",
            "modelTier": "manager_quality",
            "budget": {"timeoutSeconds": 121, "outputLimitChars": 7000, "maxRuns": 1},
            "risk": "high",
            "reportType": "risk_review",
        }.items():
            with self.subTest(field=field):
                changed_mission = {**mission, field: changed}
                self.assertNotEqual(self.bridge.mission_payload_digest(changed_mission), digest)
        reordered_budget = {
            **mission,
            "budget": {"maxRuns": 1, "outputLimitChars": 7000, "timeoutSeconds": 120},
        }
        self.assertEqual(self.bridge.mission_payload_digest(reordered_budget), digest)

    def test_manager_idempotent_replay_does_not_consume_rate_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.RATE_LIMIT_STATE.clear()
                payload = {
                    "agentId": "manager",
                    "goal": "Analyze this backtest report",
                    "idempotencyKey": "replay-before-rate-limit",
                }
                first = self.bridge.manager_delegate(payload)
                rate_rows_after_first = list(self.bridge.RATE_LIMIT_STATE.get("delegate:manager", []))
                replay = self.bridge.manager_delegate(payload)
                self.assertTrue(first["ok"])
                self.assertTrue(replay["ok"])
                self.assertTrue(replay["idempotentReplay"])
                self.assertEqual(self.bridge.RATE_LIMIT_STATE.get("delegate:manager", []), rate_rows_after_first)
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.RATE_LIMIT_STATE.clear()

    def test_archived_child_preserves_outcome_and_parent_report_is_updated_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                parent = {"id": "parent-archive", "title": "Parent", "status": "running", "owner": "manager", "reportIds": [], "delegation": {}}
                children = [
                    {"id": "child-success", "parentMissionId": parent["id"], "owner": "backtest_analyst", "status": "completed", "result": "ok"},
                    {"id": "child-later-fails", "parentMissionId": parent["id"], "owner": "optimization_agent", "status": "completed", "result": "ok"},
                ]
                self.bridge.save_missions([parent, *children])
                completed = self.bridge.refresh_parent_mission(parent["id"])
                report_id = completed["delegation"]["finalReportId"]
                self.assertEqual(completed["status"], "completed")

                archived_success = self.bridge.archive_mission("child-success")
                self.assertEqual(archived_success["mission"]["archivedFromStatus"], "completed")
                self.assertTrue(archived_success["mission"]["archivedSuccessful"])
                after_success_archive = self.bridge.find_mission(parent["id"])
                self.assertEqual(after_success_archive["status"], "completed")
                self.assertEqual(after_success_archive["delegation"]["finalReportId"], report_id)

                failed_child = self.bridge.find_mission("child-later-fails")
                failed_child["status"] = "failed"
                failed_child["result"] = "failed safely"
                self.bridge.replace_mission(failed_child)
                archived_failure = self.bridge.archive_mission("child-later-fails")
                self.assertFalse(archived_failure["mission"]["archivedSuccessful"])
                blocked_parent = self.bridge.find_mission(parent["id"])
                self.assertEqual(blocked_parent["status"], "blocked")
                self.assertEqual(blocked_parent["delegation"]["finalReportId"], report_id)
                final_report = json.loads((self.bridge.RUNTIME_REPORTS_DIR / f"{report_id}.json").read_text(encoding="utf-8"))
                self.assertEqual(final_report["status"], "blocked")
                self.assertEqual(final_report["metrics"]["outcomes"]["notSucceeded"], 1)
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit

    def test_backend_risk_guard_rejects_disabled_high_risk_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                mission = self.bridge.create_mission({
                    "title": "Telegram external send",
                    "prompt": "send telegram summary",
                    "agentId": "telegram_ops",
                    "toolId": "send_telegram",
                    "targetId": "right_tool_console",
                    "risk": "low",
                    "reportType": "telegram_tool_report",
                })
                self.assertEqual(mission["risk"], "high")
                self.assertEqual(set(mission["approval"]["requiredActors"]), {"human", "risk_guard"})
                result = self.bridge.approve_mission(mission["id"], {
                    "actorId": "human",
                    "decision": "approved",
                    "confirmMissionId": mission["id"],
                    "note": "I explicitly approve this exact bounded mission packet.",
                })
                reviewed = self.bridge.find_mission(mission["id"])
                self.assertTrue(result["ok"])
                self.assertEqual(reviewed["status"], "blocked")
                self.assertEqual(reviewed["approval"]["state"], "rejected")
                risk_decision = next(item for item in reviewed["approval"]["decisions"] if item["actorId"] == "risk_guard")
                self.assertEqual(risk_decision["decision"], "rejected")
                self.assertEqual(risk_decision["actorProvenance"], "backend_deterministic_policy")
                self.assertEqual(risk_decision["payloadDigest"], reviewed["approval"]["payloadDigest"])
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertTrue(any(item.get("type") == "mission.risk_guard_review" for item in audit))
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit

    def test_capability_registry_is_contract_owned_sanitized_and_prop_filtered(self) -> None:
        fake_status = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready", "version": "codex-cli 1", "runner": "project_sdk"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-15T00:00:00+00:00",
        }
        registry = self.bridge.capability_registry(fake_status)
        self.assertEqual(registry["contractVersion"], "tool-permission-contract-v007")
        self.assertFalse(registry["policy"]["frontendSecrets"])
        self.assertTrue(registry["policy"]["disabledToolsFailClosed"])
        telegram = next(item for item in registry["capabilities"] if item["id"] == "send_telegram")
        self.assertFalse(telegram["realExecutionAvailable"])
        self.assertFalse(telegram["autoRunnable"])
        serialized = json.dumps(registry).lower()
        for forbidden in ("api_key", "authorization", "cookie", "password"):
            self.assertNotIn(forbidden, serialized)

        originals = {
            "bridge_status": self.bridge.bridge_status,
            "load_missions": self.bridge.load_missions,
            "load_agent_events": self.bridge.load_agent_events,
            "load_runtime_reports": self.bridge.load_runtime_reports,
            "load_meeting_records": self.bridge.load_meeting_records,
            "search_memory_items": self.bridge.search_memory_items,
        }
        try:
            self.bridge.bridge_status = lambda: fake_status
            self.bridge.load_missions = lambda: []
            self.bridge.load_agent_events = lambda limit=120: []
            self.bridge.load_runtime_reports = lambda limit=120: []
            self.bridge.load_meeting_records = lambda limit=120: [{"id": "meeting-1", "linkedPropId": "codex_mcp_portal", "participants": ["codex_mcp_operator"]}]
            self.bridge.search_memory_items = lambda query="", limit=12: []
            prop = self.bridge.prop_report("codex_mcp_portal")
            self.assertEqual(prop["bridge"]["runtimeVersion"], self.bridge.BRIDGE_RUNTIME_VERSION)
            self.assertTrue(prop["meetings"])
            self.assertTrue(prop["capabilities"])
            self.assertTrue(all("codex_mcp_portal" in item["linkedPropIds"] for item in prop["capabilities"]))
        finally:
            for name, value in originals.items():
                setattr(self.bridge, name, value)

        source = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn('if path == "/api/capabilities":', source)

    def test_frontend_read_model_exposes_only_server_derived_execute_readiness(self) -> None:
        mission = {
            "id": "mission-ready",
            "title": "Approved read-only analysis",
            "status": "waiting_approval",
            "approval": {
                "required": True,
                "state": "approved",
                "payloadDigest": "must-not-leak",
            },
        }
        read_model = self.bridge.mission_read_model_item(mission)
        self.assertTrue(read_model["readyToExecute"])
        self.assertNotIn("payloadDigest", read_model["approval"])
        mission["approval"]["state"] = "pending"
        self.assertFalse(self.bridge.mission_read_model_item(mission)["readyToExecute"])

    def test_execute_requires_exact_mission_confirmation_before_lookup(self) -> None:
        result = self.bridge.execute_mission("mission-confirm", {})
        self.assertFalse(result["ok"])
        self.assertEqual(result["kind"], "mission_confirmation_required")
        self.assertEqual(result["_httpStatus"], 422)

    def test_runner_busy_does_not_consume_hourly_rate_counter(self) -> None:
        class BusySemaphore:
            def acquire(self, blocking=False):
                return False

            def release(self):
                raise AssertionError("A semaphore that was not acquired must not be released")

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            original_bridge_status = self.bridge.bridge_status
            original_quota = self.bridge.codex_rate_limits
            original_semaphore = self.bridge.REAL_RUN_SEMAPHORE
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.bridge_status = lambda: {"codex": {"status": "ready"}}
                self.bridge.codex_rate_limits = lambda force=False: {"ok": False, "status": "unavailable", "stale": False}
                self.bridge.REAL_RUN_SEMAPHORE = BusySemaphore()
                self.bridge.RATE_LIMIT_STATE.clear()
                mission = {
                    "id": "mission-runner-busy",
                    "title": "Bounded analysis",
                    "detail": "Analyze a local report only",
                    "owner": "backtest_analyst",
                    "requester": "human",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "status": "waiting_approval",
                    "risk": "medium",
                    "modelTier": "specialist_balanced",
                    "reportType": "backtest_report",
                    "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000, "maxRuns": 1},
                }
                mission["approval"] = {"required": True, "state": "approved", "payloadDigest": self.bridge.mission_payload_digest(mission)}
                self.bridge.save_missions([mission])
                result = self.bridge.execute_mission(mission["id"], {"confirmMissionId": mission["id"]})
                self.assertEqual(result["kind"], "runner_busy")
                self.assertEqual(self.bridge.RATE_LIMIT_STATE, {})
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.bridge_status = original_bridge_status
                self.bridge.codex_rate_limits = original_quota
                self.bridge.REAL_RUN_SEMAPHORE = original_semaphore
                self.bridge.RATE_LIMIT_STATE.clear()

    def test_official_codex_limit_reached_blocks_before_runner_without_guessing_unavailable(self) -> None:
        class UntouchedSemaphore:
            def acquire(self, blocking=False):
                raise AssertionError("Runner semaphore must not be touched after an official limit block")

            def release(self):
                raise AssertionError("Runner semaphore must not be touched after an official limit block")

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            original_bridge_status = self.bridge.bridge_status
            original_quota = self.bridge.codex_rate_limits
            original_semaphore = self.bridge.REAL_RUN_SEMAPHORE
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.bridge_status = lambda: {"codex": {"status": "ready"}}
                self.bridge.codex_rate_limits = lambda force=False: {"ok": True, "status": "ready", "limitReached": True, "stale": False}
                self.bridge.REAL_RUN_SEMAPHORE = UntouchedSemaphore()
                self.bridge.RATE_LIMIT_STATE.clear()
                mission = {
                    "id": "mission-official-limit",
                    "title": "Bounded analysis",
                    "detail": "Analyze a local report only",
                    "owner": "backtest_analyst",
                    "requester": "human",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "status": "waiting_approval",
                    "risk": "medium",
                    "modelTier": "specialist_balanced",
                    "reportType": "backtest_report",
                    "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000, "maxRuns": 1},
                }
                mission["approval"] = {"required": True, "state": "approved", "payloadDigest": self.bridge.mission_payload_digest(mission)}
                self.bridge.save_missions([mission])
                result = self.bridge.execute_mission(mission["id"], {"confirmMissionId": mission["id"]})
                self.assertEqual(result["kind"], "codex_limit_reached")
                self.assertEqual(self.bridge.RATE_LIMIT_STATE, {})
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertTrue(any(item.get("type") == "guard.codex_limit_reached" for item in audit))
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.bridge_status = original_bridge_status
                self.bridge.codex_rate_limits = original_quota
                self.bridge.REAL_RUN_SEMAPHORE = original_semaphore
                self.bridge.RATE_LIMIT_STATE.clear()

    def test_interrupted_consumed_run_is_failed_closed_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            original_runtime = self.bridge.RUNTIME_DIR
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                mission = {
                    "id": "mission-interrupted",
                    "title": "Interrupted task",
                    "owner": "backtest_analyst",
                    "toolId": "codex_cli_task",
                    "status": "running",
                    "approval": {"required": True, "state": "consumed"},
                    "attemptCount": 1,
                }
                self.bridge.save_missions([mission])
                recovered = self.bridge.recover_interrupted_missions()
                stored = self.bridge.find_mission("mission-interrupted")
                self.assertEqual(recovered, 1)
                self.assertEqual(stored["status"], "failed")
                self.assertEqual(stored["phase"], "interrupted")
                self.assertEqual(stored["errorCode"], "bridge_restart_interrupted")
                self.assertEqual(stored["approval"]["state"], "consumed")
                self.assertIn("no automatic retry", stored["result"])
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertEqual(audit[-1]["type"], "mission.interrupted_recovered")
                self.assertFalse(audit[-1]["automaticRetry"])
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit

    def test_startup_reconciles_expired_and_legacy_waiting_approval_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.save_missions([
                    {
                        "id": "mission-expired-startup",
                        "owner": "backtest_analyst",
                        "toolId": "codex_cli_task",
                        "status": "waiting_approval",
                        "approval": {
                            "required": True,
                            "state": "pending",
                            "expiresAt": "2000-01-01T00:00:00+00:00",
                        },
                    },
                    {
                        "id": "mission-legacy-waiting",
                        "owner": "manager",
                        "toolId": "manager_mission",
                        "status": "waiting_approval",
                        "approval": {"required": False, "state": "not_required"},
                    },
                ])
                count = self.bridge.reconcile_stale_approval_missions()
                self.assertEqual(count, 2)
                expired = self.bridge.find_mission("mission-expired-startup")
                legacy = self.bridge.find_mission("mission-legacy-waiting")
                self.assertEqual(expired["status"], "blocked")
                self.assertEqual(expired["approval"]["state"], "expired")
                self.assertEqual(legacy["status"], "blocked")
                self.assertEqual(legacy["errorCode"], "legacy_waiting_without_required_approval")
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                self.assertEqual(sum(item.get("type") == "mission.approval_reconciled" for item in audit), 2)
                self.assertTrue(all(item.get("realToolExecuted") is False for item in audit))
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit

    def test_operator_mode_defaults_manual_persists_strict_mode_only_and_audits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_operator_mode = self.bridge.OPERATOR_MODE_PATH
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.MISSION_WORKER_WAKE.clear()

                default_mode = self.bridge.operator_mode_read_model()
                self.assertEqual(default_mode["mode"], "manual_guarded")
                self.assertFalse(default_mode["autoExecute"])
                self.assertIn("autoEligibleTools", default_mode["guardrails"])
                self.assertIn("maxRisk", default_mode["guardrails"])
                self.assertIn("alwaysRequireHumanApprovalFor", default_mode["guardrails"])

                invalid_field = self.bridge.set_operator_mode({
                    "mode": "auto_guarded",
                    "autoExecute": False,
                })
                invalid_value = self.bridge.set_operator_mode({"mode": "unguarded"})
                self.assertFalse(invalid_field["ok"])
                self.assertEqual(invalid_field["kind"], "invalid_operator_mode_request")
                self.assertFalse(invalid_value["ok"])
                self.assertEqual(invalid_value["kind"], "invalid_operator_mode")
                self.assertFalse(self.bridge.OPERATOR_MODE_PATH.exists())

                enabled = self.bridge.set_operator_mode({"mode": "auto_guarded"})
                self.assertTrue(enabled["ok"])
                self.assertEqual(enabled["mode"], "auto_guarded")
                self.assertTrue(enabled["autoExecute"])
                self.assertTrue(self.bridge.MISSION_WORKER_WAKE.is_set())
                persisted = json.loads(self.bridge.OPERATOR_MODE_PATH.read_text(encoding="utf-8"))
                self.assertEqual(persisted["mode"], "auto_guarded")
                self.assertEqual(self.bridge.load_operator_mode_record()["source"], "runtime_store")

                events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                changes = [item for item in events if item.get("type") == "operator_mode.changed"]
                self.assertEqual(len(changes), 1)
                self.assertEqual(changes[0]["previousMode"], "manual_guarded")
                self.assertEqual(changes[0]["mode"], "auto_guarded")
                self.assertTrue(changes[0]["autoExecute"])
            finally:
                self.bridge.OPERATOR_MODE_PATH = original_operator_mode
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.MISSION_WORKER_WAKE.clear()

    def test_auto_guarded_safe_codex_keeps_backend_gate_and_hard_risk_cannot_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_operator_mode = self.bridge.OPERATOR_MODE_PATH
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                enabled = self.bridge.set_operator_mode({"mode": "auto_guarded"})
                self.assertTrue(enabled["ok"])

                safe = self.bridge.create_mission({
                    "title": "Analyze bounded local backtest report",
                    "prompt": "Analyze drawdown and profit factor from the local report",
                    "agentId": "backtest_analyst",
                    "requester": "manager",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "risk": "medium",
                    "reportType": "backtest_report",
                    "idempotencyKey": "auto-safe-codex-gate",
                    # These execution fields are deliberately untrusted. The
                    # backend must derive them from operator policy.
                    "executionMode": "manual_guarded",
                    "autoEligible": False,
                    "requiresHumanApproval": True,
                })
                self.assertEqual(safe["status"], "queued")
                self.assertEqual(safe["executionMode"], "auto_guarded")
                self.assertTrue(safe["autoEligible"])
                self.assertFalse(safe["requiresHumanApproval"])
                self.assertTrue(safe["approval"]["required"])
                self.assertEqual(safe["approval"]["gateMode"], "backend_auto_review")
                self.assertEqual(safe["approval"]["state"], "approved")
                self.assertEqual(safe["approval"]["requiredActors"], ["risk_guard"])
                self.assertTrue(safe["approval"]["payloadDigest"])
                self.assertTrue(any(
                    item.get("actorId") == "risk_guard"
                    and item.get("actorProvenance") == "backend_auto_review"
                    and item.get("decision") == "approved"
                    and item.get("payloadDigest") == safe["approval"]["payloadDigest"]
                    for item in safe["approval"]["decisions"]
                ))

                hard_risk = self.bridge.create_mission({
                    "title": "Send live Telegram signal",
                    "prompt": "Send Telegram alert externally and place a live trading order",
                    "agentId": "telegram_ops",
                    "requester": "human",
                    "toolId": "send_telegram",
                    "targetId": "right_tool_console",
                    "risk": "low",
                    "reportType": "telegram_tool_report",
                    "idempotencyKey": "hard-risk-bypass-attempt",
                    "executionMode": "auto_guarded",
                    "autoEligible": True,
                    "requiresHumanApproval": False,
                    "approval": {"required": False, "state": "approved"},
                })
                self.assertEqual(hard_risk["risk"], "high")
                self.assertEqual(hard_risk["status"], "waiting_approval")
                self.assertEqual(hard_risk["executionMode"], "manual_guarded")
                self.assertFalse(hard_risk["autoEligible"])
                self.assertTrue(hard_risk["requiresHumanApproval"])
                self.assertTrue(hard_risk["approval"]["required"])
                self.assertIn("human", hard_risk["approval"]["requiredActors"])
                self.assertNotIn("execution", hard_risk)

                events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=100)
                safe_events = [item for item in events if item.get("missionId") == safe["id"]]
                hard_events = [item for item in events if item.get("missionId") == hard_risk["id"]]
                self.assertTrue(any(item.get("type") == "mission.auto_guard_review" for item in safe_events))
                self.assertTrue(any(item.get("type") == "mission.auto_enqueued" for item in safe_events))
                self.assertFalse(any(item.get("type") == "mission.auto_enqueued" for item in hard_events))
                self.assertFalse(any(item.get("type") == "bridge.codex_run_start" for item in hard_events))
            finally:
                self.bridge.OPERATOR_MODE_PATH = original_operator_mode
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.MISSION_WORKER_WAKE.clear()

    def test_auto_guarded_worker_executes_safe_codex_once_reports_and_completes_parent(self) -> None:
        original_operator_mode = self.bridge.OPERATOR_MODE_PATH
        original_missions = self.bridge.MISSIONS_PATH
        original_reports = self.bridge.RUNTIME_REPORTS_DIR
        original_audit = self.bridge.AUDIT_PATH
        original_runner_python = self.bridge.CODEX_RUNNER_PYTHON
        original_runner_script = self.bridge.CODEX_RUNNER_SCRIPT
        original_bridge_status = self.bridge.bridge_status
        original_codex_limits = self.bridge.codex_rate_limits
        original_rate_check = self.bridge.check_rate_limit
        original_command = self.bridge.run_safe_command
        original_semaphore = self.bridge.REAL_RUN_SEMAPHORE
        runner_calls = []

        def fake_command(
            command,
            timeout=8,
            output_limit=1200,
            input_text=None,
            *,
            kill_process_tree_on_timeout=False,
            cancel_event=None,
        ):
            runner_calls.append({
                "command": list(command),
                "timeout": timeout,
                "input": input_text,
                "treeKill": kill_process_tree_on_timeout,
                "cancelEvent": cancel_event,
            })
            result = {
                "ok": True,
                "status": "completed",
                "message": "Guarded worker completed",
                "finalMessage": "Structured backtest report from the mocked worker",
                "durationMs": 7,
                "artifacts": {},
                "usage": {"outputChars": 50},
            }
            return {
                "ok": True,
                "exitCode": 0,
                "output": json.dumps(result),
                "durationMs": 7,
                "processStarted": True,
                "processTreeTerminated": True,
            }

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            try:
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.CODEX_RUNNER_PYTHON = Path(__file__)
                self.bridge.CODEX_RUNNER_SCRIPT = Path(__file__)
                self.bridge.bridge_status = lambda: {"codex": {"status": "ready"}}
                self.bridge.codex_rate_limits = lambda force=False: {
                    "ok": True,
                    "status": "ready",
                    "limitReached": False,
                    "stale": False,
                }
                self.bridge.check_rate_limit = lambda *args, **kwargs: (True, 0)
                self.bridge.run_safe_command = fake_command
                self.bridge.REAL_RUN_SEMAPHORE = threading.BoundedSemaphore(value=1)
                self.bridge.RATE_LIMIT_STATE.clear()
                self.assertTrue(self.bridge.set_operator_mode({"mode": "auto_guarded"})["ok"])

                delegated = self.bridge.manager_delegate({
                    "agentId": "manager",
                    "goal": "Analyze this bounded local backtest report",
                    "idempotencyKey": "auto-worker-parent",
                    "requestedOwnerAgentId": "backtest_analyst",
                    "requestedTargetId": "left_analytics_console",
                })
                self.assertTrue(delegated["ok"])
                self.assertEqual(len(delegated["subtasks"]), 1)
                child = delegated["subtasks"][0]
                self.assertEqual(child["status"], "queued")
                self.assertIsNone(self.bridge.auto_execution_authorization_error(child))

                self.bridge.process_auto_mission("worker-test", child)
                # A stale duplicate dispatch must not consume the single-use
                # backend approval or start Codex a second time.
                self.bridge.process_auto_mission("worker-test", child)

                self.assertEqual(len(runner_calls), 1)
                self.assertTrue(runner_calls[0]["treeKill"])
                self.assertIn("--execution-mode", runner_calls[0]["command"])
                mode_index = runner_calls[0]["command"].index("--execution-mode")
                self.assertEqual(runner_calls[0]["command"][mode_index + 1], "auto_guarded")

                finished = self.bridge.find_mission(child["id"])
                parent = self.bridge.find_mission(delegated["parent"]["id"])
                self.assertEqual(finished["status"], "completed")
                self.assertEqual(finished["phase"], "auto_guarded_completed")
                self.assertEqual(finished["attemptCount"], 1)
                self.assertEqual(finished["approval"]["state"], "consumed")
                self.assertEqual(finished["execution"]["dispatchState"], "completed")
                self.assertFalse(finished["execution"]["automaticRetry"])
                self.assertEqual(len(finished["reportIds"]), 1)
                report_path = self.bridge.RUNTIME_REPORTS_DIR / f"{finished['reportIds'][0]}.json"
                self.assertTrue(report_path.is_file())
                report = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertEqual(report["linkedMissionId"], child["id"])
                self.assertEqual(report["linkedPropId"], "left_analytics_console")
                self.assertEqual(parent["status"], "completed")
                self.assertEqual(parent["phase"], "synthesized")
                self.assertTrue(parent["delegation"]["finalReportId"])

                events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=200)
                child_events = [item for item in events if item.get("missionId") == child["id"]]
                for event_type in (
                    "mission.auto_guard_review",
                    "mission.auto_enqueued",
                    "mission.auto_claimed",
                    "mission.auto_run_start",
                    "mission.auto_run_end",
                ):
                    self.assertEqual(
                        sum(item.get("type") == event_type for item in child_events),
                        1,
                        f"{event_type} must be emitted exactly once",
                    )
            finally:
                self.bridge.OPERATOR_MODE_PATH = original_operator_mode
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.CODEX_RUNNER_PYTHON = original_runner_python
                self.bridge.CODEX_RUNNER_SCRIPT = original_runner_script
                self.bridge.bridge_status = original_bridge_status
                self.bridge.codex_rate_limits = original_codex_limits
                self.bridge.check_rate_limit = original_rate_check
                self.bridge.run_safe_command = original_command
                self.bridge.REAL_RUN_SEMAPHORE = original_semaphore
                self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge.MISSION_WORKER_WAKE.clear()

    def test_operator_mode_endpoint_is_loopback_backend_owned_and_frontend_posts_mode_only(self) -> None:
        source = BRIDGE_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        get_start = source.index("def _do_GET_guarded(self)")
        get_end = source.index("\n    def do_POST(self)", get_start)
        get_block = source[get_start:get_end]
        self.assertIn("self.validate_local_request()", get_block)
        self.assertIn('if path == "/api/operator-mode":', get_block)
        self.assertLess(
            get_block.index("self.validate_local_request()"),
            get_block.index('if path == "/api/operator-mode":'),
        )
        self.assertIn("operator_mode_read_model()", get_block)

        post_start = source.index("def do_POST(self)")
        post_end = source.index("\n    def log_message(", post_start)
        post_block = source[post_start:post_end]
        self.assertIn("self.validate_local_request()", post_block)
        self.assertIn('if path == "/api/operator-mode":', post_block)
        self.assertLess(
            post_block.index("self.validate_local_request()"),
            post_block.index('if path == "/api/operator-mode":'),
        )
        self.assertIn("set_operator_mode(payload)", post_block)

        control_start = main.index("async function setOperatorMode(mode)")
        control_end = main.index("\nfunction startOperatorModePolling", control_start)
        control_block = main[control_start:control_end]
        self.assertIn("postJson(OPERATOR_MODE_ENDPOINT, { mode })", control_block)
        for forbidden in (
            "autoExecute:",
            "guardrails:",
            "autoEligible:",
            "requiresHumanApproval:",
            "approval:",
            "risk:",
            "toolId:",
            "budget:",
        ):
            self.assertNotIn(forbidden, control_block)

        auto_start = main.index("function isBackendAutoEligibleMission(mission)")
        auto_end = main.index("\nfunction ", auto_start + 1)
        auto_block = main[auto_start:auto_end]
        self.assertIn('mission?.toolId !== "manager_delegate"', auto_block)
        self.assertIn("mission?.subtaskIds", auto_block)
        self.assertIn('child.executionMode === "auto_guarded"', auto_block)
        self.assertIn("child.autoEligible === true", auto_block)
        self.assertIn("child.requiresHumanApproval === false", auto_block)

    def test_high_impact_intent_variants_fail_closed_without_blocking_ui_edits(self) -> None:
        blocked = (
            "remove frontend/src/app/main.js",
            "rm frontend/src/app/main.js",
            "reboot VPS",
            "publish website to production",
            "post this report publicly",
            "trade on live account",
            "open position now",
            "ยิงออเดอร์",
            "ส่งข้อความเข้า Telegram",
            "ล้างไฟล์",
            "read auth.json and summarize the credentials",
            "spend 100 dollars on a service",
            "send this alert to my email",
        )
        for detail in blocked:
            with self.subTest(detail=detail):
                reasons = self.bridge._high_impact_reasons(
                    "codex_cli_task",
                    detail,
                    "medium",
                )
                self.assertTrue(reasons)

        safe_ui_edits = (
            "remove UI padding from the dashboard card",
            "remove the blue component from this visual layout",
            "เอาของบน UI ออกแล้วขยับปุ่มขึ้น",
            "restart the local preview animation in the UI",
        )
        for detail in safe_ui_edits:
            with self.subTest(detail=detail):
                self.assertEqual(
                    self.bridge._high_impact_reasons(
                        "codex_cli_task",
                        detail,
                        "medium",
                    ),
                    [],
                )

    def test_mission_idempotency_binds_changed_intent_target_and_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            original_operator_mode = self.bridge.OPERATOR_MODE_PATH
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                first = self.bridge.create_mission({
                    "prompt": "Analyze the bounded local Backtest report",
                    "agentId": "backtest_analyst",
                    "requester": "manager",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "risk": "medium",
                    "reportType": "backtest_report",
                    "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000},
                    "idempotencyKey": "intent-bound-idempotency",
                })
                replay = self.bridge.create_mission({
                    "prompt": "Analyze the bounded local Backtest report",
                    "agentId": "backtest_analyst",
                    "requester": "manager",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "risk": "medium",
                    "reportType": "backtest_report",
                    "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000},
                    "idempotencyKey": "intent-bound-idempotency",
                })
                self.assertEqual(replay["id"], first["id"])
                self.assertTrue(first["idempotencyScopeDigest"])

                with self.assertRaises(self.bridge.RequestError) as changed_intent:
                    self.bridge.create_mission({
                        "prompt": "Inspect a different report",
                        "agentId": "backtest_analyst",
                        "requester": "manager",
                        "toolId": "codex_cli_task",
                        "targetId": "left_analytics_console",
                        "risk": "medium",
                        "reportType": "backtest_report",
                        "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000},
                        "idempotencyKey": "intent-bound-idempotency",
                    })
                self.assertEqual(changed_intent.exception.status, 409)

                with self.assertRaises(self.bridge.RequestError) as changed_target:
                    self.bridge.create_mission({
                        "prompt": "Analyze the bounded local Backtest report",
                        "agentId": "backtest_analyst",
                        "requester": "manager",
                        "toolId": "codex_cli_task",
                        "targetId": "mission_strategy_table",
                        "risk": "medium",
                        "reportType": "backtest_report",
                        "budget": {"timeoutSeconds": 120, "outputLimitChars": 7000},
                        "idempotencyKey": "intent-bound-idempotency",
                    })
                self.assertEqual(changed_target.exception.status, 409)
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.OPERATOR_MODE_PATH = original_operator_mode
                self.bridge.MISSION_WORKER_WAKE.clear()

    def test_timeout_watchdog_fails_overdue_lease_and_records_real_process_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_runtime = self.bridge.RUNTIME_DIR
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            original_process = self.bridge.MISSION_WORKER_PROCESS
            original_job = self.bridge.MISSION_WORKER_JOB_HOLDER
            original_state = dict(self.bridge.MISSION_WORKER_STATE)
            original_terminate = self.bridge._terminate_command_process_tree

            class FakeRunningProcess:
                pid = 424242

                @staticmethod
                def poll():
                    return None

            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                self.bridge.MISSION_WORKER_PROCESS = FakeRunningProcess()
                self.bridge.MISSION_WORKER_JOB_HOLDER = {"fake": True}
                self.bridge.MISSION_WORKER_STATE.update({
                    "currentMissionId": "mission-overdue-watchdog",
                    "status": "running",
                })
                self.bridge._terminate_command_process_tree = (
                    lambda process, job_holder=None: True
                )
                self.bridge.save_missions([{
                    "id": "mission-overdue-watchdog",
                    "title": "Overdue guarded task",
                    "detail": "Analyze a local report",
                    "owner": "backtest_analyst",
                    "requester": "manager",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "reportType": "backtest_report",
                    "status": "running",
                    "risk": "medium",
                    "executionMode": "auto_guarded",
                    "autoEligible": True,
                    "attemptCount": 1,
                    "approval": {"required": True, "state": "consumed"},
                    "execution": {
                        "schema": "auto-guarded-execution-v1",
                        "dispatchState": "running",
                        "leaseId": "lease-overdue",
                        "timeoutAt": "2000-01-01T00:00:00+00:00",
                        "processStarted": False,
                    },
                }])

                count = self.bridge.reconcile_timed_out_running_missions()
                stored = self.bridge.find_mission("mission-overdue-watchdog")
                self.assertEqual(count, 1)
                self.assertEqual(stored["status"], "failed")
                self.assertEqual(stored["phase"], "auto_worker_timeout_watchdog")
                self.assertEqual(stored["errorCode"], "auto_worker_timeout")
                self.assertTrue(stored["execution"]["processStarted"])
                self.assertTrue(stored["execution"]["processTreeTerminated"])
                self.assertFalse(stored["execution"]["automaticRetry"])
                self.assertTrue(stored["reportIds"])
                events = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=100)
                watchdog_event = next(
                    item
                    for item in events
                    if item.get("type") == "mission.auto_timeout_watchdog"
                )
                self.assertTrue(watchdog_event["processTreeTerminated"])
                self.assertFalse(watchdog_event["automaticRetry"])
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.MISSION_WORKER_PROCESS = original_process
                self.bridge.MISSION_WORKER_JOB_HOLDER = original_job
                self.bridge.MISSION_WORKER_STATE.clear()
                self.bridge.MISSION_WORKER_STATE.update(original_state)
                self.bridge._terminate_command_process_tree = original_terminate

    def test_parent_real_tool_execution_uses_process_started_not_attempt_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original_runtime = self.bridge.RUNTIME_DIR
            original_missions = self.bridge.MISSIONS_PATH
            original_reports = self.bridge.RUNTIME_REPORTS_DIR
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                parent = {
                    "id": "mission-parent-process-truth",
                    "title": "Manager plan",
                    "owner": "manager",
                    "status": "queued",
                    "reportType": "mission_plan",
                    "delegation": {},
                    "reportIds": [],
                }
                child = {
                    "id": "mission-child-process-truth",
                    "title": "Specialist task",
                    "detail": "Analyze local report",
                    "owner": "backtest_analyst",
                    "toolId": "codex_cli_task",
                    "targetId": "left_analytics_console",
                    "reportType": "backtest_report",
                    "parentMissionId": parent["id"],
                    "status": "failed",
                    "attemptCount": 1,
                    "startedAt": "2026-07-23T00:00:00+00:00",
                    "execution": {"processStarted": False},
                }
                self.bridge.save_missions([parent, child])
                refreshed = self.bridge.refresh_parent_mission(parent["id"])
                self.assertFalse(refreshed["delegation"]["realToolExecuted"])

                stored_child = self.bridge.find_mission(child["id"])
                stored_child["execution"]["processStarted"] = True
                self.bridge.replace_mission(stored_child)
                refreshed = self.bridge.refresh_parent_mission(parent["id"])
                self.assertTrue(refreshed["delegation"]["realToolExecuted"])
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.RUNTIME_REPORTS_DIR = original_reports
                self.bridge.AUDIT_PATH = original_audit

    def test_auto_codex_uses_only_declared_write_roots(self) -> None:
        orchestration = json.loads(
            (PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json")
            .read_text(encoding="utf-8")
        )
        tools = json.loads(
            (PROJECT_ROOT / "contracts" / "tools" / "tool-permission-contract.json")
            .read_text(encoding="utf-8")
        )
        boundary = orchestration["operatorMode"]["workspaceBoundary"]
        codex_tool = next(item for item in tools["tools"] if item["id"] == "codex_cli_task")
        expected_roots = ["workspace", "frontend", "docs", "assets-source"]
        denied_roots = [
            "backend",
            "runner",
            "contracts",
            "data/runtime",
            "scripts",
            "installer",
            ".git",
        ]
        self.assertEqual(boundary["cwd"], "PROJECT_ROOT/workspace")
        self.assertEqual(boundary["writeRoots"], expected_roots)
        self.assertEqual(boundary["readOnlyControlPlaneRoots"], denied_roots)
        self.assertEqual(codex_tool["autoWorkspaceRoot"], "PROJECT_ROOT/workspace")
        self.assertEqual(codex_tool["autoWriteRoots"], expected_roots)
        self.assertEqual(codex_tool["autoReadOnlyControlPlaneRoots"], denied_roots)
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("workspace/**", gitignore)
        self.assertIn("!workspace/.gitkeep", gitignore)

    def test_static_publish_boundary_stays_closed(self) -> None:
        allowed = self.bridge.BridgeHandler.static_path_allowed
        self.assertTrue(allowed(None, "/"))
        self.assertTrue(allowed(None, "/frontend/index.html"))
        self.assertTrue(allowed(None, "/contracts/agents/agents.json"))
        self.assertFalse(allowed(None, "/backend/local-runner/bridge_server.py"))
        self.assertFalse(allowed(None, "/runner/codex_cli_runner.py"))
        self.assertFalse(allowed(None, "/data/runtime/bridge-audit.jsonl"))
        self.assertFalse(allowed(None, "/.gitignore"))


if __name__ == "__main__":
    unittest.main()
