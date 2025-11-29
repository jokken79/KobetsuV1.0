#!/usr/bin/env python3
"""
Import Demo Data Script

Imports sample data for development and testing.
Creates sample factories, employees, and contracts.

Usage:
    python scripts/import_demo_data.py
    python scripts/import_demo_data.py --count 10
"""
import argparse
import sys
from pathlib import Path
from datetime import date, time, timedelta
from decimal import Decimal
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, engine
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee


# Sample data for generation
FACTORY_NAMES = [
    "トヨタ自動車株式会社 田原工場",
    "本田技研工業株式会社 鈴鹿製作所",
    "日産自動車株式会社 追浜工場",
    "マツダ株式会社 本社工場",
    "スバル株式会社 群馬製作所",
    "三菱自動車工業株式会社 岡崎製作所",
    "スズキ株式会社 湖西工場",
    "ダイハツ工業株式会社 池田工場",
]

FACTORY_ADDRESSES = [
    "愛知県田原市緑が浜2号1番地",
    "三重県鈴鹿市平田町1907",
    "神奈川県横須賀市夏島町1番地",
    "広島県安芸郡府中町新地3-1",
    "群馬県太田市スバル町1-1",
    "愛知県岡崎市橋目町字中新切1番地",
    "静岡県湖西市白須賀4520番地",
    "大阪府池田市ダイハツ町1-1",
]

WORK_CONTENTS = [
    "自動車部品の組立作業、検品作業、梱包作業",
    "製造ライン作業、品質検査、設備点検補助",
    "エンジン部品の加工作業、検査作業",
    "車体溶接作業、塗装前処理作業",
    "電装品の組付け作業、動作確認作業",
    "内装部品の取付作業、仕上げ作業",
    "プレス加工作業、金型管理補助作業",
    "物流作業、部品供給作業、在庫管理補助",
]

SUPERVISOR_NAMES = [
    ("製造部", "課長", "田中太郎"),
    ("生産管理部", "係長", "佐藤次郎"),
    ("品質管理部", "主任", "鈴木三郎"),
    ("組立課", "課長", "高橋四郎"),
    ("検査課", "係長", "渡辺五郎"),
    ("物流部", "主任", "伊藤六郎"),
]

DEPARTMENTS = ["人事部", "総務部", "製造部", "品質管理部", "営業部"]
POSITIONS = ["部長", "課長", "係長", "主任", "担当"]
NAMES = ["山田太郎", "佐藤花子", "鈴木一郎", "高橋美咲", "田中健一", "渡辺直子"]


def generate_phone():
    """Generate a random Japanese phone number."""
    return f"0{random.randint(3, 9)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"


def generate_contact_info():
    """Generate random contact info."""
    return {
        "department": random.choice(DEPARTMENTS),
        "position": random.choice(POSITIONS),
        "name": random.choice(NAMES),
        "phone": generate_phone(),
    }


def generate_manager_info():
    """Generate random manager info."""
    return {
        "department": random.choice(DEPARTMENTS),
        "position": random.choice(POSITIONS),
        "name": random.choice(NAMES),
        "phone": generate_phone(),
        "license_number": f"R{random.randint(1, 5)}-{random.randint(10000, 99999)}",
    }


def create_demo_contracts(count: int = 5):
    """
    Create demo Kobetsu Keiyakusho contracts.

    Args:
        count: Number of contracts to create
    """
    db = SessionLocal()

    try:
        contracts_created = 0

        for i in range(count):
            # Generate contract data
            factory_idx = i % len(FACTORY_NAMES)
            supervisor_idx = i % len(SUPERVISOR_NAMES)

            # Dates
            start_date = date.today() + timedelta(days=random.randint(-30, 30))
            end_date = start_date + timedelta(days=random.randint(90, 365))

            # Generate contract number
            contract_number = f"KOB-{date.today().strftime('%Y%m')}-{i + 1:04d}"

            # Check if contract already exists
            existing = db.query(KobetsuKeiyakusho).filter(
                KobetsuKeiyakusho.contract_number == contract_number
            ).first()

            if existing:
                print(f"Contract {contract_number} already exists, skipping...")
                continue

            # Create contract
            contract = KobetsuKeiyakusho(
                contract_number=contract_number,
                factory_id=factory_idx + 1,
                dispatch_assignment_id=None,
                contract_date=date.today(),
                dispatch_start_date=start_date,
                dispatch_end_date=end_date,
                work_content=WORK_CONTENTS[factory_idx],
                responsibility_level=random.choice(["補助的業務", "通常業務", "責任業務"]),
                worksite_name=FACTORY_NAMES[factory_idx],
                worksite_address=FACTORY_ADDRESSES[factory_idx],
                organizational_unit=f"第{random.randint(1, 3)}製造部",
                supervisor_department=SUPERVISOR_NAMES[supervisor_idx][0],
                supervisor_position=SUPERVISOR_NAMES[supervisor_idx][1],
                supervisor_name=SUPERVISOR_NAMES[supervisor_idx][2],
                work_days=["月", "火", "水", "木", "金"],
                work_start_time=time(8, 0),
                work_end_time=time(17, 0),
                break_time_minutes=60,
                overtime_max_hours_day=Decimal("3.0"),
                overtime_max_hours_month=Decimal("45.0"),
                overtime_max_days_month=15,
                holiday_work_max_days=2,
                safety_measures="派遣先の安全衛生規程に従い、必要な保護具を着用すること",
                haken_moto_complaint_contact=generate_contact_info(),
                haken_saki_complaint_contact=generate_contact_info(),
                hourly_rate=Decimal(str(random.randint(1200, 1800))),
                overtime_rate=Decimal(str(random.randint(1500, 2250))),
                night_shift_rate=Decimal(str(random.randint(1600, 2400))),
                holiday_rate=Decimal(str(random.randint(1800, 2700))),
                welfare_facilities=["食堂", "更衣室", "休憩室"],
                haken_moto_manager=generate_manager_info(),
                haken_saki_manager=generate_manager_info(),
                termination_measures="30日前までに書面にて通知。派遣労働者の雇用安定に努める。",
                is_kyotei_taisho=random.choice([True, False]),
                is_direct_hire_prevention=random.choice([True, False]),
                is_mukeiko_60over_only=False,
                number_of_workers=random.randint(1, 10),
                status=random.choice(["draft", "active", "active", "active"]),
                notes=f"デモデータ #{i + 1}",
                created_by=1,
            )

            db.add(contract)
            contracts_created += 1

        db.commit()
        print(f"\nSuccessfully created {contracts_created} demo contracts!")

        # Display summary
        print("\n" + "=" * 60)
        print("Demo Data Summary")
        print("=" * 60)

        total = db.query(KobetsuKeiyakusho).count()
        active = db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.status == "active"
        ).count()
        draft = db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.status == "draft"
        ).count()

        print(f"Total Contracts: {total}")
        print(f"Active Contracts: {active}")
        print(f"Draft Contracts: {draft}")
        print("=" * 60)

    except Exception as e:
        print(f"Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def clear_demo_data():
    """Clear all demo data from the database."""
    db = SessionLocal()

    try:
        # Delete employee associations first
        deleted_employees = db.query(KobetsuEmployee).delete()

        # Delete contracts
        deleted_contracts = db.query(KobetsuKeiyakusho).delete()

        db.commit()

        print(f"Cleared {deleted_contracts} contracts and {deleted_employees} employee associations")

    except Exception as e:
        print(f"Error clearing demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import demo data for UNS Kobetsu Keiyakusho"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of demo contracts to create (default: 5)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing demo data before import"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("UNS Kobetsu Keiyakusho - Demo Data Import")
    print("=" * 60)

    if args.clear:
        print("\nClearing existing data...")
        clear_demo_data()

    print(f"\nCreating {args.count} demo contracts...")
    create_demo_contracts(count=args.count)

    print("\nDone!")


if __name__ == "__main__":
    main()
