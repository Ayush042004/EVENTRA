"""Public, fact-only contracts for deterministic recovery options."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RecoveryOptionResponse(BaseModel):
    id: str
    event_id: str
    incident_id: str
    strategy_type: str
    status: str
    is_feasible: bool
    is_stale: bool = False
    score: Optional[float] = None
    rank: Optional[int] = None
    affected_tasks: List[str] = Field(default_factory=list)
    affected_providers: List[str] = Field(default_factory=list)
    affected_resources: List[str] = Field(default_factory=list)
    proposed_changes: Dict[str, Any] = Field(default_factory=dict)
    schedule_delta: Dict[str, Any] = Field(default_factory=dict)
    budget_delta: Dict[str, Any] = Field(default_factory=dict)
    resource_delta: Dict[str, Any] = Field(default_factory=dict)
    provider_delta: Dict[str, Any] = Field(default_factory=dict)
    objective_delta: Dict[str, Any] = Field(default_factory=dict)
    constraint_impact: Dict[str, Any] = Field(default_factory=dict)
    risk_before: Dict[str, Any] = Field(default_factory=dict)
    risk_after: Dict[str, Any] = Field(default_factory=dict)
    feasibility_result: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecoveryOptionListResponse(BaseModel):
    incident_id: str
    state_snapshot: str
    items: List[RecoveryOptionResponse] = Field(default_factory=list)


RecoveryResponse = RecoveryOptionResponse
