#!/usr/bin/env python3
"""
Import Factories from JSON files

Imports factory data from config/factories/*.json files.

Usage:
    python scripts/import_factories_json.py --dir /app/factories
    python scripts/import_factories_json.py --dir /app/factories --dry-run
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.factory import Factory, FactoryLine


def parse_date(value) -> date | None:
    """Parse date from string."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        # Format: "2025-09-30 00:00:00" or "2025-09-30"
        dt = datetime.strptime(str(value).split()[0], "%Y-%m-%d")
        return dt.date()
    except:
        return None


def json_to_factory(data: dict) -> dict:
    """Convert JSON structure to Factory model fields."""
    client = data.get('client_company', {})
    plant = data.get('plant', {})
    dispatch = data.get('dispatch_company', {})
    schedule = data.get('schedule', {})
    payment = data.get('payment', {})
    agreement = data.get('agreement', {})

    return {
        'factory_id': data.get('factory_id'),
        'company_name': client.get('name') or data.get('client_company'),
        'company_address': client.get('address'),
        'company_phone': client.get('phone'),
        'client_responsible_department': client.get('responsible_person', {}).get('department'),
        'client_responsible_name': client.get('responsible_person', {}).get('name'),
        'client_responsible_phone': client.get('responsible_person', {}).get('phone'),
        'client_complaint_department': client.get('complaint_handler', {}).get('department'),
        'client_complaint_name': client.get('complaint_handler', {}).get('name'),
        'client_complaint_phone': client.get('complaint_handler', {}).get('phone'),
        'plant_name': plant.get('name') or data.get('plant_name', ''),
        'plant_address': plant.get('address'),
        'plant_phone': plant.get('phone'),
        'dispatch_responsible_department': dispatch.get('responsible_person', {}).get('department'),
        'dispatch_responsible_name': dispatch.get('responsible_person', {}).get('name'),
        'dispatch_responsible_phone': dispatch.get('responsible_person', {}).get('phone'),
        'dispatch_complaint_department': dispatch.get('complaint_handler', {}).get('department'),
        'dispatch_complaint_name': dispatch.get('complaint_handler', {}).get('name'),
        'dispatch_complaint_phone': dispatch.get('complaint_handler', {}).get('phone'),
        'work_hours_description': schedule.get('work_hours'),
        'break_time_description': schedule.get('break_time'),
        'calendar_description': schedule.get('calendar'),
        'overtime_description': schedule.get('overtime_labor'),
        'holiday_work_description': schedule.get('non_work_day_labor'),
        'conflict_date': parse_date(schedule.get('conflict_date')),
        'time_unit_minutes': Decimal(schedule.get('time_unit', '15') or '15'),
        'closing_date': payment.get('closing_date'),
        'payment_date': payment.get('payment_date'),
        'bank_account': payment.get('bank_account'),
        'worker_closing_date': payment.get('worker_closing_date'),
        'worker_payment_date': payment.get('worker_payment_date'),
        'worker_calendar': payment.get('worker_calendar'),
        'agreement_period': parse_date(agreement.get('period')),
        'agreement_explainer': agreement.get('explainer'),
        'is_active': True,
    }


def json_to_lines(data: dict, factory_db_id: int) -> list[dict]:
    """Convert JSON lines to FactoryLine model fields."""
    lines_data = data.get('lines', [])
    result = []

    for i, line in enumerate(lines_data):
        assignment = line.get('assignment', {})
        job = line.get('job', {})
        supervisor = assignment.get('supervisor', {})

        line_dict = {
            'factory_id': factory_db_id,
            'line_id': line.get('line_id'),
            'department': assignment.get('department'),
            'line_name': assignment.get('line'),
            'supervisor_department': supervisor.get('department'),
            'supervisor_name': supervisor.get('name'),
            'supervisor_phone': supervisor.get('phone'),
            'job_description': job.get('description'),
            'job_description_detail': job.get('description2'),
            'hourly_rate': Decimal(str(job.get('hourly_rate', 0) or 0)),
            'is_active': True,
            'display_order': i,
        }
        result.append(line_dict)

    return result


def import_factories(json_dir: str, dry_run: bool = False):
    """Import factories from JSON files."""
    print(f"\n{'='*60}")
    print(f"Importing factories from: {json_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    json_path = Path(json_dir)
    if not json_path.exists():
        print(f"ERROR: Directory not found: {json_dir}")
        return False

    # Find all JSON files (exclude backup, mapping files)
    json_files = [f for f in json_path.glob("*.json")
                  if not f.name.startswith('factory_id')
                  and '_mapping' not in f.name]

    print(f"Found {len(json_files)} JSON files\n")

    stats = {
        'files': 0,
        'factories_created': 0,
        'factories_updated': 0,
        'lines_created': 0,
        'lines_updated': 0,
        'errors': 0,
    }

    db = SessionLocal()

    try:
        for json_file in sorted(json_files):
            stats['files'] += 1

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                factory_id = data.get('factory_id')
                if not factory_id:
                    print(f"  SKIP {json_file.name}: No factory_id")
                    continue

                factory_data = json_to_factory(data)

                # Check if factory exists
                existing = db.query(Factory).filter(
                    Factory.factory_id == factory_id
                ).first()

                if existing:
                    # Update existing factory
                    if not dry_run:
                        for key, value in factory_data.items():
                            if value is not None:
                                setattr(existing, key, value)
                    stats['factories_updated'] += 1
                    factory_db_id = existing.id
                    action = "UPDATE"
                else:
                    # Create new factory
                    if not dry_run:
                        factory = Factory(**factory_data)
                        db.add(factory)
                        db.flush()
                        factory_db_id = factory.id
                    else:
                        factory_db_id = -1
                    stats['factories_created'] += 1
                    action = "CREATE"

                # Process lines
                lines_data = json_to_lines(data, factory_db_id)
                for line_data in lines_data:
                    if dry_run:
                        stats['lines_created'] += 1
                        continue

                    # Check if line exists
                    existing_line = db.query(FactoryLine).filter(
                        FactoryLine.factory_id == factory_db_id,
                        FactoryLine.line_id == line_data.get('line_id')
                    ).first()

                    if existing_line:
                        for key, value in line_data.items():
                            if value is not None and key != 'factory_id':
                                setattr(existing_line, key, value)
                        stats['lines_updated'] += 1
                    else:
                        line = FactoryLine(**line_data)
                        db.add(line)
                        stats['lines_created'] += 1

                print(f"  {action}: {factory_id} ({len(lines_data)} lines)")

            except json.JSONDecodeError as e:
                stats['errors'] += 1
                print(f"  ERROR {json_file.name}: Invalid JSON - {e}")
            except Exception as e:
                stats['errors'] += 1
                print(f"  ERROR {json_file.name}: {e}")

        if not dry_run:
            db.commit()
            print("\nChanges committed to database.")
        else:
            print("\nDRY RUN - No changes made.")

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    print(f"\n{'='*60}")
    print("IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Files processed:     {stats['files']}")
    print(f"Factories created:   {stats['factories_created']}")
    print(f"Factories updated:   {stats['factories_updated']}")
    print(f"Lines created:       {stats['lines_created']}")
    print(f"Lines updated:       {stats['lines_updated']}")
    print(f"Errors:              {stats['errors']}")
    print(f"{'='*60}\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Import factories from JSON files"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="/app/factories",
        help="Directory containing factory JSON files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually save to database"
    )

    args = parser.parse_args()
    success = import_factories(args.dir, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
