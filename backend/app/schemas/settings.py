# backend/app/schemas/settings.py
"""
UNS Company Settings Schema
"""

from pydantic import BaseModel, Field
from typing import Optional


class ContactInfo(BaseModel):
    """連絡先情報"""
    department: str = Field(default="", max_length=100, description="部署名")
    position: str = Field(default="", max_length=100, description="役職")
    name: str = Field(default="", max_length=100, description="氏名")
    phone: str = Field(default="", max_length=20, description="電話番号")


class ManagerInfo(ContactInfo):
    """責任者情報"""
    license_number: Optional[str] = Field(default="", max_length=50, description="講習修了証番号")


class UNSCompanySettings(BaseModel):
    """UNS企画 会社設定"""
    company_name: str = Field(default="株式会社UNS企画", max_length=100)
    license_number: str = Field(default="派13-123456", max_length=50, description="派遣事業許可番号")
    address: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=20)

    # 派遣元苦情処理担当者
    complaint_contact: ContactInfo = Field(default_factory=ContactInfo)

    # 派遣元責任者
    manager: ManagerInfo = Field(default_factory=ManagerInfo)


class DefaultWorkConditions(BaseModel):
    """デフォルト就業条件"""
    work_days: list[str] = Field(default=["月", "火", "水", "木", "金"])
    work_start_time: str = Field(default="08:00")
    work_end_time: str = Field(default="17:00")
    break_time_minutes: int = Field(default=60, ge=0, le=180)
    hourly_rate: int = Field(default=1500, ge=800, le=10000)
    overtime_rate: int = Field(default=1875, ge=1000, le=15000)
    responsibility_level: str = Field(default="通常業務")


class SystemSettings(BaseModel):
    """システム全体設定"""
    uns_company: UNSCompanySettings = Field(default_factory=UNSCompanySettings)
    default_work_conditions: DefaultWorkConditions = Field(default_factory=DefaultWorkConditions)

    class Config:
        json_schema_extra = {
            "example": {
                "uns_company": {
                    "company_name": "株式会社UNS企画",
                    "license_number": "派13-123456",
                    "address": "愛知県名古屋市中区...",
                    "phone": "052-123-4567",
                    "complaint_contact": {
                        "department": "管理部",
                        "position": "部長",
                        "name": "山田太郎",
                        "phone": "052-123-4567"
                    },
                    "manager": {
                        "department": "派遣事業部",
                        "position": "部長",
                        "name": "鈴木一郎",
                        "phone": "052-123-4568",
                        "license_number": "R5-12345"
                    }
                },
                "default_work_conditions": {
                    "work_days": ["月", "火", "水", "木", "金"],
                    "work_start_time": "08:00",
                    "work_end_time": "17:00",
                    "break_time_minutes": 60,
                    "hourly_rate": 1500,
                    "overtime_rate": 1875,
                    "responsibility_level": "通常業務"
                }
            }
        }
