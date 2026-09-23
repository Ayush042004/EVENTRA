"""Integration Test: Newly discovered Google Maps providers become available to Recovery Engine."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.user import User
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.incident import Incident
from app.schemas.vendor import ProviderDiscoveryRequest
from app.services.vendor_service import VendorService
from app.services.recovery_service import RecoveryService


def test_discovered_providers_immediately_available_for_incident_recovery(db_session: Session):
    # 1. Setup Organizer & Event
    owner = User(id="user-org-01", name="Wedding Planner", email="planner@eventra.local")
    db_session.add(owner)
    db_session.flush()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = Event(
        id="event-wedding-delhi",
        owner_id=owner.id,
        name="Grand Summer Wedding",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now,
        end_datetime=now + timedelta(hours=8),
        total_budget=Decimal("50000.00"),
    )
    db_session.add(event)
    db_session.flush()

    # 2. Setup Catering Task and Primary Caterer
    catering_task = Task(
        id="task-dinner-buffet",
        event_id=event.id,
        name="Dinner Buffet Service",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        required_provider_category="CATERING",
        duration_minutes=120,
    )
    primary_caterer = Vendor(
        id="vendor-primary-caterer",
        name="Default Catering Co",
        category="CATERING",
        city="Noida",
        status="ACTIVE",
        base_cost=3000.0,
    )
    db_session.add_all([catering_task, primary_caterer])
    db_session.flush()

    primary_assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=primary_caterer.id,
        category="CATERING",
        agreed_cost=3000.0,
        status="CONFIRMED",
    )
    db_session.add(primary_assignment)
    db_session.flush()

    # 3. Simulate Primary Caterer Incident: VENDOR_NO_SHOW
    incident = Incident(
        id="inc-caterer-noshow",
        event_id=event.id,
        incident_type="VENDOR_NO_SHOW",
        title="Primary Caterer Failed to Arrive",
        related_task_id=catering_task.id,
        related_vendor_id=primary_caterer.id,
        evidence_metadata={"delay_minutes": 60},
        impact_result={
            "directly_affected_tasks": [{"id": catering_task.id}],
            "schedule_impact": {"delay_minutes": 60},
            "affected_objectives": [],
            "affected_constraints": [],
        },
        risk_result={
            "score": 85.0,
            "level": "CRITICAL",
            "primary_risk_factor": "VENDOR_FAILURE",
        },
    )
    db_session.add(incident)
    db_session.commit()

    # 4. Run Google Maps Provider Discovery to discover real-world alternatives
    vendor_service = VendorService(db_session)
    discovery_req = ProviderDiscoveryRequest(
        category="CATERING",
        query="wedding catering buffet",
        location="Noida",
        limit=5,
    )
    discovered_vendors, created, updated, source, _ = vendor_service.discover_providers(
        request=discovery_req,
        event_id=event.id,
    )

    assert len(discovered_vendors) > 0
    discovered_ids = {v.id for v in discovered_vendors}
    # Ensure discovered vendors are distinct from primary caterer
    assert primary_caterer.id not in discovered_ids

    # 5. Run Recovery Engine to generate recovery options for the incident
    recovery_service = RecoveryService(db_session)
    recovery_options = recovery_service.generate_recovery_options(
        event_id=event.id,
        incident_id=incident.id,
        current_user_id=owner.id,
    )

    assert len(recovery_options) > 0

    # 6. Verify that discovered providers are proposed as concrete substitution options
    substitution_provider_ids = set()
    for opt in recovery_options:
        if opt.strategy_type in ("BACKUP", "REASSIGN", "SUBSTITUTE_VENDOR"):
            affected = opt.affected_providers or []
            substitution_provider_ids.update(affected)
            if opt.proposed_changes and "provider_id" in opt.proposed_changes:
                substitution_provider_ids.add(opt.proposed_changes["provider_id"])

    # Discovered providers MUST be in the substitution pool
    matching_discovered_options = substitution_provider_ids.intersection(discovered_ids)
    assert len(matching_discovered_options) > 0, (
        f"Expected discovered providers {discovered_ids} to be included in recovery options pool, "
        f"found substitution options: {substitution_provider_ids}"
    )
