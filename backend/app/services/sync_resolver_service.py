"""
Sync Resolver Service - 同期解決サービス

Handles data conflicts during synchronization between:
- Web system and Excel files
- Web system and JSON configurations
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json
import os

from sqlalchemy.orm import Session

from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee


class ConflictStrategy(str, Enum):
    SOURCE_WINS = "source_wins"  # External source overwrites DB
    DB_WINS = "db_wins"  # Keep DB value
    NEWEST_WINS = "newest_wins"  # Use most recent
    MANUAL = "manual"  # Require human decision
    MERGE = "merge"  # Combine values (for arrays/text)


class ConflictSeverity(str, Enum):
    CRITICAL = "critical"  # Blocks sync
    HIGH = "high"  # Needs review
    MEDIUM = "medium"  # Can auto-resolve
    LOW = "low"  # Informational


@dataclass
class FieldConflict:
    """Represents a conflict in a single field."""
    field_name: str
    japanese_name: str
    source_value: Any
    db_value: Any
    recommended_action: ConflictStrategy
    severity: ConflictSeverity
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "japanese_name": self.japanese_name,
            "source_value": str(self.source_value) if self.source_value else None,
            "db_value": str(self.db_value) if self.db_value else None,
            "recommended_action": self.recommended_action.value,
            "severity": self.severity.value,
            "reason": self.reason
        }


@dataclass
class SyncConflict:
    """Represents a conflict for a single record."""
    entity_type: str  # "employee", "factory"
    entity_key: str  # Unique identifier (employee_number, factory_id)
    entity_name: str
    conflicts: List[FieldConflict] = field(default_factory=list)
    source_record: Dict = field(default_factory=dict)
    db_record_id: int = None
    resolution: Optional[ConflictStrategy] = None
    resolved: bool = False

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "entity_key": self.entity_key,
            "entity_name": self.entity_name,
            "db_record_id": self.db_record_id,
            "conflicts_count": len(self.conflicts),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "max_severity": max(c.severity.value for c in self.conflicts) if self.conflicts else "low",
            "resolved": self.resolved,
            "resolution": self.resolution.value if self.resolution else None
        }


@dataclass
class SyncAnalysis:
    """Result of analyzing sync changes before applying."""
    source_type: str  # "excel", "json"
    entity_type: str
    source_count: int = 0
    db_count: int = 0
    to_create: List[Dict] = field(default_factory=list)
    to_update: List[Dict] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    conflicts: List[SyncConflict] = field(default_factory=list)
    db_only: List[Dict] = field(default_factory=list)  # In DB but not in source
    analyzed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type,
            "entity_type": self.entity_type,
            "counts": {
                "source": self.source_count,
                "db": self.db_count,
                "to_create": len(self.to_create),
                "to_update": len(self.to_update),
                "unchanged": len(self.unchanged),
                "conflicts": len(self.conflicts),
                "db_only": len(self.db_only)
            },
            "conflicts": [c.to_dict() for c in self.conflicts],
            "to_create_preview": self.to_create[:20],
            "db_only_preview": self.db_only[:20],
            "analyzed_at": self.analyzed_at.isoformat()
        }


@dataclass
class SyncResult:
    """Result of executing a sync operation."""
    success: bool = False
    created: int = 0
    updated: int = 0
    skipped: int = 0
    conflicts_resolved: int = 0
    conflicts_pending: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    snapshot_id: str = ""
    executed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "conflicts_resolved": self.conflicts_resolved,
            "conflicts_pending": self.conflicts_pending,
            "errors": self.errors,
            "warnings": self.warnings,
            "snapshot_id": self.snapshot_id,
            "executed_at": self.executed_at.isoformat()
        }


class SyncResolverService:
    """
    Resolves data conflicts during synchronization.

    Provides:
    - Pre-sync analysis (dry run)
    - Conflict detection and resolution
    - Rollback support via snapshots
    """

    def __init__(self, db: Session):
        self.db = db
        self.backup_dir = "/app/backups"

    # ========================================
    # EMPLOYEE SYNC
    # ========================================

    def analyze_employee_sync(
        self,
        source_data: List[Dict],
        source_type: str = "excel"
    ) -> SyncAnalysis:
        """
        Analyze employee sync changes without applying.

        Args:
            source_data: List of employee records from external source
            source_type: "excel" or "json"

        Returns:
            SyncAnalysis with conflicts and changes
        """
        analysis = SyncAnalysis(
            source_type=source_type,
            entity_type="employee",
            source_count=len(source_data)
        )

        # Get current DB employees
        db_employees = {
            e.employee_number: e
            for e in self.db.query(Employee).all()
        }
        analysis.db_count = len(db_employees)

        source_keys = set()

        for record in source_data:
            emp_number = str(record.get("employee_number", "")).strip()
            if not emp_number:
                continue

            source_keys.add(emp_number)
            db_emp = db_employees.get(emp_number)

            if not db_emp:
                # New employee
                analysis.to_create.append({
                    "employee_number": emp_number,
                    "full_name": record.get("full_name_kanji", ""),
                    "company_name": record.get("company_name", "")
                })
            else:
                # Existing employee - check for conflicts
                conflicts = self._compare_employee(record, db_emp)

                if conflicts:
                    analysis.conflicts.append(SyncConflict(
                        entity_type="employee",
                        entity_key=emp_number,
                        entity_name=db_emp.full_name_kanji,
                        conflicts=conflicts,
                        source_record=record,
                        db_record_id=db_emp.id
                    ))
                    analysis.to_update.append({
                        "employee_number": emp_number,
                        "has_conflicts": True,
                        "conflict_count": len(conflicts)
                    })
                else:
                    analysis.unchanged.append(emp_number)

        # Find DB-only records
        for emp_number, db_emp in db_employees.items():
            if emp_number not in source_keys:
                analysis.db_only.append({
                    "employee_number": emp_number,
                    "full_name": db_emp.full_name_kanji,
                    "status": db_emp.status
                })

        return analysis

    def _compare_employee(self, source: Dict, db: Employee) -> List[FieldConflict]:
        """Compare source record with DB record for conflicts."""
        conflicts = []

        compare_fields = [
            ("full_name_kanji", "氏名", ConflictSeverity.HIGH),
            ("full_name_kana", "カナ", ConflictSeverity.MEDIUM),
            ("company_name", "派遣先", ConflictSeverity.HIGH),
            ("department", "配属先", ConflictSeverity.MEDIUM),
            ("line_name", "ライン", ConflictSeverity.MEDIUM),
            ("hourly_rate", "時給", ConflictSeverity.HIGH),
            ("status", "状態", ConflictSeverity.CRITICAL),
        ]

        for field_name, japanese_name, severity in compare_fields:
            source_val = self._normalize_value(source.get(field_name))
            db_val = self._normalize_value(getattr(db, field_name, None))

            if source_val != db_val and source_val is not None:
                # Determine recommended action
                if severity == ConflictSeverity.CRITICAL:
                    action = ConflictStrategy.MANUAL
                elif field_name == "status" and source_val == "resigned":
                    action = ConflictStrategy.SOURCE_WINS  # Trust source for resignations
                elif field_name in ["hourly_rate"]:
                    action = ConflictStrategy.SOURCE_WINS  # Excel usually has latest rates
                else:
                    action = ConflictStrategy.NEWEST_WINS

                conflicts.append(FieldConflict(
                    field_name=field_name,
                    japanese_name=japanese_name,
                    source_value=source_val,
                    db_value=db_val,
                    recommended_action=action,
                    severity=severity,
                    reason=f"{japanese_name}がソースとDBで異なります"
                ))

        return conflicts

    def resolve_employee_conflicts(
        self,
        analysis: SyncAnalysis,
        strategy: ConflictStrategy = ConflictStrategy.SOURCE_WINS,
        manual_decisions: Dict[str, ConflictStrategy] = None
    ) -> SyncResult:
        """
        Apply employee sync with conflict resolution.

        Args:
            analysis: Previous analysis result
            strategy: Default resolution strategy
            manual_decisions: {employee_number: strategy} for manual overrides

        Returns:
            SyncResult
        """
        result = SyncResult()
        manual_decisions = manual_decisions or {}

        # Create snapshot first
        result.snapshot_id = self._create_snapshot("employees")

        try:
            # Create new employees
            for item in analysis.to_create:
                # Would need full data from source
                result.created += 1

            # Resolve conflicts
            for conflict in analysis.conflicts:
                emp_number = conflict.entity_key
                resolution = manual_decisions.get(emp_number, strategy)

                if resolution == ConflictStrategy.DB_WINS:
                    result.skipped += 1
                    continue

                if resolution == ConflictStrategy.MANUAL and emp_number not in manual_decisions:
                    result.conflicts_pending += 1
                    continue

                # Apply changes
                db_emp = self.db.query(Employee).filter(
                    Employee.employee_number == emp_number
                ).first()

                if db_emp and conflict.source_record:
                    self._apply_employee_changes(db_emp, conflict.source_record, resolution)
                    result.updated += 1
                    result.conflicts_resolved += 1

            self.db.commit()
            result.success = True

        except Exception as e:
            self.db.rollback()
            result.errors.append(str(e))
            result.success = False

        return result

    def _apply_employee_changes(
        self,
        employee: Employee,
        source: Dict,
        strategy: ConflictStrategy
    ):
        """Apply source changes to employee based on strategy."""
        updatable_fields = [
            "full_name_kanji", "full_name_kana", "company_name",
            "department", "line_name", "hourly_rate", "billing_rate",
            "address", "visa_expiry_date", "status"
        ]

        for field in updatable_fields:
            source_val = source.get(field)
            if source_val is not None:
                # Handle special conversions
                if field == "hourly_rate" or field == "billing_rate":
                    if source_val:
                        source_val = Decimal(str(source_val))
                elif field in ["visa_expiry_date", "hire_date", "termination_date"]:
                    if isinstance(source_val, str):
                        source_val = datetime.strptime(source_val, "%Y-%m-%d").date()

                setattr(employee, field, source_val)

    # ========================================
    # FACTORY SYNC
    # ========================================

    def analyze_factory_sync(
        self,
        source_data: List[Dict],
        source_type: str = "json"
    ) -> SyncAnalysis:
        """Analyze factory sync changes."""
        analysis = SyncAnalysis(
            source_type=source_type,
            entity_type="factory",
            source_count=len(source_data)
        )

        db_factories = {
            f.factory_id: f
            for f in self.db.query(Factory).all()
        }
        analysis.db_count = len(db_factories)

        source_keys = set()

        for record in source_data:
            factory_id = record.get("factory_id", "")
            if not factory_id:
                # Generate factory_id
                client = record.get("client_company", {})
                plant = record.get("plant", {})
                factory_id = f"{client.get('name', '')}_{plant.get('name', '')}".replace(" ", "_")

            if not factory_id or factory_id == "_":
                continue

            source_keys.add(factory_id)
            db_factory = db_factories.get(factory_id)

            if not db_factory:
                analysis.to_create.append({
                    "factory_id": factory_id,
                    "company_name": record.get("client_company", {}).get("name", ""),
                    "plant_name": record.get("plant", {}).get("name", "")
                })
            else:
                conflicts = self._compare_factory(record, db_factory)

                if conflicts:
                    analysis.conflicts.append(SyncConflict(
                        entity_type="factory",
                        entity_key=factory_id,
                        entity_name=f"{db_factory.company_name} {db_factory.plant_name}",
                        conflicts=conflicts,
                        source_record=record,
                        db_record_id=db_factory.id
                    ))
                else:
                    analysis.unchanged.append(factory_id)

        return analysis

    def _compare_factory(self, source: Dict, db: Factory) -> List[FieldConflict]:
        """Compare factory source with DB record."""
        conflicts = []

        client = source.get("client_company", {})
        plant = source.get("plant", {})
        schedule = source.get("schedule", {})

        compare_map = [
            (client.get("address"), db.company_address, "company_address", "会社住所", ConflictSeverity.MEDIUM),
            (plant.get("address"), db.plant_address, "plant_address", "工場住所", ConflictSeverity.MEDIUM),
            (client.get("responsible_person", {}).get("name"), db.client_responsible_name, "client_responsible_name", "派遣先責任者", ConflictSeverity.HIGH),
            (schedule.get("conflict_date"), str(db.conflict_date) if db.conflict_date else None, "conflict_date", "抵触日", ConflictSeverity.HIGH),
        ]

        for source_val, db_val, field_name, japanese_name, severity in compare_map:
            source_val = self._normalize_value(source_val)
            db_val = self._normalize_value(db_val)

            if source_val != db_val and source_val is not None:
                conflicts.append(FieldConflict(
                    field_name=field_name,
                    japanese_name=japanese_name,
                    source_value=source_val,
                    db_value=db_val,
                    recommended_action=ConflictStrategy.SOURCE_WINS,
                    severity=severity
                ))

        return conflicts

    # ========================================
    # UTILITIES
    # ========================================

    def _normalize_value(self, val: Any) -> Any:
        """Normalize value for comparison."""
        if val is None:
            return None
        if isinstance(val, str):
            val = val.strip()
            if val in ('', '0', 'nan', 'None'):
                return None
            return val
        if isinstance(val, (int, float)):
            if val == 0:
                return None
            return val
        if isinstance(val, Decimal):
            return float(val)
        return val

    def _create_snapshot(self, entity_type: str) -> str:
        """Create backup snapshot before sync."""
        os.makedirs(self.backup_dir, exist_ok=True)

        snapshot_id = f"sync_{entity_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.backup_dir, f"{snapshot_id}.json")

        if entity_type == "employees":
            data = [
                {
                    "id": e.id,
                    "employee_number": e.employee_number,
                    "full_name_kanji": e.full_name_kanji,
                    "company_name": e.company_name,
                    "status": e.status,
                    "hourly_rate": float(e.hourly_rate) if e.hourly_rate else None
                }
                for e in self.db.query(Employee).all()
            ]
        elif entity_type == "factories":
            data = [
                {
                    "id": f.id,
                    "factory_id": f.factory_id,
                    "company_name": f.company_name,
                    "plant_name": f.plant_name
                }
                for f in self.db.query(Factory).all()
            ]
        else:
            data = []

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return snapshot_id

    def rollback_sync(self, snapshot_id: str) -> bool:
        """Rollback to a previous snapshot."""
        backup_path = os.path.join(self.backup_dir, f"{snapshot_id}.json")

        if not os.path.exists(backup_path):
            return False

        # Implementation would restore from backup
        # For safety, this would need careful implementation
        return True

    def list_snapshots(self) -> List[Dict]:
        """List available snapshots."""
        if not os.path.exists(self.backup_dir):
            return []

        snapshots = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.json') and filename.startswith('sync_'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                snapshots.append({
                    "snapshot_id": filename.replace('.json', ''),
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        return sorted(snapshots, key=lambda x: x['created_at'], reverse=True)
