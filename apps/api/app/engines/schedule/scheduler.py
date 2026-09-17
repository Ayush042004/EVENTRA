"""Deterministic Engine: schedule.scheduler

Forward-pass schedule engine that assigns concrete planned_start/planned_end
datetimes to tasks using topological order and dependency constraints.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from app.engines.dependency.graph import DependencyGraph


@dataclass
class TaskScheduleEntry:
    """Scheduled datetime assignment for a single task."""
    task_id: str
    planned_start: datetime
    planned_end: datetime
    duration_minutes: int


@dataclass
class ScheduleResult:
    """Complete schedule assignment result."""
    entries: Dict[str, TaskScheduleEntry] = field(default_factory=dict)
    project_end: Optional[datetime] = None
    total_duration_minutes: int = 0


class ScheduleEngine:
    """Pure deterministic scheduling engine without LLM calls.

    Assigns concrete datetimes to tasks using forward-pass scheduling
    from the event start time, respecting dependency order and lag.
    """

    def schedule_tasks(
        self,
        event_start: datetime,
        tasks: List[Any],
        dependencies: List[Any],
        default_duration: int = 30,
    ) -> ScheduleResult:
        """Assign planned_start and planned_end datetimes to all tasks.

        Uses topological ordering to ensure predecessors are scheduled
        before successors. Each task starts at max(predecessor_finish + lag).

        Args:
            event_start: The event's start datetime.
            tasks: List of task objects/dicts.
            dependencies: List of dependency objects/dicts.
            default_duration: Default task duration in minutes if not specified.

        Returns:
            ScheduleResult with concrete datetime assignments.
        """
        graph = DependencyGraph.from_tasks_and_dependencies(tasks, dependencies)
        topo_order = graph.topological_sort()

        entries: Dict[str, TaskScheduleEntry] = {}

        for task_id in topo_order:
            duration = graph.get_duration(task_id) or default_duration
            predecessors = graph.get_predecessors(task_id)

            if predecessors:
                # Start after all predecessors finish (+ lag)
                start = max(
                    entries[pred].planned_end + timedelta(minutes=graph.get_lag(pred, task_id))
                    for pred in predecessors
                    if pred in entries
                )
            else:
                start = event_start

            end = start + timedelta(minutes=duration)

            entries[task_id] = TaskScheduleEntry(
                task_id=task_id,
                planned_start=start,
                planned_end=end,
                duration_minutes=duration,
            )

        # Project end = latest planned_end
        project_end = max(
            (e.planned_end for e in entries.values()), default=event_start
        )
        total_duration = int((project_end - event_start).total_seconds() / 60)

        return ScheduleResult(
            entries=entries,
            project_end=project_end,
            total_duration_minutes=total_duration,
        )
