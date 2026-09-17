"""Pydantic Schema: Planning"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class PlanningBase(BaseModel):
    pass

class PlanningResponse(PlanningBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
