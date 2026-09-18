"""Deterministic Schedule Verifier.

Verifies task dependencies, temporal ordering, critical path feasibility,
and deadline integrity without LLMs or opaque heuristics.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List
from app.engines.dependency.graph import DependencyGraph
from app.engines.verification.types import (
    ScheduleVerificationResult,
    ScheduleVerificationStatus,
    VerificationContext,
)


class ScheduleVerifier:
    """Verifies schedule feasibility and detects deadline/dependency violations."""

    def verify(self, context: VerificationContext) -> ScheduleVerificationResult:
        tasks = context.tasks or []
        dependencies = context.dependencies or []
        event = context.event

        deadline_violations: List[Dict[str, Any]] = []
        dep_violations: List[str] = []

        # 1. Check dependency cycles
        graph = DependencyGraph.from_tasks_and_dependencies(tasks, dependencies)
        try:
            graph.topological_sort()
        except ValueError as err:
            dep_violations.append(str(err))

        tasks_by_id = {
            (t.id if hasattr(t, "id") else t.get("id")): t
            for t in tasks
        }

        # 2. Check predecessor/successor temporal ordering
        for dep in dependencies:
            p_id = dep.predecessor_task_id if hasattr(dep, "predecessor_task_id") else dep.get("predecessor_task_id")
            s_id = dep.successor_task_id if hasattr(dep, "successor_task_id") else dep.get("successor_task_id")
            lag = dep.lag_minutes if hasattr(dep, "lag_minutes") else dep.get("lag_minutes", 0)

            pred = tasks_by_id.get(p_id)
            succ = tasks_by_id.get(s_id)
            if pred and succ and pred.planned_end and succ.planned_start:
                if succ.planned_start < pred.planned_end + timedelta(minutes=lag or 0):
                    dep_violations.append(
                        f"Task '{succ.name}' starts before predecessor '{pred.name}' finishes."
                    )

        # 3. Check Event Window & Deadlines
        event_end = getattr(event, "end_datetime", None) or (
            event.get("end_datetime") if isinstance(event, dict) else None
        )

        total_delay = 0
        min_slack = 999999

        for task in tasks:
            t_id = task.id if hasattr(task, "id") else task.get("id")
            t_name = task.name if hasattr(task, "name") else task.get("name")
            p_end = task.planned_end if hasattr(task, "planned_end") else task.get("planned_end")
            slack = task.slack_minutes if hasattr(task, "slack_minutes") else task.get("slack_minutes", 0)
            if slack is not None and slack < min_slack:
                min_slack = slack

            if p_end and event_end and p_end > event_end:
                deadline_violations.append({
                    "task_id": t_id,
                    "task_name": t_name,
                    "planned_end": p_end.isoformat() if isinstance(p_end, datetime) else str(p_end),
                    "deadline": event_end.isoformat() if isinstance(event_end, datetime) else str(event_end),
                    "reason": f"Task '{t_name}' planned end exceeds event end window.",
                })

        # 4. Check Provider ETA breaches from incident evidence or recovery payload
        evidence = {}
        if context.incident and hasattr(context.incident, "evidence_metadata") and context.incident.evidence_metadata:
            evidence = context.incident.evidence_metadata
        elif context.incident and isinstance(context.incident, dict):
            evidence = context.incident.get("evidence_metadata") or {}

        provider_etas = evidence.get("provider_eta_minutes") or {}
        # Also check payload
        if "eta_minutes" in context.payload:
            assigned_vid = context.payload.get("new_vendor_id") or context.payload.get("vendor_id")
            if assigned_vid:
                provider_etas[assigned_vid] = context.payload["eta_minutes"]

        # Check if any assigned vendor's ETA causes a deadline violation
        for assignment in context.vendor_assignments:
            if assignment.status == "CONFIRMED" and assignment.vendor_id in provider_etas:
                eta = provider_etas[assignment.vendor_id]
                # Find associated task
                cat = assignment.category
                for t in tasks:
                    if t.required_provider_category == cat:
                        # If ETA exceeds task planned start or reduces slack below 0
                        available_slack = t.slack_minutes or 0
                        if eta > available_slack and available_slack > 0:
                            deadline_violations.append({
                                "task_id": t.id,
                                "task_name": t.name,
                                "vendor_id": assignment.vendor_id,
                                "eta_minutes": eta,
                                "available_slack_minutes": available_slack,
                                "reason": f"Vendor ETA ({eta}m) exceeds task '{t.name}' slack ({available_slack}m), causing deadline breach.",
                            })

        is_feasible = len(deadline_violations) == 0 and len(dep_violations) == 0

        # Determine status
        if not is_feasible:
            status = ScheduleVerificationStatus.SCHEDULE_FAILED if len(dep_violations) > 0 else ScheduleVerificationStatus.SCHEDULE_STILL_AT_RISK
        elif min_slack > 0:
            status = ScheduleVerificationStatus.SCHEDULE_RESTORED
        else:
            status = ScheduleVerificationStatus.SCHEDULE_IMPROVED

        return ScheduleVerificationResult(
            status=status,
            is_feasible=is_feasible,
            deadline_violations=deadline_violations,
            dependency_violations=dep_violations,
            critical_path_intact=is_feasible,
            slack_remaining_minutes=max(0, min_slack) if min_slack != 999999 else 0,
            total_delay_minutes=total_delay,
            details={
                "task_count": len(tasks),
                "dependency_count": len(dependencies),
                "deadline_violation_count": len(deadline_violations),
            },
        )
