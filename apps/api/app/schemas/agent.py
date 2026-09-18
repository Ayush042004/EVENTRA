"""Pydantic schemas for the Event Operations Agent API."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """Input payload to invoke the Event Operations Agent."""
    message: str = Field(..., min_length=1, description="Natural language operator report or directive")
    approval_id: Optional[str] = Field(None, description="Optional approval request ID for resuming approved actions")


class AgentRunResponse(BaseModel):
    """Authoritative structured output from the Event Operations Agent."""
    event_id: str
    status: str
    response: Optional[str] = None
    active_incident_id: Optional[str] = None
    incident: Optional[Dict[str, Any]] = None
    impact: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    recovery_options: Optional[List[Dict[str, Any]]] = None
    selected_option: Optional[Dict[str, Any]] = None
    authorization: Optional[Dict[str, Any]] = None
    approval_id: Optional[str] = None
    approval: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    decision_trace: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    step_count: Optional[int] = None
