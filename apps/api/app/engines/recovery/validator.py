"""Validation of simulated recovery state against existing domain invariants."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

from app.engines.budget.calculator import BudgetCalculator
from app.engines.budget.validator import BudgetValidator
from app.engines.dependency.graph import DependencyGraph
from app.engines.recovery.types import RecoveryContext, RecoverySimulation, ValidationResult
from app.engines.schedule.feasibility import ScheduleFeasibilityChecker
from app.engines.schedule.scheduler import ScheduleResult, TaskScheduleEntry


class RecoveryValidator:
    """Reject hard violations while retaining concise, factual rejection reasons."""

    def __init__(self):
        self._budget_calculator = BudgetCalculator()
        self._budget_validator = BudgetValidator()
        self._schedule_checker = ScheduleFeasibilityChecker()

    def validate(self, simulation: RecoverySimulation, context: RecoveryContext) -> ValidationResult:
        violations: List[str] = []
        warnings: List[str] = []
        candidate = simulation.candidate
        try:
            graph = DependencyGraph.from_tasks_and_dependencies(simulation.simulated_tasks, context.dependencies)
            graph.topological_sort()
        except ValueError as error:
            violations.append(f"Dependency violation: {error}")

        schedule = self._schedule_from_simulation(simulation, context)
        if schedule:
            result = self._schedule_checker.check_feasibility(
                schedule, context.event.start_datetime, context.event.end_datetime
            )
            violations.extend(item.description for item in result.violations)
        if simulation.schedule_delta["slack_after_minutes"] < simulation.schedule_delta["slack_before_minutes"]:
            warnings.append(
                f"Recovery reduces schedule slack from {simulation.schedule_delta['slack_before_minutes']} "
                f"to {simulation.schedule_delta['slack_after_minutes']} minutes."
            )

        self._validate_provider(candidate, simulation, context, violations)
        self._validate_resource(candidate, context, violations)
        self._validate_budget(simulation, context, violations)
        self._validate_constraints(simulation, context, violations, warnings)
        self._validate_venue(context, violations)
        return ValidationResult(not violations, violations, warnings, datetime.now(timezone.utc).replace(tzinfo=None))

    def _schedule_from_simulation(self, simulation: RecoverySimulation, context: RecoveryContext):
        changed = {item["task_id"]: item for item in simulation.schedule_delta["task_changes"]}
        # Simulator always has all task snapshots, so reconstruct schedule entries directly.
        entries = {}
        for task in simulation.simulated_tasks:
            start, end = task.get("planned_start"), task.get("planned_end")
            if start and end:
                entries[task["id"]] = TaskScheduleEntry(task["id"], start, end, int(task.get("duration_minutes") or 0))
        if not entries:
            return None
        project_end = max(entry.planned_end for entry in entries.values())
        total = int((project_end - context.event.start_datetime).total_seconds() / 60)
        return ScheduleResult(entries=entries, project_end=project_end, total_duration_minutes=total)

    @staticmethod
    def _validate_provider(candidate, simulation, context, violations: List[str]) -> None:
        if not candidate.affected_provider_ids:
            return
        provider_id = candidate.affected_provider_ids[0]
        provider = next((item for item in context.providers if item.id == provider_id), None)
        if not provider:
            violations.append("Provider does not exist.")
            return
        if provider.status != "ACTIVE":
            violations.append(f"Provider '{provider.id}' is not active.")
        relevant = [task for task in context.tasks if task.id in candidate.affected_task_ids]
        required = {(task.required_provider_category or "").lower() for task in relevant}
        if required and (provider.category or "").lower() not in required:
            violations.append("Provider category is incompatible with affected task.")
        if provider.base_cost is None:
            violations.append("Provider cost is unknown.")
        changed_windows = [(task.get("planned_start"), task.get("planned_end")) for task in simulation.simulated_tasks if task["id"] in candidate.affected_task_ids]
        for availability in provider.availabilities:
            if availability.status in {"BOOKED", "BLOCKED"}:
                for start, end in changed_windows:
                    if start and end and availability.start_datetime < end and availability.end_datetime > start:
                        violations.append("Provider unavailable during required task window.")
                        return

    @staticmethod
    def _validate_resource(candidate, context, violations: List[str]) -> None:
        for resource_id in candidate.affected_resource_ids:
            resource = next((item for item in context.resources if item.id == resource_id), None)
            if not resource:
                violations.append("Proposed resource does not exist.")
            elif resource.status != "AVAILABLE":
                violations.append(f"Resource '{resource.id}' is not available for reassignment.")
            elif resource.quantity <= 0:
                violations.append(f"Resource '{resource.id}' has insufficient quantity.")

    def _validate_budget(self, simulation, context, violations: List[str]) -> None:
        net = Decimal(str(simulation.budget_delta.get("net_delta", 0)))
        if net < 0:
            # A saving is legitimate; no negative purchase is introduced.
            net = Decimal("0")
        simulated_items = list(context.budget_items)
        if net:
            simulated_items.append({"category": "RECOVERY", "estimated_amount": net, "actual_amount": 0})
        for violation in self._budget_validator.validate_budget(context.event.total_budget, simulated_items):
            violations.append(violation.description)
        summary = self._budget_calculator.calculate_totals(simulated_items)
        simulation.budget_delta["remaining_budget"] = float(Decimal(str(context.event.total_budget)) - summary.total_estimated)

    @staticmethod
    def _validate_constraints(simulation, context, violations: List[str], warnings: List[str]) -> None:
        for constraint in context.constraints:
            affected = False
            value = getattr(constraint, "value", None) or {}
            c_type = getattr(constraint, "type", None)
            severity = getattr(constraint, "severity", "HARD")
            c_name = getattr(constraint, "name", "Constraint")
            if c_type == "TIME_WINDOW":
                end = value.get("end_datetime") or value.get("latest_end") if isinstance(value, dict) else None
                if end:
                    try:
                        limit = datetime.fromisoformat(end) if isinstance(end, str) else end
                        if hasattr(limit, "tzinfo") and limit.tzinfo is not None:
                            limit = limit.replace(tzinfo=None)
                        proj_str = simulation.schedule_delta.get("project_end_after")
                        if proj_str:
                            proposed_end = datetime.fromisoformat(proj_str) if isinstance(proj_str, str) else proj_str
                            if hasattr(proposed_end, "tzinfo") and proposed_end.tzinfo is not None:
                                proposed_end = proposed_end.replace(tzinfo=None)
                            affected = proposed_end > limit
                    except (TypeError, ValueError):
                        affected = False
            elif c_type == "BUDGET_CAP" and isinstance(value, dict) and value.get("amount") is not None:
                total_budget = Decimal(str(getattr(context.event, "total_budget", 0) or 0))
                net_delta = Decimal(str(simulation.budget_delta.get("net_delta", 0)))
                affected = (total_budget + net_delta) > Decimal(str(value["amount"]))
            if affected:
                message = f"Constraint '{c_name}' would be violated."
                (violations if severity == "HARD" else warnings).append(message)

    @staticmethod
    def _validate_venue(context, violations: List[str]) -> None:
        venue = context.venue
        if not venue:
            return
        status = getattr(venue, "status", "")
        capacity = getattr(venue, "capacity", 0) or 0
        guest_count = getattr(context.event, "guest_count", 0) or 0
        if status != "ACTIVE":
            violations.append("Related venue is not active.")
        if capacity > 0 and guest_count > 0 and capacity < guest_count:
            violations.append("Related venue capacity is below the event guest-count requirement.")


Validator = RecoveryValidator

