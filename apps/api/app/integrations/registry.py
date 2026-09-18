"""Integration Registry: Central factory and health inspection for external adapters."""
from typing import Any, Dict, Optional
from app.core.config import settings
from app.integrations.base import (
    MapProvider,
    NotificationProvider,
    ProviderCommunicationProvider,
    VenueDirectoryProvider,
    ProviderDirectoryProvider,
)
from app.integrations.maps.mock import MockMapsProvider
from app.integrations.maps.http_maps import HTTPMapsProvider
from app.integrations.notifications.providers import (
    InAppNotificationProvider,
    WebhookNotificationProvider,
    MockNotificationProvider,
)
from app.integrations.communication.mock import MockCommunicationProvider
from app.integrations.whatsapp.client import WhatsAppAdapter
from app.integrations.venues.discovery import ExternalVenueAdapter
from app.integrations.providers.directory import ExternalProviderAdapter
from app.integrations.llm.base import LLMProvider, get_configured_llm_provider


class IntegrationRegistry:
    """Central registry and factory for all Phase 12 real-world integration adapters."""

    def __init__(self):
        self._maps_provider: Optional[MapProvider] = None
        self._notification_provider: Optional[NotificationProvider] = None
        self._communication_provider: Optional[ProviderCommunicationProvider] = None
        self._venue_provider: Optional[VenueDirectoryProvider] = None
        self._provider_directory: Optional[ProviderDirectoryProvider] = None
        self._llm_provider: Optional[LLMProvider] = None

    def get_maps_provider(self) -> MapProvider:
        if not self._maps_provider:
            provider_type = (settings.MAP_PROVIDER or "mock").lower()
            if provider_type != "mock" and settings.MAPS_API_KEY:
                self._maps_provider = HTTPMapsProvider(
                    api_key=settings.MAPS_API_KEY,
                    timeout_seconds=settings.MAPS_TIMEOUT_SECONDS,
                )
            else:
                self._maps_provider = MockMapsProvider()
        return self._maps_provider

    def get_notification_provider(self) -> NotificationProvider:
        if not self._notification_provider:
            provider_type = (settings.NOTIFICATION_PROVIDER or "in_app").lower()
            if provider_type == "webhook" and settings.NOTIFICATION_WEBHOOK_URL:
                self._notification_provider = WebhookNotificationProvider(
                    webhook_url=settings.NOTIFICATION_WEBHOOK_URL,
                )
            elif provider_type == "mock":
                self._notification_provider = MockNotificationProvider()
            else:
                self._notification_provider = InAppNotificationProvider()
        return self._notification_provider

    def get_communication_provider(self) -> ProviderCommunicationProvider:
        if not self._communication_provider:
            comm_type = (settings.COMMUNICATION_PROVIDER or "mock").lower()
            if (comm_type == "whatsapp" or settings.WHATSAPP_ENABLED) and settings.WHATSAPP_API_TOKEN:
                self._communication_provider = WhatsAppAdapter(
                    api_token=settings.WHATSAPP_API_TOKEN,
                    phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
                    verify_token=settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
                )
            else:
                self._communication_provider = MockCommunicationProvider()
        return self._communication_provider

    def get_venue_provider(self) -> VenueDirectoryProvider:
        if not self._venue_provider:
            self._venue_provider = ExternalVenueAdapter()
        return self._venue_provider

    def get_provider_directory(self) -> ProviderDirectoryProvider:
        if not self._provider_directory:
            self._provider_directory = ExternalProviderAdapter()
        return self._provider_directory

    def get_llm_provider(self) -> LLMProvider:
        if not self._llm_provider:
            self._llm_provider = get_configured_llm_provider()
        return self._llm_provider

    def get_status(self) -> Dict[str, Any]:
        """Provides operational status of external integrations without leaking secrets."""
        maps_prov = self.get_maps_provider()
        notif_prov = self.get_notification_provider()
        comm_prov = self.get_communication_provider()

        return {
            "maps": {
                "provider": settings.MAP_PROVIDER,
                "mode": "REAL" if not isinstance(maps_prov, MockMapsProvider) and settings.MAPS_API_KEY else "MOCK",
                "is_configured": bool(settings.MAPS_API_KEY),
                "timeout_seconds": settings.MAPS_TIMEOUT_SECONDS,
            },
            "notifications": {
                "provider": settings.NOTIFICATION_PROVIDER,
                "mode": "REAL" if settings.NOTIFICATION_PROVIDER in ("in_app", "webhook") else "MOCK",
                "is_configured": bool(settings.NOTIFICATION_WEBHOOK_URL or settings.NOTIFICATION_PROVIDER == "in_app"),
            },
            "communication": {
                "provider": settings.COMMUNICATION_PROVIDER,
                "mode": "REAL" if isinstance(comm_prov, WhatsAppAdapter) and settings.WHATSAPP_API_TOKEN else "MOCK",
                "whatsapp_enabled": settings.WHATSAPP_ENABLED,
                "is_configured": bool(settings.WHATSAPP_API_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID),
            },
            "llm": {
                "provider": settings.LLM_PROVIDER,
                "model": settings.LLM_MODEL,
                "mode": "REAL" if settings.LLM_PROVIDER != "mock" and settings.LLM_API_KEY else "MOCK",
                "is_configured": bool(settings.LLM_API_KEY),
                "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
            },
        }


# Global registry singleton
registry = IntegrationRegistry()
