# 個別契約書管理システム (Kobetsu Keiyakusho Management System)

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-15.0+-black.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)

**Sistema completo para generar y gestionar 個別契約書 (Contratos Individuales de Dispatch) según la 労働者派遣法第26条**

[Características](#-características) •
[Instalación](#-instalación) •
[Documentación](#-documentación) •
[API](#-api) •
[Contribuir](#-contribuir)

</div>

---

## 📋 **Tabla de Contenidos**

- [¿Qué es 個別契約書?](#-qué-es-個別契約書)
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [API Endpoints](#-api-endpoints)
- [Tecnologías](#-tecnologías)
- [Roadmap](#-roadmap)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## 🎯 **¿Qué es 個別契約書?**

個別契約書 (Kobetsu Keiyakusho) es el **contrato individual de dispatch** que las 派遣元 (empresas de staffing) deben crear con las 派遣先 (empresas cliente) cada vez que envían trabajadores.

### **Requisitos Legales (労働者派遣法第26条)**

Este contrato es **OBLIGATORIO** por ley y debe incluir **16 items específicos**:

1. ✅ **業務内容** - Contenido del trabajo
2. ✅ **責任の程度** - Nivel de responsabilidad
3. ✅ **派遣先事業所** - Lugar de trabajo (nombre, dirección, organización)
4. ✅ **指揮命令者** - Supervisor directo
5. ✅ **就業日** - Días de trabajo
6. ✅ **就業時間** - Horarios (inicio, fin, descansos)
7. ✅ **安全衛生** - Seguridad e higiene
8. ✅ **苦情処理** - Manejo de quejas
9. ✅ **契約解除時の措置** - Medidas en caso de cancelación
10. ✅ **派遣元責任者** - Responsable de派遣元
11. ✅ **派遣先責任者** - Responsable de派遣先
12. ✅ **時間外労働** - Horas extra
13. ✅ **福利厚生** - Instalaciones y beneficios
14. ✅ **直接雇用防止措置** - Prevención de contratación directa
15. ✅ **労使協定方式** - Método de acuerdo laboral
16. ✅ **無期雇用・60歳以上** - Empleados permanentes/+60 años

---

## ✨ **Características**

### **🎨 Generación Automatizada**
- ✅ Auto-completado inteligente desde base de datos
- ✅ Generación de número de contrato automático
- ✅ Validación de todos los 16 items obligatorios
- ✅ Plantillas profesionales en formato DOCX/PDF

### **📊 Dashboard de Gestión**
- ✅ Vista de todos los contratos activos
- ✅ Filtros por empresa cliente, estado, fecha
- ✅ Alertas de contratos próximos a vencer
- ✅ Estadísticas en tiempo real

### **📝 Gestión Completa del Ciclo**
- ✅ Borradores editables
- ✅ Contratos activos
- ✅ Renovaciones automáticas
- ✅ Historial completo

### **🔒 Control y Auditoría**
- ✅ Registro de quién creó cada contrato
- ✅ Historial de cambios
- ✅ Control de acceso por roles
- ✅ Exportación de reportes

### **🚀 Integración con Sistema Existente**
- ✅ Se integra con UNS-ClaudeJP
- ✅ Usa datos de `factories` y `employees`
- ✅ Compatible con `dispatch_assignments`
- ✅ API REST completa

---

## 📦 **Requisitos**

### **Software**
- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Python 3.11+
- Node.js 18+
- Git

### **Recursos**
- 4GB RAM mínimo (8GB recomendado)
- 10GB espacio en disco
- Puertos disponibles: 3000, 8000, 5432, 6379

---

## 🚀 **Instalación**

### **Opción 1: Standalone (Nuevo Proyecto)**

```bash
# 1. Clonar repositorio
git clone https://github.com/jokken79/UNS-Kobetsu-Keiyakusho.git
cd UNS-Kobetsu-Keiyakusho

# 2. El archivo .env ya está configurado ✅
# (SECRET_KEY seguro, puertos personalizados, etc.)

# 3. Iniciar servicios con Docker
docker compose up -d

# 4. Aplicar migraciones
docker exec -it uns-kobetsu-backend alembic upgrade head

# 5. Crear usuario admin (opcional)
docker exec -it uns-kobetsu-backend python scripts/create_admin.py

# 6. Importar datos demo (opcional)
docker exec -it uns-kobetsu-backend python scripts/import_demo_data.py
```

**📖 Ver guía detallada:** [INICIO_RAPIDO.md](INICIO_RAPIDO.md)

### **Opción 2: Integración con UNS-ClaudeJP**

```bash
# 1. Navegar a tu proyecto UNS-ClaudeJP existente
cd /path/to/UNS-ClaudeJP-6.0.0

# 2. Clonar módulo de Kobetsu
git clone https://github.com/jokken79/UNS-Kobetsu-Keiyakusho.git modules/kobetsu

# 3. Aplicar migration a tu base de datos existente
docker exec -it uns-claudejp-backend alembic upgrade head

# 4. Copiar archivos de backend
cp -r modules/kobetsu/backend/app/api/kobetsu.py backend/app/api/
cp -r modules/kobetsu/backend/app/models/kobetsu_keiyakusho.py backend/app/models/
cp -r modules/kobetsu/backend/app/schemas/kobetsu_keiyakusho.py backend/app/schemas/
cp -r modules/kobetsu/backend/app/services/kobetsu_service.py backend/app/services/

# 5. Copiar archivos de frontend
cp -r modules/kobetsu/frontend/app/kobetsu/ frontend/app/(dashboard)/

# 6. Reiniciar servicios
docker compose restart backend frontend
```

---

## 💻 **Uso Rápido**

### **1. Acceder al Sistema**
```
Frontend: http://localhost:3010/kobetsu
Backend API: http://localhost:8010/docs
Adminer DB: http://localhost:8090
```

**Puertos personalizados** para evitar conflictos:
- PostgreSQL: 5442
- Redis: 6389
- Backend: 8010
- Frontend: 3010
- Adminer: 8090

### **2. Crear Nuevo Contrato**

1. **Ir a: Menú → 個別契約書 → 新規作成**
2. **Seleccionar 派遣先 (Empresa Cliente)**
   - Auto-completa: nombre, dirección, responsable
3. **Seleccionar Trabajadores**
   - Buscar y seleccionar múltiples empleados
4. **Completar Detalles**
   - Fechas de dispatch
   - Condiciones laborales
   - Horarios y tarifas
5. **Generar Contrato**
   - Se crea el PDF automáticamente
   - Se guarda en la base de datos

### **3. Ver Dashboard**

```
📊 Contratos Activos: 45
⚠️ Próximos a Vencer (30 días): 5
✅ Firmados este mes: 12
📄 Borradores: 3
```

---

## 📁 **Estructura del Proyecto**

```
UNS-Kobetsu-Keiyakusho/
├── backend/                    # FastAPI Backend
│   ├── alembic/               # Database migrations
│   │   └── versions/
│   │       └── add_kobetsu_keiyakusho.py
│   ├── app/
│   │   ├── api/
│   │   │   └── kobetsu.py    # API endpoints
│   │   ├── models/
│   │   │   └── kobetsu_keiyakusho.py
│   │   ├── schemas/
│   │   │   └── kobetsu_keiyakusho.py
│   │   ├── services/
│   │   │   ├── kobetsu_service.py
│   │   │   └── kobetsu_pdf_service.py
│   │   └── main.py
│   ├── scripts/
│   │   ├── create_admin.py
│   │   └── import_demo_data.py
│   └── requirements.txt
│
├── frontend/                   # Next.js Frontend
│   ├── app/
│   │   └── kobetsu/
│   │       ├── page.tsx       # Dashboard
│   │       ├── create/        # Crear nuevo
│   │       ├── [id]/          # Ver/Editar
│   │       └── list/          # Lista
│   ├── components/
│   │   └── kobetsu/
│   │       ├── KobetsuForm.tsx
│   │       ├── KobetsuTable.tsx
│   │       └── KobetsuStats.tsx
│   └── package.json
│
├── docs/                       # Documentación
│   ├── API.md                 # API Reference
│   ├── LEGAL.md               # Requisitos legales
│   ├── INTEGRATION.md         # Guía de integración
│   └── SCREENSHOTS/           # Capturas de pantalla
│
├── docker-compose.yml         # Docker orchestration
├── .env.example               # Variables de entorno
├── README.md                  # Este archivo
└── LICENSE                    # Licencia MIT
```

---

## 🔌 **API Endpoints**

### **個別契約書 Management**

```http
POST   /api/kobetsu                    # Crear nuevo contrato
GET    /api/kobetsu                    # Listar contratos
GET    /api/kobetsu/{id}               # Obtener contrato
PUT    /api/kobetsu/{id}               # Actualizar contrato
DELETE /api/kobetsu/{id}               # Eliminar contrato
GET    /api/kobetsu/{id}/pdf           # Generar PDF
GET    /api/kobetsu/{id}/employees     # Empleados del contrato
POST   /api/kobetsu/{id}/renew         # Renovar contrato
GET    /api/kobetsu/stats              # Estadísticas
```

### **Búsqueda y Filtros**

```http
GET /api/kobetsu?factory_id=1                    # Por empresa
GET /api/kobetsu?status=active                   # Por estado
GET /api/kobetsu?expiring_within_days=30         # Próximos a vencer
GET /api/kobetsu?date_from=2024-01-01&date_to=2024-12-31
```

### **Ejemplo de Request**

```json
POST /api/kobetsu
{
  "factory_id": 1,
  "employee_ids": [10, 11, 12],
  "contract_date": "2024-11-25",
  "dispatch_start_date": "2024-12-01",
  "dispatch_end_date": "2025-11-30",
  "work_content": "製造ライン作業、検品、梱包業務",
  "responsibility_level": "通常業務",
  "worksite_name": "トヨタ自動車株式会社 田原工場",
  "work_days": ["月", "火", "水", "木", "金"],
  "work_start_time": "08:00",
  "work_end_time": "17:00",
  "hourly_rate": 1500,
  "overtime_rate": 1875
}
```

📖 **[Ver API completa →](docs/API.md)**

---

## 🛠️ **Tecnologías**

### **Backend**
- **FastAPI** 0.115+ - REST API framework
- **SQLAlchemy** 2.0+ - ORM
- **PostgreSQL** 15 - Base de datos
- **Alembic** - Migraciones
- **python-docx** - Generación de DOCX
- **Pydantic** - Validación de datos

### **Frontend**
- **Next.js** 15.0+ - Framework React
- **React** 19.0+ - UI library
- **TypeScript** 5.6+ - Type safety
- **Tailwind CSS** - Styling
- **Shadcn/ui** - Componentes
- **React Query** - Server state
- **Zustand** - State management

### **DevOps**
- **Docker** - Containerización
- **Docker Compose** - Orquestación
- **Git** - Control de versiones
- **GitHub Actions** - CI/CD

---

## 🗺️ **Roadmap**

### **v1.0 (Actual)** ✅
- [x] CRUD completo de 個別契約書
- [x] Generación de PDF/DOCX
- [x] Dashboard de gestión
- [x] Integración con UNS-ClaudeJP
- [x] API REST completa

### **v1.1 (Q1 2025)** 🚧
- [ ] Firma electrónica
- [ ] Notificaciones automáticas de vencimiento
- [ ] Plantillas personalizables
- [ ] Exportación masiva
- [ ] App móvil

### **v1.2 (Q2 2025)** 📝
- [ ] Integración con e-Gov
- [ ] OCR para contratos escaneados
- [ ] Análisis de contratos con IA
- [ ] Portal para empresas cliente
- [ ] Multiidioma (inglés, portugués, español)

---

## 🤝 **Contribuir**

¡Las contribuciones son bienvenidas! Por favor lee nuestra [Guía de Contribución](CONTRIBUTING.md).

### **Pasos para Contribuir**

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 **Licencia**

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 📞 **Soporte**

- 📧 Email: support@uns-kikaku.jp
- 🐛 Issues: [GitHub Issues](https://github.com/jokken79/UNS-Kobetsu-Keiyakusho/issues)
- 📖 Docs: [Documentación Completa](docs/)
- 💬 Discord: [Únete a la comunidad](https://discord.gg/uns-kikaku)

---

## 🙏 **Agradecimientos**

- FastAPI team por el excelente framework
- Next.js team por React App Router
- Shadcn por los componentes UI
- Comunidad de desarrollo japonés

---

<div align="center">

**Desarrollado con ❤️ para empresas de staffing japonesas**

UNS Kikaku © 2024

[⬆ Volver arriba](#個別契約書管理システム-kobetsu-keiyakusho-management-system)

</div>
