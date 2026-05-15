def generate_spec_flex_message(total_price, components, usage):
    """
    Generate a LINE Flex Message payload for PC recommendations.
    components is a dict mapping category name to the part dictionary.
    """
    
    # We build the body contents dynamically based on the selected components
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

    # Create the full Flex Message payload
    flex_message = {
        "type": "flex",
        "altText": "SpecFlow: สเปคคอมพิวเตอร์ที่แนะนำ",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#2C3E50",
                "contents": [
                    {
                        "type": "text",
                        "text": "SpecFlow PC Build",
                        "color": "#FFFFFF",
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "text",
                        "text": f"สำหรับ: {usage}",
                        "color": "#1ABC9C",
                        "size": "sm"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "อุปกรณ์ที่แนะนำ",
                        "weight": "bold",
                        "size": "md",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xxl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": body_contents
                    },
                    {
                        "type": "separator",
                        "margin": "xxl"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "ราคารวมโดยประมาณ",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": f"฿{total_price:,}",
                                "color": "#E74C3C",
                                "size": "md",
                                "align": "end",
                                "weight": "bold"
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "color": "#3498DB",
                        "action": {
                            "type": "message",
                            "label": "ขอคำแนะนำอัปเกรด",
                            "text": "อัปเกรดคอม"
                        }
                    }
                ],
                "flex": 0
            }
        }
    }
    return flex_message
