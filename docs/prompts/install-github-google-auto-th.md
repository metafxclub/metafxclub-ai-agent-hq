# Prompt ติดตั้งด้วย Codex จาก GitHub Clone พร้อม OAuth Client กลาง

Prompt นี้ใช้สำหรับให้นักเรียนวางใน Codex บน Windows เพียงครั้งเดียว Codex จะตรวจและติดตั้งเฉพาะ Git/Python ที่ขาดแบบ current-user, Clone Source รุ่นที่ล็อกไว้จาก GitHub, ตรวจ Tag/Version, ดาวน์โหลดและตรวจ Release ZIP + `.sha256`, extract เฉพาะ OAuth native/installed-app client configuration กลางที่ถูก inject ตอน build, เรียก Installer, ตรวจ Runtime และเปิด Agent HQ ให้เอง นักเรียนไม่ต้องติดตั้ง Git/Python ล่วงหน้า ไม่ต้องดาวน์โหลด ZIP เอง และไม่ต้องกดไฟล์ BAT

ก่อนส่งให้นักเรียน อาจารย์ล็อกค่า `GITHUB_REPOSITORY`, `GITHUB_TAG` และ `EXPECTED_VERSION` ไว้แล้ว นักเรียนวาง Prompt ได้ทันทีโดยไม่ต้องสร้าง Google Cloud Project/OAuth Client, เพิ่ม Test users, ดาวน์โหลด JSON หรือกรอก/แก้ Client ID กลาง:

หาก Sensitive Scope ของ OAuth app กลางยังอยู่ระหว่างตรวจสอบ ผู้ใช้ใหม่อาจเห็นหน้า `Google ยังไม่ได้ยืนยันแอปนี้` และ Project กลางอาจอยู่ภายใต้ OAuth unverified user cap การติดตั้งยังต้องหยุดเมื่อถึงหน้าที่เจ้าของบัญชีต้องเลือกบัญชีและให้ Consent เอง

```text
ช่วยติดตั้ง Metafxclub AI Agent HQ บน Windows User ปัจจุบันให้เสร็จอัตโนมัติ โดยให้คุณ Clone Tag จาก GitHub, ดาวน์โหลด Release ZIP กับ `.sha256` เพื่อตรวจและนำเข้าเฉพาะ Client กลาง แล้วเรียก Installer เอง ฉันจะไม่ดาวน์โหลด ZIP และไม่กดไฟล์ BAT

GITHUB_REPOSITORY = "https://github.com/metafxclub/metafxclub-ai-agent-hq.git"
GITHUB_TAG = "v0.9.18"
EXPECTED_VERSION = "0.9.18"

ข้อความนี้เป็นการยืนยันล่วงหน้าให้ Codex ใช้ Local endpoint มาตรฐาน `http://127.0.0.1:4186/` และส่งพอร์ต 4186 เข้า Installer ด้วย `-EndpointConfirmed` ได้ ไม่ต้องถามฉันให้เลือก Port หรือกดไฟล์ BAT ซ้ำ ห้ามใช้ 0.0.0.0, LAN IP หรือ Public IP

ข้อความนี้อนุญาตล่วงหน้าให้ Codex ติดตั้งแบบ current-user ได้เฉพาะ `Git.Git` และ `Python.Python.3.13` จาก Source `winget` เมื่อรายการนั้นขาดจริงเท่านั้น ไม่อนุญาตให้ติดตั้งซอฟต์แวร์อื่น, ถอน/อัปเกรดของเดิม, ใช้ Machine scope, ขอสิทธิ์ Administrator, ปิดระบบป้องกัน หรือเปลี่ยนค่าระบบถาวร

ให้ดำเนินการตามลำดับนี้:

1. ตรวจว่าเป็น Windows 10/11 แบบ 64-bit แล้ว Bootstrap สิ่งที่ขาดแบบ idempotent ก่อนตรวจ Release:
   - ก่อนตรวจครั้งแรก ให้ Refresh เฉพาะ Process PATH โดย Merge Process PATH เดิมกับ Machine PATH และ User PATH ที่อ่านใหม่ ตัดเฉพาะรายการซ้ำโดยไม่ทิ้ง Path เดิม ห้ามใช้ `setx` หรือเขียนค่า PATH ถาวร
   - ตรวจ `git.exe` ที่เป็น Application จริงด้วย Path เต็ม Path ต้องเป็น Local absolute path ไม่ใช่ UNC, ReparsePoint หรือไฟล์ใต้ `%TEMP%`; ตรวจ Authenticode `Status=Valid`, `ProductName=Git` และ `CompanyName=The Git Development Community` ก่อนเรียกไฟล์ จากนั้นรัน `git version --build-options` ด้วย Path เต็มและ argument แยก ต้องได้ Version, `cpu: x86_64` และ `sizeof-size_t: 8`; ถ้าผ่านให้บันทึก Path/Version/Architecture และใช้ของเดิมทันที ห้ามเรียก Winget, อัปเกรด หรือเปลี่ยน Global Git config หากพบ Git แต่ trust/architecture ไม่ผ่านให้หยุดโดยไม่ติดตั้งทับ
   - ตรวจ `py.exe` เฉพาะเมื่อเป็น Local application จริง, ไม่เป็น UNC/ReparsePoint/ไฟล์ใต้ `%TEMP%`, Authenticode `Status=Valid`, `ProductName=Python` และ `CompanyName=Python Software Foundation` จากนั้นตรวจตามลำดับ `-3.14`, `-3.13`, `-3.12`, `-3.11`, `-3.10` และ `-3` เป็นทางเลือกสุดท้าย แล้วจึงตรวจ `python.exe`/`python3.exe` ที่ไม่ใช่ WindowsApps alias ด้วยกฎ trust เดียวกัน ให้ Python คืน `sys.version_info`, `sys.executable`, `struct.calcsize('P')*8` และ `platform.machine()` และตรวจไฟล์จริงจาก `sys.executable` ซ้ำ; ถ้าพบ Python 3.10-3.14 แบบ 64-bit และ AMD64/x86_64 ให้ใช้ของเดิมทันที ห้ามติดตั้งซ้ำหรือเปลี่ยน Python default หากพบไฟล์ Python จริงแต่ trust ผิดปกติให้หยุดโดยไม่เรียกหรือติดตั้งทับ
   - หาก Git หรือ Python ที่รองรับขาดจริง ให้ตรวจ `winget.exe` และ `winget source list --name winget` ก่อน โดย Source ชื่อ `winget` ต้องมี Argument `https://cdn.winget.microsoft.com/cache` และ Type `Microsoft.PreIndexed.Package` ตรงตัว ห้าม Reset/เพิ่ม Source เอง จากนั้นตรวจ Package ที่ขาดด้วย `winget show --id <PACKAGE_ID> --exact --source winget --scope user --architecture x64 --accept-source-agreements --disable-interactivity` ก่อนติดตั้ง โดย `Git.Git` ต้องมี Publisher `The Git Development Community` และ `Python.Python.3.13` ต้องมี Publisher `Python Software Foundation`; หาก ID, Source, Publisher หรือ x64 ไม่ตรงให้หยุด
   - ติดตั้งเฉพาะรายการที่ขาดทีละรายการด้วยคำสั่งที่ตรงกัน:
     `winget install --id Git.Git --exact --source winget --scope user --architecture x64 --silent --no-upgrade --accept-package-agreements --accept-source-agreements --disable-interactivity`
     `winget install --id Python.Python.3.13 --exact --source winget --scope user --architecture x64 --silent --no-upgrade --accept-package-agreements --accept-source-agreements --disable-interactivity`
   - เรียก WinGet ได้ทีละหนึ่ง Process และรอ Exit code จริงก่อนเริ่มรายการถัดไป กำหนด Deadline รายการละ 15 นาที ห้ามเริ่ม Process ที่สอง, Retry คำสั่งเดิม, Kill Installer หรือรายงานว่าสำเร็จจากข้อความบนหน้าจอเพียงอย่างเดียว หาก Timeout, Installer busy/locked, ขอ UAC หรือแจ้ง Restart required ให้หยุดพร้อมวิธีแก้หนึ่งขั้น
   - ห้ามใช้ `winget upgrade`, `winget uninstall`, `--force`, `--ignore-security-hash`, `--override`, Local manifest, Mirror, `Invoke-Expression`, คำสั่งดาวน์โหลดแล้ว Pipe เข้า PowerShell หรือ `Start-Process -Verb RunAs`; ห้ามแก้ Machine/User PATH แบบถาวร, ปิด UAC, Defender, Antivirus หรือ Firewall
   - หลังติดตั้ง ให้ Refresh เฉพาะ Process PATH ด้วยวิธี Merge แบบเดิมโดยไม่ใช้ `setx`, Resolve executable ใหม่จากศูนย์ และตรวจ Git/Python ซ้ำด้วยเกณฑ์เดิม ก่อนเริ่ม Clone ต้องรายงานแต่ละรายการเป็น `existing` หรือ `installed_this_run` พร้อม Path, Version และ Architecture
   - หากไม่มี Winget, Source/Publisher ผิด, ติดตั้งแบบ user scope ไม่สำเร็จ, ต้องใช้ UAC/Admin/Restart หรือการตรวจหลังติดตั้งไม่ผ่าน ให้หยุดพร้อมสาเหตุและการแก้เพียงขั้นเดียว ห้ามเปลี่ยนไปใช้ Package/Source อื่นและห้ามเริ่ม Clone; เมื่อนักเรียนแก้แล้วสามารถวาง Prompt เดิมซ้ำได้ โดยรายการที่พร้อมแล้วต้องไม่ถูกติดตั้งซ้ำ

2. ใช้เฉพาะ `GITHUB_REPOSITORY` ที่กำหนดไว้ และตรวจ Release gate ก่อน Clone ดังนี้:
   - เรียก GitHub REST API ของ Repository ทางการที่ `/releases/tags/<GITHUB_TAG>` ต้องได้ Release ที่ `tag_name` ตรง, `draft=false`, มี `published_at` และมี Asset ขนาดมากกว่า 0 ครบทั้ง `Metafxclub-AI-Agent-HQ-<GITHUB_TAG>-Windows.zip` กับไฟล์ชื่อเดียวกันต่อท้าย `.sha256`
   - เก็บ `browser_download_url`, ชื่อ และขนาดจาก Release API เฉพาะ Asset สองไฟล์นี้ โดย URL เริ่มต้นต้องอยู่ใต้ Repository/Tag ทางการ จากนั้นดาวน์โหลดทั้ง ZIP และ `.sha256` ไปยังโฟลเดอร์ TEMP ใหม่ผ่าน HTTPS เท่านั้น ยอมให้ redirect ได้เฉพาะ CDN Asset ทางการของ GitHub (`objects.githubusercontent.com` หรือ `release-assets.githubusercontent.com`) ห้ามใช้ URL `latest`, Host อื่น หรือ Asset ชื่อคล้ายกัน
   - ตรวจไฟล์ `.sha256` ว่ามีเพียงหนึ่งบรรทัดรูปแบบ `<SHA-256 64 ตัว>  <ชื่อ ZIP ที่กำหนด>` แล้วรัน `Get-FileHash -Algorithm SHA256` กับ ZIP ต้องตรงกันทุกตัวอักษรและขนาดไฟล์ต้องตรงกับ Release API หากไม่ตรงให้หยุดและลบไฟล์ชั่วคราว ห้าม extract หรือเรียกไฟล์ใดจาก ZIP
   - รันคำสั่งที่เทียบเท่า `git ls-remote --exit-code --tags "<GITHUB_REPOSITORY>" "refs/tags/<GITHUB_TAG>" "refs/tags/<GITHUB_TAG>^{}"` ต้องพบ Tag จริง จากนั้นเก็บ Commit ของบรรทัด peeled (`^{}`) ถ้ามี หรือ Commit ของ Tag โดยตรงถ้าเป็น lightweight tag ไว้เป็น `REMOTE_TAG_COMMIT`
   - เรียก GitHub REST API `/commits/<REMOTE_TAG_COMMIT>/status` และต้องพบสถานะล่าสุดที่ `context=metafxclub/release` กับ `state=success` หาก Release, Asset, checksum, Tag หรือ status gate ข้อใดไม่ครบให้หยุดทันทีและแจ้งว่าเวอร์ชันยังไม่พร้อมเผยแพร่
   ห้ามเชื่อเพียงว่า Tag มีอยู่ และห้ามเปลี่ยนไปใช้ Fork, Branch `main`, URL `latest`, Source snapshot หรือใช้ Release ZIP เป็น Source code แทน Git Clone แม้จะติดตั้งง่ายกว่า ZIP ใช้ได้เฉพาะนำเข้าไฟล์ Client กลางตามข้อ 4 หลังตรวจ hash ผ่านแล้ว

3. สร้างโฟลเดอร์ใหม่ชื่อสุ่มใต้ `%TEMP%` ที่ขึ้นต้นด้วย `Metafxclub-HQ-Install-` แล้ว Clone โดยเทียบเท่าคำสั่ง:
   `git clone --depth 1 --single-branch --branch "<GITHUB_TAG>" "<GITHUB_REPOSITORY>" "<SOURCE_DIR>"`
   ห้ามใช้หรือแก้ Repository เดิมของผู้เรียน ห้าม Pull/Merge/Stash/Reset งานเดิม หลัง Clone ให้ตรวจว่า `origin` ตรงกับ GITHUB_REPOSITORY, `HEAD` ตรงกับทั้ง `REMOTE_TAG_COMMIT` และ `refs/tags/GITHUB_TAG^{commit}`, อยู่ใน detached HEAD, `git status --porcelain --untracked-files=all` ว่าง และไฟล์ `VERSION` ตรงกับ EXPECTED_VERSION หากข้อใดไม่ตรงให้หยุด

4. เส้นทางหลักต้องใช้ OAuth native/installed-app client configuration กลางที่ GitHub Actions inject จาก Release secrets ตอน build Asset เท่านั้น ไฟล์จริงต้องไม่อยู่ใน public Git tree หลัง Clone ให้ยืนยันว่า `backend/local-runner/google_oauth_native_client.txt` ไม่มีอยู่ใน Git index, คำสั่ง `git check-ignore -q -- backend/local-runner/google_oauth_native_client.txt` ผ่าน และ worktree ยังสะอาด จาก ZIP ที่ตรวจ hash แล้ว ให้เปิดแบบอ่านอย่างเดียวและยอมรับเฉพาะ entry ปกติที่ path ตรง `Metafxclub-AI-Agent-HQ-<GITHUB_TAG>/backend/local-runner/google_oauth_native_client.txt` เพียงหนึ่งรายการ (เช่น `Metafxclub-AI-Agent-HQ-v0.9.18/...`) ห้ามมี absolute path, `..`, duplicate, directory, symlink หรือ ReparsePoint อ่าน bytes ของ entry นี้แล้วเขียนแบบ atomic ไปที่ `SOURCE_DIR/backend/local-runner/google_oauth_native_client.txt` โดยตัดเฉพาะชื่อ root ของ Archive ออก ห้าม extract ไฟล์อื่นหรือทับ Source จาก Git และตรวจ `git status --porcelain --untracked-files=all` ต้องยังว่างเพราะไฟล์ถูก ignore

   ไฟล์ Client กลางมี `client_id` และ `client_secret` ของ installed app ซึ่งเป็น app metadata ที่ต้องแจกพร้อมโปรแกรม ไม่ใช่ Credential ของบัญชีนักเรียน แต่ห้าม commit ค่าจริงลง public Source และห้ามพิมพ์ค่าเต็มใน console, Chat, Frontend, Mission, Report หรือ Log ห้ามถามนักเรียนหา Client ID, Client Secret, OAuth JSON หรือ Google Cloud Project Installer ทางการต้องตรวจรูปแบบและ metadata ด้วย Release preflight เอง หากไฟล์ขาดหรือรูปแบบไม่ถูกต้องให้หยุดและแจ้งว่า Release Asset ไม่สมบูรณ์ ห้ามแก้ด้วย Credential ของนักเรียนแบบเงียบ ๆ

5. ห้ามอัปโหลด คัดลอก หรือสร้าง OAuth JSON ของนักเรียนระหว่างติดตั้ง ห้ามนำค่า Client กลางจาก Release Asset ไป commit หรือคัดลอกไว้นอก SOURCE_DIR/Runtime ที่กำหนด และห้ามพิมพ์ค่าเต็มลง Frontend, Mission, Report หรือ Log Access token, Refresh token, Authorization code, Cookie, รหัสผ่าน และ Credential ของบัญชีผู้ใช้ต้องไม่เข้า Source, Git, Frontend, Mission, Report หรือ Log และห้ามสร้างระบบเก็บ Credential ขึ้นมาเอง นักเรียนต้องทำเองเฉพาะกดเชื่อม Google, เลือกบัญชี และยืนยัน Consent ใน System Browser

6. จาก SOURCE_DIR ที่ตรวจแล้ว ให้อ่าน `AGENTS.md`, `README.md`, `STUDENT-QUICKSTART-TH.md` และ `docs/research-sheet-hub-setup-th.md` ก่อนติดตั้ง โดยคำสั่งใน Prompt นี้เป็นโหมด Git Clone และพอร์ตมาตรฐานที่ผู้ใช้ยืนยันไว้แล้ว จึงไม่ต้องเปลี่ยนไปใช้คู่มือเลือก Endpoint หรือใช้ ZIP เป็น Source ติดตั้ง; ZIP ที่ตรวจแล้วมีหน้าที่ส่งมอบ Client กลางเพียงไฟล์เดียวตามข้อ 4

7. ตรวจ Git และ Python ซ้ำจาก Path ที่ Resolve หลัง Bootstrap: Git ต้องเรียกใช้งานได้ และ Python ต้องเป็น 3.10-3.14 แบบ 64-bit หากข้อใดไม่ผ่านให้หยุดก่อนเรียก Installer ห้ามติดตั้ง Dependency แบบ Global เพราะ Installer จะสร้าง pinned Virtual Environment แยกเอง

8. จาก SOURCE_DIR ให้เรียกคำสั่งตรวจแบบ Read-only พร้อมให้ Installer ตรวจ Git ซ้ำด้วยตัวเอง:
   `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\installer\install.ps1" -ListAvailableEndpoints -RequireVerifiedGitSource -ExpectedGitRepository "<GITHUB_REPOSITORY>" -ExpectedGitTag "<GITHUB_TAG>" -ExpectedSourceVersion "<EXPECTED_VERSION>"`
   JSON ต้องมี candidate ของ `127.0.0.1:4186` ที่ `available=true` หากไม่มีให้หยุดและแจ้งว่า Port 4186 ถูกใช้อยู่ ห้ามเลือก Port อื่น ห้ามปิด Process อื่น และห้ามเริ่มติดตั้ง

9. เรียก Installer เพียงรอบเดียวจาก SOURCE_DIR พร้อมพอร์ตที่ยืนยันแล้ว โดยไม่ส่ง Credential หรือค่า Google เพิ่มเติม ห้ามใช้ `-SkipLaunch`, `-SkipAutostart` หรือ BAT:
   `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\installer\install.ps1" -Port 4186 -EndpointConfirmed -RequireVerifiedGitSource -ExpectedGitRepository "<GITHUB_REPOSITORY>" -ExpectedGitTag "<GITHUB_TAG>" -ExpectedSourceVersion "<EXPECTED_VERSION>"`
   รอให้ตัวติดตั้งรัน Preflight, สร้าง pinned venv, รันชุดตรวจติดตั้ง, เปิด Bridge, ตรวจ Health/หน้าเว็บ, ยืนยัน OAuth native-app client configuration กลางจาก Release และลงทะเบียน Watchdog หลัง Login จบ ห้ามรายงานว่าสำเร็จถ้าตัวติดตั้งคืน Exit code ที่ไม่ใช่ 0 โดยรหัส partial คือ `2=Google OAuth`, `3=Watchdog` และ `4=ทั้ง Google OAuth กับ Watchdog`; Runtime ที่ Health ผ่านจะไม่ถูก Rollback ให้ซ่อมเฉพาะส่วนที่แจ้งและห้ามรันติดตั้ง Source เต็มซ้ำโดยไม่จำเป็น

10. ห้ามเรียกขั้นตอนนำเข้า OAuth Client แบบกำหนดเองเมื่อ Installer สำเร็จ หาก Client กลางไม่พร้อม ให้หยุดและให้อาจารย์แก้ Release แล้วออก Tag ใหม่ ห้ามเปลี่ยนไปขอ JSON หรือ Client ID จากนักเรียน โหมด custom override เป็น Advanced/Recovery แยกจาก Prompt ห้องเรียนนี้และใช้ได้เฉพาะเมื่อเจ้าของ OAuth Project ตั้งใจดำเนินการเอง

    หาก Installer คืนรหัส `3` หรือ `4` ให้ซ่อมเฉพาะ Watchdog ด้วยคำสั่ง `repair_command` ที่บันทึกใน `install-result.json` หรือคำสั่งต่อไปนี้ โดยแทน `<PORT>` ด้วยพอร์ตใน `bridge-endpoint.json` (สำหรับห้องเรียนนี้ต้องเป็น 4186):
    `powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Metafxclub\AI-Agent-HQ\installer\install.ps1" -RepairOnly -Port <PORT> -EndpointConfirmed -SkipGoogleSetup -SkipShortcuts`
    คำสั่งนี้ตรวจ Runtime/Health และผูก Watchdog ใหม่จากโฟลเดอร์ติดตั้งจริง ไม่ Clone หรือคัดลอก Source ซ้ำ

11. อ่าน `url`, `health_url` และ `port` จาก `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\bridge-endpoint.json` แล้วตรวจ `health_url` ต้องได้ `ok=true`, `status=ready`, `server="Metafx Local Bridge"`, `version=EXPECTED_VERSION`, `endpoint.host=127.0.0.1` และ `endpoint.port=4186` จากนั้น GET `url` ต้องได้ HTTP 200 และพบชื่อ `Metafxclub AI Agent HQ` กับปลายทาง `frontend/index.html`; GET `{url}frontend/index.html` ต้องได้ HTTP 200 และพบทั้งชื่อ `Metafxclub AI Pixel HQ` กับไฟล์เริ่มระบบ `frontend/src/app/main.js`; GET `{url}frontend/src/app/main.js` ต้องได้ HTTP 200 และเนื้อหาไม่ว่าง

12. ตรวจ GET `{url}api/props/mission_strategy_table/research-sheet/auth` ต้องได้ `clientConfigured=true` จาก Client กลางใน Release สถานะปกติของเครื่องใหม่คือ `connected=false` และ `status=authorization_required` หากเครื่องนี้เคยเชื่อมบัญชีอย่างถูกต้องแล้วจึงยอมรับ `connected=true/status=connected` ได้ ห้ามอ้างว่า Google เชื่อมแล้วเพียงเพราะ Client กลางพร้อม

13. อ่าน `%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ\data\runtime\install-result.json` และยืนยันว่า `application_version=EXPECTED_VERSION`, `source.provenance="verified_remote_git_tag"`, `source.repository=GITHUB_REPOSITORY`, `source.tag=GITHUB_TAG`, `source.commit=REMOTE_TAG_COMMIT`, `post_install.complete=true`, `post_install.exit_code=0`, `post_install.watchdog.status="ready"`, `post_install.google_oauth_client.requested=true`, `post_install.google_oauth_client.status="ready_central"` และ `post_install.google_oauth_client.source="central_release"` ห้ามรายงานว่าสำเร็จหาก Provenance ถูกลดระดับ, Client กลางไม่พร้อม หรือ Post-install ยังเป็น partial จากนั้นตรวจ Scheduled Task ชื่อ `Metafxclub AI Agent HQ Bridge` ว่ามีทั้ง Trigger ตอน Login และ Trigger ตรวจซ้ำ, Action ต้องเป็น `wscript.exe` ที่ผูกกับ Script ในโฟลเดอร์ติดตั้งจริงและ `/Port:4186` แบบตรงตัว, เรียก `scripts/check-codex-readiness.cmd` จากโฟลเดอร์ติดตั้งจริง แล้วเปิด `url` ที่อ่านจาก `bridge-endpoint.json`
    หากเครื่องมี **Advanced/Recovery custom override** ที่ผู้ดูแลตั้งไว้ก่อนแล้ว Installer อาจรายงาน `ready_existing_override` แทนได้ แต่ต้องไม่สร้างหรือขอ Override ใหม่จากนักเรียนเพื่อเลี่ยง Client กลาง

14. หลังตรวจทุกอย่างผ่าน อนุญาตให้ลบได้เฉพาะ SOURCE_DIR และโฟลเดอร์ดาวน์โหลด ZIP/`.sha256` ชั่วคราวที่ Codex สร้างเองเท่านั้น ก่อนลบต้อง Resolve absolute path ใหม่, ยืนยันว่าเป็น Directory จริง, Parent ตรงกับ canonical `%TEMP%` พอดี, ชื่อตรงรูปแบบที่ Prompt กำหนด และ Directory ไม่มี Attribute `ReparsePoint`; หากข้อใดไม่ตรงให้ไม่ลบ ใช้การล้างแบบ Best-effort หาก Windows ยังล็อกไฟล์ให้แจ้งเป็นคำเตือน แต่ห้าม Rollback Runtime ที่ Health ผ่านแล้ว และห้ามลบ Repository อื่นหรือไฟล์ Client กลางจาก Runtime ที่ติดตั้งจริง

15. หยุดเมื่อหน้า Agent HQ เปิดแล้ว ห้ามกดปุ่มเชื่อม Google, เลือกบัญชี, กรอกรหัสผ่าน หรือกดอนุญาตแทนฉัน แจ้งฉันว่า “ติดตั้งและตรวจ OAuth Client กลางสำเร็จ กรุณากดเชื่อมบัญชี Google ครั้งเดียวใน HQ” หากแอปยัง Under review ให้แจ้งด้วยว่าหน้า Unverified warning และ OAuth user cap อาจยังมีอยู่ชั่วคราว

16. เริ่มระบบใน Demo/Read-only เท่านั้น ห้ามเปิด Live Trading, ส่ง Telegram จริง, Deploy จริง, เปิด Firewall หรือ Port Forwarding ระหว่างติดตั้ง

17. สรุปท้ายงานเฉพาะสถานะ Git/Python (`existing` หรือ `installed_this_run`), Path/Version/Architecture, Version, Git Tag, Commit แบบย่อ, ตำแหน่งติดตั้ง, URL `http://127.0.0.1:4186/`, Health, HTTP หน้าเว็บ, สถานะ Watchdog, สถานะ Codex/Rate Limit, สถานะ Google Client ว่า `ready_central` โดยไม่แสดง Client ID/Client Secret กลาง และสิ่งที่ฉันต้องกดเอง ห้ามแสดง Refresh Token, Access Token, Cookie, Auth file หรือเนื้อหา JSON

ทำงานต่อเนื่องได้โดยไม่ต้องถามฉันระหว่างขั้นตอน เว้นแต่ Bootstrap/การยืนยัน Git หรือ Python ไม่สำเร็จ, Git/Tag/Version ไม่ตรง, Client กลางใน Release ไม่พร้อม, Port 4186 ไม่ว่าง, ต้องใช้ UAC/Administrator/Restart, Health ไม่ผ่าน หรือถึงขั้นที่ฉันต้องอนุญาตบัญชี Google เอง
```

`2-SETUP-GOOGLE-HQ.bat` และ Desktop OAuth JSON ยังคงมีไว้เฉพาะ **Advanced/Recovery custom override** สำหรับเจ้าของระบบที่ตั้งใจใช้ OAuth Project ของตนเอง ไม่ใช่ส่วนหนึ่งของ Prompt ห้องเรียน ผู้เรียนปกติไม่ต้องเปิด BAT นี้ ไม่ต้องขอไฟล์จากผู้สอน และห้ามนำค่า Client หรือเนื้อหา JSON ของ Override มาวางใน Prompt

การติดตั้งอัตโนมัติทำได้ถึงสถานะ `authorization_required` ด้วย Client กลาง การ Login เลือกบัญชี และกดอนุญาต Google ต้องเป็นการกระทำของเจ้าของบัญชีเอง เมื่อต้องอัปเดตเวอร์ชัน ให้อาจารย์ส่ง Prompt ฉบับใหม่ที่ล็อก Tag/Version ใหม่ ไม่ต้องให้ผู้เรียน Pull Source หรือดาวน์โหลด ZIP เอง
