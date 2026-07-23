@echo off
setlocal
chcp 65001 >nul
title ติดตั้ง Metafxclub AI Agent HQ

echo.
echo ============================================================
echo   ติดตั้ง Metafxclub AI Agent HQ สำหรับผู้ใช้ปัจจุบัน
echo ============================================================
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1" %*
set "INSTALL_EXIT=%ERRORLEVEL%"

if not "%INSTALL_EXIT%"=="0" (
  echo.
  echo การติดตั้งไม่สำเร็จ กรุณาอ่านข้อความด้านบนหรือส่งไฟล์ Log ให้ผู้สอน
  echo Log: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ-Install.log
  echo.
  pause
  exit /b %INSTALL_EXIT%
)

echo.
echo ติดตั้งสำเร็จ สามารถเปิดจาก Shortcut บน Desktop ได้แล้ว
exit /b 0
