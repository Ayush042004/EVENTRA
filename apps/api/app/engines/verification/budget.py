"""Deterministic Budget Verifier.

Verifies budget totals, headroom, and cost caps using strict Decimal precision.
No floating-point rounding errors are permitted in financial verification.
"""
from decimal import Decimal
from typing import Any, Dict, List
from app.engines.verification.types import (
    BudgetVerificationResult,
    BudgetVerificationStatus,
    VerificationContext,
)


class BudgetVerifier:
    """Verifies event financial integrity and constraint compliance."""

    def verify(self, context: VerificationContext) -> BudgetVerificationResult:
        event = context.event
        budget_items = context.budget_items or []
        constraints = context.constraints or []

        # Get total event budget as Decimal
        raw_budget = getattr(event, "total_budget", Decimal("0.00")) or Decimal("0.00")
        total_budget = Decimal(str(raw_budget))

        currency = getattr(event, "currency", "USD") or "USD"

        total_actual = Decimal("0.00")
        total_estimated = Decimal("0.00")

        for item in budget_items:
            actual = getattr(item, "actual_amount", Decimal("0.00")) or Decimal("0.00")
            estimated = getattr(item, "estimated_amount", Decimal("0.00")) or Decimal("0.00")
            total_actual += Decimal(str(actual))
            total_estimated += Decimal(str(estimated))

        remaining_headroom = total_budget - total_actual

        violations: List[str] = []

        # 1. Check if actual amounts exceed total budget
        if total_actual > total_budget and total_budget > Decimal("0.00"):
            violations.append(
                f"Total actual expenditure ({total_actual} {currency}) exceeds event budget cap ({total_budget} {currency})."
            )

        # 2. Check budget cap constraints
        for c in constraints:
            c_type = getattr(c, "type", "")
            c_val = getattr(c, "parameters", {}) or getattr(c, "value", {})
            if isinstance(c_val, dict) and (c_type == "BUDGET_CAP" or "max_budget" in c_val):
                cap = Decimal(str(c_val.get("max_budget") or c_val.get("budget_cap", 0)))
                if cap > 0 and total_actual > cap:
                    violations.append(
                        f"Expenditure ({total_actual} {currency}) breaches constraint cap ({cap} {currency})."
                    )

        is_valid = len(violations) == 0

        status = BudgetVerificationStatus.BUDGET_VALID if is_valid else BudgetVerificationStatus.BUDGET_EXCEEDED

        return BudgetVerificationResult(
            status=status,
            is_valid=is_valid,
            total_budget=total_budget,
            total_committed=total_actual,
            total_estimated=total_estimated,
            remaining_headroom=remaining_headroom,
            currency=currency,
            violations=violations,
            details={
                "item_count": len(budget_items),
                "total_actual": float(total_actual),
                "total_budget": float(total_budget),
                "headroom": float(remaining_headroom),
            },
        )
