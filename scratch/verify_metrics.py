import os
import yaml
import re

# Paths
NLU_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\data\nlu.yml"
INTENT_REPORT_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\results\intent_report.json"
DIET_REPORT_PATH = r"c:\Users\yadak\Desktop\SpecFlow\app\rasa\results\DIETClassifier_report.json"

def count_nlu_data():
    if not os.path.exists(NLU_PATH):
        print("nlu.yml not found")
        return
        
    with open(NLU_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    nlu_items = data.get("nlu", [])
    total_examples = 0
    intent_counts = {}
    total_entities = 0
    entity_counts = {}
    
    entity_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    for item in nlu_items:
        intent = item.get("intent")
        examples_str = item.get("examples", "")
        examples = [line.strip().lstrip("- ").strip() for line in examples_str.split("\n") if line.strip()]
        
        intent_counts[intent] = len(examples)
        total_examples += len(examples)
        
        for ex in examples:
            matches = re.findall(entity_pattern, ex)
            total_entities += len(matches)
            for val, ent in matches:
                entity_counts[ent] = entity_counts.get(ent, 0) + 1
                
    print(f"Total Intents: {len(intent_counts)}")
    print(f"Total Examples (sentences): {total_examples}")
    print("Examples per intent:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  - {intent}: {count}")
        
    print(f"\nTotal Entities: {total_entities}")
    print("Entities per type:")
    for ent, count in sorted(entity_counts.items()):
        print(f"  - {ent}: {count}")

if __name__ == "__main__":
    count_nlu_data()
