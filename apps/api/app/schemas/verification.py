"""Pydantic Schemas: Verification"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class VerificationResultResponse(BaseModel):
    id: str
    event_id: str
    action_execution_id: Optional[str] = None
    recovery_option_id: Optional[str] = None
    status: str
    intended_outcome: Dict[str, Any] = Field(default_factory=dict)
    actual_outcome: Dict[str, Any] = Field(default_factory=dict)
    objective_results: List[Dict[str, Any]] = Field(default_factory=list)
    schedule_result: Dict[str, Any] = Field(default_factory=dict)
    budget_result: Dict[str, Any] = Field(default_factory=dict)
    resource_result: Dict[str, Any] = Field(default_factory=dict)
    provider_result: Dict[str, Any] = Field(default_factory=dict)
    venue_result: Dict[str, Any] = Field(default_factory=dict)
    constraint_result: Dict[str, Any] = Field(default_factory=dict)
    risk_before: Optional[str] = None
    risk_after: Optional[str] = None
    event_state_before: Optional[str] = None
    event_state_after: Optional[str] = None
    state_snapshot: str
    failure_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    verified_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationListResponse(BaseModel):
    total: int
    items: List[VerificationResultResponse]


class ReverifyRequest(BaseModel):
    reason: Optional[str] = "Operator-initiated re-verification"
