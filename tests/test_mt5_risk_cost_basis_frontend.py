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


class Mt5RiskCostBasisFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "frontend/src/app/main.js").read_text(encoding="utf-8")
        cls.node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")

    def run_js(self, body):
        script = r"""
const assert = require('node:assert/strict');
const basis = 'price_and_slippage_excluding_commission';
const safeDashboardDisplayText = (value,fallback='') => value == null ? fallback : String(value);
const signalCouncilModel = report => report.aiTradeCouncil || {};
const signalCouncilRunModel = () => ({});
const signalCurrentConsensusSource = () => ({current:false});
const signalCommandMatchesCurrentRound = () => false;
const signalConnectionItem = () => ({});
const signalConnectionIsReady = () => false;
const signalSelectedPlatformConnectionHealth = report => ({platform:report.platform,candidateId:'candidate',connected:true});
const signalSelectedPlatform = report => report.platform;
const signalExecutionGuardReasonLabel = value => String(value);
function report(platform='MT5', overrides={}) { return {platform,
 connectionChecklist:{metatraderSelection:{candidateCount:1,selectedCandidate:{candidateId:'candidate'}}},
 aiTradeCouncil:{tradeGateway:{connected:true,selectedCandidateId:'candidate',mode:'live',
 executionGuardReady:false,executionGuardReason:'SIGNING_KEY_NOT_PINNED',liveArmed:false,
 liveOrderExecutionAvailable:false,demoOrderExecutionAvailable:false,
 estimatedCommissionPerLot:0,commissionFreeAccountConfirmed:false,riskCostBasis:basis,
 positionSizingMode:'RISK_PERCENT',riskPercent:1,riskCapitalBase:'BALANCE',maxLossPerTradePercent:1,
 fixedLot:null,...overrides}}}; }
function authority(runtime) { return {
 guard:runtime.gatewayExecutionGuardReady, reason:runtime.gatewayExecutionGuardReason,
 arm:runtime.gatewayLiveArmed, orders:runtime.orderSubmissionAvailable,
 live:runtime.liveOrderExecutionAvailable, demo:runtime.demoOrderExecutionAvailable,
 commissionFree:runtime.gatewayCommissionFreeAccountConfirmed,
 signing:runtime.signedCommandVerificationAvailable, killSwitch:runtime.killSwitchActive,
}; }
"""
        script += function_block(self.main, "function getSignalRuntimeTruth(report = {})")
        script += function_block(self.main, "function signalGatewaySizingSummary(runtime = {})")
        script += body + "\nprocess.stdout.write(JSON.stringify({ok:true}));"
        result = subprocess.run([self.node, "-"], input=script, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True})

    def test_mt5_excluded_costs_are_labelled_without_claiming_commission_free(self):
        self.run_js(r"""
for (const settings of [{}, {positionSizingMode:'FIXED_LOT',fixedLot:0.1}]) {
 const input=report('MT5',settings), before=JSON.stringify(input);
 const runtime=getSignalRuntimeTruth(input), summary=signalGatewaySizingSummary(runtime);
 assert.equal(runtime.gatewayRiskCostBasis,basis);
 assert.match(summary.value,/ความเสี่ยงถึง SL ไม่รวมค่าคอมมิชชัน/);
 assert.match(summary.value,/เพดานไม่เกิน 1% ของ Balance/);
 assert.match(summary.value,/ขาดทุนจริงอาจเกินงบจากค่าคอมมิชชัน, Fill, Gap หรือ Swap/);
 assert.doesNotMatch(summary.value,/ยังไม่ยืนยันนโยบายค่าคอมมิชชัน|ยืนยันบัญชีไม่มีค่าคอมมิชชัน|สำรองค่าธรรมเนียม/);
 assert.equal(summary.tone,'ready');
 assert.equal(runtime.gatewayCommissionFreeAccountConfirmed,false);
 assert.equal(JSON.stringify(input),before);
}
""")

    def test_basis_is_exact_mt5_policy_with_numeric_zero_effective_fee(self):
        self.run_js(r"""
for (const [platform,change] of [
 ['MT4',{}],['',{}],['MT5',{riskCostBasis:undefined}],
 ['MT5',{riskCostBasis:null}],['MT5',{riskCostBasis:true}],
 ['MT5',{riskCostBasis:[basis]}],['MT5',{riskCostBasis:{value:basis}}],
 ['MT5',{riskCostBasis:basis.toUpperCase()}],['MT5',{riskCostBasis:basis+' '}],
 ['MT5',{estimatedCommissionPerLot:'0'}],['MT5',{estimatedCommissionPerLot:null}],
 ['MT5',{estimatedCommissionPerLot:false}],['MT5',{estimatedCommissionPerLot:-1}],
]) {
 const runtime=getSignalRuntimeTruth(report(platform,change)), summary=signalGatewaySizingSummary(runtime);
 assert.equal(runtime.gatewayRiskCostBasis,'',JSON.stringify([platform,change]));
 assert.doesNotMatch(summary.value,/ความเสี่ยงถึง SL ไม่รวมค่าคอมมิชชัน/);
 assert.match(summary.value,/ยังไม่ยืนยันนโยบายค่าคอมมิชชัน/);
 assert.equal(summary.tone,'warning');
}
const nonzero=getSignalRuntimeTruth(report('MT5',{estimatedCommissionPerLot:25}));
assert.equal(nonzero.gatewayRiskCostBasis,'');
assert.match(signalGatewaySizingSummary(nonzero).value,/สำรองค่าธรรมเนียม 25/);
""")

    def test_legacy_mt4_and_mt5_keep_their_commission_confirmation_policy(self):
        self.run_js(r"""
for (const platform of ['MT4','MT5']) {
 const legacy=report(platform,{riskCostBasis:undefined,eaVersion:'1.05'});
 assert.match(signalGatewaySizingSummary(getSignalRuntimeTruth(legacy)).value,/ยังไม่ยืนยันนโยบายค่าคอมมิชชัน \(Live ถูกบล็อก\)/);
 legacy.aiTradeCouncil.tradeGateway.commissionFreeAccountConfirmed=true;
 assert.match(signalGatewaySizingSummary(getSignalRuntimeTruth(legacy)).value,/ยืนยันบัญชีไม่มีค่าคอมมิชชัน/);
 legacy.aiTradeCouncil.tradeGateway.commissionFreeAccountConfirmed=false;
 legacy.aiTradeCouncil.tradeGateway.estimatedCommissionPerLot=50;
 legacy.aiTradeCouncil.dailySummary={currency:'USC'};
 assert.match(signalGatewaySizingSummary(getSignalRuntimeTruth(legacy)).value,/สำรองค่าธรรมเนียม 50 USC\/lot/);
}
""")

    def test_selected_risk_capital_never_replaces_the_balance_hard_cap(self):
        self.run_js(r"""
for (const base of ['EQUITY','BALANCE',null,undefined,'UNKNOWN']) {
 const input=report('MT5',{positionSizingMode:'FIXED_LOT',fixedLot:0.01,riskCapitalBase:base});
 const runtime=getSignalRuntimeTruth(input), before=JSON.stringify(runtime);
 const summary=signalGatewaySizingSummary(runtime);
 assert.match(summary.value,/Fixed Lot 0.01.*เพดานไม่เกิน 1% ของ Balance/);
 assert.doesNotMatch(summary.value,/เพดานไม่เกิน 1% ของ Equity/);
 assert.equal(JSON.stringify(runtime),before);
}
for (const [base,label] of [['EQUITY','Equity'],['BALANCE','Balance']]) {
 const runtime=getSignalRuntimeTruth(report('MT5',{riskCapitalBase:base}));
 const summary=signalGatewaySizingSummary(runtime);
 assert.match(summary.value,new RegExp('เป้าหมาย Risk 1% ของ '+label));
 assert.match(summary.value,/เพดานไม่เกิน 1% ของ Balance/);
 assert.doesNotMatch(summary.value,/เพดานไม่เกิน 1% ของ Equity/);
}
""")

    def test_new_display_policy_never_grants_execution_or_changes_guard_reason(self):
        self.run_js(r"""
const legacy=getSignalRuntimeTruth(report('MT5',{riskCostBasis:undefined}));
const current=getSignalRuntimeTruth(report());
const before=JSON.stringify(current);
signalGatewaySizingSummary(current);
assert.deepEqual(authority(current),authority(legacy));
assert.deepEqual(authority(current),{guard:false,reason:'SIGNING_KEY_NOT_PINNED',arm:false,
 orders:false,live:false,demo:false,commissionFree:false,signing:false,killSwitch:false});
assert.equal(JSON.stringify(current),before);
const inconsistent=getSignalRuntimeTruth(report('MT5',{executionGuardReason:'LIVE_COMMISSION_POLICY_UNCONFIRMED'}));
assert.equal(inconsistent.gatewayExecutionGuardReason,'LIVE_COMMISSION_POLICY_UNCONFIRMED');
assert.equal(inconsistent.gatewayExecutionGuardReady,false);
""")


if __name__ == "__main__":
    unittest.main()
