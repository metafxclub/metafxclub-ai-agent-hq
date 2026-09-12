# Google Sheet กลางสำหรับระบบ Research

ระบบใช้ Google Sheet กลางเพียงรายการเดียว โดยตั้ง URL หรือ Sheet ID ที่ **โต๊ะวางแผน Mission** แล้ว Backend จะผูก **3 แท็บคงที่เท่านั้น** ให้กับ 4 ระบบที่เชื่อม: Radar ระบบโลก, คลังวิจัยเชิงลึก, โรงงาน EA และ Radar Website Tool โดยโรงงาน EA อ่านร่วมจาก `Deep_Research` แบบ Read-only จึงไม่ใช่ Consumer หลักหรือแท็บที่ 4 ห้ามเพิ่มแท็บแยกสำหรับ Log, Backtest, Optimization หรือประวัติ Build เพราะข้อมูลเหล่านั้นเก็บใน Workspace/Report/Audit ของ Local Runner อยู่แล้ว

## ขอบเขตที่เชื่อม

| แท็บคงที่ | ผู้ใช้ข้อมูล | สิทธิ์และหน้าที่ |
|---|---|---|
| `World_System` | Radar ระบบเทรดทั่วโลก (`codex_mcp_portal`) | อ่านและเขียน Report ระบบเทรดทั่วโลกที่ตรวจครบ |
| `Deep_Research` | คลังวิจัย (`left_server_racks`) และโรงงาน EA (`right_server_racks`) | คลังวิจัยอ่าน/เขียน Strategy Brief 10 ช่อง A-J; โรงงานอ่าน Brief ชุดเดียวกันโดยไม่เขียนกลับจากโรงงาน |
| `Indicator_EA_Tool` | Radar Website Tool (`left_audit_crystals`) | อ่านเพื่อตรวจซ้ำและเขียนชุดงานวิจัย Indicator, EA และ Tool ที่ตรวจครบ |

ลำดับข้อมูลคือ `World_System` → `Deep_Research` → โรงงาน EA และ Indicator ส่วน Radar Website Tool ใช้ `Indicator_EA_Tool` โดยตรง จึงไม่มีแท็บกลางลำดับที่สี่

`right_tool_console` (ห้องทดลอง EA) และ `terminal_workstation` (ห้อง Dev EA) ไม่อยู่ใน Sheet pipeline นี้

## ไฟล์ต้นแบบ schema

สร้างแท็บด้วยชื่อคงที่ตามตาราง แล้วคัดลอกแถวหัวคอลัมน์จากไฟล์ CSV ที่ตรงกับแท็บนั้นโดยไม่เปลี่ยนชื่อหรือลำดับ:

| แท็บ | ไฟล์ต้นแบบ | จำนวนหัวคอลัมน์ | key |
|---|---|---:|---|
| `World_System` | `contracts/research/world-system-sheet-template.csv` | 64 | `discovery_id` |
| `Deep_Research` | `contracts/research/deep-research-sheet-template.csv` | 10 | `record_id` |
| `Indicator_EA_Tool` | `contracts/research/indicator-ea-tool-sheet-template.csv` | 38 | `radar_record_id` |

ไฟล์ทั้งสามเป็น schema-only template ซึ่งมีเพียงแถวหัวคอลัมน์ ระบบทดสอบจะเทียบหัวคอลัมน์กับ `requiredHeaders` ที่ Backend ใช้งานจริงทุกครั้ง เพื่อป้องกันไฟล์ตัวอย่างกับ runtime contract เปลี่ยนไม่พร้อมกัน สำหรับ `Deep_Research` สัญญาที่มีผลคือ Strategy Brief 10 ช่อง A-J ตามลำดับนี้เท่านั้น:

| คอลัมน์ | Header | เนื้อหา |
|---|---|---|
| A | `record_id` | รหัสถาวรของรายการ |
| B | `system_name` | ชื่อระบบเทรด |
| C | `system_overview` | ภาพรวมระบบ รวมตลาด สัญลักษณ์ กรอบเวลา และลักษณะกลยุทธ์ โดยไม่ล็อกค่าที่แหล่งข้อมูลไม่ระบุ |
| D | `entry_rules` | กฎเข้าเทรดแบบประโยคที่ AI นำไปตีความเป็นตรรกะได้ |
| E | `recovery_rules` | วิธีแก้ไม้ เช่น ไม่มีการแก้ไม้, averaging, grid, martingale หรือ hedge พร้อมเงื่อนไข |
| F | `exit_rules` | วิธีปิดไม้ รวม TP, SL, trailing stop, break-even, partial close และ exit signal |
| G | `money_management` | Lot, risk, position sizing, เพดานขาดทุน และข้อจำกัดพอร์ต |
| H | `order_execution` | ประเภทคำสั่ง market/pending เช่น Buy/Sell, Stop หรือ Limit และกติกาส่งคำสั่ง |
| I | `display_requirements` | ข้อมูลที่ต้องแสดงบนกราฟ/หน้าจอ; ถ้าไม่มีให้ระบุว่าใช้ค่าเริ่มต้น |
| J | `additional_notes` | หมายเหตุ ข้อจำกัด สมมติฐาน หรือสิ่งที่ยังไม่ทราบ; ถ้าไม่มีให้ระบุว่าไม่มีหมายเหตุเพิ่มเติม |

หัวคอลัมน์ต้องตรงและเรียงตามนี้ทั้ง 10 ช่อง ไม่เพิ่มคอลัมน์ในสัญญาหลัก ชุด `Deep_Research` เดิม A-AW/49 หัวคอลัมน์เก็บไว้ได้เฉพาะสำรองหรืออ่านเพื่อความเข้ากันได้ ห้ามใช้เป็น schema เขียนหลักหรือ Gate ยืนยันใหม่ และโรงงาน EA ต้องรับ Strategy Brief A-J โดยไม่บังคับ Blueprint 49 ช่อง

### ค่าเริ่มต้นเมื่อแหล่งข้อมูลไม่ระบุกฎสำหรับเขียน EA

งานวิจัยใหม่ใช้ policy `compact-ea-safe-inputs-v2` แบบตรวจทีละองค์ประกอบ กฎที่แหล่งข้อมูลระบุแล้วต้องคงค่าและหน่วยเดิมเสมอ ส่วนที่ขาดเท่านั้นจึงเติมค่าเริ่มต้นที่นำไปเขียน EA ได้ตรง ๆ: `StopLossPoints=300`, `TakeProfitPoints=600`, `ExecutionBufferPoints=2`, `PositionSizingMode=fixed_lot`, `FixedLot=0.01`, โหมดเสริม `percent_equity` พร้อม `RiskPercent=1.0`, จำกัดหนึ่งสถานะเปิดหรือ Pending ต่อ Symbol+Magic และใช้ Market order ตามทิศทางต้นทาง หากไม่พบจังหวะประมวลผลจะใช้ `SignalBarShift=1` กับ `TradeOnNewBar=true` เพื่ออ่านแท่งปิดและส่งคำสั่งครั้งเดียวบน tick แรกของแท่งใหม่ ส่วน Trailing Stop, Break-even และ Partial Close จะตั้งเป็น `false` แยกทีละองค์ประกอบเมื่อแหล่งไม่ได้ระบุ และจะไม่ปิดทับองค์ประกอบที่ต้นทางกำหนดไว้แล้ว

ทุก Report ใหม่ที่มีค่าซึ่งระบบต้องเติมจะมี `INPUT_METADATA_VERSION=ea-optimization-inputs-v1` ใน `additional_notes` ก่อนบันทึก Google Sheet โดยระบุชนิดค่า ค่าเริ่มต้น และช่วง `Start/Step/Stop` สำหรับค่าที่ระบบสมมุติ เช่น Fixed Lot, SL/TP แบบ broker points, Risk Percent และจำนวนสถานะ ช่วงเหล่านี้เป็นเพียงช่วงเริ่มต้นสำหรับ Backtest/Optimize ไม่ใช่ผลลัพธ์ที่รับรองแล้ว ส่วนค่าจากแหล่งข้อมูลจะคงเป็น authoritative input และไม่ถูก metadata ค่าเริ่มต้นเขียนทับ

ถ้าไม่พบระบบแก้ไม้ หรือพบเพียงชื่อ Grid/Martingale/Averaging/Hedging แต่ไม่มี Trigger, ระยะ, สูตร Lot, จำนวนชั้น, Basket exit และ Reset/Abort ครบ ระบบจะตั้ง `RecoveryMode=none` และไม่สร้างการแก้ไม้ให้เอง ทุกค่าที่ระบบเติมต้องมีป้าย `IMPLEMENTATION_DEFAULT_NOT_SOURCE_FACT`, ระบุ policy และ component ในช่องที่เกี่ยวข้อง พร้อมสรุปใน `additional_notes` ว่าเป็นสมมุติฐานที่ผู้ใช้ปรับเป็น EA Inputs ได้ ไม่ใช่ข้อเท็จจริงจากแหล่งข้อมูล และยังต้อง Compile, Backtest, Optimize และทดสอบ Demo ก่อนใช้งานจริง

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

ห้ามวาง access token, refresh token, authorization code, รหัสผ่าน หรือ Secret ที่เป็นข้อมูลผู้ใช้/Confidential server secret ในหน้าเว็บ ใน Mission ใน Dashboard settings ใน Audit หรือในไฟล์ที่ commit เข้า Git Native-app client configuration กลางต้องถูก GitHub Actions inject จาก Release secrets ตอน build Asset เท่านั้นและห้าม commit ค่าจริงลง public Git tree ผู้ใช้ตั้งสิทธิ์แบบปกติด้วยปุ่ม **เชื่อม Google** เพียงครั้งเดียว:

เส้นทางหลักสำหรับนักเรียนใช้ Google OAuth native/installed-app client configuration กลางของ Metafxclub ที่ Release workflow inject เป็น `backend/local-runner/google_oauth_native_client.txt` ภายใน Asset แล้วตรวจโดยอัตโนมัติ Public Git Source ไม่มีไฟล์จริงนี้ ไฟล์ใน Release มี `client_id` และ `client_secret` ของ native app ซึ่งเป็น app metadata ที่ต้องแจกพร้อม installed app ไม่ใช่ Credential ของ Gmail นักเรียน ระบบไม่แสดงค่า Client กลางเต็มผ่าน Browser/Frontend/Report/Audit นักเรียนไม่ต้องสร้าง Google Cloud Project/OAuth Client, เพิ่ม Gmail เป็น Test user, ดาวน์โหลดหรือส่ง OAuth JSON และไม่ต้องกรอกหรือแก้ Client ID กลาง

หลังติดตั้ง Release ที่ผ่านการตรวจแล้ว เปิด Agent HQ และกด **เชื่อมบัญชี Google ครั้งเดียว** ได้ทันที ผู้ใช้ต้องเลือกบัญชีและยืนยัน Consent ด้วยตนเองใน System Browser จากนั้นขั้นตอนประจำวันเหลือเพียงกรอก Sheet ID และตรวจ/ยืนยัน Sheet

การตั้งค่าระดับแอป เช่น Google Cloud Project, Google Sheets API, OAuth consent screen, Desktop Client และการส่ง Verification เป็นหน้าที่ของผู้ดูแล Metafxclub เพียงครั้งเดียว ไม่ใช่งานที่ทำซ้ำในเครื่องนักเรียน Client กลางรองรับ callback แบบ loopback `http://127.0.0.1:<port>` ของ Local Runner และต้องใช้ `state` กับ PKCE `S256` นักเรียนไม่ต้อง Restart Bridge เพื่อใส่ Client หลังติดตั้ง Release ปกติ

ระหว่างที่ Sensitive Scope ของแอปกลางยังอยู่ระหว่างตรวจสอบ ผู้ใช้ใหม่อาจเห็นหน้า `Google ยังไม่ได้ยืนยันแอปนี้` และ Project กลางอาจอยู่ภายใต้ OAuth unverified user cap เมื่อ Google อนุมัติ Scope ที่ระบบขอแล้ว คำเตือนและเพดานนี้จะไม่ใช้กับ Scope ที่ได้รับอนุมัติ ดู [Google Auth Platform — Audience](https://support.google.com/cloud/answer/15549945)

`2-SETUP-GOOGLE-HQ.bat` และการนำเข้า Desktop OAuth JSON ยังคงมีไว้เฉพาะ **Advanced/Recovery custom override** สำหรับเจ้าของระบบที่ตั้งใจใช้ OAuth Project ของตนเองหรือกู้การตั้งค่าเดิม ไม่ใช่ UX หลักของนักเรียน โหมดนี้ให้ Backend ตรวจและเก็บ Client configuration ด้วย Windows current-user DPAPI โดยไม่ส่ง JSON/Client Secret ผ่าน Frontend และไม่คัดลอกหรือลบไฟล์ต้นฉบับ ผู้ใช้ Advanced ต้องใช้ JSON ของ Project ที่ตนควบคุมเอง ห้ามใช้ไฟล์ของผู้สอนหรือเพื่อน และต้องรับผิดชอบ Publishing status/Test users/Verification ของ Project นั้นเอง

Environment variable เป็น fallback สำหรับผู้ดูแลหรือการย้ายระบบเดิมเท่านั้น ไม่ใช่ UX หลักของนักเรียน ตัวอย่างบันทึก Client metadata แบบ manual แล้วค่อย Restart Bridge โดยใช้เฉพาะค่าจาก OAuth Project ที่ผู้ดูแลควบคุมเอง:

```powershell
[Environment]::SetEnvironmentVariable(
  "METAFX_GOOGLE_OAUTH_CLIENT_ID",
  "YOUR_DESKTOP_CLIENT_ID.apps.googleusercontent.com",
  "User"
)
[Environment]::SetEnvironmentVariable(
  "METAFX_GOOGLE_OAUTH_CLIENT_SECRET",
  "YOUR_DESKTOP_CLIENT_SECRET",
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

เมื่อ Google ตอบ HTTP error Backend อ่าน response body ไม่เกิน 16 KiB และใช้เฉพาะรหัสที่อยู่ใน allowlist การตรวจ `error_description` อนุญาตเพียงเพื่อจำแนกสาเหตุภายใน เช่น Client metadata ไม่ครบ, code หมดอายุ หรือ redirect ไม่ตรง ทั้ง Client กลางและ Advanced/Recovery custom override อาจต้องส่ง `client_secret` ตาม metadata ของ installed app ข้อความต้นฉบับทั้งหมดจะถูกทิ้งทันที ห้ามนำ `error_description`, provider reason/header, code, state, access token, refresh token หรือค่า provider ที่ไม่รู้จักไปใส่หน้า callback, API response, console, Audit หรือ Dashboard settings

Audit เก็บได้เฉพาะ internal kind ที่กำหนดไว้ล่วงหน้าและคำแนะนำภาษาไทยทั่วไป:

- `oauth_invalid_client` — Client กลางใน Release หรือ custom override ไม่ใช่ค่าที่ Google ยอมรับ ให้ผู้ดูแลตรวจแหล่งตั้งค่าโดยไม่แสดง Client ID เต็ม แล้วรีสตาร์ต Local Runner
- `oauth_client_secret_required` — Client metadata ที่กำลังใช้อยู่ไม่มี `client_secret` ที่ Google กำหนด หากเป็น Client กลางให้ผู้ดูแลแก้ Release; หากเป็น Advanced/Recovery custom override ให้ผู้ดูแลตั้ง `METAFX_GOOGLE_OAUTH_CLIENT_SECRET` ที่ Backend แล้วเริ่มเชื่อมใหม่ ห้ามขอค่านี้จากนักเรียน
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

Backend ตรวจหัวคอลัมน์ทุกช่องที่แต่ละ Report จะเขียนจริง ไม่ได้ตรวจเพียงคอลัมน์รหัสหลัก และตรวจ `Deep_Research` ให้ตรง Strategy Brief 10 หัว A-J ก่อนให้โรงงานอ่าน หากแท็บใดผิด schema จะแจ้งเฉพาะแท็บนั้น โดยแท็บอื่นที่ตรวจผ่านยังอ่านได้ แต่สถานะรวมจะยังไม่เป็นพร้อมทั้งหมด

หลัง OAuth สำเร็จ (หรือหลังตั้ง Environment fallback แล้วรีสตาร์ต Local Bridge) ให้เปิดโต๊ะวางแผน Mission แล้วกด Apply/ตรวจอีกครั้ง ระบบจะแสดงสถานะตามจริง:

- `oauth_client_not_configured` — Local Runner ไม่พบ Client กลางจาก Release หรือ custom override ที่ถูกต้อง จึงยังเปิด System Browser เพื่อเชื่อมไม่ได้ สำหรับเครื่องนักเรียนให้หยุดและตรวจ Release ห้ามขอ Client ID/JSON มาแก้ใน flow หลัก
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
- โรงงาน EA รับแถว `Deep_Research` ที่ Backend ยืนยันว่าครบ Strategy Brief 10 ช่อง A-J แล้วสร้าง Strategy Spec ภายในจากข้อความชุดนี้ โดยไม่สร้างหรือพึ่งแท็บ Google Sheet เพิ่ม และไม่ใช้ Blueprint 49 ช่องเดิมเป็น Gate
- Cache ผูกกับ Sheet digest, `configRevision`, สิทธิ์ Backend ปัจจุบัน และอายุไม่เกิน 26 ชั่วโมง; เปลี่ยน Sheet/สิทธิ์หมด/Cache เกินอายุแล้วข้อมูลเดิมจะไม่ถูกนำมาอ้างเป็นข้อมูลสด
- Backend สแกน key ถึงแถว 10,000 และเก็บหน้าต่าง 250 แถวล่าสุดของแต่ละแท็บ จึงไม่ติดอยู่กับ 250 แถวแรกเมื่อ Sheet โตขึ้น
