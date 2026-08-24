#!/usr/bin/env python3
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from rasa.shared.importers.importer import TrainingDataImporter

def get_file_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

def evaluate_metrics(y_true, y_pred):
    acc = float(accuracy_score(y_true, y_pred))
    mp, mr, mf1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    wp, wr, wf1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
    return {
        "accuracy": acc,
        "macro_precision": float(mp),
        "macro_recall": float(mr),
        "macro_f1": float(mf1),
        "weighted_precision": float(wp),
        "weighted_recall": float(wr),
        "weighted_f1": float(wf1),
    }

def main():
    repo_root = Path(os.getcwd())
    results_dir = repo_root / "docs/dataset-engineering/cross-validation/baseline/results"
    fold_pred_dir = results_dir / "fold-predictions"
    oof_path = results_dir / "oof-predictions.csv"
    dev_path = repo_root / "app/rasa/data/nlu.yml"
    holdout_path = repo_root / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    run_cv_path = repo_root / "run_cv.py"
    
    must_defects = []
    should_items = []
    
    print("=== STEP 5 FINAL READ-ONLY AUDIT ===")
    
    # 1. DATA FREEZE
    dev_sha = get_file_sha256(dev_path)
    expected_dev_sha = "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    if dev_sha != expected_dev_sha:
        must_defects.append(f"Development SHA mismatch: {dev_sha} != {expected_dev_sha}")
    else:
        print(f"Development SHA: PASS ({dev_sha})")
        
    holdout_sha = get_file_sha256(holdout_path)
    expected_holdout_sha = "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    if holdout_sha != expected_holdout_sha:
        must_defects.append(f"Holdout SHA mismatch: {holdout_sha} != {expected_holdout_sha}")
    else:
        print(f"Holdout SHA: PASS ({holdout_sha}) [Unevaluated]")

    # Check Dev example count and unique IDs
    importer = TrainingDataImporter.load_from_dict(training_data_paths=[str(dev_path)])
    dev_examples = importer.get_nlu_data().nlu_examples
    if len(dev_examples) != 800:
        must_defects.append(f"Development examples count: {len(dev_examples)} != 800")
        
    dev_ids = []
    for ex in dev_examples:
        norm_u = ex.get("text").replace("\r\n", "\n").replace("\r", "\n").strip()
        eid = hashlib.sha256(f"{ex.get('intent')}||{norm_u}".encode("utf-8")).hexdigest()
        dev_ids.append(eid)
    if len(set(dev_ids)) != 800:
        must_defects.append(f"Development unique IDs: {len(set(dev_ids))} != 800")

    # 2. FOLD ARTIFACTS
    fold_csvs = {}
    fold_manifests = {}
    for i in range(5):
        csv_p = fold_pred_dir / f"fold-{i}-predictions.csv"
        man_p = results_dir / f"fold-{i}-manifest.json"
        if not csv_p.exists():
            must_defects.append(f"Missing fold CSV: {csv_p}")
        if not man_p.exists():
            must_defects.append(f"Missing fold manifest: {man_p}")
            
        with open(csv_p, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != 160:
            must_defects.append(f"Fold {i} row count {len(rows)} != 160")
        eids = [r["example_id"] for r in rows]
        if len(set(eids)) != 160:
            must_defects.append(f"Fold {i} duplicate IDs: {len(set(eids))} != 160")
        c = sum(1 for r in rows if r["correct"].lower() == "true")
        e = sum(1 for r in rows if r["correct"].lower() == "false")
        if c + e != 160:
            must_defects.append(f"Fold {i} correct+error count {c+e} != 160")
            
        csv_sha = get_file_sha256(csv_p)
        with open(man_p, "r", encoding="utf-8") as f:
            man_data = json.load(f)
        if man_data["prediction_csv_sha256"] != csv_sha:
            must_defects.append(f"Fold {i} manifest CSV SHA mismatch")
            
        fold_csvs[i] = rows
        fold_manifests[i] = man_data

    # Fold 0 reference check
    f0_csv_sha = get_file_sha256(fold_pred_dir / "fold-0-predictions.csv")
    if f0_csv_sha != "5f89ce4fc2076542115d3e3ae9f03877122bd0ef74eeb61e5a5d7d5fc02d8d5d":
        must_defects.append(f"Fold 0 CSV SHA mismatch: {f0_csv_sha}")

    # Pairwise overlap
    for i in range(5):
        set_i = set(r["example_id"] for r in fold_csvs[i])
        for j in range(i + 1, 5):
            set_j = set(r["example_id"] for r in fold_csvs[j])
            if len(set_i.intersection(set_j)) != 0:
                must_defects.append(f"Pairwise overlap between fold {i} and {j}")

    # 3. OOF ARTIFACT
    if not oof_path.exists():
        must_defects.append("Missing OOF file")
    oof_sha = get_file_sha256(oof_path)
    if oof_sha != "b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47":
        must_defects.append(f"OOF SHA mismatch: {oof_sha}")
        
    with open(oof_path, "r", encoding="utf-8") as f:
        oof_rows = list(csv.DictReader(f))
        
    if len(oof_rows) != 800:
        must_defects.append(f"OOF rows {len(oof_rows)} != 800")
    oof_eids = [r["example_id"] for r in oof_rows]
    if len(set(oof_eids)) != 800:
        must_defects.append("OOF duplicate example IDs")
        
    oof_c = sum(1 for r in oof_rows if r["correct"].lower() == "true")
    oof_e = sum(1 for r in oof_rows if r["correct"].lower() == "false")
    if oof_c != 730:
        must_defects.append(f"OOF correct {oof_c} != 730")
    if oof_e != 70:
        must_defects.append(f"OOF errors {oof_e} != 70")
    if oof_c + oof_e != 800:
        must_defects.append(f"OOF sum {oof_c+oof_e} != 800")
        
    # Check concatenation equality
    concatenated_fold_rows = [r for i in range(5) for r in fold_csvs[i]]
    if len(concatenated_fold_rows) != 800:
        must_defects.append("Concatenated fold rows != 800")
    for idx in range(800):
        if oof_rows[idx] != concatenated_fold_rows[idx]:
            must_defects.append(f"OOF row mismatch with concatenated fold rows at index {idx}")
            break

    # Development ID set equality
    if set(oof_eids) != set(dev_ids):
        must_defects.append("OOF ID set != Development ID set")

    # True-intent support
    expected_support = {
        "greet": 19, "goodbye": 20, "build_pc": 145, "upgrade_pc": 117,
        "inform_budget": 61, "inform_usage": 73, "inform_current_specs": 68,
        "ask_cpu_info": 23, "ask_gpu_info": 23, "ask_ram_info": 23,
        "ask_ssd_hdd_diff": 23, "optimize_performance": 98,
        "inform_future_upgrade": 58, "affirm": 24, "deny": 25
    }
    actual_support = {}
    for r in oof_rows:
        actual_support[r["true_intent"]] = actual_support.get(r["true_intent"], 0) + 1
    for k, v in expected_support.items():
        if actual_support.get(k, 0) != v:
            must_defects.append(f"Intent support mismatch for {k}: {actual_support.get(k, 0)} != {v}")

    # 4. METRIC RECOMPUTATION
    locked_label_order = [
        "greet", "goodbye", "build_pc", "upgrade_pc", "inform_budget",
        "inform_usage", "inform_current_specs", "ask_cpu_info", "ask_gpu_info",
        "ask_ram_info", "ask_ssd_hdd_diff", "optimize_performance",
        "inform_future_upgrade", "affirm", "deny"
    ]
    y_t_oof = [r["true_intent"] for r in oof_rows]
    y_p_oof = [r["predicted_intent"] for r in oof_rows]
    oof_m = evaluate_metrics(y_t_oof, y_p_oof)
    
    with open(results_dir / "oof-metrics.json", "r", encoding="utf-8") as f:
        stored_oof_m = json.load(f)
        
    for k in ["accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_precision", "weighted_recall", "weighted_f1"]:
        diff = abs(oof_m[k] - stored_oof_m[k])
        if diff > 1e-8:
            must_defects.append(f"OOF metric mismatch for {k}: delta {diff:.8e}")
            
    # Per-fold metrics
    with open(results_dir / "fold-metrics.json", "r", encoding="utf-8") as f:
        stored_fm = json.load(f)
    for i in range(5):
        y_t_f = [r["true_intent"] for r in fold_csvs[i]]
        y_p_f = [r["predicted_intent"] for r in fold_csvs[i]]
        fm_calc = evaluate_metrics(y_t_f, y_p_f)
        for k in ["accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_precision", "weighted_recall", "weighted_f1"]:
            diff = abs(fm_calc[k] - stored_fm[i][k])
            if diff > 1e-8:
                must_defects.append(f"Fold {i} metric mismatch for {k}: delta {diff:.8e}")
                
    # Aggregate metrics
    with open(results_dir / "aggregate_metrics.json", "r", encoding="utf-8") as f:
        stored_agg = json.load(f)
    for k in ["accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_precision", "weighted_recall", "weighted_f1"]:
        vals = [stored_fm[i][k] for i in range(5)]
        mean_calc = float(np.mean(vals))
        sd_calc = float(np.std(vals, ddof=1))
        if abs(mean_calc - stored_agg["metrics"][k]["mean"]) > 1e-8:
            must_defects.append(f"Aggregate mean mismatch for {k}")
        if abs(sd_calc - stored_agg["metrics"][k]["sample_sd"]) > 1e-8:
            must_defects.append(f"Aggregate sample SD mismatch for {k}")

    # 5. CONFUSION MATRIX AUDIT
    with open(results_dir / "confusion-matrix-oof.json", "r", encoding="utf-8") as f:
        stored_cm = json.load(f)
    cm_calc = confusion_matrix(y_t_oof, y_p_oof, labels=locked_label_order)
    if cm_calc.shape != (15, 15):
        must_defects.append("Confusion matrix shape != (15, 15)")
    if int(np.sum(cm_calc)) != 800:
        must_defects.append("Confusion matrix total != 800")
    if int(np.trace(cm_calc)) != 730:
        must_defects.append("Confusion matrix trace != 730")
    if (int(np.sum(cm_calc)) - int(np.trace(cm_calc))) != 70:
        must_defects.append("Confusion matrix off-diagonal != 70")
    if stored_cm["matrix"] != cm_calc.tolist():
        must_defects.append("Confusion matrix cell-by-cell mismatch")

    # Check PNG
    png_path = results_dir / "confusion-matrix-oof.png"
    if not png_path.exists() or png_path.stat().st_size == 0:
        must_defects.append("PNG missing or empty")
    else:
        try:
            im = Image.open(png_path)
            im.verify()
            if im.size[0] == 0 or im.size[1] == 0:
                must_defects.append("PNG zero dimensions")
        except Exception as ex:
            must_defects.append(f"PNG verification error: {ex}")

    # 6. PER-INTENT METRICS AUDIT
    with open(results_dir / "per-intent-metrics.csv", "r", encoding="utf-8") as f:
        stored_pi = list(csv.DictReader(f))
    if len(stored_pi) != 15:
        must_defects.append("Per-intent metrics rows != 15")
    if sum(int(r["support"]) for r in stored_pi) != 800:
        must_defects.append("Per-intent support sum != 800")

    # 7. ERROR INVENTORY AUDIT
    with open(results_dir / "error-inventory.csv", "r", encoding="utf-8") as f:
        stored_err = list(csv.DictReader(f))
    if len(stored_err) != 70:
        must_defects.append(f"Error inventory rows {len(stored_err)} != 70")
    oof_err_ids = set(r["example_id"] for r in oof_rows if r["correct"].lower() == "false")
    err_inv_ids = set(r["example_id"] for r in stored_err)
    if oof_err_ids != err_inv_ids:
        must_defects.append("Error inventory IDs != OOF error IDs")

    # 8. MANIFESTS AUDIT
    oof_man_path = results_dir / "oof-integrity-manifest.json"
    with open(oof_man_path, "r", encoding="utf-8") as f:
        oof_man = json.load(f)
    if oof_man["oof_sha256"] != oof_sha:
        must_defects.append("OOF integrity manifest OOF SHA mismatch")

    s4_man_path = results_dir / "step-4-metrics-manifest.json"
    with open(s4_man_path, "r", encoding="utf-8") as f:
        s4_man = json.load(f)
    if s4_man["source_oof_sha256"] != oof_sha:
        must_defects.append("Step 4 manifest OOF SHA mismatch")

    # 9. PIPELINE HARDENING AUDIT (Static check on run_cv.py)
    if not run_cv_path.exists():
        must_defects.append("Missing run_cv.py")
    else:
        with open(run_cv_path, "r", encoding="utf-8") as f:
            cv_src = f.read()
            
        hardening_checks = {
            "snapshot_pre_training": bool("snapshot" in cv_src.lower() or "pre_models" in cv_src.lower() or "existing_models" in cv_src.lower() or "find_newest_model" in cv_src.lower()),
            "persists_predictions": bool("predictions.csv" in cv_src or "fold_predictions" in cv_src),
            "fails_closed": bool("raise" in cv_src or "sys.exit" in cv_src),
            "manifest_creation": bool("manifest" in cv_src.lower()),
        }
        print(f"Pipeline hardening checks: {hardening_checks}")
        # If any non-fatal enhancement is observed, record in should_items
        
    print(f"\nAudit complete: MUST defects = {len(must_defects)}, SHOULD items = {len(should_items)}")
    for m in must_defects:
        print(f"MUST: {m}")
    for s in should_items:
        print(f"SHOULD: {s}")

if __name__ == "__main__":
    main()
