from app.agents.compliance_agent import ComplianceAgent
from decimal import Decimal

def test_debug():
    agent = ComplianceAgent()
    
    # Int inputs
    data_int = {"hourly_rate": 900}
    res_int = agent.validate_contract(data_int)
    print(f"Int Input Result: {res_int['is_valid']}")
    if not res_int['is_valid']:
        print(f"Errors: {res_int['errors']}")

    # Float inputs
    data_float = {"hourly_rate": 900.0}
    res_float = agent.validate_contract(data_float)
    print(f"Float Input Result: {res_float['is_valid']}")

    # String inputs
    data_str = {"hourly_rate": "900"}
    res_str = agent.validate_contract(data_str)
    print(f"String Input Result: {res_str['is_valid']}")

if __name__ == "__main__":
    test_debug()
