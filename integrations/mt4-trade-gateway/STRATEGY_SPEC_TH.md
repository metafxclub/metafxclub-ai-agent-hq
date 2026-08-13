# Strategy Spec — MetafxHQ Unified MT4 Gateway v2.16

## โปรไฟล์และขอบเขต

- โปรไฟล์ EA: `special`
- หน้าที่เดียวกันสองส่วน: ส่ง Snapshot แบบ Read-only และรับคำสั่ง Market Order ผ่าน `FILE_COMMON`
- รองรับ `BUY` / `SELL`, Timeframe ตั้งแต่ `M5` ขึ้นไป และ SL/TP แบบราคาจริง
- ไม่รองรับ Pending Order, Modify, Martingale, Grid หรือ Hedge; การ Close รองรับเฉพาะ Lifecycle ที่ผู้ใช้เปิดใน Inputs และทำเพียงหนึ่ง Attempt ต่อ Trigger โดยไม่ Retry
- AI ส่งได้เฉพาะทิศทาง, Symbol, Timeframe, SL, TP และหลักฐาน Snapshot/แท่งปิด
- EA เป็นเจ้าของ `FixedLot`, Mode, Live Armed, `TrustedSigningKeyId`, Magic Number, Spread, Slippage และเพดานความเสี่ยงทั้งหมด
- Inner Command v2 และ Heartbeat v1 ต้องอยู่ใน Signed Envelope v1 แบบ HMAC-SHA256 ทั้ง Shadow, Demo และ Live; Secret Key ไม่อยู่ใน Frontend, Prompt หรือ Inputs ของ EA

## Trigger และหลักฐาน

- EA ส่ง Snapshot ทุก 5 วินาทีเพื่อให้ Dashboard ตามกราฟทัน
- Backend เรียก Agent เมื่อเวลาแท่งปิดล่าสุดเปลี่ยน ไม่ได้เรียก Codex ทุก 5 วินาที
- Command v2 ต้องผูกกับ `snapshotId`, `snapshotObservedAt`, `barTime` และ `referencePrice`; Backend ต้องคำนวณ `streamKey = SHA256(channelId + "\\n" + UPPERCASE(fullSymbol) + "\\n" + UPPERCASE(timeframe))` ตรงกับ Stream ที่เลือก โดย Normalize ก่อน Hash แม้ Snapshot จะรายงาน Symbol เป็นตัวพิมพ์เล็ก/ผสม
- ก่อนส่ง Order EA ต้องยืนยันว่า `barTime` ตรงกับแท่งปิดล่าสุด `iTime(..., 1)` และราคายังไม่เคลื่อนเกินเพดาน
- Bar Claim ฝั่ง EA เก็บแยกด้วย Channel + ชื่อ Symbol เต็ม + Timeframe ดังนั้น Timestamp เดียวกันในคนละ Stream ทำงานได้ แต่ Stream เดิมใช้ได้เพียงครั้งเดียว

## Function Map

| ส่วน | หน้าที่ |
|---|---|
| `BuildSnapshotJson` | สร้างข้อมูลกราฟ/บัญชีแบบ Read-only |
| `VerifySignedEnvelope` | ตรวจ Schema, Key ID, HMAC-SHA256 และ Payload Hex ก่อนอ่าน Inner JSON |
| `CryptoSelfTest` | ตรวจ SHA-256/HMAC ด้วย Test Vector ตอนเริ่ม EA และ Fail-closed เมื่อผลไม่ตรง |
| `ParseCommand` | อ่าน Flat JSON ด้วย Strict Allowlist และปฏิเสธ Field ควบคุม Lot/Risk |
| `ValidateClosedBarBinding` | ผูกคำสั่งกับ Snapshot, เวลาแท่งปิด และราคาอ้างอิง |
| `ValidateRiskEnvelope` | ตรวจ Position, Lots, จำนวนเทรด, Loss ต่อครั้ง/ต่อวัน, Drawdown และ Reward/Risk |
| `ManagedWeeklyPnl` / `ReadManagedLossStreak` | ตรวจ Weekly Loss และ Consecutive-loss Cooldown ของ Managed Magic ทั้งบัญชี |
| `ValidateMarginPreflight` | ตรวจ Free Margin และ Projected Margin Level |
| `ValidateRuntime` | รวม Guard ที่ต้องผ่านทั้ง Shadow, Demo และ Live |
| `ExecuteCommand` | ถือ Account Execution Lock, ตรวจซ้ำที่ขอบ OrderSend, จองสิทธิ์แท่ง และส่งเพียงครั้งเดียวโดยไม่ Retry |
| `CaptureSelectedOrderEvidence` | ตรวจ Ticket, ราคาเปิด, SL/TP, Magic และ Comment หลัง OrderSend โดยแยก Slippage เป็นคำเตือนคุณภาพ ไม่ใช้เป็นตัวตนของ Order |
| `RefreshManagedOutcomeFiles` | อัปเดต Outcome และใช้ Ticket Map กู้ Command ID เมื่อ Broker เติม `[tp]`/`[sl]` ใน Comment |
| `ApplyOptionalPositionLifecycle` | ปิดตาม Max Holding/Session เฉพาะเมื่อผู้ใช้เปิดโหมด; ค่าเริ่มต้นไม่ทำงาน |
| `BuildStatusJson` | ส่งสถานะ Guard แบบอ่านอย่างเดียวให้ Dashboard |
| `FinalizeCommand` | เขียน ACK, Processed Ledger และ Audit Log |

## ค่าเริ่มต้นด้านความเสี่ยง

| Input | ค่าเริ่มต้น |
|---|---:|
| `FixedLot` | 0.01 |
| `TrustedSigningKeyId` | ค่าว่าง (Live ยังไม่ถูก Arm) |
| `MaxManagedOpenPositions` | 1 |
| `MaxManagedTotalLots` | 0.10 |
| `MaxTradesPerBrokerDay` | 6 |
| `MaxLossPerTradePercent` | 1.0% |
| `MaxDailyLossPercent` | 3.0% |
| `MaxManagedWeeklyLossPercent` | 5.0% |
| `MaxConsecutiveManagedLosses` | 3 ครั้ง |
| `ConsecutiveLossCooldownMinutes` | 240 นาที |
| `MaxAccountEquityDrawdownPercent` | 10.0% |
| `MinRewardRiskRatio` | 1.0 |
| `MinProjectedMarginLevelPercent` | 300% |
| `MaxSnapshotAgeSeconds` | 300 วินาที |
| `MaxSignalDriftPoints` | 100 points |
| `MaxQuoteAgeSeconds` | 30 วินาที |
| `PositionLifecycleMode` | `LIFECYCLE_SLTP_ONLY` |
| `MaxHoldingMinutes` | 0 (ปิด) |
| `EnableRolloverEntryBlock` | false |

Daily/Weekly Loss ใช้สถานะ Latch ตามวัน/สัปดาห์ของ Broker เมื่อชนเพดานแล้ว EA จะไม่เปิดคำสั่งใหม่ในช่วงนั้น แม้ P/L ภายหลังเปลี่ยนกลับ รายการ Managed ทุกตัวต้องประกาศ Magic ชุดเดียวกันใน `ManagedMagicNumbers` เพื่อให้ Guard รวมข้าม Channel ได้ถูกต้อง จำนวน Order ในประวัติ Channel เดียวไม่ใช่ค่า Portfolio Guard และห้ามใช้แทน `currentManagedPositions` แบบ account-wide

เวลา `OrderOpenTime`, `OrderCloseTime`, วัน/สัปดาห์, Consecutive-loss Cooldown และ Max Holding อยู่ใน clock domain ของ Broker เดียวกันทั้งหมด EA จึงเปรียบเทียบเวลาเหล่านี้กับ `TimeCurrent()` เท่านั้น ไม่เปรียบเทียบกับ UTC เพื่อให้ผลเหมือนกันทั้ง Broker UTC+3, UTC-5 และ timezone อื่น ส่วน `observedAt`, `issuedAt`, `expiresAt` และอายุ Snapshot/Command ยังคงเป็น Unix UTC ตาม Wire Contract; `cooldownUntil` ใน Snapshot เป็นเวลา Broker และต้องแสดงพร้อมป้าย Broker โดยไม่แปลงซ้ำเป็น UTC

สำหรับหลาย Channel แนะนำให้ใช้ Magic ไม่ซ้ำต่อ Channel และให้ทุก EA ใส่ Magic ทั้งหมดใน `ManagedMagicNumbers` ชุดเดียวกัน หากแชร์ Magic ต้องให้ทุก Instance ใช้รายการ Managed Magic และเพดาน Risk ชุดเดียวกัน Account Execution Lock ผูกกับ Account Number + Broker Server โดยไม่รวม Channel จึง Serialize Guard + Bar Claim + `OrderSend()` ข้ามทุก Channel/Terminal ที่ใช้ Windows `FILE_COMMON` เดียวกัน และ OS จะคืน Handle เมื่อ Process ล้มโดยไม่เกิด stale-lock deadlock

Account Portfolio Policy Lease ใช้ Digest ของรายการ Magic หลัง Sort รวมกับ `MaxManagedOpenPositions`, `MaxManagedTotalLots`, `MaxTradesPerBrokerDay`, Daily/Weekly Loss, Consecutive Loss/Cooldown และ Account Drawdown หากมี EA ของบัญชีเดียวกันที่ถือ Lease ด้วย Digest อื่น `OnInit` ต้องจบด้วย `PORTFOLIO_POLICY_MISMATCH`; ถ้าไม่มี Active Lease ระบบจึงอนุญาตเขียน Policy ใหม่ ทำให้เปลี่ยนค่าอย่างตั้งใจได้หลังหยุด EA เดิมครบแล้ว

`status.json` schema v5 ต้องรายงาน `portfolioPolicyStatus`, `portfolioPolicyDigest`, `portfolioGuardScope`, `managedMagicNumbers`, `allowedSymbols`, `allowedTimeframes`, `concurrencyBoundary` และ `crossVpsDistributedLock` เพื่อให้ Backend/UI ตรวจขอบเขตจริงจาก EA ได้โดยไม่คาดเดาจากค่าใน Dashboard

Policy enforcement ต้องใช้ v2.16 ขึ้นไปทุก Instance ห้ามทำ Mixed-version concurrency กับ v2.15 หรือต่ำกว่า เพราะรุ่นเก่าไม่ถือ Policy Lease

## ผลลัพธ์และการกู้สถานะ

- `EXECUTED` ใช้ได้เมื่อ Post-Order Verification ด้านตัวตนผ่านเท่านั้น; Slippage เกิน Input จะเป็นคำเตือน `ORDER_ACCEPTED_WITH_SLIPPAGE_WARNING` โดยไม่ซ่อน Ticket ที่เปิดจริง
- `EXECUTION_UNKNOWN` จะคง Slot และ Bar Claim เพื่อป้องกันการส่งซ้ำ
- EA พยายาม Reconcile จาก Magic + Comment + Symbol หลัง Restart; หากพบไม่ตรงหนึ่งรายการจะไม่เดาผล
- คำสั่งซ้ำด้วย `idempotencyKey` เดิมจะไม่เขียนทับ Ledger ของคำสั่งต้นฉบับ
- Backend มี Primitive `quarantine_execution_unknown()` ซึ่งเปิด Kill Switch ก่อนปล่อย Slot, เก็บ Bar Claim และไม่เปลี่ยนผลเป็นกำไร/ขาดทุนเอง
- `tickets/<ticket>.json` ผูก Ticket กับ Command ID แบบถาวรเพื่ออ่านผลปิด TP/SL ได้แม้ Broker เปลี่ยนท้าย Comment
- `outcomes/<commandId>.json` เป็นหลักฐานแยกสำหรับ Ticket, Open Price, SL/TP และ Closed P/L
- ตอนเริ่ม EA จะสแกน Processed ACK แบบจำกัด 256 ไฟล์ เพื่อ Backfill Ticket Map/Outcome ของรุ่นเก่า เฉพาะเมื่อ Ticket, Magic, Symbol, ฝั่ง, Lot, Open Price, SL, TP และ Comment ตรงครบ; หลักฐานกำกวมหรือขัดแย้งจะไม่ถูกเขียน
- Recovery ACK เก็บเวลา, Slippage และ Comment จาก ACK เดิมไว้ ส่วน Lifecycle ใหม่อัปเดตได้เฉพาะสถานะ OPEN/CLOSED, เวลา Close และ P/L
- Outcome ที่ CLOSED และ Payload ไม่เปลี่ยนเป็น Idempotent write จึงไม่เขียนไฟล์เดิมซ้ำทุก Timer

## ลำดับใช้งาน

1. Compile แบบมองเห็นใน MetaEditor ของ MT4 เป้าหมาย
2. เริ่ม `GATEWAY_SHADOW` และ `LiveArmed=false`
3. ทดสอบ Snapshot, Status v5, Signature Verification, SHADOWED ACK v3, stale bar, price drift, spread, margin, risk และ Kill Switch
4. ทดสอบบัญชี Demo ด้วย Lot ต่ำ โดยใช้ Signed Envelope เส้นทางเดียวกับ Live
5. ก่อน Live ให้ปักหมุด Active Key ID ใน `TrustedSigningKeyId`, ตรวจ Key match, เปิด `GATEWAY_LIVE` และ `LiveArmed=true` จากหน้า Inputs ของ EA เท่านั้น
6. Live จะส่ง Order ได้เมื่อคะแนนถึงเกณฑ์ 1/3, 2/3 หรือ 3/3 ที่ผู้ใช้เลือก ไม่มีเสียง BUY/SELL ขัดกัน, News ไม่ VETO, Price Action มี SL/TP, Signed Envelope และ Guard ทุกชั้นผ่านครบ; ค่าเริ่มต้นยังคง Shadow และไม่เปิด Live อัตโนมัติ
7. Status v5 ส่งประเภทบัญชีจาก EA ให้ Backend ตรวจซ้ำ: `GATEWAY_DEMO` ใช้ได้กับบัญชี Demo และ `GATEWAY_LIVE` ใช้ได้กับบัญชีจริงเท่านั้น
8. `roundDeadlineAt` แบบ UTC เป็นขอบเขตสุดท้ายของการ Publish คำสั่งใหม่ เพื่อไม่ให้ Bridge ส่ง Order จากผลวิเคราะห์เก่าหลัง Restart หรือจากเวลาแท่งโบรกเกอร์ที่มี timezone ต่างกัน; Command ที่ส่งไปแล้วจะยังติดตาม ACK ต่อจนจบ

## ความเข้ากันได้ของ Broker และไฟล์สื่อสาร

- ใช้ `FILE_COMMON` เท่านั้น ไม่ใช้ `WebRequest()` และไม่ต้องตั้ง Allow URL
- `AllowedSymbols` รองรับชื่อฐานพร้อม suffix ของ Brokerที่ประกอบด้วยตัวอักษร/ตัวเลข/`.`/`_`/`#`/`-` แต่ `command.symbol` ต้องตรงชื่อเต็มบนกราฟ เช่น `XAUUSD.m` หรือ `EURUSD#`; ไม่ยอมรับ `+`
- ราคาและ SL/TP Normalize ตาม `Digits`; ระยะ Stop ใช้ `Point`/`MODE_STOPLEVEL`; Spread ใช้หน่วย points ของ Symbol
- BUY ตรวจ `SL < Bid` และ `TP > Ask`; SELL ตรวจ `SL > Ask` และ `TP < Bid`
- Quote ต้องสดทั้งจาก Local Tick และ `MODE_TIME`; Market ปิด, Trade Disabled, Off Quotes, Requote และ Trade Context Busy จบแบบไม่ Retry พร้อมเหตุผลเฉพาะ
- EA หนึ่งตัวผูกกับ Symbol/Timeframe ของกราฟเดียวและเริ่มที่ M5 ขึ้นไป แต่ละ Symbol เพิ่มเติมต้องใช้ EA/Channel แยก
- ระหว่างเปลี่ยน Symbol/Timeframe EA จะลบ Runtime status/capabilities/snapshot เก่าก่อนปล่อย Channel; Backend ต้องรอ `INIT_SUCCEEDED` และสถานะใหม่ตรงครบก่อนส่งงาน
- Lock และ Policy Lease ข้าม Terminal ได้เฉพาะใน Windows User/`FILE_COMMON` เดียวกัน บัญชีเดียวกันบนหลาย VPS เป็นขอบเขตที่ไม่รองรับ ต้องมี Active Execution Owner เพียง VPS เดียวจนกว่าจะมี Distributed Lock ภายนอก

ไฟล์ Source ชุดนี้ยังไม่ถือว่าผ่าน Compile หรือ Runtime จนกว่าจะ Compile บน MT4 เป้าหมาย และยืนยัน Shadow/Demo ตามขั้นตอนข้างต้น
