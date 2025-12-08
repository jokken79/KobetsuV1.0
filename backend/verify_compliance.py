from app.agents.compliance_agent import ComplianceAgent
from datetime import date, timedelta

def test_compliance():
    agent = ComplianceAgent()
    
    print("Testing ComplianceAgent scenarios...")

    # Scenario 1: Valid Contract
    print("\n[Scenario 1] Valid Contract")
    valid_data = {
        "hourly_rate": 1500,
        "overtime_rate": 1875, # 1.25x
        "work_days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "work_start_time": "09:00",
        "work_end_time": "18:00",
        "break_time_minutes": 60,
        "dispatch_start_date": "2024-01-01",
        "dispatch_end_date": "2024-12-31"
    }
    result = agent.validate_contract(valid_data)
    if result["is_valid"] and not result["warnings"]:
        print("PASS: Valid contract accepted.")
    else:
        print(f"FAIL: Valid contract rejected. Errors: {result['errors']}")

    # Scenario 2: Minimum Wage Violation
    print("\n[Scenario 2] Minimum Wage Violation")
    low_wage_data = valid_data.copy()
    low_wage_data["hourly_rate"] = 900 # Below 1027
    result = agent.validate_contract(low_wage_data)
    if not result["is_valid"] and any(e["code"] == "MIN_WAGE_VIOLATION" for e in result["errors"]):
        print("PASS: Detected minimum wage violation.")
    else:
        print(f"FAIL: Failed to detect minimum wage violation. Result: {result}")

    # Scenario 3: Illegal Overtime Rate
    print("\n[Scenario 3] Illegal Overtime Rate")
    bad_ot_data = valid_data.copy()
    bad_ot_data["hourly_rate"] = 2000
    bad_ot_data["overtime_rate"] = 2100 # < 1.25x (should be >= 2500)
    result = agent.validate_contract(bad_ot_data)
    if not result["is_valid"] and any(e["code"] == "ILLEGAL_OVERTIME_RATE" for e in result["errors"]):
        print("PASS: Detected illegal overtime rate.")
    else:
        print(f"FAIL: Failed to detect illegal overtime rate. Result: {result}")

    # Scenario 4: High Overtime Warning (60H Rule)
    print("\n[Scenario 4] High Overtime Risk")
    long_hours_data = valid_data.copy()
    long_hours_data["work_start_time"] = "08:00"
    long_hours_data["work_end_time"] = "22:00" # 13h - 1h break = 12h work (4h OT/day)
    long_hours_data["work_days"] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] # 6 days
    # 4h OT * 6 days * 4.3 weeks = ~100h OT/month
    
    result = agent.validate_contract(long_hours_data)
    if any(w["code"] == "HIGH_OVERTIME_RISK" for w in result["warnings"]):
        print("PASS: Warned about high overtime risk.")
    else:
        print(f"FAIL: Failed to warn about high overtime. Warnings: {result['warnings']}")

if __name__ == "__main__":
    test_compliance()
