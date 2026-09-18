"""Pydantic Schemas: Approval / ApprovalRequest"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ApprovalRequestCreate(BaseModel):
    """Payload for requesting operational approval."""
    action_type: str = Field(..., description="Action type, e.g. REASSIGN_VENDOR, ADJUST_SCHEDULE")
    target_type: str = Field(..., description="Target entity type, e.g. TASK, VENDOR_ASSIGNMENT")
    target_id: Optional[str] = Field(None, description="Target entity ID within event")
    requested_action: Dict[str, Any] = Field(default_factory=dict, description="Immutable action parameters")
    recovery_option_id: Optional[str] = Field(None, description="Optional associated recovery option ID")
    notes: Optional[str] = Field(None, description="Context or justification for approval")


class ApprovalDecisionRequest(BaseModel):
    """Payload when approving an approval request."""
    decision_notes: Optional[str] = Field(None, description="Optional notes or rationale from approver")


class ApprovalRejectionRequest(BaseModel):
    """Payload when rejecting an approval request."""
    reason: str = Field(..., min_length=1, description="Mandatory rejection reason")


class ApprovalRequestResponse(BaseModel):
    """Authoritative representation of an approval request."""
    id: str
    event_id: str
    requester_id: str
    approver_id: Optional[str] = None
    action_type: str
    target_type: str
    target_id: Optional[str] = None
    impact_level: str
    requested_action: Dict[str, Any]
    recovery_option_id: Optional[str] = None
    status: str
    state_snapshot: str
    rejection_reason: Optional[str] = None
    decision_notes: Optional[str] = None
    decided_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequestListResponse(BaseModel):
    """Paginated list of approval requests."""
    total: int
    items: List[ApprovalRequestResponse]
    limit: int
    offset: int
