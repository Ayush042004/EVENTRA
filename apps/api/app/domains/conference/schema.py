"""Conference Domain Implementation."""
from typing import List
from app.domains.base import BaseEventDomain
from app.models.enums import EventType
from app.domains.types import (
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
)
from app.domains.conference.baseline import (
    CONFERENCE_REQUIREMENTS,
    CONFERENCE_PROVIDER_CATEGORIES,
)
from app.domains.conference.tasks import CONFERENCE_TASKS
from app.domains.conference.dependencies import CONFERENCE_DEPENDENCIES


class ConferenceDomain(BaseEventDomain):
    """Domain intelligence implementation for Conferences."""

    @property
    def event_type(self) -> EventType:
        return EventType.CONFERENCE

    def baseline_requirements(self) -> List[RequirementDefinition]:
        return list(CONFERENCE_REQUIREMENTS)

    def baseline_tasks(self) -> List[TaskDefinition]:
        return list(CONFERENCE_TASKS)

    def baseline_dependencies(self) -> List[DependencyDefinition]:
        return list(CONFERENCE_DEPENDENCIES)

    def provider_categories(self) -> List[str]:
        return list(CONFERENCE_PROVIDER_CATEGORIES)
