# Metafxclub AI Agent Office - Agent Bible

เอกสารนี้คือ Agent Bible หลักของโปรเจกต์ Metafxclub AI Agent Office / AI Pixel Agent HQ / AI Agent Visual Office

ใช้ไฟล์นี้เพื่อส่งต่อให้ Codex, ChatGPT, AI agent หรือ developer อ่านก่อนเริ่มงาน เพื่อให้เข้าใจว่าโปรเจกต์นี้คืออะไร โครงโฟลเดอร์แบ่งอย่างไร AI แต่ละตัวทำอะไรได้ งานไหลอย่างไร และ MCP/Codex runner ต้องเชื่อมอย่างปลอดภัยตรงไหน

## 1. Project Identity

ชื่อโปรเจกต์: `Metafxclub AI Agent Office`

ชื่อโฟลเดอร์หลักที่แนะนำ: `AI Agent HQ Virtual Office`

แนวคิด:

- AI Pixel Agent HQ
- AI Agent Visual Office
- Metafxclub AI Kingdom
- Isometric fantasy-tech castle office

ระบบนี้ไม่ใช่ dashboard ธรรมดา แต่เป็นสำนักงาน AI แบบเห็นเป็นภาพ ตัวละครทุกตัวคือ AI Agent / role / worker ที่รับงาน เดินไปทำงานที่ prop ประชุมกัน และส่งรายงานกลับมา

## 2. Brand Context

Metafxclub คือแบรนด์ด้าน High-Performance VPS และ Automated Trading Systems สำหรับตลาด Forex

ระบบนี้ต้องรองรับ:

- Forex VPS สำหรับรัน EA 24/7
- EA MT4 / MT5
- Backtest
- Optimization
- Telegram Alert
- VPS Monitoring
- Dashboard / Report
- Codex / MCP assisted workflow

น้ำเสียงของระบบ:

- ชัดเจน
- มืออาชีพ
- ไม่รับประกันกำไร
- ไม่กระตุ้นการเทรดเสี่ยง
- ให้ความสำคัญกับ audit, risk, approval และความปลอดภัย

## 3. Current Project State

สถานะตอนนี้:

- มี prototype local web แล้ว
- มี map ห้องหลักแนว fantasy-tech castle office แล้ว
- มีแนวคิด prop/layer สำหรับกดดู report แล้ว
- มี agent roster หลัก 8 ตัวแล้ว
- มี asset ตัวละครบางตัว เช่น Manager Agent ที่เริ่มจัดเป็น sprite/status/portrait package แล้ว
- กำลังจัดโครงโปรเจกต์ใหม่บน Desktop เพื่อใช้ต่อใน VS Code / GitHub
- ยังไม่ถือว่ามี backend, database, runner, MCP bridge จริงครบแล้ว
- ตอนแรกควรเริ่มจาก mock contract ก่อน แล้วค่อยต่อ backend/runner จริง

## 4. Core Product Definition

ระบบต้องเป็น AI Agent Visual Office ที่:

- ตัวละครแต่ละตัวคือ AI Agent / role / task worker
- ผู้ใช้กดตัวละครเพื่อคุยหรือสั่งงานได้
- ผู้ใช้กด prop เพื่อเปิด report, tool, mission, workstation หรือ archive ได้
- Agent เดินไปหา prop เพื่อแสดงว่างานกำลังเกิดขึ้นจริง
- Agent เดินไปหา agent อีกตัวหรือเข้าห้องประชุมเพื่อแสดง agent-to-agent workflow
- Manager Agent รับคำสั่งจาก CEO แล้วแตกงานให้ specialist
- Specialist ทำงานตาม role และส่งผลกลับมา
- ผลงานถูกเก็บเป็น mission, report, meeting transcript, audit log และ archive
- งานเสี่ยงต้องรอ human approval
- MCP / Codex CLI / tool จริงต้องอยู่หลัง backend หรือ local runner เท่านั้น
- ห้าม expose token, API key, Codex auth, cookie, SSH key หรือ secret ลง frontend

## 5. What This Project Is Not

ห้ามตีความโปรเจกต์นี้เป็น:

- passive dashboard ที่มีตัวละครตกแต่งเฉย ๆ
- game demo ที่ไม่มี mission/report/tool จริง
- frontend ที่เรียก Codex/MCP/tool โดยตรง
- public web app ที่เปิด runner หรือ token ให้คนภายนอก
- ระบบรับประกันกำไรจาก Forex, EA หรือ AI Trader
- ระบบที่ agent สั่ง live trading, ลบไฟล์, ส่งข้อความสาธารณะ หรือ restart VPS โดยไม่รออนุมัติ

## 6. Core Agents

ระบบเริ่มต้นต้องมี agent หลัก 8 ตัว

### CEO

เจ้าของระบบ สั่งเป้าหมายใหญ่ รับ executive report และอนุมัติงานเสี่ยง

### Manager Agent

รับคำสั่งจาก CEO แตกงาน เลือก specialist ตั้ง deadline เรียกประชุม รวมผล และสรุปกลับ CEO

Manager Agent เป็นตัวหลักที่มีสิทธิสร้าง worker เพิ่มเมื่อ workload เต็ม แต่ต้องใช้ role template, mission context, budget, approval และ audit log

### EA Developer

เขียนหรือแก้ EA MT4/MT5 ตรวจ logic ตรวจ compile error และสร้าง next version plan

### Backtest Analyst

อ่าน backtest report วิเคราะห์ equity curve, drawdown, profit factor, win rate และข้อสังเกตสำคัญ

### Optimization Agent

วาง parameter range วิเคราะห์ optimization result ตรวจ overfit และเลือก candidate set

### VPS Watch

ตรวจ latency, uptime, CPU/RAM/disk, MT4/MT5 terminal status และเตือนเมื่อ service ผิดปกติ

### Telegram Ops

สร้าง alert เขียน summary เตรียมข้อความแจ้งเตือน และส่ง Telegram หลังได้รับอนุมัติ

### Risk Guard

ตรวจคำสั่งเสี่ยง secret exposure live trading file delete deploy public send compliance และมีสิทธิ block งาน

## 7. Agent Statuses

ใช้ status กลางชุดนี้:

- `idle`
- `resting`
- `planning`
- `walking`
- `meeting`
- `working`
- `waiting`
- `waiting_approval`
- `blocked`
- `reporting`
- `completed`
- `archived`
- `offline_sleep`

กติกา animation:

- ถ้า status = `walking` ให้ใช้ walk animation ตาม direction
- ถ้า status ไม่ใช่ `walking` ให้ใช้ status pose
- ถ้าไม่มี pose เฉพาะ ให้ fallback เป็น `idle`
- ถ้าเป็น `waiting_approval` ต้องแสดงว่ารอคนอนุมัติ
- ถ้าเป็น `blocked` ต้องแสดงสัญญาณเตือน

## 8. World And Rooms

โครงโลกในอนาคต:

```text
Metafx Kingdom
  Castle Hub
    Command Room
    EA & Backtest Lab
    VPS Ops Room
    Archive Library
  Future City
    Content Ops Room
    Customer Support Room
    Payment Credit Room
```

แนวทางปัจจุบัน:

- ทำ Command Room ให้ครบก่อน
- เตรียม contract สำหรับห้องอื่นไว้
- อย่าเริ่มหลายห้องก่อน mission/prop/report/archive ของห้องแรกทำงานครบ

## 9. Prop System

Prop ไม่ใช่ของตกแต่ง แต่เป็น report/action surface

ตัวอย่าง prop:

- Mission Table
- Server Rack
- Backtest Console
- Optimization Board
- Telegram Console
- Risk Guard Panel
- Archive Shelf
- MCP Portal
- Codex Runner Terminal
- Meeting Table

Prop ต้องมีข้อมูล:

- `prop_id`
- `room_id`
- `type`
- `label`
- `description`
- `position`
- `hitbox`
- `linked_mission_id`
- `linked_report_id`
- `linked_tool_id`
- `allowed_agents`
- `popup_view`
- `latest_status`

เมื่อกด prop:

1. Frontend ส่ง `prop_id` ไป backend
2. Backend หา report/mission/tool ที่ผูกไว้
3. Backend ส่ง popup data กลับมา
4. Frontend เปิด popup
5. User เห็นงานล่าสุด ประวัติ สถานะ และ action ที่ทำได้

## 10. Mission System

ทุกงานต้องเป็น mission และมี `mission_id`

Mission flow:

```text
CEO สั่งงาน
-> Manager สร้าง mission
-> Manager แตก task
-> Specialist รับงาน
-> Agent เดินไป prop
-> Runner ทำ mock/real tool
-> Specialist ส่ง report
-> Risk Guard ตรวจ
-> Manager รวมผล
-> CEO รับ executive summary
-> ปิดงานหรือทำต่อ
-> Archive
```

Mission ต้องเก็บ:

- `mission_id`
- `title`
- `status`
- `priority`
- `deadline`
- `created_by`
- `assigned_manager`
- `assigned_agents`
- `room_id`
- `related_props`
- `tasks`
- `reports`
- `meetings`
- `artifacts`
- `approval_required`
- `audit_log`

## 11. Agent-To-Agent Meeting

AI คุยกับ AI ได้ แต่ต้องผ่าน backend/orchestration

Meeting ต้องมี:

- `meeting_id`
- `mission_id`
- `room_id`
- `agenda`
- `participants`
- `turns`
- `decisions`
- `next_actions`
- `summary`
- `transcript`
- `audit_log`

Visual action:

- Manager เดินไป Mission Table
- Manager เรียก specialist
- Specialist เดินมาประชุม
- Meeting popup เปิด transcript/summary
- หลังประชุม agent แยกย้ายไป prop ของตัวเอง

## 12. Archive And Memory

งานเก่าต้องค้นกลับมาได้

Archive ใช้สำหรับ:

- ดูประวัติงาน
- เปิด report เก่า
- ให้ AI ดึงบริบทเดิมกลับมา
- เริ่ม mission ใหม่จากงานเก่า
- ลดปัญหาแชทยาวแล้วค้าง

โครง archive:

```text
data/runtime/archive/missions/mission-2026-06-10-backtest-001/
  summary.md
  manifest.json
  report.json
  transcript.json
  audit-log.json
  artifacts/
```

## 13. Architecture Rule

Flow ที่ถูกต้อง:

```text
frontend
-> backend
-> runner
-> Codex CLI / MCP / tool
-> runner parses output
-> backend saves result
-> frontend displays report/status
```

ห้าม:

```text
frontend -> Codex CLI
frontend -> MCP server
frontend -> secret/token
```

## 14. Folder Structure

โปรเจกต์หลักควรอยู่ที่:

```text
AI Agent HQ Virtual Office/
```

โครงหลัก:

```text
docs/
contracts/
frontend/
backend/
runner/
data/
assets-source/
scripts/
```

หน้าที่:

- `docs/` เอกสารหลัก เช่น Agent Bible, Room Bible, MCP bridge, security
- `contracts/` JSON/schema ที่ frontend/backend/runner ใช้ร่วมกัน
- `frontend/` เว็บเกม map, agent, prop, popup, dialogue
- `backend/` สมองระบบ mission, meeting, report, approval, audit
- `runner/` จุดเชื่อม Codex CLI, MCP, MT4/MT5, Telegram, VPS
- `data/runtime/` session, mission, meeting, report, audit, archive
- `data/imports/` prototype เก่าและ generated assets
- `data/exports/` report/export/backup
- `assets-source/` ภาพต้นฉบับ prompt pack source sheet
- `frontend/public/assets/` asset ที่ runtime ใช้จริง
- `scripts/` script ช่วย start, check, package, backup

## 15. Asset Naming Contract

กฎชื่อไฟล์:

- ใช้ภาษาอังกฤษตัวพิมพ์เล็ก
- ใช้ hyphen
- ห้ามเว้นวรรค
- ห้ามใช้ภาษาไทยในชื่อไฟล์ runtime
- version ต้องชัด เช่น `v001`

Agent package:

```text
agent-{role}-{variant}-{version}/
```

Walk frame:

```text
agent-{role}-{variant}-walk-{direction}-{frame_number}-192-{version}.png
```

Status frame:

```text
agent-{role}-{variant}-status-{status_slug}-192-{version}.png
```

Portrait:

```text
agent-{role}-{variant}-portrait-dialogue-{version}.png
```

ตัวอย่าง:

```text
agent-manager-exec-walk-down-01-192-v001.png
agent-manager-exec-status-waiting-approval-192-v001.png
agent-manager-exec-portrait-dialogue-v001.png
```

## 16. Database Plan

เริ่มด้วย SQLite ที่:

```text
backend/data/app.db
```

Table หลัก:

- `users`
- `agents`
- `agent_states`
- `rooms`
- `props`
- `missions`
- `tasks`
- `meetings`
- `meeting_turns`
- `reports`
- `runner_jobs`
- `approvals`
- `audit_logs`
- `artifacts`
- `archives`
- `agent_memory`

กติกา:

- Database เก็บ state และ index
- ไฟล์ใหญ่เก็บเป็น artifact path
- Raw transcript ยาวต้องสรุปก่อนแสดง
- Audit log ห้ามลบง่าย
- Secret ไม่ควรเก็บ plain text

## 17. Event And API Contract

Event สำคัญ:

- `agent.status.changed`
- `agent.walk.started`
- `agent.walk.completed`
- `mission.created`
- `mission.updated`
- `mission.completed`
- `mission.archived`
- `task.assigned`
- `meeting.started`
- `meeting.turn.added`
- `meeting.completed`
- `prop.opened`
- `prop.report.updated`
- `runner.job.created`
- `runner.job.completed`
- `runner.job.failed`
- `approval.requested`
- `approval.approved`
- `approval.rejected`
- `report.created`
- `archive.created`
- `audit.log.created`

API เบื้องต้น:

```text
GET  /api/worlds/current
GET  /api/rooms
GET  /api/agents
GET  /api/props?room_id=:room_id
POST /api/props/:prop_id/open
GET  /api/missions
POST /api/missions
GET  /api/missions/:mission_id
POST /api/missions/:mission_id/archive
GET  /api/meetings?mission_id=:mission_id
POST /api/meetings
GET  /api/reports?mission_id=:mission_id
GET  /api/approvals
POST /api/approvals/:approval_id/approve
POST /api/approvals/:approval_id/reject
POST /api/runner/jobs
GET  /api/runner/jobs/:job_id
GET  /api/archive/missions
```

## 18. Approval Gate

Action เหล่านี้ต้องรออนุมัติ:

- live trading
- placing order
- closing order
- changing EA setting on live account
- deleting files
- overwriting important files
- sending Telegram to public/customer group
- restart VPS
- restart MT4/MT5 terminal
- deploy production
- accessing secret/token
- charging customer
- publishing public content

## 19. Development Phase Plan

Phase 1:

- สร้างโครง repo
- สร้าง docs
- สร้าง Agent Bible
- สร้าง Room Bible
- ย้าย asset ที่พร้อมใช้

Phase 2:

- Command Room ใช้งานได้
- Manager เดินได้
- prop กดได้
- mission mock
- report popup
- archive mock

Phase 3:

- แสดง 8 agents
- agent statuses
- meeting mock
- inbox
- task assignment

Phase 4:

- Backend mock API
- Frontend อ่าน agents, rooms, props, missions จาก backend/contracts

Phase 5:

- Runner mock
- job queue
- audit log
- approval gate

Phase 6:

- Real local runner
- Codex CLI หรือ MCP tool แบบปลอดภัย

Phase 7:

- Multi room / Castle Hub

## 20. AI Handoff Prompt

ใช้ prompt นี้เมื่อเปิดแชทใหม่:

```text
อ่าน docs/01-agent-bible.md ก่อนเริ่มงาน

โปรเจกต์นี้คือ Metafxclub AI Agent Office / AI Pixel Agent HQ เป็นเว็บเกมพิกเซลแบบ AI Agent Visual Office ไม่ใช่ dashboard ธรรมดา

เป้าหมายคือทำให้ agent แต่ละตัวเป็น worker จริง มี mission, meeting, prop report, archive, approval gate และ backend/local runner สำหรับ Codex/MCP

ห้าม expose token, secret, Codex auth, API key หรือ MCP runner ลง frontend

ให้ยึด agent หลัก 8 ตัว: CEO, Manager Agent, EA Developer, Backtest Analyst, Optimization Agent, VPS Watch, Telegram Ops, Risk Guard

ก่อนแก้โค้ดให้บอกว่าจะกระทบ folder ไหน และต้องรักษาโครง frontend/backend/runner/data/contracts ตาม Agent Bible
```

## 21. Final Product Sentence

Metafxclub AI Agent Office คือสำนักงาน AI แบบ pixel-art ที่ทำให้ผู้ใช้เห็นงาน AI เป็นภาพ: CEO สั่ง Manager, Manager แตกงานให้ specialist, agent เดินไปทำงานที่ prop, agent ประชุมกัน, runner เรียก Codex/MCP/tool หลังบ้าน, report ถูกเก็บและเปิดดูผ่าน prop, งานเก่าถูก archive และทุก action เสี่ยงต้องผ่าน approval ก่อนทำจริง

