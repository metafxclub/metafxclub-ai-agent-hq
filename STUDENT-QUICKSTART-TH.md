# คู่มือเริ่มต้นสำหรับนักเรียน — Metafxclub AI Agent HQ

## เตรียมเครื่องก่อนเริ่ม

1. ใช้ Windows 10 หรือ 11 และเชื่อมต่ออินเทอร์เน็ต
2. ติดตั้ง Python **3.10-3.14** จาก [python.org](https://www.python.org/downloads/windows/) และเลือก `Add Python to PATH`
3. ใช้บัญชี Codex ของตนเอง ห้ามรับ Token, Cookie หรือไฟล์ Auth จากผู้สอนหรือเพื่อน

ตัวติดตั้งจะสร้าง Python Virtual Environment แยกให้เอง แต่จะไม่ดาวน์โหลดหรือติดตั้ง Python หลักแทนผู้เรียน หาก Python ไม่อยู่ในช่วงที่รองรับ ระบบจะหยุดก่อนติดตั้งและแจ้งวิธีแก้ การเชื่อม Google Sheet แบบ Private เป็นขั้นตอนเสริมภายหลังตาม `docs/research-sheet-hub-setup-th.md`; ไม่ต้องนำไฟล์ OAuth ของผู้สอนไปใส่เครื่องนักเรียน

## เชื่อม Google Sheet แบบ Private ครั้งเดียว

1. เปิด Google Auth Platform ของ Project ตนเอง และดาวน์โหลด OAuth Client JSON ประเภท **Desktop app**
2. ระหว่างติดตั้ง เลือกตั้งค่า Google แล้วเลือกไฟล์ JSON หรือข้ามไปก่อนก็ได้
3. หากข้าม ให้ดับเบิลคลิก `2-SETUP-GOOGLE-HQ.bat` หรือจะลากไฟล์ JSON มาวางบน BAT นี้
4. ระบบตรวจไฟล์และให้ Backend CLI บันทึก Client configuration ด้วย Windows current-user DPAPI โดย JSON/Secret ไม่ผ่าน Browser และไม่ถูกคัดลอกเข้า Project
5. เมื่อ Agent HQ เปิดแล้ว กด **เชื่อมบัญชี Google ครั้งเดียว** เลือกบัญชีของตนเอง แล้วกลับมาใส่ Sheet ID

ไฟล์ OAuth JSON ต้นฉบับใน Downloads หรือโฟลเดอร์ที่เลือกจะไม่ถูกลบอัตโนมัติ ต้องเก็บเป็นความลับและลบเองเมื่อไม่ต้องใช้แล้ว

> **สำคัญ:** หาก OAuth consent screen ยังอยู่สถานะ `Testing` ต้องเพิ่ม Gmail ของผู้เรียนใน **Test users** และ Google อาจทำให้สิทธิ์/Refresh token หมดอายุหลัง 7 วัน ผู้เรียนจึงต้องกดเชื่อมใหม่ หากต้องการให้การเชื่อมครั้งเดียวใช้งานต่อเนื่อง ต้องจัด Publishing status และ Verification ตามนโยบายของ Google ก่อนนำไปใช้ในชั้นเรียน ดูรายละเอียดจาก [Google Auth Platform — Audience](https://support.google.com/cloud/answer/15549945)

ห้ามส่ง OAuth JSON ให้ผู้สอนหรือเพื่อน และห้ามวาง JSON/Client Secret ในหน้าเว็บ, Mission, Chat หรือ GitHub

## วิธีที่ง่ายที่สุด: Prompt เดียว ไม่ต้องกด BAT

1. เปิด [Prompt ติดตั้งอัตโนมัติ](docs/prompts/install-github-google-auto-th.md)
2. เปลี่ยนเพียง `GITHUB_RELEASE_URL`, `EXPECTED_GOOGLE_CLIENT_ID` และ `GOOGLE_DESKTOP_OAUTH_JSON`
3. วาง Prompt ทั้งชุดลงใน Codex แล้วรอให้ Codexติดตั้ง, นำเข้า JSON, ตรวจ Health และเปิด Agent HQ
4. เมื่อหน้า HQ เปิด ให้กด **เชื่อมบัญชี Google ครั้งเดียว** แล้ว Login/กดอนุญาตในหน้าทางการของ Google

Prompt เป็นคำยืนยันล่วงหน้าให้ Codex เลือก Local endpoint รายการแรกที่ว่างบน `127.0.0.1` จึงไม่ต้องหยุดถามเลือก Port และไม่ต้องให้ผู้เรียนกด `1-INSTALL-HQ.bat` หรือ `2-SETUP-GOOGLE-HQ.bat` เอง หาก Release, Checksum, Python, JSON หรือ Health ไม่ผ่าน Codex ต้องหยุดและบอกสาเหตุตามจริง

หาก Windows ขอสิทธิ์ดาวน์โหลดหรือเปิดตัวติดตั้ง ให้อ่านชื่อไฟล์และตรวจว่าเป็น Release ของ Metafxclub ที่อาจารย์ส่งให้ก่อนกดยืนยัน ห้ามปิดระบบป้องกันไวรัสหรือข้ามคำเตือนของไฟล์ที่ไม่ทราบแหล่งที่มา

## วิธีติดตั้งเองเมื่อไม่ได้ใช้ Codex

1. ตรวจว่าติดตั้ง Python 3.10-3.14 พร้อม `Add Python to PATH` แล้ว
2. ดาวน์โหลดไฟล์ ZIP สำหรับ Windows จาก GitHub Release
3. คลิกขวาแล้วเลือก **Extract All / แตกไฟล์ทั้งหมด**
4. เปิดโฟลเดอร์ที่แตกแล้ว
5. ดับเบิลคลิก `1-INSTALL-HQ.bat`
6. เมื่อเห็น URL ว่าง ให้พิมพ์ `Y` เพื่อยืนยัน หรือ `N` เพื่อดูตัวเลือกถัดไป
7. เมื่อติดตั้งสำเร็จ ให้ดับเบิลคลิก `Open Metafx Agent HQ.cmd`
8. หากตั้งค่า Google แล้ว ให้กด **เชื่อมบัญชี Google ครั้งเดียว** ใน Agent HQ แล้วกรอก Sheet ID

ลิงก์เข้าโปรแกรมจะแสดงก่อนและหลังติดตั้ง เช่น `http://127.0.0.1:4186/` หาก Port นี้ถูกใช้อยู่ ระบบจะเสนอ URL อื่นและรอคำยืนยัน ระบบจะไม่ปิดโปรแกรมอื่นหรือสลับ URL เอง

## ถ้าติดตั้งด้วย GitHub Clone

```powershell
git clone https://github.com/metafxclub/metafxclub-ai-agent-hq.git
cd metafxclub-ai-agent-hq
.\1-INSTALL-HQ.bat
```

- โฟลเดอร์ Clone คือ Source สำหรับเรียนและแก้โค้ด
- โปรแกรมที่เปิดใช้งานจริงอยู่ที่ `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ`
- เมื่อต้องการรับรุ่นใหม่ ให้ Commit หรือสำรองงานของตนเองให้เรียบร้อย แล้วดับเบิลคลิก `UPDATE-HQ.bat`
- ตัวอัปเดตยอมรับเฉพาะการอัปเดตแบบ fast-forward หากมีไฟล์แก้ค้างหรือประวัติคนละทาง ระบบจะหยุดก่อนและไม่ทับงาน
- ถ้าต้องการส่งงานกลับ GitHub ให้ Fork Repository แล้ว Push Branch ของตนเองเพื่อเปิด Pull Request ห้าม Push Runtime, Memory, Log, Token หรือ Auth

## เปิด Bridge อัตโนมัติหลังเปิดเครื่อง

หลังติดตั้งและยืนยัน URL แล้ว ให้ดับเบิลคลิก `scripts/register-bridge-autostart.cmd` หนึ่งครั้ง ระบบจะสร้าง Scheduled Task ของ Windows User คนนี้ พร้อมลองใหม่เมื่อเปิดไม่สำเร็จและตรวจ Bridge ทุก 15 นาทีโดยค่าเริ่มต้นผ่านตัวเปิดแบบไม่มีหน้าต่าง

ระบบไม่เปิด Browser หรือ MT4/MT5 เอง เมื่อต้องการเปิดหน้าจอให้ใช้ Shortcut `Metafxclub AI Agent HQ` บน Desktop หากไม่ต้องการเปิด Bridge อัตโนมัติแล้ว ให้ดับเบิลคลิก `scripts/unregister-bridge-autostart.cmd`

## ถ้าเปิดโปรแกรมไม่ได้

ทำตามลำดับนี้:

1. ดับเบิลคลิก `scripts/status-local-bridge.cmd` เพื่อตรวจสถานะ
2. ดับเบิลคลิก `scripts/check-codex-readiness.cmd` เพื่อตรวจ Codex และ Rate Limit
3. หาก Bridge ยังไม่พร้อม ให้ดับเบิลคลิก `scripts/repair-hq.cmd` แล้วเลือก URL ใหม่เมื่อระบบถาม
4. เปิด `Open Metafx Agent HQ.cmd` ใหม่
5. หากยังไม่สำเร็จ ให้ส่งข้อความที่หน้าจอแจ้งเตือนให้อาจารย์ โดยลบข้อมูลส่วนตัวหรือรหัสผ่านออกก่อน

ไม่ควรปิด Process หรือโปรแกรมอื่นเองเพียงเพราะ Port เดิมถูกใช้งาน ระบบจะรักษาโปรแกรมนั้นไว้และขอให้นักเรียนยืนยัน URL ว่างใหม่บน `127.0.0.1`

## เรื่องบัญชี Codex

- นักเรียนต้อง Login ด้วยบัญชี Codex ของตนเอง
- ห้ามขอบัญชี Token, Cookie หรือไฟล์ Auth จากอาจารย์หรือเพื่อน
- Quota และ Rate Limit ที่แสดงเป็นของบัญชีที่ Login อยู่ในเครื่องนั้น
- หากเห็น `auth_required` แต่หน้า Office เปิดได้ ให้ Login Codex แล้วลองใหม่ ไม่จำเป็นต้องติดตั้ง HQ ซ้ำ
- ใช้ `scripts/login-codex-runner.ps1` เฉพาะเมื่อนักเรียนยืนยันว่าจะ Login ผ่านหน้าทางการ และห้ามส่ง Token หรือไฟล์ Auth ให้ผู้อื่น

## ถอนการติดตั้งและข้อมูล Google

- ดับเบิลคลิก `UNINSTALL-HQ.bat` เป็นการถอนแบบปกติ: เก็บ Mission, Report, Memory, Log รวมทั้ง Google OAuth Client และการยืนยัน Google ที่เข้ารหัสไว้ เพื่อใช้ต่อเมื่อติดตั้งใหม่
- หากต้องการลบข้อมูลทั้งหมดจริง ต้องเรียก `scripts\uninstall-hq.ps1` พร้อม `-RemoveUserData -ConfirmUserDataRemoval DELETE-METAFX-DATA` ระบบจึงจะให้ Backend CLI ลบทั้ง OAuth Client และการยืนยัน Google
- Environment variable ที่ผู้ดูแลตั้งเองและ OAuth JSON ต้นฉบับใน Downloads จะไม่ถูกลบอัตโนมัติ

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
