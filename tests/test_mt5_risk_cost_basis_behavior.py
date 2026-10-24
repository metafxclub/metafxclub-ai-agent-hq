"""Execute extracted MT5 sizing/guard bodies against deterministic broker APIs.

This syntax-limited harness preserves scalar output references with accessor
boxes. Broker calculations are deterministic doubles, not an MT5 emulator or
native compile proof; the sizing, rounding, budget and guard branches are MQ5.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5"


def extract(source, name):
    match = re.search(rf"(?ms)^(?:bool|void|int|string|double)\s+{name}\s*\((.*?)\)\s*\{{(.*?)^\}}", source)
    if not match:
        raise AssertionError(name)
    return match.group(1), match.group(2)


def arguments(text, opening):
    depth, start, args = 1, opening + 1, []
    for index in range(start, len(text)):
        ch = text[index]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                args.append(text[start:index].strip())
                return args, index
        elif ch == "," and depth == 1:
            args.append(text[start:index].strip())
            start = index + 1
    raise AssertionError("Unclosed call")


def compile_functions(source, names):
    parsed = {name: extract(source, name) for name in names}
    refs = {}
    for name, (parameters, _) in parsed.items():
        refs[name] = [i for i, p in enumerate(parameters.split(","))
                      if re.search(r"\b(?:double|int|string|bool)\s*&", p)]
    refs.update({"SymbolInfoDouble": [2], "OrderCalcProfit": [5], "OrderCalcMargin": [4],
                 "ReadManagedOpenState": [0, 1, 2], "ReadDirectionalSymbolVolume": [1, 2],
                 "NormalizedManagedMagicNumbers": [0], "Sha256TextHex": [1],
                 "ValidateCurrentRiskState": [1], "LiveAccountOwnerLockReady": [0],
                 "ValidateConfiguredModes": [0], "ReadFreshTick": [1],
                 "ValidateHeartbeat": [1], "ValidateClosedBarBinding": [2],
                 "BuildTradeRequest": [4], "CheckTradeRequest": [2], "ReadLastOrderBar": [0]})
    output = []
    for name, (parameters, body) in parsed.items():
        parameter_names = [re.search(r"(\w+)\s*$", p).group(1) for p in parameters.split(",") if p.strip()]
        body = re.sub(r"//[^\n]*", "", body)
        for index in refs[name]:
            body = re.sub(rf"\b{parameter_names[index]}\b", parameter_names[index] + ".value", body)
        for match in reversed(list(re.finditer(r"\b(" + "|".join(refs) + r")\s*\(", body))):
            callee = match.group(1)
            opening = body.index("(", match.start())
            args, closing = arguments(body, opening)
            for index in refs[callee]:
                if index < len(args):
                    arg = args[index]
                    args[index] = "{get value(){return " + arg + ";},set value(v){" + arg + "=v;}}"
            body = body[:opening + 1] + ",".join(args) + body[closing:]
        body = re.sub(r"\bconst\s+", "", body)
        body = re.sub(r"\b(?:bool|int|long|double|string|uint|ulong|datetime|ENUM_\w+)\s+(\w+)", r"let \1", body)
        body = re.sub(r"\bMql\w+\s+(\w+)\s*;", r"let \1 = {};", body)
        body = re.sub(r"\((?:int|long|uint|ulong|double|datetime|ENUM_\w+)\)", "", body)
        output.append(f"function {name}({','.join(parameter_names)}) {{{body}\n}}")
    return "\n".join(output)


class Mt5RiskCostBasisBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("Node required for extracted MQL behavior")
        cls.source = SOURCE.read_text(encoding="utf-8")
        names = ("EffectiveRiskPercent", "EffectiveEstimatedCommissionPerLot", "RiskCostBasisName",
                 "ReadBrokerVolumeLimits", "ValidateVolumeOnBrokerGrid", "ValidateFixedLot",
                 "ValidateMoneyManagementConfiguration", "SelectedRiskCapital", "ResolveOrderVolume",
                 "ValidateRiskEnvelope", "ValidateStopsWithTick", "FilledRiskAssessmentCode",
                 "GatewayInitializationReady", "InitializationBlockReason", "ValidateRuntime",
                 "SetAckSizingEvidence", "BuildPortfolioPolicyCanonical")
        cls.functions = compile_functions(cls.source, names)
        prefix = cls.source.split("struct CommandPayload", 1)[0]
        declarations = ["const INVALID_HANDLE=-1, INIT_FAILED=1;"]
        for _, values in re.findall(r"enum\s+(\w+)\s*\{([^}]+)\}", prefix):
            declarations.extend(f"const {name}={value};" for name, value in re.findall(r"(\w+)\s*=\s*(\d+)", values))
        declarations.extend(f"let {name}={value};" for name, value in re.findall(
            r"(?m)^(?:input\s+|const\s+)?(?:string|bool|int|uint|double|ENUM_\w+)\s+(\w+)\s*=\s*([^;]+);", prefix))
        cls.declarations = "\n".join(declarations)

    def run_js(self, scenario):
        script = r"""
const assert=require('node:assert/strict');
const ORDER_TYPE_BUY=0, ORDER_TYPE_SELL=1, FILE_COMMON=1, _Symbol='XAUUSD', _Period=16385;
const SYMBOL_VOLUME_MIN=0, SYMBOL_VOLUME_MAX=1, SYMBOL_VOLUME_STEP=2, SYMBOL_VOLUME_LIMIT=3;
const SYMBOL_POINT=4, ACCOUNT_BALANCE=5, ACCOUNT_EQUITY=6, ACCOUNT_MARGIN_FREE=7;
const SYMBOL_TRADE_STOPS_LEVEL=8, SYMBOL_TRADE_FREEZE_LEVEL=9, MQL_TESTER=10, MQL_OPTIMIZATION=11;
let balance=10000,equity=10000,freeMargin=10000,minLot=.01,maxLot=100,step=.01,volumeLimit=0;
let managedLots=0,directionalLots=0,point=.01,blocked='',profitCalls=[],demo=false;
const ref=value=>({value});
const MathIsValidNumber=Number.isFinite, MathMin=Math.min, MathMax=Math.max, MathAbs=Math.abs;
const MathFloor=Math.floor, MathRound=Math.round;
const NormalizeDouble=(x,n)=>Number(x.toFixed(n)), NormalizeSymbolPrice=x=>x;
const DoubleToString=(x,n)=>x.toFixed(n), IntegerToString=String, LotDigits=()=>2;
function SymbolInfoDouble(symbol,key,out){
 const value=({[SYMBOL_VOLUME_MIN]:minLot,[SYMBOL_VOLUME_MAX]:maxLot,[SYMBOL_VOLUME_STEP]:step,
 [SYMBOL_VOLUME_LIMIT]:volumeLimit,[SYMBOL_POINT]:point})[key];
 if(out){out.value=value;return blocked!=='volume_metadata';} return value;
}
const SymbolInfoInteger=()=>0;
const AccountInfoDouble=key=>({[ACCOUNT_BALANCE]:balance,[ACCOUNT_EQUITY]:equity,[ACCOUNT_MARGIN_FREE]:freeMargin})[key];
function OrderCalcProfit(type,symbol,volume,entry,exit,out){
 profitCalls.push({volume,entry,exit});
 out.value=(type===ORDER_TYPE_BUY?exit-entry:entry-exit)*100*volume;
 return blocked!=='profit';
}
function OrderCalcMargin(type,symbol,volume,entry,out){out.value=volume*1000;return true;}
function ReadManagedOpenState(count,lots,pnl){count.value=0;lots.value=managedLots;pnl.value=0;return true;}
function ReadDirectionalSymbolVolume(type,lots,reason){lots.value=directionalLots;return true;}
function ValidateCurrentRiskState(volume,reason){if(blocked==='daily_loss'){reason.value='MAX_DAILY_LOSS_REACHED';return false;}return true;}
const PositionSizingModeName=()=>MoneyManagementMode===MONEY_MANAGEMENT_RISK_PERCENT?'RISK_PERCENT':'FIXED_LOT';
const RiskCapitalBaseName=()=>RiskCapitalBase===RISK_CAPITAL_EQUITY?'EQUITY':'BALANCE';
function NormalizedManagedMagicNumbers(out){out.value='4186001';return true;}
function Sha256TextHex(value,out){out.value='digest:'+value;return true;}
const IsDemo=()=>demo, IsHedgingAccount=()=>blocked!=='hedging';
const IsConnected=()=>blocked!=='connection', IsTradeAllowed=()=>blocked!=='trading';
const ValidateConfiguredModes=()=>true, NowUtc=()=>1000, Uppercase=s=>s.toUpperCase();
const IsCommandIdentifier=()=>true, IsIdempotencyIdentifier=()=>true, IsHeartbeatIdentifier=()=>true;
const TimeframeToPeriod=()=>_Period, MQLInfoInteger=()=>0;
const CsvContains=(csv,s)=>s==='H1'||(blocked!=='symbol'&&csv.split(',').includes(s));
const IsAllowedBrokerSymbol=()=>true, KillMarkerPath=()=>'', FileIsExist=()=>blocked==='kill';
function LiveAccountOwnerLockReady(reason){if(blocked==='owner'){reason.value='LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE';return false;}return true;}
function ValidateHeartbeat(command,reason){if(blocked==='heartbeat'){reason.value='HEARTBEAT_MISSING';return false;}return true;}
function ReadFreshTick(tick,reason){Object.assign(tick,{bid:99.98,ask:100});return true;}
const ValidateClosedBarBinding=()=>true, BuildTradeRequest=()=>true;
function CheckTradeRequest(request,result,reason){if(blocked==='margin'){reason.value='MIN_MARGIN_LEVEL_NOT_MET';return false;}return true;}
function ReadLastOrderBar(out){out.value=0;return true;}
const SignedCommandVerificationAvailable=()=>blocked!=='signing';
""" + self.declarations + "\n" + self.functions + r"""
GatewayMode=GATEWAY_LIVE; LiveArmed=true; SingleHostLiveAcknowledged=true;
g_channel_lock_handle=10;g_runtime_initialized=true;MoneyManagementMode=MONEY_MANAGEMENT_RISK_PERCENT;
const command={action:'BUY',stop_loss:90,take_profit:120,schema_version:COMMAND_SCHEMA,command_id:'c',
 idempotency_key:'i',heartbeat_id:'h',channel_id:SnapshotChannel,symbol:'XAUUSD',timeframe:'H1',issued_at:999,expires_at:1060,bar_time:950};
const tick={ask:100,bid:99.98};
function size(cmd=command,t=tick){const volume=ref(0),capital=ref(0),risk=ref(0),reason=ref('');
 const ok=ResolveOrderVolume(cmd,t,volume,capital,risk,reason);return {ok,volume:volume.value,capital:capital.value,risk:risk.value,reason:reason.value};}
function evidence(s){SetAckSizingEvidence(s.volume,PositionSizingModeName(),EffectiveRiskPercent(),RiskCapitalBaseName(),EffectiveEstimatedCommissionPerLot(),s.capital,s.risk);}
function envelope(s,cmd=command,t=tick){evidence(s);const risk=ref(0),reason=ref('');const ok=ValidateRiskEnvelope(cmd,t,s.volume,risk,reason);return {ok,risk:risk.value,reason:reason.value};}
""" + scenario
        result = subprocess.run([self.node, "-"], input=script, text=True, capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_fee_inputs_do_not_change_buy_sell_lots_or_budget(self):
        self.run_js(r"""
for(const action of ['BUY','SELL']){
 const cmd={...command,action,stop_loss:action==='BUY'?90:110,take_profit:action==='BUY'?120:80};
 let expected;
 for(const fee of [0,7,1000000,NaN,-1])for(const confirmation of [false,true]){
  EstimatedCommissionPerLot=fee;CommissionFreeAccountConfirmed=confirmation;
  const s=size(cmd);assert.equal(s.ok,true);assert.equal(s.volume,.09);
  assert.ok(s.risk<=100);assert.ok(s.risk>90);
  assert.equal(EffectiveEstimatedCommissionPerLot(),0);
  const verified=envelope(s,cmd);assert.equal(verified.ok,true);assert.equal(verified.risk,s.risk);
  assert.equal(g_ack_estimated_commission_per_lot,0);
  if(expected)assert.deepEqual(s,expected);expected=s;
 }
}
assert.ok(profitCalls.some(c=>c.entry===100.03));
assert.ok(profitCalls.some(c=>Math.abs(c.entry-99.95)<1e-9));
console.log(JSON.stringify({ok:true}));
""")

    def test_one_percent_cap_adverse_entry_and_stop_direction_remain_enforced(self):
        self.run_js(r"""
EstimatedCommissionPerLot=7;CommissionFreeAccountConfirmed=false;
RiskPercent=1.01;assert.equal(size().reason,'RISK_PERCENT_INVALID_OR_ABOVE_HARD_CAP');RiskPercent=1;
const s=size();assert.equal(s.ok,true);
const changed=envelope(s,command,{ask:103,bid:102.98});assert.equal(changed.ok,false);
assert.equal(changed.reason,'MAX_LOSS_PER_TRADE_EXCEEDED');
assert.equal(size({...command,stop_loss:101}).reason,'RISK_STOP_LOSS_CALCULATION_FAILED');
const reason=ref('');assert.equal(ValidateStopsWithTick({...command,stop_loss:0},tick,reason),false);
assert.equal(reason.value,'STOP_CONFIGURATION_INVALID');
MoneyManagementMode=MONEY_MANAGEMENT_FIXED_LOT;FixedLot=.1;
const fixed=size();assert.equal(fixed.ok,true);assert.equal(envelope(fixed).reason,'MAX_LOSS_PER_TRADE_EXCEEDED');
console.log(JSON.stringify({ok:true}));
""")

    def test_broker_grid_exposure_and_margin_caps_still_fail_closed(self):
        self.run_js(r"""
freeMargin=1;assert.equal(size().reason,'BROKER_MARGIN_CALCULATION_FAILED_OR_INSUFFICIENT');freeMargin=10000;
managedLots=.09;assert.equal(size().volume,.01);managedLots=.1;
assert.equal(size().reason,'RISK_VOLUME_BELOW_BROKER_MINIMUM');managedLots=0;
volumeLimit=.04;directionalLots=.02;assert.equal(size().volume,.02);
directionalLots=.04;assert.equal(size().reason,'RISK_VOLUME_BELOW_BROKER_MINIMUM');
volumeLimit=0;directionalLots=0;minLot=.1;step=.1;
assert.equal(size().reason,'RISK_VOLUME_BELOW_BROKER_MINIMUM');
minLot=.01;step=.01;blocked='volume_metadata';assert.equal(size().reason,'BROKER_VOLUME_LIMITS_UNAVAILABLE');
blocked='profit';assert.equal(size().reason,'RISK_STOP_LOSS_CALCULATION_FAILED');
console.log(JSON.stringify({ok:true}));
""")

    def test_live_runtime_no_longer_requires_commission_but_other_guards_remain(self):
        self.run_js(r"""
EstimatedCommissionPerLot=0;CommissionFreeAccountConfirmed=false;const s=size();evidence(s);
const reason=ref('');assert.equal(ValidateRuntime(command,s.volume,reason),true);
for(const [cause,expected] of [['owner','LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE'],['hedging','MT5_HEDGING_ACCOUNT_REQUIRED'],
 ['kill','KILL_SWITCH_ACTIVE'],['symbol','LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST'],['heartbeat','HEARTBEAT_MISSING'],
 ['connection','TERMINAL_NOT_CONNECTED'],['daily_loss','MAX_DAILY_LOSS_REACHED'],['margin','MIN_MARGIN_LEVEL_NOT_MET'],
 ['signing','SIGNED_COMMAND_VERIFICATION_NOT_READY'],['trading','EA_TRADING_NOT_ALLOWED']]){
 blocked=cause;reason.value='';assert.equal(ValidateRuntime(command,s.volume,reason),false,cause);assert.equal(reason.value,expected,cause);
}
blocked='';LiveArmed=false;assert.equal(ValidateRuntime(command,s.volume,reason),false);assert.equal(reason.value,'LIVE_NOT_ARMED');
LiveArmed=true;SingleHostLiveAcknowledged=false;assert.equal(ValidateRuntime(command,s.volume,reason),false);assert.equal(reason.value,'SINGLE_HOST_LIVE_ACK_REQUIRED');
SingleHostLiveAcknowledged=true;demo=true;assert.equal(ValidateRuntime(command,s.volume,reason),false);assert.equal(reason.value,'LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT');
demo=false;g_runtime_initialized=false;assert.equal(ValidateRuntime(command,s.volume,reason),false);assert.equal(reason.value,'GATEWAY_INITIALIZATION_INCOMPLETE');
assert.equal(CommissionFreeAccountConfirmed,false);
console.log(JSON.stringify({ok:true}));
""")

    def test_policy_identity_ignores_legacy_inputs_but_binds_explicit_cost_basis(self):
        self.run_js(r"""
let expected;
for(const fee of [0,7,1000000])for(const confirmed of [false,true]){
 EstimatedCommissionPerLot=fee;CommissionFreeAccountConfirmed=confirmed;
 const canonical=ref(''),digest=ref('');assert.equal(BuildPortfolioPolicyCanonical(canonical,digest),true);
 assert.ok(canonical.value.includes('|riskCostBasis=price_and_slippage_excluding_commission'));
 assert.ok(canonical.value.includes('|estimatedCommissionPerLot=0.00000000'));
 assert.ok(!canonical.value.includes('commissionFreeAccountConfirmed'));
 if(expected)assert.equal(canonical.value,expected);expected=canonical.value;
}
console.log(JSON.stringify({ok:true}));
""")

    def test_recorded_recovery_fee_is_not_rewritten_by_new_effective_fee(self):
        self.run_js(r"""
EstimatedCommissionPerLot=1000000;
SetAckSizingEvidence(1,'RISK_PERCENT',1,'EQUITY',7,10000,100);
assert.equal(g_ack_estimated_commission_per_lot,7);assert.equal(EffectiveEstimatedCommissionPerLot(),0);
assert.equal(FilledRiskAssessmentCode('BUY',1,100,100,99,g_ack_estimated_commission_per_lot,100),'RISK_ESTIMATE_EXCEEDED');
assert.equal(FilledRiskAssessmentCode('BUY',1,100,100,99,0,100),'WITHIN_ESTIMATE');
console.log(JSON.stringify({ok:true}));
""")
        recovery = extract(self.source, "ReconcileExecutingCommand")[1]
        self.assertIn("attempt.estimated_commission_per_lot", recovery)
        self.assertNotIn("EffectiveEstimatedCommissionPerLot()", recovery)
        for helper in ("ManagedDailyPnl", "ManagedWeeklyPnl", "ReadManagedLossStreak"):
            # Actual fee aggregation is kept in the shared strict deal-history readers.
            self.assertIn(helper, self.source)
        self.assertIn("profit + swap + commission + fee", self.source)


if __name__ == "__main__":
    unittest.main()
