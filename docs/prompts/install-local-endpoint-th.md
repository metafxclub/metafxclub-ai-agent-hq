# Prompt ให้ Codex ติดตั้งและยืนยัน Local Endpoint

หากต้องการให้ Codex Clone Git Tag ที่ล็อกไว้ ใช้พอร์ตมาตรฐาน `127.0.0.1:4186` ที่ยืนยันล่วงหน้า และใช้ Google OAuth native/installed-app client configuration กลางจาก Release โดยผู้เรียนไม่ต้องสร้าง Project/Client/Test users, ดาวน์โหลด JSON หรือแก้ Client ID ให้ใช้ [Prompt ติดตั้งจาก GitHub พร้อม OAuth Client กลาง](install-github-google-auto-th.md) แทน เอกสารหน้านี้คงไว้สำหรับกรณีที่ต้องการให้ผู้ใช้เลือก Endpoint เอง Client กลางมี `client_id` และ `client_secret` ซึ่งเป็น app metadata ที่ต้องแจกพร้อม installed app ไม่ใช่ Credential ของบัญชีผู้ใช้ ค่าจริงถูก GitHub Actions inject จาก Release secrets ตอน build Asset และห้าม commit ลง public Git tree ส่วน access/refresh token ของผู้ใช้ยังเข้ารหัสด้วย Windows current-user DPAPI และไม่เข้า Repository, Frontend, Report หรือ Log

คัดลอกข้อความด้านล่างไปสั่ง Codex พร้อมแนบลิงก์ GitHub Release ของ Metafxclub AI Agent HQ ผู้ใช้ส่งคำขอครั้งเดียว และตอบยืนยัน URL อีกหนึ่งครั้งก่อนเริ่มติดตั้ง

```text
ช่วยติดตั้ง Metafxclub AI Agent HQ จาก GitHub Release ลิงก์นี้บนเครื่อง Windows ของผมให้พร้อมใช้งาน:

[วางลิงก์ GitHub Release ที่นี่]

ให้ทำตามขั้นตอนนี้อย่างเคร่งครัด

1. อ่าน AGENTS.md, README.md และ STUDENT-QUICKSTART-TH.md จาก Release ก่อน
2. ตรวจว่ามี Python 3.10-3.14 แบบ 64-bit จาก python.org และอยู่ใน PATH; หากไม่มีให้หยุดและแจ้งผู้ใช้ติดตั้ง Python x64 โดยเลือก Add Python to PATH ห้ามดาวน์โหลดหรือติดตั้ง Python แทนโดยไม่ได้รับอนุญาต
3. ตรวจ SHA-256 ถ้ามีไฟล์ Checksum แล้วแตก ZIP ไปยังโฟลเดอร์ชั่วคราว ห้ามรันจากใน ZIP
4. ก่อนติดตั้ง หยุด Bridge คัดลอกไฟล์ หรือสร้าง Python environment ให้เรียก:
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -ListAvailableEndpoints
5. นำ Local URL ที่ผลลัพธ์ระบุว่า available=true มาเสนอให้ผม 3 ตัวเลือก แล้วหยุดรอให้ผมเลือกก่อน
6. อธิบายด้วยภาษาง่าย ๆ ว่า IP จะเป็น 127.0.0.1 เหมือนกันทุกตัว เพราะเปิดเฉพาะเครื่องนี้ สิ่งที่เลือกคือหมายเลข Port เช่น 4186
7. เมื่อผมเลือกแล้ว ให้ตรวจว่าพอร์ตนั้นยังว่าง จากนั้นเรียก:
   .\1-INSTALL-HQ.bat -Port PORT_ที่ผมเลือก -EndpointConfirmed
8. ห้ามเปลี่ยนไปใช้ Port หรือ URL อื่นเอง หากพอร์ตถูกแย่งระหว่างติดตั้ง ให้หยุดและกลับมาเสนอ URL ว่างชุดใหม่
9. หลังติดตั้ง ให้อ่าน URL และ health_url จาก data/runtime/bridge-endpoint.json ห้ามเดาเลข Port และต้องตรวจว่า Health ตอบ ok=true, status=ready, host=127.0.0.1 และ Port ตรงกัน
10. ตรวจ GET `{url}api/props/mission_strategy_table/research-sheet/auth` ต้องได้ `clientConfigured=true` จาก native-app client configuration กลางใน Release โดยไม่แสดงค่า Client เต็ม หาก Client กลางไม่พร้อมให้หยุดและรายงานว่า Release ไม่สมบูรณ์ ห้ามขอ OAuth JSON, Client ID หรือ Client Secret จากนักเรียนแทน
11. เรียก scripts/check-codex-readiness.cmd เพื่อตรวจ Codex และ Rate Limit ของบัญชีที่ Login อยู่ใน Windows User เครื่องนี้
12. ถ้าขึ้น auth_required ให้แจ้งว่าต้อง Login ด้วยบัญชีของนักเรียนเอง ห้ามอ่าน คัดลอก หรือแสดง Token, Cookie, API key, Auth file หรือข้อมูลบัญชี
13. ถ้าขึ้น config_error ให้รายงานว่า Codex CLI มีค่า Config ที่ไม่รองรับ ห้ามแก้โดยเดาหรือคัดลอก Config จากเครื่องอื่น
14. เมื่อ Health พร้อม ให้เปิด URL ที่ยืนยันแล้ว และรายงานเป็นภาษาไทยเฉพาะ: เวอร์ชัน, ตำแหน่งติดตั้ง, URL, Health, สถานะ Client กลาง, สถานะ Codex และ Rate Limit
15. หยุดก่อนกดเชื่อมบัญชี Google แจ้งให้ผู้ใช้กด **เชื่อมบัญชี Google**, เลือกบัญชีของตนเอง และยืนยัน Consent ใน System Browser ด้วยตนเอง หากแอปยัง Under review ผู้ใช้ใหม่อาจเห็น Unverified warning และ Project กลางอาจอยู่ภายใต้ OAuth unverified user cap
16. ถามผู้ใช้ว่าจะเปิด Bridge อัตโนมัติหลังเข้าสู่ Windows หรือไม่ หากตอบตกลง ให้รัน `scripts/register-bridge-autostart.cmd` จากชุดติดตั้งถาวร และยืนยันว่า Scheduled Task ของผู้ใช้ปัจจุบันถูกสร้างสำเร็จ

กติกาความปลอดภัย:
- Local Bridge ต้องใช้ 127.0.0.1 เท่านั้น ห้ามใช้ 0.0.0.0, LAN IP หรือ Public IP
- ห้ามเปิด Firewall, Port Forwarding หรือเปิด HQ ออกสู่อินเทอร์เน็ต
- ห้ามปิด Process อื่นเพียงเพราะใช้ Port เดียวกัน
- เริ่มในโหมด Local/Demo ห้ามเปิด Live Trading, ส่ง Telegram จริง หรือ Deploy จริงระหว่างติดตั้ง
- Rate Limit ต้องมาจากบัญชี Codex ของผู้ใช้เครื่องนั้นเท่านั้น และห้ามพยายาม bypass หรือ reset limit
```

หลักการสำคัญ: ระบบไม่สุ่ม IP โดยเด็ดขาด เพราะ `127.0.0.1` คือที่อยู่เฉพาะเครื่องและปลอดภัยกว่า ระบบเสนอเฉพาะหมายเลข Port ที่ตรวจว่าว่าง ณ เวลานั้น และจะใช้ Port นั้นต่อเมื่อผู้ใช้ยืนยันแล้วเท่านั้น

`2-SETUP-GOOGLE-HQ.bat` และ Desktop OAuth JSON เป็น **Advanced/Recovery custom override** เท่านั้น ไม่ใช่ขั้นตอนติดตั้งปกติ หากเจ้าของระบบตั้งใจใช้ OAuth Project ของตนเองจึงค่อยใช้ BAT นี้กับ JSON ของ Project ที่ตนควบคุม ห้ามใช้หรือส่งไฟล์ของผู้สอน/เพื่อน และห้ามเปิดเผยค่า Client กลางเต็มที่มากับ Release
