"""Orchestrator: EventOperationsAgent (Single unified operations agent)."""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.agent.graph import EventOperationsAgentGraph
from app.agent.provider import LLMProvider, get_default_llm_provider


class EventOperationsAgent:
    """The single Event Operations Agent sitting above EVENTRA's deterministic backend.
    
    Orchestrates the operational loop:
    Observe -> Interpret -> Investigate -> Generate Options (Phase 8) ->
    Deterministic Validation -> Agent Selects -> Authorize (Phase 9) ->
    [Approval Gate] -> Execute (Phase 9) -> Verify (Phase 10) -> Reevaluate.
    """

    def __init__(self, db: Session, llm_provider: Optional[LLMProvider] = None):
        self.db = db
        self.llm_provider = llm_provider or get_default_llm_provider()
        self._graph_builder = EventOperationsAgentGraph()
        self.graph = self._graph_builder.build_graph()

    def run(
        self,
        event_id: str,
        message: str,
        user_id: str = "anonymous_operator",
        approval_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes an agent run across the live event graph.
        
        Args:
            event_id: The authoritative event ID
            message: Natural language report or command from operator
            user_id: Authenticated user ID (governs Phase 9 authorization)
            approval_id: Optional approval request ID for resuming approved actions
        
        Returns:
            Structured operational dictionary containing status, response message,
            incident details, impact, risk, recovery option, approval, execution,
            verification, and decision trace.
        """
        initial_state: AgentState = {
            "event_id": event_id,
            "user_id": user_id,
            "message": message,
            "current_event_state": None,
            "current_incidents": [],
            "active_incident_id": None,
            "impact": None,
            "risk": None,
            "recovery_options": [],
            "selected_option": None,
            "authorization_result": None,
            "approval_id": approval_id,
            "approval_result": None,
            "execution_result": None,
            "verification_result": None,
            "decision_trace": None,
            "messages": [{"role": "user", "content": message}],
            "next_action": None,
            "status": "INITIALIZED",
            "step_count": 0,
            "final_response": None,
            "error": None,
        }

        # Invoke LangGraph StateGraph with DB and LLM injected through configuration
        final_state: AgentState = self.graph.invoke(
            initial_state,
            config={"configurable": {"db": self.db, "llm_provider": self.llm_provider}},
        )

        return {
            "event_id": final_state.get("event_id"),
            "status": final_state.get("status"),
            "response": final_state.get("final_response"),
            "active_incident_id": final_state.get("active_incident_id"),
            "incident": (final_state.get("current_incidents") or [None])[0],
            "impact": final_state.get("impact"),
            "risk": final_state.get("risk"),
            "recovery_options": final_state.get("recovery_options"),
            "selected_option": final_state.get("selected_option"),
            "authorization": final_state.get("authorization_result"),
            "approval_id": final_state.get("approval_id"),
            "approval": final_state.get("approval_result"),
            "execution": final_state.get("execution_result"),
            "verification": final_state.get("verification_result"),
            "decision_trace": final_state.get("decision_trace"),
            "error": final_state.get("error"),
            "step_count": final_state.get("step_count"),
        }
