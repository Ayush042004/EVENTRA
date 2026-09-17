"""Unit tests for Planning Engine components.

Verifies deterministic task generation, dependency building, resource planning,
budget distribution, and requirement interpretation across domains.
"""
from decimal import Decimal
import pytest

from datetime import datetime
from app.services.specification_service import SpecificationService
from app.engines.planning.task_generator import TaskGenerator
from app.engines.planning.dependency_builder import DependencyBuilder
from app.engines.planning.resource_planner import ResourcePlanner
from app.engines.planning.budget_planner import BudgetPlanner
from app.engines.planning.requirement_interpreter import RequirementInterpreter
from app.schemas.specification import EventSpecification


@pytest.fixture
def wedding_spec() -> EventSpecification:
    """Returns a valid EventSpecification for a wedding."""
    service = SpecificationService()
    return service.build_specification(event={
        "id": "evt-wedding-01",
        "name": "Wedding Celebration",
        "event_type": "WEDDING",
        "start_time": datetime(2026, 10, 15, 10, 0),
        "end_time": datetime(2026, 10, 15, 22, 0),
        "guest_count": 150,
        "total_budget": 50000.0,
        "currency": "USD",
        "location": {"address": "Banquet Hall"},
    })


@pytest.fixture
def conference_spec() -> EventSpecification:
    """Returns a valid EventSpecification for a conference."""
    service = SpecificationService()
    return service.build_specification(event={
        "id": "evt-conf-01",
        "name": "Tech Conference",
        "event_type": "CONFERENCE",
        "start_time": datetime(2026, 11, 1, 8, 0),
        "end_time": datetime(2026, 11, 1, 18, 0),
        "guest_count": 300,
        "total_budget": 80000.0,
        "currency": "USD",
        "location": {"address": "Convention Center"},
    })


@pytest.fixture
def fest_spec() -> EventSpecification:
    """Returns a valid EventSpecification for a college fest."""
    service = SpecificationService()
    return service.build_specification(event={
        "id": "evt-fest-01",
        "name": "Spring Fest",
        "event_type": "COLLEGE_FEST",
        "start_time": datetime(2026, 12, 5, 12, 0),
        "end_time": datetime(2026, 12, 5, 23, 0),
        "guest_count": 1000,
        "total_budget": 25000.0,
        "currency": "USD",
        "location": {"address": "Campus Grounds"},
    })


def test_task_generator_wedding(wedding_spec):
    """Test generating tasks from wedding specification."""
    generator = TaskGenerator()
    tasks = generator.generate_tasks(wedding_spec)

    assert len(tasks) > 0
    keys = {t["key"] for t in tasks}
    assert len(keys) == len(tasks), "Task keys must be unique"

    for task in tasks:
        assert task["status"] == "PENDING"
        assert task["name"]
        assert task["key"]
        assert "duration_minutes" in task
        assert "is_critical_path" in task
        assert task["phase"] in ("PRE_EVENT", "SETUP", "EXECUTION")


def test_task_generator_all_domains(wedding_spec, conference_spec, fest_spec):
    """Ensure task generation succeeds for all three supported domain specifications."""
    generator = TaskGenerator()
    for spec in (wedding_spec, conference_spec, fest_spec):
        tasks = generator.generate_tasks(spec)
        assert len(tasks) >= 3
        for t in tasks:
            assert isinstance(t["duration_minutes"], int)
            assert t["duration_minutes"] > 0


def test_dependency_builder_success(wedding_spec):
    """Test building dependencies with valid task key mapping."""
    builder = DependencyBuilder()
    key_to_id = {task.key: f"uuid-{i}" for i, task in enumerate(wedding_spec.tasks)}

    deps = builder.build_dependencies(wedding_spec, key_to_id)
    assert len(deps) == len(wedding_spec.dependencies)

    for dep in deps:
        assert dep["predecessor_task_id"].startswith("uuid-")
        assert dep["successor_task_id"].startswith("uuid-")
        assert dep["predecessor_task_id"] != dep["successor_task_id"]
        assert dep["dependency_type"] in ("FINISH_TO_START", "START_TO_START")
        assert dep["lag_minutes"] >= 0


def test_dependency_builder_missing_key(wedding_spec):
    """Test building dependencies raises ValueError when key is missing in map."""
    builder = DependencyBuilder()
    # Incomplete map
    key_to_id = {wedding_spec.tasks[0].key: "uuid-0"}

    if len(wedding_spec.dependencies) > 0:
        with pytest.raises(ValueError, match="not found in persisted tasks"):
            builder.build_dependencies(wedding_spec, key_to_id)


def test_resource_planner(wedding_spec):
    """Test resource generation from mandatory requirements."""
    planner = ResourcePlanner()
    resources = planner.plan_resources(wedding_spec)

    assert len(resources) > 0
    types = {r["type"] for r in resources}
    # Expected standard types
    assert types.issubset({"FACILITY", "EQUIPMENT", "MATERIAL", "STAFF", "TRANSPORT"})

    for res in resources:
        assert res["name"]
        assert res["status"] == "AVAILABLE"
        assert res["quantity"] >= 1
        assert res["unit"]


def test_budget_planner_proportional_distribution(wedding_spec):
    """Test budget items are generated for all provider categories plus contingency."""
    planner = BudgetPlanner()
    items = planner.plan_budget(wedding_spec)

    # Must contain item for each provider category + OPERATIONS (contingency)
    assert len(items) == len(wedding_spec.provider_categories) + 1
    categories = {item["category"] for item in items}
    assert "OPERATIONS" in categories

    for item in items:
        assert item["status"] == "PLANNED"
        assert item["actual_amount"] == Decimal("0.00")
        assert item["currency"] == wedding_spec.currency
        assert item["estimated_amount"] > Decimal("0.00")


def test_budget_planner_with_vendor_costs(wedding_spec):
    """Test budget planner uses known vendor costs when supplied."""
    planner = BudgetPlanner()
    known_costs = {wedding_spec.provider_categories[0]: Decimal("12500.00")}

    items = planner.plan_budget(wedding_spec, vendor_costs=known_costs)
    first_cat = wedding_spec.provider_categories[0].upper()

    matching = [it for it in items if it["category"] == first_cat]
    assert len(matching) == 1
    assert matching[0]["estimated_amount"] == Decimal("12500.00")


def test_requirement_interpreter(wedding_spec):
    """Test requirement interpreter validates satisfiable requirements."""
    interpreter = RequirementInterpreter()
    planner = ResourcePlanner()
    resources = planner.plan_resources(wedding_spec)

    unmet = interpreter.validate_requirements(wedding_spec, resources)
    assert isinstance(unmet, list)
    assert len(unmet) == 0, f"Expected 0 unmet requirements, got {unmet}"
