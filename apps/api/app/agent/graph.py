"""LangGraph definition for the single Event Operations Agent.

Supports both incident recovery AND provider communication/negotiation workflows.
The agent interprets operational intent and routes accordingly:
- Incident/recovery → existing observe→investigate→options→authorize→execute→verify flow
- Provider operations → provider_operations_node using communication tools
"""
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
    contact_provider,
    negotiate_with_provider,
    request_provider_approval,
    confirm_provider_engagement,
    simulate_provider_response,
    get_provider_negotiation_history,
    start_autonomous_operations,
    modify_event_plan,
)

MAX_AGENT_STEPS = 10

# --- Intent keywords for routing ---
PROVIDER_KEYWORDS = [
    "provider", "vendor", "contact", "negotiate", "quotation", "quote", "engagement",
    "photographer", "caterer", "catering", "dj", "sound", "lighting", "decor",
    "decorator", "florist", "videographer", "confirm provider", "assign provider",
    "approval", "approve engagement", "counter-offer", "counter offer", "simulate",
    "whatsapp", "message provider", "send message", "coverage", "available",
    "booking", "book provider", "provider communication", "negotiation",
]

INCIDENT_KEYWORDS = [
    "incident", "cancelled", "no-show", "delay", "broken", "shortage", "risk",
    "emergency", "critical", "blocked", "failed", "recovery", "overheat",
]


def _get_context(config: Optional[RunnableConfig]):
    configurable = (config or {}).get("configurable", {})
    db = configurable.get("db")
    llm = configurable.get("llm_provider") or get_default_llm_provider()
    return db, llm


def _classify_intent(message: str, has_incidents: bool) -> str:
    """Deterministic intent classification based on message keywords and event state."""
    msg_lower = (message or "").lower()

    # Explicit communication and negotiation action triggers
    explicit_comm_actions = [
        "contact provider", "contact vendor", "whatsapp", "send message", "message provider",
        "negotiate", "counter-offer", "counter offer", "simulate provider", "simulate response",
        "confirm engagement", "confirm provider", "request engagement approval",
        "provider conversation", "provider thread",
    ]
    is_explicit_comm = any(kw in msg_lower for kw in explicit_comm_actions)

    # If there are open incidents or the message indicates an incident / failure:
    # Priority is INCIDENT_RECOVERY unless the user is explicitly executing provider communication.
    if has_incidents or any(kw in msg_lower for kw in INCIDENT_KEYWORDS):
        if not is_explicit_comm:
            return "INCIDENT_RECOVERY"

    # Route provider operational actions
    if any(kw in msg_lower for kw in ["contact", "engage", "whatsapp", "message provider"]):
        return "PROVIDER_CONTACT"
    if any(kw in msg_lower for kw in ["negotiate", "counter-offer", "counter offer"]):
        return "PROVIDER_NEGOTIATION"
    if any(kw in msg_lower for kw in ["approve engagement", "provider approval", "request approval"]):
        return "PROVIDER_APPROVAL"
    if any(kw in msg_lower for kw in ["confirm provider", "confirm engagement"]):
        return "PROVIDER_CONFIRMATION"
    if any(kw in msg_lower for kw in ["simulate"]):
        return "PROVIDER_SIMULATION"
    if any(kw in msg_lower for kw in ["conversation", "history", "thread", "messages"]):
        return "PROVIDER_QUERY"

    # Start operations triggers
    if any(kw in msg_lower for kw in ["start operations", "begin operations", "start operation", "launch operations", "start executing", "start execution", "execute plan"]):
        return "START_OPERATIONS"

    # Plan modification triggers
    if any(kw in msg_lower for kw in ["remove ", "delete ", "drop requirement", "add ", "without ", "modify budget", "update budget", "change guest", "change pax"]):
        return "PLAN_MODIFICATION"

    # If no incidents and message mentions provider/vendor discovery
    if any(kw in msg_lower for kw in ["provider", "vendor", "caterer", "dj", "decorator", "photographer"]):
        return "PROVIDER_DISCOVERY"

    if has_incidents:
        return "INCIDENT_RECOVERY"

    return "GENERAL_EVENT_QUERY"


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
    """Interprets natural language report and determines operational intent."""
    _, llm = _get_context(config)
    message = state.get("message", "")
    event_state = state.get("current_event_state") or {}
    incidents = state.get("current_incidents") or []

    # Classify operational intent deterministically
    has_incidents = len(incidents) > 0
    intent = _classify_intent(message, has_incidents)

    interpretation = llm.interpret_incident(message, event_state, incidents)

    messages = list(state.get("messages", []))
    messages.append({
        "role": "agent",
        "type": "interpretation",
        "content": interpretation.get("summary", "Interpreted operational situation."),
    })

    return {
        "operational_intent": intent,
        "status": "INTERPRETING",
        "messages": messages,
    }


def route_after_interpret(state: AgentState) -> str:
    """Routes based on operational intent: provider operations, autonomous execution, or incident recovery."""
    intent = state.get("operational_intent", "")

    if intent.startswith("PROVIDER_") or intent in ("START_OPERATIONS", "PLAN_MODIFICATION"):
        return "provider_operations"

    return "investigate"


def provider_operations_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Executes provider communication/negotiation operations using deterministic tools.

    Dispatches to the appropriate communication tool based on operational intent.
    All business logic, budget checks, and approvals are executed deterministically
    through NegotiationService.
    """
    db, _ = _get_context(config)
    event_id = state["event_id"]
    message = state.get("message", "")
    intent = state.get("operational_intent", "PROVIDER_DISCOVERY")
    event_state = state.get("current_event_state") or {}

    result: Dict[str, Any] = {"intent": intent}

    try:
        if intent == "START_OPERATIONS":
            op_result = start_autonomous_operations(
                db=db,
                event_id=event_id,
                user_id=state.get("user_id", "anonymous_operator"),
            )
            result["operation"] = "START_OPERATIONS"
            result["data"] = op_result
            result["response"] = op_result.get("message", "Autonomous operations started.")

        elif intent == "PLAN_MODIFICATION":
            op_result = modify_event_plan(
                db=db,
                event_id=event_id,
                modification=message,
                user_id=state.get("user_id", "anonymous_operator"),
            )
            result["operation"] = "MODIFY_PLAN"
            result["data"] = op_result
            result["response"] = op_result.get("message", "Operational plan updated.")

        elif intent == "PROVIDER_CONTACT":
            # Extract assignment_id from message context or find pending assignments
            assignment_id = _extract_assignment_id(db, event_id, message)
            if assignment_id:
                op_result = contact_provider(
                    db=db,
                    event_id=event_id,
                    assignment_id=assignment_id,
                )
                result["operation"] = "CONTACT_PROVIDER"
                result["data"] = op_result
                result["response"] = (
                    f"Provider contacted. Status: {op_result.get('negotiation_status', 'CONTACTED')}. "
                    f"Channel: {op_result.get('channel', 'MOCK')}."
                )
            else:
                result["response"] = "No pending provider assignment found for this event. Assign a provider first."
                result["operation"] = "NO_ASSIGNMENT"

        elif intent == "PROVIDER_NEGOTIATION":
            assignment_id = _extract_assignment_id(db, event_id, message, status_filter="NEGOTIATING")
            if assignment_id:
                op_result = negotiate_with_provider(db=db, assignment_id=assignment_id)
                result["operation"] = "NEGOTIATE"
                result["data"] = op_result
                result["response"] = (
                    f"Counter-offer sent. Round: {op_result.get('round', '?')}. "
                    f"Counter amount: {op_result.get('counter_offer_amount', 'N/A')}."
                )
            else:
                result["response"] = "No assignment in NEGOTIATING state found."
                result["operation"] = "NO_NEGOTIABLE_ASSIGNMENT"

        elif intent == "PROVIDER_APPROVAL":
            assignment_id = _extract_assignment_id(db, event_id, message, status_filter="AWAITING_APPROVAL")
            if assignment_id:
                op_result = request_provider_approval(db=db, event_id=event_id, assignment_id=assignment_id)
                result["operation"] = "REQUEST_APPROVAL"
                result["data"] = op_result
                result["response"] = (
                    f"Approval requested. Approval ID: {op_result.get('approval_id', 'N/A')}. "
                    f"Organizer must approve before confirmation."
                )
            else:
                result["response"] = "No assignment awaiting approval found."
                result["operation"] = "NO_APPROVAL_NEEDED"

        elif intent == "PROVIDER_CONFIRMATION":
            assignment_id = _extract_assignment_id(db, event_id, message, status_filter="AWAITING_APPROVAL")
            if assignment_id:
                op_result = confirm_provider_engagement(db=db, assignment_id=assignment_id)
                result["operation"] = "CONFIRM_ENGAGEMENT"
                result["data"] = op_result
                result["response"] = (
                    f"Provider confirmed: {op_result.get('vendor_name', 'Unknown')} for "
                    f"{op_result.get('category', 'N/A')} at {op_result.get('agreed_cost', 'N/A')}."
                )
            else:
                result["response"] = "No assignment ready for confirmation. Approval must be granted first."
                result["operation"] = "CONFIRMATION_NOT_READY"

        elif intent == "PROVIDER_SIMULATION":
            assignment_id = _extract_assignment_id(db, event_id, message)
            if assignment_id:
                scenario = "ACCEPT"
                msg_lower = message.lower()
                if "decline" in msg_lower:
                    scenario = "DECLINE"
                elif "counter" in msg_lower:
                    scenario = "COUNTER"
                elif "no response" in msg_lower or "no_response" in msg_lower:
                    scenario = "NO_RESPONSE"

                op_result = simulate_provider_response(
                    db=db,
                    assignment_id=assignment_id,
                    scenario=scenario,
                )
                result["operation"] = "SIMULATION"
                result["data"] = op_result
                result["response"] = (
                    f"[DEMO SIMULATION] Provider response simulated ({scenario}). "
                    f"Status: {op_result.get('negotiation_status', 'N/A')}."
                )
            else:
                result["response"] = "No provider assignment found for simulation."
                result["operation"] = "NO_ASSIGNMENT"

        elif intent == "PROVIDER_QUERY":
            assignment_id = _extract_assignment_id(db, event_id, message)
            if assignment_id:
                op_result = get_provider_negotiation_history(db=db, assignment_id=assignment_id)
                # Serialize assignment for response
                assignment_data = op_result.get("assignment")
                vendor_data = op_result.get("vendor")
                msg_count = len(op_result.get("messages", []))
                v_name = getattr(vendor_data, "name", "Unknown") if vendor_data else "Unknown"
                neg_status = getattr(assignment_data, "negotiation_status", "N/A") if assignment_data else "N/A"
                result["operation"] = "QUERY_CONVERSATION"
                result["data"] = {
                    "message_count": msg_count,
                    "negotiation_status": neg_status,
                    "vendor_name": v_name,
                    "messages": op_result.get("messages", []),
                    "budget_validation": op_result.get("budget_validation"),
                }
                result["response"] = (
                    f"Conversation with {v_name}: {msg_count} messages. "
                    f"Negotiation status: {neg_status}."
                )
            else:
                result["response"] = "No provider assignment found for this event."
                result["operation"] = "NO_ASSIGNMENT"

        else:
            # PROVIDER_DISCOVERY or general provider query
            from app.models.vendor_assignment import VendorAssignment
            assignments = (
                db.query(VendorAssignment)
                .filter(VendorAssignment.event_id == event_id)
                .all()
            )
            summary_parts = []
            for a in assignments:
                summary_parts.append(
                    f"- {a.category}: {a.negotiation_status} "
                    f"(quoted: {a.quoted_amount or 'N/A'}, target: {a.target_amount or 'N/A'})"
                )
            if summary_parts:
                result["response"] = (
                    f"Provider assignments for this event:\n" + "\n".join(summary_parts)
                )
            else:
                result["response"] = "No provider assignments found for this event."
            result["operation"] = "PROVIDER_SUMMARY"

    except Exception as exc:
        result["operation"] = "ERROR"
        result["error"] = str(exc)
        result["response"] = f"Provider operation failed: {str(exc)}"

    return {
        "provider_operation_result": result,
        "status": "COMPLETED",
        "final_response": result.get("response", "Provider operation completed."),
    }


def _extract_assignment_id(
    db, event_id: str, message: str, status_filter: Optional[str] = None
) -> Optional[str]:
    """Finds the most relevant vendor assignment for an event.

    Deterministic resolution: finds the assignment matching the status filter,
    or the most recently created one if no filter specified.
    """
    from app.models.vendor_assignment import VendorAssignment

    query = db.query(VendorAssignment).filter(VendorAssignment.event_id == event_id)

    if status_filter:
        query = query.filter(VendorAssignment.negotiation_status == status_filter)

    # Order by most recent
    assignments = query.order_by(VendorAssignment.created_at.desc()).all()

    if not assignments:
        # If filtered by status and nothing found, try without filter
        if status_filter:
            assignments = (
                db.query(VendorAssignment)
                .filter(VendorAssignment.event_id == event_id)
                .order_by(VendorAssignment.created_at.desc())
                .all()
            )
        if not assignments:
            return None

    # Try to match by category keyword from message
    msg_lower = message.lower()
    for a in assignments:
        cat_lower = (a.category or "").lower().replace("_", " ")
        if cat_lower and cat_lower in msg_lower:
            return a.id

    # Return first (most recent)
    return assignments[0].id


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

    # Build informative response with provider state
    db, _ = _get_context(config)
    event_id = state["event_id"]

    response_parts = [
        f"Event '{event_state.get('name', event_id)}' is in state '{event_state.get('state', 'NORMAL')}'.",
        "No active incidents require recovery.",
    ]

    # Include provider assignment summary
    try:
        from app.models.vendor_assignment import VendorAssignment
        assignments = db.query(VendorAssignment).filter(VendorAssignment.event_id == event_id).all()
        if assignments:
            response_parts.append(f"\nProvider assignments ({len(assignments)}):")
            for a in assignments:
                response_parts.append(
                    f"  • {a.category}: {a.negotiation_status}"
                    + (f" — quoted {a.currency} {a.quoted_amount:,.0f}" if a.quoted_amount else "")
                )
    except Exception:
        pass

    return {
        "status": "COMPLETED",
        "final_response": "\n".join(response_parts),
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
    """LangGraph definition for EVENTRA's single Event Operations Agent.

    Supports two operational branches:
    1. Incident Recovery: observe → interpret → investigate → generate → authorize → execute → verify
    2. Provider Operations: observe → interpret → provider_operations → end
    """

    def __init__(self):
        self._compiled_graph = None

    def build_graph(self):
        """Constructs and compiles the StateGraph."""
        builder = StateGraph(AgentState)

        # 1. Register Nodes
        builder.add_node("observe", observe_node)
        builder.add_node("interpret", interpret_node)
        builder.add_node("provider_operations", provider_operations_node)
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

        # After interpret: route to provider operations or incident investigation
        builder.add_conditional_edges(
            "interpret",
            route_after_interpret,
            {
                "provider_operations": "provider_operations",
                "investigate": "investigate",
            },
        )

        # Provider operations terminate directly
        builder.add_edge("provider_operations", END)

        # Incident recovery flow (existing)
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
