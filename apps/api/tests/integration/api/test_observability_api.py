"""Phase 10 Integration Tests: Observability REST APIs (Audit, Activity, Decision Trace, State History)"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, RoleType
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.user import User
from app.models.state_transition import StateTransition
from app.observability.audit import AuditRecorder


def _setup_observability_api_env(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer = User(name="Alice Lead", email="alice.obs@eventra.test")
    stranger = User(name="Eve Stranger", email="eve.obs@eventra.test")
    db.add_all([organizer, stranger])
    db.flush()

    event = Event(
        owner_id=organizer.id,
        name="Observability Summit",
        lifecycle_state=EventLifecycleState.PLANNED.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(days=3),
        end_datetime=now + timedelta(days=3, hours=6),
        total_budget=Decimal("40000.00"),
    )
    db.add(event)
    db.flush()

    mem_org = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    db.add(mem_org)

    # Record some audits via AuditRecorder
    recorder = AuditRecorder(db)
    recorder.record(
        event_id=event.id,
        actor_id=organizer.id,
        actor_type="USER",
        action="UPDATE_TASK",
        action_type="TASK_MANAGEMENT",
        before_state={"status": "READY"},
        after_state={"status": "IN_PROGRESS", "auth_token": "secret-xyz"},  # Should be sanitized
        impact_level="MINOR",
    )

    # Record a state transition
    trans = StateTransition(
        event_id=event.id,
        entity_type="EVENT",
        entity_id=event.id,
        previous_state=EventState.NORMAL.value,
        new_state=EventState.AT_RISK.value,
        reason="Generator failure",
    )
    db.add(trans)
    db.commit()

    return organizer, stranger, event


def test_audit_api_endpoint(test_client: TestClient, db_session: Session):
    organizer, stranger, event = _setup_observability_api_env(db_session)

    resp = test_client.get(
        f"/api/events/{event.id}/audit",
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    record = data["items"][0]
    assert record["event_id"] == event.id
    assert record["action"] == "UPDATE_TASK"
    # Verify sanitization in after_state response
    assert record["after_state"]["auth_token"] == "[REDACTED]"


def test_audit_api_forbidden_for_stranger(test_client: TestClient, db_session: Session):
    organizer, stranger, event = _setup_observability_api_env(db_session)

    resp = test_client.get(
        f"/api/events/{event.id}/audit",
        headers={"x-user-id": stranger.id},
    )
    assert resp.status_code == 403


def test_activity_history_endpoint(test_client: TestClient, db_session: Session):
    organizer, stranger, event = _setup_observability_api_env(db_session)

    resp = test_client.get(
        f"/api/events/{event.id}/activity",
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_decision_trace_endpoint(test_client: TestClient, db_session: Session):
    organizer, stranger, event = _setup_observability_api_env(db_session)

    resp = test_client.get(
        f"/api/events/{event.id}/decision-trace",
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)


def test_state_history_endpoint(test_client: TestClient, db_session: Session):
    organizer, stranger, event = _setup_observability_api_env(db_session)

    resp = test_client.get(
        f"/api/events/{event.id}/state-history",
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1
    item = data["items"][0]
    assert item["previous_state"] == EventState.NORMAL.value
    assert item["new_state"] == EventState.AT_RISK.value
