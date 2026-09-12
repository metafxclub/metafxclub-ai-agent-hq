import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "frontend" / "src" / "app" / "main.js"
INDEX_PATH = ROOT / "frontend" / "index.html"
STYLES_PATH = ROOT / "frontend" / "src" / "app" / "styles.css"


def function_block(source: str, name: str) -> str:
    markers = (f"function {name}(", f"async function {name}(")
    starts = [source.find(marker) for marker in markers]
    start = min(index for index in starts if index >= 0)
    brace = source.index(") {", start) + 2
    depth = 0
    quote = ""
    escaped = False
    template_expression_depth = 0
    for index in range(brace, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote and template_expression_depth == 0:
                quote = ""
            elif quote == "`" and char == "$" and index + 1 < len(source) and source[index + 1] == "{":
                template_expression_depth += 1
            elif quote == "`" and char == "}" and template_expression_depth:
                template_expression_depth -= 1
            continue
        if char in ('"', "'", "`"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f"unterminated function {name}")


class CodexReserveFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.index = INDEX_PATH.read_text(encoding="utf-8")
        cls.styles = STYLES_PATH.read_text(encoding="utf-8")
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
        cls.node = next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)
        if not cls.node:
            raise RuntimeError("Node.js runtime is required")

    def run_node(self, script: str) -> dict:
        result = subprocess.run(
            [self.node, "-e", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return json.loads(result.stdout)

    def test_compact_global_reserve_control_is_visible_and_accessible(self) -> None:
        for element_id in (
            "codexRateReserveForm",
            "codexRateReserveInput",
            "codexRateReserveSave",
            "codexRateReserveHint",
            "codexRateReserveStatus",
        ):
            self.assertIn(f'id="{element_id}"', self.index)
        self.assertIn('min="0"', self.index)
        self.assertIn('max="100"', self.index)
        self.assertIn("0 = ใช้ได้จนโควตาหมด", self.index)
        self.assertIn("ค่านี้ใช้ร่วมกันทุกระบบ", self.index)
        self.assertIn(".codex-rate-reserve-controls", self.styles)

    def test_policy_presentation_uses_lowest_window_and_allows_equality(self) -> None:
        script = "\n".join([
            "const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));",
            function_block(self.main, "normalizeCodexRateReservePercent"),
            function_block(self.main, "formatCodexRatePercent"),
            function_block(self.main, "codexRatePolicyRemainingPercent"),
            function_block(self.main, "codexRateReservePresentation"),
            "const snapshot={primary:{remainingPercent:20},secondary:{remainingPercent:10},limitReached:false};",
            "const equal=codexRateReservePresentation(snapshot,10);",
            "const below=codexRateReservePresentation(snapshot,11);",
            "const zero=codexRateReservePresentation({primary:{remainingPercent:0},limitReached:false},0);",
            "const official=codexRateReservePresentation({...snapshot,limitReached:true},0);",
            "const malformed=codexRateReservePresentation({primary:{remainingPercent:20},secondary:{remainingPercent:'bad'},limitReached:false},0);",
            "const booleanValue=codexRateReservePresentation({primary:{remainingPercent:true},limitReached:false},0);",
            "const outOfRange=codexRateReservePresentation({primary:{remainingPercent:101},limitReached:false},0);",
            "process.stdout.write(JSON.stringify({equal,below,zero,official,malformed,booleanValue,outOfRange}));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["equal"]["tone"], "ready")
        self.assertEqual(payload["below"]["tone"], "warning")
        self.assertEqual(payload["zero"]["tone"], "ready")
        self.assertEqual(payload["official"]["tone"], "error")
        self.assertEqual(payload["malformed"]["tone"], "neutral")
        self.assertEqual(payload["booleanValue"]["tone"], "neutral")
        self.assertEqual(payload["outOfRange"]["tone"], "neutral")
        self.assertIn("ต่ำสุด 10%", payload["equal"]["text"])

    def test_reserve_normalizer_rejects_coerced_non_numeric_values(self) -> None:
        script = "\n".join([
            function_block(self.main, "normalizeCodexRateReservePercent"),
            "const values={validZero:normalizeCodexRateReservePercent('0'),validHundred:normalizeCodexRateReservePercent(100),booleanValue:normalizeCodexRateReservePercent(true),objectValue:normalizeCodexRateReservePercent({value:15}),arrayValue:normalizeCodexRateReservePercent([15]),outOfRange:normalizeCodexRateReservePercent(101)};",
            "process.stdout.write(JSON.stringify(values));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["validZero"], 0)
        self.assertEqual(payload["validHundred"], 100)
        self.assertIsNone(payload["booleanValue"])
        self.assertIsNone(payload["objectValue"])
        self.assertIsNone(payload["arrayValue"])
        self.assertIsNone(payload["outOfRange"])

    def test_rate_payload_preserves_policy_but_rejects_any_malformed_window(self) -> None:
        script = "\n".join([
            "const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));",
            function_block(self.main, "normalizeCodexRateTimestamp"),
            function_block(self.main, "normalizeCodexRateWindow"),
            function_block(self.main, "normalizeCodexRateReservePercent"),
            function_block(self.main, "codexRateLimitWasReached"),
            function_block(self.main, "normalizeCodexRatePayload"),
            "const malformedSecondary=normalizeCodexRatePayload({status:'ready',automationPolicy:{rateReservePercent:0},primary:{usedPercent:80,remainingPercent:20},secondary:{remainingPercent:'bad'}});",
            "const booleanPrimary=normalizeCodexRatePayload({status:'ready',rateReservePercent:10,primary:{usedPercent:true}});",
            "const booleanPolicy=normalizeCodexRatePayload({status:'ready',rateReservePercent:true,primary:{remainingPercent:20}});",
            "process.stdout.write(JSON.stringify({malformedSecondary,booleanPrimary,booleanPolicy}));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["malformedSecondary"]["status"], "unavailable")
        self.assertIsNone(payload["malformedSecondary"]["primary"])
        self.assertFalse(payload["malformedSecondary"]["quotaWindowsValid"])
        self.assertEqual(payload["malformedSecondary"]["rateReservePercent"], 0)
        self.assertEqual(payload["booleanPrimary"]["status"], "unavailable")
        self.assertIsNone(payload["booleanPrimary"]["primary"])
        self.assertIsNone(payload["booleanPolicy"]["rateReservePercent"])

    def test_save_posts_exact_policy_payload_and_trusts_backend_value(self) -> None:
        save = function_block(self.main, "saveCodexRateReserve")
        self.assertIn("CODEX_RATE_RESERVE_POLICY_ENDPOINT", save)
        self.assertNotIn("save_agent_preferences", save)
        script = "\n".join([
            'const CODEX_RATE_RESERVE_POLICY_ENDPOINT="/api/automation/quota-policy";',
            "let posted=null; let rateRefresh=0; let missionRefresh=0;",
            "const input={value:'0',setCustomValidity:()=>{},reportValidity:()=>{}};",
            "const els={codexRateReserveInput:input};",
            "const state={codexRate:{reserveSaveInFlight:false,reservePercent:15,reserveMessage:'',reserveTone:'neutral'},modal:{open:false,type:''}};",
            "const postJson=async(path,body)=>{posted={path,body};return {rateReservePercent:15,policy:{rateReservePercent:15}};};",
            "const renderCodexRateReserve=()=>{};",
            "const refreshCodexRateLimits=async()=>{rateRefresh+=1;};",
            "const pollMissionReadModel=async()=>{missionRefresh+=1;};",
            "const pollOpenPropReport=async()=>{};",
            "const safeDashboardDisplayText=(value,fallback)=>String(value||fallback);",
            function_block(self.main, "normalizeCodexRateReservePercent"),
            function_block(self.main, "readCodexRateReserveInput"),
            save,
            "(async()=>{await saveCodexRateReserve({preventDefault(){}});await Promise.resolve();process.stdout.write(JSON.stringify({posted,rateRefresh,missionRefresh,reserve:state.codexRate.reservePercent,inputValue:input.value,message:state.codexRate.reserveMessage,tone:state.codexRate.reserveTone}));})().catch(error=>{console.error(error);process.exit(1);});",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["posted"], {
            "path": "/api/automation/quota-policy",
            "body": {"rateReservePercent": 0},
        })
        self.assertEqual(payload["reserve"], 15)
        self.assertEqual(payload["inputValue"], "15")
        self.assertEqual(payload["tone"], "warning")
        self.assertIn("Backend ใช้ค่า 15%", payload["message"])
        self.assertEqual(payload["rateRefresh"], 1)
        self.assertEqual(payload["missionRefresh"], 1)

    def test_dependent_agent_views_read_the_central_reserve(self) -> None:
        collaboration = function_block(
            self.main,
            "normalizeAgentCollaborationPayload",
        )
        collaboration_form = function_block(
            self.main,
            "collaborationFormPayload",
        )
        collaboration_render = function_block(
            self.main,
            "renderAgentCollaborationControl",
        )
        council = function_block(self.main, "signalCouncilAutomationModel")
        council_health = function_block(self.main, "signalRoundHealthModel")

        self.assertIn("state.codexRate.reserveAuthoritative", collaboration)
        self.assertIn("state.codexRate.reservePercent", collaboration)
        self.assertIn("state.codexRate?.reserveAuthoritative", council)
        self.assertIn("state.codexRate.reservePercent", council)
        self.assertIn("state.codexRate.reservePercent", collaboration_form)
        self.assertIn("state.codexRate?.reserveAuthoritative", council_health)
        self.assertIn("ต้องเหลืออย่างน้อย", collaboration_render)
        self.assertNotIn(
            "`ต้องมากกว่า ${collaboration.minRemainingPercent}%`",
            collaboration_render,
        )

    def test_deferred_research_is_not_mislabelled_as_analyzing(self) -> None:
        script = "\n".join([
            "const tradingResearchBlueprintObject=(value)=>value&&typeof value==='object'&&!Array.isArray(value)?value:{};",
            "const safeDashboardDisplayText=(value,fallback)=>String(value||fallback||'');",
            "const TRADING_RESEARCH_STATE_LABELS={queued:'อยู่ในคิว',queued_deferred:'รอโควตา',in_progress:'กำลังวิเคราะห์',research_failed:'ล้มเหลว'};",
            function_block(self.main, "tradingResearchAttemptQueueState"),
            function_block(self.main, "tradingResearchAttemptReadModel"),
            "const deferred=tradingResearchAttemptReadModel({researchState:'in_progress',latestResearchMissionId:'m1'},null,{id:'m1',status:'queued',reasonCode:'quota_below_reserve'});",
            "const catalogDeferred=tradingResearchAttemptReadModel({researchState:'queued_deferred',latestResearchMissionId:'m2'},null,null);",
            "const queued=tradingResearchAttemptReadModel({}, {status:'queued'}, null);",
            "const running=tradingResearchAttemptReadModel({}, {status:'running'}, null);",
            "process.stdout.write(JSON.stringify({deferred,catalogDeferred,queued,running}));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["deferred"]["state"], "queued_deferred")
        self.assertTrue(payload["deferred"]["isQuotaDeferred"])
        self.assertFalse(payload["deferred"]["isRunning"])
        self.assertEqual(payload["catalogDeferred"]["state"], "queued_deferred")
        self.assertTrue(payload["catalogDeferred"]["isQuotaDeferred"])
        self.assertFalse(payload["catalogDeferred"]["isRunning"])
        self.assertEqual(payload["queued"]["state"], "queued")
        self.assertFalse(payload["queued"]["isRunning"])
        self.assertEqual(payload["running"]["state"], "in_progress")
        self.assertTrue(payload["running"]["isRunning"])


if __name__ == "__main__":
    unittest.main()
