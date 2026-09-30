# 🪟 คู่มือติดตั้ง SpecFlow บน Windows

คู่มือนี้ใช้ **Command Prompt (CMD)** สำหรับทุกคำสั่ง ตั้งแต่ clone โปรเจกต์ เปิดบอทผ่าน LINE ไปจนถึงดูข้อมูล Admin หากใช้ Windows Terminal ให้เลือกโปรไฟล์ **Command Prompt**

สำหรับ macOS / Linux หรือ WSL ให้อ่าน [คู่มือติดตั้ง macOS / Linux](setup.md)

> [!IMPORTANT]
> บน Windows ให้เปิดบริการแยกกันตามขั้นตอนที่ 4 เพราะ `run.py` ปัจจุบันใช้พาธ executable และ `PYTHONPATH` แบบ Unix คู่มือนี้ยังไม่ได้ทดสอบติดตั้งจริงบน Windows และ dependencies ทั้งหมดยังไม่มี lockfile

## 📥 ก่อนเริ่ม: เตรียมเครื่องและ clone

เตรียมสิ่งต่อไปนี้:

* Git และ Python 3.10 พร้อม Python Launcher (`py`)
* LINE Official Account ที่เปิด Messaging API พร้อม Channel secret และ Channel access token
* บัญชี ngrok และ authtoken สำหรับเปิด HTTPS tunnel
* อินเทอร์เน็ตสำหรับติดตั้งไลบรารีและเชื่อมต่อ LINE
* พอร์ต 5005 และ 5055 ที่ว่างสำหรับ Rasa และ Action Server

ตรวจสอบใน CMD:

```cmd
git --version
py -3.10 --version
```

แทนที่ `YOUR_REPOSITORY_URL` ด้วย URL ของ repository แล้วรัน:

```cmd
cd /d "%USERPROFILE%"
git clone YOUR_REPOSITORY_URL SpecFlow
cd SpecFlow
```

ตัวอย่างต่อจากนี้ใช้โฟลเดอร์ `%USERPROFILE%\SpecFlow` หาก clone ไว้ที่อื่น ให้เปลี่ยนพาธในคำสั่ง `cd /d` ให้ตรงกับเครื่องของคุณ

หากต้องการดูเฉพาะรายงาน Admin ใช้ Python และข้ามไปขั้นตอนที่ 6 ได้เลย โดยไม่ต้องติดตั้ง Rasa หรือตั้งค่า LINE

---

## ⚙️ ขั้นตอนที่ 1: สร้าง Python environment

รันจากโฟลเดอร์หลักของโปรเจกต์:

```cmd
py -3.10 -m venv venv
venv\Scripts\activate.bat
python --version
python -c "import sys; print(sys.executable)"
```

ควรเห็น `(venv)` ที่ต้นบรรทัด, Python `3.10.x` และพาธ Python ลงท้ายด้วย `SpecFlow\venv\Scripts\python.exe`

สร้าง environment ใหม่บนเครื่องนี้เสมอ เพราะโฟลเดอร์ `venv` ไม่ติดไปกับ Git และไม่ควรคัดลอกจากเครื่องอื่น Rasa 3.6.21 รองรับ Python `>=3.8,<3.11` จึงไม่ใช้ Python 3.11 ขึ้นไปกับชุดนี้ ดูรายละเอียดใน [คู่มือติดตั้ง Rasa 3.6](https://github.com/RasaHQ/rasa/blob/3.6.x/docs/docs/installation/environment-set-up.mdx)

---

## 📦 ขั้นตอนที่ 2: ติดตั้งไลบรารีและ ngrok

ใน CMD ที่เปิด environment แล้ว รัน:

```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements/ai.txt -r requirements/rasa.txt "rasa==3.6.21" "rasa-sdk==3.6.2" "line-bot-sdk==2.3.0" "pythainlp==5.3.4"
python -m pip check
rasa --version
```

`pip check` ควรแสดง `No broken requirements found.` หากติดตั้งไม่สำเร็จ ให้แก้ข้อผิดพลาดก่อนเปิดบอท เวอร์ชันทั้งสี่อ้างอิงจาก environment ของเครื่องพัฒนา เนื่องจากไฟล์ `requirements/*.txt` ยังไม่ได้ล็อกเวอร์ชัน

ติดตั้ง ngrok ตาม [คู่มือติดตั้ง ngrok สำหรับ Windows](https://ngrok.com/download/windows) และให้เรียกคำสั่งได้ผ่าน `PATH` จากนั้นเปิด CMD ใหม่เพื่อตรวจสอบ:

```cmd
ngrok version
```

สมัครหรือเข้าสู่บัญชี ngrok แล้วคัดลอก authtoken จาก [หน้า Your Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) แทนที่ `YOUR_NGROK_AUTHTOKEN` ในคำสั่งนี้ด้วยค่าจริง:

```cmd
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

ทำขั้นตอนนี้ครั้งแรกสำหรับบัญชีผู้ใช้ Windows ที่จะรัน ngrok โดย authtoken ของ ngrok เป็นคนละค่ากับ Channel access token ของ LINE

เตรียม Channel secret และ Channel access token ของ LINE channel ตาม [คู่มือสร้างบอทของ LINE](https://developers.line.biz/en/docs/messaging-api/building-bot/) จะนำมาใส่ในหน้าต่าง Rasa ในขั้นตอนที่ 4

---

## 🧠 ขั้นตอนที่ 3: ตรวจสอบโมเดล

repository มีโมเดลที่เทรนด้วย Python 3.9.6 และ Rasa 3.6.21 อยู่แล้ว จึงไม่จำเป็นต้องเทรนใหม่เพื่อทดลองเปิดระบบ ตรวจสอบจากโฟลเดอร์หลัก:

```cmd
dir final_models\run-20260825-001846\20260825-001851-woolen-billet.tar.gz
```

หากไม่พบไฟล์ ให้ตรวจสอบ branch/commit ที่ clone หรือรับไฟล์โมเดลจากผู้ดูแลโปรเจกต์ก่อน

เฉพาะกรณีแก้ข้อมูลฝึกหรือต้องการเทรนใหม่ ให้เปิด environment แล้วรัน:

```cmd
cd app\rasa
rasa train
cd ..\..
```

โมเดลใหม่อยู่ใน `app\rasa\models\` และไม่ติดไปกับ Git หากต้องการใช้โมเดลใหม่นี้ ให้เปลี่ยนค่า `--model` ในขั้นตอนที่ 4 และ 5 เป็น `models\ชื่อไฟล์โมเดล.tar.gz` โดยคำสั่งทั้งสองรันจาก `app\rasa`

---

## 🚀 ขั้นตอนที่ 4: เปิดบอทผ่าน LINE

เปิด **CMD 3 หน้าต่าง** และปล่อยแต่ละหน้าต่างทำงานค้างไว้หลังเริ่มบริการ

### หน้าต่างที่ 1: Action Server

```cmd
cd /d "%USERPROFILE%\SpecFlow"
venv\Scripts\activate.bat
python -c "from pathlib import Path; Path('data').mkdir(exist_ok=True)"
cd app\rasa
rasa run actions --actions actions.actions --port 5055
```

รอให้ Action Server พร้อมใช้งานที่พอร์ต 5055

### หน้าต่างที่ 2: Rasa Server และ LINE credentials

แทนที่ `YOUR_CHANNEL_SECRET` และ `YOUR_CHANNEL_ACCESS_TOKEN` ด้วยค่าจริงของ channel ที่จะใช้:

```cmd
cd /d "%USERPROFILE%\SpecFlow"
venv\Scripts\activate.bat
set "LINE_CHANNEL_SECRET=YOUR_CHANNEL_SECRET"
set "LINE_CHANNEL_ACCESS_TOKEN=YOUR_CHANNEL_ACCESS_TOKEN"
cd app\rasa
rasa run --model ..\..\final_models\run-20260825-001846\20260825-001851-woolen-billet.tar.gz --endpoints endpoints.yml --credentials credentials.yml --port 5005
```

ตัวแปรจาก `set` ใช้เฉพาะ CMD หน้าต่างนี้ เมื่อเปิดหน้าต่างใหม่ต้องตั้งค่าอีกครั้ง การรันแยกตามคู่มือนี้ไม่จำเป็นต้องสร้าง `.env` เพราะ `rasa run` ไม่ได้เรียกตัวโหลด `.env` ใน `run.py` หากมี `.env` อยู่แล้ว ให้ใช้ค่าเดียวกันมาตั้งผ่าน `set` และไม่ commit credentials ลง Git

เปิด `http://127.0.0.1:5005/webhooks/line/` ในเบราว์เซอร์ ควรได้ `{"status":"ok"}` ก่อนทำขั้นตอนถัดไป

### หน้าต่างที่ 3: ngrok

```cmd
ngrok http 5005
```

มองหาบรรทัด **Forwarding** แล้วคัดลอกเฉพาะ URL ที่ขึ้นต้นด้วย `https://` ซึ่งชี้ไปยัง `http://localhost:5005` ใช้ URL จริงที่ ngrok แสดง แล้วตั้งค่าที่ LINE:

1. เปิด [LINE Developers Console](https://developers.line.biz/console/) แล้วเลือก channel ที่ใช้ credentials ในหน้าต่างที่ 2
2. ไปที่แท็บ **Messaging API** และตั้ง **Webhook URL** โดยนำ HTTPS URL ของ ngrok มาต่อท้ายด้วย `/webhooks/line/webhook`
3. กด **Verify** ให้สำเร็จ และเปิด **Use webhook**
4. เพิ่ม LINE Official Account เป็นเพื่อน แล้วส่งข้อความ เช่น `จัดสเปคเล่นเกม งบ 25000`

หากใช้ channel เดียวกับเครื่องเดิม ข้อความ LINE จะถูกส่งไปยัง Webhook URL ที่ตั้งล่าสุด ต้องเปลี่ยน URL ใน LINE ใหม่ทุกครั้งที่เปิด tunnel แล้วได้ URL ใหม่

เมื่อต้องการหยุดระบบ กด **Ctrl+C** ในทั้งสามหน้าต่าง การเปิดบอทครั้งถัดไปเริ่มที่ขั้นตอนที่ 4 ได้เลย

---

## 🧪 ขั้นตอนที่ 5: ประเมินผล NLU (เมื่อต้องการ)

เปิด CMD อีกหน้าต่างแล้วรัน:

```cmd
cd /d "%USERPROFILE%\SpecFlow"
venv\Scripts\activate.bat
cd app\rasa
rasa test nlu --model ..\..\final_models\run-20260825-001846\20260825-001851-woolen-billet.tar.gz --nlu tests\nlu_test.yml --out results
cd ..\..
```

ผลจะอยู่ที่ `app\rasa\results\` ปฏิบัติตาม [ข้อกำหนดชุดทดสอบที่ล็อกไว้](../app/rasa/tests/TEST_SET_LOCK.md) และไม่ใช้ชุดทดสอบนี้เป็นข้อมูลฝึก

---

## 📊 ขั้นตอนที่ 6: ดูข้อมูลฝั่ง Admin

เปิด CMD อีกหน้าต่าง รันจากโฟลเดอร์หลักด้วย Python 3.10 ได้โดยตรง สคริปต์นี้ใช้เฉพาะไลบรารีมาตรฐาน:

```cmd
cd /d "%USERPROFILE%\SpecFlow"
py -3.10 -X utf8 scripts\analytics_report.py
```

รายงานแสดงผ่าน Terminal แล้วจบการทำงาน ไม่มีหน้าเว็บ Admin สำหรับรายงานนี้ หากต้องการข้อมูลล่าสุดให้รันคำสั่งเดิมอีกครั้ง ข้อมูลที่ดูได้ประกอบด้วย:

* จำนวนการค้นหาทั้งหมดและจำนวนผู้ใช้งานที่ไม่ซ้ำกัน
* จำนวนผู้ใช้งานและการค้นหารายสัปดาห์/รายเดือน
* ประเภทการใช้งานยอดนิยมและสัดส่วนเปอร์เซ็นต์
* งบประมาณเฉลี่ยและช่วงงบประมาณยอดนิยม

ข้อมูลอ่านจาก `data\analytics.db` ตาราง `user_searches` สามารถดูข้อมูลเดิมได้โดยไม่เปิดบอท หากต้องการเก็บข้อมูลใหม่ ให้เปิดบอทตามขั้นตอนที่ 4 แล้วทดลองขอคำแนะนำจัดสเปคหรืออัปเกรดให้สำเร็จ

> [!IMPORTANT]
> หากตารางยังว่าง สคริปต์รายงานจะสร้างและบันทึกข้อมูลจำลอง 50 รายการอัตโนมัติ ข้อมูลเหล่านี้จะรวมอยู่ในรายงานครั้งต่อไปด้วย จึงไม่ควรอ้างอิงว่าเป็นสถิติผู้ใช้จริงทั้งหมด

### การย้ายข้อมูล Admin จากเครื่องเดิม

`data\analytics.db` เป็นไฟล์ภายในแต่ละเครื่อง ไม่มีการซิงก์อัตโนมัติ ปัจจุบันไฟล์นี้ยังถูกติดตามใน Git ดังนั้น clone จะได้ข้อมูลตาม commit ที่ดึงมา แม้ `.gitignore` จะระบุ `*.db` ไว้ก็ตาม

หากต้องการสถิติล่าสุด ให้หยุดบอทและงานที่เขียนฐานข้อมูลก่อน สำรองไฟล์ปลายทาง แล้วคัดลอก `data\analytics.db` จากเครื่องเดิมมาวางตำแหน่งเดียวกัน หากต้องการเริ่มเก็บข้อมูลใหม่ ให้สำรองและย้ายไฟล์เดิมออกก่อนเปิด Action Server แล้วใช้งานบอทให้มีข้อมูลจริงก่อนเปิดรายงาน เพื่อไม่ให้สคริปต์สร้างข้อมูลจำลอง

---

## 🔧 ปัญหาที่อาจพบบน Windows

| อาการ | วิธีตรวจสอบ |
| :--- | :--- |
| ไม่รู้จัก `git`, `py` หรือ `ngrok` | ตรวจการติดตั้งและ `PATH` แล้วเปิด CMD ใหม่ |
| ngrok แจ้งปัญหา authentication หรือ authtoken | ตรวจบัญชีและตั้งค่า `ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN` ตามขั้นตอนที่ 2 |
| ไม่พบ Python 3.10 | ตรวจว่าได้ติดตั้ง Python 3.10 พร้อม Python Launcher แล้ว |
| ไม่รู้จัก `rasa` | กลับโฟลเดอร์หลัก เรียก `venv\Scripts\activate.bat` และตรวจว่าติดตั้งขั้นตอนที่ 2 สำเร็จ |
| ติดตั้งไลบรารีไม่ผ่าน | ตรวจ Python ด้วย `python --version` และอ่านข้อผิดพลาด pip; ใช้เวอร์ชันตามขั้นตอนที่ 2 |
| รัน `Activate.ps1` ไม่ได้ | คู่มือนี้ใช้ CMD ให้เปลี่ยนมาใช้ `activate.bat` ตามขั้นตอนที่ 1 |
| `Deployment environment not found` เมื่อเรียก `run.py` | ใช้วิธีรันแยกบริการในขั้นตอนที่ 4 สำหรับ Windows |
| ไม่พบ `thai_tokenizer` หรือ `line_channel` | เข้า `app\rasa` ก่อนเรียก Rasa |
| ไม่พบโมเดล | ตรวจพาธในขั้นตอนที่ 3 และค่า `--model` |
| พอร์ต 5005 หรือ 5055 ถูกใช้ | หยุดบริการเดิมที่ใช้พอร์ตนั้นก่อนเริ่มใหม่ |
| LINE Verify ไม่ผ่าน | ตรวจ local health, tunnel, Webhook URL และค่าจาก `set` ใน CMD ที่เปิด Rasa |
| ภาษาไทยในรายงานอ่านไม่ออก | ใช้คำสั่ง `-X utf8` ตามขั้นตอนที่ 6 และฟอนต์ Terminal ที่รองรับภาษาไทย |
| ตัวเลข Admin ไม่เหมือนเครื่องเดิม | ตรวจฐานข้อมูลที่คัดลอกมาและข้อมูลจำลองที่อาจปะปนอยู่ |
