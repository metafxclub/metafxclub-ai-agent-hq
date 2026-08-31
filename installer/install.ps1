[CmdletBinding()]
param(
    [switch]$RepairOnly,
    [switch]$SkipLaunch,
    [switch]$SkipShortcuts,
    [switch]$SkipGoogleSetup,
    [switch]$SkipAutostart,
    [string]$GoogleClientJsonPath = "",
    [string]$ExpectedGoogleClientId = "",
    [string]$ExpectedGitRepository = "",
    [string]$ExpectedGitTag = "",
    [string]$ExpectedSourceVersion = "",
    [string]$ExpectedGitCommit = "",
    [switch]$RequireVerifiedGitSource,
    [switch]$PrePublishVerification,
    [switch]$ListAvailableEndpoints,
    [switch]$PackageSmoke,
    [switch]$PackageUpgradeSmoke,
    [switch]$PackageSmokeFailAfterPublish,
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
$bridgeTaskName = "Metafxclub AI Agent HQ Bridge"
$bridgeTaskWatchdogMinutes = 15
$bridgeTaskPreviousPort = 0
$bridgeTaskExisted = $false
$applicationRollbackState = $null
$applicationMutationStarted = $false
$previousBridgeWasRunning = $false
$previousBridgeWasHealthy = $false
$previousBridgeRuntimeIdentity = $null
$previousBridgeWasStopped = $false
$candidateBridgeMayBeRunning = $false
$rollbackIncomplete = $false
$postInstallFailures = New-Object 'System.Collections.Generic.List[string]'
$watchdogStatus = "pending"
$watchdogFailure = $false
$googleSetupFailure = $false
$validatedSourceCommit = ""

$gitProvenanceValues = @($ExpectedGitRepository, $ExpectedGitTag, $ExpectedSourceVersion)
$gitProvenanceValueCount = @($gitProvenanceValues | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
if ($gitProvenanceValueCount -ne 0 -and $gitProvenanceValueCount -ne 3) {
    throw "โหมดตรวจ Git ต้องระบุ ExpectedGitRepository, ExpectedGitTag และ ExpectedSourceVersion ให้ครบ"
}
if ($RequireVerifiedGitSource -and $gitProvenanceValueCount -ne 3) {
    throw "โหมดติดตั้งด้วย Prompt ต้องเปิดการตรวจ Git และระบุ Repository, Tag และ Version ให้ครบ"
}
if ($PrePublishVerification) {
    if (-not $PackageSmoke -or -not $RequireVerifiedGitSource) {
        throw "PrePublishVerification ใช้ได้เฉพาะ Package Smoke ที่ตรวจ Git Source เต็มรูปแบบ"
    }
    if ($ExpectedGitCommit.Trim() -notmatch '^[A-Fa-f0-9]{40,64}$') {
        throw "PrePublishVerification ต้องระบุ ExpectedGitCommit แบบเต็ม"
    }
}
elseif (-not [string]::IsNullOrWhiteSpace($ExpectedGitCommit)) {
    throw "ExpectedGitCommit ใช้ได้เฉพาะ PrePublishVerification"
}
if ($PackageUpgradeSmoke -and -not $PackageSmoke) {
    throw "PackageUpgradeSmoke ต้องใช้ร่วมกับ PackageSmoke"
}
if ($PackageSmokeFailAfterPublish -and -not $PackageUpgradeSmoke) {
    throw "PackageSmokeFailAfterPublish ใช้ได้เฉพาะ PackageUpgradeSmoke"
}
if ($gitProvenanceValueCount -eq 3) {
    $officialRepository = "https://github.com/metafxclub/metafxclub-ai-agent-hq.git"
    if (-not [string]::Equals($ExpectedGitRepository.Trim(), $officialRepository, [StringComparison]::OrdinalIgnoreCase)) {
        throw "ExpectedGitRepository ต้องเป็น Repository ทางการของ Metafxclub AI Agent HQ"
    }
    if ($ExpectedGitTag.Trim() -notmatch '^v\d+\.\d+\.\d+$') {
        throw "ExpectedGitTag ต้องเป็น Tag แบบ vMAJOR.MINOR.PATCH"
    }
    if ($ExpectedSourceVersion.Trim() -notmatch '^\d+\.\d+\.\d+$') {
        throw "ExpectedSourceVersion ต้องเป็น Version แบบ MAJOR.MINOR.PATCH"
    }
    if ($ExpectedGitTag.Trim().Substring(1) -cne $ExpectedSourceVersion.Trim()) {
        throw "ExpectedGitTag และ ExpectedSourceVersion ไม่ตรงกัน"
    }
}

if (
    [string]::IsNullOrWhiteSpace($GoogleClientJsonPath) -xor
    [string]::IsNullOrWhiteSpace($ExpectedGoogleClientId)
) {
    throw "การตั้งค่า Google แบบครั้งเดียวต้องระบุทั้ง GoogleClientJsonPath และ ExpectedGoogleClientId"
}
if (
    -not [string]::IsNullOrWhiteSpace($ExpectedGoogleClientId) -and
    $ExpectedGoogleClientId.Trim() -notmatch '^[A-Za-z0-9._-]+\.apps\.googleusercontent\.com$'
) {
    throw "ExpectedGoogleClientId ไม่ใช่ Google OAuth Client ID ที่รองรับ"
}

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

function Split-InstallerCommandLine {
    param([Parameter(Mandatory = $true)][string]$CommandLine)

    $tokens = New-Object System.Collections.Generic.List[string]
    foreach ($match in [regex]::Matches($CommandLine, '(?:"[^"]*"|[^\s"]+)')) {
        $value = [string]$match.Value
        if ($value.Length -ge 2 -and $value[0] -eq '"' -and $value[$value.Length - 1] -eq '"') {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $tokens.Add($value)
    }
    return $tokens.ToArray()
}

function Get-InstalledBridgeListenerIdentity {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$CandidatePort)

    $expectedServer = Join-Path $installRoot "backend\local-runner\bridge_server.py"
    if (-not (Test-Path -LiteralPath $expectedServer -PathType Leaf)) {
        return $null
    }
    try {
        $listenerIds = @(
            Get-NetTCPConnection -LocalPort $CandidatePort -State Listen -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty OwningProcess -Unique
        )
        if ($listenerIds.Count -ne 1) {
            return $null
        }
        $processId = [int]$listenerIds[0]
        $record = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
        if (
            -not $record -or
            ([string]$record.Name) -notin @("python.exe", "pythonw.exe") -or
            [string]::IsNullOrWhiteSpace([string]$record.CommandLine) -or
            [string]::IsNullOrWhiteSpace([string]$record.ExecutablePath)
        ) {
            return $null
        }
        $tokens = @(Split-InstallerCommandLine -CommandLine ([string]$record.CommandLine))
        if ($tokens.Count -ne 6) {
            return $null
        }
        $commandExecutable = Get-ComparablePath -Path ([string]$tokens[0])
        $recordExecutable = Get-ComparablePath -Path ([string]$record.ExecutablePath)
        $commandServer = Get-ComparablePath -Path ([string]$tokens[1])
        $expectedServerPath = Get-ComparablePath -Path $expectedServer
        $parsedPort = 0
        if (
            -not $commandExecutable.Equals($recordExecutable, [StringComparison]::OrdinalIgnoreCase) -or
            -not $commandServer.Equals($expectedServerPath, [StringComparison]::OrdinalIgnoreCase) -or
            [string]$tokens[2] -cne "--host" -or
            [string]$tokens[3] -cne "127.0.0.1" -or
            [string]$tokens[4] -cne "--port" -or
            -not [int]::TryParse([string]$tokens[5], [ref]$parsedPort) -or
            $parsedPort -ne $CandidatePort
        ) {
            return $null
        }
        return [pscustomobject]@{
            ProcessId = $processId
            Port = $CandidatePort
            PythonPath = [string]$record.ExecutablePath
            ServerPath = $expectedServer
        }
    }
    catch {
        return $null
    }
}

function Get-SavedBridgeEndpointState {
    if (-not (Test-Path -LiteralPath $bridgeEndpointPath -PathType Leaf)) {
        return $null
    }

    try {
        $installedVersionPath = Join-Path $installRoot "VERSION"
        if (-not (Test-Path -LiteralPath $installedVersionPath -PathType Leaf)) {
            return $null
        }
        $installedVersion = (Get-Content -LiteralPath $installedVersionPath -Raw -Encoding UTF8).Trim()
        $saved = Get-Content -LiteralPath $bridgeEndpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $savedPort = [int]$saved.port
        if ([string]$saved.host -cne "127.0.0.1" -or $savedPort -lt 1024 -or $savedPort -gt 65535) {
            return $null
        }

        # A 503 response is not sufficient proof of ownership. Reuse an occupied
        # endpoint only when the sole listener PID has the exact installed
        # Python/server/loopback command line. Arbitrary local listeners remain
        # fail-closed and are never eligible for Stop-ExistingBridge.
        $identity = Get-InstalledBridgeListenerIdentity -CandidatePort $savedPort
        if (-not $identity) {
            return $null
        }

        $healthy = $false
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$savedPort/api/health" -Method Get -TimeoutSec 2
            $healthy = (
                $health.ok -eq $true -and
                [string]$health.status -ceq "ready" -and
                [string]$health.server -ceq "Metafx Local Bridge" -and
                [string]$health.version -ceq $installedVersion -and
                $health.endpoint -and
                [string]$health.endpoint.host -ceq "127.0.0.1" -and
                [int]$health.endpoint.port -eq $savedPort
            )
        }
        catch {
            # A proven legacy Bridge can deliberately report 503/degraded. Its
            # exact listener identity above is authoritative for upgrade safety.
            $healthy = $false
        }

        return [pscustomobject]@{
            Host = "127.0.0.1"
            Port = $savedPort
            Url = "http://127.0.0.1:$savedPort/"
            Reusable = $true
            Running = $true
            Healthy = [bool]$healthy
            Reason = $(if ($healthy) {
                "HQ เดิมกำลังใช้งานอยู่และสามารถใช้ URL เดิมต่อได้"
            } else {
                "ยืนยันตัวตน HQ เดิมแล้ว แม้ Health ยัง degraded; Installer จะอัปเกรดที่ URL เดิมอย่างปลอดภัย"
            })
            RuntimeIdentity = $identity
        }
    }
    catch {
        return $null
    }
}

function Get-HealthySavedEndpoint {
    $state = Get-SavedBridgeEndpointState
    if ($state -and $state.Healthy) {
        return $state
    }
    return $null
}

function Get-AvailableBridgeEndpointCandidates {
    param([ValidateRange(1, 8)][int]$Count = 3)

    $results = New-Object System.Collections.Generic.List[object]
    $seen = New-Object 'System.Collections.Generic.HashSet[int]'
    $saved = Get-SavedBridgeEndpointState
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

    $saved = Get-SavedBridgeEndpointState
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
            "import json,platform,struct,sys; print(json.dumps({'major':sys.version_info[0],'minor':sys.version_info[1],'micro':sys.version_info[2],'executable':sys.executable,'bits':struct.calcsize('P')*8,'machine':platform.machine()}))"
        )
        $raw = & $FilePath @arguments 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) {
            return $null
        }
        $details = ($raw | Select-Object -Last 1) | ConvertFrom-Json
        if (
            [int]$details.major -ne 3 -or
            [int]$details.minor -lt 10 -or
            [int]$details.minor -gt 14 -or
            [int]$details.bits -ne 64
        ) {
            return $null
        }
        return [pscustomobject]@{
            FilePath = $FilePath
            PrefixArguments = @($PrefixArguments)
            Version = "{0}.{1}.{2}" -f $details.major, $details.minor, $details.micro
            Executable = [string]$details.executable
            Architecture = "{0}-bit {1}" -f $details.bits, $details.machine
        }
    }
    catch {
        return $null
    }
}

function Resolve-SystemPython {
    $launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($launcher) {
        # Try every supported minor explicitly before the launcher's default.
        # A machine can have Python 3.11 installed while `py -3` points to a
        # newer unsupported interpreter, which must not become a false failure.
        foreach ($selector in @("-3.14", "-3.13", "-3.12", "-3.11", "-3.10", "-3")) {
            $candidate = Test-PythonCommand -FilePath $launcher.Source -PrefixArguments @($selector)
            if ($candidate) {
                return $candidate
            }
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

    throw "ไม่พบ Python 3.10-3.14 แบบ 64-bit กรุณาติดตั้ง Python x64 จาก python.org และเลือก Add Python to PATH แล้วเปิด Installer อีกครั้ง ระบบจะไม่ดาวน์โหลด Python หรือขอสิทธิ์ Administrator ให้อัตโนมัติ"
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

function Get-Sha256Hex {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)

    # Use .NET directly instead of Get-FileHash. Codex can launch Windows
    # PowerShell from a PowerShell 7 parent whose inherited PSModulePath points
    # at incompatible modules, causing cmdlet auto-loading to fail on an
    # otherwise valid student machine.
    $stream = [IO.File]::OpenRead($LiteralPath)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha256.ComputeHash($stream)
        return ([BitConverter]::ToString($hashBytes)).Replace("-", "").ToUpperInvariant()
    }
    finally {
        $sha256.Dispose()
        $stream.Dispose()
    }
}

function Invoke-GitSourceCapture {
    param(
        [Parameter(Mandatory = $true)][string]$GitPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    $gitDirectory = Join-Path $sourceRoot ".git"
    $savedGitEnvironment = @{}
    foreach ($entry in @(Get-ChildItem Env: | Where-Object { $_.Name -like "GIT_*" })) {
        $savedGitEnvironment[[string]$entry.Name] = [string]$entry.Value
        [Environment]::SetEnvironmentVariable([string]$entry.Name, $null, "Process")
    }
    [Environment]::SetEnvironmentVariable("GIT_TERMINAL_PROMPT", "0", "Process")
    try {
        $gitArguments = @(
            "--no-replace-objects",
            "--git-dir=$gitDirectory",
            "--work-tree=$sourceRoot",
            "-c", "core.fsmonitor=false"
        ) + @($Arguments)
        $output = @(& $GitPath @gitArguments 2>$null)
        $nativeExitCode = $LASTEXITCODE
        if ($nativeExitCode -ne 0) {
            throw "$FailureMessage (Git รหัส $nativeExitCode)"
        }
        return (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
    finally {
        [Environment]::SetEnvironmentVariable("GIT_TERMINAL_PROMPT", $null, "Process")
        foreach ($name in $savedGitEnvironment.Keys) {
            [Environment]::SetEnvironmentVariable([string]$name, [string]$savedGitEnvironment[$name], "Process")
        }
    }
}

function Invoke-GitRemoteCapture {
    param(
        [Parameter(Mandatory = $true)][string]$GitPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    $savedGitEnvironment = @{}
    foreach ($entry in @(Get-ChildItem Env: | Where-Object { $_.Name -like "GIT_*" })) {
        $savedGitEnvironment[[string]$entry.Name] = [string]$entry.Value
        [Environment]::SetEnvironmentVariable([string]$entry.Name, $null, "Process")
    }
    [Environment]::SetEnvironmentVariable("GIT_TERMINAL_PROMPT", "0", "Process")
    try {
        $output = @(& $GitPath --no-replace-objects @Arguments 2>$null)
        $nativeExitCode = $LASTEXITCODE
        if ($nativeExitCode -ne 0) {
            throw "$FailureMessage (Git รหัส $nativeExitCode)"
        }
        return (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
    finally {
        [Environment]::SetEnvironmentVariable("GIT_TERMINAL_PROMPT", $null, "Process")
        foreach ($name in $savedGitEnvironment.Keys) {
            [Environment]::SetEnvironmentVariable([string]$name, [string]$savedGitEnvironment[$name], "Process")
        }
    }
}

function Assert-ExpectedGitSource {
    if ([string]::IsNullOrWhiteSpace($ExpectedGitRepository)) {
        return
    }

    $gitDirectory = Join-Path $sourceRoot ".git"
    if (-not (Test-Path -LiteralPath $gitDirectory -PathType Container)) {
        throw "โหมด Git Clone ต้องเรียก Installer จาก Git Repository ที่ตรวจสอบได้"
    }
    $gitCommand = Get-Command git.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $gitCommand) {
        throw "ไม่พบ Git for Windows สำหรับตรวจ Source"
    }

    $topLevel = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("rev-parse", "--show-toplevel") -FailureMessage "ตรวจ Git worktree root ไม่สำเร็จ"
    $resolvedGitDirectory = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("rev-parse", "--absolute-git-dir") -FailureMessage "ตรวจ Git directory ไม่สำเร็จ"
    if (
        -not (Get-ComparablePath -Path $topLevel).Equals((Get-ComparablePath -Path $sourceRoot), [StringComparison]::OrdinalIgnoreCase) -or
        -not (Get-ComparablePath -Path $resolvedGitDirectory).Equals((Get-ComparablePath -Path $gitDirectory), [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "หยุดติดตั้ง: Git worktree หรือ Git directory ไม่ตรงกับ Source ของ Installer"
    }

    $origin = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("remote", "get-url", "origin") -FailureMessage "อ่าน Git origin ไม่สำเร็จ"
    if (-not [string]::Equals($origin, $ExpectedGitRepository.Trim(), [StringComparison]::OrdinalIgnoreCase)) {
        throw "หยุดติดตั้ง: Git origin ไม่ตรงกับ Repository ที่ล็อกไว้"
    }

    $headCommit = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("rev-parse", "--verify", "HEAD^{commit}") -FailureMessage "อ่าน Git HEAD ไม่สำเร็จ"
    $tagCommitReference = "refs/tags/$($ExpectedGitTag.Trim())^{commit}"
    $tagCommit = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("rev-parse", "--verify", $tagCommitReference) -FailureMessage "ไม่พบ Git Tag ที่ล็อกไว้ใน Source"
    if (
        $headCommit -notmatch '^[A-Fa-f0-9]{40,64}$' -or
        $tagCommit -notmatch '^[A-Fa-f0-9]{40,64}$' -or
        -not [string]::Equals($headCommit, $tagCommit, [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "หยุดติดตั้ง: Git HEAD ไม่ตรงกับ Tag ที่ล็อกไว้"
    }

    if ($PrePublishVerification) {
        if (-not [string]::Equals($headCommit, $ExpectedGitCommit.Trim(), [StringComparison]::OrdinalIgnoreCase)) {
            throw "หยุดตรวจ Pre-publish: Git HEAD ไม่ตรงกับ Commit ของ Workflow"
        }
    }
    else {
        $remoteTagReference = "refs/tags/$($ExpectedGitTag.Trim())"
        $remoteTagOutput = Invoke-GitRemoteCapture `
            -GitPath $gitCommand.Source `
            -Arguments @(
                "ls-remote", "--exit-code", "--tags", $officialRepository,
                $remoteTagReference, "$remoteTagReference^{}"
            ) `
            -FailureMessage "ตรวจ Git Tag จาก GitHub ทางการไม่สำเร็จ"
        $remoteDirectCommit = ""
        $remotePeeledCommit = ""
        foreach ($line in @($remoteTagOutput -split "`r?`n")) {
            if ($line -notmatch '^([A-Fa-f0-9]{40,64})\s+(.+)$') {
                continue
            }
            if ([string]$Matches[2] -ceq $remoteTagReference) {
                $remoteDirectCommit = [string]$Matches[1]
            }
            elseif ([string]$Matches[2] -ceq "$remoteTagReference^{}") {
                $remotePeeledCommit = [string]$Matches[1]
            }
        }
        $remoteCommit = if ($remotePeeledCommit) { $remotePeeledCommit } else { $remoteDirectCommit }
        if (
            $remoteCommit -notmatch '^[A-Fa-f0-9]{40,64}$' -or
            -not [string]::Equals($headCommit, $remoteCommit, [StringComparison]::OrdinalIgnoreCase)
        ) {
            throw "หยุดติดตั้ง: Git HEAD ไม่ตรงกับ Tag ที่เผยแพร่บน GitHub ทางการ"
        }
    }

    $branch = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("branch", "--show-current") -FailureMessage "ตรวจ Git Branch ไม่สำเร็จ"
    if (-not [string]::IsNullOrWhiteSpace($branch)) {
        throw "หยุดติดตั้ง: Source ต้อง Checkout จาก Tag แบบ detached ไม่ใช่ Branch ที่เปลี่ยนแปลงได้"
    }
    $worktreeStatus = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("status", "--porcelain", "--untracked-files=all") -FailureMessage "ตรวจ Git worktree ไม่สำเร็จ"
    if (-not [string]::IsNullOrWhiteSpace($worktreeStatus)) {
        throw "หยุดติดตั้ง: Source มีไฟล์แก้ไขหรือไฟล์ใหม่ที่ไม่อยู่ใน Tag"
    }
    $indexFlags = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("ls-files", "-v") -FailureMessage "ตรวจ Git index flags ไม่สำเร็จ"
    if (@($indexFlags -split "`r?`n" | Where-Object { $_ -cmatch '^(?:[a-z]|S)\s' }).Count -gt 0) {
        throw "หยุดติดตั้ง: Git index มี assume-unchanged หรือ skip-worktree ซึ่งอาจซ่อนไฟล์ที่แก้ไข"
    }

    $sourceVersion = Invoke-GitSourceCapture -GitPath $gitCommand.Source -Arguments @("show", "$headCommit`:VERSION") -FailureMessage "อ่าน VERSION จาก Git Tag ไม่สำเร็จ"
    if ($sourceVersion -cne $ExpectedSourceVersion.Trim()) {
        throw "หยุดติดตั้ง: VERSION ใน Source ไม่ตรงกับ Version ที่ล็อกไว้"
    }

    $script:validatedSourceCommit = $headCommit.ToLowerInvariant()
}

function Assert-SafeSource {
    Assert-ExpectedGitSource

    $requiredFiles = @(
        ".gitattributes",
        ".gitignore",
        "VERSION",
        "backend\local-runner\bridge_server.py",
        "backend\local-runner\configure_google_oauth_client.py",
        "frontend\index.html",
        "integrations\mt4-trade-gateway\MetafxHQTradeGateway.mq4",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\MetafxHQTradeGateway.mq4",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\MetafxHQTradeGateway.ex4",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\README_TH.md",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\AUDIT_TH.md",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\SHA256SUMS.txt",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\BUILD_LOG.txt",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\MANIFEST.json",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\COMPILE_PROOF.png",
        "runner\codex_cli_runner.py",
        "scripts\register-bridge-autostart.ps1",
        "scripts\run-bridge-watchdog-hidden.vbs",
        "scripts\setup-google-oauth.ps1",
        "scripts\start-local-bridge.ps1",
        "2-SETUP-GOOGLE-HQ.bat",
        "docs\prompts\install-github-google-auto-th.md",
        "tests\release_secret_scan.py",
        "tests\test_release_candidate_preflight.py",
        "tests\test_runtime_integrity.py",
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
    $allowedDirectories = @(".github", "backend", "contracts", "docs", "frontend", "installer", "integrations", "runner", "scripts", "tests")
    $excludedDirectoryNames = @(".venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build")
    foreach ($directoryName in $allowedDirectories) {
        $directory = Join-Path $sourceRoot $directoryName
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            continue
        }
        $pendingDirectories = New-Object 'System.Collections.Generic.Stack[string]'
        $pendingDirectories.Push($directory)
        while ($pendingDirectories.Count -gt 0) {
            $currentDirectory = $pendingDirectories.Pop()
            foreach ($item in Get-ChildItem -LiteralPath $currentDirectory -Force) {
                if ($item.PSIsContainer -and $excludedDirectoryNames -contains $item.Name) {
                    # Do not recurse into generated dependency/build trees.
                    continue
                }
                if ($item.PSIsContainer -and $item.Name -ieq ".codex") {
                    throw "หยุดติดตั้งเพื่อความปลอดภัย: พบโฟลเดอร์ .codex ในชุดแจก"
                }
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "หยุดติดตั้งเพื่อความปลอดภัย: ชุดแจกมี Link/Junction ที่ไม่ได้รับอนุญาต ($($item.Name))"
                }
                if ($item.PSIsContainer) {
                    $pendingDirectories.Push($item.FullName)
                    continue
                }
                if ($item.Extension.ToLowerInvariant() -in @(".log", ".jsonl", ".bak", ".tmp")) {
                    # ไฟล์เหล่านี้ถูกตัดออกโดย Robocopy อยู่แล้ว จึงไม่เป็นส่วนหนึ่งของชุดติดตั้ง
                    continue
                }
                $fileNameLower = $item.Name.ToLowerInvariant()
                $fileExtensionLower = $item.Extension.ToLowerInvariant()
                # Source-code filenames may legitimately describe the security
                # boundary (for example tests/release_secret_scan.py). Treat a
                # sensitive word as a credential filename only for JSON data;
                # executable/source text remains subject to the content scan.
                $isSensitiveJsonName = $fileExtensionLower -ceq ".json" -and (
                    $fileNameLower -match "(?i)(token|credential|cookie|secret)" -or
                    $fileNameLower -match "(?i)oauth.*client" -or
                    $fileNameLower -match "(?i)google.*oauth" -or
                    $fileNameLower -match "(?i)service[._-]?account" -or
                    $fileNameLower -match "(?i)^(auth|secret)s?.*\.json$"
                )
                $isSensitiveEnvironmentName = (
                    $fileNameLower -cne ".env.example" -and
                    $fileNameLower -match "(?i)^\.env(?:\..+)?$"
                )
                if (
                    $blockedNames -contains $fileNameLower -or
                    $isSensitiveJsonName -or
                    $isSensitiveEnvironmentName -or
                    $fileExtensionLower -in @(".pem", ".key", ".pfx", ".p12", ".dpapi")
                ) {
                    throw "หยุดติดตั้งเพื่อความปลอดภัย: พบไฟล์ที่อาจเป็นข้อมูลลับในชุดแจก ($($item.Name))"
                }
            }
        }
    }

    Assert-EaArtifactIntegrity
    Assert-NoEmbeddedHighConfidenceSecrets
}

function Assert-EaArtifactIntegrity {
    param([string]$CandidateRoot = $sourceRoot)

    $artifactDirectory = Join-Path $CandidateRoot "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness"
    $manifestPath = Join-Path $artifactDirectory "SHA256SUMS.txt"
    $expectedHashes = @{}
    foreach ($line in Get-Content -LiteralPath $manifestPath -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        if ($line -notmatch '^([A-Fa-f0-9]{64})\s+([^\\/]+)$') {
            throw "Manifest SHA-256 ของ EA มีรูปแบบไม่ถูกต้อง"
        }
        $expectedHashes[$Matches[2]] = $Matches[1].ToUpperInvariant()
    }

    $hashedArtifactFiles = @(
        "AUDIT_TH.md",
        "BUILD_LOG.txt",
        "COMPILE_PROOF.png",
        "MANIFEST.json",
        "MetafxHQTradeGateway.ex4",
        "MetafxHQTradeGateway.mq4",
        "README_TH.md"
    )
    if ($expectedHashes.Count -ne $hashedArtifactFiles.Count) {
        throw "Manifest SHA-256 ของ EA ต้องครอบคลุมไฟล์หลักฐาน v2.18 ครบถ้วนและไม่มีรายการแทรก"
    }
    foreach ($fileName in $hashedArtifactFiles) {
        if (-not $expectedHashes.ContainsKey($fileName)) {
            throw "Manifest SHA-256 ของ EA ไม่มีรายการ $fileName"
        }
        $artifactPath = Join-Path $artifactDirectory $fileName
        $actualHash = Get-Sha256Hex -LiteralPath $artifactPath
        if ($actualHash -cne [string]$expectedHashes[$fileName]) {
            throw "หยุดติดตั้ง: SHA-256 ของ $fileName ไม่ตรงกับ Manifest"
        }
    }

    $integrationSource = Join-Path $CandidateRoot "integrations\mt4-trade-gateway\MetafxHQTradeGateway.mq4"
    $artifactSource = Join-Path $artifactDirectory "MetafxHQTradeGateway.mq4"
    $integrationHash = Get-Sha256Hex -LiteralPath $integrationSource
    $artifactSourceHash = Get-Sha256Hex -LiteralPath $artifactSource
    if ($integrationHash -cne $artifactSourceHash) {
        throw "หยุดติดตั้ง: Source EA ใน Integration ไม่ตรงกับ Source ที่ใช้สร้าง Artifact"
    }

    $artifactManifestPath = Join-Path $artifactDirectory "MANIFEST.json"
    try {
        $artifactManifest = Get-Content -LiteralPath $artifactManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        throw "หยุดติดตั้ง: MANIFEST.json ของ EA ไม่ใช่ JSON ที่สมบูรณ์"
    }
    $binaryPath = Join-Path $artifactDirectory "MetafxHQTradeGateway.ex4"
    $proofPath = Join-Path $artifactDirectory "COMPILE_PROOF.png"
    $proofBytes = [IO.File]::ReadAllBytes($proofPath)
    $pngSignature = if ($proofBytes.Length -ge 8) {
        (($proofBytes[0..7] | ForEach-Object { $_.ToString("X2") }) -join "")
    } else {
        ""
    }
    if (
        [string]$artifactManifest.schemaVersion -cne "metafx-hq-mt4-ea-artifact-v1" -or
        [string]$artifactManifest.packageVersion -cne "2.18" -or
        [string]$artifactManifest.candidateStatus -cne "ready_visible_metaeditor_compiled" -or
        [string]$artifactManifest.sourceFile -cne "MetafxHQTradeGateway.mq4" -or
        [string]$artifactManifest.sourceSha256 -cne $integrationHash -or
        [string]$artifactManifest.binaryFile -cne "MetafxHQTradeGateway.ex4" -or
        [string]$artifactManifest.binarySha256 -cne [string]$expectedHashes["MetafxHQTradeGateway.ex4"] -or
        [long]$artifactManifest.binaryBytes -ne [long](Get-Item -LiteralPath $binaryPath).Length -or
        $artifactManifest.ex4Included -ne $true -or
        [string]$artifactManifest.compileEvidence.status -cne "passed" -or
        [string]$artifactManifest.compileEvidence.mode -cne "visible_metaeditor_front_office" -or
        [int]$artifactManifest.compileEvidence.errors -ne 0 -or
        [int]$artifactManifest.compileEvidence.warnings -ne 0 -or
        [string]$artifactManifest.compileEvidence.screenshot -cne "COMPILE_PROOF.png" -or
        [string]$artifactManifest.compileEvidence.screenshotSha256 -cne [string]$expectedHashes["COMPILE_PROOF.png"] -or
        $pngSignature -cne "89504E470D0A1A0A"
    ) {
        throw "หยุดติดตั้ง: MANIFEST/Compile proof ของ EA v2.18 ไม่ตรงกับ Source, Binary หรือผล Compile ที่อนุมัติ"
    }

    $buildLogPath = Join-Path $artifactDirectory "BUILD_LOG.txt"
    $buildLog = Get-Content -LiteralPath $buildLogPath -Raw -Encoding UTF8
    if (
        $buildLog -notmatch '(?m)^PackageVersion:\s*2\.18\s*$' -or
        $buildLog -notmatch '(?m)^CompileResult:\s*PASS\s*$' -or
        $buildLog -notmatch '(?m)^CompileErrors:\s*0\s*$' -or
        $buildLog -notmatch '(?m)^CompileWarnings:\s*0\s*$' -or
        $buildLog -notmatch ("(?m)^SourceSHA256:\s*{0}\s*$" -f [regex]::Escape($integrationHash)) -or
        $buildLog -notmatch ("(?m)^BinarySHA256:\s*{0}\s*$" -f [regex]::Escape([string]$expectedHashes["MetafxHQTradeGateway.ex4"])) -or
        $buildLog -notmatch ("(?m)^CompileProofSHA256:\s*{0}\s*$" -f [regex]::Escape([string]$expectedHashes["COMPILE_PROOF.png"]))
    ) {
        throw "หยุดติดตั้ง: หลักฐาน Compile ของ EA ไม่ตรงกับ Source/Binary/Proof ใน Artifact"
    }
    if ($buildLog -match '(?i)(?:[A-Z]:\\|/Users/|/home/)') {
        throw "หยุดติดตั้ง: BUILD_LOG ของ EA มี Absolute local path"
    }
}

function Assert-NoEmbeddedHighConfidenceSecrets {
    param([string]$CandidateRoot = $sourceRoot)

    $productionRoots = @(".github", "backend", "contracts", "docs", "frontend", "installer", "integrations", "runner", "scripts", "tests")
    $textExtensions = @(".bat", ".cmd", ".css", ".html", ".js", ".json", ".md", ".mq4", ".ps1", ".py", ".txt", ".vbs", ".yaml", ".yml")
    $secretPatterns = @(
        '(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{32,}',
        '(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{30,}',
        '(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{20,}',
        '(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])',
        '(?<![0-9])\d{8,10}:[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])',
        '-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'
    )

    foreach ($relativeRoot in $productionRoots) {
        $root = Join-Path $CandidateRoot $relativeRoot
        if (-not (Test-Path -LiteralPath $root -PathType Container)) {
            continue
        }
        foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Force) {
            if ($file.Extension.ToLowerInvariant() -notin $textExtensions) {
                continue
            }
            if ($file.FullName -match '[\\/](?:\.venv|node_modules|__pycache__|dist|build)[\\/]') {
                continue
            }
            $content = [IO.File]::ReadAllText($file.FullName)
            foreach ($pattern in $secretPatterns) {
                if ($content -match $pattern) {
                    throw "หยุดติดตั้ง: พบข้อมูลที่มีรูปแบบคล้าย Secret ในไฟล์โปรแกรม ($($file.Name))"
                }
            }
        }
    }

    $additionalTextFiles = @(
        "index.html", "Open Metafx Agent HQ.cmd", "README.md", $requirementsName,
        "1-INSTALL-HQ.bat", "UPDATE-HQ.bat", "REPAIR-HQ.bat", "UNINSTALL-HQ.bat", "2-SETUP-GOOGLE-HQ.bat",
        "STUDENT-QUICKSTART-TH.md", "AGENTS.md", "SECURITY.md", "LICENSE", "LICENSE.md",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\README_TH.md",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\AUDIT_TH.md",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\BUILD_LOG.txt",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\SHA256SUMS.txt",
        "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness\MANIFEST.json"
    )
    foreach ($relativePath in $additionalTextFiles) {
        $path = Join-Path $CandidateRoot $relativePath
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            continue
        }
        $content = [IO.File]::ReadAllText($path)
        foreach ($pattern in $secretPatterns) {
            if ($content -match $pattern) {
                throw "หยุดติดตั้ง: พบข้อมูลที่มีรูปแบบคล้าย Secret ในไฟล์ชุดแจก ($relativePath)"
            }
        }
    }
}

function Suspend-BridgeScheduledTask {
    if (
        -not (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue) -or
        -not (Get-Command Disable-ScheduledTask -ErrorAction SilentlyContinue) -or
        -not (Get-Command Stop-ScheduledTask -ErrorAction SilentlyContinue)
    ) {
        return $false
    }

    $task = Get-ScheduledTask -TaskName $bridgeTaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        return $false
    }
    $script:bridgeTaskExisted = $true

    $autostartStatePath = Join-Path $installRoot "data\runtime\bridge-autostart.json"
    if (Test-Path -LiteralPath $autostartStatePath -PathType Leaf) {
        try {
            $autostartState = Get-Content -LiteralPath $autostartStatePath -Raw -Encoding UTF8 | ConvertFrom-Json
            $savedWatchdogMinutes = [int]$autostartState.watchdog_minutes
            if ($savedWatchdogMinutes -ge 1 -and $savedWatchdogMinutes -le 30) {
                $savedStateVersion = 0
                $versionProperty = $autostartState.PSObject.Properties["version"]
                if ($versionProperty) {
                    $savedStateVersion = [int]$versionProperty.Value
                }
                if ($savedStateVersion -lt 3 -and $savedWatchdogMinutes -eq 5) {
                    $script:bridgeTaskWatchdogMinutes = 15
                }
                else {
                    $script:bridgeTaskWatchdogMinutes = $savedWatchdogMinutes
                }
            }
        }
        catch {
            throw "ข้อมูล Autostart เดิมไม่สมบูรณ์ จึงหยุดก่อนเปลี่ยน Scheduled Task"
        }
    }
    if (Test-Path -LiteralPath $bridgeEndpointPath -PathType Leaf) {
        try {
            $previousEndpoint = Get-Content -LiteralPath $bridgeEndpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ([string]$previousEndpoint.host -cne "127.0.0.1") {
                throw "host ไม่ถูกต้อง"
            }
            $previousPort = [int]$previousEndpoint.port
            if ($previousPort -lt 1024 -or $previousPort -gt 65535) {
                throw "port ไม่ถูกต้อง"
            }
            $script:bridgeTaskPreviousPort = $previousPort
        }
        catch {
            throw "Endpoint เดิมของ Autostart ไม่สมบูรณ์ จึงหยุดก่อนอัปเดต"
        }
    }

    if ([string]$task.State -ceq "Disabled") {
        return $false
    }

    $taskWasDisabled = $false
    try {
        Write-Step "กำลังพัก Watchdog ของ Bridge ระหว่างอัปเดตไฟล์"
        Disable-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop | Out-Null
        $taskWasDisabled = $true
        $task = Get-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop
        if ([string]$task.State -in @("Running", "Queued")) {
            Stop-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop
            $deadline = [DateTime]::UtcNow.AddSeconds(15)
            do {
                Start-Sleep -Milliseconds 250
                $task = Get-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop
            } while ([string]$task.State -in @("Running", "Queued") -and [DateTime]::UtcNow -lt $deadline)
            if ([string]$task.State -in @("Running", "Queued")) {
                throw "พัก Watchdog ไม่สำเร็จ จึงหยุดก่อนแก้ไฟล์โปรแกรม"
            }
        }
        return $true
    }
    catch {
        $suspendError = [string]$_.Exception.Message
        if ($taskWasDisabled -and (Get-Command Enable-ScheduledTask -ErrorAction SilentlyContinue)) {
            try {
                Enable-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop | Out-Null
            }
            catch {
                throw "พัก Watchdog ล้มเหลวและเปิด Task เดิมคืนไม่สำเร็จ: $suspendError | $($_.Exception.Message)"
            }
        }
        throw $suspendError
    }
}

function Restore-BridgeScheduledTask {
    param([Parameter(Mandatory = $true)][bool]$WasEnabled)

    if (-not $WasEnabled) {
        return
    }
    if (-not (Get-Command Enable-ScheduledTask -ErrorAction SilentlyContinue)) {
        throw "ไม่สามารถเปิด Watchdog ของ Bridge คืนหลังติดตั้งได้"
    }

    $task = Get-ScheduledTask -TaskName $bridgeTaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        throw "Scheduled Task ของ Bridge หายไประหว่างติดตั้ง"
    }
    Enable-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop | Out-Null
    Write-Step "เปิด Watchdog ของ Bridge คืนแล้ว"
}

function Set-BridgeAutostartEnabledState {
    param([Parameter(Mandatory = $true)][bool]$Enabled)

    $statePath = Join-Path $installRoot "data\runtime\bridge-autostart.json"
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "ไม่พบสถานะ Watchdog ที่เพิ่งลงทะเบียน"
    }
    try {
        $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $state.enabled = $Enabled
        $temporaryPath = "$statePath.tmp.$([Guid]::NewGuid().ToString('N'))"
        $utf8 = New-Object Text.UTF8Encoding($false)
        [IO.File]::WriteAllText(
            $temporaryPath,
            ($state | ConvertTo-Json -Depth 6) + [Environment]::NewLine,
            $utf8
        )
        Move-Item -LiteralPath $temporaryPath -Destination $statePath -Force
    }
    catch {
        throw "บันทึกสถานะเปิด/ปิด Watchdog ไม่สำเร็จ"
    }
}

function Assert-BridgeScheduledTaskReady {
    param(
        [Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$ConfirmedPort,
        [Parameter(Mandatory = $true)][bool]$ExpectedEnabled
    )

    $task = Get-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop
    $taskActions = @($task.Actions)
    $taskTriggers = @($task.Triggers)
    $systemRoot = [Environment]::GetEnvironmentVariable("SystemRoot")
    $expectedWscript = Join-Path $systemRoot "System32\wscript.exe"
    $expectedLauncher = Join-Path $installRoot "scripts\run-bridge-watchdog-hidden.vbs"
    $expectedArguments = '//B //NoLogo "{0}" /Port:{1}' -f $expectedLauncher, $ConfirmedPort
    if (
        $taskActions.Count -ne 1 -or
        -not [string]::Equals([string]$taskActions[0].Execute, $expectedWscript, [StringComparison]::OrdinalIgnoreCase) -or
        [string]$taskActions[0].Arguments -cne $expectedArguments -or
        -not [string]::Equals([string]$taskActions[0].WorkingDirectory, $installRoot, [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "Scheduled Task ไม่ได้ผูกกับ Watchdog, โฟลเดอร์ติดตั้ง และพอร์ต $ConfirmedPort แบบตรงตัว"
    }

    $hasLogonTrigger = $false
    $hasPeriodicTrigger = $false
    foreach ($trigger in $taskTriggers) {
        $className = [string]$trigger.CimClass.CimClassName
        if ($className -ceq "MSFT_TaskLogonTrigger") {
            $hasLogonTrigger = $true
        }
        elseif (
            $className -ceq "MSFT_TaskTimeTrigger" -and
            $trigger.Repetition -and
            -not [string]::IsNullOrWhiteSpace([string]$trigger.Repetition.Interval)
        ) {
            $hasPeriodicTrigger = $true
        }
    }
    if (-not $hasLogonTrigger -or -not $hasPeriodicTrigger) {
        throw "Scheduled Task ต้องมีทั้ง Trigger ตอน Login และ Trigger ตรวจ Health ซ้ำเป็นระยะ"
    }

    $isDisabled = [string]$task.State -ceq "Disabled"
    if (($ExpectedEnabled -and $isDisabled) -or (-not $ExpectedEnabled -and -not $isDisabled)) {
        throw "สถานะเปิด/ปิดของ Scheduled Task ไม่ตรงกับสถานะที่ต้องคงไว้"
    }

    $statePath = Join-Path $installRoot "data\runtime\bridge-autostart.json"
    try {
        $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (
            [int]$state.version -lt 3 -or
            [string]$state.task_name -cne $bridgeTaskName -or
            [string]$state.host -cne "127.0.0.1" -or
            [int]$state.confirmed_port -ne $ConfirmedPort -or
            [string]$state.launch_method -cne "wscript_hidden_v1" -or
            [bool]$state.enabled -ne $ExpectedEnabled
        ) {
            throw "state mismatch"
        }
    }
    catch {
        throw "สถานะ Watchdog ใน Runtime ไม่ตรงกับ Scheduled Task ที่ตรวจจริง"
    }
    return $task
}

function Rebind-BridgeScheduledTask {
    param(
        [Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$ConfirmedPort,
        [Parameter(Mandatory = $true)][bool]$EnableAfterRebind
    )

    $registerScript = Join-Path $installRoot "scripts\register-bridge-autostart.ps1"
    if (-not (Test-Path -LiteralPath $registerScript -PathType Leaf)) {
        throw "ไม่พบ Script สำหรับผูก Scheduled Task กับ Endpoint ใหม่"
    }

    $previousTaskXml = Export-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop
    try {
        Write-Step "กำลังผูก Watchdog กับพอร์ตที่ผ่าน Health check ($ConfirmedPort)"
        & powershell.exe `
            -NoLogo `
            -NoProfile `
            -NonInteractive `
            -ExecutionPolicy Bypass `
            -File $registerScript `
            -WatchdogMinutes $bridgeTaskWatchdogMinutes | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "ผูก Scheduled Task กับพอร์ต $ConfirmedPort ไม่สำเร็จ"
        }

        if (-not $EnableAfterRebind) {
            Disable-ScheduledTask -TaskName $bridgeTaskName -ErrorAction Stop | Out-Null
            Set-BridgeAutostartEnabledState -Enabled $false
            Write-Step "อัปเกรด Watchdog แบบไม่มีหน้าต่างแล้ว และคงสถานะปิดตามเดิม"
        }
        Assert-BridgeScheduledTaskReady `
            -ConfirmedPort $ConfirmedPort `
            -ExpectedEnabled $EnableAfterRebind | Out-Null
    }
    catch {
        $rebindError = [string]$_.Exception.Message
        Unregister-ScheduledTask -TaskName $bridgeTaskName -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $bridgeTaskName -Xml $previousTaskXml -Force | Out-Null
        throw "ผูก Watchdog ใหม่ไม่สำเร็จและคืน Task เดิมแล้ว: $rebindError"
    }
}

function Register-NewBridgeScheduledTask {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$ConfirmedPort)

    if ($SkipAutostart -or $SkipLaunch) {
        return
    }

    $registerScript = Join-Path $installRoot "scripts\register-bridge-autostart.ps1"
    if (-not (Test-Path -LiteralPath $registerScript -PathType Leaf)) {
        throw "ไม่พบ Script สำหรับเปิด Bridge อัตโนมัติหลังเข้า Windows"
    }
    if (Get-ScheduledTask -TaskName $bridgeTaskName -ErrorAction SilentlyContinue) {
        throw "พบ Scheduled Task ของ Bridge ที่ไม่ได้ผ่านขั้นตอนพัก Task จึงหยุดก่อนเขียนทับ"
    }

    try {
        Write-Step "กำลังเปิด Bridge อัตโนมัติหลังเข้าสู่ Windows และตั้ง Health watchdog"
        & powershell.exe `
            -NoLogo `
            -NoProfile `
            -NonInteractive `
            -ExecutionPolicy Bypass `
            -File $registerScript `
            -WatchdogMinutes $bridgeTaskWatchdogMinutes | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "สร้าง Scheduled Task สำหรับ Local Bridge ไม่สำเร็จ"
        }

        Assert-BridgeScheduledTaskReady `
            -ConfirmedPort $ConfirmedPort `
            -ExpectedEnabled $true | Out-Null
        Write-Step "Bridge จะฟื้นตัวอัตโนมัติหลัง Login และตรวจซ้ำทุก $bridgeTaskWatchdogMinutes นาที"
    }
    catch {
        $registrationError = [string]$_.Exception.Message
        Unregister-ScheduledTask -TaskName $bridgeTaskName -Confirm:$false -ErrorAction SilentlyContinue
        throw "เปิด Bridge อัตโนมัติไม่สำเร็จและลบ Task ที่สร้างไม่สมบูรณ์แล้ว: $registrationError"
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
    param(
        [Parameter(Mandatory = $true)][string]$DirectoryName,
        [string]$DestinationRoot = $installRoot
    )

    $sourceDirectory = Join-Path $sourceRoot $DirectoryName
    if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
        return
    }
    $destinationDirectory = Join-Path $DestinationRoot $DirectoryName
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null

    $arguments = @(
        $sourceDirectory, $destinationDirectory, "/MIR", "/XJ", "/R:2", "/W:1",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
        "/XF", ".env", ".env.*", "config.toml",
        "*token*.json", "*credential*.json", "*cookie*.json", "*secret*.json", "*oauth*client*.json", "*google*oauth*.json", "service-account*.json", "service_account*.json", "auth*.json",
        "*.pem", "*.key", "*.pfx", "*.p12", "*.dpapi", "*.log", "*.jsonl", "*.bak", "*.tmp",
        "/XD", ".git", ".codex", ".venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build",
        (Join-Path $sourceDirectory ".git"), (Join-Path $sourceDirectory ".codex"), (Join-Path $sourceDirectory ".venv"), (Join-Path $sourceDirectory "__pycache__"),
        (Join-Path $sourceDirectory "node_modules"), (Join-Path $sourceDirectory ".pytest_cache"), (Join-Path $sourceDirectory "dist"), (Join-Path $sourceDirectory "build"),
        (Join-Path $destinationDirectory ".git"), (Join-Path $destinationDirectory ".codex"), (Join-Path $destinationDirectory ".venv"), (Join-Path $destinationDirectory "__pycache__"),
        (Join-Path $destinationDirectory "node_modules"), (Join-Path $destinationDirectory ".pytest_cache"), (Join-Path $destinationDirectory "dist"), (Join-Path $destinationDirectory "build")
    )
    & robocopy.exe @arguments | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "คัดลอกโฟลเดอร์ $DirectoryName ไม่สำเร็จ (Robocopy รหัส $LASTEXITCODE)"
    }
}

function Copy-ApplicationFiles {
    param([string]$DestinationRoot = $installRoot)

    if (
        (Get-ComparablePath -Path $sourceRoot).Equals((Get-ComparablePath -Path $installRoot), [StringComparison]::OrdinalIgnoreCase) -and
        (Get-ComparablePath -Path $DestinationRoot).Equals((Get-ComparablePath -Path $installRoot), [StringComparison]::OrdinalIgnoreCase)
    ) {
        Write-Step "กำลังซ่อมแซมจากโฟลเดอร์ที่ติดตั้งอยู่ โดยไม่คัดลอกทับข้อมูลผู้ใช้"
        return
    }

    Write-Step "กำลังคัดลอกเฉพาะไฟล์โปรแกรมที่อนุญาต"
    New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
    foreach ($directoryName in @(".github", "backend", "contracts", "docs", "frontend", "installer", "integrations", "runner", "scripts", "tests")) {
        Sync-Directory -DirectoryName $directoryName -DestinationRoot $DestinationRoot
    }
    Sync-Directory -DirectoryName "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness" -DestinationRoot $DestinationRoot

    $rootFiles = @(
        "index.html", "Open Metafx Agent HQ.cmd", "README.md", $requirementsName,
        "1-INSTALL-HQ.bat", "UPDATE-HQ.bat", "REPAIR-HQ.bat", "UNINSTALL-HQ.bat", "2-SETUP-GOOGLE-HQ.bat",
        "AGENTS.md", ".gitattributes", ".gitignore", "LICENSE", "LICENSE.md", "SECURITY.md", "VERSION", "STUDENT-QUICKSTART-TH.md"
    )
    foreach ($fileName in $rootFiles) {
        $sourceFile = Join-Path $sourceRoot $fileName
        if (Test-Path -LiteralPath $sourceFile -PathType Leaf) {
            Copy-Item -LiteralPath $sourceFile -Destination (Join-Path $DestinationRoot $fileName) -Force
        }
    }
}

function Export-VerifiedGitSource {
    param([Parameter(Mandatory = $true)][string]$DestinationRoot)

    if ([string]::IsNullOrWhiteSpace($validatedSourceCommit)) {
        throw "ยังไม่มี Git commit ที่ตรวจยืนยันจาก GitHub สำหรับสร้าง Staging"
    }
    $gitCommand = Get-Command git.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $gitCommand) {
        throw "ไม่พบ Git for Windows สำหรับสร้าง Staging ที่ตรวจสอบได้"
    }

    $temporaryParent = Get-InstallerTemporaryParent
    $archivePath = Join-Path $temporaryParent ("mfxhq-source-{0}.zip" -f [Guid]::NewGuid().ToString("N"))
    $releasePaths = @(
        ".github", "backend", "contracts", "docs", "frontend", "installer", "integrations", "runner", "scripts", "tests",
        "artifacts/mt4-ai-council-ea-v2.18-enum-fail-closed-readiness",
        "index.html", "Open Metafx Agent HQ.cmd", "README.md", $requirementsName,
        "1-INSTALL-HQ.bat", "UPDATE-HQ.bat", "REPAIR-HQ.bat", "UNINSTALL-HQ.bat", "2-SETUP-GOOGLE-HQ.bat",
        "AGENTS.md", ".gitattributes", ".gitignore", "SECURITY.md", "VERSION", "STUDENT-QUICKSTART-TH.md"
    )
    try {
        $null = Invoke-GitSourceCapture `
            -GitPath $gitCommand.Source `
            -Arguments (@("archive", "--format=zip", "--output=$archivePath", $validatedSourceCommit, "--") + $releasePaths) `
            -FailureMessage "สร้าง Archive จาก Git Tag ที่ตรวจสอบแล้วไม่สำเร็จ"
        if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
            throw "Git ไม่ได้สร้าง Archive สำหรับ Staging"
        }
        New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::ExtractToDirectory($archivePath, $DestinationRoot)
    }
    finally {
        if (Test-Path -LiteralPath $archivePath -PathType Leaf) {
            Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Get-InstallerTemporaryParent {
    return [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd("\")
}

function Assert-InstallerTemporaryDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][ValidateSet("stage", "rollback")][string]$Kind
    )

    $resolved = [IO.Path]::GetFullPath($Path).TrimEnd("\")
    $expectedParent = Get-InstallerTemporaryParent
    $actualParent = [IO.Path]::GetDirectoryName($resolved).TrimEnd("\")
    $expectedName = if ($Kind -ceq "stage") {
        '^mfxhq-stage-[a-f0-9]{32}$'
    }
    else {
        '^mfxhq-rollback-[a-f0-9]{32}$'
    }
    if (
        -not $actualParent.Equals($expectedParent, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($resolved) -cnotmatch $expectedName
    ) {
        throw "ปฏิเสธ Temporary path ของ Installer ที่อยู่นอกพื้นที่หรือรูปแบบที่กำหนด"
    }
    return $resolved
}

function Remove-StagedApplication {
    param(
        [Parameter(Mandatory = $true)][string]$StagingRoot,
        [switch]$BestEffort
    )

    $resolved = Assert-InstallerTemporaryDirectory -Path $StagingRoot -Kind stage
    Remove-InstallerTemporaryDirectoryWithRetry `
        -ResolvedPath $resolved `
        -Kind stage `
        -BestEffort:$BestEffort
}

function Remove-InstallerTemporaryDirectoryWithRetry {
    param(
        [Parameter(Mandatory = $true)][string]$ResolvedPath,
        [Parameter(Mandatory = $true)][ValidateSet("stage", "rollback")][string]$Kind,
        [switch]$BestEffort
    )

    # Windows Defender, Search Indexer and a just-finished child process can
    # briefly retain a directory entry even after all application handles are
    # closed (ERROR_DIR_NOT_EMPTY/145 or sharing violations). Cleanup is never
    # allowed outside the exact short TEMP roots validated above, and it gets a
    # small bounded retry window instead of turning a healthy installation into
    # a false rollback.
    $resolved = Assert-InstallerTemporaryDirectory -Path $ResolvedPath -Kind $Kind
    $delaysMilliseconds = @(0, 100, 250, 500, 1000, 2000)
    $lastError = ""
    foreach ($delay in $delaysMilliseconds) {
        if ($delay -gt 0) {
            Start-Sleep -Milliseconds $delay
        }
        if (-not (Test-Path -LiteralPath $resolved)) {
            return
        }
        try {
            Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction Stop
            if (-not (Test-Path -LiteralPath $resolved)) {
                return
            }
            $lastError = "Temporary directory ยังปรากฏอยู่หลังคำสั่งลบ"
        }
        catch {
            $lastError = [string]$_.Exception.Message
        }
    }

    $message = "ลบ Temporary directory ของ Installer ไม่สำเร็จหลัง retry แบบจำกัด: $lastError"
    if ($BestEffort) {
        Write-Warning $message
        try {
            Write-InstallLog -Message $message
        }
        catch {
            # Best-effort cleanup must stay non-fatal even when antivirus or a
            # log viewer briefly locks the installer log itself.
            Write-Warning "ไม่สามารถบันทึกคำเตือน Cleanup ลง Install log ได้"
        }
        return
    }
    throw $message
}

function Stop-CandidateBridgeAfterFailedStart {
    param([ValidateRange(1024, 65535)][int]$CandidatePort)

    $lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
    if (-not (Test-Path -LiteralPath $lifecycle -PathType Leaf)) {
        throw "ไม่พบ Lifecycle สำหรับหยุด Candidate Bridge ก่อน Rollback"
    }
    try {
        & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
            -File $lifecycle -Action Stop -Port $CandidatePort | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Lifecycle คืนรหัส $LASTEXITCODE"
        }
        $listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $CandidatePort -State Listen -ErrorAction SilentlyContinue
        if ($listener) {
            throw "ยังพบ Listener ที่พอร์ต $CandidatePort"
        }
        return $true
    }
    catch {
        throw "หยุด Candidate Bridge ที่พอร์ต $CandidatePort ไม่สำเร็จ จึงไม่เขียนทับไฟล์ระหว่าง Rollback: $($_.Exception.Message)"
    }
}

function Start-PreviousDegradedBridgeAfterRollback {
    if (-not $previousBridgeRuntimeIdentity) {
        return $false
    }
    $previousPort = [int]$script:bridgeTaskPreviousPort
    if ($previousPort -lt 1024 -or $previousPort -gt 65535) {
        return $false
    }
    $existingIdentity = Get-InstalledBridgeListenerIdentity -CandidatePort $previousPort
    if ($existingIdentity) {
        return $true
    }
    if (-not (Test-LoopbackPortAvailable -CandidatePort $previousPort)) {
        Write-Warning "คืนไฟล์ Last-good แล้ว แต่พอร์ตเดิมถูก Listener อื่นครอบครอง จึงไม่หยุด Process นั้น"
        return $false
    }

    $pythonPath = [string]$previousBridgeRuntimeIdentity.PythonPath
    $serverPath = Join-Path $installRoot "backend\local-runner\bridge_server.py"
    if (
        -not (Test-Path -LiteralPath $pythonPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $serverPath -PathType Leaf)
    ) {
        Write-Warning "คืนไฟล์ Last-good แล้ว แต่ไม่พบ Python หรือ Bridge เดิมสำหรับเปิดสถานะ degraded กลับคืน"
        return $false
    }

    $logRoot = Join-Path $installRoot "data\runtime\logs"
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    $stdoutPath = Join-Path $logRoot "bridge-stdout.log"
    $stderrPath = Join-Path $logRoot "bridge-stderr.log"
    $venvLauncherName = "__PYVENV_LAUNCHER__"
    $venvLauncher = Join-Path $installRoot "runner\.venv\Scripts\python.exe"
    $originalVenvLauncher = [Environment]::GetEnvironmentVariable($venvLauncherName, "Process")
    $startedProcess = $null
    try {
        [Environment]::SetEnvironmentVariable(
            $venvLauncherName,
            $(if (Test-Path -LiteralPath $venvLauncher -PathType Leaf) { $venvLauncher } else { $null }),
            "Process"
        )
        $arguments = @(
            ('"{0}"' -f $serverPath),
            "--host", "127.0.0.1",
            "--port", ([string]$previousPort)
        )
        $startedProcess = Start-Process `
            -FilePath $pythonPath `
            -ArgumentList $arguments `
            -WorkingDirectory $installRoot `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru
    }
    finally {
        [Environment]::SetEnvironmentVariable($venvLauncherName, $originalVenvLauncher, "Process")
    }

    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        $identity = Get-InstalledBridgeListenerIdentity -CandidatePort $previousPort
        if ($identity -and [int]$identity.ProcessId -eq [int]$startedProcess.Id) {
            Write-Step "คืน Bridge Last-good ที่พอร์ต $previousPort แล้ว โดยคงสถานะ degraded เดิมไว้ให้ซ่อมต่อได้"
            return $true
        }
        if ($startedProcess.HasExited) {
            break
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)

    if (-not $startedProcess.HasExited) {
        Stop-Process -Id $startedProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Warning "คืนไฟล์ Last-good แล้ว แต่ Bridge เดิมไม่กลับมา Listen ที่พอร์ต $previousPort ภายในเวลาที่กำหนด"
    return $false
}

function Start-PreviousBridgeAfterRollback {
    if ($script:bridgeTaskPreviousPort -lt 1024 -or $script:bridgeTaskPreviousPort -gt 65535) {
        return $false
    }
    if (-not $previousBridgeWasHealthy) {
        return (Start-PreviousDegradedBridgeAfterRollback)
    }
    $lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
    if (-not (Test-Path -LiteralPath $lifecycle -PathType Leaf)) {
        return $false
    }
    try {
        $exitCode = Invoke-BridgeLifecycleProcess `
            -Action Start `
            -ConfirmedPort $script:bridgeTaskPreviousPort
        if ($exitCode -ne 0) {
            Write-Warning "คืนไฟล์ Last-good แล้ว แต่เปิด Bridge เดิมที่พอร์ต $($script:bridgeTaskPreviousPort) ไม่สำเร็จ"
            return $false
        }
        return $true
    }
    catch {
        Write-Warning "คืนไฟล์ Last-good แล้ว แต่เปิด Bridge เดิมไม่สำเร็จ: $($_.Exception.Message)"
        return $false
    }
}

function New-StagedApplication {
    # Staging beside a long LOCALAPPDATA path can push valid, deeply nested
    # assets beyond legacy Win32 MAX_PATH. Use the short system temp root and
    # validate every staged and projected installed file before mutation.
    $stagingParent = Get-InstallerTemporaryParent
    New-Item -ItemType Directory -Path $stagingParent -Force | Out-Null
    $stagingRoot = Join-Path $stagingParent ("mfxhq-stage-{0}" -f [Guid]::NewGuid().ToString("N"))
    try {
        if ($validatedSourceCommit) {
            Write-Step "กำลังสร้าง Staging จากไฟล์ที่ติดตามใน Git Tag ซึ่งยืนยันกับ GitHub แล้ว"
            Export-VerifiedGitSource -DestinationRoot $stagingRoot
        }
        else {
            Copy-ApplicationFiles -DestinationRoot $stagingRoot
        }
        foreach ($file in Get-ChildItem -LiteralPath $stagingRoot -Recurse -File -Force) {
            if ($file.FullName.Length -ge 260) {
                throw "Staged path ยาวเกินขอบเขต Win32 ที่รองรับ ($($file.Name))"
            }
            $relativePath = $file.FullName.Substring($stagingRoot.Length).TrimStart("\")
            $installedPath = Join-Path $installRoot $relativePath
            if ($installedPath.Length -ge 260) {
                throw "ตำแหน่งติดตั้งทำให้ Path ของไฟล์ยาวเกินขอบเขต Win32 กรุณาใช้ Windows user path ที่สั้นลง"
            }
        }
        Assert-EaArtifactIntegrity -CandidateRoot $stagingRoot
        Assert-NoEmbeddedHighConfidenceSecrets -CandidateRoot $stagingRoot
        # The staged copy deliberately excludes runner/.venv and all user
        # state. Run only the dependency-free candidate preflight here. The
        # installed-runtime deployment checks run again after the pinned venv
        # is installed; the complete regression matrix is gated in GitHub
        # Actions, where it cannot collide with a student's real machine state.
        $resolved = Resolve-SystemPython
        $candidatePython = [string]$resolved.FilePath
        $candidatePrefix = @($resolved.PrefixArguments)
        Push-Location $stagingRoot
        try {
            $arguments = @($candidatePrefix) + @(
                "-m", "unittest", "-v", "tests.test_release_candidate_preflight"
            )
            Invoke-CheckedNative -FilePath $candidatePython -Arguments $arguments -FailureMessage "การตรวจ Release candidate ก่อนติดตั้งไม่ผ่าน"
        }
        finally {
            Pop-Location
        }
        return $stagingRoot
    }
    catch {
        # Preserve the real candidate validation error. A transient Windows
        # TEMP cleanup race must not replace it with an unrelated exception.
        Remove-StagedApplication -StagingRoot $stagingRoot -BestEffort
        throw
    }
}

function Publish-StagedApplication {
    param([Parameter(Mandatory = $true)][string]$StagingRoot)

    foreach ($directoryName in @(".github", "backend", "contracts", "docs", "frontend", "installer", "integrations", "runner", "scripts", "tests")) {
        $sourceDirectory = Join-Path $StagingRoot $directoryName
        if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
            continue
        }
        $destinationDirectory = Join-Path $installRoot $directoryName
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        & robocopy.exe $sourceDirectory $destinationDirectory /MIR /XJ /R:2 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -gt 7) {
            throw "Publish staged directory $directoryName ไม่สำเร็จ (Robocopy รหัส $LASTEXITCODE)"
        }
    }
    $artifactDirectory = "artifacts\mt4-ai-council-ea-v2.18-enum-fail-closed-readiness"
    $artifactSource = Join-Path $StagingRoot $artifactDirectory
    $artifactDestination = Join-Path $installRoot $artifactDirectory
    New-Item -ItemType Directory -Path $artifactDestination -Force | Out-Null
    & robocopy.exe $artifactSource $artifactDestination /MIR /XJ /R:2 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "Publish staged EA artifact ไม่สำเร็จ (Robocopy รหัส $LASTEXITCODE)"
    }
    foreach ($file in Get-ChildItem -LiteralPath $StagingRoot -File) {
        Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $installRoot $file.Name) -Force
    }
}

function New-ApplicationRollbackSnapshot {
    $rollbackParent = Get-InstallerTemporaryParent
    New-Item -ItemType Directory -Path $rollbackParent -Force | Out-Null
    $snapshotRoot = Join-Path $rollbackParent ("mfxhq-rollback-{0}" -f [Guid]::NewGuid().ToString("N"))
    $installExisted = Test-Path -LiteralPath $installRoot -PathType Container
    New-Item -ItemType Directory -Path $snapshotRoot -Force | Out-Null

    if ($installExisted) {
        Write-Step "กำลังเก็บ Last-good application ก่อนอัปเดต"
        $arguments = @(
            $installRoot, $snapshotRoot, "/MIR", "/XJ", "/R:2", "/W:1",
            "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
            "/XD", "data", "workspace", ".git", ".codex", "node_modules", "__pycache__", ".pytest_cache",
            (Join-Path $installRoot "data"), (Join-Path $installRoot "workspace"),
            (Join-Path $installRoot ".git"), (Join-Path $installRoot ".codex")
        )
        & robocopy.exe @arguments | Out-Null
        if ($LASTEXITCODE -gt 7) {
            Remove-Item -LiteralPath $snapshotRoot -Recurse -Force -ErrorAction SilentlyContinue
            throw "เก็บ Last-good application ไม่สำเร็จ (Robocopy รหัส $LASTEXITCODE)"
        }
    }

    return [pscustomobject]@{
        SnapshotRoot = $snapshotRoot
        InstallExisted = [bool]$installExisted
    }
}

function Restore-ApplicationRollbackSnapshot {
    param([Parameter(Mandatory = $true)]$RollbackState)

    $snapshotRoot = Assert-InstallerTemporaryDirectory -Path ([string]$RollbackState.SnapshotRoot) -Kind rollback

    Write-Step "การติดตั้งไม่สำเร็จ กำลังคืน Last-good application"
    if ([bool]$RollbackState.InstallExisted) {
        New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
        $arguments = @(
            $snapshotRoot, $installRoot, "/MIR", "/XJ", "/R:3", "/W:1",
            "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
            "/XD", "data", "workspace", ".git", ".codex",
            (Join-Path $installRoot "data"), (Join-Path $installRoot "workspace"),
            (Join-Path $installRoot ".git"), (Join-Path $installRoot ".codex")
        )
        & robocopy.exe @arguments | Out-Null
        if ($LASTEXITCODE -gt 7) {
            throw "คืน Last-good application ไม่สำเร็จ (Robocopy รหัส $LASTEXITCODE)"
        }
    }
    elseif (Test-Path -LiteralPath $installRoot) {
        $resolvedInstall = [IO.Path]::GetFullPath($installRoot).TrimEnd("\")
        $expectedInstall = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Metafxclub\AI-Agent-HQ")).TrimEnd("\")
        if (-not $resolvedInstall.Equals($expectedInstall, [StringComparison]::OrdinalIgnoreCase)) {
            throw "ปฏิเสธการลบ Installation ที่ไม่สมบูรณ์เพราะ Path ไม่ตรงกับพื้นที่ที่กำหนด"
        }
        Remove-Item -LiteralPath $installRoot -Recurse -Force
    }
}

function Remove-ApplicationRollbackSnapshot {
    param(
        [Parameter(Mandatory = $true)]$RollbackState,
        [switch]$BestEffort
    )

    $snapshotRoot = Assert-InstallerTemporaryDirectory -Path ([string]$RollbackState.SnapshotRoot) -Kind rollback
    Remove-InstallerTemporaryDirectoryWithRetry `
        -ResolvedPath $snapshotRoot `
        -Kind rollback `
        -BestEffort:$BestEffort
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
        Write-Step ("พบ Python {0} ({1}) ที่ {2} และกำลังสร้าง Virtual Environment แยกสำหรับ HQ" -f $python.Version, $python.Architecture, $python.Executable)
        $arguments = @($python.PrefixArguments) + @("-m", "venv", $venvRoot)
        Invoke-CheckedNative -FilePath $python.FilePath -Arguments $arguments -FailureMessage "สร้าง Virtual Environment ไม่สำเร็จ"
    }
    else {
        Write-Step ("กำลังตรวจและใช้ Virtual Environment เดิม (Python {0})" -f $venvDetails.Version)
    }

    Write-Step "กำลังติดตั้ง Dependency ที่ล็อกเวอร์ชันไว้"
    Invoke-CheckedNative -FilePath $venvPython -Arguments @("-m", "pip", "install", "--disable-pip-version-check", "--require-hashes", "--upgrade", "--requirement", $requirements) -FailureMessage "ติดตั้ง Dependency ไม่สำเร็จ กรุณาตรวจอินเทอร์เน็ตแล้วลองใหม่"
    Invoke-CheckedNative -FilePath $venvPython -Arguments @("-m", "pip", "check") -FailureMessage "Dependency ตรวจสอบไม่ผ่าน"

    $codexBinary = Join-Path $venvRoot "Lib\site-packages\codex_cli_bin\bin\codex.exe"
    if (-not (Test-Path -LiteralPath $codexBinary -PathType Leaf)) {
        throw "ติดตั้ง Dependency แล้วแต่ไม่พบ Codex CLI ภายใน Virtual Environment"
    }
    return $venvPython
}

function Test-InstalledApplication {
    param([Parameter(Mandatory = $true)][string]$PythonPath)

    Write-Step "กำลังรันชุดตรวจติดตั้งแบบคงที่สำหรับเครื่องผู้ใช้"
    Push-Location $installRoot
    try {
        # The complete developer regression suite is release-gated in GitHub
        # Actions on Python 3.10-3.14. Running all of those stateful/concurrent
        # tests against a student's real TEMP, Google state and antivirus made
        # otherwise valid installs fail nondeterministically. Keep an actual
        # deployment gate here: verify the exact release tree again with the
        # installed venv, import every Bridge dependency through --help, import
        # the guarded Codex runner, then let Start-And-TestBridge prove the real
        # HTTP runtime and /api/health immediately afterwards.
        Invoke-CheckedNative `
            -FilePath $PythonPath `
            -Arguments @("-m", "unittest", "-v", "tests.test_release_candidate_preflight") `
            -FailureMessage "ชุดตรวจ Release ที่ติดตั้งแล้วไม่ผ่าน"
        Invoke-CheckedNative `
            -FilePath $PythonPath `
            -Arguments @("backend\local-runner\bridge_server.py", "--help") `
            -FailureMessage "โหลด Dependency ของ Local Bridge ไม่สำเร็จ"
        Invoke-CheckedNative `
            -FilePath $PythonPath `
            -Arguments @("runner\codex_cli_runner.py", "--help") `
            -FailureMessage "โหลด Codex Runner ไม่สำเร็จ"
    }
    finally {
        Pop-Location
    }
}

function Test-GoogleOAuthDeploymentConfigured {
    param([Parameter(Mandatory = $true)][string]$CandidateRoot)

    $configureCli = Join-Path $CandidateRoot "backend\local-runner\configure_google_oauth_client.py"
    if (-not (Test-Path -LiteralPath $configureCli -PathType Leaf)) {
        return $false
    }
    try {
        $python = Resolve-SystemPython
        $arguments = @($python.PrefixArguments) + @($configureCli, "--status")
        $output = @(& $python.FilePath @arguments 2>$null)
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        $jsonLine = @($output | ForEach-Object { [string]$_ } | Where-Object { $_.TrimStart().StartsWith("{") }) | Select-Object -Last 1
        if (-not $jsonLine) {
            return $false
        }
        $status = $jsonLine | ConvertFrom-Json
        return $status.ok -eq $true -and $status.configured -eq $true
    }
    catch {
        return $false
    }
}

function Invoke-GoogleOAuthFirstRunSetup {
    param([Parameter(Mandatory = $true)][string]$CandidateRoot)

    $alreadyConfigured = Test-GoogleOAuthDeploymentConfigured -CandidateRoot $CandidateRoot
    $explicitClientSetup = -not [string]::IsNullOrWhiteSpace($GoogleClientJsonPath)
    # Preserve the original optional gate semantics ($SkipGoogleSetup -or $SkipLaunch)
    # unless an explicit, fully validated one-shot JSON setup was requested.
    if (($SkipGoogleSetup -and -not $explicitClientSetup) -or $SkipLaunch -or ($alreadyConfigured -and -not $explicitClientSetup)) {
        if ($alreadyConfigured) {
            Write-Host "Google OAuth Client ของ Windows User นี้ตั้งค่าไว้แล้ว" -ForegroundColor Green
        }
        return
    }

    $setupScript = Join-Path $CandidateRoot "scripts\setup-google-oauth.ps1"
    if (-not (Test-Path -LiteralPath $setupScript -PathType Leaf)) {
        Write-Warning "ไม่พบ Google first-run wizard ในชุดติดตั้ง ระบบหลักจะติดตั้งต่อโดยยังไม่เปิด Google Sheet"
        return
    }
    if (-not $explicitClientSetup) {
        Write-Host ""
        Write-Host "ตั้งค่า Google Sheets แบบ Private ครั้งเดียว (ไม่บังคับ)" -ForegroundColor Cyan
        Write-Host "ใช้ OAuth Client JSON ประเภท Desktop app ของผู้เรียนเอง ระบบจะตรวจไฟล์และเก็บด้วย Windows DPAPI" -ForegroundColor DarkGray
        $answer = Read-Host "ต้องการเลือก OAuth Client JSON ตอนนี้หรือไม่? [Y/N]"
        if ($answer -notmatch '^(?i)y(?:es)?$') {
            Write-Host "ข้ามขั้นตอน Google ตอนนี้ เปิด 2-SETUP-GOOGLE-HQ.bat ภายหลังได้" -ForegroundColor Yellow
            return
        }
    }

    # Interactive and explicit paths both use -SkipBridgeEnsure -SkipOpen;
    # the already-verified Bridge stays online while only the DPAPI client is updated.
    $setupArguments = @(
        "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", $setupScript,
        "-SkipBridgeEnsure", "-SkipOpen"
    )
    if ($explicitClientSetup) {
        $setupArguments += @(
            "-ClientJsonPath", $GoogleClientJsonPath,
            "-ExpectedClientId", $ExpectedGoogleClientId
        )
    }
    & powershell.exe @setupArguments
    if ($LASTEXITCODE -ne 0) {
        if ($explicitClientSetup) {
            throw "ติดตั้ง HQ สำเร็จ แต่การตั้งค่า Google OAuth ที่ระบุไม่ผ่าน กรุณาตรวจ Path และ Client ID แล้วรันติดตั้งซ้ำ"
        }
        Write-Warning "ยังตั้งค่า Google ไม่สำเร็จ ระบบหลักจะติดตั้งต่อ และสามารถเปิด 2-SETUP-GOOGLE-HQ.bat เพื่อลองใหม่"
    }
}

function Invoke-BridgeLifecycleProcess {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("Start", "Stop")][string]$Action,
        [Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$ConfirmedPort
    )

    $lifecycle = Join-Path $installRoot "scripts\start-local-bridge.ps1"
    $arguments = @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ('"{0}"' -f $lifecycle),
        "-Action",
        $Action,
        "-Port",
        [string]$ConfirmedPort
    )
    if ($Action -ceq "Start") {
        $arguments += @("-HealthTimeoutSeconds", "45")
    }

    # A native PowerShell pipeline can retain a descendant's inherited pipe
    # handle and make the installer wait until the long-running Bridge exits.
    # Launch the bounded lifecycle command without a pipeline and wait only for
    # that command process; the Bridge itself owns redirected runtime logs.
    $process = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList $arguments `
        -WindowStyle Hidden `
        -PassThru
    # Start-Process -Wait follows the whole descendant tree on Windows and
    # would therefore wait for the intentionally long-running Bridge. The
    # .NET Process wait below is bounded to the exact lifecycle command PID.
    if (-not $process.WaitForExit(60000)) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        throw "คำสั่งจัดการ Local Bridge ไม่จบภายใน 60 วินาที"
    }
    return [int]$process.ExitCode
}

function Test-IsolatedInstalledBridge {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$ConfirmedPort)

    Write-Step "กำลังเปิดและปิด Local Bridge ภายในพื้นที่ Package Smoke เพื่อตรวจ Runtime จริง"
    $primaryError = $null
    try {
        $endpoint = Start-And-TestBridge -ConfirmedPort $ConfirmedPort
        $frontend = Invoke-WebRequest -Uri $endpoint.Url -Method Get -UseBasicParsing -TimeoutSec 10
        if ([int]$frontend.StatusCode -ne 200 -or [int]$frontend.RawContentLength -le 0) {
            throw "Frontend จากแพ็กเกจติดตั้งจริงไม่ตอบกลับอย่างสมบูรณ์"
        }
    }
    catch {
        $primaryError = $_.Exception
        throw
    }
    finally {
        $stopExitCode = Invoke-BridgeLifecycleProcess -Action Stop -ConfirmedPort $ConfirmedPort
        if ($stopExitCode -ne 0) {
            if ($primaryError) {
                Write-Warning "Package Smoke พบข้อผิดพลาดหลักและหยุด Bridge ทดสอบไม่สำเร็จ กรุณาตรวจ process ใน RUNNER_TEMP"
            }
            else {
                throw "Package Smoke เปิด Runtime ได้ แต่หยุด Bridge ทดสอบไม่สำเร็จ"
            }
        }
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

    if (-not (Test-LoopbackPortAvailable -CandidatePort $ConfirmedPort)) {
        throw "พอร์ตที่ยืนยัน ($ConfirmedPort) ถูกใช้งานก่อนเริ่ม Bridge ระบบหยุดโดยไม่เปลี่ยน URL อัตโนมัติ"
    }

    Write-Step "กำลังเปิด Local Bridge ที่ URL ซึ่งผู้ใช้ยืนยันและตรวจสุขภาพระบบ"
    $lifecycleExitCode = Invoke-BridgeLifecycleProcess -Action Start -ConfirmedPort $ConfirmedPort
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
    $installedVersion = (Get-Content -LiteralPath (Join-Path $installRoot "VERSION") -Raw -Encoding UTF8).Trim()
    $healthIdentityMatches = (
        $healthProperties -contains "server" -and
        $healthProperties -contains "version" -and
        [string]$health.server -ceq "Metafx Local Bridge" -and
        [string]$health.version -ceq $installedVersion
    )
    if (
        -not $healthOk -or
        -not $healthReady -or
        -not $healthEndpointMatches -or
        -not $healthIdentityMatches
    ) {
        throw "Local Bridge ตอบกลับแต่ชื่อระบบ Version หรือ endpoint จาก Health check ไม่ตรงกับ Runtime ที่ติดตั้ง"
    }
    $frontend = Invoke-WebRequest -Uri $endpoint.Url -Method Get -UseBasicParsing -TimeoutSec 10
    if (
        [int]$frontend.StatusCode -ne 200 -or
        [int]$frontend.RawContentLength -le 0 -or
        [string]$frontend.Content -notmatch '<title>Metafxclub AI Agent HQ' -or
        [string]$frontend.Content -notmatch 'frontend/index\.html'
    ) {
        throw "Local Bridge ผ่าน Health แต่หน้า Agent HQ ที่ $($endpoint.Url) ยังเปิดใช้งานไม่ได้"
    }
    $frontendAppUrl = "{0}frontend/index.html" -f $endpoint.Url
    $frontendApp = Invoke-WebRequest -Uri $frontendAppUrl -Method Get -UseBasicParsing -TimeoutSec 10
    if (
        [int]$frontendApp.StatusCode -ne 200 -or
        [int]$frontendApp.RawContentLength -le 0 -or
        [string]$frontendApp.Content -notmatch '<title>Metafxclub AI Pixel HQ' -or
        [string]$frontendApp.Content -notmatch 'frontend/src/app/main\.js'
    ) {
        throw "หน้าเปิดระบบตอบกลับ แต่หน้า Visual Office ที่ $frontendAppUrl ยังโหลดโครงสร้างหลักไม่ได้"
    }
    $mainJsUrl = "{0}frontend/src/app/main.js" -f $endpoint.Url
    $mainJs = Invoke-WebRequest -Uri $mainJsUrl -Method Get -UseBasicParsing -TimeoutSec 10
    if (
        [int]$mainJs.StatusCode -ne 200 -or
        [int]$mainJs.RawContentLength -le 0 -or
        [string]$mainJs.Content -notmatch 'window\.MetafxHqBoot' -or
        [string]$mainJs.Content -notmatch 'init\(\)\.catch'
    ) {
        throw "หน้า Agent HQ ตอบกลับ แต่ไฟล์เริ่มระบบ main.js ยังโหลดหรือยืนยันโครงสร้างไม่ได้"
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
        [Parameter(Mandatory = $true)]$Readiness,
        [Parameter(Mandatory = $true)][string]$WatchdogStatus,
        [Parameter(Mandatory = $true)][ValidateRange(0, 4)][int]$PostInstallExitCode
    )

    $versionPath = Join-Path $installRoot "VERSION"
    $version = if (Test-Path -LiteralPath $versionPath -PathType Leaf) {
        (Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8).Trim()
    }
    else {
        "unknown"
    }
    $result = [ordered]@{
        version = 2
        installed_at = [DateTime]::UtcNow.ToString("o")
        application_version = $version
        install_root = "%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ"
        install_scope = "current_windows_user"
        source = [ordered]@{
            provenance = $(if ($PrePublishVerification) {
                "verified_official_commit_pre_release"
            } elseif ($validatedSourceCommit) {
                "verified_remote_git_tag"
            } else {
                "unverified_archive_or_local_source"
            })
            repository = $(if ($validatedSourceCommit) { "https://github.com/metafxclub/metafxclub-ai-agent-hq.git" } else { $null })
            tag = $(if ($validatedSourceCommit) { $ExpectedGitTag.Trim() } else { $null })
            commit = $(if ($validatedSourceCommit) { $validatedSourceCommit } else { $null })
        }
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
        post_install = [ordered]@{
            complete = $PostInstallExitCode -eq 0
            exit_code = $PostInstallExitCode
            watchdog = [ordered]@{
                status = $WatchdogStatus
                task_name = $bridgeTaskName
                port = [int]$Endpoint.Port
                repair_command = $(if ($WatchdogStatus -ceq "repair_required") {
                    'powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\installer\install.ps1" -RepairOnly -Port {0} -EndpointConfirmed -SkipGoogleSetup -SkipShortcuts' -f [int]$Endpoint.Port
                } else {
                    $null
                })
            }
            google_oauth_client = [ordered]@{
                status = $(if ($googleSetupFailure) { "repair_required" } else { "complete_or_not_requested" })
            }
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
    if ($PackageSmoke) {
        if ($PackageUpgradeSmoke) {
            if ($SkipLaunch -or -not ($SkipShortcuts -and $SkipAutostart -and $SkipGoogleSetup)) {
                throw "PackageUpgradeSmoke ต้องเปิด Bridge แต่ต้องข้าม Shortcut, Autostart และ Google setup"
            }
        }
        elseif (-not ($SkipLaunch -and $SkipShortcuts)) {
            throw "PackageSmoke ต้องใช้ร่วมกับ SkipLaunch และ SkipShortcuts เท่านั้น"
        }
        $runnerTemp = [string]$env:RUNNER_TEMP
        $localAppDataFull = [IO.Path]::GetFullPath([string]$env:LOCALAPPDATA).TrimEnd("\")
        $runnerTempFull = if ($runnerTemp) { [IO.Path]::GetFullPath($runnerTemp).TrimEnd("\") } else { "" }
        if (
            [string]$env:GITHUB_ACTIONS -cne "true" -or
            -not $runnerTempFull -or
            -not $localAppDataFull.StartsWith($runnerTempFull + "\", [StringComparison]::OrdinalIgnoreCase)
        ) {
            throw "PackageSmoke ใช้ได้เฉพาะ GitHub Actions ที่แยก LOCALAPPDATA ไว้ใต้ RUNNER_TEMP"
        }
    }
    Write-InstallLog -Message ("เริ่ม {0} หลังผู้ใช้ยืนยัน http://127.0.0.1:{1}/" -f `
        $(if ($RepairOnly) { "ซ่อมแซม" } else { "ติดตั้ง" }), $selectedBridgePort)
    $bridgeEndpoint = $null
    $codexReadiness = $null
    $stagingRoot = $null
    $previousBridgeWasRunning = $false
    $previousBridgeEndpointState = $null
    $previousBridgeRestored = $false
    if (-not $RepairOnly) {
        # Validate the complete candidate while the current installation and
        # Bridge are still untouched. A bad source tree must not cause downtime.
        $stagingRoot = New-StagedApplication
    }
    elseif (-not (Get-ComparablePath -Path $sourceRoot).Equals((Get-ComparablePath -Path $installRoot), [StringComparison]::OrdinalIgnoreCase)) {
        throw "การซ่อมแซมต้องเรียกจากชุด Installer ที่อยู่ในโฟลเดอร์ติดตั้ง"
    }
    if ($PackageSmoke -and -not $PackageUpgradeSmoke) {
        # CI/package validation owns an isolated LOCALAPPDATA tree and must not
        # inspect, stop, or reconfigure a real user Bridge or Scheduled Task.
        Publish-StagedApplication -StagingRoot $stagingRoot
        Remove-StagedApplication -StagingRoot $stagingRoot -BestEffort
        $stagingRoot = $null
        Initialize-UserDataDirectories
        $venvPython = Initialize-PythonEnvironment
        Test-InstalledApplication -PythonPath $venvPython
        Test-IsolatedInstalledBridge -ConfirmedPort $selectedBridgePort
        Write-Step "Package Smoke ผ่านทั้งชุดทดสอบและ Runtime จริง โดยไม่แตะ Bridge, Watchdog, Shortcut หรือ Browser ของผู้ใช้"
        exit 0
    }
    $previousBridgeEndpointState = Get-SavedBridgeEndpointState
    if ($previousBridgeEndpointState) {
        $script:bridgeTaskPreviousPort = [int]$previousBridgeEndpointState.Port
        $previousBridgeWasRunning = $true
        $previousBridgeWasHealthy = [bool]$previousBridgeEndpointState.Healthy
        $previousBridgeRuntimeIdentity = $previousBridgeEndpointState.RuntimeIdentity
    }
    $bridgeTaskWasEnabled = $false
    try {
        $bridgeTaskWasEnabled = Suspend-BridgeScheduledTask
        if (
            $SkipLaunch -and
            $bridgeTaskWasEnabled -and
            ($bridgeTaskPreviousPort -lt 1024 -or $bridgeTaskPreviousPort -ne $selectedBridgePort)
        ) {
            throw "เมื่อเปิด Autostart อยู่ การติดตั้งแบบ SkipLaunch ต้องใช้พอร์ตเดิม เพราะพอร์ตใหม่ยังไม่ผ่าน Health check"
        }
        $script:previousBridgeWasStopped = $previousBridgeWasRunning
        Stop-ExistingBridge
        if (-not (Test-LoopbackPortAvailable -CandidatePort $selectedBridgePort)) {
            throw "พอร์ตที่ผู้ใช้ยืนยัน ($selectedBridgePort) ไม่ว่างหลังหยุด HQ เดิม ระบบหยุดโดยไม่เปลี่ยน URL"
        }
        if (-not $RepairOnly) {
            # The candidate already passed its tests before the Bridge was
            # stopped. The rollback snapshot covers the short publish,
            # dependency, installed-test, and health window that follows.
            $script:applicationRollbackState = New-ApplicationRollbackSnapshot
            $script:applicationMutationStarted = $true
            Publish-StagedApplication -StagingRoot $stagingRoot
            Remove-StagedApplication -StagingRoot $stagingRoot -BestEffort
            $stagingRoot = $null
            if ($PackageSmokeFailAfterPublish) {
                throw "PackageUpgradeSmoke forced a post-publish failure to verify Last-good rollback"
            }
        }
        elseif (-not $script:applicationRollbackState) {
            $script:applicationRollbackState = New-ApplicationRollbackSnapshot
            $script:applicationMutationStarted = $true
        }

        Initialize-UserDataDirectories
        $venvPython = Initialize-PythonEnvironment
        Test-InstalledApplication -PythonPath $venvPython
        if (-not $SkipLaunch) {
            # The lifecycle command may start a process and then fail a later
            # endpoint/health assertion. Mark it before the call so rollback
            # always attempts to stop that candidate safely.
            $script:candidateBridgeMayBeRunning = $true
            $bridgeEndpoint = Start-And-TestBridge -ConfirmedPort $selectedBridgePort
            $codexReadiness = Get-SafeCodexReadiness -Endpoint $bridgeEndpoint
            Show-CodexReadiness -Readiness $codexReadiness
        }
        if ($script:applicationRollbackState) {
            # Application tests and live Health have already passed. Failure to
            # remove a TEMP snapshot must be logged, not roll back a healthy HQ.
            Remove-ApplicationRollbackSnapshot -RollbackState $script:applicationRollbackState -BestEffort
            $script:applicationRollbackState = $null
            $script:applicationMutationStarted = $false
        }
        # Watchdog and Google setup are non-transactional onboarding. Run them
        # only after the installed Runtime passed its full tests and Health
        # check and the rollback snapshot was released. Their failure must not
        # turn a healthy, installed HQ into a false rollback report.
        if (-not $SkipLaunch) {
            try {
                if ($bridgeTaskExisted) {
                    # -SkipAutostart is the only explicit request to keep the
                    # replacement disabled. A normal classroom install must
                    # finish with a working Login/periodic Watchdog even when a
                    # legacy task happened to be disabled.
                    $enableReboundTask = -not $SkipAutostart
                    Rebind-BridgeScheduledTask `
                        -ConfirmedPort $selectedBridgePort `
                        -EnableAfterRebind $enableReboundTask
                    $watchdogStatus = $(if ($enableReboundTask) { "ready" } else { "skipped_by_request" })
                    # The registration script enabled and verified the replacement
                    # task already, so the finally block must not restore the old one.
                    $bridgeTaskWasEnabled = $false
                }
                elseif (-not $SkipAutostart) {
                    Register-NewBridgeScheduledTask -ConfirmedPort $selectedBridgePort
                    $watchdogStatus = "ready"
                }
                else {
                    $watchdogStatus = "skipped_by_request"
                }
            }
            catch {
                $watchdogStatus = "repair_required"
                $watchdogFailure = $true
                $watchdogMessage = "Agent HQ และ Health พร้อมแล้ว แต่ Watchdog หลัง Login ยังไม่ผ่านการตรวจจริง กรุณารันคำสั่ง Repair Watchdog ที่แสดงด้านล่าง"
                [void]$postInstallFailures.Add($watchdogMessage)
                Write-Warning "${watchdogMessage}: $($_.Exception.Message)"
            }
        }
        else {
            $watchdogStatus = "skipped_no_launch"
        }
        try {
            Invoke-GoogleOAuthFirstRunSetup -CandidateRoot $installRoot
        }
        catch {
            if (-not [string]::IsNullOrWhiteSpace($GoogleClientJsonPath)) {
                $googleSetupFailure = $true
                $googleMessage = "Agent HQ ติดตั้งและเปิดใช้งานแล้ว แต่ยังนำเข้า Google OAuth Client ไม่สำเร็จ กรุณาตรวจ JSON/Client ID แล้วเปิด 2-SETUP-GOOGLE-HQ.bat"
                [void]$postInstallFailures.Add($googleMessage)
                Write-Warning $googleMessage
            }
            else {
                Write-Warning "ติดตั้ง Agent HQ สำเร็จ แต่ยังตั้งค่า Google ไม่ได้ ให้เปิด 2-SETUP-GOOGLE-HQ.bat ภายหลัง: $($_.Exception.Message)"
            }
        }
        if (-not $SkipShortcuts) {
            try {
                Install-Shortcuts
            }
            catch {
                Write-Warning "ติดตั้งและตรวจระบบสำเร็จ แต่สร้าง Shortcut ไม่สำเร็จ: $($_.Exception.Message)"
            }
        }
        if ($bridgeEndpoint -and -not $PackageSmoke) {
            try {
                Start-Process $bridgeEndpoint.Url
            }
            catch {
                Write-Warning "ระบบพร้อมใช้งานแล้ว แต่เปิด Browser อัตโนมัติไม่สำเร็จ กรุณาเปิด $($bridgeEndpoint.Url) เอง"
            }
        }
    }
    catch {
        $installError = [string]$_.Exception.Message
        if ($stagingRoot) {
            Remove-StagedApplication -StagingRoot $stagingRoot -BestEffort
            $stagingRoot = $null
        }
        if ($script:applicationMutationStarted -and $script:applicationRollbackState) {
            $rollbackRestored = $false
            try {
                if ($script:candidateBridgeMayBeRunning) {
                    # A new candidate Bridge may already be healthy. Stop only
                    # that exact process before restoring its application files.
                    Stop-CandidateBridgeAfterFailedStart -CandidatePort $selectedBridgePort
                    $bridgeEndpoint = $null
                    $script:candidateBridgeMayBeRunning = $false
                }
                Restore-ApplicationRollbackSnapshot -RollbackState $script:applicationRollbackState
                $rollbackRestored = $true
            }
            catch {
                $rollbackError = [string]$_.Exception.Message
                $recoveryPath = [string]$script:applicationRollbackState.SnapshotRoot
                $script:rollbackIncomplete = $true
                throw "การติดตั้งล้มเหลวและ Rollback ไม่สมบูรณ์: $installError | $rollbackError | เก็บ Last-good ไว้ที่ $recoveryPath"
            }
            finally {
                if ($rollbackRestored) {
                    Remove-ApplicationRollbackSnapshot -RollbackState $script:applicationRollbackState -BestEffort
                    $script:applicationRollbackState = $null
                    $script:applicationMutationStarted = $false
                }
            }
            if ($rollbackRestored -and $previousBridgeWasRunning) {
                $previousBridgeRestored = [bool](Start-PreviousBridgeAfterRollback)
            }
        }
        elseif ($script:previousBridgeWasStopped -and $previousBridgeWasRunning) {
            # Port races and snapshot/pre-publish failures occur before any
            # application mutation, but the verified old Bridge was already
            # stopped. Restore its service independently of file rollback.
            $previousBridgeRestored = [bool](Start-PreviousBridgeAfterRollback)
        }
        throw $installError
    }
    finally {
        if ($script:rollbackIncomplete) {
            Write-Warning "คง Watchdog ไว้ในสถานะปิด เพราะ Rollback ไม่สมบูรณ์ กรุณาตรวจ Last-good ที่แจ้งไว้ก่อนเปิดระบบ"
        }
        else {
            try {
                Restore-BridgeScheduledTask -WasEnabled $bridgeTaskWasEnabled
            }
            catch {
                if ($bridgeEndpoint -and -not $script:applicationMutationStarted) {
                    $watchdogStatus = "repair_required"
                    $watchdogFailure = $true
                    $restoreWatchdogMessage = "Agent HQ และ Health พร้อมแล้ว แต่คืนสถานะ Watchdog เดิมไม่สำเร็จ กรุณารันคำสั่ง Repair Watchdog ที่แสดงด้านล่าง"
                    if (-not $postInstallFailures.Contains($restoreWatchdogMessage)) {
                        [void]$postInstallFailures.Add($restoreWatchdogMessage)
                    }
                    Write-Warning "${restoreWatchdogMessage}: $($_.Exception.Message)"
                }
                else {
                    throw
                }
            }
        }
    }

    $postInstallExitCode = if ($watchdogFailure -and $googleSetupFailure) {
        4
    }
    elseif ($watchdogFailure) {
        3
    }
    elseif ($googleSetupFailure) {
        2
    }
    else {
        0
    }
    if ($bridgeEndpoint) {
        Write-InstallResult `
            -Endpoint $bridgeEndpoint `
            -Readiness $codexReadiness `
            -WatchdogStatus $watchdogStatus `
            -PostInstallExitCode $postInstallExitCode
    }

    Write-Step "ติดตั้ง Runtime และตรวจ Health สำเร็จ ข้อมูลเริ่มต้นเป็นแบบ Local/Demo และไม่ได้ Login หรือเปิด Live Trading ให้อัตโนมัติ"
    Write-Host "ตำแหน่งโปรแกรม: $installRoot" -ForegroundColor Green
    if ($bridgeEndpoint) {
        Write-Host "หน้าโปรแกรม: $($bridgeEndpoint.Url)" -ForegroundColor Green
        Write-Host "รายงานการติดตั้ง: $installResultPath" -ForegroundColor Green
    }
    else {
        Write-Host "ยังไม่ได้เปิด Bridge ในขั้นตอนนี้ ให้เปิดจาก Shortcut เพื่อเลือกและยืนยัน Local endpoint" -ForegroundColor Yellow
    }
    if ($postInstallFailures.Count -gt 0) {
        $combinedFailure = ($postInstallFailures.ToArray() -join " | ")
        Write-InstallLog -Message ("ติดตั้ง Runtime สำเร็จแต่ขั้นตอนหลังติดตั้งยังไม่ครบ: {0}" -f $combinedFailure)
        foreach ($failure in $postInstallFailures) {
            Write-Host $failure -ForegroundColor Red
        }
        if ($watchdogFailure) {
            $repairCommand = 'powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "{0}" -RepairOnly -Port {1} -EndpointConfirmed -SkipGoogleSetup -SkipShortcuts' -f `
                (Join-Path $installRoot "installer\install.ps1"), $selectedBridgePort
            Write-Host "คำสั่ง Repair Watchdog (ไม่ติดตั้ง Source ซ้ำ):" -ForegroundColor Yellow
            Write-Host $repairCommand -ForegroundColor Cyan
        }
        Write-Host ("Runtime ยังเปิดใช้ได้และไม่ถูก Rollback; รหัสผลลัพธ์ {0}: 2=Google, 3=Watchdog, 4=ทั้งสองส่วน" -f $postInstallExitCode) -ForegroundColor Yellow
        exit $postInstallExitCode
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
