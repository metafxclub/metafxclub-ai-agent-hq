from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"


def function_block(source: str, signature: str) -> str:
    start = source.index(signature)
    next_function = source.find("\nfunction ", start + len(signature))
    next_async = source.find("\nasync function ", start + len(signature))
    candidates = [value for value in (next_function, next_async) if value >= 0]
    return source[start : min(candidates) if candidates else len(source)]


class FrontendSymbolTimeframeContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main = MAIN_PATH.read_text(encoding="utf-8")
        self.styles = STYLES_PATH.read_text(encoding="utf-8")

    def test_history_defaults_to_all_and_persists_explicit_scope(self) -> None:
        self.assertIn('signalHistoryScope: "all"', self.main)
        self.assertIn("signalHistoryScope: state.modal.signalHistoryScope", self.main)
        self.assertIn('["all", "active"].includes(snapshot.modal.signalHistoryScope)', self.main)

    def test_active_context_uses_automation_backend_contract(self) -> None:
        context = function_block(self.main, "function signalActiveStreamContext(report = {})")
        self.assertIn("automationState.activeStream", context)
        self.assertIn("automationState.transition", context)
        self.assertIn("transition.active === true", context)
        self.assertIn("mismatches.length", context)
        self.assertIn("candidateId", context)
        self.assertIn("streamKey", context)
        self.assertIn("symbol", context)
        self.assertIn("timeframe", context)
        stream_source = function_block(self.main, "function signalStreamContextFromSource(")
        self.assertIn("Preserve the broker's exact Symbol", stream_source)
        self.assertNotIn("closedBar.symbol, { uppercase: true }", stream_source)

    def test_current_history_requires_authoritative_backend_scope(self) -> None:
        capability = function_block(self.main, "function signalHistoryScopeCapability(report = {})")
        request = function_block(self.main, "function signalHistoryRequestScope(report = {})")
        self.assertIn("history.scopeCapabilities", capability)
        self.assertIn('advertised.filterStage === "before_summary_and_pagination"', capability)
        self.assertIn("advertised.endpoint === AI_TRADE_COUNCIL_HISTORY_ENDPOINT", capability)
        self.assertIn("scope.authoritative === true", capability)
        self.assertIn('scope.mode', capability)
        self.assertIn("identityReady", capability)
        self.assertIn('return { mode: "all", capability }', request)
        self.assertIn('mode: "active"', request)

    def test_scoped_endpoint_has_optimistic_stream_identity_and_validates_response(self) -> None:
        query = function_block(self.main, "function signalHistoryScopeQuery(report = {})")
        validator = function_block(
            self.main,
            "function signalHistoryResponseMatchesRequest(scope = {}, request = {})",
        )
        loader = function_block(
            self.main,
            "async function loadSignalHistoryPage(kind, report = {}, { firstPage = false } = {})",
        )
        for field in ("candidateId", "streamKey", "symbol", "timeframe"):
            self.assertIn(f'params.set("{field}"', query)
            self.assertIn(f'"{field}"', validator)
        self.assertIn("signalHistoryScopeQuery(report)", loader)
        self.assertIn("signalHistoryResponseMatchesRequest(history.scope, requestScope)", loader)
        self.assertIn("requestGeneration", loader)
        self.assertIn("requestScopeKey", loader)

    def test_global_history_is_loaded_from_authoritative_all_scope(self) -> None:
        merged = function_block(self.main, "function signalHistoryMergedReadModel(report = {}, kind = \"analysis\")")
        loader = function_block(self.main, "function loadSignalHistoryScopeFirstPages(report = {})")
        render = function_block(self.main, "function renderSignalHistoryPanel(")
        self.assertIn("baseScope.authoritative === true", merged)
        self.assertIn("baseScope.mode === requestedScope.mode", merged)
        self.assertNotIn('requestedScope.mode === "all"\n    ||', merged)
        self.assertIn("scopePending: !useLoadedPage && !baseMatchesRequestedScope", merged)
        self.assertIn("signalHistoryRequestScope(report)", loader)
        self.assertIn("loadSignalHistoryScopeFirstPages", render)
        self.assertNotIn("if (nextScope === \"active\")", render)

    def test_consensus_rejects_results_from_another_stream(self) -> None:
        source = function_block(self.main, "function signalCurrentConsensusSource(")
        model = function_block(self.main, "function signalConsensusModel(")
        identity = function_block(self.main, "function signalStreamContextIdentityComplete(context = {})")
        for field in ("candidateId", "streamKey", "symbol", "timeframe", "snapshotId"):
            self.assertIn(f"context.{field}", identity)
        self.assertIn("signalStreamContextIdentityComplete(activeStream)", source)
        self.assertIn("activeStream.stable === true", source)
        self.assertIn("signalStreamContextIdentityComplete(sourceStream)", source)
        self.assertIn("signalStreamContextsMatch(activeStream, sourceStream)", source)
        self.assertIn("item.identityValid !== false", source)
        self.assertIn("signalStreamContextIdentityComplete(activeStream)", model)
        self.assertIn("activeStream.stable === true", model)
        self.assertIn("signalStreamContextIdentityComplete(analyzedStream)", model)
        self.assertIn("matchesCurrentStream", model)
        self.assertIn("&& matchesCurrentStream", model)
        self.assertIn("available && snapshotIdentityAvailable && matchesCurrentSnapshot", model)

    def test_context_ui_is_accessible_and_surfaces_gateway_prerequisites(self) -> None:
        banner = function_block(self.main, "function createSignalStreamContextBanner(")
        self.assertIn('section.setAttribute("role", "status")', banner)
        self.assertIn('section.setAttribute("aria-live", "polite")', banner)
        self.assertIn('controls.setAttribute("role", "group")', banner)
        self.assertIn('button.setAttribute("aria-pressed"', banner)
        self.assertIn("SYMBOL_OR_TIMEFRAME_NOT_ALLOWED", banner)
        self.assertIn("supportedTimeframes", banner)
        self.assertIn("activeButton.disabled = !scopeCapability.available", banner)
        self.assertIn('"AllowedSymbols"', banner)
        self.assertIn('"ManagedMagicNumbers portfolio"', banner)
        self.assertIn('"ขอบเขตการล็อกบัญชี"', banner)
        self.assertIn("portfolioPolicyStatus", banner)
        self.assertIn('["not_ready", "mismatch"].includes(portfolioPolicyStatus)', banner)
        self.assertIn("crossVpsDistributedLock", banner)
        self.assertIn("ห้ามเปิดบัญชีเดียวกันหลาย VPS พร้อมกัน", banner)
        self.assertIn('"Point / Spread / Slippage / Drift"', banner)
        self.assertIn('gatewayCodes.includes("SNAPSHOT_CHANNEL_ALREADY_OWNED")', banner)

    def test_history_labels_scope_and_never_render_global_counts_while_scoped_loading(self) -> None:
        render = function_block(self.main, "function renderSignalHistoryPanel(")
        self.assertIn('scopeLabel = scopeRequest.mode === "active"', render)
        self.assertIn("orderHistory.scopePending", render)
        self.assertIn("canonicalAnalysis.scopePending", render)
        self.assertIn('? "…"', render)
        self.assertIn("createSignalStreamContextBanner(report, { historyControls: true })", render)
        self.assertIn("activeHistoryPageState.sourceReportUpdatedAt !== reportUpdatedAt", render)
        self.assertIn("!activeHistoryPageState.errorMessage", render)

    def test_context_card_has_focus_mobile_and_alert_styles(self) -> None:
        self.assertIn(".signal-stream-context", self.styles)
        self.assertIn('.signal-stream-prerequisite[data-tone="error"]', self.styles)
        self.assertIn(".signal-stream-checklist", self.styles)
        self.assertIn(".signal-history-scope-controls button:focus-visible", self.styles)
        self.assertIn("@media (max-width: 520px)", self.styles)


if __name__ == "__main__":
    unittest.main()
