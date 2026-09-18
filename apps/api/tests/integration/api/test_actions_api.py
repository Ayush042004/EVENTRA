"""Phase 9 Integration Tests: Actions API"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, RoleType, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.incident import Incident
from app.models.recovery import RecoveryOption
from app.models.task import Task
from app.models.user import User
from app.models.vendor import Vendor
from app.models.budget import BudgetItem


def _setup_actions_api_env(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer = User(name="Alice Lead", email="alice.l@eventra.test")
    collaborator = User(name="Bob Member", email="bob.m@eventra.test")
    db.add_all([organizer, collaborator])
    db.flush()

    event = Event(
        owner_id=organizer.id,
        name="Global Summit",
        lifecycle_state=EventLifecycleState.PLANNED.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(days=5),
        end_datetime=now + timedelta(days=5, hours=10),
        total_budget=Decimal("75000.00"),
    )
    db.add(event)
    db.flush()

    mem_org = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    mem = EventMember(event_id=event.id, user_id=collaborator.id, role=RoleType.COLLABORATOR.value)
    db.add_all([mem_org, mem])

    task = Task(
        event_id=event.id,
        name="Sound Rigging",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=60,
        is_critical_path=True,
    )
    budget_item = BudgetItem(
        event_id=event.id,
        name="Audio budget",
        category="av",
        estimated_amount=Decimal("5000.00"),
        actual_amount=Decimal("2000.00"),
    )
    db.add_all([task, budget_item])
    db.commit()

    return organizer, collaborator, event, task, budget_item


def test_organizer_executes_action_directly(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task, budget_item = _setup_actions_api_env(db_session)

    payload = {
        "action_type": "ADJUST_BUDGET",
        "target_type": "BUDGET",
        "target_id": budget_item.id,
        "payload": {"actual_amount": 2500.00},
    }

    resp = test_client.post(
        f"/api/events/{event.id}/actions",
        json=payload,
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["decision"]["requires_approval"] is False
    assert data["execution"] is not None
    assert data["execution"]["status"] == "SUCCESS"

    db_session.refresh(budget_item)
    assert budget_item.actual_amount == Decimal("2500.00")


def test_collaborator_major_action_routed_to_approval(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task, budget_item = _setup_actions_api_env(db_session)

    # Collaborator attempts to modify a CRITICAL task (classified as MAJOR/CRITICAL impact)
    payload = {
        "action_type": "REASSIGN_TASK",
        "target_type": "TASK",
        "target_id": task.id,
        "payload": {"priority": "LOW"},
    }

    resp = test_client.post(
        f"/api/events/{event.id}/actions",
        json=payload,
        headers={"x-user-id": collaborator.id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["decision"]["requires_approval"] is True
    assert data["approval_request"] is not None
    assert data["approval_request"]["status"] == "PENDING"
    assert data["execution"] is None

    # Verify task was NOT modified yet
    db_session.refresh(task)
    assert task.priority == TaskPriority.CRITICAL.value


def test_execute_recovery_option_api(test_client: TestClient, db_session: Session):
    from app.engines.auth.snapshot import compute_event_state_snapshot
    organizer, collaborator, event, task, budget_item = _setup_actions_api_env(db_session)

    # Setup incident and recovery option
    incident = Incident(
        event_id=event.id,
        title="Lead technician unavailable",
        incident_type="STAFF_UNAVAILABLE",
        severity="MEDIUM",
        status="INVESTIGATING",
        description="Lead technician unavailable",
    )
    db_session.add(incident)
    db_session.flush()

    current_snapshot = compute_event_state_snapshot(db_session, event.id)
    rec_opt = RecoveryOption(
        incident_id=incident.id,
        event_id=event.id,
        strategy_type="ADJUST_SCHEDULE",
        status="FEASIBLE",
        is_feasible=True,
        state_snapshot=current_snapshot,
        affected_tasks=[task.id],
        proposed_changes={"schedule_adjustment": {"task_id": task.id, "shift_minutes": 20}},
    )
    db_session.add(rec_opt)
    db_session.commit()

    # Organizer executes recovery option
    resp = test_client.post(
        f"/api/events/{event.id}/actions/execute-recovery",
        json={"recovery_option_id": rec_opt.id},
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["execution"]["status"] == "SUCCESS"

    db_session.refresh(rec_opt)
    assert rec_opt.status == "EXECUTED"


def test_execute_recovery_option_stale_rejection(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task, budget_item = _setup_actions_api_env(db_session)

    incident = Incident(
        event_id=event.id,
        title="Technician shortage",
        incident_type="STAFF_UNAVAILABLE",
        severity="MEDIUM",
        status="INVESTIGATING",
        description="Lead technician unavailable",
    )
    db_session.add(incident)
    db_session.flush()

    # Create option with an old/outdated snapshot checksum
    rec_opt = RecoveryOption(
        incident_id=incident.id,
        event_id=event.id,
        strategy_type="ADJUST_SCHEDULE",
        status="FEASIBLE",
        is_feasible=True,
        state_snapshot="outdated-sha256-hash-1234567890abcdef",
        affected_tasks=[task.id],
        proposed_changes={"schedule_adjustment": {"task_id": task.id, "shift_minutes": 20}},
    )
    db_session.add(rec_opt)
    db_session.commit()

    # Attempt execution with stale snapshot
    resp = test_client.post(
        f"/api/events/{event.id}/actions/execute-recovery",
        json={"recovery_option_id": rec_opt.id},
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 409
    assert "STALE_ACTION" in resp.json()["error"]["message"]

