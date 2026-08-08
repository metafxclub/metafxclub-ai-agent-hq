from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
FRONTEND_STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"


def function_block(source: str, signature: str) -> str:
    start = source.index(signature)
    next_function = source.find("\nfunction ", start + len(signature))
    next_async = source.find("\nasync function ", start + len(signature))
    candidates = [value for value in (next_function, next_async) if value >= 0]
    return source[start : min(candidates) if candidates else len(source)]


class FrontendRuntimeTruthRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main = FRONTEND_MAIN_PATH.read_text(encoding="utf-8")
        self.styles = FRONTEND_STYLES_PATH.read_text(encoding="utf-8")

    def test_quote_not_observed_is_plain_thai_with_one_recovery_path(self) -> None:
        reason = function_block(self.main, "function signalExecutionGuardReasonLabel(value)")
        recovery = function_block(self.main, "function signalExecutionGuardRecoveryLabel(value)")
        summary = function_block(self.main, "function signalExecutionGuardSummary(runtime = {})")

        self.assertIn('QUOTE_NOT_OBSERVED: "EA ยังไม่ส่งราคา Bid/Ask ที่ตรวจสอบได้"', reason)
        self.assertIn("หากตลาดปิดให้รอ Tick แรกหลังตลาดเปิด", recovery)
        self.assertIn("ตรวจ Market Watch ว่าราคาเคลื่อนไหว", recovery)
        self.assertIn("Symbol กับ Timeframe ที่อนุญาต", recovery)
        self.assertIn("วิธีแก้:", summary)
        self.assertIn("signalExecutionGuardReasonLabel(runtime.gatewayExecutionGuardReason)", summary)
        self.assertIn("signalExecutionGuardRecoveryLabel(runtime.gatewayExecutionGuardReason)", summary)

    def test_connected_gateway_is_not_presented_as_ready_when_guard_is_blocked(self) -> None:
        runtime = function_block(self.main, "function getSignalRuntimeTruth(report = {})")
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        market_strip = function_block(self.main, "function renderSignalMarketStrip(")
        live = function_block(self.main, "function renderSignalLivePanel(report = {})")
        risk_list = function_block(self.main, "function renderSignalRiskList(")
        decision = function_block(self.main, "function renderSignalDecisionPanel(report = {})")

        self.assertIn("&& (gatewayMode === \"shadow\" || gateway.executionGuardReady === true)", runtime)
        self.assertIn("gateway.executionGuardReady === true", runtime)
        self.assertNotIn('gatewayConnected ? "ready" : "not_connected"', runtime)
        self.assertIn("signalExecutionGuardSummary(runtime)", daily)
        self.assertIn('"สิทธิ์ส่ง Order"', market_strip)
        self.assertIn("runtime.gatewayExecutionGuardReady", market_strip)
        self.assertIn("runtime.gatewayExecutionGuardReady", live)
        self.assertIn("เชื่อม EA แล้ว • ยังไม่พร้อมส่ง Order", live)
        self.assertIn("signalExecutionGuardSummary(runtime)", live)
        self.assertIn("runtime.liveOrderExecutionAvailable && guardReady", risk_list)
        self.assertIn("ยังไม่ส่ง Order •", decision)
        self.assertIn("signalExecutionGuardReasonLabel(runtime.gatewayExecutionGuardReason)", decision)

    def test_terminal_selection_uses_connected_gateway_as_authoritative_truth(self) -> None:
        render = function_block(self.main, "function renderMetatraderSelection(")
        runtime = function_block(self.main, "function getSignalRuntimeTruth(report = {})")

        self.assertIn("connectedGatewayCandidateId", render)
        self.assertIn("authoritativeSelectedId", render)
        self.assertIn("selectionConflict", render)
        self.assertIn("gatewaySelectedCandidateId || checklistSelectedCandidateId", runtime)
        self.assertIn("selectedCandidateId: gatewaySelectedCandidateId || checklistSelectedCandidateId", runtime)

    def test_active_council_round_locks_all_analysis_entry_points(self) -> None:
        model = function_block(self.main, "function signalCouncilRunModel(report = {})")
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        run = function_block(self.main, "async function runAiTradeCouncilAnalysis(snapshotId = \"\")")
        deep = function_block(self.main, "function renderSignalDeepShell(")

        self.assertIn("const activeParent = parents.find", model)
        self.assertIn('signalMissionUiState(item) === "running"', model)
        self.assertIn("hasActiveRound: Boolean(activeParent)", model)
        self.assertIn("councilRun.hasActiveRound", daily)
        self.assertIn("signalCouncilRunModel(refreshedReport).hasActiveRound", run)
        self.assertIn(".hasActiveRound", deep)

    def test_truncated_reason_and_mission_signature_refresh_safely(self) -> None:
        reason = function_block(self.main, "function signalMissionReason(")
        signature = function_block(self.main, "function missionReadModelSignature(missions = [])")

        self.assertIn('resultText !== "[TRUNCATED]"', reason)
        self.assertIn("เปิดรายละเอียด Task เพื่อดูข้อมูลฉบับเต็ม", reason)
        for field in (
            "requester",
            "toolId",
            "reportType",
            "executionMode",
            "workStatus",
            "phase",
            "blocker",
            "webSearchEvidence",
            "evidence",
            "approval",
            "parentMissionId",
            "subtaskIds",
            "reportIds",
        ):
            self.assertIn(f"{field}:", signature)

    def test_compact_dashboard_keeps_tabs_in_two_columns_without_horizontal_scroll(self) -> None:
        compact_query = '@media (max-width: 900px) and (max-height: 640px)'
        start = self.styles.index(compact_query)
        compact = self.styles[start : self.styles.find("\n@media ", start + len(compact_query))]

        self.assertIn(".game-modal.dashboard-modal.signal-consensus-modal .signal-consensus-tabs", compact)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", compact)
        self.assertIn("overflow-x: visible;", compact)
        self.assertIn("grid-template-rows: minmax(118px, 30%) minmax(0, 1fr);", compact)
        self.assertIn("grid-template-columns: 18px minmax(70px, 0.85fr) minmax(0, 1.35fr);", self.styles)
        self.assertIn("overflow-wrap: anywhere;", self.styles)


if __name__ == "__main__":
    unittest.main()
