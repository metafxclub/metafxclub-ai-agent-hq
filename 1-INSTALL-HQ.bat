@echo off
setlocal
chcp 65001 >nul
title ติดตั้ง Metafxclub AI Agent HQ

echo.
echo ============================================================
echo   ติดตั้ง Metafxclub AI Agent HQ สำหรับผู้ใช้ปัจจุบัน
echo ============================================================
echo.

if "%~1"=="" (
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1" -Port 4186 -EndpointConfirmed
) else (
  powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1" %*
)
set "INSTALL_EXIT=%ERRORLEVEL%"

if "%INSTALL_EXIT%"=="2" (
  echo.
  echo Runtime และ Health พร้อมใช้งานแล้ว แต่ Google OAuth ยังต้องซ่อม ^(สถานะบางส่วน 2^)
  echo ไม่ต้องติดตั้ง Source ซ้ำ กรุณาอ่านข้อความ Repair ด้านบนหรือติดต่อผู้สอน
  echo Log: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ-Install.log
  echo.
  if "%~1"=="" pause
  exit /b 2
)

if "%INSTALL_EXIT%"=="3" (
  echo.
  echo Runtime และ Health พร้อมใช้งานแล้ว แต่ Watchdog หลัง Login ยังต้องซ่อม ^(สถานะบางส่วน 3^)
  echo ไม่ต้องติดตั้ง Source ซ้ำ กรุณารันคำสั่ง Repair Watchdog ที่แสดงด้านบน
  echo Log: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ-Install.log
  echo.
  if "%~1"=="" pause
  exit /b 3
)

if "%INSTALL_EXIT%"=="4" (
  echo.
  echo Runtime และ Health พร้อมใช้งานแล้ว แต่ Google OAuth และ Watchdog ยังต้องซ่อม ^(สถานะบางส่วน 4^)
  echo ไม่ต้องติดตั้ง Source ซ้ำ กรุณาทำตามข้อความ Repair ด้านบนหรือติดต่อผู้สอน
  echo Log: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ-Install.log
  echo.
  if "%~1"=="" pause
  exit /b 4
)

if not "%INSTALL_EXIT%"=="0" (
  echo.
  echo การติดตั้งไม่สำเร็จ กรุณาอ่านข้อความด้านบนหรือส่งไฟล์ Log ให้ผู้สอน
  echo Log: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ-Install.log
  echo.
  if "%~1"=="" pause
  exit /b %INSTALL_EXIT%
)

echo.
echo ติดตั้งสำเร็จ สามารถเปิดจาก Shortcut บน Desktop ได้แล้ว
exit /b 0
