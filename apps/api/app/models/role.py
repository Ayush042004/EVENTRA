"""SQLAlchemy Model: Role"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.permission import role_permissions


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)  # MAIN_ORGANIZER, EVENT_MANAGER, COLLABORATOR, VENDOR, VIEWER
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="select")
    members = relationship("EventMember", back_populates="role_rel", lazy="select")
