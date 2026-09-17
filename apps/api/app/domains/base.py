"""Base Domain Interface and validation contract."""
from abc import ABC, abstractmethod
from typing import List, Set, Tuple
from app.domains.types import (
    EventType,
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
)


class BaseEventDomain(ABC):
    """Abstract base contract for event domain operational intelligence."""

    @property
    @abstractmethod
    def event_type(self) -> EventType:
        """The specific EventType handled by this domain."""
        pass

    @abstractmethod
    def baseline_requirements(self) -> List[RequirementDefinition]:
        """Return the deterministic list of baseline requirements for this domain."""
        pass

    @abstractmethod
    def baseline_tasks(self) -> List[TaskDefinition]:
        """Return the deterministic list of baseline tasks for this domain."""
        pass

    @abstractmethod
    def baseline_dependencies(self) -> List[DependencyDefinition]:
        """Return the deterministic list of baseline dependencies between tasks."""
        pass

    @abstractmethod
    def provider_categories(self) -> List[str]:
        """Return the list of standard provider/vendor categories for this domain."""
        pass

    def validate_baseline(self) -> None:
        """Validate structural integrity of domain baseline definitions.
        
        Checks:
        1. All dependency predecessor keys exist in baseline tasks.
        2. All dependency successor keys exist in baseline tasks.
        3. No self-dependencies (predecessor cannot equal successor).
        4. No duplicate dependency edges.
        """
        tasks = self.baseline_tasks()
        dependencies = self.baseline_dependencies()

        task_keys: Set[str] = {t.key for t in tasks}

        # Check for unique task keys
        if len(task_keys) != len(tasks):
            seen: Set[str] = set()
            duplicates = [t.key for t in tasks if t.key in seen or seen.add(t.key)]
            raise ValueError(f"Domain {self.event_type} contains duplicate task keys: {duplicates}")

        seen_dependencies: Set[Tuple[str, str, str]] = set()

        for dep in dependencies:
            # Self-dependency check
            if dep.predecessor_key == dep.successor_key:
                raise ValueError(
                    f"Self-dependency rejected in domain {self.event_type}: task '{dep.predecessor_key}' cannot depend on itself"
                )

            # Predecessor existence check
            if dep.predecessor_key not in task_keys:
                raise ValueError(
                    f"Invalid dependency in domain {self.event_type}: predecessor task '{dep.predecessor_key}' does not exist"
                )

            # Successor existence check
            if dep.successor_key not in task_keys:
                raise ValueError(
                    f"Invalid dependency in domain {self.event_type}: successor task '{dep.successor_key}' does not exist"
                )

            # Duplicate dependency edge check
            dep_tuple = (dep.predecessor_key, dep.successor_key, str(dep.dependency_type))
            if dep_tuple in seen_dependencies:
                raise ValueError(
                    f"Duplicate dependency edge in domain {self.event_type}: from '{dep.predecessor_key}' to '{dep.successor_key}' with type '{dep.dependency_type}'"
                )
            seen_dependencies.add(dep_tuple)
