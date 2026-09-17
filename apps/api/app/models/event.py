"""SQLAlchemy Model: Event"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=utc_now)
