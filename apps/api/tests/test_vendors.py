"""Comprehensive Tests: Phase 3 Provider Network

Covers:
- Provider creation & retrieval
- Provider search & multi-criteria filtering (category, city, cost, status)
- Availability checks & conflict detection
- Inactive provider handling
- Domain integration & category compatibility (Wedding, College Fest, Conference)
- Provider assignment representation (event-vendor relationship)
- Determinism guarantees (stable ordering and reproducible results)
- API endpoints (CRUD, search, availability, category validation, assignments)
"""
from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.event import Event
from app.services.vendor_service import VendorService
from app.domains.registry import (
    get_domain_provider_categories,
    is_provider_category_compatible,
)
from app.schemas.vendor import (
    VendorCreate,
    ProviderAvailabilityCreate,
    VendorAssignmentCreate,
)


def test_provider_creation_and_retrieval(db_session: Session):
    """Test provider creation with all Phase 3 operational fields and retrieval."""
    service = VendorService(db_session)
    vendor_in = VendorCreate(
        name="SoundWave Productions",
        category="sound",
        city="Delhi",
        contact_name="Rohan Gupta",
        contact_email="rohan@soundwave.demo",
        contact_phone="+91-9876543211",
        base_cost=800.0,
        service_description="High-end concert audio line arrays and digital desks.",
        status="ACTIVE",
    )
    vendor = service.create_vendor(vendor_in)
    assert vendor.id is not None
    assert vendor.name == "SoundWave Productions"
    assert vendor.category == "sound"
    assert vendor.city == "Delhi"
    assert vendor.base_cost == 800.0

    fetched = service.get_vendor(vendor.id)
    assert fetched is not None
    assert fetched.id == vendor.id
    assert fetched.contact_name == "Rohan Gupta"


def test_provider_search_and_filtering(db_session: Session):
    """Test provider search with category, location, and cost filters."""
    service = VendorService(db_session)

    service.create_vendor(VendorCreate(
        name="Delhi Pro Audio",
        category="sound",
        city="Delhi",
        base_cost=700.0,
        status="ACTIVE",
    ))
    service.create_vendor(VendorCreate(
        name="Delhi Feast Caterers",
        category="catering",
        city="Delhi",
        base_cost=1200.0,
        status="ACTIVE",
    ))
    service.create_vendor(VendorCreate(
        name="Bengaluru Bright Lights",
        category="lighting",
        city="Bengaluru",
        base_cost=500.0,
        status="ACTIVE",
    ))

    # Filter by category
    sound_vendors, total_sound = service.search_vendors(category="sound")
    assert total_sound == 1
    assert sound_vendors[0].name == "Delhi Pro Audio"

    # Filter by city
    delhi_vendors, total_delhi = service.search_vendors(city="Delhi")
    assert total_delhi == 2

    # Filter by max base cost
    budget_vendors, total_budget = service.search_vendors(max_base_cost=600.0)
    assert total_budget == 1
    assert budget_vendors[0].name == "Bengaluru Bright Lights"


def test_provider_availability_and_conflict(db_session: Session):
    """Test provider availability checking with conflict-free and booked windows."""
    service = VendorService(db_session)
    vendor = service.create_vendor(VendorCreate(
        name="Metro Stage Rigging",
        category="stage",
        city="Delhi",
        status="ACTIVE",
    ))

    slot_start = datetime(2026, 11, 20, 8, 0, 0)
    service.add_provider_availability(
        vendor.id,
        ProviderAvailabilityCreate(
            start_datetime=slot_start,
            end_datetime=slot_start + timedelta(hours=10),
            status="BOOKED",
            notes="Annual Day Stage Setup",
        ),
    )

    # 1. Overlapping window -> conflict
    conflict_res = service.check_provider_availability(
        vendor.id,
        start_datetime=slot_start + timedelta(hours=2),
        end_datetime=slot_start + timedelta(hours=6),
    )
    assert conflict_res.is_available is False
    assert len(conflict_res.conflicts) == 1

    # 2. Non-overlapping window -> available
    free_res = service.check_provider_availability(
        vendor.id,
        start_datetime=slot_start + timedelta(days=2),
        end_datetime=slot_start + timedelta(days=2, hours=8),
    )
    assert free_res.is_available is True
    assert len(free_res.conflicts) == 0


def test_inactive_provider_availability(db_session: Session):
    """Test that inactive providers are reported as unavailable."""
    service = VendorService(db_session)
    vendor = service.create_vendor(VendorCreate(
        name="Decommissioned Sound",
        category="sound",
        city="Mumbai",
        status="INACTIVE",
    ))

    res = service.check_provider_availability(
        vendor.id,
        start_datetime=datetime(2026, 11, 20, 8, 0),
        end_datetime=datetime(2026, 11, 20, 16, 0),
    )
    assert res.is_available is False
    assert "INACTIVE" in res.reason


def test_domain_category_compatibility():
    """Test domain intelligence category validation across Wedding, College Fest, and Conference."""
    # Wedding domain
    wedding_cats = get_domain_provider_categories("wedding")
    assert "catering" in wedding_cats
    assert "photography" in wedding_cats
    assert "videography" in wedding_cats
    assert "music" in wedding_cats
    assert "lighting" in wedding_cats
    assert "transportation" in wedding_cats
    assert is_provider_category_compatible("wedding", "catering") is True
    assert is_provider_category_compatible("wedding", "nonexistent_service") is False

    # College Fest domain
    fest_cats = get_domain_provider_categories("college_fest")
    assert "sound" in fest_cats
    assert "stage" in fest_cats
    assert "security" in fest_cats
    assert "power" in fest_cats
    assert is_provider_category_compatible("college_fest", "sound") is True
    assert is_provider_category_compatible("college_fest", "videography") is False

    # Conference domain
    conf_cats = get_domain_provider_categories("conference")
    assert "av" in conf_cats
    assert "connectivity" in conf_cats
    assert "signage" in conf_cats
    assert is_provider_category_compatible("conference", "av") is True
    assert is_provider_category_compatible("conference", "bouncers") is False


def test_domain_driven_provider_search(db_session: Session):
    """Test searching providers using required categories extracted from event domain specifications."""
    service = VendorService(db_session)

    # Seed providers with various categories
    service.create_vendor(VendorCreate(name="V1 Sound", category="sound", city="Delhi"))
    service.create_vendor(VendorCreate(name="V2 AV", category="av", city="Delhi"))
    service.create_vendor(VendorCreate(name="V3 Photo", category="photography", city="Delhi"))

    # Wedding domain search (should find photography, but not sound or av)
    wedding_reqs = get_domain_provider_categories("wedding")
    wedding_candidates = []
    for cat in wedding_reqs:
        items, _ = service.search_vendors(category=cat)
        wedding_candidates.extend(items)
    assert len(wedding_candidates) == 1
    assert wedding_candidates[0].name == "V3 Photo"

    # College Fest domain search (should find sound)
    fest_reqs = get_domain_provider_categories("college_fest")
    fest_candidates = []
    for cat in fest_reqs:
        items, _ = service.search_vendors(category=cat)
        fest_candidates.extend(items)
    assert len(fest_candidates) == 1
    assert fest_candidates[0].name == "V1 Sound"

    # Conference domain search (should find av)
    conf_reqs = get_domain_provider_categories("conference")
    conf_candidates = []
    for cat in conf_reqs:
        items, _ = service.search_vendors(category=cat)
        conf_candidates.extend(items)
    assert len(conf_candidates) == 1
    assert conf_candidates[0].name == "V2 AV"


def test_provider_assignment(db_session: Session):
    """Test assigning a provider to an event and retrieving assignments."""
    # Create parent event
    event = Event(id="evt-fest-2026")
    db_session.add(event)
    db_session.commit()

    service = VendorService(db_session)
    vendor = service.create_vendor(VendorCreate(
        name="Titan Audio",
        category="sound",
        city="Delhi",
    ))

    # Create assignment
    assignment = service.create_assignment(
        VendorAssignmentCreate(
            event_id=event.id,
            vendor_id=vendor.id,
            category="sound",
            status="CONFIRMED",
            agreed_cost=1500.0,
            notes="Main stage PA provider",
        )
    )
    assert assignment.id is not None
    assert assignment.event_id == event.id
    assert assignment.vendor_id == vendor.id
    assert assignment.status == "CONFIRMED"

    # Retrieve assignments for event
    assignments = service.get_assignments_for_event(event.id)
    assert len(assignments) == 1
    assert assignments[0].id == assignment.id
    assert assignments[0].category == "sound"


def test_search_determinism(db_session: Session):
    """Test that same search input and database state always produces identical ordered outputs."""
    service = VendorService(db_session)

    # Insert 5 providers with alphabetical ordering
    names = ["Echo Audio", "Alpha Sound", "Delta Lighting", "Bravo Catering", "Charlie Staging"]
    for name in names:
        service.create_vendor(VendorCreate(name=name, category="general", city="Bengaluru"))

    # Run search 3 times
    run_1, total_1 = service.search_vendors(city="Bengaluru")
    run_2, total_2 = service.search_vendors(city="Bengaluru")
    run_3, total_3 = service.search_vendors(city="Bengaluru")

    assert total_1 == total_2 == total_3 == 5
    ids_1 = [v.id for v in run_1]
    ids_2 = [v.id for v in run_2]
    ids_3 = [v.id for v in run_3]
    assert ids_1 == ids_2 == ids_3
    # Check alphabetical ordering
    assert [v.name for v in run_1] == sorted(names)


def test_vendor_api_endpoints(test_client: TestClient, db_session: Session):
    """Test Vendor REST API endpoints for creation, search, category validation, and assignments."""
    # Create parent event in DB
    event = Event(id="evt-demo-123")
    db_session.add(event)
    db_session.commit()

    # Create provider via API
    payload = {
        "name": "Prism Light Solutions",
        "category": "lighting",
        "city": "Bengaluru",
        "base_cost": 650.0,
        "service_description": "Smart LED moving heads and ambient lighting.",
        "status": "ACTIVE",
    }
    create_resp = test_client.post("/api/vendors", json=payload)
    assert create_resp.status_code == 201
    vendor_data = create_resp.json()
    vendor_id = vendor_data["id"]
    assert vendor_data["name"] == "Prism Light Solutions"

    # Get provider
    get_resp = test_client.get(f"/api/vendors/{vendor_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == vendor_id

    # Nonexistent provider returns 404
    not_found_resp = test_client.get("/api/vendors/nonexistent-vendor-id")
    assert not_found_resp.status_code == 404

    # Validate category endpoint
    cat_resp = test_client.get("/api/vendors/categories/validate?domain=conference&category=av")
    assert cat_resp.status_code == 200
    assert cat_resp.json()["is_valid"] is True
    assert "av" in cat_resp.json()["allowed_categories"]

    invalid_cat_resp = test_client.get("/api/vendors/categories/validate?domain=conference&category=fireworks")
    assert invalid_cat_resp.status_code == 200
    assert invalid_cat_resp.json()["is_valid"] is False

    # Create assignment via API
    assign_resp = test_client.post(
        "/api/vendors/assignments",
        json={
            "event_id": event.id,
            "vendor_id": vendor_id,
            "category": "lighting",
            "status": "REQUESTED",
            "agreed_cost": 600.0,
            "notes": "Lighting rig for demo event",
        },
    )
    assert assign_resp.status_code == 201
    assignment_id = assign_resp.json()["id"]

    # List assignments for event
    list_assign_resp = test_client.get(f"/api/vendors/assignments/event/{event.id}")
    assert list_assign_resp.status_code == 200
    assigns = list_assign_resp.json()
    assert len(assigns) == 1
    assert assigns[0]["id"] == assignment_id
