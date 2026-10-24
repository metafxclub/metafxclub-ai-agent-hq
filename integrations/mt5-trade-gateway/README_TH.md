# MetafxHQ AI Trade Council Gateway สำหรับ MT5

ไฟล์ `MetafxHQTradeGateway.mq5` เป็น Gateway สำหรับ MetaTrader 5 ที่ใช้สัญญาไฟล์กลางชุดเดียวกับ Gateway MT4 เดิม เพื่อให้ Local Runner อ่าน Snapshot ส่งคำสั่งที่ลงลายเซ็น และรับ ACK ได้โดยไม่ต้องมี Backend อีกชุด

## ขอบเขตของรุ่น 1.07

- รองรับเฉพาะบัญชี MT5 แบบ **Hedging** เท่านั้น หากเป็น Netting หรือ Exchange EA จะคงติดกราฟเพื่อแสดง `MT5_HEDGING_ACCOUNT_REQUIRED` แต่ไม่เปิดทางประมวลผลคำสั่ง
- ค่าเริ่มต้นคือ `GatewayMode = GATEWAY_SHADOW`, `LiveArmed = false` และ `SingleHostLiveAcknowledged = false`
- รองรับคำสั่งตลาด `BUY` และ `SELL` ที่มี SL/TP เท่านั้น
- เลือก Money Management จาก Input ของ EA ได้ 2 แบบ: `MONEY_MANAGEMENT_FIXED_LOT` ใช้ `FixedLot` และ `MONEY_MANAGEMENT_RISK_PERCENT` คำนวณ Lot จาก `RiskPercent` ของ `BALANCE` หรือ `EQUITY` ตาม `RiskCapitalBase`; คำสั่งจาก Backend/AI ไม่มีสิทธิ์กำหนด Lot, Risk หรือโหมด Money Management
- โหมด Risk Percent คิดขาดทุนถึง SL ด้วย `OrderCalcProfit` ในหน่วยเงินของบัญชี เพิ่มระยะเผื่อราคาเสียเปรียบตาม `SlippagePoints` และ **ไม่รวมค่าคอมมิชชัน** ในงบนี้ เช่น `RiskPercent=1` และ `MaxLossPerTradePercent=1` จำกัดค่าประมาณจากราคาและ slippage ที่ 1% ตามฐานเงินและ hard cap เดิม ผลขาดทุนสุทธิจริงอาจมากกว่านี้เมื่อรวมค่าคอมมิชชัน Swap, Gap หรือ Slippage เกินที่เผื่อไว้ ไม่เดาชื่อบัญชีหรือคูณ/หาร 100 สำหรับบัญชี Cent
- Inputs `EstimatedCommissionPerLot` และ `CommissionFreeAccountConfirmed` ยังคงชื่อและชนิดเดิมเพื่อโหลดชุดตั้งค่าเก่า แต่รุ่น 1.05 ไม่ใช้สองค่านี้คำนวณ Lot, สร้าง policy identity หรือเป็นเงื่อนไขเริ่ม LIVE และไม่ตั้งคำยืนยันบัญชีปลอดค่าคอมมิชชันให้อัตโนมัติ Status ระบุ `riskCostBasis="price_and_slippage_excluding_commission"` และ `estimatedCommissionPerLot=0`; ค่า 0 หมายถึงไม่ได้กันค่าธรรมเนียมในงบ ไม่ได้หมายความว่าโบรกเกอร์ไม่เก็บค่าธรรมเนียม
- โหมด Shadow/Demo อนุญาตการจับคู่ชื่อ Symbol แบบ prefix/suffix ที่มีขอบเขตเพื่อช่วยทดสอบกับชื่อโบรกเกอร์ แต่โหมด Live ต้องใส่ชื่อเต็มของกราฟปัจจุบัน (เช่น `mXAUUSD` หรือ `XAUUSD.a`) เป็น token ตรงตัวใน `AllowedSymbols`; มิฉะนั้นจะ fail-closed ด้วย `LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST`
- Lot ที่คำนวณได้จะปัดลงตาม `SYMBOL_VOLUME_MIN/MAX/STEP`, ไม่ฝืนส่งขั้นต่ำหาก Risk Budget ต่ำกว่า Lot ขั้นต่ำ, เคารพ `SYMBOL_VOLUME_LIMIT`, `MaxManagedTotalLots`, Margin และ `OrderCheck`; ถ้าคำนวณ SL, มูลค่าความเสี่ยง หรือข้อมูลโบรกเกอร์ไม่ได้ ระบบจะ fail-closed
- ขนาด Lot จะคำนวณเพียงครั้งเดียวต่อคำสั่งและบันทึกลง execution-attempt ก่อน `OrderSend`; หาก EA/Terminal รีสตาร์ต การตรวจหลักฐานจะใช้ Lot ที่บันทึกไว้นั้น ไม่คำนวณใหม่จาก Equity หรือ Tick ที่เปลี่ยนไป คำสั่งใหม่บันทึกค่าคอมมิชชันสำรองเป็น 0 แต่การกู้คืนคำสั่งเก่าคงค่า commission/risk ที่บันทึกไว้เดิมโดยไม่เขียนทับย้อนหลัง
- ไม่มีการส่งคำสั่งซ้ำอัตโนมัติ หากผลการส่งไม่สามารถพิสูจน์ได้จะตอบ `EXECUTION_UNKNOWN` และใช้สถานะ one-order-per-bar ที่บันทึกไว้เพื่อป้องกันการยิงซ้ำ
- รุ่น 1.06 ต้องได้รับ `OnTick` จริงหลังเริ่ม EA หรือเชื่อมต่อ Broker ใหม่ และตรวจอายุ Tick ด้วยนาฬิกา monotonic ควบคู่กับเวลา Broker การที่ `TimeCurrent()` ค้างอยู่เมื่อไม่มี Tick ไม่ทำให้ราคาเก่าถูกถือว่าสด; timer และการรีเฟรช Dashboard ไม่ต่ออายุราคา `QUOTE_NOT_OBSERVED` หมายถึงรอ Tick ที่ตรวจสอบได้ ส่วน `QUOTE_STALE_OR_FUTURE` หมายถึงอายุหรือเวลาไม่ผ่านเกณฑ์ จึงไม่ส่ง Order
- การกู้คืนหลัง `EXECUTION_UNKNOWN` ใช้ reason code เดียวคือ `RECOVERED_ORDER_FOUND` และ Backend ยอมรับเฉพาะ MT5 command stream ที่ผูกบัญชีแล้ว พร้อม ticket, ราคา, SL/TP, Magic และ comment ที่ตรงกับคำสั่งครบถ้วนเท่านั้น
- ACK ที่วัด Slippage ตอนส่ง/Fill ได้จริงระบุ `filledSlippageKnown=true` พร้อมจำนวนจุด ส่วนการกู้คืนที่ไม่มีหลักฐานราคาตอนส่งเดิมระบุ `filledSlippageKnown=false` และ `filledSlippagePoints=null` ไม่เติมเป็นศูนย์และไม่อ้างว่าอยู่ใน Slippage reserve หาก ledger มีค่าที่ตรวจสอบได้อยู่ก่อนแล้ว Backend ยังคงหลักฐานเดิม การยืนยันพบ Order ไม่ได้พิสูจน์ Slippage ของคำสั่งเดิม
- รุ่นนี้ใช้ `LIFECYCLE_SLTP_ONLY` เท่านั้น ไม่ปิด Position ตามเวลา
- Daily/Weekly loss guard และ loss streak ยังคงอ่านกำไรขาดทุนจริงรวม `DEAL_COMMISSION`, `DEAL_FEE` และ Swap จากประวัติ รวมกับ Floating loss ตามกติกาเดิมของทุก Position ใน `ManagedMagicNumbers`; Floating profit ที่ยังไม่ปิดจะไม่นำมาหักล้างผลขาดทุนเพื่อคลาย Guard
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

รุ่น 1.07 เปิด `GATEWAY_LIVE` ได้เฉพาะรูปแบบ **Single-host Live** โดยถือ account-owner lock ตาม Login + Server ภายใต้ `FILE_COMMON` ตลอดช่วงที่ initialization สำเร็จ หากมี Gateway MT5 รุ่นที่รองรับ lock นี้เป็นเจ้าของบัญชีเดียวกันอยู่แล้ว ตัวที่สองจะคงติดกราฟในสถานะ blocked ด้วย `LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE` โดยไม่ถือ account-owner lock และหากมีการเปลี่ยน Login หรือ Server หลังเริ่มทำงาน คำสั่งจะถูกปฏิเสธด้วย `LIVE_ACCOUNT_BINDING_CHANGED`

Portfolio policy ของ MT5 รุ่น 1.05 ผูก `riskCostBasis` ไว้ใน digest เพื่อไม่ให้ใช้นโยบายร่วมกับ EA รุ่นเก่าหรือ MT4 ที่ยังรวมค่าคอมมิชชันโดยเข้าใจว่าเหมือนกัน การเปลี่ยน Inputs ค่าธรรมเนียมที่เลิกใช้แล้วไม่เปลี่ยน digest ห้ามลบ policy/lock files เพื่อข้าม policy conflict

ข้อจำกัดสำคัญ: `FILE_COMMON` **ไม่ใช่ Distributed Lock** และไม่สามารถกัน Terminal ที่อยู่คนละ Windows user, คนละเครื่อง หรือคนละ VPS ได้ ค่า Status จึงยังรายงาน `crossVpsDistributedLock=false` และ `liveSafetyScope=single_windows_user_file_common_only` ตามความจริง ห้ามเปิด Live ของบัญชีเดียวกันซ้ำบน Windows user/เครื่อง/VPS อื่น หากต้องการรันข้ามหลายเครื่องต้องเพิ่ม remote account-scoped fenced lease ที่ Backend ก่อน

## การติดตั้ง

1. เปิด MT5 แล้วเลือก `File > Open Data Folder`
2. คัดลอก `MetafxHQTradeGateway.mq5` ไปที่ `MQL5\\Experts\\Metafxclub\\TradeGateway`
3. เปิดไฟล์ด้วย MetaEditor 5 แล้ว Compile
4. ลาก EA ลงกราฟ Symbol และ Timeframe ที่ตรงกับ Dashboard
5. ใส่ Channel ID จาก AI Agent HQ ใน `SnapshotChannel`
6. เลือก `MoneyManagementMode`:
   - `MONEY_MANAGEMENT_FIXED_LOT`: ตั้ง `FixedLot`
   - `MONEY_MANAGEMENT_RISK_PERCENT`: ตั้ง `RiskPercent` (ต้องไม่เกิน `MaxLossPerTradePercent`) และเลือก `RiskCapitalBase` เป็น `EQUITY` หรือ `BALANCE`
   - ทั้งสองโหมด: งบความเสี่ยงไม่รวมค่าคอมมิชชัน; Inputs ค่าธรรมเนียมเดิมมีไว้โหลดชุดตั้งค่าเก่า ไม่ต้องเปลี่ยนเป็นค่าปลอมหรือยืนยันว่าบัญชีปลอดค่าคอมมิชชัน
7. เริ่มด้วย `GATEWAY_SHADOW` และตรวจว่า Snapshot, Status และ Shadow ACK ปรากฏครบ รวมถึง `positionSizingMode`, `riskPercent`, `riskCapitalBase` และ Broker volume limits
8. ใช้บัญชี Demo เปลี่ยนเป็น `GATEWAY_DEMO` แล้วทดสอบคำสั่งจริงแบบมองเห็นได้ก่อนเสมอ

## จำนวนแท่งสำหรับสภา AI และ Deep Analysis

`SnapshotBars` เป็นจำนวนแท่งปิดที่ EA ส่งจาก **Symbol และ Timeframe ของกราฟที่ติด EA อยู่** ค่าเริ่มต้นของ EA รุ่น 1.07 คือ `240` และปรับได้ตั้งแต่ `20` ถึง `1000` แท่ง หน้า Deep Analysis ต้องได้รับอย่างน้อย **500 แท่งปิดจริง** เพื่อคำนวณ Indicator ก่อนแสดง 300 แท่งล่าสุด ส่วนสภา AI ปกติยังใช้จำนวนแท่งที่เลือกไว้ใน HQ เช่น 120 แท่ง การเพิ่มข้อมูลต้นทางไม่เปลี่ยนค่านี้

สำหรับการใช้งาน Deep Analysis ให้ตั้ง `SnapshotBars = 1000` บน EA ตัวเดิม:

1. ตรวจว่าเลือก MT5, Channel, Symbol และ Timeframe ตรงกับสภา AI ใน HQ
2. เปิด Properties ของ `MetafxHQTradeGateway` ที่ติดอยู่บนกราฟนั้น แล้วเปิดแท็บ Inputs
3. เปลี่ยนเฉพาะ `SnapshotBars` เป็น `1000` และยืนยัน โดยคงค่า Channel, โหมด, LiveArmed, SingleHostLiveAcknowledged, Signing Key ID และค่า Risk ทุกช่องตามเดิม ห้ามใช้ Reset หรือโหลด Preset ทับการตั้งค่าอื่น
4. รอ Snapshot รอบใหม่และตรวจจำนวนแท่งที่ส่งมาจริง หาก MT5 ยังโหลดประวัติไม่ครบ ระบบจะยังแจ้งข้อมูลไม่พอ ไม่เติมแท่งจำลองและไม่ลดเกณฑ์ 500 แท่ง
5. ตรวจ Deep Analysis ว่า `sourceBarCount >= 500`, `analysisBarCount = 300`, `closedBarsOnly = true` และเวลา/OHLC ของแท่งสุดท้ายตรงกับ Snapshot จาก MT5; ข้อมูล 1000 แท่งจะใช้ 700 แท่งก่อนหน้าสำหรับคำนวณ Indicator

การอ่านข้อมูลใช้ `CopyRates` เริ่มที่ตำแหน่ง 1 จึงไม่รวมแท่งปัจจุบันที่ยังเปิดอยู่ และส่งเฉพาะจำนวนแท่งที่ MT5 คืนมาจริง ปรับจำนวนแท่งผ่าน Input ได้กับ Binary เดิม ไม่ต้อง Compile ใหม่ การอัปเดต Source หรือ HQ จะไม่เปลี่ยน Inputs ของ EA ที่ติดกราฟไว้แล้วโดยอัตโนมัติ

การเพิ่มประวัติราคาไม่ได้เปิดสิทธิ์ส่งคำสั่งเทรดหรือแก้ Risk Guard ของ EA และไม่ได้เปลี่ยน Symbol/Timeframe ให้เอง

## ขั้นตอนเปิด Single-host Live

เปิด Live หลังจาก Demo ผ่านแล้วเท่านั้น และต้องครบทุกข้อดังนี้

1. ตรวจว่า Dashboard เลือก MT5 Terminal/Channel ที่ต้องการเพียงตัวเดียว และ Login + Server ตรงกับบัญชีจริงที่จะใช้
2. ใช้บัญชี MT5 แบบ **Real + Hedging** เท่านั้น เปิด Algo Trading และอนุญาต EA ให้เทรด
3. ตั้ง `GatewayMode = GATEWAY_LIVE`
4. ใส่ชื่อ Symbol เต็มที่ MT5 แสดงในกราฟปัจจุบันเป็น token ตรงตัวใน `AllowedSymbols` รวม prefix/suffix ของโบรกเกอร์ทุกตัวอักษร
5. ตรวจ `RiskPercent`, `MaxLossPerTradePercent`, SL และ slippage ว่าตรงงบความเสี่ยงจากราคา; งบนี้ไม่รวมค่าคอมมิชชันและสอง Inputs ค่าธรรมเนียมเดิมไม่ใช้เป็นเงื่อนไขเปิด LIVE
6. ตั้ง `TrustedSigningKeyId` เป็น Key ID ที่ Local Runner ใช้อยู่จริง ห้ามเว้นว่าง และต้องผ่าน HMAC verification
7. ตั้ง `LiveArmed = true`
8. อ่านข้อจำกัด Single-host ด้านบน แล้วตั้ง `SingleHostLiveAcknowledged = true` เฉพาะเมื่อยืนยันว่าจะไม่รันบัญชีเดียวกันบน Windows user/เครื่อง/VPS อื่น
9. ตรวจข้อความบนกราฟให้เป็น `Live Owner Lock: ready`, `Risk Guard: READY` และยืนยันว่าแสดง `Cross-VPS Distributed Lock: false` ก่อนเริ่ม

หากขาด Real account, exact Symbol allowlist, `LiveArmed`, acknowledgement, signing pin/HMAC, heartbeat, owner lock หรือ Risk Guard อื่น ๆ EA จะ fail-closed และไม่เรียก `OrderSend`

การเลือก Terminal ใหม่ที่ Backend จะต้องทำเมื่อไม่มีคำสั่งค้าง/สถานะไม่แน่นอน/Position ที่ระบบดูแลอยู่เท่านั้น แต่ account-owner lock รุ่นนี้ครอบคลุมเฉพาะ Local Gateway ที่รองรับ lock ภายใต้ Windows user และ host เดียว ไม่ได้พิสูจน์ความเป็นเจ้าของข้าม VPS

## หลักฐานการส่งคำสั่ง

ก่อนส่งคำสั่ง EA จะทำ `OrderCheck` กับ `MqlTradeRequest` จริง โดยผลตรวจที่ผ่านต้องมี `MqlTradeCheckResult.retcode == 0` ตามสัญญาของ MQL5 จากนั้น `OrderSend` ต้องได้ `TRADE_RETCODE_DONE` และ EA ต้องตรวจพบทั้ง Deal และ Position ที่ตรงกันทุกช่อง ได้แก่ Symbol, action, Lot ที่เลือกไว้สำหรับคำสั่งนั้น, MagicNumber, comment, SL, TP และ `DEAL_POSITION_ID/POSITION_IDENTIFIER` จึงจะตอบ `EXECUTED` ได้

`OrderSend()` ที่คืนค่า `true` เพียงอย่างเดียวไม่ถือว่าสำเร็จ, `TRADE_RETCODE_DONE_PARTIAL` และ `TRADE_RETCODE_PLACED` ไม่ถูกยกระดับเป็น `EXECUTED`

`ORDER_VERIFIED_OPEN` หมายถึงตรวจพบ Order ที่เปิดแล้ว ส่วนรหัส `ORDER_VERIFIED_OPEN_*` ที่มีคำเตือนความเสี่ยงหรือ Slippage หมายถึงเปิดแล้วแต่ค่าหลัง Fill เกินค่าประมาณหรือยังตรวจไม่ได้ ไม่ใช่การปฏิเสธก่อนส่งและไม่ใช่เหตุให้ส่งซ้ำ `RECOVERED_ORDER_FOUND` / `EXECUTION_RECONCILED_WITH_WARNING` ให้ตรวจ Position หรือประวัติ Broker และข้อมูลที่ยังไม่ทราบต่อไป คำเตือนเหล่านี้ไม่แก้สิทธิ์ execution หรือสั่งปิด Position เอง

`estimatedRiskMoney` ของคำสั่งใหม่เป็นค่าประมาณถึง SL จากราคาและ slippage โดยไม่รวมค่าคอมมิชชัน ไม่ใช่การรับประกันขาดทุนสุทธิสูงสุดจริง เพราะราคา Gap, Slippage ที่มากกว่าค่าที่เผื่อไว้, Swap และค่าธรรมเนียมจริงอาจทำให้ผลขาดทุนจริงสูงกว่าได้ ประวัติและ guard ผลขาดทุนรวมยังนับค่าธรรมเนียมจริง ต้องทดลองบน Demo ก่อน Live เสมอ

## Ticket, ACK เดิม และสถานะ OPEN/CLOSED ในรุ่น 1.07

MT5 ใช้ Ticket แบบ unsigned 64-bit ตั้งแต่ `1` ถึง `18446744073709551615` ใน ACK และ outcome ไม่ตัดเหลือ signed 32-bit ฝั่ง MT4 ยังคงขอบเขตเดิม Backend ส่ง `ticketText` เป็นข้อความเลขฐานสิบครบถ้วนให้ HQ จับคู่และแสดงผล จึงไม่เสียความแม่นยำเมื่อ Ticket มากกว่าขอบเขต integer ที่ JavaScript แสดงเป็น Number ได้ตรงทุกหลัก

หากคำสั่งเก่าค้าง `invalid_ack_ticket` หรือ `expired_waiting_ack` ให้ตรวจ ACK เดิมกับ Command, Channel, Account binding และประวัติ Broker ที่ตรงกัน การรับ ACK เดิมหลังแก้ตัวอ่าน Ticket เป็นการยืนยันผลเดิม ไม่สร้างหรือส่ง Command ซ้ำ TTL ที่หมดอายุไม่ปล่อยคิวเอง; `single_outstanding_command` ยังคงหยุดคำสั่งใหม่จนมี terminal ACK ที่บันทึกและตรวจสอบได้ ห้ามลบ ledger หรือคัดลอก ACK ข้ามบัญชีเพื่อปลดคิว

EA รีเฟรช outcome แบบอ่านสถานะ Position และประวัติ Deal โดยไม่เรียก `OrderSend` และไม่เขียนทับ ACK เปิดเดิม Archive ใน `processed/outcome-commands` เก็บเฉพาะ Command เดิมที่ลงลายเซ็นและผ่านการตรวจ Account/Channel/Stream/Digest กับหลักฐาน EXECUTED ที่ตรงกัน เพื่ออ่านผลต่อได้แม้คิวหลักเปลี่ยนเป็น Command ถัดไป การอ่าน archive จำกัดรอบละ 8 รายการทุก 5 วินาที และตรวจใหม่เมื่อบัญชี หลักฐาน หรือไฟล์เปลี่ยน

HQ แสดง OPEN เมื่อ outcome ที่ตรงตัวตนยังสด และ CLOSED เมื่อพบผลปิดที่ตรงตัวตน หากไม่พบหลักฐานล่าสุดจะแสดงว่าไม่ทราบสถานะ ไม่เดา CLOSED จากการที่ Position หายไป และไม่เดา OPEN จาก `READY`, ผลโหวต SELL หรือการเข้าคิว คำสั่งค้างแสดงแยกจากรายการ Order ที่ยืนยันแล้ว

Outcome เดิมที่ไม่มีรายละเอียดต้นทุนยังอ่านได้ รุ่นใหม่เพิ่มกลุ่ม optional 5 ช่องพร้อมกัน: `closePrice` (ราคาออกเฉลี่ยถ่วงน้ำหนัก), `grossProfit`, `commission`, `swap`, `fee` เมื่อ OPEN ช่องเหล่านี้เป็น null; เมื่อ CLOSED ต้องเป็นค่าตัวเลขที่ตรวจสอบได้ครบทั้งกลุ่ม `closedPnl` เป็นผลสุทธิรวมต้นทุนจริง ไม่เปลี่ยน ACK เปิดเดิม ถ้าหลักฐานเก่าไม่มีช่องเหล่านี้ HQ จะแจ้งว่าไม่มีรายละเอียดต้นทุน ไม่เติมเป็นศูนย์

## เมื่อ EA ติดกราฟแต่เริ่มทำงานไม่ผ่าน

ตั้งแต่รุ่น 1.04 การไม่ผ่าน guard ใน `OnInit` จะคง EA บนกราฟในสถานะ **ATTACHED / BLOCKED** พร้อม Stage, Reason และคำแนะนำว่าต้องตรวจ Input ใด เช่น `LIVE_SIGNING_KEY_PIN_REQUIRED` ให้ตรวจ Key ID ที่ผูกกับ Local Runner รุ่น 1.05 ไม่สร้าง error เรื่องการยืนยันค่าคอมมิชชันอีกต่อไป การที่ EA ยังติดกราฟไม่ได้แปลว่าพร้อมเทรด

- สถานะ blocked ไม่อ่านหรือประมวลผลคำสั่ง ไม่เขียน ACK/ledger ไม่กู้คืน execution attempt และไม่เรียก `OrderSend` ทุกช่องทางมีตัวล็อก initialization แยกจาก risk cache
- มีเฉพาะ diagnostic ที่รีเฟรชได้ทุก 5 วินาทีโดยไม่เขียน audit ซ้ำทุกครั้ง; ไม่เผยแพร่ Snapshot, Status หรือ Capabilities ปกติ ข้อมูล `eaAttached=true` / `runtimeReady=false` ใช้อธิบายสถานะเท่านั้น ไม่ให้สิทธิ์เทรด โดย `returnCode` เก็บรหัสสาเหตุ init ที่ไม่ผ่าน แม้ `OnInit` คืนสำเร็จเพื่อรักษาหน้าจอ diagnostic
- EA ต้องถือ channel lock ก่อนเขียน diagnostic หรือลบ publication เก่าของตัวเอง หาก Channel ไม่ถูกต้องหรือมีตัวอื่นเป็นเจ้าของ จะแสดงบนกราฟอย่างเดียวและไม่แตะไฟล์ของเจ้าของเดิม ระหว่าง blocked จะปล่อย account-execution lock, live-owner lock และ portfolio lease ที่ตัวเองถือไว้ โดยคง channel lock สำหรับ diagnostic
- หากเริ่ม timer ไม่ได้ ข้อผิดพลาดยังแสดงบนกราฟ ไม่มีการลองเปิด runtime เอง เมื่อถอด EA ที่ blocked จะบันทึก `eaAttached=false` / `runtimeReady=false` เฉพาะ channel ที่ตัวเองถืออยู่ก่อนปล่อย lock
- แก้ค่าตามสาเหตุแล้วเปิด Inputs และกด OK เพื่อเริ่มตรวจใหม่ทุกด่าน; timer ไม่เปลี่ยนจาก blocked เป็นพร้อมเอง ห้ามลบ policy, lock หรือ execution-history files เพื่อข้ามข้อผิดพลาด
- ระหว่าง initialization ตัวที่ถือ channel lock และยังไม่ blocked อ่าน telemetry เพื่อสร้าง Snapshot แรกได้ แต่ยังไม่ให้สิทธิ์ execution รวมถึงเมื่อใช้ risk cache; ต้องเผยแพร่ Snapshot, Capabilities และ Status สำเร็จครบก่อนตั้งตัวล็อกพร้อม แล้ว timer รอบถัดไปจึงอัปเดต readiness ปกติ Guard ด้านบัญชี, signing, Symbol, risk, heartbeat และ kill switch ยังคงเดิม

## การ Compile และหลักฐาน

เปิด MetaEditor 5 จาก MT5 ที่ต้องการใช้งาน เปิดไฟล์ `MetafxHQTradeGateway.mq5` จากโฟลเดอร์ `MQL5\Experts\Metafxclub\TradeGateway` แล้วกด **Compile** จากนั้นตรวจผลใน Toolbox ว่าไม่มี Error หรือ Warning ก่อนนำ EA ไปวางบนกราฟ

หลักฐานเดิมของรุ่น 1.03: source SHA-256 `42CB8A410DDE98E608307C12FC272513ED30F1E23F5B3267F7DCDF128A69175C` ผ่าน Visible Compile ด้วย MetaEditor64 `5.0.0.6230` ผล `0 errors, 0 warnings` ภายใน 9358 ms บน `AVX2+FMA3` หลักฐานอยู่ที่ `artifacts/mt5-trade-gateway-v1.03-visible-compile-readiness/` ซึ่งไม่ใช่หลักฐาน compile ของ source รุ่น 1.04

หลักฐานรุ่น 1.04 คงอยู่ที่ `artifacts/mt5-trade-gateway-v1.04-visible-compile-readiness/` สำหรับ Source SHA-256 `21BD0EAE671740B67590BE0CD188FBF6649EA154CCE2E1E8E46A27A21F2FC946` เท่านั้น ไม่ใช่หลักฐานของ 1.05

หลักฐานรุ่น 1.05 คงอยู่ที่ `artifacts/mt5-trade-gateway-v1.05-visible-compile-readiness/` เป็นหลักฐานย้อนหลังของรุ่นนั้น ไม่ใช้แทนการตรวจรุ่น 1.06

หลักฐานรุ่น 1.06 คงอยู่ที่ `artifacts/mt5-trade-gateway-v1.06-visible-compile-readiness/` สำหรับการตรวจย้อนหลัง ไม่ใช้ยืนยัน source รุ่น 1.07

รุ่น 1.07 ต้องตรวจหลักฐานที่ `artifacts/mt5-trade-gateway-v1.07-visible-compile-readiness/` ให้ Source/Binary hash ตรงกับไฟล์ที่จะใช้ก่อนติดกราฟ การระบุ path นี้ การเปลี่ยนหมายเลขรุ่น หรือผ่าน harness tests ไม่ถือเป็นหลักฐานว่า MetaEditor compile ผ่าน ต้องมีผล Compile จริงและ Manifest ที่ตรงกันก่อนใช้งาน Release ยังคงเป็นแบบ Source-only และไม่บรรจุ `.ex5`

ผล Compile เป็นเพียง `compile_verified` ยังไม่ใช่หลักฐานว่าได้ส่งคำสั่งจริงบนบัญชี Demo หรือ Live ต้องทดสอบแบบมองเห็นได้บน MT5 Demo อีกครั้งก่อนใช้งานเงินจริง และระบบนี้ไม่ใช่การรับประกันผลกำไร
