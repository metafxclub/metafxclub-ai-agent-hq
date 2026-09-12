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

เมื่อผู้ใช้วาง `docs/prompts/install-github-google-auto-th.md` ซึ่งล็อก Repository, Tag และ Version ไว้แล้ว ให้ทำตามลำดับนี้โดยไม่ข้ามขั้น เส้นทางหลักต้องใช้ Google OAuth native/installed-app client configuration กลางที่บรรจุอยู่ใน Release Asset นักเรียนไม่ต้องสร้าง Google Cloud Project/OAuth Client, เพิ่ม Test users, ดาวน์โหลด JSON หรือแก้ Client ID ไฟล์ Client จริงถูก GitHub Actions inject จาก Release secrets ตอน build Asset และต้องไม่ถูก commit ลง public Git tree; ค่า `client_id`/`client_secret` ของ installed app เป็น app metadata ที่แจกพร้อมโปรแกรม ไม่ใช่ Credential ของบัญชีผู้ใช้:

1. ยืนยันว่ากำลังทำงานบน Windows 10/11 แบบ 64-bit และ Repository เป็น URL ทางการที่ Prompt กำหนด จากนั้นตรวจและใช้ Git/Python เดิมก่อน หาก Git ใช้งานไม่ได้หรือไม่มี Python 3.10-3.14 แบบ 64-bit จึง Bootstrap เฉพาะตัวที่ขาดตาม Package ID, Source, Publisher, user scope และคำสั่ง WinGet ที่ล็อกไว้ใน Prompt ห้ามติดตั้งซ้ำ อัปเกรด/ถอนของเดิม ใช้ Source อื่น ขอสิทธิ์ Administrator หรือเปลี่ยน PATH ถาวร ต้องตรวจ Path, Version และ Architecture ซ้ำก่อนทำข้อ 2
2. ตรวจ Tag ด้วย `git ls-remote --tags` แล้ว Clone Tag ที่ล็อกไว้ลงโฟลเดอร์ใหม่ใต้ `%TEMP%` ห้ามใช้ Pull/Merge/Stash/Reset หรือลบ Repository เดิมของผู้เรียน
3. ตรวจ `origin`, Commit ของ Tag, worktree ที่สะอาด และไฟล์ `VERSION` ให้ตรงกับ Prompt หากไม่ตรงให้หยุด จากนั้นดาวน์โหลด Release ZIP และ `.sha256` ของ Tag เดียวกันจาก GitHub Release ทางการ ตรวจ hash ให้ตรง แล้ว extract เฉพาะ `backend/local-runner/google_oauth_native_client.txt` เข้า SOURCE_DIR หลังยืนยันว่า path นี้ถูก `.gitignore` และ `git status --porcelain` ยังว่าง ห้าม extract หรือใช้โค้ดส่วนอื่นจาก ZIP ทับ Git tree และห้ามแสดงค่า Client เต็ม
4. อ่าน `README.md`, `STUDENT-QUICKSTART-TH.md` และ `docs/research-sheet-hub-setup-th.md` จาก Source ที่ตรวจแล้ว
5. ตรวจว่ามี `1-INSTALL-HQ.bat` และ `installer/install.ps1` อยู่จริง หากขาดไฟล์ใด ให้ถือว่า Source ไม่สมบูรณ์และหยุดอย่างปลอดภัย
6. ก่อนหยุด Bridge เดิม คัดลอกไฟล์ หรือสร้าง Runtime ให้เรียก `installer/install.ps1 -ListAvailableEndpoints` ซึ่งเป็นการตรวจแบบอ่านอย่างเดียว
7. ถ้า Prompt ยืนยัน `127.0.0.1:4186` ล่วงหน้าแล้ว ให้ตรวจว่า candidate นี้มี `available: true` และส่ง `-Port 4186 -EndpointConfirmed` ได้โดยไม่ถามซ้ำ หากไม่ว่างให้หยุด ห้ามสลับ Port หรือปิด Process อื่นเอง
8. เรียก `installer/install.ps1` โดยตรงเพียงรอบเดียวโดยไม่ส่ง `GoogleClientJsonPath` หรือ `ExpectedGoogleClientId`; Installer ต้องตรวจและใช้ native-app client configuration กลางจาก `backend/local-runner/google_oauth_native_client.txt` เอง ห้ามสร้างขั้นตอน `pip install`, คัดลอก `.venv` หรือนำเข้า Credential เอง หาก Client กลางไม่พร้อมให้หยุดและรายงานว่า Release ไม่สมบูรณ์ ห้ามขอ JSON หรือ Client ID จากนักเรียนมาแก้แบบเงียบ ๆ
9. ตรวจสถานะด้วย `scripts/status-local-bridge.cmd` จาก Runtime ที่ติดตั้งจริง
10. อ่าน `health_url` จาก `data/runtime/bridge-endpoint.json` และตรวจว่า Health ส่ง `ok: true`, `status: "ready"`, Host/Port ตรงกับไฟล์
11. ตรวจหน้าเว็บ, Google Client status ว่า `clientConfigured=true` และผลติดตั้งเป็น `ready_central` จาก `central_release`, Scheduled Task, Codex login และ Rate Limit ตามเกณฑ์ใน Prompt โดยไม่แสดงค่า Client เต็ม
12. เมื่อ Health พร้อมแล้ว ให้เปิด URL ที่บันทึกไว้ ห้ามกด Login/เลือกบัญชี/อนุญาต Google แทนผู้ใช้
13. การล้าง Source ชั่วคราวทำได้เฉพาะโฟลเดอร์ที่ผู้ช่วยสร้างและตรวจ Absolute path แล้วเท่านั้น เป็น Best-effort และห้ามทำให้ Runtime ที่ Health ผ่านแล้วถูก Rollback

### โหมดสำรอง: ผู้ใช้เลือกติดตั้ง ZIP เอง

ใช้เฉพาะเมื่อผู้ใช้ขอวิธี Manual หรือส่ง GitHub Release Asset มาโดยตรง: ตรวจ Release ที่ล็อกเวอร์ชันและ SHA-256, แตก ZIP แล้วเรียก `1-INSTALL-HQ.bat` หากยังไม่มีการยืนยัน Endpoint ล่วงหน้า ให้แสดง URL ที่ `available: true` จำนวน 3 ตัวเลือกและรอให้ผู้ใช้เลือก ห้ามใช้ Branch `main`, URL `latest` หรือ Source snapshot แทน Release แบบเงียบ ๆ

`2-SETUP-GOOGLE-HQ.bat` และการนำเข้า Desktop OAuth JSON ยังคงมีไว้เฉพาะ **Advanced/Recovery custom override** เมื่อเจ้าของระบบตั้งใจใช้ OAuth Project ของตนเองหรือได้รับคำแนะนำให้กู้การตั้งค่าเท่านั้น ไม่ใช่ขั้นตอนห้องเรียนปกติ ผู้ใช้ Advanced ต้องใช้ JSON ของ Project ที่ตนควบคุมเอง ห้ามใช้ไฟล์ของผู้สอนหรือเพื่อน และการ Override ต้องไม่เปิดเผยหรือเปลี่ยน Client ID กลางที่มากับ Release

คำสั่งอ้างอิงเมื่ออยู่ในโฟลเดอร์ที่ติดตั้งแล้ว:

```powershell
& ".\scripts\status-local-bridge.cmd"
$endpoint = Get-Content ".\data\runtime\bridge-endpoint.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$health = Invoke-RestMethod -Uri $endpoint.health_url -TimeoutSec 10
$health | Select-Object ok, status, agentCount, agentRosterComplete, version
& ".\scripts\check-codex-readiness.cmd"
& ".\Open Metafx Agent HQ.cmd"
```

ในโหมด Manual หาก Runtime เดิมติดตั้งอยู่แล้วแต่ Health ไม่ผ่าน จึงใช้ `scripts/repair-hq.cmd` ได้หนึ่งครั้งแล้วตรวจสถานะใหม่ สำหรับ Prompt อัตโนมัติ กฎห้ามซ่อม/ติดตั้งซ้ำแบบเงียบ ๆ ในข้อนี้หมายถึง Runtime ของ Agent HQ ไม่ใช่การ Bootstrap Git/Python ที่ขาดตามข้อ 1; หาก Runtime ผิดปกติให้หยุดและรายงานสาเหตุก่อน และห้ามฆ่า Process ที่ไม่สามารถยืนยันได้ว่าเป็น HQ Bridge เพียงเพราะ Process นั้นใช้ Port เดียวกัน

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
- เส้นทางหลักห้ามขอให้นักเรียนสร้าง/ส่ง OAuth JSON หรือกรอก Client ID/Client Secret และห้ามแสดงค่า Client กลางแบบเต็ม; ไฟล์ Client จริงต้องมาจาก GitHub Actions build/release injection เท่านั้นและห้าม commit ลง public Git tree ส่วน access token, refresh token และ Credential ของบัญชีผู้ใช้ต้องไม่เข้า Repository, Frontend, Report หรือ Log และนักเรียนต้องทำเองเฉพาะกด **เชื่อมบัญชี Google**, เลือกบัญชี และยืนยัน Consent ใน System Browser
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
