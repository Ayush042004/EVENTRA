"""Pydantic Schemas: Vendor (Provider), Availability, Assignment, and Category Validation"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    maps_url: Optional[str] = Field(None, max_length=500)
    base_cost: Optional[float] = Field(None, ge=0.0)
    rating: Optional[float] = None
    review_count: Optional[int] = None
    service_description: Optional[str] = None
    status: str = Field(default="ACTIVE", max_length=50)
    source: str = Field(default="INTERNAL", max_length=50)
    source_id: Optional[str] = Field(None, max_length=255)
    raw_category: Optional[str] = Field(None, max_length=255)
    capabilities: List[str] = Field(default_factory=list)
    classification_confidence: Optional[float] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    maps_url: Optional[str] = Field(None, max_length=500)
    base_cost: Optional[float] = Field(None, ge=0.0)
    rating: Optional[float] = None
    review_count: Optional[int] = None
    service_description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    capabilities: Optional[List[str]] = None


class VendorResponse(VendorBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderDiscoveryRequest(BaseModel):
    """Payload to discover providers from Google Maps."""
    category: Optional[str] = Field(None, description="EVENTRA category (e.g. CATERING, DECOR, DJ_MUSIC)")
    query: Optional[str] = Field(None, description="Custom search keywords (e.g. 'wedding caterers')")
    location: Optional[str] = Field(None, description="City or specific location string (e.g. 'Noida')")
    latitude: Optional[float] = Field(None, description="Optional geocoded latitude")
    longitude: Optional[float] = Field(None, description="Optional geocoded longitude")
    limit: int = Field(default=20, ge=1, le=100, description="Max providers to discover")
    use_real_scraper: bool = Field(default=True, description="Attempt real scraping if scraper service alive")


class ProviderDiscoveryResponse(BaseModel):
    """Result of provider discovery operation."""
    event_id: Optional[str] = None
    total_discovered: int
    total_created: int
    total_updated: int
    source: str
    query_used: List[str]
    items: List[VendorResponse]


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
