"""Unit Tests: ApprovalService (Governance, Separation of Duties, Stale Revalidation)"""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.enums import RoleType, TaskPriority, EventState
from app.schemas.approval import ApprovalRequestCreate
from app.services.approval_service import ApprovalService
from app.core.exceptions import ForbiddenException, ConflictException, BadRequestException


def _setup_approval_context(db: Session):
    organizer = User(name="Organizer", email="organizer@eventra.demo")
    collaborator = User(name="Collaborator", email="collab@eventra.demo")
    manager = User(name="Manager", email="manager@eventra.demo")
    db.add_all([organizer, collaborator, manager])
    db.commit()

    event = Event(
        owner_id=organizer.id,
        name="Global Tech Gala",
        state=EventState.NORMAL.value,
        total_budget=Decimal("60000.00"),
    )
    db.add(event)
    db.commit()

    m1 = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    m2 = EventMember(event_id=event.id, user_id=collaborator.id, role=RoleType.COLLABORATOR.value)
    m3 = EventMember(event_id=event.id, user_id=manager.id, role=RoleType.EVENT_MANAGER.value)
    db.add_all([m1, m2, m3])
    db.commit()

    task = Task(
        event_id=event.id,
        name="Keynote Sound Stage",
        priority=TaskPriority.HIGH.value,
        is_critical_path=True,
        slack_minutes=0,
    )
    vendor_old = Vendor(name="Old Sound Co", category="sound", city="Chicago")
    vendor_new = Vendor(name="New Pro Sound", category="sound", city="Chicago")
    db.add_all([task, vendor_old, vendor_new])
    db.commit()

    return {
        "event": event,
        "organizer": organizer,
        "collaborator": collaborator,
        "manager": manager,
        "task": task,
        "vendor_old": vendor_old,
        "vendor_new": vendor_new,
    }


def test_create_approval_request_success(db_session: Session):
    """Collaborator submitting a major action creates an immutable PENDING approval request."""
    ctx = _setup_approval_context(db_session)
    service = ApprovalService(db_session)

    req_data = ApprovalRequestCreate(
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        requested_action={"new_vendor_id": ctx["vendor_new"].id, "agreed_cost": 1500.0},
        notes="Primary vendor delayed, replacement required urgently.",
    )

    approval = service.create_request(
        event_id=ctx["event"].id,
        requester_id=ctx["collaborator"].id,
        data=req_data,
    )

    assert approval.id is not None
    assert approval.status == "PENDING"
    assert approval.impact_level in ("MAJOR", "CRITICAL")
    assert approval.state_snapshot is not None
    assert approval.requested_action["new_vendor_id"] == ctx["vendor_new"].id


def test_separation_of_duties_self_approval_rejected(db_session: Session):
    """Requester attempting to approve their own request is rejected."""
    ctx = _setup_approval_context(db_session)
    service = ApprovalService(db_session)

    req_data = ApprovalRequestCreate(
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        requested_action={"new_vendor_id": ctx["vendor_new"].id, "agreed_cost": 1500.0},
    )
    approval = service.create_request(ctx["event"].id, ctx["collaborator"].id, req_data)

    # Collaborator attempts to approve their own request
    with pytest.raises(ForbiddenException) as exc:
        service.approve(
            event_id=ctx["event"].id,
            approval_id=approval.id,
            approver_id=ctx["collaborator"].id,
        )
    assert "Separation of duties violation" in str(exc.value)


def test_approval_role_eligibility(db_session: Session):
    """Collaborators cannot approve requests (only managers and organizers)."""
    ctx = _setup_approval_context(db_session)
    service = ApprovalService(db_session)

    req_data = ApprovalRequestCreate(
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        requested_action={"new_vendor_id": ctx["vendor_new"].id, "agreed_cost": 1500.0},
    )
    approval = service.create_request(ctx["event"].id, ctx["organizer"].id, req_data)

    # Collaborator attempts to approve organizer's request
    with pytest.raises(ForbiddenException) as exc:
        service.approve(
            event_id=ctx["event"].id,
            approval_id=approval.id,
            approver_id=ctx["collaborator"].id,
        )
    assert "lacks permission" in str(exc.value)


def test_successful_approval_triggers_execution(db_session: Session):
    """Main Organizer approves collaborator's request, mutating state and recording execution."""
    ctx = _setup_approval_context(db_session)
    service = ApprovalService(db_session)

    req_data = ApprovalRequestCreate(
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        requested_action={"new_vendor_id": ctx["vendor_new"].id, "agreed_cost": 1800.0},
    )
    approval = service.create_request(ctx["event"].id, ctx["collaborator"].id, req_data)

    # Organizer approves
    approved_req, execution = service.approve(
        event_id=ctx["event"].id,
        approval_id=approval.id,
        approver_id=ctx["organizer"].id,
        decision_notes="Approved immediately to preserve keynote schedule.",
    )

    assert approved_req.status == "APPROVED"
    assert approved_req.approver_id == ctx["organizer"].id
    assert approved_req.decided_at is not None
    assert execution is not None
    assert execution.status == "SUCCESS"


def test_reject_approval_request(db_session: Session):
    """Authorized approver rejects request with reason; no mutations occur."""
    ctx = _setup_approval_context(db_session)
    service = ApprovalService(db_session)

    req_data = ApprovalRequestCreate(
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        requested_action={"new_vendor_id": ctx["vendor_new"].id, "agreed_cost": 2500.0},
    )
    approval = service.create_request(ctx["event"].id, ctx["collaborator"].id, req_data)

    rejected = service.reject(
        event_id=ctx["event"].id,
        approval_id=approval.id,
        approver_id=ctx["organizer"].id,
        reason="Replacement quote exceeds available contingency buffer.",
    )
    assert rejected.status == "REJECTED"
    assert "Replacement quote exceeds" in rejected.rejection_reason


def test_cancel_approval_request(db_session: Session):
    """Requester can cancel a pending approval request."""
    ctx = _setup_approval_context(db_session)
    service = ApprovalService(db_session)

    req_data = ApprovalRequestCreate(
        action_type="ADJUST_SCHEDULE",
        target_type="TASK",
        target_id=ctx["task"].id,
        requested_action={"shift_minutes": 30},
    )
    approval = service.create_request(ctx["event"].id, ctx["collaborator"].id, req_data)

    cancelled = service.cancel(
        event_id=ctx["event"].id,
        approval_id=approval.id,
        requester_id=ctx["collaborator"].id,
        reason="Vendor recovered lost time, delay cancelled.",
    )
    assert cancelled.status == "CANCELLED"


def test_stale_approval_request_rejected(db_session: Session):
    """If event state changes before approval, execution is rejected with STALE_ACTION / ConflictException."""
    ctx = _setup_approval_context(db_session)
    service = ApprovalService(db_session)

    req_data = ApprovalRequestCreate(
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=ctx["task"].id,
        requested_action={"new_vendor_id": ctx["vendor_new"].id, "agreed_cost": 1500.0},
    )
    approval = service.create_request(ctx["event"].id, ctx["collaborator"].id, req_data)

    # Concurrency mutation: Another user updates the task in the background
    ctx["task"].duration_minutes = 120
    db_session.commit()

    # Organizer attempts to approve the now-stale request
    with pytest.raises(ConflictException) as exc:
        service.approve(
            event_id=ctx["event"].id,
            approval_id=approval.id,
            approver_id=ctx["organizer"].id,
        )
    assert "STALE_ACTION" in str(exc.value)

    db_session.refresh(approval)
    assert approval.status == "STALE"
