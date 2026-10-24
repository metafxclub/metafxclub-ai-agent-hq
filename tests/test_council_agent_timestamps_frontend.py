import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def function_block(source, signature):
    start = source.index(signature)
    ends = [source.find(prefix, start + len(signature)) for prefix in ("\nfunction ", "\nasync function ")]
    return source[start:min(end for end in ends if end >= 0)]


class CouncilAgentTimestampsFrontendTests(unittest.TestCase):
    def run_js(self, body):
        main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")
        script = r"""
const assert=require('node:assert/strict');
const AI_TRADE_COUNCIL_PUBLIC_NAMES={optimization_agent:'Tech',backtest_analyst:'PA',codex_mcp_operator:'News'};
const safeDashboardDisplayText=(value,fallback='')=>value==null ? fallback : String(value);
const formatThaiDateTime=value=>value;
const signalCouncilRunModel=report=>report.run;
const signalCouncilModel=report=>report.council;
const signalCurrentConsensusSource=report=>report.selection;
const signalMissionUiState=mission=>mission?.status || 'idle';
const signalMissionBlockerModel=()=>({});
const signalMissionStatusLabel=mission=>mission?.status || 'idle';
const signalMissionReason=()=>'';
const signalVoteLabel=value=>value;
function report() {
 const mission={id:'news-mission',status:'completed',createdAt:'2026-10-21T10:40:53Z',completedAt:'2026-10-21T10:41:57Z'};
 return {run:{byAgent:new Map([['codex_mcp_operator',mission]]),state:'completed'},
 council:{chartSnapshot:{observedAt:'2026-10-21T10:40:39Z'}},
 selection:{current:true,source:{votes:[{agentId:'codex_mcp_operator',roleId:'news',decision:'SELL',confidence:74,
 snapshotId:'current-snapshot',readOnly:true,observations:['news'],
 evidence:[{observedAt:'2026-10-21T09:10:00Z'},{observedAt:'2026-10-21T10:40:43Z'}]}]}}};
}
"""
        script += function_block(main, "function signalAgentViews(")
        script += function_block(main, "function signalAgentTimestampLabel(")
        result = subprocess.run([node, "-"], input=script + body + "\nprocess.stdout.write(JSON.stringify({ok:true}));", text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True})
        self.assertEqual(main.count("footer.textContent = signalAgentTimestampLabel(view);"), 2)

    def test_current_news_separates_completed_round_time_from_first_evidence_time(self):
        self.run_js(r"""
const input=report(), before=JSON.stringify(input);
const view=signalAgentViews(input,{}).find(view=>view.id==='news');
assert.equal(view.analysisCompletedAt,'2026-10-21T10:41:57Z');
assert.equal(view.evidenceObservedAt,'2026-10-21T09:10:00Z');
assert.equal(signalAgentTimestampLabel(view),'วิเคราะห์เสร็จ 2026-10-21T10:41:57Z • เวลาหลักฐานข่าวแรก 2026-10-21T09:10:00Z');
assert.equal(view.direction,'SELL'); assert.equal(view.confidence,74); assert.equal(view.available,true);
assert.equal(JSON.stringify(input),before);
""")

    def test_missing_completion_and_unavailable_votes_do_not_invent_analysis_timestamp(self):
        self.run_js(r"""
const input=report(); delete input.run.byAgent.get('codex_mcp_operator').completedAt;
let view=signalAgentViews(input,{}).find(view=>view.id==='news');
assert.equal(view.analysisCompletedAt,null);
assert.match(signalAgentTimestampLabel(view),/^ยังไม่มีเวลาจบการวิเคราะห์.*เวลาหลักฐานข่าวแรก/);
assert.doesNotMatch(signalAgentTimestampLabel(view),/วิเคราะห์เสร็จ/);
for (const variant of ['mismatch','running','blocked']) {
 const current=report();
 if(variant==='mismatch')current.selection.current=false;
 else current.run.byAgent.get('codex_mcp_operator').status=variant;
 view=signalAgentViews(current,{}).find(view=>view.id==='news');
 assert.equal(view.available,false); assert.equal(view.analysisCompletedAt,null); assert.equal(view.evidenceObservedAt,null);
 assert.doesNotMatch(signalAgentTimestampLabel(view),/วิเคราะห์เสร็จ|เวลาหลักฐานข่าวแรก/);
 assert.equal(view.direction,null);
}
assert.match(signalAgentTimestampLabel({available:true,id:'technical',analysisCompletedAt:'done',evidenceObservedAt:'snapshot'}),/วิเคราะห์เสร็จ done.*เวลาข้อมูลที่ใช้ snapshot/);
""")


if __name__ == "__main__":
    unittest.main()
