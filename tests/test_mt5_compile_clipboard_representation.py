"""Pure clipboard-value tests: never read, write, or open the system clipboard."""
from __future__ import annotations

import json
import os
import subprocess
import unittest

import test_ea_factory_visible_terminal_mt5 as fixtures


@unittest.skipUnless(os.name == "nt", "Production C# helper tests require Windows PowerShell")
class ClipboardRepresentationTests(unittest.TestCase):
    def run_ps(self, body: str):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = f"""
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)
if ($errors.Count -ne 0) {{ throw ($errors | Out-String) }}
$command=$ast.Find({{param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -ceq 'Add-Type' -and $n.Extent.Text.Contains('public static class MetafxMetaEditorCompileNative')}},$true)
Invoke-Expression $command.Extent.Text
$flags=[Reflection.BindingFlags]'NonPublic,Static'
$fingerprint=[MetafxMetaEditorCompileNative].GetMethod('FingerprintClipboardValue',$flags)
$clone=[MetafxMetaEditorCompileNative].GetMethod('CloneClipboardValue',$flags)
function Fingerprint($value) {{ return $fingerprint.Invoke($null,[object[]]@(,$value)) }}
function Clone-Value($value) {{ return ,$clone.Invoke($null,[object[]]@(,$value)) }}
{body}
"""
        completed = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile",
                                    "-NonInteractive", "-Command", script],
                                   capture_output=True, text=True, timeout=25)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_same_binary_payload_has_one_fingerprint_across_managed_wrappers(self):
        result = self.run_ps(r"""
$raw=[byte[]]@(0,1,2,127,128,255)
$memory=[IO.MemoryStream]::new($raw,$false); $memory.Position=3
$buffer=[IO.BufferedStream]::new([IO.MemoryStream]::new($raw,$false)); $buffer.Position=2
@{ bytes=(Fingerprint $raw); memory=(Fingerprint $memory); buffer=(Fingerprint $buffer)
   memoryPosition=$memory.Position; bufferPosition=$buffer.Position } | ConvertTo-Json -Compress
$memory.Dispose(); $buffer.Dispose()
""")
        self.assertEqual(result["bytes"], result["memory"])
        self.assertEqual(result["bytes"], result["buffer"])
        self.assertEqual(result["memoryPosition"], 3)
        self.assertEqual(result["bufferPosition"], 2)

    def test_changed_payload_or_length_never_matches_and_type_families_stay_distinct(self):
        result = self.run_ps(r"""
$raw=[byte[]]@(0,1,2,127,128,255)
$changed=[byte[]]@(0,1,2,127,128,254)
$longer=[byte[]]@(0,1,2,127,128,255,0)
$shorter=[byte[]]@(0,1,2,127,128)
$text='binary test'; $textBytes=[Text.Encoding]::UTF8.GetBytes($text)
$empty=[byte[]]@(); $emptyStream=[IO.MemoryStream]::new()
@{ original=(Fingerprint $raw); changed=(Fingerprint $changed); longer=(Fingerprint $longer)
   shorter=(Fingerprint $shorter); text=(Fingerprint $text); textBytes=(Fingerprint $textBytes)
   strings=(Fingerprint ([string[]]@($text))); empty=(Fingerprint $empty); emptyStream=(Fingerprint $emptyStream)
   emptyText=(Fingerprint '') } | ConvertTo-Json -Compress
$emptyStream.Dispose()
""")
        for name in ("changed", "longer", "shorter"):
            self.assertNotEqual(result["original"], result[name], name)
        self.assertEqual(len({result["text"], result["textBytes"], result["strings"]}), 3)
        self.assertEqual(result["empty"], result["emptyStream"])
        self.assertNotEqual(result["empty"], result["emptyText"])

    def test_cloned_binary_values_are_independent_and_keep_source_stream_position(self):
        result = self.run_ps(r"""
$raw=[byte[]]@(3,4,5)
$copy=Clone-Value $raw
$before=Fingerprint $copy; $raw[0]=99
$memory=[IO.MemoryStream]::new([byte[]]@(3,4,5),$false); $memory.Position=2
$memoryCopy=Clone-Value $memory
@{ before=$before; copied=(Fingerprint $copy); changed=(Fingerprint $raw)
   streamCopied=(Fingerprint $memoryCopy); sourcePosition=$memory.Position; copyPosition=$memoryCopy.Position } | ConvertTo-Json -Compress
$memory.Dispose(); $memoryCopy.Dispose()
""")
        self.assertEqual(result["before"], result["copied"])
        self.assertNotEqual(result["before"], result["changed"])
        self.assertEqual(result["before"], result["streamCopied"])
        self.assertEqual(result["sourcePosition"], 2)
        self.assertEqual(result["copyPosition"], 0)

    def test_unsupported_values_and_images_do_not_get_binary_wrapper_exception(self):
        result = self.run_ps(r"""
$failures=@()
foreach ($value in @($null,[object]::new(),[int]7)) {
 try { [void](Fingerprint $value); $failures+='accepted' }
 catch { $e=$_.Exception; while ($null -ne $e.InnerException) { $e=$e.InnerException }; $failures+=$e.Message }
}
$image=[Drawing.Bitmap]::new(2,2); $image.SetPixel(0,0,[Drawing.Color]::Red)
$original=Fingerprint $image; $copy=Clone-Value $image
$stream=[IO.MemoryStream]::new(); $image.Save($stream,[Drawing.Imaging.ImageFormat]::Png)
$same=Fingerprint $copy; $copy.SetPixel(0,0,[Drawing.Color]::Blue)
@{ failures=$failures; original=$original; copy=$same; changed=(Fingerprint $copy); encoded=(Fingerprint $stream) } | ConvertTo-Json -Compress
$image.Dispose(); $copy.Dispose(); $stream.Dispose()
""")
        self.assertEqual(result["failures"], ["metaeditor_clipboard_format_unavailable",
                                             "metaeditor_clipboard_format_unsupported",
                                             "metaeditor_clipboard_format_unsupported"])
        self.assertEqual(result["original"], result["copy"])
        self.assertNotEqual(result["original"], result["changed"])
        self.assertNotEqual(result["original"], result["encoded"])

    def test_restore_retains_exact_format_set_and_per_format_payload_checks(self):
        text = fixtures.PS_PATH.read_text(encoding="utf-8")
        start = text.index("static void RestoreClipboard(")
        body = text[start:text.index("public static int GetItemCount(", start)]
        self.assertIn("restoredFormats.Length != snapshot.Formats.Length", body)
        self.assertIn("String.Equals(expected, restoredFormats[index], StringComparison.Ordinal)", body)
        self.assertIn("String.Equals(actualFingerprint, snapshot.Fingerprints[expected], StringComparison.Ordinal)", body)
        self.assertIn("FingerprintClipboardValue", body)
        self.assertIn("metaeditor_clipboard_restore_incomplete", body)

    def test_mismatch_diagnostics_expose_only_format_and_managed_type_names(self):
        result = self.run_ps(r"""
$method=[MetafxMetaEditorCompileNative].GetMethod('ClipboardRestoreMismatch',$flags)
$expected=[byte[]]@(21,22,23); $actual=[IO.MemoryStream]::new([byte[]]@(21,22,24),$false)
$mismatchError=$method.Invoke($null,[object[]]@('Test Binary Format',$expected,$actual))
$metadata=[ordered]@{}; foreach ($key in $mismatchError.Data.Keys) { $metadata[$key]=$mismatchError.Data[$key] }
@{ code=$mismatchError.Message; metadata=$metadata } | ConvertTo-Json -Compress
$actual.Dispose()
""")
        self.assertEqual(result, {"code": "metaeditor_clipboard_restore_mismatch", "metadata": {
            "clipboardFormat": "Test Binary Format", "expectedType": "System.Byte[]",
            "actualType": "System.IO.MemoryStream"}})

    def test_metadata_is_bounded_consumed_once_and_reset_before_next_observation(self):
        result = self.run_ps(r"""
$method=[MetafxMetaEditorCompileNative].GetMethod('ClipboardRestoreMismatch',$flags)
[void]$method.Invoke($null,[object[]]@(('F'*300),[byte[]]@(1),[byte[]]@(2)))
$first=[MetafxMetaEditorCompileNative]::ConsumeClipboardRestoreMismatchMetadata()
$second=[MetafxMetaEditorCompileNative]::ConsumeClipboardRestoreMismatchMetadata()
[void]$method.Invoke($null,[object[]]@('OldFormat',[byte[]]@(1),[byte[]]@(2)))
# Zero handles fail before any user32 call; only reset is under test.
try { [void][MetafxMetaEditorCompileNative]::CopyLastVisibleRow([IntPtr]::Zero,[IntPtr]::Zero) } catch {}
$after=[MetafxMetaEditorCompileNative]::ConsumeClipboardRestoreMismatchMetadata()
@{ formatLength=$first['clipboardFormat'].Length; count=$first.Count; consumed=$null -eq $second; reset=$null -eq $after } | ConvertTo-Json -Compress
""")
        self.assertEqual(result, {"formatLength": 256, "count": 3, "consumed": True, "reset": True})

    def test_real_failure_writer_adds_metadata_only_to_failed_diagnostic_response(self):
        result = self.run_ps(r"""
$method=[MetafxMetaEditorCompileNative].GetMethod('ClipboardRestoreMismatch',$flags)
$writer=$ast.Find({param($n) $n -is [Management.Automation.Language.TryStatementAst] -and $n.Body.Extent.Text.Contains('$failureResult = [ordered]@{ schemaVersion')},$true)
if ($null -eq $writer) { throw 'production failure writer not found' }
$writerBody=$writer.Body.Statements.Extent.Text -join "`n"
$ResultSchema='test-schema'; $ResponsePath='unused.json'
function Write-JsonExclusive($path,$value) { $script:lastFailure=$value }
$outputs=@()
foreach ($action in @('diagnose_compile','compile','diagnose_compile')) {
  [void]$method.Invoke($null,[object[]]@('Test Format',[byte[]]@(1),[IO.MemoryStream]::new([byte[]]@(2),$false)))
  $request=[pscustomobject]@{ action=$action; operationId='ea-visible-test' }
  $code=if ($outputs.Count -eq 2) { 'metaeditor_compile_rows_invalid' } else { 'metaeditor_clipboard_restore_mismatch' }
  Invoke-Expression $writerBody
  $outputs+=,$script:lastFailure
}
ConvertTo-Json -InputObject $outputs -Depth 5 -Compress
""")
        for index, entry in enumerate(result):
            self.assertFalse(entry["ok"])
            self.assertEqual(entry["operationId"], "ea-visible-test")
            self.assertEqual(entry["reasonCode"], "metaeditor_compile_rows_invalid" if index == 2
                             else "metaeditor_clipboard_restore_mismatch")
            self.assertEqual("clipboardMismatch" in entry, index == 0)
        self.assertEqual(result[0]["clipboardMismatch"], {"clipboardFormat": "Test Format",
                         "expectedType": "System.Byte[]", "actualType": "System.IO.MemoryStream"})


if __name__ == "__main__":
    unittest.main()
