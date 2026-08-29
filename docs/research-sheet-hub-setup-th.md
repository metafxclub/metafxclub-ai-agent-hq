# Google Sheet กลางสำหรับระบบ Research

ระบบใช้ Google Sheet กลางเพียงรายการเดียว โดยตั้ง URL หรือ Sheet ID ที่ **โต๊ะวางแผน Mission** แล้ว Backend จะผูก **3 แท็บคงที่เท่านั้น** ให้กับ 4 ระบบที่เชื่อม: Radar ระบบโลก, คลังวิจัยเชิงลึก, โรงงาน EA และ Radar Website Tool โดยโรงงาน EA อ่านร่วมจาก `Deep_Research` แบบ Read-only จึงไม่ใช่ Consumer หลักหรือแท็บที่ 4 ห้ามเพิ่มแท็บแยกสำหรับ Log, Backtest, Optimization หรือประวัติ Build เพราะข้อมูลเหล่านั้นเก็บใน Workspace/Report/Audit ของ Local Runner อยู่แล้ว

## ขอบเขตที่เชื่อม

| แท็บคงที่ | ผู้ใช้ข้อมูล | สิทธิ์และหน้าที่ |
|---|---|---|
| `World_System` | Radar ระบบเทรดทั่วโลก (`codex_mcp_portal`) | อ่านและเขียน Report ระบบเทรดทั่วโลกที่ตรวจครบ |
| `Deep_Research` | คลังวิจัย (`left_server_racks`) และโรงงาน EA (`right_server_racks`) | คลังวิจัยอ่าน/เขียนผลเจาะลึก; โรงงานอ่านแถวที่ผ่านเกณฑ์จากแท็บเดียวกันและแปลงเป็น 23 ฟิลด์กลยุทธ์ภายใน โดยไม่เขียนกลับจากโรงงาน |
| `Indicator_EA_Tool` | Radar Website Tool (`left_audit_crystals`) | อ่านเพื่อตรวจซ้ำและเขียนชุดงานวิจัย Indicator, EA และ Tool ที่ตรวจครบ |

ลำดับข้อมูลคือ `World_System` → `Deep_Research` → โรงงาน EA และ Indicator ส่วน Radar Website Tool ใช้ `Indicator_EA_Tool` โดยตรง จึงไม่มีแท็บกลางลำดับที่สี่

`right_tool_console` (ห้องทดลอง EA) และ `terminal_workstation` (ห้อง Dev EA) ไม่อยู่ใน Sheet pipeline นี้

## ไฟล์ต้นแบบ schema

สร้างแท็บด้วยชื่อคงที่ตามตาราง แล้วคัดลอกแถวหัวคอลัมน์จากไฟล์ CSV ที่ตรงกับแท็บนั้นโดยไม่เปลี่ยนชื่อหรือลำดับ:

| แท็บ | ไฟล์ต้นแบบ | จำนวนหัวคอลัมน์ | key |
|---|---|---:|---|
| `World_System` | `contracts/research/world-system-sheet-template.csv` | 64 | `discovery_id` |
| `Deep_Research` | `contracts/research/deep-research-sheet-template.csv` | 49 | `research_id` |
| `Indicator_EA_Tool` | `contracts/research/indicator-ea-tool-sheet-template.csv` | 38 | `radar_record_id` |

ไฟล์ทั้งสามเป็น schema-only template ซึ่งมีเพียงแถวหัวคอลัมน์ ระบบทดสอบจะเทียบหัวคอลัมน์กับ `requiredHeaders` ที่ Backend ใช้งานจริงทุกครั้ง เพื่อป้องกันไฟล์ตัวอย่างกับ runtime contract เปลี่ยนไม่พร้อมกัน โรงงาน EA จะอ่านหัวคอลัมน์บังคับ 49 ช่องของ `Deep_Research` (A-AW; อนุญาตคอลัมน์เพิ่มเติมที่ผู้ใช้ดูแลเอง) แล้วแปลงเป็น 23 ฟิลด์กลยุทธ์ภายใน ซึ่งไม่ใช่ช่วงคอลัมน์ของ Google Sheet

ไฟล์ `contracts/research/trading-system-sheet-template.csv` เป็น legacy 42 ช่องสำหรับหน้าจอ Discovery เดิม ไม่ใช่ schema ของแท็บ `World_System` และไม่ควรใช้สร้างแท็บกลางนี้

ขั้น Apply Sheet ใช้ API สองขั้นเท่านั้น: ขั้น Inspect ส่ง `{googleSheetUrlOrId}` และขั้น Activate ส่ง `{verificationToken, confirmActivate: true, expectedConfigRevision, idempotencyKey}` ส่วนการเชื่อม/อ่านสถานะ/ยกเลิก Google OAuth ใช้กลุ่ม `/research-sheet/auth` แยกต่างหาก ชื่อแท็บ สิทธิ์ และ Credential เป็นสัญญาที่ Backend ควบคุม

Sheet ID เป็นรหัสเอกสารและไม่ใช่ Credential หน้าโต๊ะวางแผน Mission จึงต้องแสดง Sheet ที่ **Active** อยู่เต็มค่าและเติมกลับหลังรีโหลดได้ แม้ผู้ใช้กำลังกรอกรหัสใหม่หรือการตรวจรหัสใหม่ล้มเหลว ส่วน OAuth token, refresh token และ client secret ยังคงอยู่ใน Backend เท่านั้นและห้ามส่งกลับ Frontend

Lifecycle ที่บังคับมีลำดับเดียวคือ `draft` → `inspecting` → `awaiting_confirmation` → `activating` → `active`:

1. ผู้ใช้กรอก URL/Sheet ID เป็น Candidate Draft โดยยังไม่เปลี่ยน Sheet ที่ Active
2. Frontend เรียก `POST /api/props/mission_strategy_table/research-sheet/inspect` ด้วย `{googleSheetUrlOrId}` แล้ว Backend ตรวจ Credential, ชื่อแท็บ, หัวคอลัมน์ และ key-column read probe ครบทั้ง 3 แท็บ โดย Active Sheet เดิมยังไม่เปลี่ยน
3. เมื่อผ่านครบจึงได้รับ `verificationPreview` และ `verificationToken` อายุสั้นแบบใช้ครั้งเดียว แล้วแสดงหน้าต่างให้ผู้ใช้ยืนยันใน UX; ถ้าไม่ผ่าน Token ต้องเป็น `null`
4. หลังผู้ใช้ยืนยัน Frontend เรียก `POST /api/props/mission_strategy_table/research-sheet/activate` ด้วย `{verificationToken, confirmActivate: true, expectedConfigRevision, idempotencyKey}` Backend จะตรวจอ่านสดอีกครั้งแล้วจึง Activate แบบ atomic
5. ผลสำเร็จต้องคืน `activation.active=true`, `configRevision` ปัจจุบัน และ `researchSheet` ที่ Consumer หลักทั้ง 3 มีหลักฐานอ่านของ revision เดียวกัน

Token ที่หมดอายุ เก่า ถูกใช้แล้ว หรือผูกกับ revision/schema คนละชุดต้องถูกปฏิเสธด้วย HTTP 409; request ที่ขาด `confirmActivate=true`, revision หรือ idempotency key ต้องถูกปฏิเสธด้วย HTTP 422 Draft ที่ตรวจไม่ผ่านหรือ Activate ไม่สำเร็จต้องไม่แทนที่ Active revision เดิม และห้ามล้าง Sheet ID เดิมออกจากหน้าจอ

คำว่า `Apply 3/3` หมายถึง Backend นำ Active revision ไปผูกกับ Consumer หลักทั้งสามแล้ว ไม่ได้แปลว่าเชื่อม Google สำเร็จ หน้าจอจะแสดงผลสำเร็จสีเขียวได้ต่อเมื่อ `active=true`, `readReady=true`, revision ปัจจุบันตรงกัน, ทั้งสาม Consumer ได้รับการ Apply และแต่ละ Consumer มีหลักฐาน `tabName`, `configRevision`, `status`, `readReady`, `rowCount`, `cachedRowCount` และ `observedAt` ตามจริงเท่านั้น Sheet ที่ใช้งานต้องแสดงจาก field จริงชุดเดียวคือ `sheetId`, `canonicalUrl`, `configRevision`, `activeConfigRevision` และ `activationConfirmedAt` สถานะของโรงงาน EA ต้องสืบทอดหลักฐานเดียวกับ Consumer `Deep_Research`; ห้ามนับโรงงานเป็น Consumer หรือแท็บที่ 4

## สิทธิ์สำหรับ Sheet แบบ Private

ห้ามวาง Token หรือ Secret ในหน้าเว็บ ใน Mission ใน Dashboard settings ใน Audit หรือในไฟล์ที่ commit เข้า Git ผู้ใช้ตั้งสิทธิ์แบบปกติด้วยปุ่ม **เชื่อม Google** เพียงครั้งเดียว:

ก่อนเชื่อมครั้งแรกต้องนำเข้า Google OAuth Client ประเภท Desktop app ที่ Local Runner หนึ่งครั้ง วิธีหลักสำหรับผู้เรียนคือ First-run wizard ของตัวติดตั้ง หรือ `2-SETUP-GOOGLE-HQ.bat` ซึ่งรองรับทั้งดับเบิลคลิกเพื่อเลือกไฟล์และลาก OAuth JSON มาวางบน BAT ระบบส่งเฉพาะ Path ของไฟล์ให้ `configure_google_oauth_client.py`; Backend เป็นผู้ตรวจรูปแบบและบันทึก Client configuration ด้วย Windows current-user DPAPI ในพื้นที่ข้อมูลผู้ใช้นอก Project โดยไม่ส่ง JSON, Client ID เต็ม หรือ Client Secret ผ่าน Browser/Frontend/Report/Audit และไม่คัดลอก OAuth JSON ต้นฉบับ ไฟล์ JSON ต้นฉบับใน Downloads หรือโฟลเดอร์ที่ผู้ใช้เลือกจะไม่ถูกลบอัตโนมัติ ผู้ใช้ต้องเก็บเป็นความลับและลบเองเมื่อไม่ต้องใช้แล้ว

หลัง Backend CLI ยืนยันการนำเข้าแล้วไม่ต้อง Restart Bridge เพราะกลุ่ม `/research-sheet/auth` จะ resolve Client configuration จาก secure store สด เปิด Agent HQ แล้วกด **เชื่อมบัญชี Google ครั้งเดียว** ได้ทันที จากนั้นขั้นตอนประจำวันเหลือเพียงกรอก Sheet ID และตรวจ/ยืนยัน Sheet

การตั้งค่าระดับแอปทำเพียงครั้งเดียว: เปิด Google Sheets API ใน Google Cloud Project ของ Metafxclub, ตั้ง OAuth consent screen (และเพิ่มบัญชีเป็น Test user หากแอปยังอยู่โหมด Testing), จากนั้นสร้าง OAuth Client ID ประเภท **Desktop app** เพื่อรองรับ callback แบบ loopback `http://127.0.0.1:<port>` ของ Local Runner ห้ามนำ Client ID ของปลั๊กอินหรือแอปบุคคลอื่นมาใช้แทน

สถานะ `Testing` เหมาะสำหรับทดลองเท่านั้น: Google ระบุว่าสิทธิ์ของ Test user และ Refresh token สำหรับ offline access อาจหมดอายุหลัง 7 วัน จึงต้องเชื่อมใหม่ หากต้องการให้ผู้เรียนเชื่อมครั้งเดียวและใช้ต่อเนื่อง ให้ผู้ดูแลจัด Publishing status/Verification ตามนโยบาย Google ก่อนแจกระบบ ดู [Google Auth Platform — Audience](https://support.google.com/cloud/answer/15549945)

Environment variable เป็น fallback สำหรับผู้ดูแลหรือการย้ายระบบเดิมเท่านั้น ไม่ใช่ UX หลักของนักเรียน ตัวอย่างบันทึก Client ID แบบ manual แล้วค่อย Restart Bridge:

```powershell
[Environment]::SetEnvironmentVariable(
  "METAFX_GOOGLE_OAUTH_CLIENT_ID",
  "YOUR_DESKTOP_CLIENT_ID.apps.googleusercontent.com",
  "User"
)
```

1. Frontend เรียก `POST /api/props/mission_strategy_table/research-sheet/auth/start` ด้วย JSON ว่าง `{}` แล้วได้รับเฉพาะ `authorizationUrl` แบบ HTTPS
2. ระบบเปิด Google ใน System Browser ผู้ใช้เลือกบัญชีและยืนยันสิทธิ์ โดยคำขอใช้ `state` และ PKCE `S256`, ขอ `access_type=offline` และ `prompt=consent`
3. Google ส่งผลกลับเข้า `GET /api/props/mission_strategy_table/research-sheet/auth/callback` บน `127.0.0.1` และ port ของ Local Runner ปัจจุบันเท่านั้น Backend ตรวจ `state`, อายุคำขอ และ PKCE verifier ก่อนแลก Token; `state` และ verifier ใช้ได้ครั้งเดียว แม้ callback หรือตอนแลก Token จะล้มเหลว
4. Backend เก็บ refresh token ด้วย Windows current-user DPAPI ในโฟลเดอร์ข้อมูลผู้ใช้ภายนอก Project ไม่เก็บใน Dashboard settings/Report/Audit และไม่ส่ง access token, refresh token, authorization code, PKCE verifier หรือ client secret กลับ Frontend ค่า `state` อยู่ได้เฉพาะภายใน `authorizationUrl` ที่ต้องส่งให้ System Browser และไม่ถูกส่งเป็น field แยก
5. เมื่อเชื่อมครั้งแรกสำเร็จ การเปิด Local Runner ครั้งถัดไปจะอ่านสิทธิ์เดิมจาก secure store ผู้ใช้จึงกรอกเพียง Sheet ID แล้ว Inspect/ยืนยัน/Activate ได้

หน้าเว็บตรวจสถานะที่ `GET /api/props/mission_strategy_table/research-sheet/auth` ซึ่งตอบเฉพาะสถานะปลอดภัย เช่น เชื่อมแล้วหรือไม่และวิธีที่ใช้อยู่ ห้ามใช้ endpoint นี้คืน Token หรือ callback query ส่วน `POST /api/props/mission_strategy_table/research-sheet/auth/disconnect` ด้วย `{}` จะลบ durable OAuth grant และคำขอเชื่อมที่ยังค้างทั้งหมด หลัง Disconnect ต้องไม่สามารถใช้ credential เดิมจาก secure store ได้

OAuth callback เป็นข้อมูลอ่อนไหว: Local Runner ห้ามบันทึก raw request target หรือ query string ที่มี `code`, `state` หรือ error detail ลง console, Audit หรือไฟล์ตั้งค่า การตอบหน้า callback ควรเป็นข้อความสำเร็จ/ไม่สำเร็จแบบทั่วไปแล้วให้ผู้ใช้กลับหน้า HQ

### วินิจฉัย Token Exchange แบบไม่เปิดเผยข้อมูล Google

เมื่อ Google ตอบ HTTP error Backend อ่าน response body ไม่เกิน 16 KiB และใช้เฉพาะรหัสที่อยู่ใน allowlist การตรวจ `error_description` อนุญาตเพียงเพื่อตรวจ signature ที่ยืนยันว่า OAuth Client นี้ต้องใช้ `client_secret`; ข้อความต้นฉบับทั้งหมดจะถูกทิ้งทันที ห้ามนำ `error_description`, provider reason/header, code, state, access token, refresh token หรือค่า provider ที่ไม่รู้จักไปใส่หน้า callback, API response, console, Audit หรือ Dashboard settings

Audit เก็บได้เฉพาะ internal kind ที่กำหนดไว้ล่วงหน้าและคำแนะนำภาษาไทยทั่วไป:

- `oauth_invalid_client` — Client ID/Client Secret ไม่ใช่คู่ที่ Google ยอมรับ ให้ตรวจค่า Backend แล้วรีสตาร์ต Local Runner
- `oauth_client_secret_required` — OAuth Client นี้กำหนดให้ส่ง Client Secret ให้ตั้ง `METAFX_GOOGLE_OAUTH_CLIENT_SECRET` ที่ Backend แล้วเริ่มเชื่อมใหม่
- `oauth_code_invalid_or_expired` — code หมดอายุ, ถูกใช้แล้ว หรือ PKCE ไม่ผ่าน ให้เริ่มเชื่อมใหม่เพื่อออก code ใหม่
- `oauth_redirect_mismatch` — callback ไม่ตรง ให้ใช้ Desktop OAuth Client และ loopback ของ Local Runner
- `oauth_scope_missing` — Consent Screen/Client ยังไม่อนุญาต Google Sheets scope
- `oauth_invalid_request` — รูปแบบคำขอถูก Google ปฏิเสธ ให้ตรวจการตั้งค่า Desktop OAuth Client
- `oauth_authorization_denied` — ผู้ใช้หรือ Google ไม่อนุญาตสิทธิ์
- `oauth_rate_limited` — ถูกจำกัดคำขอชั่วคราว ให้รอแล้วลองใหม่
- `oauth_unavailable` — Google OAuth ไม่พร้อมชั่วคราว
- `oauth_exchange_rejected` — fallback สำหรับ provider error ที่ไม่รู้จัก, body ผิดรูปแบบ หรือ body เกินขนาด; ห้ามนำค่าจาก provider มาสร้าง kind ใหม่

Environment credential เดิมยังเป็น fallback สำหรับผู้ดูแลระบบและการย้ายรุ่น โดยไม่ต้องกรอกผ่าน Frontend:

- Access token ชั่วคราว: `METAFX_GOOGLE_SHEETS_ACCESS_TOKEN`
- OAuth refresh token: ต้องมี `METAFX_GOOGLE_OAUTH_CLIENT_ID` และ `METAFX_GOOGLE_OAUTH_REFRESH_TOKEN`; `METAFX_GOOGLE_OAUTH_CLIENT_SECRET` เป็นตัวเลือกสำหรับ Client ที่กำหนดให้ใช้

ถ้ามีทั้ง durable OAuth grant และ Environment fallback ให้สถานะปลอดภัยของ Backend ระบุวิธีที่กำลังใช้อยู่ตามจริง แต่ห้ามเปิดเผยค่า Credential การ Disconnect ลบเฉพาะ grant ใน secure store ไม่แก้ Environment ของเครื่อง ดังนั้น Environment fallback ที่ตั้งแยกไว้ยังใช้งานได้

Adapter รุ่นปัจจุบันยังไม่รองรับ Service Account JSON/JWT หรือ `GOOGLE_APPLICATION_CREDENTIALS`; การเก็บ Service Account key ไว้ฝั่ง Backend อย่างเดียวไม่ได้ทำให้เชื่อมได้จนกว่าจะมี Adapter รองรับโดยตรง

บัญชี Google ที่ OAuth อ้างถึงต้องเข้าถึง Spreadsheet ได้ และต้องมีสิทธิ์ Editor สำหรับทั้งสามแท็บ โรงงาน EA ใช้สิทธิ์อ่าน `Deep_Research` ผ่าน Adapter เดียวกับคลังวิจัยและไม่เขียน Sheet เอง

Backend ตรวจหัวคอลัมน์ทุกช่องที่แต่ละ Report จะเขียนจริง ไม่ได้ตรวจเพียงคอลัมน์รหัสหลัก และตรวจ `Deep_Research` ครบ 49 หัวคอลัมน์ก่อนให้โรงงานอ่าน หากแท็บใดผิด schema จะแจ้งเฉพาะแท็บนั้น โดยแท็บอื่นที่ตรวจผ่านยังอ่านได้ แต่สถานะรวมจะยังไม่เป็นพร้อมทั้งหมด

หลัง OAuth สำเร็จ (หรือหลังตั้ง Environment fallback แล้วรีสตาร์ต Local Bridge) ให้เปิดโต๊ะวางแผน Mission แล้วกด Apply/ตรวจอีกครั้ง ระบบจะแสดงสถานะตามจริง:

- `oauth_client_not_configured` — Local Runner ยังไม่มี OAuth Client ID จึงยังเปิด System Browser เพื่อเชื่อมไม่ได้
- `authorization_required` — Client พร้อมแล้วแต่ยังไม่มี durable grant ให้กดเชื่อม Google หนึ่งครั้ง
- `connected` — มี durable OAuth grant หรือ Environment fallback ที่ Backend ใช้งานได้; ยังไม่ถือว่า Sheet ผ่านจนกว่าจะ Inspect/Activate ครบสามแท็บ
- `secure_store_unavailable`, `secure_store_read_failed`, `secure_store_invalid` — ที่เก็บ DPAPI ใช้ไม่ได้/อ่านไม่ได้/ข้อมูลเสีย ให้ Disconnect หรือล้าง grant ที่เสียแล้วเชื่อมใหม่ โดยห้าม fallback เป็นสถานะสำเร็จปลอม
- `auth_required` — ยังไม่มี Backend credential
- `permission_denied` — Backend มี Credential แต่บัญชีไม่มีสิทธิ์อ่าน Sheet/แท็บที่กำหนดหรือ OAuth scope ไม่พอ Candidate ต้องไม่ถูก Activate
- `schema_mismatch` — ขาดแท็บหรือหัวคอลัมน์บังคับ
- `read_ready_write_unverified` — อ่านครบแล้ว แต่ยังไม่มีการเขียนและอ่านกลับที่ยืนยันได้
- `ready` — อ่านได้และมี write/read-back receipt ใน config revision ปัจจุบัน

## การรับประกันข้อมูล

- Report ที่ยังไม่ `ready` หรือหลักฐานไม่ครบจะไม่เข้าคิว Sheet
- Radar ระบบโลกเขียน 3 ระบบต่อรอบ; Radar Website Tool เขียนเมื่อครบชุดที่ Backend ตรวจยืนยัน
- ใช้ key ของแต่ละแท็บทำ upsert จึงไม่เพิ่มแถวซ้ำจากการ retry เดิม
- การแก้แถวเดิมเขียนเฉพาะคอลัมน์ที่ Adapter เป็นเจ้าของ จึงไม่เขียนทับสูตรหรือคอลัมน์หมายเหตุที่ผู้ใช้ดูแลเอง
- หากผลการเขียนไม่ชัดเจน รายการจะอยู่ที่ `write_unknown` แล้ว retry ผ่าน key เดิมแบบ idempotent โดยอ่าน key ก่อนทุกครั้ง จึงไม่ append ซ้ำแบบเดาสุ่ม
- ทุกการเขียนต้องอ่านแถวกลับมาเทียบตรงกันก่อนถือว่าสำเร็จ
- สถานะเขียนยืนยันแยกต่อแท็บ การเขียนสำเร็จใน `World_System` จะไม่ทำให้ `Deep_Research` หรือ `Indicator_EA_Tool` ถูกแสดงว่าพร้อมเขียนโดยอัตโนมัติ
- ชุด Radar 6 รายการเข้าคิวแบบ atomic: หากพื้นที่คิวไม่พอ ระบบจะปฏิเสธทั้ง 6 รายการและรายงานจำนวนที่ถูกปฏิเสธ ห้ามเกิดสถานะหลอก 1/6
- รายการที่ retry ครบเพดานจะเปลี่ยนเป็น `failed` และคงอยู่ให้เห็นจนกว่า Verify/backfill หลังแก้สิทธิ์หรือ schema จะนำรายการเดิมกลับมาทำใหม่
- คิวส่งผูกกับ `configRevision` เมื่อเปลี่ยน Sheet งานคิวของ revision เก่าจะถูกตัดออก และระบบ backfill Report ที่เข้าเกณฑ์ไปยังไฟล์ใหม่
- คลังวิจัยรับเฉพาะแถว `World_System` ที่ยืนยันแล้วและมี URL สาธารณะอย่างน้อยสองแหล่ง
- โรงงาน EA รับเฉพาะแถว `Deep_Research` ที่ Backend ยืนยันและแปลงเป็น Strategy Spec ภายในได้ครบ โดยไม่สร้างหรือพึ่งแท็บ Google Sheet เพิ่ม
- Cache ผูกกับ Sheet digest, `configRevision`, สิทธิ์ Backend ปัจจุบัน และอายุไม่เกิน 26 ชั่วโมง; เปลี่ยน Sheet/สิทธิ์หมด/Cache เกินอายุแล้วข้อมูลเดิมจะไม่ถูกนำมาอ้างเป็นข้อมูลสด
- Backend สแกน key ถึงแถว 10,000 และเก็บหน้าต่าง 250 แถวล่าสุดของแต่ละแท็บ จึงไม่ติดอยู่กับ 250 แถวแรกเมื่อ Sheet โตขึ้น
