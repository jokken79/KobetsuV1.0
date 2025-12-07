"""
Statistics Endpoints

Provides system and application statistics.
"""
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, Request

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.models.employee import Employee
from app.models.factory import Factory
from app.models.company import Company
from app.models.plant import Plant
from app.services.compliance_checker_service import ComplianceCheckerService
from app.services.alert_manager_service import AlertManagerService

router = APIRouter()


@router.get("/system")
@limiter.limit("100 per minute")
async def system_stats(request: Request):
    """Get system resource statistics."""

    # CPU stats
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()

    # Memory stats
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk stats
    disk = psutil.disk_usage('/')

    # Network stats
    net_io = psutil.net_io_counters()

    # Process stats
    process = psutil.Process()
    process_create_time = datetime.fromtimestamp(process.create_time())
    uptime = datetime.now() - process_create_time

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count,
            "frequency_mhz": cpu_freq.current if cpu_freq else None,
            "load_average": psutil.getloadavg()
        },
        "memory": {
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "available_gb": round(memory.available / (1024 ** 3), 2),
            "used_gb": round(memory.used / (1024 ** 3), 2),
            "percent": memory.percent,
            "swap_percent": swap.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent
        },
        "network": {
            "bytes_sent_gb": round(net_io.bytes_sent / (1024 ** 3), 2),
            "bytes_recv_gb": round(net_io.bytes_recv / (1024 ** 3), 2),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        },
        "process": {
            "pid": process.pid,
            "memory_mb": round(process.memory_info().rss / (1024 ** 2), 2),
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "uptime_hours": round(uptime.total_seconds() / 3600, 2)
        }
    }


@router.get("/app")
@limiter.limit("100 per minute")
async def app_stats(
    request: Request,
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to include in statistics")
):
    """Get application statistics."""

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    try:
        # Count total records
        total_contracts = db.query(func.count(KobetsuKeiyakusho.id)).scalar() or 0
        total_employees = db.query(func.count(Employee.id)).scalar() or 0
        total_factories = db.query(func.count(Factory.id)).scalar() or 0
        total_companies = db.query(func.count(Company.id)).scalar() or 0
        total_plants = db.query(func.count(Plant.id)).scalar() or 0

        # Active contracts (current date between start and end)
        active_contracts = db.query(func.count(KobetsuKeiyakusho.id)).filter(
            KobetsuKeiyakusho.contract_start <= datetime.now().date(),
            KobetsuKeiyakusho.contract_end >= datetime.now().date()
        ).scalar() or 0

        # Expiring soon (within 30 days)
        expiring_date = datetime.now().date() + timedelta(days=30)
        expiring_contracts = db.query(func.count(KobetsuKeiyakusho.id)).filter(
            KobetsuKeiyakusho.contract_end <= expiring_date,
            KobetsuKeiyakusho.contract_end >= datetime.now().date()
        ).scalar() or 0

        # New contracts in period
        new_contracts = db.query(func.count(KobetsuKeiyakusho.id)).filter(
            KobetsuKeiyakusho.created_at >= start_date
        ).scalar() or 0

        # Contracts by status
        status_counts = db.query(
            KobetsuKeiyakusho.status,
            func.count(KobetsuKeiyakusho.id)
        ).group_by(KobetsuKeiyakusho.status).all()

        status_dict = {status: count for status, count in status_counts}

        # Top factories by contract count
        top_factories = db.query(
            Factory.factory_name,
            func.count(KobetsuKeiyakusho.id).label('contract_count')
        ).join(
            KobetsuKeiyakusho,
            Factory.id == KobetsuKeiyakusho.factory_id
        ).group_by(
            Factory.factory_name
        ).order_by(
            func.count(KobetsuKeiyakusho.id).desc()
        ).limit(5).all()

        # Calculate growth rate
        prev_period_start = start_date - timedelta(days=days)
        prev_period_contracts = db.query(func.count(KobetsuKeiyakusho.id)).filter(
            KobetsuKeiyakusho.created_at >= prev_period_start,
            KobetsuKeiyakusho.created_at < start_date
        ).scalar() or 0

        if prev_period_contracts > 0:
            growth_rate = ((new_contracts - prev_period_contracts) / prev_period_contracts) * 100
        else:
            growth_rate = 100 if new_contracts > 0 else 0

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period_days": days,
            "totals": {
                "contracts": total_contracts,
                "employees": total_employees,
                "factories": total_factories,
                "companies": total_companies,
                "plants": total_plants
            },
            "contracts": {
                "active": active_contracts,
                "expiring_soon": expiring_contracts,
                "new_in_period": new_contracts,
                "by_status": status_dict,
                "growth_rate_percent": round(growth_rate, 2)
            },
            "top_factories": [
                {"name": name, "contracts": count}
                for name, count in top_factories
            ]
        }
    except Exception as e:
        # Handle case where tables don't exist yet
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Database not initialized",
            "details": str(e)
        }


@router.get("/database")
@limiter.limit("50 per minute")
async def database_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get detailed database statistics."""

    try:
        # Database size
        db_size_result = db.execute(text("""
            SELECT
                pg_database_size(current_database()) as total_size,
                pg_size_pretty(pg_database_size(current_database())) as total_size_pretty
        """)).fetchone()

        # Table sizes
        table_sizes = db.execute(text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """)).fetchall()

        # Connection stats
        connection_stats = db.execute(text("""
            SELECT
                state,
                COUNT(*) as count
            FROM pg_stat_activity
            WHERE datname = current_database()
            GROUP BY state
        """)).fetchall()

        # Query stats (if pg_stat_statements is available)
        try:
            slow_queries = db.execute(text("""
                SELECT
                    query,
                    calls,
                    total_time,
                    mean_time,
                    max_time
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat_statements%'
                ORDER BY mean_time DESC
                LIMIT 5
            """)).fetchall()

            query_stats = [
                {
                    "query": q[0][:100] + "..." if len(q[0]) > 100 else q[0],
                    "calls": q[1],
                    "total_time_ms": round(q[2], 2),
                    "mean_time_ms": round(q[3], 2),
                    "max_time_ms": round(q[4], 2)
                }
                for q in slow_queries
            ]
        except:
            query_stats = "pg_stat_statements not available"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "size_bytes": db_size_result[0] if db_size_result else 0,
                "size_pretty": db_size_result[1] if db_size_result else "0 bytes"
            },
            "tables": [
                {
                    "schema": t[0],
                    "name": t[1],
                    "size": t[2],
                    "size_bytes": t[3]
                }
                for t in table_sizes
            ],
            "connections": {
                state if state else "idle": count
                for state, count in connection_stats
            },
            "slow_queries": query_stats
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Failed to retrieve database statistics",
            "details": str(e)
        }


@router.get("/usage")
@limiter.limit("100 per minute")
async def usage_stats(
    request: Request,
    db: Session = Depends(get_db),
    days: int = Query(7, description="Number of days to analyze")
):
    """Get usage statistics and trends."""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    try:
        # Daily contract creation trend
        daily_contracts = db.execute(text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM kobetsu_keiyakusho
            WHERE created_at >= :start_date
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """), {"start_date": start_date}).fetchall()

        # User activity (if we have audit logs)
        # For now, we'll use contract modifications as a proxy
        daily_activity = db.execute(text("""
            SELECT
                DATE(updated_at) as date,
                COUNT(*) as modifications
            FROM kobetsu_keiyakusho
            WHERE updated_at >= :start_date
                AND updated_at != created_at
            GROUP BY DATE(updated_at)
            ORDER BY date DESC
        """), {"start_date": start_date}).fetchall()

        # Most active factories
        active_factories = db.execute(text("""
            SELECT
                f.factory_name,
                COUNT(k.id) as contract_count,
                MAX(k.created_at) as last_contract
            FROM factories f
            JOIN kobetsu_keiyakusho k ON f.id = k.factory_id
            WHERE k.created_at >= :start_date
            GROUP BY f.factory_name
            ORDER BY contract_count DESC
            LIMIT 10
        """), {"start_date": start_date}).fetchall()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "daily_contracts": [
                {
                    "date": str(date),
                    "count": count
                }
                for date, count in daily_contracts
            ],
            "daily_activity": [
                {
                    "date": str(date),
                    "modifications": mods
                }
                for date, mods in daily_activity
            ],
            "active_factories": [
                {
                    "name": name,
                    "contracts": count,
                    "last_contract": last.isoformat() if last else None
                }
                for name, count, last in active_factories
            ]
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Failed to retrieve usage statistics",
            "details": str(e)
        }


@router.get("/compliance")
@limiter.limit("50 per minute")
async def compliance_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get compliance statistics for the dashboard.

    Returns:
    - compliance_score: Overall system compliance (0-100)
    - contract_compliance: Contract-specific compliance
    - alert_counts: Alert counts by priority
    - top_issues: Most urgent compliance issues
    """
    try:
        # Get compliance summary
        checker = ComplianceCheckerService(db)
        compliance_summary = checker.get_compliance_summary()

        # Get alert summary
        alert_manager = AlertManagerService(db)
        daily_summary = alert_manager.get_daily_summary()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "compliance": {
                "score": compliance_summary.get("quick_score", 0),
                "status": compliance_summary.get("status", "UNKNOWN"),
                "active_contracts": compliance_summary.get("active_contracts", 0),
                "expired_but_active": compliance_summary.get("expired_but_active", 0),
                "factories_missing_info": compliance_summary.get("factories_missing_info", 0)
            },
            "alerts": {
                "critical": daily_summary.get("counts", {}).get("critical", 0),
                "high": daily_summary.get("counts", {}).get("high", 0),
                "medium": daily_summary.get("counts", {}).get("medium", 0),
                "total_action_required": daily_summary.get("counts", {}).get("total_action_required", 0)
            },
            "highlights": daily_summary.get("highlights", {}),
            "top_priorities": daily_summary.get("top_priorities", [])[:5]
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Failed to retrieve compliance statistics",
            "details": str(e)
        }


@router.get("/dashboard")
@limiter.limit("100 per minute")
async def dashboard_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get all statistics for the main dashboard in one call.

    Combines: app stats, compliance stats, and alerts.
    Optimized to reduce multiple API calls from frontend.
    """
    try:
        today = datetime.now().date()

        # Basic counts
        total_contracts = db.query(func.count(KobetsuKeiyakusho.id)).scalar() or 0
        active_contracts = db.query(func.count(KobetsuKeiyakusho.id)).filter(
            KobetsuKeiyakusho.status == 'active'
        ).scalar() or 0
        total_employees = db.query(func.count(Employee.id)).filter(
            Employee.status == 'active'
        ).scalar() or 0
        total_factories = db.query(func.count(Factory.id)).filter(
            Factory.is_active == True
        ).scalar() or 0

        # Expiring soon (7 days)
        expiring_week = db.query(func.count(KobetsuKeiyakusho.id)).filter(
            KobetsuKeiyakusho.dispatch_end_date.between(
                today,
                today + timedelta(days=7)
            ),
            KobetsuKeiyakusho.status == 'active'
        ).scalar() or 0

        # Expired but still active
        expired_active = db.query(func.count(KobetsuKeiyakusho.id)).filter(
            KobetsuKeiyakusho.dispatch_end_date < today,
            KobetsuKeiyakusho.status == 'active'
        ).scalar() or 0

        # Compliance summary
        checker = ComplianceCheckerService(db)
        compliance = checker.get_compliance_summary()

        # Alert summary
        alert_manager = AlertManagerService(db)
        alerts = alert_manager.get_daily_summary()

        # Status breakdown
        status_counts = db.query(
            KobetsuKeiyakusho.status,
            func.count(KobetsuKeiyakusho.id)
        ).group_by(KobetsuKeiyakusho.status).all()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overview": {
                "total_contracts": total_contracts,
                "active_contracts": active_contracts,
                "total_employees": total_employees,
                "total_factories": total_factories
            },
            "attention_required": {
                "expiring_this_week": expiring_week,
                "expired_still_active": expired_active,
                "critical_alerts": alerts.get("counts", {}).get("critical", 0),
                "high_alerts": alerts.get("counts", {}).get("high", 0)
            },
            "compliance": {
                "score": compliance.get("quick_score", 0),
                "status": compliance.get("status", "UNKNOWN")
            },
            "contracts_by_status": {
                status: count for status, count in status_counts
            },
            "top_priorities": alerts.get("top_priorities", [])[:5]
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Failed to retrieve dashboard statistics",
            "details": str(e)
        }