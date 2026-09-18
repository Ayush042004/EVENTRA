"""SQLAlchemy Model: AuditRecord"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(36), nullable=True, index=True)
    actor_type = Column(String(20), nullable=False, default="USER")  # USER, SYSTEM, AGENT
    action = Column(String(100), nullable=False)
    action_type = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(36), nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    impact_level = Column(String(20), nullable=True)
    approval_id = Column(String(36), nullable=True)
    execution_id = Column(String(36), nullable=True)
    verification_id = Column(String(36), nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    event = relationship("Event")


# Alias for backwards compatibility
Audit = AuditRecord
