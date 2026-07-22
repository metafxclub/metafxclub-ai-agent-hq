# AGENTS.md — คู่มือสำหรับผู้ช่วยติดตั้ง Metafxclub AI Agent HQ

ไฟล์นี้เป็นข้อกำหนดสำหรับ Codex หรือ AI Agent ที่ได้รับมอบหมายให้ติดตั้ง Repository นี้บน Windows ให้นักเรียนใช้งานได้จริง เป้าหมายคือให้ผู้ใช้ส่งลิงก์ GitHub Release เพียงครั้งเดียว แล้วผู้ช่วยดำเนินการติดตั้ง ตรวจสอบ และเปิดโปรแกรมให้ครบถ้วน

## ขอบเขตของโปรเจกต์

Metafxclub AI Agent HQ เป็น Visual Office แบบ Local-first:

- Frontend แสดงห้อง ตัวละคร Agent, Mission และ Dashboard เท่านั้น
- งานจริงทั้งหมดต้องผ่าน `backend/local-runner/`
- Bridge ต้องรับการเชื่อมต่อเฉพาะ `127.0.0.1:4186`
- ค่าเริ่มต้นสำหรับนักเรียนคือ Demo/Read-only
- Telegram จริง การ Deploy การลบไฟล์ การแก้ระบบ MT4/MT5 และ Live Trading ต้องไม่ถูกเปิดใช้งานระหว่างติดตั้ง

## ขั้นตอนมาตรฐานเมื่อผู้ใช้ขอให้ติดตั้ง

เมื่อผู้ใช้ส่งลิงก์ GitHub และขอให้ติดตั้ง ให้ทำตามลำดับนี้โดยไม่ข้ามขั้น:

1. ยืนยันว่ากำลังทำงานบน Windows และลิงก์มาจาก Repository/Release ของ Metafxclub ที่ผู้ใช้ระบุ
2. หากได้รับลิงก์ Repository ให้เลือก GitHub Release ที่เผยแพร่แล้วและล็อกเวอร์ชัน หากไม่มี Release ห้ามเดาไฟล์ติดตั้งจาก Source snapshot ให้แจ้งผู้ใช้
3. ดาวน์โหลด Asset สำหรับ Windows จาก Release และตรวจสอบค่า SHA-256 หาก Release มีไฟล์ Checksum
4. แตกไฟล์ไปยังโฟลเดอร์ชั่วคราวที่ผู้ใช้เขียนได้ ห้ามรันโดยตรงจากใน ZIP
5. อ่าน `README.md` และ `STUDENT-QUICKSTART-TH.md`
6. ตรวจว่ามี `1-INSTALL-HQ.bat` และ `installer/install.ps1` อยู่จริง หากขาดไฟล์ใด ให้ถือว่า Release ไม่สมบูรณ์และหยุดอย่างปลอดภัย
7. เรียก `1-INSTALL-HQ.bat` จากโฟลเดอร์รากของชุดติดตั้ง ให้สคริปต์เป็นผู้เลือกตำแหน่งติดตั้งและสร้าง Runtime ที่จำเป็น ห้ามสร้างขั้นตอน `pip install` หรือคัดลอก `.venv` เอง
8. ตรวจสถานะด้วย `scripts/status-local-bridge.cmd`
9. ตรวจ Health endpoint ที่ `http://127.0.0.1:4186/api/health`
10. เมื่อ Health พร้อมแล้ว ให้เปิดด้วย `Open Metafx Agent HQ.cmd` และยืนยันหน้า `http://127.0.0.1:4186/`

คำสั่งอ้างอิงเมื่ออยู่ในโฟลเดอร์ที่ติดตั้งแล้ว:

```powershell
& ".\scripts\status-local-bridge.cmd"
$health = Invoke-RestMethod -Uri "http://127.0.0.1:4186/api/health" -TimeoutSec 10
$health | Select-Object ok, status, agentCount, agentRosterComplete, version
& ".\Open Metafx Agent HQ.cmd"
```

หากการติดตั้งหรือ Health check ไม่ผ่าน ให้ใช้ `scripts/repair-hq.cmd` หนึ่งครั้ง แล้วตรวจสถานะและ Health ใหม่ ห้ามฆ่า Process ที่ไม่สามารถยืนยันได้ว่าเป็น HQ Bridge เพียงเพราะ Process นั้นใช้ Port 4186

## เกณฑ์ว่าติดตั้งสำเร็จ

ห้ามรายงานว่า “พร้อมใช้งาน” จนกว่าจะมีหลักฐานครบทุกข้อ:

- `1-INSTALL-HQ.bat` จบโดยไม่มีข้อผิดพลาด
- `scripts/status-local-bridge.cmd` ยืนยันว่า HQ Bridge ทำงาน
- `/api/health` ตอบกลับโดยมี `ok: true` และ `status: "ready"`
- `agentRosterComplete: true` และจำนวน Agent ตรงตาม Contract
- หน้า `http://127.0.0.1:4186/` เปิดได้
- ไม่มีการเปิด Live Trading, Telegram จริง หรือ Real execution ใดระหว่างการติดตั้ง

รายงานผลให้นักเรียนด้วยภาษาง่าย ๆ โดยระบุเวอร์ชัน ตำแหน่งโปรแกรม สถานะ Bridge, Health และลิงก์เปิดใช้งาน หากยังมี `auth_required` ของ Codex ให้แยกเป็น “ขั้นตอน Login บัญชีของนักเรียน” ไม่ควรกล่าวว่าการติดตั้ง HQ ล้มเหลวหากส่วน Demo และ Health พร้อมแล้ว

## ข้อกำหนดด้านความปลอดภัย

- ห้ามอ่าน คัดลอก แสดง หรือบันทึก Token, API key, Cookie, Broker password, Telegram token และข้อมูล Authentication
- ห้ามนำ `%USERPROFILE%\.codex`, `.env`, `.venv`, `data/runtime/`, Log หรือ Memory จากเครื่องผู้สอนไปติดตั้งในเครื่องนักเรียน
- นักเรียนต้อง Login Codex ผ่านช่องทางทางการด้วยบัญชีของตนเอง Quota และ Rate Limit ต้องเป็นของบัญชีนักเรียน
- Frontend ส่งได้เฉพาะ Intent และห้ามถือ Secret
- ห้ามเปลี่ยน Bridge ให้ออกไปฟังบน LAN หรือ Public network
- ห้ามปิด Approval Gate, Risk Guard, Budget, Timeout, Audit log หรือ Kill switch
- ห้ามเปิด Live Trading อัตโนมัติ แม้ผู้ใช้จะขอให้ “ติดตั้งให้พร้อมใช้” เพราะคำดังกล่าวหมายถึงพร้อมใช้ในโหมด Demo/Read-only เท่านั้น
- หาก Windows แสดงคำเตือนด้านความปลอดภัย ให้ตรวจแหล่งที่มาและ Checksum ก่อน ห้ามแนะนำให้ข้ามคำเตือนจากไฟล์ที่ตรวจสอบไม่ได้

## กติกาสำหรับการแก้โค้ด

- อ่านโครงสร้างและ Contract ก่อนแก้
- รักษาไฟล์และข้อมูลเดิมของผู้ใช้ ห้ามลบหรือย้ายโดยไม่จำเป็น
- Real tool call ทุกครั้งต้องมี Mission ID, Owner agent, Status, Audit log และ Report routing
- การเปลี่ยน Installer ต้องคง Entry point เหล่านี้: `1-INSTALL-HQ.bat`, `installer/install.ps1`, `Open Metafx Agent HQ.cmd`, `scripts/repair-hq.cmd` และ `scripts/status-local-bridge.cmd`
- หลังแก้ต้องรันชุดทดสอบที่ Repository จัดเตรียมไว้ และตรวจ `/api/health` โดยไม่เรียก Real tool

