"""Phase 10 Integration Tests: Verification REST APIs"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, RoleType, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.action import ActionExecution
from app.models.task import Task
from app.models.user import User
from app.engines.auth.snapshot import compute_event_state_snapshot


def _setup_verification_api_env(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer = User(name="Alice Lead", email="alice.verif@eventra.test")
    stranger = User(name="Eve Stranger", email="eve.verif@eventra.test")
    db.add_all([organizer, stranger])
    db.flush()

    event = Event(
        owner_id=organizer.id,
        name="Verification Expo",
        lifecycle_state=EventLifecycleState.PLANNED.value,
        state=EventState.AT_RISK.value,
        start_datetime=now + timedelta(days=2),
        end_datetime=now + timedelta(days=2, hours=8),
        total_budget=Decimal("50000.00"),
    )
    db.add(event)
    db.flush()

    mem_org = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    db.add(mem_org)

    task = Task(
        event_id=event.id,
        name="Stage Setup",
        status=TaskStatus.READY.value,
        priority=TaskPriority.HIGH.value,
        duration_minutes=120,
    )
    db.add(task)
    db.flush()

    current_snap = compute_event_state_snapshot(db, event.id)

    action = ActionExecution(
        action_id="act-verif-api-1",
        event_id=event.id,
        executor_id=organizer.id,
        action_type="REASSIGN_TASK",
        status="SUCCESS",
        affected_entities=[{"type": "TASK", "id": task.id}],
        before_version="snap-before",
        after_version=current_snap,
        execution_payload={"priority": "CRITICAL"},
        execution_result_data={"updated": True},
    )
    db.add(action)
    db.commit()

    return organizer, stranger, event, action


def test_verify_action_endpoint(test_client: TestClient, db_session: Session):
    organizer, stranger, event, action = _setup_verification_api_env(db_session)

    resp = test_client.post(
        f"/api/events/{event.id}/actions/{action.id}/verify",
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["action_execution_id"] == action.id
    assert data["event_id"] == event.id
    assert data["status"] in ["VERIFIED", "PARTIALLY_VERIFIED"]
    assert "objective_results" in data
    assert "schedule_result" in data
    assert "budget_result" in data
    assert "resource_result" in data
    assert "provider_result" in data
    assert "constraint_result" in data


def test_get_and_list_verifications(test_client: TestClient, db_session: Session):
    organizer, stranger, event, action = _setup_verification_api_env(db_session)

    # First verify to generate a verification record
    v_resp = test_client.post(
        f"/api/events/{event.id}/actions/{action.id}/verify",
        headers={"x-user-id": organizer.id},
    )
    assert v_resp.status_code == 201, v_resp.text
    v_data = v_resp.json()
    ver_id = v_data["id"]

    # Test GET single verification
    get_resp = test_client.get(
        f"/api/events/{event.id}/verifications/{ver_id}",
        headers={"x-user-id": organizer.id},
    )
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["id"] == ver_id

    # Test GET list verifications for event
    list_resp = test_client.get(
        f"/api/events/{event.id}/verifications",
        headers={"x-user-id": organizer.id},
    )
    assert list_resp.status_code == 200, list_resp.text
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == ver_id for item in list_data["items"])


def test_reverify_action_endpoint(test_client: TestClient, db_session: Session):
    organizer, stranger, event, action = _setup_verification_api_env(db_session)

    v_resp = test_client.post(
        f"/api/events/{event.id}/actions/{action.id}/verify",
        headers={"x-user-id": organizer.id},
    )
    assert v_resp.status_code == 201, v_resp.text
    ver_id = v_resp.json()["id"]

    # Reverify
    re_resp = test_client.post(
        f"/api/events/{event.id}/verifications/{ver_id}/reverify",
        headers={"x-user-id": organizer.id},
    )
    assert re_resp.status_code == 200, re_resp.text
    re_data = re_resp.json()
    assert re_data["id"] == ver_id  # Re-verification updates the authoritative verification record
    assert re_data["status"] in ["VERIFIED", "PARTIALLY_VERIFIED", "FAILED"]


def test_verify_action_permissions_and_errors(test_client: TestClient, db_session: Session):
    organizer, stranger, event, action = _setup_verification_api_env(db_session)

    # Stranger tries to verify
    resp = test_client.post(
        f"/api/events/{event.id}/actions/{action.id}/verify",
        headers={"x-user-id": stranger.id},
    )
    assert resp.status_code == 403

    # Non-existent action
    resp_404 = test_client.post(
        f"/api/events/{event.id}/actions/non-existent-act/verify",
        headers={"x-user-id": organizer.id},
    )
    assert resp_404.status_code == 404
