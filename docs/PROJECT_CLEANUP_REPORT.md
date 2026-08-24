# SpecFlow Project Cleanup Report
## Post-Holdout / Post-Evidence Cleanup Audit

- **Date**: 2026-08-25
- **Branch**: `main`
- **Cleanup Strategy**: Safe deletion of temporary artifacts, intermediate recovery files, and macOS filesystem caches while 100% preserving authoritative provenance and reproducibility files.

---

## 1. Cleanup Summary

- **Files Deleted (10)**:
  - 4 macOS cache files: `.DS_Store` across repository tree
  - 4 Intermediate recovery YAMLs: `nlu_350_recovered.yml`, `nlu_600.yml`, `nlu_800.yml`, `nlu_pre_clean_rebuild.yml`
  - 2 Scratch scripts: `recover_and_build.py`, `run_cv.py` (authoritative scripts preserved in `docs/dataset-engineering/scripts/`)
- **Directories Deleted (16)**:
  - Local runtime cache: `.rasa` (1)
  - Temporary evaluation scratch dirs: `tmp_holdout_eval_20260825-013559`, `tmp_holdout_eval_20260825-013611`, `tmp_holdout_eval_20260825-013629`, `tmp_holdout_eval_20260825-013835` (4)
  - Temporary development scratch dirs: `tmp`, `tmp_salvage`, `cv_canary` (3)
  - Incomplete/technical preparation Holdout runs: `final-holdout-evaluation/run-20260825-013559`, `run-20260825-013611`, `run-20260825-013629`, `run-20260825-013835` (4)
  - Incomplete/preliminary System E2E runs: `system-e2e-evidence/run-20260825-014327`, `run-20260825-014416`, `run-20260825-014455`, `run-20260825-014535` (4)

---

## 2. Preserved Critical Artifacts & Provenance

- **Development Dataset**: `app/rasa/data/nlu.yml` (800 examples, SHA: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`)
- **Holdout Dataset**: `docs/dataset-engineering/holdout/locked-holdout-v1.yml` (200 examples, SHA: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`)
- **Final Model**: `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz` (SHA: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7`)
- **Baseline 5-Fold CV Provenance**: `cv_results/` models & reports; `docs/dataset-engineering/cross-validation/baseline/`
- **Entity Baseline Evidence**: `docs/dataset-engineering/entity-evaluation/baseline/`
- **Final Configuration Freeze**: `docs/final-readiness/final-configuration-freeze/` (Manifest SHA: `aaa9aaf7...`)
- **Final Model Training Run**: `docs/final-readiness/final-model-training/run-20260825-001846/` (Manifest SHA: `4bd8ef1f...`)
- **Runtime Verification**: `docs/final-readiness/final-model-runtime-verification/run-20260825-012754/` (Manifest SHA: `15056ebdb...`)
- **Pre-Holdout Gate Authorization**: `docs/final-readiness/pre-holdout-gate/` (Manifest SHA: `88f56ea9...`)
- **Authoritative Final Holdout Evaluation Run**: `docs/final-readiness/final-holdout-evaluation/run-20260825-013923/` (Manifest SHA: `864013f9...`, 10 files complete)
- **Authoritative System E2E Evidence Run**: `docs/final-readiness/system-e2e-evidence/run-20260825-014623/` (Manifest SHA: `7d7a256f...`, 16/16 PASS)
- **Master Final Values**: `docs/final-readiness/master-final-values/` (Manifest SHA: `1318d7a3...`)

---

## 3. Methodological Safety Guarantees

- **Training Executed Post-Holdout**: `NO`
- **Holdout Re-evaluated**: `NO`
- **Model Modified**: `NO`
- **Dataset Modified**: `NO`
- **Configuration Modified**: `NO`
- **Protected Hashes Match**: `100% PASS (All 7 canonical hashes verified)`
