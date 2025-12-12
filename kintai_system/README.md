# UNS 勤怠管理システム (Kintai Management System)

Sistema completo de gestión de asistencia y nómina para派遣社員 de **ユニバーサル企画株式会社**.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)
![Python](https://img.shields.io/badge/python-3.10+-green)

## 📋 Características

- ✅ **勤怠登録**: Registro de entrada/salida con cálculo automático
- ✅ **給与計算**: Cálculo con割増賃金 (残業25%, 深夜25%, 休日35%)
- ✅ **給与明細**: Generación de recibos individuales
- ✅ **控除計算**: 社会保険, 税金, 社宅, etc.
- ✅ **Visa Alerts**: Alertas de vencimiento de在留カード
- ✅ **Excel Export**: Generación de hojas de cálculo

## 🏢 Configuración UNS

| Campo | Valor |
|-------|-------|
| 会社名 | ユニバーサル企画株式会社 |
| 許可番号 | 派23-303669 |
| 社員数 | ~400名 |
| 派遣先 | 6+ 工場 |

## 📁 Estructura del Proyecto

```
kintai_system/
├── database/
│   ├── init_db.py          # Inicialización de DB
│   └── uns_kintai.db       # SQLite database
├── backend/
│   └── main.py             # FastAPI server
├── frontend/
│   └── KintaiApp.jsx       # React application
├── skill/
│   └── SKILL.md            # Claude skill definition
├── kintai_generator.py     # Excel generator
└── README.md
```

## 🚀 Instalación

### 1. Requisitos
```bash
pip install fastapi uvicorn openpyxl pandas --break-system-packages
```

### 2. Inicializar Base de Datos
```bash
cd database
python init_db.py
```

### 3. Iniciar API
```bash
cd backend
python main.py
# http://localhost:8080
```

### 4. Generar Excel
```bash
python kintai_generator.py
# Output: UNS_勤怠システム_YYYYMM.xlsx
```

## 📊 Base de Datos

### Tablas
| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| hakensaki | 6 | 派遣先（工場） |
| employees | 50 | 従業員マスタ |
| kintai | 2,000+ | 勤怠データ |
| salary | - | 給与計算結果 |

### 派遣先 Registradas
- 加藤木材工業株式会社 (本社・春日井)
- 高雄工業株式会社 (岡山)
- コーリツ株式会社
- ユアサ工機株式会社
- ピーエムアイ有限会社

## 🔧 API Endpoints

### Dashboard
```
GET /api/dashboard
```

### Employees
```
GET /api/employees
GET /api/employees?hakensaki_id=KATO-HON
GET /api/employees/{employee_id}
```

### Attendance
```
GET /api/kintai?year=2025&month=12
POST /api/kintai
```

### Salary
```
GET /api/salary/calculate?year=2025&month=12
```

## 💰 Cálculos de Nómina

### 割増率 (Premium Rates)
| 区分 | 率 |
|------|-----|
| 時間外 | 25% (×1.25) |
| 深夜 | 25% (×1.25) |
| 休日 | 35% (×1.35) |

### 控除率 (Deductions)
| 項目 | 率 |
|------|-----|
| 健康保険 | 5% |
| 厚生年金 | 9.15% |
| 雇用保険 | 0.6% |

## 📱 Frontend React

La aplicación React incluye:
- Dashboard con estadísticas
- Lista de empleados filtrable
- Vista de派遣先
- Cálculo de給与 con detalles

Para usar como artifact, copiar `frontend/KintaiApp.jsx`.

## 📄 License

Proprietary - ユニバーサル企画株式会社

---

Desarrollado con ❤️ para UNS | 2025
