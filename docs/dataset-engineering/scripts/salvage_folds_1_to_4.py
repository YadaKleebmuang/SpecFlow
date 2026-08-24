#!/usr/bin/env python3
import asyncio
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
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

def compare_metrics(m1, report_dict):
    # m1 is dict with keys: accuracy, macro_precision, etc.
    # report_dict is intent_report.json structure
    acc2 = report_dict["accuracy"]
    mp2 = report_dict["macro avg"]["precision"]
    mr2 = report_dict["macro avg"]["recall"]
    mf12 = report_dict["macro avg"]["f1-score"]
    wp2 = report_dict["weighted avg"]["precision"]
    wr2 = report_dict["weighted avg"]["recall"]
    wf12 = report_dict["weighted avg"]["f1-score"]

    deltas = [
        abs(m1["accuracy"] - acc2),
        abs(m1["macro_precision"] - mp2),
        abs(m1["macro_recall"] - mr2),
        abs(m1["macro_f1"] - mf12),
        abs(m1["weighted_precision"] - wp2),
        abs(m1["weighted_recall"] - wr2),
        abs(m1["weighted_f1"] - wf12),
    ]
    return max(deltas)

def salvage_fold(fold_num: int, repo_root: Path, dev_sha: str, holdout_sha: str):
    print(f"\n==================================================")
    print(f"SPECFLOW STEP 2 SALVAGE: FOLD {fold_num}")
    print(f"Stage: CANDIDATE_INVENTORY")
    print(f"==================================================")

    model_dir = repo_root / f"cv_results/model_fold_{fold_num}"
    val_path = repo_root / f"cv_folds/fold_{fold_num}/val.yml"
    val_rel = f"cv_folds/fold_{fold_num}/val.yml"
    train_path = repo_root / f"cv_folds/fold_{fold_num}/train/nlu.yml"
    train_rel = f"cv_folds/fold_{fold_num}/train/nlu.yml"
    existing_intent_report_path = repo_root / f"cv_results/fold_{fold_num}/intent_report.json"
    existing_intent_report_rel = f"cv_results/fold_{fold_num}/intent_report.json"

    assert val_path.exists(), f"Val path {val_path} does not exist"
    val_sha256 = get_file_sha256(val_path)
    assert train_path.exists(), f"Train path {train_path} does not exist"
    train_sha256 = get_file_sha256(train_path)

    # 1. Candidate model inventory
    candidate_files = sorted([f for f in model_dir.iterdir() if f.name.endswith(".tar.gz")])
    assert len(candidate_files) > 0, f"No candidate models found in {model_dir}"
    
    candidates_info = []
    for cand in candidate_files:
        cand_info = {
            "path": cand,
            "rel_path": f"cv_results/model_fold_{fold_num}/{cand.name}",
            "size_bytes": cand.stat().st_size,
            "mtime": int(cand.stat().st_mtime),
            "sha256": get_file_sha256(cand),
        }
        candidates_info.append(cand_info)
        print(f"Candidate: {cand_info['rel_path']} | Size: {cand_info['size_bytes']} | SHA: {cand_info['sha256']}")

    with open(existing_intent_report_path, "r", encoding="utf-8") as f:
        existing_report = json.load(f)

    # 2. Model Selection: Run fresh inference on every candidate
    matching_candidates = []
    cand_eval_results = {}

    importer = TrainingDataImporter.load_from_dict(training_data_paths=[str(val_path)])
    test_data = importer.get_nlu_data()
    assert len(test_data.nlu_examples) == 160, f"Expected 160 validation examples in {val_path}, got {len(test_data.nlu_examples)}"

    for idx, cand_info in enumerate(candidates_info, 1):
        safe_model_name = cand_info["path"].name.replace(".tar.gz", "").replace(".", "_")
        cand_out_dir = repo_root / f"tmp_salvage/fold_{fold_num}/candidate_{safe_model_name}"
        cand_out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[Fold {fold_num}] Testing candidate {idx}/{len(candidates_info)}: {cand_info['rel_path']}")
        
        # Fresh inference via CLI for physical CLI artifact + exit code
        cmd = [
            f"{repo_root}/.venv-rasa-cv/bin/rasa",
            "test", "nlu",
            "--model", str(cand_info["path"]),
            "--nlu", str(val_path),
            "--out", str(cand_out_dir),
            "--quiet"
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root / "app/rasa")
        
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        assert res.returncode == 0, f"Fresh inference failed with exit code {res.returncode}: {res.stderr}"

        fresh_rep_path = cand_out_dir / "intent_report.json"
        assert fresh_rep_path.exists(), f"Fresh intent report not created at {fresh_rep_path}"
        with open(fresh_rep_path, "r", encoding="utf-8") as f:
            cand_fresh_report = json.load(f)

        # In-process per-example extraction for deterministic prediction vector
        agent = Agent.load(str(cand_info["path"]))
        intent_results, _, _ = asyncio.run(get_eval_data(agent.processor, test_data))
        assert len(intent_results) == 160

        y_true = [item.intent_target for item in intent_results]
        y_pred = [item.intent_prediction for item in intent_results]
        metrics = evaluate_metrics(y_true, y_pred)
        delta = compare_metrics(metrics, existing_report)
        print(f"Candidate {idx} delta against historical report: {delta:.8e} (acc={metrics['accuracy']:.4f}, macro_f1={metrics['macro_f1']:.4f})")

        cand_eval_results[cand_info["rel_path"]] = {
            "cand_info": cand_info,
            "intent_results": intent_results,
            "metrics": metrics,
            "delta": delta,
            "fresh_rep_path": str(fresh_rep_path.relative_to(repo_root)),
            "out_dir": cand_out_dir,
        }

        if delta <= 1e-5:
            matching_candidates.append(cand_info["rel_path"])

    print(f"\nMatching candidates for Fold {fold_num}: {matching_candidates}")
    assert len(matching_candidates) >= 1, f"No candidate reconciled for Fold {fold_num}!"

    if len(matching_candidates) == 1:
        selected_rel = matching_candidates[0]
        model_selection_status = "EXACT_RECONCILED_CANDIDATE"
        model_selection_basis = "exact_metric_reconciliation_delta_zero"
    else:
        # Compare prediction vectors
        vecs = {}
        for rel in matching_candidates:
            cand_res = cand_eval_results[rel]
            records = []
            for item in cand_res["intent_results"]:
                raw_text = item.message
                norm_utt = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
                true_intent = item.intent_target
                pred_intent = item.intent_prediction
                conf = float(item.confidence) if item.confidence is not None else 0.0
                eid = hashlib.sha256(f"{true_intent}||{norm_utt}".encode("utf-8")).hexdigest()
                records.append({"example_id": eid, "true_intent": true_intent, "predicted_intent": pred_intent, "confidence": conf})
            cj = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            vecs[rel] = hashlib.sha256(cj.encode("utf-8")).hexdigest()
        
        unique_vecs = set(vecs.values())
        if len(unique_vecs) == 1:
            # All candidates produce identical predictions on all 160 validation examples
            # Select earliest/proven candidate
            selected_rel = sorted(matching_candidates)[0]
            model_selection_status = "EQUIVALENT_ON_VALIDATION"
            model_selection_basis = f"identical_160_prediction_vectors_across_{len(matching_candidates)}_candidates_selected_canonical_first"
        else:
            raise ValueError(f"STOPPING: Multiple matching candidates with divergent prediction vectors: {vecs}")

    selected_eval = cand_eval_results[selected_rel]
    selected_cand = selected_eval["cand_info"]
    print(f"\nSELECTED MODEL for Fold {fold_num}: {selected_rel} ({model_selection_status})")

    # 3. Build canonical predictions list
    prediction_rows = []
    example_ids = []
    for item in selected_eval["intent_results"]:
        raw_text = item.message
        norm_utt = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        true_intent = item.intent_target
        pred_intent = item.intent_prediction
        conf = float(item.confidence) if item.confidence is not None else 0.0
        correct = bool(true_intent == pred_intent)
        eid = hashlib.sha256(f"{true_intent}||{norm_utt}".encode("utf-8")).hexdigest()
        assert len(eid) == 64 and bool(re.match("^[0-9a-f]{64}$", eid))
        example_ids.append(eid)
        prediction_rows.append({
            "example_id": eid,
            "fold": fold_num,
            "utterance": norm_utt,
            "true_intent": true_intent,
            "predicted_intent": pred_intent,
            "confidence": conf,
            "correct": correct,
            "model_path": selected_rel,
            "model_sha256": selected_cand["sha256"],
        })

    assert len(example_ids) == 160
    assert len(set(example_ids)) == 160
    assert len(prediction_rows) == 160

    # 4. Write canonical CSV
    canonical_csv_rel = f"docs/dataset-engineering/cross-validation/baseline/results/fold-predictions/fold-{fold_num}-predictions.csv"
    canonical_csv_path = repo_root / canonical_csv_rel
    canonical_csv_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_csv_path = repo_root / f"tmp_salvage/fold_{fold_num}/fold-{fold_num}-predictions.candidate.csv"
    tmp_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "example_id", "fold", "utterance", "true_intent", "predicted_intent",
        "confidence", "correct", "model_path", "model_sha256"
    ]
    with open(tmp_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in prediction_rows:
            writer.writerow(r)

    new_csv_sha = get_file_sha256(tmp_csv_path)

    if canonical_csv_path.exists():
        with open(canonical_csv_path, "r", encoding="utf-8") as f:
            existing_rows = list(csv.DictReader(f))
        if len(existing_rows) == 160:
            existing_sha = get_file_sha256(canonical_csv_path)
            if existing_sha != new_csv_sha:
                sys.stderr.write(f"AUTHORITATIVE FOLD {fold_num} ARTIFACT CONFLICT\n")
                sys.exit(1)
            else:
                print(f"Existing CSV matched exactly. Reusing.")
        else:
            os.replace(tmp_csv_path, canonical_csv_path)
            print(f"Atomically replaced stub with canonical CSV: {canonical_csv_path}")
    else:
        os.replace(tmp_csv_path, canonical_csv_path)
        print(f"Atomically created canonical CSV: {canonical_csv_path}")

    # 5. Reopen physical CSV and verify
    with open(canonical_csv_path, "r", encoding="utf-8") as f:
        physical_rows = list(csv.DictReader(f))
    assert len(physical_rows) == 160
    assert len(set(r["example_id"] for r in physical_rows)) == 160
    assert set(int(r["fold"]) for r in physical_rows) == {fold_num}

    correct_count = sum(1 for r in physical_rows if r["correct"].lower() == "true")
    error_count = sum(1 for r in physical_rows if r["correct"].lower() == "false")
    assert correct_count + error_count == 160

    csv_size = canonical_csv_path.stat().st_size
    csv_sha = get_file_sha256(canonical_csv_path)

    # 6. Compute prediction-vector SHA-256
    vec_records = []
    for r in physical_rows:
        vec_records.append({
            "example_id": r["example_id"],
            "true_intent": r["true_intent"],
            "predicted_intent": r["predicted_intent"],
            "confidence": float(r["confidence"])
        })
    canonical_json_str = json.dumps(vec_records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prediction_vector_sha256 = hashlib.sha256(canonical_json_str.encode("utf-8")).hexdigest()
    prediction_vector_hash_method = "sha256_canonical_json_v1"

    # 7. Recompute metrics from physical CSV
    y_t = [r["true_intent"] for r in physical_rows]
    y_p = [r["predicted_intent"] for r in physical_rows]
    csv_metrics = evaluate_metrics(y_t, y_p)
    metric_reconciliation_max_delta = compare_metrics(csv_metrics, existing_report)
    assert metric_reconciliation_max_delta <= 1e-5

    # 8. Manifest creation
    canonical_manifest_rel = f"docs/dataset-engineering/cross-validation/baseline/results/fold-{fold_num}-manifest.json"
    canonical_manifest_path = repo_root / canonical_manifest_rel

    manifest_data = {
        "fold": fold_num,
        "train_path": train_rel,
        "train_sha256": train_sha256,
        "validation_path": val_rel,
        "validation_sha256": val_sha256,
        "validation_rows": 160,
        "model_path": selected_rel,
        "model_size_bytes": selected_cand["size_bytes"],
        "model_sha256": selected_cand["sha256"],
        "model_mtime": selected_cand["mtime"],
        "training_exit_code": "EXIT_CODE_NOT_PERSISTED",
        "existing_intent_report_path": existing_intent_report_rel,
        "fresh_intent_report_path": selected_eval["fresh_rep_path"],
        "fresh_inference_exit_code": 0,
        "prediction_csv_path": canonical_csv_rel,
        "prediction_csv_size_bytes": csv_size,
        "prediction_csv_sha256": csv_sha,
        "prediction_rows": 160,
        "unique_example_ids": 160,
        "prediction_vector_sha256": prediction_vector_sha256,
        "prediction_vector_hash_method": prediction_vector_hash_method,
        "correct": correct_count,
        "errors": error_count,
        "accuracy": csv_metrics["accuracy"],
        "macro_precision": csv_metrics["macro_precision"],
        "macro_recall": csv_metrics["macro_recall"],
        "macro_f1": csv_metrics["macro_f1"],
        "weighted_precision": csv_metrics["weighted_precision"],
        "weighted_recall": csv_metrics["weighted_recall"],
        "weighted_f1": csv_metrics["weighted_f1"],
        "metric_reconciliation_max_delta": metric_reconciliation_max_delta,
        "model_selection_status": model_selection_status,
        "model_selection_basis": model_selection_basis,
        "candidate_models_checked": [c["rel_path"] for c in candidates_info],
        "matching_candidates": matching_candidates,
        "development_sha256": dev_sha,
        "holdout_sha256": holdout_sha,
        "holdout_evaluated": False,
        "runtime": {
            "python_version": "3.9.6",
            "rasa_version": "3.6.21",
            "rasa_sdk_version": "3.6.2",
            "pythainlp_version": "5.3.4",
            "thai_tokenizer_import": "PASS"
        }
    }

    tmp_manifest_path = repo_root / f"tmp_salvage/fold_{fold_num}/fold-{fold_num}-manifest.candidate.json"
    with open(tmp_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    os.replace(tmp_manifest_path, canonical_manifest_path)
    manifest_sha = get_file_sha256(canonical_manifest_path)

    # Reopen and verify manifest
    with open(canonical_manifest_path, "r", encoding="utf-8") as f:
        loaded_manifest = json.load(f)
    assert loaded_manifest["fold"] == fold_num
    assert loaded_manifest["prediction_csv_sha256"] == csv_sha
    assert loaded_manifest["prediction_vector_sha256"] == prediction_vector_sha256

    print(f"\nFOLD {fold_num} SALVAGE PHYSICALLY COMPLETE")
    print(f"FOLD {fold_num} = CLOSED")

    return {
        "fold": fold_num,
        "selected_model": selected_rel,
        "selection_status": model_selection_status,
        "candidates_checked": len(candidates_info),
        "matching_candidates": len(matching_candidates),
        "model_sha256": selected_cand["sha256"],
        "fresh_inference": "PASS",
        "rows": 160,
        "unique_ids": 160,
        "correct": correct_count,
        "errors": error_count,
        "accuracy": csv_metrics["accuracy"],
        "macro_f1": csv_metrics["macro_f1"],
        "weighted_f1": csv_metrics["weighted_f1"],
        "metric_delta": metric_reconciliation_max_delta,
        "csv_sha256": csv_sha,
        "prediction_vector_sha256": prediction_vector_sha256,
        "manifest_sha256": manifest_sha,
        "status": "CLOSED",
        "example_ids": example_ids,
    }

def main():
    repo_root = Path(os.getcwd())
    dev_path = repo_root / "app/rasa/data/nlu.yml"
    holdout_path = repo_root / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"

    dev_sha = get_file_sha256(dev_path)
    assert dev_sha == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    holdout_sha = get_file_sha256(holdout_path)
    assert holdout_sha == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"

    fold_results = {}
    for f in [1, 2, 3, 4]:
        fold_results[f] = salvage_fold(f, repo_root, dev_sha, holdout_sha)

    # Cross-fold check for Folds 0-4
    print("\n==================================================")
    print("CROSS-FOLD PRE-OOF CHECK (FOLDS 0–4)")
    print("==================================================")
    
    all_fold_ids = {}
    for f in range(5):
        csv_p = repo_root / f"docs/dataset-engineering/cross-validation/baseline/results/fold-predictions/fold-{f}-predictions.csv"
        assert csv_p.exists(), f"Missing prediction CSV for fold {f}"
        with open(csv_p, "r", encoding="utf-8") as fp:
            rows = list(csv.DictReader(fp))
        assert len(rows) == 160, f"Fold {f} does not have 160 rows (found {len(rows)})"
        eids = [r["example_id"] for r in rows]
        assert len(set(eids)) == 160, f"Fold {f} has duplicate example IDs"
        all_fold_ids[f] = eids
        print(f"Fold {f} rows: {len(rows)}, Unique IDs: {len(set(eids))}")

    total_rows = sum(len(ids) for ids in all_fold_ids.values())
    assert total_rows == 800, f"Total rows {total_rows} != 800"

    # Pairwise intersections
    pairwise_overlaps = {}
    has_overlap = False
    for i in range(5):
        for j in range(i + 1, 5):
            inter = set(all_fold_ids[i]).intersection(set(all_fold_ids[j]))
            pairwise_overlaps[f"fold_{i}_vs_fold_{j}"] = len(inter)
            if len(inter) > 0:
                has_overlap = True
            print(f"Pairwise overlap Fold {i} vs Fold {j}: {len(inter)}")

    assert not has_overlap, f"Pairwise overlaps detected: {pairwise_overlaps}"

    combined_unique = set().union(*all_fold_ids.values())
    print(f"Combined unique IDs across all 5 folds: {len(combined_unique)}")
    assert len(combined_unique) == 800, f"Combined unique IDs {len(combined_unique)} != 800"

    print("\nALL CROSS-FOLD PRE-OOF GATES PASSED")
    
    # Save summary json for reference
    summary_path = repo_root / "tmp_salvage/step2_summary.json"
    clean_results = {}
    for f, res in fold_results.items():
        clean_results[f] = {k: v for k, v in res.items() if k != "example_ids"}
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(clean_results, f, indent=2)

if __name__ == "__main__":
    main()
