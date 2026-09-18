"""Deterministic Objective Verifier.

Compares event objectives before vs after operational actions to evaluate
whether critical and standard objectives are restored or remain at risk.
"""
from typing import Any, Dict, List
from app.engines.verification.types import (
    ObjectiveStatus,
    ObjectiveVerificationResult,
    VerificationContext,
)


class ObjectiveVerifier:
    """Evaluates whether operational event objectives were preserved or restored."""

    def verify(
        self, context: VerificationContext, schedule_feasible: bool, deadline_violations: List[Dict[str, Any]]
    ) -> ObjectiveVerificationResult:
        objectives = context.objectives or []
        tasks_by_id = {t.id: t for t in context.tasks}
        assignments_by_cat = {a.category: a for a in context.vendor_assignments if a.status == "CONFIRMED"}

        violating_task_ids = {v.get("task_id") for v in deadline_violations if v.get("task_id")}

        # Check before statuses from original_impact if available
        before_impact_objs = {}
        if context.original_impact:
            for aff in context.original_impact.get("affected_objectives", []):
                before_impact_objs[aff.get("id")] = aff.get("status", "AT_RISK")

        evaluated: List[Dict[str, Any]] = []
        restored: List[str] = []
        still_at_risk: List[str] = []
        critical_satisfied = True

        for obj in objectives:
            obj_id = obj.id if hasattr(obj, "id") else obj.get("id", "")
            obj_name = (obj.name if hasattr(obj, "name") else obj.get("name", "")).lower()
            obj_priority = (obj.priority if hasattr(obj, "priority") else obj.get("priority", "HIGH")).upper()
            is_critical = obj_priority == "CRITICAL"

            status_before = before_impact_objs.get(obj_id, "SATISFIED")

            # Check if any tasks matching this objective have issues
            threatened = False
            failed = False

            for task_id, task in tasks_by_id.items():
                tname = (task.name or "").lower()
                cat = task.required_provider_category or ""

                # If objective relates to this task
                if any(w in obj_name for w in tname.split() if len(w) > 3) or (cat and cat.lower() in obj_name):
                    # Check task status and deadline
                    if task_id in violating_task_ids:
                        failed = True
                        break
                    if task.status in ("FAILED", "BLOCKED"):
                        threatened = True
                    # Check provider assignment if required
                    if cat and cat not in assignments_by_cat:
                        threatened = True

            if not schedule_feasible and is_critical:
                threatened = True

            if failed:
                status_after = ObjectiveStatus.FAILED.value
                still_at_risk.append(obj_name)
                if is_critical:
                    critical_satisfied = False
            elif threatened:
                status_after = ObjectiveStatus.AT_RISK.value
                still_at_risk.append(obj_name)
                if is_critical:
                    critical_satisfied = False
            else:
                status_after = ObjectiveStatus.SATISFIED.value
                if status_before in ("AT_RISK", "FAILED"):
                    restored.append(obj_name)

            evaluated.append({
                "id": obj_id,
                "name": obj.name if hasattr(obj, "name") else obj.get("name", ""),
                "priority": obj_priority,
                "status_before": status_before,
                "status_after": status_after,
                "restored": status_after == ObjectiveStatus.SATISFIED.value and status_before != "SATISFIED",
            })

        overall_status = ObjectiveStatus.SATISFIED.value if critical_satisfied and not still_at_risk else (
            ObjectiveStatus.AT_RISK.value if critical_satisfied else ObjectiveStatus.FAILED.value
        )

        return ObjectiveVerificationResult(
            status=overall_status,
            objectives_evaluated=evaluated,
            objectives_restored=restored,
            objectives_still_at_risk=still_at_risk,
            critical_objectives_satisfied=critical_satisfied,
            details={
                "total_count": len(objectives),
                "restored_count": len(restored),
                "at_risk_count": len(still_at_risk),
            },
        )
