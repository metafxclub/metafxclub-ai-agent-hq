@echo off
setlocal
chcp 65001 >nul
title ตั้งค่า Google Sheets - Metafxclub AI Agent HQ

echo.
echo ============================================================
echo   ตั้งค่า Google Sheets ครั้งเดียวสำหรับ Windows User นี้
echo ============================================================
echo.
echo ดับเบิลคลิกเพื่อเลือก OAuth Client JSON ประเภท Desktop app
echo หรือลากไฟล์ JSON มาวางบน BAT นี้ได้
echo JSON และ Client Secret จะไม่ผ่าน Browser
echo.

if "%~1"=="" (
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-google-oauth.ps1"
) else (
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-google-oauth.ps1" -ClientJsonPath "%~1"
)
set "SETUP_EXIT=%ERRORLEVEL%"

if not "%SETUP_EXIT%"=="0" (
  echo.
  echo ตั้งค่า Google ไม่สำเร็จ กรุณาอ่านข้อความด้านบนแล้วลองใหม่
  echo.
  pause
  exit /b %SETUP_EXIT%
)

echo.
echo ตั้งค่าเสร็จแล้ว ให้กด "เชื่อมบัญชี Google ครั้งเดียว" ใน Agent HQ
exit /b 0
