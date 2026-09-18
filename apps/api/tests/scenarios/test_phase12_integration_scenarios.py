"""Phase 12 Comprehensive Integration Scenario Tests.

End-to-End Operational Loop with Real-World Integrations:
1. Live Event with critical catering task & venue
2. Vendor No-Show Incident occurs
3. Integration (Notifications): Alert operations team of incident
4. Integration (Maps): Compute transit distance & ETA for backup vendor to venue
5. Recovery Engine: Evaluates replacement option
6. Governance: Approval required
7. Integration (Notifications): Alert human organizer that approval is required
8. Human Organizer approves ticket
9. Action Execution: Vendor assignment mutated to backup vendor
10. Integration (Provider Communication / WhatsApp): Send dispatch instruction to backup vendor
11. Integration (Provider Communication): Receive inbound confirmation from backup vendor
12. Phase 10 Verification: Confirm operational state restored
13. Audit Verification: Confirm complete audit trail with zero secret leakage
14. Invariant Check: Confirm integrations never modified authoritative state directly
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.user import User
from app.models.event_member import EventMember
from app.models.task import Task
from app.models.venue import Venue
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.budget import BudgetItem
from app.models.objective import Objective
from app.models.incident import Incident
from app.models.approval import Approval
from app.models.action import ActionExecution
from app.models.verification import VerificationResult
from app.models.notification import Notification
from app.models.audit import AuditRecord
from app.models.enums import (
    EventLifecycleState,
    EventState,
    RoleType,
    TaskPriority,
    TaskStatus,
    IncidentType,
    IncidentSeverity,
)
from app.integrations.registry import registry
from app.integrations.base import IntegrationSource
from app.services.notification_service import NotificationService
from app.services.provider_communication_service import ProviderCommunicationService
from app.services.action_service import ActionService
from app.services.verification_service import VerificationService
from app.engines.auth.snapshot import compute_event_state_snapshot
from app.core.config import settings


def _setup_live_event_with_integrations(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # 1. Users
    organizer = User(name="Elena Ops Lead", email="elena.ops@eventra.test")
    collaborator = User(name="Alex Floor Manager", email="alex.floor@eventra.test")
    db.add_all([organizer, collaborator])
    db.flush()

    # 2. Event (LIVE, NORMAL)
    event = Event(
        owner_id=organizer.id,
        name="Global Tech Summit Live 2026",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(hours=1),
        end_datetime=now + timedelta(hours=10),
        total_budget=Decimal("75000.00"),
    )
    db.add(event)
    db.flush()

    # 3. Memberships
    mem_org = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    mem_col = EventMember(event_id=event.id, user_id=collaborator.id, role=RoleType.COLLABORATOR.value)
    db.add_all([mem_org, mem_col])

    # 4. Venue
    venue = Venue(
        name="Chicago Grand Pavilion",
        address="200 E Randolph St, Chicago, IL",
        city="Chicago",
        venue_type="CONVENTION_CENTER",
        capacity=1200,
        hourly_rate=250.0,
    )
    db.add(venue)
    db.flush()
    event.venue_id = venue.id

    # 5. Critical Task
    lunch_task = Task(
        event_id=event.id,
        name="Keynote VIP Luncheon",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=90,
        is_critical_path=True,
        slack_minutes=15,
        required_provider_category="catering",
        planned_start=now + timedelta(hours=2),
        planned_end=now + timedelta(hours=3, minutes=30),
    )
    db.add(lunch_task)
    db.flush()

    # 6. Primary and Backup Vendors
    primary_vendor = Vendor(
        name="Original Catering Corp",
        category="catering",
        city="Chicago",
        base_cost=4000.0,
        status="ACTIVE",
    )
    backup_vendor = Vendor(
        name="Rapid Gourmet Backup",
        category="catering",
        city="Chicago",
        base_cost=4500.0,
        status="ACTIVE",
    )
    db.add_all([primary_vendor, backup_vendor])
    db.flush()

    assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=primary_vendor.id,
        category="catering",
        status="CONFIRMED",
        agreed_cost=4000.0,
    )
    db.add(assignment)

    # 7. Budget Item & Objective
    budget = BudgetItem(
        event_id=event.id,
        name="Catering & Hospitality",
        category="catering",
        estimated_amount=Decimal("6000.00"),
        actual_amount=Decimal("4000.00"),
    )
    objective = Objective(
        event_id=event.id,
        name="Executive Luncheon Delivery",
        priority="CRITICAL",
    )
    db.add_all([budget, objective])
    db.commit()

    return {
        "organizer": organizer,
        "collaborator": collaborator,
        "event": event,
        "venue": venue,
        "task": lunch_task,
        "primary_vendor": primary_vendor,
        "backup_vendor": backup_vendor,
        "assignment": assignment,
        "budget": budget,
        "objective": objective,
    }


def test_end_to_end_operational_loop_with_integrations(db_session: Session):
    """Verifies the complete integration scenario:
    Incident -> Maps transit calculation -> Approval Notification -> Human sign-off ->
    Action Execution -> Provider communication dispatch & reply -> Verification -> Audit checks.
    """
    ctx = _setup_live_event_with_integrations(db_session)
    event = ctx["event"]
    venue = ctx["venue"]
    backup_vendor = ctx["backup_vendor"]
    organizer = ctx["organizer"]

    notif_service = NotificationService(db_session)
    comm_service = ProviderCommunicationService(db_session)

    # -----------------------------------------------------------------------
    # Step 1: Incident Occurs & Notification Sent
    # -----------------------------------------------------------------------
    incident = Incident(
        event_id=event.id,
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        title="Primary Caterer No-Show",
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_vendor_id=ctx["primary_vendor"].id,
        related_task_id=ctx["task"].id,
        evidence_metadata={"category": "catering"},
    )
    db_session.add(incident)
    db_session.commit()

    # Alert operations team of incident
    incident_notif_res = notif_service.notify_incident(
        event_id=event.id,
        incident={
            "id": incident.id,
            "title": incident.title,
            "severity": incident.severity,
            "type": incident.incident_type,
        },
    )
    assert incident_notif_res.success is True
    assert incident_notif_res.data["id"] is not None

    # INVARIANT CHECK: Notification did NOT alter event state
    db_session.refresh(event)
    assert event.state == EventState.NORMAL.value
    assert event.total_budget == Decimal("75000.00")

    # -----------------------------------------------------------------------
    # Step 2: Maps Integration — Compute Transit Distance and ETA
    # -----------------------------------------------------------------------
    maps = registry.get_maps_provider()
    backup_vendor_address = "100 S Wacker Dr, Chicago, IL"
    venue_address = venue.address

    transit_res = maps.get_distance(origin=backup_vendor_address, destination=venue_address)
    assert transit_res.success is True
    assert transit_res.source == IntegrationSource.MOCK
    assert transit_res.data["distance_km"] > 0
    assert transit_res.data["duration_minutes"] > 0

    route_res = maps.get_route(origin=backup_vendor_address, destination=venue_address)
    assert route_res.success is True
    assert "route_summary" in route_res.data

    # -----------------------------------------------------------------------
    # Step 3: Governance — Approval Required & Dispatched via Notification
    # -----------------------------------------------------------------------
    snapshot = compute_event_state_snapshot(db_session, event.id)
    approval = Approval(
        event_id=event.id,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        impact_level="HIGH",
        requested_action={
            "task_id": ctx["task"].id,
            "old_vendor_id": ctx["primary_vendor"].id,
            "new_vendor_id": backup_vendor.id,
            "agreed_cost": 4500.0,
            "transit_minutes": transit_res.data["duration_minutes"],
        },
        state_snapshot=snapshot,
        status="PENDING",
        requester_id=ctx["collaborator"].id,
    )
    db_session.add(approval)
    db_session.commit()

    # Dispatch approval notification
    appr_notif_res = notif_service.notify_approval_requested(
        event_id=event.id,
        approval={
            "id": approval.id,
            "action_type": approval.action_type,
            "cost": 4500.0,
            "eta_minutes": transit_res.data["duration_minutes"],
        },
    )
    assert appr_notif_res.success is True

    # -----------------------------------------------------------------------
    # Step 4: Human Signs Off & Action Execution
    # -----------------------------------------------------------------------
    approval.status = "APPROVED"
    approval.approver_id = organizer.id
    approval.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.commit()

    action_service = ActionService(db_session)
    exec_result = action_service.execute_action(
        event_id=event.id,
        executor_id=organizer.id,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        payload={
            "task_id": ctx["task"].id,
            "new_vendor_id": backup_vendor.id,
            "agreed_cost": 4500.0,
        },
        approval_request_id=approval.id,
    )
    assert exec_result.status == "SUCCESS"

    # Notify action execution
    notif_service.notify_action_executed(
        event_id=event.id,
        action={"id": exec_result.id, "action_type": approval.action_type},
    )

    # -----------------------------------------------------------------------
    # Step 5: Provider Communication — Dispatch & Inbound Webhook Reply
    # -----------------------------------------------------------------------
    # Outbound dispatch message to backup vendor
    outbound_res = comm_service.send_message(
        event_id=event.id,
        provider_id=backup_vendor.id,
        recipient_contact="+13125550199",
        message=f"Urgent dispatch: Keynote luncheon backup catering confirmed for {venue.name}. ETA ~{transit_res.data['duration_minutes']} min.",
        actor_id=organizer.id,
        actor_type="USER",
    )
    assert outbound_res.success is True
    assert outbound_res.data["status"] == "SENT"

    # Inbound reply from backup vendor
    comm_provider = registry.get_communication_provider()
    inbound_res = comm_provider.receive_inbound({
        "event_id": event.id,
        "provider_id": backup_vendor.id,
        "text": "Confirmed: Team is departing immediately, ETA 25 minutes.",
        "id": "reply-vendor-001",
    })
    assert inbound_res.success is True

    # Verify conversation thread has 2 messages
    thread = comm_service.get_messages(event_id=event.id, provider_id=backup_vendor.id)
    assert len(thread) == 2
    assert thread[0]["direction"] == "OUTBOUND"
    assert thread[1]["direction"] == "INBOUND"

    # -----------------------------------------------------------------------
    # Step 6: Phase 10 Verification
    # -----------------------------------------------------------------------
    verif_service = VerificationService(db_session)
    verif_res = verif_service.verify_action(
        event_id=event.id,
        action_execution_id=exec_result.id,
        current_user_id=organizer.id,
    )
    assert verif_res.status in ("VERIFIED", "PARTIALLY_VERIFIED")

    # Notify verification completed
    notif_service.notify_verification_completed(
        event_id=event.id,
        verification={"id": verif_res.id, "status": verif_res.status},
    )

    # -----------------------------------------------------------------------
    # Step 7: Audit Trail & Zero-Secrets Invariant Assertions
    # -----------------------------------------------------------------------
    audits = db_session.query(AuditRecord).filter_by(event_id=event.id).all()
    assert len(audits) >= 3

    actions_recorded = {a.action for a in audits}
    assert "NOTIFICATION_SENT" in actions_recorded
    assert "PROVIDER_MESSAGE_SENT" in actions_recorded
    assert "VERIFY_ACTION" in actions_recorded

    # Check for secret leakage across all audit entries
    for audit in audits:
        raw_text = f"{audit.before_state} {audit.after_state} {audit.action}"
        if settings.MAPS_API_KEY:
            assert settings.MAPS_API_KEY not in raw_text
        if settings.WHATSAPP_API_TOKEN:
            assert settings.WHATSAPP_API_TOKEN not in raw_text
        if settings.LLM_API_KEY:
            assert settings.LLM_API_KEY not in raw_text

    # Verify persisted notifications
    persisted_notifs = notif_service.list_notifications(event_id=event.id)
    assert len(persisted_notifs) >= 3
    notif_types = {n["notification_type"] for n in persisted_notifs}
    assert "INCIDENT_DETECTED" in notif_types
    assert "APPROVAL_REQUESTED" in notif_types
    assert "ACTION_EXECUTED" in notif_types
