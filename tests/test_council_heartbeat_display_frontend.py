import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from test_frontend_polling_stability import function_block

ROOT = Path(__file__).resolve().parents[1]


class CouncilHeartbeatDisplayFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "frontend/src/styles/main.css").read_text(encoding="utf-8")
        cls.node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")

    def run_js(self, body):
        script = "\n".join(re.search(rf"^const {name} = .*?;", self.main, re.M).group(0) for name in (
            "AI_TRADE_COUNCIL_PROP_ID", "AI_TRADE_HEARTBEAT_POLL_MS", "AI_TRADE_HEARTBEAT_FETCH_TIMEOUT_MS",
            "AI_TRADE_HEARTBEAT_FRESH_SECONDS", "DEFAULT_FETCH_TIMEOUT_MS", "OPEN_PROP_REPORT_POLL_TTL_MS",
        )) + r"""
const assert = require('node:assert/strict');
let clock = 100000; Date.now = () => clock;
let focused = true, renderCount = 0, timerId = 0;
const document = {visibilityState: 'visible', hasFocus: () => focused};
const timers = new Map();
const window = {
 setTimeout: (fn, ms) => {const id=++timerId; timers.set(id,{fn,due:clock+ms}); return id;},
 clearTimeout: id => timers.delete(id),
 setInterval: (fn, ms) => {const id=++timerId; timers.set(id,{fn,due:clock+ms,repeat:ms}); return id;},
 clearInterval: id => timers.delete(id),
};
async function advance(ms) {clock += ms; for (const [id,t] of [...timers]) if(t.due<=clock) {
 if(t.repeat) t.due=clock+t.repeat; else timers.delete(id); t.fn();
} for(let n=0;n<15;n++) await Promise.resolve();}
const fetches=[];
const fetch=(path,{signal})=>new Promise((resolve,reject)=>{
 fetches.push({path,signal,resolve:body=>resolve({ok:true,json:async()=>body}),reject});
 signal.addEventListener('abort',()=>reject(signal.reason),{once:true});
});
const target={propId:AI_TRADE_COUNCIL_PROP_ID,status:'configured',selectionRevision:3,
 selectedCandidate:{candidateId:'selected',platform:'mt5'}};
const state={
 globalMetatraderHub:{readModel:{activePlatform:'mt5',platforms:{mt5:{targets:[target],selectedCandidate:target.selectedCandidate}}}},
 modal:{open:true,type:'prop',id:AI_TRADE_COUNCIL_PROP_ID},
 aiTradeCouncilHeartbeat:{data:null,status:'idle',controller:null,timer:null,nextPollAt:0,failures:0},
 propReportLoadState:{},propReportLoadedAt:{left_analytics_console:clock-40000},
};
const renderOpenAiTradeCouncilRuntimeStatus=()=>{renderCount++;};
const safeDashboardDisplayText=(value,fallback='')=>value==null?fallback:String(value);
const signalCouncilModel=(report={})=>report.aiTradeCouncil||{};
const signalCouncilRunModel=()=>({});
const signalCurrentConsensusSource=()=>({current:false});
const signalExecutionGuardReasonLabel=value=>String(value);
const report={connectionChecklist:{metatraderSelection:{selectedCandidate:target.selectedCandidate},items:[]},
 aiTradeCouncil:{tradeGateway:{selectedCandidateId:'selected',selectedPlatform:'mt5',platform:'mt5',
  connected:true,observedAt:new Date(clock-40000).toISOString(),ageSeconds:40,mode:'live',
  liveOrderExecutionAvailable:true,demoOrderExecutionAvailable:true,executionGuardReady:true},
  runtimeTruth:{tradingStateAvailable:false,ensembleAvailable:false},
  platformConnections:{items:[{platform:'mt5',selected:true,candidateId:'selected',connectionState:'connected',
  observedAt:new Date(clock-40000).toISOString(),ageSeconds:40,freshForSeconds:20}]}}};
function response(overrides={}) {return {ok:true,tradeGateway:{selectedCandidateId:'selected',selectedPlatform:'mt5',
 selectionRevision:3,connected:true,observedAt:new Date(clock).toISOString(),ageSeconds:0,
 executionGuardReady:true,liveOrderExecutionAvailable:true,...overrides}};}
function fullResponse(overrides={}) {return response({mode:'shadow',status:'READY',executionGuardReason:'READY',
 liveArmed:false,liveOrderExecutionAvailable:false,demoOrderExecutionAvailable:false,
 shadowValidationAvailable:true,killSwitchActive:false,...overrides});}
"""
        start = self.main.index("class FetchTimeoutError ")
        end = self.main.index("\nfunction renderCodexRateReserve", start)
        script += self.main[start:end]
        for name in (
            "aiTradeHeartbeatSelection", "canPollAiTradeHeartbeat", "stopAiTradeHeartbeatPolling",
            "startAiTradeHeartbeatPolling", "aiTradeHeartbeatDisplayModel", "signalTradingReportPendingLabel",
            "signalCurrentInitFailureDisplay", "signalCurrentGatewayStatusDisplay",
            "signalSelectedPlatform", "signalSelectedPlatformConnectionHealth", "signalCommandMatchesCurrentRound",
            "signalConnectionItem", "signalConnectionIsReady", "getSignalRuntimeTruth",
            "signalEffectiveExecutionGuardReason", "signalExecutionGuardSummary", "signalLiveAccountStatus",
            "signalGatewayInputValidationText", "signalGatewayInitStatusMessage",
            "signalExecutionGuardRecoveryLabel", "renderSignalMarketStrip", "renderSignalRiskList",
        ):
            script += "\n" + function_block(self.main, name)
        live_panel = function_block(self.main, "renderSignalLivePanel")
        script += "\nfunction renderGatewayControlsOnly(container, runtime) {\n" + live_panel[live_panel.index("  const gatewayAction ="):]
        script += "\nasync " + function_block(self.main, "pollAiTradeHeartbeat")
        script += "\n(async()=>{\n" + body + "\nprocess.stdout.write(JSON.stringify({ok:true}));\n})().catch(e=>{console.error(e);process.exit(1)});"
        result = subprocess.run([self.node, "-"], input=script, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True})

    def test_fresh_display_does_not_change_report_or_grant_analysis_and_orders(self):
        self.run_js(r"""
const before=structuredClone(report), runtimeBefore=getSignalRuntimeTruth(report);
const pending=pollAiTradeHeartbeat();
await pollAiTradeHeartbeat(); assert.equal(fetches.length,1);
fetches[0].resolve(response()); await pending;
assert.equal(fetches[0].path,'/api/mt4-trade-gateway/status');
assert.equal(aiTradeHeartbeatDisplayModel().state,'connected');
assert.equal(aiTradeHeartbeatDisplayModel().executionGuardReady,false);
assert.deepEqual(report,before);
const after=getSignalRuntimeTruth(report); assert.deepEqual(after,runtimeBefore);
for(const key of ['gatewayConnected','orderSubmissionAvailable','liveOrderExecutionAvailable',
 'demoOrderExecutionAvailable','gatewayExecutionGuardReady','tradingStateAvailable','ensembleAvailable']) assert.equal(after[key],false,key);
assert.match(signalExecutionGuardSummary(after),/รอรายงานสถานะการเทรด/);
assert.match(signalLiveAccountStatus(after,{}),/รอรายงานสถานะการเทรด/);
assert.equal(signalTradingReportPendingLabel({selectedConnectionHealth:{reasonCode:'terminal_broker_not_connected'}}),'');
await advance(20001); assert.equal(aiTradeHeartbeatDisplayModel().state,'waiting');
assert.equal(aiTradeHeartbeatDisplayModel().reasonCode,'gateway_status_stale');
""")

    def test_wrong_candidate_revision_platform_or_changed_selection_is_rejected(self):
        self.run_js(r"""
for(const overrides of [{selectedCandidateId:'other'},{selectionRevision:2},{selectionRevision:'3'},
 {selectedPlatform:'mt4'},{observedAt:'invalid'}]) {
 state.aiTradeCouncilHeartbeat.nextPollAt=0;
 const pending=pollAiTradeHeartbeat(); fetches.at(-1).resolve(response(overrides)); await pending;
 assert.equal(aiTradeHeartbeatDisplayModel().state,'waiting');
}
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const pending=pollAiTradeHeartbeat(); target.selectionRevision=4;
fetches.at(-1).resolve(response()); await pending;
assert.equal(state.aiTradeCouncilHeartbeat.data,null);
assert.equal(aiTradeHeartbeatDisplayModel().state,'waiting');
target.status='not_configured'; assert.equal(aiTradeHeartbeatDisplayModel(),null);
""")

    def test_current_full_status_is_separate_from_expired_report_and_order_authority(self):
        self.run_js(r"""
const before=structuredClone(report), runtimeBefore=getSignalRuntimeTruth(report);
const pending=pollAiTradeHeartbeat(); fetches[0].resolve(fullResponse()); await pending;
const runtime=getSignalRuntimeTruth(report);
assert.deepEqual(runtime,runtimeBefore); assert.deepEqual(report,before);
assert.match(signalCurrentGatewayStatusDisplay(runtime).status,/READY/);
assert.match(signalExecutionGuardSummary(runtime),/Execution Guard พร้อมตรวจคำสั่ง.*SHADOW ไม่ส่ง Order/);
assert.match(signalLiveAccountStatus(runtime,{}),/รอรายงานสถานะการเทรด/);
for(const key of ['gatewayConnected','orderSubmissionAvailable','liveOrderExecutionAvailable',
 'demoOrderExecutionAvailable','gatewayExecutionGuardReady','tradingStateAvailable','ensembleAvailable']) assert.equal(runtime[key],false,key);
globalThis.signalGatewaySizingSummary=()=>({value:'fixed lot'});
globalThis.signalGatewayAckSizingSummary=()=>'';
globalThis.signalGatewayModeAccountStatus=()=>({observed:false,mismatch:false});
globalThis.signalMarketModel=()=>({freshnessMinutes:null,spread:null});
globalThis.signalSigningKeyCopyState=()=>({ready:false,label:'รอ Key',copyValue:''});
globalThis.displayStatus=value=>String(value);
const node=()=>({children:[],dataset:{},append(...children){this.children.push(...children);},
 appendChild(child){this.children.push(child);},setAttribute(){},addEventListener(){}});
document.createElement=node;
const strip=node(); renderSignalMarketStrip(strip,report,runtime);
const metrics=Object.fromEntries(strip.children.map(item=>item.children.map(child=>child.textContent)));
assert.match(metrics['สถานะ Gateway'],/READY/); assert.match(metrics['โหมด Gateway'],/SHADOW/);
assert.match(metrics['สิทธิ์ส่ง Order'],/รอรายงานสถานะการเทรด/);
const risk=node(); renderSignalRiskList(risk,runtime);
const guardRow=risk.children.find(row=>row.children[1].textContent==='Execution Guard ของ EA');
assert.match(guardRow.children[2].textContent,/สถานะ EA ล่าสุด: Execution Guard พร้อม/);
assert.equal(guardRow.dataset.ready,'false');
const action={disabled:true,dataset:{}},detail={};
renderGatewayControlsOnly({querySelector:s=>s==='[data-signal-gateway-action]'?action:detail},runtime);
assert.match(action.textContent,/SHADOW ไม่ส่ง Order/);
assert.equal(action.disabled,true); assert.equal(action.dataset.ready,'false');
// Even a full current LIVE observation cannot enable stale report actions.
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const live=pollAiTradeHeartbeat(); fetches.at(-1).resolve(fullResponse({mode:'live',liveArmed:true,liveOrderExecutionAvailable:true})); await live;
renderGatewayControlsOnly({querySelector:s=>s==='[data-signal-gateway-action]'?action:detail},runtime);
assert.match(action.textContent,/สิทธิ์ส่ง Order ตรวจจากรอบวิเคราะห์ใหม่/);
assert.equal(action.dataset.ready,'false'); assert.equal(action.disabled,true);
assert.deepEqual(getSignalRuntimeTruth(report),runtimeBefore);
""")

    def test_current_status_requires_full_shape_exact_binding_and_fresh_observation(self):
        self.run_js(r"""
const runtime=getSignalRuntimeTruth(report);
for(const overrides of [{observedAt:new Date(clock-20001).toISOString()}, {ageSeconds:20.001},
 {ageSeconds:'0'}, {ageSeconds:null}, {ageSeconds:-1}, {observedAt:'invalid'},
 {observedAt:new Date(clock+1000).toISOString()}, {mode:'unknown'}, {executionGuardReady:'true'},
 {killSwitchActive:null}, {status:''}, {selectedCandidateId:'other'}, {selectedPlatform:'mt4'}, {selectionRevision:2}]) {
 state.aiTradeCouncilHeartbeat.nextPollAt=0;
 const p=pollAiTradeHeartbeat(); fetches.at(-1).resolve(fullResponse(overrides)); await p;
 assert.doesNotMatch(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
}
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const partial=pollAiTradeHeartbeat(); fetches.at(-1).resolve(response()); await partial;
assert.doesNotMatch(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const p=pollAiTradeHeartbeat(); fetches.at(-1).resolve(fullResponse()); await p;
assert.doesNotMatch(signalExecutionGuardSummary({...runtime,selectedCandidateId:'old'}),/Execution Guard พร้อม/);
assert.doesNotMatch(signalExecutionGuardSummary({...runtime,selectedPlatform:'MT4'}),/Execution Guard พร้อม/);
await advance(20000); assert.match(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
await advance(1); assert.doesNotMatch(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
// Renewed receipt cannot make an old EA observation fresh.
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const old=pollAiTradeHeartbeat(); fetches.at(-1).resolve(fullResponse({observedAt:new Date(clock-21000).toISOString(),ageSeconds:0})); await old;
assert.doesNotMatch(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
""")

    def test_new_error_disconnection_and_selection_race_never_resurrect_ready(self):
        self.run_js(r"""
const runtime={...getSignalRuntimeTruth(report),gatewayConnected:true,gatewayMode:'live',gatewayExecutionGuardReady:true};
for(const overrides of [{}, {connected:false,status:'DISCONNECTED'},
 {executionGuardReady:false,executionGuardReason:'RISK_LIMIT'}, {killSwitchActive:true}]) {
 state.aiTradeCouncilHeartbeat.nextPollAt=0;
 const p=pollAiTradeHeartbeat(); fetches.at(-1).resolve(fullResponse(overrides)); await p;
 const text=signalExecutionGuardSummary(runtime);
 if(!Object.keys(overrides).length) assert.match(text,/Execution Guard พร้อม/);
 else assert.doesNotMatch(text,/Execution Guard พร้อม/);
}
const init={available:true,severity:'error',reasonCode:'LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST',
 observedAt:new Date(clock).toISOString(),ageSeconds:0,stale:false,supersededByLiveStatus:false,eaAttached:true,runtimeReady:false};
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const blocked=pollAiTradeHeartbeat(); fetches.at(-1).resolve(fullResponse({initStatus:init})); await blocked;
assert.match(signalExecutionGuardSummary(runtime),/LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST/);
assert.doesNotMatch(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const failed=pollAiTradeHeartbeat(); fetches.at(-1).reject(new Error('offline')); await failed;
assert.doesNotMatch(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
assert.equal(state.aiTradeCouncilHeartbeat.data,null);
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const race=pollAiTradeHeartbeat(); target.selectionRevision=4;
fetches.at(-1).resolve(fullResponse()); await race;
assert.doesNotMatch(signalExecutionGuardSummary(runtime),/Execution Guard พร้อม/);
assert.equal(state.aiTradeCouncilHeartbeat.data,null);
assert.equal(runtime.gatewayExecutionGuardReady,true); // Display never rewrites report authority.
stopAiTradeHeartbeatPolling(); assert.equal(signalCurrentGatewayStatusDisplay(runtime),null);
""")

    def test_timeout_failure_and_backoff_never_reuse_green(self):
        self.run_js(r"""
const good=pollAiTradeHeartbeat(); fetches[0].resolve(response()); await good;
await advance(5000);
const timed=pollAiTradeHeartbeat(); await advance(5000); await timed;
assert.equal(fetches[1].signal.aborted,true);
assert.equal(fetches[1].signal.reason.timeoutMs,5000);
assert.equal(state.aiTradeCouncilHeartbeat.data,null);
assert.equal(aiTradeHeartbeatDisplayModel().state,'waiting');
await pollAiTradeHeartbeat(); assert.equal(fetches.length,2);
for(let n=0;n<4;n++) {
 await advance(30000); const p=pollAiTradeHeartbeat(); fetches.at(-1).reject(new Error('offline')); await p;
 assert.ok(state.aiTradeCouncilHeartbeat.nextPollAt-clock<=30000);
}
""")

    def test_hide_blur_close_abort_and_single_flight_lifecycle(self):
        self.run_js(r"""
focused=false; startAiTradeHeartbeatPolling(); await pollAiTradeHeartbeat(); assert.equal(fetches.length,0);
focused=true; document.visibilityState='hidden'; startAiTradeHeartbeatPolling(); assert.equal(fetches.length,0);
document.visibilityState='visible'; state.modal.open=false; startAiTradeHeartbeatPolling(); assert.equal(fetches.length,0);
state.modal.open=true; startAiTradeHeartbeatPolling(); startAiTradeHeartbeatPolling();
assert.equal(fetches.length,1); assert.equal([...timers.values()].filter(t=>t.repeat).length,1);
focused=false; stopAiTradeHeartbeatPolling(); await advance(0);
assert.equal(fetches[0].signal.aborted,true); assert.equal(state.aiTradeCouncilHeartbeat.data,null);
assert.equal(state.aiTradeCouncilHeartbeat.timer,null); assert.equal(aiTradeHeartbeatDisplayModel(),null);
focused=true; startAiTradeHeartbeatPolling(); assert.equal(fetches.length,2);
stopAiTradeHeartbeatPolling(); await advance(0);
""")

    def test_lifecycle_and_render_consumers_are_display_only(self):
        self.assertIn('window.addEventListener("blur", stopAiTradeHeartbeatPolling)', self.main)
        for name in ("stopAutomaticPolling", "closeGameModal"):
            self.assertIn("stopAiTradeHeartbeatPolling()", function_block(self.main, name))
        self.assertIn("stopAiTradeHeartbeatPolling()", function_block(self.main, "openGameModal"))
        self.assertIn("aiTradeHeartbeatDisplayModel()", function_block(self.main, "aiTradePlatformConnectionModels"))
        for name in ("signalSelectedPlatformConnectionHealth", "getSignalRuntimeTruth", "signalCurrentConsensusSource"):
            self.assertNotIn("aiTradeHeartbeat", function_block(self.main, name))

    def test_current_init_failure_overrides_old_fresh_heartbeat_without_authority(self):
        self.run_js(r"""
const init={available:true,severity:'error',stage:'money_management',reasonCode:'LIVE_COMMISSION_POLICY_UNCONFIRMED',
 observedAt:new Date(clock-60000).toISOString(),ageSeconds:60,stale:false,supersededByLiveStatus:false,
 eaAttached:true,runtimeReady:false};
const pending=pollAiTradeHeartbeat(); fetches[0].resolve(response({initStatus:init})); await pending;
const model=aiTradeHeartbeatDisplayModel();
assert.equal(model.state,'error'); assert.equal(model.executionGuardReady,false);
assert.equal(model.reasonCode,'LIVE_COMMISSION_POLICY_UNCONFIRMED');
assert.match(model.messageTh,/EA ยังอยู่บนกราฟ/); assert.match(model.messageTh,/ไม่ส่งคำสั่งเทรด/);
assert.match(model.messageTh,/ค่าคอมมิชชัน/); assert.match(model.messageTh,/LIVE_COMMISSION_POLICY_UNCONFIRMED/);
assert.equal(getSignalRuntimeTruth(report).orderSubmissionAvailable,false);
await advance(20001); assert.notEqual(aiTradeHeartbeatDisplayModel().state,'error');
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const recovered=pollAiTradeHeartbeat();
fetches[1].resolve(response({initStatus:{...init,supersededByLiveStatus:true}})); await recovered;
assert.equal(aiTradeHeartbeatDisplayModel().state,'connected');
assert.equal(signalGatewayInitStatusMessage({...init,supersededByLiveStatus:true}),null);
for(const [reason,fragment] of [['LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST','AllowedSymbols'],
 ['MT5_HEDGING_ACCOUNT_REQUIRED','Hedging'],['LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE','ถือสิทธิ์'],
 ['LIVE_SIGNING_KEY_PIN_REQUIRED','Key ID']]) {
 const diagnostic=signalGatewayInitStatusMessage({...init,eaAttached:false,reasonCode:reason});
 assert.match(diagnostic.text,/เริ่มทำงานไม่สำเร็จ/); assert.ok(diagnostic.text.includes(fragment));
 assert.ok(diagnostic.text.includes(reason));
}
""")

    def test_blocked_init_is_shown_across_overview_risk_and_controls_without_granting_readiness(self):
        self.run_js(r"""
const init={available:true,severity:'error',reasonCode:'LIVE_COMMISSION_POLICY_UNCONFIRMED',
 observedAt:new Date(clock).toISOString(),ageSeconds:0,stale:false,supersededByLiveStatus:false,
 eaAttached:true,runtimeReady:false};
const pending=pollAiTradeHeartbeat();
fetches[0].resolve(response({connected:false,observedAt:null,ageSeconds:null,initStatus:init})); await pending;
const runtime=getSignalRuntimeTruth(report), before=structuredClone(runtime);
runtime.gatewayExecutionGuardReason='TERMINAL_NOT_CONNECTED';
const expected=structuredClone(runtime);
const node=()=>({children:[],dataset:{},attributes:{},append(...children){this.children.push(...children);},
 appendChild(child){this.children.push(child);},setAttribute(key,value){this.attributes[key]=value;},addEventListener(){}});
document.createElement=node;
globalThis.signalMarketModel=()=>({freshnessMinutes:null,spread:null});
globalThis.signalGatewayModeAccountStatus=()=>({observed:false,mismatch:false});
globalThis.signalGatewaySizingSummary=()=>({label:'Money Management',value:'รอข้อมูลจาก EA',tone:'muted'});
globalThis.signalSigningKeyCopyState=()=>({ready:false,label:'รอ Key',copyValue:''});
globalThis.signalGatewayAckSizingSummary=()=>'';
globalThis.displayStatus=value=>String(value);
const strip=node(); renderSignalMarketStrip(strip,report,runtime);
const banner=strip.children[0];
assert.equal(banner.className,'signal-market-init-diagnostic');
assert.equal(banner.attributes.role,'alert'); assert.equal(banner.attributes['aria-atomic'],'true');
assert.match(banner.textContent,/EA ยังอยู่บนกราฟ/);
assert.match(banner.textContent,/LIVE_COMMISSION_POLICY_UNCONFIRMED/);
assert.match(banner.textContent,/\nวิธีแก้:.*EstimatedCommissionPerLot/);
const metrics=Object.fromEntries(strip.children.filter(item=>item.className==='signal-market-stat').map(item=>item.children.map(child=>child.textContent)));
for(const key of ['สถานะ Gateway','สิทธิ์ส่ง Order','โหมด Gateway']) {
 assert.match(metrics[key],/LIVE_COMMISSION_POLICY_UNCONFIRMED/);
 assert.doesNotMatch(metrics[key],/ยังไม่เชื่อม EA|TERMINAL_NOT_CONNECTED|Broker/);
}
const risk=node(); renderSignalRiskList(risk,runtime);
const rows=Object.fromEntries(risk.children.map(row=>[row.children[1].textContent,row]));
for(const key of ['MetafxHQ AI Council EA','Execution Guard ของ EA','บัญชีจริง']) {
 assert.equal(rows[key].dataset.ready,'false');
 assert.match(rows[key].children[2].textContent,/LIVE_COMMISSION_POLICY_UNCONFIRMED/);
 assert.doesNotMatch(rows[key].children[2].textContent,/ใส่ Channel|ยังไม่เชื่อม EA|Broker/);
}
assert.match(rows['Execution Guard ของ EA'].children[2].textContent,/EstimatedCommissionPerLot/);
const action={disabled:true,dataset:{}}, detail={};
renderGatewayControlsOnly({querySelector:s=>s==='[data-signal-gateway-action]'?action:detail},runtime);
assert.equal(action.disabled,true); assert.equal(action.dataset.ready,'false');
assert.match(action.textContent,/EA ถูกบล็อก/); assert.match(detail.textContent,/ค่าคอมมิชชัน/);
assert.doesNotMatch(detail.textContent,/ใส่ Channel|ยังไม่เชื่อม EA|Broker/);
assert.deepEqual(runtime,expected);
for(const key of ['gatewayConnected','orderSubmissionAvailable','liveOrderExecutionAvailable',
 'demoOrderExecutionAvailable','gatewayExecutionGuardReady','tradingStateAvailable','ensembleAvailable']) assert.equal(runtime[key],false,key);
assert.equal(before.gatewayConnected,false);
// A slower report may still contain the previous READY observation. The newer
// diagnostic must suppress only its visual green state, without rewriting it.
const oldReady={...runtime,gatewayConnected:true,gatewayMode:'live',gatewayExecutionGuardReady:true,
 liveOrderExecutionAvailable:true,orderSubmissionAvailable:true};
const oldReadyBefore=structuredClone(oldReady);
const oldStrip=node(); renderSignalMarketStrip(oldStrip,report,oldReady);
for(const item of oldStrip.children.filter(item=>item.className==='signal-market-stat' && ['สถานะ Gateway','สิทธิ์ส่ง Order','โหมด Gateway'].includes(item.children[0].textContent))) {
 assert.equal(item.dataset.tone,'error');
 assert.match(item.children[1].textContent,/LIVE_COMMISSION_POLICY_UNCONFIRMED/);
}
const oldRisk=node(); renderSignalRiskList(oldRisk,oldReady);
for(const row of oldRisk.children.filter(row=>['MetafxHQ AI Council EA','Execution Guard ของ EA','บัญชีจริง'].includes(row.children[1].textContent)))
 assert.equal(row.dataset.ready,'false');
renderGatewayControlsOnly({querySelector:s=>s==='[data-signal-gateway-action]'?action:detail},oldReady);
assert.equal(action.dataset.ready,'false'); assert.equal(action.disabled,true);
assert.deepEqual(oldReady,oldReadyBefore);
await advance(20001);
const expiredStrip=node(); renderSignalMarketStrip(expiredStrip,report,runtime);
assert.ok(expiredStrip.children.every(item=>item.className==='signal-market-stat'));
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const recovered=pollAiTradeHeartbeat();
fetches.at(-1).resolve(response({initStatus:{...init,supersededByLiveStatus:true}})); await recovered;
const recoveredStrip=node(); renderSignalMarketStrip(recoveredStrip,report,runtime);
assert.ok(recoveredStrip.children.every(item=>item.className==='signal-market-stat'));
""")

    def test_init_banner_spans_metrics_and_wraps_without_ellipsis(self):
        rule = re.search(r"\.signal-market-strip \.signal-market-init-diagnostic\s*\{([^}]+)\}", self.styles).group(1)
        for declaration in ("grid-column: 1 / -1", "white-space: pre-line", "overflow: visible", "overflow-wrap: anywhere", "text-overflow: clip"):
            self.assertIn(declaration, rule)
        self.assertNotIn("ellipsis", rule)

    def test_overview_init_diagnostic_rejects_stale_superseded_and_other_selection(self):
        self.run_js(r"""
const init={available:true,severity:'error',reasonCode:'LIVE_COMMISSION_POLICY_UNCONFIRMED',
 observedAt:new Date(clock).toISOString(),ageSeconds:0,stale:false,supersededByLiveStatus:false,
 eaAttached:true,runtimeReady:false};
const runtime={selectedPlatform:'MT5',selectedCandidateId:'selected',gatewayConnected:false};
for(const override of [{},{stale:true},{supersededByLiveStatus:true}]) {
 state.aiTradeCouncilHeartbeat.nextPollAt=0;
 const p=pollAiTradeHeartbeat(); fetches.at(-1).resolve(response({initStatus:{...init,...override}})); await p;
 assert.equal(Boolean(signalCurrentInitFailureDisplay(runtime)),Object.keys(override).length===0);
}
state.aiTradeCouncilHeartbeat.nextPollAt=0;
const p=pollAiTradeHeartbeat(); fetches.at(-1).resolve(response({initStatus:init})); await p;
assert.equal(signalCurrentInitFailureDisplay({...runtime,selectedCandidateId:'old'}),null);
assert.equal(signalCurrentInitFailureDisplay({...runtime,selectedPlatform:'MT4'}),null);
target.selectionRevision=4; assert.equal(signalCurrentInitFailureDisplay(runtime),null);
target.selectionRevision=3; assert.ok(signalCurrentInitFailureDisplay(runtime));
await advance(20001); assert.equal(signalCurrentInitFailureDisplay(runtime),null);
assert.doesNotMatch(signalExecutionGuardSummary(runtime),/LIVE_COMMISSION_POLICY_UNCONFIRMED/);
stopAiTradeHeartbeatPolling(); assert.equal(signalCurrentInitFailureDisplay(runtime),null);
""")


if __name__ == "__main__":
    unittest.main()
