"""Exercise production viewport/reveal logic with in-memory native geometry.

No real window, foreground, shortcut, clipboard or MetaTrader API is invoked.
"""
from __future__ import annotations

import json
import os
import subprocess
import unittest

import test_ea_factory_visible_terminal_mt5 as fixtures


@unittest.skipUnless(os.name == "nt", "PowerShell helper execution is Windows only")
class TesterViewportReadinessTests(unittest.TestCase):
    def test_real_helpers_reject_clipped_controls_and_restore_before_one_reveal(self):
        path = str(fixtures.PS_PATH).replace("'", "''")
        script = r"""
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -TypeDefinition @'
using System;
public static class MetafxMt5VisibleNative {
 public const uint GA_ROOT=2;
 public class RECT { public int Left,Top,Right,Bottom; public RECT(){} public RECT(int l,int t,int r,int b){Left=l;Top=t;Right=r;Bottom=b;} }
 public struct POINT { public int X,Y; }
 public static bool Minimized,Collapsed,Partial,NoConverge,WrongOwner,ReadFails,FocusFails,Hidden;
 public static IntPtr Foreground=(IntPtr)1;
 public static void Reset(){Minimized=Collapsed=Partial=NoConverge=WrongOwner=ReadFails=FocusFails=Hidden=false; Foreground=(IntPtr)1;}
 public static bool IsWindow(IntPtr h){return h.ToInt32()>=1 && h.ToInt32()<=4;}
 public static bool IsWindowVisible(IntPtr h){return !Hidden||h==(IntPtr)1;}
 public static int GetDlgCtrlID(IntPtr h){return h==(IntPtr)2?32846:0;}
 public static IntPtr GetAncestor(IntPtr h,uint f){return (IntPtr)1;}
 public static IntPtr GetParent(IntPtr h){return (IntPtr)(h.ToInt32()==3?4:h.ToInt32()==4?2:h.ToInt32()==2?1:0);}
 public static IntPtr GetForegroundWindow(){return Foreground;}
 public static bool GetWindowRect(IntPtr h,out RECT r){
  int n=h.ToInt32(); r=n==1?new RECT(0,0,1000,1000):n==2?(Collapsed?new RECT(0,900,1000,901):new RECT(0,800,1000,1000)):n==4?new RECT(10,970,1000,995):new RECT(900,972,Partial?1005:980,990);
  return !(ReadFails && n==3);
 }
 public static bool GetClientRect(IntPtr h,out RECT r){
  int n=h.ToInt32(); r=n==1?(Minimized?new RECT(0,2,0,0):new RECT(0,0,1000,1000)):n==2?new RECT(0,0,1000,Collapsed?0:200):new RECT(0,0,990,25);return true;
 }
 public static bool ClientToScreen(IntPtr h,ref POINT p){RECT r;GetWindowRect(h,out r);p.X+=r.Left;p.Y+=r.Top;return true;}
}
'@
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PS_PATH',[ref]$tokens,[ref]$errors)
if ($errors.Count -gt 0) {throw ($errors|Out-String)}
foreach ($name in @('Read-TesterDiagnosticClientRect','Read-TesterDiagnosticGeometry','Test-TesterControlViewport','Test-TesterPaneContentVisible','Test-TesterPaneCollapsed','Fail-TesterPaneReadiness','Ensure-TesterPaneVisible')) {
 $fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 $code=$fn.Extent.Text.Replace('[System.Windows.Automation.AutomationElement]$','[object]$')
 # The only actual OS mutation is replaced by a counter. Production branches,
 # target checks and readback remain verbatim; shorten only the failure wait.
 $code=$code.Replace('[MetafxMt5VisibleNative]::InvokeTesterRevealMenuExact([uint32]$TerminalProcess.Id, $signedRoot)','Send-TestShortcut')
 $code=$code.Replace('.AddSeconds(8)','.AddMilliseconds(100)').Replace('.AddSeconds(2)','.AddMilliseconds(100)')
 Invoke-Expression $code
}
function Fail($Code){throw $Code}
function Start-Sleep {param($Milliseconds)}
function New-Control($Handle){return [pscustomobject]@{Current=@{NativeWindowHandle=$Handle;IsOffscreen=$false;BoundingRectangle=@{Left=[double]::NegativeInfinity;Top=0;Right=[double]::PositiveInfinity;Bottom=1000}}}}
$script:TerminalRootHandle=[IntPtr]1
$TerminalProcess=[pscustomobject]@{Id=100}
$root=New-Control 1; $pane=New-Control 2; $start=New-Control 3
$request=[pscustomobject]@{expectedTerminalWindowHandle=1;requiredAutomationIds=@{testerPane='32846';start='1'}}
function Get-NativeOwner($Handle){if([MetafxMt5VisibleNative]::WrongOwner -and $Handle -eq [IntPtr]3){return 999};return 100}
function Get-NativeClass($Handle){if($script:wrongClass){return 'WrongClass'};return 'Afx:ControlBar:fixture'}
function Get-All($Root,$Condition){if($script:ambiguousPane){return @($pane,$pane)};return @($pane)}
function Find-ControlByIdPresent($Root,$Id){if($Id -eq '32846'){return $pane};if($Id -eq '1'){return $start};return $null}
function Get-BoundTerminalRoot($Request,$Expected){
 if ($Expected -ne [IntPtr]1 -or ($script:restored -and $script:drift)) {throw 'mt5_terminal_window_changed'}
 if ($script:restored -and $script:restoreFocusLost) {[MetafxMt5VisibleNative]::Foreground=[IntPtr]99}
 return $root
}
function Set-Foreground($Process,$Root){
 $script:focusCount++;$script:restored=$true
 if ($script:focusThrows) {throw 'visible_window_foreground_failed'}
 if (-not $script:restoreStuck) {[MetafxMt5VisibleNative]::Minimized=$false}
 if([MetafxMt5VisibleNative]::FocusFails){[MetafxMt5VisibleNative]::Foreground=[IntPtr]99}
}
function Send-TestShortcut {
 if(-not $script:restored -or [MetafxMt5VisibleNative]::Foreground -ne [IntPtr]1){throw 'shortcut before restore'}
 $script:shortcutCount++
 [MetafxMt5VisibleNative]::Hidden=$false
 if ($script:revealFocusLost) {[MetafxMt5VisibleNative]::Foreground=[IntPtr]99}
 if(-not [MetafxMt5VisibleNative]::NoConverge){[MetafxMt5VisibleNative]::Collapsed=$false}
}
$results=@()
foreach($case in @('visible','collapsed','hidden','minimized_open','minimized_collapsed','minimized_hidden','ambiguous_pane','wrong_class','partial','read_failure','wrong_owner','root_drift','focus_failure','focus_throws','restore_focus_lost','restore_timeout','reveal_focus_lost','no_convergence')) {
 [MetafxMt5VisibleNative]::Reset();$script:focusCount=0;$script:shortcutCount=0;$script:restored=$false;$script:drift=$false
 $script:focusThrows=$false;$script:restoreFocusLost=$false;$script:restoreStuck=$false;$script:revealFocusLost=$false;$script:ambiguousPane=$false;$script:wrongClass=$false
 switch($case){
  'collapsed'{[MetafxMt5VisibleNative]::Collapsed=$true}
  'hidden'{[MetafxMt5VisibleNative]::Collapsed=$true;[MetafxMt5VisibleNative]::Hidden=$true}
  'minimized_hidden'{[MetafxMt5VisibleNative]::Minimized=$true;[MetafxMt5VisibleNative]::Collapsed=$true;[MetafxMt5VisibleNative]::Hidden=$true}
  'ambiguous_pane'{[MetafxMt5VisibleNative]::Collapsed=$true;$script:ambiguousPane=$true}
  'wrong_class'{[MetafxMt5VisibleNative]::Collapsed=$true;$script:wrongClass=$true}
  'minimized_open'{[MetafxMt5VisibleNative]::Minimized=$true}
  'minimized_collapsed'{[MetafxMt5VisibleNative]::Minimized=$true;[MetafxMt5VisibleNative]::Collapsed=$true}
  'partial'{[MetafxMt5VisibleNative]::Partial=$true}
  'read_failure'{[MetafxMt5VisibleNative]::ReadFails=$true}
  'wrong_owner'{[MetafxMt5VisibleNative]::WrongOwner=$true}
  'root_drift'{[MetafxMt5VisibleNative]::Minimized=$true;$script:drift=$true}
  'focus_failure'{[MetafxMt5VisibleNative]::Minimized=$true;[MetafxMt5VisibleNative]::FocusFails=$true}
  'focus_throws'{[MetafxMt5VisibleNative]::Minimized=$true;$script:focusThrows=$true}
  'restore_focus_lost'{[MetafxMt5VisibleNative]::Minimized=$true;$script:restoreFocusLost=$true}
  'restore_timeout'{[MetafxMt5VisibleNative]::Minimized=$true;$script:restoreStuck=$true}
  'reveal_focus_lost'{[MetafxMt5VisibleNative]::Hidden=$true;[MetafxMt5VisibleNative]::Collapsed=$true;$script:revealFocusLost=$true}
  'no_convergence'{[MetafxMt5VisibleNative]::Hidden=$true;[MetafxMt5VisibleNative]::Collapsed=$true;[MetafxMt5VisibleNative]::NoConverge=$true}
 }
 $reason='ready'
 try{Ensure-TesterPaneVisible $request $root}catch{$reason=$_.Exception.Message}
 $results += [ordered]@{case=$case;reason=$reason;focusCount=$script:focusCount;shortcutCount=$script:shortcutCount}
}
[MetafxMt5VisibleNative]::Reset()
# Execute the real root-only geometry branch with no Tester controls at all.
# Nonfinite UIA rectangles remain unavailable instead of invalid JSON numbers.
$rootOnly=Read-TesterDiagnosticGeometry @{root=$root} $request $true
if($rootOnly.controls.Count -ne 1 -or $rootOnly.startAncestors.Count -ne 0 -or
   $rootOnly.controls.root.nativeRect.right -ne 1000 -or
   $rootOnly.controls.root.uiaRectAvailable -ne $false -or $null -ne $rootOnly.controls.root.uiaRect){throw 'invalid root-only geometry'}
$results|ConvertTo-Json -Compress
""".replace("PS_PATH", path)
        run = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                              "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        results = {row["case"]: row for row in json.loads(run.stdout)}
        expected = {
            "visible": ("ready", 0, 0),
            "collapsed": ("mt5_tester_pane_collapsed", 1, 0),
            "hidden": ("ready", 1, 1),
            "minimized_hidden": ("ready", 1, 1),
            "ambiguous_pane": ("mt5_tester_pane_geometry_unverified", 1, 0),
            "wrong_class": ("mt5_tester_pane_geometry_unverified", 1, 0),
            "minimized_open": ("ready", 1, 0),
            "minimized_collapsed": ("mt5_tester_pane_collapsed", 1, 0),
            "partial": ("mt5_tester_pane_partially_clipped", 0, 0),
            "read_failure": ("mt5_tester_pane_geometry_unverified", 0, 0),
            "wrong_owner": ("mt5_tester_pane_geometry_unverified", 0, 0),
            "root_drift": ("mt5_terminal_window_changed", 1, 0),
            "focus_failure": ("mt5_tester_pane_focus_before_reveal_failed", 1, 0),
            "focus_throws": ("mt5_tester_pane_focus_before_reveal_failed", 1, 0),
            "restore_focus_lost": ("mt5_tester_pane_restore_focus_lost", 1, 0),
            "restore_timeout": ("mt5_tester_pane_restore_timeout", 1, 0),
            "reveal_focus_lost": ("mt5_tester_pane_reveal_focus_lost", 1, 1),
            "no_convergence": ("mt5_tester_pane_collapsed", 1, 1),
        }
        for name, want in expected.items():
            with self.subTest(case=name):
                actual = results[name]
                self.assertEqual((actual["reason"], actual["focusCount"], actual["shortcutCount"]), want)


if __name__ == "__main__":
    unittest.main()
