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
if ($RemoveUserData -and $ConfirmUserDataRemoval -cne "DELETE-METAFX-DATA") {
    throw "หากต้องการลบข้อมูลผู้ใช้จริง ให้ระบุ -ConfirmUserDataRemoval DELETE-METAFX-DATA ด้วย การถอนปกติจะเก็บข้อมูลไว้"
}

function Remove-GoogleOAuthUserConfiguration {
    $pythonPath = Join-Path $installRoot "runner\.venv\Scripts\python.exe"
    $configureCli = Join-Path $installRoot "backend\local-runner\configure_google_oauth_client.py"
    if (
        -not (Test-Path -LiteralPath $pythonPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $configureCli -PathType Leaf)
    ) {
        throw "ลบข้อมูล Google แบบปลอดภัยไม่ได้ เพราะชุด Backend CLI ไม่ครบ กรุณา Repair แล้วถอนพร้อมลบข้อมูลอีกครั้ง"
    }

    $output = @(& $pythonPath $configureCli --remove 2>$null)
    if ($LASTEXITCODE -ne 0) {
        throw "ลบการยืนยัน Google และ OAuth Client ไม่สำเร็จ จึงยังไม่ถอนข้อมูลผู้ใช้"
    }
    $jsonLine = @($output | ForEach-Object { [string]$_ } | Where-Object { $_.TrimStart().StartsWith("{") }) | Select-Object -Last 1
    if (-not $jsonLine) {
        throw "Backend CLI ไม่คืนผลยืนยันการลบ Google ที่ปลอดภัย จึงยังไม่ถอนข้อมูลผู้ใช้"
    }
    try {
        $result = $jsonLine | ConvertFrom-Json
    }
    catch {
        throw "อ่านผลยืนยันการลบ Google ไม่สำเร็จ จึงยังไม่ถอนข้อมูลผู้ใช้"
    }
    if ($result.ok -ne $true -or $result.configured -ne $false) {
        throw "Backend ยังไม่ยืนยันว่าลบการตั้งค่า Google แล้ว จึงยังไม่ถอนข้อมูลผู้ใช้"
    }
}

$unregisterAutostart = Join-Path $installRoot "scripts\unregister-bridge-autostart.ps1"
if (Test-Path -LiteralPath $unregisterAutostart -PathType Leaf) {
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $unregisterAutostart
    if ($LASTEXITCODE -ne 0) {
        throw "ยกเลิก Task เปิด Bridge อัตโนมัติไม่สำเร็จ จึงยังไม่ถอนโปรแกรม"
    }
}
elseif (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue) {
    $taskName = "Metafxclub AI Agent HQ Bridge"
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    }
}

if (-not (Test-Path -LiteralPath $installRoot -PathType Container)) {
    Write-Host "ไม่พบตัวโปรแกรมในเครื่อง และยกเลิก Scheduled Task ที่อาจค้างอยู่แล้ว"
    exit 0
}

$lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
if (Test-Path -LiteralPath $lifecycle -PathType Leaf) {
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $lifecycle -Action Stop
    if ($LASTEXITCODE -ne 0) {
        throw "หยุด Local Bridge ไม่สำเร็จ จึงยังไม่ถอนโปรแกรม"
    }
}

if ($RemoveUserData) {
    # Only the explicit destructive mode with the exact confirmation above may
    # remove the DPAPI client and refresh grant outside the install directory.
    # The canonical Backend CLI owns both paths and the DPAPI contract.
    Remove-GoogleOAuthUserConfiguration
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

foreach ($directoryName in @("artifacts", "backend", "contracts", "docs", "frontend", "installer", "integrations", "runner", "tests")) {
    $path = Join-Path $installRoot $directoryName
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

$rootFiles = @(
    "index.html", "Open Metafx Agent HQ.cmd", "README.md", "requirements-runner.txt",
    "1-INSTALL-HQ.bat", "2-SETUP-GOOGLE-HQ.bat", "UPDATE-HQ.bat", "REPAIR-HQ.bat", "AGENTS.md", ".gitattributes", ".gitignore", "LICENSE", "LICENSE.md", "SECURITY.md", "VERSION", "STUDENT-QUICKSTART-TH.md"
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
    Write-Host "ถอนโปรแกรม ลบข้อมูลผู้ใช้ และลบการยืนยัน Google ที่ Backend เก็บไว้ตามคำยืนยันแล้ว" -ForegroundColor Yellow
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
if ($RemoveUserData) {
    Write-Host "Environment variable ของ Google ที่ผู้ดูแลตั้งเองจะไม่ถูกแก้ไขอัตโนมัติ" -ForegroundColor Yellow
}
else {
    Write-Host "การยืนยัน Google และ OAuth Client ที่เข้ารหัสไว้นอกโฟลเดอร์ HQ ยังคงอยู่ หากติดตั้งใหม่จะใช้ต่อได้" -ForegroundColor Yellow
}
exit 0
