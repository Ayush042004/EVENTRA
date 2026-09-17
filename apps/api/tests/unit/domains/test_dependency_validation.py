"""Unit tests for baseline dependency validation rules."""
import pytest
from app.domains.base import BaseEventDomain
from app.domains.types import (
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
)
from app.models.enums import DependencyType, TaskPriority


class MockDomain(BaseEventDomain):
    """Configurable mock domain for testing baseline validation edge cases."""

    def __init__(self, tasks=None, dependencies=None):
        self._tasks = tasks or []
        self._dependencies = dependencies or []

    @property
    def event_type(self) -> str:
        return "MOCK_DOMAIN"

    def baseline_requirements(self):
        return [
            RequirementDefinition(
                key="mock.req",
                category="GENERAL",
                name="Mock Requirement",
                is_mandatory=True,
            )
        ]

    def baseline_tasks(self):
        return self._tasks

    def baseline_dependencies(self):
        return self._dependencies

    def provider_categories(self):
        return ["general"]


def test_valid_domain_dependencies():
    """Verify clean tasks and valid dependency passes validation without error."""
    t1 = TaskDefinition(key="task.a", name="Task A", priority=TaskPriority.HIGH)
    t2 = TaskDefinition(key="task.b", name="Task B", priority=TaskPriority.MEDIUM)
    dep = DependencyDefinition(
        predecessor_key="task.a",
        successor_key="task.b",
        dependency_type=DependencyType.FINISH_TO_START,
        lag_minutes=10,
    )

    domain = MockDomain(tasks=[t1, t2], dependencies=[dep])
    # Should not raise
    domain.validate_baseline()


def test_self_dependency_rejected():
    """Verify that a task depending on itself is rejected with a ValueError."""
    t1 = TaskDefinition(key="task.a", name="Task A")
    dep = DependencyDefinition(
        predecessor_key="task.a",
        successor_key="task.a",
        dependency_type=DependencyType.FINISH_TO_START,
    )

    domain = MockDomain(tasks=[t1], dependencies=[dep])
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()

    assert "Self-dependency rejected" in str(exc_info.value)
    assert "task.a" in str(exc_info.value)


def test_unknown_predecessor_rejected():
    """Verify that a dependency referencing a non-existent predecessor is rejected."""
    t1 = TaskDefinition(key="task.valid", name="Valid Task")
    dep = DependencyDefinition(
        predecessor_key="task.non_existent",
        successor_key="task.valid",
        dependency_type=DependencyType.FINISH_TO_START,
    )

    domain = MockDomain(tasks=[t1], dependencies=[dep])
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()

    assert "predecessor task 'task.non_existent' does not exist" in str(exc_info.value)


def test_unknown_successor_rejected():
    """Verify that a dependency referencing a non-existent successor is rejected."""
    t1 = TaskDefinition(key="task.valid", name="Valid Task")
    dep = DependencyDefinition(
        predecessor_key="task.valid",
        successor_key="task.ghost",
        dependency_type=DependencyType.FINISH_TO_START,
    )

    domain = MockDomain(tasks=[t1], dependencies=[dep])
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()

    assert "successor task 'task.ghost' does not exist" in str(exc_info.value)


def test_duplicate_dependency_edge_rejected():
    """Verify that duplicate edges between same tasks with same type are rejected."""
    t1 = TaskDefinition(key="task.1", name="Task 1")
    t2 = TaskDefinition(key="task.2", name="Task 2")
    dep1 = DependencyDefinition(
        predecessor_key="task.1",
        successor_key="task.2",
        dependency_type=DependencyType.FINISH_TO_START,
    )
    dep2 = DependencyDefinition(
        predecessor_key="task.1",
        successor_key="task.2",
        dependency_type=DependencyType.FINISH_TO_START,
    )

    domain = MockDomain(tasks=[t1, t2], dependencies=[dep1, dep2])
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()

    assert "Duplicate dependency edge" in str(exc_info.value)
    assert "from 'task.1' to 'task.2'" in str(exc_info.value)


def test_duplicate_task_keys_rejected():
    """Verify that duplicate task keys in baseline tasks are rejected."""
    t1 = TaskDefinition(key="task.duplicate", name="Task Version 1")
    t2 = TaskDefinition(key="task.duplicate", name="Task Version 2")

    domain = MockDomain(tasks=[t1, t2], dependencies=[])
    with pytest.raises(ValueError) as exc_info:
        domain.validate_baseline()

    assert "contains duplicate task keys" in str(exc_info.value)
    assert "task.duplicate" in str(exc_info.value)
