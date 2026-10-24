"""Execute explicit same-Build continuation UI and exact receipt recovery."""
import importlib.util
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryCancelledContinuationFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        cls.node = shutil.which("node") or str(
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )

    def block(self, start, end):
        offset = self.main.index(start)
        return self.main[offset:self.main.index(end, offset)]

    def run_js(self, body, extra=""):
        support = r"""
const assert=require('node:assert/strict');
class Element {
  constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attrs={};this.events={};this._text='';}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent??String(c)).join(' ');}
  append(...children){this.children.push(...children);}
  appendChild(child){this.children.push(child);return child;}
  setAttribute(name,value){this.attrs[name]=String(value);}
  addEventListener(name,handler){this.events[name]=handler;}
}
const document={createElement:tag=>new Element(tag)};
const EA_FACTORY_PROP_ID='right_server_racks';
const EA_FACTORY_VISUAL_STAGE_IDS=['generate'];
const EA_FACTORY_STAGE_VISUALS={generate:{image:'fixture.png',imageAltTh:'source',shortTitleTh:'สร้าง Source'}};
const EA_FACTORY_STAGE_COPY={generate:{descriptionTh:'Source',titleTh:'Source'}};
const EA_FACTORY_SUPPORTED_MODES=new Set(['one_click_with_manual_stage_recovery']);
const EA_FACTORY_UI_STAGE_BY_BACKEND={generate_source:'generate'};
const EA_FACTORY_STAGE_IDS=['generate'];
const digest='a'.repeat(64),archive='b'.repeat(64);
const endpoint='/api/props/right_server_racks/ea-factory/builds/ea-build-exact/resume-cancelled';
let state,domain,posts,reads,renders,navigations,headerReady,keyCount,events,missionViews,postEaFactoryJson,loadEaFactoryReadModel;
let eaFactoryActiveActionAbortController=null;
const safeDashboardDisplayText=(v,f='')=>v||f;
const eaFactoryFirstArray=(...values)=>values.find(Array.isArray)||[];
const normalizeEaFactoryStageStatus=v=>v;
const eaFactoryPlatformLabel=v=>v,eaFactoryArtifactKindLabel=v=>v;
const eaFactoryPhaseGateProgress=d=>({status:d.oneClick?.run?.status||'idle',active:!!d.backendBusy,waiting:false,determinate:true,percent:0,currentStageLabel:'Source'});
const eaFactoryOneClickStageStatus=(d,id)=>d.stages.find(s=>s.id===id)?.status||'unknown';
const eaFactoryCertifiedDeliveryCompleted=()=>false;
const eaFactoryExistingOneClickAdmission=()=>({canSubmit:false});
const createEaFactoryStopButton=()=>new Element('button');
const createEaFactoryPageNavigation=(label,page)=>{const e=new Element('button');e.textContent=label;e.addEventListener('click',()=>navigations.push(page));return e;};
const refreshEaFactoryProgressStatus=async()=>{reads++;};
const restartEaFactoryBacktestOnly=async()=>{throw Error('unexpected restart');};
const runEaFactoryOneClick=async()=>{throw Error('unexpected ordinary Run');};
const openTaskDetail=(id)=>missionViews.push(id);
const eaFactoryTopHeaderLockPreflight=()=>({ready:headerReady});
const getModalSubject=()=>({id:EA_FACTORY_PROP_ID}),getPropertyRole=()=>({});
const normalizeWorkflowDashboard=()=>({domainData:{eaFactory:domain}});
const renderWorkflowDashboard=()=>{renders++;};
const eaFactoryReadModelStateKey=v=>JSON.stringify(v);
const setEaFactoryActionState=next=>{Object.assign(state.modal.eaFactory,{inFlight:false},next);events.push({...next});};
const createWorkflowIdempotencyKey=()=>`continuation-key-${++keyCount}`;
const setWorkflowDashboardTab=(_prop,page)=>navigations.push(page);
const mergeBackendMission=()=>{throw Error('unexpected Mission merge');};
const mergeEaFactoryResponseReport=response=>{assert.equal(response.report,undefined);};
let mergeEaFactoryReadModel=response=>{assert.equal(response.eaFactory,undefined);return false;};
const eaFactoryReadModelFailurePresentation=e=>({kind:e.kind==='fetch_timeout'?'timeout':'request_rejected',tone:'warning',message:e.message});
const eaFactoryBusyPresentation=busy=>({kind:'busy',tone:'warning',message:'busy',busy});
const eaFactoryActionPresentation=(_domain,action)=>action;
function fixture(){
  posts=[];reads=0;renders=0;navigations=[];events=[];missionViews=[];keyCount=0;headerReady=true;eaFactoryActiveActionAbortController=null;
  const run={runId:'ea-run-cancelled',status:'cancelled',canResumeCancelled:true,resumeCancelledEndpoint:endpoint,
    resumeCancelledRunDigest:digest,resumeCancelledReasonCode:'',resumeCancelledStageId:'generate_source',resumeCancelledMissionId:'mission-source'};
  state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{selectedBuildId:'ea-build-exact',readContextRevision:0,inFlight:false}},propReports:{},
    eaFactoryReadModel:{payload:{snapshotStale:false},stale:false,busy:null}};
  domain={authoritative:true,backendBusy:null,activeBuild:{id:'ea-build-exact',platform:'mt5',artifactKind:'expert_advisor'},
    stages:[{id:'generate',backendId:'generate_source',status:'running',missionId:'mission-source'}],
    oneClick:{enabled:true,selectedPlatform:'mt5',selectedPlatformSupported:true,supportedVisiblePlatforms:['mt5'],
      selectedTerminalId:'terminal-a',terminalReady:true,terminalRunning:true,visibleAdapterConnected:true,terminalProcessLaunchAllowed:false,run}};
  postEaFactoryJson=async(path,payload)=>{posts.push({path,payload:{...payload}});return wire(payload);};
  loadEaFactoryReadModel=async()=>{reads++;return null;};
  return {factory:state.modal.eaFactory,run};
}
function wire(payload,replay=false){return {ok:true,kind:replay?'ea_factory_cancelled_run_resume_replayed':'ea_factory_cancelled_run_resumed',
  buildId:'ea-build-exact',previousRunId:payload.previousRunId,previousRunDigest:payload.previousRunDigest,
  runId:'ea-run-successor',requestIdempotencyKey:payload.idempotencyKey,continuationArchiveDigest:archive,
  adoptedMissionId:'mission-source',idempotentReplay:replay,workerStarted:!replay,
  eaFactoryReadResult:{kind:'ea_factory_refresh_deferred',status:'deferred',readinessConfirmed:false,refreshEndpoint:'/api/props/right_server_racks/ea-factory'}};}
const all=e=>[e,...e.children.flatMap(c=>c instanceof Element?all(c):[])];
const buttons=e=>all(e).filter(n=>n.tagName==='button');
const continuationButton=e=>buttons(e).find(n=>n.textContent==='ทำงานต่อจาก Build เดิม');
const render=()=>{const e=new Element('main');renderEaFactoryGameProgressPanel(e,domain);return e;};
const submit=()=>resumeEaFactoryCancelledRun('ea-build-exact','ea-run-cancelled',digest);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
"""
        parts = [support]
        for start, end in (
            ("function normalizeEaFactoryOneClickRun", "function applyEaFactoryStageAdmission"),
            ("function eaFactoryCurrentVisualStageId", "function renderEaFactoryOneClickSetup"),
            ("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet"),
            ("function eaFactoryCancelledContinuationReceipt", "async function runEaFactoryOneClick"),
        ):
            parts.append(self.block(start, end))
        parts.extend([extra, "(async()=>{\n" + body + "\n})().catch(e=>{console.error(e);process.exitCode=1;});"])
        result = subprocess.run([self.node, "-"], input="\n".join(parts), cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_render_is_explicit_and_click_uses_only_exact_recovery_endpoint(self):
        self.run_js(r"""
fixture();const root=render();assert.equal(posts.length,0);assert.equal(reads,0);
const button=continuationButton(root);assert.ok(button);button.events.click();await tick();
assert.equal(posts.length,1);assert.equal(posts[0].path,endpoint);
assert.deepEqual(posts[0].payload,{previousRunId:'ea-run-cancelled',previousRunDigest:digest,idempotencyKey:'continuation-key-1'});
assert.equal(state.modal.eaFactory.selectedBuildId,'ea-build-exact');assert.deepEqual(navigations,['progress']);
assert.equal(state.eaFactoryReadModel.stale,true);assert.equal(continuationButton(render()),undefined);
""")

    def test_reload_busy_build_requires_read_only_selection_before_explicit_resume(self):
        self.run_js(r"""
fixture();state.modal.eaFactory.selectedBuildId='';
domain.backendBusy={buildId:'ea-build-exact',stageId:'generate_source',missionId:'mission-source'};
const root=render();assert.equal(continuationButton(root),undefined);assert.equal(posts.length,0);
const choose=buttons(root).find(b=>b.textContent==='เลือก Build นี้เพื่อทำต่อ');assert.ok(choose);
choose.events.click();assert.equal(state.modal.eaFactory.selectedBuildId,'ea-build-exact');
assert.equal(posts.length,0);assert.equal(reads,0);assert.equal(renders,1);assert.equal(keyCount,0);
const resume=continuationButton(render());assert.ok(resume);assert.equal(posts.length,0);
resume.events.click();await tick();assert.equal(posts.length,1);assert.equal(posts[0].path,endpoint);
""")

    def test_displayed_build_selection_rechecks_context_identity_freshness_and_capability(self):
        self.run_js(r"""
for(const change of [()=>state.modal.open=false,()=>state.modal.id='other',
  ()=>state.modal.eaFactory.readContextRevision++,()=>state.modal.eaFactory={...state.modal.eaFactory},
  ()=>state.modal.eaFactory.selectedBuildId='ea-build-other',()=>state.modal.eaFactory.inFlight=true,
  ()=>domain.authoritative=false,()=>state.eaFactoryReadModel.stale=true,
  ()=>state.eaFactoryReadModel.payload.snapshotStale=true,()=>domain.activeBuild.id='ea-build-other',
  ()=>domain.oneClick.run.runId='ea-run-other',()=>domain.oneClick.run.resumeCancelledRunDigest='c'.repeat(64),
  ()=>domain.oneClick.run.canResumeCancelled=false,()=>domain.backendBusy.missionId='foreign',
  ()=>domain.backendBusy.stageId='compile_validate',()=>headerReady=false]){
  fixture();state.modal.eaFactory.selectedBuildId='';
  domain.backendBusy={buildId:'ea-build-exact',stageId:'generate_source',missionId:'mission-source'};
  const choose=buttons(render()).find(b=>b.textContent==='เลือก Build นี้เพื่อทำต่อ');assert.ok(choose);
  change();const before=state.modal.eaFactory.selectedBuildId;choose.events.click();
  assert.equal(state.modal.eaFactory.selectedBuildId,before);assert.equal(renders,0);assert.equal(posts.length,0);assert.equal(reads,0);
}
""")

    def test_actual_reload_normalization_auto_picks_busy_build_without_selecting_it(self):
        normalization = self.block("function applyEaFactoryStageAdmission", "function eaOptimizationLabFirstArray")
        ingestion = self.block("function validateEaFactoryBusyModel", "function eaFactoryBusyContext")
        ingestion += "\nmergeEaFactoryReadModel=" + self.block("function mergeEaFactoryReadModel", "function mergeEaFactoryResponseReport") + ";"
        self.run_js(r"""
fixture();const buildId='ea-build-1792303401129-27a169',missionId='mission-1792306126519-37e8b3';
const runId='ea-run-cc0a3f5a61b38c3a32457e99';
const rawRun={...domain.oneClick.run,runId,resumeCancelledMissionId:missionId,
  resumeCancelledEndpoint:`/api/props/right_server_racks/ea-factory/builds/${buildId}/resume-cancelled`,
  resumeCancelledRunDigest:'2a2a31eacb102a645dd0a18af059af08888a7cb6f163b773fb4fa0b06238c259'};
const busy={buildId,stageId:'generate_source',missionId,status:'queued',activeOperation:'generate_source'};
const model={schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,snapshotStale:false,
  busy,builds:[{id:buildId,platform:'mt5',artifactKind:'expert_advisor',oneClickRun:rawRun,
    stages:[{id:'generate_source',status:'queued',missionId}]}],
  oneClick:{...domain.oneClick},terminalSelection:{selectedTerminalId:'terminal-a',adapterReady:true,
    candidates:[{id:'terminal-a',platform:'mt5'}]}};
state.modal.eaFactory.selectedBuildId='';assert.equal(mergeEaFactoryReadModel({eaFactory:model}),true);
assert.equal(state.eaFactoryReadModel.busy.missionId,missionId);
domain=normalizeEaFactoryDomain(state.eaFactoryReadModel.payload);
assert.equal(domain.activeBuild.id,buildId);assert.equal(domain.authoritative,true);
assert.equal(state.modal.eaFactory.selectedBuildId,'');assert.equal(continuationButton(render()),undefined);
const choose=buttons(render()).find(b=>b.textContent==='เลือก Build นี้เพื่อทำต่อ');assert.ok(choose);
choose.events.click();assert.equal(state.modal.eaFactory.selectedBuildId,buildId);assert.equal(posts.length,0);
domain=normalizeEaFactoryDomain({eaFactory:model});assert.ok(continuationButton(render()));assert.equal(posts.length,0);
for(const identity of [undefined,null,'','mission-foreign']){
  state.modal.eaFactory.selectedBuildId='';model.busy={...busy,missionId:identity};
  assert.equal(mergeEaFactoryReadModel({eaFactory:model}),true);
  domain=normalizeEaFactoryDomain(state.eaFactoryReadModel.payload);
  assert.equal(eaFactoryCancelledContinuationAdmission(domain).canSelect,false);
  assert.equal(continuationButton(render()),undefined);assert.equal(posts.length,0);
}
for(const identity of [false,true,123,{},[], '../mission', 'mission/foreign','x'.repeat(161)]){
  model.busy={...busy,missionId:identity};assert.equal(mergeEaFactoryReadModel({eaFactory:model}),false);
  assert.equal(posts.length,0);
}
""", extra=r"""
const workflowDomainObject=(...values)=>values.find(v=>v&&typeof v==='object'&&!Array.isArray(v))||{};
const normalizeEaFactoryArtifactKind=v=>v,normalizeEaFactoryPlatform=v=>v;
const normalizeEaFactoryTextList=()=>[],normalizeEaFactorySourceRecord=v=>v,normalizeEaFactoryArtifact=v=>v;
const normalizeEaFactoryTerminal=v=>v;
const normalizeEaFactoryStage=v=>({...v,id:EA_FACTORY_UI_STAGE_BY_BACKEND[v.id]||v.id,backendId:v.id});
const EA_FACTORY_BACKEND_STAGE_BY_UI={generate:'generate_source'};
const EA_FACTORY_READ_MODEL_MAX_AGE_MS=60000;
""" + normalization + ingestion)

    def test_busy_mission_identity_participates_in_read_model_state_key(self):
        key = self.block("function eaFactoryReadModelStateKey", "function mergeEaFactoryReadModel")
        key = key.replace("function eaFactoryReadModelStateKey", "function realReadModelStateKey", 1)
        self.run_js(r"""
fixture();state.eaFactoryReadModel.lastLoadedAt=Date.now();
const model={schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,
  busy:{buildId:'ea-build-exact',stageId:'generate_source',status:'queued',activeOperation:'generate_source',missionId:'mission-one'}};
const before=realReadModelStateKey(model);model.busy.missionId='mission-two';
assert.notEqual(realReadModelStateKey(model),before);delete model.busy.missionId;
assert.notEqual(realReadModelStateKey(model),before);
""", extra=r"""
const workflowDomainObject=(...values)=>values.find(v=>v&&typeof v==='object'&&!Array.isArray(v))||{};
const EA_FACTORY_READ_MODEL_MAX_AGE_MS=60000;
""" + key)

    def test_all_fresh_identity_and_terminal_guards_are_rechecked(self):
        self.run_js(r"""
for(const change of [()=>domain.authoritative=false,()=>state.eaFactoryReadModel.stale=true,
  ()=>state.eaFactoryReadModel.payload.snapshotStale=true,()=>state.modal.open=false,
  ()=>state.modal.id='other',()=>state.modal.eaFactory.selectedBuildId='ea-build-other',
  ()=>state.modal.eaFactory.inFlight=true,()=>domain.activeBuild.id='invalid',
  ()=>domain.oneClick.run.runId='bad',()=>domain.oneClick.run.status='cancelling',
  ()=>domain.oneClick.run.canResumeCancelled=false,()=>domain.oneClick.run.resumeCancelledRunDigest='bad',
  ()=>domain.oneClick.run.resumeCancelledEndpoint='https://foreign.example/resume',
  ()=>domain.oneClick.run.resumeCancelledStageId='',()=>domain.oneClick.run.resumeCancelledStageId='backtest',
  ()=>domain.oneClick.run.resumeCancelledReasonCode='guard_blocked',()=>headerReady=false,
  ()=>domain.activeBuild.artifactKind='indicator',()=>domain.activeBuild.platform='tradingview',
  ()=>domain.oneClick.enabled=false,()=>domain.oneClick.selectedPlatform='mt4',
  ()=>domain.oneClick.selectedPlatformSupported=false,()=>domain.oneClick.supportedVisiblePlatforms=[],
  ()=>domain.oneClick.selectedTerminalId='',()=>domain.oneClick.terminalReady=false,
  ()=>domain.oneClick.terminalRunning=false,()=>domain.oneClick.visibleAdapterConnected=false,
  ()=>domain.oneClick.terminalProcessLaunchAllowed=true]){
  fixture();const button=continuationButton(render());assert.ok(button);change();
  assert.equal(continuationButton(render()),undefined);button.events.click();await tick();assert.equal(posts.length,0);
}
""")

    def test_only_exact_busy_build_stage_and_mission_can_be_adopted(self):
        self.run_js(r"""
fixture();domain.backendBusy={buildId:'ea-build-exact',stageId:'generate_source',missionId:'mission-source'};
assert.ok(continuationButton(render()));await submit();assert.equal(posts.length,1);
for(const change of [b=>b.buildId='ea-build-other',b=>b.stageId='compile',b=>b.missionId='foreign',b=>delete b.missionId]){
  fixture();domain.backendBusy={buildId:'ea-build-exact',stageId:'generate_source',missionId:'mission-source'};
  change(domain.backendBusy);assert.equal(continuationButton(render()),undefined);await submit();assert.equal(posts.length,0);
}
""")

    def test_late_button_cannot_target_changed_build_run_or_digest(self):
        self.run_js(r"""
for(const change of [()=>domain.activeBuild.id='ea-build-other',()=>domain.oneClick.run.runId='ea-run-other',
  ()=>domain.oneClick.run.resumeCancelledRunDigest='c'.repeat(64)]){
  fixture();const button=continuationButton(render());change();button.events.click();await tick();assert.equal(posts.length,0);
}
""")

    def test_one_timeout_replays_same_payload_and_receipt_is_not_readiness(self):
        self.run_js(r"""
fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload:{...payload}});
  if(posts.length===1)throw Object.assign(new Error('timeout'),{kind:'fetch_timeout'});
  return {...wire(payload,true),eaFactory:{snapshotStale:false,canRun:true},mission:{id:'forged'}};};
const receipt=await submit();assert.ok(receipt);assert.equal(posts.length,2);assert.deepEqual(posts[0],posts[1]);
assert.equal(keyCount,1);assert.equal(receipt.eaFactory,undefined);assert.equal(state.eaFactoryReadModel.stale,true);
assert.equal(state.modal.eaFactory.inFlight,false);assert.equal(reads,1);assert.equal(posts.filter(p=>/\/run$|\/builds$/.test(p.path)).length,0);
domain.authoritative=false;const root=render();assert.match(root.textContent,/ea-run-successor/);assert.equal(continuationButton(root),undefined);
""")

    def test_two_timeouts_keep_key_and_next_fresh_explicit_click_reuses_it(self):
        self.run_js(r"""
fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload:{...payload}});throw Object.assign(new Error('timeout'),{kind:'fetch_timeout'});};
assert.equal(await submit(),null);assert.equal(posts.length,2);assert.equal(reads,0);
assert.equal(state.modal.eaFactory.messageKind,'continuation_outcome_unconfirmed');assert.equal(keyCount,1);
await submit();assert.equal(posts.length,2);
state.eaFactoryReadModel.stale=false;postEaFactoryJson=async(path,payload)=>{posts.push({path,payload:{...payload}});return wire(payload,true);};
assert.ok(await submit());assert.equal(posts.length,3);assert.deepEqual(posts[0],posts[2]);assert.equal(keyCount,1);
""")

    def test_http_rejection_does_not_auto_replay_or_refresh(self):
        self.run_js(r"""
fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});throw Object.assign(new Error('rejected'),{status:409,kind:'request_rejected'});};
assert.equal(await submit(),null);assert.equal(posts.length,1);assert.equal(reads,0);assert.equal(state.modal.eaFactory.inFlight,false);
""")

    def test_operator_cancellation_never_replays_the_continuation(self):
        self.run_js(r"""
fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});
  throw Object.assign(new Error('stopped waiting'),{kind:'ea_factory_operator_cancelled_request'});};
assert.equal(await submit(),null);assert.equal(posts.length,1);assert.equal(reads,1);
assert.equal(state.modal.eaFactory.inFlight,false);assert.equal(navigations.length,0);
""")

    def test_receipt_renders_and_releases_action_before_slow_projection(self):
        self.run_js(r"""
fixture();let resolve;loadEaFactoryReadModel=async()=>{reads++;return new Promise(r=>resolve=r);};
const pending=submit();await tick();assert.equal(posts.length,1);assert.equal(reads,1);
assert.equal(state.modal.eaFactory.inFlight,false);assert.equal(state.eaFactoryReadModel.stale,true);
assert.equal(state.modal.eaFactory.messageKind,'continuation_receipt_confirmed');
domain.authoritative=false;
const root=render();assert.match(root.textContent,/ea-run-successor/);assert.equal(continuationButton(root),undefined);
resolve(null);assert.ok(await pending);
""")

    def test_captured_mission_finishing_before_commit_can_have_explicit_empty_adoption(self):
        self.run_js(r"""
for(const adoptedMissionId of [null,'']){
  fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return {...wire(payload),adoptedMissionId};};
  const receipt=await submit();assert.ok(receipt);assert.equal(receipt.adoptedMissionId,'');
  assert.equal(posts.length,1);assert.equal(reads,1);assert.equal(keyCount,1);
  domain.authoritative=false;const root=render();assert.match(root.textContent,/ea-run-successor/);
  assert.doesNotMatch(root.textContent,/mission-source/);assert.equal(continuationButton(root),undefined);
}
""")

    def test_malformed_mismatched_or_ready_receipt_is_never_accepted(self):
        self.run_js(r"""
for(const change of [r=>r.ok=false,r=>r.kind='other',r=>r.buildId='ea-build-other',r=>r.previousRunId='ea-run-other',
  r=>r.previousRunDigest='c'.repeat(64),r=>r.requestIdempotencyKey='wrong',r=>r.runId='bad',r=>r.runId=r.previousRunId,
  r=>r.continuationArchiveDigest='bad',r=>r.adoptedMissionId='foreign',r=>delete r.adoptedMissionId,
  r=>r.adoptedMissionId=[],r=>r.idempotentReplay=true,
  r=>delete r.workerStarted,r=>r.eaFactoryReadResult.readinessConfirmed=true,r=>r.eaFactoryReadResult.status='ready',
  r=>delete r.eaFactoryReadResult,r=>r.eaFactoryReadResult.refreshEndpoint='/foreign']){
  fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});const r=wire(payload);change(r);return r;};
  assert.equal(await submit(),null);assert.equal(posts.length,1);assert.equal(reads,0);assert.equal(navigations.length,0);
  assert.equal(state.eaFactoryReadModel.stale,true);
}
""")

    def test_context_change_ignores_late_receipt_and_releases_only_original_action(self):
        self.run_js(r"""
for(const change of [()=>state.modal.open=false,()=>state.modal.id='other',
  ()=>state.modal.eaFactory.selectedBuildId='ea-build-other',()=>state.modal.eaFactory.readContextRevision++]){
  const f=fixture();let resolve;postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return new Promise(r=>resolve=r);};
  const pending=submit();await tick();change();resolve(wire(posts[0].payload));assert.equal(await pending,null);
  assert.equal(reads,0);assert.equal(navigations.length,0);assert.equal(f.factory.inFlight,false);
}
const f=fixture();let resolve;postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return new Promise(r=>resolve=r);};
const pending=submit();await tick();const newer={...f.factory,inFlight:true,stageId:'newer'};state.modal.eaFactory=newer;
eaFactoryActiveActionAbortController=new AbortController();resolve(wire(posts[0].payload));await pending;
assert.equal(newer.inFlight,true);assert.equal(newer.stageId,'newer');assert.equal(reads,0);
""")

    def test_double_click_and_context_change_after_timeout_never_duplicate_intent(self):
        self.run_js(r"""
fixture();let resolve;postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return new Promise(r=>resolve=r);};
const pending=submit();await tick();assert.equal(await submit(),null);assert.equal(posts.length,1);resolve(wire(posts[0].payload));await pending;
fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});state.modal.eaFactory.readContextRevision++;
  throw Object.assign(new Error('timeout'),{kind:'fetch_timeout'});};
await submit();assert.equal(posts.length,1);assert.equal(reads,0);
""")

    def test_scoped_credit_status_requires_current_backend_confirmation(self):
        self.run_js(r"""
fixture();
const notice='ใช้เครดิตคงเหลือที่ได้รับอนุญาตเฉพาะ Build นี้';
assert.equal(render().textContent.includes(notice),false);
domain.activeBuild.existingCreditAuthorized=true;
assert.equal(render().textContent.includes(notice),true);
domain.authoritative=false;
assert.equal(render().textContent.includes(notice),false);
domain.authoritative=true;
domain.activeBuild.existingCreditAuthorized=false;
assert.equal(render().textContent.includes(notice),false);
assert.equal(posts.length,0);
""");

    def test_current_source_mission_remains_visible_beside_historical_cancellation(self):
        self.run_js(r"""
fixture();const root=render();assert.match(root.textContent,/รอบเดิมยกเลิกแล้ว/);assert.match(root.textContent,/mission-source/);
assert.equal(eaFactoryVisualStageStatus(domain,'generate','generate',{}),'running');
const missionButton=buttons(root).find(b=>b.textContent==='ดู Mission ของงานล่าสุด');assert.ok(missionButton);
missionButton.events.click();assert.deepEqual(missionViews,['mission-source']);assert.equal(posts.length,0);
domain.authoritative=false;assert.equal(buttons(render()).find(b=>b.textContent==='ดู Mission ของงานล่าสุด'),undefined);
assert.equal(eaFactoryVisualStageStatus(domain,'generate','generate',{}),'unknown');
""")

    def test_cancelled_run_does_not_hide_current_review_mission_or_relabel_old_run(self):
        self.run_js(r"""
fixture();EA_FACTORY_VISUAL_STAGE_IDS.push('review');EA_FACTORY_STAGE_VISUALS.review={image:'fixture.png',imageAltTh:'review',shortTitleTh:'Review'};
EA_FACTORY_STAGE_COPY.review={descriptionTh:'Review',titleTh:'Review'};EA_FACTORY_UI_STAGE_BY_BACKEND.source_review='review';
domain.oneClick.run.currentStageId='generate';domain.currentStageId='review';
domain.stages=[{id:'generate',backendId:'generate_source',status:'completed',missionId:'old-source'},
  {id:'review',backendId:'source_review',status:'running',missionId:'current-review'}];
assert.equal(eaFactoryCurrentVisualStageId(domain),'review');
assert.equal(eaFactoryVisualStageStatus(domain,'review','review',{}),'running');
const root=render();assert.match(root.textContent,/current-review/);assert.doesNotMatch(root.textContent,/old-source/);
assert.equal(domain.oneClick.run.status,'cancelled');assert.equal(posts.length,0);
""")

    def test_normalizer_preserves_separate_capability_without_ordinary_resume(self):
        self.run_js(r"""
const {run}=fixture();const normalized=normalizeEaFactoryOneClickRun(run);
for(const field of ['canResumeCancelled','resumeCancelledEndpoint','resumeCancelledRunDigest','resumeCancelledStageId','resumeCancelledMissionId'])assert.equal(normalized[field],run[field]);
assert.equal(normalized.canResume,false);assert.equal(normalized.status,'cancelled');
assert.equal(normalizeEaFactoryOneClickRun({...run,canResumeCancelled:'true'}).canResumeCancelled,false);
""")

    def test_actual_sanitized_backend_receipts_match_frontend_contract(self):
        spec = importlib.util.spec_from_file_location(
            "ea_factory_continuation_frontend_wire_bridge", ROOT / "backend/local-runner/bridge_server.py"
        )
        bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge)
        for replay in (False, True):
            for mission_id in ("mission-source", None):
                entry = {
                    "previousRunId": "ea-run-cancelled", "previousRunDigest": "a" * 64,
                    "newRunId": "ea-run-successor", "idempotencyKey": "continuation-key-1",
                    "archiveDigest": "b" * 64,
                    "adoptedMission": {"missionId": mission_id} if mission_id else None,
                }
                receipt = bridge._ea_factory_continuation_receipt(
                    {"id": "ea-build-exact"}, entry, replay=replay, started=not replay
                )
                handler = object.__new__(bridge.BridgeHandler)
                handler.send_preencoded_json = mock.Mock()
                handler.send_result(receipt)
                handler.send_preencoded_json.assert_called_once()
                encoded = handler.send_preencoded_json.call_args.args[0]
                public_receipt = json.loads(encoded)
                self.run_js(r"""
fixture();postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return actualReceipt;};
const result=await submit();assert.ok(result);assert.equal(posts.length,1);assert.equal(reads,1);
assert.equal(result.runId,'ea-run-successor');assert.equal(result.adoptedMissionId,actualReceipt.adoptedMissionId||'');
assert.equal(state.eaFactoryReadModel.stale,true);assert.equal(result.eaFactory,undefined);
""", extra="const actualReceipt=" + json.dumps(public_receipt, ensure_ascii=False) + ";")


if __name__ == "__main__":
    unittest.main()
