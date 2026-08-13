# MetafxHQTradeGateway v2.16 — Stream Transition Hardening

ชุด Compile สำหรับ MT4 ที่ทำให้การย้าย EA ข้าม Symbol, Timeframe, Channel และ Terminal ปลอดภัยขึ้น

- ผูก Stream และ Bar Claim ด้วย `channelId + ชื่อ Symbol เต็ม + timeframe`; เวลาแท่งเดียวกันในคนละ Stream ใช้ได้ แต่ Stream เดิมได้เพียงครั้งเดียว
- รองรับ Broker suffix `#` เช่น `EURUSD#` ให้ตรงกันตลอด Bridge → Gateway → EA โดยยังไม่ยอมรับ `+`
- Stream digest ใช้ชื่อ Symbol เต็มและ Timeframe หลัง Normalize เป็นตัวพิมพ์ใหญ่ จึงไม่แตก Stream เพราะ Display case ต่างกัน
- ตรวจ `streamKey` ซ้ำที่ Backend Publisher เพื่อบล็อกผลวิเคราะห์เก่าซึ่งถูกส่งมาผิดกราฟ
- ล้าง Runtime status/capabilities/snapshot เก่าระหว่างเปลี่ยนกราฟแบบ fail-closed
- แยก Ticket Map, Outcome และ Legacy recovery ตาม Channel ที่มี Command Ledger เป็นเจ้าของจริง
- ใช้ Account Execution Lock แบบ OS file handle ครอบ mutable guards, Bar Claim และ `OrderSend()` ข้ามทุก Channel ที่ใช้บัญชีเดียวกัน; Process ล้มแล้ว OS คืน Handle จึงไม่เกิด stale-lock deadlock
- Max Position/Lot/Trades/Loss ยังคงนับแบบ account-wide ตาม `ManagedMagicNumbers` ไม่ใช่จำนวนรายการในประวัติ Channel เดียว
- Account Portfolio Policy Lease บังคับให้ชุด Managed Magic และ Portfolio caps ตรงกันทุก EA ของบัญชีเดียวกัน; ค่าต่างกันหยุดด้วย `PORTFOLIO_POLICY_MISMATCH` และ Crash lease ถูกล้างได้หลัง OS คืน Handle
- Status schema v5 รายงาน Policy Digest/Scope, Managed Magic, Allowed Symbol/Timeframe และขอบเขต Lock แบบ `same_windows_user_file_common` โดยตรง; Cross-VPS distributed lock เป็น `false`
- ต้องอัปเกรด EA ที่ทำงานพร้อมกันทั้งหมดเป็น v2.16; ไม่รองรับการรัน v2.16 ปะปน v2.15 หรือต่ำกว่าในบัญชีเดียวกัน
- Backend Gateway มีประวัติแบบ cursor pagination เพื่อไม่ให้รายการเก่าหายเงียบหลังเกิน 500 Command
- Consecutive-loss Cooldown และ Max Holding เปรียบเทียบ `OrderCloseTime`/`OrderOpenTime` กับ `TimeCurrent()` ใน clock domain ของ Broker เดียวกัน จึงไม่เลื่อนเร็วหรือช้าตาม Broker UTC+3/UTC-5; Wire `observedAt` ยังคงใช้ UTC

ผล Compile ด้วย MetaEditor ของ RoboForex MT4 เมื่อ 13 สิงหาคม 2569:

```text
Result: 0 errors, 0 warnings, 81 msec elapsed
```

ก่อนย้ายกราฟให้หยุด Publish, รอ Command เดิมจบ, ตรวจชื่อ Symbol เต็ม/Timeframe/Channel/Magic แล้วเริ่ม Shadow ใหม่ตาม `integrations/mt4-trade-gateway/README_TH.md` ชุดนี้ไม่ Deploy, Reload EA, เปิด Live หรือส่งคำสั่งซื้อขายให้อัตโนมัติ

Concurrency guard รองรับเฉพาะ Terminal ภายใต้ Windows User/`FILE_COMMON` เดียวกัน การใช้บัญชีเดียวกันข้าม VPS ต้องมี Active Execution Owner เพียงเครื่องเดียว
