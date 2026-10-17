"""Queued/deferred work must not look like a process that has started."""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MissionQueueTruthFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for Mission status tests")
        functions = []
        for name in ["safeDashboardDisplayText", "normalizeMissionStatus", "getMissionPresentationStatus", "getMissionWaitingPresentation",
                     "getMissionCenterColumnStatus", "createTaskCard", "getMissionNextStep", "renderMissionKanban"]:
            start = re.search(r"^(?:async )?function " + name + r"\(", cls.main, re.M)
            end = re.search(r"^(?:async )?function ", cls.main[start.end():], re.M)
            functions.append(cls.main[start.start():start.end() + end.start()])
        cls.source = "\n".join(functions)

    def run_case(self, scenario):
        script = r"""
const vm = require('node:vm');
class Element {
  constructor(tag) {this.tagName=tag; this.children=[]; this.dataset={}; this.attributes={}; this.textContent=''; this.classList={toggle(){}};}
  append(...nodes) {this.children.push(...nodes);} appendChild(node) {this.children.push(node);}
  set innerHTML(value) {this.children=[];} setAttribute(key,value){this.attributes[key]=value;}
  addEventListener(){} querySelectorAll(){return [];}
}
const board = new Element('div');
const state = {missions: [], modal: {selectedMissionId:null, kanbanScrollTop:{}, showArchived:false, searchText:''}};
const context = {state, document:{createElement:tag=>new Element(tag)}, els:{modalKanbanBoard:board},
  MISSION_KANBAN_COLUMNS:[{id:'running',label:'กำลังทำงาน'},{id:'blocked',label:'ติดขัด'},{id:'completed',label:'เสร็จแล้ว'},{id:'failed',label:'ไม่สำเร็จ'}],
  displayStatus: status=>({queued:'รับงานแล้ว',running:'กำลังทำงาน',completed:'เสร็จแล้ว',blocked:'ติดขัด',failed:'ไม่สำเร็จ'}[status] || status),
  isBackendAutoEligibleMission:()=>true, displayAgentName:id=>id, getAgentIdFromOwner:id=>id, displayPropName:id=>id,
  missionRequiresExplicitHumanApproval: mission=>mission.requiresHumanApproval === true && mission.approval?.required === true,
  isMissionReadyForExplicitExecution:()=>false, missionMatchesSearch:()=>true, refreshOpenTaskDetail:()=>{},
};
vm.createContext(context); vm.runInContext(SOURCE,context);
const child = owner => ({id:'mission-'+owner, owner, title:owner, status:'queued', phase:'auto_guarded_deferred',
  runnerStatus:'codex_limit_reached', dispatchState:'deferred', startedAt:null, targetId:'mission_strategy_table'});
const parent = {id:'mission-parent',owner:'manager',title:'Manager analysis',toolId:'manager_delegate',status:'queued',
  phase:'awaiting_specialist_start',subtaskIds:['mission-optimization_agent','mission-backtest_analyst','mission-risk_guard'],
  delegation:{subtaskCount:3,subtaskStatusCounts:{queued:3,running:0}}};
const flatten = node=>[node.textContent,...node.children.map(flatten)].join(' ');
SCENARIO
""".replace("SOURCE", json.dumps(self.source)).replace("SCENARIO", scenario)
        result = subprocess.run([self.node, "-e", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_all_three_quota_deferred_children_and_parent_are_waiting_not_running(self):
        result = self.run_case("""
state.missions=[parent,...['optimization_agent','backtest_analyst','risk_guard'].map(child)];
const before=JSON.stringify(state.missions); context.renderMissionKanban();
const column=board.children[0];
process.stdout.write(JSON.stringify({label:column.children[0].children[0].textContent,count:column.children[0].children[1].textContent,
 cards:column.children[1].children.map(flatten),unchanged:before===JSON.stringify(state.missions)}));
""")
        self.assertEqual((result["label"], result["count"]), ("รอเริ่มงาน", "4"))
        self.assertIn("Manager รอ Agent เริ่มงาน", result["cards"][0])
        for card in result["cards"][1:]:
            self.assertIn("รอโควตา Codex", card)
            self.assertIn("codex_limit_reached", card)
            self.assertIn("งานยังรอคิว", card)
            self.assertNotIn("ยังไม่ได้เริ่มรัน", card)
            self.assertNotIn("กำลังทำงาน", card)
            self.assertNotIn("Backend ดูแลงานนี้อัตโนมัติ", card)
        self.assertTrue(result["unchanged"])

    def test_detail_next_step_uses_quota_reason_and_parent_zero_started_children(self):
        result = self.run_case("""
const zero={...parent,status:'running',delegation:{subtaskCount:3,subtaskStatusCounts:{queued:0,running:0}}};
process.stdout.write(JSON.stringify({child:context.getMissionNextStep(child('risk_guard')),
 explicitNotStarted:context.getMissionNextStep({...child('risk_guard'),execution:{processStarted:false}}),
 parent:context.getMissionNextStep(parent),zero:context.getMissionWaitingPresentation(zero),
 card:flatten(context.createTaskCard(zero,{source:'kanban',statusOverride:'running'}))}));
""")
        self.assertIn("codex_limit_reached", result["child"])
        self.assertIn("ยังไม่มีผลใหม่", result["child"])
        self.assertIn("ยังไม่ได้เริ่มรัน", result["explicitNotStarted"])
        self.assertNotIn("ยังไม่ได้เริ่มรัน", result["child"])
        self.assertNotIn("Runner ว่าง", result["child"])
        self.assertIn("ยังรอเริ่ม", result["parent"])
        self.assertEqual(result["zero"]["label"], "Manager รอ Agent เริ่มงาน")
        self.assertNotIn("กำลังทำงาน", result["card"])
        self.assertIn('appendMissionDetailRow(facts, "สถานะ", getMissionWaitingPresentation(mission)?.label || displayStatus(presentationStatus));', self.main)

    def test_real_running_and_terminal_states_ignore_stale_quota_markers(self):
        result = self.run_case("""
const cases=['running','completed','failed','blocked'].map(status=>({...child('risk_guard'),status,execution:{processStarted:true,lastDeferredReason:'codex_limit_reached'}}));
const activeParent={...parent,delegation:{subtaskCount:3,subtaskStatusCounts:{running:1,queued:2}}};
process.stdout.write(JSON.stringify({cases:cases.map(m=>({status:m.status,waiting:context.getMissionWaitingPresentation(m),text:flatten(context.createTaskCard(m))})),
 parent:context.getMissionWaitingPresentation(activeParent)}));
""")
        for row in result["cases"]:
            self.assertIsNone(row["waiting"])
            self.assertNotIn("รอโควตา", row["text"])
        self.assertIn("กำลังทำงาน", result["cases"][0]["text"])
        self.assertIsNone(result["parent"])

    def test_mixed_queue_column_labels_both_states_and_approval_guard_stays_blocked(self):
        result = self.run_case("""
state.missions=[child('risk_guard'),{...child('optimization_agent'),status:'running',phase:'auto_guarded_running',execution:{processStarted:true}},
 {id:'mission-approval',owner:'ceo',status:'waiting_approval',requiresHumanApproval:true,approval:{required:true}}];
context.renderMissionKanban();
process.stdout.write(JSON.stringify({labels:board.children.map(c=>c.children[0].children[0].textContent),
 counts:board.children.map(c=>c.children[0].children[1].textContent),approval:flatten(board.children[1].children[1])}));
""")
        self.assertEqual(result["labels"][0], "กำลังทำงาน / รอคิว")
        self.assertEqual(result["counts"][:2], ["2", "1"])
        self.assertIn("ติดขัด", result["approval"])
        self.assertNotIn("รอโควตา", result["approval"])


if __name__ == "__main__":
    unittest.main()
