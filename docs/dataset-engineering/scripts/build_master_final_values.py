#!/usr/bin/env python3
import datetime
import hashlib
import json
import os
from pathlib import Path

def get_file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    repo = Path(os.getcwd())
    master_dir = repo / "docs/final-readiness/master-final-values"
    master_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Source files and hashes
    dev_p = repo / "app/rasa/data/nlu.yml"
    holdout_p = repo / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    model_p = repo / "final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz"
    cfg_p = repo / "app/rasa/config.yml"
    dom_p = repo / "app/rasa/domain.yml"
    rules_p = repo / "app/rasa/data/rules.yml"
    stories_p = repo / "app/rasa/data/stories.yml"
    hw_p = repo / "app/services/recommendation/hardware_db.json"
    analytics_p = repo / "data/analytics.db"
    
    dev_sha = get_file_sha256(dev_p)
    holdout_sha = get_file_sha256(holdout_p)
    model_sha = get_file_sha256(model_p)
    cfg_sha = get_file_sha256(cfg_p)
    dom_sha = get_file_sha256(dom_p)
    rules_sha = get_file_sha256(rules_p)
    stories_sha = get_file_sha256(stories_p)
    hw_sha = get_file_sha256(hw_p)
    
    assert dev_sha == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    assert holdout_sha == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    assert model_sha == "86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7"
    assert cfg_sha == "61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0"
    assert dom_sha == "c2a76780257345efc57dd32a8f261ac610745a4f21bad08bb308ad9b74717857"
    assert rules_sha == "37325e428ddcec108ff10cc3ec93b1d0e667c54f23d59c23f3c710ece7db22e5"
    assert stories_sha == "45e869d2b571bec45926228cf9537d099b3d6002484a985a0bcf09913c492985"
    
    # 2. Build Master Final Values JSON
    master_json_data = {
        "master_id": "specflow_master_final_values_v1",
        "timestamp": datetime.datetime.now().astimezone().isoformat(),
        "project": {
            "name": "SpecFlow",
            "type": "Thai Conversational PC Hardware Recommendation & Upgrade Assistant",
            "primary_channel": "LINE Official Account (LINE Messaging API)",
            "backend_framework": "Rasa Open Source 3.6.21",
            "implementation_language": "Python 3.9.6"
        },
        "runtime_environment": {
            "python": "3.9.6",
            "rasa": "3.6.21",
            "rasa_sdk": "3.6.2",
            "pythainlp": "5.3.4"
        },
        "datasets": {
            "development_800": {
                "path": "app/rasa/data/nlu.yml",
                "sha256": dev_sha,
                "rows": 800,
                "unique_rows": 800,
                "intents_count": 15,
                "distribution_type": "INTENTIONALLY_UNEQUAL_DESIGNED_COVERAGE",
                "distribution": {
                    "greet": 19, "goodbye": 20, "build_pc": 145, "upgrade_pc": 117,
                    "inform_budget": 61, "inform_usage": 73, "inform_current_specs": 68,
                    "ask_cpu_info": 23, "ask_gpu_info": 23, "ask_ram_info": 23,
                    "ask_ssd_hdd_diff": 23, "optimize_performance": 98,
                    "inform_future_upgrade": 58, "affirm": 24, "deny": 25
                },
                "entity_spans_total": 187,
                "entity_spans_by_type": {
                    "component_type": 96, "budget": 46, "usage": 33, "future_upgrade": 12
                }
            },
            "locked_holdout_200": {
                "path": "docs/dataset-engineering/holdout/locked-holdout-v1.yml",
                "sha256": holdout_sha,
                "rows": 200,
                "unique_rows": 200,
                "intents_count": 15,
                "distribution": {
                    "greet": 5, "goodbye": 5, "build_pc": 36, "upgrade_pc": 29,
                    "inform_budget": 15, "inform_usage": 18, "inform_current_specs": 17,
                    "ask_cpu_info": 6, "ask_gpu_info": 6, "ask_ram_info": 6,
                    "ask_ssd_hdd_diff": 6, "optimize_performance": 25,
                    "inform_future_upgrade": 14, "affirm": 6, "deny": 6
                },
                "exact_duplicate_overlap_with_dev": 0,
                "evaluation_status": "FINAL_EVALUATED_CLOSED",
                "evaluation_count": 1
            }
        },
        "baseline_stratified_5fold_cv": {
            "evaluation_name": "Baseline Development Stratified 5-Fold Cross-Validation",
            "scope": "Development 800 examples",
            "oof_rows": 800,
            "correct": 730,
            "errors": 70,
            "oof_metrics": {
                "accuracy": 0.91250000,
                "macro_precision": 0.93456081,
                "macro_recall": 0.89567678,
                "macro_f1": 0.91355855,
                "weighted_precision": 0.91474247,
                "weighted_recall": 0.91250000,
                "weighted_f1": 0.91247033
            },
            "fold_mean_sample_sd": {
                "accuracy": "0.91250000 ± 0.01397542",
                "macro_precision": "0.93883481 ± 0.01566618",
                "macro_recall": "0.89436763 ± 0.02618612",
                "macro_f1": "0.90846876 ± 0.02069854",
                "weighted_precision": "0.91847530 ± 0.01429771",
                "weighted_recall": "0.91250000 ± 0.01397542",
                "weighted_f1": "0.91044731 ± 0.01349372"
            },
            "error_decision": "ACCEPT CURRENT BASELINE NLU (NO DEVELOPMENT DATASET CHANGE REQUIRED, NO NLU PIPELINE TUNING REQUIRED)"
        },
        "baseline_entity_evaluation": {
            "semantics": "TOKEN_LEVEL_DIET_EVALUATION",
            "macro_precision": "0.4199 ± 0.0921",
            "macro_recall": "0.5938 ± 0.1582",
            "macro_f1": "0.4568 ± 0.0761",
            "weighted_precision": "0.4870 ± 0.0714",
            "weighted_recall": "0.6443 ± 0.1306",
            "weighted_f1": "0.5264 ± 0.0481",
            "micro_f1": "0.5288 ± 0.0742",
            "per_entity_mean_sd": {
                "component_type": {"precision": "0.5414 ± 0.1240", "recall": "0.7470 ± 0.2533", "f1": "0.6116 ± 0.1577"},
                "budget": {"precision": "0.3490 ± 0.1009", "recall": "0.7379 ± 0.1246", "f1": "0.4667 ± 0.0996"},
                "usage": {"precision": "0.4953 ± 0.1634", "recall": "0.5819 ± 0.1032", "f1": "0.5271 ± 0.1316"},
                "future_upgrade": {"precision": "0.2940 ± 0.3640", "recall": "0.3082 ± 0.3757", "f1": "0.2217 ± 0.2934"}
            }
        },
        "final_model": {
            "path": "final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz",
            "sha256": model_sha,
            "size_bytes": 43774326,
            "training_examples": 800,
            "training_invocations": 1,
            "training_exit_code": 0,
            "training_elapsed_seconds": 3594.66
        },
        "final_holdout_evaluation": {
            "evaluation_name": "One-Time Locked Holdout 200 Final Evaluation",
            "type": "ONE_TIME_LOCKED_HOLDOUT_FINAL_TEST",
            "holdout_rows": 200,
            "correct": 141,
            "errors": 59,
            "intent_metrics": {
                "accuracy": 0.70500000,
                "macro_precision": 0.78831203,
                "macro_recall": 0.71515891,
                "macro_f1": 0.72564964,
                "weighted_precision": 0.75312253,
                "weighted_recall": 0.70500000,
                "weighted_f1": 0.70027716
            },
            "fallback_observation": {
                "count": 10,
                "rate": 0.05,
                "description": "FallbackClassifier was triggered on 10 Holdout utterances according to the configured fallback decision criteria (confidence < 0.3)"
            },
            "entity_evidence": {
                "semantics": "TOKEN_LEVEL_DIET_EVALUATION",
                "coverage": "BUDGET_ANNOTATIONS_ONLY",
                "gold_spans": 15,
                "token_support": 15,
                "metrics": {
                    "precision": 0.1000,
                    "recall": 0.0667,
                    "f1_score": 0.0800
                },
                "limitation": "The Holdout entity evaluation contained 15 annotated budget spans; observed final entity metrics reflect only the budget entity present in evaluable Holdout evidence."
            },
            "cv_vs_holdout_comparison": {
                "accuracy": {"cv_mean": 0.91250000, "holdout": 0.70500000, "delta": -0.20750000},
                "macro_f1": {"cv_mean": 0.90846876, "holdout": 0.72564964, "delta": -0.18281912}
            }
        },
        "runtime_verification": {
            "total_cases": 8,
            "passed": 8,
            "failed": 0,
            "status": "FINAL_MODEL_RUNTIME_LOCKED"
        },
        "system_e2e_verification": {
            "total_cases": 16,
            "passed": 16,
            "failed": 0,
            "verification_level": "BACKEND_E2E_VERIFIED_LIVE_LINE_NOT_VERIFIED",
            "hardware_catalog_records": 64,
            "hardware_catalog_sha256": hw_sha
        },
        "security_status": {
            "tracked_active_secrets": 0,
            "credential_source": "ENVIRONMENT_VARIABLES (LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN)",
            "signature_verification": "IMPLEMENTED_AND_VERIFIED (HMAC-SHA256 via linebot.WebhookParser)",
            "credential_rotation_required": True,
            "credential_rotation_completed": "UNKNOWN",
            "production_action": "PRODUCTION SECURITY ACTION OUTSTANDING (Rotate tokens before public deployment)"
        },
        "analytics_status": {
            "database_path": "data/analytics.db",
            "technology": "SQLite",
            "table": "user_searches",
            "columns": ["id", "timestamp", "user_id", "usage_type", "budget_requested", "allocated_total_price"],
            "storage_scope": "STRUCTURED_AGGREGATE_METRICS_ONLY (No raw personal chat transcripts stored)"
        }
    }
    
    master_json_p = master_dir / "master-final-values.json"
    with open(master_json_p, "w", encoding="utf-8") as fp:
        json.dump(master_json_data, fp, indent=2, ensure_ascii=False)
        
    # 3. Build Report Safe Claims (report-safe-claims.md)
    claims_md = """# SpecFlow Report-Safe Claims Reference Guide
## Single Source of Truth for Thesis Writing (Chapters 3, 4, and 5)

## 1. Approved Claims (Fully Supported by Physical Evidence)
- **Development Dataset**: Contains 800 examples across 15 intents with an intentionally unequal distribution reflecting the designed intent domain.
- **Holdout Dataset**: Unseen evaluation set containing 200 examples across 15 intents with zero duplicate overlap with Development.
- **Baseline 5-Fold Cross-Validation**: Achieved OOF Accuracy of **0.9125** (91.25%) and OOF Macro F1 of **0.9136** (91.36%) across the 800 Development examples.
- **Final Model Training**: Trained once on 100% of Development 800 (59.9 minutes, 0 errors, SHA: `86a76534...`).
- **Final Holdout Intent Performance**: Achieved Accuracy of **0.7050** (70.50%) and Macro F1 of **0.7256** (72.56%) on the locked 200-example Holdout set (141 correct, 59 errors).
- **Runtime Verification**: Passed 8/8 test cases verifying model loading, multi-turn forms, Action Server integration, and recommendation generation.
- **System Verification**: Passed 16/16 functional cases verifying full backend architecture, database lookups, fallback routing, and non-sensitive analytics.
- **Hardware Database**: Contains 64 physical component records across 8 categories (CPU: 14, GPU: 12, Motherboard: 10, RAM: 8, Storage: 5, PSU: 6, Case: 5, Cooler: 4).

## 2. Qualified Claims (Must Include Required Engineering Nuance)
- **Entity Extraction Evaluation**: Must be explicitly described as **token-level DIET evaluation** across sub-words/syllables, not span-level F1.
- **Holdout Entity Performance**: The Holdout entity metrics (`Precision: 0.1000`, `Recall: 0.0667`, `F1: 0.0800`) reflect **only the 15 `budget` entity annotations** present in the evaluable Holdout evidence.
- **LINE Integration**: Must be classified as **Backend E2E Verified, Live LINE Platform Delivery Not Proven** (connector and signature logic verified locally; live external webhook calls not executed).
- **Recommendation Engine**: Budget optimization is **budget-aware with tolerance warning**, not guaranteed to strictly equal or fall below the target budget.
- **Security Posture**: Repository is sanitized (0 tracked active secrets, env var loading), but credential rotation in the LINE Console is marked as **Production Security Action Outstanding**.
- **Analytics Storage**: Stores structured usage metrics (`usage_type`, `budget_requested`, `allocated_total_price`); does not store full conversational transcripts.

## 3. Forbidden / Unsupported Claims (Strictly Prohibited)
- **DO NOT claim**: Final Model Accuracy is 91.25% (91.25% is the Development 5-Fold CV baseline, not final Holdout).
- **DO NOT claim**: Final Holdout Macro F1 is ~90% (Final Holdout Macro F1 is 72.56%).
- **DO NOT claim**: The Development dataset is "balanced" (Distribution is intentionally non-uniform).
- **DO NOT claim**: Holdout fallback utterances were "Out-of-Distribution (OOD)" (Correct statement: FallbackClassifier triggered on 10 Holdout utterances per configured confidence threshold).
- **DO NOT claim**: Final Entity F1 of 0.08 represents all 4 entity types (It represents only `budget`).
- **DO NOT claim**: Live LINE end-to-end messaging was verified in production.
- **DO NOT claim**: ResponseSelector handles general FAQ intents (FAQs are handled via Custom Actions).
- **DO NOT claim**: Credential rotation is complete without external administrative verification.
"""
    with open(master_dir / "report-safe-claims.md", "w", encoding="utf-8") as fp:
        fp.write(claims_md)
        
    # 4. Build Chapter 3 Facts (chapter-3-facts.md)
    ch3_md = f"""# Chapter 3 Facts Sheet — Methodology & System Development
## Source of Truth for Thesis Chapter 3

### 1. System Architecture
- **Framework**: Rasa Open Source 3.6.21 + Rasa SDK 3.6.2 (Python 3.9.6).
- **Data Flow**: `LINE User` → `LINE Messaging API` → `LineInput (app/rasa/line_channel.py)` → `Rasa Server (NLU Pipeline + Policies)` → `Rasa Action Server (port 5055, app/rasa/actions/actions.py)` → `SpecRecommender / UpgradeAdvisor (app/services/recommendation/)` → `hardware_db.json` → `Flex Message Builder (app/rasa/actions/flex.py)` → `Analytics DB (data/analytics.db)` → `LINE User`.

### 2. Final NLU Pipeline Configuration (`app/rasa/config.yml`)
1. `ThaiTokenizer` (PyThaiNLP `newmm` word segmentation engine).
2. `RegexFeaturizer`
3. `LexicalSyntacticFeaturizer`
4. `CountVectorsFeaturizer` (analyzer: `word`, min_ngram: 1, max_ngram: 1)
5. `CountVectorsFeaturizer` (analyzer: `char_wb`, min_ngram: 1, max_ngram: 4)
6. `DIETClassifier` (epochs: 100, constrain_similarities: True)
7. `EntitySynonymMapper`
8. `ResponseSelector` (epochs: 100, constrain_similarities: True)
9. `FallbackClassifier` (threshold: 0.3, ambiguity_threshold: 0.1)

### 3. Dialogue Policies Configuration (`app/rasa/config.yml`)
1. `MemoizationPolicy` (max_history: 5)
2. `RulePolicy` (core_fallback_threshold: 0.3, core_fallback_action_name: `action_default_fallback`)
3. `UnexpecTEDIntentPolicy` (max_history: 5, epochs: 100)
4. `TEDPolicy` (max_history: 5, epochs: 100, constrain_similarities: True)

### 4. Domain Definition (`app/rasa/domain.yml`)
- **Intents (15)**: `greet`, `goodbye`, `build_pc`, `upgrade_pc`, `inform_budget`, `inform_usage`, `inform_current_specs`, `ask_cpu_info`, `ask_gpu_info`, `ask_ram_info`, `ask_ssd_hdd_diff`, `optimize_performance`, `inform_future_upgrade`, `affirm`, `deny`.
- **Entities (4)**: `component_type`, `budget`, `usage`, `future_upgrade`.
- **Slots (4)**: `budget` (text), `usage` (text), `current_specs` (text), `future_upgrade` (bool).
- **Forms (2)**:
  - `build_pc_form`: slot filling order: `budget` → `usage` → `future_upgrade` → triggers `action_recommend_pc`.
  - `upgrade_pc_form`: slot filling order: `usage` → `current_specs` → triggers `action_recommend_upgrade`.

### 5. Custom Actions (`app/rasa/actions/actions.py`)
- `action_recommend_pc`: Executes `SpecRecommender`, builds Flex spec card, resets slots.
- `action_recommend_upgrade`: Executes `UpgradeAdvisor`, analyzes hardware bottlenecks, resets slots.
- `action_cpu_info`, `action_gpu_info`, `action_ram_info`, `action_ssd_hdd_diff`: FAQ informational actions.
- `action_optimize_performance`: Troubleshooting and OS optimization recommendations.

### 6. Hardware Catalog (`hardware_db.json`, SHA: `{hw_sha}`)
- Total catalog: **64 records** (CPU: 14, GPU: 12, Motherboard: 10, RAM: 8, Storage: 5, PSU: 6, Case: 5, Cooler: 4).
- Compatibility rules: Socket matching (AM4, AM5, LGA1700), RAM generation (DDR4, DDR5), PSU sizing, form factor matching.

### 7. Security Architecture
- Secret storage: Loaded from environment variables (`${{LINE_CHANNEL_SECRET}}`, `${{LINE_CHANNEL_ACCESS_TOKEN}}`).
- Signature verification: HMAC-SHA256 implemented in `LineInput` via `linebot.WebhookParser`.
"""
    with open(master_dir / "chapter-3-facts.md", "w", encoding="utf-8") as fp:
        fp.write(ch3_md)
        
    # 5. Build Chapter 4 Facts (chapter-4-facts.md)
    ch4_md = """# Chapter 4 Facts Sheet — Results
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
"""
    with open(master_dir / "chapter-4-facts.md", "w", encoding="utf-8") as fp:
        fp.write(ch4_md)
        
    # 6. Build Chapter 5 Facts (chapter-5-facts.md)
    ch5_md = """# Chapter 5 Facts Sheet — Discussion, Limitations & Future Work
## Source of Truth for Thesis Chapter 5 Discussion

## 1. Supported Discussion Findings
- **Generalization Gap**: Final Holdout test performance (Accuracy: 70.50%, Macro F1: 72.56%) was lower than Development 5-Fold cross-validation (Accuracy: 91.25%, Macro F1: 90.85%). This reveals a true out-of-sample generalization gap when exposed to unseen phrasing variations and salt noise in the independent test set.
- **Intent Strength Variations**:
  - High-performing intents on Holdout: `inform_current_specs` (Recall 1.0000, F1 0.8947), `upgrade_pc` (Recall 0.9310, F1 0.7013), `ask_ram_info` (F1 0.9091), `ask_ssd_hdd_diff` (F1 0.9091), `greet` (F1 0.9091).
  - Challenging intents on Holdout: `ask_gpu_info` (F1 0.4444), `inform_budget` (F1 0.5294), `optimize_performance` (Recall 0.4400), `inform_future_upgrade` (Recall 0.4286).
- **Fallback Classifier Utility**: FallbackClassifier successfully captured 10 low-confidence Holdout utterances (5.00%), preventing incorrect action routing and delivering user guidance.
- **Entity Extraction vs Intent Classification**: Entity extraction showed lower performance than intent classification across both Development (Macro F1 0.4568) and Holdout (`budget` F1 0.0800), attributable to token-level segmentation challenges in complex Thai technical compounding.
- **Dialogue & System Reliability**: Despite NLU variation, conversational multi-turn forms (`build_pc_form`, `upgrade_pc_form`) and slot-filling mechanisms successfully handled user dialogues and triggered hardware recommendation algorithms without failure in all runtime/functional tests.

## 2. Limitations
- **Token-Level Entity Representation**: Rasa evaluates DIET entities at the sub-word/token level rather than exact whole-phrase span matching.
- **Holdout Entity Annotation Scope**: The independent Holdout set contained evaluable entity annotations only for the `budget` entity (15 spans); entity generalization for `component_type`, `usage`, and `future_upgrade` was not separately measured on Holdout.
- **Offline Backend Verification**: Live external delivery through the LINE platform was not tested in this offline environment (evaluated as Backend E2E verified).
- **Credential Rotation Status**: Production security action (manual secret rotation in LINE Developers Console) remains outstanding.

## 3. Recommended Future Work
- **NLU Data Expansion**: Broaden training examples for overlapping intents (`inform_future_upgrade` vs `upgrade_pc`, `optimize_performance`).
- **Compound Entity Normalization**: Introduce specialized Thai hardware dictionary tokenization and character-level entity post-processing.
- **Complete Test Set Entity Tagging**: Fully annotate all 4 entity types across independent evaluation sets.
- **Live Production Telemetry**: Deploy in a staging LINE Official Account with live webhook monitoring and analytics tracking.
"""
    with open(master_dir / "chapter-5-facts.md", "w", encoding="utf-8") as fp:
        fp.write(ch5_md)
        
    # 7. Build Master Final Values Markdown (master-final-values.md)
    master_md = f"""# SpecFlow — Master Final Values Summary
## Authoritative Single Source of Truth for Thesis Chapters 3–5

## Master Values Table
| Dimension / Parameter | Authoritative Final Value | Evidence Source |
| :--- | :--- | :--- |
| **Project Name** | SpecFlow | Physical Repository |
| **System Domain** | Thai Conversational PC Spec Recommender | Architecture / Domain |
| **Primary Channel** | LINE Official Account | `line_channel.py` / `credentials.yml` |
| **Python Version** | `3.9.6` | Runtime Environment |
| **Rasa Version** | `3.6.21` | Runtime Environment |
| **rasa-sdk Version** | `3.6.2` | Runtime Environment |
| **PyThaiNLP Version** | `5.3.4` | Runtime Environment |
| **Development Dataset Rows** | `800` examples (15 intents) | `app/rasa/data/nlu.yml` (`{dev_sha[:12]}...`) |
| **Development Entity Spans** | `187` spans (4 types) | `entity-baseline-evidence.md` |
| **Holdout Dataset Rows** | `200` examples (15 intents) | `locked-holdout-v1.yml` (`{holdout_sha[:12]}...`) |
| **Holdout Evaluation Count** | `1` (Single authorized evaluation) | `final-holdout-evaluation-manifest.json` |
| **Development CV Accuracy (OOF)** | `0.91250000` (91.25%, 730/800) | `oof-predictions.csv` |
| **Development CV Macro F1 (OOF)** | `0.91355855` (91.36%) | `oof-predictions.csv` |
| **Development CV 5-Fold Mean Accuracy** | `0.91250000 ± 0.01397542` | `cv-summary-metrics.json` |
| **Development CV 5-Fold Mean Macro F1** | `0.90846876 ± 0.02069854` | `cv-summary-metrics.json` |
| **Development Entity Macro F1** | `0.4568 ± 0.0761` (Token-level DIET) | `entity-aggregate-metrics.json` |
| **Final Model Path** | `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz` | Physical Model Artifact |
| **Final Model SHA-256** | `{model_sha}` | `final-model-training-manifest.json` |
| **Final Model Training Time** | `3594.66` seconds (59.9 min) | `final-model-training-manifest.json` |
| **Runtime Verification Cases** | `8 / 8 PASS` | `final-model-runtime-verification-manifest.json` |
| **Holdout Test Correct** | `141` | `holdout-predictions.csv` |
| **Holdout Test Errors** | `59` | `holdout-errors.csv` |
| **Final Test Accuracy** | `0.70500000` (70.50%) | `holdout-intent-metrics.json` |
| **Final Test Macro Precision** | `0.78831203` (78.83%) | `holdout-intent-metrics.json` |
| **Final Test Macro Recall** | `0.71515891` (71.52%) | `holdout-intent-metrics.json` |
| **Final Test Macro F1-Score** | `0.72564964` (72.56%) | `holdout-intent-metrics.json` |
| **Final Test Weighted Precision** | `0.75312253` (75.31%) | `holdout-intent-metrics.json` |
| **Final Test Weighted Recall** | `0.70500000` (70.50%) | `holdout-intent-metrics.json` |
| **Final Test Weighted F1-Score** | `0.70027716` (70.03%) | `holdout-intent-metrics.json` |
| **Holdout Fallback Count / Rate** | `10` / `5.00%` | `holdout-intent-metrics.json` |
| **Holdout Entity Scope** | `budget` entity only (`F1: 0.0800`) | `holdout-entity-evidence.json` |
| **System Functional Cases** | `16 / 16 PASS` | `system-e2e-evidence-manifest.json` |
| **Hardware Catalog Records** | `64` records (8 categories) | `hardware_db.json` (`{hw_sha[:12]}...`) |
| **LINE E2E Verification Level** | `BACKEND E2E VERIFIED` (Live not proven) | `integration-test-results.json` |
| **Tracked Active Secrets** | `0` (Environment variable loading) | `security-evidence.json` |
| **Credential Rotation Status** | `REQUIRED (Outstanding action)` | `security-evidence.json` |
| **Analytics Database** | SQLite `user_searches` (Metric fields only) | `data/analytics.db` |

## Master Evidence Files
- **[master-final-values.json](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/master-final-values.json)**
- **[chapter-3-facts.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-3-facts.md)**
- **[chapter-4-facts.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-4-facts.md)**
- **[chapter-5-facts.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-5-facts.md)**
- **[report-safe-claims.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/report-safe-claims.md)**
- **[master-final-values-manifest.json](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/master-final-values-manifest.json)**
"""
    with open(master_dir / "master-final-values.md", "w", encoding="utf-8") as fp:
        fp.write(master_md)
        
    # 8. Build Master Manifest (master-final-values-manifest.json)
    manifest_data = {
        "master_id": "specflow_master_final_values_v1",
        "timestamp": datetime.datetime.now().astimezone().isoformat(),
        "source_evidence": {
            "development": {"path": "app/rasa/data/nlu.yml", "sha256": dev_sha},
            "holdout": {"path": "docs/dataset-engineering/holdout/locked-holdout-v1.yml", "sha256": holdout_sha},
            "baseline_cv": {"manifest": "docs/dataset-engineering/cross-validation/baseline/results/baseline-cv-manifest.json"},
            "error_decision": {"record": "docs/dataset-engineering/error-analysis/baseline-error-analysis/error-decision-record.json"},
            "entity_baseline": {"manifest": "docs/dataset-engineering/entity-evaluation/baseline/entity-baseline-evidence-manifest.json"},
            "final_configuration": {"manifest": "docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json", "sha256": "aaa9aaf7408032147995bd42c1f1ed822d26bc837e405c093727a0843769cc2c"},
            "final_training": {"manifest": "docs/final-readiness/final-model-training/run-20260825-001846/final-model-training-manifest.json", "sha256": "4bd8ef1f1879c093c0be00abff0737e3f8512d82e10e00325dedddf62aea121c"},
            "runtime_verification": {"manifest": "docs/final-readiness/final-model-runtime-verification/run-20260825-012754/final-model-runtime-verification-manifest.json", "sha256": "15056ebdb4290af0ca09f8a9702faca45c00195f05c14a14ce218313ca849939"},
            "final_holdout": {"manifest": "docs/final-readiness/final-holdout-evaluation/run-20260825-013923/final-holdout-evaluation-manifest.json", "sha256": "864013f9d5b7667b5bd81bdc3817d1ddaa4c2b8bec7c692b8899066847875716"},
            "system_e2e": {"manifest": "docs/final-readiness/system-e2e-evidence/run-20260825-014623/system-e2e-evidence-manifest.json", "sha256": "7d7a256f530884c73ec01abb763b75de8788845aec40b97bb849ddbaef7c3d28"}
        },
        "final_dataset_values": master_json_data["datasets"],
        "final_runtime_values": master_json_data["runtime_environment"],
        "baseline_cv_metrics": master_json_data["baseline_stratified_5fold_cv"],
        "baseline_entity_metrics": master_json_data["baseline_entity_evaluation"],
        "final_holdout_metrics": master_json_data["final_holdout_evaluation"],
        "runtime_test_results": master_json_data["runtime_verification"],
        "system_test_results": master_json_data["system_e2e_verification"],
        "security_status": master_json_data["security_status"],
        "analytics_status": master_json_data["analytics_status"],
        "reporting_constraints": {
            "chapter3_fact_sheet": "docs/final-readiness/master-final-values/chapter-3-facts.md",
            "chapter4_fact_sheet": "docs/final-readiness/master-final-values/chapter-4-facts.md",
            "chapter5_fact_sheet": "docs/final-readiness/master-final-values/chapter-5-facts.md",
            "report_safe_claims": "docs/final-readiness/master-final-values/report-safe-claims.md"
        },
        "post_holdout": {
            "training_executed": False,
            "tuning_performed": False,
            "holdout_reevaluated": False
        }
    }
    manifest_p = master_dir / "master-final-values-manifest.json"
    with open(manifest_p, "w", encoding="utf-8") as fp:
        json.dump(manifest_data, fp, indent=2, ensure_ascii=False)
        
    # Reopen and compute SHA-256 for all 7 files
    files = [
        master_json_p,
        master_dir / "master-final-values.md",
        master_dir / "chapter-3-facts.md",
        master_dir / "chapter-4-facts.md",
        master_dir / "chapter-5-facts.md",
        master_dir / "report-safe-claims.md",
        manifest_p
    ]
    for p in files:
        assert p.exists()
        assert p.stat().st_size > 0
        sha = get_file_sha256(p)
        print(f"Verified: {p.name:36s} | Size: {p.stat().st_size:7d} bytes | SHA: {sha}")
        
    print("\nMASTER FINAL VALUES SUMMARY COMPLETE")

if __name__ == "__main__":
    main()
