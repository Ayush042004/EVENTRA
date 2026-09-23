"""Domain Service: VendorService (Provider Network)

Coordinates discovery, filtering, availability checks, category validation,
and assignment representations for providers/vendors.
"""
import math
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.vendor import Vendor
from app.models.provider_availability import ProviderAvailability
from app.models.vendor_assignment import VendorAssignment
from app.models.event import Event
from app.models.venue import Venue
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
    ProviderDiscoveryRequest,
)
from app.integrations.registry import registry
from app.services.provider_classifier import ProviderClassifier
from app.services.deduplication import ProviderDeduplicator
from app.integrations.google_maps_scraper.models import NormalizedProvider
from app.integrations.google_maps_scraper.queries import build_discovery_query


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class VendorService:
    """Coordinates business logic and enforces domain invariants for Providers/Vendors."""

    def __init__(self, db: Session):
        self.db = db

    def create_vendor(self, vendor_in: VendorCreate) -> Vendor:
        """Creates a new provider record."""
        vendor = Vendor(
            name=vendor_in.name.strip(),
            category=vendor_in.category.strip(),
            city=vendor_in.city.strip(),
            address=vendor_in.address.strip() if vendor_in.address else None,
            latitude=vendor_in.latitude,
            longitude=vendor_in.longitude,
            contact_name=vendor_in.contact_name.strip() if vendor_in.contact_name else None,
            contact_email=vendor_in.contact_email.strip() if vendor_in.contact_email else None,
            contact_phone=vendor_in.contact_phone.strip() if vendor_in.contact_phone else None,
            website=vendor_in.website.strip() if vendor_in.website else None,
            maps_url=vendor_in.maps_url.strip() if vendor_in.maps_url else None,
            base_cost=vendor_in.base_cost,
            rating=vendor_in.rating,
            review_count=vendor_in.review_count,
            service_description=vendor_in.service_description.strip() if vendor_in.service_description else None,
            status=vendor_in.status.strip().upper(),
            source=vendor_in.source.strip().upper() if vendor_in.source else "INTERNAL",
            source_id=vendor_in.source_id.strip() if vendor_in.source_id else None,
            raw_category=vendor_in.raw_category.strip() if vendor_in.raw_category else None,
            capabilities=vendor_in.capabilities or [],
            classification_confidence=vendor_in.classification_confidence,
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

    def discover_providers(
        self,
        request: ProviderDiscoveryRequest,
        event_id: Optional[str] = None,
    ) -> Tuple[List[Vendor], int, int, str, List[str]]:
        """Discovers providers from Google Maps, normalizes, classifies into EVENTRA taxonomy,
        deduplicates against the existing database, and persists the results.
        Returns: (saved_vendors, total_created, total_updated, source, queries_used)
        """
        adapter = registry.get_google_maps_scraper()

        category = (request.category or "OTHER").strip().upper()
        city = (request.location or "Seattle").strip()

        keywords = build_discovery_query(
            category=category,
            custom_query=request.query,
            location=city,
        )

        res = adapter.search_providers(
            category=category,
            city=city,
            query=request.query,
            latitude=request.latitude,
            longitude=request.longitude,
            limit=request.limit,
        )

        raw_list = res.data or []
        source_label = res.source.value if hasattr(res.source, "value") else str(res.source)

        deduplicator = ProviderDeduplicator(self.db)
        saved_vendors: List[Vendor] = []
        created_count = 0
        updated_count = 0

        # Pre-fetch assigned vendor IDs if event_id is available
        assigned_vendor_ids = set()
        if event_id:
            assigned_vendor_ids = {a.vendor_id for a in self.get_assignments_for_event(event_id)}

        for item in raw_list:
            if isinstance(item, dict):
                norm_p = NormalizedProvider(**item)
            else:
                norm_p = item

            # Classify into EVENTRA's controlled taxonomy strictly based on evidence
            classification = ProviderClassifier.classify(
                name=norm_p.name,
                raw_category=norm_p.raw_category or norm_p.category,
                description=norm_p.description,
                city=norm_p.city,
                website=norm_p.website,
            )

            # Preserve raw category from discovery source and set evidence-based controlled category
            norm_p.raw_category = norm_p.raw_category or norm_p.category
            norm_p.category = classification.category
            norm_p.capabilities = classification.capabilities
            norm_p.classification_confidence = classification.confidence
            norm_p.classification_reason = classification.reason

            # STRICT CLASSIFICATION RULE:
            # Requested category is a filter/intent, NEVER evidence.
            # If the provider does not match the requested category, strictly exclude it.
            if category != "OTHER" and norm_p.category != category:
                continue

            vendor, is_new = deduplicator.upsert_provider(norm_p, commit=False)

            # Set assignment status
            vendor.is_assigned = (vendor.id in assigned_vendor_ids)

            # Calculate distance from request coordinates if provided
            if (
                request.latitude is not None
                and request.longitude is not None
                and vendor.latitude is not None
                and vendor.longitude is not None
            ):
                vendor.distance_km = haversine_distance_km(
                    request.latitude, request.longitude, vendor.latitude, vendor.longitude
                )
            else:
                vendor.distance_km = None

            # Apply radius filtering if specified
            if request.radius_km is not None and vendor.distance_km is not None:
                if vendor.distance_km > request.radius_km:
                    continue  # Filter out providers outside requested radius

            saved_vendors.append(vendor)
            if is_new:
                created_count += 1
            else:
                updated_count += 1

        # Single batch commit for all upserted providers (prevents remote DB latency bottleneck)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        # Sort by distance if available (closest first)
        saved_vendors.sort(
            key=lambda v: getattr(v, "distance_km", None) if getattr(v, "distance_km", None) is not None else 99999.0
        )

        return saved_vendors, created_count, updated_count, source_label, keywords

    def discover_providers_for_event(
        self,
        event_id: str,
        request: ProviderDiscoveryRequest,
    ) -> Tuple[List[Vendor], int, int, str, List[str], Optional[Tuple[float, float]], Optional[str], str]:
        """Context-aware provider discovery using the event's venue, location, and requirement.

        Supports:
        - Natural language search parsing ("photographers near venue", "wedding caterers within 10km")
        - 3-tier Location Resolution:
            1. REGION / Explicit Location: geocoded via existing adapter to obtain coordinates
            2. NEAR_ME: browser/user GPS coordinates
            3. NEAR_EVENT (Default): event venue coordinates or geocoded event location
        - Deterministic Haversine distance calculation and radius filtering
        - Real source rating and review counts
        - Event assignment status
        """
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event with id '{event_id}' not found")

        from app.integrations.google_maps_scraper.queries import parse_discovery_query
        from app.services.geospatial_service import geospatial_discovery

        # 1. Natural Language Query Parsing
        parsed = {}
        if request.query and request.query.strip():
            parsed = parse_discovery_query(request.query)

        category = (request.category or parsed.get("category") or "OTHER").strip().upper()
        radius_km = request.radius_km or parsed.get("radius_km")
        parsed_anchor = parsed.get("anchor_mode")
        custom_loc = request.location or parsed.get("location")
        clean_query = parsed.get("clean_query") if parsed.get("clean_query") else request.query

        # Determine anchor mode (explicit REGION takes precedence if custom_loc provided)
        if custom_loc and (not request.anchor_mode or request.anchor_mode == "NEAR_EVENT" or parsed_anchor == "REGION"):
            anchor_mode = "REGION"
        else:
            anchor_mode = (request.anchor_mode or parsed_anchor or "NEAR_EVENT").strip().upper()

        # 2. Location Anchor Resolution
        anchor_lat: Optional[float] = None
        anchor_lon: Optional[float] = None
        anchor_label: Optional[str] = None
        search_city: str = "Seattle"

        if (anchor_mode == "REGION" or custom_loc) and custom_loc:
            # Explicit location takes top priority: geocode via existing geocoding adapter
            search_city = geospatial_discovery.clean_city_name(custom_loc)
            anchor_lat, anchor_lon = geospatial_discovery.resolve_city_center(search_city)
            anchor_label = search_city

        elif anchor_mode == "NEAR_ME" and request.latitude is not None and request.longitude is not None:
            # Device/Browser coordinates
            anchor_lat = request.latitude
            anchor_lon = request.longitude
            anchor_label = "Your Location"
            base_loc = getattr(event, "location", "Seattle") or "Seattle"
            search_city = geospatial_discovery.clean_city_name(base_loc)

        else:
            # Default / NEAR_EVENT: Event Venue coordinates or Event Location
            venue = None
            if getattr(event, "venue_id", None):
                venue = self.db.query(Venue).filter(Venue.id == event.venue_id).first()

            if venue and venue.latitude is not None and venue.longitude is not None:
                anchor_lat = venue.latitude
                anchor_lon = venue.longitude
                anchor_label = f"Venue: {venue.name}"
                search_city = venue.city or "Seattle"
            elif getattr(event, "location", None):
                search_city = geospatial_discovery.clean_city_name(event.location)
                anchor_lat, anchor_lon = geospatial_discovery.resolve_city_center(search_city)
                anchor_label = event.location
            elif request.latitude is not None and request.longitude is not None:
                anchor_lat = request.latitude
                anchor_lon = request.longitude
                anchor_label = "Event Location"
                search_city = "Seattle"
            else:
                search_city = "Seattle"
                anchor_lat, anchor_lon = geospatial_discovery.resolve_city_center("Seattle")
                anchor_label = "Seattle, WA"

        search_city = geospatial_discovery.clean_city_name(search_city)

        enriched_request = ProviderDiscoveryRequest(
            category=category,
            query=clean_query,
            location=search_city,
            latitude=anchor_lat,
            longitude=anchor_lon,
            radius_km=radius_km,
            anchor_mode=anchor_mode,
            limit=request.limit,
            use_real_scraper=request.use_real_scraper,
        )

        vendors, created, updated, source, queries = self.discover_providers(enriched_request, event_id=event_id)

        # 3. Post-Process Distance Calculation, Radius Filtering & Assignment Status
        assigned_vendor_ids = {a.vendor_id for a in self.get_assignments_for_event(event_id)}

        processed_vendors: List[Vendor] = []
        for v in vendors:
            v.is_assigned = (v.id in assigned_vendor_ids)

            if anchor_lat is not None and anchor_lon is not None and v.latitude is not None and v.longitude is not None:
                v.distance_km = haversine_distance_km(anchor_lat, anchor_lon, v.latitude, v.longitude)
            else:
                v.distance_km = None

            if radius_km is not None and v.distance_km is not None:
                if v.distance_km > radius_km:
                    continue

            processed_vendors.append(v)

        processed_vendors.sort(
            key=lambda item: getattr(item, "distance_km", None) if getattr(item, "distance_km", None) is not None else 99999.0
        )

        anchor_coords = (anchor_lat, anchor_lon) if (anchor_lat is not None and anchor_lon is not None) else None
        return processed_vendors, created, updated, source, queries, anchor_coords, anchor_label, anchor_mode

