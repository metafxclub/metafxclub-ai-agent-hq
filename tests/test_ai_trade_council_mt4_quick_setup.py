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

    def test_compact_read_only_status_is_in_left_connection_rail_before_details(self) -> None:
        rail_index = self.html.index('id="modalDashboardConnectionRail"')
        summary_index = self.html.index('id="modalAiTradeTerminalSummary"')
        details_index = self.html.index('id="modalDashboardConnectionDetails"')
        checklist_index = self.html.index('id="modalDashboardConnectionList"')
        self.assertLess(rail_index, summary_index)
        self.assertLess(summary_index, details_index)
        self.assertLess(details_index, checklist_index)
        for element_id in (
            "modalAiTradeTerminalBadge",
            "modalAiTradeActivePlatform",
            "modalAiTradeActiveTerminal",
            "modalAiTradeFeedFreshness",
            "modalAiTradeOpenGlobal",
            "modalAiTradeTerminalStatus",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        for retired_id in (
            "modalAiTradeMt4QuickAction",
            "modalAiTradeMt4QuickCandidates",
            "modalAiTradeMt4QuickConfirm",
            "modalAiTradeMt4QuickChannel",
            "modalAiTradeMt4QuickCopy",
        ):
            self.assertNotIn(f'id="{retired_id}"', self.html)
        self.assertIn("สถานะแหล่งข้อมูลของสภา AI Trade", self.html)
        self.assertIn("อุปกรณ์นี้อ่าน Terminal ที่ยืนยันจากแถบกลางเท่านั้น", self.html)
        self.assertIn(".ai-trade-terminal-summary", self.styles)

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

    def test_summary_reads_either_selected_platform_without_mutation_controls(self) -> None:
        render = function_block(
            self.main,
            "function renderAiTradeTerminalSummary(subject, checklist, canDiscoverMetatrader, report = null)",
        )
        self.assertIn("const applicable = subject?.id === AI_TRADE_COUNCIL_PROP_ID;", render)
        self.assertIn('["MT4", "MT5"].includes(selection.selectedCandidate?.platform)', render)
        self.assertIn("modalAiTradeActivePlatform.textContent", render)
        self.assertIn("modalAiTradeActiveTerminal.textContent", render)
        self.assertIn("modalAiTradeFeedFreshness.textContent", render)
        self.assertIn("signalMarketModel(report || {})", render)
        for forbidden in (
            'input.type = "radio"',
            "postJson(",
            "signalSnapshotChannel(",
            "modalAiTradeMt4QuickChannel",
            "modalAiTradeMt4QuickCopy",
        ):
            self.assertNotIn(forbidden, render)

    def test_device_has_one_change_cta_and_it_only_opens_central_hub(self) -> None:
        self.assertEqual(self.html.count('id="modalAiTradeOpenGlobal"'), 1)
        listener_start = self.main.index('els.modalAiTradeOpenGlobal?.addEventListener("click"')
        listener_end = self.main.index("\n});", listener_start) + len("\n});")
        listener = self.main[listener_start:listener_end]
        self.assertIn("openGlobalMetatraderHubFromDevice(event)", listener)
        self.assertNotIn("postJson", listener)
        open_hub = function_block(self.main, "function openGlobalMetatraderHubFromDevice(event = null)")
        self.assertIn("event?.stopPropagation?.()", open_hub)
        self.assertIn("closeGameModal()", open_hub)
        self.assertIn("setGlobalMetatraderPanelOpen(true)", open_hub)
        self.assertIn("prepareGlobalMetatraderHubOnOpen()", open_hub)

    def test_daily_summary_keeps_channel_setup_but_not_a_second_terminal_cta(self) -> None:
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        self.assertIn("data-signal-copy-channel", daily)
        self.assertIn("signalSnapshotChannel(report)", daily)
        self.assertNotIn("data-signal-open-metatrader", daily)
        self.assertNotIn("openGlobalMetatraderHubFromDevice(event)", daily)
        self.assertNotIn("prepareAiTradeMt4Channel()", daily)
        self.assertIn('const platformLabel = activePlatform || "MT4 / MT5";', daily)
        self.assertIn('"MetafxHQTradeGateway.mq5"', daily)
        self.assertIn('"MQL5"', daily)

    def test_duplicate_terminal_gateway_rows_are_suppressed_in_council_details(self) -> None:
        render = function_block(self.main, "function renderDashboardConnectionPanel(subject, propertyRole = null)")
        self.assertIn(
            "els.modalDashboardConnectionDetails.open = subject.id !== AI_TRADE_COUNCIL_PROP_ID;",
            render,
        )
        for item_id in (
            '"mt4_terminal"',
            '"mt5_terminal"',
            '"trading_state_adapter"',
            '"mt4_trade_gateway"',
        ):
            self.assertIn(item_id, render)
        self.assertIn("backendItems.filter", render)
        self.assertIn("councilSummaryItemIds.has", render)


if __name__ == "__main__":
    unittest.main()
