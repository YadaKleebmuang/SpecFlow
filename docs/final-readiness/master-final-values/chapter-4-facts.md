# Chapter 4 Facts Sheet — Results
## Source of Truth for Thesis Chapter 4 Evaluation Sections

### 1. Development Dataset Statistics (800 Examples)
- **Total Examples**: 800
- **Total Intents**: 15 (Distribution: `build_pc`: 145, `upgrade_pc`: 117, `optimize_performance`: 98, `inform_usage`: 73, `inform_current_specs`: 68, `inform_budget`: 61, `inform_future_upgrade`: 58, `deny`: 25, `affirm`: 24, `ask_cpu_info`: 23, `ask_gpu_info`: 23, `ask_ram_info`: 23, `ask_ssd_hdd_diff`: 23, `goodbye`: 20, `greet`: 19).
- **Entity Annotations**: 187 total (`component_type`: 96, `budget`: 46, `usage`: 33, `future_upgrade`: 12).

### 2. Baseline Stratified 5-Fold Cross-Validation Results (Development 800)
- **OOF Accuracy**: `0.91250000` (91.25%, 730 / 800 correct, 70 errors)
- **OOF Macro Precision**: `0.93456081` (93.46%)
- **OOF Macro Recall**: `0.89567678` (89.57%)
- **OOF Macro F1-Score**: `0.91355855` (91.36%)
- **OOF Weighted Precision**: `0.91474247` (91.47%)
- **OOF Weighted Recall**: `0.91250000` (91.25%)
- **OOF Weighted F1-Score**: `0.91247033` (91.25%)
- **5-Fold Cross-Validation Summary (Mean ± Sample SD, $ddof=1$)**:
  - Accuracy: `0.91250000 ± 0.01397542`
  - Macro Precision: `0.93883481 ± 0.01566618`
  - Macro Recall: `0.89436763 ± 0.02618612`
  - Macro F1-Score: `0.90846876 ± 0.02069854`
  - Weighted Precision: `0.91847530 ± 0.01429771`
  - Weighted Recall: `0.91250000 ± 0.01397542`
  - Weighted F1-Score: `0.91044731 ± 0.01349372`

### 3. Baseline Entity Extraction Evaluation (Token-Level DIET Evaluation)
- **Macro Precision**: `0.4199 ± 0.0921`
- **Macro Recall**: `0.5938 ± 0.1582`
- **Macro F1-Score**: `0.4568 ± 0.0761`
- **Weighted F1-Score**: `0.5264 ± 0.0481`
- **Per-Entity Metrics**:
  - `component_type`: Precision `0.5414 ± 0.1240`, Recall `0.7470 ± 0.2533`, F1 `0.6116 ± 0.1577` (183 token support)
  - `budget`: Precision `0.3490 ± 0.1009`, Recall `0.7379 ± 0.1246`, F1 `0.4667 ± 0.0996` (67 token support)
  - `usage`: Precision `0.4953 ± 0.1634`, Recall `0.5819 ± 0.1032`, F1 `0.5271 ± 0.1316` (144 token support)
  - `future_upgrade`: Precision `0.2940 ± 0.3640`, Recall `0.3082 ± 0.3757`, F1 `0.2217 ± 0.2934` (73 token support)

### 4. Final Model Training & Runtime Verification
- **Training**: Single run on all 800 Development examples (59.9 min, 0 errors, Final Model SHA: `86a76534...`).
- **Runtime Verification**: 8 / 8 test cases passed (RT-01 to RT-08).

### 5. Final Holdout 200 Test Performance (DEFINITIVE TEST BENCHMARK)
- **Total Test Examples**: 200 (Unseen Locked Holdout)
- **Correct Predictions**: 141
- **Classification Errors**: 59
- **Accuracy**: `0.70500000` (70.50%)
- **Macro Precision**: `0.78831203` (78.83%)
- **Macro Recall**: `0.71515891` (71.52%)
- **Macro F1-Score**: `0.72564964` (72.56%)
- **Weighted Precision**: `0.75312253` (75.31%)
- **Weighted Recall**: `0.70500000` (70.50%)
- **Weighted F1-Score**: `0.70027716` (70.03%)
- **Fallback Predictions**: 10 (5.00% trigger rate on utterances where max intent confidence < 0.3)

#### Per-Intent Final Test Results Table
| Intent | Precision | Recall | F1-Score | Support | TP | FP | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `greet` | 0.8333 | 1.0000 | 0.9091 | 5 | 5 | 1 | 0 |
| `goodbye` | 0.8000 | 0.8000 | 0.8000 | 5 | 4 | 1 | 1 |
| `build_pc` | 0.6757 | 0.6944 | 0.6849 | 36 | 25 | 12 | 11 |
| `upgrade_pc` | 0.5625 | 0.9310 | 0.7013 | 29 | 27 | 21 | 2 |
| `inform_budget` | 0.4737 | 0.6000 | 0.5294 | 15 | 9 | 10 | 6 |
| `inform_usage` | 1.0000 | 0.6667 | 0.8000 | 18 | 12 | 0 | 6 |
| `inform_current_specs` | 0.8095 | 1.0000 | 0.8947 | 17 | 17 | 4 | 0 |
| `ask_cpu_info` | 0.5000 | 0.8333 | 0.6250 | 6 | 5 | 5 | 1 |
| `ask_gpu_info` | 0.6667 | 0.3333 | 0.4444 | 6 | 2 | 1 | 4 |
| `ask_ram_info` | 1.0000 | 0.8333 | 0.9091 | 6 | 5 | 0 | 1 |
| `ask_ssd_hdd_diff` | 1.0000 | 0.8333 | 0.9091 | 6 | 5 | 0 | 1 |
| `optimize_performance` | 0.8462 | 0.4400 | 0.5789 | 25 | 11 | 2 | 14 |
| `inform_future_upgrade` | 0.8571 | 0.4286 | 0.5714 | 14 | 6 | 1 | 8 |
| `affirm` | 0.8000 | 0.6667 | 0.7273 | 6 | 4 | 1 | 2 |
| `deny` | 1.0000 | 0.6667 | 0.8000 | 6 | 4 | 0 | 2 |
| **Total / Macro** | **0.7883** | **0.7152** | **0.7256** | **200** | **141** | **59** | **59** |

### 6. Comparison: Development CV vs Final Holdout
| Metric | Development CV (5-Fold Mean) | Holdout 200 Final Test | Descriptive Delta |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 0.9125 (91.25%) | 0.7050 (70.50%) | -0.2075 (-20.75%) |
| **Macro F1** | 0.9085 (90.85%) | 0.7256 (72.56%) | -0.1828 (-18.28%) |

### 7. System / End-to-End Verification
- **Functional Tests**: 16 / 16 passed (SYS-01 to SYS-16).
- **Verification Level**: `BACKEND E2E VERIFIED, LIVE LINE NOT VERIFIED`.
