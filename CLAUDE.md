# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**UNS Kobetsu Keiyakusho Management System** - A full-stack application for managing 個別契約書 (individual dispatch contracts) in compliance with Japanese Labor Dispatch Law (労働者派遣法第26条). The system ensures all 16 legally required contract items are properly documented and managed.

**Tech Stack:**
- **Backend:** FastAPI 0.115+, SQLAlchemy 2.0+, PostgreSQL 15, Redis, Alembic
- **Frontend:** Next.js 15, React 18+, TypeScript 5.6+, Tailwind CSS, Zustand
- **DevOps:** Docker Compose, custom ports (8010, 3010, 5442, 6389, 8090)

## Development Commands

### Docker Operations

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f
docker compose logs -f backend    # Backend only
docker compose logs -f frontend   # Frontend only

# Stop services
docker compose down

# Rebuild after dependency changes
docker compose up -d --build

# Access containers
docker exec -it uns-kobetsu-backend bash
docker exec -it uns-kobetsu-frontend sh
```

### Database Migrations

```bash
# Apply all migrations
docker exec -it uns-kobetsu-backend alembic upgrade head

# Create new migration
docker exec -it uns-kobetsu-backend alembic revision --autogenerate -m "description"

# Rollback one migration
docker exec -it uns-kobetsu-backend alembic downgrade -1

# View migration history
docker exec -it uns-kobetsu-backend alembic history

# View current version
docker exec -it uns-kobetsu-backend alembic current
```

### Backend Development

```bash
# Run tests
docker exec -it uns-kobetsu-backend pytest
docker exec -it uns-kobetsu-backend pytest -v  # Verbose output
docker exec -it uns-kobetsu-backend pytest tests/test_kobetsu_api.py  # Single file
docker exec -it uns-kobetsu-backend pytest tests/test_kobetsu_api.py::test_create_kobetsu  # Single test

# Python shell with app context
docker exec -it uns-kobetsu-backend python

# Create admin user
docker exec -it uns-kobetsu-backend python scripts/create_admin.py

# Import demo data
docker exec -it uns-kobetsu-backend python scripts/import_demo_data.py

# Access FastAPI docs
# http://localhost:8010/docs
```

### Frontend Development

```bash
# Install dependencies (if modified)
docker exec -it uns-kobetsu-frontend npm install

# Run tests
docker exec -it uns-kobetsu-frontend npm test
docker exec -it uns-kobetsu-frontend npm run test:watch

# Lint code
docker exec -it uns-kobetsu-frontend npm run lint

# Build production bundle
docker exec -it uns-kobetsu-frontend npm run build
```

### Access Points

- **Frontend:** http://localhost:3010
- **Backend API:** http://localhost:8010/api/v1
- **API Docs:** http://localhost:8010/docs
- **Adminer (DB UI):** http://localhost:8090
  - System: PostgreSQL
  - Server: uns-kobetsu-db
  - Username: kobetsu_admin
  - Password: (see .env)
  - Database: kobetsu_db

## Architecture

### Backend Architecture

The backend follows a layered architecture pattern:

```
backend/app/
├── api/v1/           # API endpoints (routes)
│   ├── auth.py       # JWT authentication
│   ├── kobetsu.py    # Main contract endpoints
│   ├── factories.py  # Factory/client company management
│   ├── employees.py  # Employee management
│   ├── imports.py    # Data import functionality
│   └── documents.py  # Document generation
├── models/           # SQLAlchemy ORM models
│   ├── kobetsu_keiyakusho.py  # Main contract model (16 legal fields)
│   ├── factory.py              # Factory model
│   ├── employee.py             # Employee model
│   └── dispatch_assignment.py  # Assignment linking
├── schemas/          # Pydantic schemas (request/response validation)
│   ├── kobetsu_keiyakusho.py
│   └── factory.py
├── services/         # Business logic layer
│   ├── kobetsu_service.py         # Contract CRUD + validation
│   ├── kobetsu_pdf_service.py     # PDF/DOCX generation
│   ├── contract_logic_service.py  # Legal compliance checks
│   └── import_service.py          # Excel/CSV imports
├── core/            # Core utilities
│   ├── config.py    # Settings from environment
│   ├── database.py  # DB session management
│   └── security.py  # JWT, password hashing
└── main.py         # FastAPI app initialization
```

**Key Patterns:**
- **Service Layer:** Business logic lives in `services/`, not in API routes
- **Dependency Injection:** Database sessions injected via FastAPI's `Depends()`
- **Validation:** Pydantic schemas validate all inputs/outputs
- **ORM:** SQLAlchemy models map to PostgreSQL tables

### Frontend Architecture

Next.js 15 App Router with component-based structure:

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home/dashboard
│   ├── kobetsu/           # Contract management routes
│   │   ├── page.tsx       # List all contracts
│   │   ├── create/        # Create new contract
│   │   └── [id]/          # View/edit contract (dynamic route)
│   ├── assign/            # Employee assignment
│   ├── import/            # Data import
│   └── providers.tsx      # React Query provider
├── components/
│   ├── common/            # Shared components (Header, etc.)
│   ├── kobetsu/           # Contract-specific components
│   │   ├── KobetsuForm.tsx    # Contract form
│   │   ├── KobetsuTable.tsx   # Contract list table
│   │   └── KobetsuStats.tsx   # Statistics dashboard
│   └── factory/           # Factory/company components
├── lib/
│   └── api.ts             # Axios client with JWT interceptors
├── types/
│   └── index.ts           # TypeScript type definitions
└── styles/
    └── globals.css        # Tailwind CSS
```

**Key Patterns:**
- **App Router:** File-based routing with `app/` directory
- **Server State:** React Query (`@tanstack/react-query`) manages API data
- **Client State:** Zustand for lightweight client-side state
- **API Client:** Centralized Axios instance in `lib/api.ts` with automatic JWT injection
- **Type Safety:** TypeScript types mirror backend Pydantic schemas

### Database Schema

**Core Model: `kobetsu_keiyakusho`**

The main table stores individual dispatch contracts with 16 legally required fields (労働者派遣法第26条):

- **Relations:** Links to `factories` (dispatch destination) and `employees` (via `kobetsu_employees` join table)
- **Contract Number:** Auto-generated format `KOB-YYYYMM-XXXX`
- **Work Details:** Job content, responsibility level, work location
- **Schedule:** Work days (JSONB array), start/end times, break duration
- **Overtime:** Max hours per day/month
- **Legal Fields:** Supervisor info, safety measures, complaint handling, etc.

**Key Relationships:**
```
factories (派遣先) ──< kobetsu_keiyakusho >── kobetsu_employees >─ employees (派遣社員)
                         │
                         └─── dispatch_assignments (optional link)
```

### API Structure

All endpoints are versioned under `/api/v1`:

**Authentication:**
- `POST /auth/login` - Get JWT tokens
- `POST /auth/refresh` - Refresh access token

**Kobetsu Keiyakusho (Main):**
- `GET /kobetsu` - List contracts (with filters: factory_id, status, date_range, expiring_within_days)
- `POST /kobetsu` - Create new contract
- `GET /kobetsu/{id}` - Get contract details
- `PUT /kobetsu/{id}` - Update contract
- `DELETE /kobetsu/{id}` - Delete contract
- `GET /kobetsu/{id}/pdf` - Generate PDF
- `GET /kobetsu/{id}/employees` - Get linked employees
- `POST /kobetsu/{id}/renew` - Renew contract
- `GET /kobetsu/stats` - Dashboard statistics

**Supporting Endpoints:**
- `/factories` - Factory/client company management
- `/employees` - Employee management
- `/import` - Bulk data import
- `/documents` - Document generation

## Key Services

### `KobetsuService` (backend/app/services/kobetsu_service.py)

Main business logic for contract management:
- `generate_contract_number()` - Creates unique contract IDs (KOB-YYYYMM-XXXX format)
- `create()` - Validates and creates contracts with employee associations
- `get_stats()` - Calculates dashboard metrics (active contracts, expiring soon, etc.)
- `list_contracts()` - Queries with filters, pagination, and search

### `KobetsuPDFService` (backend/app/services/kobetsu_pdf_service.py)

Generates legally compliant contract documents:
- Uses `python-docx` to create DOCX templates
- Includes all 16 required fields from 労働者派遣法第26条
- Converts to PDF via external library
- Stores generated files in `outputs/` volume

### API Client (frontend/lib/api.ts)

Centralized Axios client with:
- **JWT Interceptors:** Automatically adds `Authorization: Bearer <token>` to all requests
- **Token Refresh:** Auto-refreshes expired tokens
- **Error Handling:** Unified error responses
- **Type Safety:** Fully typed API calls matching backend schemas

## Important Conventions

### Backend

1. **Service Layer First:** Always implement business logic in `services/` before creating API endpoints
2. **Schema Validation:** Use Pydantic schemas for all API inputs/outputs (in `schemas/`)
3. **Database Sessions:** Use `Depends(get_db)` for dependency injection, never create sessions manually
4. **Error Handling:** Raise `HTTPException` with appropriate status codes (400, 404, 500)
5. **Testing:** Write pytest tests in `tests/` matching the module structure

### Frontend

1. **React Query:** Use for all server state (API data). Never store API responses in Zustand
2. **Type Everything:** All props, state, and API responses must have TypeScript types
3. **API Calls:** Always use the centralized `api.ts` client, never raw `fetch()` or `axios`
4. **Component Structure:** Keep components small and focused. Extract reusable logic to custom hooks
5. **Styling:** Use Tailwind CSS utility classes. Avoid custom CSS unless necessary

### Database Migrations

1. **Auto-generate:** Use `alembic revision --autogenerate` for model changes
2. **Review Generated:** Always review and edit auto-generated migrations before applying
3. **Test Migrations:** Test both upgrade and downgrade paths
4. **Data Migrations:** For data changes, write manual migrations (not auto-generated)
5. **Naming:** Use descriptive names: `add_kobetsu_keiyakusho_table`, not `update_schema`

## Configuration

**Environment Variables** (see .env.example):
- Database credentials and connection strings
- JWT secret key (MUST change in production)
- CORS origins
- Company information (UNS Kikaku details for contract generation)
- File upload limits

**Critical Security Notes:**
- Never commit `.env` to version control
- Generate strong `SECRET_KEY` with `openssl rand -hex 32`
- Change default `POSTGRES_PASSWORD` in production
- Set `DEBUG=false` in production
- Configure proper CORS origins

## Testing

### Backend Tests

Run with pytest:
```bash
docker exec -it uns-kobetsu-backend pytest -v
```

Tests are in `backend/tests/`:
- `test_kobetsu_api.py` - API endpoint tests
- `test_schemas.py` - Pydantic schema validation tests
- `conftest.py` - Pytest fixtures (test DB, test client, etc.)

### Frontend Tests

Run with Vitest:
```bash
docker exec -it uns-kobetsu-frontend npm test
```

Tests are in `frontend/__tests__/`:
- Component tests using @testing-library/react
- API client tests
- Setup in `setup.ts`

## Common Issues

**Database Connection Errors:**
- Ensure PostgreSQL container is healthy: `docker compose ps`
- Check DATABASE_URL in .env matches container name `uns-kobetsu-db`
- Verify migrations are applied: `docker exec -it uns-kobetsu-backend alembic current`

**Frontend Can't Reach Backend:**
- Check NEXT_PUBLIC_API_URL in .env points to correct backend port (8010)
- Verify CORS_ORIGINS in backend includes frontend URL
- Check network connectivity: `docker exec -it uns-kobetsu-frontend ping uns-kobetsu-backend`

**Port Conflicts:**
- This project uses custom ports to avoid conflicts (8010, 3010, 5442, 6389, 8090)
- If ports are still occupied, modify them in .env and restart containers

**JWT Token Errors:**
- Verify SECRET_KEY matches between sessions
- Check token expiration (default 30 minutes)
- Clear localStorage in browser and re-login

## Integration with UNS-ClaudeJP

This module can be integrated into the larger UNS-ClaudeJP system:

1. **Database:** Add Alembic migration to existing UNS-ClaudeJP database
2. **Backend:** Copy API routes, models, schemas, and services to main backend
3. **Frontend:** Copy app routes and components to main frontend
4. **Shared Data:** Reuses existing `factories` and `employees` tables

See README.md for detailed integration steps.

## Excel System Migration

### Background

This project replaces an existing Excel-based system (`個別契約書TEXPERT2025.7.xlsx`) that has:
- **18 interconnected sheets** with 11,000+ formulas
- **1,028 employees** in DBGenzai table
- **111 factory configurations** in TBKaisha table
- **Complex filtering logic** using XLOOKUP, COUNTIF, UNIQUE, FILTER
- **Automated document generation** for 9 different document types

### Key Excel Architecture

The Excel system uses a 3-layer architecture:

```
1. Data Layer: DBGenzai (employees) + TBKaisha (factories)
2. Filter Layer: Filtro + Trasformacion (5,500+ formulas)
3. Control Layer: 個別契約書X (central control with dropdown selections)
4. Output Layer: 9 document sheets (通知書, DAICHO, 契約書, etc.)
```

**Critical Excel Fields:**
- **Control Cells (個別契約書X):**
  - AD1: 派遣先 (Company name)
  - AD2: 工場名 (Factory name)
  - AD3: 配属先 (Department)
  - AD4: ライン (Production line) - **KEY IDENTIFIER**
  - H16: HakenkikanS (Start date)
  - P16: HakenKikanE (End date)

**Unique Identifier in Excel:**
The combination `派遣先 + 工場名 + 配属先 + ライン` acts as the unique key for factory configurations.

### Import from Excel

Import existing Excel data:

```bash
# Import employees only
docker exec -it uns-kobetsu-backend python scripts/import_from_excel.py \
  --file "/path/to/個別契約書TEXPERT2025.7.xlsx" \
  --mode employees

# Import factories only
docker exec -it uns-kobetsu-backend python scripts/import_from_excel.py \
  --file "/path/to/個別契約書TEXPERT2025.7.xlsx" \
  --mode factories

# Import everything
docker exec -it uns-kobetsu-backend python scripts/import_from_excel.py \
  --file "/path/to/個別契約書TEXPERT2025.7.xlsx" \
  --mode all
```

**Excel Column Mappings:**

DBGenzai → employees:
- 社員№ (col 1) → employee_number
- 氏名 (col 7) → full_name
- カナ (col 8) → katakana_name
- 性別 (col 9) → gender
- 国籍 (col 10) → nationality
- 生年月日 (col 11) → date_of_birth
- 現在 (col 0) → status ("退社" = resigned, else active)

TBKaisha → factories:
- 派遣先 (col 0) → company_name
- 工場名 (col 6) → factory_name
- 配属先 (col 9) → department
- ライン (col 12+) → line (KEY field)
- 派遣先住所 (col 1) → company_address
- 仕事内容 → work_content

### Documents to Migrate

The web system should eventually generate all documents from the Excel system:

**Priority 1 (Core):**
- ✅ 個別契約書 (Individual Contract) - Already implemented
- 🚧 通知書 (Notification to client company)
- 🚧 DAICHO (Individual registry)

**Priority 2 (Legal compliance):**
- 派遣元管理台帳 (Dispatch origin registry)
- 就業条件明示書 (Employment conditions document)
- 雇入れ時の待遇情報 (Treatment information at hiring)

**Priority 3 (Operations):**
- タイムシート (Timesheet)
- 就業状況報告書 (Employment status report)
- 契約書 (Employment contract)

See [EXCEL_TO_WEB_MIGRATION.md](EXCEL_TO_WEB_MIGRATION.md) for detailed migration strategy.
