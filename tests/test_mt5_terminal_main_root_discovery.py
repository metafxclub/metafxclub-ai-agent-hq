"""Execute the production root filter and probe helpers against fake windows."""
import json
import os
import subprocess
import unittest

import test_ea_factory_visible_terminal_mt5 as fixtures


@unittest.skipUnless(os.name == "nt", "PowerShell/C# helper execution requires Windows")
class TerminalMainRootDiscoveryTests(unittest.TestCase):
    def test_unique_native_root_and_probe_continuity_without_dynamic_mainwindow(self):
        source = fixtures.PS_PATH.read_text(encoding="utf-8-sig")
        method = source[source.index("  public static IntPtr FindTerminalMainWindowExact("):
                        source.index("  public static void PostButtonClickIfTextExact(")]
        script = r"""
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
public static class MetafxMt5VisibleNative {
 public const uint GA_ROOT=2,GW_OWNER=4;
 public class Window {public int H,Pid,Owner,Root;public bool Visible=true,Enabled=true,Exists=true;public string Class="MetaQuotes::MetaTrader::5.00";public Window(int h,int pid){H=h;Pid=pid;Root=h;}}
 public static Window[] Rows=new Window[0];
 public static bool EnumFailure;
 delegate bool EnumWindowProc(IntPtr h,IntPtr l);
 static bool EnumWindows(EnumWindowProc cb,IntPtr l){if(EnumFailure)return false;foreach(Window w in Rows)if(!cb((IntPtr)w.H,l))return false;return true;}
 public static Window Get(IntPtr h){foreach(Window w in Rows)if(w.H==h.ToInt32())return w;return null;}
 public static bool IsWindow(IntPtr h){Window w=Get(h);return w!=null&&w.Exists;}
 public static bool IsWindowVisible(IntPtr h){return Get(h).Visible;}
 public static bool IsWindowEnabled(IntPtr h){return Get(h).Enabled;}
 public static IntPtr GetWindow(IntPtr h,uint k){return (IntPtr)Get(h).Owner;}
 public static IntPtr GetAncestor(IntPtr h,uint k){return (IntPtr)Get(h).Root;}
 static uint GetWindowThreadProcessId(IntPtr h,out uint pid){pid=(uint)Get(h).Pid;return 1;}
 static string ReadWindowClassExact(IntPtr h){return Get(h).Class;}
METHOD
}
'@
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PS_PATH',[ref]$tokens,[ref]$errors)
if($errors.Count -gt 0){throw ($errors|Out-String)}
foreach($name in @('Get-TerminalMainWindowExact','Get-ExactTerminal','New-Probe','New-BoundProbe')){
 $fn=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 Invoke-Expression ($fn.Extent.Text.Replace('[System.Diagnostics.Process]','[object]').Replace('[System.Windows.Automation.AutomationElement]','[object]'))
}
function Fail($Code){throw $Code}
function Get-NativeOwner($Handle){return [MetafxMt5VisibleNative]::Get($Handle).Pid}
function Get-Process {param($Name,$ErrorAction) return $script:processes}
function New-Process($PidValue,$PathValue){return [pscustomobject]@{Id=$PidValue;Path=$PathValue;MainWindowHandle=[IntPtr]99;MainWindowTitle=''}}
function Native-Reason($PidValue){try{return [long](Get-TerminalMainWindowExact (New-Process $PidValue 'C:\fake\terminal64.exe'))}catch{return $_.Exception.Message}}
$main=[MetafxMt5VisibleNative+Window]::new(1,101)
$owned=[MetafxMt5VisibleNative+Window]::new(99,101);$owned.Owner=1
$wrongClass=[MetafxMt5VisibleNative+Window]::new(2,101);$wrongClass.Class='#32770'
$wrongPid=[MetafxMt5VisibleNative+Window]::new(3,202)
$hidden=[MetafxMt5VisibleNative+Window]::new(4,101);$hidden.Visible=$false
$disabled=[MetafxMt5VisibleNative+Window]::new(5,101);$disabled.Enabled=$false
$child=[MetafxMt5VisibleNative+Window]::new(6,101);$child.Root=1
[MetafxMt5VisibleNative]::Rows=@($owned,$wrongClass,$wrongPid,$hidden,$disabled,$child,$main)
$observed=[ordered]@{unique=(Native-Reason 101)}
$script:processes=@((New-Process 101 'C:\fake\terminal64.exe'),(New-Process 202 'C:\other\terminal64.exe'))
$selected=Get-ExactTerminal 'C:\fake\terminal64.exe' 0 0
if($selected.Id -ne 101){throw 'executable selection changed'}
$script:TerminalRootHandle=[IntPtr]1
$root=[pscustomobject]@{Current=@{ProcessId=101;NativeWindowHandle=1;Name='Exact main caption';ClassName='MetaQuotes::MetaTrader::5.00'}}
$probe=New-Probe $selected $root
$observed['probeHandle']=$probe.windowHandle
$observed['probeTitle']=$probe.windowTitle
$observed['dynamicHandle']=[long]$selected.MainWindowHandle
# No fallback to another window after the signed root disappears or changes owner.
$main.Exists=$false
try{New-Probe $selected $root|Out-Null;$observed['missing']='accepted'}catch{$observed['missing']=$_.Exception.Message}
$main.Exists=$true;$main.Pid=202
try{New-Probe $selected $root|Out-Null;$observed['ownerDrift']='accepted'}catch{$observed['ownerDrift']=$_.Exception.Message}
$main.Pid=101
$script:processes=@((New-Process 101 'C:\fake\terminal64.exe'),(New-Process 202 'C:\fake\terminal64.exe'))
try{Get-ExactTerminal 'C:\fake\terminal64.exe' 0 0|Out-Null;$observed['processAmbiguity']='accepted'}catch{$observed['processAmbiguity']=$_.Exception.Message}
[MetafxMt5VisibleNative]::Rows=@($main,[MetafxMt5VisibleNative+Window]::new(7,101))
$observed['rootAmbiguity']=Native-Reason 101
[MetafxMt5VisibleNative]::Rows=@($owned,$wrongClass,$wrongPid,$hidden,$disabled,$child)
$observed['noMain']=Native-Reason 101
[MetafxMt5VisibleNative]::EnumFailure=$true
$observed['enumerationFailure']=Native-Reason 101
$observed|ConvertTo-Json -Compress
""".replace("METHOD", method).replace("PS_PATH", str(fixtures.PS_PATH).replace("'", "''"))
        run = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                              "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout), {
            "unique": 1, "probeHandle": 1, "probeTitle": "Exact main caption", "dynamicHandle": 99,
            "missing": "mt5_terminal_process_changed", "ownerDrift": "mt5_terminal_process_changed",
            "processAmbiguity": "mt5_selected_terminal_not_ready", "rootAmbiguity": "mt5_terminal_root_ambiguous",
            "noMain": 0, "enumerationFailure": "mt5_terminal_root_enumeration_failed",
        })

    def test_entrypoint_uses_discovery_only_before_signing_and_rebinds_before_publication(self):
        text = fixtures.PS_PATH.read_text(encoding="utf-8-sig")
        start = text.index("[IntPtr]$initialRootHandle =")
        end = text.index('"post_probe" {', start)
        body = text[start:end]
        self.assertIn("if ($expectedWindow -gt 0) { [IntPtr][long]$expectedWindow } else { Get-TerminalMainWindowExact $TerminalProcess }", body)
        self.assertNotIn("$TerminalProcess.MainWindowHandle", body)
        self.assertIn("$probeRoot = Get-BoundTerminalRoot $request ([IntPtr]$script:TerminalRootHandle)", body)
        self.assertIn("terminalProbe = New-Probe $TerminalProcess $probeRoot", body)
        signed = text[text.index("if ($ExpectedWindow -gt 0) {"):text.index("function Get-Root(")]
        self.assertNotIn("Get-TerminalMainWindowExact", signed)

    def test_root_disappearing_between_process_selection_and_binding_cannot_fall_back(self):
        text = fixtures.PS_PATH.read_text(encoding="utf-8-sig")
        start = text.index("[IntPtr]$initialRootHandle =")
        snippet = text[start:text.index("$script:TerminalRootHandle =", start)]
        script = r"""
$ErrorActionPreference='Stop'
function Fail($Code){throw $Code}
$TerminalProcess=[pscustomobject]@{MainWindowHandle=[IntPtr]99}
$script:rootCalls=0;$script:discoveryCalls=0
function Get-TerminalMainWindowExact($Process){$script:discoveryCalls++;return [IntPtr]::Zero}
function Get-Root($Process,$Handle){$script:rootCalls++;if($Handle -eq [IntPtr]::Zero){throw 'popup fallback invoked'};return @{handle=[long]$Handle}}
$expectedWindow=0;$reason='accepted'
try{SNIPPET}catch{$reason=$_.Exception.Message}
if($reason -cne 'mt5_selected_terminal_not_ready' -or $script:rootCalls -ne 0 -or $script:discoveryCalls -ne 1){throw 'disappeared main root accepted'}
$expectedWindow=1
SNIPPET
if($script:rootCalls -ne 1 -or $script:discoveryCalls -ne 1 -or $TerminalRoot.handle -ne 1){throw 'signed root rediscovered'}
'PASS'
""".replace("SNIPPET", snippet)
        run = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                              "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "PASS")


if __name__ == "__main__":
    unittest.main()
