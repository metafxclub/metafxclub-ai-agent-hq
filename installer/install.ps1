[CmdletBinding()]
param(
    [switch]$RepairOnly,
    [switch]$SkipLaunch,
    [switch]$SkipShortcuts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$sourceRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd("\")
$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ")).TrimEnd("\")
$installLog = Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ-Install.log"
$requirementsName = "requirements-runner.txt"
$bridgeUrl = "http://127.0.0.1:4186/"
$healthUrl = "${bridgeUrl}api/health"

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

function Get-ComparablePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    return [IO.Path]::GetFullPath($Path).TrimEnd("\")
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
        "auth.json", "secrets.json", "id_rsa", "id_ed25519"
    )
    $allowedDirectories = @("backend", "contracts", "docs", "frontend", "installer", "runner", "scripts", "tests")
    foreach ($directoryName in $allowedDirectories) {
        $directory = Join-Path $sourceRoot $directoryName
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            continue
        }
        foreach ($item in Get-ChildItem -LiteralPath $directory -Recurse -Force) {
            if ($item.FullName -match "[\\/]\.venv(?:[\\/]|$)" -or $item.FullName -match "[\\/]__pycache__(?:[\\/]|$)") {
                continue
            }
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "หยุดติดตั้งเพื่อความปลอดภัย: ชุดแจกมี Link/Junction ที่ไม่ได้รับอนุญาต ($($item.Name))"
            }
            if ($item.PSIsContainer) {
                continue
            }
            if ($blockedNames -contains $item.Name.ToLowerInvariant() -or $item.Extension.ToLowerInvariant() -in @(".pem", ".key", ".pfx", ".p12")) {
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
        "/XF", ".env", ".env.*", "*.pem", "*.key", "*.pfx", "*.p12", "credentials*.json", "cookies*.json", "auth*.json", "secrets*.json",
        "/XD", ".git", ".venv", "__pycache__", (Join-Path $sourceDirectory ".git"), (Join-Path $sourceDirectory ".venv"), (Join-Path $sourceDirectory "__pycache__"),
        (Join-Path $destinationDirectory ".git"), (Join-Path $destinationDirectory ".venv"), (Join-Path $destinationDirectory "__pycache__")
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
    $lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
    Write-Step "กำลังเปิด Local Bridge เฉพาะที่ 127.0.0.1 และตรวจสุขภาพระบบ"
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $lifecycle -Action Start -HealthTimeoutSeconds 45
    if ($LASTEXITCODE -ne 0) {
        throw "Local Bridge เปิดไม่สำเร็จ กรุณาตรวจว่า Port 4186 ถูกโปรแกรมอื่นใช้อยู่หรือไม่"
    }

    $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5
    if ($health.ok -ne $true -or $health.status -ne "ready") {
        throw "Local Bridge ตอบกลับแต่ยังไม่พร้อมใช้งาน"
    }
}

try {
    Write-InstallLog -Message ("เริ่ม {0}" -f $(if ($RepairOnly) { "ซ่อมแซม" } else { "ติดตั้ง" }))
    Assert-SafeSource
    Stop-ExistingBridge
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

    if (-not $SkipLaunch) {
        Start-And-TestBridge
        Start-Process $bridgeUrl
    }

    Write-Step "ติดตั้งและตรวจสอบสำเร็จ ข้อมูลเริ่มต้นเป็นแบบ Local/Demo และไม่ได้ Login หรือเปิด Live Trading ให้อัตโนมัติ"
    Write-Host "ตำแหน่งโปรแกรม: $installRoot" -ForegroundColor Green
    Write-Host "หน้าโปรแกรม: $bridgeUrl" -ForegroundColor Green
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
