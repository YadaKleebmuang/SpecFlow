# S14: การจัดการข้อมูลและการสรุปรายงาน (Data Management, CRUD, Search, and Reporting Specification)

---

## 1. การจัดการข้อมูลขั้นพื้นฐาน (CRUD Operations)

ระบบ SpecFlow ดำเนินการจัดการฐานข้อมูล (Create, Read, Update, Delete - CRUD) แบบแยกบทบาทระหว่างฐานข้อมูลธุรกรรมประวัติ (SQLite) และคลังชิ้นส่วนอุปกรณ์ (JSON):

### 1.1. การสร้างข้อมูล (Create)
1. **การบันทึกประวัติการสืบค้น (Search Transaction Logging):**
   * เกิดขึ้นแบบอัตโนมัติในฝั่งหลังบ้าน เมื่อผู้ใช้ออกคำสั่งจัดสเปคคอมสำเร็จ (`ActionRecommendPC`) หรืออัปเกรดสำเร็จ (`ActionRecommendUpgrade`) ระบบจะเรียกฟังก์ชัน `log_search()` บันทึกข้อมูลลงตาราง `user_searches` ในไฟล์ [analytics.db](file:///c:/Users/thirs/Downloads/SpecFlow/data/analytics.db)
2. **การเพิ่มข้อมูลอุปกรณ์ไอทีคลังสินค้า (Hardware Component Insertion):**
   * ทำการเพิ่มเติมข้อมูลลงในรายการคลาสอาเรย์คลังสินค้าในสคริปต์ [generate_hardware_db.py](file:///c:/Users/thirs/Downloads/SpecFlow/app/scripts/generate_hardware_db.py) จากนั้นแอดมินรันคำสั่งเพื่อให้ระบบเขียนโครงสร้าง JSON ทับไฟล์ฐานข้อมูลหลัก

### 1.2. การอ่านข้อมูล (Read)
1. **การดึงรายการเพื่อคำนวณ (Recommendation Processing):**
   * คลาส `SpecRecommender` และ `UpgradeAdvisor` จะทำการอ่านไฟล์ `hardware_db.json` ขึ้นมาบนหน่วยความจำเพื่อเปรียบเทียบหาอุปกรณ์ที่เข้ากันได้
2. **การดึงเพื่อประมวลรายงาน (Reporting Query):**
   * โมดูล `response_builder.py` เปิดฟังก์ชันเชื่อมต่อ SQLite และยิง SQL Select คำสั่งดึงรายการทั้งหมดขึ้นมาคำนวณสถิติภาพรวม

### 1.3. การอัปเดตข้อมูล (Update)
* **การปรับเปลี่ยนราคาหรือรุ่นอุปกรณ์ (Hardware Catalog Updating):**
  * ดำเนินการอัปเดตราคาหรือสถานะคุณสมบัติของอุปกรณ์โดยเขียนทับข้อมูลใน `hardware_db.json` ในส่วนแถวที่ต้องการแก้ไข (ไม่มีการบันทึกแก้ไขใน SQLite เนื่องจากตารางประวัติธุรกรรมใช้เก็บล็อกแบบถาวร ห้ามทำการแก้ไขเพื่อป้องกันความน่าเชื่อถือของข้อมูลสถิติลดลง)

### 1.4. การลบข้อมูล (Delete)
* **การล้างประวัติธุรกรรม (Database Clearing):**
  * ผู้ดูแลระบบสามารถลบประวัติล็อกทั้งหมดออกเพื่อเริ่มต้นเก็บสถิติรอบใหม่ได้โดยลบไฟล์ `analytics.db` ทิ้งโดยตรง ระบบมีกลไกป้องกันความขัดข้องโดยจะตรวจเช็คและเรียกคำสั่ง SQL: `CREATE TABLE IF NOT EXISTS user_searches` ขึ้นมาสร้างโครงสร้างตารางใหม่โดยอัตโนมัติในการสืบค้นครั้งถัดไป

---

## 2. การค้นหาและการกรองข้อมูล (Search & Filter Logic)

ตรรกะการค้นหาอุปกรณ์คอมพิวเตอร์ที่เหมาะสมที่สุดภายใต้งบประมาณและการใช้งาน ควบคุมผ่านฟังก์ชันตัวกรองช่วย `get_best_part` ในโมดูล [spec_recommender.py](file:///c:/Users/thirs/Downloads/SpecFlow/app/services/recommendation/spec_recommender.py) โครงสร้างคำสั่งมีดังนี้:

```python
def get_best_part(category, max_price, filter_func=lambda x: True):
    if category not in self.db:
        return None
    # กรองอุปกรณ์ที่ราคาไม่เกินงบประมาณจัดสรรเฉพาะหมวด และตรงตามเงื่อนไขความเข้ากันได้ (filter_func)
    valid_parts = [p for p in self.db[category] if p['price'] <= max_price and filter_func(p)]
    
    # กรณีงบประมาณจัดสรรน้อยเกินไปจนไม่พบชิ้นส่วนในราคาที่กำหนด
    if not valid_parts:
        # ดึงอุปกรณ์ที่เข้ากันได้ทั้งหมดมา แล้วเลือกตัวที่มีราคาถูกที่สุดแทน เพื่อให้ระบบจัดสเปคคอมเสร็จสิ้นได้
        valid_parts = [p for p in self.db[category] if filter_func(p)]
        if not valid_parts:
            return None
        return min(valid_parts, key=lambda x: x['price'])
        
    # ดึงอุปกรณ์ที่ราคาแพงที่สุดและไม่เกินกรอบงบประมาณจัดสรร เพื่อประสิทธิภาพสูงสุดของผู้ใช้
    return max(valid_parts, key=lambda x: x['price'])
```

### การประยุกต์ใช้งานตัวกรองข้อจำกัด (Applied Filter Functions)
* **ตัวกรองเมนบอร์ด (Mainboard Filter):** กรอง Socket ให้ตรงซีพียู และหากเลือกเผื่ออนาคต บังคับกรองเฉพาะบอร์ดชนิดแรม DDR5
  $$\text{Filter: } \text{lambda } x: x.\text{get}(\text{'socket'}) == \text{cpu\_socket} \text{ and } (\text{not future\_upgrade or } x.\text{get}(\text{'ram\_type'}) == \text{'DDR5'})$$
* **ตัวกรองเคสคอมพิวเตอร์ (Case Filter):** กรองเคสที่รองรับขนาดเมนบอร์ด
  $$\text{Filter: } \text{lambda } x: \text{mb\_form\_factor} \in x.\text{get}(\text{'form\_factor\_support'}, []) $$
* **ตัวกรองพาวเวอร์ซัพพลาย (PSU Filter):** กรองวัตต์ PSU ให้มากกว่าหรือเท่ากับค่า TDP รวม
  $$\text{Filter: } \text{lambda } x: x.\text{get}(\text{'wattage'}, 0) \ge \text{total\_tdp}$$

---

## 3. การประมวลผลสรุปสถิติรายงาน (Reporting & Analytical SQL)

ระบบมีการสืบค้นประวัติและประมวลผลข้อมูลก้อนใหญ่จาก SQLite เพื่อสรุปยอดสถิติเชิงปริมาณสำหรับนำเสนอให้แอดมินหรือใช้ในเล่มรายงานวิจัยผ่านโมดูล [response_builder.py](file:///c:/Users/thirs/Downloads/SpecFlow/app/services/response/response_builder.py):

### 3.1. การออกรายงานสถิติรายสัปดาห์ (Weekly Usage Query)
ใช้ชุดคำสั่ง SQL จัดหมวดหมู่วันที่ด้วยฟังก์ชัน `strftime` เพื่อสรุปจำนวนธุรกรรมและผู้ใช้งานไม่ซ้ำกันต่อสัปดาห์:
```sql
SELECT strftime('%Y-W%W', timestamp) as week, COUNT(DISTINCT user_id), COUNT(*) 
FROM user_searches 
GROUP BY week 
ORDER BY week;
```

### 3.2. การออกรายงานความต้องการยอดนิยม (Usage Popularity Query)
ดึงสัดส่วนความต้องการใช้งานหลักของคอมพิวเตอร์เพื่อประเมินความต้องการของผู้บริโภค:
```sql
SELECT usage_type, COUNT(*) as count 
FROM user_searches 
GROUP BY usage_type 
ORDER BY count DESC;
```

### 3.3. การวิเคราะห์จัดประเภทช่วงงบประมาณ (Budget Range Analysis Query)
สรุปการวิเคราะห์สัดส่วนระดับฐานะหรืองบประมาณที่ผู้ใช้ร้องขอเข้ามาบ่อยที่สุด โดยใช้เงื่อนไขตรรกะจัดกลุ่ม:
```sql
SELECT 
    CASE 
        WHEN budget_requested < 15000 THEN 'ต่ำกว่า 15,000 บาท'
        WHEN budget_requested >= 15000 AND budget_requested < 20000 THEN '15,000 - 19,999 บาท'
        WHEN budget_requested >= 20000 AND budget_requested < 30000 THEN '20,000 - 29,999 บาท'
        WHEN budget_requested >= 30000 AND budget_requested < 40000 THEN '30,000 - 39,999 บาท'
        WHEN budget_requested >= 40000 AND budget_requested < 50000 THEN '40,000 - 49,999 บาท'
        ELSE '50,000 บาทขึ้นไป'
    END as budget_range,
    COUNT(*) as count
FROM user_searches
WHERE budget_requested > 0
GROUP BY budget_range
ORDER BY count DESC;
```
*(สถิติเฉลี่ยงบประมาณสืบค้นทั้งหมดคำนวณผ่านคำสั่ง SQL: `SELECT AVG(budget_requested) FROM user_searches WHERE budget_requested > 0`)*
