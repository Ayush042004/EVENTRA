"""SQLAlchemy Model: Venue"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Venue(Base):
    __tablename__ = "venues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity = Column(Integer, nullable=False, index=True)
    venue_type = Column(String(100), nullable=False, index=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    hourly_rate = Column(Float, nullable=True)
    amenities = Column(JSON, default=list, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    availabilities = relationship(
        "VenueAvailability",
        back_populates="venue",
        cascade="all, delete-orphan",
        lazy="select",
    )
