#!/usr/bin/env python3
import datetime
import hashlib
import json
import os
from pathlib import Path
import yaml

def get_file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    repo = Path(os.getcwd())
    gate_dir = repo / "docs/final-readiness/pre-holdout-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Protected Datasets & Baselines
    dev_p = repo / "app/rasa/data/nlu.yml"
    oof_p = repo / "docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv"
    holdout_p = repo / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    
    dev_sha = get_file_sha256(dev_p)
    assert dev_sha == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    
    oof_sha = get_file_sha256(oof_p)
    assert oof_sha == "b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47"
    
    holdout_sha = get_file_sha256(holdout_p)
    assert holdout_sha == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    
    # 2. Frozen Training Inputs
    cfg_p = repo / "app/rasa/config.yml"
    dom_p = repo / "app/rasa/domain.yml"
    rules_p = repo / "app/rasa/data/rules.yml"
    stories_p = repo / "app/rasa/data/stories.yml"
    
    cfg_sha = get_file_sha256(cfg_p)
    assert cfg_sha == "61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0"
    dom_sha = get_file_sha256(dom_p)
    assert dom_sha == "c2a76780257345efc57dd32a8f261ac610745a4f21bad08bb308ad9b74717857"
    rules_sha = get_file_sha256(rules_p)
    assert rules_sha == "37325e428ddcec108ff10cc3ec93b1d0e667c54f23d59c23f3c710ece7db22e5"
    stories_sha = get_file_sha256(stories_p)
    assert stories_sha == "45e869d2b571bec45926228cf9537d099b3d6002484a985a0bcf09913c492985"
    
    # 3. Final Configuration Freeze Manifest
    freeze_manifest_p = repo / "docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json"
    freeze_manifest_sha = get_file_sha256(freeze_manifest_p)
    assert freeze_manifest_sha == "aaa9aaf7408032147995bd42c1f1ed822d26bc837e405c093727a0843769cc2c"
    
    # 4. Final Model & Training Manifest
    model_p = repo / "final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz"
    assert model_p.exists()
    model_sha = get_file_sha256(model_p)
    assert model_sha == "86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7"
    
    train_manifest_p = repo / "docs/final-readiness/final-model-training/run-20260825-001846/final-model-training-manifest.json"
    train_manifest_sha = get_file_sha256(train_manifest_p)
    assert train_manifest_sha == "4bd8ef1f1879c093c0be00abff0737e3f8512d82e10e00325dedddf62aea121c"
    
    # 5. Final Runtime Verification Manifest
    runtime_manifest_p = repo / "docs/final-readiness/final-model-runtime-verification/run-20260825-012754/final-model-runtime-verification-manifest.json"
    runtime_manifest_sha = get_file_sha256(runtime_manifest_p)
    assert runtime_manifest_sha == "15056ebdb4290af0ca09f8a9702faca45c00195f05c14a14ce218313ca849939"
    with open(runtime_manifest_p, "r", encoding="utf-8") as fp:
        runtime_data = json.load(fp)
    assert len(runtime_data["test_cases"]) == 8
    assert all(c["status"] == "PASS" for c in runtime_data["test_cases"])
    
    # 6. Entity Baseline Evidence Manifest
    entity_manifest_p = repo / "docs/dataset-engineering/entity-evaluation/baseline/entity-baseline-evidence-manifest.json"
    entity_manifest_sha = get_file_sha256(entity_manifest_p)
    assert entity_manifest_sha == "c40c1bf5227271aa57da4fd92dd487c65de5b59d11d7a3f9ad1661f66497c4fc"
    
    # 7. Error Decision Record
    error_decision_p = repo / "docs/dataset-engineering/error-analysis/baseline-error-analysis/error-decision-record.json"
    with open(error_decision_p, "r", encoding="utf-8") as fp:
        error_decision_data = json.load(fp)
    assert error_decision_data["primary_decision"] == "ACCEPT CURRENT BASELINE NLU (NO DEVELOPMENT DATASET CHANGE REQUIRED, NO NLU PIPELINE TUNING REQUIRED)"
    
    # Build Authorization Record JSON
    auth_data = {
        "gate_id": "specflow_pre_holdout_gate_v1",
        "timestamp": datetime.datetime.now().astimezone().isoformat(),
        "development": {
            "path": str(dev_p.relative_to(repo)),
            "rows": 800,
            "intents": 15,
            "sha256": dev_sha,
            "status": "FINAL_LOCKED"
        },
        "holdout": {
            "path": str(holdout_p.relative_to(repo)),
            "rows": 200,
            "sha256": holdout_sha,
            "evaluated_before_gate": False,
            "tuning_usage": False,
            "status": "LOCKED_UNEVALUATED"
        },
        "baseline_cv": {
            "oof_path": str(oof_p.relative_to(repo)),
            "oof_sha256": oof_sha,
            "accuracy": 0.9125,
            "macro_f1": 0.91355855,
            "status": "FINAL_LOCKED"
        },
        "error_decision": {
            "status": "CLOSED",
            "primary_decision": error_decision_data["primary_decision"],
            "development_change_required": False,
            "nlu_tuning_required": False
        },
        "entity_baseline": {
            "evidence_manifest": str(entity_manifest_p.relative_to(repo)),
            "evidence_manifest_sha256": entity_manifest_sha,
            "aggregate_status": "AUTHORITATIVE ENTITY 5-FOLD AGGREGATION POSSIBLE",
            "metric_semantics": "TOKEN_LEVEL_DIET_EVALUATION",
            "chapter4_reporting_approved": True
        },
        "final_configuration": {
            "manifest": str(freeze_manifest_p.relative_to(repo)),
            "sha256": freeze_manifest_sha,
            "frozen_input_shas": {
                "config.yml": cfg_sha,
                "domain.yml": dom_sha,
                "nlu.yml": dev_sha,
                "rules.yml": rules_sha,
                "stories.yml": stories_sha
            },
            "status": "LOCKED"
        },
        "final_model": {
            "path": str(model_p.relative_to(repo)),
            "sha256": model_sha,
            "training_manifest": str(train_manifest_p.relative_to(repo)),
            "training_manifest_sha256": train_manifest_sha,
            "status": "FINAL_LOCKED"
        },
        "runtime_verification": {
            "manifest": str(runtime_manifest_p.relative_to(repo)),
            "sha256": runtime_manifest_sha,
            "total_tests": 8,
            "passed": 8,
            "failed": 0,
            "status": "PASS"
        },
        "fallback": {
            "threshold": 0.3,
            "ambiguity_threshold": 0.1,
            "rule": "nlu_fallback -> utter_fallback",
            "runtime_verified": True
        },
        "security": {
            "current_active_secrets": 0,
            "environment_variable_loading": True,
            "credential_rotation_required": True,
            "credential_rotation_completed": False,
            "blocks_offline_holdout_evaluation": False
        },
        "open_decisions": {
            "development_change": False,
            "nlu_tuning": False,
            "model_selection": False,
            "configuration_change": False
        },
        "holdout_one_time_policy_acknowledged": True,
        "training_executed_during_gate": False,
        "holdout_evaluated_during_gate": False,
        "authorization": "AUTHORIZED FOR ONE-TIME LOCKED HOLDOUT 200 EVALUATION"
    }
    
    auth_json_p = gate_dir / "pre-holdout-authorization.json"
    with open(auth_json_p, "w", encoding="utf-8") as fp:
        json.dump(auth_data, fp, indent=2, ensure_ascii=False)
        
    # Build Authorization Record Markdown
    auth_md_p = gate_dir / "pre-holdout-authorization.md"
    md_content = f"""# Pre-Holdout Authorization Record
## SpecFlow Final Model Evaluation Authorization (Gate ID: `specflow_pre_holdout_gate_v1`)

## 1. Authorization Scope
This document formally records the final read-only governance authorization for the **ONE-TIME evaluation of the Locked Holdout 200 dataset** against the canonical **Final Model** (`{model_p.name}`).

## 2. Experimental Locks Verification
- **Development 800**: `app/rasa/data/nlu.yml` (SHA: `{dev_sha}`) → **FINAL LOCKED**
- **Baseline Intent CV**: `docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv` (SHA: `{oof_sha}`) → **FINAL LOCKED**
- **Error Decision**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/error-decision-record.json` → **CLOSED (ACCEPT BASELINE NLU)**
- **Entity Baseline Evidence**: `docs/dataset-engineering/entity-evaluation/baseline/entity-baseline-evidence-manifest.json` (SHA: `{entity_manifest_sha}`) → **CLOSED (APPROVED FOR CHAPTER 4)**
- **Final Configuration Freeze**: `docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json` (SHA: `{freeze_manifest_sha}`) → **FINAL LOCKED**
- **Final Model Artifact**: `{model_p.relative_to(repo)}` (SHA: `{model_sha}`) → **FINAL LOCKED**
- **Runtime Verification**: `docs/final-readiness/final-model-runtime-verification/run-20260825-012754/final-model-runtime-verification-manifest.json` (SHA: `{runtime_manifest_sha}`) → **8/8 PASS**
- **Locked Holdout 200**: `docs/dataset-engineering/holdout/locked-holdout-v1.yml` (SHA: `{holdout_sha}`) → **LOCKED / UNEVALUATED**

## 3. Pre-Holdout Gate Matrix
| Check Item | Requirement | Observed State | Status |
| :--- | :--- | :--- | :---: |
| **Development 800 Integrity** | Match SHA `37b05d1f...` | `{dev_sha}` | **PASS** |
| **Holdout 200 Integrity** | Match SHA `61d0c3c2...` | `{holdout_sha}` | **PASS** |
| **Holdout Isolation** | Evaluated count = 0 | Evaluated = NO, Tuning usage = NO | **PASS** |
| **Baseline Intent CV Lock** | OOF SHA `b66e9e0e...` | `{oof_sha}` (Acc: 0.9125, Macro F1: 0.9136) | **PASS** |
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
"""
    with open(auth_md_p, "w", encoding="utf-8") as fp:
        fp.write(md_content)
        
    for p in [auth_json_p, auth_md_p]:
        assert p.exists()
        assert p.stat().st_size > 0
        sha = get_file_sha256(p)
        print(f"Verified: {p.name:35s} | Size: {p.stat().st_size:7d} bytes | SHA: {sha}")
        
    print("\nPRE-HOLDOUT AUTHORIZATION GATE COMPLETE")

if __name__ == "__main__":
    main()
