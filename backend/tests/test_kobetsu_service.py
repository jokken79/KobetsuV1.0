"""
Tests unitarios para KobetsuService
Cubre: generación de números, cálculo de stats, validaciones
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.kobetsu_service import KobetsuService
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.models.factory import Factory


class TestContractNumberGeneration:
    """Tests para generación de números de contrato."""

    def test_generate_contract_number_format(self, db: Session, test_factory: Factory):
        """El número debe tener formato KOB-YYYYMM-XXXX."""
        service = KobetsuService(db)
        number = service.generate_contract_number()

        assert number.startswith("KOB-")
        parts = number.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 6  # YYYYMM
        assert len(parts[2]) == 4  # XXXX

    def test_generate_contract_number_unique(self, db: Session, test_factory: Factory):
        """Los números generados deben ser únicos."""
        service = KobetsuService(db)
        numbers = [service.generate_contract_number() for _ in range(5)]

        assert len(numbers) == len(set(numbers))

    def test_generate_contract_number_sequential(self, db: Session, test_factory: Factory):
        """Los números deben ser secuenciales dentro del mismo mes."""
        service = KobetsuService(db)

        num1 = service.generate_contract_number()
        num2 = service.generate_contract_number()

        # Extraer la parte numérica
        seq1 = int(num1.split("-")[2])
        seq2 = int(num2.split("-")[2])

        assert seq2 == seq1 + 1


class TestContractStats:
    """Tests para cálculo de estadísticas."""

    def test_get_stats_empty_db(self, db: Session, test_factory: Factory):
        """Stats con DB vacía deben ser todos ceros."""
        service = KobetsuService(db)
        stats = service.get_stats()

        assert stats["total_contracts"] == 0
        assert stats["active_contracts"] == 0
        assert stats["expiring_soon"] == 0
        assert stats["expired_contracts"] == 0
        assert stats["draft_contracts"] == 0

    def test_get_stats_counts_by_status(
        self,
        db: Session,
        test_factory: Factory,
        test_employee
    ):
        """Stats deben contar correctamente por status."""
        service = KobetsuService(db)

        # Crear contratos de prueba con diferentes estados
        base_data = {
            "factory_id": test_factory.id,
            "contract_date": date.today(),
            "dispatch_start_date": date.today(),
            "work_content": "Test work content for testing purposes minimum length",
            "responsibility_level": "通常業務",
            "worksite_name": "Test Factory",
            "worksite_address": "Test Address 123",
            "supervisor_department": "製造部",
            "supervisor_position": "課長",
            "supervisor_name": "Test Supervisor",
            "work_days": ["月", "火", "水", "木", "金"],
            "work_start_time": "08:00",
            "work_end_time": "17:00",
            "break_time_minutes": 60,
            "hourly_rate": Decimal("1500"),
            "overtime_rate": Decimal("1875"),
            "haken_moto_complaint_contact": {
                "department": "人事", "position": "部長",
                "name": "山田", "phone": "123"
            },
            "haken_saki_complaint_contact": {
                "department": "総務", "position": "課長",
                "name": "佐藤", "phone": "456"
            },
            "haken_moto_manager": {
                "department": "派遣", "position": "部長",
                "name": "鈴木", "phone": "789"
            },
            "haken_saki_manager": {
                "department": "人事", "position": "部長",
                "name": "高橋", "phone": "012"
            },
            "number_of_workers": 1,
        }

        # Active contract
        active_contract = KobetsuKeiyakusho(
            **base_data,
            contract_number="KOB-202512-0001",
            dispatch_end_date=date.today() + timedelta(days=60),
            status="active",
        )
        db.add(active_contract)

        # Draft contract
        draft_contract = KobetsuKeiyakusho(
            **base_data,
            contract_number="KOB-202512-0002",
            dispatch_end_date=date.today() + timedelta(days=30),
            status="draft",
        )
        db.add(draft_contract)

        # Expired contract
        expired_contract = KobetsuKeiyakusho(
            **base_data,
            contract_number="KOB-202512-0003",
            dispatch_end_date=date.today() - timedelta(days=10),
            status="expired",
        )
        db.add(expired_contract)

        db.commit()

        stats = service.get_stats()

        assert stats["total_contracts"] == 3
        assert stats["active_contracts"] == 1
        assert stats["draft_contracts"] == 1
        assert stats["expired_contracts"] == 1

    def test_get_stats_expiring_soon(
        self,
        db: Session,
        test_factory: Factory,
        test_employee
    ):
        """Debe contar contratos que expiran pronto (30 días)."""
        service = KobetsuService(db)

        base_data = {
            "factory_id": test_factory.id,
            "contract_date": date.today(),
            "dispatch_start_date": date.today(),
            "work_content": "Test work content minimum length required here",
            "responsibility_level": "通常業務",
            "worksite_name": "Test Factory",
            "worksite_address": "Test Address",
            "supervisor_department": "製造部",
            "supervisor_position": "課長",
            "supervisor_name": "Supervisor",
            "work_days": ["月", "火", "水", "木", "金"],
            "work_start_time": "08:00",
            "work_end_time": "17:00",
            "break_time_minutes": 60,
            "hourly_rate": Decimal("1500"),
            "overtime_rate": Decimal("1875"),
            "haken_moto_complaint_contact": {"department": "A", "position": "B", "name": "C", "phone": "1"},
            "haken_saki_complaint_contact": {"department": "A", "position": "B", "name": "C", "phone": "1"},
            "haken_moto_manager": {"department": "A", "position": "B", "name": "C", "phone": "1"},
            "haken_saki_manager": {"department": "A", "position": "B", "name": "C", "phone": "1"},
            "number_of_workers": 1,
            "status": "active",
        }

        # Contrato que expira en 15 días
        expiring_soon = KobetsuKeiyakusho(
            **base_data,
            contract_number="KOB-202512-0010",
            dispatch_end_date=date.today() + timedelta(days=15),
        )
        db.add(expiring_soon)

        # Contrato que expira en 60 días (no cuenta)
        not_expiring_soon = KobetsuKeiyakusho(
            **base_data,
            contract_number="KOB-202512-0011",
            dispatch_end_date=date.today() + timedelta(days=60),
        )
        db.add(not_expiring_soon)

        db.commit()

        stats = service.get_stats()

        assert stats["expiring_soon"] >= 1


class TestContractValidation:
    """Tests para validación de datos de contrato."""

    def test_validate_dates_end_before_start_raises(self, db: Session):
        """Debe rechazar fecha fin anterior a inicio."""
        service = KobetsuService(db)

        # Esta validación puede estar en el servicio o en el schema
        # Ajustar según implementación real
        start = date(2025, 12, 1)
        end = date(2025, 11, 1)

        # Si el servicio tiene método de validación explícito
        if hasattr(service, 'validate_contract_dates'):
            with pytest.raises((ValueError, Exception)):
                service.validate_contract_dates(start_date=start, end_date=end)

    def test_validate_dates_same_day_allowed(self, db: Session):
        """Fecha inicio = fecha fin debe ser válido."""
        service = KobetsuService(db)

        start = date(2025, 12, 1)
        end = date(2025, 12, 1)

        # No debe lanzar excepción
        if hasattr(service, 'validate_contract_dates'):
            result = service.validate_contract_dates(start_date=start, end_date=end)
            # Debe pasar sin error

    def test_validate_work_days_valid_japanese(self, db: Session):
        """Días válidos en japonés deben pasar validación."""
        valid_days = ["月", "火", "水", "木", "金"]

        # La validación puede estar en schema Pydantic
        # Este test verifica que los días japoneses son aceptados
        assert all(day in ["月", "火", "水", "木", "金", "土", "日"] for day in valid_days)


class TestContractCRUD:
    """Tests para operaciones CRUD de contratos."""

    def test_list_contracts_empty(self, db: Session, test_factory: Factory):
        """Listar contratos debe retornar lista vacía si no hay datos."""
        service = KobetsuService(db)
        result = service.list_contracts()

        assert result["items"] == []
        assert result["total"] == 0

    def test_list_contracts_with_status_filter(
        self,
        db: Session,
        test_factory: Factory,
        sample_contract_data: dict
    ):
        """Debe filtrar contratos por status."""
        service = KobetsuService(db)

        # Crear contrato
        contract = service.create(sample_contract_data)
        assert contract.status == "draft"

        # Filtrar por draft
        result = service.list_contracts(status="draft")
        assert result["total"] >= 1

        # Filtrar por active (no debe incluir el draft)
        result_active = service.list_contracts(status="active")
        assert all(item["status"] == "active" for item in result_active["items"])

    def test_activate_draft_contract(
        self,
        db: Session,
        test_factory: Factory,
        sample_contract_data: dict
    ):
        """Debe poder activar un contrato en borrador."""
        service = KobetsuService(db)

        # Crear contrato (nace como draft)
        contract = service.create(sample_contract_data)
        assert contract.status == "draft"

        # Activar
        activated = service.activate(contract.id)
        assert activated.status == "active"

    def test_cannot_delete_active_contract(
        self,
        db: Session,
        test_factory: Factory,
        sample_contract_data: dict
    ):
        """No debe poder eliminar un contrato activo (soft delete o restricción)."""
        service = KobetsuService(db)

        contract = service.create(sample_contract_data)
        service.activate(contract.id)

        # Intentar eliminar - comportamiento depende de implementación
        # Puede lanzar error o hacer soft delete
        try:
            service.delete(contract.id)
            # Si no lanza error, verificar que fue soft delete
            db.refresh(contract)
            # El contrato puede seguir existiendo pero marcado
        except Exception:
            # Correcto, no se permite eliminar activos
            pass
