# backend/app/schemas/kobetsu.py
"""
Re-export kobetsu_keiyakusho schemas with shorter names.
Also includes KobetsuPDFRequest for PDF generation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Re-export from kobetsu_keiyakusho with shorter names
from .kobetsu_keiyakusho import (
    KobetsuKeiyakushoCreate as KobetsuCreate,
    KobetsuKeiyakushoUpdate as KobetsuUpdate,
    KobetsuKeiyakushoResponse as KobetsuResponse,
    KobetsuKeiyakushoList as KobetsuListItem,
    KobetsuKeiyakushoStats as KobetsuStats,
    ContactInfo,
    ManagerInfo,
    EmployeeBasicInfo,
    KobetsuEmployeeInfo,
)


class KobetsuPDFRequest(BaseModel):
    """PDF生成リクエスト"""
    contract_id: int = Field(..., gt=0, description="契約書ID")
    employee_ids: Optional[List[int]] = Field(
        None,
        description="特定の従業員のみ生成する場合のIDリスト"
    )
    document_types: Optional[List[str]] = Field(
        default=["kobetsu", "shugyo_joken"],
        description="生成する書類タイプ: kobetsu, shugyo_joken, tsuchisho, hakensaki_daicho, hakenmoto_daicho"
    )
    include_combined: bool = Field(
        default=True,
        description="個別契約書+就業条件明示書の結合版を含めるか"
    )
    output_format: str = Field(
        default="docx",
        description="出力形式: docx, pdf"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": 1,
                "employee_ids": [1, 2, 3],
                "document_types": ["kobetsu", "shugyo_joken"],
                "include_combined": True,
                "output_format": "docx"
            }
        }


class KobetsuPaginatedResponse(BaseModel):
    """ページネーション付きレスポンス"""
    items: List[KobetsuListItem]
    total: int
    page: int
    per_page: int
    pages: int


class KobetsuEmployeeAssign(BaseModel):
    """従業員割り当てリクエスト"""
    employee_id: int = Field(..., gt=0)
    individual_start_date: Optional[date] = None
    individual_end_date: Optional[date] = None
    hourly_rate: Optional[float] = Field(None, ge=0)
    overtime_rate: Optional[float] = Field(None, ge=0)
    is_indefinite_employment: bool = Field(default=False)


class KobetsuRenewRequest(BaseModel):
    """契約更新リクエスト"""
    new_end_date: date = Field(..., description="新しい終了日")
    keep_employees: bool = Field(default=True, description="従業員を引き継ぐか")
    notes: Optional[str] = Field(None, max_length=500)


class MessageResponse(BaseModel):
    """汎用メッセージレスポンス"""
    message: str
    success: bool = True
    data: Optional[dict] = None


__all__ = [
    "KobetsuCreate",
    "KobetsuUpdate",
    "KobetsuResponse",
    "KobetsuListItem",
    "KobetsuStats",
    "KobetsuPDFRequest",
    "KobetsuPaginatedResponse",
    "KobetsuEmployeeAssign",
    "KobetsuRenewRequest",
    "MessageResponse",
    "ContactInfo",
    "ManagerInfo",
    "EmployeeBasicInfo",
    "KobetsuEmployeeInfo",
]
