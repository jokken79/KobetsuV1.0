"""
Alert Manager Service - アラート管理サービス

Manages proactive alerts for:
- Expiring contracts
- Missing employee assignments
- Incomplete factory configurations
- Compliance issues
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.factory import Factory
from app.models.employee import Employee


class AlertPriority(str, Enum):
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Action within same day
    MEDIUM = "medium"  # Action within 3 days
    LOW = "low"  # Action within week
    INFO = "info"  # No action needed


class AlertType(str, Enum):
    CONTRACT_EXPIRING = "contract_expiring"
    CONTRACT_EXPIRED = "contract_expired"
    EMPLOYEE_UNASSIGNED = "employee_unassigned"
    FACTORY_INCOMPLETE = "factory_incomplete"
    COMPLIANCE_VIOLATION = "compliance_violation"
    CONFLICT_DATE_APPROACHING = "conflict_date_approaching"
    VISA_EXPIRING = "visa_expiring"


@dataclass
class Alert:
    """Represents a single alert."""
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    entity_type: str  # contract, employee, factory
    entity_id: int
    entity_name: str = ""
    action_url: str = ""
    expires_in_days: int = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "action_url": self.action_url,
            "expires_in_days": self.expires_in_days,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class AlertSummary:
    """Summary of all alerts."""
    critical: List[Alert] = field(default_factory=list)
    high: List[Alert] = field(default_factory=list)
    medium: List[Alert] = field(default_factory=list)
    low: List[Alert] = field(default_factory=list)
    info: List[Alert] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "summary": {
                "critical": len(self.critical),
                "high": len(self.high),
                "medium": len(self.medium),
                "low": len(self.low),
                "info": len(self.info),
                "total": len(self.critical) + len(self.high) + len(self.medium) + len(self.low)
            },
            "critical": [a.to_dict() for a in self.critical],
            "high": [a.to_dict() for a in self.high],
            "medium": [a.to_dict() for a in self.medium],
            "low": [a.to_dict() for a in self.low],
            "generated_at": self.generated_at.isoformat()
        }


class AlertManagerService:
    """
    Manages proactive alerts for the UNS-Kobetsu system.

    Monitors contracts, employees, and factories for issues that need attention.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_alerts(self) -> AlertSummary:
        """Get all current alerts across all categories."""
        summary = AlertSummary()

        # Gather all alerts
        all_alerts = []
        all_alerts.extend(self.check_expiring_contracts())
        all_alerts.extend(self.check_expired_contracts())
        all_alerts.extend(self.check_unassigned_employees())
        all_alerts.extend(self.check_incomplete_factories())
        all_alerts.extend(self.check_approaching_conflict_dates())
        all_alerts.extend(self.check_expiring_visas())

        # Sort into priority buckets
        for alert in all_alerts:
            if alert.priority == AlertPriority.CRITICAL:
                summary.critical.append(alert)
            elif alert.priority == AlertPriority.HIGH:
                summary.high.append(alert)
            elif alert.priority == AlertPriority.MEDIUM:
                summary.medium.append(alert)
            elif alert.priority == AlertPriority.LOW:
                summary.low.append(alert)
            else:
                summary.info.append(alert)

        # Sort each bucket by expires_in_days (if applicable)
        summary.critical.sort(key=lambda x: x.expires_in_days or 999)
        summary.high.sort(key=lambda x: x.expires_in_days or 999)

        return summary

    def check_expiring_contracts(self, days_ahead: int = 30) -> List[Alert]:
        """Check for contracts expiring within specified days."""
        alerts = []
        today = date.today()

        # Define thresholds
        thresholds = [
            (1, AlertPriority.CRITICAL, "明日期限切れ"),
            (7, AlertPriority.HIGH, "7日以内に期限切れ"),
            (15, AlertPriority.HIGH, "15日以内に期限切れ"),
            (30, AlertPriority.MEDIUM, "30日以内に期限切れ"),
        ]

        for days, priority, label in thresholds:
            if days > days_ahead:
                continue

            target_date = today + timedelta(days=days)

            contracts = self.db.query(KobetsuKeiyakusho).filter(
                and_(
                    KobetsuKeiyakusho.dispatch_end_date == target_date,
                    KobetsuKeiyakusho.status == 'active'
                )
            ).all()

            for contract in contracts:
                alerts.append(Alert(
                    type=AlertType.CONTRACT_EXPIRING,
                    priority=priority,
                    title=f"契約期限切れ警告: {contract.contract_number}",
                    message=f"{label}: {contract.worksite_name}",
                    entity_type="contract",
                    entity_id=contract.id,
                    entity_name=contract.contract_number,
                    action_url=f"/kobetsu/{contract.id}",
                    expires_in_days=days,
                    metadata={
                        "factory_name": contract.worksite_name,
                        "end_date": str(contract.dispatch_end_date),
                        "workers": contract.number_of_workers
                    }
                ))

        return alerts

    def check_expired_contracts(self) -> List[Alert]:
        """Check for contracts that have expired but still marked active."""
        alerts = []
        today = date.today()

        expired = self.db.query(KobetsuKeiyakusho).filter(
            and_(
                KobetsuKeiyakusho.dispatch_end_date < today,
                KobetsuKeiyakusho.status == 'active'
            )
        ).all()

        for contract in expired:
            days_expired = (today - contract.dispatch_end_date).days

            alerts.append(Alert(
                type=AlertType.CONTRACT_EXPIRED,
                priority=AlertPriority.CRITICAL,
                title=f"期限切れ契約: {contract.contract_number}",
                message=f"{days_expired}日前に期限切れ。ステータス更新または更新が必要",
                entity_type="contract",
                entity_id=contract.id,
                entity_name=contract.contract_number,
                action_url=f"/kobetsu/{contract.id}",
                expires_in_days=-days_expired,
                metadata={
                    "factory_name": contract.worksite_name,
                    "end_date": str(contract.dispatch_end_date),
                    "days_expired": days_expired,
                    "suggested_actions": [
                        f"更新する: /kobetsu/{contract.id}/renew",
                        f"終了する: ステータスを'expired'に変更"
                    ]
                }
            ))

        return alerts

    def check_unassigned_employees(self) -> List[Alert]:
        """Check for active employees without current contracts."""
        alerts = []
        today = date.today()

        # Get all active employees
        active_employees = self.db.query(Employee).filter(
            Employee.status == 'active'
        ).all()

        # Get employee IDs with active contracts
        assigned_subquery = self.db.query(
            KobetsuEmployee.employee_id
        ).join(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.status == 'active',
            KobetsuKeiyakusho.dispatch_start_date <= today,
            KobetsuKeiyakusho.dispatch_end_date >= today
        ).distinct()

        assigned_ids = set(row[0] for row in assigned_subquery.all())

        for emp in active_employees:
            if emp.id not in assigned_ids:
                alerts.append(Alert(
                    type=AlertType.EMPLOYEE_UNASSIGNED,
                    priority=AlertPriority.HIGH,
                    title=f"未配属社員: {emp.full_name_kanji}",
                    message=f"社員番号 {emp.employee_number} は有効な契約がありません",
                    entity_type="employee",
                    entity_id=emp.id,
                    entity_name=emp.full_name_kanji,
                    action_url=f"/employees/{emp.id}",
                    metadata={
                        "employee_number": emp.employee_number,
                        "company_name": emp.company_name,
                        "last_factory": emp.factory_id
                    }
                ))

        return alerts

    def check_incomplete_factories(self) -> List[Alert]:
        """Check for factories missing required information."""
        alerts = []

        required_fields = [
            ("client_responsible_name", "派遣先責任者", AlertPriority.HIGH),
            ("client_complaint_name", "苦情処理担当者", AlertPriority.MEDIUM),
            ("dispatch_responsible_name", "派遣元責任者", AlertPriority.MEDIUM),
            ("company_address", "会社住所", AlertPriority.LOW),
        ]

        factories = self.db.query(Factory).filter(Factory.is_active == True).all()

        for factory in factories:
            missing_fields = []
            max_priority = AlertPriority.LOW

            for field_name, japanese_name, priority in required_fields:
                if not getattr(factory, field_name, None):
                    missing_fields.append(japanese_name)
                    if priority == AlertPriority.HIGH:
                        max_priority = AlertPriority.HIGH
                    elif priority == AlertPriority.MEDIUM and max_priority != AlertPriority.HIGH:
                        max_priority = AlertPriority.MEDIUM

            if missing_fields:
                alerts.append(Alert(
                    type=AlertType.FACTORY_INCOMPLETE,
                    priority=max_priority,
                    title=f"工場情報不足: {factory.company_name}",
                    message=f"不足項目: {', '.join(missing_fields)}",
                    entity_type="factory",
                    entity_id=factory.id,
                    entity_name=f"{factory.company_name} {factory.plant_name}",
                    action_url=f"/factories/{factory.id}",
                    metadata={
                        "missing_fields": missing_fields,
                        "impact": "準拠書類を生成できない可能性があります"
                    }
                ))

        return alerts

    def check_approaching_conflict_dates(self, days_ahead: int = 90) -> List[Alert]:
        """Check for factories approaching their 抵触日."""
        alerts = []
        today = date.today()
        threshold = today + timedelta(days=days_ahead)

        factories = self.db.query(Factory).filter(
            and_(
                Factory.is_active == True,
                Factory.conflict_date.isnot(None),
                Factory.conflict_date <= threshold,
                Factory.conflict_date >= today
            )
        ).all()

        for factory in factories:
            days_remaining = (factory.conflict_date - today).days

            if days_remaining <= 30:
                priority = AlertPriority.CRITICAL
                label = "30日以内に抵触日"
            elif days_remaining <= 60:
                priority = AlertPriority.HIGH
                label = "60日以内に抵触日"
            else:
                priority = AlertPriority.MEDIUM
                label = "90日以内に抵触日"

            # Count active contracts at this factory
            active_contracts = self.db.query(KobetsuKeiyakusho).filter(
                KobetsuKeiyakusho.factory_id == factory.id,
                KobetsuKeiyakusho.status == 'active'
            ).count()

            alerts.append(Alert(
                type=AlertType.CONFLICT_DATE_APPROACHING,
                priority=priority,
                title=f"抵触日接近: {factory.company_name}",
                message=f"{label}（{factory.conflict_date}）",
                entity_type="factory",
                entity_id=factory.id,
                entity_name=f"{factory.company_name} {factory.plant_name}",
                action_url=f"/factories/{factory.id}",
                expires_in_days=days_remaining,
                metadata={
                    "conflict_date": str(factory.conflict_date),
                    "active_contracts": active_contracts,
                    "days_remaining": days_remaining
                }
            ))

        return alerts

    def check_expiring_visas(self, days_ahead: int = 60) -> List[Alert]:
        """Check for employees with visas expiring soon."""
        alerts = []
        today = date.today()
        threshold = today + timedelta(days=days_ahead)

        employees = self.db.query(Employee).filter(
            and_(
                Employee.status == 'active',
                Employee.visa_expiry_date.isnot(None),
                Employee.visa_expiry_date <= threshold,
                Employee.visa_expiry_date >= today
            )
        ).all()

        for emp in employees:
            days_remaining = (emp.visa_expiry_date - today).days

            if days_remaining <= 14:
                priority = AlertPriority.CRITICAL
            elif days_remaining <= 30:
                priority = AlertPriority.HIGH
            else:
                priority = AlertPriority.MEDIUM

            alerts.append(Alert(
                type=AlertType.VISA_EXPIRING,
                priority=priority,
                title=f"ビザ期限警告: {emp.full_name_kanji}",
                message=f"ビザ期限: {emp.visa_expiry_date}（残り{days_remaining}日）",
                entity_type="employee",
                entity_id=emp.id,
                entity_name=emp.full_name_kanji,
                action_url=f"/employees/{emp.id}",
                expires_in_days=days_remaining,
                metadata={
                    "employee_number": emp.employee_number,
                    "visa_type": emp.visa_type,
                    "visa_expiry_date": str(emp.visa_expiry_date)
                }
            ))

        return alerts

    def get_daily_summary(self) -> dict:
        """Generate daily summary for dashboard/notifications."""
        summary = self.get_all_alerts()
        today = date.today()

        # Contracts expiring this week
        expiring_this_week = self.db.query(KobetsuKeiyakusho).filter(
            and_(
                KobetsuKeiyakusho.dispatch_end_date.between(
                    today,
                    today + timedelta(days=7)
                ),
                KobetsuKeiyakusho.status == 'active'
            )
        ).count()

        # Unassigned employees count
        unassigned_count = len([a for a in summary.high if a.type == AlertType.EMPLOYEE_UNASSIGNED])

        return {
            "date": str(today),
            "title": f"日次アラートサマリー: {today.strftime('%Y-%m-%d')}",
            "counts": {
                "critical": len(summary.critical),
                "high": len(summary.high),
                "medium": len(summary.medium),
                "total_action_required": len(summary.critical) + len(summary.high)
            },
            "highlights": {
                "expiring_this_week": expiring_this_week,
                "unassigned_employees": unassigned_count,
                "expired_contracts": len([a for a in summary.critical if a.type == AlertType.CONTRACT_EXPIRED])
            },
            "top_priorities": [a.to_dict() for a in (summary.critical + summary.high)[:10]],
            "generated_at": datetime.now().isoformat()
        }

    def get_alerts_for_entity(self, entity_type: str, entity_id: int) -> List[Alert]:
        """Get alerts specific to an entity (contract, employee, or factory)."""
        all_alerts = self.get_all_alerts()
        all_list = (
            all_alerts.critical +
            all_alerts.high +
            all_alerts.medium +
            all_alerts.low
        )

        return [
            a for a in all_list
            if a.entity_type == entity_type and a.entity_id == entity_id
        ]
