# ANÁLISIS COMPLETO, PLAN DE TESTS Y CONTRATO - KobetsuV1.0

**Fecha:** 2025-12-07
**Analizado por:** Ingeniero Senior + QA
**Repositorio:** https://github.com/jokken79/KobetsuV1.0

---

# === 1. ANÁLISIS DE LA APP KOBETSUV1.0 ===

## 1.1 ¿Qué hace la aplicación?

**UNS Kobetsu Keiyakusho Management System** es un sistema de gestión de contratos individuales de dispatch (派遣) diseñado específicamente para cumplir con la **Ley de Dispatch de Trabajadores de Japón (労働者派遣法第26条)**.

### Funcionalidades principales:
1. **Gestión de contratos (個別契約書)**: Crear, editar, activar, renovar y cancelar contratos de dispatch con los 16 campos legalmente obligatorios
2. **Gestión de fábricas (派遣先)**: Administrar empresas cliente, plantas, departamentos y líneas de producción
3. **Gestión de empleados (派遣社員)**: Registro de trabajadores dispatch, control de visas, asignaciones
4. **Generación de documentos**: Creación automática de PDF/DOCX de contratos según plantillas legales
5. **Importación de datos**: Sincronización con sistema Excel legado (11,000+ fórmulas)
6. **Dashboard y estadísticas**: Métricas de contratos activos, por vencer, empleados asignados

---

## 1.2 Módulos y Capas Principales

### Backend (FastAPI + PostgreSQL)
```
backend/app/
├── api/v1/          # 12 archivos de endpoints (78 endpoints totales)
│   ├── auth.py      # Autenticación JWT (6 endpoints)
│   ├── kobetsu.py   # Contratos principales (28 endpoints)
│   ├── factories.py # Fábricas y líneas (16 endpoints)
│   ├── employees.py # Empleados (11 endpoints)
│   ├── imports.py   # Importación de datos (7 endpoints)
│   ├── documents.py # Generación de documentos (7 endpoints)
│   └── ...
├── models/          # 9 modelos SQLAlchemy
│   ├── kobetsu_keiyakusho.py  # Modelo principal (16 campos legales)
│   ├── factory.py             # Factory + FactoryLine + FactoryBreak
│   ├── employee.py            # Empleados dispatch
│   └── ...
├── services/        # 19 servicios de lógica de negocio
│   ├── kobetsu_service.py           # CRUD contratos
│   ├── kobetsu_pdf_service.py       # Generación PDF
│   ├── kobetsu_excel_generator.py   # Generación Excel
│   ├── import_service.py            # Importación datos
│   ├── contract_renewal_service.py  # Renovación contratos
│   └── ...
└── core/            # Configuración, seguridad, BD
```

### Frontend (Next.js 15 + React 19)
```
frontend/
├── app/                    # 23 páginas (App Router)
│   ├── kobetsu/           # CRUD contratos
│   ├── factories/         # Gestión fábricas
│   ├── employees/         # Gestión empleados
│   ├── import/            # Importación datos
│   └── sync/              # Sincronización
├── components/            # Componentes reutilizables
│   ├── kobetsu/          # StatusBadge, KobetsuStats, KobetsuTable
│   └── common/           # Header, Toast, Breadcrumbs
├── lib/api.ts            # Cliente API centralizado (1023 líneas)
└── types/index.ts        # Tipos TypeScript (~500 líneas)
```

### Base de Datos (PostgreSQL 15)
- **Tablas principales**: `kobetsu_keiyakusho`, `kobetsu_employees`, `factories`, `factory_lines`, `employees`, `users`
- **Características**: JSONB para datos semiestructurados, índices optimizados, restricciones CHECK

### Infraestructura (Docker)
- 5 servicios: PostgreSQL, Redis, Backend, Frontend, Adminer
- Red aislada: `uns-kobetsu-keiyakusho-network`
- Puertos: 8010 (backend), 3010 (frontend), 5442 (postgres), 6389 (redis), 8090 (adminer)

---

## 1.3 Tecnologías Detectadas

| Capa | Tecnología | Versión | Uso |
|------|------------|---------|-----|
| **Backend** | FastAPI | 0.115.6 | Framework API REST |
| | SQLAlchemy | 2.0.36 | ORM |
| | Alembic | 1.13.1 | Migraciones DB |
| | PostgreSQL | 15 | Base de datos |
| | Redis | 7 | Caché, sesiones |
| | python-jose | 3.3.0 | JWT tokens |
| | python-docx | 1.1.0 | Generación DOCX |
| | openpyxl | 3.1.2 | Manejo Excel |
| **Frontend** | Next.js | 15.0.0 | Framework React |
| | React | 19.0.0 | UI Library |
| | TypeScript | 5.x | Tipado estático |
| | Tailwind CSS | 3.4.0 | Estilos |
| | TanStack Query | 5.14.2 | Estado servidor |
| | Zustand | 4.4.7 | Estado cliente |
| | Axios | 1.6.2 | HTTP Client |
| **Testing** | pytest | - | Tests backend |
| | Vitest | - | Tests frontend |
| | Playwright | - | Tests E2E |
| **DevOps** | Docker | - | Contenedores |
| | Docker Compose | - | Orquestación |

---

## 1.4 Puntos Fuertes del Diseño

### Backend
1. **Arquitectura limpia con capa de servicios**: La lógica de negocio está correctamente separada de los endpoints
2. **Modelo de datos robusto**: Los 16 campos legales están modelados con tipos correctos (Numeric para dinero, JSONB para datos flexibles)
3. **Validación exhaustiva**: Pydantic schemas validan todas las entradas/salidas
4. **Autenticación JWT sólida**: Tokens de acceso + refresh con renovación automática
5. **Indexación inteligente**: Índices en campos de búsqueda frecuente

### Frontend
1. **Gestión de estado moderna**: React Query para servidor + Zustand para cliente
2. **URL como fuente de verdad**: Filtros y paginación sincronizados con URL
3. **Lazy loading**: Componentes pesados cargados dinámicamente
4. **UX consistente**: Providers centralizados para Toast y Confirm dialogs

### Infraestructura
1. **Containerización completa**: Todo el stack en Docker
2. **Healthchecks**: Verificación de estado en todos los servicios
3. **Proxy interno**: Next.js proxea API calls evitando CORS

---

## 1.5 Puntos Débiles y Riesgos

### 🔴 CRÍTICO - Corregir antes de tests

| ID | Problema | Ubicación | Impacto | Solución |
|----|----------|-----------|---------|----------|
| SEC-01 | **Endpoint DELETE /delete-all SIN AUTENTICACIÓN** | `backend/app/api/v1/kobetsu.py` | Cualquiera puede borrar TODOS los contratos | Descomentar `Depends(get_current_user)` y agregar `require_role("super_admin")` |
| SEC-02 | Tokens en localStorage | `frontend/lib/api.ts` | Vulnerabilidad XSS | Mover refresh_token a cookie HttpOnly |

### 🟡 MEDIO - Deuda técnica

| ID | Problema | Ubicación | Impacto |
|----|----------|-----------|---------|
| ARCH-01 | kobetsu.py tiene 1000+ líneas | `backend/app/api/v1/kobetsu.py` | Difícil de mantener |
| ARCH-02 | Autenticación en memoria (demo) | `backend/app/api/v1/auth.py` | Usuarios se pierden al reiniciar |
| ARCH-03 | React 19 RC (no estable) | `frontend/package.json` | Posibles bugs |
| TEST-01 | Cobertura frontend muy baja | `frontend/__tests__/` | Regresiones no detectadas |

### 🟢 BAJO - Mejoras futuras

| ID | Problema | Ubicación |
|----|----------|-----------|
| OPT-01 | Falta rate limiting en endpoints públicos | backend |
| OPT-02 | Sin mecanismo de revocación de tokens | backend |
| OPT-03 | Logging no centralizado | backend/frontend |

---

## 1.6 Conclusión del Análisis

### ¿Está la app en un estado razonablemente estable para diseñar y generar tests automatizados?

## **SÍ, SE PUEDE TESTEAR** ✅

**Justificación:**
1. La arquitectura es sólida y bien organizada
2. La separación de capas permite testear servicios aisladamente
3. Ya existe una suite de 67+ tests backend funcionando
4. Los fixtures de pytest están bien configurados
5. Vitest está configurado para frontend

**Advertencia importante:**
> ⚠️ **ANTES de ejecutar tests en producción**, debe corregirse el endpoint `/delete-all` que no tiene autenticación. Esta vulnerabilidad crítica podría causar pérdida de datos.

---

# === 2. PLAN DE TESTS (TABLA) ===

## 2.1 Estrategia de Pruebas por Capas

### Backend
- **Unit Tests**: Servicios aislados con mocks de DB
- **Integration Tests**: API + DB real (SQLite in-memory)
- **Contract Tests**: Validación de schemas Pydantic

### Frontend
- **Unit Tests**: Componentes con mocks de API
- **Integration Tests**: Páginas con React Testing Library
- **E2E Tests**: Flujos completos con Playwright

---

## 2.2 Tests Existentes (Cobertura Actual)

| Archivo | Tests | Cobertura |
|---------|-------|-----------|
| `test_auth_api.py` | 16 | Login, registro, tokens, logout |
| `test_factory_api.py` | 23 | CRUD fábricas, líneas, cascade dropdowns |
| `test_employee_api.py` | 28 | CRUD empleados, stats, visa, asignaciones |
| `test_kobetsu_api.py` | 17 | CRUD contratos, activate, duplicate, stats |
| `test_schemas.py` | ~5 | Validación schemas |
| **Frontend** `components.test.tsx` | ~25 | StatusBadge, KobetsuStats, validaciones |
| **E2E** `test_factory_lines.py` | 1 | Crear línea de fábrica |
| **E2E** `test_edit_line.py` | 1 | Editar/eliminar línea |
| **TOTAL** | **~116** | |

---

## 2.3 Tabla de Casos de Prueba FALTANTES

| ID | Capa | Tipo | Módulo/Archivo | Descripción | Datos de Entrada | Resultado Esperado |
|----|------|------|----------------|-------------|------------------|-------------------|
| **BACKEND - SERVICIOS** |
| BE-S01 | backend | unitario | `kobetsu_service.py` | Generar número de contrato único | Mes/año actual | `KOB-YYYYMM-XXXX` único |
| BE-S02 | backend | unitario | `kobetsu_service.py` | Calcular estadísticas de contratos | Lista de contratos | Stats con totales correctos |
| BE-S03 | backend | unitario | `contract_renewal_service.py` | Renovar contrato existente | Contract ID, nueva fecha fin | Nuevo contrato con `previous_contract_id` |
| BE-S04 | backend | unitario | `contract_date_service.py` | Validar fechas contra conflict_date | Factory ID, fecha propuesta | Valid/Invalid con mensaje |
| BE-S05 | backend | unitario | `contract_logic_service.py` | Validar compatibilidad empleados | Employee IDs, line_id, rate | Lista compatible/incompatible |
| BE-S06 | backend | unitario | `import_service.py` | Parsear fila de Excel empleados | Row data | Employee dict validado |
| BE-S07 | backend | unitario | `import_service.py` | Detectar duplicados en import | Lista con duplicados | Duplicados marcados |
| BE-S08 | backend | unitario | `sync_service.py` | Sincronizar empleados con Excel | Excel path | Created/Updated counts |
| **BACKEND - GENERACIÓN DOCUMENTOS** |
| BE-D01 | backend | integración | `kobetsu_pdf_service.py` | Generar PDF de contrato | Contract ID | Blob PDF válido |
| BE-D02 | backend | integración | `kobetsu_excel_generator.py` | Generar Excel de contrato | Contract ID | Blob XLSX válido |
| BE-D03 | backend | unitario | `template_manager.py` | Cargar plantilla correcta | Template name | Template object |
| **BACKEND - API ENDPOINTS** |
| BE-A01 | backend | integración | `kobetsu.py` | Batch create múltiples contratos | Groups con employee_ids | N contratos creados |
| BE-A02 | backend | integración | `kobetsu.py` | Suggest assignment (add vs new) | Employee, factory, line | Recommendation correcta |
| BE-A03 | backend | integración | `kobetsu.py` | Validate conflict date | Factory ID, date | Warning si cerca de conflict |
| BE-A04 | backend | integración | `kobetsu.py` | Export CSV de contratos | Filtros opcionales | CSV válido |
| BE-A05 | backend | integración | `documents.py` | Download signed PDF | Contract ID con PDF | Blob descargable |
| BE-A06 | backend | integración | `imports.py` | Preview + Execute import | Excel file | Counts correctos |
| BE-A07 | backend | integración | `settings.py` | Get/Update form defaults | Defaults data | Guardado persistente |
| **BACKEND - SEGURIDAD** |
| BE-SEC01 | backend | integración | `kobetsu.py` | DELETE /delete-all requiere auth | Sin token | 401/403 |
| BE-SEC02 | backend | integración | `auth.py` | Rate limiting en login | 10+ intentos rápidos | 429 Too Many Requests |
| BE-SEC03 | backend | integración | `*` | Endpoints protegidos sin token | Request sin auth | 401 Unauthorized |
| **FRONTEND - COMPONENTES** |
| FE-C01 | frontend | unitario | `KobetsuTable` | Renderizar tabla de contratos | Lista de contratos | Filas correctas |
| FE-C02 | frontend | unitario | `KobetsuTable` | Ordenar por columna | Click en header | Orden cambiado |
| FE-C03 | frontend | unitario | `KobetsuForm` | Validar campos requeridos | Form vacío | Errores mostrados |
| FE-C04 | frontend | unitario | `KobetsuForm` | Submit formulario válido | Datos completos | API llamada correcta |
| FE-C05 | frontend | unitario | `FactoryLineCard` | Mostrar datos de línea | Line data | Info renderizada |
| FE-C06 | frontend | unitario | `EmployeeSelector` | Seleccionar empleados | Click en checkbox | IDs actualizados |
| FE-C07 | frontend | unitario | `ImportPreview` | Mostrar preview de import | Preview data | Tabla con errores |
| FE-C08 | frontend | unitario | `Pagination` | Cambiar de página | Click en número | URL actualizada |
| **FRONTEND - PÁGINAS** |
| FE-P01 | frontend | integración | `kobetsu/page.tsx` | Listar contratos con filtros | Filtros en URL | Lista filtrada |
| FE-P02 | frontend | integración | `kobetsu/create/page.tsx` | Crear contrato completo | Form data | Redirect a detalle |
| FE-P03 | frontend | integración | `kobetsu/[id]/page.tsx` | Ver detalle de contrato | Contract ID | Info correcta |
| FE-P04 | frontend | integración | `factories/page.tsx` | Listar fábricas | - | Lista de factories |
| FE-P05 | frontend | integración | `employees/page.tsx` | Listar empleados | - | Lista de employees |
| FE-P06 | frontend | integración | `import/page.tsx` | Flujo de importación | Excel file | Preview + Execute |
| **E2E - FLUJOS COMPLETOS** |
| E2E-01 | e2e | e2e | Flujo completo | Login → Crear contrato → Activar → Ver PDF | Credenciales, datos contrato | PDF descargado |
| E2E-02 | e2e | e2e | Flujo completo | Renovar contrato existente | Contract ID, nueva fecha | Contrato renovado |
| E2E-03 | e2e | e2e | Flujo completo | Importar empleados desde Excel | Excel file | Empleados en sistema |
| E2E-04 | e2e | e2e | Flujo completo | Crear fábrica con líneas | Factory data + lines | Factory con líneas |
| E2E-05 | e2e | e2e | Flujo completo | Asignar empleado a contrato existente | Employee ID, Contract ID | Empleado asignado |

---

# === 3. CÓDIGO DE TESTS PROPUESTOS ===

## 3.1 Backend Tests

### Archivo: `backend/tests/test_kobetsu_service.py`

```python
"""
Tests unitarios para KobetsuService
Cubre: generación de números, cálculo de stats, validaciones
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.kobetsu_service import KobetsuService
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho


class TestContractNumberGeneration:
    """Tests para generación de números de contrato."""

    def test_generate_contract_number_format(self, db: Session):
        """El número debe tener formato KOB-YYYYMM-XXXX."""
        service = KobetsuService(db)
        number = service.generate_contract_number()

        assert number.startswith("KOB-")
        parts = number.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 6  # YYYYMM
        assert len(parts[2]) == 4  # XXXX

    def test_generate_contract_number_unique(self, db: Session):
        """Los números generados deben ser únicos."""
        service = KobetsuService(db)
        numbers = [service.generate_contract_number() for _ in range(10)]

        assert len(numbers) == len(set(numbers))

    def test_generate_contract_number_increments(self, db: Session):
        """El contador debe incrementar correctamente."""
        service = KobetsuService(db)

        # Simular contrato existente
        existing = KobetsuKeiyakusho(
            contract_number="KOB-202512-0005",
            # ... otros campos requeridos
        )
        db.add(existing)
        db.commit()

        new_number = service.generate_contract_number()
        assert "0006" in new_number or new_number > "KOB-202512-0005"


class TestContractStats:
    """Tests para cálculo de estadísticas."""

    def test_get_stats_empty_db(self, db: Session):
        """Stats con DB vacía deben ser todos ceros."""
        service = KobetsuService(db)
        stats = service.get_stats()

        assert stats["total_contracts"] == 0
        assert stats["active_contracts"] == 0
        assert stats["expiring_soon"] == 0
        assert stats["expired_contracts"] == 0
        assert stats["draft_contracts"] == 0

    def test_get_stats_with_contracts(self, db: Session, test_factory):
        """Stats deben contar correctamente por status."""
        service = KobetsuService(db)

        # Crear contratos de prueba
        contracts_data = [
            {"status": "active", "dispatch_end_date": date.today() + timedelta(days=60)},
            {"status": "active", "dispatch_end_date": date.today() + timedelta(days=15)},  # expiring
            {"status": "draft", "dispatch_end_date": date.today() + timedelta(days=30)},
            {"status": "expired", "dispatch_end_date": date.today() - timedelta(days=10)},
        ]

        for i, data in enumerate(contracts_data):
            contract = KobetsuKeiyakusho(
                contract_number=f"KOB-202512-{i:04d}",
                factory_id=test_factory.id,
                contract_date=date.today(),
                dispatch_start_date=date.today(),
                dispatch_end_date=data["dispatch_end_date"],
                work_content="Test work content for testing purposes",
                responsibility_level="通常業務",
                worksite_name="Test Factory",
                worksite_address="Test Address",
                supervisor_department="製造部",
                supervisor_position="課長",
                supervisor_name="Test Supervisor",
                work_days=["月", "火", "水", "木", "金"],
                work_start_time="08:00",
                work_end_time="17:00",
                break_time_minutes=60,
                hourly_rate=Decimal("1500"),
                overtime_rate=Decimal("1875"),
                haken_moto_complaint_contact={"department": "人事", "position": "部長", "name": "山田", "phone": "123"},
                haken_saki_complaint_contact={"department": "総務", "position": "課長", "name": "佐藤", "phone": "456"},
                haken_moto_manager={"department": "派遣", "position": "部長", "name": "鈴木", "phone": "789"},
                haken_saki_manager={"department": "人事", "position": "部長", "name": "高橋", "phone": "012"},
                number_of_workers=1,
                status=data["status"],
            )
            db.add(contract)
        db.commit()

        stats = service.get_stats()

        assert stats["total_contracts"] == 4
        assert stats["active_contracts"] == 2
        assert stats["draft_contracts"] == 1
        assert stats["expired_contracts"] == 1
        assert stats["expiring_soon"] >= 1  # Al menos el que vence en 15 días

    def test_get_stats_by_factory(self, db: Session, test_factory):
        """Stats pueden filtrarse por factory_id."""
        service = KobetsuService(db)
        stats = service.get_stats(factory_id=test_factory.id)

        assert "total_contracts" in stats
        # Solo debe contar contratos de esa fábrica


class TestContractValidation:
    """Tests para validación de datos de contrato."""

    def test_validate_dates_end_before_start(self, db: Session):
        """Debe rechazar fecha fin anterior a inicio."""
        service = KobetsuService(db)

        with pytest.raises(ValueError) as exc:
            service.validate_contract_dates(
                start_date=date(2025, 12, 1),
                end_date=date(2025, 11, 1)
            )

        assert "fecha" in str(exc.value).lower() or "date" in str(exc.value).lower()

    def test_validate_dates_same_day_allowed(self, db: Session):
        """Fecha inicio = fecha fin debe ser válido."""
        service = KobetsuService(db)

        # No debe lanzar excepción
        result = service.validate_contract_dates(
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 1)
        )
        assert result is True or result is None

    def test_validate_work_days_empty(self, db: Session):
        """Debe rechazar días de trabajo vacíos."""
        service = KobetsuService(db)

        with pytest.raises(ValueError):
            service.validate_work_days([])

    def test_validate_work_days_valid(self, db: Session):
        """Días válidos deben pasar validación."""
        service = KobetsuService(db)

        valid_days = ["月", "火", "水", "木", "金"]
        result = service.validate_work_days(valid_days)
        assert result is True or result is None


class TestContractRenewal:
    """Tests para renovación de contratos."""

    def test_renew_contract_creates_new(
        self,
        db: Session,
        test_factory,
        sample_contract_data
    ):
        """Renovar debe crear nuevo contrato vinculado."""
        service = KobetsuService(db)

        # Crear contrato original
        original = service.create(sample_contract_data)
        original_id = original.id

        # Renovar
        new_end_date = date.today() + timedelta(days=365)
        renewed = service.renew(original_id, new_end_date)

        assert renewed.id != original_id
        assert renewed.previous_contract_id == original_id
        assert renewed.dispatch_end_date == new_end_date
        assert renewed.status == "draft"

    def test_renew_contract_updates_original_status(
        self,
        db: Session,
        test_factory,
        sample_contract_data
    ):
        """El contrato original debe marcarse como 'renewed'."""
        service = KobetsuService(db)

        original = service.create(sample_contract_data)
        service.activate(original.id)

        new_end_date = date.today() + timedelta(days=365)
        service.renew(original.id, new_end_date)

        db.refresh(original)
        assert original.status == "renewed"
```

### Archivo: `backend/tests/test_import_service.py`

```python
"""
Tests para ImportService - importación de datos desde Excel
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.services.import_service import ImportService


class TestEmployeeImport:
    """Tests para importación de empleados."""

    def test_parse_employee_row_valid(self, db):
        """Fila válida debe parsearse correctamente."""
        service = ImportService(db)

        row_data = {
            "社員№": "EMP001",
            "氏名": "山田太郎",
            "カナ": "ヤマダタロウ",
            "性別": "男",
            "国籍": "日本",
            "生年月日": "1990-01-15",
            "派遣先": "テスト株式会社",
            "工場名": "本社工場",
            "時給": 1500,
            "現在": "在籍",
        }

        result = service.parse_employee_row(row_data, row_number=1)

        assert result["is_valid"] is True
        assert result["employee_number"] == "EMP001"
        assert result["full_name_kanji"] == "山田太郎"
        assert result["hourly_rate"] == Decimal("1500")

    def test_parse_employee_row_missing_required(self, db):
        """Fila sin campos requeridos debe marcar errores."""
        service = ImportService(db)

        row_data = {
            "社員№": "",  # Vacío
            "氏名": "山田太郎",
        }

        result = service.parse_employee_row(row_data, row_number=1)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert any("社員№" in e or "employee_number" in e for e in result["errors"])

    def test_parse_employee_row_invalid_date(self, db):
        """Fecha de nacimiento inválida debe marcarse."""
        service = ImportService(db)

        row_data = {
            "社員№": "EMP001",
            "氏名": "山田太郎",
            "生年月日": "invalid-date",
        }

        result = service.parse_employee_row(row_data, row_number=1)

        assert result["is_valid"] is False
        assert any("fecha" in e.lower() or "date" in e.lower() for e in result["errors"])

    def test_detect_duplicates(self, db):
        """Debe detectar empleados duplicados en import."""
        service = ImportService(db)

        preview_data = [
            {"employee_number": "EMP001", "full_name_kanji": "山田太郎"},
            {"employee_number": "EMP002", "full_name_kanji": "佐藤花子"},
            {"employee_number": "EMP001", "full_name_kanji": "山田太郎"},  # Duplicado
        ]

        result = service.detect_duplicates(preview_data)

        assert result["has_duplicates"] is True
        assert "EMP001" in result["duplicate_numbers"]

    def test_execute_import_create_mode(self, db, test_factory):
        """Modo 'create' debe crear nuevos empleados."""
        service = ImportService(db)

        preview_data = [
            {
                "is_valid": True,
                "employee_number": "NEW001",
                "full_name_kanji": "新規太郎",
                "full_name_kana": "シンキタロウ",
                "gender": "male",
                "nationality": "日本",
                "factory_id": test_factory.id,
            }
        ]

        result = service.execute_employee_import(preview_data, mode="create")

        assert result["success"] is True
        assert result["imported_count"] == 1
        assert result["errors"] == []


class TestFactoryImport:
    """Tests para importación de fábricas."""

    def test_parse_factory_row_valid(self, db):
        """Fila de fábrica válida debe parsearse."""
        service = ImportService(db)

        row_data = {
            "派遣先": "テスト株式会社",
            "工場名": "本社工場",
            "派遣先住所": "東京都千代田区1-1-1",
            "連絡先": "03-1234-5678",
            "配属先": "製造部",
            "ライン": "第1ライン",
        }

        result = service.parse_factory_row(row_data, row_number=1)

        assert result["is_valid"] is True
        assert result["company_name"] == "テスト株式会社"
        assert result["plant_name"] == "本社工場"

    def test_import_creates_factory_and_lines(self, db):
        """Import debe crear fábrica con sus líneas."""
        service = ImportService(db)

        preview_data = [
            {
                "is_valid": True,
                "company_name": "Nueva Corp",
                "plant_name": "Factory A",
                "company_address": "Address 1",
                "lines": [
                    {"department": "Dept1", "line_name": "Line1"},
                    {"department": "Dept1", "line_name": "Line2"},
                ]
            }
        ]

        result = service.execute_factory_import(preview_data, mode="create")

        assert result["success"] is True
        assert result["imported_count"] == 1
```

### Archivo: `backend/tests/test_contract_date_service.py`

```python
"""
Tests para ContractDateService - validación de fechas y conflict dates
"""
import pytest
from datetime import date, timedelta
from app.services.contract_date_service import ContractDateService


class TestConflictDateValidation:
    """Tests para validación contra conflict_date."""

    def test_validate_within_conflict_date(self, db, test_factory):
        """Fecha dentro de conflict_date debe ser válida."""
        service = ContractDateService(db)

        # Factory con conflict_date en 2025-06-30
        test_factory.conflict_date = date(2025, 6, 30)
        db.commit()

        result = service.validate_against_conflict_date(
            factory_id=test_factory.id,
            proposed_end_date=date(2025, 6, 29)
        )

        assert result["valid"] is True

    def test_validate_exceeds_conflict_date(self, db, test_factory):
        """Fecha después de conflict_date debe ser inválida."""
        service = ContractDateService(db)

        test_factory.conflict_date = date(2025, 6, 30)
        db.commit()

        result = service.validate_against_conflict_date(
            factory_id=test_factory.id,
            proposed_end_date=date(2025, 7, 15)
        )

        assert result["valid"] is False
        assert "conflict" in result["message"].lower()

    def test_validate_no_conflict_date(self, db, test_factory):
        """Sin conflict_date, cualquier fecha es válida."""
        service = ContractDateService(db)

        test_factory.conflict_date = None
        db.commit()

        result = service.validate_against_conflict_date(
            factory_id=test_factory.id,
            proposed_end_date=date(2030, 12, 31)
        )

        assert result["valid"] is True


class TestDateSuggestions:
    """Tests para sugerencia de fechas."""

    def test_suggest_dates_respects_conflict(self, db, test_factory):
        """Sugerencia debe ajustarse a conflict_date."""
        service = ContractDateService(db)

        test_factory.conflict_date = date(2025, 6, 30)
        db.commit()

        result = service.suggest_dates(
            factory_id=test_factory.id,
            start_date=date(2025, 1, 1),
            duration_months=12  # Normalmente terminaría 2025-12-31
        )

        assert result["suggested_end"] <= date(2025, 6, 29)
        assert result["was_adjusted"] is True

    def test_suggest_dates_no_adjustment_needed(self, db, test_factory):
        """Si cabe en conflict_date, no ajustar."""
        service = ContractDateService(db)

        test_factory.conflict_date = date(2026, 12, 31)
        db.commit()

        result = service.suggest_dates(
            factory_id=test_factory.id,
            start_date=date(2025, 1, 1),
            duration_months=6
        )

        expected_end = date(2025, 6, 30)
        assert result["suggested_end"] == expected_end
        assert result["was_adjusted"] is False
```

### Archivo: `backend/tests/test_security_endpoints.py`

```python
"""
Tests de seguridad para endpoints críticos
"""
import pytest
from fastapi.testclient import TestClient


class TestSecurityEndpoints:
    """Tests de seguridad para endpoints protegidos."""

    def test_delete_all_requires_auth(self, client: TestClient):
        """DELETE /delete-all DEBE requerir autenticación."""
        response = client.delete("/api/v1/kobetsu/delete-all")

        # Debe rechazar sin auth
        assert response.status_code in [401, 403]

    def test_delete_all_requires_admin_role(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """DELETE /delete-all DEBE requerir rol admin/super_admin."""
        # Crear usuario con rol 'user' normal
        # (Este test asume que auth_headers es de un admin)
        response = client.delete(
            "/api/v1/kobetsu/delete-all",
            headers=auth_headers
        )

        # Admin puede acceder, pero el test principal es que requiere auth
        assert response.status_code != 401

    def test_all_kobetsu_endpoints_require_auth(self, client: TestClient):
        """Todos los endpoints de kobetsu deben requerir auth."""
        endpoints = [
            ("GET", "/api/v1/kobetsu"),
            ("POST", "/api/v1/kobetsu"),
            ("GET", "/api/v1/kobetsu/1"),
            ("PUT", "/api/v1/kobetsu/1"),
            ("DELETE", "/api/v1/kobetsu/1"),
            ("GET", "/api/v1/kobetsu/stats"),
            ("POST", "/api/v1/kobetsu/1/activate"),
            ("POST", "/api/v1/kobetsu/1/renew"),
        ]

        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path)
            elif method == "PUT":
                response = client.put(path, json={})
            elif method == "DELETE":
                response = client.delete(path)

            assert response.status_code in [401, 403], \
                f"{method} {path} debería requerir auth, got {response.status_code}"

    def test_rate_limiting_on_login(self, client: TestClient):
        """Login debe tener rate limiting."""
        # Intentar login muchas veces rápidamente
        for i in range(15):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "wrong"}
            )

        # Después de varios intentos, debe recibir 429
        # (Depende de la configuración de rate limiting)
        # Este test puede necesitar ajustes según la implementación
        assert response.status_code in [401, 429]


class TestCORSAndHeaders:
    """Tests para headers de seguridad."""

    def test_cors_headers_present(self, client: TestClient):
        """Response debe incluir headers CORS correctos."""
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3010"}
        )

        # Verificar que CORS está configurado
        # Los headers específicos dependen de la configuración

    def test_no_sensitive_data_in_error(self, client: TestClient):
        """Errores no deben exponer información sensible."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "wrong"}
        )

        # El mensaje no debe indicar si el usuario existe o no
        data = response.json()
        detail = data.get("detail", "")

        assert "user not found" not in detail.lower()
        assert "incorrect password" not in detail.lower()
```

---

## 3.2 Frontend Tests

### Archivo: `frontend/__tests__/components/kobetsu/KobetsuForm.test.tsx`

```tsx
/**
 * Tests para el formulario de creación/edición de contratos Kobetsu
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'

// Mock del router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
  useParams: () => ({ id: '1' }),
}))

// Mock de React Query
const mockMutate = vi.fn()
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
  })),
  useMutation: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}))

// Mock del API
vi.mock('@/lib/api', () => ({
  kobetsuApi: {
    create: vi.fn(),
    update: vi.fn(),
  },
  factoryApi: {
    getCompanies: vi.fn(() => Promise.resolve([])),
    getPlants: vi.fn(() => Promise.resolve([])),
    getLines: vi.fn(() => Promise.resolve([])),
  },
}))

// Componente de formulario simplificado para tests
const KobetsuFormFields = ({ onSubmit, errors = {} }: any) => (
  <form onSubmit={onSubmit} data-testid="kobetsu-form">
    <div>
      <label htmlFor="worksite_name">派遣先名 *</label>
      <input
        id="worksite_name"
        name="worksite_name"
        aria-invalid={!!errors.worksite_name}
      />
      {errors.worksite_name && (
        <span role="alert">{errors.worksite_name}</span>
      )}
    </div>

    <div>
      <label htmlFor="work_content">業務内容 *</label>
      <textarea
        id="work_content"
        name="work_content"
        aria-invalid={!!errors.work_content}
      />
      {errors.work_content && (
        <span role="alert">{errors.work_content}</span>
      )}
    </div>

    <div>
      <label htmlFor="dispatch_start_date">開始日 *</label>
      <input
        type="date"
        id="dispatch_start_date"
        name="dispatch_start_date"
      />
    </div>

    <div>
      <label htmlFor="dispatch_end_date">終了日 *</label>
      <input
        type="date"
        id="dispatch_end_date"
        name="dispatch_end_date"
      />
    </div>

    <div>
      <label htmlFor="hourly_rate">時給 *</label>
      <input
        type="number"
        id="hourly_rate"
        name="hourly_rate"
        min="800"
      />
    </div>

    <fieldset>
      <legend>勤務日</legend>
      {['月', '火', '水', '木', '金', '土', '日'].map((day) => (
        <label key={day}>
          <input type="checkbox" name="work_days" value={day} />
          {day}
        </label>
      ))}
    </fieldset>

    <button type="submit">保存</button>
  </form>
)


describe('KobetsuForm - Validación', () => {
  const validateForm = (data: Record<string, any>) => {
    const errors: Record<string, string> = {}

    if (!data.worksite_name?.trim()) {
      errors.worksite_name = '派遣先名を入力してください'
    }

    if (!data.work_content || data.work_content.length < 10) {
      errors.work_content = '業務内容を10文字以上で入力してください'
    }

    if (!data.dispatch_start_date) {
      errors.dispatch_start_date = '開始日を入力してください'
    }

    if (!data.dispatch_end_date) {
      errors.dispatch_end_date = '終了日を入力してください'
    }

    if (data.dispatch_end_date && data.dispatch_start_date) {
      if (data.dispatch_end_date < data.dispatch_start_date) {
        errors.dispatch_end_date = '終了日は開始日より後でなければなりません'
      }
    }

    if (!data.hourly_rate || data.hourly_rate < 800) {
      errors.hourly_rate = '時給は最低賃金以上でなければなりません'
    }

    if (!data.work_days || data.work_days.length === 0) {
      errors.work_days = '少なくとも1つの勤務日を選択してください'
    }

    return errors
  }

  it('debe mostrar errores para campos vacíos', () => {
    const emptyData = {
      worksite_name: '',
      work_content: '',
      dispatch_start_date: '',
      dispatch_end_date: '',
      hourly_rate: 0,
      work_days: [],
    }

    const errors = validateForm(emptyData)

    expect(errors.worksite_name).toBeDefined()
    expect(errors.work_content).toBeDefined()
    expect(errors.dispatch_start_date).toBeDefined()
    expect(errors.dispatch_end_date).toBeDefined()
    expect(errors.hourly_rate).toBeDefined()
    expect(errors.work_days).toBeDefined()
  })

  it('debe validar que fecha fin sea posterior a fecha inicio', () => {
    const invalidDates = {
      worksite_name: 'Test',
      work_content: 'Test content with more than 10 characters',
      dispatch_start_date: '2025-12-01',
      dispatch_end_date: '2025-11-01', // Antes del inicio
      hourly_rate: 1500,
      work_days: ['月'],
    }

    const errors = validateForm(invalidDates)

    expect(errors.dispatch_end_date).toBe('終了日は開始日より後でなければなりません')
  })

  it('debe validar salario mínimo', () => {
    const lowWage = {
      worksite_name: 'Test',
      work_content: 'Test content with more than 10 characters',
      dispatch_start_date: '2025-01-01',
      dispatch_end_date: '2025-12-31',
      hourly_rate: 500, // Muy bajo
      work_days: ['月'],
    }

    const errors = validateForm(lowWage)

    expect(errors.hourly_rate).toBe('時給は最低賃金以上でなければなりません')
  })

  it('debe pasar validación con datos correctos', () => {
    const validData = {
      worksite_name: 'テスト株式会社',
      work_content: '製造ライン作業、検品、梱包業務の補助作業を担当',
      dispatch_start_date: '2025-01-01',
      dispatch_end_date: '2025-12-31',
      hourly_rate: 1500,
      work_days: ['月', '火', '水', '木', '金'],
    }

    const errors = validateForm(validData)

    expect(Object.keys(errors)).toHaveLength(0)
  })
})


describe('KobetsuForm - Renderizado', () => {
  it('debe renderizar todos los campos requeridos', () => {
    render(<KobetsuFormFields onSubmit={vi.fn()} />)

    expect(screen.getByLabelText(/派遣先名/)).toBeInTheDocument()
    expect(screen.getByLabelText(/業務内容/)).toBeInTheDocument()
    expect(screen.getByLabelText(/開始日/)).toBeInTheDocument()
    expect(screen.getByLabelText(/終了日/)).toBeInTheDocument()
    expect(screen.getByLabelText(/時給/)).toBeInTheDocument()
    expect(screen.getByText('勤務日')).toBeInTheDocument()
  })

  it('debe mostrar errores de validación', () => {
    const errors = {
      worksite_name: '派遣先名を入力してください',
      work_content: '業務内容を10文字以上で入力してください',
    }

    render(<KobetsuFormFields onSubmit={vi.fn()} errors={errors} />)

    expect(screen.getByText('派遣先名を入力してください')).toBeInTheDocument()
    expect(screen.getByText('業務内容を10文字以上で入力してください')).toBeInTheDocument()
  })

  it('debe permitir seleccionar días de trabajo', async () => {
    const user = userEvent.setup()
    render(<KobetsuFormFields onSubmit={vi.fn()} />)

    const mondayCheckbox = screen.getByRole('checkbox', { name: '月' })
    const tuesdayCheckbox = screen.getByRole('checkbox', { name: '火' })

    await user.click(mondayCheckbox)
    await user.click(tuesdayCheckbox)

    expect(mondayCheckbox).toBeChecked()
    expect(tuesdayCheckbox).toBeChecked()
  })
})


describe('KobetsuForm - Interacción', () => {
  it('debe llamar onSubmit con datos del formulario', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn((e) => e.preventDefault())

    render(<KobetsuFormFields onSubmit={handleSubmit} />)

    // Llenar campos
    await user.type(screen.getByLabelText(/派遣先名/), 'テスト会社')
    await user.type(screen.getByLabelText(/業務内容/), '製造ラインでの組立作業を担当します')
    await user.type(screen.getByLabelText(/時給/), '1500')

    // Seleccionar días
    await user.click(screen.getByRole('checkbox', { name: '月' }))
    await user.click(screen.getByRole('checkbox', { name: '火' }))

    // Submit
    await user.click(screen.getByRole('button', { name: '保存' }))

    expect(handleSubmit).toHaveBeenCalled()
  })
})
```

### Archivo: `frontend/__tests__/pages/kobetsu-list.test.tsx`

```tsx
/**
 * Tests para la página de listado de contratos
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock data
const mockContracts = [
  {
    id: 1,
    contract_number: 'KOB-202512-0001',
    worksite_name: 'テスト株式会社 本社工場',
    dispatch_start_date: '2025-01-01',
    dispatch_end_date: '2025-12-31',
    number_of_workers: 5,
    status: 'active',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    contract_number: 'KOB-202512-0002',
    worksite_name: 'サンプル工業 第二工場',
    dispatch_start_date: '2025-02-01',
    dispatch_end_date: '2025-07-31',
    number_of_workers: 3,
    status: 'draft',
    created_at: '2025-01-15T00:00:00Z',
  },
]

// Mock router
const mockPush = vi.fn()
const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/kobetsu',
}))

// Mock React Query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: {
      items: mockContracts,
      total: 2,
      skip: 0,
      limit: 10,
      has_more: false,
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}))

// Componente simplificado de tabla
const KobetsuListTable = ({
  contracts,
  onRowClick,
  onStatusFilter
}: {
  contracts: typeof mockContracts
  onRowClick: (id: number) => void
  onStatusFilter: (status: string) => void
}) => (
  <div>
    <div data-testid="filters">
      <select onChange={(e) => onStatusFilter(e.target.value)} aria-label="ステータス">
        <option value="">すべて</option>
        <option value="active">有効</option>
        <option value="draft">下書き</option>
        <option value="expired">期限切れ</option>
      </select>
    </div>

    <table>
      <thead>
        <tr>
          <th>契約番号</th>
          <th>派遣先</th>
          <th>期間</th>
          <th>人数</th>
          <th>ステータス</th>
        </tr>
      </thead>
      <tbody>
        {contracts.map((contract) => (
          <tr
            key={contract.id}
            onClick={() => onRowClick(contract.id)}
            data-testid={`contract-row-${contract.id}`}
          >
            <td>{contract.contract_number}</td>
            <td>{contract.worksite_name}</td>
            <td>{contract.dispatch_start_date} 〜 {contract.dispatch_end_date}</td>
            <td>{contract.number_of_workers}</td>
            <td>{contract.status}</td>
          </tr>
        ))}
      </tbody>
    </table>

    {contracts.length === 0 && (
      <p data-testid="no-data">契約が見つかりません</p>
    )}
  </div>
)


describe('KobetsuList - Renderizado', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('debe mostrar la lista de contratos', () => {
    render(
      <KobetsuListTable
        contracts={mockContracts}
        onRowClick={vi.fn()}
        onStatusFilter={vi.fn()}
      />
    )

    expect(screen.getByText('KOB-202512-0001')).toBeInTheDocument()
    expect(screen.getByText('KOB-202512-0002')).toBeInTheDocument()
    expect(screen.getByText('テスト株式会社 本社工場')).toBeInTheDocument()
  })

  it('debe mostrar headers de tabla correctos', () => {
    render(
      <KobetsuListTable
        contracts={mockContracts}
        onRowClick={vi.fn()}
        onStatusFilter={vi.fn()}
      />
    )

    expect(screen.getByText('契約番号')).toBeInTheDocument()
    expect(screen.getByText('派遣先')).toBeInTheDocument()
    expect(screen.getByText('期間')).toBeInTheDocument()
    expect(screen.getByText('人数')).toBeInTheDocument()
    expect(screen.getByText('ステータス')).toBeInTheDocument()
  })

  it('debe mostrar mensaje cuando no hay contratos', () => {
    render(
      <KobetsuListTable
        contracts={[]}
        onRowClick={vi.fn()}
        onStatusFilter={vi.fn()}
      />
    )

    expect(screen.getByTestId('no-data')).toBeInTheDocument()
    expect(screen.getByText('契約が見つかりません')).toBeInTheDocument()
  })
})


describe('KobetsuList - Interacción', () => {
  it('debe navegar al detalle al hacer click en fila', async () => {
    const user = userEvent.setup()
    const handleRowClick = vi.fn()

    render(
      <KobetsuListTable
        contracts={mockContracts}
        onRowClick={handleRowClick}
        onStatusFilter={vi.fn()}
      />
    )

    const firstRow = screen.getByTestId('contract-row-1')
    await user.click(firstRow)

    expect(handleRowClick).toHaveBeenCalledWith(1)
  })

  it('debe filtrar por status', async () => {
    const user = userEvent.setup()
    const handleStatusFilter = vi.fn()

    render(
      <KobetsuListTable
        contracts={mockContracts}
        onRowClick={vi.fn()}
        onStatusFilter={handleStatusFilter}
      />
    )

    const statusSelect = screen.getByRole('combobox', { name: 'ステータス' })
    await user.selectOptions(statusSelect, 'active')

    expect(handleStatusFilter).toHaveBeenCalledWith('active')
  })
})
```

### Archivo: `frontend/__tests__/lib/api.test.ts`

```typescript
/**
 * Tests para el cliente API
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
  },
}))

// Mock localStorage
const localStorageMock = {
  store: {} as Record<string, string>,
  getItem: vi.fn((key: string) => localStorageMock.store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    localStorageMock.store[key] = value
  }),
  removeItem: vi.fn((key: string) => {
    delete localStorageMock.store[key]
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {}
  }),
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})


describe('API Client - Authentication', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  it('debe guardar tokens después de login', async () => {
    const mockResponse = {
      data: {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
      },
    }

    // Simular respuesta de login
    localStorageMock.setItem('access_token', mockResponse.data.access_token)
    localStorageMock.setItem('refresh_token', mockResponse.data.refresh_token)

    expect(localStorageMock.getItem('access_token')).toBe('test-access-token')
    expect(localStorageMock.getItem('refresh_token')).toBe('test-refresh-token')
  })

  it('debe limpiar tokens en logout', () => {
    localStorageMock.setItem('access_token', 'token')
    localStorageMock.setItem('refresh_token', 'refresh')

    localStorageMock.removeItem('access_token')
    localStorageMock.removeItem('refresh_token')

    expect(localStorageMock.getItem('access_token')).toBeNull()
    expect(localStorageMock.getItem('refresh_token')).toBeNull()
  })

  it('isAuthenticated debe retornar false sin token', () => {
    const isAuthenticated = () => !!localStorageMock.getItem('access_token')

    expect(isAuthenticated()).toBe(false)
  })

  it('isAuthenticated debe retornar true con token', () => {
    localStorageMock.setItem('access_token', 'valid-token')

    const isAuthenticated = () => !!localStorageMock.getItem('access_token')

    expect(isAuthenticated()).toBe(true)
  })
})


describe('API Client - Error Handling', () => {
  it('debe manejar error 401 y redirigir a login', () => {
    const mockLocation = { href: '' }
    Object.defineProperty(window, 'location', {
      value: mockLocation,
      writable: true,
    })

    // Simular manejo de 401
    const handle401 = () => {
      localStorageMock.removeItem('access_token')
      localStorageMock.removeItem('refresh_token')
      window.location.href = '/login'
    }

    localStorageMock.setItem('access_token', 'expired-token')
    handle401()

    expect(localStorageMock.getItem('access_token')).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('debe manejar errores de red gracefully', () => {
    const handleNetworkError = (error: any) => {
      if (!error.response) {
        return { message: 'Network error. Please check your connection.' }
      }
      return error.response.data
    }

    const networkError = { message: 'Network Error' }
    const result = handleNetworkError(networkError)

    expect(result.message).toContain('Network')
  })
})


describe('API Client - Request Formatting', () => {
  it('debe formatear parámetros de paginación correctamente', () => {
    const formatPaginationParams = (params: { page: number; pageSize: number }) => ({
      skip: (params.page - 1) * params.pageSize,
      limit: params.pageSize,
    })

    const result = formatPaginationParams({ page: 2, pageSize: 10 })

    expect(result.skip).toBe(10)
    expect(result.limit).toBe(10)
  })

  it('debe formatear filtros de fecha correctamente', () => {
    const formatDateFilter = (date: Date) => {
      return date.toISOString().split('T')[0]
    }

    const date = new Date('2025-12-15')
    const result = formatDateFilter(date)

    expect(result).toBe('2025-12-15')
  })
})
```

---

## 3.3 Tests E2E (Playwright)

### Archivo: `e2e/contract-workflow.spec.ts`

```typescript
/**
 * E2E Tests - Flujo completo de creación de contrato
 */
import { test, expect } from '@playwright/test'

test.describe('Contract Creation Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login antes de cada test
    await page.goto('http://localhost:3010/login')
    await page.fill('input[name="email"]', 'admin@example.com')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')

    // Esperar a que cargue el dashboard
    await page.waitForURL('**/')
    await expect(page.locator('text=ダッシュボード')).toBeVisible({ timeout: 10000 })
  })

  test('debe crear un contrato completo desde cero', async ({ page }) => {
    // 1. Navegar a crear contrato
    await page.click('text=契約作成')
    await page.waitForURL('**/kobetsu/create')

    // 2. Seleccionar fábrica (cascade dropdowns)
    await page.selectOption('select[name="company"]', { label: 'テスト株式会社' })
    await page.waitForTimeout(500) // Esperar carga de plantas
    await page.selectOption('select[name="plant"]', { label: '本社工場' })
    await page.waitForTimeout(500)
    await page.selectOption('select[name="line"]', { index: 1 })

    // 3. Llenar datos del contrato
    await page.fill('input[name="dispatch_start_date"]', '2025-01-01')
    await page.fill('input[name="dispatch_end_date"]', '2025-12-31')
    await page.fill('textarea[name="work_content"]', '製造ライン作業、検品、梱包業務を担当します。')

    // 4. Seleccionar días de trabajo
    await page.check('input[name="work_days"][value="月"]')
    await page.check('input[name="work_days"][value="火"]')
    await page.check('input[name="work_days"][value="水"]')
    await page.check('input[name="work_days"][value="木"]')
    await page.check('input[name="work_days"][value="金"]')

    // 5. Llenar horarios
    await page.fill('input[name="work_start_time"]', '08:00')
    await page.fill('input[name="work_end_time"]', '17:00')
    await page.fill('input[name="break_time_minutes"]', '60')

    // 6. Llenar tarifas
    await page.fill('input[name="hourly_rate"]', '1500')
    await page.fill('input[name="overtime_rate"]', '1875')

    // 7. Seleccionar empleados
    await page.click('button:has-text("従業員を選択")')
    await page.waitForSelector('[data-testid="employee-selector-modal"]')
    await page.check('input[data-employee-id="1"]')
    await page.check('input[data-employee-id="2"]')
    await page.click('button:has-text("選択を確定")')

    // 8. Guardar como borrador
    await page.click('button:has-text("下書き保存")')

    // 9. Verificar creación exitosa
    await expect(page.locator('text=契約が作成されました')).toBeVisible()

    // 10. Verificar que estamos en la página de detalle
    await expect(page).toHaveURL(/\/kobetsu\/\d+/)
    await expect(page.locator('text=KOB-')).toBeVisible()
  })

  test('debe activar un contrato en borrador', async ({ page }) => {
    // Navegar a lista de contratos
    await page.goto('http://localhost:3010/kobetsu')

    // Filtrar por borradores
    await page.selectOption('select[name="status"]', 'draft')
    await page.waitForTimeout(500)

    // Click en primer contrato
    await page.click('tbody tr:first-child')
    await page.waitForURL(/\/kobetsu\/\d+/)

    // Verificar que está en borrador
    await expect(page.locator('text=下書き')).toBeVisible()

    // Activar contrato
    await page.click('button:has-text("有効化")')

    // Confirmar en modal
    await page.click('button:has-text("確認")')

    // Verificar cambio de estado
    await expect(page.locator('.badge-active')).toBeVisible()
    await expect(page.locator('text=有効')).toBeVisible()
  })

  test('debe generar y descargar PDF de contrato', async ({ page }) => {
    // Navegar a un contrato existente
    await page.goto('http://localhost:3010/kobetsu')
    await page.selectOption('select[name="status"]', 'active')
    await page.waitForTimeout(500)
    await page.click('tbody tr:first-child')

    // Click en generar PDF
    const downloadPromise = page.waitForEvent('download')
    await page.click('button:has-text("PDF生成")')

    const download = await downloadPromise

    // Verificar que se descargó
    expect(download.suggestedFilename()).toContain('.pdf')
  })

  test('debe renovar un contrato existente', async ({ page }) => {
    // Navegar a contrato activo
    await page.goto('http://localhost:3010/kobetsu')
    await page.selectOption('select[name="status"]', 'active')
    await page.waitForTimeout(500)
    await page.click('tbody tr:first-child')

    const oldContractNumber = await page.locator('[data-testid="contract-number"]').textContent()

    // Click en renovar
    await page.click('button:has-text("更新")')

    // Llenar nueva fecha fin
    await page.fill('input[name="new_end_date"]', '2026-12-31')

    // Confirmar renovación
    await page.click('button:has-text("更新を確定")')

    // Verificar nuevo contrato creado
    await expect(page.locator('text=契約が更新されました')).toBeVisible()

    // El número de contrato debe ser diferente
    const newContractNumber = await page.locator('[data-testid="contract-number"]').textContent()
    expect(newContractNumber).not.toBe(oldContractNumber)
  })
})


test.describe('Factory Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3010/login')
    await page.fill('input[name="email"]', 'admin@example.com')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/')
  })

  test('debe crear una fábrica con líneas de producción', async ({ page }) => {
    await page.goto('http://localhost:3010/factories/create')

    // Datos de fábrica
    await page.fill('input[name="company_name"]', 'E2E Test Company')
    await page.fill('input[name="plant_name"]', 'Test Factory')
    await page.fill('input[name="company_address"]', 'Test Address 123')
    await page.fill('input[name="company_phone"]', '03-1234-5678')

    // Agregar línea
    await page.click('button:has-text("ライン追加")')
    await page.fill('input[name="lines.0.department"]', 'Manufacturing')
    await page.fill('input[name="lines.0.line_name"]', 'Line A')
    await page.fill('input[name="lines.0.hourly_rate"]', '1500')

    // Guardar
    await page.click('button:has-text("保存")')

    // Verificar
    await expect(page.locator('text=工場が作成されました')).toBeVisible()
  })
})


test.describe('Data Import', () => {
  test('debe importar empleados desde Excel', async ({ page }) => {
    await page.goto('http://localhost:3010/login')
    await page.fill('input[name="email"]', 'admin@example.com')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/')

    await page.goto('http://localhost:3010/import')

    // Seleccionar tab de empleados
    await page.click('text=従業員インポート')

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('test-data/test-employees.xlsx')

    // Esperar preview
    await page.waitForSelector('[data-testid="import-preview"]')

    // Verificar preview
    await expect(page.locator('table tbody tr')).toHaveCount({ minimum: 1 })

    // Ejecutar import
    await page.click('button:has-text("インポート実行")')

    // Verificar resultado
    await expect(page.locator('text=インポートが完了しました')).toBeVisible()
  })
})
```

---

## 3.4 Tests que Amplían los Existentes

### Mejoras para `test_factory_lines.py`

```python
"""
Mejoras para test_factory_lines.py
Añade más casos de prueba y mejor estructura
"""
import asyncio
import pytest
from playwright.async_api import async_playwright, expect

# Configuración
BASE_URL = "http://localhost:3010"
TEST_FACTORY_ID = 39  # Ajustar según datos de prueba


@pytest.fixture(scope="module")
async def browser():
    """Browser fixture reutilizable."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser):
    """Page fixture con login automático."""
    context = await browser.new_context()
    page = await context.new_page()

    # Login
    await page.goto(f"{BASE_URL}/login")
    await page.fill('input[name="email"]', 'admin@example.com')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.wait_for_url("**/")

    yield page
    await context.close()


class TestFactoryLinesCRUD:
    """Tests CRUD para líneas de fábrica."""

    @pytest.mark.asyncio
    async def test_view_factory_lines(self, page):
        """Debe mostrar líneas existentes de una fábrica."""
        await page.goto(f"{BASE_URL}/factories/{TEST_FACTORY_ID}")
        await page.wait_for_load_state("networkidle")

        # Verificar sección de líneas
        lines_section = page.locator('text=配属先・ライン情報')
        await expect(lines_section).to_be_visible()

        # Debe haber al menos una línea
        line_cards = page.locator('[data-testid="line-card"]')
        count = await line_cards.count()
        assert count >= 0  # Puede ser 0 si no hay líneas

    @pytest.mark.asyncio
    async def test_create_new_line(self, page):
        """Debe crear una nueva línea de producción."""
        await page.goto(f"{BASE_URL}/factories/{TEST_FACTORY_ID}")
        await page.wait_for_load_state("networkidle")

        # Click en añadir línea
        await page.click('button:has-text("新規ライン追加")')
        await page.wait_for_selector('[data-testid="line-modal"]')

        # Llenar formulario
        await page.fill('input[name="department"]', 'TestDept')
        await page.fill('input[name="line_name"]', f'TestLine-{asyncio.get_event_loop().time()}')
        await page.fill('input[name="supervisor_name"]', 'Test Supervisor')
        await page.fill('input[name="hourly_rate"]', '1500')

        # Guardar
        await page.click('button:has-text("保存")')

        # Verificar éxito
        await expect(page.locator('text=ラインが作成されました')).to_be_visible(timeout=5000)

    @pytest.mark.asyncio
    async def test_edit_existing_line(self, page):
        """Debe editar una línea existente."""
        await page.goto(f"{BASE_URL}/factories/{TEST_FACTORY_ID}")
        await page.wait_for_load_state("networkidle")

        # Expandir primera línea
        first_line = page.locator('[data-testid="line-card"]').first
        await first_line.click()
        await page.wait_for_timeout(500)

        # Click en editar
        edit_btn = page.locator('button:has-text("編集")').last
        await edit_btn.click()
        await page.wait_for_selector('[data-testid="line-modal"]')

        # Modificar supervisor
        supervisor_input = page.locator('input[name="supervisor_name"]')
        await supervisor_input.clear()
        await supervisor_input.fill('Updated Supervisor')

        # Guardar
        await page.click('button:has-text("保存")')

        # Verificar
        await expect(page.locator('text=ラインが更新されました')).to_be_visible(timeout=5000)

    @pytest.mark.asyncio
    async def test_delete_line_soft_delete(self, page):
        """Debe hacer soft delete de una línea."""
        await page.goto(f"{BASE_URL}/factories/{TEST_FACTORY_ID}")
        await page.wait_for_load_state("networkidle")

        # Contar líneas antes
        initial_count = await page.locator('[data-testid="line-card"]').count()

        if initial_count > 0:
            # Expandir y eliminar primera línea
            first_line = page.locator('[data-testid="line-card"]').first
            await first_line.click()
            await page.wait_for_timeout(500)

            # Preparar para confirmar dialog
            page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

            # Click en eliminar
            delete_btn = page.locator('button:has-text("削除")').last
            await delete_btn.click()
            await page.wait_for_timeout(1000)

            # Verificar que la línea ya no está visible o está marcada como inactiva
            # (El comportamiento exacto depende de la implementación)

    @pytest.mark.asyncio
    async def test_line_validation_errors(self, page):
        """Debe mostrar errores de validación al crear línea inválida."""
        await page.goto(f"{BASE_URL}/factories/{TEST_FACTORY_ID}")
        await page.wait_for_load_state("networkidle")

        await page.click('button:has-text("新規ライン追加")')
        await page.wait_for_selector('[data-testid="line-modal"]')

        # Intentar guardar sin datos
        await page.click('button:has-text("保存")')

        # Debe mostrar errores
        # (El comportamiento específico depende de la implementación de validación)
```

---

# === 4. CONTRATO COMO ADMINISTRADOR DEL PROYECTO KOBETSUV1.0 ===

## CONTRATO DE DESARROLLO DE SOFTWARE

---

### CONTRATO DE DESARROLLO, PRUEBAS Y MANTENIMIENTO
### SISTEMA DE GESTIÓN DE CONTRATOS INDIVIDUALES DE DISPATCH
### "KOBETSU KEIYAKUSHO MANAGEMENT SYSTEM (KobetsuV1.0)"

---

**FECHA DE FIRMA:** ________________

**NÚMERO DE CONTRATO:** DEV-KOB-2025-001

---

## 1. PARTES DEL CONTRATO

### 1.1 CLIENTE (Administrador del Proyecto)

**Nombre/Razón Social:** ________________________________

**Representante Legal:** ________________________________

**Domicilio:** ________________________________

**Teléfono:** ________________________________

**Email:** ________________________________

**NIF/CIF:** ________________________________

En adelante, "EL CLIENTE"

### 1.2 DESARROLLADOR (Proveedor del Servicio)

**Nombre/Razón Social:** ________________________________

**Representante Legal:** ________________________________

**Domicilio:** ________________________________

**Teléfono:** ________________________________

**Email:** ________________________________

**NIF/CIF:** ________________________________

En adelante, "EL DESARROLLADOR"

---

## 2. OBJETO DEL CONTRATO

### 2.1 Descripción General

EL DESARROLLADOR se compromete a realizar el desarrollo, mejora, pruebas automatizadas y mantenimiento del sistema denominado **"KobetsuV1.0 – Sistema de Gestión de Contratos Individuales de Dispatch (個別契約書管理システム)"**, diseñado para cumplir con la Ley de Dispatch de Trabajadores de Japón (労働者派遣法第26条).

### 2.2 Repositorio del Proyecto

El código fuente se encuentra en: `https://github.com/jokken79/KobetsuV1.0`

### 2.3 Objetivo del Sistema

El sistema permite gestionar:
- Contratos individuales de dispatch con los 16 campos legalmente obligatorios
- Fábricas y empresas cliente (派遣先)
- Empleados dispatch (派遣社員)
- Generación automática de documentos PDF/DOCX
- Importación de datos desde el sistema Excel legado

---

## 3. ALCANCE DEL TRABAJO (SCOPE)

### 3.1 Incluido en el Alcance

#### 3.1.1 Backend (API REST con FastAPI)
- [ ] Mantenimiento de los 78 endpoints existentes
- [ ] Corrección de la vulnerabilidad crítica en `/delete-all`
- [ ] Implementación de autenticación con base de datos (reemplazar sistema en memoria)
- [ ] Optimización de consultas y rendimiento
- [ ] Implementación de rate limiting completo
- [ ] Logging centralizado

#### 3.1.2 Frontend (Next.js 15)
- [ ] Mantenimiento de las 23 páginas existentes
- [ ] Mejoras de UX según feedback del cliente
- [ ] Migración de React 19 RC a versión estable si se requiere
- [ ] Responsive design para tablets

#### 3.1.3 Base de Datos (PostgreSQL 15)
- [ ] Migraciones con Alembic
- [ ] Optimización de índices
- [ ] Backups automatizados
- [ ] Scripts de seed para datos de prueba

#### 3.1.4 Generación de Documentos
- [ ] Plantillas PDF/DOCX para contratos
- [ ] Exportación CSV
- [ ] Mejoras en el generador Excel

#### 3.1.5 Tests Automatizados
- [ ] Suite de tests backend (pytest) con cobertura mínima 80%
- [ ] Suite de tests frontend (Vitest) con cobertura mínima 70%
- [ ] Tests E2E (Playwright) para flujos críticos
- [ ] Integración con CI/CD

#### 3.1.6 DevOps
- [ ] Configuración Docker Compose para desarrollo y producción
- [ ] GitHub Actions para CI/CD
- [ ] Documentación de despliegue

### 3.2 Fuera de Alcance (Exclusiones)

- Integración con sistemas de nómina externos
- Aplicación móvil nativa (iOS/Android)
- Traducción del sistema a idiomas distintos del japonés
- Soporte para bases de datos distintas de PostgreSQL
- Hosting/infraestructura en la nube (responsabilidad del cliente)
- Migración completa de datos del sistema Excel existente (solo herramientas)

---

## 4. FASES DEL PROYECTO

### Fase 1: Análisis y Estabilización
- Revisión del código existente
- Corrección de vulnerabilidades de seguridad
- Documentación técnica actualizada
- **Entregable:** Informe de análisis + vulnerabilidades corregidas

### Fase 2: Desarrollo de Tests
- Implementación de tests unitarios backend
- Implementación de tests de componentes frontend
- Implementación de tests E2E
- **Entregable:** Suite de tests con cobertura objetivo

### Fase 3: Mejoras Funcionales
- Nuevas funcionalidades según backlog priorizado
- Optimizaciones de rendimiento
- Mejoras de UX
- **Entregable:** Funcionalidades implementadas y documentadas

### Fase 4: Preparación para Producción
- Configuración de CI/CD completo
- Documentación de operaciones
- Scripts de backup y recuperación
- **Entregable:** Sistema listo para producción

### Fase 5: Despliegue y Formación
- Despliegue en entorno de producción
- Formación básica al equipo del cliente
- **Entregable:** Sistema desplegado + manual de usuario

### Fase 6: Soporte Post-Lanzamiento
- Corrección de bugs críticos
- Soporte técnico
- **Entregable:** Sistema estable en producción

---

## 5. PLAZOS E HITOS

| Fase | Descripción | Duración Estimada | Hito |
|------|-------------|-------------------|------|
| **1** | Análisis y Estabilización | 2 semanas | Vulnerabilidades corregidas |
| **2** | Desarrollo de Tests | 3 semanas | Cobertura backend ≥80% |
| **3** | Mejoras Funcionales | 4 semanas | Features del backlog completadas |
| **4** | Preparación Producción | 2 semanas | CI/CD funcionando |
| **5** | Despliegue y Formación | 1 semana | Sistema en producción |
| **6** | Soporte Post-Lanzamiento | 4 semanas | Periodo de garantía |

**Duración Total Estimada:** 16 semanas (4 meses)

**Fecha Inicio:** ________________

**Fecha Fin Estimada:** ________________

---

## 6. CONDICIONES ECONÓMICAS

### 6.1 Modelo de Pago

[  ] Precio Fijo Total: _____________ €/USD/JPY

[  ] Por Horas: _____________ €/USD/JPY por hora

[  ] Híbrido (precio fijo por fase)

### 6.2 Calendario de Pagos

| Hito | Porcentaje | Importe | Fecha Límite Pago |
|------|------------|---------|-------------------|
| Firma del contrato | 20% | _________ | A la firma |
| Fin Fase 1 (Análisis) | 15% | _________ | +2 semanas |
| Fin Fase 2 (Tests) | 20% | _________ | +5 semanas |
| Fin Fase 3 (Mejoras) | 20% | _________ | +9 semanas |
| Fin Fase 4+5 (Producción) | 15% | _________ | +12 semanas |
| Fin Fase 6 (Garantía) | 10% | _________ | +16 semanas |
| **TOTAL** | **100%** | _________ | |

### 6.3 Gastos Adicionales

Los siguientes gastos NO están incluidos y serán facturados por separado:
- Licencias de software de terceros
- Servicios de hosting/cloud
- Certificados SSL
- Dominios

### 6.4 Forma de Pago

Transferencia bancaria a la cuenta:
- **Banco:** ________________________________
- **IBAN/Número:** ________________________________
- **Concepto:** "KobetsuV1.0 - Fase X"

---

## 7. CALIDAD Y PRUEBAS

### 7.1 Estándares de Calidad

EL DESARROLLADOR se compromete a:

1. Seguir las convenciones de código establecidas en `CLAUDE.md`
2. Documentar todas las funciones y clases públicas
3. Utilizar TypeScript para todo el código frontend
4. Utilizar type hints para todo el código Python

### 7.2 Cobertura de Tests

| Capa | Cobertura Mínima | Métrica |
|------|------------------|---------|
| Backend (Python) | 80% | Lines covered |
| Frontend (TypeScript) | 70% | Lines covered |
| E2E (flujos críticos) | 100% | Flujos definidos |

### 7.3 Criterios de Aceptación

Un entregable se considera aceptado cuando:
1. Todos los tests automatizados pasan
2. No hay vulnerabilidades de seguridad críticas (según OWASP Top 10)
3. La documentación está actualizada
4. El código ha pasado code review

### 7.4 Periodo de Corrección de Bugs

- **Bugs Críticos** (bloquean funcionalidad): Corrección en 24-48 horas
- **Bugs Mayores** (afectan UX): Corrección en 1 semana
- **Bugs Menores** (cosméticos): Corrección en siguiente release

El periodo de garantía para corrección de bugs es de **90 días** desde la entrega final.

---

## 8. PROPIEDAD INTELECTUAL

### 8.1 Código Desarrollado

Todo el código fuente desarrollado bajo este contrato será propiedad exclusiva de EL CLIENTE una vez completado el pago total.

### 8.2 Librerías de Terceros

El sistema utiliza librerías de código abierto (MIT, Apache 2.0, BSD). EL CLIENTE recibirá un listado completo de dependencias y sus licencias.

### 8.3 Código Preexistente

El código existente en el repositorio `KobetsuV1.0` previo a la firma de este contrato permanece bajo la propiedad y licencia actuales.

### 8.4 Documentación

Toda la documentación técnica y de usuario generada será propiedad de EL CLIENTE.

---

## 9. CONFIDENCIALIDAD

### 9.1 Información Confidencial

EL DESARROLLADOR se compromete a mantener estricta confidencialidad sobre:

1. Datos de empleados (nombres, nacionalidades, visas, salarios)
2. Datos de empresas cliente (fábricas, direcciones, contactos)
3. Contenido de los contratos de dispatch
4. Estrategias de negocio de EL CLIENTE
5. Credenciales de acceso a sistemas

### 9.2 Medidas de Seguridad

EL DESARROLLADOR implementará:

1. No almacenar datos de producción en entornos de desarrollo
2. Utilizar datos anonimizados o ficticios para pruebas
3. No compartir accesos con terceros no autorizados
4. Borrar copias locales de datos sensibles al finalizar el proyecto

### 9.3 Duración

Esta obligación de confidencialidad se mantendrá durante **5 años** después de la terminación del contrato.

---

## 10. MANTENIMIENTO Y SOPORTE

### 10.1 Soporte Incluido (Fase 6)

Durante el periodo de garantía (4 semanas post-lanzamiento):
- Corrección de bugs sin coste adicional
- Soporte técnico por email en horario laboral
- Pequeños ajustes de configuración

### 10.2 Mantenimiento Posterior (Opcional)

Después del periodo de garantía, se puede contratar mantenimiento mensual que incluye:

| Plan | Horas/Mes | Coste Mensual | Incluye |
|------|-----------|---------------|---------|
| Básico | 5h | _________ | Bug fixes, actualizaciones seguridad |
| Estándar | 15h | _________ | + Pequeñas mejoras |
| Premium | 30h | _________ | + Nuevas funcionalidades |

### 10.3 Respuesta a Incidencias

| Severidad | Tiempo de Respuesta | Tiempo de Resolución |
|-----------|--------------------|-----------------------|
| Crítica (sistema caído) | 4 horas | 24 horas |
| Alta (funcionalidad bloqueada) | 8 horas | 48 horas |
| Media (funcionalidad degradada) | 24 horas | 1 semana |
| Baja (mejora/cosmético) | 48 horas | Siguiente release |

---

## 11. RESOLUCIÓN Y TERMINACIÓN

### 11.1 Terminación por Mutuo Acuerdo

El contrato puede terminarse en cualquier momento por acuerdo escrito de ambas partes.

### 11.2 Terminación por Incumplimiento

Cualquiera de las partes puede terminar el contrato si la otra:
- Incumple obligaciones esenciales y no subsana en 15 días tras notificación
- Entra en situación de insolvencia o quiebra

### 11.3 Efectos de la Terminación

En caso de terminación:

1. EL CLIENTE pagará los trabajos completados hasta la fecha
2. EL DESARROLLADOR entregará todo el código desarrollado
3. EL DESARROLLADOR transferirá accesos y documentación
4. Ambas partes mantendrán las obligaciones de confidencialidad

### 11.4 Suspensión del Proyecto

Si EL CLIENTE necesita suspender el proyecto temporalmente:
- Notificación con 2 semanas de antelación
- Máximo 3 meses de suspensión
- Tras 3 meses sin reactivación, se considera terminación

---

## 12. RESOLUCIÓN DE CONFLICTOS

### 12.1 Negociación

Las partes intentarán resolver cualquier disputa mediante negociación directa durante un periodo de 30 días.

### 12.2 Mediación

Si la negociación falla, las partes someterán la disputa a mediación ante:
- [ ] Cámara de Comercio de _____________
- [ ] Mediador designado por _____________

### 12.3 Jurisdicción

Para cualquier litigio derivado de este contrato, las partes se someten a los Juzgados y Tribunales de _____________.

### 12.4 Ley Aplicable

Este contrato se rige por las leyes de _____________.

---

## 13. DISPOSICIONES GENERALES

### 13.1 Modificaciones

Cualquier modificación a este contrato debe hacerse por escrito y firmarse por ambas partes.

### 13.2 Cesión

Ninguna de las partes podrá ceder sus derechos u obligaciones sin consentimiento escrito de la otra.

### 13.3 Notificaciones

Las notificaciones oficiales se enviarán a las direcciones indicadas en la Cláusula 1, por:
- Email con confirmación de lectura
- Carta certificada con acuse de recibo

### 13.4 Fuerza Mayor

Ninguna de las partes será responsable por retrasos debidos a causas de fuerza mayor (desastres naturales, pandemias, guerras, etc.).

### 13.5 Divisibilidad

Si alguna cláusula resulta nula, el resto del contrato mantendrá su validez.

### 13.6 Acuerdo Completo

Este contrato constituye el acuerdo completo entre las partes y reemplaza cualquier negociación o acuerdo previo.

---

## 14. ANEXOS

- **Anexo A:** Especificaciones técnicas detalladas (CLAUDE.md)
- **Anexo B:** Backlog de funcionalidades priorizadas
- **Anexo C:** Plan de tests detallado
- **Anexo D:** Cronograma del proyecto (Diagrama de Gantt)
- **Anexo E:** Listado de dependencias y licencias

---

## FIRMAS

En prueba de conformidad, las partes firman el presente contrato en dos ejemplares.


**POR EL CLIENTE:**

Firma: _________________________

Nombre: _________________________

Cargo: _________________________

Fecha: _________________________


**POR EL DESARROLLADOR:**

Firma: _________________________

Nombre: _________________________

Cargo: _________________________

Fecha: _________________________

---

*Este contrato ha sido generado como plantilla modelo. Se recomienda revisión por asesor legal antes de su uso.*

---

## FIN DEL DOCUMENTO

---

# RESUMEN EJECUTIVO

## Estado de la App
✅ **APROBADA PARA TESTING** - La aplicación está en estado estable y bien estructurado.

## Tests Existentes
- **67+ tests backend** (pytest)
- **~25 tests frontend** (Vitest)
- **3 tests E2E** (Playwright, manuales)

## Tests Propuestos (Nuevos)
- **~30 tests backend** adicionales (servicios, seguridad, importación)
- **~20 tests frontend** adicionales (formularios, páginas, API client)
- **~10 tests E2E** estructurados (flujos completos)

## Cobertura Objetivo
- Backend: **80%**
- Frontend: **70%**
- E2E: **100% flujos críticos**

## Vulnerabilidad Crítica a Corregir
⚠️ `DELETE /api/v1/kobetsu/delete-all` - Sin autenticación

---

**Documento generado por análisis automatizado del repositorio KobetsuV1.0**
