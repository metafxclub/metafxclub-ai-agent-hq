# รายงานตรวจรับ MetafxHQTradeGateway v2.18

วันที่ตรวจ: 31 สิงหาคม 2569

- Source SHA-256: `E053CD85E0F252E8DCC42C334D17EB9A7F0C26DE4C42A38ABB4B6D45C9C204DA`
- EX4 SHA-256: `8961E60D128D8755DE9999AFFF00FD03FA91359AF48E33ADED41516AE936A181`
- ยืนยัน Version ใน Source ทั้ง `#property version` และ `EA_VERSION` เป็น `2.18`
- ยืนยัน Allowlist ของ Gateway Mode 3 ค่าและ Position Lifecycle Mode 4 ค่าแบบ explicit
- ยืนยัน `OnInit()`, Execution Guard และ Runtime Guard ปฏิเสธ Enum ที่ไม่รู้จัก
- ยืนยันตรวจซ้ำตรงขอบก่อน `OrderSend()` และ `OrderClose()`
- ยืนยัน Position Lifecycle บังคับ Signing ทั้ง Demo และ Live และหยุดอัตโนมัติใน Shadow/Tester/Optimizer
- ยืนยัน Position Lifecycle ใช้ Account-wide execution lock, ตรวจ Guard ซ้ำภายใต้ Lock และปล่อย Lock ทุกเส้นทางก่อนออกจากฟังก์ชัน
- Static regression `tests.test_mt4_unified_ea` ผ่าน 53 tests
- เปิด Source สำเนาในโฟลเดอร์ Build แยกและ Compile ด้วย MetaEditor ที่อยู่ข้าง MT4 ตัวเดียวที่กำลังทำงาน
- ภาพ `COMPILE_PROOF.png` แสดง Source v2.18 และผล `0 errors, 0 warnings, 126 msec elapsed`
- คอมไพล์ Release จาก Source ที่ Hash ตรงกับ Integration ด้วย MetaEditor แบบมองเห็นได้จริง
- MT4 เดิมยังเปิดอยู่ และไม่ได้แก้ Inputs, Chart, บัญชี, Gateway Mode หรือ `LiveArmed`
- ไม่มีการส่ง Order หรือคำสั่งซื้อขายระหว่างการ Compile

สถานะ: `READY_VISIBLE_METAEDITOR_COMPILED`
