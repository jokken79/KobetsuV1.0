"""
Database configuration and session management.
Provides SQLAlchemy engine, session factory, and dependency injection.
"""
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from .config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.get_database_url(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Event listener for connection setup (PostgreSQL specific)
@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    """Set default search path for PostgreSQL connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET timezone = 'Asia/Tokyo'")
    cursor.close()


def init_db() -> None:
    """
    Initialize database tables.
    Should be called on application startup in development.
    In production, use Alembic migrations.
    """
    # Import all models to ensure they are registered with Base
    # This ensures all relationships and foreign keys are properly resolved
    from app.models import (  # noqa: F401
        User,
        Employee,
        Factory,
        FactoryLine,
        KobetsuKeiyakusho,
        KobetsuEmployee,
        DispatchAssignment,
    )

    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False
