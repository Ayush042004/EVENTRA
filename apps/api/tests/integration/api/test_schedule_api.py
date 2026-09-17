"""Integration tests for Schedule API endpoints.

Tests POST /api/events/{event_id}/schedule/compute and GET /api/events/{event_id}/schedule.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.enums import EventLifecycleState


def _setup_planned_event(test_client: TestClient, db: Session) -> str:
    """Helper to create an event and generate an operational plan."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        name="Scheduled Conference",
        event_type="CONFERENCE",
        start_datetime=now + timedelta(days=10),
        end_datetime=now + timedelta(days=10, hours=10),
        guest_count=200,
        total_budget=Decimal("50000.00"),
        currency="USD",
        lifecycle_state=EventLifecycleState.DRAFT.value,
        location="Grand Ballroom",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Generate plan
    plan_resp = test_client.post(f"/api/events/{event.id}/plan")
    assert plan_resp.status_code == 200
    return event.id


def test_compute_schedule_api(test_client: TestClient, db_session: Session):
    """Verify POST /api/events/{event_id}/schedule/compute computes and persists schedule."""
    event_id = _setup_planned_event(test_client, db_session)

    resp = test_client.post(f"/api/events/{event_id}/schedule/compute")
    assert resp.status_code == 200
    data = resp.json()

    assert data["event_id"] == event_id
    assert len(data["entries"]) > 0
    assert "critical_path" in data
    assert len(data["critical_path"]["critical_path_tasks"]) > 0
    assert data["is_feasible"] is True

    # Check task entries have datetimes
    for entry in data["entries"]:
        assert entry["planned_start"] is not None
        assert entry["planned_end"] is not None
        assert entry["duration_minutes"] > 0


def test_get_schedule_api(test_client: TestClient, db_session: Session):
    """Verify GET /api/events/{event_id}/schedule returns the schedule."""
    event_id = _setup_planned_event(test_client, db_session)

    # Compute schedule first
    comp_resp = test_client.post(f"/api/events/{event_id}/schedule/compute")
    assert comp_resp.status_code == 200

    # Retrieve schedule
    get_resp = test_client.get(f"/api/events/{event_id}/schedule")
    assert get_resp.status_code == 200
    data = get_resp.json()

    assert data["event_id"] == event_id
    assert len(data["entries"]) > 0
    assert data["project_end"] is not None


def test_compute_schedule_no_tasks(test_client: TestClient, db_session: Session):
    """Verify compute schedule fails with 400 when no tasks have been planned."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        name="Empty Event",
        event_type="WEDDING",
        start_datetime=now + timedelta(days=5),
        end_datetime=now + timedelta(days=5, hours=5),
        guest_count=50,
        lifecycle_state=EventLifecycleState.DRAFT.value,
    )
    db_session.add(event)
    db_session.commit()

    resp = test_client.post(f"/api/events/{event.id}/schedule/compute")
    assert resp.status_code == 400


def test_compute_schedule_not_found(test_client: TestClient):
    """Verify compute schedule returns 404 for unknown event."""
    resp = test_client.post("/api/events/non-existent-sched-evt/schedule/compute")
    assert resp.status_code == 404
