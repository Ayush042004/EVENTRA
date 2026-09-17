"""Pydantic Schemas: Vendor (Provider), Availability, Assignment, and Category Validation"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    base_cost: Optional[float] = Field(None, ge=0.0)
    service_description: Optional[str] = None
    status: str = Field(default="ACTIVE", max_length=50)


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    base_cost: Optional[float] = Field(None, ge=0.0)
    service_description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)


class VendorResponse(VendorBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderAvailabilityBase(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    status: str = Field(default="AVAILABLE", max_length=50)
    notes: Optional[str] = Field(None, max_length=500)


class ProviderAvailabilityCreate(ProviderAvailabilityBase):
    pass


class ProviderAvailabilityResponse(ProviderAvailabilityBase):
    id: str
    vendor_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderAvailabilityCheck(BaseModel):
    start_datetime: datetime
    end_datetime: datetime


class ProviderAvailabilityResult(BaseModel):
    vendor_id: str
    is_available: bool
    start_datetime: datetime
    end_datetime: datetime
    conflicts: List[ProviderAvailabilityResponse] = Field(default_factory=list)
    reason: Optional[str] = None


class VendorAssignmentBase(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=36)
    vendor_id: str = Field(..., min_length=1, max_length=36)
    category: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="REQUESTED", max_length=50)
    agreed_cost: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None


class VendorAssignmentCreate(VendorAssignmentBase):
    pass


class VendorAssignmentUpdate(BaseModel):
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    agreed_cost: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None


class VendorAssignmentResponse(VendorAssignmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryValidationResult(BaseModel):
    domain: str
    category: str
    is_valid: bool
    allowed_categories: List[str]


class PaginatedVendorsResponse(BaseModel):
    total: int
    items: List[VendorResponse]
    limit: int
    offset: int
