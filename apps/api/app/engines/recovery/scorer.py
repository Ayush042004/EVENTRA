"""Transparent deterministic scoring for feasible recovery options only.

score = risk reduction (0..50) + schedule slack preserved (0..25) +
        objective restoration (0..15) - budget utilization penalty (0..10).
"""
from typing import Dict, List

from app.engines.recovery.types import RecoveryContext, RecoverySimulation


class RecoveryScorer:
    """Ranks feasible options without selecting or executing any option."""

    def score(self, simulation: RecoverySimulation, context: RecoveryContext) -> float:
        before = float(context.risk_result.get("score", 0.0))
        after = float(simulation.risk_after.get("score", before))
        risk_reduction = max(0.0, min(50.0, before - after))
        before_slack = max(1, simulation.schedule_delta.get("slack_before_minutes", 0))
        after_slack = max(0, simulation.schedule_delta.get("slack_after_minutes", 0))
        schedule = min(25.0, 25.0 * after_slack / before_slack)
        before_objectives = simulation.objective_delta.get("before", {})
        after_objectives = simulation.objective_delta.get("after", {})
        restored = sum(1 for key, value in before_objectives.items() if value == "AT_RISK" and key not in after_objectives)
        objective = min(15.0, restored * 15.0)
        budget = max(0.0, float(simulation.budget_delta.get("net_delta", 0.0)))
        budget_penalty = min(10.0, 10.0 * budget / max(float(context.event.total_budget or 1), 1.0))
        return round(risk_reduction + schedule + objective - budget_penalty, 2)

    def rank(self, options: List[Dict]) -> List[Dict]:
        """Stable ranking: score descending, strategy then id tie-breakers."""
        feasible = [option for option in options if option["is_feasible"]]
        feasible.sort(key=lambda option: (-float(option["score"]), option["strategy_type"], option.get("id", "")))
        for index, option in enumerate(feasible, start=1):
            option["rank"] = index
        return feasible


Scorer = RecoveryScorer
