"""WhatsApp Business API Adapter.

Isolates external WhatsApp communication behind ProviderCommunicationProvider.
Falls back safely to MockCommunicationProvider when unconfigured.
"""
import time
import uuid
from typing import Any, Dict, List, Optional
import httpx

from app.integrations.base import ProviderCommunicationProvider, IntegrationResult, IntegrationSource
from app.integrations.communication.mock import MockCommunicationProvider


class WhatsAppAdapter(ProviderCommunicationProvider):
    """WhatsApp integration adapter supporting outbound templates and inbound webhooks."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        verify_token: Optional[str] = None,
        timeout_seconds: int = 5,
    ):
        self.api_token = api_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.timeout_seconds = timeout_seconds
        self._fallback = MockCommunicationProvider()

    def send_message(
        self,
        event_id: str,
        provider_id: str,
        message: str,
        recipient_contact: Optional[str] = None,
    ) -> IntegrationResult[Dict[str, Any]]:
        # If credentials are not configured, fall back safely to mock
        if not self.api_token or not self.phone_number_id:
            res = self._fallback.send_message(event_id, provider_id, message, recipient_contact)
            res.error = "WHATSAPP_API_TOKEN or PHONE_NUMBER_ID not configured; captured in fallback."
            return res

        start_time = time.time()
        url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_contact or "",
            "type": "text",
            "text": {"body": message},
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(url, headers=headers, json=payload)
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    record = {
                        "id": data.get("messages", [{}])[0].get("id", str(uuid.uuid4())),
                        "event_id": event_id,
                        "provider_id": provider_id,
                        "message": message,
                        "direction": "OUTBOUND",
                        "channel": "WHATSAPP",
                        "status": "SENT",
                        "timestamp": time.time(),
                    }
                    return IntegrationResult(
                        data=record,
                        source=IntegrationSource.REAL,
                        success=True,
                        latency_ms=latency,
                    )
                else:
                    return IntegrationResult(
                        data=None,
                        source=IntegrationSource.UNAVAILABLE,
                        success=False,
                        error=f"WhatsApp dispatch failed with HTTP {resp.status_code}: {resp.text[:100]}",
                    )
        except Exception as err:
            return IntegrationResult(
                data=None,
                source=IntegrationSource.UNAVAILABLE,
                success=False,
                error=f"WhatsApp network failure: {err}",
            )

    def get_messages(
        self,
        event_id: str,
        provider_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._fallback.get_messages(event_id, provider_id)

    def receive_inbound(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
    ) -> IntegrationResult[Dict[str, Any]]:
        # Normalize WhatsApp webhook structure: entry -> changes -> value -> messages
        try:
            entry = payload.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            val = change.get("value", {})
            msgs = val.get("messages", [])

            if msgs:
                raw_msg = msgs[0]
                sender = raw_msg.get("from")
                text = raw_msg.get("text", {}).get("body", "")
                msg_id = raw_msg.get("id", str(uuid.uuid4()))

                normalized = {
                    "id": msg_id,
                    "sender": sender,
                    "message": text,
                    "direction": "INBOUND",
                    "channel": "WHATSAPP",
                    "timestamp": time.time(),
                }
                return IntegrationResult(
                    data=normalized,
                    source=IntegrationSource.REAL,
                    success=True,
                    latency_ms=1.0,
                )
        except Exception:
            pass

        # Fallback to general inbound handler
        return self._fallback.receive_inbound(payload, signature)

    def verify_webhook_token(self, mode: str, token: str) -> bool:
        """Validates the hub.verify_token during WhatsApp webhook registration."""
        if not self.verify_token:
            return True
        return mode == "subscribe" and token == self.verify_token
