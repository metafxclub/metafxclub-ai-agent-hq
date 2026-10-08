@echo off
setlocal
chcp 65001 >nul
title อัปเดต Metafxclub AI Agent HQ

echo.
echo ============================================================
echo   อัปเดต Metafxclub AI Agent HQ จาก GitHub แบบปลอดภัย
echo ============================================================
echo.

powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0scripts\update-hq.ps1" %*
set "UPDATE_EXIT=%ERRORLEVEL%"

if "%UPDATE_EXIT%"=="2" (
  echo.
  echo Source และ Runtime อัปเดตแล้ว แต่ Google OAuth ยังต้อง Repair ^(สถานะบางส่วน 2^)
  echo ห้ามติดตั้ง Source ซ้ำ ให้ใช้ post_install.repair_command ใน install-result.json
  echo Receipt: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\install-result.json
  echo.
  if "%~1"=="" pause
  exit /b 2
)

if "%UPDATE_EXIT%"=="3" (
  echo.
  echo Source และ Runtime อัปเดตแล้ว แต่ Watchdog ยังต้อง Repair ^(สถานะบางส่วน 3^)
  echo ห้ามติดตั้ง Source ซ้ำ ให้ใช้ post_install.repair_command ใน install-result.json
  echo Receipt: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\install-result.json
  echo.
  if "%~1"=="" pause
  exit /b 3
)

if "%UPDATE_EXIT%"=="4" (
  echo.
  echo Source และ Runtime อัปเดตแล้ว แต่ Google OAuth และ Watchdog ยังต้อง Repair ^(สถานะบางส่วน 4^)
  echo ห้ามติดตั้ง Source ซ้ำ ให้ใช้ post_install.repair_command ใน install-result.json
  echo Receipt: %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\install-result.json
  echo.
  if "%~1"=="" pause
  exit /b 4
)

if not "%UPDATE_EXIT%"=="0" (
  echo.
  echo การอัปเดตหยุดก่อนเขียนทับโปรเจกต์ กรุณาอ่านข้อความด้านบน
  echo.
  if "%~1"=="" pause
  exit /b %UPDATE_EXIT%
)

echo.
echo อัปเดตและตรวจสอบสำเร็จ
exit /b 0
