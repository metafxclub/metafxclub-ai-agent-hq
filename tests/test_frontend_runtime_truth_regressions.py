from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
FRONTEND_STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"
FRONTEND_INDEX_PATH = PROJECT_ROOT / "frontend" / "index.html"


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
        self.index = FRONTEND_INDEX_PATH.read_text(encoding="utf-8")

    def node_binary(self) -> str:
        candidates = [
            shutil.which("node"),
            str(
                Path.home()
                / ".cache"
                / "codex-runtimes"
                / "codex-primary-runtime"
                / "dependencies"
                / "node"
                / "bin"
                / "node.exe"
            ),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return candidate
        self.fail("Node.js runtime is required")

    def test_broker_bar_time_keeps_broker_wall_clock_across_local_timezones(self) -> None:
        broker_formatter = function_block(self.main, "function formatBrokerBarTime(value")
        broker_date_time = function_block(self.main, "function signalBrokerDateTime(value)")
        self.assertIn("signalBrokerDateTime(value)", broker_formatter)
        self.assertIn("เวลา Broker", broker_formatter)
        self.assertNotIn("formatThaiDateTime", broker_formatter)

        script = "\n".join(
            [
                broker_date_time,
                broker_formatter,
                "const rawBrokerBarTime = Date.UTC(2026, 7, 13, 9, 30, 0) / 1000;",
                "const brokerDateTime = signalBrokerDateTime(rawBrokerBarTime);",
                "process.stdout.write(JSON.stringify({",
                "  rendered: formatBrokerBarTime(rawBrokerBarTime),",
                "  expected: `เวลา Broker ${brokerDateTime}` ,",
                "  localHour: new Date(rawBrokerBarTime * 1000).getHours(),",
                "  fallback: formatBrokerBarTime(0, 'fallback'),",
                "}));",
            ]
        )

        def render_in(timezone: str) -> dict[str, object]:
            result = subprocess.run(
                [self.node_binary(), "-e", script],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "TZ": timezone},
            )
            return json.loads(result.stdout)

        utc_plus_three = render_in("Etc/GMT-3")
        utc_minus_five = render_in("Etc/GMT+5")

        self.assertEqual(utc_plus_three["localHour"], 12)
        self.assertEqual(utc_minus_five["localHour"], 4)
        self.assertEqual(utc_plus_three["rendered"], utc_plus_three["expected"])
        self.assertEqual(utc_minus_five["rendered"], utc_minus_five["expected"])
        self.assertEqual(utc_plus_three["rendered"], utc_minus_five["rendered"])
        self.assertEqual(utc_plus_three["fallback"], "fallback")
        self.assertEqual(utc_minus_five["fallback"], "fallback")

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

    def test_max_managed_orders_control_is_an_ai_dispatch_cap_not_an_ea_ack(self) -> None:
        automation = function_block(
            self.main,
            "function signalCouncilAutomationModel(report = {})",
        )
        limit_model = function_block(
            self.main,
            "function signalManagedOrderLimitModel(report = {}, runtime = getSignalRuntimeTruth(report))",
        )
        live = function_block(self.main, "function renderSignalLivePanel(report = {})")
        setter = function_block(
            self.main,
            "async function setAiTradeCouncilMaxManagedOrders(maxManagedOrders)",
        )

        self.assertIn("allowedMaxManagedOrders", automation)
        self.assertIn("[1, 3, 5, 10]", automation)
        self.assertIn("maxManagedOrders", automation)
        self.assertIn("data-signal-max-managed-orders", live)
        self.assertIn("[1, 3, 5, 10]", live)
        self.assertIn("configuredMaxManagedOrders", limit_model)
        self.assertIn("eaMaxManagedPositions", limit_model)
        self.assertIn("effectiveMaxManagedOrders", limit_model)
        self.assertIn('source === "backend_dispatch_cap"', limit_model)
        self.assertIn("maxManagedOrders: nextMaxManagedOrders", setter)
        self.assertIn('postJson("/api/ai-trade-council/automation"', setter)

        # This is a Backend pre-dispatch cap.  It must never be presented as
        # an EA-applied setting or inferred from an order ACK.
        self.assertNotIn("ackStatus", limit_model)
        self.assertNotIn("orderExecutionConfirmed", limit_model)
        control_start = live.index('data-signal-max-managed-orders')
        control_end = live.find("</section>", control_start)
        control = live[control_start : control_end if control_end >= 0 else len(live)]
        self.assertNotIn("EA ACK", control)
        self.assertNotIn("EA ยืนยันแล้ว", control)

    def test_council_config_setters_post_partial_updates_and_share_one_race_guard(self) -> None:
        automation = function_block(
            self.main,
            "async function setAiTradeCouncilAutomation(enabled, configOverrides = {})",
        )
        votes = function_block(
            self.main,
            "async function setAiTradeCouncilRequiredVotes(requiredVotes)",
        )
        max_orders = function_block(
            self.main,
            "async function setAiTradeCouncilMaxManagedOrders(maxManagedOrders)",
        )
        setters = (automation, votes, max_orders)

        # Every setter must lock against every other setter before reading the
        # current report. Otherwise two quick clicks can race and restore a
        # stale sibling value.
        for setter in setters:
            with self.subTest(setter=setter.splitlines()[0]):
                self.assertIn("state.aiTradeCouncilAutomation.inFlight", setter)
                self.assertIn("state.aiTradeCouncilConsensusPolicy.inFlight", setter)
                self.assertIn("state.aiTradeCouncilOrderLimit.inFlight", setter)

        # The backend accepts partial updates, so setters must not echo a stale
        # full config snapshot. Automation may update enabled and, when the
        # caller explicitly supplies it, analysisBarCount; the other controls
        # each own exactly one field.
        self.assertIn('postJson("/api/ai-trade-council/automation"', automation)
        self.assertIn("enabled: Boolean(enabled)", automation)
        self.assertIn("analysisBarCount", automation)
        for stale_key in (
            "maxDailyRounds:",
            "minRemainingPercent:",
            "requiredVotes:",
            "maxManagedOrders:",
        ):
            self.assertNotIn(stale_key, automation)

        self.assertIn('postJson("/api/ai-trade-council/automation"', votes)
        self.assertIn("requiredVotes: nextRequiredVotes", votes)
        for stale_key in (
            "enabled:",
            "maxDailyRounds:",
            "minRemainingPercent:",
            "analysisBarCount:",
            "maxManagedOrders:",
        ):
            self.assertNotIn(stale_key, votes)

        self.assertIn('postJson("/api/ai-trade-council/automation"', max_orders)
        self.assertIn("maxManagedOrders: nextMaxManagedOrders", max_orders)
        for stale_key in (
            "enabled:",
            "maxDailyRounds:",
            "minRemainingPercent:",
            "analysisBarCount:",
            "requiredVotes:",
        ):
            self.assertNotIn(stale_key, max_orders)

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

    def test_new_closed_bar_does_not_reuse_a_historical_council_round(self) -> None:
        automation = function_block(self.main, "function signalCouncilAutomationModel(report = {})")
        model = function_block(self.main, "function signalCouncilRunModel(report = {})")
        views = function_block(self.main, "function signalAgentViews(report = {}, runtime = getSignalRuntimeTruth(report))")

        self.assertIn("lastMissionId,", automation)
        self.assertIn("newBarPending,", automation)
        self.assertIn("lastObservedClosedBarTime > lastAnalyzedClosedBarTime", automation)
        self.assertIn('const currentRun = pipeline.currentRun && typeof pipeline.currentRun === "object"', model)
        self.assertIn("const activeParent = parents.find", model)
        self.assertIn("const automationParent = automation.lastMissionId", model)
        self.assertIn("const waitingForCurrentRound = automation.newBarPending === true && !activeParent;", model)
        self.assertIn('state: "waiting_current_round"', model)
        self.assertIn("children: []", model)
        self.assertIn("byAgent: new Map()", model)
        self.assertIn(
            "const parent = activeParent\n    || currentRunParent\n    || automationParent\n    || consensusParent",
            model,
        )
        self.assertIn('String(item?.parentMissionId || "") === parentId', model)
        self.assertIn('run.state === "waiting_current_round"', views)
        self.assertIn("? run.reason", views)

    def test_newer_blocked_last_mission_wins_an_old_completed_consensus(self) -> None:
        model = function_block(self.main, "function signalCouncilRunModel(report = {})")

        self.assertIn("const consensusParentId = safeDashboardDisplayText(", model)
        self.assertIn("const automationParent = automation.lastMissionId", model)
        self.assertIn("const consensusParent = !automation.lastMissionId && consensusParentId", model)
        selection = "const parent = activeParent\n    || currentRunParent\n    || automationParent\n    || consensusParent"
        self.assertIn(selection, model)
        selection_block = model[
            model.index("const parent = activeParent") : model.index("const parentId =")
        ]
        self.assertLess(
            selection_block.index("|| automationParent"),
            selection_block.index("|| consensusParent"),
        )

    def test_disabled_automation_ignores_stale_closed_bar_timestamps(self) -> None:
        automation = function_block(self.main, "function signalCouncilAutomationModel(report = {})")

        self.assertIn("const newBarPending = enabled && (", automation)
        self.assertIn("pendingCount > 0", automation)
        self.assertIn("lastObservedClosedBarTime !== null", automation)

    def test_closed_bar_automation_presents_unlimited_backend_policy_truthfully(self) -> None:
        automation = function_block(self.main, "function signalCouncilAutomationModel(report = {})")
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        round_health = function_block(self.main, "function signalRoundHealthModel(")

        self.assertIn("dailyRoundLimitMode", automation)
        self.assertIn("dailyRoundLimitEnabled", automation)
        self.assertIn("effectiveMaxDailyRounds", automation)
        self.assertIn('dailyRoundLimitMode === "limited"', automation)
        self.assertIn("staleDailyLimitReasons.has(rawReason)", automation)
        self.assertIn('waiting_for_new_closed_bar: "แท่งปัจจุบันยังไม่ปิด', automation)
        self.assertIn('watching: "เปิดอยู่ • เฝ้าแท่งปิดใหม่"', automation)
        self.assertIn("const statusLabel = !enabled", automation)
        self.assertIn(": blocked", automation)

        self.assertIn("แท่งปิดใหม่ • วันนี้", daily)
        self.assertIn("ไม่มีเพดานรายวัน", daily)
        self.assertIn("เมื่อพบแท่งปิดใหม่จะเริ่มวิเคราะห์เมื่อระบบพร้อม", daily)
        self.assertIn("ทุกแท่งจะเข้าคิวถาวรตามลำดับ FIFO", daily)
        self.assertIn("ประมวลผลคิวแท่งปิดตามลำดับ FIFO", daily)
        self.assertIn("ห้ามส่ง Order เก่า", daily)
        self.assertNotIn("ใช้รอบล่าสุดเท่านั้น", daily)
        self.assertNotIn("${automation.dailyRunCount}/${automation.maxDailyRounds}", daily)

        self.assertIn('label: "รอบวิเคราะห์แท่งปิด"', round_health)
        self.assertIn("ไม่จำกัด • วันนี้", round_health)
        self.assertIn("แท่งปิดใหม่จะเริ่มวิเคราะห์เมื่อระบบพร้อม", round_health)
        self.assertIn("คิวถาวรตามลำดับ FIFO", round_health)
        self.assertNotIn('label: "Quota วันนี้"', round_health)

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

    def test_order_history_uses_ea_executions_not_current_votes(self) -> None:
        base = function_block(self.main, "function signalHistoryBaseReadModel(report = {}, kind = \"analysis\")")
        entries = function_block(self.main, "function signalOrderHistoryEntries(report = {}, readModel = null)")
        number = function_block(self.main, "function signalOrderNumber(value, maximumFractionDigits = 5)")
        thai_time = function_block(self.main, "function signalThaiDateTime(value)")
        row = function_block(self.main, "function createSignalOrderHistoryRow(order)")
        panel = function_block(self.main, "function renderSignalHistoryPanel(report = {}, { focusSearch = false } = {})")

        self.assertIn("council?.history?.orderExecutions", base)
        self.assertIn('signalHistoryMergedReadModel(report, "orders")', entries)
        self.assertIn('value === null || value === undefined || value === ""', number)
        self.assertIn('timeZone: "Asia/Bangkok"', thai_time)
        self.assertIn("order.openedAt", row)
        self.assertIn("order.brokerOpenedAt", row)
        self.assertIn("order.reasonTh", row)
        self.assertIn("order.voteSummaryTh", row)
        self.assertIn("order.ticket", row)
        self.assertIn("order.verified === true", row)
        self.assertIn("order.mode", row)
        self.assertIn("String(order.mode).toUpperCase()", row)
        self.assertIn("signalOrderOpenedTime(right) - signalOrderOpenedTime(left)", panel)
        self.assertIn("data-signal-history-list", panel)
        self.assertIn('row.dataset.verified = order.verified === true ? "true" : "false"', row)
        self.assertIn('.signal-order-history-row[data-verified="false"]', self.styles)
        self.assertIn("var(--amber)", self.styles)
        self.assertIn(
            "if (!focusSearch && query && allOrders.length && !filtered.length)",
            panel,
        )
        self.assertIn('state.modal.signalHistoryQuery = "";', panel)
        self.assertIn("filtered = allOrders.slice();", panel)
        self.assertNotIn("signalAgentViews(", panel)

    def test_history_has_exactly_two_nested_views_and_per_bar_agent_truth(self) -> None:
        panel = function_block(
            self.main,
            "function renderSignalHistoryPanel(report = {}, { focusSearch = false } = {})",
        )
        sources = function_block(self.main, "function signalHistoryAnalysisSources(report = {}, canonicalOverride = null)")
        timestamp = function_block(self.main, "function signalHistoryTimestamp(...values)")
        final = function_block(self.main, "function signalHistoryFinalDecision(source = {})")
        order = function_block(self.main, "function signalHistoryOrderState(")
        normalize = function_block(self.main, "function signalHistoryNormalizeRound(")
        vote = function_block(self.main, "function signalHistoryVote(value = {}, fallbackRole = \"\")")
        row = function_block(self.main, "function createSignalAnalysisHistoryRow(round)")

        self.assertIn('const SIGNAL_HISTORY_TABS = ["orders", "analysis"]', self.main)
        self.assertEqual(panel.count('data-signal-history-tab="'), 2)
        self.assertIn("ประวัติการเปิดออเดอร์", panel)
        self.assertIn("ประวัติการวิเคราะห์", panel)
        self.assertIn("data-signal-analysis-round-list", panel)
        for heading in (
            "เวลาแท่ง",
            "สัญลักษณ์",
            "TF",
            "Technical",
            "Price Action",
            "ข่าว",
            "มติสุดท้าย",
            "Order",
        ):
            self.assertIn(heading, panel)

        # New canonical aliases are preferred, while the bounded legacy report
        # and decision-pipeline forms remain readable during upgrades.
        for alias in (
            "analysisRounds",
            "barAnalysisRounds",
            "councilRounds",
            "analysisDecisions",
            "tradingReports",
            "decisionPipeline",
        ):
            self.assertIn(alias, sources)
        self.assertIn('const finalDecision = signalHistoryFinalDecision(source) || "NO_DATA";', normalize)
        self.assertIn("source.timestamp", normalize)
        self.assertIn("metrics.timestamp", normalize)
        self.assertIn("source.skipReasonCode", normalize)
        self.assertIn("roundSkipped", normalize)
        self.assertIn("roundPending", normalize)
        self.assertIn("numeric * 1000", timestamp)
        self.assertIn("consensus.decision", final)
        self.assertIn("source.orderLinkage", order)
        self.assertIn("linkage.available === true", order)
        self.assertIn("linkage.ticket", order)
        self.assertIn("linkage.commandId", order)
        self.assertIn("พบ Order • หลักฐานยังไม่ครบ", order)
        self.assertNotIn('|| "HOLD"', vote)
        self.assertIn('complete: ["BUY", "SELL", "HOLD"].includes(decision)', vote)
        self.assertIn('createSignalAnalysisVoteCell(round.votes.technical, "Technical")', row)
        self.assertIn('createSignalAnalysisVoteCell(round.votes.price_action, "Price Action")', row)
        self.assertIn('createSignalAnalysisVoteCell(round.votes.news, "ข่าว")', row)
        self.assertIn("round.roundSkipped", row)
        self.assertIn("round.roundFailed", row)
        self.assertIn('"ล้มเหลว"', row)
        self.assertIn("round.skipReason", row)
        self.assertIn("เวลาที่ Backend บันทึก", row)

    def test_analysis_history_summary_and_mobile_layout_are_readable(self) -> None:
        panel = function_block(
            self.main,
            "function renderSignalHistoryPanel(report = {}, { focusSearch = false } = {})",
        )
        summary = function_block(
            self.main,
            "function signalAnalysisHistorySummary(report = {}, rounds = [], canonicalOverride = null)",
        )

        for selector in (
            "data-signal-analysis-total",
            "data-signal-analysis-complete",
            "data-signal-analysis-no-trade",
            "data-signal-analysis-no-data",
            "data-signal-analysis-buy",
            "data-signal-analysis-sell",
            "data-signal-analysis-attention",
        ):
            self.assertIn(selector, panel)
        self.assertIn("canonicalHistory.summary", summary)
        self.assertIn("history.analysisSummary", summary)
        self.assertIn("history.analysisHistorySummary", summary)
        self.assertIn('"expected"', summary)
        self.assertIn("supplied.analyzed", summary)
        self.assertIn("supplied.skipped", summary)
        self.assertIn("supplied.pending", summary)
        self.assertIn("supplied.completeThreeOfThree", summary)
        self.assertIn('["HOLD", "NO_TRADE"].includes(round.finalDecision)', summary)
        self.assertNotIn('["HOLD", "NO_TRADE", "NO_DATA"]', summary)

        responsive = self.styles[self.styles.rfind("@media (max-width: 900px)") :]
        self.assertIn(".signal-analysis-round-head", responsive)
        self.assertIn("display: none;", responsive)
        self.assertIn("content: attr(data-label);", responsive)
        self.assertIn("@media (max-width: 520px)", responsive)
        self.assertIn("grid-template-columns: minmax(0, 1fr);", responsive)
        self.assertIn("font-size: 12px;", self.styles)
        self.assertIn("font-size: 11px;", self.styles)

    def test_pending_and_skipped_analysis_rows_never_claim_hold_consensus(self) -> None:
        order = function_block(self.main, "function signalHistoryOrderState(")

        self.assertIn('coverageStatus === "skipped"', order)
        self.assertIn("source.skipReasonCode", order)
        self.assertIn('label: "ข้ามรอบ • ไม่มีคำสั่ง"', order)
        self.assertIn('detail: reason || "Backend ข้ามรอบนี้ก่อนการลงมติ"', order)
        self.assertIn('["pending", "queued", "running", "settling", "waiting"].includes(coverageStatus)', order)
        self.assertIn('label: running ? "กำลังวิเคราะห์ • ยังไม่มีคำสั่ง" : "รอวิเคราะห์ • ยังไม่มีคำสั่ง"', order)
        self.assertIn('label: "ยังไม่ประเมินคำสั่ง"', order)
        self.assertIn('"แท่งนี้อยู่ในคิว FIFO และยังไม่เริ่มลงมติ"', order)
        self.assertIn('if (["HOLD", "NO_TRADE"].includes(finalDecision))', order)
        self.assertEqual(order.count('detail: "มติเป็น HOLD / NO TRADE"'), 1)
        self.assertIn('detail: "ยังไม่มีมติสุดท้ายจาก Backend"', order)

    def test_waiting_gate_and_fifo_queue_contract_are_mapped_without_guessing(self) -> None:
        automation = function_block(self.main, "function signalCouncilAutomationModel(report = {})")

        self.assertIn("runtimeState.reasonCode", automation)
        self.assertIn("waitingGate.reasonCode", automation)
        self.assertIn('quota_below_reserve: "พักการวิเคราะห์', automation)
        self.assertIn('quota_limit_reached: "โควตา Codex ถึงขีดจำกัดแล้ว', automation)
        self.assertIn('"waiting_gate"', automation)
        self.assertIn("runtimeState.pendingCount", automation)
        self.assertIn("pending.queuePosition", automation)
        self.assertIn("pending.queueDepth", automation)
        self.assertIn("pending.detectedAt", automation)
        self.assertIn("waitingGateActive", automation)
        self.assertIn("backlogPolicy", automation)
        daily = function_block(self.main, "function renderSignalDailyPanel(report = {})")
        self.assertIn("automation.pendingCount > 0", daily)
        self.assertIn("รอคิว ${automation.pendingCount} แท่ง", daily)
        self.assertIn("แท่งเก่าสุด ${formatBrokerBarTime(automation.pending.closedBarTime)}", daily)
        self.assertIn("รอตั้งแต่ ${formatThaiDateTime(automation.pending.detectedAt)}", daily)

    def test_skipped_durable_snapshot_state_is_fail_closed_and_never_claims_watching(self) -> None:
        automation = function_block(self.main, "function signalCouncilAutomationModel(report = {})")

        self.assertIn('durable_snapshot_unavailable: "หยุดรอบอัตโนมัติชั่วคราว', automation)
        self.assertIn('"durable_snapshot_unavailable"', automation)
        self.assertIn('"snapshot_artifact_capture_failed"', automation)
        self.assertIn('"pending_queue_capacity_exceeded"', automation)
        self.assertIn('"timeframe_not_supported"', automation)
        self.assertIn('"skipped"', automation)
        self.assertIn('skipped: "รอบล่าสุดถูกข้าม', automation)

    def test_history_pages_use_backend_cursor_and_attempt_identity(self) -> None:
        key = function_block(
            self.main,
            'function signalHistoryAttemptKey(item = {}, kind = "analysis", index = 0)',
        )
        loader = function_block(
            self.main,
            'async function loadSignalHistoryPage(kind, report = {}, { firstPage = false } = {})',
        )
        entries = function_block(
            self.main,
            "function signalAnalysisHistoryEntries(report = {}, canonicalOverride = null, orderOverride = null)",
        )
        order_link = function_block(self.main, "function signalHistoryOrderState(")

        self.assertIn("item.attemptId", key)
        self.assertIn("`attempt:${attemptId}`", key)
        self.assertNotIn("item.snapshotId", key)
        self.assertIn("AI_TRADE_COUNCIL_HISTORY_ENDPOINT", loader)
        self.assertIn('params.set("kind", kind)', loader)
        self.assertIn('params.set("limit", "50")', loader)
        self.assertIn('if (cursor) params.set("cursor", cursor)', loader)
        self.assertIn("signalHistoryScopeQuery(report)", loader)
        self.assertIn("signalHistoryResponseMatchesRequest(history.scope, requestScope)", loader)
        self.assertIn("history.nextCursor || history.page?.nextCursor", loader)
        self.assertIn("nextCursor === cursor", loader)
        self.assertIn("source.attemptId", entries)
        self.assertIn("`attempt:${attemptId}`", entries)
        self.assertNotIn("identity.snapshotId ||", entries)
        self.assertIn("hasCanonicalReadModel", entries)
        self.assertIn("? [...canonicalRounds]", entries)
        self.assertIn("order.missionId || order.linkedMissionId", order_link)
        self.assertIn("!safeDashboardDisplayText(order.missionId || order.linkedMissionId", order_link)
        self.assertIn("legacySnapshotMatches.length === 1", order_link)

    def test_analysis_summary_uses_one_canonical_attempt_source_before_paging(self) -> None:
        summary = function_block(
            self.main,
            "function signalAnalysisHistorySummary(report = {}, rounds = [], canonicalOverride = null)",
        )

        self.assertIn('supplied.source === "canonical_attempt_rows_before_pagination"', summary)
        self.assertIn('["completeThreeOfThree", "complete", "completeRounds"]', summary)
        self.assertIn('["partialTerminal"]', summary)
        self.assertIn('["waiting"]', summary)
        self.assertIn('["running"]', summary)
        self.assertIn("decisionCounts.NO_TRADE", summary)
        self.assertIn("decisionCounts.NO_DATA", summary)
        self.assertIn("exactTotal: true", summary)

    def test_history_modal_keyboard_and_list_semantics_are_explicit(self) -> None:
        panel = function_block(
            self.main,
            "function renderSignalHistoryPanel(report = {}, { focusSearch = false } = {})",
        )
        trap = function_block(self.main, "function trapGameModalFocus(event)")
        analysis_row = function_block(self.main, "function createSignalAnalysisHistoryRow(round)")
        order_row = function_block(self.main, "function createSignalOrderHistoryRow(order)")

        self.assertIn('aria-labelledby="modalTitle"', self.index)
        self.assertIn('tabindex="-1"', self.index)
        self.assertIn('role="tablist"', panel)
        self.assertIn('role="tabpanel"', panel)
        self.assertIn('event.key === "ArrowRight"', panel)
        self.assertIn('event.key === "ArrowLeft"', panel)
        self.assertIn('event.key === "Home"', panel)
        self.assertIn('event.key === "End"', panel)
        self.assertIn('row.setAttribute("role", "listitem")', analysis_row)
        self.assertIn('row.setAttribute("role", "listitem")', order_row)
        self.assertIn('event.key === "Escape"', trap)
        self.assertIn('event.key !== "Tab"', trap)
        self.assertIn("gameModalFocusableElements()", trap)

    def test_closed_modal_is_inert_and_focus_returns_to_the_opened_subject(self) -> None:
        self.assertIn('id="gameModal"', self.index)
        modal_start = self.index.index('id="gameModal"')
        game_modal_tag = self.index[modal_start : self.index.index('>', modal_start)]
        self.assertIn(" inert", game_modal_tag)

        opened = function_block(self.main, "function openGameModal(")
        closed = function_block(self.main, "function closeGameModal(")
        self.assertIn('els.gameModal?.removeAttribute("inert")', opened)
        self.assertIn('els.gameModal?.setAttribute("inert", "")', closed)
        self.assertIn('node.dataset.id === closingId', closed)
        self.assertIn('node.dataset.agentId === closingId', closed)
        self.assertIn("savedReturnTarget || semanticReturnTarget", closed)

    def test_radar_website_tool_has_an_eleven_pixel_text_floor(self) -> None:
        radar_start = self.styles.index(".workflow-radar-website-tool")
        radar_end = self.styles.index(".workflow-truth-empty", radar_start)
        radar = self.styles[radar_start:radar_end]

        self.assertIn(".workflow-radar-card dt,", radar)
        self.assertIn(".workflow-radar-card dd", radar)
        self.assertNotIn("font-size: 7px", radar)
        self.assertNotIn("font-size: 8px", radar)
        self.assertNotIn("font-size: 9px", radar)
        self.assertNotIn("font-size: 10px", radar)

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
