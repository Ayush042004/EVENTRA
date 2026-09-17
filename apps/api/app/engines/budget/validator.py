"""Deterministic Engine: budget.validator

Validates budget items against the total event budget ceiling,
detecting overspend and per-category violations.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List


@dataclass
class BudgetViolation:
    """A single budget validation violation."""
    category: str
    violation_type: str  # OVERSPEND, UNALLOCATED, EXCEEDED_CATEGORY_CAP
    amount: Decimal
    description: str


class BudgetValidator:
    """Pure deterministic budget validator."""

    def validate_budget(
        self,
        total_budget: Decimal,
        budget_items: List[Any],
        category_caps: Dict[str, Decimal] = None,
    ) -> List[BudgetViolation]:
        """Check for budget violations.

        Args:
            total_budget: The total event budget ceiling.
            budget_items: List of BudgetItem records.
            category_caps: Optional per-category spending limits.

        Returns:
            List of BudgetViolation objects. Empty list = budget is valid.
        """
        violations: List[BudgetViolation] = []
        total_budget = Decimal(str(total_budget))
        category_caps = category_caps or {}

        total_estimated = Decimal("0.00")
        total_actual = Decimal("0.00")
        category_totals: Dict[str, Decimal] = {}

        for item in budget_items:
            if isinstance(item, dict):
                est = Decimal(str(item.get("estimated_amount", 0)))
                act = Decimal(str(item.get("actual_amount", 0)))
                cat = item.get("category", "UNKNOWN")
            else:
                est = Decimal(str(getattr(item, "estimated_amount", 0)))
                act = Decimal(str(getattr(item, "actual_amount", 0)))
                cat = getattr(item, "category", "UNKNOWN")

            total_estimated += est
            total_actual += act
            category_totals[cat] = category_totals.get(cat, Decimal("0.00")) + est

        # Check total estimated overspend
        if total_estimated > total_budget:
            overspend = (total_estimated - total_budget).quantize(Decimal("0.01"))
            violations.append(BudgetViolation(
                category="TOTAL",
                violation_type="OVERSPEND",
                amount=overspend,
                description=(
                    f"Total estimated budget ({total_estimated}) exceeds "
                    f"event budget ceiling ({total_budget}) by {overspend}"
                ),
            ))

        # Check actual spending overspend
        if total_actual > total_budget:
            overspend = (total_actual - total_budget).quantize(Decimal("0.01"))
            violations.append(BudgetViolation(
                category="TOTAL",
                violation_type="OVERSPEND",
                amount=overspend,
                description=(
                    f"Total actual spending ({total_actual}) exceeds "
                    f"event budget ceiling ({total_budget}) by {overspend}"
                ),
            ))

        # Check per-category caps
        for cat, cap in category_caps.items():
            cap = Decimal(str(cap))
            cat_total = category_totals.get(cat, Decimal("0.00"))
            if cat_total > cap:
                overspend = (cat_total - cap).quantize(Decimal("0.01"))
                violations.append(BudgetViolation(
                    category=cat,
                    violation_type="EXCEEDED_CATEGORY_CAP",
                    amount=overspend,
                    description=(
                        f"Category '{cat}' estimated ({cat_total}) exceeds "
                        f"cap ({cap}) by {overspend}"
                    ),
                ))

        return violations
