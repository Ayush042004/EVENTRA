"""SQLAlchemy Model: ActionExecution"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ActionExecution(Base):
    """Immutable audit and idempotency record of executed operational actions."""

    __tablename__ = "action_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_id = Column(String(64), unique=True, nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    
    approval_request_id = Column(String(36), ForeignKey("approvals.id", ondelete="SET NULL"), nullable=True, index=True)
    recovery_option_id = Column(String(36), ForeignKey("recovery_options.id", ondelete="SET NULL"), nullable=True, index=True)
    executor_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(20), nullable=False, default="SUCCESS", index=True)
    affected_entities = Column(JSON, nullable=False, default=list)
    
    before_version = Column(String(128), nullable=False)
    after_version = Column(String(128), nullable=False)
    failure_reason = Column(Text, nullable=True)
    
    execution_payload = Column(JSON, nullable=False, default=dict)
    execution_result_data = Column(JSON, nullable=False, default=dict)
    executed_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    event = relationship("Event", foreign_keys=[event_id])
    approval_request = relationship("Approval", foreign_keys=[approval_request_id])
    recovery_option = relationship("Recovery", foreign_keys=[recovery_option_id])
    executor = relationship("User", foreign_keys=[executor_id])
