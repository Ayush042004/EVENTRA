"""Domain Service: VendorService (Provider Network)

Coordinates discovery, filtering, availability checks, category validation,
and assignment representations for providers/vendors.
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.vendor import Vendor
from app.models.provider_availability import ProviderAvailability
from app.models.vendor_assignment import VendorAssignment
from app.domains.registry import (
    is_provider_category_compatible,
    get_domain_provider_categories,
    get_domain,
)
from app.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    ProviderAvailabilityCreate,
    ProviderAvailabilityResult,
    ProviderAvailabilityResponse,
    VendorAssignmentCreate,
    VendorAssignmentUpdate,
    CategoryValidationResult,
)


class VendorService:
    """Coordinates business logic and enforces domain invariants for Providers/Vendors."""

    def __init__(self, db: Session):
        self.db = db

    def create_vendor(self, vendor_in: VendorCreate) -> Vendor:
        """Creates a new provider record."""
        vendor = Vendor(
            name=vendor_in.name.strip(),
            category=vendor_in.category.strip().lower(),
            city=vendor_in.city.strip(),
            contact_name=vendor_in.contact_name.strip() if vendor_in.contact_name else None,
            contact_email=vendor_in.contact_email.strip() if vendor_in.contact_email else None,
            contact_phone=vendor_in.contact_phone.strip() if vendor_in.contact_phone else None,
            base_cost=vendor_in.base_cost,
            service_description=vendor_in.service_description.strip() if vendor_in.service_description else None,
            status=vendor_in.status.strip().upper(),
        )
        self.db.add(vendor)
        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Retrieves provider by ID."""
        return self.db.query(Vendor).filter(Vendor.id == vendor_id).first()

    def update_vendor(self, vendor_id: str, vendor_in: VendorUpdate) -> Optional[Vendor]:
        """Updates provider attributes."""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return None

        update_data = vendor_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "category" and value is not None:
                vendor.category = value.strip().lower()
            elif field == "status" and value is not None:
                vendor.status = value.strip().upper()
            elif isinstance(value, str):
                setattr(vendor, field, value.strip())
            else:
                setattr(vendor, field, value)

        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def search_vendors(
        self,
        category: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[str] = "ACTIVE",
        max_base_cost: Optional[float] = None,
        available_from: Optional[datetime] = None,
        available_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Vendor], int]:
        """Deterministically searches providers with multi-criteria filtering and pagination.

        Ordering is strictly stable: ORDER BY name ASC, id ASC.
        """
        query = self.db.query(Vendor)

        if category:
            query = query.filter(func.lower(Vendor.category) == category.strip().lower())

        if city:
            query = query.filter(func.lower(Vendor.city) == city.strip().lower())

        if status:
            query = query.filter(Vendor.status == status.strip().upper())

        if max_base_cost is not None:
            query = query.filter(Vendor.base_cost <= max_base_cost)

        # Availability filter
        if available_from and available_to:
            if available_from >= available_to:
                raise ValueError("available_from must be before available_to")

            conflict_subquery = (
                self.db.query(ProviderAvailability.vendor_id)
                .filter(
                    ProviderAvailability.status.in_(["BOOKED", "BLOCKED"]),
                    ProviderAvailability.start_datetime < available_to,
                    ProviderAvailability.end_datetime > available_from,
                )
                .subquery()
            )
            query = query.filter(~Vendor.id.in_(conflict_subquery))

        total = query.count()
        results = (
            query.order_by(Vendor.name.asc(), Vendor.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return results, total

    def add_provider_availability(
        self,
        vendor_id: str,
        avail_in: ProviderAvailabilityCreate,
    ) -> ProviderAvailability:
        """Records an availability slot for a provider."""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            raise ValueError(f"Provider with id '{vendor_id}' not found")

        if avail_in.start_datetime >= avail_in.end_datetime:
            raise ValueError("start_datetime must be strictly before end_datetime")

        slot = ProviderAvailability(
            vendor_id=vendor_id,
            start_datetime=avail_in.start_datetime,
            end_datetime=avail_in.end_datetime,
            status=avail_in.status.strip().upper(),
            notes=avail_in.notes.strip() if avail_in.notes else None,
        )
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def check_provider_availability(
        self,
        vendor_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> ProviderAvailabilityResult:
        """Evaluates whether a provider is available for the requested time window."""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            raise ValueError(f"Provider with id '{vendor_id}' not found")

        if start_datetime >= end_datetime:
            raise ValueError("start_datetime must be strictly before end_datetime")

        if vendor.status != "ACTIVE":
            return ProviderAvailabilityResult(
                vendor_id=vendor_id,
                is_available=False,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                conflicts=[],
                reason=f"Provider status is '{vendor.status}', not ACTIVE",
            )

        conflicts_query = self.db.query(ProviderAvailability).filter(
            ProviderAvailability.vendor_id == vendor_id,
            ProviderAvailability.status.in_(["BOOKED", "BLOCKED"]),
            ProviderAvailability.start_datetime < end_datetime,
            ProviderAvailability.end_datetime > start_datetime,
        ).order_by(ProviderAvailability.start_datetime.asc())

        conflicts = conflicts_query.all()
        conflict_responses = [
            ProviderAvailabilityResponse.model_validate(c) for c in conflicts
        ]

        is_available = len(conflicts) == 0
        reason = None if is_available else f"Found {len(conflicts)} conflicting booked/blocked window(s)"

        return ProviderAvailabilityResult(
            vendor_id=vendor_id,
            is_available=is_available,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            conflicts=conflict_responses,
            reason=reason,
        )

    def validate_category_for_domain(
        self,
        domain_name: str,
        category: str,
    ) -> CategoryValidationResult:
        """Validates if a category is supported by the domain specification."""
        domain = get_domain(domain_name)
        if not domain:
            raise ValueError(f"Unknown event domain '{domain_name}'")

        allowed = get_domain_provider_categories(domain_name)
        is_valid = is_provider_category_compatible(domain_name, category)

        return CategoryValidationResult(
            domain=domain_name,
            category=category,
            is_valid=is_valid,
            allowed_categories=allowed,
        )

    def create_assignment(
        self,
        assignment_in: VendorAssignmentCreate,
    ) -> VendorAssignment:
        """Records a provider assignment for an event."""
        vendor = self.get_vendor(assignment_in.vendor_id)
        if not vendor:
            raise ValueError(f"Provider with id '{assignment_in.vendor_id}' not found")

        assignment = VendorAssignment(
            event_id=assignment_in.event_id,
            vendor_id=assignment_in.vendor_id,
            category=assignment_in.category.strip().lower(),
            status=assignment_in.status.strip().upper(),
            agreed_cost=assignment_in.agreed_cost,
            notes=assignment_in.notes.strip() if assignment_in.notes else None,
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def update_assignment(
        self,
        assignment_id: str,
        update_in: VendorAssignmentUpdate,
    ) -> Optional[VendorAssignment]:
        """Updates an existing assignment."""
        assignment = self.db.query(VendorAssignment).filter(VendorAssignment.id == assignment_id).first()
        if not assignment:
            return None

        update_data = update_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "category" and value is not None:
                assignment.category = value.strip().lower()
            elif field == "status" and value is not None:
                assignment.status = value.strip().upper()
            elif isinstance(value, str):
                setattr(assignment, field, value.strip())
            else:
                setattr(assignment, field, value)

        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_assignments_for_event(self, event_id: str) -> List[VendorAssignment]:
        """Returns all vendor assignments for a specific event with deterministic ordering."""
        return (
            self.db.query(VendorAssignment)
            .filter(VendorAssignment.event_id == event_id)
            .order_by(VendorAssignment.created_at.asc(), VendorAssignment.id.asc())
            .all()
        )
