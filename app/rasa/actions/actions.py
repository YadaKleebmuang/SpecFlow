from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import sys
import os
import sqlite3
import datetime
import re

# Add the project root to sys.path to allow importing from the app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from app.services.recommendation.spec_recommender import SpecRecommender
from app.rasa.actions.flex import generate_spec_flex_message

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
