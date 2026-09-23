"""Deterministic Backend Tools for Provider Communication & Negotiation.

Wraps NegotiationService and ProviderCommunicationService.
All authoritative business logic, budget checks, and approvals are executed deterministically.
"""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session


def contact_provider(
    db: Session,
    event_id: str,
    assignment_id: str,
    target_amount: Optional[float] = None,
    max_approved_amount: Optional[float] = None,
    currency: str = "INR",
    required_coverage_start: Optional[str] = None,
    required_coverage_end: Optional[str] = None,
) -> Dict[str, Any]:
    """Initiates contact with a provider for an event assignment."""
    from app.services.negotiation_service import NegotiationService
    service = NegotiationService(db)
    return service.initiate_engagement(
        event_id=event_id,
        assignment_id=assignment_id,
        target_amount=target_amount,
        max_approved_amount=max_approved_amount,
        currency=currency,
        required_coverage_start=required_coverage_start,
        required_coverage_end=required_coverage_end,
    )


def negotiate_with_provider(
    db: Session,
    assignment_id: str,
) -> Dict[str, Any]:
    """Generates and dispatches a deterministic counter-offer towards target amount."""
    from app.services.negotiation_service import NegotiationService
    service = NegotiationService(db)
    return service.negotiate(assignment_id=assignment_id)


def request_provider_approval(
    db: Session,
    event_id: str,
    assignment_id: str,
) -> Dict[str, Any]:
    """Creates a human approval request for a negotiated provider agreement."""
    from app.services.negotiation_service import NegotiationService
    service = NegotiationService(db)
    return service.request_approval(event_id=event_id, assignment_id=assignment_id)


def confirm_provider_engagement(
    db: Session,
    assignment_id: str,
) -> Dict[str, Any]:
    """Confirms the provider assignment once human approval has been granted."""
    from app.services.negotiation_service import NegotiationService
    service = NegotiationService(db)
    return service.confirm_engagement(assignment_id=assignment_id)


def simulate_provider_response(
    db: Session,
    assignment_id: str,
    scenario: str,
    quoted_amount: Optional[float] = None,
    coverage_start: Optional[str] = None,
    coverage_end: Optional[str] = None,
    advance_required: Optional[bool] = None,
    provider_count: Optional[int] = None,
    custom_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Simulates provider incoming communication for interactive testing and demonstration."""
    from app.services.negotiation_service import NegotiationService
    service = NegotiationService(db)
    return service.simulate_response(
        assignment_id=assignment_id,
        scenario=scenario,
        quoted_amount=quoted_amount,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        advance_required=advance_required,
        provider_count=provider_count,
        custom_message=custom_message,
    )


def get_provider_negotiation_history(
    db: Session,
    assignment_id: str,
) -> Dict[str, Any]:
    """Fetches full communication thread and negotiation state for an assignment."""
    from app.services.negotiation_service import NegotiationService
    service = NegotiationService(db)
    return service.get_conversation(assignment_id=assignment_id)
