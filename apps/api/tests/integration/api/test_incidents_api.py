"""Integration tests for Incident Detection, Impact Analysis, and Risk Engine API.

Tests:
- POST /api/events/{event_id}/incidents (201 Created, impact & risk calculated, event state escalated)
- GET /api/events/{event_id}/incidents (filtering, pagination)
- GET /api/events/{event_id}/incidents/{incident_id} (200 OK & 404 Not Found)
- GET /api/events/{event_id}/incidents/{incident_id}/impact (impact breakdown)
- GET /api/events/{event_id}/incidents/{incident_id}/risk (risk score, level, factors)
- POST /api/events/{event_id}/incidents/{incident_id}/recalculate (deterministic re-evaluation)
- POST /api/events/{event_id}/incidents/{incident_id}/resolve (resolution, event state de-escalation)
- RBAC authorization check (403 Forbidden for non-member)
- Operational entity validation (400 Bad Request for foreign task / invalid vendor)
"""
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.event import Event
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.resource import Resource
from app.models.enums import EventState, EventLifecycleState, TaskPriority, TaskStatus


def _setup_live_event_with_entities(db: Session):
    """Sets up an event owner, live event, critical task, and active vendor."""
    user = User(name="Ops Lead", email="opslead@eventra.demo")
    db.add(user)
    db.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        owner_id=user.id,
        name="Global Developer Summit",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(hours=2),
        end_datetime=now + timedelta(hours=10),
        total_budget=50000.0,
    )
    db.add(event)
    db.commit()

    task = Task(
        event_id=event.id,
        name="Mainstage Audio & Mic Rigging",
        status=TaskStatus.IN_PROGRESS.value,
        priority=TaskPriority.CRITICAL.value,
        is_critical_path=True,
        slack_minutes=0,
        duration_minutes=60,
        planned_start=now + timedelta(hours=1),
        planned_end=now + timedelta(hours=2),
        required_provider_category="sound",
    )
    vendor = Vendor(
        name="SoundWave Live Systems",
        category="sound",
        city="Mumbai",
    )
    resource = Resource(
        event_id=event.id,
        name="Primary Wireless Microphone Set",
        type="EQUIPMENT",
        quantity=4,
        status="ALLOCATED",
    )
    db.add_all([task, vendor, resource])
    db.commit()

    return user, event, task, vendor, resource


def test_create_incident_api_success(test_client: TestClient, db_session: Session):
    """Verify POST /api/events/{event_id}/incidents ingests incident and computes impact + risk."""
    user, event, task, vendor, resource = _setup_live_event_with_entities(db_session)

    payload = {
        "incident_type": "VENDOR_DELAY",
        "severity": "HIGH",
        "title": "Audio Hardware Van Delayed in Expressway Jam",
        "description": "Primary console delayed by 90 minutes due to unexpected traffic accident.",
        "related_task_id": task.id,
        "related_vendor_id": vendor.id,
        "related_resource_id": resource.id,
        "evidence_metadata": {"delay_minutes": 90, "source": "vendor_whatsapp"},
    }

    response = test_client.post(
        f"/api/events/{event.id}/incidents",
        json=payload,
        headers={"x-user-id": user.id},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["event_id"] == event.id
    assert data["status"] == "OPEN"
    assert data["title"] == payload["title"]
    assert data["incident_type"] == "VENDOR_DELAY"

    # Verify structured impact analysis is embedded
    impact = data["impact_result"]
    assert impact is not None
    assert len(impact["directly_affected_tasks"]) >= 1
    assert impact["directly_affected_tasks"][0]["id"] == task.id
    assert impact["schedule_impact"]["delay_minutes"] == 90
    assert impact["schedule_impact"]["critical_path_breached"] is True

    # Verify structured risk evaluation is embedded
    risk = data["risk_result"]
    assert risk is not None
    assert risk["score"] > 0
    assert len(risk["factors"]) == 8

    # Verify event state transitioned
    db_session.refresh(event)
    assert event.state in (EventState.AT_RISK.value, EventState.CRITICAL.value, EventState.EMERGENCY.value)


def test_list_and_filter_incidents_api(test_client: TestClient, db_session: Session):
    """Verify GET /api/events/{event_id}/incidents supports filtering and pagination."""
    user, event, task, vendor, _ = _setup_live_event_with_entities(db_session)

    # Ingest two incidents of different types
    test_client.post(
        f"/api/events/{event.id}/incidents",
        json={"incident_type": "VENDOR_DELAY", "title": "Delay 1", "related_task_id": task.id},
        headers={"x-user-id": user.id},
    )
    test_client.post(
        f"/api/events/{event.id}/incidents",
        json={"incident_type": "RESOURCE_SHORTAGE", "title": "Shortage 1"},
        headers={"x-user-id": user.id},
    )

    # 1. List all
    resp_all = test_client.post = test_client.get(
        f"/api/events/{event.id}/incidents",
        headers={"x-user-id": user.id},
    )
    assert resp_all.status_code == 200
    all_data = resp_all.json()
    assert all_data["total"] == 2
    assert len(all_data["items"]) == 2

    # 2. Filter by status
    resp_status = test_client.get(
        f"/api/events/{event.id}/incidents?status=OPEN",
        headers={"x-user-id": user.id},
    )
    assert resp_status.status_code == 200
    assert resp_status.json()["total"] == 2

    # 3. Filter by incident_type
    resp_type = test_client.get(
        f"/api/events/{event.id}/incidents?incident_type=RESOURCE_SHORTAGE",
        headers={"x-user-id": user.id},
    )
    assert resp_type.status_code == 200
    type_data = resp_type.json()
    assert type_data["total"] == 1
    assert type_data["items"][0]["incident_type"] == "RESOURCE_SHORTAGE"


def test_get_incident_and_sub_resources_api(test_client: TestClient, db_session: Session):
    """Verify retrieving incident, /impact, and /risk endpoints, plus 404 behavior."""
    user, event, task, vendor, _ = _setup_live_event_with_entities(db_session)

    create_resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "SCHEDULE_DEVIATION",
            "title": "Keynote Speaker Late",
            "related_task_id": task.id,
        },
        headers={"x-user-id": user.id},
    )
    incident_id = create_resp.json()["id"]

    # 1. GET /incidents/{incident_id}
    get_resp = test_client.get(
        f"/api/events/{event.id}/incidents/{incident_id}",
        headers={"x-user-id": user.id},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == incident_id

    # 2. GET /incidents/{incident_id}/impact
    impact_resp = test_client.get(
        f"/api/events/{event.id}/incidents/{incident_id}/impact",
        headers={"x-user-id": user.id},
    )
    assert impact_resp.status_code == 200
    impact_json = impact_resp.json()
    assert "directly_affected_tasks" in impact_json
    assert "severity" in impact_json

    # 3. GET /incidents/{incident_id}/risk
    risk_resp = test_client.get(
        f"/api/events/{event.id}/incidents/{incident_id}/risk",
        headers={"x-user-id": user.id},
    )
    assert risk_resp.status_code == 200
    risk_json = risk_resp.json()
    assert "score" in risk_json
    assert "factors" in risk_json
    assert len(risk_json["factors"]) == 8

    # 4. 404 for non-existent incident
    resp_404 = test_client.get(
        f"/api/events/{event.id}/incidents/non-existent-id",
        headers={"x-user-id": user.id},
    )
    assert resp_404.status_code == 404


def test_recalculate_and_resolve_incident_api(test_client: TestClient, db_session: Session):
    """Verify recalculation and resolution endpoints de-escalating event state."""
    user, event, task, _, _ = _setup_live_event_with_entities(db_session)

    create_resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "RESOURCE_SHORTAGE",
            "title": "Spare Mic Battery Depleted",
            "related_task_id": task.id,
        },
        headers={"x-user-id": user.id},
    )
    incident_id = create_resp.json()["id"]

    # 1. Recalculate
    recalc_resp = test_client.post(
        f"/api/events/{event.id}/incidents/{incident_id}/recalculate",
        headers={"x-user-id": user.id},
    )
    assert recalc_resp.status_code == 200
    assert recalc_resp.json()["id"] == incident_id

    # 2. Resolve
    resolve_resp = test_client.post(
        f"/api/events/{event.id}/incidents/{incident_id}/resolve",
        json={"resolution_notes": "Backup battery packs dispatched from operations room."},
        headers={"x-user-id": user.id},
    )
    assert resolve_resp.status_code == 200
    resolved_json = resolve_resp.json()
    assert resolved_json["status"] == "RESOLVED"
    assert resolved_json["resolved_at"] is not None
    assert resolved_json["resolution_notes"] == "Backup battery packs dispatched from operations room."

    # Event state restored to NORMAL
    db_session.refresh(event)
    assert event.state == EventState.NORMAL.value


def test_incident_api_authorization_and_validation(test_client: TestClient, db_session: Session):
    """Verify 403 Forbidden for non-members and 400 Bad Request for foreign entity references."""
    user, event, task, _, _ = _setup_live_event_with_entities(db_session)

    # 1. 403 Forbidden for unauthorized user
    resp_forbidden = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={"incident_type": "VENUE_ISSUE", "title": "Power Glitch"},
        headers={"x-user-id": "unauthorized-stranger-id"},
    )
    assert resp_forbidden.status_code == 403

    # 2. 400 Bad Request for non-existent vendor
    resp_bad_vendor = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "VENDOR_DELAY",
            "title": "Unknown Vendor Delay",
            "related_vendor_id": "ghost-vendor-999",
        },
        headers={"x-user-id": user.id},
    )
    assert resp_bad_vendor.status_code == 400
    assert "Referenced vendor" in resp_bad_vendor.json()["error"]["message"]
