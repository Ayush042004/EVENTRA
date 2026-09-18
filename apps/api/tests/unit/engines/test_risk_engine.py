"""Unit Tests: Deterministic Risk Engine (Gate 3)

Covers:
- Evaluation of all 8 explicit risk factors
- Threshold mapping to risk levels and EventState
- Low, Medium, High, and Critical risk scenarios
- Contributing factor breakdown
- Risk calculation determinism
"""
from datetime import datetime, timezone, timedelta
from app.engines.risk.calculator import RiskCalculator
from app.engines.risk.classifier import RiskClassifier
from app.models.enums import EventState, IncidentSeverity, TaskPriority


def test_risk_classifier_thresholds():
    """Verify exact threshold mapping from 0-100 scores to risk levels and EventState."""
    classifier = RiskClassifier()

    # LOW: 0 - 24.9 -> NORMAL
    lvl, state = classifier.classify_score(0.0)
    assert lvl == IncidentSeverity.LOW.value
    assert state == EventState.NORMAL.value

    lvl, state = classifier.classify_score(24.5)
    assert lvl == IncidentSeverity.LOW.value
    assert state == EventState.NORMAL.value

    # MEDIUM: 25.0 - 49.9 -> AT_RISK
    lvl, state = classifier.classify_score(25.0)
    assert lvl == IncidentSeverity.MEDIUM.value
    assert state == EventState.AT_RISK.value

    lvl, state = classifier.classify_score(48.0)
    assert lvl == IncidentSeverity.MEDIUM.value
    assert state == EventState.AT_RISK.value

    # HIGH: 50.0 - 74.9 -> CRITICAL
    lvl, state = classifier.classify_score(50.0)
    assert lvl == IncidentSeverity.HIGH.value
    assert state == EventState.CRITICAL.value

    lvl, state = classifier.classify_score(74.0)
    assert lvl == IncidentSeverity.HIGH.value
    assert state == EventState.CRITICAL.value

    # CRITICAL: 75.0 - 100.0 -> EMERGENCY
    lvl, state = classifier.classify_score(75.0)
    assert lvl == IncidentSeverity.CRITICAL.value
    assert state == EventState.EMERGENCY.value

    lvl, state = classifier.classify_score(100.0)
    assert lvl == IncidentSeverity.CRITICAL.value
    assert state == EventState.EMERGENCY.value


def test_risk_calculator_critical_factors():
    """Verify risk calculation under high-severity conditions yields CRITICAL / EMERGENCY."""
    calc = RiskCalculator()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    incident = {"id": "inc-crit", "title": "Vendor No-Show"}
    event = {
        "id": "evt-1",
        "start_datetime": now + timedelta(hours=1),  # Urgent time pressure
        "total_budget": 5000.0,
    }

    impact_result = {
        "directly_affected_tasks": [
            {
                "id": "T1",
                "name": "Main Audio Rigging",
                "priority": TaskPriority.CRITICAL.value,
                "planned_start": (now + timedelta(hours=1)).isoformat(),
            }
        ],
        "indirectly_affected_tasks": [{"id": f"T{i}"} for i in range(2, 8)],  # 6 downstream tasks
        "dependency_depth": 3,
        "schedule_impact": {
            "critical_path_breached": True,
            "slack_consumed": 0,
            "delay_minutes": 120,
        },
        "affected_resources": [{"id": "r1"}, {"id": "r2"}],
        "affected_providers": [{"vendor_id": "v1"}],
        "budget_impact": {"committed_cost_at_risk": 2000.0},  # 40% of budget
        "affected_objectives": [{"name": "Keynote Broadcast", "priority": "CRITICAL"}],
        "affected_constraints": [{"name": "Sound Curfew", "is_hard": True}],
    }

    result = calc.calculate(
        incident=incident,
        impact_result=impact_result,
        event=event,
        alternative_providers_count=0,  # Zero alternatives
    )

    # Score should be high (>= 75.0) resulting in CRITICAL level and EMERGENCY state
    assert result["score"] >= 75.0
    assert result["level"] == IncidentSeverity.CRITICAL.value
    assert result["target_event_state"] == EventState.EMERGENCY.value

    # Verify factors exist and have non-empty explanations
    assert len(result["factors"]) == 8
    for f in result["factors"]:
        assert "name" in f
        assert "score" in f
        assert "weight" in f
        assert "description" in f


def test_risk_calculator_low_factors():
    """Verify risk calculation under minor isolated conditions yields LOW / NORMAL."""
    calc = RiskCalculator()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    incident = {"id": "inc-minor", "title": "Minor delivery delay"}
    event = {
        "id": "evt-2",
        "start_datetime": now + timedelta(days=5),  # 5 days away
        "total_budget": 50000.0,
    }

    impact_result = {
        "directly_affected_tasks": [
            {
                "id": "T-decor",
                "name": "Signage Placement",
                "priority": TaskPriority.LOW.value,
                "planned_start": (now + timedelta(days=3)).isoformat(),
            }
        ],
        "indirectly_affected_tasks": [],  # Isolated task
        "dependency_depth": 0,
        "schedule_impact": {
            "critical_path_breached": False,
            "slack_consumed": 180,  # Ample slack
            "delay_minutes": 15,
        },
        "affected_resources": [],
        "affected_providers": [],
        "budget_impact": {"committed_cost_at_risk": 0.0},
        "affected_objectives": [],
        "affected_constraints": [],
    }

    result = calc.calculate(
        incident=incident,
        impact_result=impact_result,
        event=event,
        alternative_providers_count=3,
    )

    assert result["score"] < 25.0
    assert result["level"] == IncidentSeverity.LOW.value
    assert result["target_event_state"] == EventState.NORMAL.value


def test_risk_calculation_determinism():
    """Verify that identical inputs produce identical risk results."""
    calc = RiskCalculator()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    incident = {"id": "inc-det", "title": "Determinism Test"}
    impact_result = {
        "directly_affected_tasks": [{"id": "T1", "priority": "HIGH", "planned_start": (now + timedelta(hours=5)).isoformat()}],
        "indirectly_affected_tasks": [{"id": "T2"}],
        "dependency_depth": 1,
        "schedule_impact": {"critical_path_breached": False, "slack_consumed": 30, "delay_minutes": 20},
        "affected_resources": [],
        "affected_providers": [],
        "budget_impact": {"committed_cost_at_risk": 100.0},
        "affected_objectives": [],
        "affected_constraints": [],
    }

    res1 = calc.calculate(incident=incident, impact_result=impact_result)
    res2 = calc.calculate(incident=incident, impact_result=impact_result)

    res1.pop("calculated_at")
    res2.pop("calculated_at")
    assert res1 == res2
