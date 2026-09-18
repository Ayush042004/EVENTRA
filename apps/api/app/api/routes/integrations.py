"""REST API Endpoints: Real-World Integrations"""
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_id, get_db_session
from app.core.config import settings
from app.integrations.registry import registry
from app.services.notification_service import NotificationService
from app.services.provider_communication_service import ProviderCommunicationService

router = APIRouter(tags=["Integrations"])


# --- Schemas ---

class DistanceRequest(BaseModel):
    origin: Union[str, List[float], Dict[str, float]]
    destination: Union[str, List[float], Dict[str, float]]


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=1)


class SendNotificationRequest(BaseModel):
    notification_type: str = Field(..., description="e.g. INCIDENT_DETECTED, APPROVAL_REQUESTED")
    title: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    channel: Optional[str] = "IN_APP"
    recipient: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class ProviderMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    recipient_contact: Optional[str] = None


# --- Endpoints ---

@router.get("/integrations/status")
def get_integrations_status():
    """Returns the operational status of all external integration adapters without exposing credentials."""
    return registry.get_status()


@router.post("/integrations/maps/distance")
def get_map_distance(payload: DistanceRequest):
    """Calculates transit distance and ETA using the active maps adapter."""
    maps = registry.get_maps_provider()
    result = maps.get_distance(payload.origin, payload.destination)
    return result.to_dict()


@router.post("/integrations/maps/geocode")
def geocode_address(payload: GeocodeRequest):
    """Resolves coordinates for an address using the active maps adapter."""
    maps = registry.get_maps_provider()
    result = maps.geocode(payload.address)
    return result.to_dict()


@router.get("/integrations/whatsapp/webhook")
def verify_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """Handles Meta WhatsApp webhook verification challenge."""
    comm = registry.get_communication_provider()
    from app.integrations.whatsapp.client import WhatsAppAdapter
    if isinstance(comm, WhatsAppAdapter) and hub_mode and hub_verify_token:
        if comm.verify_webhook_token(hub_mode, hub_verify_token):
            return Response(content=hub_challenge or "", media_type="text/plain")
    elif hub_mode == "subscribe":
        expected_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN or "eventra_verify_secret"
        if hub_verify_token == expected_token or not settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            return Response(content=hub_challenge or "", media_type="text/plain")
    return Response(content="Verification failed", status_code=status.HTTP_403_FORBIDDEN)


@router.post("/integrations/whatsapp/webhook")
def receive_whatsapp_webhook(payload: Dict[str, Any]):
    """Receives and normalizes inbound webhook message from WhatsApp."""
    comm = registry.get_communication_provider()
    result = comm.receive_inbound(payload)
    return {"status": "PROCESSED", "result": result.to_dict()}


# --- Event Notification Routes ---

@router.post("/events/{event_id}/notifications", status_code=status.HTTP_201_CREATED)
def send_event_notification(
    event_id: str,
    payload: SendNotificationRequest,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Dispatches an operational alert for an event."""
    service = NotificationService(db)
    result = service.send_notification(
        event_id=event_id,
        notification_type=payload.notification_type,
        title=payload.title,
        message=payload.message,
        channel=payload.channel,
        recipient=payload.recipient,
        payload=payload.payload,
    )
    return result.to_dict()


@router.get("/events/{event_id}/notifications")
def list_event_notifications(
    event_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Retrieves notification history for an event."""
    service = NotificationService(db)
    items = service.list_notifications(event_id=event_id, limit=limit)
    return {"total": len(items), "items": items}


# --- Event Provider Messaging Routes ---

@router.post("/events/{event_id}/providers/{provider_id}/messages", status_code=status.HTTP_201_CREATED)
def send_provider_message(
    event_id: str,
    provider_id: str,
    payload: ProviderMessageRequest,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Dispatches an operational message to a vendor/provider."""
    service = ProviderCommunicationService(db)
    result = service.send_message(
        event_id=event_id,
        provider_id=provider_id,
        message=payload.message,
        recipient_contact=payload.recipient_contact,
    )
    return result.to_dict()


@router.get("/events/{event_id}/providers/{provider_id}/messages")
def get_provider_messages(
    event_id: str,
    provider_id: str,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Retrieves message history with a vendor/provider."""
    service = ProviderCommunicationService(db)
    items = service.get_messages(event_id=event_id, provider_id=provider_id)
    return {"total": len(items), "items": items}
