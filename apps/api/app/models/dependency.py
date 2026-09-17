"""SQLAlchemy Model: TaskDependency"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship, validates
from app.db.base import Base
from app.models.enums import DependencyType


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    predecessor_task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    successor_task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(String(50), default=DependencyType.FINISH_TO_START.value, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("predecessor_task_id", "successor_task_id", name="uq_task_dependencies_pred_succ"),
        CheckConstraint("predecessor_task_id != successor_task_id", name="ck_task_dependencies_prevent_self_dep"),
    )

    predecessor_task = relationship(
        "Task",
        foreign_keys=[predecessor_task_id],
        back_populates="outgoing_dependencies",
    )
    successor_task = relationship(
        "Task",
        foreign_keys=[successor_task_id],
        back_populates="incoming_dependencies",
    )
    event = relationship("Event")

    @validates("successor_task_id")
    def validate_successor(self, key, successor_id):
        if self.predecessor_task_id and successor_id == self.predecessor_task_id:
            raise ValueError("Self-dependency detected: predecessor and successor tasks cannot be the same.")
        return successor_id

    @validates("predecessor_task_id")
    def validate_predecessor(self, key, predecessor_id):
        if self.successor_task_id and predecessor_id == self.successor_task_id:
            raise ValueError("Self-dependency detected: predecessor and successor tasks cannot be the same.")
        return predecessor_id


# Alias for backwards compatibility
Dependency = TaskDependency
