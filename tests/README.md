# แผนที่ชุดทดสอบ

ชุดทดสอบใช้ Python `unittest` และเรียก Node.js สำหรับพฤติกรรม Frontend บางส่วน ไฟล์ `test_*.py` อยู่ระดับเดียวกันเพื่อรักษา Test discovery, Import และรายการไฟล์ของ Installer ส่วนข้อมูลจำลองอยู่ใน `fixtures/`

| หมวด | กลุ่มไฟล์ |
|---|---|
| Runtime, HTTP และวงจรชีวิต Bridge | `test_runtime_integrity.py`, `test_bridge_*.py`, `test_scheduler_*.py` |
| Full Agent และ Codex | `test_full_agent_*.py`, `test_codex_*.py`, `test_automation_quota_policy.py` |
| สภา AI Trade และการวิเคราะห์ | `test_ai_trade_council_*.py`, `test_council_analysis_module.py` |
| EA Factory และ Optimization | `test_ea_factory_*.py`, `test_ea_optimization_lab_*.py`, `test_ea_strategy_brief.py` |
| Research และ Radar | `test_ea_research_*.py`, `test_deep_research_*.py`, `test_radar_*.py` |
| Google Sheet และ OAuth | `test_research_sheet_*.py`, `test_google_*.py` |
| MetaTrader และ Trade Gateway | `test_mt4_*.py`, `test_mt5_*.py`, `test_metatrader_*.py`, `test_global_metatrader_*.py`, `test_trade_gateway_cross_platform_contract.py` |
| Dashboard, Frontend และประชุม Agent | `test_dashboard_*.py`, `test_frontend_*.py`, `test_mission_*.py`, `test_meeting_*.py`, `test_interactive_meeting_sessions_backend.py` |
| ข้อมูลข่าว, OHLC และอุปกรณ์ | `test_*news*.py`, `test_ohlc_*.py`, `test_equipment_*.py` |
| Release, Installer และข้อมูลที่ห้ามแจกจ่าย | `test_release_*.py`, `release_secret_scan.py` |

## รันชุดทดสอบ

รันจากราก Repository หลังเตรียม Dependency ตามคู่มือแล้ว:

```powershell
.\scripts\run-regression-suite.ps1 -PythonPath .\runner\.venv\Scripts\python.exe
```

ตัวอย่างทดสอบเฉพาะส่วน:

```powershell
.\runner\.venv\Scripts\python.exe -m unittest tests.test_frontend_module_boundaries tests.test_council_analysis_module
```

Tests ที่สร้างหน้าต่าง Windows จำลองทั้ง 10 รายการเป็น opt-in เพราะเปิดหน้าต่างและบางรายการดึงโฟกัสหรือส่งปุ่มกด การรันตามปกติจะข้ามกลุ่มนี้ หากตั้งใจทดสอบบนหน้าจอ ให้ตั้ง `METAFX_RUN_INTERACTIVE_UI_TESTS=1` เฉพาะ session ที่ใช้ทดสอบและหยุดใช้งานหน้าจอชั่วคราว ไม่ตั้งค่านี้ถาวร

ผลที่ข้ามเพราะต้องใช้ MetaEditor หรือ Windows UI จริงต้องรายงานตามผลรัน ห้ามนับเป็นหลักฐานว่า Compile หรือการใช้งานบนหน้าจอผ่านแล้ว

`test_google_sheet_credential_binding.py` ใช้ข้อมูลจำลองเพื่อตรวจการผูกบัญชีและการปิดกั้น Request ที่ไม่ตรงบัญชี เป็น Source ของชุดทดสอบที่ต้องเก็บไว้ ไม่ใช่ไฟล์ Credential ของผู้ใช้
