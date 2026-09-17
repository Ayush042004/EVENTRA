"""SQLAlchemy Model: EventMember"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import RoleType


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EventMember(Base):
    __tablename__ = "event_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default=RoleType.COLLABORATOR.value)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_members_event_user"),
    )

    event = relationship("Event", back_populates="members")
    user = relationship("User", back_populates="memberships")
    role_rel = relationship("Role", back_populates="members")
