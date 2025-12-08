from typing import Any, Dict, Optional
from .base_agent import BaseAgent
from .data_analyst_agent import DataAnalystAgent
from .compliance_agent import ComplianceAgent

class OrchestratorAgent(BaseAgent):
    """
    The 'Director of Operations'. 
    Coordinates specialized agents to fulfill complex user requests.
    """

    def __init__(self):
        super().__init__(name="OrchestratorAgent", role="Operations Director")
        # Initialize sub-agents
        self.data_analyst = DataAnalystAgent()
        self.compliance_officer = ComplianceAgent()

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Main entry point for the Orchestrator.
        Expects a dictionary with 'intent' and 'payload'.
        """
        if not isinstance(input_data, dict):
             return {"success": False, "message": "Invalid input format. Expected dict."}

        intent = input_data.get("intent")
        payload = input_data.get("payload")

        self.log_activity(f"Processing intent: {intent}")

        if intent == "analyze_file":
            return self._handle_file_analysis(payload)
        
        elif intent == "audit_contract":
            return self._handle_contract_audit(payload)

        elif intent == "full_import_flow":
            return self._handle_full_import(payload)
            
        else:
            return {
                "success": False, 
                "message": f"Unknown intent: {intent}. Supported: analyze_file, audit_contract, full_import_flow"
            }

    def _handle_file_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to Data Analyst."""
        file_content = payload.get("file_content")
        filename = payload.get("filename", "unknown.xlsx")
        
        if not file_content:
            return {"success": False, "message": "Missing 'file_content' in payload"}
            
        # For now, we assume it's an employee file for this demo
        # Real version would need a 'file_type' or auto-detection
        return self.data_analyst.preview_employees(file_content, filename)

    def _handle_contract_audit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to Compliance Officer."""
        contract_data = payload.get("contract_data")
        if not contract_data:
             return {"success": False, "message": "Missing 'contract_data' in payload"}
             
        return self.compliance_officer.validate_contract(contract_data)

    def _handle_full_import(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complex Workflow:
        1. Parse File (Data Analyst)
        2. Audit Data (Compliance Officer) - e.g. check rates in the parsed data
        """
        # 1. Parse
        parse_result = self._handle_file_analysis(payload)
        if not parse_result.get("success"):
            return parse_result
        
        # 2. Audit each row (Preliminary check)
        parsed_rows = parse_result.get("preview_data", [])
        audited_rows = []
        
        compliance_issues = 0
        
        for row in parsed_rows:
            # Construct a mini-contract object for validation
            # We only have limited data from Excel, but we can check rates
            validation_context = {
                "hourly_rate": row.get("hourly_rate"),
                # We assume standard overtime rate if not present, just to check min wage
                "overtime_rate": row.get("hourly_rate") * 1.25 if row.get("hourly_rate") else None
            }
            
            audit_res = self.compliance_officer.validate_contract(validation_context)
            
            # Enrich row with audit info
            row["_audit"] = {
                "is_valid": audit_res["is_valid"],
                "errors": audit_res["errors"],
                "warnings": audit_res["warnings"]
            }
            
            if not audit_res["is_valid"]:
                compliance_issues += 1
                row["is_valid"] = False # Override parse validity if legal check fails
                # Append legal errors to row errors
                legal_errs = [f"[Legal] {e['message']}" for e in audit_res["errors"]]
                # row["errors"] is a list of strings in DataAnalyst, check typical format
                # DataAnalyst returns "errors": ["Row 1: ..."]
                # We should append properly
                if "errors" not in row: row["errors"] = []
                row["errors"].extend(legal_errs)
            
            audited_rows.append(row)
            
        parse_result["preview_data"] = audited_rows
        parse_result["message"] += f" Compliance Audit: {compliance_issues} issues found."
        
        return parse_result
