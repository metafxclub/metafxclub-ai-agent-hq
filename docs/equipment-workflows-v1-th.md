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
- เรดาร์ระบบเทรดและ Radar Website Tool เปิดอัตโนมัติวันละหนึ่งรอบเวลา 09:00 น. Asia/Bangkok แบบ Backend-owned คงที่ ผู้ใช้ปิด เปลี่ยนเวลา สั่งรันทันที หรือสร้าง Mission ทดแทนไม่ได้ ส่วนข่าวตลาดเปิดเวลา 00:00 และ 12:00 น. ตามเวลาไทย โดย Backend เป็นผู้สร้าง Mission ภายในเอง ผู้ใช้ไม่ต้องสร้างหรืออนุมัติ Mission อ่านเว็บ
- ก่อน Bridge เปิดรับคำขอ Backend จะตรวจสัญญาอุปกรณ์ทั้งหมดตั้งแต่เริ่มระบบ ทั้ง Action, ฟิลด์รับเข้า, เวลา, Timezone, งานที่อนุญาตให้ตั้งเวลา และชนิดหลักฐาน หากรายการใดผิดหรือสะกดไม่ตรง Bridge จะไม่เริ่มทำงานแทนการปล่อย Workflow ที่ไม่ครบเข้า Runtime
- การเปิดตารางเวลาไม่ได้แปลว่างานจะเริ่มทันที Backend ใช้หลัก Fail-closed: ต้องพบ Scheduler thread และ Mission Worker thread, heartbeat ของทั้งคู่ต้องยังสด, Timeout Watchdog ของ Worker ต้องทำงาน, สถานะ runtime ต้องพร้อม, Full Access แบบมีระบบป้องกัน, Codex Runner ต้องพร้อม และ Rate Limit ต้องสูงกว่าค่าสำรอง จึงตั้ง `effectiveEnabled=true`; ถ้าข้อใดไม่ผ่านจะพักงานพร้อมบอกสาเหตุ
- เกณฑ์กลางของงานอัตโนมัติคือ Codex ต้องเหลือ **มากกว่า 15%**; ที่ 15% พอดีหรือต่ำกว่าจะพักงานโดยไม่เปิด Runner และกลับมาทำต่อเมื่อยอดสูงกว่า 15%
- `/api/health` จะรายงาน `degraded` แม้ไฟล์และ Dashboard Scheduler ปกติ หาก Mission Worker หยุด, อยู่สถานะ `degraded`/`blocked`, heartbeat เก่า หรือ Timeout Watchdog ตาย เพราะ Scheduler ที่สร้าง Mission ได้แต่ไม่มี Worker ปลอดภัยมารับงานยังไม่ถือว่าระบบพร้อมใช้งาน
- เมื่อ Bridge หรือเครื่องกลับมาทำงาน ระบบชดเชยได้เฉพาะ **รอบล่าสุดที่ถึงเวลาแล้วในวันเดียวกัน** และทำได้สูงสุดหนึ่งรอบต่ออุปกรณ์ต่อการตรวจหนึ่งครั้ง (`latest_due_slot_wins`) เพื่อป้องกันงานถาโถม การเพิ่งเปิดหรือแก้ตารางเวลาระหว่างวันจะไม่ย้อนรันรอบที่อยู่ก่อนเวลาบันทึก
- Namespace ของ Idempotency Key ที่ขึ้นต้นด้วย `dashboard-schedule:` สงวนให้ Backend Scheduler เท่านั้น Frontend หรือคำขอทั่วไปใช้ชื่อนี้ไม่ได้
- งานที่ Runner ตอบว่าเสร็จแล้วจะผ่านได้ต่อเมื่อส่ง `outputFields` และ `evidenceRequired` ตามสัญญา หากขาด ระบบเปลี่ยน Mission เป็น `blocked` ด้วยรหัส `workflow_output_contract_incomplete` แทนการแสดงว่าสำเร็จ
- การใส่ชื่อชนิดหลักฐานใน `evidenceKinds` อย่างเดียวไม่ถือว่าผ่าน Backend ตรวจความหมายของหลักฐานด้วย เช่น URL สาธารณะต้องมีตามจำนวน, เวลาต้องเป็น ISO timestamp ที่อ่านได้, Digest ต้องเป็น SHA-256 64 ตัว, Path ต้องเป็น Project-relative และมีไฟล์จริง, รายงาน Bias ต้องตรงกับรายชื่อมาตรฐาน 28 คู่ทุกคู่พอดีและมีแหล่งอ้างอิงสำหรับแถวที่ยืนยัน ส่วนชนิดหลักฐานที่ Backend ยังไม่มีตัวตรวจจะ Fail-closed
- ค่าผลลัพธ์แบบ Structured ใช้งบ Output ของ Mission เป็นเพดาน ปกติสูงสุด 12,000 ตัวอักษรต่อฟิลด์; งานค้นหาระบบเทรดใช้ `systems` array ตรงตาม Nested Schema ก่อนที่ Runner จะแปลงเป็น Backend contract โดยเล็งไม่เกิน 14,000 และมีเพดาน 16,000 ตัวอักษร ทุก Profile สูงสุด 20,000 ตัวอักษรรวม และ Strict Profile ส่ง `finalMessage` แบบสรุปเพื่อไม่ทำสำเนา payload ซ้ำระหว่าง Runner กับ Bridge หากเกินระบบจะปฏิเสธผลลัพธ์โดยไม่บันทึก JSON ที่ถูกตัด
- Report, เนื้อหาเว็บไซต์, หลักฐาน และไฟล์ที่ Agent ส่งต่อไป Mission ถัดไปถูกครอบเป็นข้อมูลอ้างอิงที่ไม่น่าเชื่อถือเสมอ Runner ห้ามทำตาม Prompt, คำสั่ง Tool หรือโค้ดที่ฝังอยู่ภายใน แม้เนื้อหาจะอ้างว่าเป็น System, ผู้ใช้ หรือ Backend
- หลักฐานจาก Adapter จริงใน `completionEvidenceRequired` เป็นข้อกำหนดคนละชั้นกับหลักฐานรายงาน ต้องรอ Adapter นั้นทำงานจริงและห้ามสร้างภาพ, ผล Compile, Backtest, Optimization หรือสถานะระบบจำลองขึ้นมาแทน
- งานอัตโนมัติทั้งสามรายการเป็นการค้นคว้าแบบ Read-only เท่านั้น Scheduler ไม่เขียนข้อมูลภายนอกและไม่ส่งคำสั่ง MT4/MT5

## รูปแบบหน้าจอที่ใช้ร่วมกัน

- เมื่อเปิดอุปกรณ์ ระบบเข้าหน้า **งานหลักของอุปกรณ์นั้นทันที** เช่น เรดาร์จะแสดงงานค้นหาระบบเทรด ไม่เปิดด้วยหัวข้อแนะนำหรือรายงานรวม
- ชื่อ รูป และคำอธิบายอุปกรณ์แสดงที่แถบซ้ายเพียงจุดเดียว หน้าเนื้อหาหลักไม่แสดงตราและชื่อซ้ำ
- ตารางของเรดาร์ระบบเทรดและ Radar Website Tool แสดงในแถบซ้ายแบบอ่านอย่างเดียว ส่วนการตั้งค่า Agent และค่าควบคุมของอุปกรณ์อื่นอยู่ในแถบซ้าย ไม่ปะปนกับแท็บงานหลัก
- ช่องส่งต่อ Report ผ่าน Agent อยู่ในแถบซ้าย และจะแสดงเฉพาะเมื่อมี Report ที่ Backend ยืนยันแล้วและมีเส้นทางปลายทางที่อนุญาต หากยังส่งไม่ได้ระบบจะซ่อนช่องนี้ ไม่สร้างข้อมูลทดแทน
- แท็บสุดท้ายของอุปกรณ์ทุกจุดใช้ชื่อ **ประวัติและรายงาน** สำหรับ Mission, Report, หลักฐาน และ Artifact ย้อนหลัง
- แผงรายงานรวมจะแสดงเฉพาะแท็บประวัติและรายงาน หน้าแรกจึงเหลือเฉพาะงานสำคัญ ผลวันนี้ และปุ่มเริ่มงานที่เกี่ยวข้อง
- หากยังไม่มีข้อมูล หน้าเว็บแสดงข้อความสั้น ๆ ว่ากำลังรอ Local Runner พร้อมทางเลือกที่ทำต่อได้ โดยไม่แสดงข้อความทางเทคนิคยาวในหน้าแรก

## 1. เรดาร์ระบบเทรดโลก — ห้องค้นคว้าเฉพาะระบบเทรด

แท็บ:

- ค้นหาระบบเทรด
- คลังและแบบฟอร์มข้อมูล
- ประวัติและรายงาน

แถบซ้าย: ดูตาราง Backend คงที่ 09:00 น. Asia/Bangkok แบบอ่านอย่างเดียว, โควตา Codex และส่งต่อผ่าน Agent เมื่อมี Report ที่ใช้ได้

ทำได้แล้ว:

- ค้นคว้าเว็บสาธารณะแบบอ่านอย่างเดียวผ่าน Codex runner โดย Backend สร้าง Mission ภายในให้เองและรับเฉพาะระบบเทรด ไม่รับรายการ EA, Indicator หรือ Tool เดี่ยว
- บังคับผลลัพธ์ 3 ระบบจาก 3 ตระกูลกลยุทธ์ต่อรอบ พร้อมชื่อผู้สร้าง/นักเทรดเมื่อแหล่งสาธารณะระบุ ขั้นตอนเข้าออกแบบเรียงลำดับ การจัดการออเดอร์ ความเสี่ยง และสิ่งที่ยังไม่ทราบ
- บันทึก Report พร้อม URL หลักฐานที่ผูกกับกฎ วันที่ และ Agent ผู้รับผิดชอบ
- ให้ Backend คำนวณ Fingerprint และตรวจรายการซ้ำกับ Report ในเครื่อง
- แสดงโครงสร้างข้อมูลมาตรฐาน 42 ช่องสำหรับนำไปใช้กับ Google Sheet
- เปิดค้นหาอัตโนมัติเวลา 09:00 น. Asia/Bangkok วันละหนึ่งรอบแบบคงที่ เมื่อ Gate พร้อม Scheduler จะสร้าง Mission ภายใน, Audit และ Report จริงโดยไม่รออนุมัติ คำขอ Manual ถูกปฏิเสธก่อนสร้าง Mission และไม่ใช้โควตารอบรายวัน
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

- 1 เลือกระบบจากคลังวิจัยหรือ Google Sheets
- 2 ตรวจและยืนยัน Strategy Spec
- 3 สร้างโค้ด
- 4 ตรวจ Source Code
- 5 Compile / Validate
- 6 Visual Backtest / Logic Recheck
- 7 ไฟล์และ Report

ทำได้แล้ว:

- เลือก Record ที่ Backend ยืนยันจากคลังวิจัยเชิงลึก หรือ Sync แถวที่ผ่านเกณฑ์จากแท็บ `Deep_Research` ของ Google Sheet กลางโดยไม่รับ Credential แล้วแปลงเป็น 23 ฟิลด์ Strategy Spec ภายใน
- แสดง A-M เป็นข้อมูลแกนกลางสำหรับเขียนระบบ ได้แก่ชื่อ/ตระกูล/ตลาด/Timeframe/Entry/Exit/SL/TP/การแก้ไม้/Lot-Risk/Indicator/เงื่อนไขพิเศษ และแสดง N-W เป็นสถานะ downstream
- เลือก MT4/MQL4, MT5/MQL5 หรือ TradingView/Pine Script และยืนยัน Strategy Spec ก่อนเริ่มสร้างไฟล์
- ทำงานแบบ Manual stage-by-stage เท่านั้น หนึ่งปุ่มเลื่อนได้ไม่เกินหนึ่งขั้น ไม่มี Scheduler และไม่มี Loop สร้าง-แก้อัตโนมัติ
- สร้าง Source แต่ละเวอร์ชันใน `workspace/ea-factory/<build-id>` โดยไม่ทับเวอร์ชันเดิม พร้อมโฟลเดอร์ Source, EA_Versions, Reports, Sets, Screenshots และ Summaries
- ตรวจ Source Code แบบ Static พร้อม Signal Guard, order lifecycle, look-ahead/repaint, Money Management, error handling และ source digest
- Pine Script จบสาย execution หลัง Source validation แล้วเข้าสรุป Report โดยไม่อ้างว่าเผยแพร่หรือ Backtest บน TradingView
- MT4/MT5 ต้องเลือก Terminal ให้ตรงแพลตฟอร์มก่อน และจะถือว่า Compile/Backtest ผ่านได้เฉพาะเมื่อมีหลักฐานหน้าบ้านจาก MetaEditor/Strategy Tester ที่ผูกกับ Source digest และ Audit ของ Build เดียวกัน
- ดาวน์โหลด Source และไฟล์ผลลัพธ์ได้ผ่าน URL same-origin ที่ Backend อนุญาต โดยไม่เปิดเผย Path จริง

กติกาหยุดแบบ Fail-closed:

- หาก Google Sheet เป็น Private, คอลัมน์ไม่ครบ, Record ID ซ้ำ หรือข้อมูล A-M สำคัญขาด ระบบต้องหยุดก่อนสร้าง Build
- หากยังไม่ได้เลือก MT4/MT5 ที่ตรงแพลตฟอร์ม หรือยังไม่มีหลักฐาน MetaEditor/Visual Mode ระบบต้องแสดง `blocked` และห้ามแสดง Passed
- Process exit code, Static review, ไฟล์ `.set` หรือ `.ini` อย่างเดียวไม่ใช่หลักฐาน Compile/Backtest
- หาก Build ขั้นใดไม่ผ่าน ผู้ใช้เป็นผู้กดสร้างเวอร์ชันถัดไป ไม่มีการเปิด Loop แก้ซ้ำเอง

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

ไฟล์ `contracts/research/trading-system-sheet-template.csv` มี 42 ช่องสองภาษาและเป็น legacy template ของหน้าจอ Discovery เดิมเท่านั้น ส่วน Google Sheet กลางมีเพียง 3 แท็บและต้องใช้ schema จาก `contracts/research/world-system-sheet-template.csv`, `deep-research-sheet-template.csv` และ `indicator-ea-tool-sheet-template.csv` ตาม `docs/research-sheet-hub-setup-th.md`

Google Sheets Adapter ทำงานหลัง Local Runner เท่านั้น Credential ต้องอยู่ใน Environment ของ Backend; Frontend รับเฉพาะ Sheet URL/ID ที่โต๊ะวางแผน Mission โดย Sheet ID แสดงได้เพราะเป็นรหัสเอกสาร ไม่ใช่ Secret แต่ Token และ OAuth secret ต้องไม่แสดงกลับมาที่หน้าเว็บ Candidate ใหม่ต้องผ่าน `draft → inspect → confirmation ใน UX → activate` โดยใช้เฉพาะ `/research-sheet/inspect` และ `/research-sheet/activate` ก่อนเปลี่ยน Active revision และทั้ง 4 ระบบที่เชื่อมต้องอ้างหลักฐานอ่านของ Consumer หลัก 3 แท็บเท่านั้น: Radar ระบบโลกใช้ `World_System`, คลังวิจัยใช้ `Deep_Research`, โรงงาน EA อ่านร่วมจาก `Deep_Research`, และ Radar Website Tool ใช้ `Indicator_EA_Tool` ดูขั้นตอน, credential mode ที่รองรับจริง และ schema ที่ `docs/research-sheet-hub-setup-th.md`

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

แถบซ้าย: ดูตาราง Backend คงที่ 09:00 น. Asia/Bangkok แบบอ่านอย่างเดียวและดูโควตา Codex

ทำได้แล้ว:

- Backend สร้าง Mission ภายในให้ Codex MCP Operator ค้นเว็บไซต์สาธารณะแบบอ่านอย่างเดียวโดยไม่รออนุมัติ
- เก็บ URL วันที่ตรวจสอบ สถานะหลักฐาน และผลตรวจรายการซ้ำใน Report
- กรองแพลตฟอร์ม MT4, MT5, TradingView และหมวด Indicator
- เปิดค้นหาแบบอ่านอย่างเดียวเวลา 09:00 น. Asia/Bangkok วันละหนึ่งรอบแบบคงที่ พร้อม Mission ภายใน, Audit, Report และการกันงานซ้ำ โดยคำขอ Manual ถูกปฏิเสธก่อนสร้าง Mission

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
- ตั้งค่าที่ปลอดภัย 5 รายการ: ภาษา, Model Tier, งบ Token โดยประมาณ, Timeout และ Output Limit; เกณฑ์โควตาเป็นนโยบายกลางที่ผู้ใช้แก้ไม่ได้
- Backend บังคับ Timeout ที่ 15-600 วินาทีและ Output Limit ที่ 1,000-20,000 ตัวอักษรจริง ส่วนเกณฑ์โควตาคงที่ 15%: หยุดที่ 15% และเริ่มงานอัตโนมัติเมื่อค่าคงเหลือมากกว่า 15%
- งบ Token เป็นค่าแนะนำสำหรับประมาณการและ Audit (`advisory`) เท่านั้น Codex CLI ยังไม่มี Hard Token Ceiling จึงห้ามสื่อว่าค่านี้ตัดหรือหยุด Token ได้แน่นอน
- ปฏิเสธ Token, API Key, Password, Cookie, Credential, Provider Model ID และการเปลี่ยนสิทธิ์ Tool จาก Frontend

ยังเป็น `Coming Soon`:

- VPS Metrics Adapter ภายนอกสำหรับ CPU, RAM, Disk, Uptime และ Latency จริง หากยังไม่เชื่อมต้องแสดง `ยังไม่มีข้อมูล` ห้ามสร้างตัวเลขจำลอง

## Adapter ที่ยังเป็น `Coming Soon`

- `codex_mcp_portal`: Google Sheets Sync ใช้ Adapter กลางได้แล้วและต้องแสดงสถานะ OAuth/schema/write-readback ตาม Backend จริง; ส่วน Screenshot เต็มหน้าจากเว็บไซต์ยังไม่เชื่อมและห้ามสร้างภาพแทน
- `left_server_racks`: Screenshot/Browser evidence สำหรับงานวิจัยเชิงลึก เมื่อยังไม่มี Adapter ให้ใช้ URL และหลักฐานข้อความที่ Backend ตรวจได้
- `right_server_racks`: การควบคุม MetaEditor/Strategy Tester อัตโนมัติจะพร้อมเฉพาะเครื่องที่มี Adapter หน้าบ้านและหลักฐานตรงกับ Terminal ที่ผู้ใช้เลือก; หาก Adapter ไม่พร้อม Stage จะหยุดแบบ `blocked` ไม่สร้างผลจำลอง
- `right_tool_console`: Strategy Tester, Optimization และ Discovery runner; ปัจจุบันสร้างแผนได้ แต่สถานะสัญญายังเป็น `plan_ready_terminal_runner_not_connected` หรือ `plan_ready_discovery_runner_not_connected`
- `left_audit_crystals`: Screenshot หน้าเว็บไซต์จริงสำหรับรายการ Indicator
- `left_signal_cube`: Economic Calendar Feed โดยตรง และการต่อข่าวไปสร้าง FX Bias อัตโนมัติ
- `terminal_workstation`: Direct Import จาก Frontend, Compiler/MetaEditor และ Backtest/Optimization อัตโนมัติ
- `right_status_crystals`: VPS Metrics ภายนอกสำหรับ CPU, RAM, Disk, Uptime และ Latency

รายการข้างต้นต้องแสดงสถานะตาม Backend จริง หาก Adapter ยังไม่เชื่อม ระบบต้องคง `Coming Soon` หรือ `ยังไม่มีข้อมูล` และห้ามสร้างภาพ, ผล Compile, Backtest, Optimization หรือค่าระบบจำลองขึ้นมาแทน

การที่ Codex Runner สร้างคำอธิบาย, Source Code หรือแผนการทดสอบได้ ไม่ได้แปลว่า Adapter ภายนอกเชื่อมแล้ว สถานะ `completed` ของ Mission จะยืนยันได้เฉพาะผลลัพธ์และหลักฐานที่ Backend ตรวจได้ในขอบเขตปัจจุบัน Google Sheets Adapter กลางถือว่าพร้อมเฉพาะแท็บที่ Backend ตรวจ OAuth, schema และ write/read-back ผ่าน ส่วน Screenshot, MetaEditor/Compiler, Strategy Tester, Optimization/Discovery runner, Economic Calendar Feed และ VPS Telemetry ยังต้องคงสถานะตามรายการ `Coming Soon` ข้างต้น

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
