@echo off
call "%~dp0start-local-bridge.cmd"
if errorlevel 1 exit /b %errorlevel%
start "" "http://127.0.0.1:4186/"
exit /b 0
