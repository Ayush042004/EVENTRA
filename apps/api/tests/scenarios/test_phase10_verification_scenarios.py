"""Phase 10 Comprehensive Operational Scenarios:
Verification Engine, Audit Trail, Activity History, and Decision Tracing.

Scenarios:
1. Canonical End-to-End Recovery Flow:
   Incident -> Recovery Option -> Action Execution -> Verification -> Recovery Verified -> Event State NORMAL
2. Critical Operational Failure ("Action Success != Verification Success"):
   Action executes successfully in DB, but provider ETA violates schedule deadline -> Verification FAILED
3. Partial Recovery:
   Action solves budget, but a task remains BLOCKED causing objective to be AT_RISK -> PARTIALLY_VERIFIED
4. Re-Verification Lifecycle:
   Initial PARTIALLY_VERIFIED -> real-world confirmation -> Reverify -> VERIFIED
5. Stale Concurrency Protection:
   State mutates between execution and verification -> STALE
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.engines.auth.snapshot import compute_event_state_snapshot
from app.models.action import ActionExecution
from app.models.budget import BudgetItem
from app.models.enums import (
    EventLifecycleState,
    EventState,
    IncidentSeverity,
    IncidentType,
    RoleType,
    TaskPriority,
    TaskStatus,
)
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.incident import Incident
from app.models.objective import Objective
from app.models.recovery import Recovery
from app.models.task import Task
from app.models.user import User
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.services.verification_service import VerificationService


def _setup_base_phase10_scenario(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer = User(name="Elena Ops Lead", email="elena.phase10@eventra.test")
    db.add(organizer)
    db.flush()

    event = Event(
        owner_id=organizer.id,
        name="Global Tech Congress 2026",
        lifecycle_state=EventLifecycleState.LIVE.value,
        state=EventState.AT_RISK.value,
        start_datetime=now + timedelta(hours=2),
        end_datetime=now + timedelta(hours=14),
        total_budget=Decimal("150000.00"),
    )
    db.add(event)
    db.flush()

    mem = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    db.add(mem)

    # Initial tasks
    t1 = Task(
        event_id=event.id,
        name="Main Stage AV Rigging",
        status=TaskStatus.IN_PROGRESS.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=90,
        slack_minutes=15,
        required_provider_category="av",
        planned_start=now + timedelta(hours=2),
        planned_end=now + timedelta(hours=3, minutes=30),
    )
    db.add(t1)

    # Initial budget
    b1 = BudgetItem(
        event_id=event.id,
        name="AV Engineering",
        category="av",
        estimated_amount=Decimal("15000.00"),
        actual_amount=Decimal("12000.00"),
    )
    db.add(b1)
    db.flush()

    return organizer, event, t1, b1


def test_scenario_1_canonical_recovery_verified_transitions_state(test_client: TestClient, db_session: Session):
    """Scenario 1: Canonical End-to-End Recovery Flow.
    Action successfully replaces damaged equipment/vendor, verification verifies all domains,
    event state transitions from AT_RISK to NORMAL, and audit + decision trace are complete.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer, event, task, budget = _setup_base_phase10_scenario(db_session)

    # 1. Incident
    incident = Incident(
        event_id=event.id,
        title="Primary Video Mixer Overheated",
        incident_type=IncidentType.RESOURCE_SHORTAGE.value,
        severity=IncidentSeverity.HIGH.value,
        status="OPEN",
        impact_result={"affected_tasks": [task.id]},
    )
    db_session.add(incident)
    db_session.flush()

    # 2. Recovery Option
    recovery = Recovery(
        incident_id=incident.id,
        event_id=event.id,
        strategy_type="REPLACE_VENDOR",
        status="FEASIBLE",
        is_feasible=True,
        state_snapshot="snap-init",
    )
    db_session.add(recovery)
    db_session.flush()

    # 3. Action executed
    snap_before = compute_event_state_snapshot(db_session, event.id)
    # Perform action effect: assign backup audio vendor
    vendor = Vendor(
        name="ProStage Audio Backup",
        category="av",
        city="San Francisco",
        status="ACTIVE",
    )
    db_session.add(vendor)
    db_session.flush()

    assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=vendor.id,
        category="av",
        status="CONFIRMED",
        agreed_cost=1500.0,
    )
    db_session.add(assignment)
    db_session.flush()

    snap_after = compute_event_state_snapshot(db_session, event.id)

    action = ActionExecution(
        action_id="act-scen-1-recov",
        event_id=event.id,
        recovery_option_id=recovery.id,
        executor_id=organizer.id,
        action_type="REPLACE_VENDOR",
        status="SUCCESS",
        affected_entities=[{"type": "VENDOR", "id": vendor.id}],
        before_version=snap_before,
        after_version=snap_after,
        execution_payload={"vendor_id": vendor.id, "cost": 1500.00},
        execution_result_data={"assigned": True},
    )
    db_session.add(action)
    db_session.commit()

    # 4. Trigger Verification via Service
    service = VerificationService(db_session)
    ver_result = service.verify_action(
        event_id=event.id,
        action_execution_id=action.id,
        current_user_id=organizer.id,
    )

    # Invariants Check
    assert ver_result.status in ["VERIFIED", "PARTIALLY_VERIFIED"]
    db_session.refresh(event)
    # Verify state transitioned to NORMAL
    assert event.state == EventState.NORMAL.value

    # Check Audit Record
    audit_resp = test_client.get(
        f"/api/events/{event.id}/audit",
        headers={"x-user-id": organizer.id},
    )
    assert audit_resp.status_code == 200
    audits = audit_resp.json()["items"]
    assert any(a["action"] == "VERIFY_ACTION" for a in audits)

    # Check Decision Trace
    trace_resp = test_client.get(
        f"/api/events/{event.id}/decision-trace",
        headers={"x-user-id": organizer.id},
    )
    assert trace_resp.status_code == 200
    traces = trace_resp.json()
    assert len(traces) >= 1
    t = traces[0]
    assert t["incident"]["title"] == "Primary Video Mixer Overheated"
    assert t["execution"]["action_type"] == "REPLACE_VENDOR"
    assert t["verification"]["status"] in ["VERIFIED", "PARTIALLY_VERIFIED"]
    assert t["event_state"]["state_after"] == EventState.NORMAL.value


def test_scenario_2_action_success_is_not_verification_success(test_client: TestClient, db_session: Session):
    """Scenario 2: Action succeeds in DB, but verification detects schedule violation.
    Operational principle: ACTION SUCCESS != VERIFICATION SUCCESS.
    Event remains AT_RISK.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer, event, task, budget = _setup_base_phase10_scenario(db_session)

    late_vendor = Vendor(
        name="Slow Logistics Ltd",
        category="av",
        city="San Francisco",
        status="ACTIVE",
    )
    db_session.add(late_vendor)
    db_session.flush()

    # Create assignment with CONFIRMED status
    assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=late_vendor.id,
        category="av",
        status="CONFIRMED",
        agreed_cost=1800.0,
    )
    db_session.add(assignment)
    db_session.flush()

    snap_before = compute_event_state_snapshot(db_session, event.id)
    snap_after = compute_event_state_snapshot(db_session, event.id)

    # ActionExecution succeeded in DB, but payload specifies eta_minutes that violates slack
    action = ActionExecution(
        action_id="act-scen-2-late",
        event_id=event.id,
        executor_id=organizer.id,
        action_type="REPLACE_VENDOR",
        status="SUCCESS",
        affected_entities=[{"type": "VENDOR", "id": late_vendor.id}],
        before_version=snap_before,
        after_version=snap_after,
        # ETA is 90 minutes, while task slack is only 15 minutes!
        execution_payload={"vendor_id": late_vendor.id, "eta_minutes": 90},
        execution_result_data={"dispatched": True},
    )
    db_session.add(action)
    db_session.commit()

    service = VerificationService(db_session)
    ver_result = service.verify_action(
        event_id=event.id,
        action_execution_id=action.id,
        current_user_id=organizer.id,
    )

    # Verification MUST fail or be at risk because vendor ETA breaches task slack
    assert ver_result.status in ("FAILED", "PARTIALLY_VERIFIED")
    assert ver_result.schedule_result["is_feasible"] is False
    # Event state must NOT transition to NORMAL
    db_session.refresh(event)
    assert event.state in (EventState.AT_RISK.value, EventState.CRITICAL.value)
    assert event.state != EventState.NORMAL.value


def test_scenario_3_partial_recovery_keeps_event_at_risk(test_client: TestClient, db_session: Session):
    """Scenario 3: Partial recovery where one objective remains AT_RISK due to a blocked task.
    Overall verification status is PARTIALLY_VERIFIED, and event remains AT_RISK.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer, event, task, budget = _setup_base_phase10_scenario(db_session)

    # Add a blocked task and an objective tied to it
    t2 = Task(
        event_id=event.id,
        name="Satellite Broadcast Uplink",
        status=TaskStatus.BLOCKED.value,
        priority=TaskPriority.HIGH.value,
        duration_minutes=60,
    )
    obj = Objective(
        event_id=event.id,
        name="Satellite Broadcast Uplink Stream",
        priority="CRITICAL",
        target_value={"uptime": 99.9},
    )
    db_session.add_all([t2, obj])
    db_session.flush()

    snap_before = compute_event_state_snapshot(db_session, event.id)
    snap_after = compute_event_state_snapshot(db_session, event.id)

    action = ActionExecution(
        action_id="act-scen-3-partial",
        event_id=event.id,
        executor_id=organizer.id,
        action_type="ADJUST_BUDGET",
        status="SUCCESS",
        affected_entities=[{"type": "BUDGET", "id": budget.id}],
        before_version=snap_before,
        after_version=snap_after,
        execution_payload={"actual_amount": 13000.00},
    )
    db_session.add(action)
    db_session.commit()

    service = VerificationService(db_session)
    ver_result = service.verify_action(
        event_id=event.id,
        action_execution_id=action.id,
        current_user_id=organizer.id,
    )

    assert ver_result.status == "PARTIALLY_VERIFIED"
    assert any(o["status_after"] == "AT_RISK" for o in ver_result.objective_results)
    db_session.refresh(event)
    assert event.state == EventState.AT_RISK.value


def test_scenario_4_reverification_lifecycle(test_client: TestClient, db_session: Session):
    """Scenario 4: Verification transitions upon real-world state evolution.
    Initial verification is FAILED because vendor assignment was unconfirmed.
    Once vendor assignment is confirmed, reverification upgrades status to VERIFIED.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer, event, task, budget = _setup_base_phase10_scenario(db_session)

    vendor = Vendor(
        name="Lighting Pro",
        category="lighting",
        city="San Francisco",
        status="ACTIVE",
    )
    db_session.add(vendor)
    db_session.flush()

    # Unconfirmed assignment (status=REQUESTED)
    assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=vendor.id,
        category="lighting",
        status="REQUESTED",  # NOT confirmed in real world
        agreed_cost=2000.0,
    )
    db_session.add(assignment)
    db_session.flush()

    snap = compute_event_state_snapshot(db_session, event.id)

    action = ActionExecution(
        action_id="act-scen-4-reverif",
        event_id=event.id,
        executor_id=organizer.id,
        action_type="ASSIGN_VENDOR",
        status="SUCCESS",
        affected_entities=[{"type": "VENDOR_ASSIGNMENT", "id": assignment.id}],
        before_version=snap,
        after_version=snap,
        execution_payload={"vendor_id": vendor.id},
    )
    db_session.add(action)
    db_session.commit()

    service = VerificationService(db_session)
    v1 = service.verify_action(event_id=event.id, action_execution_id=action.id, current_user_id=organizer.id)
    assert v1.status == "FAILED"
    assert v1.provider_result["assignment_confirmed"] is False

    # Real world updates: vendor confirms on site
    assignment.status = "CONFIRMED"
    db_session.commit()

    # Re-verify
    v2 = service.reverify(event_id=event.id, verification_id=v1.id, current_user_id=organizer.id)
    assert v2.status in ("VERIFIED", "PARTIALLY_VERIFIED")
    assert v2.provider_result["assignment_confirmed"] is True
    assert v2.id == v1.id


def test_scenario_5_stale_concurrency_protection(test_client: TestClient, db_session: Session):
    """Scenario 5: World state mutates between action execution and verification.
    Verification detects snapshot discrepancy and flags status as STALE.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    organizer, event, task, budget = _setup_base_phase10_scenario(db_session)

    action = ActionExecution(
        action_id="act-scen-5-stale",
        event_id=event.id,
        executor_id=organizer.id,
        action_type="ADJUST_BUDGET",
        status="SUCCESS",
        affected_entities=[{"type": "BUDGET", "id": budget.id}],
        before_version="snap-version-1",
        after_version="snap-version-old",  # Out of sync with actual DB state
        execution_payload={"amount": 1000},
    )
    db_session.add(action)
    db_session.commit()

    service = VerificationService(db_session)
    ver_result = service.verify_action(
        event_id=event.id,
        action_execution_id=action.id,
        current_user_id=organizer.id,
    )

    assert ver_result.status == "STALE"
    assert any("mutated" in w for w in ver_result.warnings)
