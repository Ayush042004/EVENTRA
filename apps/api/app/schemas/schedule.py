"""Pydantic Schemas: Schedule Engine Output"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskScheduleResponse(BaseModel):
    """Scheduled datetime assignment for a single task."""
    task_id: str
    task_name: Optional[str] = None
    planned_start: datetime
    planned_end: datetime
    duration_minutes: int
    slack_minutes: Optional[int] = None
    is_critical_path: bool = False


class CriticalPathResponse(BaseModel):
    """Critical path analysis response."""
    critical_path_tasks: List[str] = Field(default_factory=list)
    total_duration_minutes: int = 0


class ScheduleResponse(BaseModel):
    """Complete schedule output for an event."""
    event_id: str
    event_start: datetime
    event_end: datetime
    project_end: Optional[datetime] = None
    total_duration_minutes: int = 0
    is_feasible: bool = True
    buffer_minutes: int = 0
    entries: List[TaskScheduleResponse] = []
    critical_path: CriticalPathResponse = CriticalPathResponse()


class FeasibilityViolationResponse(BaseModel):
    """A schedule feasibility violation."""
    task_id: Optional[str] = None
    violation_type: str
    description: str


class FeasibilityResponse(BaseModel):
    """Schedule feasibility check response."""
    is_feasible: bool = True
    violations: List[FeasibilityViolationResponse] = []
    total_schedule_minutes: int = 0
    available_minutes: int = 0
    buffer_minutes: int = 0
