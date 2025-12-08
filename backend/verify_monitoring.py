from app.agents.monitoring_agent import MonitoringAgent
from pathlib import Path
import time
import os

def test_monitoring():
    print("Testing MonitoringAgent...")
    agent = MonitoringAgent()
    
    # Clean state
    if agent.state_path.exists():
        os.remove(agent.state_path)

    # 1. Initial Scan (Establish Baseline)
    print("\n[Test 1] Initial Scan (Establish Baseline)")
    res1 = agent.scan_codebase()
    if res1["success"] and not res1["changes_detected"]:
        print("PASS: Baseline established. State saved.")
    else:
        print(f"FAIL: Initial scan failed or detected changes? {res1}")

    # 2. Simulate Change (Create a dummy file)
    print("\n[Test 2] Detect New File")
    dummy_file = Path("app/services/dummy_service.py")
    with open(dummy_file, "w") as f:
        f.write("# Dummy file for testing monitoring agent")
    
    res2 = agent.scan_codebase()
    
    # Cleanup dummy
    if dummy_file.exists():
        os.remove(dummy_file)

    changes = res2.get("changes", [])
    if any(c["type"] == "NEW" and "dummy_service.py" in c["file"] for c in changes):
        print("PASS: Detected new file.")
    else:
        print(f"FAIL: Failed to detect new file. Changes: {changes}")

    # 3. Detect Deletion (of the dummy file above)
    print("\n[Test 3] Detect Deletion")
    res3 = agent.scan_codebase()
    changes = res3.get("changes", [])
    
    if any(c["type"] == "DELETED" and "dummy_service.py" in c["file"] for c in changes):
        print("PASS: Detected deletion.")
    else:
        print(f"FAIL: Failed to detect deletion. Changes: {changes}")

if __name__ == "__main__":
    test_monitoring()
