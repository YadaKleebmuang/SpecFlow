import os
import yaml
import re
import hashlib

NLU_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\data\nlu.yml"
CONFIG_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\config.yml"
TOKENIZER_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\thai_tokenizer.py"

def calculate_sha256(filepath):
    if not os.path.exists(filepath):
        return "File Not Found"
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def audit_dataset():
    if not os.path.exists(NLU_PATH):
        print("Dataset not found")
        return
        
    with open(NLU_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    nlu_items = data.get("nlu", [])
    intent_counts = {}
    all_examples = []
    
    entity_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    for item in nlu_items:
        intent = item.get("intent")
        examples_str = item.get("examples", "")
        examples = [line.strip().lstrip("- ").strip() for line in examples_str.split("\n") if line.strip()]
        
        intent_counts[intent] = len(examples)
        for ex in examples:
            all_examples.append((ex, intent))
            
    total_examples = len(all_examples)
    print(f"Total NLU examples parsed: {total_examples}")
    print(f"Total Intent classes: {len(intent_counts)}")
    print("Support per intent:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  - {intent}: {count}")
        
    min_support = min(intent_counts.values()) if intent_counts else 0
    print(f"Minimum class support: {min_support}")
    
    # Check if stratified 5-fold is possible (every class must have at least 5 examples)
    is_cv_possible = min_support >= 5
    print(f"Is Stratified 5-Fold Cross-Validation possible? {is_cv_possible}")
    
    # Check exact duplicates
    text_to_intents = {}
    for text, intent in all_examples:
        text_to_intents.setdefault(text, []).append(intent)
        
    exact_duplicates = {text: intents for text, intents in text_to_intents.items() if len(intents) > 1}
    print(f"\nExact duplicate count (same text): {len(exact_duplicates)}")
    conflicting_labels = 0
    for text, intents in exact_duplicates.items():
        if len(set(intents)) > 1:
            conflicting_labels += 1
            print(f"  - Conflicting label duplicate: '{text}' labeled as {intents}")
            
    print(f"Conflicting label duplicates count: {conflicting_labels}")
    
    # Normalized duplicates
    def normalize_text(t):
        t = t.strip()
        t = re.sub(r'\s+', ' ', t)
        return t
        
    norm_to_original = {}
    for text, intent in all_examples:
        norm = normalize_text(text)
        norm_to_original.setdefault(norm, []).append((text, intent))
        
    norm_duplicates = {norm: items for norm, items in norm_to_original.items() if len(items) > 1}
    print(f"Normalized duplicate groups count: {len(norm_duplicates)}")

if __name__ == "__main__":
    print(f"nlu.yml SHA-256: {calculate_sha256(NLU_PATH)}")
    print(f"config.yml SHA-256: {calculate_sha256(CONFIG_PATH)}")
    print(f"thai_tokenizer.py SHA-256: {calculate_sha256(TOKENIZER_PATH)}")
    print("-" * 50)
    audit_dataset()
