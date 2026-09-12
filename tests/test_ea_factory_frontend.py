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
        self.assertIn('const oneClickOwnsBuild = ["queued", "running", "waiting_ai", "awaiting_visible_terminal"]', normalizer)
        self.assertIn("const canStartNewBuild = !backendBusyActive && !oneClickOwnsBuild", normalizer)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("if (domain.canStartNewBuild)", source)
        self.assertIn("if (domain.canStartNewBuild)", spec)
        self.assertIn("ไม่เขียนทับ Version เดิม", spec)

    def test_running_build_keeps_its_exact_source_record_bound(self):
        selector = self.block("function eaFactorySelectedSource", "function createEaFactoryNotice")
        self.assertIn("!domain.canStartNewBuild && domain.activeBuild?.sourceRecordId", selector)
        self.assertIn("if (!domain.canStartNewBuild && requestedRecord) return requestedRecord", selector)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn("select.disabled = !domain.canStartNewBuild", source)

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

    def test_build_history_is_selectable_and_terminal_status_is_read_only_in_left_rail(self):
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
        self.assertIn("state.eaFactoryReadModel.stale = false", merge)
        normalizer = self.block("function normalizeEaFactoryDomain", "function normalizeWorkflowDomainData")
        self.assertIn("eaFactoryFirstArray(activeBuildRaw?.files)", normalizer)
        self.assertNotIn("root.downloads", normalizer)
        self.assertNotIn("root.artifacts", normalizer)
        self.assertNotIn("root.files", normalizer)

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
        self.assertIn("backendBusyActive ? { ...stage, canRun: false }", normalizer)
        buttons = self.block("function createEaFactoryActionButton", "function renderEaFactoryStatusStrip")
        self.assertIn("Boolean(state.eaFactoryReadModel.busy)", buttons)
        self.assertIn("disabled || requestBusy || backendBusy", buttons)

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
        self.assertIn("/retry`", actions)
        self.assertIn("failedMissionId: stage.missionId", actions)
        self.assertIn("eaFactoryRetryableInvalidOutput(domain, stage)", actions)
        self.assertIn('{ terminalAware: true }', actions)
        self.assertIn("raw?.canRetry === true", self.main)
        self.assertIn('.ea-factory-bound-report[data-tone="error"]', self.styles)
        self.assertIn('.ea-factory-bound-report > summary', self.styles)

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
        self.assertIn("terminalProcessLaunchAllowed: false", domain)

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
        self.assertIn("capability.selectedPlatform === domain.activeBuild.platform", one_click)
        self.assertIn("Retry จากปุ่มนี้ไม่ได้ • เปิดขั้นละเอียด", one_click)
        self.assertIn('appendEaFactoryFact(facts, "One-click Run", run.runId)', one_click)
        self.assertIn("capability.visibleAdapterConnected", one_click)
        self.assertIn("เปิด MT4 ให้พร้อม แล้วกดตรวจซ้ำ", one_click)
        self.assertIn('domain.activeBuild.platform !== "mt4"', one_click)
        self.assertIn("One-click แบบหน้าต่างจริงยังไม่รองรับ MT5", one_click)
        self.assertIn("ระบบจะไม่เปิด MetaEditor/MT5", one_click)
        self.assertIn('const platformReady = domain.activeBuild.platform === "mt4"', one_click)
        self.assertIn("capability.terminalRunning === true", one_click)
        self.assertIn("capability.terminalProcessLaunchAllowed === false", one_click)
        self.assertNotIn("สำเร็จอัตโนมัติ", one_click)

        panel = self.block("function renderEaFactoryPanel", "function mergeEaFactoryReadModel")
        self.assertIn("renderEaFactoryOneClickPanel(section, domain)", panel)
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertIn("renderEaFactoryOneClickSetup(section, domain, selected)", source)
        self.assertIn("ตรวจ Strategy Spec / เปิดตัวเลือกขั้นสูง", source)
        spec = self.block("function renderEaFactorySpecStage", "function renderEaFactoryTerminalPicker")
        self.assertIn("renderEaFactoryOneClickSetup(section, domain, source)", spec)
        self.assertIn("ตัวเลือกขั้นสูง • Indicator / TradingView / ทำทีละขั้น", spec)

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
        self.assertIn("force || factoryStageActive || factoryOneClickActive || factoryTtlExpired", poller)

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
