import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend" / "src" / "app" / "styles.css").read_text(encoding="utf-8")

    def block(self, start, end):
        start_index = self.main.index(start)
        return self.main[start_index:self.main.index(end, start_index)]

    def test_factory_has_seven_manual_presentation_tabs_and_six_backend_stages(self):
        constants = self.block("const EA_FACTORY_STAGE_IDS", "const TRADING_RESEARCH_MAX_OHLC_ROWS")
        ui_ids = re.findall(r'^\s+"([a-z_]+)",?$', constants[constants.index("Object.freeze(["):constants.index("]);", constants.index("Object.freeze(["))], re.M)
        self.assertEqual(
            ui_ids,
            [
                "source",
                "spec",
                "generate",
                "review",
                "compile_validate",
                "backtest_recheck",
                "artifacts_report",
            ],
        )
        for ui_id, backend_id in {
            "spec": "strategy_spec",
            "generate": "generate_source",
            "review": "source_review",
            "compile_validate": "compile_validate",
            "backtest_recheck": "backtest_recheck",
            "artifacts_report": "final_report",
        }.items():
            self.assertIn(f'{ui_id}: "{backend_id}"', constants)
        self.assertIn("Manual Stage-by-Stage • ไม่มี Scheduler / Loop", self.main)

    def test_sheet_source_uses_exact_a_w_and_posts_opaque_source_record_id(self):
        constants = self.block("const EA_FACTORY_SHEET_COLUMNS", "const TRADING_RESEARCH_MAX_OHLC_ROWS")
        columns = re.findall(r'\["([A-W])", "([a-z_]+)"\]', constants)
        self.assertEqual(len(columns), 23)
        self.assertEqual("".join(letter for letter, _ in columns), "ABCDEFGHIJKLMNOPQRSTUVW")
        self.assertEqual(dict(columns)["F"], "entry_rules")
        self.assertEqual(dict(columns)["G"], "exit_rules")
        self.assertEqual(dict(columns)["J"], "recovery")
        self.assertEqual(dict(columns)["K"], "lot_risk")

        normalizer = self.block("function normalizeEaFactorySourceRecord", "function normalizeEaFactoryStageStatus")
        self.assertIn("item?.sourceRecordId", normalizer)
        self.assertIn("item?.columnValues", normalizer)
        self.assertIn("item?.core", normalizer)
        self.assertIn("item?.downstream", normalizer)
        self.assertIn("buildReady: item?.buildReady === true", normalizer)
        self.assertIn("backtestReport:", normalizer)
        self.assertIn("optimizationReport:", normalizer)
        self.assertIn("sourceUrls.slice(0, 10)", normalizer)
        list_normalizer = self.block("function normalizeEaFactoryTextList", "function eaFactoryFirstArray")
        self.assertIn("safeAgentChatReplyText", list_normalizer)
        self.assertIn("limit = 80", list_normalizer)
        self.assertIn(r"split(/\r?\n|\s*;\s*/)", list_normalizer)
        create = self.block("async function createEaFactoryBuild", "async function advanceEaFactoryStage")
        self.assertIn("sourceRecordId,", create)
        self.assertIn("platform: normalizedPlatform", create)
        self.assertIn(".slice(0, 900)", create)
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("brief.maxLength = 900", spec)

    def test_requests_use_dedicated_endpoints_and_tradingview_is_canonical(self):
        actions = self.block("async function syncEaFactoryGoogleSheet", "function connectionHubStatusGroup")
        self.assertIn('"/api/props/right_server_racks/ea-factory/sources/google-sheet/sync"', actions)
        self.assertIn('"/api/props/right_server_racks/ea-factory/builds"', actions)
        self.assertIn("/ea-factory/builds/${encodeURIComponent(buildId)}/advance", actions)
        self.assertIn('"/api/integrations/metatrader/select"', actions)
        self.assertIn("{ propId: EA_FACTORY_PROP_ID, candidateId: candidate.id }", actions)
        self.assertIn('["tradingview", "TradingView / Pine Script"]', self.main)
        self.assertNotIn('["pine", "TradingView / Pine Script"]', self.main)
        self.assertIn('return "tradingview";', self.block("function normalizeEaFactoryPlatform", "function normalizeEaFactorySourceRecord"))

    def test_authoritative_read_model_and_stage_gates_fail_closed(self):
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn('root.schemaVersion === "ea-factory-v1"', normalizer)
        self.assertIn('root.mode === "manual_stage_by_stage"', normalizer)
        self.assertIn("root.scheduled === false", normalizer)
        self.assertIn("dedicatedReadModelFresh", normalizer)
        self.assertNotIn("report.eaFactory", normalizer)
        self.assertNotIn("latestReportMetrics", normalizer)
        self.assertIn("const canRun = raw?.canAdvance === true", self.main)
        stage_normalizer = self.block("function normalizeEaFactoryStage", "function normalizeEaFactoryTerminal")
        self.assertNotIn("raw?.canRun", stage_normalizer)
        self.assertNotIn("raw?.actionEnabled", stage_normalizer)
        self.assertIn('canRun && normalizedStatus === "locked" ? "ready"', self.main)
        self.assertIn("terminalSelection.selectedCandidate", normalizer)
        self.assertIn('status: "locked"', normalizer)

        tabs = self.block("function renderWorkflowTabs", "function workflowAvailabilityCopy")
        self.assertIn('["locked", "unknown"].includes(factoryStage.status)', tabs)
        self.assertIn("button.disabled = Boolean(factoryLocked)", tabs)
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn("stage?.canRun === true", operational)
        self.assertIn("domain.currentStageId === stageId", operational)
        self.assertIn("domain.selectedTerminalReady === true", operational)
        self.assertIn('["compile_validate", "backtest_recheck"].includes(stageId)', operational)
        self.assertIn("ยังไม่มีผล Visual Backtest จริง", operational)
        self.assertNotIn("domain.activeBuild.raw?.backtest", operational)
        self.assertIn("ระบบไม่อ่าน metric นอกสัญญา", operational)

    def test_pine_skips_terminal_and_backtest_without_fake_result(self):
        picker = self.block("function renderEaFactoryTerminalPicker", "function renderEaFactoryOperationalStage")
        self.assertIn('platform === "tradingview"', picker)
        self.assertIn("Pine Script ใช้ Code Validation เท่านั้น", picker)
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn('domain.activeBuild.platform === "tradingview"', operational)
        self.assertIn("Not Applicable สำหรับ Pine Script", operational)
        self.assertIn("ระบบไม่สร้างผล Backtest ทดแทน", operational)

    def test_completed_or_attention_build_does_not_lock_factory_forever(self):
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn('"completed"', normalizer)
        self.assertIn('"attention_required"', normalizer)
        self.assertIn('"blocked"', normalizer)
        self.assertIn("canStartNewBuild", normalizer)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("if (domain.canStartNewBuild)", source)
        self.assertIn("if (domain.canStartNewBuild)", spec)
        self.assertIn("ไม่เขียนทับ Version เดิม", spec)

    def test_running_build_keeps_its_exact_source_record_bound(self):
        selector = self.block("function eaFactorySelectedSource", "function createEaFactoryNotice")
        self.assertIn("!domain.canStartNewBuild && domain.activeBuild?.sourceRecordId", selector)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn("select.disabled = !domain.canStartNewBuild", source)

    def test_strategy_spec_confirmation_shows_all_a_m_rules(self):
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        for column in "ABCDEFGHIJKLM":
            self.assertIn(f'"{column} •', spec)
        rule_renderer = self.block("function appendEaFactoryRuleList", "function createEaFactoryStageHeader")
        self.assertIn("safeAgentChatReplyText(rule", rule_renderer)

    def test_all_downstream_sheet_fields_and_full_bounded_catalog_are_visible(self):
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn(").slice(0, 200).map(normalizeEaFactorySourceRecord)", normalizer)
        self.assertIn("eaFactoryFirstArray(root.builds).slice(0, 100)", normalizer)
        self.assertIn("eaFactoryFirstArray(activeBuildRaw?.files).slice(0, 200)", normalizer)
        for label in (
            "N • Source URLs",
            "O • Verification",
            "P • Backtest Status",
            "Q • Backtest Report",
            "R • Optimization Status",
            "S • Optimization Report",
            "T • Issues",
            "U • Next Action",
            "V • Target Platform",
            "W • Updated At",
        ):
            self.assertIn(label, source)

    def test_build_history_is_selectable_and_terminal_picker_is_in_left_rail(self):
        self.assertIn('selectedBuildId: ""', self.main)
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("state.modal.eaFactory.selectedBuildId", normalizer)
        self.assertIn("requestedBuild,", normalizer)
        self.assertIn("selectedTerminalMatch", normalizer)
        self.assertIn("buildTerminalGate.ready === true", normalizer)
        self.assertIn("buildTerminalGate.adapterReady === true", normalizer)
        self.assertIn("buildTerminalGate.platform === activeBuild?.platform", normalizer)
        self.assertIn("buildTerminalGate.candidateId === selectedTerminalId", normalizer)
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn('row.setAttribute("role", "button")', operational)
        self.assertIn('row.setAttribute("aria-pressed"', operational)
        self.assertIn("state.modal.eaFactory.selectedBuildId = historyBuildId", operational)
        self.assertIn("กำลังดูไฟล์และประวัติแบบ Read-only", operational)
        tabs = self.block("function renderWorkflowTabs", "function workflowAvailabilityCopy")
        self.assertIn('tab.id === "artifacts_report"', tabs)
        self.assertIn("factoryReadOnlyHistory", tabs)
        navigation = self.block("function setWorkflowDashboardTab", "function workflowActionFormPayload")
        self.assertIn("readOnlyHistory", navigation)
        self.assertIn('selected.id === "artifacts_report"', navigation)
        rail = self.block("function renderWorkflowSettingsRail", "function getWorkflowHandoffReports")
        self.assertIn("subject?.id === EA_FACTORY_PROP_ID", rail)
        self.assertIn("renderEaFactoryTerminalPicker(terminalRail", rail)
        picker = self.block("function renderEaFactoryTerminalPicker", "function renderEaFactoryOperationalStage")
        self.assertIn("เลือก Target Platform ในขั้น Strategy Spec ก่อน", picker)
        self.assertIn("Array.isArray(domain.terminals)", picker)
        self.assertIn(".ea-factory-rail-terminal", self.styles)
        self.assertIn('li[data-selected="true"]', self.styles)

    def test_factory_authority_and_downloads_only_use_dedicated_read_model(self):
        domain_router = self.block("function normalizeWorkflowDomainData", "function createWorkflowExternalSource")
        self.assertIn("state.eaFactoryReadModel.payload || {}", domain_router)
        merge = self.block("function mergeEaFactoryReadModel", "async function loadEaFactoryReadModel")
        self.assertIn("state.eaFactoryReadModel.payload = model", merge)
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("eaFactoryFirstArray(activeBuildRaw?.files)", normalizer)
        self.assertNotIn("root.downloads", normalizer)
        self.assertNotIn("root.artifacts", normalizer)
        self.assertNotIn("root.files", normalizer)

    def test_dedicated_read_model_is_polled_without_overlapping_requests(self):
        loader = self.block("async function loadEaFactoryReadModel", "function setEaFactoryActionState")
        self.assertIn("state.eaFactoryReadModel.inFlight", loader)
        self.assertIn("signal?.aborted", loader)
        self.assertIn("lastLoadedAt = Date.now()", loader)
        self.assertIn("state.eaFactoryReadModel.payload = null", loader)
        self.assertIn("โหลด EA Factory Read Model ไม่สำเร็จ", loader)
        self.assertIn("setEaFactoryActionState", loader)
        poller = self.block("async function pollOpenPropReport", "function startMissionPolling")
        self.assertIn("factoryStageActive", poller)
        self.assertIn("factoryTtlExpired", poller)
        self.assertIn("await loadEaFactoryReadModel({ signal })", poller)

    def test_artifacts_are_backend_downloads_and_factory_layout_is_responsive(self):
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        url_guard = self.block("function getSafeReportArtifactUrl", "function appendDashboardArtifactLinks")
        artifact_normalizer = self.block("function normalizeEaFactoryArtifact", "function normalizeEaFactoryDomain")
        self.assertIn("/ea-factory\\/builds\\/ea-build-", url_guard)
        self.assertIn("item.downloadUrl || item.url", artifact_normalizer)
        self.assertIn("item.available === true || isFactoryFile", artifact_normalizer)
        self.assertIn("domain.activeBuild.artifactLineage", operational)
        self.assertIn("appendDashboardArtifactLinks(section, domain.activeBuild.artifacts, { limit: 200 })", operational)
        self.assertNotIn("reports.flatMap", operational)
        artifact_links = self.block("function appendDashboardArtifactLinks", "function appendDashboardVisualEvidence")
        self.assertIn("Math.min(Number(limit) || 20, 200)", artifact_links)
        self.assertIn(".slice(0, boundedLimit)", artifact_links)
        self.assertIn("ยังไม่มีไฟล์ที่ Backend อนุญาตให้ดาวน์โหลด", operational)
        self.assertIn("Audit และประวัติ Version", operational)
        self.assertIn("ประวัติ Build ในโรงงาน", operational)
        self.assertIn(".ea-factory-panel", self.styles)
        self.assertIn(".ea-factory-source-rules", self.styles)
        self.assertIn(".ea-factory-terminal-picker", self.styles)
        self.assertIn(".ea-factory-build-history", self.styles)
        self.assertRegex(self.styles, r"@media \(max-width: 900px\)[\s\S]+?ea-factory")


if __name__ == "__main__":
    unittest.main()
