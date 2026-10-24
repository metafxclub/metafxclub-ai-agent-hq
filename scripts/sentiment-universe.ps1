[CmdletBinding()]
param(
    [ValidateSet('Start','Ensure','Status','Stop','Restart')][string]$Action = 'Ensure',
    [ValidateRange(1024,65535)][int]$Port = 4197,
    [string]$StateDirectory = '',
    [string]$PythonPath = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$hqRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$packageRoot = Join-Path $hqRoot 'backend\local-runner\sentiment_universe'
$launcher = Join-Path $packageRoot 'scripts\start-live.py'
$staticRoot = Join-Path $hqRoot 'frontend\public\sentiment-universe'
$mirror = Join-Path $staticRoot 'market.json'
if (-not $StateDirectory) { $StateDirectory = Join-Path $env:LOCALAPPDATA 'Metafxclub\SentimentUniverse' }
$StateDirectory = [IO.Path]::GetFullPath($StateDirectory).TrimEnd('\')
if (-not $PythonPath) { $PythonPath = Join-Path $hqRoot 'runner\.venv\Scripts\pythonw.exe' }
$PythonPath = [IO.Path]::GetFullPath($PythonPath)
$supervisorPath = Join-Path $StateDirectory 'supervisor.json'
$servicePath = Join-Path $StateDirectory 'service.json'

if (-not ('SentimentCommandLine' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SentimentCommandLine {
 [DllImport("shell32.dll", SetLastError=true)] static extern IntPtr CommandLineToArgvW([MarshalAs(UnmanagedType.LPWStr)] string value, out int count);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr value);
 public static string[] Split(string value) {
  int count; IntPtr pointer=CommandLineToArgvW(value,out count);
  if(pointer==IntPtr.Zero) return new string[0];
  try { string[] values=new string[count]; for(int n=0;n<count;n++) values[n]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(pointer,n*IntPtr.Size)); return values; }
  finally { LocalFree(pointer); }
 }
}
'@
}

function Read-Record([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}
function Get-RecordedPid($Record,[string]$Name='pid') {
    if ($null -eq $Record -or -not $Record.PSObject.Properties[$Name]) { return 0 }
    try { return [int]$Record.$Name } catch { return 0 }
}
function Get-ProcessRecord([int]$ProcessId) {
    if ($ProcessId -le 0) { return $null }
    return Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
}
function Get-AllowedPythonPaths {
    $paths = @($PythonPath)
    $venvConfig = Join-Path (Split-Path -Parent (Split-Path -Parent $PythonPath)) 'pyvenv.cfg'
    if (Test-Path -LiteralPath $venvConfig -PathType Leaf) {
        $homeLine = Get-Content -LiteralPath $venvConfig | Where-Object { $_ -match '^home\s*=\s*(.+)$' } | Select-Object -First 1
        if ($homeLine -match '^home\s*=\s*(.+)$') { $paths += Join-Path $Matches[1].Trim() 'pythonw.exe' }
    }
    return $paths
}
function Get-ExpectedArguments([string]$Kind) {
    $prefix = if ($Kind -eq 'supervisor') { @($launcher) } else { @('-m','live_backend.server') }
    return @($prefix) + @('--port',[string]$Port,'--state-dir',$StateDirectory,'--static-dir',$staticRoot,'--public-mirror',$mirror)
}
function Test-OwnedProcess([int]$ProcessId,[string]$Kind) {
    $process = Get-ProcessRecord $ProcessId
    if ($null -eq $process -or -not $process.CommandLine -or -not $process.ExecutablePath) { return $false }
    $allowed = @(Get-AllowedPythonPaths)
    if (-not ($allowed | Where-Object { [string]::Equals([IO.Path]::GetFullPath($_),[IO.Path]::GetFullPath([string]$process.ExecutablePath),[StringComparison]::OrdinalIgnoreCase) })) { return $false }
    $actual = @([SentimentCommandLine]::Split([string]$process.CommandLine))
    $expected = @(Get-ExpectedArguments $Kind)
    if ($actual.Count -ne $expected.Count + 1) { return $false }
    for ($i=0; $i -lt $expected.Count; $i++) {
        if (-not [string]::Equals([string]$actual[$i+1],[string]$expected[$i],[StringComparison]::OrdinalIgnoreCase)) { return $false }
    }
    return $true
}
function Get-Health {
    $response = $null
    try {
        $request = [Net.HttpWebRequest]::Create("http://127.0.0.1:$Port/api/health")
        $request.Proxy = $null
        $request.Timeout = 2500
        $response = $request.GetResponse()
        $reader = New-Object IO.StreamReader($response.GetResponseStream())
        try { $health = $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
        if ($health.ok -ne $true -or $health.service -cne 'sentiment-universe' -or -not $health.PSObject.Properties['project']) { return $null }
        if (-not [string]::Equals([IO.Path]::GetFullPath([string]$health.project),[IO.Path]::GetFullPath($packageRoot),[StringComparison]::OrdinalIgnoreCase)) { return $null }
        if (-not (Test-OwnedProcess (Get-RecordedPid $health) 'worker')) { return $null }
        return $health
    } catch { return $null } finally { if ($response) { $response.Close() } }
}
function Test-PortOccupied {
    $client = New-Object Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect('127.0.0.1',$Port,$null,$null)
        if (-not $async.AsyncWaitHandle.WaitOne(350)) { return $false }
        $client.EndConnect($async)
        return $true
    } catch { return $false } finally { $client.Close() }
}
function Get-SentimentStatus {
    $health = Get-Health
    $supervisor = Read-Record $supervisorPath
    $supervisorId = Get-RecordedPid $supervisor
    $ownedSupervisor = Test-OwnedProcess $supervisorId 'supervisor'
    $state = if ($health) { 'healthy' } elseif (Test-PortOccupied) { 'port_conflict_or_unhealthy' } elseif ($ownedSupervisor) { 'starting' } else { 'stopped' }
    return [ordered]@{ service='sentiment-universe'; status=$state; host='127.0.0.1'; port=$Port; project=$packageRoot; supervisorOwned=$ownedSupervisor; supervisorPid=$(if($ownedSupervisor){$supervisorId}else{$null}); workerPid=$(if($health){[int]$health.pid}else{$null}); stateDirectory=$StateDirectory }
}
function Start-Sentiment {
    if (-not (Test-Path -LiteralPath $launcher -PathType Leaf) -or -not (Test-Path -LiteralPath (Join-Path $staticRoot 'index.html') -PathType Leaf) -or -not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Sentiment package, bundled web assets or installed Python is missing. Run setup from a complete release.' }
    $status = Get-SentimentStatus
    if ($status.status -eq 'healthy' -and $status.supervisorOwned) { return $status }
    if ($status.status -eq 'port_conflict_or_unhealthy') { throw 'Port is occupied by an unverified/unhealthy listener; no process was stopped.' }
    if (-not $status.supervisorOwned) {
        $arguments = @(Get-ExpectedArguments 'supervisor' | ForEach-Object { '"' + ([string]$_).Replace('"','\"') + '"' })
        $null = Start-Process -FilePath $PythonPath -ArgumentList $arguments -WorkingDirectory $packageRoot -WindowStyle Hidden -PassThru
    }
    for ($attempt=0; $attempt -lt 45; $attempt++) {
        Start-Sleep -Milliseconds 500
        $status = Get-SentimentStatus
        if ($status.status -eq 'healthy' -and $status.supervisorOwned) { return $status }
    }
    throw 'Sentiment service did not pass its own health check; HQ and MT5 were not restarted.'
}
function Stop-Sentiment {
    $supervisor = Read-Record $supervisorPath
    $service = Read-Record $servicePath
    $supervisorId = Get-RecordedPid $supervisor
    $workerIds = @((Get-RecordedPid $supervisor 'childPid'),(Get-RecordedPid $service)) | Where-Object { $_ -gt 0 } | Select-Object -Unique
    $targets = @()
    if (Get-ProcessRecord $supervisorId) {
        if (-not (Test-OwnedProcess $supervisorId 'supervisor')) { throw 'Supervisor identity is unverified; no process was stopped.' }
        $targets += [pscustomobject]@{ Id=$supervisorId; Kind='supervisor' }
    }
    foreach ($workerId in $workerIds) {
        if (Get-ProcessRecord $workerId) {
            if (-not (Test-OwnedProcess $workerId 'worker')) { throw 'Worker identity is unverified; no process was stopped.' }
            $targets += [pscustomobject]@{ Id=$workerId; Kind='worker' }
        }
    }
    # Stop the verified supervisor first so it cannot restart/spawn a worker.
    # A child can exist in the tiny interval before childPid/service.json was
    # written. Recover only exact-command children of this verified parent.
    $ownedSupervisor = $targets | Where-Object { $_.Kind -eq 'supervisor' }
    if ($ownedSupervisor -and (Test-OwnedProcess $supervisorId 'supervisor')) {
        Stop-Process -Id $supervisorId -Force -ErrorAction Stop
        foreach ($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$supervisorId" -ErrorAction SilentlyContinue)) {
            $childId = [int]$child.ProcessId
            if (($targets.Id -notcontains $childId) -and (Test-OwnedProcess $childId 'worker')) {
                $targets += [pscustomobject]@{Id=$childId;Kind='worker'}
            }
        }
    }
    foreach ($target in @($targets | Where-Object { $_.Kind -eq 'worker' })) {
        if (Test-OwnedProcess $target.Id $target.Kind) { Stop-Process -Id $target.Id -Force -ErrorAction Stop }
    }
    return [ordered]@{service='sentiment-universe';status='stopped';stoppedCount=$targets.Count;statePreserved=$true}
}

$hash = [Security.Cryptography.SHA256]::Create()
try { $identity = [BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($StateDirectory.ToLowerInvariant()+':'+$Port))).Replace('-','').Substring(0,24) } finally { $hash.Dispose() }
$mutex = New-Object Threading.Mutex($false,('Local\MetafxSentimentControl-'+$identity))
$acquired = $false
try {
    try { $acquired = $mutex.WaitOne(5000) } catch [Threading.AbandonedMutexException] { $acquired = $true }
    if (-not $acquired) { throw 'Another sentiment lifecycle operation is running.' }
    $result = switch ($Action) {
        'Status' { Get-SentimentStatus }
        'Stop' { Stop-Sentiment }
        'Restart' { $null=Stop-Sentiment; Start-Sentiment }
        default { Start-Sentiment }
    }
    $result | ConvertTo-Json -Compress
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
} finally {
    if ($acquired) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
