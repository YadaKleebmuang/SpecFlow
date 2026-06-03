import os
import sys

# เพิ่มโฟลเดอร์หลักของโปรเจกต์ (Project Root) เข้ามาใน sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.response.response_builder import generate_analytics_report

def main():
    # เรียกดึงข้อมูลสถิติที่ประมวลผลแล้ว
    data = generate_analytics_report()

    print("=" * 65)
    print("📈 รายงานสถิติการใช้งานแชทบอทจัดสเปคคอมพิวเตอร์ (SpecFlow Analytics)")
    print("=" * 65)
    print(f"📊 จำนวนการค้นหาทั้งหมด (Total Searches): {data['total_searches']:,} ครั้ง")
    print(f"👤 จำนวนผู้ใช้งานไม่ระบุตัวตนทั้งหมด (Unique Users): {data['total_users']:,} คน")
    print("-" * 65)

    # 1. รายสัปดาห์
    print("\n📅 สถิติการใช้งานแยกตามรายสัปดาห์ (Weekly Stats):")
    print(f"{'สัปดาห์ (Week)':<20}{'จำนวนผู้ใช้ (Unique Users)':<25}{'จำนวนสืบค้น (Total Searches)'}")
    for item in data["weekly_stats"]:
        print(f"{item['week']:<20}{item['unique_users']:<25}{item['total_searches']}")

    # 2. รายเดือน
    print("\n📅 สถิติการใช้งานแยกตามรายเดือน (Monthly Stats):")
    print(f"{'เดือน (Month)':<20}{'จำนวนผู้ใช้ (Unique Users)':<25}{'จำนวนสืบค้น (Total Searches)'}")
    for item in data["monthly_stats"]:
        print(f"{item['month']:<20}{item['unique_users']:<25}{item['total_searches']}")

    # 3. ลักษณะการใช้งานยอดนิยม
    print("\n🎨 สัดส่วนลักษณะความต้องการใช้งานคอมพิวเตอร์ (Usage Popularity):")
    print(f"{'ประเภทการใช้งาน':<20}{'จำนวนครั้ง':<15}{'คิดเป็นสัดส่วนเปอร์เซ็นต์ (%)'}")
    for item in data["usage_popularity"]:
        print(f"{item['usage_type']:<20}{item['count']:<15}{item['percentage']:.2f}%")

    # 4. งบประมาณเฉลี่ยและช่วงงบประมาณยอดนิยม
    print("\n💰 วิเคราะห์งบประมาณการจัดสเปค (Budget Analysis):")
    print(f"💵 งบประมาณเฉลี่ยรวมที่ผู้ใช้ต้องการ: {data['average_budget']:,.2f} บาท")
    print(f"\n{'ช่วงงบประมาณ (Budget Range)':<30}{'จำนวนครั้งที่สืบค้น':<20}{'คิดเป็นเปอร์เซ็นต์ (%)'}")
    for item in data["budget_ranges"]:
        print(f"{item['range']:<30}{item['count']:<20}{item['percentage']:.2f}%")
        
    print("=" * 65)
    print("💡 ข้อมูลนี้พร้อมสำหรับการนำไปจัดทำตาราง/แผนภูมิในรายงานผลการทดลอง บทที่ 4")
    print("=" * 65)

if __name__ == "__main__":
    main()
