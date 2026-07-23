# Prompt ให้ Codex ติดตั้งและยืนยัน Local Endpoint

คัดลอกข้อความด้านล่างไปสั่ง Codex พร้อมแนบลิงก์ GitHub Release ของ Metafxclub AI Agent HQ ผู้ใช้ส่งคำขอครั้งเดียว และตอบยืนยัน URL อีกหนึ่งครั้งก่อนเริ่มติดตั้ง

```text
ช่วยติดตั้ง Metafxclub AI Agent HQ จาก GitHub Release ลิงก์นี้บนเครื่อง Windows ของผมให้พร้อมใช้งาน:

[วางลิงก์ GitHub Release ที่นี่]

ให้ทำตามขั้นตอนนี้อย่างเคร่งครัด

1. อ่าน AGENTS.md, README.md และ STUDENT-QUICKSTART-TH.md จาก Release ก่อน
2. ตรวจ SHA-256 ถ้ามีไฟล์ Checksum แล้วแตก ZIP ไปยังโฟลเดอร์ชั่วคราว ห้ามรันจากใน ZIP
3. ก่อนติดตั้ง หยุด Bridge คัดลอกไฟล์ หรือสร้าง Python environment ให้เรียก:
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -ListAvailableEndpoints
4. นำ Local URL ที่ผลลัพธ์ระบุว่า available=true มาเสนอให้ผม 3 ตัวเลือก แล้วหยุดรอให้ผมเลือกก่อน
5. อธิบายด้วยภาษาง่าย ๆ ว่า IP จะเป็น 127.0.0.1 เหมือนกันทุกตัว เพราะเปิดเฉพาะเครื่องนี้ สิ่งที่เลือกคือหมายเลข Port เช่น 4186
6. เมื่อผมเลือกแล้ว ให้ตรวจว่าพอร์ตนั้นยังว่าง จากนั้นเรียก:
   .\1-INSTALL-HQ.bat -Port PORT_ที่ผมเลือก -EndpointConfirmed
7. ห้ามเปลี่ยนไปใช้ Port หรือ URL อื่นเอง หากพอร์ตถูกแย่งระหว่างติดตั้ง ให้หยุดและกลับมาเสนอ URL ว่างชุดใหม่
8. หลังติดตั้ง ให้อ่าน URL และ health_url จาก data/runtime/bridge-endpoint.json ห้ามเดาเลข Port และต้องตรวจว่า Health ตอบ ok=true, status=ready, host=127.0.0.1 และ Port ตรงกัน
9. เรียก scripts/check-codex-readiness.cmd เพื่อตรวจ Codex และ Rate Limit ของบัญชีที่ Login อยู่ใน Windows User เครื่องนี้
10. ถ้าขึ้น auth_required ให้แจ้งว่าต้อง Login ด้วยบัญชีของนักเรียนเอง ห้ามอ่าน คัดลอก หรือแสดง Token, Cookie, API key, Auth file หรือข้อมูลบัญชี
11. ถ้าขึ้น config_error ให้รายงานว่า Codex CLI มีค่า Config ที่ไม่รองรับ ห้ามแก้โดยเดาหรือคัดลอก Config จากเครื่องอื่น
12. เมื่อ Health พร้อม ให้เปิด URL ที่ยืนยันแล้ว และรายงานเป็นภาษาไทยเฉพาะ: เวอร์ชัน, ตำแหน่งติดตั้ง, URL, Health, สถานะ Codex และ Rate Limit

กติกาความปลอดภัย:
- Local Bridge ต้องใช้ 127.0.0.1 เท่านั้น ห้ามใช้ 0.0.0.0, LAN IP หรือ Public IP
- ห้ามเปิด Firewall, Port Forwarding หรือเปิด HQ ออกสู่อินเทอร์เน็ต
- ห้ามปิด Process อื่นเพียงเพราะใช้ Port เดียวกัน
- เริ่มในโหมด Local/Demo ห้ามเปิด Live Trading, ส่ง Telegram จริง หรือ Deploy จริงระหว่างติดตั้ง
- Rate Limit ต้องมาจากบัญชี Codex ของผู้ใช้เครื่องนั้นเท่านั้น และห้ามพยายาม bypass หรือ reset limit
```

หลักการสำคัญ: ระบบไม่สุ่ม IP โดยเด็ดขาด เพราะ `127.0.0.1` คือที่อยู่เฉพาะเครื่องและปลอดภัยกว่า ระบบเสนอเฉพาะหมายเลข Port ที่ตรวจว่าว่าง ณ เวลานั้น และจะใช้ Port นั้นต่อเมื่อผู้ใช้ยืนยันแล้วเท่านั้น
