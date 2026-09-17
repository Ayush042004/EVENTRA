"""Unit tests for EventSpecification construction, validation, and determinism."""
import pytest
from datetime import datetime, timedelta
from app.services.specification_service import (
    SpecificationService,
    SpecificationValidationError,
)
from app.domains.types import (
    EventType,
    EventStatus,
    ObjectivePriority,
    RequirementDefinition,
)
from app.schemas.specification import (
    ConstraintDefinition,
    ObjectiveDefinition,
    EventSpecification,
)


@pytest.fixture
def service():
    return SpecificationService()


def test_build_wedding_specification(service):
    start = datetime(2026, 6, 20, 14, 0, 0)
    end = datetime(2026, 6, 20, 23, 0, 0)
    event_data = {
        "id": "event-wedding-1",
        "title": "Sarah & Alex Wedding",
        "event_type": "WEDDING",
        "start_time": start,
        "end_time": end,
        "guest_count": 180,
        "total_budget": 35000.0,
        "currency": "USD",
        "location": {"venue_name": "Sunset Winery", "city": "Napa Valley"},
    }

    spec = service.build_specification(event=event_data)

    assert isinstance(spec, EventSpecification)
    assert spec.event_id == "event-wedding-1"
    assert spec.title == "Sarah & Alex Wedding"
    assert spec.event_type == EventType.WEDDING
    assert spec.guest_count == 180
    assert spec.total_budget == 35000.0
    assert spec.location["venue_name"] == "Sunset Winery"

    # Verify baseline requirements, tasks, dependencies, provider categories
    assert len(spec.requirements) > 0
    assert len(spec.tasks) > 0
    assert len(spec.dependencies) > 0
    assert "CATERING" in spec.provider_categories
    assert "PHOTOGRAPHY" in spec.provider_categories


def test_build_specification_with_custom_requirements_override_and_addition(service):
    start = datetime(2026, 11, 10, 9, 0, 0)
    end = datetime(2026, 11, 10, 21, 0, 0)
    event_data = {
        "id": "event-wedding-custom",
        "title": "Minimal Wedding",
        "event_type": "WEDDING",
        "start_time": start,
        "end_time": end,
        "guest_count": 50,
    }

    # Override photography to NOT be mandatory, plus add custom drone light show
    custom_reqs = [
        RequirementDefinition(
            key="wedding.photography",
            category="PHOTOGRAPHY",
            name="Wedding Photography",
            is_mandatory=False,
            parameters={"photographers_count": 0},
        ),
        RequirementDefinition(
            key="custom.drone_show",
            category="ENTERTAINMENT",
            name="Drone Aerial Light Show",
            is_mandatory=True,
            parameters={"drone_count": 50},
        ),
    ]

    spec = service.build_specification(
        event=event_data,
        custom_requirements=custom_reqs,
    )

    req_by_key = {r.key: r for r in spec.requirements}

    # Verification of baseline override
    assert "wedding.photography" in req_by_key
    assert req_by_key["wedding.photography"].is_mandatory is False
    assert req_by_key["wedding.photography"].parameters["photographers_count"] == 0

    # Verification of custom addition
    assert "custom.drone_show" in req_by_key
    assert req_by_key["custom.drone_show"].is_mandatory is True
    assert req_by_key["custom.drone_show"].parameters["drone_count"] == 50


def test_build_specification_preserves_constraints_and_objectives(service):
    start = datetime(2026, 9, 15, 8, 0, 0)
    end = datetime(2026, 9, 15, 18, 0, 0)
    event_data = {
        "id": "event-conf-1",
        "title": "Global AI Summit",
        "event_type": "CONFERENCE",
        "start_time": start,
        "end_time": end,
        "guest_count": 500,
    }

    constraints = [
        ConstraintDefinition(
            constraint_type="TIME_WINDOW",
            parameters={"hard_curfew_time": "18:00:00"},
            description="Strict venue closure deadline",
        ),
        ConstraintDefinition(
            constraint_type="NOISE_CURFEW",
            parameters={"decibel_limit": 85},
            description="Civic acoustic ordinances",
        ),
    ]

    objectives = [
        ObjectiveDefinition(
            title="Start Keynote Presentation Precisely at 09:00",
            priority=ObjectivePriority.CRITICAL,
        ),
        ObjectiveDefinition(
            title="Provide 100% Wi-Fi uptime during live demos",
            priority=ObjectivePriority.HIGH,
        ),
    ]

    spec = service.build_specification(
        event=event_data,
        constraints=constraints,
        objectives=objectives,
    )

    assert len(spec.constraints) == 2
    assert spec.constraints[0].constraint_type == "TIME_WINDOW"
    assert spec.constraints[1].constraint_type == "NOISE_CURFEW"

    assert len(spec.objectives) == 2
    assert spec.objectives[0].title == "Start Keynote Presentation Precisely at 09:00"
    assert spec.objectives[0].priority == ObjectivePriority.CRITICAL


def test_invalid_dates_rejected(service):
    start = datetime(2026, 10, 10, 18, 0, 0)
    end = datetime(2026, 10, 10, 12, 0, 0)  # end before start
    event_data = {
        "id": "event-invalid-dates",
        "title": "Invalid Date Event",
        "event_type": "WEDDING",
        "start_time": start,
        "end_time": end,
        "guest_count": 100,
    }

    with pytest.raises(SpecificationValidationError) as exc_info:
        service.build_specification(event=event_data)
    assert "Logical date violation" in str(exc_info.value)


def test_negative_guest_count_rejected(service):
    start = datetime(2026, 10, 10, 10, 0, 0)
    end = datetime(2026, 10, 10, 18, 0, 0)
    event_data = {
        "id": "event-negative-guests",
        "title": "Negative Guests Event",
        "event_type": "WEDDING",
        "start_time": start,
        "end_time": end,
        "guest_count": -5,
    }

    with pytest.raises(SpecificationValidationError) as exc_info:
        service.build_specification(event=event_data)
    assert "Capacity requirement cannot be negative" in str(exc_info.value)


def test_unsupported_event_type_rejected(service):
    start = datetime(2026, 10, 10, 10, 0, 0)
    end = datetime(2026, 10, 10, 18, 0, 0)
    event_data = {
        "id": "event-unsupported",
        "title": "Unsupported Domain Event",
        "event_type": "GOLF_TOURNAMENT",
        "start_time": start,
        "end_time": end,
        "guest_count": 100,
    }

    with pytest.raises(SpecificationValidationError) as exc_info:
        service.build_specification(event=event_data)
    assert "Unsupported event type 'GOLF_TOURNAMENT'" in str(exc_info.value)


def test_specification_determinism(service):
    """Calling specification builder with identical input produces equivalent, deterministic output."""
    start = datetime(2026, 8, 15, 10, 0, 0)
    end = datetime(2026, 8, 15, 22, 0, 0)
    event_data = {
        "id": "event-determinism-check",
        "title": "College Tech Fest 2026",
        "event_type": "COLLEGE_FEST",
        "start_time": start,
        "end_time": end,
        "guest_count": 1200,
        "total_budget": 75000.0,
    }

    spec1 = service.build_specification(event=event_data)
    spec2 = service.build_specification(event=event_data)

    assert spec1.model_dump() == spec2.model_dump()


def test_validate_specification_standalone_success(service):
    start = datetime(2026, 8, 15, 10, 0, 0)
    end = datetime(2026, 8, 15, 22, 0, 0)
    spec = service.build_specification(event={
        "id": "event-valid",
        "title": "Valid Event",
        "event_type": "WEDDING",
        "start_time": start,
        "end_time": end,
        "guest_count": 100,
    })
    # Must pass without raising error
    service.validate_specification(spec)


def test_validate_specification_empty_title_fails(service):
    start = datetime(2026, 8, 15, 10, 0, 0)
    end = datetime(2026, 8, 15, 22, 0, 0)
    spec = service.build_specification(event={
        "id": "event-empty-title",
        "title": "Placeholder",
        "event_type": "WEDDING",
        "start_time": start,
        "end_time": end,
        "guest_count": 100,
    })
    spec.title = "   "
    with pytest.raises(SpecificationValidationError) as exc_info:
        service.validate_specification(spec)
    assert "non-empty 'title'" in str(exc_info.value)

