import os
import sys
import pandas as pd
from io import BytesIO

# Add backend to path - NOT NEEDED IN CONTAINER
# sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.agents.data_analyst_agent import DataAnalystAgent

def create_mock_excel(is_dbgenzai=False):
    """Create a mock Excel file in memory."""
    output = BytesIO()
    
    if is_dbgenzai:
        data = [{
            "社員№": "EMP001",
            "氏名": "Test User",
            "配属ライン": "Line A",
            "現在": "在職中"
        }]
    else:
        data = [{
            "社員番号": "EMP002",
            "氏名": "Simple User",
            "カナ": "Simple Kana",
            "入社日": "2024-01-01"
        }]
        
    df = pd.DataFrame(data)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sheet_name = 'DBGenzaiX' if is_dbgenzai else 'Sheet1'
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
    return output.getvalue()

def test_agent():
    print("Testing DataAnalystAgent...")
    agent = DataAnalystAgent()
    
    # Test 1: Simple Template
    print("\n[Test 1] Simple Template Format")
    content = create_mock_excel(is_dbgenzai=False)
    result = agent.preview_employees(content, "test_simple.xlsx")
    
    if result["success"] and result["total_rows"] == 1:
        print("PASS: Parsed simple template correctly.")
        print(f"Preview: {result['preview_data'][0]['full_name_kanji']}")
    else:
        print("FAIL: Failed to parse simple template.")
        print(result)

    # Test 2: DBGenzaiX Format
    print("\n[Test 2] DBGenzaiX Format")
    content = create_mock_excel(is_dbgenzai=True)
    result = agent.preview_employees(content, "test_dbgenzai.xlsx")
    
    if result["success"] and result["total_rows"] == 1:
        print("PASS: Parsed DBGenzaiX template correctly.")
        print(f"Preview: {result['preview_data'][0]['full_name_kanji']}")
    else:
        print("FAIL: Failed to parse DBGenzaiX template.")
        print(result)

if __name__ == "__main__":
    test_agent()
