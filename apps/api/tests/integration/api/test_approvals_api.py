"""Phase 9 Integration Tests: Approvals API"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, RoleType, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.task import Task
from app.models.user import User


def _setup_approval_api_env(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer = User(name="Eve Organizer", email="eve.org@eventra.test")
    collaborator = User(name="Colin Collab", email="colin.c@eventra.test")
    db.add_all([organizer, collaborator])
    db.flush()

    event = Event(
        owner_id=organizer.id,
        name="Tech Gala 2026",
        lifecycle_state=EventLifecycleState.PLANNED.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(days=2),
        end_datetime=now + timedelta(days=2, hours=8),
        total_budget=Decimal("50000.00"),
    )
    db.add(event)
    db.flush()

    # Add collaborator
    mem = EventMember(event_id=event.id, user_id=collaborator.id, role=RoleType.COLLABORATOR.value)
    db.add(mem)

    task = Task(
        event_id=event.id,
        name="Stage Setup",
        status=TaskStatus.PENDING.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=120,
        is_critical_path=True,
    )
    db.add(task)
    db.commit()

    return organizer, collaborator, event, task


def test_create_and_get_approval_request(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task = _setup_approval_api_env(db_session)

    # Collaborator creates approval request
    payload = {
        "action_type": "REASSIGN_TASK",
        "target_type": "TASK",
        "target_id": task.id,
        "requested_action": {"priority": "LOW"},
        "justification": "Task priority downgraded due to vendor change",
    }
    resp = test_client.post(
        f"/api/events/{event.id}/approvals",
        json=payload,
        headers={"x-user-id": collaborator.id},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["event_id"] == event.id
    assert data["requester_id"] == collaborator.id
    assert data["action_type"] == "REASSIGN_TASK"
    assert data["status"] == "PENDING"
    approval_id = data["id"]

    # Get single approval request
    get_resp = test_client.get(
        f"/api/events/{event.id}/approvals/{approval_id}",
        headers={"x-user-id": collaborator.id},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == approval_id


def test_list_approvals_with_status_filter(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task = _setup_approval_api_env(db_session)

    # Create 2 requests
    for i in range(2):
        resp = test_client.post(
            f"/api/events/{event.id}/approvals",
            json={
                "action_type": "REASSIGN_TASK",
                "target_type": "TASK",
                "target_id": task.id,
                "requested_action": {"duration_minutes": 150 + i * 10},
                "justification": f"Need {i} extra time",
            },
            headers={"x-user-id": collaborator.id},
        )
        assert resp.status_code == 201

    list_resp = test_client.get(
        f"/api/events/{event.id}/approvals?status=PENDING",
        headers={"x-user-id": organizer.id},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 2


def test_separation_of_duties_self_approval_rejected(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task = _setup_approval_api_env(db_session)

    # Collaborator creates request
    resp = test_client.post(
        f"/api/events/{event.id}/approvals",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": task.id,
            "requested_action": {"priority": "MEDIUM"},
            "justification": "Self approval check",
        },
        headers={"x-user-id": collaborator.id},
    )
    assert resp.status_code == 201
    approval_id = resp.json()["id"]

    # Collaborator attempts to approve their own request -> 403 Forbidden
    approve_resp = test_client.post(
        f"/api/events/{event.id}/approvals/{approval_id}/approve",
        json={"notes": "Approving my own request"},
        headers={"x-user-id": collaborator.id},
    )
    assert approve_resp.status_code == 403
    assert "Separation of duties" in approve_resp.json()["detail"]


def test_organizer_approves_and_executes_request(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task = _setup_approval_api_env(db_session)

    # Collaborator creates request
    resp = test_client.post(
        f"/api/events/{event.id}/approvals",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": task.id,
            "requested_action": {"priority": "LOW"},
            "justification": "Priority downgrade",
        },
        headers={"x-user-id": collaborator.id},
    )
    assert resp.status_code == 201
    approval_id = resp.json()["id"]

    # Organizer approves
    approve_resp = test_client.post(
        f"/api/events/{event.id}/approvals/{approval_id}/approve",
        json={"notes": "Approved by lead"},
        headers={"x-user-id": organizer.id},
    )
    assert approve_resp.status_code == 200
    data = approve_resp.json()
    assert data["status"] == "APPROVED"
    assert data["approver_id"] == organizer.id

    # Verify task was actually mutated in DB
    db_session.refresh(task)
    assert task.priority == "LOW"


def test_reject_and_cancel_approval_requests(test_client: TestClient, db_session: Session):
    organizer, collaborator, event, task = _setup_approval_api_env(db_session)

    # 1. Rejection by organizer
    resp1 = test_client.post(
        f"/api/events/{event.id}/approvals",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": task.id,
            "requested_action": {"priority": "HIGH"},
            "justification": "Reject this one",
        },
        headers={"x-user-id": collaborator.id},
    )
    app1_id = resp1.json()["id"]

    rej_resp = test_client.post(
        f"/api/events/{event.id}/approvals/{app1_id}/reject",
        json={"reason": "Denied due to risk"},
        headers={"x-user-id": organizer.id},
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "REJECTED"

    # 2. Cancellation by requester
    resp2 = test_client.post(
        f"/api/events/{event.id}/approvals",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": task.id,
            "requested_action": {"priority": "HIGH"},
            "justification": "Cancel this one",
        },
        headers={"x-user-id": collaborator.id},
    )
    app2_id = resp2.json()["id"]

    cancel_resp = test_client.post(
        f"/api/events/{event.id}/approvals/{app2_id}/cancel",
        headers={"x-user-id": collaborator.id},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"
