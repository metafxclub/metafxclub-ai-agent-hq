"""Execute extracted MQL initialization/control flow with inert terminal APIs.

This is a syntax-limited MQL-to-JavaScript harness, not an MT5 emulator or a
compile/execution certificate. The tested branch bodies come from the MQ5 file;
terminal APIs and unrelated validation helpers are inert spies. This proves the
extracted control-flow boundaries, not broker guards. The snapshot output string
uses an explicit reference box; other terminal helper references remain spies.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5"


def function(source: str, name: str) -> tuple[str, str]:
    match = re.search(
        rf"(?ms)^(?:bool|void|int|string|double)\s+{name}\s*\((.*?)\)\s*\{{(.*?)^\}}",
        source,
    )
    if not match:
        raise AssertionError(f"Missing source function: {name}")
    return match.group(1), match.group(2)


def transpile(source: str, name: str) -> str:
    parameters, body = function(source, name)
    parameters = re.sub(r"\bconst\s+", "", parameters)
    parameters = re.sub(r"\b\w+\s+&?\s*(\w+)", r"\1", parameters)
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r"\bconst\s+", "", body)
    body = re.sub(
        r"\b(?:bool|int|double|string|uint|ulong|datetime)\s+(\w+)",
        r"let \1", body,
    )
    body = re.sub(
        r"\b(?:Mql\w+|CommandPayload|ExecutionAttempt)\s+(\w+)\s*;",
        r"let \1 = {};", body,
    )
    body = re.sub(r"\((?:int|uint|long|ulong|double|datetime)\)", "", body)
    if name == "BuildSnapshotJson":
        # Preserve this real output-reference boundary through WriteSnapshot.
        parameters = "payloadRef"
        body = re.sub(r"\bpayload\b", "payloadRef.value", body)
    elif name == "WriteSnapshot":
        body = body.replace('let payload = "";', 'let payload = {value: ""};')
        body = body.replace("WriteCommonTextAtomic(SnapshotPath(), payload)",
                            "WriteCommonTextAtomic(SnapshotPath(), payload.value)")
    return f"function {name}({parameters}) {{{body}\n}}"


class Mt5GatewayResidentInitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("Node is required for extracted MQL control-flow tests")
        names = (
            "GatewayInitializationReady", "InitializationBlockReason",
            "InitializationRecoveryHint", "InitFailure", "OnInit", "OnTimer",
            "OnDeinit", "UpdateBlockedInitDiagnostic", "RecordInitDiagnostic",
            "InvalidatePublishedRuntimeState", "UpdateChartStatus", "UpdateRiskTelemetry",
            "ProcessCommandFile", "ExecuteCommand", "ReconcileExecutingCommand",
            "ValidateRuntime", "BuildCapabilitiesJson", "BuildStatusJson",
            "WriteCapabilitiesSnapshot", "WriteStatusSnapshot", "WriteSnapshot",
            "BuildSnapshotJson", "IsSnapshotDue", "PublishSnapshotIfDue",
            "RiskCostBasisName", "EffectiveEstimatedCommissionPerLot",
            "ResetInputValidationDiagnostic", "InvalidInput", "InputInRange",
            "BuildInputValidationJson", "InputValidationMessage",
            "ValidateGatewayInputConfiguration",
        )
        cls.functions = "\n".join(transpile(cls.source, name) for name in names)
        prefix = cls.source.split("struct CommandPayload", 1)[0]
        declarations = ["const INVALID_HANDLE=-1, INIT_FAILED=1, INIT_PARAMETERS_INCORRECT=2, INIT_SUCCEEDED=0;"]
        for _, values in re.findall(r"enum\s+(\w+)\s*\{([^}]+)\}", prefix):
            for name, value in re.findall(r"(\w+)\s*=\s*(\d+)", values):
                declarations.append(f"const {name}={value};")
        for name, value in re.findall(
            r"(?m)^(?:input\s+|const\s+)?(?:string|bool|int|uint|double|ENUM_\w+)\s+(\w+)\s*=\s*([^;]+);",
            prefix,
        ):
            declarations.append(f"let {name}={value};")
        cls.declarations = "\n".join(declarations)
        calls = set(re.findall(r"\b([A-Z]\w+)\s*\(", cls.functions))
        cls.stub_names = sorted(calls - set(names))

    def run_js(self, scenario: str) -> dict:
        script = r"""
const assert = require('node:assert/strict');
const calls = [], writes = [], audits = [], deleted = [], prints = [];
let now=1000, fail='', timerWorks=true, channelSafe=true, channelBusy=false;
let comment='', ledgerReads=0, tradeCalls=0;
const FILE_COMMON=1, TIME_SECONDS=1, TIME_DATE=2;
const _Symbol='XAUUSD', _Period=16385, _Digits=2;
const SYMBOL_VOLUME_MIN=0, SYMBOL_VOLUME_MAX=1, SYMBOL_VOLUME_STEP=2, SYMBOL_VOLUME_LIMIT=3;
const SYMBOL_POINT=4, ACCOUNT_CURRENCY=5, ACCOUNT_BALANCE=6, ACCOUNT_EQUITY=7;
const ACCOUNT_MARGIN=8, ACCOUNT_MARGIN_FREE=9;
""" + self.declarations + "\n" + "\n".join(
            f"globalThis.{name} = (...args) => {{ calls.push('{name}'); return true; }};"
            for name in self.stub_names
        ) + r"""
NowUtc=()=>now;
StringLen=(s)=>s.length; StringFind=(s,v)=>s.indexOf(v);
IntegerToString=String; JsonString=JSON.stringify;
JsonBoolean=(v)=>v?'true':'false'; JsonNumber=String; DoubleToString=String;
MathIsValidNumber=Number.isFinite;
Trimmed=(s)=>s.trim(); NormalizeSigningKeyId=(s)=>s.trim();
Comment=(...args)=>{comment=args.join(''); calls.push('Comment');};
Print=(...args)=>{calls.push('Print');prints.push(args.join(''));};
ModeName=()=>GatewayMode===GATEWAY_LIVE?'live':'shadow';
AccountModeName=()=> 'live';
IsDemo=()=>false; IsHedgingAccount=()=>fail!=='account_mode';
IsSafeChannel=()=>channelSafe;
AcquireChannelLock=()=>{calls.push('AcquireChannelLock'); if(channelBusy)return false; g_channel_lock_handle=10; return true;};
ReleaseChannelLock=()=>{calls.push('ReleaseChannelLock'); g_channel_lock_handle=INVALID_HANDLE;};
AcquireLiveAccountOwnerLock=()=>{calls.push('AcquireLiveAccountOwnerLock'); if(fail==='live_account_owner_lock')return false; g_live_account_owner_handle=20; return true;};
ReleaseLiveAccountOwnerLock=()=>{calls.push('ReleaseLiveAccountOwnerLock');g_live_account_owner_handle=INVALID_HANDLE;};
AcquireAccountExecutionLock=()=>{calls.push('AcquireAccountExecutionLock');if(fail==='account_execution_lock')return false;g_account_execution_lock_handle=30;return true;};
ReleaseAccountExecutionLock=()=>{calls.push('ReleaseAccountExecutionLock');g_account_execution_lock_handle=INVALID_HANDLE;};
AcquirePortfolioPolicyLease=()=>{calls.push('AcquirePortfolioPolicyLease');if(fail==='portfolio_policy')return false;g_portfolio_policy_lease_handle=40;return true;};
ReleasePortfolioPolicyLease=()=>{calls.push('ReleasePortfolioPolicyLease');g_portfolio_policy_lease_handle=INVALID_HANDLE;};
EventKillTimer=()=>calls.push('EventKillTimer');
EventSetTimer=()=>{calls.push('EventSetTimer');return timerWorks && fail!=='timer';};
CryptoSelfTest=()=>fail!=='crypto';
ValidateConfiguredModes=()=>fail!=='inputs';
ValidateMoneyManagementConfiguration=()=>fail!=='money_management';
RefreshSigningReadiness=()=>fail!=='signing';
IsSigningKeyId=()=>true;
LiveAccountOwnerLockReady=()=>g_live_account_owner_handle!==INVALID_HANDLE;
StatusPath=()=> 'status'; CapabilitiesPath=()=> 'capabilities';
SnapshotPath=()=> 'snapshot'; InitStatusPath=()=> 'init-status';
WriteCommonTextAtomic=(path,payload)=>{writes.push({path,payload,initialized:g_runtime_initialized});return fail!==path;};
AppendAudit=(payload)=>{audits.push(payload);return true;};
FileDelete=(path)=>{deleted.push(path);return true;};
FileIsExist=()=>false;
ReadCommonText=()=>{ledgerReads++;return false;};
BuildSystemAckJson=(...args)=>JSON.stringify(args);
SymbolInfoTick=(_symbol,tick)=>{tick.bid=4000;tick.ask=4000.2;return true;};
BuildSnapshotBarsJson=()=> '[]';
ReadManagedOpenState=()=>{calls.push('ReadManagedOpenState');return fail!=='position_telemetry';};
ManagedDailyPnl=()=>fail!=='history_telemetry';
CurrentAccountDrawdownPercent=()=>fail!=='account_telemetry';
OrderSend=()=>{tradeCalls++;throw Error('Unexpected broker call');};
OrderCheck=()=>{tradeCalls++;throw Error('Unexpected broker check');};
""" + self.functions + "\n" + scenario
        completed = subprocess.run(
            [self.node, "-"], input=script, capture_output=True, text=True, timeout=20,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout.strip().splitlines()[-1])

    def test_invalid_numeric_input_reports_first_field_and_preserves_all_ranges(self) -> None:
        self.run_js(r"""
const invalid = [
 ['PollIntervalSeconds',2], ['SnapshotIntervalSeconds',1], ['SnapshotBars',1001],
 ['MaxCommandBytes',255], ['MaxCommandTtlSeconds',29], ['MaxHeartbeatTtlSeconds',29],
 ['MaxClockSkewSeconds',-1], ['MaxSpreadPoints',0], ['SlippagePoints',-1],
 ['MaxSpreadPoints',MAX_SAFE_SPREAD_POINTS+1], ['SlippagePoints',MAX_SAFE_SLIPPAGE_POINTS+1],
 ['MagicNumber',0], ['MaxSnapshotAgeSeconds',1000], ['MaxSignalDriftPoints',10001],
 ['MaxQuoteAgeSeconds',121], ['MaxManagedOpenPositions',0], ['MaxManagedTotalLots',0],
 ['FixedLot',0.2], ['MaxTradesPerBrokerDay',0], ['MaxLossPerTradePercent',0],
 ['MaxDailyLossPercent',101], ['MaxManagedWeeklyLossPercent',-1],
 ['MaxConsecutiveManagedLosses',101], ['ConsecutiveLossCooldownMinutes',10081],
 ['MaxAccountEquityDrawdownPercent',101], ['MinRewardRiskRatio',0],
 ['MinProjectedMarginLevelPercent',99],
];
for(const [field,value] of invalid){
 const saved=eval(field); eval(field+'='+value);
 assert.equal(ValidateGatewayInputConfiguration(),false,field);
 const diagnostic=JSON.parse(BuildInputValidationJson());
 assert.equal(diagnostic.field,field); assert.equal(diagnostic.value,value);
 assert.match(InputValidationMessage(),new RegExp(field));
 eval(field+'='+saved);
}
GatewayMode=GATEWAY_DEMO; RequireHeartbeat=false;
assert.equal(ValidateGatewayInputConfiguration(),false);
assert.equal(JSON.parse(BuildInputValidationJson()).constraint,'required_for_execution');
RequireHeartbeat=true; MaxSnapshotAgeSeconds=1000; MaxSignalDriftPoints=20000;
assert.equal(ValidateGatewayInputConfiguration(),false);
assert.equal(JSON.parse(BuildInputValidationJson()).field,'MaxSnapshotAgeSeconds');
MaxSnapshotAgeSeconds=900; MaxSignalDriftPoints=10000;
assert.equal(ValidateGatewayInputConfiguration(),true);
assert.equal(BuildInputValidationJson(),'null'); assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_nonfinite_input_is_reported_without_invalid_json(self) -> None:
        self.run_js(r"""
for(const value of [NaN,Infinity,-Infinity]){
 MaxDailyLossPercent=value;
 assert.equal(ValidateGatewayInputConfiguration(),false);
 const diagnostic=JSON.parse(BuildInputValidationJson());
 assert.equal(diagnostic.field,'MaxDailyLossPercent'); assert.equal(diagnostic.value,null);
 assert.equal(diagnostic.minimum,0); assert.equal(diagnostic.minimumInclusive,false);
 assert.equal(diagnostic.maximum,100);
}
console.log(JSON.stringify({ok:true}));
""")

    def test_bad_snapshot_age_is_visible_and_corrected_reinit_clears_diagnostic(self) -> None:
        self.run_js(r"""
MaxSnapshotAgeSeconds=1000;
assert.equal(OnInit(),INIT_SUCCEEDED); assert.equal(GatewayInitializationReady(),false);
assert.equal(g_init_failure_reason,'GATEWAY_INPUT_CONFIGURATION_INVALID');
const status=JSON.parse(writes.at(-1).payload);
assert.deepEqual(status.inputValidation,{field:'MaxSnapshotAgeSeconds',value:1000,
 minimum:5,maximum:900,minimumInclusive:true,maximumInclusive:true,constraint:'range'});
assert.equal(status.runtimeReady,false); assert.match(comment,/MaxSnapshotAgeSeconds=1000/);
assert.match(prints.at(-1),/MaxSnapshotAgeSeconds=1000/); assert.match(comment,/900/);
now+=6; OnTimer(); assert.equal(JSON.parse(writes.at(-1).payload).inputValidation.value,1000);
MaxSnapshotAgeSeconds=900; assert.equal(OnInit(),INIT_SUCCEEDED);
assert.equal(GatewayInitializationReady(),true);
assert.equal(JSON.parse(writes.at(-1).payload).inputValidation,null);
assert.equal(tradeCalls,0); console.log(JSON.stringify({ok:true}));
""")

    def test_ttl_inputs_require_backend_packet_compatibility_before_readiness(self) -> None:
        self.run_js(r"""
for(const field of ['MaxCommandTtlSeconds','MaxHeartbeatTtlSeconds']){
 const saved=eval(field); eval(field+'=29');
 assert.equal(OnInit(),INIT_SUCCEEDED); assert.equal(GatewayInitializationReady(),false);
 const diagnostic=JSON.parse(writes.at(-1).payload).inputValidation;
 assert.equal(diagnostic.field,field); assert.equal(diagnostic.minimum,30);
 eval(field+'=30'); assert.equal(OnInit(),INIT_SUCCEEDED);
 assert.equal(GatewayInitializationReady(),true); eval(field+'='+saved);
}
assert.equal(tradeCalls,0); console.log(JSON.stringify({ok:true}));
""")
        bridge = (ROOT / "backend/local-runner/bridge_server.py").read_text(encoding="utf-8")
        self.assertIn("command_ttl_seconds=30", bridge)
        self.assertIn("heartbeat_ttl_seconds=30", bridge)

    def test_failures_before_and_after_locks_remain_resident_without_execution(self) -> None:
        for stage in (
            "inputs", "account_mode", "crypto", "money_management", "signing",
            "live_account_owner_lock", "account_execution_lock", "portfolio_policy",
            "timer", "snapshot", "capabilities", "status",
        ):
            with self.subTest(stage=stage):
                self.run_js("fail=" + json.dumps(stage) + r""";
GatewayMode=GATEWAY_LIVE; LiveArmed=true; SingleHostLiveAcknowledged=true;
assert.equal(OnInit(),INIT_SUCCEEDED);
assert.equal(g_init_blocked,true); assert.equal(GatewayInitializationReady(),false);
assert.equal(g_init_failure_stage,fail);
assert.equal(g_channel_lock_handle,10);
assert.equal(g_live_account_owner_handle,INVALID_HANDLE);
assert.equal(g_account_execution_lock_handle,INVALID_HANDLE);
assert.equal(g_portfolio_policy_lease_handle,INVALID_HANDLE);
assert.match(comment,/ATTACHED \/ BLOCKED/);
const previousWrites=writes.length, previousAudits=audits.length;
fail=''; now+=6; OnTimer();
assert.equal(GatewayInitializationReady(),false);
assert.equal(writes.length,previousWrites+1);
assert.equal(writes.at(-1).path,'init-status');
assert.equal(audits.length,previousAudits);
assert.equal(ledgerReads,0); assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_unsafe_or_busy_channel_never_modifies_the_existing_owner_files(self) -> None:
        for setup in ("channelSafe=false", "channelBusy=true"):
            with self.subTest(setup=setup):
                self.run_js(setup + r""";
assert.equal(OnInit(),INIT_SUCCEEDED);
OnTimer(); OnDeinit(3);
assert.equal(writes.length,0); assert.equal(audits.length,0);
assert.equal(deleted.length,0); assert.equal(ledgerReads,0);
assert.equal(tradeCalls,0); assert.equal(g_runtime_initialized,false);
console.log(JSON.stringify({ok:true}));
""")

    def test_timer_failure_keeps_actionable_chart_comment_without_retry(self) -> None:
        self.run_js(r"""
fail='timer'; assert.equal(OnInit(),INIT_SUCCEEDED);
assert.equal(calls.filter(x=>x==='EventSetTimer').length,1);
assert.match(comment,/GATEWAY_TIMER_START_FAILED/);
assert.match(comment,/reapply Inputs/);
assert.match(comment,/message stays visible/);
assert.equal(g_diagnostic_timer_ready,false);
console.log(JSON.stringify({ok:true}));
""")

    def test_blocked_entry_points_preserve_ledger_ack_and_cache_reason(self) -> None:
        self.run_js(r"""
g_channel_lock_handle=10;
InitFailure(INIT_PARAMETERS_INCORRECT,'money_management','LIVE_COMMISSION_POLICY_UNCONFIRMED','blocked');
const n=writes.length;
g_runtime_initialized=true; // A stale ready bit must not override the blocked latch.
g_cached_execution_guard_ready=true; g_risk_cache_at=now+100;
ProcessCommandFile(); ExecuteCommand({},'',0.01,1000,1);
ReconcileExecutingCommand({},'');
assert.equal(ValidateRuntime({},0.01,''),false);
assert.equal(UpdateRiskTelemetry(false),false);
assert.equal(g_cached_execution_guard_ready,false);
assert.equal(g_cached_execution_guard_reason,'LIVE_COMMISSION_POLICY_UNCONFIRMED');
assert.equal(WriteSnapshot(),false); assert.equal(WriteStatusSnapshot(),false);
assert.equal(WriteCapabilitiesSnapshot(),false);
assert.equal(writes.length,n); assert.equal(ledgerReads,0); assert.equal(tradeCalls,0);
const cap=JSON.parse(BuildCapabilitiesJson());
assert.equal(cap.liveExecutionAvailable,false);
assert.equal(cap.demoExecutionAvailable,false);
assert.equal(cap.shadowValidationAvailable,false);
assert.equal(cap.signedCommandVerification,false);
assert.equal(cap.liveBlockReason,'LIVE_COMMISSION_POLICY_UNCONFIRMED');
assert.match(comment,/EstimatedCommissionPerLot/);
assert.match(comment,/CommissionFreeAccountConfirmed/);
console.log(JSON.stringify({ok:true}));
""")

    def test_diagnostic_timer_and_file_failure_still_leave_visible_block(self) -> None:
        self.run_js(r"""
g_channel_lock_handle=10; timerWorks=false; fail='init-status';
assert.equal(InitFailure(2,'money_management','LIVE_COMMISSION_POLICY_UNCONFIRMED','blocked'),INIT_SUCCEEDED);
assert.equal(g_runtime_initialized,false); assert.equal(g_diagnostic_timer_ready,false);
assert.match(comment,/LIVE_COMMISSION_POLICY_UNCONFIRMED/);
assert.match(comment,/EstimatedCommissionPerLot/);
assert.match(comment,/message stays visible/);
assert.equal(ledgerReads,0); assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_diagnostics_are_bounded_and_deinit_cleans_only_owned_publication(self) -> None:
        self.run_js(r"""
g_channel_lock_handle=10;
InitFailure(2,'money_management','LIVE_COMMISSION_POLICY_UNCONFIRMED','blocked');
let d=JSON.parse(writes.at(-1).payload);
assert.equal(d.eaAttached,true); assert.equal(d.runtimeReady,false);
assert.equal(d.returnCode,2); assert.equal(d.severity,'error');
const n=writes.length, a=audits.length;
for(let i=0;i<20;i++)OnTimer();
assert.equal(writes.length,n); assert.equal(audits.length,a);
now+=5; OnTimer(); assert.equal(writes.length,n+1); assert.equal(audits.length,a);
OnDeinit(5);
const stopped=JSON.parse(writes.at(-1).payload);
assert.equal(stopped.eaAttached,false); assert.equal(stopped.runtimeReady,false);
assert.equal(g_channel_lock_handle,INVALID_HANDLE);
const nd=deleted.length; OnDeinit(5); assert.equal(deleted.length,nd);
assert.equal(audits.length,a); assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_success_latches_only_after_initial_files_and_requires_explicit_reinit(self) -> None:
        self.run_js(r"""
fail='crypto'; OnInit(); fail='';
now+=50; OnTimer(); assert.equal(GatewayInitializationReady(),false);
OnDeinit(5); writes.length=0; deleted.length=0;
assert.equal(OnInit(),INIT_SUCCEEDED);
assert.equal(GatewayInitializationReady(),true); assert.equal(g_init_blocked,false);
for(const w of writes.filter(w=>['snapshot','status','capabilities'].includes(w.path)))
  assert.equal(w.initialized,false);
assert.equal(writes.filter(w=>w.path==='snapshot').length,1);
const snapshot=JSON.parse(writes.find(w=>w.path==='snapshot').payload);
assert.equal(snapshot.mode,'read_only'); assert.equal(snapshot.terminalPlatform,'mt5');
assert.equal(snapshot.chart.symbol,'XAUUSD');
const initialCapabilities=JSON.parse(writes.find(w=>w.path==='capabilities').payload);
assert.equal(initialCapabilities.signedCommandVerification,false);
assert.equal(initialCapabilities.liveExecutionAvailable,false);
assert.equal(initialCapabilities.demoExecutionAvailable,false);
assert.equal(initialCapabilities.shadowValidationAvailable,false);
const initialStatus=JSON.parse(writes.find(w=>w.path==='status').payload);
assert.equal(initialStatus.executionGuardReady,false);
assert.equal(initialStatus.executionGuardReason,'GATEWAY_INITIALIZATION_INCOMPLETE');
assert.equal(initialStatus.riskCostBasis,'price_and_slippage_excluding_commission');
assert.equal(initialStatus.estimatedCommissionPerLot,0);
assert.equal(initialStatus.commissionFreeAccountConfirmed,false);
const ready=JSON.parse(writes.at(-1).payload);
assert.equal(ready.runtimeReady,true); assert.equal(ready.severity,'info');
const n=writes.filter(w=>w.path==='snapshot').length;
now+=SnapshotIntervalSeconds;
OnTimer();
assert.equal(writes.filter(w=>w.path==='snapshot').length,n+1);
assert.equal(ledgerReads,1); assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_owned_startup_snapshot_reads_telemetry_without_execution_readiness(self) -> None:
        self.run_js(r"""
g_channel_lock_handle=10;
g_cached_execution_guard_ready=true;
const payload={value:''};
assert.equal(BuildSnapshotJson(payload),true);
assert.equal(JSON.parse(payload.value).mode,'read_only');
assert.equal(g_cached_history_telemetry_ready,true);
assert.equal(g_cached_execution_guard_ready,false);
assert.equal(g_cached_execution_guard_reason,'GATEWAY_INITIALIZATION_INCOMPLETE');
const reads=calls.filter(x=>x==='ReadManagedOpenState').length;
g_cached_execution_guard_ready=true;
assert.equal(BuildSnapshotJson({value:''}),true); // The cache cannot reopen execution.
assert.equal(calls.filter(x=>x==='ReadManagedOpenState').length,reads);
assert.equal(g_cached_execution_guard_ready,false);
ProcessCommandFile(); ExecuteCommand({},'',0.01,1000,1); ReconcileExecutingCommand({},'');
assert.equal(ValidateRuntime({},0.01,''),false);
assert.equal(writes.length,0); assert.equal(ledgerReads,0); assert.equal(tradeCalls,0);
g_channel_lock_handle=INVALID_HANDLE;
assert.equal(BuildSnapshotJson({value:''}),false);
assert.equal(g_cached_history_telemetry_ready,false);
assert.equal(calls.filter(x=>x==='ReadManagedOpenState').length,reads);
console.log(JSON.stringify({ok:true}));
""")

    def test_initial_snapshot_telemetry_failures_latch_block_and_clean_owned_files(self) -> None:
        for failure in ("position_telemetry", "history_telemetry", "account_telemetry"):
            with self.subTest(failure=failure):
                self.run_js("fail=" + json.dumps(failure) + r""";
assert.equal(OnInit(),INIT_SUCCEEDED);
assert.equal(g_init_blocked,true); assert.equal(GatewayInitializationReady(),false);
assert.equal(g_init_failure_stage,'snapshot');
assert.equal(g_init_failure_reason,'INITIAL_SNAPSHOT_WRITE_FAILED');
assert.equal(writes.some(w=>['snapshot','capabilities','status'].includes(w.path)),false);
assert.equal(g_cached_execution_guard_ready,false);
assert.equal(g_live_account_owner_handle,INVALID_HANDLE);
assert.equal(g_portfolio_policy_lease_handle,INVALID_HANDLE);
assert.equal(g_channel_lock_handle,10);
fail=''; now+=10; OnTimer();
assert.equal(GatewayInitializationReady(),false);
assert.equal(ledgerReads,0); assert.equal(tradeCalls,0);
console.log(JSON.stringify({ok:true}));
""")

    def test_guard_presence_and_no_timer_promotion(self) -> None:
        _, timer = function(self.source, "OnTimer")
        self.assertLess(timer.index("!GatewayInitializationReady()"), timer.index("ProcessCommandFile()"))
        self.assertNotIn("g_runtime_initialized = true", timer)
        self.assertNotIn("OnInit()", timer)
        for name in ("ProcessCommandFile", "ExecuteCommand", "ReconcileExecutingCommand", "ValidateRuntime"):
            _, body = function(self.source, name)
            self.assertTrue(body.lstrip().startswith("//") or body.lstrip().startswith("if(!GatewayInitializationReady())"))
            self.assertIn("if(!GatewayInitializationReady())", body[:230])
        _, init = function(self.source, "OnInit")
        self.assertEqual(init.count("g_runtime_initialized = true"),1)
        self.assertGreater(init.index("g_runtime_initialized = true"),init.index('"INITIAL_STATUS_WRITE_FAILED"'))
        for guard in (
            "ValidateConfiguredModes", "IsHedgingAccount", "CryptoSelfTest",
            "LiveSymbolExactAllowlistConfirmed", "ValidateMoneyManagementConfiguration",
            "ValidateManagedMagicConfiguration", "RefreshSigningReadiness",
            "AcquireLiveAccountOwnerLock", "AcquireAccountExecutionLock", "AcquirePortfolioPolicyLease",
        ):
            self.assertIn(guard,init)


if __name__ == "__main__":
    unittest.main()
