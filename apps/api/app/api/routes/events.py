"""API Route: Events (Phase 1 Foundational Endpoints + Phase 2 Specification Preview)"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_current_user_id
from app.services.event_service import EventService
from app.services.collaboration_service import CollaborationService
from app.services.specification_service import (
    SpecificationService,
    SpecificationValidationError,
)
from app.schemas.event import EventCreate, EventResponse
from app.schemas.event_member import EventMemberCreate, EventMemberUpdate, EventMemberResponse
from app.schemas.specification import (
    EventSpecification,
    EventSpecificationPreviewRequest,
)
from app.core.exceptions import NotFoundException, BadRequestException

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


# --- Phase 2: Specification Endpoints ---
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
        raise BadRequestException(str(err))


@router.get("/{event_id}/specification", response_model=EventSpecification)
def get_event_specification(
    event_id: str,
    db: Session = Depends(get_db_session),
) -> EventSpecification:
    """Retrieve the deterministic EventSpecification for an existing or demo event."""
    spec_service = SpecificationService(db)

    # 1. Check database first
    event_service = EventService(db)
    db_event = event_service.get_event(event_id)
    if db_event:
        try:
            return spec_service.build_specification(event=db_event)
        except SpecificationValidationError as err:
            raise BadRequestException(str(err))

    # 2. Check demo events store
    demo_event = DEMO_EVENTS.get(event_id)
    if demo_event:
        try:
            return spec_service.build_specification(event=demo_event)
        except SpecificationValidationError as err:
            raise BadRequestException(str(err))

    raise NotFoundException(f"Event with id '{event_id}' not found.")


# --- Phase 1: Foundational Event Endpoints ---
@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db_session),
):
    """Creates a new event with authoritative user ownership."""
    service = EventService(db)
    event = service.create_event(payload)
    return event


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    db: Session = Depends(get_db_session),
):
    """Retrieves an event by its unique ID."""
    service = EventService(db)
    event = service.get_event(event_id)
    if not event:
        raise NotFoundException(f"Event with id '{event_id}' not found.")
    return event


@router.post("/{event_id}/members", response_model=EventMemberResponse, status_code=status.HTTP_201_CREATED)
def add_event_member(
    event_id: str,
    payload: EventMemberCreate,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Adds a collaborator or member to the event with role authorization."""
    service = CollaborationService(db)
    member = service.add_member(event_id, payload, current_user_id=current_user_id)
    return member


@router.get("/{event_id}/members", response_model=List[EventMemberResponse])
def list_event_members(
    event_id: str,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Lists all members/collaborators for an event."""
    service = CollaborationService(db)
    return service.list_members(event_id, current_user_id=current_user_id)


@router.patch("/{event_id}/members/{member_id}", response_model=EventMemberResponse)
def update_event_member(
    event_id: str,
    member_id: str,
    payload: EventMemberUpdate,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Updates an event member's role (Organizers only)."""
    service = CollaborationService(db)
    return service.update_member_role(event_id, member_id, payload, current_user_id=current_user_id)


@router.delete("/{event_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event_member(
    event_id: str,
    member_id: str,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Removes a member from the event (Organizers only)."""
    service = CollaborationService(db)
    service.remove_member(event_id, member_id, current_user_id=current_user_id)
    return None
