"""Unit Tests: Deterministic Impact Analysis Engine (Gate 2)

Covers:
- Direct task impact
- Downstream task impact (propagation)
- Upstream exclusion (ancestors never marked downstream affected)
- Blocked task identification
- Dependency chain depth
- Schedule impact (delay, slack consumption, critical path breach, deadline pressure)
- Resource impact
- Provider impact
- Budget impact
- Objective impact
- Constraint impact
- Severity calculation (CRITICAL, HIGH, MEDIUM, LOW)
- Determinism guarantee
"""
from datetime import datetime, timezone, timedelta
from app.engines.impact.analyzer import ImpactAnalyzer
from app.engines.impact.propagation import ImpactPropagation
from app.engines.impact.severity import ImpactSeverityCalculator
from app.engines.dependency.graph import DependencyGraph
from app.models.enums import TaskPriority, TaskStatus, IncidentSeverity


def test_propagation_downstream_and_upstream_exclusion():
    """Verify that downstream descendants are propagated while upstream ancestors are excluded."""
    # Graph: A -> B -> C -> D, and X -> B
    # If B is directly affected:
    # Downstream affected: C, D
    # Directly affected: B
    # Upstream excluded: A, X must NOT be in indirect tasks!
    tasks = [
        {"id": "A", "duration_minutes": 60, "status": TaskStatus.COMPLETED.value},
        {"id": "X", "duration_minutes": 45, "status": TaskStatus.COMPLETED.value},
        {"id": "B", "duration_minutes": 90, "status": TaskStatus.IN_PROGRESS.value},
        {"id": "C", "duration_minutes": 60, "status": TaskStatus.PENDING.value},
        {"id": "D", "duration_minutes": 30, "status": TaskStatus.PENDING.value},
    ]
    dependencies = [
        {"predecessor_task_id": "A", "successor_task_id": "B", "lag_minutes": 0},
        {"predecessor_task_id": "X", "successor_task_id": "B", "lag_minutes": 0},
        {"predecessor_task_id": "B", "successor_task_id": "C", "lag_minutes": 15},
        {"predecessor_task_id": "C", "successor_task_id": "D", "lag_minutes": 0},
    ]

    graph = DependencyGraph.from_tasks_and_dependencies(tasks, dependencies)
    tasks_by_id = {t["id"]: t for t in tasks}
    prop = ImpactPropagation()

    indirect_ids, blocked_ids, affected_deps, max_depth = prop.propagate_task_impact(
        direct_task_ids={"B"},
        graph=graph,
        tasks_by_id=tasks_by_id,
    )

    # Assertions
    assert set(indirect_ids) == {"C", "D"}
    assert "A" not in indirect_ids
    assert "X" not in indirect_ids
    assert "B" not in indirect_ids
    assert blocked_ids == ["C", "D"]
    assert max_depth == 2  # B -> C (1) -> D (2)
    assert len(affected_deps) == 2


def test_severity_calculator_rules():
    """Verify explainable severity calculation based on factual criteria."""
    calc = ImpactSeverityCalculator()

    # 1. Critical Path breach -> CRITICAL
    sev_cp = calc.calculate_severity(
        incident_type="SCHEDULE_DEVIATION",
        direct_tasks=[{"priority": TaskPriority.MEDIUM.value}],
        indirect_tasks=[],
        schedule_impact={"critical_path_breached": True, "delay_minutes": 45},
        affected_objectives=[],
        affected_constraints=[],
        dependency_depth=0,
    )
    assert sev_cp == IncidentSeverity.CRITICAL.value

    # 2. Hard constraint violated -> CRITICAL
    sev_hc = calc.calculate_severity(
        incident_type="VENUE_ISSUE",
        direct_tasks=[{"priority": TaskPriority.LOW.value}],
        indirect_tasks=[],
        schedule_impact={"critical_path_breached": False, "delay_minutes": 10},
        affected_objectives=[],
        affected_constraints=[{"type": "NOISE_CURFEW", "severity": "HARD", "is_hard": True}],
        dependency_depth=0,
    )
    assert sev_hc == IncidentSeverity.CRITICAL.value

    # 3. High propagation with depth >= 2 -> HIGH
    sev_high = calc.calculate_severity(
        incident_type="VENDOR_DELAY",
        direct_tasks=[{"priority": TaskPriority.MEDIUM.value, "slack_minutes": 60}],
        indirect_tasks=[{"id": "1"}, {"id": "2"}, {"id": "3"}],
        schedule_impact={"critical_path_breached": False, "delay_minutes": 30},
        affected_objectives=[],
        affected_constraints=[],
        dependency_depth=2,
    )
    assert sev_high == IncidentSeverity.HIGH.value

    # 4. Isolated task with slack -> LOW
    sev_low = calc.calculate_severity(
        incident_type="RESOURCE_SHORTAGE",
        direct_tasks=[{"priority": TaskPriority.LOW.value, "slack_minutes": 120}],
        indirect_tasks=[],
        schedule_impact={"critical_path_breached": False, "delay_minutes": 0},
        affected_objectives=[],
        affected_constraints=[],
        dependency_depth=0,
    )
    assert sev_low == IncidentSeverity.LOW.value


def test_impact_analyzer_full_pipeline():
    """Verify complete ImpactAnalyzer execution covering tasks, schedule, resources, budget, and objectives."""
    analyzer = ImpactAnalyzer()
    now = datetime(2026, 10, 15, 10, 0, 0)

    tasks = [
        {
            "id": "task-sound-setup",
            "name": "Main Stage Sound Rigging",
            "status": TaskStatus.READY.value,
            "priority": TaskPriority.CRITICAL.value,
            "required_provider_category": "sound",
            "duration_minutes": 120,
            "slack_minutes": 0,
            "is_critical_path": True,
            "planned_start": now,
            "planned_end": now + timedelta(hours=2),
        },
        {
            "id": "task-sound-check",
            "name": "Live Soundcheck",
            "status": TaskStatus.PENDING.value,
            "priority": TaskPriority.HIGH.value,
            "required_provider_category": "sound",
            "duration_minutes": 60,
            "slack_minutes": 0,
            "is_critical_path": True,
            "planned_start": now + timedelta(hours=2),
            "planned_end": now + timedelta(hours=3),
        },
        {
            "id": "task-decor-setup",
            "name": "Hall Floral Decor",
            "status": TaskStatus.READY.value,
            "priority": TaskPriority.LOW.value,
            "required_provider_category": "decoration",
            "duration_minutes": 180,
            "slack_minutes": 120,
            "is_critical_path": False,
            "planned_start": now,
            "planned_end": now + timedelta(hours=3),
        },
    ]

    dependencies = [
        {"predecessor_task_id": "task-sound-setup", "successor_task_id": "task-sound-check", "lag_minutes": 0},
    ]

    resources = [
        {
            "id": "res-pa-speakers",
            "name": "Line Array PA Speakers",
            "type": "EQUIPMENT",
            "quantity": 4,
            "status": "ALLOCATED",
            "allocated_task_id": "task-sound-setup",
        }
    ]

    vendor_assignments = [
        {
            "id": "va-sound",
            "vendor_id": "vnd-sound-pro",
            "category": "sound",
            "status": "CONFIRMED",
            "agreed_cost": 2500.0,
        }
    ]

    budget_items = [
        {
            "id": "bi-sound",
            "category": "sound",
            "description": "Sound engineering contract",
            "committed_amount": 2500.0,
            "estimated_amount": 2500.0,
        }
    ]

    objectives = [
        {
            "id": "obj-acoustics",
            "name": "Flawless Sound Experience",
            "type": "QUALITY",
            "priority": "CRITICAL",
        }
    ]

    incident = {
        "id": "inc-001",
        "incident_type": "VENDOR_NO_SHOW",
        "related_task_id": "task-sound-setup",
        "related_vendor_id": "vnd-sound-pro",
        "evidence_metadata": {"delay_minutes": 120},
    }

    event = {
        "id": "evt-123",
        "end_datetime": now + timedelta(hours=8),
        "total_budget": 10000.0,
    }

    result = analyzer.analyze(
        incident=incident,
        tasks=tasks,
        dependencies=dependencies,
        resources=resources,
        vendor_assignments=vendor_assignments,
        budget_items=budget_items,
        objectives=objectives,
        event=event,
    )

    # Verify structured impact result
    assert result["incident_id"] == "inc-001"
    assert len(result["directly_affected_tasks"]) == 1
    assert result["directly_affected_tasks"][0]["id"] == "task-sound-setup"
    assert len(result["indirectly_affected_tasks"]) == 1
    assert result["indirectly_affected_tasks"][0]["id"] == "task-sound-check"
    assert result["blocked_tasks"][0]["id"] == "task-sound-check"

    # Verify decor task was NOT affected
    all_affected = [t["id"] for t in result["directly_affected_tasks"] + result["indirectly_affected_tasks"]]
    assert "task-decor-setup" not in all_affected

    # Schedule impact
    assert result["schedule_impact"]["critical_path_breached"] is True
    assert result["schedule_impact"]["delay_minutes"] == 120

    # Resource & Provider impact
    assert len(result["affected_resources"]) == 1
    assert result["affected_resources"][0]["id"] == "res-pa-speakers"
    assert len(result["affected_providers"]) == 1
    assert result["affected_providers"][0]["vendor_id"] == "vnd-sound-pro"

    # Budget impact
    assert result["budget_impact"]["committed_cost_at_risk"] == 2500.0

    # Objectives impact
    assert len(result["affected_objectives"]) == 1
    assert result["affected_objectives"][0]["status"] == "AT_RISK"

    # Severity should be CRITICAL
    assert result["severity"] == IncidentSeverity.CRITICAL.value


def test_impact_analysis_determinism():
    """Verify that identical inputs produce exactly the same ImpactResult."""
    analyzer = ImpactAnalyzer()
    now = datetime(2026, 11, 1, 9, 0, 0)
    tasks = [
        {"id": "T1", "name": "Task 1", "duration_minutes": 60, "priority": "HIGH", "status": "PENDING", "slack_minutes": 10, "is_critical_path": False, "planned_start": now, "planned_end": now + timedelta(hours=1)},
        {"id": "T2", "name": "Task 2", "duration_minutes": 30, "priority": "MEDIUM", "status": "PENDING", "slack_minutes": 10, "is_critical_path": False, "planned_start": now + timedelta(hours=1), "planned_end": now + timedelta(hours=1, minutes=30)},
    ]
    deps = [{"predecessor_task_id": "T1", "successor_task_id": "T2", "lag_minutes": 0}]
    incident = {"id": "inc-det", "incident_type": "SCHEDULE_DEVIATION", "related_task_id": "T1", "evidence_metadata": {"delay_minutes": 20}}

    res1 = analyzer.analyze(incident=incident, tasks=tasks, dependencies=deps)
    res2 = analyzer.analyze(incident=incident, tasks=tasks, dependencies=deps)

    # Omit timestamp when testing determinism
    res1.pop("generated_at")
    res2.pop("generated_at")
    assert res1 == res2
