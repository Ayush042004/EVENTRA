"""Pydantic Schemas: Specification (Requirement, Constraint, Objective)"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.enums import RequirementType, ConstraintType


# --- Requirement Schemas ---
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


# --- Constraint Schemas ---
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


# --- Objective Schemas ---
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
