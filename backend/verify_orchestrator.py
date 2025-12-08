import sys
import os
import pandas as pd
from io import BytesIO
from app.agents.orchestrator_agent import OrchestratorAgent

def create_mock_excel():
    output = BytesIO()
    # Create a row that has a wage violation (900 JPY < 1027 JPY)
    data = [{
        "社員№": "EMP001",
        "氏名": "Orchestrator Test",
        "時給": 900,  # Violation
        "配属ライン": "Line A"
    }]
    df = pd.DataFrame(data)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='DBGenzaiX', index=False)
    return output.getvalue()

def test_orchestrator():
    print("Testing OrchestratorAgent...")
    orchestrator = OrchestratorAgent()
    
    mock_file = create_mock_excel()
    
    # Test 1: Full Import Flow (Analysis + Audit)
    print("\n[Test 1] Full Import Flow (Expect Audit Errors)")
    result = orchestrator.process({
        "intent": "full_import_flow",
        "payload": {
            "file_content": mock_file,
            "filename": "test_orchestrator.xlsx"
        }
    })
    
    if not result["success"]:
        print(f"FAIL: Processing failed. {result}")
        return

    # Check if we parsed 1 row
    rows = result["preview_data"]
    if len(rows) != 1:
        print(f"FAIL: Expected 1 row, got {len(rows)}")
        return

    row = rows[0]
    with open("verify_output.txt", "w") as f:
        f.write(f"DEBUG RATE: {row.get('hourly_rate')} (Type: {type(row.get('hourly_rate'))})\n")
        f.write(f"DEBUG AUDIT: {row.get('_audit')}\n")
        
        if not row["is_valid"] and any("MIN_WAGE_VIOLATION" in str(e) for e in row.get("errors", [])):
            f.write("PASS: Orchestrator correctly coordinated DataAnalyst (parse) and Compliance (audit).\n")
        else:
            f.write(f"FAIL: Expected validation error for low wage. Got: {row}\n")

if __name__ == "__main__":
    test_orchestrator()
