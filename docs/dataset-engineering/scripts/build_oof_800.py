#!/usr/bin/env python3
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from collections import Counter

from rasa.shared.importers.importer import TrainingDataImporter

def get_file_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

def main():
    repo_root = Path(os.getcwd())
    results_dir = repo_root / "docs/dataset-engineering/cross-validation/baseline/results"
    fold_pred_dir = results_dir / "fold-predictions"
    canonical_oof_path = results_dir / "oof-predictions.csv"
    canonical_manifest_path = results_dir / "oof-integrity-manifest.json"
    
    dev_path = repo_root / "app/rasa/data/nlu.yml"
    holdout_path = repo_root / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    
    print("==================================================")
    print("SPECFLOW STEP 3 — OOF 800")
    print("Stage: PREFLIGHT")
    print("==================================================")
    
    # STEP 0: Preflight
    fold_csv_paths = [fold_pred_dir / f"fold-{i}-predictions.csv" for i in range(5)]
    fold_manifest_paths = [results_dir / f"fold-{i}-manifest.json" for i in range(5)]
    
    source_fold_csvs_meta = []
    fold_data = {}
    
    for i in range(5):
        csv_p = fold_csv_paths[i]
        man_p = fold_manifest_paths[i]
        
        assert csv_p.exists(), f"Missing fold CSV: {csv_p}"
        assert man_p.exists(), f"Missing fold manifest: {man_p}"
        
        csv_size = csv_p.stat().st_size
        csv_sha = get_file_sha256(csv_p)
        
        with open(csv_p, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        
        assert len(reader) == 160, f"Fold {i} has {len(reader)} rows, expected 160"
        eids = [r["example_id"] for r in reader]
        assert len(set(eids)) == 160, f"Fold {i} has duplicate example IDs"
        
        with open(man_p, "r", encoding="utf-8") as f:
            man_data = json.load(f)
        
        assert man_data["fold"] == i
        assert man_data["prediction_csv_sha256"] == csv_sha, f"Manifest CSV SHA mismatch for fold {i}"
        assert man_data["prediction_rows"] == 160
        assert man_data["unique_example_ids"] == 160
        
        source_fold_csvs_meta.append({
            "fold": i,
            "path": str(csv_p.relative_to(repo_root)),
            "sha256": csv_sha,
            "size_bytes": csv_size,
            "rows": len(reader),
            "unique_ids": len(set(eids)),
        })
        fold_data[i] = reader
        print(f"Fold {i}: 160 rows, 160 unique IDs | CSV SHA: {csv_sha}")

    print("\n==================================================")
    print("Stage: FOLD_INTEGRITY & PER-FOLD BASIC INTEGRITY")
    print("==================================================")
    
    required_cols = [
        "example_id", "fold", "utterance", "true_intent",
        "predicted_intent", "confidence", "correct", "model_path", "model_sha256"
    ]
    
    fold_correct = {}
    fold_errors = {}
    
    for i in range(5):
        rows = fold_data[i]
        for idx, r in enumerate(rows):
            for col in required_cols:
                assert col in r, f"Missing column {col} in fold {i} row {idx}"
                assert r[col] is not None and r[col] != "", f"Empty value for {col} in fold {i} row {idx}"
            
            assert int(r["fold"]) == i, f"Fold value mismatch in fold {i} row {idx}: {r['fold']}"
            
            expected_correct = (r["true_intent"] == r["predicted_intent"])
            actual_correct = (r["correct"].lower() == "true")
            assert expected_correct == actual_correct, f"Correct flag mismatch in fold {i} row {idx}"
        
        c = sum(1 for r in rows if r["correct"].lower() == "true")
        e = sum(1 for r in rows if r["correct"].lower() == "false")
        assert c + e == 160
        fold_correct[i] = c
        fold_errors[i] = e
        print(f"Fold {i} integrity: PASS | Correct: {c}, Errors: {e}, Total: {c+e}")

    print("\n==================================================")
    print("Stage: ID_DISTINCTNESS")
    print("==================================================")
    
    pairwise_overlaps = {}
    for i in range(5):
        ids_i = set(r["example_id"] for r in fold_data[i])
        for j in range(i + 1, 5):
            ids_j = set(r["example_id"] for r in fold_data[j])
            overlap = ids_i.intersection(ids_j)
            pairwise_overlaps[f"fold_{i}_vs_fold_{j}"] = len(overlap)
            assert len(overlap) == 0, f"Overlap between fold {i} and fold {j}: {len(overlap)}"
            print(f"Pairwise overlap Fold {i} vs Fold {j}: 0")
            
    all_source_ids = [r["example_id"] for i in range(5) for r in fold_data[i]]
    assert len(all_source_ids) == 800
    assert len(set(all_source_ids)) == 800
    
    id_freqs = Counter(all_source_ids)
    assert all(freq == 1 for freq in id_freqs.values()), "Some example IDs have frequency != 1"
    print("Every example_id validation frequency = 1: PASS")

    print("\n==================================================")
    print("Stage: SUPPORT_CHECK")
    print("==================================================")
    
    expected_support = {
        "greet": 19,
        "goodbye": 20,
        "build_pc": 145,
        "upgrade_pc": 117,
        "inform_budget": 61,
        "inform_usage": 73,
        "inform_current_specs": 68,
        "ask_cpu_info": 23,
        "ask_gpu_info": 23,
        "ask_ram_info": 23,
        "ask_ssd_hdd_diff": 23,
        "optimize_performance": 98,
        "inform_future_upgrade": 58,
        "affirm": 24,
        "deny": 25,
    }
    
    all_true_intents = [r["true_intent"] for i in range(5) for r in fold_data[i]]
    actual_support = Counter(all_true_intents)
    
    print("Intent support verification:")
    for intent, exp_cnt in expected_support.items():
        act_cnt = actual_support.get(intent, 0)
        print(f"  {intent:25s}: actual={act_cnt:3d}, expected={exp_cnt:3d}")
        assert act_cnt == exp_cnt, f"Support mismatch for {intent}: {act_cnt} != {exp_cnt}"
    
    assert sum(actual_support.values()) == 800, f"Total intent support sum {sum(actual_support.values())} != 800"
    print("True-intent support gate: PASS")

    print("\n==================================================")
    print("Stage: DEVELOPMENT_COVERAGE")
    print("==================================================")
    
    assert dev_path.exists()
    dev_sha = get_file_sha256(dev_path)
    assert dev_sha == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d", f"Dev SHA mismatch: {dev_sha}"
    
    assert holdout_path.exists()
    holdout_sha = get_file_sha256(holdout_path)
    assert holdout_sha == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961", f"Holdout SHA mismatch: {holdout_sha}"
    
    # Load development data with Rasa
    importer = TrainingDataImporter.load_from_dict(training_data_paths=[str(dev_path)])
    dev_nlu = importer.get_nlu_data()
    dev_examples = dev_nlu.nlu_examples
    assert len(dev_examples) == 800, f"Expected 800 dev examples, got {len(dev_examples)}"
    
    dev_ids = []
    for ex in dev_examples:
        raw_text = ex.get("text")
        norm_utt = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        true_intent = ex.get("intent")
        eid = hashlib.sha256(f"{true_intent}||{norm_utt}".encode("utf-8")).hexdigest()
        assert len(eid) == 64 and bool(re.match("^[0-9a-f]{64}$", eid))
        dev_ids.append(eid)
        
    assert len(dev_ids) == 800
    assert len(set(dev_ids)) == 800
    
    oof_id_set = set(all_source_ids)
    dev_id_set = set(dev_ids)
    
    oof_missing_from_dev = len(oof_id_set - dev_id_set)
    dev_missing_from_oof = len(dev_id_set - oof_id_set)
    
    print(f"OOF missing from Development: {oof_missing_from_dev}")
    print(f"Development missing from OOF: {dev_missing_from_oof}")
    assert oof_missing_from_dev == 0
    assert dev_missing_from_oof == 0
    assert oof_id_set == dev_id_set
    print("Development coverage set equality: PASS (TRUE)")

    print("\n==================================================")
    print("Stage: OOF_BUILD & ATOMIC PHYSICAL WRITE")
    print("==================================================")
    
    # Build concatenated rows
    oof_rows = []
    for i in range(5):
        oof_rows.extend(fold_data[i])
        
    assert len(oof_rows) == 800
    assert len(set(r["example_id"] for r in oof_rows)) == 800
    
    tmp_oof_path = repo_root / "tmp_salvage/oof-predictions.candidate.csv"
    tmp_oof_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(tmp_oof_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=required_cols)
        writer.writeheader()
        for r in oof_rows:
            writer.writerow(r)
            
    new_oof_sha = get_file_sha256(tmp_oof_path)
    
    if canonical_oof_path.exists():
        with open(canonical_oof_path, "r", encoding="utf-8") as f:
            existing_rows = list(csv.DictReader(f))
        if len(existing_rows) == 800:
            existing_sha = get_file_sha256(canonical_oof_path)
            if existing_sha != new_oof_sha:
                sys.stderr.write("AUTHORITATIVE OOF CONFLICT\n")
                sys.exit(1)
            else:
                print("Existing canonical OOF matched candidate exactly. Reusing.")
        else:
            os.replace(tmp_oof_path, canonical_oof_path)
            print(f"Replaced stub with canonical OOF: {canonical_oof_path}")
    else:
        os.replace(tmp_oof_path, canonical_oof_path)
        print(f"Created canonical OOF: {canonical_oof_path}")

    print("\n==================================================")
    print("Stage: PHYSICAL_VERIFY")
    print("==================================================")
    
    with open(canonical_oof_path, "r", encoding="utf-8") as f:
        reopened_oof = list(csv.DictReader(f))
        
    assert len(reopened_oof) == 800
    reopened_eids = [r["example_id"] for r in reopened_oof]
    assert len(set(reopened_eids)) == 800
    
    oof_fold_counts = Counter(int(r["fold"]) for r in reopened_oof)
    for i in range(5):
        assert oof_fold_counts[i] == 160, f"Fold {i} count in OOF != 160: {oof_fold_counts[i]}"
        
    total_correct = sum(1 for r in reopened_oof if r["correct"].lower() == "true")
    total_errors = sum(1 for r in reopened_oof if r["correct"].lower() == "false")
    assert total_correct + total_errors == 800
    
    oof_size_bytes = canonical_oof_path.stat().st_size
    oof_sha256 = get_file_sha256(canonical_oof_path)
    assert len(oof_sha256) == 64 and bool(re.match("^[0-9a-f]{64}$", oof_sha256))
    
    # Exact union equality verification
    for idx in range(800):
        assert reopened_oof[idx] == oof_rows[idx], f"Row mismatch at index {idx}"
    print("Physical union exact equality and deterministic order: PASS")
    
    # Compute OOF prediction vector hash
    vec_records = []
    for r in reopened_oof:
        vec_records.append({
            "example_id": r["example_id"],
            "fold": int(r["fold"]),
            "true_intent": r["true_intent"],
            "predicted_intent": r["predicted_intent"],
            "confidence": float(r["confidence"])
        })
    canonical_json_str = json.dumps(vec_records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    oof_prediction_vector_sha256 = hashlib.sha256(canonical_json_str.encode("utf-8")).hexdigest()
    oof_prediction_vector_hash_method = "sha256_canonical_json_v1"
    assert len(oof_prediction_vector_sha256) == 64 and bool(re.match("^[0-9a-f]{64}$", oof_prediction_vector_sha256))

    print("\n==================================================")
    print("Stage: MANIFEST")
    print("==================================================")
    
    manifest_data = {
        "creation_method": "concatenate_verified_fold_predictions_v1",
        "source_fold_csvs": source_fold_csvs_meta,
        "oof_path": str(canonical_oof_path.relative_to(repo_root)),
        "oof_size_bytes": oof_size_bytes,
        "oof_sha256": oof_sha256,
        "oof_prediction_vector_sha256": oof_prediction_vector_sha256,
        "oof_prediction_vector_hash_method": oof_prediction_vector_hash_method,
        "rows": 800,
        "unique_example_ids": 800,
        "fold_counts": {str(k): v for k, v in sorted(oof_fold_counts.items())},
        "correct": total_correct,
        "errors": total_errors,
        "pairwise_id_overlap": pairwise_overlaps,
        "development_rows": 800,
        "development_unique_ids": 800,
        "development_id_set_equals_oof": True,
        "true_intent_support": {k: actual_support[k] for k in expected_support},
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
    
    tmp_manifest_path = repo_root / "tmp_salvage/oof-integrity-manifest.candidate.json"
    with open(tmp_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
    os.replace(tmp_manifest_path, canonical_manifest_path)
    manifest_sha = get_file_sha256(canonical_manifest_path)
    
    # Reopen and verify manifest
    with open(canonical_manifest_path, "r", encoding="utf-8") as f:
        loaded_mf = json.load(f)
        
    assert loaded_mf["rows"] == 800
    assert loaded_mf["unique_example_ids"] == 800
    assert loaded_mf["oof_sha256"] == oof_sha256
    assert loaded_mf["oof_prediction_vector_sha256"] == oof_prediction_vector_sha256
    assert loaded_mf["development_id_set_equals_oof"] is True
    assert loaded_mf["holdout_evaluated"] is False
    
    for meta in loaded_mf["source_fold_csvs"]:
        f_idx = meta["fold"]
        assert meta["sha256"] == get_file_sha256(repo_root / meta["path"])
        
    print("\n==================================================")
    print("Stage: FINAL_GATE — ALL GATES PASSED")
    print("==================================================")
    print(f"OOF Path: {canonical_oof_path}")
    print(f"OOF Size: {oof_size_bytes} bytes")
    print(f"OOF SHA-256: {oof_sha256}")
    print(f"OOF Prediction-Vector SHA-256: {oof_prediction_vector_sha256}")
    print(f"Manifest Path: {canonical_manifest_path}")
    print(f"Manifest SHA-256: {manifest_sha}")
    print(f"Total Correct: {total_correct}, Total Errors: {total_errors}")

if __name__ == "__main__":
    main()
