"""Test Suite: Provider Communication & Negotiation Agent.

Verifies:
1. Initiation of provider engagement with negotiation boundaries (target, ceiling, coverage).
2. Communication dispatch via Mock/WhatsApp channels.
3. Provider response simulation (accept, counter, decline).
4. CRITICAL AUTHORITY RULE:
   - Agent negotiates toward target amount
   - Agent never exceeds max_approved_amount
   - Agent NEVER autonomously accepts any offer
   - All commitments require explicit human approval
5. Confirmation transitions assignment to CONFIRMED and records audit trace.
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.event import Event
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.enums import EventType, EventState, NegotiationStatus
from app.services.negotiation_service import NegotiationService
from app.services.approval_service import ApprovalService
from app.core.exceptions import BadRequestException


@pytest.fixture
def sample_event(db_session: Session) -> Event:
    event = Event(
        name="Global Tech Summit 2026",
        event_type=EventType.CONFERENCE,
        state=EventState.NORMAL,
        location="Seattle, WA",
        total_budget=500000.0,
        start_datetime=datetime.now(timezone.utc),
        end_datetime=datetime.now(timezone.utc),
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def sample_vendor(db_session: Session) -> Vendor:
    vendor = Vendor(
        name="Apex Cine Productions",
        category="photography",
        city="Seattle",
        base_cost=45000.0,
        contact_phone="+1-206-555-0199",
        status="ACTIVE",
        source="SYSTEM",
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)
    return vendor


@pytest.fixture
def sample_assignment(db_session: Session, sample_event: Event, sample_vendor: Vendor) -> VendorAssignment:
    assignment = VendorAssignment(
        event_id=sample_event.id,
        vendor_id=sample_vendor.id,
        category="photography",
        status="ASSIGNED",
        negotiation_status=NegotiationStatus.NOT_CONTACTED.value,
        agreed_cost=45000.0,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


def test_initiate_engagement(db_session: Session, sample_event: Event, sample_assignment: VendorAssignment):
    """Test agent pitches event and establishes commercial negotiation parameters."""
    service = NegotiationService(db_session)
    result = service.initiate_engagement(
        event_id=sample_event.id,
        assignment_id=sample_assignment.id,
        target_amount=42000.0,
        max_approved_amount=45000.0,
        currency="INR",
        required_coverage_start="10:00",
        required_coverage_end="20:00",
    )

    assert result["success"] is True
    assert result["negotiation_status"] == NegotiationStatus.CONTACTED.value
    assert "Global Tech Summit 2026" in result["message_sent"]

    # Verify db assignment updated
    db_session.refresh(sample_assignment)
    assert sample_assignment.target_amount == 42000.0
    assert sample_assignment.max_approved_amount == 45000.0
    assert sample_assignment.negotiation_status == NegotiationStatus.CONTACTED.value


def test_provider_counter_over_ceiling_triggers_negotiation(
    db_session: Session, sample_event: Event, sample_assignment: VendorAssignment
):
    """Test that when provider quotes above max ceiling, agent negotiates and does NOT accept."""
    service = NegotiationService(db_session)
    service.initiate_engagement(
        event_id=sample_event.id,
        assignment_id=sample_assignment.id,
        target_amount=42000.0,
        max_approved_amount=45000.0,
    )

    # Provider counters with ₹50,000 (above ceiling of ₹45,000)
    sim_result = service.simulate_response(
        assignment_id=sample_assignment.id,
        scenario="COUNTER",
        quoted_amount=50000.0,
    )

    assert sim_result["negotiation_status"] == NegotiationStatus.NEGOTIATING.value
    assert sim_result["action"] == "NEGOTIATE"

    # Agent executes counter-offer
    counter_result = service.negotiate(sample_assignment.id)
    assert counter_result["action"] == "COUNTER_OFFER_SENT"
    assert counter_result["counter_offer_amount"] <= 45000.0  # Must never exceed ceiling


def test_deterministic_authority_rule_requires_human_approval(
    db_session: Session, sample_event: Event, sample_assignment: VendorAssignment
):
    """CRITICAL TEST: Even when provider quote is within ceiling, agent NEVER autonomously accepts.
    Human approval is always required.
    """
    service = NegotiationService(db_session)
    service.initiate_engagement(
        event_id=sample_event.id,
        assignment_id=sample_assignment.id,
        target_amount=42000.0,
        max_approved_amount=45000.0,
    )

    # Provider offers ₹44,000 (within approved ceiling of ₹45,000)
    sim_result = service.simulate_response(
        assignment_id=sample_assignment.id,
        scenario="ACCEPT",
        quoted_amount=44000.0,
    )

    # MUST be AWAITING_APPROVAL, NOT CONFIRMED
    assert sim_result["negotiation_status"] == NegotiationStatus.AWAITING_APPROVAL.value
    assert sim_result["action"] == "AWAITING_APPROVAL"

    # Direct confirmation without approval or in wrong state should be restricted
    db_session.refresh(sample_assignment)
    assert sample_assignment.negotiation_status == NegotiationStatus.AWAITING_APPROVAL.value

    # Human approval flow
    approval_res = service.request_approval(sample_event.id, sample_assignment.id)
    assert approval_res["approval_id"] is not None

    # Simulate human approval decision
    from app.models.approval import Approval
    approval = db_session.query(Approval).filter(Approval.id == approval_res["approval_id"]).first()
    approval.status = "APPROVED"
    db_session.commit()

    # Approve and confirm
    confirm_res = service.confirm_engagement(sample_assignment.id)
    assert confirm_res["negotiation_status"] == NegotiationStatus.CONFIRMED.value
    assert confirm_res["status"] == "CONFIRMED"
    assert confirm_res["agreed_cost"] == 44000.0


def test_provider_decline_recommends_recovery(
    db_session: Session, sample_event: Event, sample_assignment: VendorAssignment
):
    """Test that provider decline is recorded and recovery recommended."""
    service = NegotiationService(db_session)
    service.initiate_engagement(
        event_id=sample_event.id,
        assignment_id=sample_assignment.id,
        target_amount=42000.0,
        max_approved_amount=45000.0,
    )

    result = service.simulate_response(
        assignment_id=sample_assignment.id,
        scenario="DECLINE",
    )

    assert result["negotiation_status"] == NegotiationStatus.DECLINED.value
    assert result["action"] == "PROVIDER_DECLINED"
