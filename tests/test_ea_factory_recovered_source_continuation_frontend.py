"""Recovered Source uses the exact existing Run without promoting old failure to AI success."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RecoveredSourceContinuationFrontendTests(unittest.TestCase):
    def run_js(self, body):
        main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        def block(start, end):
            offset = main.index(start)
            return main[offset:main.index(end, offset)]
        support = r'''
const assert=require('node:assert/strict');
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.events={};this.attrs={};this._text='';}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+' '+this.children.map(x=>x.textContent||'').join(' ');}
 append(...items){this.children.push(...items);} appendChild(item){this.children.push(item);return item;}
 setAttribute(k,v){this.attrs[k]=v;} addEventListener(k,v){this.events[k]=v;}
}
const document={createElement:tag=>new Element(tag)};
const EA_FACTORY_PROP_ID='right_server_racks';
const EA_FACTORY_VISUAL_STAGE_IDS=['generate','review'];
const EA_FACTORY_UI_STAGE_BY_BACKEND={generate_source:'generate',source_review:'review'};
const EA_FACTORY_STAGE_VISUALS={generate:{shortTitleTh:'AI สร้าง Source',image:'source.png'},review:{shortTitleTh:'ตรวจโค้ด',image:'review.png'}};
EA_FACTORY_STAGE_VISUALS.artifacts_report={shortTitleTh:'จัดเตรียมไฟล์',image:'result.png'};
const EA_FACTORY_STAGE_COPY={generate:{descriptionTh:'สร้าง Source'},review:{descriptionTh:'ตรวจ Source'}};
let state,domain,posts,headerReady,pendingResponse;
const safeDashboardDisplayText=(v,f='')=>v||f;
const eaFactoryPlatformLabel=v=>v,eaFactoryArtifactKindLabel=v=>v;
const eaFactoryStageStatusLabel=v=>v;
const eaFactoryCertifiedDeliveryCompleted=d=>d.deliveryCompleted===true;
const eaFactoryOneClickStageStatus=(d,id)=>d.stages.find(s=>s.id===id)?.status||'pending';
const eaFactoryPhaseGateProgress=()=>({status:domain.oneClick.run.status,active:false,waiting:false,determinate:true,percent:20});
const eaFactoryCancelledContinuationAdmission=()=>({canSubmit:false,canSelect:false});
const eaFactoryTopHeaderLockPreflight=()=>({ready:headerReady});
const rejectEaFactoryMissingTopHeaderLocks=()=>!headerReady;
const createEaFactoryPageNavigation=(label)=>{const e=new Element('button');e.textContent=label;return e;};
const createEaFactoryStopButton=()=>new Element('button');
const renderEaFactoryExistingBuildPicker=()=>{};
const appendDashboardArtifactLinks=()=>false;
const createWorkflowTruthEmpty=text=>{const e=new Element('p');e.textContent=text;return e;};
const refreshEaFactoryProgressStatus=()=>{},restartEaFactoryBacktestOnly=()=>{},resumeEaFactoryCancelledRun=()=>{};
const getModalSubject=()=>({}),getPropertyRole=()=>({});
const normalizeWorkflowDashboard=()=>({domainData:{eaFactory:domain}});
const setEaFactoryActionState=next=>Object.assign(state.modal.eaFactory,next);
const eaFactoryReadModelStateKey=()=>'';
const createWorkflowIdempotencyKey=()=>{throw Error('must reuse original key');};
const postEaFactoryJson=async(endpoint,payload)=>{posts.push({endpoint,payload});if(pendingResponse)await pendingResponse;return {ok:true};};
const runEaFactoryRequest=async(_stage,fn)=>{if(state.modal.eaFactory.inFlight)return null;state.modal.eaFactory.inFlight=true;try{return await fn();}finally{state.modal.eaFactory.inFlight=false;}};
function fixture(){
 posts=[];pendingResponse=null;headerReady=true;
 state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{selectedBuildId:'ea-build-one',inFlight:false,readContextRevision:7,cancelledContinuationIntents:{}}},eaFactoryReadModel:{stale:false,payload:{snapshotStale:false}},propReports:{}};
 const suffix='a'.repeat(24),sourceDigest='b'.repeat(64);
 const run={runId:'ea-run-existing',idempotencyKey:'wf-original-same-run',status:'failed',currentStageId:'generate',failureCode:'invalid_output',canRetry:false};
 const raw={id:'ea-build-one',oneClickRun:{...run,currentStageId:'generate_source',visibleAction:null},
 sourceRecovery:{reasonCode:'source_recovery_already_recorded',strategySpecDigest:'c'.repeat(64),history:[{recoveryId:'ea-source-recovery-'+suffix,recoveryMissionId:'mission-eaf-recovery-'+suffix,reportId:'report-eaf-recovery-'+suffix,sourceDigest,previousRunDigest:'d'.repeat(64),sourceOrigin:'operator_recovery',aiExecuted:false,nextStageId:'source_review'}]},
 stages:[{id:'generate_source',status:'completed',evidenceVerified:true,missionId:'mission-eaf-recovery-'+suffix,reportId:'report-eaf-recovery-'+suffix},{id:'source_review',status:'pending',canAdvance:true}],
 versions:[{immutable:true,sourceDigest,sourceReportId:'report-eaf-recovery-'+suffix}]};
 domain={authoritative:true,backendBusy:null,activeBuild:{id:raw.id,platform:'mt5',artifactKind:'expert_advisor',raw,oneClickRun:run},currentStageId:'review',
 stages:[{id:'generate',backendId:'generate_source',status:'completed'},{id:'review',backendId:'source_review',status:'pending',canRun:true}],
 oneClick:{run,enabled:true,canRun:false,canRetry:false,canResume:false,selectedPlatform:'mt5',selectedPlatformSupported:true,supportedVisiblePlatforms:['mt5'],selectedTerminalId:'mtc-one',terminalReady:true,terminalRunning:true,visibleAdapterConnected:true,terminalProcessLaunchAllowed:false}};
}
const descendants=e=>[e,...e.children.flatMap(descendants)];
const render=()=>{const e=new Element('main');renderEaFactoryGameProgressPanel(e,domain);return e;};
const renderResult=()=>{const e=new Element('main');renderEaFactoryResultPage(e,domain);return e;};
const continueButton=e=>descendants(e).find(x=>x.tag==='button'&&x.textContent.trim()==='ตรวจ Source ที่แก้แล้วและทำต่อ');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
'''
        parts = [support,
                 block("function eaFactoryExistingOneClickAdmission", "function renderEaFactoryOneClickPanel"),
                 block("function eaFactoryCurrentVisualStageId", "function eaFactoryCancelledContinuationAdmission"),
                 block("function renderEaFactoryGameProgressPanel", "function renderEaFactoryOneClickSetup"),
                 block("function renderEaFactoryResultPage", "function renderEaFactoryPanel"),
                 block("function eaFactoryOneClickRequestKey", "function eaFactoryBacktestRestartRequestKey"),
                 block("async function runEaFactoryOneClick", "function cancelEaFactorySubmittingRequest"),
                 "(async()=>{" + body + "})().catch(e=>{console.error(e);process.exitCode=1;});"]
        node = shutil.which("node") or str(Path.home()/".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")
        result = subprocess.run([node, "-"], input="\n".join(parts), cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_verified_recovery_renders_truthfully_and_reuses_same_run_key(self):
        self.run_js(r'''
fixture();const snapshot=JSON.stringify(domain.activeBuild.raw);const view=render();
assert.equal(eaFactoryCurrentVisualStageId(domain),'review');
assert(view.textContent.includes('Source ที่ผู้พัฒนาแก้ไข'));
assert(view.textContent.includes('เก็บผล AI ที่ไม่ผ่านและ Retry เดิม'));
assert(!view.textContent.includes('กลับไปตั้งค่างานหน้า 1'));
const button=continueButton(view);assert(button);button.events.click();await tick();
assert.deepEqual(posts,[{endpoint:'/api/props/right_server_racks/ea-factory/builds/ea-build-one/run',payload:{idempotencyKey:'wf-original-same-run'}}]);
assert.equal(JSON.stringify(domain.activeBuild.raw),snapshot);
''')

    def test_failed_generation_without_verified_recovery_stays_blocked(self):
        self.run_js(r'''
for(const mutate of [()=>delete domain.activeBuild.raw.sourceRecovery,
 ()=>domain.activeBuild.raw.sourceRecovery.reasonCode='operator_source_recovery_available',
 ()=>domain.activeBuild.raw.stages[0].status='failed',()=>domain.activeBuild.raw.stages[0].evidenceVerified=false,
 ()=>domain.activeBuild.raw.versions=[],()=>domain.activeBuild.raw.sourceRecovery.history[0].aiExecuted=true]){
 fixture();mutate();assert.equal(eaFactoryExistingOneClickAdmission(domain).canSubmit,false);
 assert(!continueButton(render()));await runEaFactoryOneClick('ea-build-one');assert.equal(posts.length,0);
}
''')

    def test_stale_modal_header_busy_and_terminal_changes_cannot_continue(self):
        self.run_js(r'''
for(const mutate of [()=>domain.authoritative=false,()=>state.eaFactoryReadModel.stale=true,
 ()=>state.eaFactoryReadModel.payload.snapshotStale=true,()=>state.modal.open=false,()=>state.modal.id='other',
 ()=>state.modal.eaFactory.selectedBuildId='ea-build-other',()=>state.modal.eaFactory.inFlight=true,
 ()=>headerReady=false,()=>domain.backendBusy={buildId:'ea-build-one'},()=>domain.oneClick.terminalReady=false,
 ()=>domain.oneClick.terminalRunning=false,()=>domain.oneClick.visibleAdapterConnected=false,
 ()=>domain.oneClick.terminalProcessLaunchAllowed=true,()=>domain.oneClick.selectedPlatform='mt4',
 ()=>domain.oneClick.supportedVisiblePlatforms=[],()=>domain.oneClick.enabled=false]){
 fixture();const button=continueButton(render());assert(button);mutate();button.events.click();await tick();assert.equal(posts.length,0);
}
''')

    def test_recovery_digest_identity_and_next_stage_are_required(self):
        self.run_js(r'''
for(const mutate of [()=>domain.activeBuild.raw.id='ea-build-other',()=>domain.activeBuild.raw.sourceRecovery.strategySpecDigest='invalid',
 ()=>domain.activeBuild.raw.sourceRecovery.history.push({...domain.activeBuild.raw.sourceRecovery.history[0]}),
 ()=>domain.activeBuild.raw.sourceRecovery.history[0].sourceOrigin='ai',()=>domain.activeBuild.raw.sourceRecovery.history[0].sourceDigest='f'.repeat(64),
 ()=>domain.activeBuild.raw.stages[0].missionId='mission-other',()=>domain.activeBuild.raw.stages[0].reportId='report-other',
 ()=>domain.activeBuild.raw.versions[0].immutable=false,()=>domain.activeBuild.raw.versions[0].sourceReportId='report-other',
 ()=>domain.activeBuild.raw.stages[1].canAdvance=false,()=>domain.activeBuild.raw.stages[1].status='running',
 ()=>domain.activeBuild.raw.oneClickRun.visibleAction={},()=>domain.activeBuild.raw.oneClickRun.runId='ea-run-other',
 ()=>domain.activeBuild.raw.oneClickRun.idempotencyKey='wf-other-key']){
 fixture();const button=continueButton(render());mutate();assert.equal(eaFactoryExistingOneClickAdmission(domain).canSubmit,false);
 button.events.click();await tick();assert.equal(posts.length,0);
}
''')

    def test_rendered_intent_is_rejected_after_valid_context_changes(self):
        self.run_js(r'''
for(const mutate of [()=>state.modal.eaFactory.readContextRevision++,()=>{
 const raw=domain.activeBuild.raw;raw.sourceRecovery.history[0].sourceDigest='e'.repeat(64);raw.versions[0].sourceDigest='e'.repeat(64);
},()=>domain.activeBuild.raw.sourceRecovery.strategySpecDigest='f'.repeat(64),()=>{
 domain.oneClick.run.runId='ea-run-other';domain.activeBuild.raw.oneClickRun.runId='ea-run-other';
}]){
 fixture();const button=continueButton(render());mutate();domain.oneClick.canRetry=true;
 button.events.click();await tick();assert.equal(posts.length,0);
}
''')

    def test_triple_click_preserves_pending_lock_and_never_duplicates_request(self):
        self.run_js(r'''
fixture();await runEaFactoryOneClick('ea-build-one');assert.equal(posts.length,0);
let release;pendingResponse=new Promise(resolve=>release=resolve);
const button=continueButton(render());button.events.click();await tick();assert.equal(posts.length,1);
assert.equal(state.modal.eaFactory.inFlight,true);
const pendingState=JSON.stringify(state.modal.eaFactory);
button.events.click();await tick();assert.equal(state.modal.eaFactory.inFlight,true);
assert.equal(JSON.stringify(state.modal.eaFactory),pendingState);
button.events.click();await tick();assert.equal(posts.length,1);assert.equal(state.modal.eaFactory.inFlight,true);
assert.equal(JSON.stringify(state.modal.eaFactory),pendingState);
release();await tick();assert.equal(posts.length,1);assert.equal(state.modal.eaFactory.inFlight,false);
''')

    def test_inflight_request_is_not_reset_by_unsigned_or_invalid_preflight(self):
        self.run_js(r'''
fixture();state.modal.eaFactory.inFlight=true;state.modal.eaFactory.stageId='one_click_run';
state.modal.eaFactory.message='existing request in progress';const pendingState=JSON.stringify(state.modal.eaFactory);
await runEaFactoryOneClick('ea-build-one');await runEaFactoryOneClick('invalid build id');
assert.equal(posts.length,0);assert.equal(JSON.stringify(state.modal.eaFactory),pendingState);
''')

    def test_later_run_keeps_operator_source_label_without_resume_action(self):
        self.run_js(r'''
fixture();Object.assign(domain.oneClick.run,{status:'running',currentStageId:'review'});
Object.assign(domain.activeBuild.raw.oneClickRun,{status:'running',currentStageId:'source_review'});
domain.activeBuild.raw.stages[1].status='running';domain.activeBuild.raw.stages[1].canAdvance=false;
const view=render();assert(view.textContent.includes('Source ที่ผู้พัฒนาแก้ไข'));assert(!continueButton(view));assert.equal(posts.length,0);
''')

    def test_completed_result_labels_verified_recovered_source_without_claiming_ai_success(self):
        self.run_js(r'''
fixture();domain.deliveryCompleted=true;
Object.assign(domain.oneClick.run,{status:'completed',currentStageId:'artifacts_report'});
Object.assign(domain.activeBuild.raw.oneClickRun,{status:'completed',currentStageId:'final_report'});
domain.stages.forEach(stage=>stage.status='completed');
domain.activeBuild.raw.stages[1].status='completed';domain.activeBuild.raw.stages[1].canAdvance=false;
const before=JSON.stringify(domain),view=renderResult();
assert(view.textContent.includes('สร้างและตรวจสอบเสร็จแล้ว'));
assert(view.textContent.includes('Source ที่ผู้พัฒนาแก้ไข'));
assert(!view.textContent.includes('AI สร้าง Source'));
assert(view.textContent.includes('ตรวจโค้ด'));
assert.equal(descendants(view).find(node=>node.tag==='img').alt,'ไฟล์และรายงานจาก Build ที่ตรวจสอบเสร็จแล้ว');
assert.equal(JSON.stringify(domain),before);assert.equal(posts.length,0);
''')

    def test_result_source_label_requires_existing_verified_recovery_provenance(self):
        self.run_js(r'''
for(const mutate of [()=>delete domain.activeBuild.raw.sourceRecovery,
 ()=>domain.activeBuild.raw.sourceRecovery.history[0].aiExecuted=true,
 ()=>domain.activeBuild.raw.sourceRecovery.history[0].sourceOrigin='ai',
 ()=>domain.activeBuild.raw.sourceRecovery.history[0].sourceDigest='f'.repeat(64),
 ()=>domain.activeBuild.raw.versions[0].immutable=false,
 ()=>domain.activeBuild.raw.stages[0].evidenceVerified=false,
 ()=>domain.authoritative=false,()=>state.eaFactoryReadModel.stale=true,
 ()=>state.eaFactoryReadModel.payload.snapshotStale=true]){
 fixture();domain.deliveryCompleted=true;domain.oneClick.run.status='completed';mutate();
 const before=JSON.stringify(domain),view=renderResult();
 assert(!view.textContent.includes('Source ที่ผู้พัฒนาแก้ไข'));
 assert(view.textContent.includes('AI สร้าง Source'));
 assert.equal(JSON.stringify(domain),before);assert.equal(posts.length,0);
}
''')

    def test_later_compile_resume_and_stage_retry_use_normal_admission(self):
        self.run_js(r'''
for(const status of ['awaiting_visible_terminal','failed']){
 fixture();Object.assign(domain.oneClick.run,{status,currentStageId:'compile_validate'});
 Object.assign(domain.activeBuild.raw.oneClickRun,{status,currentStageId:'compile_validate'});
 domain.activeBuild.raw.stages[1].status='completed';domain.activeBuild.raw.stages[1].canAdvance=false;
 domain.currentStageId='compile_validate';domain.stages.push({id:'compile_validate',status:status==='failed'?'failed':'pending'});
 domain.oneClick.canResume=status==='awaiting_visible_terminal';domain.oneClick.canRetry=status==='failed';
 const admission=eaFactoryExistingOneClickAdmission(domain);
 assert.equal(admission.canSubmit,true);assert.equal(admission.recoveredSource,false);assert.equal(admission.recoverySignature,'');
 const view=render();assert(view.textContent.includes('Source ที่ผู้พัฒนาแก้ไข'));assert(!continueButton(view));
 const label=status==='failed'?'ลองใหม่จากขั้นที่ติดขัด':'ทำขั้นนี้ต่อ';
 const button=descendants(view).find(x=>x.tag==='button'&&x.textContent.trim()===label);assert(button);
 button.events.click();await tick();assert.deepEqual(posts,[{endpoint:'/api/props/right_server_racks/ea-factory/builds/ea-build-one/run',payload:{idempotencyKey:'wf-original-same-run'}}]);
}
''')

    def test_later_compile_resume_retains_normal_header_and_terminal_guards(self):
        self.run_js(r'''
for(const mutate of [()=>headerReady=false,()=>domain.oneClick.terminalReady=false,()=>domain.authoritative=false,
 ()=>state.modal.eaFactory.inFlight=true,()=>domain.backendBusy={buildId:'ea-build-one'}]){
 fixture();Object.assign(domain.oneClick.run,{status:'awaiting_visible_terminal',currentStageId:'compile_validate'});
 Object.assign(domain.activeBuild.raw.oneClickRun,{status:'awaiting_visible_terminal',currentStageId:'compile_validate'});
 domain.oneClick.canResume=true;domain.currentStageId='compile_validate';
 const button=descendants(render()).find(x=>x.tag==='button'&&x.textContent.trim()==='ทำขั้นนี้ต่อ');assert(button);
 mutate();button.events.click();await tick();assert.equal(posts.length,0);
}
''')


if __name__ == "__main__":
    unittest.main()
