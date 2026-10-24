"""Execute deferred Factory reads without granting stale display authority."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DeferredFactoryReadFrontendTests(unittest.TestCase):
    def run_js(self, body):
        main = (ROOT / 'frontend/src/app/main.js').read_text(encoding='utf-8')
        code = main[main.index('async function loadEaFactoryReadModel('):main.index('\nfunction setEaFactoryActionState(', main.index('async function loadEaFactoryReadModel('))]
        node = shutil.which('node') or str(Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
        support = r'''
const assert = require('node:assert/strict');
const EA_FACTORY_PROP_ID='right_server_racks', PROP_REPORT_FETCH_TIMEOUT_MS=20000;
let eaFactoryReadModelInFlight=null, calls=0, merges=0, actions=[], response, afterFetch=()=>{};
const oldModel={schemaVersion:'ea-factory-v1',builds:[{id:'original-build'}]};
const oldBusy={reasonCode:'existing-operation'};
let state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{inFlight:false,selectedBuildId:'original-build',readContextRevision:3}},
 eaFactoryReadModel:{payload:oldModel,busy:oldBusy,lastLoadedAt:123,stale:false,inFlight:false}};
const deferred=()=>({ok:true,kind:'ea_factory_refresh_deferred',status:'deferred',readinessConfirmed:false,retryAfterMs:1000});
const fetchJson=async()=>{calls++;afterFetch();return response;};
const mergeEaFactoryReadModel=(payload)=>{merges++;if(payload?.eaFactory?.schemaVersion!=='ea-factory-v1')return false;
 state.eaFactoryReadModel.payload=payload.eaFactory;state.eaFactoryReadModel.stale=false;state.eaFactoryReadModel.lastError=null;return true;};
const setEaFactoryActionState=(value)=>actions.push(value);
const eaFactoryReadModelFailurePresentation=()=>({kind:'schema',tone:'error',message:'invalid schema'});
'''
        proc = subprocess.run([node, '-'], input=support+code+'\n(async()=>{'+body+'})().catch(e=>{console.error(e);process.exitCode=1;});', capture_output=True, text=True, encoding='utf-8', timeout=20, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_deferred_retains_display_and_selection_but_never_merges_authority(self):
        self.run_js(r'''
response={...deferred(),eaFactory:{schemaVersion:'ea-factory-v1',canRun:true}};
assert.equal(await loadEaFactoryReadModel(),null);
assert.equal(calls,1);assert.equal(merges,0);
assert.equal(state.eaFactoryReadModel.payload,oldModel);assert.equal(state.eaFactoryReadModel.busy,oldBusy);
assert.equal(state.eaFactoryReadModel.lastLoadedAt,123);assert.equal(state.eaFactoryReadModel.stale,true);
assert.equal(state.modal.eaFactory.selectedBuildId,'original-build');assert.equal(actions[0].tone,'working');
assert.equal(state.eaFactoryReadModel.inFlight,false);assert.equal(eaFactoryReadModelInFlight,null);
''')

    def test_initial_deferred_is_not_fresh_and_does_not_replace_an_active_action(self):
        self.run_js(r'''
state.eaFactoryReadModel.payload=null;state.eaFactoryReadModel.lastLoadedAt=0;
state.modal.eaFactory.inFlight=true;state.modal.eaFactory.stageId='source_recovery';response=deferred();
await loadEaFactoryReadModel();assert.equal(state.eaFactoryReadModel.payload,null);
assert.equal(state.eaFactoryReadModel.lastLoadedAt,0);assert.equal(state.eaFactoryReadModel.stale,true);
assert.equal(actions.length,0);assert.equal(state.modal.eaFactory.stageId,'source_recovery');
''')

    def test_next_fresh_model_can_replace_deferred_and_malformed_receipt_fails_closed(self):
        self.run_js(r'''
response=deferred();await loadEaFactoryReadModel();
response={eaFactory:{schemaVersion:'ea-factory-v1',builds:[{id:'original-build',status:'completed'}]}};
assert.equal(await loadEaFactoryReadModel(),response);assert.equal(merges,1);assert.equal(state.eaFactoryReadModel.stale,false);
response={...deferred(),readinessConfirmed:true,eaFactory:{schemaVersion:'ea-factory-v1',canRun:true}};await loadEaFactoryReadModel();
assert.equal(merges,1);
assert.equal(state.eaFactoryReadModel.payload,null);assert.equal(state.eaFactoryReadModel.busy,null);
assert.equal(state.eaFactoryReadModel.lastLoadedAt,0);assert.equal(state.eaFactoryReadModel.lastError.kind,'schema');
''')

    def test_aborted_deferred_response_does_not_change_current_display(self):
        self.run_js(r'''
const controller=new AbortController();response=deferred();afterFetch=()=>controller.abort();
await loadEaFactoryReadModel({signal:controller.signal});assert.equal(merges,0);assert.equal(actions.length,0);
assert.equal(state.eaFactoryReadModel.payload,oldModel);assert.equal(state.eaFactoryReadModel.stale,false);
''')
