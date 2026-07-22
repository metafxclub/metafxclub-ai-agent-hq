[CmdletBinding()]
param([switch]$SkipLaunch)

$ErrorActionPreference = "Stop"
$installRoot = Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ"
$installer = Join-Path $installRoot "installer\install.ps1"

if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    Write-Error "ยังไม่พบ Metafxclub AI Agent HQ ในเครื่องนี้ กรุณาเปิด 1-INSTALL-HQ.bat ก่อน"
    exit 1
}

$arguments = @("-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $installer, "-RepairOnly")
if ($SkipLaunch) {
    $arguments += "-SkipLaunch"
}

& powershell.exe @arguments
exit $LASTEXITCODE
