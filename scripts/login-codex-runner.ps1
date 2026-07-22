$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$codex = Join-Path $projectRoot "runner\.venv\Lib\site-packages\codex_cli_bin\bin\codex.exe"

if (!(Test-Path $codex)) {
  throw "Project Codex runner is missing. Ask Codex to run runner setup first."
}

Write-Host "Opening Codex login for the project runner..."
Write-Host "This uses the project runner, not the WindowsApps alias."
& $codex login
