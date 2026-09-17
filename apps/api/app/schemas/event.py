"""Pydantic Schema: Event"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class EventBase(BaseModel):
    pass

class EventResponse(EventBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
