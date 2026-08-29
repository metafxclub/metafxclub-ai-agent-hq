from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "frontend" / "src" / "app" / "main.js"
STYLES_PATH = ROOT / "frontend" / "src" / "app" / "styles.css"
INDEX_PATH = ROOT / "frontend" / "index.html"


class EaOptimizationLabFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.styles = STYLES_PATH.read_text(encoding="utf-8")
        cls.index = INDEX_PATH.read_text(encoding="utf-8")

    def function_source(self, name: str) -> str:
        match = re.search(rf"(?:async\s+)?function\s+{re.escape(name)}\s*\(", self.main)
        self.assertIsNotNone(match, f"missing frontend function {name}")
        remainder = self.main[match.start() + 1 :]
        next_match = re.search(r"\n(?:async\s+)?function\s+[A-Za-z0-9_$]+\s*\(", remainder)
        if not next_match:
            return self.main[match.start() :]
        return self.main[match.start() : match.start() + 1 + next_match.start()]

    def const_block(self, name: str, next_name: str) -> str:
        start = self.main.index(f"const {name}")
        end = self.main.index(f"const {next_name}", start)
        return self.main[start:end]

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
            if candidate and Path(candidate).is_file():
                return candidate
        self.skipTest("Node.js is required for frontend behavior regressions")

    def run_node(self, script: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ea-optimization-lab-regression.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run(
                [self.node_binary(), str(path)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        return json.loads(result.stdout)

    def test_main_javascript_is_syntactically_valid(self) -> None:
        subprocess.run(
            [self.node_binary(), "--check", str(MAIN_PATH)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_lab_keeps_backend_tab_ids_but_presents_four_user_stages(self) -> None:
        stage_ids = self.const_block(
            "EA_OPTIMIZATION_LAB_STAGE_IDS",
            "EA_OPTIMIZATION_LAB_STAGE_COPY",
        )
        self.assertEqual(
            re.findall(r'^\s+"([a-z_]+)",?$', stage_ids, flags=re.MULTILINE),
            ["backtest", "optimization", "ea_discovery", "history"],
        )
        stage_copy = self.const_block(
            "EA_OPTIMIZATION_LAB_STAGE_COPY",
            "EA_OPTIMIZATION_LAB_MAX_FILE_BYTES",
        )
        for label in (
            "1 เลือก EA",
            "2 Inputs / Ranges",
            "3 แผนหลายรอบ",
            "4 วิเคราะห์ผล / Report",
        ):
            self.assertIn(f'labelTh: "{label}"', stage_copy)
        self.assertIn('const EA_OPTIMIZATION_LAB_PROP_ID = "right_tool_console";', self.main)
        self.assertIn(
            'EA_OPTIMIZATION_LAB_STAGE_IDS.map((id) => ({',
            self.main,
        )

    def test_source_and_set_parsers_preserve_mode_inputs_as_categories(self) -> None:
        helper_names = (
            "eaOptimizationLabFileExtension",
            "eaOptimizationLabPlatformForExtension",
            "eaOptimizationLabRoundNumber",
            "eaOptimizationLabDefaultNumericRange",
            "eaOptimizationLabParseLiteral",
            "eaOptimizationLabNullableNumber",
            "eaOptimizationLabStripComments",
            "eaOptimizationLabEnumMap",
            "eaOptimizationLabInputModel",
            "eaOptimizationLabParseSetFile",
            "eaOptimizationLabParseSourceInputs",
            "eaOptimizationLabRangeCount",
        )
        script = "const EA_OPTIMIZATION_LAB_MAX_COMBINATIONS = 1_000_000;\n"
        script += "\n".join(self.function_source(name) for name in helper_names)
        script += r'''
const source = `
enum EntryMethod { Trend = 0, CounterTrend = 2 };
input EntryMethod EntryMode = Trend;
input int TradeMode = 1;
input double Risk = 1.5;
input bool UseFilter = true;
input int Period = 20;
sinput double FixedThreshold = 2.0;
input int Lookback = 14;
`;
const setRanges = eaOptimizationLabParseSetFile(
  "Risk=1.5||0.5||0.5||3.0||Y\nPeriod=20||10||5||40||Y\nUseFilter=true||0||1||1||Y\nFixedThreshold=2||1||0.5||3||Y"
);
const inputs = eaOptimizationLabParseSourceInputs(source, setRanges);
const byName = Object.fromEntries(inputs.map((item) => [item.name, item]));
process.stdout.write(JSON.stringify({
  extensions: [
    eaOptimizationLabFileExtension("Robot.MQ4"),
    eaOptimizationLabFileExtension("Robot.ex5"),
  ],
  platforms: [
    eaOptimizationLabPlatformForExtension(".mq4"),
    eaOptimizationLabPlatformForExtension(".ex5"),
  ],
  entryMode: byName.EntryMode,
  tradeMode: byName.TradeMode,
  risk: byName.Risk,
  useFilter: byName.UseFilter,
  periodCount: eaOptimizationLabRangeCount(byName.Period),
  fixedThreshold: byName.FixedThreshold,
  lookback: byName.Lookback,
}));
'''
        payload = self.run_node(script)
        self.assertEqual(payload["extensions"], [".mq4", ".ex5"])
        self.assertEqual(payload["platforms"], ["MT4", "MT5"])
        self.assertEqual(payload["entryMode"]["kind"], "categorical")
        self.assertEqual(payload["entryMode"]["categoryValues"], ["0", "2"])
        self.assertFalse(payload["entryMode"]["optimize"])
        self.assertEqual(payload["tradeMode"]["kind"], "categorical")
        self.assertIsNone(payload["tradeMode"]["start"])
        self.assertIsNone(payload["tradeMode"]["step"])
        self.assertIsNone(payload["tradeMode"]["stop"])
        self.assertEqual(payload["useFilter"]["kind"], "categorical")
        self.assertEqual(payload["useFilter"]["categoryValues"], ["false", "true"])
        self.assertTrue(payload["useFilter"]["optimize"])
        self.assertIsNone(payload["useFilter"]["start"])
        self.assertIsNone(payload["useFilter"]["step"])
        self.assertIsNone(payload["useFilter"]["stop"])
        self.assertEqual(payload["risk"]["start"], 0.5)
        self.assertEqual(payload["risk"]["step"], 0.5)
        self.assertEqual(payload["risk"]["stop"], 3)
        self.assertEqual(payload["periodCount"], 7)
        self.assertEqual(payload["fixedThreshold"]["source"], "source • static input")
        self.assertFalse(payload["fixedThreshold"]["optimize"])
        self.assertEqual(payload["lookback"]["kind"], "numeric")
        self.assertFalse(payload["lookback"]["optimize"])
        self.assertIsNone(payload["lookback"]["start"])
        self.assertIsNone(payload["lookback"]["step"])
        self.assertIsNone(payload["lookback"]["stop"])

    def test_blank_candidate_metrics_stay_null_instead_of_becoming_zero(self) -> None:
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            self.function_source("eaOptimizationLabNullableNumber"),
            self.function_source("normalizeEaOptimizationCandidate"),
            "const empty = normalizeEaOptimizationCandidate({netProfit:'',drawdown:null,trades:'   ',profitFactor:undefined,stability:''});",
            "const partial = normalizeEaOptimizationCandidate({netProfit:'',drawdown:'',trades:'0',profitFactor:null,stability:undefined});",
            "process.stdout.write(JSON.stringify({",
            "allBlank:eaOptimizationLabNullableNumber(null,undefined,'','   '),",
            "emptyCandidate:empty,",
            "partialCandidate:partial,",
            "}));",
        ])
        payload = self.run_node(script)
        self.assertIsNone(payload["allBlank"])
        self.assertIsNone(payload["emptyCandidate"])
        self.assertEqual(payload["partialCandidate"]["trades"], 0)
        self.assertIsNone(payload["partialCandidate"]["profit"])
        self.assertIsNone(payload["partialCandidate"]["drawdown"])

    def test_blank_numeric_ranges_are_invalid_and_never_coerced_to_zero(self) -> None:
        helper_names = (
            "eaOptimizationLabPlatformForExtension",
            "eaOptimizationLabNullableNumber",
            "eaOptimizationLabRangeCount",
            "eaOptimizationLabPlanValidation",
            "eaOptimizationLabBuildPlan",
        )
        script = "const EA_OPTIMIZATION_LAB_MAX_COMBINATIONS = 1_000_000;\n"
        script += "\n".join(self.function_source(name) for name in helper_names)
        script += r'''
const session = {
  platform: "MT5",
  eaFile: {name: "BlankRangeEA.mq5", extension: ".mq5"},
  sourceReportId: "",
  selectedTerminalId: "terminal-mt5",
  programKind: "expert_advisor",
  inputs: [{
    name: "Risk",
    kind: "numeric",
    integer: false,
    optimize: true,
    start: "",
    step: 1,
    stop: "",
  }],
  symbol: "XAUUSD",
  timeframe: "M15",
  dateFrom: "2024-01-01",
  dateTo: "2025-01-01",
  validationMethod: "walk_forward",
  targetProfitPercent: "",
  maxDrawdownPercent: "20",
  minimumTrades: "100",
  roundCount: "3",
};
const validation = eaOptimizationLabPlanValidation(session);
const plan = eaOptimizationLabBuildPlan(session);
process.stdout.write(JSON.stringify({
  rangeCount: eaOptimizationLabRangeCount(session.inputs[0]),
  issues: validation.issues,
  planOk: plan.ok,
}));
'''
        payload = self.run_node(script)
        self.assertEqual(payload["rangeCount"], 0)
        self.assertTrue(any("Risk" in issue for issue in payload["issues"]))
        self.assertFalse(payload["planOk"])

    def test_optimization_report_requires_backend_verified_execution_evidence(self) -> None:
        helper_names = (
            "eaOptimizationLabFirstArray",
            "eaOptimizationLabNullableNumber",
            "normalizeEaOptimizationCandidate",
            "normalizeEaOptimizationReport",
            "normalizeEaOptimizationLabDomain",
        )
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            "function getMetatraderSelectionModel() { return {candidates:[],selectedCandidate:null,adapterReady:false,adapterConnection:'coming_soon',detailTh:''}; }",
            "function normalizeConnectionStatus(value) { return String(value || '').toLowerCase(); }",
            *(self.function_source(name) for name in helper_names),
            r'''
const base = {
  type: "optimization_report",
  title: "Tester output",
  updatedAt: "2026-08-24T10:00:00Z",
  results: {
    available: true,
    passes: [{id:"pass-1",netProfit:42,drawdownPercent:8,trades:100}],
    currentBands: [{name:"Risk",start:0.5,step:0.5,stop:2}],
  },
};
const unverified = {
  ...base,
  id: "unverified",
  executionEvidence: {
    sourceKind: "analysis_only",
    mtExecutionVerified: false,
    optimizationProofVerified: false,
  },
};
const verified = {
  ...base,
  id: "verified",
  executionEvidence: {
    sourceKind: "mt5_visible_run",
    backendVerificationId: "verification-1",
    mtExecutionVerified: true,
    compileProofVerified: true,
    visualBacktestProofVerified: true,
    optimizationProofVerified: true,
  },
};
const unverifiedReport = normalizeEaOptimizationReport(unverified);
const verifiedReport = normalizeEaOptimizationReport(verified);
const unverifiedDomain = normalizeEaOptimizationLabDomain({}, {reports:[unverified]});
const verifiedDomain = normalizeEaOptimizationLabDomain({}, {reports:[verified]});
process.stdout.write(JSON.stringify({
  unverifiedActual: unverifiedReport.actualResultsAvailable,
  verifiedActual: verifiedReport.actualResultsAvailable,
  unverifiedLatest: unverifiedDomain.latestReport?.id || null,
  verifiedLatest: verifiedDomain.latestReport?.id || null,
}));
''',
        ])
        payload = self.run_node(script)
        self.assertFalse(payload["unverifiedActual"])
        self.assertTrue(payload["verifiedActual"])
        self.assertIsNone(payload["unverifiedLatest"])
        self.assertEqual(payload["verifiedLatest"], "verified")

    def test_empty_top_level_arrays_do_not_shadow_nonempty_nested_results(self) -> None:
        helper_names = (
            "eaOptimizationLabFirstArray",
            "eaOptimizationLabNullableNumber",
            "normalizeEaOptimizationCandidate",
            "normalizeEaOptimizationReport",
        )
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            *(self.function_source(name) for name in helper_names),
            r'''
const report = normalizeEaOptimizationReport({
  id: "nested-results",
  type: "optimization_report",
  passes: [],
  candidates: [],
  currentBands: [],
  nextParameterPlan: [],
  executionEvidence: {
    sourceKind: "mt5_visible_run",
    backendVerificationId: "verification-nested",
    mtExecutionVerified: true,
    optimizationProofVerified: true,
  },
  results: {
    passes: [{id:"nested-pass",netProfit:10,drawdownPercent:2,trades:40}],
    currentBands: [{name:"Risk",start:0.5,step:0.5,stop:2}],
    nextParameterPlan: [{name:"Risk",start:1,step:0.1,stop:1.5,reason:"stable cluster"}],
  },
});
process.stdout.write(JSON.stringify({
  candidateIds: report.candidates.map((item) => item.id),
  currentBandNames: report.currentBands.map((item) => item.name),
  nextPlanNames: report.nextParameterPlan.map((item) => item.name),
}));
''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["candidateIds"], ["nested-pass"])
        self.assertEqual(payload["currentBandNames"], ["Risk"])
        self.assertEqual(payload["nextPlanNames"], ["Risk"])

    def test_profit_percentage_is_not_inferred_from_candidate_summaries(self) -> None:
        helper_names = (
            "eaOptimizationLabFirstArray",
            "eaOptimizationLabNullableNumber",
            "normalizeEaOptimizationCandidate",
            "normalizeEaOptimizationReport",
        )
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            *(self.function_source(name) for name in helper_names),
            r'''
const report = normalizeEaOptimizationReport({
  id: "top-candidates-only",
  type: "optimization_report",
  passCount: 1000,
  candidates: [
    {id:"top-1",netProfit:100,drawdownPercent:10,trades:80},
    {id:"top-2",netProfit:50,drawdownPercent:8,trades:90},
  ],
  executionEvidence: {
    sourceKind: "mt5_visible_run",
    backendVerificationId: "verification-candidates",
    mtExecutionVerified: true,
    optimizationProofVerified: true,
  },
});
process.stdout.write(JSON.stringify({
  profitablePercent: report.profitablePercent,
  passCount: report.passCount,
  candidateCount: report.candidates.length,
}));
''',
        ])
        payload = self.run_node(script)
        self.assertIsNone(payload["profitablePercent"])
        self.assertEqual(payload["passCount"], 1000)
        self.assertEqual(payload["candidateCount"], 2)

        analysis = self.function_source("renderEaOptimizationLabAnalysisStage")
        self.assertNotIn("calculatedProfitablePercent", analysis)
        self.assertNotRegex(analysis, r"candidates\.filter\([^\n]*profit")

    def test_domain_sorts_before_limiting_reports_so_newest_survives(self) -> None:
        helper_names = (
            "eaOptimizationLabFirstArray",
            "eaOptimizationLabNullableNumber",
            "normalizeEaOptimizationCandidate",
            "normalizeEaOptimizationReport",
            "normalizeEaOptimizationLabDomain",
        )
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            "function getMetatraderSelectionModel() { return {candidates:[],selectedCandidate:null,adapterReady:false,adapterConnection:'coming_soon',detailTh:''}; }",
            "function normalizeConnectionStatus(value) { return String(value || '').toLowerCase(); }",
            *(self.function_source(name) for name in helper_names),
            r'''
const proof = {
  sourceKind: "mt5_visible_run",
  backendVerificationId: "verification-history",
  mtExecutionVerified: true,
  optimizationProofVerified: true,
};
const reports = Array.from({length: 101}, (_, index) => ({
  id: `old-${index}`,
  type: "optimization_report",
  updatedAt: new Date(Date.UTC(2025, 0, index + 1)).toISOString(),
  executionEvidence: proof,
  results: {passes:[{id:`pass-${index}`,netProfit:1,drawdownPercent:1,trades:1}]},
}));
reports.push({
  id: "newest-report",
  type: "optimization_report",
  updatedAt: "2026-08-24T12:00:00Z",
  executionEvidence: proof,
  results: {passes:[{id:"newest-pass",netProfit:99,drawdownPercent:2,trades:99}]},
});
const domain = normalizeEaOptimizationLabDomain({}, {reports});
process.stdout.write(JSON.stringify({
  reportCount: domain.reports.length,
  latestPlanId: domain.latestPlanReport?.id || null,
  latestRealId: domain.latestReport?.id || null,
  containsNewest: domain.reports.some((item) => item.id === "newest-report"),
}));
''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["reportCount"], 100)
        self.assertTrue(payload["containsNewest"])
        self.assertEqual(payload["latestPlanId"], "newest-report")
        self.assertEqual(payload["latestRealId"], "newest-report")

    def test_backend_selected_terminal_is_effective_for_gate_and_saved_draft(self) -> None:
        helper_names = (
            "eaOptimizationLabPlatformForExtension",
            "eaOptimizationLabNullableNumber",
            "eaOptimizationLabRangeCount",
            "eaOptimizationLabPlanValidation",
            "eaOptimizationLabBuildPlan",
            "getEaOptimizationLabTerminalGate",
        )
        script = "const EA_OPTIMIZATION_LAB_MAX_COMBINATIONS = 1_000_000;\n"
        script += "\n".join(self.function_source(name) for name in helper_names)
        script += r'''
const session = {
  platform: "MT4",
  eaFile: {name:"BackendSelectedEA.mq4",extension:".mq4"},
  sourceReportId: "",
  selectedTerminalId: "",
  programKind: "expert_advisor",
  inputs: [{name:"Risk",kind:"numeric",integer:false,optimize:true,start:0.5,step:0.5,stop:2,current:1}],
  symbol: "XAUUSD",
  timeframe: "M15",
  dateFrom: "2024-01-01",
  dateTo: "2025-01-01",
  validationMethod: "walk_forward",
  targetProfitPercent: "15",
  maxDrawdownPercent: "20",
  minimumTrades: "100",
  roundCount: "3",
};
const selected = {candidateId:"terminal-backend-mt4",platform:"MT4",detected:true,labelTh:"RoboForex MT4"};
const domain = {terminals:[selected],selectedTerminal:selected,adapterReady:true};
const gate = getEaOptimizationLabTerminalGate(domain, session);
const plan = eaOptimizationLabBuildPlan(session, domain);
process.stdout.write(JSON.stringify({
  effectiveTerminalId: gate.effectiveTerminalId || null,
  gateReady: gate.ready,
  planOk: plan.ok,
  planTerminalId: plan.terminalId || null,
}));
'''
        payload = self.run_node(script)
        self.assertEqual(payload["effectiveTerminalId"], "terminal-backend-mt4")
        self.assertTrue(payload["gateReady"])
        self.assertTrue(payload["planOk"])
        self.assertEqual(payload["planTerminalId"], "terminal-backend-mt4")

    def test_sinput_cannot_be_reenabled_for_optimization(self) -> None:
        helper_names = (
            "eaOptimizationLabPlatformForExtension",
            "eaOptimizationLabNullableNumber",
            "eaOptimizationLabParseLiteral",
            "eaOptimizationLabStripComments",
            "eaOptimizationLabEnumMap",
            "eaOptimizationLabInputModel",
            "eaOptimizationLabParseSetFile",
            "eaOptimizationLabParseSourceInputs",
            "eaOptimizationLabRangeCount",
            "eaOptimizationLabPlanValidation",
        )
        script = "const EA_OPTIMIZATION_LAB_MAX_COMBINATIONS = 1_000_000;\n"
        script += "\n".join(self.function_source(name) for name in helper_names)
        script += r'''
const source = `
sinput double FixedThreshold = 2.0;
input double Risk = 1.0;
void OnTick() {}
`;
const ranges = eaOptimizationLabParseSetFile(
  "FixedThreshold=2||1||0.5||3||Y\nRisk=1||0.5||0.5||2||Y"
);
const inputs = eaOptimizationLabParseSourceInputs(source, ranges);
const fixed = inputs.find((item) => item.name === "FixedThreshold");
const initiallyOptimized = fixed.optimize;
fixed.optimize = true;
fixed.start = 1;
fixed.step = 0.5;
fixed.stop = 3;
const validation = eaOptimizationLabPlanValidation({
  platform: "MT5",
  eaFile: {name:"StaticInputEA.mq5",extension:".mq5"},
  sourceReportId: "",
  programKind: "expert_advisor",
  inputs,
  symbol: "XAUUSD",
  timeframe: "M15",
  dateFrom: "2024-01-01",
  dateTo: "2025-01-01",
  targetProfitPercent: "",
  maxDrawdownPercent: "20",
  minimumTrades: "100",
});
process.stdout.write(JSON.stringify({
  initiallyOptimized,
  optimizedNames: validation.optimized.map((item) => item.name),
  issues: validation.issues,
}));
'''
        payload = self.run_node(script)
        self.assertFalse(payload["initiallyOptimized"])
        self.assertNotIn("FixedThreshold", payload["optimizedNames"])
        self.assertIn("Risk", payload["optimizedNames"])
        self.assertTrue(any("FixedThreshold" in issue for issue in payload["issues"]))

    def test_unknown_program_kind_is_blocked_from_draft_plan(self) -> None:
        helper_names = (
            "eaOptimizationLabPlatformForExtension",
            "eaOptimizationLabNullableNumber",
            "eaOptimizationLabRangeCount",
            "eaOptimizationLabPlanValidation",
            "eaOptimizationLabBuildPlan",
        )
        script = "const EA_OPTIMIZATION_LAB_MAX_COMBINATIONS = 1_000_000;\n"
        script += "\n".join(self.function_source(name) for name in helper_names)
        script += r'''
const session = {
  platform: "MT4",
  eaFile: {name:"UnknownProgram.mq4",extension:".mq4"},
  sourceReportId: "",
  selectedTerminalId: "terminal-mt4",
  programKind: "unknown",
  inputs: [{name:"Risk",kind:"numeric",integer:false,optimize:true,start:0.5,step:0.5,stop:2,current:1}],
  symbol: "XAUUSD",
  timeframe: "M15",
  dateFrom: "2024-01-01",
  dateTo: "2025-01-01",
  validationMethod: "walk_forward",
  targetProfitPercent: "",
  maxDrawdownPercent: "20",
  minimumTrades: "100",
  roundCount: "3",
};
const validation = eaOptimizationLabPlanValidation(session);
const plan = eaOptimizationLabBuildPlan(session);
process.stdout.write(JSON.stringify({issues:validation.issues,planOk:plan.ok}));
'''
        payload = self.run_node(script)
        self.assertFalse(payload["planOk"])
        self.assertTrue(any("Expert Advisor" in issue for issue in payload["issues"]))

    def test_categorical_next_parameter_plan_preserves_values(self) -> None:
        helper_names = (
            "eaOptimizationLabFirstArray",
            "eaOptimizationLabNullableNumber",
            "normalizeEaOptimizationCandidate",
            "normalizeEaOptimizationReport",
        )
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            *(self.function_source(name) for name in helper_names),
            r'''
const report = normalizeEaOptimizationReport({
  id: "categorical-next-plan",
  type: "optimization_report",
  executionEvidence: {
    sourceKind: "mt5_visible_run",
    backendVerificationId: "verification-categorical",
    mtExecutionVerified: true,
    optimizationProofVerified: true,
  },
  results: {
    passes: [{id:"pass-1",netProfit:1,drawdownPercent:1,trades:1}],
    nextParameterPlan: [{
      name: "EntryMode",
      values: [0, 2],
      reason: "keep both stable categories",
    }],
  },
});
const band = report.nextParameterPlan[0] || {};
process.stdout.write(JSON.stringify({
  kind: band.kind || null,
  values: band.values || null,
  start: band.start ?? null,
  step: band.step ?? null,
  stop: band.stop ?? null,
  reason: band.reason || null,
}));
''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["kind"], "categorical")
        self.assertEqual(payload["values"], ["0", "2"])
        self.assertIsNone(payload["start"])
        self.assertIsNone(payload["step"])
        self.assertIsNone(payload["stop"])
        self.assertEqual(payload["reason"], "keep both stable categories")

    def test_number_plan_fields_persist_input_before_blur_or_save(self) -> None:
        source = self.function_source("appendEaOptimizationLabPlanField")
        script = "\n".join([
            r'''
class FakeElement {
  constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.value = ""; }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.children.push(child); return child; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  dispatch(name) { if (this.listeners[name]) this.listeners[name](); }
}
const document = {createElement: (tag) => new FakeElement(tag)};
let rerenders = 0;
function rerenderEaOptimizationLab() { rerenders += 1; }
''',
            source,
            r'''
const session = {targetProfitPercent: ""};
const grid = new FakeElement("div");
appendEaOptimizationLabPlanField(
  grid,
  "เป้าหมายกำไร (%)",
  "number",
  session.targetProfitPercent,
  (value) => { session.targetProfitPercent = value; },
);
const control = grid.children[0].children[1];
control.value = "15";
control.dispatch("input");
const afterInput = session.targetProfitPercent;
const rerendersAfterInput = rerenders;
control.dispatch("change");
process.stdout.write(JSON.stringify({
  afterInput,
  afterChange: session.targetProfitPercent,
  rerendersAfterInput,
  rerendersAfterChange: rerenders,
}));
''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["afterInput"], "15")
        self.assertEqual(payload["afterChange"], "15")
        self.assertEqual(payload["rerendersAfterInput"], 0)
        self.assertEqual(payload["rerendersAfterChange"], 1)

    def test_draft_persistence_excludes_raw_source_and_requires_file_reattach(self) -> None:
        helper_names = (
            "eaOptimizationLabNullableNumber",
            "serializeEaOptimizationLabSession",
            "restoreEaOptimizationLabSession",
        )
        script = "\n".join(self.function_source(name) for name in helper_names)
        script += r'''
const raw = {
  platform: "MT4",
  sourceReportId: "report-safe-1",
  selectedTerminalId: "terminal-safe-1",
  eaFile: {name:"SafeDraftEA.mq4",size:1200,extension:".mq4",sha256:"a".repeat(64)},
  setFile: {name:"SafeDraftEA.set",size:300,extension:".set",sha256:"b".repeat(64)},
  sourceText: "SECRET_SOURCE_MARKER input string Token = 'do-not-persist';",
  setText: "SECRET_SET_MARKER=do-not-persist",
  programKind: "expert_advisor",
  inputs: [{
    id:"Risk",name:"Risk",type:"double",current:1,defaultRaw:"1",kind:"numeric",
    integer:false,canOptimize:true,options:[],categoryValues:[],optimize:true,
    start:0.5,step:0.5,stop:2,source:"source + set",
  }],
  symbol: "XAUUSD",
  timeframe: "M15",
  dateFrom: "2024-01-01",
  dateTo: "2025-01-01",
  validationMethod: "walk_forward",
  targetProfitPercent: "15",
  maxDrawdownPercent: "20",
  minimumTrades: "100",
  roundCount: "3",
  plan: {ok:true},
};
const serialized = serializeEaOptimizationLabSession(raw);
const serializedText = JSON.stringify(serialized);
const restored = restoreEaOptimizationLabSession(serialized, {
  sourceText:"fallback-source",
  setText:"fallback-set",
  plan:{ok:true},
  fileBusy:true,
  terminalBusy:true,
});
process.stdout.write(JSON.stringify({
  hasSourceTextKey: Object.prototype.hasOwnProperty.call(serialized, "sourceText"),
  hasSetTextKey: Object.prototype.hasOwnProperty.call(serialized, "setText"),
  leakedSource: serializedText.includes("SECRET_SOURCE_MARKER"),
  leakedSet: serializedText.includes("SECRET_SET_MARKER"),
  serializedTarget: serialized.targetProfitPercent,
  restoredSourceText: restored.sourceText,
  restoredSetText: restored.setText,
  restoredTarget: restored.targetProfitPercent,
  eaNeedsReattach: restored.eaFile?.needsReattach === true,
  setNeedsReattach: restored.setFile?.needsReattach === true,
  restoredPlan: restored.plan,
  restoredDraft: restored.restoredDraft,
}));
'''
        payload = self.run_node(script)
        self.assertFalse(payload["hasSourceTextKey"])
        self.assertFalse(payload["hasSetTextKey"])
        self.assertFalse(payload["leakedSource"])
        self.assertFalse(payload["leakedSet"])
        self.assertEqual(payload["serializedTarget"], "15")
        self.assertEqual(payload["restoredSourceText"], "")
        self.assertEqual(payload["restoredSetText"], "")
        self.assertEqual(payload["restoredTarget"], "15")
        self.assertTrue(payload["eaNeedsReattach"])
        self.assertTrue(payload["setNeedsReattach"])
        self.assertIsNone(payload["restoredPlan"])
        self.assertTrue(payload["restoredDraft"])

    def test_file_import_rejects_duplicates_and_new_ea_clears_stale_set(self) -> None:
        helper_names = (
            "eaOptimizationLabFileExtension",
            "eaOptimizationLabPlatformForExtension",
            "processEaOptimizationLabFiles",
        )
        script = "\n".join([
            'const EA_OPTIMIZATION_LAB_SOURCE_EXTENSIONS = [".mq4",".mq5",".ex4",".ex5",".set"];',
            "const EA_OPTIMIZATION_LAB_MAX_FILE_BYTES = 2 * 1024 * 1024;",
            "const state = {modal:{eaOptimizationLab:{fileBusy:false,fileRequestId:0,message:'',tone:'',eaFile:null,setFile:null,sourceText:'',setText:'',programKind:'unknown',inputs:[],platform:'',plan:null,restoredDraft:false}}};",
            "let rerenders = 0; let saves = 0;",
            "function rerenderEaOptimizationLab() { rerenders += 1; }",
            "function saveSessionSnapshot() { saves += 1; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            "async function eaOptimizationLabReadTextFile() { return 'input double Risk = 1.0;\\nvoid OnTick() {}'; }",
            "async function eaOptimizationLabFileSha256() { return 'a'.repeat(64); }",
            "function eaOptimizationLabParseSetFile() { return new Map(); }",
            "function eaOptimizationLabParseSourceInputs() { return [{name:'Risk',kind:'numeric',optimize:false}]; }",
            "function eaOptimizationLabDetectProgramKind() { return 'expert_advisor'; }",
            *(self.function_source(name) for name in helper_names),
            r'''
const file = (name) => ({name,size:100,arrayBuffer:async () => new Uint8Array([1,2,3]).buffer});
(async () => {
  await processEaOptimizationLabFiles([file("One.mq4"), file("Two.mq4")]);
  const duplicateEaMessage = state.modal.eaOptimizationLab.message;
  await processEaOptimizationLabFiles([file("One.set"), file("Two.set")]);
  const duplicateSetMessage = state.modal.eaOptimizationLab.message;

  Object.assign(state.modal.eaOptimizationLab, {
    eaFile:{name:"SameName.mq4",size:90,extension:".mq4",sha256:"b".repeat(64)},
    setFile:{name:"Stale.set",size:30,extension:".set",sha256:"c".repeat(64)},
    sourceText:"old source",
    setText:"StaleRisk=99",
    inputs:[{name:"StaleRisk"}],
    programKind:"expert_advisor",
  });
  await processEaOptimizationLabFiles([file("SameName.mq4")]);
  const session = state.modal.eaOptimizationLab;
  process.stdout.write(JSON.stringify({
    duplicateEaMessage,
    duplicateSetMessage,
    eaName:session.eaFile?.name || null,
    staleSetFile:session.setFile,
    staleSetText:session.setText,
    inputNames:session.inputs.map((item) => item.name),
    fileBusy:session.fileBusy,
    saves,
  }));
})().catch((error) => { console.error(error); process.exit(1); });
''',
        ])
        payload = self.run_node(script)
        self.assertIn("EA เพียง 1 ไฟล์", payload["duplicateEaMessage"])
        self.assertIn(".set เพียง 1 ไฟล์", payload["duplicateSetMessage"])
        self.assertEqual(payload["eaName"], "SameName.mq4")
        self.assertIsNone(payload["staleSetFile"])
        self.assertEqual(payload["staleSetText"], "")
        self.assertEqual(payload["inputNames"], ["Risk"])
        self.assertFalse(payload["fileBusy"])
        self.assertGreaterEqual(payload["saves"], 1)

    def test_terminal_selection_posts_to_backend_and_commits_only_after_verification(self) -> None:
        source = self.function_source("selectEaOptimizationLabTerminal")
        script = "\n".join([
            'const EA_OPTIMIZATION_LAB_PROP_ID = "right_tool_console";',
            "const candidate = {candidateId:'terminal-robo-mt4',platform:'MT4',detected:true,labelTh:'RoboForex MT4'};",
            "const state = {modal:{eaOptimizationLab:{platform:'MT4',terminalBusy:false,selectedTerminalId:'',plan:{ok:true},message:'',tone:''}},propReports:{right_tool_console:{}}};",
            "let posted = null; let saved = 0; let rerenders = 0; let verificationMatches = true;",
            "function getModalSubject() { return {id:EA_OPTIMIZATION_LAB_PROP_ID}; }",
            "function getPropertyRole() { return {}; }",
            "function normalizeWorkflowDashboard() { return {domainData:{eaOptimizationLab:{terminals:[candidate]}}}; }",
            "async function postJson(url, body) { posted = {url,body}; return {ok:true}; }",
            "async function loadPropReport() { return {connectionChecklist:{}}; }",
            "function getMetatraderSelectionModel() { return {selectedCandidate:verificationMatches ? candidate : {candidateId:'different-terminal'}}; }",
            "function saveSessionSnapshot() { saved += 1; }",
            "function rerenderEaOptimizationLab() { rerenders += 1; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            source,
            r'''
(async () => {
  const confirmed = await selectEaOptimizationLabTerminal(candidate.candidateId);
  const success = {
    returned: Boolean(confirmed),
    selectedTerminalId: state.modal.eaOptimizationLab.selectedTerminalId,
    tone: state.modal.eaOptimizationLab.tone,
    posted,
    saved,
  };
  verificationMatches = false;
  state.modal.eaOptimizationLab.selectedTerminalId = "";
  state.modal.eaOptimizationLab.plan = {ok:true};
  const rejected = await selectEaOptimizationLabTerminal(candidate.candidateId);
  const failure = {
    returned: rejected,
    selectedTerminalId: state.modal.eaOptimizationLab.selectedTerminalId,
    plan: state.modal.eaOptimizationLab.plan,
    tone: state.modal.eaOptimizationLab.tone,
  };
  process.stdout.write(JSON.stringify({success,failure,rerenders}));
})().catch((error) => { console.error(error); process.exit(1); });
''',
        ])
        payload = self.run_node(script)
        self.assertTrue(payload["success"]["returned"])
        self.assertEqual(payload["success"]["posted"]["url"], "/api/integrations/metatrader/select")
        self.assertEqual(
            payload["success"]["posted"]["body"],
            {"propId": "right_tool_console", "candidateId": "terminal-robo-mt4"},
        )
        self.assertEqual(payload["success"]["selectedTerminalId"], "terminal-robo-mt4")
        self.assertEqual(payload["success"]["tone"], "success")
        self.assertGreaterEqual(payload["success"]["saved"], 1)
        self.assertIsNone(payload["failure"]["returned"])
        self.assertEqual(payload["failure"]["selectedTerminalId"], "")
        self.assertIsNone(payload["failure"]["plan"])
        self.assertEqual(payload["failure"]["tone"], "error")

    def test_dropzone_is_a_real_button_and_notices_are_live_regions(self) -> None:
        notice_source = self.function_source("createEaOptimizationLabNotice")
        source_stage = self.function_source("renderEaOptimizationLabSourceStage")
        script = "\n".join([
            r'''
class FakeElement {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.dataset = {}; this.textContent = ""; }
  append(...children) { this.children.push(...children); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
}
const document = {createElement:(tag) => new FakeElement(tag)};
''',
            notice_source,
            r'''
const errorNotice = createEaOptimizationLabNotice("error", "ผิดพลาด", "ตรวจข้อมูล");
const readyNotice = createEaOptimizationLabNotice("success", "พร้อม", "บันทึกแล้ว");
process.stdout.write(JSON.stringify({
  errorTag:errorNotice.tag,
  errorRole:errorNotice.attributes.role,
  errorLive:errorNotice.attributes["aria-live"],
  errorAtomic:errorNotice.attributes["aria-atomic"],
  readyRole:readyNotice.attributes.role,
  readyLive:readyNotice.attributes["aria-live"],
}));
''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["errorTag"], "aside")
        self.assertEqual(payload["errorRole"], "alert")
        self.assertEqual(payload["errorLive"], "assertive")
        self.assertEqual(payload["errorAtomic"], "true")
        self.assertEqual(payload["readyRole"], "status")
        self.assertEqual(payload["readyLive"], "polite")
        self.assertIn('const dropzone = document.createElement("button")', source_stage)
        self.assertIn('dropzone.type = "button"', source_stage)
        self.assertIn('dropzone.addEventListener("click", () => fileInput.click())', source_stage)
        self.assertIn('fileInput.setAttribute("aria-hidden", "true")', source_stage)
        self.assertIn("fileInput.tabIndex = -1", source_stage)

    def test_v2_all_pass_rows_and_aliases_normalize_without_losing_truth(self) -> None:
        helper_names = (
            "eaOptimizationLabFirstArray",
            "eaOptimizationLabNullableNumber",
            "normalizeEaOptimizationCandidate",
            "normalizeEaOptimizationReport",
            "normalizeEaOptimizationLabDomain",
        )
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            "function getMetatraderSelectionModel() { return {candidates:[],selectedCandidate:null,adapterReady:false,adapterConnection:'coming_soon',detailTh:''}; }",
            "function normalizeConnectionStatus(value) { return String(value || '').toLowerCase(); }",
            *(self.function_source(name) for name in helper_names),
            r'''
const report = {
  id:"experiment-v2",
  schemaVersion:"ea-experiment-report-v2",
  reportType:"ea_experiment_report",
  updatedAt:"2026-08-24T12:00:00Z",
  executionEvidence:{
    sourceKind:"mt5_visible_run",
    backendVerificationId:"verification-v2",
    mtExecutionVerified:true,
    optimizationProofVerified:true,
  },
  results:{
    passCount:2,
    profitablePassCount:1,
    allPassRows:[
      {pass:"701",profit:12.5,maxDrawdownPercent:4.5,tradeCount:80,inputs:{Risk:1.0}},
      {pass:"702",profit:-2,maxDrawdownPercent:3,tradeCount:75,inputs:{Risk:1.5}},
    ],
    allPassRowsTruncated:false,
    parameterBands:[{parameter:"Risk",start:1,step:0.5,stop:1.5}],
    nextRanges:[{parameter:"EntryMode",values:["trend","counter"],clusterReason:"two stable islands"}],
  },
};
const normalized = normalizeEaOptimizationReport(report);
const domain = normalizeEaOptimizationLabDomain({}, {reports:[report]});
process.stdout.write(JSON.stringify({
  ids:normalized.candidates.map((item) => item.id),
  profits:normalized.candidates.map((item) => item.profit),
  firstParameters:normalized.candidates[0]?.parameters || null,
  passCount:normalized.passCount,
  profitablePercent:normalized.profitablePercent,
  passesTruncated:normalized.passesTruncated,
  currentBand:normalized.currentBands[0] || null,
  nextBand:normalized.nextParameterPlan[0] || null,
  latestId:domain.latestReport?.id || null,
}));
''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["ids"], ["701", "702"])
        self.assertEqual(payload["profits"], [12.5, -2])
        self.assertEqual(payload["firstParameters"], {"Risk": 1})
        self.assertEqual(payload["passCount"], 2)
        self.assertEqual(payload["profitablePercent"], 50)
        self.assertFalse(payload["passesTruncated"])
        self.assertEqual(payload["currentBand"]["name"], "Risk")
        self.assertEqual(payload["nextBand"]["kind"], "categorical")
        self.assertEqual(payload["nextBand"]["values"], ["trend", "counter"])
        self.assertEqual(payload["latestId"], "experiment-v2")

    def test_plan_only_report_is_not_promoted_to_latest_real_result(self) -> None:
        helper_names = (
            "eaOptimizationLabFirstArray",
            "eaOptimizationLabNullableNumber",
            "normalizeEaOptimizationCandidate",
            "normalizeEaOptimizationReport",
            "normalizeEaOptimizationLabDomain",
        )
        script = "\n".join([
            "function workflowDomainObject(...values) { return values.find((value) => value && typeof value === 'object' && !Array.isArray(value)) || {}; }",
            "function safeDashboardDisplayText(value, fallback = '') { const text = String(value ?? '').trim(); return text || fallback; }",
            "function getMetatraderSelectionModel() { return {candidates:[],selectedCandidate:null,adapterReady:false,adapterConnection:'coming_soon',detailTh:''}; }",
            "function normalizeConnectionStatus(value) { return String(value || '').toLowerCase(); }",
            *(self.function_source(name) for name in helper_names),
            r'''
const planOnly = {
  id: "ea-experiment-report-v1",
  type: "ea_experiment_report",
  title: "Draft plan only",
  updatedAt: "2026-08-24T10:00:00Z",
  plan: {eaName: "Plan Identity EA", platform: "MT5"},
  execution: {status: "not_started"},
  results: {},
  metrics: {},
};
const real = {
  id: "optimization-real-v1",
  type: "optimization_report",
  title: "Real tester result",
  updatedAt: "2026-08-24T09:00:00Z",
  eaName: "Real Identity EA",
  platform: "MT4",
  executionEvidence: {
    sourceKind: "mt4_visible_run",
    backendVerificationId: "verification-real-v1",
    mtExecutionVerified: true,
    optimizationProofVerified: true,
  },
  results: {available: true, passes: [{id:"pass-1",netProfit:12.5,drawdownPercent:4,trades:25}]},
};
const planDomain = normalizeEaOptimizationLabDomain({}, {reports:[planOnly]});
const mixedDomain = normalizeEaOptimizationLabDomain({}, {reports:[real, planOnly]});
process.stdout.write(JSON.stringify({
  planLatestId: planDomain.latestPlanReport?.id || null,
  planRealLatest: planDomain.latestReport,
  mixedPlanId: mixedDomain.latestPlanReport?.id || null,
  mixedRealId: mixedDomain.latestReport?.id || null,
  mixedPlanEa: mixedDomain.latestPlanReport?.eaName || null,
  mixedRealEa: mixedDomain.latestReport?.eaName || null,
  mixedPlanActual: mixedDomain.latestPlanReport?.actualResultsAvailable,
  mixedRealActual: mixedDomain.latestReport?.actualResultsAvailable,
}));
''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["planLatestId"], "ea-experiment-report-v1")
        self.assertIsNone(payload["planRealLatest"])
        self.assertEqual(payload["mixedPlanId"], "ea-experiment-report-v1")
        self.assertEqual(payload["mixedRealId"], "optimization-real-v1")
        self.assertEqual(payload["mixedPlanEa"], "Plan Identity EA")
        self.assertEqual(payload["mixedRealEa"], "Real Identity EA")
        self.assertFalse(payload["mixedPlanActual"])
        self.assertTrue(payload["mixedRealActual"])

    def test_utf16_reader_handles_bom_and_uses_array_buffer_decoder(self) -> None:
        reader = self.function_source("eaOptimizationLabReadTextFile")
        for token in (
            "file.arrayBuffer()",
            'encoding = "utf-16le"',
            'encoding = "utf-16be"',
            "new TextDecoder(encoding, { fatal: false })",
        ):
            self.assertIn(token, reader)
        script = reader + r'''
(async () => {
  const littleEndian = Uint8Array.from([0xFF,0xFE,0x45,0x00,0x41,0x00,0x20,0x00,0x35,0x00]);
  const text = await eaOptimizationLabReadTextFile({arrayBuffer:async () => littleEndian.buffer});
  process.stdout.write(JSON.stringify({text}));
})().catch((error) => { console.error(error); process.exit(1); });
'''
        payload = self.run_node(script)
        self.assertEqual(payload["text"], "EA 5")

    def test_plan_fields_rerender_after_every_change(self) -> None:
        field_source = self.function_source("appendEaOptimizationLabPlanField")
        self.assertRegex(
            field_source,
            r'control\.addEventListener\("change",\s*\(\)\s*=>\s*\{\s*onChange\(control\.value\);\s*rerenderEaOptimizationLab\(\);',
        )

    def test_right_tool_console_has_no_generic_rail_actions(self) -> None:
        rail_source = self.function_source("workflowRailActions")
        self.assertIn(
            "if ([EA_FACTORY_PROP_ID, EA_OPTIMIZATION_LAB_PROP_ID].includes(subject?.id)) return [];",
            rail_source,
        )

    def test_plan_validation_caps_combinations_at_one_million(self) -> None:
        helper_names = (
            "eaOptimizationLabPlatformForExtension",
            "eaOptimizationLabNullableNumber",
            "eaOptimizationLabRangeCount",
            "eaOptimizationLabPlanValidation",
        )
        script = "const EA_OPTIMIZATION_LAB_MAX_COMBINATIONS = 1_000_000;\n"
        script += "\n".join(self.function_source(name) for name in helper_names)
        script += r'''
const numericInput = (name) => ({
  name,
  kind: "numeric",
  optimize: true,
  start: 0,
  step: 1,
  stop: 100,
});
const result = eaOptimizationLabPlanValidation({
  platform: "MT5",
  eaFile: { name: "CaseStudy.mq5", extension: ".mq5" },
  sourceReportId: "",
  inputs: [numericInput("A"), numericInput("B"), numericInput("C")],
  symbol: "XAUUSD",
  timeframe: "M15",
  dateFrom: "2024-01-01",
  dateTo: "2025-01-01",
});
const oversized = eaOptimizationLabPlanValidation({
  platform: "MT5",
  eaFile: { name: "CaseStudy.mq5", extension: ".mq5" },
  sourceReportId: "",
  inputs: [{ ...numericInput("Huge"), stop: 1000001 }],
  symbol: "XAUUSD",
  timeframe: "M15",
  dateFrom: "2024-01-01",
  dateTo: "2025-01-01",
});
process.stdout.write(JSON.stringify({
  issues: result.issues,
  combinations: result.combinations.toString(),
  oversizedIssues: oversized.issues,
}));
'''
        payload = self.run_node(script)
        self.assertEqual(payload["combinations"], "1030301")
        self.assertIn(
            "จำนวน Combination เกิน 1,000,000 ค่า กรุณาลดช่วงหรือแยกเป็นหลายรอบ",
            payload["issues"],
        )
        self.assertIn(
            "Huge: มีค่ามากกว่า 1,000,000 ค่า กรุณาลดช่วงหรือเพิ่ม Step",
            payload["oversizedIssues"],
        )

    def test_file_import_copy_is_truthful_about_binary_and_browser_only_state(self) -> None:
        process_source = self.function_source("processEaOptimizationLabFiles")
        for truth_copy in (
            "กำลังอ่านไฟล์ในเบราว์เซอร์ • ยังไม่อัปโหลดไป Backend",
            "ไฟล์ Binary อ่าน Inputs โดยตรงไม่ได้ • กรุณาแนบ .set หรือ Source .mq4/.mq5 เพิ่ม",
            "ข้อมูลยังอยู่เฉพาะในเบราว์เซอร์",
            "ไฟล์ต้องมีขนาดไม่เกิน 2 MB ต่อไฟล์",
        ):
            self.assertIn(truth_copy, process_source)
        self.assertIn(
            'const EA_OPTIMIZATION_LAB_MAX_FILE_BYTES = 2 * 1024 * 1024;',
            self.main,
        )
        self.assertIn(
            'Object.freeze([".mq4", ".mq5", ".ex4", ".ex5", ".set"])',
            self.main,
        )

    def test_real_run_stays_disabled_and_results_are_never_fabricated(self) -> None:
        rounds = self.function_source("renderEaOptimizationLabRoundsStage")
        analysis = self.function_source("renderEaOptimizationLabAnalysisStage")
        self.assertIn('"เริ่ม Optimization จริง"', rounds)
        self.assertRegex(
            rounds,
            r'"เริ่ม Optimization จริง",\s*\(\) => \{\},\s*\{ disabled: true \}',
        )
        self.assertIn("ยังไม่เปิด Strategy Tester จริง", rounds)
        self.assertIn("ห้องนี้จะไม่สร้างผลจำลองหรืออ้างว่ารัน MT4/MT5 แล้ว", rounds)
        self.assertIn("ยังไม่มี Optimization Report จริง", analysis)
        self.assertIn("Dashboard จะไม่สร้างกำไร Drawdown หรือ Candidate จำลอง", analysis)
        self.assertIn("Current Bands • ช่วงที่ทดสอบจริง", analysis)
        self.assertIn("Next Parameter Plan • รอบถัดไป", analysis)
        self.assertIn("Draft Plan ไม่ถูกนับเป็นผลทดสอบ", analysis)
        self.assertNotIn("Math.random", rounds + analysis)

    def test_domain_renderer_routes_right_tool_console_to_the_lab(self) -> None:
        domain_normalizer = self.function_source("normalizeWorkflowDomainData")
        domain_renderer = self.function_source("renderWorkflowDomainPanel")
        dashboard_renderer = self.function_source("renderWorkflowDashboard")
        self.assertIn(
            "if (propId === EA_OPTIMIZATION_LAB_PROP_ID)",
            domain_normalizer,
        )
        self.assertIn(
            "return { eaOptimizationLab: normalizeEaOptimizationLabDomain(backend, report) };",
            domain_normalizer,
        )
        self.assertIn(
            "if (subject.id === EA_OPTIMIZATION_LAB_PROP_ID)",
            domain_renderer,
        )
        self.assertIn("renderEaOptimizationLabPanel(", domain_renderer)
        self.assertIn(
            "const isEaOptimizationLabDashboard = subject.id === EA_OPTIMIZATION_LAB_PROP_ID;",
            dashboard_renderer,
        )
        self.assertIn("isEaOptimizationLabDashboard", dashboard_renderer)

    def test_lab_styles_are_scoped_and_cover_dense_and_responsive_surfaces(self) -> None:
        for selector in (
            ".ea-optimization-lab-panel",
            ".ea-optimization-lab-heading",
            ".ea-optimization-lab-source-layout",
            ".ea-optimization-lab-dropzone",
            ".ea-optimization-lab-input-table",
            ".ea-optimization-lab-rounds",
            ".ea-optimization-lab-run-gate",
            ".ea-optimization-lab-candidates",
            ".ea-optimization-lab-bands-grid",
        ):
            self.assertIn(selector, self.styles)
        self.assertRegex(
            self.styles,
            r"@media\s*\([^)]*max-width:\s*(?:900|920|960)px[^)]*\)[\s\S]*?\.ea-optimization-lab",
        )

    def test_frontend_cache_version_is_bumped_for_the_lab_and_matches_runtime(self) -> None:
        stylesheet_match = re.search(r"styles\.css\?v=([^\"']+)", self.index)
        runtime_match = re.search(r'RUNTIME_BUILD_VERSION\s*=\s*"([^"]+)"', self.index)
        self.assertIsNotNone(stylesheet_match)
        self.assertIsNotNone(runtime_match)
        self.assertEqual(stylesheet_match.group(1), runtime_match.group(1))
        self.assertEqual(runtime_match.group(1), "20260827-google-auth-v074")


if __name__ == "__main__":
    unittest.main()
