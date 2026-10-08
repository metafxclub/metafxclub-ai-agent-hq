# MT5 v1.03 Visible Compile Readiness Evidence

โฟลเดอร์นี้เก็บหลักฐานว่า Source ปัจจุบันของ `MetafxHQTradeGateway.mq5` ผ่าน Visible Compile ด้วย MetaEditor64 ที่จับคู่กับ MT5 Demo Terminal แล้ว

ชุดหลักฐานประกอบด้วย:

- `COMPILE_PROOF.png` — ภาพ Toolbox ที่แสดง `0 errors, 0 warnings`
- `MANIFEST.json` — Source hash, Compiler, เวลา Compile และข้อจำกัดของหลักฐาน
- `BUILD_LOG.txt` — สรุปผล Compile และ Static/Contract tests
- `AUDIT_TH.md` — รายงานตรวจรับภาษาไทย
- `SHA256SUMS.txt` — checksum ของไฟล์หลักฐานทุกไฟล์ในโฟลเดอร์นี้ ยกเว้นตัวมันเอง

ไม่มีไฟล์ `.ex5` ในโฟลเดอร์นี้โดยตั้งใจ เพราะ Release ของ MT5 ใช้นโยบาย Source-only และต้อง Compile บน MetaEditor64 ของ Terminal เป้าหมาย
