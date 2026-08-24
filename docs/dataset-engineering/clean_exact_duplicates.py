#!/usr/bin/env python3
"""Deterministic exact‑duplicate cleaning script for SpecFlow.
   Reads the raw NLU file, verifies pre‑conditions, removes only exact duplicate
   utterance lines per intent, validates post‑conditions, and writes the cleaned
   dataset to a temporary location outside the Rasa training directory.
"""
import sys, os, hashlib, collections
import yaml

RAW_PATH = 'app/rasa/data/nlu.yml'
TMP_PATH = '/tmp/specflow_nlu_clean_validation.yml'
EXPECTED_SHA = '200d6198f468b6ed2828953f81d8d55910f0536af76d8df13ab2395521183a3a'
EXPECTED_TOTAL = 264
EXPECTED_UNIQUE = 250
EXPECTED_INTENTS = 15
EXPECTED_DUP_GROUPS = 12
EXPECTED_EXTRA = 14
EXPECTED_CROSS = 0

def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def audit(data):
    intents = data.get('nlu', [])
    all_pairs = []
    per_intent = {}
    for entry in intents:
        intent = entry.get('intent')
        ex = entry.get('examples', '')
        utts = [ln.strip()[2:] for ln in ex.splitlines() if ln.strip().startswith('- ')]
        per_intent.setdefault(intent, []).extend(utts)
        for utt in utts:
            all_pairs.append((intent, utt))
    total = len(all_pairs)
    unique = len(set(all_pairs))
    extra = total - unique
    # duplicate groups per intent
    dup_groups = 0
    extra_dup = 0
    for utts in per_intent.values():
        c = collections.Counter(utts)
        dup_groups += sum(1 for v in c.values() if v > 1)
        extra_dup += sum(v-1 for v in c.values() if v > 1)
    # cross‑intent exact duplicates
    utt_to_intents = collections.defaultdict(set)
    for intent, utt in all_pairs:
        utt_to_intents[utt].add(intent)
    cross = sum(1 for s in utt_to_intents.values() if len(s) > 1)
    return {
        'total': total,
        'unique': unique,
        'extra': extra,
        'intent_count': len(per_intent),
        'dup_groups': dup_groups,
        'extra_dup': extra_dup,
        'cross': cross,
        'per_intent': {k: (len(v), len(set(v)), sum(c-1 for c in collections.Counter(v).values() if c>1))
                       for k, v in per_intent.items()}
    }

def dedup_preserve_text(raw_text):
    lines = raw_text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith('- intent:'):
            # copy intent header
            out.append(line)
            i += 1
            # copy following lines until we hit next intent or end
            seen = set()
            while i < len(lines) and not lines[i].lstrip().startswith('- intent:'):
                cur = lines[i]
                stripped = cur.strip()
                if stripped.startswith('- '):
                    utt = stripped[2:]
                    if utt not in seen:
                        seen.add(utt)
                        out.append('    - ' + utt)
                    # else skip duplicate
                else:
                    out.append(cur)
                i += 1
        else:
            out.append(line)
            i += 1
    return '\n'.join(out) + '\n'

# ---- Pre‑condition verification ----
if sha256(RAW_PATH) != EXPECTED_SHA:
    sys.exit('RAW SHA‑256 mismatch')
raw_yaml = load_yaml(RAW_PATH)
pre = audit(raw_yaml)
assert pre['total'] == EXPECTED_TOTAL, f"total {pre['total']} != {EXPECTED_TOTAL}"
assert pre['unique'] == EXPECTED_UNIQUE, f"unique {pre['unique']} != {EXPECTED_UNIQUE}"
assert pre['intent_count'] == EXPECTED_INTENTS, f"intent count {pre['intent_count']} != {EXPECTED_INTENTS}"
assert pre['dup_groups'] == EXPECTED_DUP_GROUPS, f"dup groups {pre['dup_groups']} != {EXPECTED_DUP_GROUPS}"
assert pre['extra'] == EXPECTED_EXTRA, f"extra {pre['extra']} != {EXPECTED_EXTRA}"
assert pre['cross'] == EXPECTED_CROSS, f"cross {pre['cross']} != {EXPECTED_CROSS}"

# ---- Deduplication ----
with open(RAW_PATH, 'r', encoding='utf-8') as f:
    raw_text = f.read()
clean_text = dedup_preserve_text(raw_text)
# Load cleaned yaml to re‑audit
clean_yaml = yaml.safe_load(clean_text)
post = audit(clean_yaml)
assert post['total'] == EXPECTED_TOTAL - EXPECTED_EXTRA, 'post total mismatch'
assert post['dup_groups'] == 0, 'post duplicate groups not zero'
assert post['extra'] == 0, 'post extra not zero'
assert post['cross'] == 0, 'post cross not zero'
# ---- Write temp file ----
with open(TMP_PATH, 'w', encoding='utf-8') as f:
    f.write(clean_text)
print('Cleaned dataset written to', TMP_PATH)
print('Post‑audit stats:', post)
