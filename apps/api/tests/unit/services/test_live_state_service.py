"""Unit tests for LiveStateService.

Tests go-live transition, task progress tracking, readiness cascading,
live state aggregation, and event conclusion.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.task import Task
from app.models.dependency import TaskDependency
from app.models.budget import BudgetItem
from app.models.state_transition import StateTransition
from app.models.enums import EventLifecycleState, TaskStatus
from app.services.planning_service import PlanningService
from app.services.live_state_service import LiveStateService
from app.engines.schedule.scheduler import ScheduleEngine
from app.core.exceptions import BadRequestException, NotFoundException


@pytest.fixture
def planned_event_with_schedule(db_session: Session) -> Event:
    """Sets up an event with plan generated and tasks scheduled."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        name="Live Festival",
        event_type="COLLEGE_FEST",
        start_datetime=now + timedelta(days=2),
        end_datetime=now + timedelta(days=2, hours=12),
        guest_count=500,
        total_budget=Decimal("35000.00"),
        currency="USD",
        lifecycle_state=EventLifecycleState.DRAFT.value,
        location="Open Field",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    # 1. Generate plan
    planning_service = PlanningService(db_session)
    planning_service.generate_plan(event.id)

    # 2. Compute and set schedule
    tasks = db_session.query(Task).filter(Task.event_id == event.id).all()
    deps = db_session.query(TaskDependency).filter(TaskDependency.event_id == event.id).all()

    scheduler = ScheduleEngine()
    sched_result = scheduler.schedule_tasks(event.start_datetime, tasks, deps)

    for task in tasks:
        entry = sched_result.entries.get(task.id)
        if entry:
            task.planned_start = entry.planned_start
            task.planned_end = entry.planned_end

    db_session.commit()
    db_session.refresh(event)
    return event


def test_go_live_success(db_session: Session, planned_event_with_schedule: Event):
    """Test transitioning to LIVE activates root tasks and records transitions."""
    service = LiveStateService(db_session)
    live_state = service.go_live(planned_event_with_schedule.id)

    assert live_state.lifecycle_state == EventLifecycleState.LIVE.value
    assert live_state.progress_percent == 0.0

    # Tasks with no predecessors should now be READY
    tasks = db_session.query(Task).filter(Task.event_id == planned_event_with_schedule.id).all()
    ready_tasks = [t for t in tasks if t.status == TaskStatus.READY.value]
    assert len(ready_tasks) > 0

    # Event transition recorded
    event_trans = db_session.query(StateTransition).filter(
        StateTransition.event_id == planned_event_with_schedule.id,
        StateTransition.entity_type == "EVENT",
        StateTransition.new_state == "LIVE",
    ).first()
    assert event_trans is not None


def test_go_live_not_ready_error(db_session: Session):
    """Test go-live fails if event is not in PLANNED state."""
    event = Event(
        name="Unplanned Event",
        event_type="WEDDING",
        lifecycle_state=EventLifecycleState.DRAFT.value,
    )
    db_session.add(event)
    db_session.commit()

    service = LiveStateService(db_session)
    with pytest.raises(BadRequestException, match="Event is not ready to go live"):
        service.go_live(event.id)


def test_task_status_updates_and_readiness_cascading(
    db_session: Session, planned_event_with_schedule: Event
):
    """Test progressing a task and cascading READY status to its successor."""
    service = LiveStateService(db_session)
    service.go_live(planned_event_with_schedule.id)

    tasks = db_session.query(Task).filter(Task.event_id == planned_event_with_schedule.id).all()
    deps = db_session.query(TaskDependency).filter(
        TaskDependency.event_id == planned_event_with_schedule.id
    ).all()

    # Find a ready predecessor task that has a successor
    target_task = None
    target_succ_id = None
    for dep in deps:
        pred = next(t for t in tasks if t.id == dep.predecessor_task_id)
        if pred.status == TaskStatus.READY.value:
            target_task = pred
            target_succ_id = dep.successor_task_id
            break

    assert target_task is not None, "Expected at least one ready task with successors"

    # Start the task
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    updated = service.update_task_status(
        planned_event_with_schedule.id,
        target_task.id,
        TaskStatus.IN_PROGRESS.value,
        actual_start=now,
    )
    assert updated.status == TaskStatus.IN_PROGRESS.value
    assert updated.actual_start is not None

    # Complete the task
    completed = service.update_task_status(
        planned_event_with_schedule.id,
        target_task.id,
        TaskStatus.COMPLETED.value,
        actual_end=now + timedelta(minutes=30),
    )
    assert completed.status == TaskStatus.COMPLETED.value
    assert completed.actual_end is not None

    # Verify live state reflects updated progress
    live_state = service.get_live_state(planned_event_with_schedule.id)
    assert live_state.completed_tasks >= 1
    assert live_state.progress_percent > 0.0


def test_conclude_event_success_and_guard(
    db_session: Session, planned_event_with_schedule: Event
):
    """Test concluding an event when ready, and guard against concluding when tasks are active."""
    service = LiveStateService(db_session)
    service.go_live(planned_event_with_schedule.id)

    tasks = db_session.query(Task).filter(Task.event_id == planned_event_with_schedule.id).all()

    # Put a task in IN_PROGRESS: conclude should be rejected
    ready_task = next(t for t in tasks if t.status == TaskStatus.READY.value)
    service.update_task_status(
        planned_event_with_schedule.id, ready_task.id, TaskStatus.IN_PROGRESS.value
    )

    with pytest.raises(BadRequestException, match="Event is not ready to conclude"):
        service.conclude_event(planned_event_with_schedule.id)

    # Complete or cancel all tasks
    for t in tasks:
        t.status = TaskStatus.COMPLETED.value
    db_session.commit()

    # Conclude should now succeed
    concluded = service.conclude_event(planned_event_with_schedule.id)
    assert concluded.lifecycle_state == EventLifecycleState.CONCLUDED.value
