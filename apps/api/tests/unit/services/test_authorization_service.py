"""Unit Tests: AuthorizationService & Role-Based Access Control (Phase 9 Gate 1 & Gate 2)"""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.budget import BudgetItem
from app.models.enums import RoleType, TaskPriority, EventState
from app.services.authorization_service import AuthorizationService
from app.core.exceptions import ForbiddenException, BadRequestException, NotFoundException


def _setup_event_with_team(db: Session):
    """Sets up an event with owner (organizer), manager, collaborator, vendor, and viewer."""
    organizer = User(name="Organizer", email="organizer@eventra.demo")
    manager = User(name="Manager", email="manager@eventra.demo")
    collaborator = User(name="Collaborator", email="collab@eventra.demo")
    vendor_user = User(name="Vendor User", email="vendor@eventra.demo")
    viewer = User(name="Viewer", email="viewer@eventra.demo")
    stranger = User(name="Stranger", email="stranger@eventra.demo")
    db.add_all([organizer, manager, collaborator, vendor_user, viewer, stranger])
    db.commit()

    event = Event(
        owner_id=organizer.id,
        name="Security Summit 2026",
        state=EventState.NORMAL.value,
        total_budget=Decimal("50000.00"),
    )
    db.add(event)
    db.commit()

    m_organizer = EventMember(event_id=event.id, user_id=organizer.id, role=RoleType.MAIN_ORGANIZER.value)
    m_manager = EventMember(event_id=event.id, user_id=manager.id, role=RoleType.EVENT_MANAGER.value)
    m_collab = EventMember(event_id=event.id, user_id=collaborator.id, role=RoleType.COLLABORATOR.value)
    m_vendor = EventMember(event_id=event.id, user_id=vendor_user.id, role=RoleType.VENDOR.value)
    m_viewer = EventMember(event_id=event.id, user_id=viewer.id, role=RoleType.VIEWER.value)
    db.add_all([m_organizer, m_manager, m_collab, m_vendor, m_viewer])
    db.commit()

    task_normal = Task(
        event_id=event.id,
        name="Stage Signage Setup",
        priority=TaskPriority.LOW.value,
        is_critical_path=False,
        slack_minutes=60,
    )
    task_critical = Task(
        event_id=event.id,
        name="Main Audio Engineering",
        priority=TaskPriority.CRITICAL.value,
        is_critical_path=True,
        slack_minutes=0,
    )
    vendor = Vendor(name="SoundMaster", category="sound", city="Boston")
    db.add_all([task_normal, task_critical, vendor])
    db.commit()

    return {
        "event": event,
        "organizer": organizer,
        "manager": manager,
        "collaborator": collaborator,
        "vendor_user": vendor_user,
        "viewer": viewer,
        "stranger": stranger,
        "task_normal": task_normal,
        "task_critical": task_critical,
        "vendor": vendor,
    }


def test_organizer_authorization(db_session: Session):
    """Main Organizer has broad execution permissions."""
    data = _setup_event_with_team(db_session)
    service = AuthorizationService(db_session)

    decision = service.authorize_action(
        event_id=data["event"].id,
        user_id=data["organizer"].id,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=data["task_normal"].id,
        payload={"new_vendor_id": data["vendor"].id, "agreed_cost": 500.0},
    )
    assert decision.allowed is True
    assert decision.requires_approval is False  # Organizer executes directly


def test_collaborator_action_requires_approval(db_session: Session):
    """Collaborator attempting a major or critical action requires approval."""
    data = _setup_event_with_team(db_session)
    service = AuthorizationService(db_session)

    # 1. Major action: Reassigning vendor -> requires approval
    decision = service.authorize_action(
        event_id=data["event"].id,
        user_id=data["collaborator"].id,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id=data["task_normal"].id,
        payload={"new_vendor_id": data["vendor"].id, "agreed_cost": 500.0},
    )
    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.impact_level == "MAJOR"

    # 2. Critical action: Changing critical path task -> requires approval with CRITICAL impact
    decision_crit = service.authorize_action(
        event_id=data["event"].id,
        user_id=data["collaborator"].id,
        action_type="REASSIGN_TASK",
        target_type="TASK",
        target_id=data["task_critical"].id,
        payload={"priority": "CRITICAL"},
    )
    assert decision_crit.allowed is True
    assert decision_crit.requires_approval is True
    assert decision_crit.impact_level == "CRITICAL"


def test_viewer_mutation_rejected(db_session: Session):
    """Viewer is read-only and prohibited from any state-changing mutations."""
    data = _setup_event_with_team(db_session)
    service = AuthorizationService(db_session)

    decision = service.authorize_action(
        event_id=data["event"].id,
        user_id=data["viewer"].id,
        action_type="REASSIGN_TASK",
        target_type="TASK",
        target_id=data["task_normal"].id,
    )
    assert decision.allowed is False
    assert "Viewers have read-only access" in decision.reason


def test_stranger_access_rejected(db_session: Session):
    """Users without event membership are rejected with ForbiddenException."""
    data = _setup_event_with_team(db_session)
    service = AuthorizationService(db_session)

    with pytest.raises(ForbiddenException) as exc:
        service.authorize_action(
            event_id=data["event"].id,
            user_id=data["stranger"].id,
            action_type="REASSIGN_TASK",
            target_type="TASK",
            target_id=data["task_normal"].id,
        )
    assert "not an authorized member" in str(exc.value)


def test_cross_event_target_rejection(db_session: Session):
    """Target belonging to another event is strictly rejected."""
    data = _setup_event_with_team(db_session)
    service = AuthorizationService(db_session)

    # Create another event and a foreign task
    other_event = Event(owner_id=data["organizer"].id, name="Other Event")
    db_session.add(other_event)
    db_session.commit()

    foreign_task = Task(event_id=other_event.id, name="Foreign Task")
    db_session.add(foreign_task)
    db_session.commit()

    # Attempting to target foreign task within event A must raise BadRequestException
    with pytest.raises(BadRequestException) as exc:
        service.authorize_action(
            event_id=data["event"].id,
            user_id=data["organizer"].id,
            action_type="REASSIGN_TASK",
            target_type="TASK",
            target_id=foreign_task.id,
        )
    assert "does not belong to event" in str(exc.value)


def test_vendor_scope_isolation(db_session: Session):
    """Vendors are restricted to assigned tasks and cannot touch budget or non-task entities."""
    data = _setup_event_with_team(db_session)
    service = AuthorizationService(db_session)

    # Vendor cannot execute budget adjustment
    decision = service.authorize_action(
        event_id=data["event"].id,
        user_id=data["vendor_user"].id,
        action_type="ADJUST_BUDGET",
        target_type="BUDGET",
        target_id="some-id",
        payload={"delta_amount": 100},
    )
    assert decision.allowed is False
    assert "Vendors are restricted" in decision.reason
