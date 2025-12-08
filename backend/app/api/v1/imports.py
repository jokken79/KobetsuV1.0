"""
Import API Router - データインポートAPI

Provides endpoints for importing factories and employees from JSON/Excel files.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.rate_limit import limiter, RateLimits
from app.services.import_service import ImportService
from app.services.sync_resolver_service import SyncResolverService, ConflictStrategy

router = APIRouter()


# ========================================
# Request/Response Models
# ========================================

class PreviewItem(BaseModel):
    """Single item in preview data."""
    row: int
    is_valid: bool
    errors: List[str] = []
    _raw: dict = {}

    class Config:
        extra = "allow"


class ImportRequest(BaseModel):
    """Request to execute import after preview."""
    preview_data: List[dict]
    mode: str = "create"  # create, update, sync


class ImportResponse(BaseModel):
    """Response from import operations."""
    success: bool
    total_rows: int
    imported_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    errors: List[dict] = []
    preview_data: List[dict] = []
    message: str


# ========================================
# FACTORY IMPORT ENDPOINTS
# ========================================

@router.post("/factories/preview", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_PREVIEW)
async def preview_factory_import(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    Preview factory import from JSON or Excel file.

    Upload a file to see what will be imported before confirming.
    Supports:
    - JSON files (.json)
    - Excel files (.xlsx, .xls, .xlsm)

    Returns preview data with validation errors.
    """
    # Validate file type
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.json', '.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="サポートされていないファイル形式です。JSON または Excel ファイルをアップロードしてください。"
        )

    content = await file.read()
    service = ImportService(db)

    if filename.endswith('.json'):
        result = service.preview_factories_json(content)
    else:
        result = service.preview_factories_excel(content)

    return ImportResponse(**result.to_dict())


@router.post("/factories/execute", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def execute_factory_import(
    request: Request,
    response: Response,
    import_data: ImportRequest,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    Execute factory import after preview confirmation.

    Args:
        preview_data: Data from preview step
        mode: Import mode
            - "create": Only create new records, skip existing
            - "update": Update existing records, create new ones
            - "sync": Full sync (update + create)
    """
    service = ImportService(db)
    result = service.import_factories(import_data.preview_data, import_data.mode)
    return ImportResponse(**result.to_dict())


# ========================================
# EMPLOYEE IMPORT ENDPOINTS
# ========================================

@router.post("/employees/preview", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_PREVIEW)
async def preview_employee_import(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    Preview employee import from Excel file.

    Upload an Excel file (.xlsx, .xlsm) to see what will be imported.

    Expected columns (Japanese or English):
    - 社員№ / employee_number (required)
    - 氏名 / full_name_kanji (required)
    - カナ / full_name_kana (required)
    - 入社日 / hire_date (required)
    - その他オプション項目...

    Returns preview data with validation errors.
    """
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel ファイル (.xlsx, .xlsm) をアップロードしてください。"
        )

    content = await file.read()
    service = ImportService(db)
    result = service.preview_employees_excel(content)

    return ImportResponse(**result.to_dict())


@router.post("/employees/execute", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def execute_employee_import(
    request: Request,
    response: Response,
    import_data: ImportRequest,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    Execute employee import after preview confirmation.

    Args:
        preview_data: Data from preview step
        mode: Import mode
            - "create": Only create new records
            - "update": Only update existing records
            - "sync": Create new + update existing (recommended)
    """
    service = ImportService(db)
    result = service.import_employees(import_data.preview_data, import_data.mode)
    return ImportResponse(**result.to_dict())


@router.post("/employees/sync", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def sync_employees_from_excel(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    One-click sync employees from Excel.

    Combines preview and execute in one step for quick sync.
    - Creates new employees not in database
    - Updates existing employees with new data
    - Does NOT delete employees not in Excel

    Use this for regular sync operations.
    """
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel ファイル (.xlsx, .xlsm) をアップロードしてください。"
        )

    content = await file.read()
    service = ImportService(db)

    # Preview first
    preview_result = service.preview_employees_excel(content)

    # If there are critical errors, return preview result
    if not preview_result.success:
        return ImportResponse(**preview_result.to_dict())

    # Execute sync
    import_result = service.import_employees(preview_result.preview_data, mode="sync")
    return ImportResponse(**import_result.to_dict())


# ========================================
# SYNC-RESOLVER ENDPOINTS (Conflict Detection)
# ========================================

class ConflictResolutionRequest(BaseModel):
    """Request for resolving sync conflicts."""
    strategy: str = "source_wins"  # source_wins, db_wins, newest_wins, manual
    manual_decisions: Optional[dict] = None  # For manual strategy: {record_id: field_decisions}


@router.post("/employees/sync/analyze")
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def analyze_employee_sync(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Analyze employee sync BEFORE applying changes.

    Returns detailed analysis of:
    - New employees to create
    - Existing employees to update
    - Records with conflicting values (require decision)
    - Records in DB but not in Excel source

    Use this endpoint first to preview conflicts, then use
    /employees/sync/resolve to apply with chosen strategy.
    """
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel ファイル (.xlsx, .xlsm) をアップロードしてください。"
        )

    content = await file.read()
    import_service = ImportService(db)

    # First get preview data
    preview_result = import_service.preview_employees_excel(content)
    if not preview_result.success:
        return {
            "success": False,
            "message": "Excel parsing failed",
            "errors": preview_result.errors
        }

    # Analyze with sync resolver
    resolver = SyncResolverService(db)
    analysis = resolver.analyze_employee_sync(
        source_data=preview_result.preview_data,
        source_type="excel"
    )

    return {
        "success": True,
        "analysis": analysis.to_dict(),
        "summary": {
            "to_create": len(analysis.to_create),
            "to_update": len(analysis.to_update),
            "conflicts": len(analysis.conflicts),
            "db_only": len(analysis.db_only),
            "requires_attention": len(analysis.conflicts) > 0
        },
        "message": f"分析完了: {len(analysis.to_create)}件作成, {len(analysis.to_update)}件更新, {len(analysis.conflicts)}件コンフリクト"
    }


@router.post("/employees/sync/resolve")
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def resolve_employee_sync(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    strategy: str = Query("source_wins", description="Conflict resolution strategy"),
    db: Session = Depends(get_db),
):
    """
    Execute employee sync with conflict resolution.

    Strategies:
    - source_wins: Excel data overwrites DB (default)
    - db_wins: Keep existing DB values
    - newest_wins: Use most recently updated values
    - merge: Combine non-conflicting fields

    For complex conflicts, use /employees/sync/analyze first
    to review conflicts, then call this with appropriate strategy.
    """
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.xlsm']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel ファイル (.xlsx, .xlsm) をアップロードしてください。"
        )

    # Validate strategy
    valid_strategies = ["source_wins", "db_wins", "newest_wins", "merge"]
    if strategy not in valid_strategies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無効なストラテジー。有効な値: {', '.join(valid_strategies)}"
        )

    content = await file.read()
    import_service = ImportService(db)

    # Get preview data
    preview_result = import_service.preview_employees_excel(content)
    if not preview_result.success:
        return ImportResponse(
            success=False,
            total_rows=0,
            message="Excel parsing failed",
            errors=preview_result.errors
        )

    # Analyze
    resolver = SyncResolverService(db)
    analysis = resolver.analyze_employee_sync(
        source_data=preview_result.preview_data,
        source_type="excel"
    )

    # Resolve conflicts
    strategy_enum = ConflictStrategy(strategy)
    sync_result = resolver.resolve_employee_conflicts(
        analysis=analysis,
        strategy=strategy_enum
    )

    return {
        "success": sync_result.success,
        "total_rows": len(preview_result.preview_data),
        "created_count": sync_result.created_count,
        "updated_count": sync_result.updated_count,
        "conflict_count": sync_result.conflict_count,
        "error_count": sync_result.error_count,
        "snapshot_id": sync_result.snapshot_id,
        "errors": sync_result.errors,
        "message": f"同期完了: {sync_result.created_count}件作成, {sync_result.updated_count}件更新, {sync_result.conflict_count}件コンフリクト解決"
    }


@router.get("/employees/sync/snapshots")
async def list_sync_snapshots(
    db: Session = Depends(get_db),
):
    """
    List available sync snapshots for potential rollback.

    Each sync operation creates a snapshot that can be used
    to revert changes if needed.
    """
    resolver = SyncResolverService(db)
    snapshots = resolver.list_snapshots()

    return {
        "snapshots": snapshots,
        "count": len(snapshots)
    }


# ========================================
# FACTORY FOLDER IMPORT (JSON FILES)
# ========================================

class FolderImportRequest(BaseModel):
    """Request for folder-based import."""
    folder_path: str
    mode: str = "sync"  # create, update, sync


@router.post("/factories/folder", response_model=ImportResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def import_factories_from_folder(
    request: Request,
    response: Response,
    import_request: FolderImportRequest,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    Import all factory JSON files from a folder.

    This endpoint reads all JSON files from the specified folder and imports them.
    Expected JSON format matches the UNS-ClaudeJP config/factories structure:
    - client_company (with responsible_person and complaint_handler)
    - plant
    - lines (with assignment, job, supervisor)
    - dispatch_company
    - schedule (work_hours, break_time, conflict_date, overtime_labor)
    - payment (closing_date, payment_date, bank_account)
    - agreement

    Args:
        folder_path: Full path to folder containing factory JSON files
        mode: Import mode
            - "create": Only create new records, skip existing
            - "update"/"sync": Update existing records, create new ones

    Example folder: E:\\config\\factories
    """
    import os

    folder_path = import_request.folder_path

    # Validate folder exists
    if not os.path.exists(folder_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"フォルダが見つかりません: {folder_path}"
        )

    if not os.path.isdir(folder_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"指定されたパスはフォルダではありません: {folder_path}"
        )

    service = ImportService(db)
    result = service.import_factories_from_folder(folder_path, import_request.mode)
    return ImportResponse(**result.to_dict())


# ========================================
# TEMPLATE DOWNLOAD ENDPOINTS
# ========================================

@router.get("/templates/factories")
async def download_factory_template(
    format: str = Query("excel", description="Template format: excel or json"),
):
    """
    Download a template file for factory import.

    Returns an empty template with the expected columns/structure.
    """
    from fastapi.responses import Response

    if format == "json":
        template = {
            "company_name": "会社名を入力",
            "plant_name": "工場名を入力",
            "plant_address": "工場住所",
            "conflict_date": "2026-12-31",
            "client_responsible_name": "派遣先責任者名",
            "client_complaint_name": "苦情処理担当者名",
            "closing_date": "月末日",
            "payment_date": "翌月末日"
        }
        import json
        content = json.dumps([template], ensure_ascii=False, indent=2)
        return Response(
            content=content.encode('utf-8'),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=factory_template.json"}
        )
    else:
        # Excel template
        import pandas as pd
        from io import BytesIO

        df = pd.DataFrame([{
            "派遣先名": "",
            "工場名": "",
            "工場住所": "",
            "抵触日": "",
            "派遣先責任者": "",
            "派遣先苦情担当者": "",
            "締め日": "",
            "支払日": ""
        }])

        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=factory_template.xlsx"}
        )


# ========================================
# EMPLOYEE-FACTORY SYNC ENDPOINTS
# ========================================

class SyncEmployeesRequest(BaseModel):
    """Request for employee-factory sync."""
    excel_path: Optional[str] = None  # If None, uses default path


class SyncEmployeesResponse(BaseModel):
    """Response from employee-factory sync."""
    success: bool
    message: str
    linked_count: int = 0
    updated_count: int = 0
    not_found_employees_count: int = 0
    not_found_factories_count: int = 0
    not_found_factories: List[dict] = []
    errors: List[dict] = []


@router.post("/employees/sync-to-factories", response_model=SyncEmployeesResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def sync_employees_to_factories(
    request: Request,
    response: Response,
    sync_request: SyncEmployeesRequest = None,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    Sincroniza empleados con fábricas usando el archivo Excel de empleados.

    Lee la tabla DBGenzaiX del Excel y vincula empleados a fábricas basándose en:
    - 派遣先 (destino de envío) → company_name, plant_name
    - 配属先 (departamento) → department
    - 配属ライン (línea) → line_name

    El mapeo de 派遣先 a (company_name, plant_name) está definido en EMPLOYEE_TO_FACTORY_MAPPING.

    Args:
        excel_path: Ruta al archivo Excel (opcional).
                   Por defecto usa: D:/【新】社員台帳(UNS)T　2022.04.05～.xlsm

    Returns:
        Estadísticas de la sincronización:
        - linked_count: Nuevos vínculos creados
        - updated_count: Vínculos actualizados
        - not_found_employees_count: Empleados no encontrados en DB
        - not_found_factories_count: Fábricas no encontradas en DB
    """
    service = ImportService(db)

    # Get Excel path
    excel_path = None
    if sync_request and sync_request.excel_path:
        excel_path = sync_request.excel_path

    # If no path provided, use default
    if not excel_path:
        import os
        # Try common paths
        possible_paths = [
            'D:/【新】社員台帳(UNS)T　2022.04.05～.xlsm',
            '/app/data/shain_daicho.xlsm',
            '/d/【新】社員台帳(UNS)T　2022.04.05～.xlsm',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                excel_path = path
                break

    if not excel_path:
        return SyncEmployeesResponse(
            success=False,
            message="Excel file not found. Please provide excel_path.",
            errors=[{"error": "Excel file not found. Checked paths: D:/【新】社員台帳(UNS)T　2022.04.05～.xlsm"}]
        )

    result = service.sync_employees_from_excel(excel_path)

    return SyncEmployeesResponse(
        success=result.success,
        message=result.message,
        linked_count=result.imported_count,
        updated_count=result.updated_count,
        not_found_employees_count=result.skipped_count,
        not_found_factories_count=len(result.preview_data.get('not_found_factories', [])) if isinstance(result.preview_data, dict) else 0,
        not_found_factories=result.preview_data.get('not_found_factories', []) if isinstance(result.preview_data, dict) else [],
        errors=[{"row": e.row, "field": e.field, "message": e.message} for e in result.errors]
    )


@router.post("/employees/sync-from-db", response_model=SyncEmployeesResponse)
@limiter.limit(RateLimits.IMPORT_EXECUTE)
async def sync_employees_from_db(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # TODO: Re-enable auth in production
):
    """
    Sincroniza empleados con fábricas usando datos existentes en la base de datos.

    Usa el campo company_name del empleado para vincularlo a su fábrica.
    Este endpoint es útil cuando los empleados ya tienen company_name pero no factory_id.

    Returns:
        Estadísticas de la sincronización
    """
    service = ImportService(db)
    result = service.sync_employees_to_factories_from_db()

    return SyncEmployeesResponse(
        success=True,
        message=result.get("message", "Sync completed"),
        linked_count=result.get("linked_count", 0),
        not_found_factories_count=result.get("not_linked_count", 0),
        not_found_factories=result.get("not_linked", [])[:50]
    )


# ========================================
# TEMPLATE DOWNLOAD ENDPOINTS
# ========================================

@router.get("/templates/employees")
async def download_employee_template():
    """
    Download a template Excel file for employee import.

    Returns an empty template with all expected columns.
    """
    import pandas as pd
    from io import BytesIO
    from fastapi.responses import Response

    df = pd.DataFrame([{
        "社員№": "",
        "氏名": "",
        "カナ": "",
        "ローマ字": "",
        "性別": "",
        "生年月日": "",
        "国籍": "ベトナム",
        "住所": "",
        "電話番号": "",
        "携帯電話": "",
        "入社日": "",
        "退社日": "",
        "派遣先": "",
        "工場": "",
        "配属先": "",
        "ライン": "",
        "時給": "",
        "請求単価": "",
        "在留資格": "",
        "ビザ期限": "",
        "在留カード番号": "",
        "雇用保険": "○",
        "健康保険": "○",
        "厚生年金": "○",
        "備考": ""
    }])

    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employee_template.xlsx"}
    )
