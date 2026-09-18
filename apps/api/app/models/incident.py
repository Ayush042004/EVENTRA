"""SQLAlchemy Model: Incident"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import IncidentSeverity, IncidentStatus


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(50), default=IncidentSeverity.MEDIUM.value, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(100), default="MANUAL", nullable=False)
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    occurred_at = Column(DateTime, nullable=True)

    # Operational entities related to this incident
    related_task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    related_vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    related_resource_id = Column(String(36), ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, index=True)
    related_venue_id = Column(String(36), ForeignKey("venues.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(String(50), default=IncidentStatus.OPEN.value, nullable=False, index=True)
    evidence_metadata = Column(JSON, nullable=True)

    # Cached deterministic impact & risk evaluations
    impact_result = Column(JSON, nullable=True)
    risk_result = Column(JSON, nullable=True)

    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    event = relationship("Event", back_populates="incidents")
    related_task = relationship("Task", foreign_keys=[related_task_id])
    related_vendor = relationship("Vendor", foreign_keys=[related_vendor_id])
    related_resource = relationship("Resource", foreign_keys=[related_resource_id])
    related_venue = relationship("Venue", foreign_keys=[related_venue_id])
