"""Unit tests for Event Specification Service and Determinism."""
from datetime import datetime, timedelta
import pytest
from app.models.enums import EventType, TaskPriority, DependencyType
from app.domains.types import RequirementDefinition, ObjectivePriority
from app.schemas.specification import (
    ConstraintDefinition,
    ObjectiveDefinition,
    EventSpecification,
)
from app.services.specification_service import (
    SpecificationService,
    SpecificationValidationError,
)
from app.models import Event, Requirement, Constraint, Objective
from app.models.enums import EventState, RequirementType, ConstraintType


def test_build_specification_for_wedding():
    """Verify building specification for Wedding produces valid normalized EventSpecification."""
    service = SpecificationService()
    start = datetime(2026, 10, 15, 12, 0, 0)
    end = datetime(2026, 10, 15, 23, 0, 0)

    event_payload = {
        "id": "evt-wedding-01",
        "title": "A & B Royal Wedding",
        "description": "Grand Celebration",
        "event_type": "WEDDING",
        "start_time": start,
        "end_time": end,
        "guest_count": 250,
        "total_budget": 50000.0,
        "currency": "USD",
        "location": {"venue": "Palace Grounds", "city": "Jaipur"},
    }

    spec = service.build_specification(event=event_payload)

    assert isinstance(spec, EventSpecification)
    assert spec.event_id == "evt-wedding-01"
    assert spec.title == "A & B Royal Wedding"
    assert spec.event_type == EventType.WEDDING
    assert spec.guest_count == 250
    assert spec.total_budget == 50000.0

    # Baseline elements populated
    assert len(spec.requirements) >= 8
    assert len(spec.tasks) >= 8
    assert len(spec.dependencies) >= 8
    assert "catering" in spec.provider_categories
    assert "photography" in spec.provider_categories


def test_build_specification_with_requirement_override_and_custom_addition():
    """Verify overriding a baseline requirement and adding a custom event-specific requirement."""
    service = SpecificationService()
    start = datetime(2026, 10, 15, 12, 0, 0)
    end = datetime(2026, 10, 15, 23, 0, 0)

    # 1. Override baseline requirement wedding.photography to non-mandatory
    override_req = RequirementDefinition(
        key="wedding.photography",
        category="PHOTOGRAPHY",
        name="Optional Drone Shoot",
        description="Couple opting out of traditional photography",
        is_mandatory=False,
        parameters={"drone_only": True},
    )

    # 2. Add novel custom requirement
    custom_req = RequirementDefinition(
        key="custom.fireworks",
        category="SPECIAL_EFFECTS",
        name="Midnight Fireworks Display",
        description="Synchronized musical fireworks finale",
        is_mandatory=True,
        parameters={"duration_minutes": 15},
    )

    spec = service.build_specification(
        event={
            "id": "evt-wedding-override",
            "title": "Custom Wedding",
            "event_type": EventType.WEDDING,
            "start_time": start,
            "end_time": end,
            "guest_count": 100,
        },
        custom_requirements=[override_req, custom_req],
    )

    req_map = {r.key: r for r in spec.requirements}
    assert "wedding.photography" in req_map
    assert req_map["wedding.photography"].is_mandatory is False
    assert req_map["wedding.photography"].parameters.get("drone_only") is True

    assert "custom.fireworks" in req_map
    assert req_map["custom.fireworks"].name == "Midnight Fireworks Display"
    assert req_map["custom.fireworks"].is_mandatory is True


def test_build_specification_preserves_constraints_and_objectives():
    """Verify custom constraints and objectives are properly structured and preserved."""
    service = SpecificationService()
    start = datetime(2026, 11, 20, 9, 0, 0)
    end = datetime(2026, 11, 20, 18, 0, 0)

    constraints = [
        ConstraintDefinition(
            constraint_type="NOISE_CURFEW",
            parameters={"max_decibels": 85, "curfew_time": "22:00"},
            description="Municipal noise ordinance",
        )
    ]

    objectives = [
        ObjectiveDefinition(
            title="Start Keynote on Time",
            priority=ObjectivePriority.CRITICAL,
            description="Broadcast begins promptly at 10:00 AM",
        )
    ]

    spec = service.build_specification(
        event={
            "id": "evt-conf-01",
            "title": "Global Tech Summit",
            "event_type": "CONFERENCE",
            "start_time": start,
            "end_time": end,
            "guest_count": 500,
        },
        constraints=constraints,
        objectives=objectives,
    )

    assert len(spec.constraints) == 1
    assert spec.constraints[0].constraint_type == "NOISE_CURFEW"
    assert spec.constraints[0].parameters["max_decibels"] == 85

    assert len(spec.objectives) == 1
    assert spec.objectives[0].title == "Start Keynote on Time"
    assert spec.objectives[0].priority == ObjectivePriority.CRITICAL


def test_validation_rejects_invalid_dates():
    """Verify end_time <= start_time raises SpecificationValidationError."""
    service = SpecificationService()
    start = datetime(2026, 10, 15, 18, 0, 0)
    end = datetime(2026, 10, 15, 12, 0, 0)  # Before start

    with pytest.raises(SpecificationValidationError) as exc_info:
        service.build_specification(
            event={
                "id": "bad-date-evt",
                "title": "Time Traveler Event",
                "event_type": "WEDDING",
                "start_time": start,
                "end_time": end,
                "guest_count": 50,
            }
        )

    assert "Logical date violation" in str(exc_info.value)


def test_validation_rejects_negative_guest_count():
    """Verify negative guest capacity is rejected."""
    service = SpecificationService()
    start = datetime(2026, 10, 15, 10, 0, 0)
    end = datetime(2026, 10, 15, 18, 0, 0)

    with pytest.raises(SpecificationValidationError) as exc_info:
        service.build_specification(
            event={
                "id": "negative-guests",
                "title": "Ghost Event",
                "event_type": "COLLEGE_FEST",
                "start_time": start,
                "end_time": end,
                "guest_count": -5,
            }
        )

    assert "Invalid guest count: -5" in str(exc_info.value)


def test_validation_rejects_unsupported_event_type():
    """Verify unsupported event type is rejected cleanly."""
    service = SpecificationService()
    start = datetime(2026, 10, 15, 10, 0, 0)
    end = datetime(2026, 10, 15, 18, 0, 0)

    with pytest.raises(SpecificationValidationError) as exc_info:
        service.build_specification(
            event={
                "id": "unknown-type-evt",
                "title": "Unknown Event",
                "event_type": "SECRET_GATHERING",
                "start_time": start,
                "end_time": end,
                "guest_count": 20,
            }
        )

    assert "Unsupported event type 'SECRET_GATHERING'" in str(exc_info.value)


def test_specification_determinism():
    """Verify calling build_specification multiple times with the exact same input produces identical output."""
    service = SpecificationService()
    start = datetime(2026, 11, 15, 9, 0, 0)
    end = datetime(2026, 11, 15, 23, 0, 0)

    payload = {
        "id": "fest-det-01",
        "title": "Deterministic College Fest",
        "description": "Annual Spring Fest",
        "event_type": "COLLEGE_FEST",
        "start_time": start,
        "end_time": end,
        "guest_count": 1200,
        "total_budget": 35000.0,
        "currency": "USD",
        "location": {"campus": "Main Quad"},
    }

    spec1 = service.build_specification(event=payload)
    spec2 = service.build_specification(event=payload)

    # Dictionaries must be identical
    dump1 = spec1.model_dump()
    dump2 = spec2.model_dump()
    assert dump1 == dump2


def test_orm_event_compatibility():
    """Verify building specification directly from a SQLAlchemy Event ORM entity."""
    service = SpecificationService()
    start = datetime(2026, 10, 1, 9, 0, 0)
    end = datetime(2026, 10, 1, 17, 0, 0)

    orm_event = Event(
        id="orm-conf-01",
        name="Enterprise Tech Conference",
        description="Annual developer keynote",
        event_type=EventType.CONFERENCE,
        state=EventState.NORMAL,
        start_datetime=start,
        end_datetime=end,
        guest_count=450,
        total_budget=80000.0,
        currency="USD",
        location="Silicon Valley Center",
    )

    # Attach relationship objects
    orm_event.requirements = [
        Requirement(
            id="req-101",
            event_id=orm_event.id,
            name="10Gbps Internet Fiber",
            type=RequirementType.VENUE.value,
            description="Dedicated redundant uplink",
            required=True,
            value={"bandwidth_gbps": 10},
        )
    ]
    orm_event.constraints = [
        Constraint(
            id="c-201",
            event_id=orm_event.id,
            name="Venue Curfew",
            type=ConstraintType.TIME_WINDOW.value,
            severity="HARD",
            value={"curfew_hour": 18},
        )
    ]
    orm_event.objectives = [
        Objective(
            id="o-301",
            event_id=orm_event.id,
            name="Zero Audio Dropout During Livestream",
            type="TECHNICAL",
            priority="CRITICAL",
        )
    ]

    spec = service.build_specification(event=orm_event)

    assert spec.event_id == "orm-conf-01"
    assert spec.title == "Enterprise Tech Conference"
    assert spec.event_type == EventType.CONFERENCE
    assert spec.guest_count == 450
    assert any(r.name == "10Gbps Internet Fiber" for r in spec.requirements)
    assert any(c.constraint_type == ConstraintType.TIME_WINDOW.value for c in spec.constraints)
    assert any(o.title == "Zero Audio Dropout During Livestream" for o in spec.objectives)
