"""Pydantic Schemas: Incident, Impact, and Risk"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import IncidentType, IncidentStatus, IncidentSeverity


class IncidentBase(BaseModel):
    incident_type: IncidentType
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    source: str = Field(default="MANUAL", max_length=100)
    occurred_at: Optional[datetime] = None
    related_task_id: Optional[str] = None
    related_vendor_id: Optional[str] = None
    related_resource_id: Optional[str] = None
    related_venue_id: Optional[str] = None
    evidence_metadata: Optional[Dict[str, Any]] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    evidence_metadata: Optional[Dict[str, Any]] = None


class IncidentResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None


class ImpactResultResponse(BaseModel):
    incident_id: str
    directly_affected_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    indirectly_affected_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    blocked_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    affected_dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    dependency_depth: int = 0
    affected_resources: List[Dict[str, Any]] = Field(default_factory=list)
    affected_providers: List[Dict[str, Any]] = Field(default_factory=list)
    schedule_impact: Dict[str, Any] = Field(default_factory=dict)
    budget_impact: Dict[str, Any] = Field(default_factory=dict)
    affected_objectives: List[Dict[str, Any]] = Field(default_factory=list)
    affected_constraints: List[Dict[str, Any]] = Field(default_factory=list)
    severity: str
    generated_at: datetime


class RiskFactor(BaseModel):
    name: str
    score: float
    weight: float
    weighted_score: float
    description: str


class RiskResultResponse(BaseModel):
    incident_id: str
    score: float
    level: str
    factors: List[RiskFactor] = Field(default_factory=list)
    affected_objectives: List[str] = Field(default_factory=list)
    critical_constraints: List[str] = Field(default_factory=list)
    target_event_state: str
    calculated_at: datetime


class IncidentResponse(IncidentBase):
    id: str
    event_id: str
    status: str
    detected_at: datetime
    impact_result: Optional[Dict[str, Any]] = None
    risk_result: Optional[Dict[str, Any]] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    total: int
    items: List[IncidentResponse]
    limit: int
    offset: int
