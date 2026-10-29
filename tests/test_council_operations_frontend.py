"""Isolated Node DOM/GET fixtures; no Bridge import, provider, MT5 or live browser."""
import shutil
import subprocess
import unittest
from pathlib import Path

from test_frontend_polling_stability import function_block


ROOT = Path(__file__).resolve().parents[1]


class CouncilOperationsFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        cls.node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")

    def run_js(self, body):
        script = r"""
const assert = require('node:assert/strict');
const AI_TRADE_COUNCIL_PROP_ID='council';
const AI_TRADE_COUNCIL_OPERATIONS_ENDPOINT='/api/ai-trade-council/operations';
const AI_TRADE_COUNCIL_DIAGNOSTICS_ENDPOINT='/api/ai-trade-council/diagnostics';
const SIGNAL_HISTORY_VIEW_TABS=['orders','analysis','operations'];
const safeDashboardDisplayText=(v,f='')=>v==null || v===''?f:String(v);
const allNodes=n=>[n,...n.children.flatMap(allNodes)];
class Node {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.attrs={};this.handlers={};this.ownText='';this.disabled=false;}
 append(...nodes){nodes.forEach(n=>{n.parent=this;this.children.push(n);});}
 appendChild(n){this.append(n);return n;}
 replaceChildren(...nodes){this.children=[];this.append(...nodes);}
 set textContent(v){this.ownText=String(v);this.children=[];}
 get textContent(){return [this.ownText,...this.children.map(n=>n.textContent)].join(' ');}
 set innerHTML(v){throw Error('Operations must not interpolate HTML');}
 setAttribute(k,v){this.attrs[k]=String(v);}
 addEventListener(k,v){this.handlers[k]=v;}
 contains(n){return allNodes(this).includes(n);}
 querySelectorAll(q){const key=q.match(/^\[data-(.+)\]$/)?.[1]?.replace(/-([a-z])/g,(_,c)=>c.toUpperCase());return allNodes(this).filter(n=>key&&n.dataset[key]!==undefined);}
 focus(){document.activeElement=this;}
 click(){if(this.disabled)return; if(this.tag==='a')downloads.push({href:this.href,name:this.download});return this.handlers.click?.({currentTarget:this});}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}
}
const document={body:new Node('body'),activeElement:null,createElement:tag=>new Node(tag)};
const els={signalConsensusHistoryContent:new Node('root')};
const state={modal:{open:true,id:'council',signalTab:'history',signalHistoryTab:'operations'},propReports:{},aiTradeCouncilOperations:{
 data:null,events:[],inFlight:false,lastAttemptAt:0,nextCursor:'',hasMore:false,errorMessage:'',exportInFlight:false,exportMessage:''}};
let requests=[],downloads=[],blobs=[],revoked=[],snapshots=0;
URL.createObjectURL=blob=>{blobs.push(blob);return 'blob:fixture-'+blobs.length;};
URL.revokeObjectURL=url=>revoked.push(url);
let reply=()=>{throw Error('Unexpected GET');};
const fetchJson=async(path,options)=>{requests.push({path,options});return reply(path,options);};
const saveSessionSnapshot=()=>{snapshots++;};
const renderSignalHistoryPanel=()=>{if(state.modal.signalHistoryTab==='operations')renderSignalOperationsPanel();};
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const data=()=>({schemaVersion:'council-operations-v1',available:true,observedAt:new Date().toISOString(),lastSeenAt:new Date().toISOString(),
 heartbeat:{status:'ready'},events:[],incidents:{active:[],recovered:[]},readiness:{schemaVersion:'council-preflight-v1',advisory:true,
 canAuthorizeAnalysis:false,status:'ready',checkedAt:new Date().toISOString(),nextBarAt:null,checks:[]},nextCursor:null,hasMore:false,limitations:[]});
const event=(id,other={})=>({id,type:'incident',status:'active',severity:'warning',startedAt:'2026-10-29T11:00:00Z',
 lastSeenAt:'2026-10-29T11:01:00Z',reasonCode:'quota_limit_reached',certainty:'confirmed',occurrences:1,evidence:{source:'quota observer'},...other});
const find=(focus)=>allNodes(els.signalConsensusHistoryContent).find(n=>n.dataset.operationsFocus===focus);
"""
        for name in (
            "signalHistorySkipReasonLabel", "signalOperationsText", "signalOperationsTime", "signalOperationsReason",
            "signalOperationsMergeEvents", "signalOperationsIsOpen", "loadSignalOperations", "downloadSignalOperationsDiagnostics",
            "signalOperationsNode", "createSignalOperationsEvent", "renderSignalOperationsPanel",
        ):
            prefix = "async " if f"async function {name}(" in self.main else ""
            script += "\n" + prefix + function_block(self.main, name)
        result = subprocess.run([self.node, "-"], input=script + "\n(async()=>{\n" + body + "\n})().catch(e=>{console.error(e);process.exitCode=1;});",
                                text=True, encoding="utf-8", capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_events_deduplicate_by_id_preserve_distinct_attempts_and_unknown_reason(self):
        self.run_js(r"""
const first=event('same'),second=event('same',{status:'recovered',lastSeenAt:'2026-10-29T11:02:00Z'}),retry=event('retry');
const rows=signalOperationsMergeEvents([first],[second,retry]);
assert.equal(rows.length,2);assert.equal(rows.find(x=>x.id==='same').status,'recovered');
assert.match(signalOperationsReason({reasonCode:'new_backend_reason'}),/ยังไม่มีคำอธิบาย.*new_backend_reason/);
assert.doesNotMatch(signalOperationsReason({reasonCode:'new_backend_reason'}),/แอปปิด|NO TRADE|โควตาเต็ม/);
assert.match(signalOperationsReason({reasonCode:'quota_limit_reached'}),/โควตา Codex ถึงขีดจำกัด/);
assert.match(signalOperationsReason({reasonCode:'quota_unavailable',messageTh:'บันทึกสถานะจากสภา AI; ดูรหัส'}),/ไม่ได้ยืนยันว่าโควตาหมด/);
""")

    def test_get_cursor_pages_merge_without_overwriting_current_readiness(self):
        self.run_js(r"""
reply=()=>({...data(),events:[event('one')],nextCursor:'cursor + / ?',hasMore:true});
assert.equal(await loadSignalOperations({force:true}),true);
const current=state.aiTradeCouncilOperations.data;
reply=()=>({...data(),events:[event('one'),event('two',{startedAt:'2026-10-29T10:00:00Z'})],readiness:{status:'old'},hasMore:false});
assert.equal(await loadSignalOperations({more:true}),true);
assert.equal(state.aiTradeCouncilOperations.data,current);
assert.equal(state.aiTradeCouncilOperations.events.length,2);
assert.match(requests[1].path,/cursor=cursor\+%2B\+%2F\+%3F/);
assert.equal(requests.length,2);assert.equal(state.aiTradeCouncilOperations.hasMore,false);
assert.equal(await loadSignalOperations({more:true}),false);
""")

    def test_unavailable_malformed_and_repeated_cursor_preserve_existing_evidence(self):
        self.run_js(r"""
const page=state.aiTradeCouncilOperations;page.events=[event('cached')];page.data=data();page.nextCursor='same';page.hasMore=true;
for(const payload of [{...data(),available:false},{...data(),schemaVersion:'wrong'}, {...data(),events:[{}]}, {...data(),hasMore:true,nextCursor:'same'}]){
 reply=()=>payload;assert.equal(await loadSignalOperations({more:true}),false);
 assert.equal(page.events[0].id,'cached');assert.equal(page.inFlight,false);assert.match(page.errorMessage,/ไม่สำเร็จ/);
}
reply=()=>{throw Error('secret provider exception');};
await loadSignalOperations({force:true});assert.doesNotMatch(page.errorMessage,/secret/);
assert.match(page.errorMessage,/ยังสรุปไม่ได้ว่า HQ ปิด/);
""")

    def test_safe_dom_thai_times_unknown_gap_and_attempt_truth(self):
        self.run_js(r"""
const payload=data();payload.events=[event('gap',{type:'gap',certainty:'unknown',status:'unknown',messageTh:'<img src=x onerror=alert(1)>',reasonCode:'gap_unknown'}),
 event('bar',{type:'bar',status:'analyzed',attemptStatus:'partial',messageTh:'ผลไม่ครบ'})];
payload.incidents.active=[event('alert'),event('alert')];
state.aiTradeCouncilOperations.data=payload;state.aiTradeCouncilOperations.events=payload.events;
renderSignalOperationsPanel();const root=els.signalConsensusHistoryContent,text=root.textContent;
assert.match(text,/<img src=x onerror=alert\(1\)>/);assert.equal(allNodes(root).filter(n=>n.tag==='img').length,0);
assert.match(text,/18:00:00/);assert.match(text,/ยังยืนยันสาเหตุไม่ได้/);assert.match(text,/ได้ผลบางส่วน/);
assert.match(text,/เหตุที่ยังต้องตรวจ · 1/);assert.match(text,/ที่มา: quota observer/);
assert.equal(requests.length,0);assert.equal(downloads.length,0);
assert.equal(allNodes(root).filter(n=>n.attrs.role==='listitem').length,2);
""")

    def test_advisory_cannot_authorize_and_stale_heartbeat_not_green(self):
        self.run_js(r"""
const payload=data();payload.heartbeat.status='stale';payload.readiness.checks=[{id:'quota',label:'โควตา',status:'ready',messageTh:'พร้อม'}];
state.aiTradeCouncilOperations.data=payload;renderSignalOperationsPanel();
assert.match(els.signalConsensusHistoryContent.textContent,/ต้องตรวจข้อมูลใหม่/);
assert.equal(allNodes(els.signalConsensusHistoryContent).filter(n=>n.className==='signal-operations-check'&&n.dataset.tone==='ready').length,0);
payload.heartbeat.status='ready';payload.readiness.canAuthorizeAnalysis=true;renderSignalOperationsPanel();
assert.match(els.signalConsensusHistoryContent.textContent,/ก่อนแท่งถัดไป · ยังยืนยันไม่ได้/);
assert.match(els.signalConsensusHistoryContent.textContent,/ตรวจเงื่อนไขจริงอีกครั้ง/);
""")

    def test_queued_and_waiting_rounds_do_not_claim_ai_started(self):
        self.run_js(r"""
for(const attemptStatus of ['queued','waiting']) {
 const row=createSignalOperationsEvent(event('pending',{type:'bar',status:'pending',attemptStatus}));
 assert.match(row.textContent,/รับรอบแล้ว รอหลักฐานเริ่ม AI/);
 assert.doesNotMatch(row.textContent,/กำลังวิเคราะห์|Agent ให้ผลครบ/);
}
const running=createSignalOperationsEvent(event('started',{type:'bar',status:'queued',attemptStatus:'running',evidence:{processesStarted:1,completedVotes:0}}));
assert.match(running.textContent,/กำลังวิเคราะห์/);assert.match(running.textContent,/เริ่ม AI 1\/3/);
""")

    def test_current_unobserved_interval_and_superseded_incident_are_not_called_recovered(self):
        self.run_js(r"""
const payload=data();payload.unobservedInterval={startedAt:'2026-10-29T11:05:00Z',reasonCode:'observation_gap_unknown'};
payload.incidents.recovered=[event('old',{status:'superseded'})];state.aiTradeCouncilOperations.data=payload;
renderSignalOperationsPanel();const root=els.signalConsensusHistoryContent;
const gap=allNodes(root).find(n=>n.dataset.eventId==='current-unobserved-interval');
assert.match(gap.textContent,/18:05:00/);assert.match(gap.textContent,/ยังยืนยันสาเหตุไม่ได้/);
assert.doesNotMatch(gap.textContent,/แอปปิด|ยืนยันจากหลักฐาน/);
const old=allNodes(root).find(n=>n.dataset.eventId==='old');
assert.match(old.textContent,/เปลี่ยนไปติดเงื่อนไขอื่น/);assert.doesNotMatch(old.textContent,/กลับมาปกติแล้ว/);
assert.equal(state.aiTradeCouncilOperations.events.length,0);
""")

    def test_user_pagination_refresh_and_keyboard_navigation(self):
        self.run_js(r"""
const page=state.aiTradeCouncilOperations;page.data=data();page.hasMore=true;page.nextCursor='older';page.loadedMore=true;
reply=()=>({...data(),events:[event('older')],hasMore:false});renderSignalOperationsPanel();
find('more').click();await flush();assert.match(requests[0].path,/cursor=older/);
find('refresh').click();await flush();assert.doesNotMatch(requests[1].path,/cursor=/);assert.equal(page.loadedMore,false);
let prevented=false;find('tab-operations').handlers.keydown({key:'Home',preventDefault(){prevented=true;}});
assert.equal(state.modal.signalHistoryTab,'orders');assert.equal(prevented,true);assert.equal(snapshots,1);
""")

    def test_export_is_user_only_validated_redacted_get_and_blob_is_released(self):
        self.run_js(r"""
state.aiTradeCouncilOperations.data=data();renderSignalOperationsPanel();assert.equal(requests.length,0);
const report={schemaVersion:'council-diagnostics-v1',redacted:true,generatedAt:'2026-10-29T11:00:00Z',summary:{roles:3}};
reply=()=>report;find('download').click();await flush();
assert.equal(requests.length,1);assert.equal(requests[0].path,AI_TRADE_COUNCIL_DIAGNOSTICS_ENDPOINT);
assert.equal(downloads.length,1);assert.match(downloads[0].name,/^metafxclub-council-diagnostics-.*\.json$/);
assert.deepEqual(JSON.parse(await blobs[0].text()),report);assert.deepEqual(revoked,['blob:fixture-1']);
assert.equal(document.body.children.length,0);assert.equal(state.aiTradeCouncilOperations.exportInFlight,false);
""")

    def test_export_rejects_unverified_payload_errors_and_double_click(self):
        self.run_js(r"""
for(const payload of [{schemaVersion:'council-diagnostics-v1',redacted:false,token:'secret'}, {schemaVersion:'wrong',redacted:true}]){
 reply=()=>payload;assert.equal(await downloadSignalOperationsDiagnostics(),false);
}
assert.equal(downloads.length,0);assert.equal(blobs.length,0);assert.doesNotMatch(state.aiTradeCouncilOperations.exportMessage,/secret/);
let release;reply=()=>new Promise(resolve=>{release=resolve;});
const first=downloadSignalOperationsDiagnostics();assert.equal(await downloadSignalOperationsDiagnostics(),false);
release({schemaVersion:'council-diagnostics-v1',redacted:true});await first;
assert.equal(downloads.length,1);assert.equal(requests.length,3);
""")

    def test_gets_are_single_flight_throttled_and_close_does_not_reopen_ui(self):
        self.run_js(r"""
let release;reply=()=>new Promise(resolve=>{release=resolve;});const first=loadSignalOperations({force:true});
assert.equal(await loadSignalOperations({force:true}),false);assert.equal(requests.length,1);
state.modal.open=false;els.signalConsensusHistoryContent.textContent='closed';release(data());await first;
assert.equal(els.signalConsensusHistoryContent.textContent.trim(),'closed');
assert.equal(await loadSignalOperations(),false);assert.equal(requests.length,1);
""")

    def test_history_data_contract_and_existing_polling_lifecycle_remain_separate(self):
        self.assertIn('const SIGNAL_HISTORY_TABS = ["orders", "analysis"];', self.main)
        self.assertIn('const SIGNAL_HISTORY_VIEW_TABS = ["orders", "analysis", "operations"];', self.main)
        lifecycle = function_block(self.main, "renderOpenAiTradeCouncilRuntimeStatus")
        self.assertIn('state.modal.signalHistoryTab === "operations"', lifecycle)
        render = function_block(self.main, "renderSignalHistoryPanel")
        self.assertIn("void loadSignalOperations();", render)
        for name in ("loadSignalOperations", "renderSignalOperationsPanel", "downloadSignalOperationsDiagnostics"):
            block = function_block(self.main, name)
            for forbidden in ("setInterval", "setTimeout", "postJson", "Notification", "window.open", "innerHTML"):
                self.assertNotIn(forbidden, block)


if __name__ == "__main__":
    unittest.main()
