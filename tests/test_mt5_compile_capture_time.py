from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_ea_factory_visible_terminal_mt5 as fixtures


@unittest.skipUnless(os.name == "nt", "Real PowerShell contract tests are Windows only")
class CompileCaptureTimeTests(unittest.TestCase):
    def run_ps(self, body: str, *, timeout: int = 25):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
if ($errors.Count -ne 0) {{ throw ($errors | Out-String) }}
function Load-Function([string]$name) {{
  $fn=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name}},$true)
  Invoke-Expression ('function global:'+$fn.Name+$fn.Extent.Text.Substring(('function '+$fn.Name).Length))
}}
Load-Function 'Fail'
{body}
"""
        completed = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile",
                                    "-NonInteractive", "-Command", script],
                                   capture_output=True, text=True, timeout=timeout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_timely_capture_survives_slow_successful_cleanup_but_invalid_or_late_capture_does_not(self):
        result = self.run_ps(r"""
Load-Function 'Wait-CompileResult'
$script:mode=''; $script:calls=0
$script:oldStamp=[Diagnostics.Stopwatch]::GetTimestamp()
function Find-CompileResult($Root,$Editor,$RequireSuccess) {
  $script:calls++
  [long]$stamp=[Diagnostics.Stopwatch]::GetTimestamp()
  switch ($script:mode) {
    'slow_cleanup' { Start-Sleep -Milliseconds 1200 }
    'restore_failed' { throw [InvalidOperationException]::new('metaeditor_clipboard_restore_mismatch') }
    'late' { Start-Sleep -Milliseconds 1200; $stamp=[Diagnostics.Stopwatch]::GetTimestamp() }
    'reused' { $stamp=$script:oldStamp }
    'future' { $stamp=[Diagnostics.Stopwatch]::GetTimestamp()+[Diagnostics.Stopwatch]::Frequency }
  }
  $row=[ordered]@{ rowCount=3; snapshotSha256=('c'*64); resultLine='0 errors, 0 warnings'; captureTimestampTicks=$stamp }
  if ($script:mode -ceq 'missing') { $row.Remove('captureTimestampTicks') }
  if ($script:mode -ceq 'wrong_type') { $row.captureTimestampTicks=[string]$stamp }
  if ($script:mode -ceq 'empty') { $row.rowCount=0; $row.resultLine=$null }
  return $row
}
$results=[ordered]@{}
foreach ($mode in @('slow_cleanup','restore_failed','late','reused','future','missing','wrong_type','empty')) {
  $script:mode=$mode; $script:calls=0
  $watch=[Diagnostics.Stopwatch]::StartNew()
  try {
    $row=Wait-CompileResult $null $null ($mode -cne 'empty') ('b'*64) 1 'mt5_metaeditor_compile_result_not_fresh'
    $results[$mode]=[ordered]@{ accepted=$true; rowCount=$row.rowCount; elapsedMs=$watch.ElapsedMilliseconds; calls=$script:calls }
  } catch {
    $results[$mode]=[ordered]@{ accepted=$false; code=$_.Exception.Message; calls=$script:calls }
  }
}
$results | ConvertTo-Json -Depth 5 -Compress
""")
        self.assertTrue(result["slow_cleanup"]["accepted"])
        self.assertGreaterEqual(result["slow_cleanup"]["elapsedMs"], 1200)
        self.assertEqual(result["slow_cleanup"]["calls"], 1)
        self.assertTrue(result["empty"]["accepted"])
        self.assertEqual(result["empty"]["rowCount"], 0)
        self.assertEqual(result["restore_failed"]["code"], "metaeditor_clipboard_restore_mismatch")
        self.assertEqual(result["late"]["code"], "mt5_metaeditor_compile_result_not_fresh")
        for case in ("reused", "future", "missing", "wrong_type"):
            self.assertEqual(result[case]["code"], "mt5_metaeditor_compile_capture_unverified", case)
            self.assertEqual(result[case]["calls"], 1, case)

    def test_native_capture_stamp_is_consumed_once_and_reset_before_invalid_new_observations(self):
        result = self.run_ps(r"""
$command=$ast.Find({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -ceq 'Add-Type' -and $n.Extent.Text.Contains('public static class MetafxMetaEditorCompileNative')},$true)
Invoke-Expression $command.Extent.Text
$field=[MetafxMetaEditorCompileNative].GetField('captureTimestamp',[Reflection.BindingFlags]'NonPublic,Static')
$field.SetValue($null,[long]123)
$first=[MetafxMetaEditorCompileNative]::ConsumeCaptureTimestamp()
$second=[MetafxMetaEditorCompileNative]::ConsumeCaptureTimestamp()
$field.SetValue($null,[long]456)
try { [void][MetafxMetaEditorCompileNative]::GetItemCount([IntPtr]::Zero) } catch {}
$afterCount=[MetafxMetaEditorCompileNative]::ConsumeCaptureTimestamp()
$field.SetValue($null,[long]789)
try { [void][MetafxMetaEditorCompileNative]::CopyLastVisibleRow([IntPtr]::Zero,[IntPtr]::Zero) } catch {}
$afterCopy=[MetafxMetaEditorCompileNative]::ConsumeCaptureTimestamp()
$restore=[MetafxMetaEditorCompileNative].GetMethod('RestoreSelectionAndFocus',[Reflection.BindingFlags]'NonPublic,Static')
$restoreCodes=@()
foreach ($case in 0,1) {
  # Invalid handles only: exercise actual native cleanup classification without
  # selecting, focusing, or changing any real application or clipboard.
  $states=$null; if ($case -eq 0) { $states=[uint32[]]@(1) }
  $focus=if ($case -eq 1) { [IntPtr]1 } else { [IntPtr]::Zero }
  try { [void]$restore.Invoke($null,[object[]]@([IntPtr]::Zero,[IntPtr]::Zero,[IntPtr]::Zero,$states,$focus)); $restoreCodes+='accepted' }
  catch { $e=$_.Exception; while ($null -ne $e.InnerException) { $e=$e.InnerException }; $restoreCodes+=$e.Message }
}
@{ first=$first; second=$second; afterCount=$afterCount; afterCopy=$afterCopy; restoreCodes=$restoreCodes } | ConvertTo-Json -Compress
""")
        self.assertEqual(result.pop("restoreCodes"), ["metaeditor_selection_focus_restore_failed"] * 2)
        self.assertEqual(result, {"first": 123, "second": 0, "afterCount": 0, "afterCopy": 0})

    def test_real_production_reader_catch_preserves_fatal_restoration_failures(self):
        result = self.run_ps(r"""
Load-Function 'Get-CompileDiagnosticErrorCode'
$reader=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Find-CompileResult'},$true)
$catch=$reader.Find({param($n) $n -is [Management.Automation.Language.CatchClauseAst] -and $n.Extent.Text.Contains('$underlyingCode = Get-CompileDiagnosticErrorCode')},$true)
$catchScript=$catch.Body.Statements.Extent.Text -join "`n"
$DiagnosticState=$null
$out=[ordered]@{}
foreach ($code in @('metaeditor_clipboard_restore_mismatch','metaeditor_clipboard_restore_failed',
                   'metaeditor_clipboard_restore_incomplete','metaeditor_diagnostic_foreground_restore_failed',
                   'metaeditor_compile_focus_restore_failed','mt5_metaeditor_compile_capture_unverified',
                   'metaeditor_selection_focus_restore_failed',
                   'metaeditor_compile_rows_invalid')) {
  try {
    try { throw [Exception]::new('wrapper',[InvalidOperationException]::new($code)) }
    catch { Invoke-Expression $catchScript }
    $out[$code]='accepted'
  } catch { $out[$code]=$_.Exception.Message }
}
$out | ConvertTo-Json -Compress
""")
        for code, observed in result.items():
            self.assertEqual(observed, "mt5_metaeditor_compile_result_unverified"
                             if code == "metaeditor_compile_rows_invalid" else code)

    def test_source_and_binary_content_or_mtime_drift_are_rejected_after_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="compile-artifact-identity-") as tmp:
            root = Path(tmp)
            source, binary = root / "test.mq5", root / "test.ex5"
            source.write_bytes(b"source original")
            binary.write_bytes(b"binary original")
            paths = json.dumps([str(source), str(binary)]).replace("'", "''")
            result = self.run_ps(r"""
Load-Function 'Get-CompileArtifactIdentity'
Load-Function 'Assert-CompileArtifactIdentity'
Load-Function 'Get-Sha256'
""" + f"$paths=ConvertFrom-Json '{paths}'\n" + r"""
$baseline=Get-CompileArtifactIdentity $paths[0] $paths[1]
Assert-CompileArtifactIdentity $baseline (Get-CompileArtifactIdentity $paths[0] $paths[1])
$out=[ordered]@{ unchanged=$true }
foreach ($index in 0,1) {
  $path=$paths[$index]; $bytes=[IO.File]::ReadAllBytes($path); $mtime=[IO.File]::GetLastWriteTimeUtc($path)
  $changed=[byte[]]$bytes.Clone(); $changed[0]=$changed[0] -bxor 1
  [IO.File]::WriteAllBytes($path,$changed); [IO.File]::SetLastWriteTimeUtc($path,$mtime)
  try { Assert-CompileArtifactIdentity $baseline (Get-CompileArtifactIdentity $paths[0] $paths[1]); $out["content$index"]='accepted' }
  catch { $out["content$index"]=$_.Exception.Message }
  [IO.File]::WriteAllBytes($path,$bytes); [IO.File]::SetLastWriteTimeUtc($path,$mtime.AddSeconds(1))
  try { Assert-CompileArtifactIdentity $baseline (Get-CompileArtifactIdentity $paths[0] $paths[1]); $out["mtime$index"]='accepted' }
  catch { $out["mtime$index"]=$_.Exception.Message }
  [IO.File]::SetLastWriteTimeUtc($path,$mtime)
}
[IO.File]::Delete($paths[1])
try { [void](Get-CompileArtifactIdentity $paths[0] $paths[1]); $out.deleted='accepted' } catch { $out.deleted=$_.Exception.Message }
$out | ConvertTo-Json -Compress
""")
        self.assertTrue(result.pop("unchanged"))
        self.assertEqual(len(result), 5)
        self.assertEqual(set(result.values()), {"mt5_compile_artifacts_changed_during_observation"})


if __name__ == "__main__":
    unittest.main()
