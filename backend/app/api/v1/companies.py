"""
Company and Plant API Router

Provides endpoints for companies and plants synced from Base Madre.
These match the Base Madre schema for consistency.
Includes company-level shift management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.company import Company, CompanyShift
from app.models.plant import Plant
from app.models.jigyosho import Jigyosho
from app.schemas.company import (
    CompanyShiftCreate,
    CompanyShiftUpdate,
    CompanyShiftResponse
)


router = APIRouter(redirect_slashes=False)


# ========================================
# COMPANIES ENDPOINTS
# ========================================

@router.get("/companies", response_model=List[dict])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of companies.

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Max number of records to return
    - search: Search by company name
    - is_active: Filter by active status
    """
    query = db.query(Company)

    if is_active is not None:
        query = query.filter(Company.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Company.name.ilike(search_term)) |
            (Company.name_kana.ilike(search_term))
        )

    query = query.order_by(Company.name)
    total = query.count()
    companies = query.offset(skip).limit(limit).all()

    return [company.to_dict() for company in companies]


@router.get("/companies/{company_id}", response_model=dict)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get a specific company by ID."""
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )
    return company.to_dict()


@router.get("/companies/{company_id}/plants", response_model=List[dict])
async def get_company_plants(company_id: int, db: Session = Depends(get_db)):
    """Get all plants for a specific company."""
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )

    plants = db.query(Plant).filter(
        Plant.company_id == company_id,
        Plant.is_active == True
    ).order_by(Plant.plant_name).all()

    return [plant.to_dict() for plant in plants]


# ========================================
# PLANTS ENDPOINTS
# ========================================

@router.get("/plants", response_model=List[dict])
async def list_plants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of plants.

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Max number of records to return
    - company_id: Filter by company ID
    - search: Search by plant name
    - is_active: Filter by active status
    """
    query = db.query(Plant).options(joinedload(Plant.company))

    if is_active is not None:
        query = query.filter(Plant.is_active == is_active)

    if company_id:
        query = query.filter(Plant.company_id == company_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(Plant.plant_name.ilike(search_term))

    query = query.order_by(Plant.plant_name)
    total = query.count()
    plants = query.offset(skip).limit(limit).all()

    return [plant.to_dict() for plant in plants]


@router.get("/plants/{plant_id}", response_model=dict)
async def get_plant(plant_id: int, db: Session = Depends(get_db)):
    """Get a specific plant by ID."""
    plant = db.query(Plant).options(joinedload(Plant.company)).filter(
        Plant.plant_id == plant_id
    ).first()
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant with ID {plant_id} not found"
        )
    return plant.to_dict()


# ========================================
# SYNC STATUS ENDPOINTS
# ========================================

@router.get("/sync/status", response_model=dict)
async def get_sync_status(db: Session = Depends(get_db)):
    """
    Get sync status for companies and plants.

    Returns counts and last sync timestamps.
    """
    # Companies stats
    total_companies = db.query(func.count(Company.company_id)).scalar()
    synced_companies = db.query(func.count(Company.company_id)).filter(
        Company.base_madre_company_id.isnot(None)
    ).scalar()
    last_company_sync = db.query(func.max(Company.last_synced_at)).scalar()

    # Plants stats
    total_plants = db.query(func.count(Plant.plant_id)).scalar()
    synced_plants = db.query(func.count(Plant.plant_id)).filter(
        Plant.base_madre_plant_id.isnot(None)
    ).scalar()
    last_plant_sync = db.query(func.max(Plant.last_synced_at)).scalar()

    return {
        "companies": {
            "total": total_companies,
            "synced_from_base_madre": synced_companies,
            "last_sync": last_company_sync.isoformat() if last_company_sync else None,
        },
        "plants": {
            "total": total_plants,
            "synced_from_base_madre": synced_plants,
            "last_sync": last_plant_sync.isoformat() if last_plant_sync else None,
        }
    }


# ========================================
# CASCADE OPTIONS (for form dropdowns)
# ========================================

@router.get("/options/companies", response_model=List[dict])
async def get_company_options(db: Session = Depends(get_db)):
    """Get simplified list of companies for dropdown options."""
    companies = db.query(Company).filter(Company.is_active == True).order_by(Company.name).all()
    return [
        {
            "company_id": c.company_id,
            "name": c.name,
            "name_kana": c.name_kana
        }
        for c in companies
    ]


@router.get("/options/plants", response_model=List[dict])
async def get_plant_options(
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get simplified list of plants for dropdown options."""
    query = db.query(Plant).options(joinedload(Plant.company)).filter(Plant.is_active == True)

    if company_id:
        query = query.filter(Plant.company_id == company_id)

    plants = query.order_by(Plant.plant_name).all()
    return [
        {
            "plant_id": p.plant_id,
            "company_id": p.company_id,
            "plant_name": p.plant_name,
            "company_name": p.company.name if p.company else None
        }
        for p in plants
    ]


# ========================================
# COMPANY SHIFTS ENDPOINTS
# ========================================

@router.get("/companies/{company_id}/shifts", response_model=List[CompanyShiftResponse])
async def get_company_shifts(
    company_id: int,
    include_inactive: bool = Query(False, description="Include inactive shifts"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all shifts for a specific company.

    All factories belonging to this company inherit these shifts by default
    (unless they have use_company_shifts=False).
    """
    # Verify company exists
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )

    # Query shifts
    query = db.query(CompanyShift).filter(CompanyShift.company_id == company_id)

    if not include_inactive:
        query = query.filter(CompanyShift.is_active == True)

    shifts = query.order_by(CompanyShift.display_order, CompanyShift.shift_name).all()
    return shifts


@router.post("/companies/{company_id}/shifts", response_model=CompanyShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_company_shift(
    company_id: int,
    shift_data: CompanyShiftCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new shift for a company.

    This shift will be inherited by all factories that belong to this company
    and have use_company_shifts=True.
    """
    # Verify company exists
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )

    # Create shift
    company_shift = CompanyShift(
        company_id=company_id,
        **shift_data.model_dump()
    )
    db.add(company_shift)
    db.commit()
    db.refresh(company_shift)

    return company_shift


@router.put("/companies/shifts/{shift_id}", response_model=CompanyShiftResponse)
async def update_company_shift(
    shift_id: int,
    shift_data: CompanyShiftUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a company shift.

    Changes will automatically apply to all factories that inherit this company's shifts.
    """
    shift = db.query(CompanyShift).filter(CompanyShift.id == shift_id).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company shift with ID {shift_id} not found"
        )

    # Update only provided fields
    update_data = shift_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shift, field, value)

    db.commit()
    db.refresh(shift)

    return shift


@router.delete("/companies/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a company shift (soft delete by setting is_active=False).

    This will affect all factories that inherit this company's shifts.
    """
    shift = db.query(CompanyShift).filter(CompanyShift.id == shift_id).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company shift with ID {shift_id} not found"
        )

    # Soft delete
    shift.is_active = False
    db.commit()

    return None
