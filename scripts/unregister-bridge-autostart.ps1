[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd("\")
$statePath = Join-Path $projectRoot "data\runtime\bridge-autostart.json"
$taskName = "Metafxclub AI Agent HQ Bridge"
$startupDirectory = [Environment]::GetFolderPath("Startup")
$legacyShortcutPath = if ([string]::IsNullOrWhiteSpace($startupDirectory)) {
    $null
}
else {
    Join-Path $startupDirectory "Metafxclub AI Agent HQ Bridge.lnk"
}

if (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    }
}

if ($legacyShortcutPath -and (Test-Path -LiteralPath $legacyShortcutPath -PathType Leaf)) {
    Remove-Item -LiteralPath $legacyShortcutPath -Force
}

$state = [ordered]@{
    version = 2
    enabled = $false
    scope = "current_user_scheduled_task"
    task_name = $taskName
    legacy_startup_shortcut_removed = $true
    unregistered_at = [DateTime]::UtcNow.ToString("o")
}
$stateDirectory = Split-Path -Parent $statePath
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$utf8 = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText($statePath, (($state | ConvertTo-Json -Depth 3) + [Environment]::NewLine), $utf8)

Write-Host "ยกเลิก Task เปิดและเฝ้าตรวจ Bridge อัตโนมัติแล้ว" -ForegroundColor Yellow
