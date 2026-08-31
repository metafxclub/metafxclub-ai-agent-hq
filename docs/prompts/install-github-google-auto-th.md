# Prompt ติดตั้งด้วย Codex จาก GitHub Clone พร้อม Google OAuth

Prompt นี้ใช้สำหรับให้นักเรียนวางใน Codex บน Windows เพียงครั้งเดียว Codex จะ Clone Source รุ่นที่ล็อกไว้จาก GitHub, ตรวจ Tag/Version, เรียก Installer, ตรวจ Runtime และเปิด Agent HQ ให้เอง นักเรียนไม่ต้องดาวน์โหลด ZIP และไม่ต้องกดไฟล์ BAT

ก่อนส่งให้นักเรียน อาจารย์ล็อกค่า `GITHUB_REPOSITORY`, `GITHUB_TAG` และ `EXPECTED_VERSION` ไว้แล้ว นักเรียนแก้เฉพาะ 2 บรรทัดสุดท้ายคือ Client ID และ Path ของ Desktop OAuth JSON ของตนเอง:

ก่อนใช้ Prompt หาก OAuth app ยังมี Publishing status เป็น `Testing` ให้เพิ่ม Gmail ที่นักเรียนจะใช้เชื่อมไว้ที่ Google Auth Platform → `Audience` → `Test users` ก่อน มิฉะนั้น Google จะตอบ `403 access_denied` แม้ติดตั้งโปรแกรมและนำเข้า JSON ถูกต้องแล้ว

```text
ช่วยติดตั้ง Metafxclub AI Agent HQ บน Windows User ปัจจุบันให้เสร็จอัตโนมัติ โดยให้คุณ Clone จาก GitHub และเรียก Installer เอง ฉันจะไม่ดาวน์โหลด ZIP และไม่กดไฟล์ BAT

GITHUB_REPOSITORY = "https://github.com/metafxclub/metafxclub-ai-agent-hq.git"
GITHUB_TAG = "v0.9.7"
EXPECTED_VERSION = "0.9.7"
EXPECTED_GOOGLE_CLIENT_ID = "[Client ID ที่ลงท้ายด้วย .apps.googleusercontent.com]"
GOOGLE_DESKTOP_OAUTH_JSON = "[Path เต็มของ Desktop OAuth JSON เช่น C:\Users\ชื่อผู้ใช้\Downloads\client_secret_xxx.json]"

ข้อความนี้เป็นการยืนยันล่วงหน้าให้ Codex ใช้ Local endpoint มาตรฐาน `http://127.0.0.1:4186/` และส่งพอร์ต 4186 เข้า Installer ด้วย `-EndpointConfirmed` ได้ ไม่ต้องถามฉันให้เลือก Port หรือกดไฟล์ BAT ซ้ำ ห้ามใช้ 0.0.0.0, LAN IP หรือ Public IP

ให้ดำเนินการตามลำดับนี้:

1. ตรวจว่าเป็น Windows 10/11 และมี `git.exe` ใช้งานได้ หากไม่มี Git ให้หยุดและแจ้งวิธีติดตั้ง Git for Windows ห้ามติดตั้ง Git, เปลี่ยน Global Git config หรือขอสิทธิ์ Administrator เอง

2. ใช้เฉพาะ `GITHUB_REPOSITORY` ที่กำหนดไว้ และตรวจ Release gate ก่อน Clone ดังนี้:
   - เรียก GitHub REST API ของ Repository ทางการที่ `/releases/tags/<GITHUB_TAG>` ต้องได้ Release ที่ `tag_name` ตรง, `draft=false`, มี `published_at` และมี Asset ขนาดมากกว่า 0 ครบทั้ง `Metafxclub-AI-Agent-HQ-<GITHUB_TAG>-Windows.zip` กับไฟล์ชื่อเดียวกันต่อท้าย `.sha256`
   - ดาวน์โหลดเฉพาะไฟล์ `.sha256` ไปยัง TEMP แล้วตรวจว่าเป็นบรรทัดรูปแบบ `<SHA-256 64 ตัว>  <ชื่อ ZIP ที่กำหนด>` เท่านั้น จากนั้นลบไฟล์ TEMP นี้เมื่อจบ ห้ามใช้ ZIP Asset แทน Git Clone
   - รันคำสั่งที่เทียบเท่า `git ls-remote --exit-code --tags "<GITHUB_REPOSITORY>" "refs/tags/<GITHUB_TAG>" "refs/tags/<GITHUB_TAG>^{}"` ต้องพบ Tag จริง จากนั้นเก็บ Commit ของบรรทัด peeled (`^{}`) ถ้ามี หรือ Commit ของ Tag โดยตรงถ้าเป็น lightweight tag ไว้เป็น `REMOTE_TAG_COMMIT`
   - เรียก GitHub REST API `/commits/<REMOTE_TAG_COMMIT>/status` และต้องพบสถานะล่าสุดที่ `context=metafxclub/release` กับ `state=success` หาก Release, Asset, checksum, Tag หรือ status gate ข้อใดไม่ครบให้หยุดทันทีและแจ้งว่าเวอร์ชันยังไม่พร้อมเผยแพร่
   ห้ามเชื่อเพียงว่า Tag มีอยู่ และห้ามเปลี่ยนไปใช้ Fork, Branch `main`, URL `latest`, Source snapshot, Release ZIP หรือ Direct ZIP Asset แม้จะติดตั้งง่ายกว่า

3. สร้างโฟลเดอร์ใหม่ชื่อสุ่มใต้ `%TEMP%` ที่ขึ้นต้นด้วย `Metafxclub-HQ-Install-` แล้ว Clone โดยเทียบเท่าคำสั่ง:
   `git clone --depth 1 --single-branch --branch "<GITHUB_TAG>" "<GITHUB_REPOSITORY>" "<SOURCE_DIR>"`
   ห้ามใช้หรือแก้ Repository เดิมของผู้เรียน ห้าม Pull/Merge/Stash/Reset งานเดิม หลัง Clone ให้ตรวจว่า `origin` ตรงกับ GITHUB_REPOSITORY, `HEAD` ตรงกับทั้ง `REMOTE_TAG_COMMIT` และ `refs/tags/GITHUB_TAG^{commit}`, อยู่ใน detached HEAD, `git status --porcelain --untracked-files=all` ว่าง และไฟล์ `VERSION` ตรงกับ EXPECTED_VERSION หากข้อใดไม่ตรงให้หยุด

4. ตรวจ GOOGLE_DESKTOP_OAUTH_JSON เฉพาะข้อมูลไฟล์: Path ต้องเป็นไฟล์จริง นามสกุล `.json` ขนาดไม่เกิน 64 KiB และไม่เป็น Link/Junction ห้ามให้ Codex เปิด อ่าน Parse หรือพิมพ์เนื้อหา JSON เอง ให้ส่งเฉพาะ Path กับ EXPECTED_GOOGLE_CLIENT_ID เข้า Installer ทางการ ซึ่งจะตรวจโครงสร้าง `installed`, ตรวจ Client ID และนำเข้าผ่าน Backend โดยไม่เปิดเผย Secret หาก Installer แจ้งว่าไฟล์ผิดประเภทหรือ Client ID ไม่ตรงให้หยุด

5. ห้ามอัปโหลด คัดลอก ย้าย หรือลบ OAuth JSON ต้นฉบับ ห้ามวาง JSON/Client Secret ใน Source, Git, Frontend, Mission หรือ Report และห้ามสร้างระบบเก็บ Credential ขึ้นมาเอง

6. จาก SOURCE_DIR ที่ตรวจแล้ว ให้อ่าน `AGENTS.md`, `README.md`, `STUDENT-QUICKSTART-TH.md` และ `docs/research-sheet-hub-setup-th.md` ก่อนติดตั้ง โดยคำสั่งใน Prompt นี้เป็นโหมด Git Clone และพอร์ตมาตรฐานที่ผู้ใช้ยืนยันไว้แล้ว จึงไม่ต้องเปลี่ยนไปใช้คู่มือเลือก Endpoint หรือดาวน์โหลด ZIP

7. ตรวจ Python 3.10-3.14 แบบ 64-bit จาก python.org ใน PATH หากไม่มี, เป็น 32-bit หรือ Version ไม่รองรับ ให้หยุดพร้อมบอกขั้นตอนติดตั้ง Python x64 และ Add Python to PATH ห้ามติดตั้ง Python, ปิด Antivirus หรือขอสิทธิ์ Administrator เอง

8. จาก SOURCE_DIR ให้เรียกคำสั่งตรวจแบบ Read-only พร้อมให้ Installer ตรวจ Git ซ้ำด้วยตัวเอง:
   `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\installer\install.ps1" -ListAvailableEndpoints -RequireVerifiedGitSource -ExpectedGitRepository "<GITHUB_REPOSITORY>" -ExpectedGitTag "<GITHUB_TAG>" -ExpectedSourceVersion "<EXPECTED_VERSION>"`
   JSON ต้องมี candidate ของ `127.0.0.1:4186` ที่ `available=true` หากไม่มีให้หยุดและแจ้งว่า Port 4186 ถูกใช้อยู่ ห้ามเลือก Port อื่น ห้ามปิด Process อื่น และห้ามเริ่มติดตั้ง

9. เรียก Installer เพียงรอบเดียวจาก SOURCE_DIR พร้อมพอร์ตและ OAuth JSON ที่ตรวจแล้ว ห้ามใช้ `-SkipLaunch`, `-SkipAutostart` หรือ BAT:
   `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\installer\install.ps1" -Port 4186 -EndpointConfirmed -RequireVerifiedGitSource -ExpectedGitRepository "<GITHUB_REPOSITORY>" -ExpectedGitTag "<GITHUB_TAG>" -ExpectedSourceVersion "<EXPECTED_VERSION>" -GoogleClientJsonPath "<Path เต็มจาก GOOGLE_DESKTOP_OAUTH_JSON>" -ExpectedGoogleClientId "<EXPECTED_GOOGLE_CLIENT_ID>"`
   รอให้ตัวติดตั้งรัน Preflight, สร้าง pinned venv, รันชุดตรวจติดตั้ง, เปิด Bridge, ตรวจ Health/หน้าเว็บ, นำเข้า OAuth Client ผ่าน DPAPI และลงทะเบียน Watchdog หลัง Login จบ ห้ามรายงานว่าสำเร็จถ้าตัวติดตั้งคืน Exit code ที่ไม่ใช่ 0 โดยรหัส partial คือ `2=Google OAuth`, `3=Watchdog` และ `4=ทั้ง Google OAuth กับ Watchdog`; Runtime ที่ Health ผ่านจะไม่ถูก Rollback ให้ซ่อมเฉพาะส่วนที่แจ้งและห้ามรันติดตั้ง Source เต็มซ้ำโดยไม่จำเป็น

10. ห้ามเรียกคำสั่งนำเข้า OAuth ซ้ำเมื่อ Installer สำเร็จ หากต้องซ่อมเฉพาะ Google หลังผู้ใช้แก้ Path/JSON แล้วเท่านั้น จึงใช้ Runtime ที่ติดตั้งจริง:
    `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Metafxclub\AI-Agent-HQ\scripts\setup-google-oauth.ps1" -ClientJsonPath "<Path เต็มจาก GOOGLE_DESKTOP_OAUTH_JSON>" -ExpectedClientId "<EXPECTED_GOOGLE_CLIENT_ID>" -SkipOpen`
    ห้ามเรียก Python/DPAPI แบบที่สร้างขึ้นเอง และห้ามแสดง Client ID เต็มหรือ Client Secret ในผลลัพธ์

    หาก Installer คืนรหัส `3` หรือ `4` ให้ซ่อมเฉพาะ Watchdog ด้วยคำสั่ง `repair_command` ที่บันทึกใน `install-result.json` หรือคำสั่งต่อไปนี้ โดยแทน `<PORT>` ด้วยพอร์ตใน `bridge-endpoint.json` (สำหรับห้องเรียนนี้ต้องเป็น 4186):
    `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Metafxclub\AI-Agent-HQ\installer\install.ps1" -RepairOnly -Port <PORT> -EndpointConfirmed -SkipGoogleSetup -SkipShortcuts`
    คำสั่งนี้ตรวจ Runtime/Health และผูก Watchdog ใหม่จากโฟลเดอร์ติดตั้งจริง ไม่ Clone หรือคัดลอก Source ซ้ำ

11. อ่าน `url`, `health_url` และ `port` จาก `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\bridge-endpoint.json` แล้วตรวจ `health_url` ต้องได้ `ok=true`, `status=ready`, `server="Metafx Local Bridge"`, `version=EXPECTED_VERSION`, `endpoint.host=127.0.0.1` และ `endpoint.port=4186` จากนั้น GET `url` ต้องได้ HTTP 200 และพบชื่อ `Metafxclub AI Agent HQ` กับปลายทาง `frontend/index.html`; GET `{url}frontend/index.html` ต้องได้ HTTP 200 และพบทั้งชื่อ `Metafxclub AI Pixel HQ` กับไฟล์เริ่มระบบ `frontend/src/app/main.js`; GET `{url}frontend/src/app/main.js` ต้องได้ HTTP 200 และเนื้อหาไม่ว่าง

12. ตรวจ GET `{url}api/props/mission_strategy_table/research-sheet/auth` ต้องได้ `clientConfigured=true` สถานะปกติของเครื่องใหม่คือ `connected=false` และ `status=authorization_required` หากเครื่องนี้เคยเชื่อม Client เดิมอย่างถูกต้องแล้วจึงยอมรับ `connected=true/status=connected` ได้ ห้ามอ้างว่า Google เชื่อมแล้วจากการบันทึก JSON เพียงอย่างเดียว

13. อ่าน `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\install-result.json` และยืนยันว่า `application_version=EXPECTED_VERSION`, `source.provenance="verified_remote_git_tag"`, `source.repository=GITHUB_REPOSITORY`, `source.tag=GITHUB_TAG`, `source.commit=REMOTE_TAG_COMMIT`, `post_install.complete=true`, `post_install.exit_code=0` และ `post_install.watchdog.status="ready"` ห้ามรายงานว่าสำเร็จหาก Provenance ถูกลดระดับหรือ Post-install ยังเป็น partial จากนั้นตรวจ Scheduled Task ชื่อ `Metafxclub AI Agent HQ Bridge` ว่ามีทั้ง Trigger ตอน Login และ Trigger ตรวจซ้ำ, Action ต้องเป็น `wscript.exe` ที่ผูกกับ Script ในโฟลเดอร์ติดตั้งจริงและ `/Port:4186` แบบตรงตัว, เรียก `scripts/check-codex-readiness.cmd` จากโฟลเดอร์ติดตั้งจริง แล้วเปิด `url` ที่อ่านจาก `bridge-endpoint.json`

14. หลังตรวจทุกอย่างผ่าน อนุญาตให้ลบได้เฉพาะ SOURCE_DIR ชั่วคราวที่ Codex สร้างเองเท่านั้น ก่อนลบต้อง Resolve absolute path ใหม่, ยืนยันว่าเป็น Directory จริง, Parent ตรงกับ canonical `%TEMP%` พอดี, ชื่อตรง `^Metafxclub-HQ-Install-[A-Za-z0-9-]+$` และ Directory ไม่มี Attribute `ReparsePoint`; หากข้อใดไม่ตรงให้ไม่ลบ ใช้การล้างแบบ Best-effort หาก Windows ยังล็อกไฟล์ให้แจ้งเป็นคำเตือน แต่ห้าม Rollback Runtime ที่ Health ผ่านแล้ว ห้ามลบ Repository อื่นหรือ OAuth JSON

15. หยุดเมื่อหน้า Agent HQ เปิดแล้ว ห้ามกดปุ่มเชื่อม Google, เลือกบัญชี, กรอกรหัสผ่าน หรือกดอนุญาตแทนฉัน แจ้งฉันว่า “ติดตั้งและนำเข้า OAuth Client สำเร็จ กรุณากดเชื่อมบัญชี Google ครั้งเดียวใน HQ”

16. เริ่มระบบใน Demo/Read-only เท่านั้น ห้ามเปิด Live Trading, ส่ง Telegram จริง, Deploy จริง, เปิด Firewall หรือ Port Forwarding ระหว่างติดตั้ง

17. สรุปท้ายงานเฉพาะ Version, Git Tag, Commit แบบย่อ, ตำแหน่งติดตั้ง, URL `http://127.0.0.1:4186/`, Health, HTTP หน้าเว็บ, สถานะ Watchdog, สถานะ Codex/Rate Limit, สถานะ Google Client แบบปิดบัง และสิ่งที่ฉันต้องกดเอง ห้ามแสดง Client Secret, Refresh Token, Access Token, Cookie, Auth file หรือเนื้อหา JSON

ทำงานต่อเนื่องได้โดยไม่ต้องถามฉันระหว่างขั้นตอน เว้นแต่พบ Git/Tag/Version ไม่ตรง, JSON ผิดประเภทหรือ Client ID ไม่ตรง, Python ไม่พร้อม, Port 4186 ไม่ว่าง, ต้องใช้สิทธิ์ Administrator, Health ไม่ผ่าน หรือถึงขั้นที่ฉันต้องอนุญาตบัญชี Google เอง
```

`EXPECTED_GOOGLE_CLIENT_ID` ใช้ตรวจว่าเลือก JSON ถูกไฟล์เท่านั้น Runtime จะอ่านค่าจริงจาก JSON ผ่าน Backend ที่โครงการเตรียมไว้ จึงห้ามนำ Client Secret หรือเนื้อหา JSON มาวางใน Prompt

การติดตั้งอัตโนมัติทำได้ถึงสถานะ `authorization_required` การ Login เลือกบัญชี และกดอนุญาต Google ต้องเป็นการกระทำของเจ้าของบัญชีเอง เมื่อต้องอัปเดตเวอร์ชัน ให้อาจารย์ส่ง Prompt ฉบับใหม่ที่ล็อก Tag/Version ใหม่ ไม่ต้องให้ผู้เรียน Pull Source หรือดาวน์โหลด ZIP เอง
