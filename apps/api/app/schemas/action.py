"""Pydantic Schemas: Action and Execution"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.approval import ApprovalRequestResponse


class ActionRequest(BaseModel):
    """Payload for submitting an operational action mutation."""
    action_id: Optional[str] = Field(None, description="Client-supplied idempotency key (UUID)")
    action_type: str = Field(..., description="Type of action: REASSIGN_VENDOR, REASSIGN_TASK, ADJUST_SCHEDULE, ALLOCATE_RESOURCE, ADJUST_BUDGET")
    target_type: str = Field(..., description="Target scope: TASK, VENDOR_ASSIGNMENT, RESOURCE, SCHEDULE, BUDGET, EVENT")
    target_id: Optional[str] = Field(None, description="Target entity ID within event")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action parameters and modification data")


class ExecuteRecoveryRequest(BaseModel):
    """Payload for submitting a Phase 8 recovery option for execution."""
    action_id: Optional[str] = Field(None, description="Client-supplied idempotency key (UUID)")
    recovery_option_id: str = Field(..., description="ID of the recovery option to execute")


class AuthorizationDecisionResponse(BaseModel):
    """Authoritative authorization and policy determination for an action."""
    allowed: bool
    requires_approval: bool
    reason: str
    action_type: str
    impact_level: str
    required_permission: str
    required_role: Optional[str] = None
    approval_policy: Optional[str] = None
    approval_request_id: Optional[str] = None
    event_id: str
    target_id: Optional[str] = None


class ActionExecutionResponse(BaseModel):
    """Result of an executed operational action."""
    id: str
    action_id: str
    event_id: str
    action_type: str
    status: str
    approval_request_id: Optional[str] = None
    recovery_option_id: Optional[str] = None
    executor_id: str
    affected_entities: List[Dict[str, Any]]
    before_version: str
    after_version: str
    failure_reason: Optional[str] = None
    execution_result_data: Dict[str, Any]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionSubmissionResponse(BaseModel):
    """Unified response when submitting an action via POST /actions."""
    decision: AuthorizationDecisionResponse
    execution: Optional[ActionExecutionResponse] = None
    approval_request: Optional[ApprovalRequestResponse] = None
