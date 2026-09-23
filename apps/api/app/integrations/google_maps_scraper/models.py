"""Data models for Google Maps Scraper Integration and Normalized Providers."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RawScraperJobCreate(BaseModel):
    """Payload sent to gosom/google-maps-scraper /api/v1/jobs endpoint."""
    name: str = "eventra-provider-discovery"
    keywords: List[str]
    lang: str = "en"
    zoom: int = 15
    lat: str
    lon: str
    fast_mode: bool = False
    radius: int = 10000
    depth: int = 5
    email: bool = False
    max_time: int = 60


class RawScraperJobStatus(BaseModel):
    """Job status returned by /api/v1/jobs/{id}."""
    id: str
    status: str
    error: Optional[str] = None


class RawScraperBusiness(BaseModel):
    """Represents a raw business record retrieved from the Google Maps scraper."""
    title: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    emails: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    review_rating: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    link: Optional[str] = None
    cid: Optional[str] = None
    place_id: Optional[str] = None
    description: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class NormalizedProvider(BaseModel):
    """Internal normalized representation between the scraper and EVENTRA's Provider Network."""
    source: str = "GOOGLE_MAPS"
    source_id: Optional[str] = None
    name: str
    category: str = "OTHER"  # Default EVENTRA taxonomy category
    raw_category: Optional[str] = None
    address: Optional[str] = None
    city: str = "Local"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    maps_url: Optional[str] = None
    description: Optional[str] = None
    base_cost: Optional[float] = None
    capabilities: List[str] = Field(default_factory=list)
    classification_confidence: float = 0.0
    classification_reason: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
