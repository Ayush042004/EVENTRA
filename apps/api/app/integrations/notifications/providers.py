"""Notification Provider Adapters (In-App, Webhook, Mock)."""
import time
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.integrations.base import NotificationProvider, IntegrationResult, IntegrationSource
from app.models.notification import Notification


class MockNotificationProvider(NotificationProvider):
    """Mock notification provider for unit tests and offline demonstrations."""

    def __init__(self):
        self.sent_notifications: List[Dict[str, Any]] = []

    def send_notification(
        self,
        event_id: str,
        notification_type: str,
        title: str,
        message: str,
        channel: str = "IN_APP",
        recipient: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> IntegrationResult[Dict[str, Any]]:
        record = {
            "event_id": event_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "channel": channel,
            "recipient": recipient,
            "payload": payload or {},
            "timestamp": time.time(),
            "status": "DELIVERED",
        }
        self.sent_notifications.append(record)
        return IntegrationResult(
            data=record,
            source=IntegrationSource.MOCK,
            success=True,
            latency_ms=1.0,
        )

    def clear(self):
        self.sent_notifications.clear()


class InAppNotificationProvider(NotificationProvider):
    """In-app notification provider persisting alerts to PostgreSQL / SQLite database."""

    def __init__(self, db_factory: Optional[Any] = None):
        self.db_factory = db_factory

    def send_notification(
        self,
        event_id: str,
        notification_type: str,
        title: str,
        message: str,
        channel: str = "IN_APP",
        recipient: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> IntegrationResult[Dict[str, Any]]:
        start_time = time.time()
        session = db or (self.db_factory() if callable(self.db_factory) else None)

        record_data = {
            "event_id": event_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "channel": channel,
            "recipient": recipient,
            "payload": payload or {},
            "status": "DELIVERED",
        }

        if session:
            notif = Notification(
                event_id=event_id,
                notification_type=notification_type,
                channel=channel,
                recipient=recipient,
                title=title,
                message=message,
                payload=payload or {},
                status="DELIVERED",
            )
            session.add(notif)
            session.commit()
            session.refresh(notif)
            record_data["id"] = notif.id

        latency = round((time.time() - start_time) * 1000, 2)
        return IntegrationResult(
            data=record_data,
            source=IntegrationSource.REAL if session else IntegrationSource.MOCK,
            success=True,
            latency_ms=latency,
        )


class WebhookNotificationProvider(NotificationProvider):
    """External webhook notification dispatcher with timeout protection."""

    def __init__(self, webhook_url: Optional[str] = None, timeout_seconds: int = 5):
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds
        self._fallback = MockNotificationProvider()

    def send_notification(
        self,
        event_id: str,
        notification_type: str,
        title: str,
        message: str,
        channel: str = "WEBHOOK",
        recipient: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> IntegrationResult[Dict[str, Any]]:
        if not self.webhook_url:
            # Fall back to mock recording if webhook URL not configured
            res = self._fallback.send_notification(
                event_id, notification_type, title, message, channel, recipient, payload
            )
            res.error = "NOTIFICATION_WEBHOOK_URL not configured; captured in fallback."
            return res

        start_time = time.time()
        body = {
            "event_id": event_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "recipient": recipient,
            "payload": payload or {},
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(self.webhook_url, json=body)
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code in (200, 201, 202, 204):
                    return IntegrationResult(
                        data={"status_code": resp.status_code, "delivered": True},
                        source=IntegrationSource.REAL,
                        success=True,
                        latency_ms=latency,
                    )
                else:
                    return IntegrationResult(
                        data=None,
                        source=IntegrationSource.UNAVAILABLE,
                        success=False,
                        error=f"Webhook delivery failed with HTTP {resp.status_code}",
                    )
        except Exception as err:
            return IntegrationResult(
                data=None,
                source=IntegrationSource.UNAVAILABLE,
                success=False,
                error=f"Webhook connection error: {err}",
            )
