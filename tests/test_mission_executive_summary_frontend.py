"""Exercise exact Manager report navigation without browser or Runtime calls."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MissionExecutiveSummaryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        start = cls.main.index("function getMissionExecutiveSummaryId(")
        cls.source = cls.main[start:cls.main.index("function renderMissionDetail(", start)]
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for report navigation tests")

    def run_case(self, scenario):
        harness = r"""
const vm = require('node:vm');
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.listeners = {}; this.textContent = ''; this.disabled = false; }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.children.push(child); }
  setAttribute(key, value) { this.attributes[key] = value; }
  addEventListener(type, callback) { this.listeners[type] = callback; }
}
function fixture() {
  const requests = [], opened = [];
  const mission = {id: 'mission-parent', toolId: 'manager_delegate', owner: 'manager',
    targetId: 'mission_strategy_table', status: 'completed', phase: 'synthesized',
    delegation: {state: 'synthesized', finalReportId: 'report-summary'}, reportIds: ['report-summary']};
  const report = {id: 'report-summary', type: 'executive_summary', ownerAgentId: 'manager',
    linkedMissionId: 'mission-parent', linkedPropId: 'mission_strategy_table', status: 'ready',
    summary: 'Manager completed 3/3', findings: ['risk_guard: actual result 1', 'vps_watch: actual result 2', 'mission_archivist: actual result 3']};
  const context = {selected: mission, AbortController, PROP_REPORT_FETCH_TIMEOUT_MS: 10000,
    document: {createElement: tag => new Element(tag)}, els: {taskDetailDialog: {open: true}},
    getActiveTaskDetailMission: () => context.selected,
    fetchJson: (url, options) => new Promise((resolve, reject) => { requests.push({url, options, resolve, reject}); }),
    openDashboardResultDetail: (item, trigger) => opened.push({item, trigger}),
  };
  vm.createContext(context);
  vm.runInContext('let missionSummaryRequest = null;\n' + SOURCE, context);
  function controls() {
    const host = new Element('div');
    context.appendMissionExecutiveSummary(host, context.selected);
    const children = host.children[0]?.children || [];
    return {host, button: children[1], status: children[2]};
  }
  function response() { return {ok: true, readModel: 'report_detail_v1', report: structuredClone(report)}; }
  return {context, mission, report, requests, opened, controls, response};
}
(async () => {
SCENARIO
})().then(result => process.stdout.write(JSON.stringify(result))).catch(error => {
  process.stderr.write(error.stack); process.exitCode = 1;
});
""".replace("SOURCE", json.dumps(self.source)).replace("SCENARIO", scenario)
        result = subprocess.run(
            [self.node, "-e", harness], cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_button_is_only_for_bound_completed_manager_parent(self):
        result = self.run_case(r"""
const changes = [
  {toolId: 'codex_cli_task'}, {owner: 'ceo'}, {targetId: 'other'}, {status: 'running'},
  {phase: 'review_required'}, {delegation: {state: 'queued', finalReportId: 'report-summary'}},
  {delegation: {state: 'synthesized'}}, {reportIds: []},
  ...['../secret', 'report/secret', 'report\\secret', ' report-summary', 'https:evil', '', 123].map(finalReportId => ({delegation: {state: 'synthesized', finalReportId}, reportIds: [finalReportId]})),
];
const f = fixture();
const valid = f.context.getMissionExecutiveSummaryId(f.mission);
const invalid = changes.map(change => {
  f.context.selected = {...f.mission, ...change};
  return {id: f.context.getMissionExecutiveSummaryId(f.context.selected), sections: f.controls().host.children.length};
});
return {valid, invalid, requests: f.requests.length, absent: f.context.getMissionExecutiveSummaryId(null)};
""")
        self.assertEqual(result["valid"], "report-summary")
        self.assertIsNone(result["absent"])
        self.assertTrue(all(row == {"id": None, "sections": 0} for row in result["invalid"]))
        self.assertEqual(result["requests"], 0)

    def test_real_report_findings_open_in_existing_viewer_after_exact_get(self):
        result = self.run_case(r"""
const f = fixture(), ui = f.controls();
const before = {requests: f.requests.length, label: ui.button.textContent, popup: ui.button.attributes['aria-haspopup']};
ui.button.listeners.click();
const loading = ui.button.disabled;
f.requests[0].resolve(f.response());
await new Promise(resolve => setImmediate(resolve));
return {before, loading, url: f.requests[0].url, requestKeys: Object.keys(f.requests[0].options),
  findings: f.opened[0]?.item.findings, sameTrigger: f.opened[0]?.trigger === ui.button,
  disabled: ui.button.disabled, status: ui.status.textContent};
""")
        self.assertEqual(result["before"], {"requests": 0, "label": "เปิดรายงานสรุปรวม", "popup": "dialog"})
        self.assertTrue(result["loading"])
        self.assertEqual(result["url"], "/api/reports/report-summary")
        self.assertEqual(set(result["requestKeys"]), {"timeoutMs", "signal"})
        self.assertEqual(result["findings"], ["risk_guard: actual result 1", "vps_watch: actual result 2", "mission_archivist: actual result 3"])
        self.assertTrue(result["sameTrigger"])
        self.assertFalse(result["disabled"])
        self.assertEqual(result["status"], "")

    def test_wrong_or_unready_report_is_not_presented_as_success(self):
        result = self.run_case(r"""
const patches = [
  {ok: false}, {readModel: 'report_list_v1'}, {report: null},
  ...[{id: 'report-other'}, {type: 'agent_report'}, {ownerAgentId: 'risk_guard'},
    {linkedMissionId: 'mission-other'}, {linkedPropId: 'other'}, {status: 'blocked'}]
    .map(fields => ({reportPatch: fields})),
];
const results = [];
for (const patch of patches) {
  const f = fixture(), ui = f.controls();
  const pending = f.context.openMissionExecutiveSummary(f.mission.id, ui.button, ui.status);
  const response = {...f.response(), ...patch};
  if (patch.reportPatch) Object.assign(response.report, patch.reportPatch);
  f.requests[0].resolve(response); await pending;
  results.push({opened: f.opened.length, disabled: ui.button.disabled, message: ui.status.textContent});
}
return results;
""")
        for row in result:
            self.assertEqual(row["opened"], 0)
            self.assertFalse(row["disabled"])
            self.assertIn("ไม่ตรงกับ Mission", row["message"])

    def test_changed_selection_or_final_report_discards_late_response(self):
        result = self.run_case(r"""
const results = [];
for (const change of ['mission', 'report', 'status', 'closed']) {
  const f = fixture(), ui = f.controls();
  const pending = f.context.openMissionExecutiveSummary(f.mission.id, ui.button, ui.status);
  if (change === 'mission') f.context.selected = {...f.mission, id: 'mission-other'};
  if (change === 'report') f.context.selected = {...f.mission, reportIds: ['report-new'], delegation: {state: 'synthesized', finalReportId: 'report-new'}};
  if (change === 'status') f.context.selected = {...f.mission, status: 'blocked'};
  if (change === 'closed') f.context.els.taskDetailDialog.open = false;
  f.requests[0].resolve(f.response()); await pending;
  results.push(f.opened.length);
}
return results;
""")
        self.assertEqual(result, [0, 0, 0, 0])

    def test_cancelled_request_cannot_replace_a_reopened_mission_report(self):
        result = self.run_case(r"""
const f = fixture(), first = f.controls();
const oldPending = f.context.openMissionExecutiveSummary(f.mission.id, first.button, first.status);
f.context.cancelMissionSummaryRequest();
const second = f.controls();
const newPending = f.context.openMissionExecutiveSummary(f.mission.id, second.button, second.status);
f.requests[0].resolve(f.response()); await oldPending;
const midway = {opened: f.opened.length, disabled: second.button.disabled, aborted: f.requests[0].options.signal.aborted};
f.requests[1].resolve(f.response()); await newPending;
return {midway, opened: f.opened.length, newTrigger: f.opened[0]?.trigger === second.button};
""")
        self.assertEqual(result["midway"], {"opened": 0, "disabled": True, "aborted": True})
        self.assertEqual(result["opened"], 1)
        self.assertTrue(result["newTrigger"])

    def test_repeated_click_has_one_request_and_failure_can_be_retried(self):
        result = self.run_case(r"""
const f = fixture(), ui = f.controls();
const pending = f.context.openMissionExecutiveSummary(f.mission.id, ui.button, ui.status);
await f.context.openMissionExecutiveSummary(f.mission.id, ui.button, ui.status);
const firstCount = f.requests.length;
f.requests[0].reject(new Error('private server diagnostics')); await pending;
const failed = {message: ui.status.textContent, disabled: ui.button.disabled};
const retry = f.context.openMissionExecutiveSummary(f.mission.id, ui.button, ui.status);
f.requests[1].resolve(f.response()); await retry;
return {firstCount, failed, total: f.requests.length, opened: f.opened.length};
""")
        self.assertEqual(result["firstCount"], 1)
        self.assertFalse(result["failed"]["disabled"])
        self.assertIn("ลองอีกครั้ง", result["failed"]["message"])
        self.assertNotIn("private", result["failed"]["message"])
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["opened"], 1)

    def test_rerender_while_loading_restores_the_current_button_and_focus_target(self):
        result = self.run_case(r"""
const f = fixture(), first = f.controls();
const pending = f.context.openMissionExecutiveSummary(f.mission.id, first.button, first.status);
const refreshed = f.controls(), loading = refreshed.button.disabled;
f.requests[0].resolve(f.response()); await pending;
return {loading, disabled: refreshed.button.disabled, status: refreshed.status.textContent,
  currentTrigger: f.opened[0]?.trigger === refreshed.button};
""")
        self.assertEqual(result, {"loading": True, "disabled": False, "status": "", "currentTrigger": True})

    def test_navigation_hooks_cancel_pending_report_and_render_the_entry(self):
        detail = self.main.split("function renderMissionDetail(", 1)[1].split("function openTaskDetail(", 1)[0]
        self.assertIn("appendMissionExecutiveSummary(friendly, mission)", detail)
        for start, end in (
            ("function openTaskDetail(", "function closeTaskDetail("),
            ("function closeTaskDetail(", "function restoreTaskDetailReturnFocus("),
            ('els.taskDetailDialog?.addEventListener("close",', 'els.dashboardResultDetailClose?.addEventListener('),
        ):
            self.assertIn("cancelMissionSummaryRequest()", self.main.split(start, 1)[1].split(end, 1)[0])


class ManagerStructuredSummaryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        start = main.index("function normalizeManagerExecutiveSummary(")
        cls.source = main[start:main.index("function getDashboardWorkState(", start)]
        safe_start = main.index("function safeDashboardDisplayText(")
        cls.source += main[safe_start:main.index("function safeAgentChatReplyText(", safe_start)]
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for structured summary tests")

    def run_case(self, scenario):
        script = r"""
const vm = require('node:vm');
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.dataset = {}; this.textContent = ''; this.attributes = {}; }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.children.push(child); }
  setAttribute(key, value) { this.attributes[key] = value; }
  set innerHTML(value) { if (value) throw new Error('Backend content entered HTML'); this.children = []; }
}
const provenance = {sourceReportId: 'report-source-123', recordId: 'orb-record-9', snapshotDigest: 'a'.repeat(64)};
function reportFixture() {
  const agents = [['technical', 'optimization_agent'], ['price_action', 'backtest_analyst'], ['risk', 'risk_guard']].map(([roleId, ownerAgentId], index) => ({
    roleId, ownerAgentId, missionId: 'mission-' + index, reportId: 'report-' + index,
    summary: 'Role summary ' + roleId, sourceReference: {...provenance},
    keyPoints: ['fact', 'inference', 'unknown'].map((kind, point) => ({kind, topic: 'topic-' + point,
      statement: roleId + ' statement ' + point, evidenceIds: ['evidence-' + point]})),
    blockers: ['blocker-' + roleId], nextSteps: ['next-' + roleId],
  }));
  return {id: 'report-parent', linkedMissionId: 'mission-parent', linkedPropId: 'mission_strategy_table',
    type: 'executive_summary', ownerAgentId: 'manager', status: 'ready', summary: 'Generic complete 3/3',
    findings: ['legacy finding'], risks: ['legacy risk'], nextActions: ['legacy action'], metrics: {total: 3},
    managerSummary: {schemaVersion: 'manager-summary-v1', sourceReference: {...provenance}, overallSummary: 'Manager synthesis of the three distinct roles',
      keyPoints: [], blockers: ['combined blocker'], nextSteps: ['combined next step'], agents},
  };
}
function flattened(node) { return [node.textContent || '', ...node.children.flatMap(flattened)]; }
const body = new Element('div'), genericCalls = [];
const context = {HTMLElement: Element, document: {createElement: tag => new Element(tag), activeElement: null},
  els: {dashboardResultDialog: {open: false, showModal() {this.open = true;}}, dashboardResultDetailBody: body, dashboardResultDetailTitle: new Element('h2')},
  displayStatus: value => value, displayAgentName: value => value, getAgentIdFromOwner: value => value,
  formatThaiDateTime: value => value || '-', reportExecutionScope: () => null,
  appendDashboardResultFact: (container, label, value) => {const row = new Element('dd'); row.textContent = label + ': ' + value; container.appendChild(row);},
  appendDashboardMetricSection: () => genericCalls.push('metrics'),
  appendDashboardDetailList: (container, title, values) => genericCalls.push({title, values}),
  appendDashboardVisualEvidence: () => {}, appendDashboardSourceLinks: () => {}, appendDashboardArtifactLinks: () => {},
};
vm.createContext(context);
vm.runInContext('let dashboardResultShouldRestoreFocus; let dashboardResultReturnFocus;\n' + SOURCE, context);
SCENARIO
""".replace("SOURCE", json.dumps(self.source)).replace("SCENARIO", scenario)
        result = subprocess.run([self.node, "-e", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_complete_role_points_and_exact_source_ids_are_visible_without_preview_clipping(self):
        result = self.run_case(r"""
const report = reportFixture();
report.managerSummary.overallSummary = 'S'.repeat(5900) + ' OVERALL_END';
report.managerSummary.agents.forEach((agent, index) => {
  agent.summary = 'A'.repeat(1500) + ' AGENT_END_' + index;
  agent.keyPoints.forEach((point, p) => point.statement = 'P'.repeat(1100) + ' POINT_END_' + index + '_' + p);
});
context.openDashboardResultDetail(report);
process.stdout.write(JSON.stringify({text: flattened(body).join('\n'), genericCalls, panels: body.children.filter(node => node.className === 'dashboard-result-section manager-summary-agent').length}));
""")
        self.assertEqual(result["panels"], 3)
        self.assertEqual(result["genericCalls"], [])
        self.assertIn("OVERALL_END", result["text"])
        for index in range(3):
            self.assertIn(f"AGENT_END_{index}", result["text"])
            for point in range(3):
                self.assertIn(f"POINT_END_{index}_{point}", result["text"])
            self.assertIn(f"Mission ID: mission-{index}", result["text"])
            self.assertIn(f"Report ID: report-{index}", result["text"])
        for token in ["report-source-123", "orb-record-9", "a" * 64, "optimization_agent", "backtest_analyst", "risk_guard", "ข้อเท็จจริงจากแหล่งข้อมูล", "ข้อวิเคราะห์", "ยังไม่ยืนยัน", "evidence-2"]:
            self.assertIn(token, result["text"])
        self.assertNotIn("Generic complete 3/3", result["text"])

    def test_all_role_blockers_and_next_steps_are_preserved_including_full_parent_lists(self):
        result = self.run_case(r"""
const report = reportFixture(), summary = report.managerSummary;
summary.blockers = Array.from({length: 24}, (_, i) => 'parent-block-' + i);
summary.nextSteps = Array.from({length: 24}, (_, i) => 'parent-next-' + i);
summary.agents.forEach((agent, i) => {
  agent.blockers = Array.from({length: 8}, (_, j) => 'role-block-' + i + '-' + j);
  agent.nextSteps = Array.from({length: 8}, (_, j) => 'role-next-' + i + '-' + j);
});
context.openDashboardResultDetail(report);
process.stdout.write(JSON.stringify(flattened(body)));
""")
        for index in range(24):
            self.assertIn(f"parent-block-{index}", result)
            self.assertIn(f"parent-next-{index}", result)
        for role in range(3):
            for index in range(8):
                self.assertIn(f"role-block-{role}-{index}", result)
                self.assertIn(f"role-next-{role}-{index}", result)

    def test_wrong_role_binding_provenance_duplicates_and_malformed_points_fail_closed(self):
        result = self.run_case(r"""
const mutations = [
  r => r.managerSummary.schemaVersion = 'guessed-v2',
  r => r.managerSummary.sourceReference.recordId = '../other',
  r => r.managerSummary.sourceReference.snapshotDigest = 'bad',
  r => r.managerSummary.agents[0].sourceReference.recordId = 'different-record',
  r => r.managerSummary.agents[0].sourceReference.snapshotDigest = 'b'.repeat(64),
  r => r.managerSummary.agents[0].ownerAgentId = 'ceo',
  r => r.managerSummary.agents[0].roleId = 'price_action',
  r => r.managerSummary.agents[1].missionId = r.managerSummary.agents[0].missionId,
  r => r.managerSummary.agents[1].reportId = r.managerSummary.agents[0].reportId,
  r => r.managerSummary.agents[0].keyPoints = [],
  r => r.managerSummary.agents[0].keyPoints[0].kind = 'guaranteed',
  r => r.managerSummary.agents[0].keyPoints[0].statement = 'x'.repeat(1201),
  r => r.managerSummary.agents[0].keyPoints[0].evidenceIds = [],
  r => r.managerSummary.agents[0].nextSteps = null,
];
const invalid = mutations.map(mutate => {const report = reportFixture(); mutate(report); return context.normalizeManagerExecutiveSummary(report) === null;});
const report = reportFixture(); report.managerSummary.agents[0].sourceReference.recordId = 'other';
context.openDashboardResultDetail(report);
process.stdout.write(JSON.stringify({invalid, text: flattened(body).join('\n'), genericCalls}));
""")
        self.assertTrue(all(result["invalid"]))
        self.assertIn("ข้อมูลสรุปของ Manager ไม่ครบหรือแหล่งข้อมูลไม่ตรงกัน", result["text"])
        self.assertNotIn("Generic complete 3/3", result["text"])
        self.assertNotIn("technical statement", result["text"])
        self.assertEqual(result["genericCalls"], [])

    def test_single_role_and_empty_lists_do_not_invent_additional_agents_or_findings(self):
        result = self.run_case(r"""
const report = reportFixture(), summary = report.managerSummary;
summary.agents = [summary.agents[2]]; summary.blockers = []; summary.nextSteps = [];
summary.agents[0].blockers = []; summary.agents[0].nextSteps = [];
context.openDashboardResultDetail(report);
process.stdout.write(JSON.stringify({accepted: !!context.normalizeManagerExecutiveSummary(report), text: flattened(body).join('\n')}));
""")
        self.assertTrue(result["accepted"])
        self.assertIn("risk_guard", result["text"])
        self.assertNotIn("optimization_agent", result["text"])
        self.assertIn("ไม่มีรายการข้อขัดข้องที่ระบุในรายงานนี้", result["text"])

    def test_structured_text_stays_text_and_sensitive_values_stay_redacted(self):
        result = self.run_case(r"""
const report = reportFixture();
report.managerSummary.agents[0].keyPoints[0].statement = '<img src=x onerror=alert(1)> api_key=never-show-this';
context.openDashboardResultDetail(report);
process.stdout.write(JSON.stringify(flattened(body).join('\n')));
""")
        self.assertIn("<img src=x onerror=alert(1)>", result)
        self.assertNotIn("never-show-this", result)
        self.assertIn("[ปกปิด]", result)

    def test_legacy_and_non_manager_reports_keep_existing_renderer(self):
        result = self.run_case(r"""
const report = reportFixture(); delete report.managerSummary;
context.openDashboardResultDetail(report);
process.stdout.write(JSON.stringify({text: flattened(body).join('\n'), genericCalls}));
""")
        self.assertIn("Generic complete 3/3", result["text"])
        self.assertEqual(result["genericCalls"], ["metrics", {"title": "สิ่งที่พบ", "values": ["legacy finding"]}, {"title": "ความเสี่ยงหรือข้อควรระวัง", "values": ["legacy risk"]}, {"title": "ขั้นตอนถัดไป", "values": ["legacy action"]}])


if __name__ == "__main__":
    unittest.main()
