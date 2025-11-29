#!/usr/bin/env python3
"""
Factory Import Script

Imports factory data from JSON files (UNS-ClaudeJP-6.0.0 format)
into the database.

Usage:
    # Import from directory
    python import_factories.py --dir /path/to/factories/

    # Import single file
    python import_factories.py --file /path/to/factory.json

    # Import from factories_index.json
    python import_factories.py --index /path/to/factories_index.json --dir /path/to/factories/
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import Factory, FactoryLine
from app.core.database import Base


def parse_date(date_str: str | None) -> datetime.date | None:
    """Parse date string to date object."""
    if not date_str:
        return None

    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_time(time_str: str | None) -> datetime.time | None:
    """Parse time string to time object."""
    if not time_str:
        return None

    formats = ["%H:%M", "%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    return None


def import_factory_json(db: Session, data: dict, factory_id: str) -> Factory | None:
    """Import a single factory from JSON data."""

    # Check if factory already exists
    existing = db.query(Factory).filter(Factory.factory_id == factory_id).first()
    if existing:
        print(f"  ⏭️  Factory '{factory_id}' already exists, skipping...")
        return None

    # Extract nested data
    client = data.get("client_company", {})
    plant = data.get("plant", {})
    dispatch = data.get("dispatch_company", {})
    schedule = data.get("schedule", {})
    payment = data.get("payment", {})
    agreement = data.get("agreement", {})
    lines_data = data.get("lines", [])

    # Create factory
    factory = Factory(
        factory_id=factory_id,

        # Client company
        company_name=client.get("name", "Unknown"),
        company_address=client.get("address"),
        company_phone=client.get("phone"),
        company_fax=client.get("fax"),

        # Client responsible person
        client_responsible_department=client.get("responsible", {}).get("department"),
        client_responsible_name=client.get("responsible", {}).get("name"),
        client_responsible_phone=client.get("responsible", {}).get("phone"),

        # Client complaint handler
        client_complaint_department=client.get("complaint", {}).get("department"),
        client_complaint_name=client.get("complaint", {}).get("name"),
        client_complaint_phone=client.get("complaint", {}).get("phone"),

        # Plant/Factory
        plant_name=plant.get("name", factory_id.split("__")[-1] if "__" in factory_id else "本社"),
        plant_address=plant.get("address"),
        plant_phone=plant.get("phone"),

        # Dispatch company (UNS)
        dispatch_responsible_department=dispatch.get("responsible", {}).get("department"),
        dispatch_responsible_name=dispatch.get("responsible", {}).get("name"),
        dispatch_responsible_phone=dispatch.get("responsible", {}).get("phone"),
        dispatch_complaint_department=dispatch.get("complaint", {}).get("department"),
        dispatch_complaint_name=dispatch.get("complaint", {}).get("name"),
        dispatch_complaint_phone=dispatch.get("complaint", {}).get("phone"),

        # Schedule
        work_hours_description=schedule.get("work_hours"),
        break_time_description=schedule.get("break_time"),
        calendar_description=schedule.get("calendar"),
        overtime_description=schedule.get("overtime", {}).get("description"),
        holiday_work_description=schedule.get("holiday_work", {}).get("description"),

        # Parse times if available
        day_shift_start=parse_time(schedule.get("day_shift", {}).get("start")),
        day_shift_end=parse_time(schedule.get("day_shift", {}).get("end")),
        night_shift_start=parse_time(schedule.get("night_shift", {}).get("start")),
        night_shift_end=parse_time(schedule.get("night_shift", {}).get("end")),
        break_minutes=schedule.get("break_minutes", 60),

        # Overtime limits
        overtime_max_hours_day=schedule.get("overtime", {}).get("max_hours_day"),
        overtime_max_hours_month=schedule.get("overtime", {}).get("max_hours_month"),
        overtime_max_hours_year=schedule.get("overtime", {}).get("max_hours_year"),
        overtime_special_max_month=schedule.get("overtime", {}).get("special_max_month"),
        overtime_special_count_year=schedule.get("overtime", {}).get("special_count_year"),

        # Holiday work
        holiday_work_max_days_month=schedule.get("holiday_work", {}).get("max_days_month"),

        # Conflict date
        conflict_date=parse_date(schedule.get("conflict_date")),

        # Time unit
        time_unit_minutes=schedule.get("time_unit_minutes", 15),

        # Payment
        closing_date=payment.get("closing_date"),
        payment_date=payment.get("payment_date"),
        bank_account=payment.get("bank_account"),
        worker_closing_date=payment.get("worker_closing_date"),
        worker_payment_date=payment.get("worker_payment_date"),
        worker_calendar=payment.get("worker_calendar"),

        # Agreement
        agreement_period=parse_date(agreement.get("period")),
        agreement_explainer=agreement.get("explainer"),

        is_active=True
    )

    db.add(factory)
    db.flush()  # Get the ID

    # Import lines
    for i, line_data in enumerate(lines_data):
        supervisor = line_data.get("supervisor", {})

        line = FactoryLine(
            factory_id=factory.id,
            line_id=line_data.get("line_id", f"{factory_id}-{i+1}"),
            department=line_data.get("department"),
            line_name=line_data.get("line_name"),

            # Supervisor
            supervisor_department=supervisor.get("department"),
            supervisor_name=supervisor.get("name"),
            supervisor_phone=supervisor.get("phone"),

            # Job details
            job_description=line_data.get("job_description"),
            job_description_detail=line_data.get("job_description_detail"),
            responsibility_level=line_data.get("responsibility_level", "通常業務"),

            # Rates
            hourly_rate=line_data.get("hourly_rate"),
            billing_rate=line_data.get("billing_rate"),
            overtime_rate=line_data.get("overtime_rate"),
            night_rate=line_data.get("night_rate"),
            holiday_rate=line_data.get("holiday_rate"),

            is_active=True,
            display_order=i
        )
        db.add(line)

    print(f"  ✅ Imported factory '{factory_id}' with {len(lines_data)} lines")
    return factory


def import_from_file(db: Session, file_path: Path) -> int:
    """Import factories from a single JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error reading {file_path}: {e}")
        return 0

    # Determine factory_id from filename or data
    factory_id = data.get("factory_id") or file_path.stem

    result = import_factory_json(db, data, factory_id)
    return 1 if result else 0


def import_from_directory(db: Session, dir_path: Path) -> tuple[int, int]:
    """Import all JSON files from a directory."""
    imported = 0
    skipped = 0

    json_files = list(dir_path.glob("*.json"))

    # Exclude index files
    json_files = [f for f in json_files if not f.name.endswith("_index.json")]

    print(f"Found {len(json_files)} JSON files in {dir_path}")

    for json_file in sorted(json_files):
        result = import_from_file(db, json_file)
        if result:
            imported += 1
        else:
            skipped += 1

    return imported, skipped


def import_from_index(db: Session, index_path: Path, factories_dir: Path) -> tuple[int, int]:
    """Import factories listed in an index file."""
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading index file: {e}")
        return 0, 0

    factories_list = index_data.get("factories", [])
    print(f"Found {len(factories_list)} factories in index")

    imported = 0
    skipped = 0

    for factory_entry in factories_list:
        factory_id = factory_entry.get("factory_id", "")
        file_name = factory_entry.get("file", f"{factory_id}.json")

        factory_file = factories_dir / file_name
        if not factory_file.exists():
            print(f"  ⚠️  File not found: {factory_file}")
            skipped += 1
            continue

        result = import_from_file(db, factory_file)
        if result:
            imported += 1
        else:
            skipped += 1

    return imported, skipped


def main():
    parser = argparse.ArgumentParser(description="Import factories from JSON files")
    parser.add_argument("--file", type=Path, help="Single JSON file to import")
    parser.add_argument("--dir", type=Path, help="Directory containing JSON files")
    parser.add_argument("--index", type=Path, help="factories_index.json file")
    parser.add_argument("--create-tables", action="store_true", help="Create database tables")

    args = parser.parse_args()

    if args.create_tables:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")

    if not any([args.file, args.dir, args.index]):
        parser.print_help()
        print("\n❌ Please specify --file, --dir, or --index")
        return 1

    db = SessionLocal()

    try:
        if args.file:
            print(f"\nImporting from file: {args.file}")
            count = import_from_file(db, args.file)
            print(f"\n✅ Imported {count} factory")

        elif args.index and args.dir:
            print(f"\nImporting from index: {args.index}")
            imported, skipped = import_from_index(db, args.index, args.dir)
            print(f"\n✅ Imported {imported} factories, skipped {skipped}")

        elif args.dir:
            print(f"\nImporting from directory: {args.dir}")
            imported, skipped = import_from_directory(db, args.dir)
            print(f"\n✅ Imported {imported} factories, skipped {skipped}")

        db.commit()
        print("\n✅ All changes committed to database")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
