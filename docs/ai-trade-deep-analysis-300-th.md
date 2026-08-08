# AI Trade Council — Deep Analysis 300

เอกสารนี้อธิบายข้อมูลที่หน้า `สภา AI Trade` ใช้จริง โดยแยกการอ่านข้อมูล Local ออกจากการเรียก Codex อย่างชัดเจน

## หน้าจอใน Dashboard

1. `สรุปวันนี้` — Balance, Equity, กำไร/ขาดทุน, จำนวนการเทรด และ Position จาก Snapshot ล่าสุด
2. `กราฟภาพรวม` — แท่ง OHLC และ Overlay ที่เลือกสำหรับตรวจภาพรวม
3. `Price Action` — กราฟเปล่า 300 แท่ง พร้อม Swing, แนวรับ–แนวต้าน, Trendline, Fibonacci, RSI Divergence และ MACD Divergence
4. `Technical 300` — ตาราง OHLCV และค่า Indicator รายแท่งย้อนหลัง 300 แท่ง เลือก Indicator, ช่วงข้อมูล และค้นหาได้
5. `ข่าวและแนวโน้ม` — ผลของ News Consultant ล่าสุด พร้อมผลกระทบระยะสั้น กลาง และยาวเท่าที่ Backend มีหลักฐานจริง
6. `ขั้นตอนตัดสินใจ` — ผลโหวตของ Specialist 3 ตัวและ Risk/EA Gate
7. `ประวัติทั้งหมด` — รอบวิเคราะห์และผลลัพธ์ก่อนหน้า

## ขอบเขตข้อมูล 300 แท่ง

- Local Runner ต้องได้รับแท่งที่ปิดแล้วอย่างน้อย 500 แท่ง
- ระบบคำนวณ Indicator จากข้อมูลต้นทางทั้งหมดก่อน แล้วเลือก 300 แท่งล่าสุดมาแสดงและวิเคราะห์
- หาก Snapshot มี 1,000 แท่ง ค่า `warmupBarsUsed` จะเป็น 700 แท่ง และช่วงตัดสินใจเป็น 300 แท่งล่าสุด
- ข้อมูลไม่ครบ, ลำดับเวลาไม่ถูกต้อง หรือมีแท่งน้อยกว่า 500 จะหยุดแบบ fail-closed และไม่สร้างข้อมูลจำลอง
- Snapshot เก่ายังเปิดดูและสร้างไฟล์ตรวจสอบได้ แต่จะเป็น `fresh=false` และ `decisionEligible=false`

## ข้อมูลที่ส่งให้ Specialist

### Technical Consultant

- OHLCV แบบ columnar สูงสุด 300 แท่ง
- ค่า `EMA20`, `EMA50`, `EMA200`, `RSI14`, `ATR14`, `MACD Histogram` และ `ADX14` ครบ 300 จุด
- Indicator รายละเอียด 27 fields สำหรับ 60 แท่งล่าสุด
- Summary ของ Technical 14 โมดูลยังอ้างอิงช่วงวิเคราะห์เต็ม
- หากข้อมูลต้องถูกลดขนาด `promptScope` จะระบุขอบเขตและ fallback ตามจริง

### Price Action Consultant

- OHLCV สูงสุด 300 แท่งสำหรับ Mission ปกติ
- Price Action features จาก Backend ครบตามโมดูลที่พร้อม
- เป็นผู้เสนอ SL/TP เพียงบทบาทเดียว แต่ EA เป็นผู้ควบคุม Lot และ Risk จาก Inputs

### News Consultant

- ไม่ส่ง OHLCV หรือ Indicator 300 แท่ง
- ใช้ข่าวและบริบทตลาดพร้อมแหล่งอ้างอิงตามที่ Runner หาได้
- หากผลข่าวมาจาก Snapshot คนละรอบ Dashboard ต้องแสดงว่าเป็นข้อมูลคนละ Snapshot และห้ามนำไปอ้างว่าเป็นผลสดของรอบปัจจุบัน

## Rate Limit และไฟล์ตรวจสอบ

- เปิดแท็บหรือกด `โหลดข้อมูลล่าสุด` เรียกเฉพาะ Local Runner และไม่ใช้ Codex Rate Limit
- กด `เตรียมไฟล์ Local` สร้างแพ็กเกจภายใน Workspace โดยไม่เรียก Codex
- กด `ให้ AI วิเคราะห์รอบนี้` หรือ Trigger เมื่อเกิดแท่งใหม่จึงเรียก Codex และใช้ Rate Limit
- แพ็กเกจประกอบด้วย `manifest.json`, `bars-300.csv`, `technical-300.csv`, `price-action.json` และ `local-summary.json`
- ทุกไฟล์มี SHA-256 และ Workspace-relative path; หากถูกแก้ภายหลัง ระบบหยุดและไม่เขียนทับแพ็กเกจเดิม

## การเปิดระบบหลังรีสตาร์ต Windows

- `scripts/register-bridge-autostart.cmd` เปิด Local Bridge แบบซ่อนหลังผู้ใช้เข้าสู่ Windows และตรวจซ้ำทุก 5 นาทีผ่าน Task Scheduler โดยอ่าน endpoint ที่ยืนยันไว้
- `scripts/unregister-bridge-autostart.cmd` ยกเลิก Scheduled Task และล้าง Startup shortcut รุ่นเก่าถ้ามี
- Auto-start เปิดเฉพาะ Bridge เท่านั้น ไม่เปิด Browser, MT4 หรือ MT5 และไม่เปลี่ยนพอร์ตเองเมื่อพอร์ตที่ยืนยันไม่ว่าง
