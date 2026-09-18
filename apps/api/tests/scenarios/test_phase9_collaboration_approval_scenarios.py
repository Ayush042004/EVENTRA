"""Phase 9 Comprehensive Scenario Tests: Collaboration, Approval, Stale Concurrency, Rollback, and Integrity"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.engines.auth.snapshot import compute_event_state_snapshot
from app.models.enums import EventLifecycleState, EventState, RoleType, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.incident import Incident
from app.models.recovery import Recovery
from app.models.task import Task
from app.models.user import User
from app.models.vendor import Vendor
from app.models.budget import BudgetItem


def _setup_scenario_environment(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Users
    organizer = User(name="Elena Organizer", email="elena.org@eventra.test")
    collaborator_a = User(name="Alex Collab", email="alex.collab@eventra.test")
    collaborator_b = User(name="Bella Collab", email="bella.collab@eventra.test")
    db.add_all([organizer, collaborator_a, collaborator_b])
    db.flush()

    # Event
    event = Event(
        owner_id=organizer.id,
        name="Summit 2026",
        lifecycle_state=EventLifecycleState.PLANNED.value,
        state=EventState.NORMAL.value,
        start_datetime=now + timedelta(days=7),
        end_datetime=now + timedelta(days=7, hours=12),
        total_budget=Decimal("100000.00"),
    )
    db.add(event)
    db.flush()

    # Memberships
    mem_org = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    mem_a = EventMember(event_id=event.id, user_id=collaborator_a.id, role=RoleType.COLLABORATOR.value)
    mem_b = EventMember(event_id=event.id, user_id=collaborator_b.id, role=RoleType.COLLABORATOR.value)
    db.add_all([mem_org, mem_a, mem_b])

    # Domain entities
    task_non_critical = Task(
        event_id=event.id,
        name="Print Name Tags",
        status=TaskStatus.READY.value,
        priority=TaskPriority.LOW.value,
        duration_minutes=30,
        is_critical_path=False,
    )
    task_critical = Task(
        event_id=event.id,
        name="Main Stage Lighting",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        duration_minutes=180,
        is_critical_path=True,
    )
    vendor1 = Vendor(name="LightWorks Pro", category="lighting", city="Seattle", base_cost=4000.0)
    vendor2 = Vendor(name="Apex Illumination", category="lighting", city="Seattle", base_cost=4500.0)
    budget_item = BudgetItem(
        event_id=event.id,
        name="Lighting Budget",
        category="lighting",
        estimated_amount=Decimal("5000.00"),
        actual_amount=Decimal("4000.00"),
    )
    db.add_all([task_non_critical, task_critical, vendor1, vendor2, budget_item])
    db.commit()

    return {
        "organizer": organizer,
        "collab_a": collaborator_a,
        "collab_b": collaborator_b,
        "event": event,
        "task_non_crit": task_non_critical,
        "task_crit": task_critical,
        "vendor1": vendor1,
        "vendor2": vendor2,
        "budget_item": budget_item,
    }


def test_scenario_minor_change_direct_execution(test_client: TestClient, db_session: Session):
    """Collaborator performs a MINOR action (low-priority task duration tweak) -> Executes directly."""
    data = _setup_scenario_environment(db_session)
    event_id = data["event"].id
    collab = data["collab_a"]
    task = data["task_non_crit"]

    resp = test_client.post(
        f"/api/events/{event_id}/actions",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": task.id,
            "payload": {"duration_minutes": 45},
        },
        headers={"x-user-id": collab.id},
    )
    assert resp.status_code == 200, resp.text
    res_data = resp.json()
    assert res_data["decision"]["requires_approval"] is False
    assert res_data["execution"] is not None
    assert res_data["execution"]["status"] == "SUCCESS"

    db_session.refresh(task)
    assert task.duration_minutes == 45


def test_scenario_major_change_approval_lifecycle(test_client: TestClient, db_session: Session):
    """Collaborator performs a MAJOR change (critical task modification) -> Requires approval -> Approved by Organizer."""
    data = _setup_scenario_environment(db_session)
    event_id = data["event"].id
    collab = data["collab_a"]
    organizer = data["organizer"]
    task = data["task_crit"]

    # 1. Submission requires approval
    resp = test_client.post(
        f"/api/events/{event_id}/actions",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": task.id,
            "payload": {"priority": "HIGH"},
        },
        headers={"x-user-id": collab.id},
    )
    assert resp.status_code == 200, resp.text
    res_data = resp.json()
    assert res_data["decision"]["requires_approval"] is True
    assert res_data["approval_request"] is not None
    approval_id = res_data["approval_request"]["id"]

    # 2. Requester cannot approve (Separation of duties)
    self_approve_resp = test_client.post(
        f"/api/events/{event_id}/approvals/{approval_id}/approve",
        json={"notes": "Trying to self approve"},
        headers={"x-user-id": collab.id},
    )
    assert self_approve_resp.status_code == 403

    # 3. Organizer approves
    approve_resp = test_client.post(
        f"/api/events/{event_id}/approvals/{approval_id}/approve",
        json={"notes": "Priority change approved by Lead Organizer"},
        headers={"x-user-id": organizer.id},
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "APPROVED"

    # 4. Verified state change in DB
    db_session.refresh(task)
    assert task.priority == "HIGH"


def test_scenario_section_35_stale_action_rejection(test_client: TestClient, db_session: Session):
    """SECTION 35 CRITICAL NEGATIVE TEST:
    1. User A generates a recovery option pinned to event snapshot S1.
    2. User B mutates event state (e.g. adjusts budget or task), changing event snapshot to S2.
    3. User A attempts to execute the recovery option.
    4. Execution MUST be rejected with STALE_ACTION (HTTP 409 Conflict) and NO state mutation.
    """
    data = _setup_scenario_environment(db_session)
    event_id = data["event"].id
    organizer = data["organizer"]
    collab_a = data["collab_a"]
    collab_b = data["collab_b"]
    task = data["task_crit"]

    # Snapshot S1 before any changes
    snapshot_s1 = compute_event_state_snapshot(db_session, event_id)

    # Create Incident and Recovery Option bound to Snapshot S1
    incident = Incident(
        event_id=event_id,
        title="Lighting Crew Delay",
        incident_type="VENDOR_DELAY",
        severity="HIGH",
        status="INVESTIGATING",
    )
    db_session.add(incident)
    db_session.flush()

    recovery_opt = Recovery(
        incident_id=incident.id,
        event_id=event_id,
        strategy_type="ADJUST_SCHEDULE",
        status="FEASIBLE",
        is_feasible=True,
        state_snapshot=snapshot_s1,
        affected_tasks=[task.id],
        proposed_changes={"schedule_adjustment": {"task_id": task.id, "shift_minutes": 30}},
    )
    db_session.add(recovery_opt)
    db_session.commit()

    # User B mutates the event independently (changes duration of non-critical task), changing snapshot to S2
    mut_resp = test_client.post(
        f"/api/events/{event_id}/actions",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": data["task_non_crit"].id,
            "payload": {"duration_minutes": 55},
        },
        headers={"x-user-id": collab_b.id},
    )
    assert mut_resp.status_code == 200

    # Verify event snapshot has moved to S2
    snapshot_s2 = compute_event_state_snapshot(db_session, event_id)
    assert snapshot_s1 != snapshot_s2

    # User A now attempts to execute the recovery option (which is still pinned to S1)
    exec_resp = test_client.post(
        f"/api/events/{event_id}/actions/execute-recovery",
        json={"recovery_option_id": recovery_opt.id},
        headers={"x-user-id": organizer.id},
    )
    assert exec_resp.status_code == 409, f"Expected 409 Conflict, got {exec_resp.status_code}"
    assert "STALE_ACTION" in exec_resp.json()["error"]["message"]

    # Verify task was NOT modified
    db_session.refresh(task)
    assert task.duration_minutes == 180
    db_session.refresh(recovery_opt)
    assert recovery_opt.status == "STALE"


def test_scenario_section_36_transaction_rollback_guarantee(test_client: TestClient, db_session: Session):
    """SECTION 36 TRANSACTION ROLLBACK TEST:
    When an action execution encounters an error mid-flight, the transaction rolls back cleanly
    and zero partial mutations are persisted in the database.
    """
    data = _setup_scenario_environment(db_session)
    event_id = data["event"].id
    organizer = data["organizer"]
    task = data["task_crit"]
    budget_item = data["budget_item"]

    orig_budget_actual = budget_item.actual_amount
    orig_provider_cat = task.required_provider_category

    # Attempt reassigning vendor to an invalid/non-existent vendor UUID
    resp = test_client.post(
        f"/api/events/{event_id}/actions",
        json={
            "action_type": "REASSIGN_VENDOR",
            "target_type": "TASK",
            "target_id": task.id,
            "payload": {
                "new_vendor_id": "00000000-0000-0000-0000-000000000000",
                "agreed_cost": 9999.00,
            },
        },
        headers={"x-user-id": organizer.id},
    )
    assert resp.status_code == 404, resp.text

    # Verify no partial mutations were committed
    db_session.refresh(task)
    assert task.required_provider_category == orig_provider_cat
    db_session.refresh(budget_item)
    assert budget_item.actual_amount == orig_budget_actual


def test_scenario_section_37_approval_integrity(test_client: TestClient, db_session: Session):
    """SECTION 37 APPROVAL INTEGRITY TEST:
    Approval requests are strictly immutable. Any modification or cancellation prevents execution,
    and stale requests cannot be approved.
    """
    data = _setup_scenario_environment(db_session)
    event_id = data["event"].id
    collab = data["collab_a"]
    organizer = data["organizer"]
    task = data["task_crit"]

    # 1. Create approval request
    resp = test_client.post(
        f"/api/events/{event_id}/approvals",
        json={
            "action_type": "REASSIGN_TASK",
            "target_type": "TASK",
            "target_id": task.id,
            "requested_action": {"duration_minutes": 240},
            "justification": "Extended rig time required",
        },
        headers={"x-user-id": collab.id},
    )
    assert resp.status_code == 201
    approval_id = resp.json()["id"]

    # 2. Requester cancels their approval request
    cancel_resp = test_client.post(
        f"/api/events/{event_id}/approvals/{approval_id}/cancel",
        headers={"x-user-id": collab.id},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # 3. Organizer attempts to approve a cancelled request -> 400 Bad Request
    approve_resp = test_client.post(
        f"/api/events/{event_id}/approvals/{approval_id}/approve",
        json={"notes": "Approving after cancel"},
        headers={"x-user-id": organizer.id},
    )
    assert approve_resp.status_code == 400
    assert "only PENDING requests can be approved" in approve_resp.json()["error"]["message"]
