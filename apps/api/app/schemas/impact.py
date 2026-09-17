"""Pydantic Schema: Impact"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ImpactBase(BaseModel):
    pass

class ImpactResponse(ImpactBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
