[CmdletBinding()]
param(
    [ValidateRange(1, 30)]
    [int]$WatchdogMinutes = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd("\")
$lifecyclePath = Join-Path $PSScriptRoot "start-local-bridge.ps1"
$endpointPath = Join-Path $projectRoot "data\runtime\bridge-endpoint.json"
$statePath = Join-Path $projectRoot "data\runtime\bridge-autostart.json"
$taskName = "Metafxclub AI Agent HQ Bridge"
$legacyStartupDirectory = [Environment]::GetFolderPath("Startup")
$legacyShortcutPath = if ([string]::IsNullOrWhiteSpace($legacyStartupDirectory)) {
    $null
}
else {
    Join-Path $legacyStartupDirectory "Metafxclub AI Agent HQ Bridge.lnk"
}

if (-not (Test-Path -LiteralPath $lifecyclePath -PathType Leaf)) {
    throw "ไม่พบตัวควบคุม Local Bridge: $lifecyclePath"
}
if (-not (Test-Path -LiteralPath $endpointPath -PathType Leaf)) {
    throw "ยังไม่มี Local endpoint ที่ยืนยัน กรุณาเปิด Bridge และยืนยันพอร์ตก่อน"
}

$endpoint = Get-Content -LiteralPath $endpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
$confirmedPort = [int]$endpoint.port
if ([string]$endpoint.host -cne "127.0.0.1" -or $confirmedPort -lt 1024 -or $confirmedPort -gt 65535) {
    throw "Endpoint ที่บันทึกไว้ไม่ใช่ Local loopback ที่อนุญาต"
}

$requiredCommands = @(
    "New-ScheduledTaskAction",
    "New-ScheduledTaskTrigger",
    "New-ScheduledTaskSettingsSet",
    "New-ScheduledTaskPrincipal",
    "Register-ScheduledTask",
    "Get-ScheduledTask",
    "Export-ScheduledTask",
    "Unregister-ScheduledTask"
)
foreach ($commandName in $requiredCommands) {
    if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "Windows เครื่องนี้ไม่มีคำสั่ง Task Scheduler ที่ต้องใช้ ($commandName)"
    }
}

$powerShellPath = (Get-Command powershell.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$arguments = '-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}" -Action Ensure -Port {1}' -f $lifecyclePath, $confirmedPort
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction `
    -Execute $powerShellPath `
    -Argument $arguments `
    -WorkingDirectory $projectRoot
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
$watchdogTrigger = New-ScheduledTaskTrigger `
    -Once `
    -At ([DateTime]::Now.AddMinutes($WatchdogMinutes)) `
    -RepetitionInterval (New-TimeSpan -Minutes $WatchdogMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -Hidden `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
$principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType Interactive `
    -RunLevel Limited

$previousTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
$previousTaskXml = if ($previousTask) { Export-ScheduledTask -TaskName $taskName } else { $null }
$registeredReplacement = $false
$legacyShortcutRemoved = $false

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger @($logonTrigger, $watchdogTrigger) `
        -Settings $settings `
        -Principal $principal `
        -Description "เปิดและเฝ้าตรวจ Metafxclub AI Agent HQ Local Bridge สำหรับผู้ใช้ปัจจุบัน" `
        -Force | Out-Null
    $registeredReplacement = $true

    $registeredTask = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    if (-not $registeredTask) {
        throw "สร้าง Scheduled Task สำหรับ Bridge ไม่สำเร็จ"
    }

    & powershell.exe `
        -NoLogo `
        -NoProfile `
        -NonInteractive `
        -ExecutionPolicy Bypass `
        -File $lifecyclePath `
        -Action Ensure `
        -Port $confirmedPort | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "ลงทะเบียน Task แล้ว แต่ Bridge ยังไม่ผ่าน Health check ที่พอร์ต $confirmedPort"
    }

    $state = [ordered]@{
        version = 2
        enabled = $true
        scope = "current_user_scheduled_task"
        host = "127.0.0.1"
        confirmed_port = $confirmedPort
        task_name = $taskName
        user = $currentUser
        watchdog_minutes = $WatchdogMinutes
        restart_count = 3
        restart_interval_minutes = 1
        legacy_startup_shortcut_removed = $legacyShortcutRemoved
        registered_at = [DateTime]::UtcNow.ToString("o")
    }
    $stateDirectory = Split-Path -Parent $statePath
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($statePath, (($state | ConvertTo-Json -Depth 4) + [Environment]::NewLine), $utf8)
}
catch {
    $registrationError = [string]$_.Exception.Message
    if ($registeredReplacement) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    }
    if ($previousTaskXml) {
        Register-ScheduledTask -TaskName $taskName -Xml $previousTaskXml -Force | Out-Null
    }
    throw "เปิด Autostart ไม่สำเร็จและย้อนกลับ Task เดิมแล้ว: $registrationError"
}

if ($legacyShortcutPath -and (Test-Path -LiteralPath $legacyShortcutPath -PathType Leaf)) {
    try {
        Remove-Item -LiteralPath $legacyShortcutPath -Force
        $legacyShortcutRemoved = -not (Test-Path -LiteralPath $legacyShortcutPath -PathType Leaf)
        $state["legacy_startup_shortcut_removed"] = $legacyShortcutRemoved
        [IO.File]::WriteAllText($statePath, (($state | ConvertTo-Json -Depth 4) + [Environment]::NewLine), $utf8)
    }
    catch {
        Write-Warning "Autostart ผ่านแล้ว แต่ลบ Startup shortcut รุ่นเก่าไม่สำเร็จ กรุณาลบไฟล์นี้ภายหลัง: $legacyShortcutPath"
    }
}

Write-Host "เปิด Bridge อัตโนมัติและระบบตรวจซ้ำผ่าน Task Scheduler แล้ว" -ForegroundColor Green
Write-Host "Local endpoint ที่ยืนยัน: http://127.0.0.1:$confirmedPort/"
Write-Host "ระบบลองใหม่เมื่อเริ่มไม่สำเร็จ และตรวจ Bridge ทุก $WatchdogMinutes นาที"
Write-Host "ระบบเปิดเฉพาะ Bridge แบบซ่อน และไม่เปิด Browser หรือ MT4/MT5 เอง"
