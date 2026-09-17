"""Deterministic Engine: state.event_state

Lifecycle state machine for events. Defines valid transitions and
enforces transition rules deterministically.
"""
from typing import Dict, List, Set
from app.models.enums import EventLifecycleState


# Valid lifecycle transitions: from_state -> {allowed_target_states}
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    EventLifecycleState.DRAFT.value: {
        EventLifecycleState.SPECIFIED.value,
        EventLifecycleState.CANCELLED.value,
    },
    EventLifecycleState.SPECIFIED.value: {
        EventLifecycleState.PLANNED.value,
        EventLifecycleState.CANCELLED.value,
    },
    EventLifecycleState.PLANNED.value: {
        EventLifecycleState.LIVE.value,
        EventLifecycleState.CANCELLED.value,
    },
    EventLifecycleState.LIVE.value: {
        EventLifecycleState.INCIDENT.value,
        EventLifecycleState.CONCLUDED.value,
        EventLifecycleState.CANCELLED.value,
    },
    EventLifecycleState.INCIDENT.value: {
        EventLifecycleState.LIVE.value,
        EventLifecycleState.EMERGENCY.value,
        EventLifecycleState.CONCLUDED.value,
    },
    EventLifecycleState.EMERGENCY.value: {
        EventLifecycleState.LIVE.value,
        EventLifecycleState.CONCLUDED.value,
        EventLifecycleState.CANCELLED.value,
    },
    EventLifecycleState.CONCLUDED.value: set(),  # Terminal state
    EventLifecycleState.CANCELLED.value: set(),  # Terminal state
}


class EventStateMachine:
    """Pure deterministic state machine for event lifecycle transitions.

    Enforces valid transition rules without side effects.
    """

    def can_transition(self, current_state: str, target_state: str) -> bool:
        """Check if a transition from current to target state is valid."""
        allowed = VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed

    def get_valid_transitions(self, current_state: str) -> List[str]:
        """Get list of valid target states from the current state."""
        return sorted(VALID_TRANSITIONS.get(current_state, set()))

    def validate_transition(self, current_state: str, target_state: str) -> None:
        """Validate a state transition, raising ValueError if invalid.

        Raises:
            ValueError: If the transition is not allowed.
        """
        if not self.can_transition(current_state, target_state):
            valid = self.get_valid_transitions(current_state)
            raise ValueError(
                f"Invalid lifecycle transition: {current_state} → {target_state}. "
                f"Valid transitions from '{current_state}': {valid}"
            )

    def is_terminal(self, state: str) -> bool:
        """Check if the state is a terminal state (no outgoing transitions)."""
        return len(VALID_TRANSITIONS.get(state, set())) == 0
