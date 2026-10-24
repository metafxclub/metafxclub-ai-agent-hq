"""Execute the bounded, read-only Factory polling path without a Build."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InitialDeferredFactoryPollTests(unittest.TestCase):
    def run_js(self, body):
        main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        start = main.index("function stopEaFactoryActiveProgressPolling(")
        code = main[start:main.index("\nfunction createEaFactoryStopButton(", start)]
        start = main.index("function renderEaFactoryReadModelNotice(")
        code += main[start:main.index("\nfunction eaFactoryReadModelStateKey(", start)]
        support = r'''
const assert = require('node:assert/strict');
const EA_FACTORY_PROP_ID='right_server_racks', EA_FACTORY_ACTIVE_POLL_MS=3000;
let eaFactoryActiveProgressPollTimer=null, eaFactoryDeferredReadPollingContext=null;
let now=1000,nextId=1,reads=0,renders=0,progressActive=false,readHook=null;
const timers=new Map(),pending=[];Date.now=()=>now;
globalThis.window={setTimeout:(fn,ms)=>{const id=nextId++;timers.set(id,{fn,at:now+ms});return id;},clearTimeout:id=>timers.delete(id)};
globalThis.document={visibilityState:'visible'};
let state={modal:{open:true,id:EA_FACTORY_PROP_ID,eaFactory:{inFlight:false,readContextRevision:1}},
 eaFactoryReadModel:{inFlight:false,payload:null,stale:true,lastLoadedAt:0,lastError:{kind:'refreshing',message:'checking'}}};
const eaFactoryPhaseGateProgress=()=>({shouldPoll:progressActive});
const renderGameModal=()=>{renders++;scheduleEaFactoryActiveProgressPolling({});};
const fresh=()=>{state.eaFactoryReadModel.payload={schemaVersion:'ea-factory-v1',builds:[]};state.eaFactoryReadModel.stale=false;state.eaFactoryReadModel.lastError=null;};
const loadEaFactoryReadModel=async options=>{
 reads++;state.eaFactoryReadModel.inFlight=true;
 try {if(readHook) await readHook(options);return state.eaFactoryReadModel.payload;}
 finally {state.eaFactoryReadModel.inFlight=false;}
};
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const advance=async ms=>{
 const target=now+ms;
 while(true){const next=[...timers].filter(([,t])=>t.at<=target).sort((a,b)=>a[1].at-b[1].at)[0];
  if(!next)break;now=next[1].at;timers.delete(next[0]);
  const value=next[1].fn();if(value?.then)pending.push(value);await flush();
 }now=target;await flush();
};
const createEaFactoryGameAction=(label,fn)=>({label,fn,disabled:false});
const createEaFactoryNotice=(tone,title,message)=>({tone,title,message});
const eaFactoryBusyPresentation=()=>null,formatThaiDateTime=value=>value;
'''
        node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")
        proc = subprocess.run([node, "-"], input=support + code + "\n(async()=>{" + body + "})().catch(e=>{console.error(e);process.exitCode=1;});",
                              capture_output=True, text=True, encoding="utf-8", timeout=15, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_no_build_refreshes_until_fresh_with_one_timer_and_no_action(self):
        self.run_js(r'''
readHook=async()=>{renderGameModal();if(reads===2)fresh();};
scheduleEaFactoryActiveProgressPolling({});const deadline=eaFactoryDeferredReadPollingContext.deadline;
for(let i=0;i<10;i++)renderGameModal();assert.equal(timers.size,1);
await advance(3000);assert.equal(reads,1);assert.equal(eaFactoryDeferredReadPollingContext.deadline,deadline);
await advance(3000);assert.equal(reads,2);assert.equal(state.eaFactoryReadModel.stale,false);
assert.equal(timers.size,0);assert.equal(eaFactoryDeferredReadPollingContext,null);
assert.equal(state.modal.eaFactory.inFlight,false);assert.equal(state.modal.eaFactory.selectedBuildId,undefined);
await advance(60000);assert.equal(reads,2);
''')

    def test_deadline_survives_renders_and_manual_refresh_starts_new_window(self):
        self.run_js(r'''
scheduleEaFactoryActiveProgressPolling({});const deadline=eaFactoryDeferredReadPollingContext.deadline;
await advance(45000);const oldReads=reads;assert.equal(oldReads,14);assert.equal(timers.size,0);
for(let i=0;i<50;i++)renderGameModal();assert.equal(timers.size,0);assert.equal(eaFactoryDeferredReadPollingContext.deadline,deadline);
await advance(30000);assert.equal(reads,oldReads);
await refreshEaFactoryProgressStatus();assert.equal(reads,oldReads+1);
assert.equal(eaFactoryDeferredReadPollingContext.deadline,now+45000);assert.equal(timers.size,1);
''')

    def test_closed_hidden_replaced_or_revised_context_never_issues_scheduled_read(self):
        self.run_js(r'''
for(const change of [()=>state.modal.open=false,()=>document.visibilityState='hidden',
 ()=>state.modal.eaFactory={...state.modal.eaFactory},()=>state.modal.eaFactory.readContextRevision++]){
 state.modal.open=true;document.visibilityState='visible';stopEaFactoryActiveProgressPolling({resetRefresh:true});
 scheduleEaFactoryActiveProgressPolling({});change();await advance(3000);
 assert.equal(reads,0);assert.equal(timers.size,0);assert.equal(eaFactoryDeferredReadPollingContext,null);
}
''')

    def test_pending_read_is_aborted_on_close_and_cannot_restart(self):
        self.run_js(r'''
let signal;
readHook=options=>new Promise(resolve=>{signal=options.signal;signal.addEventListener('abort',resolve,{once:true});});
scheduleEaFactoryActiveProgressPolling({});await advance(3000);assert.equal(reads,1);assert.equal(signal.aborted,false);
state.modal.open=false;stopEaFactoryActiveProgressPolling({resetRefresh:true});await flush();
assert.equal(signal.aborted,true);assert.equal(timers.size,0);await advance(60000);assert.equal(reads,1);
''')

    def test_read_cannot_outlive_remaining_window(self):
        self.run_js(r'''
let lastSignal;
readHook=options=>{if(reads===14)return new Promise(resolve=>{lastSignal=options.signal;lastSignal.addEventListener('abort',resolve,{once:true});});};
scheduleEaFactoryActiveProgressPolling({});await advance(42000);assert.equal(reads,14);assert.equal(lastSignal.aborted,false);
await advance(3000);assert.equal(lastSignal.aborted,true);assert.equal(timers.size,0);
assert.equal(state.eaFactoryReadModel.stale,true);renderGameModal();await advance(60000);assert.equal(reads,14);
''')

    def test_hard_error_stops_and_existing_active_build_poll_remains(self):
        self.run_js(r'''
readHook=async()=>{state.eaFactoryReadModel.lastError={kind:'integrity_blocked',message:'blocked'};};
scheduleEaFactoryActiveProgressPolling({});await advance(3000);assert.equal(reads,1);assert.equal(timers.size,0);
for(const kind of ['schema','transport','backend_error']){state.eaFactoryReadModel.lastError={kind};renderGameModal();assert.equal(timers.size,0);}
progressActive=true;readHook=async()=>{};renderGameModal();await advance(3000);assert.equal(reads,2);assert.equal(timers.size,1);
progressActive=false;state.eaFactoryReadModel.lastError=null;renderGameModal();assert.equal(timers.size,0);
''')

    def test_manual_retry_button_is_read_only_and_disabled_during_owned_read_or_action(self):
        self.run_js(r'''
const section={items:[],appendChild(item){this.items.push(item);}};
renderEaFactoryReadModelNotice(section);const button=section.items[1];assert.equal(button.label,'ตรวจสถานะล่าสุด');assert.equal(button.disabled,false);
button.fn();await flush();assert.equal(reads,1);assert.equal(state.modal.eaFactory.inFlight,false);
for(const busy of ['read','action']){section.items=[];state.eaFactoryReadModel.inFlight=busy==='read';state.modal.eaFactory.inFlight=busy==='action';
 renderEaFactoryReadModelNotice(section);assert.equal(section.items[1].disabled,true);}
state.eaFactoryReadModel.inFlight=true;await refreshEaFactoryProgressStatus();assert.equal(reads,1);
''')

    def test_notice_shared_by_all_pages_and_lifecycle_hooks_stop_reads(self):
        main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        panel = main[main.index("function renderEaFactoryPanel("):main.index("function renderEaFactoryPanel(") + 650]
        self.assertLess(panel.index("renderEaFactoryReadModelNotice(section)"), panel.index('if (tabId === "source")'))
        for start, end in [("function openGameModal(", "function closeGameModal("),
                           ("function closeGameModal(", "function openAgentDialog(")]:
            block = main[main.index(start):main.index(end)]
            self.assertIn("stopEaFactoryActiveProgressPolling({ resetRefresh: true })", block)
        self.assertIn('else {\n    stopMeetingRoomPolling();\n    stopEaFactoryActiveProgressPolling({ resetRefresh: true });', main)


if __name__ == "__main__":
    unittest.main()
