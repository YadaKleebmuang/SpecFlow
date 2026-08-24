#!/usr/bin/env python3
"""verify_locked_holdout_v1.py – Verify Locked Holdout Dataset v1
Usage: python verify_locked_holdout_v1.py --verify-only
The script performs:
1. Development SHA check (must match expected hash)
2. Holdout YAML structure validation
3. Example count = 200, unique = 200
4. Intent distribution matches required counts
5. No exact duplicates within holdout
6. No cross‑intent duplicate utterances
7. No overlap with Development800 examples (exact normalized match)
8. Entity schema validation (allowed entities only)
Exit code 0 on PASS, non‑zero on failure.
"""
import argparse, hashlib, os, sys, yaml
from collections import Counter

DEV_PATH = os.path.join('app', 'rasa', 'data', 'nlu.yml')
HOLDOUT_PATH = os.path.join('docs', 'dataset-engineering', 'holdout', 'locked-holdout-v1.yml')
EXPECTED_DEV_SHA = '37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d'
ALLOWED_ENTITIES = {'budget', 'usage', 'component_type', 'future_upgrade'}
REQUIRED_DISTRIBUTION = {
    'greet':5,'goodbye':5,'build_pc':36,'upgrade_pc':29,'inform_budget':15,'inform_usage':18,
    'inform_current_specs':17,'ask_cpu_info':6,'ask_gpu_info':6,'ask_ram_info':6,'ask_ssd_hdd_diff':6,
    'optimize_performance':25,'inform_future_upgrade':14,'affirm':6,'deny':6}

def compute_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def load_nlu(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('nlu', [])

def normalize(text):
    return text.strip()

def extract_entities(text):
    import re
    return set(m.group(1) for m in re.finditer(r"\[.*?\]\(([^)]+)\)", text))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    # 1. Development SHA
    dev_sha = compute_sha(DEV_PATH)
    if dev_sha != EXPECTED_DEV_SHA:
        print('FAIL: Development SHA mismatch')
        sys.exit(1)
    # 2. Load holdout
    holdout = load_nlu(HOLDOUT_PATH)
    if len(holdout) != 200:
        print('FAIL: Holdout example count', len(holdout))
        sys.exit(2)
    # 3. Uniqueness inside holdout
    texts = [normalize(item['text']) for item in holdout]
    if len(set(texts)) != 200:
        print('FAIL: Duplicate utterances within holdout')
        sys.exit(3)
    # 4. Distribution check
    dist = Counter(item['intent'] for item in holdout)
    if dist != Counter(REQUIRED_DISTRIBUTION):
        print('FAIL: Distribution mismatch')
        print('Expected', REQUIRED_DISTRIBUTION)
        print('Found', dict(dist))
        sys.exit(4)
    # 5. Cross‑intent duplicates
    intent_map = {}
    for item in holdout:
        key = normalize(item['text'])
        intent = item['intent']
        if key in intent_map and intent_map[key] != intent:
            print('FAIL: Cross‑intent duplicate', key)
            sys.exit(5)
        intent_map[key] = intent
    # 6. Overlap with Development
    dev_examples = load_nlu(DEV_PATH)
    dev_texts = set(normalize(e['text']) for e in dev_examples)
    overlap = dev_texts.intersection(set(texts))
    if overlap:
        print('FAIL: Overlap with Development', len(overlap))
        sys.exit(6)
    # 7. Entity schema validation
    for item in holdout:
        ents = extract_entities(item['text'])
        if not ents.issubset(ALLOWED_ENTITIES):
            print('FAIL: Disallowed entity in', item['text'])
            sys.exit(7)
    print('VERIFICATION PASS')
    sys.exit(0)

if __name__ == '__main__':
    main()
