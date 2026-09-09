[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$PythonPath,

  [string]$LogPath = ""
)

$ErrorActionPreference = "Stop"

$resolvedPython = [IO.Path]::GetFullPath($PythonPath)
if (-not (Test-Path -LiteralPath $resolvedPython -PathType Leaf)) {
  throw "Regression Python executable is missing."
}

if ([string]::IsNullOrWhiteSpace($LogPath)) {
  $logRoot = if ([string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
    [IO.Path]::GetTempPath()
  }
  else {
    $env:RUNNER_TEMP
  }
  $LogPath = Join-Path $logRoot "metafxclub-regression-suite.log"
}

$resolvedLog = [IO.Path]::GetFullPath($LogPath)
$logDirectory = Split-Path -Parent $resolvedLog
if (-not (Test-Path -LiteralPath $logDirectory -PathType Container)) {
  New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
}

& $resolvedPython -m unittest discover -s tests -p "test_*.py" -v 2>&1 |
  Tee-Object -FilePath $resolvedLog
$testExitCode = $LASTEXITCODE

if ($testExitCode -eq 0) {
  return
}

# GitHub-hosted logs require a signed-in account. Publish only test identifiers
# and the aggregate result as a safe check annotation so a classroom release
# failure remains diagnosable without exposing traceback data or local paths.
$safeFailureLines = @(
  Get-Content -LiteralPath $resolvedLog -Encoding UTF8 |
    Where-Object {
      $_ -match "^(FAIL|ERROR):\s+test_[A-Za-z0-9_]+\s+\([A-Za-z0-9_.]+\)$" -or
      $_ -match "^FAILED\s+\((failures|errors)="
    } |
    Select-Object -First 24
)

$diagnostic = if ($safeFailureLines.Count -gt 0) {
  $safeFailureLines -join " | "
}
else {
  "Regression process exited nonzero before unittest emitted a safe failure identifier."
}

if ($diagnostic.Length -gt 3000) {
  $diagnostic = $diagnostic.Substring(0, 3000)
}

if ($env:GITHUB_ACTIONS -eq "true") {
  $escaped = $diagnostic.Replace("%", "%25").Replace("`r", "%0D").Replace("`n", "%0A")
  Write-Host "::error title=Regression suite failed::$escaped"
}

throw "Regression suite failed with exit code $testExitCode."
