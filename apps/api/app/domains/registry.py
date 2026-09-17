"""Central Domain Registry and factory for event type resolution."""
from typing import Dict, List, Union
from app.domains.base import BaseEventDomain
from app.domains.types import EventType


class UnsupportedEventTypeException(ValueError):
    """Raised when an unsupported or unregistered event type is requested."""
    def __init__(self, event_type: str, supported: List[str]):
        super().__init__(
            f"Unsupported event type '{event_type}'. Supported domain types are: {', '.join(supported)}"
        )
        self.event_type = event_type
        self.supported = supported


class DomainRegistry:
    """Singleton registry mapping event types to domain implementations."""

    _domains: Dict[str, BaseEventDomain] = {}

    @classmethod
    def register(cls, domain: BaseEventDomain) -> None:
        """Register a domain implementation instance."""
        # Also run structural self-validation upon registration
        domain.validate_baseline()
        raw_key = domain.event_type
        key = (raw_key.value if hasattr(raw_key, "value") else str(raw_key)).upper()
        cls._domains[key] = domain

    @classmethod
    def get(cls, event_type: Union[EventType, str]) -> BaseEventDomain:
        """Retrieve the domain handler for a given event type."""
        normalized_key = (event_type.value if isinstance(event_type, EventType) else str(event_type)).upper()
        if normalized_key not in cls._domains:
            supported = list(cls._domains.keys())
            raise UnsupportedEventTypeException(normalized_key, supported)
        return cls._domains[normalized_key]

    @classmethod
    def list_supported_event_types(cls) -> List[str]:
        """Return list of supported event type keys."""
        return list(cls._domains.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear registry (useful for test resets)."""
        cls._domains.clear()


def get_domain(event_type: Union[EventType, str]) -> BaseEventDomain:
    """Convenience function to resolve domain by event type."""
    return DomainRegistry.get(event_type)
