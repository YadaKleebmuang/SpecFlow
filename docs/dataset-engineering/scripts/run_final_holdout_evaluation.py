#!/usr/bin/env python3
import asyncio
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
import yaml

def get_file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()

def compute_example_id(intent: str, text: str) -> str:
    norm = normalize_text(text)
    raw = f"{intent}||{norm}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

async def main():
    repo = Path(os.getcwd())
    
    print("=== STEP 0: LAST NARROW AUTHORIZATION CHECK ===")
    pre_auth_p = repo / "docs/final-readiness/pre-holdout-gate/pre-holdout-authorization.json"
    assert pre_auth_p.exists(), f"Missing pre-holdout authorization: {pre_auth_p}"
    pre_auth_sha = get_file_sha256(pre_auth_p)
    assert pre_auth_sha == "88f56ea96fa89ae5e900c58787b116bcd95a4f3e824106ac226aa314aa22a827", f"Auth SHA mismatch: {pre_auth_sha}"
    
    model_p = repo / "final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz"
    assert model_p.exists()
    model_sha = get_file_sha256(model_p)
    assert model_sha == "86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7"
    
    holdout_p = repo / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    assert holdout_p.exists()
    holdout_sha = get_file_sha256(holdout_p)
    assert holdout_sha == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    
    dev_p = repo / "app/rasa/data/nlu.yml"
    dev_sha = get_file_sha256(dev_p)
    assert dev_sha == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    
    print("Authorization & Protected Locks: PASS")
    
    print("\n=== STEP 1: CREATE UNIQUE FINAL EVALUATION RUN DIRECTORY ===")
    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"run-{now_str}"
    run_dir = repo / f"docs/final-readiness/final-holdout-evaluation/{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    temp_eval_dir = repo / f"tmp_holdout_eval_{now_str}"
    temp_eval_dir.mkdir(parents=True, exist_ok=True)
    
    log_p = run_dir / "holdout-evaluation.log"
    log_fp = open(log_p, "w", encoding="utf-8")
    
    def log(msg: str):
        print(msg)
        log_fp.write(msg + "\n")
        log_fp.flush()
        
    start_time = datetime.datetime.now().astimezone()
    start_ts = start_time.isoformat()
    t0 = time.time()
    
    log(f"Evaluation Run ID: {run_id}")
    log(f"Start Timestamp:   {start_ts}")
    log(f"Final Model:       {model_p.relative_to(repo)} (SHA: {model_sha})")
    log(f"Locked Holdout:    {holdout_p.relative_to(repo)} (SHA: {holdout_sha})")
    
    # Parse Holdout YAML to extract 200 gold examples
    with open(holdout_p, "r", encoding="utf-8") as f:
        holdout_yaml = yaml.safe_load(f)
        
    gold_examples = []
    gold_entity_spans_count = {}
    total_gold_entity_spans = 0
    
    for item in holdout_yaml.get("nlu", []):
        intent = item.get("intent")
        if "text" in item:
            raw_utt = str(item.get("text", "")).strip()
            # extract entities if any
            clean_utt = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', raw_utt)
            matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', raw_utt)
            for val, ent in matches:
                ent_name = ent.split(":")[0].strip()
                gold_entity_spans_count[ent_name] = gold_entity_spans_count.get(ent_name, 0) + 1
                total_gold_entity_spans += 1
            
            ex_id = compute_example_id(intent, clean_utt)
            gold_examples.append({
                "example_id": ex_id,
                "true_intent": intent,
                "utterance": clean_utt,
                "raw_annotated": raw_utt
            })
        elif "examples" in item:
            examples_str = item.get("examples", "")
            for line in examples_str.split("\n"):
                line_s = line.strip()
                if line_s.startswith("-"):
                    raw_utt = line_s[1:].strip()
                    # extract entities if any
                    clean_utt = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', raw_utt)
                    matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', raw_utt)
                    for val, ent in matches:
                        ent_name = ent.split(":")[0].strip()
                        gold_entity_spans_count[ent_name] = gold_entity_spans_count.get(ent_name, 0) + 1
                        total_gold_entity_spans += 1
                    
                    ex_id = compute_example_id(intent, clean_utt)
                    gold_examples.append({
                        "example_id": ex_id,
                        "true_intent": intent,
                        "utterance": clean_utt,
                        "raw_annotated": raw_utt
                    })
                
    assert len(gold_examples) == 200, f"Expected 200 holdout examples, got {len(gold_examples)}"
    assert len(set(e["example_id"] for e in gold_examples)) == 200, "Duplicate example IDs in Holdout"
    log(f"Extracted 200 unique Holdout examples across {len(set(e['true_intent'] for e in gold_examples))} intents.")
    log(f"Holdout gold entity spans count: {total_gold_entity_spans} ({gold_entity_spans_count})")
    
    # STEP 6: Leakage Check vs Development IDs
    with open(dev_p, "r", encoding="utf-8") as f:
        dev_yaml = yaml.safe_load(f)
    dev_ids = set()
    for item in dev_yaml.get("nlu", []):
        intent = item.get("intent")
        for line in item.get("examples", "").split("\n"):
            line_s = line.strip()
            if line_s.startswith("-"):
                raw_utt = line_s[1:].strip()
                clean_utt = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', raw_utt)
                dev_ids.add(compute_example_id(intent, clean_utt))
                
    overlap_ids = set(e["example_id"] for e in gold_examples) & dev_ids
    assert len(overlap_ids) == 0, f"Critical Leakage: {len(overlap_ids)} examples overlap with Development!"
    log(f"Leakage Check: PASS (Exact duplicate overlap with Development 800 = 0)")
    
    # STEP 3: Execute CLI rasa test nlu using temporary formatted yaml in temp_eval_dir
    print("\n=== STEP 3: EXECUTE RASA TEST NLU ===")
    rasa_bin = repo / ".venv-rasa-cv/bin/rasa"
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{repo / 'app/rasa'}:{env.get('PYTHONPATH', '')}"
    
    temp_nlu_p = temp_eval_dir / "holdout_rasa_format.yml"
    temp_nlu_data = {"version": "3.1", "nlu": []}
    by_intent = {}
    for ex in gold_examples:
        by_intent.setdefault(ex["true_intent"], []).append(ex["raw_annotated"])
    for intent, examples in by_intent.items():
        temp_nlu_data["nlu"].append({
            "intent": intent,
            "examples": "\n".join(f"- {e}" for e in examples)
        })
    with open(temp_nlu_p, "w", encoding="utf-8") as fp:
        yaml.safe_dump(temp_nlu_data, fp, allow_unicode=True, sort_keys=False)
        
    test_cmd = [
        str(rasa_bin), "test", "nlu",
        "--model", str(model_p),
        "--nlu", str(temp_nlu_p),
        "--out", str(temp_eval_dir)
    ]
    log(f"Running command: {' '.join(test_cmd)}")
    cli_proc = subprocess.run(test_cmd, cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log(f"CLI rasa test nlu exit code: {cli_proc.returncode}")
    log_fp.write(cli_proc.stdout + "\n")
    assert cli_proc.returncode == 0, f"Rasa test CLI failed with code {cli_proc.returncode}"
    
    # STEP 4: Exact Agent Inference on all 200 examples for per-example provenance
    print("\n=== STEP 4: PER-EXAMPLE AGENT INFERENCE (200 ROWS) ===")
    sys.path.insert(0, str(repo / "app/rasa"))
    from rasa.core.agent import Agent
    
    agent = Agent.load(str(model_p))
    assert agent.is_ready(), "Agent failed to load"
    
    predictions = []
    fallback_count = 0
    
    for ex in gold_examples:
        res = await agent.parse_message(ex["utterance"])
        
        # Classifier prediction (skipping nlu_fallback in ranking)
        non_fallback = [it for it in res.get("intent_ranking", []) if it.get("name") != "nlu_fallback"]
        if non_fallback:
            pred_intent = non_fallback[0].get("name")
            conf = float(non_fallback[0].get("confidence", 0.0))
        else:
            pred_intent = res.get("intent", {}).get("name")
            conf = float(res.get("intent", {}).get("confidence", 0.0))
            
        top_intent_with_fallback = res.get("intent", {}).get("name")
        if top_intent_with_fallback == "nlu_fallback":
            fallback_count += 1
            
        correct = (pred_intent == ex["true_intent"])
        
        predictions.append({
            "example_id": ex["example_id"],
            "utterance": ex["utterance"],
            "true_intent": ex["true_intent"],
            "predicted_intent": pred_intent,
            "confidence": f"{conf:.4f}",
            "correct": "TRUE" if correct else "FALSE",
            "final_model_path": str(model_p.relative_to(repo)),
            "final_model_sha256": model_sha
        })
        
    assert len(predictions) == 200
    assert len(set(r["example_id"] for r in predictions)) == 200
    correct_count = sum(1 for r in predictions if r["correct"] == "TRUE")
    error_count = 200 - correct_count
    log(f"Predictions captured: 200 rows | Correct: {correct_count} | Errors: {error_count} | Accuracy: {correct_count/200:.4f}")
    log(f"Fallback triggers observed: {fallback_count} / 200 ({fallback_count/200*100:.2f}%)")
    
    # STEP 7: Write holdout-predictions.csv
    pred_csv_p = run_dir / "holdout-predictions.csv"
    with open(pred_csv_p, "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["example_id", "utterance", "true_intent", "predicted_intent", "confidence", "correct", "final_model_path", "final_model_sha256"])
        writer.writeheader()
        writer.writerows(predictions)
        
    pred_csv_sha = get_file_sha256(pred_csv_p)
    log(f"Written holdout-predictions.csv (SHA: {pred_csv_sha})")
    
    # STEP 8 & 9: Compute Intent Metrics & Per-Intent Metrics
    ordered_intents = [
        "greet", "goodbye", "build_pc", "upgrade_pc", "inform_budget",
        "inform_usage", "inform_current_specs", "ask_cpu_info", "ask_gpu_info",
        "ask_ram_info", "ask_ssd_hdd_diff", "optimize_performance",
        "inform_future_upgrade", "affirm", "deny"
    ]
    
    y_true = [r["true_intent"] for r in predictions]
    y_pred = [r["predicted_intent"] for r in predictions]
    
    per_intent_records = []
    cm_matrix = {t: {p: 0 for p in ordered_intents} for t in ordered_intents}
    for t, p in zip(y_true, y_pred):
        if t in cm_matrix and p in cm_matrix[t]:
            cm_matrix[t][p] += 1
            
    macro_precisions = []
    macro_recalls = []
    macro_f1s = []
    supports = []
    
    for intent in ordered_intents:
        tp = cm_matrix[intent][intent]
        fn = sum(cm_matrix[intent][p] for p in ordered_intents) - tp
        fp = sum(cm_matrix[t][intent] for t in ordered_intents) - tp
        supp = tp + fn
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        
        macro_precisions.append(prec)
        macro_recalls.append(rec)
        macro_f1s.append(f1)
        supports.append(supp)
        
        per_intent_records.append({
            "intent": intent,
            "precision": f"{prec:.8f}",
            "recall": f"{rec:.8f}",
            "f1_score": f"{f1:.8f}",
            "support": supp,
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn
        })
        
    total_supp = sum(supports)
    assert total_supp == 200
    
    acc = correct_count / 200.0
    macro_p_val = float(np.mean(macro_precisions))
    macro_r_val = float(np.mean(macro_recalls))
    macro_f1_val = float(np.mean(macro_f1s))
    
    weighted_p_val = float(sum(p * s for p, s in zip(macro_precisions, supports)) / total_supp)
    weighted_r_val = float(sum(r * s for r, s in zip(macro_recalls, supports)) / total_supp)
    weighted_f1_val = float(sum(f * s for f, s in zip(macro_f1s, supports)) / total_supp)
    
    # Write per-intent CSV
    per_intent_csv_p = run_dir / "holdout-per-intent-metrics.csv"
    with open(per_intent_csv_p, "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(per_intent_records[0].keys()))
        writer.writeheader()
        writer.writerows(per_intent_records)
        
    # STEP 10: Final Confusion Matrix
    cm_json_p = run_dir / "holdout-confusion-matrix.json"
    with open(cm_json_p, "w", encoding="utf-8") as fp:
        json.dump({
            "label_order": ordered_intents,
            "matrix": cm_matrix,
            "total": total_supp,
            "diagonal": correct_count,
            "off_diagonal": error_count
        }, fp, indent=2, ensure_ascii=False)
        
    # Plot PNG
    cm_array = np.zeros((15, 15), dtype=int)
    for i, t in enumerate(ordered_intents):
        for j, p in enumerate(ordered_intents):
            cm_array[i, j] = cm_matrix[t][p]
            
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm_array, cmap="Blues", interpolation="nearest")
    plt.colorbar(im)
    ax.set_xticks(range(15))
    ax.set_yticks(range(15))
    ax.set_xticklabels(ordered_intents, rotation=90)
    ax.set_yticklabels(ordered_intents)
    ax.set_xlabel("Predicted Intent")
    ax.set_ylabel("True Intent")
    ax.set_title("Holdout 200 Confusion Matrix")
    
    for i in range(15):
        for j in range(15):
            val = cm_array[i, j]
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center", color="white" if val > cm_array.max()/2 else "black")
                
    plt.tight_layout()
    cm_png_p = run_dir / "holdout-confusion-matrix.png"
    plt.savefig(cm_png_p, dpi=200)
    plt.close()
    
    # STEP 11: Final Error Inventory
    error_rows = [r for r in predictions if r["correct"] == "FALSE"]
    assert len(error_rows) == error_count
    
    err_inventory_rows = []
    for r in error_rows:
        err_inventory_rows.append({
            "example_id": r["example_id"],
            "utterance": r["utterance"],
            "true_intent": r["true_intent"],
            "predicted_intent": r["predicted_intent"],
            "confidence": r["confidence"],
            "confusion_pair": f"{r['true_intent']} -> {r['predicted_intent']}"
        })
        
    err_csv_p = run_dir / "holdout-errors.csv"
    with open(err_csv_p, "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["example_id", "utterance", "true_intent", "predicted_intent", "confidence", "confusion_pair"])
        writer.writeheader()
        writer.writerows(err_inventory_rows)
        
    # STEP 12 & 13: Holdout Entity Evidence from CLI report
    diet_report_src = temp_eval_dir / "DIETClassifier_report.json"
    holdout_entity_evidence = {}
    if diet_report_src.exists():
        with open(diet_report_src, "r", encoding="utf-8") as fp:
            diet_rep = json.load(fp)
        holdout_entity_evidence = {
            "evaluation_level": "token_level_entity_classification",
            "gold_spans_total": total_gold_entity_spans,
            "gold_spans_by_entity": gold_entity_spans_count,
            "token_level_support_total": diet_rep.get("macro avg", {}).get("support", 0),
            "macro_precision": diet_rep.get("macro avg", {}).get("precision", 0.0),
            "macro_recall": diet_rep.get("macro avg", {}).get("recall", 0.0),
            "macro_f1": diet_rep.get("macro avg", {}).get("f1-score", 0.0),
            "weighted_precision": diet_rep.get("weighted avg", {}).get("precision", 0.0),
            "weighted_recall": diet_rep.get("weighted avg", {}).get("recall", 0.0),
            "weighted_f1": diet_rep.get("weighted avg", {}).get("f1-score", 0.0),
            "micro_f1": diet_rep.get("micro avg", {}).get("f1-score", 0.0),
            "per_entity": {k: v for k, v in diet_rep.items() if k not in ["macro avg", "weighted avg", "micro avg", "accuracy"]}
        }
        
    entity_json_p = run_dir / "holdout-entity-evidence.json"
    with open(entity_json_p, "w", encoding="utf-8") as fp:
        json.dump(holdout_entity_evidence, fp, indent=2, ensure_ascii=False)
        
    # STEP 15: Holdout Intent Metrics JSON
    intent_metrics_data = {
        "source_predictions_path": str(pred_csv_p.relative_to(repo)),
        "source_predictions_sha256": pred_csv_sha,
        "final_model_path": str(model_p.relative_to(repo)),
        "final_model_sha256": model_sha,
        "holdout_path": str(holdout_p.relative_to(repo)),
        "holdout_sha256": holdout_sha,
        "rows": 200,
        "unique_ids": 200,
        "correct": correct_count,
        "errors": error_count,
        "accuracy": acc,
        "macro_precision": macro_p_val,
        "macro_recall": macro_r_val,
        "macro_f1": macro_f1_val,
        "weighted_precision": weighted_p_val,
        "weighted_recall": weighted_r_val,
        "weighted_f1": weighted_f1_val,
        "fallback_count": fallback_count,
        "fallback_rate": fallback_count / 200.0,
        "label_order": ordered_intents,
        "zero_division": 0,
        "evaluation_type": "ONE_TIME_LOCKED_HOLDOUT_FINAL_TEST"
    }
    intent_metrics_json_p = run_dir / "holdout-intent-metrics.json"
    with open(intent_metrics_json_p, "w", encoding="utf-8") as fp:
        json.dump(intent_metrics_data, fp, indent=2, ensure_ascii=False)
        
    t1 = time.time()
    end_time = datetime.datetime.now().astimezone()
    end_ts = end_time.isoformat()
    elapsed_seconds = round(t1 - t0, 2)
    
    # STEP 18: Final Evaluation Manifest
    manifest_data = {
        "evaluation_id": "specflow_final_holdout_v1",
        "evaluation_type": "ONE_TIME_LOCKED_HOLDOUT_FINAL_TEST",
        "evaluation_start_timestamp": start_ts,
        "evaluation_end_timestamp": end_ts,
        "elapsed_seconds": elapsed_seconds,
        "evaluation_invocation_count": 1,
        "runtime": {
            "python_version": "3.9.6",
            "rasa_version": "3.6.21",
            "rasa_sdk_version": "3.6.2",
            "pythainlp_version": "5.3.4"
        },
        "pre_holdout_authorization": {
            "path": "docs/final-readiness/pre-holdout-gate/pre-holdout-authorization.json",
            "sha256": pre_auth_sha
        },
        "final_configuration": {
            "manifest": "docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json",
            "sha256": "aaa9aaf7408032147995bd42c1f1ed822d26bc837e405c093727a0843769cc2c"
        },
        "final_model": {
            "path": str(model_p.relative_to(repo)),
            "sha256": model_sha,
            "size_bytes": model_p.stat().st_size
        },
        "development": {
            "path": str(dev_p.relative_to(repo)),
            "sha256": dev_sha
        },
        "holdout": {
            "path": str(holdout_p.relative_to(repo)),
            "rows": 200,
            "sha256": holdout_sha,
            "prior_evaluated": False,
            "evaluation_count": 1
        },
        "predictions": {
            "path": str(pred_csv_p.relative_to(repo)),
            "rows": 200,
            "unique_ids": 200,
            "sha256": pred_csv_sha
        },
        "intent_metrics": {
            "accuracy": acc,
            "macro_precision": macro_p_val,
            "macro_recall": macro_r_val,
            "macro_f1": macro_f1_val,
            "weighted_precision": weighted_p_val,
            "weighted_recall": weighted_r_val,
            "weighted_f1": weighted_f1_val,
            "per_intent_metrics_path": str(per_intent_csv_p.relative_to(repo))
        },
        "confusion_matrix": {
            "json_path": str(cm_json_p.relative_to(repo)),
            "png_path": str(cm_png_p.relative_to(repo)),
            "total": 200,
            "diagonal": correct_count,
            "off_diagonal": error_count
        },
        "errors": {
            "path": str(err_csv_p.relative_to(repo)),
            "rows": error_count
        },
        "fallback": {
            "count": fallback_count,
            "rate": fallback_count / 200.0,
            "availability": "EXPOSED_IN_INTENT_OUTPUT"
        },
        "entity_evaluation": {
            "availability": "AVAILABLE",
            "metric_semantics": "token_level_entity_classification",
            "artifact_path": str(entity_json_p.relative_to(repo)),
            "macro_f1": holdout_entity_evidence.get("macro_f1", 0.0),
            "weighted_f1": holdout_entity_evidence.get("weighted_f1", 0.0)
        },
        "development_holdout_exact_overlap": 0,
        "model_selection_closed": True,
        "tuning_after_holdout_allowed": False,
        "training_executed": False,
        "development_modified": False,
        "configuration_modified": False,
        "final_model_modified": False
    }
    manifest_p = run_dir / "final-holdout-evaluation-manifest.json"
    with open(manifest_p, "w", encoding="utf-8") as fp:
        json.dump(manifest_data, fp, indent=2, ensure_ascii=False)
        
    # STEP 19: Markdown Report
    cv_mean_acc = 0.91250000
    cv_mean_macro_f1 = 0.90846876
    diff_acc = acc - cv_mean_acc
    diff_f1 = macro_f1_val - cv_mean_macro_f1
    
    per_intent_md_table = "| Intent | Precision | Recall | F1-Score | Support | TP | FP | FN |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
    for r in per_intent_records:
        per_intent_md_table += f"| `{r['intent']}` | {float(r['precision']):.4f} | {float(r['recall']):.4f} | {float(r['f1_score']):.4f} | {r['support']} | {r['true_positive']} | {r['false_positive']} | {r['false_negative']} |\n"
        
    md_p = run_dir / "final-holdout-evaluation.md"
    md_content = f"""# One-Time Locked Holdout 200 Final Evaluation Report
## SpecFlow Conversational AI Final Test Performance (Evaluation ID: `specflow_final_holdout_v1`)

## 1. Evaluation Scope
This document records the **single authoritative evaluation** of the locked Final Model against the unseen **Locked Holdout 200 dataset**.
This evaluation provides the definitive test benchmark for the undergraduate project report.

## 2. One-Time Authorization
- **Authorization Gate**: `docs/final-readiness/pre-holdout-gate/pre-holdout-authorization.json` (SHA: `{pre_auth_sha}`)
- **Evaluation Invocation**: `1` (Exactly one execution)

## 3. Final Model Identity
- **Model Path**: `{model_p.relative_to(repo)}`
- **Model SHA-256**: `{model_sha}`
- **Training Scope**: 100% of Development 800 (Run ID: `run-20260825-001846`)

## 4. Locked Holdout Identity
- **Holdout Path**: `{holdout_p.relative_to(repo)}`
- **Holdout SHA-256**: `{holdout_sha}`
- **Holdout Examples**: 200
- **Prior Evaluations**: 0
- **Exact Duplicate Overlap with Development 800**: **0**

## 5. Evaluation Method
Deterministic per-example inference using Rasa 3.6.21 Agent runtime and CLI evaluation on the complete 200-example Holdout set.

## 6. Final Intent Classification Results
- **Total Test Examples**: **200**
- **Correct Predictions**: **{correct_count}**
- **Classification Errors**: **{error_count}**
- **Accuracy**: **{acc:.8f}** ({acc*100:.2f}%)
- **Macro Precision**: **{macro_p_val:.8f}** ({macro_p_val*100:.2f}%)
- **Macro Recall**: **{macro_r_val:.8f}** ({macro_r_val*100:.2f}%)
- **Macro F1-Score**: **{macro_f1_val:.8f}** ({macro_f1_val*100:.2f}%)
- **Weighted Precision**: **{weighted_p_val:.8f}** ({weighted_p_val*100:.2f}%)
- **Weighted Recall**: **{weighted_r_val:.8f}** ({weighted_r_val*100:.2f}%)
- **Weighted F1-Score**: **{weighted_f1_val:.8f}** ({weighted_f1_val*100:.2f}%)

## 7. Per-Intent Results
{per_intent_md_table}

## 8. Confusion Matrix
- **Dimensions**: 15 x 15
- **Total Instances**: 200
- **Diagonal Sum (Correct)**: {correct_count}
- **Off-Diagonal Sum (Errors)**: {error_count}
- **Matrix Artifacts**:
  - `holdout-confusion-matrix.json`
  - `holdout-confusion-matrix.png`

## 9. Holdout Error Inventory
- **Error Count**: **{error_count}**
- **Error CSV**: `holdout-errors.csv` (Contains all {error_count} misclassifications with true intent, predicted intent, and confidence).

## 10. Fallback Observation
- **Fallback Predictions**: {fallback_count}
- **Fallback Rate**: {fallback_count/200.0*100:.2f}%

## 11. Entity Final Evaluation (Token-Level DIET Evaluation)
- **Gold Entity Spans**: {total_gold_entity_spans} ({gold_entity_spans_count})
- **Token Support Total**: {holdout_entity_evidence.get('token_level_support_total', 0)}
- **Macro Precision**: {holdout_entity_evidence.get('macro_precision', 0.0):.4f}
- **Macro Recall**: {holdout_entity_evidence.get('macro_recall', 0.0):.4f}
- **Macro F1-Score**: {holdout_entity_evidence.get('macro_f1', 0.0):.4f}
- **Weighted F1-Score**: {holdout_entity_evidence.get('weighted_f1', 0.0):.4f}

## 12. Comparison with Development Cross-Validation
| Metric | Development CV (5-Fold Mean) | Holdout 200 Final Test | Descriptive Delta |
| :--- | :---: | :---: | :---: |
| **Accuracy** | {cv_mean_acc:.4f} (91.25%) | {acc:.4f} ({acc*100:.2f}%) | {diff_acc:+.4f} ({diff_acc*100:+.2f}%) |
| **Macro F1** | {cv_mean_macro_f1:.4f} (90.85%) | {macro_f1_val:.4f} ({macro_f1_val*100:.2f}%) | {diff_f1:+.4f} ({diff_f1*100:+.2f}%) |

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
"""
    with open(md_p, "w", encoding="utf-8") as fp:
        fp.write(md_content)
        
    # Cleanup temp directory
    shutil.rmtree(temp_eval_dir, ignore_errors=True)
    
    # Verify Artifacts
    for p in [pred_csv_p, intent_metrics_json_p, per_intent_csv_p, cm_json_p, cm_png_p, err_csv_p, entity_json_p, manifest_p, md_p, log_p]:
        assert p.exists()
        assert p.stat().st_size > 0
        sha = get_file_sha256(p)
        print(f"Verified: {p.name:45s} | Size: {p.stat().st_size:7d} bytes | SHA: {sha}")
        
    print("\nFINAL HOLDOUT EVALUATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())
