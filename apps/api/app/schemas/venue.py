"""Pydantic Schema: Venue"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class VenueBase(BaseModel):
    pass

class VenueResponse(VenueBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
