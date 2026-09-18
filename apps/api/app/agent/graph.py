"""LangGraph definition for the single Event Operations Agent."""
from typing import Any, Dict, List, Optional
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.provider import LLMProvider, MockLLMProvider, get_default_llm_provider
from app.agent.tools import (
    get_event_state,
    get_incidents,
    analyze_impact,
    calculate_risk,
    generate_recovery_options,
    validate_recovery_option,
    check_action_authorization,
    request_action_approval,
    check_approval_status,
    execute_action,
    verify_action,
    get_decision_trace,
)

MAX_AGENT_STEPS = 10


def _get_context(config: Optional[RunnableConfig]):
    configurable = (config or {}).get("configurable", {})
    db = configurable.get("db")
    llm = configurable.get("llm_provider") or get_default_llm_provider()
    return db, llm


def observe_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Retrieves authoritative current event state and open incidents from PostgreSQL."""
    db, _ = _get_context(config)
    event_id = state["event_id"]
    step_count = state.get("step_count", 0) + 1

    event_state = get_event_state(db, event_id)
    incidents = get_incidents(db, event_id)

    # Pick the most recent open incident as active incident if present
    active_incident_id = state.get("active_incident_id")
    if not active_incident_id and incidents:
        active_incident_id = incidents[0]["id"]

    return {
        "current_event_state": event_state,
        "current_incidents": incidents,
        "active_incident_id": active_incident_id,
        "status": "OBSERVING",
        "step_count": step_count,
    }


def interpret_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Interprets natural language report and operational context."""
    _, llm = _get_context(config)
    message = state.get("message", "")
    event_state = state.get("current_event_state") or {}
    incidents = state.get("current_incidents") or []

    interpretation = llm.interpret_incident(message, event_state, incidents)

    messages = list(state.get("messages", []))
    messages.append({
        "role": "agent",
        "type": "interpretation",
        "content": interpretation.get("summary", "Interpreted operational situation."),
    })

    return {
        "status": "INTERPRETING",
        "messages": messages,
    }


def investigate_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Investigates active incidents via deterministic impact and risk engines."""
    db, _ = _get_context(config)
    event_id = state["event_id"]
    incident_id = state.get("active_incident_id")

    if not incident_id:
        # No incident to investigate
        return {"status": "INVESTIGATING"}

    impact = analyze_impact(db, event_id, incident_id)
    risk = calculate_risk(db, event_id, incident_id)

    return {
        "impact": impact,
        "risk": risk,
        "status": "INVESTIGATING",
    }


def route_after_investigate(state: AgentState) -> str:
    """Routes to option generation if an incident requires recovery, else ends."""
    if not state.get("active_incident_id"):
        return "end_no_incident"
    return "generate_options"


def generate_options_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Calls Phase 8 deterministic RecoveryEngine to generate candidate recovery options."""
    db, _ = _get_context(config)
    event_id = state["event_id"]
    incident_id = state["active_incident_id"]
    user_id = state.get("user_id", "anonymous_operator")

    options = generate_recovery_options(db, event_id, incident_id, user_id)
    return {
        "recovery_options": options,
        "status": "OPTIONS_GENERATED",
    }


def validate_options_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Filters candidate options to ensure only deterministically feasible options proceed."""
    options = state.get("recovery_options") or []
    feasible_options = [opt for opt in options if opt.get("is_feasible", False)]

    return {
        "recovery_options": options,  # keep all with feasibility recorded
        "status": "OPTIONS_VALIDATED" if feasible_options else "NO_FEASIBLE_OPTIONS",
    }


def select_option_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Agent evaluates validated candidate options and selects the optimal option."""
    _, llm = _get_context(config)
    options = state.get("recovery_options") or []
    feasible = [opt for opt in options if opt.get("is_feasible", False)]

    if not feasible:
        return {
            "selected_option": None,
            "error": "No feasible recovery option identified by deterministic engine.",
            "status": "FAILED",
        }

    # Agent selects strategy
    selected_id = llm.select_recovery_strategy(
        feasible,
        {"incident_id": state.get("active_incident_id")},
        state.get("risk") or {},
    )

    selected = next((o for o in feasible if o["id"] == selected_id), feasible[0])

    return {
        "selected_option": selected,
        "status": "OPTION_SELECTED",
    }


def authorize_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Authorizes the selected action using Phase 9 AuthorizationService.
    
    IMPORTANT: pre_approved is NOT an authorization bypass.
    If approval is required, an authoritative approval record with status 'APPROVED'
    must exist in PostgreSQL for execution to proceed.
    """
    db, _ = _get_context(config)
    event_id = state["event_id"]
    user_id = state.get("user_id", "anonymous_operator")
    selected = state.get("selected_option")
    approval_id = state.get("approval_id")

    if not selected:
        return {
            "authorization_result": {"allowed": False, "reason": "No option selected."},
            "status": "FAILED",
        }

    strat = selected.get("strategy_type", "REASSIGN_VENDOR")
    action_type = "REASSIGN_VENDOR" if "VENDOR" in strat else "ADJUST_SCHEDULE"

    auth_result = check_action_authorization(
        db=db,
        event_id=event_id,
        user_id=user_id,
        action_type=action_type,
        target_type="TASK",
        target_id=selected.get("affected_tasks", [None])[0] if selected.get("affected_tasks") else None,
        payload=selected.get("proposed_changes"),
        recovery_option_id=selected.get("id"),
    )

    # Check if existing approval_id was passed and is authoritatively APPROVED in DB
    existing_approved = False
    approval_record = None
    if approval_id:
        try:
            approval_record = check_approval_status(db, approval_id)
            if approval_record.get("is_approved"):
                existing_approved = True
        except Exception:
            existing_approved = False

    return {
        "authorization_result": auth_result,
        "approval_result": approval_record,
        "status": "AUTHORIZED" if (auth_result.get("allowed") and (not auth_result.get("requires_approval") or existing_approved)) else "NEEDS_APPROVAL",
    }


def route_after_authorize(state: AgentState) -> str:
    """Routes based on authorization outcome and approval requirement."""
    auth = state.get("authorization_result") or {}
    if not auth.get("allowed"):
        return "end_failed"

    appr = state.get("approval_result") or {}
    if auth.get("requires_approval"):
        if appr.get("is_approved"):
            return "execute"
        return "request_approval"

    return "execute"


def request_approval_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Creates an immutable approval ticket through Phase 9 and terminates graph safely to PENDING_APPROVAL."""
    db, llm = _get_context(config)
    event_id = state["event_id"]
    user_id = state.get("user_id", "anonymous_operator")
    selected = state.get("selected_option") or {}
    strat = selected.get("strategy_type", "REASSIGN_VENDOR")
    action_type = "REASSIGN_VENDOR" if "VENDOR" in strat else "ADJUST_SCHEDULE"

    appr_dict = request_action_approval(
        db=db,
        event_id=event_id,
        user_id=user_id,
        action_type=action_type,
        target_type="TASK",
        target_id=selected.get("affected_tasks", [None])[0] if selected.get("affected_tasks") else None,
        requested_action=selected.get("proposed_changes") or {},
        recovery_option_id=selected.get("id"),
        notes=f"Agent requested approval for recovery strategy: {strat}",
    )

    context = {
        "incident": state.get("current_incidents", [{}])[0] if state.get("current_incidents") else {},
        "selected_option": selected,
        "risk": state.get("risk") or {},
        "approval": appr_dict,
    }
    response_msg = llm.format_operational_response("PENDING_APPROVAL", context)

    return {
        "approval_id": appr_dict["id"],
        "approval_result": appr_dict,
        "status": "PENDING_APPROVAL",
        "final_response": response_msg,
    }


def execute_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Executes the authorized recovery action via Phase 9 ActionService."""
    db, _ = _get_context(config)
    event_id = state["event_id"]
    user_id = state.get("user_id", "anonymous_operator")
    selected = state.get("selected_option") or {}
    recovery_id = selected.get("id")
    approval_id = state.get("approval_id")

    exec_result = execute_action(
        db=db,
        event_id=event_id,
        user_id=user_id,
        recovery_option_id=recovery_id,
        approval_request_id=approval_id,
    )

    return {
        "execution_result": exec_result,
        "status": "EXECUTED",
    }


def verify_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Calls Phase 10 VerificationService to authoritatively verify operational recovery."""
    db, _ = _get_context(config)
    event_id = state["event_id"]
    user_id = state.get("user_id", "anonymous_operator")
    exec_result = state.get("execution_result") or {}
    action_execution_id = exec_result.get("id") or exec_result.get("action_id")

    verification = verify_action(
        db=db,
        event_id=event_id,
        action_execution_id=action_execution_id,
        user_id=user_id,
    )

    decision_trace = get_decision_trace(db, event_id, verification.get("id"))

    return {
        "verification_result": verification,
        "decision_trace": decision_trace,
        "status": "VERIFIED",
    }


def reevaluate_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Re-evaluates post-verification state and composes final operational response."""
    _, llm = _get_context(config)
    verification = state.get("verification_result") or {}
    status_ver = verification.get("status", "FAILED")

    context = {
        "incident": state.get("current_incidents", [{}])[0] if state.get("current_incidents") else {},
        "selected_option": state.get("selected_option") or {},
        "risk": state.get("risk") or {},
        "verification": verification,
        "decision_trace": state.get("decision_trace"),
    }

    if status_ver in ("VERIFIED", "PARTIALLY_VERIFIED"):
        final_resp = llm.format_operational_response("COMPLETED", context)
        return {
            "status": "COMPLETED",
            "final_response": final_resp,
        }
    else:
        final_resp = llm.format_operational_response("FAILED", context)
        return {
            "status": "FAILED",
            "final_response": final_resp,
            "error": "Verification failed to confirm operational recovery.",
        }


def end_no_incident_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Terminal node when no active incident requires recovery."""
    event_state = state.get("current_event_state") or {}
    return {
        "status": "COMPLETED",
        "final_response": f"Event '{event_state.get('name', state['event_id'])}' is in state '{event_state.get('state', 'NORMAL')}'. No active incidents require recovery.",
    }


def end_failed_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Terminal node when authorization or option validation fails."""
    err = state.get("error") or state.get("authorization_result", {}).get("reason", "Action not authorized.")
    return {
        "status": "FAILED",
        "final_response": f"Operational action could not proceed: {err}",
        "error": err,
    }


class EventOperationsAgentGraph:
    """LangGraph definition for EVENTRA's single Event Operations Agent."""

    def __init__(self):
        self._compiled_graph = None

    def build_graph(self):
        """Constructs and compiles the StateGraph."""
        builder = StateGraph(AgentState)

        # 1. Register Nodes
        builder.add_node("observe", observe_node)
        builder.add_node("interpret", interpret_node)
        builder.add_node("investigate", investigate_node)
        builder.add_node("generate_options", generate_options_node)
        builder.add_node("validate_options", validate_options_node)
        builder.add_node("select_option", select_option_node)
        builder.add_node("authorize", authorize_node)
        builder.add_node("request_approval", request_approval_node)
        builder.add_node("execute", execute_node)
        builder.add_node("verify", verify_node)
        builder.add_node("reevaluate", reevaluate_node)
        builder.add_node("end_no_incident", end_no_incident_node)
        builder.add_node("end_failed", end_failed_node)

        # 2. Register Edges
        builder.add_edge(START, "observe")
        builder.add_edge("observe", "interpret")
        builder.add_edge("interpret", "investigate")

        builder.add_conditional_edges(
            "investigate",
            route_after_investigate,
            {
                "end_no_incident": "end_no_incident",
                "generate_options": "generate_options",
            },
        )

        builder.add_edge("generate_options", "validate_options")
        builder.add_edge("validate_options", "select_option")
        builder.add_edge("select_option", "authorize")

        builder.add_conditional_edges(
            "authorize",
            route_after_authorize,
            {
                "execute": "execute",
                "request_approval": "request_approval",
                "end_failed": "end_failed",
            },
        )

        builder.add_edge("request_approval", END)
        builder.add_edge("end_no_incident", END)
        builder.add_edge("end_failed", END)

        builder.add_edge("execute", "verify")
        builder.add_edge("verify", "reevaluate")
        builder.add_edge("reevaluate", END)

        self._compiled_graph = builder.compile()
        return self._compiled_graph

    def get_graph(self):
        if not self._compiled_graph:
            self.build_graph()
        return self._compiled_graph
