# รายงานตรวจรับ MetafxHQTradeGateway v2.19

วันที่ตรวจ: 27 กันยายน 2569

- Source SHA-256: `5267C06FB193A23C9CE4CEF2E8C1D02CBB4599F1331DFE31BEBD463C9B277D62`
- EX4 SHA-256: `AB880514CA8A435325D8322803A7551DB38AB2DD1FA6EE6764BB1D289F3C2DCC`
- ยืนยัน Version ใน Source ทั้ง `#property version` และ `EA_VERSION` เป็น `2.19`
- ยืนยัน Allowlist ของ Gateway Mode 3 ค่าและ Position Lifecycle Mode 4 ค่าแบบ explicit
- ยืนยัน `OnInit()`, Execution Guard และ Runtime Guard ปฏิเสธ Enum ที่ไม่รู้จัก
- ยืนยันตรวจซ้ำตรงขอบก่อน `OrderSend()` และ `OrderClose()`
- ยืนยัน Position Lifecycle บังคับ Signing ทั้ง Demo และ Live และหยุดอัตโนมัติใน Shadow/Tester/Optimizer
- ยืนยัน Position Lifecycle ใช้ Account-wide execution lock, ตรวจ Guard ซ้ำภายใต้ Lock และปล่อย Lock ทุกเส้นทางก่อนออกจากฟังก์ชัน
- Static regression `tests.test_mt4_unified_ea` ผ่าน 64 tests
- ภาพ `COMPILE_PROOF.png` แสดง Source v2.19 ที่มี SHA-256 ตรงกับ Artifact และผล `0 errors, 0 warnings, 114 msec elapsed`
- คอมไพล์ Release EX4 ใหม่จาก Source ใน Artifact โดยตรงด้วย MetaEditor command line: `0 errors, 0 warnings, 120 msec elapsed`
- ไม่ได้เปิดหรือเปลี่ยน MT4 Terminal, Inputs, Chart, บัญชี, Gateway Mode หรือ `LiveArmed`
- ไม่มีการส่ง Order หรือคำสั่งซื้อขายระหว่างการ Compile

สถานะ: `READY_VISIBLE_METAEDITOR_COMPILED`
