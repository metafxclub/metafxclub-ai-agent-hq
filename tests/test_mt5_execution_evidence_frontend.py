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


class Mt5ExecutionEvidenceFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8-sig")
        cls.node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")

    def run_js(self, body):
        script = "const assert=require('node:assert/strict');\n"
        script += "const safeDashboardDisplayText=(value,fallback='')=>value == null ? fallback : String(value);\n"
        for signature in ("function signalGatewayAckSizingSummary(", "function signalExecutionGuardReasonLabel(", "function signalExecutionGuardRecoveryLabel("):
            script += function_block(self.main, signature)
        script += r"""
function ack(extra={}) { return {status:'EXECUTED',sizingEvidenceSource:'ea_ack_read_only',
 sizingEvidenceAuthoritative:false,resolvedLot:0.01,positionSizingMode:'FIXED_LOT',
 estimatedRiskMoney:10,riskCapitalAmount:1000,...extra}; }
"""
        result = subprocess.run([self.node, "-"], input=script + body + "\nprocess.stdout.write(JSON.stringify({ok:true}));", text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True})

    def test_verified_open_and_postfill_warnings_never_claim_order_was_blocked(self):
        self.run_js(r"""
assert.match(signalExecutionGuardReasonLabel('ORDER_VERIFIED_OPEN'),/ยืนยันว่าเปิด Order แล้ว/);
for (const code of [
 'ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED',
 'ORDER_VERIFIED_OPEN_RISK_ESTIMATE_EXCEEDED',
 'ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_EXCEEDED',
 'ORDER_VERIFIED_OPEN_RISK_UNAVAILABLE',
]) {
 const text=signalExecutionGuardReasonLabel(code);
 assert.match(text,/เปิด Order แล้ว.*คำเตือน/);
 assert.doesNotMatch(text,/ยังไม่อนุญาต|ไม่ได้เปิด|ปฏิเสธ/);
 assert.match(signalExecutionGuardRecoveryLabel(code),/ไม่ส่ง.*ซ้ำ|ไม่ใช่เหตุให้ส่งซ้ำ/);
}
assert.match(signalExecutionGuardReasonLabel('UNKNOWN_FUTURE_CODE'),/ยังไม่อนุญาต/);
assert.match(signalExecutionGuardReasonLabel('EXECUTION_SLIPPAGE_EVIDENCE_UNAVAILABLE'),/ส่งคำสั่งไปแล้ว.*ยังตรวจ.*ไม่ได้.*ห้ามส่งซ้ำ/);
assert.doesNotMatch(signalExecutionGuardReasonLabel('EXECUTION_SLIPPAGE_EVIDENCE_UNAVAILABLE'),/ไม่ได้เปิด Order|Slippage.* 0/);
""")

    def test_unknown_recovered_slippage_is_explicit_and_never_coerced_to_zero(self):
        self.run_js(r"""
for (const value of [null,0,undefined]) {
 const input=Object.freeze(ack({filledSlippageKnown:false,filledSlippagePoints:value,reasonCode:'RECOVERED_ORDER_FOUND'}));
 const before=JSON.stringify(input), text=signalGatewayAckSizingSummary(input,'USD');
 assert.match(text,/คำเตือน: ไม่ทราบ Slippage.*หลักฐานกู้คืน/);
 assert.doesNotMatch(text,/Slippage ที่ EA รายงาน 0/);
 assert.equal(JSON.stringify(input),before);
}
for (const code of ['RECOVERED_ORDER_FOUND','EXECUTION_RECONCILED_WITH_WARNING']) {
 assert.match(signalExecutionGuardReasonLabel(code),/หลักฐาน.*Broker.*ไม่ส่งคำสั่งซ้ำ/);
 assert.doesNotMatch(signalExecutionGuardReasonLabel(code),/ยังไม่อนุญาต|ไม่ได้เปิด/);
}
""")

    def test_measured_and_legacy_numeric_slippage_remain_distinct_from_missing_data(self):
        self.run_js(r"""
for (const known of [true,undefined]) {
 for (const value of [0,3.5]) {
  assert.match(signalGatewayAckSizingSummary(ack({filledSlippageKnown:known,filledSlippagePoints:value})),new RegExp('Slippage ที่ EA รายงาน '+value+' จุด'));
 }
 for (const value of [null,undefined,'',false,NaN,-1]) {
  const text=signalGatewayAckSizingSummary(ack({filledSlippageKnown:known,filledSlippagePoints:value}));
  assert.match(text,/ไม่พบหลักฐาน Slippage ที่ตรวจสอบได้/);
  assert.doesNotMatch(text,/Slippage ที่ EA รายงาน 0/);
 }
}
for (const known of ['false',0,null,{}]) {
 assert.match(signalGatewayAckSizingSummary(ack({filledSlippageKnown:known,filledSlippagePoints:0})),/ไม่พบหลักฐาน Slippage ที่ตรวจสอบได้/);
}
""")

    def test_nonexecution_or_untrusted_sizing_does_not_invent_fill_evidence(self):
        self.run_js(r"""
for (const status of ['REJECTED','SHADOWED','EXECUTION_UNKNOWN','FAILED_FINAL','']) {
 assert.doesNotMatch(signalGatewayAckSizingSummary(ack({status,filledSlippageKnown:false,filledSlippagePoints:null})),/Slippage/);
}
for (const change of [{sizingEvidenceSource:'backend'},{sizingEvidenceAuthoritative:true}]) {
 assert.equal(signalGatewayAckSizingSummary(ack(change)),'');
}
""")

    def test_waiting_for_real_tick_is_not_an_initialization_failure_or_permission(self):
        self.run_js(r"""
assert.match(signalExecutionGuardReasonLabel('QUOTE_NOT_OBSERVED'),/รอ Tick ใหม่.*เริ่มทำงานหรือเชื่อมต่อ Broker ใหม่/);
assert.match(signalExecutionGuardReasonLabel('QUOTE_STALE_OR_FUTURE'),/เก่าเกินกำหนดหรือเวลา Broker.*ยังไม่ส่ง/);
assert.match(signalExecutionGuardRecoveryLabel('QUOTE_STALE_OR_FUTURE'),/Tick ใหม่.*EA ได้รับจริง/);
assert.doesNotMatch(signalExecutionGuardReasonLabel('QUOTE_NOT_OBSERVED'),/เริ่มระบบไม่ผ่าน|พร้อมส่ง Order/);
""")
        runtime_truth = function_block(self.main, "function getSignalRuntimeTruth(report = {})")
        self.assertNotIn("filledSlippageKnown", runtime_truth)
        self.assertNotIn("signalGatewayAckSizingSummary", runtime_truth)


if __name__ == "__main__":
    unittest.main()
