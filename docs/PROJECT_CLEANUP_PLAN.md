# SpecFlow Project Cleanup Plan
## Post-Holdout / Post-Evidence Cleanup Decision Matrix

| Path / Target | Classification | Reason | Referenced By | Action |
| :--- | :--- | :--- | :--- | :---: |
| `app/rasa/data/nlu.yml` | `KEEP_REQUIRED` | Final Locked Development Dataset (800 examples) | `final-configuration-freeze-manifest.json`, `master-final-values-manifest.json` | **KEEP** |
| `docs/dataset-engineering/holdout/locked-holdout-v1.yml` | `KEEP_REQUIRED` | Final Locked Holdout Dataset (200 examples) | `final-holdout-evaluation-manifest.json`, `master-final-values-manifest.json` | **KEEP** |
| `final_models/run-20260825-001846/` | `KEEP_REQUIRED` | Authoritative Final Model archive & training manifest | `master-final-values-manifest.json` | **KEEP** |
| `app/rasa/config.yml` | `KEEP_REQUIRED` | Final Frozen Rasa Pipeline & Dialogue Policies | `final-configuration-freeze-manifest.json` | **KEEP** |
| `app/rasa/domain.yml` | `KEEP_REQUIRED` | Final Frozen Rasa Domain | `final-configuration-freeze-manifest.json` | **KEEP** |
| `app/rasa/data/rules.yml` | `KEEP_REQUIRED` | Final Frozen Rasa Rules (Fallback + Form rules) | `final-configuration-freeze-manifest.json` | **KEEP** |
| `app/rasa/data/stories.yml` | `KEEP_REQUIRED` | Final Frozen Rasa Stories | `final-configuration-freeze-manifest.json` | **KEEP** |
| `app/rasa/credentials.yml` | `KEEP_REQUIRED` | Secure environment-variable credential mappings | `system-e2e-evidence-manifest.json` | **KEEP** |
| `app/rasa/endpoints.yml` | `KEEP_REQUIRED` | Action Server and core endpoints configuration | Runtime System Architecture | **KEEP** |
| `app/rasa/line_channel.py` | `KEEP_REQUIRED` | Custom LINE Webhook Channel with signature verification | `system-e2e-evidence-manifest.json` | **KEEP** |
| `app/rasa/thai_tokenizer.py` | `KEEP_REQUIRED` | Custom PyThaiNLP NLU Tokenizer component | `config.yml` | **KEEP** |
| `app/rasa/actions/` | `KEEP_REQUIRED` | Custom Action Server logic & Flex Message builders | `system-e2e-evidence-manifest.json` | **KEEP** |
| `app/services/` | `KEEP_REQUIRED` | Core recommendation engines & NLP preprocessing | `system-e2e-evidence-manifest.json` | **KEEP** |
| `data/analytics.db` | `KEEP_REQUIRED` | SQLite analytics database for user queries | `system-e2e-evidence-manifest.json` | **KEEP** |
| `cv_results/` | `KEEP_REPRODUCIBILITY` | Baseline 5-Fold Cross-Validation models & fold reports | `entity-baseline-evidence-manifest.json`, `baseline-cv-manifest.json` | **KEEP** |
| `docs/dataset-engineering/cross-validation/baseline/` | `KEEP_REPRODUCIBILITY` | Locked Baseline 5-Fold CV metrics, OOF predictions | `master-final-values-manifest.json` | **KEEP** |
| `docs/dataset-engineering/entity-evaluation/baseline/` | `KEEP_REPRODUCIBILITY` | Locked Entity Baseline evidence and fold CSVs | `master-final-values-manifest.json` | **KEEP** |
| `docs/final-readiness/pre-holdout-gate/` | `KEEP_REPRODUCIBILITY` | Pre-Holdout authorization artifacts | `master-final-values-manifest.json` | **KEEP** |
| `docs/final-readiness/final-holdout-evaluation/run-20260825-013923/` | `KEEP_REPRODUCIBILITY` | Authoritative Final Holdout evaluation results & charts | `master-final-values-manifest.json` | **KEEP** |
| `docs/final-readiness/system-e2e-evidence/run-20260825-014623/` | `KEEP_REPRODUCIBILITY` | Authoritative System E2E verification artifacts (16/16 PASS) | `master-final-values-manifest.json` | **KEEP** |
| `docs/final-readiness/master-final-values/` | `KEEP_REPRODUCIBILITY` | Authoritative Single Source of Truth for Thesis | `master-final-values-manifest.json` | **KEEP** |
| `.venv-rasa-cv/` | `KEEP_REQUIRED` | Local virtual environment for Python 3.9.6 runtime | Local Execution (Untracked) | **KEEP** |
| `.DS_Store` (all instances) | `SAFE_DELETE_CACHE` | macOS filesystem metadata files | None | **DELETE** |
| `.rasa/` | `SAFE_DELETE_CACHE` | Rasa runtime cache and telemetry logs | None | **DELETE** |
| `tmp_holdout_eval_20260825-013559/` | `SAFE_DELETE_TEMPORARY` | Empty temporary directory | None | **DELETE** |
| `tmp_holdout_eval_20260825-013611/` | `SAFE_DELETE_TEMPORARY` | Empty temporary directory | None | **DELETE** |
| `tmp_holdout_eval_20260825-013629/` | `SAFE_DELETE_TEMPORARY` | Temporary scratch files from pre-inference format testing | None | **DELETE** |
| `tmp_holdout_eval_20260825-013835/` | `SAFE_DELETE_TEMPORARY` | Temporary scratch files from pre-inference format testing | None | **DELETE** |
| `tmp/` | `SAFE_DELETE_TEMPORARY` | Obsolete dataset merge scripts and intermediate YAMLs | None | **DELETE** |
| `tmp_salvage/` | `SAFE_DELETE_TEMPORARY` | Intermediate fold salvage artifacts (final merged in cv_results) | None | **DELETE** |
| `recover_and_build.py` | `SAFE_DELETE_TEMPORARY` | Scratch recovery script (official scripts in docs/dataset-engineering/scripts/) | None | **DELETE** |
| `run_cv.py` | `SAFE_DELETE_TEMPORARY` | Scratch CV script (official scripts in docs/dataset-engineering/scripts/) | None | **DELETE** |
| `cv_canary/` | `SAFE_DELETE_TEMPORARY` | Early exploratory canary fold not referenced in final evidence | None | **DELETE** |
| `app/rasa/data/nlu_350_recovered.yml` | `SAFE_DELETE_TEMPORARY` | Intermediate dataset reconstruction file | None | **DELETE** |
| `app/rasa/data/nlu_600.yml` | `SAFE_DELETE_TEMPORARY` | Intermediate dataset reconstruction file | None | **DELETE** |
| `app/rasa/data/nlu_800.yml` | `SAFE_DELETE_TEMPORARY` | Intermediate dataset reconstruction file | None | **DELETE** |
| `app/rasa/data/nlu_pre_clean_rebuild.yml` | `SAFE_DELETE_TEMPORARY` | Intermediate dataset reconstruction file | None | **DELETE** |
| `docs/final-readiness/final-holdout-evaluation/run-20260825-013559/` | `SAFE_DELETE_TEMPORARY` | Incomplete startup attempt log without predictions/manifest | None | **DELETE** |
| `docs/final-readiness/final-holdout-evaluation/run-20260825-013611/` | `SAFE_DELETE_TEMPORARY` | Incomplete startup attempt log without predictions/manifest | None | **DELETE** |
| `docs/final-readiness/final-holdout-evaluation/run-20260825-013629/` | `SAFE_DELETE_TEMPORARY` | Technical preparation run prior to final evaluation harness | None | **DELETE** |
| `docs/final-readiness/final-holdout-evaluation/run-20260825-013835/` | `SAFE_DELETE_TEMPORARY` | Technical preparation run prior to final evaluation harness | None | **DELETE** |
| `docs/final-readiness/system-e2e-evidence/run-20260825-014327/` | `SAFE_DELETE_TEMPORARY` | Incomplete pre-execution run without results/manifest | None | **DELETE** |
| `docs/final-readiness/system-e2e-evidence/run-20260825-014416/` | `SAFE_DELETE_TEMPORARY` | Incomplete pre-execution run without results/manifest | None | **DELETE** |
| `docs/final-readiness/system-e2e-evidence/run-20260825-014455/` | `SAFE_DELETE_TEMPORARY` | Incomplete pre-execution run without results/manifest | None | **DELETE** |
| `docs/final-readiness/system-e2e-evidence/run-20260825-014535/` | `SAFE_DELETE_TEMPORARY` | Preliminary test run (15/16) superseded by authoritative run-20260825-014623 (16/16) | None | **DELETE** |
