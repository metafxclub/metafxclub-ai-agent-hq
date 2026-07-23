# ความปลอดภัยของ Metafxclub AI Agent HQ

โปรเจกต์นี้ออกแบบให้หน้าเว็บส่งเฉพาะคำสั่งเชิงเจตนาไปยัง Local Bridge เท่านั้น หน้าเว็บต้องไม่เก็บ Token, API key, Cookie, รหัสผ่านโบรกเกอร์ หรือข้อมูลยืนยันตัวตนทุกชนิด

## หลักการสำคัญ

- Local Bridge เปิดรับเฉพาะ `127.0.0.1` เท่านั้น ตัวติดตั้งเสนอ Port ว่างให้ผู้ใช้ยืนยันก่อน และห้ามเปลี่ยน URL แบบเงียบหรือเปิดเป็น LAN/Public Port
- Agent Chat เรียก Codex เพื่อสนทนาและจำแนกคำขอแบบแยกบทบาท โดยตัว Chat ห้ามเปิด Tool, Shell, Computer Use, Browser, Plugin หรือ MCP หากผลเป็น `task_request` Backend เท่านั้นที่สร้าง Mission แบบ Idempotent จากเป้าหมายงานที่ผ่านการตรวจ
- งานที่เรียก Codex Task, MCP, Plugin หรือเครื่องมือจริง ต้องมี Mission ID, เจ้าของงาน, งบประมาณ, Audit log และ Report
- โหมด `อัตโนมัติ — Full Access ใน Workspace` ใช้ `workspace-write` เฉพาะภายใน `PROJECT_ROOT` งานต้องอยู่ใน Allowlist ผ่าน Backend Risk Guard และมีสิทธิ์แบบผูกกับ Digest ของ Mission เพียงครั้งเดียว
- Full Access ไม่ได้ใช้ `danger-full-access` และไม่อนุญาตให้ข้าม Sandbox, Approval Gate หรือกฎใน `AGENTS.md`
- งานทั่วไปที่ผ่านเกณฑ์อัตโนมัติไม่ต้องให้ผู้ใช้กดอนุมัติทีละงาน ส่วนงานเสี่ยงยังต้องผ่าน Approval ตามระดับความเสี่ยง
- Live trading, การส่ง Telegram จริง, การลบไฟล์, การ Deploy และการใช้เงินจริง ต้องผ่าน Risk Guard และการอนุมัติจากผู้ใช้
- เริ่มต้นด้วย Demo หรือ Read-only เสมอ และไม่มีการรับประกันผลกำไร
- ผู้ติดตั้งต้องเข้าสู่ระบบ Codex ด้วยบัญชีของตนเอง ระบบนี้ไม่รวมและไม่แจกข้อมูลล็อกอินของผู้พัฒนา
- การตรวจ Rate Limit อ่านผ่าน Backend แบบ Allowlist เท่านั้น แสดงเฉพาะสถานะ เปอร์เซ็นต์ และเวลารีเซ็ต โดยไม่เก็บชื่อบัญชี Token, Cookie หรือ Auth

## ก่อน Commit หรือแจกไฟล์

ตรวจว่าไม่มี `.env`, `.codex`, `auth.json`, `config.toml`, `runner/.venv`, `data/runtime`, `data/memory` หรือไฟล์ Credential อยู่ในชุดแจก

หากพบช่องโหว่หรือข้อมูลลับ ให้หยุดเผยแพร่และติดต่อเจ้าของโปรเจกต์โดยตรง ไม่ควรเปิดเผย Secret ผ่าน Issue สาธารณะ
