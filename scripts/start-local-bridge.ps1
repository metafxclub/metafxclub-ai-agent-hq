[CmdletBinding()]
param(
    [ValidateSet("Start", "Status", "Stop", "Restart")]
    [string]$Action = "Start",

    [ValidateRange(5, 120)]
    [int]$HealthTimeoutSeconds = 25
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot "runner\.venv\Scripts\python.exe"
$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$serverPath = Join-Path $projectRoot "backend\local-runner\bridge_server.py"
$runtimePath = Join-Path $projectRoot "data\runtime"
$logPath = Join-Path $runtimePath "logs"
$statePath = Join-Path $runtimePath "bridge-lifecycle-state.json"
$stdoutPath = Join-Path $logPath "bridge-stdout.log"
$stderrPath = Join-Path $logPath "bridge-stderr.log"
$auditPath = Join-Path $logPath "bridge-lifecycle-audit.jsonl"
$bridgeHost = "127.0.0.1"
$bridgePort = 4186
$bridgeUrl = "http://${bridgeHost}:$bridgePort/"
$healthUrl = "${bridgeUrl}api/health"
$maxLogBytes = 5MB
$logGenerations = 3
$mutexName = "Local\MetafxclubAgentHQBridge4186Lifecycle"

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

function Test-BridgeProcess {
    param([Parameter(Mandatory = $true)]$ProcessRecord)

    if (-not $ProcessRecord -or -not $ProcessRecord.CommandLine -or -not $ProcessRecord.ExecutablePath) {
        return $false
    }

    if ($ProcessRecord.Name -notin @("python.exe", "pythonw.exe")) {
        return $false
    }

    $tokens = @(Split-CommandLine -CommandLine ([string]$ProcessRecord.CommandLine))
    if ($tokens.Count -ne 6) {
        return $false
    }

    $commandExecutable = Get-ComparablePath -Path $tokens[0]
    $recordExecutable = Get-ComparablePath -Path ([string]$ProcessRecord.ExecutablePath)
    $commandServer = Get-ComparablePath -Path $tokens[1]
    $expectedServer = Get-ComparablePath -Path $serverPath

    return (
        $commandExecutable -and
        $recordExecutable -and
        $commandServer -and
        $expectedServer -and
        $commandExecutable.Equals($recordExecutable, [StringComparison]::OrdinalIgnoreCase) -and
        $commandServer.Equals($expectedServer, [StringComparison]::OrdinalIgnoreCase) -and
        $tokens[2] -ceq "--host" -and
        $tokens[3] -ceq $bridgeHost -and
        $tokens[4] -ceq "--port" -and
        $tokens[5] -ceq ([string]$bridgePort)
    )
}

function Get-ProcessRecord {
    param([Parameter(Mandatory = $true)][int]$ProcessId)

    return Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
}

function Get-BridgeProcesses {
    $pythonProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop
    return @($pythonProcesses | Where-Object { Test-BridgeProcess -ProcessRecord $_ })
}

function Get-ListenerProcessIds {
    return @(
        Get-NetTCPConnection -LocalPort $bridgePort -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    )
}

function Test-BridgeHealth {
    try {
        $response = Invoke-WebRequest -Uri $healthUrl -Method Get -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -ne 200) {
            return $false
        }
        $health = $response.Content | ConvertFrom-Json
        return $health.ok -eq $true -and $health.status -eq "ready"
    }
    catch {
        return $false
    }
}

function Wait-ForBridgeHealth {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        # Always re-discover the exact command. On Windows, a venv launcher can
        # temporarily coexist with the base Python listener under another PID.
        $candidates = @(Get-BridgeProcesses)

        $listenerProcessIds = @(Get-ListenerProcessIds)
        foreach ($candidate in $candidates) {
            $candidateId = [int]$candidate.ProcessId
            if ($listenerProcessIds -contains $candidateId -and (Test-BridgeHealth)) {
                return $candidateId
            }
        }

        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)

    return $null
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
    if (-not (Test-BridgeProcess -ProcessRecord $record)) {
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

    $bridgeProcesses = @(Get-BridgeProcesses)
    $listenerProcessIds = @(Get-ListenerProcessIds)
    $bridgeProcessIds = @($bridgeProcesses | Select-Object -ExpandProperty ProcessId)
    $foreignListeners = @($listenerProcessIds | Where-Object { $bridgeProcessIds -notcontains $_ })

    if ($foreignListeners.Count -gt 0) {
        throw "Port $bridgePort is already used by an unrelated process (PID $($foreignListeners -join ', ')). It was not stopped."
    }
    if ($bridgeProcesses.Count -gt 1) {
        throw "Multiple exact Metafx bridge processes were found (PID $($bridgeProcessIds -join ', ')). Run Restart to cleanly replace them."
    }

    if ($bridgeProcesses.Count -eq 1) {
        $existing = $bridgeProcesses[0]
        $existingId = [int]$existing.ProcessId
        $healthyExistingId = Wait-ForBridgeHealth -ProcessId $existingId -TimeoutSeconds $HealthTimeoutSeconds
        if ($healthyExistingId) {
            $healthyExisting = Get-ProcessRecord -ProcessId $healthyExistingId
            $startedAt = if ($healthyExisting.CreationDate) { ([DateTime]$healthyExisting.CreationDate).ToUniversalTime().ToString("o") } else { "" }
            Write-LifecycleState -Status "running" -ProcessId $healthyExistingId -PythonPath ([string]$healthyExisting.ExecutablePath) -StartedAt $startedAt
            Write-AuditEvent -Operation "start" -Outcome "already_running" -ProcessId $healthyExistingId -Message "Healthy exact bridge instance reused."
            Write-Host "Metafx Local Bridge is already healthy at $bridgeUrl (PID $healthyExistingId)."
            return 0
        }

        throw "An exact Metafx bridge process exists (PID $existingId) but did not become healthy. Run Restart to replace it safely."
    }

    $pythonPath = Resolve-PythonExecutable
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
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

    $healthyProcessId = Wait-ForBridgeHealth -ProcessId $startedId -TimeoutSeconds $HealthTimeoutSeconds
    if (-not $healthyProcessId) {
        # There was no exact instance before this guarded start. Clean up any
        # exact verified child left by a failed venv redirector launch.
        foreach ($record in @(Get-BridgeProcesses)) {
            Stop-VerifiedProcess -ProcessId ([int]$record.ProcessId) | Out-Null
        }
        Write-LifecycleState -Status "failed" -PythonPath $pythonPath -StartedAt $startedAt -LastError "Health check did not pass within $HealthTimeoutSeconds seconds."
        throw "Bridge startup failed its health check after $HealthTimeoutSeconds seconds. See $stderrPath"
    }

    $healthyRecord = Get-ProcessRecord -ProcessId $healthyProcessId
    $healthyPythonPath = if ($healthyRecord -and $healthyRecord.ExecutablePath) { [string]$healthyRecord.ExecutablePath } else { $pythonPath }
    Write-LifecycleState -Status "running" -ProcessId $healthyProcessId -PythonPath $healthyPythonPath -StartedAt $startedAt
    Write-AuditEvent -Operation "start" -Outcome "started" -ProcessId $healthyProcessId -Message "Bridge passed the HTTP health check."
    Write-Host "Metafx Local Bridge is healthy at $bridgeUrl (PID $healthyProcessId)."
    Write-Host "Logs: $stdoutPath and $stderrPath"
    return 0
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

    Write-AuditEvent -Operation $operation -Outcome "requested" -Message "Lifecycle action requested."
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
