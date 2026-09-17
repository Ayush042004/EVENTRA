"""Deterministic Engine: state.transitions

Pre-flight validation for lifecycle transitions, ensuring
preconditions are met before state changes.
"""
from typing import Any, List
from app.models.enums import EventLifecycleState, TaskStatus


class TransitionValidator:
    """Pure deterministic transition precondition validator.

    Validates that events meet readiness criteria before
    lifecycle state transitions (e.g., go-live).
    """

    def validate_go_live_readiness(
        self,
        event: Any,
        tasks: List[Any],
    ) -> List[str]:
        """Check if an event is ready to go live.

        Validates:
        1. Event is in PLANNED state
        2. At least one task exists
        3. All tasks have planned_start and planned_end set
        4. No tasks are in FAILED or CANCELLED status

        Args:
            event: The Event ORM object or dict.
            tasks: List of Task ORM objects or dicts.

        Returns:
            List of validation failure messages. Empty = ready.
        """
        failures: List[str] = []

        # Check lifecycle state
        lifecycle_state = (
            event.get("lifecycle_state") if isinstance(event, dict)
            else getattr(event, "lifecycle_state", None)
        )
        if lifecycle_state != EventLifecycleState.PLANNED.value:
            failures.append(
                f"Event must be in PLANNED state to go live (current: {lifecycle_state})"
            )

        # Check tasks exist
        if not tasks:
            failures.append("Event has no planned tasks — cannot go live without a plan")

        # Validate each task
        for task in tasks:
            if isinstance(task, dict):
                name = task.get("name", "unknown")
                planned_start = task.get("planned_start")
                planned_end = task.get("planned_end")
                status = task.get("status", "")
            else:
                name = getattr(task, "name", "unknown")
                planned_start = getattr(task, "planned_start", None)
                planned_end = getattr(task, "planned_end", None)
                status = getattr(task, "status", "")

            if not planned_start or not planned_end:
                failures.append(f"Task '{name}' missing planned schedule (start/end not set)")

            if status in (TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
                failures.append(f"Task '{name}' is in {status} status — resolve before go-live")

        return failures

    def validate_conclude_readiness(
        self,
        event: Any,
        tasks: List[Any],
    ) -> List[str]:
        """Check if an event is ready to conclude.

        Validates:
        1. Event is in LIVE state
        2. No tasks are in IN_PROGRESS or BLOCKED status

        Returns:
            List of validation failure messages. Empty = ready.
        """
        failures: List[str] = []

        lifecycle_state = (
            event.get("lifecycle_state") if isinstance(event, dict)
            else getattr(event, "lifecycle_state", None)
        )
        if lifecycle_state != EventLifecycleState.LIVE.value:
            failures.append(
                f"Event must be in LIVE state to conclude (current: {lifecycle_state})"
            )

        active_statuses = {TaskStatus.IN_PROGRESS.value, TaskStatus.BLOCKED.value}
        for task in tasks:
            if isinstance(task, dict):
                name = task.get("name", "unknown")
                status = task.get("status", "")
            else:
                name = getattr(task, "name", "unknown")
                status = getattr(task, "status", "")

            if status in active_statuses:
                failures.append(f"Task '{name}' is still {status} — complete or cancel before concluding")

        return failures
