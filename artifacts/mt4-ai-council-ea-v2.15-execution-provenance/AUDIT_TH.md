# รายงานตรวจรับ MetafxHQTradeGateway v2.15

วันที่ตรวจ: 12 สิงหาคม 2569

- Source ตรงกับ `integrations/mt4-trade-gateway/MetafxHQTradeGateway.mq4`
- Compile ผ่าน `0 errors, 0 warnings`
- Unit/contract tests ครอบคลุม Slippage warning, Ticket Map, `[tp]`/`[sl]`, ledger migration, exact reconciliation, startup backfill แบบ bounded/fail-closed, Atomic write retry และ Closed-outcome idempotency
- Recovery ACK เก็บค่า Slippage, Comment และเวลา ACK เดิมไว้ ไม่ใช้ค่า `0` จากการกู้หลัง Restart ไปทับหลักฐาน Execution เดิม
- Build transcript ที่ตัดเฉพาะ Absolute path ของเครื่องออกอยู่ใน `BUILD_LOG.txt`
- การ Compile และทดสอบไม่ได้ส่ง Order, ไม่เปิด Live และไม่เปลี่ยน Inputs ของ EA

ไฟล์ EX4 ต้องถูกติดตั้งคู่กับ Source v2.15 ใน Terminal ที่ผู้ใช้เลือก และต้อง Reload/Attach EA จึงจะโหลดโค้ดใหม่
