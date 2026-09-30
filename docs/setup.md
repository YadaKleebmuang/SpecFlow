# 🛠️ คู่มือติดตั้ง SpecFlow บน macOS / Linux

คู่มือนี้ใช้เตรียมเครื่อง macOS / Linux หลัง clone repository ตั้งแต่ติดตั้ง Python และไลบรารี ตั้งค่า LINE เปิดบอท ไปจนถึงดูรายงานฝั่ง Admin

สำหรับ Windows ให้อ่าน [คู่มือติดตั้งบน Windows](setup-windows.md) ซึ่งรวมคำสั่งสำหรับ Command Prompt ไว้ในไฟล์เดียว

> [!IMPORTANT]
> เครื่องใหม่ต้องสร้าง virtual environment และไฟล์ `.env` เอง เพราะสองส่วนนี้ไม่ติดไปกับ Git หากใช้ WSL ให้ติดตั้ง Python, environment และ `cloudflared` ภายใน WSL แล้วทำตามคู่มือนี้

## 📥 ก่อนเริ่ม: Clone และเตรียมเครื่อง

ติดตั้ง Git และ Python 3.10 สำหรับคำสั่งในคู่มือนี้ จากนั้นแทนที่ `YOUR_REPOSITORY_URL` ด้วย URL ของ repository ที่ต้องการ:

```bash
git clone YOUR_REPOSITORY_URL SpecFlow
cd SpecFlow
```

คำสั่งทั้งหมดเริ่มจากโฟลเดอร์หลัก `SpecFlow` เว้นแต่ระบุให้เปลี่ยนโฟลเดอร์ เครื่องต้องเชื่อมต่ออินเทอร์เน็ตสำหรับติดตั้งไลบรารีและเชื่อมต่อ LINE

| ส่วนที่ต้องเตรียม | ใช้เมื่อใด |
| :--- | :--- |
| Python และ virtual environment | รันบอทและรายงาน Admin |
| LINE Official Account ที่เปิด Messaging API พร้อม Channel secret และ Channel access token | รับส่งข้อความผ่าน LINE |
| `cloudflared` | เปิด HTTPS tunnel ให้ LINE เข้าถึงบอทในเครื่อง |
| พอร์ต 5005 และ 5055 ที่ว่าง | Rasa Server และ Action Server |

หากต้องการดูเฉพาะรายงาน Admin ใช้ Python และข้ามไปขั้นตอนที่ 6 ได้เลย สคริปต์รายงานใช้เฉพาะไลบรารีมาตรฐานของ Python

---

## ⚙️ ขั้นตอนที่ 1: การเตรียมสภาพแวดล้อมจำลอง (Environment Setup)

โมเดลที่แนบมาเทรนด้วย **Python 3.9.6 และ Rasa 3.6.21** ส่วนคู่มือนี้ใช้คำสั่งสร้าง environment ด้วย **Python 3.10** ซึ่งอยู่ในช่วงที่ Rasa 3.6.21 รองรับ (`>=3.8,<3.11`) ยังไม่ได้ทดสอบติดตั้งใหม่ครบทุกระบบปฏิบัติการ ดูข้อกำหนดเพิ่มเติมใน [คู่มือติดตั้ง Rasa 3.6](https://github.com/RasaHQ/rasa/blob/3.6.x/docs/docs/installation/environment-set-up.mdx)

### สร้างและเปิดใช้งาน environment

ใช้ชื่อ `.venv-rasa-deploy` ให้ตรงกับพาธที่ `run.py` เรียกใช้:

```bash
python3.10 -m venv .venv-rasa-deploy
source .venv-rasa-deploy/bin/activate
```

หากใช้ Python 3.9 ที่ติดตั้งอยู่ ให้เปลี่ยนคำสั่งแรกเป็น `python3.9 -m venv .venv-rasa-deploy` ต้องสร้าง environment ใหม่บนเครื่องปลายทาง ไม่คัดลอก environment จากเครื่องเดิม

### ตรวจสอบ Python ที่ใช้งาน

```bash
python --version
python -c "import sys; print(sys.executable)"
```

พาธต้องอยู่ภายใน environment ที่เพิ่งสร้าง และเวอร์ชันต้องตรงกับ Python ที่เลือกไว้ อย่าใช้ Python 3.11 ขึ้นไปกับ Rasa 3.6.21

---

## 📦 ขั้นตอนที่ 2: การติดตั้ง Dependencies และไลบรารี

หลัง Activate environment แล้ว รันจากโฟลเดอร์หลัก:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements/ai.txt -r requirements/rasa.txt "rasa==3.6.21" "rasa-sdk==3.6.2" "line-bot-sdk==2.3.0" "pythainlp==5.3.4"
python -m pip check
rasa --version
```

เวอร์ชันทั้งสี่ข้างต้นอ้างอิงจาก environment ที่มีอยู่ในเครื่องพัฒนา เนื่องจากไฟล์ `requirements/*.txt` ยังไม่ได้ล็อกเวอร์ชัน จึงระบุเวอร์ชันในคำสั่งติดตั้งด้วย โดยเฉพาะ LINE SDK ซึ่งโค้ดปัจจุบันใช้ API แบบ `linebot` / `linebot.models`

`pip check` ควรแสดง `No broken requirements found.` การติดตั้งอาจใช้เวลานานตามเครือข่ายและเครื่องที่ใช้ หากมีข้อผิดพลาดให้แก้ให้สำเร็จก่อนเปิดบอท ชุดคำสั่งนี้ยังไม่ใช่ lockfile ของ dependencies ทั้งหมด จึงอาจต้องปรับการติดตั้งตามระบบปฏิบัติการและสถาปัตยกรรม CPU

### ตั้งค่า LINE Credentials

สร้างไฟล์ `.env` จากตัวอย่าง **เฉพาะเมื่อยังไม่มีไฟล์ `.env`**:

```bash
cp .env.example .env
```

เปิด `.env` แล้วใส่ค่าจริงของ LINE channel ที่จะใช้:

```dotenv
LINE_CHANNEL_SECRET=YOUR_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN=YOUR_CHANNEL_ACCESS_TOKEN
```

เตรียม token และตั้งค่า channel ตาม [คู่มือสร้างบอทของ LINE](https://developers.line.biz/en/docs/messaging-api/building-bot/) ไฟล์ `.env` ถูกละไว้ใน `.gitignore` และต้องตั้งค่าใหม่บนเครื่องปลายทาง ไม่ commit ค่าจริงลง repository

### ติดตั้ง Cloudflare Tunnel

ติดตั้ง `cloudflared` ให้ตรงกับระบบปฏิบัติการและ CPU ตาม [คู่มือดาวน์โหลดอย่างเป็นทางการ](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/) แล้วตรวจว่าเรียกได้จาก Terminal:

```bash
cloudflared --version
```

`run.py` เปิด Cloudflare Quick Tunnel ให้เอง เมื่อรันแยกบริการให้เปิด tunnel ตามขั้นตอนที่ 4

---

## 🧠 ขั้นตอนที่ 3: เลือกโมเดลหรือเทรนใหม่ (Model Training)

### ใช้โมเดลที่แนบมากับ repository

สำหรับทดลองรันระบบ **ไม่จำเป็นต้องเทรนใหม่** ตรวจสอบว่า clone แล้วมีไฟล์นี้:

```text
final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz
```

`run.py` เลือกใช้ไฟล์นี้โดยตรง หากไม่มีไฟล์ ให้ตรวจสอบ branch/commit ที่ clone มาหรือรับไฟล์โมเดลจากผู้ดูแลโปรเจกต์ก่อน

### เทรนใหม่เมื่อแก้ข้อมูลฝึกหรือการตั้งค่า

```bash
cd app/rasa
rasa train
cd ../..
```

โมเดลใหม่จะอยู่ที่ `app/rasa/models/` ซึ่งไม่ติดไปกับ Git หากต้องการใช้โมเดลใหม่กับ `run.py` ต้องแก้ค่า `FINAL_MODEL` ในสคริปต์ให้ชี้ไปยังไฟล์นั้น หรือใช้วิธีรันแยกบริการแล้วเปลี่ยนค่า `--model` ให้ตรงกับไฟล์ใหม่

---

## 🚀 ขั้นตอนที่ 4: การรันเซิร์ฟเวอร์เพื่อเปิดใช้งานระบบ (Running the Bot)

### วิธีที่ 1: รันผ่านสคริปต์อัตโนมัติ

เมื่อเตรียม `.venv-rasa-deploy`, `.env`, `cloudflared` และโมเดลครบแล้ว รันจากโฟลเดอร์หลัก:

```bash
.venv-rasa-deploy/bin/python run.py
```

สคริปต์จะเปิด Action Server (5055), Rasa Server (5005), Cloudflare Quick Tunnel และเปลี่ยน Webhook URL ของ LINE channel ตาม credentials ที่ตั้งไว้ให้ชี้มาที่เครื่องนี้โดยอัตโนมัติ ถ้าใช้ channel เดียวกับเครื่องเดิม ข้อความ LINE จะถูกส่งไปยัง URL ที่ตั้งล่าสุด

รอข้อความ `SPECFLOW LIVE RUNTIME IS READY` แล้วตรวจ `Webhook Active` และ `LINE Webhook Test Call` หาก `Use webhook` ยังปิดอยู่ ให้เปิดใน LINE Developers Console แล้ว Verify อีกครั้ง กด **Ctrl+C** เพื่อหยุดบริการทั้งหมด

### วิธีที่ 2: รันแยกบริการ

เปิด Terminal 3 หน้าต่าง เริ่มที่โฟลเดอร์หลักของโปรเจกต์ และ Activate environment ในหน้าต่างที่รัน Python/Rasa

#### หน้าต่างที่ 1: เปิด Action Server

```bash
python -c "from pathlib import Path; Path('data').mkdir(exist_ok=True)"
cd app/rasa
rasa run actions --actions actions.actions --port 5055
```

รอให้ Action Server พร้อมที่พอร์ต 5055

#### หน้าต่างที่ 2: ตั้งค่าตัวแปรแวดล้อมและเปิด Rasa Server

การเรียก `rasa run` โดยตรงไม่ได้ใช้ตัวโหลด `.env` ใน `run.py` จึงต้องตั้งตัวแปรสองตัวนี้ใน Terminal ที่จะเปิด Rasa ก่อน โดยแทนค่าตัวอย่างด้วยค่าของ channel เดียวกับ `.env`

```bash
export LINE_CHANNEL_SECRET="YOUR_CHANNEL_SECRET"
export LINE_CHANNEL_ACCESS_TOKEN="YOUR_CHANNEL_ACCESS_TOKEN"
```

จากนั้นรันในหน้าต่างเดียวกัน:

```bash
cd app/rasa
rasa run --model ../../final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz --endpoints endpoints.yml --credentials credentials.yml --port 5005
```

เปิด `http://127.0.0.1:5005/webhooks/line/` ในเบราว์เซอร์ ควรได้ `{"status":"ok"}` ก่อนเชื่อมต่อ tunnel

#### หน้าต่างที่ 3: เปิด Cloudflare Tunnel และตั้ง LINE Webhook

```bash
cloudflared tunnel --protocol http2 --url http://127.0.0.1:5005
```

1. คัดลอก URL `https://...trycloudflare.com` ที่ปรากฏใน Terminal
2. ไปที่ [LINE Developers Console](https://developers.line.biz/console/) เลือก channel แล้วเปิดแท็บ **Messaging API**
3. ตั้ง **Webhook URL** เป็น `https://...trycloudflare.com/webhooks/line/webhook`
4. กด **Verify** ให้สำเร็จ และเปิด **Use webhook**
5. เพิ่ม LINE Official Account เป็นเพื่อน แล้วทดลองส่งข้อความ เช่น `จัดสเปคเล่นเกม งบ 25000`

การรันแยกบริการต้องตั้ง Webhook URL เองใหม่เมื่อ URL ของ tunnel เปลี่ยน หากหยุดระบบให้กด **Ctrl+C** ในทั้งสามหน้าต่าง

---

## 🧪 ขั้นตอนที่ 5: การประเมินผลระบบ (NLU Evaluation)

Activate environment แล้วเริ่มจากโฟลเดอร์หลัก ระบุโมเดลและชุดทดสอบให้ชัดเจน:

```bash
cd app/rasa
rasa test nlu --model ../../final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz --nlu tests/nlu_test.yml --out results
cd ../..
```

ผลประเมินจะอยู่ที่ `app/rasa/results/` หากทดสอบโมเดลที่เทรนใหม่ให้เปลี่ยนค่า `--model` ตามไฟล์ที่ต้องการ และปฏิบัติตาม [ข้อกำหนดชุดทดสอบที่ล็อกไว้](../app/rasa/tests/TEST_SET_LOCK.md) ไม่ใช้ชุดทดสอบนี้เป็นข้อมูลฝึก

---

## 📊 ขั้นตอนที่ 6: การดูข้อมูลฝั่งผู้ดูแลระบบ (Admin Analytics)

ผู้ดูแลระบบสามารถดูรายงานสถิติการใช้งานผ่าน Terminal ด้วยสคริปต์ `scripts/analytics_report.py` โดยปัจจุบันยังไม่มีหน้าเว็บ Admin สำหรับรายงานนี้

### 1. เปิดรายงานสถิติ

เปิด Terminal อีกหน้าต่างที่ **โฟลเดอร์หลักของโปรเจกต์ SpecFlow** แล้ว Activate venv ตามขั้นตอนที่ 1 หากยังอยู่ที่ `app/rasa` ให้รัน `cd ../..` ก่อน จากนั้นรัน:

```bash
python scripts/analytics_report.py
```

สำหรับ macOS / Linux ที่ใช้ environment `.venv-rasa-deploy` ของโปรเจกต์ สามารถรันจากโฟลเดอร์หลักได้โดยตรง:

```bash
.venv-rasa-deploy/bin/python scripts/analytics_report.py
```

รายงานจะแสดงใน Terminal แล้วจบการทำงาน หากต้องการดูข้อมูลล่าสุดให้รันคำสั่งเดิมอีกครั้ง

### 2. ข้อมูลที่แสดงในรายงาน

* จำนวนการค้นหาทั้งหมดและจำนวนผู้ใช้งานที่ไม่ซ้ำกัน
* จำนวนผู้ใช้งานและการค้นหาแยกตามรายสัปดาห์และรายเดือน
* ประเภทการใช้งานคอมพิวเตอร์ยอดนิยม พร้อมจำนวนครั้งและสัดส่วนเปอร์เซ็นต์
* งบประมาณเฉลี่ยและช่วงงบประมาณยอดนิยม

ข้อมูลมาจากฐานข้อมูล SQLite ที่ `data/analytics.db` ตาราง `user_searches` ซึ่งระบบบันทึกเมื่อประมวลผลคำแนะนำจัดสเปคหรืออัปเกรดสำเร็จ สามารถเปิดรายงานจากข้อมูลที่บันทึกไว้ได้โดยไม่ต้องเปิด Rasa Server หรือบริการเชื่อมต่อ LINE หากต้องการเก็บข้อมูลใหม่ ให้เปิดบอทตามขั้นตอนที่ 4 และทดลองขอคำแนะนำผ่าน LINE ก่อนรันรายงานอีกครั้ง

> [!IMPORTANT]
> หากตาราง `user_searches` ยังไม่มีข้อมูล สคริปต์จะสร้างและบันทึก **ข้อมูลจำลอง (Mock Data) 50 รายการ** ลงในฐานข้อมูลโดยอัตโนมัติ รายงานที่ได้ในกรณีนี้จึงเป็นข้อมูลตัวอย่าง และข้อมูลจำลองจะยังรวมอยู่ในรายงานครั้งถัดไปด้วย ไม่ควรนำไปอ้างอิงเป็นสถิติผู้ใช้งานจริงทั้งหมด

### 3. ข้อมูล Admin เมื่อย้ายเครื่อง

`data/analytics.db` เป็นไฟล์ภายในเครื่อง ไม่ได้ซิงก์ข้อมูลผ่าน LINE หรือ Git อัตโนมัติ ปัจจุบันไฟล์นี้ยังถูกติดตามใน Git ดังนั้น clone จะได้ข้อมูลตาม commit ที่ดึงมา แม้ `.gitignore` จะมี `*.db` อยู่ก็ตาม ข้อมูลที่เพิ่มภายหลังในเครื่องเดิมจะไม่ตามไปยังเครื่องใหม่เอง

หากต้องการย้ายสถิติล่าสุด ให้หยุดบอทและงานที่เขียนฐานข้อมูลก่อน สำรองไฟล์ของเครื่องปลายทาง แล้วคัดลอก `data/analytics.db` จากเครื่องต้นทางมาวางที่ตำแหน่งเดียวกัน หากต้องการเริ่มเก็บข้อมูลใหม่ ให้สำรองและย้ายไฟล์เดิมออกก่อนเปิด Action Server แล้วทดลองใช้งานบอทให้มีข้อมูลจริงก่อนเรียกรายงาน เพื่อหลีกเลี่ยงการสร้างข้อมูลจำลองอัตโนมัติ

---

## 🔧 ปัญหาที่อาจพบหลัง clone

| อาการ | สิ่งที่ควรตรวจสอบ |
| :--- | :--- |
| `Deployment environment not found` | สร้าง `.venv-rasa-deploy` ตามขั้นตอนที่ 1 |
| ติดตั้ง Rasa ไม่ผ่าน | ตรวจ Python, ระบบปฏิบัติการ/CPU และข้อผิดพลาดจาก pip; ใช้เวอร์ชันในขั้นตอนที่ 2 |
| `LINE Credentials are missing` | ใส่ค่าจริงใน `.env` สำหรับ `run.py` หรือตั้ง environment variables สำหรับการรันแยก |
| ไม่พบ `cloudflared` | ติดตั้งและเพิ่ม executable ใน `PATH` แล้วเปิด Terminal ใหม่ |
| ไม่พบ `thai_tokenizer` หรือ `line_channel` | เมื่อรันแยก ให้เข้า `app/rasa` ก่อนเรียก Rasa |
| ไม่พบโมเดล | ตรวจไฟล์ใน `final_models/` และค่า `--model` / `FINAL_MODEL` |
| พอร์ต 5005 หรือ 5055 ถูกใช้ | หยุดบริการเดิมที่ใช้พอร์ตนั้นก่อนเปิดใหม่ |
| LINE Verify ไม่ผ่าน | ตรวจ local health, tunnel, Webhook URL ที่ลงท้าย `/webhooks/line/webhook` และ credentials ของ channel |
| ตัวเลข Admin ไม่เหมือนเครื่องเดิม | ตรวจว่าใช้ฐานข้อมูลไฟล์เดียวกัน และมีข้อมูลจำลองปะปนหรือไม่ |
