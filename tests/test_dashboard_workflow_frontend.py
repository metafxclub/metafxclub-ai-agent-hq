from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]

WORKFLOW_PROP_IDS = (
    "codex_mcp_portal",
    "left_server_racks",
    "right_server_racks",
    "right_tool_console",
    "left_audit_crystals",
    "left_signal_cube",
    "terminal_workstation",
    "right_status_crystals",
)


class DashboardWorkflowFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        cls.main = (ROOT / "frontend" / "src" / "app" / "main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend" / "src" / "app" / "styles.css").read_text(encoding="utf-8")
        cls.role_map = json.loads(
            (ROOT / "contracts" / "props" / "property-role-map.json").read_text(encoding="utf-8")
        )["properties"]

    def run_research_node(self, body: str) -> dict:
        bundled_node = (
            Path.home()
            / ".cache"
            / "codex-runtimes"
            / "codex-primary-runtime"
            / "dependencies"
            / "node"
            / "bin"
            / "node.exe"
        )
        node = shutil.which("node") or (str(bundled_node) if bundled_node.exists() else None)
        if not node:
            self.skipTest("Node.js is unavailable")
        start = self.main.index("function tradingResearchNormalizeHeader")
        end = self.main.index("function normalizeFxBiasValue", start)
        functions = self.main[start:end]
        prelude = """
const TRADING_RESEARCH_MAX_OHLC_ROWS = 50000;
const TRADING_RESEARCH_MAX_FILE_BYTES = 5 * 1024 * 1024;
const TRADING_RESEARCH_MAX_RANGE_MS = Math.round(10 * 365.2425 * 24 * 60 * 60 * 1000);
const TRADING_RESEARCH_TIMEFRAME_MS = Object.freeze({
  M1: 60000, M5: 300000, M15: 900000, M30: 1800000,
  H1: 3600000, H4: 14400000, D1: 86400000, W1: 604800000, MN1: 2592000000,
});
const TRADING_RESEARCH_SIMULATION_REGIMES = Object.freeze([
  { id: "trend_up", labelTh: "up", drift: 0.42, volatility: 0.85 },
  { id: "sideways", labelTh: "sideways", drift: 0, volatility: 0.72 },
  { id: "volatility_shock", labelTh: "volatile", drift: 0.04, volatility: 2.35 },
  { id: "trend_down", labelTh: "down", drift: -0.38, volatility: 0.95 },
]);
"""
        process = subprocess.run(
            [node, "-e", prelude + functions + "\n" + body],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def run_node_json(self, source: str) -> dict:
        bundled_node = (
            Path.home()
            / ".cache"
            / "codex-runtimes"
            / "codex-primary-runtime"
            / "dependencies"
            / "node"
            / "bin"
            / "node.exe"
        )
        node = shutil.which("node") or (str(bundled_node) if bundled_node.exists() else None)
        if not node:
            self.skipTest("Node.js is unavailable")
        process = subprocess.run(
            [node, "-e", source],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def test_one_reusable_workspace_serves_all_eight_independent_dashboard_props(self):
        self.assertEqual(self.index.count('id="modalWorkflowDashboardWorkspace"'), 1)
        self.assertNotIn('id="workflowDashboardPipeline"', self.index)
        self.assertNotIn('id="workflowDashboardIdentityMark"', self.index)
        self.assertNotIn('id="workflowDashboardIdentityLabel"', self.index)
        self.assertNotIn('id="workflowDashboardStage"', self.index)
        self.assertNotIn('id="workflowDashboardTitle"', self.index)
        self.assertNotIn('id="workflowDashboardSummary"', self.index)
        self.assertIn('id="workflowSettingsRail"', self.index)
        self.assertIn('id="workflowSettingsRailContent"', self.index)
        self.assertIn('id="workflowAgentHandoffRail"', self.index)
        self.assertIn('id="workflowHandoffReport"', self.index)
        self.assertIn('id="workflowHandoffTarget"', self.index)
        self.assertIn('id="workflowHandoffAction"', self.index)
        self.assertIn('id="workflowHandoffButton"', self.index)
        self.assertIn('id="workflowDashboardTabs"', self.index)
        self.assertIn('id="workflowDashboardContent"', self.index)
        self.assertIn('id="workflowResultsPanel"', self.index)
        for prop_id in WORKFLOW_PROP_IDS:
            self.assertIn(prop_id, self.main)
        self.assertIn("WORKFLOW_DASHBOARD_PROP_IDS", self.main)
        self.assertIn("WORKFLOW_DASHBOARD_IDENTITIES", self.main)
        self.assertIn("isWorkflowDashboardPropId(subject.id)", self.main)

    def test_settings_and_agent_handoff_live_in_left_rail_not_the_main_workspace(self):
        left_rail_start = self.index.index('id="modalPortraitPanel"')
        left_rail_end = self.index.index('<div class="modal-content-panel">', left_rail_start)
        left_rail = self.index[left_rail_start:left_rail_end]
        workspace_start = self.index.index('id="modalWorkflowDashboardWorkspace"')
        workspace_end = self.index.index('id="modalKanbanPanel"', workspace_start)
        workspace = self.index[workspace_start:workspace_end]

        for control_id in (
            "workflowSettingsRail",
            "workflowSettingsRailContent",
            "workflowAgentHandoffRail",
            "workflowHandoffReport",
            "workflowHandoffTarget",
            "workflowHandoffAction",
            "workflowHandoffButton",
            "workflowHandoffStatus",
        ):
            self.assertIn(f'id="{control_id}"', left_rail)
            self.assertNotIn(f'id="{control_id}"', workspace)

        self.assertRegex(
            left_rail,
            re.compile(r'id="workflowSettingsRail"[^>]*\bhidden\b'),
        )
        self.assertRegex(
            left_rail,
            re.compile(r'id="workflowAgentHandoffRail"[^>]*\bhidden\b'),
        )

    def test_workflow_actions_use_the_guarded_prop_endpoint_and_minimal_payload(self):
        self.assertIn("`/api/props/${encodeURIComponent(propId)}/workflow/actions`", self.main)
        self.assertRegex(
            self.main,
            re.compile(
                r"postJson\(`/api/props/\$\{encodeURIComponent\(propId\)\}/workflow/actions`,\s*\{\s*actionId,\s*form:\s*actionForm,\s*idempotencyKey,?\s*\}\)",
                re.S,
            ),
        )
        self.assertNotIn("/api/dashboard-workflows/action", self.main)
        self.assertNotIn('type = "password"', self.main)
        self.assertIn("WORKFLOW_FIELD_DENY_PATTERN", self.main)

    def test_canonical_tabs_and_actions_are_present(self):
        expected = {
            "research": "deep_research_system",
            "backtest": "prepare_backtest_plan",
            "optimization": "prepare_optimization_plan",
            "ea_discovery": "prepare_ea_discovery_plan",
        }
        for tab_id, action_id in expected.items():
            self.assertIn(f'id: "{tab_id}"', self.main)
            self.assertIn(f'id: "{action_id}"', self.main)
        self.assertIn('id: "chart"', self.main)
        self.assertIn('id: "report"', self.main)
        self.assertIn('id: "outputs"', self.main)
        self.assertIn('id: "systems"', self.main)
        self.assertIn('id: "schedule"', self.main)
        for stage_id in (
            "source",
            "spec",
            "generate",
            "review",
            "compile_validate",
            "backtest_recheck",
            "artifacts_report",
        ):
            self.assertIn(f'"{stage_id}"', self.main)
        for backend_stage_id in (
            "strategy_spec",
            "generate_source",
            "source_review",
            "compile_validate",
            "backtest_recheck",
            "final_report",
        ):
            self.assertIn(f'"{backend_stage_id}"', self.main)

    def test_big_portal_is_trading_system_only_and_has_no_callable_actions(self):
        portal_start = self.main.index("codex_mcp_portal: {", self.main.index("const WORKFLOW_DASHBOARD_FALLBACKS"))
        portal_end = self.main.index("\n  left_server_racks:", portal_start)
        portal = self.main[portal_start:portal_end]
        self.assertNotIn('id: "discover_trading_systems"', portal)
        self.assertNotIn('id: "save_discovery_schedule"', portal)
        self.assertNotIn("discover_ea_updates", portal)
        self.assertNotIn('id: "ea_updates"', portal)
        self.assertIn("3 ตระกูล", portal)
        self.assertIn("actions: []", portal)
        self.assertEqual(portal.count("actionIds: []"), 3)
        self.assertIn("09:00 น. Asia/Bangkok", portal)

    def test_big_portal_projects_three_verified_systems_instead_of_generic_reports(self):
        normalize_start = self.main.index("function normalizeTradingSystemPortalDomain")
        normalize_end = self.main.index("function normalizeFxBiasValue", normalize_start)
        normalize = self.main[normalize_start:normalize_end]
        self.assertIn('workflowReportRows(report, "trading_system_discovery_report")', normalize)
        self.assertIn('String(item?.status || "").toLowerCase() === "ready"', normalize)
        self.assertIn("item.metrics.systems.length === 3", normalize)
        self.assertIn("new Set(systems.map((item) => item.strategyFamily)).size === 3", normalize)
        self.assertIn("sources.length !== 2", normalize)
        self.assertIn('String(creator.status || "").toLowerCase() !== "publicly_stated"', normalize)
        self.assertNotIn("JSON.parse", normalize)

        domain_start = self.main.index("function normalizeWorkflowDomainData")
        domain_end = self.main.index("function createWorkflowExternalSource", domain_start)
        domain = self.main[domain_start:domain_end]
        self.assertIn('propId === "codex_mcp_portal"', domain)
        self.assertIn("normalizeTradingSystemPortalDomain(backend, report)", domain)

        renderer_start = self.main.index("function createTradingSystemCard")
        renderer_end = self.main.index("function renderWorkflowDomainPanel", renderer_start)
        renderer = self.main[renderer_start:renderer_end]
        for copy in (
            "ผู้สร้าง/ผู้เผยแพร่",
            "ขั้นตอนเข้า",
            "ขั้นตอนออก",
            "การจัดการออเดอร์",
            "Money & Risk Management",
            "ความเสี่ยงและข้อจำกัด",
            "แหล่งข้อมูลสาธารณะ 2 แห่ง",
        ):
            self.assertIn(copy, renderer)
        self.assertIn("domain.systems.forEach", renderer)

        route_start = self.main.index("function renderWorkflowDomainPanel")
        route_end = self.main.index("function renderWorkflowCatalog", route_start)
        route = self.main[route_start:route_end]
        self.assertIn('subject.id === "codex_mcp_portal"', route)
        self.assertIn('selectedTab.id === "catalog"', route)
        self.assertIn("renderTradingSystemPortalPanel", route)

        for selector in (
            ".workflow-trading-system-portal",
            ".workflow-trading-system-grid",
            ".workflow-trading-system-card",
            ".workflow-trading-system-rules",
            ".workflow-trading-system-risk",
            ".workflow-trading-system-source-links",
        ):
            self.assertIn(selector, self.styles)

    def test_research_vault_has_four_contract_aligned_tabs_and_verified_catalog_projection(self):
        fallback_start = self.main.index(
            "left_server_racks: {",
            self.main.index("const WORKFLOW_DASHBOARD_FALLBACKS"),
        )
        fallback_end = self.main.index("\n  right_server_racks:", fallback_start)
        fallback = self.main[fallback_start:fallback_end]
        tab_positions = [
            fallback.index(f'id: "{tab_id}"')
            for tab_id in ("research", "chart", "backtest", "report")
        ]
        self.assertEqual(tab_positions, sorted(tab_positions))
        self.assertEqual(fallback.count("actionIds:"), 4)
        self.assertIn('tabId: "research"', fallback)
        self.assertIn("ช่วงไม่เกิน 10 ปี", fallback)
        self.assertIn("ไม่สร้างตัวเลขทดแทน", fallback)

        normalize_start = self.main.index("function normalizeTradingSystemResearchLabDomain")
        normalize_end = self.main.index("function tradingResearchNormalizeHeader", normalize_start)
        normalize = self.main[normalize_start:normalize_end]
        self.assertIn("normalizeTradingSystemPortalDomain(portalBackend, portalReport)", normalize)
        self.assertIn("portal.systems.length === 3", normalize)
        self.assertNotIn("JSON.parse", normalize)

        domain_start = self.main.index("function normalizeWorkflowDomainData")
        domain_end = self.main.index("function createWorkflowExternalSource", domain_start)
        domain = self.main[domain_start:domain_end]
        self.assertIn("propId === TRADING_RESEARCH_LAB_PROP_ID", domain)
        self.assertIn("state.propReports.codex_mcp_portal || {}", domain)

        open_start = self.main.index("async function openPropDialog")
        open_end = self.main.index("function setConnectionActionState", open_start)
        open_dialog = self.main[open_start:open_end]
        self.assertIn('loadPropReport("codex_mcp_portal")', open_dialog)
        self.assertIn("await portalReportRequest", open_dialog)

        direct_source_start = self.main.index("function workflowDeepResearchCatalogSources")
        direct_source_end = self.main.index("function getWorkflowSpeechRecognitionConstructor", direct_source_start)
        direct_source = self.main[direct_source_start:direct_source_end]
        self.assertIn('sourcePropId: "codex_mcp_portal"', direct_source)
        self.assertIn('type: "trading_system_discovery_report"', direct_source)
        self.assertIn('status: "verified"', direct_source)
        self.assertIn("directVerifiedCatalog && sources.length === 1", self.main)
        self.assertIn('state.modal.tradingResearchLab.selectedSystemId || systems[0]?.id || ""', self.main)
        self.assertIn('label: "พร้อมวิจัยโดยไม่รออนุมัติ"', self.main)
        self.assertNotIn(
            'เลือกชื่อระบบในฟอร์มด้านล่างแล้วกด “วิจัยระบบที่เลือกต่อ”',
            self.main,
        )

    def test_research_simulation_is_deterministic_educational_only_and_never_reports_metrics(self):
        generate_start = self.main.index("function generateTradingResearchSimulationBars")
        generate_end = self.main.index("function normalizeFxBiasValue", generate_start)
        generator = self.main[generate_start:generate_end]
        self.assertIn("tradingResearchSimulationSeed", generator)
        self.assertNotIn("Math.random", generator)

        simulation_start = self.main.index("function renderTradingResearchSimulation")
        simulation_end = self.main.index("function createTradingResearchDatasetSummary", simulation_start)
        simulation = self.main[simulation_start:simulation_end]
        for copy in (
            "EDUCATIONAL SIMULATION • ไม่ใช่ผลตลาดจริง",
            "ไม่ใช่ Backtest, Forecast หรือผลของระบบที่เลือก",
            "ENTRY",
            "EXIT",
            "ไม่มีการคำนวณกำไร, Win rate หรือ Drawdown",
        ):
            self.assertIn(copy, simulation)
        self.assertNotIn("renderTradingResearchBacktestResult", simulation)
        self.assertEqual(self.main.count('id: "trend_up"'), 1)
        self.assertEqual(self.main.count('id: "sideways"'), 1)
        self.assertEqual(self.main.count('id: "volatility_shock"'), 1)
        self.assertEqual(self.main.count('id: "trend_down"'), 1)

    def test_ohlc_csv_parser_and_backtest_guards_execute_fail_closed(self):
        body = r"""
const rows = ["timestamp,open,high,low,close"];
const start = Date.UTC(2024, 0, 1);
for (let index = 0; index < 260; index += 1) {
  const close = 100 + Math.sin(index / 3) * 4 + index * 0.03;
  rows.push(new Date(start + index * 3600000).toISOString() + ","
    + close + "," + (close + 1) + "," + (close - 1) + "," + close);
}
const parsed = parseTradingResearchCsv(rows.join("\n"));
const malformed = parseTradingResearchCsv(
  "timestamp,open,high,low,close\n2024-01-01T00:00:00Z,10,9,8,10\n2024-01-01T01:00:00Z,10,11,9,10"
);
const range = validateTradingResearchDateRange(parsed.rows, "2024-01-01", "2024-01-11");
const longRange = validateTradingResearchDateRange(
  parsed.rows,
  "2010-01-01",
  "2024-01-11"
);
const timeframe = validateTradingResearchTimeframe(range.rows, "H1");
const wrongTimeframe = validateTradingResearchTimeframe(range.rows, "M5");
const monthlyRows = Array.from({ length: 36 }, (_, index) => ({
  timestamp: Date.UTC(2020, 0, 1) + index * 2592000000,
  open: 100, high: 102, low: 99, close: 101,
}));
const monthlyTimeframe = validateTradingResearchTimeframe(monthlyRows, "MN1");
const strategy = compileTradingResearchStrategy({
  systemName: "RSI-2",
  strategyFamily: "mean_reversion",
  indicatorSettings: [{ name: "RSI", settings: "period 2", role: "entry" }],
  setupConditions: ["Price above 200-day SMA"],
  entrySteps: [{ rule: "RSI(2) below 10" }],
  exitSteps: [{ rule: "Price crosses above 5-day SMA" }],
  tradeManagementSteps: [],
});
const unsupported = compileTradingResearchStrategy({
  systemName: "Fundamental discretionary",
  strategyFamily: "other",
});
const ambiguous = compileTradingResearchStrategy({
  systemName: "RSI-2",
  strategyFamily: "mean_reversion",
  indicatorSettings: [{ name: "RSI", settings: "period 2", role: "entry" }],
  setupConditions: ["Price above 200-day SMA"],
  entrySteps: [{ rule: "RSI(2) below 10" }, { rule: "RSI(2) below 5" }],
  exitSteps: [{ rule: "Price crosses above 5-day SMA" }],
  tradeManagementSteps: [],
});
const backtest = runTradingResearchBacktest(range.rows, strategy);
console.log(JSON.stringify({
  parsed: parsed.ok,
  count: parsed.rows.length,
  malformed: malformed.ok,
  range: range.ok,
  longRange: longRange.ok,
  timeframe: timeframe.ok,
  wrongTimeframe: wrongTimeframe.ok,
  monthlyTimeframe: monthlyTimeframe.ok,
  strategy: strategy.ok,
  unsupported: unsupported.ok,
  ambiguous: ambiguous.ok,
  ambiguousCode: ambiguous.code,
  backtest: backtest.ok,
  metricsFinite: Object.values(backtest.metrics || {}).every(Number.isFinite),
}));
"""
        result = self.run_research_node(body)
        self.assertTrue(result["parsed"])
        self.assertEqual(result["count"], 260)
        self.assertFalse(result["malformed"])
        self.assertTrue(result["range"])
        self.assertFalse(result["longRange"])
        self.assertTrue(result["timeframe"])
        self.assertFalse(result["wrongTimeframe"])
        self.assertTrue(result["monthlyTimeframe"])
        self.assertTrue(result["strategy"])
        self.assertFalse(result["unsupported"])
        self.assertFalse(result["ambiguous"])
        self.assertEqual(result["ambiguousCode"], "ambiguous_rule_translation")
        self.assertTrue(result["backtest"])
        self.assertTrue(result["metricsFinite"])

    def test_csv_and_xlsx_use_the_local_runner_without_network_or_persistence_claims(self):
        read_start = self.main.index("async function readTradingResearchOhlcFile")
        read_end = self.main.index("function tradingResearchDateKey", read_start)
        reader = self.main[read_start:read_end]
        self.assertIn('["csv", "xlsx"].includes(extension)', reader)
        self.assertIn('postJson("/api/props/left_server_racks/ohlc/import"', reader)
        self.assertIn("privacy.networkUpload !== false", reader)
        self.assertIn("privacy.filePersisted !== false", reader)
        self.assertIn("privacy.metaTraderActions !== false", reader)
        self.assertIn("TRADING_RESEARCH_MAX_FILE_BYTES", reader)
        for network_primitive in ("fetch(", "fetchJson(", "FormData", "XMLHttpRequest"):
            self.assertNotIn(network_primitive, reader)

        body = r"""
(async () => {
  globalThis.window = { btoa: (value) => Buffer.from(value, "binary").toString("base64") };
  globalThis.safeDashboardDisplayText = (value, fallback = "") => String(value || fallback);
  let request = null;
  globalThis.postJson = async (path, payload) => {
    request = { path, payload };
    return {
      ok: true,
      kind: "ohlc_import_ready",
      timeframe: "H1",
      rowCount: 2,
      bars: [
        { time: "2025-01-01T00:00:00", open: 100, high: 102, low: 99, close: 101 },
        { time: "2025-01-01T01:00:00", open: 101, high: 103, low: 100, close: 102 },
      ],
      file: { sha256: "a".repeat(64) },
      privacy: { localOnly: true, networkUpload: false, filePersisted: false, metaTraderActions: false },
    };
  };
  const result = await readTradingResearchOhlcFile({
    name: "prices.xlsx",
    size: 10,
    arrayBuffer: async () => Uint8Array.from([80, 75, 3, 4]).buffer,
  }, "H1");
  console.log(JSON.stringify({
    ok: result.ok,
    format: result.format,
    rows: result.rows?.length,
    path: request?.path,
    sentBase64: typeof request?.payload?.contentBase64 === "string",
  }));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""
        result = self.run_research_node(body)
        self.assertTrue(result["ok"])
        self.assertEqual(result["format"], "XLSX")
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["path"], "/api/props/left_server_racks/ohlc/import")
        self.assertTrue(result["sentBase64"])

    def test_backtest_requires_complete_rules_real_ohlc_and_bounded_timeframe(self):
        compile_start = self.main.index("function compileTradingResearchStrategy")
        compile_end = self.main.index("function tradingResearchSma", compile_start)
        compiler = self.main[compile_start:compile_end]
        self.assertIn('code: "unsupported_rule_family"', compiler)
        self.assertIn('code: "incomplete_rule_translation"', compiler)
        self.assertIn('code: "ambiguous_rule_translation"', compiler)
        self.assertIn("ไม่เลือกค่าหนึ่งแทนผู้ใช้", compiler)
        self.assertIn("unsupportedManagement", compiler)
        self.assertIn("ไม่สร้างตัวเลข Backtest", compiler)

        backtest_start = self.main.index("function runTradingResearchBacktest")
        backtest_end = self.main.index("function tradingResearchSimulationSeed", backtest_start)
        backtest = self.main[backtest_start:backtest_end]
        self.assertIn("!strategy?.ok", backtest)
        self.assertIn('strategy.kind !== "rsi2_long_mean_reversion"', backtest)
        self.assertIn("ยังไม่รวม Spread, Commission, Slippage, Swap หรือ Position sizing", backtest)
        self.assertNotIn("generateTradingResearchSimulationBars", backtest)
        self.assertNotIn("Math.random", backtest)

        validation_start = self.main.index("function validateTradingResearchDateRange")
        validation_end = self.main.index("function tradingResearchRuleText", validation_start)
        validation = self.main[validation_start:validation_end]
        self.assertIn("TRADING_RESEARCH_MAX_RANGE_MS", validation)
        self.assertIn("ช่วง Backtest ต้องไม่เกิน 10 ปี", validation)
        self.assertIn("validateTradingResearchTimeframe", validation)
        self.assertIn("ระยะห่างแท่งไม่ตรงกับ", validation)

    def test_frontend_timeframes_match_local_runner_ohlc_contract(self):
        backend = (ROOT / "backend" / "local-runner" / "ohlc_import.py").read_text(encoding="utf-8")
        match = re.search(r"ALLOWED_TIMEFRAMES\s*=\s*frozenset\(\{([^}]+)\}\)", backend)
        self.assertIsNotNone(match)
        backend_timeframes = set(re.findall(r'"([A-Z0-9]+)"', match.group(1)))
        frontend_start = self.main.index("const TRADING_RESEARCH_TIMEFRAME_MS")
        frontend_end = self.main.index("\n});", frontend_start)
        frontend_timeframes = set(re.findall(r"^\s{2}([A-Z0-9]+):", self.main[frontend_start:frontend_end], re.MULTILINE))
        self.assertEqual(frontend_timeframes, backend_timeframes)
        self.assertIn("MN1", frontend_timeframes)
        self.assertIn("MN1: 30 * 24 * 60 * 60 * 1000", self.main[frontend_start:frontend_end])

    def test_research_report_never_promotes_simulation_or_missing_backtest_numbers(self):
        summary_start = self.main.index("function renderTradingResearchSummary")
        summary_end = self.main.index("function renderTradingResearchLabPanel", summary_start)
        summary = self.main[summary_start:summary_end]
        self.assertIn("REPORT ที่ไม่สร้างตัวเลขทดแทน", summary)
        self.assertIn("กราฟ Educational Simulation จะไม่ถูกนับเป็นผลทดสอบ", summary)
        self.assertIn("session.backtest?.ok", summary)
        self.assertIn("ยังไม่มีผล Backtest สำหรับระบบนี้", summary)
        self.assertNotIn("generateTradingResearchSimulationBars", summary)

        renderer_start = self.main.index("function renderTradingResearchLabPanel")
        renderer_end = self.main.index("function renderWorkflowDomainPanel", renderer_start)
        renderer = self.main[renderer_start:renderer_end]
        for tab_id in ("research", "chart", "backtest", "report"):
            self.assertIn(f'tabId === "{tab_id}"', renderer)
        self.assertIn("metrics.systems แบบ array ครบ 3 ระบบ", renderer)

        for selector in (
            ".workflow-trading-research-lab",
            ".workflow-research-lab-header",
            ".workflow-research-system-selector",
            ".workflow-research-candlestick-chart",
            ".workflow-research-backtest-form",
            ".workflow-research-backtest-result",
        ):
            self.assertIn(selector, self.styles)

    def test_research_catalog_load_order_is_truthful_and_refreshes_portal_dependency(self):
        normalize_start = self.main.index("function normalizeTradingSystemResearchLabDomain")
        normalize_end = self.main.index("function getTradingResearchLabSession", normalize_start)
        normalizer = self.main[normalize_start:normalize_end]
        self.assertIn("portalLoadState = {}", normalizer)
        self.assertIn('catalogStatus = hasVerifiedCatalog', normalizer)
        self.assertIn('? "ready"', normalizer)
        self.assertIn(': (["loading", "error"].includes(rawCatalogStatus)', normalizer)
        self.assertIn("catalogLoading: catalogStatus === \"loading\"", normalizer)
        self.assertIn("catalogError: catalogStatus === \"error\"", normalizer)

        panel_start = self.main.index("function createTradingResearchLabHeader")
        panel_end = self.main.index("function renderWorkflowDomainPanel", panel_start)
        panel = self.main[panel_start:panel_end]
        self.assertIn("กำลังโหลดข้อมูลจาก Backend", panel)
        self.assertIn("ระบบจะไม่แสดงข้อมูลว่างหรือเปิดปุ่มวิจัยก่อนเวลา", panel)
        self.assertIn('"loading"', panel)
        self.assertIn('role", "status"', panel)
        self.assertIn('aria-live", "polite"', panel)
        self.assertIn('role", "alert"', panel)

        action_start = self.main.index("function workflowAvailabilityCopy")
        action_end = self.main.index("function getWorkflowSpeechRecognitionConstructor", action_start)
        action = self.main[action_start:action_end]
        self.assertIn('action.id === "deep_research_system" && catalogStatus === "loading"', action)
        self.assertIn("กำลังโหลดระบบจาก Backend...", action)
        self.assertIn("ปุ่มวิจัยจะเปิดเมื่อได้รับ Report ที่ยืนยันแล้ว", action)
        self.assertIn("select.disabled = !sources.length", action)

        poll_start = self.main.index("async function pollOpenPropReport")
        poll_end = self.main.index("function startMissionPolling", poll_start)
        poller = self.main[poll_start:poll_end]
        self.assertIn('? [propId, "codex_mcp_portal"]', poller)
        self.assertIn("Promise.all", poller)
        self.assertIn("dependencyPropIds.map", poller)

    def test_research_reports_bind_to_exact_source_report_and_selected_system(self):
        helper_start = self.main.index("function tradingResearchReportsForSystem")
        helper_end = self.main.index("function renderTradingResearchDetail", helper_start)
        helper = self.main[helper_start:helper_end]
        source = helper + r"""
const domain = {
  sourceReportId: "portal-report-1",
  researchReports: [
    { id: "exact", workflowContext: { source: { reportId: "portal-report-1", recordId: "rsi-2" } } },
    { id: "wrong-system", workflowContext: { source: { reportId: "portal-report-1", recordId: "canslim" } } },
    { id: "wrong-report", workflowContext: { source: { reportId: "portal-report-0", recordId: "rsi-2" } } },
    { id: "unbound" },
  ],
};
console.log(JSON.stringify({
  rsi: tradingResearchReportsForSystem(domain, { id: "rsi-2" }).map((row) => row.id),
  turtle: tradingResearchReportsForSystem(domain, { id: "turtle" }).map((row) => row.id),
  missingSource: tradingResearchReportsForSystem({ ...domain, sourceReportId: "" }, { id: "rsi-2" }).length,
}));
"""
        result = self.run_node_json(source)
        self.assertEqual(result["rsi"], ["exact"])
        self.assertEqual(result["turtle"], [])
        self.assertEqual(result["missingSource"], 0)

        detail_start = self.main.index("function renderTradingResearchDetail")
        detail_end = self.main.index("function tradingResearchMovingAverage", detail_start)
        detail = self.main[detail_start:detail_end]
        self.assertIn("tradingResearchReportsForSystem(domain, system)[0]", detail)
        self.assertIn('className = "workflow-research-result-provenance"', detail)
        self.assertIn("matchingResearch.linkedMissionId", detail)
        summary_start = self.main.index("function renderTradingResearchSummary")
        summary_end = self.main.index("function renderTradingResearchLabPanel", summary_start)
        summary = self.main[summary_start:summary_end]
        self.assertIn("const selectedResearchReports = tradingResearchReportsForSystem(domain, system)", summary)
        self.assertIn("String(selectedResearchReports.length) + \" Report\"", summary)

        dashboard_start = self.main.index("function renderWorkflowDashboard")
        dashboard_end = self.main.index("function setWorkflowDashboardTab", dashboard_start)
        dashboard = self.main[dashboard_start:dashboard_end]
        self.assertIn("const isDirectResearchDashboard = subject.id === TRADING_RESEARCH_LAB_PROP_ID", dashboard)
        self.assertIn("isFxNewsDashboard || isDirectResearchDashboard", dashboard)
        self.assertIn('["right_server_racks", "right_tool_console", "terminal_workstation"].includes(subject.id)', dashboard)
        self.assertNotIn('["left_server_racks", "right_server_racks", "right_tool_console", "terminal_workstation"]', dashboard)

    def test_out_of_order_agent_missions_use_newest_meaningful_activity(self):
        active_start = self.main.index("function getActiveMissionForAgent")
        active_end = self.main.index("function getAgentSidebarState", active_start)
        activity_start = self.main.index("function getMissionActivityTime")
        activity_end = self.main.index("function isMissionCompletedToday", activity_start)
        source = "\n".join((
            "const state = { missions: [] };",
            "function getAgentIdFromOwner(owner) { return owner; }",
            "function getMissionPresentationStatus(mission) { return mission.status; }",
            self.main[active_start:active_end],
            self.main[activity_start:activity_end],
            r"""
const oldFailed = { id: "old-failed", owner: "mission_archivist", status: "failed", updatedAt: "2026-08-22T11:40:00Z" };
const newerCompleted = { id: "new-completed", owner: "mission_archivist", status: "completed", completedAt: "2026-08-22T11:55:00Z" };
state.missions = [oldFailed, newerCompleted];
const ordered = getActiveMissionForAgent("mission_archivist");
state.missions = [newerCompleted, oldFailed];
const reversed = getActiveMissionForAgent("mission_archivist");
state.missions.push({ id: "new-running", owner: "mission_archivist", status: "running", startedAt: "2026-08-22T12:00:00Z" });
const active = getActiveMissionForAgent("mission_archivist");
console.log(JSON.stringify({ ordered, reversed, activeId: active?.id || null }));
""",
        ))
        result = self.run_node_json(source)
        self.assertIsNone(result["ordered"])
        self.assertIsNone(result["reversed"])
        self.assertEqual(result["activeId"], "new-running")

    def test_research_controls_and_statuses_have_accessible_truthful_states(self):
        simulation_start = self.main.index("function renderTradingResearchSimulation")
        simulation_end = self.main.index("function createTradingResearchDatasetSummary", simulation_start)
        simulation = self.main[simulation_start:simulation_end]
        self.assertIn('controls.setAttribute("role", "group")', simulation)
        self.assertIn('canvas.setAttribute("role", "img")', simulation)
        self.assertIn('button.setAttribute("aria-pressed"', simulation)

        dataset_start = self.main.index("function createTradingResearchDatasetSummary")
        dataset_end = self.main.index("function tradingResearchResultMetric", dataset_start)
        dataset = self.main[dataset_start:dataset_end]
        self.assertIn('summary.setAttribute("role", "status")', dataset)
        self.assertIn('summary.setAttribute("aria-live", "polite")', dataset)

        backtest_start = self.main.index("function renderTradingResearchBacktestResult")
        backtest_end = self.main.index("function renderTradingResearchBacktest(", backtest_start)
        backtest = self.main[backtest_start:backtest_end]
        self.assertIn('panel.setAttribute("role", "region")', backtest)
        self.assertIn('panel.setAttribute("aria-label"', backtest)

        css_start = self.styles.index(".workflow-trading-research-lab")
        css_end = self.styles.index(".workflow-radar-website-tool", css_start)
        research_css = self.styles[css_start:css_end]
        self.assertNotRegex(research_css, r"font-size:\s*(?:9|10)px")
        self.assertIn('.workflow-research-notice[data-tone="loading"]', research_css)
        self.assertIn('.workflow-research-notice[data-tone="error"]', research_css)
        self.assertIn(".workflow-research-result-provenance", research_css)

    def test_radar_shows_backend_next_run_even_after_daily_cap_is_reached(self):
        start = self.main.index("function createRadarRailTruthCard")
        end = self.main.index("function createBackendOwnedDailyScheduleCard", start)
        rail = self.main[start:end]
        next_run = rail.index('["รอบถัดไป", schedule.nextRunAt')
        effective = rail.index("schedule.effectiveEnabled", next_run)
        formatted = rail.index("formatThaiDateTime(schedule.nextRunAt)", next_run)
        self.assertLess(next_run, formatted)
        self.assertLess(formatted, effective)

    def test_stale_backend_owned_actions_are_filtered_and_cannot_submit(self):
        denylist_start = self.main.index("const BACKEND_OWNED_DAILY_ACTION_IDS")
        denylist_end = self.main.index("\n]);", denylist_start)
        denylist = self.main[denylist_start:denylist_end]
        for action_id in (
            "discover_trading_systems",
            "save_discovery_schedule",
            "discover_new_indicators",
            "save_indicator_scout_schedule",
        ):
            self.assertIn(f'"{action_id}"', denylist)

        normalize_start = self.main.index("function normalizeWorkflowDashboard")
        normalize_end = self.main.index("function getWorkflowSelectedTab", normalize_start)
        normalize = self.main[normalize_start:normalize_end]
        self.assertIn("!BACKEND_OWNED_DAILY_ACTION_IDS.has(action.id)", normalize)
        self.assertIn("requestedActionIds.filter((actionId) => actionMap.has(actionId))", normalize)

        rail_start = self.main.index("function workflowRailActions")
        rail_end = self.main.index("function createWorkflowUseGuideCard", rail_start)
        rail = self.main[rail_start:rail_end]
        self.assertIn('["codex_mcp_portal", INDICATOR_SCOUT_PROP_ID].includes(subject?.id)', rail)
        self.assertIn("return [];", rail)

        submit_start = self.main.index("async function submitWorkflowDashboardAction")
        submit_end = self.main.index("function renderPropDashboard", submit_start)
        submit = self.main[submit_start:submit_end]
        guard = "if (BACKEND_OWNED_DAILY_ACTION_IDS.has(actionId)) return;"
        self.assertIn(guard, submit)
        self.assertLess(submit.index(guard), submit.index("postJson("))

    def test_each_workflow_device_opens_on_main_work_and_only_history_devices_end_with_reports(self):
        expected_last_ids = {
            "codex_mcp_portal": "catalog",
            "left_signal_cube": "history",
            "left_server_racks": "report",
            "right_server_racks": "final_report",
            "right_tool_console": "history",
            "left_audit_crystals": "archive",
            "terminal_workstation": "outputs",
        }
        no_history_props = {"right_status_crystals"}
        single_view_props = {"right_status_crystals": "connections"}
        for prop_id in WORKFLOW_PROP_IDS:
            role = self.role_map[prop_id]
            tabs = role["localTabs"]
            ux = role["dashboardUx"]
            with self.subTest(prop_id=prop_id):
                if prop_id in single_view_props:
                    self.assertEqual(len(tabs), 1)
                    self.assertEqual(tabs[0]["id"], single_view_props[prop_id])
                else:
                    self.assertGreaterEqual(len(tabs), 2)
                self.assertEqual(role["defaultTab"], tabs[0]["id"])
                self.assertEqual(ux["mainWorkTabId"], tabs[0]["id"])
                if prop_id in no_history_props:
                    self.assertIsNone(ux["historyReportTabId"])
                    self.assertIsNone(ux["historyReportTabPosition"])
                    self.assertNotIn(tabs[-1]["id"], {"schedule_history", "activity_history"})
                    continue
                self.assertEqual(ux["historyReportTabId"], expected_last_ids[prop_id])
                self.assertEqual(tabs[-1]["id"], expected_last_ids[prop_id])
                self.assertEqual(
                    tabs[-1]["labelTh"],
                    (
                        "ประวัติข่าว"
                        if prop_id == "left_signal_cube"
                        else (
                            "สรุป Report"
                            if prop_id == "left_server_racks"
                            else ("7 ไฟล์และ Report" if prop_id == "right_server_racks" else "ประวัติและรายงาน")
                        )
                    ),
                )
                self.assertEqual(ux["historyReportTabPosition"], "last")

        self.assertIn("const WORKFLOW_DASHBOARD_PRIMARY_TABS", self.main)
        self.assertIn("const WORKFLOW_DASHBOARD_SETTING_TAB_IDS", self.main)
        self.assertIn("const WORKFLOW_DASHBOARD_HISTORY_TAB_IDS", self.main)
        self.assertIn(
            "const visibleTabs = normalizedTabs.filter((tab) => !WORKFLOW_DASHBOARD_SETTING_TAB_IDS.has(tab.id));",
            self.main,
        )
        self.assertIn('id: "history",\n      labelTh: "ประวัติและรายงาน"', self.main)
        self.assertIn(
            'const isPortalCatalog = subject?.id === "codex_mcp_portal" && tab.id === "catalog";',
            self.main,
        )
        self.assertIn('isPortalCatalog ? "คลังและแบบฟอร์มข้อมูล"', self.main)
        self.assertIn("return tabs.find((tab) => tab.id === requested) || tabs[0] || null;", self.main)
        self.assertIn('isHistory ? "ประวัติและรายงาน"', self.main)

    def test_portal_catalog_label_does_not_duplicate_the_final_history_tab(self):
        start = self.main.index("const visibleTabs = normalizedTabs.filter")
        end = self.main.index("const deliveredSourceRows", start)
        normalization = self.main[start:end]
        catalog_label = re.search(r'isPortalCatalog \? "([^"]+)"', normalization)
        history_label = re.search(r'isHistory \? "([^"]+)"', normalization)

        self.assertIsNotNone(catalog_label)
        self.assertIsNotNone(history_label)
        self.assertEqual(catalog_label.group(1), "คลังและแบบฟอร์มข้อมูล")
        self.assertEqual(history_label.group(1), "ประวัติและรายงาน")
        self.assertNotEqual(catalog_label.group(1), history_label.group(1))
        self.assertIn('visibleTabs.push({\n      id: "history"', normalization)

    def test_view_only_tabs_are_truthful_and_survive_backend_schema_merging(self):
        self.assertIn("อัปเดตจาก Google Sheet กลาง", self.main)
        self.assertIn("Frontend ไม่รับ Credential หรือ Token", self.main)
        self.assertIn("Pine Script ใช้ Code Validation เท่านั้น", self.main)
        self.assertIn("ยังไม่มีผล Visual Backtest จริง", self.main)
        self.assertIn("ระบบจะไม่แสดง Win Rate, Profit Factor หรือ Drawdown", self.main)
        self.assertIn('root.schemaVersion === "ea-factory-v1"', self.main)
        self.assertIn('root.mode === "manual_stage_by_stage"', self.main)
        self.assertIn("root.scheduled === false", self.main)
        self.assertIn("const suppliedTabMap = new Map", self.main)
        self.assertIn("(fallback.tabs || []).length", self.main)
        self.assertIn("selectedTab?.emptyMessageTh ||", self.main)

    def test_device_identity_is_used_for_theming_without_duplicate_main_header(self):
        identity_start = self.main.index("const WORKFLOW_DASHBOARD_IDENTITIES")
        identity_end = self.main.index("\n});", identity_start)
        identity_block = self.main[identity_start:identity_end]
        for identity in (
            "world-radar",
            "research-vault",
            "ea-factory",
            "experiment-lab",
            "indicator-scout",
            "market-news-bias",
            "ea-dev-desk",
            "hq-vps-settings",
        ):
            self.assertIn(f'id: "{identity}"', identity_block)
        self.assertNotIn("WORKFLOW_PIPELINE", self.main)
        self.assertNotIn("WORKFLOW_OPERATIONS_PIPELINE", self.main)
        self.assertNotIn("renderWorkflowPipeline", self.main)
        self.assertNotIn("data-workflow-prop", self.main)
        self.assertNotIn("workflow-pipeline", self.styles)
        self.assertNotIn("workflowDashboardIdentityMark", self.main)
        self.assertNotIn("workflowDashboardIdentityLabel", self.main)
        self.assertNotIn("workflowDashboardStage", self.main)
        self.assertNotIn("workflowDashboardTitle", self.main)
        self.assertNotIn("workflowDashboardSummary", self.main)

        tabs_start = self.main.index("function renderWorkflowTabs")
        tabs_end = self.main.index("function workflowAvailabilityCopy", tabs_start)
        tabs_block = self.main[tabs_start:tabs_end]
        self.assertNotIn("index + 1", tabs_block)
        self.assertIn("propId === EA_FACTORY_PROP_ID", tabs_block)
        self.assertIn('createElement("span")', tabs_block)
        self.assertIn('createElement("small")', tabs_block)
        self.assertIn("button.disabled = Boolean(factoryLocked)", tabs_block)
        self.assertIn("button.textContent = tab.labelTh", tabs_block)

    def test_catalog_renders_42_field_template_and_deduplication_truth(self):
        start = self.main.index("const WORKFLOW_DISCOVERY_SHEET_COLUMNS")
        end = self.main.index("\n]);", start)
        columns = re.findall(r'^\s*"([a-z][a-z0-9_]*)",?$', self.main[start:end], re.M)
        self.assertEqual(len(columns), 42)
        self.assertEqual(columns[0], "discovery_id")
        self.assertEqual(columns[-1], "notes")
        self.assertIn("template.columns.length", self.main)
        self.assertIn("การเชื่อม Google Sheets", self.main)
        self.assertIn("Backend ยังไม่ยืนยันว่ารวมแถวจาก Google Sheet กลางแล้ว", self.main)
        self.assertIn("พร้อมตรวจรายการซ้ำกับ Report ในเครื่อง", self.main)
        self.assertIn("Frontend ไม่รับ Token, Credential หรือ Secret", self.main)
        self.assertIn("credentialsAcceptedByFrontend: false", self.main)

    def test_workflow_actions_wait_for_authoritative_read_model_without_false_connection_error(self):
        normalize_start = self.main.index("function normalizeWorkflowDashboard")
        normalize_end = self.main.index("function getWorkflowSelectedTab", normalize_start)
        normalize = self.main[normalize_start:normalize_end]
        availability_start = self.main.index("function workflowAvailabilityCopy")
        availability_end = self.main.index("function createWorkflowSourceSelect", availability_start)
        availability = self.main[availability_start:availability_end]
        card_start = self.main.index("function createWorkflowActionCard")
        card_end = self.main.index("function renderWorkflowAutomationSummary", card_start)
        card = self.main[card_start:card_end]
        open_start = self.main.index("async function openPropDialog")
        open_end = self.main.index("function setConnectionActionState", open_start)
        open_dialog = self.main[open_start:open_end]

        self.assertIn("const hasAuthoritativeReadModel = Array.isArray(backend.actions)", normalize)
        self.assertIn("workflowReadModel,", normalize)
        self.assertIn("workflowReadModel.authoritative !== true", availability)
        self.assertIn('label: "กำลังตรวจสอบสถานะ..."', availability)
        self.assertIn('label: "โหลดสถานะไม่สำเร็จ"', availability)
        self.assertIn("ปิดและเปิดอุปกรณ์นี้ใหม่เพื่อลองอีกครั้ง", availability)
        self.assertIn("dashboard.workflowReadModel?.authoritative === true", card)
        self.assertIn("submit.disabled = !canSubmit || inFlight", card)
        self.assertLess(open_dialog.index("const reportRequest = loadPropReport(propId)"), open_dialog.index("openGameModal("))
        self.assertIn("await reportRequest", open_dialog)
        self.assertIn("state.modal.id === propId", open_dialog)

    def test_workflow_submit_has_opaque_retry_safe_idempotency(self):
        self.assertIn("function createWorkflowIdempotencyKey", self.main)
        self.assertIn("globalThis.crypto?.randomUUID?.()", self.main)
        self.assertIn("function workflowActionFormSignature", self.main)
        self.assertIn('previousAction.tone === "error"', self.main)
        self.assertIn("previousAction.formSignature === formSignature", self.main)
        self.assertIn("idempotencyKey,", self.main)
        request = re.search(
            r"postJson\(`/api/props/\$\{encodeURIComponent\(propId\)\}/workflow/actions`,\s*\{(?P<body>.*?)\}\);",
            self.main,
            re.S,
        )
        self.assertIsNotNone(request)
        self.assertNotRegex(request.group("body"), re.compile(r"\b(?:token|password|secret|cookie)\b", re.I))

    def test_workflow_source_selection_and_clickable_result_details_are_wired(self):
        self.assertIn('id: "sourceReportId"', self.main)
        self.assertIn("createWorkflowSourceSelect", self.main)
        self.assertIn("backend.agentDeliveredSources", self.main)
        self.assertNotIn("backend.upstreamSources", self.main)
        self.assertIn("dashboard.agentDeliveredSources", self.main)
        self.assertNotIn("dashboard.upstreamSources", self.main)
        self.assertIn("Report ที่ Agent ส่งเข้ามาผ่าน Mission", self.main)
        self.assertIn("openDashboardResultDetail(source, card)", self.main)
        self.assertIn("findWorkflowCurrentPropReportProjection", self.main)
        self.assertIn("renderDashboardWorkColumn(els.workflowRunningList", self.main)
        self.assertIn("renderDashboardWorkColumn(els.workflowCompletedList", self.main)
        self.assertIn("renderDashboardWorkColumn(els.workflowBlockedList", self.main)

    def test_report_handoff_is_explicit_agent_mission_flow_without_direct_navigation(self):
        left_rail_start = self.index.index('id="modalPortraitPanel"')
        left_rail_end = self.index.index('<div class="modal-content-panel">', left_rail_start)
        left_rail = self.index[left_rail_start:left_rail_end]
        self.assertIn("Backend จะบันทึก Mission และเส้นทางของ Report ก่อนส่งต่อ", left_rail)
        self.assertIn("ให้ Agent ส่งต่อ Report", left_rail)
        handoff_start = self.main.index("async function submitWorkflowAgentHandoff")
        handoff_end = self.main.index("function renderWorkflowDashboard", handoff_start)
        handoff = self.main[handoff_start:handoff_end]
        self.assertRegex(
            handoff,
            re.compile(
                r"postJson\(`/api/props/\$\{encodeURIComponent\(targetPropId\)\}/workflow/transfers`,\s*\{\s*actionId,\s*sourceReportId:\s*reportId,\s*idempotencyKey,?\s*\}\)",
                re.S,
            ),
        )
        self.assertNotIn("assignTask(", handoff)
        self.assertIn('result?.kind !== "agent_report_transfer_recorded"', handoff)
        self.assertIn("mergeBackendMission(mission)", handoff)
        self.assertIn("loadPropReport(subject.id)", handoff)
        self.assertIn("loadPropReport(targetPropId)", handoff)
        self.assertIn("routeAgentToTargetId(transferAgentId, targetPropId", handoff)
        self.assertIn("ยังไม่ได้เริ่มงานปลายทาง", handoff)
        self.assertNotIn("openPropDialog", handoff)
        self.assertNotIn("openGameModal", handoff)

    def test_agent_handoff_and_settings_are_context_aware(self):
        settings_start = self.main.index("function renderWorkflowSettingsRail")
        settings_end = self.main.index("function getWorkflowHandoffReports", settings_start)
        settings = self.main[settings_start:settings_end]
        handoff_start = self.main.index("function renderWorkflowAgentHandoff")
        handoff_end = self.main.index("function workflowHandoffErrorMessage", handoff_start)
        handoff = self.main[handoff_start:handoff_end]

        self.assertIn("function workflowRailActions", self.main)
        self.assertIn("WORKFLOW_DASHBOARD_SETTING_ACTION_IDS.has(left.id)", self.main)
        self.assertIn("els.workflowSettingsRail.hidden = false", settings)
        self.assertIn("createWorkflowUseGuideCard(subject)", settings)
        self.assertIn("els.workflowSettingsRailContent.innerHTML = \"\"", settings)
        self.assertIn("els.workflowAgentHandoffRail.hidden = !selectedRoute", handoff)
        self.assertIn("getWorkflowReportTransferRoutes(subject.id, selectedReport)", handoff)
        self.assertIn("els.workflowHandoffButton.disabled = !selectedRoute", handoff)

    def test_main_tab_is_friendly_and_reports_only_render_on_the_last_tab(self):
        overview_start = self.main.index("function renderWorkflowPrimaryOverview")
        overview_end = self.main.index("function findWorkflowCurrentPropReportProjection", overview_start)
        overview = self.main[overview_start:overview_end]
        render_start = self.main.index("function renderWorkflowDashboard")
        render_end = self.main.index("function setWorkflowDashboardTab", render_start)
        render = self.main[render_start:render_end]

        self.assertIn("const isPrimaryTab = selectedTab?.id === dashboard.tabs[0]?.id", render)
        self.assertIn("const isHistoryTab = WORKFLOW_DASHBOARD_HISTORY_TAB_IDS.has(selectedTab?.id)", render)
        self.assertIn("els.workflowResultsPanel.hidden = isFxNewsDashboard", render)
        self.assertIn('isFxNewsDashboard ? "ประวัติอัปเดตข่าว" : "ประวัติและรายงาน"', render)
        self.assertIn("if (!isPrimaryTab && !isHistoryTab)", render)
        self.assertIn('note.className = "workflow-empty-message"', render)
        self.assertIn(
            '"ยังไม่มีข้อมูลในส่วนนี้ เมื่อ Local Runner ส่งผลกลับมาระบบจะแสดงที่นี่"',
            render,
        )
        self.assertLess(
            render.index("renderWorkflowDomainPanel("),
            render.index("renderWorkflowPrimaryOverview("),
        )
        self.assertLess(
            render.index("renderWorkflowPrimaryOverview("),
            render.index("if (actions.length)"),
        )
        self.assertIn('copy.textContent = "ยังไม่มีผลล่าสุดจาก Local Runner"', overview)
        self.assertIn("const primaryAction = actions[0] || null", overview)
        self.assertEqual(overview.count('className = "modal-action primary workflow-primary-empty-cta"'), 1)
        self.assertIn("findWorkflowCurrentPropReportProjection", overview)

    def test_report_handoff_allow_list_is_fail_closed_and_matches_backend_routes(self):
        route_start = self.main.index("const WORKFLOW_REPORT_TRANSFER_ROUTES")
        route_end = self.main.index("\n]);", route_start)
        route_block = self.main[route_start:route_end]
        for action_id in (
            "deep_research_system",
            "build_strategy_code",
            "review_source_code",
            "prepare_backtest_plan",
            "prepare_optimization_plan",
            "prepare_ea_discovery_plan",
            "inspect_ea_source",
            "develop_ea_source",
            "propose_ea_performance_improvements",
        ):
            self.assertIn(f'actionId: "{action_id}"', route_block)
        self.assertEqual(route_block.count('"codex_mcp_portal"'), 1)
        self.assertIn('sourcePropIds: ["codex_mcp_portal"]', route_block)
        self.assertIn('sourcePropIds: ["left_server_racks"]', route_block)
        self.assertIn(
            'sourcePropIds: ["left_server_racks", "right_server_racks"]',
            route_block,
        )
        self.assertNotIn('actionId: "build_fx_pair_bias"', route_block)
        self.assertIn("WORKFLOW_REPORT_TRANSFER_READY_STATUSES", self.main)
        self.assertIn("getWorkflowReportTransferRoutes", self.main)
        self.assertIn("Report นี้ไม่มีเส้นทางปลายทางที่ Backend อนุญาต", self.main)
        self.assertIn("workflowHandoffFormSignature", self.main)
        self.assertIn('previousHandoff.tone === "error"', self.main)

    def test_backend_field_aliases_are_supported(self):
        self.assertIn('source_report: "source"', self.main)
        self.assertIn('boolean: "checkbox"', self.main)
        self.assertIn('time_list: "list"', self.main)
        self.assertIn('integer: "number"', self.main)
        self.assertIn('"settings_only"', self.main)

    def test_task_routing_matches_the_new_equipment_roles(self):
        expected_routes = (
            'taskKeywords.deepResearch)) return "left_server_racks"',
            'taskKeywords.eaDiscovery)) return "right_tool_console"',
            'taskKeywords.backtest)) return "right_tool_console"',
            'taskKeywords.optimization)) return "right_tool_console"',
            'taskKeywords.globalDiscovery)) return "codex_mcp_portal"',
            'taskKeywords.eaBuild)) return "right_server_racks"',
        )
        for route in expected_routes:
            self.assertIn(route, self.main)

    def test_workspace_has_responsive_no_overlap_layout_and_accessible_tabs(self):
        self.assertIn(".workflow-dashboard-workspace", self.styles)
        self.assertIn(".workflow-settings-rail", self.styles)
        self.assertIn(".workflow-settings-rail[hidden]", self.styles)
        self.assertIn(".workflow-agent-handoff", self.styles)
        self.assertIn(".workflow-agent-handoff[hidden]", self.styles)
        self.assertIn(".workflow-results[hidden]", self.styles)
        self.assertIn(".workflow-primary-overview", self.styles)
        self.assertIn(".workflow-primary-empty", self.styles)
        self.assertIn(".workflow-command-deck", self.styles)
        self.assertIn(".workflow-dashboard-scroll", self.styles)
        self.assertIn("overflow-y: auto", self.styles)
        self.assertIn("@media (max-width: 900px)", self.styles)
        self.assertIn(".workflow-result-columns", self.styles)
        self.assertIn('role="tablist"', self.index)
        self.assertIn('aria-live="polite"', self.index)
        self.assertIn('setAttribute("aria-selected", active ? "true" : "false")', self.main)
        self.assertIn('event.key === "ArrowRight"', self.main)

    def test_custom_plugin_profile_and_automatic_schedule_truth_are_visible(self):
        self.assertIn("rawPluginProfile", self.main)
        self.assertIn('pluginSkillId: safeDashboardDisplayText', self.main)
        self.assertIn('automationMode', self.main)
        self.assertIn('className = "workflow-plugin-profile"', self.main)
        self.assertIn('className = "workflow-automation-summary"', self.main)
        self.assertIn("renderWorkflowAutomationSummary", self.main)
        self.assertIn("schedule?.automaticRunsImplemented === true", self.main)
        self.assertIn("schedule.requestedEnabled ?? schedule.enabled", self.main)
        self.assertIn("schedule.nextRunAt", self.main)
        self.assertIn("schedule.lastRunAt", self.main)
        self.assertIn(".workflow-plugin-profile", self.styles)
        self.assertIn(".workflow-automation-summary", self.styles)

    def test_custom_plugin_wording_does_not_claim_direct_dispatch(self):
        self.assertIn("function workflowProcedurePresentation", self.main)
        self.assertIn('title: "Codex ใช้ขั้นตอนจาก Custom Plugin"', self.main)
        self.assertIn('"ขั้นตอน Backend ที่ปรับจาก Custom Plugin"', self.main)
        self.assertIn('"ขั้นตอน Backend"', self.main)
        self.assertIn("Backend นำความต้องการจาก Custom Plugin มาทำเป็นขั้นตอนคลิกเดียว", self.main)
        self.assertIn("ไม่ใช่การเรียก Plugin โดยตรงจากหน้าเว็บ", self.main)
        self.assertIn("ยังไม่พบ Custom Plugin นี้ใน Codex ของผู้ใช้", self.main)
        self.assertIn("Version ไม่ตรงกัน", self.main)
        self.assertIn("Workflow ต้องการ", self.main)
        self.assertNotIn(" / Plugin → Local Runner", self.main)

    def test_platform_selection_updates_the_visible_backend_and_reference_profile(self):
        self.assertIn("function workflowPluginProfileForSelection", self.main)
        self.assertIn("pluginSelectionField", self.main)
        self.assertIn("pluginCandidates", self.main)
        self.assertIn("renderSelectedPluginProfile", self.main)
        self.assertIn("workflowPluginProfileForSelection(action.pluginProfile, selectionControl.value)", self.main)
        self.assertIn('platformControl.dispatchEvent(new Event("change"))', self.main)

    def test_plugin_profile_never_expands_frontend_execution_authority(self):
        action_start = self.main.index("function createWorkflowActionCard")
        action_end = self.main.index("function renderWorkflowAutomationSummary", action_start)
        action_block = self.main[action_start:action_end]
        self.assertNotIn("fetch(", action_block)
        self.assertNotIn("WebSocket", action_block)
        self.assertNotIn("localStorage.setItem", action_block)
        self.assertNotIn('type = "password"', action_block)
        self.assertIn("action.pluginProfile", action_block)

    def test_plugin_flow_labels_do_not_reference_an_out_of_scope_agent_name(self):
        self.assertNotIn(
            'displayAgentName(action.ownerAgentId || "manager", agentName)',
            self.main,
        )
        self.assertNotIn(
            'displayAgentName(primaryAction.ownerAgentId || "manager", agentName)',
            self.main,
        )
        self.assertIn(
            'displayAgentName(action.ownerAgentId || "manager", "Agent ผู้รับงาน")',
            self.main,
        )


if __name__ == "__main__":
    unittest.main()
