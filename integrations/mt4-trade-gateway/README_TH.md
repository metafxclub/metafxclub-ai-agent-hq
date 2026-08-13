# MetafxHQ Unified MT4 Snapshot + Trade Gateway

> อัปเดต v2.16: การย้าย EA ไป Symbol/Timeframe ใหม่จะล้างสถานะ Runtime เก่าทันที, ผูก Stream/Bar Claim ด้วย Channel + ชื่อ Symbol เต็ม + Timeframe, แยกประวัติ/Outcome ตาม Channel อย่างเคร่งครัด และใช้ OS file-handle lock ระดับบัญชีครอบ Guard + Bar Claim + `OrderSend()` เพื่อไม่ให้หลาย Channel ที่ทำงานพร้อมกันทะลุ Max Order

> อัปเดต v2.15: แยกการยืนยันตัวตน Order ออกจากคำเตือน Slippage, เก็บ Ticket → Command ID ถาวร, กู้ Ticket Map/Outcome รุ่นเก่าแบบ bounded และ fail-closed ตอนเริ่ม EA และติดตามผลปิด TP/SL ได้แม้ Broker เปลี่ยนท้าย Comment เป็น `[tp]`/`[sl]`; ยังคงความเข้ากันได้กับ Symbol suffix และ Guard ของ v2.14 ทั้งหมด

> อัปเดต v2.13: EA จะตัดช่องว่างและแปลง `TrustedSigningKeyId` เป็นตัวพิมพ์เล็กก่อนตรวจสอบ ใน Demo/Shadow ค่า Pin ที่ไม่ถูกต้องหรือไม่ตรงเป็นเพียงคำเตือนและ EA จะใช้ Active Key ของ Backend ต่อ ส่วน Live ยังคงบล็อกแบบ fail-closed เมื่อไม่มี Pin, Pin ผิดรูปแบบ หรือ Pin ไม่ตรง พร้อมเขียน `init-status.json` และ Audit Event เมื่อเริ่มระบบสำเร็จ ติดขัด หรือหยุดเพราะการตั้งค่า

> อัปเดต v2.12: Inner command ยังเป็น `command-v2` แต่ `command.json` และ `heartbeat.json` ถูกห่อด้วย Signed Envelope v1 แบบ HMAC-SHA256, ACK เป็น `ack-v3` และ Status เป็น `status-v4` ซึ่งรายงานประเภทบัญชี Demo/Live ให้ Backend ตรวจเทียบกับโหมด Gateway ก่อนอนุญาตส่งคำสั่ง ทุกคำสั่งยังผูกกับ Snapshot/แท่งปิด/ราคาอ้างอิง พร้อม Risk Envelope, Margin Preflight, Quote Freshness, Channel Lock, Daily-loss Latch และสถานะ Guard สำหรับ Dashboard รุ่นนี้รักษาเลขราคาอ้างอิงใน ACK ไว้ 8 ตำแหน่งและรองรับ Tick Size ของ CFD ที่ Broker ส่งมาเป็นหน่วยราคา

`MetafxHQTradeGateway.mq4` เป็น EA โปรไฟล์ `special` ตัวเดียวที่ทำงานสองส่วนผ่าน `FILE_COMMON`:

- ส่ง `snapshot.json` ให้ Dashboard อ่านข้อมูลกราฟและข้อมูลสรุปบัญชี
- รับคำสั่งซื้อขายแบบ Flat JSON จาก Local Runner แล้วตรวจ Guard ก่อนส่ง Order

เวอร์ชัน `2.16` รวมหน้าที่ของ Snapshot Indicator เดิมเข้ามาใน Gateway EA แล้ว จึงติดกราฟเพียง EA ตัวเดียวได้ โดยยังคง Contract `metafx-hq-mt4-snapshot-v1` สำหรับข้อมูลอ่านอย่างเดียว และใช้ Signed Envelope รอบ Command/Heartbeat สำหรับเส้นทางส่งคำสั่งทั้ง Shadow, Demo และ Live

- Timer มีเพียงตัวเดียวและทำงานทุก 1 วินาที
- คำสั่ง, Heartbeat, `status.json` และ Kill Switch ถูกตรวจทุก 1 วินาที
- Snapshot ส่งตาม `SnapshotIntervalSeconds` ค่าเริ่มต้นทุก 5 วินาที
- Snapshot ทุก 5 วินาทีไม่ได้หมายความว่า Codex ถูกเรียกทุก 5 วินาที การเรียก AI เป็นหน้าที่ของ Backend และควร Trigger เฉพาะแท่งปิดใหม่
- Frontend และ AI ไม่มีสิทธิ์กำหนด Lot, Risk, Mode, Spread, Slippage หรือ Magic Number
- Lot มาจาก `FixedLot` ใน Inputs ของ EA เท่านั้น
- ค่าเริ่มต้นเป็น `Shadow` และไม่เรียก `OrderSend()`

## สิ่งที่เสริมในรอบ Operational Hardening

- เพดาน Position, Lot, จำนวนเทรด และ P/L ใช้ขอบเขต `ManagedMagicNumbers` แบบรวมทั้งบัญชี ไม่จำกัดเฉพาะ Symbol/กราฟปัจจุบัน เพื่อให้หลาย Channel ใช้เพดาน Portfolio เดียวกันได้
- จำนวนในประวัติของ Channel ที่เลือก **ไม่ใช่** จำนวน Portfolio ทั้งหมดและห้ามใช้แทน Max Order; ค่าที่ Guard ใช้จริงคือ `currentManagedPositions` จากทุก Market Order ในบัญชีที่ Magic อยู่ใน `ManagedMagicNumbers`
- แนวทางที่แนะนำคือให้แต่ละ Channel ใช้ `MagicNumber` ไม่ซ้ำกัน แล้วใส่ Magic ของทุก Channel ใน `ManagedMagicNumbers` ชุดเดียวกันบน EA ทุกตัว หากจำเป็นต้องแชร์ Magic ก็ต้องให้ EA ทุก Channel ใช้รายการ `ManagedMagicNumbers` และเพดาน Portfolio ชุดเดียวกัน มิฉะนั้นให้ถือว่าการตั้งค่าไม่ปลอดภัยสำหรับการทำงานพร้อมกัน
- v2.16 บังคับเงื่อนไขนี้ด้วย Account Portfolio Policy Lease: EA ทุกตัวของบัญชีเดียวกันภายใต้ Windows User/`FILE_COMMON` เดียวกันต้องมีชุด Magic หลัง Sort และเพดาน `MaxManagedOpenPositions`, `MaxManagedTotalLots`, `MaxTradesPerBrokerDay`, Daily/Weekly Loss, Consecutive-loss/Cooldown และ Account Drawdown ตรงกัน หากต่างกัน EA ตัวใหม่หยุดที่ `OnInit` ด้วย `PORTFOLIO_POLICY_MISMATCH` เมื่อ EA เดิมหยุดครบแล้วจึงเปลี่ยน Policy ได้; Lease ที่เหลือจาก Process crash จะถูกตรวจและล้างโดยไม่เกิด stale-lock deadlock
- ชื่อ Lease ใช้ช่องแบบสั้น `policy-p-<policy-prefix16>-c-<channel-prefix16>.lease` เพื่อให้พาธที่ขยายใต้ `FILE_COMMON` ไม่เกินงบ 259 ตัวอักษรบน Windows แบบ `MAX_PATH`; prefix ใช้เลือกชื่อไฟล์เท่านั้น การยืนยันสิทธิ์อ่าน Payload V2 ซึ่งมี Account/Policy/Channel SHA-256 เต็ม 64 hex พร้อม Snapshot Channel ที่ไม่ใช่ Secret แล้วคำนวณ Channel SHA-256 ซ้ำให้ตรงครบ 64 hex หาก prefix ชนกัน, digest ส่วนท้ายถูกแก้, Payload ผิดรูป, อ่านไม่ได้, สแกนไดเรกทอรีผิดพลาด หรือพาธเกินงบ ระบบหยุดแบบ fail-closed โดย `init-status.json` รายงานเฉพาะ Error Code และความยาวพาธ ไม่เผยพาธจริง
- ตัวสแกนยังอ่าน Lease ชื่อเดิม `policy-<policy-digest64>-channel-<channel-digest64>.lease` และตรวจ Payload เดิมแบบเต็ม เพื่อไม่มองข้าม Instance รุ่นก่อนหน้า; ก่อนอ่าน Payload จะ probe ownership แบบ exclusive ทำให้ไฟล์ stale ว่าง/เขียนค้างจาก Process crash ถูกลบได้ แต่ไฟล์ที่ยังมี owner ต้องผ่านการตรวจเต็ม; ชื่อใหม่ยังอยู่ใน namespace `policy-*.lease` ทำให้ EA v2.16 ก่อนแพตช์เห็นรูปแบบที่ไม่รู้จักแล้วหยุด fail-closed แทนการรันปะปน
- `status.json` v5 เปิดเผยสถานะที่ตรวจได้โดยตรง ได้แก่ `portfolioPolicyStatus=ready`, Digest ที่ไม่ใช่ Secret, ชุด Managed Magic/Allowed Symbol/Timeframe, `concurrencyBoundary=same_windows_user_file_common` และ `crossVpsDistributedLock=false`; หาก Policy ไม่ตรง EA จะไม่เผยแพร่สถานะ READY และ `init-status.json` จะระบุ `PORTFOLIO_POLICY_MISMATCH`
- การรับประกันนี้ใช้ได้เมื่อ EA ทุกตัวที่เปิดพร้อมกันเป็น v2.16 ขึ้นไปเท่านั้น ก่อนอัปเกรดจาก v2.15 หรือต่ำกว่าให้หยุด EA เก่าทุกตัวก่อน แล้วจึง Attach v2.16 ด้วย Policy ชุดเดียวกัน; ห้ามรันรุ่นเก่าปะปนในบัญชีเดียวกัน
- เพิ่ม Weekly Loss Guard และ Consecutive-loss Cooldown; ผลกำไร/ขาดทุนที่ใช้กับ Guard นับเฉพาะ Market Order ของ Magic ที่ประกาศไว้
- `PositionLifecycleMode` เริ่มต้นที่ `LIFECYCLE_SLTP_ONLY` จึงไม่ปิด Order เพิ่มเอง ค่า Max Holding และ Session Close จะทำงานเมื่อผู้ใช้เลือกโหมดนั้นเองเท่านั้น ส่วน Rollover Entry Block เริ่มต้นปิด
- หลัง `OrderSend()` EA ต้อง `OrderSelect()` Ticket กลับมาตรวจราคาเปิด, SL, TP, Magic Number และ Comment ก่อน ACK เป็น `EXECUTED`; หากยืนยันไม่ได้จะเป็น `EXECUTION_UNKNOWN` และไม่ส่งซ้ำ
- EA เขียน `outcomes/<commandId>.json` เพื่ออัปเดตสถานะ `OPEN/CLOSED` และ Closed P/L ของ Order ที่จัดการอยู่
- `capabilities.json` แจ้งความสามารถจริงโดยไม่บรรจุ Key หรือ Secret
- Local Runner สร้าง Key แบบสุ่มแยกตาม Channel และเก็บไว้ในพื้นที่ Local เท่านั้น ส่วน EA ตรวจ Signed Envelope ก่อนแตะ Ledger และตรวจซ้ำก่อน `OrderSend()`
- Live พร้อมใช้งานเชิงโค้ด แต่ปิดโดยค่าเริ่มต้น จนกว่า EA จะอยู่โหมด Live, เปิด `LiveArmed`, ปักหมุด `TrustedSigningKeyId` ให้ตรงกับ Local Runner และ Guard ทุกข้อผ่าน
- Snapshot แยกสรุป `ACCOUNT_WIDE` ออกจาก `MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE` และรายงาน `marketOpen` จากสถานะ Connection, Broker trade flag และความสดของ Tick เท่านั้น โดยไม่เดาชื่อ Session ตลาด
- ตัวเลขรายวัน รายสัปดาห์ และจำนวนแพ้ต่อเนื่องอ้างอิงเฉพาะประวัติบัญชีที่ MT4 โหลดไว้ (`MT4_LOADED_ACCOUNT_HISTORY`) จึงควรตั้งแท็บ Account History เป็น All History ก่อนใช้ Guard ใน Demo

> Source ไม่ติดตั้งหรือเปิด MT4 ให้อัตโนมัติในเครื่องใหม่ ผู้ใช้ต้องเลือก Terminal เป้าหมายก่อนเสมอ Source v2.16 ต้อง Compile ให้ผ่าน `0 errors, 0 warnings` และตรวจ Hash ของ EX4 ก่อนติดตั้งแทนรุ่นเดิม การมีโค้ด Live ไม่ได้หมายความว่าบัญชีจริงถูกเปิดอัตโนมัติ

## ความเข้ากันได้กับ Indicator เดิม

`MetafxHQReadOnlySnapshot.mq4` ยังถูกเก็บไว้โดยไม่แก้ไข เพื่อใช้เป็นตัวสำรองแบบ Read-only:

- การติดตั้งใหม่ให้ใช้ `MetafxHQTradeGateway.mq4` ตัวเดียว
- หากใช้ EA แบบรวมแล้ว **ห้ามติด Indicator เดิมด้วย Channel เดียวกันบนกราฟอื่นพร้อมกัน** เพราะทั้งสองตัวจะเขียน `snapshot.json` ทับกัน
- หากต้องการ Dashboard อย่างเดียวและไม่ต้องการเส้นทางรับคำสั่ง สามารถใช้ Indicator เดิมต่อได้
- Snapshot จาก EA แบบรวมยังมี `"mode":"read_only"` เพราะ Field นี้อธิบายสิทธิ์ของข้อมูล Snapshot ไม่ใช่โหมดส่ง Order ของ Gateway

## ตารางเวลาการทำงาน

| งาน | รอบเวลา | หมายเหตุ |
|---|---:|---|
| ตรวจ `command.json` และ Heartbeat | 1 วินาที | `PollIntervalSeconds` ต้องเท่ากับ `1` |
| เขียน `status.json` | 1 วินาที | Backend ใช้ตรวจว่า EA ยัง Online |
| ตรวจ Kill Switch | ทุกครั้งที่ตรวจคำสั่ง | พบ `kill.switch` แล้วปฏิเสธคำสั่งทันที |
| เขียน `snapshot.json` | ค่าเริ่มต้น 5 วินาที | ปรับได้ 2–60 วินาที |
| เรียก AI วิเคราะห์ | ไม่ได้ทำใน EA | Backend ควบคุม Trigger เช่น เมื่อแท่งปิดใหม่ |

## ขอบเขตคำสั่งจาก AI

AI ส่งได้เฉพาะ:

- `BUY` หรือ `SELL`
- Symbol และ Timeframe ที่ต้องตรงกับกราฟซึ่งติด EA อยู่
- Stop Loss และ Take Profit เป็นราคาแบบ Absolute
- รหัส Mission, Council Decision และ Heartbeat สำหรับ Audit

ถ้าพบ Field เช่น `lot`, `lots`, `volume`, `fixedLot`, `risk` หรือ `riskPercent` ระบบจะปฏิเสธทั้งคำสั่ง

Gateway ใช้ Strict Allowlist ของ Field ดังนั้น Field ที่ไม่อยู่ใน Contract จะถูกปฏิเสธเช่นกัน

## โหมดการทำงาน

| Mode | พฤติกรรม |
|---|---|
| `GATEWAY_SHADOW` | ตรวจ Contract, TTL, Heartbeat, Symbol, Timeframe, SL/TP และ Filter ทั้งหมด แต่ไม่ส่ง Order |
| `GATEWAY_DEMO` | ส่ง Order ได้เฉพาะบัญชี Demo และคำสั่งต้องผ่าน Signed Envelope |
| `GATEWAY_LIVE` | ส่ง Order ได้เฉพาะบัญชีที่ไม่ใช่ Demo ต้องตั้ง `LiveArmed=true` และปักหมุด Signing Key ID ให้ตรงกับ Local Runner |

การเลือก Mode, `LiveArmed` และ `TrustedSigningKeyId` เป็นการตั้งค่าที่หน้า Inputs ของ EA ไม่รับค่าจาก AI หรือ Frontend

## Inputs สำคัญ

| Input | ค่าเริ่มต้น | ความหมาย |
|---|---:|---|
| `SnapshotChannel` | `mtc-set-from-hq` | Candidate/Channel ID ต้องขึ้นต้นด้วย `mtc-` |
| `GatewayMode` | `GATEWAY_SHADOW` | Shadow, Demo หรือ Live |
| `LiveArmed` | `false` | สวิตช์ Arm สำหรับบัญชี Live |
| `TrustedSigningKeyId` | ค่าว่าง | Key ID แบบไม่เป็นความลับ; ระบบตัดช่องว่างและแปลงเป็นตัวพิมพ์เล็ก Demo/Shadow ใช้ Active Key ของ Backend ต่อได้แม้ Optional Pin ผิดหรือไม่ตรง แต่ Live ต้องกรอก Key ID ให้ถูกและตรงเพื่อปักหมุด |
| `FixedLot` | `0.01` | Lot คงที่จาก EA เท่านั้น |
| `MagicNumber` | `4186001` | Magic Number ของ Gateway |
| `PollIntervalSeconds` | `1` | รอบตรวจคำสั่งและ Heartbeat; เวอร์ชันนี้บังคับเป็น 1 วินาที |
| `SnapshotIntervalSeconds` | `5` | รอบส่ง Snapshot ปรับได้ 2–60 วินาที |
| `SnapshotBars` | `240` | จำนวนแท่งปิดที่ส่ง ปรับได้ 20–1,000 แท่ง; ใช้ 500/1,000 เมื่อต้องการหน้าต่างวิเคราะห์ยาว โดย Codex ยังทำงานตาม Trigger แท่งปิดใหม่ |
| `MaxCommandTtlSeconds` | `120` | อายุคำสั่งสูงสุด |
| `MaxHeartbeatTtlSeconds` | `60` | อายุ Heartbeat สูงสุด |
| `MaxSpreadPoints` | `30` | Spread สูงสุดจาก EA |
| `SlippagePoints` | `3` | Slippage สูงสุดจาก EA |
| `MaxSnapshotAgeSeconds` | `300` | อายุ Snapshot สูงสุดก่อนปฏิเสธคำสั่ง |
| `MaxSignalDriftPoints` | `100` | ระยะราคาปัจจุบันจากราคา Snapshot สูงสุด |
| `MaxQuoteAgeSeconds` | `30` | อายุ Tick ล่าสุดสูงสุด |
| `MaxManagedOpenPositions` | `1` | จำนวน Position สูงสุดรวมทั้งบัญชีของ Magic ที่ระบุใน `ManagedMagicNumbers` |
| `MaxManagedTotalLots` | `0.10` | Lot รวมสูงสุดทั้งบัญชีของ Magic ที่ระบุใน `ManagedMagicNumbers` |
| `MaxTradesPerBrokerDay` | `6` | จำนวนการเปิดเทรดสูงสุดต่อวัน Broker |
| `MaxLossPerTradePercent` | `1.0` | Loss ประมาณการจาก Fixed Lot ถึง SL สูงสุดต่อครั้ง |
| `MaxDailyLossPercent` | `3.0` | Daily Loss สูงสุด; เมื่อชนแล้ว Latch จนเปลี่ยนวัน Broker |
| `MaxAccountEquityDrawdownPercent` | `10.0` | Drawdown ปัจจุบันของบัญชีสูงสุดสำหรับคำสั่งใหม่ |
| `MinRewardRiskRatio` | `1.0` | Reward/Risk ขั้นต่ำจาก SL/TP ที่ AI เสนอ |
| `MinProjectedMarginLevelPercent` | `300.0` | Margin Level คาดการณ์ขั้นต่ำหลังเปิด Order |
| `AllowedSymbols` | `XAUUSD` | รายการ Symbol คั่นด้วยจุลภาค; ชื่อฐานยอมรับ suffix ของ Broker ที่เป็นตัวอักษร/ตัวเลข/`.`/`_`/`#`/`-` ยาวไม่เกิน 8 ตัว แต่คำสั่งต้องใช้ชื่อเต็มตรงกับกราฟ เช่น `XAUUSD.m` หรือ `EURUSD#` (`+` ไม่รองรับ) |
| `AllowedTimeframes` | `M5,...,MN1` | Timeframe Allowlist; ไม่รองรับ M1 |
| `RequireHeartbeat` | `true` | Fail-closed เมื่อไม่มี Heartbeat |

`FixedLot` ต้องตรงกับ Min/Max/Lot Step ของ Broker หากไม่ตรง EA จะไม่เริ่มทำงาน

## ตำแหน่งไฟล์ใน FILE_COMMON

EA รุ่นนี้ไม่ใช้ HTTP และไม่เรียก `WebRequest()` จึงไม่ต้องเพิ่ม URL ในหน้า Allow WebRequest ของ MT4 การสื่อสารทั้งหมดอยู่ใน `FILE_COMMON` ของ Windows User เดียวกัน ซึ่งโดยทั่วไปคือ:

```text
%APPDATA%\MetaQuotes\Terminal\Common\Files
```

หากหาไฟล์ไม่พบ ให้เปิด MT4 แล้วเลือก `File > Open Data Folder` จากนั้นย้อนขึ้นไปที่ `Terminal\Common\Files` ของ Windows User เดียวกัน ห้ามใช้ `MQL4\Files` ของ Terminal เพราะเป็นคนละตำแหน่ง

เมื่อ Channel เป็น `mtc-demo-01`:

```text
MetaQuotes\Terminal\Common\Files\
└─ MetafxHQ\
   └─ mtc-demo-01\
      ├─ snapshot.json
      └─ trade-gateway\
         ├─ command.json
         ├─ heartbeat.json
         ├─ status.json
         ├─ kill.switch
         ├─ keys\
         │  ├─ active-key.id
         │  └─ <keyId>.key
         ├─ acks\
         │  └─ <commandId>.json
         ├─ processed\
         │  ├─ commands\
         │  └─ idempotency\
         ├─ state\
         │  ├─ last-order-bar.txt
         │  ├─ channel-owner.lock
         │  └─ daily-loss-YYYY.MM.DD.lock
         └─ audit\
            └─ events.jsonl
```

- Local Runner ควรเขียน `command.json.tmp` แล้ว Rename เป็น `command.json`
- Unified EA เขียน `snapshot.tmp` แล้ว Rename เป็น `snapshot.json` แบบ Atomic
- Atomic writer ลองใหม่สูงสุด 3 ครั้งด้วย Backoff 25/50 ms และบันทึก `GetLastError` พร้อมจำนวน Operation ที่ล้มเหลวต่อเนื่องบนกราฟ; การ Retry นี้เป็นเฉพาะการเขียนไฟล์ ไม่ใช่การ Retry `OrderSend()`
- Gateway จะไม่ลบ `command.json`; Local Runner เป็นเจ้าของ Lifecycle
- Local Runner ต้องรอ ACK ก่อน Publish คำสั่งถัดไป
- Gateway เขียน `status.json.tmp` แล้ว Rename ทับ `status.json` แบบ Atomic ทุก `OnTimer`

## สถานะ Gateway สำหรับ Local Runner

Gateway เขียน `status.json` ไว้ในโฟลเดอร์ Channel เดียวกับ `command.json` และ `heartbeat.json` เพื่อให้ Local Runner อ่านสถานะล่าสุดได้โดยไม่ต้องอ่านข้อความจากหน้าจอ MT4

ดูรูปแบบที่ `status.example.json` โดยมี Field แบบ Flat JSON และไม่มี Account Number, Broker Password, Token, Cookie หรือ Secret:

```text
schemaVersion
channelId
profile
mode
liveArmed
fixedLot
symbol
timeframe
observedAt
autoTradingAllowed
tradeAllowed
killSwitchActive
commandSchemaVersion
ackSchemaVersion
executionGuardReady
executionGuardReason
maxManagedPositions / currentManagedPositions
maxManagedLots / currentManagedLots
maxTradesToday / currentTradesToday
maxLossPerTradePercent / maxDailyLossPercent / managedDailyPnl
maxAccountEquityDrawdownPercent / currentAccountEquityDrawdownPercent
minRewardRiskRatio / minProjectedMarginLevelPercent / currentMarginLevelPercent
maxSnapshotAgeSeconds / maxSignalDriftPoints / maxQuoteAgeSeconds
signedCommandVerificationAvailable / activeSigningKeyId / signingKeyPinned
signatureAlgorithm / lastSignatureVerificationStatus
```

- `observedAt` เป็น Unix UTC Seconds; Backend ต้องตรวจความสดของเวลานี้ก่อนเชื่อว่าสถานะยัง Online
- `OrderOpenTime`, `OrderCloseTime`, เวลาแท่ง และ `cooldownUntil` เป็นเวลา Broker; การคำนวณ Cooldown/Max Holding ใช้ `TimeCurrent()` ใน clock domain เดียวกัน ห้ามนำไปลบหรือเปรียบเทียบกับ UTC และหน้าจอต้องระบุว่าเป็นเวลา Broker
- `autoTradingAllowed` สะท้อนปุ่ม AutoTrading/Expert Advisors ของ MT4
- `tradeAllowed` สะท้อนว่าสถานะ Terminal ในขณะที่เขียนไฟล์อนุญาตให้ EA ส่งคำสั่งซื้อขายหรือไม่
- `killSwitchActive=true` หมายถึงมีไฟล์ `kill.switch` และ Gateway จะไม่รับคำสั่งซื้อขาย
- การมี `mode=live` หรือ `liveArmed=true` ในไฟล์สถานะไม่ได้แทนการตรวจ Gate อื่น เช่น Heartbeat, Spread, Symbol, Timeframe, TTL และข้อจำกัดบัญชี

## Signed Envelope และขอบเขตความลับ

`command.json` และ `heartbeat.json` ไม่ใช่ Inner JSON ตรง ๆ อีกต่อไป แต่เป็น Envelope ที่มีเฉพาะ `schemaVersion`, `algorithm`, `keyId`, `payloadHex` และ `signatureHex` โดย EA ตรวจ HMAC-SHA256 ก่อนอ่านคำสั่ง และตรวจซ้ำที่ขอบ `OrderSend()`

- Local Runner สร้าง Key สุ่ม 32 ไบต์แยกตาม Channel และเก็บใน `keys/<keyId>.key`
- `active-key.id` บอกเฉพาะ Key ID ปัจจุบัน ไม่ใช่ Secret
- Dashboard แสดงได้เฉพาะ Key ID, Algorithm, สถานะปักหมุด และผลตรวจลายเซ็น ห้ามส่ง Key หรือพาธไฟล์ให้ Frontend
- Live ต้องกรอก `TrustedSigningKeyId` ให้ตรงกับ Active Key ID; ห้ามกรอก Secret Key ใน Inputs ของ EA
- HMAC ป้องกันคำสั่งปลอมจาก Frontend หรือไฟล์ที่ถูกแก้โดยไม่รู้ Key แต่ไม่ป้องกัน Malware/โปรเซสอื่นที่รันภายใต้ Windows User เดียวกันและอ่าน Local Key ได้ สำหรับ Live ควรใช้ Windows User/VPS เฉพาะและจำกัดสิทธิ์โฟลเดอร์ FILE_COMMON

## Command Contract

ดู Inner Payload ที่ `command.example.json` และไฟล์ที่ EA รับจริงที่ `command-envelope.example.json`

ค่าเวลาในไฟล์ตัวอย่างมีไว้แสดงรูปแบบเท่านั้น Local Runner ต้องสร้าง `issuedAt`, `expiresAt` และ `heartbeatId` ใหม่ทุกครั้ง ห้ามนำเวลาตัวอย่างเก่าไปใช้ส่งคำสั่งจริง

Field บังคับ:

```text
schemaVersion
commandId
idempotencyKey
channelId
snapshotId
snapshotObservedAt
barTime
referencePrice
action
symbol
timeframe
stopLoss
takeProfit
issuedAt
expiresAt
heartbeatId
```

Field อ้างอิงที่ไม่บังคับ:

```text
missionId
councilDecisionId
ownerAgentId
```

ข้อกำหนด:

- JSON ต้องเป็น Object ชั้นเดียว ไม่มี Object/Array ซ้อน
- Key ห้ามซ้ำ
- String ใช้ ASCII ที่ไม่ต้อง Escape
- `schemaVersion` ต้องเป็น `metafx-hq-mt4-command-v2`
- `issuedAt` และ `expiresAt` เป็น Unix UTC Seconds
- `snapshotObservedAt` เป็น Unix UTC Seconds และต้องไม่เก่ากว่า `MaxSnapshotAgeSeconds`
- `barTime` ต้องตรงกับแท่งปิดล่าสุดของกราฟที่ติด EA
- `referencePrice` คือราคากลางจาก Snapshot; EA จะปฏิเสธเมื่อราคาเคลื่อนเกิน `MaxSignalDriftPoints`
- `expiresAt` ต้องยังไม่หมดอายุ และ TTL ต้องไม่เกิน Input ของ EA
- `stopLoss` และ `takeProfit` เป็นราคา Absolute
- BUY เปิดที่ `Ask`: ต้องมี `SL < Bid` และ `TP > Ask`
- SELL เปิดที่ `Bid`: ต้องมี `SL > Ask` และ `TP < Bid`
- ราคา SL/TP ถูก Normalize ตาม `Digits` ของ Symbol และต้องผ่าน Stop Level ของ Broker; Broker ยังอาจปฏิเสธในเวลาส่งจริงหากมี Floating Stop Level หรือกฎเฉพาะบัญชี

## Heartbeat และ Kill Switch

ดู Inner Payload ที่ `heartbeat.example.json` และไฟล์ที่ EA รับจริงที่ `heartbeat-envelope.example.json`

- `heartbeatId` ในคำสั่งต้องตรงกับ Heartbeat ล่าสุด
- Heartbeat ที่หมดอายุทำให้ Gateway ปฏิเสธคำสั่ง
- หากไฟล์ `kill.switch` มีอยู่ Gateway จะหยุดรับคำสั่งซื้อขายทันที
- การลบ `kill.switch` ต้องเป็นการกระทำโดย Local Admin/Runner ที่ได้รับสิทธิ์ ไม่ใช่ AI Prompt

## Idempotency และ One-order-per-bar

- Gateway เก็บ Ledger ทั้ง `commandId` และ `idempotencyKey`
- คำสั่งเดิมจะไม่ถูกส่ง Order ซ้ำหลัง Restart
- Gateway เขียนสถานะ `EXECUTING` ลงดิสก์ก่อนเรียก `OrderSend()`
- หาก `OrderSend()` ล้มเหลว Gateway จะไม่ Retry อัตโนมัติ Backend ต้องตรวจ Audit และออกคำสั่งใหม่ด้วย ID ใหม่
- Demo/Live อนุญาตหนึ่ง Execution Attempt ต่อแท่งของกราฟที่ติด EA
- Bar Lock ถูกเขียนหลัง Heartbeat, Quote, แท่งปิด, SL/TP, Risk, Margin, Spread และลายเซ็นขั้นสุดท้ายผ่าน แต่ก่อน `OrderSend()` เพื่อไม่กินสิทธิ์ทั้งแท่งจากข้อมูลที่ยังไม่พร้อม และยังลดความเสี่ยงส่งซ้ำหลังโปรเซสล้ม
- คำสั่งที่ใช้ `idempotencyKey` เดิมจะอ้างถึงผลเดิมและไม่เขียนทับ Ledger ต้นฉบับ
- ตอน `OnInit()` EA ตรวจ Processed ACK ไม่เกิน 256 ไฟล์และ Backfill เฉพาะ ACK `EXECUTED` ที่ Persist แล้ว โดย Ticket, Magic, Symbol, BUY/SELL, Lot, Open Price, SL, TP และ Comment ต้องตรง Order จริงทั้งหมด; Duplicate Ticket, Map ขัดแย้ง หรือ Field ไม่ตรงจะถูกข้าม และไม่มี `OrderSend()` ในเส้นทางนี้
- Outcome `CLOSED` ใช้เวลา Broker close เป็น `observedAt` แบบคงที่ และไม่ Rewrite เมื่อ Serialized payload ไม่เปลี่ยน

## ACK และ Audit

ACK ตัวอย่างอยู่ที่ `ack.example.json`

สถานะหลัก:

```text
SHADOWED
EXECUTING
EXECUTED
REJECTED
DUPLICATE
FAILED_FINAL
```

ทุกผลลัพธ์ถูกเขียนทั้ง:

- `acks/<commandId>.json`
- Processed Ledger
- `audit/events.jsonl`
- `init-status.json` สำหรับสถานะเริ่มต้นล่าสุด ส่วน Audit จะเก็บประวัติคำเตือนและสาเหตุที่เริ่มไม่สำเร็จ
- Experts Log ของ MT4

หาก EA หายจากกราฟทันที ให้เปิด `init-status.json` ก่อน สาเหตุที่ทำให้ `OnInit()` ล้มเหลวได้แก่ Channel ไม่ถูกต้อง, Input/Magic/Lot/Symbol/Timeframe ไม่ผ่าน, Channel ถูก EA อีกตัวครอบครอง, HMAC Self-test หรือ Signing Key ไม่พร้อม, สร้าง Timer ไม่สำเร็จ หรือเขียน Snapshot/Status/Capabilities ไม่ได้ เมื่อ EA ถูกถอด, Terminal ปิด หรือเปลี่ยนกราฟ รุ่น v2.16 จะลบ `status.json`, `capabilities.json` และ `snapshot.json` เก่าก่อนปล่อย Channel Lock เพื่อไม่ให้ Backend เห็นสถานะ READY ของกราฟเดิม ส่วน `init-status.json` ยังคงบอก Stage/Reason Code ที่แน่นอน

## Preflight ก่อนย้าย Symbol / Timeframe / Terminal

1. หยุดการ Publish คำสั่งใหม่และรอให้ Command ปัจจุบันมี ACK ปลายทางก่อนเปลี่ยนกราฟ
2. ตรวจชื่อ Symbol **เต็มตาม Broker** เช่น `XAUUSD.r` และเพิ่มชื่อฐานใน `AllowedSymbols`; ตรวจ Timeframe อยู่ใน `AllowedTimeframes` และตั้งแต่ M5 ขึ้นไป
3. ใช้ `SnapshotChannel` ไม่ซ้ำสำหรับแต่ละ EA/กราฟ/Terminal หากย้าย EA ตัวเดิมให้คง Channel เดิมได้ แต่ Backend จะตั้ง Baseline ของ Stream ใหม่และไม่เอางานค้างจาก Stream เดิมมาส่ง
4. กำหนด Magic แบบแยก Channel แล้วให้ EA ทุกตัวประกาศ `ManagedMagicNumbers` ชุดเดียวกัน เพื่อให้ `MaxManagedOpenPositions` และ Lot/Loss Guard นับทั้ง Portfolio ตรงกัน
5. Reload/Attach v2.16 แล้วรอ `init-status.json = INIT_SUCCEEDED`, `status.json` และ `snapshot.json` แสดง Channel + Symbol + Timeframe ใหม่ตรงกันก่อนเปิด Automation
6. ทดสอบ Shadow ก่อน Demo และห้ามเปิด Live ระหว่างการย้ายกราฟหรือระหว่างที่สถานะทั้งสามไฟล์ยังไม่ตรงกัน

Stream identity และ `command.symbol` ใช้ชื่อ Symbol เต็มหลังตัดช่องว่างและแปลงเป็นตัวพิมพ์ใหญ่เสมอ เช่น Snapshot `eurusd#` ต้องคำนวณด้วย `EURUSD#`; สูตรคือ `SHA256(channelId + "\n" + UPPERCASE(fullSymbol) + "\n" + UPPERCASE(timeframe))` การใช้ตัวพิมพ์จาก Display โดยไม่ Normalize จะถูกปฏิเสธแบบ fail-closed อย่างไรก็ตาม EA ส่ง Order ด้วย `Symbol()` ของกราฟที่ Attach จริง จึงคงชื่อ/case ที่ Broker ใช้ใน execution ไว้

## ข้อสมมติและขอบเขตของ v2.16

- รองรับ Market Order `BUY` และ `SELL` เท่านั้น
- SL/TP เป็นราคา Absolute ไม่ใช่ Points
- หนึ่ง Channel มี Gateway EA เจ้าของเพียงตัวเดียว
- Local Runner Publish คำสั่งทีละรายการ
- FILE_COMMON เป็น Local Trust Boundary และ Signed Envelope ใช้ Shared Secret ภายใน Windows User เดียวกัน; ก่อน Live ควรจำกัด ACL และใช้ Windows User/VPS เฉพาะ
- ไม่มี Close, Modify, Pending Order, Martingale, Grid หรือ Hedge; Recovery ใน v2.16 เป็นการกู้หลักฐาน Ticket/Outcome แบบอ่านอย่างเดียวและไม่สร้างคำสั่งซื้อขาย
- ไม่มีการ Retry `OrderSend()` อัตโนมัติ และไม่มีโหมดเปิด Order แบบไม่ใส่ SL/TP สำหรับ Broker แบบ ECN; หาก Broker ไม่ยอมรับ SL/TP ตอนเปิด คำสั่งจะจบแบบ Fail-closed
- EA หนึ่งตัวดูแล Symbol และ Timeframe ของกราฟที่ติดอยู่เพียงชุดเดียว การใช้หลาย Symbol ต้องแยก Channel/EA และต้องกำหนด `ManagedMagicNumbers` ให้ครอบคลุมพอร์ตที่ต้องการคุมร่วมกัน
- ขอบเขต Concurrency/Portfolio Lock รองรับเฉพาะ MT4 Terminal ที่รันด้วย Windows User เดียวกันและมองเห็น `FILE_COMMON` เดียวกันเท่านั้น การรันบัญชี Broker เดียวกันข้าม VPS/Windows คนละเครื่องไม่แชร์ Lock และยังไม่รองรับ Active Trading พร้อมกัน ต้องกำหนดให้มี Active Execution Owner เพียงเครื่องเดียว
- ความพร้อมเชิง Source/Compile ไม่ใช่หลักฐานว่า Broker ทุกแห่งหรือบัญชีทุกประเภทรับคำสั่งจริง ต้องยืนยัน Shadow และ Demo บน Terminal/Broker เป้าหมายก่อน Live
- ไม่มีการรับประกันกำไร ผลลัพธ์ขึ้นกับกลยุทธ์ ราคา Broker และสภาวะตลาด

## ขั้นติดตั้งหลังผู้ใช้เลือก MT4 แล้ว

ต้องให้ผู้ใช้เลือก MT4 Terminal เป้าหมายก่อน ห้ามเดา Data Folder จาก Terminal อื่น จากนั้นจึงทำแบบมองเห็นได้:

1. ใน MT4 ที่เลือก ใช้ `File > Open Data Folder`
2. วาง Source ที่ `MQL4\Experts\Metafxclub\TradeGateway\MetafxHQTradeGateway.mq4`
3. เปิด MetaEditor จาก MT4 ตัวเดียวกัน แล้ว Compile ให้เห็น Error/Warning จริง
4. กลับ MT4 และ Refresh รายการ Expert Advisors
5. ลาก EA ลงกราฟ Symbol และ Timeframe ที่อยู่ใน Allowlist โดยเริ่มที่ M5 ขึ้นไป
6. ตั้ง `SnapshotChannel` ให้ตรง Candidate ID ที่ Dashboard เลือก
7. เริ่มด้วย `GATEWAY_SHADOW`, `LiveArmed=false`, `TrustedSigningKeyId` ค่าว่าง และตรวจว่า Dashboard ได้ Snapshot/Status พร้อมสถานะลายเซ็น

ไม่ต้องติด `MetafxHQReadOnlySnapshot` ซ้ำเมื่อใช้ Unified EA

## ลำดับเปิดใช้งานอย่างปลอดภัย

### ระยะ 1 — Shadow

- `GatewayMode=GATEWAY_SHADOW`
- `LiveArmed=false`
- ตรวจ Snapshot, Heartbeat, ACK, Duplicate, Expired Command, Spread, SL/TP, One-order-per-bar และ Kill Switch
- ระบบตรวจคำสั่งครบ แต่ไม่เรียก `OrderSend()`

### ระยะ 2 — Demo

- ใช้บัญชี Demo เท่านั้น
- `GatewayMode=GATEWAY_DEMO`
- `LiveArmed=false`
- ใช้ `FixedLot` ต่ำและตรวจผล Signed Envelope, ACK/Ticket/Journal ต่อเนื่อง Demo ใช้เส้นทางลายเซ็นเดียวกับ Live

### ระยะ 3 — Live

- ใช้บัญชีจริงเฉพาะหลัง Shadow และ Demo ผ่านครบ รวมถึง Restart, Duplicate, Expired Command, Heartbeat, Key mismatch และ Kill Switch
- คัดลอกเฉพาะ Active Key ID ที่ Dashboard แสดงไปใส่ `TrustedSigningKeyId` ใน EA; ห้ามคัดลอก Secret Key
- ตั้ง `GatewayMode=GATEWAY_LIVE`, `LiveArmed=true` และตรวจว่า Dashboard แสดง Backend signer, EA verifier, Key match/pin และ Execution Guard พร้อมทั้งหมด
- `OrderSend()` จะทำงานได้เมื่อคะแนนถึงเกณฑ์ที่ผู้ใช้เลือก `1/3`, `2/3` หรือ `3/3`, ไม่มีเสียง BUY/SELL ตรงข้ามกัน, Price Action ส่ง SL/TP ที่ผ่าน Gate, ข่าวไม่ VETO และ Guard ทุกชั้นผ่าน
- `HOLD` ของ News Consultant คือการงดออกเสียง ส่วน `VETO` เท่านั้นที่หยุดรอบ; ถ้า News โหวต BUY/SELL ต้องมีข่าวสดและหลักฐานตาม News Gate
- โหมด Demo ต้องอยู่บนบัญชี Demo และโหมด Live ต้องอยู่บนบัญชีจริง หากประเภทบัญชีไม่ตรงโหมด EA และ Backend จะบล็อกคำสั่ง
- Backend ติดตามผลย้อนหลังได้ แต่จะไม่สร้าง Order ใหม่จาก Mission ที่พ้น `roundDeadlineAt` แล้ว แม้เวลาแท่งจากโบรกเกอร์จะมี timezone ต่างจากเครื่องหรือ Bridge เพิ่งเริ่มใหม่
- AI และ Frontend ยังคงไม่มีสิทธิ์เปลี่ยน Lot, Risk, Mode, Magic Number, `LiveArmed` หรือ `TrustedSigningKeyId`

## ขั้นตอนตรวจรับที่ต้องทำแบบมองเห็นได้

1. ให้ผู้ใช้เลือก MT4 Terminal เป้าหมาย
2. เปิด MetaEditor ของ Terminal นั้นแบบมองเห็นได้
3. วาง Source ใน `MQL4\Experts\Metafxclub\TradeGateway`
4. Compile และตรวจ Error/Warning บนหน้าจอจริง
5. เริ่มทดสอบ `Shadow`
6. ทดสอบ Restart, Duplicate, Expired Command, Heartbeat และ Kill Switch
7. จึงทดสอบ Demo ด้วย Lot ต่ำ
8. ห้ามเปิด Live ก่อนมีผลทดสอบ Demo, Key pin/match, Signed-command, Kill Switch และ ACL ตามนโยบายที่ตกลง
