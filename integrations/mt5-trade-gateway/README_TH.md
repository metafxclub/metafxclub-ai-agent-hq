# MetafxHQ AI Trade Council Gateway สำหรับ MT5

ไฟล์ `MetafxHQTradeGateway.mq5` เป็น Gateway สำหรับ MetaTrader 5 ที่ใช้สัญญาไฟล์กลางชุดเดียวกับ Gateway MT4 เดิม เพื่อให้ Local Runner อ่าน Snapshot ส่งคำสั่งที่ลงลายเซ็น และรับ ACK ได้โดยไม่ต้องมี Backend อีกชุด

## ขอบเขตของรุ่น 1.03

- รองรับเฉพาะบัญชี MT5 แบบ **Hedging** เท่านั้น หากเป็น Netting หรือ Exchange EA จะหยุดตั้งแต่ `OnInit` ด้วย `MT5_HEDGING_ACCOUNT_REQUIRED`
- ค่าเริ่มต้นคือ `GatewayMode = GATEWAY_SHADOW`, `LiveArmed = false` และ `SingleHostLiveAcknowledged = false`
- รองรับคำสั่งตลาด `BUY` และ `SELL` ที่มี SL/TP เท่านั้น
- เลือก Money Management จาก Input ของ EA ได้ 2 แบบ: `MONEY_MANAGEMENT_FIXED_LOT` ใช้ `FixedLot` และ `MONEY_MANAGEMENT_RISK_PERCENT` คำนวณ Lot จาก `RiskPercent` ของ `BALANCE` หรือ `EQUITY` ตาม `RiskCapitalBase`; คำสั่งจาก Backend/AI ไม่มีสิทธิ์กำหนด Lot, Risk หรือโหมด Money Management
- โหมด Risk Percent คิดขาดทุนถึง SL ด้วย `OrderCalcProfit` ในหน่วยเงินของบัญชี เพิ่มระยะเผื่อราคาเสียเปรียบตาม `SlippagePoints` และสำรองค่าธรรมเนียมไป-กลับจาก `EstimatedCommissionPerLot` จึงใช้หลักเดียวกันกับบัญชี Standard, Cent หรือ Pro-Cent โดยไม่มีการเดาชื่อบัญชีหรือคูณ/หาร 100
- Lot ที่คำนวณได้จะปัดลงตาม `SYMBOL_VOLUME_MIN/MAX/STEP`, ไม่ฝืนส่งขั้นต่ำหาก Risk Budget ต่ำกว่า Lot ขั้นต่ำ, เคารพ `SYMBOL_VOLUME_LIMIT`, `MaxManagedTotalLots`, Margin และ `OrderCheck`; ถ้าคำนวณ SL, มูลค่าความเสี่ยง หรือข้อมูลโบรกเกอร์ไม่ได้ ระบบจะ fail-closed
- ขนาด Lot จะคำนวณเพียงครั้งเดียวต่อคำสั่งและบันทึกลง execution-attempt ก่อน `OrderSend`; หาก EA/Terminal รีสตาร์ต การตรวจหลักฐานจะใช้ Lot ที่บันทึกไว้นั้น ไม่คำนวณใหม่จาก Equity หรือ Tick ที่เปลี่ยนไป
- ไม่มีการส่งคำสั่งซ้ำอัตโนมัติ หากผลการส่งไม่สามารถพิสูจน์ได้จะตอบ `EXECUTION_UNKNOWN` และใช้สถานะ one-order-per-bar ที่บันทึกไว้เพื่อป้องกันการยิงซ้ำ
- การกู้คืนหลัง `EXECUTION_UNKNOWN` ใช้ reason code เดียวคือ `RECOVERED_ORDER_FOUND` และ Backend ยอมรับเฉพาะ MT5 command stream ที่ผูกบัญชีแล้ว พร้อม ticket, ราคา, SL/TP, Magic และ comment ที่ตรงกับคำสั่งครบถ้วนเท่านั้น
- รุ่นนี้ใช้ `LIFECYCLE_SLTP_ONLY` เท่านั้น ไม่ปิด Position ตามเวลา
- Daily/Weekly loss guard นับผลขาดทุนที่ปิดแล้วรวมกับ Floating loss ปัจจุบันของทุก Position ที่อยู่ใน `ManagedMagicNumbers`; Floating profit ที่ยังไม่ปิดจะไม่นำมาหักล้างผลขาดทุนเพื่อคลาย Guard
- หาก MT5 อ่านช่วงเวลาเทรดของ Symbol จากโบรกเกอร์ไม่ได้หรือข้อมูล Session ไม่ถูกต้อง ระบบจะ fail-closed และไม่ส่งคำสั่ง
- เพดาน Input ฝั่ง Execution คือ `MaxSpreadPoints <= 10000`, `SlippagePoints <= 1000` และ `MaxSignalDriftPoints <= 10000`; ค่าที่สูงกว่านี้ทำให้ `OnInit` ปฏิเสธการตั้งค่า

## ความเข้ากันได้กับ Backend เดิม

ชื่อ Schema ต่อไปนี้ยังคงเป็นชื่อ MT4 โดยตั้งใจ เพราะเป็นชื่อ protocol เดิม ไม่ใช่การระบุชนิด Terminal:

- `metafx-hq-mt4-command-v2`
- `metafx-hq-mt4-heartbeat-v1`
- `metafx-hq-mt4-signed-envelope-v1`
- `metafx-hq-mt4-ack-v3`
- `metafx-hq-mt4-status-v5`
- `metafx-hq-mt4-snapshot-v1`

ห้ามเปลี่ยนชื่อ Schema เหล่านี้เฉพาะฝั่ง EA เพราะจะทำให้ตัวตรวจสอบ Backend ไม่ตรงกัน แต่ลายเซ็นของ MT5 แยก domain เป็น `METAFXHQ|MT5|...` และผูก `accountBindingId` แบบ SHA-256 ที่สร้างจาก Platform + Login + Server ไว้ใน HMAC preimage ทุก Command/Heartbeat โดยไม่ส่งเลขบัญชีจริงไปยัง Frontend, Log หรือ Report ดังนั้น EA MT4 จะตรวจคำสั่ง MT5 ไม่ผ่าน และการเปลี่ยนบัญชี MT5 จะทำให้ binding เดิมใช้ไม่ได้

EA ใช้ `FILE_COMMON` ภายใต้ `MetafxHQ\\<SnapshotChannel>` เหมือน MT4 และใช้ namespace `MT4|<login>|<server>` สำหรับ account execution lock โดยตั้งใจ เพื่อประสาน MT4 กับ MT5 ที่ใช้บัญชีเดียวกันภายใต้ Windows user และเครื่องเดียวกัน

รุ่น 1.03 เปิด `GATEWAY_LIVE` ได้เฉพาะรูปแบบ **Single-host Live** โดยถือ account-owner lock แบบค้างตลอดอายุ EA ตาม Login + Server ภายใต้ `FILE_COMMON` หากมี Gateway MT5 รุ่นที่รองรับ lock นี้เป็นเจ้าของบัญชีเดียวกันอยู่แล้ว ตัวที่สองจะหยุดด้วย `LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE` และหากมีการเปลี่ยน Login หรือ Server หลังเริ่มทำงาน คำสั่งจะถูกปฏิเสธด้วย `LIVE_ACCOUNT_BINDING_CHANGED`

ข้อจำกัดสำคัญ: `FILE_COMMON` **ไม่ใช่ Distributed Lock** และไม่สามารถกัน Terminal ที่อยู่คนละ Windows user, คนละเครื่อง หรือคนละ VPS ได้ ค่า Status จึงยังรายงาน `crossVpsDistributedLock=false` และ `liveSafetyScope=single_windows_user_file_common_only` ตามความจริง ห้ามเปิด Live ของบัญชีเดียวกันซ้ำบน Windows user/เครื่อง/VPS อื่น หากต้องการรันข้ามหลายเครื่องต้องเพิ่ม remote account-scoped fenced lease ที่ Backend ก่อน

## การติดตั้ง

1. เปิด MT5 แล้วเลือก `File > Open Data Folder`
2. คัดลอก `MetafxHQTradeGateway.mq5` ไปที่ `MQL5\\Experts\\Metafxclub\\TradeGateway`
3. เปิดไฟล์ด้วย MetaEditor 5 แล้ว Compile
4. ลาก EA ลงกราฟ Symbol และ Timeframe ที่ตรงกับ Dashboard
5. ใส่ Channel ID จาก AI Agent HQ ใน `SnapshotChannel`
6. เลือก `MoneyManagementMode`:
   - `MONEY_MANAGEMENT_FIXED_LOT`: ตั้ง `FixedLot`
   - `MONEY_MANAGEMENT_RISK_PERCENT`: ตั้ง `RiskPercent` (ต้องไม่เกิน `MaxLossPerTradePercent`), เลือก `RiskCapitalBase` เป็น `EQUITY` หรือ `BALANCE` และตั้ง `EstimatedCommissionPerLot` เป็นค่าประมาณค่าธรรมเนียมไป-กลับต่อ 1.0 Lot ในหน่วยเงินของบัญชี
7. เริ่มด้วย `GATEWAY_SHADOW` และตรวจว่า Snapshot, Status และ Shadow ACK ปรากฏครบ รวมถึง `positionSizingMode`, `riskPercent`, `riskCapitalBase` และ Broker volume limits
8. ใช้บัญชี Demo เปลี่ยนเป็น `GATEWAY_DEMO` แล้วทดสอบคำสั่งจริงแบบมองเห็นได้ก่อนเสมอ

## ขั้นตอนเปิด Single-host Live

เปิด Live หลังจาก Demo ผ่านแล้วเท่านั้น และต้องครบทุกข้อดังนี้

1. ตรวจว่า Dashboard เลือก MT5 Terminal/Channel ที่ต้องการเพียงตัวเดียว และ Login + Server ตรงกับบัญชีจริงที่จะใช้
2. ใช้บัญชี MT5 แบบ **Real + Hedging** เท่านั้น เปิด Algo Trading และอนุญาต EA ให้เทรด
3. ตั้ง `GatewayMode = GATEWAY_LIVE`
4. ตั้ง `TrustedSigningKeyId` เป็น Key ID ที่ Local Runner ใช้อยู่จริง ห้ามเว้นว่าง และต้องผ่าน HMAC verification
5. ตั้ง `LiveArmed = true`
6. อ่านข้อจำกัด Single-host ด้านบน แล้วตั้ง `SingleHostLiveAcknowledged = true` เฉพาะเมื่อยืนยันว่าจะไม่รันบัญชีเดียวกันบน Windows user/เครื่อง/VPS อื่น
7. ตรวจข้อความบนกราฟให้เป็น `Live Owner Lock: ready`, `Risk Guard: READY` และยืนยันว่าแสดง `Cross-VPS Distributed Lock: false` ก่อนเริ่ม

หากขาด Real account, `LiveArmed`, acknowledgement, signing pin/HMAC, heartbeat, owner lock หรือ Risk Guard ใด ๆ EA จะ fail-closed และไม่เรียก `OrderSend`

การเลือก Terminal ใหม่ที่ Backend จะต้องทำเมื่อไม่มีคำสั่งค้าง/สถานะไม่แน่นอน/Position ที่ระบบดูแลอยู่เท่านั้น แต่ account-owner lock รุ่นนี้ครอบคลุมเฉพาะ Local Gateway ที่รองรับ lock ภายใต้ Windows user และ host เดียว ไม่ได้พิสูจน์ความเป็นเจ้าของข้าม VPS

## หลักฐานการส่งคำสั่ง

ก่อนส่งคำสั่ง EA จะทำ `OrderCheck` กับ `MqlTradeRequest` จริง โดยผลตรวจที่ผ่านต้องมี `MqlTradeCheckResult.retcode == 0` ตามสัญญาของ MQL5 จากนั้น `OrderSend` ต้องได้ `TRADE_RETCODE_DONE` และ EA ต้องตรวจพบทั้ง Deal และ Position ที่ตรงกันทุกช่อง ได้แก่ Symbol, action, Lot ที่เลือกไว้สำหรับคำสั่งนั้น, MagicNumber, comment, SL, TP และ `DEAL_POSITION_ID/POSITION_IDENTIFIER` จึงจะตอบ `EXECUTED` ได้

`OrderSend()` ที่คืนค่า `true` เพียงอย่างเดียวไม่ถือว่าสำเร็จ, `TRADE_RETCODE_DONE_PARTIAL` และ `TRADE_RETCODE_PLACED` ไม่ถูกยกระดับเป็น `EXECUTED`

`estimatedRiskMoney` เป็นค่าประมาณก่อนส่งคำสั่ง ไม่ใช่การรับประกันขาดทุนสูงสุดจริง เพราะราคา Gap, Slippage ที่มากกว่าค่าที่เผื่อไว้, Swap และค่าธรรมเนียมจริงที่ต่างจาก `EstimatedCommissionPerLot` อาจทำให้ผลขาดทุนจริงสูงกว่าได้ ต้องตั้งค่าจากเงื่อนไขบัญชีของโบรกเกอร์และทดลองบน Demo ก่อน Live เสมอ

## การ Compile ที่ตรวจแล้ว

เปิด MetaEditor 5 จาก MT5 ที่ต้องการใช้งาน เปิดไฟล์ `MetafxHQTradeGateway.mq5` จากโฟลเดอร์ `MQL5\Experts\Metafxclub\TradeGateway` แล้วกด **Compile** จากนั้นตรวจผลใน Toolbox ว่าไม่มี Error หรือ Warning ก่อนนำ EA ไปวางบนกราฟ

ผลที่ตรวจล่าสุด: `0 errors, 0 warnings` บน `X64 Regular`

ผล Compile เป็นเพียง `compile_verified` ยังไม่ใช่หลักฐานว่าได้ส่งคำสั่งจริงบนบัญชี Demo หรือ Live ต้องทดสอบแบบมองเห็นได้บน MT5 Demo อีกครั้งก่อนใช้งานเงินจริง และระบบนี้ไม่ใช่การรับประกันผลกำไร
