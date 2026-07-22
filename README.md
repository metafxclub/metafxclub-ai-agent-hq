# Metafxclub AI Agent HQ

AI Agent Visual Office แบบ Local สำหรับจัดการ Mission, Agent และ Dashboard ของงาน Forex VPS, EA, Backtest, Optimization, Codex/MCP และระบบ Automation โดยข้อมูลลับและการเรียกเครื่องมือจริงจะอยู่หลัง Local Bridge เท่านั้น

โปรแกรมเริ่มต้นในโหมด **Demo/Read-only** จึงไม่ส่ง Telegram จริง ไม่ Deploy และไม่ส่งคำสั่ง Live Trading ระหว่างติดตั้ง

## ติดตั้งด้วยลิงก์เดียวและ Prompt เดียว

อาจารย์ส่งลิงก์ GitHub Release ให้ผู้เรียน จากนั้นผู้เรียนวางข้อความนี้ใน Codex:

```text
ช่วยติดตั้ง Metafxclub AI Agent HQ จาก GitHub Release ลิงก์นี้บนเครื่อง Windows ของผมให้พร้อมใช้งาน และเปิดโปรแกรมให้ด้วยครับ:

[วางลิงก์ GitHub Release ที่นี่]

ให้อ่าน AGENTS.md, README.md และ STUDENT-QUICKSTART-TH.md ก่อนติดตั้ง ใช้ตัวติดตั้งที่โปรเจกต์จัดเตรียมไว้ ตรวจสถานะ Bridge และตรวจ http://127.0.0.1:4186/api/health จนพร้อม แล้วเปิด http://127.0.0.1:4186/ ให้ผม

ให้เริ่มในโหมด Demo/Read-only ห้ามเปิด Live Trading ห้ามส่ง Telegram จริง และห้ามแสดงหรือคัดลอก Token, Cookie, API key, Codex Auth หรือรหัสผ่านใด ๆ
```

Codex จะดำเนินการตามลำดับ `ดาวน์โหลด Release → ตรวจชุดติดตั้ง → ติดตั้ง → ตรวจ Bridge → ตรวจ Health → เปิดโปรแกรม` ผู้เรียนอาจต้องกดยืนยันสิทธิ์ดาวน์โหลดหรือเรียกตัวติดตั้งตามระบบความปลอดภัยของ Windows แต่ไม่ต้องพิมพ์คำสั่งติดตั้งเอง

ควรใช้ลิงก์ Release ที่ล็อกเวอร์ชัน เช่น `.../releases/tag/v1.0.0` ไม่ควรใช้ไฟล์ ZIP จาก Branch `main` ในห้องเรียน เพราะนักเรียนแต่ละคนอาจได้รับไฟล์คนละช่วงเวลา

## ติดตั้งด้วยตนเอง

หากไม่ได้ใช้ Codex ช่วยติดตั้ง:

1. ดาวน์โหลด Asset สำหรับ Windows จาก GitHub Release ที่อาจารย์ส่งให้
2. แตก ZIP ให้เรียบร้อย ห้ามเปิดตัวติดตั้งจากใน ZIP
3. ดับเบิลคลิก `1-INSTALL-HQ.bat`
4. รอจนตัวติดตั้งแจ้งว่าสำเร็จ
5. ดับเบิลคลิก `Open Metafx Agent HQ.cmd`
6. เปิด `http://127.0.0.1:4186/`

คู่มือฉบับย่อสำหรับส่งให้นักเรียนอยู่ที่ [STUDENT-QUICKSTART-TH.md](STUDENT-QUICKSTART-TH.md)

## วิธีตรวจว่าพร้อมใช้งาน

การเห็นหน้าต่างคำสั่งเปิดขึ้นมาอย่างเดียวยังไม่ถือว่าติดตั้งสำเร็จ ต้องตรวจครบดังนี้:

- `scripts/status-local-bridge.cmd` แสดงว่า HQ Bridge ทำงาน
- `http://127.0.0.1:4186/api/health` แสดง `ok: true` และ `status: "ready"`
- หน้า `http://127.0.0.1:4186/` เปิดได้และเห็น Agent ครบตามระบบ

หากเปิดไม่ได้ ให้รัน `scripts/repair-hq.cmd` แล้วตรวจสถานะอีกครั้ง ระบบจะไม่ปิดโปรแกรมอื่นที่บังเอิญใช้ Port 4186 โดยไม่ตรวจสอบก่อน

## สิ่งที่ใช้งานได้ในโหมดเริ่มต้น

- เปิด Visual Office และดู Agent ทั้ง 10 บทบาท
- คุยกับ Agent และส่ง Intent เพื่อสร้าง Mission
- ดู Mission Kanban, Task, Event, Meeting และ Report ตาม Dashboard
- ตรวจ Bridge, Codex/MCP status และ Codex Rate Limit ของบัญชีที่ Login อยู่ในเครื่อง
- ทดลอง Workflow แบบ Demo/Read-only พร้อม Approval และ Audit log

การ Login Codex เป็นขั้นตอนแยก ผู้เรียนต้อง Login ด้วยบัญชีของตนเอง ระบบจะไม่แจกหรือคัดลอกบัญชีของผู้สอน หาก Codex แสดง `auth_required` แต่หน้า Office และ Health พร้อม แปลว่า HQ ติดตั้งสำเร็จแล้วและเหลือเพียง Login บัญชี Codex

## ขอบเขตความปลอดภัย

- Frontend ไม่เก็บ Token, API key, Cookie, Auth หรือรหัสผ่าน
- Bridge รับการเชื่อมต่อเฉพาะ `127.0.0.1:4186`
- การอนุมัติและการ Execute เป็นคนละขั้นตอน
- งานเสี่ยงต้องผ่าน Risk Guard และ Approval Gate
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
- `scripts/repair-hq.cmd` — ซ่อมการติดตั้งและตรวจใหม่
- `scripts/restart-local-bridge.cmd` — Restart Bridge อย่างควบคุม
- `scripts/stop-local-bridge.cmd` — หยุดเฉพาะ HQ Bridge ที่ตรวจสอบตัวตนแล้ว

รายละเอียดการทำงานภายในดูได้ที่ `scripts/README-bridge-lifecycle.md` และเอกสารใน `docs/`

