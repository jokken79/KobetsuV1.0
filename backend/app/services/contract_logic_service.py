"""
Contract Logic Service - 契約ロジックサービス

Handles business logic for Kobetsu Keiyakusho contracts:
1. 抵触日 (Conflict Date) validation
2. Contract assignment logic (new vs existing)
3. Date control and validation
4. Individual rate management
"""
from datetime import date, timedelta
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee


class ContractValidationError(Exception):
    """Custom exception for contract validation errors."""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ContractLogicService:
    """
    契約ロジックサービス

    Responsibilities:
    - Validate contract dates against 抵触日
    - Determine if employee should join existing contract or create new
    - Calculate individual rates
    - Handle mid-period entries and exits
    """

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # 抵触日 VALIDATION
    # ========================================

    def validate_against_conflict_date(
        self,
        factory_id: int,
        dispatch_end_date: date
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that dispatch_end_date does not exceed factory's conflict_date.

        Returns:
            Tuple of (is_valid, error_message)
        """
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory:
            return False, "工場が見つかりません"

        if not factory.conflict_date:
            # No conflict date set - warn but allow
            return True, "警告: この工場には抵触日が設定されていません"

        if dispatch_end_date > factory.conflict_date:
            days_over = (dispatch_end_date - factory.conflict_date).days
            return False, (
                f"派遣終了日 ({dispatch_end_date}) が抵触日 ({factory.conflict_date}) を超えています。"
                f"\n{days_over}日超過しています。"
                f"\n派遣終了日は抵触日以前に設定してください。"
            )

        # Calculate warning if close to conflict date
        days_until = (factory.conflict_date - dispatch_end_date).days
        if days_until <= 30:
            return True, f"注意: 抵触日まで残り{days_until}日です"

        return True, None

    def get_conflict_date_info(self, factory_id: int) -> dict:
        """
        Get conflict date information for a factory.

        Returns dict with:
        - conflict_date: The conflict date
        - days_remaining: Days until conflict date
        - is_expired: Whether conflict date has passed
        - warning_level: 'danger', 'warning', 'ok'
        """
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory or not factory.conflict_date:
            return {
                "conflict_date": None,
                "days_remaining": None,
                "is_expired": False,
                "warning_level": "unknown"
            }

        today = date.today()
        days_remaining = (factory.conflict_date - today).days

        if days_remaining < 0:
            warning_level = "expired"
            is_expired = True
        elif days_remaining <= 30:
            warning_level = "danger"
            is_expired = False
        elif days_remaining <= 90:
            warning_level = "warning"
            is_expired = False
        else:
            warning_level = "ok"
            is_expired = False

        return {
            "conflict_date": factory.conflict_date,
            "days_remaining": days_remaining,
            "is_expired": is_expired,
            "warning_level": warning_level,
            "message": self._get_conflict_date_message(days_remaining, is_expired)
        }

    def _get_conflict_date_message(self, days: int, is_expired: bool) -> str:
        """Generate human-readable message about conflict date."""
        if is_expired:
            return f"抵触日を{abs(days)}日超過しています。新規派遣はできません。"
        elif days <= 30:
            return f"抵触日まで残り{days}日！契約更新に注意してください。"
        elif days <= 90:
            return f"抵触日まで残り{days}日です。"
        else:
            return f"抵触日まで{days}日あります。"

    # ========================================
    # CONTRACT ASSIGNMENT LOGIC
    # ========================================

    def find_existing_contract(
        self,
        factory_id: int,
        factory_line_id: Optional[int],
        target_date: date
    ) -> Optional[KobetsuKeiyakusho]:
        """
        Find an existing active contract that an employee could join.

        Criteria:
        - Same factory (and optionally same line)
        - Status is 'active'
        - Target date falls within contract period
        """
        query = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.factory_id == factory_id,
            KobetsuKeiyakusho.status == 'active',
            KobetsuKeiyakusho.dispatch_start_date <= target_date,
            KobetsuKeiyakusho.dispatch_end_date >= target_date
        )

        # If line is specified, we might want to filter by work_content or organizational_unit
        # For now, return the first matching contract

        return query.first()

    def should_create_new_contract(
        self,
        employee: Employee,
        factory_id: int,
        factory_line_id: Optional[int],
        start_date: date,
        existing_contract: Optional[KobetsuKeiyakusho] = None
    ) -> Tuple[bool, str]:
        """
        Determine if a new contract should be created or employee added to existing.

        Reasons to create new contract:
        1. No existing contract found
        2. Employee's rate differs significantly from contract rate
        3. Different work content
        4. Different organizational unit

        Returns:
            Tuple of (should_create_new, reason)
        """
        if not existing_contract:
            return True, "該当する有効な契約が見つかりません。新規契約を作成します。"

        # Check if employee's rate differs significantly (>10%)
        if employee.hourly_rate and existing_contract.hourly_rate:
            rate_diff = abs(float(employee.hourly_rate) - float(existing_contract.hourly_rate))
            rate_pct = rate_diff / float(existing_contract.hourly_rate) * 100
            if rate_pct > 10:
                return True, f"時給単価が契約と{rate_pct:.1f}%異なります。新規契約を作成することを推奨します。"

        # Check if employee is joining after contract start
        if start_date > existing_contract.dispatch_start_date:
            days_late = (start_date - existing_contract.dispatch_start_date).days
            if days_late > 14:
                # More than 2 weeks late - might want new contract
                return False, f"既存契約に途中参加します（{days_late}日遅れ）。"

        return False, "既存の契約に追加できます。"

    # ========================================
    # EMPLOYEE ASSIGNMENT
    # ========================================

    def add_employee_to_contract(
        self,
        contract_id: int,
        employee_id: int,
        hourly_rate: Optional[Decimal] = None,
        individual_start_date: Optional[date] = None,
        individual_end_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> KobetsuEmployee:
        """
        Add an employee to an existing contract with optional individual rates.

        If hourly_rate is not provided, uses employee's current rate.
        If individual dates are not provided, uses contract dates.
        """
        contract = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.id == contract_id
        ).first()
        if not contract:
            raise ContractValidationError("契約が見つかりません", "CONTRACT_NOT_FOUND")

        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ContractValidationError("従業員が見つかりません", "EMPLOYEE_NOT_FOUND")

        # Check if already assigned
        existing = self.db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
        if existing:
            raise ContractValidationError(
                "この従業員は既にこの契約に登録されています",
                "ALREADY_ASSIGNED"
            )

        # Validate individual dates against contract dates
        start = individual_start_date or contract.dispatch_start_date
        end = individual_end_date or contract.dispatch_end_date

        if start < contract.dispatch_start_date:
            raise ContractValidationError(
                f"個別開始日 ({start}) は契約開始日 ({contract.dispatch_start_date}) より前にできません",
                "INVALID_START_DATE"
            )
        if end > contract.dispatch_end_date:
            raise ContractValidationError(
                f"個別終了日 ({end}) は契約終了日 ({contract.dispatch_end_date}) より後にできません",
                "INVALID_END_DATE"
            )

        # Use employee rate if not specified
        rate = hourly_rate or employee.hourly_rate

        # Check if employee qualifies for indefinite employment
        is_indefinite = employee.is_indefinite_employment if hasattr(employee, 'is_indefinite_employment') else False

        kobetsu_employee = KobetsuEmployee(
            kobetsu_keiyakusho_id=contract_id,
            employee_id=employee_id,
            hourly_rate=rate,
            overtime_rate=employee.hourly_rate * Decimal("1.25") if employee.hourly_rate else None,
            individual_start_date=individual_start_date,
            individual_end_date=individual_end_date,
            is_indefinite_employment=is_indefinite,
            notes=notes
        )

        self.db.add(kobetsu_employee)

        # Update contract worker count
        contract.number_of_workers = self.db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).count() + 1  # +1 for the one we're adding

        self.db.flush()

        return kobetsu_employee

    def remove_employee_from_contract(
        self,
        contract_id: int,
        employee_id: int,
        end_date: Optional[date] = None
    ) -> bool:
        """
        Remove employee from contract or set individual end date.

        If end_date is provided, updates individual_end_date instead of removing.
        """
        kobetsu_employee = self.db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()

        if not kobetsu_employee:
            return False

        if end_date:
            # Set individual end date (early termination)
            kobetsu_employee.individual_end_date = end_date
            kobetsu_employee.notes = f"途中終了: {end_date}"
        else:
            # Remove completely
            self.db.delete(kobetsu_employee)

            # Update worker count
            contract = self.db.query(KobetsuKeiyakusho).filter(
                KobetsuKeiyakusho.id == contract_id
            ).first()
            if contract:
                contract.number_of_workers = max(0, contract.number_of_workers - 1)

        return True

    # ========================================
    # DATE CALCULATIONS
    # ========================================

    def calculate_max_end_date(self, factory_id: int) -> Optional[date]:
        """
        Calculate the maximum allowed end date for a new contract.

        Rules:
        1. Cannot exceed conflict_date
        2. Maximum 3 years from start (per labor law)
        """
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory:
            return None

        today = date.today()
        max_by_law = today + timedelta(days=365 * 3)  # 3 years

        if factory.conflict_date:
            return min(max_by_law, factory.conflict_date)

        return max_by_law

    def suggest_contract_dates(
        self,
        factory_id: int,
        employee_start_date: date,
        preferred_duration_months: int = 3
    ) -> dict:
        """
        Suggest contract dates based on business rules.

        Returns:
        - suggested_start: Recommended start date
        - suggested_end: Recommended end date
        - max_end: Maximum allowed end date
        - conflict_date: Factory's conflict date
        - warnings: List of warnings
        """
        warnings = []
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()

        if not factory:
            return {"error": "工場が見つかりません"}

        suggested_start = employee_start_date

        # Calculate preferred end date
        # Typical contracts are 1, 3, or 6 months
        from dateutil.relativedelta import relativedelta
        preferred_end = suggested_start + relativedelta(months=preferred_duration_months)

        # Adjust to end of month (common practice)
        from calendar import monthrange
        last_day = monthrange(preferred_end.year, preferred_end.month)[1]
        preferred_end = date(preferred_end.year, preferred_end.month, last_day)

        max_end = self.calculate_max_end_date(factory_id)

        # Check against conflict date
        if factory.conflict_date:
            if preferred_end > factory.conflict_date:
                preferred_end = factory.conflict_date
                warnings.append(
                    f"契約終了日を抵触日 ({factory.conflict_date}) に調整しました"
                )

            days_until = (factory.conflict_date - suggested_start).days
            if days_until < 30:
                warnings.append(f"警告: 抵触日まで残り{days_until}日です")

        return {
            "suggested_start": suggested_start,
            "suggested_end": preferred_end,
            "max_end": max_end,
            "conflict_date": factory.conflict_date,
            "warnings": warnings
        }

    # ========================================
    # RATE CALCULATIONS
    # ========================================

    def get_effective_rate(
        self,
        kobetsu_employee: KobetsuEmployee,
        contract: KobetsuKeiyakusho
    ) -> dict:
        """
        Get the effective rate for an employee in a contract.

        Priority:
        1. KobetsuEmployee individual rate (if set)
        2. Contract default rate
        3. Employee's base rate
        """
        emp = kobetsu_employee.employee

        hourly = (
            kobetsu_employee.hourly_rate or
            contract.hourly_rate or
            (emp.hourly_rate if emp else None)
        )

        overtime = (
            kobetsu_employee.overtime_rate or
            contract.overtime_rate or
            (hourly * Decimal("1.25") if hourly else None)
        )

        night = (
            kobetsu_employee.night_shift_rate or
            contract.night_shift_rate or
            (hourly * Decimal("1.50") if hourly else None)
        )

        holiday = (
            kobetsu_employee.holiday_rate or
            contract.holiday_rate or
            (hourly * Decimal("1.35") if hourly else None)
        )

        return {
            "hourly_rate": hourly,
            "overtime_rate": overtime,
            "night_shift_rate": night,
            "holiday_rate": holiday,
            "source": "individual" if kobetsu_employee.hourly_rate else "contract"
        }

    # ========================================
    # ALERTS AND NOTIFICATIONS
    # ========================================

    def get_expiring_contracts(self, days: int = 30) -> List[dict]:
        """Get contracts expiring within specified days."""
        threshold = date.today() + timedelta(days=days)

        contracts = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.status == 'active',
            KobetsuKeiyakusho.dispatch_end_date <= threshold,
            KobetsuKeiyakusho.dispatch_end_date >= date.today()
        ).all()

        result = []
        for contract in contracts:
            days_until = (contract.dispatch_end_date - date.today()).days
            result.append({
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "worksite_name": contract.worksite_name,
                "dispatch_end_date": contract.dispatch_end_date,
                "days_until_expiry": days_until,
                "number_of_workers": contract.number_of_workers,
                "urgency": "critical" if days_until <= 7 else "warning"
            })

        return sorted(result, key=lambda x: x["days_until_expiry"])

    def get_factories_near_conflict_date(self, days: int = 90) -> List[dict]:
        """Get factories approaching their conflict date."""
        threshold = date.today() + timedelta(days=days)

        factories = self.db.query(Factory).filter(
            Factory.is_active == True,
            Factory.conflict_date.isnot(None),
            Factory.conflict_date <= threshold,
            Factory.conflict_date >= date.today()
        ).all()

        result = []
        for factory in factories:
            days_until = (factory.conflict_date - date.today()).days

            # Count active workers
            active_workers = self.db.query(Employee).filter(
                Employee.factory_id == factory.id,
                Employee.status == 'active'
            ).count()

            result.append({
                "factory_id": factory.id,
                "factory_name": f"{factory.company_name} - {factory.plant_name}",
                "conflict_date": factory.conflict_date,
                "days_until_conflict": days_until,
                "active_workers": active_workers,
                "urgency": "critical" if days_until <= 30 else "warning"
            })

        return sorted(result, key=lambda x: x["days_until_conflict"])
