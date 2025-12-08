from app.agents.orchestrator_agent import OrchestratorAgent

def test_debug_orch():
    orch = OrchestratorAgent()
    
    # Simulate a parsed row from DataAnalyst
    row = {
        "hourly_rate": 900,
        "is_valid": True,
        "errors": []
    }
    
    # 2. Audit logic copy-pasted from OrchestratorAgent (to verify)
    validation_context = {
        "hourly_rate": row.get("hourly_rate"),
        "overtime_rate": row.get("hourly_rate") * 1.25 if row.get("hourly_rate") else None
    }
    
    audit_res = orch.compliance_officer.validate_contract(validation_context)
    print(f"Audit Result Valid: {audit_res['is_valid']}")
    print(f"Audit Errors: {audit_res['errors']}")
    
    row["_audit"] = {
        "is_valid": audit_res["is_valid"],
        "errors": audit_res["errors"],
        "warnings": audit_res["warnings"]
    }
    
    if not audit_res["is_valid"]:
        row["is_valid"] = False 
        
    print(f"Final Row Valid: {row['is_valid']}")

if __name__ == "__main__":
    test_debug_orch()
