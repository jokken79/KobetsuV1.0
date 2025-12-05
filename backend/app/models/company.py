"""
Company model - matches Base Madre schema

This model represents client companies (派遣先企業) and is designed to sync
with Base Madre's companies table.
"""
from datetime import datetime, time
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, Time, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Company(Base):
    """
    Company (派遣先企業)

    Represents a client company that hires dispatch workers.
    Synced from Base Madre API.
    """
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_kana = Column(String(255))
    address = Column(Text)
    phone = Column(String(50))
    fax = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))

    # Responsible person
    responsible_department = Column(String(100))
    responsible_name = Column(String(100))
    responsible_phone = Column(String(50))

    # Contract period
    contract_start = Column(Date)
    contract_end = Column(Date)

    # Metadata
    notes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Base Madre sync tracking
    base_madre_company_id = Column(Integer, unique=True, index=True, comment="Reference to Base Madre company_id")
    last_synced_at = Column(DateTime, comment="Last sync from Base Madre")

    # Relationships
    jigyosho = relationship("Jigyosho", back_populates="company", cascade="all, delete-orphan")
    plants = relationship("Plant", back_populates="company", cascade="all, delete-orphan")
    kobetsu_contracts = relationship("KobetsuKeiyakusho", back_populates="company")
    shifts = relationship("CompanyShift", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id={self.company_id}, name='{self.name}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "company_id": self.company_id,
            "name": self.name,
            "name_kana": self.name_kana,
            "address": self.address,
            "phone": self.phone,
            "fax": self.fax,
            "email": self.email,
            "website": self.website,
            "responsible_department": self.responsible_department,
            "responsible_name": self.responsible_name,
            "responsible_phone": self.responsible_phone,
            "contract_start": self.contract_start.isoformat() if self.contract_start else None,
            "contract_end": self.contract_end.isoformat() if self.contract_end else None,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "base_madre_company_id": self.base_madre_company_id,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
        }


class CompanyShift(Base):
    """
    Company-level shift configuration (企業共通シフト設定)

    All factories belonging to this company inherit these shifts by default.
    Individual factories can override by setting use_company_shifts=False.

    Example: All Takao factories inherit Takao's 7:00-15:30 shift
             All Koritsu factories inherit Koritsu's 8:00-16:45 shift
    """
    __tablename__ = "company_shifts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)

    # Shift details (same structure as FactoryShift)
    shift_name = Column(String(100), nullable=False, comment="シフト名 (例: 昼勤, 夜勤, 第3シフト)")
    shift_start = Column(Time, comment="シフト開始時間")
    shift_end = Column(Time, comment="シフト終了時間")

    # Premium/bonus for this shift (夜勤手当など)
    shift_premium = Column(Numeric(10, 2), comment="シフト手当金額（円）")
    shift_premium_type = Column(String(50), comment="手当種別 (時給/日給/月額)")

    description = Column(Text, comment="シフトの説明・備考")
    display_order = Column(Integer, default=0, comment="表示順序")
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationship
    company = relationship("Company", back_populates="shifts")

    def __repr__(self):
        return f"<CompanyShift(id={self.id}, company_id={self.company_id}, name='{self.shift_name}')>"
