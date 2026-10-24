"""Read-only projections must distinguish votes, pending transport and broker outcomes."""
import copy
import importlib.util
import json
import shutil
import subprocess
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def function_block(source, signature):
    start = source.index(signature)
    ends = [source.find(prefix, start + len(signature)) for prefix in ("\nfunction ", "\nasync function ")]
    return source[start:min(end for end in ends if end >= 0)]


class ExecutionHistoryBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("execution_history_truth_bridge", ROOT / "backend/local-runner/bridge_server.py")
        cls.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bridge)

    def command(self, suffix="a", channel="mtc-history"):
        return {
            "command": {"commandId": "cmd-" + suffix * 24, "channelId": channel,
                        "missionId": "mission-history", "snapshotId": "f" * 64,
                        "symbol": "XAUUSD", "timeframe": "H1", "action": "SELL"},
            "status": "expired_waiting_ack", "outstanding": True, "ack": None,
            "createdAt": "2026-10-22T00:00:00Z", "updatedAt": "2026-10-22T01:00:00Z",
        }

    def history(self, records, outcome=None):
        gateway = mock.Mock()
        gateway.list_commands_page = None
        gateway.list_commands.return_value = records
        gateway.read_outcome.return_value = outcome
        before = copy.deepcopy(records)
        result = self.bridge._mt4_trade_gateway_order_history(gateway, selected_candidate_id="mtc-history")
        self.assertEqual(records, before)
        gateway.ingest_ack.assert_not_called()
        gateway.queue_trade_intent.assert_not_called()
        return result

    def executed(self, ticket=18446744073709551615):
        record = self.command()
        record.update(status="ack_EXECUTED", outstanding=False)
        record["ack"] = {
            "status": "EXECUTED", "ticket": ticket, "filledPrice": 4090,
            "actualMagicNumber": 4186001, "actualComment": "HQ:" + record["command"]["commandId"],
            "actualStopLoss": 4100, "actualTakeProfit": 4070,
            "verificationStatus": "VERIFIED_OPEN", "observedAt": int(time.time()),
            "statePersisted": True, "mode": "live", "fixedLot": 0.01,
        }
        return record

    def test_pending_command_is_visible_separately_and_not_counted_as_order(self):
        history = self.history([self.command(), self.command("b", "mtc-other")])
        self.assertEqual(history["items"], [])
        self.assertEqual(history["totalExecuted"], 0)
        self.assertEqual(history["totalVisible"], 0)
        self.assertEqual(len(history["pendingCommands"]), 1)
        pending = history["pendingCommands"][0]
        self.assertEqual(pending["reasonCode"], "expired_waiting_ack")
        self.assertFalse(pending["orderExecutionConfirmed"])
        self.assertEqual(pending["streamKey"], self.bridge._ai_trade_council_stream_key("mtc-history", "XAUUSD", "H1"))
        transformed = self.bridge._ai_trade_order_history_read_model(history, [])
        self.assertEqual(transformed["pendingCommands"], history["pendingCommands"])
        self.assertEqual(transformed["summary"]["total"], 0)

    def test_ticket_decimal_text_is_lossless_and_closed_outcome_requires_identity(self):
        record = self.executed()
        outcome = {
            "ticket": record["ack"]["ticket"], "magicNumber": 4186001,
            "comment": record["ack"]["actualComment"], "executionState": "CLOSED",
            "observedAt": 1792623740, "closedPnl": 1.25, "lots": 0.01,
            "openPrice": 4090, "stopLoss": 4100, "takeProfit": 4070,
        }
        history = self.history([record], outcome)
        item = history["items"][0]
        self.assertEqual(item["ticketText"], "18446744073709551615")
        self.assertEqual(item["executionState"], "CLOSED")
        self.assertTrue(item["outcomeIdentityVerified"])
        self.assertEqual(history["pendingCommands"], [])
        outcome["ticket"] -= 1
        mismatch = self.history([record], outcome)["items"][0]
        self.assertEqual(mismatch["executionState"], "CONFIRMED_UNKNOWN")
        self.assertFalse(mismatch["outcomeIdentityVerified"])

    def test_open_outcome_requires_freshness_and_never_inferred_from_ack(self):
        record = self.executed(500029817749)
        self.assertEqual(self.history([record])["items"][0]["executionState"], "CONFIRMED_UNKNOWN")
        outcome = {"ticket": 500029817749, "magicNumber": 4186001,
                   "comment": record["ack"]["actualComment"], "executionState": "OPEN",
                   "observedAt": int(time.time())}
        self.assertEqual(self.history([record], outcome)["items"][0]["executionState"], "OPEN")
        outcome["observedAt"] -= 120
        self.assertEqual(self.history([record], outcome)["items"][0]["executionState"], "CONFIRMED_UNKNOWN")

    def test_close_cost_fields_require_exact_executed_closed_outcome_and_preserve_unknowns(self):
        record = self.executed(500029817749)
        outcome = {"ticket": 500029817749, "magicNumber": 4186001,
                   "comment": record["ack"]["actualComment"], "executionState": "CLOSED",
                   "observedAt": 1792623740, "closedPnl": 1.1,
                   "closePrice": 4080.5, "grossProfit": 2, "commission": -0.7, "swap": -0.2, "fee": 0}
        item = self.history([record], outcome)["items"][0]
        self.assertEqual([item[key] for key in ("closePrice", "grossProfit", "commission", "swap", "fee")],
                         [4080.5, 2, -0.7, -0.2, 0])
        del outcome["commission"]
        self.assertIsNone(self.history([record], outcome)["items"][0]["commission"])
        outcome["ticket"] += 1
        item = self.history([record], outcome)["items"][0]
        self.assertTrue(all(item[key] is None for key in ("closePrice", "grossProfit", "commission", "swap", "fee")))

    def parent(self, dispatch):
        return {"id": "mission-history", "status": "completed", "createdAt": "2026-10-22T08:00:00Z",
                "analysisContext": {"kind": "ai_trade_council_parent", "snapshotId": "f" * 64,
                    "closedBarIdentity": {"candidateId": "mtc-history", "streamKey": "a" * 64,
                                          "closedBarTime": 1792663200, "symbol": "XAUUSD", "timeframe": "H1"}},
                "councilDecision": {"decision": "SELL", "selectedDirection": "SELL", "consensusReached": True,
                                    "requiredVotes": 2, "directionCounts": {"SELL": 2, "HOLD": 1}},
                "tradeGateway": dispatch}

    def analysis(self, parent, history=None):
        with mock.patch.object(self.bridge, "load_ai_trade_council_automation_store", return_value={"state": {"coverageRecords": []}}):
            return self.bridge._ai_trade_council_analysis_history_read_model(
                [parent], history or {"items": []}, scope={"mode": "all"})["items"][0]

    def test_canonical_round_retains_dispatch_reason_and_preflight_without_command_payload(self):
        dispatch = {"status": "blocked", "reasonCode": "signal_price_drift_exceeded_before_publish",
                    "commandPublished": False, "commandId": None, "command": {"private": "excluded"},
                    "executionPricePreflight": {"status": "blocked", "priceDriftPoints": 444,
                                                "maximumSignalDriftPoints": 100, "private": "excluded"}}
        row = self.analysis(self.parent(dispatch))
        self.assertEqual(row["consensus"]["decision"], "SELL")
        self.assertEqual(row["tradeGateway"]["reasonCode"], dispatch["reasonCode"])
        self.assertEqual(row["tradeGateway"]["executionPricePreflight"]["priceDriftPoints"], 444)
        self.assertFalse(row["tradeGateway"]["commandPublished"])
        self.assertNotIn("private", json.dumps(row))
        self.assertFalse(row["orderLinkage"]["available"])

    def test_pending_overlay_is_exact_command_and_mission_only(self):
        record = self.command()
        history = self.history([record])
        parent = self.parent({"status": "queued", "commandPublished": True, "commandId": record["command"]["commandId"]})
        self.assertEqual(self.analysis(parent, history)["tradeGateway"]["status"], "expired_waiting_ack")
        parent["tradeGateway"]["commandId"] = "cmd-" + "b" * 24
        self.assertEqual(self.analysis(parent, history)["tradeGateway"]["status"], "queued")


class ExecutionHistoryFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        cls.node = shutil.which("node")

    def run_js(self, body):
        script = "const assert=require('node:assert/strict');\nconst safeDashboardDisplayText=(v,f='')=>v==null?f:String(v);\nfunction signalCouncilModel(report){return report.aiTradeCouncil||{};}\n"
        for signature in ("signalTicketText", "signalHistoryObject", "signalHistoryMetricObject", "signalHistoryDecision",
                          "signalHistoryFinalDecision", "signalPrepublishExecutionBlockReason", "signalExecutionGuardReasonLabel",
                          "signalOrderNumber", "signalOrderSignedPnl", "signalOrderClosedFinancialText", "signalBrokerDateTime", "signalHistorySkipReasonLabel",
                          "signalSnapshotAgeDetail", "signalHistoryOrderState", "signalPendingCommandModels"):
            script += function_block(self.main, "function " + signature + "(")
        result = subprocess.run([self.node, "-"], input=script + body, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_large_ticket_linkage_uses_exact_text_not_rounded_number(self):
        self.run_js("""
const a='18446744073709551615', b='18446744073709551614';
assert.equal(Number(a), Number(b));
assert.equal(signalTicketText({ticket:Number(a)}), '');
assert.equal(signalTicketText({ticket:Number(a),ticketText:a}),a);
assert.equal(signalTicketText({ticketText:'18446744073709551616'}),'');
const source={consensus:{decision:'SELL'},orderLinkage:{available:true,commandId:'cmd-a',ticketText:a}};
const orders=[{commandId:'cmd-a',ticket:Number(a),ticketText:b,status:'open',side:'BUY'},
 {commandId:'cmd-a',ticket:Number(a),ticketText:a,status:'closed',side:'SELL',executionState:'CLOSED',
 outcomeIdentityVerified:true,verificationStatus:'VERIFIED_CLOSED',closedPnl:2}];
const result=signalHistoryOrderState(source,{missionId:'mission-a'},orders);
assert.equal(result.label,'ปิด SELL'); assert.match(result.detail,new RegExp(a)); assert.doesNotMatch(result.detail,new RegExp(b));
""")

    def test_drift_and_previous_ack_blocks_are_readable_not_missing_evidence(self):
        self.run_js("""
const identity={missionId:'mission-a'};
const drift=signalHistoryOrderState({consensus:{decision:'SELL'},tradeGateway:{status:'blocked',
 reasonCode:'signal_price_drift_exceeded_before_publish',commandPublished:false,
 executionPricePreflight:{priceDriftPoints:444,maximumSignalDriftPoints:100}}},identity,[]);
assert.match(drift.label,/บล็อกก่อนส่ง/); assert.match(drift.detail,/444.*100/);
assert.match(drift.detail,/signal_price_drift_exceeded_before_publish/);
const pending=signalHistoryOrderState({consensus:{decision:'SELL'},tradeGateway:{status:'waiting_previous_ack',
 reasonCode:'single_outstanding_command',commandPublished:false}},identity,[]);
assert.match(pending.detail,/คำสั่งก่อนหน้า.*single_outstanding_command/);
assert.doesNotMatch(pending.detail,/ไม่พบหลักฐาน/);
""")

    def test_ack_rejection_only_attaches_to_exact_pending_command(self):
        self.run_js("""
const history={pendingCommands:[{commandId:'cmd-a',outstanding:true,status:'expired_waiting_ack',reasonCode:'expired_waiting_ack'}],items:[]};
const report={aiTradeCouncil:{tradeGateway:{ackEvents:[{commandId:'cmd-other',code:'invalid_ack_ticket'}]}}};
assert.equal(signalPendingCommandModels(report,history)[0].reasonCode,'expired_waiting_ack');
report.aiTradeCouncil.tradeGateway.ackEvents.push({commandId:'cmd-a',code:'invalid_ack_ticket'});
const result=signalPendingCommandModels(report,history)[0];
assert.match(result.detail,/Ticket ไม่ถูกต้อง.*ห้ามส่งซ้ำ/);
assert.equal(history.items.length,0);
assert.equal(signalPendingCommandModels(report,{...history,scopePending:true}).length,0);
assert.equal(signalPendingCommandModels(report,{...history,available:false}).length,0);
""")

    def test_snapshot_age_block_explains_actual_and_ea_limit_without_inventing_numbers(self):
        self.run_js("""
const identity={missionId:'mission-a'};
const source={consensus:{decision:'SELL'},tradeGateway:{status:'blocked',
 reasonCode:'analysis_snapshot_stale_before_publish',commandPublished:false,
 executionPricePreflight:{analysisSnapshotAgeSeconds:390.23,maximumSnapshotAgeSeconds:300}}};
const result=signalHistoryOrderState(source,identity,[]);
assert.match(result.label,/บล็อกก่อนส่ง/);
assert.match(result.detail,/Snapshot.*390.2 วินาที.*300 วินาที/);
assert.match(result.detail,/เก่าเกินเกณฑ์ของ EA/);
assert.equal(source.tradeGateway.commandPublished,false);
for(const value of [null,undefined,'300',false,-1]) {
 assert.equal(signalSnapshotAgeDetail({analysisSnapshotAgeSeconds:value,maximumSnapshotAgeSeconds:300}),'');
}
const skipped=signalHistoryOrderState({coverageStatus:'skipped',skipReasonCode:'analysis_snapshot_expired_before_start',
 analysisStartPreflight:{analysisSnapshotAgeSeconds:600,maximumSnapshotAgeSeconds:300}},identity,[]);
assert.match(skipped.detail,/ข้ามโดยไม่เรียก AI.*600 วินาที.*300 วินาที/);
assert.doesNotMatch(skipped.label,/เปิดสำเร็จ/);
for(const reasonCode of ['analysis_snapshot_expired_before_start','analysis_snapshot_time_invalid_before_start']) {
 const audit=signalHistoryOrderState({status:'completed',finalDecision:'SELL',analysisContext:{automation:{
 analysisStartPreflight:{status:'audit_only',reasonCode,analysisSnapshotAgeSeconds:600,maximumSnapshotAgeSeconds:300}}}},identity,[]);
 assert.match(audit.label,/วิเคราะห์เก็บประวัติ.*ไม่ส่งคำสั่ง/);
 assert.match(audit.detail,/600 วินาที.*300 วินาที/);
 assert.doesNotMatch(audit.label+' '+audit.detail,/ข้าม|เปิดสำเร็จ/);
}
""")

    def test_cancelled_backlog_overrides_legacy_audit_preflight_without_changing_evidence(self):
        self.run_js("""
const source={status:'skipped',coverageStatus:'skipped',skipReasonCode:'new_bar_only_backlog_cancelled',
 analysisStartPreflight:{status:'audit_only',reasonCode:'analysis_snapshot_expired_before_start',
  analysisSnapshotAgeSeconds:600,maximumSnapshotAgeSeconds:300}};
const before=JSON.stringify(source),result=signalHistoryOrderState(source,{missionId:''},[]);
assert.equal(result.label,'ข้ามรอบ • ไม่มีคำสั่ง');
assert.match(result.detail,/ยกเลิกคิวย้อนหลัง.*ไม่เรียก AI.*600 วินาที.*300 วินาที/);
assert.doesNotMatch(result.label+' '+result.detail,/วิเคราะห์เก็บประวัติ|รอวิเคราะห์/);
assert.equal(JSON.stringify(source),before);
""")

    def test_new_bar_skip_reasons_remain_readable_and_never_appear_as_hold_votes(self):
        self.run_js("""
for(const reasonCode of ['new_bar_only_trigger_not_admitted','new_bar_only_trigger_window_expired',
 'new_bar_only_missed_trigger','new_bar_only_restart_baseline','new_bar_only_stream_change_baseline',
 'quota_limit_reached','quota_unavailable','quota_below_reserve','quota_stale','quota_incomplete',
 'codex_runner_not_ready','daily_cap_reached','council_new_bar_all_votes_skipped',
 'council_new_bar_analysis_snapshot_expired_before_start','council_new_bar_execution_age_limit_unavailable_before_start',
 'council_new_bar_gate_skipped_quota_limit_reached','council_new_bar_gate_skipped_runner_busy']) {
 const result=signalHistoryOrderState({coverageStatus:'skipped',skipReasonCode:reasonCode},{missionId:''},[]);
 assert.equal(result.label,'ข้ามรอบ • ไม่มีคำสั่ง',reasonCode);
 assert.match(result.detail,/ข้าม|ไม่วิเคราะห์ย้อนหลัง|ไม่เรียก AI/,reasonCode);
 assert.match(result.detail,new RegExp(reasonCode));
 assert.doesNotMatch(result.label+' '+result.detail,/HOLD|เปิดสำเร็จ|กำลังวิเคราะห์|รอวิเคราะห์/,reasonCode);
}
""")

    def test_ready_or_queued_never_becomes_open_and_unknown_lifecycle_is_explicit(self):
        self.run_js("""
for(const status of ['ready','queued']) {
 const result=signalHistoryOrderState({consensus:{decision:'SELL'},tradeGateway:{status,commandPublished:status==='queued'}},{missionId:'m'},[]);
 assert.doesNotMatch(result.label,/^เปิด SELL|^ปิด SELL/);
}
const result=signalHistoryOrderState({consensus:{decision:'SELL'}},{missionId:'m'},[{missionId:'m',ticket:500029817749,status:'confirmed_unknown',side:'SELL'}]);
assert.match(result.label,/ไม่ทราบสถานะล่าสุด/);
""")

    def test_old_deferred_work_does_not_promise_backfill_or_invent_a_skip(self):
        self.run_js("""
const source={status:'pending',coverageStatus:'pending',queue:{position:null,depth:512,deferred:true,
 reasonCode:'pending_runnable_window_deferred'},skipReasonCode:null};
const before=JSON.stringify(source),result=signalHistoryOrderState(source,{missionId:''},[]);
assert.match(result.label,/คิวเดิม.*รอ Backend ยืนยันสถานะ/);
assert.match(result.detail,/ยังไม่มีคำสั่ง.*ไม่วิเคราะห์ย้อนหลัง/);
assert.doesNotMatch(result.label+' '+result.detail,/ข้าม|ล้มเหลว|เปิดสำเร็จ/);
assert.equal(JSON.stringify(source),before);
""")

    def test_closed_cost_display_does_not_coerce_nulls_or_partial_evidence_to_zero(self):
        self.run_js("""
const order={status:'closed',executionState:'CLOSED',outcomeIdentityVerified:true,verificationStatus:'VERIFIED_CLOSED',
 ackStatus:'EXECUTED',closePrice:4080.5,grossProfit:2,commission:-0.7,swap:-0.2,fee:0};
assert.match(signalOrderClosedFinancialText(order),/ราคาปิด.*Commission -0.7.*Swap -0.2.*Fee 0/);
for(const value of [null,undefined,'',false]) {
 const result=signalOrderClosedFinancialText({...order,commission:value});
 assert.match(result,/ยังไม่มีหลักฐาน/); assert.doesNotMatch(result,/Commission 0/);
}
assert.equal(signalOrderClosedFinancialText({...order,outcomeIdentityVerified:false}), '');
assert.equal(signalOrderClosedFinancialText({...order,ackStatus:'EXECUTION_UNKNOWN'}), '');
assert.equal(signalOrderClosedFinancialText({...order,executionState:'OPEN'}), '');
""")

    def test_validated_history_page_is_not_hidden_by_unavailable_compact_report(self):
        script = "const assert=require('node:assert/strict');\n"
        script += "const safeDashboardDisplayText=(v,f='')=>v==null?f:String(v);\n"
        script += function_block(self.main, "function signalHistoryMergedReadModel(")
        script += """
const base={available:false,error:{code:'gateway_stale'},reasonCode:'gateway_stale',items:[],
 scope:{authoritative:true,mode:'all'}};
const page={initialized:true,scopeKey:'all',items:[{commandId:'cmd-history'}],summary:{total:1},
 scope:{authoritative:true,mode:'all'},pendingCommands:[],errorMessage:''};
const state={aiTradeCouncilHistoryPages:{orders:page}};
function signalHistoryBaseReadModel(){return base;}
function signalHistoryRequestScope(){return {mode:'all'};}
function signalHistoryPageScopeKey(){return 'all';}
function signalHistoryAttemptKey(item){return item.commandId;}
let result=signalHistoryMergedReadModel({},'orders');
assert.equal(result.available,true); assert.equal(result.error,null); assert.equal(result.reasonCode,null);
assert.equal(result.items.length,1); assert.equal(result.summary.total,1);
page.errorMessage='newer page request failed';
result=signalHistoryMergedReadModel({},'orders');
assert.equal(result.available,true); assert.equal(result.paginationError,'newer page request failed');
page.scopeKey='different-scope';
result=signalHistoryMergedReadModel({},'orders');
assert.equal(result.available,false); assert.equal(result.reasonCode,'gateway_stale'); assert.equal(result.items.length,0);
page.scopeKey='all'; page.initialized=false;
assert.equal(signalHistoryMergedReadModel({},'orders').available,false);
"""
        result = subprocess.run([self.node, "-"], input=script, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
