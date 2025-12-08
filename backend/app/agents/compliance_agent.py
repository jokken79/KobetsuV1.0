from typing import Any, Dict, List, Optional
from decimal import Decimal
from datetime import date, datetime
from .base_agent import BaseAgent

class ComplianceAgent(BaseAgent):
    """
    Agent responsible for Legal Compliance and Validation.
    Ensures contracts meet Labor Standards Act and Worker Dispatch Law requirements.
    """

    def __init__(self):
        super().__init__(name="ComplianceAgent", role="Legal & Compliance Officer")
        # TODO: Load these from a DB or Config in future
        self.MINIMUM_WAGE_AICHI = Decimal("1027")  # Aichi Prefecture Oct 2023
        self.LEGAL_OVERTIME_RATE = Decimal("1.25")
        self.SPECIAL_OVERTIME_RATE = Decimal("1.50") # For >60h/month

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Generic process method. Expects a dictionary with 'action' and 'data'.
        """
        if isinstance(input_data, dict):
            action = input_data.get("action")
            data = input_data.get("data")
            
            if action == "validate_contract":
                return self.validate_contract(data)
        
        return {"success": False, "message": "Unknown action or invalid input"}

    def validate_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a contract draft against legal rules.
        """
        self.log_activity(f"Validating contract draft")
        
        errors = []
        warnings = []
        
        # 1. Minimum Wage Check
        hourly_rate = self._get_decimal(contract_data.get("hourly_rate"))
        if hourly_rate and hourly_rate < self.MINIMUM_WAGE_AICHI:
            errors.append({
                "code": "MIN_WAGE_VIOLATION",
                "field": "hourly_rate",
                "message": f"Hourly rate ({hourly_rate} JPY) is below Aichi minimum wage ({self.MINIMUM_WAGE_AICHI} JPY)."
            })

        # 2. Overtime Rate Check
        overtime_rate = self._get_decimal(contract_data.get("overtime_rate"))
        if hourly_rate and overtime_rate:
            min_overtime = hourly_rate * self.LEGAL_OVERTIME_RATE
            if overtime_rate < min_overtime:
                errors.append({
                    "code": "ILLEGAL_OVERTIME_RATE",
                    "field": "overtime_rate",
                    "message": f"Overtime rate must be at least 1.25x base rate (Minimum: {min_overtime})."
                })

        # 3. 60H Rule Analysis (Warning)
        # Check if the contract implies heavy overtime that might trigger the 1.5x rule
        # This is a heuristic check based on work days and times
        estimated_monthly_hours = self._estimate_monthly_hours(contract_data)
        if estimated_monthly_hours > 200: # Rough threshold (160h regular + 40h overtime)
             warnings.append({
                "code": "HIGH_OVERTIME_RISK",
                "field": "work_time",
                "message": f"Estimated monthly hours ({estimated_monthly_hours}h) are high. Ensure '60H Overtime Rule' (1.5x) clauses are included if applicable."
            })

        # 4. Dispatch Period Check (3-Year Rule)
        start_date = self._parse_date(contract_data.get("dispatch_start_date"))
        end_date = self._parse_date(contract_data.get("dispatch_end_date"))
        
        if start_date and end_date:
            duration_days = (end_date - start_date).days
            if duration_days > (365 * 3):
                 warnings.append({
                    "code": "DISPATCH_LIMIT_WARNING",
                    "field": "dispatch_end_date",
                    "message": "Contract duration exceeds 3 years. Check '抵触日' (Conflict Date) rules for the organizational unit."
                })

        is_valid = len(errors) == 0
        
        return {
            "success": True,
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "compliance_checked": True,
            "timestamp": datetime.now().isoformat()
        }

    def _get_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except:
            return None

    def _parse_date(self, value: Any) -> Optional[date]:
        if not value:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except:
                return None
        return None

    def _estimate_monthly_hours(self, data: Dict[str, Any]) -> float:
        """Roughly estimate monthly working hours."""
        try:
            days_per_week = len(data.get("work_days", []))
            if not days_per_week:
                days_per_week = 5 # Default
            
            start_str = data.get("work_start_time")
            end_str = data.get("work_end_time")
            break_min = int(data.get("break_time_minutes", 60))
            
            if start_str and end_str:
                # Simple parsing assuming HH:MM matches regex in schema
                # But here we might receive time objects or strings depending on Pydantic
                
                # Helper to convert to minutes
                def to_minutes(t):
                    if isinstance(t, str):
                        parts = t.split(':')
                        return int(parts[0]) * 60 + int(parts[1])
                    return t.hour * 60 + t.minute
                
                start_min = to_minutes(start_str)
                end_min = to_minutes(end_str)
                
                daily_min = end_min - start_min - break_min
                daily_hours = daily_min / 60.0
                
                # Approx weeks per month
                return daily_hours * days_per_week * 4.33
                
        except Exception:
            return 0.0
        
        return 0.0
