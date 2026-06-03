import sys
import os
import unittest

# เพิ่มโฟลเดอร์หลักของโปรเจกต์ (Project Root) เข้ามาใน sys.path เพื่อให้สามารถเรียกโมดูลภายในแอปได้
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.nlp.preprocessing import preprocess_thai_text

class TestThaiNLPPreprocessing(unittest.TestCase):
    
    def test_thai_segmentation_with_stopwords(self):
        # 1. ทดสอบการตัดคำภาษาไทยและการคัดคำสร้อย/คำฟุ่มเฟือยทิ้ง
        text = "อยากจัดสเปคคอมงบ30000เล่นเกมครับ"
        # คำว่า "อยาก", "งบ", "ครับ" เป็นคำสร้อยที่จะต้องถูกกรองออก
        result = preprocess_thai_text(text)
        print(f"\n[Test 1] Original: '{text}' \n         Result:   '{result}'")
        
        # ตรวจสอบคำหลักที่แยกกันด้วยเว้นวรรค
        self.assertIn("จัด", result)
        self.assertIn("สเปค", result)
        self.assertIn("คอม", result)
        self.assertIn("30000", result)
        self.assertIn("เล่น", result)
        self.assertIn("เกม", result)
        
        # ตรวจสอบว่าคำฟุ่มเฟือยต้องถูกคัดออก
        self.assertNotIn("ครับ", result)
        self.assertNotIn("อยาก", result)

    def test_typo_normalization(self):
        # 2. ทดสอบการแปลงคำเขียนสะกดผิด/คำสแลงคอมพิวเตอร์ให้เข้าสู่คำกลางของไอที
        text = "แนะนำกาดจอแรงๆและสเป็กคอมหน่อยค่ะ"
        # "กาดจอ" -> "การ์ดจอ" -> (ตัดคำเป็น "การ์ด" และ "จอ"), "สเป็ก" -> "สเปค"
        result = preprocess_thai_text(text)
        print(f"[Test 2] Original: '{text}' \n         Result:   '{result}'")
        
        self.assertIn("การ์ด", result)
        self.assertIn("จอ", result)
        self.assertIn("สเปค", result)
        self.assertIn("คอม", result)
        
        self.assertNotIn("กาด", result)
        self.assertNotIn("สเป็ก", result)
        self.assertNotIn("หน่อย", result)
        self.assertNotIn("ค่ะ", result)

    def test_office_usage_segmentation(self):
        # 3. ทดสอบประโยคสำหรับทำงานสำนักงาน
        text = "มีงบ15000บาทเน้นพิมพ์งานทำเอกสารออฟฟิศทั่วไปค่ะ"
        result = preprocess_thai_text(text)
        print(f"[Test 3] Original: '{text}' \n         Result:   '{result}'")
        
        self.assertIn("15000", result)
        self.assertIn("พิมพ์", result)
        self.assertIn("งาน", result)
        self.assertIn("เอกสาร", result)
        self.assertIn("ออฟฟิศ", result)

    def test_brand_normalization(self):
        # 4. ทดสอบการแปลงชื่อค่ายแบรนด์ไอทีภาษาไทยให้เป็นภาษาอังกฤษสากล
        text = "อยากจัดคอมค่ายอินเทลกับการ์ดจอเอ็นวิเดียและเมนบอร์ดเอซุสค่ะ"
        result = preprocess_thai_text(text)
        print(f"[Test 4] Original: '{text}' \n         Result:   '{result}'")
        
        self.assertIn("intel", result)
        self.assertIn("nvidia", result)
        self.assertIn("asus", result)
        self.assertNotIn("อินเทล", result)
        self.assertNotIn("เอ็นวิเดีย", result)
        self.assertNotIn("เอซุส", result)

    def test_empty_and_null_input(self):
        # 5. ทดสอบความทนทานต่อค่าว่าง หรือ Null Input
        self.assertEqual(preprocess_thai_text(""), "")
        self.assertEqual(preprocess_thai_text(None), "")

    def test_thai_tokenizer(self):
        # 6. ทดสอบการตัดคำภาษาไทยแบบ Custom Tokenizer ของ Rasa
        from app.rasa.thai_tokenizer import ThaiTokenizer
        from rasa.shared.nlu.training_data.message import Message

        tokenizer = ThaiTokenizer({"case_sensitive": True})
        msg = Message.build(text="จัดสเปคคอมงบ30000เล่นเกม")
        tokens = tokenizer.tokenize(msg, "text")
        token_texts = [t.text for t in tokens]
        print(f"[Test Tokenizer] Original: 'จัดสเปคคอมงบ30000เล่นเกม' \n                 Tokens:   {token_texts}")
        
        self.assertTrue(len(tokens) > 0)
        self.assertIn("จัด", token_texts)
        self.assertIn("สเปค", token_texts)
        self.assertIn("คอม", token_texts)
        self.assertIn("30000", token_texts)
        self.assertIn("เล่น", token_texts)
        self.assertIn("เกม", token_texts)

if __name__ == "__main__":
    unittest.main()
