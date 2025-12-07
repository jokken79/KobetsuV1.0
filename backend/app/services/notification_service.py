"""
Notification Service - 通知サービス

Handles sending notifications via:
- Email (SMTP)
- Slack (Webhook)
- In-app notifications (database)
"""
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from enum import Enum

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.alert_manager_service import Alert, AlertSummary, AlertManagerService

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    URGENT = "urgent"  # Immediate send
    HIGH = "high"  # Within 1 hour
    NORMAL = "normal"  # Batched daily
    LOW = "low"  # Weekly digest


@dataclass
class NotificationResult:
    """Result of a notification send attempt."""
    success: bool
    channel: str
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[datetime] = None

    def __post_init__(self):
        if self.sent_at is None:
            self.sent_at = datetime.now()


class NotificationService:
    """
    Manages notifications across multiple channels.

    Supports:
    - Email via SMTP
    - Slack via webhook
    - Configurable priority and batching
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
    ):
        self.db = db
        self.smtp_host = smtp_host or getattr(settings, 'SMTP_HOST', None)
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user or getattr(settings, 'SMTP_USER', None)
        self.smtp_password = smtp_password or getattr(settings, 'SMTP_PASSWORD', None)
        self.slack_webhook_url = slack_webhook_url or getattr(settings, 'SLACK_WEBHOOK_URL', None)

    # =========================================================================
    # Email Notifications
    # =========================================================================

    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> NotificationResult:
        """
        Send an email notification.

        Args:
            to: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional, will strip HTML if not provided)
            from_email: Sender email (defaults to settings)

        Returns:
            NotificationResult indicating success/failure
        """
        if not self.smtp_host:
            logger.warning("SMTP not configured, skipping email notification")
            return NotificationResult(
                success=False,
                channel="email",
                recipient=to,
                error="SMTP not configured"
            )

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email or self.smtp_user or 'noreply@uns-kobetsu.local'
            msg['To'] = to

            # Plain text version
            if body_text:
                msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

            # HTML version
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Email sent successfully to {to}")
            return NotificationResult(
                success=True,
                channel="email",
                recipient=to,
                message_id=msg['Message-ID']
            )

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return NotificationResult(
                success=False,
                channel="email",
                recipient=to,
                error=str(e)
            )

    # =========================================================================
    # Slack Notifications
    # =========================================================================

    def send_slack(
        self,
        message: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        channel: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> NotificationResult:
        """
        Send a Slack notification via webhook.

        Args:
            message: Main message text (used as fallback)
            blocks: Slack Block Kit blocks for rich formatting
            channel: Override channel (if webhook supports it)
            webhook_url: Override webhook URL

        Returns:
            NotificationResult indicating success/failure
        """
        url = webhook_url or self.slack_webhook_url

        if not url:
            logger.warning("Slack webhook not configured, skipping notification")
            return NotificationResult(
                success=False,
                channel="slack",
                recipient="webhook",
                error="Slack webhook not configured"
            )

        try:
            payload = {
                "text": message,
            }

            if blocks:
                payload["blocks"] = blocks

            if channel:
                payload["channel"] = channel

            with httpx.Client() as client:
                response = client.post(url, json=payload, timeout=10)
                response.raise_for_status()

            logger.info("Slack notification sent successfully")
            return NotificationResult(
                success=True,
                channel="slack",
                recipient=channel or "webhook"
            )

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return NotificationResult(
                success=False,
                channel="slack",
                recipient=channel or "webhook",
                error=str(e)
            )

    # =========================================================================
    # Alert-based Notifications
    # =========================================================================

    def send_alert_notification(
        self,
        alert: Alert,
        channels: List[NotificationChannel] = None,
        recipients: Dict[NotificationChannel, str] = None,
    ) -> List[NotificationResult]:
        """
        Send notification for a single alert.

        Args:
            alert: Alert to send notification for
            channels: List of channels to use (default: based on priority)
            recipients: Dict of channel -> recipient

        Returns:
            List of NotificationResults
        """
        if channels is None:
            # Default channels based on priority
            if alert.priority.value in ['critical', 'high']:
                channels = [NotificationChannel.SLACK, NotificationChannel.EMAIL]
            else:
                channels = [NotificationChannel.IN_APP]

        results = []

        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                recipient = recipients.get(NotificationChannel.EMAIL) if recipients else None
                if recipient:
                    result = self.send_email(
                        to=recipient,
                        subject=f"[{alert.priority.value.upper()}] {alert.title}",
                        body_html=self._format_alert_email_html(alert),
                        body_text=self._format_alert_email_text(alert)
                    )
                    results.append(result)

            elif channel == NotificationChannel.SLACK:
                result = self.send_slack(
                    message=f"*{alert.title}*\n{alert.message}",
                    blocks=self._format_alert_slack_blocks(alert)
                )
                results.append(result)

        return results

    def send_daily_summary(
        self,
        summary: AlertSummary,
        email_recipients: List[str] = None,
        send_slack: bool = True,
    ) -> List[NotificationResult]:
        """
        Send daily alert summary.

        Args:
            summary: AlertSummary from AlertManagerService
            email_recipients: List of email addresses to send to
            send_slack: Whether to send Slack notification

        Returns:
            List of NotificationResults
        """
        results = []
        today = datetime.now().strftime('%Y-%m-%d')

        # Email notifications
        if email_recipients:
            subject = f"[日次レポート] UNS-Kobetsu アラートサマリー - {today}"
            body_html = self._format_summary_email_html(summary)
            body_text = self._format_summary_email_text(summary)

            for recipient in email_recipients:
                result = self.send_email(
                    to=recipient,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text
                )
                results.append(result)

        # Slack notification
        if send_slack:
            result = self.send_slack(
                message=f"UNS-Kobetsu 日次サマリー: {today}",
                blocks=self._format_summary_slack_blocks(summary)
            )
            results.append(result)

        return results

    # =========================================================================
    # Formatting Helpers
    # =========================================================================

    def _format_alert_email_html(self, alert: Alert) -> str:
        """Format alert as HTML email body."""
        priority_colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#d97706',
            'low': '#2563eb',
        }
        color = priority_colors.get(alert.priority.value, '#6b7280')

        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="border-left: 4px solid {color}; padding-left: 16px; margin-bottom: 20px;">
                    <h2 style="color: {color}; margin: 0 0 8px 0;">{alert.title}</h2>
                    <p style="color: #374151; margin: 0;">{alert.message}</p>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 8px; background: #f3f4f6; font-weight: bold;">タイプ</td>
                        <td style="padding: 8px;">{alert.type.value}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f3f4f6; font-weight: bold;">優先度</td>
                        <td style="padding: 8px; color: {color};">{alert.priority.value.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f3f4f6; font-weight: bold;">対象</td>
                        <td style="padding: 8px;">{alert.entity_name}</td>
                    </tr>
                    {f'<tr><td style="padding: 8px; background: #f3f4f6; font-weight: bold;">残り日数</td><td style="padding: 8px;">{alert.expires_in_days}日</td></tr>' if alert.expires_in_days else ''}
                </table>

                <a href="{alert.action_url}" style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px;">
                    対応する
                </a>

                <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
                <p style="color: #6b7280; font-size: 12px;">
                    このメールは UNS-Kobetsu 管理システムから自動送信されました。
                </p>
            </div>
        </body>
        </html>
        """

    def _format_alert_email_text(self, alert: Alert) -> str:
        """Format alert as plain text email body."""
        return f"""
{alert.title}
{'=' * len(alert.title)}

{alert.message}

タイプ: {alert.type.value}
優先度: {alert.priority.value.upper()}
対象: {alert.entity_name}
{f'残り日数: {alert.expires_in_days}日' if alert.expires_in_days else ''}

対応する: {alert.action_url}

---
このメールは UNS-Kobetsu 管理システムから自動送信されました。
        """

    def _format_alert_slack_blocks(self, alert: Alert) -> List[Dict]:
        """Format alert as Slack Block Kit blocks."""
        priority_emoji = {
            'critical': ':red_circle:',
            'high': ':large_orange_circle:',
            'medium': ':large_yellow_circle:',
            'low': ':large_blue_circle:',
        }
        emoji = priority_emoji.get(alert.priority.value, ':white_circle:')

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.message
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*タイプ:*\n{alert.type.value}"},
                    {"type": "mrkdwn", "text": f"*優先度:*\n{alert.priority.value.upper()}"},
                    {"type": "mrkdwn", "text": f"*対象:*\n{alert.entity_name}"},
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "対応する"},
                        "url": alert.action_url,
                        "style": "primary"
                    }
                ]
            }
        ]

        if alert.expires_in_days is not None:
            blocks[2]["fields"].append({
                "type": "mrkdwn",
                "text": f"*残り:*\n{alert.expires_in_days}日"
            })

        return blocks

    def _format_summary_email_html(self, summary: AlertSummary) -> str:
        """Format summary as HTML email body."""
        critical_count = len(summary.critical)
        high_count = len(summary.high)
        total = critical_count + high_count + len(summary.medium) + len(summary.low)

        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #111827;">UNS-Kobetsu 日次アラートサマリー</h1>
                <p style="color: #6b7280;">{datetime.now().strftime('%Y年%m月%d日')}</p>

                <div style="display: flex; gap: 16px; margin: 24px 0;">
                    <div style="flex: 1; padding: 16px; background: #fef2f2; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: #dc2626;">{critical_count}</div>
                        <div style="color: #7f1d1d;">緊急</div>
                    </div>
                    <div style="flex: 1; padding: 16px; background: #fff7ed; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: #ea580c;">{high_count}</div>
                        <div style="color: #7c2d12;">高</div>
                    </div>
                    <div style="flex: 1; padding: 16px; background: #f3f4f6; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: #374151;">{total}</div>
                        <div style="color: #6b7280;">合計</div>
                    </div>
                </div>

                {'<h2>緊急アラート</h2>' + ''.join(f'<p style="border-left: 4px solid #dc2626; padding-left: 12px; margin: 8px 0;">{a.title}<br/><small style="color: #6b7280;">{a.message}</small></p>' for a in summary.critical[:5]) if summary.critical else ''}

                {'<h2>高優先度アラート</h2>' + ''.join(f'<p style="border-left: 4px solid #ea580c; padding-left: 12px; margin: 8px 0;">{a.title}<br/><small style="color: #6b7280;">{a.message}</small></p>' for a in summary.high[:5]) if summary.high else ''}

                <a href="/compliance" style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px;">
                    コンプライアンスダッシュボードを開く
                </a>

                <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
                <p style="color: #6b7280; font-size: 12px;">
                    このメールは UNS-Kobetsu 管理システムから自動送信されました。
                </p>
            </div>
        </body>
        </html>
        """

    def _format_summary_email_text(self, summary: AlertSummary) -> str:
        """Format summary as plain text email body."""
        lines = [
            "UNS-Kobetsu 日次アラートサマリー",
            f"{datetime.now().strftime('%Y年%m月%d日')}",
            "",
            f"緊急: {len(summary.critical)}件",
            f"高: {len(summary.high)}件",
            f"中: {len(summary.medium)}件",
            f"低: {len(summary.low)}件",
            "",
        ]

        if summary.critical:
            lines.append("--- 緊急アラート ---")
            for alert in summary.critical[:5]:
                lines.append(f"- {alert.title}")
            lines.append("")

        if summary.high:
            lines.append("--- 高優先度アラート ---")
            for alert in summary.high[:5]:
                lines.append(f"- {alert.title}")
            lines.append("")

        lines.append("コンプライアンスダッシュボード: /compliance")

        return "\n".join(lines)

    def _format_summary_slack_blocks(self, summary: AlertSummary) -> List[Dict]:
        """Format summary as Slack Block Kit blocks."""
        critical_count = len(summary.critical)
        high_count = len(summary.high)
        total = critical_count + high_count + len(summary.medium) + len(summary.low)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"UNS-Kobetsu 日次サマリー - {datetime.now().strftime('%Y/%m/%d')}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f":red_circle: *緊急:* {critical_count}件"},
                    {"type": "mrkdwn", "text": f":large_orange_circle: *高:* {high_count}件"},
                    {"type": "mrkdwn", "text": f":large_yellow_circle: *中:* {len(summary.medium)}件"},
                    {"type": "mrkdwn", "text": f":white_circle: *合計:* {total}件"},
                ]
            },
            {"type": "divider"},
        ]

        if summary.critical:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*緊急アラート:*\n" + "\n".join(
                        f"• {a.title}" for a in summary.critical[:5]
                    )
                }
            })

        if summary.high:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*高優先度:*\n" + "\n".join(
                        f"• {a.title}" for a in summary.high[:5]
                    )
                }
            })

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "ダッシュボードを開く"},
                    "url": "/compliance",
                    "style": "primary"
                }
            ]
        })

        return blocks


# Convenience function for scheduled tasks
def send_daily_alerts(db: Session) -> List[NotificationResult]:
    """
    Send daily alert summary (for use in scheduled tasks).

    Reads configuration from settings for recipients.
    """
    alert_manager = AlertManagerService(db)
    notification_service = NotificationService(db)

    summary = alert_manager.get_all_alerts()

    # Get recipients from settings
    email_recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', '').split(',')
    email_recipients = [r.strip() for r in email_recipients if r.strip()]

    send_slack = bool(getattr(settings, 'SLACK_WEBHOOK_URL', None))

    return notification_service.send_daily_summary(
        summary=summary,
        email_recipients=email_recipients,
        send_slack=send_slack
    )
