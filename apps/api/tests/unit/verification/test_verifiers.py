"""Unit tests for deterministic sub-verifiers in app/engines/verification/"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.engines.verification.budget import BudgetVerifier
from app.engines.verification.constraints import ConstraintVerifier
from app.engines.verification.objectives import ObjectiveVerifier
from app.engines.verification.providers import ProviderVerifier
from app.engines.verification.resources import ResourceVerifier
from app.engines.verification.schedule import ScheduleVerifier
from app.engines.verification.state import StateVerifier
from app.engines.verification.types import (
    BudgetVerificationStatus,
    ObjectiveStatus,
    ProviderVerificationStatus,
    ResourceVerificationStatus,
    ScheduleVerificationStatus,
    VerificationContext,
    VerificationStatus,
)
from app.engines.verification.verifier import VerificationEngine
from app.models.enums import EventState, TaskPriority, TaskStatus


class MockObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _build_base_context(now: datetime) -> VerificationContext:
    event = MockObj(
        id="evt-1",
        name="Tech Gala",
        total_budget=Decimal("50000.00"),
        currency="USD",
        state=EventState.RECOVERY.value,
        end_datetime=now + timedelta(hours=10),
        guest_count=500,
        venue_id=None,
    )
    task1 = MockObj(
        id="task-1",
        name="Main Catering Prep",
        status=TaskStatus.READY.value,
        priority=TaskPriority.CRITICAL.value,
        planned_start=now + timedelta(hours=1),
        planned_end=now + timedelta(hours=3),
        slack_minutes=60,
        required_provider_category="catering",
    )
    dep1 = MockObj(
        predecessor_task_id="task-1",
        successor_task_id="task-2",
        lag_minutes=0,
    )
    task2 = MockObj(
        id="task-2",
        name="Guest Meal Service",
        status=TaskStatus.PENDING.value,
        priority=TaskPriority.HIGH.value,
        planned_start=now + timedelta(hours=3),
        planned_end=now + timedelta(hours=5),
        slack_minutes=60,
        required_provider_category="catering",
    )
    budget_item = MockObj(
        id="bi-1",
        name="Catering Budget",
        category="catering",
        estimated_amount=Decimal("10000.00"),
        actual_amount=Decimal("8000.00"),
    )
    resource = MockObj(
        id="res-1",
        name="Chafing Dishes",
        status="ALLOCATED",
        quantity=10,
        allocated_task_id="task-1",
    )
    vendor = MockObj(
        id="ven-1",
        name="Gourmet Catering Co",
        category="catering",
        status="ACTIVE",
    )
    assignment = MockObj(
        id="va-1",
        vendor_id="ven-1",
        category="catering",
        status="CONFIRMED",
        agreed_cost=Decimal("8000.00"),
    )
    objective = MockObj(
        id="obj-1",
        name="Guest Meal Quality and Readiness",
        priority="CRITICAL",
    )
    constraint = MockObj(
        id="con-1",
        name="Meal Budget Cap",
        type="BUDGET_CAP",
        severity="HARD",
        value={"max_budget": 15000.0},
    )

    action = MockObj(
        id="act-1",
        action_type="REASSIGN_VENDOR",
        action_id="act-uuid-1",
        status="SUCCESS",
        affected_entities=[{"id": "task-1"}],
        execution_payload={"new_vendor_id": "ven-1"},
    )

    return VerificationContext(
        event_id="evt-1",
        event=event,
        action_execution=action,
        action_type="REASSIGN_VENDOR",
        target_type="TASK",
        target_id="task-1",
        payload={"new_vendor_id": "ven-1"},
        tasks=[task1, task2],
        dependencies=[dep1],
        budget_items=[budget_item],
        resources=[resource],
        providers=[vendor],
        vendor_assignments=[assignment],
        objectives=[objective],
        constraints=[constraint],
        current_snapshot="snap-1234",
    )


def test_objective_verifier():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    verifier = ObjectiveVerifier()

    res = verifier.verify(ctx, schedule_feasible=True, deadline_violations=[])
    assert res.status == ObjectiveStatus.SATISFIED.value
    assert res.critical_objectives_satisfied is True
    assert len(res.objectives_evaluated) == 1


def test_schedule_verifier_feasible():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    verifier = ScheduleVerifier()

    res = verifier.verify(ctx)
    assert res.is_feasible is True
    assert res.status in (ScheduleVerificationStatus.SCHEDULE_RESTORED, ScheduleVerificationStatus.SCHEDULE_IMPROVED)
    assert len(res.deadline_violations) == 0


def test_schedule_verifier_deadline_violation():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    # Task 2 ends after event end
    ctx.tasks[1].planned_end = ctx.event.end_datetime + timedelta(hours=2)
    verifier = ScheduleVerifier()

    res = verifier.verify(ctx)
    assert res.is_feasible is False
    assert len(res.deadline_violations) >= 1
    assert res.status == ScheduleVerificationStatus.SCHEDULE_STILL_AT_RISK


def test_budget_verifier_decimal_precision():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    verifier = BudgetVerifier()

    res = verifier.verify(ctx)
    assert res.is_valid is True
    assert res.status == BudgetVerificationStatus.BUDGET_VALID
    assert res.total_committed == Decimal("8000.00")
    assert res.remaining_headroom == Decimal("42000.00")

    # Over budget scenario
    ctx.budget_items[0].actual_amount = Decimal("60000.00")
    res2 = verifier.verify(ctx)
    assert res2.is_valid is False
    assert res2.status == BudgetVerificationStatus.BUDGET_EXCEEDED


def test_resource_verifier():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    verifier = ResourceVerifier()

    res = verifier.verify(ctx)
    assert res.is_valid is True
    assert res.status == ResourceVerificationStatus.RESOURCE_RESTORED

    # Conflict scenario: allocation to non-existent task
    ctx.resources[0].allocated_task_id = "ghost-task-id"
    res_conflict = verifier.verify(ctx)
    assert res_conflict.is_valid is False
    assert len(res_conflict.conflicts) >= 1


def test_provider_verifier():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    verifier = ProviderVerifier()

    res = verifier.verify(ctx)
    assert res.is_valid is True
    assert res.status == ProviderVerificationStatus.PROVIDER_VERIFIED
    assert res.assignment_confirmed is True
    assert res.details["database_confirmed"] is True
    assert res.details["real_world_confirmed"] is False

    # Vendor inactive scenario
    ctx.providers[0].status = "INACTIVE"
    res_inactive = verifier.verify(ctx)
    assert res_inactive.is_valid is False
    assert res_inactive.status == ProviderVerificationStatus.PROVIDER_UNAVAILABLE


def test_constraint_verifier():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    verifier = ConstraintVerifier()

    res = verifier.verify(ctx, schedule_feasible=True, budget_valid=True, deadline_violations=[])
    assert res.hard_constraints_satisfied is True

    # Budget cap violated
    res_breach = verifier.verify(ctx, schedule_feasible=True, budget_valid=False, deadline_violations=[])
    assert res_breach.hard_constraints_satisfied is False
    assert len(res_breach.violations) >= 1


def test_verification_engine_master():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ctx = _build_base_context(now)
    engine = VerificationEngine()

    result = engine.verify(ctx)
    assert result.status == VerificationStatus.VERIFIED
    assert result.event_state_after == EventState.NORMAL.value
    assert len(result.failure_reasons) == 0
