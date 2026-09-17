"""API Route: Events (Phase 1 Foundational Endpoints)"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db_session
from app.services.event_service import EventService
from app.schemas.event import EventCreate, EventResponse
from app.schemas.event_member import EventMemberCreate, EventMemberResponse
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/events", tags=["events"])


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
):
    """Adds a collaborator or member to the event."""
    service = EventService(db)
    member = service.add_event_member(event_id, payload)
    return member


@router.get("/{event_id}/members", response_model=List[EventMemberResponse])
def list_event_members(
    event_id: str,
    db: Session = Depends(get_db_session),
):
    """Lists all members/collaborators for an event."""
    service = EventService(db)
    event = service.get_event(event_id)
    if not event:
        raise NotFoundException(f"Event with id '{event_id}' not found.")
    return service.get_event_members(event_id)
