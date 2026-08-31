# MetafxHQTradeGateway v2.18 — Enum Fail-closed

ชุด Release นี้ประกอบด้วย Source และ EX4 ที่ตรวจ Compile แบบมองเห็นได้จริง แล้ว Compile ซ้ำจาก Source ที่มี Hash ตรงกับ Integration ด้วย MetaEditor โดยทั้งสองรอบเป็น `0 errors, 0 warnings`

สิ่งที่เปลี่ยนใน v2.18:

- `GatewayMode` ยอมรับเฉพาะ `GATEWAY_SHADOW`, `GATEWAY_DEMO`, `GATEWAY_LIVE`
- `PositionLifecycleMode` ยอมรับเฉพาะ `LIFECYCLE_SLTP_ONLY`, `LIFECYCLE_MAX_HOLDING`, `LIFECYCLE_SESSION_CLOSE`, `LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE`
- ค่า Enum อื่นจากไฟล์ SET ที่ถูกแก้ไขจะหยุด `OnInit()` ด้วย `GATEWAY_MODE_INVALID` หรือ `POSITION_LIFECYCLE_MODE_INVALID`
- ตรวจ Mode ซ้ำใน Runtime Guard และตรงขอบก่อน `OrderSend()`/`OrderClose()` เพื่อหยุดแบบ fail-closed
- การปิด Order ตาม Position Lifecycle ตรวจ Signing ซ้ำทั้ง Demo และ Live ก่อนถึง `OrderClose()`; ถ้า Signing ไม่พร้อม EA จะไม่ปิด Order
- Position Lifecycle ใช้ Account-wide execution lock ก่อนตรวจ Guard รอบสุดท้ายและก่อน `OrderClose()` เพื่อป้องกันหลาย EA instance แข่งกับ Risk Guard/OrderSend บัญชีเดียวกัน
- Shadow, Strategy Tester และ Optimizer ไม่อนุญาตให้ Position Lifecycle ปิด Order อัตโนมัติ
- `ModeName()` และ `LifecycleModeName()` รายงานค่าที่ไม่รู้จักเป็น `invalid`/`INVALID` ไม่แปลงเป็น Shadow หรือ SLTP-only

หลักฐานตรวจรับ:

- Source SHA-256: `E053CD85E0F252E8DCC42C334D17EB9A7F0C26DE4C42A38ABB4B6D45C9C204DA`
- EX4 SHA-256: `8961E60D128D8755DE9999AFFF00FD03FA91359AF48E33ADED41516AE936A181`
- MetaEditor: `5.0.0.2418`
- Compile: `0 errors, 0 warnings`
- ภาพหลักฐาน: `COMPILE_PROOF.png`
- Static regression: `53/53` ผ่าน

ค่าเริ่มต้นยังเป็น `GATEWAY_SHADOW` และ `LiveArmed=false` การติดตั้ง artifact ไม่ได้เปิด Demo/Live และไม่ได้อนุญาตให้ Frontend หรือ AI เปลี่ยน Inputs ของ EA
