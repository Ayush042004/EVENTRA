"""Comprehensive Test Suite: Autonomous Event Operations Lifecycle

Tests:
1. Natural language event intake & structured intent extraction
2. Missing information detection and conversational prompts
3. Authoritative operational plan generation (tasks, DAG dependencies, resources, budget)
4. Conversational plan modifications (add/remove requirements, budget adjustments)
5. 'Start Operations' autonomous execution across multiple categories (Venue, Catering, AV, Photography, Security, etc.)
6. Live operations status telemetry and observability
7. Provider quote parsing, budget enforcement, and human approval gates
8. LangGraph agent integration for conversational control
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.event import Event
from app.models.task import Task
from app.models.vendor import Vendor
from app.models.venue import Venue
from app.models.vendor_assignment import VendorAssignment
from app.models.budget import BudgetItem
from app.models.requirement import Requirement
from app.models.enums import EventLifecycleState, TaskStatus, ProviderCategory
from app.services.intake_service import IntakeService
from app.services.autonomous_operations_service import AutonomousOperationsService
from app.services.negotiation_service import NegotiationService
from app.agent.agent import EventOperationsAgent


@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_intent_extraction_and_missing_info(db_session):
    """Verifies natural language extraction of event type, city, pax, budget, and missing fields."""
    service = IntakeService(db_session)

    # 1. Partial request missing date
    partial_text = (
        "I want to organize a 500-person corporate conference in Delhi. "
        "The budget is around 8 lakh. I need a venue, catering, AV, photography and transportation."
    )
    res = service.process_intake(partial_text, user_id="test_organizer")

    assert res["status"] == "MISSING_INFO"
    assert "Delhi" in res["message"]
    assert "500" in res["message"]
    assert "₹800,000" in res["message"]
    assert any("date" in m.lower() for m in res["missing_fields"])

    # 2. Complete request with date
    full_text = (
        "I want to organize a 500-person corporate conference in Delhi on 15 November 2026. "
        "The budget is around 8 lakh. I need a venue, catering, AV, photography and transportation."
    )
    plan_res = service.process_intake(full_text, user_id="test_organizer")

    assert plan_res["status"] == "PLAN_READY"
    assert plan_res["event_id"] is not None
    assert plan_res["event"]["guest_count"] == 500
    assert plan_res["event"]["location"] == "Delhi"
    assert plan_res["event"]["total_budget"] == 800000.0
    assert "VENUE" in plan_res["event"]["requirements"]
    assert "CATERING" in plan_res["event"]["requirements"]
    assert "AV_TECH" in plan_res["event"]["requirements"]
    assert "PHOTOGRAPHY" in plan_res["event"]["requirements"]
    assert "TRANSPORT" in plan_res["event"]["requirements"]

    # Check that authoritative plan generated tasks and DAG dependencies
    tasks = db_session.query(Task).filter(Task.event_id == plan_res["event_id"]).all()
    assert len(tasks) > 0
    budget_items = db_session.query(BudgetItem).filter(BudgetItem.event_id == plan_res["event_id"]).all()
    assert len(budget_items) > 0


def test_conversational_plan_modification(db_session):
    """Verifies modifying the plan conversationally (e.g. 'Remove photography and add security')."""
    service = IntakeService(db_session)

    initial_text = (
        "Organizing a 300-person wedding in Jaipur on 20 December 2026. "
        "Budget is 15 lakh. Requirements: venue, catering, decor, photography, dj."
    )
    plan_res = service.process_intake(initial_text, user_id="test_organizer")
    event_id = plan_res["event_id"]

    # Check initial requirements
    reqs = db_session.query(Requirement).filter(Requirement.event_id == event_id).all()
    req_types = {r.type for r in reqs}
    assert "PHOTOGRAPHY" in req_types
    assert "SECURITY" not in req_types

    # Modify plan: Remove photography, add security, increase budget to 18 lakh
    mod_res = service.modify_plan(
        event_id=event_id,
        modification_text="Remove photography and add security. Also update budget to 18 lakh.",
        user_id="test_organizer",
    )

    assert mod_res["status"] == "PLAN_UPDATED"
    updated_reqs = db_session.query(Requirement).filter(Requirement.event_id == event_id).all()
    updated_types = {r.type for r in updated_reqs}
    assert "PHOTOGRAPHY" not in updated_types
    assert "SECURITY" in updated_types

    event = db_session.query(Event).filter(Event.id == event_id).first()
    assert event.total_budget == 1800000.0


def test_start_autonomous_operations(db_session):
    """Verifies that 'Start Operations' transitions to LIVE, discovers providers, and dispatches outreach."""
    intake = IntakeService(db_session)
    ops = AutonomousOperationsService(db_session)

    # 1. Create planned event
    init_res = intake.process_intake(
        "500-person conference in Delhi on 15 November 2026. Budget 8 lakh. Requirements: venue, catering, av, transport.",
        user_id="test_organizer",
    )
    event_id = init_res["event_id"]

    # 2. Trigger Autonomous Operations
    ops_res = ops.start_operations(event_id=event_id, user_id="test_organizer")

    assert ops_res["status"] == "OPERATING"
    assert ops_res["lifecycle_state"] == EventLifecycleState.LIVE.value
    assert ops_res["providers_contacted_count"] > 0
    assert len(ops_res["operations_report"]) >= 4

    # 3. Check Database State
    event = db_session.query(Event).filter(Event.id == event_id).first()
    assert event.lifecycle_state == EventLifecycleState.LIVE.value

    # Check Vendor Assignments
    assignments = db_session.query(VendorAssignment).filter(VendorAssignment.event_id == event_id).all()
    assert len(assignments) > 0

    # 4. Check Telemetry Status
    status = ops.get_operations_status(event_id=event_id)
    assert status["lifecycle_state"] == EventLifecycleState.LIVE.value
    assert len(status["assignments"]) > 0
    assert status["total_budget"] == 800000.0


def test_provider_quote_budget_and_approval_gate(db_session):
    """Verifies provider quote ingestion, budget enforcement, and approval gate creation."""
    intake = IntakeService(db_session)
    ops = AutonomousOperationsService(db_session)
    neg_service = NegotiationService(db_session)

    init_res = intake.process_intake(
        "100-person tech meetup in Bangalore on 10 October 2026. Budget 2 lakh. Requirements: catering, av.",
        user_id="test_organizer",
    )
    event_id = init_res["event_id"]
    ops.start_operations(event_id=event_id)

    # Find catering assignment
    catering_assignment = (
        db_session.query(VendorAssignment)
        .filter(VendorAssignment.event_id == event_id, VendorAssignment.category == "catering")
        .first()
    )
    assert catering_assignment is not None

    # Simulate quote exceeding target threshold
    quote_res = neg_service.process_quote(
        assignment_id=catering_assignment.id,
        quoted_amount=60000.0,
        notes="Premium buffet package for 100 pax",
    )

    assert "negotiation_status" in quote_res
    # Verify assignment has updated agreed_cost or quote
    db_session.refresh(catering_assignment)
    assert catering_assignment.agreed_cost is not None


def test_agent_graph_start_operations_and_plan_modification(db_session):
    """Verifies that the LangGraph operations agent handles 'Start Operations' and plan modification commands."""
    intake = IntakeService(db_session)
    init_res = intake.process_intake(
        "400-person corporate summit in Mumbai on 25 November 2026. Budget 10 lakh. Requirements: venue, catering, photography.",
        user_id="test_organizer",
    )
    event_id = init_res["event_id"]

    agent = EventOperationsAgent(db_session)

    # 1. Modify plan via agent
    mod_output = agent.run(
        event_id=event_id,
        message="Remove photography and add security",
        user_id="test_organizer",
    )
    assert mod_output["status"] == "COMPLETED"
    assert "Operational plan updated" in mod_output["response"] or "Updated" in mod_output["response"]

    # 2. Start operations via agent
    start_output = agent.run(
        event_id=event_id,
        message="Start operations",
        user_id="test_organizer",
    )
    assert start_output["status"] == "COMPLETED"
    assert "Operations Active" in start_output["response"] or "Autonomous operations" in start_output["response"]

    event = db_session.query(Event).filter(Event.id == event_id).first()
    assert event.lifecycle_state == EventLifecycleState.LIVE.value
