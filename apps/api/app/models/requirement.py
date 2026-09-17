"""SQLAlchemy Model: Requirement"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import RequirementType


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(100), nullable=False, default=RequirementType.GENERAL.value, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    value = Column(JSON, nullable=True)
    required = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    event = relationship("Event", back_populates="requirements")
