# Prompt อัปเกรด v0.9.27 — เก็บค่าตั้งและข้อมูลเดิม

ใช้กับเครื่องที่ติดตั้ง Metafxclub AI Agent HQ อยู่แล้วเท่านั้น คัดลอกข้อความในกรอบทั้งหมดไปให้ Codex บนเครื่องนั้น รุ่นนี้เปลี่ยน backend จึงต้องอัปเกรดในช่วงบำรุงรักษาที่เจ้าของเครื่องหยุด HQ ไว้แล้ว หาก Bridge ยังเปิดอยู่ ตัวติดตั้งจะปฏิเสธก่อนเปลี่ยนบริการ ตัวช่วยต้องรายงานและรอช่วงบำรุงรักษา ไม่ปิดสภา เปลี่ยนค่าตั้ง หรือปิดออเดอร์ให้เอง

```text
ช่วยอัปเกรด Metafxclub AI Agent HQ บน Windows เครื่องนี้เป็นรุ่นที่ล็อกไว้ โดยรักษาค่าตั้งเดิมและข้อมูลของฉัน

GITHUB_REPOSITORY = "https://github.com/metafxclub/metafxclub-ai-agent-hq.git"
GITHUB_TAG = "v0.9.27"
EXPECTED_VERSION = "0.9.27"
INSTALL_ROOT = "%LOCALAPPDATA%\Metafxclub\AI-Agent-HQ"

นี่คือคำสั่งอัปเกรด ไม่ใช่ติดตั้งใหม่หรือรีเซ็ตเครื่อง ห้ามส่ง/แก้/ปิดออเดอร์ เปลี่ยน EA Inputs/risk/account/timeframe/key เปิดหรือปิด Live/AutoTrading เปลี่ยนการตั้งสภา AI หยุดหรือเปิด MT4/MT5 หรือลบข้อมูลของฉัน หากยังมีงานสภา/Agent/คำสั่งเทรดหรือระบบเทรดอัตโนมัติที่ทำให้การอัปเกรดไม่ปลอดภัย ให้หยุดก่อนแตะบริการและรายงานเหตุผล ไม่ทำให้ระบบว่างด้วยการปิดงานเอง

1. ตรวจว่าเป็น Windows 10/11 x64 และมี Git กับ Python 3.10–3.14 x64 ที่ใช้งานได้ ใช้ของเดิม ไม่ติดตั้งซ้ำหรืออัปเกรด global packages ถ้าขาดให้รายงานก่อนทำต่อ ตรวจ INSTALL_ROOT ว่ามีโปรแกรมเดิมจริง หากไม่มีให้ใช้ prompt ติดตั้งใหม่ของ tag นี้แทน

2. อ่านเฉพาะสถานะและ metadata ที่จำเป็นจาก data/runtime/bridge-endpoint.json และ VERSION ยืนยัน install identity และ endpoint ที่บันทึกไว้ว่าตรง INSTALL_ROOT หาก HQ ถูกหยุดเพื่อบำรุงรักษาแล้ว การเชื่อม /api/health ไม่ได้เป็นสถานะที่คาดหมาย ห้ามเปิด HQ ขึ้นมาเพียงเพื่อให้ Health ผ่านก่อนอัปเกรด หากยังตอบ Health อยู่ให้ถือว่ายังไม่พร้อมอัปเกรดและหยุด บันทึก version/endpoint/status กับ hash ของไฟล์การตั้งที่จำเป็นโดยไม่แสดงเนื้อหาที่เป็นความลับ รักษาพอร์ตเดิมที่ตรวจแล้ว: ฉันยืนยันให้ใช้ 127.0.0.1 และพอร์ตเดิมนั้น ห้ามสลับไป 4186 หรือพอร์ตอื่นเอง ห้ามอ่านหรือแสดง Token/Password/Cookie/Auth/signing key/DPAPI payload

3. ตรวจ release ที่ https://api.github.com/repos/metafxclub/metafxclub-ai-agent-hq/releases/tags/v0.9.27 ต้องเป็น tag ที่ตรง ไม่เป็น draft/prerelease มี published_at และ assets สองไฟล์:
   Metafxclub-AI-Agent-HQ-v0.9.27-Windows.zip
   Metafxclub-AI-Agent-HQ-v0.9.27-Windows.zip.sha256
   ดาวน์โหลดเฉพาะ browser_download_url ของสองไฟล์นี้จาก repository/tag ทางการผ่าน HTTPS ลงโฟลเดอร์ใหม่ใต้ TEMP ยอมให้ redirect เฉพาะ GitHub official asset CDN ตรวจชื่อ ขนาด และ SHA-256 ให้ตรง ไฟล์ checksum ต้องมีหนึ่งบรรทัดรูปแบบ hash 64 ตัวตามด้วยชื่อ ZIP ที่ระบุ หากไม่ตรงให้หยุดก่อน extract

4. ตรวจ git ls-remote --tags ของ repository/tag ที่ล็อกไว้ ใช้ peeled commit ถ้ามี แล้วตรวจ GitHub /commits/<commit>/status ว่าสถานะล่าสุดของ context metafxclub/release เป็น success ก่อนดำเนินการ ห้ามใช้ main, latest, fork หรือ source snapshot แทน

5. สร้าง SOURCE_DIR ใหม่ชื่อสุ่มใต้ TEMP ขึ้นต้น Metafxclub-HQ-Update- และ clone --depth 1 --single-branch --branch v0.9.27 จาก GITHUB_REPOSITORY ตรวจ origin/HEAD/refs/tags/v0.9.27^{commit} ให้ตรง remote commit, detached HEAD, git status --porcelain --untracked-files=all ว่าง และ VERSION เป็น 0.9.27 ห้าม pull/merge/stash/reset หรือแก้ repo เดิมของฉัน

6. อ่าน AGENTS.md, README.md, STUDENT-QUICKSTART-TH.md, docs/releases/v0.9.27-th.md และ docs/research-sheet-hub-setup-th.md จาก SOURCE_DIR โดยคำสั่งนี้กำหนดโหมดอัปเกรดแบบรักษาค่าไว้ชัดเจน จึงห้ามใช้ -ResetGoogleOAuthToCentralRelease, -RepairOnly, -PackageSmoke หรือสลับ endpoint เพื่อให้ผ่าน

7. เตรียมเฉพาะ native app client metadata กลางจาก release ที่ตรวจ hash แล้ว: ยืนยันว่า backend/local-runner/google_oauth_native_client.txt ไม่อยู่ใน Git index และถูก ignore เปิด ZIP แบบอ่านอย่างเดียว เลือก regular entry ตรง Metafxclub-AI-Agent-HQ-v0.9.27/backend/local-runner/google_oauth_native_client.txt เพียงหนึ่งรายการ ปฏิเสธ duplicate/path traversal/absolute path/directory/symlink/reparse point เขียนไฟล์นี้แบบ atomic ลง SOURCE_DIR โดยไม่พิมพ์ค่าเต็ม ห้าม extract โค้ดอื่นทับ Git tree และตรวจ worktree ยังสะอาด ห้ามนำ auth/token ของเครื่องอื่นมาใช้

8. ก่อนแก้บริการ รันจาก SOURCE_DIR:
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -ListAvailableEndpoints -RequireVerifiedGitSource -ExpectedGitRepository "<GITHUB_REPOSITORY>" -ExpectedGitTag "v0.9.27" -ExpectedSourceVersion "0.9.27" -ExpectedGitCommit "<REMOTE_TAG_COMMIT>"
   ต้องพบ endpoint เดิมที่ available=true และยืนยัน ownership ได้ ห้ามหยุด process อื่นหรือเปลี่ยนพอร์ตเพื่อแก้ปัญหา

9. เรียก installer จาก SOURCE_DIR เพียงรอบเดียว:
   powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Port <SAVED_PORT> -EndpointConfirmed -RequireVerifiedGitSource -ExpectedGitRepository "<GITHUB_REPOSITORY>" -ExpectedGitTag "v0.9.27" -ExpectedSourceVersion "0.9.27" -ExpectedGitCommit "<REMOTE_TAG_COMMIT>"
   ให้ตัวติดตั้งทำ preflight/backup/pinned dependency/upgrade/rollback ตามปกติ ห้ามคัดลอก .venv เอง ห้ามลด TLS หรือข้าม guard หาก Bridge เดิมยังรันอยู่ แม้ขณะนั้นไม่มีงาน หรือมี Council/Agent/EA/คำสั่งที่ทำให้ไม่ปลอดภัย ให้หยุดและเก็บโปรแกรมเดิมไว้ รอฉันเลือกช่วงบำรุงรักษา ไม่หยุด HQ/ระบบเทรดหรือเปลี่ยน config เพื่อข้าม guard หากต้องการคำแนะนำการหยุดอย่างปลอดภัยให้ตรวจสถานะปัจจุบันและเสนอขั้นตอนก่อน ห้ามถือ prompt นี้เป็นคำอนุญาตให้หยุดสภาที่กำลังรัน

10. เก็บ data/runtime, workspace, Mission/Report/history, โหมดเดิม, การเชื่อม Google/Myfxbook, MT4/MT5 targets และ SentimentUniverse private state ไว้ รวม data/runtime/sentiment-news-ai/days และ result/state เพื่อไม่ให้วิเคราะห์ข่าวซ้ำ ห้ามลบ ledger, เปลี่ยนค่า quota/risk หรือเปิด FX28/ตัวดึงข่าวเก่าให้รันคู่กัน ห้าม deploy EA ไปทับ Terminal/กราฟที่เปิดอยู่

11. หลัง installer สำเร็จ อ่าน install-result และตรวจ VERSION/Health/endpoint/version/agentRosterComplete ตาม contract ตรวจสถานะ Sheet service และ Sentiment Universe ด้วย health แบบอ่านอย่างเดียว ตรวจค่าตั้งที่คาดว่าจะคงเดิมและ MT4/MT5 process เทียบก่อนทำ ห้ามเรียก gateway endpoint ที่ provision/ingest/dispatch หรือสั่งวิเคราะห์เพื่อทดสอบ หาก exit code ไม่เป็น 0 หรือเกิด partial failure ให้รายงานตามจริง ไม่รันติดตั้งเต็มซ้ำและไม่ปิด guard

12. เปิดหน้าเดิมหรือรีเฟรช แล้วสรุป version, URL, สถานะบริการ, ค่าที่คงเดิม, สิ่งที่ยังต้องให้ฉันทำเองพร้อมแหล่งหลักฐาน ไม่อ้างว่าส่งออเดอร์จริงผ่านหากไม่ได้มีผลตามธรรมชาติที่ตรวจได้ การเชื่อมบัญชีหรือให้ Consent ต้องเป็นฉันทำเองเท่านั้น ห้ามส่ง credentials ในแชต
```
