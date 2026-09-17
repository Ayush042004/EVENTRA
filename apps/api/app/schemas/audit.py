"""Pydantic Schema: Audit"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AuditBase(BaseModel):
    pass

class AuditResponse(AuditBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
