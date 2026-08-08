# MT4 Read-only Snapshot Adapter

ไฟล์ `MetafxHQReadOnlySnapshot.mq4` อ่านข้อมูลจากกราฟ MT4 ที่ผู้ใช้เลือก แล้วเขียน Snapshot ลง `MetaQuotes\Terminal\Common\Files` เพื่อให้ Local Runner อ่านเท่านั้น

สิ่งที่ Adapter นี้ทำ:

- อ่านแท่งราคาที่ปิดแล้วได้ 20–1,000 แท่ง (`SnapshotBars`) โดยค่าเริ่มต้นยังเป็น 240 แท่ง
- การเพิ่มเป็น 500 หรือ 1,000 แท่งเพิ่มขนาด Snapshot แต่ไม่ทำให้ Codex ถูกเรียกทุก 5 วินาที; Backend ใช้หน้าต่างเต็มเพื่อคำนวณ และเรียกวิเคราะห์เมื่อเกิดแท่งปิดใหม่ตามการตั้งค่า
- อ่าน Symbol, Timeframe, Bid, Ask และ Spread
- สรุปกำไรที่ปิดแล้วของวันตามเวลา Broker และกำไร/ขาดทุนลอยตัว
- สรุปจำนวน Position โดยไม่ส่งเลขบัญชี, Broker Server หรือ Ticket
- อัปเดตไฟล์ทุก 2–60 วินาทีตามค่าที่ตั้ง

สิ่งที่ Adapter นี้ไม่ทำ:

- ไม่ใช้ DLL
- ไม่เปิด ปิด หรือแก้ไข Order
- ไม่เปิดหรือควบคุม MT4 ให้อัตโนมัติ
- ไม่ส่ง Token, Password, Cookie, API Key หรือข้อมูล Login ไป Frontend

## วิธีติดตั้งแบบมองเห็นได้

1. ใน AI Agent HQ เปิด `AI Trade Council` แล้วค้นหาและเลือก MT4 เป้าหมาย
2. คัดลอก `Candidate ID` ที่ขึ้นต้นด้วย `mtc-`
3. เปิด MT4 เครื่องนั้นด้วยตนเอง แล้วเปิด `File > Open Data Folder`
4. วาง `MetafxHQReadOnlySnapshot.mq4` ใน `MQL4\Indicators`
5. เปิด MetaEditor จาก MT4 และ Compile ไฟล์ ต้องตรวจให้เห็นว่าไม่มี Error
6. กลับ MT4 แล้วลาก Indicator ไปไว้บนกราฟที่ต้องการ เช่น XAUUSD H4
7. ตั้ง `SnapshotChannel` ให้ตรงกับ Candidate ID จาก HQ ทุกตัวอักษร
8. เปิด HQ แล้วตรวจสถานะ `อ่านสถานะการเทรดแบบ Read-only` ระบบควรเปลี่ยนเป็นพร้อมภายในประมาณ 5–20 วินาที

การเปลี่ยน Symbol หรือ Timeframe ให้เปลี่ยนบนกราฟ MT4 ที่ติด Indicator อยู่ Snapshot รอบถัดไปจะสะท้อนค่าที่เปลี่ยนโดยอัตโนมัติ

> การมี Snapshot ไม่ได้เปิดสิทธิ์ซื้อขายจริง AI Trade Council รุ่นนี้วิเคราะห์และบันทึกรายงานเท่านั้น
