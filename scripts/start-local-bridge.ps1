[CmdletBinding()]
param(
    [ValidateSet("Start", "Status", "Stop", "Restart")]
    [string]$Action = "Start",

    [ValidateRange(5, 120)]
    [int]$HealthTimeoutSeconds = 25,

    [ValidateRange(0, 65535)]
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"

if ($Port -ne 0 -and $Port -lt 1024) {
    throw "Port ต้องเป็น 0 หรืออยู่ในช่วง 1024-65535"
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot "runner\.venv\Scripts\python.exe"
$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$serverPath = Join-Path $projectRoot "backend\local-runner\bridge_server.py"
$runtimePath = Join-Path $projectRoot "data\runtime"
$logPath = Join-Path $runtimePath "logs"
$statePath = Join-Path $runtimePath "bridge-lifecycle-state.json"
$endpointPath = Join-Path $runtimePath "bridge-endpoint.json"
$stdoutPath = Join-Path $logPath "bridge-stdout.log"
$stderrPath = Join-Path $logPath "bridge-stderr.log"
$auditPath = Join-Path $logPath "bridge-lifecycle-audit.jsonl"
$bridgeHost = "127.0.0.1"
$bridgePort = 4186
$bridgeUrl = "http://${bridgeHost}:$bridgePort/"
$healthUrl = "${bridgeUrl}api/health"
$maxLogBytes = 5MB
$logGenerations = 3
$mutexName = "Local\MetafxclubAgentHQBridgeLifecycle"
$bridgeInventoryConflict = @()
$requestedBridgePort = if ($Port -ge 1024) { $Port } else { 0 }
$confirmedEndpointRequired = $false

function Get-UtcTimestamp {
    return [DateTime]::UtcNow.ToString("o")
}

function Get-ComparablePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    try {
        return [IO.Path]::GetFullPath($Path).TrimEnd("\")
    }
    catch {
        return $null
    }
}

function Split-CommandLine {
    param([Parameter(Mandatory = $true)][string]$CommandLine)

    $tokens = New-Object System.Collections.Generic.List[string]
    foreach ($match in [regex]::Matches($CommandLine, '(?:"[^"]*"|[^\s"]+)')) {
        $value = $match.Value
        if ($value.Length -ge 2 -and $value[0] -eq '"' -and $value[$value.Length - 1] -eq '"') {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $tokens.Add($value)
    }
    return $tokens.ToArray()
}

function Set-BridgeEndpointContext {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$Port)

    $script:bridgeHost = "127.0.0.1"
    $script:bridgePort = $Port
    $script:bridgeUrl = "http://127.0.0.1:$Port/"
    $script:healthUrl = "${script:bridgeUrl}api/health"
}

function Read-BridgeEndpoint {
    if (-not (Test-Path -LiteralPath $endpointPath -PathType Leaf)) {
        return $null
    }

    try {
        $endpoint = Get-Content -LiteralPath $endpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ([string]$endpoint.host -cne "127.0.0.1") {
            return $null
        }
        $port = [int]$endpoint.port
        if ($port -lt 1024 -or $port -gt 65535) {
            return $null
        }
        return [pscustomobject]@{
            Host = "127.0.0.1"
            Port = $port
            Url = "http://127.0.0.1:$port/"
            HealthUrl = "http://127.0.0.1:$port/api/health"
        }
    }
    catch {
        return $null
    }
}

function Write-BridgeEndpoint {
    param([Parameter(Mandatory = $true)]$Health)

    if (-not $Health -or -not $Health.endpoint) {
        throw "Bridge health response did not include a confirmed endpoint."
    }
    $reportedHost = [string]$Health.endpoint.host
    $reportedPort = [int]$Health.endpoint.port
    if ($reportedHost -cne "127.0.0.1" -or $reportedPort -ne $bridgePort) {
        throw "Bridge health endpoint did not match the requested loopback host and port."
    }

    New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
    $endpoint = [ordered]@{
        version = 1
        host = "127.0.0.1"
        port = $bridgePort
        url = $bridgeUrl
        health_url = $healthUrl
        confirmed_at = Get-UtcTimestamp
    }
    $json = $endpoint | ConvertTo-Json -Depth 3
    $temporaryPath = "$endpointPath.tmp.$([Guid]::NewGuid().ToString('N'))"
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($temporaryPath, $json + [Environment]::NewLine, $utf8)
    Move-Item -LiteralPath $temporaryPath -Destination $endpointPath -Force
}

function Test-LoopbackPortAvailable {
    param([Parameter(Mandatory = $true)][ValidateRange(1024, 65535)][int]$Port)

    $listener = $null
    try {
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
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

function Select-RandomAvailableBridgePort {
    $attempted = New-Object 'System.Collections.Generic.HashSet[int]'
    for ($attempt = 0; $attempt -lt 256; $attempt++) {
        $candidate = Get-Random -Minimum 42000 -Maximum 50000
        if (-not $attempted.Add($candidate)) {
            continue
        }
        if ((@(Get-ListenerProcessIds -Port $candidate)).Count -eq 0 -and (Test-LoopbackPortAvailable -Port $candidate)) {
            return $candidate
        }
    }
    throw "No available local port was found in the guarded range 42000-49999."
}

function Select-StartBridgeEndpoint {
    $listenerProcessIds = @(Get-ListenerProcessIds)
    $bridgeProcesses = @(Get-BridgeProcesses)
    $bridgeProcessIds = @($bridgeProcesses | Select-Object -ExpandProperty ProcessId)
    $foreignListeners = @($listenerProcessIds | Where-Object { $bridgeProcessIds -notcontains $_ })
    $portUnavailable = $listenerProcessIds.Count -eq 0 -and -not (Test-LoopbackPortAvailable -Port $bridgePort)

    if ($foreignListeners.Count -eq 0 -and -not $portUnavailable) {
        return
    }

    if ($confirmedEndpointRequired) {
        throw "พอร์ตที่ยืนยันไว้ ($bridgePort) ไม่ว่างแล้ว ระบบหยุดโดยไม่เปลี่ยนไปใช้ URL อื่น กรุณาเลือกพอร์ตใหม่"
    }

    $previousPort = $bridgePort
    $selectedPort = Select-RandomAvailableBridgePort
    Set-BridgeEndpointContext -Port $selectedPort
    Write-AuditEvent `
        -Operation "endpoint_select" `
        -Outcome "foreign_port_preserved" `
        -Message "Port $previousPort was unavailable; selected a free loopback port without stopping another process."
}

function Get-BridgeProcessIdentity {
    param([Parameter(Mandatory = $true)]$ProcessRecord)

    if (-not $ProcessRecord -or -not $ProcessRecord.CommandLine -or -not $ProcessRecord.ExecutablePath) {
        return $null
    }

    if ($ProcessRecord.Name -notin @("python.exe", "pythonw.exe")) {
        return $null
    }

    $tokens = @(Split-CommandLine -CommandLine ([string]$ProcessRecord.CommandLine))
    if ($tokens.Count -ne 6) {
        return $null
    }

    $commandExecutable = Get-ComparablePath -Path $tokens[0]
    $recordExecutable = Get-ComparablePath -Path ([string]$ProcessRecord.ExecutablePath)
    $commandServer = Get-ComparablePath -Path $tokens[1]
    $expectedServer = Get-ComparablePath -Path $serverPath

    if (
        -not $commandExecutable -or
        -not $recordExecutable -or
        -not $commandServer -or
        -not $expectedServer -or
        -not $commandExecutable.Equals($recordExecutable, [StringComparison]::OrdinalIgnoreCase) -or
        -not $commandServer.Equals($expectedServer, [StringComparison]::OrdinalIgnoreCase) -or
        $tokens[2] -cne "--host" -or
        $tokens[3] -cne "127.0.0.1" -or
        $tokens[4] -cne "--port"
    ) {
        return $null
    }

    $parsedPort = 0
    if (-not [int]::TryParse([string]$tokens[5], [ref]$parsedPort) -or $parsedPort -lt 1024 -or $parsedPort -gt 65535) {
        return $null
    }

    return [pscustomobject]@{
        ProcessId = [int]$ProcessRecord.ProcessId
        Port = $parsedPort
        Record = $ProcessRecord
    }
}

function Test-BridgeProcess {
    param(
        [Parameter(Mandatory = $true)]$ProcessRecord,
        [Nullable[int]]$ExpectedPort = $null
    )

    $identity = Get-BridgeProcessIdentity -ProcessRecord $ProcessRecord
    if (-not $identity) {
        return $false
    }
    if ($null -ne $ExpectedPort -and [int]$identity.Port -ne [int]$ExpectedPort) {
        return $false
    }
    return $true
}

function Get-ProcessRecord {
    param([Parameter(Mandatory = $true)][int]$ProcessId)

    return Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
}

function Get-AllBridgeProcessIdentities {
    $pythonProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop
    $identities = New-Object System.Collections.Generic.List[object]
    foreach ($processRecord in @($pythonProcesses)) {
        $identity = Get-BridgeProcessIdentity -ProcessRecord $processRecord
        if ($identity) {
            $identities.Add($identity)
        }
    }
    return $identities.ToArray()
}

function Get-BridgeProcesses {
    return @(
        Get-AllBridgeProcessIdentities |
            Where-Object { [int]$_.Port -eq $bridgePort } |
            ForEach-Object { $_.Record }
    )
}

function Get-ListenerProcessIds {
    param([int]$Port = $bridgePort)

    return @(
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    )
}

function Get-ConfirmedBridgeHealth {
    param([int]$Port = $bridgePort)

    $targetHealthUrl = "http://127.0.0.1:$Port/api/health"
    try {
        $response = Invoke-WebRequest -Uri $targetHealthUrl -Method Get -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -ne 200) {
            return $null
        }
        $health = $response.Content | ConvertFrom-Json
        if (
            $health.ok -ne $true -or
            $health.status -ne "ready" -or
            -not $health.endpoint -or
            [string]$health.endpoint.host -cne "127.0.0.1" -or
            [int]$health.endpoint.port -ne $Port
        ) {
            return $null
        }
        return $health
    }
    catch {
        return $null
    }
}

function Test-BridgeHealth {
    return $null -ne (Get-ConfirmedBridgeHealth -Port $bridgePort)
}

function Wait-ForBridgeHealth {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $missingPolls = 0
    do {
        $candidate = Get-ProcessRecord -ProcessId $ProcessId
        if (-not $candidate) {
            $missingPolls++
            if ($missingPolls -ge 4) {
                return $null
            }
            Start-Sleep -Milliseconds 250
            continue
        }
        $missingPolls = 0
        $listenerProcessIds = @(Get-ListenerProcessIds)
        if (
            (Test-BridgeProcess -ProcessRecord $candidate -ExpectedPort $bridgePort) -and
            $listenerProcessIds -contains $ProcessId
        ) {
            $health = Get-ConfirmedBridgeHealth -Port $bridgePort
            if ($health) {
                return [pscustomobject]@{
                    ProcessId = $ProcessId
                    Health = $health
                }
            }
        }

        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)

    return $null
}

function Get-BridgeIdentityHealth {
    param([Parameter(Mandatory = $true)]$Identity)

    $identityPort = [int]$Identity.Port
    $listenerProcessIds = @(Get-ListenerProcessIds -Port $identityPort)
    if ($listenerProcessIds -notcontains [int]$Identity.ProcessId) {
        return $null
    }
    return Get-ConfirmedBridgeHealth -Port $identityPort
}

function Initialize-BridgeEndpointContext {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("start", "status", "stop", "restart")]
        [string]$Operation
    )

    $savedEndpoint = Read-BridgeEndpoint
    $identities = @(Get-AllBridgeProcessIdentities)
    $script:bridgeInventoryConflict = @()

    if ($identities.Count -gt 1) {
        $script:bridgeInventoryConflict = $identities
        if ($savedEndpoint) {
            Set-BridgeEndpointContext -Port ([int]$savedEndpoint.Port)
        }
        else {
            Set-BridgeEndpointContext -Port 4186
        }
        if ($Operation -eq "status") {
            return "inventory_conflict"
        }
        $ids = @($identities | ForEach-Object { $_.ProcessId })
        throw "Multiple exact Metafx bridge processes were found (PID $($ids -join ', ')). Refusing to guess which instance owns the saved endpoint."
    }

    if ($identities.Count -eq 1) {
        $identity = $identities[0]
        if (
            $Operation -eq "start" -and
            $requestedBridgePort -ge 1024 -and
            [int]$identity.Port -ne $requestedBridgePort
        ) {
            throw "พบ HQ Bridge เดิมทำงานอยู่ที่พอร์ต $($identity.Port) แต่คำขอนี้ระบุพอร์ต $requestedBridgePort ระบบจึงไม่เปิด Instance ซ้ำ"
        }
        Set-BridgeEndpointContext -Port ([int]$identity.Port)
        $health = Get-BridgeIdentityHealth -Identity $identity
        if ($health) {
            if ($savedEndpoint -and [int]$savedEndpoint.Port -eq [int]$identity.Port) {
                $script:confirmedEndpointRequired = $true
                return "saved_verified"
            }
            try {
                Write-BridgeEndpoint -Health $health
                $script:confirmedEndpointRequired = $true
                return "recovered_verified"
            }
            catch {
                if ($Operation -in @("status", "stop", "restart")) {
                    return "recovered_unpersisted"
                }
                throw
            }
        }
        return "exact_process_unhealthy"
    }

    if ($Operation -eq "start" -and $requestedBridgePort -ge 1024) {
        Set-BridgeEndpointContext -Port $requestedBridgePort
        $script:confirmedEndpointRequired = $true
        return "user_confirmed"
    }

    if ($savedEndpoint) {
        Set-BridgeEndpointContext -Port ([int]$savedEndpoint.Port)
        if ($Operation -in @("start", "restart")) {
            $script:confirmedEndpointRequired = $true
        }
        return "saved"
    }

    Set-BridgeEndpointContext -Port 4186
    return "default"
}

function Rotate-LogFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [switch]$ArchiveCurrent
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }

    $item = Get-Item -LiteralPath $Path
    if (-not $ArchiveCurrent -and $item.Length -lt $maxLogBytes) {
        return
    }

    for ($generation = $logGenerations; $generation -ge 1; $generation--) {
        $destination = "$Path.$generation"
        if ($generation -eq $logGenerations) {
            if (Test-Path -LiteralPath $destination) {
                Remove-Item -LiteralPath $destination -Force
            }
            continue
        }

        $source = "$Path.$generation"
        $nextDestination = "$Path.$($generation + 1)"
        if (Test-Path -LiteralPath $source) {
            Move-Item -LiteralPath $source -Destination $nextDestination -Force
        }
    }

    Move-Item -LiteralPath $Path -Destination "$Path.1" -Force
}

function Write-AuditEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Operation,
        [Parameter(Mandatory = $true)][string]$Outcome,
        [Nullable[int]]$ProcessId = $null,
        [string]$Message = ""
    )

    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    Rotate-LogFile -Path $auditPath

    $event = [ordered]@{
        timestamp = Get-UtcTimestamp
        component = "local_bridge_lifecycle"
        operation = $Operation
        outcome = $Outcome
        process_id = $ProcessId
        host = $bridgeHost
        port = $bridgePort
        message = $Message
    }
    $line = ($event | ConvertTo-Json -Compress -Depth 4) + [Environment]::NewLine
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::AppendAllText($auditPath, $line, $utf8)
}

function Write-LifecycleState {
    param(
        [Parameter(Mandatory = $true)][string]$Status,
        [Nullable[int]]$ProcessId = $null,
        [string]$PythonPath = "",
        [string]$StartedAt = "",
        [string]$LastError = ""
    )

    New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
    $state = [ordered]@{
        version = 1
        status = $Status
        process_id = $ProcessId
        host = $bridgeHost
        port = $bridgePort
        url = $bridgeUrl
        health_url = $healthUrl
        server_path = $serverPath
        python_path = $PythonPath
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        started_at = $StartedAt
        updated_at = Get-UtcTimestamp
        last_error = $LastError
    }
    $json = $state | ConvertTo-Json -Depth 4
    $temporaryPath = "$statePath.tmp.$([Guid]::NewGuid().ToString('N'))"
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($temporaryPath, $json + [Environment]::NewLine, $utf8)
    Move-Item -LiteralPath $temporaryPath -Destination $statePath -Force
}

function Resolve-PythonExecutable {
    if (Test-Path -LiteralPath $projectPython -PathType Leaf) {
        # The Windows venv executable is a redirector that can leave both a
        # launcher PID and a listener PID. Resolve its base interpreter once so
        # lifecycle identity, status and stop operations track one exact PID.
        try {
            $basePython = (& $projectPython -c "import sys; print(sys._base_executable)" 2>$null | Select-Object -Last 1)
            if ($LASTEXITCODE -eq 0 -and $basePython -and (Test-Path -LiteralPath $basePython -PathType Leaf)) {
                return (Get-Item -LiteralPath $basePython).FullName
            }
        }
        catch {
            # Fall through to the bundled runtime or PATH lookup below.
        }
    }

    if (Test-Path -LiteralPath $bundledPython -PathType Leaf) {
        return (Get-Item -LiteralPath $bundledPython).FullName
    }

    $command = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) {
        throw "Python was not found. Run 1-INSTALL-HQ.bat first, or install Python 3.10 or newer."
    }
    return $command.Source
}

function Stop-VerifiedProcess {
    param([Parameter(Mandatory = $true)][int]$ProcessId)

    $record = Get-ProcessRecord -ProcessId $ProcessId
    if (-not $record) {
        return $false
    }
    if (-not (Test-BridgeProcess -ProcessRecord $record -ExpectedPort $bridgePort)) {
        throw "Refusing to stop PID $ProcessId because its exact command line is not the Metafx bridge command."
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction Stop
    Wait-Process -Id $ProcessId -Timeout 10 -ErrorAction SilentlyContinue
    return $true
}

function Start-Bridge {
    if (-not (Test-Path -LiteralPath $serverPath -PathType Leaf)) {
        throw "Bridge server not found at $serverPath"
    }

    Select-StartBridgeEndpoint
    $candidates = @(Get-BridgeProcesses)
    $bridgeProcesses = $candidates
    $bridgeProcessIds = @($bridgeProcesses | Select-Object -ExpandProperty ProcessId)
    if ($bridgeProcesses.Count -gt 1) {
        throw "Multiple exact Metafx bridge processes were found (PID $($bridgeProcessIds -join ', ')). Run Restart to cleanly replace them."
    }

    if ($bridgeProcesses.Count -eq 1) {
        $existing = $bridgeProcesses[0]
        $existingId = [int]$existing.ProcessId
        $healthyExistingResult = Wait-ForBridgeHealth -ProcessId $existingId -TimeoutSeconds $HealthTimeoutSeconds
        if ($healthyExistingResult) {
            $healthyExistingId = [int]$healthyExistingResult.ProcessId
            $healthyExisting = Get-ProcessRecord -ProcessId $healthyExistingId
            $startedAt = if ($healthyExisting.CreationDate) { ([DateTime]$healthyExisting.CreationDate).ToUniversalTime().ToString("o") } else { "" }
            Write-BridgeEndpoint -Health $healthyExistingResult.Health
            Write-LifecycleState -Status "running" -ProcessId $healthyExistingId -PythonPath ([string]$healthyExisting.ExecutablePath) -StartedAt $startedAt
            Write-AuditEvent -Operation "start" -Outcome "already_running" -ProcessId $healthyExistingId -Message "Healthy exact bridge instance reused."
            Write-Host "Metafx Local Bridge is already healthy at $bridgeUrl (PID $healthyExistingId)."
            return 0
        }

        throw "An exact Metafx bridge process exists (PID $existingId) but did not become healthy. Run Restart to replace it safely."
    }

    $pythonPath = Resolve-PythonExecutable
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        if ($attempt -gt 1) {
            if ($confirmedEndpointRequired) {
                throw "พอร์ตที่ผู้ใช้ยืนยันไม่สามารถเริ่ม Bridge ได้ ระบบหยุดโดยไม่สลับไป URL อื่น"
            }
            $previousPort = $bridgePort
            $retryPort = Select-RandomAvailableBridgePort
            Set-BridgeEndpointContext -Port $retryPort
            Write-AuditEvent -Operation "start" -Outcome "retry_port_selected" -Message "Retry $attempt selected port $retryPort after port $previousPort failed without stopping another process."
        }

        Select-StartBridgeEndpoint
        $attemptBridgeProcesses = @(Get-BridgeProcesses)
        if ($attemptBridgeProcesses.Count -gt 0) {
            $ids = @($attemptBridgeProcesses | Select-Object -ExpandProperty ProcessId)
            throw "An exact Metafx bridge process appeared during startup (PID $($ids -join ', ')). Refusing to launch a duplicate."
        }

        $attemptListenerIds = @(Get-ListenerProcessIds)
        if ($attemptListenerIds.Count -gt 0 -or -not (Test-LoopbackPortAvailable -Port $bridgePort)) {
            Write-AuditEvent -Operation "start" -Outcome "port_race_detected" -Message "Attempt $attempt found port $bridgePort unavailable and preserved its listener."
            if ($attempt -lt 3) {
                continue
            }
            throw "Bridge could not reserve a local port after 3 guarded attempts. No foreign process was stopped."
        }

        Rotate-LogFile -Path $stdoutPath -ArchiveCurrent
        Rotate-LogFile -Path $stderrPath -ArchiveCurrent
        $startedAt = Get-UtcTimestamp
        Write-LifecycleState -Status "starting" -PythonPath $pythonPath -StartedAt $startedAt
        $arguments = @(
            ('"{0}"' -f $serverPath),
            "--host",
            $bridgeHost,
            "--port",
            ([string]$bridgePort)
        )

        $startedProcess = Start-Process `
            -FilePath $pythonPath `
            -ArgumentList $arguments `
            -WorkingDirectory $projectRoot `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru

        $startedId = [int]$startedProcess.Id
        Write-LifecycleState -Status "starting" -ProcessId $startedId -PythonPath $pythonPath -StartedAt $startedAt

        $healthyProcessResult = Wait-ForBridgeHealth -ProcessId $startedId -TimeoutSeconds $HealthTimeoutSeconds
        if (-not $healthyProcessResult) {
            $startedRecord = Get-ProcessRecord -ProcessId $startedId
            if ($startedRecord -and (Test-BridgeProcess -ProcessRecord $startedRecord -ExpectedPort $bridgePort)) {
                Stop-VerifiedProcess -ProcessId $startedId | Out-Null
            }
            Write-LifecycleState -Status "failed" -PythonPath $pythonPath -StartedAt $startedAt -LastError "Startup attempt $attempt did not pass its endpoint-bound health check."
            Write-AuditEvent -Operation "start" -Outcome "attempt_failed" -ProcessId $startedId -Message "Attempt $attempt failed health or bind verification; only its exact launched PID was eligible for cleanup."
            if ($attempt -lt 3) {
                continue
            }
            throw "Bridge startup failed after 3 guarded attempts. See $stderrPath"
        }

        $healthyProcessId = [int]$healthyProcessResult.ProcessId
        $healthyRecord = Get-ProcessRecord -ProcessId $healthyProcessId
        $healthyPythonPath = if ($healthyRecord -and $healthyRecord.ExecutablePath) { [string]$healthyRecord.ExecutablePath } else { $pythonPath }
        try {
            Write-BridgeEndpoint -Health $healthyProcessResult.Health
            Write-LifecycleState -Status "running" -ProcessId $healthyProcessId -PythonPath $healthyPythonPath -StartedAt $startedAt
        }
        catch {
            $persistError = [string]$_.Exception.Message
            $verifiedRecord = Get-ProcessRecord -ProcessId $healthyProcessId
            if ($verifiedRecord -and (Test-BridgeProcess -ProcessRecord $verifiedRecord -ExpectedPort $bridgePort)) {
                Stop-VerifiedProcess -ProcessId $healthyProcessId | Out-Null
            }
            try {
                Write-AuditEvent -Operation "start" -Outcome "persistence_failed_process_stopped" -ProcessId $healthyProcessId -Message "The newly launched verified PID was stopped because endpoint/state persistence failed."
            }
            catch { }
            throw "Bridge passed Health but endpoint/state persistence failed; the newly launched process was stopped. $persistError"
        }
        Write-AuditEvent -Operation "start" -Outcome "started" -ProcessId $healthyProcessId -Message "Bridge passed the endpoint-bound HTTP health check."
        Write-Host "Metafx Local Bridge is healthy at $bridgeUrl (PID $healthyProcessId)."
        Write-Host "Logs: $stdoutPath and $stderrPath"
        return 0
    }

    throw "Bridge startup exhausted its guarded retries."
}

function Stop-Bridge {
    $bridgeProcesses = @(Get-BridgeProcesses)
    if ($bridgeProcesses.Count -eq 0) {
        $listenerProcessIds = @(Get-ListenerProcessIds)
        if ($listenerProcessIds.Count -gt 0) {
            Write-Host "No exact Metafx bridge process is running. Port $bridgePort belongs to unrelated PID $($listenerProcessIds -join ', ') and was left untouched."
        }
        else {
            Write-Host "Metafx Local Bridge is already stopped."
        }
        Write-LifecycleState -Status "stopped"
        Write-AuditEvent -Operation "stop" -Outcome "already_stopped" -Message "No exact bridge process found."
        return 0
    }

    $stoppedIds = New-Object System.Collections.Generic.List[int]
    foreach ($processRecord in $bridgeProcesses) {
        $processId = [int]$processRecord.ProcessId
        if (Stop-VerifiedProcess -ProcessId $processId) {
            $stoppedIds.Add($processId)
        }
    }

    Write-LifecycleState -Status "stopped"
    Write-AuditEvent -Operation "stop" -Outcome "stopped" -Message "Stopped exact bridge PID(s): $($stoppedIds -join ', ')."
    Write-Host "Metafx Local Bridge stopped (PID $($stoppedIds -join ', '))."
    return 0
}

function Get-BridgeStatus {
    if (@($bridgeInventoryConflict).Count -gt 1) {
        $ids = @($bridgeInventoryConflict | ForEach-Object { $_.ProcessId })
        Write-AuditEvent -Operation "status" -Outcome "multiple_instances" -Message "Multiple exact bridge processes were found across local ports."
        Write-Host "UNHEALTHY: multiple exact Metafx bridge processes found (PID $($ids -join ', '))."
        return 5
    }

    $bridgeProcesses = @(Get-BridgeProcesses)
    $listenerProcessIds = @(Get-ListenerProcessIds)

    if ($bridgeProcesses.Count -eq 0) {
        if ($listenerProcessIds.Count -gt 0) {
            Write-AuditEvent -Operation "status" -Outcome "port_conflict" -Message "Port belongs to an unrelated process."
            Write-Host "CONFLICT: port $bridgePort is used by unrelated PID $($listenerProcessIds -join ', ')."
            return 4
        }
        Write-AuditEvent -Operation "status" -Outcome "stopped" -Message "No exact bridge process found."
        Write-Host "STOPPED: Metafx Local Bridge is not running."
        return 3
    }

    if ($bridgeProcesses.Count -gt 1) {
        $ids = @($bridgeProcesses | Select-Object -ExpandProperty ProcessId)
        Write-AuditEvent -Operation "status" -Outcome "multiple_instances" -Message "Multiple exact bridge processes found."
        Write-Host "UNHEALTHY: multiple exact bridge processes found (PID $($ids -join ', '))."
        return 5
    }

    $bridgeProcess = $bridgeProcesses[0]
    $bridgeProcessId = [int]$bridgeProcess.ProcessId
    if ($listenerProcessIds -contains $bridgeProcessId -and (Test-BridgeHealth)) {
        Write-AuditEvent -Operation "status" -Outcome "healthy" -ProcessId $bridgeProcessId -Message "Listener and HTTP health check are ready."
        Write-Host "HEALTHY: $bridgeUrl (PID $bridgeProcessId)."
        Write-Host "State: $statePath"
        Write-Host "Logs: $stdoutPath and $stderrPath"
        return 0
    }

    Write-AuditEvent -Operation "status" -Outcome "unhealthy" -ProcessId $bridgeProcessId -Message "Exact process exists but listener or HTTP health check is unavailable."
    Write-Host "UNHEALTHY: exact bridge PID $bridgeProcessId exists, but the listener or HTTP health check is not ready."
    return 2
}

$mutex = New-Object Threading.Mutex($false, $mutexName)
$lockTaken = $false
$operation = $Action.ToLowerInvariant()
$exitCode = 1

try {
    try {
        $lockTaken = $mutex.WaitOne([TimeSpan]::FromSeconds(15))
    }
    catch [Threading.AbandonedMutexException] {
        $lockTaken = $true
    }
    if (-not $lockTaken) {
        throw "Another bridge lifecycle action is still running. Try again shortly."
    }

    $endpointSource = Initialize-BridgeEndpointContext -Operation $operation
    Write-AuditEvent -Operation $operation -Outcome "requested" -Message "Lifecycle action requested with $endpointSource loopback endpoint."
    switch ($Action) {
        "Start" {
            $exitCode = Start-Bridge
        }
        "Status" {
            $exitCode = Get-BridgeStatus
        }
        "Stop" {
            $exitCode = Stop-Bridge
        }
        "Restart" {
            Write-AuditEvent -Operation "restart" -Outcome "stopping" -Message "Restart requested; stopping exact bridge instance first."
            Stop-Bridge | Out-Null
            if ($requestedBridgePort -ge 1024) {
                Set-BridgeEndpointContext -Port $requestedBridgePort
            }
            $exitCode = Start-Bridge
            if ($exitCode -eq 0) {
                Write-AuditEvent -Operation "restart" -Outcome "started" -Message "Restart completed and health check passed."
            }
        }
    }
}
catch {
    $safeMessage = [string]$_.Exception.Message
    try {
        Write-AuditEvent -Operation $operation -Outcome "failed" -Message $safeMessage
    }
    catch {
        # The primary error is more useful than a secondary audit-write error.
    }
    Write-Error $safeMessage
    $exitCode = 1
}
finally {
    if ($lockTaken) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}

exit $exitCode
