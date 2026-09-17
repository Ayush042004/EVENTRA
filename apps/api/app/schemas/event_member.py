"""Pydantic Schemas: EventMember"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import RoleType


class EventMemberBase(BaseModel):
    role: str = RoleType.COLLABORATOR.value
    role_id: Optional[str] = None


class EventMemberCreate(EventMemberBase):
    user_id: str


class EventMemberResponse(EventMemberBase):
    id: str
    event_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
