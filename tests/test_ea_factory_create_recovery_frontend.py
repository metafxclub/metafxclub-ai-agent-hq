"""Execute Create receipt recovery and Run admission with controlled transports."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryCreateRecoveryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        cls.node = shutil.which("node") or str(
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )

    def block(self, start, end):
        offset = self.main.index(start)
        return self.main[offset:self.main.index(end, offset)]

    def run_js(self, body):
        support = r"""
const assert=require('node:assert/strict');
const EA_FACTORY_PROP_ID='right_server_racks';
const EA_FACTORY_CUSTOM_SOURCE_ENDPOINT='/api/props/right_server_racks/ea-factory/sources/custom';
const EA_FACTORY_SUPPORTED_MODES=new Set(['one_click_with_manual_stage_recovery']);
const a='a'.repeat(64),b='b'.repeat(64),c='c'.repeat(64),d='d'.repeat(64);
let state, domain, posts, reads, events, keyCount, navigation, postEaFactoryJson, loadEaFactoryReadModel;
let eaFactoryActiveActionAbortController=null;
let fakeNow=0;
Date.now=()=>fakeNow;
globalThis.window={setTimeout:(fn,ms)=>{if(ms<=1000){fakeNow+=ms;queueMicrotask(fn);}return 1;},clearTimeout:()=>{}};
const normalizeEaFactoryArtifactKind=v=>v, normalizeEaFactoryPlatform=v=>v;
const getModalSubject=()=>({id:EA_FACTORY_PROP_ID}), getPropertyRole=()=>({});
const safeDashboardDisplayText=(v,f='')=>v||f;
const eaFactoryReadModelStateKey=v=>JSON.stringify(v);
const eaFactoryPlatformLabel=v=>v;
const rejectEaFactoryMissingTopHeaderLocks=()=>false;
const mergeBackendMission=()=>{},mergeEaFactoryResponseReport=()=>{},mergeEaFactoryReadModel=()=>false;
const eaFactoryActionPresentation=(_domain,action)=>action;
const eaFactoryBusyPresentation=busy=>({kind:'busy',tone:'warning',message:'busy',busy});
const eaFactoryReadModelFailurePresentation=error=>({kind:error.kind==='fetch_timeout'?'timeout':'request_rejected',tone:'warning',message:'request failed'});
const setEaFactoryActionState=next=>{Object.assign(state.modal.eaFactory,{inFlight:false},next);events.push({...next});};
const createWorkflowIdempotencyKey=()=>`workflow-key-${++keyCount}`;
const setWorkflowDashboardTab=(_prop,page)=>{navigation=page;};
const eaFactoryCreateSourceBinding=()=>({required:true,ready:true,fields:{recordId:'deep-a',recordDigest:a,catalogDigest:b,snapshotDigest:c,configRevision:1}});
function normalizeWorkflowDashboard(){
  const selected=state.modal.eaFactory.selectedBuildId;
  domain.activeBuild=state.eaFactoryReadModel.payload.builds.find(item=>item.id===selected)||null;
  return {domainData:{eaFactory:domain}};
}
function fixture(){
  posts=[];reads=0;events=[];keyCount=0;navigation=null;fakeNow=0;
  const source={sourceRecordId:'source-a',recordDigest:a,buildReady:true,compatiblePlatforms:['mt5']};
  const factory={inFlight:false,sourceMode:'google_sheet',selectedSourceId:'source-a',selectedPlatform:'mt5',selectedArtifactKind:'expert_advisor',sheetRecordId:'deep-a',createFormSignature:'',createIdempotencyKey:'',selectedBuildId:'',readContextRevision:0,googleSheetCatalog:{configRevision:1,catalogDigest:b,snapshotDigest:c}};
  const model={schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,snapshotStale:false,builds:[]};
  state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:factory},propReports:{},eaFactoryReadModel:{payload:model,stale:false,busy:null,lastLoadedAt:Date.now()}};
  domain={authoritative:true,backendBusy:null,canStartNewBuild:true,sourceCatalog:{records:[source]},stages:[],oneClick:{enabled:true,canRun:true,selectedTerminalId:'terminal-a',selectedPlatform:'mt5',selectedPlatformSupported:true,supportedVisiblePlatforms:['mt5'],terminalReady:true,terminalRunning:true,visibleAdapterConnected:true,terminalProcessLaunchAllowed:false,run:{status:'idle'}}};
  const receipt=payload=>({ok:true,kind:'ea_factory_build_created',requestIdempotencyKey:payload.idempotencyKey,createRequestDigest:d,build:{id:'ea-build-new',sourceRecordId:payload.sourceRecordId,sourceRecordDigest:a,platform:payload.platform,artifactKind:payload.artifactKind,brief:String(payload.brief||'').replace(/\s+/g,' ').trim(),createRequestDigest:d,createSheetBinding:{sourceRecordId:payload.sourceRecordId,recordId:payload.recordId,recordDigest:payload.recordDigest,catalogDigest:payload.catalogDigest,snapshotDigest:payload.snapshotDigest,configRevision:payload.configRevision}}});
  postEaFactoryJson=async(path,payload)=>{posts.push({path,payload:{...payload}});return path.endsWith('/run')?{ok:true}:receipt(payload);};
  loadEaFactoryReadModel=async()=>{reads++;model.builds=[{...receipt(posts[0].payload).build}];state.eaFactoryReadModel.stale=false;return {eaFactory:model};};
  return {source,factory,model,receipt};
}
function customFixture(){
  const f=fixture();
  Object.assign(f.factory,{sourceMode:'custom',customSystemName:'EMA 10/60 Closed-Bar Smoke EA',customConditions:'EMA 10/60 with adjustable TP and SL',customTemplateId:'ema_10_60_smoke_v1'});
  f.model.sourceCatalog={records:[f.source]};
  postEaFactoryJson=async(path,payload)=>{
    posts.push({path,payload:{...payload}});
    if(path===EA_FACTORY_CUSTOM_SOURCE_ENDPOINT)return {ok:true,kind:'ea_factory_custom_source',sourceRecordId:f.source.sourceRecordId,source:f.source};
    return path.endsWith('/run')?{ok:true}:f.receipt(payload);
  };
  loadEaFactoryReadModel=async()=>{
    reads++;const created=posts.find(row=>row.path.endsWith('/builds'));
    if(created)f.model.builds=[{...f.receipt(created.payload).build}];
    f.model.snapshotStale=false;state.eaFactoryReadModel.stale=false;state.eaFactoryReadModel.lastError=null;
    return {eaFactory:f.model};
  };
  return f;
}
"""
        parts = [support]
        for start, end in (
            ("function eaFactoryEmaSmokeCustomSourcePayload", "function eaFactoryTopHeaderLockPreflight"),
            ("async function waitForEaFactoryAuthoritativeReceipt", "async function createEaFactoryCustomSourceAndStart"),
            ("async function createEaFactoryCustomSourceAndStart", "function renderEaFactoryCustomSourcePreview"),
            ("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet"),
            ("function eaFactoryCreateBuildFormSignature", "function eaFactoryOneClickRequestKey"),
            ("function eaFactoryOneClickRequestKey", "function eaFactoryBacktestRestartRequestKey"),
            ("async function runEaFactoryOneClick", "function cancelEaFactorySubmittingRequest"),
            ("async function createAndRunEaFactoryBuild", "async function advanceEaFactoryStage"),
        ):
            parts.append(self.block(start, end))
        parts.append("(async()=>{\n" + body + "\n})().catch(error=>{console.error(error);process.exitCode=1;});")
        result = subprocess.run([self.node, "-"], input="\n".join(parts), cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_receipt_is_visible_before_projection_but_never_authority(self):
        self.run_js(r"""
const f=fixture();let finish;
loadEaFactoryReadModel=async()=>new Promise(resolve=>{finish=resolve;});
const pending=createEaFactoryBuild('source-a','expert_advisor','mt5','same brief');
await new Promise(resolve=>setImmediate(resolve));
assert.equal(f.factory.selectedBuildId,'ea-build-new');assert.equal(navigation,'progress');
assert.equal(f.factory.confirmedCreateBuildId,'ea-build-new');
assert.equal(f.factory.messageKind,'create_receipt_confirmed');assert.equal(state.eaFactoryReadModel.stale,true);
assert.equal(posts.length,1);finish(null);assert.ok(await pending);
""")

    def test_confirmed_receipt_survives_real_read_timeout_without_run_or_duplicate_create(self):
        loader = self.block("async function loadEaFactoryReadModel", "function setEaFactoryActionState")
        progress = self.block("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage")
        self.run_js("let eaFactoryReadModelInFlight=null; const PROP_REPORT_FETCH_TIMEOUT_MS=20;\n"
                    "const fetchJson=async()=>{throw Object.assign(new Error('cold model'),{kind:'fetch_timeout'});};\n"
                    "loadEaFactoryReadModel=" + loader.rstrip() + ";\n" + progress + r"""
globalThis.document={createElement:()=>({children:[],append(...values){this.children.push(...values);},appendChild(v){this.children.push(v);}})};
globalThis.createEaFactoryGameAction=(label,handler)=>({textContent:label,handler});
globalThis.createEaFactoryPageNavigation=()=>({textContent:'new create navigation'});
globalThis.refreshEaFactoryProgressStatus=async()=>{};
const realLoader=loadEaFactoryReadModel;
const f=fixture();loadEaFactoryReadModel=realLoader;
assert.ok(await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5',''));
assert.equal(posts.length,1);assert.match(posts[0].path,/\/builds$/);
assert.equal(f.factory.selectedBuildId,'ea-build-new');
assert.equal(f.factory.confirmedCreateBuildId,'ea-build-new');
assert.equal(f.factory.stageId,'read_model');assert.equal(state.eaFactoryReadModel.stale,true);
assert.equal(f.factory.createIdempotencyKey,'workflow-key-1');
const section=document.createElement('section');renderEaFactoryProgressPage(section,{});
const panel=section.children[0];
assert.equal(panel.children[0].textContent,'Backend รับ Build แล้ว');
assert.match(panel.children[1].textContent,/ea-build-new/);
assert.match(panel.children[1].textContent,/ยังยืนยันสถานะปัจจุบันไม่ได้/);
assert.equal(panel.children[2].textContent,'ตรวจสถานะ Build นี้');
assert.equal(panel.children.length,3);assert.equal(posts.length,1);
""")

    def test_timeout_replays_exact_payload_once_without_projection_wait(self):
        self.run_js(r"""
const f=fixture();postEaFactoryJson=async(path,payload)=>{
  posts.push({path,payload:{...payload}});assert.equal(reads,0);
  if(posts.length===1)throw Object.assign(new Error('ack lost'),{kind:'fetch_timeout'});
  return {...f.receipt(payload),kind:'ea_factory_build_replayed'};
};
assert.ok(await createEaFactoryBuild('source-a','expert_advisor','mt5','same brief'));
assert.equal(posts.length,2);assert.deepEqual(posts[0],posts[1]);assert.equal(keyCount,1);assert.equal(reads,1);
assert.equal(f.factory.createIdempotencyKey,'');assert.equal(f.factory.selectedBuildId,'ea-build-new');
""")

    def test_second_timeout_retains_original_identity_and_no_run(self):
        self.run_js(r"""
const f=fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});throw Object.assign(new Error('timeout'),{kind:'fetch_timeout'});};
assert.equal(await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5',''),null);
assert.equal(posts.length,2);assert.equal(reads,0);assert.equal(keyCount,1);
assert.equal(f.factory.createIdempotencyKey,'workflow-key-1');assert.equal(f.factory.selectedBuildId,'');
assert.equal(f.factory.messageKind,'create_outcome_unconfirmed');
""")

    def test_http_and_operator_cancel_never_replay_or_run(self):
        self.run_js(r"""
for(const kind of ['request_rejected','ea_factory_operator_cancelled_request']){
  fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});throw Object.assign(new Error(kind),{kind});};
  if(kind==='ea_factory_operator_cancelled_request')loadEaFactoryReadModel=async()=>null;
  assert.equal(await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5',''),null);
  assert.equal(posts.length,1);assert.equal(keyCount,1);
}
""")

    def test_exact_receipt_rejects_missing_proof_and_changed_form_fields(self):
        self.run_js(r"""
const f=fixture();const payload={sourceRecordId:'source-a',artifactKind:'expert_advisor',platform:'mt5',brief:'same   brief',...eaFactoryCreateSourceBinding().fields};
const identity=eaFactoryCreateBuildRequestIdentity(payload);payload.idempotencyKey=identity.idempotencyKey;
const response=f.receipt(payload);assert.ok(eaFactoryCreateCommitReceipt(response,identity,a));
for(const mutate of [r=>delete r.build,r=>r.build=[],r=>r.requestIdempotencyKey='other-key',r=>r.createRequestDigest=a,
  r=>r.build.sourceRecordId='other',r=>r.build.sourceRecordDigest=b,r=>r.build.platform='mt4',r=>r.build.artifactKind='custom_indicator',
  r=>r.build.brief='different brief',r=>r.build.createSheetBinding.sourceRecordId='other',r=>r.build.createSheetBinding.recordId='other',r=>r.build.createSheetBinding.recordDigest=b,
  r=>r.build.createSheetBinding.catalogDigest=a,r=>r.build.createSheetBinding.snapshotDigest=b,r=>r.build.createSheetBinding.configRevision=2]){
  const bad=structuredClone(response);mutate(bad);assert.equal(eaFactoryCreateCommitReceipt(bad,identity,a),null);
}
""")

    def test_actual_sanitized_http_created_and_replayed_receipts_match_request(self):
        # Captured from create_ea_factory_build -> BridgeHandler.do_POST ->
        # send_result/send_json using isolated synthetic state, not hand-shaped JSON.
        wire = json.loads((ROOT / "tests/fixtures/ea_factory_create_wire_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(wire["status"], 200)
        self.assertEqual(wire["replayStatus"], 200)
        self.run_js("const wire=" + json.dumps(wire) + r""";
fixture();const identity={idempotencyKey:wire.request.idempotencyKey,formSignature:eaFactoryCreateBuildFormSignature(wire.request)};
for(const response of [wire.created,wire.replayed]){
  assert.equal(response.eaFactory,undefined);assert.equal(response.build.oneClick,undefined);
  assert.ok(eaFactoryCreateCommitReceipt(response,identity,wire.sourceRecordDigest));
  const wrong=structuredClone(response);wrong.build.sourceRecordId='different-source';
  assert.equal(eaFactoryCreateCommitReceipt(wrong,identity,wire.sourceRecordDigest),null);
}
""")

    def test_custom_source_receipt_without_sheet_binding_remains_supported(self):
        self.run_js(r"""
fixture();const request={sourceRecordId:'custom-source',artifactKind:'expert_advisor',platform:'mt5',brief:'custom brief'};
const identity=eaFactoryCreateBuildRequestIdentity(request);
const response={ok:true,kind:'ea_factory_build_created',requestIdempotencyKey:identity.idempotencyKey,createRequestDigest:d,
  build:{id:'ea-build-custom',...request,sourceRecordDigest:a,createRequestDigest:d}};
assert.ok(eaFactoryCreateCommitReceipt(response,identity,a));
""")

    def test_custom_source_and_create_wait_through_deferred_and_stale_without_reposting(self):
        self.run_js(r"""
const f=customFixture();const normal=loadEaFactoryReadModel;const phases={source:0,build:0};
loadEaFactoryReadModel=async()=>{
  const phase=posts.some(row=>row.path.endsWith('/builds'))?'build':'source';
  phases[phase]++;const payload=await normal();
  if(phases[phase]<=2){state.eaFactoryReadModel.stale=true;state.eaFactoryReadModel.lastError={kind:'refreshing'};
    if(phases[phase]===1)return null;f.model.snapshotStale=true;}
  return payload;
};
assert.ok(await createEaFactoryCustomSourceAndStart({platform:'mt5',artifactKind:'expert_advisor'}));
assert.deepEqual(posts.map(row=>row.path),[EA_FACTORY_CUSTOM_SOURCE_ENDPOINT,
  '/api/props/right_server_racks/ea-factory/builds','/api/props/right_server_racks/ea-factory/builds/ea-build-new/run']);
assert.equal(phases.source,3);assert.ok(phases.build>=3);assert.equal(keyCount,2);
assert.equal(f.factory.selectedBuildId,'ea-build-new');assert.equal(f.factory.createIdempotencyKey,'');
""")

    def test_waiting_source_disables_double_submission_until_same_intent_continues(self):
        self.run_js(r"""
const f=customFixture();const normal=loadEaFactoryReadModel;let finish;
loadEaFactoryReadModel=()=>new Promise(resolve=>{finish=async()=>{loadEaFactoryReadModel=normal;resolve(await normal());};});
const pending=createEaFactoryCustomSourceAndStart({platform:'mt5',artifactKind:'expert_advisor'});
await new Promise(resolve=>setImmediate(resolve));
assert.equal(f.factory.inFlight,true);assert.equal(f.factory.stageId,'awaiting_fresh_read');
assert.equal(posts.length,1);
assert.equal(await createEaFactoryCustomSourceAndStart({platform:'mt5',artifactKind:'expert_advisor'}),null);
assert.equal(posts.length,1);await finish();await pending;
assert.equal(posts.filter(row=>row.path===EA_FACTORY_CUSTOM_SOURCE_ENDPOINT).length,1);
assert.equal(posts.filter(row=>row.path.endsWith('/builds')).length,1);
""")

    def test_custom_wait_cancels_on_closed_replaced_changed_context_or_operator_abort(self):
        self.run_js(r"""
for(const change of [f=>state.modal.open=false,f=>state.modal.eaFactory={...f.factory,inFlight:true,stageId:'other'},
  f=>f.factory.readContextRevision++,f=>f.factory.customConditions='different requirements',
  f=>f.factory.selectedPlatform='mt4',f=>f.factory.selectedSourceId='another',
  f=>eaFactoryActiveActionAbortController.abort()]){
  const f=customFixture();const normal=loadEaFactoryReadModel;
  loadEaFactoryReadModel=async()=>{const result=await normal();change(f);return result;};
  await createEaFactoryCustomSourceAndStart({platform:'mt5',artifactKind:'expert_advisor'});
  assert.equal(posts.length,1);assert.equal(f.factory.selectedBuildId,'');
  if(state.modal.eaFactory===f.factory)assert.equal(f.factory.inFlight,false);
  else assert.equal(state.modal.eaFactory.inFlight,true);
}
""")

    def test_custom_wait_hard_errors_or_wrong_receipt_identity_never_create(self):
        self.run_js(r"""
for(const failure of ['integrity','schema','wrong-id','wrong-digest','malformed-receipt']){
  const f=customFixture();const normal=loadEaFactoryReadModel;
  if(failure==='malformed-receipt')postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return {ok:true,kind:'ea_factory_custom_source',sourceRecordId:'source-a'};};
  else loadEaFactoryReadModel=async()=>{
    if(['integrity','schema'].includes(failure)){reads++;state.eaFactoryReadModel.lastError={kind:failure,message:'blocked by '+failure};return null;}
    const result=await normal();if(failure==='wrong-id')f.model.sourceCatalog.records=[{...f.source,sourceRecordId:'different'}];
    else f.model.sourceCatalog.records=[{...f.source,recordDigest:b}];return result;
  };
  await createEaFactoryCustomSourceAndStart({platform:'mt5',artifactKind:'expert_advisor'});
  assert.equal(posts.length,1);assert.equal(f.factory.selectedBuildId,'');assert.ok(reads<=1);
}
""")

    def test_source_wait_deadline_is_read_only_and_cannot_accept_late_fresh_result(self):
        self.run_js(r"""
for(const lateFresh of [false,true]){
  const f=customFixture();const normal=loadEaFactoryReadModel;
  loadEaFactoryReadModel=async()=>{
    if(lateFresh){const result=await normal();fakeNow+=45000;return result;}
    reads++;state.eaFactoryReadModel.stale=true;state.eaFactoryReadModel.lastError={kind:'refreshing'};return null;
  };
  await createEaFactoryCustomSourceAndStart({platform:'mt5',artifactKind:'expert_advisor'});
  assert.equal(posts.length,1);assert.equal(f.factory.selectedBuildId,'');assert.equal(f.factory.selectedSourceId,'source-a');
  assert.equal(f.factory.inFlight,false);assert.ok(reads<=45);assert.ok(fakeNow>=45000);
}
""")

    def test_build_wait_keeps_receipt_and_key_without_running_after_deadline(self):
        self.run_js(r"""
for(const lateFresh of [false,true]){
  const f=fixture();const normal=loadEaFactoryReadModel;
  loadEaFactoryReadModel=async()=>{
    const result=await normal();
    if(lateFresh){fakeNow+=45000;return result;}
    f.model.snapshotStale=true;state.eaFactoryReadModel.stale=true;state.eaFactoryReadModel.lastError={kind:'refreshing'};return result;
  };
  const response=await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5','');
  assert.equal(response.readModelReady,false);assert.equal(posts.length,1);assert.equal(keyCount,1);
  assert.equal(f.factory.selectedBuildId,'ea-build-new');assert.equal(f.factory.confirmedCreateBuildId,'ea-build-new');
  assert.equal(f.factory.createIdempotencyKey,'workflow-key-1');assert.equal(f.factory.inFlight,false);
}
""")

    def test_closed_replaced_or_changed_intent_cannot_commit_or_replay(self):
        self.run_js(r"""
for(const change of [f=>state.modal.open=false,f=>state.modal.eaFactory={...f.factory,inFlight:true,stageId:'other'},
  f=>f.factory.readContextRevision++,f=>f.factory.selectedSourceId='other',f=>f.factory.selectedPlatform='mt4',
  f=>f.factory.selectedArtifactKind='custom_indicator',f=>f.factory.googleSheetCatalog.configRevision=2]){
  const f=fixture();let reject;postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return new Promise((_r,j)=>{reject=j;});};
  const pending=createAndRunEaFactoryBuild('source-a','expert_advisor','mt5','');
  change(f);reject(Object.assign(new Error('ack lost'),{kind:'fetch_timeout'}));
  assert.equal(await pending,null);assert.equal(posts.length,1);assert.equal(reads,0);assert.equal(f.factory.selectedBuildId,'');
  if(state.modal.eaFactory===f.factory)assert.equal(f.factory.inFlight,false);
  else assert.equal(state.modal.eaFactory.inFlight,true);
}
""")

    def test_tab_change_keeps_create_and_fresh_run_allowed(self):
        self.run_js(r"""
const f=fixture();let finish;postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});if(path.endsWith('/run'))return {ok:true};return new Promise(resolve=>{finish=()=>resolve(f.receipt(payload));});};
const pending=createAndRunEaFactoryBuild('source-a','expert_advisor','mt5','');navigation='progress';finish();
assert.ok(await pending);assert.equal(posts.length,2);assert.match(posts[1].path,/ea-build-new\/run$/);
""")

    def test_stale_wrong_or_missing_build_never_auto_runs(self):
        self.run_js(r"""
for(const mutate of [f=>state.eaFactoryReadModel.stale=true,f=>f.model.snapshotStale=true,f=>domain.authoritative=false,
  f=>f.model.builds=[],f=>f.model.builds[0].id='ea-build-old',f=>f.model.builds[0].sourceRecordId='other',
  f=>f.model.builds[0].sourceRecordDigest=b,f=>f.model.builds[0].platform='mt4',f=>f.model.builds[0].artifactKind='custom_indicator']){
  const f=fixture();const normal=loadEaFactoryReadModel;loadEaFactoryReadModel=async()=>{const result=await normal();mutate(f);return result;};
  assert.ok(await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5',''));
  assert.equal(posts.length,1);assert.equal(f.factory.selectedBuildId,'ea-build-new');
}
""")

    def test_late_model_never_starts_and_context_changes_during_get_cannot_continue(self):
        self.run_js(r"""
for(const change of [f=>state.modal.open=false,f=>f.factory.readContextRevision++,f=>f.factory.selectedSourceId='other']){
  const f=fixture();const normal=loadEaFactoryReadModel;loadEaFactoryReadModel=async()=>{const value=await normal();change(f);return value;};
  assert.equal(await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5',''),null);assert.equal(posts.length,1);
}
const f=fixture();const normal=loadEaFactoryReadModel;loadEaFactoryReadModel=async()=>null;
assert.ok(await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5',''));assert.equal(posts.length,1);
await normal();assert.equal(posts.length,1);
""")

    def test_normal_run_guards_still_block_after_exact_fresh_receipt(self):
        self.run_js(r"""
for(const mutate of [()=>domain.oneClick.canRun=false,()=>domain.oneClick.enabled=false,
  ()=>domain.oneClick.terminalRunning=false,()=>domain.oneClick.visibleAdapterConnected=false,
  ()=>domain.oneClick.terminalProcessLaunchAllowed=true,()=>domain.backendBusy={buildId:'other'}]){
  fixture();const normal=loadEaFactoryReadModel;loadEaFactoryReadModel=async()=>{const value=await normal();mutate();return value;};
  assert.equal(await createAndRunEaFactoryBuild('source-a','expert_advisor','mt5',''),null);assert.equal(posts.length,1);
}
""")

    def test_progress_keeps_uncertain_create_message_visible(self):
        progress = self.block("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage")
        self.run_js(progress + r"""
globalThis.document={createElement:()=>({children:[],append(...values){this.children.push(...values);},appendChild(v){this.children.push(v);}})};
globalThis.createEaFactoryPageNavigation=()=>({});
const f=fixture();f.factory.stageId='create_build';f.factory.messageKind='create_outcome_unconfirmed';f.factory.message='Original request outcome unknown';
const section=document.createElement('section');renderEaFactoryProgressPage(section,{});
assert.match(section.children[0].children[0].textContent,/กำลังตรวจคำขอสร้าง Build/);
assert.equal(section.children[0].children[1].textContent,f.factory.message);
""")


if __name__ == "__main__":
    unittest.main()
