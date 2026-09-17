"""Deterministic Engine: planning.requirement_interpreter

Validates that event requirements are satisfiable within the current plan context.
"""
from typing import Any, Dict, List
from app.schemas.specification import EventSpecification


class RequirementInterpreter:
    """Pure deterministic calculation engine without LLM calls.

    Validates event requirements against planned resources and capacity.
    """

    def validate_requirements(
        self,
        specification: EventSpecification,
        planned_resources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Check that all mandatory requirements have corresponding resources.

        Returns a list of unmet requirement dicts (empty = all satisfied).
        """
        unmet: List[Dict[str, Any]] = []
        resource_names = {r["name"].lower() for r in planned_resources}

        for req in specification.requirements:
            if req.is_mandatory and req.name.lower() not in resource_names:
                unmet.append({
                    "key": req.key,
                    "name": req.name,
                    "category": req.category,
                    "reason": "No corresponding resource allocated",
                })

        return unmet
