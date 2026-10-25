[CmdletBinding()]
param(
    [ValidateRange(1024,65535)][int]$Port = 4197,
    [switch]$SkipAutostart,
    [switch]$OpenSetup,
    [switch]$OpenSetupIfNeeded,
    [string]$LegacyLauncherPath = '',
    [string]$LegacyPythonPath = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([bool]$LegacyLauncherPath -xor [bool]$LegacyPythonPath) { throw 'Legacy shortcut migration requires both exact launcher and Python paths.' }

function Test-SentimentSetupRequired($SetupStatus) {
    if ($null -eq $SetupStatus -or -not $SetupStatus.PSObject.Properties['encryptedCredentialsPresent'] -or $SetupStatus.encryptedCredentialsPresent -ne $true) { return $true }
    if (-not $SetupStatus.PSObject.Properties['mt5'] -or $null -eq $SetupStatus.mt5 -or -not $SetupStatus.mt5.PSObject.Properties['configured']) { return $true }
    # A selected terminal may be closed or awaiting live ticks. Its saved
    # selection is still valid; do not ask users to replace account settings.
    return $SetupStatus.mt5.configured -ne $true
}

function Get-SentimentSetupStatus {
    $response = $null
    try {
        $request = [Net.HttpWebRequest]::Create("http://127.0.0.1:$Port/api/setup")
        $request.Proxy = $null
        $request.Timeout = 5000
        $response = $request.GetResponse()
        $reader = New-Object IO.StreamReader($response.GetResponseStream())
        try { return $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
    } finally { if ($response) { $response.Close() } }
}
$lifecycle = Join-Path $PSScriptRoot 'sentiment-universe.ps1'
$register = Join-Path $PSScriptRoot 'register-sentiment-autostart.ps1'
$registerArgs = @('-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$register,'-Port',[string]$Port)
if ($LegacyLauncherPath -and $LegacyPythonPath) { $registerArgs += @('-LegacyLauncherPath',$LegacyLauncherPath,'-LegacyPythonPath',$LegacyPythonPath) }
# Resolve an old launcher's ownership before starting any new collector.
$preflightArgs = $registerArgs + @('-ValidateMigrationOnly')
& powershell.exe @preflightArgs
if ($LASTEXITCODE -ne 0) { throw 'Sentiment legacy launcher migration is unresolved; no new service was started by setup.' }
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $lifecycle -Action Ensure -Port $Port
if ($LASTEXITCODE -ne 0) { throw 'Sentiment service is not ready; HQ was not restarted.' }
if ($SkipAutostart) { $registerArgs += '-Remove' }
& powershell.exe @registerArgs
if ($LASTEXITCODE -ne 0) { throw 'Sentiment is running, but its autostart setup needs repair. Saved credentials were preserved.' }
Write-Host "One-time account setup: http://127.0.0.1:$Port/connect"
Write-Host 'Each Windows user connects their own Myfxbook account. Missing providers remain visibly unconfigured.'
$needsSetup = $false
if ($OpenSetupIfNeeded -and -not $OpenSetup) {
    try { $needsSetup = Test-SentimentSetupRequired (Get-SentimentSetupStatus) }
    catch {
        # Service health already passed. Present its local setup/status page
        # when onboarding status could not be verified; never reset state.
        $needsSetup = $true
        Write-Warning 'Cannot verify account setup status. Open the local setup page to review it.'
    }
}
if ($OpenSetup -or $needsSetup) {
    try { Start-Process "http://127.0.0.1:$Port/connect" }
    catch { Write-Warning "Open this setup link manually: http://127.0.0.1:$Port/connect" }
}
