"""SQLAlchemy Model: Vendor_assignment"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from app.db.session import Base
import uuid
from datetime import datetime

class VendorAssignment(Base):
    __tablename__ = "vendor_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
