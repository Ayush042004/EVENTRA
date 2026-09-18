"""Unit Tests: ActionService (Transactional Mutations, Idempotency & Rollback)"""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.event import Event
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.resource import Resource
from app.models.budget import BudgetItem
from app.models.enums import TaskPriority, EventState
from app.models.action import ActionExecution
from app.services.action_service import ActionService
from app.core.exceptions import BadRequestException, NotFoundException


def _setup_action_test_data(db: Session):
    user = User(name="Lead Operator", email="lead@eventra.demo")
    db.add(user)
    db.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        owner_id=user.id,
        name="Automation Expo",
        state=EventState.NORMAL.value,
        total_budget=Decimal("40000.00"),
    )
    db.add(event)
    db.commit()

    task = Task(
        event_id=event.id,
        name="Main Stage Lighting",
        priority=TaskPriority.MEDIUM.value,
        is_critical_path=False,
        slack_minutes=45,
        planned_start=now + timedelta(hours=1),
        planned_end=now + timedelta(hours=2),
        required_provider_category="lighting",
    )
    vendor1 = Vendor(name="Lumen Rigging", category="lighting", city="Denver")
    vendor2 = Vendor(name="Apex Glow", category="lighting", city="Denver")
    resource = Resource(
        event_id=event.id,
        name="Moving Head Spotlight",
        type="EQUIPMENT",
        quantity=6,
        status="AVAILABLE",
    )
    budget_item = BudgetItem(
        event_id=event.id,
        category="lighting",
        name="Lighting contract",
        estimated_amount=Decimal("3000.00"),
        actual_amount=Decimal("2500.00"),
    )
    db.add_all([task, vendor1, vendor2, resource, budget_item])
    db.commit()

    return {
        "user": user,
        "event": event,
        "task": task,
        "vendor1": vendor1,
        "vendor2": vendor2,
        "resource": resource,
        "budget_item": budget_item,
        "now": now,
    }


def test_execute_reassign_vendor(db_session: Session):
    """REASSIGN_VENDOR updates assignment, task provider category, and committed budget."""
    data = _setup_action_test_data(db_session)
    service = ActionService(db_session)

    execution = service.execute_action(
        event_id=data["event"].id,
        executor_id=data["user"].id,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=data["task"].id,
        payload={"new_vendor_id": data["vendor2"].id, "agreed_cost": 3200.0},
    )

    assert execution.status == "SUCCESS"
    assert len(execution.affected_entities) >= 1

    # Verify VendorAssignment was updated/created
    assignment = (
        db_session.query(VendorAssignment)
        .filter(VendorAssignment.event_id == data["event"].id, VendorAssignment.category == "lighting")
        .first()
    )
    assert assignment is not None
    assert assignment.vendor_id == data["vendor2"].id
    assert assignment.agreed_cost == Decimal("3200.00")

    # Verify BudgetItem was updated
    db_session.refresh(data["budget_item"])
    assert data["budget_item"].actual_amount == Decimal("3200.00")


def test_execute_adjust_schedule(db_session: Session):
    """ADJUST_SCHEDULE shifts planned_start/end and reduces slack."""
    data = _setup_action_test_data(db_session)
    service = ActionService(db_session)

    orig_start = data["task"].planned_start
    orig_slack = data["task"].slack_minutes

    execution = service.execute_action(
        event_id=data["event"].id,
        executor_id=data["user"].id,
        action_type="ADJUST_SCHEDULE",
        target_type="TASK",
        target_id=data["task"].id,
        payload={"shift_minutes": 20},
    )

    assert execution.status == "SUCCESS"
    db_session.refresh(data["task"])
    assert data["task"].planned_start == orig_start + timedelta(minutes=20)
    assert data["task"].slack_minutes == orig_slack - 20


def test_execute_allocate_resource(db_session: Session):
    """ALLOCATE_RESOURCE binds resource to task and marks it ALLOCATED."""
    data = _setup_action_test_data(db_session)
    service = ActionService(db_session)

    execution = service.execute_action(
        event_id=data["event"].id,
        executor_id=data["user"].id,
        action_type="ALLOCATE_RESOURCE",
        target_type="RESOURCE",
        target_id=data["resource"].id,
        payload={"task_id": data["task"].id, "quantity": 4},
    )

    assert execution.status == "SUCCESS"
    db_session.refresh(data["resource"])
    assert data["resource"].allocated_task_id == data["task"].id
    assert data["resource"].status == "ALLOCATED"
    assert data["resource"].quantity == 4


def test_execute_adjust_budget(db_session: Session):
    """ADJUST_BUDGET updates committed and estimated figures with Decimal accuracy."""
    data = _setup_action_test_data(db_session)
    service = ActionService(db_session)

    execution = service.execute_action(
        event_id=data["event"].id,
        executor_id=data["user"].id,
        action_type="ADJUST_BUDGET",
        target_type="BUDGET",
        target_id=data["budget_item"].id,
        payload={"actual_amount": 3500.00, "estimated_amount": 4000.00},
    )

    assert execution.status == "SUCCESS"
    db_session.refresh(data["budget_item"])
    assert data["budget_item"].actual_amount == Decimal("3500.00")
    assert data["budget_item"].estimated_amount == Decimal("4000.00")


def test_action_idempotency(db_session: Session):
    """Submitting the same action_id multiple times returns the cached execution without re-mutating."""
    data = _setup_action_test_data(db_session)
    service = ActionService(db_session)
    fixed_action_id = "act-fixed-uuid-12345"

    # 1. First execution
    exec1 = service.execute_action(
        event_id=data["event"].id,
        executor_id=data["user"].id,
        action_type="ADJUST_BUDGET",
        target_type="BUDGET",
        target_id=data["budget_item"].id,
        payload={"actual_amount": 2800.00},
        action_id=fixed_action_id,
    )

    # 2. Second execution with identical action_id
    exec2 = service.execute_action(
        event_id=data["event"].id,
        executor_id=data["user"].id,
        action_type="ADJUST_BUDGET",
        target_type="BUDGET",
        target_id=data["budget_item"].id,
        payload={"actual_amount": 9999.00},  # Different payload should be ignored due to idempotency
        action_id=fixed_action_id,
    )

    assert exec1.id == exec2.id
    assert exec1.action_id == fixed_action_id
    db_session.refresh(data["budget_item"])
    # Value must remain 2800.00 from the first execution!
    assert data["budget_item"].actual_amount == Decimal("2800.00")


def test_action_transaction_rollback(db_session: Session):
    """When an error occurs during execution, all changes are rolled back cleanly."""
    data = _setup_action_test_data(db_session)
    service = ActionService(db_session)

    orig_actual = data["budget_item"].actual_amount

    # Attempt reassigning vendor to a non-existent vendor ID
    with pytest.raises(NotFoundException):
        service.execute_action(
            event_id=data["event"].id,
            executor_id=data["user"].id,
            action_type="REASSIGN_VENDOR",
            target_type="TASK",
            target_id=data["task"].id,
            payload={"new_vendor_id": "non-existent-vendor-id", "agreed_cost": 5000.0},
        )

    # Verify no partial mutation was persisted
    db_session.refresh(data["budget_item"])
    assert data["budget_item"].actual_amount == orig_actual
    db_session.refresh(data["task"])
    assert data["task"].required_provider_category == "lighting"
