import json
import os
import re
from pythainlp import word_tokenize

# ชุดคำฟุ่มเฟือยภาษาไทยที่พบได้บ่อยในแชทและไม่มีความสำคัญต่อการจัดสเปค/ระบุความต้องการ
CUSTOM_STOPWORDS = {
    'ครับ', 'ค่ะ', 'นะ', 'หน่อย', 'ด้วย', 'ช่วย', 'อยาก', 'อยากได้', 'ขอ', 
    'ให้', 'เครื่อง', 'ผม', 'หนู', 'เรา', 'คุณ', 'ครับผม', 'นะคะ', 'จ้า', 
    'นะจ๊ะ', 'นะจะ', 'เว้ย', 'ละ', 'เด้อ', 'บาท', 'งบ', 'งบประมาณ', 'มี',
    'ได้ไหม', 'ได้ไหมครับ', 'ได้ไหมค่ะ', 'เอางบ', 'เงิน', 'มีเงิน'
}

class ThaiPreprocessor:
    def __init__(self):
        # โหลดไฟล์ typo_dict.json เพื่อนำมาแก้สะกดผิดอัตโนมัติ
        dict_path = os.path.join(os.path.dirname(__file__), 'typo_dict.json')
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                self.typo_dict = json.load(f)
        except Exception as e:
            print(f"Error loading typo dict in preprocessor: {e}")
            self.typo_dict = {}

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # ลดช่องว่างที่ซ้ำกัน
        text = re.sub(r'\s+', ' ', text)
        # แปลงภาษาอังกฤษให้เป็นตัวพิมพ์เล็กทั้งหมด
        text = text.lower().strip()
        return text

    def remove_stopwords(self, tokens: list) -> list:
        # ตัดคำสร้อยและคำที่ไม่มีนัยยะในการประเมินประสิทธิภาพ
        return [t for t in tokens if t not in CUSTOM_STOPWORDS]

    def preprocess(self, text: str) -> str:
        cleaned = self.clean_text(text)
        if not cleaned:
            return ""
            
        # 1. ดำเนินการทดแทนคำสะกดผิดที่ระดับข้อความดิบ ก่อนการตัดคำ (String-level replacement)
        # วิธีนี้ช่วยป้องกันไม่ให้คำยาว เช่น "กาดจอ" ถูก PyThaiNLP แยกออกเป็น "กาด" และ "จอ" ตั้งแต่แรก
        for typo, replacement in self.typo_dict.items():
            if typo in cleaned:
                cleaned = cleaned.replace(typo, replacement)
            
        # 2. ทำการตัดคำภาษาไทยด้วยโมเดล newmm ของ PyThaiNLP
        tokens = word_tokenize(cleaned, keep_whitespace=False)
        
        # 3. ลบคำฟุ่มเฟือยและคำหางเสียงในแชท
        tokens = self.remove_stopwords(tokens)
        
        # 4. เชื่อมคำที่ตัดแล้วกลับมาด้วยเว้นวรรค " " เพื่อให้ WhitespaceTokenizer ของ Rasa ทำงานต่อได้
        return " ".join(tokens)

# อินสแตนซ์หลักของ Preprocessor
_preprocessor = ThaiPreprocessor()

def preprocess_thai_text(text: str) -> str:
    """
    ฟังก์ชันสำหรับใช้งานจากโมดูลอื่น เพื่อเตรียมข้อความภาษาไทยให้พร้อมส่งให้ Rasa NLU
    """
    return _preprocessor.preprocess(text)
