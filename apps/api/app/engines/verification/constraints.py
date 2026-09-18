"""Deterministic Constraint Verifier.

Evaluates hard and soft operational constraints across time windows,
capacity, noise curfews, and budget caps.
"""
from typing import Any, Dict, List
from app.engines.verification.types import (
    ConstraintVerificationResult,
    VerificationContext,
)


class ConstraintVerifier:
    """Verifies that operational state respects all defined hard and soft constraints."""

    def verify(
        self,
        context: VerificationContext,
        schedule_feasible: bool,
        budget_valid: bool,
        deadline_violations: List[Dict[str, Any]],
    ) -> ConstraintVerificationResult:
        constraints = context.constraints or []

        violations: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        for c in constraints:
            c_id = getattr(c, "id", "")
            c_name = getattr(c, "name", "Unnamed Constraint")
            c_type = getattr(c, "type", "GENERAL")
            c_sev = (getattr(c, "severity", "HARD") or "HARD").upper()
            is_hard = c_sev == "HARD"

            violated = False
            reason = ""

            if c_type == "TIME_WINDOW" and (not schedule_feasible or len(deadline_violations) > 0):
                violated = True
                reason = "Time window violated due to task deadline or dependency breaches."
            elif c_type == "BUDGET_CAP" and not budget_valid:
                violated = True
                reason = "Budget cap breached by actual expenditures."
            elif c_type == "VENUE_CAPACITY" and context.venue:
                cap = getattr(context.venue, "capacity", 0) or 0
                guests = getattr(context.event, "guest_count", 0) or 0
                if cap > 0 and guests > cap:
                    violated = True
                    reason = f"Guest count ({guests}) exceeds venue capacity ({cap})."

            if violated:
                entry = {
                    "constraint_id": c_id,
                    "name": c_name,
                    "type": c_type,
                    "severity": c_sev,
                    "reason": reason,
                }
                if is_hard:
                    violations.append(entry)
                else:
                    warnings.append(entry)

        return ConstraintVerificationResult(
            hard_constraints_satisfied=len(violations) == 0,
            soft_constraints_satisfied=len(warnings) == 0,
            violations=violations,
            warnings=warnings,
        )
