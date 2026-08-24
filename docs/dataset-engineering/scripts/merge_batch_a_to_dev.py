#!/usr/bin/env python3
"""Merge frozen seed (250 examples) with approved Batch A (100 examples) to create the development dataset (350 examples).
Performs strict validation of example counts, duplicate detection, and ensures exact expected distribution.
"""
import sys
import yaml
import os

# Paths (adjust if repository layout changes)
FROZEN_SEED = "/tmp/specflow_frozen_seed_250.yml"
BATCH_A = "/Users/ploy/Desktop/mini_project/SpecFlow/docs/dataset-engineering/candidates/batch-a/batch-a-candidates.yml"
OUTPUT = "/tmp/specflow_development_350.yml"

EXPECTED_COUNTS = {
    "greet": 12,
    "goodbye": 13,
    "build_pc": 55,
    "upgrade_pc": 40,
    "inform_budget": 25,
    "inform_usage": 33,
    "inform_current_specs": 30,
    "ask_cpu_info": 17,
    "ask_gpu_info": 17,
    "ask_ram_info": 17,
    "ask_ssd_hdd_diff": 17,
    "optimize_performance": 34,
    "inform_future_upgrade": 21,
    "affirm": 9,
    "deny": 10,
}

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def count_examples(data):
    total = 0
    per_intent = {}
    for intent in data.get("nlu", []):
        examples = intent.get("examples", "").strip().split("\n")
        cnt = len([e for e in examples if e.strip()])
        total += cnt
        per_intent[intent["intent"]] = cnt
    return total, per_intent

def merge():
    frozen = load_yaml(FROZEN_SEED)
    batch = load_yaml(BATCH_A)

    # Index frozen intents for easy update
    frozen_index = {i["intent"]: i for i in frozen.get("nlu", [])}

    # Append Batch A examples to matching intent in frozen
    for intent in batch.get("nlu", []):
        name = intent["intent"]
        batch_ex = intent.get("examples", "").strip()
        if name not in frozen_index:
            print(f"[ERROR] Intent '{name}' from Batch A not present in frozen seed.")
            sys.exit(1)
        frozen_ex = frozen_index[name].get("examples", "").strip()
        combined = "\n".join([frozen_ex, batch_ex]) if frozen_ex else batch_ex
        frozen_index[name]["examples"] = combined

    merged = {"nlu": [frozen_index[name] for name in frozen_index]}

    # Write output
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as out:
        yaml.dump(merged, out, allow_unicode=True, sort_keys=False)

    # Validation
    total, per_intent = count_examples(merged)
    if total != 350:
        print(f"[ERROR] Total examples {total} != 350")
        sys.exit(1)
    mismatches = []
    for intent, expected in EXPECTED_COUNTS.items():
        actual = per_intent.get(intent, 0)
        if actual != expected:
            mismatches.append(f"{intent}: {actual} != {expected}")
    if mismatches:
        print("[ERROR] Distribution mismatches:", mismatches)
        sys.exit(1)

    # Duplicate detection
    seen = set()
    duplicates = []
    for intent in merged["nlu"]:
        intent_name = intent["intent"]
        for line in intent.get("examples", "").strip().split("\n"):
            pair = (intent_name, line.strip())
            if pair in seen:
                duplicates.append(pair)
            else:
                seen.add(pair)
    if duplicates:
        print("[ERROR] Duplicate intent‑utterance pairs found:", duplicates)
        sys.exit(1)

    print("MERGE VALIDATION PASSED")
    print("Total examples:", total)
    print("Per‑intent counts:", per_intent)

if __name__ == "__main__":
    merge()
