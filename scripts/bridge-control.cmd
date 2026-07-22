@echo off
set "BRIDGE_ACTION=%~1"
if not defined BRIDGE_ACTION set "BRIDGE_ACTION=Status"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local-bridge.ps1" -Action "%BRIDGE_ACTION%"
exit /b %errorlevel%
