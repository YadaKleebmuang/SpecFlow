import os
import re
import sys

# เพิ่ม Project Root ใน sys.path เพื่ออ้างอิงและนำเข้าไลบรารี preprocessing ของเรา
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.services.nlp.preprocessing import preprocess_thai_text

def preprocess_nlu_line(line_content: str) -> str:
    """
    ตัดคำและเตรียมประโยคภาษาไทยในประโยคตัวอย่างของ Rasa NLU 
    โดยยังคงรักษาและแปลงค่าใน Entity Markup [value](entity) ไว้อย่างถูกต้อง
    """
    # แพทเทิร์นจับกลุ่ม Entity ของ Rasa เช่น [30000](budget)
    entity_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    entities = []
    
    def replace_to_placeholder(match):
        val = match.group(1)
        ent = match.group(2)
        # ทำความสะอาดและตัดคำของค่าที่อยู่ข้างในวงเล็บด้วย
        # เพื่อให้สอดคล้องกับธรรมชาติของคำที่ Rasa จะได้รับที่รันไทม์
        preprocessed_val = preprocess_thai_text(val)
        
        # ใช้ตัวพิมพ์เล็กเสมอเพื่อรองรับกรณี preprocessor ทำการแปลงเป็นตัวพิมพ์เล็ก (lowercase)
        placeholder = f"__entity_{len(entities)}__"
        entities.append(f"[{preprocessed_val}]({ent})")
        return placeholder

    # 1. แทนที่รูปแบบ Entity ทั้งหมดด้วยตัวแปลชั่วคราว (Placeholders)
    placeholder_text = re.sub(entity_pattern, replace_to_placeholder, line_content)
    
    # 2. นำข้อความที่เหลือมาทำ Preprocessing ตัดคำภาษาไทยและลบคำหางเสียง
    preprocessed_placeholder_text = preprocess_thai_text(placeholder_text)
    
    # 3. นำ Entity ดั้งเดิมที่ตัดคำเสร็จแล้วมาแทนที่กลับคืนลงในช่องเดิม โดยอิงตาม placeholder ตัวพิมพ์เล็ก
    result_text = preprocessed_placeholder_text
    for i, ent_markup in enumerate(entities):
        placeholder = f"__entity_{i}__"
        result_text = result_text.replace(placeholder, ent_markup)
        
    return result_text

def run_preprocessing():
    # กำหนดพาธไฟล์ NLU ต้นฉบับ
    nlu_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../rasa/data/nlu.yml'))
    
    if not os.path.exists(nlu_path):
        print(f"❌ ไม่พบไฟล์ NLU ที่พาธ: {nlu_path}")
        return
        
    print(f"📂 กำลังอ่านไฟล์และเริ่มระบบการตัดคำที่: {nlu_path}")
    
    processed_lines = []
    total_examples = 0
    
    with open(nlu_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        # ตรวจสอบบรรทัดที่เป็นข้อความตัวอย่างฝึกสอนบอท ซึ่งขึ้นต้นด้วย "    - "
        if line.startswith("    - "):
            total_examples += 1
            raw_example = line[6:].strip() # ดึงข้อความดิบหลังสัญลักษณ์ "- "
            
            # รันการตัดคำและเตรียมข้อความ
            processed_example = preprocess_nlu_line(raw_example)
            
            # ประกอบคำคืนรูปเดิมในแบบตัดคำแล้ว
            processed_lines.append(f"    - {processed_example}\n")
        else:
            # บรรทัดปกติหรือคอมเมนต์ ให้คงรูปเดิมไว้ 100%
            processed_lines.append(line)
            
    # บันทึกทับไฟล์เดิม เพื่อความสะดวกของบอทในการสั่ง rasa train ทันที
    with open(nlu_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
        
    print(f"✅ ประมวลผลและแปลงสเปคประโยคใน NLU สำเร็จเสร็จสิ้น!")
    print(f"   จำนวนประโยคตัวอย่างที่ประมวลผล: {total_examples} ประโยค")

if __name__ == "__main__":
    run_preprocessing()
