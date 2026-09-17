"""EVENTRA Domain Intelligence Package.

Provides deterministic domain contracts, baseline requirements, tasks,
dependencies, and provider categories for specialized event types.
"""
from app.domains.types import (
    EventType,
    DependencyType,
    ObjectivePriority,
    EventStatus,
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
    ProviderCategoryDefinition,
)
from app.domains.base import BaseEventDomain
from app.domains.registry import (
    DomainRegistry,
    get_domain,
    UnsupportedEventTypeException,
)
from app.domains.wedding import WeddingDomain
from app.domains.college_fest import CollegeFestDomain
from app.domains.conference import ConferenceDomain

# Auto-register canonical domain implementations
DomainRegistry.register(WeddingDomain())
DomainRegistry.register(CollegeFestDomain())
DomainRegistry.register(ConferenceDomain())

__all__ = [
    "EventType",
    "DependencyType",
    "ObjectivePriority",
    "EventStatus",
    "RequirementDefinition",
    "TaskDefinition",
    "DependencyDefinition",
    "ProviderCategoryDefinition",
    "BaseEventDomain",
    "DomainRegistry",
    "get_domain",
    "UnsupportedEventTypeException",
    "WeddingDomain",
    "CollegeFestDomain",
    "ConferenceDomain",
]
