import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# เพิ่ม Project Root ใน sys.path เพื่ออ้างอิงและนำเข้าไลบรารี preprocessing ของเรา
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.services.nlp.preprocessing import preprocess_thai_text

def preprocess_nlu_line(line_content: str) -> str:
    entity_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    entities = []
    
    def replace_to_placeholder(match):
        val = match.group(1)
        ent = match.group(2)
        preprocessed_val = preprocess_thai_text(val)
        placeholder = f"__entity_{len(entities)}__"
        entities.append(f"[{preprocessed_val}]({ent})")
        return placeholder

    placeholder_text = re.sub(entity_pattern, replace_to_placeholder, line_content)
    preprocessed_placeholder_text = preprocess_thai_text(placeholder_text)
    
    result_text = preprocessed_placeholder_text
    for i, ent_markup in enumerate(entities):
        placeholder = f"__entity_{i}__"
        result_text = result_text.replace(placeholder, ent_markup)
        
    return result_text

def run_preprocessing():
    nlu_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../rasa/data/nlu.yml'))
    
    if not os.path.exists(nlu_path):
        print(f"[ERR] File not found: {nlu_path}")
        return
        
    print(f"Reading NLU file: {nlu_path}")
    
    processed_lines = []
    total_examples = 0
    
    with open(nlu_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        if line.startswith("    - "):
            total_examples += 1
            raw_example = line[6:].strip()
            processed_example = preprocess_nlu_line(raw_example)
            processed_lines.append(f"    - {processed_example}\n")
        else:
            processed_lines.append(line)
            
    with open(nlu_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
        
    print(f"[OK] Successfully preprocessed NLU dataset. Processed {total_examples} examples.")

if __name__ == "__main__":
    run_preprocessing()
