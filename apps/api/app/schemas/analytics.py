"""Pydantic Schema: Analytics"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalyticsBase(BaseModel):
    pass

class AnalyticsResponse(AnalyticsBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
