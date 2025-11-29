"""
Document Generation API - 書類生成API

Endpoints for generating dispatch-related documents:
1. 個別契約書 (Individual Contract)
2. 就業条件明示書 (Working Conditions)
3. 派遣通知書 (Dispatch Notification)
4. 派遣先管理台帳 (Destination Ledger)
5. 派遣元管理台帳 (Source Ledger)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.dispatch_documents_service import DispatchDocumentService
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee

router = APIRouter()


# ========================================
# Generate documents from contract ID
# ========================================

@router.get("/{contract_id}/kobetsu-keiyakusho")
async def generate_kobetsu_keiyakusho(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 個別契約書 (Individual Contract) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Build data dict from contract
    data = _build_contract_data(contract)

    service = DispatchDocumentService()
    doc_bytes = service.generate_kobetsu_keiyakusho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=kobetsu_keiyakusho_{contract.contract_number}.docx"
        }
    )


@router.get("/{contract_id}/shugyo-joken")
async def generate_shugyo_joken_meijisho(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 就業条件明示書 (Working Conditions) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get specific employee or first employee
    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    data = _build_worker_condition_data(contract, kobetsu_emp, employee)

    service = DispatchDocumentService()
    doc_bytes = service.generate_shugyo_joken_meijisho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=shugyo_joken_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/haken-tsuchisho")
async def generate_haken_tsuchisho(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 派遣通知書 (Dispatch Notification) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get all employees for this contract
    kobetsu_employees = db.query(KobetsuEmployee).filter(
        KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
    ).all()

    if not kobetsu_employees:
        raise HTTPException(status_code=404, detail="No employees assigned to this contract")

    data = _build_notification_data(contract, kobetsu_employees)

    service = DispatchDocumentService()
    doc_bytes = service.generate_haken_tsuchisho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=haken_tsuchisho_{contract.contract_number}.docx"
        }
    )


@router.get("/{contract_id}/hakensaki-daicho")
async def generate_hakensaki_daicho(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 派遣先管理台帳 (Destination Ledger) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    data = _build_ledger_data(contract, kobetsu_emp, employee, is_source=False)

    service = DispatchDocumentService()
    doc_bytes = service.generate_hakensaki_kanri_daicho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=hakensaki_daicho_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/hakenmoto-daicho")
async def generate_hakenmoto_daicho(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate 派遣元管理台帳 (Source Ledger) - Compact A4 1 page."""
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee
    data = _build_ledger_data(contract, kobetsu_emp, employee, is_source=True)

    service = DispatchDocumentService()
    doc_bytes = service.generate_hakenmoto_kanri_daicho(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=hakenmoto_daicho_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/kobetsu-shugyo-combined")
async def generate_kobetsu_shugyo_combined(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate combined 個別契約書 + 就業条件明示書 on ONE A4 page.

    This is the compact format that combines both documents for efficiency.
    派遣元 ↔ 派遣先 契約 + 派遣労働者への条件明示
    """
    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get specific employee or first employee
    if employee_id:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).first()
    else:
        kobetsu_emp = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).first()

    if not kobetsu_emp:
        raise HTTPException(status_code=404, detail="No employee assigned to this contract")

    employee = kobetsu_emp.employee

    # Build combined data from contract and worker
    data = _build_combined_data(contract, kobetsu_emp, employee)

    service = DispatchDocumentService()
    doc_bytes = service.generate_kobetsu_shugyo_combined(data)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=kobetsu_shugyo_{contract.contract_number}_{employee.employee_number}.docx"
        }
    )


@router.get("/{contract_id}/all-documents")
async def generate_all_documents(
    contract_id: int,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate all documents for a contract as a ZIP file.

    Includes:
    - 個別契約書
    - 就業条件明示書 (for each employee)
    - 派遣通知書
    - 派遣先管理台帳 (for each employee)
    - 派遣元管理台帳 (for each employee)
    """
    import zipfile
    from io import BytesIO

    contract = db.query(KobetsuKeiyakusho).filter(KobetsuKeiyakusho.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get employees
    if employee_id:
        kobetsu_employees = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
            KobetsuEmployee.employee_id == employee_id
        ).all()
    else:
        kobetsu_employees = db.query(KobetsuEmployee).filter(
            KobetsuEmployee.kobetsu_keiyakusho_id == contract_id
        ).all()

    if not kobetsu_employees:
        raise HTTPException(status_code=404, detail="No employees assigned to this contract")

    service = DispatchDocumentService()

    # Create ZIP file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. 個別契約書
        data = _build_contract_data(contract)
        doc_bytes = service.generate_kobetsu_keiyakusho(data)
        zip_file.writestr(f"01_個別契約書_{contract.contract_number}.docx", doc_bytes)

        # 2. 派遣通知書
        notif_data = _build_notification_data(contract, kobetsu_employees)
        doc_bytes = service.generate_haken_tsuchisho(notif_data)
        zip_file.writestr(f"02_派遣通知書_{contract.contract_number}.docx", doc_bytes)

        # For each employee
        for ke in kobetsu_employees:
            emp = ke.employee
            emp_num = emp.employee_number

            # 3. 就業条件明示書
            worker_data = _build_worker_condition_data(contract, ke, emp)
            doc_bytes = service.generate_shugyo_joken_meijisho(worker_data)
            zip_file.writestr(f"03_就業条件明示書_{emp_num}.docx", doc_bytes)

            # 4. 派遣先管理台帳
            ledger_data = _build_ledger_data(contract, ke, emp, is_source=False)
            doc_bytes = service.generate_hakensaki_kanri_daicho(ledger_data)
            zip_file.writestr(f"04_派遣先管理台帳_{emp_num}.docx", doc_bytes)

            # 5. 派遣元管理台帳
            ledger_data = _build_ledger_data(contract, ke, emp, is_source=True)
            doc_bytes = service.generate_hakenmoto_kanri_daicho(ledger_data)
            zip_file.writestr(f"05_派遣元管理台帳_{emp_num}.docx", doc_bytes)

    zip_buffer.seek(0)

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=documents_{contract.contract_number}.zip"
        }
    )


# ========================================
# Helper functions
# ========================================

def _build_contract_data(contract: KobetsuKeiyakusho) -> dict:
    """Build data dictionary from contract for document generation."""
    factory = contract.factory

    return {
        "contract_number": contract.contract_number,
        "contract_date": contract.contract_date,
        "dispatch_start_date": contract.dispatch_start_date,
        "dispatch_end_date": contract.dispatch_end_date,
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "client_address": factory.company_address if factory else contract.worksite_address,
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,
        "supervisor_dept": contract.supervisor_department,
        "supervisor_position": contract.supervisor_position,
        "supervisor_name": contract.supervisor_name,
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "overtime_max_day": float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4,
        "overtime_max_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "holiday_work_max": contract.holiday_work_max_days or 2,
        "hourly_rate": float(contract.hourly_rate),
        "overtime_rate": float(contract.overtime_rate),
        "holiday_rate": float(contract.holiday_rate) if contract.holiday_rate else float(contract.overtime_rate),
        "number_of_workers": contract.number_of_workers,
        "haken_moto_manager": contract.haken_moto_manager,
        "haken_saki_manager": contract.haken_saki_manager,
        "haken_moto_complaint": contract.haken_moto_complaint_contact,
        "haken_saki_complaint": contract.haken_saki_complaint_contact,
        "safety_measures": contract.safety_measures,
        "termination_measures": contract.termination_measures,
        "welfare_facilities": contract.welfare_facilities,
        "is_kyotei_taisho": contract.is_kyotei_taisho,
        "is_mukeiko_60over": contract.is_mukeiko_60over_only,
        "conflict_date": factory.conflict_date if factory else None,
    }


def _build_worker_condition_data(contract: KobetsuKeiyakusho, kobetsu_emp: KobetsuEmployee, employee) -> dict:
    """Build worker condition data for 就業条件明示書."""
    factory = contract.factory

    # Determine hourly wage (employee individual > contract)
    hourly_wage = kobetsu_emp.hourly_rate or employee.hourly_rate or contract.hourly_rate
    overtime_wage = kobetsu_emp.overtime_rate or contract.overtime_rate

    return {
        "worker_name": employee.full_name_kanji,
        "worker_number": employee.employee_number,
        "dispatch_start_date": kobetsu_emp.individual_start_date or contract.dispatch_start_date,
        "dispatch_end_date": kobetsu_emp.individual_end_date or contract.dispatch_end_date,
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,
        "supervisor_name": contract.supervisor_name,
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "overtime_max_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "holiday_work_max": contract.holiday_work_max_days or 2,
        "hourly_wage": float(hourly_wage) if hourly_wage else 0,
        "overtime_wage": float(overtime_wage) if overtime_wage else 0,
        "has_health_insurance": employee.has_health_insurance,
        "has_pension": employee.has_pension_insurance,
        "has_employment_insurance": employee.has_employment_insurance,
        "conflict_date": factory.conflict_date if factory else None,
        "is_indefinite": kobetsu_emp.is_indefinite_employment or employee.is_indefinite_employment,
        "is_agreement_target": contract.is_kyotei_taisho,
        "haken_moto_manager": contract.haken_moto_manager,
        "complaint_handler_moto": contract.haken_moto_complaint_contact,
        "complaint_handler_saki": contract.haken_saki_complaint_contact,
        "welfare_facilities": contract.welfare_facilities,
    }


def _build_notification_data(contract: KobetsuKeiyakusho, kobetsu_employees: list) -> dict:
    """Build notification data for 派遣通知書."""
    factory = contract.factory

    workers = []
    for ke in kobetsu_employees:
        emp = ke.employee
        workers.append({
            "worker_name": emp.full_name_kanji,
            "worker_gender": emp.gender or "男",
            "is_indefinite": ke.is_indefinite_employment or emp.is_indefinite_employment,
            "is_over_60": (emp.age or 0) >= 60 if emp.age else False,
            "has_health_insurance": emp.has_health_insurance,
            "has_pension": emp.has_pension_insurance,
            "has_employment_insurance": emp.has_employment_insurance,
            "is_agreement_target": contract.is_kyotei_taisho,
        })

    return {
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "workers": workers,
        "dispatch_start_date": contract.dispatch_start_date,
        "dispatch_end_date": contract.dispatch_end_date,
        "worksite_name": contract.worksite_name,
        "work_content": contract.work_content,
        "haken_moto_manager": contract.haken_moto_manager,
    }


def _build_ledger_data(contract: KobetsuKeiyakusho, kobetsu_emp: KobetsuEmployee, employee, is_source: bool) -> dict:
    """Build ledger data for 管理台帳."""
    factory = contract.factory

    hourly_wage = kobetsu_emp.hourly_rate or employee.hourly_rate or contract.hourly_rate
    billing_rate = kobetsu_emp.billing_rate or employee.billing_rate or contract.hourly_rate

    return {
        "worker_name": employee.full_name_kanji,
        "worker_number": employee.employee_number,
        "worker_gender": employee.gender or "",
        "is_indefinite": kobetsu_emp.is_indefinite_employment or employee.is_indefinite_employment,
        "is_over_60": (employee.age or 0) >= 60 if employee.age else False,
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,
        "supervisor_name": contract.supervisor_name,
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,
        "is_agreement_target": contract.is_kyotei_taisho,
        "dispatch_start_date": kobetsu_emp.individual_start_date or contract.dispatch_start_date,
        "dispatch_end_date": kobetsu_emp.individual_end_date or contract.dispatch_end_date,
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "hourly_wage": float(hourly_wage) if hourly_wage else 0,
        "billing_rate": float(billing_rate) if billing_rate else 0,
        "haken_moto_manager": contract.haken_moto_manager,
        "haken_saki_manager": contract.haken_saki_manager,
        "complaint_handler_moto": contract.haken_moto_complaint_contact,
        "complaint_handler_saki": contract.haken_saki_complaint_contact,
        "has_health_insurance": employee.has_health_insurance,
        "has_pension": employee.has_pension_insurance,
        "has_employment_insurance": employee.has_employment_insurance,
        "welfare_facilities": contract.welfare_facilities,
        "conflict_date": factory.conflict_date if factory else None,
        "dispatch_company": None,  # Will use settings default
        "dispatch_address": None,  # Will use settings default
    }


def _build_combined_data(contract: KobetsuKeiyakusho, kobetsu_emp: KobetsuEmployee, employee) -> dict:
    """Build combined data for 個別契約書 + 就業条件明示書 one-page document."""
    factory = contract.factory

    # Determine wages (employee individual > contract)
    hourly_wage = kobetsu_emp.hourly_rate or employee.hourly_rate or contract.hourly_rate
    overtime_wage = kobetsu_emp.overtime_rate or contract.overtime_rate

    return {
        # Contract info
        "contract_number": contract.contract_number,
        "contract_date": contract.contract_date,
        "dispatch_start_date": kobetsu_emp.individual_start_date or contract.dispatch_start_date,
        "dispatch_end_date": kobetsu_emp.individual_end_date or contract.dispatch_end_date,
        "client_company_name": factory.company_name if factory else contract.worksite_name,
        "client_address": factory.company_address if factory else contract.worksite_address,
        "number_of_workers": contract.number_of_workers,

        # Worksite info
        "worksite_name": contract.worksite_name,
        "worksite_address": contract.worksite_address,
        "organizational_unit": contract.organizational_unit,

        # Work content
        "work_content": contract.work_content,
        "responsibility_level": contract.responsibility_level,

        # Supervisor
        "supervisor_dept": contract.supervisor_department,
        "supervisor_position": contract.supervisor_position,
        "supervisor_name": contract.supervisor_name,
        "supervisor_phone": "",

        # Work schedule
        "work_days": contract.work_days,
        "work_start_time": contract.work_start_time,
        "work_end_time": contract.work_end_time,
        "break_minutes": contract.break_time_minutes,
        "overtime_max_day": float(contract.overtime_max_hours_day) if contract.overtime_max_hours_day else 4,
        "overtime_max_month": float(contract.overtime_max_hours_month) if contract.overtime_max_hours_month else 45,
        "holiday_work_max": contract.holiday_work_max_days or 2,

        # Rates (for contract)
        "hourly_rate": float(contract.hourly_rate) if contract.hourly_rate else 0,
        "overtime_rate": float(contract.overtime_rate) if contract.overtime_rate else 0,
        "holiday_rate": float(contract.holiday_rate) if contract.holiday_rate else float(contract.overtime_rate) if contract.overtime_rate else 0,

        # Wages (for worker)
        "hourly_wage": float(hourly_wage) if hourly_wage else 0,
        "overtime_wage": float(overtime_wage) if overtime_wage else 0,
        "wage_closing": "月末",
        "wage_payment": "翌25日",

        # Managers
        "haken_moto_manager": contract.haken_moto_manager or {},
        "haken_saki_manager": contract.haken_saki_manager or {},
        "haken_moto_complaint": contract.haken_moto_complaint_contact or {},
        "haken_saki_complaint": contract.haken_saki_complaint_contact or {},

        # Safety and termination
        "safety_measures": contract.safety_measures,
        "termination_measures": contract.termination_measures,

        # Welfare
        "welfare_facilities": contract.welfare_facilities,

        # Worker info
        "worker_name": employee.full_name_kanji,
        "worker_number": employee.employee_number,

        # Insurance
        "has_health_insurance": employee.has_health_insurance,
        "has_pension": employee.has_pension_insurance,
        "has_employment_insurance": employee.has_employment_insurance,

        # Employment status
        "is_indefinite": kobetsu_emp.is_indefinite_employment or employee.is_indefinite_employment,
        "is_over_60": (employee.age or 0) >= 60 if employee.age else False,
        "is_kyotei_taisho": contract.is_kyotei_taisho,
        "is_mukeiko_60over": contract.is_mukeiko_60over_only,

        # Conflict dates
        "conflict_date": factory.conflict_date if factory else None,
        "personal_conflict_date": kobetsu_emp.personal_conflict_date if hasattr(kobetsu_emp, 'personal_conflict_date') else None,

        # Scope changes (2024 requirement)
        "work_change_scope": "会社の定める業務",
        "location_change_scope": "会社の定める場所",

        # Renewal
        "renewal_policy": "更新する場合がある",
        "notes": "",
    }
