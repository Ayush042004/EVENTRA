"""SQLAlchemy Model: Vendor (Provider)"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # catering, sound, lighting, photography, etc.
    city = Column(String(100), nullable=False, index=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    base_cost = Column(Float, nullable=True)
    service_description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)  # ACTIVE, INACTIVE, UNAVAILABLE
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    availabilities = relationship(
        "ProviderAvailability",
        back_populates="vendor",
        cascade="all, delete-orphan",
        lazy="select",
    )
    assignments = relationship(
        "VendorAssignment",
        back_populates="vendor",
        cascade="all, delete-orphan",
        lazy="select",
    )
