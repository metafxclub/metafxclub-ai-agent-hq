# Metafxclub AI Agent HQ

AI Agent Visual Office แบบ Local สำหรับจัดการ Mission, Agent และ Dashboard ของงาน Forex VPS, EA, Backtest, Optimization, Codex/MCP และระบบ Automation โดยข้อมูลลับและการเรียกเครื่องมือจริงจะอยู่หลัง Local Bridge เท่านั้น

โปรแกรมเริ่มต้นในโหมด **Demo/Read-only** จึงไม่ส่ง Telegram จริง ไม่ Deploy และไม่ส่งคำสั่ง Live Trading ระหว่างติดตั้ง

## สิ่งที่ต้องมีก่อนติดตั้งบน Windows

- Windows 10 หรือ 11 แบบ 64-bit และอินเทอร์เน็ตสำหรับติดตั้ง Dependency ที่ล็อกเวอร์ชันไว้
- บัญชี Codex ของผู้เรียนเอง (Login ภายหลังได้; HQ และ Health ยังเปิดตรวจได้แม้ Codex ยังไม่ Login)

สำหรับเส้นทางหลักแบบ Prompt/Codex ผู้เรียน **ไม่ต้องติดตั้ง Git หรือ Python ล่วงหน้า** Prompt จะตรวจของเดิมก่อน หากพบ Git ที่ใช้งานได้และ Python 3.10-3.14 แบบ 64-bit จะใช้ของเดิมโดยไม่ติดตั้งซ้ำหรืออัปเกรด หากขาดจริงจึงติดตั้งแพ็กเกจทางการที่ล็อก ID ไว้ผ่าน WinGet แบบ current-user แล้วตรวจซ้ำก่อน Clone ส่วนผู้ที่เลือกติดตั้ง ZIP ด้วยตนเองยังต้องมี Python รุ่นที่รองรับตามหัวข้อ Manual ด้านล่าง

ตัวติดตั้งจะลง Codex Python SDK และ Codex CLI จาก `requirements-runner.txt` เป็นรุ่นเดียวกัน พร้อมตรวจ SHA-256 และ `pip check` ห้ามเปลี่ยนเฉพาะไฟล์ `codex.exe` แยกจาก SDK เพราะการอ่าน Rate Limit ผ่าน app-server และการรันงานจริงต้องใช้ protocol รุ่นเดียวกัน

`installer/install.ps1` ยังคงไม่ดาวน์โหลด Python และไม่ลดระดับการตรวจสอบใด ๆ การติดตั้ง Git/Python ที่ขาดเป็นหน้าที่ของ Prompt ก่อน Clone เท่านั้น และจำกัดอยู่ที่ current-user โดยไม่ขอสิทธิ์ Administrator หาก WinGet หรือการตรวจหลังติดตั้งไม่ผ่าน Prompt จะหยุดอย่างปลอดภัยก่อนสร้าง Runtime การใช้ Google Sheet แบบ Private เป็นการตั้งค่าเสริมหลัง HQ พร้อมใช้งาน โดยทำตาม [docs/research-sheet-hub-setup-th.md](docs/research-sheet-hub-setup-th.md)

Release สำหรับห้องเรียนมี Google OAuth native/installed-app client configuration กลางของ Metafxclub อยู่แล้วใน `backend/local-runner/google_oauth_native_client.txt` ไฟล์จริงถูก GitHub Actions inject จาก Release secrets ตอน build Asset และถูกกันออกจาก public Git tree; ห้าม commit ค่า Client จริงลง Source สาธารณะ แม้ `client_id`/`client_secret` ของ installed app จะเป็น metadata ที่ต้องแจกพร้อมตัวโปรแกรมและไม่ใช่รหัสผ่านหรือ Credential ของบัญชีผู้ใช้ ตัวติดตั้งตรวจ Client กลางจากชุด Release โดยอัตโนมัติ ผู้เรียนจึง **ไม่ต้อง** สร้าง Google Cloud Project/OAuth Client, เพิ่ม Gmail เป็น Test user, ดาวน์โหลด OAuth JSON, ส่งไฟล์ Credential หรือแก้ Client ID ใด ๆ หลังเปิด Agent HQ ผู้เรียนทำเองเพียงกด **เชื่อมบัญชี Google**, เลือกบัญชีของตน และกดยืนยัน Consent ในหน้าทางการของ Google แล้วจึงกรอก Sheet ID ส่วน access token และ refresh token ของผู้เรียนจะเก็บแบบเข้ารหัสด้วย Windows current-user DPAPI และไม่เข้า Repository, Frontend, Report หรือ Log

ระหว่างที่ Google ยังตรวจสอบ Sensitive Scope ของแอปกลาง ผู้ใช้ใหม่อาจเห็นหน้า `Google ยังไม่ได้ยืนยันแอปนี้` และจำนวนผู้ใช้ใหม่อาจอยู่ภายใต้ OAuth unverified user cap ของ Project กลาง เมื่อ Google อนุมัติ Scope ที่ระบบขอแล้ว คำเตือนและเพดานนี้จะไม่ใช้กับ Scope ที่ได้รับอนุมัติ ดู [Google Auth Platform — Audience](https://support.google.com/cloud/answer/15549945)

`2-SETUP-GOOGLE-HQ.bat` และ Desktop OAuth JSON ยังคงมีไว้เฉพาะ **Advanced/Recovery custom override** สำหรับเจ้าของระบบที่ตั้งใจใช้ OAuth Project ของตนเอง ไม่ใช่ขั้นตอนติดตั้งของนักเรียน หากใช้โหมดนี้ต้องใช้ JSON ของ Project ที่ตนควบคุมเอง ห้ามส่งให้ผู้อื่น และไฟล์ต้นฉบับจะไม่ถูกลบอัตโนมัติ

## ติดตั้งด้วย Prompt เดียวผ่าน Codex

เส้นทางหลักสำหรับห้องเรียนคือ [Prompt ติดตั้งอัตโนมัติ](docs/prompts/install-github-google-auto-th.md) ซึ่งล็อก Repository, Git Tag และ Version ไว้แล้ว ผู้เรียนวาง Prompt ทั้งชุดใน Codex ได้ทันทีโดยไม่ต้องกรอก Client ID หรือ Path ของ OAuth JSON Codex จะตรวจและใช้ Git/Python เดิมก่อน ติดตั้งเฉพาะตัวที่ขาดผ่าน WinGet แบบ current-user, Clone Tag ที่กำหนดจาก GitHub ลงพื้นที่ชั่วคราว, ตรวจ Source, ดาวน์โหลด Release ZIP กับ `.sha256` ที่ตรง Tag, ตรวจ hash แล้ว extract เฉพาะไฟล์ Client กลางที่ GitHub Actions inject เข้า SOURCE_DIR ก่อนเรียก Installer ตัว Installer จะตรวจ SHA-256 และ Bootstrap `pip==26.2.1` จากไฟล์ Offline ก่อนเชื่อม PyPI เพื่อใช้ Windows certificate store โดยไม่ปิด TLS จากนั้นตรวจ Bridge/Health/หน้าเว็บ เปิด Watchdog หลัง Login และเปิด HQ ที่ `http://127.0.0.1:4186/` โดยผู้เรียนไม่ต้องติดตั้ง Git/Python ล่วงหน้า ไม่ต้องดาวน์โหลด ZIP เอง และไม่ต้องกด BAT

ขั้นตอนที่ระบบไม่ทำแทนคือการ Login/เลือกบัญชี/กดอนุญาตในหน้าทางการของ Google ผู้เรียนเหลือเพียงกด **เชื่อมบัญชี Google ครั้งเดียว** ใน HQ เท่านั้น

Prompt ต้องล็อก Git Tag และ `EXPECTED_VERSION` ให้ตรงกัน ห้ามเปลี่ยนเป็น Branch `main` หรือ URL `latest` ระหว่างคาบ เพราะนักเรียนแต่ละคนอาจได้รับ Source คนละช่วงเวลา เมื่อออกเวอร์ชันใหม่ให้อาจารย์ส่ง Prompt ฉบับที่อัปเดต Tag/Version แล้วแทนการให้ผู้เรียน Pull เอง

## ติดตั้งด้วยตนเอง

หากไม่ได้ใช้ Codex ช่วยติดตั้ง:

1. ตรวจว่ามี Python 3.10-3.14 แบบ 64-bit และเลือก `Add Python to PATH` แล้ว
2. ดาวน์โหลดทั้ง Asset `.zip` และไฟล์ `.zip.sha256` ชื่อเดียวกันจาก GitHub Release ที่อาจารย์ส่งให้
3. เปิด PowerShell ในโฟลเดอร์ดาวน์โหลด รัน `Get-FileHash -Algorithm SHA256 .\ชื่อไฟล์.zip` แล้วเทียบค่ากับข้อความตัวแรกในไฟล์ `.zip.sha256` ให้ตรงกันทุกตัวอักษร หากไม่ตรงให้ลบไฟล์และหยุดติดตั้ง
4. แตก ZIP ให้เรียบร้อย ห้ามเปิดตัวติดตั้งจากใน ZIP
5. ดับเบิลคลิก `1-INSTALL-HQ.bat`
6. ตัวติดตั้งใช้ `http://127.0.0.1:4186/`, รัน Deployment Preflight, เปิด Bridge และตรวจทั้ง Health กับหน้าเว็บให้เอง หากพอร์ต 4186 ถูกโปรแกรมอื่นใช้อยู่ ระบบจะหยุดโดยไม่ปิดโปรแกรมนั้น
7. รอจน Browser เปิดหน้า Agent HQ และตัวติดตั้งแจ้งว่าสำเร็จ พร้อมแสดง Health, Codex และ Rate Limit ของบัญชีเครื่องนี้
8. Client กลางพร้อมมากับ Release แล้ว ให้กด **เชื่อมบัญชี Google ครั้งเดียว** ใน Agent HQ เลือกบัญชีและยืนยัน Consent ด้วยตนเอง จากนั้นกรอก Sheet ID

คู่มือฉบับย่อสำหรับส่งให้นักเรียนอยู่ที่ [STUDENT-QUICKSTART-TH.md](STUDENT-QUICKSTART-TH.md)

## Clone Source เพื่อเรียนและพัฒนา

Repository หลัก: `https://github.com/metafxclub/metafxclub-ai-agent-hq`

ส่วนนี้มีไว้เก็บ Source เพื่ออ่าน เรียน GitHub แก้โค้ด และรันชุดทดสอบเท่านั้น ไม่ใช่เส้นทางติดตั้งสำหรับห้องเรียนและไม่ได้รับสถานะ `verified_remote_git_tag` แบบ Prompt อัตโนมัติ Public Git Source จงใจไม่มีไฟล์ Client กลางจาก Release ดังนั้น **ห้ามคาดหวังว่า Plain clone แล้วเปิด `1-INSTALL-HQ.bat` หรือ `UPDATE-HQ.bat` จะติดตั้ง Runtime ห้องเรียนพร้อม Google ได้** การติดตั้งหรืออัปเดต Runtime ของนักเรียนต้องใช้ [Prompt หลัก](docs/prompts/install-github-google-auto-th.md) ที่ล็อก Tag/Version และตรวจ Release Asset + hash แล้วเท่านั้น ส่วน Advanced/Recovery custom override สงวนไว้สำหรับผู้ดูแลระบบที่ควบคุม OAuth Project ของตนเอง ห้ามคัดลอก Client จาก Runtime กลับมา commit

```powershell
git clone https://github.com/metafxclub/metafxclub-ai-agent-hq.git
cd metafxclub-ai-agent-hq
git status
```

Plain clone ข้างต้นไม่ใช่ Runtime ที่ติดตั้งใน `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ` และ `UPDATE-HQ.bat` ไม่ใช่ตัวอัปเดตสำหรับชุดห้องเรียนที่ติดตั้งด้วย Release เมื่อมีรุ่นใหม่ให้อาจารย์ส่ง Prompt ฉบับใหม่ที่ล็อก Tag/Version ใหม่ ห้ามเปลี่ยนเป็นการ Pull `main` แล้วติดตั้งทับ Runtime เอง

นักเรียนที่ต้องการส่งโค้ดกลับควร Fork Repository ของตนเอง แล้วใช้ Branch → Commit → Push → Pull Request ตามบทเรียน GitHub โดยไม่ Commit โฟลเดอร์ `data/runtime`, `data/memory`, `outputs`, `.env`, `.codex`, Token, Auth หรือข้อมูลบัญชีใด ๆ ตัวติดตั้งใน `%LOCALAPPDATA%` ไม่ใช่ Git Repository และไม่ควรใช้เป็นโฟลเดอร์เขียนโค้ด

## วิธีตรวจว่าพร้อมใช้งาน

การเห็นหน้าต่างคำสั่งเปิดขึ้นมาอย่างเดียวยังไม่ถือว่าติดตั้งสำเร็จ ต้องตรวจครบดังนี้:

- `scripts/status-local-bridge.cmd` แสดงว่า HQ Bridge ทำงาน
- อ่าน `health_url` จาก `data/runtime/bridge-endpoint.json` แล้วพบ `ok: true`, `status: "ready"` และ Endpoint ตรงกัน
- เปิด `url` จากไฟล์เดียวกันได้และเห็น Agent ครบตามระบบ
- `scripts/check-codex-readiness.cmd` แสดงสถานะ Codex และ Rate Limit ของบัญชีที่ Login อยู่ใน Windows User เครื่องนี้
- `data/runtime/install-result.json` มีรายงานการติดตั้งแบบไม่เก็บชื่อบัญชี Token, Cookie หรือ Auth

หากเปิดไม่ได้ ให้รัน `scripts/repair-hq.cmd` แล้วตรวจสถานะอีกครั้ง ระบบจะไม่ปิดโปรแกรมอื่นที่ใช้ Port เดิมและจะไม่เปลี่ยน URL เองโดยไม่ถามผู้ใช้

ตัวติดตั้งลงทะเบียน Bridge ให้กลับมาทำงานเองหลังเข้าสู่ Windows โดยอัตโนมัติ สร้าง Scheduled Task สำหรับ Windows User ปัจจุบัน ลองเปิดใหม่เมื่อเริ่มไม่สำเร็จ และตรวจ Bridge ซ้ำทุก 15 นาทีผ่านตัวเปิดแบบไม่มีหน้าต่าง Task นี้เปิดเฉพาะ Bridge แบบซ่อน ไม่เปิด Browser หรือ MT4/MT5 และยกเลิกได้ด้วย `scripts/unregister-bridge-autostart.cmd` หากจงใจติดตั้งโดยไม่สร้าง Task ให้เรียก Installer ขั้นสูงด้วย `-SkipAutostart`

## สิ่งที่ใช้งานได้ในโหมดเริ่มต้น

- เปิด Visual Office และดู Agent ทั้ง 10 บทบาท
- คุยกับ Agent ทั้ง 10 ตัวผ่าน Codex ตามบทบาท โดยการคุยแต่ละครั้งใช้โควตา Codex
- เมื่อข้อความเป็นคำสั่งให้ลงมือทำ Backend จะสร้าง Mission จากบทสนทนาแบบไม่ซ้ำ และส่งงานไปยัง Agent/อุปกรณ์ที่ตรงกับหน้าที่
- เปิดโหมด `อัตโนมัติ — Full Access ใน Workspace` ที่มุมขวาบน เพื่อให้งานทั่วไปเริ่มต่อเองจนได้ Report โดยไม่ต้องกดอนุมัติทีละงาน
- ใช้ปุ่ม `สร้าง Task ทางลัด` ได้เมื่อต้องการสร้างงานโดยตรงโดยไม่ต้องให้ Chat จำแนกคำขอ
- เปิด Dashboard ของอุปกรณ์ 9 จุดผ่าน 3 แท็บ: `การเชื่อมต่อ`, `งานของอุปกรณ์` และ `ผลลัพธ์งาน`
- กดหัวข้อ Task หรือ Report เพื่อเปิดรายละเอียด และดู Mission ทั้งหมดที่โต๊ะ Mission Kanban
- ตรวจ Bridge, Codex/MCP status และ Codex Rate Limit ของบัญชีที่ Login อยู่ในเครื่อง
- สแกนและเลือก MT4 / MT5 จากแถบกลางครั้งเดียว แล้วให้สภา AI Trade, โรงงานสร้าง EA และห้องทดลองอ่าน Terminal เป้าหมายจาก Backend เดียวกัน
- ทุกงานจริงมี Mission ID, เจ้าของงาน, สถานะ, Audit log และ Report

หน้า `สภา AI Trade` มีหน้าวิเคราะห์เพิ่มสำหรับ Price Action, ตาราง Technical ย้อนหลัง 300 แท่ง และข่าว/แนวโน้ม การเปิดดูหรือสร้างแพ็กเกจ Local ไม่เรียก Codex; จะใช้ Rate Limit เมื่อกดให้ AI วิเคราะห์หรือ Trigger วิเคราะห์เมื่อเกิดแท่งใหม่เท่านั้น รายละเอียดข้อมูลจริงที่ส่งให้ Specialist อยู่ที่ [docs/ai-trade-deep-analysis-300-th.md](docs/ai-trade-deep-analysis-300-th.md)

การ Login Codex เป็นขั้นตอนแยก ผู้เรียนต้อง Login ด้วยบัญชีของตนเอง ระบบจะไม่แจกหรือคัดลอกบัญชีของผู้สอน หาก Codex แสดง `auth_required` แต่หน้า Office และ Health พร้อม แปลว่า HQ ติดตั้งสำเร็จแล้วและเหลือเพียง Login บัญชี Codex

Agent Chat ไม่มีสิทธิ์เรียก Tool เอง โดยจะคืนเฉพาะคำตอบและประเภทคำขอให้ Backend หากเป็นคำสั่งงาน Backend จึงค่อยสร้าง Mission และให้ Worker ทำงานผ่าน Local Runner ภายใต้สิทธิ์ของโหมดที่เลือก ปัจจุบัน Computer Use, MCP execution, Plugin execution, Telegram จริง และ MT4/MT5 execution adapter ยังไม่เปิดใช้งาน

## เชื่อม MT4 / MT5 จากแถบกลาง

- แท็บเดิม `Agent คุยกันเอง` ถูกแทนด้วย `เชื่อม MT4 / MT5`; ตาราง Agent คุยกันเองแบบตั้งเวลาถูกปิดใช้งานและไม่ใช้โควตา Codex เบื้องหลัง
- ปุ่มสแกนตรวจเฉพาะตำแหน่งติดตั้งมาตรฐานและสถานะโปรแกรมแบบอ่านอย่างเดียว ไม่เปิด Terminal และไม่อ่านเลขบัญชี รหัสผ่าน หรือข้อมูล Broker
- หากพบ Terminal แพลตฟอร์มเดียวกันหลายตัว ต้องเปิดตัวที่ต้องการเพียงหนึ่งตัวแล้วสแกนใหม่ ระบบจึงจะยอม Apply เพื่อลดความเสี่ยงเลือกผิดโปรแกรม
- การ Apply หนึ่งครั้งบันทึกค่ากลางแบบ atomic: MT4 ส่งให้สภา AI Trade, โรงงานสร้าง EA และห้องทดลอง; MT5 ส่งให้โรงงานสร้าง EA และห้องทดลองที่รองรับ
- หน้าของอุปกรณ์แต่ละห้องแสดงสถานะจาก Backend แบบอ่านอย่างเดียว การเลือก Terminal ทำได้เฉพาะแถบกลาง และไม่เปิด Demo, Live Trading หรือการส่งคำสั่งเทรดให้อัตโนมัติ

## โหมดการทำงานมุมขวาบน

- `ตรวจสอบก่อนเริ่มงาน` — เหมาะกับเครื่องนักเรียนและการทดลอง งานที่เรียก Codex Task จะรอการยืนยันตามกฎเดิม
- `อัตโนมัติ — Full Access ใน Workspace` — งานที่ Backend อนุญาตสามารถอ่าน สร้าง และแก้ไฟล์ภายในโฟลเดอร์โปรเจกต์นี้ แล้วส่ง Report กลับ Dashboard โดยอัตโนมัติ
- คำว่า Full Access ในที่นี้ไม่ใช่การข้าม Sandbox และไม่ใช่สิทธิ์ทั้งเครื่อง งานจะรันด้วย `workspace-write` ภายใน `PROJECT_ROOT` เท่านั้น
- การส่ง Telegram จริง, Deploy/Publish ภายนอก, ลบไฟล์, Restart VPS, ใช้เงินจริง/เครดิต และงานที่มี Secret ยังคงถูกหยุดหรือรอการอนุมัติ ส่วน Live Trading ใช้สิทธิ์ถาวรที่ Inputs ของ EA พร้อม Signed Command และ Risk Guard โดย Frontend เปิดแทนไม่ได้
- Mission เก่าที่สร้างก่อนเปิดโหมดอัตโนมัติจะไม่ถูกหยิบไปรันย้อนหลังโดยอัตโนมัติ

## ขอบเขตความปลอดภัย

- Frontend ไม่เก็บ Token, API key, Cookie, Auth หรือรหัสผ่าน
- Bridge รับการเชื่อมต่อเฉพาะ `127.0.0.1`; ตัวติดตั้งเสนอ Port ว่างให้ผู้ใช้ยืนยัน และบันทึก Port หลัง Health check ผ่านเท่านั้น
- งานทั่วไปในโหมดอัตโนมัติผ่านการตรวจสิทธิ์และ Risk Guard ของ Backend แบบผูกกับ Mission โดยไม่ต้องกดอนุมัติซ้ำ
- งานเสี่ยงยังคงแยกการอนุมัติออกจากการ Execute และต้องผ่าน Risk Guard/Approval Gate
- Live Trading ปิดโดยค่าเริ่มต้น และเปิดได้เฉพาะใน MT4 EA เมื่อผ่าน Shadow/Demo, Risk limit, Kill Switch, Signed Envelope, Key pin/match และตั้ง `GatewayMode=GATEWAY_LIVE` กับ `LiveArmed=true`; ไม่ต้องอนุมัติทีละ Order และ AI/Frontend เปลี่ยนค่านี้ไม่ได้
- ห้ามนำ `.env`, `.venv`, `data/runtime`, Log, Memory หรือ `%USERPROFILE%\.codex` ของบุคคลอื่นมาใส่ในชุดติดตั้ง

การถอนด้วย `UNINSTALL-HQ.bat` แบบปกติจะเก็บ Mission/Report/Memory/Log และ durable Google grant ที่เข้ารหัสไว้ เพื่อให้ติดตั้งใหม่แล้วใช้ต่อได้ การลบข้อมูลทั้งหมดต้องเรียก `scripts\uninstall-hq.ps1 -RemoveUserData -ConfirmUserDataRemoval DELETE-METAFX-DATA` โดยตรง จึงจะลบ durable grant และ OAuth Client แบบ custom override ผ่าน Backend CLI ด้วย ส่วน Client กลางเป็นส่วนหนึ่งของ Release และ Environment variable/OAuth JSON ต้นฉบับที่ผู้ดูแลตั้งเองในโหมด Advanced จะไม่ถูกลบอัตโนมัติ

## โครงสร้างระบบสำหรับผู้พัฒนา

1. `frontend/` — ห้อง ตัวละคร การเคลื่อนไหว และ Dashboard
2. `contracts/` — บทบาท Agent, Mission, Report, Permission และ Approval
3. `backend/local-runner/bridge_server.py` — Local API, Queue, Policy gate, Audit และ Report routing
4. `runner/codex_cli_runner.py` — เรียก Codex CLI หลังผ่านเงื่อนไขที่กำหนด
5. `data/runtime/` — Mission, Report และ Audit ของเครื่องผู้ใช้
6. `data/memory/` — Memory card, Summary และ Meeting transcript ที่ไม่ใช่ข้อมูลลับ
7. `tests/` — ชุดตรวจ Contract, Asset, Health, Approval boundary และ Secret redaction

คำสั่งดูแลระบบ:

- `Open Metafx Agent HQ.cmd` — เปิด HQ
- `UPDATE-HQ.bat` — รับ Source รุ่นใหม่จาก GitHub แบบ fast-forward และติดตั้งซ้ำอย่างปลอดภัย
- `scripts/status-local-bridge.cmd` — ตรวจสถานะ
- `scripts/check-codex-readiness.cmd` — ตรวจ Codex login และ Rate Limit ของบัญชีเครื่องนี้
- `scripts/repair-hq.cmd` — ซ่อมการติดตั้งและตรวจใหม่
- `scripts/restart-local-bridge.cmd` — Restart Bridge อย่างควบคุม
- `scripts/stop-local-bridge.cmd` — หยุดเฉพาะ HQ Bridge ที่ตรวจสอบตัวตนแล้ว
- `scripts/register-bridge-autostart.cmd` — เปิด Bridge อัตโนมัติหลังเข้าสู่ Windows
- `scripts/unregister-bridge-autostart.cmd` — ยกเลิกการเปิดอัตโนมัติ

รายละเอียดการทำงานภายในดูได้ที่ `scripts/README-bridge-lifecycle.md` และเอกสารใน `docs/`
