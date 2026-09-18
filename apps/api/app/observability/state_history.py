"""Observability: State Transition History.

Queries and formats the immutable append-only state transition history for an event.
Clients cannot modify, overwrite, or delete historical transitions.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.state_transition import StateTransition


class StateHistoryService:
    """Provides append-only historical access to authoritative state transitions."""

    def __init__(self, db: Session):
        self.db = db

    def get_state_history(
        self, event_id: str, entity_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Returns the chronological sequence of state transitions for an event."""
        query = self.db.query(StateTransition).filter(StateTransition.event_id == event_id)
        if entity_type:
            query = query.filter(StateTransition.entity_type == entity_type)

        transitions = query.order_by(StateTransition.transitioned_at.desc()).limit(limit).all()

        return [
            {
                "id": t.id,
                "event_id": t.event_id,
                "entity_type": t.entity_type,
                "entity_id": t.entity_id,
                "previous_state": t.previous_state,
                "new_state": t.new_state,
                "reason": t.reason,
                "transitioned_at": t.transitioned_at.isoformat(),
            }
            for t in transitions
        ]
