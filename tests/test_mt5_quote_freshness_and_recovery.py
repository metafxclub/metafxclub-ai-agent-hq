"""Execute current MQ5 quote/recovery branches with deterministic terminal APIs.

This extends the resident-init harness; no terminal or broker is contacted.
The real function bodies retain scalar output references through accessor boxes.
"""
from __future__ import annotations

import re
import unittest

import test_mt5_gateway_resident_init as resident_harness
from test_mt5_risk_cost_basis_behavior import arguments, compile_functions


class Mt5QuoteFreshnessAndRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        resident_harness.Mt5GatewayResidentInitTests.setUpClass()
        cls.harness = resident_harness.Mt5GatewayResidentInitTests()
        cls.source = cls.harness.source
        names = (
            "ResetObservedTick", "ObserveChartTick", "ValidateObservedTickAge",
            "ReadFreshTick", "SnapshotMarketOpen", "OnTick", "UpdateRiskTelemetry",
            "ResetAckExecutionEvidence", "SetAckSizingEvidence", "BuildAckJson",
            "ReconcileExecutingCommand", "CaptureExecutionEvidence",
        )
        # JavaScript uses numbers for test tickets; preserve the MQL ulong output
        # reference with the same scalar accessor mapping used for int outputs.
        code = compile_functions(cls.source.replace("ulong &position_ticket", "int &position_ticket"), names)
        code = re.sub(r"\bExecutionAttempt\s+(\w+)\s*;", r"let \1 = {};", code)
        # Extra output references used by the actual recovery body.
        extra_refs = {
            "FindRecoveryOpenPosition": list(range(2, 8)),
            "FindRecoveryCurrentOrders": list(range(2, 5)),
            "FindRecoveryHistory": list(range(2, 15)),
            "FindPositionByIdentifier": [1],
        }
        for match in reversed(list(re.finditer(r"\b(" + "|".join(extra_refs) + r")\s*\(", code))):
            opening = code.index("(", match.start())
            args, closing = arguments(code, opening)
            for index in extra_refs[match.group(1)]:
                arg = args[index]
                args[index] = "{get value(){return " + arg + ";},set value(v){" + arg + "=v;}}"
            code = code[:opening + 1] + ",".join(args) + code[closing:]
        # Replace the resident harness's unrelated inert spies with actual bodies.
        cls.overrides = re.sub(r"(?m)^function (\w+)\(", r"\1 = function(", code)

    def run_js(self, body):
        prelude = r"""
let millis=100000,serverClock=5000,connected=true,tickAvailable=true;
let quote={bid:4000,ask:4000.2,time:5000};
let g_last_tick_millis=0,g_last_tick_server_time=0;
const SYMBOL_TRADE_MODE=99,SYMBOL_TRADE_MODE_DISABLED=0;
GetTickCount64=()=>millis; TimeCurrent=()=>serverClock; IsConnected=()=>connected;
MathIsValidNumber=Number.isFinite; MathMax=Math.max; MathAbs=Math.abs;
SymbolInfoInteger=()=>1;
SymbolInfoTick=(_symbol,tick)=>{Object.assign(tick,quote);return tickAvailable;};
ZeroMemory=o=>Object.keys(o).forEach(key=>delete o[key]);
Symbol=()=>_Symbol; Period=()=>_Period; iTime=()=>123;
StringFormat=(_format,value)=>String(value); LotDigits=()=>2;
StringToInteger=Number;
PositionSizingModeName=()=> 'FIXED_LOT'; RiskCapitalBaseName=()=> 'EQUITY';
EffectiveRiskPercent=()=>1;
JsonNumber=(value,digits)=>JSON.stringify(Number(Number(value).toFixed(digits)));
""" + self.overrides + r"""
function fresh(){const tick={},reason={value:''};return {ok:ReadFreshTick(tick,reason),reason:reason.value};}
function currentMarket(){return SnapshotMarketOpen(quote,tickAvailable);}
"""
        return self.harness.run_js(prelude + body)

    def test_frozen_server_clock_expires_on_monotonic_age_and_recovers_on_tick(self):
        self.run_js(r"""
assert.deepEqual(fresh(),{ok:false,reason:'QUOTE_NOT_OBSERVED'});
assert.equal(currentMarket(),false);
OnTick(); assert.equal(fresh().ok,true); assert.equal(currentMarket(),true);
millis+=30000; assert.equal(fresh().ok,true);
millis+=1; assert.equal(fresh().ok,false); assert.equal(currentMarket(),false);
millis+=89999; // All broker quotes and TimeCurrent have remained frozen for120s.
assert.equal(fresh().reason,'QUOTE_STALE_OR_FUTURE');
assert.equal(currentMarket(),false);
assert.equal(g_last_tick_millis,100000); // Reading cached prices never renews age.
serverClock++; quote.time++; OnTick();
assert.equal(fresh().ok,true); assert.equal(currentMarket(),true);
console.log(JSON.stringify({ok:true}));
""")

    def test_disconnect_reconnect_and_reinit_require_actual_new_tick(self):
        self.run_js(r"""
OnTick(); assert.equal(fresh().ok,true);
connected=false; OnTimer(); assert.equal(g_tick_observed,false);
connected=true; assert.equal(fresh().reason,'QUOTE_NOT_OBSERVED');
OnTick(); assert.equal(fresh().ok,true);
OnDeinit(5); assert.equal(g_tick_observed,false);
assert.equal(OnInit(),INIT_SUCCEEDED); assert.equal(g_init_blocked,false);
assert.equal(fresh().reason,'QUOTE_NOT_OBSERVED');
OnTick(); assert.equal(fresh().ok,true);
console.log(JSON.stringify({ok:true}));
""")

    def test_startup_waiting_feed_stays_resident_and_recovers_without_reattach(self):
        self.run_js(r"""
assert.equal(OnInit(),INIT_SUCCEEDED);
assert.equal(GatewayInitializationReady(),true); assert.equal(g_init_blocked,false);
assert.equal(g_cached_execution_guard_ready,false);
assert.equal(g_cached_execution_guard_reason,'QUOTE_NOT_OBSERVED');
const initial=JSON.parse(writes.find(w=>w.path==='snapshot').payload);
assert.equal(initial.chart.marketOpen,false);
now+=SnapshotIntervalSeconds; OnTimer();
assert.equal(g_init_blocked,false); assert.equal(g_cached_execution_guard_ready,false);
OnTick(); now++; OnTimer();
assert.equal(g_cached_execution_guard_ready,true); assert.equal(g_cached_execution_guard_reason,'READY');
assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_cached_readiness_cannot_outlive_quote_or_skip_disconnection(self):
        self.run_js(r"""
OnInit(); OnTick(); UpdateRiskTelemetry(true);
assert.equal(g_cached_execution_guard_ready,true);
millis+=31000; // UTC and server time intentionally frozen, risk-cache age stays zero.
UpdateRiskTelemetry(false);
assert.equal(g_cached_execution_guard_ready,false);
assert.equal(g_cached_execution_guard_reason,'QUOTE_STALE_OR_FUTURE');
OnTick(); UpdateRiskTelemetry(false); assert.equal(g_cached_execution_guard_ready,true);
connected=false; UpdateRiskTelemetry(false);
assert.equal(g_cached_execution_guard_ready,false); assert.equal(g_tick_observed,false);
connected=true; UpdateRiskTelemetry(false); assert.equal(g_cached_execution_guard_ready,false);
OnTick(); UpdateRiskTelemetry(false); assert.equal(g_cached_execution_guard_ready,true);
console.log(JSON.stringify({ok:true}));
""")

    def test_broker_clock_invalid_quote_and_counter_regression_still_fail_closed(self):
        self.run_js(r"""
OnTick(); serverClock=4999; assert.equal(fresh().ok,false); assert.equal(currentMarket(),false);
serverClock=5031; assert.equal(fresh().ok,false); assert.equal(currentMarket(),false);
serverClock=5000; millis=99999; assert.equal(fresh().ok,false); assert.equal(currentMarket(),false);
millis=100000; quote.bid=NaN; OnTick(); assert.equal(g_tick_observed,false);
quote.bid=4000; quote.ask=Infinity; OnTick(); assert.equal(g_tick_observed,false);
quote.ask=4000.2; tickAvailable=false; OnTick(); assert.equal(g_tick_observed,false);
tickAvailable=true; OnTick(); assert.equal(fresh().ok,true);
// 64-bit timer remains valid beyond the former32-bit wrap boundary.
millis=2**32+100000; OnTick(); millis+=30001; assert.equal(fresh().ok,false);
console.log(JSON.stringify({ok:true}));
""")

    def test_observed_postfill_ack_requires_measurable_slippage_and_never_emits_unknown_flag(self):
        self.run_js(r"""
const DEAL_TYPE_BUY=0,DEAL_TYPE_SELL=1,DEAL_ENTRY_IN=0,POSITION_TYPE_BUY=0,POSITION_TYPE_SELL=1;
const DEAL_TYPE=1,DEAL_ENTRY=2,DEAL_MAGIC=3,DEAL_POSITION_ID=4,DEAL_SYMBOL=5,DEAL_COMMENT=6,DEAL_VOLUME=7,DEAL_PRICE=8;
const POSITION_TYPE=1,POSITION_MAGIC=2,POSITION_SYMBOL=3,POSITION_COMMENT=4,POSITION_VOLUME=5,POSITION_SL=6,POSITION_TP=7;
const command={command_id:'c',idempotency_key:'i',channel_id:SnapshotChannel,mission_id:'m',
 council_decision_id:'d',owner_agent_id:'a',snapshot_id:'s',snapshot_observed_at:100,bar_time:99,
 reference_price:4000.1,action:'BUY',symbol:'XAUUSD',timeframe:'H1',signature_verification_status:'VERIFIED'};
const request={price:4000.2,volume:.01,sl:3990,tp:4020,comment:'HQ:c'},result={deal:12};
let point=.01,dealPrice=4000.42;
HistoryDealSelect=()=>true;
HistoryDealGetInteger=(_id,key)=>({[DEAL_TYPE]:DEAL_TYPE_BUY,[DEAL_ENTRY]:DEAL_ENTRY_IN,[DEAL_MAGIC]:MagicNumber,[DEAL_POSITION_ID]:13})[key];
HistoryDealGetString=(_id,key)=>key===DEAL_SYMBOL?'XAUUSD':'HQ:c';
HistoryDealGetDouble=(_id,key)=>key===DEAL_VOLUME?.01:dealPrice;
FindPositionByIdentifier=(_id,ticket)=>{ticket.value=13;return true;};
PositionGetInteger=key=>key===POSITION_TYPE?POSITION_TYPE_BUY:MagicNumber;
PositionGetString=key=>key===POSITION_SYMBOL?'XAUUSD':'HQ:c';
PositionGetDouble=key=>({[POSITION_VOLUME]:.01,[POSITION_SL]:3990,[POSITION_TP]:4020})[key];
SymbolInfoDouble=()=>point; Uppercase=s=>s.toUpperCase();
FilledRiskAssessmentCode=()=> 'WITHIN_ESTIMATE';
let ticket={value:0},reason={value:''};
ResetAckExecutionEvidence();
assert.equal(CaptureExecutionEvidence(command,request,result,ticket,reason),true);
assert.equal(ticket.value,13); assert.equal(reason.value,'ORDER_VERIFIED_OPEN');
for(const status of ['EXECUTED','EXECUTION_UNKNOWN']){
 const ack=JSON.parse(BuildAckJson(command,status,reason.value,ticket.value,0,true));
 assert.equal(ack.filledSlippageKnown,true); assert.equal(ack.filledSlippagePoints,22);
}
for(point of [0,-.01,NaN,Infinity,1e-15]){
 ResetAckExecutionEvidence();
 assert.equal(CaptureExecutionEvidence(command,request,result,ticket,reason),false);
 assert.equal(reason.value,'EXECUTION_SLIPPAGE_EVIDENCE_UNAVAILABLE');
 assert.equal(g_ack_has_execution_evidence,false);
 g_ack_verification_status='MISMATCH';g_ack_execution_state='UNKNOWN';
 const ack=JSON.parse(BuildAckJson(command,'EXECUTION_UNKNOWN',reason.value,ticket.value,0,true));
 assert.equal(Object.hasOwn(ack,'filledSlippageKnown'),false);assert.equal(ack.filledSlippagePoints,null);
}
point=.01;dealPrice=NaN;ResetAckExecutionEvidence();
assert.equal(CaptureExecutionEvidence(command,request,result,ticket,reason),false);
assert.equal(g_ack_has_execution_evidence,false);assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_recovered_open_and_closed_ack_do_not_invent_zero_slippage(self):
        self.run_js(r"""
g_runtime_initialized=true;g_channel_lock_handle=10;
const command={command_id:'c',idempotency_key:'i',channel_id:SnapshotChannel,mission_id:'m',
 council_decision_id:'d',owner_agent_id:'a',snapshot_id:'s',snapshot_observed_at:100,bar_time:99,
 reference_price:4000.1,action:'BUY',symbol:'XAUUSD',timeframe:'H1',signature_verification_status:'VERIFIED'};
let closed=false,ack=null;
ReadExecutionAttempt=(_c,_s,a)=>{Object.assign(a,{expected_volume:.01,position_sizing_mode:'FIXED_LOT',risk_percent:1,
 risk_capital_base:'EQUITY',estimated_commission_per_lot:7,risk_capital_amount:1000,estimated_risk_money:1,
 order_id:'11',deal_id:'12',broker_comment:'HQ:c'});return true;};
FindRecoveryOpenPosition=(_c,_v,count,ticket,price,sl,tp)=>{count.value=closed?0:1;ticket.value=13;price.value=4000.4;sl.value=3990;tp.value=4020;return true;};
FindRecoveryCurrentOrders=(_c,_v,count,ticket)=>{count.value=0;ticket.value=0;return true;};
FindRecoveryHistory=(_c,_v,count,ticket,sl,tp,deals,deal,position,entry,vol,exit,time,pnl)=>{
 count.value=1;ticket.value=11;sl.value=3990;tp.value=4020;deals.value=1;deal.value=12;position.value=13;
 entry.value=4000.4;vol.value=.01;exit.value=closed?.01:0;time.value=closed?1001:0;pnl.value=-.5;return true;};
FinalizeCommand=(c,status,reason,ticket,error)=>{ack=JSON.parse(BuildAckJson(c,status,reason,ticket,error,true));};
MarkRecoveryUnknown=()=>{throw Error('Unexpected unresolved recovery');};
for(closed of [false,true]){
 ResetAckExecutionEvidence(); ReconcileExecutingCommand(command,'signed');
 assert.equal(ack.status,'EXECUTED'); assert.equal(ack.reasonCode,'RECOVERED_ORDER_FOUND');
 assert.equal(ack.verificationStatus,closed?'VERIFIED_CLOSED':'VERIFIED_OPEN');
 assert.equal(ack.filledSlippageKnown,false); assert.equal(ack.filledSlippagePoints,null);
 assert.equal(ack.filledPrice,4000.4); assert.equal(ack.estimatedCommissionPerLot,7);
 assert.equal(tradeCalls,0);
}
// Known observed evidence remains numeric; nonexecution ACKs omit the newflag.
g_ack_filled_slippage_known=true; g_ack_filled_slippage_points=22;
const observed=JSON.parse(BuildAckJson(command,'EXECUTED','ORDER_VERIFIED_OPEN',13,0,true));
assert.equal(observed.filledSlippageKnown,true); assert.equal(observed.filledSlippagePoints,22);
ResetAckExecutionEvidence();
const rejected=JSON.parse(BuildAckJson(command,'REJECTED','TEST',0,0,true));
assert.equal(Object.hasOwn(rejected,'filledSlippageKnown'),false); assert.equal(rejected.filledSlippagePoints,null);
console.log(JSON.stringify({ok:true}));
""")


if __name__ == "__main__":
    unittest.main()
