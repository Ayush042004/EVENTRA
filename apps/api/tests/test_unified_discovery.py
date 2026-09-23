"""Tests for EVENTRA Unified Location-Aware Provider & Venue Discovery Layer."""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.venue import Venue
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.integrations.google_maps_scraper.queries import (
    CATEGORY_SEARCH_QUERIES,
    build_discovery_query,
    parse_discovery_query,
)
from app.services.vendor_service import haversine_distance_km, VendorService
from app.schemas.vendor import ProviderDiscoveryRequest


def test_category_queries_mapping():
    """Verifies that all controlled categories have deterministic query mappings."""
    controlled_categories = [
        "VENUE", "CATERING", "DECOR", "PHOTOGRAPHY", "VIDEOGRAPHY",
        "DJ_MUSIC", "LIGHTING", "AV_TECH", "ENTERTAINMENT", "TRANSPORT",
        "SECURITY", "STAFFING", "MAKEUP_STYLING", "PRINTING", "RENTALS",
        "FLORIST", "PRODUCTION", "CLEANING", "OTHER"
    ]
    for cat in controlled_categories:
        queries = build_discovery_query(category=cat, location="Seattle")
        assert len(queries) >= 1
        assert any("Seattle" in q for q in queries)


def test_natural_language_query_parser():
    """Verifies natural language query parsing into structured discovery parameters."""
    # 1. Category + Near Venue
    res1 = parse_discovery_query("find photographers near venue")
    assert res1["category"] == "PHOTOGRAPHY"
    assert res1["anchor_mode"] == "NEAR_EVENT"
    assert "photographers" in res1["clean_query"]

    # 2. Category + Radius in km
    res2 = parse_discovery_query("wedding caterers within 10km")
    assert res2["category"] == "CATERING"
    assert res2["radius_km"] == 10.0
    assert "wedding caterers" in res2["clean_query"]

    # 3. Category + Radius in miles (converted to km)
    res3 = parse_discovery_query("event decorators within 5 miles")
    assert res3["category"] == "DECOR"
    assert res3["radius_km"] == pytest.approx(8.0, 0.1)

    # 4. Near Me
    res4 = parse_discovery_query("AV companies near me")
    assert res4["category"] == "AV_TECH"
    assert res4["anchor_mode"] == "NEAR_ME"

    # 5. Explicit Region + Radius
    res5 = parse_discovery_query("security guards in Seattle within 25km")
    assert res5["category"] == "SECURITY"
    assert res5["location"] == "Seattle"
    assert res5["radius_km"] == 25.0


def test_haversine_distance_calculation():
    """Verifies great-circle Haversine distance formula."""
    # Seattle Space Needle (47.6205, -122.3493) to Pike Place Market (47.6097, -122.3422) ~ 1.3 km
    dist = haversine_distance_km(47.6205, -122.3493, 47.6097, -122.3422)
    assert 1.1 <= dist <= 1.5

    # Same coordinates should be 0.0 km
    assert haversine_distance_km(47.6062, -122.3321, 47.6062, -122.3321) == 0.0


def test_location_aware_provider_discovery_api(test_client: TestClient, db_session: Session):
    """Verifies event-anchored provider discovery with distance calculation and assignment status."""
    # Setup venue and event
    venue = Venue(
        id="venue-seattle-arch",
        name="Seattle Convention Center Arch",
        city="Seattle",
        address="800 Convention Place, Seattle",
        latitude=47.6115,
        longitude=-122.3332,
        capacity=2000,
        hourly_rate=650.0,
        venue_type="CONVENTION_CENTER",
    )
    db_session.add(venue)
    db_session.flush()

    event = Event(
        id="event-discovery-test-01",
        name="Cloud Developer Summit",
        event_type="CONFERENCE",
        location="Seattle, WA",
        start_datetime=datetime.now(timezone.utc),
        end_datetime=datetime.now(timezone.utc),
        guest_count=400,
        owner_id="test_admin",
    )
    event.venue_id = venue.id
    db_session.add(event)
    db_session.commit()

    # Pre-assign a vendor to test is_assigned flag
    assigned_vendor = Vendor(
        id="vnd-preassigned-001",
        name="Elite Audio Visual Seattle",
        category="AV_TECH",
        city="Seattle",
        address="Pike Street, Seattle",
        latitude=47.6105,
        longitude=-122.3340,
        status="ACTIVE",
        source="LIVE_OPENSTREETMAP_NETWORK",
        capabilities=["av_production", "sound_system"],
    )
    db_session.add(assigned_vendor)
    db_session.flush()

    assignment = VendorAssignment(
        id="asgn-test-001",
        event_id=event.id,
        vendor_id=assigned_vendor.id,
        category="AV_TECH",
        status="CONFIRMED",
    )
    db_session.add(assignment)
    db_session.commit()

    # Test discovery using natural language query
    payload = {
        "query": "AV companies near venue",
        "radius_km": 15.0,
    }
    response = test_client.post(f"/api/events/{event.id}/providers/discover", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["event_id"] == event.id
    assert data["total_discovered"] > 0
    assert data["anchor_label"] is not None
    assert data["anchor_coordinates"] is not None

    # Check discovered items
    found_assigned = False
    for item in data["items"]:
        assert item["category"] == "AV_TECH"
        # Verify distance is computed
        if item["latitude"] and item["longitude"]:
            assert item["distance_km"] is not None
            assert item["distance_km"] <= 15.0  # within radius!
        if item["id"] == assigned_vendor.id:
            found_assigned = True
            assert item["is_assigned"] is True

    # Items should be sorted by distance ascending
    distances = [it["distance_km"] for it in data["items"] if it.get("distance_km") is not None]
    assert distances == sorted(distances)


def test_user_cases_query_parsing():
    """Validates the exact 6 user test cases."""
    # CASE 1: photographers near venue
    c1 = parse_discovery_query("photographers near venue")
    assert c1["category"] == "PHOTOGRAPHY"
    assert c1["anchor_mode"] == "NEAR_EVENT"

    # CASE 2: caterers within 10km
    c2 = parse_discovery_query("caterers within 10km")
    assert c2["category"] == "CATERING"
    assert c2["radius_km"] == 10.0

    # CASE 3: AV companies near event
    c3 = parse_discovery_query("AV companies near event")
    assert c3["category"] == "AV_TECH"
    assert c3["anchor_mode"] == "NEAR_EVENT"

    # CASE 4: photographers in Delhi
    c4 = parse_discovery_query("photographers in Delhi")
    assert c4["category"] == "PHOTOGRAPHY"
    assert c4["anchor_mode"] == "REGION"
    assert c4["location"].lower() == "delhi"

    # CASE 5: photographers near me
    c5 = parse_discovery_query("photographers near me")
    assert c5["category"] == "PHOTOGRAPHY"
    assert c5["anchor_mode"] == "NEAR_ME"

    # CASE 6: Delhi (standalone city query)
    c6 = parse_discovery_query("Delhi")
    assert c6["anchor_mode"] == "REGION"
    assert c6["location"].lower() == "delhi"


def test_strict_evidence_based_classification():
    """Verifies that non-event businesses (plumbers, labs, streets) are never forced into PHOTOGRAPHY."""
    from app.services.provider_classifier import ProviderClassifier
    from app.integrations.google_maps_scraper.models import NormalizedProvider
    from app.services.deduplication import ProviderDeduplicator

    # Plumber must classify as OTHER, not PHOTOGRAPHY
    res_plumber = ProviderClassifier.classify("Seattle Plumbing Pros", raw_category="plumber")
    assert res_plumber.category == "OTHER"

    # Laboratory must classify as OTHER, not PHOTOGRAPHY
    res_lab = ProviderClassifier.classify("ARCpoint Labs of Seattle West", raw_category="laboratory")
    assert res_lab.category == "OTHER"

    # Street/Highway must classify as OTHER, not PHOTOGRAPHY
    res_street = ProviderClassifier.classify("Delridge Way Southwest", raw_category="primary")
    assert res_street.category == "OTHER"

    # Real photography studio must classify as PHOTOGRAPHY
    res_photo = ProviderClassifier.classify("Adonis Commercial Photography", raw_category="photographer")
    assert res_photo.category == "PHOTOGRAPHY"


def test_zero_fabricated_pricing_in_discovery():
    """Verifies that discovered providers without legitimate price data have base_cost=None."""
    from app.services.geospatial_service import geospatial_discovery

    providers = geospatial_discovery.discover_real_providers("PHOTOGRAPHY", "Seattle", limit=3)
    for p in providers:
        # No fabricated $2500/hr
        assert p.get("base_cost") is None
        # Raw category must be preserved
        assert "raw_category" in p
        assert p["raw_category"] is not None
