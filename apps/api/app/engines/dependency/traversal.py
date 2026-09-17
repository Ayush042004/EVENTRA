"""Deterministic Engine: dependency.traversal

Critical path calculation using forward and backward pass algorithms.
Computes earliest/latest start and finish times, slack, and identifies
critical path tasks.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List
from app.engines.dependency.graph import DependencyGraph


@dataclass
class TaskTiming:
    """Timing analysis result for a single task."""
    task_id: str
    duration: int  # minutes
    earliest_start: int = 0   # minutes from project start
    earliest_finish: int = 0
    latest_start: int = 0
    latest_finish: int = 0
    slack: int = 0            # total float (latest_start - earliest_start)
    is_critical: bool = False


@dataclass
class CriticalPathResult:
    """Complete critical path analysis result."""
    task_timings: Dict[str, TaskTiming] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)  # ordered task IDs on the critical path
    total_duration: int = 0  # total project duration in minutes


class CriticalPathCalculator:
    """Pure deterministic critical path method (CPM) calculator.

    Uses forward pass (earliest times) and backward pass (latest times)
    to compute slack and identify the critical path.
    """

    def calculate(self, graph: DependencyGraph) -> CriticalPathResult:
        """Calculate the critical path for the given dependency graph.

        Args:
            graph: A DependencyGraph with task durations set.

        Returns:
            CriticalPathResult with per-task timings and critical path.

        Raises:
            ValueError: If the graph contains cycles.
        """
        topo_order = graph.topological_sort()  # raises ValueError on cycles

        if not topo_order:
            return CriticalPathResult()

        timings: Dict[str, TaskTiming] = {}

        # Initialize timings
        for task_id in topo_order:
            timings[task_id] = TaskTiming(
                task_id=task_id,
                duration=graph.get_duration(task_id),
            )

        # Forward Pass: compute earliest start and finish
        for task_id in topo_order:
            timing = timings[task_id]
            predecessors = graph.get_predecessors(task_id)

            if predecessors:
                timing.earliest_start = max(
                    timings[pred].earliest_finish + graph.get_lag(pred, task_id)
                    for pred in predecessors
                )

            timing.earliest_finish = timing.earliest_start + timing.duration

        # Project total duration = max earliest_finish across all tasks
        total_duration = max(t.earliest_finish for t in timings.values()) if timings else 0

        # Backward Pass: compute latest start and finish
        for task_id in reversed(topo_order):
            timing = timings[task_id]
            successors = graph.get_successors(task_id)

            if successors:
                timing.latest_finish = min(
                    timings[succ].latest_start - graph.get_lag(task_id, succ)
                    for succ in successors
                )
            else:
                timing.latest_finish = total_duration

            timing.latest_start = timing.latest_finish - timing.duration

        # Calculate slack and identify critical tasks
        for task_id, timing in timings.items():
            timing.slack = timing.latest_start - timing.earliest_start
            timing.is_critical = (timing.slack == 0)

        # Build critical path: critical tasks in topological order
        critical_path = [t for t in topo_order if timings[t].is_critical]

        return CriticalPathResult(
            task_timings=timings,
            critical_path=critical_path,
            total_duration=total_duration,
        )
