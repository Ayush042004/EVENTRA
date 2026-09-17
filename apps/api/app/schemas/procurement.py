"""Pydantic Schema: Procurement"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProcurementBase(BaseModel):
    pass

class ProcurementResponse(ProcurementBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
