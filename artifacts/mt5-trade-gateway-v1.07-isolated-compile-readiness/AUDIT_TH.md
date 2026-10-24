# ขอบเขตหลักฐาน

ซอร์สรุ่น 1.07 ถูกคง byte เดิมตาม audit วันที่ 24 ตุลาคม 2569 และคอมไพล์ใหม่ด้วย compiler สำเนาที่ตรวจลายเซ็น/แฮชแล้ว Process exit code คือ 1 แต่ log จบด้วย 0 errors, 0 warnings และมี binary ใหม่หลังเริ่มคอมไพล์ จึงใช้ hash และผล compiler เป็นหลักฐาน ไม่แปลง exit code เป็นความสำเร็จโดยลำพัง

หลักฐาน before/after ส่วนตัวตรวจว่า original editor/MT5 processes และไฟล์ที่ใช้งานเดิมไม่เปลี่ยน; ไฟล์ส่วนตัวซึ่งมี paths/process IDs ไม่รวมใน release ไม่มีการทดสอบ attach หรือส่งคำสั่งซื้อขายในรอบนี้
