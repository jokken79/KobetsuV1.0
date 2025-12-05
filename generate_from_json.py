import json
import sys
import os
from datetime import date, time, datetime
from decimal import Decimal
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
    from app.services.kobetsu_pdf_service import KobetsuPDFService
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def parse_date(d_str):
    return datetime.strptime(d_str, "%Y-%m-%d").date()

def parse_time(t_str):
    return datetime.strptime(t_str, "%H:%M").time()

def generate_from_json(json_path):
    print(f"Reading JSON from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Map JSON to Model
    # Note: The JSON structure we designed is slightly more nested than the flat model,
    # so we map it here.
    
    c_info = data["contract_info"]
    p_a = data["parties"]["party_a"]
    p_b = data["parties"]["party_b"]
    work = data["work_conditions"]
    fin = data["financials"]
    legal = data["legal_checks"]

    contract = KobetsuKeiyakusho(
        contract_number=c_info["contract_number"],
        contract_date=parse_date(c_info["contract_date"]),
        
        dispatch_start_date=parse_date(c_info["dispatch_period"]["start_date"]),
        dispatch_end_date=parse_date(c_info["dispatch_period"]["end_date"]),
        
        work_content=work["content"],
        responsibility_level=work["responsibility"],
        
        worksite_name=p_b["worksite"]["name"],
        worksite_address=p_b["worksite"]["address"],
        organizational_unit=p_b["worksite"].get("organization_unit"),
        
        supervisor_department=p_b["commander"]["department"],
        supervisor_position=p_b["commander"]["position"],
        supervisor_name=p_b["commander"]["name"],
        
        work_days=work["days"],
        work_start_time=parse_time(work["hours"]["start"]),
        work_end_time=parse_time(work["hours"]["end"]),
        break_time_minutes=work["hours"]["break_minutes"],
        
        hourly_rate=Decimal(str(fin["rates"]["hourly"])),
        overtime_rate=Decimal(str(fin["rates"]["overtime"])),
        night_shift_rate=Decimal(str(fin["rates"]["night"])),
        holiday_rate=Decimal(str(fin["rates"]["holiday"])),
        
        haken_moto_complaint_contact=p_a["complaint_contact"],
        haken_saki_complaint_contact=p_b["complaint_contact"],
        
        haken_moto_manager=p_a["manager"],
        haken_saki_manager=p_b["manager"],
        
        number_of_workers=1, # Default or from JSON if added
        
        # Legal checks
        is_kyotei_taisho=legal["is_kyotei_taisho"],
        is_mukeiko_60over_only=legal.get("is_60_over", False),
        is_direct_hire_prevention=legal.get("direct_hire_clause", False),
        
        # New fields that might be in notes or specific fields
        # For now, we assume the service handles the layout logic
        status="active"
    )

    service = KobetsuPDFService()
    # Output to 'outputs/json_generated' to distinguish
    service.output_dir = Path(os.getcwd()) / 'outputs' / 'json_generated'
    service.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating contract from JSON data...")
    try:
        path = service.generate_docx(contract)
        print(f"Contract generated successfully at: {path}")
    except Exception as e:
        print(f"Error generating contract: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Use the artifact path we just created
    json_file = r"C:\Users\JPMiniOffice\.gemini\antigravity\brain\8439d38b-be9d-4cc9-bf84-09f897dc1f62\contract_example.json"
    generate_from_json(json_file)
