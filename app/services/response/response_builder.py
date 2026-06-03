import sqlite3
import os
import datetime
import random

# ตำแหน่งของไฟล์ฐานข้อมูล SQLite
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/analytics.db"))

def generate_analytics_report() -> dict:
    """
    ประมวลผลข้อมูลก้อนใหญ่จาก SQLite เพื่อสรุปยอดสถิติเชิงปริมาณสำหรับแอดมิน
    """
    # ตรวจสอบและสร้างโฟลเดอร์ data/ หากไม่มีในระบบ
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ตรวจสอบ/สร้างตาราง user_searches เผื่อกรณีเริ่มระบบจากเครื่องใหม่
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            usage_type TEXT NOT NULL,
            budget_requested INTEGER NOT NULL,
            allocated_total_price INTEGER NOT NULL
        )
    """)
    conn.commit()

    # ตรวจสอบข้อมูลในตาราง
    cursor.execute("SELECT COUNT(*) FROM user_searches")
    count = cursor.fetchone()[0]
    
    # หากยังไม่มีสถิติใดๆ ในเครื่อง ให้จำลองข้อมูล (Mock Data) 50 รายการ เพื่อรันรายงานตัวอย่างทดสอบ
    if count == 0:
        user_ids = [f"U{random.randint(10000000, 99999999)}abcdef" for _ in range(10)]
        usages = ["เล่นเกม"] * 30 + ["กราฟิก"] * 12 + ["ออฟฟิศ"] * 8
        budgets = [12000, 15000, 18000, 20000, 25000, 30000, 35000, 40000, 45000, 50000, 60000]
        
        now = datetime.datetime.now()
        for _ in range(50):
            days_ago = random.randint(0, 45)  # ข้อมูลกระจายอยู่ในรอบ 6 สัปดาห์
            search_time = now - datetime.timedelta(days=days_ago, hours=random.randint(0, 23))
            timestamp = search_time.strftime("%Y-%m-%d %H:%M:%S")
            user_id = random.choice(user_ids)
            usage_type = random.choice(usages)
            budget_val = random.choice(budgets)
            allocated = int(budget_val * random.uniform(0.95, 1.05))
            
            cursor.execute("""
                INSERT INTO user_searches (timestamp, user_id, usage_type, budget_requested, allocated_total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, user_id, usage_type, budget_val, allocated))
        conn.commit()

    # ดึงค่าสถิติภาพรวม
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT user_id) FROM user_searches")
    total_searches, total_users = cursor.fetchone()

    # 1. จำนวนคนเล่นแชทบอทแยกตามรายสัปดาห์
    cursor.execute("""
        SELECT strftime('%Y-W%W', timestamp) as week, COUNT(DISTINCT user_id), COUNT(*) 
        FROM user_searches 
        GROUP BY week 
        ORDER BY week
    """)
    weekly_stats = []
    for week, users, searches in cursor.fetchall():
        weekly_stats.append({
            "week": week,
            "unique_users": users,
            "total_searches": searches
        })

    # 2. จำนวนคนเล่นแชทบอทแยกตามรายเดือน
    cursor.execute("""
        SELECT strftime('%Y-%m', timestamp) as month, COUNT(DISTINCT user_id), COUNT(*) 
        FROM user_searches 
        GROUP BY month 
        ORDER BY month
    """)
    monthly_stats = []
    for month, users, searches in cursor.fetchall():
        monthly_stats.append({
            "month": month,
            "unique_users": users,
            "total_searches": searches
        })

    # 3. สัดส่วนความนิยมความต้องการใช้งาน
    cursor.execute("""
        SELECT usage_type, COUNT(*) as count 
        FROM user_searches 
        GROUP BY usage_type 
        ORDER BY count DESC
    """)
    usage_popularity = []
    for usage_type, cnt in cursor.fetchall():
        percentage = (cnt / total_searches) * 100 if total_searches > 0 else 0
        usage_popularity.append({
            "usage_type": usage_type,
            "count": cnt,
            "percentage": round(percentage, 2)
        })

    # 4. งบประมาณที่ต้องการเฉลี่ย
    cursor.execute("SELECT AVG(budget_requested) FROM user_searches WHERE budget_requested > 0")
    avg_budget = cursor.fetchone()[0] or 0

    # 5. ช่วงงบประมาณยอดนิยม
    cursor.execute("SELECT COUNT(*) FROM user_searches WHERE budget_requested > 0")
    total_budget_searches = cursor.fetchone()[0] or 1

    cursor.execute("""
        SELECT 
            CASE 
                WHEN budget_requested < 15000 THEN 'ต่ำกว่า 15,000 บาท'
                WHEN budget_requested >= 15000 AND budget_requested < 20000 THEN '15,000 - 19,999 บาท'
                WHEN budget_requested >= 20000 AND budget_requested < 30000 THEN '20,000 - 29,999 บาท'
                WHEN budget_requested >= 30000 AND budget_requested < 40000 THEN '30,000 - 39,999 บาท'
                WHEN budget_requested >= 40000 AND budget_requested < 50000 THEN '40,000 - 49,999 บาท'
                ELSE '50,000 บาทขึ้นไป'
            END as budget_range,
            COUNT(*) as count
        FROM user_searches
        WHERE budget_requested > 0
        GROUP BY budget_range
        ORDER BY count DESC
    """)
    budget_ranges = []
    for range_name, cnt in cursor.fetchall():
        percentage = (cnt / total_budget_searches) * 100
        budget_ranges.append({
            "range": range_name,
            "count": cnt,
            "percentage": round(percentage, 2)
        })

    conn.close()

    return {
        "total_searches": total_searches,
        "total_users": total_users,
        "weekly_stats": weekly_stats,
        "monthly_stats": monthly_stats,
        "usage_popularity": usage_popularity,
        "average_budget": round(avg_budget, 2),
        "budget_ranges": budget_ranges
    }
