"""Pydantic Schemas: BudgetItem"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BudgetItemBase(BaseModel):
    name: str
    category: str
    estimated_amount: Decimal = Decimal("0.00")
    actual_amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    status: str = "PLANNED"


class BudgetItemCreate(BudgetItemBase):
    pass


class BudgetItemResponse(BudgetItemBase):
    id: str
    event_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
