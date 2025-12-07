"""
Compliance API Router

Endpoints for contract validation, compliance auditing, and alerts.
Integrates contract-validator, compliance-checker, and alert-manager services.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.services.contract_validator_service import ContractValidatorService
from app.services.compliance_checker_service import ComplianceCheckerService
from app.services.alert_manager_service import AlertManagerService
from app.services.sync_resolver_service import SyncResolverService, ConflictStrategy

router = APIRouter(redirect_slashes=False)


# ========================================
# CONTRACT VALIDATION ENDPOINTS
# ========================================

@router.post("/validate/contract")
async def validate_contract_data(
    data: dict,
    factory_id: Optional[int] = Query(None, description="Factory ID"),
    employee_ids: Optional[List[int]] = Query(None, description="Employee IDs"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Validate contract data before creation.

    Checks all 16 legally required fields according to 労働者派遣法第26条.

    Returns validation result with:
    - is_valid: Whether contract passes validation
    - errors: List of validation errors (must fix)
    - warnings: List of warnings (recommended fixes)
    - compliance_score: 0-100 score
    """
    validator = ContractValidatorService(db)
    result = validator.validate_contract_data(
        data=data,
        factory_id=factory_id,
        employee_ids=employee_ids
    )
    return result.to_dict()


@router.get("/validate/contract/{contract_id}")
async def validate_existing_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Validate an existing contract.

    Returns detailed validation report including:
    - All 16 required field checks
    - Date validation
    - Factory consistency
    - Employee conflicts
    """
    validator = ContractValidatorService(db)
    result = validator.validate_existing_contract(contract_id)
    return result.to_dict()


@router.get("/validate/contract/{contract_id}/summary")
async def get_contract_validation_summary(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get human-readable validation summary for a contract.
    """
    validator = ContractValidatorService(db)
    return validator.get_validation_summary(contract_id)


# ========================================
# COMPLIANCE AUDIT ENDPOINTS
# ========================================

@router.get("/compliance/summary")
async def get_compliance_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get quick compliance summary without full audit.

    Returns:
    - quick_score: Estimated compliance score
    - active_contracts: Count of active contracts
    - expired_but_active: Count of expired contracts still marked active
    - factories_missing_info: Count of incomplete factories
    - status: "COMPLIANT" or "ISSUES_FOUND"
    """
    checker = ComplianceCheckerService(db)
    return checker.get_compliance_summary()


@router.post("/compliance/audit")
async def run_compliance_audit(
    start_date: Optional[date] = Query(None, description="Audit period start"),
    end_date: Optional[date] = Query(None, description="Audit period end"),
    factory_id: Optional[int] = Query(None, description="Limit to specific factory"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Run full compliance audit.

    Audits:
    - All contracts for 16 required fields (労働者派遣法第26条)
    - Contract durations (3 year limit)
    - Overtime limits
    - Factory completeness
    - Employee documentation

    Returns comprehensive ComplianceReport with:
    - Overall compliance score
    - All violations by severity
    - Remediation recommendations
    """
    checker = ComplianceCheckerService(db)
    report = checker.run_full_audit(
        start_date=start_date,
        end_date=end_date,
        factory_id=factory_id
    )
    return report.to_dict()


@router.post("/compliance/audit/contracts")
async def run_contract_audit(
    status: str = Query("active", description="Contract status to audit"),
    factory_id: Optional[int] = Query(None, description="Limit to specific factory"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Run compliance audit on contracts only.
    """
    checker = ComplianceCheckerService(db)
    report = checker.audit_contracts_only(
        status=status,
        factory_id=factory_id
    )
    return report.to_dict()


# ========================================
# ALERT MANAGEMENT ENDPOINTS
# ========================================

@router.get("/alerts")
async def get_all_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all current alerts.

    Returns alerts categorized by priority:
    - critical: Immediate action required
    - high: Same day action
    - medium: Within 3 days
    - low: Within week

    Alert types include:
    - CONTRACT_EXPIRING / CONTRACT_EXPIRED
    - EMPLOYEE_UNASSIGNED
    - FACTORY_INCOMPLETE
    - CONFLICT_DATE_APPROACHING
    - VISA_EXPIRING
    """
    alert_manager = AlertManagerService(db)
    summary = alert_manager.get_all_alerts()
    return summary.to_dict()


@router.get("/alerts/daily-summary")
async def get_daily_alert_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get daily alert summary for dashboard.

    Returns:
    - counts: By priority level
    - highlights: Key metrics (expiring this week, unassigned, etc.)
    - top_priorities: Top 10 most urgent alerts
    """
    alert_manager = AlertManagerService(db)
    return alert_manager.get_daily_summary()


@router.get("/alerts/contracts/expiring")
async def get_expiring_contract_alerts(
    days: int = Query(30, ge=1, le=365, description="Days ahead to check"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get alerts for contracts expiring within specified days.
    """
    alert_manager = AlertManagerService(db)
    alerts = alert_manager.check_expiring_contracts(days_ahead=days)
    return {
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts]
    }


@router.get("/alerts/employees/unassigned")
async def get_unassigned_employee_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get alerts for active employees without current contracts.
    """
    alert_manager = AlertManagerService(db)
    alerts = alert_manager.check_unassigned_employees()
    return {
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts]
    }


@router.get("/alerts/factories/incomplete")
async def get_incomplete_factory_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get alerts for factories missing required information.
    """
    alert_manager = AlertManagerService(db)
    alerts = alert_manager.check_incomplete_factories()
    return {
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts]
    }


@router.get("/alerts/entity/{entity_type}/{entity_id}")
async def get_entity_alerts(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get alerts for a specific entity (contract, employee, or factory).
    """
    if entity_type not in ["contract", "employee", "factory"]:
        raise HTTPException(status_code=400, detail="Invalid entity type")

    alert_manager = AlertManagerService(db)
    alerts = alert_manager.get_alerts_for_entity(entity_type, entity_id)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts]
    }


# ========================================
# SYNC RESOLVER ENDPOINTS
# ========================================

@router.post("/sync/analyze/employees")
async def analyze_employee_sync(
    source_data: List[dict],
    source_type: str = Query("excel", description="Source type"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze employee sync changes before applying.

    Returns:
    - to_create: New employees to add
    - to_update: Existing employees with changes
    - conflicts: Records with conflicting values
    - db_only: Records in DB but not in source
    """
    resolver = SyncResolverService(db)
    analysis = resolver.analyze_employee_sync(source_data, source_type)
    return analysis.to_dict()


@router.post("/sync/resolve/employees")
async def resolve_employee_sync(
    analysis_data: dict,
    strategy: str = Query("source_wins", description="Conflict resolution strategy"),
    manual_decisions: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Execute employee sync with conflict resolution.

    Strategies:
    - source_wins: External source overwrites DB
    - db_wins: Keep DB values
    - newest_wins: Use most recent
    - manual: Require manual_decisions parameter
    """
    # This would need the original analysis to be passed back
    # For now, return info about the endpoint
    return {
        "message": "Use /sync/analyze/employees first, then pass analysis to this endpoint",
        "available_strategies": ["source_wins", "db_wins", "newest_wins", "manual"]
    }


@router.get("/sync/snapshots")
async def list_sync_snapshots(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List available sync snapshots for rollback.
    """
    resolver = SyncResolverService(db)
    return {
        "snapshots": resolver.list_snapshots()
    }


# ========================================
# SCHEDULED TASK ENDPOINTS (for cron)
# ========================================

@router.post("/tasks/update-expired-contracts", dependencies=[Depends(require_role("admin"))])
async def task_update_expired_contracts(
    db: Session = Depends(get_db),
):
    """
    Scheduled task: Update status of expired contracts.

    Should be called daily by cron job.
    """
    from app.services.kobetsu_service import KobetsuService
    service = KobetsuService(db)
    count = service.update_expired_contracts()

    return {
        "task": "update_expired_contracts",
        "contracts_updated": count,
        "executed_at": date.today().isoformat()
    }


@router.post("/tasks/generate-daily-alerts", dependencies=[Depends(require_role("admin"))])
async def task_generate_daily_alerts(
    db: Session = Depends(get_db),
):
    """
    Scheduled task: Generate daily alert summary.

    Should be called daily by cron job.
    Can be used to send notifications.
    """
    alert_manager = AlertManagerService(db)
    summary = alert_manager.get_daily_summary()

    return {
        "task": "generate_daily_alerts",
        "summary": summary,
        "executed_at": date.today().isoformat()
    }


@router.post("/tasks/compliance-check", dependencies=[Depends(require_role("admin"))])
async def task_compliance_check(
    db: Session = Depends(get_db),
):
    """
    Scheduled task: Run quick compliance check.

    Should be called weekly by cron job.
    """
    checker = ComplianceCheckerService(db)
    summary = checker.get_compliance_summary()

    return {
        "task": "compliance_check",
        "result": summary,
        "executed_at": date.today().isoformat()
    }
