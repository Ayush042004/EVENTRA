"""API Route: Vendors (Provider Network Discovery, Availability, and Assignment)"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.services.vendor_service import VendorService
from app.schemas.vendor import (
    VendorCreate,
    VendorResponse,
    ProviderAvailabilityCreate,
    ProviderAvailabilityResponse,
    ProviderAvailabilityResult,
    VendorAssignmentCreate,
    VendorAssignmentResponse,
    CategoryValidationResult,
    PaginatedVendorsResponse,
)
from app.core.exceptions import AppException

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("", response_model=PaginatedVendorsResponse)
def search_vendors(
    category: Optional[str] = Query(None, description="Provider category (e.g. catering, sound, lighting)"),
    city: Optional[str] = Query(None, description="Filter by city (case-insensitive)"),
    status: Optional[str] = Query("ACTIVE", description="Operational status"),
    max_base_cost: Optional[float] = Query(None, ge=0.0, description="Maximum base cost"),
    available_from: Optional[datetime] = Query(None, description="Start of availability window"),
    available_to: Optional[datetime] = Query(None, description="End of availability window"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db_session),
):
    """Deterministically searches and filters providers."""
    service = VendorService(db)
    try:
        items, total = service.search_vendors(
            category=category,
            city=city,
            status=status,
            max_base_cost=max_base_cost,
            available_from=available_from,
            available_to=available_to,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise AppException(message=str(exc), status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_PARAMETERS")

    return PaginatedVendorsResponse(
        total=total,
        items=[VendorResponse.model_validate(v) for v in items],
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_in: VendorCreate,
    db: Session = Depends(get_db_session),
):
    """Registers a new provider in the provider network."""
    service = VendorService(db)
    vendor = service.create_vendor(vendor_in)
    return VendorResponse.model_validate(vendor)


@router.get("/categories/validate", response_model=CategoryValidationResult)
def validate_category(
    domain: str = Query(..., description="Event domain (e.g., wedding, college_fest, conference)"),
    category: str = Query(..., description="Provider category to validate"),
    db: Session = Depends(get_db_session),
):
    """Deterministically checks if a provider category is valid and required for an event domain."""
    service = VendorService(db)
    try:
        return service.validate_category_for_domain(domain, category)
    except ValueError as exc:
        raise AppException(message=str(exc), status_code=status.HTTP_400_BAD_REQUEST, code="UNKNOWN_DOMAIN")


@router.get("/assignments/event/{event_id}", response_model=List[VendorAssignmentResponse])
def get_assignments_for_event(
    event_id: str,
    db: Session = Depends(get_db_session),
):
    """Lists all provider assignments for an event with stable ordering."""
    service = VendorService(db)
    assignments = service.get_assignments_for_event(event_id)
    return [VendorAssignmentResponse.model_validate(a) for a in assignments]


@router.post("/assignments", response_model=VendorAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_in: VendorAssignmentCreate,
    db: Session = Depends(get_db_session),
):
    """Records an operational provider assignment for an event."""
    service = VendorService(db)
    try:
        assignment = service.create_assignment(assignment_in)
        return VendorAssignmentResponse.model_validate(assignment)
    except ValueError as exc:
        raise AppException(message=str(exc), status_code=status.HTTP_404_NOT_FOUND, code="RESOURCE_NOT_FOUND")


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: str,
    db: Session = Depends(get_db_session),
):
    """Retrieves single provider record by ID."""
    service = VendorService(db)
    vendor = service.get_vendor(vendor_id)
    if not vendor:
        raise AppException(
            message=f"Provider '{vendor_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            code="PROVIDER_NOT_FOUND",
        )
    return VendorResponse.model_validate(vendor)


@router.post("/{vendor_id}/availability", response_model=ProviderAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def add_provider_availability(
    vendor_id: str,
    avail_in: ProviderAvailabilityCreate,
    db: Session = Depends(get_db_session),
):
    """Records provider availability or blackout window (AVAILABLE, BOOKED, BLOCKED)."""
    service = VendorService(db)
    try:
        slot = service.add_provider_availability(vendor_id, avail_in)
        return ProviderAvailabilityResponse.model_validate(slot)
    except ValueError as exc:
        err_msg = str(exc)
        if "not found" in err_msg:
            raise AppException(message=err_msg, status_code=status.HTTP_404_NOT_FOUND, code="PROVIDER_NOT_FOUND")
        raise AppException(message=err_msg, status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_TIMEFRAME")


@router.get("/{vendor_id}/availability", response_model=ProviderAvailabilityResult)
def check_provider_availability(
    vendor_id: str,
    start_datetime: datetime = Query(..., description="Start of requested window"),
    end_datetime: datetime = Query(..., description="End of requested window"),
    db: Session = Depends(get_db_session),
):
    """Evaluates provider availability for a requested time window."""
    service = VendorService(db)
    try:
        return service.check_provider_availability(
            vendor_id=vendor_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
    except ValueError as exc:
        err_msg = str(exc)
        if "not found" in err_msg:
            raise AppException(message=err_msg, status_code=status.HTTP_404_NOT_FOUND, code="PROVIDER_NOT_FOUND")
        raise AppException(message=err_msg, status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_TIMEFRAME")
