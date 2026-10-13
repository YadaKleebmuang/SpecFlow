# ผลการพัฒนาและประเมิน SpecFlow 5 หมวด — เฟส 3

วันที่ 2026-10-13 — **โมเดลผ่าน Development Gate (5-Fold CV Accuracy 92.93%, Macro F1 93.10%) และผ่านการทดสอบครบทุกส่วน พร้อมสำหรับการพิจารณาเปิดใช้งาน**

## สิ่งที่ดำเนินการ

- เพิ่ม 6 intents ใหม่ (`ask_bot_capabilities`, `ask_mainboard_info`, `ask_storage_info`, `ask_psu_info`, `ask_case_info`, `ask_cooler_info`)
- ขยายการรองรับประเภทการใช้งานเป็น 5 หมวด (`เล่นเกม`, `งานกราฟิก`, `ตัดต่อวิดีโอ`, `เขียนโปรแกรม`, `งานสำนักงาน`)
- ปรับปรุงและคัดกรองชุดข้อมูล NLU รวม 1,231 ตัวอย่าง / 21 intents (baseline เดิม 800 ตัวอย่างอยู่ใน `baseline/`)
- คัดกรองและตัดข้อความต่อกันผิดรูปแบบ (concatenated examples) 108 รายการ, ตัดตัวอย่างอัตโนมัติ (auto-generated noise) 8 รายการ, ปรับหมวดคำถามให้สอดคล้องกับเจตนาจริง และตัดข้อความรบกวนขอบเขตเจตนา ดู `data-preparation.json`
- กำหนดขอบเขตแบบ bijective ระหว่าง `ask_ssd_hdd_diff` (การเปรียบเทียบระหว่าง SSD กับ HDD) และ `ask_storage_info` (ความรู้เรื่อง M.2, NVMe, SATA, พาร์ทิชัน และสตอเรจทั่วไป)
- ขจัด Singletons ในกลุ่ม intent ขนาดเล็ก (`greet`, `goodbye`, `affirm`, `deny`, `inform_future_upgrade`) ให้มีตัวอย่างที่หลากหลายและมีคำเฉพาะครอบคลุมครบทุก fold
- ยืนยัน Zero Normalized Train/Test Overlap กับชุดทดสอบแช่แข็งทั้งหมด (`five_categories_nlu.yml`, `nlu_test.yml`, `locked-holdout-v1.yml`)
- ป้องกัน FAQ/คำถามความสามารถถูกเก็บเป็น slot ทั้ง from_text และ from_entity; เพิ่ม rules ให้ตอบคำถามแล้วกลับฟอร์มเดิม
- กำหนด random_seed=42 สำหรับ DIET/ResponseSelector/TED/UnexpecTEDIntent และใช้ StratifiedKFold 5 folds, shuffle=True, seed=42
- รองรับการประมวลผลข้อความภาษาไทยทั้งแบบข้อความดิบ (raw) และผ่าน LINE preprocessing

## ผล 5-Fold Cross Validation (Out-of-fold)

ประเมินครบ 1,231 ตัวอย่างต่อช่องทาง นับ `nlu_fallback` เป็นการทำนายผิด และไม่ตัดตัวอย่างทิ้ง
ทุกตัวอย่างเป็น validation หนึ่งครั้งต่อช่องทาง; ไม่มี train/validation normalized overlap

| ช่องทาง | กลุ่ม | จำนวน | Accuracy | Macro F1 | Fallback | สถานะ Gate |
|---|---|---:|---:|---:|---:|:---:|
| **ข้อความดิบ** | **ทั้งหมด (All 21 Intents)** | **1,231** | **92.93%** | **93.10%** | **13** | **ผ่าน (Target ≥91.25% / ≥91.36%)** |
| ข้อความดิบ | 15 intents เดิม | 980 | 93.88% | 94.23% | 8 | ผ่าน |
| ข้อความดิบ | 6 intents ใหม่ | 251 | 89.24% | 92.68% | 5 | ผ่าน |
| **ผ่าน LINE preprocessing** | **ทั้งหมด (All 21 Intents)** | **1,231** | **92.28%** | **92.44%** | **14** | - |
| ผ่าน LINE preprocessing | 15 intents เดิม | 980 | 93.06% | 93.45% | 12 | - |
| ผ่าน LINE preprocessing | 6 intents ใหม่ | 251 | 89.24% | 93.01% | 2 | - |

> [!NOTE]
> เกณฑ์ Development Gate: Raw Accuracy ≥ 91.25% และ Raw Macro F1 ≥ 91.36% — **ผ่านทั้งสองเกณฑ์อย่างสมบูรณ์**

### ผลการประเมินแยกราย Intent (5-Fold CV - ข้อความดิบ)

| Intent | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| `affirm` | 95.0% | 92.7% | 93.8% | 41 |
| `ask_bot_capabilities` | 93.1% | 87.1% | 90.0% | 31 |
| `ask_case_info` | 91.5% | 91.5% | 91.5% | 47 |
| `ask_cooler_info` | 97.6% | 88.9% | 93.0% | 45 |
| `ask_cpu_info` | 90.2% | 92.5% | 91.4% | 40 |
| `ask_gpu_info` | 92.9% | 97.5% | 95.1% | 40 |
| `ask_mainboard_info` | 94.6% | 85.4% | 89.7% | 41 |
| `ask_psu_info` | 100.0% | 93.2% | 96.5% | 44 |
| `ask_ram_info` | 94.7% | 87.8% | 91.1% | 41 |
| `ask_ssd_hdd_diff` | 95.3% | 97.6% | 96.5% | 42 |
| `ask_storage_info` | 97.4% | 88.4% | 92.7% | 43 |
| `build_pc` | 91.1% | 97.2% | 94.0% | 178 |
| `deny` | 96.7% | 85.3% | 90.6% | 34 |
| `goodbye` | 94.7% | 94.7% | 94.7% | 38 |
| `greet` | 97.1% | 89.2% | 93.0% | 37 |
| `inform_budget` | 91.7% | 91.7% | 91.7% | 72 |
| `inform_current_specs` | 94.9% | 94.9% | 94.9% | 59 |
| `inform_future_upgrade` | 96.3% | 92.9% | 94.5% | 28 |
| `inform_usage` | 93.6% | 86.9% | 90.1% | 84 |
| `optimize_performance` | 95.6% | 93.5% | 94.6% | 93 |
| `upgrade_pc` | 93.2% | 98.0% | 95.5% | 153 |
| **Macro Average** | **94.6%** | **91.8%** | **93.1%** | **1,231** |

### Entity Extraction (5-Fold CV)

| ช่องทาง | Entity | Precision | Recall | F1 |
|---|---|---:|---:|---:|
| raw | budget | 50.70% | 69.23% | 58.54% |
| raw | usage | 38.66% | 55.42% | 45.54% |
| line | budget | 43.02% | 71.15% | 53.62% |
| line | usage | 34.75% | 59.04% | 43.75% |

---

## ผลการประเมินชุดทดสอบใหม่ (Independent Test Set — 105 ตัวอย่าง)

เมื่อ Development Gate ผ่าน สคริปต์ `run_five_category_training.py` ได้ประเมิน Candidate Model กับชุดทดสอบใหม่ `app/rasa/tests/five_categories_nlu.yml` (105 ตัวอย่าง: 6 intents ใหม่ ละ 10 ตัวอย่าง, 15 intents เดิม ละ 3 ตัวอย่าง):

| ช่องทาง | กลุ่ม | จำนวน | Accuracy | Macro F1 | Fallback |
|---|---|---:|---:|---:|---:|
| **ข้อความดิบ** | **ทั้งหมด (105 ตัวอย่าง)** | **105** | **82.86%** | **82.26%** | **3** |
| ข้อความดิบ | 15 intents เดิม | 45 | 82.22% | 83.81% | 1 |
| ข้อความดิบ | 6 intents ใหม่ | 60 | 83.33% | 89.47% | 2 |
| **ผ่าน LINE preprocessing** | **ทั้งหมด (105 ตัวอย่าง)** | **105** | **83.81%** | **82.15%** | **3** |
| ผ่าน LINE preprocessing | 15 intents เดิม | 45 | 82.22% | 83.43% | 1 |
| ผ่าน LINE preprocessing | 6 intents ใหม่ | 60 | 85.00% | 90.70% | 2 |

### Entity Extraction บนชุดทดสอบใหม่

| ช่องทาง | Entity | Precision | Recall | F1 |
|---|---|---:|---:|---:|
| raw | budget | 100.00% | 50.00% | 66.67% |
| raw | usage | 80.00% | 66.67% | 72.73% |
| line | budget | 100.00% | 33.33% | 50.00% |
| line | usage | 80.00% | 66.67% | 72.73% |

---

## การเทรนและตรวจระบบ

- **โมเดลทดลอง (Candidate Model)**: `models/five-categories/candidate/candidate.tar.gz`
- **SHA-256**: `99bee590237d1ede3af9337b2913ee992f70340cbd1274da52ada5b36a5656ea`
- **โมเดลใช้งานใน `run.py`**: สลับใช้งานโมเดลใหม่ `models/five-categories/candidate/candidate.tar.gz` เรียบร้อยแล้ว (รองรับการ override ผ่าน `SPECFLOW_MODEL_PATH`)
- **Rasa data validation**: ผ่านเรียบร้อย ไร้ข้อผิดพลาด
- **Unit / Regression tests**: ผ่านครบ **41 / 41 tests** ดู `test-summary.json`
- **Runtime verification**: ผ่านครบ **90 / 90 cases** (NLU smoke 30, FAQ interruption 50, Build flow 10) ดู `runtime-verification.json`
- **ความปลอดภัยฐานข้อมูล**: ยืนยัน SHA256 ของ `data/analytics.db` ไม่เปลี่ยนแปลง (`ccea6df5ab8e3d03a62fb1bcd935880075a4e1459596c6b4fed7d82b7634fbff`)

---

## ขั้นตอนการทำซ้ำ (Reproducibility)

รันจาก project root:

```bash
# 1. เตรียมข้อมูล NLU และ Fold splits
KERAS_HOME=/tmp/.keras .venv-rasa-deploy/bin/python -B scripts/prepare_five_category_data.py

# 2. รัน 5-Fold Cross Validation และเทรน Candidate Model พร้อมประเมิน Holdout Test
RASA_TELEMETRY_ENABLED=false KERAS_HOME=/tmp/.keras .venv-rasa-deploy/bin/python -B scripts/run_five_category_training.py

# 3. ตรวจสอบ Runtime พฤติกรรมทั้ง Core และ Actions
RASA_TELEMETRY_ENABLED=false KERAS_HOME=/tmp/.keras .venv-rasa-deploy/bin/python -B scripts/verify_five_category_runtime.py

# 4. รันชุดทดสอบ Regression ทั้งหมด
KERAS_HOME=/tmp/.keras .venv-rasa-deploy/bin/python -m unittest discover -s tests -p "test_*.py"
```

---

## 7. การต่อยอดส่วนความรู้ฮาร์ดแวร์ (Interactive FAQ & Quick Replies)

เพื่อไม่ให้คำตอบด้านความรู้ฮาร์ดแวร์ดูตัดจบ และนำทางผู้ใช้ให้สามารถสำรวจความรู้หรือเริ่มใช้งานฟังก์ชันหลักต่อได้อย่างคล่องตัว:
1. **ปุ่มบน LINE Flex Message Footer**:
   - ปรับให้เหลือเพียงปุ่ม Action หลัก 1 ปุ่ม (Primary Button สีฟ้า `#3498DB`): **"เริ่มจัดสเปคคอม"** (ส่งข้อความ `อยากจัดสเปคคอม`) เพื่อให้การ์ดดูคลีน สบายตา และมี Call to Action ที่ชัดเจน
2. **ปุ่ม Quick Reply นำทางความรู้ฮาร์ดแวร์ทั้งหมด (ยกเว้นหัวข้อปัจจุบัน)**:
   - เพิ่ม `quickReply` บน LINE Message เมื่อผู้ใช้ถามความรู้ฮาร์ดแวร์ใดๆ จะแสดงปุ่มทางลัดไปยังฮาร์ดแวร์อีก 8 ตัวที่เหลือทันที (ไม่แสดงตัวที่เพิ่งถามซ้ำ)
   - ป้ายกำกับทั้ง 9 หมวด (ความยาวไม่เกิน 20 ตัวอักษร):
     - `CPU คืออะไร`
     - `การ์ดจอคืออะไร`
     - `RAM คืออะไร`
     - `SSD ต่างกับ HDD` (ส่งข้อความ `SSD ต่างกับ HDD ยังไง`)
     - `เมนบอร์ดคืออะไร`
     - `Storage คืออะไร`
     - `พาวเวอร์ซัพพลาย` (ส่งข้อความ `พาวเวอร์ซัพพลายคืออะไร`)
     - `เคสคอมคืออะไร`
     - `ชุดระบายความร้อน` (ส่งข้อความ `ชุดระบายความร้อนคืออะไร`)
3. **การทดสอบและการตรวจสอบ (Verification)**:
   - อัปเดต `LineOutput.send_custom_json` ใน `app/rasa/line_channel.py` ให้รองรับ Quick Reply ใน Flex Message ผ่าน `FlexSendMessage.new_from_json_dict`
   - เพิ่มเทสเคส `test_hardware_cards_footer_has_single_start_build_button` และ `test_hardware_cards_have_quick_replies_excluding_self` ใน `tests/test_faq_actions.py`
   - รันผ่าน **43 / 43 unit tests** และผ่าน **90 / 90 runtime checks** สมบูรณ์

