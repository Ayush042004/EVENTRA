"""Pydantic Schema: Notification"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class NotificationBase(BaseModel):
    pass

class NotificationResponse(NotificationBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
