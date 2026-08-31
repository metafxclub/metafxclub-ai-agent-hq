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


class AiTradeCouncilMt4QuickSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = FRONTEND_INDEX.read_text(encoding="utf-8")
        cls.main = FRONTEND_MAIN.read_text(encoding="utf-8")
        cls.styles = FRONTEND_STYLES.read_text(encoding="utf-8")

    def test_compact_setup_is_in_left_connection_rail_before_checklist(self) -> None:
        rail_index = self.html.index('id="modalDashboardConnectionRail"')
        quick_index = self.html.index('id="modalAiTradeMt4QuickSetup"')
        checklist_index = self.html.index('id="modalDashboardConnectionList"')
        self.assertLess(rail_index, quick_index)
        self.assertLess(quick_index, checklist_index)
        for element_id in (
            "modalAiTradeMt4QuickAction",
            "modalAiTradeMt4QuickCandidates",
            "modalAiTradeMt4QuickConfirm",
            "modalAiTradeMt4QuickChannel",
            "modalAiTradeMt4QuickCopy",
            "modalAiTradeMt4QuickStatus",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn("ตรวจ MT4 และสร้าง Channel ID", self.html)
        self.assertIn(".ai-trade-mt4-quick-card", self.styles)

    def test_left_connection_rail_is_visible_only_for_ai_trade_council(self) -> None:
        modal = function_block(self.main, "function renderGameModal()")
        self.assertIn('surface === "dashboard" && subject.id === AI_TRADE_COUNCIL_PROP_ID', modal)
        self.assertNotIn("els.modalDashboardConnectionRail.hidden = true", modal)

    def test_quick_flow_filters_mt5_and_never_randomly_selects_mt4(self) -> None:
        model = function_block(self.main, "function getAiTradeMt4SelectionModel(checklist)")
        choose = function_block(self.main, "function deterministicAiTradeMt4Candidate(selection)")
        prepare = function_block(self.main, "async function prepareAiTradeMt4Channel()")
        discover = function_block(self.main, "async function discoverMetatraderConnections(propId)")

        self.assertIn('candidate.platform === "MT4"', model)
        self.assertIn('runningCandidates.length === 1', choose)
        self.assertIn('detectedCandidates.length === 1', choose)
        self.assertNotIn("Math.random", choose)
        self.assertIn("await discoverMetatraderConnections(AI_TRADE_COUNCIL_PROP_ID)", prepare)
        self.assertIn("deterministicAiTradeMt4Candidate(selection)", prepare)
        self.assertIn("await confirmMetatraderSelection(AI_TRADE_COUNCIL_PROP_ID)", prepare)
        self.assertIn("พบ MT4 ${selection.candidateCount} รายการ", prepare)
        self.assertIn("state.aiTradeMt4QuickSetup.inFlight", prepare)
        self.assertIn("MT5 จะไม่ถูกเลือกในสภา AI Trade", prepare)
        self.assertIn('propId === AI_TRADE_COUNCIL_PROP_ID ? "MT4" : "MT4 / MT5"', discover)
        self.assertIn("ค้นหา ${platformLabel}", discover)

    def test_daily_button_routes_to_same_guarded_setup_helper(self) -> None:
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        self.assertIn("prepareAiTradeMt4Channel()", daily)
        self.assertIn("state.aiTradeMt4QuickSetup?.inFlight", daily)
        self.assertNotIn("refreshDashboardConnections(AI_TRADE_COUNCIL_PROP_ID)", daily)

    def test_left_card_displays_only_opaque_channel_and_guards_double_click(self) -> None:
        render = function_block(
            self.main,
            "function renderAiTradeMt4QuickSetup(subject, checklist, canDiscoverMetatrader, report = null)",
        )
        prepare = function_block(self.main, "async function prepareAiTradeMt4Channel()")
        confirm = function_block(self.main, "async function confirmAiTradeMt4QuickSelection()")
        self.assertIn("signalSnapshotChannel(report || {})", render)
        self.assertIn("selection.candidateCount <= 1", render)
        self.assertIn("modalAiTradeMt4QuickChannel.textContent", render)
        self.assertIn("modalAiTradeMt4QuickCopy.disabled", render)
        self.assertIn("state.aiTradeMt4QuickSetup.inFlight || state.connectionAction.inFlight", prepare)
        self.assertIn("state.aiTradeMt4QuickSetup.inFlight || state.connectionAction.inFlight", confirm)
        for forbidden in ("installPath", "localPath", "terminalPath", "processId", "accountNumber"):
            self.assertNotIn(forbidden, render)


if __name__ == "__main__":
    unittest.main()
