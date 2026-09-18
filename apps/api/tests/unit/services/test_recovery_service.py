"""Unit tests for RecoveryService orchestration, stale option detection, and authorization."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.enums import EventLifecycleState, EventState, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.incident import Incident
from app.models.task import Task
from app.models.user import User
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.recovery import Recovery
from app.services.recovery_service import RecoveryService


def _create_test_event_with_incident(db: Session, owner_id: str):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        owner_id=owner_id,
        name="Music Festival",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now,
        end_datetime=now + timedelta(hours=10),
        total_budget=Decimal("10000.00"),
    )
    db.add(event)
    db.flush()

    t1 = Task(
        event_id=event.id,
        name="Stage Setup",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        required_provider_category="staging",
        duration_minutes=60,
    )
    v1 = Vendor(name="Stage Corp", category="staging", city="Mumbai", status="ACTIVE", base_cost=1000.0)
    v2 = Vendor(name="Backup Stage Co", category="staging", city="Mumbai", status="ACTIVE", base_cost=1200.0)

    db.add_all([t1, v1, v2])
    db.flush()

    assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=v1.id,
        category="staging",
        agreed_cost=1000.0,
        status="CONFIRMED",
    )

    db.add(assignment)
    db.flush()

    incident = Incident(
        event_id=event.id,
        incident_type="VENDOR_NO_SHOW",
        title="Stage Corp No-Show",
        related_task_id=t1.id,
        related_vendor_id=v1.id,
        evidence_metadata={"delay_minutes": 60, "provider_eta_minutes": {v2.id: 20}},
        impact_result={
            "directly_affected_tasks": [{"id": t1.id}],
            "schedule_impact": {"delay_minutes": 60},
            "affected_objectives": [],
            "affected_constraints": [],
        },
        risk_result={
            "score": 80.0,
            "level": "HIGH",
            "primary_risk_factor": "VENDOR_FAILURE",
        },
    )
    db.add(incident)
    db.commit()
    return event, incident, t1, v1, v2


def test_generate_recovery_options_creates_persisted_records(db_session: Session):
    owner = User(name="Fest Owner", email="owner@fest.test")
    db_session.add(owner)
    db_session.flush()

    event, incident, t1, v1, v2 = _create_test_event_with_incident(db_session, owner.id)
    service = RecoveryService(db_session)

    options = service.generate_recovery_options(event.id, incident.id, owner.id)
    assert len(options) > 0
    assert all(isinstance(opt, Recovery) for opt in options)

    # Verify options are persisted in DB
    db_records = db_session.query(Recovery).filter(Recovery.incident_id == incident.id).all()
    assert len(db_records) == len(options)

    # Verify authoritative event state was NOT mutated
    db_session.refresh(event)
    db_session.refresh(t1)
    db_session.refresh(v1)
    assert event.state == EventState.NORMAL.value
    assert t1.status == TaskStatus.READY.value
    assert v1.status == "ACTIVE"


def test_stale_option_detection_and_recalculation(db_session: Session):
    owner = User(name="Fest Owner 2", email="owner2@fest.test")
    db_session.add(owner)
    db_session.flush()

    event, incident, t1, _, _ = _create_test_event_with_incident(db_session, owner.id)
    service = RecoveryService(db_session)

    options = service.generate_recovery_options(event.id, incident.id, owner.id)
    assert options
    first_snapshot = options[0].state_snapshot

    # Modify live task state
    t1.status = TaskStatus.IN_PROGRESS.value
    db_session.commit()

    # Listing options should flag them as stale because snapshot changed
    listed = service.list_recovery_options(event.id, incident.id, owner.id)
    assert all(opt._is_stale for opt in listed)

    # Recalculate options
    recalculated = service.recalculate_options(event.id, incident.id, owner.id)
    assert recalculated

    fresh_options = service.list_recovery_options(event.id, incident.id, owner.id)
    active_options = [opt for opt in fresh_options if opt.status != "STALE"]
    assert active_options
    assert all(not opt._is_stale for opt in active_options)



def test_authorization_prevents_unauthorized_access(db_session: Session):
    owner = User(name="Owner User", email="owner3@fest.test")
    stranger = User(name="Stranger User", email="stranger@fest.test")
    db_session.add_all([owner, stranger])
    db_session.flush()

    event, incident, _, _, _ = _create_test_event_with_incident(db_session, owner.id)
    service = RecoveryService(db_session)

    with pytest.raises(ForbiddenException):
        service.generate_recovery_options(event.id, incident.id, stranger.id)

    with pytest.raises(ForbiddenException):
        service.list_recovery_options(event.id, incident.id, stranger.id)
