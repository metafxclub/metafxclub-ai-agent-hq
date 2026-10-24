from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_ea_factory_visible_terminal_mt5 as fixtures

mt5 = fixtures.mt5


class TesterDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mt5-tester-diagnostic-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(strict=True)
        self.fixture = fixtures.Mt5AdapterFixture(self.root)
        compile_request = self.fixture.request("compile_validate", "aa01")
        self.compile_operation = compile_request["visibleOperation"]["operationId"]
        # The normal handler creates the real receipt contract using only this
        # test's fake transport; no MetaTrader process is ever accessed.
        self.fixture.capability(compile_request)
        self.fixture.adapter.compile_handler(request=compile_request)
        self.request = self.fixture.request("backtest_recheck", "bb02")
        self.request["visibleOperation"].update(state="uncertain", requiresExplicitResume=True)
        self.operation = self.request["visibleOperation"]["operationId"]
        self.receipt_path = self.fixture.workspace / "Summaries" / f"{self.compile_operation}-compile-receipt.json"
        self.actions = []
        self.patch = {}
        self.mutate = False

        def runner(payload, **kwargs):
            self.actions.append(payload["action"])
            self.assertLessEqual(kwargs["timeout_seconds"], 30)
            if payload["action"] == "probe":
                self.assertEqual(payload["stageId"], "compile_validate")
                self.assertEqual(payload["requiredAutomationIds"], {})
                return self.fixture.runner.probe(payload)
            self.assertEqual(payload["action"], "diagnose_tester")
            self.assertEqual(payload["expectedTerminalProcessId"], 101)
            self.assertEqual(payload["expectedTerminalWindowHandle"], 10101)
            self.assertEqual(payload["requiredAutomationIds"], mt5.BACKTEST_TESTER_AUTOMATION_IDS)
            if self.mutate:
                self.fixture.source.with_suffix(".ex5").write_bytes(b"changed")
            capture = {}
            if "diagnosticScreenshotPath" in payload:
                self.assertTrue(payload["allowDiagnosticFocusChange"])
                Path(payload["diagnosticScreenshotPath"]).write_bytes(fixtures.png_bytes())
                capture = {"diagnosticScreenshotCaptured": True, "focusMayHaveChanged": True}
            return {"schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA, "ok": True,
                    "action": "diagnose_tester", "operationId": self.operation,
                    "diagnosticOnly": True, "startInvoked": False, "testerVerified": False,
                    "sourceDigest": payload["expectedSourceDigest"],
                    "compiledBinarySha256": payload["expectedBinaryDigest"],
                    "terminalProcessId": 101, "terminalWindowHandle": 10101,
                    "observation": {"startState": "Start", "selectedTab": "Settings"}, **capture, **self.patch}

        self.fixture.adapter._powershell_runner = runner

    def invoke(self):
        return self.fixture.adapter.tester_diagnostic(
            request=self.request, compile_operation_id=self.compile_operation)

    def snapshot(self):
        return {str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.root.rglob("*") if path.is_file()}

    def test_diagnostic_observes_exact_operation_without_evidence_or_state_mutation(self):
        before = self.snapshot()
        request_before = copy.deepcopy(self.request)
        cache_before = copy.deepcopy(self.fixture.adapter._operation_probes)
        result = self.invoke()
        self.assertEqual(self.actions, ["probe", "diagnose_tester"])
        self.assertFalse(result["startInvoked"])
        self.assertFalse(result["testerVerified"])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(request_before, self.request)
        self.assertEqual(cache_before, self.fixture.adapter._operation_probes)

    def test_only_uncertain_backtest_diagnostic_exception_is_allowed(self):
        for patch in ({"state": "reserved", "requiresExplicitResume": False},
                      {"state": "completed"}, {"stageId": "optimize"}):
            original = copy.deepcopy(self.request["visibleOperation"])
            self.request["visibleOperation"].update(patch)
            with self.assertRaises(mt5.VisibleTerminalAdapterError):
                self.invoke()
            self.request["visibleOperation"] = original
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "visible_request_safety_invalid"):
            self.fixture.adapter.backtest_handler(request=self.request)
        self.assertEqual(self.actions, [])

    def test_receipt_source_binary_binding_and_evidence_drift_fail_before_native(self):
        original = self.receipt_path.read_bytes()
        for field, value in (("sourceDigest", "b" * 64), ("compiledBinarySha256", "b" * 64),
                             ("terminalCandidateId", "other"), ("zeroErrors", False),
                             ("compileLogSha256", "c" * 64), ("visibleWindowSha256", "d" * 64),
                             ("operationId", self.operation)):
            row = json.loads(original)
            row[field] = value
            self.receipt_path.write_text(json.dumps(row), encoding="utf-8")
            with self.subTest(field=field), self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError, "visible_receipt_evidence_mismatch"):
                self.invoke()
        self.receipt_path.write_bytes(original)
        row = json.loads(original)
        row["processBinding"]["terminalSelectionRevision"] = 2
        self.receipt_path.write_text(json.dumps(row), encoding="utf-8")
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "visible_receipt_evidence_mismatch"):
            self.invoke()
        self.assertEqual(self.actions, [])

    def test_compile_operation_and_intent_must_match_exact_terminal_selection(self):
        for operation in ("../escape", self.operation, "ea-visible-" + "c" * 24):
            with self.assertRaises(mt5.VisibleTerminalAdapterError):
                self.fixture.adapter.tester_diagnostic(request=self.request, compile_operation_id=operation)
        intent = self.receipt_path.with_name(f"{self.compile_operation}-compile-intent.json")
        row = json.loads(intent.read_text())
        row["terminalBindingDigest"] = "d" * 64
        intent.write_text(json.dumps(row), encoding="utf-8")
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "visible_action_intent_mismatch"):
            self.invoke()
        self.assertEqual(self.actions, [])

    def test_observation_cannot_claim_execution_or_change_identity(self):
        for patch in ({"startInvoked": True}, {"testerVerified": True}, {"diagnosticOnly": False},
                      {"operationId": self.compile_operation}, {"terminalProcessId": True},
                      {"terminalWindowHandle": 99}, {"sourceDigest": "c" * 64},
                      {"compiledBinarySha256": "d" * 64}, {"receipt": {}},
                      {"observation": {"text": "x" * 25000}}):
            self.patch = patch
            with self.subTest(field=next(iter(patch))), self.assertRaisesRegex(
                    mt5.VisibleTerminalAdapterError, "tester_diagnostic_result_invalid"):
                self.invoke()

    def test_concurrent_artifact_change_rejected_without_repair(self):
        self.mutate = True
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "tester_diagnostic_artifact_changed"):
            self.invoke()
        self.assertEqual(self.fixture.source.with_suffix(".ex5").read_bytes(), b"changed")

    def test_optional_capture_is_exclusive_task_output_never_stage_evidence(self):
        outputs = self.root / "outputs"
        outputs.mkdir()
        output = outputs / "diagnostic.png"
        before = self.snapshot()
        result = self.fixture.adapter.tester_diagnostic(request=self.request,
            compile_operation_id=self.compile_operation, diagnostic_screenshot_path=output,
            allow_focus_change=True)
        self.assertEqual(output.read_bytes(), fixtures.png_bytes())
        after = self.snapshot()
        after.pop(str(output.relative_to(self.root)))
        self.assertEqual(before, after)
        self.assertTrue(result["focusMayHaveChanged"])
        self.assertTrue(result["diagnosticScreenshot"]["notStageEvidence"])
        self.assertNotIn("artifactSpecifications", result)
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "tester_diagnostic_output_invalid"):
            self.fixture.adapter.tester_diagnostic(request=self.request,
                compile_operation_id=self.compile_operation, diagnostic_screenshot_path=output,
                allow_focus_change=True)

    def test_capture_requires_explicit_focus_permission_and_safe_output(self):
        outputs = self.root / "outputs"
        outputs.mkdir()
        unsafe = self.fixture.workspace / "outputs"
        unsafe.mkdir()
        for output, allow in ((outputs / "view.png", False), (outputs / "view.txt", True),
                              (unsafe / "view.png", True), (None, True)):
            with self.subTest(output=output), self.assertRaises(mt5.VisibleTerminalAdapterError):
                self.fixture.adapter.tester_diagnostic(request=self.request,
                    compile_operation_id=self.compile_operation, diagnostic_screenshot_path=output,
                    allow_focus_change=allow)
        self.assertEqual(self.actions, [])

    @unittest.skipUnless(os.name == "nt", "PowerShell AST is Windows only")
    def test_real_native_control_reader_handles_missing_and_non_native_controls(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
$fn=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Read-TesterDiagnosticControl'}},$true)
Invoke-Expression $fn.Extent.Text
function Fail($code) {{ throw $code }}
$script:rows=@()
function Get-All($Root,$Condition) {{
 if ($Condition -isnot [System.Windows.Automation.PropertyCondition] -or $Condition.Value -cne '10490') {{ throw 'invalid actual condition' }}
 return @($script:rows)
}}
$missing=Read-TesterDiagnosticControl 'fakeRoot' '10490' 'visualMode'
if ($missing.matchCount -ne 0 -or $missing.controls.Count -ne 0) {{ throw 'missing is not an observation' }}
$script:rows=@([pscustomobject]@{{Current=@{{NativeWindowHandle=0;IsOffscreen=$true;IsEnabled=$false}}}})
$nonNative=Read-TesterDiagnosticControl 'fakeRoot' '10490' 'visualMode'
if ($nonNative.matchCount -ne 1 -or $nonNative.controls[0].exists -ne $false -or
    $nonNative.controls[0].enabled -ne $false -or $nonNative.controls[0].offscreen -ne $true) {{ throw 'partial state lost' }}
'PASS'
"""
        completed = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "PASS")

    @unittest.skipUnless(os.name == "nt", "PowerShell AST is Windows only")
    def test_native_reader_observes_partial_controls_and_rejects_tab_drift(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
public static class MetafxMt5TabNative {{
 public static int Calls; public static bool Drift;
 public static string[] GetNames(System.IntPtr h) {{ return new[] {{ "Overview", "Settings", "Inputs" }}; }}
 public static int GetSelectedIndex(System.IntPtr h) {{ Calls++; return Drift && Calls>1 ? 2 : 1; }}
}}
'@
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
$fn=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Read-TesterDiagnostic'}},$true)
Invoke-Expression $fn.Extent.Text
function Fail($code) {{ throw $code }}
$script:TerminalRootHandle=[IntPtr]10101
$TerminalProcess=[pscustomobject]@{{Id=101}}
$ResultSchema='ea-factory-visible-mt5-powershell-result-v1'
$script:minimalCalls=0
function Get-BoundTerminalRoot($Request,$Root) {{ return 'fakeRoot' }}
function Get-MinimalBoundTesterControlSet($Request,$Root,$AllowReveal) {{
 if ($AllowReveal -ne $false -or $Root -ne [IntPtr]10101) {{ throw 'mutation or wrong root' }}
 $script:minimalCalls++
 return @{{root='fakeRoot';controls=@{{start='fakeStart';tabs=[pscustomobject]@{{Current=@{{NativeWindowHandle=20202}}}}}}}}
}}
function Assert-NativeControl($Control,$Class,$Code) {{ return [IntPtr]30303 }}
function Read-TesterStartState($Control,$Code,$Expected) {{ if ($Expected -ne [IntPtr]30303) {{throw 'wrong start'}}; return 'Start' }}
function Read-TesterDiagnosticControl($Root,$Id,$Kind) {{
 if ($Kind -eq 'visualMode') {{ return @{{matchCount=0;controls=@()}} }}
 return @{{matchCount=1;controls=@(@{{enabled=$false;dropdownOpen=$null}})}}
}}
function Read-TesterDiagnosticCheckboxes($Root,$Id) {{ return @{{matchCount=0;controls=@()}} }}
function Read-TesterDiagnosticGeometry($Bound,$Request) {{ return @{{rootClient=@{{left=0;top=0;right=1920;bottom=1080}};controls=@{{}}}} }}
function Read-TesterDiagnosticNavigation($Root,$Request) {{ return @{{viewMenu=@{{available=$false}}}} }}
$request=[pscustomobject]@{{stageId='backtest_recheck'; operationId='ea-visible-00000000000000000000bb02';expectedSourceDigest=('a'*64);expectedBinaryDigest=('b'*64);requiredAutomationIds=@{{optimization='10487';visualMode='10490';expert='10485'}}}}
$ok=Read-TesterDiagnostic $request
if ($ok.startInvoked -ne $false -or $ok.testerVerified -ne $false -or
    $ok.observation.selectedTab -cne 'Settings' -or $ok.observation.visualMode.matchCount -ne 0 -or
    $script:minimalCalls -ne 2) {{ throw 'read-only partial observation invalid' }}
[MetafxMt5TabNative]::Calls=0
[MetafxMt5TabNative]::Drift=$true
$reason='accepted'
try {{ Read-TesterDiagnostic $request | Out-Null }} catch {{ $reason=$_.Exception.Message }}
if ($reason -cne 'mt5_tester_diagnostic_state_changed') {{ throw $reason }}
'PASS'
"""
        completed = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "PASS")

    @unittest.skipUnless(os.name == "nt", "PowerShell AST is Windows only")
    def test_missing_tester_can_capture_bound_root_without_promoting_readiness(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
if ($errors.Count -gt 0) {{throw ($errors|Out-String)}}
$fn=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Read-TesterDiagnostic'}},$true)
Invoke-Expression $fn.Extent.Text
function Fail($Code) {{throw $Code}}
$script:TerminalRootHandle=[IntPtr]10101
$TerminalProcess=[pscustomobject]@{{Id=101}}
$ResultSchema='ea-factory-visible-mt5-powershell-result-v1'
$script:rootCalls=0;$script:captures=0;$script:missingCode='mt5_tester_controls_not_verified';$script:rootDrift=$false
function Get-BoundTerminalRoot($Request,$Root) {{
 if ($Root -ne [IntPtr]10101) {{throw 'wrong root'}}
 $script:rootCalls++
 if($script:rootDrift) {{throw 'mt5_terminal_window_changed'}}
 return 'exactRoot'
}}
function Get-MinimalBoundTesterControlSet($Request,$Root,$AllowReveal) {{
 if ($AllowReveal -ne $false) {{throw 'unexpected reveal'}}
 throw $script:missingCode
}}
function Read-TesterDiagnosticGeometry($Bound,$Request,$RootOnly) {{
 if ($RootOnly -ne $true -or $Bound.root -cne 'exactRoot') {{throw 'not root-only'}}
 return @{{rootClient=@{{left=0;top=0;right=1920;bottom=1080}};controls=@{{root=@{{handle=10101}}}};startAncestors=@()}}
}}
function Read-TesterDiagnosticControl($Root,$Id,$Kind) {{return @{{matchCount=0;controls=@()}}}}
function Read-TesterDiagnosticNavigation($Root,$Request) {{return @{{viewMenu=@{{available=$false}}}}}}
function Capture-BoundTerminalWindow($Request,$Path) {{
 if ($Request.allowDiagnosticFocusChange -ne $true) {{throw 'capture without consent'}}
 $script:captures++
}}
$request=[pscustomobject]@{{stageId='backtest_recheck';operationId='ea-visible-00000000000000000000bb02';expectedSourceDigest=('a'*64);expectedBinaryDigest=('b'*64);requiredAutomationIds=@{{}}}}
$plain=Read-TesterDiagnostic $request
if ($plain.observation.available -ne $false -or $plain.observation.unavailableReason -cne 'mt5_tester_controls_not_verified' -or
    $plain.testerVerified -ne $false -or $plain.startInvoked -ne $false -or $script:captures -ne 0 -or $script:rootCalls -ne 2) {{throw 'unavailable observation invalid'}}
$request|Add-Member diagnosticScreenshotPath ([System.IO.Path]::Combine([System.IO.Path]::GetTempPath(),([Guid]::NewGuid().ToString()+'.png')))
$request|Add-Member allowDiagnosticFocusChange $true
$captured=Read-TesterDiagnostic $request
if ($captured.observation.available -ne $false -or $captured.testerVerified -ne $false -or $captured.startInvoked -ne $false -or
    $captured.diagnosticScreenshotCaptured -ne $true -or $script:captures -ne 1 -or $script:rootCalls -ne 4) {{throw 'capture changed readiness'}}
foreach($reason in @('mt5_terminal_window_changed','mt5_tester_diagnostic_state_changed','unexpected_error')) {{
 $script:missingCode=$reason;$caught='accepted'
 try {{Read-TesterDiagnostic $request|Out-Null}}catch{{$caught=$_.Exception.Message}}
 if($caught -cne $reason -or $script:captures -ne 1) {{throw 'unsafe binding accepted for capture'}}
}}
$script:rootDrift=$true;$caught='accepted'
try {{Read-TesterDiagnostic $request|Out-Null}}catch{{$caught=$_.Exception.Message}}
if($caught -cne 'mt5_terminal_window_changed' -or $script:captures -ne 1) {{throw 'root drift accepted'}}
'PASS'
"""
        completed = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "PASS")

    @unittest.skipUnless(os.name == "nt", "PowerShell AST is Windows only")
    def test_native_observation_parses_and_has_no_state_changing_calls(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
if ($errors.Count -gt 0) {{ throw ($errors | Out-String) }}
$out=@()
foreach ($name in @('Read-TesterDiagnostic','Read-TesterDiagnosticControl','Read-TesterDiagnosticCheckboxes','Read-TesterDiagnosticGeometry','Read-TesterDiagnosticClientRect','Read-TesterDiagnosticNavigation','Read-TesterPaneResizeDiagnostic')) {{
  $fn=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name}},$true)
  if ($null -eq $fn) {{ throw 'missing diagnostic function' }}
  $out += $fn.Extent.Text
}}
$out -join "`n"
"""
        completed = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        body = completed.stdout
        for forbidden in ("Normalize-", "Select-", "SelectExact", "Ensure-", "Close-", "Focus-",
                          "SetFocus", "SetForeground", "Start-Process", "Send-BalancedKey", "PostMessage",
                          "Invoke-Tester", "Write-", "Save-", "SetValue", "Click"):
            self.assertNotIn(forbidden, body)
        self.assertEqual(body.count("Get-MinimalBoundTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false"), 2)
        self.assertIn("CB_GETDROPPEDSTATE", body)
        self.assertIn('"expert") { 512 } else { 128 }', body)
        self.assertIn("[System.Windows.Automation.ControlType]::CheckBox", body)
        self.assertIn("$matches.Count -gt 16", body)
        self.assertIn("GetClientRect", body)
        self.assertIn("ClientToScreen", body)
        self.assertEqual(body.count("Capture-BoundTerminalWindow $Request"), 1)
        self.assertIn("if ($captureRequested)", body)
        self.assertIn("$Request.allowDiagnosticFocusChange -cne $true", body)
        self.assertIn("mt5_tester_diagnostic_state_changed", body)


if __name__ == "__main__":
    unittest.main()
