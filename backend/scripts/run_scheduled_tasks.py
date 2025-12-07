#!/usr/bin/env python3
"""
Scheduled Tasks Runner - 定期タスク実行スクリプト

This script runs scheduled tasks for the UNS Kobetsu system.
Can be called by system cron, Docker cron, or systemd timers.

Usage:
    # Run all daily tasks
    python scripts/run_scheduled_tasks.py --daily

    # Run specific task
    python scripts/run_scheduled_tasks.py --task update-expired
    python scripts/run_scheduled_tasks.py --task alerts
    python scripts/run_scheduled_tasks.py --task compliance

    # Run weekly tasks
    python scripts/run_scheduled_tasks.py --weekly

Example cron entries:
    # Daily at 6:00 AM - update expired and generate alerts
    0 6 * * * cd /app && python scripts/run_scheduled_tasks.py --daily

    # Weekly on Monday at 7:00 AM - compliance check
    0 7 * * 1 cd /app && python scripts/run_scheduled_tasks.py --weekly
"""
import argparse
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.kobetsu_service import KobetsuService
from app.services.alert_manager_service import AlertManagerService
from app.services.compliance_checker_service import ComplianceCheckerService


class ScheduledTaskRunner:
    """Runs scheduled tasks for the UNS Kobetsu system."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results = []

    def log(self, message: str):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")

    def get_db(self) -> Session:
        """Get a database session."""
        return SessionLocal()

    def task_update_expired_contracts(self) -> dict:
        """Update status of expired contracts to 'expired'."""
        self.log("Starting: Update expired contracts")

        db = self.get_db()
        try:
            service = KobetsuService(db)
            count = service.update_expired_contracts()

            result = {
                "task": "update_expired_contracts",
                "success": True,
                "contracts_updated": count,
                "timestamp": datetime.now().isoformat()
            }

            self.log(f"Completed: {count} contracts updated to expired status")
            return result

        except Exception as e:
            result = {
                "task": "update_expired_contracts",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.log(f"ERROR: {e}")
            return result

        finally:
            db.close()

    def task_generate_daily_alerts(self) -> dict:
        """Generate daily alert summary."""
        self.log("Starting: Generate daily alerts")

        db = self.get_db()
        try:
            alert_manager = AlertManagerService(db)
            summary = alert_manager.get_daily_summary()

            # Log alert counts
            self.log(f"  Critical alerts: {summary.get('critical_count', 0)}")
            self.log(f"  High alerts: {summary.get('high_count', 0)}")
            self.log(f"  Medium alerts: {summary.get('medium_count', 0)}")
            self.log(f"  Low alerts: {summary.get('low_count', 0)}")

            result = {
                "task": "generate_daily_alerts",
                "success": True,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }

            # Check for critical alerts
            critical_count = summary.get('critical_count', 0)
            if critical_count > 0:
                self.log(f"⚠️ WARNING: {critical_count} critical alerts require immediate attention!")

            self.log("Completed: Daily alert summary generated")
            return result

        except Exception as e:
            result = {
                "task": "generate_daily_alerts",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.log(f"ERROR: {e}")
            return result

        finally:
            db.close()

    def task_compliance_check(self) -> dict:
        """Run compliance summary check."""
        self.log("Starting: Compliance check")

        db = self.get_db()
        try:
            checker = ComplianceCheckerService(db)
            summary = checker.get_compliance_summary()

            # Log compliance status
            score = summary.get('quick_score', 0)
            status = summary.get('status', 'UNKNOWN')

            self.log(f"  Compliance Score: {score}%")
            self.log(f"  Status: {status}")
            self.log(f"  Active contracts: {summary.get('active_contracts', 0)}")
            self.log(f"  Expired but active: {summary.get('expired_but_active', 0)}")
            self.log(f"  Factories missing info: {summary.get('factories_missing_info', 0)}")

            result = {
                "task": "compliance_check",
                "success": True,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }

            # Warn if score is low
            if score < 80:
                self.log(f"⚠️ WARNING: Compliance score {score}% is below 80% threshold!")

            self.log("Completed: Compliance check")
            return result

        except Exception as e:
            result = {
                "task": "compliance_check",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.log(f"ERROR: {e}")
            return result

        finally:
            db.close()

    def task_full_compliance_audit(self) -> dict:
        """Run full compliance audit (weekly task)."""
        self.log("Starting: Full compliance audit")

        db = self.get_db()
        try:
            checker = ComplianceCheckerService(db)
            report = checker.run_full_audit()

            # Count violations by severity
            critical_count = len([v for v in report.violations if v.severity == "critical"])
            high_count = len([v for v in report.violations if v.severity == "high"])
            medium_count = len([v for v in report.violations if v.severity == "medium"])

            self.log(f"  Contracts audited: {report.contracts_audited}")
            self.log(f"  Compliance score: {report.compliance_score}%")
            self.log(f"  Critical violations: {critical_count}")
            self.log(f"  High violations: {high_count}")
            self.log(f"  Medium violations: {medium_count}")

            result = {
                "task": "full_compliance_audit",
                "success": True,
                "report": report.to_dict(),
                "timestamp": datetime.now().isoformat()
            }

            if critical_count > 0:
                self.log(f"🚨 ALERT: {critical_count} critical compliance violations found!")

            self.log("Completed: Full compliance audit")
            return result

        except Exception as e:
            result = {
                "task": "full_compliance_audit",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.log(f"ERROR: {e}")
            return result

        finally:
            db.close()

    def run_daily_tasks(self) -> list:
        """Run all daily scheduled tasks."""
        self.log("=" * 60)
        self.log("Running DAILY scheduled tasks")
        self.log("=" * 60)

        results = []

        # 1. Update expired contracts
        results.append(self.task_update_expired_contracts())

        # 2. Generate daily alerts
        results.append(self.task_generate_daily_alerts())

        # 3. Quick compliance check
        results.append(self.task_compliance_check())

        self.log("=" * 60)
        self.log("Daily tasks completed")
        self.log("=" * 60)

        return results

    def run_weekly_tasks(self) -> list:
        """Run all weekly scheduled tasks."""
        self.log("=" * 60)
        self.log("Running WEEKLY scheduled tasks")
        self.log("=" * 60)

        results = []

        # Full compliance audit
        results.append(self.task_full_compliance_audit())

        self.log("=" * 60)
        self.log("Weekly tasks completed")
        self.log("=" * 60)

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Run scheduled tasks for UNS Kobetsu system"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--daily",
        action="store_true",
        help="Run all daily tasks"
    )
    group.add_argument(
        "--weekly",
        action="store_true",
        help="Run all weekly tasks"
    )
    group.add_argument(
        "--task",
        choices=["update-expired", "alerts", "compliance", "audit"],
        help="Run a specific task"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (only show errors)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    runner = ScheduledTaskRunner(verbose=not args.quiet)

    try:
        if args.daily:
            results = runner.run_daily_tasks()
        elif args.weekly:
            results = runner.run_weekly_tasks()
        elif args.task == "update-expired":
            results = [runner.task_update_expired_contracts()]
        elif args.task == "alerts":
            results = [runner.task_generate_daily_alerts()]
        elif args.task == "compliance":
            results = [runner.task_compliance_check()]
        elif args.task == "audit":
            results = [runner.task_full_compliance_audit()]

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))

        # Check if any task failed
        failed = [r for r in results if not r.get("success", False)]
        if failed:
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
