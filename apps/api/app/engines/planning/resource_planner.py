"""Deterministic Engine: planning.resource_planner

Generates resource allocation items from an EventSpecification's
requirements, mapping requirement categories to resource types.
"""
from typing import Any, Dict, List
from app.schemas.specification import EventSpecification


# Map requirement categories to resource types
_CATEGORY_TO_RESOURCE_TYPE: Dict[str, str] = {
    "VENUE": "FACILITY",
    "CATERING": "EQUIPMENT",
    "AV_LIGHTING": "EQUIPMENT",
    "SOUND": "EQUIPMENT",
    "LIGHTING": "EQUIPMENT",
    "STAGE": "EQUIPMENT",
    "DECORATION": "MATERIAL",
    "PHOTOGRAPHY": "EQUIPMENT",
    "VIDEOGRAPHY": "EQUIPMENT",
    "MUSIC": "EQUIPMENT",
    "SECURITY": "STAFF",
    "POWER": "EQUIPMENT",
    "HEAVY_EQUIPMENT": "EQUIPMENT",
    "REGISTRATION": "EQUIPMENT",
    "CONNECTIVITY": "EQUIPMENT",
    "INTERNET": "EQUIPMENT",
    "SIGNAGE": "MATERIAL",
    "TRANSPORTATION": "TRANSPORT",
    "EQUIPMENT": "EQUIPMENT",
    "STAFFING": "STAFF",
    "GENERAL": "MATERIAL",
}


class ResourcePlanner:
    """Pure deterministic calculation engine without LLM calls.

    Generates resource allocation items from event requirements.
    """

    def plan_resources(self, specification: EventSpecification) -> List[Dict[str, Any]]:
        """Generate resource records from specification requirements.

        Each mandatory requirement produces a resource allocation item.
        """
        resources: List[Dict[str, Any]] = []

        for req in specification.requirements:
            if not req.is_mandatory:
                continue

            resource_type = _CATEGORY_TO_RESOURCE_TYPE.get(
                req.category.upper(), "MATERIAL"
            )

            quantity = req.parameters.get("quantity", 1) if req.parameters else 1
            unit = req.parameters.get("unit", "unit") if req.parameters else "unit"

            resources.append({
                "name": req.name,
                "type": resource_type,
                "quantity": int(quantity),
                "unit": str(unit),
                "status": "AVAILABLE",
            })

        return resources
