import json
import os

def load_static_card(filename: str) -> dict:
    """
    โหลดไฟล์ JSON จากโฟลเดอร์ templates ไปส่งให้ผู้ใช้โดยตรง
    """
    file_path = os.path.join(os.path.dirname(__file__), "templates", filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_dynamic_card(filename: str, data_dict: dict) -> dict:
    """
    โหลดไฟล์แม่แบบการ์ด แตกข้อมูลแทนค่า Placeholder และแปลงกลับเป็น JSON Dictionary
    """
    file_path = os.path.join(os.path.dirname(__file__), "templates", filename)
    with open(file_path, "r", encoding="utf-8") as f:
        card_content_str = f.read()
    
    # ดำเนินการแทนค่าตัวแปร (เช่น แทนค่า <USAGE> ด้วยคำใช้งานจริง)
    for placeholder, value in data_dict.items():
        target_token = f"<{placeholder.upper()}>"
        card_content_str = card_content_str.replace(target_token, str(value))
        
    return json.loads(card_content_str)

def generate_spec_flex_message(total_price, components, usage, warning=""):
    """
    โหลดเทมเพลตสเปคแนะนำ และเติมรายการอุปกรณ์รวมถึงราคาอัปเกรด
    """
    data_dict = {
        "usage": usage,
        "total_price": f"{total_price:,}"
    }
    
    # 1. โหลดโครงสร้างการ์ดแนะนำสเปคจากไฟล์ JSON
    flex_message = generate_dynamic_card("card_spec_builder.json", data_dict)
    
    # 2. สร้างรายการอุปกรณ์ฮาร์ดแวร์แบบไดนามิก
    body_contents = []
    cat_names = {
        'cpu': 'CPU', 
        'motherboard': 'Mainboard', 
        'ram': 'RAM', 
        'gpu': 'GPU', 
        'storage': 'Storage', 
        'psu': 'PSU', 
        'case': 'Case', 
        'cooler': 'Cooler'
    }
    
    for cat, name in cat_names.items():
        if cat in components and components[cat]:
            part = components[cat]
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": name,
                        "color": "#aaaaaa",
                        "size": "sm",
                        "flex": 2
                    },
                    {
                        "type": "text",
                        "text": f"{part['name']} ({part['price']:,} ฿)",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                        "flex": 5
                    }
                ]
            })

    # แทรกข้อมูลอุปกรณ์แถวที่ 3 (contents[2]) ในส่วน body
    flex_message["contents"]["body"]["contents"][2]["contents"] = body_contents
    
    # 3. แทรกคำแจ้งเตือนกรณีมีเงื่อนไขเตือนงบประมาณ
    if warning:
        flex_message["contents"]["body"]["contents"].extend([
            {
                "type": "separator",
                "margin": "md"
            },
            {
                "type": "text",
                "text": f"⚠️ คำเตือน: {warning}",
                "color": "#D35400",
                "size": "xxs",
                "wrap": True,
                "margin": "md"
            }
        ])
        
    # 4. แทรก Disclaimer ปฏิเสธความรับผิดชอบ
    flex_message["contents"]["body"]["contents"].extend([
        {
            "type": "separator",
            "margin": "md"
        },
        {
            "type": "text",
            "text": "⚠️ หมายเหตุ: ราคาและสเปคคอมพิวเตอร์ที่แนะนำเป็นเพียงแนวทางทั่วไป ไม่สามารถรับประกันประสิทธิภาพการใช้งานจริงและราคาเชิงพาณิชย์ได้ กรุณาตรวจสอบกับผู้จัดจำหน่ายอีกครั้ง",
            "color": "#95A5A6",
            "size": "xxs",
            "wrap": True,
            "margin": "md"
        }
    ])

    return flex_message

def generate_upgrade_flex_message(total_price, recommendations, usage):
    """
    โหลดเทมเพลตวิเคราะห์การอัปเกรดคอมเดิม และเติมชิ้นส่วนแนะนำแบบไดนามิก
    """
    data_dict = {
        "usage": usage,
        "total_price": f"{total_price:,}"
    }
    
    # 1. โหลดโครงสร้างการ์ดแนะนำอัปเกรดจากไฟล์ JSON
    flex_message = generate_dynamic_card("card_upgrade_advisor.json", data_dict)
    
    # 2. ป้อนข้อมูลการวิเคราะห์อุปกรณ์ทีละรายการ
    body_contents = []
    for rec in recommendations:
        clean_rec = rec.replace("**", "")  # ลบเครื่องหมายความหนาเพื่อความสะอาดบน LINE
        body_contents.append({
            "type": "text",
            "text": f"• {clean_rec}",
            "wrap": True,
            "color": "#555555",
            "size": "xs",
            "margin": "xs"
        })
        
    # แทรกข้อมูลคำอัปเกรดแถวที่ 3 (contents[2]) ในส่วน body
    flex_message["contents"]["body"]["contents"][2]["contents"] = body_contents
    
    # 3. แทรก Disclaimer ปฏิเสธความรับผิดชอบ
    flex_message["contents"]["body"]["contents"].extend([
        {
            "type": "separator",
            "margin": "md"
        },
        {
            "type": "text",
            "text": "⚠️ หมายเหตุ: ราคาและสเปคคอมพิวเตอร์ที่แนะนำเป็นเพียงแนวทางทั่วไป ไม่สามารถรับประกันประสิทธิภาพการใช้งานจริงและราคาเชิงพาณิชย์ได้ กรุณาตรวจสอบกับผู้จัดจำหน่ายอีกครั้ง",
            "color": "#95A5A6",
            "size": "xxs",
            "wrap": True,
            "margin": "md"
        }
    ])
    
    return flex_message
