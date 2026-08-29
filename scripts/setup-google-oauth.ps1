[CmdletBinding()]
param(
    [string]$ClientJsonPath = "",
    [string]$ExpectedClientId = "",
    [switch]$SkipBridgeEnsure,
    [switch]$SkipOpen
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd("\")
$configureCli = Join-Path $projectRoot "backend\local-runner\configure_google_oauth_client.py"
$lifecycleScript = Join-Path $projectRoot "scripts\start-local-bridge.ps1"
$endpointPath = Join-Path $projectRoot "data\runtime\bridge-endpoint.json"

function Get-SelectedClientJsonPath {
    if (-not [string]::IsNullOrWhiteSpace($ClientJsonPath)) {
        return $ClientJsonPath.Trim().Trim('"')
    }

    try {
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.OpenFileDialog
        $dialog.Title = "เลือก Google OAuth Client JSON ประเภท Desktop app"
        $dialog.Filter = "Google OAuth Client JSON (*.json)|*.json"
        $dialog.CheckFileExists = $true
        $dialog.Multiselect = $false
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            return [string]$dialog.FileName
        }
        return ""
    }
    catch {
        $typedPath = Read-Host "วาง Path ของ OAuth Desktop client JSON หรือเว้นว่างเพื่อข้าม"
        if ([string]::IsNullOrWhiteSpace($typedPath)) {
            return ""
        }
        return $typedPath.Trim().Trim('"')
    }
}

function Get-SafeClientJsonPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    try {
        $fullPath = [IO.Path]::GetFullPath($Path)
        $exists = Test-Path -LiteralPath $fullPath -PathType Leaf
    }
    catch {
        throw "อ่านตำแหน่ง OAuth JSON ที่เลือกไม่ได้"
    }
    if (-not $exists) {
        throw "ไม่พบไฟล์ OAuth JSON ที่เลือก"
    }
    try {
        $file = Get-Item -LiteralPath $fullPath -Force
    }
    catch {
        throw "อ่าน OAuth JSON ที่เลือกไม่ได้"
    }
    if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "ไม่รับ OAuth JSON ที่เป็น Link/Junction"
    }
    if ($file.Extension -ine ".json" -or $file.Length -lt 16 -or $file.Length -gt 64KB) {
        throw "OAuth Client ต้องเป็นไฟล์ JSON ขนาดไม่เกิน 64 KiB"
    }
    return $fullPath
}

function Resolve-SetupPython {
    $venvPython = Join-Path $projectRoot "runner\.venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        return [pscustomobject]@{ FilePath = $venvPython; PrefixArguments = @() }
    }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        return [pscustomobject]@{ FilePath = $launcher.Source; PrefixArguments = @("-3") }
    }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        return [pscustomobject]@{ FilePath = $python.Source; PrefixArguments = @() }
    }
    throw "ไม่พบ Python สำหรับนำเข้า Google OAuth Client"
}

function Import-GoogleOAuthClient {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$Expected = ""
    )

    if (-not (Test-Path -LiteralPath $configureCli -PathType Leaf)) {
        throw "ชุดติดตั้งไม่มี Google OAuth configuration CLI"
    }
    $python = Resolve-SetupPython
    $arguments = @($python.PrefixArguments) + @($configureCli, "--file", $Path)
    if (-not [string]::IsNullOrWhiteSpace($Expected)) {
        $arguments += @("--expected-client-id", $Expected.Trim())
    }
    $output = @(& $python.FilePath @arguments 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "นำเข้า OAuth Client ไม่สำเร็จ กรุณาใช้ JSON ประเภท Desktop app จาก Google Auth Platform"
    }
    $jsonLine = @($output | ForEach-Object { [string]$_ } | Where-Object { $_.TrimStart().StartsWith("{") }) | Select-Object -Last 1
    if (-not $jsonLine) {
        throw "Google OAuth configuration CLI ไม่คืนผลยืนยันที่ปลอดภัย"
    }
    try {
        $result = $jsonLine | ConvertFrom-Json
    }
    catch {
        throw "อ่านผลยืนยัน Google OAuth configuration ไม่สำเร็จ"
    }
    if ($result.ok -ne $true -or $result.configured -ne $true) {
        throw "Backend ยังไม่ยืนยันการบันทึก Google OAuth Client"
    }
    return $result
}

function Open-AgentHq {
    if (-not (Test-Path -LiteralPath $endpointPath -PathType Leaf)) {
        return
    }
    try {
        $endpoint = Get-Content -LiteralPath $endpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $url = [string]$endpoint.url
        if ($url -match '^http://127\.0\.0\.1:\d{4,5}/$') {
            Start-Process $url
        }
    }
    catch {
        Write-Warning "ตั้งค่า Google สำเร็จ แต่ยังเปิด Agent HQ อัตโนมัติไม่ได้"
    }
}

try {
    $selectedPath = Get-SelectedClientJsonPath
    if ([string]::IsNullOrWhiteSpace($selectedPath)) {
        Write-Host "ข้ามการตั้งค่า Google ตอนนี้ เปิด 2-SETUP-GOOGLE-HQ.bat ภายหลังได้" -ForegroundColor Yellow
        exit 0
    }

    $safePath = Get-SafeClientJsonPath -Path $selectedPath
    $result = Import-GoogleOAuthClient -Path $safePath -Expected $ExpectedClientId
    $clientHint = [string]$result.clientHint
    $hintText = if ($clientHint) { " ($clientHint)" } else { "" }
    Write-Host "บันทึก Google OAuth Client สำหรับ Windows User นี้แล้ว$hintText" -ForegroundColor Green
    Write-Host "JSON และ Client Secret ไม่ผ่าน Browser และไม่ถูกคัดลอกเข้า Project" -ForegroundColor DarkGray

    if (-not $SkipBridgeEnsure) {
        if (-not (Test-Path -LiteralPath $lifecycleScript -PathType Leaf)) {
            throw "ไม่พบสคริปต์ Local Bridge"
        }
        & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $lifecycleScript -Action Ensure
        if ($LASTEXITCODE -ne 0) {
            throw "บันทึก OAuth Client แล้ว แต่ Local Bridge ยังไม่พร้อม"
        }
    }
    if (-not $SkipOpen) {
        Open-AgentHq
    }

    Write-Host "ขั้นต่อไป: เปิด Agent HQ กด 'เชื่อมบัญชี Google ครั้งเดียว' แล้วใส่ Sheet ID" -ForegroundColor Cyan
    exit 0
}
catch {
    $safeMessage = [string]$_.Exception.Message
    $safeMessage = $safeMessage -replace '(?i)(client_secret|secret|token|authorization)\s*[:=]\s*\S+', '$1=[REDACTED]'
    Write-Error $safeMessage
    exit 1
}
