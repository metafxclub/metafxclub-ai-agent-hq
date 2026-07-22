@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local-bridge.ps1" -Action Restart
exit /b %errorlevel%
