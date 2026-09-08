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

    def test_compact_read_only_status_is_in_left_connection_rail_before_checklist(self) -> None:
        rail_index = self.html.index('id="modalDashboardConnectionRail"')
        quick_index = self.html.index('id="modalAiTradeMt4QuickSetup"')
        checklist_index = self.html.index('id="modalDashboardConnectionList"')
        self.assertLess(rail_index, quick_index)
        self.assertLess(quick_index, checklist_index)
        for element_id in (
            "modalAiTradeMt4QuickTerminal",
            "modalAiTradeMt4OpenGlobal",
            "modalAiTradeMt4QuickChannel",
            "modalAiTradeMt4QuickCopy",
            "modalAiTradeMt4QuickStatus",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        for retired_id in (
            "modalAiTradeMt4QuickAction",
            "modalAiTradeMt4QuickCandidates",
            "modalAiTradeMt4QuickConfirm",
        ):
            self.assertNotIn(f'id="{retired_id}"', self.html)
        self.assertIn("สถานะ MT4 ของสภา AI Trade", self.html)
        self.assertIn("อุปกรณ์นี้อ่าน Terminal ที่ยืนยันจากแถบกลางเท่านั้น", self.html)
        self.assertIn(".ai-trade-mt4-quick-card", self.styles)

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

    def test_quick_status_stays_visible_and_reads_only_mt4_backend_selection(self) -> None:
        render = function_block(
            self.main,
            "function renderAiTradeMt4QuickSetup(subject, checklist, canDiscoverMetatrader, report = null)",
        )
        self.assertIn("const applicable = subject?.id === AI_TRADE_COUNCIL_PROP_ID;", render)
        self.assertNotIn("&& canDiscoverMetatrader", render)
        self.assertIn('selection.selectedCandidate?.platform === "MT4"', render)
        self.assertIn("Terminal กลาง:", render)
        self.assertIn("แถบเชื่อม MT4 / MT5 ด้านบน", render)
        for forbidden in ('input.type = "radio"', "postJson(", "candidateId ="):
            self.assertNotIn(forbidden, render)

    def test_device_cta_only_opens_the_central_terminal_hub(self) -> None:
        listener_start = self.main.index('els.modalAiTradeMt4OpenGlobal?.addEventListener("click"')
        listener_end = self.main.index("\n});", listener_start) + len("\n});")
        listener = self.main[listener_start:listener_end]
        self.assertIn("openGlobalMetatraderHubFromDevice(event)", listener)
        self.assertNotIn("postJson", listener)
        open_hub = function_block(self.main, "function openGlobalMetatraderHubFromDevice(event = null)")
        self.assertIn("event?.stopPropagation?.()", open_hub)
        self.assertIn("closeGameModal()", open_hub)
        self.assertIn("setGlobalMetatraderPanelOpen(true)", open_hub)
        self.assertIn("prepareGlobalMetatraderHubOnOpen()", open_hub)

    def test_daily_button_routes_to_the_same_central_hub(self) -> None:
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        self.assertIn("data-signal-open-metatrader", daily)
        self.assertIn("openGlobalMetatraderHubFromDevice(event)", daily)
        self.assertNotIn("prepareAiTradeMt4Channel()", daily)
        self.assertNotIn("refreshDashboardConnections(AI_TRADE_COUNCIL_PROP_ID)", daily)

    def test_left_card_displays_only_opaque_channel_and_never_terminal_details(self) -> None:
        render = function_block(
            self.main,
            "function renderAiTradeMt4QuickSetup(subject, checklist, canDiscoverMetatrader, report = null)",
        )
        self.assertIn("signalSnapshotChannel(report || {})", render)
        self.assertIn("modalAiTradeMt4QuickChannel.textContent", render)
        self.assertIn("modalAiTradeMt4QuickCopy.disabled", render)
        for forbidden in ("installPath", "localPath", "terminalPath", "processId", "accountNumber"):
            self.assertNotIn(forbidden, render)


if __name__ == "__main__":
    unittest.main()
