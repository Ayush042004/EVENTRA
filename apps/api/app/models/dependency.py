"""SQLAlchemy Model: Dependency"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from app.db.session import Base
import uuid
from datetime import datetime

class Dependency(Base):
    __tablename__ = "dependencys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
