"""API Routes: Operational Actions & Recovery Execution"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_current_user_id
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.recovery import Recovery
from app.services.authorization_service import AuthorizationService
from app.services.action_service import ActionService
from app.services.approval_service import ApprovalService
from app.schemas.action import (
    ActionRequest,
    ExecuteRecoveryRequest,
    ActionSubmissionResponse,
    AuthorizationDecisionResponse,
    ActionExecutionResponse,
)
from app.schemas.approval import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
)

router = APIRouter(prefix="/events", tags=["actions"])


@router.post(
    "/{event_id}/actions",
    response_model=ActionSubmissionResponse,
    status_code=status.HTTP_200_OK,
)
def submit_action(
    event_id: str,
    payload: ActionRequest,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
) -> ActionSubmissionResponse:
    """Submits an operational mutation. Evaluates authorization and either executes directly or routes to approval."""
    auth_service = AuthorizationService(db)
    decision = auth_service.authorize_action(
        event_id=event_id,
        user_id=current_user_id,
        action_type=payload.action_type,
        target_type=payload.target_type,
        target_id=payload.target_id,
        payload=payload.payload,
    )

    if not decision.allowed:
        raise ForbiddenException(decision.reason)

    decision_resp = AuthorizationDecisionResponse(
        allowed=decision.allowed,
        requires_approval=decision.requires_approval,
        reason=decision.reason,
        action_type=decision.action_type,
        impact_level=decision.impact_level,
        required_permission=decision.required_permission,
        required_role=decision.required_role,
        approval_policy=decision.approval_policy,
        event_id=event_id,
        target_id=payload.target_id,
    )

    # If policy requires approval, create an approval request
    if decision.requires_approval:
        approval_service = ApprovalService(db)
        approval = approval_service.create_request(
            event_id=event_id,
            requester_id=current_user_id,
            data=ApprovalRequestCreate(
                action_type=payload.action_type,
                target_type=payload.target_type,
                target_id=payload.target_id,
                requested_action=payload.payload,
            ),
        )
        decision_resp.approval_request_id = approval.id
        return ActionSubmissionResponse(
            decision=decision_resp,
            approval_request=ApprovalRequestResponse.model_validate(approval),
        )

    # Else policy permits direct execution
    action_service = ActionService(db)
    execution = action_service.execute_action(
        event_id=event_id,
        executor_id=current_user_id,
        action_type=payload.action_type,
        target_type=payload.target_type,
        target_id=payload.target_id,
        payload=payload.payload,
        action_id=payload.action_id,
    )
    return ActionSubmissionResponse(
        decision=decision_resp,
        execution=ActionExecutionResponse.model_validate(execution),
    )


@router.post(
    "/{event_id}/actions/execute-recovery",
    response_model=ActionSubmissionResponse,
    status_code=status.HTTP_200_OK,
)
def submit_recovery_execution(
    event_id: str,
    payload: ExecuteRecoveryRequest,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
) -> ActionSubmissionResponse:
    """Submits a Phase 8 recovery option for execution. Enforces authorization, concurrency, and approval rules."""
    recovery = (
        db.query(Recovery)
        .filter(Recovery.id == payload.recovery_option_id, Recovery.event_id == event_id)
        .first()
    )
    if not recovery:
        raise NotFoundException(f"Recovery option '{payload.recovery_option_id}' not found.")

    auth_service = AuthorizationService(db)
    decision = auth_service.authorize_action(
        event_id=event_id,
        user_id=current_user_id,
        action_type="REASSIGN_VENDOR",
        target_type="RECOVERY_OPTION",
        target_id=recovery.id,
        payload=recovery.proposed_changes,
        recovery_option_id=recovery.id,
    )

    if not decision.allowed:
        raise ForbiddenException(decision.reason)

    decision_resp = AuthorizationDecisionResponse(
        allowed=decision.allowed,
        requires_approval=decision.requires_approval,
        reason=decision.reason,
        action_type=f"RECOVERY_{recovery.strategy_type}",
        impact_level=decision.impact_level,
        required_permission=decision.required_permission,
        required_role=decision.required_role,
        approval_policy=decision.approval_policy,
        event_id=event_id,
        target_id=recovery.id,
    )

    if decision.requires_approval:
        approval_service = ApprovalService(db)
        approval = approval_service.create_request(
            event_id=event_id,
            requester_id=current_user_id,
            data=ApprovalRequestCreate(
                action_type=f"RECOVERY_{recovery.strategy_type}",
                target_type="RECOVERY_OPTION",
                target_id=recovery.id,
                requested_action=recovery.proposed_changes,
                recovery_option_id=recovery.id,
            ),
        )
        decision_resp.approval_request_id = approval.id
        return ActionSubmissionResponse(
            decision=decision_resp,
            approval_request=ApprovalRequestResponse.model_validate(approval),
        )

    # Direct execution
    action_service = ActionService(db)
    execution = action_service.execute_recovery_option(
        event_id=event_id,
        executor_id=current_user_id,
        recovery_option_id=recovery.id,
        action_id=payload.action_id,
    )
    return ActionSubmissionResponse(
        decision=decision_resp,
        execution=ActionExecutionResponse.model_validate(execution),
    )
