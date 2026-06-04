import json
import os
import re

class UpgradeAdvisor:
    def __init__(self):
        # Load hardware_db.json
        db_path = os.path.join(os.path.dirname(__file__), 'hardware_db.json')
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
        except Exception as e:
            print(f"Error loading hardware DB: {e}")
            self.db = {}

    def analyze_upgrade(self, current_specs: str, usage: str) -> dict:
        if not current_specs:
            return {"status": "error", "text": "ขออภัยครับ ไม่พบข้อมูลสเปคคอมพิวเตอร์ปัจจุบันของคุณ รบกวนบอกสเปคคร่าวๆ อีกครั้งได้ไหมครับ?"}

        specs_lower = current_specs.lower()
        usage_lower = usage.lower() if usage else "gaming"
        
        # ลบเว้นวรรคออกทั้งหมดเพื่อแก้ไขปัญหาการตัดคำภาษาไทยที่อาจใส่เว้นวรรคระหว่างอักษรและตัวเลข (เช่น "i 3", "4 gb")
        specs_normalized = specs_lower.replace(" ", "")
        usage_normalized = usage_lower.replace(" ", "")
        
        upgrades = []
        recommendations = []
        total_price = 0

        # 1. Check RAM
        if "4gb" in specs_normalized or "8gb" in specs_normalized or "ram4" in specs_normalized or "ram8" in specs_normalized:
            upgrades.append("RAM")
            ram_options = self.db.get('ram', [])
            if ram_options:
                best_ram = max(ram_options, key=lambda x: x['price']) # Or filter by usage
                recommendations.append(f"**เพิ่ม RAM**: แนะนำให้อัปเกรดเป็น {best_ram['name']} เพื่อการใช้งานที่ลื่นไหลขึ้น ({best_ram['price']:,} บาท)")
                total_price += best_ram['price']

        # 2. Check Storage
        if "hdd" in specs_normalized or "harddisk" in specs_normalized or "ฮาร์ดดิสก์" in specs_normalized:
            upgrades.append("Storage (SSD)")
            storage_options = self.db.get('storage', [])
            if storage_options:
                best_ssd = storage_options[0]
                recommendations.append(f"**เปลี่ยนไปใช้ SSD**: แนะนำ {best_ssd['name']} จะช่วยให้เปิดเครื่องและโหลดข้อมูลไวขึ้นมาก ({best_ssd['price']:,} บาท)")
                total_price += best_ssd['price']

        # 3. Check GPU
        old_gpus = ["1050", "1060", "1650", "970", "rx570", "rx580", "1050ti", "1650super", "1660"]
        needs_gpu_upgrade = any(gpu in specs_normalized for gpu in old_gpus)
        if needs_gpu_upgrade or "เล่นเกมหนัก" in usage_normalized or "ตัดต่อ" in usage_normalized:
            # If user has an old GPU or needs heavy usage, recommend a new one
            if needs_gpu_upgrade or ("gpu" not in specs_normalized and "การ์ดจอ" not in specs_normalized):
                upgrades.append("การ์ดจอ (GPU)")
                gpu_options = self.db.get('gpu', [])
                if gpu_options:
                    best_gpu = max(gpu_options, key=lambda x: x['price'])
                    recommendations.append(f"**อัปเกรดการ์ดจอ**: แนะนำ {best_gpu['name']} เพื่อรองรับการประมวลผลกราฟิกยุคใหม่ ({best_gpu['price']:,} บาท)")
                    total_price += best_gpu['price']

        # 4. Check CPU
        old_cpus = ["i3", "gen4", "gen6", "gen7", "gen8", "gen9", "gen10", "ryzen3"]
        if any(cpu in specs_normalized for cpu in old_cpus):
            upgrades.append("ซีพียู (CPU)")
            cpu_options = self.db.get('cpu', [])
            if cpu_options:
                best_cpu = max(cpu_options, key=lambda x: x['price'])
                recommendations.append(f"**อัปเกรด CPU**: แนะนำ {best_cpu['name']} (อาจต้องเปลี่ยนเมนบอร์ดร่วมด้วย) ({best_cpu['price']:,} บาท)")
                total_price += best_cpu['price']

        # If no specific old parts were detected but user wants to upgrade
        if not recommendations:
            return {
                "status": "success",
                "text": f"จากสเปคที่คุณแจ้งมา (\"{current_specs}\") ถือว่ายังใช้งานได้ดีครับ แต่ถ้าต้องการอัปเกรดเพื่อรองรับการทำงานด้าน {usage} ผมแนะนำให้ลองเพิ่ม RAM เป็น 32GB หรือเปลี่ยนการ์ดจอรุ่นใหม่ขึ้นครับ",
                "total_price": 0
            }

        response_text = f"จากการวิเคราะห์สเปคปัจจุบันของคุณ (\"{current_specs}\") และการนำไปใช้งานด้าน {usage} ผมขอแนะนำให้อัปเกรดชิ้นส่วนดังนี้ครับ:\n\n"
        response_text += "\n".join(recommendations)
        response_text += f"\n\n**งบประมาณโดยรวมในการอัปเกรด**: ประมาณ {total_price:,} บาทครับ"
        response_text += f"\n\n⚠️ **หมายเหตุ**: ราคาและสเปคคอมพิวเตอร์ที่แนะนำเป็นเพียงแนวทางทั่วไป ไม่สามารถรับประกันประสิทธิภาพการใช้งานจริงและราคาเชิงพาณิชย์ได้ กรุณาตรวจสอบกับผู้จัดจำหน่ายอีกครั้ง"

        return {
            "status": "success",
            "text": response_text,
            "total_price": total_price,
            "recommendations": recommendations
        }
