"""Native View menu and keyboard inspection, with no live UI or menu messages."""
import json
import os
import subprocess
import unittest

import test_ea_factory_visible_terminal_mt5 as fixtures


@unittest.skipUnless(os.name == "nt", "PowerShell/C# execution requires Windows")
class TesterNavigationDiagnosticTests(unittest.TestCase):
    def test_reveal_dispatch_is_one_exact_verified_menu_command_or_none(self):
        source = fixtures.PS_PATH.read_text(encoding="utf-8-sig")
        body = source[source.index("  public static void InvokeTesterRevealMenuExact("):
                      source.index("  public sealed class TESTERWINDOWDIAGNOSTIC")]
        script = r'''
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
public static class Reveal {
 public const uint GA_ROOT=2,GW_OWNER=4;public const int WM_COMMAND=273;
 public class MENUITEMSNAPSHOT {public uint CommandId=32846;public bool IsEnabled=true;}
 public class TESTERMENUDIAGNOSTICITEM {public MENUITEMSNAPSHOT Item=new MENUITEMSNAPSHOT();}
 public class TESTERVIEWMENUSNAPSHOT {public IntPtr MainMenu=(IntPtr)10,ViewMenu=(IntPtr)11;public MENUITEMSNAPSHOT ViewItem=new MENUITEMSNAPSHOT(),TesterItem=new MENUITEMSNAPSHOT();public TESTERMENUDIAGNOSTICITEM[] ViewItems=new[]{new TESTERMENUDIAGNOSTICITEM()};}
 public static string Fault;public static int Calls,Posts,ForegroundReads;public static int LastCommand;public static long LastTarget;
 static IntPtr GetForegroundWindow(){return Fault=="focusBefore"||(Fault=="focusAfter"&&ForegroundReads++>0)?(IntPtr)99:(IntPtr)1;}
 static uint GetWindowThreadProcessId(IntPtr h,out uint pid){pid=Fault=="pid"?999u:101u;return Fault=="thread"&&Calls>0?22u:11u;}
 static bool IsWindow(IntPtr h){return true;}static bool IsWindowVisible(IntPtr h){return Fault!="hiddenRoot";}static bool IsWindowEnabled(IntPtr h){return true;}
 static IntPtr GetAncestor(IntPtr h,uint f){return h;}static IntPtr GetWindow(IntPtr h,uint f){return Fault=="owner"?(IntPtr)99:IntPtr.Zero;}
 static string ReadWindowClassExact(IntPtr h){return Fault=="class"?"#32770":"MetaQuotes::MetaTrader::5.00";}
 static IntPtr GetMenu(IntPtr h){return Fault=="menuHandle"?(IntPtr)99:(IntPtr)10;}
 static bool SamePopupMenuItem(MENUITEMSNAPSHOT a,MENUITEMSNAPSHOT b){return a.CommandId==b.CommandId&&a.IsEnabled==b.IsEnabled;}
 static TESTERVIEWMENUSNAPSHOT ReadTesterViewMenuExact(uint pid,IntPtr root){
  Calls++;var r=new TESTERVIEWMENUSNAPSHOT();
  if(Fault=="ambiguous")throw new InvalidOperationException("mt5_tester_menu_command_ambiguous");
  if(Fault=="id")r.TesterItem.CommandId=16790;
  if(Fault=="disabled")r.TesterItem.IsEnabled=false;
  if(Fault=="duplicate")r.ViewItems=new[]{new TESTERMENUDIAGNOSTICITEM(),new TESTERMENUDIAGNOSTICITEM()};
  if(Fault=="changed"&&Calls==2)r.ViewMenu=(IntPtr)99;
  return r;
 }
 static bool PostMessage(IntPtr target,int message,IntPtr w,IntPtr l){
  if(message!=WM_COMMAND||l!=IntPtr.Zero)throw new Exception("wrong message");Posts++;LastCommand=w.ToInt32();LastTarget=target.ToInt64();return Fault!="postFailure";
 }
BODY
 public static string Run(string fault){Fault=fault;Calls=Posts=ForegroundReads=0;LastCommand=0;LastTarget=0;try{InvokeTesterRevealMenuExact(101,(IntPtr)1);return "sent";}catch(Exception e){return e.Message;}}
}
'@
$rows=@();foreach($fault in @('','focusBefore','focusAfter','pid','thread','hiddenRoot','owner','class','menuHandle','ambiguous','id','disabled','duplicate','changed','postFailure')){
 $reason=[Reveal]::Run($fault);$rows+=@{fault=$fault;reason=$reason;posts=[Reveal]::Posts;command=[Reveal]::LastCommand;target=[Reveal]::LastTarget}
};$rows|ConvertTo-Json -Compress
'''.replace("\nBODY\n", "\n" + body + "\n")
        run = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                              "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        for row in json.loads(run.stdout):
            with self.subTest(fault=row["fault"]):
                if row["fault"] in ("", "postFailure"):
                    self.assertEqual((row["posts"], row["target"], row["command"]), (1, 1, 32846))
                    self.assertEqual(row["reason"], "sent" if not row["fault"] else "mt5_tester_reveal_menu_dispatch_failed")
                else:
                    self.assertEqual(row["posts"], 0)
                    self.assertTrue(row["reason"].startswith("mt5_"))

    def test_selected_process_window_inventory_is_bounded_and_never_returns_captions(self):
        source = fixtures.PS_PATH.read_text(encoding="utf-8-sig")
        body = source[source.index("  public sealed class TESTERWINDOWDIAGNOSTIC"):
                      source.index("  public sealed class TESTERVIEWMENUSNAPSHOT")]
        for forbidden in ("PostMessage", "SendMessage", "SetForeground", "ShowWindow", "SelectExact", "SendKeys"):
            self.assertNotIn(forbidden, body)
        script = r'''
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;using System.Collections.Generic;
public static class Inventory {
 public const uint GA_ROOT=2,GW_OWNER=4;
 public struct RECT {public int Left,Top,Right,Bottom;}
 delegate bool EnumWindowProc(IntPtr h,IntPtr p);
 public static bool Many,Drift;static int rootReads;
 static bool EnumWindows(EnumWindowProc callback,IntPtr p){
  for(int n=1;n<=(Many?70:4);n++)if(!callback((IntPtr)n,p))return false;
  return true;
 }
 static bool EnumChildWindows(IntPtr root,EnumWindowProc callback,IntPtr p){
  if(root==(IntPtr)2){for(int n=100;n<=105;n++)if(!callback((IntPtr)n,p))return false;}
  return true;
 }
 static uint GetWindowThreadProcessId(IntPtr h,out uint pid){
  pid=h==(IntPtr)3||h==(IntPtr)104?999u:101u;
  if(h==(IntPtr)1&&Drift&&++rootReads>=4)pid=999;
  return 1;
 }
 static bool IsWindow(IntPtr h){return true;}
 static bool IsWindowVisible(IntPtr h){return h!=(IntPtr)2 && h!=(IntPtr)4;}
 static bool IsWindowEnabled(IntPtr h){return true;}
 static IntPtr GetAncestor(IntPtr h,uint f){return h.ToInt64()>=100?(IntPtr)2:h;}
 static IntPtr GetWindow(IntPtr h,uint f){return h==(IntPtr)2?(IntPtr)1:IntPtr.Zero;}
 static int GetDlgCtrlID(IntPtr h){var n=h.ToInt64();return n==100?32846:n==101?16790:n==102?10002:n==103?10490:77;}
 static string ReadWindowClassExact(IntPtr h){if(h==(IntPtr)3||h==(IntPtr)104)throw new Exception("foreign read");return h==(IntPtr)1?"MetaQuotes::MetaTrader::5.00":"#32770";}
 static string ReadWindowTextExact(IntPtr h){if(h==(IntPtr)3||h==(IntPtr)104)throw new Exception("foreign read");return h==(IntPtr)2?"Strategy Tester PRIVATE_ACCOUNT":"PRIVATE_SECRET";}
 static bool GetWindowRect(IntPtr h,out RECT r){r=new RECT{Left=3000,Top=100,Right=3400,Bottom=800};return true;}
BODY
 public static TESTERWINDOWINVENTORY Run(bool many,bool drift){Many=many;Drift=drift;rootReads=0;return ReadTesterWindowsDiagnostic(101,(IntPtr)1);}
}
'@
$ordinary=[Inventory]::Run($false,$false)
$bounded=[Inventory]::Run($true,$false)
$drift='accepted';try{$null=[Inventory]::Run($false,$true)}catch{$e=$_.Exception;while($e.InnerException){$e=$e.InnerException};$drift=$e.Message}
@{ordinary=$ordinary;bounded=$bounded;drift=$drift}|ConvertTo-Json -Depth 9 -Compress
'''.replace("\nBODY\n", "\n" + body + "\n")
        run = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                              "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn("PRIVATE", run.stdout)
        result = json.loads(run.stdout)
        ordinary = result["ordinary"]
        self.assertEqual([x["handle"] for x in ordinary["topLevelWindows"]], [1, 2])
        self.assertEqual([x["controlId"] for x in ordinary["testerControls"]], [32846, 16790, 10002, 10490])
        floating = ordinary["topLevelWindows"][1]
        self.assertEqual(floating["titleCategory"], "strategy_tester")
        self.assertEqual(floating["ownerHandle"], 1)
        self.assertEqual(floating["nativeRect"]["Left"], 3000)
        self.assertTrue(all(x["rootHandle"] == 2 for x in ordinary["testerControls"]))
        self.assertEqual(len(result["bounded"]["topLevelWindows"]), 16)
        self.assertTrue(result["bounded"]["truncated"])
        self.assertEqual(result["drift"], "mt5_tester_window_diagnostic_changed")

    def test_diagnostic_empty_label_does_not_relax_execution_reader_or_native_integrity(self):
        source = fixtures.PS_PATH.read_text(encoding="utf-8-sig")
        info = source[source.index("  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct MENUITEMINFO"):
                      source.index("  public sealed class POPUPMENUTOKEN")]
        execution = source[source.index("  static MENUITEMSNAPSHOT ReadPopupMenuItemExact("):
                           source.index("  static bool SamePopupMenuItem(")]
        diagnostic = source[source.index("  public sealed class TESTERMENUDIAGNOSTICITEM"):
                            source.index("  static TESTERMENUDIAGNOSTICITEM[] ListTesterMenuDiagnosticItems(")]
        self.assertIn("(!separator && String.IsNullOrWhiteSpace(text))", execution)
        script = r'''
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class MenuReaders {
INFO
 public static string Label=""; public static string Fault=""; static int reads;
 static bool IsMenu(IntPtr h){return h==(IntPtr)100;}
 static bool GetMenuItemInfo(IntPtr h,uint position,bool byPosition,ref MENUITEMINFO value){
  reads++;
  value.fType=0x100;value.fState=8;value.wID=33011;value.dwItemData=(UIntPtr)17;
  uint length=(uint)Label.Length;
  if(value.dwTypeData!=IntPtr.Zero){
   for(int i=0;i<Label.Length;i++)Marshal.WriteInt16(value.dwTypeData,i*2,(short)Label[i]);
   if(Fault=="sentinel")Marshal.WriteByte(value.dwTypeData,1024,0);
  }
  value.cch=Fault=="oversize"?512u:length;
  if(Fault=="length"&&reads==2)value.cch++;
  if(Fault=="type"&&reads==3)value.fType++;
  if(Fault=="state"&&reads==2)value.fState++;
  if(Fault=="id"&&reads==3)value.wID++;
  if(Fault=="data"&&reads==3)value.dwItemData=(UIntPtr)18;
  if(Fault=="submenu")value.hSubMenu=(IntPtr)999;
  return Fault!="native";
 }
EXECUTION
DIAGNOSTIC
 public static string Run(bool diagnostic,string label,string fault){
  Label=label;Fault=fault;reads=0;
  try {
   if(diagnostic){var r=ReadTesterMenuDiagnosticItem((IntPtr)100,0);return "ok:"+r.Type+":"+r.Item.Text;}
   return "ok:"+ReadPopupMenuItemExact((IntPtr)100,0).Text;
  }catch(Exception e){return e.Message;}
 }
}
'@
$rows=@()
foreach($fault in @('','native','oversize','length','sentinel','type','state','id','data','submenu')){
 $rows+=@{fault=$fault;diagnostic=[MenuReaders]::Run($true,'',$fault);execution=[MenuReaders]::Run($false,'',$fault)}
}
@{rows=$rows;spaceDiagnostic=[MenuReaders]::Run($true,'   ','');spaceExecution=[MenuReaders]::Run($false,'   ','');named=[MenuReaders]::Run($true,'Strategy Tester','')}|ConvertTo-Json -Depth 5 -Compress
'''.replace("\nINFO\n", "\n"+info+"\n").replace("\nEXECUTION\n", "\n"+execution+"\n").replace("\nDIAGNOSTIC\n", "\n"+diagnostic+"\n")
        run = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                              "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        for row in result["rows"]:
            if not row["fault"]:
                self.assertEqual(row["diagnostic"], "ok:256:")
                self.assertEqual(row["execution"], "mt5_popup_menu_text_invalid")
            else:
                self.assertEqual(row["diagnostic"], "mt5_tester_diagnostic_menu_item_invalid", row)
                self.assertEqual(row["execution"], "mt5_popup_menu_item_invalid", row)
        self.assertEqual(result["spaceDiagnostic"], "ok:256:   ")
        self.assertEqual(result["spaceExecution"], "mt5_popup_menu_text_invalid")
        self.assertEqual(result["named"], "ok:256:Strategy Tester")

    def test_real_menu_filter_and_navigation_metadata_use_only_bound_read_operations(self):
        source = fixtures.PS_PATH.read_text(encoding="utf-8-sig")
        body = source[source.index("  public sealed class TESTERVIEWMENUSNAPSHOT"):
                      source.index("  static MENUITEMSNAPSHOT FindPopupSubmenuExact(")]
        for forbidden in ("PostMessage", "SendMessage", "SetForeground", "SelectExact", "SendKeys", "EnumWindows"):
            self.assertNotIn(forbidden, body)
        script = r"""
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
public static class MetafxMt5VisibleNative {
 public const uint GA_ROOT=2,GW_OWNER=4;
 public class RECT {public int Left,Top,Right,Bottom;}
 public class MENUITEMSNAPSHOT {public int Position;public uint CommandId,State;public string Text;public bool IsEnabled=true,IsSeparator,HasSubmenu;public IntPtr SubmenuHandle;}
 public sealed class TESTERMENUDIAGNOSTICITEM { public uint Type; public MENUITEMSNAPSHOT Item; }
 public static Dictionary<long,MENUITEMSNAPSHOT[]> Menus=new Dictionary<long,MENUITEMSNAPSHOT[]>();
 public static int MenuCalls;public static bool Missing,Changed;public static uint RootPid=101;
 public static bool IsWindow(IntPtr h){return h==(IntPtr)1||h==(IntPtr)2||h==(IntPtr)99;}
 public static bool IsWindowVisible(IntPtr h){return true;}
 public static bool IsWindowEnabled(IntPtr h){return true;}
 public static IntPtr GetAncestor(IntPtr h,uint f){return h;}
 public static IntPtr GetWindow(IntPtr h,uint f){return IntPtr.Zero;}
 public static uint GetWindowThreadProcessId(IntPtr h,out uint pid){pid=h==(IntPtr)1?RootPid:h==(IntPtr)99?101u:999u;return pid==101?10u:20u;}
 public static string ReadWindowClassExact(IntPtr h){return h==(IntPtr)1?"MetaQuotes::MetaTrader::5.00":"#32770";}
 public static IntPtr GetMenu(IntPtr h){MenuCalls++;return Missing?IntPtr.Zero:Changed&&MenuCalls>1?(IntPtr)2000:(IntPtr)1000;}
 static bool IsMenu(IntPtr h){return Menus.ContainsKey(h.ToInt64());}
 static TESTERMENUDIAGNOSTICITEM[] ListTesterMenuDiagnosticItems(IntPtr h){if(!IsMenu(h))throw new Exception("bad menu");var result=new List<TESTERMENUDIAGNOSTICITEM>();foreach(var item in Menus[h.ToInt64()]) result.Add(new TESTERMENUDIAGNOSTICITEM {Type=0,Item=item});return result.ToArray();}
 static TESTERMENUDIAGNOSTICITEM ReadTesterMenuDiagnosticItem(IntPtr h,int pos){return new TESTERMENUDIAGNOSTICITEM{Type=0,Item=Menus[h.ToInt64()][pos]};}
 static bool SamePopupMenuItem(MENUITEMSNAPSHOT a,MENUITEMSNAPSHOT b){return Object.ReferenceEquals(a,b);}
 public static IntPtr GetForegroundWindow(){return (IntPtr)2;}
 public static IntPtr GetKeyboardLayout(uint thread){return thread==10?(IntPtr)0x041E:(IntPtr)0x0409;}
 public static bool GetWindowRect(IntPtr h,out RECT r){r=new RECT{Left=2500,Top=100,Right=2800,Bottom=500};return true;}
BODY
}
'@
$blank=[MetafxMt5VisibleNative+MENUITEMSNAPSHOT]::new();$blank.Text='';$blank.Position=0
$view=[MetafxMt5VisibleNative+MENUITEMSNAPSHOT]::new();$view.Text='&View';$view.Position=1;$view.HasSubmenu=$true;$view.SubmenuHandle=[IntPtr]1001
$tester=[MetafxMt5VisibleNative+MENUITEMSNAPSHOT]::new();$tester.Text="Strategy &Tester`tCtrl+R";$tester.Position=0;$tester.CommandId=33011
[MetafxMt5VisibleNative]::Menus[1000]=@($blank,$view);[MetafxMt5VisibleNative]::Menus[1001]=@($tester)
$results=@()
foreach($case in @('valid','checked','disabled','duplicateView','duplicateTester','noMenu','changed','wrongPid')){
 [MetafxMt5VisibleNative]::MenuCalls=0;[MetafxMt5VisibleNative]::Missing=$false;[MetafxMt5VisibleNative]::Changed=$false;[MetafxMt5VisibleNative]::RootPid=101
 [MetafxMt5VisibleNative]::Menus[1000]=@($blank,$view);[MetafxMt5VisibleNative]::Menus[1001]=@($tester);$tester.State=0;$tester.IsEnabled=$true
 switch($case){
  'checked'{$tester.State=8}
  'disabled'{$tester.IsEnabled=$false}
  'duplicateView'{[MetafxMt5VisibleNative]::Menus[1000]=@($blank,$view,$view)}
  'duplicateTester'{[MetafxMt5VisibleNative]::Menus[1001]=@($tester,$tester)}
  'noMenu'{[MetafxMt5VisibleNative]::Missing=$true}
  'changed'{[MetafxMt5VisibleNative]::Changed=$true}
  'wrongPid'{[MetafxMt5VisibleNative]::RootPid=999}
 }
 $reason='available';$row=$null
 try{$row=[MetafxMt5VisibleNative]::ReadTesterViewMenuExact(101,[IntPtr]1)}catch{$e=$_.Exception;while($e.InnerException){$e=$e.InnerException};$reason=$e.Message}
 $results+=@{case=$case;reason=$reason;commandId=if($row){$row.TesterItem.CommandId}else{0};checked=if($row){($row.TesterItem.State-band8)-ne0}else{$false};enabled=if($row){$row.TesterItem.IsEnabled}else{$false}}
}
[MetafxMt5VisibleNative]::RootPid=101;[MetafxMt5VisibleNative]::Missing=$false;[MetafxMt5VisibleNative]::Changed=$false;[MetafxMt5VisibleNative]::MenuCalls=0
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('PS_PATH',[ref]$tokens,[ref]$errors)
if($errors.Count -gt 0){throw ($errors|Out-String)}
$fn=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Read-TesterDiagnosticNavigation'},$true)
Invoke-Expression $fn.Extent.Text
function Fail($Code){throw $Code}
function Get-NativeOwner($Handle){[uint32]$pidValue=0;$null=[MetafxMt5VisibleNative]::GetWindowThreadProcessId($Handle,[ref]$pidValue);return $pidValue}
function Get-NativeClass($Handle){return [MetafxMt5VisibleNative]::ReadWindowClassExact($Handle)}
function Get-BoundTerminalRoot($Request,$Root){if($Root-ne[IntPtr]1){throw 'root changed'};return $rootElement}
$script:TerminalRootHandle=[IntPtr]1
$TerminalProcess=[pscustomobject]@{Id=101;MainWindowHandle=[IntPtr]99}
$TerminalProcess|Add-Member -MemberType ScriptMethod -Name Refresh -Value {}
$rootElement=[pscustomobject]@{Current=@{NativeWindowHandle=1}}
$navigation=Read-TesterDiagnosticNavigation $rootElement @{}
[MetafxMt5VisibleNative]::Missing=$true
$unavailable=Read-TesterDiagnosticNavigation $rootElement @{}
@{cases=$results;navigation=$navigation;unavailable=$unavailable}|ConvertTo-Json -Depth 12 -Compress
""".replace("BODY", body).replace("PS_PATH", str(fixtures.PS_PATH).replace("'", "''"))
        run = subprocess.run([str(fixtures.mt5._powershell_executable()), "-NoProfile", "-NonInteractive",
                              "-Command", script], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        cases = {row["case"]: row for row in result["cases"]}
        self.assertEqual(cases["valid"]["commandId"], 33011)
        self.assertTrue(cases["checked"]["checked"])
        self.assertFalse(cases["disabled"]["enabled"])
        for case, code in {"duplicateView": "mt5_tester_view_menu_ambiguous",
                           "duplicateTester": "mt5_tester_menu_command_ambiguous",
                           "noMenu": "mt5_tester_native_menu_unavailable", "changed": "mt5_tester_menu_changed",
                           "wrongPid": "mt5_tester_menu_root_unverified"}.items():
            self.assertEqual(cases[case]["reason"], code)
        navigation = result["navigation"]
        self.assertEqual(navigation["viewMenu"]["mainMenuHandle"], 1000)
        self.assertEqual(navigation["viewMenu"]["viewMenuHandle"], 1001)
        self.assertEqual(navigation["viewMenu"]["topItems"][0]["label"], "")
        self.assertEqual(navigation["viewMenu"]["topItems"][1]["label"], "&View")
        self.assertEqual(navigation["viewMenu"]["viewItems"][0]["commandId"], 33011)
        self.assertEqual(navigation["keyboard"]["rootLayout"], "000000000000041E")
        self.assertEqual(navigation["keyboard"]["foregroundLayout"], "0000000000000409")
        self.assertEqual(navigation["processConvenienceWindow"]["handle"], 99)
        self.assertEqual(navigation["processConvenienceWindow"]["nativeRect"]["left"], 2500)
        self.assertTrue(navigation["processConvenienceWindow"]["sameProcess"])
        self.assertFalse(result["unavailable"]["viewMenu"]["available"])
        self.assertEqual(result["unavailable"]["viewMenu"]["reasonCode"], "mt5_tester_native_menu_unavailable")


if __name__ == "__main__":
    unittest.main()
