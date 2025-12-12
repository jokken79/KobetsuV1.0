#!/usr/bin/env python3
"""
UNS Kintai Database Initialization
Crea la base de datos SQLite con todos los datos de empleados y fábricas
"""

import sqlite3
import json
from datetime import datetime, date, timedelta
import random

DB_PATH = "uns_kintai.db"

def create_tables(conn):
    """Create all database tables"""
    cursor = conn.cursor()
    
    # ═══════════════════════════════════════════════════════════════
    # 派遣先マスタ (Client Companies / Factories)
    # ═══════════════════════════════════════════════════════════════
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hakensaki (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hakensaki_id TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            plant_name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            responsible_dept TEXT,
            responsible_name TEXT,
            closing_day INTEGER DEFAULT 20,
            payment_day TEXT DEFAULT '翌月20日',
            day_shift_start TEXT DEFAULT '08:00',
            day_shift_end TEXT DEFAULT '17:00',
            night_shift_start TEXT,
            night_shift_end TEXT,
            break_minutes INTEGER DEFAULT 60,
            work_hours_per_day REAL DEFAULT 8.0,
            rounding_unit INTEGER DEFAULT 15,
            base_rate REAL DEFAULT 1700,
            overtime_rate REAL DEFAULT 1.25,
            night_rate REAL DEFAULT 1.25,
            holiday_rate REAL DEFAULT 1.35,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ═══════════════════════════════════════════════════════════════
    # 従業員マスタ (Employees)
    # ═══════════════════════════════════════════════════════════════
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            name_kanji TEXT NOT NULL,
            name_kana TEXT,
            name_romaji TEXT,
            gender TEXT CHECK(gender IN ('男', '女')),
            birth_date DATE,
            nationality TEXT DEFAULT 'ベトナム',
            residence_card TEXT,
            visa_type TEXT,
            visa_expiry DATE,
            address TEXT,
            phone TEXT,
            hakensaki_id TEXT,
            department TEXT,
            line TEXT,
            hire_date DATE,
            hourly_wage REAL DEFAULT 1700,
            transport_allowance REAL DEFAULT 5000,
            has_housing TEXT DEFAULT '有',
            housing_rent REAL DEFAULT 25000,
            dependents INTEGER DEFAULT 0,
            status TEXT DEFAULT '在職中' CHECK(status IN ('在職中', '退社', '休職')),
            jlpt_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hakensaki_id) REFERENCES hakensaki(hakensaki_id)
        )
    ''')
    
    # ═══════════════════════════════════════════════════════════════
    # 勤怠データ (Attendance Records)
    # ═══════════════════════════════════════════════════════════════
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kintai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            work_date DATE NOT NULL,
            clock_in TIME,
            clock_out TIME,
            break_minutes INTEGER DEFAULT 60,
            actual_hours REAL,
            overtime_hours REAL DEFAULT 0,
            night_hours REAL DEFAULT 0,
            holiday_flag INTEGER DEFAULT 0,
            paid_leave_flag INTEGER DEFAULT 0,
            absence_flag INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            UNIQUE(employee_id, work_date)
        )
    ''')
    
    # ═══════════════════════════════════════════════════════════════
    # 給与計算 (Salary Calculations)
    # ═══════════════════════════════════════════════════════════════
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            work_days INTEGER DEFAULT 0,
            regular_hours REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            night_hours REAL DEFAULT 0,
            holiday_hours REAL DEFAULT 0,
            paid_leave_days INTEGER DEFAULT 0,
            
            -- 支給
            base_salary REAL DEFAULT 0,
            overtime_pay REAL DEFAULT 0,
            night_pay REAL DEFAULT 0,
            holiday_pay REAL DEFAULT 0,
            paid_leave_pay REAL DEFAULT 0,
            transport_allowance REAL DEFAULT 0,
            gross_salary REAL DEFAULT 0,
            
            -- 控除
            health_insurance REAL DEFAULT 0,
            pension REAL DEFAULT 0,
            employment_insurance REAL DEFAULT 0,
            income_tax REAL DEFAULT 0,
            resident_tax REAL DEFAULT 0,
            housing_rent REAL DEFAULT 0,
            utilities REAL DEFAULT 0,
            meal_deduction REAL DEFAULT 0,
            advance_payment REAL DEFAULT 0,
            total_deductions REAL DEFAULT 0,
            
            -- 差引支給額
            net_salary REAL DEFAULT 0,
            
            status TEXT DEFAULT '未計算' CHECK(status IN ('未計算', '計算済', '確定', '支払済')),
            calculated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            UNIQUE(employee_id, year, month)
        )
    ''')
    
    # ═══════════════════════════════════════════════════════════════
    # インデックス (Indexes)
    # ═══════════════════════════════════════════════════════════════
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kintai_employee ON kintai(employee_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kintai_date ON kintai(work_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_period ON salary(year, month)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_employees_hakensaki ON employees(hakensaki_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(status)')
    
    conn.commit()
    print("✅ Tables created successfully")


def insert_factories(conn):
    """Insert factory/client company data"""
    factories = [
        {
            "hakensaki_id": "KATO-HON",
            "company_name": "加藤木材工業株式会社",
            "plant_name": "本社工場",
            "address": "愛知県春日井市新開町字平渕6",
            "phone": "0568-36-2931",
            "responsible_dept": "生産統括部",
            "responsible_name": "部長 渡邉 茂芳",
            "closing_day": 20,
            "payment_day": "翌月20日",
            "day_shift_start": "08:00",
            "day_shift_end": "17:00",
            "night_shift_start": "20:00",
            "night_shift_end": "05:00",
            "break_minutes": 80,
            "work_hours_per_day": 7.67,
            "rounding_unit": 5,
            "base_rate": 1700,
        },
        {
            "hakensaki_id": "KATO-KAS",
            "company_name": "加藤木材工業株式会社",
            "plant_name": "春日井工場",
            "address": "愛知県春日井市新開町字別渕20",
            "phone": "0568-36-2932",
            "responsible_dept": "生産統括部",
            "responsible_name": "課長 山田 太郎",
            "closing_day": 20,
            "payment_day": "翌月20日",
            "day_shift_start": "08:00",
            "day_shift_end": "17:00",
            "night_shift_start": "20:00",
            "night_shift_end": "05:00",
            "break_minutes": 80,
            "work_hours_per_day": 7.67,
            "rounding_unit": 5,
            "base_rate": 1700,
        },
        {
            "hakensaki_id": "TAKAO-OKA",
            "company_name": "高雄工業株式会社",
            "plant_name": "岡山工場",
            "address": "岡山県岡山市北区御津伊田1028-19",
            "phone": "086-724-5330",
            "responsible_dept": "岡山事業所",
            "responsible_name": "課長 大治 国利",
            "closing_day": 15,
            "payment_day": "当月末日",
            "day_shift_start": "07:00",
            "day_shift_end": "15:30",
            "night_shift_start": "19:00",
            "night_shift_end": "03:30",
            "break_minutes": 45,
            "work_hours_per_day": 7.5,
            "rounding_unit": 15,
            "base_rate": 1650,
        },
        {
            "hakensaki_id": "KORITSU-HON",
            "company_name": "コーリツ株式会社",
            "plant_name": "本社工場",
            "address": "愛知県半田市州の崎町2-112",
            "phone": "0569-21-1234",
            "responsible_dept": "製造部",
            "responsible_name": "部長 田中 一郎",
            "closing_day": 20,
            "payment_day": "翌月15日",
            "base_rate": 1650,
        },
        {
            "hakensaki_id": "YUASA-HON",
            "company_name": "ユアサ工機株式会社",
            "plant_name": "本社工場",
            "address": "愛知県豊川市本野町北浦1-22",
            "phone": "0533-86-2311",
            "responsible_dept": "製造課",
            "responsible_name": "課長 鈴木 健太",
            "closing_day": 20,
            "payment_day": "翌月20日",
            "base_rate": 1700,
        },
        {
            "hakensaki_id": "PMI-HON",
            "company_name": "ピーエムアイ有限会社",
            "plant_name": "本社工場",
            "address": "愛知県知多市八幡字荒古後88-1",
            "phone": "0562-32-4567",
            "responsible_dept": "製造部",
            "responsible_name": "部長 佐藤 正樹",
            "closing_day": 20,
            "payment_day": "翌月15日",
            "base_rate": 1600,
        },
    ]
    
    cursor = conn.cursor()
    for f in factories:
        cursor.execute('''
            INSERT OR REPLACE INTO hakensaki 
            (hakensaki_id, company_name, plant_name, address, phone, 
             responsible_dept, responsible_name, closing_day, payment_day,
             day_shift_start, day_shift_end, night_shift_start, night_shift_end,
             break_minutes, work_hours_per_day, rounding_unit, base_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f.get("hakensaki_id"), f.get("company_name"), f.get("plant_name"),
            f.get("address"), f.get("phone"), f.get("responsible_dept"),
            f.get("responsible_name"), f.get("closing_day", 20), f.get("payment_day", "翌月20日"),
            f.get("day_shift_start", "08:00"), f.get("day_shift_end", "17:00"),
            f.get("night_shift_start"), f.get("night_shift_end"),
            f.get("break_minutes", 60), f.get("work_hours_per_day", 8.0),
            f.get("rounding_unit", 15), f.get("base_rate", 1700)
        ))
    
    conn.commit()
    print(f"✅ Inserted {len(factories)} factories")


def insert_employees(conn):
    """Insert sample employee data"""
    
    # Vietnamese names (common)
    vn_surnames = ["グエン", "チャン", "レ", "ファム", "ホアン", "フイン", "ヴォ", "ダン", "ブイ", "ド"]
    vn_male_names = ["ヴァン・ミン", "ドゥック", "フン", "タイン", "クアン", "トゥアン", "ハイ", "ナム", "ロン", "ダット"]
    vn_female_names = ["ティ・ラン", "ティ・フォン", "ティ・トゥイ", "ティ・ハ", "ティ・マイ", "ティ・リン", "ティ・ホア", "ティ・タオ"]
    
    departments_kato = ["生産企画部/資材課", "資材供給部/基材課", "資材供給部/メラミン課", 
                        "生産1部/1課", "生産1部/2課", "生産1部/3課", "生産2部/生産課", "生産2部/J加工1課"]
    departments_takao = ["製作課/CVJ清掃", "製作課/CVJ短軸旋盤係", "製作課/CVJ長軸旋盤係",
                         "製作課/CVJ研磨係", "製作1課/1次旋係", "岡山HUB品証課/検査課係"]
    
    employees = []
    employee_id = 200800
    
    # Generate 50 employees
    for i in range(50):
        employee_id += 1
        gender = random.choice(["男", "女"])
        surname = random.choice(vn_surnames)
        given_name = random.choice(vn_male_names if gender == "男" else vn_female_names)
        name_kanji = f"{surname}・{given_name}"
        
        # Random assignment
        if i < 25:  # 25 at Kato
            hakensaki_id = random.choice(["KATO-HON", "KATO-KAS"])
            dept = random.choice(departments_kato)
            wage = 1700
        elif i < 35:  # 10 at Takao
            hakensaki_id = "TAKAO-OKA"
            dept = random.choice(departments_takao)
            wage = 1650
        elif i < 42:  # 7 at Koritsu
            hakensaki_id = "KORITSU-HON"
            dept = "製造部/製造ライン"
            wage = 1650
        elif i < 47:  # 5 at Yuasa
            hakensaki_id = "YUASA-HON"
            dept = "製造課/組立ライン"
            wage = 1700
        else:  # 3 at PMI
            hakensaki_id = "PMI-HON"
            dept = "製造部/検査ライン"
            wage = 1600
        
        birth_year = random.randint(1985, 2002)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        hire_year = random.randint(2020, 2024)
        hire_month = random.randint(1, 12)
        
        visa_expiry = date(2025, 12, 31) + timedelta(days=random.randint(30, 730))
        
        employees.append({
            "employee_id": f"E{employee_id}",
            "name_kanji": name_kanji,
            "name_kana": name_kanji,
            "gender": gender,
            "birth_date": f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
            "nationality": "ベトナム",
            "residence_card": f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))}{random.randint(10000000, 99999999)}{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))}",
            "visa_type": random.choice(["技術・人文知識・国際業務", "特定技能1号", "技能実習2号"]),
            "visa_expiry": visa_expiry.isoformat(),
            "address": f"愛知県名古屋市港区当知{random.randint(1,5)}-{random.randint(1,10)}-{random.randint(1,20)}",
            "phone": f"090-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            "hakensaki_id": hakensaki_id,
            "department": dept.split("/")[0],
            "line": dept.split("/")[1] if "/" in dept else "",
            "hire_date": f"{hire_year}-{hire_month:02d}-01",
            "hourly_wage": wage,
            "transport_allowance": random.choice([5000, 6000, 8000]),
            "has_housing": random.choice(["有", "有", "有", "無"]),
            "housing_rent": random.choice([25000, 28000, 30000]),
            "jlpt_level": random.choice(["N2", "N3", "N3", "N4", "N4", "N5", None]),
        })
    
    cursor = conn.cursor()
    for e in employees:
        cursor.execute('''
            INSERT OR REPLACE INTO employees 
            (employee_id, name_kanji, name_kana, gender, birth_date, nationality,
             residence_card, visa_type, visa_expiry, address, phone,
             hakensaki_id, department, line, hire_date, hourly_wage,
             transport_allowance, has_housing, housing_rent, jlpt_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            e["employee_id"], e["name_kanji"], e["name_kana"], e["gender"],
            e["birth_date"], e["nationality"], e["residence_card"], e["visa_type"],
            e["visa_expiry"], e["address"], e["phone"], e["hakensaki_id"],
            e["department"], e["line"], e["hire_date"], e["hourly_wage"],
            e["transport_allowance"], e["has_housing"], e["housing_rent"], e["jlpt_level"]
        ))
    
    conn.commit()
    print(f"✅ Inserted {len(employees)} employees")
    return employees


def generate_kintai_data(conn, year, month):
    """Generate sample attendance data for a month"""
    import calendar
    
    cursor = conn.cursor()
    
    # Get all active employees
    cursor.execute("SELECT employee_id FROM employees WHERE status = '在職中'")
    employees = [row[0] for row in cursor.fetchall()]
    
    # Get days in month
    _, days_in_month = calendar.monthrange(year, month)
    
    records = 0
    for emp_id in employees:
        for day in range(1, days_in_month + 1):
            work_date = date(year, month, day)
            weekday = work_date.weekday()
            
            # Skip weekends (mostly)
            if weekday >= 5:
                # 10% chance of working on weekend
                if random.random() > 0.1:
                    continue
                is_holiday = True
            else:
                is_holiday = False
            
            # 95% attendance on weekdays
            if random.random() > 0.95:
                continue
            
            # Random shift (80% day, 20% night)
            if random.random() > 0.8:
                clock_in = f"{random.randint(19,20):02d}:{random.choice(['00','30'])}"
                clock_out = f"0{random.randint(3,5)}:{random.choice(['00','30'])}"
                actual_hours = 7.5 + random.uniform(-0.5, 2)
                night_hours = actual_hours * 0.6
            else:
                clock_in = f"0{random.randint(7,8)}:{random.choice(['00','30','55'])}"
                clock_out = f"{random.randint(16,19):02d}:{random.choice(['00','30'])}"
                actual_hours = 7.5 + random.uniform(-0.5, 2)
                night_hours = max(0, actual_hours - 8) * 0.3
            
            overtime = max(0, actual_hours - 8)
            
            cursor.execute('''
                INSERT OR REPLACE INTO kintai 
                (employee_id, work_date, clock_in, clock_out, break_minutes,
                 actual_hours, overtime_hours, night_hours, holiday_flag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp_id, work_date.isoformat(), clock_in, clock_out, 60,
                round(actual_hours, 2), round(overtime, 2), round(night_hours, 2),
                1 if is_holiday else 0
            ))
            records += 1
    
    conn.commit()
    print(f"✅ Generated {records} attendance records for {year}/{month}")


def main():
    """Main initialization"""
    print("=" * 60)
    print("UNS 勤怠管理システム - Database Initialization")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        print("\n1. Creating tables...")
        create_tables(conn)
        
        print("\n2. Inserting factory data...")
        insert_factories(conn)
        
        print("\n3. Inserting employee data...")
        insert_employees(conn)
        
        print("\n4. Generating attendance data...")
        # Generate for current and previous month
        today = datetime.today()
        generate_kintai_data(conn, today.year, today.month)
        if today.month > 1:
            generate_kintai_data(conn, today.year, today.month - 1)
        
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print(f"   Database: {DB_PATH}")
        print("=" * 60)
        
        # Show summary
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hakensaki")
        print(f"\n   派遣先: {cursor.fetchone()[0]} companies")
        cursor.execute("SELECT COUNT(*) FROM employees")
        print(f"   従業員: {cursor.fetchone()[0]} employees")
        cursor.execute("SELECT COUNT(*) FROM kintai")
        print(f"   勤怠記録: {cursor.fetchone()[0]} records")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
