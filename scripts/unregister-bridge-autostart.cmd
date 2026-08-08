@echo off
setlocal
set "INSTALLED_SCRIPT=%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\scripts\unregister-bridge-autostart.ps1"
if exist "%INSTALLED_SCRIPT%" (
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%INSTALLED_SCRIPT%" %*
) else (
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0unregister-bridge-autostart.ps1" %*
)
exit /b %ERRORLEVEL%
exit /b %errorlevel%
