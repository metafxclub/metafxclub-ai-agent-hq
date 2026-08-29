# Prompt ติดตั้งจาก GitHub พร้อม Google OAuth แบบอัตโนมัติ

Prompt นี้ใช้สำหรับให้ลูกค้าวางใน Codex บน Windows เพียงครั้งเดียว ลูกค้าไม่ต้องกดไฟล์ BAT และไม่ต้องกรอก Client ID ในหน้า Agent HQ หลัง Codex ทำงานเสร็จ ลูกค้าเหลือเพียงกด **เชื่อมบัญชี Google ครั้งเดียว** และอนุญาตในหน้าทางการของ Google

แก้เฉพาะค่า 3 บรรทัดแรกก่อนส่ง Prompt:

```text
ช่วยติดตั้ง Metafxclub AI Agent HQ บน Windows User ปัจจุบันให้เสร็จอัตโนมัติ โดยไม่ให้ฉันกดไฟล์ BAT หรือติดตั้งด้วยตนเอง

GITHUB_RELEASE_URL = "[ลิงก์ GitHub Release แบบล็อก Version หรือ Direct ZIP Asset]"
EXPECTED_GOOGLE_CLIENT_ID = "[Client ID ที่ลงท้ายด้วย .apps.googleusercontent.com]"
GOOGLE_DESKTOP_OAUTH_JSON = "[Path เต็มของ Desktop OAuth JSON เช่น C:\Users\ชื่อผู้ใช้\Downloads\client_secret_xxx.json]"

ข้อความนี้เป็นการยืนยันล่วงหน้าให้ Codex ใช้ Local endpoint มาตรฐาน `http://127.0.0.1:4186/` และส่งพอร์ต 4186 เข้า Installer ด้วย -EndpointConfirmed ได้ ไม่ต้องถามฉันให้เลือก Port หรือกดไฟล์ BAT ซ้ำ ห้ามใช้ 0.0.0.0, LAN IP หรือ Public IP

ให้ดำเนินการตามลำดับนี้:

1. รับ Release จาก github.com เท่านั้น ต้องเป็น Release ที่ล็อก Version หรือ Direct Asset ของ Version ชัดเจน ห้ามใช้ Branch main หรือ URL latest ที่เปลี่ยนปลายทางได้ ดาวน์โหลด ZIP และไฟล์ .sha256 ของ Asset เดียวกันลงโฟลเดอร์ชั่วคราว ตรวจ SHA-256 ให้ตรงก่อนแตกไฟล์ และห้ามรันจากใน ZIP

2. ตรวจ GOOGLE_DESKTOP_OAUTH_JSON แบบ Local เท่านั้น: Path ต้องเป็นไฟล์จริง นามสกุล .json ขนาดไม่เกิน 64 KiB ไม่เป็น Link/Junction และต้องมีโครงสร้าง Google Desktop app ใต้ installed ตรวจเฉพาะ installed.client_id ในหน่วยความจำว่าเท่ากับ EXPECTED_GOOGLE_CLIENT_ID หากไม่ตรงให้หยุด ห้ามพิมพ์ JSON, client_secret หรือ object ที่อ่านจาก JSON ลง Console, Log หรือ Chat

3. ห้ามอัปโหลด คัดลอก ย้าย หรือลบ OAuth JSON ต้นฉบับ ห้ามวาง JSON/Client Secret ใน Source, Git, Frontend, Mission หรือ Report และห้ามสร้างระบบเก็บ Credential ขึ้นมาเอง

4. หลังแตก Release ให้อ่าน AGENTS.md, README.md, STUDENT-QUICKSTART-TH.md, docs/prompts/install-local-endpoint-th.md และ docs/research-sheet-hub-setup-th.md ก่อนติดตั้ง

5. ตรวจ Windows 10/11 และ Python 3.10-3.14 จาก python.org ใน PATH หากไม่มีหรือ Version ไม่รองรับ ให้หยุดพร้อมบอกขั้นตอนติดตั้ง Python และ Add Python to PATH ห้ามติดตั้ง Python, ปิด Antivirus หรือขอสิทธิ์ Administrator เอง

6. จากโฟลเดอร์ Release ให้เรียกคำสั่งตรวจแบบ Read-only:
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\installer\install.ps1" -ListAvailableEndpoints
   JSON ต้องมี candidate ของ `127.0.0.1:4186` ที่ available=true หากไม่มีให้หยุดและแจ้งว่า Port 4186 ถูกใช้อยู่ ห้ามเลือก Port อื่น ห้ามปิด Process อื่น และห้ามเริ่มติดตั้ง

7. เรียก Installer เพียงรอบเดียว พร้อมพอร์ตและ OAuth JSON ที่ตรวจแล้ว ห้ามใช้ -SkipLaunch หรือ -SkipAutostart:
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\installer\install.ps1" -Port 4186 -EndpointConfirmed -GoogleClientJsonPath "<Path เต็มจาก GOOGLE_DESKTOP_OAUTH_JSON>" -ExpectedGoogleClientId "<EXPECTED_GOOGLE_CLIENT_ID>"
   รอให้ตัวติดตั้งรัน Preflight, สร้าง pinned venv, รัน Tests, เปิด Bridge, ตรวจ Health/หน้าเว็บ, นำเข้า OAuth Client ผ่าน DPAPI และลงทะเบียน Watchdog หลัง Login จบ ห้ามรายงานว่าสำเร็จถ้าตัวติดตั้งคืน Exit code ที่ไม่ใช่ 0 โดย Exit code 2 หมายถึงตัว HQ ติดตั้งและเปิดได้แล้ว แต่ Google OAuth ยังตั้งค่าไม่ครบ ให้รายงานเป็น partial success พร้อมสาเหตุและซ่อมเฉพาะ Google หลังแก้ JSON/Client ID ห้ามรันติดตั้งเต็มซ้ำโดยไม่จำเป็น

8. ห้ามเรียกคำสั่งนำเข้า OAuth ซ้ำเมื่อ Installer สำเร็จ หากต้องซ่อมเฉพาะ Google หลังผู้ใช้แก้ Path/JSON แล้วเท่านั้น จึงใช้ Runtime ที่ติดตั้งจริง:
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Metafxclub\AI-Agent-HQ\scripts\setup-google-oauth.ps1" -ClientJsonPath "<Path เต็มจาก GOOGLE_DESKTOP_OAUTH_JSON>" -ExpectedClientId "<EXPECTED_GOOGLE_CLIENT_ID>" -SkipOpen
   ห้ามเรียก Python/DPAPI แบบที่สร้างขึ้นเอง และห้ามแสดง Client ID เต็มหรือ Client Secret ในผลลัพธ์

9. อ่าน url, health_url และ port จาก:
   %LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\bridge-endpoint.json
   แล้วตรวจ health_url ต้องได้ ok=true, status=ready, endpoint.host=127.0.0.1 และ endpoint.port=4186 จากนั้น GET url ต้องได้ HTTP 200 และมีเนื้อหาหน้าเว็บ

10. ตรวจ GET {url}api/props/mission_strategy_table/research-sheet/auth ต้องได้ clientConfigured=true สถานะปกติของเครื่องใหม่คือ connected=false และ status=authorization_required หากเครื่องนี้เคยเชื่อม Client เดิมอย่างถูกต้องแล้วจึงยอมรับ connected=true/status=connected ได้ ห้ามอ้างว่า Google เชื่อมแล้วจากการบันทึก JSON เพียงอย่างเดียว

11. ตรวจ Scheduled Task ชื่อ `Metafxclub AI Agent HQ Bridge` ว่ามี Trigger ตอน Login และ Action ผูกกับ `/Port:4186` จากนั้นเรียก scripts/check-codex-readiness.cmd จากโฟลเดอร์ติดตั้งจริง แล้วเปิด url ที่อ่านจาก bridge-endpoint.json

12. หยุดเมื่อหน้า Agent HQ เปิดแล้ว ห้ามกดปุ่มเชื่อม Google, เลือกบัญชี, กรอกรหัสผ่าน หรือกดอนุญาตแทนฉัน แจ้งฉันว่า “ติดตั้งและนำเข้า OAuth Client สำเร็จ กรุณากดเชื่อมบัญชี Googleครั้งเดียวใน HQ”

13. เริ่มระบบใน Demo/Read-only เท่านั้น ห้ามเปิด Live Trading, ส่ง Telegram จริง, Deploy จริง, เปิด Firewall หรือ Port Forwarding ระหว่างติดตั้ง

14. สรุปท้ายงานเฉพาะ Version, ตำแหน่งติดตั้ง, URL `http://127.0.0.1:4186/`, Health, HTTP หน้าเว็บ, สถานะ Watchdog, สถานะ Codex/Rate Limit, สถานะ Google Client แบบปิดบัง และสิ่งที่ฉันต้องกดเอง ห้ามแสดง Client Secret, Refresh Token, Access Token, Cookie, Auth file หรือเนื้อหา JSON

ทำงานต่อเนื่องได้โดยไม่ต้องถามฉันระหว่างขั้นตอน เว้นแต่พบ Release/Checksum ไม่ถูกต้อง, JSON ผิดประเภทหรือ Client ID ไม่ตรง, Python ไม่พร้อม, ต้องใช้สิทธิ์ Administrator, Health ไม่ผ่าน หรือถึงขั้นที่ฉันต้องอนุญาตบัญชี Googleเอง
```

`EXPECTED_GOOGLE_CLIENT_ID` ใช้ตรวจว่าเลือก JSON ถูกไฟล์เท่านั้น Runtime จะอ่านค่าจริงจาก JSON ผ่าน Backend ที่โครงการเตรียมไว้ จึงห้ามนำ Client Secret หรือเนื้อหา JSON มาวางใน Prompt

การติดตั้งอัตโนมัติทำได้ถึงสถานะ `authorization_required` การ Login เลือกบัญชี และกดอนุญาต Google ต้องเป็นการกระทำของเจ้าของบัญชีเอง
