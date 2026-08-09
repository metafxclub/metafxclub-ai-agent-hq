# ห้องทำงานอุปกรณ์ 8 จุดแบบอิสระ — AI Agent HQ

เอกสารนี้อธิบายหน้าที่ของอุปกรณ์ 8 จุดและขอบเขตที่ระบบทำได้จริงในรุ่นปัจจุบัน โดย `left_analytics_console` (สภา AI Trade) และ `mission_strategy_table` (โต๊ะวางแผน Mission) ยังคงเป็นระบบเฉพาะของตัวเอง

## หลักการทำงาน

- อุปกรณ์ทั้ง 8 จุดเป็นห้องทำงานอิสระ แต่ละจุดมี Mission, Report, ประวัติ และปุ่มสั่งงานของตัวเอง
- ไม่มีอุปกรณ์ใดดึงข้อมูลจากอุปกรณ์อื่นโดยตรง และไม่มีลำดับบังคับแบบขั้นที่ 1 → 2 → 3 → 4
- เมื่อต้องการนำผลงานจากอุปกรณ์หนึ่งไปใช้อีกอุปกรณ์ ผู้ใช้ต้องเลือก Report แล้วมอบหมายให้ Agent นำส่งผ่าน Local Runner
- Backend จะสร้าง Mission ส่งต่องาน บันทึก Agent ผู้รับผิดชอบ อุปกรณ์ต้นทาง อุปกรณ์ปลายทาง Report ต้นทาง และ Audit Log ให้ครบ
- การส่งต่อ Report ไม่เท่ากับการเริ่มงานที่อุปกรณ์ปลายทาง ผู้ใช้ยังต้องเปิดอุปกรณ์ปลายทางและกดเริ่ม Mission ของอุปกรณ์นั้น
- `mission_strategy_table` เป็นข้อยกเว้นที่แสดงภาพรวม Mission ทั้ง HQ แต่ไม่เป็นตัวดึงข้อมูลแทนอุปกรณ์ปลายทาง

งานจริงทุกครั้งต้องเริ่มจาก Intent บน Frontend แล้วผ่าน Local Runner เพื่อสร้าง Mission, Audit และ Report เท่านั้น Frontend ไม่รับ Token, API Key, Cookie, Broker Password หรือ Secret

## ความสัมพันธ์กับ Custom Plugin

- Local Runner อ่านสัญญา `contracts/workflows/equipment-plugin-map.json` เพื่อเลือกขั้นตอน เจ้าของงาน ค่าเริ่มต้น ผลลัพธ์ และหลักฐานที่ต้องมี
- งานแบบคลิกเดียวในอุปกรณ์เป็น **Backend procedure ที่ปรับจากความต้องการของ Custom Plugin** ไม่ใช่การข้ามขั้นถามข้อมูลหรือเรียก Plugin เต็มแบบเงียบ ๆ
- เมื่อเลือก MT4, MT5, MQL4 หรือ MQL5 Backend จะเปลี่ยนทั้งขั้นตอนและ Plugin ต้นแบบตามแพลตฟอร์มพร้อมกัน ส่วน TradingView ไม่แสดง Plugin MT4 เป็นแหล่งอ้างอิง
- ฟิลด์ที่ Frontend ส่งได้ยึด `DASHBOARD_WORKFLOW_ACTIONS.formFields` ของ Backend เพียงแหล่งเดียว ค่า `inputPreset` ในสัญญาเป็นค่าเริ่มต้นที่ Backend เชื่อถือ ไม่ใช่สิทธิ์เพิ่มฟิลด์เอง
- หาก Plugin เต็มต้องใช้ Google Sheet, ไฟล์, Terminal, Compile หรือ Strategy Tester ระบบจะทำเฉพาะส่วนที่มี Adapter จริงและบอกส่วนที่ยังไม่เชื่อมอย่างชัดเจน

## สัญญาการทำงานจริงของ Workflow

- อุปกรณ์แต่ละจุดมีคิวเชิงตรรกะ, Mission lineage, Report, Slot Key และประวัติของตัวเอง จึงไม่ดึงงานข้ามอุปกรณ์โดยตรง Scheduler จะทยอยปล่อยงานตามเวลา **ครั้งละหนึ่ง Mission ต่อการตรวจหนึ่งรอบ** เพื่อไม่ให้ Codex และ Local Runner แย่งทรัพยากร คำว่า “คิวอิสระ” จึงไม่ได้หมายถึงรันทุกอุปกรณ์พร้อมกัน
- Mission ตามเวลาที่กำลัง `queued`, `running` หรือ `waiting_approval` จะล็อกเฉพาะคิวของอุปกรณ์/งานชนิดเดียวกัน งานของอุปกรณ์ A ที่ยังไม่จบจึงไม่ขวางอุปกรณ์ B ที่ถึงเวลา ส่วนอุปกรณ์เดิมจะไม่ถูกปล่อยงานซ้อนจนกว่า Mission เดิมพ้นสถานะทำงาน
- ตารางเวลาของเรดาร์ระบบเทรด, เรดาร์ Indicator และข่าวตลาดเป็น `OFF` โดยค่าเริ่มต้น ผู้ใช้ต้องเปิดเองก่อน ระบบจึงจะพิจารณารอบทำงาน
- ก่อน Bridge เปิดรับคำขอ Backend จะตรวจสัญญาอุปกรณ์ทั้งหมดตั้งแต่เริ่มระบบ ทั้ง Action, ฟิลด์รับเข้า, เวลา, Timezone, งานที่อนุญาตให้ตั้งเวลา และชนิดหลักฐาน หากรายการใดผิดหรือสะกดไม่ตรง Bridge จะไม่เริ่มทำงานแทนการปล่อย Workflow ที่ไม่ครบเข้า Runtime
- การเปิดตารางเวลาไม่ได้แปลว่างานจะเริ่มทันที Backend ใช้หลัก Fail-closed: ต้องพบ Scheduler thread และ Mission Worker thread, heartbeat ของทั้งคู่ต้องยังสด, Timeout Watchdog ของ Worker ต้องทำงาน, สถานะ runtime ต้องพร้อม, Full Access แบบมีระบบป้องกัน, Codex Runner ต้องพร้อม และ Rate Limit ต้องสูงกว่าค่าสำรอง จึงตั้ง `effectiveEnabled=true`; ถ้าข้อใดไม่ผ่านจะพักงานพร้อมบอกสาเหตุ
- `/api/health` จะรายงาน `degraded` แม้ไฟล์และ Dashboard Scheduler ปกติ หาก Mission Worker หยุด, อยู่สถานะ `degraded`/`blocked`, heartbeat เก่า หรือ Timeout Watchdog ตาย เพราะ Scheduler ที่สร้าง Mission ได้แต่ไม่มี Worker ปลอดภัยมารับงานยังไม่ถือว่าระบบพร้อมใช้งาน
- เมื่อ Bridge หรือเครื่องกลับมาทำงาน ระบบชดเชยได้เฉพาะ **รอบล่าสุดที่ถึงเวลาแล้วในวันเดียวกัน** และทำได้สูงสุดหนึ่งรอบต่ออุปกรณ์ต่อการตรวจหนึ่งครั้ง (`latest_due_slot_wins`) เพื่อป้องกันงานถาโถม การเพิ่งเปิดหรือแก้ตารางเวลาระหว่างวันจะไม่ย้อนรันรอบที่อยู่ก่อนเวลาบันทึก
- Namespace ของ Idempotency Key ที่ขึ้นต้นด้วย `dashboard-schedule:` สงวนให้ Backend Scheduler เท่านั้น Frontend หรือคำขอทั่วไปใช้ชื่อนี้ไม่ได้
- งานที่ Runner ตอบว่าเสร็จแล้วจะผ่านได้ต่อเมื่อส่ง `outputFields` และ `evidenceRequired` ตามสัญญา หากขาด ระบบเปลี่ยน Mission เป็น `blocked` ด้วยรหัส `workflow_output_contract_incomplete` แทนการแสดงว่าสำเร็จ
- การใส่ชื่อชนิดหลักฐานใน `evidenceKinds` อย่างเดียวไม่ถือว่าผ่าน Backend ตรวจความหมายของหลักฐานด้วย เช่น URL สาธารณะต้องมีตามจำนวน, เวลาต้องเป็น ISO timestamp ที่อ่านได้, Digest ต้องเป็น SHA-256 64 ตัว, Path ต้องเป็น Project-relative และมีไฟล์จริง, รายงาน Bias ต้องตรงกับรายชื่อมาตรฐาน 28 คู่ทุกคู่พอดีและมีแหล่งอ้างอิงสำหรับแถวที่ยืนยัน ส่วนชนิดหลักฐานที่ Backend ยังไม่มีตัวตรวจจะ Fail-closed
- ค่าผลลัพธ์แบบ Structured ใช้งบ Output ของ Mission เป็นเพดาน สูงสุด 12,000 ตัวอักษรต่อฟิลด์และสูงสุด 20,000 ตัวอักษรรวม หากเกิน Backend จะปฏิเสธผลลัพธ์และแจ้งว่าสัญญาไม่ครบโดยไม่ตัดข้อความกลาง JSON
- Report, เนื้อหาเว็บไซต์, หลักฐาน และไฟล์ที่ Agent ส่งต่อไป Mission ถัดไปถูกครอบเป็นข้อมูลอ้างอิงที่ไม่น่าเชื่อถือเสมอ Runner ห้ามทำตาม Prompt, คำสั่ง Tool หรือโค้ดที่ฝังอยู่ภายใน แม้เนื้อหาจะอ้างว่าเป็น System, ผู้ใช้ หรือ Backend
- หลักฐานจาก Adapter จริงใน `completionEvidenceRequired` เป็นข้อกำหนดคนละชั้นกับหลักฐานรายงาน ต้องรอ Adapter นั้นทำงานจริงและห้ามสร้างภาพ, ผล Compile, Backtest, Optimization หรือสถานะระบบจำลองขึ้นมาแทน
- งานอัตโนมัติทั้งสามรายการเป็นการค้นคว้าแบบ Read-only เท่านั้น Scheduler ไม่เขียนข้อมูลภายนอกและไม่ส่งคำสั่ง MT4/MT5

## รูปแบบหน้าจอที่ใช้ร่วมกัน

- เมื่อเปิดอุปกรณ์ ระบบเข้าหน้า **งานหลักของอุปกรณ์นั้นทันที** เช่น เรดาร์จะแสดงงานค้นหาระบบเทรด ไม่เปิดด้วยหัวข้อแนะนำหรือรายงานรวม
- ชื่อ รูป และคำอธิบายอุปกรณ์แสดงที่แถบซ้ายเพียงจุดเดียว หน้าเนื้อหาหลักไม่แสดงตราและชื่อซ้ำ
- การตั้งเวลา ตั้งค่า Agent และค่าควบคุมที่จำเป็นอยู่ในแถบซ้าย ไม่ปะปนกับแท็บงานหลัก
- ช่องส่งต่อ Report ผ่าน Agent อยู่ในแถบซ้าย และจะแสดงเฉพาะเมื่อมี Report ที่ Backend ยืนยันแล้วและมีเส้นทางปลายทางที่อนุญาต หากยังส่งไม่ได้ระบบจะซ่อนช่องนี้ ไม่สร้างข้อมูลทดแทน
- แท็บสุดท้ายของอุปกรณ์ทุกจุดใช้ชื่อ **ประวัติและรายงาน** สำหรับ Mission, Report, หลักฐาน และ Artifact ย้อนหลัง
- แผงรายงานรวมจะแสดงเฉพาะแท็บประวัติและรายงาน หน้าแรกจึงเหลือเฉพาะงานสำคัญ ผลวันนี้ และปุ่มเริ่มงานที่เกี่ยวข้อง
- หากยังไม่มีข้อมูล หน้าเว็บแสดงข้อความสั้น ๆ ว่ากำลังรอ Local Runner พร้อมทางเลือกที่ทำต่อได้ โดยไม่แสดงข้อความทางเทคนิคยาวในหน้าแรก

## 1. เรดาร์ระบบเทรดโลกและ EA — ห้องค้นคว้าอิสระ

แท็บ:

- ค้นหาระบบเทรด
- ค้นหา EA ใหม่
- คลังและแบบฟอร์มข้อมูล
- ประวัติและรายงาน

แถบซ้าย: ตั้งเวลา, โควตา Codex และส่งต่อผ่าน Agent เมื่อมี Report ที่ใช้ได้

ทำได้แล้ว:

- ส่ง Mission ค้นคว้าเว็บสาธารณะแบบอ่านอย่างเดียวผ่าน Codex runner
- บันทึก Report พร้อม URL หลักฐาน วันที่ และ Agent ผู้รับผิดชอบ
- แสดงโครงสร้างข้อมูลมาตรฐาน 42 ช่องสำหรับนำไปใช้กับ Google Sheet
- ตั้งเวลาค้นหาแบบอ่านอย่างเดียวได้ เวลาเริ่มต้น 09:00 น. เวลาไทย แต่สวิตช์เป็น `OFF` โดยค่าเริ่มต้น เมื่อเปิดและ Gate พร้อม Scheduler จึงสร้าง Mission, Audit และ Report จริง
- ป้องกันงานซ้ำด้วย Slot Key และ Idempotency Key; หลัง Bridge กลับมาระบบชดเชยเฉพาะรอบล่าสุดที่พลาดในวันเดียวกัน และไม่ย้อนรอบที่อยู่ก่อนเวลาที่เพิ่งเปิดหรือแก้ตาราง

ยังไม่ทำงานจริง:

- Google Sheets Adapter และการ Sync อัตโนมัติ
- Screenshot Adapter สำหรับจับภาพเว็บไซต์จริง

## 2. คลังวิจัยระบบเทรดเชิงลึก — ห้องวิจัยอิสระ

แท็บ:

- วิจัยเชิงลึก
- ผลตรวจสอบ
- แนวทางประยุกต์
- ประวัติและรายงาน

ทำได้แล้ว:

- รับ Report ที่ Agent นำส่งเข้ามาอย่างถูกต้องตามเส้นทางที่ Backend อนุญาต
- ส่ง Mission ให้ Mission Archivist ตรวจ Entry, Exit, SL/TP, Position Sizing, การแก้ไม้, ตลาด, Timeframe, เงื่อนไขพิเศษ, ความเหมาะสม และข้อจำกัด
- บันทึกสายที่มาจาก Report ต้นทางถึง Report วิจัย

ระบบต้องปฏิเสธรายงานที่ติดขัด ถูกยกเลิก ไม่ใช่ประเภทรายงานที่ปลายทางรองรับ หรือไม่มี Mission ส่งต่อโดย Agent ที่เสร็จสมบูรณ์

## 3. โรงงานสร้าง EA และ Indicator — ห้องผลิตอิสระ

แท็บ:

- สร้าง EA / Indicator
- ตรวจ Source Code
- ผล Compile
- ประวัติและรายงาน

ทำได้แล้ว:

- เลือก Report ที่ Agent นำส่งเข้าห้องผลิตและผ่านการตรวจสิทธิ์ของ Backend
- เลือก MT4/MQL4, MT5/MQL5 หรือ TradingView/Pine Script
- ส่ง Mission ให้ EA Developer สร้าง Source Code ภายใน Workspace
- ตรวจ Source Code แบบ Static และรายงานไฟล์อ้างอิงแบบ Project-relative
- ดาวน์โหลด Source ที่ Backend สร้างจริงได้จาก Report `ea_build_report` เมื่อ Output Contract และหลักฐาน Project-relative ผ่านเท่านั้น โดยระบบไม่เชื่อถือ Artifact ทั่วไปและไม่เปิดเผย Path ในเครื่อง

ยังไม่ทำงานจริง:

- MetaEditor/Compiler Adapter
- การ Compile ผ่าน MT4/MT5 หรือ TradingView อัตโนมัติ
- การติดตั้งไฟล์ลง Terminal

หน้า Compile ต้องแสดง `Coming Soon` จนกว่าจะมีหลักฐานจาก Adapter จริง

## 4. ห้องทดลอง EA — ห้องทดสอบอิสระ

แท็บ:

- Auto Backtest
- Auto Optimization
- EA Discovery
- ประวัติและรายงาน

ทำได้แล้ว:

- เลือก Source หรือ Report ที่ Agent นำส่งเข้าห้องทดลองตามรายการที่ Backend อนุญาต
- สร้าง Mission วางแผน Backtest พร้อม Platform, Symbol, Timeframe, ช่วงวันที่ และเกณฑ์ผลลัพธ์
- สร้าง Mission วางแผน Optimization พร้อม Parameter Range, Objective และกติกาป้องกัน Overfit
- สร้าง Mission วางแผน EA Discovery จากแรงบันดาลใจ เป้าหมายกำไร Drawdown และจำนวนการเทรด

ยังไม่ทำงานจริง:

- MetaTrader Strategy Tester Adapter
- Optimization Adapter
- Discovery Plugin Adapter

ระบบห้ามสร้างผลกำไร, Drawdown, Backtest หรือ Optimization จำลองแล้วแสดงว่าเป็นผลจริง

## Google Sheet Template

ไฟล์ต้นแบบอยู่ที่ `contracts/research/trading-system-sheet-template.csv` มี 42 ช่องสองภาษา ครอบคลุมแหล่งที่มา กฎเข้าออก ความเสี่ยง เงื่อนไขพิเศษ สถานะตรวจหลักฐาน การตรวจรายการซ้ำ Mission/Report lineage และหมายเหตุ

เมื่อต่อ Google Sheets ในอนาคต Credential ต้องอยู่หลัง Local Runner เท่านั้น Frontend รับได้เฉพาะ Sheet ID หรือ Alias ที่ Backend อนุญาต และต้องไม่แสดง Secret กลับมาที่หน้าเว็บ

## กติกาป้องกันงานซ้ำ

- ทุกการกดส่งงานมี Idempotency Key
- การกดซ้ำหรือ Retry คำขอเดิมต้องไม่สร้าง Mission ใหม่
- รายการค้นพบใช้ URL ที่ Normalize แล้วร่วมกับชื่อระบบ ผู้เขียน ตลาด และ Timeframe เป็นกุญแจตรวจซ้ำ
- รายการที่ยังตรวจไม่ได้ต้องแสดงว่า `ยังไม่ยืนยัน` ไม่ใช่ `ไม่ซ้ำแน่นอน`

## อุปกรณ์ชุดที่สอง: Scout, ข่าว, พัฒนา EA และสถานะ HQ

อุปกรณ์ชุดนี้ทำงานแยกจากกันเช่นเดียวกับ 4 จุดแรก: Frontend ส่งเฉพาะ Intent, Backend สร้าง Mission พร้อม Owner Agent, Event, Report และ Audit Log ผลจะกลับสู่อุปกรณ์เจ้าของงาน และจะแสดงในอุปกรณ์อื่นได้ต่อเมื่อ Agent นำส่ง Report อย่างชัดเจนเท่านั้น

### 5. เรดาร์เว็บไซต์ Indicator (`left_audit_crystals`)

แท็บ:

- ค้นหา Indicator
- หลักฐาน
- ประวัติและรายงาน

แถบซ้าย: ตั้งเวลาและโควตา Codex

ทำได้แล้ว:

- สร้าง Mission ให้ Codex MCP Operator ค้นเว็บไซต์สาธารณะแบบอ่านอย่างเดียว
- เก็บ URL วันที่ตรวจสอบ สถานะหลักฐาน และผลตรวจรายการซ้ำใน Report
- กรองแพลตฟอร์ม MT4, MT5, TradingView และหมวด Indicator
- ตั้งเวลาค้นหาแบบอ่านอย่างเดียวได้ เวลาเริ่มต้น 09:00 น. เวลาไทย โดยสวิตช์เป็น `OFF` จนกว่าผู้ใช้จะเปิด พร้อม Mission, Audit, Report และการกันงานซ้ำ

ยังเป็น `Coming Soon`:

- Screenshot Adapter ที่จับภาพหน้าเว็บไซต์จริง

### 6. ข่าวตลาดวันนี้และมุมมอง 28 คู่เงิน (`left_signal_cube`)

แท็บ:

- วิเคราะห์ข่าววันนี้
- มุมมอง 28 คู่เงิน
- แนวโน้มตามช่วงเวลา
- ประวัติและรายงาน

แถบซ้าย: ตั้งเวลา, โควตา Codex และส่งต่อผ่าน Agent เมื่อมี Report ที่ใช้ได้

ทำได้แล้ว:

- สร้าง Mission ค้นข่าวสาธารณะ พร้อมเวลา ระดับผลกระทบ คู่เงินที่เกี่ยวข้อง คำเตือนสำหรับผู้ใช้ EA และ URL อ้างอิง
- แสดงรายการมาตรฐาน 28 คู่เงินครบทุกแถว
- แยกมุมมองระยะสั้น กลาง และยาวเป็น Bullish, Bearish, Sideway หรือ `ยังไม่มีข้อมูล`
- Backend ยืนยันว่ารายการต้องเป็น 28 คู่มาตรฐานครบพอดี แต่ละแถวมี Bias ระยะสั้น/กลาง/ยาว ความเชื่อมั่น สถานะตรวจสอบ และรหัสอ้างอิงกลับไปยัง URL สาธารณะ พร้อมเวลาอัปเดตที่อ่านได้
- ไม่สร้าง Bias แทนแหล่งข่าว หากหลักฐานไม่ครบแถวนั้นจะคงสถานะรอข้อมูล
- ตั้งเวลาค้นข่าวแบบอ่านอย่างเดียวได้ เวลาเริ่มต้น 07:00, 13:00 และ 19:00 น. เวลาไทย โดยสวิตช์เป็น `OFF` จนกว่าผู้ใช้จะเปิด พร้อม Mission, Audit และ Report
- รอบข่าวอัตโนมัติไม่แอบสร้าง FX Bias ต่อเอง งาน Bias 28 คู่ยังต้องสั่งแยกเพื่อให้ตรวจหลักฐานได้ชัดเจน

ยังเป็น `Coming Soon`:

- Economic Calendar Feed โดยตรง
- Scheduler ที่ต่อ Economic Calendar โดยตรงและการสร้าง FX Bias ต่อเนื่องอัตโนมัติ

### 7. สตูดิโอพัฒนา EA (`terminal_workstation`)

แท็บ:

- พัฒนา EA
- โจทย์พัฒนา
- เป้าหมาย
- ประวัติและรายงาน

ทำได้แล้ว:

- เลือก MQL4/MQL5 จาก Approved Workspace Source Catalog หรือ Report ต้นทางที่ Backend อนุญาต
- ตรวจ Source แบบ Static, ส่งโจทย์พัฒนา และขอแนวทางเพิ่มกำไร ลด Drawdown หรือปรับจำนวน Order
- พูดโจทย์ผ่านไมโครโฟนเพื่อแปลงเป็นข้อความในเบราว์เซอร์ โดยจะส่งออกเมื่อผู้ใช้กดสร้าง Mission เท่านั้น
- แสดง Artifact ที่ Backend ตรวจสอบแล้วเป็นลิงก์ดาวน์โหลดแบบ Same-origin โดยไม่เปิดเผย Path จริง

ยังเป็น `Coming Soon`:

- Direct Import Source จาก Frontend
- Compiler/MetaEditor Adapter และการยืนยันว่า Compile ผ่านจริง
- Backtest หรือ Optimization อัตโนมัติจากอุปกรณ์นี้

### 8. ศูนย์สถานะ VPS, HQ และตั้งค่า Agent (`right_status_crystals`)

แท็บ:

- ตรวจสถานะระบบ
- HQ และ Bridge
- ประวัติและรายงาน

แถบซ้าย: ตั้งค่า Agent และโควตา Codex

ทำได้แล้ว:

- อ่านสถานะ Local Bridge, Codex Runner, MCP และ Mission Worker จาก Backend แบบ Read-only
- แสดง Mission Worker แบบ Fail-closed โดยตรวจสถานะ Worker thread, อายุ Heartbeat และ Timeout Watchdog แยกจาก Dashboard Scheduler; หากส่วนใดไม่พร้อม Health ของ Bridge จะเป็น `degraded`
- รีเฟรชสถานะโดยไม่เรียก Codex และบันทึก Mission/Report/Audit
- ตั้งค่าที่ปลอดภัย 6 รายการ: ภาษา, Model Tier, งบ Token โดยประมาณ, Timeout, Output Limit และ Rate Limit สำรอง
- Backend บังคับ Timeout ที่ 15-600 วินาทีและ Output Limit ที่ 1,000-20,000 ตัวอักษรจริง ส่วน Rate Limit สำรอง 10-80% ใช้เป็น Gate พักงานตามเวลาเมื่อโควตาต่ำกว่าค่าที่กำหนด
- งบ Token เป็นค่าแนะนำสำหรับประมาณการและ Audit (`advisory`) เท่านั้น Codex CLI ยังไม่มี Hard Token Ceiling จึงห้ามสื่อว่าค่านี้ตัดหรือหยุด Token ได้แน่นอน
- ปฏิเสธ Token, API Key, Password, Cookie, Credential, Provider Model ID และการเปลี่ยนสิทธิ์ Tool จาก Frontend

ยังเป็น `Coming Soon`:

- VPS Metrics Adapter ภายนอกสำหรับ CPU, RAM, Disk, Uptime และ Latency จริง หากยังไม่เชื่อมต้องแสดง `ยังไม่มีข้อมูล` ห้ามสร้างตัวเลขจำลอง

## Adapter ที่ยังเป็น `Coming Soon`

- `codex_mcp_portal`: Google Sheets Sync และ Screenshot จากเว็บไซต์จริง งานค้นคว้าเว็บแบบ Read-only ใช้ได้แล้ว แต่ยังไม่เขียน Sheet และไม่สร้างภาพแทน
- `left_server_racks`: Screenshot/Browser evidence สำหรับงานวิจัยเชิงลึก เมื่อยังไม่มี Adapter ให้ใช้ URL และหลักฐานข้อความที่ Backend ตรวจได้
- `right_server_racks`: MetaEditor/Compiler, Compile อัตโนมัติ และการติดตั้งไฟล์ลง MT4/MT5
- `right_tool_console`: Strategy Tester, Optimization และ Discovery runner; ปัจจุบันสร้างแผนได้ แต่สถานะสัญญายังเป็น `plan_ready_terminal_runner_not_connected` หรือ `plan_ready_discovery_runner_not_connected`
- `left_audit_crystals`: Screenshot หน้าเว็บไซต์จริงสำหรับรายการ Indicator
- `left_signal_cube`: Economic Calendar Feed โดยตรง และการต่อข่าวไปสร้าง FX Bias อัตโนมัติ
- `terminal_workstation`: Direct Import จาก Frontend, Compiler/MetaEditor และ Backtest/Optimization อัตโนมัติ
- `right_status_crystals`: VPS Metrics ภายนอกสำหรับ CPU, RAM, Disk, Uptime และ Latency

รายการข้างต้นต้องแสดงสถานะตาม Backend จริง หาก Adapter ยังไม่เชื่อม ระบบต้องคง `Coming Soon` หรือ `ยังไม่มีข้อมูล` และห้ามสร้างภาพ, ผล Compile, Backtest, Optimization หรือค่าระบบจำลองขึ้นมาแทน

การที่ Codex Runner สร้างคำอธิบาย, Source Code หรือแผนการทดสอบได้ ไม่ได้แปลว่า Adapter ภายนอกเชื่อมแล้ว สถานะ `completed` ของ Mission จะยืนยันได้เฉพาะผลลัพธ์และหลักฐานที่ Backend ตรวจได้ในขอบเขตปัจจุบัน ส่วน Google Sheets Sync, Screenshot, MetaEditor/Compiler, Strategy Tester, Optimization/Discovery runner, Economic Calendar Feed และ VPS Telemetry ยังต้องคงสถานะตามรายการ `Coming Soon` ข้างต้น

### โต๊ะวางแผน Mission (`mission_strategy_table`)

โครงเดิมยังคงอยู่และเป็นหน้ารวมงานทั้ง HQ โดยต้องแสดง Mission ID, งานแม่/งานย่อย, Owner Agent, อุปกรณ์รับรายงาน, สถานะ, เวลา, Event และ Report ที่เชื่อมกัน ผู้ใช้กดแต่ละรายการเพื่อดูรายละเอียดได้ และการกดซ้ำด้วย Idempotency Key เดิมต้องไม่สร้างงานใหม่

## วิธีส่งผลงานข้ามอุปกรณ์ผ่าน Agent

1. เปิดอุปกรณ์ต้นทาง หากมี Report ที่เสร็จสมบูรณ์และมีเส้นทางที่ Backend อนุญาต ช่องส่งต่อผ่าน Agent จะปรากฏที่แถบซ้าย
2. เลือกอุปกรณ์ปลายทางและงานที่ต้องการให้ Agent นำไปเตรียม
3. กดส่งต่อผ่าน Agent
4. Backend ตรวจประเภท Report, สถานะ Mission, เส้นทางที่อนุญาต และ Idempotency Key
5. เมื่อผ่าน ระบบสร้าง Mission ส่งต่อแบบเสร็จสมบูรณ์ บันทึกสายที่มา และให้ Agent เดินไปยังอุปกรณ์ปลายทาง
6. เปิดอุปกรณ์ปลายทางเพื่อตรวจ Report ที่รับมา แล้วกดเริ่ม Mission ของห้องนั้นเมื่อพร้อม

หากไม่มี Report ที่ถูกต้อง ช่องส่งต่อจะไม่สร้างข้อมูลทดแทนและจะแสดงว่าไม่มีรายการพร้อมส่ง
