"""
Company Schemas - Pydantic models for Company API validation.

Includes schemas for company-level shift management that factories inherit.
"""
from datetime import date, time, datetime
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, Field


# ========================================
# COMPANY SHIFT SCHEMAS
# ========================================

class CompanyShiftBase(BaseModel):
    """Base schema for company-level shifts."""
    shift_name: str = Field(..., min_length=1, max_length=100, description="シフト名 (e.g., 昼勤, 夜勤, 第3シフト)")
    shift_start: Optional[time] = Field(None, description="シフト開始時間")
    shift_end: Optional[time] = Field(None, description="シフト終了時間")
    shift_premium: Optional[Decimal] = Field(None, ge=0, description="シフト手当（円）")
    shift_premium_type: Optional[str] = Field(None, max_length=50, description="手当種別 (e.g., 時給, 日給, 月額)")
    description: Optional[str] = Field(None, description="シフトの詳細説明")
    display_order: int = Field(default=0, description="表示順序")
    is_active: bool = Field(default=True, description="有効フラグ")


class CompanyShiftCreate(CompanyShiftBase):
    """Schema for creating a company shift."""
    pass


class CompanyShiftUpdate(BaseModel):
    """Schema for updating a company shift."""
    shift_name: Optional[str] = None
    shift_start: Optional[time] = None
    shift_end: Optional[time] = None
    shift_premium: Optional[Decimal] = Field(None, ge=0)
    shift_premium_type: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CompanyShiftResponse(CompanyShiftBase):
    """Response schema for company shift."""
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# COMPANY SCHEMAS
# ========================================

class CompanyBase(BaseModel):
    """Base schema for company."""
    name: str = Field(..., min_length=1, max_length=255)
    name_kana: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    fax: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)

    responsible_department: Optional[str] = Field(None, max_length=100)
    responsible_name: Optional[str] = Field(None, max_length=100)
    responsible_phone: Optional[str] = Field(None, max_length=50)

    contract_start: Optional[date] = None
    contract_end: Optional[date] = None

    notes: Optional[str] = None
    is_active: bool = Field(default=True)


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_kana: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    responsible_department: Optional[str] = None
    responsible_name: Optional[str] = None
    responsible_phone: Optional[str] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    """Response schema for company."""
    company_id: int
    base_madre_company_id: Optional[int] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Include shifts in response
    shifts: List[CompanyShiftResponse] = []

    class Config:
        from_attributes = True
