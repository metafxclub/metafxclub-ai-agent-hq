# รายงานตรวจระบบ Metafxclub AI Agent HQ แบบครบวงจร

วันที่ตรวจ: 8 สิงหาคม 2569
URL ภายในเครื่อง: `http://127.0.0.1:4191/frontend/index.html`

## สรุปผลตรงไปตรงมา

ระบบ Frontend, Local Bridge, Mission/Council orchestration และสัญญาการสื่อสารกับ EA ผ่านการตรวจอัตโนมัติและการตรวจหน้าเว็บจริงแล้ว ปัญหางานค้าง งานซ้ำ การส่งคำสั่งซ้ำ การแสดงสถานะเกินความจริง และหน้าจอซ้อนกันได้รับการแก้ใน Source ปัจจุบัน

อย่างไรก็ตาม **ยังไม่ถือว่าพร้อมเปิด Order บน MT4 ในขณะตรวจ** เพราะ MT4 ที่เชื่อมอยู่ยังรายงาน EA รุ่น `2.13` ขณะที่ชุดแก้ล่าสุดคือ `2.14` และ Execution Guard รายงาน `QUOTE_NOT_OBSERVED` จึงปิดทั้ง Demo Order และ Live Order แบบ Fail-closed ระบบไม่ได้ส่ง Order ระหว่างการตรวจครั้งนี้

## สิ่งที่แก้และป้องกันแล้ว

### 1. Mission และ AI Council

- ป้องกันการสร้าง Council ซ้ำเมื่อรอบเดิมยังทำงาน
- บังคับให้หนึ่งรอบมี Specialist ครบ 3 ตัวและใช้ Snapshot/Contract เดียวกัน
- ถ้าสร้าง Subtask ไม่ครบ จะ Block ทั้ง Parent และ Child ที่บันทึกไปแล้วในครั้งเดียว ไม่ปล่อยงานครึ่งชุดให้ Worker หยิบ
- ป้องกัน Race ระหว่างการสร้าง Queue, Worker claim และ Parent reconciliation
- Retry ใช้ลำดับล่าสุดจริง ไม่ย้อนกลับไปเติมหมายเลขเก่า
- Parent ที่เคย Publish Command แล้วจะไม่สร้าง Command ซ้ำ แม้ข้อมูล Ledger บางส่วนหาย
- Parent ที่ไม่มี Child หรือมี Child ไม่ครบจะถูกกู้สถานะเพียงครั้งเดียว และไม่สร้าง Audit log ซ้ำทุก Loop

### 2. สถานะบน Frontend

- แยกคำว่า “EA เชื่อมแล้ว” ออกจาก “พร้อมส่ง Order” อย่างชัดเจน
- ถ้า `executionGuardReady=false` หน้าจอจะไม่แสดงว่าพร้อมเทรด
- `QUOTE_NOT_OBSERVED` แสดงเป็นภาษาไทย พร้อมแนวทางว่าให้รอ Tick แรกหลังตลาดเปิด หรือตรวจ Market Watch, Symbol, Timeframe และ Snapshot
- Agent ที่ติดขัดแสดงสาเหตุของงานและวิธีแก้ ไม่ใช้คำว่า “ติดขัด” เปล่า ๆ
- ลบข้อความ `[TRUNCATED]` ออกจากการ์ด Agent และใช้ข้อความภาษาไทยที่อ่านรู้เรื่อง
- ป้องกันการกดเริ่ม Council ซ้ำจากหน้า Dashboard
- ใช้ Terminal/Gateway ตัวที่เลือกจริงเป็นแหล่งสถานะหลัก ลดกรณีการ์ดหนึ่งบอกเชื่อมแต่อีกการ์ดบอกไม่เชื่อม

### 3. หน้าจอและการย่อขยาย

- ตรวจ 4 แท็บหลัก: สรุปวันนี้, กราฟและบทวิเคราะห์สด, ขั้นตอนตัดสินใจ และประวัติทั้งหมด
- ตรวจ 4 แท็บย่อย: ภาพรวมสภา AI, กราฟเปล่าและโครงสร้างราคา, Technical ย้อนหลัง และข่าว/แนวโน้ม
- ที่ขนาด 800×700 แท็บหลักจัดเป็น 2×2, แท็บย่อยยังเลือกได้ และหน้าไม่ล้นแนวนอน
- ที่ขนาด 1916×932 Modal อยู่ในจอ รายการเลื่อนได้ และไม่มี Layer ทับกันแบบเดิม
- Console ของ Browser ไม่มี Error หรือ Warning ในรอบตรวจสุดท้าย

### 4. EA และ Trade Gateway

- ชุด Source ล่าสุดคือ `MetafxHQTradeGateway v2.14`
- Compile ด้วย MetaEditor ผ่าน `0 errors, 0 warnings`
- เสริมการตรวจ Symbol suffix, Stop Level, ราคา Bid/Ask, Spread, Margin, Broker session และ Error จาก Broker
- Demo mode ปฏิเสธบัญชีจริง และ Live mode ปฏิเสธบัญชี Demo
- Live ต้องมี `LiveArmed=true`, Signing Key ตรง, Guard พร้อม และบัญชีเป็น Live จริง
- Lot มาจาก Input ของ EA เท่านั้น AI เปลี่ยน Lot/Risk ไม่ได้
- คำสั่งซ้ำไม่ถูกส่งซ้ำ; กรณีผลไม่ชัดเจนหลัง Restart จะเข้า `EXECUTION_UNKNOWN` และ Quarantine แทนการเดาหรือ Retry Order

### 5. การบันทึกสถานะหน้า UI

- แก้ Race condition เมื่อ Browser หลายแท็บบันทึก `/api/ui-session` พร้อมกัน โดยครอบการอ่าน ตรวจรุ่น และเขียนด้วย Lock เดียวกัน
- การแทนที่ไฟล์บน Windows ใช้ Atomic replace พร้อมลองซ้ำแบบมีขอบเขต เฉพาะกรณี `PermissionError`; ไม่วนซ้ำไม่สิ้นสุด
- ก่อนเขียนทับจะเก็บไฟล์ `.bak` ที่ตรวจว่าเป็น JSON ถูกต้องแล้ว หากการเขียนใหม่ล้มเหลวไฟล์เดิมและไฟล์สำรองยังอ่านได้
- เพิ่ม Failure-injection ครอบคลุมการเขียนพร้อมกัน, `Access denied` ชั่วคราว, `Access denied` ต่อเนื่อง และการทำความสะอาดไฟล์ชั่วคราว
- หลัง Restart ยิงคำขอบันทึกพร้อมกัน 36 ครั้งด้วย 12 Worker ผ่านทุกคำขอ และเฝ้าระบบจริงอย่างน้อย 396.5 วินาทีโดยไม่พบ `/api/ui-session` failure หรือ `PermissionError` เพิ่ม
- จำนวน `manager.parent_refreshed` คงที่ที่ 1,289 ตลอดช่วงเฝ้าดู จึงไม่พบ Audit churn กลับมาอีก

## หลักฐานการทดสอบ

| การตรวจ | ผล |
|---|---:|
| Full repository test suite | 339/339 ผ่าน |
| Safety matrix เฉพาะ Council/Gateway/EA/Security | 148/148 ผ่าน |
| Failure-injection ของ Queue/Retry/Reconcile | 21/21 ผ่าน |
| Council/Gateway targeted suite | 271/271 ผ่าน |
| Frontend runtime-truth regression | 33/33 ผ่าน |
| UI session persistence / Windows file-lock regression | 3/3 ผ่าน |
| UI session concurrent HTTP requests | 36/36 ผ่าน |
| Post-restart soak 396.5 วินาที | 0 request failure, 0 UI-session failure, 0 PermissionError, 0 parent-refresh churn |
| Python `py_compile` | ผ่าน |
| JavaScript syntax check | ผ่าน |
| JSON integrity (ไม่รวม third-party dependencies) | 342 ไฟล์ผ่าน |
| Frontend secret scan | 0 credential assignment, 0 JWT, 0 private key |
| Browser Console รอบสุดท้าย | 0 error, 0 warning |

ชุด Safety matrix ครอบคลุม:

- เกณฑ์โหวต 1/3, 2/3 และ 3/3
- BUY/SELL ขัดแย้งกันแล้วต้อง NO TRADE
- Snapshot หมดอายุ, Digest เปลี่ยน หรือ Heartbeat เก่า
- SL/TP ผิดทิศทางหรือข้อมูลไม่ครบ
- ไม่มี Quote และ Execution Guard ไม่พร้อม
- ป้องกัน Command ซ้ำก่อนและหลัง Restart
- ACK, Fill, Outcome และ Execution Unknown recovery แบบจำลอง
- การแยก Shadow/Demo/Live, Account mode, Signature และ LiveArmed
- การป้องกัน Secret หลุดสู่ Frontend, Report และ Agent context

## สถานะจริงขณะปิดการตรวจ

| รายการ | สถานะจริง |
|---|---|
| Local Bridge | พร้อมใช้งานที่ `127.0.0.1:4191`, เวอร์ชัน 0.9.1 |
| Process หลัง Restart | PID 39988 |
| Agent roster | 10/10 ตัวและ Asset ครบ |
| EA เชื่อมกับ Local Runner | เชื่อมแล้ว |
| EA ที่ MT4 รายงาน | รุ่น 2.13 |
| โหมด EA / ประเภทบัญชี | Demo / Demo และตรงกัน |
| Symbol / Timeframe | XAUUSD / M5 |
| Fixed Lot | 0.01 จาก Input ของ EA |
| Signature | VERIFIED และ Key ตรง |
| Execution Guard | ยังไม่พร้อม |
| สาเหตุ | `QUOTE_NOT_OBSERVED` |
| Demo Order execution | ยังไม่พร้อม |
| Live Order execution | ยังไม่พร้อม |
| Active Command | ไม่มี |
| ACK ใหม่ในรอบตรวจ | ไม่มี |
| Latest historical command | ถูกปฏิเสธด้วย `SIGNAL_PRICE_DRIFT_EXCEEDED`; ไม่มี Fill |
| Council ที่กำลังทำ | 0 รอบ |
| Auto analysis | รอแท่งปิดใหม่, ใช้เกณฑ์ 1/3, ตรวจ Snapshot ทุก 5 วินาที แต่ไม่เรียก AI ซ้ำจนแท่งปิดเปลี่ยน |
| ข้อมูลวิเคราะห์ | Source 1,000 แท่ง; รอบปัจจุบันใช้ 120 แท่งปิดตามค่าที่ตั้ง |

วันที่ตรวจเป็นวันเสาร์ จึงไม่มีหลักฐาน Quote ใหม่จาก Broker ในรอบนี้ แต่ระบบไม่เดาสถานะตลาดจากวันอย่างเดียวและยังคง Fail-closed จน EA รายงาน Bid/Ask และเวลาราคาที่ตรวจสอบได้

## เหตุผลที่บาง Agent ยังขึ้น “รอแก้ปัญหา”

Agent card แสดงผลของ Task ล่าสุดที่ยังต้องดูแล ไม่ได้หมายความว่าอุปกรณ์หรือ Bridge เสียเสมอไป ตัวอย่างที่พบคือรอบ Technical ใช้จำนวนงานต่อชั่วโมงครบก่อนเปิด Codex และ Parent Council หมดเวลารอผลครบ 3 ตัว ระบบจึงหยุดรอบนั้นไว้แทนการเอาผลไม่ครบไปเทรด

การแก้ไขคือรอหน้าต่าง Rate limit รอบถัดไปหรือเริ่ม Council รอบใหม่เมื่อโควตาพร้อม รอบเก่าจะเก็บไว้เป็นหลักฐานและไม่ถูกนำกลับไปส่ง Order ซ้ำ

## ขั้นตอน Acceptance Test บัญชี Demo ที่ต้องทำต่อ

1. ปิด AutoTrading หรือเปลี่ยน EA เป็น `GATEWAY_SHADOW` ก่อนเปลี่ยนไฟล์
2. สำรอง EA รุ่น 2.13 ของ Terminal เป้าหมาย
3. วาง MQ4/EX4 รุ่น 2.14 จาก `artifacts/mt4-ai-council-ea-v2.14-broker-compat-hardening` ใน Data Folder ของ Terminal เดียวกัน
4. เปิด MetaEditor จาก MT4 ตัวเป้าหมาย, Compile ให้เห็น `0 errors, 0 warnings`, แล้ว Reload/Attach EA ใหม่
5. ยืนยันบน Dashboard ว่า EA รายงาน `2.14`, Channel ID ตรง, บัญชีเป็น Demo, `LiveArmed=false` และเริ่มที่ Shadow
6. รอ Tick ใหม่จาก Broker และตรวจให้ `Execution Guard = พร้อม` ก่อนเริ่มรอบวิเคราะห์
7. รอแท่งปิดใหม่หรือกดวิเคราะห์ใหม่เพียงหนึ่งรอบ แล้วตรวจ Snapshot, คะแนน 3 Agent, Council Quality Gate และ SL/TP
8. ใน Shadow ตรวจว่า Command ที่จำลองผ่านทุก Guard โดยไม่ส่ง Order
9. เปลี่ยนเป็น `GATEWAY_DEMO`, ใช้ Fixed Lot ต่ำ, แล้วทดสอบหนึ่งคำสั่งบนบัญชี Demo
10. ต้องเห็น Command → ACK `EXECUTED` → Ticket/Fill → Outcome ใน Dashboard และ MT4 ตรงกัน
11. ทดสอบ Kill Switch, Restart/Recovery และยืนยันว่า Command เดิมไม่ถูกส่งซ้ำ
12. เก็บหลักฐาน Demo หลายรอบและกฎเฉพาะ Broker ก่อนพิจารณา Live

## สิ่งที่ยืนยันได้และสิ่งที่ยังยืนยันไม่ได้

ยืนยันได้:

- Logic, Contract, Guard, Queue, Retry, Idempotency, UI truth และ Responsive ผ่าน Automated/Browser test
- EA v2.14 Compile ผ่านและไฟล์ MQ4/EX4 มี Hash สำหรับตรวจความถูกต้อง
- ระบบปิดการส่ง Order เมื่อ Quote, Account mode, Signature, SL/TP, Risk หรือข้อมูลรอบวิเคราะห์ไม่พร้อม

ยังยืนยันไม่ได้จนกว่าจะทำ Acceptance Test กับ Broker จริง:

- EX4 รุ่น 2.14 ถูกติดตั้งและทำงานใน MT4 ตัวที่ผู้ใช้เลือก
- Demo Order ถูก Broker รับและมี Ticket/Fill จริง
- ทุกคู่เงิน, ทุก Symbol suffix, ทุก Stop/Floating Stop Level และทุกนโยบาย Execution ของ Broker ใช้ได้เหมือนกัน
- บัญชี Live พร้อมใช้งานจริง

ดังนั้นคำตอบที่ถูกต้อง ณ ตอนนี้คือ **ระบบซอฟต์แวร์แก้และทดสอบเชิงอัตโนมัติครบแล้ว แต่ยังไม่ควรเปิด Live และยังไม่ควรประกาศว่าเทรดได้ทุก Broker/ทุกคู่เงิน จนกว่าจะติดตั้ง v2.14 และผ่าน Demo Acceptance Test หลังมี Quote สด**

## ความปลอดภัยในการตรวจครั้งนี้

- ไม่เรียก Agent/Codex วิเคราะห์รอบใหม่
- ไม่ส่ง Command ใหม่ไป EA
- ไม่ส่ง Demo หรือ Live Order
- ไม่เปลี่ยน Input ใน MT4
- ไม่แสดง Channel secret, Broker account หรือ Signing secret ในรายงาน
- ไม่ลบ Mission/Audit เดิม; แก้สาเหตุที่ทำให้ Log เพิ่มซ้ำในอนาคตแทน
