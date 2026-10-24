"""Pure JS regression probes: no backend import, real browser, network or MT5."""
import shutil
import subprocess
import unittest
from pathlib import Path

from test_frontend_polling_stability import function_block


ROOT = Path(__file__).resolve().parents[1]


class CouncilFrontendAuditFixesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        cls.node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")

    def run_js(self, body):
        script = r"""
const assert=require('node:assert/strict');
const safeDashboardDisplayText=(v,f='')=>v==null?f:String(v);
const clamp=(v,l,h)=>Math.max(l,Math.min(h,v));
const firstFiniteSignalNumber=(...values)=>values.find(v=>typeof v==='number' && Number.isFinite(v))??null;
const formatThaiDateTime=v=>v;
const getSafeExternalHttpUrl=v=>typeof v==='string' && /^https?:\/\//.test(v)?v:null;
class Node {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.className='';this.ownText='';}
 append(...nodes){this.children.push(...nodes);}
 appendChild(node){this.children.push(node);return node;}
 set textContent(v){this.ownText=String(v);this.children=[];}
 get textContent(){return [this.ownText,...this.children.map(n=>n.textContent)].filter(Boolean).join(' ');}
}
const document={createElement:tag=>new Node(tag)};
const createSignalDeepEmptyState=(title,detail)=>{const n=new Node('empty');n.textContent=title+' '+detail;return n;};
const els={signalConsensusNewsContent:new Node('root')};
let news={};
const renderSignalDeepShell=()=>({body:els.signalConsensusNewsContent,data:{available:true,news}});
const allNodes=n=>[n,...n.children.flatMap(allNodes)];
const render=()=>{els.signalConsensusNewsContent.children=[];renderSignalNewsContextPanel();return els.signalConsensusNewsContent;};
"""
        for name in (
            "signalDeepNewsHorizon", "signalDeepDirection", "signalDeepEvidenceItems", "appendSignalDeepEvidenceList",
            "renderSignalNewsHorizonCard", "renderSignalLatestNewsVote", "renderSignalNewsContextPanel",
            "signalGatewayInputValidationText", "signalGatewayInitStatusMessage",
        ):
            script += "\n" + function_block(self.main, name)
        result = subprocess.run([self.node, "-"], input=script+"\n"+body, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_canonical_news_observations_and_evidence_render_once_without_empty_horizons(self):
        self.run_js(r"""
news={available:true,decision:'HOLD',confidence:82,usableForCurrentSnapshot:false,
 observations:['ระยะสั้น: first view','ระยะกลาง: second view','ระยะยาว: third view'],
 evidence:[{label:'source evidence',sourceUrl:'https://example.org/news',observedAt:'2026-10-22T00:00:00Z'}]};
const before=JSON.stringify(news),root=render(),nodes=allNodes(root);
assert.equal(nodes.filter(n=>n.className==='signal-deep-news-grid').length,0);
for(const text of [...news.observations,'source evidence']) assert.equal(root.textContent.split(text).length-1,1);
assert.match(root.textContent,/Snapshot อื่น.*บริบทเท่านั้น/);
assert.doesNotMatch(root.textContent,/ยังไม่มีข่าวระยะ/);
assert.equal(JSON.stringify(news),before);
""")

    def test_legacy_structured_horizons_are_preserved_and_missing_cards_are_not_invented(self):
        self.run_js(r"""
news={available:true,horizons:{short:{summary:'short supplied',direction:'BUY',confidence:75},long:{summary:'long supplied'}}};
let root=render(),nodes=allNodes(root);
assert.equal(nodes.filter(n=>n.className==='signal-deep-news-card').length,2);
assert.match(root.textContent,/short supplied.*long supplied/);
assert.doesNotMatch(root.textContent,/ระยะกลาง|ยังไม่มีข่าว/);
news={available:true,shortTerm:'short legacy',medium_term:{summary:'medium legacy'},long:[{summary:'long legacy'}]};
root=render();
assert.equal(allNodes(root).filter(n=>n.className==='signal-deep-news-card').length,3);
assert.match(root.textContent,/short legacy.*medium legacy.*long legacy/);
news={available:true,decision:'HOLD',observations:['legacy latest'],sources:[{label:'legacy source',url:'https://example.org/source'}]};
root=render();
assert.equal(root.textContent.split('legacy source').length-1,1);
""")

    def test_unavailable_news_keeps_truthful_empty_state_and_no_fabricated_vote(self):
        self.run_js(r"""
news={available:false,reasonCode:'news_vote_unavailable',horizons:{short:[],medium:[],long:[]}};
const root=render();
assert.match(root.textContent,/ยังไม่มีผลข่าวที่ใช้กับ Snapshot นี้/);
assert.doesNotMatch(root.textContent,/BUY|SELL|Confidence/);
assert.equal(allNodes(root).filter(n=>n.className==='signal-deep-news-grid').length,0);
""")

    def test_init_diagnostic_displays_actual_input_bounds_without_changing_authority(self):
        self.run_js(r"""
const inputValidation={field:'MaxSnapshotAgeSeconds',value:1000,minimum:5,maximum:900,
 minimumInclusive:true,maximumInclusive:true,constraint:'range'};
const init={available:true,severity:'error',reasonCode:'GATEWAY_INPUT_CONFIGURATION_INVALID',
 eaAttached:true,runtimeReady:false,inputValidation};
const before=JSON.stringify(init),message=signalGatewayInitStatusMessage(init);
assert.match(message.text,/MaxSnapshotAgeSeconds = 1000.*≥ 5.*≤ 900/);
assert.match(message.text,/ไม่ส่งคำสั่งเทรด/);assert.equal(message.tone,'error');
assert.equal(JSON.stringify(init),before);
assert.equal(signalGatewayInitStatusMessage({...init,supersededByLiveStatus:true}),null);
assert.match(signalGatewayInitStatusMessage({...init,stale:true}).text,/ข้อมูลนี้เก่า/);
assert.match(signalGatewayInputValidationText({...inputValidation,field:'FixedLot',constraint:'at_most_MaxManagedTotalLots',minimum:0,minimumInclusive:false,maximum:0.1}),/> 0.*≤ 0.1 \(MaxManagedTotalLots\)/);
assert.match(signalGatewayInputValidationText({...inputValidation,field:'RequireHeartbeat',constraint:'required_for_execution',value:0}),/ต้องเปิดใช้งาน/);
assert.match(signalGatewayInputValidationText({...inputValidation,value:null}),/ค่าตัวเลขไม่ถูกต้อง/);
""")

    def test_malformed_or_secret_input_fields_never_enter_diagnostic_text(self):
        self.run_js(r"""
const valid={field:'MaxSnapshotAgeSeconds',value:1000,minimum:5,maximum:900,minimumInclusive:true,maximumInclusive:true,constraint:'range'};
for(const changes of [{field:'secret'}, {value:'sensitive'}, {value:Infinity}, {minimum:false},
 {maximum:undefined}, {minimumInclusive:'true'}, {minimum:901}, {constraint:'unknown'}, {field:'FixedLot'}]) {
 assert.equal(signalGatewayInputValidationText({...valid,...changes}),'');
}
const message=signalGatewayInitStatusMessage({available:true,severity:'error',reasonCode:'GATEWAY_INPUT_CONFIGURATION_INVALID',
 inputValidation:{...valid,field:'secret',value:'sensitive'}});
assert.doesNotMatch(message.text,/secret|sensitive/);
assert.match(message.text,/ค่าตั้งต้นของ EA/);
""")

    def test_pending_counts_are_reported_without_promising_historical_analysis(self):
        automation = function_block(self.main, "signalCouncilAutomationModel")
        daily = function_block(self.main, "renderSignalDailyPanel")
        start = daily.index("  const automationQueueMessage =")
        end = daily.index("\n  const automationMessage =", start)
        self.run_js(automation + r"""
const state={codexRate:{},aiTradeCouncilOrderLimit:{}};
const signalCouncilModel=report=>report.aiTradeCouncil||{};
const normalizeSignalAnalysisBars=v=>v||500;
const normalizeSignalMaxManagedOrders=v=>v||1;
const formatBrokerBarTime=v=>String(v);
function queueText(automation) {
""" + daily[start:end] + r"""
 return automationQueueMessage;
}
const report={aiTradeCouncil:{autoAnalysis:{config:{enabled:true},state:{pendingCount:512,
 pendingTotalCount:513,deferredPendingCount:1,pending:{closedBarTime:123,queuePosition:1,queueDepth:512}}}}};
const before=JSON.stringify(report),model=signalCouncilAutomationModel(report),text=queueText(model);
assert.equal(model.pendingCount,512);assert.equal(model.pendingTotalCount,513);assert.equal(model.deferredPendingCount,1);
assert.match(text,/Backend รายงานงานรอ 513 แท่ง.*เวลาแท่ง 123/);
assert.match(text,/เริ่มได้เฉพาะแท่งปิดใหม่.*คิวเก่าจะถูกข้าม/);
assert.doesNotMatch(text,/เก็บแท่งย้อนหลังไว้|วิเคราะห์ประวัติ|รอพื้นที่คิว/);assert.equal(JSON.stringify(report),before);
delete report.aiTradeCouncil.autoAnalysis.state.pendingTotalCount;
delete report.aiTradeCouncil.autoAnalysis.state.deferredPendingCount;
const legacy=signalCouncilAutomationModel(report);
assert.equal(legacy.pendingTotalCount,512);assert.equal(legacy.deferredPendingCount,0);
assert.match(queueText(legacy),/Backend รายงานงานรอ 512 แท่ง/);
assert.doesNotMatch(queueText(legacy),/รอพื้นที่คิว/);
""")

    def test_skipped_bar_does_not_appear_pending_when_quota_recovers_mid_bar(self):
        self.run_js(function_block(self.main, "signalCouncilAutomationModel") + r"""
const state={codexRate:{},aiTradeCouncilOrderLimit:{}};
const signalCouncilModel=report=>report.aiTradeCouncil||{};
const normalizeSignalAnalysisBars=v=>v||120;
const normalizeSignalMaxManagedOrders=v=>v||1;
const runtime={status:'watching',reasonCode:'new_bar_only_wait_next_bar',pendingCount:0,pendingTotalCount:0,
 lastObservedClosedBarTime:200,lastAnalyzedClosedBarTime:100,coverageCursorClosedBarTime:200};
const report={aiTradeCouncil:{autoAnalysis:{config:{enabled:true},state:runtime}}};
const before=JSON.stringify(report),model=signalCouncilAutomationModel(report);
assert.equal(model.newBarPending,false);
assert.match(model.statusLabel,/รอแท่งปิดใหม่.*โควตากลับมาระหว่างแท่งจะไม่เริ่มย้อนหลัง/);
assert.equal(JSON.stringify(report),before);
runtime.reasonCode='waiting_for_new_closed_bar';
assert.equal(signalCouncilAutomationModel(report).newBarPending,false);
runtime.pendingCount=1;runtime.pendingTotalCount=1;runtime.status='pending_settle';runtime.reasonCode='settle_window';
assert.equal(signalCouncilAutomationModel(report).newBarPending,true);
assert.match(signalCouncilAutomationModel(report).statusLabel,/Snapshot.*นิ่ง/);
report.aiTradeCouncil.autoAnalysis.config.enabled=false;
assert.equal(signalCouncilAutomationModel(report).newBarPending,false);
""")

    def test_quota_and_expired_labels_explain_skips_without_a_backfill_promise(self):
        self.run_js(function_block(self.main, "signalCouncilAutomationModel") + r"""
const state={codexRate:{},aiTradeCouncilOrderLimit:{}};
const signalCouncilModel=report=>report.aiTradeCouncil||{};
const normalizeSignalAnalysisBars=v=>v||120;
const normalizeSignalMaxManagedOrders=v=>v||1;
for(const reasonCode of ['quota_limit_reached','quota_below_reserve',
 'analysis_snapshot_expired_before_start','analysis_snapshot_time_invalid_before_start',
 'new_bar_only_backlog_cancelled','new_bar_only_trigger_not_admitted','new_bar_only_trigger_window_expired',
 'new_bar_only_missed_trigger','new_bar_only_restart_baseline','new_bar_only_stream_change_baseline']) {
 const model=signalCouncilAutomationModel({aiTradeCouncil:{autoAnalysis:{config:{enabled:true},
  state:{status:'skipped',reasonCode,pendingCount:0,lastObservedClosedBarTime:200,lastAnalyzedClosedBarTime:100}}}});
 assert.equal(model.newBarPending,false,reasonCode);
 assert.match(model.statusLabel,/ข้าม/,reasonCode);
 assert.doesNotMatch(model.statusLabel,/บันทึกเข้าคิว|คิวถาวร|วิเคราะห์เก็บประวัติ/,reasonCode);
}
""")


if __name__ == "__main__":
    unittest.main()
