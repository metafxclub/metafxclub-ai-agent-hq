param([string]$SourceRoot = (Split-Path -Parent $PSScriptRoot))

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# This invokes the real installer only on an ephemeral GitHub-hosted runner.
# Never set GITHUB_ACTIONS here or turn this into a local-install bypass.
if ([string]$env:GITHUB_ACTIONS -cne 'true' -or -not $env:RUNNER_TEMP) {
    throw 'Isolated installer smoke requires actual GitHub Actions and RUNNER_TEMP.'
}
$ciSmokeRoot = Join-Path ([IO.Path]::GetFullPath($env:RUNNER_TEMP)) ('hq-installer-smoke-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $ciSmokeRoot | Out-Null
$ciSourceRoot = [IO.Path]::GetFullPath($SourceRoot)
$ciArchive = Join-Path $ciSmokeRoot 'fixture-source.zip'
$ciPackageRoot = Join-Path $ciSmokeRoot 'package'
$ciDataRoot = Join-Path $ciSmokeRoot 'LocalAppData'
$ciInstalled = Join-Path $ciDataRoot 'Metafxclub\AI-Agent-HQ'
$ciOriginalLocal = $env:LOCALAPPDATA
$ciOriginalAppData = $env:APPDATA
$ciOriginalCodex = $env:CODEX_HOME
$ciPort = 0
$ciLifecycle = Join-Path $ciInstalled 'scripts\start-local-bridge.ps1'
$ciUtf8 = New-Object Text.UTF8Encoding($false)

function Invoke-FixtureInstaller {
    param([string[]]$ExtraArguments)
    & powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass `
        -File (Join-Path $ciPackageRoot 'installer\install.ps1') `
        -Port $ciPort -EndpointConfirmed -SkipShortcuts -SkipAutostart -SkipGoogleSetup -PackageSmoke @ExtraArguments | Out-Host
    return [int]$LASTEXITCODE
}

try {
    # HEAD archive includes no worktree credentials, runtime data or local venv.
    & git -C $ciSourceRoot archive --format=zip --output=$ciArchive HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot archive committed candidate.' }
    Expand-Archive -LiteralPath $ciArchive -DestinationPath $ciPackageRoot
    # Inert syntax fixture only: never log in, publish or upload this package.
    # Release packaging continues to inject its real client from CI secrets.
    $ciClientPath = Join-Path $ciPackageRoot 'backend\local-runner\google_oauth_native_client.txt'
    $ciDummySecret = 'GOC' + 'SPX-' + ('INERT_SMOKE_FIXTURE_' * 2)
    [IO.File]::WriteAllText($ciClientPath, "client_id=inert-smoke-fixture.apps.googleusercontent.com`nclient_secret=$ciDummySecret`n", $ciUtf8)
    $env:LOCALAPPDATA = $ciDataRoot
    $env:APPDATA = Join-Path $ciSmokeRoot 'AppData'
    $env:CODEX_HOME = Join-Path $ciSmokeRoot 'CodexHome'
    foreach ($ciDirectory in @($env:LOCALAPPDATA, $env:APPDATA, $env:CODEX_HOME)) {
        New-Item -ItemType Directory -Path $ciDirectory -Force | Out-Null
    }
    $ciListener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
    try { $ciListener.Start(); $ciPort = ([Net.IPEndPoint]$ciListener.LocalEndpoint).Port }
    finally { $ciListener.Stop() }
    if ($ciPort -in @(4186,4197) -or $ciPort -lt 1024) { throw 'Unsafe smoke port selected.' }

    $ciFreshExit = Invoke-FixtureInstaller -ExtraArguments @('-SkipLaunch')
    if ($ciFreshExit -ne 0) { throw "Fresh package install/health/stop failed: $ciFreshExit" }
    if (-not (Test-Path -LiteralPath $ciLifecycle -PathType Leaf)) { throw 'Installed lifecycle script missing.' }

    # Upgrade mode must launch the isolated Bridge to check health. Its existing
    # contract disallows SkipLaunch; shortcuts, autostart and Google stay off.
    $ciVersion = Join-Path $ciInstalled 'VERSION'
    $ciOldVersion = '0.0.0-smoke-fixture'
    [IO.File]::WriteAllText($ciVersion, "$ciOldVersion`n", $ciUtf8)
    $ciSentinel = Join-Path $ciInstalled 'data\runtime\smoke-preserved-user-data.txt'
    [IO.File]::WriteAllText($ciSentinel, 'CI fixture preserved across rollback and upgrade', $ciUtf8)
    $ciSentinelHash = (Get-FileHash -LiteralPath $ciSentinel -Algorithm SHA256).Hash
    $ciFailedExit = Invoke-FixtureInstaller -ExtraArguments @('-PackageUpgradeSmoke','-PackageSmokeFailAfterPublish')
    if ($ciFailedExit -eq 0) { throw 'Forced post-publish failure unexpectedly succeeded.' }
    if ((Get-Content -LiteralPath $ciVersion -Raw).Trim() -cne $ciOldVersion) { throw 'Rollback did not restore previous VERSION.' }
    if ((Get-FileHash -LiteralPath $ciSentinel -Algorithm SHA256).Hash -cne $ciSentinelHash) { throw 'Rollback changed preserved user data.' }

    $ciUpgradeExit = Invoke-FixtureInstaller -ExtraArguments @('-PackageUpgradeSmoke')
    if ($ciUpgradeExit -ne 0) { throw "Isolated upgrade failed: $ciUpgradeExit" }
    $ciExpectedVersion = (Get-Content -LiteralPath (Join-Path $ciPackageRoot 'VERSION') -Raw).Trim()
    if ((Get-Content -LiteralPath $ciVersion -Raw).Trim() -cne $ciExpectedVersion) { throw 'Upgrade VERSION mismatch.' }
    if ((Get-FileHash -LiteralPath $ciSentinel -Algorithm SHA256).Hash -cne $ciSentinelHash) { throw 'Upgrade changed preserved user data.' }
    $ciHealth = Invoke-RestMethod -Uri "http://127.0.0.1:$ciPort/api/health" -TimeoutSec 15
    if ($ciHealth.ok -ne $true -or [string]$ciHealth.status -cne 'ready') { throw 'Installed Bridge health is not ready.' }
    Write-Output 'CI fresh install, real health, forced rollback and upgrade passed; OAuth is an inert fixture and no EA was attached.'
}
finally {
    # The lifecycle script verifies the installed path, Python identity and PID.
    # Never kill by port or name, and never touch a global scheduled task here.
    try {
        if ($ciPort -gt 0 -and (Test-Path -LiteralPath $ciLifecycle -PathType Leaf)) {
            & powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                -File $ciLifecycle -Action Stop -Port $ciPort
            if ($LASTEXITCODE -ne 0) { throw 'Owned CI Bridge cleanup could not be confirmed.' }
        }
    }
    finally {
        $env:LOCALAPPDATA = $ciOriginalLocal
        $env:APPDATA = $ciOriginalAppData
        $env:CODEX_HOME = $ciOriginalCodex
    }
}
