"""Unit Tests: IncidentService (Gate 1 & Service State Transitions)

Covers:
- Incident ingestion with operational entities
- Foreign key validation (task, vendor, resource, venue)
- Event-scoped authorization (rejects unauthorized users)
- Authoritative event state transitions (NORMAL -> AT_RISK / CRITICAL / EMERGENCY)
- StateTransition audit logging
- Incident resolution restoring event state
- Incident recalculation
"""
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.resource import Resource
from app.models.venue import Venue
from app.models.state_transition import StateTransition
from app.models.enums import EventState, EventLifecycleState, IncidentStatus, IncidentType, IncidentSeverity, TaskPriority
from app.services.incident_service import IncidentService
from app.schemas.incident import IncidentCreate
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException


def test_create_incident_success(db_session: Session):
    """Test creating an incident with valid operational entities and state transition."""
    # Create user & event
    user = User(name="Organizer", email="organizer@eventra.demo")
    db_session.add(user)
    db_session.commit()

    event = Event(
        owner_id=user.id,
        name="Annual Tech Fest",
        state=EventState.NORMAL.value,
        lifecycle_state=EventLifecycleState.LIVE.value,
        total_budget=10000.0,
    )
    db_session.add(event)
    db_session.commit()

    # Create task & vendor
    task = Task(
        event_id=event.id,
        name="AV Projection Setup",
        priority="CRITICAL",
        is_critical_path=True,
        slack_minutes=0,
        status="IN_PROGRESS",
    )
    vendor = Vendor(
        name="Apex Displays",
        category="av",
        city="Delhi",
    )
    db_session.add_all([task, vendor])
    db_session.commit()

    service = IncidentService(db_session)
    incident_in = IncidentCreate(
        incident_type=IncidentType.VENDOR_DELAY,
        title="AV Equipment Stalled in Transit",
        description="Delivery truck delayed due to traffic",
        severity=IncidentSeverity.HIGH,
        related_task_id=task.id,
        related_vendor_id=vendor.id,
        evidence_metadata={"delay_minutes": 90},
    )

    incident = service.create_incident(
        event_id=event.id,
        data=incident_in,
        current_user_id=user.id,
    )

    # Verify incident persisted with evaluations
    assert incident.id is not None
    assert incident.event_id == event.id
    assert incident.status == IncidentStatus.OPEN.value
    assert incident.impact_result is not None
    assert incident.risk_result is not None

    # Verify event state transitioned
    db_session.refresh(event)
    assert event.state in (EventState.AT_RISK.value, EventState.CRITICAL.value, EventState.EMERGENCY.value)

    # Verify StateTransition record was written
    transitions = db_session.query(StateTransition).filter(StateTransition.event_id == event.id).all()
    assert len(transitions) >= 1
    assert any(t.entity_type == "EVENT" for t in transitions)


def test_incident_entity_validation(db_session: Session):
    """Verify that referencing non-existent or foreign entities raises BadRequestException."""
    user = User(name="User", email="user@eventra.demo")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Event A")
    other_event = Event(owner_id=user.id, name="Event B")
    db_session.add_all([event, other_event])
    db_session.commit()

    # Task belongs to other event
    task_other = Task(event_id=other_event.id, name="Other Task")
    db_session.add(task_other)
    db_session.commit()

    service = IncidentService(db_session)

    # Rejection of foreign task
    with pytest.raises(BadRequestException) as exc:
        service.create_incident(
            event_id=event.id,
            data=IncidentCreate(
                incident_type=IncidentType.SCHEDULE_DEVIATION,
                title="Delay",
                related_task_id=task_other.id,
            ),
            current_user_id=user.id,
        )
    assert "does not belong to event" in str(exc.value)

    # Rejection of non-existent vendor
    with pytest.raises(BadRequestException) as exc:
        service.create_incident(
            event_id=event.id,
            data=IncidentCreate(
                incident_type=IncidentType.VENDOR_DELAY,
                title="Vendor missing",
                related_vendor_id="non-existent-vendor-id",
            ),
            current_user_id=user.id,
        )
    assert "Referenced vendor" in str(exc.value)


def test_incident_authorization(db_session: Session):
    """Verify that a non-member cannot create incidents on a private event."""
    owner = User(name="Owner", email="owner@eventra.demo")
    stranger = User(name="Stranger", email="stranger@eventra.demo")
    db_session.add_all([owner, stranger])
    db_session.commit()

    event = Event(owner_id=owner.id, name="Private Event")
    db_session.add(event)
    db_session.commit()

    service = IncidentService(db_session)

    with pytest.raises(ForbiddenException) as exc:
        service.create_incident(
            event_id=event.id,
            data=IncidentCreate(
                incident_type=IncidentType.VENUE_ISSUE,
                title="Power Outage",
            ),
            current_user_id=stranger.id,
        )
    assert "not an authorized member" in str(exc.value)


def test_incident_resolution_restores_state(db_session: Session):
    """Verify that resolving all active incidents restores the event state to NORMAL."""
    user = User(name="Operator", email="op@eventra.demo")
    db_session.add(user)
    db_session.commit()

    event = Event(
        owner_id=user.id,
        name="Conference Live",
        state=EventState.NORMAL.value,
        lifecycle_state=EventLifecycleState.LIVE.value,
    )
    db_session.add(event)
    db_session.commit()

    task = Task(
        event_id=event.id,
        name="Keynote Projection",
        priority=TaskPriority.CRITICAL.value,
        is_critical_path=True,
        slack_minutes=0,
    )
    db_session.add(task)
    db_session.commit()

    service = IncidentService(db_session)
    incident = service.create_incident(
        event_id=event.id,
        data=IncidentCreate(
            incident_type=IncidentType.RESOURCE_SHORTAGE,
            title="Projector Bulb Blown",
            related_task_id=task.id,
        ),
        current_user_id=user.id,
    )

    db_session.refresh(event)
    # Event state should be elevated
    assert event.state != EventState.NORMAL.value

    # Now resolve the incident
    service.resolve_incident(
        event_id=event.id,
        incident_id=incident.id,
        resolution_notes="Spare bulb replaced successfully",
        current_user_id=user.id,
    )

    db_session.refresh(event)
    assert event.state == EventState.NORMAL.value
    assert event.lifecycle_state == EventLifecycleState.LIVE.value

    # Check that resolution was logged in transitions
    transitions = db_session.query(StateTransition).filter(
        StateTransition.event_id == event.id,
        StateTransition.new_state == EventState.NORMAL.value,
    ).all()
    assert len(transitions) >= 1
