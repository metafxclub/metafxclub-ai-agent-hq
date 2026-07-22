@echo off
setlocal
set "INSTALLED_OPENER=%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\scripts\open-agent-hq.cmd"
if exist "%INSTALLED_OPENER%" (
  call "%INSTALLED_OPENER%"
) else (
  call "%~dp0scripts\open-agent-hq.cmd"
)
exit /b %errorlevel%
