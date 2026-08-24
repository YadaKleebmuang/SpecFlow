#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def remove_path(p: Path):
    if not p.exists():
        return
    if p.is_dir():
        shutil.rmtree(p)
        print(f"Removed directory: {p}")
    else:
        p.unlink()
        print(f"Removed file:      {p}")

def main():
    repo = Path(os.getcwd())
    
    # 1. Remove .DS_Store files
    for ds in repo.rglob(".DS_Store"):
        if ".venv-rasa-cv" not in str(ds):
            ds.unlink()
            print(f"Removed .DS_Store: {ds}")
            
    # 2. Approved temporary directories
    temp_dirs = [
        repo / ".rasa",
        repo / "tmp_holdout_eval_20260825-013559",
        repo / "tmp_holdout_eval_20260825-013611",
        repo / "tmp_holdout_eval_20260825-013629",
        repo / "tmp_holdout_eval_20260825-013835",
        repo / "tmp",
        repo / "tmp_salvage",
        repo / "cv_canary",
        repo / "docs/final-readiness/final-holdout-evaluation/run-20260825-013559",
        repo / "docs/final-readiness/final-holdout-evaluation/run-20260825-013611",
        repo / "docs/final-readiness/final-holdout-evaluation/run-20260825-013629",
        repo / "docs/final-readiness/final-holdout-evaluation/run-20260825-013835",
        repo / "docs/final-readiness/system-e2e-evidence/run-20260825-014327",
        repo / "docs/final-readiness/system-e2e-evidence/run-20260825-014416",
        repo / "docs/final-readiness/system-e2e-evidence/run-20260825-014455",
        repo / "docs/final-readiness/system-e2e-evidence/run-20260825-014535",
    ]
    for td in temp_dirs:
        remove_path(td)
        
    # 3. Approved temporary files
    temp_files = [
        repo / "recover_and_build.py",
        repo / "run_cv.py",
        repo / "app/rasa/data/nlu_350_recovered.yml",
        repo / "app/rasa/data/nlu_600.yml",
        repo / "app/rasa/data/nlu_800.yml",
        repo / "app/rasa/data/nlu_pre_clean_rebuild.yml",
    ]
    for tf in temp_files:
        remove_path(tf)
        
    print("\nSAFE CLEANUP EXECUTION COMPLETE")

if __name__ == "__main__":
    main()
