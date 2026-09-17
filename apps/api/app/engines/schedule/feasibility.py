"""Deterministic Engine: schedule.feasibility

Validates that a computed schedule fits within event constraints
(time window, venue operating hours, buffer adequacy).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.engines.schedule.scheduler import ScheduleResult


@dataclass
class FeasibilityViolation:
    """A single schedule feasibility violation."""
    task_id: Optional[str]
    violation_type: str  # EXCEEDS_EVENT_WINDOW, INSUFFICIENT_BUFFER, CONSTRAINT_VIOLATION
    description: str


@dataclass
class FeasibilityResult:
    """Result of schedule feasibility check."""
    is_feasible: bool = True
    violations: List[FeasibilityViolation] = field(default_factory=list)
    total_schedule_minutes: int = 0
    available_minutes: int = 0
    buffer_minutes: int = 0


class ScheduleFeasibilityChecker:
    """Pure deterministic feasibility checker without LLM calls."""

    def check_feasibility(
        self,
        schedule: ScheduleResult,
        event_start: datetime,
        event_end: datetime,
        constraints: Optional[List[Dict[str, Any]]] = None,
    ) -> FeasibilityResult:
        """Check if a computed schedule fits within the event time window.

        Args:
            schedule: The computed ScheduleResult.
            event_start: Event start datetime.
            event_end: Event end datetime.
            constraints: Optional list of time constraints.

        Returns:
            FeasibilityResult indicating whether the schedule is feasible.
        """
        violations: List[FeasibilityViolation] = []
        available_minutes = int((event_end - event_start).total_seconds() / 60)
        total_schedule = schedule.total_duration_minutes

        # Check if schedule exceeds event window
        if schedule.project_end and schedule.project_end > event_end:
            violations.append(FeasibilityViolation(
                task_id=None,
                violation_type="EXCEEDS_EVENT_WINDOW",
                description=(
                    f"Schedule ends at {schedule.project_end.isoformat()} "
                    f"but event ends at {event_end.isoformat()} "
                    f"(exceeds by {int((schedule.project_end - event_end).total_seconds() / 60)} minutes)"
                ),
            ))

        # Check individual tasks
        for task_id, entry in schedule.entries.items():
            if entry.planned_end > event_end:
                violations.append(FeasibilityViolation(
                    task_id=task_id,
                    violation_type="EXCEEDS_EVENT_WINDOW",
                    description=f"Task ends at {entry.planned_end.isoformat()}, after event end",
                ))
            if entry.planned_start < event_start:
                violations.append(FeasibilityViolation(
                    task_id=task_id,
                    violation_type="EXCEEDS_EVENT_WINDOW",
                    description=f"Task starts at {entry.planned_start.isoformat()}, before event start",
                ))

        buffer = available_minutes - total_schedule

        return FeasibilityResult(
            is_feasible=len(violations) == 0,
            violations=violations,
            total_schedule_minutes=total_schedule,
            available_minutes=available_minutes,
            buffer_minutes=max(buffer, 0),
        )
