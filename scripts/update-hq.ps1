[CmdletBinding()]
param(
    [switch]$SkipLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd("\")
$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ")).TrimEnd("\")
$installerPath = Join-Path $projectRoot "installer\install.ps1"
$installedEndpointPath = Join-Path $installRoot "data\runtime\bridge-endpoint.json"

function Invoke-GitChecked {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureMessage,
        [switch]$Capture
    )

    if ($Capture) {
        $output = & git.exe -C $projectRoot @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            throw "$FailureMessage (Git รหัส $exitCode)"
        }
        return @($output)
    }

    & git.exe -C $projectRoot @Arguments | Out-Host
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "$FailureMessage (Git รหัส $exitCode)"
    }
}

if (-not (Get-Command git.exe -CommandType Application -ErrorAction SilentlyContinue)) {
    throw "ไม่พบ Git สำหรับ Windows กรุณาติดตั้ง Git หรือดาวน์โหลด Release ZIP รุ่นใหม่แทน"
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot ".git") -PathType Container)) {
    throw "โฟลเดอร์นี้มาจาก Release ZIP จึงอัปเดตด้วย Git ไม่ได้ กรุณาดาวน์โหลด Release รุ่นใหม่แล้วรัน 1-INSTALL-HQ.bat"
}
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "ชุด Source ไม่สมบูรณ์: ไม่พบ installer\install.ps1"
}

$statusLines = @(Invoke-GitChecked -Arguments @("status", "--porcelain", "--untracked-files=normal") -FailureMessage "ตรวจสถานะ Git ไม่สำเร็จ" -Capture)
if ($statusLines.Count -gt 0) {
    throw "พบไฟล์ที่แก้หรือไฟล์ใหม่ใน Source จึงหยุดก่อนอัปเดต กรุณา Commit, Stash หรือสำรองงานของตนเองก่อน"
}

$branch = ((Invoke-GitChecked -Arguments @("branch", "--show-current") -FailureMessage "อ่าน Branch ปัจจุบันไม่สำเร็จ" -Capture) | Select-Object -Last 1).Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
    throw "ขณะนี้ Git อยู่แบบ Detached HEAD กรุณา Checkout Branch ที่ต้องการอัปเดตก่อน"
}

$upstream = $null
try {
    $upstream = ((Invoke-GitChecked -Arguments @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") -FailureMessage "Branch นี้ยังไม่มี Upstream" -Capture) | Select-Object -Last 1).Trim()
}
catch {
    if ($branch -ceq "main") {
        $originMain = & git.exe -C $projectRoot show-ref --verify --quiet refs/remotes/origin/main
        if ($LASTEXITCODE -eq 0) {
            $upstream = "origin/main"
        }
    }
}
if ([string]::IsNullOrWhiteSpace($upstream)) {
    throw "Branch '$branch' ยังไม่มี Upstream กรุณาตั้ง Upstream หรือเปลี่ยนกลับ main ก่อนอัปเดต"
}

Write-Host "กำลังตรวจ GitHub และอัปเดต Source แบบ fast-forward เท่านั้น" -ForegroundColor Cyan
Invoke-GitChecked -Arguments @("fetch", "--all", "--prune") -FailureMessage "ดาวน์โหลดข้อมูลล่าสุดจาก GitHub ไม่สำเร็จ"
Invoke-GitChecked -Arguments @("merge", "--ff-only", $upstream) -FailureMessage "อัปเดตแบบ fast-forward ไม่ได้ อาจมี Commit คนละทาง ระบบไม่ Merge หรือทับงานให้อัตโนมัติ"

$selectedPort = 0
if (Test-Path -LiteralPath $installedEndpointPath -PathType Leaf) {
    try {
        $endpoint = Get-Content -LiteralPath $installedEndpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ([string]$endpoint.host -cne "127.0.0.1") {
            throw "host ไม่ถูกต้อง"
        }
        $selectedPort = [int]$endpoint.port
        if ($selectedPort -lt 1024 -or $selectedPort -gt 65535) {
            throw "port ไม่ถูกต้อง"
        }
    }
    catch {
        throw "Endpoint ของชุดติดตั้งเดิมไม่สมบูรณ์ กรุณาเปิด 1-INSTALL-HQ.bat และเลือก URL ใหม่"
    }
}

$installerArguments = @(
    "-NoLogo",
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $installerPath
)
if ($selectedPort -ge 1024) {
    $installerArguments += @("-Port", [string]$selectedPort, "-EndpointConfirmed")
}
if ($SkipLaunch) {
    $installerArguments += "-SkipLaunch"
}

Write-Host "กำลังนำ Source ที่อัปเดตแล้วไปติดตั้งในตำแหน่งถาวร" -ForegroundColor Cyan
& powershell.exe @installerArguments
$installExitCode = $LASTEXITCODE
if ($installExitCode -ne 0) {
    throw "Source อัปเดตแล้ว แต่ติดตั้ง Runtime ไม่สำเร็จ (รหัส $installExitCode) กรุณารัน 1-INSTALL-HQ.bat อีกครั้ง"
}

$commit = ((Invoke-GitChecked -Arguments @("rev-parse", "--short", "HEAD") -FailureMessage "อ่าน Commit หลังอัปเดตไม่สำเร็จ" -Capture) | Select-Object -Last 1).Trim()
Write-Host "อัปเดตสำเร็จ: Branch $branch • Commit $commit" -ForegroundColor Green
Write-Host "ข้อมูล Mission, Memory, Log และ Codex Login ของผู้ใช้ไม่ได้ถูกส่งขึ้น GitHub"
exit 0
