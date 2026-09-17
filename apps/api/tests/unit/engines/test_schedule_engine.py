"""Unit tests for Schedule Engine components.

Tests forward-pass task scheduling, feasibility checks against event windows,
and downstream delay propagation.
"""
from datetime import datetime, timedelta
import pytest

from app.engines.dependency.graph import DependencyGraph
from app.engines.schedule.scheduler import ScheduleEngine
from app.engines.schedule.feasibility import ScheduleFeasibilityChecker
from app.engines.schedule.adjustment import ScheduleAdjuster


@pytest.fixture
def event_start() -> datetime:
    return datetime(2026, 10, 15, 9, 0, 0)


@pytest.fixture
def event_end() -> datetime:
    return datetime(2026, 10, 15, 17, 0, 0)  # 8 hours = 480 minutes


def test_schedule_engine_forward_pass(event_start):
    """Test assigning concrete planned_start and planned_end datetimes in topological order."""
    tasks = [
        {"id": "setup", "duration_minutes": 60},
        {"id": "ceremony", "duration_minutes": 90},
        {"id": "reception", "duration_minutes": 120},
    ]
    deps = [
        {"predecessor_task_id": "setup", "successor_task_id": "ceremony", "lag_minutes": 15},
        {"predecessor_task_id": "ceremony", "successor_task_id": "reception", "lag_minutes": 0},
    ]

    engine = ScheduleEngine()
    result = engine.schedule_tasks(event_start, tasks, deps)

    # setup: 09:00 - 10:00 (60 min)
    setup = result.entries["setup"]
    assert setup.planned_start == event_start
    assert setup.planned_end == event_start + timedelta(minutes=60)

    # ceremony: 10:15 - 11:45 (90 min, 15 min lag)
    ceremony = result.entries["ceremony"]
    assert ceremony.planned_start == event_start + timedelta(minutes=75)
    assert ceremony.planned_end == event_start + timedelta(minutes=165)

    # reception: 11:45 - 13:45 (120 min, 0 lag)
    reception = result.entries["reception"]
    assert reception.planned_start == event_start + timedelta(minutes=165)
    assert reception.planned_end == event_start + timedelta(minutes=285)

    assert result.project_end == reception.planned_end
    assert result.total_duration_minutes == 285


def test_feasibility_checker_feasible(event_start, event_end):
    """Test schedule that comfortably fits within the event window is marked feasible."""
    tasks = [{"id": "t1", "duration_minutes": 120}]
    engine = ScheduleEngine()
    sched = engine.schedule_tasks(event_start, tasks, [])

    checker = ScheduleFeasibilityChecker()
    feasibility = checker.check_feasibility(sched, event_start, event_end)

    assert feasibility.is_feasible is True
    assert len(feasibility.violations) == 0
    assert feasibility.available_minutes == 480
    assert feasibility.total_schedule_minutes == 120
    assert feasibility.buffer_minutes == 360


def test_feasibility_checker_exceeds_window(event_start, event_end):
    """Test schedule that exceeds the event window is marked infeasible with violations."""
    # 600 minutes exceeds 480 minutes window
    tasks = [{"id": "long_task", "duration_minutes": 600}]
    engine = ScheduleEngine()
    sched = engine.schedule_tasks(event_start, tasks, [])

    checker = ScheduleFeasibilityChecker()
    feasibility = checker.check_feasibility(sched, event_start, event_end)

    assert feasibility.is_feasible is False
    assert len(feasibility.violations) > 0
    assert any(v.violation_type == "EXCEEDS_EVENT_WINDOW" for v in feasibility.violations)
    assert feasibility.buffer_minutes == 0


def test_schedule_adjuster_delay_propagation(event_start):
    """Test propagating a delay on an upstream task downstream to successors."""
    tasks = [
        {"id": "t1", "duration_minutes": 30},
        {"id": "t2", "duration_minutes": 30},
        {"id": "t3_independent", "duration_minutes": 60},
    ]
    deps = [
        {"predecessor_task_id": "t1", "successor_task_id": "t2", "lag_minutes": 0},
    ]

    graph = DependencyGraph.from_tasks_and_dependencies(tasks, deps)
    engine = ScheduleEngine()
    schedule = engine.schedule_tasks(event_start, tasks, deps)

    adjuster = ScheduleAdjuster()
    # Apply a 45 minute delay to t1
    adjusted = adjuster.adjust_for_delay("t1", 45, graph, schedule)

    assert "t1" in adjusted.affected_tasks
    assert "t2" in adjusted.affected_tasks
    assert "t3_independent" not in adjusted.affected_tasks

    # t1 should end 45 min later
    original_t1_end = schedule.entries["t1"].planned_end
    assert adjusted.entries["t1"].planned_end == original_t1_end + timedelta(minutes=45)

    # t2 should start at new t1 end
    assert adjusted.entries["t2"].planned_start == adjusted.entries["t1"].planned_end
    assert adjusted.total_delay_minutes == 45
