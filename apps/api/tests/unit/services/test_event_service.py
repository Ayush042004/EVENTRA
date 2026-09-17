"""Unit Tests: EventService Persistence and Invariants"""
from decimal import Decimal
from sqlalchemy.orm import Session
from app.services.event_service import EventService
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate, EventUpdate
from app.schemas.specification import RequirementCreate, ConstraintCreate, ObjectiveCreate
from app.schemas.task import TaskCreate, TaskDependencyCreate
from app.schemas.resource import ResourceCreate
from app.schemas.budget import BudgetItemCreate


def test_event_service_crud_lifecycle(db_session: Session):
    """Test full foundational persistence lifecycle through EventService."""
    service = EventService(db_session)

    # 1. Create User
    user = service.create_user(UserCreate(name="Elena Rostova", email="elena@example.com"))
    assert user.id is not None
    assert service.get_user_by_email("elena@example.com").id == user.id

    # 2. Create Event
    event = service.create_event(EventCreate(
        owner_id=user.id,
        name="Autumn Symphony Gala",
        description="Classical music evening",
        guest_count=400,
        total_budget=Decimal("35000.00"),
    ))
    assert event.id is not None
    assert event.owner_id == user.id

    # 3. Update Event
    updated_event = service.update_event(event.id, EventUpdate(guest_count=450))
    assert updated_event.guest_count == 450

    # 4. Create Requirement
    req = service.create_requirement(event.id, RequirementCreate(
        name="Acoustic Shell",
        type="EQUIPMENT",
        value={"panels": 12},
    ))
    assert req.id is not None
    assert len(service.list_requirements(event.id)) == 1

    # 5. Create Constraint
    constraint = service.create_constraint(event.id, ConstraintCreate(
        name="Strict curfew",
        type="TIME_WINDOW",
        severity="HARD",
    ))
    assert constraint.id is not None
    assert len(service.list_constraints(event.id)) == 1

    # 6. Create Objective
    obj = service.create_objective(event.id, ObjectiveCreate(
        name="Zero acoustics distortion",
        priority="CRITICAL",
    ))
    assert obj.id is not None
    assert len(service.list_objectives(event.id)) == 1

    # 7. Create Tasks
    task1 = service.create_task(event.id, TaskCreate(name="Rig Acoustic Panels"))
    task2 = service.create_task(event.id, TaskCreate(name="Position Grand Piano"))
    assert len(service.list_tasks(event.id)) == 2

    # 8. Create Dependency
    dep = service.create_dependency(event.id, TaskDependencyCreate(
        predecessor_task_id=task1.id,
        successor_task_id=task2.id,
    ))
    assert dep.id is not None
    assert len(service.list_dependencies(event.id)) == 1

    # 9. Create Resource
    res = service.create_resource(event.id, ResourceCreate(
        name="Concert Grand Piano Steinway D",
        type="EQUIPMENT",
        quantity=1,
    ))
    assert res.id is not None
    assert len(service.list_resources(event.id)) == 1

    # 10. Create Budget Item
    budget_item = service.create_budget_item(event.id, BudgetItemCreate(
        name="Piano Rental & Tuning",
        category="EQUIPMENT",
        estimated_amount=Decimal("2500.00"),
        actual_amount=Decimal("2450.00"),
    ))
    assert budget_item.id is not None
    assert len(service.list_budget_items(event.id)) == 1
    assert service.list_budget_items(event.id)[0].actual_amount == Decimal("2450.00")
