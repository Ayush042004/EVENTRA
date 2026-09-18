"""SQLAlchemy Model: Notification"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Notification(Base):
    """Operational notification record emitted during event lifecycle and recovery."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(50), nullable=False, default="IN_APP")
    recipient = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="DELIVERED", index=True)  # DELIVERED, PENDING, FAILED
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    event = relationship("Event")
