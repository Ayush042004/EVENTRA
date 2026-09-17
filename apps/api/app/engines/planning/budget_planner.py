"""Deterministic Engine: planning.budget_planner

Generates budget line items from an EventSpecification's provider
categories, requirements, and event budget allocation.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.schemas.specification import EventSpecification


class BudgetPlanner:
    """Pure deterministic calculation engine without LLM calls.

    Generates budget line items by distributing the total event budget
    across provider categories proportionally.
    """

    def plan_budget(
        self,
        specification: EventSpecification,
        vendor_costs: Optional[Dict[str, Decimal]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate budget line items from specification.

        Distributes total_budget across provider categories. If vendor_costs
        are provided, uses those as estimated amounts for matching categories.

        Args:
            specification: The EventSpecification with provider categories and budget.
            vendor_costs: Optional mapping of category -> known cost from vendor assignments.

        Returns:
            List of dicts representing BudgetItem rows to persist.
        """
        items: List[Dict[str, Any]] = []
        vendor_costs = vendor_costs or {}

        total_budget = Decimal(str(specification.total_budget or 0))
        categories = specification.provider_categories

        if not categories:
            return items

        # Calculate allocation per category
        # Categories with known vendor costs use those; remainder is distributed equally
        known_total = sum(vendor_costs.get(cat, Decimal("0")) for cat in categories)
        remaining = max(total_budget - known_total, Decimal("0"))
        unknown_categories = [c for c in categories if c not in vendor_costs]
        per_category = (
            remaining / Decimal(str(len(unknown_categories)))
            if unknown_categories
            else Decimal("0")
        )

        for category in categories:
            estimated = vendor_costs.get(category, per_category)
            items.append({
                "name": f"{category.replace('_', ' ').title()} Budget",
                "category": category.upper(),
                "estimated_amount": estimated.quantize(Decimal("0.01")),
                "actual_amount": Decimal("0.00"),
                "currency": specification.currency,
                "status": "PLANNED",
            })

        # Add operations/contingency budget line (10% of total or remainder)
        contingency = (total_budget * Decimal("0.10")).quantize(Decimal("0.01"))
        items.append({
            "name": "Operations & Contingency",
            "category": "OPERATIONS",
            "estimated_amount": contingency,
            "actual_amount": Decimal("0.00"),
            "currency": specification.currency,
            "status": "PLANNED",
        })

        return items
