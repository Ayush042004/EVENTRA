"""College Fest Domain Implementation."""
from typing import List
from app.domains.base import BaseEventDomain
from app.domains.types import (
    EventType,
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
)
from app.domains.college_fest.baseline import (
    COLLEGE_FEST_REQUIREMENTS,
    COLLEGE_FEST_PROVIDER_CATEGORIES,
)
from app.domains.college_fest.tasks import COLLEGE_FEST_TASKS
from app.domains.college_fest.dependencies import COLLEGE_FEST_DEPENDENCIES


class CollegeFestDomain(BaseEventDomain):
    """Domain intelligence implementation for College Festivals."""

    @property
    def event_type(self) -> EventType:
        return EventType.COLLEGE_FEST

    def baseline_requirements(self) -> List[RequirementDefinition]:
        return list(COLLEGE_FEST_REQUIREMENTS)

    def baseline_tasks(self) -> List[TaskDefinition]:
        return list(COLLEGE_FEST_TASKS)

    def baseline_dependencies(self) -> List[DependencyDefinition]:
        return list(COLLEGE_FEST_DEPENDENCIES)

    def provider_categories(self) -> List[str]:
        return list(COLLEGE_FEST_PROVIDER_CATEGORIES)
