#!/usr/bin/env python3
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, accuracy_score

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
    
    # 1. Preflight
    assert oof_path.exists(), f"Missing OOF file: {oof_path}"
    oof_sha = get_file_sha256(oof_path)
    expected_oof_sha = "b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47"
    assert oof_sha == expected_oof_sha, f"OOF SHA mismatch: {oof_sha} != {expected_oof_sha}"
    
    with open(oof_path, "r", encoding="utf-8") as f:
        oof_rows = list(csv.DictReader(f))
        
    assert len(oof_rows) == 800
    assert len(set(r["example_id"] for r in oof_rows)) == 800
    
    total_correct = sum(1 for r in oof_rows if r["correct"].lower() == "true")
    total_errors = sum(1 for r in oof_rows if r["correct"].lower() == "false")
    assert total_correct == 730
    assert total_errors == 70
    assert total_correct + total_errors == 800
    
    # 2. Locked Label Order
    locked_label_order = [
        "greet",
        "goodbye",
        "build_pc",
        "upgrade_pc",
        "inform_budget",
        "inform_usage",
        "inform_current_specs",
        "ask_cpu_info",
        "ask_gpu_info",
        "ask_ram_info",
        "ask_ssd_hdd_diff",
        "optimize_performance",
        "inform_future_upgrade",
        "affirm",
        "deny"
    ]
    assert len(locked_label_order) == 15
    
    # 3. OOF Metrics
    y_true_oof = [r["true_intent"] for r in oof_rows]
    y_pred_oof = [r["predicted_intent"] for r in oof_rows]
    
    oof_metrics = evaluate_metrics(y_true_oof, y_pred_oof)
    
    # 4. Write oof-metrics.json
    oof_metrics_data = {
        "source_oof_path": str(oof_path.relative_to(repo_root)),
        "source_oof_sha256": oof_sha,
        "rows": 800,
        "unique_example_ids": 800,
        "correct": total_correct,
        "errors": total_errors,
        "accuracy": oof_metrics["accuracy"],
        "macro_precision": oof_metrics["macro_precision"],
        "macro_recall": oof_metrics["macro_recall"],
        "macro_f1": oof_metrics["macro_f1"],
        "weighted_precision": oof_metrics["weighted_precision"],
        "weighted_recall": oof_metrics["weighted_recall"],
        "weighted_f1": oof_metrics["weighted_f1"],
        "label_order": locked_label_order,
        "calculation_method": "physical_oof_predictions_v1",
        "zero_division": 0
    }
    
    oof_metrics_path = results_dir / "oof-metrics.json"
    tmp_oof_metrics_path = repo_root / "tmp_salvage/oof-metrics.candidate.json"
    tmp_oof_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_oof_metrics_path, "w", encoding="utf-8") as f:
        json.dump(oof_metrics_data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_oof_metrics_path, oof_metrics_path)
    
    # 5. Per-Fold Metrics
    fold_metrics_list = []
    fold_csv_sources = {}
    for fold_i in range(5):
        f_csv = fold_pred_dir / f"fold-{fold_i}-predictions.csv"
        assert f_csv.exists()
        f_sha = get_file_sha256(f_csv)
        fold_csv_sources[f"fold_{fold_i}"] = {
            "path": str(f_csv.relative_to(repo_root)),
            "sha256": f_sha
        }
        with open(f_csv, "r", encoding="utf-8") as f:
            f_rows = list(csv.DictReader(f))
        assert len(f_rows) == 160
        f_corr = sum(1 for r in f_rows if r["correct"].lower() == "true")
        f_err = sum(1 for r in f_rows if r["correct"].lower() == "false")
        assert f_corr + f_err == 160
        
        y_t = [r["true_intent"] for r in f_rows]
        y_p = [r["predicted_intent"] for r in f_rows]
        f_m = evaluate_metrics(y_t, y_p)
        
        fold_metrics_list.append({
            "fold": fold_i,
            "rows": 160,
            "correct": f_corr,
            "errors": f_err,
            "accuracy": f_m["accuracy"],
            "macro_precision": f_m["macro_precision"],
            "macro_recall": f_m["macro_recall"],
            "macro_f1": f_m["macro_f1"],
            "weighted_precision": f_m["weighted_precision"],
            "weighted_recall": f_m["weighted_recall"],
            "weighted_f1": f_m["weighted_f1"],
        })
        
    # Write fold-metrics.csv
    fold_metrics_csv_path = results_dir / "fold-metrics.csv"
    tmp_fold_metrics_csv = repo_root / "tmp_salvage/fold-metrics.candidate.csv"
    fieldnames_fm = [
        "fold", "rows", "correct", "errors", "accuracy",
        "macro_precision", "macro_recall", "macro_f1",
        "weighted_precision", "weighted_recall", "weighted_f1"
    ]
    with open(tmp_fold_metrics_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames_fm)
        w.writeheader()
        for fm in fold_metrics_list:
            w.writerow(fm)
    os.replace(tmp_fold_metrics_csv, fold_metrics_csv_path)
    
    # Write fold-metrics.json
    fold_metrics_json_path = results_dir / "fold-metrics.json"
    tmp_fold_metrics_json = repo_root / "tmp_salvage/fold-metrics.candidate.json"
    with open(tmp_fold_metrics_json, "w", encoding="utf-8") as f:
        json.dump(fold_metrics_list, f, indent=2, ensure_ascii=False)
    os.replace(tmp_fold_metrics_json, fold_metrics_json_path)
    
    # 6. Aggregate 5-Fold Metrics
    metric_keys = [
        "accuracy", "macro_precision", "macro_recall", "macro_f1",
        "weighted_precision", "weighted_recall", "weighted_f1"
    ]
    aggregate_dict = {
        "n_folds": 5,
        "sd_type": "sample",
        "ddof": 1,
        "metrics": {}
    }
    for k in metric_keys:
        vals = [fm[k] for fm in fold_metrics_list]
        m = float(np.mean(vals))
        sd = float(np.std(vals, ddof=1))
        aggregate_dict["metrics"][k] = {
            "mean": m,
            "sample_sd": sd,
            "fold_values": vals,
            "zero_sd_physically_reproduced": (sd == 0.0)
        }
        
    aggregate_json_path = results_dir / "aggregate_metrics.json"
    tmp_agg_path = repo_root / "tmp_salvage/aggregate_metrics.candidate.json"
    with open(tmp_agg_path, "w", encoding="utf-8") as f:
        json.dump(aggregate_dict, f, indent=2, ensure_ascii=False)
    os.replace(tmp_agg_path, aggregate_json_path)
    
    # 7. Confusion Matrix
    cm = confusion_matrix(y_true_oof, y_pred_oof, labels=locked_label_order)
    assert cm.shape == (15, 15)
    cm_total = int(np.sum(cm))
    cm_diag = int(np.trace(cm))
    cm_offdiag = cm_total - cm_diag
    assert cm_total == 800
    assert cm_diag == 730
    assert cm_offdiag == 70
    
    cm_data = {
        "label_order": locked_label_order,
        "matrix": cm.tolist(),
        "total": cm_total,
        "diagonal_correct": cm_diag,
        "off_diagonal_errors": cm_offdiag,
        "source_oof_sha256": oof_sha
    }
    cm_json_path = results_dir / "confusion-matrix-oof.json"
    tmp_cm_json = repo_root / "tmp_salvage/confusion-matrix-oof.candidate.json"
    with open(tmp_cm_json, "w", encoding="utf-8") as f:
        json.dump(cm_data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_cm_json, cm_json_path)
    
    # 8. Confusion Matrix PNG
    cm_png_path = results_dir / "confusion-matrix-oof.png"
    tmp_cm_png = repo_root / "tmp_salvage/confusion-matrix-oof.candidate.png"
    
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    cax = ax.matshow(cm, cmap="Blues", interpolation="nearest")
    fig.colorbar(cax, fraction=0.046, pad=0.04)
    
    ax.set_xticks(range(15))
    ax.set_yticks(range(15))
    ax.set_xticklabels(locked_label_order, rotation=45, ha="left", fontsize=9)
    ax.set_yticklabels(locked_label_order, fontsize=9)
    ax.set_xlabel("Predicted Intent", fontsize=11, labelpad=10)
    ax.set_ylabel("True Intent", fontsize=11, labelpad=10)
    ax.set_title("OOF 800 Intent Confusion Matrix (Baseline 5-Fold CV)", fontsize=13, pad=20)
    
    # Text annotations inside cells
    thresh = cm.max() / 2.0
    for i in range(15):
        for j in range(15):
            val = cm[i, j]
            color = "white" if val > thresh else "black"
            ax.text(j, i, str(val), ha="center", va="center", color=color, fontsize=8)
            
    plt.tight_layout()
    plt.savefig(tmp_cm_png, dpi=300)
    plt.close(fig)
    os.replace(tmp_cm_png, cm_png_path)
    
    # 9. Per-Intent Metrics
    p_per, r_per, f1_per, sup_per = precision_recall_fscore_support(
        y_true_oof, y_pred_oof, labels=locked_label_order, zero_division=0
    )
    assert int(np.sum(sup_per)) == 800
    
    per_intent_rows = []
    for idx, intent in enumerate(locked_label_order):
        tp = int(cm[idx, idx])
        fn = int(np.sum(cm[idx, :]) - tp)
        fp = int(np.sum(cm[:, idx]) - tp)
        per_intent_rows.append({
            "intent": intent,
            "support": int(sup_per[idx]),
            "predicted_support": int(np.sum(cm[:, idx])),
            "precision": float(p_per[idx]),
            "recall": float(r_per[idx]),
            "f1": float(f1_per[idx]),
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn
        })
        
    per_intent_csv_path = results_dir / "per-intent-metrics.csv"
    tmp_per_intent_csv = repo_root / "tmp_salvage/per-intent-metrics.candidate.csv"
    fieldnames_pi = [
        "intent", "support", "predicted_support", "precision", "recall", "f1",
        "true_positive", "false_positive", "false_negative"
    ]
    with open(tmp_per_intent_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames_pi)
        w.writeheader()
        for r in per_intent_rows:
            w.writerow(r)
    os.replace(tmp_per_intent_csv, per_intent_csv_path)
    
    # 10. Error Inventory
    error_rows = []
    for r in oof_rows:
        if r["correct"].lower() == "false":
            error_rows.append({
                "example_id": r["example_id"],
                "fold": r["fold"],
                "utterance": r["utterance"],
                "true_intent": r["true_intent"],
                "predicted_intent": r["predicted_intent"],
                "confidence": r["confidence"],
                "model_path": r["model_path"],
                "model_sha256": r["model_sha256"],
                "confusion_pair": f"{r['true_intent']} -> {r['predicted_intent']}"
            })
            
    assert len(error_rows) == 70
    error_csv_path = results_dir / "error-inventory.csv"
    tmp_error_csv = repo_root / "tmp_salvage/error-inventory.candidate.csv"
    fieldnames_err = [
        "example_id", "fold", "utterance", "true_intent",
        "predicted_intent", "confidence", "model_path", "model_sha256", "confusion_pair"
    ]
    with open(tmp_error_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames_err)
        w.writeheader()
        for r in error_rows:
            w.writerow(r)
    os.replace(tmp_error_csv, error_csv_path)
    
    # 11. Data Freeze Checks
    dev_sha = get_file_sha256(dev_path)
    assert dev_sha == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    holdout_sha = get_file_sha256(holdout_path)
    assert holdout_sha == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    
    # 12. Step 4 Manifest
    artifacts = [
        oof_metrics_path,
        fold_metrics_csv_path,
        fold_metrics_json_path,
        aggregate_json_path,
        per_intent_csv_path,
        error_csv_path,
        cm_json_path,
        cm_png_path
    ]
    gen_art_meta = {}
    for art in artifacts:
        gen_art_meta[art.name] = {
            "path": str(art.relative_to(repo_root)),
            "size_bytes": art.stat().st_size,
            "sha256": get_file_sha256(art)
        }
        
    step4_manifest_data = {
        "source_oof_path": str(oof_path.relative_to(repo_root)),
        "source_oof_sha256": oof_sha,
        "generated_artifacts": gen_art_meta,
        "oof_counts": {
            "rows": 800,
            "correct": total_correct,
            "errors": total_errors
        },
        "oof_metrics": oof_metrics,
        "fold_metrics_source": fold_csv_sources,
        "aggregate": {
            "n_folds": 5,
            "ddof": 1,
            "means": {k: aggregate_dict["metrics"][k]["mean"] for k in metric_keys},
            "sample_sds": {k: aggregate_dict["metrics"][k]["sample_sd"] for k in metric_keys}
        },
        "confusion": {
            "total": cm_total,
            "diagonal": cm_diag,
            "off_diagonal": cm_offdiag
        },
        "error_inventory_rows": len(error_rows),
        "per_intent_support_total": int(np.sum(sup_per)),
        "development_sha256": dev_sha,
        "holdout_sha256": holdout_sha,
        "holdout_evaluated": False,
        "training_executed": False
    }
    
    step4_manifest_path = results_dir / "step-4-metrics-manifest.json"
    tmp_s4_man = repo_root / "tmp_salvage/step-4-metrics-manifest.candidate.json"
    with open(tmp_s4_man, "w", encoding="utf-8") as f:
        json.dump(step4_manifest_data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_s4_man, step4_manifest_path)
    
    # 13. Reopen & Verify All Physical Artifacts
    for art in artifacts + [step4_manifest_path]:
        assert art.exists(), f"Artifact missing: {art}"
        assert art.stat().st_size > 0, f"Artifact empty: {art}"
        sha = get_file_sha256(art)
        assert len(sha) == 64
        print(f"Verified: {art.name:30s} | Size: {art.stat().st_size:7d} bytes | SHA: {sha}")
        
    print("\nALL STEP 4 GATES PASSED")

if __name__ == "__main__":
    main()
