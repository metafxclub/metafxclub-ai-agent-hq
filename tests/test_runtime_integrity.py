from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = PROJECT_ROOT / "backend" / "local-runner" / "bridge_server.py"
RUNNER_PATH = PROJECT_ROOT / "runner" / "codex_cli_runner.py"
FRONTEND_INDEX_PATH = PROJECT_ROOT / "frontend" / "index.html"
FRONTEND_MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
FRONTEND_STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"
LIFECYCLE_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "start-local-bridge.ps1"
AUTOSTART_REGISTER_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "register-bridge-autostart.ps1"
AUTOSTART_UNREGISTER_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "unregister-bridge-autostart.ps1"
UPDATE_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "update-hq.ps1"
INSTALLER_SCRIPT_PATH = PROJECT_ROOT / "installer" / "install.ps1"
UNINSTALL_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "uninstall-hq.ps1"
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

    def test_visual_roster_and_daily_council_session_migrate_without_overlap(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        self.assertIn("const EXPECTED_OFFICE_AGENT_COUNT = 10;", main)
        self.assertIn("const OFFICE_LAYOUT_VERSION = 2;", main)
        self.assertIn("const SIGNAL_DASHBOARD_VERSION = 6;", main)
        self.assertIn(
            "const SIGNAL_CHART_DISPLAY_BAR_OPTIONS = [40, 60, 120, 240, 500, 1000];",
            main,
        )
        self.assertIn(
            "const SIGNAL_ANALYSIS_BAR_OPTIONS = [120, 180, 240, 300, 500, 1000];",
            main,
        )
        for contract_path in (
            PROJECT_ROOT / "contracts" / "connections" / "dashboard-connection-contract.json",
            PROJECT_ROOT / "contracts" / "props" / "property-role-map.json",
        ):
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            serialized = json.dumps(contract, ensure_ascii=False, separators=(",", ":"))
            self.assertIn(
                '"displayBars":{"owner":"frontend_client_only","allowedValues":[40,60,120,240,500,1000],"affectsAnalysis":false}',
                serialized,
            )
        self.assertIn("function savedOfficeAgentsOverlap(snapshot)", main)
        self.assertIn("function migrateOfficeSessionLayout(snapshot)", main)
        self.assertIn("function selectNewestSessionSnapshot(localSession, backendSession)", main)
        self.assertIn("localDashboardVersion > backendDashboardVersion", main)
        self.assertIn("staleSignalDashboard", main)
        self.assertIn(
            "const legacyDeepTab = SIGNAL_DEEP_ANALYSIS_TABS.includes(legacySignalTab)",
            main,
        )
        self.assertIn('legacyDeepTab\n      ? "live_analysis"', main)
        self.assertIn("migratedModal.signalLiveTab = legacyDeepTab || (", main)
        self.assertIn(': "chart_overview"', main)
        self.assertIn(
            "migratedModal.signalChartDisplayBars = SIGNAL_CHART_DEFAULT_DISPLAY_BARS;",
            main,
        )
        self.assertIn("signalDashboardVersion: SIGNAL_DASHBOARD_VERSION", main)
        self.assertIn(
            'codex_mcp_operator: { x: 33.5, y: 61.0, label: `จุดวิเคราะห์ข่าวของ ${AI_TRADE_COUNCIL_PUBLIC_NAMES.codex_mcp_operator}` }',
            main,
        )
        self.assertNotIn(
            'telegram_ops: { x: 33.5, y: 61.0, label: "จุดวิเคราะห์ข่าวของ Telegram Ops" }',
            main,
        )

    def test_ui_session_store_rejects_an_older_dashboard_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_path = self.bridge.UI_SESSION_PATH
            self.bridge.UI_SESSION_PATH = Path(temp_dir) / "ui-session.json"
            try:
                current = {
                    "savedAt": "2026-08-01T13:46:20Z",
                    "modal": {
                        "signalDashboardVersion": 6,
                        "signalTab": "live_analysis",
                        "signalLiveTab": "technical_deep",
                    },
                }
                stale = {
                    "savedAt": "2026-08-01T13:47:20Z",
                    "modal": {
                        "signalDashboardVersion": 5,
                        "signalTab": "price_action",
                    },
                }
                stored = self.bridge.store_ui_session(current)
                ignored = self.bridge.store_ui_session(stale)
                payload = json.loads(self.bridge.UI_SESSION_PATH.read_text(encoding="utf-8"))
            finally:
                self.bridge.UI_SESSION_PATH = original_path

        self.assertFalse(stored["ignored"])
        self.assertTrue(ignored["ignored"])
        self.assertEqual(ignored["reason"], "older_dashboard_version")
        self.assertEqual(payload["session"]["modal"]["signalDashboardVersion"], 6)
        self.assertEqual(payload["session"]["modal"]["signalLiveTab"], "technical_deep")

    def test_ai_trade_council_keeps_ea_channel_visible_after_snapshot_ready(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")
        daily_start = main.index("function renderSignalDailyPanel(report = {})")
        daily_end = main.index("async function setAiTradeCouncilAutomation", daily_start)
        daily = main[daily_start:daily_end]

        self.assertIn("function signalSnapshotChannel(report = {})", main)
        self.assertIn("report?.metatraderReadOnly?.installPreparation?.snapshotChannel", main)
        self.assertIn("council?.tradeGateway?.selectedCandidateId", main)
        self.assertIn("const snapshotChannel = signalSnapshotChannel(report);", daily)
        self.assertIn("data-signal-channel-code", daily)
        self.assertIn("data-signal-copy-channel", daily)
        self.assertIn("SnapshotChannel", daily)
        self.assertNotIn("!daily.available && snapshotChannel", daily)
        self.assertIn(".signal-channel-card", styles)

    def test_ai_trade_council_explains_signed_live_readiness_without_false_positive(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        self.assertIn("gatewayLiveArmed: gateway.liveArmed === true", main)
        self.assertIn("signedCommandRequiredForLive", main)
        self.assertIn("backendSignedCommandVerificationAvailable", main)
        self.assertIn("signedCommandVerificationAvailable", main)
        self.assertIn("signingKeyMatch", main)
        self.assertIn("signingKeyPinned", main)
        self.assertIn("ลายเซ็นคำสั่งจาก Local Runner", main)
        self.assertIn("Key ID สำหรับตั้ง Live", main)
        self.assertIn("คัดลอก Signing Key ID สำหรับตั้งค่า Live ที่ EA", main)
        self.assertIn("Key สำหรับบัญชีจริง", main)
        self.assertIn("ยังไม่เทรดจริง • EA อยู่ SHADOW", main)
        self.assertIn("ยังไม่เทรดจริง • ต้องเปิด LiveArmed ที่ EA", main)
        self.assertIn("ต้องปักหมุด Trusted Signing Key ID ที่ EA", main)
        self.assertNotIn('"ปิดที่ EA"', main)

    def test_ai_trade_council_hold_is_abstention_veto_is_news_blocker_and_ui_is_explicit(self) -> None:
        prompts = json.loads(
            (
                PROJECT_ROOT
                / "contracts"
                / "orchestration"
                / "ai-trade-council-prompts.json"
            ).read_text(encoding="utf-8")
        )
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        index = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        policy = prompts["sharedPolicy"]
        news = next(agent for agent in prompts["agents"] if agent["roleId"] == "news")

        self.assertEqual(policy["qualityGate"]["newsEventRiskBlockingValues"], ["VETO"])
        self.assertIn("HOLD เป็นการงดออกเสียงและไม่บล็อก Order", policy["consensusPolicy"])
        self.assertIn("Only eventRisk=VETO blocks the entire round", news["roleOutputRule"])
        self.assertIn("อย่างน้อย 2 โดเมนสาธารณะที่ต่างกัน", news["promptTemplate"])
        self.assertIn('if (normalized === "HOLD") return "งดออกเสียง";', main)
        self.assertIn('eventRiskVeto ? "หยุดเพราะข่าว (VETO)"', main)
        self.assertIn('"งดออกเสียง • ไม่หยุดรอบ"', main)
        self.assertIn("LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT", main)
        self.assertIn("DEMO_MODE_REQUIRES_DEMO_ACCOUNT", main)
        self.assertIn("ACCOUNT_IDENTITY_UNAVAILABLE", main)
        self.assertIn("DECISION_DISPATCH_WINDOW_EXPIRED", main)
        self.assertIn("20260808-workflow-transfer-v050", index)

    def test_ai_trade_council_shows_protective_plan_source_and_thai_block_reason(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")
        index = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        orchestration = json.loads(
            (PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json")
            .read_text(encoding="utf-8")
        )
        reports = json.loads(
            (PROJECT_ROOT / "contracts" / "reports" / "report-contract.json")
            .read_text(encoding="utf-8")
        )
        prompts = json.loads(
            (PROJECT_ROOT / "contracts" / "orchestration" / "ai-trade-council-prompts.json")
            .read_text(encoding="utf-8")
        )

        self.assertEqual(orchestration["version"], "orchestration-contract-v009")
        self.assertEqual(reports["version"], "report-contract-v011")
        policy = orchestration["aiTradeCouncilAutoAnalysis"]["consensusPolicy"]
        self.assertEqual(
            policy["protectivePlanSources"],
            ["price_action_agent", "backend_deterministic_fallback", "unavailable"],
        )
        self.assertEqual(
            policy["protectivePlanFallback"]["ownerRole"],
            "backend_deterministic_guard",
        )
        trade_plan = reports["typed_report_schemas"]["ai_trade_council_report"]["consensus"]["tradePlan"]
        self.assertEqual(
            trade_plan["protectivePlanProvenance"]["schemaVersion"],
            "ai-trade-council-protective-plan-v1",
        )
        self.assertIn("backend_deterministic_fallback", prompts["sharedPolicy"]["protectiveFallbackPolicy"])
        self.assertIn("function signalProtectivePlanViewModel(", main)
        self.assertIn("function renderSignalProtectivePlanProvenance(", main)
        self.assertGreaterEqual(main.count("data-signal-plan-provenance"), 4)
        self.assertIn("SL/TP จาก Price Action AI", main)
        self.assertIn("SL/TP สำรองจาก Backend", main)
        self.assertIn("SL/TP จาก Price Action ไม่ผ่าน", main)
        self.assertIn("ไม่พบลายนิ้วมือดิจิทัลของ Snapshot", main)
        self.assertIn("ลายนิ้วมือดิจิทัลของ Snapshot ไม่ตรงกัน", main)
        self.assertIn("fallback_snapshot_digest_missing", main)
        self.assertIn("fallback_snapshot_digest_mismatch", main)
        self.assertIn('.signal-protective-plan-provenance[data-state="blocked"]', styles)
        self.assertIn("20260808-workflow-transfer-v050", index)

    def test_daily_council_frontend_consumes_v2_votes_and_finishes_read_only_pipeline(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        self.assertIn("const parentSource = response?.parent || response?.manager;", main)
        self.assertIn("function signalCurrentConsensusSource(", main)
        self.assertIn("sourceMissionId === parentId", main)
        self.assertIn("sourceSnapshotId === runSnapshotId", main)
        self.assertIn("const sourceVotes = Array.isArray(consensusSelection.source?.votes)", main)
        self.assertIn("view.decision || view.direction || view.vote", main)
        self.assertIn("Array.isArray(view.observations)", main)
        self.assertIn('.replaceAll("_", " ")', main)
        self.assertIn('canvas.dataset.signalDeepPriceChart = "";', main)
        self.assertIn(
            '["4", "Council Quality Gate", states.quality]',
            main,
        )
        self.assertIn('["5", "Risk / EA Gate", states.riskEa]', main)
        self.assertIn('["6", "ส่ง Command และรอ ACK",', main)
        self.assertIn('["7", "ตรวจ Fill / Recovery", states.fill]', main)
        self.assertIn("function signalCouncilQualityModel(", main)
        self.assertIn("function signalTradeOperationsModel(", main)
        self.assertIn("function signalRoundHealthModel(", main)
        self.assertIn("Specialist 3 ตัว ลงคะแนน", main)
        self.assertIn("ทั้งบัญชี MT4 (Account-wide)", main)
        self.assertIn("เฉพาะ AI Council (Council-managed)", main)
        self.assertIn("ACK EXECUTED ไม่ถูกตีความเป็น Fill ที่ตรวจแล้ว", main)
        self.assertIn(".signal-assurance-grid", styles)
        self.assertIn("repeat(auto-fit, minmax(240px, 1fr))", styles)
        self.assertNotIn("min-width: 1110px;", styles)
        self.assertIn("riskGuard.terminalActions === false", main)
        self.assertIn("gatewayRun.commandPublished === true", main)

    def test_current_council_round_never_reuses_a_historical_gateway_command(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.assertIn("function signalCommandMatchesCurrentRound(", main)
        self.assertIn("commandMissionId !== expectedMissionId", main)
        self.assertIn("commandSnapshotId === expectedSnapshotId", main)
        self.assertIn('if (!run.parent || !run.snapshotId) return { source: {}, current: false, run };', main)
        self.assertIn("gatewayCommandMatchesCurrentRound: Boolean(gatewayCommand)", main)
        self.assertIn("gatewayLatestHistoricalCommand: latestCommand", main)
        self.assertNotIn(
            'const gatewayCommand = gateway.activeCommand && typeof gateway.activeCommand === "object"',
            main,
        )

        summary = self.bridge._mt4_trade_gateway_command_summary({
            "command": {
                "commandId": "cmd-current-round",
                "missionId": "mission-current-round",
                "snapshotId": "a" * 64,
                "councilDecisionId": "council-current-round",
                "action": "BUY",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "stopLoss": 4300.0,
                "takeProfit": 4400.0,
            },
            "status": "published",
            "outstanding": True,
        })
        self.assertEqual(summary["missionId"], "mission-current-round")
        self.assertEqual(summary["snapshotId"], "a" * 64)

    def test_quality_gate_and_agent_cards_fail_closed_on_stale_or_truncated_evidence(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        quality_start = main.index("function signalCouncilQualityModel(")
        quality_end = main.index("\nfunction ", quality_start + 10)
        quality = main[quality_start:quality_end]
        self.assertIn("gateMatchesCurrentRun", quality)
        self.assertIn("missionId === expectedMissionId && snapshotId === expectedSnapshotId", quality)
        self.assertIn("currentConsensusSelection.current", quality)
        self.assertNotIn("].find((value) => value && typeof value === \"object\") || null", quality)

        agent_start = main.index("function signalAgentViews(")
        agent_end = main.index("\nfunction ", agent_start + 10)
        agent_views = main[agent_start:agent_end]
        self.assertIn('reason !== "[TRUNCATED]"', agent_views)
        self.assertIn("เปิดรายละเอียด Mission เพื่อดูข้อมูลฉบับเต็ม", agent_views)

    def test_agent_sidebar_tracks_pending_and_blocked_work_and_mission_poll_is_change_aware(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.assertIn("function missionReadModelSignature(missions = [])", main)
        self.assertIn("const missionChanged = hasBackendMissionList", main)
        self.assertIn("if (persist && missionChanged) saveSessionSnapshot();", main)

        mission_start = main.index("function getActiveMissionForAgent(")
        mission_end = main.index("\nfunction getAgentSidebarState", mission_start)
        mission_block = main[mission_start:mission_end]
        for status in ("running", "blocked", "failed", "waiting_approval", "queued"):
            self.assertIn(f"{status}:", mission_block)
        sidebar_start = main.index("function getAgentSidebarState(")
        sidebar_end = main.index("\nfunction createAgentStatusCard", sidebar_start)
        sidebar = main[sidebar_start:sidebar_end]
        self.assertIn('signalMissionReason(mission, "เปิดรายละเอียด Task เพื่อดูสาเหตุและวิธีแก้")', sidebar)

    def test_today_work_sidebar_uses_progressive_rendering_instead_of_mounting_full_history(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        self.assertIn("const AGENT_COLLABORATION_POLL_MS = 15000;", main)
        self.assertIn("todayWorkView", main)
        self.assertIn("missions.slice(0, limit)", main)
        self.assertIn("ดูเพิ่มอีก ${nextBatch} งาน", main)
        self.assertIn("state.todayWorkView.completedLimit += count", main)
        self.assertIn(".today-work-more", styles)
        self.assertIn("runtime.gatewayConnected", main)
        self.assertIn("Array.isArray(pipeline.items) ? pipeline.items : []", main)
        self.assertIn("const suppliedMissions = Array.isArray(pipeline.items)", main)
        self.assertIn("function signalCouncilRunModel(report = {})", main)
        self.assertIn("run.counts.blocked > 0", main)
        self.assertIn("data-signal-run-reason", main)
        self.assertIn("signalMissionStatusLabel(event)", main)
        self.assertIn("function signalSnapshotComparisonText(", main)
        self.assertIn("เป็นข้อมูลคนละรอบ", main)
        decision_panel = main[
            main.index("function renderSignalDecisionPanel("):
            main.index("function signalHistoryEntries(")
        ]
        self.assertNotIn("runtime.liveOrderExecutionAvailable", decision_panel)
        self.assertIn("function renderSignalConsensusPanel(tabName, report = {})", main)

    def test_room_declares_nine_dashboards_and_one_mission_kanban(self) -> None:
        room = json.loads((PROJECT_ROOT / "contracts" / "rooms" / "command-room.json").read_text(encoding="utf-8"))
        roles = json.loads((PROJECT_ROOT / "contracts" / "props" / "property-role-map.json").read_text(encoding="utf-8"))["properties"]
        prop_ids = {str(item["id"]) for item in room["props"]}
        dashboards = {prop_id for prop_id, role in roles.items() if role.get("interactionMode") == "dashboard"}
        kanban = {prop_id for prop_id, role in roles.items() if role.get("interactionMode") == "kanban"}
        self.assertEqual(len(prop_ids), 10)
        self.assertEqual(len(dashboards), 9)
        self.assertEqual(kanban, {"mission_strategy_table"})

    def test_repurposed_props_keep_canonical_roles_and_safe_report_routes(self) -> None:
        role_map = json.loads(
            (PROJECT_ROOT / "contracts" / "props" / "property-role-map.json")
            .read_text(encoding="utf-8")
        )["properties"]
        profiles = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))["profiles"]
        report_targets = json.loads(
            (PROJECT_ROOT / "contracts" / "reports" / "report-contract.json")
            .read_text(encoding="utf-8")
        )["report_targets"]

        canonical = {
            "left_audit_crystals": {
                "functionName": "Indicator Website Scout",
                "owner": "codex_mcp_operator",
                "primaryReportType": "indicator_scout_report",
                "actions": {"discover_new_indicators", "save_indicator_scout_schedule"},
            },
            "left_signal_cube": {
                "functionName": "Daily Market News & FX Bias",
                "owner": "codex_mcp_operator",
                "primaryReportType": "fx_news_bias_report",
                "actions": {
                    "analyze_daily_market_news",
                    "build_fx_pair_bias",
                    "save_news_bias_schedule",
                },
            },
            "terminal_workstation": {
                "functionName": "EA Development Studio",
                "owner": "ea_developer",
                "primaryReportType": "ea_development_report",
                "actions": {
                    "inspect_ea_source",
                    "develop_ea_source",
                    "propose_ea_performance_improvements",
                },
            },
            "right_status_crystals": {
                "functionName": "VPS / HQ Health & Agent Settings",
                "owner": "vps_watch",
                "primaryReportType": "ops_overview_report",
                "actions": {"refresh_vps_hq_status", "save_agent_preferences"},
            },
        }
        for prop_id, expected in canonical.items():
            with self.subTest(prop=prop_id):
                role = role_map[prop_id]
                profile = profiles[prop_id]
                self.assertEqual(role["functionName"], expected["functionName"])
                self.assertEqual(role["primaryOwnerAgentId"], expected["owner"])
                self.assertEqual(role["primaryReportType"], expected["primaryReportType"])
                self.assertEqual(set(role["allowedDashboardActions"]), expected["actions"])
                self.assertIn(expected["primaryReportType"], role["acceptedReportTypes"])
                self.assertIn(prop_id, report_targets[expected["primaryReportType"]])
                self.assertEqual(profile["reportRoute"]["targetPropId"], prop_id)
                self.assertEqual(
                    profile["reportRoute"]["primaryReportType"],
                    expected["primaryReportType"],
                )
                self.assertEqual(
                    profile["reportRoute"]["summaryTargetPropId"],
                    "mission_strategy_table",
                )
                connection_ids = {item["id"] for item in profile["connections"]}
                self.assertTrue(
                    "mission_report_audit" in connection_ids
                    or {"mission_store", "agent_event_store", "report_routing"}.issubset(connection_ids),
                    f"{prop_id} must retain Mission / Report / Audit tracking",
                )

        news_policy = role_map["left_signal_cube"]["executionPolicy"]
        self.assertEqual(news_policy["mode"], "analysis_only")
        self.assertFalse(news_policy["liveTradingEnabled"])
        self.assertFalse(news_policy["orderSubmissionEnabled"])
        self.assertFalse(news_policy["frontendMayEnableExecution"])
        self.assertFalse(role_map["terminal_workstation"]["artifactPolicy"]["rawPathAllowed"])
        self.assertFalse(role_map["terminal_workstation"]["briefInputs"]["audioUploadToRunner"])
        self.assertNotIn("risk_review", role_map["left_audit_crystals"]["acceptedReportTypes"])
        self.assertNotIn("auto_trading_status_report", role_map["left_signal_cube"]["acceptedReportTypes"])
        self.assertIn("risk_review", role_map["mission_strategy_table"]["acceptedReportTypes"])
        self.assertIn("mission_strategy_table", report_targets["risk_review"])
        self.assertIn(
            "auto_trading_status_report",
            role_map["left_analytics_console"]["acceptedReportTypes"],
        )
        self.assertIn("left_analytics_console", report_targets["auto_trading_status_report"])

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
        self.assertIn("codex_web_research", chat["execution"]["taskRouting"]["specialist"])
        self.assertIn("publicWebResearch", chat["execution"]["taskRouting"])
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

    def test_prop_dashboards_use_connection_rail_and_single_work_results_view(self) -> None:
        contract = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))
        ui = contract["dashboardUi"]
        self.assertEqual(ui["dashboardCount"], 9)
        self.assertTrue(ui["missionStrategyTableIsKanban"])
        self.assertTrue(ui["missionStrategyTableExcludedFromDashboardTabs"])
        self.assertEqual(ui["defaultView"], "work_results")
        self.assertFalse(ui["tabsEnabled"])
        self.assertEqual(
            set(ui["layout"]["leftRail"]["shows"]),
            {"prop_image", "short_description", "connection_checklist", "connection_actions"},
        )
        self.assertEqual(
            set(ui["layout"]["leftRail"]["doesNotShow"]),
            {"owner_summary", "report_type", "mission_count", "memory_count", "generic_prop_status"},
        )
        self.assertEqual(
            set(ui["layout"]["mainWorkspace"]["showsOnly"]),
            {"missions", "structured_reports", "report_attachments"},
        )
        status_groups = ui["layout"]["mainWorkspace"]["statusGroups"]
        self.assertEqual(set(status_groups), {"running", "completed", "blocked"})
        self.assertTrue({"queued", "running", "draft"}.issubset(status_groups["running"]))
        self.assertTrue({"completed", "archived", "ready", "published"}.issubset(status_groups["completed"]))
        self.assertTrue(
            {"waiting_approval", "needs_approval", "blocked", "failed", "error"}.issubset(status_groups["blocked"])
        )
        self.assertFalse(ui["propChatEnabled"])
        self.assertTrue(ui["taskCardsOpenDetails"])
        self.assertTrue(ui["reportCardsOpenDetails"])
        self.assertTrue(ui["connectionRailDoesNotCreateTasks"])
        self.assertTrue(ui["reportDetailsSupportTextMetricsAndImages"])

    def test_ai_trade_council_uses_four_top_tabs_and_four_accessible_live_analysis_subtabs(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        connection_contract = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))
        role_map = json.loads(
            (PROJECT_ROOT / "contracts" / "props" / "property-role-map.json").read_text(encoding="utf-8")
        )["properties"]
        agents = json.loads(
            (PROJECT_ROOT / "contracts" / "agents" / "agents.json").read_text(encoding="utf-8")
        )["agents"]

        self.assertFalse(connection_contract["dashboardUi"]["tabsEnabled"])
        self.assertEqual(connection_contract["dashboardUi"]["defaultView"], "work_results")
        self.assertIn("localTabs", connection_contract["profiles"]["left_analytics_console"])
        self.assertEqual(
            [item["id"] for item in connection_contract["profiles"]["left_analytics_console"]["localTabs"]],
            [
                "daily_summary",
                "live_analysis",
                "decision_pipeline",
                "history",
            ],
        )
        self.assertEqual(
            connection_contract["profiles"]["left_analytics_console"]["defaultLiveAnalysisSubTab"],
            "chart_overview",
        )
        self.assertEqual(
            [
                item["id"]
                for item in connection_contract["profiles"]["left_analytics_console"]["liveAnalysisSubTabs"]
            ],
            ["chart_overview", "price_action", "technical_deep", "news_context"],
        )
        news_profile = connection_contract["profiles"]["left_signal_cube"]
        self.assertEqual(
            [item["id"] for item in news_profile["localTabs"]],
            ["today", "pair_bias", "horizons", "schedule_history"],
        )
        self.assertEqual(news_profile["reportRoute"]["primaryReportType"], "fx_news_bias_report")
        self.assertEqual(news_profile["reportRoute"]["targetPropId"], "left_signal_cube")
        self.assertFalse(news_profile["liveTradingPolicy"]["enabled"])
        self.assertFalse(news_profile["liveTradingPolicy"]["activationFromFrontend"])
        self.assertTrue(news_profile["liveTradingPolicy"]["analysisIsNotTradeSignal"])
        self.assertIn("localTabs", role_map["left_analytics_console"])
        self.assertEqual(
            [item["id"] for item in role_map["left_analytics_console"]["localTabs"]],
            [
                "daily_summary",
                "live_analysis",
                "decision_pipeline",
                "history",
            ],
        )
        self.assertEqual(
            role_map["left_analytics_console"]["defaultLiveAnalysisSubTab"],
            "chart_overview",
        )
        self.assertEqual(
            [item["id"] for item in role_map["left_analytics_console"]["liveAnalysisSubTabs"]],
            ["chart_overview", "price_action", "technical_deep", "news_context"],
        )
        self.assertEqual(
            role_map["left_analytics_console"]["dashboardSections"],
            ["daily_summary", "live_analysis", "decision_pipeline", "history"],
        )
        for contract_source in (
            connection_contract["profiles"]["left_analytics_console"]["liveAnalysisSubTabs"],
            role_map["left_analytics_console"]["liveAnalysisSubTabs"],
        ):
            sub_tabs = {item["id"]: item for item in contract_source}
            self.assertEqual(sub_tabs["chart_overview"]["labelTh"], "ภาพรวมสภา AI")
            self.assertIn("ผู้เชี่ยวชาญ 3 ตัว", sub_tabs["chart_overview"]["purpose"])
            self.assertIn("สถานะการวิเคราะห์", sub_tabs["chart_overview"]["purpose"])
            self.assertIn("มติล่าสุด", sub_tabs["chart_overview"]["purpose"])
            self.assertIn("ไม่แสดงกราฟ", sub_tabs["chart_overview"]["purpose"])
            self.assertEqual(
                sub_tabs["price_action"]["labelTh"],
                "กราฟเปล่าและโครงสร้างราคา",
            )
            for item in contract_source:
                self.assertTrue(str(item.get("labelTh") or "").strip())
                self.assertTrue(str(item.get("purpose") or "").strip())
        self.assertEqual(role_map["left_analytics_console"]["defaultTab"], "daily_summary")
        self.assertEqual(
            [item["id"] for item in role_map["left_signal_cube"]["localTabs"]],
            ["today", "pair_bias", "horizons", "schedule_history"],
        )
        self.assertEqual(role_map["left_signal_cube"]["primaryReportType"], "fx_news_bias_report")
        self.assertEqual(role_map["left_signal_cube"]["executionPolicy"]["mode"], "analysis_only")
        self.assertFalse(role_map["left_signal_cube"]["executionPolicy"]["liveTradingEnabled"])
        self.assertEqual(role_map["left_analytics_console"]["primaryOwnerAgentId"], "manager")
        manager = next(agent for agent in agents if agent["id"] == "manager")
        self.assertIn("left_analytics_console", manager["allowed_surfaces"])

        shared_tab_start = main.index("function setModalTab(")
        shared_tab_end = main.find("\nfunction ", shared_tab_start + 1)
        shared_tab_block = main[shared_tab_start:shared_tab_end if shared_tab_end >= 0 else len(main)]
        self.assertIn('dashboard: ["results"]', shared_tab_block)
        for nested_key in (
            "daily_summary",
            "live_analysis",
            "chart_overview",
            "price_action",
            "technical_deep",
            "news_context",
            "decision_pipeline",
            "history",
        ):
            self.assertNotIn(f'dashboard: ["{nested_key}"', shared_tab_block)

        self.assertIn('const AI_TRADE_COUNCIL_PROP_ID = "left_analytics_console";', main)
        self.assertNotIn('const AI_TRADE_COUNCIL_PROP_ID = "left_signal_cube";', main)
        council_render_start = main.index("function renderSignalConsensusDashboard(")
        council_render_end = main.find("\nfunction ", council_render_start + 1)
        council_render_block = main[
            council_render_start:council_render_end if council_render_end >= 0 else len(main)
        ]
        self.assertIn("subject.id !== AI_TRADE_COUNCIL_PROP_ID", council_render_block)

        prop_render_start = main.index("function renderPropDashboard(")
        prop_render_end = main.find("\nfunction ", prop_render_start + 1)
        prop_render_block = main[prop_render_start:prop_render_end if prop_render_end >= 0 else len(main)]
        self.assertIn("subject.id === AI_TRADE_COUNCIL_PROP_ID", prop_render_block)

        dashboard_panel_start = html.index('id="modalDashboardPanel"')
        signal_workspace_start = html.index('id="modalSignalConsensusWorkspace"')
        kanban_panel_start = html.index('id="modalKanbanPanel"')
        self.assertLess(dashboard_panel_start, signal_workspace_start)
        self.assertLess(signal_workspace_start, kanban_panel_start)

        def opening_tag(element_id: str) -> str:
            match = re.search(
                rf'<[a-z][a-z0-9-]*\b(?=[^>]*\bid="{re.escape(element_id)}")[^>]*>',
                html,
                re.IGNORECASE,
            )
            self.assertIsNotNone(match, f"missing element #{element_id}")
            return match.group(0)

        tablist = opening_tag("signalConsensusTabs")
        self.assertIn('role="tablist"', tablist)
        self.assertIn("aria-label=", tablist)

        expected_top_tabs = (
            ("signalConsensusDailyTab", "daily_summary", "signalConsensusDailyPanel", True),
            ("signalConsensusLiveTab", "live_analysis", "signalConsensusLivePanel", False),
            ("signalConsensusDecisionTab", "decision_pipeline", "signalConsensusDecisionPanel", False),
            ("signalConsensusHistoryTab", "history", "signalConsensusHistoryPanel", False),
        )
        for tab_id, tab_key, panel_id, selected in expected_top_tabs:
            with self.subTest(tab=tab_key):
                tab = opening_tag(tab_id)
                panel = opening_tag(panel_id)
                self.assertIn('type="button"', tab)
                self.assertIn('role="tab"', tab)
                self.assertIn(f'data-signal-tab="{tab_key}"', tab)
                self.assertIn(f'aria-controls="{panel_id}"', tab)
                self.assertIn(f'aria-selected="{str(selected).lower()}"', tab)
                self.assertIn(f'tabindex="{"0" if selected else "-1"}"', tab)
                self.assertIn('role="tabpanel"', panel)
                self.assertIn(f'aria-labelledby="{tab_id}"', panel)
                self.assertIn(f'data-signal-panel="{tab_key}"', panel)
                if selected:
                    self.assertNotIn(" hidden", panel)
                else:
                    self.assertIn(" hidden", panel)

        live_tablist = opening_tag("signalConsensusLiveTabs")
        self.assertIn('role="tablist"', live_tablist)
        self.assertIn("aria-label=", live_tablist)
        self.assertLess(
            html.index('id="signalConsensusLivePanel"'),
            html.index('id="signalConsensusLiveTabs"'),
        )
        self.assertLess(
            html.index('id="signalConsensusLiveTabs"'),
            html.index('id="signalConsensusDecisionPanel"'),
        )

        expected_live_subtabs = (
            (
                "signalConsensusLiveOverviewTab",
                "chart_overview",
                "signalConsensusLiveOverviewPanel",
                True,
            ),
            (
                "signalConsensusPriceActionTab",
                "price_action",
                "signalConsensusPriceActionPanel",
                False,
            ),
            (
                "signalConsensusTechnicalTab",
                "technical_deep",
                "signalConsensusTechnicalPanel",
                False,
            ),
            (
                "signalConsensusNewsTab",
                "news_context",
                "signalConsensusNewsPanel",
                False,
            ),
        )
        for tab_id, tab_key, panel_id, selected in expected_live_subtabs:
            with self.subTest(live_subtab=tab_key):
                tab = opening_tag(tab_id)
                panel = opening_tag(panel_id)
                self.assertIn('type="button"', tab)
                self.assertIn('role="tab"', tab)
                self.assertIn(f'data-signal-live-tab="{tab_key}"', tab)
                self.assertIn(f'aria-controls="{panel_id}"', tab)
                self.assertIn(f'aria-selected="{str(selected).lower()}"', tab)
                self.assertIn(f'tabindex="{"0" if selected else "-1"}"', tab)
                self.assertIn('role="tabpanel"', panel)
                self.assertIn(f'aria-labelledby="{tab_id}"', panel)
                self.assertIn(f'data-signal-live-panel="{tab_key}"', panel)
                if selected:
                    self.assertNotIn(" hidden", panel)
                else:
                    self.assertIn(" hidden", panel)

        self.assertEqual(html.count('data-signal-tab="'), 4)
        self.assertEqual(html.count('data-signal-panel="'), 4)
        self.assertEqual(html.count('data-signal-live-tab="'), 4)
        self.assertEqual(html.count('data-signal-live-panel="'), 4)

    def test_ai_trade_council_overview_is_three_character_cards_without_chart_controls(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        def function_block(signature: str) -> str:
            start = main.index(signature)
            end = main.find("\nfunction ", start + len(signature))
            return main[start:end if end >= 0 else len(main)]

        agent_ids_match = re.search(
            r"const AI_TRADE_COUNCIL_AGENT_IDS = \[(.*?)\];",
            main,
            re.DOTALL,
        )
        self.assertIsNotNone(agent_ids_match, "missing AI Trade Council character roster")
        agent_ids = re.findall(r'"([a-z_]+)"', agent_ids_match.group(1))
        self.assertEqual(
            agent_ids,
            ["optimization_agent", "backtest_analyst", "codex_mcp_operator"],
        )

        agent_views = function_block("function signalAgentViews(")
        self.assertEqual(
            re.findall(r'agentId:\s*"([a-z_]+)"', agent_views),
            agent_ids,
            "the overview must resolve exactly the three council characters",
        )

        overview = function_block("function renderSignalLivePanel(report = {})")
        card = function_block("function createSignalCouncilOverviewCard(view)")
        self.assertIn("const views = signalAgentViews(report, runtime);", overview)
        self.assertIn("signal-council-overview-grid", overview)
        self.assertIn("data-signal-agent-grid", overview)
        self.assertIn(
            "views.forEach((view) => agentGrid?.appendChild(createSignalCouncilOverviewCard(view)))",
            overview,
        )
        self.assertIn("signal-council-agent-card", card)
        self.assertIn("createSignalAgentSprite(view", card)
        self.assertIn("card.dataset.workState", card)

        for forbidden_anchor in (
            "data-signal-chart",
            "signal-chart-controls",
            "data-signal-display-bars",
            "data-signal-analysis-bars",
            "data-signal-overlay",
            "data-signal-indicator-filter",
            "data-signal-core20-grid",
        ):
            with self.subTest(forbidden_overview_anchor=forbidden_anchor):
                self.assertNotIn(forbidden_anchor, overview)

        price_action = function_block("function renderSignalPriceActionDeepPanel()")
        self.assertIn('canvas.dataset.signalDeepPriceChart = "";', price_action)

        daily = function_block("function renderSignalDailyPanel(report = {})")
        self.assertIn("signal-daily-team-grid--hero", daily)
        self.assertIn(
            "team?.appendChild(createSignalCouncilOverviewCard(view));",
            daily,
            "daily refreshes must keep the same full-size council character cards",
        )
        self.assertNotIn('card.className = "signal-daily-agent";', daily)

        analyze = function_block("async function runAiTradeCouncilAnalysis(snapshotId = \"\")")
        self.assertNotIn(
            'state.modal.signalTab = "decision_pipeline";',
            analyze,
            "analysis must preserve the tab selected by the user",
        )

    def test_ai_trade_council_top_and_live_subtabs_have_keyboard_and_aria_state_hooks(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "function setSignalConsensusTab(",
            main,
            "AI Trade Council nested tabs need a dedicated state synchronizer",
        )
        tab_state_start = main.index("function setSignalConsensusTab(")
        tab_state_end = main.find("\nfunction ", tab_state_start + 1)
        tab_state_block = main[tab_state_start:tab_state_end if tab_state_end >= 0 else len(main)]
        self.assertIn('setAttribute("aria-selected"', tab_state_block)
        self.assertIn(".tabIndex =", tab_state_block)
        self.assertIn(".hidden =", tab_state_block)
        self.assertIn(".classList.toggle(", tab_state_block)
        self.assertIn(".focus()", tab_state_block)

        keyboard_match = re.search(
            r'els\.signalConsensusTabs\??\.addEventListener\("keydown"',
            main,
        )
        self.assertIsNotNone(keyboard_match, "AI Trade Council tablist needs its own keyboard handler")
        keyboard_block = main[keyboard_match.start():keyboard_match.start() + 2600]
        for key in ("ArrowLeft", "ArrowRight", "Home", "End"):
            with self.subTest(key=key):
                self.assertIn(f'"{key}"', keyboard_block)
        self.assertIn("event.preventDefault()", keyboard_block)
        self.assertIn("setSignalConsensusTab(", keyboard_block)
        self.assertIn("{ focus: true }", keyboard_block)

        click_match = re.search(
            r'els\.signalConsensusTabs\??\.addEventListener\("click"',
            main,
        )
        self.assertIsNotNone(click_match, "AI Trade Council tabs need a click handler")

        self.assertIn(
            "function setSignalLiveAnalysisTab(",
            main,
            "Live Analysis sub-tabs need a dedicated state synchronizer",
        )
        live_state_start = main.index("function setSignalLiveAnalysisTab(")
        live_state_end = main.find("\nfunction ", live_state_start + 1)
        live_state_block = main[
            live_state_start:live_state_end if live_state_end >= 0 else len(main)
        ]
        self.assertIn('querySelectorAll("[data-signal-live-tab]")', live_state_block)
        self.assertIn('setAttribute("aria-selected"', live_state_block)
        self.assertIn(".tabIndex =", live_state_block)
        self.assertIn(".hidden =", live_state_block)
        self.assertIn(".classList.toggle(", live_state_block)
        self.assertIn(".focus()", live_state_block)

        live_keyboard_match = re.search(
            r'els\.signalConsensusLiveTabs\??\.addEventListener\("keydown"',
            main,
        )
        self.assertIsNotNone(
            live_keyboard_match,
            "Live Analysis sub-tablist needs its own keyboard handler",
        )
        live_keyboard_block = main[
            live_keyboard_match.start():live_keyboard_match.start() + 2600
        ]
        for key in ("ArrowLeft", "ArrowRight", "Home", "End"):
            with self.subTest(live_subtab_key=key):
                self.assertIn(f'"{key}"', live_keyboard_block)
        self.assertIn("event.preventDefault()", live_keyboard_block)
        self.assertIn("SIGNAL_LIVE_ANALYSIS_TABS", live_keyboard_block)
        self.assertIn("setSignalLiveAnalysisTab(", live_keyboard_block)
        self.assertIn("{ focus: true }", live_keyboard_block)

        live_click_match = re.search(
            r'els\.signalConsensusLiveTabs\??\.addEventListener\("click"',
            main,
        )
        self.assertIsNotNone(
            live_click_match,
            "Live Analysis sub-tabs need a click handler",
        )

    def test_ai_trade_council_and_auto_trading_status_routes_do_not_cross(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        orchestration = json.loads(
            (PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json")
            .read_text(encoding="utf-8")
        )
        routing_rules = orchestration["managerAutoDelegation"]["specialistRules"]
        council_rule = next(
            item for item in routing_rules
            if item["id"] == "ai_trade_council"
        )
        status_rule = next(
            item for item in routing_rules
            if item["id"] == "ea_runtime_status"
        )
        self.assertEqual(council_rule["agentId"], "manager")
        self.assertEqual(status_rule["agentId"], "vps_watch")
        self.assertEqual(council_rule["targetPropId"], "left_analytics_console")
        self.assertEqual(status_rule["targetPropId"], "left_analytics_console")
        self.assertEqual(council_rule["reportType"], "ai_trade_council_report")
        self.assertEqual(status_rule["reportType"], "auto_trading_status_report")
        self.assertIn("ai trade council", council_rule["keywords"])
        self.assertIn("auto trade status", status_rule["keywords"])
        self.assertLess(routing_rules.index(status_rule), routing_rules.index(council_rule))
        self.assertEqual(
            self.bridge.pick_target_for_task("check auto trade status and terminal status"),
            "left_analytics_console",
        )
        self.assertEqual(
            self.bridge.pick_target_for_task("ask AI Trade Council for a consensus vote"),
            "left_analytics_console",
        )

        target_start = main.index("function pickTargetForTask(")
        target_end = main.find("\nfunction ", target_start + 1)
        target_block = main[target_start:target_end if target_end >= 0 else len(main)]
        status_target = (
            'if (hasTaskKeyword(lower, taskKeywords.autoTradingStatus)) '
            'return AI_TRADE_COUNCIL_PROP_ID;'
        )
        council_target = (
            "if (hasTaskKeyword(lower, taskKeywords.autoTradeCouncil)) "
            "return AI_TRADE_COUNCIL_PROP_ID;"
        )
        self.assertIn(status_target, target_block)
        self.assertIn(council_target, target_block)
        self.assertLess(target_block.index(status_target), target_block.index(council_target))

        agent_start = main.index("function pickAgentForTask(")
        agent_end = main.find("\nfunction ", agent_start + 1)
        agent_block = main[agent_start:agent_end if agent_end >= 0 else len(main)]
        status_agent = (
            'if (hasTaskKeyword(lower, taskKeywords.autoTradingStatus)) '
            'return "vps_watch";'
        )
        council_agent = (
            'if (hasTaskKeyword(lower, taskKeywords.autoTradeCouncil)) '
            'return "manager";'
        )
        self.assertIn(status_agent, agent_block)
        self.assertIn(council_agent, agent_block)
        self.assertLess(agent_block.index(status_agent), agent_block.index(council_agent))

    def test_ai_trade_council_terminal_detection_never_claims_adapter_or_live_trading_ready(self) -> None:
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
        originals = {
            "metatrader_snapshot_read_model": self.bridge.metatrader_snapshot_read_model,
            "mt4_trade_gateway_status_read_model": self.bridge.mt4_trade_gateway_status_read_model,
        }
        try:
            self.bridge.metatrader_snapshot_read_model = lambda prop_id: (
                self.bridge._empty_metatrader_snapshot_read_model(
                    prop_id,
                    "not_selected",
                    "selected_terminal_missing",
                )
            )
            self.bridge.mt4_trade_gateway_status_read_model = lambda: (
                self.bridge._empty_mt4_trade_gateway_status(
                    status="not_selected",
                    reason_code="selected_mt4_terminal_missing",
                )
            )
            checklist = self.bridge.dashboard_connection_checklist(
                "left_analytics_console",
                bridge=fake_bridge,
                quota={"ok": True, "status": "ready", "primary": {"usedPercent": 15, "remainingPercent": 85}},
                terminals=terminals,
            )
        finally:
            for name, value in originals.items():
                setattr(self.bridge, name, value)
        items = {item["id"]: item for item in checklist["items"]}

        self.assertEqual(items["mt4_terminal"]["status"], "detected")
        self.assertEqual(items["mt5_terminal"]["status"], "detected")
        self.assertFalse(items["mt4_terminal"]["adapterReady"])
        self.assertFalse(items["mt5_terminal"]["adapterReady"])
        self.assertEqual(items["mt4_terminal"]["executionAdapterStatus"], "coming_soon")
        self.assertEqual(items["mt5_terminal"]["executionAdapterStatus"], "coming_soon")
        self.assertEqual(items["trading_state_adapter"]["status"], "not_selected")
        self.assertEqual(items["ai_trader_ensemble"]["status"], "waiting_snapshot")
        self.assertEqual(items["mt4_trade_gateway"]["status"], "not_selected")
        self.assertEqual(items["live_trading"]["status"], "disabled")
        self.assertEqual(checklist["overallStatus"], "needs_attention")
        self.assertFalse(checklist["metatraderSelection"]["adapterReady"])

        role_map = json.loads(
            (PROJECT_ROOT / "contracts" / "props" / "property-role-map.json").read_text(encoding="utf-8")
        )["properties"]
        self.assertIn("executionPolicy", role_map["left_analytics_console"])
        execution_policy = role_map["left_analytics_console"]["executionPolicy"]
        self.assertEqual(execution_policy["mode"], "guarded_trade_gateway")
        self.assertFalse(execution_policy["liveTradingEnabled"])
        self.assertEqual(execution_policy["orderSubmissionEnabled"], "ea_mode_only")
        self.assertFalse(execution_policy["frontendMayEnableExecution"])
        self.assertFalse(execution_policy["aiMaySetLotOrRisk"])
        self.assertEqual(execution_policy["fixedLotSource"], "mt4_ea_input_only")
        self.assertEqual(execution_policy["minimumAutomaticTimeframe"], "M5")
        self.assertEqual(execution_policy["defaultGatewayMode"], "shadow")

        report_contract = json.loads(
            (PROJECT_ROOT / "contracts" / "reports" / "report-contract.json").read_text(encoding="utf-8")
        )
        council_schema = report_contract["typed_report_schemas"]["prop_report"]["properties"]["aiTradeCouncil"]
        self.assertEqual(council_schema["scope"], "left_analytics_console only")
        self.assertNotIn("left_signal_cube", council_schema["scope"])
        self.assertEqual(council_schema["schemaVersion"], "ai-trade-council-v2")
        self.assertEqual(
            council_schema["tabOrder"],
            ["dailySummary", "liveAnalysis", "decisionPipeline", "history"],
        )
        for section in ("runtimeTruth", "dailySummary", "chartSnapshot", "analysisReadiness", "liveAnalysis", "decisionPipeline", "history"):
            self.assertIn(section, council_schema)
        self.assertFalse(council_schema["runtimeTruth"]["terminalDetection"]["adapterReady"])
        self.assertFalse(council_schema["runtimeTruth"]["liveTradingEnabled"])
        self.assertFalse(council_schema["runtimeTruth"]["liveOrderExecutionAvailable"])
        self.assertEqual(
            council_schema["decisionPipeline"]["sourceScope"],
            "exact_analytics_console_mission_routing",
        )
        self.assertEqual(
            council_schema["history"]["sourceScope"],
            "exact_analytics_console_linked_reports_only",
        )
        self.assertFalse(council_schema["history"]["memoryIncluded"])
        self.assertFalse(council_schema["history"]["meetingsIncluded"])
        self.assertGreaterEqual(len(council_schema["truthRules"]), 5)

        tool_contract = json.loads(
            (PROJECT_ROOT / "contracts" / "tools" / "tool-permission-contract.json").read_text(encoding="utf-8")
        )
        live_tool = next(tool for tool in tool_contract["tools"] if tool["id"] == "live_trading")
        self.assertEqual(live_tool["adapterStatus"], "disabled")
        self.assertFalse(live_tool["realExecutionAvailable"])
        self.assertFalse(live_tool["autoRunnable"])

    def test_ai_trade_council_backend_payload_is_exclusive_to_analytics_console(self) -> None:
        fake_bridge = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-29T00:00:00+00:00",
        }
        fake_checklist = {
            "overallStatus": "partial",
            "checkedAt": "2026-07-29T00:00:00Z",
            "metatraderSelection": {
                "candidates": [],
                "selectedCandidate": None,
                "adapterReady": False,
            },
            "items": [
                {"id": "mt4_terminal", "status": "not_found"},
                {"id": "mt5_terminal", "status": "not_found"},
                {"id": "trading_state_adapter", "status": "coming_soon", "adapterStatus": "coming_soon"},
                {"id": "ai_trader_ensemble", "status": "coming_soon", "adapterStatus": "coming_soon"},
                {"id": "risk_policy", "status": "ready", "adapterStatus": "implemented"},
                {"id": "live_trading", "status": "disabled", "adapterStatus": "disabled"},
            ],
        }
        reports = [
            {
                "id": "report-analytics-council",
                "type": "auto_trading_status_report",
                "title": "Analytics Council report",
                "summary": "Read-only analytics result",
                "status": "ready",
                "linkedPropId": "left_analytics_console",
            },
            {
                "id": "report-signal-cube",
                "type": "auto_trading_status_report",
                "title": "Signal cube report",
                "summary": "Must not enter Council history",
                "status": "ready",
                "linkedPropId": "left_signal_cube",
            },
        ]
        runtime_sandbox = tempfile.TemporaryDirectory()
        self.addCleanup(runtime_sandbox.cleanup)
        isolated_runtime = Path(runtime_sandbox.name) / "runtime"
        originals = {
            "RUNTIME_DIR": self.bridge.RUNTIME_DIR,
            "AUDIT_PATH": self.bridge.AUDIT_PATH,
            "load_missions": self.bridge.load_missions,
            "load_agent_events": self.bridge.load_agent_events,
            "load_runtime_reports": self.bridge.load_runtime_reports,
            "load_meeting_records": self.bridge.load_meeting_records,
            "search_memory_items": self.bridge.search_memory_items,
            "bridge_status": self.bridge.bridge_status,
            "capability_registry": self.bridge.capability_registry,
            "dashboard_connection_checklist": self.bridge.dashboard_connection_checklist,
            "metatrader_snapshot_read_model": self.bridge.metatrader_snapshot_read_model,
            "mt4_trade_gateway_status_read_model": self.bridge.mt4_trade_gateway_status_read_model,
            "load_ai_trade_council_automation_store": self.bridge.load_ai_trade_council_automation_store,
        }
        try:
            self.bridge.RUNTIME_DIR = isolated_runtime
            self.bridge.AUDIT_PATH = isolated_runtime / "bridge-audit.jsonl"
            self.bridge.load_missions = lambda: []
            self.bridge.load_agent_events = lambda limit=120: []
            self.bridge.load_runtime_reports = lambda limit=120: reports
            self.bridge.load_meeting_records = lambda limit=120: []
            self.bridge.search_memory_items = lambda query="", limit=6: []
            self.bridge.bridge_status = lambda: fake_bridge
            self.bridge.capability_registry = lambda status: {
                "bridge": status,
                "capabilities": [],
            }
            self.bridge.dashboard_connection_checklist = (
                lambda prop_id, bridge=None: fake_checklist
            )
            self.bridge.metatrader_snapshot_read_model = lambda prop_id: (
                self.bridge._empty_metatrader_snapshot_read_model(
                    prop_id,
                    "not_selected",
                    "selected_terminal_missing",
                )
            )
            self.bridge.mt4_trade_gateway_status_read_model = lambda: (
                self.bridge._empty_mt4_trade_gateway_status(
                    status="not_selected",
                    reason_code="selected_mt4_terminal_missing",
                )
            )
            self.bridge.load_ai_trade_council_automation_store = (
                lambda: self.bridge._ai_trade_council_automation_default_store()
            )

            analytics_report = self.bridge.prop_report("left_analytics_console")
            signal_cube_report = self.bridge.prop_report("left_signal_cube")
        finally:
            for name, value in originals.items():
                setattr(self.bridge, name, value)

        self.assertIn("aiTradeCouncil", analytics_report)
        self.assertNotIn("aiTradeCouncil", signal_cube_report)
        council = analytics_report["aiTradeCouncil"]
        self.assertEqual(council["schemaVersion"], "ai-trade-council-v2")
        self.assertEqual(
            set(council),
            {
                "schemaVersion",
                "tabOrder",
                "runtimeTruth",
                "dailySummary",
                "chartSnapshot",
                "analysisReadiness",
                "autoAnalysis",
                "tradeGateway",
                "liveAnalysis",
                "decisionPipeline",
                "history",
            },
        )
        runtime_truth = council["runtimeTruth"]
        self.assertEqual(runtime_truth["scope"], "terminal_detection_only")
        self.assertFalse(runtime_truth["terminalDetection"]["adapterReady"])
        self.assertEqual(council["liveAnalysis"]["dataScope"], "terminal_detection_only")
        self.assertFalse(council["tradeGateway"]["connected"])
        self.assertFalse(runtime_truth["tradingStateAdapter"]["available"])
        self.assertEqual(runtime_truth["tradingStateAdapter"]["status"], "not_selected")
        self.assertFalse(runtime_truth["ensemble"]["available"])
        self.assertEqual(runtime_truth["ensemble"]["status"], "coming_soon")
        self.assertFalse(runtime_truth["tradingKillSwitchAvailable"])
        self.assertFalse(runtime_truth["liveTradingEnabled"])
        self.assertEqual(
            runtime_truth["liveTradingStatus"],
            "selected_mt4_terminal_missing",
        )
        self.assertFalse(runtime_truth["liveOrderExecutionAvailable"])
        automation = council["autoAnalysis"]
        self.assertEqual(
            automation["config"]["triggerMode"],
            "last_closed_candle_time_change",
        )
        self.assertEqual(automation["config"]["pollSeconds"], 5)
        self.assertEqual(automation["config"]["settleSeconds"], 10)
        self.assertFalse(automation["config"]["enabled"])

        live_analysis = council["liveAnalysis"]
        self.assertFalse(live_analysis["available"])
        self.assertEqual(live_analysis["status"], "not_selected")
        self.assertEqual(
            live_analysis["positionsSummary"],
            {
                "available": False,
                "count": None,
                "items": None,
                "reasonCode": "selected_terminal_missing",
            },
        )
        self.assertFalse(live_analysis["latestSignal"]["available"])
        self.assertIsNone(live_analysis["latestSignal"]["direction"])
        self.assertFalse(live_analysis["consensus"]["available"])
        self.assertIsNone(live_analysis["consensus"]["decision"])
        self.assertFalse(council["history"]["memoryIncluded"])
        self.assertFalse(council["history"]["meetingsIncluded"])
        self.assertEqual(
            council["decisionPipeline"]["sourceScope"],
            "exact_analytics_console_mission_routing",
        )
        self.assertEqual(
            council["history"]["sourceScope"],
            "exact_analytics_console_linked_reports_only",
        )
        council_history_ids = {
            item["id"] for item in council["history"]["items"]
        }
        self.assertEqual(council_history_ids, {"report-analytics-council"})
        self.assertNotIn("report-signal-cube", council_history_ids)

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
                    self.assertIn(
                        item["adapterStatus"],
                        {
                            "implemented",
                            "implemented_read_only_snapshot",
                            "implemented_unified_ea_snapshot",
                            "implemented_guarded_manual",
                            "implemented_guarded_closed_bar",
                            "source_ready_requires_ea_install",
                            "implemented_in_trade_gateway",
                            "ea_local_arm_required",
                            "runtime_detected",
                            "coming_soon",
                            "disabled",
                        },
                    )
                    if item["adapterStatus"] in {"coming_soon", "disabled"}:
                        self.assertNotEqual(item["adapterStatus"], "implemented")

        self.assertTrue({"partial", "needs_attention"}.issubset(set(contract["statusVocabulary"])))
        mt_any_of_dashboards = {"right_server_racks", "right_tool_console", "left_analytics_console"}
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
        self.assertEqual(rules["optimization_review"]["targetPropId"], "right_tool_console")
        self.assertEqual(rules["vps_status"]["targetPropId"], "right_status_crystals")
        self.assertEqual(agent_map["optimization_agent"]["visual"]["default_target"], "right_tool_console")
        self.assertEqual(agent_map["vps_watch"]["visual"]["default_target"], "right_status_crystals")
        self.assertIn("left_analytics_console", reports["backtest_report"])
        self.assertIn("right_tool_console", reports["optimization_report"])
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
            "optimization_agent": "right_tool_console",
            "vps_watch": "right_status_crystals",
            "telegram_ops": "mission_strategy_table",
            "risk_guard": "mission_strategy_table",
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
            [
                "ea_build_report",
                "ea_compile_report",
                "code_change_report",
                "trading_system_research_report",
                "trading_system_discovery_report",
                "dashboard_connection_report",
                "terminal_discovery_report",
                "terminal_selection_report",
            ],
        )
        self.assertEqual(
            role_map["right_tool_console"]["acceptedReportTypes"],
            [
                "ea_experiment_report",
                "backtest_report",
                "optimization_report",
                "ea_discovery_report",
                "ea_build_report",
                "ea_compile_report",
                "dashboard_connection_report",
                "terminal_discovery_report",
                "terminal_selection_report",
            ],
        )
        self.assertEqual(
            role_map["left_analytics_console"]["acceptedReportTypes"],
            [
                "ai_trade_council_report",
                "auto_trading_status_report",
                "backtest_report",
                "backtest_optimization_report",
                "dashboard_connection_report",
                "terminal_discovery_report",
                "terminal_selection_report",
            ],
        )

    def test_terminal_target_selection_contract_is_fail_closed_and_frontend_safe(self) -> None:
        contracts = PROJECT_ROOT / "contracts"
        connection_contract = json.loads(DASHBOARD_CONNECTION_PATH.read_text(encoding="utf-8"))
        tool_contract = json.loads((contracts / "tools" / "tool-permission-contract.json").read_text(encoding="utf-8"))
        report_contract = json.loads((contracts / "reports" / "report-contract.json").read_text(encoding="utf-8"))
        role_map = json.loads((contracts / "props" / "property-role-map.json").read_text(encoding="utf-8"))["properties"]
        bridge_contract = json.loads((contracts / "bridge" / "bridge-contract.json").read_text(encoding="utf-8"))

        expected_props = {"right_server_racks", "right_tool_console", "left_analytics_console"}
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
        channel_ui = selection["eaSnapshotChannelUi"]
        self.assertEqual(
            channel_ui["sourcePriority"],
            [
                "metatraderReadOnly.installPreparation.snapshotChannel",
                "aiTradeCouncil.tradeGateway.selectedCandidateId",
                "metatraderReadOnly.selectedCandidateId",
                "connectionChecklist.metatraderSelection.selectedCandidate.candidateId",
            ],
        )
        self.assertEqual(channel_ui["requiredPrefix"], "mtc-")
        self.assertEqual(channel_ui["displayWhen"], "channel_available_or_missing_guidance")
        self.assertTrue(channel_ui["displayIndependentOfSnapshotAvailability"])
        self.assertTrue(channel_ui["copyAction"])
        self.assertFalse(channel_ui["httpPortIsChannel"])

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

    def test_visual_routing_matches_builder_experiment_and_vps_contracts(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        optimization_start = main.index('id: "optimization_agent"')
        vps_start = main.index('id: "vps_watch"', optimization_start)
        telegram_start = main.index('id: "telegram_ops"', vps_start)
        optimization_block = main[optimization_start:vps_start]
        vps_block = main[vps_start:telegram_start]
        target_start = main.index("function pickTargetForTask(text)")
        target_end = main.index("\nfunction pickAgentForTask(text)", target_start)
        target_block = main[target_start:target_end]

        self.assertIn('right_server_racks: "โรงงานสร้าง EA และ Indicator"', main)
        self.assertIn('right_tool_console: "ห้องทดลอง EA"', main)
        self.assertIn('terminal_workstation: "EA Development Studio"', main)
        self.assertIn('left_audit_crystals: "Indicator Scout"', main)
        self.assertIn('left_signal_cube: "ข่าวรายวันและแนวโน้ม Forex"', main)
        self.assertIn('right_status_crystals: "สถานะ VPS/HQ และตั้งค่า Agent"', main)
        self.assertIn('defaultTarget: "right_tool_console"', optimization_block)
        self.assertIn('homeTarget: "right_tool_console"', optimization_block)
        self.assertIn('defaultTarget: "right_status_crystals"', vps_block)
        self.assertIn('homeTarget: "right_status_crystals"', vps_block)
        self.assertIn('taskKeywords.optimization)) return "right_tool_console"', target_block)
        self.assertIn('taskKeywords.eaBuild)) return "right_server_racks"', target_block)
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
                    self.bridge.select_metatrader_target("right_tool_console", candidate["candidateId"]),
                ]

                for result, prop_id in zip(results, ("right_server_racks", "right_tool_console")):
                    self.assertTrue(result["ok"])
                    self.assertEqual(result["status"], "completed")
                    self.assertEqual(result["selection"]["propId"], prop_id)
                    self.assertEqual(result["selection"]["status"], "selected")
                    self.assertEqual(result["selection"]["configurationStatus"], "configured")
                    self.assertEqual(result["selection"]["adapterConnection"], "read_only_snapshot")
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
                    self.assertEqual(selected_item["executionAdapterStatus"], "read_only_snapshot")
                    self.assertFalse(selected_item["adapterReady"])

                persisted = json.loads((runtime / self.bridge.METATRADER_TARGET_STORE_FILENAME).read_text(encoding="utf-8"))
                self.assertEqual(set(persisted["selections"]), {"right_server_racks", "right_tool_console"})
                self.assertEqual(persisted["selections"]["right_server_racks"]["candidateId"], candidate["candidateId"])
                self.assertEqual(persisted["selections"]["right_tool_console"]["candidateId"], candidate["candidateId"])

                missions = self.bridge.load_missions()
                self.assertEqual(len(missions), 2)
                self.assertTrue(all(mission["toolId"] == "terminal_target_select" for mission in missions))
                self.assertTrue(all(mission["status"] == "completed" for mission in missions))
                reports = [report for report in self.bridge.load_runtime_reports() if report["type"] == "terminal_selection_report"]
                self.assertEqual({report["linkedPropId"] for report in reports}, {"right_server_racks", "right_tool_console"})
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH)
                selected_events = [item for item in audit if item.get("type") == "terminal.target_selected"]
                self.assertEqual({item["dashboardId"] for item in selected_events}, {"right_server_racks", "right_tool_console"})
                self.assertTrue(all(item["adapterConnection"] == "read_only_snapshot" and item["adapterReady"] is False for item in selected_events))

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
        self.assertEqual(items["metaeditor_compile_adapter"]["status"], "coming_soon")
        self.assertEqual(checklist["connectionRequirements"]["anyOf"], ["mt4_terminal", "mt5_terminal"])
        self.assertTrue(checklist["connectionRequirements"]["anyOfSatisfied"])
        self.assertEqual(checklist["overallStatus"], "partial")
        self.assertEqual(checklist["operationMode"]["aiEveryTwoHours"]["status"], "not_required")
        self.assertFalse(checklist["operationMode"]["aiEveryTwoHours"]["enabled"])

        experiment_checklist = self.bridge.dashboard_connection_checklist(
            "right_tool_console",
            bridge=fake_bridge,
            quota={"ok": True, "status": "ready", "primary": {"usedPercent": 15, "remainingPercent": 85}},
            terminals=terminals,
        )
        experiment_items = {item["id"]: item for item in experiment_checklist["items"]}
        self.assertEqual(experiment_items["optimization_adapter"]["status"], "coming_soon")
        self.assertEqual(experiment_items["strategy_tester_adapter"]["status"], "coming_soon")

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
                result = self.bridge.run_metatrader_discovery("right_server_racks")
                self.assertTrue(result["ok"])
                self.assertEqual(result["status"], "completed")
                self.assertTrue(result["missionId"].startswith("mission-"))
                missions = self.bridge.load_missions()
                mission = next(item for item in missions if item["id"] == result["missionId"])
                self.assertEqual(mission["toolId"], "terminal_discovery")
                self.assertEqual(mission["status"], "completed")
                reports = self.bridge.load_runtime_reports()
                report = next(item for item in reports if item["linkedMissionId"] == mission["id"])
                self.assertEqual(report["linkedPropId"], "right_server_racks")
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
                lambda: self.bridge.run_metatrader_discovery("right_server_racks"),
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

    def test_equipment_dashboard_keeps_connections_left_and_work_results_in_three_columns(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")

        connection_rail_start = html.index('id="modalDashboardConnectionRail"')
        portrait_panel_end = html.index("</aside>", connection_rail_start)
        dashboard_workspace_start = html.index('id="modalDashboardPanel"')
        self.assertLess(connection_rail_start, portrait_panel_end)
        self.assertLess(portrait_panel_end, dashboard_workspace_start)
        self.assertNotIn('data-tab="connections"', html)
        self.assertNotIn('data-tab="results" data-surfaces="dashboard"', html)

        for element_id in (
            "modalDashboardConnectionRail",
            "modalDashboardWorkCount",
            "modalDashboardFreshness",
            "modalDashboardRunningCount",
            "modalDashboardCompletedCount",
            "modalDashboardBlockedCount",
            "modalDashboardRunning",
            "modalDashboardCompleted",
            "modalDashboardBlocked",
        ):
            self.assertIn(f'id="{element_id}"', html)
            self.assertIn(f'document.getElementById("{element_id}")', main)

        self.assertEqual(html.count('class="dashboard-work-column"'), 3)
        for state in ("running", "completed", "blocked"):
            self.assertIn(f'data-state="{state}"', html)
        self.assertIn("function renderDashboardWorkColumn(", main)
        self.assertIn("function createDashboardReportCard(", main)
        self.assertIn("function openDashboardResultDetail(", main)
        self.assertIn("function appendDashboardMetricSection(", main)
        self.assertIn("function appendDashboardVisualEvidence(", main)
        work_state_start = main.index("function getDashboardWorkState(")
        work_state_end = main.index("\nfunction getDashboardItemTime(", work_state_start)
        work_state_block = main[work_state_start:work_state_end]
        self.assertIn('["completed", "archived", "ready", "published"]', work_state_block)
        self.assertIn(
            '["waiting_approval", "needs_approval", "blocked", "failed", "error"]',
            work_state_block,
        )
        self.assertIn('return "blocked"', work_state_block)
        safe_url_start = main.index("function getSafeReportImageUrl(")
        safe_url_end = main.index("\nfunction appendDashboardVisualEvidence(", safe_url_start)
        safe_url_block = main[safe_url_start:safe_url_end]
        self.assertIn("parsed.origin !== window.location.origin", safe_url_block)
        self.assertIn(r"\/api\/reports\/", safe_url_block)
        self.assertIn(r"\/attachments\/", safe_url_block)
        self.assertNotIn(r"\/evidence\/", safe_url_block)

    def test_scrollable_agent_and_dashboard_cards_keep_natural_height(self) -> None:
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        def css_rule(selector: str) -> str:
            start = styles.index(f"{selector} {{")
            end = styles.index("\n}", start)
            return styles[start:end]

        agent_list_rule = css_rule(".agent-status-list")
        self.assertIn("flex: 1 1 0;", agent_list_rule)
        self.assertIn("grid-auto-rows: max-content;", agent_list_rule)
        self.assertIn("align-content: start;", agent_list_rule)
        self.assertIn("overflow-y: auto;", agent_list_rule)
        self.assertIn("scrollbar-gutter: stable;", agent_list_rule)

        agent_actions_rule = css_rule(".agent-status-actions button")
        self.assertIn("min-height: 34px;", agent_actions_rule)
        self.assertIn("white-space: normal;", agent_actions_rule)
        self.assertNotIn("white-space: nowrap;", agent_actions_rule)

        dashboard_list_rule = css_rule(".dashboard-work-column > .dashboard-list")
        self.assertIn("grid-auto-rows: max-content;", dashboard_list_rule)
        self.assertIn("align-content: start;", dashboard_list_rule)
        self.assertIn("overflow-y: auto;", dashboard_list_rule)
        self.assertIn("scrollbar-gutter: stable;", dashboard_list_rule)

        dashboard_heading_rule = css_rule(".dashboard-workspace-heading")
        self.assertIn("padding: 2px 52px 12px 2px;", dashboard_heading_rule)
        self.assertIn("min-width: 0;", dashboard_heading_rule)

        report_title_rule = css_rule(".dashboard-report-card > strong")
        self.assertIn("-webkit-line-clamp: 2;", report_title_rule)
        report_summary_rule = css_rule(
            ".dashboard-report-card > span:not(.dashboard-report-card-topline):not(.dashboard-report-card-footer)"
        )
        self.assertIn("-webkit-line-clamp: 3;", report_summary_rule)

        compact = styles[styles.index("@media (max-width: 900px)"):]
        self.assertIn(".game-modal.dashboard-modal .game-modal-body", compact)
        self.assertIn("grid-template-columns: minmax(0, 1fr);", compact)
        self.assertIn("grid-template-rows: minmax(180px, 34%) minmax(0, 1fr);", compact)
        self.assertIn("grid-template-columns: repeat(3, minmax(260px, 80vw));", compact)

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

        render_start = main.index("function renderMetatraderSelection(subject, checklist, canDiscoverMetatrader, report = null)")
        render_end = main.index("\nfunction renderDashboardConnectionPanel", render_start)
        render_block = main[render_start:render_end]
        self.assertIn("hidden = !canDiscoverMetatrader", render_block)
        self.assertIn("modalDashboardConfirmMetatrader.disabled", render_block)
        self.assertIn("gatewayConnected && snapshotConnected", render_block)
        self.assertIn("EA Gateway และข้อมูล Snapshot ของ Terminal นี้เชื่อมกับ Local Runner แล้ว", render_block)

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
        self.assertIn("Array.isArray(report?.reports)", main)
        self.assertIn("memoryCardsToMissionItems", main)
        self.assertIn("getDashboardWorkState(item, kind)", main)
        self.assertIn("createDashboardReportCard(item)", main)
        self.assertIn("item.attachments", main)
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

    def test_topbar_keeps_only_the_full_access_control(self) -> None:
        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        self.assertIn('id="operatorModeControl"', html)
        self.assertIn('id="operatorModeButton"', html)
        self.assertIn('id="operatorModePanel"', html)
        self.assertIn('? "Full Access"', main)
        self.assertIn('"เปิด Full Access"', main)

        self.assertIn("@media (min-width: 1181px)", styles)
        self.assertIn("right: calc(100% + 12px);", styles)
        self.assertIn(
            '.app-shell:has(.operator-mode-button[aria-expanded="true"]) .today-work-panel',
            styles,
        )

        for removed_id in (
            "fitModeButton",
            "agentRouteButton",
            "agentMeetingButton",
            "resetButton",
        ):
            self.assertNotIn(f'id="{removed_id}"', html)
            self.assertNotIn(f'document.getElementById("{removed_id}")', main)
            self.assertNotIn(f"els.{removed_id}.addEventListener", main)

    def test_topbar_popovers_stay_above_the_depth_sorted_room(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

        def css_integer(variable: str) -> int:
            match = re.search(rf"{re.escape(variable)}:\s*(\d+);", styles)
            self.assertIsNotNone(match, f"Missing CSS layer variable: {variable}")
            return int(match.group(1))

        def css_block(selector: str) -> str:
            start = styles.index(f"{selector} {{")
            return styles[start:styles.index("}", start) + 1]

        scene_layer = css_integer("--z-office-scene")
        topbar_layer = css_integer("--z-office-topbar")
        popover_layer = css_integer("--z-office-popover")
        modal_backdrop_layer = css_integer("--z-office-modal-backdrop")

        self.assertLess(scene_layer, topbar_layer)
        self.assertGreaterEqual(popover_layer, topbar_layer)
        self.assertLess(popover_layer, modal_backdrop_layer)
        self.assertIn("return Math.round(clamp(y, 0, 100) * 10);", main)

        stage_block = css_block(".stage-wrap")
        self.assertIn("z-index: var(--z-office-scene);", stage_block)
        self.assertIn("isolation: isolate;", stage_block)

        topbar_block = css_block(".topbar")
        self.assertIn("z-index: var(--z-office-topbar);", topbar_block)
        self.assertIn("overflow: visible;", topbar_block)

        for selector in (".agent-collab-panel", ".operator-mode-panel"):
            with self.subTest(selector=selector):
                panel_block = css_block(selector)
                self.assertIn("z-index: var(--z-office-popover);", panel_block)
                self.assertIn("pointer-events: auto;", panel_block)

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
        self.assertIn("getActiveMissionForAgent(agent.id)", status_block)
        active_block = function_block("getActiveMissionForAgent")
        for outstanding_status in ("running", "waiting_approval", "queued", "blocked", "failed"):
            self.assertIn(f"{outstanding_status}:", active_block)
        self.assertNotIn("taskLabelByStatus", status_block)
        self.assertIn("missionStatus", status_block)
        self.assertIn('key: "busy"', status_block)
        self.assertRegex(status_block, r'return\s*\{\s*key:\s*"busy"')
        self.assertIn('state.bridge.status === "Backend ออฟไลน์"', status_block)
        self.assertNotIn("if (!state.bridge.apiOnline)", status_block)
        self.assertLess(
            status_block.index('key: "unavailable"'),
            status_block.index("if (mission)"),
            "Confirmed runtime unavailability must be evaluated independently from Mission status.",
        )
        self.assertIn("getAgentStatusPriorityOrder(state.officeAgents)", render_block)
        self.assertIn("createAgentStatusCard(agent)", render_block)
        self.assertNotIn(".slice(", render_block)
        priority_start = main.index("const AGENT_STATUS_PRIORITY = Object.freeze([")
        priority_end = main.index("]);", priority_start)
        priority_block = main[priority_start:priority_end]
        self.assertLess(priority_block.index('"ceo"'), priority_block.index('"manager"'))

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
        self.assertIn("isMissionCompletedToday(mission, now)", today_panel)
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
        # nine equipment dashboards, Mission Kanban, or shared detail dialogs.
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
        self.assertIn('dashboard: ["results"]', main)
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

        dashboard_panel_start = styles.index(".game-modal.dashboard-modal #modalDashboardPanel.active")
        dashboard_panel_end = styles.index("\n}", dashboard_panel_start)
        dashboard_panel_rule = styles[dashboard_panel_start:dashboard_panel_end]
        self.assertIn("grid-template-rows: minmax(0, 1fr);", dashboard_panel_rule)
        self.assertIn("overflow: hidden;", dashboard_panel_rule)
        self.assertIn(".game-modal.dashboard-modal .game-modal-body", styles)
        self.assertIn("grid-template-columns: 370px minmax(0, 1fr);", styles)
        self.assertIn(".dashboard-report-workspace", styles)
        self.assertIn("grid-template-rows: auto auto minmax(0, 1fr);", styles)
        self.assertIn(".dashboard-work-columns", styles)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr));", styles)
        self.assertIn(".dashboard-result-dialog", styles)
        self.assertIn("width: min(1180px, calc(100vw - 40px));", styles)
        mobile = styles[styles.index("@media (max-width: 720px)"):]
        self.assertIn(".game-modal.dashboard-modal .game-modal-body", mobile)
        self.assertIn("grid-template-rows: minmax(0, 44%) minmax(0, 1fr);", mobile)
        self.assertIn("grid-template-columns: repeat(3, minmax(250px, 82vw));", mobile)
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

    def test_task_and_dashboard_report_details_use_safe_structured_renderers(self) -> None:
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
        self.assertTrue(
            "renderTaskList(" in kanban_block or "createTaskCard(" in kanban_block,
            "Kanban must use the same task-card renderer as the Agent and Current Work surfaces.",
        )
        for destination in (
            "els.modalDashboardRunning",
            "els.modalDashboardCompleted",
            "els.modalDashboardBlocked",
        ):
            self.assertIn(f"renderDashboardWorkColumn(\n    {destination}", prop_dashboard_block)
        self.assertIn("renderDashboardConnectionPanel(subject, propertyRole)", prop_dashboard_block)
        self.assertNotIn("renderStatusGrid(", prop_dashboard_block)
        self.assertIn("els.modalDashboardConnectionRail.hidden = surface !== \"dashboard\"", modal_block)
        self.assertIn("els.modalStatusGrid.hidden = surface === \"dashboard\"", modal_block)

        report_card_block = function_block("createDashboardReportCard")
        self.assertIn('document.createElement("button")', report_card_block)
        self.assertIn('card.setAttribute("aria-haspopup", "dialog")', report_card_block)
        self.assertIn("openDashboardResultDetail(report, card)", report_card_block)
        self.assertIn("report.attachments", report_card_block)

        dashboard_detail_block = function_block("openDashboardResultDetail")
        for structured_field in ("item.metrics", "item.findings", "item.risks", "item.nextActions"):
            self.assertIn(structured_field, dashboard_detail_block)
        self.assertIn("item.attachments", dashboard_detail_block)
        self.assertIn("item.evidence", dashboard_detail_block)
        self.assertNotIn("JSON.stringify(item", dashboard_detail_block)

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
        self.assertEqual(self.bridge.BRIDGE_RUNTIME_VERSION, "0.9.2")
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

    def test_runner_status_does_not_false_block_guarded_exec_on_login_probe(self) -> None:
        original_bin = self.runner.CODEX_BIN
        original_command = self.runner.run_command

        def fake_command(command, timeout=30, stdin=None):
            if command[-1] == "--version":
                return {
                    "ok": True,
                    "exitCode": 0,
                    "stdout": "codex-cli 0.test",
                    "stderr": "",
                    "durationMs": 1,
                }
            return {
                "ok": False,
                "exitCode": 1,
                "stdout": "Not logged in",
                "stderr": "",
                "durationMs": 1,
            }

        try:
            self.runner.CODEX_BIN = RUNNER_PATH
            self.runner.run_command = fake_command
            status = self.runner.status()
        finally:
            self.runner.CODEX_BIN = original_bin
            self.runner.run_command = original_command

        self.assertTrue(status["ok"])
        self.assertEqual(status["status"], "ready_guarded")
        self.assertFalse(status["authChecked"])

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
        original_reports_dir = self.bridge.RUNTIME_REPORTS_DIR
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
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
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
                self.bridge.RUNTIME_REPORTS_DIR = original_reports_dir
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

    def test_bridge_autostart_is_explicit_reversible_and_reuses_confirmed_loopback_endpoint(self) -> None:
        register = AUTOSTART_REGISTER_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        unregister = AUTOSTART_UNREGISTER_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        lifecycle = LIFECYCLE_SCRIPT_PATH.read_text(encoding="utf-8-sig")

        self.assertIn('"data\\runtime\\bridge-endpoint.json"', register)
        self.assertIn('[string]$endpoint.host -cne "127.0.0.1"', register)
        self.assertIn('-WindowStyle Hidden', register)
        self.assertIn('-File "{0}" -Action Ensure -Port {1}', register)
        self.assertIn('-Action Ensure `', register)
        self.assertIn('-Port $confirmedPort', register)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn", register)
        self.assertIn("-RepetitionInterval (New-TimeSpan -Minutes $WatchdogMinutes)", register)
        self.assertIn("-RestartCount 3", register)
        self.assertIn("-MultipleInstances IgnoreNew", register)
        self.assertIn("Register-ScheduledTask", register)
        self.assertIn("Export-ScheduledTask", register)
        self.assertIn("ย้อนกลับ Task เดิมแล้ว", register)
        self.assertNotIn("Start-Process", register)
        self.assertNotIn("CreateShortcut", register)
        self.assertNotIn("http://127.0.0.1:$confirmedPort/\"", register.split("$arguments", 1)[0])
        self.assertIn('[ValidateSet("Start", "Ensure", "Status", "Stop", "Restart")]', lifecycle)
        self.assertIn('function Ensure-Bridge', lifecycle)
        self.assertIn('verified_unhealthy_restarting', lifecycle)
        self.assertIn('Stop-VerifiedProcess -ProcessId $existingId', lifecycle)
        self.assertIn('$Operation -in @("start", "ensure") -and $requestedBridgePort -ge 1024) {', lifecycle)
        self.assertIn("Unregister-ScheduledTask", unregister)
        self.assertIn('"Metafxclub AI Agent HQ Bridge.lnk"', unregister)
        self.assertIn("Remove-Item -LiteralPath $legacyShortcutPath -Force", unregister)

    def test_install_update_and_uninstall_coordinate_with_the_bridge_watchdog(self) -> None:
        installer = INSTALLER_SCRIPT_PATH.read_text(encoding="utf-8-sig")
        uninstaller = UNINSTALL_SCRIPT_PATH.read_text(encoding="utf-8-sig")

        self.assertIn('function Suspend-BridgeScheduledTask', installer)
        self.assertIn('Disable-ScheduledTask -TaskName $bridgeTaskName', installer)
        self.assertIn('Stop-ScheduledTask -TaskName $bridgeTaskName', installer)
        self.assertIn('$bridgeTaskWasEnabled = Suspend-BridgeScheduledTask', installer)
        self.assertIn('Rebind-BridgeScheduledTask -ConfirmedPort $selectedBridgePort', installer)
        self.assertIn('$expectedArgument = "-Action Ensure -Port $ConfirmedPort"', installer)
        self.assertIn('ผูก Watchdog ใหม่ไม่สำเร็จและคืน Task เดิมแล้ว', installer)
        self.assertIn('การติดตั้งแบบ SkipLaunch ต้องใช้พอร์ตเดิม', installer)
        self.assertIn('finally {\n        Restore-BridgeScheduledTask -WasEnabled $bridgeTaskWasEnabled', installer)
        self.assertIn('Enable-ScheduledTask -TaskName $bridgeTaskName', installer)
        self.assertIn('"node_modules", ".pytest_cache", "dist", "build"', installer)
        self.assertIn('"scripts\\unregister-bridge-autostart.ps1"', uninstaller)
        self.assertIn('Unregister-ScheduledTask -TaskName $taskName', uninstaller)

    def test_student_git_updater_is_fast_forward_only_and_never_pushes_or_overwrites_dirty_source(self) -> None:
        updater = UPDATE_SCRIPT_PATH.read_text(encoding="utf-8-sig")

        self.assertIn('@("status", "--porcelain", "--untracked-files=normal")', updater)
        self.assertIn('@("fetch", "--all", "--prune")', updater)
        self.assertIn('@("merge", "--ff-only", $upstream)', updater)
        self.assertIn('"Metafxclub\\AI-Agent-HQ"', updater)
        self.assertIn("-EndpointConfirmed", updater)
        self.assertNotIn("reset --hard", updater.lower())
        self.assertNotIn("git push", updater.lower())
        self.assertNotIn("git.exe -C $projectRoot push", updater)

    def test_student_installer_copies_mt4_integrations_and_curated_gateway_build(self) -> None:
        installer = INSTALLER_SCRIPT_PATH.read_text(encoding="utf-8-sig")

        self.assertIn('"integrations\\mt4-trade-gateway\\MetafxHQTradeGateway.mq4"', installer)
        self.assertIn('"artifacts\\mt4-ai-council-ea-v2.14-broker-compat-hardening\\MetafxHQTradeGateway.ex4"', installer)
        self.assertIn('"integrations", "runner", "scripts", "tests"', installer)
        self.assertIn('Sync-Directory -DirectoryName "artifacts\\mt4-ai-council-ea-v2.14-broker-compat-hardening"', installer)
        self.assertIn('"1-INSTALL-HQ.bat", "UPDATE-HQ.bat"', installer)

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
            installer.index("Stop-ExistingBridge", main_start),
        )
        self.assertIn("-Port $ConfirmedPort", installer)
        self.assertIn("api/codex/rate-limits?refresh=true", installer)
        self.assertIn("account_identity_stored = $false", installer)
        self.assertNotIn("& $codex login", installer)

        self.assertIn("$confirmedEndpointRequired", lifecycle)
        self.assertIn("ระบบหยุดโดยไม่เปลี่ยนไปใช้ URL อื่น", lifecycle)
        self.assertIn("user_confirmed", lifecycle)
        self.assertIn("[Net.Sockets.SocketOptionName]::ReuseAddress", lifecycle)
        self.assertIn("Get-ListenerProcessIds", lifecycle)
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
        attributes = (PROJECT_ROOT / ".gitattributes").read_text(encoding="utf-8-sig")
        self.assertEqual(version, "0.9.2")
        self.assertNotRegex(registry_text, r"(?i)[a-z]:\\\\users\\\\")
        self.assertIn("*.mq4 text eol=lf", attributes)
        self.assertIn("*.mq5 text eol=lf", attributes)
        self.assertIn("*.mqh text eol=lf", attributes)

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
            original_status = self.runner.chat_status
            original_run_chat_command = self.runner.run_chat_command

            def fake_run_chat_command(command, timeout, stdin, cwd, output_limit=60000):
                raw_path = Path(command[command.index("-o") + 1])
                raw_output_paths.append(raw_path)
                self.assertNotEqual(raw_path.parent.resolve(), run_directory.resolve())
                raw_path.write_text(
                    json.dumps({
                        "status": "completed",
                        "summary": "token=supersecretvalue Safe report body",
                        "findings": ["Safe finding"],
                        "nextSteps": [],
                        "evidence": [],
                        "blockedCapability": "",
                    }),
                    encoding="utf-8",
                )
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
                self.runner.chat_status = lambda: {"ok": True, "status": "runtime_ready"}
                self.runner.run_chat_command = fake_run_chat_command
                result = self.runner.run_codex("Review this report", "manager", "mission-test")
            finally:
                self.runner.CODEX_RUNS_DIR = original_runs_dir
                self.runner.chat_status = original_status
                self.runner.run_chat_command = original_run_chat_command

            self.assertTrue(result["ok"])
            self.assertTrue(result["usage"]["secretRedacted"])
            for path in run_directory.glob("*"):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("supersecretvalue", content)
            self.assertTrue(raw_output_paths)
            self.assertFalse(raw_output_paths[0].exists())

    def test_report_image_attachments_are_allowlisted_projected_and_path_opaque(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original_memory_dir = self.bridge.MEMORY_DIR
            original_runtime_dir = self.bridge.RUNTIME_DIR
            original_reports_dir = self.bridge.RUNTIME_REPORTS_DIR
            try:
                self.bridge.MEMORY_DIR = root / "memory"
                self.bridge.RUNTIME_DIR = root / "runtime"
                self.bridge.RUNTIME_REPORTS_DIR = self.bridge.RUNTIME_DIR / "reports"
                screenshot_dir = self.bridge.MEMORY_DIR / "screenshots"
                artifact_dir = self.bridge.MEMORY_DIR / "artifacts"
                codex_runs_dir = self.bridge.RUNTIME_DIR / "codex-runs"
                for path in (screenshot_dir, artifact_dir, codex_runs_dir, self.bridge.RUNTIME_REPORTS_DIR):
                    path.mkdir(parents=True, exist_ok=True)

                valid_png = screenshot_dir / "equity-proof.png"
                valid_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"safe-report-image")
                invalid_magic = screenshot_dir / "not-really-an-image.png"
                invalid_magic.write_text("plain text", encoding="utf-8")
                unsupported_svg = screenshot_dir / "unsafe.svg"
                unsupported_svg.write_text("<svg></svg>", encoding="utf-8")
                outside_root = root / "outside.png"
                outside_root.write_bytes(b"\x89PNG\r\n\x1a\n" + b"outside")

                report = {
                    "id": "report-attachment-test",
                    "title": "ผล Backtest",
                    "summary": "รายงานพร้อมรูป Equity",
                    "status": "ready",
                    "artifacts": [
                        {"storageRef": str(valid_png), "label": "Equity Curve"},
                        {"storageRef": str(invalid_magic), "label": "Wrong magic"},
                        {"storageRef": str(unsupported_svg), "label": "SVG"},
                        {"storageRef": str(outside_root), "label": "Outside allowlist"},
                        {"storageRef": str(screenshot_dir / ".." / "outside.png"), "label": "Traversal"},
                    ],
                }
                projected = self.bridge.report_read_model_item(report)
                self.assertEqual(projected["artifactCount"], 5)
                self.assertEqual(len(projected["attachments"]), 1)
                attachment = projected["attachments"][0]
                self.assertEqual(attachment["kind"], "image")
                self.assertEqual(attachment["label"], "Equity Curve")
                self.assertEqual(attachment["mediaType"], "image/png")
                self.assertRegex(
                    attachment["url"],
                    r"^/api/reports/report-attachment-test/attachments/image-[a-f0-9]{20}$",
                )
                serialized = json.dumps(projected, ensure_ascii=False)
                for forbidden_path in (str(valid_png), str(screenshot_dir), str(root)):
                    self.assertNotIn(forbidden_path, serialized)

                self.bridge.write_json(
                    self.bridge.RUNTIME_REPORTS_DIR / "report-attachment-test.json",
                    report,
                    keep_backup=False,
                )
                attachment_id = attachment["id"]
                resolved = self.bridge.resolve_report_attachment("report-attachment-test", attachment_id)
                self.assertIsNotNone(resolved)
                self.assertEqual(resolved[0], valid_png.resolve())
                self.assertEqual(resolved[1], "image/png")
                self.assertIsNone(self.bridge.resolve_report_attachment("../report", attachment_id))
                self.assertIsNone(self.bridge.resolve_report_attachment("report-attachment-test", "../image"))

                for rejected in (
                    invalid_magic,
                    unsupported_svg,
                    outside_root,
                    screenshot_dir / ".." / "outside.png",
                ):
                    with self.subTest(rejected=rejected):
                        self.assertIsNone(self.bridge.resolve_report_image_artifact(str(rejected)))
            finally:
                self.bridge.MEMORY_DIR = original_memory_dir
                self.bridge.RUNTIME_DIR = original_runtime_dir
                self.bridge.RUNTIME_REPORTS_DIR = original_reports_dir

    def test_codex_web_research_requires_a_real_search_event_and_public_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_directory = Path(directory) / "codex-runs"
            original_runs_dir = self.runner.CODEX_RUNS_DIR
            original_status = self.runner.chat_status
            original_run_chat_command = self.runner.run_chat_command
            captured_commands = []

            def fake_run_chat_command(command, timeout, stdin, cwd, output_limit=60000):
                captured_commands.append(list(command))
                raw_path = Path(command[command.index("-o") + 1])
                raw_path.write_text(
                    json.dumps({
                        "status": "completed",
                        "summary": "Web research complete",
                        "findings": ["Public source checked"],
                        "nextSteps": [],
                        "evidence": [{
                            "label": "Official source",
                            "url": "https://example.com/public",
                            "note": "Public evidence",
                        }],
                        "blockedCapability": "",
                    }),
                    encoding="utf-8",
                )
                return {
                    "ok": True,
                    "exitCode": 0,
                    "stdout": (
                        json.dumps({
                            "type": "item.completed",
                            "item": {
                                "id": "item-web-1",
                                "type": "web_search",
                                "query": "official public source",
                                "action": {"type": "search", "query": "official public source"},
                            },
                        })
                        if len(captured_commands) == 1
                        else ""
                    ),
                    "stderr": "",
                    "durationMs": 1,
                    "processStarted": True,
                    "processTreeTerminated": False,
                }

            try:
                self.runner.CODEX_RUNS_DIR = run_directory
                self.runner.chat_status = lambda: {"ok": True, "status": "runtime_ready"}
                self.runner.run_chat_command = fake_run_chat_command
                completed = self.runner.run_codex(
                    "Find a public source",
                    "ea_developer",
                    "web-research-completed",
                    web_search=True,
                )
                unverified = self.runner.run_codex(
                    "Find another public source",
                    "ea_developer",
                    "web-research-unverified",
                    web_search=True,
                )
            finally:
                self.runner.CODEX_RUNS_DIR = original_runs_dir
                self.runner.chat_status = original_status
                self.runner.run_chat_command = original_run_chat_command

            self.assertTrue(completed["ok"])
            self.assertTrue(completed["webSearchUsed"])
            self.assertTrue(completed["webSearchEvidenceVerified"])
            command = captured_commands[0]
            self.assertIn("--search", command)
            self.assertIn("--json", command)
            self.assertIn("--ask-for-approval", command)
            self.assertIn("never", command)
            self.assertIn('web_search="live"', command)
            self.assertIn('sandbox_mode="read-only"', command)
            self.assertIn("plugins", command)
            self.assertIn("computer_use", command)
            self.assertEqual(command[-1], "-")

            self.assertFalse(unverified["ok"])
            self.assertEqual(unverified["status"], "blocked")
            self.assertFalse(unverified["webSearchUsed"])
            self.assertFalse(unverified["webSearchEvidenceVerified"])
            self.assertEqual(
                unverified["blockedCapability"],
                "Native Codex Web Search verification",
            )

    def test_native_web_search_event_is_detected_before_diagnostic_truncation(self) -> None:
        event = json.dumps({
            "type": "item.completed",
            "item": {
                "id": "item-web-after-noise",
                "type": "web_search",
                "query": "XAUUSD latest market news",
                "action": {"type": "search", "query": "XAUUSD latest market news"},
            },
        })
        script = f"import sys; sys.stdout.write('x' * 50000 + '\\n' + {event!r} + '\\n')"
        result = self.runner.run_chat_command(
            [sys.executable, "-c", script],
            timeout=10,
            stdin="",
            cwd=PROJECT_ROOT,
            output_limit=40000,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["nativeWebSearchUsed"])
        self.assertEqual(result["nativeWebSearchVerificationSource"], "codex_exec_jsonl")
        self.assertNotIn("item-web-after-noise", result["stdout"])
        self.assertTrue(self.runner.native_web_search_used(result))

    def test_native_web_search_jsonl_detector_rejects_unfinished_or_model_text(self) -> None:
        unfinished = json.dumps({
            "type": "item.started",
            "item": {
                "id": "item-web-started",
                "type": "web_search",
                "query": "market news",
            },
        })
        model_text = json.dumps({
            "type": "item.completed",
            "item": {
                "id": "item-agent-message",
                "type": "agent_message",
                "text": '{"type":"item.completed","item":{"type":"web_search","query":"fake"}}',
            },
        })
        empty_query = json.dumps({
            "type": "item.completed",
            "item": {"id": "item-web-empty", "type": "web_search", "query": ""},
        })

        self.assertFalse(self.runner.native_web_search_jsonl_used(unfinished))
        self.assertFalse(self.runner.native_web_search_jsonl_used(model_text))
        self.assertFalse(self.runner.native_web_search_jsonl_used(empty_query))
        used, source = self.runner.detect_native_web_search_use(
            "",
            "web search: legacy marker without a completed JSONL event",
            structured_event_mode=True,
        )
        self.assertFalse(used)
        self.assertEqual(source, "")

    def test_news_verification_block_has_clear_thai_dashboard_guidance(self) -> None:
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        capability = '"Native Codex Web Search verification"'
        reason = "ตัวค้นข่าวทำงานแล้ว แต่ระบบหลังบ้านยังยืนยันบันทึก Web Search ไม่ได้"
        next_step = "ไม่ต้องอนุมัติงานนี้ซ้ำ ให้ตรวจการยืนยัน Web Search ของ Local Runner"
        generic = "if (mission?.blockedCapability) {"

        self.assertIn(capability, main)
        self.assertIn(reason, main)
        self.assertIn(next_step, main)
        self.assertLess(main.index(next_step), main.index(generic, main.index(next_step)))

    def test_ai_trade_council_snapshot_reference_is_relative_to_workspace_root(self) -> None:
        snapshot_id = "a" * 64
        snapshot_model = {
            "dailySummary": {
                "available": True,
                "serverDay": "2026-07-29",
                "profit": 12.5,
            },
            "chartSnapshot": {
                "available": True,
                "status": "fresh",
                "snapshotId": snapshot_id,
                "observedAt": "2026-07-29T02:00:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "bid": 2400.0,
                "ask": 2400.2,
                "spreadPoints": 20,
                "barCount": 1,
                "bars": [{"time": "2026-07-29T00:00:00Z", "close": 2400.0}],
            },
        }
        original_workspace = self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR
        original_snapshot_dir = self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR
        with tempfile.TemporaryDirectory() as directory:
            try:
                workspace = Path(directory) / "workspace"
                self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = workspace
                self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = (
                    workspace / "ai-trade-council" / "snapshots"
                )
                reference = self.bridge._write_ai_trade_council_snapshot_artifact(
                    snapshot_model
                )
                expected_digest = (
                    self.bridge._ai_trade_council_snapshot_artifact_digest(
                        self.bridge._ai_trade_council_snapshot_artifact_core(
                            snapshot_model
                        )
                    )
                )
                self.assertEqual(
                    reference,
                    (
                        "ai-trade-council/snapshots/"
                        f"{expected_digest}.json"
                    ),
                )
                self.assertFalse(reference.startswith("workspace/"))
                artifact = workspace / reference
                self.assertTrue(artifact.is_file())
                stored = json.loads(artifact.read_text(encoding="utf-8"))
                self.assertEqual(stored["snapshotId"], snapshot_id)
                self.assertEqual(stored["artifactDigest"], expected_digest)
                self.assertEqual(
                    self.bridge._ai_trade_council_snapshot_artifact_digest(
                        stored
                    ),
                    expected_digest,
                )
                self.assertEqual(stored["dailySummary"]["serverDay"], "2026-07-29")

                contract = self.bridge.load_ai_trade_council_prompt_contract()
                news = next(
                    row
                    for row in contract["agents"]
                    if row["agentId"] == "codex_mcp_operator"
                )
                prompt = self.bridge._render_ai_trade_council_prompt(
                    news,
                    snapshot_id,
                    reference,
                    contract["outputSchema"],
                )
                self.assertIn(reference, prompt)
                self.assertNotIn(f"workspace/{reference}", prompt)
                self.assertNotIn("COUNCIL_VOTE_JSON:", prompt)
                self.assertNotIn("status, summary, findings", prompt)
                tools = json.loads(
                    (
                        PROJECT_ROOT
                        / "contracts"
                        / "tools"
                        / "tool-permission-contract.json"
                    ).read_text(encoding="utf-8")
                )["tools"]
                for tool_id in ("codex_cli_task", "codex_web_research"):
                    policy = next(
                        item["aiTradeCouncilPolicy"]
                        for item in tools
                        if item["id"] == tool_id
                    )
                    self.assertEqual(policy["sandbox"], "read-only")
                    self.assertFalse(policy["shellAllowed"])
                    self.assertFalse(policy["mt4TerminalAllowed"])
                    self.assertFalse(policy["secretAccessAllowed"])
                    self.assertEqual(
                        policy["allowedWorkspaceArtifactPattern"],
                        (
                            "ai-trade-council/snapshots/"
                            "<artifact-sha256>.json"
                        ),
                    )
            finally:
                self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR = original_workspace
                self.bridge.AI_TRADE_COUNCIL_SNAPSHOT_DIR = original_snapshot_dir

    def test_ai_trade_council_digest_only_snapshot_path_fits_windows_max_path(self) -> None:
        snapshot_id = "a" * 64
        artifact_digest = "b" * 64
        reference = self.bridge.ai_trade_council_snapshot_reference(
            snapshot_id,
            artifact_digest,
        )
        self.assertEqual(
            reference,
            f"ai-trade-council/snapshots/{artifact_digest}.json",
        )
        self.assertEqual(Path(reference).name, f"{artifact_digest}.json")

        artifact_path = self.bridge.AI_TRADE_COUNCIL_WORKSPACE_DIR / reference
        temporary_path = artifact_path.with_name(
            f".{artifact_path.name}.{threading.get_ident()}.tmp"
        )
        if sys.platform == "win32":
            self.assertLess(len(str(artifact_path.resolve())), 260)
            self.assertLess(len(str(temporary_path.resolve())), 260)

        legacy_name = f"{snapshot_id}-{artifact_digest}.json"
        legacy_temporary = artifact_path.with_name(
            f".{legacy_name}.{threading.get_ident()}.tmp"
        )
        self.assertGreater(
            len(str(legacy_temporary)),
            len(str(temporary_path)) + 64,
        )

    def test_ai_trade_council_requires_backend_reference_prices_exact_three_votes_and_no_ai_sizing(self) -> None:
        snapshot_id = "9" * 64
        reference_price = 2400.1
        expected_roles = [
            ("optimization_agent", "technical"),
            ("backtest_analyst", "price_action"),
            ("codex_mcp_operator", "news"),
        ]
        self.assertEqual(
            list(self.runner.AI_TRADE_COUNCIL_ROLE_BY_AGENT.items()),
            expected_roles,
        )

        output_schema = self.runner.build_ai_trade_council_output_schema(
            snapshot_id,
            "optimization_agent",
            "technical",
        )
        expected_vote_fields = {
            "snapshotId",
            "agentId",
            "roleId",
            "decision",
            "confidence",
            "horizonBars",
            "validUntilBarTime",
            "stopLossPrice",
            "takeProfitPrice",
            "indicatorValidation",
            "volatilityState",
            "eventRisk",
            "horizon",
            "observations",
            "invalidation",
            "evidence",
            "warnings",
        }
        self.assertFalse(output_schema["additionalProperties"])
        self.assertEqual(set(output_schema["properties"]), expected_vote_fields)
        self.assertEqual(set(output_schema["required"]), expected_vote_fields)
        self.assertNotIn("referencePrice", output_schema["properties"])
        for forbidden in (
            "lot",
            "lots",
            "fixedLot",
            "volume",
            "positionSize",
            "risk",
            "riskPercent",
        ):
            self.assertNotIn(forbidden, output_schema["properties"])

        horizon_bars = 1
        valid_until_bar_time = int(time.time()) + 7200
        round_deadline_at = (
            datetime.now(timezone.utc) + timedelta(minutes=5)
        ).isoformat()

        def vote_payload(
            agent_id: str,
            role_id: str,
            *,
            decision: str = "BUY",
            stop_loss_price: float | None = 2390.0,
            take_profit_price: float | None = 2410.0,
        ) -> dict:
            evidence = []
            if role_id == "news":
                evidence = [
                    {
                        "label": "Official source one",
                        "observedAt": datetime.now(timezone.utc).isoformat(),
                        "sourceUrl": "https://example.com/source-one",
                    },
                    {
                        "label": "Official source two",
                        "observedAt": datetime.now(timezone.utc).isoformat(),
                        "sourceUrl": "https://example.org/source-two",
                    },
                ]
            return {
                "snapshotId": snapshot_id,
                "agentId": agent_id,
                "roleId": role_id,
                "decision": decision,
                "confidence": 70,
                "horizonBars": horizon_bars,
                "validUntilBarTime": valid_until_bar_time,
                "stopLossPrice": stop_loss_price if role_id == "price_action" else None,
                "takeProfitPrice": take_profit_price if role_id == "price_action" else None,
                "indicatorValidation": "PASS" if role_id == "technical" else None,
                "volatilityState": "NORMAL" if role_id == "technical" else None,
                "eventRisk": "ALLOW" if role_id == "news" else None,
                "horizon": "4 hours",
                "observations": ["The bounded snapshot supports this vote."],
                "invalidation": "The closed-candle structure changes.",
                "evidence": evidence,
                "warnings": [],
            }

        technical_context = {
            "snapshotId": snapshot_id,
            "agentId": "optimization_agent",
            "roleId": "technical",
            "referencePrice": reference_price,
            "horizonBars": horizon_bars,
            "validUntilBarTime": valid_until_bar_time,
            "volatilityState": "NORMAL",
            "readOnly": True,
        }
        valid_buy = vote_payload("optimization_agent", "technical")
        parsed_buy = self.bridge.validate_ai_trade_council_vote(
            json.dumps(valid_buy),
            technical_context,
        )
        self.assertIsNotNone(parsed_buy)
        self.assertIsNone(parsed_buy["stopLossPrice"])
        self.assertIsNone(parsed_buy["takeProfitPrice"])

        price_action_context = {
            "snapshotId": snapshot_id,
            "agentId": "backtest_analyst",
            "roleId": "price_action",
            "referencePrice": reference_price,
            "horizonBars": horizon_bars,
            "validUntilBarTime": valid_until_bar_time,
            "readOnly": True,
        }
        valid_price_action = vote_payload("backtest_analyst", "price_action")
        for missing_field in ("stopLossPrice", "takeProfitPrice"):
            with self.subTest(missing_protective_price=missing_field):
                missing = dict(valid_price_action)
                missing[missing_field] = None
                self.assertIsNone(
                    self.bridge.validate_ai_trade_council_vote(
                        json.dumps(missing),
                        price_action_context,
                    )
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "protective prices",
                ):
                    self.runner.parse_ai_trade_council_result(
                        json.dumps(missing),
                        snapshot_id,
                        "backtest_analyst",
                        "price_action",
                    )

        invalid_sell = vote_payload(
            "backtest_analyst",
            "price_action",
            decision="SELL",
            stop_loss_price=2390.0,
            take_profit_price=2410.0,
        )
        self.assertIsNone(
            self.bridge.validate_ai_trade_council_vote(
                json.dumps(invalid_sell),
                price_action_context,
            )
        )
        valid_sell = vote_payload(
            "backtest_analyst",
            "price_action",
            decision="SELL",
            stop_loss_price=2410.0,
            take_profit_price=2390.0,
        )
        self.assertIsNotNone(
            self.bridge.validate_ai_trade_council_vote(
                json.dumps(valid_sell),
                price_action_context,
            )
        )

        for forbidden_field in (
            "lot",
            "lots",
            "fixedLot",
            "volume",
            "positionSize",
            "risk",
            "riskPercent",
        ):
            with self.subTest(forbidden_ai_sizing=forbidden_field):
                sized_vote = {**valid_buy, forbidden_field: 0.01}
                self.assertIsNone(
                    self.bridge.validate_ai_trade_council_vote(
                        json.dumps(sized_vote),
                        technical_context,
                    )
                )

        sanitized_votes = []
        for index, (agent_id, role_id) in enumerate(expected_roles):
            context = {
                "snapshotId": snapshot_id,
                "agentId": agent_id,
                "roleId": role_id,
                "referencePrice": reference_price,
                "horizonBars": horizon_bars,
                "validUntilBarTime": valid_until_bar_time,
                "volatilityState": "NORMAL" if role_id == "technical" else None,
                "qualityPolicy": {
                    "maximumNewsAgeSeconds": 86400,
                    "maximumFutureEvidenceSkewSeconds": 300,
                    "minimumDistinctNewsDomains": 2,
                },
                "readOnly": True,
            }
            vote = vote_payload(
                agent_id,
                role_id,
                stop_loss_price=2389.0 + index,
                take_profit_price=2410.0 + index,
            )
            sanitized = self.bridge.validate_ai_trade_council_vote(
                json.dumps(vote),
                context,
            )
            self.assertIsNotNone(sanitized)
            sanitized_votes.append(sanitized)

        parent = {
            "analysisContext": {
                "kind": "ai_trade_council_parent",
                "snapshotId": snapshot_id,
                "referencePrice": reference_price,
                "horizonBars": horizon_bars,
                "validUntilBarTime": valid_until_bar_time,
                "roundDeadlineAt": round_deadline_at,
                "qualityGate": {
                    "passed": True,
                    "reasonCodes": [],
                    "confidenceFloorDefault": 70,
                    "confidenceFloorByRole": {
                        "technical": 70,
                        "price_action": 70,
                        "news": 70,
                    },
                    "minimumRewardRiskRatio": 1.0,
                    "technical": {"volatilityState": "NORMAL"},
                    "marketState": {"status": "available", "marketOpen": True},
                    "executionEligibility": {
                        "shadow": True,
                        "demo": True,
                        "live": True,
                    },
                },
                "readOnly": True,
            }
        }
        children = [
            {"owner": agent_id, "councilVote": sanitized_votes[index]}
            for index, (agent_id, _role_id) in enumerate(expected_roles)
        ]
        incomplete = self.bridge.ai_trade_council_consensus(parent, children[:2])
        self.assertFalse(incomplete["ready"])
        self.assertEqual(incomplete["voteCount"], 2)
        self.assertEqual(incomplete["decision"], "NO_DATA")
        self.assertFalse(incomplete["tradePlan"]["available"])

        complete = self.bridge.ai_trade_council_consensus(parent, children)
        self.assertTrue(complete["ready"])
        self.assertEqual(complete["voteCount"], 3)
        self.assertTrue(complete["unanimous"])
        self.assertEqual(complete["decision"], "BUY")
        self.assertEqual(complete["tradePlan"]["stopLossPrice"], 2390.0)
        self.assertEqual(complete["tradePlan"]["takeProfitPrice"], 2411.0)
        self.assertEqual(
            set(complete["tradePlan"]),
            {
                "available",
                "direction",
                "stopLossPrice",
                "takeProfitPrice",
                "protectivePriceOwnerRole",
                "rewardRiskRatio",
                "priceAggregation",
                "protectivePlanSource",
                "protectivePlanReasonCode",
                "protectivePlanPolicyVersion",
                "protectivePlanFallbackUsed",
                "protectivePlanProvenance",
                "lotPolicy",
                "aiLotAllowed",
            },
        )
        self.assertEqual(
            complete["tradePlan"]["protectivePlanSource"],
            "price_action_agent",
        )
        self.assertFalse(complete["tradePlan"]["protectivePlanFallbackUsed"])
        self.assertEqual(complete["tradePlan"]["lotPolicy"], "ea_fixed_lot_only")
        self.assertFalse(complete["tradePlan"]["aiLotAllowed"])

    def test_ai_trade_council_automation_rejects_m1_and_supports_m5(self) -> None:
        supported = self.bridge.AI_TRADE_COUNCIL_AUTOMATION_SUPPORTED_TIMEFRAMES
        self.assertNotIn("M1", supported)
        self.assertIn("M5", supported)

        candidate_id = "mtc-timeframe-policy"
        symbol = "XAUUSD"
        closed_bar_time = 1785445200
        snapshot_id = "8" * 64
        original_runtime = self.bridge.RUNTIME_DIR
        original_audit = self.bridge.AUDIT_PATH
        original_snapshot_reader = self.bridge.metatrader_snapshot_read_model
        current_timeframe = {"value": "M1"}

        def snapshot_model(_prop_id: str) -> dict:
            return {
                "selectedCandidateId": candidate_id,
                "adapter": {"ready": True},
                "chartSnapshot": {
                    "available": True,
                    "snapshotId": snapshot_id,
                    "symbol": symbol,
                    "timeframe": current_timeframe["value"],
                    "bars": [{"time": closed_bar_time}],
                },
            }

        def store_for(timeframe: str) -> dict:
            store = self.bridge._ai_trade_council_automation_default_store()
            store["config"]["enabled"] = True
            store["state"].update({
                "status": "idle",
                "reason": "waiting_for_new_closed_bar",
                "startupId": self.bridge.SERVER_STARTED_AT,
                "dailyRunDate": self.bridge._automation_day_key(),
                "candidateId": candidate_id,
                "streamKey": self.bridge.payload_digest(
                    candidate_id,
                    symbol,
                    timeframe,
                ),
                "symbol": symbol,
                "timeframe": timeframe,
                "lastObservedClosedBarTime": closed_bar_time,
            })
            return store

        with tempfile.TemporaryDirectory() as directory:
            try:
                self.bridge.RUNTIME_DIR = Path(directory) / "runtime"
                self.bridge.AUDIT_PATH = Path(directory) / "audit.jsonl"
                self.bridge.metatrader_snapshot_read_model = snapshot_model

                self.bridge._save_ai_trade_council_automation_store(store_for("M1"))
                m1_result = self.bridge.ai_trade_council_automation_tick()
                self.assertFalse(m1_result["ok"])
                self.assertEqual(
                    m1_result["kind"],
                    "ai_trade_council_automation_unsupported_timeframe",
                )
                self.assertEqual(
                    m1_result["automation"]["state"]["status"],
                    "unsupported_timeframe",
                )

                current_timeframe["value"] = "M5"
                self.bridge._save_ai_trade_council_automation_store(store_for("M5"))
                m5_result = self.bridge.ai_trade_council_automation_tick()
                self.assertTrue(m5_result["ok"])
                self.assertEqual(
                    m5_result["kind"],
                    "ai_trade_council_automation_idle",
                )
                self.assertNotEqual(
                    m5_result["automation"]["state"]["status"],
                    "unsupported_timeframe",
                )
            finally:
                self.bridge.RUNTIME_DIR = original_runtime
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.metatrader_snapshot_read_model = original_snapshot_reader

    def _runner_council_snapshot_payload(
        self,
        snapshot_id: str,
        analysis_bar_count: int = 120,
    ) -> dict:
        start_time = 1785283200
        bars = [
            {
                "time": start_time + (index * 14400),
                "open": 2300 + index,
                "high": 2301 + index,
                "low": 2299 + index,
                "close": 2300.5 + index,
                "volume": 100 + index,
            }
            for index in range(analysis_bar_count)
        ]
        payload = {
            "schemaVersion": "ai-trade-council-input-v1",
            "snapshotId": snapshot_id,
            "createdAt": "2026-07-29T02:00:00Z",
            "sourceMode": "mt4_read_only_snapshot",
            "dailySummary": {
                "available": True,
                "serverDay": "2026-07-29",
                "profit": 12.5,
            },
            "chartSnapshot": {
                "available": True,
                "status": "fresh",
                "snapshotId": snapshot_id,
                "observedAt": "2026-07-29T02:00:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "bid": 2400.0,
                "ask": 2400.2,
                "spreadPoints": 20,
                "barCount": analysis_bar_count,
                "sourceBarCount": analysis_bar_count,
                "analysisWindow": {
                    "requestedBars": analysis_bar_count,
                    "usedBars": analysis_bar_count,
                    "startTime": bars[0]["time"],
                    "endTime": bars[-1]["time"],
                    "closedBarsOnly": True,
                    "sourceBarCount": analysis_bar_count,
                    "indicatorFormulaVersion": "metafx-deterministic-core20-price-action-v3",
                },
                "bars": bars,
                "technicalIndicators": {
                    "formulaVersion": "metafx-deterministic-core20-price-action-v3",
                    "basis": "backend_calculated_closed_bars_only",
                    "moduleCount": 14,
                    "modules": [
                        "sma_family",
                        "ema_family",
                        "rsi14",
                        "macd_12_26_9",
                        "stochastic_14_3_3",
                        "atr14",
                        "bollinger_20_2",
                        "adx_dmi14",
                        "cci20",
                        "williams_r14",
                        "roc12",
                        "momentum10",
                        "obv",
                        "mfi14",
                    ],
                    "ema20": 2400.0,
                    "ema50": 2380.0,
                    "rsi14": 60.0,
                    "atr14": 4.0,
                    "macdLine": 2.0,
                    "series": [
                        {
                            "time": item["time"],
                            "ema20": item["close"] - 2.0,
                            "rsi14": 60.0,
                        }
                        for item in bars
                    ],
                },
                "priceActionFeatures": {
                    "available": True,
                    "basis": "backend_calculated_confirmed_closed_bars_only",
                    "formulaVersion": "metafx-deterministic-core20-price-action-v3",
                    "barCount": analysis_bar_count,
                    "moduleCount": 6,
                    "modules": [
                        "confirmed_swing_pivots",
                        "support_resistance",
                        "trendlines",
                        "fibonacci_latest_confirmed_swing",
                        "rsi_divergence",
                        "macd_divergence",
                    ],
                    "swings": {"highs": [], "lows": []},
                    "supportResistance": {"supports": [], "resistances": []},
                    "trendlines": {"support": None, "resistance": None},
                    "fibonacci": {"available": False},
                    "divergences": {
                        "rsi": {"bullish": None, "bearish": None},
                        "macd": {"bullish": None, "bearish": None},
                    },
                },
            },
            "policy": {
                "readOnly": True,
                "sameSnapshotRequired": True,
                "terminalActionsAllowed": False,
                "riskGuardVoting": False,
                "sourceBarCount": analysis_bar_count,
                "analysisBarCountRequested": analysis_bar_count,
                "analysisBarCountUsed": analysis_bar_count,
                "indicatorFormulaVersion": "metafx-deterministic-core20-price-action-v3",
                "analysisWindow": {
                    "requestedBars": analysis_bar_count,
                    "usedBars": analysis_bar_count,
                    "startTime": bars[0]["time"],
                    "endTime": bars[-1]["time"],
                    "closedBarsOnly": True,
                    "sourceBarCount": analysis_bar_count,
                    "indicatorFormulaVersion": "metafx-deterministic-core20-price-action-v3",
                },
                "qualityGate": {
                    "horizonBars": 1,
                    "validUntilBarTime": 1900000000,
                    "technical": {
                        "indicatorDataSufficient": True,
                        "volatilityState": "NORMAL",
                    },
                },
            },
        }
        payload["artifactDigest"] = (
            self.runner.ai_trade_council_snapshot_artifact_digest(payload)
        )
        return payload

    def test_ai_trade_council_runner_embeds_bounded_snapshot_and_returns_exact_vote_json(self) -> None:
        snapshot_id = "b" * 64
        vote = {
            "snapshotId": snapshot_id,
            "agentId": "codex_mcp_operator",
            "roleId": "news",
            "decision": "HOLD",
            "confidence": 64,
            "horizonBars": 1,
            "validUntilBarTime": 1900000000,
            "stopLossPrice": None,
            "takeProfitPrice": None,
            "indicatorValidation": None,
            "volatilityState": None,
            "eventRisk": "HOLD",
            "horizon": "4 hours",
            "observations": ["No immediate high-impact event changed the view."],
            "invalidation": "A new verified high-impact release changes the context.",
            "evidence": [
                {
                    "label": "Official source one",
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceUrl": "https://example.com/source-one",
                },
                {
                    "label": "Official source two",
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceUrl": "https://example.org/source-two",
                },
            ],
            "warnings": [],
        }
        original_workspace = self.runner.AUTO_WORKSPACE_ROOT
        original_additional_roots = self.runner.AUTO_ADDITIONAL_WRITE_ROOTS
        original_runs_dir = self.runner.CODEX_RUNS_DIR
        original_status = self.runner.chat_status
        original_run_chat_command = self.runner.run_chat_command
        captured = {}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            snapshot_payload = self._runner_council_snapshot_payload(
                snapshot_id,
                180,
            )
            artifact_digest = snapshot_payload["artifactDigest"]
            artifact = (
                workspace
                / "ai-trade-council"
                / "snapshots"
                / f"{artifact_digest}.json"
            )
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(
                json.dumps(snapshot_payload),
                encoding="utf-8",
            )

            def fake_run_chat_command(command, timeout, stdin, cwd, output_limit=60000):
                captured["command"] = list(command)
                captured["stdin"] = stdin
                captured["cwd"] = cwd
                schema_path = Path(command[command.index("--output-schema") + 1])
                captured["schema"] = json.loads(schema_path.read_text(encoding="utf-8"))
                raw_path = Path(command[command.index("-o") + 1])
                raw_path.write_text(json.dumps(vote), encoding="utf-8")
                return {
                    "ok": True,
                    "exitCode": 0,
                    "stdout": json.dumps({
                        "type": "item.completed",
                        "item": {
                            "id": "item-council-news-web",
                            "type": "web_search",
                            "query": "official market sources",
                            "action": {"type": "search", "query": "official market sources"},
                        },
                    }),
                    "stderr": "",
                    "durationMs": 1,
                    "processStarted": True,
                    "processTreeTerminated": False,
                }

            try:
                self.runner.AUTO_WORKSPACE_ROOT = workspace
                self.runner.AUTO_ADDITIONAL_WRITE_ROOTS = ()
                self.runner.CODEX_RUNS_DIR = root / "codex-runs"
                self.runner.chat_status = lambda: {"ok": True, "status": "runtime_ready"}
                self.runner.run_chat_command = fake_run_chat_command
                result = self.runner.run_codex(
                    "Analyze the Backend-supplied Council snapshot.",
                    "codex_mcp_operator",
                    "council-news-schema-mode",
                    execution_mode="auto_guarded",
                    web_search=True,
                    result_mode="ai_trade_council_vote",
                    council_snapshot_id=snapshot_id,
                    council_role_id="news",
                    council_snapshot_digest=artifact_digest,
                )
            finally:
                self.runner.AUTO_WORKSPACE_ROOT = original_workspace
                self.runner.AUTO_ADDITIONAL_WRITE_ROOTS = original_additional_roots
                self.runner.CODEX_RUNS_DIR = original_runs_dir
                self.runner.chat_status = original_status
                self.runner.run_chat_command = original_run_chat_command

        self.assertTrue(result["ok"])
        self.assertEqual(result["workStatus"], "completed")
        self.assertEqual(result["resultMode"], "ai_trade_council_vote")
        self.assertTrue(result["webSearchUsed"])
        self.assertTrue(result["webSearchEvidenceVerified"])
        self.assertEqual(set(json.loads(result["finalMessage"])), set(vote))
        self.assertNotIn("status", json.loads(result["finalMessage"]))
        command = captured["command"]
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertIn("shell_tool", command)
        self.assertIn("--json", command)
        self.assertNotIn("--add-dir", command)
        self.assertEqual(captured["cwd"], workspace)
        self.assertEqual(
            captured["schema"]["properties"]["snapshotId"]["enum"],
            [snapshot_id],
        )
        self.assertEqual(
            set(captured["schema"]["required"]),
            {
                "snapshotId",
                "agentId",
                "roleId",
                "decision",
                "confidence",
                "horizonBars",
                "validUntilBarTime",
                "stopLossPrice",
                "takeProfitPrice",
                "indicatorValidation",
                "volatilityState",
                "eventRisk",
                "horizon",
                "observations",
                "invalidation",
                "evidence",
                "warnings",
            },
        )
        self.assertNotIn("referencePrice", captured["schema"]["properties"])
        for forbidden in (
            "lot",
            "lots",
            "fixedLot",
            "volume",
            "positionSize",
            "risk",
            "riskPercent",
        ):
            self.assertNotIn(forbidden, captured["schema"]["properties"])
        injected_prompt = captured["stdin"]
        self.assertIn("Backend-supplied Council snapshot JSON", injected_prompt)
        self.assertIn('"serverDay":"2026-07-29"', injected_prompt)
        self.assertIn('"barsIncluded":0', injected_prompt)
        self.assertNotIn('"bars":[', injected_prompt)
        self.assertNotIn("accountNumber", injected_prompt)
        self.assertLess(len(injected_prompt), 30000)

    def test_ai_trade_council_runner_rejects_mutated_digest_bound_artifact(self) -> None:
        snapshot_id = "7" * 64
        payload = self._runner_council_snapshot_payload(snapshot_id, 120)
        artifact_digest = payload["artifactDigest"]
        original_workspace = self.runner.AUTO_WORKSPACE_ROOT
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            artifact = (
                workspace
                / "ai-trade-council"
                / "snapshots"
                / f"{artifact_digest}.json"
            )
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(json.dumps(payload), encoding="utf-8")
            try:
                self.runner.AUTO_WORKSPACE_ROOT = workspace
                reference, loaded = (
                    self.runner.load_ai_trade_council_snapshot(
                        snapshot_id,
                        artifact_digest,
                    )
                )
                self.assertEqual(
                    reference,
                    (
                        "ai-trade-council/snapshots/"
                        f"{artifact_digest}.json"
                    ),
                )
                self.assertEqual(loaded["artifactDigest"], artifact_digest)

                payload["chartSnapshot"]["bars"][5]["high"] += 50
                artifact.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    self.runner.load_ai_trade_council_snapshot(
                        snapshot_id,
                        artifact_digest,
                    )
            finally:
                self.runner.AUTO_WORKSPACE_ROOT = original_workspace

    def test_ai_trade_council_runner_embeds_exact_backend_bound_bar_count(self) -> None:
        for count in (120, 240, 300):
            with self.subTest(count=count):
                payload = self._runner_council_snapshot_payload("c" * 64, count)
                compact = self.runner.compact_ai_trade_council_snapshot(
                    payload,
                    "technical",
                )
                chart = compact["chartSnapshot"]
                self.assertNotIn("bars", chart)
                bars_columnar = chart["barsColumnar"]
                self.assertEqual(bars_columnar["encoding"], "field_columns_v1")
                self.assertEqual(
                    bars_columnar["fields"],
                    list(self.runner.AI_TRADE_COUNCIL_RAW_BAR_FIELDS),
                )
                self.assertEqual(bars_columnar["pointCount"], count)
                decoded_bars = [
                    {
                        field: bars_columnar["columns"][field_index][row_index]
                        for field_index, field in enumerate(bars_columnar["fields"])
                    }
                    for row_index in range(bars_columnar["pointCount"])
                ]
                self.assertEqual(decoded_bars, payload["chartSnapshot"]["bars"])
                self.assertEqual(chart["barsIncluded"], count)
                self.assertEqual(chart["analysisWindow"]["usedBars"], count)
                self.assertEqual(
                    compact["policy"]["analysisBarCountUsed"],
                    count,
                )

    def test_ai_trade_council_runner_enforces_role_data_separation(self) -> None:
        payload = self._runner_council_snapshot_payload("d" * 64, 120)
        technical = self.runner.compact_ai_trade_council_snapshot(
            payload,
            "technical",
        )["chartSnapshot"]
        price_action = self.runner.compact_ai_trade_council_snapshot(
            payload,
            "price_action",
        )["chartSnapshot"]
        news_compact = self.runner.compact_ai_trade_council_snapshot(
            payload,
            "news",
        )
        news = news_compact["chartSnapshot"]

        self.assertEqual(technical["barsIncluded"], 120)
        self.assertIn("barsColumnar", technical)
        self.assertNotIn("bars", technical)
        self.assertIn("technicalIndicators", technical)
        self.assertEqual(
            technical["technicalIndicators"]["formulaVersion"],
            "metafx-deterministic-core20-price-action-v3",
        )
        self.assertNotIn("series", technical["technicalIndicators"])
        self.assertEqual(
            technical["technicalIndicators"]["importantSeriesColumnar"][
                "pointCount"
            ],
            120,
        )
        self.assertEqual(
            technical["technicalIndicators"]["latestDetailSeriesColumnar"][
                "pointCount"
            ],
            60,
        )

        self.assertEqual(price_action["barsIncluded"], 120)
        self.assertIn("bars", price_action)
        self.assertIn("priceActionFeatures", price_action)
        self.assertEqual(
            price_action["priceActionFeatures"]["formulaVersion"],
            "metafx-deterministic-core20-price-action-v3",
        )
        self.assertNotIn("technicalIndicators", price_action)
        self.assertNotIn("technicalSeries", price_action)
        self.assertNotIn("indicatorSeries", price_action)
        self.assertEqual(
            price_action["analysisWindow"]["indicatorFormulaVersion"],
            "metafx-deterministic-core20-price-action-v3",
        )

        self.assertEqual(news["barsIncluded"], 0)
        self.assertNotIn("bars", news)
        self.assertNotIn("technicalIndicators", news)
        self.assertNotIn("technicalSeries", news)
        self.assertNotIn("indicatorSeries", news)
        self.assertNotIn("priceActionFeatures", news)
        self.assertNotIn("barsColumnar", news)
        self.assertNotIn("indicatorFormulaVersion", news["analysisWindow"])
        self.assertNotIn("indicatorFormulaVersion", news_compact["policy"])
        self.assertNotIn("technical", news_compact["policy"]["qualityGate"])

    def test_ai_trade_council_runner_compacts_1000_bar_prompt_with_audited_scope(self) -> None:
        payload = self._runner_council_snapshot_payload("a" * 64, 1000)
        payload["chartSnapshot"].update(
            self.bridge._ai_trade_council_analysis_feature_bundle(
                payload["chartSnapshot"]["bars"]
            )
        )
        self.assertLess(
            len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            self.runner.AI_TRADE_COUNCIL_SNAPSHOT_MAX_BYTES,
        )
        technical = self.runner.compact_ai_trade_council_snapshot(
            payload,
            "technical",
        )
        technical_scope = technical["promptScope"]
        self.assertEqual(technical_scope["artifactAnalysisBars"], 1000)
        self.assertEqual(technical_scope["analysisMode"], "smart_300")
        self.assertEqual(technical_scope["rawBarsIncluded"], 300)
        self.assertEqual(technical_scope["technicalSeriesIncluded"], 300)
        self.assertEqual(
            technical_scope["technicalImportantSeriesIncluded"],
            300,
        )
        self.assertEqual(technical_scope["technicalDetailSeriesIncluded"], 60)
        self.assertEqual(
            technical_scope["rawBarsScope"],
            "latest_closed_bars_prompt_limited",
        )
        self.assertEqual(
            technical_scope["technicalImportantSeriesScope"],
            "latest_closed_bars_prompt_limited",
        )
        self.assertFalse(
            technical_scope["fullWindowCompressedEvidenceIncluded"]
        )
        self.assertEqual(
            technical_scope["technicalSummaryScope"],
            "all_module_summaries_full_analysis_window",
        )
        self.assertLessEqual(
            len(json.dumps(technical, ensure_ascii=False, separators=(",", ":"))),
            self.runner.AI_TRADE_COUNCIL_EMBEDDED_SOFT_MAX_CHARS,
        )
        full_prompt = self.runner.build_prompt(
            "x" * 8000,
            "optimization_agent",
            "prompt-cap-test",
            "specialist_balanced",
            7000,
            "auto_guarded",
            False,
            "ai_trade_council_vote",
            (
                "ai-trade-council/snapshots/"
                + ("b" * 64)
                + ".json"
            ),
            technical,
        )
        self.assertLessEqual(
            len(full_prompt),
            self.runner.AI_TRADE_COUNCIL_PROMPT_MAX_CHARS,
        )

        price_action = self.runner.compact_ai_trade_council_snapshot(
            payload,
            "price_action",
        )
        price_scope = price_action["promptScope"]
        self.assertEqual(price_scope["artifactAnalysisBars"], 1000)
        self.assertEqual(price_scope["rawBarsIncluded"], 500)
        self.assertEqual(
            price_scope["priceActionFeaturesScope"],
            "all_backend_features_full_analysis_window",
        )
        self.assertIn("priceActionFeatures", price_action["chartSnapshot"])
        self.assertNotIn("technicalIndicators", price_action["chartSnapshot"])

        news = self.runner.compact_ai_trade_council_snapshot(payload, "news")
        self.assertEqual(news["promptScope"]["rawBarsIncluded"], 0)
        self.assertNotIn("bars", news["chartSnapshot"])
        self.assertNotIn("technicalIndicators", news["chartSnapshot"])
        self.assertNotIn("priceActionFeatures", news["chartSnapshot"])

    def test_runner_separates_1000_source_bars_from_300_bar_mission_artifact(self) -> None:
        payload = self._runner_council_snapshot_payload("9" * 64, 300)
        payload["chartSnapshot"]["sourceBarCount"] = 1000
        payload["chartSnapshot"]["analysisWindow"]["sourceBarCount"] = 1000
        payload["policy"]["sourceBarCount"] = 1000
        payload["policy"]["analysisWindow"]["sourceBarCount"] = 1000
        for index, bar in enumerate(payload["chartSnapshot"]["bars"]):
            close = 2300.0 + (index * 0.137) + ((index % 17) * 0.019)
            bar.update({
                "open": round(close - ((index % 5) * 0.071), 8),
                "high": round(close + 1.113 + ((index % 7) * 0.037), 8),
                "low": round(close - 1.207 - ((index % 11) * 0.029), 8),
                "close": round(close, 8),
                "volume": 100 + ((index * 13) % 211),
            })
        payload["chartSnapshot"].update(
            self.bridge._ai_trade_council_analysis_feature_bundle(
                payload["chartSnapshot"]["bars"]
            )
        )
        self.assertLess(
            len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            self.runner.AI_TRADE_COUNCIL_SNAPSHOT_MAX_BYTES,
        )

        technical = self.runner.compact_ai_trade_council_snapshot(
            payload,
            "technical",
            {"analysisMode": "deep_300"},
        )
        scope = technical["promptScope"]
        self.assertEqual(scope["analysisMode"], "deep_300")
        self.assertFalse(scope["analysisModeDefaulted"])
        self.assertEqual(scope["sourceSnapshotBars"], 1000)
        self.assertEqual(scope["missionArtifactBars"], 300)
        self.assertEqual(scope["artifactAnalysisBars"], 300)
        self.assertEqual(
            scope["artifactScope"],
            "exact_backend_audited_analysis_window_not_full_source_snapshot",
        )
        self.assertEqual(technical["policy"]["analysisBarCountUsed"], 300)
        self.assertEqual(len(payload["chartSnapshot"]["bars"]), 300)
        self.assertEqual(scope["rawBarsIncluded"], 300)
        self.assertEqual(scope["rawBarsScope"], "full_analysis_window")
        self.assertEqual(scope["technicalSeriesIncluded"], 300)
        self.assertEqual(scope["technicalSeriesScope"], "full_analysis_window")
        self.assertEqual(scope["technicalImportantSeriesIncluded"], 300)
        self.assertEqual(scope["technicalDetailSeriesIncluded"], 60)
        self.assertEqual(
            scope["technicalDetailSeriesScope"],
            "latest_closed_bars_prompt_limited",
        )
        self.assertEqual(
            scope["technicalDetailIndicatorFieldCount"],
            27,
        )
        self.assertTrue(scope["fullWindowCompressedEvidenceIncluded"])
        self.assertFalse(scope["fallbackApplied"])
        self.assertTrue(scope["softLimitSatisfied"])
        self.assertTrue(scope["hardLimitSatisfied"])
        chart = technical["chartSnapshot"]
        self.assertNotIn("bars", chart)
        self.assertEqual(chart["barsColumnar"]["pointCount"], 300)
        indicators = chart["technicalIndicators"]
        self.assertNotIn("series", indicators)
        self.assertEqual(
            indicators["importantSeriesColumnar"]["pointCount"],
            300,
        )
        self.assertEqual(
            indicators["importantSeriesColumnar"]["fields"],
            list(
                self.runner.AI_TRADE_COUNCIL_TECHNICAL_IMPORTANT_SERIES_FIELDS
            ),
        )
        self.assertEqual(
            indicators["latestDetailSeriesColumnar"]["pointCount"],
            60,
        )
        self.assertEqual(
            indicators["latestDetailSeriesColumnar"]["fields"],
            list(
                self.runner.AI_TRADE_COUNCIL_TECHNICAL_DETAIL_SERIES_FIELDS
            ),
        )
        self.assertLessEqual(
            len(json.dumps(technical, ensure_ascii=False, separators=(",", ":"))),
            self.runner.AI_TRADE_COUNCIL_EMBEDDED_SOFT_MAX_CHARS,
        )
        technical_prompt = self.runner.build_prompt(
            "x" * 8000,
            "optimization_agent",
            "source-1000-analysis-300-cap-test",
            "specialist_balanced",
            7000,
            "auto_guarded",
            False,
            "ai_trade_council_vote",
            (
                "ai-trade-council/snapshots/"
                + ("8" * 64)
                + ".json"
            ),
            technical,
        )
        self.assertLessEqual(
            len(technical_prompt),
            self.runner.AI_TRADE_COUNCIL_PROMPT_MAX_CHARS,
        )

        price_action = self.runner.compact_ai_trade_council_snapshot(
            payload,
            "price_action",
        )
        self.assertEqual(price_action["promptScope"]["sourceSnapshotBars"], 1000)
        self.assertEqual(price_action["promptScope"]["missionArtifactBars"], 300)
        self.assertEqual(price_action["promptScope"]["rawBarsIncluded"], 300)
        self.assertEqual(
            price_action["chartSnapshot"]["priceActionFeatures"]["barCount"],
            300,
        )

        payload["policy"]["sourceBarCount"] = 999
        with self.assertRaisesRegex(ValueError, "source and analysis bar scopes"):
            self.runner.compact_ai_trade_council_snapshot(payload, "technical")

    def test_smart_300_fallback_reports_every_reduced_scope_truthfully(self) -> None:
        payload = self._runner_council_snapshot_payload("8" * 64, 300)
        payload["chartSnapshot"].update(
            self.bridge._ai_trade_council_analysis_feature_bundle(
                payload["chartSnapshot"]["bars"]
            )
        )
        original_soft_limit = (
            self.runner.AI_TRADE_COUNCIL_EMBEDDED_SOFT_MAX_CHARS
        )
        try:
            self.runner.AI_TRADE_COUNCIL_EMBEDDED_SOFT_MAX_CHARS = 12000
            compact = self.runner.compact_ai_trade_council_snapshot(
                payload,
                "technical",
                {"analysisMode": "smart_300"},
            )
        finally:
            self.runner.AI_TRADE_COUNCIL_EMBEDDED_SOFT_MAX_CHARS = (
                original_soft_limit
            )

        scope = compact["promptScope"]
        self.assertTrue(scope["fallbackApplied"])
        self.assertFalse(scope["fullWindowCompressedEvidenceIncluded"])
        self.assertLessEqual(scope["rawBarsIncluded"], 300)
        self.assertLessEqual(scope["technicalImportantSeriesIncluded"], 300)
        if scope["rawBarsIncluded"] < 300:
            self.assertNotEqual(scope["rawBarsScope"], "full_analysis_window")
        if scope["technicalImportantSeriesIncluded"] < 300:
            self.assertNotEqual(
                scope["technicalImportantSeriesScope"],
                "full_analysis_window",
            )
        self.assertEqual(
            scope["promptPayloadCharacters"],
            len(
                json.dumps(
                    compact,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            ),
        )
        self.assertLessEqual(
            scope["promptPayloadCharacters"],
            self.runner.AI_TRADE_COUNCIL_EMBEDDED_MAX_CHARS,
        )

    def test_ai_trade_council_runner_rejects_silent_bar_count_reduction(self) -> None:
        payload = self._runner_council_snapshot_payload("e" * 64, 240)
        payload["policy"]["analysisBarCountRequested"] = 300
        with self.assertRaisesRegex(ValueError, "analysis bar count"):
            self.runner.compact_ai_trade_council_snapshot(payload, "technical")

        payload = self._runner_council_snapshot_payload("f" * 64, 120)
        payload["chartSnapshot"]["bars"].append(
            dict(payload["chartSnapshot"]["bars"][-1])
        )
        with self.assertRaisesRegex(ValueError, "bound analysis count"):
            self.runner.compact_ai_trade_council_snapshot(payload, "price_action")

    def test_ai_trade_council_auto_worker_passes_bound_schema_mode_to_runner(self) -> None:
        snapshot_id = "d" * 64
        snapshot_artifact_digest = "e" * 64
        snapshot_reference = (
            "ai-trade-council/snapshots/"
            f"{snapshot_artifact_digest}.json"
        )
        vote = {
            "snapshotId": snapshot_id,
            "agentId": "codex_mcp_operator",
            "roleId": "news",
            "decision": "HOLD",
            "confidence": 60,
            "horizonBars": 1,
            "validUntilBarTime": int(time.time()) + 7200,
            "stopLossPrice": None,
            "takeProfitPrice": None,
            "indicatorValidation": None,
            "volatilityState": None,
            "eventRisk": "HOLD",
            "horizon": "4 hours",
            "observations": ["Verified public context is neutral."],
            "invalidation": "A new high-impact release changes the context.",
            "evidence": [
                {
                    "label": "Source one",
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceUrl": "https://example.com/one",
                },
                {
                    "label": "Source two",
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceUrl": "https://example.org/two",
                },
            ],
            "warnings": [],
        }
        originals = {
            "OPERATOR_MODE_PATH": self.bridge.OPERATOR_MODE_PATH,
            "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
            "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
            "AUDIT_PATH": self.bridge.AUDIT_PATH,
            "CODEX_RUNNER_PYTHON": self.bridge.CODEX_RUNNER_PYTHON,
            "CODEX_RUNNER_SCRIPT": self.bridge.CODEX_RUNNER_SCRIPT,
            "bridge_status": self.bridge.bridge_status,
            "codex_rate_limits": self.bridge.codex_rate_limits,
            "check_rate_limit": self.bridge.check_rate_limit,
            "run_safe_command": self.bridge.run_safe_command,
            "REAL_RUN_SEMAPHORE": self.bridge.REAL_RUN_SEMAPHORE,
        }
        runner_calls = []

        def fake_command(
            command,
            timeout=8,
            output_limit=1200,
            input_text=None,
            *,
            kill_process_tree_on_timeout=False,
            cancel_event=None,
            tracking_key=None,
        ):
            runner_calls.append(list(command))
            result = {
                "ok": True,
                "status": "completed",
                "workStatus": "completed",
                "finalMessage": json.dumps(vote),
                "durationMs": 4,
                "processStarted": True,
                "processTreeTerminated": False,
                "workingDirectory": "workspace",
                "writeRoots": [],
                "controlPlaneWritable": False,
                "webSearchEnabled": True,
                "webSearchMode": "live",
                "webSearchUsed": True,
                "webSearchEvidenceVerified": True,
                "evidence": vote["evidence"],
                "artifacts": {},
            }
            return {
                "ok": True,
                "exitCode": 0,
                "output": json.dumps(result),
                "durationMs": 4,
                "processStarted": True,
                "processTreeTerminated": False,
            }

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            try:
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "audit.jsonl"
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
                self.assertTrue(
                    self.bridge.set_operator_mode({"mode": "auto_guarded"})["ok"]
                )
                parent_id = "mission-council-worker-parent"
                contract_digest = "f" * 64
                mission = self.bridge.create_mission({
                    "title": "Council news analysis",
                    "prompt": "Analyze the validated read-only Council snapshot.",
                    "agentId": "codex_mcp_operator",
                    "requester": "manager",
                    "parentMissionId": parent_id,
                    "toolId": "codex_web_research",
                    "targetId": "left_analytics_console",
                    "risk": "medium",
                    "reportType": "ai_trade_council_vote",
                    "analysisContext": {
                        "kind": "ai_trade_council_vote",
                        "contractDigest": contract_digest,
                        "snapshotId": snapshot_id,
                        "snapshotArtifact": snapshot_reference,
                        "snapshotArtifactDigest": snapshot_artifact_digest,
                        "agentId": "codex_mcp_operator",
                        "roleId": "news",
                        "referencePrice": 2400.1,
                        "horizonBars": vote["horizonBars"],
                        "validUntilBarTime": vote["validUntilBarTime"],
                        "roundDeadlineAt": (
                            datetime.now(timezone.utc) + timedelta(minutes=5)
                        ).isoformat(),
                        "qualityPolicy": {
                            "maximumNewsAgeSeconds": 86400,
                            "maximumFutureEvidenceSkewSeconds": 300,
                            "minimumDistinctNewsDomains": 2,
                        },
                        "propId": "left_analytics_console",
                        "readOnly": True,
                    },
                }, status="queued", allow_analysis_context=True)
                # A Council vote is executable only as part of one atomically
                # committed three-specialist round. Build that production
                # invariant here while keeping this test focused on runner
                # argument binding for the news specialist.
                child_ids = [mission["id"]]
                siblings = []
                for sibling_agent in ("optimization_agent", "backtest_analyst"):
                    sibling_id = f"mission-council-worker-{sibling_agent}"
                    child_ids.append(sibling_id)
                    siblings.append({
                        "id": sibling_id,
                        "status": "queued",
                        "owner": sibling_agent,
                        "toolId": self.bridge.AI_TRADE_COUNCIL_ALLOWED_TOOLS[
                            sibling_agent
                        ],
                        "parentMissionId": parent_id,
                        "analysisContext": {
                            "kind": "ai_trade_council_vote",
                            "agentId": sibling_agent,
                            "roleId": self.bridge.AI_TRADE_COUNCIL_AGENT_ROLES[
                                sibling_agent
                            ],
                            "snapshotId": snapshot_id,
                            "contractDigest": contract_digest,
                        },
                    })
                parent = {
                    "id": parent_id,
                    "status": "queued",
                    "phase": "council_specialists_queued",
                    "subtaskIds": child_ids,
                    "analysisContext": {
                        "kind": "ai_trade_council_parent",
                        "snapshotId": snapshot_id,
                        "contractDigest": contract_digest,
                    },
                }
                self.bridge.save_missions([parent, mission, *siblings])
                self.assertTrue(mission["autoEligible"])
                self.bridge.process_auto_mission("council-worker-test", mission)
                finished = self.bridge.find_mission(mission["id"])
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)

        self.assertEqual(len(runner_calls), 1, finished)
        command = runner_calls[0]
        self.assertEqual(
            command[command.index("--result-mode") + 1],
            "ai_trade_council_vote",
        )
        self.assertEqual(
            command[command.index("--council-snapshot-id") + 1],
            snapshot_id,
        )
        self.assertEqual(
            command[command.index("--council-snapshot-digest") + 1],
            snapshot_artifact_digest,
        )
        self.assertEqual(
            command[command.index("--council-role-id") + 1],
            "news",
        )
        self.assertIn("--web-search", command)
        self.assertEqual(finished["status"], "completed")
        self.assertEqual(finished["councilVote"]["snapshotId"], snapshot_id)
        self.assertEqual(finished["execution"]["writeRoots"], [])
        self.assertTrue(finished["webSearchEvidenceVerified"])

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

    def test_web_research_intent_is_routed_only_for_explicit_web_goals(self) -> None:
        self.assertTrue(
            self.bridge.goal_requires_web_research(
                "หา EA จากเว็บไซต์ต่างประเทศ 2 แหล่งและสรุป URL"
            )
        )
        self.assertTrue(
            self.bridge.goal_requires_web_research(
                "Research https://example.com and summarize the public page"
            )
        )
        self.assertFalse(
            self.bridge.goal_requires_web_research(
                "วิเคราะห์ไฟล์ Backtest ที่อยู่ใน Workspace"
            )
        )

    def test_capability_registry_is_contract_owned_sanitized_and_prop_filtered(self) -> None:
        fake_status = {
            "mode": "Codex Runner Ready",
            "status": "guarded",
            "codex": {"status": "ready", "version": "codex-cli 1", "runner": "project_sdk"},
            "mcp": {"status": "config_present", "configPresent": True},
            "time": "2026-07-15T00:00:00+00:00",
        }
        registry = self.bridge.capability_registry(fake_status)
        self.assertEqual(registry["contractVersion"], "tool-permission-contract-v012")
        self.assertFalse(registry["policy"]["frontendSecrets"])
        self.assertTrue(registry["policy"]["disabledToolsFailClosed"])
        telegram = next(item for item in registry["capabilities"] if item["id"] == "send_telegram")
        self.assertFalse(telegram["realExecutionAvailable"])
        self.assertFalse(telegram["autoRunnable"])
        web_research = next(item for item in registry["capabilities"] if item["id"] == "codex_web_research")
        self.assertTrue(web_research["runtimeReady"])
        self.assertTrue(web_research["webSearchEnabled"])
        self.assertEqual(web_research["webSearchMode"], "live")
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
            tracking_key=None,
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
            original_processes = dict(self.bridge.MISSION_WORKER_PROCESSES)
            original_state = dict(self.bridge.MISSION_WORKER_STATE)
            original_terminate = self.bridge._terminate_command_process_tree

            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "bridge-audit.jsonl"
                fake_process = object.__new__(self.bridge.subprocess.Popen)
                fake_process.pid = 424242
                fake_process.poll = lambda: None
                self.bridge.MISSION_WORKER_PROCESS = fake_process
                self.bridge.MISSION_WORKER_JOB_HOLDER = {"fake": True}
                self.bridge.MISSION_WORKER_PROCESSES.clear()
                self.bridge.MISSION_WORKER_PROCESSES["mission-overdue-watchdog"] = {
                    "process": fake_process,
                    "jobHolder": {"fake": True},
                }
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
                self.bridge.MISSION_WORKER_PROCESSES.clear()
                self.bridge.MISSION_WORKER_PROCESSES.update(original_processes)
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

    def test_agent_collaboration_contract_and_frontend_are_backend_owned(self) -> None:
        tools = json.loads(
            (PROJECT_ROOT / "contracts" / "tools" / "tool-permission-contract.json")
            .read_text(encoding="utf-8")
        )
        orchestration = json.loads(
            (PROJECT_ROOT / "contracts" / "orchestration" / "orchestration-contract.json")
            .read_text(encoding="utf-8")
        )
        bridge = json.loads(
            (PROJECT_ROOT / "contracts" / "bridge" / "bridge-contract.json")
            .read_text(encoding="utf-8")
        )
        collaboration = next(item for item in tools["tools"] if item["id"] == "agent_collaboration")
        discovery_lab = next(item for item in tools["tools"] if item["id"] == "discovery_lab_mt4")
        self.assertTrue(collaboration["realExecutionAvailable"])
        self.assertTrue(collaboration["consumesCodexQuota"])
        self.assertFalse(collaboration["toolsEnabled"])
        self.assertFalse(collaboration["taskCreationEnabled"])
        self.assertFalse(discovery_lab["realExecutionAvailable"])
        self.assertFalse(discovery_lab["pluginBindingAvailable"])
        self.assertFalse(discovery_lab["liveTradingAllowed"])
        policy = orchestration["agentCollaboration"]
        self.assertFalse(policy["defaultEnabled"])
        self.assertTrue(policy["freshRateLimitRequiredBeforeEveryTurn"])
        self.assertTrue(policy["managerAlwaysFinalTurn"])
        self.assertFalse(policy["autoCreateFollowup"])
        self.assertIn("GET /api/collaboration/schedule", bridge["endpoints"])
        self.assertIn("POST /api/collaboration/run-now", bridge["endpoints"])

        html = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")
        main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        for element_id in (
            "agentCollabControl",
            "agentCollabPanel",
            "agentCollabTopic",
            "agentCollabRunNow",
            "agentCollabToggle",
        ):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn('const AGENT_COLLABORATION_ENDPOINT = "/api/collaboration/schedule";', main)
        self.assertIn('const AGENT_COLLABORATION_RUN_ENDPOINT = "/api/collaboration/run-now";', main)
        self.assertNotIn("participants:", main[main.index("function collaborationFormPayload"):main.index("async function saveAgentCollaborationSchedule")])
        collaboration_visual_start = main.index("function collaborationOwnsOfficeVisuals()")
        collaboration_visual_end = main.index("\nfunction syncAgentCollaborationVisual(", collaboration_visual_start)
        collaboration_visual_block = main[collaboration_visual_start:collaboration_visual_end]
        self.assertIn("collaboration.enabled", collaboration_visual_block)
        self.assertIn("collaboration.activeMeetingId", collaboration_visual_block)
        self.assertIn('["loading", "starting", "running"].includes(collaboration.status)', collaboration_visual_block)
        bridge_source = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("cancel_event=COLLABORATION_SCHEDULER_STOP", bridge_source)
        self.assertIn("def _record_collaboration_session_failure(", bridge_source)

    def test_collaboration_schedule_validation_persists_only_allowlisted_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            originals = {
                "COLLABORATION_SCHEDULE_PATH": self.bridge.COLLABORATION_SCHEDULE_PATH,
                "OPERATOR_MODE_PATH": self.bridge.OPERATOR_MODE_PATH,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
            }
            with self.bridge.CODEX_RATE_LIMIT_CACHE_LOCK:
                original_cache = dict(self.bridge.CODEX_RATE_LIMIT_CACHE)
                self.bridge.CODEX_RATE_LIMIT_CACHE.update({
                    "payload": {
                        "ok": True,
                        "status": "ready",
                        "primary": {"remainingPercent": 80},
                        "secondary": {"remainingPercent": 70},
                        "limitReached": False,
                        "stale": False,
                    },
                    "fetchedMonotonic": time.monotonic(),
                    "invalidated": False,
                })
            try:
                self.bridge.COLLABORATION_SCHEDULE_PATH = runtime / "collaboration-schedule.json"
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.AUDIT_PATH = runtime / "audit.jsonl"
                self.bridge.write_json(
                    self.bridge.OPERATOR_MODE_PATH,
                    {"mode": "auto_guarded", "updatedAt": self.bridge.utc_now()},
                )
                rejected = self.bridge.set_collaboration_schedule({"participants": ["ceo"]})
                self.assertFalse(rejected["ok"])
                self.assertEqual(rejected["kind"], "invalid_collaboration_schedule_request")
                secret = self.bridge.set_collaboration_schedule({"topic": "api_key=abcdefghijklmnop"})
                self.assertFalse(secret["ok"])
                saved = self.bridge.set_collaboration_schedule({
                    "enabled": True,
                    "topic": "ช่วยกันตรวจ UX รายงาน Backtest ให้คนทั่วไปอ่านเข้าใจได้ง่ายขึ้น",
                    "startTime": "22:00",
                    "endTime": "06:00",
                    "intervalMinutes": 120,
                    "maxTurns": 3,
                    "maxDailyRuns": 2,
                    "minRemainingPercent": 40,
                })
                self.assertTrue(saved["ok"])
                stored = self.bridge.load_collaboration_schedule_store()
                self.assertTrue(stored["config"]["enabled"])
                self.assertEqual(stored["config"]["participants"][-1], "manager")
                self.assertFalse(stored["config"]["autoCreateFollowup"])
                self.assertEqual(stored["config"]["timezone"], "Asia/Bangkok")
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)
                with self.bridge.CODEX_RATE_LIMIT_CACHE_LOCK:
                    self.bridge.CODEX_RATE_LIMIT_CACHE.clear()
                    self.bridge.CODEX_RATE_LIMIT_CACHE.update(original_cache)

    def test_collaboration_window_and_rate_reserve_fail_closed(self) -> None:
        config = {
            "startTime": "22:00",
            "endTime": "06:00",
            "minRemainingPercent": 30,
        }
        self.assertTrue(
            self.bridge._collaboration_inside_window(
                config,
                self.bridge.datetime(2026, 7, 24, 23, 30, tzinfo=self.bridge.THAILAND_TIMEZONE),
            )
        )
        self.assertTrue(
            self.bridge._collaboration_inside_window(
                config,
                self.bridge.datetime(2026, 7, 25, 5, 30, tzinfo=self.bridge.THAILAND_TIMEZONE),
            )
        )
        self.assertFalse(
            self.bridge._collaboration_inside_window(
                config,
                self.bridge.datetime(2026, 7, 25, 12, 0, tzinfo=self.bridge.THAILAND_TIMEZONE),
            )
        )
        original_peek = self.bridge.peek_codex_rate_limits
        try:
            self.bridge.peek_codex_rate_limits = lambda: {
                "ok": True,
                "status": "ready",
                "primary": {"remainingPercent": 70},
                "secondary": {"remainingPercent": 25},
                "limitReached": False,
                "stale": False,
            }
            blocked = self.bridge._collaboration_quota_gate(config, refresh=False)
            self.assertFalse(blocked["allowed"])
            self.assertEqual(blocked["reason"], "quota_below_reserve")
            self.bridge.peek_codex_rate_limits = lambda: {
                "ok": True,
                "status": "ready",
                "primary": {"remainingPercent": 70},
                "limitReached": False,
                "stale": True,
            }
            stale = self.bridge._collaboration_quota_gate(config, refresh=False)
            self.assertFalse(stale["allowed"])
            self.assertEqual(stale["reason"], "quota_stale")
        finally:
            self.bridge.peek_codex_rate_limits = original_peek

    def test_collaboration_runner_strips_task_authority_even_if_chat_classifies_task(self) -> None:
        original_chat = self.runner.run_agent_chat
        try:
            self.runner.run_agent_chat = lambda *args, **kwargs: {
                "ok": True,
                "status": "completed",
                "finalMessage": "เสนอให้เพิ่มการทดสอบ UX ก่อนปล่อยรุ่นถัดไป",
                "intent": "task_request",
                "taskGoal": "create a task",
                "agentName": "EA Developer",
                "durationMs": 12,
                "modelTier": "specialist_fast",
                "model": "gpt-5.5",
                "reasoningEffort": "low",
                "quotaAttempted": True,
                "quotaConsumption": "confirmed",
                "usage": {"outputChars": 48},
                "guardrails": {
                    "toolsEnabled": False,
                    "computerUseEnabled": False,
                    "projectWorkspaceExposed": False,
                    "ephemeral": True,
                },
            }
            result = self.runner.run_agent_collaboration_turn(
                "ช่วยกันทบทวน Product",
                "ea_developer",
                "meeting-test",
            )
            self.assertTrue(result["ok"])
            self.assertFalse(result["taskCreationEnabled"])
            self.assertFalse(result["guardrails"]["taskCreationEnabled"])
            self.assertNotIn("taskGoal", result)
            self.assertNotIn("intent", result)
        finally:
            self.runner.run_agent_chat = original_chat

    def test_collaboration_session_writes_mission_transcript_report_and_manager_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            originals = {
                "RUNTIME_DIR": self.bridge.RUNTIME_DIR,
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "MEMORY_DIR": self.bridge.MEMORY_DIR,
                "MEMORY_INDEX_PATH": self.bridge.MEMORY_INDEX_PATH,
                "MEETING_TRANSCRIPTS_PATH": self.bridge.MEETING_TRANSCRIPTS_PATH,
                "COLLABORATION_SCHEDULE_PATH": self.bridge.COLLABORATION_SCHEDULE_PATH,
                "OPERATOR_MODE_PATH": self.bridge.OPERATOR_MODE_PATH,
                "REAL_RUN_SEMAPHORE": self.bridge.REAL_RUN_SEMAPHORE,
                "_collaboration_quota_gate": self.bridge._collaboration_quota_gate,
                "_run_collaboration_agent_turn": self.bridge._run_collaboration_agent_turn,
            }
            original_runtime_state = dict(self.bridge.COLLABORATION_STATE)
            original_rate_state = dict(self.bridge.RATE_LIMIT_STATE)
            try:
                self.bridge.RUNTIME_DIR = runtime
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "audit.jsonl"
                self.bridge.MEMORY_DIR = runtime / "memory"
                self.bridge.MEMORY_INDEX_PATH = runtime / "memory" / "memory-index.json"
                self.bridge.MEETING_TRANSCRIPTS_PATH = runtime / "memory" / "meetings" / "meeting-transcripts.jsonl"
                self.bridge.COLLABORATION_SCHEDULE_PATH = runtime / "collaboration-schedule.json"
                self.bridge.OPERATOR_MODE_PATH = runtime / "operator-mode.json"
                self.bridge.REAL_RUN_SEMAPHORE = threading.BoundedSemaphore(value=1)
                self.bridge._collaboration_quota_gate = lambda config, refresh: {
                    "allowed": True,
                    "reason": "ready",
                    "remainingPercent": 80,
                }
                self.bridge._run_collaboration_agent_turn = lambda **kwargs: {
                    "ok": True,
                    "status": "completed",
                    "message": (
                        "สรุปให้ทดสอบกับผู้ใช้จริงและวัดเวลาอ่านรายงาน"
                        if kwargs["speaker_agent_id"] == "manager"
                        else f"ข้อเสนอจาก {kwargs['speaker_agent_id']}"
                    ),
                }
                self.bridge.write_json(
                    self.bridge.OPERATOR_MODE_PATH,
                    {"mode": "auto_guarded", "updatedAt": self.bridge.utc_now()},
                )
                store = self.bridge.ensure_collaboration_schedule_store()
                store["config"]["topic"] = "ช่วยกันตรวจรูปแบบรายงาน Backtest ให้เข้าใจง่ายและวัดผลได้"
                store["config"]["maxTurns"] = 3
                store = self.bridge._save_collaboration_schedule_store(store)
                mission = self.bridge.create_mission({
                    "title": "Agent ร่วมประชุม: ทดสอบ",
                    "prompt": store["config"]["topic"],
                    "agentId": "manager",
                    "requester": "manager",
                    "toolId": "agent_collaboration",
                    "targetId": "mission_strategy_table",
                    "risk": "low",
                    "modelTier": "manager_quality",
                    "reportType": "collaboration_report",
                }, status="queued")
                self.assertTrue(self.bridge.COLLABORATION_RUN_LOCK.acquire(blocking=False))
                self.bridge.COLLABORATION_SCHEDULER_STOP.clear()
                self.bridge._complete_collaboration_session("manual", store, mission)

                missions = self.bridge.load_missions()
                self.assertEqual(len(missions), 1)
                self.assertEqual(missions[0]["toolId"], "agent_collaboration")
                self.assertEqual(missions[0]["status"], "completed")
                reports = self.bridge.load_runtime_reports()
                self.assertEqual(len(reports), 1)
                self.assertEqual(reports[0]["type"], "collaboration_report")
                self.assertEqual(reports[0]["linkedPropId"], "mission_strategy_table")
                self.assertFalse(reports[0]["metrics"]["toolsExecuted"])
                meetings = self.bridge.load_meeting_records()
                self.assertTrue(any(item.get("kind") == "meeting" for item in meetings))
                self.assertTrue(any(item.get("kind") == "meeting.turn" for item in meetings))
                final_meeting = next(item for item in meetings if item.get("kind") == "meeting")
                self.assertTrue(final_meeting["decisions"])
                self.assertEqual(final_meeting["status"], "completed")
                audit = self.bridge.tail_jsonl(self.bridge.AUDIT_PATH, limit=100)
                end = next(item for item in audit if item.get("type") == "collaboration.session_end")
                self.assertFalse(end["toolsExecuted"])
                self.assertFalse(end["taskCreated"])
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)
                self.bridge.COLLABORATION_STATE.clear()
                self.bridge.COLLABORATION_STATE.update(original_runtime_state)
                self.bridge.RATE_LIMIT_STATE.clear()
                self.bridge.RATE_LIMIT_STATE.update(original_rate_state)
                self.bridge.COLLABORATION_SCHEDULER_STOP.clear()
                if self.bridge.COLLABORATION_RUN_LOCK.locked():
                    self.bridge.COLLABORATION_RUN_LOCK.release()

    def test_discovery_lab_readiness_never_equates_detection_with_execution(self) -> None:
        readiness = self.bridge._discovery_lab_readiness_read_model(
            "left_analytics_console",
            {
                "platforms": {
                    "mt4": {"installedCount": 4, "runningCount": 0},
                }
            },
            {
                "selectedCandidate": {
                    "candidateId": "mtc-safe",
                    "platform": "mt4",
                    "runningState": "not_running_detected",
                }
            },
        )
        self.assertTrue(readiness["selectedMt4"])
        self.assertFalse(readiness["terminalRunning"])
        self.assertFalse(readiness["pluginBindingAvailable"])
        self.assertFalse(readiness["adapterReady"])
        self.assertFalse(readiness["realExecutionAvailable"])
        self.assertFalse(readiness["liveTradingAllowed"])
        self.assertFalse(readiness["applicable"])
        self.assertEqual(readiness["status"], "not_required")
        self.assertEqual(readiness["stages"], [])

    def test_discovery_lab_best_case_detection_still_requires_missing_adapter(self) -> None:
        readiness = self.bridge._discovery_lab_readiness_read_model(
            "left_analytics_console",
            {
                "platforms": {
                    "mt4": {"installedCount": 4, "runningCount": 1},
                }
            },
            {
                "selectedCandidate": {
                    "candidateId": "mtc-safe",
                    "platform": "mt4",
                    "runningState": "platform_running_detected",
                }
            },
        )
        self.assertTrue(readiness["selectedMt4"])
        self.assertTrue(readiness["terminalRunning"])
        self.assertFalse(readiness["applicable"])
        self.assertEqual(readiness["status"], "not_required")
        self.assertFalse(readiness["pluginBindingAvailable"])
        self.assertFalse(readiness["adapterReady"])
        self.assertFalse(readiness["realExecutionAvailable"])
        self.assertEqual(readiness["stages"], [])
        tools = json.loads(
            (PROJECT_ROOT / "contracts" / "tools" / "tool-permission-contract.json")
            .read_text(encoding="utf-8")
        )
        policy = next(item for item in tools["tools"] if item["id"] == "discovery_lab_mt4")
        self.assertFalse(policy["approvalRequired"])
        self.assertTrue(policy["unavailableDoesNotRequestApproval"])

    def test_real_metatrader_intent_never_falls_through_to_generic_codex_task(self) -> None:
        for goal in (
            "ช่วยรัน Discovery Lab แล้ว Compile EA และทำ Backtest บน MT4",
            "ช่วย Backtest EA ตัวนี้บน MT4",
            "ทดสอบ EA ตัวนี้บน MT4",
            "ช่วย Optimize EA ตัวนี้บน MT4",
        ):
            self.assertEqual(self.bridge.tool_for_agent_goal(goal), "discovery_lab_mt4")
        for goal in (
            "วิเคราะห์รายงาน Backtest ที่แนบมาและสรุป Drawdown",
            "วิเคราะห์รายงาน Discovery Lab ที่แนบมา",
            "วิเคราะห์ผล Backtest EA MT4 จากรายงานเดิม",
            "สรุปรายงานที่ได้จากการ run backtest ให้หน่อย",
            "ตรวจรายงาน Strategy Tester ที่แนบมา",
            "วิเคราะห์ screenshot จาก MetaEditor",
        ):
            self.assertEqual(self.bridge.tool_for_agent_goal(goal), "codex_cli_task")
        for goal in (
            "ช่วยวิเคราะห์รายงานเดิม แล้วรัน Backtest ใหม่บน MT4",
            "วิเคราะห์รายงานเดิม แล้วเปิด MT4",
            "วิเคราะห์รายงานแล้วคอมไพล์ EA",
            "วิเคราะห์รายงานก่อน จากนั้นทำ Backtest ใหม่บน MT4",
            "analyze report then open mt4",
            "analyze report then compile ea",
            "analyze report and backtest this ea",
            "analyze report and optimize this ea",
            "วิเคราะห์รายงานแล้ว Backtest EA บน MT4",
            "วิเคราะห์รายงานแล้ว Optimize EA บน MT4",
        ):
            self.assertEqual(self.bridge.tool_for_agent_goal(goal), "discovery_lab_mt4")
        with tempfile.TemporaryDirectory() as directory:
            original_audit = self.bridge.AUDIT_PATH
            original_missions = self.bridge.MISSIONS_PATH
            try:
                self.bridge.AUDIT_PATH = Path(directory) / "audit.jsonl"
                self.bridge.MISSIONS_PATH = Path(directory) / "missions.json"
                result = self.bridge.run_bridge_task({
                    "agentId": "ea_developer",
                    "toolId": "discovery_lab_mt4",
                    "prompt": "รัน Discovery Lab MT4 แบบ Offline",
                })
                self.assertFalse(result["ok"])
                self.assertEqual(result["kind"], "capability_unavailable")
                self.assertEqual(result["_httpStatus"], 501)
                self.assertFalse(self.bridge.MISSIONS_PATH.exists())
            finally:
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.MISSIONS_PATH = original_missions

    def test_mt_execution_report_defaults_to_analysis_only_without_visible_proof(self) -> None:
        analysis = self.bridge.report_execution_evidence_read_model({}, "backtest_report")
        self.assertEqual(analysis["sourceKind"], "analysis_only")
        self.assertFalse(analysis["mtExecutionVerified"])
        self.assertIn("ยังไม่ได้ยืนยัน", analysis["scopeLabelTh"])
        forged = self.bridge.report_execution_evidence_read_model({
            "sourceKind": "mt4_visible_run",
            "toolId": "discovery_lab_mt4",
            "platform": "mt4",
            "terminalCandidateId": "mtc-safe",
            "compileProofVerified": True,
            "visualBacktestProofVerified": True,
        }, "backtest_report")
        self.assertFalse(forged["mtExecutionVerified"])
        self.assertEqual(forged["sourceKind"], "analysis_only")

        with tempfile.TemporaryDirectory() as directory:
            original_audit = self.bridge.AUDIT_PATH
            original_missions = self.bridge.MISSIONS_PATH
            try:
                self.bridge.AUDIT_PATH = Path(directory) / "audit.jsonl"
                self.bridge.MISSIONS_PATH = Path(directory) / "missions.json"
                mission_id = "mission-visible-mt4-proof"
                verification_id = "mt-proof-a1b2c3"
                self.bridge.write_json(self.bridge.MISSIONS_PATH, {
                    "missions": [{
                        "id": mission_id,
                        "status": "completed",
                        "toolId": "discovery_lab_mt4",
                    }]
                })
                self.bridge.append_audit({
                    "type": "metatrader.execution_verified",
                    "verificationId": verification_id,
                    "missionId": mission_id,
                    "toolId": "discovery_lab_mt4",
                    "platform": "mt4",
                    "terminalCandidateId": "mtc-safe",
                    "status": "completed",
                    "visibleApplicationProof": True,
                    "liveTrading": False,
                    "compileArtifactSha256": "a" * 64,
                    "visualBacktestImageSha256": "b" * 64,
                })
                verified = self.bridge.report_execution_evidence_read_model({
                    "sourceKind": "mt4_visible_run",
                    "toolId": "discovery_lab_mt4",
                    "platform": "mt4",
                    "terminalCandidateId": "mtc-safe",
                    "backendVerificationId": verification_id,
                }, "backtest_report", mission_id)
                self.assertTrue(verified["mtExecutionVerified"])
                self.assertEqual(verified["sourceKind"], "mt4_visible_run")
                self.assertTrue(verified["compileProofVerified"])
                self.assertTrue(verified["visualBacktestProofVerified"])
            finally:
                self.bridge.AUDIT_PATH = original_audit
                self.bridge.MISSIONS_PATH = original_missions

    def test_discovery_lab_is_unavailable_without_requesting_approval(self) -> None:
        bridge_contract = json.loads(
            (PROJECT_ROOT / "contracts" / "bridge" / "bridge-contract.json")
            .read_text(encoding="utf-8")
        )
        self.assertNotIn("discovery_lab_mt4", bridge_contract["approval_required_actions"])

    def test_collaboration_recovery_closes_non_terminal_mission_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            originals = {
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "COLLABORATION_SCHEDULE_PATH": self.bridge.COLLABORATION_SCHEDULE_PATH,
            }
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "audit.jsonl"
                self.bridge.COLLABORATION_SCHEDULE_PATH = runtime / "collaboration-schedule.json"
                self.bridge.write_json(self.bridge.MISSIONS_PATH, {
                    "missions": [{
                        "id": "mission-collab-restart",
                        "title": "Agent ร่วมประชุม",
                        "detail": "ทบทวน Product",
                        "owner": "manager",
                        "toolId": "agent_collaboration",
                        "targetId": "mission_strategy_table",
                        "status": "running",
                        "reportIds": [],
                        "createdAt": self.bridge.utc_now(),
                        "updatedAt": self.bridge.utc_now(),
                    }]
                })
                recovered = self.bridge.recover_interrupted_collaboration_missions()
                self.assertEqual(recovered, 1)
                mission = self.bridge.load_missions()[0]
                self.assertEqual(mission["status"], "failed")
                self.assertEqual(mission["errorCode"], "bridge_restart_interrupted")
                self.assertTrue(mission["reportIds"])
                self.assertEqual(self.bridge.load_runtime_reports()[0]["status"], "blocked")
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)

    def test_collaboration_runner_busy_finishes_as_blocked_instead_of_staying_blue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            originals = {
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "COLLABORATION_SCHEDULE_PATH": self.bridge.COLLABORATION_SCHEDULE_PATH,
                "REAL_RUN_SEMAPHORE": self.bridge.REAL_RUN_SEMAPHORE,
            }
            busy = threading.BoundedSemaphore(value=1)
            busy.acquire()
            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "audit.jsonl"
                self.bridge.COLLABORATION_SCHEDULE_PATH = runtime / "collaboration-schedule.json"
                self.bridge.REAL_RUN_SEMAPHORE = busy
                store = self.bridge.ensure_collaboration_schedule_store()
                mission = self.bridge.create_mission({
                    "title": "Agent ร่วมประชุม: Runner busy",
                    "prompt": store["config"]["topic"],
                    "agentId": "manager",
                    "requester": "manager",
                    "toolId": "agent_collaboration",
                    "targetId": "mission_strategy_table",
                    "risk": "low",
                    "modelTier": "manager_quality",
                    "reportType": "collaboration_report",
                }, status="queued")
                self.assertTrue(self.bridge.COLLABORATION_RUN_LOCK.acquire(blocking=False))
                self.bridge._complete_collaboration_session("manual", store, mission)
                stored = self.bridge.find_mission(mission["id"])
                self.assertEqual(stored["status"], "blocked")
                self.assertEqual(stored["errorCode"], "runner_busy")
                self.assertTrue(stored["reportIds"])
                self.assertFalse(self.bridge.COLLABORATION_RUN_LOCK.locked())
            finally:
                busy.release()
                for name, value in originals.items():
                    setattr(self.bridge, name, value)
                if self.bridge.COLLABORATION_RUN_LOCK.locked():
                    self.bridge.COLLABORATION_RUN_LOCK.release()

    def test_collaboration_queue_rechecks_shutdown_after_gate(self) -> None:
        original_gate = self.bridge._collaboration_gate
        stop_was_set = self.bridge.COLLABORATION_SCHEDULER_STOP.is_set()
        try:
            self.bridge.COLLABORATION_SCHEDULER_STOP.clear()

            def gate_then_stop(*_args, **_kwargs):
                self.bridge.COLLABORATION_SCHEDULER_STOP.set()
                return {"config": {}}, {"allowed": True}

            self.bridge._collaboration_gate = gate_then_stop
            result = self.bridge.queue_collaboration_session("manual")
            self.assertFalse(result["ok"])
            self.assertEqual(result["kind"], "collaboration_stopping")
            self.assertFalse(self.bridge.COLLABORATION_RUN_LOCK.locked())
        finally:
            self.bridge._collaboration_gate = original_gate
            if stop_was_set:
                self.bridge.COLLABORATION_SCHEDULER_STOP.set()
            else:
                self.bridge.COLLABORATION_SCHEDULER_STOP.clear()
            if self.bridge.COLLABORATION_RUN_LOCK.locked():
                self.bridge.COLLABORATION_RUN_LOCK.release()

    def test_collaboration_worker_honors_shutdown_between_semaphore_and_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            originals = {
                "MISSIONS_PATH": self.bridge.MISSIONS_PATH,
                "RUNTIME_REPORTS_DIR": self.bridge.RUNTIME_REPORTS_DIR,
                "AUDIT_PATH": self.bridge.AUDIT_PATH,
                "COLLABORATION_SCHEDULE_PATH": self.bridge.COLLABORATION_SCHEDULE_PATH,
                "REAL_RUN_SEMAPHORE": self.bridge.REAL_RUN_SEMAPHORE,
                "save_missions": self.bridge.save_missions,
            }
            stop_was_set = self.bridge.COLLABORATION_SCHEDULER_STOP.is_set()
            status_writes = []

            class StopOnAcquireSemaphore:
                def acquire(inner_self, blocking=False):
                    self.assertFalse(blocking)
                    with self.bridge.COLLABORATION_STATE_LOCK:
                        self.bridge.COLLABORATION_SCHEDULER_STOP.set()
                    return True

                def release(inner_self):
                    return None

            try:
                self.bridge.MISSIONS_PATH = runtime / "missions.json"
                self.bridge.RUNTIME_REPORTS_DIR = runtime / "reports"
                self.bridge.AUDIT_PATH = runtime / "audit.jsonl"
                self.bridge.COLLABORATION_SCHEDULE_PATH = runtime / "collaboration-schedule.json"
                store = self.bridge.ensure_collaboration_schedule_store()
                mission = self.bridge.create_mission({
                    "title": "Agent collaboration shutdown",
                    "prompt": store["config"]["topic"],
                    "agentId": "manager",
                    "requester": "manager",
                    "toolId": "agent_collaboration",
                    "targetId": "mission_strategy_table",
                    "risk": "low",
                    "reportType": "collaboration_report",
                }, status="queued")
                original_save_missions = self.bridge.save_missions

                def recording_save_missions(missions):
                    status_writes.extend(
                        item.get("status")
                        for item in missions
                        if item.get("id") == mission["id"]
                    )
                    return original_save_missions(missions)

                self.bridge.save_missions = recording_save_missions
                self.bridge.REAL_RUN_SEMAPHORE = StopOnAcquireSemaphore()
                self.assertTrue(self.bridge.COLLABORATION_RUN_LOCK.acquire(blocking=False))
                self.bridge.COLLABORATION_SCHEDULER_STOP.clear()
                self.bridge._complete_collaboration_session("manual", store, mission)
                stored = self.bridge.find_mission(mission["id"])
                self.assertEqual(stored["status"], "blocked")
                self.assertEqual(stored["errorCode"], "bridge_shutdown")
                self.assertNotIn("running", status_writes)
                self.assertFalse(self.bridge.COLLABORATION_RUN_LOCK.locked())
            finally:
                for name, value in originals.items():
                    setattr(self.bridge, name, value)
                if stop_was_set:
                    self.bridge.COLLABORATION_SCHEDULER_STOP.set()
                else:
                    self.bridge.COLLABORATION_SCHEDULER_STOP.clear()
                if self.bridge.COLLABORATION_RUN_LOCK.locked():
                    self.bridge.COLLABORATION_RUN_LOCK.release()

    def test_queued_collaboration_mission_cannot_be_archived(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original_missions = self.bridge.MISSIONS_PATH
            original_audit = self.bridge.AUDIT_PATH
            try:
                self.bridge.MISSIONS_PATH = Path(directory) / "missions.json"
                self.bridge.AUDIT_PATH = Path(directory) / "audit.jsonl"
                mission = self.bridge.create_mission({
                    "title": "Agent collaboration queued",
                    "prompt": "Product review",
                    "agentId": "manager",
                    "requester": "manager",
                    "toolId": "agent_collaboration",
                    "targetId": "mission_strategy_table",
                    "risk": "low",
                    "reportType": "collaboration_report",
                }, status="queued")
                result = self.bridge.archive_mission(mission["id"])
                self.assertFalse(result["ok"])
                self.assertEqual(result["kind"], "mission_active")
                self.assertEqual(self.bridge.find_mission(mission["id"])["status"], "queued")
            finally:
                self.bridge.MISSIONS_PATH = original_missions
                self.bridge.AUDIT_PATH = original_audit

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
