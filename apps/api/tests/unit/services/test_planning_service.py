"""Unit tests for PlanningService.

Tests orchestrating the full planning pipeline from Event model to
persisted tasks, dependencies, resources, budget items, and PLANNED lifecycle state.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.task import Task
from app.models.dependency import TaskDependency
from app.models.resource import Resource
from app.models.budget import BudgetItem
from app.models.state_transition import StateTransition
from app.models.enums import EventLifecycleState, TaskStatus
from app.services.planning_service import PlanningService
from app.core.exceptions import NotFoundException, BadRequestException


@pytest.fixture
def test_event(db_session: Session) -> Event:
    """Creates a sample event in DRAFT state ready for planning."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        name="Grand Summer Wedding",
        description="A beautiful summer wedding celebration",
        event_type="WEDDING",
        start_datetime=now + timedelta(days=30),
        end_datetime=now + timedelta(days=30, hours=10),
        guest_count=200,
        total_budget=Decimal("45000.00"),
        currency="USD",
        lifecycle_state=EventLifecycleState.DRAFT.value,
        location="Oceanfront Villa",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def test_generate_plan_success(db_session: Session, test_event: Event):
    """Test generating a plan creates all DB records and transitions to PLANNED."""
    service = PlanningService(db_session)
    plan = service.generate_plan(test_event.id)

    assert plan.event_id == test_event.id
    assert plan.lifecycle_state == EventLifecycleState.PLANNED.value
    assert plan.summary.total_tasks > 0
    assert plan.summary.total_dependencies > 0
    assert plan.summary.total_resources > 0
    assert plan.summary.total_budget_items > 0
    assert plan.summary.total_estimated_budget > 0

    # Verify database records
    tasks = db_session.query(Task).filter(Task.event_id == test_event.id).all()
    assert len(tasks) == plan.summary.total_tasks
    for t in tasks:
        assert t.status == TaskStatus.PENDING.value
        assert t.key is not None
        assert t.duration_minutes is not None

    deps = db_session.query(TaskDependency).filter(TaskDependency.event_id == test_event.id).all()
    assert len(deps) == plan.summary.total_dependencies

    resources = db_session.query(Resource).filter(Resource.event_id == test_event.id).all()
    assert len(resources) == plan.summary.total_resources

    budget_items = db_session.query(BudgetItem).filter(BudgetItem.event_id == test_event.id).all()
    assert len(budget_items) == plan.summary.total_budget_items

    # Verify state transition record
    transitions = db_session.query(StateTransition).filter(
        StateTransition.event_id == test_event.id,
        StateTransition.entity_type == "EVENT",
    ).all()
    assert len(transitions) == 1
    assert transitions[0].previous_state == EventLifecycleState.DRAFT.value
    assert transitions[0].new_state == EventLifecycleState.PLANNED.value


def test_get_plan(db_session: Session, test_event: Event):
    """Test retrieving an existing plan."""
    service = PlanningService(db_session)
    service.generate_plan(test_event.id)

    fetched = service.get_plan(test_event.id)
    assert fetched.event_id == test_event.id
    assert fetched.lifecycle_state == EventLifecycleState.PLANNED.value
    assert len(fetched.tasks) > 0
    assert len(fetched.dependencies) > 0
    assert len(fetched.resources) > 0
    assert len(fetched.budget_items) > 0


def test_generate_plan_not_found(db_session: Session):
    """Test generating a plan for a nonexistent event raises NotFoundException."""
    service = PlanningService(db_session)
    with pytest.raises(NotFoundException):
        service.generate_plan("nonexistent-event-id")


def test_generate_plan_invalid_state(db_session: Session, test_event: Event):
    """Test generating a plan when event is already LIVE raises BadRequestException."""
    test_event.lifecycle_state = EventLifecycleState.LIVE.value
    db_session.commit()

    service = PlanningService(db_session)
    with pytest.raises(BadRequestException, match="Cannot generate plan"):
        service.generate_plan(test_event.id)
