# รายงานตรวจรับ MetafxHQTradeGateway v2.14

วันที่ตรวจ: 8 สิงหาคม 2569

ขอบเขตการตรวจครั้งนี้คือ Source, สัญญาไฟล์ EA ↔ Local Runner, Unit/Integration Test และการ Compile แบบออฟไลน์เท่านั้น ไม่มีการส่ง Order, ไม่แตะบัญชี Demo/Live และไม่ได้ติดตั้งทับ EA ใน MT4 ของผู้ใช้

## ผลตรวจตามหัวข้อ

| หัวข้อ | ผล | หลักฐาน/พฤติกรรม |
|---|---|---|
| Channel | ผ่านเชิงโค้ด | ต้องขึ้นต้น `mtc-`, ใช้อักขระปลอดภัย, มี Channel-owner lock และแยกโฟลเดอร์ต่อ Channel |
| Signing Key | ผ่านเชิงโค้ด | HMAC-SHA256 Self-test; Shadow/Demo ใช้ Active Key ได้และ Pin เป็น Optional; Live ต้อง Pin `TrustedSigningKeyId` ให้ตรงและ Fail-closed |
| Demo/Live gate | ผ่านเชิงโค้ด | Demo mode ปฏิเสธบัญชีจริง; Live mode ปฏิเสธบัญชี Demo และต้อง `LiveArmed=true` |
| ไฟล์สื่อสาร | ผ่าน | ใช้ `FILE_COMMON` เท่านั้น ไม่ใช้ `WebRequest()` และไม่ต้อง Allow URL |
| Heartbeat/Quote | ผ่านเชิงโค้ด | ตรวจ Signed Heartbeat, ID, TTL, Local Tick freshness, `MODE_TIME`, Bid/Ask และ Spread |
| Signed Command | ผ่านเชิงโค้ด | ตรวจ Envelope ก่อนอ่าน Inner JSON และตรวจ HMAC ซ้ำตรงขอบก่อนส่งคำสั่ง |
| Replay/Idempotency | ผ่านเชิงโค้ด | Ledger ของ `commandId`/`idempotencyKey`, `EXECUTING` ก่อนส่ง, คำสั่งซ้ำไม่ส่งอีก และไม่เขียนทับ Ledger ต้นฉบับ |
| Snapshot/แท่งปิด | ผ่านเชิงโค้ด | ตรวจ Snapshot ID/เวลา, แท่งปิดล่าสุด `iTime(...,1)`, ราคาอ้างอิง และ One-attempt-per-bar |
| Symbol suffix | เสริมใน v2.14 | ชื่อฐาน เช่น `XAUUSD` รองรับ suffix สั้นของ Broker แต่คำสั่งต้องตรงชื่อเต็มของกราฟ เช่น `XAUUSD.m` |
| Timeframe | ผ่านเชิงโค้ด | รองรับเฉพาะ Allowlist มาตรฐาน M5, M15, M30, H1, H4, D1, W1, MN1 และต้องตรงกราฟ |
| Lot | ผ่านเชิงโค้ด | Lot มาจาก EA เท่านั้น ตรวจ Min/Max/Lot Step และเพดาน Portfolio; AI ใส่ Field sizing ไม่ได้ |
| SL/TP | เสริมใน v2.14 | Normalize ตาม Digits, ตรวจ Stop Level, BUY ใช้ Ask/Bid ถูกฝั่ง, SELL ใช้ Bid/Ask ถูกฝั่ง และตรวจ Reward/Risk |
| Margin/Market | เสริมใน v2.14 | ตรวจ Symbol trade flag, Broker session, Free Margin, Projected Margin; แยกเหตุผล Market Closed/Trade Disabled/Off Quotes/Requote โดยไม่ Retry |
| Restart/Recovery | ผ่านเชิงโค้ด | Persist `EXECUTING`, Reconcile ด้วย Magic + Comment + Symbol, ผลไม่ชัดเป็น `EXECUTION_UNKNOWN` ไม่เดาหรือส่งซ้ำ |
| ACK/Fill/Outcome | ผ่านเชิงโค้ด | ACK v3, Post-order verification และ Outcome `OPEN/CLOSED`; `EXECUTED` ต้องยืนยัน Ticket/ราคา/SL/TP/Magic/Comment ผ่าน |
| EA หลุดจากกราฟ | เสริมใน v2.14 | `init-status.json` เก็บสาเหตุ OnInit fail และ OnDeinit เก็บรหัสที่หยุดล่าสุด |
| Compile | ผ่านแบบออฟไลน์ | MetaEditor: `0 errors, 0 warnings`; ไม่รวม Raw compile log ในชุดแจกเพื่อไม่แนบ Path ของเครื่องผู้พัฒนา |

## ชุดทดสอบ

- ชุด `unittest discover -s tests -p "test_*.py"` ทั้ง Repository ล่าสุด: 427 tests ผ่านทั้งหมด
- Static contract ยืนยันว่า `ExecuteCommand` มี `OrderSend()` จริงเพียงหนึ่งจุด และไม่มี Automatic Retry

## สถานะไฟล์ที่ติดตั้งในเครื่องขณะตรวจ

พบ EA ใน Terminal Data Folder หนึ่งชุด แต่ยังเป็น Source/EX4 รุ่น v2.13:

- MQ4 SHA-256: `C70CB9C2C5F7D005422CEED870431A20C32810365C1139679333890C0049966B`
- EX4 SHA-256: `4F736B62A03B477C27A27FB2BB104B0E120D824E3B336B13D35246517D417989`

จึงยังไม่ถือว่า MT4 ปัจจุบันใช้การแก้ v2.14 จนกว่าจะติดตั้งไฟล์คู่จากโฟลเดอร์นี้ใน Terminal ที่ผู้ใช้เลือก แล้ว Compile/Reload/Attach ใหม่

## ข้อจำกัดที่ยังต้องยืนยันกับ MT4/Broker จริง

- ยังไม่ได้พิสูจน์การรับ Order ของ Server, Market hours, Stop/Floating Stop Level, Symbol mapping และ Execution policy ของ Broker เป้าหมาย
- Broker แบบ ECN ที่ไม่ยอมรับ SL/TP ในคำสั่งเปิดจะถูกบล็อกแบบ Fail-closed; รุ่นนี้ไม่เปิด Position เปล่าแล้วค่อย Modify
- EA หนึ่งตัวผูก Symbol/Timeframe เดียว ต้องแยก EA/Channel สำหรับกราฟอื่น
- Risk จากประวัติบัญชีขึ้นกับข้อมูลที่ MT4 โหลดไว้ ควรเลือก Account History = All History
- ผล Compile แบบออฟไลน์ไม่แทนการ Compile แบบมองเห็นใน MetaEditor ของ Terminal เป้าหมาย
- ยังไม่สามารถยืนยันคำว่า “ทุก Broker/ทุกคู่เงิน/บัญชีจริงเปิดได้แน่นอน” โดยไม่มี Shadow และ Demo evidence จาก Broker นั้น
