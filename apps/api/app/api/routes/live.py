"""API Route: Live State Engine Endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.services.live_state_service import LiveStateService
from app.schemas.live_state import (
    EventLiveState,
    GoLiveRequest,
    TaskStatusUpdate,
    ConcludeRequest,
)
from app.schemas.task import TaskResponse

router = APIRouter(prefix="/events", tags=["live"])


@router.post("/{event_id}/go-live", response_model=EventLiveState)
def go_live(
    event_id: str,
    payload: GoLiveRequest = GoLiveRequest(),
    db: Session = Depends(get_db_session),
) -> EventLiveState:
    """Transition an event from PLANNED to LIVE.

    Validates readiness preconditions, transitions lifecycle state,
    and activates initial tasks.
    """
    service = LiveStateService(db)
    return service.go_live(event_id, reason=payload.reason)


@router.get("/{event_id}/live-state", response_model=EventLiveState)
def get_live_state(
    event_id: str,
    db: Session = Depends(get_db_session),
) -> EventLiveState:
    """Get aggregated live operational state snapshot.

    Returns task progress, schedule deviations, budget variance,
    and overall event status.
    """
    service = LiveStateService(db)
    return service.get_live_state(event_id)


@router.put("/{event_id}/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    event_id: str,
    task_id: str,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db_session),
) -> TaskResponse:
    """Update a task's status during live event operations.

    Validates status transitions and propagates readiness to downstream tasks.
    """
    service = LiveStateService(db)
    task = service.update_task_status(
        event_id=event_id,
        task_id=task_id,
        new_status=payload.status,
        actual_start=payload.actual_start,
        actual_end=payload.actual_end,
    )
    return TaskResponse.model_validate(task)


@router.post("/{event_id}/conclude", response_model=EventLiveState)
def conclude_event(
    event_id: str,
    payload: ConcludeRequest = ConcludeRequest(),
    db: Session = Depends(get_db_session),
) -> EventLiveState:
    """Transition an event from LIVE to CONCLUDED.

    Validates that no tasks are in active status before concluding.
    """
    service = LiveStateService(db)
    service.conclude_event(event_id, reason=payload.reason)
    return service.get_live_state(event_id)
