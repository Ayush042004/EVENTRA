"""Pydantic Schema: Recovery"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class RecoveryBase(BaseModel):
    pass

class RecoveryResponse(RecoveryBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
