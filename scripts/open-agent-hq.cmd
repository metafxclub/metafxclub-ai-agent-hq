@echo off
setlocal
call "%~dp0start-local-bridge.cmd"
if errorlevel 1 exit /b %errorlevel%
set "HQ_ENDPOINT_FILE=%~dp0..\data\runtime\bridge-endpoint.json"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=$env:HQ_ENDPOINT_FILE; if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw 'ไม่พบ endpoint ที่ผ่าน Health check' }; $raw=Get-Content -LiteralPath $p -Raw -Encoding UTF8; $e=ConvertFrom-Json -InputObject $raw; $port=[int]$e.port; if ([string]$e.host -cne '127.0.0.1' -or $port -lt 1024 -or $port -gt 65535) { throw 'endpoint ไม่ใช่ Local loopback ที่อนุญาต' }; Start-Process ('http://127.0.0.1:{0}/' -f $port)"
exit /b %errorlevel%
