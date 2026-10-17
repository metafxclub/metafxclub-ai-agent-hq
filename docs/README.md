# คู่มือและเอกสารของ Metafxclub AI Agent HQ

เริ่มจาก [คู่มือผู้เรียน](../STUDENT-QUICKSTART-TH.md) สำหรับการติดตั้งและใช้งาน หรือ [README ของโปรเจกต์](../README.md) สำหรับภาพรวมและโครงสร้าง Source

## เอกสารที่ใช้งานปัจจุบัน

| งาน | เอกสาร |
|---|---|
| บทบาท Agent และขอบเขตการทำงาน | [Agent Bible](01-agent-bible.md) |
| Workflow ของอุปกรณ์และการส่งงาน | [Equipment Workflows](equipment-workflows-v1-th.md) |
| Manager แจกงานอ่านอย่างเดียวพร้อมกัน 3 Agent | [Manager Parallel Missions](manager-parallel-missions.md) |
| Manager วิเคราะห์ข้อมูล Radar แยกบทบาทและอ้างอิงตรงต้นฉบับ | [Manager Source Analysis](manager-source-analysis.md) |
| ตั้งค่าและใช้งาน Google Sheet กลาง | [Research Sheet Hub](research-sheet-hub-setup-th.md) |
| ข้อมูลที่ใช้วิเคราะห์ในสภา AI Trade | [AI Trade Deep Analysis](ai-trade-deep-analysis-300-th.md) |
| Prompt ติดตั้งที่ล็อก GitHub Release | [ติดตั้ง GitHub + Google OAuth](prompts/install-github-google-auto-th.md) |
| การเปิด ปิด และตรวจสถานะ Local Bridge | [Bridge Lifecycle](../scripts/README-bridge-lifecycle.md) |

ไฟล์ภายใน `prompts/` เป็น Prompt สำหรับขั้นตอนที่ระบุในแต่ละไฟล์ เส้นทางคู่มือที่ Installer และ Prompt อ้างอิงยังคงเดิม

## ประวัติการพัฒนา

เอกสารใน `history/` บันทึกผลตรวจและข้อจำกัด ณ วันที่จัดทำ จึงไม่ใช่การยืนยันสถานะ Runtime ปัจจุบัน

- [Permanent Runtime Hardening — 2026-07-14](history/permanent-runtime-hardening-2026-07-14.md)
- [Visual Office Safe-Demo Completion — 2026-07-15](history/visual-office-safe-demo-completion-2026-07-15.md)
- [System Audit — 2026-08-08](history/system-audit-20260808-th.md)
- [Design QA — ห้องแชต AI รวม](history/design-qa-ai-chat.md)

หลักฐาน Compile และ Release ที่กำหนดไว้ใน `artifacts/` ต้องรักษาไฟล์และ Checksum เดิม ส่วนภาพ QA, Log และข้อมูลจากเครื่องผู้ใช้ไม่ใช่ Source สำหรับแจกจ่าย
