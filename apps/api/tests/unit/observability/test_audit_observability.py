"""Unit tests for Observability subsystem: Audit, Activity, Decision Trace, State History."""
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.action import ActionExecution
from app.models.approval import ApprovalRequest
from app.models.enums import EventLifecycleState, EventState
from app.models.event import Event
from app.models.incident import Incident
from app.models.recovery import Recovery
from app.models.state_transition import StateTransition
from app.models.user import User
from app.models.verification import VerificationResult
from app.observability.activity import ActivityHistoryService
from app.observability.audit import AuditRecorder
from app.observability.decision_trace import DecisionTraceService
from app.observability.state_history import StateHistoryService


def _setup_observability_data(db: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user = User(name="Audit Operator", email="audit.op@eventra.test")
    db.add(user)
    db.flush()

    event = Event(
        owner_id=user.id,
        name="Observability Summit",
        lifecycle_state=EventLifecycleState.PLANNED.value,
        state=EventState.NORMAL.value,
    )
    db.add(event)
    db.flush()

    # Create State Transition
    trans = StateTransition(
        event_id=event.id,
        entity_type="EVENT",
        entity_id=event.id,
        previous_state="RECOVERY",
        new_state="NORMAL",
        reason="Recovery verified successfully",
        transitioned_at=now,
    )
    # Create Incident
    incident = Incident(
        event_id=event.id,
        title="Stage Cable Snapped",
        incident_type="EQUIPMENT_FAILURE",
        severity="HIGH",
    )
    db.add_all([trans, incident])
    db.flush()

    # Create Recovery Option
    recovery = Recovery(
        incident_id=incident.id,
        event_id=event.id,
        strategy_type="REALLOCATE_RESOURCE",
        status="FEASIBLE",
        is_feasible=True,
        state_snapshot="snap-999",
    )
    db.add(recovery)
    db.flush()

    # Create Approval Request
    approval = ApprovalRequest(
        event_id=event.id,
        requester_id=user.id,
        approver_id=user.id,
        action_type="ALLOCATE_RESOURCE",
        target_type="RESOURCE",
        impact_level="MAJOR",
        requested_action={"quantity": 2},
        status="APPROVED",
        state_snapshot="snap-999",
    )
    db.add(approval)
    db.flush()

    # Create Action Execution
    action = ActionExecution(
        action_id="act-obs-1",
        event_id=event.id,
        approval_request_id=approval.id,
        recovery_option_id=recovery.id,
        executor_id=user.id,
        action_type="ALLOCATE_RESOURCE",
        status="SUCCESS",
        affected_entities=[{"type": "RESOURCE", "id": "res-1"}],
        before_version="snap-before",
        after_version="snap-after",
        executed_at=now,
    )
    db.add(action)
    db.flush()

    # Create Verification Result
    verification = VerificationResult(
        event_id=event.id,
        action_execution_id=action.id,
        recovery_option_id=recovery.id,
        status="VERIFIED",
        intended_outcome={"action": "ALLOCATE_RESOURCE"},
        actual_outcome={"status": "RESOURCE_RESTORED"},
        risk_before="HIGH",
        risk_after="LOW",
        event_state_before="RECOVERY",
        event_state_after="NORMAL",
        state_snapshot="snap-after",
        verified_at=now,
    )
    db.add(verification)
    db.commit()

    return {
        "user": user,
        "event": event,
        "action": action,
        "verification": verification,
        "transition": trans,
    }


def test_audit_recorder_sanitization(db_session: Session):
    data = _setup_observability_data(db_session)
    recorder = AuditRecorder(db_session)

    # Attempt to log payload with sensitive credentials and secret keys
    sensitive_payload = {
        "username": "admin",
        "password": "SuperSecretPassword123!",
        "api_token": "bearer-token-xyz-12345",
        "auth_secret": "jwt-private-key",
        "chain_of_thought": "Thinking step by step...",
        "safe_field": "public_data",
    }

    record = recorder.record(
        event_id=data["event"].id,
        action="LOGIN_OR_UPDATE",
        action_type="SECURITY",
        actor_id=data["user"].id,
        before_state=sensitive_payload,
        after_state={"status": "OK"},
    )
    db_session.commit()

    # Verify secrets were redacted
    assert record.before_state["password"] == "[REDACTED]"
    assert record.before_state["api_token"] == "[REDACTED]"
    assert record.before_state["auth_secret"] == "[REDACTED]"
    assert record.before_state["chain_of_thought"] == "[REDACTED]"
    assert record.before_state["safe_field"] == "public_data"


def test_activity_history_feed(db_session: Session):
    data = _setup_observability_data(db_session)
    service = ActivityHistoryService(db_session)

    feed = service.get_activity_feed(data["event"].id)
    assert len(feed) >= 4  # Action, Approval, Transition, Verification

    categories = {item["category"] for item in feed}
    assert "ACTION" in categories
    assert "APPROVAL" in categories
    assert "STATE_TRANSITION" in categories
    assert "VERIFICATION" in categories


def test_decision_trace_factual_and_no_chain_of_thought(db_session: Session):
    data = _setup_observability_data(db_session)
    service = DecisionTraceService(db_session)

    traces = service.get_traces_for_event(data["event"].id)
    assert len(traces) >= 1
    trace = traces[0]

    # Verify complete factual pipeline
    assert trace["incident"]["type"] == "EQUIPMENT_FAILURE"
    assert trace["recovery_option"]["strategy_type"] == "REALLOCATE_RESOURCE"
    assert trace["approval"]["status"] == "APPROVED"
    assert trace["execution"]["action_id"] == "act-obs-1"
    assert trace["verification"]["status"] == "VERIFIED"
    assert trace["event_state"]["state_after"] == "NORMAL"

    # Strictly check that NO chain of thought exists in trace
    trace_str = str(trace).lower()
    assert "chain_of_thought" not in trace_str
    assert "thought:" not in trace_str
    assert "reasoning:" not in trace_str


def test_state_history_query(db_session: Session):
    data = _setup_observability_data(db_session)
    service = StateHistoryService(db_session)

    history = service.get_state_history(data["event"].id)
    assert len(history) >= 1
    assert history[0]["previous_state"] == "RECOVERY"
    assert history[0]["new_state"] == "NORMAL"
