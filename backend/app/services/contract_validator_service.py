"""
Contract Validator Service - 契約検証サービス

Validates 個別契約書 contracts for compliance with 労働者派遣法第26条.
Ensures all 16 legally required fields are present and valid.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.factory import Factory
from app.models.employee import Employee


@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    code: str
    message: str
    japanese_name: str
    severity: str = "error"  # error, warning
    value: Any = None
    suggestion: str = ""

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "japanese_name": self.japanese_name,
            "severity": self.severity,
            "value": str(self.value) if self.value is not None else None,
            "suggestion": self.suggestion
        }


@dataclass
class ValidationResult:
    """Result of contract validation."""
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    fields_checked: int = 0
    fields_valid: int = 0
    compliance_score: int = 100

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "fields_checked": self.fields_checked,
            "fields_valid": self.fields_valid,
            "compliance_score": self.compliance_score
        }


# The 16 required fields according to 労働者派遣法第26条
REQUIRED_FIELDS = [
    # (field_name, japanese_name, validation_type, min_length)
    ("work_content", "業務の内容", "text", 5),
    ("responsibility_level", "責任の程度", "text", 2),
    ("worksite_name", "派遣先事業所名", "text", 2),
    ("worksite_address", "事業所住所", "text", 5),
    ("supervisor_name", "指揮命令者", "text", 2),
    ("work_days", "就業日", "json_array", 1),
    ("work_start_time", "始業時刻", "time", None),
    ("work_end_time", "終業時刻", "time", None),
    ("break_time_minutes", "休憩時間", "integer", None),
    ("safety_measures", "安全衛生", "text_optional", 0),  # Can be null but should have value
    ("haken_moto_complaint_contact", "派遣元苦情処理担当", "json_object", None),
    ("haken_saki_complaint_contact", "派遣先苦情処理担当", "json_object", None),
    ("termination_measures", "契約解除の措置", "text_optional", 0),
    ("haken_moto_manager", "派遣元責任者", "json_object", None),
    ("haken_saki_manager", "派遣先責任者", "json_object", None),
    ("hourly_rate", "派遣料金", "decimal", None),
]


class ContractValidatorService:
    """
    Validates contracts for legal compliance.

    Checks all 16 legally required fields according to 労働者派遣法第26条.
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_contract_data(
        self,
        data: dict,
        factory_id: Optional[int] = None,
        employee_ids: Optional[List[int]] = None,
        is_update: bool = False
    ) -> ValidationResult:
        """
        Validate contract data before creation or update.

        Args:
            data: Contract data dictionary
            factory_id: Associated factory ID
            employee_ids: List of employee IDs to assign
            is_update: Whether this is an update (some fields may be optional)

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()

        # 1. Validate required fields (16 legal fields)
        self._validate_required_fields(data, result)

        # 2. Validate dates
        self._validate_dates(data, result)

        # 3. Validate factory consistency
        if factory_id:
            self._validate_factory_consistency(factory_id, data, result)

        # 4. Validate employee availability
        if employee_ids:
            self._validate_employee_availability(
                employee_ids,
                data.get("dispatch_start_date"),
                data.get("dispatch_end_date"),
                result
            )

        # 5. Validate overtime limits
        self._validate_overtime_limits(data, result)

        # 6. Validate rates
        self._validate_rates(data, result)

        # Calculate compliance score
        result.compliance_score = self._calculate_compliance_score(result)
        result.is_valid = len(result.errors) == 0

        return result

    def validate_existing_contract(self, contract_id: int) -> ValidationResult:
        """
        Validate an existing contract in the database.

        Args:
            contract_id: ID of the contract to validate

        Returns:
            ValidationResult
        """
        contract = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.id == contract_id
        ).first()

        if not contract:
            result = ValidationResult(is_valid=False)
            result.errors.append(ValidationError(
                field="contract_id",
                code="CONTRACT_NOT_FOUND",
                message=f"Contract {contract_id} not found",
                japanese_name="契約ID"
            ))
            return result

        # Convert contract to dict for validation
        data = {
            "work_content": contract.work_content,
            "responsibility_level": contract.responsibility_level,
            "worksite_name": contract.worksite_name,
            "worksite_address": contract.worksite_address,
            "supervisor_name": contract.supervisor_name,
            "supervisor_department": contract.supervisor_department,
            "supervisor_position": contract.supervisor_position,
            "work_days": contract.work_days,
            "work_start_time": contract.work_start_time,
            "work_end_time": contract.work_end_time,
            "break_time_minutes": contract.break_time_minutes,
            "safety_measures": contract.safety_measures,
            "haken_moto_complaint_contact": contract.haken_moto_complaint_contact,
            "haken_saki_complaint_contact": contract.haken_saki_complaint_contact,
            "termination_measures": contract.termination_measures,
            "haken_moto_manager": contract.haken_moto_manager,
            "haken_saki_manager": contract.haken_saki_manager,
            "hourly_rate": contract.hourly_rate,
            "overtime_rate": contract.overtime_rate,
            "dispatch_start_date": contract.dispatch_start_date,
            "dispatch_end_date": contract.dispatch_end_date,
            "overtime_max_hours_day": contract.overtime_max_hours_day,
            "overtime_max_hours_month": contract.overtime_max_hours_month,
        }

        # Get employee IDs
        employee_ids = [ke.employee_id for ke in contract.employees]

        return self.validate_contract_data(
            data,
            factory_id=contract.factory_id,
            employee_ids=employee_ids
        )

    def _validate_required_fields(self, data: dict, result: ValidationResult):
        """Check all 16 required fields."""
        for field_name, japanese_name, val_type, min_length in REQUIRED_FIELDS:
            result.fields_checked += 1
            value = data.get(field_name)

            if val_type == "text":
                if not value or (isinstance(value, str) and not value.strip()):
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="REQUIRED_FIELD_MISSING",
                        message=f"{japanese_name}は必須です (労働者派遣法第26条)",
                        japanese_name=japanese_name,
                        severity="error"
                    ))
                elif min_length and len(str(value).strip()) < min_length:
                    result.warnings.append(ValidationError(
                        field=field_name,
                        code="FIELD_TOO_SHORT",
                        message=f"{japanese_name}が短すぎます（{min_length}文字以上推奨）",
                        japanese_name=japanese_name,
                        severity="warning",
                        value=value
                    ))
                else:
                    result.fields_valid += 1

            elif val_type == "text_optional":
                # Optional but should ideally have a value
                if not value:
                    result.warnings.append(ValidationError(
                        field=field_name,
                        code="OPTIONAL_FIELD_MISSING",
                        message=f"{japanese_name}の記載を推奨します",
                        japanese_name=japanese_name,
                        severity="warning"
                    ))
                else:
                    result.fields_valid += 1

            elif val_type == "json_array":
                if not value or not isinstance(value, list) or len(value) < min_length:
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="REQUIRED_FIELD_MISSING",
                        message=f"{japanese_name}は必須です",
                        japanese_name=japanese_name,
                        severity="error"
                    ))
                else:
                    result.fields_valid += 1

            elif val_type == "json_object":
                if not value or not isinstance(value, dict):
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="REQUIRED_FIELD_MISSING",
                        message=f"{japanese_name}は必須です (労働者派遣法第26条)",
                        japanese_name=japanese_name,
                        severity="error"
                    ))
                elif not value.get("name") and not value.get("department"):
                    result.warnings.append(ValidationError(
                        field=field_name,
                        code="INCOMPLETE_CONTACT_INFO",
                        message=f"{japanese_name}の情報が不完全です",
                        japanese_name=japanese_name,
                        severity="warning",
                        suggestion="担当者名と部署を入力してください"
                    ))
                else:
                    result.fields_valid += 1

            elif val_type == "time":
                if value is None:
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="REQUIRED_FIELD_MISSING",
                        message=f"{japanese_name}は必須です",
                        japanese_name=japanese_name,
                        severity="error"
                    ))
                else:
                    result.fields_valid += 1

            elif val_type == "integer":
                if value is None:
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="REQUIRED_FIELD_MISSING",
                        message=f"{japanese_name}は必須です",
                        japanese_name=japanese_name,
                        severity="error"
                    ))
                elif not isinstance(value, (int, float)) or value < 0:
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="INVALID_VALUE",
                        message=f"{japanese_name}は正の数値である必要があります",
                        japanese_name=japanese_name,
                        severity="error",
                        value=value
                    ))
                else:
                    result.fields_valid += 1

            elif val_type == "decimal":
                if value is None:
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="REQUIRED_FIELD_MISSING",
                        message=f"{japanese_name}は必須です",
                        japanese_name=japanese_name,
                        severity="error"
                    ))
                elif not isinstance(value, (int, float, Decimal)) or float(value) <= 0:
                    result.errors.append(ValidationError(
                        field=field_name,
                        code="INVALID_VALUE",
                        message=f"{japanese_name}は正の数値である必要があります",
                        japanese_name=japanese_name,
                        severity="error",
                        value=value
                    ))
                else:
                    result.fields_valid += 1

    def _validate_dates(self, data: dict, result: ValidationResult):
        """Validate contract dates."""
        start_date = data.get("dispatch_start_date")
        end_date = data.get("dispatch_end_date")

        if not start_date:
            result.errors.append(ValidationError(
                field="dispatch_start_date",
                code="REQUIRED_FIELD_MISSING",
                message="派遣開始日は必須です",
                japanese_name="派遣開始日"
            ))
            return

        if not end_date:
            result.errors.append(ValidationError(
                field="dispatch_end_date",
                code="REQUIRED_FIELD_MISSING",
                message="派遣終了日は必須です",
                japanese_name="派遣終了日"
            ))
            return

        # Convert to date if needed
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            from datetime import datetime
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # End must be after start
        if end_date <= start_date:
            result.errors.append(ValidationError(
                field="dispatch_end_date",
                code="INVALID_DATE_RANGE",
                message="派遣終了日は派遣開始日より後でなければなりません",
                japanese_name="派遣終了日",
                value=f"{start_date} → {end_date}"
            ))

        # Check max duration (3 years per 労働者派遣法第40条の2)
        duration_days = (end_date - start_date).days
        if duration_days > 365 * 3:
            result.errors.append(ValidationError(
                field="dispatch_end_date",
                code="DURATION_EXCEEDS_LIMIT",
                message="派遣期間は3年を超えることができません (労働者派遣法第40条の2)",
                japanese_name="派遣期間",
                severity="error",
                value=f"{duration_days}日"
            ))
        elif duration_days > 365:
            result.warnings.append(ValidationError(
                field="dispatch_end_date",
                code="LONG_DURATION",
                message=f"派遣期間が{duration_days}日（約{duration_days // 30}ヶ月）です",
                japanese_name="派遣期間",
                severity="warning"
            ))

    def _validate_factory_consistency(
        self,
        factory_id: int,
        data: dict,
        result: ValidationResult
    ):
        """Validate contract data is consistent with factory."""
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()

        if not factory:
            result.errors.append(ValidationError(
                field="factory_id",
                code="FACTORY_NOT_FOUND",
                message="指定された工場が見つかりません",
                japanese_name="工場ID"
            ))
            return

        # Check required factory fields
        if not factory.client_responsible_name:
            result.warnings.append(ValidationError(
                field="factory",
                code="FACTORY_INCOMPLETE",
                message=f"工場「{factory.company_name}」に派遣先責任者が設定されていません",
                japanese_name="工場設定",
                severity="warning",
                suggestion="工場情報を更新してください"
            ))

        # Check conflict date (抵触日)
        if factory.conflict_date:
            end_date = data.get("dispatch_end_date")
            if end_date:
                if isinstance(end_date, str):
                    from datetime import datetime
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

                if end_date > factory.conflict_date:
                    result.errors.append(ValidationError(
                        field="dispatch_end_date",
                        code="EXCEEDS_CONFLICT_DATE",
                        message=f"派遣終了日が抵触日（{factory.conflict_date}）を超えています",
                        japanese_name="抵触日",
                        severity="error",
                        value=f"終了日: {end_date}, 抵触日: {factory.conflict_date}"
                    ))

    def _validate_employee_availability(
        self,
        employee_ids: List[int],
        start_date: date,
        end_date: date,
        result: ValidationResult
    ):
        """Check if employees are available for the contract period."""
        if not employee_ids:
            return

        for emp_id in employee_ids:
            employee = self.db.query(Employee).filter(Employee.id == emp_id).first()

            if not employee:
                result.errors.append(ValidationError(
                    field="employee_ids",
                    code="EMPLOYEE_NOT_FOUND",
                    message=f"従業員ID {emp_id} が見つかりません",
                    japanese_name="従業員"
                ))
                continue

            # Check if employee is active
            if employee.status == "resigned":
                result.errors.append(ValidationError(
                    field="employee_ids",
                    code="EMPLOYEE_RESIGNED",
                    message=f"従業員「{employee.full_name_kanji}」は退社済みです",
                    japanese_name="従業員状態"
                ))
                continue

            # Check for overlapping contracts
            if start_date and end_date:
                overlapping = self.db.query(KobetsuKeiyakusho).join(
                    KobetsuEmployee
                ).filter(
                    KobetsuEmployee.employee_id == emp_id,
                    KobetsuKeiyakusho.dispatch_end_date >= start_date,
                    KobetsuKeiyakusho.dispatch_start_date <= end_date,
                    KobetsuKeiyakusho.status.in_(['active', 'draft'])
                ).first()

                if overlapping:
                    result.warnings.append(ValidationError(
                        field="employee_ids",
                        code="EMPLOYEE_OVERLAP",
                        message=f"従業員「{employee.full_name_kanji}」には期間が重複する契約があります ({overlapping.contract_number})",
                        japanese_name="契約重複",
                        severity="warning"
                    ))

    def _validate_overtime_limits(self, data: dict, result: ValidationResult):
        """Validate overtime settings against legal limits."""
        daily_max = data.get("overtime_max_hours_day")
        monthly_max = data.get("overtime_max_hours_month")

        # Legal limits from 36協定
        DAILY_LIMIT = Decimal("4")  # 4 hours/day typical limit
        MONTHLY_LIMIT = Decimal("45")  # 45 hours/month limit

        if daily_max and float(daily_max) > float(DAILY_LIMIT):
            result.warnings.append(ValidationError(
                field="overtime_max_hours_day",
                code="HIGH_DAILY_OVERTIME",
                message=f"1日の時間外労働上限（{daily_max}時間）が通常の上限を超えています",
                japanese_name="時間外労働（日）",
                severity="warning",
                value=daily_max
            ))

        if monthly_max and float(monthly_max) > float(MONTHLY_LIMIT):
            result.errors.append(ValidationError(
                field="overtime_max_hours_month",
                code="EXCEEDS_MONTHLY_LIMIT",
                message=f"1ヶ月の時間外労働上限（{monthly_max}時間）が法定上限（45時間）を超えています",
                japanese_name="時間外労働（月）",
                severity="error",
                value=monthly_max
            ))

    def _validate_rates(self, data: dict, result: ValidationResult):
        """Validate payment rates."""
        hourly = data.get("hourly_rate")
        overtime = data.get("overtime_rate")

        if hourly and overtime:
            # Overtime rate should be at least 1.25x hourly
            min_overtime = float(hourly) * 1.25
            if float(overtime) < min_overtime:
                result.warnings.append(ValidationError(
                    field="overtime_rate",
                    code="LOW_OVERTIME_RATE",
                    message=f"時間外単価（{overtime}）が基本単価の1.25倍未満です",
                    japanese_name="時間外単価",
                    severity="warning",
                    suggestion=f"推奨: {min_overtime:.0f}円以上"
                ))

        # Check for unreasonably low rates
        if hourly and float(hourly) < 900:
            result.warnings.append(ValidationError(
                field="hourly_rate",
                code="LOW_HOURLY_RATE",
                message=f"時給（{hourly}円）が最低賃金を下回っている可能性があります",
                japanese_name="時給",
                severity="warning"
            ))

    def _calculate_compliance_score(self, result: ValidationResult) -> int:
        """Calculate compliance score (0-100)."""
        if result.fields_checked == 0:
            return 0

        # Base score from field validation
        field_score = (result.fields_valid / result.fields_checked) * 100

        # Penalty for errors and warnings
        error_penalty = len(result.errors) * 10
        warning_penalty = len(result.warnings) * 2

        score = max(0, field_score - error_penalty - warning_penalty)
        return int(score)

    def get_validation_summary(self, contract_id: int) -> dict:
        """Get a human-readable validation summary for a contract."""
        result = self.validate_existing_contract(contract_id)

        contract = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.id == contract_id
        ).first()

        if not contract:
            return {"error": "Contract not found"}

        return {
            "contract_id": contract_id,
            "contract_number": contract.contract_number,
            "factory_name": contract.worksite_name,
            "validation": result.to_dict(),
            "status": "VALID" if result.is_valid else "INVALID",
            "recommendation": self._get_recommendation(result)
        }

    def _get_recommendation(self, result: ValidationResult) -> str:
        """Generate recommendation based on validation result."""
        if result.is_valid and len(result.warnings) == 0:
            return "契約は完全に準拠しています。"
        elif result.is_valid:
            return f"契約は有効ですが、{len(result.warnings)}件の改善点があります。"
        else:
            return f"{len(result.errors)}件のエラーを修正してください。"
