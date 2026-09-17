"""Wedding Domain Implementation."""
from typing import List
from app.domains.base import BaseEventDomain
from app.domains.types import (
    EventType,
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
)
from app.domains.wedding.baseline import (
    WEDDING_REQUIREMENTS,
    WEDDING_PROVIDER_CATEGORIES,
)
from app.domains.wedding.tasks import WEDDING_TASKS
from app.domains.wedding.dependencies import WEDDING_DEPENDENCIES


class WeddingDomain(BaseEventDomain):
    """Domain intelligence implementation for Weddings."""

    @property
    def event_type(self) -> EventType:
        return EventType.WEDDING

    def baseline_requirements(self) -> List[RequirementDefinition]:
        return list(WEDDING_REQUIREMENTS)

    def baseline_tasks(self) -> List[TaskDefinition]:
        return list(WEDDING_TASKS)

    def baseline_dependencies(self) -> List[DependencyDefinition]:
        return list(WEDDING_DEPENDENCIES)

    def provider_categories(self) -> List[str]:
        return list(WEDDING_PROVIDER_CATEGORIES)
