"""SQLAlchemy Model: Resource"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)  # EQUIPMENT, FACILITY, STAFF, MATERIAL, TRANSPORT
    quantity = Column(Integer, default=1, nullable=False)
    unit = Column(String(50), default="item", nullable=False)
    status = Column(String(50), default="AVAILABLE", nullable=False)  # AVAILABLE, ALLOCATED, IN_USE, DEPLETED
    allocated_task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    event = relationship("Event", back_populates="resources")
    allocated_task = relationship("Task", foreign_keys=[allocated_task_id])
