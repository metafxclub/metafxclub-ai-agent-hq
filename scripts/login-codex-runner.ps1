$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$codex = Join-Path $projectRoot "runner\.venv\Lib\site-packages\codex_cli_bin\bin\codex.exe"

if (!(Test-Path -LiteralPath $codex -PathType Leaf)) {
  throw "ยังไม่พบ Codex Runner ของโปรเจกต์ กรุณารันตัวติดตั้งหรือ Repair ก่อน"
}

Write-Host "กำลังเปิดหน้า Login ทางการของ Codex สำหรับ Windows User คนนี้..." -ForegroundColor Cyan
Write-Host "ระบบจะไม่อ่านหรือคัดลอก Token, Cookie หรือไฟล์ Auth มาไว้ในโปรเจกต์" -ForegroundColor DarkGray
& $codex login
if ($LASTEXITCODE -ne 0) {
  throw "Codex Login ยังไม่สำเร็จ (รหัส $LASTEXITCODE)"
}

$readiness = Join-Path $PSScriptRoot "check-codex-readiness.ps1"
if (Test-Path -LiteralPath $readiness -PathType Leaf) {
  & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $readiness
  exit $LASTEXITCODE
}
