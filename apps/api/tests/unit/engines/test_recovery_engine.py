"""Unit tests for Phase 8 Recovery Engine components (Generator, Simulator, Validator, Scorer)."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.engines.recovery.generator import RecoveryGenerator
from app.engines.recovery.simulator import RecoverySimulator
from app.engines.recovery.validator import RecoveryValidator
from app.engines.recovery.scorer import RecoveryScorer
from app.engines.recovery.types import (
    RecoveryCandidate,
    RecoveryContext,
    RecoveryStrategy,
    ValidationResult,
)


@dataclass
class MockEvent:
    id: str = "evt-1"
    name: str = "Test Fest"
    start_datetime: datetime = datetime.now(timezone.utc).replace(tzinfo=None)
    end_datetime: datetime = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8)
    total_budget: Decimal = Decimal("5000.00")
    guest_count: int = 500


@dataclass
class MockIncident:
    id: str = "inc-1"
    incident_type: str = "VENDOR_NO_SHOW"
    related_task_id: str = "task-1"
    related_vendor_id: str = "vendor-a"
    related_resource_id: str = None
    related_venue_id: str = None
    evidence_metadata: dict = None

    def __post_init__(self):
        if self.evidence_metadata is None:
            self.evidence_metadata = {"delay_minutes": 30, "provider_eta_minutes": {"vendor-b": 15}}


@dataclass
class MockTask:
    id: str
    name: str
    status: str = "PENDING"
    priority: str = "HIGH"
    phase: str = "EXECUTION"
    required_provider_category: str = "CATERING"
    duration_minutes: int = 45
    slack_minutes: int = 60
    is_critical_path: bool = False
    planned_start: datetime = None
    planned_end: datetime = None


@dataclass
class MockVendor:
    id: str
    name: str
    category: str = "catering"
    status: str = "ACTIVE"
    base_cost: float = 300.0
    availabilities: list = None

    def __post_init__(self):
        if self.availabilities is None:
            self.availabilities = []


@dataclass
class MockVendorAssignment:
    id: str = "assign-1"
    vendor_id: str = "vendor-a"
    category: str = "catering"
    agreed_cost: float = 250.0


@dataclass
class MockResource:
    id: str
    type: str = "EQUIPMENT"
    status: str = "AVAILABLE"
    quantity: int = 5


@dataclass
class MockConstraint:
    id: str
    name: str
    type: str
    severity: str = "HARD"
    value: dict = None


def _build_test_context(
    delay: int = 30,
    provider_cost_b: float = 300.0,
    vendor_b_status: str = "ACTIVE",
    resource_status: str = "AVAILABLE",
) -> RecoveryContext:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event = MockEvent(start_datetime=now, end_datetime=now + timedelta(hours=6))
    incident = MockIncident(
        evidence_metadata={
            "delay_minutes": delay,
            "provider_eta_minutes": {"vendor-b": 15},
            "compressible_task_ids": ["task-1"],
            "max_compression_minutes": 15,
        }
    )
    t1 = MockTask(id="task-1", name="Caterer Setup", duration_minutes=45, planned_start=now, planned_end=now + timedelta(minutes=45))
    t2 = MockTask(id="task-2", name="Food Service Ready", duration_minutes=30, planned_start=now + timedelta(minutes=45), planned_end=now + timedelta(minutes=75))
    v_a = MockVendor(id="vendor-a", name="Caterer A", base_cost=250.0)
    v_b = MockVendor(id="vendor-b", name="Caterer B", base_cost=provider_cost_b, status=vendor_b_status)
    assignment = MockVendorAssignment(vendor_id="vendor-a", agreed_cost=250.0)
    res = MockResource(id="res-1", status=resource_status)

    impact_res = {
        "directly_affected_tasks": [{"id": "task-1"}],
        "schedule_impact": {"delay_minutes": delay},
        "affected_objectives": [{"id": "obj-1", "status": "AT_RISK"}],
        "affected_constraints": [],
    }
    risk_res = {
        "score": 75.0,
        "level": "HIGH",
        "primary_risk_factor": "VENDOR_FAILURE",
        "contributing_factors": ["Schedule Pressure"],
    }

    return RecoveryContext(
        event=event,
        incident=incident,
        impact_result=impact_res,
        risk_result=risk_res,
        tasks=[t1, t2],
        dependencies=[],
        budget_items=[],
        resources=[res],
        providers=[v_a, v_b],
        provider_assignments=[assignment],
        venue=None,
        objectives=[{"id": "obj-1", "name": "On-Time Catering"}],
        constraints=[],
        live_state={"status": "NORMAL"},
        snapshot_version="v1-snap",
    )


class TestRecoveryGenerator:

    def test_generate_candidates_for_vendor_no_show(self):
        context = _build_test_context()
        generator = RecoveryGenerator()
        candidates = generator.generate_candidates(context)

        strategies = [c.strategy_type for c in candidates]
        assert RecoveryStrategy.WAIT in strategies
        assert RecoveryStrategy.BACKUP in strategies
        assert RecoveryStrategy.REASSIGN in strategies
        assert RecoveryStrategy.RESCHEDULE in strategies
        assert RecoveryStrategy.COMPRESS in strategies

    def test_generator_skips_provider_without_cost(self):
        context = _build_test_context(provider_cost_b=None)
        generator = RecoveryGenerator()
        candidates = generator.generate_candidates(context)

        # Provider without base_cost must NOT be generated as backup or reassign
        assert not any(c.strategy_type == RecoveryStrategy.BACKUP for c in candidates)
        assert not any(c.strategy_type == RecoveryStrategy.REASSIGN for c in candidates)

    def test_generator_resource_shortage_candidate(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = MockEvent(start_datetime=now, end_datetime=now + timedelta(hours=4))
        incident = MockIncident(
            incident_type="RESOURCE_SHORTAGE",
            related_task_id="task-1",
            related_resource_id="res-1",
            evidence_metadata={"shortage_quantity": 2},
        )
        r1 = MockResource(id="res-1", type="EQUIPMENT", status="DEFECTIVE", quantity=0)
        r2 = MockResource(id="res-2", type="EQUIPMENT", status="AVAILABLE", quantity=5)
        t1 = MockTask(id="task-1", name="Audio Setup")

        context = RecoveryContext(
            event=event,
            incident=incident,
            impact_result={"directly_affected_tasks": [{"id": "task-1"}]},
            risk_result={"score": 50.0},
            tasks=[t1],
            dependencies=[],
            budget_items=[],
            resources=[r1, r2],
            providers=[],
            provider_assignments=[],
            venue=None,
            objectives=[],
            constraints=[],
            live_state={},
            snapshot_version="v-res",
        )

        candidates = RecoveryGenerator().generate_candidates(context)
        reassign_res = [c for c in candidates if c.strategy_type == RecoveryStrategy.REASSIGN and "res-2" in c.affected_resource_ids]
        assert len(reassign_res) == 1


class TestRecoverySimulator:

    def test_simulation_does_not_mutate_context_objects(self):
        context = _build_test_context()
        orig_start = context.tasks[0].planned_start
        orig_end = context.tasks[0].planned_end

        candidates = RecoveryGenerator().generate_candidates(context)
        backup_cand = next(c for c in candidates if c.strategy_type == RecoveryStrategy.BACKUP)

        simulator = RecoverySimulator()
        sim = simulator.simulate(backup_cand, context)

        # Context task objects must remain completely unchanged
        assert context.tasks[0].planned_start == orig_start
        assert context.tasks[0].planned_end == orig_end

        # Simulation must return structured deltas
        assert "slack_after_minutes" in sim.schedule_delta
        assert "additional_cost" in sim.budget_delta
        assert "score" in sim.risk_after


class TestRecoveryValidator:

    def test_validator_rejects_inactive_provider(self):
        context = _build_test_context(vendor_b_status="INACTIVE")
        simulator = RecoverySimulator()
        validator = RecoveryValidator()

        # Construct candidate manually to test validator logic when candidate references an inactive provider
        backup_cand = RecoveryCandidate(
            strategy_type=RecoveryStrategy.BACKUP,
            affected_task_ids=["task-1"],
            affected_provider_ids=["vendor-b"],
            proposed_changes={"provider_cost": 300.0, "delay_minutes": 15},
        )

        sim = simulator.simulate(backup_cand, context)
        res = validator.validate(sim, context)

        assert res.feasible is False
        assert any("not active" in v for v in res.violations)


    def test_validator_detects_hard_constraint_violation(self):
        context = _build_test_context(delay=120)
        # Add hard deadline constraint
        deadline = context.event.start_datetime + timedelta(minutes=60)
        context.constraints = [
            MockConstraint(
                id="c-1",
                name="Strict Catering Deadline",
                type="TIME_WINDOW",
                severity="HARD",
                value={"end_datetime": deadline.isoformat()},
            )
        ]

        simulator = RecoverySimulator()
        validator = RecoveryValidator()
        candidate = RecoveryCandidate(
            strategy_type=RecoveryStrategy.RESCHEDULE,
            affected_task_ids=["task-1"],
            proposed_changes={"delay_minutes": 120},
        )
        sim = simulator.simulate(candidate, context)
        res = validator.validate(sim, context)

        assert res.feasible is False
        assert any("Strict Catering Deadline" in v for v in res.violations)


class TestRecoveryScorer:

    def test_scorer_transparent_formula_and_ranking(self):
        context = _build_test_context()
        simulator = RecoverySimulator()
        scorer = RecoveryScorer()

        candidate = RecoveryCandidate(
            strategy_type=RecoveryStrategy.BACKUP,
            affected_task_ids=["task-1"],
            affected_provider_ids=["vendor-b"],
            proposed_changes={"provider_cost": 300.0, "delay_minutes": 15},
        )
        sim = simulator.simulate(candidate, context)
        score = scorer.score(sim, context)
        assert isinstance(score, float)

        options = [
            {"id": "opt-1", "strategy_type": "BACKUP", "is_feasible": True, "score": 42.5},
            {"id": "opt-2", "strategy_type": "WAIT", "is_feasible": True, "score": 68.0},
            {"id": "opt-3", "strategy_type": "RESCHEDULE", "is_feasible": False, "score": None},
        ]
        ranked = scorer.rank(options)
        assert len(ranked) == 2
        assert ranked[0]["id"] == "opt-2" and ranked[0]["rank"] == 1
        assert ranked[1]["id"] == "opt-1" and ranked[1]["rank"] == 2
