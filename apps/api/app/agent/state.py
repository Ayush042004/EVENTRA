"""Agent execution state schema for LangGraph."""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Minimal typed state schema for the Event Operations Agent.
    
    The database remains the authoritative source of truth.
    AgentState carries only operational context and step outcomes.
    """
    event_id: str
    user_id: str
    message: str
    
    # Authoritative snapshots from deterministic backend
    current_event_state: Optional[Dict[str, Any]]
    current_incidents: List[Dict[str, Any]]
    active_incident_id: Optional[str]
    
    # Deterministic pipeline outputs
    impact: Optional[Dict[str, Any]]
    risk: Optional[Dict[str, Any]]
    recovery_options: List[Dict[str, Any]]
    selected_option: Optional[Dict[str, Any]]
    
    # Governance & Execution
    authorization_result: Optional[Dict[str, Any]]
    approval_id: Optional[str]
    approval_result: Optional[Dict[str, Any]]
    execution_result: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    decision_trace: Optional[Dict[str, Any]]
    
    # Provider Operations (communication, negotiation, confirmation)
    operational_intent: Optional[str]  # INCIDENT_RECOVERY, PROVIDER_CONTACT, PROVIDER_NEGOTIATION, etc.
    provider_operation_result: Optional[Dict[str, Any]]
    
    # LangGraph navigation & communication
    messages: List[Dict[str, Any]]
    next_action: Optional[str]
    status: str  # OBSERVING, INTERPRETING, INVESTIGATING, OPTIONS_GENERATED, PENDING_APPROVAL, EXECUTED, COMPLETED, FAILED
    step_count: int
    final_response: Optional[str]
    error: Optional[str]

