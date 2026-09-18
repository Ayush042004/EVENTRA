"""Deterministic State & Operational Risk Verifier.

Re-evaluates operational risk post-action and determines if the event operational state
should transition (e.g., RECOVERY -> NORMAL).
"""
from typing import Any, Dict, Optional, Tuple
from app.engines.impact.analyzer import ImpactAnalyzer
from app.engines.risk.calculator import RiskCalculator
from app.engines.verification.types import VerificationContext
from app.models.enums import EventState


class StateVerifier:
    """Calculates risk delta and determines target event operational state."""

    def __init__(self):
        self._risk_calc = RiskCalculator()
        self._impact_analyzer = ImpactAnalyzer()

    def evaluate_state_and_risk(
        self,
        context: VerificationContext,
        schedule_feasible: bool,
        objectives_satisfied: bool,
        budget_valid: bool,
        hard_constraints_satisfied: bool,
    ) -> Tuple[str, str, str, str, Dict[str, Any]]:
        """Evaluates operational risk and recommended event state post-action.

        Returns:
            (risk_before, risk_after, event_state_before, event_state_after, risk_details)
        """
        event = context.event
        event_state_before = getattr(event, "state", EventState.NORMAL.value)

        # 1. Determine risk_before
        risk_before = "MEDIUM"
        if context.original_risk:
            risk_before = context.original_risk.get("risk_level", "HIGH")
        elif context.incident:
            sev = getattr(context.incident, "severity", "MEDIUM")
            risk_before = "CRITICAL" if sev in ("CRITICAL", "EMERGENCY") else ("HIGH" if sev == "HIGH" else "MEDIUM")

        # 2. Recalculate operational risk post-action
        alt_providers = len([p for p in context.providers if getattr(p, "status", "ACTIVE") == "ACTIVE"])
        impact_result = {}
        if context.incident:
            impact_result = self._impact_analyzer.analyze(
                incident=context.incident,
                tasks=context.tasks,
                dependencies=context.dependencies,
                resources=context.resources,
                vendor_assignments=context.vendor_assignments,
                budget_items=context.budget_items,
                event=context.event,
                objectives=context.objectives,
                constraints=context.constraints,
            )
            risk_result = self._risk_calc.calculate(
                incident=context.incident,
                impact_result=impact_result,
                event=context.event,
                alternative_providers_count=alt_providers,
            )
            calculated_risk = risk_result.get("risk_level", "LOW")
        else:
            calculated_risk = "LOW"

        # If schedule is not feasible or hard constraints are violated, risk cannot be LOW
        if not schedule_feasible or not hard_constraints_satisfied:
            risk_after = "CRITICAL" if not schedule_feasible else "HIGH"
        elif not objectives_satisfied:
            risk_after = "MEDIUM"
        else:
            risk_after = "LOW"

        # 3. Determine recommended event_state_after
        # Rule: Only transition to NORMAL if ALL operational invariants hold
        fully_healthy = (
            schedule_feasible
            and objectives_satisfied
            and budget_valid
            and hard_constraints_satisfied
            and risk_after in ("LOW", "MEDIUM")
        )

        if fully_healthy:
            event_state_after = EventState.NORMAL.value
        else:
            # Maintain elevated operational state
            if risk_after == "CRITICAL" or not schedule_feasible:
                event_state_after = EventState.CRITICAL.value
            elif risk_after == "HIGH":
                event_state_after = EventState.AT_RISK.value
            else:
                event_state_after = event_state_before if event_state_before != EventState.NORMAL.value else EventState.AT_RISK.value

        return (
            risk_before,
            risk_after,
            event_state_before,
            event_state_after,
            {"calculated_risk": calculated_risk, "fully_healthy": fully_healthy},
        )
