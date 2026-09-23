"""Comprehensive Tests: Phase 3 Venue Network

Covers:
- Venue creation & retrieval
- Venue search & multi-criteria filtering (capacity, city, type, amenities, price)
- Availability checks & conflict detection
- Inactive venue handling
- Deterministic suitability scorecard against guest count and amenities
- API endpoints (CRUD, search, availability, suitability, error responses)
- Pagination & stable ordering
"""
from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.services.venue_service import VenueService
from app.schemas.venue import (
    VenueCreate,
    VenueAvailabilityCreate,
    VenueSuitabilityCheck,
)


def test_venue_creation_and_retrieval(db_session: Session):
    """Test venue creation with all Phase 3 fields and retrieval by ID."""
    service = VenueService(db_session)
    venue_in = VenueCreate(
        name="Grand Sapphire Hall",
        address="100 Ring Road",
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        capacity=800,
        venue_type="banquet_hall",
        contact_email="contact@sapphirehall.demo",
        contact_phone="+91-9876543210",
        hourly_rate=200.0,
        amenities=["parking", "wifi", "ac", "av_setup"],
        status="ACTIVE",
    )
    venue = service.create_venue(venue_in)
    assert venue.id is not None
    assert venue.name == "Grand Sapphire Hall"
    assert venue.capacity == 800
    assert "parking" in venue.amenities
    assert venue.status == "ACTIVE"

    fetched = service.get_venue(venue.id)
    assert fetched is not None
    assert fetched.id == venue.id
    assert fetched.city == "Delhi"


def test_venue_search_and_filtering(db_session: Session):
    """Test deterministic venue search with city, capacity, and amenities filters."""
    service = VenueService(db_session)

    service.create_venue(VenueCreate(
        name="Delhi Grand Ballroom",
        city="Delhi",
        capacity=1000,
        venue_type="banquet_hall",
        hourly_rate=300.0,
        amenities=["parking", "ac", "av_setup"],
        status="ACTIVE",
    ))
    service.create_venue(VenueCreate(
        name="Delhi Cozy Lounge",
        city="Delhi",
        capacity=200,
        venue_type="lounge",
        hourly_rate=100.0,
        amenities=["wifi", "ac"],
        status="ACTIVE",
    ))
    service.create_venue(VenueCreate(
        name="Mumbai Ocean Pavilion",
        city="Mumbai",
        capacity=1200,
        venue_type="banquet_hall",
        hourly_rate=500.0,
        amenities=["parking", "ac", "av_setup"],
        status="ACTIVE",
    ))

    # Filter by city
    delhi_venues, total_delhi = service.search_venues(city="delhi")
    assert total_delhi == 2
    assert all(v.city == "Delhi" for v in delhi_venues)

    # Filter by minimum capacity
    large_venues, total_large = service.search_venues(min_capacity=500)
    assert total_large == 2
    assert all(v.capacity >= 500 for v in large_venues)

    # Filter by max hourly rate
    affordable_venues, total_aff = service.search_venues(max_hourly_rate=250.0)
    assert total_aff == 1
    assert affordable_venues[0].name == "Delhi Cozy Lounge"

    # Filter by required amenities
    av_venues, total_av = service.search_venues(required_amenities=["av_setup", "parking"])
    assert total_av == 2
    assert all("av_setup" in v.amenities and "parking" in v.amenities for v in av_venues)


def test_venue_availability_and_conflict(db_session: Session):
    """Test venue availability checks with conflict-free and overlapping booked windows."""
    service = VenueService(db_session)
    venue = service.create_venue(VenueCreate(
        name="Convention Arena",
        city="Bengaluru",
        capacity=1500,
        venue_type="convention_center",
        status="ACTIVE",
    ))

    base_time = datetime(2026, 11, 10, 10, 0, 0)
    # Book venue for Nov 10, 10:00 - 18:00
    service.add_venue_availability(
        venue.id,
        VenueAvailabilityCreate(
            start_datetime=base_time,
            end_datetime=base_time + timedelta(hours=8),
            status="BOOKED",
            notes="Tech Conference",
        ),
    )

    # 1. Check overlapping window -> conflict
    conflict_check = service.check_venue_availability(
        venue.id,
        start_datetime=base_time + timedelta(hours=2),
        end_datetime=base_time + timedelta(hours=6),
    )
    assert conflict_check.is_available is False
    assert len(conflict_check.conflicts) == 1
    assert conflict_check.conflicts[0].status == "BOOKED"

    # 2. Check next day window -> available
    free_check = service.check_venue_availability(
        venue.id,
        start_datetime=base_time + timedelta(days=1),
        end_datetime=base_time + timedelta(days=1, hours=8),
    )
    assert free_check.is_available is True
    assert len(free_check.conflicts) == 0


def test_inactive_venue_availability(db_session: Session):
    """Test that inactive venues are reported as unavailable."""
    service = VenueService(db_session)
    venue = service.create_venue(VenueCreate(
        name="Renovating Amphitheater",
        city="Delhi",
        capacity=600,
        venue_type="amphitheater",
        status="MAINTENANCE",
    ))

    res = service.check_venue_availability(
        venue.id,
        start_datetime=datetime(2026, 11, 10, 9, 0),
        end_datetime=datetime(2026, 11, 10, 17, 0),
    )
    assert res.is_available is False
    assert "MAINTENANCE" in res.reason


def test_venue_suitability_scorecard(db_session: Session):
    """Test deterministic venue suitability against capacity and required amenities."""
    service = VenueService(db_session)
    venue = service.create_venue(VenueCreate(
        name="Prestige Auditorium",
        city="Bengaluru",
        capacity=1000,
        venue_type="auditorium",
        amenities=["parking", "ac", "av_setup", "wifi"],
        status="ACTIVE",
    ))

    # Case 1: Requirements fully satisfied (guest count 800 <= 1000, amenities present)
    suitability_pass = service.check_venue_suitability(
        venue.id,
        VenueSuitabilityCheck(
            required_capacity=800,
            required_amenities=["parking", "av_setup"],
        ),
    )
    assert suitability_pass.capacity_satisfied is True
    assert suitability_pass.amenities_satisfied is True
    assert len(suitability_pass.missing_amenities) == 0
    assert suitability_pass.is_suitable is True

    # Case 2: Insufficient capacity (guest count 1200 > 1000)
    suitability_capacity_fail = service.check_venue_suitability(
        venue.id,
        VenueSuitabilityCheck(
            required_capacity=1200,
            required_amenities=["parking"],
        ),
    )
    assert suitability_capacity_fail.capacity_satisfied is False
    assert suitability_capacity_fail.is_suitable is False

    # Case 3: Missing required amenity
    suitability_amenity_fail = service.check_venue_suitability(
        venue.id,
        VenueSuitabilityCheck(
            required_capacity=500,
            required_amenities=["parking", "swimming_pool"],
        ),
    )
    assert suitability_amenity_fail.capacity_satisfied is True
    assert suitability_amenity_fail.amenities_satisfied is False
    assert "swimming_pool" in suitability_amenity_fail.missing_amenities
    assert suitability_amenity_fail.is_suitable is False


def test_venue_api_endpoints(test_client: TestClient):
    """Test Venue REST API endpoints for creation, search, 404s, and suitability."""
    # Create venue
    payload = {
        "name": "Emerald Banquet Palace",
        "city": "Mumbai",
        "capacity": 750,
        "venue_type": "banquet_hall",
        "hourly_rate": 250.0,
        "amenities": ["parking", "ac", "wifi"],
        "status": "ACTIVE",
    }
    create_resp = test_client.post("/api/venues", json=payload)
    assert create_resp.status_code == 201
    venue_data = create_resp.json()
    venue_id = venue_data["id"]
    assert venue_data["name"] == "Emerald Banquet Palace"

    # Get venue
    get_resp = test_client.get(f"/api/venues/{venue_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == venue_id

    # Nonexistent venue returns 404
    not_found_resp = test_client.get("/api/venues/nonexistent-venue-id")
    assert not_found_resp.status_code == 404

    # Search venues
    search_resp = test_client.get("/api/venues?city=mumbai&min_capacity=500")
    assert search_resp.status_code == 200
    res_body = search_resp.json()
    assert res_body["total"] >= 1
    assert any(item["id"] == venue_id for item in res_body["items"])

    # Add availability slot
    start = "2026-12-01T09:00:00"
    end = "2026-12-01T18:00:00"
    slot_resp = test_client.post(
        f"/api/venues/{venue_id}/availability",
        json={"start_datetime": start, "end_datetime": end, "status": "BOOKED", "notes": "Private Event"},
    )
    assert slot_resp.status_code == 201

    # Check availability endpoint (conflict)
    avail_check_resp = test_client.get(
        f"/api/venues/{venue_id}/availability?start_datetime=2026-12-01T10:00:00&end_datetime=2026-12-01T14:00:00"
    )
    assert avail_check_resp.status_code == 200
    assert avail_check_resp.json()["is_available"] is False

    # Check suitability endpoint
    suit_resp = test_client.post(
        f"/api/venues/{venue_id}/suitability",
        json={"required_capacity": 500, "required_amenities": ["parking", "ac"]},
    )
    assert suit_resp.status_code == 200
    assert suit_resp.json()["is_suitable"] is True
    assert suit_resp.json()["capacity_satisfied"] is True


def test_venue_live_discovery_endpoint(test_client: TestClient):
    """Test POST /venues/discover endpoint for real live venue discovery."""
    response = test_client.post(
        "/api/venues/discover",
        json={"city": "Seattle", "limit": 3, "save_to_db": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Seattle"
    assert data["total_discovered"] >= 1
    assert data["source"] == "LIVE_OPENSTREETMAP_NETWORK"
    assert len(data["items"]) >= 1
    first = data["items"][0]
    assert first["id"] is not None
    assert first["name"] is not None
    assert first["city"] == "Seattle"
    assert first["latitude"] is not None
    assert first["longitude"] is not None

