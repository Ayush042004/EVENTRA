"""Pydantic Schema: Task"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TaskBase(BaseModel):
    pass

class TaskResponse(TaskBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
