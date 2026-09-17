"""SQLAlchemy Model: Permission"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # VIEW, MINOR_CHANGE, CRITICAL_CHANGE, APPROVE
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
