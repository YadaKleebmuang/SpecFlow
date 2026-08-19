import json
import os
import re

class SpecRecommender:
    def __init__(self):
        # Load hardware_db.json
        db_path = os.path.join(os.path.dirname(__file__), 'hardware_db.json')
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
        except Exception as e:
            print(f"Error loading hardware DB: {e}")
            self.db = {}

    def _parse_budget(self, budget_str: str) -> int:
        if not budget_str:
            return 0
            
        # ลบช่องว่างออกเพื่อการเปรียบเทียบคำภาษาไทยได้ง่ายขึ้น
        budget_str_clean = budget_str.replace(" ", "")
        
        # ค้นหาตัวเลขในข้อความงบประมาณก่อน
        digits = re.sub(r'[^\d]', '', budget_str_clean)
        if digits:
            return int(digits)
            
        # หากไม่มีตัวเลข ให้แปลความหมายคำพูดเชิงระดับงบประมาณ (ขอบเขต 1.4.1.3)
        low_keywords = ['น้อย', 'ต่ำ', 'ประหยัด', 'เริ่มต้น', 'ไม่แพง', 'ถูก']
        mid_keywords = ['ปานกลาง', 'กลาง', 'พอดี', 'ทั่วไป', 'กลางๆ']
        high_keywords = ['สูง', 'เยอะ', 'แรง', 'จัดเต็ม', 'แพง', 'ไม่อั้น', 'สุด', 'แพงๆ']
        
        if any(w in budget_str_clean for w in low_keywords):
            return 15000  # กำหนดงบประมาณระดับต่ำเริ่มต้นที่ 15,000 บาท
        if any(w in budget_str_clean for w in mid_keywords):
            return 30000  # กำหนดงบประมาณระดับกลางเริ่มต้นที่ 30,000 บาท
        if any(w in budget_str_clean for w in high_keywords):
            return 60000  # กำหนดงบประมาณระดับสูงเริ่มต้นที่ 60,000 บาท
            
        return 0

    def _determine_usage_type(self, usage: str) -> str:
        usage = usage.lower()
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
        
        if any(word in usage for word in editing_keywords):
            return 'editing'
        if any(word in usage for word in office_keywords):
            return 'office'
        return 'gaming' # Default

    def get_recommendation(self, budget_str: str, usage: str, future_upgrade: bool = False) -> dict:
        if not budget_str or not usage:
            return {"status": "error", "text": "ขออภัยครับ ข้อมูลงบประมาณหรือการใช้งานไม่ครบถ้วน ผมจึงยังไม่สามารถจัดสเปคให้ได้ครับ"}
            
        budget = self._parse_budget(budget_str)
        if budget < 10000:
            return {"status": "error", "text": f"งบประมาณ {budget:,} บาท อาจจะน้อยเกินไปสำหรับการประกอบคอมพิวเตอร์ครบชุดครับ ลองเพิ่มงบเป็นสัก 15,000 - 20,000 บาทขึ้นไปดูไหมครับ?"}

        usage_type = self._determine_usage_type(usage)
        
        # ตรวจสอบความต้องการชิปกราฟิกในตัว (Integrated GPU) สำหรับงบประมาณระดับประหยัดต่ำกว่า 16,000 บาท
        use_integrated = budget < 16000
        
        # Layer 1: Budget Allocation
        # แบ่งงบประมาณหลัก (Core Components) และงบส่วนอื่น (Secondary Components)
        core_budget = budget * 0.75
        other_budget = budget * 0.25
        
        if use_integrated:
            # งบประหยัดมาก: ตัดค่าการ์ดจอแยกออกเป็น 0% เพื่อเอาไปลงกับ CPU (มีชิปจอในตัว), RAM, และ Storage แทน
            alloc = {'gpu': 0.0, 'cpu': 0.45, 'ram': 0.25, 'storage': 0.30}
        elif usage_type == 'gaming':
            alloc = {'gpu': 0.40, 'cpu': 0.30, 'ram': 0.15, 'storage': 0.15}
        elif usage_type == 'editing':
            alloc = {'gpu': 0.30, 'cpu': 0.35, 'ram': 0.20, 'storage': 0.15}
        else: # office
            alloc = {'gpu': 0.20, 'cpu': 0.35, 'ram': 0.20, 'storage': 0.25}
            
        budgets = {
            'gpu': core_budget * alloc['gpu'],
            'cpu': core_budget * alloc['cpu'],
            'ram': core_budget * alloc['ram'],
            'storage': core_budget * alloc['storage'],
            'motherboard': other_budget * 0.40, # 10% of total
            'psu': other_budget * 0.25,         # 6.25% of total
            'case': other_budget * 0.20,        # 5% of total
            'cooler': other_budget * 0.15       # 3.75% of total
        }

        # Helper: หาชิ้นส่วนที่ดีที่สุด(ราคาใกล้เคียงงบที่สุด) โดยอิงตามเงื่อนไข (Filter)
        def get_best_part(category, max_price, filter_func=lambda x: True):
            if category not in self.db:
                return None
            valid_parts = [p for p in self.db[category] if p['price'] <= max_price and filter_func(p)]
            # ถ้างบไม่พอ ให้หยิบตัวถูกสุดที่รองรับ เพื่อให้จัดสเปคจนจบได้
            if not valid_parts:
                valid_parts = [p for p in self.db[category] if filter_func(p)]
                if not valid_parts:
                    return None
                return min(valid_parts, key=lambda x: x['price'])
            return max(valid_parts, key=lambda x: x['price'])

        # Layer 2: Rule-based Filtering & Compatibility
        selected = {}
        
        # 1. CPU
        def cpu_filter(x):
            if future_upgrade:
                # Force newer sockets (AM5 or LGA1700)
                if x.get('socket') not in ['AM5', 'LGA1700']:
                    return False
            if use_integrated:
                # Force CPUs with integrated graphics
                if not x.get('integrated_graphics'):
                    return False
            return True
            
        selected['cpu'] = get_best_part('cpu', budgets['cpu'], cpu_filter)
        if not selected['cpu']:
            return {"status": "error", "text": "ไม่พบ CPU ที่เหมาะสมในฐานข้อมูลครับ"}
            
        # 2. Motherboard (filter socket)
        cpu_socket = selected['cpu'].get('socket')
        def mb_filter(x):
            if x.get('socket') != cpu_socket:
                return False
            if future_upgrade:
                # Force DDR5 for better upgradability if user wants future-proof
                if x.get('ram_type') != 'DDR5':
                    return False
            return True
            
        selected['motherboard'] = get_best_part('motherboard', budgets['motherboard'], mb_filter)
        if not selected['motherboard']:
            return {"status": "error", "text": "ไม่พบ Motherboard ที่เข้ากันได้กับ CPU ในระบบครับ"}
            
        # 3. RAM (filter RAM type)
        mb_ram_type = selected['motherboard'].get('ram_type')
        selected['ram'] = get_best_part('ram', budgets['ram'], lambda x: x.get('type') == mb_ram_type)
        if not selected['ram']:
            return {"status": "error", "text": "ไม่พบ RAM ที่เข้ากันได้กับ Motherboard ในระบบครับ"}
            
        # 4. GPU
        if use_integrated:
            selected['gpu'] = None
        else:
            selected['gpu'] = get_best_part('gpu', budgets['gpu'])
        
        # 5. Storage
        selected['storage'] = get_best_part('storage', budgets['storage'])
        
        # 6. Case (filter compatibility with motherboard form factor)
        mb_form_factor = selected['motherboard'].get('form_factor')
        selected['case'] = get_best_part('case', budgets['case'], lambda x: mb_form_factor in x.get('form_factor_support', []))
        
        # 7. PSU (filter PSU wattage)
        cpu_tdp = selected['cpu'].get('tdp', 65)
        gpu_power = selected['gpu'].get('power_draw', 0) if selected.get('gpu') else 0
        total_tdp = cpu_tdp + gpu_power + 100 # Buffer +100W for MB, RAM, drives, fans
        selected['psu'] = get_best_part('psu', budgets['psu'], lambda x: x.get('wattage', 0) >= total_tdp)
        
        # 8. Cooler (filter compatibility with socket)
        selected['cooler'] = get_best_part('cooler', budgets['cooler'], lambda x: cpu_socket in x.get('socket_support', []))

        # Calculate final price
        total_price = sum(part['price'] for part in selected.values() if part)
        
        # Build response
        response = f"จากงบประมาณ {budget:,} บาท และเน้นการใช้งาน {usage}\n"
        if use_integrated:
            response += f"*(ระบบเลือกใช้ CPU ที่มีชิปประมวลผลกราฟิกในตัว (Integrated GPU) เพื่อประหยัดงบและไม่ใช้การ์ดจอแยก)*\n"
        response += f"ผมได้จัดสรรงบและคัดกรองความเข้ากันได้ของอุปกรณ์ (Layer 1 & 2) ให้เรียบร้อยครับ:\n\n"
        response += f"💻 **สเปคที่แนะนำ** (ราคารวมประมาณ {total_price:,} บาท):\n"
        
        cat_names = {'cpu': 'CPU', 'motherboard': 'Mainboard', 'ram': 'RAM', 'gpu': 'GPU', 'storage': 'Storage', 'psu': 'PSU', 'case': 'Case', 'cooler': 'Cooler'}
        for cat, name in cat_names.items():
            if selected.get(cat):
                part = selected[cat]
                response += f"- **{name}**: {part['name']} ({part['price']:,} บาท)\n"
                
        response += "\n(หมายเหตุ: การจัดสเปคนี้ใช้หลักการคำนวณงบประมาณและเช็ค Socket/Wattage อัตโนมัติแล้วครับ)"
        
        warning = ""
        if total_price > budget * 1.1:
            warning = "สเปคนี้มีราคาเกินงบไปเล็กน้อย เนื่องจากอุปกรณ์ในฐานข้อมูลมีจำกัดและต้องเลือกตัวที่ใช้งานร่วมกันได้ครับ"
            response += f"\n\n⚠️ **คำเตือน**: {warning}"
            
        response += "\n\n⚠️ **หมายเหตุ**: ราคาและสเปคคอมพิวเตอร์ที่แนะนำเป็นเพียงแนวทางทั่วไป ไม่สามารถรับประกันประสิทธิภาพการใช้งานจริงและราคาเชิงพาณิชย์ได้ กรุณาตรวจสอบกับผู้จัดจำหน่ายอีกครั้ง"

        return {
            "status": "success",
            "text": response,
            "components": selected,
            "total_price": total_price,
            "warning": warning
        }
