"""SQLAlchemy Model: VerificationResult"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    action_execution_id = Column(String(36), ForeignKey("action_executions.id", ondelete="CASCADE"), nullable=True, index=True)
    recovery_option_id = Column(String(36), ForeignKey("recovery_options.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Status: PENDING, VERIFYING, VERIFIED, PARTIALLY_VERIFIED, FAILED, STALE, INCONCLUSIVE
    status = Column(String(30), nullable=False, default="PENDING", index=True)

    intended_outcome = Column(JSON, nullable=False, default=dict)
    actual_outcome = Column(JSON, nullable=False, default=dict)
    
    objective_results = Column(JSON, nullable=False, default=list)
    schedule_result = Column(JSON, nullable=False, default=dict)
    budget_result = Column(JSON, nullable=False, default=dict)
    resource_result = Column(JSON, nullable=False, default=dict)
    provider_result = Column(JSON, nullable=False, default=dict)
    venue_result = Column(JSON, nullable=False, default=dict)
    constraint_result = Column(JSON, nullable=False, default=dict)

    risk_before = Column(String(20), nullable=True)
    risk_after = Column(String(20), nullable=True)
    event_state_before = Column(String(30), nullable=True)
    event_state_after = Column(String(30), nullable=True)

    state_snapshot = Column(String(128), nullable=False, index=True)
    failure_reasons = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)

    verified_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    event = relationship("Event")
    action_execution = relationship("ActionExecution")
    recovery_option = relationship("Recovery")
