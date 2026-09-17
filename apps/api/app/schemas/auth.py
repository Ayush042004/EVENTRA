"""Pydantic Schema: Auth"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AuthBase(BaseModel):
    pass

class AuthResponse(AuthBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
