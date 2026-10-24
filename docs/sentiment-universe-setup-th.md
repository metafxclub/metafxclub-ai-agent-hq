# Sentiment Universe ใน AI Agent HQ

เอกสารนี้ประกอบ candidate สำหรับตรวจและทดสอบ ยังไม่ใช่การยืนยันว่า release ทางการบน GitHub ออกแล้ว การติดตั้งให้ลูกศิษย์ต้องใช้ release ใหม่ที่รวมไฟล์นี้และผ่าน CI/package gates ก่อน ไม่ควรใช้ prompt ของ tag เก่าแล้วคาดว่าจะได้ฟีเจอร์นี้

หน้ากาแล็กซีใช้บริการอ่านข้อมูลแยกจากสภา AI และตัวส่งออเดอร์ บริการนี้ไม่ส่งคำสั่งซื้อขาย ไม่เปลี่ยนบัญชี MT5 และไม่ใช้ Codex ในการดึง Myfxbook หรือคำนวณ correlation

## ติดตั้งครั้งแรก

1. ติดตั้งจาก release ที่ผ่านการตรวจไฟล์ตามขั้นตอน HQ ปกติ ตัวติดตั้งใช้ Python และ dependencies ที่ตรึงรุ่นไว้ของ HQ ไม่ต้องติดตั้ง Python เพิ่ม
2. ตัวติดตั้งเริ่มบริการบน `http://127.0.0.1:4197` หลัง HQ ผ่าน health check และสร้าง Task `Metafxclub Sentiment Universe` สำหรับ Windows user ปัจจุบันเท่านั้น หากพอร์ตถูกโปรแกรมอื่นใช้ ระบบจะแจ้งปัญหาโดยไม่ปิดโปรแกรมนั้น
3. ตัวติดตั้งเปิด `http://127.0.0.1:4197/connect` ให้อัตโนมัติเมื่อยังไม่มีบัญชี Myfxbook ที่เก็บเข้ารหัส หรือยังไม่ได้เลือก MT5 ให้เชื่อมด้วยบัญชีของผู้เรียนเองและเลือก MT5 ที่เปิดอยู่สำหรับอ่านแท่งราคาและ correlation หากเคยตั้งครบแล้วจะใช้ข้อมูลเดิมต่อและไม่เปิดหน้าตั้งค่าซ้ำ ไม่มีการแนบข้อมูลบัญชีของผู้สอนไปกับตัวติดตั้ง
4. ตรวจสถานะข้อมูลแต่ละแหล่งในหน้าเว็บ การเปิดหน้าได้และ service healthy ไม่ได้หมายความว่าทุก provider มีข้อมูลครบ

หลังตั้งค่าแล้ว service เริ่มเมื่อ login เข้า Windows และเปิด HQ อีกครั้งก็ตรวจ/เริ่ม service เดิมโดยไม่สร้างสำเนาซ้ำ Task ตรวจทุก 15 นาที ส่วน supervisor ดูแล worker แยกต่างหาก การเปิดหน้าเว็บไม่เป็นตัวกำหนดรอบดึงข้อมูล

คำสั่งสำหรับซ่อมเฉพาะส่วนนี้จากโฟลเดอร์ HQ:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-sentiment-universe.ps1 -OpenSetup
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\sentiment-universe.ps1 -Action Status
```

คำสั่ง setup ไม่รีสตาร์ต HQ หรือ MT5 และไม่แตะออเดอร์ที่เปิดอยู่ `-SkipAutostart` จะไม่เปิดใช้ Task นี้ และยกเลิก Task เดิมเฉพาะเมื่อยืนยันได้ว่าเป็นของแพ็กเกจนี้ `-SkipLaunch` ของตัวติดตั้งจะไม่เริ่ม collector หรือ provider ส่วน package smoke ใช้การตรวจและบริการจำลองเท่านั้น

## แหล่งข้อมูลและความถี่

- Myfxbook: ต้องเชื่อมบัญชีส่วนตัว สถานะข้อมูลและเวลาสำเร็จล่าสุดเป็นของ provider จริง สินทรัพย์ที่ provider ไม่มีจะไม่สร้างเปอร์เซ็นต์ขึ้นมาแทน
- Correlation: คำนวณจากผลตอบแทนของแท่งราคาที่ปิดแล้วและมีเวลาเดียวกันจาก MT5 บนเครื่อง สัญลักษณ์ที่โบรกเกอร์ไม่มีหรือมีข้อมูลไม่พอจะแสดงไม่พร้อม ไม่สั่งเปิด terminal หรือสลับบัญชีเพื่อเติมข้อมูล
- ข่าว: snapshot ปฏิทินจาก official Forex Factory export ดึงตามวันไทย พร้อม cache และ backoff บริการเก็บหลายข่าวเวลาเดียวกันและทุก impact ที่ feed มี ไม่แปลว่าเป็นข่าวทั้งหมดในโลก ปฏิทินนี้ไม่มี actual จึงไม่อ้างว่าตรวจผลประกาศแล้ว การอธิบายผลต่ำกว่า/เท่ากับ/สูงกว่าคาดเป็นเงื่อนไข ไม่รับประกันทิศทางราคา
- รอบข่าวสำเร็จวันละครั้งตาม Asia/Bangkok; ถ้า source ยังไม่ครอบคลุมวันใหม่หรือเกิด HTTP 429 จะเว้นช่วงอย่างน้อย 30 นาที และเคารพ Retry-After เก็บผลสำเร็จเดิมพร้อมสถานะ stale ระหว่างรอ ไม่มีการล้างข้อจำกัด provider ด้วยการรีสตาร์ต
- ข้อมูลราคาปิดและรอบต่าง ๆ ไม่จำเป็นต้องเปลี่ยนในวันหยุดตลาด วันที่ไม่มีข่าวใน feed เป็นสถานะว่างที่ถูกต้องเมื่อ coverage ครอบคลุมวันนั้น

UI แสดง `needs_configuration`, `stale`, `rate_limited`, `not_covered` หรือแหล่งข้อมูลขาดตามสภาพจริง การอนุญาตใช้/เผยแพร่ข้อมูล Myfxbook และ Forex Factory แก่นักเรียนต้องตรวจเงื่อนไขของผู้ให้บริการก่อนปล่อยใช้งานวงกว้าง การมี export สาธารณะไม่ใช่การรับรองสิทธิ์แจกจ่ายต่อ

## ข้อมูลส่วนตัวและอัปเดต

ข้อมูลส่วนตัวอยู่ที่ `%LOCALAPPDATA%\Metafxclub\SentimentUniverse` แยกจากไฟล์โปรแกรม รวมถึง DPAPI ของ Windows user, provider rate limits, cache และประวัติความสำเร็จ การอัปเดตจะเก็บข้อมูลนี้ไว้ ไม่คัดลอกไปให้ผู้ใช้รายอื่น

ไฟล์ public `frontend/public/sentiment-universe/market.json` เป็นข้อมูลสำหรับแสดงผลเท่านั้น backend เป็นผู้เขียน snapshot ที่กรองข้อมูลลับแล้ว ไม่วาง private state ใต้ static root แพ็กเกจ release ต้องไม่มี market snapshot จากเครื่องผู้สอน, DPAPI, log หรือไฟล์ cache ของผู้ใช้

ตัวถอนติดตั้งหยุดเฉพาะ sentiment supervisor/worker ที่พิสูจน์ command line ได้ และยกเลิก Task ของตัวเอง โดยเก็บ `%LOCALAPPDATA%\Metafxclub\SentimentUniverse` ไว้ รวมถึงเมื่อถอนข้อมูล HQ ด้วย `-RemoveUserData`; เมื่อติดตั้งกลับใน Windows user เดิมสามารถใช้บัญชีเดิมต่อได้ หากต้องการลบข้อมูล sentiment ให้หยุด service ก่อนและลบโฟลเดอร์ส่วนตัวนี้ด้วยตนเองหลังตรวจ path ให้ถูกต้อง

## ย้ายจาก prototype เดิม

ให้หยุด prototype ตาม PID และ command line ที่ตรวจแล้วก่อนเริ่มของ HQ จากนั้น setup รับ path เดิมที่แน่นอนเพื่อลบเฉพาะ Startup shortcut ที่ตรงกัน:

```powershell
.\scripts\setup-sentiment-universe.ps1 -LegacyLauncherPath 'C:\exact-old-project\scripts\start-live.py' -LegacyPythonPath 'C:\exact-python\pythonw.exe'
```

จะลบเฉพาะ `Metafxclub Sentiment Universe.lnk` ที่ target และ arguments ตรงทั้งสองค่า หลัง Task ใหม่ลงทะเบียนผ่านแล้ว Shortcut อื่นหรือ target ไม่ตรงจะถูกเก็บไว้ ไม่มีการค้นหาแล้วปิดทุก process ชื่อ Python

## ตรวจแพ็กเกจก่อนปล่อย

- ใช้ `tests.test_sentiment_package` ตรวจ inventory ทุกขอบเขต, static dependencies และการไม่แถม private state
- ใช้ `tests.test_sentiment_lifecycle` ทดสอบใน temporary directory บน Windows: start ซ้ำไม่เกิด process ซ้ำ, stop ทั้ง supervisor/worker, พอร์ตคนอื่นไม่ถูกแตะ, PID ปลอมไม่ถูกปิด และข้อมูลส่วนตัวไม่เปลี่ยน
- package smoke ต้องไม่เรียก Myfxbook/Forex Factory/MT5 จริง และไม่ลงทะเบียน Task ของผู้ใช้

อ้างอิง: [Myfxbook API](https://www.myfxbook.com/api), [Forex Factory Calendar](https://www.forexfactory.com/calendar), [Forex Factory notices](https://www.forexfactory.com/notices), [MetaTrader5 Python](https://www.mql5.com/en/docs/python_metatrader5)
