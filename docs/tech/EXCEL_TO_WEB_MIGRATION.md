# Migración del Sistema Excel a Sistema Web - Kobetsu Keiyakusho

## Resumen Ejecutivo

Este documento analiza el sistema Excel existente (個別契約書TEXPERT2025.7) y propone una estrategia de migración al sistema web UNS-Kobetsu-Keiyakusho.

---

## Análisis del Sistema Excel Actual

### Verificación de Estructura

**Archivo analizado:** `個別契約書TEXPERT2025.7PerfectSin nada .xlsx`

✅ **Confirmado:**
- **18 hojas** exactamente como documentado
- **4 Tablas Excel** con rangos verificados:
  - `DBGenzai` (A1:AP1029) - 1,028 empleados
  - `TablaTransfor` (B2:AC198) - Datos transformados
  - `TBKaishaInfo` (A1:AQ112) - 111 configuraciones de empresas
  - `TablaTsuchichou` (J8:R57) - Resumen de notificaciones

- **20 Nombres Definidos** verificados:
  - `派遣先` → 個別契約書X!$AD$1 (Empresa actual: 加藤木材工業株式会社)
  - `工場名` → 個別契約書X!$AD$2 (Fábrica actual: 本社工場)
  - `配属先` → 個別契約書X!$AD$3 (Departamento: 生産1部)
  - `ライン` → 個別契約書X!$AD$4 (Línea: 2課)
  - `HakenkikanS` → 個別契約書X!$H$16 (Fecha inicio)
  - `HakenKikanE` → 個別契約書X!$P$16 (Fecha fin)

- **Conteo de Fórmulas Verificado:**
  - Filtro: 2,299 fórmulas
  - Trasformacion: 5,507 fórmulas (la más compleja)
  - 通知書: 325 fórmulas
  - DAICHO: 30 fórmulas
  - ListaDinamicas: 4 fórmulas (UNIQUE/FILTER)

### Estructura de Datos Principal

#### DBGenzai (Base de Datos de Empleados)
```
Columnas principales (15 primeras de 51 totales):
1. 現在 (Estado actual) - "退社" o vacío
2. 社員№ (Nº Empleado) - Ej: 200805
3. 派遣先ID (ID Empresa destino)
4. 派遣先 (Empresa destino) - Ej: "ピーエムアイ"
5. 配属先 (Departamento asignado)
6. 配属ライン (Línea asignada)
7. 仕事内容 (Contenido trabajo)
8. 氏名 (Nombre) - Ej: "VI THI HUE"
9. カナ (Katakana)
10. 性別 (Sexo)
11. 国籍 (Nacionalidad) - Principalmente "ベトナム"
12. 生年月日 (Fecha nacimiento)
13. 年齢 (Edad)
14. 時給 (Salario por hora)
15. 時給改定 (Revisión salario)
```

#### TBKaisha (Información de Empresas Cliente)
```
Columnas principales (10 primeras de 48 totales):
1. 派遣先 (Empresa destino)
2. 派遣先住所 (Dirección empresa)
3. 派遣先電話 (Teléfono empresa)
4. 派遣先責任者部署 (Departamento responsable)
5. 派遣先責任者名 (Nombre responsable)
6. 派遣先責任者電話 (Teléfono responsable)
7. 工場名 (Nombre fábrica)
8. 工場住所 (Dirección fábrica)
9. 工場電話 (Teléfono fábrica)
10. 配属先 (Departamento asignación)
```

---

## Mapeo Excel → Base de Datos PostgreSQL

### 1. Tabla `employees` (desde DBGenzai)

| Excel (DBGenzai) | PostgreSQL | Tipo | Notas |
|------------------|------------|------|-------|
| 社員№ | employee_number | VARCHAR(20) | PK alternativa |
| 氏名 | full_name | VARCHAR(100) | Nombre completo |
| カナ | katakana_name | VARCHAR(100) | Lectura katakana |
| 性別 | gender | VARCHAR(10) | M/F |
| 国籍 | nationality | VARCHAR(50) | Principalmente "Vietnam" |
| 生年月日 | date_of_birth | DATE | Fecha nacimiento |
| 年齢 | age | INTEGER | Calculado |
| 現在 | status | VARCHAR(20) | "active"/"resigned" |
| 入社日 | hire_date | DATE | Desde columnas posteriores |
| 退社日 | resignation_date | DATE | Si 現在="退社" |
| ビザ期限 | visa_expiry_date | DATE | Fecha límite visa |

### 2. Tabla `factories` (desde TBKaisha)

| Excel (TBKaisha) | PostgreSQL | Tipo | Notas |
|------------------|------------|------|-------|
| 派遣先 | company_name | VARCHAR(200) | Nombre empresa cliente |
| 派遣先住所 | company_address | TEXT | Dirección |
| 派遣先電話 | company_phone | VARCHAR(20) | Teléfono |
| 工場名 | factory_name | VARCHAR(200) | Nombre fábrica |
| 工場住所 | factory_address | TEXT | Dirección fábrica |
| 配属先 | department | VARCHAR(100) | Departamento |
| ライン | line | VARCHAR(50) | Línea producción (CLAVE) |
| 仕事内容 | work_content | TEXT | Descripción trabajo |
| 時給単価 | hourly_rate | DECIMAL(10,2) | Tarifa hora |
| 抵触日 | limit_date | DATE | Fecha límite contrato |

### 3. Tabla `kobetsu_keiyakusho` (Nueva - desde 個別契約書X)

| Origen Excel | PostgreSQL | Tipo | Notas |
|--------------|------------|------|-------|
| H16 (HakenkikanS) | dispatch_start_date | DATE | Fecha inicio |
| P16 (HakenKikanE) | dispatch_end_date | DATE | Fecha fin |
| AD1 (派遣先) | factory_id | INTEGER | FK a factories |
| AD2 (工場名) | - | - | Redundante (en factory) |
| AD3 (配属先) | - | - | Redundante (en factory) |
| AD4 (ライン) | - | - | Redundante (en factory) |
| AD5 (時給単価) | hourly_rate | DECIMAL(10,2) | Tarifa |
| Generado | contract_number | VARCHAR(50) | KOB-YYYYMM-XXXX |
| Generado | contract_date | DATE | Fecha firma |

### 4. Tabla `kobetsu_employees` (Join table)

Relaciona contratos con empleados (relación many-to-many):
```sql
CREATE TABLE kobetsu_employees (
    kobetsu_id INTEGER REFERENCES kobetsu_keiyakusho(id),
    employee_id INTEGER REFERENCES employees(id),
    PRIMARY KEY (kobetsu_id, employee_id)
);
```

---

## Estrategia de Migración

### Fase 1: Importación Inicial de Datos

#### Script de Importación: `import_from_excel.py`

```python
# backend/scripts/import_from_excel.py

import openpyxl
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.employee import Employee
from app.models.factory import Factory
from datetime import datetime

def import_employees_from_excel(file_path: str, db: Session):
    """Importa empleados desde DBGenzai"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb['DBGenzai']

    # Saltar header (fila 1)
    for row in list(ws.rows)[1:]:
        status_raw = row[0].value  # 現在
        employee_number = row[1].value  # 社員№
        full_name = row[7].value  # 氏名
        katakana_name = row[8].value  # カナ
        gender = row[9].value  # 性別
        nationality = row[10].value  # 国籍
        date_of_birth = row[11].value  # 生年月日

        # Determinar status
        status = 'resigned' if status_raw == '退社' else 'active'

        # Crear o actualizar empleado
        employee = db.query(Employee).filter_by(
            employee_number=employee_number
        ).first()

        if not employee:
            employee = Employee(
                employee_number=employee_number,
                full_name=full_name,
                katakana_name=katakana_name,
                gender=gender,
                nationality=nationality,
                date_of_birth=date_of_birth,
                status=status
            )
            db.add(employee)

    db.commit()
    wb.close()

def import_factories_from_excel(file_path: str, db: Session):
    """Importa empresas/fábricas desde TBKaisha"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb['TBKaisha']

    for row in list(ws.rows)[1:]:
        company_name = row[0].value  # 派遣先
        company_address = row[1].value  # 派遣先住所
        factory_name = row[6].value  # 工場名
        factory_address = row[7].value  # 工場住所
        department = row[9].value  # 配属先
        line = row[13].value  # ライン (columna 14, índice 13)
        work_content = row[15].value  # 仕事内容

        # Crear factory (combinación única: company + factory + department + line)
        factory_key = f"{company_name}_{factory_name}_{department}_{line}"

        factory = db.query(Factory).filter_by(
            company_name=company_name,
            factory_name=factory_name,
            department=department,
            line=line
        ).first()

        if not factory:
            factory = Factory(
                company_name=company_name,
                company_address=company_address,
                factory_name=factory_name,
                factory_address=factory_address,
                department=department,
                line=line,
                work_content=work_content
            )
            db.add(factory)

    db.commit()
    wb.close()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        excel_path = "path/to/個別契約書TEXPERT2025.7.xlsx"

        print("Importando empleados...")
        import_employees_from_excel(excel_path, db)

        print("Importando empresas/fábricas...")
        import_factories_from_excel(excel_path, db)

        print("✅ Importación completada")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
```

### Fase 2: Replicar Lógica de Filtrado

El sistema Excel usa una arquitectura de 3 capas:
1. **Filtro**: Añade contadores únicos
2. **Transformación**: Filtra por empresa seleccionada
3. **Documentos**: Generan PDFs basados en datos transformados

En el sistema web, esto se simplifica con:

```python
# backend/app/services/kobetsu_service.py

def get_employees_for_factory(
    self,
    factory_id: int,
    status: str = "active"
) -> List[Employee]:
    """
    Replica la funcionalidad de Filtro + Transformación
    """
    factory = self.db.query(Factory).filter_by(id=factory_id).first()

    # Buscar empleados asignados a esta empresa
    employees = (
        self.db.query(Employee)
        .filter(
            Employee.status == status,
            Employee.current_factory_id == factory_id
        )
        .all()
    )

    return employees

def get_employees_by_line(
    self,
    company_name: str,
    factory_name: str,
    department: str,
    line: str
) -> List[Employee]:
    """
    Búsqueda exacta como en Excel usando ライン
    """
    factory = (
        self.db.query(Factory)
        .filter(
            Factory.company_name == company_name,
            Factory.factory_name == factory_name,
            Factory.department == department,
            Factory.line == line
        )
        .first()
    )

    if not factory:
        return []

    return self.get_employees_for_factory(factory.id)
```

### Fase 3: Generación de Documentos

El sistema Excel genera múltiples documentos. El sistema web debe replicar:

#### Documentos Prioritarios:

1. **個別契約書 (Contrato Individual)** → `kobetsu_pdf_service.py` (✅ Ya implementado)
2. **通知書 (Notificación)** → Nuevo servicio
3. **DAICHO (台帳 - Registro)** → Nuevo servicio
4. **派遣元管理台帳** → Nuevo servicio
5. **就業条件明示書** → Nuevo servicio

```python
# backend/app/services/dispatch_documents_service.py

from docx import Document
from datetime import datetime

class DispatchDocumentsService:
    """Genera documentos de dispatch (通知書, DAICHO, etc.)"""

    def generate_tsuchisho(
        self,
        factory: Factory,
        employees: List[Employee],
        dispatch_start: date,
        dispatch_end: date
    ) -> str:
        """
        Genera 通知書 (Notificación a empresa cliente)
        Replica hoja: 通知書
        """
        doc = Document()

        # Título
        doc.add_heading('労働者派遣個別契約に基づく通知書', 0)

        # Información de empresa
        doc.add_paragraph(f'派遣先: {factory.company_name}')
        doc.add_paragraph(f'工場名: {factory.factory_name}')
        doc.add_paragraph(f'派遣期間: {dispatch_start} ～ {dispatch_end}')

        # Tabla de empleados
        table = doc.add_table(rows=1, cols=7)
        table.style = 'Table Grid'

        # Headers
        headers = ['氏名', 'カナ', '性別', '年齢', '雇用保険', '健康保険', '厚生年金']
        for i, header in enumerate(headers):
            table.rows[0].cells[i].text = header

        # Datos de empleados
        for emp in employees:
            row = table.add_row()
            row.cells[0].text = emp.full_name
            row.cells[1].text = emp.katakana_name
            row.cells[2].text = emp.gender
            row.cells[3].text = str(emp.age)
            row.cells[4].text = '有' if emp.employment_insurance else '無'
            row.cells[5].text = '有' if emp.health_insurance else '有'
            row.cells[6].text = '有' if emp.pension_insurance else '有'

        # Guardar
        output_path = f'outputs/tsuchisho_{factory.id}_{datetime.now().strftime("%Y%m%d")}.docx'
        doc.save(output_path)

        return output_path

    def generate_daicho(
        self,
        employee: Employee,
        factory: Factory,
        contract: KobetsuKeiyakusho
    ) -> str:
        """
        Genera DAICHO (台帳 - Registro individual)
        Replica hoja: DAICHO
        """
        doc = Document()

        doc.add_heading('派遣元管理台帳', 0)

        # Información del trabajador
        doc.add_paragraph(f'氏名: {employee.full_name}')
        doc.add_paragraph(f'カナ: {employee.katakana_name}')
        doc.add_paragraph(f'生年月日: {employee.date_of_birth}')
        doc.add_paragraph(f'国籍: {employee.nationality}')

        # Información del contrato
        doc.add_paragraph(f'\n派遣先: {factory.company_name}')
        doc.add_paragraph(f'派遣期間: {contract.dispatch_start_date} ～ {contract.dispatch_end_date}')
        doc.add_paragraph(f'業務内容: {contract.work_content}')
        doc.add_paragraph(f'時給: {contract.hourly_rate}円')

        output_path = f'outputs/daicho_{employee.id}_{datetime.now().strftime("%Y%m%d")}.docx'
        doc.save(output_path)

        return output_path
```

### Fase 4: API Endpoints para Importación

```python
# backend/app/api/v1/imports.py

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.import_service import ImportService

router = APIRouter()

@router.post("/excel/employees")
async def import_employees_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Importa empleados desde archivo Excel (DBGenzai)
    """
    service = ImportService(db)
    result = await service.import_employees(file)

    return {
        "success": True,
        "imported": result["count"],
        "skipped": result["skipped"],
        "errors": result["errors"]
    }

@router.post("/excel/factories")
async def import_factories_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Importa empresas/fábricas desde Excel (TBKaisha)
    """
    service = ImportService(db)
    result = await service.import_factories(file)

    return {
        "success": True,
        "imported": result["count"],
        "errors": result["errors"]
    }
```

---

## Ventajas del Sistema Web sobre Excel

### 1. **Búsqueda y Filtrado**
- **Excel**: Requiere fórmulas complejas (XLOOKUP + COUNTIF) con 5,500+ fórmulas
- **Web**: Consultas SQL directas, instantáneas

### 2. **Concurrencia**
- **Excel**: Solo un usuario puede editar a la vez
- **Web**: Múltiples usuarios simultáneos con control de transacciones

### 3. **Historial y Auditoría**
- **Excel**: Sin historial de cambios (a menos que uses versiones)
- **Web**: Registro completo de quién modificó qué y cuándo

### 4. **Validación de Datos**
- **Excel**: Validación limitada por celdas
- **Web**: Validación robusta con Pydantic schemas

### 5. **Generación de Documentos**
- **Excel**: Hojas separadas para cada documento
- **Web**: Generación dinámica bajo demanda con plantillas

### 6. **Escalabilidad**
- **Excel**: 1,048,576 filas máximo
- **Web**: PostgreSQL maneja millones de registros

### 7. **Acceso Remoto**
- **Excel**: Requiere compartir archivo
- **Web**: Acceso desde cualquier navegador

---

## Plan de Migración Gradual

### Etapa 1: Coexistencia (1-2 meses)
- Sistema Excel sigue activo
- Importar datos manualmente cada semana
- Usuarios prueban sistema web con datos reales
- Identificar gaps funcionales

### Etapa 2: Migración Parcial (2-3 meses)
- Nuevos contratos se crean en sistema web
- Contratos antiguos permanecen en Excel
- Ambos sistemas activos

### Etapa 3: Migración Total (3-4 meses)
- Importar todos los contratos históricos
- Capacitación final de usuarios
- Desactivar sistema Excel
- Excel se mantiene como backup/archivo

### Etapa 4: Optimización (4-6 meses)
- Ajustes basados en feedback
- Automatizaciones adicionales
- Integraciones con otros sistemas

---

## Checklist de Funcionalidades

### ✅ Ya Implementado en Sistema Web:
- [x] CRUD de contratos (kobetsu_keiyakusho)
- [x] Gestión de empleados
- [x] Gestión de empresas/fábricas
- [x] Generación de PDF de contratos
- [x] Dashboard con estadísticas
- [x] Autenticación JWT
- [x] API REST completa

### 🚧 Pendiente de Implementar:
- [ ] Importador de Excel (DBGenzai, TBKaisha)
- [ ] Generación de 通知書 (Notificación)
- [ ] Generación de DAICHO (Registro)
- [ ] Generación de 派遣元管理台帳
- [ ] Generación de 就業条件明示書
- [ ] Generación de タイムシート (Timesheet)
- [ ] Cascada dinámica: Empresa → Fábrica → Departamento → Línea
- [ ] Filtro por 配属ライン (línea de asignación) como clave única
- [ ] Cálculo automático de edad desde fecha nacimiento
- [ ] Validación de fecha límite de visa
- [ ] Soporte para empleados vietnamitas (campos específicos)

---

## Recomendaciones

### 1. Priorizar Importación de Datos
El sistema Excel tiene **1,028 empleados** y **111 configuraciones de empresas**. Crear un importador robusto es crítico.

### 2. Mantener Compatibilidad con Estructura Excel
La clave de búsqueda en Excel es:
```
派遣先 + 工場名 + 配属先 + ライン
```
Esta combinación debe ser única en la tabla `factories`.

### 3. Implementar Búsqueda por ライン
El campo `ライン` (línea de producción) es crítico para el sistema Excel. Debe ser:
- Indexado en PostgreSQL
- Parte de la clave única de `factories`
- Visible prominentemente en el UI

### 4. Replicar Listas Dinámicas
Excel usa `UNIQUE(FILTER(...))` para generar listas desplegables. En el web:
```typescript
// frontend/components/factory/FactoryCascadeSelector.tsx
const [companies, setCompanies] = useState([])
const [factories, setFactories] = useState([])
const [departments, setDepartments] = useState([])
const [lines, setLines] = useState([])

// Cuando cambia empresa, filtrar fábricas
useEffect(() => {
  if (selectedCompany) {
    api.get(`/factories/filter?company=${selectedCompany}`)
      .then(res => setFactories(res.data))
  }
}, [selectedCompany])

// Cuando cambia fábrica, filtrar departamentos, etc.
```

### 5. Preservar Formato de Documentos
Los documentos generados por Excel tienen un formato específico que los usuarios conocen. El sistema web debe:
- Usar las mismas plantillas DOCX
- Mantener el mismo orden de campos
- Respetar el formato japonés (年月日, etc.)

---

## Conclusión

El sistema Excel es robusto y ha estado funcionando bien, pero tiene limitaciones inherentes. El sistema web UNS-Kobetsu-Keiyakusho puede replicar todas las funcionalidades mientras añade:
- Acceso multi-usuario
- Auditoría completa
- Escalabilidad ilimitada
- Acceso remoto
- Integración con otros sistemas

**Próximos pasos inmediatos:**
1. Crear script de importación desde Excel
2. Implementar generador de 通知書
3. Añadir selector en cascada (Empresa → Fábrica → Depto → Línea)
4. Probar con datos reales del Excel actual
