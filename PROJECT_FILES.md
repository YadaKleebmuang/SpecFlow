# SpecFlow Project Files (เอกสารโครงสร้างไฟล์ของระบบ)

เอกสารฉบับนี้อธิบายโครงสร้าง บทบาทหน้าที่ และสถานะของไฟล์ทั้งหมดในโครงการ **SpecFlow** (ระบบแชทบอทภาษาไทยสำหรับแนะนำสเปคและอัปเกรดคอมพิวเตอร์) เพื่อเป็นคู่มือสำหรับนักพัฒนาและการอ้างอิงในการเขียนเล่มรายงานปริญญานิพนธ์

---

## 1. ไฟล์หลักของระบบแชทบอท (Rasa & Conversational Backend)

### `app/rasa/config.yml`
- **หน้าที่**: กำหนด NLU Pipeline (การตัดคำ PyThaiNLP `newmm`, Featurizers, DIETClassifier, FallbackClassifier) และ Dialogue Policies (MemoizationPolicy, RulePolicy, UnexpecTEDIntentPolicy, TEDPolicy)
- **สถานะ**: `FINAL LOCKED` (SHA-256: `61349072...`)
- **การแก้ไข**: ไม่ควรแก้ไขหลังจากการทดสอบ Final Holdout สิ้นสุดลง

### `app/rasa/domain.yml`
- **หน้าที่**: กำหนด Intent (15 intents), Entities (4 types), Slots (4 slots), Forms (2 forms: `build_pc_form`, `upgrade_pc_form`), Bot Responses และ Custom Actions ที่ระบบรองรับ
- **สถานะ**: `FINAL LOCKED` (SHA-256: `c2a76780...`)
- **การแก้ไข**: ไม่ควรแก้ไขหลังจากการทดสอบ Final Holdout สิ้นสุดลง

### `app/rasa/data/nlu.yml`
- **หน้าที่**: ชุดข้อมูล Development สำหรับฝึกฝนโมเดล NLU จำนวน 800 ตัวอย่าง ครอบคลุม 15 เจตนา พร้อม Entity Annotations 187 ตำแหน่ง
- **สถานะ**: `FINAL LOCKED` (SHA-256: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`)
- **การแก้ไข**: ห้ามแก้ไขเพื่อรักษาความถูกต้องของการทดลอง

### `app/rasa/data/rules.yml`
- **หน้าที่**: กำหนดกฎตายตัวของระบบการสนทนา เช่น กฎการเปิดใช้งานฟอร์ม (`build_pc_form`, `upgrade_pc_form`), การประมวลผลคำตอบเมื่อฟอร์มเสร็จสิ้น, และการจัดการ NLU Fallback (`utter_fallback`)
- **สถานะ**: `FINAL LOCKED` (SHA-256: `37325e42...`)
- **การแก้ไข**: ห้ามแก้ไข

### `app/rasa/data/stories.yml`
- **หน้าที่**: ตัวอย่างเส้นทางการสนทนาแบบ Multi-turn Stories สำหรับฝึกฝน TEDPolicy
- **สถานะ**: `FINAL LOCKED` (SHA-256: `45e869d2...`)
- **การแก้ไข**: ห้ามแก้ไข

### `app/rasa/credentials.yml`
- **หน้าที่**: กำหนดช่องทางการเชื่อมต่อภายนอก (เช่น LINE Channel) โดยโหลดโทเค็นผ่าน Environment Variables (`${LINE_CHANNEL_SECRET}`, `${LINE_CHANNEL_ACCESS_TOKEN}`)
- **สถานะ**: `FINAL LOCKED / SECURED` (ไม่มี Hardcoded Secrets)
- **การแก้ไข**: แก้ไขเฉพาะเมื่อต้องการเพิ่มช่องทางสื่อสารใหม่

### `app/rasa/endpoints.yml`
- **หน้าที่**: กำหนด URL สำหรับเชื่อมต่อไปยัง Rasa SDK Action Server (`http://localhost:5055/webhook`)
- **สถานะ**: `FINAL LOCKED`
- **การแก้ไข**: แก้ไขเฉพาะเมื่อย้ายเซิร์ฟเวอร์ Action Server

### `app/rasa/thai_tokenizer.py`
- **หน้าที่**: Custom Rasa Tokenizer Component ที่ใช้ PyThaiNLP (`engine='newmm'`) สำหรับตัดคำภาษาไทยใน NLU Pipeline
- **สถานะ**: `FINAL LOCKED`
- **การแก้ไข**: โค้ดหลักของ NLU

### `app/rasa/line_channel.py`
- **หน้าที่**: Custom LINE Messaging API Input Channel พร้อมระบบตรวจสอบลายเซ็นดิจิทัล (HMAC-SHA256 Signature Verification ผ่าน `WebhookParser`)
- **สถานะ**: `FINAL LOCKED / VERIFIED`
- **การแก้ไข**: โค้ดหลักของ LINE Integration

### `app/rasa/actions/actions.py`
- **หน้าที่**: รวม Custom Actions ทั้งหมดของระบบ ได้แก่ `action_recommend_pc`, `action_recommend_upgrade`, `action_cpu_info`, `action_gpu_info`, `action_ram_info`, `action_ssd_hdd_diff`, `action_optimize_performance`
- **สถานะ**: `FINAL LOCKED / RUNTIME VERIFIED` (ผ่านการทดสอบ 7/7 actions)
- **การแก้ไข**: ไม่ควรแก้ไข

### `app/rasa/actions/flex.py`
- **หน้าที่**: ตัวสร้าง LINE Flex Message (Bubble / Carousel JSON payload) จากเทมเพลตและข้อมูลสเปคคอมพิวเตอร์ที่ระบบแนะนำ
- **สถานะ**: `FINAL LOCKED / RUNTIME VERIFIED`
- **การแก้ไข**: ไม่ควรแก้ไข

---

## 2. ระบบแนะนำฮาร์ดแวร์และการประมวลผลภาษา (Services)

### `app/services/recommendation/spec_recommender.py`
- **หน้าที่**: Engine แนะนำสเปคคอมพิวเตอร์ประกอบใหม่ โดยคำนวณงบประมาณตามวัตถุประสงค์ (Gaming, Editing, General Office), ตรวจสอบความเข้ากันได้ของอุปกรณ์ (Socket, RAM Type, PSU Wattage), และแจ้งเตือนหากงบประมาณตึงตัว
- **สถานะ**: `FINAL LOCKED / VERIFIED`

### `app/services/recommendation/upgrade_advisor.py`
- **หน้าที่**: Engine วิเคราะห์สเปคเดิมของผู้ใช้ ระบุจุดคอขวด (Bottlenecks) และแนะนำชิ้นส่วนที่ควรเปลี่ยนหรืออัปเกรดเป็นอันดับแรก
- **สถานะ**: `FINAL LOCKED / VERIFIED`

### `app/services/recommendation/hardware_db.json`
- **หน้าที่**: ฐานข้อมูลอุปกรณ์ฮาร์ดแวร์คอมพิวเตอร์จำนวน 64 รายการ (CPU: 14, GPU: 12, Mainboard: 10, RAM: 8, Storage: 5, PSU: 6, Case: 5, Cooler: 4)
- **สถานะ**: `FINAL LOCKED` (SHA-256: `ad8e11a6...`)

### `app/services/nlp/preprocessing.py` & `typo_dict.json`
- **หน้าที่**: ระบบ Preprocessing สำหรับทำความสะอาดข้อความ ปรับแก้คำผิดทั่วไป (Typo Correction) และตัดคำฟุ่มเฟือยก่อนเข้าสู่กระบวนการ NLU
- **สถานะ**: `FINAL LOCKED`

---

## 3. ฐานข้อมูลและการจัดเก็บข้อมูล (Data & Analytics)

### `data/analytics.db`
- **หน้าที่**: ฐานข้อมูล SQLite สำหรับบันทึกสถิติการค้นหาของผู้ใช้งาน ตาราง `user_searches` (`id`, `timestamp`, `user_id`, `usage_type`, `budget_requested`, `allocated_total_price`)
- **ความปลอดภัย**: จัดเก็บเฉพาะข้อมูลเชิงสถิติ (Aggregate Metrics) **ไม่จัดเก็บข้อความแชทส่วนตัวของผู้ใช้**
- **สถานะ**: `FINAL LOCKED / SECURED`

---

## 4. โมเดลและชุดข้อมูลประเมินผล (Models & Evaluations)

### `final_models/run-20260825-001846/`
- **หน้าที่**: โมเดลตัวสมบูรณ์ตัวเดียวที่ผ่านการฝึกฝนด้วยชุดข้อมูล Development 800 ตัวอย่าง (`20260825-001851-woolen-billet.tar.gz`, SHA-256: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7`)
- **สถานะ**: `FINAL AUTHORITATIVE MODEL`

### `docs/dataset-engineering/holdout/locked-holdout-v1.yml`
- **หน้าที่**: ชุดข้อมูลทดสอบอิสระ (Unseen Holdout 200 ตัวอย่าง) สำหรับประเมินประสิทธิภาพครั้งเดียว (One-time Final Evaluation)
- **สถานะ**: `FINAL LOCKED / CLOSED` (SHA-256: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`)

### `cv_results/`
- **หน้าที่**: โฟลเดอร์เก็บผลลัพธ์และโมเดลจากการทดสอบ Baseline Stratified 5-Fold Cross-Validation บนชุดข้อมูล Development เพื่อรักษาความสามารถในการทำซ้ำ (Reproducibility)
- **สถานะ**: `LOCKED REPRODUCIBILITY PROVENANCE`

---

## 5. เอกสารสรุปผลเชิงประจักษ์สำหรับปริญญานิพนธ์ (Docs & Thesis Facts)

### `docs/final-readiness/master-final-values/`
- **`master-final-values.json`**: สรุปตัวเลขผลการทดลองทั้งหมดในรูปแบบ JSON สำหรับโปรแกรมประมวลผล
- **`master-final-values.md`**: ตาราง Master Values Table สรุปผลอย่างเป็นทางการ
- **`chapter-3-facts.md`**: ข้อเท็จจริงด้านระเบียบวิธีวิจัยและสถาปัตยกรรมสำหรับเขียนบทที่ 3
- **`chapter-4-facts.md`**: ตัวเลขผลการทดลองและตาราง Performance สำหรับเขียนบทที่ 4
- **`chapter-5-facts.md`**: การอภิปรายผล ช่องว่างการเรียนรู้ ข้อจำกัด และงานในอนาคตสำหรับเขียนบทที่ 5
- **`report-safe-claims.md`**: ข้อกำหนดการอ้างอิงผล (Approved Claims, Qualified Claims, Forbidden Claims)
- **`master-final-values-manifest.json`**: Manifest รับรองความถูกต้องและความสมบูรณ์ของหลักฐานทั้งหมด
