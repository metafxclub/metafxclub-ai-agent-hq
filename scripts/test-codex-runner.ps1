$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot "runner\.venv\Scripts\python.exe"
$runner = Join-Path $projectRoot "runner\codex_cli_runner.py"

& $python $runner --status
