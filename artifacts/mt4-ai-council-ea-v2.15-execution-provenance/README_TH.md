# MetafxHQTradeGateway v2.15 — Execution Provenance

ชุด Compile สำหรับ MT4 ที่แก้การติดตาม Order จริงและประวัติการเปิดออเดอร์

- Ticket, Symbol, ฝั่ง, Lot, Magic, SL, TP และ Comment เป็นหลักฐานตัวตน Order
- Slippage เกิน Input แสดงเป็นคำเตือนคุณภาพ ไม่เปลี่ยน Order ที่เปิดจริงเป็น `EXECUTION_UNKNOWN`
- เก็บ `ticket → commandId` เพื่ออ่านผลปิด TP/SL เมื่อ Broker เติม `[tp]` หรือ `[sl]`
- ตอนเริ่ม EA จะตรวจ ACK `EXECUTED` เก่าแบบจำกัดไม่เกิน 256 ไฟล์ และสร้าง Ticket Map/Outcome เฉพาะเมื่อ Ticket, Magic, Symbol, ฝั่ง, Lot, ราคาเปิด, SL, TP และ Comment ตรงทั้งหมด
- หลักฐานที่กำกวมหรือไม่ตรงจะถูกข้ามแบบ fail-closed และไม่มีการส่ง Order ซ้ำ
- การเขียนไฟล์แบบ Atomic retry สูงสุด 3 ครั้งพร้อม Backoff และแสดง `GetLastError`/จำนวนครั้งที่ล้มเหลวต่อเนื่องบนกราฟ
- Outcome ที่ปิดแล้วและข้อมูลไม่เปลี่ยนจะไม่ถูกเขียนซ้ำทุก 5 วินาที
- ไม่ Retry และไม่ส่ง Order ซ้ำจากกระบวนการกู้สถานะ

ผล Compile ด้วย MetaEditor ของ RoboForex MT4 เมื่อ 12 สิงหาคม 2569:

```text
Result: 0 errors, 0 warnings, 98 msec elapsed
```

ก่อนใช้งานให้ตรวจ `SHA256SUMS.txt` แล้วทดสอบ Shadow/Demo ตาม `integrations/mt4-trade-gateway/README_TH.md`; ชุดนี้ไม่เปิด Live Trading ให้อัตโนมัติ
