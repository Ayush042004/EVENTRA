"""Unit tests for VerificationService."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.engines.auth.snapshot import compute_event_state_snapshot
from app.models.action import ActionExecution
from app.models.budget import BudgetItem
from app.models.enums import EventLifecycleState, EventState, RoleType, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.objective import Objective
from app.models.task import Task
from app.models.user import User
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.state_transition import StateTransition
from app.services.verification_service import VerificationService


def _setup_service_test_data(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer = User(name="Victor Verifier", email="victor.v@eventra.test")
    stranger = User(name="Sam Stranger", email="sam.s@eventra.test")
    db.add_all([organizer, stranger])
    db.flush()

    event = Event(
        owner_id=organizer.id,
        name="Annual Gala",
        lifecycle_state=EventLifecycleState.PLANNED.value,
        state=EventState.RECOVERY.value,
        start_datetime=now + timedelta(days=3),
        end_datetime=now + timedelta(days=3, hours=8),
        total_budget=Decimal("50000.00"),
    )
    db.add(event)
    db.flush()

    mem_org = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    db.add(mem_org)

    task = Task(
        event_id=event.id,
        name="Catering Service Setup",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=60,
        slack_minutes=60,
        required_provider_category="catering",
    )
    vendor = Vendor(name="Apex Food Co", category="catering", city="Chicago")
    db.add_all([task, vendor])
    db.flush()

    assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=vendor.id,
        category="catering",
        status="CONFIRMED",
        agreed_cost=Decimal("3000.00"),
    )
    budget_item = BudgetItem(
        event_id=event.id,
        name="Catering Cost",
        category="catering",
        estimated_amount=Decimal("3500.00"),
        actual_amount=Decimal("3000.00"),
    )
    obj = Objective(
        event_id=event.id,
        name="Guest Meal Readiness",
        priority="CRITICAL",
    )
    db.add_all([assignment, budget_item, obj])
    db.commit()

    snapshot = compute_event_state_snapshot(db, event.id)

    action = ActionExecution(
        action_id="act-test-uuid-100",
        event_id=event.id,
        action_type="REASSIGN_VENDOR",
        executor_id=organizer.id,
        status="SUCCESS",
        affected_entities=[{"id": task.id}],
        before_version="initial-snap",
        after_version=snapshot,
        execution_payload={"new_vendor_id": vendor.id, "agreed_cost": 3000.0},
        executed_at=now,
    )
    db.add(action)
    db.commit()

    return {
        "organizer": organizer,
        "stranger": stranger,
        "event": event,
        "task": task,
        "vendor": vendor,
        "action": action,
    }


def test_verify_action_success_transitions_event_state(db_session: Session):
    data = _setup_service_test_data(db_session)
    service = VerificationService(db_session)

    ver = service.verify_action(
        event_id=data["event"].id,
        action_execution_id=data["action"].id,
        current_user_id=data["organizer"].id,
    )

    assert ver.status == "VERIFIED"
    assert ver.event_state_after == "NORMAL"

    # Verify event state in database was updated through StateTransition
    db_session.refresh(data["event"])
    assert data["event"].state == "NORMAL"

    transition = (
        db_session.query(StateTransition)
        .filter(StateTransition.event_id == data["event"].id, StateTransition.new_state == "NORMAL")
        .first()
    )
    assert transition is not None


def test_verify_action_forbidden_for_stranger(db_session: Session):
    data = _setup_service_test_data(db_session)
    service = VerificationService(db_session)

    with pytest.raises(ForbiddenException):
        service.verify_action(
            event_id=data["event"].id,
            action_execution_id=data["action"].id,
            current_user_id=data["stranger"].id,
        )


def test_verify_action_not_found(db_session: Session):
    data = _setup_service_test_data(db_session)
    service = VerificationService(db_session)

    with pytest.raises(NotFoundException):
        service.verify_action(
            event_id=data["event"].id,
            action_execution_id="00000000-0000-0000-0000-000000000000",
            current_user_id=data["organizer"].id,
        )


def test_reverify_action(db_session: Session):
    data = _setup_service_test_data(db_session)
    service = VerificationService(db_session)

    # Initial verification
    ver = service.verify_action(
        event_id=data["event"].id,
        action_execution_id=data["action"].id,
        current_user_id=data["organizer"].id,
    )

    # Re-verify
    re_ver = service.reverify(
        event_id=data["event"].id,
        verification_id=ver.id,
        reason="Vendor checkin confirmed",
        current_user_id=data["organizer"].id,
    )

    assert re_ver.id == ver.id
    assert re_ver.status == "VERIFIED"
