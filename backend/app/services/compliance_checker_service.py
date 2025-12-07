"""
Compliance Checker Service - コンプライアンスチェックサービス

Audits the entire system for compliance with 労働者派遣法第26条
and other Japanese labor regulations.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.factory import Factory
from app.models.employee import Employee
from app.services.contract_validator_service import ContractValidatorService, ValidationResult


@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""
    violation_id: str
    severity: str  # critical, high, medium, low
    category: str  # contract, factory, employee, system
    entity_type: str
    entity_id: int
    entity_name: str
    violation_type: str
    message: str
    legal_reference: str = ""
    remediation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "violation_id": self.violation_id,
            "severity": self.severity,
            "category": self.category,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "violation_type": self.violation_type,
            "message": self.message,
            "legal_reference": self.legal_reference,
            "remediation": self.remediation,
            "metadata": self.metadata
        }


@dataclass
class ComplianceReport:
    """Complete compliance audit report."""
    report_id: str
    generated_at: datetime
    period_start: Optional[date]
    period_end: Optional[date]
    scope: str  # "full", "contracts", "factories", "employees"

    total_entities_audited: int = 0
    compliance_score: int = 100

    violations: List[ComplianceViolation] = field(default_factory=list)
    warnings: List[ComplianceViolation] = field(default_factory=list)

    contracts_audited: int = 0
    contracts_compliant: int = 0
    factories_audited: int = 0
    factories_compliant: int = 0
    employees_audited: int = 0

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "period": {
                "start": str(self.period_start) if self.period_start else None,
                "end": str(self.period_end) if self.period_end else None
            },
            "scope": self.scope,
            "summary": {
                "total_entities_audited": self.total_entities_audited,
                "compliance_score": self.compliance_score,
                "violations_count": len(self.violations),
                "warnings_count": len(self.warnings),
                "by_severity": {
                    "critical": len([v for v in self.violations if v.severity == "critical"]),
                    "high": len([v for v in self.violations if v.severity == "high"]),
                    "medium": len([v for v in self.violations if v.severity == "medium"]),
                    "low": len([v for v in self.violations if v.severity == "low"])
                }
            },
            "contracts": {
                "audited": self.contracts_audited,
                "compliant": self.contracts_compliant,
                "compliance_rate": round(self.contracts_compliant / self.contracts_audited * 100, 1) if self.contracts_audited > 0 else 100
            },
            "factories": {
                "audited": self.factories_audited,
                "compliant": self.factories_compliant,
                "compliance_rate": round(self.factories_compliant / self.factories_audited * 100, 1) if self.factories_audited > 0 else 100
            },
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings]
        }


class ComplianceCheckerService:
    """
    Audits the system for compliance with Japanese labor dispatch laws.

    Performs comprehensive checks on:
    - All 16 required contract fields (労働者派遣法第26条)
    - Contract duration limits (労働者派遣法第40条の2)
    - Overtime limits (36協定)
    - Factory configuration completeness
    - Employee documentation
    """

    def __init__(self, db: Session):
        self.db = db
        self.validator = ContractValidatorService(db)

    def run_full_audit(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        factory_id: Optional[int] = None
    ) -> ComplianceReport:
        """
        Run a complete compliance audit.

        Args:
            start_date: Start of period to audit (default: all time)
            end_date: End of period to audit (default: today)
            factory_id: Limit audit to specific factory

        Returns:
            ComplianceReport with all findings
        """
        report_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        report = ComplianceReport(
            report_id=report_id,
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date or date.today(),
            scope="full"
        )

        # 1. Audit contracts
        self._audit_contracts(report, start_date, end_date, factory_id)

        # 2. Audit factories
        self._audit_factories(report, factory_id)

        # 3. Audit employees
        self._audit_employees(report, factory_id)

        # Calculate overall compliance score
        report.compliance_score = self._calculate_overall_score(report)
        report.total_entities_audited = (
            report.contracts_audited +
            report.factories_audited +
            report.employees_audited
        )

        return report

    def audit_contracts_only(
        self,
        status: str = "active",
        factory_id: Optional[int] = None
    ) -> ComplianceReport:
        """Audit only contracts."""
        report = ComplianceReport(
            report_id=f"CONTRACT-AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            generated_at=datetime.now(),
            period_start=None,
            period_end=date.today(),
            scope="contracts"
        )

        self._audit_contracts(report, status=status, factory_id=factory_id)
        report.compliance_score = self._calculate_overall_score(report)
        report.total_entities_audited = report.contracts_audited

        return report

    def _audit_contracts(
        self,
        report: ComplianceReport,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        factory_id: Optional[int] = None,
        status: str = None
    ):
        """Audit all contracts for compliance."""
        query = self.db.query(KobetsuKeiyakusho)

        if status:
            query = query.filter(KobetsuKeiyakusho.status == status)
        if factory_id:
            query = query.filter(KobetsuKeiyakusho.factory_id == factory_id)
        if start_date:
            query = query.filter(KobetsuKeiyakusho.dispatch_start_date >= start_date)
        if end_date:
            query = query.filter(KobetsuKeiyakusho.dispatch_end_date <= end_date)

        contracts = query.all()
        report.contracts_audited = len(contracts)
        compliant_count = 0

        for contract in contracts:
            # Validate using the validator service
            validation = self.validator.validate_existing_contract(contract.id)

            if validation.is_valid:
                compliant_count += 1
            else:
                # Convert validation errors to violations
                for error in validation.errors:
                    report.violations.append(ComplianceViolation(
                        violation_id=f"CONTRACT-{contract.id}-{error.code}",
                        severity=self._map_severity(error.severity),
                        category="contract",
                        entity_type="contract",
                        entity_id=contract.id,
                        entity_name=contract.contract_number,
                        violation_type=error.code,
                        message=error.message,
                        legal_reference="労働者派遣法第26条" if "REQUIRED" in error.code else "",
                        remediation=error.suggestion or f"{error.japanese_name}を入力してください",
                        metadata={
                            "field": error.field,
                            "value": error.value
                        }
                    ))

            # Add warnings
            for warning in validation.warnings:
                report.warnings.append(ComplianceViolation(
                    violation_id=f"CONTRACT-{contract.id}-{warning.code}",
                    severity="low",
                    category="contract",
                    entity_type="contract",
                    entity_id=contract.id,
                    entity_name=contract.contract_number,
                    violation_type=warning.code,
                    message=warning.message,
                    remediation=warning.suggestion or "",
                    metadata={
                        "field": warning.field,
                        "value": warning.value
                    }
                ))

            # Additional contract-specific checks
            self._check_contract_expiration(contract, report)
            self._check_contract_duration(contract, report)

        report.contracts_compliant = compliant_count

    def _audit_factories(
        self,
        report: ComplianceReport,
        factory_id: Optional[int] = None
    ):
        """Audit factories for completeness."""
        query = self.db.query(Factory).filter(Factory.is_active == True)

        if factory_id:
            query = query.filter(Factory.id == factory_id)

        factories = query.all()
        report.factories_audited = len(factories)
        compliant_count = 0

        required_fields = [
            ("client_responsible_name", "派遣先責任者", "high"),
            ("client_responsible_department", "派遣先責任者部署", "medium"),
            ("client_complaint_name", "派遣先苦情処理担当", "high"),
            ("dispatch_responsible_name", "派遣元責任者", "high"),
            ("dispatch_complaint_name", "派遣元苦情処理担当", "medium"),
            ("company_address", "会社住所", "medium"),
            ("plant_address", "工場住所", "medium"),
        ]

        for factory in factories:
            factory_violations = []

            for field_name, japanese_name, severity in required_fields:
                if not getattr(factory, field_name, None):
                    factory_violations.append(ComplianceViolation(
                        violation_id=f"FACTORY-{factory.id}-{field_name}",
                        severity=severity,
                        category="factory",
                        entity_type="factory",
                        entity_id=factory.id,
                        entity_name=f"{factory.company_name} {factory.plant_name}",
                        violation_type="MISSING_REQUIRED_FIELD",
                        message=f"{japanese_name}が設定されていません",
                        legal_reference="労働者派遣法第26条",
                        remediation=f"工場情報で{japanese_name}を設定してください"
                    ))

            # Check conflict date
            if factory.conflict_date:
                days_until = (factory.conflict_date - date.today()).days
                if days_until < 0:
                    factory_violations.append(ComplianceViolation(
                        violation_id=f"FACTORY-{factory.id}-CONFLICT_DATE_PASSED",
                        severity="critical",
                        category="factory",
                        entity_type="factory",
                        entity_id=factory.id,
                        entity_name=f"{factory.company_name} {factory.plant_name}",
                        violation_type="CONFLICT_DATE_PASSED",
                        message=f"抵触日（{factory.conflict_date}）を過ぎています",
                        legal_reference="労働者派遣法第40条の2",
                        remediation="新しい抵触日を設定するか、派遣を終了してください"
                    ))
                elif days_until <= 30:
                    report.warnings.append(ComplianceViolation(
                        violation_id=f"FACTORY-{factory.id}-CONFLICT_DATE_SOON",
                        severity="high",
                        category="factory",
                        entity_type="factory",
                        entity_id=factory.id,
                        entity_name=f"{factory.company_name} {factory.plant_name}",
                        violation_type="CONFLICT_DATE_APPROACHING",
                        message=f"抵触日まで{days_until}日です",
                        remediation="派遣期間の終了を計画してください"
                    ))

            if not factory_violations:
                compliant_count += 1
            else:
                report.violations.extend(factory_violations)

        report.factories_compliant = compliant_count

    def _audit_employees(
        self,
        report: ComplianceReport,
        factory_id: Optional[int] = None
    ):
        """Audit employees for documentation compliance."""
        query = self.db.query(Employee).filter(Employee.status == 'active')

        if factory_id:
            query = query.filter(Employee.factory_id == factory_id)

        employees = query.all()
        report.employees_audited = len(employees)

        today = date.today()

        for emp in employees:
            # Check visa expiration for foreign workers
            if emp.nationality and emp.nationality not in ["日本", "日本人", "Japanese"]:
                if emp.visa_expiry_date:
                    days_until = (emp.visa_expiry_date - today).days
                    if days_until < 0:
                        report.violations.append(ComplianceViolation(
                            violation_id=f"EMPLOYEE-{emp.id}-VISA_EXPIRED",
                            severity="critical",
                            category="employee",
                            entity_type="employee",
                            entity_id=emp.id,
                            entity_name=emp.full_name_kanji,
                            violation_type="VISA_EXPIRED",
                            message=f"ビザが{-days_until}日前に期限切れです",
                            legal_reference="入管法",
                            remediation="ビザの更新を確認してください",
                            metadata={"employee_number": emp.employee_number}
                        ))
                    elif days_until <= 30:
                        report.warnings.append(ComplianceViolation(
                            violation_id=f"EMPLOYEE-{emp.id}-VISA_EXPIRING",
                            severity="high",
                            category="employee",
                            entity_type="employee",
                            entity_id=emp.id,
                            entity_name=emp.full_name_kanji,
                            violation_type="VISA_EXPIRING",
                            message=f"ビザ期限まで{days_until}日",
                            remediation="ビザ更新手続きを開始してください"
                        ))
                elif not emp.visa_type:
                    report.warnings.append(ComplianceViolation(
                        violation_id=f"EMPLOYEE-{emp.id}-NO_VISA_INFO",
                        severity="medium",
                        category="employee",
                        entity_type="employee",
                        entity_id=emp.id,
                        entity_name=emp.full_name_kanji,
                        violation_type="MISSING_VISA_INFO",
                        message="ビザ情報が登録されていません",
                        remediation="ビザ種類と期限を登録してください"
                    ))

    def _check_contract_expiration(self, contract: KobetsuKeiyakusho, report: ComplianceReport):
        """Check if contract has expired but status is still active."""
        if contract.status == 'active' and contract.dispatch_end_date < date.today():
            report.violations.append(ComplianceViolation(
                violation_id=f"CONTRACT-{contract.id}-EXPIRED_ACTIVE",
                severity="critical",
                category="contract",
                entity_type="contract",
                entity_id=contract.id,
                entity_name=contract.contract_number,
                violation_type="EXPIRED_CONTRACT_ACTIVE",
                message=f"契約期限（{contract.dispatch_end_date}）が過ぎていますが、ステータスがactiveです",
                remediation="契約を更新するか、ステータスを'expired'に変更してください"
            ))

    def _check_contract_duration(self, contract: KobetsuKeiyakusho, report: ComplianceReport):
        """Check contract duration against legal limits."""
        duration_days = (contract.dispatch_end_date - contract.dispatch_start_date).days

        if duration_days > 365 * 3:
            report.violations.append(ComplianceViolation(
                violation_id=f"CONTRACT-{contract.id}-DURATION_EXCEEDED",
                severity="critical",
                category="contract",
                entity_type="contract",
                entity_id=contract.id,
                entity_name=contract.contract_number,
                violation_type="DURATION_EXCEEDED",
                message=f"契約期間（{duration_days}日）が3年を超えています",
                legal_reference="労働者派遣法第40条の2",
                remediation="契約期間を3年以内に修正してください"
            ))

    def _map_severity(self, validation_severity: str) -> str:
        """Map validation severity to compliance severity."""
        mapping = {
            "error": "high",
            "warning": "low"
        }
        return mapping.get(validation_severity, "medium")

    def _calculate_overall_score(self, report: ComplianceReport) -> int:
        """Calculate overall compliance score (0-100)."""
        if report.total_entities_audited == 0:
            return 100

        # Weight violations by severity
        weights = {
            "critical": 20,
            "high": 10,
            "medium": 5,
            "low": 2
        }

        total_penalty = sum(
            weights.get(v.severity, 5)
            for v in report.violations
        )

        # Add small penalty for warnings
        total_penalty += len(report.warnings) * 1

        # Max possible score reduction
        max_penalty = report.total_entities_audited * 20

        score = max(0, 100 - (total_penalty / max_penalty * 100))
        return int(score)

    def get_compliance_summary(self) -> dict:
        """Get a quick compliance summary without full audit."""
        today = date.today()

        # Quick counts
        active_contracts = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.status == 'active'
        ).count()

        expired_but_active = self.db.query(KobetsuKeiyakusho).filter(
            and_(
                KobetsuKeiyakusho.status == 'active',
                KobetsuKeiyakusho.dispatch_end_date < today
            )
        ).count()

        factories_missing_info = self.db.query(Factory).filter(
            and_(
                Factory.is_active == True,
                or_(
                    Factory.client_responsible_name.is_(None),
                    Factory.client_complaint_name.is_(None),
                    Factory.dispatch_responsible_name.is_(None)
                )
            )
        ).count()

        # Quick score estimate
        issues = expired_but_active * 20 + factories_missing_info * 10
        total = active_contracts + self.db.query(Factory).filter(Factory.is_active == True).count()
        quick_score = max(0, 100 - (issues / max(total, 1) * 100)) if total > 0 else 100

        return {
            "quick_score": int(quick_score),
            "active_contracts": active_contracts,
            "expired_but_active": expired_but_active,
            "factories_missing_info": factories_missing_info,
            "status": "COMPLIANT" if expired_but_active == 0 and factories_missing_info == 0 else "ISSUES_FOUND",
            "recommendation": "監査を実行して詳細を確認してください" if quick_score < 90 else "システムは準拠しています",
            "generated_at": datetime.now().isoformat()
        }
