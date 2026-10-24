# MT5 Gateway 1.07 — หลักฐานคอมไพล์แบบแยก

MetaEditor 5.0.0.6230 ที่มีลายเซ็นถูกต้อง คอมไพล์ source ที่ระบุ hash แบบ portable CLI ใน workspace แยก ได้ 0 errors / 0 warnings, X64 Regular, 11603 ms ไฟล์ EX5 อยู่ใน integrations/mt5-trade-gateway และผูก source/binary/compiler/log hash ใน MANIFEST.json

COMPILE_LOG.log เป็น log จริงที่แทน absolute source path ด้วยชื่อไฟล์เพื่อเผยแพร่; เก็บ hash ของ log ต้นฉบับใน nativeLogSha256 ไม่อ้างภาพหน้าจอหรือ exit code อย่างเดียวว่า Compile ผ่าน

แพ็กเกจนี้รวม source และ verified binary ค่าเริ่มต้นยังเป็น Shadow ไม่ติดตั้ง EA ลง MetaTrader ไม่ attach/reload ไม่เปลี่ยน Inputs/Algo Trading และไม่ส่งคำสั่งเทรด หลักฐานนี้ไม่ยืนยัน Demo/Live execution หรือผลกำไร
