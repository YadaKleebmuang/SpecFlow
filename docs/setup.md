# คู่มือการติดตั้งและเปิดใช้งานระบบ SpecFlow Chatbot 🚀

คู่มือนี้จะอธิบายขั้นตอนการเปิดใช้งานระบบทั้งหมด ตั้งแต่การเปิดใช้งาน Virtual Environment (venv) ไปจนถึงการเชื่อมต่อกับแอปพลิเคชัน LINE เพื่อทดสอบใช้งานจริง

---

## 📂 ขั้นตอนที่ 0: การเข้าสู่โฟลเดอร์โครงการและการ Activate venv

ทุกครั้งที่จะทำงานกับแชทบอท Rasa ให้เปิด **Command Prompt (CMD)** หรือ **PowerShell** ใน Windows ขึ้นมา แล้วทำตามขั้นตอนต่อไปนี้:

1. **เข้าสู่โฟลเดอร์โครงการ:**
   ```bash
   cd C:\Users\yadak\Desktop\SpecFlow
   ```
2. **เปิดใช้งาน Virtual Environment (Activate venv):**
   * **สำหรับ Command Prompt (CMD):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   * **สำหรับ PowerShell:**
     ```powershell
     .\venv\Scripts\activate.ps1
     ```
   *(เมื่อสำเร็จ จะมีข้อความขึ้นต้นบรรทัดคำสั่งเป็น `(venv)` เสมอ เพื่อยืนยันว่าใช้ไลบรารีในระบบถูกต้องแล้ว)*

---

## 🛠️ ขั้นตอนที่ 1: การเปิดใช้งานระบบ (ต้องเปิดพร้อมกัน 3 หน้าต่าง)

ให้เปิด Command Prompt หรือ PowerShell แยกกัน **3 หน้าต่าง (Terminal)** และทุกหน้าต่างต้องทำการ **Activate venv** ก่อนรันคำสั่งด้านล่างนี้ครับ:

### หน้าต่างที่ 1: เปิด Action Server (ระบบประมวลผลจัดสเปค)
ใช้รัน Custom Action และโมเดลวิเคราะห์จัดสเปคคอมพิวเตอร์
```bash
# 1. เข้าไปที่โฟลเดอร์บอท
cd app/rasa

# 2. รัน Action Server
rasa run actions
```
*เมื่อทำงานสำเร็จ จะแสดงข้อความ: `Action endpoint is up and running on http://localhost:5055`*

---

### หน้าต่างที่ 2: เปิด Ngrok (สะพานเชื่อม LINE เข้าเครื่องเรา)
ทำหน้าที่ส่งข้อมูลจากแอปพลิเคชัน LINE ในมือถือลงมาที่พอร์ตของ Rasa ในคอมพิวเตอร์ของคุณ
```bash
# รันช่องทางเชื่อมต่อที่พอร์ต 5005 (พอร์ตหลักของ Rasa)
ngrok http 5005
```
1. เมื่อ Ngrok ทำงาน ให้มองหาบรรทัดที่เขียนว่า **Forwarding**
2. คัดลอกลิงก์ที่ขึ้นต้นด้วย `https://` (เช่น `https://abcd-1234.ngrok-free.app`)
3. ไปที่เว็บ [LINE Developers Console](https://developers.line.biz/) -> เลือกบอทของคุณ -> แท็บ **Messaging API**
4. แก้ไขช่อง **Webhook URL** โดยนำลิงก์ที่คัดลอกมาวาง แล้วต่อท้ายด้วย `/webhooks/line/webhook` 
   *ตัวอย่าง:* `https://abcd-1234.ngrok-free.app/webhooks/line/webhook`
5. กดปุ่ม **Verify** (ให้ขึ้นผลลัพธ์เป็น Success) และเปิดสวิตช์ **Use webhook** ให้เป็นสีเขียว 🟢

---

### หน้าต่างที่ 3: เปิด Rasa Server (สมองแชทบอทหลัก)
ทำหน้าที่ทำความเข้าใจภาษา (NLU) และโต้ตอบกับ LINE
```bash
# 1. เข้าไปที่โฟลเดอร์บอท
cd app/rasa

# 2. รัน Rasa Server ร่วมกับ LINE Connector
rasa run --enable-api --cors "*"
```
*เมื่อรันเสร็จสิ้น บอทพร้อมทำงานและรอรับข้อความจาก LINE ในมือถือของคุณทันทีครับ!*

---

## 🧪 การประเมินผลระบบ (NLU Evaluation)

หากต้องการดึงค่า Accuracy, Precision, Recall, และ F1-Score ไปใส่ในรายงานบทที่ 4 ให้เปิดหน้าต่าง Command Prompt ที่ Activate venv แล้วใช้คำสั่งนี้:
```bash
cd app/rasa
rasa test nlu
```
*เมื่อรันเสร็จแล้ว จะได้ผลลัพธ์รายงานความแม่นยำและกราฟ Confusion Matrix เก็บอยู่ในโฟลเดอร์ `app/rasa/results` ทันทีครับ*