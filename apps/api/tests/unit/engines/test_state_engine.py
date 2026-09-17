"""Unit tests for State Engine components.

Tests EventStateMachine transitions, TransitionValidator readiness checks,
and DeviationDetector schedule and budget tracking.
"""
from datetime import datetime, timedelta
from decimal import Decimal
import pytest

from app.engines.state.event_state import EventStateMachine
from app.engines.state.transitions import TransitionValidator
from app.engines.state.deviation import DeviationDetector
from app.models.enums import EventLifecycleState, TaskStatus


def test_state_machine_valid_transitions():
    """Test valid lifecycle state progression."""
    sm = EventStateMachine()

    assert sm.can_transition("DRAFT", "SPECIFIED") is True
    assert sm.can_transition("SPECIFIED", "PLANNED") is True
    assert sm.can_transition("PLANNED", "LIVE") is True
    assert sm.can_transition("LIVE", "CONCLUDED") is True
    assert sm.can_transition("LIVE", "INCIDENT") is True
    assert sm.can_transition("INCIDENT", "LIVE") is True
    assert sm.can_transition("LIVE", "CANCELLED") is True


def test_state_machine_invalid_transitions():
    """Test invalid transitions are rejected."""
    sm = EventStateMachine()

    assert sm.can_transition("DRAFT", "LIVE") is False
    assert sm.can_transition("CONCLUDED", "LIVE") is False
    assert sm.can_transition("CANCELLED", "PLANNED") is False

    with pytest.raises(ValueError, match="Invalid lifecycle transition"):
        sm.validate_transition("DRAFT", "LIVE")


def test_state_machine_terminal_states():
    """Test identifying terminal states."""
    sm = EventStateMachine()
    assert sm.is_terminal("CONCLUDED") is True
    assert sm.is_terminal("CANCELLED") is True
    assert sm.is_terminal("LIVE") is False
    assert sm.is_terminal("PLANNED") is False


def test_transition_validator_go_live_ready():
    """Test go-live validation passes when preconditions are met."""
    validator = TransitionValidator()
    event = {"lifecycle_state": "PLANNED"}
    now = datetime(2026, 10, 15, 9, 0)
    tasks = [
        {
            "id": "t1",
            "name": "Prep",
            "status": "PENDING",
            "planned_start": now,
            "planned_end": now + timedelta(minutes=60),
        }
    ]

    failures = validator.validate_go_live_readiness(event, tasks)
    assert len(failures) == 0


def test_transition_validator_go_live_failures():
    """Test go-live validation reports all precondition failures."""
    validator = TransitionValidator()

    # 1. Not in PLANNED state
    event = {"lifecycle_state": "DRAFT"}
    failures = validator.validate_go_live_readiness(event, [])
    assert any("PLANNED" in f for f in failures)
    assert any("no planned tasks" in f for f in failures)

    # 2. Missing schedule on tasks
    event = {"lifecycle_state": "PLANNED"}
    tasks = [{"name": "Unscheduled Task", "status": "PENDING", "planned_start": None, "planned_end": None}]
    failures = validator.validate_go_live_readiness(event, tasks)
    assert any("missing planned schedule" in f for f in failures)


def test_transition_validator_conclude_readiness():
    """Test conclude validation requires LIVE state and no active tasks."""
    validator = TransitionValidator()

    # Ready: LIVE and task completed
    event = {"lifecycle_state": "LIVE"}
    tasks_done = [{"name": "T1", "status": "COMPLETED"}]
    assert len(validator.validate_conclude_readiness(event, tasks_done)) == 0

    # Not ready: task in progress
    tasks_active = [{"name": "T1", "status": "IN_PROGRESS"}]
    failures = validator.validate_conclude_readiness(event, tasks_active)
    assert len(failures) == 1
    assert "IN_PROGRESS" in failures[0]


def test_deviation_detector_schedule():
    """Test detecting late start, late finish, and early finish deviations."""
    detector = DeviationDetector()
    t_start = datetime(2026, 10, 15, 10, 0)
    t_end = datetime(2026, 10, 15, 11, 0)

    tasks = [
        # Late start by 15 min
        {
            "id": "t_late_start",
            "name": "Late Start Task",
            "planned_start": t_start,
            "actual_start": t_start + timedelta(minutes=15),
            "planned_end": t_end,
            "actual_end": None,
        },
        # Late finish by 30 min
        {
            "id": "t_late_finish",
            "name": "Late Finish Task",
            "planned_start": t_start,
            "actual_start": t_start,
            "planned_end": t_end,
            "actual_end": t_end + timedelta(minutes=30),
        },
        # On time
        {
            "id": "t_on_time",
            "name": "On Time Task",
            "planned_start": t_start,
            "actual_start": t_start,
            "planned_end": t_end,
            "actual_end": t_end,
        },
    ]

    devs = detector.detect_schedule_deviations(tasks)
    dev_types = {d.deviation_type for d in devs}
    assert "LATE_START" in dev_types
    assert "LATE_FINISH" in dev_types

    late_start_dev = next(d for d in devs if d.task_id == "t_late_start")
    assert late_start_dev.deviation_minutes == 15

    late_finish_dev = next(d for d in devs if d.task_id == "t_late_finish")
    assert late_finish_dev.deviation_minutes == 30


def test_deviation_detector_budget():
    """Test detecting budget overspend and category-level deviations."""
    detector = DeviationDetector()
    items = [
        {"category": "VENUE", "estimated_amount": Decimal("10000"), "actual_amount": Decimal("12000")},
        {"category": "CATERING", "estimated_amount": Decimal("5000"), "actual_amount": Decimal("4000")},
    ]

    dev = detector.detect_budget_deviation(items, Decimal("15000"))
    assert dev.total_spent == Decimal("16000.00")
    assert dev.is_over_budget is True
    assert "VENUE" in dev.overspend_categories
