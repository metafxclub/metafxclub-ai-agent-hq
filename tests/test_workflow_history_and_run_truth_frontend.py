"""Keep World Radar history separate and preserve scheduled-run evidence."""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkflowHistoryAndRunTruthFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for dashboard behavior tests")

    def function(self, name):
        match = re.search(r"^(?:async )?function " + re.escape(name) + r"\(", self.main, re.M)
        end = re.search(r"^(?:async )?function ", self.main[match.end():], re.M)
        return self.main[match.start():match.end() + end.start()] if end else self.main[match.start():]

    def run_node(self, script):
        result = subprocess.run([self.node, "-"], input=script, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_history_refresh_preserves_selected_tab_and_shows_reports_without_latest_system_cards(self):
        source = "\n".join(self.function(name) for name in ["getWorkflowSelectedTab", "renderWorkflowDomainPanel", "renderWorkflowDashboard", "setWorkflowDashboardTab"])
        script = r"""
const vm = require('node:vm');
const portal = {id: 'codex_mcp_portal'};
const report = {reports: [{id: 'report-history-real', title: 'Stored verified report'}]};
const content = {children: [], hidden: false, set innerHTML(value) {this.children = [];}, get childElementCount() {return this.children.length;}, appendChild(node) {this.children.push(node);}};
const resultPanel = {hidden: true, dataset: {}, rows: []};
let latestSystemCalls = 0, selectedTab;
const state = {modal: {workflowTabs: {}, workflowVoice: {}}, propReports: {codex_mcp_portal: report}};
const context = {
  state, WORKFLOW_DASHBOARD_HISTORY_TAB_IDS: new Set(['history']),
  EA_FACTORY_PROP_ID: 'right_server_racks', EA_OPTIMIZATION_LAB_PROP_ID: 'right_tool_console',
  TRADING_RESEARCH_LAB_PROP_ID: 'left_server_racks', FX_NEWS_BIAS_PROP_ID: 'left_signal_cube', INDICATOR_SCOUT_PROP_ID: 'left_audit_crystals',
  els: {workflowDashboardContent: content, workflowResultsPanel: resultPanel},
  getModalSubject: () => portal, getPropertyRole: () => ({}),
  isWorkflowDashboardPropId: id => id === portal.id,
  normalizeWorkflowDashboard: () => ({tabs: [{id:'today', actionIds:[]}, {id:'catalog',actionIds:[]}, {id:'history',actionIds:[]}], actions: [], domainData: {tradingSystemPortal: {systems: [{id: 'latest'}]}}}),
  getWorkflowDashboardIdentity: () => ({id:'world-radar'}), renderWorkflowSettingsRail: () => {}, renderWorkflowAgentHandoff: () => {},
  renderWorkflowTabs: (id, dashboard, selected) => {selectedTab = selected.id;}, workflowRailActions: () => [],
  renderTradingSystemPortalPanel: host => {latestSystemCalls++; host.appendChild({textContent: 'Latest three systems'});},
  renderWorkflowResults: (subject, model) => {resultPanel.rows = model.reports;}, renderWorkflowActionStatus: () => {}, saveSessionSnapshot: () => {},
};
vm.createContext(context); vm.runInContext(SOURCE, context);
context.setWorkflowDashboardTab(portal.id, 'history');
context.renderWorkflowDashboard(portal, {}, report);
const history = {selectedTab, stored: state.modal.workflowTabs[portal.id], latestSystemCalls, contentHidden: content.hidden, reportsHidden: resultPanel.hidden, reportIds: resultPanel.rows.map(row => row.id)};
context.setWorkflowDashboardTab(portal.id, 'today');
const today = {selectedTab, latestSystemCalls, contentHidden: content.hidden, reportsHidden: resultPanel.hidden};
process.stdout.write(JSON.stringify({history, today}));
""".replace("SOURCE", json.dumps(source))
        result = self.run_node(script)
        self.assertEqual(result["history"], {"selectedTab": "history", "stored": "history", "latestSystemCalls": 0, "contentHidden": True, "reportsHidden": False, "reportIds": ["report-history-real"]})
        self.assertEqual(result["today"], {"selectedTab": "today", "latestSystemCalls": 1, "contentHidden": False, "reportsHidden": True})

    def test_authoritative_blocked_quarantined_radar_schedule_is_not_not_started_or_success(self):
        functions = "\n".join(self.function(name) for name in [
            "safeDashboardDisplayText", "workflowDomainObject", "workflowDomainArray", "workflowReportRows", "indicatorScoutObjectRows",
            "indicatorScoutBangkokDateKey", "filterIndicatorScoutToday", "filterIndicatorScoutRollingSevenDays",
            "normalizeRadarSchedule", "normalizeRadarServiceHealth", "normalizeRadarRunStatus", "radarBangkokMinuteOfDay",
            "normalizeRadarPublicationPolicy", "radarPublicationCountLabel", "getRadarTodayRunState", "normalizeIndicatorScoutDomain",
        ])
        script = r"""
const INDICATOR_SCOUT_DEFAULT_TIME = '09:00', INDICATOR_SCOUT_TIMEZONE = 'Asia/Bangkok', INDICATOR_SCOUT_EXPECTED_BATCH_SIZE = 6;
FUNCTIONS
const schedule = {lastAttemptAt: '2026-10-17T09:01:00+07:00', lastRunAt: '2026-10-17T09:01:00+07:00',
  lastMissionId: 'mission-1792202459217-1611d9', lastRunStatus: 'blocked', lastResultKind: 'radar_retry_quarantined',
  lastError: 'radar_retry_quarantined', status: 'daily_limit_reached', runsReservedToday: 1, remainingRunsToday: 0,
  nextRunAt: '2026-10-18T02:00:00Z'};
const backend = {schedule, leftRail: {schedule}, radarWebsiteTool: {schemaVersion: 'radar-website-tool-v1', todayEntries: [], sevenDayEntries: [], serviceHealth: {status: 'degraded'}}};
const before = JSON.stringify(backend);
const domain = normalizeIndicatorScoutDomain(backend, {reports: []});
const run = getRadarTodayRunState(domain, '2026-10-17T08:30:00Z');
process.stdout.write(JSON.stringify({run, reserved: domain.schedule.runsReservedToday, remaining: domain.schedule.remainingRunsToday, entries: domain.todayEntries, unchanged: before === JSON.stringify(backend), retryAvailable: domain.serviceHealth.retryAvailable}));
""".replace("FUNCTIONS", functions)
        result = self.run_node(script)
        self.assertEqual(result["run"]["state"], "corrective_failed")
        self.assertEqual(result["run"]["tone"], "error")
        self.assertEqual(result["run"]["error"], "radar_retry_quarantined")
        self.assertEqual(result["run"]["lastRunAt"], "2026-10-17T09:01:00+07:00")
        self.assertEqual(result["run"]["nextRunAt"], "2026-10-18T02:00:00Z")
        self.assertNotIn("ยังไม่เริ่ม", result["run"]["detail"])
        self.assertEqual((result["reserved"], result["remaining"]), (1, 0))
        self.assertEqual(result["entries"], [])
        self.assertTrue(result["unchanged"])
        self.assertFalse(result["retryAvailable"])

    def test_terminal_radar_quarantine_overrides_stale_repair_and_active_markers_in_visible_notice(self):
        functions = "\n".join(self.function(name) for name in [
            "safeDashboardDisplayText", "workflowDomainObject", "workflowDomainArray", "workflowReportRows", "indicatorScoutObjectRows",
            "indicatorScoutBangkokDateKey", "filterIndicatorScoutToday", "filterIndicatorScoutRollingSevenDays",
            "normalizeRadarSchedule", "normalizeRadarServiceHealth", "normalizeRadarRunStatus", "radarBangkokMinuteOfDay",
            "normalizeRadarPublicationPolicy", "radarPublicationCountLabel", "getRadarTodayRunState", "normalizeIndicatorScoutDomain", "createRadarTodayRunNotice",
        ])
        script = r"""
const INDICATOR_SCOUT_DEFAULT_TIME = '09:00', INDICATOR_SCOUT_TIMEZONE = 'Asia/Bangkok', INDICATOR_SCOUT_EXPECTED_BATCH_SIZE = 6;
class Element {
  constructor(tag) {this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.textContent = '';}
  append(...nodes) {this.children.push(...nodes);}
  appendChild(node) {this.children.push(node);}
  setAttribute(key, value) {this.attributes[key] = value;}
}
const document = {createElement: tag => new Element(tag)};
const formatThaiDateTime = value => value;
FUNCTIONS
const actualRunState = getRadarTodayRunState;
getRadarTodayRunState = domain => actualRunState(domain, '2026-10-17T08:30:00Z');
const schedule = {lastAttemptAt: '2026-10-17T09:01:00+07:00', lastRunAt: '2026-10-17T09:01:00+07:00',
  lastRunStatus: 'blocked', lastResultKind: 'radar_retry_quarantined', lastError: 'radar_retry_quarantined',
  status: 'paused', runsReservedToday: 1, remainingRunsToday: 0, pendingSlotKey: null, nextRunAt: '2026-10-18T02:00:00Z'};
const service = {status: 'degraded', lastRunStatus: 'blocked', lastResultKind: 'radar_retry_quarantined',
  lastError: 'radar_retry_quarantined', activeMissionId: null,
  automaticCorrectiveRetry: {supported: true, maximumAttemptsPerDailyReservation: null, maximumAttemptsPerBurst: 2,
    attempted: 1, remaining: 1, status: 'queued', failureReasonCode: 'radar_batch_attempt_incomplete',
    totalAttemptsQueued: 1, nextAttemptAt: null, overdueCarryForward: false,
    sameMission: true, sameDailyReservation: true, newDailyReservation: false}};
const flatten = node => [node.textContent, ...node.children.map(flatten)].join(' ');
const tags = node => [node.tagName, ...node.children.flatMap(tags)];
const rows = [{}, {activeMissionId: 'mission-stale'}, {pendingSlotKey: 'stale-slot'}, {status: 'running'}].map(variant => {
  const backend = {schedule: {...schedule, ...(variant.pendingSlotKey ? {pendingSlotKey: variant.pendingSlotKey} : {})},
    radarWebsiteTool: {todayEntries: [], sevenDayEntries: [], serviceHealth: {...service, ...variant}}};
  const before = JSON.stringify(backend);
  const domain = normalizeIndicatorScoutDomain(backend, {reports: []});
  const notice = createRadarTodayRunNotice(domain);
  return {state: notice.dataset.state, tone: notice.dataset.tone, role: notice.attributes.role,
    text: flatten(notice), tags: tags(notice), unchanged: before === JSON.stringify(backend),
    remaining: domain.schedule.remainingRunsToday, retryAvailable: domain.serviceHealth.retryAvailable};
});
const validRepair = getRadarTodayRunState({todayEntries: [], schedule: {...schedule, lastRunStatus: 'failed', lastResultKind: 'invalid_output', lastError: 'invalid_output'},
  serviceHealth: {...service, lastRunStatus: 'failed', lastResultKind: 'invalid_output', lastError: 'invalid_output'}});
process.stdout.write(JSON.stringify({rows, validRepair}));
""".replace("FUNCTIONS", functions)
        result = self.run_node(script)
        for row in result["rows"]:
            self.assertEqual((row["state"], row["tone"], row["role"]), ("corrective_failed", "error", "alert"))
            self.assertIn("รอบวันนี้ถูกหยุดไว้", row["text"])
            self.assertIn("radar_retry_quarantined", row["text"])
            self.assertIn("2026-10-17T09:01:00+07:00", row["text"])
            self.assertIn("2026-10-18T02:00:00Z", row["text"])
            self.assertNotIn("กำลังหาให้ครบ", row["text"])
            self.assertNotIn("ระหว่างทำงาน", row["text"])
            self.assertNotIn("button", row["tags"])
            self.assertTrue(row["unchanged"])
            self.assertEqual(row["remaining"], 0)
            self.assertFalse(row["retryAvailable"])
        self.assertEqual(result["validRepair"]["state"], "queued")


if __name__ == "__main__":
    unittest.main()
