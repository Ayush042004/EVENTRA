"""Pydantic Schema: Setup"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SetupBase(BaseModel):
    pass

class SetupResponse(SetupBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
