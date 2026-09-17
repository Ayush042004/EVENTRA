"""SQLAlchemy Model: VendorAssignment"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VendorAssignment(Base):
    __tablename__ = "vendor_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # purpose / role (e.g. sound, catering)
    status = Column(String(50), default="REQUESTED", nullable=False)  # REQUESTED, CONFIRMED, CANCELLED
    agreed_cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    vendor = relationship("Vendor", back_populates="assignments")
