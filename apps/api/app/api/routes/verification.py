"""API Endpoints: Operational Verification"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_id, get_db_session
from app.schemas.verification import (
    ReverifyRequest,
    VerificationListResponse,
    VerificationResultResponse,
)
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/events/{event_id}", tags=["Verification"])


@router.post("/actions/{action_id}/verify", response_model=VerificationResultResponse, status_code=status.HTTP_201_CREATED)
def verify_action_endpoint(
    event_id: str,
    action_id: str,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Triggers deterministic post-action verification on an executed operational action."""
    service = VerificationService(db)
    result = service.verify_action(
        event_id=event_id,
        action_execution_id=action_id,
        current_user_id=current_user_id,
    )
    return result


@router.get("/verifications", response_model=VerificationListResponse)
def list_verifications_endpoint(
    event_id: str,
    status: Optional[str] = Query(None, description="Filter by verification status"),
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Lists verification records for an event."""
    service = VerificationService(db)
    items = service.list_verifications(
        event_id=event_id, current_user_id=current_user_id, status=status
    )
    return VerificationListResponse(total=len(items), items=items)


@router.get("/verifications/{verification_id}", response_model=VerificationResultResponse)
def get_verification_endpoint(
    event_id: str,
    verification_id: str,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Retrieves a single verification result by ID."""
    service = VerificationService(db)
    return service.get_verification(
        event_id=event_id,
        verification_id=verification_id,
        current_user_id=current_user_id,
    )


@router.post("/verifications/{verification_id}/reverify", response_model=VerificationResultResponse)
def reverify_endpoint(
    event_id: str,
    verification_id: str,
    payload: Optional[ReverifyRequest] = None,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Re-evaluates an existing verification against the latest authoritative state."""
    service = VerificationService(db)
    reason = payload.reason if payload else None
    return service.reverify(
        event_id=event_id,
        verification_id=verification_id,
        reason=reason,
        current_user_id=current_user_id,
    )
