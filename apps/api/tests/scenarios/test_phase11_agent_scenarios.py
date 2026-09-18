"""Phase 11 Comprehensive Scenario Tests:
Mandatory End-to-End Operational Loop & REST API Integration.

Scenario:
EVENT (PLANNED -> LIVE)
  ↓
CATERING PROVIDER NO-SHOW (INCIDENT)
  ↓
AGENT OBSERVES LIVE EVENT STATE
  ↓
AGENT INTERPRETS SITUATION & INVESTIGATES IMPACT/RISK
  ↓
PHASE 8 DETERMINISTIC RECOVERY ENGINE GENERATES CANDIDATES
  ↓
AGENT SELECTS VALIDATED OPTION
  ↓
PHASE 9 AUTHORIZATION DETECTS APPROVAL REQUIRED
  ↓
AGENT REQUESTS APPROVAL & PAUSES AT PENDING_APPROVAL
  ↓
HUMAN ORGANIZER SIGNS OFF (STATUS = APPROVED)
  ↓
AGENT RESUMES WITH APPROVAL_ID
  ↓
PHASE 9 ACTION SERVICE EXECUTES
  ↓
PHASE 10 VERIFICATION SERVICE VERIFIES
  ↓
EVENT STATE RESTORED TO NORMAL
  ↓
DECISION TRACE RECORDED
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agent.agent import EventOperationsAgent
from app.agent.provider import MockLLMProvider
from app.models.event import Event
from app.models.user import User
from app.models.event_member import EventMember
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.budget import BudgetItem
from app.models.objective import Objective
from app.models.incident import Incident
from app.models.approval import Approval
from app.models.enums import (
    EventLifecycleState,
    EventState,
    RoleType,
    TaskPriority,
    TaskStatus,
    IncidentType,
    IncidentSeverity,
)


def _setup_live_catering_scenario(db: Session):
    """Sets up an authoritative live event with a critical catering task and backup vendor."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # 1. Users
    organizer = User(name="Elena Ops Lead", email="elena.ops@eventra.test")
    collaborator = User(name="Alex Floor Manager", email="alex.floor@eventra.test")
    db.add_all([organizer, collaborator])
    db.flush()

    # 2. Event (LIVE, currently NORMAL)
    event = Event(
        owner_id=organizer.id,
        name="Global Leadership Summit 2026",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(hours=2),
        end_datetime=now + timedelta(hours=12),
        total_budget=Decimal("80000.00"),
    )
    db.add(event)
    db.flush()

    # 3. Memberships
    mem_org = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    mem_collab = EventMember(event_id=event.id, user_id=collaborator.id, role=RoleType.COLLABORATOR.value)
    db.add_all([mem_org, mem_collab])

    # 4. Critical Catering Task
    lunch_task = Task(
        event_id=event.id,
        name="Delegate Lunch Banquet",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=90,
        is_critical_path=True,
        slack_minutes=15,
        required_provider_category="catering",
        planned_start=now + timedelta(hours=3),
        planned_end=now + timedelta(hours=4, minutes=30),
    )
    db.add(lunch_task)
    db.flush()

    # 5. Primary Vendor (assigned) & Backup Vendor (available in network)
    primary_vendor = Vendor(
        name="Original Caterer Inc",
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

    # 6. Budget & Objective
    budget = BudgetItem(
        event_id=event.id,
        name="Catering & Hospitality",
        category="catering",
        estimated_amount=Decimal("6000.00"),
        actual_amount=Decimal("4000.00"),
    )
    objective = Objective(
        event_id=event.id,
        name="Flawless Executive Lunch Service",
        priority="CRITICAL",
    )
    db.add_all([budget, objective])
    db.commit()

    return {
        "organizer": organizer,
        "collaborator": collaborator,
        "event": event,
        "task": lunch_task,
        "primary_vendor": primary_vendor,
        "backup_vendor": backup_vendor,
        "budget": budget,
        "objective": objective,
    }


def test_mandatory_vendor_no_show_vertical_slice(db_session: Session):
    """The Mandatory Core Scenario:
    Event LIVE -> Catering No-Show incident -> Observe -> Interpret -> Impact/Risk ->
    Recovery Candidates (Phase 8) -> Select Valid Option -> Authorize ->
    Approval Requested (PENDING_APPROVAL) -> Human Organizer Signs Off ->
    Resume Agent with approval_id -> Execute (Phase 9) -> Verify (Phase 10) ->
    Event Restored to NORMAL -> Decision Trace confirmed.
    """
    ctx = _setup_live_catering_scenario(db_session)
    event = ctx["event"]
    organizer = ctx["organizer"]
    collaborator = ctx["collaborator"]
    task = ctx["task"]

    # 1. Ingest VENDOR_NO_SHOW Incident
    incident = Incident(
        event_id=event.id,
        title="Primary Caterer Reported No-Show",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
        related_vendor_id=ctx["primary_vendor"].id,
    )
    db_session.add(incident)
    # Operational impact transitions event to AT_RISK or CRITICAL
    event.state = EventState.CRITICAL.value
    db_session.commit()

    # 2. Initialize Agent
    agent = EventOperationsAgent(db_session, llm_provider=MockLLMProvider())

    # 3. Collaborator runs Agent: "Our caterer just cancelled. What should we do?"
    run_1 = agent.run(
        event_id=event.id,
        message="Our caterer just cancelled. What should we do?",
        user_id=collaborator.id,
    )

    # 4. Assert Safe Governance Gate: PENDING_APPROVAL
    assert run_1["status"] == "PENDING_APPROVAL"
    assert run_1["approval_id"] is not None
    assert run_1["execution"] is None  # Must NOT execute without approval!
    assert "Approval requested" in run_1["response"]
    assert run_1["selected_option"] is not None
    assert run_1["risk"] is not None

    approval_id = run_1["approval_id"]

    # 5. Verify the approval record exists in Phase 9
    approval_record = db_session.query(Approval).filter(Approval.id == approval_id).first()
    assert approval_record is not None
    assert approval_record.status == "PENDING"
    assert approval_record.event_id == event.id
    assert approval_record.requester_id == collaborator.id

    # 6. Human Lead Organizer Reviews and Approves the Ticket in Phase 9
    approval_record.status = "APPROVED"
    approval_record.approver_id = organizer.id
    approval_record.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    approval_record.decision_notes = "Approved vendor reassignment to backup caterer."
    db_session.commit()

    # 7. Agent Resumes Run with approval_id
    run_2 = agent.run(
        event_id=event.id,
        message="Approval granted. Execute caterer replacement.",
        user_id=collaborator.id,
        approval_id=approval_id,
    )

    # 8. Assert Successful Execution, Verification & Normal State Restoration
    assert run_2["status"] in ("COMPLETED", "VERIFIED")
    assert run_2["execution"] is not None
    assert run_2["execution"]["status"] == "SUCCESS"
    assert run_2["verification"] is not None
    assert run_2["verification"]["status"] in ("VERIFIED", "PARTIALLY_VERIFIED")

    # 9. Verify Authoritative Live Event State in PostgreSQL
    db_session.refresh(event)
    assert event.state == EventState.NORMAL.value

    # 10. Verify Decision Trace Links the Pipeline
    trace = run_2["decision_trace"]
    assert trace is not None
    assert "verification_id" in trace
    assert trace["event_id"] == event.id


def test_agent_rest_api_endpoint(test_client: TestClient, db_session: Session):
    """Verifies POST /api/agent/events/{event_id}/run endpoint."""
    ctx = _setup_live_catering_scenario(db_session)
    event = ctx["event"]
    organizer = ctx["organizer"]
    task = ctx["task"]

    # Ingest incident
    incident = Incident(
        event_id=event.id,
        title="Audio equipment delay",
        incident_type=IncidentType.VENDOR_DELAY.value,
        severity=IncidentSeverity.HIGH.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    # Call API endpoint
    resp = test_client.post(
        f"/api/agent/events/{event.id}/run",
        json={"message": "Audio team reports delay, check status."},
        headers={"x-user-id": organizer.id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event.id
    assert data["status"] in ("COMPLETED", "PENDING_APPROVAL", "OPTIONS_GENERATED", "OBSERVING")
    assert "response" in data
    assert data["response"] is not None
