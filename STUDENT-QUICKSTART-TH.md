# คู่มือเริ่มต้นสำหรับนักเรียน — Metafxclub AI Agent HQ

## เตรียมเครื่องก่อนเริ่ม

1. ใช้ Windows 10 หรือ 11 แบบ 64-bit และเชื่อมต่ออินเทอร์เน็ต
2. เปิด Codex และใช้บัญชีของตนเอง ห้ามรับ Token, Cookie หรือไฟล์ Auth จากผู้สอนหรือเพื่อน

เมื่อใช้ Prompt หลัก ผู้เรียนไม่ต้องติดตั้ง Git หรือ Python เอง Prompt จะตรวจเครื่องก่อนเสมอ: ถ้ามี Git ที่ใช้ได้และ Python 3.10-3.14 แบบ 64-bit อยู่แล้วจะใช้ของเดิมและไม่ติดตั้งซ้ำ ถ้าขาดจึงติดตั้งแพ็กเกจทางการที่ล็อกไว้ผ่าน WinGet แบบ current-user แล้วตรวจซ้ำ ส่วน `installer/install.ps1` จะสร้าง Python Virtual Environment แยก ตรวจ SHA-256 และ Bootstrap `pip==26.2.1` จากไฟล์ Offline ก่อนเชื่อม PyPI เพื่อใช้ Windows certificate store แล้วตรวจ Runtime ซ้ำอีกชั้น การเชื่อม Google Sheet แบบ Private เป็นขั้นตอนเสริมภายหลังตาม `docs/research-sheet-hub-setup-th.md`; Client กลางพร้อมมากับ Release แล้ว จึงไม่ต้องนำไฟล์ OAuth ของผู้สอนหรือของใครมาใส่เครื่องนักเรียน

## เชื่อม Google Sheet แบบ Private ครั้งเดียว

1. ติดตั้ง Agent HQ จาก Release ที่อาจารย์ล็อกไว้ ตัวติดตั้งจะเตรียม Google OAuth native/installed-app client configuration กลางให้เอง
2. เปิด Agent HQ แล้วกด **เชื่อมบัญชี Google**
3. เลือก Gmail ของตนเองในหน้าทางการของ Google และกดยืนยัน Consent ด้วยตนเอง
4. กลับมาที่ Agent HQ แล้วใส่ Google Sheet URL/ID ที่บัญชีของตนมีสิทธิ์ Editor

นักเรียน **ไม่ต้อง** สร้าง Google Cloud Project/OAuth Client, ไม่ต้องเพิ่ม Gmail เป็น Test user, ไม่ต้องดาวน์โหลดหรือส่ง OAuth JSON และไม่ต้องกรอกหรือแก้ Client ID กลาง

Client กลางมี `client_id` และ `client_secret` ของ native app อยู่ใน Release Asset โดย GitHub Actions inject ค่าจริงจาก Release secrets ตอน build และไฟล์จริงไม่อยู่ใน public Git tree ห้าม commit หรือแสดงค่า Client เต็ม แม้ metadata นี้ต้องแจกพร้อม installed app และไม่ใช่ Credential ของ Gmail นักเรียน ส่วน access token และ refresh token ของนักเรียนจะถูกเข้ารหัสด้วย Windows current-user DPAPI และไม่เข้า Repository, Frontend, Report หรือ Log

> **ระหว่างรอ Google ตรวจสอบ:** ผู้ใช้ใหม่อาจเห็นหน้า `Google ยังไม่ได้ยืนยันแอปนี้` และ Project กลางอาจอยู่ภายใต้ OAuth unverified user cap ให้ทำตามคำแนะนำของอาจารย์และอนุญาตเฉพาะแอปชื่อ Metafxclub Agent HQ เท่านั้น เมื่อ Scope ได้รับอนุมัติแล้ว คำเตือนและเพดานนี้จะไม่ใช้กับ Scope ที่ได้รับอนุมัติ ดูรายละเอียดจาก [Google Auth Platform — Audience](https://support.google.com/cloud/answer/15549945)

`2-SETUP-GOOGLE-HQ.bat` และ OAuth JSON เป็นโหมด **Advanced/Recovery custom override** เท่านั้น ใช้เมื่อเจ้าของ Project ต้องการ Client ของตนเองหรือผู้ดูแลสั่งให้กู้การตั้งค่า ไม่ใช่ขั้นตอนปกติของนักเรียน หากจำเป็นต้องใช้ ให้ใช้ JSON ของ Project ที่ตนควบคุมเองและห้ามวาง JSON หรือค่า Client แบบเต็มในหน้าเว็บ, Mission หรือ Chat

## วิธีที่ง่ายที่สุด: Prompt เดียว ไม่ต้องกด BAT

1. เปิด [Prompt ติดตั้งอัตโนมัติ](docs/prompts/install-github-google-auto-th.md)
2. Repository, Git Tag, Version และ Client กลางถูกเตรียมไว้แล้ว ห้ามแก้ Client ID และไม่ต้องเติม Path ของ OAuth JSON
3. วาง Prompt ทั้งชุดลงใน Codex แล้วรอให้ Codex ตรวจ/ติดตั้งเฉพาะ Git หรือ Python ที่ขาด, Clone Tag ที่กำหนด, ตรวจ Source, ดาวน์โหลด Release ZIP กับ `.sha256`, ตรวจ hash และ extract เฉพาะ Client กลางจาก Asset เข้า Source ชั่วคราว จากนั้นเรียก Installer โดยตรงรอบเดียว ตรวจ Client กลาง/Health/หน้าเว็บ เปิด Watchdog และเปิด Agent HQ ที่ `http://127.0.0.1:4186/`
4. เมื่อหน้า HQ เปิด ให้กด **เชื่อมบัญชี Google ครั้งเดียว** แล้ว Login/กดอนุญาตในหน้าทางการของ Google

Prompt เป็นคำยืนยันล่วงหน้าให้ Codex ใช้ `127.0.0.1:4186` และติดตั้งเฉพาะ Git/Python ที่ขาดแบบ current-user จึงไม่ต้องหยุดถามเลือก Port และไม่ต้องให้ผู้เรียนดาวน์โหลด ZIP หรือกด `1-INSTALL-HQ.bat`/`2-SETUP-GOOGLE-HQ.bat` เอง หาก WinGet/Bootstrap ไม่สำเร็จ, Git/Tag/Version ไม่ตรง, พอร์ต 4186 ถูกใช้อยู่ หรือ Client กลางใน Release, Deployment Preflight, Health หรือหน้าเว็บไม่ผ่าน Codex ต้องหยุดและบอกสาเหตุตามจริงพร้อมวิธีแก้หนึ่งขั้น

Codex ต้อง Clone ลงโฟลเดอร์ชั่วคราวใหม่และห้ามแก้ Repository เดิมของผู้เรียน หาก Windows แสดง UAC หรือขอสิทธิ์ Administrator ให้กด **No/Cancel**, หยุดขั้นตอนนั้น และส่งข้อความผิดพลาดให้ผู้สอน ห้ามกดยอมรับแทน ห้ามปิดระบบป้องกันไวรัสหรือข้ามคำเตือนของไฟล์ที่ไม่ทราบแหล่งที่มา

## เลือก MT4 / MT5 จากจุดเดียว

1. เปิด MT4 หรือ MT5 ตัวที่ต้องการใช้ไว้เพียงหนึ่งโปรแกรมต่อแพลตฟอร์ม
2. ที่แถบบนของ Agent HQ กด `เชื่อม MT4 / MT5` แล้วกดสแกน
3. ตรวจชื่อ Terminal ที่ระบบพบ แล้วกดใช้กับทุกระบบที่รองรับ
4. หากมี MT4 หรือ MT5 หลายตัว ระบบจะไม่เดาว่าตัวใดถูกต้อง ให้ปิดตัวอื่นจนเหลือตัวที่ต้องการหนึ่งตัวแล้วสแกนใหม่

การสแกนและเลือกนี้ไม่เปิด Terminal ให้เอง ไม่อ่านเลขบัญชี/รหัสผ่าน และไม่เปิด Demo หรือ Live Trading หน้าสภา AI Trade, โรงงานสร้าง EA และห้องทดลองจะแสดงสถานะจาก Backend เดียวกันโดยไม่มีปุ่มเลือก Terminal ซ้ำภายในอุปกรณ์

## วิธีติดตั้งเองเมื่อไม่ได้ใช้ Codex

1. ตรวจว่าติดตั้ง Python 3.10-3.14 แบบ 64-bit พร้อม `Add Python to PATH` แล้ว
2. ดาวน์โหลดทั้งไฟล์ ZIP สำหรับ Windows และไฟล์ `.zip.sha256` ชื่อเดียวกันจาก GitHub Release
3. เปิด PowerShell ในโฟลเดอร์ดาวน์โหลด รัน `Get-FileHash -Algorithm SHA256 .\ชื่อไฟล์.zip` แล้วเทียบค่ากับข้อความตัวแรกใน `.zip.sha256` ให้ตรงกันทุกตัวอักษร หากไม่ตรงให้ลบไฟล์และหยุดติดตั้ง
4. คลิกขวา ZIP แล้วเลือก **Extract All / แตกไฟล์ทั้งหมด**
5. เปิดโฟลเดอร์ที่แตกแล้ว
6. ดับเบิลคลิก `1-INSTALL-HQ.bat`
7. รอให้ตัวติดตั้งรัน Deployment Preflight และเปิด `http://127.0.0.1:4186/` ให้เอง หากพอร์ตนี้ถูกใช้อยู่ให้ปิดเฉพาะโปรแกรมที่คุณทราบว่าเป็นเจ้าของพอร์ต หรือขอผู้สอนช่วยตรวจ ห้ามสุ่มปิด Process
8. Client กลางพร้อมมากับ Release แล้ว ให้กด **เชื่อมบัญชี Google ครั้งเดียว** ใน Agent HQ เลือกบัญชี/กดยืนยัน Consent ด้วยตนเอง แล้วกรอก Sheet ID

ลิงก์มาตรฐานของห้องเรียนคือ `http://127.0.0.1:4186/` ตัวติดตั้งจะไม่ปิดโปรแกรมอื่นและไม่สลับ URL เอง

## ถ้าต้องการเก็บ Source เพื่ออ่านหรือพัฒนา (ไม่ใช่การติดตั้ง)

```powershell
git clone https://github.com/metafxclub/metafxclub-ai-agent-hq.git
cd metafxclub-ai-agent-hq
git status
```

- โฟลเดอร์ Plain clone คือ Source สำหรับอ่าน เรียน GitHub แก้โค้ด และรันชุดทดสอบเท่านั้น ไม่ใช่ Runtime สำหรับห้องเรียน และจงใจไม่มีไฟล์ Client กลางจาก Release
- ห้ามเปิด `1-INSTALL-HQ.bat` หรือ `UPDATE-HQ.bat` จาก Plain clone โดยคาดหวังว่าจะติดตั้งหรืออัปเดตชุดห้องเรียนพร้อม Google หากต้องติดตั้งให้ใช้ Prompt หลักที่ล็อก Tag/Version และตรวจ Release Asset + hash แล้ว
- โปรแกรมที่เปิดใช้งานจริงอยู่ที่ `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ`
- เมื่อต้องการอัปเดต Runtime ห้องเรียน ให้อาจารย์ส่ง Prompt ฉบับใหม่ที่ล็อก Tag/Version ใหม่ ไม่ต้อง Pull `main` หรือใช้ `UPDATE-HQ.bat` จาก Plain clone
- ถ้าต้องการส่งงานกลับ GitHub ให้ Fork Repository แล้ว Push Branch ของตนเองเพื่อเปิด Pull Request ห้าม Push Runtime, Memory, Log, Token หรือ Auth

## เปิด Bridge อัตโนมัติหลังเปิดเครื่อง

ตัวติดตั้งสร้าง Scheduled Task ของ Windows User คนนี้ให้แล้ว พร้อมลองใหม่เมื่อเปิดไม่สำเร็จและตรวจ Bridge ทุก 15 นาทีผ่านตัวเปิดแบบไม่มีหน้าต่าง จึงไม่ต้องกดตั้งค่าเพิ่มหลังติดตั้งรอบแรก

Task เปิดเฉพาะ Bridge ไม่เปิด Browser หรือ MT4/MT5 เอง เมื่อต้องการเปิดหน้าจอให้ใช้ Shortcut `Metafxclub AI Agent HQ` บน Desktop หากไม่ต้องการเปิด Bridge อัตโนมัติแล้ว ให้ดับเบิลคลิก `scripts/unregister-bridge-autostart.cmd`

## ถ้าเปิดโปรแกรมไม่ได้

ทำตามลำดับนี้:

1. ดับเบิลคลิก `scripts/status-local-bridge.cmd` เพื่อตรวจสถานะ
2. ดับเบิลคลิก `scripts/check-codex-readiness.cmd` เพื่อตรวจ Codex และ Rate Limit
3. หาก Bridge ยังไม่พร้อม ให้ดับเบิลคลิก `scripts/repair-hq.cmd` แล้วเลือก URL ใหม่เมื่อระบบถาม
4. เปิด `Open Metafx Agent HQ.cmd` ใหม่
5. หากยังไม่สำเร็จ ให้ส่งข้อความที่หน้าจอแจ้งเตือนให้อาจารย์ โดยลบข้อมูลส่วนตัวหรือรหัสผ่านออกก่อน

ไม่ควรปิด Process หรือโปรแกรมอื่นเองเพียงเพราะ Port เดิมถูกใช้งาน ระบบจะรักษาโปรแกรมนั้นไว้และขอให้นักเรียนยืนยัน URL ว่างใหม่บน `127.0.0.1`

หาก Installer แจ้ง `CERTIFICATE_VERIFY_FAILED` ตัวติดตั้งจะหยุดและคืน Last-good โดยไม่ปิด TLS ให้ส่งข้อความผิดพลาดให้อาจารย์หรือผู้ดูแลเครื่องตรวจ Windows Trusted Root, Proxy หรือ Antivirus แล้วจึงวาง Prompt รุ่นเดิมใหม่ ห้ามเติม `--trusted-host`, ปิด certificate verification หรือติดตั้งใบรับรองที่ไม่ทราบแหล่งที่มาเอง

## เรื่องบัญชี Codex

- นักเรียนต้อง Login ด้วยบัญชี Codex ของตนเอง
- ห้ามขอบัญชี Token, Cookie หรือไฟล์ Auth จากอาจารย์หรือเพื่อน
- Quota และ Rate Limit ที่แสดงเป็นของบัญชีที่ Login อยู่ในเครื่องนั้น
- หากเห็น `auth_required` แต่หน้า Office เปิดได้ ให้ Login Codex แล้วลองใหม่ ไม่จำเป็นต้องติดตั้ง HQ ซ้ำ
- ใช้ `scripts/login-codex-runner.ps1` เฉพาะเมื่อนักเรียนยืนยันว่าจะ Login ผ่านหน้าทางการ และห้ามส่ง Token หรือไฟล์ Auth ให้ผู้อื่น

## ถอนการติดตั้งและข้อมูล Google

- ดับเบิลคลิก `UNINSTALL-HQ.bat` เป็นการถอนแบบปกติ: เก็บ Mission, Report, Memory, Log และการยืนยัน Google ที่เข้ารหัสไว้ เพื่อใช้ต่อเมื่อติดตั้งใหม่
- หากต้องการลบข้อมูลทั้งหมดจริง ต้องเรียก `scripts\uninstall-hq.ps1` พร้อม `-RemoveUserData -ConfirmUserDataRemoval DELETE-METAFX-DATA` ระบบจึงจะให้ Backend CLI ลบ durable Google grant และ OAuth Client แบบ custom override
- Client กลางเป็นส่วนหนึ่งของ Release ส่วน Environment variable และ OAuth JSON ต้นฉบับที่ผู้ดูแลตั้งเองในโหมด Advanced จะไม่ถูกลบอัตโนมัติ

## โหมดเริ่มต้นที่ปลอดภัย

หลังติดตั้ง ระบบต้องอยู่ในโหมด Demo/Read-only:

- ไม่ส่งคำสั่งซื้อขายจริง
- ไม่ส่ง Telegram จริง
- ไม่ Deploy ระบบจริง
- ไม่ลบหรือแก้ไฟล์สำคัญอัตโนมัติ
- งานเสี่ยงต้องผ่าน Risk Guard และได้รับการอนุมัติก่อน

## Checklist ก่อนเริ่มบทเรียน

- [ ] หน้า AI Agent HQ เปิดได้
- [ ] เห็น Agent และอุปกรณ์ในห้อง
- [ ] Bridge แสดงสถานะพร้อม
- [ ] Health แสดง `ready`
- [ ] URL/Port ตรงกับค่าที่ตนเองยืนยัน
- [ ] ระบบอยู่ในโหมด Demo/Read-only
- [ ] ใช้บัญชี Codex ของตนเอง
- [ ] Rate Limit แสดงจากบัญชีของเครื่องนี้ หรือขึ้นข้อความให้ Login อย่างชัดเจน
- [ ] ไม่ได้ส่ง Token, Cookie หรือรหัสผ่านให้ใคร

เมื่อครบทุกข้อ ถือว่าพร้อมเริ่มบทเรียนครับ
