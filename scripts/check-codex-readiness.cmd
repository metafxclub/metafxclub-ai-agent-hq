@echo off
setlocal
chcp 65001 >nul
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-codex-readiness.ps1"
set "CHECK_EXIT=%ERRORLEVEL%"
echo.
if not "%CHECK_EXIT%"=="0" pause
exit /b %CHECK_EXIT%
