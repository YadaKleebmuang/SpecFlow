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
from app.services.recommendation.usage import USAGE_LABELS, classify_usage
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
    return USAGE_LABELS[classify_usage(usage)]

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
                "texts": [
                    "CPU (ซีพียู) เปรียบเสมือนสมองของคอมพิวเตอร์ ทำหน้าที่ประมวลผลคำสั่งต่างๆ ยิ่งมี Core/Thread เยอะและความเร็ว (GHz) สูง ก็ยิ่งประมวลผลงานหนักๆ หรือหลายโปรแกรมพร้อมกันได้ดีครับ\n💡 สอบถามเพิ่มเติม: สามารถถามเกี่ยวกับอุปกรณ์ที่ต้องทำงานร่วมกัน เช่น 'เมนบอร์ดคืออะไร', 'ชุดระบายความร้อนคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "CPU ทำหน้าที่ประมวลผลกลาง คล้ายกับสมองส่วนสั่งการครับ หากต้องการเปิดโปรแกรมหลายตัวพร้อมกัน หรือทำงานประมวลผลหนัก แนะนำให้เลือก CPU ที่มี Cores/Threads เยอะ เช่น Intel Core i5/i7 หรือ AMD Ryzen 5/7 ครับ\n💡 สอบถามเพิ่มเติม: แนะนำให้ศึกษาเรื่อง 'เมนบอร์ดคืออะไร' เพื่อดู Socket หรือ 'RAM คืออะไร' เพื่อเลือกบัสแรม หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "สำหรับสายเล่นเกม นอกจากการ์ดจอแล้ว ความเร็วสัญญาณนาฬิกา (Clock Speed / GHz) ของ CPU ก็สำคัญมากครับ เพราะจะช่วยให้การคำนวณเฟรมเรตในเกมมีความนิ่งและลื่นไหลไม่มีสะดุดครับ\n💡 สอบถามเพิ่มเติม: เพื่อรีดพลัง CPU ให้เต็มที่ สามารถถามเรื่อง 'การ์ดจอคืออะไร', 'ชุดระบายความร้อนคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_gpu_info": {
                "file": "card_faq_gpu.json",
                "texts": [
                    "GPU (การ์ดจอ) ทำหน้าที่ประมวลผลภาพและกราฟิกครับ ถ้าคุณเน้นเล่นเกม 3D หรือทำงานตัดต่อ/เรนเดอร์วิดีโอ การ์ดจอที่แรงจะช่วยให้ภาพลื่นไหลและทำงานเสร็จไวขึ้นมากครับ\n💡 สอบถามเพิ่มเติม: การ์ดจอแรงๆ ต้องใช้ไฟพอดีและเคสที่จุได้ ลองถาม 'พาวเวอร์ซัพพลายคืออะไร', 'เคสคอมคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "GPU ทำงานร่วมกับ VRAM (หน่วยความจำบนการ์ดจอ) หากคุณเปิดจอความละเอียดสูง (2K/4K) หรือทำงานกราฟิกขนาดใหญ่ การเลือกการ์ดจอที่มี VRAM ขนาด 8GB ขึ้นไป จะช่วยลดปัญหาเฟรมเรตร่วงและอาการภาพโหลดช้าได้ดีครับ\n💡 สอบถามเพิ่มเติม: ใช้งานกราฟิกหรือเล่นเกมความละเอียดสูง สามารถถามต่อเรื่อง 'CPU คืออะไร', 'พาวเวอร์ซัพพลายคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "ควรเลือกการ์ดจอค่ายไหนดี? การ์ดจอ NVIDIA เด่นเรื่องเทคโนโลยี Ray Tracing และ DLSS ที่ช่วยเร่งประสิทธิภาพในเกม รวมถึงมีโปรแกรมเฉพาะทางรองรับเยอะ ส่วนค่าย AMD จะเด่นเรื่องความคุ้มค่าต่อราคาและปริมาณ VRAM ที่ให้มาเยอะครับ\n💡 สอบถามเพิ่มเติม: สนใจคำนวณไฟและการประกอบ ลองถาม 'พาวเวอร์ซัพพลายคืออะไร', 'เคสคอมคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_ram_info": {
                "file": "card_faq_ram.json",
                "texts": [
                    "RAM (แรม) คือหน่วยความจำชั่วคราว ยิ่งมี RAM เยอะ (เช่น 16GB หรือ 32GB) คอมพิวเตอร์ก็จะสามารถเปิดหลายๆ โปรแกรมพร้อมกัน หรือเปิดแท็บเบราว์เซอร์เยอะๆ ได้โดยที่เครื่องไม่ค้างครับ\n💡 สอบถามเพิ่มเติม: แนะนำให้เช็กความเข้ากันได้โดยถาม 'เมนบอร์ดคืออะไร' (ดู DDR4/DDR5) หรือ 'SSD ต่างกับ HDD ยังไง' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "ปัจจุบันแรมมีทั้ง DDR4 และ DDR5 ครับ โดย DDR5 จะมีความเร็วบัสการรับส่งข้อมูล (Speed) ที่เร็วกว่า ประหยัดพลังงานมากกว่า แต่จะต้องใช้ร่วมกับเมนบอร์ดและ CPU รุ่นใหม่ที่รองรับเท่านั้น ไม่สามารถใส่ปนกันได้ครับ\n💡 สอบถามเพิ่มเติม: อยากรู้ว่าเมนบอร์ดหรือ CPU รุ่นไหนรองรับบัส DDR5 ลองถาม 'เมนบอร์ดคืออะไร', 'CPU คืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "ความจุ RAM เท่าไหร่ถึงจะพอในปัจจุบัน? ขนาด 8GB เหมาะกับการใช้งานเอกสาร/ท่องเว็บทั่วไป ขนาด 16GB เป็นมาตรฐานสำหรับการเล่นเกมยุคใหม่ ส่วนขนาด 32GB ขึ้นไป เหมาะกับสายตัดต่อกราฟิก ทำงาน 3D หรือสตรีมเกมครับ\n💡 สอบถามเพิ่มเติม: สำหรับการทำงานหลายอย่างพร้อมกัน ลองถามเรื่อง 'Storage คืออะไร', 'CPU คืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_ssd_hdd_diff": {
                "file": "card_faq_ssd_hdd.json",
                "texts": [
                    "SSD และ HDD เป็นตัวเก็บข้อมูลทั้งคู่ครับ แต่ SSD จะเร็วกว่า HDD หลายสิบเท่า ทำให้เปิดเครื่องและโหลดเกมไวมาก ส่วน HDD จะมีราคาถูกกว่าในความจุที่เท่ากัน แนะนำให้ใช้ SSD ลงวินโดว์และโปรแกรมหลัก แล้วใช้ HDD เก็บไฟล์งานทั่วไปครับ\n💡 สอบถามเพิ่มเติม: อยากเข้าใจช่องต่อ NVMe M.2 และพอร์ตบนบอร์ด ลองถาม 'Storage คืออะไร', 'เมนบอร์ดคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "SSD เองก็แบ่งเป็นสองแบบหลักๆ คือ SATA (ความเร็วประมาณ 500 MB/s) และ PCIe NVMe M.2 (ความเร็วสูงถึง 3000-7000 MB/s) แนะนำให้เลือกซื้อแบบ NVMe M.2 เพื่อความเร็วในการโอนถ่ายข้อมูลที่คุ้มค่าที่สุดในปัจจุบันครับ\n💡 สอบถามเพิ่มเติม: นอกจากความเร็ว SSD ความเร็วหน่วยความจำชั่วคราวก็สำคัญ ลองถาม 'RAM คืออะไร', 'เมนบอร์ดคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "ความทนทานและการเก็บรักษาข้อมูล: HDD ใช้จานแม่เหล็กหมุน มีโอกาสเสียหากได้รับการกระแทกขณะทำงาน ส่วน SSD ใช้ชิปหน่วยความจำทนแรงกระแทกได้ดีกว่า แต่อายุการใช้งาน SSD จะนับตามปริมาณการเขียนข้อมูล (TBW) ครับ\n💡 สอบถามเพิ่มเติม: สนใจแนวทางการเลือกไดรฟ์เก็บข้อมูลและการติดตั้ง ลองถาม 'Storage คืออะไร', 'เคสคอมคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_mainboard_info": {
                "file": "card_faq_mainboard.json",
                "texts": [
                    "Mainboard (เมนบอร์ด) คือแผงวงจรหลักที่เชื่อม CPU, RAM, การ์ดจอ และอุปกรณ์เก็บข้อมูลเข้าด้วยกันครับ ก่อนเลือกควรดู CPU ที่รองรับ ชนิด RAM จำนวนสล็อต M.2/SATA และพอร์ตที่ต้องใช้ให้ตรงกับงาน\n💡 สอบถามเพิ่มเติม: เมนบอร์ดต้องเข้าคู่กับอุปกรณ์อื่นๆ ลองถาม 'CPU คืออะไร' (เช็ก Socket), 'RAM คืออะไร' (DDR4/5) หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "การเลือกเมนบอร์ดต้องตรวจ Socket เช่น AM4, AM5 หรือ LGA1700 ให้ตรงกับ CPU และตรวจรายชื่อ CPU ที่รองรับกับเวอร์ชัน BIOS ของบอร์ดรุ่นนั้นด้วยครับ Socket ตรงกันอย่างเดียวไม่ได้ยืนยันว่าใช้ร่วมกันได้ทุกกรณี\n💡 สอบถามเพิ่มเติม: อยากรู้ขนาดบอร์ดและการลงเคส ลองถาม 'เคสคอมคืออะไร', 'ชุดระบายความร้อนคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "เมนบอร์ดมีขนาด เช่น ATX, Micro-ATX และ Mini-ITX ซึ่งต้องตรงกับขนาดที่เคสรองรับครับ ส่วน DDR4 กับ DDR5 ใช้แทนกันในสล็อตเดียวกันไม่ได้ ต้องตรวจชนิด RAM ที่เมนบอร์ดรุ่นนั้นและ CPU รองรับก่อนซื้อ\n💡 สอบถามเพิ่มเติม: ตรวจสอบความเข้ากันได้ของระบบ ลองถาม 'CPU คืออะไร', 'เคสคอมคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_storage_info": {
                "file": "card_faq_storage.json",
                "texts": [
                    "Storage คืออุปกรณ์เก็บระบบปฏิบัติการ โปรแกรม และไฟล์ไว้แม้ปิดเครื่อง เช่น SSD และ HDD ครับ ความจุกำหนดว่าเก็บข้อมูลได้มากแค่ไหน ส่วนความเร็วอ่านเขียนมีผลกับการโหลดและย้ายไฟล์ หากต้องการเปรียบเทียบสองชนิดนี้ ถามว่า SSD กับ HDD ต่างกันอย่างไรได้เลยครับ\n💡 สอบถามเพิ่มเติม: อยากรู้ความแตกต่างเชิงลึกระหว่างไดรฟ์แต่ละประเภท ลองถาม 'SSD ต่างกับ HDD ยังไง', 'เมนบอร์ดคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "M.2 เป็นรูปแบบตัวอุปกรณ์ ไม่ได้หมายความว่าเป็น NVMe เสมอไปครับ SSD แบบ M.2 มีทั้ง SATA และ PCIe NVMe จึงต้องตรวจว่าเมนบอร์ดรองรับชนิดใด ความเร็วจริงขึ้นกับรุ่นไดรฟ์ การเชื่อมต่อ และลักษณะงาน ไม่ใช่ดูคำว่า M.2 อย่างเดียว\n💡 สอบถามเพิ่มเติม: เพื่อเลือกความจุและช่อง M.2 ให้ตรงกับงาน ลองถาม 'เมนบอร์ดคืออะไร', 'RAM คืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "การจัดไดรฟ์ควรแยกให้ง่ายต่อการดูแล เช่น ใช้ SSD ลงระบบปฏิบัติการและโปรแกรม แล้วเลือกพื้นที่เก็บไฟล์งานให้พอกับการใช้งานครับ การแบ่งพาร์ทิชันในไดรฟ์เดียวไม่ใช่การสำรองข้อมูล ควรมีสำเนาไฟล์สำคัญแยกไว้อีกอุปกรณ์หรือบริการสำรองข้อมูลด้วย\n💡 สอบถามเพิ่มเติม: สำหรับการจัดพื้นที่เก็บไฟล์และการสำรองข้อมูล ลองถาม 'SSD ต่างกับ HDD ยังไง', 'RAM คืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_psu_info": {
                "file": "card_faq_psu.json",
                "texts": [
                    "PSU (พาวเวอร์ซัพพลาย) แปลงไฟจากเต้ารับเป็นไฟที่อุปกรณ์คอมพิวเตอร์ใช้ครับ ควรเลือกกำลังไฟและหัวต่อให้เหมาะกับ CPU, GPU และอุปกรณ์ทั้งหมด พร้อมตรวจขนาด PSU ให้ติดตั้งในเคสได้\n💡 สอบถามเพิ่มเติม: PSU ต้องจ่ายไฟให้พอดีกับการ์ดจอและ CPU ลองถาม 'การ์ดจอคืออะไร', 'เคสคอมคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' เพื่อคำนวณวัตต์ได้เลยครับ",
                    "การประเมิน PSU ต้องรวมกำลังไฟของ CPU, GPU และอุปกรณ์อื่น พร้อมเผื่อภาระสูงสุดครับ SpecFlow ใช้ CPU TDP + GPU Power + 100W เป็นกฎเบื้องต้น แต่ควรตรวจคำแนะนำ PSU จากผู้ผลิตการ์ดจอและหัวต่อไฟของรุ่นที่จะใช้ด้วย เพราะ TDP ไม่ใช่กำลังไฟสูงสุดของทุกสถานการณ์\n💡 สอบถามเพิ่มเติม: หากสนใจประเมินกำลังไฟร่วมกับฮาร์ดแวร์หลัก ลองถาม 'การ์ดจอคืออะไร', 'CPU คืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "80 PLUS เช่น Standard/White, Bronze และ Gold เป็นระดับประสิทธิภาพการแปลงพลังงาน ไม่ใช่จำนวนวัตต์ที่ PSU จ่ายได้ครับ ควรดูระบบป้องกันแยกด้วย เช่น OVP ป้องกันแรงดันเกิน, OCP ป้องกันกระแสเกิน และ SCP ป้องกันลัดวงจร โดยตรวจข้อมูลของ PSU รุ่นนั้น\n💡 สอบถามเพิ่มเติม: ตรวจสอบขนาด PSU และการจัดสายไฟในเคส ลองถาม 'เคสคอมคืออะไร', 'การ์ดจอคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_case_info": {
                "file": "card_faq_case.json",
                "texts": [
                    "Case (เคสคอมพิวเตอร์) เป็นโครงสำหรับยึดและปกป้องอุปกรณ์ พร้อมจัดพื้นที่เดินสายและระบายอากาศครับ ก่อนเลือกให้ตรวจว่ารองรับเมนบอร์ด ATX, Micro-ATX หรือ Mini-ITX ที่ต้องการ รวมถึงขนาด PSU และช่องติดตั้งไดรฟ์\n💡 สอบถามเพิ่มเติม: เคสต้องมีพื้นที่พอดีกับชิ้นส่วนหลัก ลองถาม 'ชุดระบายความร้อนคืออะไร', 'เมนบอร์ดคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "นอกจากขนาดเมนบอร์ด ต้องตรวจความยาวและความหนาของ GPU ความสูงชุดระบายความร้อน CPU และตำแหน่งติดตั้งหม้อน้ำ AIO ด้วยครับ พื้นที่จริงอาจลดลงเมื่อติดพัดลมหรือหม้อน้ำ ควรเทียบขนาดอุปกรณ์กับคู่มือเคสรุ่นนั้นก่อนประกอบ\n💡 สอบถามเพิ่มเติม: อยากรู้ระยะความยาวการ์ดจอหรือหม้อน้ำ ลองถาม 'การ์ดจอคืออะไร', 'ชุดระบายความร้อนคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "Airflow คือการไหลเวียนอากาศผ่านอุปกรณ์เพื่อพาความร้อนออกจากเคสครับ การจัดพัดลมรับลมด้านหน้าหรือด้านล่าง และระบายออกด้านหลังหรือด้านบนเป็นแนวทางทั่วไป แต่ต้องดูโครงสร้างเคสด้วย จัดสายไม่ให้ขวางลมและทำความสะอาดแผ่นกรองฝุ่นเป็นระยะ\n💡 สอบถามเพิ่มเติม: เพื่อการระบายความร้อนและเลือกพาวเวอร์ซัพพลาย ลองถาม 'พาวเวอร์ซัพพลายคืออะไร', 'ชุดระบายความร้อนคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_cooler_info": {
                "file": "card_faq_cooler.json",
                "texts": [
                    "CPU Cooler ช่วยนำความร้อนออกจาก CPU ครับ หากความร้อนสูงจนถึงขีดจำกัด CPU อาจลดความเร็วเพื่อควบคุมอุณหภูมิ เรียกว่า Thermal Throttling จึงควรเลือกชุดระบายความร้อนที่เหมาะกับภาระงานและติดตั้งให้แนบกับ CPU ตามคู่มือ\n💡 สอบถามเพิ่มเติม: ซิงก์ต้องใส่กับ Socket ของ CPU และเคสได้ ลองถาม 'CPU คืออะไร', 'เคสคอมคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "ชุดลม (Air Cooler) ใช้ฮีตซิงก์และพัดลม ส่วนชุดน้ำปิด AIO ใช้ปั๊มหมุนเวียนของเหลวไปยังหม้อน้ำครับ ทั้งสองแบบต้องมีพื้นที่และทางลมที่เหมาะสม ผลการระบายความร้อนขึ้นกับรุ่น ขนาด และการติดตั้ง ชุดน้ำไม่ได้เย็นกว่าชุดลมทุกกรณี\n💡 สอบถามเพิ่มเติม: เปรียบเทียบการระบายความร้อนกับอุปกรณ์หลัก ลองถาม 'CPU คืออะไร', 'เมนบอร์ดคืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ",
                    "ก่อนติดตั้ง Cooler ให้ตรวจชุดขายึดว่ารองรับ Socket ของ CPU และเช็กความสูงฮีตซิงก์กับเคส รวมถึงพื้นที่ชนกับ RAM ครับ สำหรับ AIO ต้องตรวจขนาดและตำแหน่งหม้อน้ำ ติดตั้งซิลิโคน พัดลม และสายปั๊มตามคู่มือผู้ผลิต แล้วตรวจอุณหภูมิระหว่างใช้งาน\n💡 สอบถามเพิ่มเติม: ตรวจสอบขนาดหม้อน้ำและความสูงซิงก์ ลองถาม 'เคสคอมคืออะไร', 'RAM คืออะไร' หรือพิมพ์ 'อยากจัดสเปคคอม' ได้เลยครับ"
                ]
            },
            "ask_bot_capabilities": {
                "file": "card_bot_capabilities.json",
                "texts": [
                    "SpecFlow ช่วยคุณได้ 4 ด้านครับ:\n1. 💻 จัดสเปคคอมพิวเตอร์: ตามงบและงาน 5 หมวด: เล่นเกม กราฟิก ตัดต่อวิดีโอ เขียนโปรแกรม และสำนักงาน\n2. 🔧 แนะนำการอัปเกรด: วิเคราะห์สเปคเดิมและประเมินคอขวด CPU/GPU เบื้องต้น เพื่อช่วยวางแผนอัปเกรด\n3. 📚 ความรู้ฮาร์ดแวร์: CPU, GPU, RAM, Mainboard, Storage, PSU, Case และ Cooler พร้อมหัวข้อ SSD/HDD\n4. ⚡ แก้ปัญหาคอมช้า: แนวทางปรับแต่ง Windows และดูแลฮาร์ดแวร์เบื้องต้น\nเริ่มได้โดยพิมพ์ว่า อยากจัดสเปคคอม, อยากอัปเกรดคอม, CPU คืออะไร หรือ คอมช้าทำอย่างไร ครับ"
                ]
            }
        }
        
        cfg = intent_map.get(latest_intent)
        if cfg:
            # Randomly select a variation index
            num_variations = len(cfg["texts"])
            selected_idx = random.randint(0, num_variations - 1)
            selected_text = cfg["texts"][selected_idx]

            if tracker.get_latest_input_channel() == "line":
                try:
                    card_payload = load_static_card(cfg["file"])
                    if isinstance(card_payload, list):
                        # Use the matched index if valid, else fallback to random choice
                        if selected_idx < len(card_payload):
                            selected_card = card_payload[selected_idx]
                        else:
                            selected_card = random.choice(card_payload)
                        dispatcher.utter_message(custom=selected_card)
                    else:
                        dispatcher.utter_message(custom=card_payload)
                except Exception as e:
                    print(f"Error loading FAQ card {cfg['file']}: {e}")
                    dispatcher.utter_message(text=selected_text)
            else:
                dispatcher.utter_message(text=selected_text)
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
                dispatcher.utter_message(text="คุณเน้นนำไปใช้งานด้านไหนเป็นหลักครับ? (เช่น เล่นเกม, งานกราฟิก, ตัดต่อวิดีโอ, เขียนโปรแกรม, งานสำนักงาน)")
        else:
            dispatcher.utter_message(text="คุณเน้นนำไปใช้งานด้านไหนเป็นหลักครับ? (เช่น เล่นเกม, งานกราฟิก, ตัดต่อวิดีโอ, เขียนโปรแกรม, งานสำนักงาน)")
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
