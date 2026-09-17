"""Pydantic Schema: Risk"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class RiskBase(BaseModel):
    pass

class RiskResponse(RiskBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
