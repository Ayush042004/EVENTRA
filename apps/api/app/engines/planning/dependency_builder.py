"""Deterministic Engine: planning.dependency_builder

Converts domain DependencyDefinition baselines from an EventSpecification
into materializable dependency dictionaries, mapping stable task keys
to actual database task IDs.
"""
from typing import Any, Dict, List
from app.schemas.specification import EventSpecification


class DependencyBuilder:
    """Pure deterministic calculation engine without LLM calls.

    Maps domain DependencyDefinitions (keyed by stable task keys) into
    dependency dicts referencing actual persisted task IDs.
    """

    def build_dependencies(
        self,
        specification: EventSpecification,
        task_key_to_id: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Build materializable dependency records from specification and key-to-ID map.

        Args:
            specification: The EventSpecification containing dependency definitions.
            task_key_to_id: Mapping from stable task keys to persisted task UUIDs.

        Returns:
            List of dicts representing TaskDependency rows to persist.

        Raises:
            ValueError: If a dependency references an unknown task key.
        """
        dependencies: List[Dict[str, Any]] = []

        for dep_def in specification.dependencies:
            pred_id = task_key_to_id.get(dep_def.predecessor_key)
            succ_id = task_key_to_id.get(dep_def.successor_key)

            if not pred_id:
                raise ValueError(
                    f"Predecessor task key '{dep_def.predecessor_key}' not found in persisted tasks"
                )
            if not succ_id:
                raise ValueError(
                    f"Successor task key '{dep_def.successor_key}' not found in persisted tasks"
                )

            dep_type = dep_def.dependency_type
            if hasattr(dep_type, "value"):
                dep_type = dep_type.value

            dependencies.append({
                "predecessor_task_id": pred_id,
                "successor_task_id": succ_id,
                "dependency_type": str(dep_type),
                "lag_minutes": dep_def.lag_minutes,
            })

        return dependencies
