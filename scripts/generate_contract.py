import sys
import os
from datetime import date, time
from decimal import Decimal
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock settings if needed, but let's try to import first
try:
    from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
    from app.services.kobetsu_pdf_service import KobetsuPDFService
    from app.core.config import settings
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def generate_contract():
    # Create dummy contract data based on simulation
    # Note: factory_id is required but we use a dummy value for standalone testing
    contract = KobetsuKeiyakusho(
        id=1,  # Dummy ID for testing
        factory_id=1,  # Required field - dummy value for standalone testing
        contract_number="KOB-202504-0001",
        contract_date=date(2025, 4, 10),
        dispatch_start_date=date(2025, 4, 15),
        dispatch_end_date=date(2025, 9, 30),
        work_content="鋳造材料の工場内加工ラインへの供給作業。リフトを操作して材料を運搬し、各加工ラインへ供給。在庫管理を含む。",
        responsibility_level="通常業務",
        worksite_name="高雄工業株式会社 本社工場",
        worksite_address="愛知県弥富市楠三丁目13番地2",
        organizational_unit="製造部",  # Added - used in PDF
        supervisor_department="第一営業部本社営業課",
        supervisor_position="係長",
        supervisor_name="坂上 舞",
        work_days=["月", "火", "水", "木", "金"],
        work_start_time=time(7, 0),
        work_end_time=time(15, 30),
        break_time_minutes=45,
        overtime_max_hours_month=45,  # Added - used in PDF
        hourly_rate=Decimal("1750.00"),
        overtime_rate=Decimal("2187.50"),
        night_shift_rate=Decimal("2100.00"),
        holiday_rate=Decimal("2625.00"),
        haken_moto_complaint_contact={
            "department": "営業部",
            "position": "取締役部長",
            "name": "中山 欣英",
            "phone": "052-938-8840"
        },
        haken_saki_complaint_contact={
            "department": "人事広報管理部",
            "position": "部長",
            "name": "山田 茂",
            "phone": "0567-68-8110"
        },
        haken_moto_manager={
            "department": "営業部",
            "position": "取締役",
            "name": "ブウ ティ サウ",
            "phone": "052-938-8840"
        },
        haken_saki_manager={
            "department": "愛知事業所",
            "position": "部長",
            "name": "安藤 忍",
            "phone": "0567-68-8110"
        },
        number_of_workers=1,
        status="active",
        is_kyotei_taisho=False  # Added - used in PDF for checkbox
    )

    service = KobetsuPDFService()
    # Override output dir to current directory/outputs for visibility
    service.output_dir = Path(os.getcwd()) / 'outputs'
    service.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating contract...")
    try:
        path = service.generate_pdf(contract)
        print(f"Contract generated successfully at: {path}")
    except Exception as e:
        print(f"Error generating contract: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_contract()
