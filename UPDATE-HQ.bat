@echo off
setlocal
chcp 65001 >nul
title อัปเดต Metafxclub AI Agent HQ

echo.
echo ============================================================
echo   อัปเดต Metafxclub AI Agent HQ จาก GitHub แบบปลอดภัย
echo ============================================================
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update-hq.ps1" %*
set "UPDATE_EXIT=%ERRORLEVEL%"

if not "%UPDATE_EXIT%"=="0" (
  echo.
  echo การอัปเดตหยุดก่อนเขียนทับโปรเจกต์ กรุณาอ่านข้อความด้านบน
  echo.
  pause
  exit /b %UPDATE_EXIT%
)

echo.
echo อัปเดตและตรวจสอบสำเร็จ
exit /b 0
