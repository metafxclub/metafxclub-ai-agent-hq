"""Exercise custom Source typing without replacing or refocusing the form."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FactoryCustomFormFrontendTests(unittest.TestCase):
    def run_js(self, body):
        main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        start = main.index("function renderEaFactoryCustomSourcePreview(")
        code = main[start:main.index("\nfunction renderEaFactorySpecStage(", start)]
        support = r'''
const assert=require('node:assert/strict');
const EA_FACTORY_PROP_ID='right_server_racks',EA_FACTORY_READ_MODEL_MAX_AGE_MS=15000;
let now=1000,locks=true,rerenders=0,submissions=0;Date.now=()=>now;
const created=[];
const makeElement=tag=>({tag,children:[],listeners:{},dataset:{},value:'',disabled:false,
 appendChild(item){this.children.push(item);return item;},append(...items){this.children.push(...items);},
 addEventListener(name,fn){this.listeners[name]=fn;}});
const document={activeElement:null,createElement(tag){const el=makeElement(tag);created.push(el);return el;}};
const state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{customSystemName:'',customConditions:'',customTemplateId:'',readContextRevision:1,inFlight:false}},
 eaFactoryReadModel:{payload:{schemaVersion:'ea-factory-v1'},lastLoadedAt:1000,stale:false}};
const domain={authoritative:true,canStartNewBuild:true,backendBusy:null};
const normalizeEaFactoryPlatform=value=>['mt4','mt5','tradingview'].includes(value)?value:'';
const normalizeEaFactoryArtifactKind=value=>['expert_advisor','custom_indicator'].includes(value)?value:'';
const eaFactoryTopHeaderLockPreflight=()=>({ready:locks});
const createEaFactoryNotice=()=>makeElement('notice');
const rerenderEaFactoryDashboardPreservingFocus=()=>{rerenders++;};
const createEaFactoryCustomSourceAndStart=()=>{submissions++;state.modal.eaFactory.inFlight=true;};
const eaFactoryEmaSmokeCustomSourcePayload=()=>({systemName:'EMA template',systemOverview:'overview',entryRules:'entry',exitRules:'exit',moneyManagement:'fixed lot',orderExecution:'closed bar'});
const render=(platform='mt5',artifactKind='expert_advisor')=>{
 created.length=0;const container=makeElement('container');renderEaFactoryCustomSourcePreview(container,domain,{platform,artifactKind});
 return {container,name:created.find(el=>el.tag==='input'),conditions:created.find(el=>el.tag==='textarea'),start:created.find(el=>el.className?.includes('ea-factory-start-button')),smoke:created.find(el=>el.tag==='button'&&!el.className?.includes('ea-factory-start-button'))};
};
const type=(input,value)=>{input.value=value;input.listeners.input();};
const valid=()=>{state.modal.eaFactory.customSystemName='EMA 10/60';state.modal.eaFactory.customConditions='Closed-bar cross; adjustable TP and SL; fixed lot.';};
'''
        node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")
        proc = subprocess.run([node, "-"], input=support + code + "\n" + body, capture_output=True,
                              text=True, encoding="utf-8", cwd=ROOT, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_typing_valid_fields_enables_button_without_rerender_or_focus_loss(self):
        self.run_js(r'''
const f=render();assert.equal(f.start.disabled,true);
type(f.name,'EMA 10/60');assert.equal(f.start.disabled,true);
document.activeElement=f.conditions;f.conditions.selectionStart=17;f.conditions.selectionEnd=17;
type(f.conditions,'Closed-bar cross with adjustable TP and SL.');assert.equal(f.start.disabled,false);
assert.equal(document.activeElement,f.conditions);assert.equal(f.conditions.selectionStart,17);assert.equal(f.conditions.selectionEnd,17);
assert.equal(rerenders,0);assert.equal(submissions,0);assert.equal(f.container.children.length,1);
f.start.listeners.click();assert.equal(submissions,1);f.start.listeners.click();assert.equal(submissions,1);
''')

    def test_deleting_either_required_field_disables_button_and_clears_template_identity(self):
        self.run_js(r'''
valid();state.modal.eaFactory.customTemplateId='ema_10_60_smoke_v1';const f=render();assert.equal(f.start.disabled,false);
type(f.name,'  ab ');assert.equal(f.start.disabled,true);assert.equal(state.modal.eaFactory.customTemplateId,'');
type(f.name,'EMA 10/60');assert.equal(f.start.disabled,false);
type(f.conditions,'too short');assert.equal(f.start.disabled,true);f.start.listeners.click();assert.equal(submissions,0);
type(f.conditions,'Entry and exit with enough content.');assert.equal(f.start.disabled,false);
assert.equal(rerenders,0);
''')

    def test_typing_cannot_bypass_domain_busy_action_or_header_locks(self):
        self.run_js(r'''
for(const mutate of [()=>domain.authoritative=false,()=>domain.canStartNewBuild=false,
 ()=>domain.backendBusy={buildId:'active'},()=>state.modal.eaFactory.inFlight=true,()=>locks=false]){
 Object.assign(domain,{authoritative:true,canStartNewBuild:true,backendBusy:null});state.modal.eaFactory.inFlight=false;locks=true;
 valid();const f=render();assert.equal(f.start.disabled,false);mutate();type(f.name,'New valid name');assert.equal(f.start.disabled,true);
 f.start.listeners.click();assert.equal(submissions,0);
}
Object.assign(domain,{authoritative:true,canStartNewBuild:true,backendBusy:null});state.modal.eaFactory.inFlight=false;locks=true;
for(const pair of [['unknown','expert_advisor'],['mt5','unknown']]){const f=render(...pair);type(f.name,'Valid name');assert.equal(f.start.disabled,true);}
''')

    def test_click_revalidates_live_lock_and_dedicated_model_status(self):
        self.run_js(r'''
for(const mutate of [()=>locks=false,()=>state.eaFactoryReadModel.stale=true,
 ()=>state.eaFactoryReadModel.payload.snapshotStale=true,
 ()=>state.eaFactoryReadModel.payload={schemaVersion:'ea-factory-v1'}]){
 locks=true;now=1000;state.eaFactoryReadModel={payload:{schemaVersion:'ea-factory-v1'},lastLoadedAt:1000,stale:false};valid();
 const f=render();assert.equal(f.start.disabled,false);mutate();f.start.listeners.click();assert.equal(f.start.disabled,true);assert.equal(submissions,0);
}
''')

    def test_typing_longer_than_read_model_age_does_not_add_a_new_local_time_gate(self):
        self.run_js(r'''
const f=render();type(f.name,'EMA 10/60');now+=600000;
type(f.conditions,'A complete prompt typed for ten minutes with adjustable TP and SL.');
assert.equal(f.start.disabled,false);assert.equal(rerenders,0);
f.start.listeners.click();assert.equal(submissions,1);
''')

    def test_detached_form_or_changed_context_never_submits(self):
        self.run_js(r'''
for(const mutate of [()=>state.modal.open=false,()=>state.modal.id='another',
 ()=>state.modal.eaFactory={...state.modal.eaFactory},()=>state.modal.eaFactory.readContextRevision++]){
 state.modal.open=true;state.modal.id=EA_FACTORY_PROP_ID;valid();const f=render();assert.equal(f.start.disabled,false);
 mutate();type(f.conditions,'Valid conditions still cannot authorize detached form.');f.start.listeners.click();
 assert.equal(f.start.disabled,true);assert.equal(submissions,0);assert.equal(rerenders,0);
}
''')


if __name__ == "__main__":
    unittest.main()
