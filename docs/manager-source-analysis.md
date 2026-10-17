# Manager: วิเคราะห์รายงาน Radar แยกบทบาท

ส่งโจทย์ที่ระบุ `Read-only text-only: analyze report` หรือเจตนาวิเคราะห์รายงานแบบอ่านอย่างเดียว พร้อม `sourceReportId=...` และ `recordId=...` เต็มทุกตัวรวม suffix เช่น `-3` ผ่านหน้า Manager เดิมได้ API `POST /api/manager/delegate` รองรับ `sourceReference: {sourceReportId, recordId}` เพิ่มเติมเช่นกัน หากทั้งสองช่องทางระบุค่าไม่ตรงกันหรือขาดคู่ ระบบปฏิเสธก่อนสร้างงาน

ชื่อแหล่งข้อมูลในโจทย์เป็นเพียงตัวเลือก Backend อ่าน Report และตรวจ Mission ต้นทาง, receipt, รูปแบบ record และ ID ที่คำนวณได้ก่อนใช้ข้อมูลจริง ไม่ใช้ข้อเท็จจริงที่ผู้ใช้แปะเพิ่มเป็นข้อมูลอ้างอิงที่ตรวจแล้ว กรณี Report เก่าเก็บ receipt เป็น prefix 8,000 ตัวอักษร จะยอมรับเฉพาะเมื่อเป็นผล sanitize ตรงกับ receipt เต็มใน Mission และรายการ record ทั้งหมดตรงกันเท่านั้น ไม่มีการซ่อมหรือแก้ข้อมูลต้นทาง

ข้อมูลที่ `partially_verified` ใช้วิเคราะห์ข้อจำกัดได้ แต่ไม่ถูกเลื่อนเป็น `verified` หรือใช้แทนเกณฑ์ EA-ready ของห้องวิจัยเดิม

- Technical Consultant (`optimization_agent`, `technical`): สูตร ข้อมูล พารามิเตอร์ baseline และ overfit
- Price Action Consultant (`backtest_analyst`, `price_action`): setup/trigger ลำดับเข้าออก เวลา session และความกำกวมของราคา
- Risk Guard (`risk_guard`, `risk`): ทุน/exposure การจำกัดขาดทุน ต้นทุน/stress และเกณฑ์ตรวจรับ

แต่ละงานมี prompt เฉพาะบทบาทและข้อมูลอ้างอิงที่ตรึงไว้ใน `managerAnalysisContext` โดยผูกกับ authorization digest ของงาน Agent ไม่ได้รับคำสั่งให้ทำรายงานของเพื่อน และไม่มีสิทธิ์ใช้ Shell, Web, ไฟล์ หรือแอปภายนอก ผลลัพธ์ต้องตรง schema `manager-specialist-analysis-v1`: `ownerAgentId`, `roleId`, `sourceReference`, `summary`, `keyPoints`, `blockers`, `nextSteps` พร้อม `schemaVersion`

แต่ละ key point ระบุ topic เฉพาะบทบาท, `kind` เป็น `fact`, `inference` หรือ `unknown`, ข้อความ และ `evidenceIds` ที่มีอยู่จริงใน packet ข้อเท็จจริงต้องคัดลอกข้อความอ้างอิงตรงตัว ส่วนการตีความต้องระบุ inference การตรวจนี้ยืนยันโครงสร้างและการผูกหลักฐาน ไม่ใช่การรับประกันว่าข้ออนุมานถูกต้องทั้งหมด จึงยังต้องอ่านและตรวจผลก่อนนำไปพัฒนา

ผลที่ผิดบทบาท ผิด ID อ้างอิง ถูกตัด suffix อ้างหลักฐานที่ไม่มี หรือเกินขนาดที่กำหนด จะหยุดด้วยสถานะไม่สำเร็จ ไม่มีการเติมอ้างอิงให้เงียบ ๆ ไม่มีการเพิ่มงบหรือปิด Guard เพื่อให้ผ่าน

ที่โต๊ะ Mission ให้เปิด **รายงานสรุปรวม** ของ Mission แม่ รายงาน `managerSummary` รุ่น `manager-summary-v1` แสดงภาพรวมจากข้อสรุปครบของทุกบทบาท ตามด้วยประเด็น ข้อมูลที่ขาด และขั้นตอนถัดไปครบทุกข้อ รวม ID งานย่อย รายงาน และ source snapshot digest ภาพรวมประกอบด้วยกฎของ Backend จึงไม่อ้างว่า Manager เรียกโมเดลอีกครั้งเพื่อสังเคราะห์ การแสดงผลไม่ใช้การตัดคำตอบเหลือ 600 ตัวอักษร

ขนาดต่อ Agent: summary 1,600 ตัวอักษร, keyPoints 3–8 ข้อ ข้อละ 1,200 ตัวอักษร, blockers และ nextSteps อย่างละไม่เกิน 8 ข้อ โดยทั้ง JSON ยังต้องอยู่ภายใน output budget เดิมของ Mission ภาพรวมรวมไม่เกิน 6,000 ตัวอักษร และคงข้อความเต็มแยกแต่ละบทบาท

ทดสอบด้วย `python -m unittest tests.test_manager_source_analysis tests.test_manager_parallel_missions` รวมถึง regression suite ของ repository การแก้ Source นี้ไม่ใช่การอัปเดต Runtime ที่ติดตั้ง และไม่ใช่ Release หรือ Deploy
