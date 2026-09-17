"""Deterministic Engine: state.deviation

Detects schedule and budget deviations by comparing planned vs actual values.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class ScheduleDeviation:
    """Schedule deviation for a single task."""
    task_id: str
    task_name: str
    deviation_type: str  # LATE_START, LATE_FINISH, EARLY_FINISH
    planned_value: Optional[datetime] = None
    actual_value: Optional[datetime] = None
    deviation_minutes: int = 0


@dataclass
class BudgetDeviation:
    """Aggregated budget deviation."""
    total_budget: Decimal = Decimal("0.00")
    total_spent: Decimal = Decimal("0.00")
    total_estimated: Decimal = Decimal("0.00")
    variance: Decimal = Decimal("0.00")
    is_over_budget: bool = False
    overspend_categories: List[str] = field(default_factory=list)


class DeviationDetector:
    """Pure deterministic deviation detector."""

    def detect_schedule_deviations(
        self,
        tasks: List[Any],
    ) -> List[ScheduleDeviation]:
        """Compare actual vs planned times for all tasks.

        Args:
            tasks: List of Task ORM objects with planned/actual times.

        Returns:
            List of ScheduleDeviation objects for tasks with deviations.
        """
        deviations: List[ScheduleDeviation] = []

        for task in tasks:
            if isinstance(task, dict):
                task_id = task.get("id", "")
                name = task.get("name", "unknown")
                planned_start = task.get("planned_start")
                planned_end = task.get("planned_end")
                actual_start = task.get("actual_start")
                actual_end = task.get("actual_end")
            else:
                task_id = getattr(task, "id", "")
                name = getattr(task, "name", "unknown")
                planned_start = getattr(task, "planned_start", None)
                planned_end = getattr(task, "planned_end", None)
                actual_start = getattr(task, "actual_start", None)
                actual_end = getattr(task, "actual_end", None)

            # Check late start
            if planned_start and actual_start and actual_start > planned_start:
                delta = int((actual_start - planned_start).total_seconds() / 60)
                deviations.append(ScheduleDeviation(
                    task_id=task_id,
                    task_name=name,
                    deviation_type="LATE_START",
                    planned_value=planned_start,
                    actual_value=actual_start,
                    deviation_minutes=delta,
                ))

            # Check late finish
            if planned_end and actual_end and actual_end > planned_end:
                delta = int((actual_end - planned_end).total_seconds() / 60)
                deviations.append(ScheduleDeviation(
                    task_id=task_id,
                    task_name=name,
                    deviation_type="LATE_FINISH",
                    planned_value=planned_end,
                    actual_value=actual_end,
                    deviation_minutes=delta,
                ))

            # Check early finish
            if planned_end and actual_end and actual_end < planned_end:
                delta = int((planned_end - actual_end).total_seconds() / 60)
                deviations.append(ScheduleDeviation(
                    task_id=task_id,
                    task_name=name,
                    deviation_type="EARLY_FINISH",
                    planned_value=planned_end,
                    actual_value=actual_end,
                    deviation_minutes=-delta,
                ))

        return deviations

    def detect_budget_deviation(
        self,
        budget_items: List[Any],
        total_budget: Decimal,
    ) -> BudgetDeviation:
        """Detect budget deviation by comparing actual spend vs total budget.

        Args:
            budget_items: List of BudgetItem records.
            total_budget: The total event budget ceiling.

        Returns:
            BudgetDeviation with variance analysis.
        """
        total_budget = Decimal(str(total_budget))
        total_spent = Decimal("0.00")
        total_estimated = Decimal("0.00")
        category_spend: Dict[str, Decimal] = {}
        category_est: Dict[str, Decimal] = {}

        for item in budget_items:
            if isinstance(item, dict):
                act = Decimal(str(item.get("actual_amount", 0)))
                est = Decimal(str(item.get("estimated_amount", 0)))
                cat = item.get("category", "UNKNOWN")
            else:
                act = Decimal(str(getattr(item, "actual_amount", 0)))
                est = Decimal(str(getattr(item, "estimated_amount", 0)))
                cat = getattr(item, "category", "UNKNOWN")

            total_spent += act
            total_estimated += est
            category_spend[cat] = category_spend.get(cat, Decimal("0.00")) + act
            category_est[cat] = category_est.get(cat, Decimal("0.00")) + est

        overspend_cats = [
            cat for cat, spend in category_spend.items()
            if spend > category_est.get(cat, Decimal("0.00"))
        ]

        return BudgetDeviation(
            total_budget=total_budget.quantize(Decimal("0.01")),
            total_spent=total_spent.quantize(Decimal("0.01")),
            total_estimated=total_estimated.quantize(Decimal("0.01")),
            variance=(total_budget - total_spent).quantize(Decimal("0.01")),
            is_over_budget=total_spent > total_budget,
            overspend_categories=overspend_cats,
        )
