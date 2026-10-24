"""Read-only MT5 outcome control flow with inert broker/file APIs.

The function bodies are extracted from MQ5; this is not native compile proof.
No terminal, account, real signing key, or runtime file is used.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from test_mt5_risk_cost_basis_behavior import arguments, compile_functions, extract

SOURCE = Path(__file__).resolve().parents[1] / "integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5"


class Mt5ExecutedOutcomeTrackingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("Node required for extracted MQL behavior")
        cls.names = ("ReadOutcomeExecutionIdentity", "OutcomeOrderIsSettled", "BuildExecutedOutcome", "RefreshExecutedCommandOutcome")
        code = compile_functions(cls.source, cls.names)
        code = re.sub(r"\b(?:ExecutionAttempt|LegacyExecutedAck)\s+(\w+)\s*;", r"let \1 = {};", code)
        code = re.sub(r"let (\w+)\[\];", r"let \1 = [];", code)
        refs = {
            "ReadOutcomeTicket": [1], "ReadHistoryDealIntegerStrict": [2],
            "ReadHistoryDealDoubleStrict": [2], "ReadHistoryDealStringStrict": [2],
            "ReadHistoryOrderIntegerStrict": [2], "ReadHistoryOrderDoubleStrict": [2],
            "ReadHistoryOrderStringStrict": [2], "ReadSelectedPositionIntegerStrict": [1],
            "ReadSelectedPositionDoubleStrict": [1], "ReadSelectedPositionStringStrict": [1],
            "ReadCommonText": [2], "ReadRequiredString": [4, 5],
            "ReadRequiredDouble": [4, 5], "ReadRequiredInteger": [4, 5],
            "ReadRequiredBoolean": [4, 5], "ReverifyCommandEnvelope": [2],
            "ReadExecutionAttempt": [3],
        }
        for match in reversed(list(re.finditer(r"\b(" + "|".join(refs) + r")\s*\(", code))):
            opening = code.index("(", match.start())
            args, closing = arguments(code, opening)
            for index in refs[match.group(1)]:
                arg = args[index]
                args[index] = "{get value(){return " + arg + ";},set value(v){" + arg + "=v;}}"
            code = code[:opening + 1] + ",".join(args) + code[closing:]
        cls.code = code

    def run_js(self, scenario):
        script = r"""
const assert=require('node:assert/strict');
const FILE_COMMON=1,_Digits=2,_Symbol='XAUUSD',_Period=16385,MaxCommandBytes=8192;
const SnapshotChannel='mtc-test',MagicNumber=4186001,ACK_SCHEMA='metafx-hq-mt4-ack-v3';
const ORDER_TYPE_BUY=0,ORDER_TYPE_SELL=1,DEAL_TYPE_BUY=0,DEAL_TYPE_SELL=1;
const POSITION_TYPE_BUY=0,POSITION_TYPE_SELL=1,DEAL_ENTRY_IN=0,DEAL_ENTRY_OUT=1,DEAL_ENTRY_OUT_BY=3;
const SYMBOL_POINT='point';
const DEAL_POSITION_ID='position',DEAL_ORDER='order',DEAL_ENTRY='entry',DEAL_TYPE='type',DEAL_MAGIC='magic';
const DEAL_TIME='time',DEAL_SYMBOL='symbol',DEAL_COMMENT='comment',DEAL_VOLUME='volume',DEAL_PRICE='price';
const DEAL_PROFIT='profit',DEAL_SWAP='swap',DEAL_COMMISSION='commission',DEAL_FEE='fee';
const ORDER_MAGIC='magic',ORDER_TYPE='type',ORDER_POSITION_ID='position',ORDER_SYMBOL='symbol';
const ORDER_COMMENT='comment',ORDER_VOLUME_INITIAL='volume',ORDER_SL='sl',ORDER_TP='tp';
const POSITION_IDENTIFIER='position',POSITION_MAGIC='magic',POSITION_TYPE='type',POSITION_SYMBOL='symbol';
const POSITION_COMMENT='comment',POSITION_VOLUME='volume',POSITION_PRICE_OPEN='price',POSITION_SL='sl',POSITION_TP='tp';
const command={command_id:'cmd-43988dc026e7d81bcfde6957',idempotency_key:'idem-test',channel_id:SnapshotChannel,
 symbol:_Symbol,action:'SELL',timeframe:'H1',stop_loss:4145.76,take_profit:4113.17};
const ticket=500029817749,orderId=ticket,dealId=600029817749;
const attempt={order_id:String(orderId),deal_id:String(dealId),broker_comment:'HQ:'+command.command_id,
 expected_volume:.01,account_binding_id:'account-a',stream_key:'stream-a',signed_command_digest:'digest-a'};
const ack={schemaVersion:ACK_SCHEMA,commandId:command.command_id,idempotencyKey:command.idempotency_key,
 channelId:SnapshotChannel,status:'EXECUTED',verificationStatus:'VERIFIED_OPEN',signatureVerificationStatus:'VERIFIED',
 statePersisted:true,symbol:_Symbol,action:'SELL',actualComment:attempt.broker_comment,actualMagicNumber:MagicNumber,
 ticket,fixedLot:.01,filledPrice:4129.67,actualStopLoss:4145.76,actualTakeProfit:4113.17};
const order={magic:MagicNumber,type:ORDER_TYPE_SELL,position:ticket,symbol:_Symbol,
 comment:attempt.broker_comment,volume:.01,sl:4145.76,tp:4113.17};
function entry(id=dealId,volume=.01){return {id,position:ticket,order:orderId,entry:DEAL_ENTRY_IN,type:DEAL_TYPE_SELL,
 magic:MagicNumber,time:1792623701,symbol:_Symbol,comment:attempt.broker_comment,volume,price:4129.67,
 profit:0,swap:0,commission:0,fee:0};}
function exit(id=dealId+1,volume=.01){return {id,position:ticket,order:orderId+1,entry:DEAL_ENTRY_OUT,type:DEAL_TYPE_BUY,
 magic:MagicNumber,time:1792630801,symbol:_Symbol,comment:'[tp]',volume,price:4113.13,
 profit:16.54,swap:0,commission:0,fee:0};}
function open(volume=.01){return {ticket,position:ticket,magic:MagicNumber,type:POSITION_TYPE_SELL,symbol:_Symbol,
 comment:attempt.broker_comment,volume,price:4129.67,sl:4145.76,tp:4113.17};}
let deals=[entry(),exit()],positions=[],selected=null,ready=true,connected=true,signature=true,bound=true;
let telemetry=true,activeOrder=false,positionHistory=true,archiveWritable=true;
let historyReads=0;
const files=new Map(),writes=[];
const CommandLedgerPath=id=>'ledger/'+id,IdempotencyLedgerPath=id=>'idempotency/'+id;
const OutcomeCommandPath=id=>'archive/'+id,OutcomePath=id=>'outcome/'+id;
function storeAck(){const raw=JSON.stringify(ack);files.set(CommandLedgerPath(command.command_id),raw);
 files.set(IdempotencyLedgerPath(command.idempotency_key),raw);}
storeAck();
function ReadCommonText(path,max,out){if(!files.has(path))return false;out.value=files.get(path);return true;}
function WriteCommonTextAtomic(path,value){if(path.startsWith('archive/')&&!archiveWritable)return false;
 files.set(path,value);writes.push(path);return true;}
function ParseFlatJson(raw,keys,values,quoted){const obj=JSON.parse(raw);for(const [k,v] of Object.entries(obj)){
 keys.push(k);values.push(v);quoted.push(typeof v==='string'?1:0);}return true;}
const FindKey=(keys,key)=>keys.indexOf(key);
function required(keys,values,quoted,key,out,type){const i=keys.indexOf(key);if(i<0||typeof values[i]!==type)return false;
 out.value=values[i];return true;}
const ReadRequiredString=(k,v,q,key,out)=>required(k,v,q,key,out,'string');
const ReadRequiredDouble=(k,v,q,key,out)=>required(k,v,q,key,out,'number');
const ReadRequiredInteger=(k,v,q,key,out)=>required(k,v,q,key,out,'number');
const ReadRequiredBoolean=(k,v,q,key,out)=>required(k,v,q,key,out,'boolean');
function ReadOutcomeTicket(value,out){const n=Number(value);out.value=n;return n>0&&Number.isSafeInteger(n);}
const MathIsValidNumber=Number.isFinite,MathAbs=Math.abs,MathMax=Math.max;
const SymbolInfoDouble=()=>.01,NormalizeSymbolPrice=x=>x,Trimmed=x=>x.trim(),Uppercase=x=>x.toUpperCase();
const GatewayInitializationReady=()=>ready,IsConnected=()=>connected,TimeframeToPeriod=()=>_Period;
const ReverifyCommandEnvelope=()=>signature;
function ReadExecutionAttempt(c,raw,out){if(!bound)return false;Object.assign(out,attempt);return true;}
const HistoryDealSelect=id=>telemetry&&deals.some(d=>d.id===id);
const HistoryOrderSelect=id=>telemetry&&id===orderId;
const OrdersTotal=()=>activeOrder?1:0,OrderGetTicket=()=>orderId;
const HistorySelectByPosition=id=>{historyReads++;return positionHistory&&id===ticket;},HistoryDealsTotal=()=>deals.length;
const HistoryDealGetTicket=i=>deals[i].id;
function read(row,key,out){if(!telemetry||!row||!(key in row))return false;out.value=row[key];return true;}
const ReadHistoryDealIntegerStrict=(id,key,out)=>read(deals.find(d=>d.id===id),key,out);
const ReadHistoryDealDoubleStrict=ReadHistoryDealIntegerStrict,ReadHistoryDealStringStrict=ReadHistoryDealIntegerStrict;
const ReadHistoryOrderIntegerStrict=(id,key,out)=>read(id===orderId?order:null,key,out);
const ReadHistoryOrderDoubleStrict=ReadHistoryOrderIntegerStrict,ReadHistoryOrderStringStrict=ReadHistoryOrderIntegerStrict;
const PositionsTotal=()=>positions.length,PositionGetTicket=i=>{selected=positions[i];return selected.ticket;};
const ReadSelectedPositionIntegerStrict=(key,out)=>read(selected,key,out);
const ReadSelectedPositionDoubleStrict=ReadSelectedPositionIntegerStrict,ReadSelectedPositionStringStrict=ReadSelectedPositionIntegerStrict;
const JsonString=JSON.stringify,JsonNumber=(n,p)=>Number(n).toFixed(p),IntegerToString=String,StringFormat=(f,n)=>String(n);
const NowUtc=()=>1792630900;
const closedCache=new Map();
const CompletedOutcomeCached=(key,payload)=>closedCache.get(key)===payload;
const RememberCompletedOutcome=(key,payload)=>closedCache.set(key,payload);
const StringFind=(value,part)=>value.indexOf(part);
function Sha256TextHex(value,out){out.value=value;return true;}
""" + self.code + r"""
function refresh(){RefreshExecutedCommandOutcome(command,'signed-command');
 return files.has(OutcomePath(command.command_id))?JSON.parse(files.get(OutcomePath(command.command_id))):null;}
""" + scenario + "\nconsole.log(JSON.stringify({ok:true}));"
        result = subprocess.run([self.node, "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_existing_executed_closed_ticket_and_stable_writes_preserve_ack(self):
        self.run_js(r"""
const before=files.get(CommandLedgerPath(command.command_id));
const outcome=refresh();assert.equal(outcome.ticket,500029817749);assert.equal(outcome.executionState,'CLOSED');
assert.equal(outcome.closePrice,4113.13);assert.equal(outcome.closedPnl,16.54);assert.equal(outcome.grossProfit,16.54);
assert.equal(outcome.commission,0);assert.equal(outcome.swap,0);assert.equal(outcome.fee,0);
assert.equal(files.get(CommandLedgerPath(command.command_id)),before);
assert.equal(files.get(IdempotencyLedgerPath(command.idempotency_key)),before);
const n=writes.length;refresh();assert.equal(writes.length,n);
assert.equal(historyReads,1); // Cached broker-verified CLOSED skips repeated history scans.
assert.deepEqual(writes,['archive/'+command.command_id,'outcome/'+command.command_id]);
""")

    def test_closed_cache_revalidates_after_ack_outcome_or_account_evidence_changes(self):
        self.run_js(r"""
refresh();assert.equal(historyReads,1);
files.set(OutcomePath(command.command_id),'{}');refresh();assert.equal(historyReads,2);
ack.filledPrice=4129.68;storeAck();files.delete(OutcomePath(command.command_id));
assert.equal(refresh(),null);assert.equal(historyReads,3);
ack.filledPrice=4129.67;storeAck();attempt.account_binding_id='account-b';
refresh();assert.equal(historyReads,4);
""")

    def test_open_and_partial_close_require_matching_remaining_position(self):
        self.run_js(r"""
deals=[entry()];positions=[open()];let outcome=refresh();assert.equal(outcome.executionState,'OPEN');
for(const key of ['closedAt','closedPnl','closePrice','grossProfit','commission','swap','fee'])assert.equal(outcome[key],null);
deals.push(exit(dealId+1,.004));positions=[open(.006)];outcome=refresh();assert.equal(outcome.executionState,'OPEN');
assert.equal(outcome.lots,.01);files.delete(OutcomePath(command.command_id));positions=[];
assert.equal(refresh(),null); // A missing partial remainder never becomes CLOSED.
""")

    def test_split_fills_multiple_exits_and_all_realized_costs(self):
        self.run_js(r"""
deals=[entry(dealId,.004),entry(dealId+1,.006),exit(dealId+2,.003),exit(dealId+3,.007)];
deals[0].commission=-.2;deals[1].commission=-.3;deals[2].price=4113;deals[3].price=4114;
deals[2].profit=5;deals[3].profit=10;deals[3].swap=-.4;deals[2].fee=-.1;deals[3].fee=-.2;
deals[2].magic=0;deals[2].comment='manual close'; // Same exact position, never unrelated manual trades.
const o=refresh();assert.equal(o.executionState,'CLOSED');assert.equal(o.closePrice,4113.7);
assert.equal(o.grossProfit,15);assert.equal(o.commission,-.5);assert.equal(o.swap,-.4);assert.equal(o.fee,-.3);
assert.equal(o.closedPnl,13.8);
""")

    def test_foreign_entry_order_position_or_symbol_fails_closed(self):
        self.run_js(r"""
for(const [field,value] of [['order',orderId+99],['position',ticket+99],['symbol','EURUSD'],
 ['comment','HQ:another-command'],['magic',0],['type',DEAL_TYPE_BUY]]){
 deals=[entry(),exit()];deals[0][field]=value;assert.equal(refresh(),null,field);
}
deals=[entry(),exit()];deals[1].position=ticket+1;assert.equal(refresh(),null);
deals=[entry(),exit(),entry(dealId+4,.01)];assert.equal(refresh(),null);
""")

    def test_unavailable_ambiguous_and_malformed_history_never_infers_closed(self):
        self.run_js(r"""
for(const mode of ['unavailable','incomplete','overclose','invalid-fee','missing-entry','wrong-exit','active-order','position-history']){
 deals=[entry(),exit()];telemetry=true;activeOrder=false;positionHistory=true;
 if(mode==='unavailable')telemetry=false;if(mode==='incomplete')deals[1].volume=.005;
 if(mode==='overclose')deals[1].volume=.02;if(mode==='invalid-fee')deals[1].fee=NaN;
 if(mode==='missing-entry')deals.shift();if(mode==='wrong-exit')deals[1].type=DEAL_TYPE_SELL;
 if(mode==='active-order')activeOrder=true;if(mode==='position-history')positionHistory=false;
 assert.equal(refresh(),null,mode);
}
""")

    def test_signing_account_stream_and_durable_identity_gate_all_writes(self):
        self.run_js(r"""
for(const gate of ['init','connection','signature','account-stream-digest']){
 ready=connected=signature=bound=true;if(gate==='init')ready=false;if(gate==='connection')connected=false;
 if(gate==='signature')signature=false;if(gate==='account-stream-digest')bound=false;
 assert.equal(refresh(),null);assert.equal(writes.length,0);
}
ready=connected=signature=bound=true;
for(const [key,value] of [['channelId','other'],['commandId','other'],['idempotencyKey','other'],
 ['status','EXECUTION_UNKNOWN'],['statePersisted',false],['ticket',500029817748],['fixedLot',.02],['actualMagicNumber',1]]){
 const prior=ack[key];ack[key]=value;storeAck();assert.equal(refresh(),null,key);ack[key]=prior;storeAck();
}
""")

    def test_outcome_path_has_no_execution_mutations_or_guard_bypass(self):
        for name in self.names + ("RefreshManagedOutcomeFiles",):
            _, body = extract(self.source, name)
            for forbidden in ("OrderSend(", "ExecuteCommand(", "ReconcileExecutingCommand(",
                              "FinalizeCommand(", "WriteExecutionMarkers(", "WriteExecutionAttempt(",
                              "WriteLastOrderBar(", "ResolveOrderVolume("):
                self.assertNotIn(forbidden, body, name)
        _, process = extract(self.source, "ProcessCommandFile")
        self.assertIn('if(processed_status == "EXECUTED")', process)
        self.assertIn("RefreshExecutedCommandOutcome(command, signed_raw)", process)
        self.assertEqual(len(re.findall(
            r"ReconcileExecutingCommand\(command, signed_raw\);\s*"
            r"RefreshExecutedCommandOutcome\(command, signed_raw\);\s*return;", process)), 3)
        _, timer = extract(self.source, "OnTimer")
        self.assertIn("RefreshManagedOutcomeFiles(false)", timer)
        _, scan = extract(self.source, "RefreshManagedOutcomeFiles")
        self.assertIn("ParseCommand(raw, command, reason)", scan)
        self.assertIn('filename == command.command_id + ".json"', scan)
        self.assertIn("scanned < 8", scan)
        self.assertIn("ReleaseOutcomeSearch()", scan)
        _, release = extract(self.source, "ReleaseOutcomeSearch")
        self.assertIn("FileFindClose(g_outcome_search_handle)", release)

    def test_native_unsigned_ticket_parser_rejects_overflow_and_noncanonical_values(self):
        # BigInt preserves the MQ5 ulong arithmetic and division semantics.
        code = compile_functions(self.source.replace("ulong &ticket", "int &ticket"), ("ReadOutcomeTicket",))
        code = code.replace("ticket.value = 0;", "ticket.value = 0n;")
        code = code.replace("let maximum = -1;", "let maximum = 18446744073709551615n;")
        code = code.replace("let digit = (StringGetCharacter(value, index) - '0');",
                            "let digit = BigInt(StringGetCharacter(value, index) - 48);")
        code = code.replace("maximum / 10", "maximum / 10n").replace("maximum % 10", "maximum % 10n")
        code = code.replace("ticket.value * 10", "ticket.value * 10n")
        script = r"""
const assert=require('node:assert/strict');
const IsUnsignedIntegerText=v=>/^[0-9]+$/.test(v),StringLen=v=>v.length;
const StringGetCharacter=(s,i)=>s.charCodeAt(i),StringFormat=(f,v)=>String(v);
""" + code + r"""
for(const text of ['1','2147483648','500029817749','9223372036854775807','18446744073709551615']){
 const out={value:0n};assert.equal(ReadOutcomeTicket(text,out),true,text);assert.equal(String(out.value),text);
}
for(const text of ['0','01','-1','1.0','1e3','18446744073709551616','999999999999999999999']){
 assert.equal(ReadOutcomeTicket(text,{value:0n}),false,text);
}
"""
        result = subprocess.run([self.node, "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_archive_scan_is_bounded_resumable_and_closes_enumeration(self):
        code = compile_functions(self.source, ("RefreshManagedOutcomeFiles", "ReleaseOutcomeSearch"))
        code = re.sub(r"\bCommandPayload\s+(\w+)\s*;", r"let \1 = {};", code)
        refs = {"FileFindFirst": [1], "FileFindNext": [1], "ReadCommonText": [2], "ParseCommand": [2]}
        for match in reversed(list(re.finditer(r"\b(" + "|".join(refs) + r")\s*\(", code))):
            opening = code.index("(", match.start())
            args, closing = arguments(code, opening)
            for index in refs[match.group(1)]:
                arg = args[index]
                args[index] = "{get value(){return " + arg + ";},set value(v){" + arg + "=v;}}"
            code = code[:opening + 1] + ",".join(args) + code[closing:]
        script = r"""
const assert=require('node:assert/strict');
const INVALID_HANDLE=-1,FILE_COMMON=1,MaxCommandBytes=8192;
let g_outcome_search_handle=INVALID_HANDLE,g_outcome_search_filename='',g_last_outcome_refresh_at=0;
let ready=true,now=1000,index=0,closed=0,refreshed=[];
const GatewayInitializationReady=()=>ready,NowUtc=()=>now,BasePath=()=> 'base';
const files=Array.from({length:20},(_,i)=>'cmd-'+i+'.json');
function FileFindFirst(pattern,name){index=0;name.value=files[index];return 42;}
function FileFindNext(handle,name){index++;if(index>=files.length)return false;name.value=files[index];return true;}
const FileFindClose=handle=>{assert.equal(handle,42);closed++;};
function ReadCommonText(path,max,out){out.value=path.split('\\').at(-1);return true;}
function ParseCommand(raw,command){command.command_id=raw.slice(0,-5);return true;}
const RefreshExecutedCommandOutcome=(command,raw)=>refreshed.push(command.command_id);
""" + code + r"""
RefreshManagedOutcomeFiles(false);assert.equal(refreshed.length,8);assert.equal(closed,0);
now++;RefreshManagedOutcomeFiles(false);assert.equal(refreshed.length,8);
now+=5;RefreshManagedOutcomeFiles(false);assert.equal(refreshed.length,16);
now+=5;RefreshManagedOutcomeFiles(false);assert.equal(refreshed.length,20);assert.equal(closed,1);
assert.equal(g_outcome_search_handle,INVALID_HANDLE);assert.equal(new Set(refreshed).size,20);
ready=false;now+=5;RefreshManagedOutcomeFiles(false);assert.equal(refreshed.length,20);
"""
        result = subprocess.run([self.node, "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
