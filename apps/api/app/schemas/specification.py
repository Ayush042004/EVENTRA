"""Pydantic Schemas: Specification (Requirement, Constraint, Objective) & EventSpecification"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import RequirementType, ConstraintType, EventType, EventState
from app.domains.types import (
    ObjectivePriority,
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
)


# --- Phase 1: Entity CRUD Schemas ---
class RequirementBase(BaseModel):
    name: str
    type: str = RequirementType.GENERAL.value
    description: Optional[str] = None
    value: Optional[Dict[str, Any]] = None
    required: bool = True


class RequirementCreate(RequirementBase):
    pass


class RequirementResponse(RequirementBase):
    id: str
    event_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConstraintBase(BaseModel):
    name: str
    type: str = ConstraintType.GENERAL.value
    description: Optional[str] = None
    value: Optional[Dict[str, Any]] = None
    severity: str = "HARD"


class ConstraintCreate(ConstraintBase):
    pass


class ConstraintResponse(ConstraintBase):
    id: str
    event_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObjectiveBase(BaseModel):
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    priority: str = "HIGH"
    target_value: Optional[Dict[str, Any]] = None


class ObjectiveCreate(ObjectiveBase):
    pass


class ObjectiveResponse(ObjectiveBase):
    id: str
    event_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Phase 2: Normalized Event Specification Schemas ---
class ConstraintDefinition(BaseModel):
    """Operational constraint bounding the event plan."""
    constraint_type: str = Field(..., description="Constraint type, e.g. 'TIME_WINDOW', 'BUDGET_CAP', 'NOISE_CURFEW'")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Typed parameters governing the constraint")
    description: Optional[str] = Field(default="", description="Human-readable rationale or description")


class ObjectiveDefinition(BaseModel):
    """Operational business objective with priority ranking."""
    title: str = Field(..., description="Objective title, e.g. 'Start Keynote on Time'")
    priority: ObjectivePriority = Field(default=ObjectivePriority.MEDIUM, description="Priority classification")
    description: Optional[str] = Field(default="", description="Operational details")
    is_threatened: bool = Field(default=False, description="Flag indicates if objective is currently at risk")


class EventSpecification(BaseModel):
    """Normalized, deterministic Event Specification representing domain operational reality."""
    event_id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event name or title")
    description: Optional[str] = Field(default=None, description="Event description")
    event_type: EventType = Field(..., description="Resolved domain event type")
    status: Optional[str] = Field(default="DRAFT", description="Event lifecycle status")
    start_time: datetime = Field(..., description="Scheduled event start date and time")
    end_time: datetime = Field(..., description="Scheduled event end date and time")
    guest_count: int = Field(..., description="Scalar guest capacity requirement (NOT an attendee list)")
    total_budget: Optional[float] = Field(default=None, description="Total budget ceiling")
    currency: str = Field(default="USD", description="Currency code")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Venue or location metadata")

    # Domain Intelligence Baselines + Event Specific Additions
    requirements: List[RequirementDefinition] = Field(
        default_factory=list,
        description="Unified list of domain baseline and custom event requirements",
    )
    tasks: List[TaskDefinition] = Field(
        default_factory=list,
        description="Baseline operational tasks required for this event domain",
    )
    dependencies: List[DependencyDefinition] = Field(
        default_factory=list,
        description="Baseline task dependency DAG edges",
    )
    provider_categories: List[str] = Field(
        default_factory=list,
        description="Relevant vendor / provider operational categories",
    )
    constraints: List[ConstraintDefinition] = Field(
        default_factory=list,
        description="Hard and soft operational constraints",
    )
    objectives: List[ObjectiveDefinition] = Field(
        default_factory=list,
        description="Target business and event objectives",
    )
    custom_configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-specific custom configuration overrides",
    )
    created_at: Optional[datetime] = Field(default=None, description="Specification compilation timestamp")

    model_config = ConfigDict(from_attributes=True)


class EventSpecificationPreviewRequest(BaseModel):
    """Request payload for previewing an EventSpecification without database mutation."""
    event_id: Optional[str] = Field(default="preview-event-id", description="Optional mock or existing ID")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(default=None, description="Event description")
    event_type: str = Field(..., description="Domain event type: WEDDING, COLLEGE_FEST, or CONFERENCE")
    start_time: datetime = Field(..., description="Start datetime")
    end_time: datetime = Field(..., description="End datetime")
    guest_count: int = Field(..., description="Scalar guest count requirement")
    total_budget: Optional[float] = Field(default=None, description="Total budget amount")
    currency: Optional[str] = Field(default="USD", description="Currency code")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Location attributes")
    custom_requirements: Optional[List[RequirementDefinition]] = Field(default=None, description="Custom event requirements")
    constraints: Optional[List[ConstraintDefinition]] = Field(default=None, description="Custom constraints")
    objectives: Optional[List[ObjectiveDefinition]] = Field(default=None, description="Custom objectives")
    custom_configuration: Optional[Dict[str, Any]] = Field(default=None, description="Additional custom settings")
