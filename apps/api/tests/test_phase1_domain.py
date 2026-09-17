"""Phase 1 Domain Model Integrity and Verification Tests"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.event import Event
from app.models.event_member import EventMember
from app.models.role import Role
from app.models.permission import Permission
from app.models.requirement import Requirement
from app.models.constraint import Constraint
from app.models.objective import Objective
from app.models.task import Task
from app.models.dependency import TaskDependency
from app.models.resource import Resource
from app.models.budget import BudgetItem
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.enums import (
    EventType,
    EventState,
    TaskStatus,
    TaskPriority,
    RequirementType,
    ConstraintType,
    DependencyType,
    RoleType,
    PermissionCategory,
)
from app.services.event_service import EventService
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate
from app.schemas.event_member import EventMemberCreate
from app.schemas.task import TaskCreate, TaskDependencyCreate
from app.core.exceptions import ConflictException, BadRequestException, NotFoundException


def test_user_creation_and_unique_email(db_session: Session):
    """Verify user can be created and duplicate email is rejected by unique constraint."""
    user1 = User(name="Alice Smith", email="alice@example.com")
    db_session.add(user1)
    db_session.commit()
    assert user1.id is not None
    assert user1.email == "alice@example.com"

    # Attempt duplicate email insert directly in DB
    user2 = User(name="Alice Duplicate", email="alice@example.com")
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Verify service level handles conflict gracefully
    service = EventService(db_session)
    with pytest.raises(ConflictException):
        service.create_user(UserCreate(name="Alice Duplicate", email="alice@example.com"))


def test_event_ownership_and_relationship(db_session: Session):
    """Verify event belongs to a user and owner relationship loads correctly."""
    user = User(name="Organizer Bob", email="bob@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(
        owner_id=user.id,
        name="Global Tech Summit 2026",
        description="Flagship annual engineering conference",
        event_type=EventType.CONFERENCE.value,
        location="Grand Convention Center, Hall A",
        guest_count=500,
        state=EventState.NORMAL.value,
        total_budget=Decimal("75000.00"),
        currency="USD",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.owner is not None
    assert event.owner.id == user.id
    assert event.owner.name == "Organizer Bob"
    assert event in user.owned_events


def test_event_membership_and_duplicate_prevention(db_session: Session):
    """Verify event membership and unique constraint on (event_id, user_id)."""
    user = User(name="Member Charlie", email="charlie@example.com")
    organizer = User(name="Organizer Dave", email="dave@example.com")
    db_session.add_all([user, organizer])
    db_session.commit()

    event = Event(owner_id=organizer.id, name="Campus Spring Gala")
    db_session.add(event)
    db_session.commit()

    member1 = EventMember(
        event_id=event.id,
        user_id=user.id,
        role=RoleType.COLLABORATOR.value,
    )
    db_session.add(member1)
    db_session.commit()

    assert member1.id is not None
    assert member1.event.name == "Campus Spring Gala"
    assert member1.user.name == "Member Charlie"

    # Attempt duplicate membership for same user in same event
    member_duplicate = EventMember(
        event_id=event.id,
        user_id=user.id,
        role=RoleType.VIEWER.value,
    )
    db_session.add(member_duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Verify service level handles duplicate membership with ConflictException
    service = EventService(db_session)
    with pytest.raises(ConflictException):
        service.add_event_member(event.id, EventMemberCreate(user_id=user.id, role=RoleType.VIEWER.value))


def test_roles_and_permissions(db_session: Session):
    """Verify Role and Permission models and M2M role_permissions association."""
    perm_view = Permission(name="event:view", category=PermissionCategory.VIEW.value, description="View event state")
    perm_approve = Permission(name="recovery:approve", category=PermissionCategory.APPROVE.value, description="Approve recovery actions")
    role_organizer = Role(name=RoleType.MAIN_ORGANIZER.value, description="Full administrative owner")

    role_organizer.permissions.extend([perm_view, perm_approve])
    db_session.add_all([perm_view, perm_approve, role_organizer])
    db_session.commit()
    db_session.refresh(role_organizer)

    assert len(role_organizer.permissions) == 2
    assert "event:view" in [p.name for p in role_organizer.permissions]


def test_requirements_belong_to_event(db_session: Session):
    """Verify requirements are linked to parent event with structured value data."""
    user = User(name="Planner Eve", email="eve@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Corporate Annual Retreat")
    db_session.add(event)
    db_session.commit()

    req1 = Requirement(
        event_id=event.id,
        type=RequirementType.VENUE.value,
        name="Main Auditorium Capacity",
        value={"min_capacity": 300, "stage_required": True},
        required=True,
    )
    req2 = Requirement(
        event_id=event.id,
        type=RequirementType.CATERING.value,
        name="Vegetarian Lunch Buffet",
        value={"dietary": "vegetarian", "count": 250},
        required=True,
    )
    db_session.add_all([req1, req2])
    db_session.commit()
    db_session.refresh(event)

    assert len(event.requirements) == 2
    assert {r.type for r in event.requirements} == {RequirementType.VENUE.value, RequirementType.CATERING.value}


def test_constraints_belong_to_event(db_session: Session):
    """Verify event constraints with severity and structured data."""
    user = User(name="Planner Frank", email="frank@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="City Music Festival")
    db_session.add(event)
    db_session.commit()

    c1 = Constraint(
        event_id=event.id,
        type=ConstraintType.NOISE_CURFEW.value,
        name="Decibel limit after 10 PM",
        value={"max_decibels": 85, "curfew_time": "22:00"},
        severity="HARD",
    )
    c2 = Constraint(
        event_id=event.id,
        type=ConstraintType.BUDGET_CAP.value,
        name="Strict catering cap",
        value={"max_cost": 15000},
        severity="HARD",
    )
    db_session.add_all([c1, c2])
    db_session.commit()
    db_session.refresh(event)

    assert len(event.constraints) == 2
    assert all(c.severity == "HARD" for c in event.constraints)


def test_objectives_belong_to_event(db_session: Session):
    """Verify event objectives with priority and target values."""
    user = User(name="Organizer Grace", email="grace@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Tech Keynote 2026")
    db_session.add(event)
    db_session.commit()

    obj1 = Objective(
        event_id=event.id,
        type="TIMELINESS",
        name="Event must start on time",
        priority="CRITICAL",
        target_value={"target_start": "09:00:00"},
    )
    obj2 = Objective(
        event_id=event.id,
        type="FINANCIAL",
        name="Stay within budget",
        priority="HIGH",
        target_value={"max_variance_percent": 0.0},
    )
    db_session.add_all([obj1, obj2])
    db_session.commit()
    db_session.refresh(event)

    assert len(event.objectives) == 2
    critical_objs = [o for o in event.objectives if o.priority == "CRITICAL"]
    assert len(critical_objs) == 1
    assert critical_objs[0].name == "Event must start on time"


def test_task_creation_and_relationships(db_session: Session):
    """Verify task creation with lifecycle states and event relationship."""
    user = User(name="Manager Hank", email="hank@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Product Launch Gala")
    db_session.add(event)
    db_session.commit()

    task1 = Task(
        event_id=event.id,
        name="Stage and Lighting Rigging",
        description="Assemble central truss and connect DMX lighting lines",
        status=TaskStatus.READY.value,
        priority=TaskPriority.HIGH.value,
    )
    task2 = Task(
        event_id=event.id,
        name="Sound Check",
        description="Acoustic levels testing with live microphones",
        status=TaskStatus.PENDING.value,
        priority=TaskPriority.CRITICAL.value,
    )
    db_session.add_all([task1, task2])
    db_session.commit()
    db_session.refresh(event)

    assert len(event.tasks) == 2
    assert task1.event_id == event.id
    assert task1.event.name == "Product Launch Gala"


def test_task_dependency_integrity(db_session: Session):
    """Verify task dependency edges, rejection of self-dependencies, and duplicate edge rejection."""
    user = User(name="Planner Ivy", email="ivy@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Art Exhibition Opening")
    db_session.add(event)
    db_session.commit()

    task_a = Task(event_id=event.id, name="Install Display Walls")
    task_b = Task(event_id=event.id, name="Mount Paintings")
    db_session.add_all([task_a, task_b])
    db_session.commit()

    # Valid dependency: task_a must finish before task_b starts
    dep = TaskDependency(
        event_id=event.id,
        predecessor_task_id=task_a.id,
        successor_task_id=task_b.id,
        dependency_type=DependencyType.FINISH_TO_START.value,
    )
    db_session.add(dep)
    db_session.commit()
    db_session.refresh(task_a)
    db_session.refresh(task_b)

    assert len(task_a.outgoing_dependencies) == 1
    assert task_a.outgoing_dependencies[0].successor_task_id == task_b.id
    assert len(task_b.incoming_dependencies) == 1
    assert task_b.incoming_dependencies[0].predecessor_task_id == task_a.id

    # Self-dependency rejection in Python validation
    with pytest.raises(ValueError, match="Self-dependency detected"):
        TaskDependency(
            event_id=event.id,
            predecessor_task_id=task_a.id,
            successor_task_id=task_a.id,
        )

    # Duplicate dependency edge rejection in DB
    dup_dep = TaskDependency(
        event_id=event.id,
        predecessor_task_id=task_a.id,
        successor_task_id=task_b.id,
    )
    db_session.add(dup_dep)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Verify service-level rejection
    service = EventService(db_session)
    with pytest.raises(BadRequestException):
        service.create_dependency(event.id, TaskDependencyCreate(
            predecessor_task_id=task_a.id,
            successor_task_id=task_a.id,
        ))

    with pytest.raises(ConflictException):
        service.create_dependency(event.id, TaskDependencyCreate(
            predecessor_task_id=task_a.id,
            successor_task_id=task_b.id,
        ))


def test_resource_ownership(db_session: Session):
    """Verify resource creation and event ownership."""
    user = User(name="Manager Jack", email="jack@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Outdoor Sports Day")
    db_session.add(event)
    db_session.commit()

    res = Resource(
        event_id=event.id,
        name="Portable Diesel Generator 50kVA",
        type="EQUIPMENT",
        quantity=2,
        unit="unit",
        status="AVAILABLE",
    )
    db_session.add(res)
    db_session.commit()
    db_session.refresh(event)

    assert len(event.resources) == 1
    assert event.resources[0].name == "Portable Diesel Generator 50kVA"
    assert event.resources[0].quantity == 2


def test_budget_item_monetary_decimal_correctness(db_session: Session):
    """Verify budget items use Decimal/Numeric semantics without floating point distortion."""
    user = User(name="Treasurer Karen", email="karen@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Academic Symposium")
    db_session.add(event)
    db_session.commit()

    # Exact decimal amounts that commonly cause float representation error
    est_amount = Decimal("1999.99")
    act_amount = Decimal("2000.01")

    item = BudgetItem(
        event_id=event.id,
        name="Keynote Speaker Honorarium",
        category="SPEAKER",
        estimated_amount=est_amount,
        actual_amount=act_amount,
        currency="USD",
        status="COMMITTED",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert isinstance(item.estimated_amount, Decimal)
    assert isinstance(item.actual_amount, Decimal)
    assert item.estimated_amount == Decimal("1999.99")
    assert item.actual_amount == Decimal("2000.01")
    assert item.event.name == "Academic Symposium"


def test_vendor_assignment_relationships(db_session: Session):
    """Verify vendor assignment binds vendor and event correctly."""
    user = User(name="Producer Leo", email="leo@example.com")
    vendor = Vendor(name="SoundWave Pros", category="sound", city="Bengaluru")
    db_session.add_all([user, vendor])
    db_session.commit()

    event = Event(owner_id=user.id, name="Music Awards Gala")
    db_session.add(event)
    db_session.commit()

    assignment = VendorAssignment(
        event_id=event.id,
        vendor_id=vendor.id,
        category="sound",
        status="CONFIRMED",
        agreed_cost=4500.0,
        notes="Includes 2 sound engineers on site",
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(event)
    db_session.refresh(vendor)

    assert len(event.vendor_assignments) == 1
    assert event.vendor_assignments[0].vendor_id == vendor.id
    assert len(vendor.assignments) == 1
    assert vendor.assignments[0].event_id == event.id


def test_cascade_delete_integrity(db_session: Session):
    """Verify deleting an event cascades cleanly to sub-components without leaving orphans."""
    user = User(name="Organizer Mia", email="mia@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(owner_id=user.id, name="Temporary Demo Festival")
    db_session.add(event)
    db_session.commit()

    # Add child entities across domain types
    req = Requirement(event_id=event.id, name="Permit", type="PERMIT")
    constraint = Constraint(event_id=event.id, name="Curfew", type="TIME_WINDOW")
    obj = Objective(event_id=event.id, name="Success", priority="HIGH")
    task = Task(event_id=event.id, name="Setup Tent")
    res = Resource(event_id=event.id, name="Tent", type="FACILITY")
    budget = BudgetItem(event_id=event.id, name="Tent Rental", category="FACILITY")
    member = EventMember(event_id=event.id, user_id=user.id, role="COLLABORATOR")

    db_session.add_all([req, constraint, obj, task, res, budget, member])
    db_session.commit()

    event_id = event.id
    # Delete the event
    db_session.delete(event)
    db_session.commit()

    # Verify all child entities are removed
    assert db_session.query(Requirement).filter(Requirement.event_id == event_id).count() == 0
    assert db_session.query(Constraint).filter(Constraint.event_id == event_id).count() == 0
    assert db_session.query(Objective).filter(Objective.event_id == event_id).count() == 0
    assert db_session.query(Task).filter(Task.event_id == event_id).count() == 0
    assert db_session.query(Resource).filter(Resource.event_id == event_id).count() == 0
    assert db_session.query(BudgetItem).filter(BudgetItem.event_id == event_id).count() == 0
    assert db_session.query(EventMember).filter(EventMember.event_id == event_id).count() == 0

    # But the User itself remains alive
    assert db_session.query(User).filter(User.id == user.id).first() is not None
