"""SQLAlchemy Model: VenueAvailability"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VenueAvailability(Base):
    __tablename__ = "venue_availabilities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String(36), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="AVAILABLE", nullable=False, index=True)  # AVAILABLE, BOOKED, BLOCKED, MAINTENANCE
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    venue = relationship("Venue", back_populates="availabilities")
