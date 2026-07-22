@echo off
setlocal
chcp 65001 >nul
call "%~dp0scripts\uninstall-hq.cmd"
exit /b %ERRORLEVEL%
