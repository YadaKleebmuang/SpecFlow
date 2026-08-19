import os
import re
import sys
import yaml
import difflib
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.nlp.preprocessing import preprocess_thai_text

NLU_PATH = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'data', 'nlu.yml')
DOMAIN_PATH = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'domain.yml')
RULES_PATH = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'data', 'rules.yml')
STORIES_PATH = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'data', 'stories.yml')

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def parse_nlu(path):
    intents_data = {}
    current_intent = None
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line_str = line.strip()
        if line_str.startswith('- intent:'):
            current_intent = line_str.replace('- intent:', '').strip()
            intents_data[current_intent] = []
        elif line_str.startswith('- ') and current_intent:
            example = line_str[2:].strip()
            if example:
                intents_data[current_intent].append(example)
                
    return intents_data

def strip_entity_annotations(text):
    pattern = r'\[([^\]]+)\]\([^)]+\)'
    return re.sub(pattern, r'\1', text)

def extract_entities(text):
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)
    return matches

def main():
    print("=" * 80)
    print("[SpecFlow NLU Dataset Audit]")
    print("=" * 80)

    domain = load_yaml(DOMAIN_PATH)
    rules = load_yaml(RULES_PATH)
    stories = load_yaml(STORIES_PATH)
    nlu_intents = parse_nlu(NLU_PATH)

    domain_intents = set(domain.get('intents', []))
    domain_entities = set(domain.get('entities', []))

    print("\n1. Domain & NLU Intents check:")
    all_nlu_intents = set(nlu_intents.keys())
    missing_in_domain = all_nlu_intents - domain_intents
    print(f"   - Total Intents in NLU: {len(all_nlu_intents)}")
    print(f"   - Missing in domain.yml: {missing_in_domain if missing_in_domain else 'None (OK)'}")

    # Check rule/story coverage
    rule_intents = set()
    for rule in rules.get('rules', []):
        for step in rule.get('steps', []):
            if 'intent' in step:
                rule_intents.add(step['intent'])
    
    print(f"   - Rule/Story Coverage: {len(rule_intents)} / {len(all_nlu_intents)}")

    print("\n2. Per-intent breakdown:")
    print(f"{'Intent':<25}{'Count':<8}{'Exact Dup':<12}{'Preproc Dup':<14}{'Near Dup':<12}{'Entity Err':<12}")
    print("-" * 80)

    total_examples = 0
    all_cleaned_examples = {}
    all_preproc_examples = {}
    all_raw_list = []

    entity_errors = defaultdict(int)
    exact_dups = defaultdict(int)
    preproc_dups = defaultdict(int)
    near_dups = defaultdict(int)

    for intent, examples in nlu_intents.items():
        total_examples += len(examples)
        seen_exact = set()
        seen_preproc = set()

        for ex in examples:
            plain_text = strip_entity_annotations(ex)
            cleaned_text = re.sub(r'\s+', '', plain_text.lower())
            preproc_text = preprocess_thai_text(plain_text)

            entities = extract_entities(ex)
            for val, ent in entities:
                if ent not in domain_entities:
                    entity_errors[intent] += 1
                    print(f"   [ERR] Invalid Entity '{ent}' in intent '{intent}': {ex}")

            if ex in seen_exact:
                exact_dups[intent] += 1
            else:
                seen_exact.add(ex)

            if preproc_text in seen_preproc:
                preproc_dups[intent] += 1
            else:
                seen_preproc.add(preproc_text)

            all_raw_list.append((intent, ex, plain_text, preproc_text))

        n = len(examples)
        for i in range(n):
            for j in range(i + 1, n):
                p1 = strip_entity_annotations(examples[i])
                p2 = strip_entity_annotations(examples[j])
                ratio = difflib.SequenceMatcher(None, p1, p2).ratio()
                if 0.90 <= ratio < 1.0:
                    near_dups[intent] += 1

        print(f"{intent:<25}{len(examples):<8}{exact_dups[intent]:<12}{preproc_dups[intent]:<14}{near_dups[intent]:<12}{entity_errors[intent]:<12}")

    print("-" * 80)
    print(f"Total NLU Examples: {total_examples}")

    print("\n3. Cross-intent Duplicates:")
    cross_exact = defaultdict(list)
    cross_preproc = defaultdict(list)

    for intent, raw_text, plain_text, preproc_text in all_raw_list:
        if plain_text in all_cleaned_examples and all_cleaned_examples[plain_text][0] != intent:
            cross_exact[plain_text].append((intent, raw_text))
            cross_exact[plain_text].append(all_cleaned_examples[plain_text])
        else:
            all_cleaned_examples[plain_text] = (intent, raw_text)

        if preproc_text in all_preproc_examples and all_preproc_examples[preproc_text][0] != intent:
            cross_preproc[preproc_text].append((intent, raw_text))
            cross_preproc[preproc_text].append(all_preproc_examples[preproc_text])
        else:
            all_preproc_examples[preproc_text] = (intent, raw_text)

    if cross_exact:
        print(f"   [WARN] Exact Cross-Intent Duplicates found: {len(cross_exact)}")
        for k, v in cross_exact.items():
            print(f"      - '{k}': {v}")
    else:
        print("   [OK] No Exact Cross-Intent Duplicates")

    if cross_preproc:
        print(f"   [WARN] Preprocessed Cross-Intent Duplicates found: {len(cross_preproc)}")
        for k, v in list(cross_preproc.items())[:5]:
            print(f"      - Preprocessed: '{k}' -> {v}")
    else:
        print("   [OK] No Preprocessed Cross-Intent Duplicates")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
