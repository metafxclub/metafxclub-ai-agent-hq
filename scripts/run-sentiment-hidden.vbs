Option Explicit
Dim shell, fs, port, script, command, code
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
If Not WScript.Arguments.Named.Exists("Port") Then WScript.Quit 64
port = WScript.Arguments.Named.Item("Port")
If Not IsNumeric(port) Then WScript.Quit 64
port = CLng(port)
If port < 1024 Or port > 65535 Then WScript.Quit 64
script = fs.BuildPath(fs.GetParentFolderName(WScript.ScriptFullName), "sentiment-universe.ps1")
If Not fs.FileExists(script) Then WScript.Quit 66
command = Chr(34) & shell.ExpandEnvironmentStrings("%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe") & Chr(34) _
 & " -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File " & Chr(34) & script & Chr(34) _
 & " -Action Ensure -Port " & CStr(port)
code = shell.Run(command, 0, True)
WScript.Quit code
