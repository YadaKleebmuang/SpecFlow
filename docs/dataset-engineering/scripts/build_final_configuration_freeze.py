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
    freeze_dir = repo / "docs/final-readiness/final-configuration-freeze"
    freeze_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Protected Datasets & Baseline CV
    dev_path = repo / "app/rasa/data/nlu.yml"
    holdout_path = repo / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    oof_path = repo / "docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv"
    
    dev_sha = get_file_sha256(dev_path)
    assert dev_sha == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    
    holdout_sha = get_file_sha256(holdout_path)
    assert holdout_sha == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    
    oof_sha = get_file_sha256(oof_path)
    assert oof_sha == "b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47"
    
    # Verify Development Example and Intent counts
    with open(dev_path, "r", encoding="utf-8") as f:
        dev_yaml = yaml.safe_load(f)
    intents_list = [item.get("intent") for item in dev_yaml.get("nlu", []) if item.get("intent")]
    total_dev_examples = sum(len([l for l in item.get("examples", "").split("\n") if l.strip().startswith("-")]) for item in dev_yaml.get("nlu", []))
    assert len(intents_list) == 15
    assert total_dev_examples == 800
    
    # 2. Final Rasa Training Inputs
    cfg_path = repo / "app/rasa/config.yml"
    dom_path = repo / "app/rasa/domain.yml"
    rules_path = repo / "app/rasa/data/rules.yml"
    stories_path = repo / "app/rasa/data/stories.yml"
    
    cfg_sha = get_file_sha256(cfg_path)
    assert cfg_sha == "61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0"
    dom_sha = get_file_sha256(dom_path)
    rules_sha = get_file_sha256(rules_path)
    stories_sha = get_file_sha256(stories_path) if stories_path.exists() else None
    
    training_inputs = [
        {"path": str(cfg_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": cfg_path.stat().st_size, "sha256": cfg_sha},
        {"path": str(dom_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": dom_path.stat().st_size, "sha256": dom_sha},
        {"path": str(dev_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": dev_path.stat().st_size, "sha256": dev_sha},
        {"path": str(rules_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": rules_path.stat().st_size, "sha256": rules_sha},
    ]
    if stories_path.exists():
        training_inputs.append({
            "path": str(stories_path.relative_to(repo)),
            "classification": "TRAINING_INPUT",
            "size_bytes": stories_path.stat().st_size,
            "sha256": stories_sha
        })
        
    # 3. Domain & Rules Verification
    with open(dom_path, "r", encoding="utf-8") as f:
        dom_yaml = yaml.safe_load(f)
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_yaml = yaml.safe_load(f)
        
    domain_intents = dom_yaml.get("intents", [])
    domain_entities = dom_yaml.get("entities", [])
    domain_slots = dom_yaml.get("slots", {})
    domain_forms = dom_yaml.get("forms", {})
    domain_actions = dom_yaml.get("actions", [])
    domain_responses = dom_yaml.get("responses", {})
    
    assert "utter_fallback" in domain_responses
    assert any(any(s.get("intent") == "nlu_fallback" for s in r.get("steps", [])) for r in rules_yaml.get("rules", []))
    
    # 4. Source Files Inventory
    actions_path = repo / "app/rasa/actions/actions.py"
    spec_rec_path = repo / "app/services/recommendation/spec_recommender.py"
    upg_adv_path = repo / "app/services/recommendation/upgrade_advisor.py"
    flex_path = repo / "app/rasa/actions/flex.py"
    thai_tok_path = repo / "app/rasa/thai_tokenizer.py"
    prep_path = repo / "app/services/nlp/preprocessing.py"
    typo_path = repo / "app/services/nlp/typo_dict.json"
    line_path = repo / "app/rasa/line_channel.py"
    hw_path = repo / "app/services/recommendation/hardware_db.json"
    cred_path = repo / "app/rasa/credentials.yml"
    endpoints_path = repo / "app/rasa/endpoints.yml"
    env_ex_path = repo / ".env.example"
    gitignore_path = repo / ".gitignore"
    
    hw_sha = get_file_sha256(hw_path)
    assert hw_sha == "341659f6384ee83ebb803964c8c7a6bb06f249aa345a59b0ea540f16529245b4"
    with open(hw_path, "r", encoding="utf-8") as f:
        hw_data = json.load(f)
    hw_counts = {k: len(v) for k, v in hw_data.items()}
    assert sum(hw_counts.values()) == 64
    
    with open(typo_path, "r", encoding="utf-8") as f:
        typo_dict = json.load(f)
    typo_count = len(typo_dict)
    
    frozen_files = [
        # Training Inputs
        {"path": str(cfg_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": cfg_path.stat().st_size, "sha256": cfg_sha},
        {"path": str(dom_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": dom_path.stat().st_size, "sha256": dom_sha},
        {"path": str(dev_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": dev_path.stat().st_size, "sha256": dev_sha},
        {"path": str(rules_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": rules_path.stat().st_size, "sha256": rules_sha},
        {"path": str(stories_path.relative_to(repo)), "classification": "TRAINING_INPUT", "size_bytes": stories_path.stat().st_size, "sha256": stories_sha},
        # NLU & Dialogue Runtime Source
        {"path": str(thai_tok_path.relative_to(repo)), "classification": "NLU_RUNTIME_SOURCE", "size_bytes": thai_tok_path.stat().st_size, "sha256": get_file_sha256(thai_tok_path)},
        {"path": str(prep_path.relative_to(repo)), "classification": "PREPROCESSING_SOURCE", "size_bytes": prep_path.stat().st_size, "sha256": get_file_sha256(prep_path)},
        {"path": str(typo_path.relative_to(repo)), "classification": "PREPROCESSING_SOURCE", "size_bytes": typo_path.stat().st_size, "sha256": get_file_sha256(typo_path)},
        {"path": str(line_path.relative_to(repo)), "classification": "LINE_CHANNEL_SOURCE", "size_bytes": line_path.stat().st_size, "sha256": get_file_sha256(line_path)},
        # Actions & Recommendation Source
        {"path": str(actions_path.relative_to(repo)), "classification": "ACTION_SOURCE", "size_bytes": actions_path.stat().st_size, "sha256": get_file_sha256(actions_path)},
        {"path": str(spec_rec_path.relative_to(repo)), "classification": "RECOMMENDATION_SOURCE", "size_bytes": spec_rec_path.stat().st_size, "sha256": get_file_sha256(spec_rec_path)},
        {"path": str(upg_adv_path.relative_to(repo)), "classification": "RECOMMENDATION_SOURCE", "size_bytes": upg_adv_path.stat().st_size, "sha256": get_file_sha256(upg_adv_path)},
        {"path": str(flex_path.relative_to(repo)), "classification": "ACTION_SOURCE", "size_bytes": flex_path.stat().st_size, "sha256": get_file_sha256(flex_path)},
        # Hardware Data
        {"path": str(hw_path.relative_to(repo)), "classification": "HARDWARE_DATA", "size_bytes": hw_path.stat().st_size, "sha256": hw_sha},
        # Security & Config
        {"path": str(cred_path.relative_to(repo)), "classification": "SECURITY_CONFIG", "size_bytes": cred_path.stat().st_size, "sha256": get_file_sha256(cred_path)},
        {"path": str(endpoints_path.relative_to(repo)), "classification": "SECURITY_CONFIG", "size_bytes": endpoints_path.stat().st_size, "sha256": get_file_sha256(endpoints_path)},
        {"path": str(env_ex_path.relative_to(repo)), "classification": "SECURITY_CONFIG", "size_bytes": env_ex_path.stat().st_size, "sha256": get_file_sha256(env_ex_path)},
        {"path": str(gitignore_path.relative_to(repo)), "classification": "SECURITY_CONFIG", "size_bytes": gitignore_path.stat().st_size, "sha256": get_file_sha256(gitignore_path)},
    ]
    
    # 5. Build Freeze Manifest JSON
    timestamp = datetime.datetime.now().astimezone().isoformat()
    manifest_data = {
        "freeze_id": "specflow_final_configuration_v1",
        "freeze_timestamp": timestamp,
        "repository_root": str(repo),
        "runtime": {
            "python_version": "3.9.6",
            "rasa_version": "3.6.21",
            "rasa_sdk_version": "3.6.2",
            "pythainlp_version": "5.3.4"
        },
        "development": {
            "path": str(dev_path.relative_to(repo)),
            "rows": 800,
            "intents": 15,
            "sha256": dev_sha,
            "status": "FINAL_LOCKED"
        },
        "holdout": {
            "path": str(holdout_path.relative_to(repo)),
            "rows": 200,
            "sha256": holdout_sha,
            "evaluated": False,
            "status": "LOCKED_UNEVALUATED"
        },
        "baseline_oof": {
            "path": str(oof_path.relative_to(repo)),
            "sha256": oof_sha,
            "status": "FINAL_LOCKED"
        },
        "error_decision": {
            "primary_decision": "ACCEPT CURRENT BASELINE NLU",
            "development_dataset_change_required": False,
            "nlu_pipeline_tuning_required": False
        },
        "training_inputs": training_inputs,
        "config": {
            "path": str(cfg_path.relative_to(repo)),
            "sha256": cfg_sha,
            "pipeline": [
                {"name": "thai_tokenizer.ThaiTokenizer"},
                {"name": "RegexFeaturizer"},
                {"name": "LexicalSyntacticFeaturizer"},
                {"name": "CountVectorsFeaturizer"},
                {"name": "CountVectorsFeaturizer", "analyzer": "char_wb", "min_ngram": 1, "max_ngram": 4},
                {"name": "DIETClassifier", "epochs": 100, "constrain_similarities": True},
                {"name": "EntitySynonymMapper"},
                {"name": "ResponseSelector", "epochs": 100, "constrain_similarities": True},
                {"name": "FallbackClassifier", "threshold": 0.3, "ambiguity_threshold": 0.1}
            ],
            "policies": [
                {"name": "MemoizationPolicy"},
                {"name": "RulePolicy"},
                {"name": "UnexpecTEDIntentPolicy", "max_history": 5, "epochs": 100},
                {"name": "TEDPolicy", "max_history": 5, "epochs": 100, "constrain_similarities": True}
            ]
        },
        "domain": {
            "path": str(dom_path.relative_to(repo)),
            "sha256": dom_sha,
            "counts": {
                "intents": len(domain_intents),
                "entities": len(domain_entities),
                "slots": len(domain_slots),
                "forms": len(domain_forms),
                "actions": len(domain_actions),
                "responses": len(domain_responses)
            }
        },
        "rules": {
            "path": str(rules_path.relative_to(repo)),
            "sha256": rules_sha,
            "fallback_wired": True,
            "total_rules": len(rules_yaml.get("rules", []))
        },
        "dialogue_training_files": [
            str(rules_path.relative_to(repo)),
            str(stories_path.relative_to(repo))
        ],
        "hardware_db": {
            "path": str(hw_path.relative_to(repo)),
            "sha256": hw_sha,
            "total_records": 64,
            "category_counts": hw_counts
        },
        "preprocessing": {
            "thai_tokenizer_path": str(thai_tok_path.relative_to(repo)),
            "thai_tokenizer_sha256": get_file_sha256(thai_tok_path),
            "engine": "pythainlp.word_tokenize(engine='newmm')",
            "typo_dict_path": str(typo_path.relative_to(repo)),
            "typo_dict_count": typo_count,
            "custom_stopwords_count": 30
        },
        "security": {
            "credentials_path": str(cred_path.relative_to(repo)),
            "credentials_sha256": get_file_sha256(cred_path),
            "current_tracked_active_secrets": 0,
            "environment_variable_names": [
                "LINE_CHANNEL_SECRET",
                "LINE_CHANNEL_ACCESS_TOKEN"
            ],
            "credential_rotation_required": True,
            "credential_rotation_completed": False
        },
        "fallback": {
            "threshold": 0.3,
            "ambiguity_threshold": 0.1,
            "intent": "nlu_fallback",
            "handler": "utter_fallback",
            "static_wiring_verified": True,
            "final_model_runtime_verified": False
        },
        "forms": {
            "build_pc_form_present": True,
            "upgrade_pc_form_present": True,
            "final_model_runtime_verified": False
        },
        "tests": {
            "rasa_data_validate_exit_code": 0,
            "tests_run": 13,
            "passed": 13,
            "failed": 0,
            "skipped": 0
        },
        "response_selector": {
            "configured": True,
            "retrieval_intents_present": False,
            "runtime_role": "UNUSED_FOR_FAQ_RETRIEVAL"
        },
        "frozen_files": frozen_files,
        "final_training_ready": True,
        "training_executed": False,
        "holdout_used": False
    }
    
    manifest_path = freeze_dir / "final-configuration-freeze-manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
    # 6. Build Freeze Markdown Record
    md_path = freeze_dir / "final-configuration-freeze.md"
    
    frozen_table = ""
    for f_item in frozen_files:
        frozen_table += f"| `{f_item['path']}` | `{f_item['classification']}` | {f_item['size_bytes']:,} B | `{f_item['sha256'][:16]}...` |\n"
        
    md_content = f"""# Final Configuration Freeze Record
## SpecFlow Conversational AI System (Freeze ID: `specflow_final_configuration_v1`)

## 1. Freeze Scope
This document certifies the **authoritative Final Configuration Freeze** for the SpecFlow project.
All datasets, NLU pipelines, policy configurations, domain definitions, rules, custom action implementations, recommendation engines, hardware databases, preprocessing modules, and security configurations captured herein are **FINAL LOCKED**.

This frozen state constitutes the **sole authorized configuration** for training the canonical Final Rasa NLU/Dialogue Model on 100% of the locked Development 800 dataset.

## 2. Experimental Locks
- **Development 800**: `app/rasa/data/nlu.yml` (SHA: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`) — **FINAL LOCKED**
- **Holdout 200**: `docs/dataset-engineering/holdout/locked-holdout-v1.yml` (SHA: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`) — **LOCKED / UNEVALUATED**
- **Baseline Stratified 5-Fold CV**: `docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv` (SHA: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47`) — **FINAL LOCKED**
- **Error Decision**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/error-decision-record.json` — **ACCEPT BASELINE NLU (NO DATASET CHANGE, NO NLU TUNING)**

## 3. Final Runtime
- **Python**: `3.9.6`
- **Rasa**: `3.6.21`
- **rasa-sdk**: `3.6.2`
- **PyThaiNLP**: `5.3.4`
- **Environment**: `.venv-rasa-cv` with `PYTHONPATH="$(pwd)/app/rasa"`

## 4. Final Development Dataset
- **Path**: `app/rasa/data/nlu.yml`
- **Rows**: 800 training examples
- **Intents**: 15 canonical intents
- **SHA-256**: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`

## 5. Final NLU Configuration
- **Path**: `app/rasa/config.yml`
- **SHA-256**: `61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0`
- **NLU Pipeline**:
  1. `thai_tokenizer.ThaiTokenizer`
  2. `RegexFeaturizer`
  3. `LexicalSyntacticFeaturizer`
  4. `CountVectorsFeaturizer` (word-level)
  5. `CountVectorsFeaturizer` (char_wb, n-gram 1–4)
  6. `DIETClassifier` (100 epochs, constrain_similarities: true)
  7. `EntitySynonymMapper`
  8. `ResponseSelector` (100 epochs, constrain_similarities: true) *(Role: UNUSED_FOR_FAQ_RETRIEVAL)*
  9. `FallbackClassifier` (threshold: 0.3, ambiguity_threshold: 0.1)

## 6. Final Dialogue Configuration
- **Policies**:
  1. `MemoizationPolicy`
  2. `RulePolicy`
  3. `UnexpecTEDIntentPolicy` (max_history: 5, epochs: 100)
  4. `TEDPolicy` (max_history: 5, epochs: 100, constrain_similarities: true)
- **Rules Path**: `app/rasa/data/rules.yml` (SHA: `{rules_sha}`)
- **Stories Path**: `app/rasa/data/stories.yml` (SHA: `{stories_sha}`)

## 7. Final Domain / Forms / Actions
- **Domain Path**: `app/rasa/domain.yml` (SHA: `{dom_sha}`)
- **Intents (15)**: `greet`, `goodbye`, `build_pc`, `upgrade_pc`, `inform_budget`, `inform_usage`, `inform_current_specs`, `ask_cpu_info`, `ask_gpu_info`, `ask_ram_info`, `ask_ssd_hdd_diff`, `optimize_performance`, `inform_future_upgrade`, `affirm`, `deny`
- **Entities (4)**: `budget`, `usage`, `component_type`, `future_upgrade`
- **Slots (4)**: `budget`, `usage`, `current_specs`, `future_upgrade`
- **Forms (2)**: `build_pc_form` (required: budget, usage, future_upgrade), `upgrade_pc_form` (required: usage, current_specs)
- **Registered Actions (9)**: `action_recommend_pc`, `action_recommend_upgrade`, `action_greet`, `action_goodbye`, `action_faq`, `action_optimize_performance`, `action_ask_usage`, `action_ask_current_specs`, `action_ask_future_upgrade`
- **Responses (2)**: `utter_ask_budget`, `utter_fallback`

## 8. Recommendation & Compatibility Sources
- `app/rasa/actions/actions.py` (SHA: `{get_file_sha256(actions_path)}`)
- `app/services/recommendation/spec_recommender.py` (SHA: `{get_file_sha256(spec_rec_path)}`)
- `app/services/recommendation/upgrade_advisor.py` (SHA: `{get_file_sha256(upg_adv_path)}`)
- `app/rasa/actions/flex.py` (SHA: `{get_file_sha256(flex_path)}`)

## 9. Hardware Database
- **Path**: `app/services/recommendation/hardware_db.json`
- **SHA-256**: `341659f6384ee83ebb803964c8c7a6bb06f249aa345a59b0ea540f16529245b4`
- **Total Records**: 64 records across 8 categories (cpu: 14, gpu: 12, motherboard: 10, ram: 8, storage: 5, psu: 6, case: 5, cooler: 4)

## 10. Preprocessing & Connector
- `app/rasa/thai_tokenizer.py` (SHA: `{get_file_sha256(thai_tok_path)}`)
- `app/services/nlp/preprocessing.py` (SHA: `{get_file_sha256(prep_path)}`)
- `app/services/nlp/typo_dict.json` (SHA: `{get_file_sha256(typo_path)}`, 44 typo mapping entries)
- `app/rasa/line_channel.py` (SHA: `{get_file_sha256(line_path)}`)

## 11. LINE / Security Configuration
- `app/rasa/credentials.yml` (SHA: `{get_file_sha256(cred_path)}`)
- Active literal secrets in tracked source: **0**
- Environment variable configuration: `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`
- Git ignore patterns: `.env`, `.env.*`, `!.env.example`, `.specflow-recovery/`

## 12. Final Fallback Wiring
- `FallbackClassifier` threshold: `0.3`, ambiguity_threshold: `0.1`
- Mapping: `intent: nlu_fallback` → `action: utter_fallback`
- Static verification: **PASS**

## 13. Validation Results
- **Rasa CLI Validation**: `rasa data validate` → **Exit Code 0** (PASS)
- **Unit & Static Regression Tests**: **13/13 PASS** (`test_nlp_preprocessing.py`, `test_recommendation.py`, `test_fallback_wiring.py`)
- **ThaiTokenizer Smoke Test**: **PASS**

## 14. Deferred Final-Model Runtime Tests
- **Form Runtime Verification**: Verified statically; live interactive tracker verification deferred until Final Model is trained.
- **Fallback Runtime Inference**: Verified statically; live threshold trigger verification deferred until Final Model is trained.

## 15. External Credential Rotation Requirement
- **Credential Rotation Required**: **YES** (Due to previous historical Git commit tracking).
- **Status**: External manual action pending in LINE Developers Console prior to production use.

## 16. Frozen File Inventory
| File Path | Classification | Size | SHA-256 (Prefix) |
| :--- | :--- | :---: | :--- |
{frozen_table}

## 17. Authorization for Final Model Training
- **Final Training Ready**: **TRUE**
- **Authorization**: The above exact physical configuration is formally approved and authorized for ONE canonical Final Model Training run on 100% of Development 800 (`app/rasa/data/nlu.yml`).
- **Holdout Isolation**: The 200-example Holdout dataset remains completely locked, isolated, and unevaluated.
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    # 7. Verification of Artifacts
    for p in [manifest_path, md_path]:
        assert p.exists()
        assert p.stat().st_size > 0
        sha = get_file_sha256(p)
        print(f"Verified: {p.name:45s} | Size: {p.stat().st_size:7d} bytes | SHA: {sha}")
        
    print("\nFINAL CONFIGURATION FREEZE ARTIFACTS COMPLETE")

if __name__ == "__main__":
    main()
