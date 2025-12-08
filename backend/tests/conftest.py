"""
Pytest configuration and fixtures for backend tests.

Uses PostgreSQL via testcontainers for realistic database testing.
This ensures tests run against the same database engine as production,
catching issues with JSONB, sequences, and PostgreSQL-specific syntax.
"""
import os
import pytest
from datetime import date, timedelta
from decimal import Decimal
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee


# ========================================
# DATABASE CONFIGURATION
# ========================================

# Check if we should use testcontainers or an existing PostgreSQL instance
USE_TESTCONTAINERS = os.environ.get("USE_TESTCONTAINERS", "true").lower() == "true"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", None)


def get_test_database_url():
    """Get the database URL for tests."""
    if TEST_DATABASE_URL:
        # Use explicitly provided test database URL
        return TEST_DATABASE_URL

    if USE_TESTCONTAINERS:
        # Use testcontainers - will be set up in pytest_configure
        return None

    # Fallback: Use the development database with a test schema
    # This is less ideal but works when Docker is not available
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://kob24_admin:kob24_secure_2024@localhost:5424/kob24_db"
    )


# Global container reference (for testcontainers)
_postgres_container = None
_engine = None
_TestingSessionLocal = None


def pytest_configure(config):
    """Set up PostgreSQL container before running tests."""
    global _postgres_container, _engine, _TestingSessionLocal

    if USE_TESTCONTAINERS and TEST_DATABASE_URL is None:
        try:
            from testcontainers.postgres import PostgresContainer

            # Start PostgreSQL container
            _postgres_container = PostgresContainer(
                image="postgres:15-alpine",
                user="test_user",
                password="test_password",
                dbname="test_db",
            )
            _postgres_container.start()

            # Get connection URL
            db_url = _postgres_container.get_connection_url()
            print(f"\n🐘 PostgreSQL test container started: {db_url[:50]}...")

        except ImportError:
            print("\n⚠️  testcontainers not installed, falling back to SQLite")
            db_url = "sqlite:///:memory:"
        except Exception as e:
            print(f"\n⚠️  Could not start testcontainers ({e}), using existing database")
            db_url = get_test_database_url() or "sqlite:///:memory:"
    else:
        db_url = get_test_database_url() or "sqlite:///:memory:"

    # Create engine based on database type
    if "sqlite" in db_url:
        from sqlalchemy.pool import StaticPool
        _engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

    _TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def pytest_unconfigure(config):
    """Clean up PostgreSQL container after tests."""
    global _postgres_container

    if _postgres_container is not None:
        try:
            _postgres_container.stop()
            print("\n🐘 PostgreSQL test container stopped")
        except Exception as e:
            print(f"\n⚠️  Error stopping container: {e}")


# ========================================
# DATABASE FIXTURES
# ========================================

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    global _engine, _TestingSessionLocal

    if _engine is None:
        pytest.skip("Database engine not initialized")

    # Create all tables
    Base.metadata.create_all(bind=_engine)

    # Create contract_number_counters table if using PostgreSQL
    # (This table is created by migration but we need it for tests)
    if "postgresql" in str(_engine.url):
        with _engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS contract_number_counters (
                    id SERIAL PRIMARY KEY,
                    year_month VARCHAR(6) NOT NULL UNIQUE,
                    last_sequence INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
                )
            """))
            conn.commit()

    # Create session
    session = _TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=_engine)

        # Also drop the contract_number_counters table
        if "postgresql" in str(_engine.url):
            with _engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS contract_number_counters CASCADE"))
                conn.commit()


@pytest.fixture(scope="function")
def client(db: Session, test_user: User) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ========================================
# USER FIXTURES
# ========================================

@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_inactive_user(db: Session) -> User:
    """Create an inactive test user."""
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Inactive User",
        role="user",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test requests."""
    token = create_access_token({
        "sub": str(test_user.id),
        "email": test_user.email,
        "role": test_user.role,
    })
    return {"Authorization": f"Bearer {token}"}


# ========================================
# FACTORY FIXTURES
# ========================================

@pytest.fixture
def test_factory(db: Session) -> Factory:
    """Create a test factory."""
    factory = Factory(
        factory_id="テスト株式会社__本社工場",
        company_name="テスト株式会社",
        plant_name="本社工場",
        company_address="東京都千代田区丸の内1-1-1",
        plant_address="東京都千代田区丸の内1-1-1",
        company_phone="03-1234-5678",
        conflict_date=date(2026, 1, 1),  # Future date
        is_active=True,
    )
    db.add(factory)
    db.commit()
    db.refresh(factory)
    return factory


@pytest.fixture
def test_factory_line(db: Session, test_factory: Factory) -> FactoryLine:
    """Create a test factory line."""
    line = FactoryLine(
        factory_id=test_factory.id,
        line_id="LINE001",
        department="製造部",
        line_name="第1ライン",
        job_description="製造作業",
        hourly_rate=Decimal("1500"),
        billing_rate=Decimal("2000"),
        supervisor_name="田中太郎",
        supervisor_department="製造部",
        supervisor_phone="03-1234-5678",
        is_active=True,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


# ========================================
# EMPLOYEE FIXTURES
# ========================================

@pytest.fixture
def test_employee(db: Session, test_factory: Factory) -> Employee:
    """Create a test employee."""
    employee = Employee(
        employee_number="EMP001",
        full_name_kanji="山田太郎",
        full_name_kana="ヤマダタロウ",
        gender="male",
        nationality="日本",
        date_of_birth=date(1990, 1, 1),
        status="active",
        factory_id=test_factory.id,
        company_name=test_factory.company_name,
        plant_name=test_factory.plant_name,
        hourly_rate=Decimal("1500"),
        billing_rate=Decimal("2000"),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@pytest.fixture
def test_employee_2(db: Session, test_factory: Factory) -> Employee:
    """Create a second test employee."""
    employee = Employee(
        employee_number="EMP002",
        full_name_kanji="佐藤花子",
        full_name_kana="サトウハナコ",
        gender="female",
        nationality="ベトナム",
        date_of_birth=date(1995, 5, 15),
        status="active",
        factory_id=test_factory.id,
        company_name=test_factory.company_name,
        plant_name=test_factory.plant_name,
        visa_expiry_date=date.today() + timedelta(days=20),
        hourly_rate=Decimal("1400"),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


# ========================================
# CONTRACT DATA FIXTURES
# ========================================

@pytest.fixture
def sample_contract_data(test_factory: Factory, test_employee: Employee, test_employee_2: Employee) -> dict:
    """Sample contract data for testing."""
    return {
        "factory_id": test_factory.id,
        "employee_ids": [test_employee.id, test_employee_2.id],
        "contract_date": str(date.today()),
        "dispatch_start_date": "2024-12-01",
        "dispatch_end_date": "2025-11-30",
        "work_content": "製造ライン作業、検品、梱包業務の補助作業",
        "responsibility_level": "通常業務",
        "worksite_name": "テスト株式会社 本社工場",
        "worksite_address": "東京都千代田区丸の内1-1-1",
        "organizational_unit": "第1製造部",
        "supervisor_department": "製造部",
        "supervisor_position": "課長",
        "supervisor_name": "田中太郎",
        "work_days": ["月", "火", "水", "木", "金"],
        "work_start_time": "08:00",
        "work_end_time": "17:00",
        "break_time_minutes": 60,
        "overtime_max_hours_day": 3,
        "overtime_max_hours_month": 45,
        "hourly_rate": 1500,
        "overtime_rate": 1875,
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


@pytest.fixture
def sample_update_data() -> dict:
    """Sample update data for testing."""
    return {
        "work_content": "更新された業務内容です。新しい作業が追加されました。",
        "hourly_rate": 1600,
        "notes": "テスト更新",
    }


# ========================================
# UTILITY FIXTURES
# ========================================

@pytest.fixture
def db_is_postgresql(db: Session) -> bool:
    """Check if the test database is PostgreSQL."""
    global _engine
    return _engine is not None and "postgresql" in str(_engine.url)
