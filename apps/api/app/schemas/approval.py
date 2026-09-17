"""Pydantic Schema: Approval"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ApprovalBase(BaseModel):
    pass

class ApprovalResponse(ApprovalBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
