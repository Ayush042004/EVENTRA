"""API Route: Events and Event Specification preview."""
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from app.schemas.specification import (
    EventSpecification,
    EventSpecificationPreviewRequest,
)
from app.services.specification_service import (
    SpecificationService,
    SpecificationValidationError,
)

router = APIRouter(prefix="/events", tags=["events"])

# Seed / Demo in-memory lookup for deterministic previewing
DEMO_EVENTS: Dict[str, Dict[str, Any]] = {
    "wedding_demo": {
        "id": "wedding_demo",
        "title": "Demo Wedding",
        "description": "Deterministic baseline demo wedding",
        "event_type": "WEDDING",
        "start_time": datetime(2026, 10, 10, 10, 0, 0),
        "end_time": datetime(2026, 10, 10, 22, 0, 0),
        "guest_count": 150,
        "total_budget": 25000.0,
        "currency": "USD",
        "location": {"name": "Grand Horizon Hall", "city": "San Francisco"},
    },
    "college_fest_demo": {
        "id": "college_fest_demo",
        "title": "Demo College Fest",
        "description": "Deterministic baseline demo college fest",
        "event_type": "COLLEGE_FEST",
        "start_time": datetime(2026, 11, 15, 9, 0, 0),
        "end_time": datetime(2026, 11, 15, 23, 0, 0),
        "guest_count": 800,
        "total_budget": 50000.0,
        "currency": "USD",
        "location": {"name": "North Campus Quad", "city": "Boston"},
    },
    "conference_demo": {
        "id": "conference_demo",
        "title": "Demo Tech Conference",
        "description": "Deterministic baseline demo tech conference",
        "event_type": "CONFERENCE",
        "start_time": datetime(2026, 12, 1, 8, 0, 0),
        "end_time": datetime(2026, 12, 1, 18, 0, 0),
        "guest_count": 300,
        "total_budget": 40000.0,
        "currency": "USD",
        "location": {"name": "Civic Convention Hall", "city": "Seattle"},
    },
}


@router.get("/")
def get_events_root():
    return {"status": "ok", "resource": "events"}


@router.post("/specification/preview", response_model=EventSpecification)
def preview_event_specification(
    payload: EventSpecificationPreviewRequest,
) -> EventSpecification:
    """Build and preview an EventSpecification deterministically without persistence."""
    service = SpecificationService()
    try:
        spec = service.build_specification(
            event=payload.model_dump(),
            custom_requirements=payload.custom_requirements,
            constraints=payload.constraints,
            objectives=payload.objectives,
            custom_configuration=payload.custom_configuration,
        )
        return spec
    except SpecificationValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.get("/{event_id}/specification", response_model=EventSpecification)
def get_event_specification(
    event_id: str,
) -> EventSpecification:
    """Retrieve the deterministic EventSpecification for an existing or demo event."""
    # Check demo store first
    event_data = DEMO_EVENTS.get(event_id)

    if not event_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id '{event_id}' not found",
        )

    service = SpecificationService()
    try:
        spec = service.build_specification(event=event_data)
        return spec
    except SpecificationValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
