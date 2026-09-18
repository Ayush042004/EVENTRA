"""Inspection and recalculation APIs for non-executing recovery options."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_id, get_db_session
from app.schemas.recovery import RecoveryOptionListResponse, RecoveryOptionResponse
from app.services.recovery_service import RecoveryService

router = APIRouter(prefix="/events", tags=["recovery"])


def _response(option):
    data = RecoveryOptionResponse.model_validate(option).model_dump()
    data["is_stale"] = getattr(option, "_is_stale", option.status == "STALE")
    return RecoveryOptionResponse(**data)


@router.post("/{event_id}/incidents/{incident_id}/recovery/options", response_model=RecoveryOptionListResponse, status_code=status.HTTP_201_CREATED)
def generate_options(event_id: str, incident_id: str, db: Session = Depends(get_db_session), current_user_id: str = Depends(get_current_user_id)):
    service = RecoveryService(db)
    options = service.generate_recovery_options(event_id, incident_id, current_user_id)
    snapshot = options[0].state_snapshot if options else service._build_context(event_id, incident_id, current_user_id).snapshot_version
    return RecoveryOptionListResponse(incident_id=incident_id, state_snapshot=snapshot, items=[_response(item) for item in options])


@router.get("/{event_id}/incidents/{incident_id}/recovery/options", response_model=RecoveryOptionListResponse)
def list_options(event_id: str, incident_id: str, db: Session = Depends(get_db_session), current_user_id: str = Depends(get_current_user_id)):
    service = RecoveryService(db)
    options = service.list_recovery_options(event_id, incident_id, current_user_id)
    snapshot = service._build_context(event_id, incident_id, current_user_id).snapshot_version
    return RecoveryOptionListResponse(incident_id=incident_id, state_snapshot=snapshot, items=[_response(item) for item in options])


@router.post("/{event_id}/incidents/{incident_id}/recovery/recalculate", response_model=RecoveryOptionListResponse)
def recalculate_options(event_id: str, incident_id: str, db: Session = Depends(get_db_session), current_user_id: str = Depends(get_current_user_id)):
    service = RecoveryService(db)
    options = service.recalculate_options(event_id, incident_id, current_user_id)
    snapshot = options[0].state_snapshot if options else service._build_context(event_id, incident_id, current_user_id).snapshot_version
    return RecoveryOptionListResponse(incident_id=incident_id, state_snapshot=snapshot, items=[_response(item) for item in options])


@router.get("/{event_id}/incidents/{incident_id}/recovery/options/{option_id}", response_model=RecoveryOptionResponse)
def get_option(event_id: str, incident_id: str, option_id: str, db: Session = Depends(get_db_session), current_user_id: str = Depends(get_current_user_id)):
    return _response(RecoveryService(db).get_recovery_option(event_id, incident_id, option_id, current_user_id))
