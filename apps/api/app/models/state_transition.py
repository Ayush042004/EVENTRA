"""SQLAlchemy Model: StateTransition"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class StateTransition(Base):
    __tablename__ = "state_transitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # EVENT, TASK, RESOURCE, VENDOR_ASSIGNMENT
    entity_id = Column(String(36), nullable=False, index=True)  # ID of the entity that transitioned
    previous_state = Column(String(50), nullable=False)
    new_state = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    transitioned_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    event = relationship("Event")
