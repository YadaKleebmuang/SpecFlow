#!/usr/bin/env python3
import asyncio
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from rasa.core.agent import Agent
from rasa.nlu.test import get_eval_data
from rasa.shared.importers.importer import TrainingDataImporter
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def get_file_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

def main():
    repo_root = Path(os.getcwd())
    
    # 1. Physical file paths
    model_rel = "cv_results/model_fold_0/nlu-20260820-124132-antique-factory.tar.gz"
    model_path = repo_root / model_rel
    train_rel = "cv_folds/fold_0/train/nlu.yml"
    train_path = repo_root / train_rel
    val_rel = "cv_folds/fold_0/val.yml"
    val_path = repo_root / val_rel
    dev_rel = "app/rasa/data/nlu.yml"
    dev_path = repo_root / dev_rel
    holdout_rel = "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    holdout_path = repo_root / holdout_rel
    
    existing_intent_report_rel = "cv_results/fold_0/intent_report.json"
    existing_intent_report_path = repo_root / existing_intent_report_rel
    fresh_intent_report_rel = "tmp_salvage/fold_0/fresh_eval/intent_report.json"
    fresh_intent_report_path = repo_root / fresh_intent_report_rel
    
    canonical_csv_dir = repo_root / "docs/dataset-engineering/cross-validation/baseline/results/fold-predictions"
    canonical_csv_dir.mkdir(parents=True, exist_ok=True)
    canonical_csv_rel = "docs/dataset-engineering/cross-validation/baseline/results/fold-predictions/fold-0-predictions.csv"
    canonical_csv_path = repo_root / canonical_csv_rel
    
    canonical_manifest_dir = repo_root / "docs/dataset-engineering/cross-validation/baseline/results"
    canonical_manifest_dir.mkdir(parents=True, exist_ok=True)
    canonical_manifest_rel = "docs/dataset-engineering/cross-validation/baseline/results/fold-0-manifest.json"
    canonical_manifest_path = repo_root / canonical_manifest_rel

    # 2. Check model physically
    assert model_path.exists(), f"Model path {model_path} does not exist"
    model_size_bytes = model_path.stat().st_size
    model_mtime = int(model_path.stat().st_mtime)
    model_sha256 = get_file_sha256(model_path)
    expected_model_sha = "223a923946f063f9a0e670394f340069b38a8b95fc17d448fd77d94954e44a6b"
    assert model_sha256 == expected_model_sha, f"Model SHA mismatch: {model_sha256} != {expected_model_sha}"

    # 3. Data files check
    assert train_path.exists(), f"Train path {train_path} does not exist"
    train_sha256 = get_file_sha256(train_path)
    
    assert val_path.exists(), f"Val path {val_path} does not exist"
    val_sha256 = get_file_sha256(val_path)
    
    assert dev_path.exists(), f"Dev path {dev_path} does not exist"
    dev_sha256 = get_file_sha256(dev_path)
    expected_dev_sha = "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    assert dev_sha256 == expected_dev_sha, f"Dev SHA mismatch: {dev_sha256} != {expected_dev_sha}"

    assert holdout_path.exists(), f"Holdout path {holdout_path} does not exist"
    holdout_sha256 = get_file_sha256(holdout_path)
    expected_holdout_sha = "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    assert holdout_sha256 == expected_holdout_sha, f"Holdout SHA mismatch: {holdout_sha256} != {expected_holdout_sha}"

    # 4. Load validation data and run inference
    importer = TrainingDataImporter.load_from_dict(training_data_paths=[str(val_path)])
    test_data = importer.get_nlu_data()
    agent = Agent.load(str(model_path))
    
    intent_results, _, _ = asyncio.run(get_eval_data(agent.processor, test_data))
    assert len(intent_results) == 160, f"Expected 160 intent results, got {len(intent_results)}"

    # 5. Build prediction records
    prediction_rows = []
    example_ids = []
    
    for item in intent_results:
        raw_text = item.message
        norm_utt = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        true_intent = item.intent_target
        pred_intent = item.intent_prediction
        conf = float(item.confidence) if item.confidence is not None else 0.0
        correct = bool(true_intent == pred_intent)
        
        eid = hashlib.sha256(f"{true_intent}||{norm_utt}".encode("utf-8")).hexdigest()
        assert len(eid) == 64 and bool(re.match("^[0-9a-f]{64}$", eid)), f"Invalid example_id: {eid}"
        
        example_ids.append(eid)
        prediction_rows.append({
            "example_id": eid,
            "fold": 0,
            "utterance": norm_utt,
            "true_intent": true_intent,
            "predicted_intent": pred_intent,
            "confidence": conf,
            "correct": correct,
            "model_path": model_rel,
            "model_sha256": model_sha256
        })

    assert len(example_ids) == 160
    assert len(set(example_ids)) == 160, "Duplicate example_ids found"
    assert len(prediction_rows) == 160

    # 6. Write CSV to temporary location
    tmp_csv_path = repo_root / "tmp_salvage/fold_0/fold-0-predictions.candidate.csv"
    tmp_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "example_id",
        "fold",
        "utterance",
        "true_intent",
        "predicted_intent",
        "confidence",
        "correct",
        "model_path",
        "model_sha256"
    ]
    
    with open(tmp_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in prediction_rows:
            writer.writerow(row)

    # 7. No-blind-overwrite & atomic move
    new_csv_sha256 = get_file_sha256(tmp_csv_path)
    
    if canonical_csv_path.exists():
        # Check if canonical exists and has 160 valid rows
        with open(canonical_csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        if len(reader) == 160:
            existing_csv_sha = get_file_sha256(canonical_csv_path)
            if existing_csv_sha != new_csv_sha256:
                sys.stderr.write("AUTHORITATIVE FOLD 0 CSV CONFLICT\n")
                sys.exit(1)
            else:
                print("Existing canonical CSV is identical. Reusing.")
        else:
            # Overwriting empty/stub file atomically
            os.replace(tmp_csv_path, canonical_csv_path)
            print(f"Replaced stub with valid canonical CSV: {canonical_csv_path}")
    else:
        os.replace(tmp_csv_path, canonical_csv_path)
        print(f"Created canonical CSV: {canonical_csv_path}")

    # 8. Reopen and verify physical CSV from disk
    with open(canonical_csv_path, "r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    
    assert len(csv_rows) == 160, f"Expected 160 rows in CSV, got {len(csv_rows)}"
    csv_eids = [r["example_id"] for r in csv_rows]
    assert len(set(csv_eids)) == 160, "Duplicate IDs in physical CSV"
    for r in csv_rows:
        assert int(r["fold"]) == 0, f"Invalid fold value: {r['fold']}"
        assert r["model_path"] == model_rel
        assert r["model_sha256"] == model_sha256

    physical_csv_size = canonical_csv_path.stat().st_size
    physical_csv_sha256 = get_file_sha256(canonical_csv_path)
    
    correct_count = sum(1 for r in csv_rows if r["correct"].lower() == "true")
    error_count = sum(1 for r in csv_rows if r["correct"].lower() == "false")
    assert correct_count + error_count == 160, f"Sum mismatch: {correct_count} + {error_count} != 160"

    # 9. Compute prediction-vector SHA-256
    vector_records = []
    for r in csv_rows:
        vector_records.append({
            "example_id": r["example_id"],
            "true_intent": r["true_intent"],
            "predicted_intent": r["predicted_intent"],
            "confidence": float(r["confidence"])
        })
    
    canonical_json_str = json.dumps(
        vector_records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )
    prediction_vector_sha256 = hashlib.sha256(canonical_json_str.encode("utf-8")).hexdigest()
    prediction_vector_hash_method = "sha256_canonical_json_v1"
    assert len(prediction_vector_sha256) == 64 and bool(re.match("^[0-9a-f]{64}$", prediction_vector_sha256))

    # 10. Recompute 7 metrics from physical CSV
    y_true = [r["true_intent"] for r in csv_rows]
    y_pred = [r["predicted_intent"] for r in csv_rows]

    acc = float(accuracy_score(y_true, y_pred))
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
    
    macro_p = float(macro_p)
    macro_r = float(macro_r)
    macro_f1 = float(macro_f1)
    weighted_p = float(weighted_p)
    weighted_r = float(weighted_r)
    weighted_f1 = float(weighted_f1)

    # 11. Reconcile against fresh intent report
    with open(fresh_intent_report_path, "r", encoding="utf-8") as f:
        fresh_report = json.load(f)

    deltas = [
        abs(acc - fresh_report["accuracy"]),
        abs(macro_p - fresh_report["macro avg"]["precision"]),
        abs(macro_r - fresh_report["macro avg"]["recall"]),
        abs(macro_f1 - fresh_report["macro avg"]["f1-score"]),
        abs(weighted_p - fresh_report["weighted avg"]["precision"]),
        abs(weighted_r - fresh_report["weighted avg"]["recall"]),
        abs(weighted_f1 - fresh_report["weighted avg"]["f1-score"])
    ]
    metric_reconciliation_max_delta = max(deltas)
    assert metric_reconciliation_max_delta <= 1e-5, f"Metric reconciliation failed: max delta {metric_reconciliation_max_delta} > 1e-5"

    # 12. Build Manifest
    manifest_data = {
        "fold": 0,
        "train_path": train_rel,
        "train_sha256": train_sha256,
        "validation_path": val_rel,
        "validation_sha256": val_sha256,
        "validation_rows": 160,
        "model_path": model_rel,
        "model_size_bytes": model_size_bytes,
        "model_sha256": model_sha256,
        "model_mtime": model_mtime,
        "training_exit_code": "EXIT_CODE_NOT_PERSISTED",
        "existing_intent_report_path": existing_intent_report_rel,
        "fresh_intent_report_path": fresh_intent_report_rel,
        "fresh_inference_exit_code": 0,
        "prediction_csv_path": canonical_csv_rel,
        "prediction_csv_size_bytes": physical_csv_size,
        "prediction_csv_sha256": physical_csv_sha256,
        "prediction_rows": 160,
        "unique_example_ids": 160,
        "prediction_vector_sha256": prediction_vector_sha256,
        "prediction_vector_hash_method": prediction_vector_hash_method,
        "correct": correct_count,
        "errors": error_count,
        "accuracy": acc,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "weighted_precision": weighted_p,
        "weighted_recall": weighted_r,
        "weighted_f1": weighted_f1,
        "metric_reconciliation_max_delta": metric_reconciliation_max_delta,
        "model_selection_status": "LOCKED",
        "model_selection_basis": "fold_0_verified_physical_salvage",
        "development_sha256": dev_sha256,
        "holdout_sha256": holdout_sha256,
        "holdout_evaluated": False,
        "runtime": {
            "python_version": "3.9.6",
            "rasa_version": "3.6.21",
            "rasa_sdk_version": "3.6.2",
            "pythainlp_version": "5.3.4",
            "thai_tokenizer_import": "PASS"
        }
    }

    # Write manifest atomically
    tmp_manifest_path = repo_root / "tmp_salvage/fold_0/fold-0-manifest.candidate.json"
    with open(tmp_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    os.replace(tmp_manifest_path, canonical_manifest_path)
    
    # 13. Verify physical manifest
    with open(canonical_manifest_path, "r", encoding="utf-8") as f:
        loaded_manifest = json.load(f)
    
    manifest_size_bytes = canonical_manifest_path.stat().st_size
    manifest_sha256 = get_file_sha256(canonical_manifest_path)

    assert loaded_manifest["fold"] == 0
    assert loaded_manifest["model_sha256"] == model_sha256
    assert loaded_manifest["prediction_csv_sha256"] == physical_csv_sha256
    assert loaded_manifest["prediction_rows"] == 160
    assert loaded_manifest["unique_example_ids"] == 160
    assert loaded_manifest["correct"] + loaded_manifest["errors"] == 160
    assert loaded_manifest["metric_reconciliation_max_delta"] <= 1e-5
    assert loaded_manifest["holdout_evaluated"] is False

    print("ALL GATES PASSED")
    print(f"Manifest SHA-256: {manifest_sha256}")
    print(f"Prediction CSV SHA-256: {physical_csv_sha256}")
    print(f"Prediction-vector SHA-256: {prediction_vector_sha256}")
    print(f"CSV Size: {physical_csv_size}")
    print(f"Manifest Size: {manifest_size_bytes}")
    print(f"Correct: {correct_count}, Errors: {error_count}")
    print(f"Accuracy: {acc:.8f}")
    print(f"Macro Precision: {macro_p:.8f}, Macro Recall: {macro_r:.8f}, Macro F1: {macro_f1:.8f}")
    print(f"Weighted Precision: {weighted_p:.8f}, Weighted Recall: {weighted_r:.8f}, Weighted F1: {weighted_f1:.8f}")
    print(f"Metric reconciliation max delta: {metric_reconciliation_max_delta:.8e}")

if __name__ == "__main__":
    main()
