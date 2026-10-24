"""Opt-in failure metadata only; all native observations are in-memory fakes."""
import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_ea_factory_visible_terminal_mt5 as fixtures

mt5 = fixtures.mt5
CODE = "mt5_tester_pane_reveal_focus_lost"


def observation():
    return {"schemaVersion": "mt5-tester-pane-failure-diagnostic-v1", "diagnosticOnly": True,
            "startInvoked": False, "testerVerified": False, "reasonCode": CODE,
            "checkpoint": "tester_pane_reveal_readback", "foregroundStable": True,
            "signedRoot": {"handle": 10101, "processId": 101,
                           "nativeRect": {"left": -32000, "top": -32000, "right": -31840, "bottom": -31972},
                           "clientRect": {"left": 0, "top": 2, "right": 0, "bottom": 0}},
            "foreground": {"handle": 20202, "exists": True, "processId": 101,
                           "nativeClass": "#32770", "rootHandle": 20202, "ownerHandle": 10101,
                           "titleCategory": "strategy_tester"}}


class TesterProbeFailureDiagnosticTests(unittest.TestCase):
    def test_only_bounded_metadata_without_authority_or_captions_is_accepted(self):
        self.assertEqual(mt5._tester_pane_failure_observation(observation(), CODE), observation())
        for mutate in (
            lambda row: row.update(startInvoked=True), lambda row: row.update(testerVerified=True),
            lambda row: row.update(reasonCode="another_failure"), lambda row: row.update(caption="private"),
            lambda row: row.update(checkpoint={}),
            lambda row: row["foreground"].update(nativeClass="private caption / path"),
            lambda row: row["foreground"].update(titleCategory="private title"),
            lambda row: row["foreground"].update(titleCategory=[]),
            lambda row: row["foreground"].update(handle=True),
            lambda row: row["signedRoot"]["clientRect"].update(left=float("inf")),
        ):
            value = observation()
            mutate(value)
            self.assertIsNone(mt5._tester_pane_failure_observation(value, CODE))

    def test_actual_runner_failure_survives_capability_only_with_exact_opt_in(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = fixtures.Mt5AdapterFixture(Path(temporary))
            fixture.source.with_suffix(".ex5").write_bytes(b"test-only compiled fixture")
            request = fixture.request("backtest_recheck", "bb03")
            fixture.adapter._powershell_runner = mt5._default_powershell_runner
            calls = []
            wrong_operation = False

            def fake_run(command, **kwargs):
                payload = json.loads(Path(command[command.index("-RequestPath") + 1]).read_text())
                calls.append(payload)
                response = Path(command[command.index("-ResponsePath") + 1])
                response.write_text(json.dumps({"schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA,
                    "ok": False, "action": "probe", "operationId": "other" if wrong_operation else payload["operationId"],
                    "reasonCode": CODE, "testerPaneFailure": observation()}), encoding="utf-8")
                return subprocess.CompletedProcess(command, 1, b"", b"")

            def capability(opt_in):
                return fixture.adapter.capability_provider(platform="mt5", stage_id="backtest_recheck",
                    terminal_binding=request["terminalBinding"], visible_operation=request["visibleOperation"],
                    resolved_target=request["resolvedTarget"], diagnostic_failure_observation=opt_in)

            with mock.patch.object(mt5.subprocess, "run", side_effect=fake_run):
                default = capability(False)
                opted_in = capability(True)
                wrong_operation = True
                wrong = capability(True)
                invalid = capability("true")
            for row in (default, opted_in, wrong, invalid):
                self.assertFalse(row["ready"])
                self.assertFalse(row["freshProcessProbe"])
            self.assertNotIn("diagnosticFailureObservation", calls[0])
            self.assertIs(calls[1]["diagnosticFailureObservation"], True)
            self.assertNotIn("testerPaneFailure", default)
            self.assertEqual(opted_in["testerPaneFailure"], observation())
            self.assertEqual(opted_in["reasonCode"], CODE)
            self.assertNotIn("testerPaneFailure", wrong)
            self.assertEqual(invalid["reasonCode"], "tester_pane_diagnostic_option_invalid")
            self.assertEqual(fixture.adapter._operation_probes, {})
            self.assertEqual(len(calls), 3)

    @unittest.skipUnless(os.name == "nt", "PowerShell AST execution is Windows only")
    def test_real_snapshot_reads_only_exact_root_and_current_foreground_with_private_caption(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = r"""
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
public static class MetafxMt5VisibleNative {
 public const uint GA_ROOT=2,GW_OWNER=4;
 public class RECT { public int Left,Top,Right,Bottom; }
 public static bool External;
 public static bool IsWindow(IntPtr h){return h==(IntPtr)1||h==(IntPtr)2;}
 public static IntPtr GetForegroundWindow(){return (IntPtr)2;}
 public static IntPtr GetAncestor(IntPtr h,uint f){return h;}
 public static IntPtr GetWindow(IntPtr h,uint f){return External?IntPtr.Zero:(IntPtr)1;}
 public static string GetWindowTextExact(IntPtr h){return External?"private document - secret-account-123":"Strategy Tester - secret-account-123";}
 public static bool GetWindowRect(IntPtr h,out RECT r){if(h!=(IntPtr)1)throw new Exception("not signed root");r=new RECT();r.Left=-32000;r.Top=-32000;r.Right=-31840;r.Bottom=-31972;return true;}
}
'@
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PS_PATH',[ref]$tokens,[ref]$errors)
if($errors.Count -gt 0){throw ($errors|Out-String)}
foreach($name in @('Read-TesterPaneFailureDiagnostic','Fail-TesterPaneReadiness')){
 $fn=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 Invoke-Expression $fn.Extent.Text
}
function Fail($Code){throw $Code}
function Get-NativeOwner($Handle){if($Handle -eq [IntPtr]1){return 101};if($Handle -eq [IntPtr]2){if([MetafxMt5VisibleNative]::External){return 999};return 101};throw 'inventory forbidden'}
function Get-NativeClass($Handle){if($Handle -ne [IntPtr]2){throw 'inventory forbidden'};return '#32770'}
function Read-TesterDiagnosticClientRect($Handle){if($Handle -ne [IntPtr]1){throw 'not signed root'};return @{left=0;top=2;right=0;bottom=0}}
$script:TerminalRootHandle=[IntPtr]1;$TerminalProcess=[pscustomobject]@{Id=101};$script:FailureCheckpoint='tester_pane_reveal_readback'
$request=[pscustomobject]@{expectedTerminalWindowHandle=1;action='probe';diagnosticFailureObservation=$true}
$rows=@()
foreach($external in @($false,$true)){
 [MetafxMt5VisibleNative]::External=$external;$script:TesterPaneFailureDiagnostic=$null;$reason='accepted'
 try{Fail-TesterPaneReadiness $request 'mt5_tester_pane_reveal_focus_lost'}catch{$reason=$_.Exception.Message}
 if($reason -cne 'mt5_tester_pane_reveal_focus_lost'){throw 'failure changed'}
 $rows += $script:TesterPaneFailureDiagnostic
}
$script:TesterPaneFailureDiagnostic=$null;$request.diagnosticFailureObservation=$false
try{Fail-TesterPaneReadiness $request 'mt5_tester_pane_reveal_focus_lost'}catch{}
if($null -ne $script:TesterPaneFailureDiagnostic){throw 'non-opted observation'}
$rows|ConvertTo-Json -Depth 10 -Compress
""".replace("PS_PATH", path)
        run = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive", "-Command", script],
                             capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn("secret-account", run.stdout)
        self.assertNotIn("private document", run.stdout)
        owned, external = json.loads(run.stdout)
        self.assertEqual(owned["foreground"]["ownerHandle"], 1)
        self.assertEqual(owned["foreground"]["titleCategory"], "strategy_tester")
        self.assertEqual(external["foreground"]["processId"], 999)
        self.assertEqual(external["foreground"]["titleCategory"], "other")
        for row in (owned, external):
            self.assertIsNotNone(mt5._tester_pane_failure_observation(row, CODE))


if __name__ == "__main__":
    unittest.main()
