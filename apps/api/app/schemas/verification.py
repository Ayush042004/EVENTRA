"""Pydantic Schema: Verification"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class VerificationBase(BaseModel):
    pass

class VerificationResponse(VerificationBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
