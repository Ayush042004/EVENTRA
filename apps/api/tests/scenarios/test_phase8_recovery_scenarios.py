"""Comprehensive Phase 8 recovery scenario integration tests."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.task import Task
from app.models.dependency import TaskDependency
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.resource import Resource
from app.models.venue import Venue
from app.models.user import User
from app.services.recovery_service import RecoveryService


def test_core_demo_scenario_college_fest_caterer_no_show(test_client: TestClient, db_session: Session):
    """Core Demo Scenario:
    EVENT: College Fest
    TASK CHAIN: Caterer Setup -> Food Service Ready -> Guest Meal Service
    CURRENT: Caterer A assigned
    INCIDENT: Caterer A NO-SHOW
    PHASE 7: Impact + Risk calculated
    PHASE 8: Recovery options generated, simulated, validated, scored
    VERIFY: No real database state mutation occurs (no vendor booked, no schedule changed).
    """
    user = User(name="Fest Coordinator", email="coordinator@collegefest.test")
    db_session.add(user)
    db_session.flush()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        owner_id=user.id,
        name="College Fest 2026",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now,
        end_datetime=now + timedelta(hours=6),
        total_budget=Decimal("5000.00"),
        guest_count=400,
    )
    db_session.add(event)
    db_session.flush()

    t_setup = Task(
        event_id=event.id,
        name="Caterer Setup",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        required_provider_category="catering",
        duration_minutes=45,
        slack_minutes=60,
    )
    t_ready = Task(
        event_id=event.id,
        name="Food Service Ready",
        status=TaskStatus.PENDING.value,
        priority=TaskPriority.HIGH.value,
        required_provider_category="catering",
        duration_minutes=30,
    )
    t_meal = Task(
        event_id=event.id,
        name="Guest Meal Service",
        status=TaskStatus.PENDING.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=60,
    )

    cat_a = Vendor(name="Caterer A", category="catering", city="Mumbai", base_cost=400.0, status="ACTIVE")
    cat_b = Vendor(name="Caterer B", category="catering", city="Mumbai", base_cost=450.0, status="ACTIVE")

    db_session.add_all([t_setup, t_ready, t_meal, cat_a, cat_b])
    db_session.flush()

    db_session.add_all([
        TaskDependency(event_id=event.id, predecessor_task_id=t_setup.id, successor_task_id=t_ready.id),
        TaskDependency(event_id=event.id, predecessor_task_id=t_ready.id, successor_task_id=t_meal.id),
        VendorAssignment(event_id=event.id, vendor_id=cat_a.id, category="catering", agreed_cost=400.0, status="CONFIRMED"),
    ])
    db_session.commit()

    # Step 1: Trigger Incident via API (populates Phase 7 impact & risk)
    inc_resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "VENDOR_NO_SHOW",
            "title": "Caterer A No-Show",
            "related_task_id": t_setup.id,
            "related_vendor_id": cat_a.id,
            "evidence_metadata": {"delay_minutes": 45, "provider_eta_minutes": {cat_b.id: 20}},
        },
        headers={"x-user-id": user.id},
    )
    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    db_session.refresh(event)
    state_before_recovery = event.state

    # Step 2: Generate Recovery Options via Phase 8 API
    rec_resp = test_client.post(
        f"/api/events/{event.id}/incidents/{incident_id}/recovery/options",
        headers={"x-user-id": user.id},
    )
    assert rec_resp.status_code == 201
    data = rec_resp.json()
    items = data["items"]
    assert items

    # Step 3: Validate Feasible Recovery Options
    backup_opts = [item for item in items if item["strategy_type"] == "BACKUP"]
    assert backup_opts
    backup_opt = backup_opts[0]

    assert backup_opt["is_feasible"] is True
    assert backup_opt["score"] is not None
    assert backup_opt["rank"] is not None
    assert backup_opt["budget_delta"]["net_delta"] == 50.0  # 450 - 400
    assert backup_opt["schedule_delta"]["total_delay_change_minutes"] >= 0

    # Step 4: Verify Non-Execution (Strict Phase 8 Requirement)
    db_session.refresh(event)
    db_session.refresh(t_setup)
    db_session.refresh(cat_a)
    db_session.refresh(cat_b)

    # Event state remained unchanged by Phase 8 recovery options generation
    assert event.state == state_before_recovery
    assert t_setup.status == TaskStatus.READY.value
    assert cat_a.status == "ACTIVE"
    assert cat_b.status == "ACTIVE"

    # Verify no new vendor assignment was added to DB
    assignments = db_session.query(VendorAssignment).filter(VendorAssignment.event_id == event.id).all()
    assert len(assignments) == 1
    assert assignments[0].vendor_id == cat_a.id


def test_resource_shortage_recovery_scenario(test_client: TestClient, db_session: Session):
    user = User(name="Ops Lead", email="ops@eventra.test")
    db_session.add(user)
    db_session.flush()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        owner_id=user.id,
        name="Tech Conference",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now,
        end_datetime=now + timedelta(hours=8),
        total_budget=Decimal("20000.00"),
    )
    db_session.add(event)
    db_session.flush()

    task = Task(event_id=event.id, name="AV Setup", status=TaskStatus.READY.value, duration_minutes=60)
    res1 = Resource(event_id=event.id, name="Main Projector", type="EQUIPMENT", status="DEFECTIVE", quantity=0)
    res2 = Resource(event_id=event.id, name="Backup Projector", type="EQUIPMENT", status="AVAILABLE", quantity=2)
    db_session.add_all([task, res1, res2])
    db_session.commit()

    inc_resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "RESOURCE_SHORTAGE",
            "title": "Main Projector Defective",
            "related_task_id": task.id,
            "related_resource_id": res1.id,
            "evidence_metadata": {"shortage_quantity": 1},
        },
        headers={"x-user-id": user.id},
    )
    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    rec_resp = test_client.post(
        f"/api/events/{event.id}/incidents/{incident_id}/recovery/options",
        headers={"x-user-id": user.id},
    )
    assert rec_resp.status_code == 201
    items = rec_resp.json()["items"]
    reassign_opts = [item for item in items if item["strategy_type"] == "REASSIGN" and res2.id in item["affected_resources"]]
    assert reassign_opts
    assert reassign_opts[0]["is_feasible"] is True


def test_venue_issue_recovery_validation(test_client: TestClient, db_session: Session):
    user = User(name="Venue Mgr", email="venue@eventra.test")
    db_session.add(user)
    db_session.flush()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        owner_id=user.id,
        name="Gala Dinner",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now,
        end_datetime=now + timedelta(hours=4),
        total_budget=Decimal("8000.00"),
        guest_count=500,
    )
    db_session.add(event)
    db_session.flush()

    task = Task(event_id=event.id, name="Hall Setup", status=TaskStatus.READY.value, duration_minutes=60)
    venue = Venue(name="Grand Hall", city="Mumbai", venue_type="INDOOR", status="MAINTENANCE_CLOSED", capacity=300)

    db_session.add_all([task, venue])
    db_session.commit()

    inc_resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "VENUE_ISSUE",
            "title": "Grand Hall Under Maintenance",
            "related_task_id": task.id,
            "related_venue_id": venue.id,
            "evidence_metadata": {"delay_minutes": 30},
        },
        headers={"x-user-id": user.id},
    )

    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    rec_resp = test_client.post(
        f"/api/events/{event.id}/incidents/{incident_id}/recovery/options",
        headers={"x-user-id": user.id},
    )
    assert rec_resp.status_code == 201
    items = rec_resp.json()["items"]
    # Since venue is inactive and capacity (300) < guest_count (500), options MUST be infeasible
    assert all(item["is_feasible"] is False for item in items if "VENUE" in str(item))

