"""
Import Service - データインポートサービス

Handles importing factories and employees from JSON and Excel files.
Provides preview/validation before actual import.
"""
import json
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee


class ImportValidationError:
    """Represents a validation error during import."""

    def __init__(self, row: int, field: str, message: str, value: Any = None):
        self.row = row
        self.field = field
        self.message = message
        self.value = value

    def to_dict(self) -> dict:
        return {
            "row": self.row,
            "field": self.field,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None
        }


class ImportResult:
    """Result of an import operation."""

    def __init__(self):
        self.success = False
        self.total_rows = 0
        self.imported_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.errors: List[ImportValidationError] = []
        self.preview_data: List[dict] = []
        self.message = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "total_rows": self.total_rows,
            "imported_count": self.imported_count,
            "updated_count": self.updated_count,
            "skipped_count": self.skipped_count,
            "errors": [e.to_dict() for e in self.errors],
            "preview_data": self.preview_data[:100],  # Limit preview
            "message": self.message
        }


class ImportService:
    """Service for importing data from files."""

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # FACTORY IMPORT
    # ========================================

    def preview_factories_json(self, content: bytes) -> ImportResult:
        """Preview factory data from JSON file."""
        result = ImportResult()

        try:
            data = json.loads(content.decode('utf-8'))

            # Handle both single object and array
            if isinstance(data, dict):
                factories = [data]
            else:
                factories = data

            result.total_rows = len(factories)

            for idx, factory_data in enumerate(factories, 1):
                validated, errors = self._validate_factory(idx, factory_data)
                result.errors.extend(errors)

                # Add to preview with validation status
                preview_item = {
                    "row": idx,
                    "company_name": factory_data.get("company_name", factory_data.get("派遣先名", "")),
                    "plant_name": factory_data.get("plant_name", factory_data.get("工場名", "")),
                    "conflict_date": factory_data.get("conflict_date", factory_data.get("抵触日", "")),
                    "is_valid": len(errors) == 0,
                    "errors": [e.message for e in errors],
                    "_raw": factory_data
                }
                result.preview_data.append(preview_item)

            result.success = len(result.errors) == 0
            result.message = f"{result.total_rows}件の工場データを読み込みました" if result.success else f"{len(result.errors)}件のエラーがあります"

        except json.JSONDecodeError as e:
            result.errors.append(ImportValidationError(0, "file", f"JSON解析エラー: {str(e)}"))
            result.message = "JSONファイルの形式が正しくありません"
        except Exception as e:
            result.errors.append(ImportValidationError(0, "file", f"エラー: {str(e)}"))
            result.message = f"ファイル読み込みエラー: {str(e)}"

        return result

    def preview_factories_excel(self, content: bytes) -> ImportResult:
        """Preview factory data from Excel file."""
        result = ImportResult()

        try:
            df = pd.read_excel(BytesIO(content), engine='openpyxl')
            result.total_rows = len(df)

            # Map Japanese column names to English
            column_mapping = {
                '派遣先名': 'company_name',
                '会社名': 'company_name',
                '工場名': 'plant_name',
                '工場住所': 'plant_address',
                '抵触日': 'conflict_date',
                '派遣先責任者': 'client_responsible_name',
                '派遣先苦情担当者': 'client_complaint_name',
                '締め日': 'closing_date',
                '支払日': 'payment_date',
            }

            df = df.rename(columns=column_mapping)

            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel row (1-indexed + header)
                factory_data = row.to_dict()

                # Clean NaN values
                factory_data = {k: (None if pd.isna(v) else v) for k, v in factory_data.items()}

                validated, errors = self._validate_factory(row_num, factory_data)
                result.errors.extend(errors)

                preview_item = {
                    "row": row_num,
                    "company_name": factory_data.get("company_name", ""),
                    "plant_name": factory_data.get("plant_name", ""),
                    "conflict_date": str(factory_data.get("conflict_date", "")) if factory_data.get("conflict_date") else "",
                    "is_valid": len([e for e in errors if e.row == row_num]) == 0,
                    "errors": [e.message for e in errors if e.row == row_num],
                    "_raw": factory_data
                }
                result.preview_data.append(preview_item)

            result.success = len(result.errors) == 0
            result.message = f"{result.total_rows}件の工場データを読み込みました" if result.success else f"{len(result.errors)}件のエラーがあります"

        except Exception as e:
            result.errors.append(ImportValidationError(0, "file", f"Excelエラー: {str(e)}"))
            result.message = f"Excelファイル読み込みエラー: {str(e)}"

        return result

    def import_factories(self, preview_data: List[dict], mode: str = "create") -> ImportResult:
        """
        Actually import factories after preview confirmation.

        Args:
            preview_data: Validated data from preview
            mode: "create" (skip existing), "update" (update existing), "sync" (delete missing)
        """
        result = ImportResult()
        result.total_rows = len(preview_data)

        try:
            for item in preview_data:
                if not item.get("is_valid", False):
                    result.skipped_count += 1
                    continue

                raw_data = item.get("_raw", {})
                factory_id = f"{raw_data.get('company_name', '')}_{raw_data.get('plant_name', '')}".replace(" ", "_")

                # Check if exists
                existing = self.db.query(Factory).filter(Factory.factory_id == factory_id).first()

                if existing:
                    if mode in ["update", "sync"]:
                        # Update existing
                        self._update_factory(existing, raw_data)
                        result.updated_count += 1
                    else:
                        result.skipped_count += 1
                else:
                    # Create new
                    factory = self._create_factory(factory_id, raw_data)
                    self.db.add(factory)
                    result.imported_count += 1

            self.db.commit()
            result.success = True
            result.message = f"インポート完了: 新規{result.imported_count}件, 更新{result.updated_count}件, スキップ{result.skipped_count}件"

        except Exception as e:
            self.db.rollback()
            result.errors.append(ImportValidationError(0, "import", f"インポートエラー: {str(e)}"))
            result.message = f"インポート失敗: {str(e)}"

        return result

    def _validate_factory(self, row: int, data: dict) -> Tuple[dict, List[ImportValidationError]]:
        """Validate a single factory record."""
        errors = []

        company_name = data.get("company_name") or data.get("派遣先名")
        plant_name = data.get("plant_name") or data.get("工場名")

        if not company_name:
            errors.append(ImportValidationError(row, "company_name", "派遣先名は必須です"))

        if not plant_name:
            errors.append(ImportValidationError(row, "plant_name", "工場名は必須です"))

        # Validate conflict_date if present
        conflict_date = data.get("conflict_date") or data.get("抵触日")
        if conflict_date:
            try:
                if isinstance(conflict_date, str):
                    datetime.strptime(conflict_date, "%Y-%m-%d")
            except ValueError:
                errors.append(ImportValidationError(row, "conflict_date", "抵触日の形式が正しくありません (YYYY-MM-DD)", conflict_date))

        return data, errors

    def _create_factory(self, factory_id: str, data: dict) -> Factory:
        """Create a new Factory from import data."""
        conflict_date = data.get("conflict_date") or data.get("抵触日")
        if isinstance(conflict_date, str):
            conflict_date = datetime.strptime(conflict_date, "%Y-%m-%d").date()
        elif isinstance(conflict_date, datetime):
            conflict_date = conflict_date.date()

        return Factory(
            factory_id=factory_id,
            company_name=data.get("company_name") or data.get("派遣先名", ""),
            company_address=data.get("company_address") or data.get("派遣先住所"),
            company_phone=data.get("company_phone") or data.get("派遣先電話"),
            plant_name=data.get("plant_name") or data.get("工場名", ""),
            plant_address=data.get("plant_address") or data.get("工場住所"),
            plant_phone=data.get("plant_phone") or data.get("工場電話"),
            client_responsible_name=data.get("client_responsible_name") or data.get("派遣先責任者"),
            client_responsible_department=data.get("client_responsible_department") or data.get("派遣先責任者部署"),
            client_complaint_name=data.get("client_complaint_name") or data.get("派遣先苦情担当者"),
            client_complaint_department=data.get("client_complaint_department") or data.get("派遣先苦情担当部署"),
            dispatch_responsible_name=data.get("dispatch_responsible_name") or data.get("派遣元責任者"),
            dispatch_complaint_name=data.get("dispatch_complaint_name") or data.get("派遣元苦情担当者"),
            conflict_date=conflict_date,
            closing_date=data.get("closing_date") or data.get("締め日"),
            payment_date=data.get("payment_date") or data.get("支払日"),
            break_minutes=int(data.get("break_minutes", 60)),
            is_active=True
        )

    def _update_factory(self, factory: Factory, data: dict):
        """Update existing factory with new data."""
        if data.get("company_address") or data.get("派遣先住所"):
            factory.company_address = data.get("company_address") or data.get("派遣先住所")
        if data.get("plant_address") or data.get("工場住所"):
            factory.plant_address = data.get("plant_address") or data.get("工場住所")
        if data.get("conflict_date") or data.get("抵触日"):
            cd = data.get("conflict_date") or data.get("抵触日")
            if isinstance(cd, str):
                factory.conflict_date = datetime.strptime(cd, "%Y-%m-%d").date()
            elif isinstance(cd, datetime):
                factory.conflict_date = cd.date()

    # ========================================
    # EMPLOYEE IMPORT
    # ========================================

    def preview_employees_excel(self, content: bytes) -> ImportResult:
        """Preview employee data from Excel file."""
        result = ImportResult()

        try:
            df = pd.read_excel(BytesIO(content), engine='openpyxl')
            result.total_rows = len(df)

            # Map Japanese column names
            column_mapping = {
                '社員№': 'employee_number',
                '社員番号': 'employee_number',
                '氏名': 'full_name_kanji',
                'カナ': 'full_name_kana',
                'ローマ字': 'full_name_romaji',
                '性別': 'gender',
                '生年月日': 'date_of_birth',
                '国籍': 'nationality',
                '住所': 'address',
                '電話番号': 'phone',
                '携帯電話': 'mobile',
                '入社日': 'hire_date',
                '退社日': 'termination_date',
                '派遣先': 'company_name',
                '工場': 'plant_name',
                '配属先': 'department',
                'ライン': 'line_name',
                '時給': 'hourly_rate',
                '請求単価': 'billing_rate',
                '在留資格': 'visa_type',
                'ビザ期限': 'visa_expiry_date',
                '在留カード番号': 'zairyu_card_number',
                '雇用保険': 'has_employment_insurance',
                '健康保険': 'has_health_insurance',
                '厚生年金': 'has_pension_insurance',
                '備考': 'notes',
            }

            df = df.rename(columns=column_mapping)

            for idx, row in df.iterrows():
                row_num = idx + 2
                emp_data = row.to_dict()
                emp_data = {k: (None if pd.isna(v) else v) for k, v in emp_data.items()}

                validated, errors = self._validate_employee(row_num, emp_data)
                result.errors.extend(errors)

                preview_item = {
                    "row": row_num,
                    "employee_number": emp_data.get("employee_number", ""),
                    "full_name_kanji": emp_data.get("full_name_kanji", ""),
                    "full_name_kana": emp_data.get("full_name_kana", ""),
                    "company_name": emp_data.get("company_name", ""),
                    "hourly_rate": emp_data.get("hourly_rate"),
                    "hire_date": str(emp_data.get("hire_date", "")) if emp_data.get("hire_date") else "",
                    "is_valid": len([e for e in errors if e.row == row_num]) == 0,
                    "errors": [e.message for e in errors if e.row == row_num],
                    "_raw": emp_data
                }
                result.preview_data.append(preview_item)

            result.success = len(result.errors) == 0
            result.message = f"{result.total_rows}件の従業員データを読み込みました" if result.success else f"{len(result.errors)}件のエラーがあります"

        except Exception as e:
            result.errors.append(ImportValidationError(0, "file", f"Excelエラー: {str(e)}"))
            result.message = f"Excelファイル読み込みエラー: {str(e)}"

        return result

    def import_employees(self, preview_data: List[dict], mode: str = "sync") -> ImportResult:
        """
        Import employees after preview confirmation.

        Args:
            preview_data: Validated data from preview
            mode: "create", "update", or "sync" (update existing, create new)
        """
        result = ImportResult()
        result.total_rows = len(preview_data)

        try:
            for item in preview_data:
                if not item.get("is_valid", False):
                    result.skipped_count += 1
                    continue

                raw_data = item.get("_raw", {})
                employee_number = str(raw_data.get("employee_number", "")).strip()

                if not employee_number:
                    result.skipped_count += 1
                    continue

                # Check if exists
                existing = self.db.query(Employee).filter(
                    Employee.employee_number == employee_number
                ).first()

                if existing:
                    if mode in ["update", "sync"]:
                        self._update_employee(existing, raw_data)
                        result.updated_count += 1
                    else:
                        result.skipped_count += 1
                else:
                    if mode in ["create", "sync"]:
                        employee = self._create_employee(raw_data)
                        self.db.add(employee)
                        result.imported_count += 1
                    else:
                        result.skipped_count += 1

            self.db.commit()
            result.success = True
            result.message = f"同期完了: 新規{result.imported_count}件, 更新{result.updated_count}件, スキップ{result.skipped_count}件"

        except Exception as e:
            self.db.rollback()
            result.errors.append(ImportValidationError(0, "import", f"インポートエラー: {str(e)}"))
            result.message = f"インポート失敗: {str(e)}"

        return result

    def _validate_employee(self, row: int, data: dict) -> Tuple[dict, List[ImportValidationError]]:
        """Validate a single employee record."""
        errors = []

        if not data.get("employee_number"):
            errors.append(ImportValidationError(row, "employee_number", "社員番号は必須です"))

        if not data.get("full_name_kanji"):
            errors.append(ImportValidationError(row, "full_name_kanji", "氏名は必須です"))

        if not data.get("full_name_kana"):
            errors.append(ImportValidationError(row, "full_name_kana", "カナは必須です"))

        if not data.get("hire_date"):
            errors.append(ImportValidationError(row, "hire_date", "入社日は必須です"))

        # Validate dates
        for date_field in ["hire_date", "termination_date", "date_of_birth", "visa_expiry_date"]:
            if data.get(date_field):
                try:
                    val = data[date_field]
                    if isinstance(val, str):
                        datetime.strptime(val, "%Y-%m-%d")
                except ValueError:
                    errors.append(ImportValidationError(row, date_field, f"{date_field}の日付形式が正しくありません", data[date_field]))

        return data, errors

    def _create_employee(self, data: dict) -> Employee:
        """Create new Employee from import data."""

        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                return datetime.strptime(val, "%Y-%m-%d").date()
            return None

        def parse_bool(val):
            if val is None:
                return True
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ['true', '1', 'yes', 'はい', '○', '◯']
            return bool(val)

        def parse_decimal(val):
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except:
                return None

        return Employee(
            employee_number=str(data.get("employee_number", "")).strip(),
            full_name_kanji=data.get("full_name_kanji", ""),
            full_name_kana=data.get("full_name_kana", ""),
            full_name_romaji=data.get("full_name_romaji"),
            gender=data.get("gender"),
            date_of_birth=parse_date(data.get("date_of_birth")),
            nationality=data.get("nationality", "ベトナム"),
            address=data.get("address"),
            phone=data.get("phone"),
            mobile=data.get("mobile"),
            hire_date=parse_date(data.get("hire_date")) or date.today(),
            termination_date=parse_date(data.get("termination_date")),
            company_name=data.get("company_name"),
            plant_name=data.get("plant_name"),
            department=data.get("department"),
            line_name=data.get("line_name"),
            hourly_rate=parse_decimal(data.get("hourly_rate")),
            billing_rate=parse_decimal(data.get("billing_rate")),
            visa_type=data.get("visa_type"),
            visa_expiry_date=parse_date(data.get("visa_expiry_date")),
            zairyu_card_number=data.get("zairyu_card_number"),
            has_employment_insurance=parse_bool(data.get("has_employment_insurance")),
            has_health_insurance=parse_bool(data.get("has_health_insurance")),
            has_pension_insurance=parse_bool(data.get("has_pension_insurance")),
            notes=data.get("notes"),
            status="active"
        )

    def _update_employee(self, employee: Employee, data: dict):
        """Update existing employee with new data."""

        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                return datetime.strptime(val, "%Y-%m-%d").date()
            return None

        def parse_decimal(val):
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except:
                return None

        # Update fields if provided
        if data.get("full_name_kanji"):
            employee.full_name_kanji = data["full_name_kanji"]
        if data.get("full_name_kana"):
            employee.full_name_kana = data["full_name_kana"]
        if data.get("company_name"):
            employee.company_name = data["company_name"]
        if data.get("plant_name"):
            employee.plant_name = data["plant_name"]
        if data.get("department"):
            employee.department = data["department"]
        if data.get("line_name"):
            employee.line_name = data["line_name"]
        if data.get("hourly_rate"):
            employee.hourly_rate = parse_decimal(data["hourly_rate"])
        if data.get("billing_rate"):
            employee.billing_rate = parse_decimal(data["billing_rate"])
        if data.get("visa_expiry_date"):
            employee.visa_expiry_date = parse_date(data["visa_expiry_date"])
        if data.get("termination_date"):
            employee.termination_date = parse_date(data["termination_date"])
            if employee.termination_date:
                employee.status = "resigned"
