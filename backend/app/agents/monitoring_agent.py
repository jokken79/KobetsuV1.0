import hashlib
import json
import os
from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path
from .base_agent import BaseAgent

class MonitoringAgent(BaseAgent):
    """
    Agent responsible for Codebase Evolution Monitoring.
    Tracks changes in critical system files to detect drift or modification.
    """

    STATE_FILE = "codebase_state.json"
    
    # Critical paths to monitor relative to app root
    MONITORED_PATHS = [
        "app/models",
        "app/schemas",
        "app/agents",
        "app/services"
    ]

    def __init__(self):
        super().__init__(name="MonitoringAgent", role="Evolution Monitor")
        self.state_path = Path(self.STATE_FILE)

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process generic input.
        Action: 'scan' -> run codebase scan
        """
        if isinstance(input_data, dict):
            action = input_data.get("action")
            if action == "scan":
                return self.scan_codebase()
        
        return {"success": False, "message": "Unknown action"}

    def scan_codebase(self) -> Dict[str, Any]:
        """
        Scan critical files and compare with previous state.
        """
        current_state = self._generate_current_state()
        previous_state = self._load_previous_state()
        
        changes = self._compare_states(previous_state, current_state)
        
        # Update state file
        self._save_state(current_state)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "changes_detected": len(changes) > 0,
            "changes": changes,
            "monitored_paths": self.MONITORED_PATHS
        }

    def _generate_current_state(self) -> Dict[str, str]:
        """Generate SHA256 hashes for all monitored files."""
        state = {}
        base_path = Path(os.getcwd()) # Assumes running from /app in backend
        
        for relative_path in self.MONITORED_PATHS:
            target_dir = base_path / relative_path
            if not target_dir.exists():
                continue
                
            for file_path in target_dir.rglob("*.py"):
                if file_path.is_file():
                    rel_name = str(file_path.relative_to(base_path))
                    state[rel_name] = self._calculate_hash(file_path)
                    
        return state

    def _calculate_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except:
            return "error"

    def _load_previous_state(self) -> Dict[str, str]:
        if not self.state_path.exists():
            return {}
        try:
            with open(self.state_path, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_state(self, state: Dict[str, str]):
        try:
            with open(self.state_path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log_activity(f"Failed to save state: {e}")

    def _compare_states(self, prev: Dict[str, str], curr: Dict[str, str]) -> List[Dict[str, str]]:
        changes = []
        
        # Check modified or new
        for file, curr_hash in curr.items():
            if file not in prev:
                changes.append({"type": "NEW", "file": file})
            elif prev[file] != curr_hash:
                changes.append({"type": "MODIFIED", "file": file})
                
        # Check deleted
        for file in prev:
            if file not in curr:
                changes.append({"type": "DELETED", "file": file})
                
        return changes
