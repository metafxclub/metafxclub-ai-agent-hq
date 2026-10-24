"""Execute the real browser Import state machine with controlled transports."""
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EaFactoryImportRecoveryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        cls.node = shutil.which("node") or str(
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )

    def block(self, start, end):
        offset = self.main.index(start)
        return self.main[offset:self.main.index(end, offset)]

    def run_js(self, body, *, request=False, loader=False, sync=False):
        support = r"""
const assert = require('node:assert/strict');
const EA_FACTORY_PROP_ID = 'right_server_racks';
const EA_FACTORY_SUPPORTED_MODES = new Set(['one_click_with_manual_stage_recovery']);
const EA_FACTORY_READ_MODEL_MAX_AGE_MS = 90000;
const EA_FACTORY_GOOGLE_SHEET_CATALOG_REFRESH_MS = 75000;
const EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION = 'ea-factory-deep-research-catalog-v1';
const EA_FACTORY_ACTION_TIMEOUT_MS = 45000;
const PROP_REPORT_FETCH_TIMEOUT_MS = 20000;
const a = 'a'.repeat(64), b = 'b'.repeat(64), c = 'c'.repeat(64);
let state, events, generatedKeys, eaFactoryActiveActionAbortController = null;
let eaFactoryReadModelInFlight = null;
let postEaFactoryJson, fetchJson, loadResearchSheetHub = async () => null;
let ensureEaFactoryGoogleSheetCatalog;
const workflowDomainObject = (...values) => values.find(v => v && typeof v === 'object' && !Array.isArray(v)) || {};
const safeDashboardDisplayText = (value, fallback = '') => value || fallback;
const normalizeEaFactorySourceRecord = value => value;
const eaFactorySourceIsBuildSelectable = value => value?.buildReady === true;
const eaFactoryReadModelStateKey = value => JSON.stringify(value);
const mergeBackendMission = () => {};
const mergeEaFactoryResponseReport = () => {};
const eaFactoryBusyPresentation = busy => ({kind:'busy',tone:'warning',message:'busy',busy});
const eaFactoryReadModelFailurePresentation = error => ({kind:error.kind === 'fetch_timeout' ? 'timeout' : 'failure',tone:'warning',message:'request failed',busy:null});
function setEaFactoryActionState(next) { Object.assign(state.modal.eaFactory, {inFlight:false}, next); events.push({...next}); }
function createWorkflowIdempotencyKey() { generatedKeys += 1; return 'sync-key-' + generatedKeys; }
function fixture() {
  const record = {recordId:'deep-test',systemName:'Alexander Elder',sourceRecordId:'ea-source-test',recordDigest:a,buildReady:true};
  const snapshot = {missionId:'mission-sync',reportId:'report-sync',sourceKey:'sheet-source',syncedAt:'2026-10-18T11:42:29Z',status:'ready',headerExact:true,tabName:'Deep_Research',sourceKind:'verified_deep_research_sheet',sourceSchemaVersion:'deep-research-sheet-v2',recordCount:1};
  const model = {schemaVersion:'ea-factory-v1',mode:'one_click_with_manual_stage_recovery',scheduled:false,snapshotStale:false,busy:null,sourceCatalog:{records:[record],googleSheets:{configRevision:1}},sourceSnapshots:[snapshot]};
  const catalog = {schemaVersion:EA_FACTORY_GOOGLE_SHEET_CATALOG_SCHEMA_VERSION,status:'ready',inFlight:false,configRevision:1,tabName:'Deep_Research',catalogDigest:b,snapshotDigest:c,totalCount:1,systems:[record],lastLoadedAt:Date.now()};
  const factory = {sourceMode:'google_sheet',sheetRecordId:'deep-test',googleSheetCatalog:catalog,inFlight:false,importedSourceId:'',selectedSourceId:''};
  state = {modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:factory},eaFactoryReadModel:{payload:model,lastLoadedAt:Date.now(),stale:false,busy:null,lastError:null},propReports:{}};
  events = []; generatedKeys = 0; eaFactoryReadModelInFlight = null;
  ensureEaFactoryGoogleSheetCatalog = async () => catalog;
  const intent = {recordId:record.recordId,sourceRecordId:record.sourceRecordId,recordDigest:a,configRevision:1,catalogDigest:b,snapshotDigest:c,idempotencyKey:'sync-key-1',receipt:null};
  // The real mission projection intentionally omits its internal idempotency key.
  const response = {ok:true,kind:'ea_factory_sheet_sync_completed',requestIdempotencyKey:'sync-key-1',configRevision:1,mission:{id:'mission-sync',status:'completed',toolId:'ea_factory_google_sheet_read',targetId:EA_FACTORY_PROP_ID,owner:'mission_archivist',reportIds:['report-sync']},sourceSnapshot:snapshot,report:{id:'report-sync',status:'ready',type:'trading_system_research_report',linkedMissionId:'mission-sync',linkedPropId:EA_FACTORY_PROP_ID,ownerAgentId:'mission_archivist',metrics:{eaFactorySource:{schemaVersion:'ea-factory-sheet-snapshot-v1',sourceKey:'sheet-source',tabName:'Deep_Research',recordCount:1,snapshotDigest:c}}}};
  return {record,snapshot,model,catalog,factory,intent,response};
}
"""
        parts = [support]
        for start, end in (
            ("function eaFactoryFindSourceByExactRecordId", "function createEaFactoryNotice"),
            ("function eaFactoryGoogleSheetCatalogRecords", "function eaFactoryGoogleSheetCatalogKey"),
            ("function clearEaFactoryGoogleSheetImport", "function reconcileEaFactoryGoogleSheetSelection"),
            ("function eaFactoryGoogleSheetCatalogIsFresh", "function eaFactoryGoogleSheetImportBindingReady"),
            ("function eaFactoryGoogleSheetSyncReceipt", "function eaFactoryCreateBuildFormSignature"),
        ):
            parts.append(self.block(start, end))
        if request or sync:
            parts.append(self.block("async function runEaFactoryRequest", "async function syncEaFactoryGoogleSheet"))
        if sync:
            parts.append(self.block("async function syncEaFactoryGoogleSheet", "function normalizeEaFactoryGoogleSheetCatalog"))
        if loader:
            parts.append(self.block("async function loadEaFactoryReadModel", "function setEaFactoryActionState"))
        parts.append("(async () => {\n" + body + "\n})().catch(error => { console.error(error); process.exitCode=1; });")
        result = subprocess.run([self.node, "-"], input="\n".join(parts), cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_independent_get_timeout_cannot_release_inflight_post(self):
        self.run_js(r"""
for (const stageId of ['sheet_sync','create_build']) {
const f = fixture(); let rejectRead, calls=0;
fetchJson = async () => { calls++; return new Promise((_resolve,reject) => { rejectRead=reject; }); };
const pending=loadEaFactoryReadModel();
f.factory.inFlight=true; f.factory.stageId=stageId;
rejectRead(Object.assign(new Error('slow'),{kind:'fetch_timeout'}));
assert.equal(await pending, null); assert.equal(calls,1);
assert.equal(f.factory.inFlight, true); assert.equal(f.factory.stageId, stageId);
assert.equal(state.eaFactoryReadModel.stale, true); assert.equal(events.length, 0);
}
""", loader=True)

    def test_truthy_stale_get_after_post_failure_never_grants_authority(self):
        self.run_js(r"""
const f = fixture();
globalThis.loadEaFactoryReadModel = async () => {
  f.model.snapshotStale=true; state.eaFactoryReadModel.stale=true;
  state.eaFactoryReadModel.lastError={kind:'refreshing'}; return {eaFactory:f.model};
};
assert.equal(await runEaFactoryRequest('sheet_sync', async () => { throw new Error('lost'); }, 'ok'), null);
assert.equal(state.eaFactoryReadModel.stale, true);
assert.equal(state.eaFactoryReadModel.lastError.kind, 'refreshing');
""", request=True)

    def test_cold_get_retries_once_with_same_bound_and_stays_disabled_until_fresh(self):
        self.run_js(r"""
const f=fixture(); let requests=[], merged=0;
fetchJson=async (path, options) => {
  requests.push({path,timeoutMs:options.timeoutMs});
  if (requests.length===1) throw Object.assign(new Error('cold'),{kind:'fetch_timeout'});
  assert.equal(state.eaFactoryReadModel.stale,true);
  assert.match(f.factory.message,/กำลังตรวจประวัติ Build/);
  return {eaFactory:f.model};
};
globalThis.mergeEaFactoryReadModel=payload => { merged++; assert.equal(payload.eaFactory,f.model); state.eaFactoryReadModel.stale=false; return true; };
assert.ok(await loadEaFactoryReadModel()); assert.equal(requests.length,2);
assert.deepEqual(requests[0],requests[1]); assert.equal(requests[1].timeoutMs,20000); assert.equal(merged,1);
fixture(); requests=[];
fetchJson=async (_path,options) => { requests.push(options); throw Object.assign(new Error('still slow'),{kind:'fetch_timeout'}); };
assert.equal(await loadEaFactoryReadModel(),null); assert.equal(requests.length,2);
assert.equal(state.eaFactoryReadModel.stale,true); assert.equal(merged,1);
""", loader=True)

    def test_retry_cannot_commit_after_modal_closes_or_context_is_replaced(self):
        self.run_js(r"""
for (const change of [
  f => state.modal.open=false,
  f => state.modal.id='other',
  f => state.modal.eaFactory={...f.factory},
  f => f.factory.readContextRevision=1,
]) {
  const f=fixture(); let calls=0, finish, merged=0;
  fetchJson=async () => { calls++; if (calls===1) throw Object.assign(new Error('cold'),{kind:'fetch_timeout'}); return new Promise(resolve => { finish=resolve; }); };
  globalThis.mergeEaFactoryReadModel=() => { merged++; return true; };
  const pending=loadEaFactoryReadModel();
  await new Promise(resolve => setImmediate(resolve)); assert.equal(calls,2);
  change(f); finish({eaFactory:f.model});
  assert.equal(await pending,null); assert.equal(merged,0);
}
""", loader=True)

    def test_sync_receipt_returns_before_projection_and_keeps_exact_key(self):
        self.run_js(r"""
const f = fixture(); let posted;
globalThis.mergeEaFactoryReadModel = () => false;
globalThis.loadEaFactoryReadModel = async () => { throw new Error('Receipt must not wait for projection'); };
postEaFactoryJson = async (_path, payload) => { posted=payload; return f.response; };
assert.equal(await syncEaFactoryGoogleSheet(1,{idempotencyKey:'sync-key-1'}), f.response);
assert.deepEqual(posted, {configRevision:1,idempotencyKey:'sync-key-1'});
assert.equal(generatedKeys,0); assert.equal(f.factory.importedSourceId,'');
""", sync=True)

    def test_sync_receipt_rejects_wrong_key_mission_report_or_snapshot(self):
        self.run_js(r"""
const f = fixture(); assert.equal(f.response.mission.idempotencyKey,undefined);
assert.ok(eaFactoryGoogleSheetSyncReceipt(f.response, f.intent));
const mutations = [
  r => delete r.mission, r => r.mission=null, r => r.mission=[],
  r => delete r.report, r => r.report=null, r => r.report=[],
  r => delete r.sourceSnapshot, r => r.sourceSnapshot=null, r => r.sourceSnapshot=[],
  r => delete r.report.metrics.eaFactorySource, r => r.report.metrics.eaFactorySource=null,
  r => r.report.metrics.eaFactorySource=[],
  r => { delete r.report; delete r.sourceSnapshot.reportId; r.mission.reportIds=[]; },
  r => r.requestIdempotencyKey='wrong', r => delete r.requestIdempotencyKey,
  r => r.configRevision=2, r => delete r.configRevision, r => r.mission.status='running',
  r => r.mission.toolId='other', r => r.mission.reportIds=[],
  r => r.sourceSnapshot.missionId='other', r => r.sourceSnapshot.reportId='other',
  r => r.sourceSnapshot.headerExact=false, r => r.sourceSnapshot.sourceSchemaVersion='old',
  r => r.report.linkedMissionId='other', r => r.report.status='failed',
  r => r.report.metrics.eaFactorySource.snapshotDigest=a,
  r => r.report.metrics.eaFactorySource.sourceKey='other',
];
for (const mutate of mutations) { const bad=structuredClone(f.response); mutate(bad); assert.equal(eaFactoryGoogleSheetSyncReceipt(bad,f.intent),null); }
""")

    def test_ack_timeout_replays_one_original_key_and_late_fresh_get_recovers(self):
        self.run_js(r"""
const f=fixture(); let calls=[];
globalThis.mergeEaFactoryReadModel = () => false;
globalThis.loadEaFactoryReadModel = async () => { state.eaFactoryReadModel.stale=true; return null; };
postEaFactoryJson = async (_path,payload) => {
  calls.push({...payload});
  if (calls.length===1) throw Object.assign(new Error('ack lost'),{kind:'fetch_timeout'});
  const replay=structuredClone(f.response); replay.kind='ea_factory_sheet_sync_replayed'; delete replay.report; return replay;
};
fetchJson=async path => { assert.equal(path,'/api/reports/report-sync'); return {ok:true,readModel:'report_detail_v1',report:f.response.report}; };
assert.equal(await importEaFactorySourceRecord('deep-test'),null);
assert.equal(calls.length,2); assert.deepEqual(calls[0],calls[1]); assert.equal(generatedKeys,1);
assert.equal(f.factory.importedSourceId,''); assert.ok(f.factory.pendingGoogleSheetImport.receipt);
state.eaFactoryReadModel.stale=false; state.eaFactoryReadModel.lastLoadedAt=Date.now();
assert.equal(reconcileEaFactoryPendingGoogleSheetImport().sourceRecordId,'ea-source-test');
assert.equal(f.factory.importedRecordDigest,a); assert.equal(f.factory.importedSnapshotDigest,c);
assert.equal(f.factory.pendingGoogleSheetImport,null); assert.equal(calls.length,2);
""", sync=True)

    def test_sync_timeout_replay_does_not_wait_for_factory_projection(self):
        self.run_js(r"""
const f=fixture(); let posts=0, reads=0;
globalThis.mergeEaFactoryReadModel=()=>false;
globalThis.loadEaFactoryReadModel=async () => { reads++; throw new Error('projection must not precede replay'); };
postEaFactoryJson=async () => { posts++; throw Object.assign(new Error('ack lost'),{kind:'fetch_timeout'}); };
assert.equal(await syncEaFactoryGoogleSheet(1,{idempotencyKey:'sync-key-1'}),null);
assert.equal(posts,1); assert.equal(reads,0); assert.equal(state.eaFactoryReadModel.stale,true);
assert.equal(f.factory.inFlight,false);
""", sync=True)

    def test_sync_pauses_only_unrelated_reads_and_queued_force_fresh_followup(self):
        self.run_js(r"""
for (const stageId of ['sheet_sync','create_build']) {
const f=fixture(); let calls=0;
fetchJson=async () => { calls++; return {eaFactory:f.model}; };
globalThis.mergeEaFactoryReadModel=()=>true;
f.factory.inFlight=true; f.factory.stageId=stageId;
assert.equal(await loadEaFactoryReadModel({forceFresh:true}),null); assert.equal(calls,0);
state.eaFactoryReadModel.busy={buildId:'real-running-build'};
assert.ok(await loadEaFactoryReadModel()); assert.equal(calls,1);
state.eaFactoryReadModel.busy=null; f.factory.inFlight=false;
let settle; eaFactoryReadModelInFlight=new Promise(resolve=>{settle=resolve;});
const waiting=loadEaFactoryReadModel({forceFresh:true});
f.factory.inFlight=true; f.factory.stageId=stageId; settle({eaFactory:f.model});
assert.equal(await waiting,null); assert.equal(calls,1);
}
""", loader=True)

    def test_sheet_sync_does_not_masquerade_as_build_or_start_three_second_poll(self):
        progress = self.block("function eaFactoryPhaseGateProgress", "function stopEaFactoryActiveProgressPolling")
        self.run_js(progress + r"""
const EA_FACTORY_VISUAL_STAGE_IDS=['source','review'];
const EA_FACTORY_UI_STAGE_BY_BACKEND={}; const EA_FACTORY_STAGE_COPY={};
const eaFactoryOneClickStageStatus=()=> 'pending'; const eaFactoryCertifiedDeliveryCompleted=()=>false;
const f=fixture(); f.factory.inFlight=true;
for (const stageId of ['sheet_sync','create_build']) {
f.factory.stageId=stageId;
for (const status of ['idle','running','queued','awaiting_visible_terminal']) {
  const progress=eaFactoryPhaseGateProgress({oneClick:{run:{status}}});
  assert.equal(progress.active,false); assert.equal(progress.waiting,false); assert.equal(progress.shouldPoll,false);
}
const actual=eaFactoryPhaseGateProgress({backendBusy:{buildId:'build-live'},oneClick:{run:{status:'running'}}});
assert.equal(actual.active,true); assert.equal(actual.shouldPoll,true);
}
f.factory.stageId='one_click_create_run';
assert.equal(eaFactoryPhaseGateProgress({}).shouldPoll,true);
""")

    def test_background_poll_skips_sync_only_and_continues_real_build(self):
        poll = self.block("async function pollOpenPropReport", "function startMissionPolling")
        self.run_js(poll + r"""
const document={visibilityState:'visible',hasFocus:()=>true,activeElement:null};
const OPEN_PROP_REPORT_POLL_TTL_MS=30000; const EA_OPTIMIZATION_LAB_PROP_ID='other-lab';
const SENTIMENT_UNIVERSE_ENABLED=true, FX_NEWS_BIAS_PROP_ID='left_signal_cube';
const EA_OPTIMIZATION_LAB_ACTIVE_POLL_MS=3000, EA_OPTIMIZATION_LAB_IDLE_POLL_MS=30000;
const eaOptimizationLabSessionIsActive=()=>false, renderGameModal=()=>{};
const getModalSubject=()=>({}), getPropertyRole=()=>({});
let busy=null, reads=0;
const normalizeWorkflowDashboard=()=>({domainData:{eaFactory:{backendBusy:busy}}});
globalThis.loadEaFactoryReadModel=async()=>{reads++; return null;};
const f=fixture(); state.modal.type='prop'; state.propReportLoadedAt={};
for (const stageId of ['sheet_sync','create_build']) {
reads=0; f.factory.inFlight=true; f.factory.stageId=stageId;
await pollOpenPropReport({force:true}); assert.equal(reads,0);
busy={buildId:'build-real'}; await pollOpenPropReport({force:true}); assert.equal(reads,1);
busy=null; f.factory.inFlight=false; await pollOpenPropReport({force:true}); assert.equal(reads,2);
}
""")

    def test_http_rejection_and_operator_cancel_are_not_automatically_replayed(self):
        self.run_js(r"""
for (const kind of ['http_error','ea_factory_operator_cancelled_request']) {
  const f=fixture(); let calls=0;
  globalThis.syncEaFactoryGoogleSheet=async (_revision, options) => { calls++; options.onRequestError?.({kind}); return null; };
  await importEaFactorySourceRecord('deep-test'); assert.equal(calls,1); assert.equal(f.factory.importedSourceId,'');
}
""")

    def test_receipt_never_overrides_new_revision_selection_binding_or_stale_model(self):
        self.run_js(r"""
const mutations = [
  f => f.catalog.configRevision=2, f => f.catalog.catalogDigest=a,
  f => f.catalog.snapshotDigest=a, f => f.catalog.lastLoadedAt=1,
  f => f.factory.sheetRecordId='another', f => f.factory.sourceMode='custom',
  f => state.modal.open=false, f => state.modal.id='other-prop',
  f => f.model.snapshotStale=true, f => state.eaFactoryReadModel.stale=true,
  f => state.eaFactoryReadModel.lastLoadedAt=1,
  f => f.model.sourceCatalog.googleSheets.configRevision=2,
  f => f.model.sourceSnapshots=[], f => f.model.sourceSnapshots[0].missionId='other',
  f => f.model.sourceSnapshots[0].reportId='other',
  f => f.model.sourceCatalog.records=[{...f.record,recordDigest:b}],
  f => f.model.sourceCatalog.records=[f.record,f.record],
  f => f.catalog.systems=[{...f.record,sourceRecordId:'ea-source-other'}],
];
for (const mutate of mutations) {
  const f=fixture(); f.intent.receipt=eaFactoryGoogleSheetSyncReceipt(f.response,f.intent);
  f.factory.pendingGoogleSheetImport=f.intent; mutate(f);
  assert.equal(reconcileEaFactoryPendingGoogleSheetImport(),null);
  assert.equal(f.factory.importedSourceId,'');
}
""")

    def test_selection_changed_during_await_does_not_apply_or_replay(self):
        self.run_js(r"""
const f=fixture(); let complete, calls=0;
globalThis.syncEaFactoryGoogleSheet=async () => { calls++; return new Promise(resolve => { complete=resolve; }); };
const pending=importEaFactorySourceRecord('deep-test');
f.factory.sheetRecordId='different-record'; f.factory.pendingGoogleSheetImport=null;
complete(f.response); assert.equal(await pending,null);
assert.equal(f.factory.importedSourceId,''); assert.equal(f.factory.sheetRecordId,'different-record'); assert.equal(calls,1);
""")

    def test_confirmed_pending_import_rechecks_without_another_post(self):
        self.run_js(r"""
const f=fixture(); f.intent.receipt=eaFactoryGoogleSheetSyncReceipt(f.response,f.intent);
f.factory.pendingGoogleSheetImport=f.intent;
globalThis.syncEaFactoryGoogleSheet=async () => { throw new Error('must reuse confirmed receipt'); };
globalThis.loadEaFactoryReadModel=async () => ({eaFactory:f.model});
assert.equal((await importEaFactorySourceRecord('deep-test')).sourceRecordId,'ea-source-test');
assert.equal(generatedKeys,0);
""")


if __name__ == "__main__":
    unittest.main()
