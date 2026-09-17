"""Pydantic Schemas: Live State Engine Output"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TaskProgress(BaseModel):
    """Per-task progress status."""
    task_id: str
    task_name: str
    key: Optional[str] = None
    status: str
    priority: str
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    is_critical_path: bool = False
    deviation_minutes: int = 0
    deviation_type: Optional[str] = None  # LATE_START, LATE_FINISH, EARLY_FINISH, ON_TIME


class ScheduleDeviationResponse(BaseModel):
    """Schedule deviation for a task."""
    task_id: str
    task_name: str
    deviation_type: str
    planned_value: Optional[datetime] = None
    actual_value: Optional[datetime] = None
    deviation_minutes: int = 0


class BudgetDeviationResponse(BaseModel):
    """Budget deviation summary."""
    total_budget: float = 0.0
    total_spent: float = 0.0
    total_estimated: float = 0.0
    variance: float = 0.0
    is_over_budget: bool = False


class EventLiveState(BaseModel):
    """Complete live operational state snapshot for an event."""
    event_id: str
    event_name: str
    event_type: str
    lifecycle_state: str
    task_summary: Dict[str, int] = Field(default_factory=dict)  # status -> count
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percent: float = 0.0
    task_progress: List[TaskProgress] = []
    schedule_deviations: List[ScheduleDeviationResponse] = []
    budget_deviation: Optional[BudgetDeviationResponse] = None


class GoLiveRequest(BaseModel):
    """Request payload for transitioning an event to LIVE."""
    reason: Optional[str] = Field(default="Event going live", description="Reason for transition")


class TaskStatusUpdate(BaseModel):
    """Request payload for updating task progress."""
    status: str
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None


class ConcludeRequest(BaseModel):
    """Request payload for concluding an event."""
    reason: Optional[str] = Field(default="Event concluded", description="Reason for conclusion")
