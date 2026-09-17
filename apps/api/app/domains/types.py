"""Domain layer typed data structures and enum definitions."""
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Supported event domain types."""
    WEDDING = "WEDDING"
    COLLEGE_FEST = "COLLEGE_FEST"
    CONFERENCE = "CONFERENCE"


class DependencyType(str, Enum):
    """Temporal and operational task dependency types."""
    FINISH_TO_START = "FINISH_TO_START"
    START_TO_START = "START_TO_START"


class ObjectivePriority(str, Enum):
    """Operational priority for constraints and objectives."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    FLEXIBLE = "FLEXIBLE"


class EventStatus(str, Enum):
    """Canonical event lifecycle status."""
    DRAFT = "DRAFT"
    SPECIFIED = "SPECIFIED"
    PLANNED = "PLANNED"
    LIVE = "LIVE"
    INCIDENT = "INCIDENT"
    EMERGENCY = "EMERGENCY"
    CONCLUDED = "CONCLUDED"
    CANCELLED = "CANCELLED"


class RequirementDefinition(BaseModel):
    """Structured domain requirement specification."""
    key: str = Field(..., description="Unique stable key for the requirement, e.g. 'catering', 'venue'")
    category: str = Field(..., description="Operational category, e.g. 'CATERING', 'VENUE', 'AV_LIGHTING'")
    name: str = Field(..., description="Human-readable title of requirement")
    description: str = Field(default="", description="Operational explanation")
    is_mandatory: bool = Field(default=True, description="Whether this requirement is strictly required")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Domain configuration attributes")


class TaskDefinition(BaseModel):
    """Structured baseline task definition for downstream planning."""
    key: str = Field(..., description="Stable task identifier, e.g. 'wedding.venue_prep'")
    name: str = Field(..., description="Human-readable task name")
    description: str = Field(default="", description="Operational details of the task")
    priority: ObjectivePriority = Field(default=ObjectivePriority.MEDIUM, description="Operational priority")
    phase: str = Field(default="SETUP", description="Operational phase, e.g. 'PRE_EVENT', 'SETUP', 'EXECUTION'")
    required_provider_category: Optional[str] = Field(default=None, description="Matching vendor category")
    is_critical: bool = Field(default=False, description="Whether task is on the operational critical path")
    estimated_duration_minutes: Optional[int] = Field(default=None, description="Nominal relative duration hint in minutes")


class DependencyDefinition(BaseModel):
    """Structured task dependency definition referencing stable task keys."""
    predecessor_key: str = Field(..., description="Stable key of the predecessor task")
    successor_key: str = Field(..., description="Stable key of the successor task")
    dependency_type: DependencyType = Field(default=DependencyType.FINISH_TO_START, description="Dependency relationship")
    lag_minutes: int = Field(default=0, description="Lag or buffer time in minutes between tasks")


class ProviderCategoryDefinition(BaseModel):
    """Structured provider/vendor category representation."""
    category: str = Field(..., description="Canonical category code, e.g. 'CATERING'")
    name: str = Field(..., description="Human-readable display name")
    description: str = Field(default="", description="Category scope and capabilities")
    is_required: bool = Field(default=True, description="Whether category is normally mandatory for the domain")
