"""Observability: Operational Activity History.

Generates human-readable operational activity streams strictly from authoritative
backend events (Actions, Approvals, State Transitions, and Verifications).
Clients cannot submit arbitrary activity messages.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.action import ActionExecution
from app.models.approval import ApprovalRequest
from app.models.state_transition import StateTransition
from app.models.user import User
from app.models.verification import VerificationResult


class ActivityHistoryService:
    """Derives human-readable event activity logs from authoritative records."""

    def __init__(self, db: Session):
        self.db = db

    def get_activity_feed(self, event_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Synthesizes a combined chronological activity stream for an event."""
        activities: List[Dict[str, Any]] = []

        # 1. Action Executions
        actions = (
            self.db.query(ActionExecution)
            .filter(ActionExecution.event_id == event_id)
            .order_by(ActionExecution.executed_at.desc())
            .limit(limit)
            .all()
        )
        for act in actions:
            activities.append({
                "id": f"act-{act.id}",
                "timestamp": act.executed_at.isoformat() if act.executed_at else None,
                "category": "ACTION",
                "summary": f"Executed operational action: {act.action_type}",
                "status": act.status,
                "actor_id": act.executor_id,
                "details": {
                    "action_id": act.action_id,
                    "affected_entities_count": len(act.affected_entities or []),
                },
            })

        # 2. Approval Requests
        approvals = (
            self.db.query(ApprovalRequest)
            .filter(ApprovalRequest.event_id == event_id)
            .order_by(ApprovalRequest.created_at.desc())
            .limit(limit)
            .all()
        )
        for app in approvals:
            if app.status == "APPROVED":
                summary = f"Approval request for '{app.action_type}' was approved by authorized organizer."
            elif app.status == "REJECTED":
                summary = f"Approval request for '{app.action_type}' was rejected."
            elif app.status == "CANCELLED":
                summary = f"Approval request for '{app.action_type}' was cancelled by requester."
            else:
                summary = f"Approval requested for operational action: {app.action_type} (Impact: {app.impact_level})."

            activities.append({
                "id": f"app-{app.id}",
                "timestamp": (app.decided_at or app.created_at).isoformat(),
                "category": "APPROVAL",
                "summary": summary,
                "status": app.status,
                "actor_id": app.approver_id or app.requester_id,
                "details": {
                    "approval_id": app.id,
                    "impact_level": app.impact_level,
                },
            })

        # 3. State Transitions
        transitions = (
            self.db.query(StateTransition)
            .filter(StateTransition.event_id == event_id)
            .order_by(StateTransition.transitioned_at.desc())
            .limit(limit)
            .all()
        )
        for tr in transitions:
            activities.append({
                "id": f"trans-{tr.id}",
                "timestamp": tr.transitioned_at.isoformat(),
                "category": "STATE_TRANSITION",
                "summary": f"{tr.entity_type} state changed from {tr.previous_state} to {tr.new_state}. Reason: {tr.reason or 'Operational update'}",
                "status": "COMPLETED",
                "actor_id": None,
                "details": {
                    "entity_type": tr.entity_type,
                    "entity_id": tr.entity_id,
                    "previous_state": tr.previous_state,
                    "new_state": tr.new_state,
                },
            })

        # 4. Verifications
        verifications = (
            self.db.query(VerificationResult)
            .filter(VerificationResult.event_id == event_id)
            .order_by(VerificationResult.verified_at.desc())
            .limit(limit)
            .all()
        )
        for ver in verifications:
            if ver.status == "VERIFIED":
                summary = "Post-action operational verification completed: outcome fully verified."
            elif ver.status == "PARTIALLY_VERIFIED":
                summary = "Post-action operational verification completed: outcome partially restored event readiness."
            else:
                summary = f"Post-action verification failed: {ver.status}. Operational risks remain."

            activities.append({
                "id": f"ver-{ver.id}",
                "timestamp": ver.verified_at.isoformat(),
                "category": "VERIFICATION",
                "summary": summary,
                "status": ver.status,
                "actor_id": None,
                "details": {
                    "verification_id": ver.id,
                    "status": ver.status,
                },
            })

        # Sort all combined activities descending by timestamp
        activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        return activities[:limit]
