"""
Health Check Endpoints

Provides detailed health information about the application and its dependencies.
"""
import os
import psutil
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter

router = APIRouter()


def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connection status."""
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()

        # Get Redis info
        info = r.info()
        return {
            "status": "connected",
            "version": info.get("redis_version", "unknown"),
            "used_memory": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_days": info.get("uptime_in_days", 0)
        }
    except redis.ConnectionError:
        return {
            "status": "disconnected",
            "error": "Cannot connect to Redis server"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def check_database_connection(db: Session) -> Dict[str, Any]:
    """Check database connection and get statistics."""
    try:
        # Test connection
        result = db.execute(text("SELECT 1")).fetchone()

        # Get database statistics
        stats = {}

        # Count tables
        tables_result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public'
        """)).fetchone()
        stats["tables_count"] = tables_result[0] if tables_result else 0

        # Get database size
        size_result = db.execute(text("""
            SELECT pg_database_size(current_database())
        """)).fetchone()
        if size_result:
            size_mb = size_result[0] / (1024 * 1024)
            stats["size_mb"] = round(size_mb, 2)

        # Count records in main tables
        try:
            contracts_count = db.execute(text("SELECT COUNT(*) FROM kobetsu_keiyakusho")).fetchone()[0]
            employees_count = db.execute(text("SELECT COUNT(*) FROM employees")).fetchone()[0]
            factories_count = db.execute(text("SELECT COUNT(*) FROM factories")).fetchone()[0]

            stats["records"] = {
                "contracts": contracts_count,
                "employees": employees_count,
                "factories": factories_count
            }
        except:
            stats["records"] = "tables not yet created"

        return {
            "status": "connected",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_system_info() -> Dict[str, Any]:
    """Get system resource information."""
    try:
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Memory information
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = round(memory.used / (1024 ** 3), 2)
        memory_total_gb = round(memory.total / (1024 ** 3), 2)

        # Disk information
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)

        # Process information
        process = psutil.Process(os.getpid())
        process_memory_mb = round(process.memory_info().rss / (1024 ** 2), 2)

        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": cpu_count
            },
            "memory": {
                "percent": memory_percent,
                "used_gb": memory_used_gb,
                "total_gb": memory_total_gb
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": disk_used_gb,
                "total_gb": disk_total_gb
            },
            "process": {
                "memory_mb": process_memory_mb,
                "pid": process.pid
            }
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/basic")
@limiter.limit("1000 per minute")
async def health_basic(request: Request):
    """Basic health check for load balancers and monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/detailed")
@limiter.limit("100 per minute")
async def health_detailed(
    request: Request,
    db: Session = Depends(get_db)
):
    """Detailed health check with dependency status."""

    # Check all dependencies
    database_info = check_database_connection(db)
    redis_info = check_redis_connection()
    system_info = get_system_info()

    # Determine overall health status
    overall_status = "healthy"
    if database_info["status"] != "connected":
        overall_status = "degraded"
    if redis_info["status"] != "connected":
        overall_status = "degraded" if overall_status == "healthy" else overall_status

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": "production" if not settings.DEBUG else "development",
        "dependencies": {
            "database": database_info,
            "redis": redis_info
        },
        "system": system_info
    }


@router.get("/ready")
@limiter.limit("1000 per minute")
async def readiness_check(
    request: Request,
    db: Session = Depends(get_db)
):
    """Readiness check for container orchestration."""

    # Check critical dependencies
    try:
        # Database must be accessible
        db.execute(text("SELECT 1")).fetchone()
        db_ready = True
    except:
        db_ready = False

    # Redis is optional but we check it
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_ready = True
    except:
        redis_ready = False

    # System is ready if database is accessible
    is_ready = db_ready

    return {
        "ready": is_ready,
        "checks": {
            "database": db_ready,
            "redis": redis_ready
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live")
@limiter.limit("1000 per minute")
async def liveness_check(request: Request):
    """Liveness check for container orchestration."""
    # Simple check that the application is running
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }