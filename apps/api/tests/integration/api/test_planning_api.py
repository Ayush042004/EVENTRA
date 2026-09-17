"""Integration tests for Planning API endpoints.

Tests POST /api/events/{event_id}/plan and GET /api/events/{event_id}/plan.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.enums import EventLifecycleState


def _create_event(db: Session, **kwargs) -> Event:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    defaults = {
        "name": "Planning Test Event",
        "event_type": "WEDDING",
        "start_datetime": now + timedelta(days=20),
        "end_datetime": now + timedelta(days=20, hours=8),
        "guest_count": 100,
        "total_budget": Decimal("30000.00"),
        "currency": "USD",
        "lifecycle_state": EventLifecycleState.DRAFT.value,
        "location": "Lakeside Resort",
    }
    defaults.update(kwargs)
    event = Event(**defaults)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_generate_plan_api(test_client: TestClient, db_session: Session):
    """Verify POST /api/events/{event_id}/plan creates a plan and returns EventPlan."""
    event = _create_event(db_session)

    resp = test_client.post(f"/api/events/{event.id}/plan")
    assert resp.status_code == 200
    data = resp.json()

    assert data["event_id"] == event.id
    assert data["lifecycle_state"] == "PLANNED"
    assert data["summary"]["total_tasks"] > 0
    assert data["summary"]["total_dependencies"] > 0
    assert data["summary"]["total_resources"] > 0
    assert data["summary"]["total_budget_items"] > 0
    assert len(data["tasks"]) == data["summary"]["total_tasks"]
    assert len(data["dependencies"]) == data["summary"]["total_dependencies"]
    assert len(data["resources"]) == data["summary"]["total_resources"]
    assert len(data["budget_items"]) == data["summary"]["total_budget_items"]


def test_get_plan_api(test_client: TestClient, db_session: Session):
    """Verify GET /api/events/{event_id}/plan retrieves the generated plan."""
    event = _create_event(db_session)

    # First generate the plan
    gen_resp = test_client.post(f"/api/events/{event.id}/plan")
    assert gen_resp.status_code == 200

    # Retrieve plan
    get_resp = test_client.get(f"/api/events/{event.id}/plan")
    assert get_resp.status_code == 200
    data = get_resp.json()

    assert data["event_id"] == event.id
    assert data["lifecycle_state"] == "PLANNED"
    assert len(data["tasks"]) > 0


def test_generate_plan_not_found(test_client: TestClient):
    """Verify POST /api/events/{event_id}/plan returns 404 for unknown event."""
    resp = test_client.post("/api/events/non-existent-id-999/plan")
    assert resp.status_code == 404


def test_get_plan_not_found(test_client: TestClient):
    """Verify GET /api/events/{event_id}/plan returns 404 for unknown event."""
    resp = test_client.get("/api/events/non-existent-id-999/plan")
    assert resp.status_code == 404
