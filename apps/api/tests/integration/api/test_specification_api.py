"""Integration tests for Event Specification API endpoints."""
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def test_get_specification_demo_events(test_client: TestClient):
    """Verify GET /api/events/{event_id}/specification resolves demo events deterministically."""
    # 1. Wedding demo
    resp_wedding = test_client.get("/api/events/wedding_demo/specification")
    assert resp_wedding.status_code == 200
    wedding_data = resp_wedding.json()
    assert wedding_data["event_id"] == "wedding_demo"
    assert wedding_data["event_type"] == "WEDDING"
    assert len(wedding_data["requirements"]) > 0
    assert len(wedding_data["tasks"]) > 0
    assert len(wedding_data["dependencies"]) > 0
    assert "catering" in wedding_data["provider_categories"]

    # 2. College Fest demo
    resp_fest = test_client.get("/api/events/college_fest_demo/specification")
    assert resp_fest.status_code == 200
    fest_data = resp_fest.json()
    assert fest_data["event_id"] == "college_fest_demo"
    assert fest_data["event_type"] == "COLLEGE_FEST"
    assert "sound" in fest_data["provider_categories"]

    # 3. Conference demo
    resp_conf = test_client.get("/api/events/conference_demo/specification")
    assert resp_conf.status_code == 200
    conf_data = resp_conf.json()
    assert conf_data["event_id"] == "conference_demo"
    assert conf_data["event_type"] == "CONFERENCE"
    assert "av" in conf_data["provider_categories"]


def test_get_specification_not_found(test_client: TestClient):
    """Verify non-existent event ID returns 404."""
    resp = test_client.get("/api/events/non-existent-event-xyz/specification")
    assert resp.status_code == 404
    data = resp.json()
    error_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
    assert "not found" in error_msg.lower()


def test_get_specification_for_db_created_event(test_client: TestClient, db_session: Session):
    """Verify creating an event in the DB and then fetching its specification."""
    # Create test owner
    user = User(name="Spec Owner", email="event_spec_owner@example.com")
    db_session.add(user)
    db_session.commit()

    start = (datetime.now(timezone.utc) + timedelta(days=30)).replace(tzinfo=None).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=30, hours=8)).replace(tzinfo=None).isoformat()

    # Create event via API
    create_resp = test_client.post(
        "/api/events",
        json={
            "name": "Annual Alumni Gala",
            "event_type": "WEDDING",
            "start_datetime": start,
            "end_datetime": end,
            "guest_count": 200,
            "total_budget": 45000.0,
            "currency": "USD",
            "owner_id": user.id,
        },
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # Fetch specification
    spec_resp = test_client.get(f"/api/events/{event_id}/specification")
    assert spec_resp.status_code == 200
    spec_data = spec_resp.json()
    assert spec_data["event_id"] == event_id
    assert spec_data["title"] == "Annual Alumni Gala"
    assert spec_data["event_type"] == "WEDDING"
    assert spec_data["guest_count"] == 200
    assert len(spec_data["tasks"]) > 0


def test_preview_specification_success(test_client: TestClient):
    """Verify POST /api/events/specification/preview builds and returns a valid preview."""
    payload = {
        "title": "Preview Summit",
        "description": "Tech preview conference",
        "event_type": "CONFERENCE",
        "start_time": "2026-11-10T09:00:00",
        "end_time": "2026-11-10T18:00:00",
        "guest_count": 350,
        "total_budget": 30000.0,
        "custom_requirements": [
            {
                "key": "custom.keynote_speaker",
                "category": "TALENT",
                "name": "Celebrity Keynote",
                "is_mandatory": True,
            }
        ],
        "constraints": [
            {
                "constraint_type": "BUDGET_CAP",
                "parameters": {"max_limit": 30000},
                "description": "Strict hard cap on spend",
            }
        ],
        "objectives": [
            {
                "title": "Flawless Live Stream",
                "priority": "HIGH",
                "description": "Stream to 5,000 online attendees",
            }
        ],
    }

    resp = test_client.post("/api/events/specification/preview", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["title"] == "Preview Summit"
    assert data["event_type"] == "CONFERENCE"
    assert any(r["key"] == "custom.keynote_speaker" for r in data["requirements"])
    assert any(c["constraint_type"] == "BUDGET_CAP" for c in data["constraints"])
    assert any(o["title"] == "Flawless Live Stream" for o in data["objectives"])


def test_preview_specification_invalid_date_order(test_client: TestClient):
    """Verify preview fails with 400 if end_time <= start_time."""
    payload = {
        "title": "Invalid Date Summit",
        "event_type": "CONFERENCE",
        "start_time": "2026-11-10T18:00:00",
        "end_time": "2026-11-10T09:00:00",
        "guest_count": 100,
    }

    resp = test_client.post("/api/events/specification/preview", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    error_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
    assert "logical date violation" in error_msg.lower()


def test_preview_specification_unsupported_type(test_client: TestClient):
    """Verify preview fails with 400 for unknown event type."""
    payload = {
        "title": "Carnival",
        "event_type": "CARNIVAL",
        "start_time": "2026-11-10T09:00:00",
        "end_time": "2026-11-10T18:00:00",
        "guest_count": 100,
    }

    resp = test_client.post("/api/events/specification/preview", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    error_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
    assert "unsupported event type" in error_msg.lower()


def test_preview_specification_negative_guests(test_client: TestClient):
    """Verify preview fails with 400 for negative guest capacity."""
    payload = {
        "title": "Negative Guest Summit",
        "event_type": "WEDDING",
        "start_time": "2026-11-10T09:00:00",
        "end_time": "2026-11-10T18:00:00",
        "guest_count": -10,
    }

    resp = test_client.post("/api/events/specification/preview", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    error_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
    assert "invalid guest count" in error_msg.lower()
