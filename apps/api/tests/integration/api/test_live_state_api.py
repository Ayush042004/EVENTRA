"""Integration tests for Live State API endpoints.

Tests POST /api/events/{event_id}/go-live,
GET /api/events/{event_id}/live-state,
PUT /api/events/{event_id}/tasks/{task_id}/status,
and POST /api/events/{event_id}/conclude.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.task import Task
from app.models.enums import EventLifecycleState, TaskStatus


def _setup_scheduled_event(test_client: TestClient, db: Session) -> str:
    """Creates an event, generates plan, and computes schedule."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        name="Tech Summit Live",
        event_type="CONFERENCE",
        start_datetime=now + timedelta(days=1),
        end_datetime=now + timedelta(days=1, hours=8),
        guest_count=300,
        total_budget=Decimal("70000.00"),
        currency="USD",
        lifecycle_state=EventLifecycleState.DRAFT.value,
        location="Convention Arena",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # 1. Plan
    p_resp = test_client.post(f"/api/events/{event.id}/plan")
    assert p_resp.status_code == 200

    # 2. Schedule
    s_resp = test_client.post(f"/api/events/{event.id}/schedule/compute")
    assert s_resp.status_code == 200

    return event.id


def test_live_lifecycle_end_to_end(test_client: TestClient, db_session: Session):
    """Verify full live lifecycle: go-live -> status update -> live-state -> complete tasks -> conclude."""
    event_id = _setup_scheduled_event(test_client, db_session)

    # 1. Go Live
    go_live_resp = test_client.post(
        f"/api/events/{event_id}/go-live",
        json={"reason": "Doors opening"},
    )
    assert go_live_resp.status_code == 200
    state = go_live_resp.json()
    assert state["lifecycle_state"] == "LIVE"
    assert state["total_tasks"] > 0

    # 2. Find a READY task to progress
    tasks = db_session.query(Task).filter(Task.event_id == event_id).all()
    ready_task = next(t for t in tasks if t.status == "READY")

    # Update to IN_PROGRESS
    now_iso = datetime.now(timezone.utc).isoformat()
    update_resp = test_client.put(
        f"/api/events/{event_id}/tasks/{ready_task.id}/status",
        json={"status": "IN_PROGRESS", "actual_start": now_iso},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "IN_PROGRESS"

    # Complete the task
    end_iso = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    complete_resp = test_client.put(
        f"/api/events/{event_id}/tasks/{ready_task.id}/status",
        json={"status": "COMPLETED", "actual_end": end_iso},
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"

    # 3. Check Live State Snapshot
    get_live_resp = test_client.get(f"/api/events/{event_id}/live-state")
    assert get_live_resp.status_code == 200
    live_data = get_live_resp.json()
    assert live_data["event_id"] == event_id
    assert live_data["completed_tasks"] >= 1
    assert live_data["progress_percent"] > 0.0

    # 4. Complete all remaining tasks to allow conclusion
    for t in tasks:
        t.status = TaskStatus.COMPLETED.value
    db_session.commit()

    # 5. Conclude Event
    conclude_resp = test_client.post(
        f"/api/events/{event_id}/conclude",
        json={"reason": "Event ended successfully"},
    )
    assert conclude_resp.status_code == 200
    concluded_state = conclude_resp.json()
    assert concluded_state["lifecycle_state"] == "CONCLUDED"


def test_go_live_unplanned_fails(test_client: TestClient, db_session: Session):
    """Verify go-live fails with 400 when event is not in PLANNED state."""
    event = Event(
        name="Draft Event",
        event_type="WEDDING",
        lifecycle_state=EventLifecycleState.DRAFT.value,
    )
    db_session.add(event)
    db_session.commit()

    resp = test_client.post(f"/api/events/{event.id}/go-live")
    assert resp.status_code == 400


def test_live_endpoints_not_found(test_client: TestClient):
    """Verify 404 for unknown event ID across live endpoints."""
    bad_id = "non-existent-live-999"
    assert test_client.post(f"/api/events/{bad_id}/go-live").status_code == 404
    assert test_client.get(f"/api/events/{bad_id}/live-state").status_code == 404
    assert test_client.post(f"/api/events/{bad_id}/conclude").status_code == 404
