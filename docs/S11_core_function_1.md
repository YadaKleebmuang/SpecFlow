# S11: ฟังก์ชันหลักที่ 1 - ระบบจัดสเปคคอมพิวเตอร์อัจฉริยะ (Smart PC Builder Specification)

---

## 1. ขั้นตอนการทำงาน (Workflow)

ฟังก์ชันการจัดสเปคคอมพิวเตอร์ประกอบใหม่ (Smart PC Builder) เริ่มทำงานเมื่อผู้ใช้สื่อสารด้วยข้อความที่มีเจตนาจัดสเปคคอมพิวเตอร์ ระบบจะดำเนินขั้นตอนการรวบรวมตัวแปรและประมวลผลคำนวณตามโฟลว์สเตทดังนี้:

```text
[ผู้ใช้] พิมพ์ "จัดสเปคคอม" -> [Rasa NLU] ระบุเจตนา build_pc 
  -> [Rasa Core] เปิดฟอร์ม build_pc_form
  -> [Rasa Core] เรียก Action ถามงบประมาณ (Slot: budget)
  -> [ผู้ใช้] ระบุจำนวนงบประมาณ (เช่น 25,000 หรือพิมพ์ "งบปานกลาง")
  -> [Rasa Core] เรียก Action ถามลักษณะงาน (Slot: usage) (แสดงปุ่มตอบด่วน Quick Reply)
  -> [ผู้ใช้] กดปุ่มเลือกงาน (เช่น เล่นเกม, ทำงานกราฟิก, งานออฟฟิศ)
  -> [Rasa Core] เรียก Action ถามความต้องการเผื่ออัปเกรด (Slot: future_upgrade)
  -> [ผู้ใช้] ยืนยัน ใช่/ไม่ (Slot: future_upgrade = True/False)
  -> [Rasa Core] ปิดฟอร์ม build_pc_form และเรียก Action Server พอร์ต 5055: action_recommend_pc
  -> [Action Server] เรียก SpecRecommender ประมวลตรรกะจัดสเปคตามเงื่อนไข
  -> [Action Server] บันทึกสถิติประวัติจัดสเปคลง SQLite (analytics.db)
  -> [Action Server] ผสานข้อมูลลง Flex Message และเรียก LineOutput push_message ส่งคืนการ์ดผู้ใช้
  -> [Rasa Core] สั่งคืนค่า Reset Slots ทุกตัวเป็น Null
```

---

## 2. ตรรกะการประมวลผลทางธุรกิจ (Business Logic)

ตรรกะการจัดสเปคแบ่งออกเป็นสองชั้นหลัก ควบคุมผ่านคลาส `SpecRecommender` ในไฟล์ [spec_recommender.py](file:///c:/Users/thirs/Downloads/SpecFlow/app/services/recommendation/spec_recommender.py) ดังนี้:

### 2.1. ชั้นที่ 1: การแบ่งสัดส่วนงบประมาณ (Layer 1 - Budget Allocation)
ระบบจะทำการแบ่งเงินทุนออกเป็น 2 ก้อนหลัก ได้แก่ งบอุปกรณ์หลัก 75% (`core_budget`) และงบอุปกรณ์เสริม 25% (`other_budget`) จากนั้นกระจายตัวคูณตามพารามิเตอร์ประเภทงาน:

* **สเปคงบประหยัดเป็นพิเศษ (งบประมาณรวม < 16,000 บาท):**
  * กำหนดสัดส่วนงบการ์ดจอแยกเป็น **0%** (Integrated GPU) เพื่อโยกงบไปพัฒนาชิ้นส่วนอื่นป้องกันระบบขัดข้อง
  * อัตราส่วน: CPU (ออนบอร์ด) 45%, RAM 25%, Storage 30%
* **ประเภทเน้นการเล่นเกม (Gaming):**
  * อัตราส่วน: การ์ดจอแยก (GPU) 40%, CPU 30%, RAM 15%, Storage 15%
* **ประเภทเน้นงานตัดต่อ/กราฟิก (Editing):**
  * อัตราส่วน: CPU 35%, GPU 30%, RAM 20%, Storage 15%
* **ประเภทใช้งานเอกสารทั่วไป (Office):**
  * อัตราส่วน: CPU 35%, RAM 20%, Storage 25%, GPU 20%

สำหรับงบอุปกรณ์เสริม 25% ที่เหลือ จะทำการจัดสรรอัตราสัดส่วนคงที่เสมอ: เมนบอร์ด 40%, พาวเวอร์ซัพพลาย (PSU) 25%, เคส 20%, และพัดลมระบายความร้อน (Cooler) 15%

---

### 2.2. ชั้นที่ 2: กฎความเข้ากันได้ทางกายภาพ (Layer 2 - Hardware Compatibility Rules)
ระบบจะดึงอุปกรณ์จากฐานข้อมูล JSON โดยใช้ตัวกรองข้อจำกัด (Compatibility Filtering Rules) ดังนี้:

$$\text{1. การจับคู่ซีพียูกับเมนบอร์ด: } \text{cpu.socket} == \text{motherboard.socket}$$

$$\text{2. การจับคู่เมนบอร์ดกับแรม: } \text{motherboard.ram\_type} == \text{ram.type}$$

$$\text{3. การตรวจสอบกำลังไฟของพาวเวอร์ซัพพลาย (PSU Wattage Verification):}$$
$$\text{psu.wattage} \ge (\text{cpu.tdp} + \text{gpu.power\_draw} + 100\text{W})$$

$$\text{4. การตรวจขนาดเคสคอมพิวเตอร์: } \text{motherboard.form\_factor} \in \text{case.form\_factor\_support}$$

$$\text{5. การจับคู่พัดลมระบายความร้อน: } \text{cpu.socket} \in \text{cooler.socket\_support}$$

* **กรณีเลือกเผื่ออนาคต (Future Upgrade = True):**
  * ระบบกำหนดกฎบังคับ (Hard Constraint): $\text{cpu.socket} \in [AM5, LGA1700]$ และ $\text{ram.type} == DDR5$ เท่านั้น

---

## 3. หน้าจอและอินเทอร์เฟซโต้ตอบ (UI Screenshots & Layouts)

ฟังก์ชันการจัดสเปคประยุกต์ใช้งาน Flex Message Templates ในไดเรกทอรี `templates/`:

1. **หน้าจอสอบถามลักษณะการใช้งาน (`card_ask_usage.json`):**
   * บล็อกการ์ดคำถามสไตล์โมเดิร์น พร้อมแผงปุ่ม Quick Reply เสนอ 3 หมวดงานหลัก (เล่นเกม, กราฟิก, ออฟฟิศ) 
2. **หน้าจอสอบถามสิทธิ์การอัปเกรดในอนาคต (`card_ask_future_upgrade.json`):**
   * บล็อกปุ่ม "ใช่ (ต้องการเผื่ออนาคต)" และ "ไม่จำเป็น (ต้องการประหยัด)" เพื่อเก็บค่าพารามิเตอร์ Boolean 
3. **หน้าจอจัดแสดงสเปคคอมพิวเตอร์แนะนำ (`card_spec_builder.json`):**
   * โครงสร้างตารางรายการอุปกรณ์ 8 บรรทัด แสดงชื่ออุปกรณ์และราคาแยกชิ้นชัดเจน ยอดราคารวมบอร์ดแสดงเป็นอักษรหนาสีฟ้า และมีช่องแถบแจ้งเตือน Warning สีส้มหากราคารวมสินค้าจำเป็นเกินงบประมาณสะสมของผู้ใช้ไปเล็กน้อย

---

## 4. ฐานข้อมูลที่เกี่ยวข้อง (Database Interactions)

* **คลังสินค้าอุปกรณ์ ([hardware_db.json](file:///c:/Users/thirs/Downloads/SpecFlow/app/services/recommendation/hardware_db.json)):**
  * ค้นหาและเปรียบเทียบข้อมูลราคา อัตรากินไฟ ขา Socket ขนาดบอร์ด และชนิดแรมของอุปกรณ์ เพื่อนำมาประกอบผลตรรกะจัดสเปคคอม
* **ฐานข้อมูลบันทึกสถิติใช้งาน ([analytics.db](file:///c:/Users/thirs/Downloads/SpecFlow/data/analytics.db)):**
  * บันทึกรายการใหม่ลงในตาราง `user_searches` ทันทีเมื่อจัดสเปคสำเร็จ:
    ```sql
    INSERT INTO user_searches (timestamp, user_id, usage_type, budget_requested, allocated_total_price)
    VALUES (?, ?, ?, ?, ?)
    ```

---

## 5. ส่วนต่อประสานโปรแกรมประยุกต์ที่เกี่ยวข้อง (APIs)

* **Rasa Action Endpoint:**
  * **พอร์ตที่ใช้:** HTTP POST `http://127.0.0.1:5055/webhook`
  * **บทบาท:** ประสานงานระหว่าง Rasa Core Dialogue Manager และโค้ดคำนวณ `ActionRecommendPC`
* **LINE Messaging API:**
  * **Endpoint:** `https://api.line.me/v2/bot/message/push`
  * **บทบาท:** ทำการส่ง (Push) บล็อกข้อความ Custom JSON โครงสร้างการ์ด Flex Message (`FlexSendMessage`) กลับไปยังผู้ใช้งานตามรหัส User ID ปลายทาง
