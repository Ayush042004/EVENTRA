"""Deterministic Engine: dependency.graph

In-memory Directed Acyclic Graph (DAG) representation for task dependencies.
Supports topological sorting, cycle detection, and predecessor/successor queries.
All operations are pure in-memory — no database or network calls.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque


class DependencyGraph:
    """Pure deterministic DAG for task dependency analysis.

    Graph is constructed from task and dependency records, then supports
    topological sort, cycle detection, and path queries.
    """

    def __init__(self):
        self._adjacency: Dict[str, List[str]] = defaultdict(list)  # task_id -> [successor_ids]
        self._reverse: Dict[str, List[str]] = defaultdict(list)    # task_id -> [predecessor_ids]
        self._nodes: Set[str] = set()
        self._durations: Dict[str, int] = {}  # task_id -> duration_minutes
        self._lag: Dict[Tuple[str, str], int] = {}  # (pred_id, succ_id) -> lag_minutes

    @classmethod
    def from_tasks_and_dependencies(
        cls,
        tasks: List[Any],
        dependencies: List[Any],
    ) -> "DependencyGraph":
        """Construct a DependencyGraph from ORM or dict task/dependency records.

        Args:
            tasks: List of task objects/dicts with 'id' and optional 'duration_minutes'.
            dependencies: List of dependency objects/dicts with 'predecessor_task_id',
                         'successor_task_id', and optional 'lag_minutes'.
        """
        graph = cls()

        for task in tasks:
            task_id = task["id"] if isinstance(task, dict) else getattr(task, "id")
            duration = (
                task.get("duration_minutes", 0) if isinstance(task, dict)
                else getattr(task, "duration_minutes", 0)
            )
            graph._nodes.add(task_id)
            graph._durations[task_id] = duration or 0

        for dep in dependencies:
            if isinstance(dep, dict):
                pred_id = dep["predecessor_task_id"]
                succ_id = dep["successor_task_id"]
                lag = dep.get("lag_minutes", 0)
            else:
                pred_id = getattr(dep, "predecessor_task_id")
                succ_id = getattr(dep, "successor_task_id")
                lag = getattr(dep, "lag_minutes", 0)

            graph._adjacency[pred_id].append(succ_id)
            graph._reverse[succ_id].append(pred_id)
            graph._lag[(pred_id, succ_id)] = lag or 0

        return graph

    @property
    def nodes(self) -> Set[str]:
        return self._nodes.copy()

    def get_successors(self, task_id: str) -> List[str]:
        """Get direct successor task IDs."""
        return list(self._adjacency.get(task_id, []))

    def get_predecessors(self, task_id: str) -> List[str]:
        """Get direct predecessor task IDs."""
        return list(self._reverse.get(task_id, []))

    def get_duration(self, task_id: str) -> int:
        """Get task duration in minutes."""
        return self._durations.get(task_id, 0)

    def get_lag(self, pred_id: str, succ_id: str) -> int:
        """Get lag minutes between predecessor and successor."""
        return self._lag.get((pred_id, succ_id), 0)

    def topological_sort(self) -> List[str]:
        """Deterministic topological ordering using Kahn's algorithm.

        Returns:
            List of task IDs in valid execution order.

        Raises:
            ValueError: If the graph contains cycles.
        """
        in_degree: Dict[str, int] = {node: 0 for node in self._nodes}

        for node in self._nodes:
            for succ in self._adjacency.get(node, []):
                in_degree[succ] = in_degree.get(succ, 0) + 1

        # Start with nodes that have no predecessors, sorted for determinism
        queue = deque(sorted(node for node, deg in in_degree.items() if deg == 0))
        result: List[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for succ in sorted(self._adjacency.get(node, [])):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        if len(result) != len(self._nodes):
            raise ValueError(
                f"Dependency graph contains cycles: "
                f"processed {len(result)} of {len(self._nodes)} tasks"
            )

        return result

    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the dependency graph using DFS.

        Returns:
            List of cycles found (each cycle is a list of task IDs).
            Empty list if the graph is acyclic.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {node: WHITE for node in self._nodes}
        parent: Dict[str, Optional[str]] = {node: None for node in self._nodes}
        cycles: List[List[str]] = []

        def dfs(u: str):
            color[u] = GRAY
            for v in self._adjacency.get(u, []):
                if color.get(v, WHITE) == GRAY:
                    # Found a cycle: trace back from u to v
                    cycle = [v]
                    curr = u
                    while curr != v:
                        cycle.append(curr)
                        curr = parent.get(curr)
                        if curr is None:
                            break
                    cycle.append(v)
                    cycle.reverse()
                    cycles.append(cycle)
                elif color.get(v, WHITE) == WHITE:
                    parent[v] = u
                    dfs(v)
            color[u] = BLACK

        for node in sorted(self._nodes):
            if color[node] == WHITE:
                dfs(node)

        return cycles

    def is_acyclic(self) -> bool:
        """Check if the graph is acyclic."""
        try:
            self.topological_sort()
            return True
        except ValueError:
            return False
