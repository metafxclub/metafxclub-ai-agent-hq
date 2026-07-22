[CmdletBinding()]
param(
    [switch]$RemoveUserData,
    [string]$ConfirmUserDataRemoval = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ")).TrimEnd("\")
$expectedRoot = [IO.Path]::GetFullPath("$env:LOCALAPPDATA\Metafxclub\AI-Agent-HQ").TrimEnd("\")
if (-not $installRoot.Equals($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "ปฏิเสธการถอนการติดตั้ง เพราะ Path ไม่ตรงกับตำแหน่งที่อนุญาต"
}
if (-not (Test-Path -LiteralPath $installRoot -PathType Container)) {
    Write-Host "ไม่พบ Metafxclub AI Agent HQ ในเครื่องนี้"
    exit 0
}
if ($RemoveUserData -and $ConfirmUserDataRemoval -cne "DELETE-METAFX-DATA") {
    throw "หากต้องการลบข้อมูลผู้ใช้จริง ให้ระบุ -ConfirmUserDataRemoval DELETE-METAFX-DATA ด้วย การถอนปกติจะเก็บข้อมูลไว้"
}

$lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
if (Test-Path -LiteralPath $lifecycle -PathType Leaf) {
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $lifecycle -Action Stop
    if ($LASTEXITCODE -ne 0) {
        throw "หยุด Local Bridge ไม่สำเร็จ จึงยังไม่ถอนโปรแกรม"
    }
}

$shortcutPaths = @(
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "Metafxclub AI Agent HQ.lnk"),
    (Join-Path ([Environment]::GetFolderPath("Programs")) "Metafxclub\Metafxclub AI Agent HQ.lnk")
)
foreach ($shortcutPath in $shortcutPaths) {
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath -Force
    }
}
$startMenuFolder = Join-Path ([Environment]::GetFolderPath("Programs")) "Metafxclub"
if ((Test-Path -LiteralPath $startMenuFolder -PathType Container) -and -not (Get-ChildItem -LiteralPath $startMenuFolder -Force | Select-Object -First 1)) {
    Remove-Item -LiteralPath $startMenuFolder -Force
}

foreach ($directoryName in @("backend", "contracts", "docs", "frontend", "installer", "runner", "tests")) {
    $path = Join-Path $installRoot $directoryName
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

$rootFiles = @(
    "index.html", "Open Metafx Agent HQ.cmd", "README.md", "requirements-runner.txt",
    "1-INSTALL-HQ.bat", "REPAIR-HQ.bat", "AGENTS.md", ".gitignore", "LICENSE", "LICENSE.md", "SECURITY.md", "VERSION", "STUDENT-QUICKSTART-TH.md"
)
foreach ($fileName in $rootFiles) {
    $path = Join-Path $installRoot $fileName
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
    }
}

$scriptsRoot = Join-Path $installRoot "scripts"
if (Test-Path -LiteralPath $scriptsRoot -PathType Container) {
    foreach ($item in Get-ChildItem -LiteralPath $scriptsRoot -Force) {
        if ($item.Name -notin @("uninstall-hq.ps1", "uninstall-hq.cmd")) {
            Remove-Item -LiteralPath $item.FullName -Recurse -Force
        }
    }
}

$dataRoot = Join-Path $installRoot "data"
if ($RemoveUserData) {
    if (Test-Path -LiteralPath $dataRoot) {
        Remove-Item -LiteralPath $dataRoot -Recurse -Force
    }
    Write-Host "ถอนโปรแกรมและลบข้อมูลผู้ใช้ตามคำยืนยันแล้ว" -ForegroundColor Yellow
}
else {
    New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
    $receipt = [ordered]@{
        status = "application_removed_user_data_preserved"
        removed_at = [DateTime]::UtcNow.ToString("o")
        data_path = $dataRoot
    }
    $receiptPath = Join-Path $dataRoot "uninstall-status.json"
    $json = $receipt | ConvertTo-Json
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($receiptPath, $json + [Environment]::NewLine, $utf8)
    Write-Host "ถอนโปรแกรมแล้ว และเก็บ Mission, Report, Memory และ Log ไว้ที่:" -ForegroundColor Green
    Write-Host $dataRoot -ForegroundColor Green
}

Write-Host "Shortcut และตัวโปรแกรมถูกนำออกแล้ว ไม่ได้แตะ Codex Login หรือ Secret ภายนอกโฟลเดอร์ HQ"
exit 0
