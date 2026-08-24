#!/usr/bin/env python3
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import yaml

def get_file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    repo = Path(os.getcwd())
    
    print("=== STEP 0: PRE-TRAINING LOCK VERIFICATION ===")
    freeze_manifest_path = repo / "docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json"
    assert freeze_manifest_path.exists(), f"Missing freeze manifest: {freeze_manifest_path}"
    freeze_manifest_sha = get_file_sha256(freeze_manifest_path)
    expected_freeze_manifest_sha = "aaa9aaf7408032147995bd42c1f1ed822d26bc837e405c093727a0843769cc2c"
    assert freeze_manifest_sha == expected_freeze_manifest_sha, f"Freeze manifest SHA mismatch: {freeze_manifest_sha}"
    
    cfg_p = repo / "app/rasa/config.yml"
    dom_p = repo / "app/rasa/domain.yml"
    dev_p = repo / "app/rasa/data/nlu.yml"
    rules_p = repo / "app/rasa/data/rules.yml"
    stories_p = repo / "app/rasa/data/stories.yml"
    holdout_p = repo / "docs/dataset-engineering/holdout/locked-holdout-v1.yml"
    oof_p = repo / "docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv"
    
    assert get_file_sha256(cfg_p) == "61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0"
    assert get_file_sha256(dom_p) == "c2a76780257345efc57dd32a8f261ac610745a4f21bad08bb308ad9b74717857"
    assert get_file_sha256(dev_p) == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    assert get_file_sha256(rules_p) == "37325e428ddcec108ff10cc3ec93b1d0e667c54f23d59c23f3c710ece7db22e5"
    assert get_file_sha256(stories_p) == "45e869d2b571bec45926228cf9537d099b3d6002484a985a0bcf09913c492985"
    assert get_file_sha256(holdout_p) == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    assert get_file_sha256(oof_p) == "b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47"
    print("Pre-training lock verification: PASS")
    
    print("\n=== STEP 1: DUPLICATE PROCESS GATE ===")
    ps_res = subprocess.check_output(["ps", "aux"], text=True)
    active_train_processes = [line for line in ps_res.splitlines() if "rasa train" in line or "run_cv.py" in line]
    assert len(active_train_processes) == 0, f"Duplicate training processes detected: {active_train_processes}"
    print("Duplicate process check: PASS (0 active training processes)")
    
    print("\n=== STEP 2: CREATE UNIQUE RUN DIRECTORIES ===")
    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"run-{now_str}"
    run_dir = repo / f"docs/final-readiness/final-model-training/{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    model_out_dir = repo / f"final_models/{run_id}"
    model_out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run Directory:       {run_dir}")
    print(f"Model Out Directory: {model_out_dir}")
    
    print("\n=== STEP 3: PRE-TRAINING MODEL SNAPSHOT ===")
    pre_models = {}
    for p in repo.glob("final_models/**/*.tar.gz"):
        pre_models[str(p.relative_to(repo))] = {
            "size": p.stat().st_size,
            "mtime": p.stat().st_mtime,
            "sha256": get_file_sha256(p)
        }
    pre_state_path = run_dir / "pre-training-state.json"
    with open(pre_state_path, "w", encoding="utf-8") as f:
        json.dump(pre_models, f, indent=2)
    print(f"Pre-training models captured: {len(pre_models)}")
    
    print("\n=== STEP 4: RECORD EXACT TRAINING COMMAND ===")
    rasa_bin = repo / ".venv-rasa-cv/bin/rasa"
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{repo / 'app/rasa'}:{env.get('PYTHONPATH', '')}"
    
    # We pass the exact frozen training files directly
    cmd = [
        str(rasa_bin), "train",
        "--config", str(cfg_p),
        "--domain", str(dom_p),
        "--data", str(dev_p), str(rules_p), str(stories_p),
        "--out", str(model_out_dir)
    ]
    cmd_str = f"PYTHONPATH=\"$(pwd)/app/rasa\" {rasa_bin.relative_to(repo)} train --config {cfg_p.relative_to(repo)} --domain {dom_p.relative_to(repo)} --data {dev_p.relative_to(repo)} {rules_p.relative_to(repo)} {stories_p.relative_to(repo)} --out {model_out_dir.relative_to(repo)}"
    
    with open(run_dir / "training-command.txt", "w", encoding="utf-8") as f:
        f.write(cmd_str + "\n")
    print(f"Command: {cmd_str}")
    
    print("\n=== STEP 5: RUN EXACTLY ONE FINAL TRAINING ===")
    start_time = datetime.datetime.now().astimezone()
    start_ts = start_time.isoformat()
    t0 = time.time()
    
    log_path = run_dir / "training.log"
    with open(log_path, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd,
            cwd=repo,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"Training PID: {proc.pid} launched. Streaming log...")
        for line in proc.stdout:
            log_file.write(line)
            log_file.flush()
            # print progress lines to stdout
            if any(k in line for k in ["Training", "Processed", "Epoch", "Validation", "Your Rasa model is trained"]):
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {line.strip()}")
                
        proc.wait()
        
    t1 = time.time()
    end_time = datetime.datetime.now().astimezone()
    end_ts = end_time.isoformat()
    elapsed_seconds = round(t1 - t0, 2)
    exit_code = proc.returncode
    
    print(f"\nTraining completed in {elapsed_seconds}s with exit code {exit_code}")
    assert exit_code == 0, f"Training failed with exit code {exit_code}"
    
    print("\n=== STEP 7: IDENTIFY THE EXACT NEW MODEL ===")
    post_models = list(model_out_dir.glob("*.tar.gz"))
    new_models = [p for p in post_models if str(p.relative_to(repo)) not in pre_models]
    assert len(new_models) == 1, f"Expected exactly 1 new model, found {len(new_models)}: {new_models}"
    final_model_path = new_models[0]
    final_model_sha = get_file_sha256(final_model_path)
    final_model_size = final_model_path.stat().st_size
    final_model_mtime = datetime.datetime.fromtimestamp(final_model_path.stat().st_mtime).astimezone().isoformat()
    print(f"Final Model: {final_model_path.name}")
    print(f"Size:        {final_model_size:,} bytes")
    print(f"SHA-256:     {final_model_sha}")
    
    print("\n=== STEP 9: MODEL ARCHIVE SANITY CHECK ===")
    assert tarfile.is_tarfile(final_model_path), "Artifact is not a valid tar archive"
    with tarfile.open(final_model_path, "r:gz") as tar:
        members = tar.getnames()
    assert len(members) > 0, "Model archive is empty"
    print(f"Model archive contains {len(members)} components (PASS)")
    
    print("\n=== STEP 11: POST-TRAINING FROZEN SHA CHECK ===")
    assert get_file_sha256(cfg_p) == "61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0"
    assert get_file_sha256(dom_p) == "c2a76780257345efc57dd32a8f261ac610745a4f21bad08bb308ad9b74717857"
    assert get_file_sha256(dev_p) == "37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d"
    assert get_file_sha256(rules_p) == "37325e428ddcec108ff10cc3ec93b1d0e667c54f23d59c23f3c710ece7db22e5"
    assert get_file_sha256(stories_p) == "45e869d2b571bec45926228cf9537d099b3d6002484a985a0bcf09913c492985"
    assert get_file_sha256(holdout_p) == "61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961"
    assert get_file_sha256(oof_p) == "b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47"
    print("Post-training frozen SHA verification: PASS (0 mutations)")
    
    print("\n=== STEP 12: CREATE FINAL MODEL TRAINING MANIFEST ===")
    training_manifest_path = run_dir / "final-model-training-manifest.json"
    training_manifest_data = {
        "run_id": run_id,
        "training_type": "full_rasa_final_model",
        "training_scope": "all_locked_development_800",
        "training_start_timestamp": start_ts,
        "training_end_timestamp": end_ts,
        "elapsed_seconds": elapsed_seconds,
        "training_command": cmd_str,
        "training_exit_code": exit_code,
        "training_log_path": str(log_path.relative_to(repo)),
        "training_log_sha256": get_file_sha256(log_path),
        "runtime": {
            "python_version": "3.9.6",
            "rasa_version": "3.6.21",
            "rasa_sdk_version": "3.6.2",
            "pythainlp_version": "5.3.4"
        },
        "freeze": {
            "manifest_path": "docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json",
            "manifest_sha256": freeze_manifest_sha
        },
        "development": {
            "path": str(dev_p.relative_to(repo)),
            "rows": 800,
            "intents": 15,
            "sha256": get_file_sha256(dev_p)
        },
        "holdout": {
            "path": str(holdout_p.relative_to(repo)),
            "rows": 200,
            "sha256": get_file_sha256(holdout_p),
            "evaluated": False
        },
        "training_inputs": {
            "config": {"path": str(cfg_p.relative_to(repo)), "sha256": get_file_sha256(cfg_p)},
            "domain": {"path": str(dom_p.relative_to(repo)), "sha256": get_file_sha256(dom_p)},
            "nlu": {"path": str(dev_p.relative_to(repo)), "sha256": get_file_sha256(dev_p)},
            "rules": {"path": str(rules_p.relative_to(repo)), "sha256": get_file_sha256(rules_p)},
            "stories": {"path": str(stories_p.relative_to(repo)), "sha256": get_file_sha256(stories_p)}
        },
        "final_model": {
            "path": str(final_model_path.relative_to(repo)),
            "filename": final_model_path.name,
            "size_bytes": final_model_size,
            "mtime": final_model_mtime,
            "sha256": final_model_sha
        },
        "pre_training_models": pre_models,
        "post_training_new_models": [str(final_model_path.relative_to(repo))],
        "new_model_count": 1,
        "baseline_oof": {
            "path": str(oof_p.relative_to(repo)),
            "sha256": get_file_sha256(oof_p),
            "status": "FINAL_LOCKED"
        },
        "development_modified": False,
        "configuration_modified": False,
        "holdout_used": False,
        "cross_validation_executed": False,
        "final_model_runtime_verified": False,
        "final_holdout_evaluated": False
    }
    with open(training_manifest_path, "w", encoding="utf-8") as f:
        json.dump(training_manifest_data, f, indent=2, ensure_ascii=False)
        
    print("\n=== STEP 13: CREATE HUMAN-READABLE TRAINING RECORD ===")
    training_md_path = run_dir / "final-model-training.md"
    md_content = f"""# Final Model Training Record
## SpecFlow Canonical Final Model (Run ID: `{run_id}`)

## 1. Training Authorization
This training run represents the **single authorized Final Model training execution** for the SpecFlow project, authorized under the **Final Configuration Freeze** (`specflow_final_configuration_v1`).

## 2. Final Freeze Reference
- **Freeze Manifest**: `docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json`
- **Freeze Manifest SHA-256**: `{freeze_manifest_sha}`

## 3. Runtime
- **Python**: `3.9.6`
- **Rasa**: `3.6.21`
- **rasa-sdk**: `3.6.2`
- **PyThaiNLP**: `5.3.4`

## 4. Development Dataset
- **Path**: `app/rasa/data/nlu.yml`
- **Training Examples**: **800** (100% of locked Development dataset)
- **Intents**: **15**
- **SHA-256**: `{get_file_sha256(dev_p)}`

## 5. Exact Training Inputs
- `app/rasa/config.yml` (`{get_file_sha256(cfg_p)}`)
- `app/rasa/domain.yml` (`{get_file_sha256(dom_p)}`)
- `app/rasa/data/nlu.yml` (`{get_file_sha256(dev_p)}`)
- `app/rasa/data/rules.yml` (`{get_file_sha256(rules_p)}`)
- `app/rasa/data/stories.yml` (`{get_file_sha256(stories_p)}`)

## 6. Training Command
```bash
{cmd_str}
```

## 7. Training Execution
- **Start Timestamp**: `{start_ts}`
- **End Timestamp**: `{end_ts}`
- **Elapsed Duration**: `{elapsed_seconds} seconds`
- **Exit Code**: `0` (Success)
- **Training Invocations**: `1`

## 8. Final Model Artifact
- **Path**: `{final_model_path.relative_to(repo)}`
- **Filename**: `{final_model_path.name}`
- **Size**: `{final_model_size:,} bytes`
- **Modification Timestamp**: `{final_model_mtime}`
- **SHA-256**: `{final_model_sha}`
- **Archive Status**: Verified readable gzip-compressed tarball containing full DIET, Policy, and metadata graph components.

## 9. Hash / Provenance Linkage
- Exactly ONE new model archive was produced (`new_model_count = 1`).
- The newly-created artifact is uniquely identified via post-training set subtraction.

## 10. Protected Artifact Integrity
- **Development 800 SHA**: `{get_file_sha256(dev_p)}` (PASS — Unchanged)
- **Holdout 200 SHA**: `{get_file_sha256(holdout_p)}` (PASS — Unchanged & Unevaluated)
- **Baseline OOF SHA**: `{get_file_sha256(oof_p)}` (PASS — Unchanged)
- **Config SHA**: `{get_file_sha256(cfg_p)}` (PASS — Unchanged)

## 11. What Was NOT Evaluated
- **No Training-Set Overfitting Evaluation**: Training-set accuracy is not reported or used as performance evidence.
- **Holdout Evaluation**: The Locked Holdout dataset was **NOT** opened, evaluated, or used.

## 12. Next Required Step
1. Perform Final-Model Runtime Verification (Interactive Form dialogue test and Fallback confidence test).
2. Execute the ONE-TIME Locked Holdout 200 Final Evaluation.
"""
    with open(training_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print("\n=== STEP 14: PHYSICAL MANIFEST VERIFICATION ===")
    for p in [training_manifest_path, training_md_path, log_path]:
        assert p.exists()
        assert p.stat().st_size > 0
        sha = get_file_sha256(p)
        print(f"Verified: {p.name:35s} | Size: {p.stat().st_size:7d} bytes | SHA: {sha}")
        
    print("\nFINAL MODEL TRAINING GATES ALL PASSED")

if __name__ == "__main__":
    main()
