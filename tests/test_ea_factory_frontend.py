import json
import re
import shutil
import subprocess
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

    def node_binary(self):
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

    def test_factory_has_three_operator_pages_and_keeps_seven_internal_stages(self):
        constants = self.block("const EA_FACTORY_STAGE_IDS", "const TRADING_RESEARCH_MAX_OHLC_ROWS")
        stage_start = constants.index("const EA_FACTORY_STAGE_IDS")
        stage_end = constants.index("]);", stage_start)
        ui_ids = re.findall(r'^\s+"([a-z_]+)",?$', constants[stage_start:stage_end], re.M)
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
        page_line = re.search(r"const EA_FACTORY_PAGE_IDS = Object\.freeze\(\[([^\]]+)\]\);", constants)
        self.assertIsNotNone(page_line)
        self.assertEqual(re.findall(r'"([a-z_]+)"', page_line.group(1)), ["source", "progress", "result"])
        for label in (
            "1 เลือกระบบและเริ่มเขียน",
            "2 สถานะการทำงาน",
            "3 ตรวจโค้ดและเสร็จสิ้น",
        ):
            self.assertIn(label, constants)
        fallback = self.block("const WORKFLOW_DASHBOARD_FALLBACKS", "  right_tool_console: {")
        self.assertIn("tabs: EA_FACTORY_PAGE_IDS.map", fallback)
        self.assertNotIn("tabs: EA_FACTORY_STAGE_IDS.map", fallback)
        dashboard = self.block("function normalizeWorkflowDashboard", "function getWorkflowSelectedTab")
        self.assertIn("presentationTabs = EA_FACTORY_PAGE_IDS.map", dashboard)
        self.assertNotIn("presentationTabs = EA_FACTORY_STAGE_IDS.map", dashboard)

    def test_three_operator_pages_are_navigable_and_route_to_the_correct_content(self):
        selected = self.block("function getWorkflowSelectedTab", "function renderWorkflowTabs")
        self.assertIn("eaFactoryPreferredPageId", selected)
        tabs = self.block("function renderWorkflowTabs", "function workflowAvailabilityCopy")
        self.assertIn('dataset.eaFactoryPages = factoryPages ? "true" : "false"', tabs)
        self.assertIn("const factoryLocked = false", tabs)
        self.assertIn("button.disabled = Boolean(factoryLocked)", tabs)
        panel = self.block("function renderEaFactoryPanel", "function validateEaFactoryBusyModel")
        self.assertIn('tabId === "source"', panel)
        self.assertIn('tabId === "progress"', panel)
        self.assertIn('tabId === "result"', panel)
        self.assertNotIn('tabId === "generate"', panel)
        page_status = self.block("function eaFactoryPageStatus", "function eaFactoryPreferredPageId")
        self.assertIn("if (!domain.authoritative)", page_status)
        self.assertIn('pageId === "source" ? "blocked" : "unknown"', page_status)
        preferred = self.block("function eaFactoryPreferredPageId", "function createEaFactoryPageHeader")
        self.assertIn('if (domain.backendBusy) return "progress"', preferred)
        self.assertIn('if (runStatus === "completed" || finalStatus === "completed") return "result"', preferred)
        self.assertIn('return "source"', preferred)
        self.assertNotIn('return "progress";', preferred[preferred.index("const runStatus"):])
        self.assertIn('.workflow-tabs[data-ea-factory-pages="true"]', self.styles)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", self.styles)
        tab_switch = self.block("function setWorkflowDashboardTab", "function workflowActionFormPayload")
        self.assertIn(
            "[EA_OPTIMIZATION_LAB_PROP_ID, EA_FACTORY_PROP_ID].includes(propId)",
            tab_switch,
        )
        self.assertIn("scrollArea.scrollTop = 0", tab_switch)

    def test_preferred_page_treats_noncompleted_busy_null_runs_as_history(self):
        helper = self.block("function eaFactoryPreferredPageId", "function createEaFactoryPageHeader")
        script = "\n".join([
            helper,
            "const page = (status, busy=null, finalStatus='locked') => eaFactoryPreferredPageId({backendBusy:busy,oneClick:{run:{status}},stages:[{id:'artifacts_report',status:finalStatus}]});",
            "process.stdout.write(JSON.stringify({",
            "  busy:page('running',{buildId:'live'}),",
            "  failed:page('failed'), blocked:page('blocked'), awaiting:page('awaiting_visible_terminal'),",
            "  queued:page('queued'), running:page('running'), completed:page('completed'), finalCompleted:page('idle',null,'completed'),",
            "}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "busy": "progress",
                "failed": "source",
                "blocked": "source",
                "awaiting": "source",
                "queued": "source",
                "running": "source",
                "completed": "result",
                "finalCompleted": "result",
            },
        )

    def test_sheet_source_uses_exact_a_j_strategy_brief_and_posts_opaque_source_record_id(self):
        constants = self.block("const EA_FACTORY_SHEET_COLUMNS", "const EA_FACTORY_LEGACY_SHEET_COLUMNS")
        columns = re.findall(r'\["([A-J])", "([a-z_]+)"\]', constants)
        self.assertEqual(len(columns), 10)
        self.assertEqual("".join(letter for letter, _ in columns), "ABCDEFGHIJ")
        self.assertEqual(
            [name for _, name in columns],
            [
                "record_id",
                "system_name",
                "system_overview",
                "entry_rules",
                "recovery_rules",
                "exit_rules",
                "money_management",
                "order_execution",
                "display_requirements",
                "additional_notes",
            ],
        )

        normalizer = self.block("function normalizeEaFactorySourceRecord", "function normalizeEaFactoryStageStatus")
        self.assertIn("item?.sourceRecordId", normalizer)
        self.assertIn("item?.columnValues", normalizer)
        self.assertIn("item?.core", normalizer)
        self.assertIn("item?.downstream", normalizer)
        self.assertIn("const eaResearch = normalizeEaFactoryResearchReadModel({", normalizer)
        self.assertIn("strategyBrief: item?.strategyBrief", normalizer)
        self.assertIn("buildReady: item?.buildReady === true && eaResearch.ready", normalizer)
        self.assertIn("sourceReportId:", normalizer)
        self.assertIn("blueprintDigest: eaResearch.blueprintDigest", normalizer)
        self.assertIn("...eaResearch.readinessIssues", normalizer)
        self.assertIn("...missingCoreFields.map", normalizer)
        self.assertIn("compatiblePlatforms", normalizer)
        self.assertIn("factoryCompatibility", normalizer)
        self.assertIn("&& compatibilityReady", normalizer)
        self.assertIn("eaResearch,", normalizer)
        self.assertIn("backtestReport:", normalizer)
        self.assertIn("optimizationReport:", normalizer)
        self.assertIn("sourceUrls.slice(0, 10)", normalizer)
        list_normalizer = self.block("function normalizeEaFactoryTextList", "function eaFactoryFirstArray")
        self.assertIn("safeAgentChatReplyText", list_normalizer)
        self.assertIn("limit = 80", list_normalizer)
        self.assertIn(r"split(/\r?\n|\s*;\s*/)", list_normalizer)
        create = self.block("async function createEaFactoryBuild", "async function advanceEaFactoryStage")
        self.assertIn("sourceRecordId,", create)
        self.assertIn("artifactKind: normalizedArtifactKind", create)
        self.assertIn("platform: normalizedPlatform", create)
        self.assertIn(".slice(0, 900)", create)
        self.assertIn("source.compatiblePlatforms.includes(normalizedPlatform)", create)
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("brief.maxLength = 900", spec)
        self.assertIn("compatiblePlatformSet.has(value)", spec)
        self.assertIn("compatiblePlatformSet.has(platform.value)", spec)

    def test_custom_indicator_picker_and_truthful_no_backtest_ui(self):
        normalizer = self.block(
            "function normalizeEaFactoryArtifactKind",
            "const EA_FACTORY_READINESS_ISSUE_LABELS",
        )
        self.assertIn('return "custom_indicator"', normalizer)
        self.assertIn('return "expert_advisor"', normalizer)
        domain = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("artifactKind: normalizeEaFactoryArtifactKind", domain)
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn('artifactKind.dataset.eaFactoryArtifactKind = "true"', spec)
        self.assertIn('["custom_indicator", "Custom Indicator"]', spec)
        self.assertIn("tradingViewOption.disabled = indicatorSelected", spec)
        self.assertIn('platform.value === "tradingview"', spec)
        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn('domain.activeBuild.artifactKind === "custom_indicator"', operational)
        self.assertIn("Not Applicable สำหรับ Custom Indicator", operational)
        self.assertIn("ไม่มีการ attach หรือเทรด", self.main)
        self.assertIn("เริ่มตรวจ Indicator และ No-Trade Guard", operational)

    def test_requests_use_dedicated_endpoints_and_tradingview_is_canonical(self):
        actions = self.block("async function syncEaFactoryGoogleSheet", "function connectionHubStatusGroup")
        self.assertIn('"/api/props/right_server_racks/ea-factory/sources/google-sheet/sync"', actions)
        self.assertIn('"/api/props/right_server_racks/ea-factory/builds"', actions)
        self.assertIn("/ea-factory/builds/${encodeURIComponent(buildId)}/advance", actions)
        self.assertNotIn("/api/integrations/metatrader/", actions)
        self.assertIn('postJson("/api/integrations/metatrader/global/select"', self.main)
        self.assertNotIn('postJson("/api/integrations/metatrader/select"', self.main)
        self.assertIn('["tradingview", "TradingView / Pine Script"]', self.main)
        self.assertNotIn('["pine", "TradingView / Pine Script"]', self.main)
        self.assertIn('return "tradingview";', self.block("function normalizeEaFactoryPlatform", "function normalizeEaFactorySourceRecord"))

    def test_authoritative_read_model_and_stage_gates_fail_closed(self):
        supported_modes = self.block("const EA_FACTORY_SUPPORTED_MODES", "const POLLING_LEADER_STORAGE_KEY")
        self.assertEqual(
            re.findall(r'^\s+"([a-z_]+)",?$', supported_modes, re.M),
            ["one_click_with_manual_stage_recovery", "manual_stage_by_stage"],
        )
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn('root.schemaVersion === "ea-factory-v1"', normalizer)
        self.assertIn("EA_FACTORY_SUPPORTED_MODES.has(root.mode)", normalizer)
        self.assertIn('"one_click_with_manual_stage_recovery"', self.main)
        self.assertIn('"manual_stage_by_stage"', self.main)
        self.assertIn("root.scheduled === false", normalizer)
        self.assertIn("dedicatedReadModelFresh", normalizer)
        self.assertIn("state.eaFactoryReadModel.stale !== true", normalizer)
        self.assertIn("root.snapshotStale !== true", normalizer)
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
        self.assertIn("eaFactoryPageStatus", tabs)
        self.assertIn("const factoryLocked = false", tabs)
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

    def test_only_authoritative_backend_busy_locks_new_factory_work(self):
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("const backendBusyActive = Object.keys(backendBusy).length > 0", normalizer)
        self.assertIn("const busyBuild = backendBusyActive ? builds.find", normalizer)
        self.assertIn('const oneClickOwnsBuild = ["queued", "running", "waiting_ai", "awaiting_visible_terminal"]', normalizer)
        self.assertIn("const canStartNewBuild = !backendBusyActive", normalizer)
        self.assertIn("historicalRunLooksActive: !backendBusyActive && oneClickOwnsBuild", normalizer)
        self.assertNotIn("const canStartNewBuild = !backendBusyActive && !oneClickOwnsBuild", normalizer)
        self.assertIn("backendBusyActive ? matchingBusyRootBuild : requestedBuild", normalizer)
        self.assertIn("backendBusyActive ? null : builds[0]", normalizer)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("if (domain.canStartNewBuild)", source)
        self.assertIn("if (domain.canStartNewBuild)", spec)
        self.assertIn("ไม่เขียนทับ Version เดิม", spec)

    def test_running_build_keeps_its_exact_source_record_bound(self):
        selector = self.block("function eaFactorySelectedSource", "function createEaFactoryNotice")
        self.assertIn("domain.backendBusy && domain.activeBuild?.sourceRecordId", selector)
        self.assertIn("if (domain.backendBusy && requestedRecord) return requestedRecord", selector)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn("select.disabled = !domain.authoritative || !domain.canStartNewBuild", source)

    def test_legacy_and_non_ready_sources_are_read_only_and_never_selected_for_new_build(self):
        selector = self.block("function eaFactorySelectedSource", "function createEaFactoryNotice")
        self.assertIn("records.filter(eaFactorySourceIsBuildSelectable)", selector)
        self.assertIn("selectableRecords[0]", selector)
        self.assertNotIn("records[0]", selector)

        selectable = self.block(
            "function eaFactorySourceIsBuildSelectable",
            "function eaFactorySelectedSource",
        )
        self.assertIn("record?.buildReady === true", selectable)
        self.assertIn("research.ready === true", selectable)
        self.assertIn("research.validated === true", selectable)
        self.assertIn("research.digestMatched === true", selectable)
        self.assertIn("research.legacy !== true", selectable)
        self.assertIn("TRADING_RESEARCH_STRATEGY_BRIEF_SCHEMA_VERSION", selectable)

        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn("option.disabled = !selectable", source)
        self.assertIn('" • อ่านอย่างเดียว"', source)
        self.assertIn("if (!eaFactorySourceIsBuildSelectable(next))", source)
        self.assertIn("ยังไม่มี Strategy Brief A-J ที่พร้อมสร้าง", source)
        self.assertIn("กรุณากลับไปวิเคราะห์ Revision ใหม่ก่อน", source)

    def test_strategy_spec_confirmation_uses_canonical_strategy_brief_not_legacy_blueprint(self):
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("renderEaFactoryResearchGate(section, source, { showBrief: true })", spec)
        self.assertIn("if (!source.buildReady || !source.eaResearch.ready) return", spec)
        self.assertIn('"Brief SHA-256"', spec)
        self.assertNotIn("appendEaFactoryRuleList", spec)
        for column in "ABCDEFGHIJKLM":
            self.assertNotIn(f'"{column} •', spec)

        normalizer = self.block("function normalizeEaFactoryResearchReadModel", "function normalizeEaFactorySourceRecord")
        self.assertIn("item?.eaResearch", normalizer)
        self.assertIn("raw.strategyBrief", normalizer)
        self.assertIn("raw.briefDigest", normalizer)
        self.assertIn("raw.validated === true", normalizer)
        self.assertIn("raw.digestMatched === true", normalizer)
        self.assertIn("tradingResearchStrategyBriefReadModel(briefReport)", normalizer)
        self.assertIn("/^[0-9a-f]{64}$/", normalizer)
        self.assertIn("raw.readinessIssues", normalizer)
        self.assertIn("raw.blockingIssues", normalizer)
        self.assertNotIn("eaImplementationBlueprint", normalizer)
        self.assertNotIn("eaBlueprint", normalizer)

    def test_all_strategy_brief_fields_and_full_bounded_catalog_are_visible(self):
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn(").slice(0, 200).map(normalizeEaFactorySourceRecord)", normalizer)
        self.assertIn("eaFactoryFirstArray(root.builds).slice(0, 100)", normalizer)
        self.assertIn("eaFactoryFirstArray(activeBuildRaw?.files).slice(0, 200)", normalizer)
        self.assertIn("createTradingResearchStrategyBrief", source)
        self.assertNotIn("N • Source URLs", source)
        self.assertNotIn("W • Updated At", source)
        gate = self.block("function renderEaFactoryResearchGate", "function renderEaFactorySourceStage")
        self.assertIn("source?.readinessIssues", gate)
        self.assertIn("createTradingResearchStrategyBrief", gate)
        self.assertIn("Strategy Brief", gate)
        self.assertIn("legacy", gate)
        self.assertNotIn("innerHTML", gate)

    def test_build_history_is_selectable_and_terminal_status_is_not_a_pending_task(self):
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
        result = self.block("function renderEaFactoryResultPage", "function renderEaFactoryPanel")
        self.assertIn('renderEaFactoryOperationalStage(section, "artifacts_report"', result)
        self.assertIn("state.modal.workflowTabs[propId] = selected.id", self.main)
        rail = self.block("function renderWorkflowSettingsRail", "function getWorkflowHandoffReports")
        self.assertIn("subject?.id === EA_FACTORY_PROP_ID", rail)
        self.assertIn("createEaFactoryRailTaskStatus", rail)
        self.assertIn('selectedPageId === "progress" || factoryDomain.backendBusy', rail)
        self.assertIn("renderEaFactoryTerminalPicker(terminalRail", rail)
        rail_status = self.block("function createEaFactoryRailTaskStatus", "function createFxNewsRailFact")
        self.assertIn("ไม่มีงาน EA ค้างอยู่", rail_status)
        self.assertIn("Backend ยืนยัน busy=null", rail_status)
        self.assertIn("const staleBusy = hasBusySnapshot && domain.authoritative !== true", rail_status)
        self.assertIn("const authorityPending = domain.authoritative !== true && !requestInFlight", rail_status)
        self.assertIn('authorityPending ? "checking" : "ready"', rail_status)
        self.assertIn("เป็นสถานะครั้งล่าสุดที่เคยยืนยัน ไม่ใช่สถานะสด", rail_status)
        self.assertIn("readError?.message", rail_status)
        self.assertIn("ข้อมูลล่าสุดที่เก็บไว้เมื่อ", rail_status)
        self.assertIn("นี่คือสถานะ Terminal ไม่ใช่งาน EA ที่ค้าง", rail_status)
        self.assertIn('.ea-factory-rail-task-status[data-status="checking"]', self.styles)
        picker = self.block("function renderEaFactoryTerminalPicker", "function renderEaFactoryOperationalStage")
        self.assertIn("เลือกชนิดโค้ดในขั้น Strategy Spec ก่อน", picker)
        self.assertIn("Array.isArray(domain.terminals)", picker)
        self.assertIn("domain.selectedTerminalId", picker)
        self.assertIn("ไปที่แถบเชื่อม MT4 / MT5", picker)
        self.assertIn("openGlobalMetatraderHubFromDevice", picker)
        self.assertNotIn('document.createElement("select")', picker)
        self.assertNotIn("selectEaFactoryTerminal", picker)
        self.assertIn(".ea-factory-rail-terminal", self.styles)

    def test_factory_authority_and_downloads_only_use_dedicated_read_model(self):
        domain_router = self.block("function normalizeWorkflowDomainData", "function createWorkflowExternalSource")
        self.assertIn("state.eaFactoryReadModel.payload || {}", domain_router)
        merge = self.block("function mergeEaFactoryReadModel", "async function loadEaFactoryReadModel")
        self.assertIn("state.eaFactoryReadModel.payload = model", merge)
        self.assertIn("state.eaFactoryReadModel.lastLoadedAt = Date.now()", merge)
        self.assertIn("state.eaFactoryReadModel.stale = backendSnapshotStale", merge)
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("eaFactoryFirstArray(activeBuildRaw?.files)", normalizer)
        self.assertNotIn("root.downloads", normalizer)
        self.assertNotIn("root.artifacts", normalizer)
        self.assertNotIn("root.files", normalizer)

    def test_successful_fresh_read_clears_stale_error_but_preserves_working_action(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        merge = self.block("function mergeEaFactoryReadModel", "function mergeEaFactoryResponseReport")
        self.assertIn("const staleActionError = !actionState.inFlight", merge)
        self.assertIn('["error", "warning"].includes(state.modal.eaFactory.tone)', merge)
        self.assertIn('actionState.tone = "neutral"', merge)

        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({ spec:'strategy_spec', generate:'generate_source', review:'source_review', compile_validate:'compile_validate', backtest_recheck:'backtest_recheck', artifacts_report:'final_report' });",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 240);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const state = { eaFactoryReadModel:{payload:null,lastLoadedAt:0,stale:false,lastError:null,busy:null}, modal:{eaFactory:{inFlight:false,stageId:'generate',message:'error เก่า',tone:'error'}}, propReports:{} };",
            validator,
            merge,
            "mergeEaFactoryReadModel({eaFactory:{schemaVersion:'ea-factory-v1',busy:null}});",
            "const cleared = {...state.modal.eaFactory};",
            "state.modal.eaFactory = {inFlight:true,stageId:'one_click_run',message:'กำลังทำงาน',tone:'working'};",
            "mergeEaFactoryReadModel({eaFactory:{schemaVersion:'ea-factory-v1',busy:null}});",
            "const preserved = {...state.modal.eaFactory};",
            "process.stdout.write(JSON.stringify({cleared,preserved}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["cleared"]["stageId"], "")
        self.assertEqual(payload["cleared"]["message"], "")
        self.assertEqual(payload["cleared"]["tone"], "neutral")
        self.assertTrue(payload["preserved"]["inFlight"])
        self.assertEqual(payload["preserved"]["stageId"], "one_click_run")
        self.assertEqual(payload["preserved"]["message"], "กำลังทำงาน")
        self.assertEqual(payload["preserved"]["tone"], "working")

    def test_backend_stale_snapshot_disables_factory_authority_and_surfaces_refresh(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        merge = self.block("function mergeEaFactoryReadModel", "function mergeEaFactoryResponseReport")
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("const backendSnapshotStale = model.snapshotStale === true", merge)
        self.assertIn("state.eaFactoryReadModel.stale = backendSnapshotStale", merge)
        self.assertIn("กำลังรีเฟรชสถานะ EA Factory", merge)
        self.assertIn("state.eaFactoryReadModel.stale !== true", normalizer)
        self.assertIn("root.snapshotStale !== true", normalizer)

        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({ spec:'strategy_spec', generate:'generate_source', review:'source_review', compile_validate:'compile_validate', backtest_recheck:'backtest_recheck', artifacts_report:'final_report' });",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 240);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const state = { eaFactoryReadModel:{payload:null,lastLoadedAt:0,stale:false,lastError:null,busy:null}, modal:{eaFactory:{inFlight:false,stageId:'',message:'',tone:'neutral'}}, propReports:{} };",
            validator,
            merge,
            "const merged = mergeEaFactoryReadModel({eaFactory:{schemaVersion:'ea-factory-v1',snapshotStale:true,busy:null}});",
            "process.stdout.write(JSON.stringify({merged,stale:state.eaFactoryReadModel.stale,lastError:state.eaFactoryReadModel.lastError}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["merged"])
        self.assertTrue(payload["stale"])
        self.assertEqual(payload["lastError"]["kind"], "refreshing")

    def test_dedicated_read_model_is_polled_without_overlapping_requests(self):
        loader = self.block("async function loadEaFactoryReadModel", "function setEaFactoryActionState")
        self.assertIn("state.eaFactoryReadModel.inFlight", loader)
        self.assertIn("signal?.aborted", loader)
        self.assertIn('error?.kind === "parent_abort"', loader)
        self.assertIn("const hasLastGood = Boolean(state.eaFactoryReadModel.payload)", loader)
        self.assertIn("state.eaFactoryReadModel.stale = hasLastGood", loader)
        self.assertIn('if (presentation.kind === "schema")', loader)
        self.assertEqual(loader.count("state.eaFactoryReadModel.payload = null"), 1)
        self.assertIn("eaFactoryReadModelFailurePresentation", loader)
        self.assertIn("setEaFactoryActionState", loader)
        poller = self.block("async function pollOpenPropReport", "function startMissionPolling")
        self.assertIn("factoryStageActive", poller)
        self.assertIn("factoryTtlExpired", poller)
        self.assertIn("await loadEaFactoryReadModel({ signal })", poller)
        self.assertIn("propId !== EA_FACTORY_PROP_ID && (force || reportTtlExpired)", poller)

    def test_factory_open_starts_dedicated_read_immediately_and_skips_generic_report(self):
        open_dialog = self.block("async function openPropDialog", "function setConnectionActionState")
        self.assertIn("? loadEaFactoryReadModel()", open_dialog)
        self.assertIn("? Promise.resolve(null)\n    : loadPropReport(propId)", open_dialog)
        self.assertNotIn("reportRequest.then(() => loadEaFactoryReadModel())", open_dialog)
        self.assertLess(open_dialog.index("loadEaFactoryReadModel()"), open_dialog.index("loadPropReport(propId)"))
        self.assertLess(open_dialog.index("loadEaFactoryReadModel()"), open_dialog.index("openGameModal("))

        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        self.assertNotIn("loadPropReport(EA_FACTORY_PROP_ID)", request)
        self.assertIn("mergeEaFactoryResponseReport(response)", request)
        self.assertIn("if (!mergeEaFactoryReadModel(response))", request)

        global_apply = self.block("async function applyGlobalMetatraderTarget", "function renderAiTradeMt4QuickSetup")
        self.assertIn(".filter((target) => target.propId !== EA_FACTORY_PROP_ID)", global_apply)

    def test_fetch_timeout_and_parent_abort_are_typed_separately(self):
        fetch = self.block("class FetchTimeoutError", "function normalizeCodexRateTimestamp")
        self.assertIn('this.kind = "fetch_timeout"', fetch)
        self.assertIn('this.kind = "parent_abort"', fetch)
        self.assertIn("controller.abort(new FetchParentAbortError(path))", fetch)
        self.assertIn("controller.abort(new FetchTimeoutError(path, timeoutMs))", fetch)
        self.assertNotIn("setTimeout(() => controller.abort(), timeoutMs)", fetch)
        self.assertIn("controller.signal.reason instanceof FetchTimeoutError", fetch)
        self.assertIn("controller.signal.reason instanceof FetchParentAbortError", fetch)

        script = "\n".join([
            "const window = { setTimeout, clearTimeout };",
            "const DEFAULT_FETCH_TIMEOUT_MS = 50;",
            fetch,
            "const abortingFetch = (_path, options) => new Promise((_resolve, reject) => {",
            "  options.signal.addEventListener('abort', () => reject(options.signal.reason), { once: true });",
            "});",
            "(async () => {",
            "  globalThis.fetch = abortingFetch;",
            "  let timeoutError = null;",
            "  try { await fetchJson('/slow', { timeoutMs: 5 }); } catch (error) { timeoutError = error; }",
            "  const parent = new AbortController();",
            "  const parentRequest = fetchJson('/poll', { timeoutMs: 100, signal: parent.signal }).catch((error) => error);",
            "  parent.abort();",
            "  const parentError = await parentRequest;",
            "  globalThis.fetch = async () => ({ ok: false, status: 409, json: async () => ({",
            "    kind: 'ea_factory_busy', code: 'ea_factory_single_active_build', busy: { buildId: 'build-live' },",
            "  }) });",
            "  const httpError = await fetchJson('/busy').catch((error) => error);",
            "  process.stdout.write(JSON.stringify({",
            "    timeout: { name: timeoutError?.name, kind: timeoutError?.kind, thai: /[ก-๙]/.test(timeoutError?.message || '') },",
            "    parent: { name: parentError?.name, kind: parentError?.kind },",
            "    http: { status: httpError?.status, kind: httpError?.kind, buildId: httpError?.body?.busy?.buildId },",
            "  }));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "timeout": {"name": "TimeoutError", "kind": "fetch_timeout", "thai": True},
                "parent": {"name": "AbortError", "kind": "parent_abort"},
                "http": {"status": 409, "kind": "ea_factory_busy", "buildId": "build-live"},
            },
        )

    def test_factory_posts_have_a_bounded_timeout_and_reconcile_busy_after_failure(self):
        helper = self.block("async function postEaFactoryJson", "async function runEaFactoryRequest")
        self.assertIn("EA_FACTORY_ACTION_TIMEOUT_MS", helper)
        self.assertIn("const controller = new AbortController()", helper)
        self.assertIn("controller.abort(new FetchTimeoutError(path, timeoutMs))", helper)
        self.assertIn("window.clearTimeout(timeoutId)", helper)
        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        self.assertIn("const refreshed = await loadEaFactoryReadModel({ forceFresh: true })", request)
        self.assertIn("state.eaFactoryReadModel.busy", request)
        self.assertIn("eaFactoryBusyPresentation(state.eaFactoryReadModel.busy)", request)
        self.assertIn("const busyClearedByFreshRead = Boolean(refreshed)", request)
        self.assertIn('failedRequestPresentation.kind === "busy"', request)
        self.assertIn('kind: "busy_reconciled"', request)
        self.assertIn("Backend ยืนยัน busy=null", request)
        self.assertIn('stageId: busyClearedByFreshRead ? "" : stageId', request)
        self.assertIn("if (refreshed)", request)
        self.assertIn("state.eaFactoryReadModel.lastError = null", request)
        self.assertIn("state.eaFactoryReadModel.stale = false", request)
        self.assertIn("if (state.modal.eaFactory.inFlight", request)
        self.assertIn("คำขอสิ้นสุดแล้ว", request)

        script = "\n".join([
            "const window = { setTimeout, clearTimeout };",
            "const EA_FACTORY_ACTION_TIMEOUT_MS = 20;",
            "class FetchTimeoutError extends Error { constructor(path, timeoutMs) { super(path); this.name='TimeoutError'; this.kind='fetch_timeout'; this.timeoutMs=timeoutMs; } }",
            helper,
            "globalThis.fetch = (_path, options) => new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(options.signal.reason), {once:true}));",
            "postEaFactoryJson('/slow', {}, {timeoutMs:5}).then(() => process.exit(2)).catch((error) => process.stdout.write(JSON.stringify({name:error.name,kind:error.kind,timeoutMs:error.timeoutMs})));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {"name": "TimeoutError", "kind": "fetch_timeout", "timeoutMs": 5},
        )

    def test_structured_factory_rejection_wins_over_generic_404_copy(self):
        presentation = self.block(
            "function eaFactoryReadModelFailurePresentation",
            "function renderEaFactoryReadModelNotice",
        )
        self.assertIn("const structuredFactoryRejection", presentation)
        self.assertIn('kind === "ea_factory_request_rejected"', presentation)
        self.assertIn('String(body.code || "").startsWith("ea_factory_")', presentation)
        self.assertLess(
            presentation.index("if (structuredFactoryRejection)"),
            presentation.index("if (status === 404)"),
        )
        self.assertIn("message: `${messageTh}${staleNote}`", presentation)

    def test_integrity_409_surfaces_backend_thai_instead_of_transport_copy(self):
        presentation = self.block(
            "function eaFactoryReadModelFailurePresentation",
            "function renderEaFactoryReadModelNotice",
        )
        message_th = (
            "ตรวจพบว่าไฟล์หลักฐานของ EA Factory สูญหายหรือถูกเปลี่ยนแปลง "
            "หากเพิ่งสั่งงานผ่านหน้าต่าง MT4 ให้ถือว่าผลลัพธ์ยังไม่แน่นอน"
        )
        script = "\n".join([
            "const workflowDomainObject = (value) => value && typeof value === 'object' && !Array.isArray(value) ? value : {};",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 600);",
            "const eaFactoryBusyContext = () => null;",
            "const eaFactoryBusyPresentation = () => ({kind:'busy'});",
            "const PROP_REPORT_FETCH_TIMEOUT_MS = 1000;",
            presentation,
            "const result = eaFactoryReadModelFailurePresentation({",
            "  status: 409,",
            "  kind: 'ea_factory_integrity_blocked',",
            "  body: {",
            "    kind: 'ea_factory_integrity_blocked',",
            "    code: 'ea_factory_artifact_integrity_failed',",
            f"    messageTh: {json.dumps(message_th, ensure_ascii=False)},",
            "  },",
            "});",
            "process.stdout.write(JSON.stringify(result));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["kind"], "request_rejected")
        self.assertEqual(result["tone"], "error")
        self.assertEqual(result["message"], message_th)
        self.assertNotIn("ติดต่อ EA Factory Backend ไม่สำเร็จ", result["message"])

    def test_busy_post_runtime_reconciles_to_fresh_busy_null(self):
        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        script = "\n".join([
            "const state = { modal:{eaFactory:{inFlight:false,stageId:'',message:'',tone:'neutral'}}, eaFactoryReadModel:{payload:{schemaVersion:'ea-factory-v1'},busy:null,lastError:{kind:'busy'},stale:true} };",
            "let refreshCalls = 0;",
            "function setEaFactoryActionState(next) { Object.assign(state.modal.eaFactory, next); }",
            "function eaFactoryReadModelFailurePresentation() { return {kind:'busy',tone:'warning',title:'งานเดิม',message:'งานเดิมกำลังทำ',busy:{buildId:'old-build'}}; }",
            "async function loadEaFactoryReadModel() { refreshCalls += 1; state.eaFactoryReadModel.busy = null; return {eaFactory:{schemaVersion:'ea-factory-v1',busy:null}}; }",
            "function eaFactoryBusyPresentation(busy) { return {kind:'busy',tone:'warning',title:'busy',message:String(busy.buildId),busy}; }",
            request,
            "(async () => {",
            "  const result = await runEaFactoryRequest('one_click_run', async () => { throw new Error('HTTP 409'); }, 'ok');",
            "  process.stdout.write(JSON.stringify({result,refreshCalls,action:state.modal.eaFactory,readModel:state.eaFactoryReadModel}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["result"])
        self.assertEqual(payload["refreshCalls"], 1)
        self.assertFalse(payload["action"]["inFlight"])
        self.assertEqual(payload["action"]["stageId"], "")
        self.assertEqual(payload["action"]["tone"], "ready")
        self.assertIn("busy=null", payload["action"]["message"])
        self.assertIsNone(payload["readModel"]["busy"])
        self.assertIsNone(payload["readModel"]["lastError"])
        self.assertFalse(payload["readModel"]["stale"])

    def test_busy_409_is_thai_structured_and_blocks_new_factory_actions(self):
        helpers = self.block("function validateEaFactoryBusyModel", "function mergeEaFactoryReadModel")
        for field in ("buildId", "displayName", "stageId", "status", "activeOperation"):
            self.assertIn(field, helpers)
        self.assertIn("supportedStageIds", helpers)
        self.assertIn('stageId === "" || supportedStageIds.has(stageId)', helpers)
        self.assertIn("supportedStatuses", helpers)
        self.assertIn("supportedOperations", helpers)
        self.assertIn('body.kind === "ea_factory_busy"', helpers)
        self.assertIn('body.code === "ea_factory_single_active_build"', helpers)
        self.assertIn("ตอนนี้ยังไม่รับงานใหม่", helpers)
        self.assertNotIn("error?.message", helpers)

        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("const backendBusy = workflowDomainObject(state.eaFactoryReadModel.busy)", normalizer)
        self.assertIn("applyEaFactoryStageAdmission(stage, authoritative, backendBusyActive)", normalizer)
        buttons = self.block("function createEaFactoryActionButton", "function renderEaFactoryStatusStrip")
        self.assertIn("Boolean(state.eaFactoryReadModel.busy)", buttons)
        self.assertIn("disabled || requestBusy || backendBusy", buttons)

    def test_manual_stage_admission_fails_closed_for_stale_and_busy_models(self):
        helper = self.block(
            "function applyEaFactoryStageAdmission",
            "function normalizeEaFactoryDomain",
        )
        script = "\n".join([
            helper,
            "const stage = {id:'generate',canRun:true,canRetry:true};",
            "const pick = (authoritative,busy) => {",
            "  const value = applyEaFactoryStageAdmission(stage,authoritative,busy);",
            "  return {canRun:value.canRun,canRetry:value.canRetry};",
            "};",
            "process.stdout.write(JSON.stringify({",
            "  ready:pick(true,false), stale:pick(false,false), busy:pick(true,true), both:pick(false,true),",
            "}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "ready": {"canRun": True, "canRetry": True},
                "stale": {"canRun": False, "canRetry": False},
                "busy": {"canRun": False, "canRetry": False},
                "both": {"canRun": False, "canRetry": False},
            },
        )

    def test_successful_poll_retains_validated_backend_busy_until_backend_clears_it(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        merge = self.block("function mergeEaFactoryReadModel", "function mergeEaFactoryResponseReport")
        self.assertIn("validateEaFactoryBusyModel(model.busy)", merge)
        self.assertIn("if (!busyValidation.valid) return false", merge)
        self.assertIn("state.eaFactoryReadModel.busy = busyValidation.busy", merge)
        self.assertNotIn("state.eaFactoryReadModel.busy = null", merge)

        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({ spec:'strategy_spec', generate:'generate_source', review:'source_review', compile_validate:'compile_validate', backtest_recheck:'backtest_recheck', artifacts_report:'final_report' });",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const safeDashboardDisplayText = (value, fallback='') => String(value || fallback).slice(0, 240);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const state = { eaFactoryReadModel: { payload:null,lastLoadedAt:0,stale:false,lastError:null,busy:null }, modal:{eaFactory:{stageId:'',message:'',tone:'neutral'}}, propReports:{} };",
            validator,
            merge,
            "const liveBusy = { buildId:'ea-build-live-1', displayName:'งานทดสอบ', stageId:'generate_source', status:'running', activeOperation:'generate_source' };",
            "const first = mergeEaFactoryReadModel({ eaFactory:{ schemaVersion:'ea-factory-v1', busy:liveBusy } });",
            "const kept = state.eaFactoryReadModel.busy;",
            "const edge = validateEaFactoryBusyModel({...liveBusy, stageId:null, activeOperation:'one_click_run'});",
            "const invalid = mergeEaFactoryReadModel({ eaFactory:{ schemaVersion:'ea-factory-v1', busy:{...liveBusy, activeOperation:'unknown_raw_operation'} } });",
            "const afterInvalid = state.eaFactoryReadModel.busy;",
            "const cleared = mergeEaFactoryReadModel({ eaFactory:{ schemaVersion:'ea-factory-v1', busy:null } });",
            "process.stdout.write(JSON.stringify({first,kept,edge,invalid,afterInvalid,cleared,finalBusy:state.eaFactoryReadModel.busy}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["first"])
        self.assertEqual(payload["kept"]["buildId"], "ea-build-live-1")
        self.assertTrue(payload["edge"]["valid"])
        self.assertEqual(payload["edge"]["busy"]["stageId"], "")
        self.assertFalse(payload["invalid"])
        self.assertEqual(payload["afterInvalid"]["activeOperation"], "generate_source")
        self.assertTrue(payload["cleared"])
        self.assertIsNone(payload["finalBusy"])

    def test_timeout_or_transport_failure_keeps_last_good_payload_as_stale(self):
        state = self.block("eaFactoryReadModel: {", "todayWorkView:")
        self.assertIn("stale: false", state)
        self.assertIn("lastError: null", state)
        self.assertIn("busy: null", state)
        loader = self.block("async function loadEaFactoryReadModel", "function setEaFactoryActionState")
        catch_start = loader.index("} catch (error) {")
        catch_block = loader[catch_start:]
        stale_assignment = catch_block.index("state.eaFactoryReadModel.stale = hasLastGood")
        schema_clear = catch_block.index("state.eaFactoryReadModel.payload = null")
        self.assertGreater(stale_assignment, schema_clear)
        self.assertIn("state.eaFactoryReadModel.lastError = {", catch_block)
        notice = self.block("function renderEaFactoryReadModelNotice", "function mergeEaFactoryReadModel")
        self.assertIn("readModelState.stale", notice)
        self.assertIn("ข้อมูลล่าสุดที่เก็บไว้เมื่อ", notice)

        presentation = self.block(
            "function eaFactoryReadModelFailurePresentation",
            "function renderEaFactoryReadModelNotice",
        )
        script = "\n".join([
            "const PROP_REPORT_FETCH_TIMEOUT_MS = 20000;",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const eaFactoryBusyContext = () => null;",
            presentation,
            "const result = eaFactoryReadModelFailurePresentation({status:503,kind:'transport',message:'connect ECONNREFUSED 127.0.0.1:8765'},{hasLastGood:true});",
            "process.stdout.write(JSON.stringify(result));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["kind"], "transport")
        self.assertIn("connect ECONNREFUSED 127.0.0.1:8765", payload["message"])
        self.assertIn("ข้อมูลล่าสุด", payload["message"])

    def test_stage_request_is_accepted_before_it_is_truthfully_completed(self):
        stage_normalizer = self.block("function normalizeEaFactoryStageStatus", "function normalizeEaFactoryTerminal")
        self.assertIn("reconcileEaFactoryStageWithMission", stage_normalizer)
        self.assertIn("mission.workStatus", stage_normalizer)
        self.assertIn('"invalid_output"', stage_normalizer)
        self.assertIn("failureCode", stage_normalizer)

        presentation = self.block("function eaFactoryActionPresentation", "function renderEaFactoryOperationalStage")
        self.assertIn('tone: "working"', presentation)
        self.assertIn("คำขอถูกบันทึกแล้ว แต่ยังไม่ถือว่าสำเร็จ", presentation)
        self.assertIn('tone: "error"', presentation)
        self.assertIn("ขั้นนี้ไม่สำเร็จ", presentation)
        self.assertIn('stage.status === "completed"', presentation)

        request = self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet")
        self.assertIn("terminalAware", request)
        self.assertIn("Local Runner รับคำขอแล้ว • กำลังรอผลตรวจจาก Backend", request)
        self.assertIn("eaFactoryActionPresentation", request)

    def test_invalid_generation_output_shows_validator_findings_and_fresh_retry(self):
        diagnostics = self.block("function eaFactoryReportForStage", "function createEaFactoryActionButton")
        self.assertIn("mission?.reportIds", diagnostics)
        self.assertIn("item?.linkedMissionId", diagnostics)
        self.assertIn("workflowOutput.missingFields", diagnostics)
        self.assertIn("workflowOutput.missingEvidenceKinds", diagnostics)
        self.assertIn("semanticRepair.remainingIssues", diagnostics)
        self.assertIn("รายละเอียดที่ Backend Validator ปฏิเสธ", diagnostics)
        self.assertIn('document.createElement("details")', diagnostics)
        self.assertIn('document.createElement("summary")', diagnostics)
        self.assertIn("panel.open = !terminalFailure", diagnostics)
        self.assertIn("ดูรายละเอียด Validator", diagnostics)

        retry_guard = self.block("function eaFactoryRetryableInvalidOutput", "function eaFactoryActionPresentation")
        self.assertIn('stage?.backendId !== "generate_source"', retry_guard)
        self.assertIn("stage?.canRetry !== true", retry_guard)
        self.assertIn('stage.failureCode !== "invalid_output"', retry_guard)
        self.assertIn("versions.length === 0", retry_guard)
        self.assertIn("!hasSourceArtifact", retry_guard)

        operational = self.block("function renderEaFactoryOperationalStage", "function renderEaFactoryPanel")
        self.assertIn("eaFactoryRetryableInvalidOutput(domain, stage)", operational)
        self.assertIn("ลองใหม่ได้อีก ${retriesRemaining} ครั้ง", operational)
        self.assertIn("สร้าง Codex Mission ใหม่และใช้เครดิต Codex เพิ่ม", operational)
        self.assertIn("จะไม่เขียนทับ Version ใด ๆ", operational)
        self.assertIn("สร้าง Codex Mission ใหม่เพื่อลอง Source อีกครั้ง", operational)
        self.assertIn("retryEaFactoryStage(stageId)", operational)
        self.assertIn("stage.retryAttemptCount", operational)
        self.assertIn("stage.retryAttemptLimit", operational)
        self.assertLess(
            operational.index("if (eaFactoryRetryableInvalidOutput(domain, stage))"),
            operational.index("appendEaFactoryBoundReport(section, report, stage)"),
        )

        actions = self.block("async function advanceEaFactoryStage", "function connectionHubStatusGroup")
        self.assertIn("async function retryEaFactoryStage", actions)
        self.assertEqual(actions.count("if (\n    domain.authoritative !== true"), 2)
        self.assertEqual(actions.count("|| Boolean(domain.backendBusy)"), 2)
        self.assertEqual(actions.count("|| state.modal.eaFactory.inFlight"), 2)
        self.assertEqual(actions.count('messageKind: "local_preflight_rejected"'), 2)
        self.assertEqual(actions.count("setEaFactoryActionState({"), 2)
        self.assertIn("/retry`", actions)
        self.assertIn("failedMissionId: stage.missionId", actions)
        self.assertIn("eaFactoryRetryableInvalidOutput(domain, stage)", actions)
        self.assertIn('{ terminalAware: true }', actions)
        self.assertIn("raw?.canRetry === true", self.main)
        self.assertIn('.ea-factory-bound-report[data-tone="error"]', self.styles)
        self.assertIn('.ea-factory-bound-report > summary', self.styles)

    def test_advance_and_retry_preflight_rejections_are_visible_without_posting(self):
        actions = self.block("async function advanceEaFactoryStage", "function connectionHubStatusGroup")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const EA_FACTORY_STAGE_COPY = {};",
            "const state = {eaFactoryReadModel:{payload:{schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false}},propReports:{right_server_racks:{}},modal:{eaFactory:{inFlight:false}}};",
            "const getModalSubject = () => ({id:EA_FACTORY_PROP_ID});",
            "const getPropertyRole = () => ({});",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryReadModel"),
            "let mode = 'advance';",
            "const normalizeWorkflowDashboard = () => mode === 'advance'",
            "  ? {domainData:{eaFactory:{authoritative:false,backendBusy:false,currentStageId:'spec',activeBuild:{id:'build-1'},stages:[{id:'spec',backendId:'strategy_spec',canRun:true}]}}}",
            "  : {domainData:{eaFactory:{authoritative:true,backendBusy:true,currentStageId:'generate',activeBuild:{id:'build-1'},stages:[{id:'generate',backendId:'generate_source',missionId:'mission-1',canRetry:true,failureCode:'invalid_output'}]}}};",
            "const eaFactoryRetryableInvalidOutput = () => true;",
            "const createWorkflowIdempotencyKey = () => 'unused';",
            "let postCount = 0;",
            "const postEaFactoryJson = async () => { postCount += 1; return {}; };",
            "const runEaFactoryRequest = async () => { postCount += 1; return {}; };",
            "function setEaFactoryActionState(next={}) { Object.assign(state.modal.eaFactory,next); }",
            actions,
            "(async () => {",
            "  const advanceResult = await advanceEaFactoryStage('spec');",
            "  const advanceAction = {...state.modal.eaFactory};",
            "  mode = 'retry';",
            "  const retryResult = await retryEaFactoryStage('generate');",
            "  const retryAction = {...state.modal.eaFactory};",
            "  process.stdout.write(JSON.stringify({advanceResult,retryResult,advanceAction,retryAction,postCount}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["advanceResult"])
        self.assertIsNone(payload["retryResult"])
        self.assertEqual(payload["postCount"], 0)
        self.assertEqual(payload["advanceAction"]["messageKind"], "local_preflight_rejected")
        self.assertEqual(payload["retryAction"]["messageKind"], "local_preflight_rejected")
        self.assertTrue(payload["advanceAction"]["readModelStateKey"])
        self.assertTrue(payload["retryAction"]["readModelStateKey"])
        self.assertIn("Read Model", payload["advanceAction"]["message"])
        self.assertIn("กำลังทำอยู่", payload["retryAction"]["message"])

    def test_invalid_output_retry_policy_executes_live_read_model_matrix(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required to execute the frontend retry policy")

        first_array = self.block("function eaFactoryFirstArray", "function normalizeEaFactoryPlatform")
        retry_guard = self.block("function eaFactoryRetryableInvalidOutput", "function eaFactoryActionPresentation")
        script = f"""
const assert = require("node:assert/strict");
const vm = require("node:vm");
const sandbox = {{}};
vm.createContext(sandbox);
vm.runInContext({json.dumps(first_array + retry_guard)}, sandbox);
const canRetry = sandbox.eaFactoryRetryableInvalidOutput;

const liveStage = {{
  backendId: "generate_source",
  status: "failed",
  failureCode: "invalid_output",
  canRetry: true,
  retryAttemptCount: 0,
  retryAttemptLimit: 3,
}};
const liveDomain = {{
  activeBuild: {{
    id: "ea-build-1789123053951-6b18ad",
    version: "",
    raw: {{ versions: [] }},
    artifacts: [{{
      fileName: "strategy-spec-v01.json",
      kind: "strategy_spec",
    }}],
  }},
}};

assert.equal(canRetry(liveDomain, liveStage), true, "source-less invalid_output must show Retry");
assert.equal(canRetry(liveDomain, {{ ...liveStage, canRetry: false, retryAttemptCount: 3 }}), false,
  "retry-exhausted backend state must hide Retry");
assert.equal(canRetry({{
  activeBuild: {{
    ...liveDomain.activeBuild,
    artifacts: [{{ fileName: "CAN_SLIM.mq4", kind: "source_code" }}],
  }},
}}, liveStage), false, "an existing Source artifact must hide Retry");
assert.equal(canRetry(liveDomain, {{ ...liveStage, backendId: "source_review" }}), false,
  "Source Review failures must never replay an immutable Source/Version");
assert.equal(canRetry({{
  activeBuild: {{
    id: "ea-build-history-v1",
    version: "v1",
    raw: {{ versions: [{{ version: 1 }}] }},
    artifacts: [],
  }},
}}, liveStage), false, "a history-selected versioned Build must hide Retry");
"""
        completed = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_one_click_read_model_is_build_bound_and_resumable_after_reload(self):
        constants = self.block("const EA_FACTORY_ONE_CLICK_STAGE_IDS", "const EA_FACTORY_STAGE_COPY")
        self.assertEqual(
            re.findall(r'^\s+"([a-z_]+)",?$', constants, re.M),
            ["generate", "review", "compile_validate", "backtest_recheck"],
        )
        normalizer = self.block("function normalizeEaFactoryOneClickRun", "function normalizeEaFactoryAudit")
        for status in (
            "waiting_ai",
            "awaiting_visible_terminal",
            "blocked",
            "failed",
            "completed",
        ):
            self.assertIn(f'"{status}"', normalizer)
        self.assertIn("raw.idempotencyKey || raw.resumeKey", normalizer)
        self.assertIn('runId: String(raw.runId || "").trim()', normalizer)
        self.assertIn("canResume: raw.canResume === true", normalizer)
        self.assertIn("canRetry: raw.canRetry === true", normalizer)
        self.assertIn("stageResults:", normalizer)

        domain = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("oneClickRun: normalizeEaFactoryOneClickRun(activeBuildRaw?.oneClickRun)", domain)
        self.assertIn("const oneClickCapability = workflowDomainObject(root.oneClick)", domain)
        self.assertIn("oneClickCapability.selectedPlatform || globalSelectedTerminal?.platform", domain)
        self.assertIn("canCreateAndRun: oneClickCapability.canCreateAndRun === true", domain)
        self.assertIn("visibleAdapterConnected: oneClickCapability.visibleAdapterConnected === true", domain)
        self.assertIn("supportedVisiblePlatforms: oneClickVisiblePlatforms", domain)
        self.assertIn("selectedPlatformSupported:", domain)
        self.assertIn("terminalRunning: oneClickCapability.terminalRunning === true", domain)
        self.assertIn("terminalProcessLaunchAllowed: oneClickCapability.terminalProcessLaunchAllowed === true", domain)

    def test_one_click_ui_has_four_truthful_steps_and_visible_front_office_gate(self):
        one_click = self.block("function eaFactoryOneClickStatusLabel", "function eaFactoryRetryableInvalidOutput")
        for text in (
            "1 AI เขียน EA",
            "2 ตรวจ Source และเงื่อนไข",
            "3 เปิด MetaEditor และ Compile",
            "4 เปิด MT4 ทำ Visual Backtest",
            "Strategy Brief 10 ช่อง",
            "6 กลุ่ม",
            "Visual mode",
            "ไม่ใช้ผลหลังบ้านมาอ้างว่าผ่าน",
        ):
            self.assertIn(text, one_click)
        self.assertIn("EA_FACTORY_ONE_CLICK_STAGE_IDS.forEach", one_click)
        self.assertIn("stageResult.missionId", one_click)
        self.assertIn("stageResult.reportId", one_click)
        self.assertIn("หลักฐาน ${stageResult.evidence.length} รายการ", one_click)
        self.assertIn('status === "awaiting_visible_terminal" && capability.canResume === true', one_click)
        self.assertIn('["failed", "blocked"].includes(status) && capability.canRetry === true', one_click)
        self.assertIn("capability.selectedPlatform === domain.activeBuild?.platform", one_click)
        self.assertIn("Retry จากปุ่มนี้ไม่ได้ • เปิดขั้นละเอียด", one_click)
        self.assertIn('appendEaFactoryFact(facts, "One-click Run", run.runId)', one_click)
        self.assertIn("capability.visibleAdapterConnected", one_click)
        self.assertIn("เปิด MT4 ให้พร้อม แล้วกดตรวจซ้ำ", one_click)
        self.assertIn('domain.activeBuild.platform !== "mt4"', one_click)
        self.assertIn("One-click แบบหน้าต่างจริงยังไม่รองรับ MT5", one_click)
        self.assertIn("ระบบจะไม่เปิด MetaEditor/MT5", one_click)
        self.assertIn('const platformReady = domain.activeBuild?.platform === "mt4"', one_click)
        self.assertIn("capability.terminalRunning === true", one_click)
        self.assertIn("capability.terminalProcessLaunchAllowed === false", one_click)
        self.assertIn("function eaFactoryExistingOneClickAdmission", one_click)
        self.assertIn("domain.authoritative === true", one_click)
        self.assertIn("!domain.backendBusy", one_click)
        self.assertIn("!requestInFlight", one_click)
        self.assertIn("Read Model ล่าสุดยังไม่ได้รับการยืนยันจาก Backend", one_click)
        self.assertIn("ปุ่ม One-click ของ Build นี้จะเปิดเมื่อ Backend ยืนยันว่า busy=null", one_click)
        self.assertIn("ปุ่มปิดไว้เพื่อป้องกันการส่งคำขอซ้ำ", one_click)
        self.assertNotIn("สำเร็จอัตโนมัติ", one_click)

        progress = self.block("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage")
        self.assertIn("renderEaFactoryOneClickPanel(section, domain)", progress)
        panel = self.block("function renderEaFactoryPanel", "function validateEaFactoryBusyModel")
        self.assertNotIn("renderEaFactoryOneClickPanel(section, domain)", panel)
        self.assertIn('const progressOwnsBusyNotice = tabId === "progress"', panel)
        self.assertIn("eaFactoryBusyPresentation(domain.backendBusy).message", panel)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn("renderEaFactoryOneClickSetup(section, domain, selected)", source)
        self.assertIn("ดู Strategy Brief เต็มและตัวเลือกขั้นสูง", source)
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("if (!embedded) renderEaFactoryOneClickSetup(section, domain, source)", spec)
        self.assertIn("ตัวเลือกขั้นสูง • Indicator / TradingView / ทำทีละขั้น", spec)

    def test_existing_one_click_admission_fails_closed_for_stale_busy_and_inflight_models(self):
        helper = self.block(
            "function eaFactoryExistingOneClickAdmission",
            "function renderEaFactoryOneClickPanel",
        )
        script = "\n".join([
            "const state = {modal:{eaFactory:{inFlight:false}}};",
            helper,
            "const base = {",
            "  authoritative:true, backendBusy:null, currentStageId:'generate',",
            "  activeBuild:{platform:'mt4'}, stages:[{id:'generate',status:'ready'}],",
            "  oneClick:{enabled:true,canRun:true,selectedTerminalId:'mt4-a',selectedPlatform:'mt4',",
            "    selectedPlatformSupported:true,terminalRunning:true,terminalProcessLaunchAllowed:false,run:{status:'idle'}},",
            "};",
            "const can = (patch={}) => eaFactoryExistingOneClickAdmission({...base,...patch}).canSubmit;",
            "const result = {",
            "  ready:can(),",
            "  stale:can({authoritative:false}),",
            "  busy:can({backendBusy:{buildId:'ea-build-live'}}),",
            "  launchAllowed:can({oneClick:{...base.oneClick,terminalProcessLaunchAllowed:true}}),",
            "};",
            "state.modal.eaFactory.inFlight = true;",
            "result.inFlight = can();",
            "process.stdout.write(JSON.stringify(result));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {"ready": True, "stale": False, "busy": False, "launchAllowed": False, "inFlight": False},
        )

    def test_progress_owns_one_click_result_summarizes_gates_and_create_opens_page_two(self):
        progress = self.block("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage")
        self.assertIn("ไม่มีงาน EA ค้างอยู่", progress)
        self.assertIn("Backend ยืนยัน busy=null", progress)
        self.assertIn("else if (!domain.authoritative)", progress)
        self.assertIn("กำลังตรวจสอบสถานะงาน EA", progress)
        self.assertIn("ยังยืนยันไม่ได้ว่ามีงานค้างอยู่หรือพร้อมรับงานใหม่", progress)
        self.assertIn("domain.historicalRunLooksActive", progress)
        self.assertIn("จะไม่ใช้สถานะประวัตินี้ปิดปุ่มเริ่มงานใหม่", progress)
        self.assertIn("กำลังรอรายละเอียด Build จาก Backend", progress)
        self.assertIn("โดยไม่หยิบประวัติงานอื่นมาแสดงแทน", progress)
        self.assertEqual(progress.count("renderEaFactoryOneClickPanel(section, domain)"), 1)

        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        result = self.block("function renderEaFactoryResultPage", "function renderEaFactoryPanel")
        self.assertNotIn("renderEaFactoryOneClickPanel", source)
        for stage_id in ("review", "compile_validate", "backtest_recheck", "artifacts_report"):
            self.assertIn(f'"{stage_id}"', result)
        self.assertIn("ea-factory-result-summary", result)
        self.assertIn("ตรวจ Source", result)
        self.assertIn("Compile / Validate", result)
        self.assertIn("Backtest / Recheck", result)
        self.assertIn("ไฟล์และ Final Report", result)

        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        self.assertIn("!domain.authoritative", create)
        self.assertIn("Boolean(domain.backendBusy)", create)
        self.assertIn("domain.canStartNewBuild !== true", create)
        self.assertIn("state.modal.eaFactory.selectedBuildId = buildId", create)
        self.assertIn('setWorkflowDashboardTab(EA_FACTORY_PROP_ID, "progress")', create)
        self.assertIn("persists the selected page snapshot", create)
        navigation = self.block("function setWorkflowDashboardTab", "function workflowActionFormPayload")
        self.assertIn("renderWorkflowDashboard(subject, propertyRole, report)", navigation)
        self.assertIn("saveSessionSnapshot()", navigation)

    def test_successful_create_immediately_invokes_progress_navigation(self):
        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const state = { propReports:{right_server_racks:{}}, modal:{eaFactory:{selectedBuildId:'',selectedArtifactKind:'',selectedPlatform:''}} };",
            "const normalizeEaFactoryArtifactKind = (value) => value;",
            "const normalizeEaFactoryPlatform = (value) => value;",
            "const getModalSubject = () => ({id:EA_FACTORY_PROP_ID});",
            "const getPropertyRole = () => ({});",
            "const normalizeWorkflowDashboard = () => ({domainData:{eaFactory:{authoritative:true,backendBusy:null,canStartNewBuild:true,sourceCatalog:{records:[{sourceRecordId:'source-1',buildReady:true,compatiblePlatforms:['mt4']}]}}}});",
            "const createWorkflowIdempotencyKey = () => 'workflow-test-key';",
            "const postEaFactoryJson = async () => ({});",
            "const runEaFactoryRequest = async () => ({build:{id:'ea-build-new'}});",
            "let navigation = null;",
            "function setWorkflowDashboardTab(propId, pageId) { navigation = {propId,pageId}; }",
            create,
            "(async () => {",
            "  const response = await createEaFactoryBuild('source-1','expert_advisor','mt4','');",
            "  process.stdout.write(JSON.stringify({response,selectedBuildId:state.modal.eaFactory.selectedBuildId,navigation}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["response"]["build"]["id"], "ea-build-new")
        self.assertEqual(payload["selectedBuildId"], "ea-build-new")
        self.assertEqual(
            payload["navigation"],
            {"propId": "right_server_racks", "pageId": "progress"},
        )

    def test_create_and_run_preflight_never_leaves_phantom_working_status(self):
        create = self.block("async function createEaFactoryBuild", "function eaFactoryOneClickRequestKey")
        flow = self.block("async function createAndRunEaFactoryBuild", "async function advanceEaFactoryStage")
        state_key = self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryReadModel")
        script = "\n".join([
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const state = {eaFactoryReadModel:{payload:{schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false}},propReports:{right_server_racks:{}},modal:{eaFactory:{inFlight:false,message:'',tone:'neutral'}}};",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            "const normalizeEaFactoryArtifactKind = (value) => value;",
            "const normalizeEaFactoryPlatform = (value) => value;",
            "const getModalSubject = () => ({id:EA_FACTORY_PROP_ID});",
            "const getPropertyRole = () => ({});",
            "const normalizeWorkflowDashboard = () => ({domainData:{eaFactory:{authoritative:false,backendBusy:null,canStartNewBuild:false,sourceCatalog:{records:[{sourceRecordId:'source-1',buildReady:true,compatiblePlatforms:['mt4']}]}}}});",
            "const createWorkflowIdempotencyKey = () => 'workflow-test-key';",
            "let postCount = 0;",
            "const postEaFactoryJson = async () => { postCount += 1; return {}; };",
            "const runEaFactoryRequest = async () => { postCount += 1; return {}; };",
            "const setWorkflowDashboardTab = () => {};",
            "let oneClickCount = 0;",
            "const runEaFactoryOneClick = async () => { oneClickCount += 1; return {}; };",
            "function setEaFactoryActionState(next={}) { Object.assign(state.modal.eaFactory,next); }",
            state_key,
            create,
            flow,
            "(async () => {",
            "  const result = await createAndRunEaFactoryBuild('source-1','mt4','');",
            "  process.stdout.write(JSON.stringify({result,action:state.modal.eaFactory,postCount,oneClickCount}));",
            "})().catch((error) => { console.error(error); process.exit(1); });",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["result"])
        self.assertEqual(payload["postCount"], 0)
        self.assertEqual(payload["oneClickCount"], 0)
        self.assertFalse(payload["action"]["inFlight"])
        self.assertEqual(payload["action"]["tone"], "warning")
        self.assertEqual(payload["action"]["messageKind"], "local_preflight_rejected")
        self.assertIn("Read Model", payload["action"]["message"])

    def test_stale_busy_is_labeled_last_confirmed_with_transport_reason_in_left_rail(self):
        rail = self.block("function createEaFactoryRailTaskStatus", "function createFxNewsRailFact")
        progress = self.block("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage")
        read_notice = self.block("function renderEaFactoryReadModelNotice", "function eaFactoryReadModelStateKey")
        panel = self.block("function renderEaFactoryPanel", "function validateEaFactoryBusyModel")
        self.assertIn("งานล่าสุดที่ Backend เคยยืนยัน • ยังไม่ใช่สถานะสด", progress)
        self.assertIn("Read Model เป็นข้อมูลเก่า", progress)
        self.assertIn("readModelState.lastError", read_notice)
        self.assertIn("domain.authoritative === true", panel)

        script = "\n".join([
            "const state = {modal:{eaFactory:{inFlight:false}},eaFactoryReadModel:{lastError:{message:'HTTP 503 exact transport reason'},lastLoadedAt:1700000000000}};",
            "const workflowDomainObject = (value) => value && typeof value === 'object' && !Array.isArray(value) ? value : {};",
            "const eaFactoryBusyStatusLabel = () => 'กำลังทำงาน';",
            "const eaFactoryBusyOperationLabel = () => 'กำลังสร้าง Source Code';",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const formatThaiDateTime = () => '14 พ.ย. 2566 05:13';",
            "const setWorkflowDashboardTab = () => {};",
            "const document = {createElement:(tag) => ({tag,dataset:{},children:[],textContent:'',addEventListener(){},append(...nodes){this.children.push(...nodes);}})};",
            rail,
            "const card = createEaFactoryRailTaskStatus({authoritative:false,backendBusy:{buildId:'ea-build-stale',status:'running',activeOperation:'generate_source'},oneClick:{terminalRunning:true}});",
            "process.stdout.write(JSON.stringify({status:card.dataset.status,title:card.children[0].textContent,detail:card.children[1].textContent,button:card.children[3].textContent}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "checking")
        self.assertIn("ยังยืนยันไม่ได้", payload["title"])
        self.assertIn("สถานะครั้งล่าสุด", payload["detail"])
        self.assertIn("HTTP 503 exact transport reason", payload["detail"])
        self.assertIn("14 พ.ย. 2566 05:13", payload["detail"])
        self.assertIn("เหตุผล", payload["button"])

    def test_structured_request_rejection_survives_identical_poll_until_state_transition(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        state_merge = self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryResponseReport")
        setter = self.block("function setEaFactoryActionState", "async function postEaFactoryJson")
        self.assertIn('messageKind = ""', setter)
        self.assertIn('readModelStateKey = ""', setter)
        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({spec:'strategy_spec',generate:'generate_source',review:'source_review',compile_validate:'compile_validate',backtest_recheck:'backtest_recheck',artifacts_report:'final_report'});",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            "const state = {eaFactoryReadModel:{payload:null,lastLoadedAt:Date.now(),stale:false,lastError:null,busy:null},modal:{eaFactory:{inFlight:false,stageId:'create_build',message:'Backend rejected exact reason',tone:'warning',messageKind:'local_preflight_rejected',readModelStateKey:''}},propReports:{}};",
            validator,
            state_merge,
            "const initial = {schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,busy:null,sourceCatalog:{records:[{sourceRecordId:'source-1',buildReady:false,verificationStatus:'blocked'}]},builds:[],terminalSelection:{},oneClick:{}};",
            "state.modal.eaFactory.readModelStateKey = eaFactoryReadModelStateKey(initial);",
            "mergeEaFactoryReadModel({eaFactory:initial});",
            "const afterSame = {...state.modal.eaFactory};",
            "const changed = {...initial,oneClick:{terminalProcessLaunchAllowed:true}};",
            "mergeEaFactoryReadModel({eaFactory:changed});",
            "const afterChanged = {...state.modal.eaFactory};",
            "process.stdout.write(JSON.stringify({afterSame,afterChanged}));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["afterSame"]["message"], "Backend rejected exact reason")
        self.assertEqual(payload["afterSame"]["messageKind"], "local_preflight_rejected")
        self.assertEqual(payload["afterChanged"]["message"], "")
        self.assertEqual(payload["afterChanged"]["messageKind"], "")

    def test_local_preflight_rejection_clears_when_identical_poll_refreshes_authority(self):
        validator = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        state_merge = self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryResponseReport")
        script = "\n".join([
            "const EA_FACTORY_STAGE_IDS = Object.freeze(['source','spec','generate','review','compile_validate','backtest_recheck','artifacts_report']);",
            "const EA_FACTORY_BACKEND_STAGE_BY_UI = Object.freeze({spec:'strategy_spec',generate:'generate_source',review:'source_review',compile_validate:'compile_validate',backtest_recheck:'backtest_recheck',artifacts_report:'final_report'});",
            "const EA_FACTORY_PROP_ID = 'right_server_racks';",
            "const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;",
            "const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery','manual_stage_by_stage']);",
            "const safeDashboardDisplayText = (value,fallback='') => String(value || fallback);",
            "const workflowDomainObject = (...values) => values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {};",
            "const eaFactoryFirstArray = (...values) => values.find(Array.isArray) || [];",
            "const model = {schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,busy:null,sourceCatalog:{records:[]},builds:[],terminalSelection:{},oneClick:{}};",
            "const state = {eaFactoryReadModel:{payload:model,lastLoadedAt:Date.now()-EA_FACTORY_READ_MODEL_MAX_AGE_MS-1,stale:false,lastError:null,busy:null},modal:{eaFactory:{inFlight:false,stageId:'create_build',message:'Read Model หมดอายุ',tone:'warning',messageKind:'local_preflight_rejected',readModelStateKey:''}},propReports:{}};",
            validator,
            state_merge,
            "state.modal.eaFactory.readModelStateKey = eaFactoryReadModelStateKey(model);",
            "mergeEaFactoryReadModel({eaFactory:model});",
            "process.stdout.write(JSON.stringify(state.modal.eaFactory));",
        ])
        completed = subprocess.run(
            [self.node_binary(), "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["message"], "")
        self.assertEqual(payload["messageKind"], "")

    def test_one_click_uses_global_terminal_and_posts_exact_idempotent_run_contract(self):
        setup = self.block("function renderEaFactoryOneClickSetup", "function eaFactoryRetryableInvalidOutput")
        self.assertIn("const platform = capability.selectedPlatform", setup)
        self.assertIn("capability.selectedTerminalId || domain.selectedTerminalId", setup)
        self.assertIn('const platformSupported = platform === "mt4"', setup)
        self.assertIn("capability.selectedPlatformSupported === true", setup)
        self.assertIn("source.compatiblePlatforms.includes(platform)", setup)
        self.assertIn("createAndRunEaFactoryBuild(source.sourceRecordId, platform, brief.value)", setup)
        self.assertNotIn('document.createElement("select")', setup)

        request = self.block("function eaFactoryOneClickRequestKey", "async function advanceEaFactoryStage")
        self.assertIn("run?.idempotencyKey", request)
        self.assertIn("state.modal.eaFactory.idempotencyKey = persisted", request)
        self.assertIn("createWorkflowIdempotencyKey()", request)
        self.assertIn("async function createAndRunEaFactoryBuild", request)
        self.assertIn('"expert_advisor"', request)
        self.assertIn("/ea-factory/builds/${encodeURIComponent(buildId)}/run`", request)
        self.assertIn("{ idempotencyKey }", request)
        self.assertIn("capability.selectedPlatform !== platform", request)
        self.assertIn('platform !== "mt4"', request)
        self.assertIn("capability.terminalRunning !== true", request)
        self.assertIn("capability.terminalProcessLaunchAllowed === true", request)
        self.assertIn("{ allowFreshBuild: true }", request)

        poller = self.block("async function pollOpenPropReport", "function startMissionPolling")
        self.assertIn("factoryOneClickActive", poller)
        self.assertIn('String(factoryDomain?.oneClick?.run?.status || "")', poller)
        self.assertIn('"awaiting_visible_terminal"', poller)
        self.assertIn("const factoryBackendBusy = Boolean(factoryDomain?.backendBusy)", poller)
        self.assertIn("const factoryStageActive = factoryBackendBusy", poller)
        self.assertIn("const factoryOneClickActive = factoryBackendBusy", poller)
        self.assertIn("force || factoryBackendBusy || factoryStageActive || factoryOneClickActive || factoryTtlExpired", poller)

    def test_one_click_request_key_executes_reload_and_fresh_build_matrix(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required to execute the one-click idempotency policy")
        helper = self.block("function eaFactoryOneClickRequestKey", "async function runEaFactoryOneClick")
        script = f"""
const assert = require("node:assert/strict");
const state = {{ modal: {{ eaFactory: {{
  oneClickBuildId: "", idempotencyKey: "", formSignature: "",
}} }} }};
let generated = 0;
function createWorkflowIdempotencyKey() {{ generated += 1; return `wf-generated-${{generated}}`; }}
{helper}
const persisted = eaFactoryOneClickRequestKey("ea-build-a", {{ idempotencyKey: "wf-persisted-1234" }});
assert.equal(persisted, "wf-persisted-1234");
assert.equal(generated, 0);
const replay = eaFactoryOneClickRequestKey("ea-build-a", {{}});
assert.equal(replay, "wf-persisted-1234");
assert.equal(generated, 0);
const fresh = eaFactoryOneClickRequestKey("ea-build-b", {{}});
assert.equal(fresh, "wf-generated-1");
assert.equal(generated, 1);
assert.equal(eaFactoryOneClickRequestKey("ea-build-b", {{}}), fresh);
assert.equal(generated, 1);
"""
        completed = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_compile_and_backtest_copy_does_not_hide_visible_user_steps(self):
        picker = self.block("function renderEaFactoryTerminalPicker", "function eaFactoryOneClickStatusLabel")
        self.assertIn("MetaEditor และ Visual Strategy Tester", picker)
        self.assertIn("ขั้น Compile ต้องเปิด MetaEditor ให้เห็นจริง", picker)
        self.assertIn("Visual Strategy Tester ให้เห็นจริง", picker)
        self.assertIn("MT5 • ขั้นละเอียดแบบ Manual", picker)
        self.assertIn("รุ่นนี้จะไม่เปิด MT5 อัตโนมัติ", picker)
        constants = self.block("const EA_FACTORY_STAGE_COPY", "const EA_FACTORY_BACKEND_STAGE_BY_UI")
        self.assertIn("เปิด MetaEditor ของ Terminal ที่เลือกให้เห็นจริง", constants)
        self.assertIn("ต้องเห็น Strategy Tester", constants)

    def test_backtest_attention_distinguishes_zero_trade_and_history_quality(self):
        operational = self.block(
            "function renderEaFactoryOperationalStage",
            "function renderEaFactoryPanel",
        )
        self.assertIn("backtest_zero_trades_and_history_quality_errors", operational)
        self.assertIn("backtest_history_quality_errors", operational)
        self.assertIn("Mismatched chart errors", operational)
        self.assertIn("backtestAttention", operational)
        self.assertIn("งดการประเมินประสิทธิภาพ", operational)

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
        self.assertIn(".ea-factory-one-click-progress", self.styles)
        self.assertIn(".ea-factory-manual-details", self.styles)
        self.assertRegex(self.styles, r"@media \(max-width: 900px\)[\s\S]+?ea-factory")


if __name__ == "__main__":
    unittest.main()
