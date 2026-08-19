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
        
        # ลบเว้นวรรคและเครื่องหมายขีดออกทั้งหมดเพื่อรองรับการเขียนแบบต่างๆ (เช่น "i5-4570" -> "i54570")
        specs_normalized = specs_lower.replace(" ", "").replace("-", "")
        usage_normalized = usage_lower.replace(" ", "").replace("-", "")
        
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
        # เพิ่มการ์ดจอระดับเริ่มต้นและตระกูลเก่าที่ควรแนะนำอัปเกรดเมื่อผู้ใช้ต้องการเล่นเกม/ทำงานกราฟิก
        old_gpus = ["1030", "730", "750", "1050", "1060", "1650", "970", "rx570", "rx580", "1050ti", "1650super", "1660", "rx550", "rx560", "gt1030", "gt730"]
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
        # ค้นหา CPU รุ่นเก่าอย่างละเอียดด้วย Regex และ keyword (Gen 9 หรือต่ำกว่า หรือ Ryzen 1000-3000)
        has_old_intel = False
        match_intel = re.search(r'i[3579](\d)\d{3}', specs_normalized)
        if match_intel:
            gen_digit = int(match_intel.group(1))
            if gen_digit <= 9: # Gen 2 ถึง Gen 9
                has_old_intel = True
                
        has_old_cpu = (
            has_old_intel or 
            any(cpu in specs_normalized for cpu in ["i3", "gen2", "gen3", "gen4", "gen5", "gen6", "gen7", "gen8", "gen9", "ryzen3", "ryzen51", "ryzen52", "ryzen53", "ryzen71", "ryzen72", "ryzen73"])
        )
        
        if has_old_cpu:
            upgrades.append("ซีพียู (CPU)")
            cpu_options = self.db.get('cpu', [])
            if cpu_options:
                best_cpu = max(cpu_options, key=lambda x: x['price'])
                recommendations.append(f"**อัปเกรด CPU**: แนะนำ {best_cpu['name']} (อาจต้องเปลี่ยนเมนบอร์ดและแรมร่วมด้วยเพื่อความเข้ากันได้) ({best_cpu['price']:,} บาท)")
                total_price += best_cpu['price']

        # 5. Bottleneck Analysis (วิเคราะห์คอขวดเชิงลึก)
        bottleneck_notes = []
        has_strong_gpu = any(gpu in specs_normalized for gpu in ["3060", "4060", "4070", "4080", "4090", "6600", "7600", "7800"])
        has_modern_cpu = any(cpu in specs_normalized for cpu in ["12400", "13400", "13600", "14900", "5600", "7600", "7700", "7800x3d", "gen12", "gen13", "gen14"])
        has_weak_gpu = any(gpu in specs_normalized for gpu in ["1030", "730", "750", "1050", "rx550", "rx560", "gt1030"])
        
        if has_old_cpu and has_strong_gpu:
            bottleneck_notes.append("⚠️ **วิเคราะห์คอขวด (CPU Bottleneck)**: สเปคของคุณใช้การ์ดจอประสิทธิภาพสูงร่วมกับ CPU รุ่นเก่า ทำให้ CPU ประมวลผลข้อมูลไม่ทันการทำงานของการ์ดจอ (การ์ดจอทำงานได้ไม่เต็ม 100%) แนะนำให้อัปเกรด CPU เป็นอันดับแรกเพื่อดึงพลังการ์ดจอออกมาได้เต็มที่ครับ")
        elif has_modern_cpu and has_weak_gpu:
            bottleneck_notes.append("⚠️ **วิเคราะห์คอขวด (GPU Bottleneck)**: สเปคของคุณมี CPU รุ่นใหม่ที่แรงเพียงพอแล้ว แต่การ์ดจออยู่ในระดับเริ่มต้น (เช่น GT 1030 / GTX 1050) ทำให้การเล่นเกมหรือทำงานกราฟิกติดขัดที่การ์ดจอเป็นหลัก แนะนำอัปเกรดการ์ดจอเป็นรุ่นใหม่กว่านี้ครับ")
        elif "1030" in specs_normalized or "730" in specs_normalized or "gt1030" in specs_normalized:
            bottleneck_notes.append("⚠️ **วิเคราะห์ระดับการ์ดจอ (Entry-level GPU)**: การ์ดจอของคุณ (GT 1030 / GT 730) เป็นรุ่นประหยัดสำหรับการแสดงผลและพิมพ์งานทั่วไป ไม่เหมาะสำหรับการเล่นเกม 3D ยุคใหม่หรือการทำงานตัดต่อกราฟิก แนะนำอัปเกรดเป็นการ์ดจอแยกที่แรงขึ้นค่ะ")

        # If no specific old parts were detected but user wants to upgrade
        if not recommendations:
            return {
                "status": "success",
                "text": f"จากสเปคที่คุณแจ้งมา (\"{current_specs}\") ถือว่ายังใช้งานได้ดีครับ แต่ถ้าต้องการอัปเกรดเพื่อรองรับการทำงานด้าน {usage} ผมแนะนำให้ลองเพิ่ม RAM เป็น 32GB หรือเปลี่ยนการ์ดจอรุ่นใหม่ขึ้นครับ",
                "total_price": 0
            }

        response_text = f"จากการวิเคราะห์สเปคปัจจุบันของคุณ (\"{current_specs}\") และการนำไปใช้งานด้าน {usage} ผมขอแนะนำให้อัปเกรดชิ้นส่วนดังนี้ครับ:\n\n"
        response_text += "\n".join(recommendations)
        
        if bottleneck_notes:
            response_text += "\n\n💡 **การวิเคราะห์คอขวดของระบบ (Bottleneck Analysis)**:\n" + "\n".join(bottleneck_notes)
            
        response_text += f"\n\n**งบประมาณโดยรวมในการอัปเกรด**: ประมาณ {total_price:,} บาทครับ"
        response_text += f"\n\n⚠️ **หมายเหตุ**: ราคาและสเปคคอมพิวเตอร์ที่แนะนำเป็นเพียงแนวทางทั่วไป ไม่สามารถรับประกันประสิทธิภาพการใช้งานจริงและราคาเชิงพาณิชย์ได้ กรุณาตรวจสอบกับผู้จัดจำหน่ายอีกครั้ง"

        return {
            "status": "success",
            "text": response_text,
            "total_price": total_price,
            "recommendations": recommendations
        }
