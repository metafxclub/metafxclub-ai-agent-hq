# Metafxclub AI Agent HQ

AI Agent Visual Office แบบ Local สำหรับจัดการ Mission, Agent และ Dashboard ของงาน Forex VPS, EA, Backtest, Optimization, Codex/MCP และระบบ Automation โดยข้อมูลลับและการเรียกเครื่องมือจริงจะอยู่หลัง Local Bridge เท่านั้น

โปรแกรมเริ่มต้นในโหมด **Demo/Read-only** จึงไม่ส่ง Telegram จริง ไม่ Deploy และไม่ส่งคำสั่ง Live Trading ระหว่างติดตั้ง

## สิ่งที่ต้องมีก่อนติดตั้งบน Windows

- Windows 10 หรือ 11 และอินเทอร์เน็ตสำหรับติดตั้ง Dependency ที่ล็อกเวอร์ชันไว้
- Python **3.10-3.14** จาก [python.org](https://www.python.org/downloads/windows/) โดยเลือก `Add Python to PATH` ระหว่างติดตั้ง
- บัญชี Codex ของผู้เรียนเอง (Login ภายหลังได้; HQ และ Health ยังเปิดตรวจได้แม้ Codex ยังไม่ Login)

ตัวติดตั้งไม่ดาวน์โหลด Python และไม่ขอสิทธิ์ Administrator เพื่อติดตั้ง Python แทนผู้เรียน หากหา Python รุ่นที่รองรับไม่พบ ระบบจะหยุดพร้อมข้อความแก้ไขและไม่ทิ้ง Runtime ที่ติดตั้งครึ่งเดียว การใช้ Google Sheet แบบ Private เป็นการตั้งค่าเสริมหลัง HQ พร้อมใช้งาน โดยทำตาม [docs/research-sheet-hub-setup-th.md](docs/research-sheet-hub-setup-th.md) และห้ามส่งไฟล์ OAuth Client Secret ให้ผู้อื่น

เมื่อต้องใช้ Google Sheet แบบ Private ให้ผู้เรียนดาวน์โหลด OAuth Client JSON ประเภท **Desktop app** จาก Google Auth Platform ของตนเอง แล้วเลือกไฟล์ใน First-run wizard ของตัวติดตั้ง หรือดับเบิลคลิก/ลากไฟล์ไปวางบน `2-SETUP-GOOGLE-HQ.bat` ภายหลัง ระบบส่งเฉพาะ Path ให้ Backend CLI อ่านและบันทึกด้วย Windows current-user DPAPI; JSON และ Client Secret ไม่ผ่าน Browser ไม่ถูกคัดลอกเข้า Project และไม่ถูกส่งให้ผู้สอน หลังนำเข้าแล้วเปิด Agent HQ กด **เชื่อมบัญชี Google ครั้งเดียว** จากนั้นจึงกรอก Sheet ID ไฟล์ JSON ต้นฉบับจะไม่ถูกลบอัตโนมัติ ผู้เรียนต้องเก็บเป็นความลับและลบเองเมื่อไม่ต้องใช้แล้ว

หาก OAuth consent screen ยังเป็น `Testing` ต้องเพิ่มบัญชีผู้เรียนใน Test users และสิทธิ์/Refresh token อาจหมดอายุหลัง 7 วันตามนโยบาย Google หากต้องการประสบการณ์เชื่อมครั้งเดียวระยะยาว ต้องจัด Publishing status และ Verification ของ OAuth app ให้เหมาะสมก่อนแจก ดู [Google Auth Platform — Audience](https://support.google.com/cloud/answer/15549945)

## ติดตั้งด้วยลิงก์เดียวและ Prompt เดียว

อาจารย์ส่งลิงก์ GitHub Release, Client ID และให้ผู้เรียนคัดลอก Path ของ Desktop OAuth JSON ลงใน [Prompt ติดตั้งอัตโนมัติ](docs/prompts/install-github-google-auto-th.md) จากนั้นวาง Prompt ใน Codex เพียงครั้งเดียว Codex จะดาวน์โหลดและตรวจ Checksum, เรียก Installer ครั้งเดียวพร้อมนำเข้า JSON ผ่าน Backend DPAPI, ตรวจ Bridge/Health/หน้าเว็บ, เปิด Watchdog หลัง Login และเปิด HQ ที่ `http://127.0.0.1:4186/` โดยผู้เรียนไม่ต้องกด BAT

ขั้นตอนที่ระบบไม่ทำแทนคือการ Login/เลือกบัญชี/กดอนุญาตในหน้าทางการของ Google ผู้เรียนเหลือเพียงกด **เชื่อมบัญชี Google ครั้งเดียว** ใน HQ เท่านั้น

ควรใช้ลิงก์ Release ที่ล็อกเวอร์ชัน เช่น `.../releases/tag/v1.0.0` ไม่ควรใช้ไฟล์ ZIP จาก Branch `main` ในห้องเรียน เพราะนักเรียนแต่ละคนอาจได้รับไฟล์คนละช่วงเวลา

## ติดตั้งด้วยตนเอง

หากไม่ได้ใช้ Codex ช่วยติดตั้ง:

1. ตรวจว่ามี Python 3.10-3.14 และเลือก `Add Python to PATH` แล้ว
2. ดาวน์โหลด Asset สำหรับ Windows จาก GitHub Release ที่อาจารย์ส่งให้
3. แตก ZIP ให้เรียบร้อย ห้ามเปิดตัวติดตั้งจากใน ZIP
4. ดับเบิลคลิก `1-INSTALL-HQ.bat`
5. ตัวติดตั้งใช้ `http://127.0.0.1:4186/`, รันชุดตรวจ, เปิด Bridge และตรวจทั้ง Health กับหน้าเว็บให้เอง หากพอร์ต 4186 ถูกโปรแกรมอื่นใช้อยู่ ระบบจะหยุดโดยไม่ปิดโปรแกรมนั้น
6. รอจน Browser เปิดหน้า Agent HQ และตัวติดตั้งแจ้งว่าสำเร็จ พร้อมแสดง Health, Codex และ Rate Limit ของบัญชีเครื่องนี้
7. หากตั้งค่า Google ใน First-run wizard แล้ว ให้กด **เชื่อมบัญชี Google ครั้งเดียว** ใน Agent HQ จากนั้นกรอก Sheet ID

คู่มือฉบับย่อสำหรับส่งให้นักเรียนอยู่ที่ [STUDENT-QUICKSTART-TH.md](STUDENT-QUICKSTART-TH.md)

## ดาวน์โหลดและอัปเดตจาก GitHub

Repository หลัก: `https://github.com/metafxclub/metafxclub-ai-agent-hq`

สำหรับนักเรียนที่เรียน GitHub ให้ Clone เก็บเป็น Source และปล่อยให้ตัวติดตั้งวาง Runtime ที่ใช้งานจริงไว้ใน `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ` แยกกัน:

```powershell
git clone https://github.com/metafxclub/metafxclub-ai-agent-hq.git
cd metafxclub-ai-agent-hq
.\1-INSTALL-HQ.bat
```

เมื่อต้องการรับรุ่นใหม่และ Source ไม่มีไฟล์ที่แก้ค้างอยู่ ให้ดับเบิลคลิก `UPDATE-HQ.bat` ระบบจะใช้ `fetch --all --prune` และ `merge --ff-only` เท่านั้น จากนั้นติดตั้ง Source รุ่นใหม่ไปยังตำแหน่งถาวรและรันชุดตรวจอีกครั้ง หาก Git มีงานของนักเรียนที่ยังไม่ Commit ระบบจะหยุดก่อนโดยไม่ Stash, Merge หรือทับไฟล์ให้อัตโนมัติ

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
- ตั้งช่วงเวลาให้ Agent หลายบทบาทคุยผ่าน Codex แล้วให้ Manager สรุปกลับโต๊ะ Mission โดยจำกัดจำนวนรอบ จำนวนครั้งต่อวัน และโควตาที่ต้องสำรองไว้
- ทุกงานจริงมี Mission ID, เจ้าของงาน, สถานะ, Audit log และ Report

หน้า `สภา AI Trade` มีหน้าวิเคราะห์เพิ่มสำหรับ Price Action, ตาราง Technical ย้อนหลัง 300 แท่ง และข่าว/แนวโน้ม การเปิดดูหรือสร้างแพ็กเกจ Local ไม่เรียก Codex; จะใช้ Rate Limit เมื่อกดให้ AI วิเคราะห์หรือ Trigger วิเคราะห์เมื่อเกิดแท่งใหม่เท่านั้น รายละเอียดข้อมูลจริงที่ส่งให้ Specialist อยู่ที่ [docs/ai-trade-deep-analysis-300-th.md](docs/ai-trade-deep-analysis-300-th.md)

การ Login Codex เป็นขั้นตอนแยก ผู้เรียนต้อง Login ด้วยบัญชีของตนเอง ระบบจะไม่แจกหรือคัดลอกบัญชีของผู้สอน หาก Codex แสดง `auth_required` แต่หน้า Office และ Health พร้อม แปลว่า HQ ติดตั้งสำเร็จแล้วและเหลือเพียง Login บัญชี Codex

Agent Chat ไม่มีสิทธิ์เรียก Tool เอง โดยจะคืนเฉพาะคำตอบและประเภทคำขอให้ Backend หากเป็นคำสั่งงาน Backend จึงค่อยสร้าง Mission และให้ Worker ทำงานผ่าน Local Runner ภายใต้สิทธิ์ของโหมดที่เลือก ปัจจุบัน Computer Use, MCP execution, Plugin execution, Telegram จริง และ MT4/MT5 execution adapter ยังไม่เปิดใช้งาน

## Agent คุยกันเอง

- เปิดแผง `Agent คุยกันเอง` ด้านบนเพื่อกำหนดหัวข้อ ช่วงเวลา ระยะห่าง จำนวนคำตอบ จำนวนครั้งสูงสุดต่อวัน และเปอร์เซ็นต์ Rate Limit ที่ต้องเก็บไว้
- ค่าเริ่มต้นปิดอยู่ และ Backend จะเริ่มได้เมื่อเปิด Full Access, Codex Runner ว่าง และข้อมูล Rate Limit สดและเหลือเหนือเกณฑ์
- แต่ละรอบเป็นการปรึกษาแบบปิด Tool: Specialist เสนอ/ตรวจข้อเสนอ และ Manager เป็นผู้สรุปรอบสุดท้าย ระบบไม่เปิดโปรแกรม ไม่เรียก Plugin/MCP และไม่สร้าง Task ต่อเอง
- ทุกการประชุมจริงสร้าง Mission, Transcript, Audit และ `collaboration_report` ที่โต๊ะ Mission ส่วนภาพการประชุมจำลองจะหยุดชั่วคราวระหว่างรอบจริง
- ฟังก์ชันนี้ใช้โควตา Codex ตามจำนวนคำตอบที่ตั้งไว้ หาก Rate Limit อ่านไม่ได้ ข้อมูลเก่า ต่ำกว่าเกณฑ์ หรือครบจำนวนต่อวัน ระบบจะพักโดยไม่ลองซ้ำถี่ ๆ

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

การถอนด้วย `UNINSTALL-HQ.bat` แบบปกติจะเก็บ Mission/Report/Memory/Log และ Google credential ที่เข้ารหัสไว้ เพื่อให้ติดตั้งใหม่แล้วใช้ต่อได้ การลบข้อมูลทั้งหมดต้องเรียก `scripts\uninstall-hq.ps1 -RemoveUserData -ConfirmUserDataRemoval DELETE-METAFX-DATA` โดยตรง จึงจะลบ Google OAuth Client และ durable grant ผ่าน Backend CLI ด้วย ส่วน Environment variable ที่ผู้ดูแลตั้งเองและ OAuth JSON ต้นฉบับจะไม่ถูกลบอัตโนมัติ

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
