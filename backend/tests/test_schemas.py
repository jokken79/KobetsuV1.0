"""
Tests for Pydantic schemas validation.
"""
import pytest
from datetime import date, time
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.kobetsu_keiyakusho import (
    KobetsuKeiyakushoCreate,
    KobetsuKeiyakushoUpdate,
    ContactInfo,
    ManagerInfo,
)


class TestContactInfo:
    """Test cases for ContactInfo schema."""

    def test_valid_contact_info(self):
        """Test valid contact info creation."""
        contact = ContactInfo(
            department="人事部",
            position="課長",
            name="山田太郎",
            phone="03-1234-5678"
        )
        assert contact.department == "人事部"
        assert contact.phone == "03-1234-5678"

    def test_invalid_phone_format(self):
        """Test that invalid phone format raises error."""
        with pytest.raises(ValidationError):
            ContactInfo(
                department="人事部",
                position="課長",
                name="山田太郎",
                phone="invalid-phone"  # Invalid format
            )


class TestManagerInfo:
    """Test cases for ManagerInfo schema."""

    def test_valid_manager_info(self):
        """Test valid manager info creation."""
        manager = ManagerInfo(
            department="派遣事業部",
            position="部長",
            name="鈴木一郎",
            phone="03-9876-5432",
            license_number="R1-12345"
        )
        assert manager.name == "鈴木一郎"
        assert manager.license_number == "R1-12345"

    def test_manager_without_license(self):
        """Test manager info without optional license number."""
        manager = ManagerInfo(
            department="派遣事業部",
            position="部長",
            name="鈴木一郎",
            phone="03-9876-5432"
        )
        assert manager.license_number is None


class TestKobetsuCreate:
    """Test cases for KobetsuKeiyakushoCreate schema."""

    @pytest.fixture
    def valid_create_data(self):
        """Valid data for contract creation."""
        return {
            "factory_id": 1,
            "employee_ids": [1, 2, 3],
            "contract_date": date.today(),
            "dispatch_start_date": date(2024, 12, 1),
            "dispatch_end_date": date(2025, 11, 30),
            "work_content": "製造ライン作業、検品、梱包業務の補助作業",
            "responsibility_level": "通常業務",
            "worksite_name": "テスト株式会社",
            "worksite_address": "東京都千代田区丸の内1-1-1 テストビル3階",
            "supervisor_department": "製造部",
            "supervisor_position": "課長",
            "supervisor_name": "田中太郎",
            "work_days": ["月", "火", "水", "木", "金"],
            "work_start_time": time(8, 0),
            "work_end_time": time(17, 0),
            "break_time_minutes": 60,
            "hourly_rate": Decimal("1500"),
            "overtime_rate": Decimal("1875"),
            "haken_moto_complaint_contact": {
                "department": "人事部",
                "position": "課長",
                "name": "山田花子",
                "phone": "03-1234-5678",
            },
            "haken_saki_complaint_contact": {
                "department": "総務部",
                "position": "係長",
                "name": "佐藤次郎",
                "phone": "03-9876-5432",
            },
            "haken_moto_manager": {
                "department": "派遣事業部",
                "position": "部長",
                "name": "鈴木一郎",
                "phone": "03-1234-5678",
            },
            "haken_saki_manager": {
                "department": "人事部",
                "position": "部長",
                "name": "高橋三郎",
                "phone": "03-9876-5432",
            },
        }

    def test_valid_create(self, valid_create_data):
        """Test valid contract creation."""
        contract = KobetsuKeiyakushoCreate(**valid_create_data)
        assert contract.factory_id == 1
        assert len(contract.employee_ids) == 3
        assert contract.responsibility_level == "通常業務"

    def test_invalid_responsibility_level(self, valid_create_data):
        """Test that invalid responsibility level raises error."""
        valid_create_data["responsibility_level"] = "無効な値"
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)

    def test_invalid_work_days(self, valid_create_data):
        """Test that invalid work days raise error."""
        valid_create_data["work_days"] = ["月", "Invalid"]
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)

    def test_end_date_before_start_date(self, valid_create_data):
        """Test that end date before start date raises error."""
        valid_create_data["dispatch_start_date"] = date(2025, 12, 1)
        valid_create_data["dispatch_end_date"] = date(2025, 1, 1)
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)

    def test_work_end_before_start(self, valid_create_data):
        """Test that work end time before start time raises error."""
        valid_create_data["work_start_time"] = time(17, 0)
        valid_create_data["work_end_time"] = time(8, 0)
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)

    def test_empty_employee_ids(self, valid_create_data):
        """Test that empty employee_ids raises error."""
        valid_create_data["employee_ids"] = []
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)

    def test_work_content_too_short(self, valid_create_data):
        """Test that short work content raises error."""
        valid_create_data["work_content"] = "短い"  # Less than 10 chars
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)

    def test_hourly_rate_bounds(self, valid_create_data):
        """Test hourly rate bounds validation."""
        # Too low
        valid_create_data["hourly_rate"] = Decimal("500")
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)

        # Too high
        valid_create_data["hourly_rate"] = Decimal("15000")
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoCreate(**valid_create_data)


class TestKobetsuUpdate:
    """Test cases for KobetsuKeiyakushoUpdate schema."""

    def test_partial_update(self):
        """Test partial update with only some fields."""
        update = KobetsuKeiyakushoUpdate(
            work_content="更新された業務内容です。新しい作業追加。",
            notes="テストメモ"
        )
        assert update.work_content is not None
        assert update.hourly_rate is None
        assert update.status is None

    def test_status_validation(self):
        """Test that invalid status raises error."""
        with pytest.raises(ValidationError):
            KobetsuKeiyakushoUpdate(status="invalid_status")

    def test_valid_status_values(self):
        """Test all valid status values."""
        valid_statuses = ["draft", "active", "expired", "cancelled", "renewed"]
        for status in valid_statuses:
            update = KobetsuKeiyakushoUpdate(status=status)
            assert update.status == status
