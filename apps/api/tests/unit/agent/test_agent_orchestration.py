"""Unit tests for Phase 11: Event Operations Agent Orchestration."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.agent.provider import MockLLMProvider
from app.agent.agent import EventOperationsAgent
from app.agent.tools.operations_tools import (
    get_event_state,
    get_incidents,
    analyze_impact,
    calculate_risk,
    generate_recovery_options,
    validate_recovery_option,
    check_action_authorization,
    request_action_approval,
    check_approval_status,
    execute_action,
    verify_action,
)
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.user import User
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.budget import BudgetItem
from app.models.incident import Incident
from app.models.recovery import Recovery
from app.models.approval import Approval
from app.models.enums import EventLifecycleState, EventState, RoleType, TaskPriority, TaskStatus, IncidentType, IncidentSeverity


def _setup_test_event(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user = User(name="Alice Lead", email="alice.lead@eventra.test")
    db.add(user)
    db.flush()

    event = Event(
        owner_id=user.id,
        name="Tech Gala 2026",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.AT_RISK.value,
        start_datetime=now + timedelta(hours=2),
        end_datetime=now + timedelta(hours=10),
        total_budget=Decimal("50000.00"),
    )
    db.add(event)
    db.flush()

    mem = EventMember(event_id=event.id, user_id=user.id, role=RoleType.MAIN_ORGANIZER.value)
    db.add(mem)

    task = Task(
        event_id=event.id,
        name="Catering Setup",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=60,
        required_provider_category="catering",
        planned_start=now + timedelta(hours=2),
        planned_end=now + timedelta(hours=3),
    )
    db.add(task)

    vendor = Vendor(
        name="Gourmet Catering Co",
        category="catering",
        city="Seattle",
        base_cost=3000.0,
    )
    db.add(vendor)

    budget = BudgetItem(
        event_id=event.id,
        name="Catering Budget",
        category="catering",
        estimated_amount=Decimal("4000.00"),
        actual_amount=Decimal("3000.00"),
    )
    db.add(budget)
    db.commit()

    return user, event, task, vendor


def test_agent_state_initializes_correctly(db_session: Session):
    """1. Agent state initializes correctly with required schema."""
    user, event, _, _ = _setup_test_event(db_session)
    agent = EventOperationsAgent(db_session, llm_provider=MockLLMProvider())

    result = agent.run(
        event_id=event.id,
        message="System check",
        user_id=user.id,
    )

    assert result["event_id"] == event.id
    assert result["status"] in ("COMPLETED", "PENDING_APPROVAL", "OBSERVING")
    assert result["step_count"] >= 1


def test_observe_retrieves_event_state(db_session: Session):
    """2. Observe retrieves authoritative event state from database."""
    user, event, task, _ = _setup_test_event(db_session)
    state_data = get_event_state(db_session, event.id)

    assert state_data["event_id"] == event.id
    assert state_data["name"] == "Tech Gala 2026"
    assert state_data["lifecycle_state"] == EventLifecycleState.LIVE.value
    assert state_data["task_counts"]["total"] == 1
    assert state_data["total_budget"] == 50000.0


def test_agent_calls_impact_tool(db_session: Session):
    """3. Agent can call impact analysis tool and receive deterministic result."""
    user, event, task, vendor = _setup_test_event(db_session)
    incident = Incident(
        event_id=event.id,
        title="Caterer reported delay",
        incident_type=IncidentType.VENDOR_DELAY.value,
        severity=IncidentSeverity.HIGH.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    impact = analyze_impact(db_session, event.id, incident.id)
    assert impact is not None
    assert "directly_affected_tasks" in impact or "schedule_impact" in impact


def test_agent_calls_risk_tool(db_session: Session):
    """4. Agent can call risk calculation tool and receive deterministic score."""
    user, event, task, vendor = _setup_test_event(db_session)
    incident = Incident(
        event_id=event.id,
        title="Caterer vehicle breakdown",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    risk = calculate_risk(db_session, event.id, incident.id)
    assert risk is not None
    assert "score" in risk and "level" in risk


def test_agent_generates_recovery_options(db_session: Session):
    """5. Agent calls Phase 8 RecoveryEngine to generate candidate options."""
    user, event, task, vendor = _setup_test_event(db_session)
    # Add a backup vendor
    backup_vendor = Vendor(
        name="Backup Chef Express",
        category="catering",
        city="Seattle",
        base_cost=3200.0,
        status="ACTIVE",
    )
    db_session.add(backup_vendor)

    incident = Incident(
        event_id=event.id,
        title="Primary Caterer No-Show",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    options = generate_recovery_options(db_session, event.id, incident.id, user.id)
    assert len(options) > 0
    assert any("strategy_type" in opt for opt in options)


def test_infeasible_recovery_option_cannot_execute(db_session: Session):
    """6. Infeasible recovery option cannot execute."""
    user, event, task, vendor = _setup_test_event(db_session)
    incident = Incident(
        event_id=event.id,
        title="Caterer No-Show",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.flush()

    infeasible_opt = Recovery(
        event_id=event.id,
        incident_id=incident.id,
        strategy_type="REPLACE_VENDOR",
        status="INFEASIBLE",
        is_feasible=False,
        state_snapshot="snap-test",
        feasibility_result={"feasible": False, "violations": ["BUDGET_CAP_EXCEEDED"]},
    )
    db_session.add(infeasible_opt)
    db_session.commit()

    val = validate_recovery_option(db_session, event.id, incident.id, infeasible_opt.id, user.id)
    assert val["is_feasible"] is False


def test_authorization_is_respected(db_session: Session):
    """7. Authorization is respected and evaluates impact policy."""
    user, event, task, vendor = _setup_test_event(db_session)

    # Main organizer performing an action
    auth_lead = check_action_authorization(
        db=db_session,
        event_id=event.id,
        user_id=user.id,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=task.id,
    )
    assert auth_lead["allowed"] is True

    # Viewer attempting an action
    viewer = User(name="Bob Viewer", email="bob.viewer@eventra.test")
    db_session.add(viewer)
    db_session.flush()
    mem_v = EventMember(event_id=event.id, user_id=viewer.id, role=RoleType.VIEWER.value)
    db_session.add(mem_v)
    db_session.commit()

    auth_viewer = check_action_authorization(
        db=db_session,
        event_id=event.id,
        user_id=viewer.id,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=task.id,
    )
    assert auth_viewer["allowed"] is False


def test_approval_required_action_pauses_correctly(db_session: Session):
    """8. Actions requiring approval pause safely at PENDING_APPROVAL without executing."""
    user, event, task, vendor = _setup_test_event(db_session)

    # Collaborator role requires approval for critical path / high impact actions
    collab = User(name="Charlie Collab", email="charlie.collab@eventra.test")
    db_session.add(collab)
    db_session.flush()
    db_session.add(EventMember(event_id=event.id, user_id=collab.id, role=RoleType.COLLABORATOR.value))

    # Add backup vendor
    backup_vendor = Vendor(
        name="Star Caterers",
        category="catering",
        city="Seattle",
        base_cost=3100.0,
        status="ACTIVE",
    )
    db_session.add(backup_vendor)

    incident = Incident(
        event_id=event.id,
        title="Catering Cancellation",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    agent = EventOperationsAgent(db_session, llm_provider=MockLLMProvider())
    result = agent.run(
        event_id=event.id,
        message="Catering cancelled, what should we do?",
        user_id=collab.id,
    )

    assert result["status"] == "PENDING_APPROVAL"
    assert result["approval_id"] is not None
    assert result["execution"] is None  # Action was NOT executed!


def test_approved_action_executes_on_resume(db_session: Session):
    """9. Approved action executes upon resume with verified approval_id."""
    user, event, task, vendor = _setup_test_event(db_session)
    collab = User(name="Dave Collab", email="dave.collab@eventra.test")
    db_session.add(collab)
    db_session.flush()
    db_session.add(EventMember(event_id=event.id, user_id=collab.id, role=RoleType.COLLABORATOR.value))

    backup_vendor = Vendor(name="Summit Foods", category="catering", city="Seattle", base_cost=3000.0, status="ACTIVE")
    db_session.add(backup_vendor)

    incident = Incident(
        event_id=event.id,
        title="Catering No-Show",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    agent = EventOperationsAgent(db_session, llm_provider=MockLLMProvider())
    # 1. Initial run enters PENDING_APPROVAL
    initial_res = agent.run(
        event_id=event.id,
        message="Catering provider cancelled.",
        user_id=collab.id,
    )
    assert initial_res["status"] == "PENDING_APPROVAL"
    appr_id = initial_res["approval_id"]
    assert appr_id is not None

    # 2. Main organizer approves the ticket in Phase 9
    appr = db_session.query(Approval).filter(Approval.id == appr_id).first()
    appr.status = "APPROVED"
    appr.approver_id = user.id
    appr.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.commit()

    # 3. Agent runs again with approval_id to resume
    resume_res = agent.run(
        event_id=event.id,
        message="Proceed with approved catering recovery.",
        user_id=collab.id,
        approval_id=appr_id,
    )

    assert resume_res["status"] in ("COMPLETED", "VERIFIED")
    assert resume_res["execution"] is not None
    assert resume_res["verification"] is not None


def test_verification_is_called_after_execution(db_session: Session):
    """10. Verification is called after execution and produces verification result."""
    user, event, task, vendor = _setup_test_event(db_session)
    backup_vendor = Vendor(name="Elite Catering", category="catering", city="Seattle", base_cost=3000.0, status="ACTIVE")
    db_session.add(backup_vendor)

    incident = Incident(
        event_id=event.id,
        title="Catering Provider Failure",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    # Organizer executes directly (as organizer has direct execution authority for their event)
    agent = EventOperationsAgent(db_session, llm_provider=MockLLMProvider())
    result = agent.run(
        event_id=event.id,
        message="Fix the catering issue immediately.",
        user_id=user.id,
    )

    assert result["status"] in ("COMPLETED", "PENDING_APPROVAL", "VERIFIED")
    if result["status"] == "COMPLETED":
        assert result["verification"] is not None
        assert "status" in result["verification"]


def test_approval_cannot_be_bypassed(db_session: Session):
    """11. Approval cannot be bypassed: Critical action requires approval and execute_action is NOT called."""
    user, event, task, vendor = _setup_test_event(db_session)
    collab = User(name="Sam Collab", email="sam.collab@eventra.test")
    db_session.add(collab)
    db_session.flush()
    db_session.add(EventMember(event_id=event.id, user_id=collab.id, role=RoleType.COLLABORATOR.value))

    incident = Incident(
        event_id=event.id,
        title="Primary Caterer No-Show",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    agent = EventOperationsAgent(db_session, llm_provider=MockLLMProvider())
    res = agent.run(
        event_id=event.id,
        message="Immediately replace caterer without sign-off.",
        user_id=collab.id,
    )

    # Invariant check: MUST be PENDING_APPROVAL, execution MUST be None
    assert res["status"] == "PENDING_APPROVAL"
    assert res["execution"] is None


def test_fake_approval_id_cannot_bypass_policy(db_session: Session):
    """12. Fake/invalid approval_id cannot bypass policy; system enforces DB verification."""
    user, event, task, vendor = _setup_test_event(db_session)
    collab = User(name="Eve Collab", email="eve.collab@eventra.test")
    db_session.add(collab)
    db_session.flush()
    db_session.add(EventMember(event_id=event.id, user_id=collab.id, role=RoleType.COLLABORATOR.value))

    incident = Incident(
        event_id=event.id,
        title="Caterer No-Show",
        incident_type=IncidentType.VENDOR_NO_SHOW.value,
        severity=IncidentSeverity.CRITICAL.value,
        status="OPEN",
        related_task_id=task.id,
    )
    db_session.add(incident)
    db_session.commit()

    agent = EventOperationsAgent(db_session, llm_provider=MockLLMProvider())
    # Pass a non-existent fake approval_id
    res = agent.run(
        event_id=event.id,
        message="Execute reassign vendor with fake approval.",
        user_id=collab.id,
        approval_id="fake-approval-uuid-not-in-db",
    )

    # System detects approval is not APPROVED in DB, safely pauses at PENDING_APPROVAL
    assert res["status"] == "PENDING_APPROVAL"
    assert res["execution"] is None
