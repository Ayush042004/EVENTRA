"""Agent execution state schema."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class AgentState(BaseModel):
    event_id: str
    current_phase: str
    observations: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
