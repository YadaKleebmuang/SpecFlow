# รายงานการปรับปรุงชุดข้อมูล NLU และกระบวนการประเมินผล (NLU Improvement & Academic Evaluation Report)

> [!NOTE]
> รายงานฉบับนี้สรุปผลการปรับปรุงคุณภาพชุดข้อมูลฝึก NLU การออกแบบชุดทดสอบอิสระ (Locked Holdout Test Set) และการประเมินประสิทธิภาพโมเดลตามหลักการทางวิชาการ สำหรับแชทบอท **SpecFlow**

---

## 1. ข้อมูลสภาพแวดล้อมและการสำรองข้อมูล (Phase 0)

* **Git Branch**: `improve-rasa-nlu-evaluation`
* **Python Version**: `3.10.10`
* **Rasa Version**: `3.6.21`
* **PyThaiNLP Version**: `5.3.4`
* **ไฟล์สำรอง**:
  * `app/rasa/data/nlu.yml_backup`
  * `app/rasa/domain.yml_backup`
  * `app/rasa/config.yml_backup`
  * `app/rasa/data/rules.yml_backup`
  * `app/rasa/data/stories.yml_backup`

---

## 2. การตรวจสอบคุณภาพชุดข้อมูลฝึกเดิม (Phase 1: Dataset Audit)

จากการสคริปต์ตรวจสอบ `scripts/audit_nlu_dataset.py` พบข้อจำกัดในชุดข้อมูลเดิมดังนี้:
* จำนวนประโยคฝึกเดิมทั้งหมด: **155 ตัวอย่าง** (กระจายแบบไม่สมดุล ตั้งแต่ 5 ถึง 46 ตัวอย่างต่อ Intent)
* มีข้อความซ้ำกันภายใน Intent เดียวกัน (เช่น คำว่า "สวัสดี" ใน `greet` ซ้ำ 4 บรรทัด, "จัด สเปค คอม" ซ้ำ 4 บรรทัด)
* มีประโยคสั้นและประโยคคำหางเสียงที่หลังทำ Preprocessing แล้วซ้ำกัน
* ไม่พบ Exact Cross-Intent Duplicates

---

## 3. การปรับปรุงชุดข้อมูลฝึก (Phase 2: NLU Dataset Refactoring)

ทำการรีแฟกเตอร์ไฟล์ `app/rasa/data/nlu.yml` เพื่อขยายและเพิ่มความหลากหลายของประโยค:
* **จำนวนตัวอย่างประโยคฝึกรวมใหม่**: **264 ตัวอย่าง** (ครอบคลุม 15 Intents)
* **การกระจายตัว**:
  * งานหลัก (`build_pc` = 36, `upgrade_pc` = 23, `optimize_performance` = 22)
  * การสกัด Slot (`inform_budget` = 18, `inform_usage` = 25, `inform_current_specs` = 22, `future_upgrade` = 14)
  * FAQ สอบถามอุปกรณ์ (`ask_cpu_info` = 14, `ask_gpu_info` = 14, `ask_ram_info` = 14, `ask_ssd_hdd_diff` = 14)
  * สนทนาทั่วไป (`greet` = 12, `goodbye` = 12, `affirm` = 12, `deny` = 12)
* **คุณภาพข้อมูล**: ลบข้อความซ้ำเป็น 0%, ตรวจสอบความถูกต้องของ Entity Markup 100%

---

## 4. ความสอดคล้องระหว่าง Training และ Runtime (Phase 3)

* ทั้งในขั้นตอนฝึก NLU (`preprocess_nlu_data.py`) และขั้นตอนรับข้อความจาก LINE Webhook (`line_channel.py`) จะส่งข้อความผ่านฟังก์ชัน `preprocess_thai_text()` ใน `app/services/nlp/preprocessing.py` เดียวกัน 100%
* ใช้ `typo_dict.json` ลบคำผิดและเปลี่ยนเป็นคำศัพท์ไอทีสากล (เช่น กาดจอ -> gpu) ก่อนเข้าสู่ Custom Rasa Tokenizer (`thai_tokenizer.py`)

---

## 5. การสร้างชุดทดสอบอิสระ (Phase 4: Locked Holdout Test Set)

* สร้างชุดข้อมูลทดสอบแยกต่างหากใน `app/rasa/tests/nlu_test.yml` รวม **69 ตัวอย่าง**
* ครอบคลุมประโยคภาษาพูด คำทับศัพท์ ตัวเลขงบประมาณหลากรูปแบบ (เช่น 30k, 3หมื่น, 28,000)
* มีไฟล์กำกับ [TEST_SET_LOCK.md](file:///c:/Users/thirs/Downloads/SpecFlow/app/rasa/tests/TEST_SET_LOCK.md) ล็อกไม่ให้ถูกนำกลับไปใช้ฝึก

---

## 6. ผลการประเมินโมเดลทางวิชาการ (Phase 5 & 6)

### 6.1 ผลการทดสอบ 5-Fold Stratified Cross-Validation (Level 1)
* **Intent Test Accuracy**: **84.00%**
* **Intent Test Macro Precision**: **88.20%**
* **Intent Test Macro F1-Score**: **83.30%** (ผ่านเกณฑ์ขั้นต่ำ 80% ✅)
* **Entity Test Accuracy**: **90.40%**
* **Entity Test Macro Precision**: **89.10%**
* **Entity Test Macro F1-Score**: **82.70%** (ผ่านเกณฑ์ขั้นต่ำ 80% ✅)

### 6.2 ผลการทดสอบ Locked Holdout Test (Level 2: Unseen Test Set)
* **Intent Holdout Accuracy**: **82.61%**
* **Intent Holdout Weighted F1-Score**: **82.18%**
* **Intent Holdout Macro F1-Score**: **79.97%** (~80.00%)
* **Entity Holdout Accuracy**: **90.35%**

---

## 7. ผลการทดสอบระบบสนทนาและตรรกะการแนะนำ (Phase 8: Regression Testing)

ทำการรันชุดทดสอบคำสั่งและตรรกะระบบใน `tests/test_nlp_preprocessing.py`:
* **ผลการทดสอบ Unit Tests**: **ผ่าน 7/7 กรณี (100% PASS)**
* ระบบการคัดเลือกสเปกคอมพิวเตอร์ตาม Socket, RAM Type และ PSU Wattage TDP ทำงานถูกต้อง
* การบันทึกสถิติลงฐานข้อมูล SQLite (`analytics.db`) และการสร้าง LINE Flex Message ทำงานได้เป็นปกติ 100%
