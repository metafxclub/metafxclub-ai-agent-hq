import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "frontend" / "index.html"
MAIN_JS_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "main.js"
STYLES_PATH = PROJECT_ROOT / "frontend" / "src" / "app" / "styles.css"
CONTRACT_PATH = PROJECT_ROOT / "contracts" / "connections" / "dashboard-connection-contract.json"


def source_block(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index + len(start))
    return source[start_index:end_index]


def function_source(source: str, name: str) -> str:
    match = re.search(rf"(?:async\s+)?function\s+{re.escape(name)}\s*\(", source)
    if not match:
        raise AssertionError(f"missing frontend function {name}")
    remainder = source[match.start() + 1 :]
    next_match = re.search(r"\n(?:async\s+)?function\s+[A-Za-z0-9_$]+\s*\(", remainder)
    if not next_match:
        return source[match.start() :]
    return source[match.start() : match.start() + 1 + next_match.start()]


def optional_function_source(source: str, name: str) -> str:
    """Return an empty block when a retired device-only helper was removed."""
    try:
        return function_source(source, name)
    except AssertionError:
        return ""


class GlobalMetatraderHubFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX_PATH.read_text(encoding="utf-8")
        cls.main = MAIN_JS_PATH.read_text(encoding="utf-8")
        cls.styles = STYLES_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

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
            path = Path(directory) / "global-metatrader-hub-regression.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run(
                [self.node_binary(), str(path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if result.returncode != 0:
                raise AssertionError(
                    f"Node regression failed with exit {result.returncode}:\n{result.stderr}"
                )
        return json.loads(result.stdout)

    def test_header_replaces_unused_agent_chat_with_global_terminal_control(self) -> None:
        self.assertNotIn("Agent คุยกันเอง", self.index)
        for element_id in (
            "globalMetatraderControl",
            "globalMetatraderButton",
            "globalMetatraderPanel",
            "globalMetatraderScan",
            "globalMetatraderMt4Select",
            "globalMetatraderMt4Apply",
            "globalMetatraderMt5Select",
            "globalMetatraderMt5Apply",
            "globalMetatraderSystems",
        ):
            self.assertIn(f'id="{element_id}"', self.index)
        self.assertIn("เชื่อม MT4 / MT5", self.index)
        self.assertIn('aria-label="เชื่อม MT4 / MT5"', self.index)
        self.assertIn('class="metatrader-hub-compact-mark"', self.index)
        self.assertIn("ไม่เปิด Terminal", self.index)
        self.assertIn("ไม่อ่านเลขบัญชี", self.index)
        self.assertIn("ไม่เปิด Demo / Live", self.index)

    def test_contract_fans_mt4_to_three_systems_and_mt5_to_supported_two(self) -> None:
        terminal_contract = self.contract["terminalTargetSelection"]
        hub = terminal_contract["centralHeaderControl"]
        self.assertEqual(hub["labelTh"], "เชื่อม MT4 / MT5")
        self.assertEqual(hub["statusEndpoint"], "GET /api/integrations/metatrader/global")
        self.assertEqual(hub["discoveryEndpoint"], "POST /api/integrations/metatrader/global/discover")
        self.assertEqual(hub["selectionEndpoint"], "POST /api/integrations/metatrader/global/select")
        self.assertEqual(
            hub["selectionFanOutByPlatform"]["mt4"],
            ["left_analytics_console", "right_server_racks", "right_tool_console"],
        )
        self.assertEqual(
            hub["selectionFanOutByPlatform"]["mt5"],
            ["right_server_racks", "right_tool_console"],
        )
        self.assertTrue(hub["backendAtomicFanOut"])
        self.assertTrue(hub["frontendFanOutForbidden"])
        self.assertTrue(hub["backendReadBackVerificationRequired"])
        self.assertEqual(hub["interactiveSelectionSurface"], "central_header_only")
        self.assertFalse(hub["deviceDashboardSelectionControlsAllowed"])
        self.assertTrue(hub["deviceDashboardSelectionStatusReadOnly"])
        self.assertTrue(hub["selectionDoesNotLaunchTerminal"])
        self.assertTrue(hub["selectionDoesNotEnableLiveTrading"])
        self.assertNotIn("terminal_workstation", json.dumps(hub["selectionFanOutByPlatform"]))

    def test_frontend_target_map_matches_the_contract(self) -> None:
        target_block = source_block(
            self.main,
            "const GLOBAL_METATRADER_TARGETS = Object.freeze([",
            "]);\nconst RESEARCH_SHEET_HUB_ENDPOINT",
        )
        for prop_id in ("left_analytics_console", "right_server_racks", "right_tool_console"):
            constant_name = {
                "left_analytics_console": "AI_TRADE_COUNCIL_PROP_ID",
                "right_server_racks": "EA_FACTORY_PROP_ID",
                "right_tool_console": "EA_OPTIMIZATION_LAB_PROP_ID",
            }[prop_id]
            self.assertIn(f"propId: {constant_name}", target_block)
        self.assertRegex(
            target_block,
            r'AI_TRADE_COUNCIL_PROP_ID,[\s\S]*?supportedPlatforms: Object\.freeze\(\["MT4"\]\)',
        )
        self.assertEqual(target_block.count('supportedPlatforms: Object.freeze(["MT4", "MT5"])'), 2)
        self.assertNotIn("terminal_workstation", target_block)

    def test_lowercase_backend_platform_is_normalized_before_global_matching(self) -> None:
        normalize_source = function_source(self.main, "normalizeMetatraderCandidate")
        model_source = function_source(self.main, "getMetatraderSelectionModel")
        system_source = function_source(self.main, "globalMetatraderSystemModels")
        registry_source = function_source(self.main, "globalMetatraderCandidateRegistry")
        script = "\n".join([
            "const candidate = {candidateId:'mtc-44444444444444444444444444444444',platform:'mt4',labelTh:'MT4 หลัก',detected:true,runningState:'platform_running_detected'};",
            "const GLOBAL_METATRADER_TARGETS = [{propId:'left_analytics_console',labelTh:'สภา AI Trade',supportedPlatforms:['MT4']}];",
            "const state = {globalMetatraderHub:{checklists:{left_analytics_console:{metatraderSelection:{candidateCount:1,candidates:[candidate],selectedCandidate:candidate,canSelect:true}}}}};",
            "function safeDashboardDisplayText(value, fallback='') { const text=String(value || '').trim(); return text || fallback; }",
            normalize_source,
            model_source,
            system_source,
            registry_source,
            "const systems=globalMetatraderSystemModels(); const registry=globalMetatraderCandidateRegistry(systems); process.stdout.write(JSON.stringify({platform:registry[0]?.platform,configured:systems[0]?.configured}));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload, {"platform": "MT4", "configured": True})

    def test_scan_is_read_only_and_uses_the_global_backend_endpoint(self) -> None:
        block = source_block(
            self.main,
            "async function scanGlobalMetatraderHub()",
            "async function applyGlobalMetatraderTarget(platform)",
        )
        self.assertIn('postJson("/api/integrations/metatrader/global/discover", {})', block)
        self.assertNotIn("propId:", block)
        self.assertIn("acceptGlobalMetatraderHubReadModel(response)", block)
        self.assertIn("สแกนตำแหน่งมาตรฐานและโปรแกรมที่เปิดอยู่แบบอ่านอย่างเดียว", block)
        for forbidden in ("terminal.exe", "terminal64.exe", "Get-Process", "account_number", "broker_server"):
            self.assertNotIn(forbidden, block)

    def test_apply_posts_once_and_verifies_atomic_backend_readback(self) -> None:
        block = source_block(
            self.main,
            "async function applyGlobalMetatraderTarget(platform)",
            "function renderAiTradeMt4QuickSetup(",
        )
        self.assertEqual(block.count('postJson("/api/integrations/metatrader/global/select"'), 1)
        self.assertIn("platform: platform.toLowerCase()", block)
        self.assertIn("candidateId", block)
        self.assertIn("acceptGlobalMetatraderHubReadModel(response)", block)
        self.assertIn('response?.atomic === true', block)
        self.assertIn('configurationStatus === "configured"', block)
        self.assertIn("global_selection_readback_failed", block)
        self.assertIn("reconcileGlobalMetatraderSelection(platform, candidateId)", block)
        self.assertNotIn("ค่าเดิมของทุกระบบยังคงอยู่", block)
        self.assertIn(".filter((target) => target.propId !== EA_FACTORY_PROP_ID)", block)
        self.assertIn("loadPropReport(target.propId, { forceFresh: true })", block)
        self.assertIn("loadEaFactoryReadModel({ forceFresh: true })", block)
        self.assertNotIn("Promise.allSettled(pendingTargets.map", block)
        self.assertNotIn("propId: target.propId", block)

    def test_mutations_invalidate_stale_reads_and_reads_pause_while_busy(self) -> None:
        load = function_source(self.main, "loadGlobalMetatraderHub")
        scan = function_source(self.main, "scanGlobalMetatraderHub")
        apply = function_source(self.main, "applyGlobalMetatraderTarget")
        self.assertIn("if (hub.inFlight) return globalMetatraderSystemModels();", load)
        self.assertIn("hub.requestId += 1;", scan)
        self.assertIn("hub.requestId += 1;", apply)

    def test_device_cta_cannot_be_closed_by_the_same_bubbling_click(self) -> None:
        opener = function_source(self.main, "openGlobalMetatraderHubFromDevice")
        self.assertIn("event?.stopPropagation?.();", opener)
        self.assertLess(
            opener.index("event?.stopPropagation?.();"),
            opener.index("setGlobalMetatraderPanelOpen(true)"),
        )
        self.assertLess(
            opener.index("setGlobalMetatraderPanelOpen(true)"),
            opener.index("closeGameModal()"),
        )
        self.assertIn("Google Sheet กำลังมีขั้นตอนที่ยังไม่จบ", opener)
        daily = function_source(self.main, "renderSignalDailyPanel")
        self.assertIn('addEventListener("click", (event)', daily)
        self.assertIn("openGlobalMetatraderHubFromDevice(event)", daily)
        listeners = source_block(
            self.main,
            'els.modalAiTradeMt4OpenGlobal?.addEventListener("click"',
            'els.modalAiTradeMt4QuickCopy?.addEventListener("click"',
        )
        self.assertIn("openGlobalMetatraderHubFromDevice(event)", listeners)

    def test_sheet_busy_block_keeps_device_modal_open_and_explains_the_next_step(self) -> None:
        opener = function_source(self.main, "openGlobalMetatraderHubFromDevice")
        script = "\n".join([
            'const AI_TRADE_COUNCIL_PROP_ID = "left_analytics_console";',
            "const state = {modal:{open:true,id:AI_TRADE_COUNCIL_PROP_ID}};",
            "const status = {dataset:{},textContent:''};",
            "const scan = {focus(){}};",
            "const els = {modalAiTradeMt4QuickStatus:status,globalMetatraderScan:scan};",
            "const window = {requestAnimationFrame(callback){callback();}};",
            "let allowOpen = false; let closeCalls = 0; let prepareCalls = 0;",
            "function setGlobalMetatraderPanelOpen(){return allowOpen;}",
            "function closeGameModal(){closeCalls += 1; state.modal.open=false;}",
            "function prepareGlobalMetatraderHubOnOpen(){prepareCalls += 1;}",
            opener,
            r'''const trigger={textContent:'เดิม',title:'',setAttribute(name,value){this[name]=value;}};
const event={currentTarget:trigger,stopPropagation(){}};
const blocked=openGlobalMetatraderHubFromDevice(event);
const blockedSnapshot={blocked,modalOpen:state.modal.open,closeCalls,text:trigger.textContent,status:status.textContent};
allowOpen=true;
const opened=openGlobalMetatraderHubFromDevice(event);
process.stdout.write(JSON.stringify({blockedSnapshot,opened,modalOpen:state.modal.open,closeCalls,prepareCalls}));''',
        ])
        payload = self.run_node(script)
        self.assertFalse(payload["blockedSnapshot"]["blocked"])
        self.assertTrue(payload["blockedSnapshot"]["modalOpen"])
        self.assertEqual(payload["blockedSnapshot"]["closeCalls"], 0)
        self.assertIn("Google Sheet", payload["blockedSnapshot"]["text"])
        self.assertIn("Google Sheet", payload["blockedSnapshot"]["status"])
        self.assertTrue(payload["opened"])
        self.assertFalse(payload["modalOpen"])
        self.assertEqual(payload["closeCalls"], 1)
        self.assertEqual(payload["prepareCalls"], 1)

    def test_manager_scan_intent_returns_to_central_hub_not_a_device_picker(self) -> None:
        submit = function_source(self.main, "submitManagerCommand")
        branch_start = submit.index("if (isMetatraderDiscoveryIntent(goal))")
        branch_end = submit.index('els.runCommandButton.textContent = "กำลังแจกงาน...";', branch_start)
        branch = submit[branch_start:branch_end]
        self.assertIn("runMetatraderDiscoveryIntent", branch)
        self.assertIn("openGlobalMetatraderHubFromDevice()", branch)
        self.assertNotIn("openPropDialog(result.propId)", branch)
        self.assertNotIn("routeAgentToTargetId(requester, result.propId", branch)

    def test_scan_intent_does_not_claim_success_for_reconciled_unconfirmed_state(self) -> None:
        intent_source = function_source(self.main, "runMetatraderDiscoveryIntent")
        script = "\n".join([
            "const GLOBAL_METATRADER_DISCOVERY_PROP_ID='mission_strategy_table';",
            "let response={ok:true,reconciled:true,scanResponseUnconfirmed:true};",
            "async function scanGlobalMetatraderHub(){return response;}",
            "function globalMetatraderCandidateRegistry(){return [{candidateId:'mtc-one'}];}",
            intent_source,
            r'''(async()=>{const unconfirmed=await runMetatraderDiscoveryIntent();response={ok:true};const confirmed=await runMetatraderDiscoveryIntent();process.stdout.write(JSON.stringify({unconfirmed,confirmed}));})().catch((error)=>{console.error(error);process.exit(1);});''',
        ])
        payload = self.run_node(script)
        self.assertFalse(payload["unconfirmed"]["ok"])
        self.assertIn("ยังไม่ยืนยัน", payload["unconfirmed"]["reply"])
        self.assertNotIn("สแกนแบบอ่านอย่างเดียวแล้ว", payload["unconfirmed"]["reply"])
        self.assertTrue(payload["confirmed"]["ok"])
        self.assertIn("สแกนแบบอ่านอย่างเดียวแล้ว", payload["confirmed"]["reply"])

    def test_agent_chat_scan_intent_returns_to_central_hub_not_a_device_picker(self) -> None:
        handler = function_source(self.main, "handleModalSend")
        branch_start = handler.index("if (isMetatraderDiscoveryIntent(prompt))")
        branch_end = handler.index("} else {", branch_start)
        branch = handler[branch_start:branch_end]
        self.assertIn("openCentralMetatraderHub = result.ok", branch)
        self.assertNotIn("dashboardToOpen", handler)
        self.assertNotIn("openPropDialog", handler)
        self.assertIn(
            "if (openCentralMetatraderHub) openGlobalMetatraderHubFromDevice();",
            handler,
        )

    def test_multiple_opaque_candidates_require_exactly_one_running_terminal(self) -> None:
        suggested_source = function_source(self.main, "globalMetatraderSuggestedChoice")
        render_source = function_source(self.main, "renderGlobalMetatraderSelect")
        script = "\n".join([
            "const state={globalMetatraderHub:{choices:{MT4:''},inFlight:false,operation:''}};",
            "const document={createElement(){return {value:'',textContent:''};}};",
            "const systems=[{supportedPlatforms:['MT4'],selectedCandidate:null},{supportedPlatforms:['MT4'],selectedCandidate:null},{supportedPlatforms:['MT4'],selectedCandidate:null}];",
            "const makeCandidate=(id,runningState)=>({candidateId:id,platform:'MT4',labelTh:id,detected:true,runningState});",
            "const makeSelect=()=>({children:[],disabled:false,value:'',set innerHTML(value){this.children=[];},appendChild(value){this.children.push(value);}});",
            "const run=(states)=>{const registry=states.map((value,index)=>makeCandidate(`mtc-${index}`,value));const select=makeSelect();const button={disabled:false,textContent:''};state.globalMetatraderHub.choices.MT4='';renderGlobalMetatraderSelect('MT4',select,button,systems,registry);return {choice:state.globalMetatraderHub.choices.MT4,selectDisabled:select.disabled,buttonDisabled:button.disabled,buttonText:button.textContent};};",
            suggested_source,
            render_source,
            "const stopped=run(['not_running_detected','not_running_detected']);",
            "const twoRunning=run(['platform_running_detected','platform_running_detected']);",
            "const uniqueRunning=run(['not_running_detected','platform_running_detected']);",
            "process.stdout.write(JSON.stringify({stopped,twoRunning,uniqueRunning}));",
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["stopped"]["choice"], "")
        self.assertTrue(payload["stopped"]["selectDisabled"])
        self.assertTrue(payload["stopped"]["buttonDisabled"])
        self.assertIn("เปิด MT4", payload["stopped"]["buttonText"])
        self.assertEqual(payload["twoRunning"]["choice"], "")
        self.assertTrue(payload["twoRunning"]["selectDisabled"])
        self.assertTrue(payload["twoRunning"]["buttonDisabled"])
        self.assertIn("ปิด MT4", payload["twoRunning"]["buttonText"])
        self.assertEqual(payload["uniqueRunning"]["choice"], "mtc-1")
        self.assertTrue(payload["uniqueRunning"]["selectDisabled"])
        self.assertFalse(payload["uniqueRunning"]["buttonDisabled"])

    def test_apply_behavior_posts_once_and_reconciles_backend_truth_after_response_loss(self) -> None:
        normalize_source = function_source(self.main, "normalizeMetatraderCandidate")
        system_source = function_source(self.main, "globalMetatraderSystemModels")
        registry_source = function_source(self.main, "globalMetatraderCandidateRegistry")
        accept_source = function_source(self.main, "acceptGlobalMetatraderHubReadModel")
        reconcile_source = function_source(self.main, "reconcileGlobalMetatraderSelection")
        apply_source = function_source(self.main, "applyGlobalMetatraderTarget")
        script = "\n".join([
            'const AI_TRADE_COUNCIL_PROP_ID = "left_analytics_console";',
            'const EA_FACTORY_PROP_ID = "right_server_racks";',
            'const EA_OPTIMIZATION_LAB_PROP_ID = "right_tool_console";',
            "const GLOBAL_METATRADER_TARGETS = Object.freeze([",
            "  {propId:AI_TRADE_COUNCIL_PROP_ID,labelTh:'สภา AI Trade',supportedPlatforms:Object.freeze(['MT4'])},",
            "  {propId:EA_FACTORY_PROP_ID,labelTh:'โรงงานสร้าง EA / Indicator',supportedPlatforms:Object.freeze(['MT4','MT5'])},",
            "  {propId:EA_OPTIMIZATION_LAB_PROP_ID,labelTh:'ห้องทดลอง Backtest / Optimize',supportedPlatforms:Object.freeze(['MT4','MT5'])},",
            "]);",
            "const mt4 = {candidateId:'mtc-44444444444444444444444444444444',platform:'MT4',labelTh:'MT4 หลัก',detected:true,runningState:'platform_running_detected'};",
            "const mt5 = {candidateId:'mtc-55555555555555555555555555555555',platform:'MT5',labelTh:'MT5 หลัก',detected:true,runningState:'not_running_detected'};",
            "const makeTarget = (propId, selectedCandidate=null) => ({propId,status:selectedCandidate?'configured':'not_configured',selectedCandidate,adapterReady:false});",
            "const makeModel = (platform='', candidate=null) => ({status:platform?'configured':'not_configured',candidates:[mt4,mt5],platforms:{mt4:{configurationStatus:platform==='mt4'?'configured':'not_configured',selectedCandidate:platform==='mt4'?candidate:null,targets:GLOBAL_METATRADER_TARGETS.map((target)=>makeTarget(target.propId,platform==='mt4'&&target.supportedPlatforms.includes('MT4')?candidate:null))},mt5:{configurationStatus:platform==='mt5'?'configured':'not_configured',selectedCandidate:platform==='mt5'?candidate:null,targets:GLOBAL_METATRADER_TARGETS.filter((target)=>target.supportedPlatforms.includes('MT5')).map((target)=>makeTarget(target.propId,platform==='mt5'?candidate:null))}}});",
            "const initialModel = makeModel();",
            "const state = {globalMetatraderHub:{readModel:initialModel,checklists:{},choices:{MT4:mt4.candidateId,MT5:mt5.candidateId},inFlight:false,operation:'',message:'',tone:'neutral',lastReadCount:3,lastLoadedAt:0},modal:{open:false,type:'',id:'',eaFactory:{},eaOptimizationLab:{}}};",
            "let posts = []; let reads = 0; let fail = false; let failStatus = null; let failMessage = 'forced'; let commitBeforeThrow = false; let backendReadModel = initialModel;",
            "function getMetatraderSelectionModel(checklist) { return checklist?.metatraderSelection || {candidates:[],selectedCandidate:null,canSelect:false}; }",
            "function renderGlobalMetatraderHubControl() {}",
            "function addBridgeEvent() {}",
            "function safeDashboardDisplayText(value, fallback='') { return String(value || fallback); }",
            "async function postJson(url, body) { posts.push({url,body}); const candidate=body.platform==='mt4'?mt4:mt5; if (fail) { if (commitBeforeThrow) backendReadModel=makeModel(body.platform,candidate); const error=new Error(failMessage); if (Number.isInteger(failStatus)) { error.status=failStatus; error.body={error:failMessage}; } throw error; } backendReadModel=makeModel(body.platform,candidate); return {ok:true,atomic:true,globalMetatraderHub:backendReadModel}; }",
            "async function fetchJson(url) { reads += 1; if (url !== '/api/integrations/metatrader/global') throw new Error('wrong endpoint'); return {ok:true,globalMetatraderHub:backendReadModel}; }",
            "async function loadPropReport() { return {}; }",
            "async function loadEaFactoryReadModel() { return {}; }",
            normalize_source,
            system_source,
            registry_source,
            accept_source,
            reconcile_source,
            apply_source,
            r'''(async () => {
  const mt4Result = await applyGlobalMetatraderTarget('MT4');
  const afterMt4 = state.globalMetatraderHub.readModel.platforms.mt4;
  const postsAfterMt4 = posts.length;
  const repeatedMt4 = await applyGlobalMetatraderTarget('MT4');
  const postsAfterRepeatedMt4 = posts.length;
  const readsAfterRepeatedMt4 = reads;
  const mt5Result = await applyGlobalMetatraderTarget('MT5');
  const afterMt5 = state.globalMetatraderHub.readModel.platforms.mt5;
  const stableModel = state.globalMetatraderHub.readModel;
  state.globalMetatraderHub.choices.MT4 = mt4.candidateId;
  fail = true;
  posts = [];
  const failed = await applyGlobalMetatraderTarget('MT4');
  const failedTone = state.globalMetatraderHub.tone;
  const failedPosts = [...posts];
  const modelUnchanged = state.globalMetatraderHub.readModel===stableModel;
  commitBeforeThrow = true;
  posts = [];
  const reconciled = await applyGlobalMetatraderTarget('MT4');
  const reconciledTone = state.globalMetatraderHub.tone;
  const reconciledCandidate = state.globalMetatraderHub.readModel.platforms.mt4.selectedCandidate?.candidateId;
  const reconciledPosts = [...posts];
  failStatus = 409;
  failMessage = 'กรุณาปิด MT4 อื่น เปิดเฉพาะ MT4 ที่ต้องการ กดสแกนใหม่';
  commitBeforeThrow = false;
  posts = [];
  const readsBeforeKnown409 = reads;
  const known409 = await applyGlobalMetatraderTarget('MT4');
  const known409Result = {result:known409,tone:state.globalMetatraderHub.tone,message:state.globalMetatraderHub.message,reads:reads-readsBeforeKnown409,posts:[...posts]};
  failStatus = 503;
  failMessage = 'temporary upstream failure';
  commitBeforeThrow = true;
  posts = [];
  const readsBeforeAmbiguous503 = reads;
  const ambiguous503 = await applyGlobalMetatraderTarget('MT4');
  const ambiguous503Result = {result:ambiguous503,tone:state.globalMetatraderHub.tone,reads:reads-readsBeforeAmbiguous503,posts:[...posts]};
  process.stdout.write(JSON.stringify({mt4Result,afterMt4,postsAfterMt4,repeatedMt4,postsAfterRepeatedMt4,readsAfterRepeatedMt4,mt5Result,afterMt5,failed,failedTone,failedPosts,modelUnchanged,reconciled,reconciledTone,reconciledCandidate,reconciledPosts,known409Result,ambiguous503Result}));
})().catch((error) => { console.error(error); process.exit(1); });''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["mt4Result"], {"ok": True, "atomic": True, "succeeded": 3, "total": 3})
        self.assertEqual(payload["afterMt4"]["configurationStatus"], "configured")
        self.assertEqual(payload["postsAfterMt4"], 1)
        self.assertEqual(payload["repeatedMt4"], {"ok": True, "atomic": True, "succeeded": 3, "total": 3})
        self.assertEqual(payload["postsAfterRepeatedMt4"], 2)
        self.assertEqual(payload["readsAfterRepeatedMt4"], 0)
        self.assertEqual(payload["mt5Result"], {"ok": True, "atomic": True, "succeeded": 2, "total": 2})
        self.assertEqual(payload["afterMt5"]["configurationStatus"], "configured")
        self.assertIsNone(payload["failed"])
        self.assertEqual(payload["failedTone"], "error")
        self.assertEqual(len(payload["failedPosts"]), 1)
        self.assertTrue(payload["modelUnchanged"])
        self.assertEqual(
            payload["reconciled"],
            {"ok": True, "atomic": True, "reconciled": True, "succeeded": 3, "total": 3},
        )
        self.assertEqual(payload["reconciledTone"], "success")
        self.assertEqual(payload["reconciledCandidate"], "mtc-44444444444444444444444444444444")
        self.assertEqual(len(payload["reconciledPosts"]), 1)
        self.assertIsNone(payload["known409Result"]["result"])
        self.assertEqual(payload["known409Result"]["tone"], "error")
        self.assertIn("ปิด MT4 อื่น", payload["known409Result"]["message"])
        self.assertEqual(payload["known409Result"]["reads"], 0)
        self.assertEqual(len(payload["known409Result"]["posts"]), 1)
        self.assertEqual(
            payload["ambiguous503Result"]["result"],
            {"ok": True, "atomic": True, "reconciled": True, "succeeded": 3, "total": 3},
        )
        self.assertEqual(payload["ambiguous503Result"]["tone"], "success")
        self.assertEqual(payload["ambiguous503Result"]["reads"], 1)
        self.assertEqual(len(payload["ambiguous503Result"]["posts"]), 1)

    def test_scan_response_loss_reconciles_backend_truth_without_resubmitting(self) -> None:
        normalize_source = function_source(self.main, "normalizeMetatraderCandidate")
        system_source = function_source(self.main, "globalMetatraderSystemModels")
        registry_source = function_source(self.main, "globalMetatraderCandidateRegistry")
        accept_source = function_source(self.main, "acceptGlobalMetatraderHubReadModel")
        scan_source = function_source(self.main, "scanGlobalMetatraderHub")
        script = "\n".join([
            "const GLOBAL_METATRADER_TARGETS=[{propId:'left_analytics_console',labelTh:'สภา AI Trade',supportedPlatforms:['MT4']}];",
            "const candidate={candidateId:'mtc-44444444444444444444444444444444',platform:'MT4',labelTh:'MT4 หลัก',detected:true,runningState:'platform_running_detected'};",
            "const model={status:'not_configured',candidates:[candidate],platforms:{mt4:{configurationStatus:'not_configured',selectedCandidate:null,targets:[{propId:'left_analytics_console',status:'not_configured',selectedCandidate:null}],candidates:[candidate]},mt5:{configurationStatus:'not_configured',selectedCandidate:null,targets:[],candidates:[]}}};",
            "const state={globalMetatraderHub:{readModel:null,checklists:{},choices:{MT4:'',MT5:''},inFlight:false,operation:'',message:'',tone:'neutral',backendAvailable:true,lastReadCount:0,lastLoadedAt:0,lastScannedAt:0,requestId:0}};",
            "let posts=0; let reads=0; let events=0;",
            "function getMetatraderSelectionModel(value){return value?.metatraderSelection||{candidates:[],selectedCandidate:null,canSelect:false};}",
            "function renderGlobalMetatraderHubControl(){}",
            "function safeDashboardDisplayText(value,fallback=''){return String(value||fallback);}",
            "function addBridgeEvent(){events+=1;}",
            "async function postJson(){posts+=1; throw new Error('response lost');}",
            "async function fetchJson(url){reads+=1; if(url!=='/api/integrations/metatrader/global') throw new Error('wrong endpoint'); return {ok:true,globalMetatraderHub:model};}",
            normalize_source,
            system_source,
            registry_source,
            accept_source,
            scan_source,
            r'''(async()=>{const result=await scanGlobalMetatraderHub(); process.stdout.write(JSON.stringify({result,posts,reads,events,tone:state.globalMetatraderHub.tone,available:state.globalMetatraderHub.backendAvailable,candidateCount:state.globalMetatraderHub.readModel.candidates.length,message:state.globalMetatraderHub.message}));})().catch((error)=>{console.error(error);process.exit(1);});''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["posts"], 1)
        self.assertEqual(payload["reads"], 1)
        self.assertEqual(payload["events"], 1)
        self.assertTrue(payload["result"]["reconciled"])
        self.assertTrue(payload["result"]["scanResponseUnconfirmed"])
        self.assertEqual(payload["tone"], "warning")
        self.assertTrue(payload["available"])
        self.assertEqual(payload["candidateCount"], 1)
        self.assertIn("ตรวจสถานะล่าสุดจาก Backend", payload["message"])

    def test_global_read_timeout_replaces_preserved_stale_success_copy(self) -> None:
        load_source = function_source(self.main, "loadGlobalMetatraderHub")
        script = "\n".join([
            "const state={globalMetatraderHub:{readModel:{stale:true},checklists:{old:{}},backendAvailable:true,lastReadCount:3,status:'ready',message:'ตั้งค่าสำเร็จแล้ว',tone:'success',requestId:0,lastLoadedAt:1,inFlight:false}};",
            "function globalMetatraderSystemModels(){return [];}",
            "function renderGlobalMetatraderHubControl(){}",
            "async function fetchJson(){const error=new Error('request timed out');error.name='AbortError';throw error;}",
            load_source,
            r'''(async()=>{const result=await loadGlobalMetatraderHub({preserveMessage:true});process.stdout.write(JSON.stringify({result,message:state.globalMetatraderHub.message,tone:state.globalMetatraderHub.tone,status:state.globalMetatraderHub.status,available:state.globalMetatraderHub.backendAvailable,readModel:state.globalMetatraderHub.readModel}));})().catch((error)=>{console.error(error);process.exit(1);});''',
        ])
        payload = self.run_node(script)
        self.assertIsNone(payload["result"])
        self.assertEqual(payload["tone"], "error")
        self.assertEqual(payload["status"], "error")
        self.assertFalse(payload["available"])
        self.assertIsNone(payload["readModel"])
        self.assertNotEqual(payload["message"], "ตั้งค่าสำเร็จแล้ว")
        self.assertIn("ยังอ่านสถานะ", payload["message"])

    def test_scan_known_4xx_is_not_reconciled_but_5xx_remains_indeterminate(self) -> None:
        scan_source = function_source(self.main, "scanGlobalMetatraderHub")
        script = "\n".join([
            "const emptyModel={status:'not_configured',candidates:[],platforms:{mt4:{configurationStatus:'not_configured',selectedCandidate:null,targets:[]},mt5:{configurationStatus:'not_configured',selectedCandidate:null,targets:[]}}};",
            "const state={globalMetatraderHub:{readModel:null,checklists:{},choices:{MT4:'',MT5:''},inFlight:false,operation:'',message:'',tone:'neutral',backendAvailable:true,lastReadCount:0,lastLoadedAt:0,lastScannedAt:0,requestId:0}};",
            "let responseStatus=409;let reads=0;let events=0;",
            "function renderGlobalMetatraderHubControl(){}",
            "function safeDashboardDisplayText(value,fallback=''){return String(value||fallback);}",
            "function addBridgeEvent(){events+=1;}",
            "function acceptGlobalMetatraderHubReadModel(payload){const model=payload.globalMetatraderHub||payload;state.globalMetatraderHub.readModel=model;state.globalMetatraderHub.backendAvailable=true;state.globalMetatraderHub.status='ready';return model;}",
            "function globalMetatraderCandidateRegistry(){return [];}",
            "async function postJson(){const error=new Error('กรุณากดสแกนใหม่');error.status=responseStatus;error.body={error:error.message};throw error;}",
            "async function fetchJson(){reads+=1;return {ok:true,globalMetatraderHub:emptyModel};}",
            scan_source,
            r'''(async()=>{
  const known4xx=await scanGlobalMetatraderHub();
  const four={result:known4xx,reads,message:state.globalMetatraderHub.message,tone:state.globalMetatraderHub.tone,events};
  responseStatus=503;
  const ambiguous5xx=await scanGlobalMetatraderHub();
  const five={result:ambiguous5xx,reads,message:state.globalMetatraderHub.message,tone:state.globalMetatraderHub.tone,events};
  process.stdout.write(JSON.stringify({four,five}));
})().catch((error)=>{console.error(error);process.exit(1);});''',
        ])
        payload = self.run_node(script)
        self.assertIsNone(payload["four"]["result"])
        self.assertEqual(payload["four"]["reads"], 0)
        self.assertEqual(payload["four"]["tone"], "error")
        self.assertIn("กดสแกนใหม่", payload["four"]["message"])
        self.assertNotIn("สแกนสำเร็จ", payload["four"]["message"])
        self.assertTrue(payload["five"]["result"]["scanResponseUnconfirmed"])
        self.assertEqual(payload["five"]["reads"], 1)
        self.assertEqual(payload["five"]["tone"], "warning")
        self.assertIn("ยังไม่ยืนยันว่าการสแกนสำเร็จ", payload["five"]["message"])
        self.assertNotIn("สแกนสำเร็จ •", payload["five"]["message"])
        self.assertEqual(payload["five"]["events"], 1)

    def test_force_fresh_consumer_reads_wait_then_fetch_the_post_apply_generation(self) -> None:
        prop_loader = function_source(self.main, "loadPropReport")
        factory_loader = function_source(self.main, "loadEaFactoryReadModel")
        script = "\n".join([
            "const PROP_REPORT_FETCH_TIMEOUT_MS=1000; const EA_FACTORY_PROP_ID='right_server_racks';",
            "const propReportInFlight=new Map(); let eaFactoryReadModelInFlight=null;",
            "const state={propReportLoadState:{},propReports:{},propReportLoadedAt:{},panelObject:null,eaFactoryReadModel:{inFlight:false,lastLoadedAt:0,payload:null},modal:{open:false,id:null}};",
            "let propCalls=0; let factoryCalls=0; let resolveProp; let resolveFactory;",
            "function renderOperationalSidebars(){} function selectObject(){} function setEaFactoryActionState(){}",
            "function safeDashboardDisplayText(value,fallback=''){return String(value||fallback);}",
            "function mergeEaFactoryReadModel(payload){state.eaFactoryReadModel.payload=payload; return payload?.schemaVersion==='ea-factory-v1';}",
            "async function fetchJson(url){if(url.includes('/report')){propCalls+=1;if(propCalls===1)return new Promise((resolve)=>{resolveProp=resolve;});return {revision:2};}factoryCalls+=1;if(factoryCalls===1)return new Promise((resolve)=>{resolveFactory=resolve;});return {schemaVersion:'ea-factory-v1',revision:2};}",
            prop_loader,
            factory_loader,
            r'''(async()=>{
  const oldProp=loadPropReport('right_server_racks');
  const freshProp=loadPropReport('right_server_racks',{forceFresh:true});
  const oldFactory=loadEaFactoryReadModel();
  const freshFactory=loadEaFactoryReadModel({forceFresh:true});
  await Promise.resolve();
  resolveProp({revision:1}); resolveFactory({schemaVersion:'ea-factory-v1',revision:1});
  const values=await Promise.all([oldProp,freshProp,oldFactory,freshFactory]);
  process.stdout.write(JSON.stringify({propCalls,factoryCalls,values,storedProp:state.propReports.right_server_racks,storedFactory:state.eaFactoryReadModel.payload,factoryBusy:state.eaFactoryReadModel.inFlight}));
})().catch((error)=>{console.error(error);process.exit(1);});''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["propCalls"], 2)
        self.assertEqual(payload["factoryCalls"], 2)
        self.assertEqual(payload["values"][0]["revision"], 1)
        self.assertEqual(payload["values"][1]["revision"], 2)
        self.assertEqual(payload["values"][2]["revision"], 1)
        self.assertEqual(payload["values"][3]["revision"], 2)
        self.assertEqual(payload["storedProp"]["revision"], 2)
        self.assertEqual(payload["storedFactory"]["revision"], 2)
        self.assertFalse(payload["factoryBusy"])

    def test_global_read_replaces_stale_device_checklists_with_authoritative_model(self) -> None:
        normalize_source = function_source(self.main, "normalizeMetatraderCandidate")
        system_source = function_source(self.main, "globalMetatraderSystemModels")
        registry_source = function_source(self.main, "globalMetatraderCandidateRegistry")
        accept_source = function_source(self.main, "acceptGlobalMetatraderHubReadModel")
        load_source = function_source(self.main, "loadGlobalMetatraderHub")
        script = "\n".join([
            "const GLOBAL_METATRADER_TARGETS = [",
            "  {propId:'left_analytics_console',labelTh:'สภา AI Trade',supportedPlatforms:['MT4']},",
            "  {propId:'right_server_racks',labelTh:'โรงงานสร้าง EA',supportedPlatforms:['MT4','MT5']},",
            "  {propId:'right_tool_console',labelTh:'ห้องทดลอง EA',supportedPlatforms:['MT4','MT5']},",
            "];",
            "const candidate = {candidateId:'mtc-44444444444444444444444444444444',platform:'MT4',labelTh:'MT4 หลัก',detected:true,runningState:'platform_running_detected'};",
            "const checklist = {metatraderSelection:{candidates:[candidate],selectedCandidate:candidate,canSelect:true}};",
            "const model = {status:'configured',candidates:[candidate],platforms:{mt4:{configurationStatus:'configured',selectedCandidate:candidate,targets:GLOBAL_METATRADER_TARGETS.map((target)=>({propId:target.propId,status:'configured',selectedCandidate:candidate,adapterReady:false}))},mt5:{configurationStatus:'not_configured',selectedCandidate:null,targets:GLOBAL_METATRADER_TARGETS.slice(1).map((target)=>({propId:target.propId,status:'configured_other_platform',selectedCandidate:candidate,adapterReady:false}))}}};",
            "const state = {globalMetatraderHub:{readModel:null,status:'ready',backendAvailable:true,inFlight:false,operation:'',message:'old',tone:'success',checklists:{left_analytics_console:checklist,right_server_racks:checklist,right_tool_console:checklist},choices:{MT4:'',MT5:''},requestId:0,lastReadCount:3,lastLoadedAt:1,lastScannedAt:0}};",
            "function getMetatraderSelectionModel(value) { return value?.metatraderSelection || {candidates:[],selectedCandidate:null,canSelect:false}; }",
            "function safeDashboardDisplayText(value, fallback='') { return String(value || fallback); }",
            "function renderGlobalMetatraderHubControl() {}",
            "async function fetchJson(url) { if (url !== '/api/integrations/metatrader/global') throw new Error('wrong endpoint'); return {ok:true,globalMetatraderHub:model}; }",
            normalize_source,
            system_source,
            registry_source,
            accept_source,
            load_source,
            r'''(async () => {
  const systems = await loadGlobalMetatraderHub();
  process.stdout.write(JSON.stringify({keys:Object.keys(state.globalMetatraderHub.checklists),hasModel:state.globalMetatraderHub.readModel===model,status:state.globalMetatraderHub.status,lastReadCount:state.globalMetatraderHub.lastReadCount,message:state.globalMetatraderHub.message,tone:state.globalMetatraderHub.tone,available:systems.map((item) => [item.propId,item.available,item.configured])}));
})().catch((error) => { console.error(error); process.exit(1); });''',
        ])
        payload = self.run_node(script)
        self.assertEqual(payload["keys"], [])
        self.assertTrue(payload["hasModel"])
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["lastReadCount"], 3)
        self.assertIn("ครบทุกระบบ", payload["message"])
        self.assertEqual(payload["tone"], "success")
        self.assertEqual(
            payload["available"],
            [
                ["left_analytics_console", True, True],
                ["right_server_racks", True, True],
                ["right_tool_console", True, True],
            ],
        )

    def test_global_control_scans_and_applies_from_the_top_hub(self) -> None:
        self.assertGreaterEqual(
            self.main.count("loadGlobalMetatraderHub({ preserveMessage: true })"),
            2,
        )
        listeners = source_block(
            self.main,
            'els.globalMetatraderButton?.addEventListener("click"',
            'els.operatorModeButton?.addEventListener("click"',
        )
        self.assertIn('els.globalMetatraderScan?.addEventListener("click"', listeners)
        self.assertIn('els.globalMetatraderMt4Apply?.addEventListener("click"', listeners)
        self.assertIn('applyGlobalMetatraderTarget("MT4")', listeners)
        self.assertIn('applyGlobalMetatraderTarget("MT5")', listeners)
        self.assertIn("prepareGlobalMetatraderHubOnOpen()", listeners)
        prepare = function_source(self.main, "prepareGlobalMetatraderHubOnOpen")
        self.assertIn("await loadGlobalMetatraderHub", prepare)
        self.assertIn("lastScannedAt", prepare)
        self.assertIn("return scanGlobalMetatraderHub()", prepare)

    def test_central_hub_is_the_only_owner_of_terminal_discovery_and_selection_endpoints(self) -> None:
        scan = function_source(self.main, "scanGlobalMetatraderHub")
        apply = function_source(self.main, "applyGlobalMetatraderTarget")
        self.assertEqual(self.main.count("/api/integrations/metatrader/global/discover"), 1)
        self.assertEqual(self.main.count("/api/integrations/metatrader/global/select"), 1)
        self.assertNotIn('"/api/integrations/metatrader/discover"', self.main)
        self.assertNotIn('"/api/integrations/metatrader/select"', self.main)
        self.assertIn("/api/integrations/metatrader/global/discover", scan)
        self.assertIn("/api/integrations/metatrader/global/select", apply)

        for retired_device_action in (
            "discoverMetatraderConnections",
            "confirmMetatraderSelection",
            "confirmAiTradeMt4QuickSelection",
            "prepareAiTradeMt4Channel",
            "selectEaFactoryTerminal",
            "selectEaOptimizationLabTerminal",
        ):
            action = optional_function_source(self.main, retired_device_action)
            self.assertNotIn(
                "/api/integrations/metatrader/",
                action,
                msg=f"{retired_device_action} must not own terminal discovery/selection anymore",
            )

    def test_device_dashboard_markup_has_no_terminal_candidate_or_apply_controls(self) -> None:
        for retired_element_id in (
            "modalAiTradeMt4QuickAction",
            "modalAiTradeMt4QuickCandidates",
            "modalAiTradeMt4QuickConfirm",
            "modalDashboardDiscoverMetatrader",
            "modalDashboardMetatraderCandidates",
            "modalDashboardConfirmMetatrader",
        ):
            self.assertNotIn(f'id="{retired_element_id}"', self.index)

    def test_device_renderers_are_read_only_for_installed_terminal_selection(self) -> None:
        generic_selection = optional_function_source(self.main, "renderMetatraderSelection")
        ai_trade = optional_function_source(self.main, "renderAiTradeMt4QuickSetup")
        connection_panel = function_source(self.main, "renderDashboardConnectionPanel")
        factory = optional_function_source(self.main, "renderEaFactoryTerminalPicker")
        lab_source = function_source(self.main, "renderEaOptimizationLabSourceStage")

        for block_name, block in (
            ("generic dashboard terminal renderer", generic_selection),
            ("AI Trade terminal renderer", ai_trade),
        ):
            self.assertNotIn('input.type = "radio"', block, msg=block_name)
            self.assertNotIn("modalDashboardConfirmMetatrader", block, msg=block_name)
            self.assertNotIn("modalAiTradeMt4QuickConfirm", block, msg=block_name)
        self.assertNotIn("modalDashboardDiscoverMetatrader", connection_panel)

        self.assertNotIn('document.createElement("select")', factory)
        self.assertNotIn("selectEaFactoryTerminal(", factory)
        self.assertNotIn("ea-factory-terminal-confirm", factory)

        # The platform field describes source/build compatibility and must remain editable.
        self.assertIn('"แพลตฟอร์ม"', lab_source)
        self.assertIn('["MT4", "MT4 / MQL4"]', lab_source)
        self.assertIn('["MT5", "MT5 / MQL5"]', lab_source)
        # The concrete installed Terminal comes only from the central hub/backend selection.
        for forbidden in (
            '"Terminal ที่ตรวจพบ"',
            "filteredTerminals",
            "terminalSelect",
            "selectEaOptimizationLabTerminal(",
        ):
            self.assertNotIn(forbidden, lab_source)

    def test_device_modal_has_no_handlers_for_terminal_discovery_or_selection(self) -> None:
        listeners = source_block(
            self.main,
            'els.modalDashboardRefreshConnections?.addEventListener("click"',
            'els.modalKanbanSearch?.addEventListener("input"',
        )
        for retired_handler in (
            "modalAiTradeMt4QuickAction",
            "modalAiTradeMt4QuickConfirm",
            "modalDashboardDiscoverMetatrader",
            "modalDashboardConfirmMetatrader",
            "prepareAiTradeMt4Channel",
            "confirmAiTradeMt4QuickSelection",
            "discoverMetatraderConnections",
            "confirmMetatraderSelection",
        ):
            self.assertNotIn(retired_handler, listeners)

    def test_opening_terminal_hub_never_discards_sheet_preview_or_overlaps_busy_sheet(self) -> None:
        panel = function_source(self.main, "setGlobalMetatraderPanelOpen")
        self.assertIn("researchSheetHubPopoverIsOpen()", panel)
        self.assertIn("Boolean(state.researchSheetHub.preview)", panel)
        self.assertIn("researchSheetGoogleAuthIsBusy()", panel)
        self.assertIn("researchSheetHubQueryIsBusy()", panel)
        self.assertIn("closeResearchSheetHubPopover({ discardPreview: false, focusToggle: false })", panel)
        self.assertNotIn("discardPreview: true", panel)

    def test_snapshot_readiness_is_not_labeled_as_live_adapter_readiness(self) -> None:
        render = function_source(self.main, "renderGlobalMetatraderHubControl")
        self.assertIn("Snapshot พร้อม (อ่านอย่างเดียว)", render)
        self.assertNotIn('"Adapter พร้อม"', render)

    def test_partial_status_describes_binding_drift_not_read_failure(self) -> None:
        render = function_source(self.main, "renderGlobalMetatraderHubControl")
        self.assertIn("ตั้งค่าไม่ครบ ${configuredCount}/${totalCount} ระบบ", render)
        self.assertIn("พบ Terminal บางระบบไม่ตรงกัน", render)
        self.assertNotIn("อ่านสถานะได้ ${hub.lastReadCount}/${totalCount} ระบบ", render)

    def test_control_has_ready_partial_error_and_mobile_layout_states(self) -> None:
        for selector in (
            '.metatrader-hub-control[data-state="ready"]',
            '.metatrader-hub-control[data-state="partial"]',
            '.metatrader-hub-control[data-state="error"]',
            ".metatrader-hub-platforms",
            ".metatrader-hub-system",
            '.metatrader-hub-system[data-state="unknown"]',
        ):
            self.assertIn(selector, self.styles)
        self.assertIn("@media (max-width: 720px)", self.styles)
        self.assertIn("@media (min-width: 641px) and (max-width: 900px)", self.styles)
        self.assertIn(".topbar-research-sheet-hub .research-sheet-hub-details-toggle {\n    grid-column: auto;", self.styles)
        self.assertIn("max-height: calc(100dvh - 158px);", self.styles)
        self.assertIn("grid-template-columns: 1fr;", self.styles)


if __name__ == "__main__":
    unittest.main()
