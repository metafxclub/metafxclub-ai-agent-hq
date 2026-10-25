[CmdletBinding()]
param(
    [ValidateRange(1024,65535)][int]$Port = 4197,
    [switch]$Remove,
    [switch]$ValidateMigrationOnly,
    [string]$LegacyLauncherPath = '',
    [string]$LegacyPythonPath = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$hqRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$taskName = 'Metafxclub Sentiment Universe'
$wrapper = Join-Path $PSScriptRoot 'run-sentiment-hidden.vbs'
$wscript = Join-Path $env:SystemRoot 'System32\wscript.exe'
$arguments = '//B //NoLogo "{0}" /Port:{1}' -f $wrapper,$Port
$stateDirectory = Join-Path $env:LOCALAPPDATA 'Metafxclub\SentimentUniverse'
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()

function Test-OwnedTask($Task) {
    $actions = @($Task.Actions)
    if ($actions.Count -ne 1) { return $false }
    $expectedPrefix = '//B //NoLogo "{0}" /Port:' -f $wrapper
    if (-not [string]::Equals([string]$actions[0].Execute,$wscript,[StringComparison]::OrdinalIgnoreCase) -or -not ([string]$actions[0].Arguments).StartsWith($expectedPrefix,[StringComparison]::OrdinalIgnoreCase)) { return $false }
    $suffix = ([string]$actions[0].Arguments).Substring($expectedPrefix.Length)
    if ($suffix -notmatch '^\d{4,5}$' -or [int]$suffix -lt 1024 -or [int]$suffix -gt 65535) { return $false }
    try {
        $identity = [string]$Task.Principal.UserId
        $sid = if ($identity.StartsWith('S-1-')) { $identity } else { (New-Object Security.Principal.NTAccount($identity)).Translate([Security.Principal.SecurityIdentifier]).Value }
        return $sid -eq $currentUser.User.Value
    } catch { return $false }
}
function Remove-VerifiedLegacyShortcut([switch]$ValidateOnly, [string]$StartupDirectory = [Environment]::GetFolderPath('Startup')) {
    if ([bool]$LegacyLauncherPath -xor [bool]$LegacyPythonPath) { throw 'Legacy shortcut migration requires both exact launcher and Python paths.' }
    # The normal installer knows only its own installed package. External
    # prototype paths remain an explicit, reviewed migration input.
    $launcherPath = if ($LegacyLauncherPath) { $LegacyLauncherPath } else { Join-Path $hqRoot 'backend\local-runner\sentiment_universe\scripts\start-live.py' }
    $pythonPath = if ($LegacyPythonPath) { $LegacyPythonPath } else { Join-Path $hqRoot 'runner\.venv\Scripts\pythonw.exe' }
    if (-not [IO.Path]::IsPathRooted($launcherPath) -or -not [IO.Path]::IsPathRooted($pythonPath)) { throw 'Legacy shortcut migration requires absolute paths.' }
    $legacyLauncher = [IO.Path]::GetFullPath($launcherPath)
    $legacyPython = [IO.Path]::GetFullPath($pythonPath)
    if ([IO.Path]::GetFileName($legacyLauncher) -cne 'start-live.py' -or [IO.Path]::GetFileName($legacyPython) -ine 'pythonw.exe') { throw 'Legacy shortcut migration requires exact start-live.py and pythonw.exe paths.' }
    if (-not $StartupDirectory) { return }
    $shortcutPath = Join-Path $StartupDirectory 'Metafxclub Sentiment Universe.lnk'
    if (-not (Test-Path -LiteralPath $shortcutPath -PathType Leaf)) { return }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $targetMatches = [string]::Equals([IO.Path]::GetFullPath([string]$shortcut.TargetPath),$legacyPython,[StringComparison]::OrdinalIgnoreCase)
    # WScript retains an 8.3 path in Arguments even when GetFullPath expands
    # the expected launcher. Parse exactly one argument before normalizing it;
    # never accept extra switches or a matching path prefix.
    $shortcutArguments = [string]$shortcut.Arguments
    $argumentPath = $null
    if ($shortcutArguments -cmatch '^"([^"\r\n]+)"\z') { $argumentPath = $Matches[1] }
    elseif ($shortcutArguments -cmatch '^[^\s"]+\z') { $argumentPath = $shortcutArguments }
    $argsMatch = $false
    # IsPathRooted also accepts C:relative and \relative on .NET Framework;
    # their meaning depends on the shortcut's working directory/current drive.
    if ($argumentPath -and $argumentPath -cmatch '^(?:[A-Za-z]:[\\/]|\\\\[^\\/]+\\[^\\/]+\\)') {
        $argsMatch = [string]::Equals([IO.Path]::GetFullPath($argumentPath),$legacyLauncher,[StringComparison]::OrdinalIgnoreCase)
    }
    if ($targetMatches -and $argsMatch) {
        if ($ValidateOnly) { return }
        # The exact old shortcut is removed only after the replacement task exists.
        Remove-Item -LiteralPath $shortcutPath -Force
    } else {
        throw 'Existing Sentiment Startup shortcut has an unverified target or arguments and was preserved. Review its exact launcher/Python paths before migration; no successful migration is claimed.'
    }
}

# Reject an unresolved old launcher before registering another autostart path.
# Re-read its identity again immediately before removal after registration.
if ($ValidateMigrationOnly) {
    Remove-VerifiedLegacyShortcut -ValidateOnly
    Write-Host 'Sentiment legacy launcher identity check passed; no service or task was changed.'
    exit 0
}
if (-not $Remove) { Remove-VerifiedLegacyShortcut -ValidateOnly }
$previous = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($previous -and -not (Test-OwnedTask $previous)) { throw 'A different task owns this name; it was not overwritten or removed.' }
if ($Remove) {
    if ($previous) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop }
    if (Test-Path -LiteralPath $stateDirectory -PathType Container) {
        @{enabled=$false;taskName=$taskName;port=$Port;statePreserved=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stateDirectory 'autostart.json') -Encoding UTF8
    }
    exit 0
}
if (-not (Test-Path -LiteralPath $wrapper -PathType Leaf)) { throw 'Windowless sentiment wrapper is missing.' }
$statusRaw = & powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'sentiment-universe.ps1') -Action Status -Port $Port
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify sentiment service before registration.' }
$status = $statusRaw | ConvertFrom-Json
if ($status.status -cne 'healthy' -or $status.supervisorOwned -ne $true) { throw 'Sentiment must pass its own health and ownership checks before autostart registration.' }
$previousXml = if ($previous) { Export-ScheduledTask -TaskName $taskName } else { $null }
try {
    $action = New-ScheduledTaskAction -Execute $wscript -Argument $arguments -WorkingDirectory $hqRoot
    $logon = New-ScheduledTaskTrigger -AtLogOn -User $currentUser.Name
    $watchdog = New-ScheduledTaskTrigger -Once -At ([DateTime]::Now.AddMinutes(15)) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser.Name -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($logon,$watchdog) -Settings $settings -Principal $principal -Description 'Read-only market dashboard for this Windows user; independent of trading.' -Force | Out-Null
    $installed = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    if (-not (Test-OwnedTask $installed)) { throw 'The registered task identity did not match.' }
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
    @{enabled=$true;taskName=$taskName;port=$Port;scope='current_user';statePreserved=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stateDirectory 'autostart.json') -Encoding UTF8
} catch {
    $failure = $_
    $current = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($current -and (Test-OwnedTask $current)) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue }
    if ($previousXml) { Register-ScheduledTask -TaskName $taskName -Xml $previousXml -Force | Out-Null }
    throw $failure
}
Remove-VerifiedLegacyShortcut
Write-Host 'Sentiment autostart registered for this Windows user; HQ, MT5 and account state were preserved.'
