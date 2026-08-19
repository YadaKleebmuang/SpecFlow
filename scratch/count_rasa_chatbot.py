import yaml
import os
import hashlib

NLU_PATH = r"c:\Users\yadak\Desktop\rasa-chatbot\data\nlu.yml"

def inspect_nlu():
    if not os.path.exists(NLU_PATH):
        print("rasa-chatbot nlu.yml not found")
        return
        
    with open(NLU_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    nlu_items = data.get("nlu", [])
    total_examples = 0
    
    for item in nlu_items:
        examples_str = item.get("examples", "")
        examples = [line.strip().lstrip("- ").strip() for line in examples_str.split("\n") if line.strip()]
        total_examples += len(examples)
        
    print(f"Total Examples (sentences): {total_examples}")
    
    # Calculate SHA-256
    sha256_hash = hashlib.sha256()
    with open(NLU_PATH, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    print(f"SHA-256: {sha256_hash.hexdigest()}")

if __name__ == "__main__":
    inspect_nlu()
