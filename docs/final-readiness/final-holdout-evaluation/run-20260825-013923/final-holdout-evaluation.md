# One-Time Locked Holdout 200 Final Evaluation Report
## SpecFlow Conversational AI Final Test Performance (Evaluation ID: `specflow_final_holdout_v1`)

## 1. Evaluation Scope
This document records the **single authoritative evaluation** of the locked Final Model against the unseen **Locked Holdout 200 dataset**.
This evaluation provides the definitive test benchmark for the undergraduate project report.

## 2. One-Time Authorization
- **Authorization Gate**: `docs/final-readiness/pre-holdout-gate/pre-holdout-authorization.json` (SHA: `88f56ea96fa89ae5e900c58787b116bcd95a4f3e824106ac226aa314aa22a827`)
- **Evaluation Invocation**: `1` (Exactly one execution)

## 3. Final Model Identity
- **Model Path**: `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz`
- **Model SHA-256**: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7`
- **Training Scope**: 100% of Development 800 (Run ID: `run-20260825-001846`)

## 4. Locked Holdout Identity
- **Holdout Path**: `docs/dataset-engineering/holdout/locked-holdout-v1.yml`
- **Holdout SHA-256**: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`
- **Holdout Examples**: 200
- **Prior Evaluations**: 0
- **Exact Duplicate Overlap with Development 800**: **0**

## 5. Evaluation Method
Deterministic per-example inference using Rasa 3.6.21 Agent runtime and CLI evaluation on the complete 200-example Holdout set.

## 6. Final Intent Classification Results
- **Total Test Examples**: **200**
- **Correct Predictions**: **141**
- **Classification Errors**: **59**
- **Accuracy**: **0.70500000** (70.50%)
- **Macro Precision**: **0.78831203** (78.83%)
- **Macro Recall**: **0.71515891** (71.52%)
- **Macro F1-Score**: **0.72564964** (72.56%)
- **Weighted Precision**: **0.75312253** (75.31%)
- **Weighted Recall**: **0.70500000** (70.50%)
- **Weighted F1-Score**: **0.70027716** (70.03%)

## 7. Per-Intent Results
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


## 8. Confusion Matrix
- **Dimensions**: 15 x 15
- **Total Instances**: 200
- **Diagonal Sum (Correct)**: 141
- **Off-Diagonal Sum (Errors)**: 59
- **Matrix Artifacts**:
  - `holdout-confusion-matrix.json`
  - `holdout-confusion-matrix.png`

## 9. Holdout Error Inventory
- **Error Count**: **59**
- **Error CSV**: `holdout-errors.csv` (Contains all 59 misclassifications with true intent, predicted intent, and confidence).

## 10. Fallback Observation
- **Fallback Predictions**: 10
- **Fallback Rate**: 5.00%

## 11. Entity Final Evaluation (Token-Level DIET Evaluation)
- **Gold Entity Spans**: 15 ({'budget': 15})
- **Token Support Total**: 15
- **Macro Precision**: 0.1000
- **Macro Recall**: 0.0667
- **Macro F1-Score**: 0.0800
- **Weighted F1-Score**: 0.0800

## 12. Comparison with Development Cross-Validation
| Metric | Development CV (5-Fold Mean) | Holdout 200 Final Test | Descriptive Delta |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 0.9125 (91.25%) | 0.7050 (70.50%) | -0.2075 (-20.75%) |
| **Macro F1** | 0.9085 (90.85%) | 0.7256 (72.56%) | -0.1828 (-18.28%) |

*(Note: Comparison is strictly descriptive for final reporting. Holdout results are locked and will not be used for further tuning).*

## 13. Methodological Isolation & No-Post-Holdout-Tuning Statement
- **Training Executed**: NO
- **Development Modified**: NO
- **Final Model Modified**: NO
- **Post-Holdout Tuning**: **FORBIDDEN (Model and results are permanently frozen)**

## 14. Final Performance Statement

> **ONE-TIME LOCKED HOLDOUT 200 EVALUATION COMPLETE**  
> **FINAL MODEL PERFORMANCE = LOCKED**  
> **HOLDOUT STATUS = CLOSED / FINAL EVALUATED**
