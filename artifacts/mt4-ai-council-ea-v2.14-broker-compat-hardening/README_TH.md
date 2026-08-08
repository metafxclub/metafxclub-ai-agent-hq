# MetafxHQTradeGateway v2.14 — Broker Compatibility Hardening

ชุดนี้เป็นไฟล์แจกจ่ายที่ Compile แบบออฟไลน์จาก Source ใน Repository เดียวกัน เมื่อวันที่ 8 สิงหาคม 2569 โดย MetaEditor ของ RoboForex MT4

## ไฟล์และ SHA-256

| ไฟล์ | ขนาด | SHA-256 |
|---|---:|---|
| `MetafxHQTradeGateway.mq4` | 121,301 bytes | `80E891F5E459D1D996322C35263A61D3A0CF3CFB541E41C17665D7A62342E669` |
| `MetafxHQTradeGateway.ex4` | 267,440 bytes | `EF3994DDCDFAAD78AD8D22A2446CCD52215B084B9EF911083ED414F4CAD9F7D5` |

`MetafxHQTradeGateway.mq4` ในชุดนี้มี Hash ตรงกับ Source ล่าสุดที่ `integrations/mt4-trade-gateway/MetafxHQTradeGateway.mq4`

## ผล Compile

ผลจาก MetaEditor ที่บันทึกไว้ระหว่าง Build แสดงผลดังนี้ (ตัด Raw compile log ออกจากชุดแจกเพื่อไม่แนบ Path ของเครื่องผู้พัฒนา):

```text
Result: 0 errors, 0 warnings, 87 msec elapsed
```

ผลนี้ยืนยันความเป็นไปได้ในการ Compile เท่านั้น ยังไม่ใช่หลักฐานว่าได้ติดตั้งใน MT4 ที่ผู้ใช้เลือก หรือผ่านการส่งคำสั่งบน Broker จริง

## ก่อนทดสอบ

1. สำรอง EA รุ่นเดิมของ MT4 เป้าหมาย
2. วาง MQ4/EX4 คู่นี้ใน Data Folder ของ Terminal เดียวกัน
3. เปิด MetaEditor จาก MT4 เป้าหมายและ Compile แบบมองเห็นอีกครั้ง
4. เริ่มที่ `GATEWAY_SHADOW`
5. จากนั้นจึงทดสอบบัญชี Demo ด้วย `GATEWAY_DEMO` และ Lot ต่ำ
6. ห้ามใช้ Live จนกว่า Shadow/Demo, Key, Kill Switch, ACK/Fill และ Broker-specific rules ผ่านครบ
