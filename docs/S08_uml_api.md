# S08: การออกแบบกระบวนการ, UML, และข้อกำหนด API (Process, UML, and API Design Specification)

---

## 1. แผนภาพกระบวนการทำงาน (Activity Diagram)

แผนภาพกิจกรรมการประมวลผลคำขอจัดสเปคคอมพิวเตอร์ผ่านทาง LINE Chatbot ตั้งแต่รับอินพุต ตรวจวิเคราะห์ จนถึงส่งการ์ดข้อมูลคืนกลับ แสดงในรูปแบบ Mermaid Activity Diagram:

```mermaid
stateDiagram-v2
    [*] --> รับข้อความแชทจากLINE
    รับข้อความแชทจากLINE --> ตรวจสอบความถูกต้องลายเซ็น
    
    state check_signature <<choice>>
    ตรวจสอบความถูกต้องลายเซ็น --> check_signature
    check_signature --> [*] : ลายเซ็นไม่ถูกต้อง (HTTP 400)
    check_signature --> ล้างข้อความและลบหางเสียง : ลายเซ็นถูกต้อง
    
    ล้างข้อความและลบหางเสียง --> ตัดคำภาษาไทยและแมปสะกดคำผิด
    ตัดคำภาษาไทยและแมปสะกดคำผิด --> ส่งข้อความให้RasaNLU
    
    state check_slots <<choice>>
    ส่งข้อความให้RasaNLU --> เติมข้อมูลลงแบบฟอร์ม
    เติมข้อมูลลงแบบฟอร์ม --> check_slots
    
    check_slots --> ส่งคำถามและปุ่มตอบด่วนกลับหาLINE : ช่องข้อมูล (Slots) ไม่ครบ
    ส่งคำถามและปุ่มตอบด่วนกลับหาLINE --> รับข้อความแชทจากLINE
    
    check_slots --> ส่งข้อมูลไปที่ActionServer : ข้อมูล Slots ครบถ้วน
    
    state check_budget <<choice>>
    ส่งข้อมูลไปที่ActionServer --> แยกแยะประเภทงานและงบ
    แยกแยะประเภทงานและงบ --> check_budget
    
    check_budget --> ส่งการ์ดแจ้งเตือนงบต่ำ : งบ < 10000 บาท
    check_budget --> จับคู่อุปกรณ์และเช็คความเข้ากันได้ : งบ >= 10000 บาท
    
    จับคู่อุปกรณ์และเช็คความเข้ากันได้ --> บันทึกประวัติสืบค้นลงSQLite
    บันทึกประวัติสืบค้นลงSQLite --> ประกอบการ์ดLINEFlexMessage
    ส่งการ์ดแจ้งเตือนงบต่ำ --> ประกอบการ์ดLINEFlexMessage
    ประกอบการ์ดLINEFlexMessage --> ส่งการ์ดFlexMessageกลับหาผู้ใช้
    ส่งการ์ดFlexMessageกลับหาผู้ใช้ --> [*]
```

---

## 2. แผนภาพลำดับขั้นตอนการทำงาน (Sequence Diagram)

ลำดับการเรียกใช้งานฟังก์ชันข้ามออบเจกต์ (Objects Interaction) ในโปรเซสประมวลผลการจัดสเปคคอมพิวเตอร์:

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User Client
    participant LineWebhook as ⚙️ LineInput Channel
    participant Preprocessor as 🧠 ThaiPreprocessor
    participant RasaEngine as 🤖 Rasa Core & NLU
    participant ActionServer as 🎨 Rasa SDK Action
    participant Recommender as ⚙️ SpecRecommender
    participant DB as 📊 SQLite / JSON DB
    
    User->>LineWebhook: ส่งคำขอแชท "จัดสเปคคอมเล่นเกม 25000"
    Note over LineWebhook: ตรวจสอบ HTTP X-Line-Signature
    LineWebhook->>Preprocessor: preprocess_thai_text("จัดสเปคคอมเล่นเกม 25000")
    Preprocessor->>Preprocessor: แก้คำผิด + ลบคำสร้อย + ตัดคำ
    Preprocessor-->>LineWebhook: คืนคำตัด "จัด สเปค คอม เล่น เกม 25000"
    LineWebhook->>RasaEngine: ส่งข้อความที่แปลงเพื่อประมวลต่อ
    RasaEngine->>RasaEngine: ทำ Intent Classification & Entity Extraction
    RasaEngine->>ActionServer: HTTP POST /webhook (Slots: budget:25000, usage:gaming)
    ActionServer->>Recommender: get_recommendation("25000", "gaming")
    Recommender->>DB: โหลดคลังสินค้า (hardware_db.json)
    DB-->>Recommender: ส่งข้อมูลอุปกรณ์
    Recommender->>Recommender: Layer 1: แบ่งงบ | Layer 2: ตรวจความเข้ากันได้
    Recommender-->>ActionServer: คืนรายการชิ้นส่วนที่ผ่านการกรอง (components)
    ActionServer->>DB: บันทึกข้อมูลลง SQLite (analytics.db)
    ActionServer->>ActionServer: สร้าง Flex Message JSON Payload ด้วย flex.py
    ActionServer-->>RasaEngine: ส่งข้อความโต้ตอบกลับ
    RasaEngine->>LineWebhook: เรียกช่องส่งข้อมูล (LineOutput Channel)
    LineWebhook-->>User: Push Flex Message การ์ดจัดสเปคสวยงาม
```

---

## 3. แผนภาพแสดงโครงสร้างคลาส (Class Diagram)

สัญกรณ์แสดงความสัมพันธ์ โครงสร้างตัวแปร และฟังก์ชันภายในซอร์สโค้ดภาษา Python ของโปรเจกต์ SpecFlow:

```mermaid
classDiagram
    class Action {
        <<Rasa SDK Base Class>>
        +name() String*
        +run(dispatcher, tracker, domain) List*
    }

    class ActionRecommendPC {
        +name() String
        +run(dispatcher, tracker, domain) List
        -get_usage_type_db(usage) String
        -log_search(user_id, usage, budget, total_price)
    }

    class ActionRecommendUpgrade {
        +name() String
        +run(dispatcher, tracker, domain) List
    }

    class ActionFAQ {
        +name() String
        +run(dispatcher, tracker, domain) List
    }

    class ThaiPreprocessor {
        +typo_dict: Dictionary
        +clean_text(text) String
        +remove_stopwords(tokens) List
        +preprocess(text) String
    }

    class SpecRecommender {
        +db: Dictionary
        +get_recommendation(budget_str, usage, future_upgrade) Dictionary
        -_parse_budget(budget_str) Integer
        -_determine_usage_type(usage) String
    }

    class UpgradeAdvisor {
        +db: Dictionary
        +analyze_upgrade(current_specs, usage) Dictionary
    }

    class ResponseBuilder {
        +DB_PATH: String
        +generate_analytics_report() Dictionary
    }

    Action <|-- ActionRecommendPC
    Action <|-- ActionRecommendUpgrade
    Action <|-- ActionFAQ

    ActionRecommendPC --> SpecRecommender : เรียกใช้งานคำนวณสเปค
    ActionRecommendUpgrade --> UpgradeAdvisor : เรียกวิเคราะห์อัปเกรด
    
    ActionRecommendPC ..> ResponseBuilder : บันทึกข้อมูลลง SQLite
    ActionRecommendUpgrade ..> ResponseBuilder : บันทึกข้อมูลลง SQLite
```

---

## 4. ข้อกำหนดส่วนติดต่อการใช้งานโปรแกรม (API Specifications)

### 4.1. ช่องทางส่งข้อมูลแชท: LINE Webhook Gateway
* **Endpoint (URL):** `/webhooks/line/webhook`
* **โปรโตคอลการเข้าถึง:** HTTP POST (HTTPS เท่านั้นบนระบบจำหน่ายจริง)
* **รูปแบบการยืนยันตัวตน:** ตรวจสอบลายเซ็นผ่าน HTTP Header `X-Line-Signature`

#### ตัวอย่างโครงสร้างข้อมูลร้องขอ (Request Body Schema)
```json
{
  "destination": "U1234567890abcdef1234567890abcde",
  "events": [
    {
      "type": "message",
      "message": {
        "type": "text",
        "id": "14275892",
        "text": "จัดสเปคคอมงบ 30000 เล่นเกม"
      },
      "timestamp": 1626901857321,
      "source": {
        "type": "user",
        "userId": "U4a8a9b2c3d4e5f6g7h8i9j0k1l2m3n4"
      },
      "replyToken": "nH7bEs16a2IGJydAxZ71"
    }
  ]
}
```
#### โครงสร้างข้อมูลตอบรับ (Response)
* **HTTP Status Code:** `200 OK` (ยืนยันรับข้อความเสร็จสิ้นเพื่อไม่ให้ LINE ยิงคำสั่งซ้ำ)
* **ข้อความตอบรับ:** `OK` (Text)

---

### 4.2. ช่องทางแลกเปลี่ยนคำนวณ: Rasa Custom Action Webhook
* **Endpoint (URL):** `http://127.0.0.1:5055/webhook`
* **โปรโตคอลการเข้าถึง:** HTTP POST
* **รูปแบบข้อมูลร้องขอ:** Rasa SDK Request Payload (Tracker State JSON)

#### ตัวอย่างข้อมูลร้องขอ (Request Body Schema)
```json
{
  "next_action": "action_recommend_pc",
  "sender_id": "U4a8a9b2c3d4e5f6g7h8i9j0k1l2m3n4",
  "tracker": {
    "sender_id": "U4a8a9b2c3d4e5f6g7h8i9j0k1l2m3n4",
    "slots": {
      "budget": "30000",
      "usage": "เล่นเกม",
      "future_upgrade": true
    },
    "latest_message": {
      "intent": {
        "name": "build_pc",
        "confidence": 0.96
      }
    }
  }
}
```

#### ตัวอย่างข้อมูลตอบรับเมื่อประมวลผลเสร็จ (Response Body Schema)
คืนค่ารายการผลลัพธ์เป็นอาร์เรย์ของคำสั่งข้อความหรือบล็อก Custom Flex Message JSON กลับไปให้ Rasa Core:

```json
{
  "responses": [
    {
      "custom": {
        "type": "flex",
        "altText": "แนะนำสเปคคอมพิวเตอร์งบ 30,000 บาท",
        "contents": {
          "type": "bubble",
          "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "แนะนำสเปคคอมสำหรับ เล่นเกม",
                "weight": "bold",
                "size": "lg"
              },
              {
                "type": "separator"
              },
              {
                "type": "text",
                "text": "CPU: Intel Core i5-12400F (4,600 ฿)"
              }
            ]
          }
        }
      }
    }
  ],
  "events": [
    {"event": "slot", "value": null, "name": "budget"},
    {"event": "slot", "value": null, "name": "usage"},
    {"event": "slot", "value": null, "name": "future_upgrade"}
  ]
}
```
*(หมายเหตุ: ระบบจะทำการ Reset คืนค่า Slots ทุกตัวให้เป็น Null ในบล็อก `events` ทันทีหลังจัดสเปคเสร็จ เพื่อเตรียมความพร้อมสำหรับผู้ใช้ส่งคำสั่งจัดคอมรอบใหม่ในแชทเดิม)*
