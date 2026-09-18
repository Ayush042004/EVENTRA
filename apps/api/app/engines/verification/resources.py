"""Deterministic Resource Verifier.

Verifies resource quantities, availability states, and task allocations
to guarantee conflict-free operational execution.
"""
from typing import Any, Dict, List
from app.engines.verification.types import (
    ResourceVerificationResult,
    ResourceVerificationStatus,
    VerificationContext,
)


class ResourceVerifier:
    """Verifies that physical and logistical resources meet operational demands."""

    def verify(self, context: VerificationContext) -> ResourceVerificationResult:
        resources = context.resources or []
        tasks_by_id = {t.id: t for t in context.tasks}

        conflicts: List[str] = []
        allocated: List[Dict[str, Any]] = []

        for res in resources:
            r_id = getattr(res, "id", "")
            name = getattr(res, "name", "Unnamed Resource")
            status = getattr(res, "status", "AVAILABLE")
            quantity = getattr(res, "quantity", 1)
            task_id = getattr(res, "allocated_task_id", None)

            if quantity < 0:
                conflicts.append(f"Resource '{name}' ({r_id}) has negative quantity: {quantity}.")

            if task_id:
                if task_id not in tasks_by_id:
                    conflicts.append(
                        f"Resource '{name}' is allocated to non-existent task '{task_id}'."
                    )
                else:
                    allocated.append({
                        "resource_id": r_id,
                        "resource_name": name,
                        "task_id": task_id,
                        "task_name": tasks_by_id[task_id].name,
                        "quantity": quantity,
                        "status": status,
                    })

        # Check if action was ALLOCATE_RESOURCE and verify target is allocated
        if context.action_type == "ALLOCATE_RESOURCE" and context.target_id:
            target_res = next((r for r in resources if r.id == context.target_id), None)
            if not target_res or not target_res.allocated_task_id:
                conflicts.append(f"Resource allocation verification failed for '{context.target_id}'.")

        is_valid = len(conflicts) == 0

        status = ResourceVerificationStatus.RESOURCE_RESTORED if is_valid else (
            ResourceVerificationStatus.RESOURCE_PARTIAL if len(allocated) > 0 else ResourceVerificationStatus.RESOURCE_FAILED
        )

        return ResourceVerificationResult(
            status=status,
            is_valid=is_valid,
            conflicts=conflicts,
            allocated_resources=allocated,
            details={
                "total_resources": len(resources),
                "allocated_count": len(allocated),
                "conflict_count": len(conflicts),
            },
        )
