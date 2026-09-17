"""Pydantic Schema: Incident"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class IncidentBase(BaseModel):
    pass

class IncidentResponse(IncidentBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
