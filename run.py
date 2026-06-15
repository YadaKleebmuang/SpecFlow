import subprocess
import time
import sys
import os
import signal

# บังคับใช้รหัสภาษา UTF-8 สำหรับแสดงผลบนคอนโซลของ Windows เพื่อป้องกัน UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ค้นหาตำแหน่งโฟลเดอร์หลักของโปรเจกต์ (Project Root)
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv", "Scripts", "python.exe")
VENV_RASA = os.path.join(PROJECT_ROOT, "venv", "Scripts", "rasa.exe")
RASA_DIR = os.path.join(PROJECT_ROOT, "app", "rasa")

# ตรวจสอบตัวรันในสภาพแวดล้อมเสมือน (Virtual Environment)
if not os.path.exists(VENV_RASA):
    print("❌ ไม่พบสภาพแวดล้อมจำลอง (venv) หรือไฟล์ rasa.exe ใน venv/Scripts/")
    print("กรุณาสร้าง virtual environment และติดตั้ง dependencies ตามคู่มือ README.md ก่อน")
    sys.exit(1)

processes = []

def terminate_processes():
    print("\n🛑 กำลังหยุดการทำงานของเซิร์ฟเวอร์ SpecFlow ทั้งหมด...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("✅ ปิดเซิร์ฟเวอร์ระบบทั้งหมดและคืนค่าพอร์ตเรียบร้อยแล้ว!")

def signal_handler(sig, frame):
    terminate_processes()
    sys.exit(0)

# ลงทะเบียนตัวจับสัญญาณปิดโปรแกรม (Ctrl+C / Kill Signal)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    print("=" * 65)
    print("🚀 เริ่มระบบบอทจัดสเปคคอม SpecFlow (All-in-One Launcher Script)")
    print("=" * 65)

    # 1. รัน Rasa Action Server (พอร์ต 5055)
    print("1️⃣  กำลังสตาร์ท Rasa Action Server (Port: 5055)...")
    # ตรวจสอบและสร้างโฟลเดอร์ logs หากยังไม่มี
    os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)
    action_log_path = os.path.join(PROJECT_ROOT, "logs", "action_server.log")
    action_log_file = open(action_log_path, "w", encoding="utf-8")
    
    action_process = subprocess.Popen(
        [VENV_RASA, "run", "actions"],
        cwd=RASA_DIR,
        stdout=action_log_file,
        stderr=subprocess.STDOUT
    )
    processes.append(action_process)
    time.sleep(3)  # รอให้ Action Server บูตเครื่อง

    # 2. รัน Ngrok เชื่อมต่อ LINE API (พอร์ต 5005)
    print("2️⃣  กำลังเชื่อมต่อระบบ Ngrok Tunnel (Port: 5005)...")
    try:
        ngrok_process = subprocess.Popen(
            ["C:\\Users\\thirs\\Downloads\\ngrok.exe", "http", "5005"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        processes.append(ngrok_process)
        print("🟢 Ngrok สตาร์ทสำเร็จ! กรุณาเช็คลิงก์ Webhook HTTPS จากหน้าคอนโซล Ngrok")
        print("   และระบุลงใน LINE Developer Console (/webhooks/line/webhook)")
    except FileNotFoundError:
        print("⚠️ ไม่พบคำสั่ง 'ngrok' ใน PATH ระบบปฏิบัติการของคุณ")
        print("   ระบบจะเปิดเฉพาะแชทบอทให้ทดสอบบน Local (ข้ามการเชื่อมต่อ LINE)")

    time.sleep(2)

    # 3. รัน Rasa Server หลัก (พอร์ต 5005)
    print("3️⃣  กำลังสตาร์ท Rasa Chatbot NLU & Core (Port: 5005)...")
    rasa_process = subprocess.Popen(
        [VENV_RASA, "run", "--enable-api", "--cors", "*"],
        cwd=RASA_DIR
    )
    processes.append(rasa_process)
    
    print("\n🎉 เซิร์ฟเวอร์ SpecFlow ทั้งหมดกำลังรันอยู่ในพื้นหลัง...")
    print("👉 กดปุ่ม 'Ctrl+C' ที่หน้าต่างนี้เมื่อต้องการสั่งหยุดและปิดระบบทั้งหมด")
    print("=" * 65)

    # รอการตอบสนองจากผู้ใช้งาน หรือเมื่อมีโปรเซสใดหยุดทำงาน
    while True:
        if rasa_process.poll() is not None:
            print("❌ Rasa Server หยุดทำงานกะทันหัน")
            break
        if action_process.poll() is not None:
            print("❌ Action Server หยุดทำงานกะทันหัน")
            break
        time.sleep(1)

except KeyboardInterrupt:
    pass
finally:
    terminate_processes()
