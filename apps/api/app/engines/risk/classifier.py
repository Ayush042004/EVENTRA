"""Deterministic Engine: risk.classifier

Threshold definitions and classification mapping risk scores to risk levels
and operational EventState targets.
"""
from typing import Tuple
from app.models.enums import EventState, IncidentSeverity


class RiskClassifier:
    """Pure deterministic risk level and state classifier."""

    @staticmethod
    def classify_score(score: float) -> Tuple[str, str]:
        """Classify a 0-100 risk score into risk level and corresponding EventState.

        Thresholds:
            0.0  - 24.9  → LOW      → EventState.NORMAL
            25.0 - 49.9  → MEDIUM   → EventState.AT_RISK
            50.0 - 74.9  → HIGH     → EventState.CRITICAL
            75.0 - 100.0 → CRITICAL → EventState.EMERGENCY

        Returns:
            Tuple of (risk_level, target_event_state).
        """
        score = max(0.0, min(100.0, float(score)))

        if score >= 75.0:
            return IncidentSeverity.CRITICAL.value, EventState.EMERGENCY.value
        elif score >= 50.0:
            return IncidentSeverity.HIGH.value, EventState.CRITICAL.value
        elif score >= 25.0:
            return IncidentSeverity.MEDIUM.value, EventState.AT_RISK.value
        else:
            return IncidentSeverity.LOW.value, EventState.NORMAL.value
