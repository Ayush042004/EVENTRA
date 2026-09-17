"""Unit tests for domain baseline dependency validation."""
import pytest
from typing import List
from app.domains.base import BaseEventDomain
from app.domains.types import (
    EventType,
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
    DependencyType,
    ObjectivePriority,
)


class MockDomain(BaseEventDomain):
    """Mock domain for isolating edge case validation testing."""
    def __init__(
        self,
        tasks: List[TaskDefinition],
        dependencies: List[DependencyDefinition],
    ):
        self._tasks = tasks
        self._dependencies = dependencies

    @property
    def event_type(self) -> EventType:
        return EventType.WEDDING

    def baseline_requirements(self) -> List[RequirementDefinition]:
        return []

    def baseline_tasks(self) -> List[TaskDefinition]:
        return self._tasks

    def baseline_dependencies(self) -> List[DependencyDefinition]:
        return self._dependencies

    def provider_categories(self) -> List[str]:
        return ["VENUE"]


def test_valid_dependency_passes():
    tasks = [
        TaskDefinition(key="task.a", name="Task A"),
        TaskDefinition(key="task.b", name="Task B"),
    ]
    deps = [
        DependencyDefinition(
            predecessor_key="task.a",
            successor_key="task.b",
            dependency_type=DependencyType.FINISH_TO_START,
        )
    ]
    domain = MockDomain(tasks, deps)
    # Should pass without error
    domain.validate_baseline()


def test_unknown_predecessor_rejected():
    tasks = [
        TaskDefinition(key="task.b", name="Task B"),
    ]
    deps = [
        DependencyDefinition(
            predecessor_key="task.unknown",
            successor_key="task.b",
        )
    ]
    domain = MockDomain(tasks, deps)
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()
    assert "predecessor task 'task.unknown' does not exist" in str(exc_info.value)


def test_unknown_successor_rejected():
    tasks = [
        TaskDefinition(key="task.a", name="Task A"),
    ]
    deps = [
        DependencyDefinition(
            predecessor_key="task.a",
            successor_key="task.unknown",
        )
    ]
    domain = MockDomain(tasks, deps)
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()
    assert "successor task 'task.unknown' does not exist" in str(exc_info.value)


def test_self_dependency_rejected():
    tasks = [
        TaskDefinition(key="task.a", name="Task A"),
    ]
    deps = [
        DependencyDefinition(
            predecessor_key="task.a",
            successor_key="task.a",
        )
    ]
    domain = MockDomain(tasks, deps)
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()
    assert "Self-dependency rejected" in str(exc_info.value)


def test_duplicate_dependency_edge_rejected():
    tasks = [
        TaskDefinition(key="task.a", name="Task A"),
        TaskDefinition(key="task.b", name="Task B"),
    ]
    deps = [
        DependencyDefinition(
            predecessor_key="task.a",
            successor_key="task.b",
            dependency_type=DependencyType.FINISH_TO_START,
        ),
        DependencyDefinition(
            predecessor_key="task.a",
            successor_key="task.b",
            dependency_type=DependencyType.FINISH_TO_START,
        ),
    ]
    domain = MockDomain(tasks, deps)
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()
    assert "Duplicate dependency edge" in str(exc_info.value)


def test_duplicate_task_keys_rejected():
    tasks = [
        TaskDefinition(key="task.dup", name="Task 1"),
        TaskDefinition(key="task.dup", name="Task 2"),
    ]
    deps = []
    domain = MockDomain(tasks, deps)
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()
    assert "duplicate task keys" in str(exc_info.value)
