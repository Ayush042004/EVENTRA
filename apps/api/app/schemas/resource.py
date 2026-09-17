"""Pydantic Schemas: Resource"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ResourceBase(BaseModel):
    name: str
    type: str
    quantity: int = 1
    unit: str = "item"
    status: str = "AVAILABLE"


class ResourceCreate(ResourceBase):
    pass


class ResourceResponse(ResourceBase):
    id: str
    event_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
