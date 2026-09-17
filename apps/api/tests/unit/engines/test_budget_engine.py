"""Unit tests for Budget Engine: BudgetCalculator and BudgetValidator.

Verifies deterministic calculation of budget totals, variance, utilization,
and constraint violations using exact Decimal arithmetic for monetary precision.
"""
from decimal import Decimal
import pytest

from app.engines.budget.calculator import BudgetCalculator, BudgetSummary, BudgetVariance
from app.engines.budget.validator import BudgetValidator, BudgetViolation


@pytest.fixture
def sample_budget_items():
    return [
        {
            "id": "b1",
            "name": "Catering Package",
            "category": "CATERING",
            "estimated_amount": Decimal("15000.00"),
            "actual_amount": Decimal("14500.00"),
        },
        {
            "id": "b2",
            "name": "Venue Rental",
            "category": "VENUE",
            "estimated_amount": Decimal("20000.00"),
            "actual_amount": Decimal("22000.00"),
        },
        {
            "id": "b3",
            "name": "AV and Sound",
            "category": "AV",
            "estimated_amount": Decimal("5000.00"),
            "actual_amount": Decimal("4800.00"),
        },
    ]


def test_budget_calculator_totals(sample_budget_items):
    """Test sum of estimated and actual amounts with category breakdown."""
    calc = BudgetCalculator()
    summary = calc.calculate_totals(sample_budget_items)

    assert summary.total_estimated == Decimal("40000.00")
    assert summary.total_actual == Decimal("41300.00")
    assert summary.item_count == 3
    assert summary.categories["CATERING"] == Decimal("15000.00")
    assert summary.categories["VENUE"] == Decimal("20000.00")
    assert summary.categories["AV"] == Decimal("5000.00")


def test_budget_calculator_variance(sample_budget_items):
    """Test variance analysis against total event budget ceiling."""
    calc = BudgetCalculator()

    # Total budget = 50,000 (actual = 41,300, not over budget)
    var_ok = calc.calculate_variance(Decimal("50000.00"), sample_budget_items)
    assert var_ok.is_over_budget is False
    assert var_ok.variance_actual == Decimal("8700.00")
    assert var_ok.utilization_percent == Decimal("82.60")

    # Total budget = 40,000 (actual = 41,300, is over budget)
    var_over = calc.calculate_variance(Decimal("40000.00"), sample_budget_items)
    assert var_over.is_over_budget is True
    assert var_over.variance_actual == Decimal("-1300.00")


def test_budget_validator_valid(sample_budget_items):
    """Test validator returns no violations when within budget."""
    validator = BudgetValidator()
    violations = validator.validate_budget(Decimal("50000.00"), sample_budget_items)
    assert len(violations) == 0


def test_budget_validator_overspend(sample_budget_items):
    """Test validator detects total overspend violations."""
    validator = BudgetValidator()
    # Total budget = 35000 (estimated = 40000, actual = 41300)
    violations = validator.validate_budget(Decimal("35000.00"), sample_budget_items)

    assert len(violations) >= 1
    types = [v.violation_type for v in violations]
    assert "OVERSPEND" in types


def test_budget_validator_category_caps(sample_budget_items):
    """Test validator detects per-category cap violations."""
    validator = BudgetValidator()
    category_caps = {"AV": Decimal("4000.00")}  # estimated is 5000

    violations = validator.validate_budget(
        Decimal("60000.00"), sample_budget_items, category_caps=category_caps
    )
    assert len(violations) == 1
    assert violations[0].category == "AV"
    assert violations[0].violation_type == "EXCEEDED_CATEGORY_CAP"
    assert violations[0].amount == Decimal("1000.00")
