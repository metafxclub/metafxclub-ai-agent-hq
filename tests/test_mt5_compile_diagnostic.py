from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_ea_factory_visible_terminal_mt5 as fixtures


mt5 = fixtures.mt5


class CompileDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mt5-compile-diagnostic-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(strict=True)
        self.fixture = fixtures.Mt5AdapterFixture(self.root)
        self.request = self.fixture.request("compile_validate", "cafedead")
        self.request["visibleOperation"].update(state="uncertain", requiresExplicitResume=True)
        self.operation = self.request["visibleOperation"]["operationId"]
        working = self.fixture.data / "MQL5/Experts/Metafxclub/AgentHQ" / self.operation
        working.mkdir(parents=True)
        self.working_source = working / f"agenthq_{self.operation.removeprefix('ea-visible-')}.mq5"
        self.working_source.write_bytes(self.fixture.source.read_bytes())
        self.binary = self.working_source.with_suffix(".ex5")
        self.binary.write_bytes(b"existing-compiled-binary")
        (self.fixture.workspace / "Summaries").mkdir()
        self.intent = self.fixture.workspace / "Summaries" / f"{self.operation}-compile-intent.json"
        self.intent.write_text(json.dumps({
            "schemaVersion": mt5.ACTION_INTENT_SCHEMA, "operationId": self.operation,
            "stageId": "compile_validate", "terminalCandidateId": self.fixture.binding["candidateId"],
            "terminalSelectionRevision": 1, "terminalBindingDigest": "a" * 64,
            "sourceDigest": hashlib.sha256(self.fixture.source.read_bytes()).hexdigest(),
            "platform": "mt5",
        }), encoding="utf-8")
        self.actions = []
        self.result_patch = {}
        self.mutate_binary = False

        def runner(payload, **kwargs):
            self.actions.append(payload["action"])
            if payload["action"] == "probe":
                return self.fixture.runner.probe(payload)
            self.assertEqual(payload["action"], "diagnose_compile")
            self.assertEqual(payload["expectedTerminalProcessId"], 101)
            self.assertEqual(Path(payload["sourcePath"]), self.working_source)
            if self.mutate_binary:
                self.binary.write_bytes(b"changed")
            return {
                "schemaVersion": mt5.POWERSHELL_RESULT_SCHEMA, "ok": True,
                "action": "diagnose_compile", "operationId": self.operation,
                "diagnosticOnly": True, "compileInvoked": False, "compileVerified": False,
                "workingSourceSha256": payload["expectedSourceDigest"],
                "editorProcessId": 202, "editorWindowHandle": 20202,
                "sourceWindowBound": True, "observation": {"reasonCode": "metaeditor_clipboard_format_unsupported"},
                **self.result_patch,
            }

        self.fixture.adapter._powershell_runner = runner

    def snapshot(self):
        return {str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob("*") if p.is_file()}

    def test_uncertain_operation_observation_changes_no_evidence_or_retry(self):
        before = self.snapshot()
        request_before = copy.deepcopy(self.request)
        result = self.fixture.adapter.compile_diagnostic(request=self.request)
        self.assertEqual(self.actions, ["probe", "diagnose_compile"])
        self.assertFalse(result["compileVerified"])
        self.assertFalse(result["compileInvoked"])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.request, request_before)

    def test_working_source_drift_rejected_before_native_probe(self):
        self.working_source.write_bytes(b"different source")
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "compile_working_source_changed"):
            self.fixture.adapter.compile_diagnostic(request=self.request)
        self.assertEqual(self.actions, [])

    def test_intent_identity_drift_rejected_before_native_probe(self):
        value = json.loads(self.intent.read_text())
        value["terminalSelectionRevision"] = 2
        self.intent.write_text(json.dumps(value))
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "visible_action_intent_mismatch"):
            self.fixture.adapter.compile_diagnostic(request=self.request)
        self.assertEqual(self.actions, [])

    def test_diagnostic_cannot_claim_compile_or_different_source_operation(self):
        for patch in ({"compileVerified": True}, {"compileInvoked": True},
                      {"operationId": "ea-visible-" + "f" * 24},
                      {"workingSourceSha256": "b" * 64}, {"editorProcessId": True},
                      {"extra": "not allowed"}, {"observation": {"raw": "x" * 17000}}):
            with self.subTest(patch=next(iter(patch))):
                self.result_patch = patch
                with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "compile_diagnostic_result_invalid"):
                    self.fixture.adapter.compile_diagnostic(request=self.request)

    def test_concurrent_binary_change_is_rejected_without_repairing_it(self):
        self.mutate_binary = True
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "compile_diagnostic_artifact_changed"):
            self.fixture.adapter.compile_diagnostic(request=self.request)
        self.assertEqual(self.binary.read_bytes(), b"changed")

    def test_diagnostic_uncertain_exception_does_not_enable_normal_compile(self):
        with self.assertRaisesRegex(mt5.VisibleTerminalAdapterError, "visible_request_safety_invalid"):
            self.fixture.adapter.compile_handler(request=self.request)
        self.assertEqual(self.actions, [])

    def test_native_diagnostic_has_no_compile_launch_write_or_tab_selection(self):
        text = fixtures.PS_PATH.read_text(encoding="utf-8")
        body = text[text.index("function Read-CompileDiagnostic"):text.index("function Wait-CompileResult")]
        for forbidden in ("Invoke-Compile", "Start-Process", "Get-Or-StartMetaEditor", "Send-BalancedKey",
                          "SelectExact", "Write-Json", "File]::Delete", "Capture-Window"):
            self.assertNotIn(forbidden, body)
        self.assertIn("Assert-MetaEditorSourceBindingUnchanged", body)
        self.assertIn("CopyDiagnosticRow", body)
        self.assertIn("$observation.selectedTab -cne \"Errors\"", body)
        native = text[text.index("public static string CopyDiagnosticRow"):text.index("public static string CopyLastVisibleRow")]
        self.assertIn("finally", native)
        self.assertIn("SetForegroundWindow(foreground)", native)

    @unittest.skipUnless(os.name == "nt", "PowerShell parser is Windows only")
    def test_powershell_diagnostic_parses_and_unwraps_underlying_error(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
if ($errors.Count -gt 0) {{ throw ($errors | Out-String) }}
$fn=$ast.Find({{param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Get-CompileDiagnosticErrorCode'}},$true)
Invoke-Expression $fn.Extent.Text
$inner=[InvalidOperationException]::new('metaeditor_clipboard_format_unsupported')
$outer=[Exception]::new('wrapper', $inner)
$record=[System.Management.Automation.ErrorRecord]::new($outer,'test',[System.Management.Automation.ErrorCategory]::NotSpecified,$null)
Get-CompileDiagnosticErrorCode $record
"""
        completed = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "metaeditor_clipboard_format_unsupported")

    @unittest.skipUnless(os.name == "nt", "PowerShell timing helper is Windows only")
    def test_diagnostic_checkpoint_timings_are_bounded_monotonic_and_optional(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
$fn=$ast.Find({{param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Set-CompileDiagnosticCheckpoint'}},$true)
Invoke-Expression $fn.Extent.Text
$ignored=@(Set-CompileDiagnosticCheckpoint $null 'not_active')
if ($ignored.Count -ne 0) {{ throw 'timing helper changed production output' }}
$state=@{{}}
Set-CompileDiagnosticCheckpoint $state 'root_binding'
Start-Sleep -Milliseconds 30
Set-CompileDiagnosticCheckpoint $state 'uia_tabs_find_all'
Start-Sleep -Milliseconds 30
Set-CompileDiagnosticCheckpoint $state 'complete'
$state.timings | ConvertTo-Json -Compress
"""
        completed = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        timings = json.loads(completed.stdout)
        self.assertEqual(set(timings), {"root_binding", "uia_tabs_find_all"})
        for duration in timings.values():
            self.assertIs(type(duration), int)
            self.assertGreaterEqual(duration, 20)
            self.assertLess(duration, 5000)

    @unittest.skipUnless(os.name == "nt", "PowerShell diagnostic classification is Windows only")
    def test_wrapped_fatal_cleanup_errors_survive_both_diagnostic_catches(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
foreach ($name in @('Fail','Get-CompileDiagnosticErrorCode')) {{
  $fn=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name}},$true)
  Invoke-Expression $fn.Extent.Text
}}
$diagnostic=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Read-CompileDiagnostic'}},$true)
$outer=$diagnostic.Find({{param($n) $n -is [Management.Automation.Language.CatchClauseAst] -and $n.Extent.Text.Contains('$observation.reasonCode = Get-CompileDiagnosticErrorCode')}},$true)
$inner=$diagnostic.Find({{param($n) $n -is [Management.Automation.Language.CatchClauseAst] -and $n.Extent.Text.Contains('$readerError = Get-CompileDiagnosticErrorCode')}},$true)
$outerBody=$outer.Body.Statements.Extent.Text -join "`n"
$innerBody=$inner.Body.Statements.Extent.Text -join "`n"
$out=@()
foreach ($mode in @('direct_copy','production_reader')) {{
  foreach ($code in @('metaeditor_selection_focus_restore_failed','metaeditor_clipboard_restore_mismatch',
                     'metaeditor_diagnostic_foreground_restore_failed')) {{
    $observation=[ordered]@{{reasonCode=$null}}
    $result='unexpected_acceptance'
    try {{
      try {{
        try {{ throw [Reflection.TargetInvocationException]::new('native wrapper',[InvalidOperationException]::new($code)) }}
        catch {{ if ($mode -ceq 'production_reader') {{ Invoke-Expression $innerBody }} else {{ throw }} }}
      }} catch {{ Invoke-Expression $outerBody }}
    }} catch {{ $result=[string]$_.Exception.Message }}
    $out += [ordered]@{{mode=$mode; expected=$code; reason=$result}}
  }}
}}
$out | ConvertTo-Json -Compress
"""
        completed = subprocess.run([str(mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        rows = json.loads(completed.stdout)
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row["reason"], row["expected"], row["mode"])


if __name__ == "__main__":
    unittest.main()
