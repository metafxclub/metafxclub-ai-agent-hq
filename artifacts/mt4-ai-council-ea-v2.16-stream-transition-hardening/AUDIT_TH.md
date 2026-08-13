# รายงานตรวจรับ MetafxHQTradeGateway v2.16

วันที่ตรวจ: 13 สิงหาคม 2569

- Source ตรงกับ `integrations/mt4-trade-gateway/MetafxHQTradeGateway.mq4`
- MetaEditor Compile ผ่าน `0 errors, 0 warnings`
- ทดสอบ Stream isolation: Symbol suffix, Timeframe switch, Channel switch และ exactly-once ภายใน Stream เดิม
- ทดสอบ strict `streamKey` binding และ Ledger ที่มี Stream identity ไม่ตรงให้หยุดแบบ fail-closed
- ทดสอบ Account Execution Lock ครอบ Final Guard + Bar Claim + `OrderSend()` และไม่ใช้ Channel เป็นส่วนของ Lock identity
- ทดสอบ Outcome/History recovery ต้องมี Command Ledger ของ Channel นั้น แม้หลาย Channel ใช้ Magic เดียวกัน
- ทดสอบ Max Order นับจาก Managed Magic ทั้งบัญชี ไม่อ่านจำนวนจาก Selected-channel history
- ทดสอบ Account Portfolio Policy normalize/sort Magic + caps, ยอมรับหลาย EA เมื่อ Digest ตรง, ปฏิเสธ Policy ต่างกัน และล้าง stale lease หลัง crash ได้
- ทดสอบ Cursor pagination รวม Total/Has-more หลังมีประวัติหลาย Stream
- ทดสอบ Clock-domain ของ Consecutive-loss Cooldown และ Max Holding สำหรับ Broker UTC+3/UTC-5 โดยใช้ `TimeCurrent()` เทียบกับเวลา Order ของ Broker และคง UTC เฉพาะเวลาหลักฐานบน Wire
- ชุด Compile/Unit tests นี้ไม่ Deploy, Restart, Reload/Attach EA, เปลี่ยน Inputs หรือส่ง Order

ไฟล์ EX4 ต้องติดตั้งคู่กับ Source v2.16 ใน Terminal ที่ผู้ใช้เลือก แล้วทำ Preflight/Shadow QA ใหม่ก่อน Demo หรือ Live

ขอบเขตที่ยืนยันคือ Windows User/`FILE_COMMON` เดียวกันเท่านั้น; ไม่มี Distributed Lock ข้าม VPS และบัญชีเดียวกันต้องมี Active Execution Owner เพียง VPS เดียว
