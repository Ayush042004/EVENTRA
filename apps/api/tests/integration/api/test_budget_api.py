"""Integration tests for Budget API endpoints.

Tests GET /api/events/{event_id}/budget/summary and GET /api/events/{event_id}/budget/validate.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.enums import EventLifecycleState


def _setup_planned_event(test_client: TestClient, db: Session) -> str:
    """Helper to create an event and generate an operational plan with budget items."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        name="Budgeted Gala",
        event_type="WEDDING",
        start_datetime=now + timedelta(days=15),
        end_datetime=now + timedelta(days=15, hours=8),
        guest_count=150,
        total_budget=Decimal("60000.00"),
        currency="USD",
        lifecycle_state=EventLifecycleState.DRAFT.value,
        location="Crystal Hall",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Generate plan
    plan_resp = test_client.post(f"/api/events/{event.id}/plan")
    assert plan_resp.status_code == 200
    return event.id


def test_get_budget_summary_api(test_client: TestClient, db_session: Session):
    """Verify GET /api/events/{event_id}/budget/summary returns totals and category breakdown."""
    event_id = _setup_planned_event(test_client, db_session)

    resp = test_client.get(f"/api/events/{event_id}/budget/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["event_id"] == event_id
    assert data["total_budget"] == 60000.0
    assert data["total_estimated"] > 0
    assert data["item_count"] > 0
    assert len(data["categories"]) > 0
    assert len(data["items"]) > 0


def test_validate_budget_api(test_client: TestClient, db_session: Session):
    """Verify GET /api/events/{event_id}/budget/validate validates against ceiling."""
    event_id = _setup_planned_event(test_client, db_session)

    resp = test_client.get(f"/api/events/{event_id}/budget/validate")
    assert resp.status_code == 200
    data = resp.json()

    assert "is_valid" in data
    assert "violations" in data
    assert isinstance(data["violations"], list)


def test_budget_endpoints_not_found(test_client: TestClient):
    """Verify 404 returned for unknown event."""
    resp_sum = test_client.get("/api/events/non-existent-budget-evt/budget/summary")
    assert resp_sum.status_code == 404

    resp_val = test_client.get("/api/events/non-existent-budget-evt/budget/validate")
    assert resp_val.status_code == 404
