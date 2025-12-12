---
name: uns-kintai-system
description: |
  Sistema de gestión de勤怠 (asistencia) y給与計算 (nómina) para trabajadores派遣 de UNS.
  Usar cuando necesites: (1) Registrar/consultar勤怠 de empleados, (2) Calcular給与 con割増,
  (3) Generar給与明細, (4) Reportes de asistencia mensual, (5) Alertas de visa, (6) Integrar con
  sistemas de Excel existentes. Triggers: 勤怠, kintai, asistencia, attendance, 給与計算,
  salary, nómina, payroll, 給与明細, タイムカード, timecard, 出退勤.
---

# UNS 勤怠管理システム (Kintai Management System)

Sistema completo de gestión de asistencia y nómina para派遣社員 de ユニバーサル企画株式会社.

## Características Principales

- **勤怠登録**: Registro de出勤/退勤 con cálculo automático de horas
- **給与計算**: Cálculo de salario con割増賃金 (残業25%, 深夜25%, 休日35%)
- **給与明細**: Generación de recibos de nómina individuales
- **控除計算**: Cálculos automáticos de deducciones (社会保険, 税金, 社宅, etc.)
- **Visa Alerts**: Alertas automáticas de vencimiento de在留カード

---

## Configuración UNS

### Información de Empresa
| Campo | Valor |
|-------|-------|
| 会社名 | ユニバーサル企画株式会社 |
| 許可番号 | 派23-303669 |
| 住所 | 愛知県名古屋市港区名港二丁目6-30 |
| 電話 | 052-938-8840 |
| 銀行口座 | 愛知銀行 当知支店 普通2075479 |

### 控除率 (Deduction Rates)
| 項目 | 率 | 備考 |
|------|-----|------|
| 健康保険 | 5.0% | 本人負担分 |
| 厚生年金 | 9.15% | 本人負担分 |
| 雇用保険 | 0.6% | 労働者負担 |
| 会社負担合計 | 15.76% | 健保5%+厚生9.15%+雇用0.95%+労災0.66% |

### 割増率 (Premium Rates)
| 区分 | 率 | 計算 |
|------|-----|------|
| 時間外労働 | 25%増 | 基本時給 × 1.25 |
| 深夜労働 | 25%増 | 基本時給 × 1.25 (追加分は0.25) |
| 休日労働 | 35%増 | 基本時給 × 1.35 |
| 60h超過残業 | 50%増 | 基本時給 × 1.50 |

---

## 派遣先別設定

### 高雄工業株式会社 (岡山工場)
- **締め日**: 15日
- **支払日**: 当月末日
- **勤務時間**: 昼勤 7:00-15:30 / 夜勤 19:00-3:30
- **休憩**: 45分
- **丸め単位**: 15分
- **基本時給**: ¥1,650

### 加藤木材工業株式会社 (本社・春日井)
- **締め日**: 20日
- **支払日**: 翌月20日
- **勤務時間**: 昼勤 8:00-17:00 / 夜勤 20:00-5:00
- **休憩**: 80分
- **丸め単位**: 5分
- **基本時給**: ¥1,700

### その他派遣先
- **締め日**: 20日（デフォルト）
- **支払日**: 翌月15日〜20日
- **基本時給**: ¥1,600〜¥1,700

---

## データベーススキーマ

### hakensaki (派遣先マスタ)
```sql
CREATE TABLE hakensaki (
    hakensaki_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    plant_name TEXT,
    closing_day INTEGER DEFAULT 20,
    payment_day TEXT,
    day_shift_start TEXT DEFAULT '08:00',
    day_shift_end TEXT DEFAULT '17:00',
    night_shift_start TEXT,
    night_shift_end TEXT,
    break_minutes INTEGER DEFAULT 60,
    base_rate REAL DEFAULT 1700
);
```

### employees (従業員マスタ)
```sql
CREATE TABLE employees (
    employee_id TEXT PRIMARY KEY,
    name_kanji TEXT NOT NULL,
    nationality TEXT DEFAULT 'ベトナム',
    visa_type TEXT,
    visa_expiry DATE,
    hakensaki_id TEXT REFERENCES hakensaki,
    hourly_wage REAL DEFAULT 1700,
    housing_rent REAL DEFAULT 25000,
    status TEXT DEFAULT '在職中'
);
```

### kintai (勤怠データ)
```sql
CREATE TABLE kintai (
    employee_id TEXT NOT NULL,
    work_date DATE NOT NULL,
    clock_in TIME,
    clock_out TIME,
    break_minutes INTEGER DEFAULT 60,
    actual_hours REAL,
    overtime_hours REAL DEFAULT 0,
    night_hours REAL DEFAULT 0,
    holiday_flag INTEGER DEFAULT 0,
    PRIMARY KEY (employee_id, work_date)
);
```

### salary (給与計算)
```sql
CREATE TABLE salary (
    employee_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    work_days INTEGER,
    regular_hours REAL,
    overtime_hours REAL,
    gross_salary REAL,
    total_deductions REAL,
    net_salary REAL,
    PRIMARY KEY (employee_id, year, month)
);
```

---

## API Endpoints

### Dashboard
```
GET /api/dashboard
```
Resumen general: empleados, horas trabajadas, alertas de visa.

### Employees
```
GET /api/employees                    # Lista todos
GET /api/employees?hakensaki_id=XXX   # Por派遣先
GET /api/employees/{employee_id}      # Individual
```

### Attendance
```
GET /api/kintai?year=2025&month=12              # Mes completo
GET /api/kintai?employee_id=E200801&year=2025   # Por empleado
POST /api/kintai                                 # Registrar entrada/salida
```

### Salary
```
GET /api/salary/calculate?year=2025&month=12    # Calcular nómina
GET /api/salary/calculate?employee_id=E200801   # Individual
```

---

## Uso con Claude

### Consultar勤怠
```
Usuario: ¿Cuántas horas trabajó グエン・ヴァン・ミン en diciembre?
Claude: [Consulta API /api/kintai?employee_id=E200801&year=2025&month=12]
```

### Calcular給与
```
Usuario: Calcula la nómina de todos los empleados de加藤木材
Claude: [Consulta API /api/salary/calculate?hakensaki_id=KATO-HON]
```

### Generar Excel de勤怠
```
Usuario: Genera la勤怠表 de diciembre 2025
Claude: [Ejecuta kintai_generator.py con parámetros]
```

---

## Archivos del Sistema

| Archivo | Descripción |
|---------|-------------|
| `database/init_db.py` | Inicialización de SQLite |
| `database/uns_kintai.db` | Base de datos |
| `backend/main.py` | API FastAPI |
| `frontend/KintaiApp.jsx` | Interfaz React |
| `kintai_generator.py` | Generador de Excel |

---

## Ejecutar el Sistema

### 1. Inicializar Base de Datos
```bash
cd database
python init_db.py
```

### 2. Iniciar API Backend
```bash
cd backend
pip install fastapi uvicorn
python main.py
# API disponible en http://localhost:8080
```

### 3. Generar Excel
```bash
python kintai_generator.py
# Genera: UNS_勤怠システム_YYYYMM.xlsx
```

---

## Integración con Excel Existente

El sistema puede importar datos del Excel actual de UNS:

### Hojas Soportadas
- **勤怠表**: Datos de asistencia (53 columnas)
- **給料明細PMI**: Cálculos de nómina
- **派遣社員**: Maestro de empleados

### Importar desde Excel
```python
from database.init_db import import_from_excel
import_from_excel("path/to/勤怠表.xlsm")
```

---

## Notas Legales

Este sistema cumple con:
- 労働基準法 (Ley de Normas Laborales)
- 労働者派遣法 (Ley de Dispatch de Trabajadores)
- 最低賃金法 (Ley de Salario Mínimo)

Requisitos legales implementados:
- Registro de勤怠 por minuto (実績)
- Cálculo de割増賃金 según ley
- Retención de registros por 3 años
