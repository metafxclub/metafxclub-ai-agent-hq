"""Execute report-export control flow with fake native calls, never a real UI."""
import json
import os
import subprocess
import unittest

import test_ea_factory_visible_terminal_mt5 as fixtures


@unittest.skipUnless(os.name == "nt", "PowerShell helper execution is Windows only")
class ReportExportFailureCodeTests(unittest.TestCase):
    def test_real_host_filter_classifies_without_admitting_duplicates_or_wrong_control_type(self):
        script = r'''
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName UIAutomationClient
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PS_PATH',[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
foreach($name in @('Fail','Get-ExactNativePopupMenuHost')){
 $fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 # Replace only the OS desktop provider. All production filtering and failure
 # classification below execute unchanged against in-memory observations.
 $code=$fn.Extent.Text.Replace('$desktop = [System.Windows.Automation.AutomationElement]::RootElement','$desktop = $script:FakeDesktop')
 Invoke-Expression $code
}
$TerminalProcess=[pscustomobject]@{Id=10}
$script:FakeDesktop=[pscustomobject]@{}
$script:FakeDesktop|Add-Member ScriptMethod FindAll {param($Scope,$Condition) if($script:readFails){throw 'private read failure'}; return $script:candidates}
function New-TestHost($Handle=4,$Type=50033,$OwnerPid=10,$Offscreen=$false,$Enabled=$true,$Class='#32768'){
 return [pscustomobject]@{Current=[pscustomobject]@{ProcessId=$OwnerPid;ControlType=[pscustomobject]@{Id=$Type};IsOffscreen=$Offscreen;IsEnabled=$Enabled;ClassName=$Class;NativeWindowHandle=$Handle}}
}
$rows=@();$base='mt5_report_export_command_not_verified_popup_host_unverified'
foreach($mode in @('none','duplicate','distinct','wrong_type','foreign','hidden','disabled','wrong_class','read','valid','legacy')){
 $script:readFails=$mode -ceq 'read'
 $script:candidates=switch($mode){
  'none' {@()};'duplicate' {@((New-TestHost),(New-TestHost))};'distinct' {@((New-TestHost),(New-TestHost 5))}
  'wrong_type' {@(New-TestHost 4 50009)};'foreign' {@(New-TestHost 4 50033 11)}
  'hidden' {@(New-TestHost 4 50033 10 $true)};'disabled' {@(New-TestHost 4 50033 10 $false $false)}
  'wrong_class' {@(New-TestHost 4 50033 10 $false $true 'Other')};'legacy' {@((New-TestHost),(New-TestHost))}
  default {@(New-TestHost)}
 }
 $reason='';$handle=0
 try{$hostElement=Get-ExactNativePopupMenuHost 0 $(if($mode -ceq 'legacy'){'legacy_code'}else{$base});$handle=$hostElement.Current.NativeWindowHandle}catch{$reason=$_.Exception.Message}
 $rows += [pscustomobject]@{mode=$mode;reason=$reason;handle=$handle}
}
$rows|ConvertTo-Json -Compress
'''.replace("PS_PATH", str(fixtures.PS_PATH).replace("'", "''"))
        result = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {row["mode"]: row for row in json.loads(result.stdout)}
        base = "mt5_report_export_command_not_verified_popup_host_unverified_"
        for mode, suffix in {"none": "no_host", "duplicate": "duplicate_handle",
                             "distinct": "distinct_handles", "wrong_type": "control_type_mismatch",
                             "foreign": "no_host", "hidden": "no_host", "disabled": "no_host",
                             "wrong_class": "no_host", "read": "read_failed"}.items():
            with self.subTest(mode=mode):
                self.assertEqual(rows[mode]["reason"], base + suffix)
                self.assertEqual(rows[mode]["handle"], 0)
                self.assertLessEqual(len(rows[mode]["reason"]), 100)
        self.assertEqual(rows["legacy"]["reason"], "legacy_code")
        self.assertEqual((rows["valid"]["reason"], rows["valid"]["handle"]), ("", 4))

    def test_real_command_failures_are_stage_specific_and_never_dispatch(self):
        script = r'''
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Add-Type -TypeDefinition @'
using System;
public static class MetafxMt5VisibleNative {
 public static string Mode;
 public static int Dispatches, Opens, Cleanups;
 public class Item { public string Text; public uint CommandId; public bool IsEnabled=true,IsSeparator=false,HasSubmenu=true; public IntPtr SubmenuHandle=(IntPtr)3; }
 public class Token { public Item[] Items; }
 public static IntPtr FindOwnedDialogExact(uint p,IntPtr r,string[] n){return IntPtr.Zero;}
 public static void OpenListContextMenuExact(IntPtr l,uint p,IntPtr r,int c){Opens++;if(Mode=="context")throw new InvalidOperationException("private native detail");}
 public static Token CapturePopupMenuTokenExact(IntPtr h,uint p,IntPtr r){if(Mode=="native")throw new InvalidOperationException("mt5_popup_menu_changed");return new Token {Items=Mode=="candidate"?new Item[0]:new[]{new Item{Text="Report",CommandId=0}}};}
 public static Item AssertPopupSubmenuCommandFromTokenExact(object t,uint p,IntPtr r,string a,string b,uint id){return new Item{Text=b,CommandId=id};}
 public static void AssertListFocusExact(IntPtr h,uint p,IntPtr r,int c){if(Mode=="focus")throw new InvalidOperationException("private focus detail");}
 public static void InvokePopupSubmenuCommandExact(object t,uint p,IntPtr r,string a,string b,uint id){Dispatches++;}
 public static void DismissPopupMenuExact(object t,uint p,IntPtr r){Cleanups++;if(Mode=="focus")throw new InvalidOperationException("private cleanup detail");}
}
'@
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PS_PATH',[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
foreach($name in @('Fail','Resolve-PopupDispatchFailureCode','Invoke-TesterResultsReportCommandExact')){
 $fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 Invoke-Expression $fn.Extent.Text
}
$TerminalProcess=[pscustomobject]@{Id=10}
function Get-TestBinding([int]$Handle=2,[int]$Root=1){return @{listHandle=[IntPtr]$Handle;controlId=123;root=[pscustomobject]@{Current=[pscustomobject]@{NativeWindowHandle=$Root}}}}
function Focus-UniqueResultsTable($Request,$ExpectedTabName){return (Get-TestBinding $(if([MetafxMt5VisibleNative]::Mode -ceq 'initial'){99}else{2}))}
function Get-ExactTesterResultsList($Request,$ExpectedTabName,$Code,$ExpectedControlId){
 if([MetafxMt5VisibleNative]::Mode -ceq 'rebind'){Fail $Code}
 if([MetafxMt5VisibleNative]::Mode -ceq 'busy'){Fail 'mt5_tester_not_idle'}
 return (Get-TestBinding 2 $(if([MetafxMt5VisibleNative]::Mode -ceq 'root'){99}else{1}))
}
function Get-ExactNativePopupMenuHost($TimeoutMilliseconds,$Code){
 if(($TimeoutMilliseconds -eq 3000 -and [MetafxMt5VisibleNative]::Mode -ceq 'host') -or
    ($TimeoutMilliseconds -eq 0 -and [MetafxMt5VisibleNative]::Mode -ceq 'host_rebind')){Fail $Code}
 return [pscustomobject]@{Current=[pscustomobject]@{NativeWindowHandle=$(if($TimeoutMilliseconds -eq 0 -and [MetafxMt5VisibleNative]::Mode -ceq 'popup'){99}else{4})}}
}
function Wait-ExactOwnedFileDialog($Names,$Code){return [IntPtr]88}
$rows=@()
foreach($mode in @('initial','context','host','candidate','rebind','root','focus','host_rebind','popup','native','busy','success')){
 [MetafxMt5VisibleNative]::Mode=$mode;[MetafxMt5VisibleNative]::Dispatches=0;[MetafxMt5VisibleNative]::Opens=0;[MetafxMt5VisibleNative]::Cleanups=0
 $reason='';$dialog=0
 try{$dialog=(Invoke-TesterResultsReportCommandExact ([pscustomobject]@{}) 'Backtest' ([IntPtr]2) 'mt5_report_export_command_not_verified').ToInt64()}catch{$reason=$_.Exception.Message}
 $rows += [pscustomobject]@{mode=$mode;reason=$reason;dialog=$dialog;dispatches=[MetafxMt5VisibleNative]::Dispatches;opens=[MetafxMt5VisibleNative]::Opens;cleanups=[MetafxMt5VisibleNative]::Cleanups}
}
$rows|ConvertTo-Json -Depth 4 -Compress
'''.replace("PS_PATH", str(fixtures.PS_PATH).replace("'", "''"))
        result = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {row["mode"]: row for row in json.loads(result.stdout)}
        suffixes = {
            "initial": "initial_list_changed", "context": "context_open_failed",
            "host": "popup_host_unverified", "candidate": "candidate_count_invalid",
            "rebind": "results_rebind_unverified", "root": "results_binding_changed",
            "focus": "results_focus_lost", "host_rebind": "popup_rebind_unverified",
            "popup": "popup_identity_changed", "native": "popup_bind_menu_changed",
        }
        for mode, suffix in suffixes.items():
            with self.subTest(mode=mode):
                self.assertEqual(rows[mode]["reason"], "mt5_report_export_command_not_verified_" + suffix)
                self.assertEqual(rows[mode]["dispatches"], 0)
                self.assertEqual(rows[mode]["dialog"], 0)
        self.assertEqual(rows["busy"]["reason"], "mt5_tester_not_idle")
        self.assertEqual(rows["busy"]["dispatches"], 0)
        self.assertEqual(rows["focus"]["cleanups"], 1)  # cleanup cannot mask primary reason
        self.assertEqual((rows["success"]["reason"], rows["success"]["dialog"], rows["success"]["dispatches"]), ("", 88, 1))


if __name__ == "__main__":
    unittest.main()
