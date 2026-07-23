[CmdletBinding()]
param(
    [switch]$RepairOnly,
    [switch]$SkipLaunch,
    [switch]$SkipShortcuts,
    [switch]$ListAvailableEndpoints,
    [ValidateRange(0, 65535)]
    [int]$Port = 0,
    [switch]$EndpointConfirmed
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$sourceRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd("\")
$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ")).TrimEnd("\")
$installLog = Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ-Install.log"
$requirementsName = "requirements-runner.txt"
$bridgeEndpointPath = Join-Path $installRoot "data\runtime\bridge-endpoint.json"
$installResultPath = Join-Path $installRoot "data\runtime\install-result.json"

if ($Port -ne 0 -and $Port -lt 1024) {
    throw "Port ต้องเป็น 0 หรืออยู่ในช่วง 1024-65535"
}

function Write-InstallLog {
    param([Parameter(Mandatory = $true)][string]$Message)

    $parent = Split-Path -Parent $installLog
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $line = "[{0}] {1}{2}" -f ([DateTime]::UtcNow.ToString("o")), $Message, [Environment]::NewLine
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::AppendAllText($installLog, $line, $utf8)
}

function Write-Step {
    param([Parameter(Mandatory = $true)][string]$Message)

    Write-Host ("[Metafxclub HQ] {0}" -f $Message) -ForegroundColor Cyan
    Write-InstallLog -Message $Message
}

function Test-LoopbackPortAvailable {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$CandidatePort)

    $listener = $null
    try {
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $CandidatePort)
        $listener.Start()
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($listener) {
            try { $listener.Stop() } catch { }
        }
    }
}

function Get-HealthySavedEndpoint {
    if (-not (Test-Path -LiteralPath $bridgeEndpointPath -PathType Leaf)) {
        return $null
    }

    try {
        $saved = Get-Content -LiteralPath $bridgeEndpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $savedPort = [int]$saved.port
        if ([string]$saved.host -cne "127.0.0.1" -or $savedPort -lt 1024 -or $savedPort -gt 65535) {
            return $null
        }
        $healthUrl = "http://127.0.0.1:$savedPort/api/health"
        $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 2
        if (
            $health.ok -ne $true -or
            [string]$health.status -cne "ready" -or
            -not $health.endpoint -or
            [string]$health.endpoint.host -cne "127.0.0.1" -or
            [int]$health.endpoint.port -ne $savedPort
        ) {
            return $null
        }
        return [pscustomobject]@{
            Host = "127.0.0.1"
            Port = $savedPort
            Url = "http://127.0.0.1:$savedPort/"
            Reusable = $true
            Reason = "HQ เดิมกำลังใช้งานอยู่และสามารถใช้ URL เดิมต่อได้"
        }
    }
    catch {
        return $null
    }
}

function Get-AvailableBridgeEndpointCandidates {
    param([ValidateRange(1, 8)][int]$Count = 3)

    $results = New-Object System.Collections.Generic.List[object]
    $seen = New-Object 'System.Collections.Generic.HashSet[int]'
    $saved = Get-HealthySavedEndpoint
    if ($saved -and $seen.Add([int]$saved.Port)) {
        $results.Add($saved)
    }

    foreach ($candidatePort in 4186..4195) {
        if ($results.Count -ge $Count) {
            break
        }
        if ($seen.Add($candidatePort) -and (Test-LoopbackPortAvailable -CandidatePort $candidatePort)) {
            $results.Add([pscustomobject]@{
                Host = "127.0.0.1"
                Port = $candidatePort
                Url = "http://127.0.0.1:$candidatePort/"
                Reusable = $false
                Reason = "พอร์ตว่างบนเครื่องนี้"
            })
        }
    }

    $attempted = 0
    while ($results.Count -lt $Count -and $attempted -lt 512) {
        $attempted++
        $candidatePort = Get-Random -Minimum 42000 -Maximum 49000
        if (-not $seen.Add($candidatePort)) {
            continue
        }
        if (Test-LoopbackPortAvailable -CandidatePort $candidatePort) {
            $results.Add([pscustomobject]@{
                Host = "127.0.0.1"
                Port = $candidatePort
                Url = "http://127.0.0.1:$candidatePort/"
                Reusable = $false
                Reason = "พอร์ตสำรองว่างบนเครื่องนี้"
            })
        }
    }

    if ($results.Count -lt $Count) {
        throw "หา Local endpoint ว่างไม่ครบ $Count ตัวเลือก ระบบยังไม่ได้เปลี่ยนแปลงเครื่อง"
    }

    $numbered = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $results.Count; $index++) {
        $item = $results[$index]
        $numbered.Add([pscustomobject]@{
            number = $index + 1
            host = "127.0.0.1"
            port = [int]$item.Port
            url = [string]$item.Url
            available = $true
            reusable = [bool]$item.Reusable
            note = [string]$item.Reason
        })
    }
    return $numbered.ToArray()
}

function Test-RequestedEndpointUsable {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$CandidatePort)

    $saved = Get-HealthySavedEndpoint
    if ($saved -and [int]$saved.Port -eq $CandidatePort) {
        return $true
    }
    return Test-LoopbackPortAvailable -CandidatePort $CandidatePort
}

function Confirm-BridgeEndpoint {
    $selectedPort = $Port
    if ($selectedPort -ge 1024) {
        if (-not (Test-RequestedEndpointUsable -CandidatePort $selectedPort)) {
            throw "URL http://127.0.0.1:$selectedPort/ ไม่ว่างแล้ว ระบบยังไม่ได้ติดตั้งหรือปิดโปรแกรมอื่น"
        }
        if ($EndpointConfirmed) {
            Write-Host "ยืนยัน Local endpoint จากผู้ใช้แล้ว: http://127.0.0.1:$selectedPort/" -ForegroundColor Green
            return $selectedPort
        }

        Write-Host ""
        Write-Host "พบ Local endpoint ที่ใช้ได้: http://127.0.0.1:$selectedPort/" -ForegroundColor Green
        $answer = Read-Host "ใช้ URL นี้สำหรับ Metafxclub AI Agent HQ หรือไม่? พิมพ์ Y เพื่อยืนยัน"
        if ($answer.Trim().ToLowerInvariant() -notin @("y", "yes", "ใช่", "ตกลง")) {
            throw "ผู้ใช้ยังไม่ยืนยัน Local endpoint ระบบจึงหยุดก่อนเปลี่ยนแปลงเครื่อง"
        }
        return $selectedPort
    }

    $candidates = @(Get-AvailableBridgeEndpointCandidates -Count 3)
    foreach ($candidate in $candidates) {
        Write-Host ""
        Write-Host ("พบ Local endpoint ที่ใช้ได้: {0}" -f $candidate.url) -ForegroundColor Green
        Write-Host ("สถานะ: {0}" -f $candidate.note) -ForegroundColor DarkGray
        $answer = Read-Host "ใช้ URL นี้สำหรับ Metafxclub AI Agent HQ หรือไม่? พิมพ์ Y เพื่อยืนยัน หรือ N เพื่อดูตัวเลือกถัดไป"
        $normalized = $answer.Trim().ToLowerInvariant()
        if ($normalized -in @("y", "yes", "ใช่", "ตกลง")) {
            return [int]$candidate.port
        }
        if ($normalized -notin @("n", "no", "ไม่", "ไม่ใช้")) {
            throw "ไม่ได้รับคำยืนยัน Local endpoint ที่ชัดเจน ระบบจึงหยุดก่อนเปลี่ยนแปลงเครื่อง"
        }
    }
    throw "ผู้ใช้ปฏิเสธ Local endpoint ทุกตัวเลือก ระบบจึงหยุดโดยไม่ติดตั้ง"
}

function Get-ComparablePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    return [IO.Path]::GetFullPath($Path).TrimEnd("\")
}

function Get-ConfirmedBridgeEndpoint {
    if (-not (Test-Path -LiteralPath $bridgeEndpointPath -PathType Leaf)) {
        throw "ไม่พบ Local endpoint ที่ผ่าน Health check"
    }

    try {
        $endpoint = Get-Content -LiteralPath $bridgeEndpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $endpointProperties = @($endpoint.PSObject.Properties.Name)
        if ($endpointProperties -notcontains "host" -or $endpointProperties -notcontains "port") {
            throw "Endpoint fields are missing."
        }
        $hostValue = [string]$endpoint.host
        $port = [int]$endpoint.port
    }
    catch {
        throw "ไฟล์ Local endpoint ไม่สมบูรณ์ กรุณารัน Repair อีกครั้ง"
    }

    if ($hostValue -cne "127.0.0.1" -or $port -lt 1024 -or $port -gt 65535) {
        throw "ปฏิเสธ endpoint ที่ไม่ใช่ 127.0.0.1 หรือใช้พอร์ตนอกช่วงที่อนุญาต"
    }

    return [pscustomobject]@{
        Host = "127.0.0.1"
        Port = $port
        Url = "http://127.0.0.1:$port/"
        HealthUrl = "http://127.0.0.1:$port/api/health"
    }
}

function Test-PythonCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$PrefixArguments = @()
    )

    try {
        $arguments = @($PrefixArguments) + @(
            "-c",
            "import json,sys; print(json.dumps({'major':sys.version_info[0],'minor':sys.version_info[1],'micro':sys.version_info[2],'executable':sys.executable}))"
        )
        $raw = & $FilePath @arguments 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) {
            return $null
        }
        $details = ($raw | Select-Object -Last 1) | ConvertFrom-Json
        if ([int]$details.major -ne 3 -or [int]$details.minor -lt 10) {
            return $null
        }
        return [pscustomobject]@{
            FilePath = $FilePath
            PrefixArguments = @($PrefixArguments)
            Version = "{0}.{1}.{2}" -f $details.major, $details.minor, $details.micro
            Executable = [string]$details.executable
        }
    }
    catch {
        return $null
    }
}

function Resolve-SystemPython {
    $launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($launcher) {
        $candidate = Test-PythonCommand -FilePath $launcher.Source -PrefixArguments @("-3")
        if ($candidate) {
            return $candidate
        }
    }

    foreach ($commandName in @("python.exe", "python3.exe")) {
        $command = Get-Command $commandName -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $command -or $command.Source -match "\\WindowsApps\\") {
            continue
        }
        $candidate = Test-PythonCommand -FilePath $command.Source
        if ($candidate) {
            return $candidate
        }
    }

    throw "ไม่พบ Python 3.10 ขึ้นไป กรุณาติดตั้ง Python จาก python.org และเลือก Add Python to PATH แล้วเปิด Installer อีกครั้ง ระบบจะไม่ดาวน์โหลด Python หรือขอสิทธิ์ Administrator ให้อัตโนมัติ"
}

function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    # Forward native output to the console without leaking it into the
    # function's success pipeline. Callers rely on receiving only their
    # explicit return value (for example, the venv Python path).
    & $FilePath @Arguments | Out-Host
    $nativeExitCode = $LASTEXITCODE
    if ($nativeExitCode -ne 0) {
        throw "$FailureMessage (รหัส $nativeExitCode)"
    }
}

function Assert-SafeSource {
    $requiredFiles = @(
        "backend\local-runner\bridge_server.py",
        "frontend\index.html",
        "runner\codex_cli_runner.py",
        "scripts\start-local-bridge.ps1",
        $requirementsName
    )
    foreach ($relativePath in $requiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $relativePath) -PathType Leaf)) {
            throw "ชุดติดตั้งไม่สมบูรณ์: ไม่พบ $relativePath"
        }
    }

    $blockedNames = @(
        ".env", ".env.local", ".env.production", "credentials.json", "cookies.json",
        "auth.json", "secrets.json", "config.toml", "id_rsa", "id_ed25519"
    )
    $allowedDirectories = @("backend", "contracts", "docs", "frontend", "installer", "runner", "scripts", "tests")
    foreach ($directoryName in $allowedDirectories) {
        $directory = Join-Path $sourceRoot $directoryName
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            continue
        }
        foreach ($item in Get-ChildItem -LiteralPath $directory -Recurse -Force) {
            if (
                $item.FullName -match "[\\/]\.venv(?:[\\/]|$)" -or
                $item.FullName -match "[\\/]__pycache__(?:[\\/]|$)"
            ) {
                continue
            }
            if ($item.PSIsContainer -and $item.Name -ieq ".codex") {
                throw "หยุดติดตั้งเพื่อความปลอดภัย: พบโฟลเดอร์ .codex ในชุดแจก"
            }
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "หยุดติดตั้งเพื่อความปลอดภัย: ชุดแจกมี Link/Junction ที่ไม่ได้รับอนุญาต ($($item.Name))"
            }
            if ($item.PSIsContainer) {
                continue
            }
            if (
                $blockedNames -contains $item.Name.ToLowerInvariant() -or
                $item.Name -match "(?i)(token|credential|cookie)" -or
                $item.Name -match "(?i)^(auth|secret)s?.*\.json$" -or
                $item.Extension.ToLowerInvariant() -in @(".pem", ".key", ".pfx", ".p12", ".log", ".jsonl", ".bak", ".tmp")
            ) {
                throw "หยุดติดตั้งเพื่อความปลอดภัย: พบไฟล์ที่อาจเป็นข้อมูลลับในชุดแจก ($($item.Name))"
            }
        }
    }
}

function Stop-ExistingBridge {
    $lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
    if (-not (Test-Path -LiteralPath $lifecycle -PathType Leaf)) {
        return
    }

    Write-Step "กำลังหยุด Local Bridge เดิมแบบตรวจสอบตัวตนก่อน"
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $lifecycle -Action Stop
    if ($LASTEXITCODE -ne 0) {
        throw "หยุด Local Bridge เดิมไม่สำเร็จ จึงยกเลิกเพื่อไม่ให้แก้ไฟล์ขณะระบบกำลังทำงาน"
    }

    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $lifecycle -Action Status | Out-Host
    $statusExitCode = $LASTEXITCODE
    if ($statusExitCode -notin @(3, 4)) {
        throw "ยังพบ Local Bridge ของโปรเจกต์ทำงานอยู่หรือพบหลาย Instance จึงหยุดติดตั้งก่อนคัดลอกไฟล์"
    }
}

function Sync-Directory {
    param([Parameter(Mandatory = $true)][string]$DirectoryName)

    $sourceDirectory = Join-Path $sourceRoot $DirectoryName
    if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
        return
    }
    $destinationDirectory = Join-Path $installRoot $DirectoryName
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null

    $arguments = @(
        $sourceDirectory, $destinationDirectory, "/MIR", "/XJ", "/R:2", "/W:1",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
        "/XF", ".env", ".env.*", "config.toml", "*token*", "*credential*", "*cookie*", "*.pem", "*.key", "*.pfx", "*.p12", "*.log", "*.jsonl", "*.bak", "*.tmp", "auth*.json", "secret*.json",
        "/XD", ".git", ".codex", ".venv", "__pycache__", (Join-Path $sourceDirectory ".git"), (Join-Path $sourceDirectory ".codex"), (Join-Path $sourceDirectory ".venv"), (Join-Path $sourceDirectory "__pycache__"),
        (Join-Path $destinationDirectory ".git"), (Join-Path $destinationDirectory ".codex"), (Join-Path $destinationDirectory ".venv"), (Join-Path $destinationDirectory "__pycache__")
    )
    & robocopy.exe @arguments | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "คัดลอกโฟลเดอร์ $DirectoryName ไม่สำเร็จ (Robocopy รหัส $LASTEXITCODE)"
    }
}

function Copy-ApplicationFiles {
    if ((Get-ComparablePath -Path $sourceRoot).Equals((Get-ComparablePath -Path $installRoot), [StringComparison]::OrdinalIgnoreCase)) {
        Write-Step "กำลังซ่อมแซมจากโฟลเดอร์ที่ติดตั้งอยู่ โดยไม่คัดลอกทับข้อมูลผู้ใช้"
        return
    }

    Write-Step "กำลังคัดลอกเฉพาะไฟล์โปรแกรมที่อนุญาต"
    New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
    foreach ($directoryName in @("backend", "contracts", "docs", "frontend", "installer", "runner", "scripts", "tests")) {
        Sync-Directory -DirectoryName $directoryName
    }

    $rootFiles = @(
        "index.html", "Open Metafx Agent HQ.cmd", "README.md", $requirementsName,
        "1-INSTALL-HQ.bat", "REPAIR-HQ.bat", "UNINSTALL-HQ.bat",
        "AGENTS.md", ".gitignore", "LICENSE", "LICENSE.md", "SECURITY.md", "VERSION", "STUDENT-QUICKSTART-TH.md"
    )
    foreach ($fileName in $rootFiles) {
        $sourceFile = Join-Path $sourceRoot $fileName
        if (Test-Path -LiteralPath $sourceFile -PathType Leaf) {
            Copy-Item -LiteralPath $sourceFile -Destination (Join-Path $installRoot $fileName) -Force
        }
    }
}

function Initialize-UserDataDirectories {
    Write-Step "กำลังเตรียมพื้นที่ข้อมูลส่วนตัวแบบว่าง โดยไม่คัดลอกข้อมูลของผู้สอน"
    $directories = @(
        "data\runtime", "data\runtime\archive", "data\runtime\codex-runs", "data\runtime\logs", "data\runtime\reports",
        "data\memory", "data\memory\agent-notes", "data\memory\artifacts", "data\memory\meetings",
        "data\memory\reports", "data\memory\screenshots", "data\memory\summaries"
    )
    foreach ($relativePath in $directories) {
        New-Item -ItemType Directory -Path (Join-Path $installRoot $relativePath) -Force | Out-Null
    }
}

function Initialize-PythonEnvironment {
    $venvRoot = Join-Path $installRoot "runner\.venv"
    $venvPython = Join-Path $venvRoot "Scripts\python.exe"
    $requirements = Join-Path $installRoot $requirementsName

    $venvDetails = $null
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        $venvDetails = Test-PythonCommand -FilePath $venvPython
    }
    if (-not $venvDetails) {
        if (Test-Path -LiteralPath $venvRoot) {
            $expectedVenvRoot = Get-ComparablePath -Path (Join-Path $installRoot "runner\.venv")
            if (-not (Get-ComparablePath -Path $venvRoot).Equals($expectedVenvRoot, [StringComparison]::OrdinalIgnoreCase)) {
                throw "ปฏิเสธการลบ Virtual Environment เพราะ Path ไม่ตรงกับพื้นที่ติดตั้ง"
            }
            Remove-Item -LiteralPath $venvRoot -Recurse -Force
        }

        $python = Resolve-SystemPython
        Write-Step ("พบ Python {0} และกำลังสร้าง Virtual Environment แยกสำหรับ HQ" -f $python.Version)
        $arguments = @($python.PrefixArguments) + @("-m", "venv", $venvRoot)
        Invoke-CheckedNative -FilePath $python.FilePath -Arguments $arguments -FailureMessage "สร้าง Virtual Environment ไม่สำเร็จ"
    }
    else {
        Write-Step ("กำลังตรวจและใช้ Virtual Environment เดิม (Python {0})" -f $venvDetails.Version)
    }

    Write-Step "กำลังติดตั้ง Dependency ที่ล็อกเวอร์ชันไว้"
    Invoke-CheckedNative -FilePath $venvPython -Arguments @("-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "--requirement", $requirements) -FailureMessage "ติดตั้ง Dependency ไม่สำเร็จ กรุณาตรวจอินเทอร์เน็ตแล้วลองใหม่"
    Invoke-CheckedNative -FilePath $venvPython -Arguments @("-m", "pip", "check") -FailureMessage "Dependency ตรวจสอบไม่ผ่าน"

    $codexBinary = Join-Path $venvRoot "Lib\site-packages\codex_cli_bin\bin\codex.exe"
    if (-not (Test-Path -LiteralPath $codexBinary -PathType Leaf)) {
        throw "ติดตั้ง Dependency แล้วแต่ไม่พบ Codex CLI ภายใน Virtual Environment"
    }
    return $venvPython
}

function Test-InstalledApplication {
    param([Parameter(Mandatory = $true)][string]$PythonPath)

    Write-Step "กำลังรันชุดทดสอบความพร้อมของระบบ"
    Push-Location $installRoot
    try {
        Invoke-CheckedNative -FilePath $PythonPath -Arguments @("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v") -FailureMessage "ชุดทดสอบของ HQ ไม่ผ่าน"
    }
    finally {
        Pop-Location
    }
}

function New-HqShortcut {
    param(
        [Parameter(Mandatory = $true)][string]$ShortcutPath,
        [Parameter(Mandatory = $true)][string]$TargetPath
    )

    $shortcutDirectory = Split-Path -Parent $ShortcutPath
    New-Item -ItemType Directory -Path $shortcutDirectory -Force | Out-Null
    $shell = New-Object -ComObject WScript.Shell
    try {
        $shortcut = $shell.CreateShortcut($ShortcutPath)
        $shortcut.TargetPath = $TargetPath
        $shortcut.WorkingDirectory = $installRoot
        $shortcut.Description = "เปิด Metafxclub AI Agent HQ"
        $shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,14"
        $shortcut.Save()
    }
    finally {
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell) | Out-Null
    }
}

function Install-Shortcuts {
    Write-Step "กำลังสร้าง Shortcut สำหรับผู้ใช้ปัจจุบัน"
    $target = Join-Path $installRoot "Open Metafx Agent HQ.cmd"
    $desktop = [Environment]::GetFolderPath("Desktop")
    $programs = [Environment]::GetFolderPath("Programs")
    New-HqShortcut -ShortcutPath (Join-Path $desktop "Metafxclub AI Agent HQ.lnk") -TargetPath $target
    New-HqShortcut -ShortcutPath (Join-Path $programs "Metafxclub\Metafxclub AI Agent HQ.lnk") -TargetPath $target
}

function Start-And-TestBridge {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$ConfirmedPort)

    $lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
    if (-not (Test-LoopbackPortAvailable -CandidatePort $ConfirmedPort)) {
        throw "พอร์ตที่ยืนยัน ($ConfirmedPort) ถูกใช้งานก่อนเริ่ม Bridge ระบบหยุดโดยไม่เปลี่ยน URL อัตโนมัติ"
    }

    Write-Step "กำลังเปิด Local Bridge ที่ URL ซึ่งผู้ใช้ยืนยันและตรวจสุขภาพระบบ"
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $lifecycle -Action Start -HealthTimeoutSeconds 45 -Port $ConfirmedPort | Out-Host
    $lifecycleExitCode = $LASTEXITCODE
    if ($lifecycleExitCode -ne 0) {
        throw "Local Bridge เปิดด้วยพอร์ตที่ยืนยันไม่สำเร็จ กรุณาเลือก Local endpoint ใหม่ โดยระบบจะไม่ปิดโปรแกรมอื่นหรือเปลี่ยน URL เอง"
    }

    $endpoint = Get-ConfirmedBridgeEndpoint
    if ([int]$endpoint.Port -ne $ConfirmedPort) {
        throw "Local Bridge ใช้พอร์ตไม่ตรงกับ URL ที่ผู้ใช้ยืนยัน"
    }
    $health = Invoke-RestMethod -Uri $endpoint.HealthUrl -Method Get -TimeoutSec 5
    $healthEndpoint = $null
    $healthProperties = if ($health) { @($health.PSObject.Properties.Name) } else { @() }
    if ($healthProperties -contains "endpoint") {
        $healthEndpoint = $health.endpoint
    }
    $healthEndpointProperties = if ($healthEndpoint) { @($healthEndpoint.PSObject.Properties.Name) } else { @() }
    $healthOk = $healthProperties -contains "ok" -and $health.ok -eq $true
    $healthReady = $healthProperties -contains "status" -and $health.status -eq "ready"
    $healthEndpointMatches = (
        $healthEndpointProperties -contains "host" -and
        $healthEndpointProperties -contains "port" -and
        [string]$healthEndpoint.host -ceq $endpoint.Host -and
        [int]$healthEndpoint.port -eq $endpoint.Port
    )
    if (
        -not $healthOk -or
        -not $healthReady -or
        -not $healthEndpointMatches
    ) {
        throw "Local Bridge ตอบกลับแต่ endpoint จาก Health check ไม่ตรงกับค่าที่บันทึกไว้"
    }
    return $endpoint
}

function Get-SafeCodexReadiness {
    param([Parameter(Mandatory = $true)]$Endpoint)

    $codexStatus = "unavailable"
    $codexVersion = $null
    try {
        $bridgeStatus = Invoke-RestMethod -Uri ("{0}api/bridge/status" -f $Endpoint.Url) -Method Get -TimeoutSec 20
        if ($bridgeStatus -and $bridgeStatus.codex) {
            $candidateStatus = [string]$bridgeStatus.codex.status
            if ($candidateStatus -in @("ready", "ready_guarded", "auth_required", "config_error", "blocked", "degraded", "missing", "unknown")) {
                $codexStatus = $candidateStatus
            }
            $candidateVersion = [string]$bridgeStatus.codex.version
            if ($candidateVersion -and $candidateVersion.Length -le 120) {
                $codexVersion = $candidateVersion
            }
        }
    }
    catch {
        $codexStatus = "unavailable"
    }

    $rateStatus = "unavailable"
    $usedPercent = $null
    $remainingPercent = $null
    $resetsAt = $null
    $stale = $false
    $limitReached = $false
    try {
        $rate = Invoke-RestMethod -Uri ("{0}api/codex/rate-limits?refresh=true" -f $Endpoint.Url) -Method Get -TimeoutSec 25
        if ($rate) {
            $candidateRateStatus = [string]$rate.status
            if ($candidateRateStatus -in @("ready", "auth_required", "config_error", "timeout", "missing", "unavailable")) {
                $rateStatus = $candidateRateStatus
            }
            if ($rate.ok -eq $true -and $rate.primary) {
                $usedPercent = [double]$rate.primary.usedPercent
                $remainingPercent = [double]$rate.primary.remainingPercent
                $resetsAt = [string]$rate.primary.resetsAt
                $stale = [bool]$rate.stale
                $limitReached = [bool]$rate.limitReached
            }
        }
    }
    catch {
        $rateStatus = "unavailable"
    }

    return [pscustomobject]@{
        CodexStatus = $codexStatus
        CodexVersion = $codexVersion
        RateStatus = $rateStatus
        UsedPercent = $usedPercent
        RemainingPercent = $remainingPercent
        ResetsAt = $resetsAt
        Stale = $stale
        LimitReached = $limitReached
    }
}

function Show-CodexReadiness {
    param([Parameter(Mandatory = $true)]$Readiness)

    $versionText = if ($Readiness.CodexVersion) { " ($($Readiness.CodexVersion))" } else { "" }
    switch ([string]$Readiness.CodexStatus) {
        { $_ -in @("ready", "ready_guarded") } {
            Write-Host "Codex ของ Windows User นี้: เชื่อมต่อแล้ว$versionText" -ForegroundColor Green
            break
        }
        "auth_required" {
            Write-Host "Codex ของ Windows User นี้: ต้อง Login ด้วยบัญชีของนักเรียนก่อน" -ForegroundColor Yellow
            break
        }
        "config_error" {
            Write-Host "Codex ของ Windows User นี้: พบ Config ที่ Codex CLI ไม่รองรับ กรุณาแก้ Config แล้วตรวจใหม่" -ForegroundColor Yellow
            break
        }
        default {
            Write-Host "Codex ของ Windows User นี้: ยังตรวจความพร้อมไม่ได้ ($($Readiness.CodexStatus))" -ForegroundColor Yellow
        }
    }

    if ([string]$Readiness.RateStatus -eq "ready") {
        $staleText = if ($Readiness.Stale) { " • ข้อมูลล่าสุดที่บันทึกไว้" } else { "" }
        $limitText = if ($Readiness.LimitReached) { " • ถึงขีดจำกัดแล้ว" } else { "" }
        Write-Host ("Rate Limit Codex ของบัญชีเครื่องนี้: เหลือ {0}% • ใช้แล้ว {1}% • รีเซ็ต {2}{3}{4}" -f `
            $Readiness.RemainingPercent, $Readiness.UsedPercent, $Readiness.ResetsAt, $staleText, $limitText) -ForegroundColor Green
    }
    elseif ([string]$Readiness.RateStatus -eq "auth_required") {
        Write-Host "Rate Limit Codex: ยังอ่านไม่ได้จนกว่านักเรียนจะ Login ด้วยบัญชีของตนเอง" -ForegroundColor Yellow
    }
    elseif ([string]$Readiness.RateStatus -eq "config_error") {
        Write-Host "Rate Limit Codex: ยังอ่านไม่ได้เพราะ Config ของ Codex CLI ไม่รองรับ" -ForegroundColor Yellow
    }
    else {
        Write-Host "Rate Limit Codex: ยังตรวจไม่ได้ ($($Readiness.RateStatus)) แต่ HQ โหมด Local/Demo ยังใช้งานได้" -ForegroundColor Yellow
    }

    Write-InstallLog -Message ("Codex readiness: codex={0}; rate={1}; remaining={2}; stale={3}; limit_reached={4}" -f `
        $Readiness.CodexStatus, $Readiness.RateStatus, $Readiness.RemainingPercent, $Readiness.Stale, $Readiness.LimitReached)
}

function Write-InstallResult {
    param(
        [Parameter(Mandatory = $true)]$Endpoint,
        [Parameter(Mandatory = $true)]$Readiness
    )

    $versionPath = Join-Path $installRoot "VERSION"
    $version = if (Test-Path -LiteralPath $versionPath -PathType Leaf) {
        (Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8).Trim()
    }
    else {
        "unknown"
    }
    $result = [ordered]@{
        version = 1
        installed_at = [DateTime]::UtcNow.ToString("o")
        application_version = $version
        install_root = $installRoot
        endpoint = [ordered]@{
            host = "127.0.0.1"
            port = [int]$Endpoint.Port
            url = [string]$Endpoint.Url
            health_url = [string]$Endpoint.HealthUrl
            health = "ready"
        }
        codex = [ordered]@{
            status = [string]$Readiness.CodexStatus
            version = $Readiness.CodexVersion
            rate_limit_status = [string]$Readiness.RateStatus
            used_percent = $Readiness.UsedPercent
            remaining_percent = $Readiness.RemainingPercent
            resets_at = $Readiness.ResetsAt
            stale = [bool]$Readiness.Stale
            limit_reached = [bool]$Readiness.LimitReached
            account_identity_stored = $false
        }
        safety = [ordered]@{
            loopback_only = $true
            frontend_secrets = $false
            live_trading_enabled = $false
            telegram_real_send_enabled = $false
        }
    }
    $temporaryPath = "$installResultPath.tmp.$([Guid]::NewGuid().ToString('N'))"
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($temporaryPath, ($result | ConvertTo-Json -Depth 6) + [Environment]::NewLine, $utf8)
    Move-Item -LiteralPath $temporaryPath -Destination $installResultPath -Force
}

try {
    Assert-SafeSource
    if ($ListAvailableEndpoints) {
        $candidates = @(Get-AvailableBridgeEndpointCandidates -Count 3)
        [pscustomobject]@{
            ok = $true
            host = "127.0.0.1"
            note = "IP ถูกล็อกเพื่อใช้เฉพาะเครื่องนี้ เลือกได้เฉพาะหมายเลข Port"
            candidates = $candidates
        } | ConvertTo-Json -Depth 5
        exit 0
    }

    $selectedBridgePort = Confirm-BridgeEndpoint
    Write-InstallLog -Message ("เริ่ม {0} หลังผู้ใช้ยืนยัน http://127.0.0.1:{1}/" -f `
        $(if ($RepairOnly) { "ซ่อมแซม" } else { "ติดตั้ง" }), $selectedBridgePort)
    Stop-ExistingBridge
    if (-not (Test-LoopbackPortAvailable -CandidatePort $selectedBridgePort)) {
        throw "พอร์ตที่ผู้ใช้ยืนยัน ($selectedBridgePort) ไม่ว่างหลังหยุด HQ เดิม ระบบหยุดโดยไม่เปลี่ยน URL"
    }
    if (-not $RepairOnly) {
        Copy-ApplicationFiles
    }
    elseif (-not (Get-ComparablePath -Path $sourceRoot).Equals((Get-ComparablePath -Path $installRoot), [StringComparison]::OrdinalIgnoreCase)) {
        throw "การซ่อมแซมต้องเรียกจากชุด Installer ที่อยู่ในโฟลเดอร์ติดตั้ง"
    }

    Initialize-UserDataDirectories
    $venvPython = Initialize-PythonEnvironment
    Test-InstalledApplication -PythonPath $venvPython
    if (-not $SkipShortcuts) {
        Install-Shortcuts
    }

    $bridgeEndpoint = $null
    $codexReadiness = $null
    if (-not $SkipLaunch) {
        $bridgeEndpoint = Start-And-TestBridge -ConfirmedPort $selectedBridgePort
        $codexReadiness = Get-SafeCodexReadiness -Endpoint $bridgeEndpoint
        Show-CodexReadiness -Readiness $codexReadiness
        Write-InstallResult -Endpoint $bridgeEndpoint -Readiness $codexReadiness
        Start-Process $bridgeEndpoint.Url
    }

    Write-Step "ติดตั้งและตรวจสอบสำเร็จ ข้อมูลเริ่มต้นเป็นแบบ Local/Demo และไม่ได้ Login หรือเปิด Live Trading ให้อัตโนมัติ"
    Write-Host "ตำแหน่งโปรแกรม: $installRoot" -ForegroundColor Green
    if ($bridgeEndpoint) {
        Write-Host "หน้าโปรแกรม: $($bridgeEndpoint.Url)" -ForegroundColor Green
        Write-Host "รายงานการติดตั้ง: $installResultPath" -ForegroundColor Green
    }
    else {
        Write-Host "ยังไม่ได้เปิด Bridge ในขั้นตอนนี้ ให้เปิดจาก Shortcut เพื่อเลือกและยืนยัน Local endpoint" -ForegroundColor Yellow
    }
    Write-Host "หากต้องใช้ Codex ให้นักเรียน Login ด้วยบัญชีของตนเองภายหลัง" -ForegroundColor Yellow
    exit 0
}
catch {
    $message = [string]$_.Exception.Message
    $safeMessage = $message -replace '(?i)(token|password|secret|cookie|authorization)\s*[:=]\s*\S+', '$1=[REDACTED]'
    Write-InstallLog -Message ("ล้มเหลว: {0}" -f $safeMessage)
    Write-Error $safeMessage
    exit 1
}
