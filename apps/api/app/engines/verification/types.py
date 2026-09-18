"""Type definitions and data structures for the Verification Engine."""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FAILED = "FAILED"
    STALE = "STALE"
    INCONCLUSIVE = "INCONCLUSIVE"


class ScheduleVerificationStatus(str, Enum):
    SCHEDULE_RESTORED = "SCHEDULE_RESTORED"
    SCHEDULE_IMPROVED = "SCHEDULE_IMPROVED"
    SCHEDULE_STILL_AT_RISK = "SCHEDULE_STILL_AT_RISK"
    SCHEDULE_FAILED = "SCHEDULE_FAILED"


class BudgetVerificationStatus(str, Enum):
    BUDGET_VALID = "BUDGET_VALID"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    BUDGET_INVALID = "BUDGET_INVALID"


class ResourceVerificationStatus(str, Enum):
    RESOURCE_RESTORED = "RESOURCE_RESTORED"
    RESOURCE_PARTIAL = "RESOURCE_PARTIAL"
    RESOURCE_FAILED = "RESOURCE_FAILED"


class ProviderVerificationStatus(str, Enum):
    PROVIDER_VERIFIED = "PROVIDER_VERIFIED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_MISMATCH = "PROVIDER_MISMATCH"
    PROVIDER_FAILED = "PROVIDER_FAILED"


class ObjectiveStatus(str, Enum):
    SATISFIED = "SATISFIED"
    AT_RISK = "AT_RISK"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass
class VerificationContext:
    """Authoritative context provided to the Verification Engine."""
    event_id: str
    event: Any
    action_execution: Any
    action_type: str
    target_type: Optional[str]
    target_id: Optional[str]
    payload: Dict[str, Any]
    recovery_option: Optional[Any] = None
    incident: Optional[Any] = None
    original_impact: Optional[Dict[str, Any]] = None
    original_risk: Optional[Dict[str, Any]] = None
    tasks: List[Any] = field(default_factory=list)
    dependencies: List[Any] = field(default_factory=list)
    budget_items: List[Any] = field(default_factory=list)
    resources: List[Any] = field(default_factory=list)
    providers: List[Any] = field(default_factory=list)
    vendor_assignments: List[Any] = field(default_factory=list)
    venue: Optional[Any] = None
    objectives: List[Any] = field(default_factory=list)
    constraints: List[Any] = field(default_factory=list)
    current_snapshot: str = ""


@dataclass
class ObjectiveVerificationResult:
    status: str  # SATISFIED, AT_RISK, FAILED
    objectives_evaluated: List[Dict[str, Any]] = field(default_factory=list)
    objectives_restored: List[str] = field(default_factory=list)
    objectives_still_at_risk: List[str] = field(default_factory=list)
    critical_objectives_satisfied: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleVerificationResult:
    status: ScheduleVerificationStatus
    is_feasible: bool
    deadline_violations: List[Dict[str, Any]] = field(default_factory=list)
    dependency_violations: List[str] = field(default_factory=list)
    critical_path_intact: bool = True
    slack_remaining_minutes: int = 0
    total_delay_minutes: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetVerificationResult:
    status: BudgetVerificationStatus
    is_valid: bool
    total_budget: Decimal = Decimal("0.00")
    total_committed: Decimal = Decimal("0.00")
    total_estimated: Decimal = Decimal("0.00")
    remaining_headroom: Decimal = Decimal("0.00")
    currency: str = "USD"
    violations: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceVerificationResult:
    status: ResourceVerificationStatus
    is_valid: bool
    conflicts: List[str] = field(default_factory=list)
    allocated_resources: List[Dict[str, Any]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderVerificationResult:
    status: ProviderVerificationStatus
    is_valid: bool
    assignment_confirmed: bool = True
    category_matched: bool = True
    available: bool = True
    eta_compatible: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstraintVerificationResult:
    hard_constraints_satisfied: bool = True
    soft_constraints_satisfied: bool = True
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VerificationResultData:
    status: VerificationStatus
    intended_outcome: Dict[str, Any]
    actual_outcome: Dict[str, Any]
    objective_results: List[Dict[str, Any]]
    schedule_result: Dict[str, Any]
    budget_result: Dict[str, Any]
    resource_result: Dict[str, Any]
    provider_result: Dict[str, Any]
    venue_result: Dict[str, Any]
    constraint_result: Dict[str, Any]
    risk_before: str
    risk_after: str
    event_state_before: str
    event_state_after: str
    failure_reasons: List[str]
    warnings: List[str]
