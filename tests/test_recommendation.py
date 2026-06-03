import sys
import os
import unittest

# เพิ่มโฟลเดอร์หลักของโปรเจกต์ (Project Root) เข้ามาใน sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.recommendation.spec_recommender import SpecRecommender
from app.services.recommendation.upgrade_advisor import UpgradeAdvisor

class TestSpecFlowRecommendation(unittest.TestCase):

    def setUp(self):
        self.recommender = SpecRecommender()
        self.advisor = UpgradeAdvisor()

    def test_spec_recommender_compatibility(self):
        # 1. ทดสอบการจัดสเปคด้วยงบประมาณและลักษณะการใช้งานที่หลากหลาย
        test_cases = [
            {"budget": "20000", "usage": "เล่นเกม", "future_upgrade": False},
            {"budget": "35000", "usage": "ทำงานกราฟิก ตัดต่อวิดีโอ", "future_upgrade": False},
            {"budget": "15000", "usage": "พิมพ์งานเอกสารทั่วไป ออฟฟิศ", "future_upgrade": False},
            {"budget": "50000", "usage": "เล่นเกมหนักๆ สตรีมมิ่ง", "future_upgrade": True}, # เผื่ออนาคต
            {"budget": "80000", "usage": "ตัดต่อวิดีโอ 4k เรนเดอร์ 3d", "future_upgrade": True}
        ]

        for case in test_cases:
            result = self.recommender.get_recommendation(
                budget_str=case["budget"],
                usage=case["usage"],
                future_upgrade=case["future_upgrade"]
            )
            
            # ยืนยันว่าการรันฟังก์ชันสำเร็จ
            self.assertEqual(result["status"], "success", f"จัดสเปคไม่สำเร็จสำหรับงบ {case['budget']} ({case['usage']})")
            
            components = result["components"]
            cpu = components.get("cpu")
            motherboard = components.get("motherboard")
            ram = components.get("ram")
            gpu = components.get("gpu")
            psu = components.get("psu")
            case_comp = components.get("case")
            cooler = components.get("cooler")

            # ตรวจสอบว่ามีชิ้นส่วนจำเป็นพื้นฐานครบถ้วน
            self.assertIsNotNone(cpu, "ไม่พบ CPU ในผลลัพธ์")
            self.assertIsNotNone(motherboard, "ไม่พบ Motherboard ในผลลัพธ์")
            self.assertIsNotNone(ram, "ไม่พบ RAM ในผลลัพธ์")
            self.assertIsNotNone(psu, "ไม่พบ PSU ในผลลัพธ์")

            # A. ตรวจสอบ Socket Compatibility (CPU กับ เมนบอร์ดต้อง Socket เดียวกัน)
            cpu_socket = cpu.get("socket")
            mb_socket = motherboard.get("socket")
            self.assertEqual(
                cpu_socket, mb_socket, 
                f"Socket ไม่ตรงกัน: CPU ({cpu['name']}) ใช้ {cpu_socket} แต่ Mainboard ({motherboard['name']}) ใช้ {mb_socket}"
            )

            # B. ตรวจสอบ RAM Type Compatibility (RAM Type ต้องตรงกับที่บอร์ดรองรับ)
            ram_type = ram.get("type")
            mb_ram_support = motherboard.get("ram_type")
            self.assertEqual(
                ram_type, mb_ram_support,
                f"ประเภท RAM ไม่เข้ากัน: RAM คือ {ram_type} แต่ Mainboard รองรับ {mb_ram_support}"
            )

            # C. ตรวจสอบ Case Form Factor Compatibility (ขนาดบอร์ดต้องสามารถติดตั้งในเคสคอมพิวเตอร์ที่คัดสรรได้)
            mb_form_factor = motherboard.get("form_factor")
            case_supported_factors = case_comp.get("form_factor_support", []) if case_comp else []
            if case_comp:
                self.assertIn(
                    mb_form_factor, case_supported_factors,
                    f"เคสไม่รองรับเมนบอร์ด: เมนบอร์ดคือ {mb_form_factor} แต่เคส ({case_comp['name']}) รองรับ {case_supported_factors}"
                )

            # D. ตรวจสอบ PSU Wattage (กำลังไฟของพาวเวอร์ซัพพลายต้องพอกับ CPU + GPU + Buffer 100W)
            cpu_tdp = cpu.get("tdp", 65)
            gpu_power = gpu.get("power_draw", 0) if gpu else 0
            required_wattage = cpu_tdp + gpu_power + 100  # TDP + GPU + 100W buffer สำหรับชิ้นส่วนอื่นๆ
            psu_wattage = psu.get("wattage", 0)
            self.assertGreaterEqual(
                psu_wattage, required_wattage,
                f"วัตต์ของ PSU ไม่เพียงพอ: ความต้องการ {required_wattage}W แต่ PSU จ่ายไฟได้ {psu_wattage}W"
            )

            # E. ตรวจสอบ Cooler Socket Compatibility (พัดลมระบายความร้อนต้องรองรับ CPU Socket)
            if cooler:
                cooler_sockets = cooler.get("socket_support", [])
                self.assertIn(
                    cpu_socket, cooler_sockets,
                    f"พัดลมไม่รองรับ Socket: CPU Socket คือ {cpu_socket} แต่พัดลมรองรับ {cooler_sockets}"
                )

            # F. ตรวจสอบเงื่อนไขข้อบังคับเมื่อจัดแบบเผื่ออัปเกรดในอนาคต (Future Upgrade)
            if case["future_upgrade"]:
                self.assertIn(
                    cpu_socket, ["AM5", "LGA1700"],
                    f"Socket ต่ำเกินไปสำหรับการเผื่ออนาคต: ได้ {cpu_socket}"
                )
                self.assertEqual(
                    ram_type, "DDR5",
                    f"RAM ต้องบังคับเป็น DDR5 สำหรับสเปคเผื่ออนาคต: ได้ {ram_type}"
                )

            print(f"✅ ผ่านการตรวจความเข้ากันได้สำหรับงบ {case['budget']} ({case['usage']}) | "
                  f"CPU Socket: {cpu_socket} | RAM: {ram_type} | PSU: {psu_wattage}W")

    def test_upgrade_advisor(self):
        # 2. ทดสอบตรรกะการวิเคราะห์และอัปเกรดสเปคคอมพิวเตอร์เดิม
        test_specs = [
            {"specs": "i3 gen 4, ram 4gb, hdd 500gb, gtx 750", "usage": "เล่นเกม"},
            {"specs": "ryzen 5 3600, ram 8gb, hdd 1tb, gtx 1050 ti", "usage": "ทำงานกราฟิกและเรนเดอร์"},
            {"specs": "i5 10400f, ram 16gb, ssd 512gb, rtx 3060", "usage": "เล่นเกมหนักๆ"}
        ]

        for case in test_specs:
            result = self.advisor.analyze_upgrade(case["specs"], case["usage"])
            self.assertEqual(result["status"], "success", f"การวิเคราะห์สเปคไม่สำเร็จสำหรับ '{case['specs']}'")
            self.assertIn("text", result)
            self.assertTrue(len(result["text"]) > 0)
            
            # ยืนยันว่าได้รับราคาประเมินรวมงบอัปเกรด
            total_price = result.get("total_price", 0)
            self.assertGreaterEqual(total_price, 0)
            
            print(f"✅ ผ่านการวิเคราะห์อัปเกรดสเปค: '{case['specs']}' | งบอัปเกรดโดยประมาณ: {total_price:,} บาท")

if __name__ == "__main__":
    unittest.main()
