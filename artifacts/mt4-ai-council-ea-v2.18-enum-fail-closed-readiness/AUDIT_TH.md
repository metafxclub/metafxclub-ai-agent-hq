# รายงานตรวจรับ MetafxHQTradeGateway v2.20

ตรวจวันที่24ตุลาคม2569: Source/EX4ตรงชุดที่ตรวจแล้วและคอมไพล์ด้วย signed MetaEditor5.0.0.2425 ในโฟลเดอร์ audit แยก ได้0errors/0warnings/128ms ไม่ใช้ editor session ที่เปิดอยู่ ไม่มีการติด EA/เปิดterminal/เปลี่ยนบัญชีหรือส่งคำสั่งเทรด ตัวเลขhashและขนาดจริงอยู่ในMANIFEST.jsonและBUILD_LOG.txt

แก้ P1 ownership: instance ที่แย่ง channel ไม่ได้ไม่สามารถลบ status/capabilities/snapshot หรือเขียนทับ diagnostic ของเจ้าของเดิม Late initialization failureลบเฉพาะpublicationของตัวเองขณะยังถือlockก่อนปล่อยownership

เพิ่ม resident initialization: EAคงติดกราฟแบบATTACHED/BLOCKEDพร้อมreasonเมื่อเริ่มไม่สำเร็จ ทุกexecution/lifecycle entry ถูกreadinesslatchปิดจนinitializationผ่านครบ guard ปัญหาชั่วคราวที่ระบุretryเฉพาะinitializationทุก10วินาที ไม่ retryออเดอร์หรือ replayงานเก่า เมื่อdisconnectล้างtick markerและต้องรอtickใหม่

ชุดauditแรกผ่าน13regressionใหม่+52legacy contracts และnativecompile; releaseนำ65legacy testsทั้งหมดมาปรับให้ตรวจInitializeGatewayแทนOnInit wrapper โดยคงassertionsเดิม และเพิ่มportable resident regression/proof checks ผลreleaseล่าสุด82/82ผ่าน (65legacyครบไม่มีskip +13resident +4compile-proof), 0failures/0errors/0skips; เป็นsource/proof contracts ไม่ใช่native account execution

COMPILE_LOG.logเป็นผลnativeจริงที่ลบเฉพาะabsolute source prefixของเครื่องauditแล้วแปลงเป็นUTF-8; manifestเก็บทั้งnativeLogSha256และpublic logSha256 ไม่มีการใช้ภาพcompileของ2.19มายืนยัน2.20 Process exit codeจริงเป็น1แม้logผ่าน จึงตรวจด้วยfreshEX4และlog/hashร่วมกัน

ไม่ได้ตรวจnativeattachment/demo/live execution: FILE_COMMONเป็นพื้นที่ร่วมทุกterminalของWindowsuserตามเอกสารMQL4 https://docs.mql4.com/files/fileopen การเปิดportableภายใต้userเดิมยังไม่พิสูจน์ว่าแยกnamespaceจากระบบจริงได้ จึงไม่launch/attachเพื่อทดสอบกับเครื่องที่มีออเดอร์ทำงานอยู่ Compile/source testsไม่ใช่คำรับรองbrokerหรือบัญชีจริงทุกประเภท

โฟลเดอร์artifactยังใช้ชื่อlegacy v2.18เพื่อรักษาcompatibilityของพาธติดตั้ง รุ่นจริงคือ2.20ตามsource/manifest/hash ไม่มีการเปิดLiveอัตโนมัติ เมื่อติดตั้งเครื่องใหม่ต้องเลือกterminalของตนและตรวจShadow/Demoกับbrokerเป้าหมายก่อนLive
