Option Explicit

Const EXIT_BAD_ARGUMENT = 64
Const EXIT_MISSING_FILE = 66

Dim shell
Dim fileSystem
Dim scriptDirectory
Dim lifecyclePath
Dim powershellPath
Dim portText
Dim portNumber
Dim command
Dim exitCode

Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

If Not WScript.Arguments.Named.Exists("Port") Then
    WScript.Quit EXIT_BAD_ARGUMENT
End If

portText = Trim(CStr(WScript.Arguments.Named.Item("Port")))
If Len(portText) = 0 Or Not IsNumeric(portText) Then
    WScript.Quit EXIT_BAD_ARGUMENT
End If

On Error Resume Next
portNumber = CLng(portText)
If Err.Number <> 0 Then
    Err.Clear
    On Error GoTo 0
    WScript.Quit EXIT_BAD_ARGUMENT
End If
On Error GoTo 0

If portNumber < 1024 Or portNumber > 65535 Then
    WScript.Quit EXIT_BAD_ARGUMENT
End If

scriptDirectory = fileSystem.GetParentFolderName(WScript.ScriptFullName)
lifecyclePath = fileSystem.BuildPath(scriptDirectory, "start-local-bridge.ps1")
powershellPath = shell.ExpandEnvironmentStrings("%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe")

If Not fileSystem.FileExists(lifecyclePath) Or Not fileSystem.FileExists(powershellPath) Then
    WScript.Quit EXIT_MISSING_FILE
End If

command = QuoteArgument(powershellPath) _
    & " -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass" _
    & " -File " & QuoteArgument(lifecyclePath) _
    & " -Action Ensure -Port " & CStr(portNumber)

' Window style 0 keeps both the script host and the PowerShell child invisible.
' Waiting for completion preserves the lifecycle script exit code for Task Scheduler.
exitCode = shell.Run(command, 0, True)
WScript.Quit exitCode

Function QuoteArgument(ByVal value)
    QuoteArgument = Chr(34) & Replace(CStr(value), Chr(34), Chr(34) & Chr(34)) & Chr(34)
End Function
