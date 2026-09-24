"""Deterministic Provider Verifier.

Verifies vendor assignments, category consistency, and operational availability.
Strictly distinguishes Database Confirmation from Physical Real-World Confirmation.
"""
from typing import Any, Dict, List
from app.engines.verification.types import (
    ProviderVerificationResult,
    ProviderVerificationStatus,
    VerificationContext,
)


class ProviderVerifier:
    """Verifies vendor assignments, provider category compatibility, and availability."""

    def verify(self, context: VerificationContext) -> ProviderVerificationResult:
        assignments = context.vendor_assignments or []
        providers_by_id = {p.id: p for p in context.providers}
        tasks = context.tasks or []

        assignment_confirmed = True
        category_matched = True
        available = True
        eta_compatible = True
        violations: List[str] = []

        # If this was a vendor reassignment action or recovery option
        is_vendor_action = (
            context.action_type in ("REASSIGN_VENDOR", "RECOVERY_BACKUP", "RECOVERY_REASSIGN")
            or "vendor_id" in context.payload
            or "new_vendor_id" in context.payload
        )

        target_vendor_id = (
            context.payload.get("new_vendor_id")
            or context.payload.get("vendor_id")
            or (context.recovery_option.proposed_changes.get("vendor_id") if context.recovery_option and context.recovery_option.proposed_changes else None)
        )

        relevant_assignments = (
            [a for a in assignments if a.vendor_id == target_vendor_id]
            if (is_vendor_action and target_vendor_id)
            else assignments
        )

        for assign in relevant_assignments:
            vendor = providers_by_id.get(assign.vendor_id)
            if not vendor:
                violations.append(f"Assignment references unknown vendor '{assign.vendor_id}'.")
                assignment_confirmed = False
                continue

            # Check status
            if assign.status != "CONFIRMED":
                violations.append(f"Vendor assignment for '{vendor.name}' is not CONFIRMED (status={assign.status}).")
                assignment_confirmed = False

            # Check vendor status
            v_status = getattr(vendor, "status", "ACTIVE")
            if v_status in ("UNAVAILABLE", "INACTIVE"):
                violations.append(f"Assigned vendor '{vendor.name}' is {v_status}.")
                available = False

            # Check category compatibility
            if vendor.category and assign.category:
                if vendor.category.lower() != assign.category.lower():
                    violations.append(
                        f"Vendor '{vendor.name}' category '{vendor.category}' does not match assignment category '{assign.category}'."
                    )
                    category_matched = False

        if is_vendor_action and target_vendor_id:
            matching_assign = next((a for a in assignments if a.vendor_id == target_vendor_id), None)
            if not matching_assign:
                violations.append(f"Target vendor '{target_vendor_id}' was not successfully assigned in authoritative state.")
                assignment_confirmed = False

        is_valid = assignment_confirmed and category_matched and available and (len(violations) == 0)

        if not is_valid:
            if not available:
                status = ProviderVerificationStatus.PROVIDER_UNAVAILABLE
            elif not category_matched:
                status = ProviderVerificationStatus.PROVIDER_MISMATCH
            else:
                status = ProviderVerificationStatus.PROVIDER_FAILED
        else:
            status = ProviderVerificationStatus.PROVIDER_VERIFIED

        return ProviderVerificationResult(
            status=status,
            is_valid=is_valid,
            assignment_confirmed=assignment_confirmed,
            category_matched=category_matched,
            available=available,
            eta_compatible=eta_compatible,
            details={
                "assignment_count": len(assignments),
                "violations": violations,
                "database_confirmed": True,
                "real_world_confirmed": False,  # Never claim physical external confirmation without explicit signal
            },
        )
