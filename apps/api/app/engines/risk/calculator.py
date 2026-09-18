"""Deterministic Engine: risk.calculator

Calculates operational event risk from explicit factors:
time remaining, task criticality, dependency count & depth, schedule slack,
resource availability, provider alternatives, budget headroom, and objective criticality.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.engines.risk.classifier import RiskClassifier
from app.models.enums import TaskPriority


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RiskCalculator:
    """Pure deterministic risk engine calculator without opaque scoring or AI confidence."""

    def __init__(self):
        self._classifier = RiskClassifier()

    def calculate(
        self,
        incident: Any,
        impact_result: Dict[str, Any],
        event: Optional[Any] = None,
        alternative_providers_count: int = 0,
    ) -> Dict[str, Any]:
        """Calculates operational risk based on 8 explicit factors.

        Args:
            incident: Incident ORM object or dict.
            impact_result: Structured result from ImpactAnalyzer.
            event: Event ORM object or dict.
            alternative_providers_count: Number of alternative compatible vendors available.

        Returns:
            Structured RiskResult dictionary.
        """
        incident_id = (
            incident.get("id") if isinstance(incident, dict)
            else getattr(incident, "id", "")
        )

        direct_tasks = impact_result.get("directly_affected_tasks", [])
        indirect_tasks = impact_result.get("indirectly_affected_tasks", [])
        all_affected_tasks = direct_tasks + indirect_tasks
        schedule_impact = impact_result.get("schedule_impact", {})
        affected_resources = impact_result.get("affected_resources", [])
        affected_providers = impact_result.get("affected_providers", [])
        budget_impact = impact_result.get("budget_impact", {})
        affected_objectives = impact_result.get("affected_objectives", [])
        affected_constraints = impact_result.get("affected_constraints", [])
        dep_depth = impact_result.get("dependency_depth", 0)

        factors: List[Dict[str, Any]] = []

        # 1. TIME REMAINING (Weight: 0.15)
        # Check time until event start or nearest affected task start
        time_score = 20.0
        time_desc = "More than 24 hours remaining before operation"
        now = utc_now()
        target_time = None

        if event:
            event_start = event.get("start_datetime") if isinstance(event, dict) else getattr(event, "start_datetime", None)
            if event_start and isinstance(event_start, datetime):
                target_time = event_start

        for t in direct_tasks:
            p_start = t.get("planned_start")
            if p_start:
                dt = datetime.fromisoformat(p_start) if isinstance(p_start, str) else p_start
                if target_time is None or dt < target_time:
                    target_time = dt

        if target_time:
            hours_rem = (target_time - now).total_seconds() / 3600.0
            if hours_rem <= 2.0:
                time_score = 100.0
                time_desc = f"Critical time pressure: only {max(hours_rem, 0):.1f} hours remaining"
            elif hours_rem <= 6.0:
                time_score = 75.0
                time_desc = f"High time pressure: {hours_rem:.1f} hours remaining"
            elif hours_rem <= 24.0:
                time_score = 50.0
                time_desc = f"Moderate time pressure: {hours_rem:.1f} hours remaining"
            else:
                time_score = 20.0
                time_desc = f"Ample time remaining: {hours_rem:.1f} hours"

        factors.append({
            "name": "time_remaining",
            "score": time_score,
            "weight": 0.15,
            "weighted_score": round(time_score * 0.15, 2),
            "description": time_desc,
        })

        # 2. TASK CRITICALITY (Weight: 0.20)
        task_score = 15.0
        task_desc = "Low priority task affected"
        priorities = [t.get("priority") for t in direct_tasks if t.get("priority")]

        if TaskPriority.CRITICAL.value in priorities:
            task_score = 100.0
            task_desc = "At least one CRITICAL priority task directly affected"
        elif TaskPriority.HIGH.value in priorities:
            task_score = 75.0
            task_desc = "At least one HIGH priority task directly affected"
        elif TaskPriority.MEDIUM.value in priorities:
            task_score = 45.0
            task_desc = "MEDIUM priority tasks affected"
        elif not direct_tasks:
            task_score = 30.0
            task_desc = "General incident without specific direct task"

        factors.append({
            "name": "task_criticality",
            "score": task_score,
            "weight": 0.20,
            "weighted_score": round(task_score * 0.20, 2),
            "description": task_desc,
        })

        # 3. DEPENDENCY COUNT & DEPTH (Weight: 0.15)
        downstream_count = len(indirect_tasks)
        if downstream_count >= 5 or dep_depth >= 3:
            dep_score = 100.0
            dep_desc = f"Severe propagation: {downstream_count} downstream tasks across depth {dep_depth}"
        elif downstream_count >= 2 or dep_depth >= 2:
            dep_score = 75.0
            dep_desc = f"High propagation: {downstream_count} downstream tasks across depth {dep_depth}"
        elif downstream_count >= 1:
            dep_score = 45.0
            dep_desc = f"Moderate propagation: {downstream_count} downstream task affected"
        else:
            dep_score = 10.0
            dep_desc = "No downstream tasks affected (isolated leaf task)"

        factors.append({
            "name": "dependency_count_and_depth",
            "score": dep_score,
            "weight": 0.15,
            "weighted_score": round(dep_score * 0.15, 2),
            "description": dep_desc,
        })

        # 4. SCHEDULE SLACK (Weight: 0.15)
        rem_slack = schedule_impact.get("remaining_slack")
        avail_slack = schedule_impact.get("available_slack", schedule_impact.get("slack_consumed"))
        cp_breach = schedule_impact.get("critical_path_breached", False)
        delay = schedule_impact.get("delay_minutes", 0)

        if cp_breach or (rem_slack is not None and rem_slack <= 0):
            slack_score = 100.0
            slack_desc = "Critical path breached or zero slack remaining"
        elif avail_slack is not None and delay > avail_slack:
            slack_score = 80.0
            slack_desc = f"Delay ({delay}m) exceeds available slack ({avail_slack}m)"
        elif rem_slack is not None and rem_slack < 30:
            slack_score = 50.0
            slack_desc = f"Low schedule buffer remaining ({rem_slack}m)"
        else:
            slack_score = 15.0
            slack_desc = f"Adequate schedule slack available ({rem_slack if rem_slack is not None else 'N/A'}m)"

        factors.append({
            "name": "schedule_slack",
            "score": slack_score,
            "weight": 0.15,
            "weighted_score": round(slack_score * 0.15, 2),
            "description": slack_desc,
        })

        # 5. RESOURCE AVAILABILITY (Weight: 0.10)
        res_count = len(affected_resources)
        if res_count >= 2:
            res_score = 90.0
            res_desc = f"{res_count} operational resources affected or shortage detected"
        elif res_count == 1:
            res_score = 60.0
            res_desc = "1 operational resource affected"
        else:
            res_score = 10.0
            res_desc = "No resource shortages detected"

        factors.append({
            "name": "resource_availability",
            "score": res_score,
            "weight": 0.10,
            "weighted_score": round(res_score * 0.10, 2),
            "description": res_desc,
        })

        # 6. PROVIDER ALTERNATIVES (Weight: 0.10)
        prov_affected = len(affected_providers) > 0
        if prov_affected and alternative_providers_count == 0:
            prov_score = 100.0
            prov_desc = "Provider affected with zero alternative vendors available in network"
        elif prov_affected and alternative_providers_count <= 2:
            prov_score = 60.0
            prov_desc = f"Provider affected with limited alternatives ({alternative_providers_count} available)"
        elif prov_affected:
            prov_score = 25.0
            prov_desc = f"Provider affected but alternatives exist ({alternative_providers_count} available)"
        else:
            prov_score = 0.0
            prov_desc = "No provider/vendor disruption involved"

        factors.append({
            "name": "provider_alternatives",
            "score": prov_score,
            "weight": 0.10,
            "weighted_score": round(prov_score * 0.10, 2),
            "description": prov_desc,
        })

        # 7. BUDGET HEADROOM (Weight: 0.05)
        cost_at_risk = budget_impact.get("committed_cost_at_risk", 0.0)
        total_budget = (
            float(event.get("total_budget", 0)) if isinstance(event, dict)
            else float(getattr(event, "total_budget", 0) or 0)
        ) if event else 0.0

        if total_budget > 0 and (cost_at_risk / total_budget) >= 0.25:
            budget_score = 90.0
            budget_desc = f"High budget exposure: ${cost_at_risk:,.2f} ({round(cost_at_risk / total_budget * 100)}% of total budget)"
        elif cost_at_risk > 0:
            budget_score = 50.0
            budget_desc = f"Moderate budget exposure: ${cost_at_risk:,.2f}"
        else:
            budget_score = 10.0
            budget_desc = "Negligible or zero budget exposure"

        factors.append({
            "name": "budget_headroom",
            "score": budget_score,
            "weight": 0.05,
            "weighted_score": round(budget_score * 0.05, 2),
            "description": budget_desc,
        })

        # 8. OBJECTIVE CRITICALITY (Weight: 0.10)
        critical_objs = [o for o in affected_objectives if o.get("priority") == "CRITICAL"]
        high_objs = [o for o in affected_objectives if o.get("priority") == "HIGH"]

        if critical_objs:
            obj_score = 100.0
            obj_desc = f"{len(critical_objs)} CRITICAL objective(s) threatened"
        elif high_objs:
            obj_score = 65.0
            obj_desc = f"{len(high_objs)} HIGH priority objective(s) threatened"
        elif affected_objectives:
            obj_score = 35.0
            obj_desc = f"{len(affected_objectives)} objective(s) at risk"
        else:
            obj_score = 0.0
            obj_desc = "No strategic objectives threatened"

        factors.append({
            "name": "objective_criticality",
            "score": obj_score,
            "weight": 0.10,
            "weighted_score": round(obj_score * 0.10, 2),
            "description": obj_desc,
        })

        # Aggregate weighted score
        total_score = sum(f["weighted_score"] for f in factors)
        # Normalize to 0-100
        total_score = round(max(0.0, min(100.0, total_score)), 2)

        risk_level, target_event_state = self._classifier.classify_score(total_score)

        return {
            "incident_id": incident_id,
            "score": total_score,
            "level": risk_level,
            "factors": factors,
            "affected_objectives": [o.get("name", "") for o in affected_objectives],
            "critical_constraints": [c.get("name", "") for c in affected_constraints if c.get("is_hard", False)],
            "target_event_state": target_event_state,
            "calculated_at": utc_now().isoformat(),
        }
