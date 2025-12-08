from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional, Dict, Any
from app.core.security import get_current_user
from app.agents.orchestrator_agent import OrchestratorAgent

router = APIRouter()

@router.post("/process")
async def process_agent_request(
    intent: str = Form(...),
    file: Optional[UploadFile] = File(None),
    contract_data: Optional[str] = Form(None), # JSON string if needed
    current_user: dict = Depends(get_current_user),
):
    """
    Unified entry point for Agent Ecosystem.
    Supported Intents:
    - 'analyze_file': Upload Excel, get analysis (Data Analyst)
    - 'full_import_flow': Upload Excel, get analysis + legal audit (Orchestrator)
    """
    orchestrator = OrchestratorAgent()
    
    payload = {}
    
    # Handle File Uploads
    if file:
        content = await file.read()
        payload["file_content"] = content
        payload["filename"] = file.filename
        
    # Handle JSON data (future use for contract audit without file)
    if contract_data:
        import json
        try:
            payload["contract_data"] = json.loads(contract_data)
        except:
             raise HTTPException(status_code=400, detail="Invalid JSON in contract_data")

    # Delegate to Orchestrator
    result = orchestrator.process({
        "intent": intent,
        "payload": payload
    })
    
    return result
