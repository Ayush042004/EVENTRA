"""Domain Service: NotificationService

Coordinates operational alert lifecycles and dispatches notifications through configured integration providers.
CRITICAL INVARIANT: Notifications are outputs. They NEVER modify authoritative event operational state.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.integrations.registry import registry
from app.integrations.base import IntegrationResult
from app.observability.audit import AuditRecorder


class NotificationService:
    """Dispatches operational alerts and tracks notification delivery."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._provider = registry.get_notification_provider()
        self._audit = AuditRecorder(db) if db else None

    def send_notification(
        self,
        event_id: str,
        notification_type: str,
        title: str,
        message: str,
        channel: Optional[str] = None,
        recipient: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = "system",
        actor_type: Optional[str] = "SYSTEM",
    ) -> IntegrationResult[Dict[str, Any]]:
        """Dispatches an operational notification through the active integration adapter."""
        ch = channel or "IN_APP"
        result = self._provider.send_notification(
            event_id=event_id,
            notification_type=notification_type,
            title=title,
            message=message,
            channel=ch,
            recipient=recipient,
            payload=payload,
        )

        # Record in DB if using in-app or if session provided
        if self.db and ch == "IN_APP" and result.success and not result.data.get("id"):
            notif = Notification(
                event_id=event_id,
                notification_type=notification_type,
                channel=ch,
                recipient=recipient,
                title=title,
                message=message,
                payload=payload or {},
                status="DELIVERED",
            )
            self.db.add(notif)
            self.db.commit()
            self.db.refresh(notif)
            result.data["id"] = notif.id

        # Audit notification dispatch
        if self._audit:
            self._audit.record(
                event_id=event_id,
                actor_id=actor_id or "system",
                actor_type=actor_type or "SYSTEM",
                action="NOTIFICATION_SENT",
                action_type="COMMUNICATION",
                target_type="NOTIFICATION",
                target_id=result.data.get("id") if result.data else None,
                after_state={
                    "notification_type": notification_type,
                    "channel": ch,
                    "recipient": recipient,
                    "title": title,
                    "success": result.success,
                },
            )

        return result

    def notify_incident(self, event_id: str, incident: Dict[str, Any]) -> IntegrationResult[Dict[str, Any]]:
        title = f"Operational Incident: {incident.get('title', 'Disruption')}"
        msg = f"Severity {incident.get('severity', 'HIGH')} incident detected. Impact analysis in progress."
        return self.send_notification(
            event_id=event_id,
            notification_type="INCIDENT_DETECTED",
            title=title,
            message=msg,
            payload=incident,
        )

    def notify_risk_escalation(self, event_id: str, risk: Dict[str, Any]) -> IntegrationResult[Dict[str, Any]]:
        score = risk.get("composite_score") or risk.get("score", "EVALUATED")
        level = risk.get("level", "HIGH")
        return self.send_notification(
            event_id=event_id,
            notification_type="RISK_ESCALATED",
            title=f"Operational Risk Escalated to {level}",
            message=f"Event risk score evaluated at {score}. Corrective recovery required.",
            payload=risk,
        )

    def notify_approval_requested(self, event_id: str, approval: Dict[str, Any]) -> IntegrationResult[Dict[str, Any]]:
        appr_id = approval.get("id", "N/A")
        action_type = approval.get("action_type", "Operational Action")
        return self.send_notification(
            event_id=event_id,
            notification_type="APPROVAL_REQUESTED",
            title=f"Approval Required: {action_type}",
            message=f"Ticket {appr_id} requires human organizer sign-off under event governance.",
            payload=approval,
        )

    def notify_action_executed(self, event_id: str, action: Dict[str, Any]) -> IntegrationResult[Dict[str, Any]]:
        action_id = action.get("action_id") or action.get("id", "N/A")
        return self.send_notification(
            event_id=event_id,
            notification_type="ACTION_EXECUTED",
            title=f"Action Executed: {action.get('action_type', 'Action')}",
            message=f"Operational mutation {action_id} successfully executed in database.",
            payload=action,
        )

    def notify_verification_completed(self, event_id: str, verification: Dict[str, Any]) -> IntegrationResult[Dict[str, Any]]:
        ver_status = verification.get("status", "VERIFIED")
        return self.send_notification(
            event_id=event_id,
            notification_type="VERIFICATION_COMPLETED",
            title=f"Recovery Verification: {ver_status}",
            message=f"Post-action operational verification finished with status {ver_status}.",
            payload=verification,
        )

    def notify_recovery_failed(self, event_id: str, error_message: str) -> IntegrationResult[Dict[str, Any]]:
        return self.send_notification(
            event_id=event_id,
            notification_type="RECOVERY_FAILED",
            title="Operational Recovery Failed",
            message=f"Automated recovery could not restore event state: {error_message}",
            payload={"error": error_message},
        )

    def list_notifications(self, event_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Queries stored notifications for an event."""
        if not self.db:
            return []
        items = (
            self.db.query(Notification)
            .filter(Notification.event_id == event_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": n.id,
                "event_id": n.event_id,
                "notification_type": n.notification_type,
                "channel": n.channel,
                "recipient": n.recipient,
                "title": n.title,
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ]
