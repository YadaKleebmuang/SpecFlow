# แหล่งอ้างอิงเนื้อหา FAQ เฟส 2

ตรวจเนื้อหาเมื่อ 2026-10-13 สำหรับข้อความใน `ActionFAQ` และ templates ใหม่ 6 ไฟล์
ข้อความภาษาไทยเรียบเรียงใหม่สำหรับคำอธิบายเบื้องต้น ไม่อ้างราคาหรือจัดอันดับผลิตภัณฑ์

| หมวด | ประเด็นที่ใช้ตรวจเนื้อหา | เอกสารผู้ผลิต |
|---|---|---|
| Mainboard | Socket อย่างเดียวไม่พอ ต้องตรวจ BIOS และ CPU support ของบอร์ด | [Intel: Package Type Guide](https://www.intel.com/content/www/us/en/support/articles/000005670/processors.html) |
| Storage | M.2 เป็นรูปแบบอุปกรณ์; มีทั้ง SATA และ NVMe และต้องตรวจการรองรับ | [Kingston: Two Types of M.2 SSDs](https://www.kingston.com/en/blog/pc-performance/two-types-m2-vs-ssd) |
| PSU | 80 PLUS เป็นระดับประสิทธิภาพการแปลงพลังงาน | [Corsair: Efficiency Ratings Explained](https://help.corsair.com/hc/en-us/articles/14641912717453-PSU-Efficiency-Ratings-Explained) |
| PSU | OVP, OCP และ SCP เป็นระบบป้องกันคนละประเภท ต้องตรวจตามรุ่น | [Corsair: PSU Protections Explained](https://www.corsair.com/us/en/explorer/diy-builder/power-supply-units/psu-protections-explained/) |
| Case | ต้องตรวจพื้นที่ GPU, CPU cooler และหม้อน้ำแยกจากขนาดเมนบอร์ด | [Corsair: 5000D Case Manual](https://assets.corsair.com/image/upload/corsairmedia/sys_master/productcontent/WW_5000D_5000D_Airflow_QSG_WEB_AA.pdf), [Case Form Factors](https://help.corsair.com/hc/en-us/articles/360029181092-Case-Form-Factors) |
| Cooler | หลักการชุดลม/ชุดน้ำและความเหมาะสมกับพื้นที่ติดตั้ง | [Intel: Liquid Cooling vs. Air Cooling](https://www.intel.com/content/www/us/en/gaming/resources/cpu-cooler-liquid-cooling-vs-air-cooling.html) |
| Cooler/Case | อุณหภูมิ, thermal throttling, ซิลิโคน และ airflow | [Intel: The Importance of Keeping Your PC Cool](https://www.intel.com/content/www/us/en/gaming/resources/pc-cooling-the-importance-of-keeping-your-pc-cool.html) |

สูตร CPU TDP + GPU Power + 100W ในคำตอบ PSU เป็นกฎเบื้องต้นของ SpecFlow
ตาม `spec_recommender.py` ไม่ใช่สูตรรับรองจากผู้ผลิตหรือการจำลองกำลังไฟสูงสุด
เนื้อหา FAQ อธิบายสิ่งที่ผู้ใช้ควรตรวจเพิ่มเติมได้ แม้ฐานข้อมูลจัดสเปคยังไม่มีข้อมูลนั้น
เช่น ความยาว GPU, ระยะ RAM/Cooler และ BIOS

เนื้อหา 3 รูปแบบของแต่ละ hardware intent เป็นหัวข้อย่อยตามพฤติกรรมสุ่มของ ActionFAQ เดิม
ข้อความสำรองแต่ละรูปแบบต้องตรงกับข้อความในการ์ดลำดับเดียวกัน
เมนูความสามารถใช้ข้อความสรุปเพียง 1 รูปแบบ เพื่อแสดงบริการทั้ง 4 ด้านครบทุกครั้ง

ผลตรวจในเครื่องครอบคลุม Action, JSON และการ serialize ด้วย LINE SDK
ยังไม่ใช่การตรวจรับจาก LINE API หรือการยืนยันภาพบนแอป LINE จริง
การจำแนก intent ใหม่และการกลับเข้า form หลังถาม FAQ ต้องตรวจในเฟส 3
