"""
Tests for Agent Services
Tests: ContractValidatorService, ComplianceCheckerService, AlertManagerService
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.services.contract_validator_service import (
    ContractValidatorService,
    ValidationResult,
    ValidationError,
    REQUIRED_FIELDS
)
from app.services.compliance_checker_service import (
    ComplianceCheckerService,
    ComplianceReport,
    ComplianceViolation
)
from app.services.alert_manager_service import (
    AlertManagerService,
    AlertPriority,
    AlertType,
    Alert,
    AlertSummary
)
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.factory import Factory
from app.models.employee import Employee


# =============================================================================
# ContractValidatorService Tests
# =============================================================================

class TestContractValidatorService:
    """Tests for contract validation service."""

    def test_validate_complete_contract_data(self, db: Session, test_factory: Factory):
        """Complete valid data should pass validation."""
        service = ContractValidatorService(db)

        valid_data = {
            "work_content": "製造ライン作業、検品、梱包業務の補助作業",
            "responsibility_level": "通常業務",
            "worksite_name": "テスト株式会社 本社工場",
            "worksite_address": "東京都千代田区丸の内1-1-1",
            "supervisor_name": "田中太郎",
            "work_days": ["月", "火", "水", "木", "金"],
            "work_start_time": "08:00",
            "work_end_time": "17:00",
            "break_time_minutes": 60,
            "safety_measures": "安全帽着用義務",
            "haken_moto_complaint_contact": {
                "department": "人事部", "position": "課長",
                "name": "山田花子", "phone": "03-1234-5678"
            },
            "haken_saki_complaint_contact": {
                "department": "総務部", "position": "係長",
                "name": "佐藤次郎", "phone": "03-9876-5432"
            },
            "termination_measures": "14日前に書面で通知",
            "haken_moto_manager": {
                "department": "派遣事業部", "position": "部長",
                "name": "鈴木一郎", "phone": "03-1234-5678"
            },
            "haken_saki_manager": {
                "department": "人事部", "position": "部長",
                "name": "高橋三郎", "phone": "03-9876-5432"
            },
            "hourly_rate": 1500,
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=180)),
        }

        result = service.validate_contract_data(valid_data, factory_id=test_factory.id)

        assert result.is_valid
        assert len(result.errors) == 0
        assert result.compliance_score >= 80

    def test_validate_missing_required_fields(self, db: Session, test_factory: Factory):
        """Missing required fields should produce errors."""
        service = ContractValidatorService(db)

        incomplete_data = {
            "work_content": "Test",  # Too short but present
            # Missing most required fields
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=30)),
        }

        result = service.validate_contract_data(incomplete_data)

        assert not result.is_valid
        assert len(result.errors) > 0

        # Check specific missing fields are reported
        error_fields = [e.field for e in result.errors]
        assert "worksite_name" in error_fields
        assert "supervisor_name" in error_fields
        assert "hourly_rate" in error_fields

    def test_validate_date_range_end_before_start(self, db: Session):
        """End date before start date should fail."""
        service = ContractValidatorService(db)

        data = {
            "work_content": "製造ライン作業",
            "dispatch_start_date": str(date.today() + timedelta(days=30)),
            "dispatch_end_date": str(date.today()),  # Before start
        }

        result = service.validate_contract_data(data)

        assert not result.is_valid
        date_errors = [e for e in result.errors if e.field == "dispatch_end_date"]
        assert len(date_errors) > 0
        assert any("INVALID_DATE_RANGE" in e.code for e in date_errors)

    def test_validate_duration_exceeds_3_years(self, db: Session):
        """Contract exceeding 3 years should fail."""
        service = ContractValidatorService(db)

        data = {
            "work_content": "製造ライン作業と検品業務",
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=365 * 4)),  # 4 years
        }

        result = service.validate_contract_data(data)

        duration_errors = [e for e in result.errors if "DURATION" in e.code]
        assert len(duration_errors) > 0

    def test_validate_overtime_exceeds_monthly_limit(self, db: Session):
        """Monthly overtime exceeding 45 hours should produce error."""
        service = ContractValidatorService(db)

        data = {
            "work_content": "製造ライン作業",
            "overtime_max_hours_month": 50,  # Exceeds 45 hour limit
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=30)),
        }

        result = service.validate_contract_data(data)

        overtime_errors = [e for e in result.errors if "MONTHLY" in e.code]
        assert len(overtime_errors) > 0

    def test_validate_low_overtime_rate_warning(self, db: Session):
        """Overtime rate below 1.25x should produce warning."""
        service = ContractValidatorService(db)

        data = {
            "work_content": "製造ライン作業と検品業務",
            "hourly_rate": 1000,
            "overtime_rate": 1100,  # Should be at least 1250
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=30)),
        }

        result = service.validate_contract_data(data)

        rate_warnings = [w for w in result.warnings if "OVERTIME_RATE" in w.code]
        assert len(rate_warnings) > 0

    def test_validate_employee_resigned(
        self, db: Session, test_factory: Factory, test_employee: Employee
    ):
        """Resigned employee should produce error."""
        service = ContractValidatorService(db)

        # Mark employee as resigned
        test_employee.status = "resigned"
        db.commit()

        data = {
            "work_content": "製造ライン作業と検品業務",
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=30)),
        }

        result = service.validate_contract_data(
            data,
            factory_id=test_factory.id,
            employee_ids=[test_employee.id]
        )

        emp_errors = [e for e in result.errors if "RESIGNED" in e.code]
        assert len(emp_errors) > 0

    def test_validate_factory_not_found(self, db: Session):
        """Invalid factory ID should produce error."""
        service = ContractValidatorService(db)

        data = {
            "work_content": "製造ライン作業と検品業務",
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=30)),
        }

        result = service.validate_contract_data(data, factory_id=99999)

        factory_errors = [e for e in result.errors if "FACTORY" in e.code]
        assert len(factory_errors) > 0

    def test_compliance_score_calculation(self, db: Session):
        """Compliance score should reflect validation results."""
        service = ContractValidatorService(db)

        # Valid data should have high score
        valid_data = {
            "work_content": "製造ライン作業、検品、梱包業務の補助作業",
            "responsibility_level": "通常業務",
            "worksite_name": "テスト工場",
            "worksite_address": "東京都千代田区",
            "supervisor_name": "田中太郎",
            "work_days": ["月", "火", "水", "木", "金"],
            "work_start_time": "08:00",
            "work_end_time": "17:00",
            "break_time_minutes": 60,
            "haken_moto_complaint_contact": {"department": "A", "name": "B"},
            "haken_saki_complaint_contact": {"department": "A", "name": "B"},
            "haken_moto_manager": {"department": "A", "name": "B"},
            "haken_saki_manager": {"department": "A", "name": "B"},
            "hourly_rate": 1500,
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=30)),
        }

        result = service.validate_contract_data(valid_data)
        assert result.compliance_score >= 70

        # Invalid data should have lower score
        invalid_data = {
            "dispatch_start_date": str(date.today()),
            "dispatch_end_date": str(date.today() + timedelta(days=30)),
        }

        result = service.validate_contract_data(invalid_data)
        assert result.compliance_score < 50


# =============================================================================
# ComplianceCheckerService Tests
# =============================================================================

class TestComplianceCheckerService:
    """Tests for compliance checker service."""

    def test_run_full_audit_empty_db(self, db: Session, test_factory: Factory):
        """Full audit on empty DB should return clean report."""
        service = ComplianceCheckerService(db)
        report = service.run_full_audit()

        assert isinstance(report, ComplianceReport)
        assert report.scope == "full"
        assert report.generated_at is not None

    def test_run_full_audit_with_contracts(
        self, db: Session, test_factory: Factory, test_employee: Employee
    ):
        """Audit should check all contracts."""
        # Create a test contract
        contract = KobetsuKeiyakusho(
            contract_number="KOB-202512-0001",
            factory_id=test_factory.id,
            contract_date=date.today(),
            dispatch_start_date=date.today(),
            dispatch_end_date=date.today() + timedelta(days=60),
            work_content="テスト業務内容です。最低文字数を満たす",
            responsibility_level="通常業務",
            worksite_name=test_factory.company_name,
            worksite_address="東京都",
            supervisor_department="製造部",
            supervisor_position="課長",
            supervisor_name="田中",
            work_days=["月", "火", "水", "木", "金"],
            work_start_time="08:00",
            work_end_time="17:00",
            break_time_minutes=60,
            hourly_rate=Decimal("1500"),
            overtime_rate=Decimal("1875"),
            haken_moto_complaint_contact={"department": "A", "name": "B"},
            haken_saki_complaint_contact={"department": "A", "name": "B"},
            haken_moto_manager={"department": "A", "name": "B"},
            haken_saki_manager={"department": "A", "name": "B"},
            status="active",
            number_of_workers=1,
        )
        db.add(contract)
        db.commit()

        service = ComplianceCheckerService(db)
        report = service.run_full_audit()

        assert report.contracts_audited >= 1

    def test_detect_expired_active_contracts(
        self, db: Session, test_factory: Factory
    ):
        """Should detect contracts that are expired but still active."""
        # Create expired but active contract
        contract = KobetsuKeiyakusho(
            contract_number="KOB-202512-0099",
            factory_id=test_factory.id,
            contract_date=date.today() - timedelta(days=100),
            dispatch_start_date=date.today() - timedelta(days=90),
            dispatch_end_date=date.today() - timedelta(days=10),  # Expired
            work_content="テスト業務内容",
            responsibility_level="通常",
            worksite_name=test_factory.company_name,
            worksite_address="住所",
            supervisor_department="部署",
            supervisor_position="課長",
            supervisor_name="担当者",
            work_days=["月"],
            work_start_time="08:00",
            work_end_time="17:00",
            break_time_minutes=60,
            hourly_rate=Decimal("1500"),
            overtime_rate=Decimal("1875"),
            haken_moto_complaint_contact={"department": "A", "name": "B"},
            haken_saki_complaint_contact={"department": "A", "name": "B"},
            haken_moto_manager={"department": "A", "name": "B"},
            haken_saki_manager={"department": "A", "name": "B"},
            status="active",  # Should be expired!
            number_of_workers=1,
        )
        db.add(contract)
        db.commit()

        service = ComplianceCheckerService(db)
        report = service.run_full_audit()

        # Should find the expired-but-active violation
        violation_types = [v.violation_type for v in report.violations]
        assert "EXPIRED_CONTRACT_ACTIVE" in violation_types

    def test_detect_missing_factory_fields(self, db: Session):
        """Should detect factories with missing required fields."""
        # Create factory without required fields
        factory = Factory(
            factory_id="TEST_INCOMPLETE",
            company_name="不完全テスト株式会社",
            plant_name="本社",
            is_active=True,
            # Missing: client_responsible_name, client_complaint_name, etc.
        )
        db.add(factory)
        db.commit()

        service = ComplianceCheckerService(db)
        report = service.run_full_audit()

        # Should find missing field violations
        factory_violations = [
            v for v in report.violations if v.category == "factory"
        ]
        assert len(factory_violations) > 0

    def test_detect_visa_expiration(self, db: Session, test_factory: Factory):
        """Should detect employees with expired visas."""
        # Create foreign employee with expired visa
        employee = Employee(
            employee_number="VISA001",
            full_name_kanji="グエン テスト",
            full_name_kana="グエン テスト",
            gender="male",
            nationality="ベトナム",
            date_of_birth=date(1990, 1, 1),
            status="active",
            factory_id=test_factory.id,
            visa_expiry_date=date.today() - timedelta(days=5),  # Expired
        )
        db.add(employee)
        db.commit()

        service = ComplianceCheckerService(db)
        report = service.run_full_audit()

        # Should find visa expiration violation
        visa_violations = [
            v for v in report.violations if "VISA" in v.violation_type
        ]
        assert len(visa_violations) > 0

    def test_compliance_summary_quick_check(self, db: Session, test_factory: Factory):
        """Quick compliance summary should return essential stats."""
        service = ComplianceCheckerService(db)
        summary = service.get_compliance_summary()

        assert "quick_score" in summary
        assert "active_contracts" in summary
        assert "expired_but_active" in summary
        assert "status" in summary
        assert summary["quick_score"] >= 0
        assert summary["quick_score"] <= 100

    def test_audit_contracts_only(self, db: Session, test_factory: Factory):
        """Should be able to audit only contracts."""
        service = ComplianceCheckerService(db)
        report = service.audit_contracts_only(status="active")

        assert report.scope == "contracts"
        assert report.factories_audited == 0


# =============================================================================
# AlertManagerService Tests
# =============================================================================

class TestAlertManagerService:
    """Tests for alert manager service."""

    def test_get_all_alerts_empty_db(self, db: Session, test_factory: Factory):
        """Empty DB should return empty alert summary."""
        service = AlertManagerService(db)
        summary = service.get_all_alerts()

        assert isinstance(summary, AlertSummary)
        assert summary.generated_at is not None

    def test_detect_expiring_contracts(
        self, db: Session, test_factory: Factory
    ):
        """Should detect contracts expiring soon."""
        # Create contract expiring in 7 days
        contract = KobetsuKeiyakusho(
            contract_number="KOB-EXPIRE-001",
            factory_id=test_factory.id,
            contract_date=date.today(),
            dispatch_start_date=date.today() - timedelta(days=30),
            dispatch_end_date=date.today() + timedelta(days=7),  # 7 days left
            work_content="テスト業務",
            responsibility_level="通常",
            worksite_name=test_factory.company_name,
            worksite_address="住所",
            supervisor_department="部署",
            supervisor_position="課長",
            supervisor_name="担当者",
            work_days=["月"],
            work_start_time="08:00",
            work_end_time="17:00",
            break_time_minutes=60,
            hourly_rate=Decimal("1500"),
            overtime_rate=Decimal("1875"),
            haken_moto_complaint_contact={"department": "A", "name": "B"},
            haken_saki_complaint_contact={"department": "A", "name": "B"},
            haken_moto_manager={"department": "A", "name": "B"},
            haken_saki_manager={"department": "A", "name": "B"},
            status="active",
            number_of_workers=1,
        )
        db.add(contract)
        db.commit()

        service = AlertManagerService(db)
        alerts = service.check_expiring_contracts()

        # Should find the expiring contract
        assert len(alerts) >= 1
        assert any(a.type == AlertType.CONTRACT_EXPIRING for a in alerts)

    def test_detect_expired_contracts(
        self, db: Session, test_factory: Factory
    ):
        """Should detect expired but active contracts."""
        # Create expired contract
        contract = KobetsuKeiyakusho(
            contract_number="KOB-EXPIRED-001",
            factory_id=test_factory.id,
            contract_date=date.today() - timedelta(days=100),
            dispatch_start_date=date.today() - timedelta(days=90),
            dispatch_end_date=date.today() - timedelta(days=5),  # Expired
            work_content="テスト業務",
            responsibility_level="通常",
            worksite_name=test_factory.company_name,
            worksite_address="住所",
            supervisor_department="部署",
            supervisor_position="課長",
            supervisor_name="担当者",
            work_days=["月"],
            work_start_time="08:00",
            work_end_time="17:00",
            break_time_minutes=60,
            hourly_rate=Decimal("1500"),
            overtime_rate=Decimal("1875"),
            haken_moto_complaint_contact={"department": "A", "name": "B"},
            haken_saki_complaint_contact={"department": "A", "name": "B"},
            haken_moto_manager={"department": "A", "name": "B"},
            haken_saki_manager={"department": "A", "name": "B"},
            status="active",  # Still active!
            number_of_workers=1,
        )
        db.add(contract)
        db.commit()

        service = AlertManagerService(db)
        alerts = service.check_expired_contracts()

        assert len(alerts) >= 1
        assert any(a.type == AlertType.CONTRACT_EXPIRED for a in alerts)
        assert any(a.priority == AlertPriority.CRITICAL for a in alerts)

    def test_detect_unassigned_employees(
        self, db: Session, test_factory: Factory, test_employee: Employee
    ):
        """Should detect employees without active contracts."""
        # test_employee is not assigned to any contract
        service = AlertManagerService(db)
        alerts = service.check_unassigned_employees()

        assert len(alerts) >= 1
        assert any(a.type == AlertType.EMPLOYEE_UNASSIGNED for a in alerts)
        assert any(a.entity_id == test_employee.id for a in alerts)

    def test_detect_incomplete_factories(self, db: Session):
        """Should detect factories missing required fields."""
        # Create incomplete factory
        factory = Factory(
            factory_id="INCOMPLETE_TEST",
            company_name="不完全株式会社",
            plant_name="工場",
            is_active=True,
            # Missing required fields
        )
        db.add(factory)
        db.commit()

        service = AlertManagerService(db)
        alerts = service.check_incomplete_factories()

        # Should find the incomplete factory
        assert len(alerts) >= 1
        assert any(a.type == AlertType.FACTORY_INCOMPLETE for a in alerts)

    def test_detect_approaching_conflict_dates(self, db: Session):
        """Should detect factories with approaching conflict dates."""
        # Create factory with conflict date in 30 days
        factory = Factory(
            factory_id="CONFLICT_TEST",
            company_name="抵触日テスト株式会社",
            plant_name="工場",
            is_active=True,
            conflict_date=date.today() + timedelta(days=30),
        )
        db.add(factory)
        db.commit()

        service = AlertManagerService(db)
        alerts = service.check_approaching_conflict_dates()

        assert len(alerts) >= 1
        assert any(a.type == AlertType.CONFLICT_DATE_APPROACHING for a in alerts)

    def test_detect_expiring_visas(self, db: Session, test_factory: Factory):
        """Should detect employees with expiring visas."""
        # Create foreign employee with visa expiring soon
        employee = Employee(
            employee_number="VISA_EXPIRE_001",
            full_name_kanji="テスト 外国人",
            full_name_kana="テスト ガイコクジン",
            gender="male",
            nationality="ベトナム",
            date_of_birth=date(1990, 1, 1),
            status="active",
            factory_id=test_factory.id,
            visa_type="技能実習",
            visa_expiry_date=date.today() + timedelta(days=20),  # 20 days left
        )
        db.add(employee)
        db.commit()

        service = AlertManagerService(db)
        alerts = service.check_expiring_visas()

        assert len(alerts) >= 1
        assert any(a.type == AlertType.VISA_EXPIRING for a in alerts)

    def test_daily_summary_structure(self, db: Session, test_factory: Factory):
        """Daily summary should have correct structure."""
        service = AlertManagerService(db)
        summary = service.get_daily_summary()

        assert "date" in summary
        assert "counts" in summary
        assert "highlights" in summary
        assert "top_priorities" in summary

        assert "critical" in summary["counts"]
        assert "high" in summary["counts"]
        assert "total_action_required" in summary["counts"]

    def test_get_alerts_for_entity(
        self, db: Session, test_factory: Factory, test_employee: Employee
    ):
        """Should filter alerts for specific entity."""
        service = AlertManagerService(db)

        # Get alerts for test_employee
        alerts = service.get_alerts_for_entity("employee", test_employee.id)

        # All returned alerts should be for this employee
        for alert in alerts:
            assert alert.entity_type == "employee"
            assert alert.entity_id == test_employee.id

    def test_alert_priority_sorting(self, db: Session, test_factory: Factory):
        """Alerts should be sorted by priority."""
        # Create multiple contracts with different expiration dates
        for i, days in enumerate([1, 7, 15, 30]):
            contract = KobetsuKeiyakusho(
                contract_number=f"KOB-SORT-{i:03d}",
                factory_id=test_factory.id,
                contract_date=date.today(),
                dispatch_start_date=date.today() - timedelta(days=30),
                dispatch_end_date=date.today() + timedelta(days=days),
                work_content="テスト業務",
                responsibility_level="通常",
                worksite_name=test_factory.company_name,
                worksite_address="住所",
                supervisor_department="部署",
                supervisor_position="課長",
                supervisor_name="担当者",
                work_days=["月"],
                work_start_time="08:00",
                work_end_time="17:00",
                break_time_minutes=60,
                hourly_rate=Decimal("1500"),
                overtime_rate=Decimal("1875"),
                haken_moto_complaint_contact={"department": "A", "name": "B"},
                haken_saki_complaint_contact={"department": "A", "name": "B"},
                haken_moto_manager={"department": "A", "name": "B"},
                haken_saki_manager={"department": "A", "name": "B"},
                status="active",
                number_of_workers=1,
            )
            db.add(contract)
        db.commit()

        service = AlertManagerService(db)
        summary = service.get_all_alerts()

        # Critical should be sorted by expires_in_days
        if len(summary.critical) > 1:
            for i in range(len(summary.critical) - 1):
                days1 = summary.critical[i].expires_in_days or 999
                days2 = summary.critical[i + 1].expires_in_days or 999
                assert days1 <= days2


# =============================================================================
# Integration Tests
# =============================================================================

class TestAgentServicesIntegration:
    """Integration tests across multiple services."""

    def test_validator_and_compliance_consistency(
        self, db: Session, test_factory: Factory, test_employee: Employee
    ):
        """Validator and compliance checker should agree on issues."""
        # Create contract with issues
        contract = KobetsuKeiyakusho(
            contract_number="KOB-INTEG-001",
            factory_id=test_factory.id,
            contract_date=date.today() - timedelta(days=100),
            dispatch_start_date=date.today() - timedelta(days=90),
            dispatch_end_date=date.today() - timedelta(days=10),  # Expired
            work_content="A",  # Too short
            responsibility_level="通常",
            worksite_name=test_factory.company_name,
            worksite_address="住所",
            supervisor_department="部署",
            supervisor_position="課長",
            supervisor_name="担当者",
            work_days=["月"],
            work_start_time="08:00",
            work_end_time="17:00",
            break_time_minutes=60,
            hourly_rate=Decimal("1500"),
            overtime_rate=Decimal("1875"),
            haken_moto_complaint_contact={"department": "A", "name": "B"},
            haken_saki_complaint_contact={"department": "A", "name": "B"},
            haken_moto_manager={"department": "A", "name": "B"},
            haken_saki_manager={"department": "A", "name": "B"},
            status="active",
            number_of_workers=1,
        )
        db.add(contract)
        db.commit()

        # Both services should detect issues
        validator = ContractValidatorService(db)
        validation = validator.validate_existing_contract(contract.id)

        checker = ComplianceCheckerService(db)
        report = checker.run_full_audit()

        # Validator should find issues
        assert len(validation.warnings) > 0 or not validation.is_valid

        # Compliance checker should also find the expired contract
        expired_violations = [
            v for v in report.violations if "EXPIRED" in v.violation_type
        ]
        assert len(expired_violations) > 0

    def test_alerts_match_compliance_issues(
        self, db: Session, test_factory: Factory
    ):
        """Alert manager should generate alerts for compliance issues."""
        # Create expired contract
        contract = KobetsuKeiyakusho(
            contract_number="KOB-ALERT-COMP-001",
            factory_id=test_factory.id,
            contract_date=date.today() - timedelta(days=100),
            dispatch_start_date=date.today() - timedelta(days=90),
            dispatch_end_date=date.today() - timedelta(days=5),
            work_content="テスト業務",
            responsibility_level="通常",
            worksite_name=test_factory.company_name,
            worksite_address="住所",
            supervisor_department="部署",
            supervisor_position="課長",
            supervisor_name="担当者",
            work_days=["月"],
            work_start_time="08:00",
            work_end_time="17:00",
            break_time_minutes=60,
            hourly_rate=Decimal("1500"),
            overtime_rate=Decimal("1875"),
            haken_moto_complaint_contact={"department": "A", "name": "B"},
            haken_saki_complaint_contact={"department": "A", "name": "B"},
            haken_moto_manager={"department": "A", "name": "B"},
            haken_saki_manager={"department": "A", "name": "B"},
            status="active",
            number_of_workers=1,
        )
        db.add(contract)
        db.commit()

        # Check compliance
        checker = ComplianceCheckerService(db)
        report = checker.run_full_audit()

        # Check alerts
        alert_manager = AlertManagerService(db)
        alerts = alert_manager.get_all_alerts()

        # Both should detect the expired contract
        compliance_expired = any(
            "EXPIRED" in v.violation_type for v in report.violations
        )
        alert_expired = any(
            a.type == AlertType.CONTRACT_EXPIRED
            for a in alerts.critical + alerts.high
        )

        assert compliance_expired
        assert alert_expired
