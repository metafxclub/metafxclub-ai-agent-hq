"""Read-only resize capability and non-client hit-test observations, no real UI."""
import json
import os
import subprocess
import unittest

import test_ea_factory_visible_terminal_mt5 as fixtures


@unittest.skipUnless(os.name == "nt", "PowerShell helper test requires Windows")
class TesterResizeDiagnosticTests(unittest.TestCase):
    def test_exact_pane_observation_is_read_only_and_rejects_binding_drift(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = r'''
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -TypeDefinition @'
using System;
public static class MetafxMt5VisibleNative {
 public const uint GA_ROOT=2,SMTO_ABORTIFHUNG=2,SMTO_BLOCK=1,SMTO_ERRORONEXIT=32;
 public class RECT {public int Left,Top,Right,Bottom;}
 public static int Calls;public static bool Timeout,Drift;
 public static bool IsWindow(IntPtr h){return h==(IntPtr)1||h==(IntPtr)2;}
 public static int GetDlgCtrlID(IntPtr h){return 32846;}
 public static IntPtr GetAncestor(IntPtr h,uint f){return Drift&&Calls>0?(IntPtr)99:(IntPtr)1;}
 public static IntPtr GetParent(IntPtr h){return (IntPtr)1;}
 public static bool GetWindowRect(IntPtr h,out RECT r){r=new RECT{Left=0,Top=745,Right=1920,Bottom=746};return true;}
 public static IntPtr SendMessageTimeout(IntPtr h,int message,IntPtr w,IntPtr l,uint flags,uint timeout,out IntPtr hit){
  if((h!=(IntPtr)1&&h!=(IntPtr)2)||message!=0x84||w!=IntPtr.Zero||timeout!=250)throw new Exception("mutation or unbound read");
  Calls++;hit=(IntPtr)12;return Timeout?IntPtr.Zero:(IntPtr)1;
 }
}
'@
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PS_PATH',[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
$fn=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Read-TesterPaneResizeDiagnostic'},$true)
Invoke-Expression $fn.Extent.Text
function Fail($code){throw $code}
function Get-NativeOwner($h){if($script:wrongOwner){return 999};return 101}
$script:TerminalRootHandle=[IntPtr]1;$TerminalProcess=[pscustomobject]@{Id=101}
$control=[pscustomobject]@{Current=@{NativeWindowHandle=2}}
$control|Add-Member ScriptMethod GetSupportedPatterns {return @([pscustomobject]@{ProgrammaticName='TransformPatternIdentifiers.Pattern'})}
$control|Add-Member ScriptMethod TryGetCurrentPattern {param($p,$out);if($script:noTransform){return $false};$out.Value=[pscustomobject]@{Current=@{CanMove=$false;CanResize=$true;CanRotate=$false}};return $true}
$rows=@()
foreach($case in @('valid','noTransform','timeout','wrongOwner','drift')){
 [MetafxMt5VisibleNative]::Calls=0;[MetafxMt5VisibleNative]::Timeout=$case-eq'timeout';[MetafxMt5VisibleNative]::Drift=$case-eq'drift'
 $script:wrongOwner=$case-eq'wrongOwner';$script:noTransform=$case-eq'noTransform'
 $reason='observed';$value=$null;try{$value=Read-TesterPaneResizeDiagnostic $control}catch{$reason=$_.Exception.Message}
 $rows+=@{case=$case;reason=$reason;calls=[MetafxMt5VisibleNative]::Calls;value=$value}
};$rows|ConvertTo-Json -Depth 10 -Compress
'''.replace("PS_PATH", path)
        completed = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                                    "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        rows = {row["case"]: row for row in json.loads(completed.stdout)}
        self.assertTrue(rows["valid"]["value"]["canResize"])
        self.assertFalse(rows["valid"]["value"]["canMove"])
        self.assertEqual(rows["valid"]["calls"], 6)
        self.assertEqual([x["y"] for x in rows["valid"]["value"]["hitTests"]], [744, 745, 746] * 2)
        self.assertFalse(rows["noTransform"]["value"]["transformAvailable"])
        self.assertTrue(all(x["hitCode"] is None for x in rows["timeout"]["value"]["hitTests"]))
        self.assertEqual(rows["wrongOwner"]["calls"], 0)
        self.assertEqual(rows["wrongOwner"]["reason"], "mt5_tester_resize_diagnostic_binding_invalid")
        self.assertEqual(rows["drift"]["reason"], "mt5_tester_resize_diagnostic_binding_changed")


if __name__ == "__main__":
    unittest.main()
