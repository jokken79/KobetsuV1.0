"""
Employee Model - 派遣社員 (Dispatch Worker)

Based on DBGenzai structure from Excel and Employee model from UNS-ClaudeJP-6.0.0
"""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date,
    DateTime, Numeric, ForeignKey, Index, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class EmployeeStatus(enum.Enum):
    """Employee status enum."""
    ACTIVE = "active"  # 在籍
    RESIGNED = "resigned"  # 退社
    ON_LEAVE = "on_leave"  # 休職
    TRANSFERRED = "transferred"  # 転籍


class Gender(enum.Enum):
    """Gender enum."""
    MALE = "male"  # 男
    FEMALE = "female"  # 女
    OTHER = "other"


class Employee(Base):
    """
    派遣社員 - Dispatch worker information.

    Matches DBGenzai structure from Excel with additional fields
    from UNS-ClaudeJP-6.0.0 Employee model.
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    # ========================================
    # 識別情報 (Identifiers)
    # ========================================
    employee_number = Column(String(20), unique=True, nullable=False, index=True)  # 社員№
    hakenmoto_id = Column(String(50), index=True)  # 派遣元管理番号
    rirekisho_id = Column(String(50))  # 履歴書ID (link to candidate)

    # ========================================
    # 基本情報 (Basic Info)
    # ========================================
    full_name_kanji = Column(String(100), nullable=False)  # 氏名
    full_name_kana = Column(String(100), nullable=False, index=True)  # カナ
    full_name_romaji = Column(String(100))  # ローマ字

    gender = Column(String(10))  # 性別
    date_of_birth = Column(Date)  # 生年月日
    age = Column(Integer)  # 年齢 (calculated)

    nationality = Column(String(50), default="ベトナム")  # 国籍

    # ========================================
    # 連絡先 (Contact)
    # ========================================
    postal_code = Column(String(10))  # 郵便番号
    address = Column(Text)  # 住所
    phone = Column(String(20))  # 電話番号
    mobile = Column(String(20))  # 携帯電話
    email = Column(String(255))  # メール

    emergency_contact_name = Column(String(100))  # 緊急連絡先氏名
    emergency_contact_phone = Column(String(20))  # 緊急連絡先電話
    emergency_contact_relationship = Column(String(50))  # 続柄

    # ========================================
    # 雇用情報 (Employment)
    # ========================================
    hire_date = Column(Date, nullable=False, index=True)  # 入社日
    termination_date = Column(Date)  # 退社日
    termination_reason = Column(Text)  # 退社理由

    status = Column(String(20), default="active", index=True)  # 現在 (在籍/退社)

    contract_type = Column(String(50))  # 契約種類 (有期/無期)
    employment_type = Column(String(50))  # 雇用形態

    # ========================================
    # 派遣先情報 (Current Assignment)
    # ========================================
    factory_id = Column(Integer, ForeignKey("factories.id"), index=True)
    factory_line_id = Column(Integer, ForeignKey("factory_lines.id"))

    # Denormalized for quick access (also in factory/line)
    company_name = Column(String(255))  # 派遣先
    plant_name = Column(String(255))  # 工場名
    department = Column(String(100))  # 配属先
    line_name = Column(String(100))  # ライン
    position = Column(String(100))  # 職種

    # ========================================
    # 給与情報 (Salary)
    # ========================================
    hourly_rate = Column(Numeric(8, 2))  # 時給
    billing_rate = Column(Numeric(8, 2))  # 請求単価
    transportation_allowance = Column(Numeric(8, 2), default=0)  # 交通費

    # ========================================
    # 在留資格 (Visa/Residence)
    # ========================================
    visa_type = Column(String(100))  # 在留資格
    visa_status = Column(String(100))  # 在留資格状態
    visa_expiry_date = Column(Date, index=True)  # ビザ期限
    zairyu_card_number = Column(String(50))  # 在留カード番号
    zairyu_card_expiry = Column(Date)  # 在留カード有効期限

    passport_number = Column(String(50))  # パスポート番号
    passport_expiry = Column(Date)  # パスポート有効期限

    # ========================================
    # 保険情報 (Insurance)
    # ========================================
    has_employment_insurance = Column(Boolean, default=True)  # 雇用保険
    employment_insurance_number = Column(String(50))  # 雇用保険番号

    has_health_insurance = Column(Boolean, default=True)  # 健康保険
    health_insurance_number = Column(String(50))  # 健康保険番号

    has_pension_insurance = Column(Boolean, default=True)  # 厚生年金
    pension_insurance_number = Column(String(50))  # 厚生年金番号

    has_workers_comp = Column(Boolean, default=True)  # 労災保険

    # ========================================
    # 有給休暇 (Paid Leave)
    # ========================================
    yukyu_total = Column(Integer, default=0)  # 有給合計
    yukyu_used = Column(Integer, default=0)  # 有給使用
    yukyu_remaining = Column(Integer, default=0)  # 有給残
    yukyu_grant_date = Column(Date)  # 有給付与日

    # ========================================
    # 住居情報 (Housing)
    # ========================================
    apartment_id = Column(Integer)  # アパートID (FK if apartments table exists)
    apartment_name = Column(String(255))  # アパート名
    apartment_room = Column(String(50))  # 部屋番号
    apartment_rent = Column(Numeric(8, 2))  # 家賃
    is_corporate_housing = Column(Boolean, default=False)  # 社宅
    housing_subsidy = Column(Numeric(8, 2), default=0)  # 住宅手当

    # ========================================
    # 銀行口座 (Bank Account)
    # ========================================
    bank_name = Column(String(100))  # 銀行名
    bank_branch = Column(String(100))  # 支店名
    bank_account_type = Column(String(20))  # 口座種別
    bank_account_number = Column(String(20))  # 口座番号
    bank_account_holder = Column(String(100))  # 口座名義

    # ========================================
    # 資格・免許 (Qualifications)
    # ========================================
    qualifications = Column(Text)  # 資格一覧 (JSON or comma-separated)
    drivers_license = Column(String(50))  # 運転免許
    drivers_license_expiry = Column(Date)  # 運転免許有効期限
    forklift_license = Column(Boolean, default=False)  # フォークリフト

    # ========================================
    # メモ・その他
    # ========================================
    notes = Column(Text)  # 備考
    photo_url = Column(String(500))  # 写真URL

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)

    # ========================================
    # Relationships
    # ========================================
    factory = relationship("Factory", back_populates="employees")
    factory_line = relationship("FactoryLine", back_populates="employees")
    contracts = relationship("KobetsuEmployee", back_populates="employee")

    __table_args__ = (
        Index('ix_employees_name_kana', 'full_name_kana'),
        Index('ix_employees_company', 'company_name'),
        Index('ix_employees_status_company', 'status', 'company_name'),
        Index('ix_employees_visa_expiry', 'visa_expiry_date'),
    )

    def __repr__(self):
        return f"<Employee {self.employee_number}: {self.full_name_kanji}>"

    @property
    def calculated_age(self) -> Optional[int]:
        """Calculate age from date of birth."""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_indefinite_employment(self) -> bool:
        """
        Check if employee qualifies for indefinite employment (無期雇用).
        Rule: 3 years (1095 days) of continuous employment.
        """
        if not self.hire_date:
            return False
        days_employed = (date.today() - self.hire_date).days
        return days_employed >= 1095

    @property
    def employment_type_display(self) -> str:
        """Return employment type for contract display."""
        if self.is_indefinite_employment:
            return "☑無期雇用  □有期雇用"
        return "□無期雇用  ☑有期雇用"

    @property
    def display_name(self) -> str:
        """
        Return appropriate name based on nationality.
        日本人 → 漢字 (kanji)
        外国人 → カタカナ (katakana)
        """
        japanese_nationalities = ["日本", "日本人", "Japanese", "japan"]
        if self.nationality and self.nationality.lower() in [n.lower() for n in japanese_nationalities]:
            return self.full_name_kanji
        return self.full_name_kana or self.full_name_kanji

    @property
    def age_category(self) -> str:
        """
        Return age category for 派遣先通知書 document.

        Based on Excel formula:
        =IF(age<=18,"18未満(age)歳",
          IF(AND(age>=18,age<=45),"18以上45歳未満",
            IF(AND(age>=46,age<=60),"46以上60歳未満",
              IF(age<=60,"60歳未満","60歳以上"))))
        """
        age = self.calculated_age
        if age is None:
            return ""

        if age < 18:
            return f"18未満({age})歳"
        elif age >= 18 and age <= 45:
            return "18以上45歳未満"
        elif age >= 46 and age <= 60:
            return "46以上60歳未満"
        else:  # age > 60
            return "60歳以上"
