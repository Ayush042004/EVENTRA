"""API Route: Planning Engine Endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.services.planning_service import PlanningService
from app.schemas.planning import EventPlan

router = APIRouter(prefix="/events", tags=["planning"])


@router.post("/{event_id}/plan", response_model=EventPlan)
def generate_plan(
    event_id: str,
    db: Session = Depends(get_db_session),
) -> EventPlan:
    """Generate an operational plan from the event's specification.

    Materializes tasks, dependencies, resources, and budget items,
    then transitions the event lifecycle to PLANNED.
    """
    service = PlanningService(db)
    return service.generate_plan(event_id)


@router.get("/{event_id}/plan", response_model=EventPlan)
def get_plan(
    event_id: str,
    db: Session = Depends(get_db_session),
) -> EventPlan:
    """Retrieve the current operational plan for an event."""
    service = PlanningService(db)
    return service.get_plan(event_id)
