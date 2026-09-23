"""Tests for Provider Discovery Endpoints (/vendors/discover and /events/{id}/providers/discover)."""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.venue import Venue
from app.models.vendor import Vendor


def test_global_vendor_discovery_api(test_client: TestClient, db_session: Session):
    payload = {
        "category": "CATERING",
        "query": "wedding caterers",
        "location": "Noida",
        "limit": 10,
    }
    response = test_client.post("/api/vendors/discover", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total_discovered"] > 0
    assert len(data["items"]) > 0
    assert data["source"] in ("REAL", "MOCK")

    # Verify first discovered item properties
    first_item = data["items"][0]
    assert first_item["category"] == "CATERING"
    assert first_item["city"] == "Noida"
    assert first_item["base_cost"] is not None
    assert first_item["status"] == "ACTIVE"

    # Verify records persisted in database
    db_vendors = db_session.query(Vendor).filter(Vendor.category == "CATERING").all()
    assert len(db_vendors) >= len(data["items"])


def test_event_scoped_provider_discovery_api(test_client: TestClient, db_session: Session):
    # Setup test venue and event
    venue = Venue(
        id="venue-noida-grand",
        name="Grand Noida Ballroom",
        city="Noida",
        address="Sector 128, Expressway, Noida",
        latitude=28.5123,
        longitude=77.3891,
        capacity=600,
        venue_type="BANQUET",
    )
    db_session.add(venue)
    db_session.flush()

    event = Event(
        id="event-wedding-001",
        name="Priya & Rahul Wedding",
        event_type="WEDDING",
        location="Noida",
        start_datetime=datetime.now(timezone.utc),
        end_datetime=datetime.now(timezone.utc),
        guest_count=500,
        owner_id="anonymous_operator",
    )
    db_session.add(event)
    db_session.commit()

    # Discover without explicit location - should automatically inherit from event venue!
    payload = {
        "category": "DECOR",
        "query": "floral stage decoration",
        "limit": 5,
    }
    response = test_client.post(f"/api/events/{event.id}/providers/discover", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["event_id"] == event.id
    assert data["total_discovered"] > 0
    for item in data["items"]:
        assert item["category"] == "DECOR"
        assert item["city"] == "Noida"  # Inherited from venue


def test_discovery_for_nonexistent_event(test_client: TestClient):
    response = test_client.post(
        "/api/events/nonexistent-id-12345/providers/discover",
        json={"category": "CATERING"},
    )
    assert response.status_code == 404
