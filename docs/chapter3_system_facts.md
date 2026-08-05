# ข้อเท็จจริงของระบบ SpecFlow สำหรับเขียนเอกสารบทที่ 3 และบทที่ 4 (Chapter 3 System Facts)

> [!NOTE]
> เอกสารฉบับนี้สรุปข้อมูลเชิงประจักษ์จากซอร์สโค้ดและผลการทดลองจริง สำหรับใช้อ้างอิงในการเขียนหรือแก้ไขเอกสารบทที่ 3 (วิธีการดำเนินงาน) และบทที่ 4 (ผลการประเมินทดลอง)

---

## 1. ข้อมูลชุดข้อมูลและโครงสร้าง Intent/Entity

* **จำนวน Intent สุดท้าย**: 15 Intents
* **จำนวนข้อมูลฝึกทั้งหมด (`nlu.yml`)**: 264 ตัวอย่าง
* **จำนวนข้อมูลทดสอบอิสระ (`nlu_test.yml`)**: 69 ตัวอย่าง
* **จำนวนข้อมูลฝึกแต่ละ Intent**:
  * `build_pc` (36), `inform_usage` (25), `upgrade_pc` (23), `optimize_performance` (22), `inform_current_specs` (22), `inform_budget` (18), `inform_future_upgrade` (14), `ask_cpu_info` (14), `ask_gpu_info` (14), `ask_ram_info` (14), `ask_ssd_hdd_diff` (14), `greet` (12), `goodbye` (12), `affirm` (12), `deny` (12)
* **Entities ที่ใช้งานจริง (4 Entities)**: `budget`, `usage`, `component_type`, `future_upgrade`
* **Slots ที่ใช้งานจริง (4 Slots)**: `budget` (text), `usage` (text), `current_specs` (text), `future_upgrade` (bool)
* **Forms ที่ใช้งานจริง (2 Forms)**: `build_pc_form`, `upgrade_pc_form`

---

## 2. ขั้นตอนการเตรียมข้อความและการประมวลผล (NLP Pipeline)

1. **Text Normalization & Lowercasing**: ทำความสะอาดและแปลงตัวพิมพ์เล็กภาษาอังกฤษ
2. **Dictionary-based Typo Correction**: แปลงคำผิดและคำศัพท์ฮาร์ดแวร์ด้วย [typo_dict.json](file:///c:/Users/thirs/Downloads/SpecFlow/app/services/nlp/typo_dict.json) (เช่น 'กาดจอ' $\rightarrow$ 'gpu', 'ซีพียู' $\rightarrow$ 'cpu')
3. **Thai Word Segmentation**: ตัดคำภาษาไทยด้วยห้องสมุด **PyThaiNLP** (`engine="newmm"`)
4. **Stopword Filtering**: ลบคำหางเสียงและคำฟุ่มเฟือย (`CUSTOM_STOPWORDS`)
5. **Rasa Custom Tokenizer**: ส่งต่อข้อความที่ตัดคำแล้วให้ `ThaiTokenizer` ใน Rasa Pipeline

---

## 3. Rasa Pipeline และ Policy Configurations

* **Pipeline Components**: 
  1. `thai_tokenizer.ThaiTokenizer`
  2. `RegexFeaturizer`
  3. `LexicalSyntacticFeaturizer`
  4. `CountVectorsFeaturizer` (word level)
  5. `CountVectorsFeaturizer` (char_wb level, min_ngram=1, max_ngram=4)
  6. `DIETClassifier` (epochs=100, constrain_similarities=true)
  7. `EntitySynonymMapper`
  8. `ResponseSelector` (epochs=100)
  9. `FallbackClassifier` (threshold=0.3)
* **Policies**: `MemoizationPolicy`, `RulePolicy`, `UnexpecTEDIntentPolicy`, `TEDPolicy`

---

## 4. วิธีการฝึกและประเมินผล (Training & Evaluation Methodology)

* **คำสั่งฝึก**: `rasa train` (รันจากโฟลเดอร์ `app/rasa/`) โหลดและบันทึกโมเดลไว้ใน `app/rasa/models/` เป็นรูปแบบไฟล์ `.tar.gz`
* **การประเมินระดับที่ 1 (Cross-Validation)**: ใช้ Stratified 5-Fold Cross-Validation บนชุดข้อมูลฝึก (`rasa test nlu --cross-validation --folds 5`) 
  * Intent Test Accuracy = **84.00%**, Intent Test F1-Score = **83.30%**
  * Entity Test Accuracy = **90.40%**, Entity Test F1-Score = **82.70%**
* **การประเมินระดับที่ 2 (Locked Holdout Test Set)**: ทดสอบหนึ่งครั้งบนชุดทดสอบอิสระ `nlu_test.yml` 69 ตัวอย่าง
  * Intent Holdout Accuracy = **82.61%**, Weighted F1-score = **82.18%**, Macro F1-score = **79.97%**
  * Entity Holdout Accuracy = **90.35%**
* **ไฟล์ผลลัพธ์การประเมิน**:
  * Cross-validation: `app/rasa/results/cross_validation/intent_report.json`
  * Holdout Test: `app/rasa/results/out_of_sample_v1/intent_report.json`

---

## 5. Data Flow Architecture ของระบบ Production

$$\text{LINE User} \xrightarrow{\text{Webhook}} \text{Ngrok (5005)} \xrightarrow{\text{LineInput}} \text{PyThaiNLP Preprocessor} \xrightarrow{\text{Rasa NLU DIET}} \text{Action Server (5055)} \xrightarrow{\text{SpecRecommender Logic}} \text{SQLite (analytics.db)} \xrightarrow{\text{Flex Message}} \text{LINE App}$$
