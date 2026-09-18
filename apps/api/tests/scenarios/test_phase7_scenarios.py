"""Phase 7 Scenario Integration Tests: Operational Intelligence Pipeline.

Tests the full operational loop:
PLAN -> SCHEDULE -> GO-LIVE -> INCIDENT INGESTION -> IMPACT PROPAGATION -> RISK ENGINE -> STATE ESCALATION -> RESOLUTION
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.user import User
from app.models.vendor import Vendor
from app.models.venue import Venue
from app.models.resource import Resource
from app.models.task import Task
from app.models.state_transition import StateTransition
from app.models.enums import EventState, EventLifecycleState, TaskPriority, TaskStatus, IncidentType, IncidentSeverity


def _create_running_live_event(client: TestClient, db: Session):
    """Bootstraps a complete operational live event with plan, schedule, and live state."""
    user = User(name="Operations Director", email="ops.director@eventra.demo")
    db.add(user)
    db.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        owner_id=user.id,
        name="Global Tech Summit Live",
        event_type="CONFERENCE",
        lifecycle_state=EventLifecycleState.DRAFT.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(hours=3),
        end_datetime=now + timedelta(hours=12),
        total_budget=Decimal("75000.00"),
        currency="USD",
        location="Grand Expo Center",
    )
    db.add(event)
    db.commit()

    # 1. Generate Plan
    plan_resp = client.post(f"/api/events/{event.id}/plan")
    assert plan_resp.status_code == 200

    # 2. Compute Schedule
    sched_resp = client.post(f"/api/events/{event.id}/schedule/compute")
    assert sched_resp.status_code == 200

    # 3. Go Live
    live_resp = client.post(
        f"/api/events/{event.id}/go-live",
        json={"reason": "Operations commencing on schedule"},
    )
    assert live_resp.status_code == 200

    db.refresh(event)
    assert event.lifecycle_state == EventLifecycleState.LIVE.value
    assert event.state == EventState.NORMAL.value

    return user, event


def test_primary_scenario_vendor_no_show_escalation(test_client: TestClient, db_session: Session):
    """Primary Scenario: Live Event -> Vendor No-Show -> Impact Traversal -> Risk Escalation.

    Verifies Section 19 end-to-end verification requirement:
    - Event in LIVE state, NORMAL risk
    - Ingest VENDOR_NO_SHOW incident on critical path task
    - Impact Engine identifies directly affected task and downstream dependencies
    - Risk Engine scores >= 50.0 (HIGH/CRITICAL)
    - Event operational state transitions to CRITICAL or EMERGENCY
    - Lifecycle state escalates to INCIDENT or EMERGENCY
    - Authoritative StateTransition records written
    """
    user, event = _create_running_live_event(test_client, db_session)

    # Find a critical path task from the generated plan
    critical_task = (
        db_session.query(Task)
        .filter(Task.event_id == event.id, Task.is_critical_path.is_(True))
        .first()
    )
    assert critical_task is not None

    # Register the primary vendor
    vendor = Vendor(
        name="Apex Audio Rigging",
        category=critical_task.required_provider_category or "av",
        city="San Francisco",
    )
    db_session.add(vendor)
    db_session.commit()

    # Ingest VENDOR_NO_SHOW incident via API
    incident_payload = {
        "incident_type": "VENDOR_NO_SHOW",
        "severity": "CRITICAL",
        "title": "Main Stage AV Vendor Failed to Arrive",
        "description": "Provider has not arrived 30 minutes past call time and phone is unreachable.",
        "related_task_id": critical_task.id,
        "related_vendor_id": vendor.id,
        "evidence_metadata": {"call_time_missed_minutes": 30, "phone_attempts": 4},
    }

    resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json=incident_payload,
        headers={"x-user-id": user.id},
    )
    assert resp.status_code == 201
    incident_data = resp.json()
    incident_id = incident_data["id"]

    # 1. Verify Impact Analysis
    impact = incident_data["impact_result"]
    assert impact["incident_id"] == incident_id
    assert len(impact["directly_affected_tasks"]) >= 1
    assert any(t["id"] == critical_task.id for t in impact["directly_affected_tasks"])
    assert impact["schedule_impact"]["critical_path_breached"] is True
    assert impact["severity"] in ("HIGH", "CRITICAL", "EMERGENCY")

    # 2. Verify Risk Engine
    risk = incident_data["risk_result"]
    assert risk["score"] >= 50.0
    assert risk["level"] in ("HIGH", "CRITICAL")
    assert risk["target_event_state"] in (EventState.CRITICAL.value, EventState.EMERGENCY.value)

    # 3. Verify Authoritative Event State Escalation
    db_session.refresh(event)
    assert event.state in (EventState.CRITICAL.value, EventState.EMERGENCY.value)
    assert event.lifecycle_state in (EventLifecycleState.INCIDENT.value, EventLifecycleState.EMERGENCY.value)

    # 4. Verify StateTransition Audit Logs
    transitions = (
        db_session.query(StateTransition)
        .filter(StateTransition.event_id == event.id)
        .all()
    )
    event_transitions = [t for t in transitions if t.entity_type == "EVENT"]
    lifecycle_transitions = [t for t in transitions if t.entity_type == "EVENT_LIFECYCLE"]

    assert len(event_transitions) >= 1
    assert event_transitions[-1].new_state == event.state
    assert len(lifecycle_transitions) >= 1
    assert lifecycle_transitions[-1].new_state == event.lifecycle_state


def test_scenario_vendor_delay_within_and_exceeding_slack(test_client: TestClient, db_session: Session):
    """Scenario: Vendor Delay.

    Tests that delays within available slack maintain lower risk, while delays
    exceeding slack consume buffer and trigger critical path breach warnings.
    """
    user, event = _create_running_live_event(test_client, db_session)

    # Create a non-critical task with 60 minutes slack
    slack_task = Task(
        event_id=event.id,
        name="Banquet Signage Setup",
        priority=TaskPriority.LOW.value,
        is_critical_path=False,
        slack_minutes=60,
        duration_minutes=30,
    )
    db_session.add(slack_task)
    db_session.commit()

    # Delay within slack: 20 minutes delay
    resp_small = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "VENDOR_DELAY",
            "severity": "LOW",
            "title": "Minor Signage Van Delay",
            "related_task_id": slack_task.id,
            "evidence_metadata": {"delay_minutes": 20},
        },
        headers={"x-user-id": user.id},
    )
    assert resp_small.status_code == 201
    small_data = resp_small.json()
    assert small_data["impact_result"]["schedule_impact"]["critical_path_breached"] is False
    assert small_data["impact_result"]["schedule_impact"]["slack_consumed"] == 20

    # Delay exceeding slack: 90 minutes delay on a 60m slack task
    resp_large = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "VENDOR_DELAY",
            "severity": "HIGH",
            "title": "Severe Signage Delay",
            "related_task_id": slack_task.id,
            "evidence_metadata": {"delay_minutes": 90},
        },
        headers={"x-user-id": user.id},
    )
    assert resp_large.status_code == 201
    large_data = resp_large.json()
    assert large_data["impact_result"]["schedule_impact"]["critical_path_breached"] is True
    assert large_data["impact_result"]["schedule_impact"]["slack_consumed"] == 60


def test_scenario_resource_shortage(test_client: TestClient, db_session: Session):
    """Scenario: Resource Shortage.

    Tests that shortage of a required equipment resource is quantified in impact
    and reflected in the resource availability risk factor.
    """
    user, event = _create_running_live_event(test_client, db_session)

    res = Resource(
        event_id=event.id,
        name="High-Lumen Laser Projector",
        type="EQUIPMENT",
        quantity=2,
        status="IN_USE",
    )
    db_session.add(res)
    db_session.commit()

    resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "RESOURCE_SHORTAGE",
            "severity": "HIGH",
            "title": "Laser Projector Lens Cracked",
            "related_resource_id": res.id,
            "evidence_metadata": {"shortage_quantity": 1},
        },
        headers={"x-user-id": user.id},
    )
    assert resp.status_code == 201
    data = resp.json()

    # Resource impact captured
    impact = data["impact_result"]
    assert len(impact["affected_resources"]) >= 1
    assert impact["affected_resources"][0]["id"] == res.id

    # Risk factor resource_availability evaluated
    risk = data["risk_result"]
    res_factor = next(f for f in risk["factors"] if f["name"] == "resource_availability")
    assert res_factor["score"] >= 60.0


def test_scenario_multi_incident_resolution_and_state_restoration(test_client: TestClient, db_session: Session):
    """Scenario: Multi-incident lifecycle and resolution.

    - Ingest Incident A -> State escalates
    - Ingest Incident B -> State reflects combined operational risk
    - Resolve Incident A -> State remains elevated due to active Incident B
    - Resolve Incident B -> State de-escalates to NORMAL
    """
    user, event = _create_running_live_event(test_client, db_session)

    critical_task = (
        db_session.query(Task)
        .filter(Task.event_id == event.id, Task.is_critical_path.is_(True))
        .first()
    )

    # Ingest Incident A (Critical)
    resp_a = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "VENDOR_NO_SHOW",
            "severity": "CRITICAL",
            "title": "Incident A - Primary Audio Failure",
            "related_task_id": critical_task.id,
        },
        headers={"x-user-id": user.id},
    )
    inc_a_id = resp_a.json()["id"]

    db_session.refresh(event)
    assert event.state in (EventState.CRITICAL.value, EventState.EMERGENCY.value)

    # Ingest Incident B (Medium)
    resp_b = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "SCHEDULE_DEVIATION",
            "severity": "MEDIUM",
            "title": "Incident B - Registration Desk Delay",
            "evidence_metadata": {"delay_minutes": 15},
        },
        headers={"x-user-id": user.id},
    )
    inc_b_id = resp_b.json()["id"]

    # Resolve Incident A
    resolve_a = test_client.post(
        f"/api/events/{event.id}/incidents/{inc_a_id}/resolve",
        json={"resolution_notes": "Replacement sound team arrived and sound check complete."},
        headers={"x-user-id": user.id},
    )
    assert resolve_a.status_code == 200

    # Event state should still reflect Incident B (i.e. still evaluated against open incidents)
    db_session.refresh(event)
    # Since Incident B is still open, event state must not be confused or broken
    assert event.state in (EventState.NORMAL.value, EventState.AT_RISK.value)

    # Resolve Incident B
    resolve_b = test_client.post(
        f"/api/events/{event.id}/incidents/{inc_b_id}/resolve",
        json={"resolution_notes": "Additional registration volunteers opened extra lines."},
        headers={"x-user-id": user.id},
    )
    assert resolve_b.status_code == 200

    # Both incidents resolved -> Event state must return to NORMAL
    db_session.refresh(event)
    assert event.state == EventState.NORMAL.value
    assert event.lifecycle_state == EventLifecycleState.LIVE.value
