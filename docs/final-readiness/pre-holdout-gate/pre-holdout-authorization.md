# Pre-Holdout Authorization Record
## SpecFlow Final Model Evaluation Authorization (Gate ID: `specflow_pre_holdout_gate_v1`)

## 1. Authorization Scope
This document formally records the final read-only governance authorization for the **ONE-TIME evaluation of the Locked Holdout 200 dataset** against the canonical **Final Model** (`20260825-001851-woolen-billet.tar.gz`).

## 2. Experimental Locks Verification
- **Development 800**: `app/rasa/data/nlu.yml` (SHA: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`) → **FINAL LOCKED**
- **Baseline Intent CV**: `docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv` (SHA: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47`) → **FINAL LOCKED**
- **Error Decision**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/error-decision-record.json` → **CLOSED (ACCEPT BASELINE NLU)**
- **Entity Baseline Evidence**: `docs/dataset-engineering/entity-evaluation/baseline/entity-baseline-evidence-manifest.json` (SHA: `c40c1bf5227271aa57da4fd92dd487c65de5b59d11d7a3f9ad1661f66497c4fc`) → **CLOSED (APPROVED FOR CHAPTER 4)**
- **Final Configuration Freeze**: `docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json` (SHA: `aaa9aaf7408032147995bd42c1f1ed822d26bc837e405c093727a0843769cc2c`) → **FINAL LOCKED**
- **Final Model Artifact**: `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz` (SHA: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7`) → **FINAL LOCKED**
- **Runtime Verification**: `docs/final-readiness/final-model-runtime-verification/run-20260825-012754/final-model-runtime-verification-manifest.json` (SHA: `15056ebdb4290af0ca09f8a9702faca45c00195f05c14a14ce218313ca849939`) → **8/8 PASS**
- **Locked Holdout 200**: `docs/dataset-engineering/holdout/locked-holdout-v1.yml` (SHA: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`) → **LOCKED / UNEVALUATED**

## 3. Pre-Holdout Gate Matrix
| Check Item | Requirement | Observed State | Status |
| :--- | :--- | :--- | :---: |
| **Development 800 Integrity** | Match SHA `37b05d1f...` | `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d` | **PASS** |
| **Holdout 200 Integrity** | Match SHA `61d0c3c2...` | `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961` | **PASS** |
| **Holdout Isolation** | Evaluated count = 0 | Evaluated = NO, Tuning usage = NO | **PASS** |
| **Baseline Intent CV Lock** | OOF SHA `b66e9e0e...` | `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47` (Acc: 0.9125, Macro F1: 0.9136) | **PASS** |
| **Error Decision Gate** | Closed decision | ACCEPT BASELINE NLU (No dataset/pipeline change) | **PASS** |
| **Entity Baseline Evidence** | Consolidated 5-Fold metrics | Token-level DIET evaluation approved | **PASS** |
| **Final Config Lineage** | Freeze SHA `aaa9aaf7...` | All 5 training input SHAs strictly identical | **PASS** |
| **Final Model Lineage** | Model SHA `86a76534...` | Produced from 1 authorized training run | **PASS** |
| **Runtime Verification** | 8/8 test cases pass | Forms, Fallback, Action Server verified | **PASS** |
| **Fallback Wiring** | `nlu_fallback` → `utter_fallback` | Thresholds 0.3 / 0.1, rule wired & tested | **PASS** |
| **Security Sanitization** | 0 active secrets in source | Environment variable interpolation verified | **PASS** |
| **Open Decisions** | 0 unresolved design choices | Dev=NO, NLU=NO, Model=NO, Config=NO | **PASS** |

## 4. Holdout One-Time Policy Acknowledgment
> **MANDATORY POLICY STATEMENT**:  
> The Locked Holdout 200 dataset will be evaluated exactly once against the locked Final Model.  
> Following evaluation, NO hyperparameter tuning, NO dataset modifications, and NO retraining will be permitted.  
> The resulting metrics represent the definitive, unbiased test performance for the thesis/report.

## 5. Final Authorization Decision

> **AUTHORIZED FOR ONE-TIME LOCKED HOLDOUT 200 EVALUATION**
