# รายงานตรวจรับการ Compile MetafxHQTradeGateway MT5 v1.03

วันที่ตรวจรับ: 9 ตุลาคม 2569

- Source ที่ตรวจคือ `integrations/mt5-trade-gateway/MetafxHQTradeGateway.mq5` ขนาด 241508 bytes, SHA-256 `42CB8A410DDE98E608307C12FC272513ED30F1E23F5B3267F7DCDF128A69175C`
- ใช้ MetaEditor64 5.0.0.6230 ของ MT5 Terminal ที่เลือก และ Compile แบบมองเห็นบนหน้าจอจริง
- ผลใน Toolbox คือ `0 errors, 0 warnings` ใช้เวลา 9358 ms เป้าหมาย CPU `AVX2+FMA3`
- ตรวจ Source hash ซ้ำหลัง Compile แล้วไม่เปลี่ยน และไม่ได้แก้หรือ Save Source ภายใน MetaEditor
- EX5 ที่สร้างใหม่ใน Data Folder ของ Terminal มีขนาด 287818 bytes, SHA-256 `8E221E7A860BDA9778AA4B57E21F9AC043D0084C43B2F1784C68043616F27FBA`
- ภาพ `COMPILE_PROOF.png` แสดงชื่อไฟล์ v1.03 และผล Compile จริง SHA-256 `D13FE16FE8E60C35A8F32AA261D49F44E8B9716628B5F9ED3DF783CAE7E19332`
- ชุดทดสอบ Static/Contract ของ MT4/MT5 ผ่านรวม 153 tests โดยไม่มี failure, error หรือ skipped
- Release ของ MT5 ยังคงเป็นแบบ Source-only จึงไม่บรรจุ EX5 ลง GitHub/Release; ผู้ติดตั้งต้อง Compile Source บน MetaEditor64 ของ MT5 เป้าหมาย
- ระหว่างตรวจ MT5 Demo ยังคงเปิดอยู่ ไม่มีการติด EA ลงกราฟ เปลี่ยน Algo Trading หรือส่ง Order/คำสั่งซื้อขาย
- หลักฐานนี้ยืนยันระดับ Source และ Compile เท่านั้น ยังไม่ใช่หลักฐาน Demo execution หรือ Live execution และไม่ใช่การรับประกันผลกำไร

สถานะ: `COMPILE_VERIFIED_SOURCE_ONLY`
