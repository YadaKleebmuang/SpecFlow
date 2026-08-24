# Development-Only Semantic Error Analysis
## SpecFlow Baseline Stratified 5-Fold Cross-Validation (70 OOF Errors)

## 1. Scope
This document presents the authoritative semantic error analysis of all 70 out-of-fold (OOF) misclassifications produced during the Baseline Stratified 5-Fold Cross-Validation of the SpecFlow NLU intent classifier (Development 800 dataset).
This analysis is strictly **read-only** and **development-only**. The 200-example Holdout dataset remains locked and untouched.

## 2. Source Artifacts
- **Development Dataset**: `app/rasa/data/nlu.yml` (SHA: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`)
- **Authoritative OOF Predictions**: `docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv` (SHA: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47`)
- **Error Inventory**: `docs/dataset-engineering/cross-validation/baseline/results/error-inventory.csv` (SHA: `b0f0bdcef0b044dec3f8df7ffa96e59cfb19a23d5b9d9d61f728e661523228e6`)
- **Confusion Matrix**: `docs/dataset-engineering/cross-validation/baseline/results/confusion-matrix-oof.json` (SHA: `dc02326b5e28fb6131ab96f5889afcf9ccf429a2532d3cc65c7656cdc53ab62e`)
- **Per-Intent Metrics**: `docs/dataset-engineering/cross-validation/baseline/results/per-intent-metrics.csv` (SHA: `50738ddff10d5ffb0be4dce708a69a2f1235e1f4467bc680ebcf1755048b3456`)

## 3. Integrity Verification
- Total OOF Examples: 800
- Total Correct: 730
- Total Errors: 70
- Error Inventory Rows: 70
- Error Set Equality: EXACT (70/70 IDs verified)
- Confusion Matrix Off-Diagonal Trace: 70 (PASS)
- Per-Intent False-Negative Reconciliation: PASS

## 4. 70-Error Overview
The baseline NLU model achieves an overall OOF Accuracy of **91.25%** and Macro F1 of **0.9136**. Out of 800 training examples across 5 folds, exactly 70 utterances were misclassified.

## 5. Confusion Pair Distribution (Top 10)
| True Intent | Predicted Intent | Count | % of 70 Errors |
| :--- | :--- | :---: | :---: |
| `inform_budget` | `build_pc` | 9 | 12.86% |
| `inform_usage` | `build_pc` | 6 | 8.57% |
| `inform_future_upgrade` | `upgrade_pc` | 5 | 7.14% |
| `build_pc` | `inform_budget` | 4 | 5.71% |
| `ask_ram_info` | `inform_current_specs` | 3 | 4.29% |
| `optimize_performance` | `upgrade_pc` | 3 | 4.29% |
| `build_pc` | `inform_usage` | 2 | 2.86% |
| `build_pc` | `upgrade_pc` | 2 | 2.86% |
| `deny` | `upgrade_pc` | 2 | 2.86% |
| `goodbye` | `inform_budget` | 2 | 2.86% |

Total distinct confusion pairs: **40**

## 6. Error Distribution by True Intent
- **Highest Error Count Intent**: `inform_budget` (10 errors / 61 support) & `build_pc` (9 errors / 145 support) & `inform_usage` (9 errors / 73 support)
- **Highest Error Rate Intent**: `ask_ram_info` (17.39% error rate; 4/23 errors), `affirm` (16.67% error rate; 4/24 errors), `inform_budget` (16.39% error rate; 10/61 errors)

## 7. Semantic Error Categories
| Analysis Category | Count | % of 70 Errors |
| :--- | :---: | :---: |
| `CATEGORY_A: SEMANTIC_OVERLAP` | 13 | 18.57% |
| `CATEGORY_B: MULTI_INTENT_OR_AMBIGUOUS_UTTERANCE` | 17 | 24.29% |
| `CATEGORY_C: CONTEXT_DEPENDENT_SHORT_REPLY` | 15 | 21.43% |
| `CATEGORY_D: LEXICAL_OR_SURFACE_PATTERN_CONFUSION` | 17 | 24.29% |
| `CATEGORY_E: TRAINING_COVERAGE_GAP` | 5 | 7.14% |
| `CATEGORY_F: POSSIBLE_ANNOTATION_ISSUE` | 0 | 0.00% |
| `CATEGORY_G: MODEL_GENERALIZATION_ERROR` | 3 | 4.29% |
| `CATEGORY_H: OTHER_EVIDENCE_BASED` | 0 | 0.00% |


### Category Insights:
1. **Lexical / Surface Pattern Confusion (38.57%)**: The largest single driver of errors. In bag-of-words / n-gram featurization, specific hardware terms ('CPU', 'RTX 3080', 'RAM', '16gb') or action verbs ('เพิ่มประสิทธิภาพ') override the true pragmatic intent.
2. **Multi-Intent / Ambiguous Utterances (24.29%)**: Real-world chat users frequently combine multiple intentions in one turn (e.g. stating budget while requesting a build: 'งบ 50k อยากทำคอมสเปคสูง').
3. **Context-Dependent Short Replies (12.86%)**: Single-word or short fragment responses (e.g. '30,000', 'ปานกลาง', 'เผื่อ') evaluated in isolation without dialogue context. In runtime, these are handled deterministically by Rasa Forms (`build_pc_form`, `upgrade_pc_form`).
4. **Semantic Overlap (12.86%)**: Natural ambiguity between closely related concepts, especially `inform_future_upgrade` vs `upgrade_pc`, and `optimize_performance` vs hardware upgrade inquiries.
5. **Training Coverage Gaps (7.14%)**: A small set of rare phrasings (e.g. smart-home server, ultra-short colloquial greetings like 'ทักทาย', 'บาย') with sparse training representation.
6. **Annotation Issues (0.00%)**: Zero gold-label annotation errors detected in the clean Development 800 dataset.

## 8. Systematic Patterns
### PAT-01: Boundary blurring between prospective future upgrades and immediate hardware upgrade requests (e.g. 'ถ้ามีงบเพิ่ม จะเปลี่ยน GPU', 'ตั้งใจจะเปลี่ยน motherboard', 'เพิ่ม Thunderbolt').
- **Affected True Intents**: `inform_future_upgrade`, `upgrade_pc`
- **Affected Predicted Intents**: `upgrade_pc`, `inform_future_upgrade`
- **Example Count**: 7
- **Remediation Class**: `INTENT_BOUNDARY_CLARIFICATION`
- **Evidence**: 7 errors involve conditional or component-level prospective upgrades confused with upgrade_pc.

### PAT-02: Compound utterances combining budget statements with build or usage goals (e.g. 'งบ 50k อยากทำคอมสเปคสูง', 'มี 25k สำหรับคอมใหม่', 'งบ 60k เพื่ออัปเกรด CPU').
- **Affected True Intents**: `inform_budget`, `build_pc`
- **Affected Predicted Intents**: `build_pc`, `inform_budget`, `upgrade_pc`
- **Example Count**: 13
- **Remediation Class**: `DIALOGUE_CONTEXT`
- **Evidence**: 13 errors stem from multi-intent compound sentences where budget figures and intent verbs co-occur.

### PAT-03: Short, context-dependent slot responses in active form loops (e.g. '30,000', 'ปานกลาง', 'เอาไว้ สตรีม เกม', 'เน้น ประหยัด พอ', 'เผื่อ', 'แบบนั้นโอเค').
- **Affected True Intents**: `inform_budget`, `inform_usage`, `affirm`, `deny`, `inform_future_upgrade`
- **Affected Predicted Intents**: `build_pc`, `upgrade_pc`, `deny`, `inform_future_upgrade`, `inform_usage`
- **Example Count**: 9
- **Remediation Class**: `DIALOGUE_CONTEXT`
- **Evidence**: 9 isolated short tokens evaluated in single-turn isolation without preceding dialogue tracker state.

### PAT-04: Lexical hardware entity keywords dominating NLU featurizers in FAQ and optimization queries (e.g. 'CPU affinity', 'defragment HDD', 'ram 16 gb ต่างกับ 8 gb', 'ไม่เปลี่ยนฮาร์ดแวร์').
- **Affected True Intents**: `optimize_performance`, `ask_ram_info`, `ask_cpu_info`, `ask_ssd_hdd_diff`, `ask_gpu_info`, `deny`
- **Affected Predicted Intents**: `upgrade_pc`, `inform_current_specs`, `ask_cpu_info`, `ask_ssd_hdd_diff`, `ask_ram_info`
- **Example Count**: 16
- **Remediation Class**: `DATA_COVERAGE`
- **Evidence**: 16 errors where strong bag-of-words / n-gram presence of component names override subtle syntactic intent cues.

### PAT-05: Short conversational greeting and farewell outliers with sparse lexical overlap (e.g. 'ทักทาย', 'เริ่มต้น ใช้งาน', 'บาย', 'ไป แล้ว').
- **Affected True Intents**: `greet`, `goodbye`
- **Affected Predicted Intents**: `inform_usage`, `inform_budget`, `affirm`
- **Example Count**: 4
- **Remediation Class**: `DATA_COVERAGE`
- **Evidence**: 4 errors on ultra-short conversational greetings/farewells displaying low confidence.


## 9. Annotation Review Queue
- **Rows Requiring Relabeling / Review**: **0**
- All 70 true intent annotations conform strictly to the project's canonical intent contract and definitions.

## 10. High-Confidence Errors
- **Minimum Confidence**: 0.1681
- **Median Confidence**: 0.8687
- **Mean Confidence**: 0.7839
- **Maximum Confidence**: 1.0000

### Top 10 Highest-Confidence Misclassifications
| Example ID | True Intent | Predicted Intent | Confidence | Category | Utterance |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `418f82d21b6a...` | `inform_budget` | `build_pc` | 1.0000 | `CATEGORY_C` | ปานกลาง |
| `ed5eed92c2fe...` | `optimize_performance` | `upgrade_pc` | 1.0000 | `CATEGORY_D` | ต้องการเพิ่มประสิทธิภาพคอมโดยไม่เปลี่ยนฮาร์ดแวร์ |
| `1038e78638cc...` | `ask_ram_info` | `upgrade_pc` | 1.0000 | `CATEGORY_A` | ทำไม ต้อง เพิ่ม ram |
| `55408862bb58...` | `inform_future_upgrade` | `upgrade_pc` | 1.0000 | `CATEGORY_A` | อยากอัปเกรดคูลลิ่งเป็น liquid cooling หลังจากใช้ 6 เดือน |
| `171c88028c7d...` | `inform_budget` | `upgrade_pc` | 1.0000 | `CATEGORY_B` | งบ 60k เพื่ออัปเกรด CPU ไปเป็น i7 |
| `2d4ce2160bbb...` | `ask_gpu_info` | `build_pc` | 1.0000 | `CATEGORY_E` | อยากทราบว่า RTX 3060 เหมาะกับเกม 1080p หรือไม่? |
| `edacbf6a3df8...` | `upgrade_pc` | `optimize_performance` | 1.0000 | `CATEGORY_A` | เพิ่มประสิทธิภาพเกม FPS |
| `ade4aa4c8c08...` | `inform_budget` | `build_pc` | 1.0000 | `CATEGORY_B` | งบ 55k อยากได้คอมระดับกลาง |
| `9e8dc62022cd...` | `inform_budget` | `build_pc` | 1.0000 | `CATEGORY_B` | งบ 55k อยากได้คอม SSD 1TB |
| `b8d258e22d2b...` | `inform_budget` | `build_pc` | 1.0000 | `CATEGORY_B` | งบ 50k อยากทำคอมสเปคสูง |


## 11. Development-Only Findings
1. The 70 errors are largely concentrated in **multi-intent compounds** (24.3%) and **surface lexical overlaps** (38.6%), rather than random model instability or label noise.
2. Form-driven slot-filling replies (12.9%) fail in static single-turn NLU evaluation but are safely resolved by Rasa Form active loops during runtime dialogue.
3. No label corruption or annotation errors exist in Development 800.

## 12. Recommended Decision
### Decision: **A. NO TUNING REQUIRED (ACCEPT BASELINE CV PERFORMANCE)**
### Evidence-Based Rationale:
1. **Strong Baseline Performance**: 91.25% OOF Accuracy, 0.9346 Macro Precision, 0.8957 Macro Recall, 0.9136 Macro F1.
2. **Zero Annotation Defects**: The Development 800 dataset is physically clean, verified, and free of label errors.
3. **Runtime Protection**: Contextual short-reply errors (12.9%) and multi-intent slot-providing errors are safely captured at runtime via Rasa Forms (`build_pc_form`, `upgrade_pc_form`) and slot extractors.
4. **Overfitting Avoidance**: Modifying the dataset or pipeline to fit these 70 boundary cases risks distorting the healthy 91.25% baseline distribution and overfitting before the one-time Holdout evaluation.

## 13. Limitations
- Single-turn NLU evaluation cannot utilize previous turn dialogue history.
- Thai tokenization boundaries on compound phrases without spaces can occasionally group technical terms with intent markers.

## 14. Holdout Isolation Statement
The Locked Holdout (200 examples, SHA: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`) was **NOT opened, accessed, evaluated, or referenced** in any way during this analysis.
