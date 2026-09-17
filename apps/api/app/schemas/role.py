"""Pydantic Schemas: Role and Permission"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PermissionResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: str
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []

    model_config = ConfigDict(from_attributes=True)
