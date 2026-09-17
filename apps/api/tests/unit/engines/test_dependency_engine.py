"""Unit tests for Dependency Engine: DependencyGraph and CriticalPathCalculator.

Tests in-memory DAG operations: topological sort, cycle detection,
critical path calculation, and slack analysis using forward and backward passes.
"""
import pytest

from app.engines.dependency.graph import DependencyGraph
from app.engines.dependency.traversal import CriticalPathCalculator, CriticalPathResult


def test_empty_graph():
    """Test graph with no nodes or dependencies."""
    graph = DependencyGraph.from_tasks_and_dependencies([], [])
    assert len(graph.nodes) == 0
    assert graph.topological_sort() == []
    assert graph.detect_cycles() == []
    assert graph.is_acyclic() is True

    cpc = CriticalPathCalculator()
    result = cpc.calculate(graph)
    assert result.total_duration == 0
    assert result.critical_path == []


def test_single_task_graph():
    """Test graph with a single task."""
    tasks = [{"id": "t1", "duration_minutes": 45}]
    graph = DependencyGraph.from_tasks_and_dependencies(tasks, [])

    assert graph.nodes == {"t1"}
    assert graph.topological_sort() == ["t1"]
    assert graph.get_duration("t1") == 45
    assert graph.is_acyclic() is True

    cpc = CriticalPathCalculator()
    result = cpc.calculate(graph)
    assert result.total_duration == 45
    assert result.critical_path == ["t1"]
    assert result.task_timings["t1"].slack == 0
    assert result.task_timings["t1"].is_critical is True


def test_linear_chain_topological_sort_and_critical_path():
    """Test linear chain of tasks: A (30m) -> B (45m) -> C (60m)."""
    tasks = [
        {"id": "A", "duration_minutes": 30},
        {"id": "B", "duration_minutes": 45},
        {"id": "C", "duration_minutes": 60},
    ]
    deps = [
        {"predecessor_task_id": "A", "successor_task_id": "B", "lag_minutes": 0},
        {"predecessor_task_id": "B", "successor_task_id": "C", "lag_minutes": 15},
    ]

    graph = DependencyGraph.from_tasks_and_dependencies(tasks, deps)
    topo = graph.topological_sort()
    assert topo == ["A", "B", "C"]
    assert graph.get_predecessors("B") == ["A"]
    assert graph.get_successors("B") == ["C"]
    assert graph.get_lag("B", "C") == 15

    cpc = CriticalPathCalculator()
    result = cpc.calculate(graph)

    # A: 0..30
    # B: 30..75
    # C: (75 + 15 lag) = 90..150
    assert result.total_duration == 150
    assert result.critical_path == ["A", "B", "C"]
    for tid in ("A", "B", "C"):
        assert result.task_timings[tid].is_critical is True
        assert result.task_timings[tid].slack == 0


def test_diamond_graph_slack_and_critical_path():
    """Test diamond graph with two parallel paths:
        A (10) -> B (50) -> D (20)  [total: 10 + 50 + 20 = 80]  <- CRITICAL
        A (10) -> C (20) -> D (20)  [total: 10 + 20 + 20 = 50]  <- slack = 30
    """
    tasks = [
        {"id": "A", "duration_minutes": 10},
        {"id": "B", "duration_minutes": 50},
        {"id": "C", "duration_minutes": 20},
        {"id": "D", "duration_minutes": 20},
    ]
    deps = [
        {"predecessor_task_id": "A", "successor_task_id": "B"},
        {"predecessor_task_id": "A", "successor_task_id": "C"},
        {"predecessor_task_id": "B", "successor_task_id": "D"},
        {"predecessor_task_id": "C", "successor_task_id": "D"},
    ]

    graph = DependencyGraph.from_tasks_and_dependencies(tasks, deps)
    topo = graph.topological_sort()
    assert topo.index("A") < topo.index("B")
    assert topo.index("A") < topo.index("C")
    assert topo.index("B") < topo.index("D")
    assert topo.index("C") < topo.index("D")

    cpc = CriticalPathCalculator()
    result = cpc.calculate(graph)

    assert result.total_duration == 80
    assert result.critical_path == ["A", "B", "D"]

    # C should have slack of 30 minutes
    assert result.task_timings["C"].slack == 30
    assert result.task_timings["C"].is_critical is False

    # A, B, D should have 0 slack
    assert result.task_timings["A"].slack == 0
    assert result.task_timings["B"].slack == 0
    assert result.task_timings["D"].slack == 0


def test_cycle_detection():
    """Test detecting cycles in a cyclic dependency graph: A -> B -> C -> A."""
    tasks = [
        {"id": "A", "duration_minutes": 10},
        {"id": "B", "duration_minutes": 20},
        {"id": "C", "duration_minutes": 30},
    ]
    deps = [
        {"predecessor_task_id": "A", "successor_task_id": "B"},
        {"predecessor_task_id": "B", "successor_task_id": "C"},
        {"predecessor_task_id": "C", "successor_task_id": "A"},
    ]

    graph = DependencyGraph.from_tasks_and_dependencies(tasks, deps)
    assert graph.is_acyclic() is False

    cycles = graph.detect_cycles()
    assert len(cycles) > 0

    with pytest.raises(ValueError, match="cycles"):
        graph.topological_sort()

    cpc = CriticalPathCalculator()
    with pytest.raises(ValueError, match="cycles"):
        cpc.calculate(graph)
