from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import sys
import os
import sqlite3
import datetime
import re
import random

# Add the project root to sys.path to allow importing from the app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from app.services.recommendation.spec_recommender import SpecRecommender
from app.rasa.actions.flex import (
    generate_spec_flex_message, 
    generate_upgrade_flex_message, 
    load_static_card
)

# ฐานข้อมูล SQLite เก็บไว้ในโฟลเดอร์ data/ ของโครงการ
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/analytics.db"))

def init_db():
    # ตรวจสอบและสร้างตาราง user_searches หากยังไม่มีในระบบ
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            usage_type TEXT NOT NULL,
            budget_requested INTEGER NOT NULL,
            allocated_total_price INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_search(user_id: str, usage_type: str, budget_requested: int, allocated_total_price: int):
    try:
        init_db() # ตรวจสอบให้มั่นใจว่าตารางถูกสร้างแล้ว
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO user_searches (timestamp, user_id, usage_type, budget_requested, allocated_total_price)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, user_id, usage_type, budget_requested, allocated_total_price))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging search to database: {e}")

def get_usage_type_db(usage: str) -> str:
    usage_lower = usage.lower() if usage else ""
    editing_keywords = [
        'ตัดต่อ', 'เรนเดอร์', 'กราฟิก', 'วาดรูป', 'ออกแบบ', 'สตรีม', 'เขียนโค้ด', 'โปรแกรม', 
        'เขียนแบบ', 'โมเดล', 'ทำเพลง', 'edit', 'render', 'work', 'graphic', 'design', 
        'stream', 'code', 'develop', '3d', 'photoshop', 'illustrator', 'premiere', 
        'after effect', 'autocad', 'blender', 'sketchup', 'lightroom', 'cad'
    ]
    office_keywords = [
        'ทั่วไป', 'ออฟฟิศ', 'พิมพ์งาน', 'เอกสาร', 'เรียน', 'เทรด', 'ดูหนัง', 'ฟังเพลง', 
        'สำนักงาน', 'บัญชี', 'ศึกษา', 'office', 'study', 'learn', 'trade', 'excel', 
        'word', 'powerpoint', 'youtube', 'netflix', 'surf', 'browse'
    ]
    if any(word in usage_lower for word in editing_keywords):
        return "กราฟิก"
    elif any(word in usage_lower for word in office_keywords):
        return "ออฟฟิศ"
    else:
        return "เล่นเกม"

# เรียกใช้งานเตรียมระบบฐานข้อมูลเบื้องหลังตั้งแต่เริ่มโหลดไฟล์
init_db()

class ActionGreet(Action):
    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_latest_input_channel() == "line":
            try:
                greet_cards = load_static_card("card_greet.json")
                selected_card = random.choice(greet_cards)
                dispatcher.utter_message(custom=selected_card)
            except Exception as e:
                print(f"Error loading greet template: {e}")
                dispatcher.utter_message(text="สวัสดีครับ ยินดีต้อนรับสู่ SpecFlow มีอะไรให้ผมช่วยจัดสเปค หรืออัปเกรดคอมไหมครับ?")
        else:
            dispatcher.utter_message(text="สวัสดีครับ ยินดีต้อนรับสู่ SpecFlow มีอะไรให้ผมช่วยจัดสเปค หรืออัปเกรดคอมไหมครับ?")
        return []

class ActionGoodbye(Action):
    def name(self) -> Text:
        return "action_goodbye"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_latest_input_channel() == "line":
            try:
                goodbye_cards = load_static_card("card_goodbye.json")
                selected_card = random.choice(goodbye_cards)
                dispatcher.utter_message(custom=selected_card)
            except Exception as e:
                print(f"Error loading goodbye template: {e}")
                dispatcher.utter_message(text="ยินดีที่ได้ช่วยเหลือครับ! หากต้องการจัดสเปคคอมพิวเตอร์หรือขอคำแนะนำอีก พิมพ์มาบอกผมได้ตลอดเลยนะครับ บ๊ายบายครับ! 💻👋")
        else:
            dispatcher.utter_message(text="ยินดีที่ได้ช่วยเหลือครับ! หากต้องการจัดสเปคคอมพิวเตอร์หรือขอคำแนะนำอีก พิมพ์มาบอกผมได้ตลอดเลยนะครับ บ๊ายบายครับ! 💻👋")
        return []

class ActionFAQ(Action):
    def name(self) -> Text:
        return "action_faq"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        latest_intent = tracker.latest_message.get("intent", {}).get("name", "")
        
        intent_map = {
            "ask_cpu_info": {
                "file": "card_faq_cpu.json",
                "text": "CPU (ซีพียู) เปรียบเสมือนสมองของคอมพิวเตอร์ ทำหน้าที่ประมวลผลคำสั่งต่างๆ ยิ่งมี Core/Thread เยอะและความเร็ว (GHz) สูง ก็ยิ่งประมวลผลงานหนักๆ หรือหลายโปรแกรมพร้อมกันได้ดีครับ"
            },
            "ask_gpu_info": {
                "file": "card_faq_gpu.json",
                "text": "GPU (การ์ดจอ) ทำหน้าที่ประมวลผลภาพและกราฟิกครับ ถ้าคุณเน้นเล่นเกม 3D หรือทำงานตัดต่อ/เรนเดอร์วิดีโอ การ์ดจอที่แรงจะช่วยให้ภาพลื่นไหลและทำงานเสร็จไวขึ้นมากครับ"
            },
            "ask_ram_info": {
                "file": "card_faq_ram.json",
                "text": "RAM (แรม) คือหน่วยความจำชั่วคราว ยิ่งมี RAM เยอะ (เช่น 16GB หรือ 32GB) คอมพิวเตอร์ก็จะสามารถเปิดหลายๆ โปรแกรมพร้อมกัน หรือเปิดแท็บเบราว์เซอร์เยอะๆ ได้โดยที่เครื่องไม่ค้างครับ"
            },
            "ask_ssd_hdd_diff": {
                "file": "card_faq_ssd_hdd.json",
                "text": "SSD และ HDD เป็นตัวเก็บข้อมูลทั้งคู่ครับ แต่ SSD จะเร็วกว่า HDD หลายสิบเท่า ทำให้เปิดเครื่องและโหลดเกมไวมาก ส่วน HDD จะมีราคาถูกกว่าในความจุที่เท่ากัน แนะนำให้ใช้ SSD ลงวินโดว์และโปรแกรมหลัก แล้วใช้ HDD เก็บไฟล์งานทั่วไปครับ"
            }
        }
        
        cfg = intent_map.get(latest_intent)
        if cfg:
            if tracker.get_latest_input_channel() == "line":
                try:
                    card_payload = load_static_card(cfg["file"])
                    dispatcher.utter_message(custom=card_payload)
                except Exception as e:
                    print(f"Error loading FAQ card {cfg['file']}: {e}")
                    dispatcher.utter_message(text=cfg["text"])
            else:
                dispatcher.utter_message(text=cfg["text"])
        else:
            dispatcher.utter_message(text="ขออภัยครับ ผมยังไม่มีข้อมูลสำหรับคำถามนี้ครับ")
        return []

class ActionOptimizePerformance(Action):
    def name(self) -> Text:
        return "action_optimize_performance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        fallback_text = (
            "สำหรับการเพิ่มความเร็วและการปรับแต่งให้คอมพิวเตอร์ทำงานลื่นไหลขึ้น เบื้องต้นผมขอแนะนำดังนี้ครับ:\n"
            "1. **อัปเดตไดรเวอร์**: โดยเฉพาะไดรเวอร์การ์ดจอ ให้เป็นเวอร์ชันล่าสุดเสมอ\n"
            "2. **ปิด Startup Programs**: ปิดโปรแกรมที่ไม่ได้ใช้แต่รันขึ้นมาพร้อมวินโดวส์\n"
            "3. **เคลียร์ไฟล์ขยะ (Disk Cleanup)**: และตรวจสอบไม่ให้ไดรฟ์ C: เต็มจนเกินไป\n"
            "4. **เปิด Game Mode / High Performance Power Plan**: ในตั้งค่า Windows เพื่อรีดประสิทธิภาพสูงสุดครับ\n\n"
            "*หากทำตามนี้แล้วยังช้าอยู่ อาจถึงเวลาต้องอัปเกรดฮาร์ดแวร์ (สามารถพิมพ์ว่า 'อยากอัปเกรดคอม' เพื่อให้ผมช่วยวิเคราะห์ได้ครับ)*"
        )
        if tracker.get_latest_input_channel() == "line":
            try:
                card_payload = load_static_card("card_optimize_performance.json")
                dispatcher.utter_message(custom=card_payload)
            except Exception as e:
                print(f"Error loading optimize template: {e}")
                dispatcher.utter_message(text=fallback_text)
        else:
            dispatcher.utter_message(text=fallback_text)
        return []

class ActionRecommendPC(Action):
    def name(self) -> Text:
        return "action_recommend_pc"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        budget = tracker.get_slot("budget")
        usage = tracker.get_slot("usage")
        future_upgrade_slot = tracker.get_slot("future_upgrade")
        
        # Convert to boolean. True if it's explicitly True or a string meaning yes.
        is_future = False
        if future_upgrade_slot is True:
            is_future = True
        elif isinstance(future_upgrade_slot, str) and future_upgrade_slot.lower() in ['true', 'yes', 'ใช่', 'เผื่อ', 'เผื่อด้วย']:
            is_future = True

        recommender = SpecRecommender()
        result = recommender.get_recommendation(budget, usage, future_upgrade=is_future)

        if isinstance(result, dict) and result.get("status") == "success":
            # Generate Flex Message payload (including warning if present)
            flex_payload = generate_spec_flex_message(
                total_price=result["total_price"], 
                components=result["components"],
                usage=usage,
                warning=result.get("warning", "")
            )
            # Send only the Flex Message for LINE to avoid sending two messages, fallback to text for others
            if tracker.get_latest_input_channel() == "line":
                dispatcher.utter_message(custom=flex_payload)
            else:
                dispatcher.utter_message(text=result["text"])

            # บันทึกสถิติการใช้งานลงฐานข้อมูล SQLite
            try:
                user_id = tracker.sender_id or "anonymous"
                usage_type_db = get_usage_type_db(usage)

                # แปลงงบประมาณเป็นจำนวนเต็ม
                digits = re.sub(r'[^\d]', '', budget) if budget else ""
                budget_val = int(digits) if digits else 0
                allocated_total_price = result.get("total_price", 0)

                log_search(user_id, usage_type_db, budget_val, allocated_total_price)
            except Exception as ex:
                print(f"Error logging search data: {ex}")

        elif isinstance(result, dict):
            dispatcher.utter_message(text=result.get("text", "เกิดข้อผิดพลาดในการคำนวณสเปคครับ"))
        else:
            # Fallback if result is just a string
            dispatcher.utter_message(text=str(result))

        return [
            SlotSet("budget", None),
            SlotSet("usage", None),
            SlotSet("future_upgrade", None)
        ]

class ActionRecommendUpgrade(Action):
    def name(self) -> Text:
        return "action_recommend_upgrade"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        current_specs = tracker.get_slot("current_specs")
        usage = tracker.get_slot("usage")

        from app.services.recommendation.upgrade_advisor import UpgradeAdvisor
        advisor = UpgradeAdvisor()
        result = advisor.analyze_upgrade(current_specs, usage)

        if isinstance(result, dict) and result.get("status") == "success":
            # Send Flex Message for LINE if recommendations list is present, fallback to text for others
            if tracker.get_latest_input_channel() == "line" and result.get("recommendations"):
                try:
                    flex_payload = generate_upgrade_flex_message(
                        total_price=result["total_price"],
                        recommendations=result["recommendations"],
                        usage=usage
                    )
                    dispatcher.utter_message(custom=flex_payload)
                except Exception as e:
                    print(f"Error generating upgrade Flex Message: {e}")
                    dispatcher.utter_message(text=result["text"])
            else:
                dispatcher.utter_message(text=result["text"])

            # บันทึกสถิติการอัปเกรดคอมพิวเตอร์ลงฐานข้อมูล SQLite
            try:
                user_id = tracker.sender_id or "anonymous"
                usage_type_db = get_usage_type_db(usage)

                # ตรวจสอบงบประมาณถ้ามีระบุใน slot (หรือบันทึกเป็น 0 หากไม่มี)
                budget = tracker.get_slot("budget")
                digits = re.sub(r'[^\d]', '', budget) if budget else ""
                budget_val = int(digits) if digits else 0

                # งบประมาณเฉลี่ยรวมที่แนะนำในการอัปเกรด
                allocated_total_price = result.get("total_price", 0)

                log_search(user_id, usage_type_db, budget_val, allocated_total_price)
            except Exception as ex:
                print(f"Error logging upgrade search data: {ex}")

        elif isinstance(result, dict):
            dispatcher.utter_message(text=result.get("text", "เกิดข้อผิดพลาดในการวิเคราะห์สเปคครับ"))
        else:
            dispatcher.utter_message(text=str(result))

        return [
            SlotSet("usage", None),
            SlotSet("current_specs", None)
        ]


class ActionAskUsage(Action):
    def name(self) -> Text:
        return "action_ask_usage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_latest_input_channel() == "line":
            try:
                card_payload = load_static_card("card_ask_usage.json")
                dispatcher.utter_message(custom=card_payload)
            except Exception as e:
                print(f"Error loading ask_usage template: {e}")
                dispatcher.utter_message(text="คุณเน้นนำไปใช้งานด้านไหนเป็นหลักครับ? (เช่น เล่นเกม, งานกราฟิกหรือวิดีโอ, งานสำนักงาน)")
        else:
            dispatcher.utter_message(text="คุณเน้นนำไปใช้งานด้านไหนเป็นหลักครับ? (เช่น เล่นเกม, งานกราฟิกหรือวิดีโอ, งานสำนักงาน)")
        return []


class ActionAskCurrentSpecs(Action):
    def name(self) -> Text:
        return "action_ask_current_specs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_latest_input_channel() == "line":
            try:
                card_payload = load_static_card("card_ask_current_specs.json")
                dispatcher.utter_message(custom=card_payload)
            except Exception as e:
                print(f"Error loading ask_current_specs template: {e}")
                dispatcher.utter_message(text="ปัจจุบันคุณใช้คอมพิวเตอร์สเปคอะไรอยู่บ้างครับ? (เช่น CPU, การ์ดจอ, แรม) พอบอกคร่าวๆ ได้ไหมครับ?")
        else:
            dispatcher.utter_message(text="ปัจจุบันคุณใช้คอมพิวเตอร์สเปคอะไรอยู่บ้างครับ? (เช่น CPU, การ์ดจอ, แรม) พอบอกคร่าวๆ ได้ไหมครับ?")
        return []


class ActionAskFutureUpgrade(Action):
    def name(self) -> Text:
        return "action_ask_future_upgrade"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_latest_input_channel() == "line":
            try:
                card_payload = load_static_card("card_ask_future_upgrade.json")
                dispatcher.utter_message(custom=card_payload)
            except Exception as e:
                print(f"Error loading ask_future_upgrade template: {e}")
                dispatcher.utter_message(text="คุณต้องการเผื่ออัปเกรดในอนาคตด้วยไหมครับ? (เช่น เลือกเมนบอร์ดและแรมรุ่นใหม่ๆ เผื่อไว้) ตอบ ใช่/ไม่ หรือพิมพ์บอกได้เลยครับ")
        else:
            dispatcher.utter_message(text="คุณต้องการเผื่ออัปเกรดในอนาคตด้วยไหมครับ? (เช่น เลือกเมนบอร์ดและแรมรุ่นใหม่ๆ เผื่อไว้) ตอบ ใช่/ไม่ หรือพิมพ์บอกได้เลยครับ")
        return []
