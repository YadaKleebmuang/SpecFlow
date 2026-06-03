import os
import json
import sys

# ค้นหาพาธไฟล์รายงานผลลัพธ์จาก Rasa NLU Evaluation
RESULT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/rasa/results'))
INTENT_REPORT_PATH = os.path.join(RESULT_DIR, 'intent_report.json')
ENTITY_REPORT_PATH = os.path.join(RESULT_DIR, 'DIETClassifier_report.json')

def print_nlu_report():
    print("=" * 75)
    print("🔬 ผลประเมินความเข้าใจภาษาธรรมชาติ (Rasa NLU Scientific Metrics Summary)")
    print("=" * 75)

    # 1. รายงานผลการจำแนกเจตนา (Intent Classification)
    if os.path.exists(INTENT_REPORT_PATH):
        with open(INTENT_REPORT_PATH, 'r', encoding='utf-8') as f:
            intent_data = json.load(f)
        
        accuracy = intent_data.get("accuracy", 0.0)
        macro_avg = intent_data.get("macro avg", {})

        print("\n🎯 สถิติการจำแนกเจตนา (Intent Classification Metrics):")
        print(f"➖ ค่าความถูกต้อง (Accuracy):         {accuracy * 100:.2f}%")
        print(f"➖ Precision (Macro Average):       {macro_avg.get('precision', 0.0) * 100:.2f}%")
        print(f"➖ Recall (Macro Average):          {macro_avg.get('recall', 0.0) * 100:.2f}%")
        print(f"➖ F1-Score (Macro Average):        {macro_avg.get('f1-score', 0.0) * 100:.2f}%")
        print(f"➖ Support (จำนวนตัวอย่างทั้งหมด):     {macro_avg.get('support', 0)}")
        print("-" * 75)
        
        # แสดงรายละเอียดรายเจตนาหลัก (Intent-level Breakdown)
        print(f"{'ชื่อเจตนา (Intent Name)':<35}{'Precision':<15}{'Recall':<15}{'F1-Score':<10}")
        print("-" * 75)
        for key, val in sorted(intent_data.items()):
            if key not in ["accuracy", "macro avg", "weighted avg"] and isinstance(val, dict):
                print(f"{key:<35}{val.get('precision', 0.0)*100:<15.2f}{val.get('recall', 0.0)*100:<15.2f}{val.get('f1-score', 0.0)*100:<10.2f}")
    else:
        print("❌ ไม่พบไฟล์ผลทดสอบ Intent (intent_report.json) กรุณารัน 'rasa test nlu' ก่อน")

    # 2. รายงานผลการดึงเอนทิตี (Entity Extraction)
    print("\n" + "=" * 75)
    if os.path.exists(ENTITY_REPORT_PATH):
        with open(ENTITY_REPORT_PATH, 'r', encoding='utf-8') as f:
            entity_data = json.load(f)
            
        macro_avg = entity_data.get("macro avg", {})

        print("\n🧩 สถิติการดึงเอนทิตี (Entity Extraction Metrics - DIETClassifier):")
        print(f"➖ Precision (Macro Average):       {macro_avg.get('precision', 0.0) * 100:.2f}%")
        print(f"➖ Recall (Macro Average):          {macro_avg.get('recall', 0.0) * 100:.2f}%")
        print(f"➖ F1-Score (Macro Average):        {macro_avg.get('f1-score', 0.0) * 100:.2f}%")
        print(f"➖ Support (จำนวนตัวอย่างทั้งหมด):     {macro_avg.get('support', 0)}")
        print("-" * 75)
        
        # แสดงรายละเอียดรายเอนทิตีหลัก (Entity-level Breakdown)
        print(f"{'ชื่อเอนทิตี (Entity Name)':<35}{'Precision':<15}{'Recall':<15}{'F1-Score':<10}")
        print("-" * 75)
        for key, val in sorted(entity_data.items()):
            if key not in ["macro avg", "weighted avg", "micro avg"] and isinstance(val, dict):
                print(f"{key:<35}{val.get('precision', 0.0)*100:<15.2f}{val.get('recall', 0.0)*100:<15.2f}{val.get('f1-score', 0.0)*100:<10.2f}")
    else:
        print("❌ ไม่พบไฟล์ผลทดสอบ Entity (DIETClassifier_report.json) กรุณารัน 'rasa test nlu' ก่อน")
        
    print("=" * 75)

    # 3. ตัวอย่างประโยคภาษาไทยมาตรฐานสำหรับการทดสอบความถูกต้อง
    print("\n📝 ตัวอย่างประโยคทดสอบภาษาไทยมาตรฐานสำหรับการใช้งานวิจัย (NLU Test Set Samples):")
    test_sentences = [
        "จัดสเปคคอมงบ 30000 เล่นเกม",
        "แนะนำสเปคคอม 20000 กราฟิก",
        "คอมช้ามาก อัปเกรดอะไรดี",
        "การ์ดจอกาดจอแรงๆ",
        "มีเงิน 15000 อยากได้คอมพิมพ์งาน",
        "cpu หน้าที่อะไร",
        "อยากได้แบบเผื่ออัปเกรดในอนาคตด้วย"
    ]
    for idx, sent in enumerate(test_sentences, 1):
        print(f"  {idx}. {sent}")
    print("=" * 75)

if __name__ == "__main__":
    print_nlu_report()
