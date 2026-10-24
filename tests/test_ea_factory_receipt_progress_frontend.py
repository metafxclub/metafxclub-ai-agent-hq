"""Exercise shipped receipt/progress renderers and normal exact-Build Run guards."""
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryReceiptProgressFrontendTests(unittest.TestCase):
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
const window={location:new URL('http://127.0.0.1:4186/frontend/index.html')};
const EA_FACTORY_PROP_ID='right_server_racks';
const EA_FACTORY_VISUAL_STAGE_IDS=['generate'];
const EA_FACTORY_STAGE_VISUALS={generate:{image:'fixture.png',imageAltTh:'source',shortTitleTh:'สร้าง Source'}};
EA_FACTORY_STAGE_VISUALS.artifacts_report=EA_FACTORY_STAGE_VISUALS.generate;
const EA_FACTORY_STAGE_COPY={generate:{descriptionTh:'กำลังเขียน Source'}};
const EA_FACTORY_SUPPORTED_MODES=new Set(['one_click_with_manual_stage_recovery']);
let state,domain,posts,refreshes,navigations,renders,headerReady,eaFactoryActiveActionAbortController;
const safeDashboardDisplayText=(v,f='')=>v||f;
const eaFactoryPlatformLabel=v=>v,eaFactoryArtifactKindLabel=v=>v;
const eaFactoryCurrentVisualStageId=()=> 'generate';
const eaFactoryPhaseGateProgress=d=>({status:d.oneClick?.run?.status||'idle',active:['running','queued','waiting_ai','cancelling'].includes(d.oneClick?.run?.status),waiting:false,determinate:true,percent:0,currentStageLabel:'Source'});
const eaFactoryVisualStageStatus=()=> 'pending',eaFactoryVisualStageStatusLabel=v=>v;
const createWorkflowTruthEmpty=text=>{const x=new Element('p');x.textContent=text;return x;};
const createEaFactoryStopButton=()=>{const x=new Element('button');x.textContent='หยุด';return x;};
const createEaFactoryPageNavigation=(label,page)=>{const x=new Element('button');x.textContent=label;x.addEventListener('click',()=>navigations.push(page));return x;};
const refreshEaFactoryProgressStatus=async()=>{refreshes++;};
const restartEaFactoryBacktestOnly=async()=>{throw Error('unexpected backtest restart');};
const eaFactoryTopHeaderLockPreflight=()=>({ready:headerReady});
const rejectEaFactoryMissingTopHeaderLocks=()=>!headerReady;
const eaFactoryOneClickRequestKey=id=>`exact-run-key-${id}`;
const getModalSubject=()=>({id:EA_FACTORY_PROP_ID}),getPropertyRole=()=>({});
const normalizeWorkflowDashboard=()=>({domainData:{eaFactory:domain}});
const renderWorkflowDashboard=()=>{renders++;};
const setEaFactoryActionState=next=>Object.assign(state.modal.eaFactory,next);
const eaFactoryReadModelStateKey=v=>JSON.stringify(v);
const mergeBackendMission=()=>{},mergeEaFactoryResponseReport=()=>{},mergeEaFactoryReadModel=()=>true;
const loadEaFactoryReadModel=async()=>null;
const eaFactoryActionPresentation=(_d,action)=>action;
const postEaFactoryJson=async(path,payload)=>{posts.push({path,payload});return {ok:true};};
function fixture(){
  posts=[];refreshes=0;navigations=[];renders=0;headerReady=true;eaFactoryActiveActionAbortController=null;
  state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{inFlight:false,stageId:'read_model',messageKind:'timeout',message:'Backend ตอบกลับเกิน 20 วินาที',selectedBuildId:'ea-build-exact',confirmedCreateBuildId:'ea-build-exact'}},propReports:{},eaFactoryReadModel:{payload:{},stale:false}};
  domain={authoritative:true,backendBusy:null,activeBuild:{id:'ea-build-exact',platform:'mt5',artifactKind:'expert_advisor',sourceDisplayName:'Alexander'},currentStageId:'generate_source',stages:[{id:'generate_source',status:'pending'}],oneClick:{enabled:true,canRun:true,canRetry:false,canResume:false,selectedTerminalId:'terminal-a',selectedPlatform:'mt5',selectedPlatformSupported:true,supportedVisiblePlatforms:['mt5'],terminalReady:true,terminalRunning:true,visibleAdapterConnected:true,terminalProcessLaunchAllowed:false,run:{status:'idle'}}};
  return domain;
}
const all=e=>[e,...e.children.flatMap(c=>c instanceof Element?all(c):[])];
const buttons=e=>all(e).filter(n=>n.tagName==='button');
const resumeButton=e=>buttons(e).find(n=>n.textContent==='เริ่มงานต่อจาก Build นี้');
const buildPicker=e=>all(e).find(n=>n.tagName==='select'&&n.dataset.eaFactoryExistingBuild!==undefined);
const render=()=>{const root=new Element('main');renderEaFactoryProgressPage(root,domain);return root;};
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function reloadFixture(){
  fixture();domain.activeBuild=null;state.modal.eaFactory.selectedBuildId='';state.modal.eaFactory.confirmedCreateBuildId='';
  state.modal.eaFactory.stageId='';state.modal.eaFactory.message='';
  domain.builds=Array.from({length:30},(_,i)=>({id:`ea-build-history-${i+1}`,platform:'mt5',artifactKind:'expert_advisor',sourceDisplayName:`System ${i+1}`,status:'ready'}));
  return domain;
}
"""
        parts = [support]
        for start, end in (
            ("function getSafeReportArtifactUrl", "function appendDashboardVisualEvidence"),
            ("function eaFactoryCertifiedDeliveryCompleted", "function eaFactoryRunNeedsProgressPage"),
            ("function eaFactoryExistingOneClickAdmission", "function renderEaFactoryOneClickPanel"),
            ("function createEaFactoryGameAction", "function renderEaFactoryOneClickSetup"),
            ("function renderEaFactoryExistingBuildPicker", "function renderEaFactoryProgressPage"),
            ("function renderEaFactoryProgressPage", "function renderEaFactoryResultPage"),
            ("function renderEaFactoryResultPage", "function renderEaFactoryPanel"),
            ("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet"),
            ("async function runEaFactoryOneClick", "function cancelEaFactorySubmittingRequest"),
        ):
            parts.append(self.block(start, end))
        parts.append("(async()=>{\n" + body + "\n})().catch(error=>{console.error(error);process.exitCode=1;});")
        result = subprocess.run([self.node, "-"], input="\n".join(parts), cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_confirmed_receipt_survives_read_timeout_and_offers_refresh_only(self):
        self.run_js(r"""
fixture();domain.activeBuild=null;domain.authoritative=false;
state.eaFactoryReadModel.lastError={kind:'timeout',message:'Backend ตอบกลับเกิน 20 วินาที'};
const root=render();assert.match(root.textContent,/Backend รับ Build แล้ว/);
assert.match(root.textContent,/ea-build-exact/);assert.match(root.textContent,/20 วินาที/);
assert.doesNotMatch(root.textContent,/ยังไม่มีงานที่กำลังสร้าง/);
assert.deepEqual(buttons(root).map(b=>b.textContent),['ตรวจสถานะ Build นี้']);
buttons(root)[0].events.click();await flush();
assert.equal(refreshes,1);assert.equal(posts.length,0);assert.deepEqual(navigations,[]);
""")

    def test_missing_wrong_or_malformed_receipt_id_cannot_claim_confirmation(self):
        self.run_js(r"""
for(const id of ['',null,'ea-build-other','not-a-build','ea-build-<unsafe>']){
  fixture();domain.activeBuild=null;state.modal.eaFactory.confirmedCreateBuildId=id;
  const root=render();assert.doesNotMatch(root.textContent,/Backend รับ Build แล้ว/);
  assert.equal(resumeButton(root),undefined);assert.equal(posts.length,0);
}
""")

    def test_idle_exact_build_is_truthfully_not_running_and_runs_only_on_click(self):
        self.run_js(r"""
fixture();const root=render();assert.match(root.textContent,/Build รอเริ่มขั้นถัดไป/);
assert.doesNotMatch(root.textContent,/ระบบกำลังสร้างงานของคุณ/);
const start=resumeButton(root);assert.ok(start);assert.equal(posts.length,0);
start.events.click();await flush();
assert.equal(posts.length,1);assert.match(posts[0].path,/\/builds\/ea-build-exact\/run$/);
assert.equal(posts[0].payload.idempotencyKey,'exact-run-key-ea-build-exact');
assert.equal(refreshes,0);assert.deepEqual(navigations,[]);
""")

    def test_start_remains_unavailable_without_each_normal_admission_guard(self):
        self.run_js(r"""
for(const change of [d=>d.authoritative=false,d=>d.backendBusy={buildId:'other'},
  d=>state.modal.eaFactory.inFlight=true,d=>d.oneClick.enabled=false,d=>d.oneClick.canRun=false,
  d=>d.oneClick.selectedTerminalId='',d=>d.oneClick.selectedPlatform='mt4',
  d=>d.oneClick.selectedPlatformSupported=false,d=>d.oneClick.supportedVisiblePlatforms=[],
  d=>d.oneClick.terminalReady=false,d=>d.oneClick.terminalRunning=false,
  d=>d.oneClick.visibleAdapterConnected=false,d=>d.oneClick.terminalProcessLaunchAllowed=true,
  d=>headerReady=false,d=>d.stages[0].status='failed',d=>d.stages[0].status='blocked']){
  fixture();change(domain);assert.equal(resumeButton(render()),undefined);assert.equal(posts.length,0);
}
""")

    def test_non_ea_or_non_visible_platform_never_gets_initial_start(self):
        self.run_js(r"""
for(const change of [d=>d.activeBuild.artifactKind='custom_indicator',
  d=>{d.activeBuild.platform='tradingview';d.oneClick.selectedPlatform='tradingview';d.oneClick.supportedVisiblePlatforms=['tradingview'];}]){
  fixture();change(domain);assert.equal(resumeButton(render()),undefined);assert.equal(posts.length,0);
}
""")

    def test_active_finished_or_failed_run_does_not_offer_initial_start(self):
        self.run_js(r"""
for(const status of ['running','queued','waiting_ai','cancelling','completed','cancelled','failed','blocked']){
  fixture();domain.oneClick.run.status=status;
  assert.equal(resumeButton(render()),undefined);assert.equal(posts.length,0);
}
""")

    def test_old_button_cannot_target_changed_selected_build(self):
        self.run_js(r"""
fixture();const start=resumeButton(render());assert.ok(start);
domain.activeBuild={...domain.activeBuild,id:'ea-build-replacement'};
state.modal.eaFactory.selectedBuildId='ea-build-replacement';
start.events.click();await flush();assert.equal(posts.length,0);
assert.equal(state.modal.eaFactory.messageKind,'local_preflight_rejected');
""")

    def test_old_button_rechecks_stale_busy_terminal_header_and_inflight_guards(self):
        self.run_js(r"""
for(const change of [d=>d.authoritative=false,d=>d.backendBusy={buildId:'other'},
  d=>d.oneClick.terminalRunning=false,d=>d.oneClick.visibleAdapterConnected=false,
  d=>headerReady=false,d=>state.modal.eaFactory.inFlight=true]){
  fixture();const start=resumeButton(render());assert.ok(start);change(domain);
  start.events.click();await flush();assert.equal(posts.length,0);
}
""")

    def test_certified_completed_manual_build_without_run_shows_result_not_start(self):
        self.run_js(r"""
fixture();domain.oneClick.canRun=false;
domain.stages.push({id:'artifacts_report',status:'completed'});
assert.equal(domain.oneClick.run.runId,undefined);
const root=render();assert.match(root.textContent,/สร้างงานเสร็จแล้ว/);
assert.doesNotMatch(root.textContent,/Build รอเริ่มขั้นถัดไป|ระบบกำลังสร้างงานของคุณ/);
assert.equal(resumeButton(root),undefined);
const results=buttons(root).find(b=>b.textContent==='ดูผลลัพธ์และไฟล์');
assert.ok(results);results.events.click();assert.deepEqual(navigations,['result']);
assert.equal(posts.length,0);
""")

    def test_stale_completed_manual_build_cannot_claim_current_completion(self):
        self.run_js(r"""
fixture();domain.oneClick.canRun=false;domain.authoritative=false;
domain.stages.push({id:'artifacts_report',status:'completed'});
const root=render();assert.doesNotMatch(root.textContent,/สร้างงานเสร็จแล้ว/);
assert.equal(all(root).find(e=>e.className==='ea-factory-game-progress').dataset.status,'checking');
assert.equal(resumeButton(root),undefined);
assert.equal(buttons(root).some(b=>b.textContent==='ดูผลลัพธ์และไฟล์'),false);
assert.equal(posts.length,0);
""")

    def test_reload_lists_all_known_builds_without_auto_selecting_or_dispatching(self):
        self.run_js(r"""
reloadFixture();const root=render();const picker=buildPicker(root);assert.ok(picker);
assert.match(root.textContent,/เลือก Build ที่มีอยู่/);
const options=picker.children.filter(e=>e.tagName==='option');
assert.equal(options.length,31);assert.equal(options[0].value,'');
assert.deepEqual(options.slice(1).map(e=>e.value),domain.builds.map(b=>b.id));
assert.ok(options.slice(1).every((e,i)=>e.textContent.includes(domain.builds[i].id)));
assert.equal(state.modal.eaFactory.selectedBuildId,'');assert.equal(domain.activeBuild,null);
assert.equal(posts.length,0);assert.equal(refreshes,0);assert.equal(renders,0);
""")

    def test_explicit_picker_selection_selects_exact_id_and_only_renders(self):
        self.run_js(r"""
reloadFixture();const picker=buildPicker(render());picker.value='ea-build-history-17';
picker.events.change({target:picker});await flush();
assert.equal(state.modal.eaFactory.selectedBuildId,'ea-build-history-17');
assert.equal(renders,1);assert.equal(posts.length,0);assert.equal(refreshes,0);
assert.equal(state.modal.eaFactory.confirmedCreateBuildId,'');
""")

    def test_active_pending_build_can_select_other_exact_build_without_dispatch_or_history_change(self):
        self.run_js(r"""
fixture();domain.oneClick.run={runId:'ea-run-elder',status:'awaiting_visible_terminal',canResume:false};
domain.builds=[{id:'ea-build-exact',platform:'mt5',sourceDisplayName:'Elder',status:'blocked',attemptCount:3},
  {id:'ea-build-ema-10-60',platform:'mt5',sourceDisplayName:'EMA10/60',status:'ready',attemptCount:1}];
const history=JSON.stringify(domain.builds),run=JSON.stringify(domain.oneClick.run);
const root=render(),picker=buildPicker(root);assert.ok(picker);assert.equal(picker.disabled,false);
assert.equal(picker.value,'ea-build-exact');picker.value='ea-build-ema-10-60';picker.events.change({target:picker});await flush();
assert.equal(state.modal.eaFactory.selectedBuildId,'ea-build-ema-10-60');assert.equal(renders,1);
assert.equal(posts.length,0);assert.equal(refreshes,0);assert.deepEqual(navigations,[]);
assert.equal(JSON.stringify(domain.builds),history);assert.equal(JSON.stringify(domain.oneClick.run),run);
assert.equal(state.modal.eaFactory.confirmedCreateBuildId,'ea-build-exact');
""")

    def test_result_page_also_offers_existing_build_picker_with_unchanged_freshness_guards(self):
        self.run_js(r"""
for(const stale of [false,true]){
  fixture();domain.builds=[{id:'ea-build-exact',platform:'mt5'}, {id:'ea-build-ema-10-60',platform:'mt5'}];
  state.eaFactoryReadModel.stale=stale;
  const root=new Element('main');renderEaFactoryResultPage(root,domain);
  const picker=buildPicker(root);assert.ok(picker);assert.equal(picker.value,'ea-build-exact');assert.equal(picker.disabled,stale);
  picker.value='ea-build-ema-10-60';picker.events.change({target:picker});await flush();
  assert.equal(state.modal.eaFactory.selectedBuildId,stale?'ea-build-exact':'ea-build-ema-10-60');
  assert.equal(posts.length,0);assert.equal(refreshes,0);
}
""")

    def test_source_setup_has_the_same_existing_build_picker_before_new_build_controls(self):
        source = self.block("function renderEaFactorySourceStage", "function renderEaFactorySpecStage")
        self.assertLess(source.index("renderEaFactoryExistingBuildPicker(section, domain)"),
                        source.index('const intake = document.createElement("div")'))

    def test_completed_build_backtest_html_after_first_twelve_is_visible_through_safe_links_only(self):
        self.run_js(r"""
fixture();domain.oneClick.run={runId:'ea-run-existing',status:'completed'};
domain.activeBuild.artifacts=Array.from({length:18},(_,i)=>({available:true,
  fileName:`evidence-${i}.png`,url:`/api/props/right_server_racks/ea-factory/builds/ea-build-exact/files/ea-file-${i}`}));
domain.activeBuild.artifacts.push({available:true,fileName:'EMA10_60_Backtest_Report.html',kind:'backtest_report',
  url:'/api/props/right_server_racks/ea-factory/builds/ea-build-exact/files/ea-file-backtest'});
domain.activeBuild.artifacts.push({available:false,fileName:'unavailable.html',url:'/api/reports/report-a/artifacts/file-a'},
  {available:true,fileName:'external.html',url:'https://example.com/report.html'},
  {available:true,fileName:'unsafe.html',url:'javascript:alert(1)'});
const before=JSON.stringify(domain.activeBuild.artifacts),root=new Element('main');renderEaFactoryResultPage(root,domain);
const links=all(root).filter(e=>e.tagName==='a');assert.equal(links.length,19);
const report=links.find(e=>e.textContent==='EMA10_60_Backtest_Report.html');assert.ok(report);
assert.equal(report.href,'http://127.0.0.1:4186/api/props/right_server_racks/ea-factory/builds/ea-build-exact/files/ea-file-backtest');
assert.equal(report.rel,'noopener noreferrer');assert.equal(report.target,'_blank');
assert.equal(links.some(e=>['unavailable.html','external.html','unsafe.html'].includes(e.textContent)),false);
assert.equal(JSON.stringify(domain.activeBuild.artifacts),before);assert.equal(posts.length,0);
""")

    def test_picker_rejects_invalid_unknown_or_removed_build_identity(self):
        self.run_js(r"""
for(const id of ['','unknown','ea-build-<unsafe>','ea-build-not-in-model','ea-build-history-17']){
  reloadFixture();const picker=buildPicker(render());
  if(id==='ea-build-history-17')domain.builds=domain.builds.filter(b=>b.id!==id);
  picker.value=id;picker.events.change({target:picker});await flush();
  assert.equal(state.modal.eaFactory.selectedBuildId,'');assert.equal(posts.length,0);assert.equal(renders,0);
}
""")

    def test_picker_rejects_late_stale_or_replaced_modal_context(self):
        self.run_js(r"""
for(const change of [()=>domain.authoritative=false,()=>state.modal.open=false,
  ()=>state.modal.id='another-room',()=>state.modal.eaFactory={...state.modal.eaFactory},
  ()=>state.modal.eaFactory.readContextRevision=1,()=>state.modal.eaFactory.inFlight=true,
  ()=>state.eaFactoryReadModel.stale=true,()=>state.eaFactoryReadModel.payload.snapshotStale=true,
  ()=>domain.backendBusy={buildId:'ea-build-other'}]){
  reloadFixture();const picker=buildPicker(render());change();
  picker.value='ea-build-history-17';picker.events.change({target:picker});await flush();
  assert.equal(state.modal.eaFactory.selectedBuildId,'');assert.equal(posts.length,0);assert.equal(renders,0);
}
""")

    def test_picker_filters_malformed_ids_and_stale_initial_model_has_no_enabled_choice(self):
        self.run_js(r"""
reloadFixture();domain.builds.push({id:'bad-id'},{id:'ea-build-<unsafe>'},{id:''});
const picker=buildPicker(render());assert.equal(picker.children.filter(e=>e.tagName==='option').length,31);
for(const change of [()=>domain.authoritative=false,()=>state.eaFactoryReadModel.stale=true,
  ()=>state.eaFactoryReadModel.payload.snapshotStale=true]){
  reloadFixture();change();const stalePicker=buildPicker(render());
  assert.ok(!stalePicker||stalePicker.disabled);
  assert.equal(state.modal.eaFactory.selectedBuildId,'');assert.equal(posts.length,0);
}
""")

    def test_confirmed_receipt_keeps_its_identity_instead_of_showing_history_picker(self):
        self.run_js(r"""
reloadFixture();state.modal.eaFactory.selectedBuildId='ea-build-receipted';
state.modal.eaFactory.confirmedCreateBuildId='ea-build-receipted';
const root=render();assert.equal(buildPicker(root),undefined);
assert.match(root.textContent,/Backend รับ Build แล้ว.*ea-build-receipted/);
assert.deepEqual(buttons(root).map(b=>b.textContent),['ตรวจสถานะ Build นี้']);
assert.equal(state.modal.eaFactory.selectedBuildId,'ea-build-receipted');assert.equal(posts.length,0);
""")


if __name__ == "__main__":
    unittest.main()
