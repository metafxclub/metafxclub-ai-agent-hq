import json
import shutil
import subprocess
import unittest
from pathlib import Path

from test_frontend_polling_stability import function_block


ROOT = Path(__file__).resolve().parents[1]


class CouncilCompletedRoundFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        cls.node = shutil.which("node") or str(
            Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )

    def run_js(self, body):
        script = r"""
const assert = require('node:assert/strict');
const AI_TRADE_COUNCIL_AGENT_IDS = ['optimization_agent', 'backtest_analyst', 'codex_mcp_operator'];
const AI_TRADE_COUNCIL_PUBLIC_NAMES = Object.fromEntries(AI_TRADE_COUNCIL_AGENT_IDS.map(id => [id, id]));
const safeDashboardDisplayText = (value, fallback = '') => value == null ? fallback : String(value);
const signalHistoryObject = value => value && typeof value === 'object' ? value : {};
const signalCouncilModel = (report = {}) => report.aiTradeCouncil || {};
const signalCouncilAutomationModel = report => report.aiTradeCouncil.autoAnalysis.state;
const signalMissionStatusLabel = mission => mission?.status || 'idle';
const signalMissionBlockerModel = () => null;
const signalCouncilConsensusPolicyModel = () => ({requiredVotes: 3});
const signalMarketModel = report => report.aiTradeCouncil.chartSnapshot;
const firstFiniteSignalNumber = (...values) => {
  const value = values.find(value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value)));
  return value === undefined ? null : Number(value);
};
function fixture() {
  const parent = (id, createdAt, status = 'completed') => ({id, createdAt, status,
    reportType: 'ai_trade_council_report', delegation: {mode: 'ai_trade_council_read_only', snapshotId: id + '-snapshot'},
    subtaskIds: AI_TRADE_COUNCIL_AGENT_IDS.map(owner => id + '-' + owner)});
  const automatic = parent('automatic', '2026-10-21T07:00:00Z');
  const manual = parent('manual', '2026-10-21T07:09:00Z');
  const children = parent => AI_TRADE_COUNCIL_AGENT_IDS.map(owner => ({id: parent.id + '-' + owner,
    owner, status: 'completed', parentMissionId: parent.id, createdAt: parent.createdAt, result: '{"raw":"old JSON"}'}));
  const identity = {candidateId: 'selected-mt5', streamKey: 'selected-mt5|XAUUSD|H1', symbol: 'XAUUSD', timeframe: 'H1'};
  const consensus = {...identity, sourceMissionId: manual.id, snapshotId: manual.delegation.snapshotId,
    ready: true, available: true, identityValid: true, voteCount: 3, decision: 'HOLD',
    votes: AI_TRADE_COUNCIL_AGENT_IDS.map(agentId => ({agentId, snapshotId: manual.delegation.snapshotId,
      decision: 'HOLD', available: true, confidence: 70, observations: ['role result ' + agentId]}))};
  const report = {aiTradeCouncil: {
    chartSnapshot: {...identity, snapshotId: manual.delegation.snapshotId},
    autoAnalysis: {state: {lastMissionId: automatic.id, newBarPending: false}},
    decisionPipeline: {items: [manual, ...children(manual), automatic, ...children(automatic)], consensus},
  }};
  return {report, automatic, manual, consensus};
}
"""
        for name in (
            "signalStreamToken", "signalStreamContextFromSource", "signalAnalysisSourceStreamContext",
            "signalStreamContextsMatch", "signalStreamContextIdentityComplete", "signalActiveStreamContext",
            "signalMissionStatusValue", "signalMissionUiState", "signalMissionCreatedTime", "signalMissionReason",
            "signalCurrentSnapshotId", "signalCouncilRunModel", "signalCurrentConsensusSource",
            "signalVoteLabel", "signalAgentViews", "normalizeSignalRequiredVotes", "signalConsensusModel",
        ):
            script += "\n" + function_block(self.main, name)
        script += "\n" + body + "\nprocess.stdout.write(JSON.stringify({ok:true}));"
        result = subprocess.run([self.node, "-"], input=script, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True})

    def test_newer_completed_manual_round_shows_its_three_votes_and_keeps_snapshot_guard(self):
        self.run_js(r"""
const {report, manual} = fixture();
const originalItems = report.aiTradeCouncil.decisionPipeline.items.slice();
const run = signalCouncilRunModel(report);
assert.equal(run.parent.id, 'manual');
assert.equal(run.snapshotId, manual.delegation.snapshotId);
assert.equal(run.counts.completed, 3);
const views = signalAgentViews(report, {});
assert.equal(views.length, 3);
assert.ok(views.every(view => view.available && view.direction === 'HOLD' && view.missionId.startsWith('manual-')));
assert.ok(views.every(view => view.reasons[0].startsWith('role result ')));
assert.equal(signalConsensusModel(report, {}).available, true);
report.aiTradeCouncil.chartSnapshot.snapshotId = 'new-live-snapshot';
assert.ok(signalAgentViews(report, {}).every(view => view.available));
const historical = signalConsensusModel(report, {});
assert.equal(historical.available, false);
assert.equal(historical.matchesCurrentSnapshot, false);
assert.equal(historical.snapshotId, 'manual-snapshot');
assert.equal(historical.currentSnapshotId, 'new-live-snapshot');
assert.equal(historical.voteCount, 3);
assert.deepEqual(report.aiTradeCouncil.decisionPipeline.items, originalItems);
""")

    def test_only_strictly_newer_completed_matching_consensus_supersedes_completed_automatic(self):
        self.run_js(r"""
for (const change of [
  ({manual}) => {manual.createdAt = '2026-10-21T06:59:00Z';},
  ({manual, automatic}) => {manual.createdAt = automatic.createdAt;},
  ({manual}) => {manual.createdAt = 'invalid';},
  ({automatic}) => {automatic.createdAt = 'invalid';},
  ({manual}) => {manual.status = 'failed';},
  ({automatic}) => {automatic.status = 'failed';},
  ({automatic}) => {automatic.status = 'failed'; automatic.createdAt = '2026-10-21T07:11:00Z';},
  ({consensus}) => {consensus.snapshotId = 'wrong-round';},
]) {
  const value = fixture(); change(value);
  value.report.aiTradeCouncil.chartSnapshot.snapshotId = value.automatic.delegation.snapshotId;
  assert.equal(signalCouncilRunModel(value.report).parent.id, 'automatic');
}
""")

    def test_active_current_and_new_bar_waiting_precedence_is_unchanged(self):
        self.run_js(r"""
{
  const {report, automatic} = fixture(); automatic.status = 'running';
  const run = signalCouncilRunModel(report);
  assert.equal(run.parent.id, 'automatic'); assert.equal(run.hasActiveRound, true);
}
{
  const {report, automatic} = fixture();
  report.aiTradeCouncil.decisionPipeline.currentRun = {parent: automatic, parentMissionId: automatic.id, current: true};
  assert.equal(signalCouncilRunModel(report).parent.id, 'automatic');
}
{
  const {report} = fixture(); report.aiTradeCouncil.autoAnalysis.state.newBarPending = true;
  const run = signalCouncilRunModel(report);
  assert.equal(run.parent, null); assert.equal(run.state, 'waiting_current_round');
  assert.equal(run.children.length, 0);
}
""")

    def test_newer_completed_result_cannot_mix_a_different_stream_or_candidate(self):
        self.run_js(r"""
for (const change of [
  consensus => {consensus.candidateId = 'other-terminal';},
  consensus => {consensus.streamKey = 'different-stream';},
  consensus => {consensus.symbol = 'EURUSD';},
  consensus => {consensus.timeframe = 'M5';},
  consensus => {consensus.identityValid = false;},
]) {
  const {report, consensus} = fixture(); change(consensus);
  assert.equal(signalCurrentConsensusSource(report).current, false);
  const views=signalAgentViews(report, {});
  assert.ok(views.every(view => !view.available));
  assert.ok(views.every(view => view.reasons.every(reason => !reason.includes('"raw"') && !reason.includes('old JSON'))));
  assert.ok(views.every(view => view.reasons[0].includes('ยังไม่มีผลที่ยืนยันสำหรับรอบปัจจุบัน')));
  assert.equal(signalConsensusModel(report, {}).available, false);
}
""")

    def test_json_fallback_is_readable_and_plain_failure_or_truncation_remains_visible(self):
        self.run_js(r"""
for(const result of ['{"decision":"SELL"}', '[{"decision":"SELL"}]', '```json\n{"decision":"SELL"}\n```', {decision:'SELL'}]) {
 const text=signalMissionReason({status:'completed',result});
 assert.match(text,/ยังไม่มีผลที่ยืนยันสำหรับรอบปัจจุบัน/);
 assert.doesNotMatch(text,/SELL|\{|\[object/);
}
assert.equal(signalMissionReason({status:'completed',result:'บทวิเคราะห์ที่อ่านได้'}),'บทวิเคราะห์ที่อ่านได้');
assert.match(signalMissionReason({status:'completed',result:'[TRUNCATED]'}),/รายละเอียดถูกตัด/);
""")


if __name__ == "__main__":
    unittest.main()
