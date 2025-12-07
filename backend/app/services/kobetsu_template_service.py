"""
Kobetsu Template Service - Template-based 個別契約書 generation.

This service generates 個別契約書 documents by filling an existing Excel template
with data from the database. Unlike the XML-based generator, this preserves:
- All formatting (borders, colors, fonts)
- VBA macros
- Print settings
- Original template structure

Template: 個別契約書高雄工業TEXPERT3.xlsm
Sheet: 個別契約書
Print Area: A1:Y67 (Columns Z-AA contain auxiliary formulas - DO NOT MODIFY)
"""
import logging
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Union

from openpyxl import load_workbook
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from app.core.config import settings
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.models.factory import Factory

logger = logging.getLogger(__name__)


class KobetsuTemplateService:
    """
    Generates 個別契約書 from Excel template maintaining all formatting and macros.

    Usage:
        service = KobetsuTemplateService()
        xlsx_bytes = service.generate_from_contract(contract, db_session)
        # or
        xlsx_bytes = service.generate_from_data(data_dict)
    """

    # Template location - can be customized via settings
    TEMPLATE_PATH = Path("/app/templates/個別契約書高雄工業TEXPERT3.xlsm")
    SHEET_NAME = "個別契約書"

    # Fallback template path (for local development)
    FALLBACK_TEMPLATE_PATH = Path("個別契約書高雄工業TEXPERT3.xlsm")

    def __init__(self, template_path: Optional[Path] = None):
        """
        Initialize the service.

        Args:
            template_path: Optional custom template path
        """
        if template_path:
            self.template_path = template_path
        elif self.TEMPLATE_PATH.exists():
            self.template_path = self.TEMPLATE_PATH
        elif self.FALLBACK_TEMPLATE_PATH.exists():
            self.template_path = self.FALLBACK_TEMPLATE_PATH
        else:
            # Try to find in the project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            alt_path = project_root / "個別契約書高雄工業TEXPERT3.xlsm"
            if alt_path.exists():
                self.template_path = alt_path
            else:
                raise FileNotFoundError(
                    f"Template not found at {self.TEMPLATE_PATH}, "
                    f"{self.FALLBACK_TEMPLATE_PATH}, or {alt_path}"
                )

    def generate_from_contract(
        self,
        contract: KobetsuKeiyakusho,
        factory: Optional[Factory] = None
    ) -> bytes:
        """
        Generate 個別契約書 from a contract model.

        Args:
            contract: KobetsuKeiyakusho model instance
            factory: Optional Factory model (if not provided, uses contract.factory)

        Returns:
            bytes: The generated .xlsm file content
        """
        if factory is None:
            factory = contract.factory

        data = self._build_data_from_contract(contract, factory)
        return self.generate_from_data(data)

    def generate_from_data(self, data: Dict[str, Any]) -> bytes:
        """
        Generate 個別契約書 from a data dictionary.

        Args:
            data: Dictionary with all contract data fields

        Returns:
            bytes: The generated .xlsm file content
        """
        # Load template with VBA macros preserved
        wb = load_workbook(str(self.template_path), keep_vba=True)

        # Get the target sheet
        if self.SHEET_NAME not in wb.sheetnames:
            # Try to find a sheet with similar name
            for name in wb.sheetnames:
                if "個別" in name or "契約" in name:
                    ws = wb[name]
                    break
            else:
                ws = wb.active
                logger.warning(f"Sheet '{self.SHEET_NAME}' not found, using active sheet")
        else:
            ws = wb[self.SHEET_NAME]

        # Fill all cells according to mapping
        self._fill_sheet(ws, data)

        # Save to bytes
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return output.getvalue()

    def _fill_sheet(self, ws: Worksheet, data: Dict[str, Any]) -> None:
        """
        Fill the worksheet with contract data.

        All cell references are based on the template analysis:
        - Print area: A1:Y67
        - Auxiliary formulas in Z-AA should NOT be modified
        """
        # ================================================================
        # SECTION: 派遣先 (Client Company) - Rows 4-8
        # ================================================================

        # Row 4: 派遣先事業所 (Client company)
        self._set_cell(ws, 'E4', data.get('client_company_name', ''))
        self._set_cell(ws, 'N4', data.get('client_address', ''))
        self._set_cell(ws, 'U4', data.get('client_tel', ''))

        # Row 5: 事業所 (Branch office)
        self._set_cell(ws, 'E5', data.get('client_branch_name', data.get('client_company_name', '')))
        self._set_cell(ws, 'N5', data.get('client_branch_address', data.get('client_address', '')))
        self._set_cell(ws, 'U5', data.get('client_branch_tel', data.get('client_tel', '')))

        # Row 6: 組織単位 & 派遣期間終了日
        self._set_cell(ws, 'E6', data.get('organizational_unit', ''))
        self._set_cell(ws, 'J6', self._format_japanese_date(data.get('dispatch_end_date')))

        # Row 7: 指揮命令者 (Supervisor)
        self._set_cell(ws, 'E7', data.get('supervisor_dept', ''))
        self._set_cell(ws, 'I7', data.get('supervisor_position', ''))
        self._set_cell(ws, 'K7', data.get('supervisor_name', ''))

        # Row 8: 就業場所 (Work location)
        self._set_cell(ws, 'E8', data.get('work_location', data.get('worksite_name', '')))

        # ================================================================
        # SECTION: 派遣元 (Dispatch Agency - UNS) - Rows 9-12
        # ================================================================

        # Row 10: 派遣元事業所 (Agency company)
        self._set_cell(ws, 'E10', data.get('agency_company_name', settings.COMPANY_NAME))
        self._set_cell(ws, 'N10', data.get('agency_address', settings.COMPANY_ADDRESS))
        self._set_cell(ws, 'U10', data.get('agency_tel', settings.COMPANY_TEL))

        # Row 11: 派遣元責任者 (Dispatch manager)
        self._set_cell(ws, 'E11', data.get('agency_branch_name', settings.DISPATCH_RESPONSIBLE_DEPARTMENT))
        self._set_cell(ws, 'K11', data.get('agency_manager_name', settings.DISPATCH_RESPONSIBLE_NAME))

        # Row 12: 取扱担当者 (Contact person)
        self._set_cell(ws, 'E12', data.get('agency_department', settings.DISPATCH_RESPONSIBLE_DEPARTMENT))
        self._set_cell(ws, 'K12', data.get('agency_contact_name', settings.DISPATCH_COMPLAINT_NAME))

        # ================================================================
        # SECTION: 契約詳細 (Contract Details) - Rows 15-26
        # ================================================================

        # Row 15: 業務内容 (Job description)
        self._set_cell(ws, 'E15', data.get('job_description', data.get('work_content', '')))

        # Row 16: 派遣期間 (Dispatch period)
        self._set_cell(ws, 'E16', self._format_japanese_date(data.get('dispatch_start_date')))
        self._set_cell(ws, 'J16', self._format_japanese_date(data.get('dispatch_end_date')))
        self._set_cell(ws, 'T16', data.get('headcount', data.get('number_of_workers', 1)))

        # Row 17: 就業日 (Work days)
        self._set_cell(ws, 'E17', data.get('work_days_text', self._format_work_days(data.get('work_days'))))

        # Row 18: 就業時間 (Work hours)
        self._set_cell(ws, 'E18', self._format_time(data.get('hours_day_start', data.get('work_start_time'))))
        self._set_cell(ws, 'H18', self._format_time(data.get('hours_day_end', data.get('work_end_time'))))
        self._set_cell(ws, 'L18', self._format_time(data.get('hours_night_start')))
        self._set_cell(ws, 'P18', self._format_time(data.get('hours_night_end')))

        # Row 19: 休憩時間 (Break time)
        self._set_cell(ws, 'E19', self._format_time(data.get('break_day_start')))
        self._set_cell(ws, 'H19', self._format_time(data.get('break_day_end')))
        self._set_cell(ws, 'L19', self._format_time(data.get('break_night_start')))
        self._set_cell(ws, 'P19', self._format_time(data.get('break_night_end')))
        self._set_cell(ws, 'T19', data.get('break_minutes', data.get('break_time_minutes', 45)))

        # Row 21: 時間外労働条件 (Overtime conditions)
        overtime_text = data.get('overtime_limit')
        if not overtime_text:
            max_day = data.get('overtime_max_hours_day', 3)
            max_month = data.get('overtime_max_hours_month', 42)
            overtime_text = (
                f"{max_day}時間/日、{max_month}時間/月、320時間/年を定める。"
                "但し、特別条項の発動により、80時間/月、720時間/年を限度とし、"
                "その回数は6回/年とする。"
            )
        self._set_cell(ws, 'E21', overtime_text)

        # Row 22: 派遣料金 基本 (Base rate)
        base_rate = data.get('rate_base', data.get('hourly_rate', 0))
        if base_rate:
            self._set_cell(ws, 'E22', self._format_currency(base_rate))

            # Calculate derived rates if not provided
            overtime_rate = data.get('rate_overtime_125', data.get('overtime_rate'))
            if not overtime_rate and base_rate:
                overtime_rate = float(base_rate) * 1.25
            self._set_cell(ws, 'H22', self._format_currency(overtime_rate))

            night_rate = data.get('rate_night_125', data.get('night_shift_rate'))
            if not night_rate and base_rate:
                night_rate = float(base_rate) * 1.25
            self._set_cell(ws, 'L22', self._format_currency(night_rate))

        # Row 23: 休日・超過60時間 (Holiday and over-60h rates)
        holiday_rate = data.get('rate_holiday_135', data.get('holiday_rate'))
        if not holiday_rate and base_rate:
            holiday_rate = float(base_rate) * 1.35
        self._set_cell(ws, 'E23', self._format_currency(holiday_rate))

        over60_rate = data.get('rate_over60_150')
        if not over60_rate and base_rate:
            over60_rate = float(base_rate) * 1.50
        self._set_cell(ws, 'H23', self._format_currency(over60_rate))

        # Row 25: 支払条件 (Payment terms)
        self._set_cell(ws, 'E25', data.get('cutoff_day', '15日'))
        self._set_cell(ws, 'H25', data.get('payment_day', '当月末日'))
        self._set_cell(ws, 'L25', data.get('payment_method', '銀行振込'))

        # Row 26: 振込先 (Bank info)
        self._set_cell(ws, 'E26', data.get('bank_name', '愛知銀行'))
        self._set_cell(ws, 'H26', data.get('bank_branch', '当知支店'))
        self._set_cell(ws, 'K26', data.get('account_number', '普通2075479'))
        self._set_cell(ws, 'N26', data.get('account_holder', 'ユニバーサル企画（株）'))

        # ================================================================
        # SECTION: 派遣内容詳細 (Detailed Content) - Rows 27-40
        # ================================================================

        # Row 27: 安全・衛生 (Safety and health)
        self._set_cell(ws, 'E27', data.get('safety_details', data.get('safety_measures', '')))

        # Row 35: 便宜供与 (Welfare facilities)
        welfare = data.get('welfare_details', data.get('welfare_facilities'))
        if isinstance(welfare, list):
            welfare = '、'.join(welfare)
        self._set_cell(ws, 'E35', welfare or '')

        # Row 38: 苦情処理方法 (Complaint process)
        self._set_cell(ws, 'E38', data.get('complaint_process', ''))

        # ================================================================
        # SECTION: 署名 (Signatures) - Rows 60-67
        # ================================================================

        # Row 61: 契約締結日 (Contract date)
        self._set_cell(ws, 'E61', self._format_japanese_date(data.get('contract_date')))

        # Rows 63-66: 派遣元情報 (Agency signature block)
        self._set_cell(ws, 'N63', data.get('head_office_address', settings.COMPANY_ADDRESS))
        self._set_cell(ws, 'N64', data.get('company_name_signature', settings.COMPANY_NAME))

        # Row 65: 代表者 (Representative)
        rep_title = data.get('representative_title', settings.DISPATCH_MANAGER_POSITION)
        rep_name = data.get('representative_name', settings.DISPATCH_MANAGER_NAME)
        self._set_cell(ws, 'N65', f"{rep_title} {rep_name}")

        # Row 66: 許可番号 (License number)
        license_num = data.get('license_number', settings.COMPANY_LICENSE_NUMBER)
        self._set_cell(ws, 'N66', f"派 {license_num}" if not license_num.startswith('派') else license_num)

    def _set_cell(self, ws: Worksheet, cell_ref: str, value: Any) -> None:
        """
        Set a cell value, preserving existing formatting.

        Args:
            ws: Worksheet object
            cell_ref: Cell reference (e.g., 'E4')
            value: Value to set
        """
        if value is None or value == '':
            return  # Don't overwrite with empty values

        try:
            cell = ws[cell_ref]
            cell.value = value
        except Exception as e:
            logger.warning(f"Failed to set cell {cell_ref}: {e}")

    def _format_japanese_date(self, d: Optional[Union[date, datetime, str]]) -> str:
        """
        Format date in Japanese format (YYYY年MM月DD日).

        Args:
            d: Date object, datetime object, or ISO string

        Returns:
            Japanese formatted date string
        """
        if d is None:
            return ""

        if isinstance(d, str):
            try:
                d = datetime.fromisoformat(d.replace('Z', '+00:00')).date()
            except ValueError:
                return d

        if isinstance(d, datetime):
            d = d.date()

        if isinstance(d, date):
            return f"{d.year}年{d.month}月{d.day}日"

        return str(d)

    def _format_time(self, t: Optional[Union[time, datetime, str]]) -> str:
        """
        Format time in Japanese format (HH時MM分).

        Args:
            t: Time object, datetime object, or string

        Returns:
            Japanese formatted time string
        """
        if t is None:
            return ""

        if isinstance(t, str):
            if '時' in t:  # Already formatted
                return t
            try:
                # Parse HH:MM format
                parts = t.split(':')
                if len(parts) >= 2:
                    return f"{int(parts[0])}時{int(parts[1])}分"
            except (ValueError, IndexError):
                return t

        if isinstance(t, datetime):
            t = t.time()

        if isinstance(t, time):
            return f"{t.hour}時{t.minute:02d}分"

        return str(t)

    def _format_currency(self, amount: Optional[Union[int, float, Decimal]]) -> str:
        """
        Format currency with yen symbol.

        Args:
            amount: Numeric amount

        Returns:
            Formatted currency string (e.g., ¥1,792)
        """
        if amount is None:
            return ""

        try:
            amount_int = int(float(amount))
            return f"¥{amount_int:,}"
        except (ValueError, TypeError):
            return str(amount)

    def _format_work_days(self, work_days: Optional[list]) -> str:
        """
        Format work days list to Japanese text.

        Args:
            work_days: List of day abbreviations (e.g., ['月', '火', '水', '木', '金'])

        Returns:
            Formatted work days text
        """
        if not work_days:
            return ""

        if isinstance(work_days, str):
            return work_days

        if isinstance(work_days, list):
            if len(work_days) == 5 and set(work_days) == {'月', '火', '水', '木', '金'}:
                return "月〜金（シフトに準ずる）休日は土曜日・日曜日・年末年始・GW"
            return '・'.join(work_days)

        return str(work_days)

    def _build_data_from_contract(
        self,
        contract: KobetsuKeiyakusho,
        factory: Optional[Factory] = None
    ) -> Dict[str, Any]:
        """
        Build data dictionary from contract and factory models.

        This maps the database fields to the template cell mapping.
        """
        # Get factory info
        if factory is None and hasattr(contract, 'factory'):
            factory = contract.factory

        data = {
            # ================================================================
            # Client company (派遣先)
            # ================================================================
            'client_company_name': factory.company_name if factory else contract.worksite_name,
            'client_address': factory.company_address if factory else contract.worksite_address,
            'client_tel': factory.company_phone if factory else '',

            # Branch office (often same as company)
            'client_branch_name': (
                f"{factory.company_name} {factory.plant_name}"
                if factory and factory.plant_name
                else contract.worksite_name
            ),
            'client_branch_address': (
                factory.plant_address if factory and factory.plant_address
                else contract.worksite_address
            ),
            'client_branch_tel': factory.plant_phone if factory else '',

            # Organization unit
            'organizational_unit': contract.organizational_unit or (
                f"{factory.plant_name}" if factory else ''
            ),

            # Supervisor
            'supervisor_dept': contract.supervisor_department,
            'supervisor_position': contract.supervisor_position,
            'supervisor_name': contract.supervisor_name,

            # Work location
            'work_location': contract.worksite_name,
            'worksite_name': contract.worksite_name,

            # ================================================================
            # Contract details
            # ================================================================
            'job_description': contract.work_content,
            'work_content': contract.work_content,

            # Dispatch period
            'dispatch_start_date': contract.dispatch_start_date,
            'dispatch_end_date': contract.dispatch_end_date,
            'contract_date': contract.contract_date,
            'headcount': contract.number_of_workers,
            'number_of_workers': contract.number_of_workers,

            # Work schedule
            'work_days': contract.work_days,
            'work_start_time': contract.work_start_time,
            'work_end_time': contract.work_end_time,
            'break_time_minutes': contract.break_time_minutes,

            # Overtime
            'overtime_max_hours_day': (
                float(contract.overtime_max_hours_day)
                if contract.overtime_max_hours_day else None
            ),
            'overtime_max_hours_month': (
                float(contract.overtime_max_hours_month)
                if contract.overtime_max_hours_month else None
            ),

            # Rates
            'hourly_rate': float(contract.hourly_rate) if contract.hourly_rate else None,
            'rate_base': float(contract.hourly_rate) if contract.hourly_rate else None,
            'overtime_rate': float(contract.overtime_rate) if contract.overtime_rate else None,
            'night_shift_rate': (
                float(contract.night_shift_rate) if contract.night_shift_rate else None
            ),
            'holiday_rate': float(contract.holiday_rate) if contract.holiday_rate else None,

            # Safety and welfare
            'safety_measures': contract.safety_measures,
            'welfare_facilities': contract.welfare_facilities,

            # ================================================================
            # Agency info (派遣元 - defaults from settings)
            # ================================================================
            'agency_company_name': settings.COMPANY_NAME,
            'agency_address': settings.COMPANY_ADDRESS,
            'agency_tel': settings.COMPANY_TEL,
            'agency_branch_name': settings.DISPATCH_RESPONSIBLE_DEPARTMENT,
            'agency_manager_name': settings.DISPATCH_RESPONSIBLE_NAME,
            'agency_department': settings.DISPATCH_RESPONSIBLE_DEPARTMENT,
            'agency_contact_name': settings.DISPATCH_COMPLAINT_NAME,

            # Signature block
            'head_office_address': settings.COMPANY_ADDRESS,
            'company_name_signature': settings.COMPANY_NAME,
            'representative_title': settings.DISPATCH_MANAGER_POSITION,
            'representative_name': settings.DISPATCH_MANAGER_NAME,
            'license_number': settings.COMPANY_LICENSE_NUMBER,
        }

        # Add factory-specific work schedule if available
        if factory:
            if factory.day_shift_start:
                data['hours_day_start'] = factory.day_shift_start
            if factory.day_shift_end:
                data['hours_day_end'] = factory.day_shift_end
            if factory.night_shift_start:
                data['hours_night_start'] = factory.night_shift_start
            if factory.night_shift_end:
                data['hours_night_end'] = factory.night_shift_end
            if factory.break_minutes:
                data['break_minutes'] = factory.break_minutes

            # Payment terms from factory
            if factory.closing_date:
                data['cutoff_day'] = factory.closing_date
            if factory.payment_date:
                data['payment_day'] = factory.payment_date
            if factory.bank_account:
                data['bank_info_full'] = factory.bank_account

        return data


# Convenience function for direct usage
def generate_kobetsu_from_template(
    contract: KobetsuKeiyakusho,
    factory: Optional[Factory] = None,
    template_path: Optional[Path] = None
) -> bytes:
    """
    Generate 個別契約書 from template.

    Args:
        contract: KobetsuKeiyakusho model instance
        factory: Optional Factory model
        template_path: Optional custom template path

    Returns:
        bytes: The generated .xlsm file content
    """
    service = KobetsuTemplateService(template_path)
    return service.generate_from_contract(contract, factory)
