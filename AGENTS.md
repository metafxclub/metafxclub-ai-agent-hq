# AGENTS.md — คู่มือสำหรับผู้ช่วยติดตั้ง Metafxclub AI Agent HQ

ไฟล์นี้เป็นข้อกำหนดสำหรับ Codex หรือ AI Agent ที่ได้รับมอบหมายให้ติดตั้ง Repository นี้บน Windows ให้นักเรียนใช้งานได้จริง เส้นทางหลักคือให้นักเรียนวาง Prompt เต็มเพียงครั้งเดียว แล้วผู้ช่วย Clone Tag ที่ล็อกไว้จาก GitHub, ดำเนินการติดตั้ง ตรวจสอบ และเปิดโปรแกรมให้ครบถ้วน โดยนักเรียนไม่ต้องดาวน์โหลด ZIP หรือกด BAT เอง

## ขอบเขตของโปรเจกต์

Metafxclub AI Agent HQ เป็น Visual Office แบบ Local-first:

- Frontend แสดงห้อง ตัวละคร Agent, Mission และ Dashboard เท่านั้น
- งานจริงทั้งหมดต้องผ่าน `backend/local-runner/`
- Bridge ต้องรับการเชื่อมต่อเฉพาะ `127.0.0.1`; ตัวติดตั้งต้องใช้ Port ที่ผู้ใช้ยืนยันโดยตรง หรือ Port 4186 ที่ยืนยันล่วงหน้าไว้ชัดเจนใน Prompt อัตโนมัติ และบันทึก Port หลัง Health check ผ่านเท่านั้น
- ค่าเริ่มต้นสำหรับนักเรียนคือ Demo/Read-only
- Telegram จริง การ Deploy การลบไฟล์ การแก้ระบบ MT4/MT5 และ Live Trading ต้องไม่ถูกเปิดใช้งานระหว่างติดตั้ง

## ขั้นตอนมาตรฐานเมื่อผู้ใช้ขอให้ติดตั้ง

### โหมดหลัก: Prompt เดียว + Git Clone

เมื่อผู้ใช้วาง `docs/prompts/install-github-google-auto-th.md` และระบุ Repository, Tag, Version, Google Client ID และ Path ของ OAuth JSON ให้ทำตามลำดับนี้โดยไม่ข้ามขั้น:

1. ยืนยันว่ากำลังทำงานบน Windows, Repository เป็น URL ทางการที่ Prompt กำหนด และมี Git กับ Python รุ่นที่รองรับ
2. ตรวจ Tag ด้วย `git ls-remote --tags` แล้ว Clone Tag ที่ล็อกไว้ลงโฟลเดอร์ใหม่ใต้ `%TEMP%` ห้ามใช้ Pull/Merge/Stash/Reset หรือลบ Repository เดิมของผู้เรียน
3. ตรวจ `origin`, Commit ของ Tag, worktree ที่สะอาด และไฟล์ `VERSION` ให้ตรงกับ Prompt หากไม่ตรงให้หยุด
4. อ่าน `README.md`, `STUDENT-QUICKSTART-TH.md` และ `docs/research-sheet-hub-setup-th.md` จาก Source ที่ตรวจแล้ว
5. ตรวจว่ามี `1-INSTALL-HQ.bat` และ `installer/install.ps1` อยู่จริง หากขาดไฟล์ใด ให้ถือว่า Source ไม่สมบูรณ์และหยุดอย่างปลอดภัย
6. ก่อนหยุด Bridge เดิม คัดลอกไฟล์ หรือสร้าง Runtime ให้เรียก `installer/install.ps1 -ListAvailableEndpoints` ซึ่งเป็นการตรวจแบบอ่านอย่างเดียว
7. ถ้า Prompt ยืนยัน `127.0.0.1:4186` ล่วงหน้าแล้ว ให้ตรวจว่า candidate นี้มี `available: true` และส่ง `-Port 4186 -EndpointConfirmed` ได้โดยไม่ถามซ้ำ หากไม่ว่างให้หยุด ห้ามสลับ Port หรือปิด Process อื่นเอง
8. เรียก `installer/install.ps1` โดยตรงเพียงรอบเดียว พร้อม Google JSON Path และ Expected Client ID ตาม Prompt ห้ามสร้างขั้นตอน `pip install`, คัดลอก `.venv` หรือนำเข้า Credential เอง
9. ตรวจสถานะด้วย `scripts/status-local-bridge.cmd` จาก Runtime ที่ติดตั้งจริง
10. อ่าน `health_url` จาก `data/runtime/bridge-endpoint.json` และตรวจว่า Health ส่ง `ok: true`, `status: "ready"`, Host/Port ตรงกับไฟล์
11. ตรวจหน้าเว็บ, Google Client status, Scheduled Task, Codex login และ Rate Limit ตามเกณฑ์ใน Prompt
12. เมื่อ Health พร้อมแล้ว ให้เปิด URL ที่บันทึกไว้ ห้ามกด Login/เลือกบัญชี/อนุญาต Google แทนผู้ใช้
13. การล้าง Source ชั่วคราวทำได้เฉพาะโฟลเดอร์ที่ผู้ช่วยสร้างและตรวจ Absolute path แล้วเท่านั้น เป็น Best-effort และห้ามทำให้ Runtime ที่ Health ผ่านแล้วถูก Rollback

### โหมดสำรอง: ผู้ใช้เลือกติดตั้ง ZIP เอง

ใช้เฉพาะเมื่อผู้ใช้ขอวิธี Manual หรือส่ง GitHub Release Asset มาโดยตรง: ตรวจ Release ที่ล็อกเวอร์ชันและ SHA-256, แตก ZIP แล้วเรียก `1-INSTALL-HQ.bat` หากยังไม่มีการยืนยัน Endpoint ล่วงหน้า ให้แสดง URL ที่ `available: true` จำนวน 3 ตัวเลือกและรอให้ผู้ใช้เลือก ห้ามใช้ Branch `main`, URL `latest` หรือ Source snapshot แทน Release แบบเงียบ ๆ

คำสั่งอ้างอิงเมื่ออยู่ในโฟลเดอร์ที่ติดตั้งแล้ว:

```powershell
& ".\scripts\status-local-bridge.cmd"
$endpoint = Get-Content ".\data\runtime\bridge-endpoint.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$health = Invoke-RestMethod -Uri $endpoint.health_url -TimeoutSec 10
$health | Select-Object ok, status, agentCount, agentRosterComplete, version
& ".\scripts\check-codex-readiness.cmd"
& ".\Open Metafx Agent HQ.cmd"
```

ในโหมด Manual หาก Runtime เดิมติดตั้งอยู่แล้วแต่ Health ไม่ผ่าน จึงใช้ `scripts/repair-hq.cmd` ได้หนึ่งครั้งแล้วตรวจสถานะใหม่ สำหรับ Prompt อัตโนมัติ ให้หยุดและรายงานสาเหตุก่อน ห้ามซ่อม/ติดตั้งซ้ำแบบเงียบ ๆ และห้ามฆ่า Process ที่ไม่สามารถยืนยันได้ว่าเป็น HQ Bridge เพียงเพราะ Process นั้นใช้ Port เดียวกัน

## เกณฑ์ว่าติดตั้งสำเร็จ

ห้ามรายงานว่า “พร้อมใช้งาน” จนกว่าจะมีหลักฐานครบทุกข้อ:

- `installer/install.ps1` หรือ `1-INSTALL-HQ.bat` ตามโหมดที่ผู้ใช้เลือกจบโดยไม่มีข้อผิดพลาด
- `scripts/status-local-bridge.cmd` ยืนยันว่า HQ Bridge ทำงาน
- `/api/health` ตอบกลับโดยมี `ok: true` และ `status: "ready"`
- `agentRosterComplete: true` และจำนวน Agent ตรงตาม Contract
- URL ใน `data/runtime/bridge-endpoint.json` เปิดได้
- URL/Port ตรงกับค่าที่ผู้ใช้ยืนยัน
- มีรายงานสถานะ Codex และ Rate Limit ของบัญชีเครื่องนี้ หรือแจ้ง `auth_required`/`config_error` อย่างชัดเจน
- `data/runtime/install-result.json` มีเฉพาะสถานะที่อนุญาตและไม่เก็บข้อมูลระบุตัวบัญชี
- ไม่มีการเปิด Live Trading, Telegram จริง หรือ Real execution ใดระหว่างการติดตั้ง

รายงานผลให้นักเรียนด้วยภาษาง่าย ๆ โดยระบุเวอร์ชัน ตำแหน่งโปรแกรม สถานะ Bridge, Health และลิงก์เปิดใช้งาน หากยังมี `auth_required` ของ Codex ให้แยกเป็น “ขั้นตอน Login บัญชีของนักเรียน” ไม่ควรกล่าวว่าการติดตั้ง HQ ล้มเหลวหากส่วน Demo และ Health พร้อมแล้ว

## ข้อกำหนดด้านความปลอดภัย

- ห้ามอ่าน คัดลอก แสดง หรือบันทึก Token, API key, Cookie, Broker password, Telegram token และข้อมูล Authentication
- ห้ามนำ `%USERPROFILE%\.codex`, `.env`, `.venv`, `data/runtime/`, Log หรือ Memory จากเครื่องผู้สอนไปติดตั้งในเครื่องนักเรียน
- นักเรียนต้อง Login Codex ผ่านช่องทางทางการด้วยบัญชีของตนเอง Quota และ Rate Limit ต้องเป็นของบัญชีนักเรียน ห้าม Login ให้อัตโนมัติหรือคัดลอก Auth จากเครื่องอื่น
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
