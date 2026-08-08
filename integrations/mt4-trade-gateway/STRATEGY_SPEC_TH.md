# Strategy Spec — MetafxHQ Unified MT4 Gateway v2.14

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
- Command v2 ต้องผูกกับ `snapshotId`, `snapshotObservedAt`, `barTime` และ `referencePrice`
- ก่อนส่ง Order EA ต้องยืนยันว่า `barTime` ตรงกับแท่งปิดล่าสุด `iTime(..., 1)` และราคายังไม่เคลื่อนเกินเพดาน

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
| `ExecuteCommand` | ตรวจซ้ำที่ขอบ OrderSend, จองสิทธิ์แท่ง และส่งเพียงครั้งเดียวโดยไม่ Retry |
| `CaptureSelectedOrderEvidence` | ตรวจ Ticket, ราคาเปิด, Slippage, SL/TP, Magic และ Comment หลัง OrderSend |
| `RefreshManagedOutcomeFiles` | อัปเดตไฟล์ Outcome เมื่อ Order ยังเปิดหรือปิดแล้ว |
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

Daily/Weekly Loss ใช้สถานะ Latch ตามวัน/สัปดาห์ของ Broker เมื่อชนเพดานแล้ว EA จะไม่เปิดคำสั่งใหม่ในช่วงนั้น แม้ P/L ภายหลังเปลี่ยนกลับ รายการ Managed ทุกตัวต้องประกาศ Magic ชุดเดียวกันใน `ManagedMagicNumbers` เพื่อให้ Guard รวมข้าม Channel ได้ถูกต้อง

## ผลลัพธ์และการกู้สถานะ

- `EXECUTED` ใช้ได้เมื่อ Post-Order Verification ผ่านเท่านั้น
- `EXECUTION_UNKNOWN` จะคง Slot และ Bar Claim เพื่อป้องกันการส่งซ้ำ
- EA พยายาม Reconcile จาก Magic + Comment + Symbol หลัง Restart; หากพบไม่ตรงหนึ่งรายการจะไม่เดาผล
- คำสั่งซ้ำด้วย `idempotencyKey` เดิมจะไม่เขียนทับ Ledger ของคำสั่งต้นฉบับ
- Backend มี Primitive `quarantine_execution_unknown()` ซึ่งเปิด Kill Switch ก่อนปล่อย Slot, เก็บ Bar Claim และไม่เปลี่ยนผลเป็นกำไร/ขาดทุนเอง
- `outcomes/<commandId>.json` เป็นหลักฐานแยกสำหรับ Ticket, Open Price, SL/TP และ Closed P/L

## ลำดับใช้งาน

1. Compile แบบมองเห็นใน MetaEditor ของ MT4 เป้าหมาย
2. เริ่ม `GATEWAY_SHADOW` และ `LiveArmed=false`
3. ทดสอบ Snapshot, Status v4, Signature Verification, SHADOWED ACK v3, stale bar, price drift, spread, margin, risk และ Kill Switch
4. ทดสอบบัญชี Demo ด้วย Lot ต่ำ โดยใช้ Signed Envelope เส้นทางเดียวกับ Live
5. ก่อน Live ให้ปักหมุด Active Key ID ใน `TrustedSigningKeyId`, ตรวจ Key match, เปิด `GATEWAY_LIVE` และ `LiveArmed=true` จากหน้า Inputs ของ EA เท่านั้น
6. Live จะส่ง Order ได้เมื่อคะแนนถึงเกณฑ์ 1/3, 2/3 หรือ 3/3 ที่ผู้ใช้เลือก ไม่มีเสียง BUY/SELL ขัดกัน, News ไม่ VETO, Price Action มี SL/TP, Signed Envelope และ Guard ทุกชั้นผ่านครบ; ค่าเริ่มต้นยังคง Shadow และไม่เปิด Live อัตโนมัติ
7. Status v4 ส่งประเภทบัญชีจาก EA ให้ Backend ตรวจซ้ำ: `GATEWAY_DEMO` ใช้ได้กับบัญชี Demo และ `GATEWAY_LIVE` ใช้ได้กับบัญชีจริงเท่านั้น
8. `roundDeadlineAt` แบบ UTC เป็นขอบเขตสุดท้ายของการ Publish คำสั่งใหม่ เพื่อไม่ให้ Bridge ส่ง Order จากผลวิเคราะห์เก่าหลัง Restart หรือจากเวลาแท่งโบรกเกอร์ที่มี timezone ต่างกัน; Command ที่ส่งไปแล้วจะยังติดตาม ACK ต่อจนจบ

## ความเข้ากันได้ของ Broker และไฟล์สื่อสาร

- ใช้ `FILE_COMMON` เท่านั้น ไม่ใช้ `WebRequest()` และไม่ต้องตั้ง Allow URL
- `AllowedSymbols` รองรับชื่อฐานพร้อม suffix ของ Broker แต่ `command.symbol` ต้องตรงชื่อเต็มบนกราฟ เช่น `XAUUSD.m`
- ราคาและ SL/TP Normalize ตาม `Digits`; ระยะ Stop ใช้ `Point`/`MODE_STOPLEVEL`; Spread ใช้หน่วย points ของ Symbol
- BUY ตรวจ `SL < Bid` และ `TP > Ask`; SELL ตรวจ `SL > Ask` และ `TP < Bid`
- Quote ต้องสดทั้งจาก Local Tick และ `MODE_TIME`; Market ปิด, Trade Disabled, Off Quotes, Requote และ Trade Context Busy จบแบบไม่ Retry พร้อมเหตุผลเฉพาะ
- EA หนึ่งตัวผูกกับ Symbol/Timeframe ของกราฟเดียวและเริ่มที่ M5 ขึ้นไป แต่ละ Symbol เพิ่มเติมต้องใช้ EA/Channel แยก

ไฟล์ Source ชุดนี้ยังไม่ถือว่าผ่าน Compile หรือ Runtime จนกว่าจะ Compile บน MT4 เป้าหมาย และยืนยัน Shadow/Demo ตามขั้นตอนข้างต้น
