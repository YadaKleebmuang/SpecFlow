# รายงานการประเมินประสิทธิภาพโมเดล Rasa NLU (Model Evaluation Report)

> [!NOTE]
> เอกสารแสดงผลการประเมินประสิทธิภาพโมเดล **Rasa NLU** (โมเดลล่าสุด: `20260805-145642-kinetic-cliff.tar.gz`) ทั้งจากการประเมินแบบ 5-Fold Cross-Validation และ Locked Holdout Test Set

---

## 1. ผลการประเมินแบบ 5-Fold Cross-Validation (Level 1 Evaluation)

สรุปผลการทดสอบการแบ่งชุดข้อมูลฝึกออกเป็น 5 Folds (Stratified Split) โดยประเมินค่าเฉลี่ยบน Test Folds:

| งานประเมิน (Task) | Accuracy | Precision (Macro Avg) | Recall (Macro Avg) | F1-Score (Macro Avg) | ตำแหน่งไฟล์ผลลัพธ์ |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Intent Classification** | **84.00%** | **88.20%** | **83.30%** | **83.30%** | `app/rasa/results/cross_validation/intent_report.json` |
| **Entity Extraction** | **90.40%** | **89.10%** | **82.70%** | **82.70%** | `app/rasa/results/cross_validation/DIETClassifier_report.json` |

---

## 2. ผลการประเมินบนชุดทดสอบอิสระ (Level 2: Locked Holdout Test Set)

การทดสอบโมเดลที่ฝึกสำเร็จกับชุดข้อมูลที่ไม่เคยผ่านการฝึกมาก่อน (`app/rasa/tests/nlu_test.yml` จำนวน 69 ประโยค):

### 2.1 สรุปภาพรวม (Overall Holdout Performance)

* **Intent Holdout Accuracy**: **82.61%**
* **Intent Holdout Weighted F1-score**: **82.18%**
* **Intent Holdout Macro F1-score**: **79.97%**
* **Entity Holdout Accuracy**: **90.35%**

### 2.2 ผลประเมินราย Intent บนชุด Holdout Test Set (`results/out_of_sample_v1/intent_report.json`)

| ชื่อ Intent | Precision | Recall | F1-Score | Support (จำนวนตัวอย่าง) |
| :--- | :---: | :---: | :---: | :---: |
| `build_pc` | 0.8750 | 1.0000 | 0.9333 | 7 |
| `upgrade_pc` | 1.0000 | 1.0000 | 1.0000 | 6 |
| `optimize_performance` | 0.7500 | 1.0000 | 0.8571 | 6 |
| `inform_budget` | 1.0000 | 0.8333 | 0.9091 | 6 |
| `inform_usage` | 0.7500 | 1.0000 | 0.8571 | 6 |
| `inform_current_specs` | 1.0000 | 0.8000 | 0.8889 | 5 |
| `ask_gpu_info` | 0.7500 | 0.7500 | 0.7500 | 4 |
| `ask_cpu_info` | 0.7500 | 0.7500 | 0.7500 | 4 |
| `ask_ssd_hdd_diff` | 0.7500 | 0.7500 | 0.7500 | 4 |
| `goodbye` | 1.0000 | 0.5000 | 0.6667 | 4 |
| `ask_ram_info` | 1.0000 | 0.5000 | 0.6667 | 4 |
| `affirm` | 1.0000 | 0.6667 | 0.8000 | 3 |
| `inform_future_upgrade` | 0.6000 | 1.0000 | 0.7500 | 3 |
| `deny` | 0.6667 | 0.6667 | 0.6667 | 3 |
| `greet` | 0.7500 | 0.7500 | 0.7500 | 4 |

---

## 3. การวิเคราะห์คู่ Intent ที่สับสนและข้อเสนอแนะในการปรับปรุง

จากการวิเคราะห์ `intent_errors.json` พบคู่ Intent ที่สับสนกันเล็กน้อย:
1. `deny` สับสนกับ `inform_future_upgrade` (เกิดจากประโยคที่มีคำปฏิเสธและคำว่าเผื่ออัปเกรดร่วมกัน)
2. `goodbye` สับสนกับ `optimize_performance` หรือ `inform_usage` (คำบอกลาที่มีการกล่าวขอบคุณคำแนะนำการใช้งาน)
3. `ask_ram_info` สับสนกับ `ask_cpu_info` (คำถามเปรียบเทียบสเปกอุปกรณ์)
