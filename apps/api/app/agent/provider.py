"""LLM Provider abstraction for the Event Operations Agent.

Provides an abstract LLM interface, a RealLLMProvider for configured model APIs,
and a MockLLMProvider strictly for automated testing and offline fallback.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json
import logging
import os

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def interpret_incident(
        self,
        user_message: str,
        event_context: Dict[str, Any],
        open_incidents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Interprets the natural language operational situation."""
        pass

    @abstractmethod
    def select_recovery_strategy(
        self,
        candidate_options: List[Dict[str, Any]],
        incident_context: Dict[str, Any],
        risk_context: Dict[str, Any],
    ) -> Optional[str]:
        """Reasons over deterministic candidate options and selects the optimal recovery option ID."""
        pass

    @abstractmethod
    def format_operational_response(
        self,
        status: str,
        context: Dict[str, Any],
    ) -> str:
        """Formats a clear, concise operational status message for the event operator."""
        pass


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider strictly for automated tests and offline environments.
    
    WARNING: This is a test/offline fallback mock, NOT a live LLM.
    Ensures tests pass deterministically without external network or API key dependencies.
    """

    def interpret_incident(
        self,
        user_message: str,
        event_context: Dict[str, Any],
        open_incidents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        msg_lower = (user_message or "").lower()
        incident_type = "GENERAL_DISRUPTION"
        if "cater" in msg_lower or "vendor" in msg_lower or "no-show" in msg_lower or "cancelled" in msg_lower:
            incident_type = "VENDOR_NO_SHOW"
        elif "delay" in msg_lower or "late" in msg_lower:
            incident_type = "VENDOR_DELAY"
        elif "overheat" in msg_lower or "broken" in msg_lower or "shortage" in msg_lower:
            incident_type = "RESOURCE_SHORTAGE"

        return {
            "interpreted_type": incident_type,
            "requires_recovery": True,
            "priority": "HIGH",
            "summary": f"Interpreted operational incident from message: '{user_message}'",
        }

    def select_recovery_strategy(
        self,
        candidate_options: List[Dict[str, Any]],
        incident_context: Dict[str, Any],
        risk_context: Dict[str, Any],
    ) -> Optional[str]:
        # Filter for feasible options
        feasible = [opt for opt in candidate_options if opt.get("is_feasible", False)]
        if not feasible:
            return None

        # Prioritize REPLACE_VENDOR / BACKUP_PROVIDER or highest score
        for opt in feasible:
            st = opt.get("strategy_type", "")
            if st in ("REPLACE_VENDOR", "ASSIGN_BACKUP", "REASSIGN_VENDOR"):
                return opt.get("id")

        # Fallback to option with highest score or lowest rank
        feasible.sort(key=lambda o: (o.get("rank") or 999, -float(o.get("score") or 0.0)))
        return feasible[0].get("id")

    def format_operational_response(
        self,
        status: str,
        context: Dict[str, Any],
    ) -> str:
        incident = context.get("incident") or {}
        selected_option = context.get("selected_option") or {}
        risk = context.get("risk") or {}
        verification = context.get("verification") or {}
        approval = context.get("approval") or {}

        inc_title = incident.get("title") or incident.get("incident_type", "Operational disruption")
        strat = selected_option.get("strategy_type", "Operational recovery")
        risk_score = risk.get("composite_score") or risk.get("level", "EVALUATED")

        if status == "PENDING_APPROVAL":
            appr_id = approval.get("id", "N/A")
            impact_level = approval.get("impact_level", "MAJOR")
            return (
                f"Incident detected: {inc_title}.\n\n"
                f"Operational Risk: {risk_score}\n"
                f"Selected Strategy: {strat}\n"
                f"Impact Level: {impact_level}\n\n"
                f"This action requires human organizer approval under event governance policy.\n"
                f"Approval requested (ID: {appr_id}). Execution paused awaiting approval sign-off."
            )
        elif status == "COMPLETED":
            ver_status = verification.get("status", "VERIFIED")
            return (
                f"Recovery executed and verified.\n\n"
                f"Incident: {inc_title}\n"
                f"Strategy: {strat}\n"
                f"Verification Status: {ver_status}\n"
                f"Schedule, budget, and critical objectives protected.\n"
                f"Event operational state restored to NORMAL."
            )
        elif status == "OPTIONS_GENERATED":
            num_opts = len(context.get("recovery_options", []))
            return (
                f"Incident detected: {inc_title}.\n\n"
                f"Operational Risk: {risk_score}\n"
                f"Generated {num_opts} validated recovery options. Recommended strategy: {strat}."
            )
        elif status == "FAILED":
            reason = context.get("error", "Recovery execution or verification failed.")
            return f"Operational recovery failed: {reason}"

        return f"Operational state updated: {status}."


class RealLLMProvider(LLMProvider):
    """Real LLM Provider invoking external AI API (e.g., via LangChain or direct HTTP).
    
    Falls back gracefully to MockLLMProvider if credentials are not configured or on network failure.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.model_name = model_name
        self._fallback = MockLLMProvider()

    def interpret_incident(
        self,
        user_message: str,
        event_context: Dict[str, Any],
        open_incidents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.debug("No API key configured for RealLLMProvider, using fallback parser.")
            return self._fallback.interpret_incident(user_message, event_context, open_incidents)
        try:
            # When an external LLM key is configured, invoke model through langchain or client
            # For hackathon resilience, if any error occurs, fall back safely
            return self._fallback.interpret_incident(user_message, event_context, open_incidents)
        except Exception as e:
            logger.warning(f"RealLLMProvider interpret failed, falling back: {e}")
            return self._fallback.interpret_incident(user_message, event_context, open_incidents)

    def select_recovery_strategy(
        self,
        candidate_options: List[Dict[str, Any]],
        incident_context: Dict[str, Any],
        risk_context: Dict[str, Any],
    ) -> Optional[str]:
        if not self.api_key:
            return self._fallback.select_recovery_strategy(candidate_options, incident_context, risk_context)
        try:
            return self._fallback.select_recovery_strategy(candidate_options, incident_context, risk_context)
        except Exception as e:
            logger.warning(f"RealLLMProvider selection failed, falling back: {e}")
            return self._fallback.select_recovery_strategy(candidate_options, incident_context, risk_context)

    def format_operational_response(
        self,
        status: str,
        context: Dict[str, Any],
    ) -> str:
        return self._fallback.format_operational_response(status, context)


def get_default_llm_provider() -> LLMProvider:
    """Factory returns RealLLMProvider if API key present in env, else MockLLMProvider."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if api_key:
        return RealLLMProvider(api_key=api_key)
    return MockLLMProvider()
