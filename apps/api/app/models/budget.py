"""SQLAlchemy Model: BudgetItem"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # VENUE, CATERING, AV, DECOR, OPERATIONS, etc.
    estimated_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    actual_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(String(50), default="PLANNED", nullable=False)  # PLANNED, COMMITTED, PAID, CANCELLED
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    event = relationship("Event", back_populates="budget_items")


# Alias for backwards compatibility
Budget = BudgetItem
