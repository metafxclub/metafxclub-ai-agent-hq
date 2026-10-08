from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_INDEX = PROJECT_ROOT / "frontend" / "index.html"
FRONTEND_MAIN = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
FRONTEND_STYLES = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"


def function_block(source: str, signature: str) -> str:
    start = source.index(signature)
    next_function = source.find("\nfunction ", start + len(signature))
    next_async = source.find("\nasync function ", start + len(signature))
    candidates = [index for index in (next_function, next_async) if index >= 0]
    return source[start : min(candidates) if candidates else len(source)]


class AiTradeCouncilTerminalSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = FRONTEND_INDEX.read_text(encoding="utf-8")
        cls.main = FRONTEND_MAIN.read_text(encoding="utf-8")
        cls.styles = FRONTEND_STYLES.read_text(encoding="utf-8")

    def test_two_platform_status_cards_and_single_selector_are_in_left_rail(self) -> None:
        rail_index = self.html.index('id="modalDashboardConnectionRail"')
        summary_index = self.html.index('id="modalAiTradeTerminalSummary"')
        details_index = self.html.index('id="modalDashboardConnectionDetails"')
        checklist_index = self.html.index('id="modalDashboardConnectionList"')
        self.assertLess(rail_index, summary_index)
        self.assertLess(summary_index, details_index)
        self.assertLess(details_index, checklist_index)
        for element_id in (
            "modalAiTradeTerminalBadge",
            "modalAiTradeMt4StatusCard",
            "modalAiTradeMt4SelectedBadge",
            "modalAiTradeMt4Health",
            "modalAiTradeMt4Reason",
            "modalAiTradeMt4Fix",
            "modalAiTradeMt5StatusCard",
            "modalAiTradeMt5SelectedBadge",
            "modalAiTradeMt5Health",
            "modalAiTradeMt5Reason",
            "modalAiTradeMt5Fix",
            "modalAiTradePlatformChoice",
            "modalAiTradePlatformMt4",
            "modalAiTradePlatformMt5",
            "modalAiTradeCandidateSelect",
            "modalAiTradeApplySelection",
            "modalAiTradeRefreshPlatforms",
            "modalAiTradeSelectionStatus",
            "modalAiTradeTerminalStatus",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        for retired_id in (
            "modalAiTradeMt4QuickAction",
            "modalAiTradeMt4QuickCandidates",
            "modalAiTradeMt4QuickConfirm",
            "modalAiTradeMt4QuickChannel",
            "modalAiTradeMt4QuickCopy",
            "modalAiTradeActivePlatform",
            "modalAiTradeActiveTerminal",
            "modalAiTradeFeedFreshness",
            "modalAiTradeOpenGlobal",
        ):
            self.assertNotIn(f'id="{retired_id}"', self.html)
        self.assertEqual(self.html.count('name="modalAiTradePlatform"'), 2)
        self.assertIn("สถานะ MT4 / MT5 ของสภา AI Trade", self.html)
        self.assertIn("เลือก Dashboard ที่จะรับข้อมูลและเทรด", self.html)
        self.assertIn("เลือกได้ทีละหนึ่งแพลตฟอร์มเท่านั้น", self.html)
        self.assertIn(".ai-trade-terminal-summary", self.styles)
        self.assertIn(".ai-trade-platform-status-grid", self.styles)
        self.assertIn(".ai-trade-platform-selector", self.styles)
        for state in ("connected", "waiting", "error"):
            self.assertIn(f'[data-state="{state}"]', self.styles)

    def test_left_connection_rail_is_visible_only_for_ai_trade_council(self) -> None:
        modal = function_block(self.main, "function renderGameModal()")
        self.assertIn('surface === "dashboard" && subject.id === AI_TRADE_COUNCIL_PROP_ID', modal)
        self.assertNotIn("els.modalDashboardConnectionRail.hidden = true", modal)

    def test_device_has_no_terminal_discovery_or_selection_logic(self) -> None:
        for retired_function in (
            "getAiTradeMt4SelectionModel",
            "deterministicAiTradeMt4Candidate",
            "prepareAiTradeMt4Channel",
            "confirmAiTradeMt4QuickSelection",
            "discoverMetatraderConnections",
            "confirmMetatraderSelection",
        ):
            self.assertNotIn(f"function {retired_function}(", self.main)
            self.assertNotIn(f"async function {retired_function}(", self.main)
        self.assertNotIn('postJson("/api/integrations/metatrader/discover"', self.main)
        self.assertNotIn('postJson("/api/integrations/metatrader/select"', self.main)

    def test_summary_renders_backend_platform_projection_without_guessing_green(self) -> None:
        render = function_block(
            self.main,
            "function renderAiTradeTerminalSummary(",
        )
        self.assertIn("const applicable = subject?.id === AI_TRADE_COUNCIL_PROP_ID;", render)
        self.assertIn("aiTradePlatformConnectionModels(report || {}, checklist || {})", render)
        self.assertIn("renderAiTradePlatformStatusCard", render)
        self.assertIn("renderAiTradePlatformSelector", render)
        self.assertIn('selected?.state === "connected"', render)
        self.assertIn('selected?.state === "error"', render)
        self.assertIn('item.state === "connected" && !item.selected', render)
        connection_models = function_block(self.main, "function aiTradePlatformConnectionModels(report = {}, checklist = {})")
        self.assertIn("council?.platformConnections", connection_models)
        self.assertIn('["connected", "waiting", "error"]', connection_models)
        self.assertIn("hubSelectedPlatform", connection_models)
        self.assertIn("hubSelectedPlatform === platform", connection_models)
        self.assertIn("hubModelPresent", connection_models)
        self.assertIn("hubSelectedCandidateId", connection_models)
        self.assertIn("selected_candidate_heartbeat_pending", connection_models)
        self.assertIn("suppliedCandidateId !== hubSelectedCandidateId", connection_models)
        self.assertIn("Date.parse", connection_models)
        self.assertIn("AI_TRADE_HEARTBEAT_FRESH_SECONDS", connection_models)
        self.assertIn("gateway_status_stale", connection_models)
        self.assertIn("council_report_refresh_failed", connection_models)
        self.assertIn('reportLoadState.status === "error"', connection_models)
        self.assertIn("reportAuthorityMatches", connection_models)
        self.assertIn("reportCandidateId === expectedCandidateId", connection_models)
        self.assertIn("gatewayHeartbeatFresh", connection_models)
        self.assertIn("Only the selected", connection_models)
        self.assertIn("const connected = reportAuthorityMatches", connection_models)
        for forbidden in (
            "postJson(",
            "signalSnapshotChannel(",
            "modalAiTradeMt4QuickChannel",
            "modalAiTradeMt4QuickCopy",
        ):
            self.assertNotIn(forbidden, render)

    def test_council_heartbeat_is_refreshed_with_the_global_selector_poll(self) -> None:
        polling = function_block(self.main, "function startGlobalMetatraderPolling()")
        self.assertIn("GLOBAL_METATRADER_POLL_MS", polling)
        self.assertIn("state.modal.id === AI_TRADE_COUNCIL_PROP_ID", polling)
        self.assertIn("loadPropReport(AI_TRADE_COUNCIL_PROP_ID)", polling)
        self.assertIn("renderOpenAiTradeTerminalSummary()", polling)

    def test_connected_card_surfaces_execution_guard_reason_and_recovery(self) -> None:
        card = function_block(self.main, "function renderAiTradePlatformStatusCard(model)")
        self.assertIn('model.state === "connected"', card)
        self.assertIn("model.executionGuardReady !== true", card)
        self.assertIn("signalExecutionGuardReasonLabel(model.executionGuardReason)", card)
        self.assertIn("signalExecutionGuardRecoveryLabel(model.executionGuardReason)", card)
        self.assertIn("fix.hidden = !remediation", card)

    def test_connected_cards_schedule_an_exact_expiry_rerender(self) -> None:
        scheduler = function_block(self.main, "function scheduleAiTradeHeartbeatExpiry(")
        self.assertIn('item.state === "connected"', scheduler)
        self.assertIn("item.freshForSeconds", scheduler)
        self.assertIn("item.ageSeconds", scheduler)
        self.assertIn("signalSelectedPlatformConnectionHealth(report)", scheduler)
        self.assertIn("selectedConnectionHealth.expiresInSeconds", scheduler)
        self.assertIn("window.setTimeout", scheduler)
        self.assertIn("renderOpenAiTradeCouncilRuntimeStatus()", scheduler)
        render = function_block(self.main, "function renderAiTradeTerminalSummary(")
        self.assertIn("scheduleAiTradeHeartbeatExpiry(connectionModels, report || {})", render)

    def test_selected_connection_health_is_authoritative_and_non_recursive(self) -> None:
        health = function_block(
            self.main,
            "function signalSelectedPlatformConnectionHealth(report = {})",
        )
        self.assertNotIn("getSignalRuntimeTruth", health)
        self.assertNotIn("aiTradePlatformConnectionModels", health)
        self.assertIn("rawHubModel?.selectedPlatform", health)
        self.assertIn("hubPlatformModel?.selectedCandidate?.candidateId", health)
        self.assertIn("council?.platformConnections", health)
        self.assertIn("expectedCandidateId === suppliedCandidateId", health)
        self.assertIn("Date.parse", health)
        self.assertIn("AI_TRADE_HEARTBEAT_FRESH_SECONDS", health)
        self.assertIn("OPEN_PROP_REPORT_POLL_TTL_MS", health)
        self.assertIn('reportLoadState.status === "error"', health)
        self.assertIn('reasonCode: "selected_candidate_not_configured"', health)
        self.assertIn('"council_report_expired"', health)

    def test_runtime_order_authority_fails_closed_with_selected_connection_health(self) -> None:
        runtime = function_block(self.main, "function getSignalRuntimeTruth(report = {})")
        self.assertIn("signalSelectedPlatformConnectionHealth(report)", runtime)
        self.assertIn(
            "gatewayReportedConnected && selectedConnectionHealth.connected === true",
            runtime,
        )
        self.assertIn(
            "const gatewayExecutionGuardReady = gatewayConnected && gateway.executionGuardReady === true;",
            runtime,
        )
        self.assertIn("selectedConnectionHealth,", runtime)
        self.assertIn("gatewayExecutionGuardReady,", runtime)
        self.assertIn("gatewayMode === \"shadow\" || gatewayExecutionGuardReady", runtime)
        self.assertIn(
            "demoOrderExecutionAvailable: gatewayConnected && gateway.demoOrderExecutionAvailable === true",
            runtime,
        )
        self.assertIn(
            "liveOrderExecutionAvailable: gatewayConnected && gateway.liveOrderExecutionAvailable === true",
            runtime,
        )

    def test_expiry_rerenders_only_runtime_sensitive_council_panels(self) -> None:
        rerender = function_block(self.main, "function renderOpenAiTradeCouncilRuntimeStatus()")
        self.assertIn("renderOpenAiTradeTerminalSummary()", rerender)
        self.assertIn('activeTab === "daily_summary"', rerender)
        self.assertIn('activeTab === "decision_pipeline"', rerender)
        self.assertIn('state.modal.signalLiveTab === "chart_overview"', rerender)
        self.assertIn("renderSignalConsensusPanel(", rerender)
        self.assertNotIn("renderGameModal", rerender)

    def test_left_rail_has_one_shared_atomic_apply_path_and_no_open_global_cta(self) -> None:
        self.assertNotIn('id="modalAiTradeOpenGlobal"', self.html)
        self.assertNotIn('els.modalAiTradeOpenGlobal?.addEventListener("click"', self.main)
        listeners = self.main[self.main.index('els.modalAiTradePlatformChoice?.addEventListener("change"') :]
        self.assertIn('input[name="modalAiTradePlatform"]', listeners)
        self.assertIn("state.globalMetatraderHub.platformChoice = platform", listeners)
        self.assertIn('els.modalAiTradeApplySelection?.addEventListener("click"', listeners)
        self.assertIn("await applyGlobalMetatraderTarget(platform)", listeners)
        self.assertIn('els.modalAiTradeRefreshPlatforms?.addEventListener("click"', listeners)
        self.assertIn("await scanGlobalMetatraderHub()", listeners)
        self.assertEqual(self.main.count('els.modalAiTradeApplySelection?.addEventListener("click"'), 1)
        self.assertEqual(self.main.count("await applyGlobalMetatraderTarget(platform)"), 1)

    def test_daily_summary_is_compact_and_keeps_channel_without_stream_banner(self) -> None:
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        self.assertIn("data-signal-copy-channel", daily)
        self.assertIn("signalSnapshotChannel(report)", daily)
        self.assertIn("data-signal-daily-market-line", daily)
        self.assertIn("`Platform ${platformLabel}`", daily)
        self.assertIn("`คู่เงิน ${market.symbol", daily)
        self.assertIn("`Timeframe ${market.timeframe", daily)
        self.assertNotIn("createSignalStreamContextBanner(report)", daily)
        self.assertNotIn("data-signal-open-metatrader", daily)
        self.assertNotIn("openGlobalMetatraderHubFromDevice(event)", daily)
        self.assertNotIn("prepareAiTradeMt4Channel()", daily)
        self.assertIn("const hubModelPresent = Boolean(", daily)
        self.assertIn("hubReadModel.selectedPlatform", daily)
        self.assertIn('const platformLabel = activePlatform || "MT4 / MT5";', daily)
        self.assertIn('"MetafxHQTradeGateway.mq5"', daily)
        self.assertIn('"MQL5"', daily)

    def test_duplicate_terminal_gateway_rows_are_suppressed_in_council_details(self) -> None:
        render = function_block(self.main, "function renderDashboardConnectionPanel(subject, propertyRole = null)")
        self.assertIn("const isAiTradeCouncil = subject.id === AI_TRADE_COUNCIL_PROP_ID;", render)
        self.assertIn("els.modalDashboardConnectionDetails.hidden = isAiTradeCouncil;", render)
        self.assertIn("els.modalDashboardConnectionDetails.open = !isAiTradeCouncil;", render)
        for item_id in (
            '"mt4_terminal"',
            '"mt5_terminal"',
            '"trading_state_adapter"',
            '"mt4_trade_gateway"',
        ):
            self.assertIn(item_id, render)
        self.assertIn("backendItems.filter", render)
        self.assertIn("councilSummaryItemIds.has", render)

    def test_unreconciled_scan_failure_clears_stale_apply_targets(self) -> None:
        scan = function_block(self.main, "async function scanGlobalMetatraderHub()")
        self.assertIn("hub.readModel = null", scan)
        self.assertIn("hub.checklists = {}", scan)
        self.assertIn('hub.choices = { MT4: "", MT5: "" }', scan)
        selector = function_block(self.main, "function renderAiTradePlatformSelector(")
        self.assertIn("!hub.backendAvailable", selector)


if __name__ == "__main__":
    unittest.main()
