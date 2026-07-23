# Metafxclub AI Agent HQ

AI Agent Visual Office แบบ Local สำหรับจัดการ Mission, Agent และ Dashboard ของงาน Forex VPS, EA, Backtest, Optimization, Codex/MCP และระบบ Automation โดยข้อมูลลับและการเรียกเครื่องมือจริงจะอยู่หลัง Local Bridge เท่านั้น

โปรแกรมเริ่มต้นในโหมด **Demo/Read-only** จึงไม่ส่ง Telegram จริง ไม่ Deploy และไม่ส่งคำสั่ง Live Trading ระหว่างติดตั้ง

## ติดตั้งด้วยลิงก์เดียวและ Prompt เดียว

อาจารย์ส่งลิงก์ GitHub Release ให้ผู้เรียน จากนั้นผู้เรียนวางข้อความนี้ใน Codex:

```text
ช่วยติดตั้ง Metafxclub AI Agent HQ จาก GitHub Release ลิงก์นี้บนเครื่อง Windows ของผมให้พร้อมใช้งาน และเปิดโปรแกรมให้ด้วยครับ:

[วางลิงก์ GitHub Release ที่นี่]

ให้อ่าน AGENTS.md, README.md, STUDENT-QUICKSTART-TH.md และ docs/prompts/install-local-endpoint-th.md ก่อนติดตั้ง จากนั้นให้ตัวติดตั้งตรวจพอร์ตว่างและเสนอ Local URL 3 ตัวเลือก อธิบายว่า IP 127.0.0.1 ถูกล็อกไว้เพื่อใช้เฉพาะเครื่องนี้ แล้วหยุดรอให้ผมเลือก URL ก่อนเริ่มติดตั้ง

เมื่อผมเลือกแล้ว ให้ใช้ตัวติดตั้งที่โปรเจกต์จัดเตรียมไว้กับ Port ที่ผมยืนยัน ห้ามสลับ URL เอง จากนั้นตรวจ Health, ตรวจการเชื่อม Codex และ Rate Limit ของบัญชีที่ Login อยู่ใน Windows User เครื่องนี้ แล้วเปิด URL ที่ผ่าน Health check ให้ผม

ให้เริ่มในโหมด Demo/Read-only ห้ามเปิด Live Trading ห้ามส่ง Telegram จริง และห้ามแสดงหรือคัดลอก Token, Cookie, API key, Codex Auth หรือรหัสผ่านใด ๆ
```

Codex จะดำเนินการตามลำดับ `ดาวน์โหลด Release → ตรวจชุดติดตั้ง → เสนอ URL ว่าง → รอผู้ใช้ยืนยันหนึ่งครั้ง → ติดตั้ง → ตรวจ Bridge/Health → ตรวจ Codex/Rate Limit → เปิดโปรแกรม` ผู้เรียนอาจต้องกดยืนยันสิทธิ์ดาวน์โหลดหรือเรียกตัวติดตั้งตามระบบความปลอดภัยของ Windows แต่ไม่ต้องพิมพ์คำสั่งติดตั้งเอง

ควรใช้ลิงก์ Release ที่ล็อกเวอร์ชัน เช่น `.../releases/tag/v1.0.0` ไม่ควรใช้ไฟล์ ZIP จาก Branch `main` ในห้องเรียน เพราะนักเรียนแต่ละคนอาจได้รับไฟล์คนละช่วงเวลา

## ติดตั้งด้วยตนเอง

หากไม่ได้ใช้ Codex ช่วยติดตั้ง:

1. ดาวน์โหลด Asset สำหรับ Windows จาก GitHub Release ที่อาจารย์ส่งให้
2. แตก ZIP ให้เรียบร้อย ห้ามเปิดตัวติดตั้งจากใน ZIP
3. ดับเบิลคลิก `1-INSTALL-HQ.bat`
4. ตัวติดตั้งจะแสดง URL ที่ว่าง เช่น `http://127.0.0.1:4186/` ให้พิมพ์ `Y` เพื่อยืนยัน หรือ `N` เพื่อดูตัวเลือกถัดไป
5. รอจนตัวติดตั้งแจ้งว่าสำเร็จ พร้อมแสดง Health, Codex และ Rate Limit ของบัญชีเครื่องนี้
6. ดับเบิลคลิก `Open Metafx Agent HQ.cmd`
7. เปิด URL ที่ตัวติดตั้งบันทึกหลัง Health ผ่าน

คู่มือฉบับย่อสำหรับส่งให้นักเรียนอยู่ที่ [STUDENT-QUICKSTART-TH.md](STUDENT-QUICKSTART-TH.md)

## วิธีตรวจว่าพร้อมใช้งาน

การเห็นหน้าต่างคำสั่งเปิดขึ้นมาอย่างเดียวยังไม่ถือว่าติดตั้งสำเร็จ ต้องตรวจครบดังนี้:

- `scripts/status-local-bridge.cmd` แสดงว่า HQ Bridge ทำงาน
- อ่าน `health_url` จาก `data/runtime/bridge-endpoint.json` แล้วพบ `ok: true`, `status: "ready"` และ Endpoint ตรงกัน
- เปิด `url` จากไฟล์เดียวกันได้และเห็น Agent ครบตามระบบ
- `scripts/check-codex-readiness.cmd` แสดงสถานะ Codex และ Rate Limit ของบัญชีที่ Login อยู่ใน Windows User เครื่องนี้
- `data/runtime/install-result.json` มีรายงานการติดตั้งแบบไม่เก็บชื่อบัญชี Token, Cookie หรือ Auth

หากเปิดไม่ได้ ให้รัน `scripts/repair-hq.cmd` แล้วตรวจสถานะอีกครั้ง ระบบจะไม่ปิดโปรแกรมอื่นที่ใช้ Port เดิมและจะไม่เปลี่ยน URL เองโดยไม่ถามผู้ใช้

## สิ่งที่ใช้งานได้ในโหมดเริ่มต้น

- เปิด Visual Office และดู Agent ทั้ง 10 บทบาท
- คุยกับ Agent ทั้ง 10 ตัวผ่าน Codex ตามบทบาท โดยการคุยแต่ละครั้งใช้โควตา Codex
- เมื่อข้อความเป็นคำสั่งให้ลงมือทำ Backend จะสร้าง Mission จากบทสนทนาแบบไม่ซ้ำ และส่งงานไปยัง Agent/อุปกรณ์ที่ตรงกับหน้าที่
- เปิดโหมด `อัตโนมัติ — Full Access ใน Workspace` ที่มุมขวาบน เพื่อให้งานทั่วไปเริ่มต่อเองจนได้ Report โดยไม่ต้องกดอนุมัติทีละงาน
- ใช้ปุ่ม `สร้าง Task ทางลัด` ได้เมื่อต้องการสร้างงานโดยตรงโดยไม่ต้องให้ Chat จำแนกคำขอ
- เปิด Dashboard ของอุปกรณ์ 9 จุดผ่าน 3 แท็บ: `การเชื่อมต่อ`, `งานของอุปกรณ์` และ `ผลลัพธ์งาน`
- กดหัวข้อ Task หรือ Report เพื่อเปิดรายละเอียด และดู Mission ทั้งหมดที่โต๊ะ Mission Kanban
- ตรวจ Bridge, Codex/MCP status และ Codex Rate Limit ของบัญชีที่ Login อยู่ในเครื่อง
- ทุกงานจริงมี Mission ID, เจ้าของงาน, สถานะ, Audit log และ Report

การ Login Codex เป็นขั้นตอนแยก ผู้เรียนต้อง Login ด้วยบัญชีของตนเอง ระบบจะไม่แจกหรือคัดลอกบัญชีของผู้สอน หาก Codex แสดง `auth_required` แต่หน้า Office และ Health พร้อม แปลว่า HQ ติดตั้งสำเร็จแล้วและเหลือเพียง Login บัญชี Codex

Agent Chat ไม่มีสิทธิ์เรียก Tool เอง โดยจะคืนเฉพาะคำตอบและประเภทคำขอให้ Backend หากเป็นคำสั่งงาน Backend จึงค่อยสร้าง Mission และให้ Worker ทำงานผ่าน Local Runner ภายใต้สิทธิ์ของโหมดที่เลือก ปัจจุบัน Computer Use, MCP execution, Plugin execution, Telegram จริง และ MT4/MT5 execution adapter ยังไม่เปิดใช้งาน

## โหมดการทำงานมุมขวาบน

- `ตรวจสอบก่อนเริ่มงาน` — เหมาะกับเครื่องนักเรียนและการทดลอง งานที่เรียก Codex Task จะรอการยืนยันตามกฎเดิม
- `อัตโนมัติ — Full Access ใน Workspace` — งานที่ Backend อนุญาตสามารถอ่าน สร้าง และแก้ไฟล์ภายในโฟลเดอร์โปรเจกต์นี้ แล้วส่ง Report กลับ Dashboard โดยอัตโนมัติ
- คำว่า Full Access ในที่นี้ไม่ใช่การข้าม Sandbox และไม่ใช่สิทธิ์ทั้งเครื่อง งานจะรันด้วย `workspace-write` ภายใน `PROJECT_ROOT` เท่านั้น
- Live Trading, การส่ง Telegram จริง, Deploy/Publish ภายนอก, ลบไฟล์, Restart VPS, ใช้เงินจริง/เครดิต และงานที่มี Secret ยังคงถูกหยุดหรือรอการอนุมัติ
- Mission เก่าที่สร้างก่อนเปิดโหมดอัตโนมัติจะไม่ถูกหยิบไปรันย้อนหลังโดยอัตโนมัติ

## ขอบเขตความปลอดภัย

- Frontend ไม่เก็บ Token, API key, Cookie, Auth หรือรหัสผ่าน
- Bridge รับการเชื่อมต่อเฉพาะ `127.0.0.1`; ตัวติดตั้งเสนอ Port ว่างให้ผู้ใช้ยืนยัน และบันทึก Port หลัง Health check ผ่านเท่านั้น
- งานทั่วไปในโหมดอัตโนมัติผ่านการตรวจสิทธิ์และ Risk Guard ของ Backend แบบผูกกับ Mission โดยไม่ต้องกดอนุมัติซ้ำ
- งานเสี่ยงยังคงแยกการอนุมัติออกจากการ Execute และต้องผ่าน Risk Guard/Approval Gate
- Live Trading ปิดไว้ จนกว่าจะมี Risk limit, Account allowlist, Kill switch และการอนุมัติอย่างชัดเจน
- ห้ามนำ `.env`, `.venv`, `data/runtime`, Log, Memory หรือ `%USERPROFILE%\.codex` ของบุคคลอื่นมาใส่ในชุดติดตั้ง

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
- `scripts/status-local-bridge.cmd` — ตรวจสถานะ
- `scripts/check-codex-readiness.cmd` — ตรวจ Codex login และ Rate Limit ของบัญชีเครื่องนี้
- `scripts/repair-hq.cmd` — ซ่อมการติดตั้งและตรวจใหม่
- `scripts/restart-local-bridge.cmd` — Restart Bridge อย่างควบคุม
- `scripts/stop-local-bridge.cmd` — หยุดเฉพาะ HQ Bridge ที่ตรวจสอบตัวตนแล้ว

รายละเอียดการทำงานภายในดูได้ที่ `scripts/README-bridge-lifecycle.md` และเอกสารใน `docs/`
