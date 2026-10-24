"""Run the shipped confirmation handlers with synthetic receipts and read failures."""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeepResearchConfirmationFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        cls.node = shutil.which("node") or (str(bundled) if bundled.exists() else None)
        if not cls.node:
            raise RuntimeError("Node.js is required for confirmation behavior tests")
        source = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        names = (
            "tradingResearchBlueprintObject", "tradingResearchConfirmationReadModel",
            "resetTradingResearchConfirmationStatus", "tradingResearchConfirmationMessage",
            "tradingResearchConfirmationSheetKey", "tradingResearchConfirmationForSession",
            "tradingResearchConfirmationRequestIsCurrent",
            "blockTradingResearchFactoryRead", "refreshTradingResearchConfirmationReads",
            "completeTradingResearchConfirmationReads",
            "confirmTradingResearchForSheet", "refreshTradingResearchConfirmationStatus",
            "createTradingResearchConfirmationPanel",
        )
        functions = []
        for name in names:
            match = re.search(rf"^(?:async )?function {name}\([^\n]*\).*?^\}}", source, re.M | re.S)
            if not match:
                raise AssertionError(f"Shipped function missing: {name}")
            functions.append(match.group(0))
        cls.functions = "\n\n".join(functions)

    def run_node(self, body):
        prelude = r"""
const assert = require('node:assert/strict');
const TRADING_RESEARCH_LAB_PROP_ID = 'left_server_racks';
const EA_FACTORY_PROP_ID = 'right_server_racks';
const TRADING_RESEARCH_CONFIRMATION_ENDPOINT = '/api/props/left_server_racks/deep-research/confirm';
const TRADING_RESEARCH_SHEET_COLUMN_COUNT = 10;
const safeDashboardDisplayText = (value, fallback = '-') => value == null || value === '' ? fallback : String(value);
const formatThaiDateTime = value => value;
class Node {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.events = {}; this.textContent = ''; }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.append(child); return child; }
  addEventListener(name, callback) { this.events[name] = callback; }
  setAttribute() {}
}
const document = { createElement: tag => new Node(tag) };
const createTradingResearchNotice = (title, detail, tone) => {
  const node = new Node('notice'); node.textContent = title + ' ' + detail; node.dataset.tone = tone; return node;
};
const state = {
  modal: { open: true, id: TRADING_RESEARCH_LAB_PROP_ID, tradingResearchLab: {
    sourceReportId: 'source-report-1', selectedSystemId: 'system-1',
    confirmationInFlight: false, confirmationMessage: '', confirmationTone: 'neutral',
    confirmationReportKey: '', confirmationReceipt: null, confirmationRequest: null,
    confirmationRefreshMessage: '',
  } },
  eaFactoryReadModel: { payload: {schemaVersion: 'ea-factory-v1'}, stale: false, lastError: null },
  researchSheetHub: {data: {sheetId: 'synthetic-sheet-1', configRevision: 'rev-1', activeConfigRevision: 'rev-1',
    activationConfirmedAt: '2026-10-18T01:00:00Z', active: true}},
};
const session = state.modal.tradingResearchLab;
const calls = { posts: [], reads: [], merges: [], opens: [], renders: [] };
const rerenderTradingResearchLab = () => {};
const renderGameModal = () => { calls.renders.push({tone: session.confirmationTone,
  inFlight: session.confirmationInFlight, message: session.confirmationMessage}); };
const settleRefresh = () => new Promise(resolve => setImmediate(resolve));
const openPropDialog = id => { calls.opens.push(id); };
const mergeEaFactoryReadModel = payload => {
  calls.merges.push(payload); state.eaFactoryReadModel.stale = false; state.eaFactoryReadModel.lastError = null; return true;
};
const digest = 'a'.repeat(64);
const report = {
  id: 'research-report-1', eaResearch: { briefDigest: digest, confirmation: {
    reportId: 'research-report-1', briefDigest: digest, endpoint: TRADING_RESEARCH_CONFIRMATION_ENDPOINT,
    required: true, confirmed: false, canConfirm: true, saveToGoogleSheet: true,
    columnCompleteness: { requiredColumnCount: 10, populatedColumnCount: 10, missingColumns: [],
      columnStatuses: Array.from({length: 10}, (_, index) => ({name: 'column_' + index, present: true})) },
  } },
};
const receipt = () => ({ ...structuredClone(report.eaResearch.confirmation), confirmed: true,
  canConfirm: false, handoffReady: true, sheetDelivery: {status: 'synced', synced: true},
});
let postResult = {ok: true, confirmation: receipt(), eaFactoryReadResult: {ok: true}, eaFactory: {schemaVersion: 'ea-factory-v1'}};
let postImpl = async () => postResult;
const postJson = async (path, payload) => { calls.posts.push({path, payload}); return postImpl(); };
let readImpl = async name => ({ok: true, name});
let loadPropReport = async () => { calls.reads.push('report'); return readImpl('report'); };
const loadResearchSheetHub = async () => { calls.reads.push('sheet'); return readImpl('sheet'); };
const loadEaFactoryReadModel = async () => { calls.reads.push('factory'); return readImpl('factory'); };
const panel = () => createTradingResearchConfirmationPanel(report, {canonical: true});
const nodes = root => [root, ...root.children.flatMap(nodes)];
const copy = root => nodes(root).map(node => node.textContent).join(' ');
const buttons = root => nodes(root).filter(node => node.tag === 'button');
const saveButtons = root => buttons(root).filter(node => /บันทึก.*Google Sheet/.test(node.textContent));
const submitButtons = root => buttons(root).filter(node => node.className.includes('workflow-research-confirmation-submit'));
"""
        script = prelude + "\n" + self.functions + "\n(async () => {\n" + body + "\nconsole.log(JSON.stringify({passed: true}));\n})().catch(error => {console.error(error); process.exitCode = 1;});"
        result = subprocess.run(
            [self.node, "-e", script], cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"passed": True})

    def test_synced_receipt_survives_factory_integrity_block_and_only_opens_inspection(self):
        self.run_node("""
postResult.eaFactoryReadResult = {ok: false, kind: 'ea_factory_integrity_blocked',
  status: 'blocked', messageTh: 'หลักฐาน Build ไม่ผ่านการตรวจสอบ',
  oneClick: {commandsAllowed: false}, liveTradingAllowed: false};
delete postResult.eaFactory;
readImpl = async name => name === 'factory' ? null : {ok: true};
await confirmTradingResearchForSheet(report);
assert.equal(calls.posts.length, 1);
assert.deepEqual(calls.posts[0], {path: TRADING_RESEARCH_CONFIRMATION_ENDPOINT, payload: {
  researchReportId: report.id, confirmBriefDigest: digest, confirmSaveToGoogleSheet: true,
}});
assert.equal(session.confirmationTone, 'success');
assert.equal(session.confirmationReceipt.reportId, report.id);
assert.equal(session.confirmationReceipt.briefDigest, digest);
assert.equal(state.eaFactoryReadModel.stale, true);
assert.equal(state.eaFactoryReadModel.lastError.kind, 'ea_factory_integrity_blocked');
assert.equal(calls.merges.length, 0);
const view = panel();
assert.match(copy(view), /บันทึก Google Sheet แล้ว/);
assert.match(copy(view), /ซิงก์สำเร็จ/);
assert.match(copy(view), /หลักฐาน Build ไม่ผ่านการตรวจสอบ/);
assert.doesNotMatch(copy(view), /ส่งโรงงาน EA ได้|โรงงาน EA โหลดระบบนี้ได้/);
assert.equal(saveButtons(view).length, 0);
buttons(view).find(button => button.textContent === 'เปิดโรงงาน EA เพื่อดูสาเหตุ').events.click();
assert.deepEqual(calls.opens, [EA_FACTORY_PROP_ID]);
assert.equal(calls.posts.length, 1);
assert.equal(report.eaResearch.confirmation.confirmed, false); // receipt does not mutate canonical reports
""")

    def test_rejected_optional_reads_do_not_turn_committed_save_into_failure_or_repeat_post(self):
        self.run_node("""
readImpl = async name => { throw new Error('read failed: ' + name); };
await confirmTradingResearchForSheet(report);
await settleRefresh();
assert.deepEqual(calls.reads.sort(), ['factory', 'report', 'sheet']);
assert.equal(session.confirmationTone, 'success');
assert.match(session.confirmationMessage, /บันทึก Strategy Brief ลง Google Sheet แล้ว/);
assert.match(session.confirmationRefreshMessage, /รีเฟรช.*ไม่สำเร็จ/);
assert.equal(session.confirmationInFlight, false);
assert.equal(session.confirmationReceipt.sheetDelivery.synced, true);
await confirmTradingResearchForSheet(report);
await confirmTradingResearchForSheet(report, {retryDelivery: true});
assert.equal(calls.posts.length, 1);
assert.equal(saveButtons(panel()).length, 0);
assert.equal(state.eaFactoryReadModel.stale, true);
""")

    def test_null_read_failures_and_catalog_projection_failure_remain_separate(self):
        self.run_node("""
postResult.researchCatalogReadResult = {ok: false, kind: 'research_catalog_integrity_blocked', messageTh: 'คลังวิจัยตรวจไม่ผ่าน'};
readImpl = async () => null;
await confirmTradingResearchForSheet(report);
await settleRefresh();
assert.equal(session.confirmationTone, 'success');
assert.match(session.confirmationRefreshMessage, /คลังวิจัยตรวจไม่ผ่าน/);
assert.ok(session.confirmationRefreshMessage.includes('รายงานวิจัย / สถานะ Google Sheet / โรงงาน EA'));
assert.equal(saveButtons(panel()).length, 0);
""")

    def test_critical_post_failure_never_creates_receipt_or_runs_optional_reads(self):
        self.run_node("""
postImpl = async () => { throw new Error('Digest ไม่ตรงกับรายงานล่าสุด'); };
await confirmTradingResearchForSheet(report);
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationTone, 'error');
assert.match(session.confirmationMessage, /Digest ไม่ตรง/);
assert.equal(session.confirmationInFlight, false);
assert.equal(calls.reads.length, 0);
assert.equal(saveButtons(panel()).length, 1);
assert.equal(saveButtons(panel())[0].disabled, false);
""")

    def test_mismatched_or_unconfirmed_receipts_are_rejected_before_storage(self):
        for change in ("reportId: 'other-report'", "briefDigest: 'b'.repeat(64)", "confirmed: false"):
            with self.subTest(change=change):
                self.run_node("""
postResult.confirmation = {...receipt(), CHANGE};
await confirmTradingResearchForSheet(report);
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationTone, 'error');
assert.match(session.confirmationMessage, /ใบยืนยันไม่ตรง/);
assert.equal(calls.reads.length, 0);
assert.equal(calls.merges.length, 0);
""".replace("CHANGE", change))

    def test_selection_changed_while_post_pending_discards_old_response(self):
        self.run_node("""
let completePost;
postImpl = () => new Promise(resolve => { completePost = resolve; });
const pending = confirmTradingResearchForSheet(report);
session.sourceReportId = 'source-report-2';
session.selectedSystemId = 'system-2';
resetTradingResearchConfirmationStatus(session);
completePost(postResult);
await pending;
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationMessage, '');
assert.equal(session.confirmationInFlight, false);
assert.equal(calls.reads.length, 0);
assert.equal(calls.merges.length, 0);
""")

    def test_changed_report_or_digest_resets_receipt_and_never_confirms_another_revision(self):
        for change in ("next.id = 'research-report-2'; next.eaResearch.confirmation.reportId = next.id;",
                       "next.eaResearch.briefDigest = 'b'.repeat(64); next.eaResearch.confirmation.briefDigest = 'b'.repeat(64);",
                       "next.eaResearch.briefDigest = 'b'.repeat(64); // mismatched backend confirmation is also a new context"):
            with self.subTest(change=change):
                self.run_node("""
await confirmTradingResearchForSheet(report);
const next = structuredClone(report);
CHANGE
const view = createTradingResearchConfirmationPanel(next, {canonical: true});
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationMessage, '');
assert.equal(session.confirmationRefreshMessage, '');
assert.equal(submitButtons(view).length, 1);
assert.doesNotMatch(copy(view), /บันทึก Google Sheet แล้ว/);
""".replace("CHANGE", change))

    def test_manual_refresh_failure_keeps_success_receipt_and_hides_save_button(self):
        self.run_node("""
await confirmTradingResearchForSheet(report);
readImpl = async () => { throw new Error('offline'); };
await refreshTradingResearchConfirmationStatus();
assert.equal(session.confirmationReceipt.sheetDelivery.synced, true);
assert.equal(session.confirmationTone, 'success');
assert.match(session.confirmationMessage, /บันทึก Strategy Brief ลง Google Sheet แล้ว/);
assert.match(session.confirmationRefreshMessage, /ไม่ต้องบันทึกซ้ำ/);
assert.equal(saveButtons(panel()).length, 0);
assert.equal(calls.posts.length, 1);
""")

    def test_unsynced_receipt_keeps_explicit_retry_and_backend_guards(self):
        self.run_node("""
postResult.confirmation = {...receipt(), handoffReady: false, sheetDelivery: {status: 'failed', failed: true}};
await confirmTradingResearchForSheet(report);
assert.equal(session.confirmationTone, 'error');
assert.match(session.confirmationMessage, /บันทึก Google Sheet ไม่สำเร็จ/);
const retry = saveButtons(panel());
assert.equal(retry.length, 1);
assert.equal(retry[0].textContent, 'ลองบันทึก Google Sheet อีกครั้ง');
assert.equal(retry[0].disabled, false);
postResult.confirmation = receipt();
await confirmTradingResearchForSheet(report, {retryDelivery: true});
assert.equal(calls.posts.length, 2);
assert.equal(saveButtons(panel()).length, 0);
""")

    def test_inflight_double_click_sends_one_request_and_success_does_not_claim_factory_availability(self):
        self.run_node("""
let completePost;
postImpl = () => new Promise(resolve => { completePost = resolve; });
const pending = confirmTradingResearchForSheet(report);
await confirmTradingResearchForSheet(report);
assert.equal(calls.posts.length, 1);
assert.equal(submitButtons(panel())[0].disabled, true);
completePost(postResult);
await pending;
assert.equal(calls.merges.length, 1);
assert.equal(session.confirmationTone, 'success');
assert.equal(saveButtons(panel()).length, 0);
assert.doesNotMatch(session.confirmationMessage, /โรงงาน EA โหลดระบบนี้ได้|โรงงาน EA พร้อม/);
assert.doesNotMatch(copy(panel()), /ส่งโรงงาน EA ได้/);
""")

    def test_fresh_authoritative_negative_wins_over_same_id_and_digest_receipt(self):
        self.run_node("""
await confirmTradingResearchForSheet(report);
assert.equal(saveButtons(panel()).length, 0);
const freshReport = structuredClone(report);
const view = createTradingResearchConfirmationPanel(freshReport, {canonical: true});
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationMessage, '');
assert.equal(submitButtons(view).length, 1);
assert.equal(submitButtons(view)[0].disabled, false);
assert.doesNotMatch(copy(view), /บันทึก Google Sheet แล้ว/);
""")

    def test_changed_hub_binding_invalidates_receipt_even_with_original_report(self):
        for field, value in (("sheetId", "synthetic-sheet-2"), ("configRevision", "rev-2"),
                             ("activeConfigRevision", "rev-2"), ("activationConfirmedAt", "2026-10-18T02:00:00Z")):
            with self.subTest(field=field):
                self.run_node("""
await confirmTradingResearchForSheet(report);
state.researchSheetHub.data[FIELD] = VALUE;
const view = panel();
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationMessage, '');
assert.equal(submitButtons(view).length, 1);
assert.doesNotMatch(copy(view), /บันทึก Google Sheet แล้ว/);
""".replace("FIELD", json.dumps(field)).replace("VALUE", json.dumps(value)))

    def test_hub_changed_during_pending_post_discards_old_sheet_receipt(self):
        self.run_node("""
let completePost;
postImpl = () => new Promise(resolve => { completePost = resolve; });
const pending = confirmTradingResearchForSheet(report);
state.researchSheetHub.data.activeConfigRevision = 'rev-2';
completePost(postResult);
await pending;
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationMessage, '');
assert.equal(session.confirmationInFlight, false);
assert.equal(calls.reads.length, 0);
""")

    def test_validated_post_returns_and_renders_before_slow_optional_reads(self):
        self.run_node("""
postResult.eaFactoryReadResult = {status: 'deferred', kind: 'ea_factory_refresh_deferred', readinessConfirmed: false};
postResult.researchCatalogReadResult = {status: 'deferred', kind: 'research_catalog_refresh_deferred'};
delete postResult.eaFactory;
const completions = [];
readImpl = name => new Promise(resolve => { completions.push(() => resolve({ok: true, name})); });
await confirmTradingResearchForSheet(report);
assert.equal(completions.length, 3);
assert.equal(session.confirmationInFlight, false);
assert.equal(session.confirmationTone, 'success');
assert.equal(session.confirmationReceipt.sheetDelivery.synced, true);
assert.equal(state.eaFactoryReadModel.stale, true);
assert.equal(state.eaFactoryReadModel.lastError, null); // Deferred is not an integrity failure.
assert.equal(calls.merges.length, 0);
assert.equal(calls.renders.at(-1).inFlight, false);
assert.match(calls.renders.at(-1).message, /บันทึก Strategy Brief ลง Google Sheet แล้ว/);
assert.match(session.confirmationRefreshMessage, /กำลังตรวจ/);
assert.equal(saveButtons(panel()).length, 0);
await confirmTradingResearchForSheet(report, {retryDelivery: true});
assert.equal(calls.posts.length, 1);
completions.forEach(complete => complete());
await settleRefresh();
assert.equal(session.confirmationRequest, null);
assert.equal(session.confirmationRefreshMessage, '');
""")

    def test_old_background_completion_does_not_clear_a_new_manual_refresh(self):
        self.run_node("""
const completions = [];
readImpl = name => new Promise(resolve => { completions.push(() => resolve({ok: true, name})); });
await confirmTradingResearchForSheet(report);
const oldRequest = session.confirmationRequest;
const manual = refreshTradingResearchConfirmationStatus();
await settleRefresh();
const newRequest = session.confirmationRequest;
assert.notEqual(oldRequest, newRequest);
assert.equal(session.confirmationInFlight, true);
completions.slice(0, 3).forEach(complete => complete());
await settleRefresh();
assert.equal(session.confirmationRequest, newRequest);
assert.equal(session.confirmationInFlight, true);
assert.match(session.confirmationRefreshMessage, /กำลังตรวจสถานะ/);
completions.slice(3).forEach(complete => complete());
await manual;
assert.equal(session.confirmationInFlight, false);
assert.equal(session.confirmationRequest, null);
""")

    def test_context_change_during_background_reads_does_not_restore_old_receipt(self):
        self.run_node("""
const completions = [];
readImpl = name => new Promise(resolve => { completions.push(() => resolve({ok: true, name})); });
await confirmTradingResearchForSheet(report);
session.sourceReportId = 'source-report-2';
session.selectedSystemId = 'system-2';
resetTradingResearchConfirmationStatus(session);
completions.forEach(complete => complete());
await settleRefresh();
assert.equal(session.confirmationReceipt, null);
assert.equal(session.confirmationMessage, '');
assert.equal(session.confirmationRequest, null);
""")

    def test_old_report_refresh_cannot_discard_a_new_successful_retry(self):
        source = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        loader = re.search(r"^async function loadPropReport\([^\n]*\).*?^\}", source, re.M | re.S).group(0)
        loader = loader.replace("async function loadPropReport(", "async function guardedLoadPropReport(", 1)
        self.run_node(loader + """
const propReportInFlight = new Map();
const PROP_REPORT_FETCH_TIMEOUT_MS = 1000;
const SENTIMENT_UNIVERSE_ENABLED = true, FX_NEWS_BIAS_PROP_ID = 'left_signal_cube';
const renderOperationalSidebars = () => {};
const selectObject = () => {};
state.propReports = {[TRADING_RESEARCH_LAB_PROP_ID]: report};
state.propReportLoadedAt = {};
state.propReportLoadState = {};
let completeOldReport;
let reportFetches = 0;
const fetchJson = async () => {
  reportFetches++;
  if (reportFetches === 1) return new Promise(resolve => { completeOldReport = resolve; });
  return state.propReports[TRADING_RESEARCH_LAB_PROP_ID];
};
loadPropReport = guardedLoadPropReport;
postResult.confirmation = {...receipt(), handoffReady: false, sheetDelivery: {status: 'failed', failed: true}};
await confirmTradingResearchForSheet(report);
let completeRetry;
postImpl = () => new Promise(resolve => { completeRetry = resolve; });
const retry = confirmTradingResearchForSheet(report, {retryDelivery: true});
const retryRequest = session.confirmationRequest;
const oldReport = structuredClone(report);
oldReport.eaResearch.confirmation = structuredClone(postResult.confirmation);
completeOldReport(oldReport);
await settleRefresh();
assert.equal(state.propReports[TRADING_RESEARCH_LAB_PROP_ID], report);
createTradingResearchConfirmationPanel(state.propReports[TRADING_RESEARCH_LAB_PROP_ID], {canonical: true});
assert.equal(session.confirmationRequest, retryRequest);
assert.equal(session.confirmationInFlight, true);
completeRetry({...postResult, confirmation: receipt()});
await retry;
assert.equal(session.confirmationReceipt.sheetDelivery.synced, true);
assert.match(copy(panel()), /บันทึก Google Sheet แล้ว/);
assert.equal(saveButtons(panel()).length, 0);
await settleRefresh();
assert.equal(calls.posts.length, 2);
""")


if __name__ == "__main__":
    unittest.main()
