"""Execute recovery UI admission and request identity without an actual backend."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceRecoveryFrontendTests(unittest.TestCase):
    def run_js(self, body):
        main = (ROOT/'frontend/src/app/main.js').read_text(encoding='utf-8')
        code = main[main.index('function eaFactorySourceRecoveryAdmission'):main.index('function renderEaFactoryProgressPage')]
        node = shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
        support = r'''
const assert=require('node:assert/strict');
const crypto=require('node:crypto').webcrypto;
const EA_FACTORY_PROP_ID='right_server_racks';
let state,domain,posts,reads,actions,responseChange;
const getModalSubject=()=>({}),getPropertyRole=()=>({});
const normalizeWorkflowDashboard=()=>({domainData:{eaFactory:domain}});
const safeDashboardDisplayText=(value,fallback='')=>value||fallback;
const loadEaFactoryReadModel=async()=>{reads++;};
const setEaFactoryActionState=value=>actions.push(value);
const runEaFactoryRequest=async(stage,request,_message,options)=>{
  assert.equal(stage,'source_recovery');assert.equal(options.refreshReadModel,false);
  if(state.modal.eaFactory.inFlight||!options.isCurrent())return null;
  state.modal.eaFactory.inFlight=true;
  try{return await request();}catch(e){actions.push(e);return null;}
  finally{state.modal.eaFactory.inFlight=false;}
};
const postEaFactoryJson=async(endpoint,payload)=>{
  posts.push({endpoint,payload});
  return {...payload,ok:true,kind:'ea_factory_source_recovered',buildId:domain.activeBuild.id,
    requestIdempotencyKey:payload.idempotencyKey,workerStarted:false,idempotentReplay:false,
    sourceDigest:'b'.repeat(64),...responseChange};
};
function fixture(){
  posts=[];reads=0;actions=[];responseChange={};
  state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{selectedBuildId:'ea-build-old',readContextRevision:1,inFlight:false}},
    eaFactoryReadModel:{stale:false,payload:{snapshotStale:false}},propReports:{}};
  domain={authoritative:true,backendBusy:null,activeBuild:{id:'ea-build-old',platform:'mt5',artifactKind:'expert_advisor',raw:{sourceRecovery:{
    eligible:true,endpoint:'/api/props/right_server_racks/ea-factory/builds/ea-build-old/recover-source',
    strategySpecDigest:'a'.repeat(64),failedMissionId:'mission-failed',failureReportId:'report-failed'}}}};
}
const file=(content='source')=>({name:'Elder.mq5',size:content.length,text:async()=>content});
'''
        proc = subprocess.run([node,'-'],input=support+code+'\n(async()=>{'+body+'})().catch(e=>{console.error(e);process.exitCode=1;});',
                              capture_output=True,text=True,encoding='utf-8',timeout=20,cwd=ROOT)
        self.assertEqual(proc.returncode,0,proc.stderr)

    def test_stale_foreign_busy_and_unselected_context_never_admit(self):
        self.run_js(r'''
for(const mutate of [()=>domain.authoritative=false,()=>domain.backendBusy={},()=>state.eaFactoryReadModel.stale=true,
  ()=>state.eaFactoryReadModel.payload.snapshotStale=true,()=>state.modal.open=false,()=>state.modal.id='other',
  ()=>state.modal.eaFactory.inFlight=true,()=>state.modal.eaFactory.selectedBuildId='ea-build-other',
  ()=>domain.activeBuild.raw.sourceRecovery.endpoint='/api/other',()=>domain.activeBuild.raw.sourceRecovery.eligible=false,
  ()=>domain.activeBuild.raw.sourceRecovery.strategySpecDigest='bad']){
  fixture();const expected=eaFactorySourceRecoveryAdmission(domain);mutate();
  assert.equal(eaFactorySourceRecoveryAdmission(domain).canSubmit,false);
  await submitEaFactorySourceRecovery(expected,file());assert.equal(posts.length,0);
}
''')

    def test_exact_file_replay_uses_same_key_after_reload_without_starting_work(self):
        self.run_js(r'''
fixture();await submitEaFactorySourceRecovery(eaFactorySourceRecoveryAdmission(domain),file());
assert.equal(posts.length,1);assert.equal(reads,1);assert.equal(state.eaFactoryReadModel.stale,true);
const first=posts[0];assert.deepEqual(Object.keys(first.payload).sort(),['content','failedMissionId','failureReportId','fileName','idempotencyKey','strategySpecDigest']);
fixture();await submitEaFactorySourceRecovery(eaFactorySourceRecoveryAdmission(domain),file());
assert.deepEqual(posts[0],first);
fixture();await submitEaFactorySourceRecovery(eaFactorySourceRecoveryAdmission(domain),file('revised'));
assert.notEqual(posts[0].payload.idempotencyKey,first.payload.idempotencyKey);
''')

    def test_file_bounds_and_context_change_during_read_prevent_post(self):
        self.run_js(r'''
for(const bad of [{name:'Elder.mq4'},{name:'../Elder.mq5'},{size:49153},{size:0}]){
 fixture();await submitEaFactorySourceRecovery(eaFactorySourceRecoveryAdmission(domain),{...file(),...bad});assert.equal(posts.length,0);
}
fixture();const expected=eaFactorySourceRecoveryAdmission(domain);
await submitEaFactorySourceRecovery(expected,{...file(),text:async()=>{state.modal.eaFactory.readContextRevision++;return 'source';}});
assert.equal(posts.length,0);
''')

    def test_foreign_receipt_cannot_claim_success_or_merge_readiness(self):
        self.run_js(r'''
fixture();responseChange={buildId:'ea-build-other',eaFactory:{canRun:true},mission:{id:'fake'}};
const receipt=await submitEaFactorySourceRecovery(eaFactorySourceRecoveryAdmission(domain),file());
assert.equal(receipt,null);assert.equal(actions.length,1);assert.equal(reads,1);
assert.equal(state.eaFactoryReadModel.stale,true);
''')
