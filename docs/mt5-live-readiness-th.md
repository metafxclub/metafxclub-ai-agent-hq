# ตรวจความพร้อม MT5 ก่อนเปิด LIVE

ตารางและค่าด้านล่างเป็นบันทึกการตรวจวันที่ 21 ตุลาคม 2026 ซึ่งขณะนั้นเป็น SHADOW ไม่ใช่สถานะ Runtime ปัจจุบัน งานตรวจครั้งนั้นไม่ได้เปิด LIVE หรือส่งคำสั่งซื้อขาย ให้ตรวจ Inputs และสถานะสดก่อนเปลี่ยนทุกครั้ง การ Compile ผ่านและผ่าน regression tests เป็นหลักฐานตามขอบเขตที่ทดสอบ ไม่ใช่คำรับรองว่าปราศจากข้อบกพร่องทุกกรณีหรือจะไม่ขาดทุน

## สี่ค่าที่ยังปิดการเทรดจริงไว้โดยตั้งใจ

| Input | ค่าที่ตรวจไว้ | สิ่งที่เจ้าของบัญชีต้องยืนยันก่อนเปลี่ยน |
| --- | --- | --- |
| `GatewayMode` | `GATEWAY_SHADOW` | บัญชี Real แบบ Hedging, Channel, Symbol และ Timeframe ตรงกับ HQ |
| `LiveArmed` | `false` | ตรวจความพร้อมและความเสี่ยงครบก่อนเปิดเป็นขั้นสุดท้าย |
| `SingleHostLiveAcknowledged` | `false` | บัญชีเดียวกันไม่ได้รัน Gateway บน Windows user, เครื่อง หรือ VPS อื่น |
| `TrustedSigningKeyId` | ว่าง | คัดลอก Key ID ที่ HQ แสดงสำหรับ Terminal นี้ไปยัง EA ให้ตรงกัน; Key ID เป็น metadata ไม่ใช่ secret ห้ามคัดลอกหรือเปิดเผยเนื้อหา signing key |

เปลี่ยนค่าเฉพาะเมื่อเจ้าของบัญชีตั้งใจเปิด LIVE แล้วเท่านั้น ห้ามใช้ Reset หรือโหลด preset ทับ Inputs เดิม การเปลี่ยน Inputs ทำให้ EA ตรวจ initialization ใหม่ทุกด่าน; หากยังไม่ผ่านให้แก้สาเหตุ ไม่ลบ lock, policy หรือ execution-history files เพื่อข้าม guard

ค่าที่ตรวจไว้ใช้ **Fixed Lot 0.01** พร้อมเพดานความเสี่ยงต่อรายการ **1% ของ Balance** จาก `MaxLossPerTradePercent` ซึ่งเป็น hard cap ที่บังคับทุกโหมด หาก Lot 0.01 กับระยะ SL และ slippage reserve เกินเพดาน EA จะปฏิเสธ

Input `RiskCapitalBase=EQUITY` (ค่า enum ในชุดตั้งค่าคือ `1`) และ `RiskPercent=1` มีอยู่จริง แต่ใช้กำหนดงบเป้าหมายเมื่อเลือกโหมด `MONEY_MANAGEMENT_RISK_PERCENT` เท่านั้น ในการตรวจครั้งนั้นใช้ Fixed Lot หากเลือก Risk Percent ด้วยค่าตัวอย่างนี้ งบคำนวณ Lot จะใช้ค่าที่ต่ำกว่าระหว่าง 1% ของ EQUITY กับ hard cap 1% ของ Balance ไม่ใช้ EQUITY มาแทนฐานของ hard cap

ค่าคอมมิชชันไม่รวมในงบนี้ตาม `riskCostBasis=price_and_slippage_excluding_commission` ซึ่งไม่ได้แปลว่าบัญชีไม่มีค่าธรรมเนียม ผลขาดทุนสุทธิอาจเกินงบจากค่าธรรมเนียม, Swap, Gap หรือ Slippage ที่เกิดจริง

Position ที่เปิดเองและไม่ได้อยู่ใน `ManagedMagicNumbers` ไม่ถือเป็น Position ที่ Gateway นี้ดูแล ต้องตรวจภาระรวมของบัญชีด้วยตนเอง รวมถึง Margin และ Position อื่น ไม่ควรถือว่าเพดานของ managed trades ครอบคลุมทุก Position ในบัญชี

## ก่อนเปิดและหลังเปิด

1. ตรวจ source/binary กับหลักฐาน Compile รุ่น 1.07 ที่ตรงกัน และทดสอบ Demo ตามคู่มือ Gateway ก่อนใช้งานเงินจริง ตรวจ Position เดิมและคำสั่งค้างให้ครบ หลักฐานรุ่น 1.06 เก็บไว้ตรวจย้อนหลังและไม่ใช้แทนรุ่นใหม่
2. ตรวจชื่อ Symbol เต็มใน `AllowedSymbols`, SL/TP, Fixed Lot, hard cap 1% ของ Balance และเพดาน Spread/Lot/Margin พร้อม Kill Switch, signed heartbeat และสิทธิ์ Algo Trading โดยคง guard ทุกตัว ส่วนฐาน EQUITY ที่ตั้งไว้ใช้เฉพาะเมื่อเลือกโหมด Risk Percent
3. คัดลอกเฉพาะ Key ID จาก HQ แล้วให้เจ้าของบัญชียืนยัน Single-host และเปิด `LiveArmed` เป็นขั้นสุดท้ายเมื่อพร้อมจริง การกดวิเคราะห์ manual เป็น read-only และไม่ใช้เป็นการอนุญาตส่ง Order
4. รอ Tick ใหม่ที่ EA ได้รับจริง ตรวจเวลา Broker, Snapshot และสถานะสดที่ตรง Candidate/Channel เดียวกัน `runtimeReady` และการเชื่อมต่ออย่างเดียวไม่แทน `executionGuardReady`; guard อาจกลับมาบล็อกได้ทุกเวลา
5. เมื่อต้องหยุดเปิดรายการใหม่ ให้กลับ `GatewayMode=GATEWAY_SHADOW`, `LiveArmed=false`, `SingleHostLiveAcknowledged=false` แล้วตรวจสถานะรอบใหม่ การกลับ SHADOW ไม่ได้ปิด Position ที่เปิดอยู่ ต้องตรวจ Position/SL/TP ที่ Broker แยกต่างหาก

## ข้อความที่อาจพบ

- `LIVE_NOT_ARMED` / `SINGLE_HOST_LIVE_ACK_REQUIRED`: ค่ายังปิดไว้โดยตั้งใจ ให้เจ้าของบัญชียืนยันก่อนเปลี่ยน
- `LIVE_SIGNING_KEY_PIN_REQUIRED` / `LIVE_SIGNING_KEY_NOT_PINNED` / `SIGNING_KEY_MISMATCH`: ตรวจ Key ID ให้ตรงกับ HQ ห้ามแก้ด้วยการข้ามการตรวจลายเซ็น
- `QUOTE_NOT_OBSERVED`: รอ Tick ใหม่หลังเริ่ม EA หรือเชื่อมต่อใหม่ ไม่ใช่ init ล้มเหลว; `QUOTE_STALE_OR_FUTURE`: ราคาเก่าหรือเวลาไม่ผ่าน ตรวจ Broker แล้วรอ Tick จริง การรีเฟรช HQ ไม่ต่ออายุราคา
- `LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE` / `PORTFOLIO_POLICY_CONFLICT`: ตรวจ Gateway อีกตัวและ policy ที่ใช้อยู่ ห้ามลบไฟล์เพื่อฝืนเปิด
- `ORDER_VERIFIED_OPEN`: EA ยืนยันการเปิดแล้ว ส่วน `ORDER_VERIFIED_OPEN_*` ที่เตือน Risk/Slippage คือเปิดแล้วแต่ต้องตรวจค่าหลัง Fill ไม่ใช่คำสั่งถูกบล็อกก่อนส่ง
- `RECOVERED_ORDER_FOUND` / `EXECUTION_RECONCILED_WITH_WARNING`: พบหลักฐานคำสั่งเดิมและไม่ส่งซ้ำ หาก `filledSlippageKnown=false` ให้คงเป็น “ไม่ทราบ” ห้ามถือว่า Slippage เป็นศูนย์
- `EXECUTION_UNKNOWN` / `PREVIOUS_COMMAND_UNRESOLVED`: ตรวจ ACK, Position และประวัติ Broker ก่อนทำรายการต่อ ห้ามส่งคำสั่งเดิมซ้ำเพื่อทดลอง
- `invalid_ack_ticket`: ตรวจ Ticket ใน ACK เดิมกับ Broker ให้ตรงกัน รุ่น 1.07 รองรับ MT5 unsigned 64-bit และ HQ ใช้ `ticketText` แสดงทุกหลัก การยืนยัน ACK เดิมไม่ส่งคำสั่งเทรดซ้ำ
- `expired_waiting_ack` / `single_outstanding_command`: คำสั่งเดิมยังไม่จบตามหลักฐาน Backend จึงหยุดคำสั่งใหม่ แม้คำสั่งเก่าหมดอายุแล้ว ห้ามลบ ledger เพื่อปลดคิว
- `signal_price_drift_exceeded_before_publish`: ราคาเคลื่อนไกลกว่าค่าที่อนุญาตระหว่างการวิเคราะห์ จึงไม่มี Command ส่งจากรอบนั้น ผลโหวต SELL ไม่ใช่หลักฐานว่าเปิด Order แล้ว

## ติดตาม Order เดิมหลังอัปเดต

รุ่น 1.07 อ่าน Position/Deal เพื่อรีเฟรช outcome ของ Command ที่ตรวจตัวตนแล้ว โดยไม่ส่ง Order ใหม่และไม่เขียนทับ ACK เปิดเดิม HQ แสดง OPEN/CLOSED จากผลตรวจจริง; ถ้าขาดหลักฐานล่าสุดจะแสดงไม่ทราบสถานะ และคำสั่งค้าง ACK แยกจาก Orders ที่ยืนยันแล้ว ต้องตรวจ Command, Channel, Account binding, Ticket และ Broker history ให้ตรงกันก่อนยืนยันผลเดิม

Outcome รองรับกลุ่ม optional `closePrice`, `grossProfit`, `commission`, `swap`, `fee` พร้อมกัน โดย `closedPnl` เป็นผลสุทธิจากต้นทุนจริง ถ้าหลักฐานเก่าไม่มีรายละเอียดกลุ่มนี้ให้คงเป็น “ไม่มีหลักฐาน” ไม่แทนค่าธรรมเนียมหรือ Swap ที่ไม่ทราบด้วยศูนย์ การอัปเดตไม่ได้เปลี่ยนโหมด Lot, Risk Percent หรือ Inputs เดิมโดยอัตโนมัติ

ดูรายละเอียด guard และข้อจำกัดได้ที่ [คู่มือ MT5 Gateway](../integrations/mt5-trade-gateway/README_TH.md)
