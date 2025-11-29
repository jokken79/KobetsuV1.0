#!/usr/bin/env python3
"""
Deduplicate Factories Script

Removes duplicate factory records that have double underscore (__) in factory_id
and missing conflict_date. Keeps the newer records with single underscore (_)
that have complete data.

Usage:
    python scripts/deduplicate_factories.py --dry-run
    python scripts/deduplicate_factories.py
"""
import argparse
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.factory import Factory, FactoryLine


def analyze_duplicates(db):
    """Analyze and return duplicate factory groups."""
    factories = db.query(Factory).order_by(Factory.company_name, Factory.plant_name).all()

    # Group by company_name + plant_name
    groups = defaultdict(list)
    for f in factories:
        key = (
            f.company_name.strip() if f.company_name else '',
            f.plant_name.strip() if f.plant_name else ''
        )
        groups[key].append(f)

    # Find duplicates
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    return duplicates


def identify_records_to_delete(duplicates):
    """
    Identify which records should be deleted.

    Strategy: Delete records with:
    - Double underscore (__) in factory_id
    - Missing conflict_date
    """
    to_delete = []
    to_keep = []

    for (company, plant), factories in duplicates.items():
        for f in factories:
            # Check if this is an "old" record (double underscore, no conflict_date)
            has_double_underscore = '__' in (f.factory_id or '')
            missing_conflict_date = f.conflict_date is None

            if has_double_underscore and missing_conflict_date:
                to_delete.append(f)
            else:
                to_keep.append(f)

    return to_delete, to_keep


def deduplicate_factories(dry_run: bool = True):
    """
    Remove duplicate factory records.

    Args:
        dry_run: If True, only show what would be deleted
    """
    print(f"\n{'='*60}")
    print("FACTORY DEDUPLICATION")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    db = SessionLocal()

    try:
        # Analyze duplicates
        duplicates = analyze_duplicates(db)

        if not duplicates:
            print("No duplicates found. Database is clean.")
            return True

        print(f"Found {len(duplicates)} duplicate groups:\n")

        # Identify records to delete
        to_delete, to_keep = identify_records_to_delete(duplicates)

        # Show analysis
        print("=" * 60)
        print("RECORDS TO DELETE (old, incomplete data):")
        print("=" * 60)

        total_lines_to_delete = 0
        for f in to_delete:
            lines_count = db.query(FactoryLine).filter(FactoryLine.factory_id == f.id).count()
            total_lines_to_delete += lines_count
            print(f"  ID {f.id:3}: {f.factory_id}")
            print(f"           conflict_date: {f.conflict_date} | lines: {lines_count}")

        print(f"\n{'='*60}")
        print("RECORDS TO KEEP (new, complete data):")
        print("=" * 60)

        for f in to_keep:
            lines_count = db.query(FactoryLine).filter(FactoryLine.factory_id == f.id).count()
            print(f"  ID {f.id:3}: {f.factory_id}")
            print(f"           conflict_date: {f.conflict_date} | lines: {lines_count}")

        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Factories to delete: {len(to_delete)}")
        print(f"Factory lines to delete: {total_lines_to_delete}")
        print(f"Factories to keep: {len(to_keep)}")

        if dry_run:
            print(f"\n{'='*60}")
            print("DRY RUN - No changes made")
            print("Run without --dry-run to execute deletion")
            print(f"{'='*60}\n")
            return True

        # Execute deletion
        print(f"\n{'='*60}")
        print("EXECUTING DELETION...")
        print(f"{'='*60}")

        deleted_factories = 0
        deleted_lines = 0

        for factory in to_delete:
            # Delete factory lines first (cascade should handle this, but explicit is safer)
            lines = db.query(FactoryLine).filter(FactoryLine.factory_id == factory.id).all()
            for line in lines:
                db.delete(line)
                deleted_lines += 1

            # Delete factory
            db.delete(factory)
            deleted_factories += 1
            print(f"  Deleted: {factory.factory_id} (ID: {factory.id})")

        db.commit()

        print(f"\n{'='*60}")
        print("DELETION COMPLETE")
        print(f"{'='*60}")
        print(f"Factories deleted: {deleted_factories}")
        print(f"Factory lines deleted: {deleted_lines}")

        # Verify final state
        final_count = db.query(Factory).count()
        final_lines = db.query(FactoryLine).count()
        print(f"\nFinal state:")
        print(f"  Total factories: {final_count}")
        print(f"  Total lines: {final_lines}")
        print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate factory records"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without making changes"
    )

    args = parser.parse_args()
    success = deduplicate_factories(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
