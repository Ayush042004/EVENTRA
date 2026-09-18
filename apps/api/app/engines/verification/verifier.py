"""Master Verification Engine.

Coordinates all deterministic sub-verifiers to evaluate operational outcomes,
re-evaluate risk, and determine final verification status.
"""
from typing import Any, Dict, List
from app.engines.verification.budget import BudgetVerifier
from app.engines.verification.constraints import ConstraintVerifier
from app.engines.verification.objectives import ObjectiveVerifier
from app.engines.verification.providers import ProviderVerifier
from app.engines.verification.resources import ResourceVerifier
from app.engines.verification.schedule import ScheduleVerifier
from app.engines.verification.state import StateVerifier
from app.engines.verification.types import (
    BudgetVerificationStatus,
    ProviderVerificationStatus,
    ScheduleVerificationStatus,
    VerificationContext,
    VerificationResultData,
    VerificationStatus,
)


class VerificationEngine:
    """Deterministic orchestrator for comprehensive post-action verification."""

    def __init__(self):
        self._schedule_verifier = ScheduleVerifier()
        self._budget_verifier = BudgetVerifier()
        self._resource_verifier = ResourceVerifier()
        self._provider_verifier = ProviderVerifier()
        self._constraint_verifier = ConstraintVerifier()
        self._objective_verifier = ObjectiveVerifier()
        self._state_verifier = StateVerifier()

    def verify(self, context: VerificationContext) -> VerificationResultData:
        failure_reasons: List[str] = []
        warnings: List[str] = []

        # 1. Verify Schedule
        sched_res = self._schedule_verifier.verify(context)
        for v in sched_res.deadline_violations:
            failure_reasons.append(v.get("reason", "Schedule deadline violation."))
        for d in sched_res.dependency_violations:
            failure_reasons.append(d)

        # 2. Verify Budget
        budget_res = self._budget_verifier.verify(context)
        for b in budget_res.violations:
            failure_reasons.append(b)

        # 3. Verify Resources
        res_res = self._resource_verifier.verify(context)
        for r in res_res.conflicts:
            failure_reasons.append(r)

        # 4. Verify Providers
        prov_res = self._provider_verifier.verify(context)
        for p in prov_res.details.get("violations", []):
            failure_reasons.append(p)

        # 5. Verify Constraints
        const_res = self._constraint_verifier.verify(
            context=context,
            schedule_feasible=sched_res.is_feasible,
            budget_valid=budget_res.is_valid,
            deadline_violations=sched_res.deadline_violations,
        )
        for c in const_res.violations:
            failure_reasons.append(f"Hard constraint violation: {c.get('name')} - {c.get('reason')}")
        for w in const_res.warnings:
            warnings.append(f"Soft constraint warning: {w.get('name')} - {w.get('reason')}")

        # 6. Verify Objectives
        obj_res = self._objective_verifier.verify(
            context=context,
            schedule_feasible=sched_res.is_feasible,
            deadline_violations=sched_res.deadline_violations,
        )
        if not obj_res.critical_objectives_satisfied:
            failure_reasons.append("Critical event objective is not satisfied.")
        elif obj_res.objectives_still_at_risk:
            warnings.append(f"Objectives still at risk: {', '.join(obj_res.objectives_still_at_risk)}.")

        # 7. Evaluate State & Risk
        risk_before, risk_after, state_before, state_after, risk_meta = self._state_verifier.evaluate_state_and_risk(
            context=context,
            schedule_feasible=sched_res.is_feasible,
            objectives_satisfied=obj_res.status == "SATISFIED",
            budget_valid=budget_res.is_valid,
            hard_constraints_satisfied=const_res.hard_constraints_satisfied,
        )

        # 8. Determine Intended and Actual Outcomes
        intended = self._determine_intended_outcome(context)
        actual = {
            "schedule_status": sched_res.status.value,
            "budget_status": budget_res.status.value,
            "resource_status": res_res.status.value,
            "provider_status": prov_res.status.value,
            "objective_status": obj_res.status,
            "objectives_restored": obj_res.objectives_restored,
            "objectives_still_at_risk": obj_res.objectives_still_at_risk,
            "risk_reduced": (risk_before in ("HIGH", "CRITICAL") and risk_after in ("LOW", "MEDIUM")),
            "deadline_breaches": len(sched_res.deadline_violations),
        }

        # 9. Synthesize Overall Verification Status
        # PRINCIPLE: ACTION SUCCESS IS NOT VERIFICATION SUCCESS.
        if (
            sched_res.is_feasible
            and budget_res.is_valid
            and res_res.is_valid
            and prov_res.is_valid
            and const_res.hard_constraints_satisfied
            and obj_res.critical_objectives_satisfied
            and len(obj_res.objectives_still_at_risk) == 0
        ):
            status = VerificationStatus.VERIFIED
        elif (
            # If critical deadline breach, provider failure, or hard constraint failure
            len(sched_res.deadline_violations) > 0
            or not prov_res.is_valid
            or not const_res.hard_constraints_satisfied
            or not obj_res.critical_objectives_satisfied
        ):
            # If some sub-systems improved but critical items failed
            if prov_res.assignment_confirmed and (budget_res.is_valid or len(obj_res.objectives_restored) > 0):
                status = VerificationStatus.PARTIALLY_VERIFIED
            else:
                status = VerificationStatus.FAILED
        else:
            # One or more non-critical objectives still at risk, or soft warnings
            status = VerificationStatus.PARTIALLY_VERIFIED

        return VerificationResultData(
            status=status,
            intended_outcome=intended,
            actual_outcome=actual,
            objective_results=obj_res.objectives_evaluated,
            schedule_result={
                "status": sched_res.status.value,
                "is_feasible": sched_res.is_feasible,
                "deadline_violations": sched_res.deadline_violations,
                "dependency_violations": sched_res.dependency_violations,
                "slack_remaining_minutes": sched_res.slack_remaining_minutes,
            },
            budget_result={
                "status": budget_res.status.value,
                "is_valid": budget_res.is_valid,
                "total_budget": float(budget_res.total_budget),
                "total_committed": float(budget_res.total_committed),
                "remaining_headroom": float(budget_res.remaining_headroom),
                "currency": budget_res.currency,
                "violations": budget_res.violations,
            },
            resource_result={
                "status": res_res.status.value,
                "is_valid": res_res.is_valid,
                "conflicts": res_res.conflicts,
                "allocated_resources": res_res.allocated_resources,
            },
            provider_result={
                "status": prov_res.status.value,
                "is_valid": prov_res.is_valid,
                "assignment_confirmed": prov_res.assignment_confirmed,
                "category_matched": prov_res.category_matched,
                "available": prov_res.available,
                "eta_compatible": prov_res.eta_compatible,
            },
            venue_result={"status": "VALID", "capacity_valid": True},
            constraint_result={
                "hard_constraints_satisfied": const_res.hard_constraints_satisfied,
                "soft_constraints_satisfied": const_res.soft_constraints_satisfied,
                "violations": const_res.violations,
                "warnings": const_res.warnings,
            },
            risk_before=risk_before,
            risk_after=risk_after,
            event_state_before=state_before,
            event_state_after=state_after,
            failure_reasons=failure_reasons,
            warnings=warnings,
        )

    def _determine_intended_outcome(self, context: VerificationContext) -> Dict[str, Any]:
        """Constructs structured intended outcomes based on action and recovery metadata."""
        act_type = context.action_type
        if "REASSIGN_VENDOR" in act_type or "BACKUP" in act_type:
            return {
                "action": "REASSIGN_VENDOR",
                "goal": "Assign replacement provider, preserve schedule feasibility, and restore service objective.",
                "target_id": context.target_id,
            }
        elif "ADJUST_SCHEDULE" in act_type or "RESCHEDULE" in act_type:
            return {
                "action": "ADJUST_SCHEDULE",
                "goal": "Shift task window, maintain dependency order, and avoid event end window breach.",
                "target_id": context.target_id,
            }
        elif "ALLOCATE_RESOURCE" in act_type:
            return {
                "action": "ALLOCATE_RESOURCE",
                "goal": "Allocate sufficient resource quantity to unblock target task.",
                "target_id": context.target_id,
            }
        elif "ADJUST_BUDGET" in act_type:
            return {
                "action": "ADJUST_BUDGET",
                "goal": "Update committed expenditure without breaching event budget cap.",
                "target_id": context.target_id,
            }
        return {
            "action": act_type,
            "goal": "Execute operational modification and maintain event stability.",
            "target_id": context.target_id,
        }
