"""Deterministic Engine: schedule.adjustment

Propagates schedule adjustments (delays) downstream through the dependency graph.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from app.engines.dependency.graph import DependencyGraph
from app.engines.schedule.scheduler import ScheduleResult, TaskScheduleEntry


@dataclass
class AdjustedSchedule:
    """Result of a schedule adjustment due to a delay."""
    affected_tasks: List[str] = field(default_factory=list)  # task IDs with changed times
    entries: Dict[str, TaskScheduleEntry] = field(default_factory=dict)
    total_delay_minutes: int = 0
    new_project_end: Optional[datetime] = None


class ScheduleAdjuster:
    """Pure deterministic schedule adjustment engine.

    Propagates delays downstream through the dependency graph.
    """

    def adjust_for_delay(
        self,
        task_id: str,
        delay_minutes: int,
        graph: DependencyGraph,
        schedule: ScheduleResult,
    ) -> AdjustedSchedule:
        """Propagate a delay on a specific task through the dependency graph.

        Args:
            task_id: The task experiencing the delay.
            delay_minutes: The delay amount in minutes.
            graph: The dependency graph.
            schedule: The current schedule.

        Returns:
            AdjustedSchedule with updated task timings.
        """
        if task_id not in schedule.entries:
            raise ValueError(f"Task '{task_id}' not found in schedule")

        # Copy current schedule entries
        adjusted: Dict[str, TaskScheduleEntry] = {}
        for tid, entry in schedule.entries.items():
            adjusted[tid] = TaskScheduleEntry(
                task_id=entry.task_id,
                planned_start=entry.planned_start,
                planned_end=entry.planned_end,
                duration_minutes=entry.duration_minutes,
            )

        # Apply delay to the source task
        delay = timedelta(minutes=delay_minutes)
        source = adjusted[task_id]
        source.planned_end = source.planned_end + delay
        affected: List[str] = [task_id]

        # Propagate downstream using topological order
        topo = graph.topological_sort()
        # Only process tasks that come after the delayed task
        start_idx = topo.index(task_id) + 1

        for i in range(start_idx, len(topo)):
            tid = topo[i]
            predecessors = graph.get_predecessors(tid)

            if predecessors:
                new_start = max(
                    adjusted[pred].planned_end + timedelta(minutes=graph.get_lag(pred, tid))
                    for pred in predecessors
                    if pred in adjusted
                )

                current = adjusted[tid]
                if new_start > current.planned_start:
                    shift = new_start - current.planned_start
                    current.planned_start = new_start
                    current.planned_end = new_start + timedelta(minutes=current.duration_minutes)
                    affected.append(tid)

        new_project_end = max(
            (e.planned_end for e in adjusted.values()), default=schedule.project_end
        )

        total_delay = 0
        if new_project_end and schedule.project_end:
            total_delay = int((new_project_end - schedule.project_end).total_seconds() / 60)

        return AdjustedSchedule(
            affected_tasks=affected,
            entries=adjusted,
            total_delay_minutes=max(total_delay, 0),
            new_project_end=new_project_end,
        )
