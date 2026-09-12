@echo off
setlocal
chcp 65001 >nul
title Advanced/Recovery Google OAuth - Metafxclub AI Agent HQ

echo.
echo ============================================================
echo   ADVANCED/RECOVERY สำหรับผู้ดูแลระบบเท่านั้น
echo ============================================================
echo.
echo นี่ไม่ใช่ขั้นตอนปกติของนักเรียน
echo ผู้เรียนทั่วไปให้ใช้ Client กลางจาก Release แล้วกดเชื่อมบัญชี Google ใน HQ
echo ดำเนินการต่อเฉพาะผู้ดูแลที่ควบคุม Google OAuth Project ของตนเอง
echo.
echo ผู้ดูแล: ดับเบิลคลิกเพื่อเลือก OAuth Client JSON ประเภท Desktop app
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
