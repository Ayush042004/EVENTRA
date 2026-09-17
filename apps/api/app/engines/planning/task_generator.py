"""Deterministic Engine: planning.task_generator

Converts domain TaskDefinition baselines from an EventSpecification
into materializable task dictionaries ready for database persistence.
"""
from typing import Any, Dict, List
from app.schemas.specification import EventSpecification
from app.models.enums import TaskStatus


class TaskGenerator:
    """Pure deterministic calculation engine without LLM calls.

    Transforms EventSpecification baseline TaskDefinitions into
    flat task dicts suitable for ORM materialization.
    """

    def generate_tasks(self, specification: EventSpecification) -> List[Dict[str, Any]]:
        """Generate materializable task records from an EventSpecification.

        Returns a list of dicts, each representing one Task row to persist.
        """
        tasks: List[Dict[str, Any]] = []

        for task_def in specification.tasks:
            tasks.append({
                "key": task_def.key,
                "name": task_def.name,
                "description": task_def.description or "",
                "status": TaskStatus.PENDING.value,
                "priority": task_def.priority.value if hasattr(task_def.priority, "value") else str(task_def.priority),
                "phase": task_def.phase or "SETUP",
                "required_provider_category": task_def.required_provider_category,
                "duration_minutes": task_def.estimated_duration_minutes,
                "is_critical_path": task_def.is_critical,
            })

        return tasks
