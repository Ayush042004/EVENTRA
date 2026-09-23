"""Provider Deduplication and Upsert Service.

Implements a 5-tier deduplication strategy to prevent duplicate records
and enriches existing provider profiles with fresh discovered metadata.
"""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.vendor import Vendor
from app.integrations.google_maps_scraper.models import NormalizedProvider


# Default baseline cost estimations for providers lacking explicit quotes,
# enabling immediate eligibility in the Recovery Engine (which skips null base_cost).
DEFAULT_CATEGORY_BASE_COSTS = {
    "CATERING": 3500.0,
    "VENUE": 15000.0,
    "DECOR": 4000.0,
    "PHOTOGRAPHY": 2500.0,
    "VIDEOGRAPHY": 3000.0,
    "DJ_MUSIC": 1800.0,
    "LIGHTING": 2200.0,
    "AV_TECH": 2800.0,
    "ENTERTAINMENT": 3500.0,
    "TRANSPORT": 1500.0,
    "SECURITY": 1200.0,
    "STAFFING": 1000.0,
    "MAKEUP_STYLING": 1500.0,
    "PRINTING": 800.0,
    "RENTALS": 2000.0,
    "FLORIST": 1200.0,
    "PRODUCTION": 5000.0,
    "CLEANING": 800.0,
    "OTHER": 1500.0,
}


class ProviderDeduplicator:
    """Matches, deduplicates, and upserts discovered providers into the Vendor table."""

    def __init__(self, db: Session):
        self.db = db

    def _extract_domain(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        try:
            domain = urlparse(url).netloc.lower()
            return domain[4:] if domain.startswith("www.") else domain
        except Exception:
            return None

    def find_match(self, provider: NormalizedProvider) -> Optional[Vendor]:
        """Evaluates existing vendors using a 5-tier matching hierarchy."""
        # Tier 1: Strong identifier (source + source_id)
        if provider.source and provider.source_id:
            match = (
                self.db.query(Vendor)
                .filter(
                    Vendor.source == provider.source,
                    Vendor.source_id == provider.source_id,
                )
                .first()
            )
            if match:
                return match

        # Tier 2: Exact Google Maps URL or CID match
        if provider.maps_url:
            clean_url = provider.maps_url.strip().lower()
            match = (
                self.db.query(Vendor)
                .filter(func.lower(Vendor.maps_url) == clean_url)
                .first()
            )
            if match:
                return match

            cid_match = re.search(r"cid=([0-9a-zA-Z_]+)", clean_url)
            if cid_match:
                cid = cid_match.group(1)
                match = (
                    self.db.query(Vendor)
                    .filter(Vendor.maps_url.isnot(None), Vendor.maps_url.contains(f"cid={cid}"))
                    .first()
                )
                if match:
                    return match

        # Tier 3: Normalized website domain (ignoring generic engines & directories)
        GENERIC_DOMAINS = {"google.com", "maps.google.com", "instagram.com", "facebook.com", "yelp.com", "example.com"}
        prov_domain = self._extract_domain(provider.website)
        if prov_domain and len(prov_domain) > 4 and prov_domain not in GENERIC_DOMAINS:
            candidates = (
                self.db.query(Vendor)
                .filter(Vendor.website.isnot(None))
                .all()
            )
            for cand in candidates:
                cand_domain = self._extract_domain(cand.website)
                if cand_domain and cand_domain not in GENERIC_DOMAINS and cand_domain == prov_domain:
                    return cand

        # Tier 4: Contact phone number (ignoring generic toll-free/dummy numbers)
        GENERIC_PHONES = {"+1-800-eventra", "+1800eventra", "0000000000", "1234567890"}
        if provider.phone and len(provider.phone) >= 8 and provider.phone.strip().lower() not in GENERIC_PHONES:
            match = (
                self.db.query(Vendor)
                .filter(Vendor.contact_phone == provider.phone)
                .first()
            )
            if match:
                return match

        # Tier 5: Normalized name + city
        name_clean = provider.name.strip().lower()
        city_clean = provider.city.strip().lower()
        if name_clean:
            match = (
                self.db.query(Vendor)
                .filter(
                    func.lower(Vendor.name) == name_clean,
                    func.lower(Vendor.city) == city_clean,
                )
                .first()
            )
            if match:
                return match

        return None

    def upsert_provider(
        self,
        provider: NormalizedProvider,
        commit: bool = True,
    ) -> Tuple[Vendor, bool]:
        """Upserts a normalized provider. Returns (vendor_record, is_new)."""
        existing = self.find_match(provider)

        cat_upper = provider.category.strip().upper()
        base_cost = provider.base_cost  # Sourced from legitimate provider data only; None if unavailable

        if existing:
            # Enrich existing record
            if not existing.address and provider.address:
                existing.address = provider.address
            if not existing.latitude and provider.latitude:
                existing.latitude = provider.latitude
            if not existing.longitude and provider.longitude:
                existing.longitude = provider.longitude
            if not existing.website and provider.website:
                existing.website = provider.website
            if not existing.maps_url and provider.maps_url:
                existing.maps_url = provider.maps_url
            if not existing.contact_phone and provider.phone:
                existing.contact_phone = provider.phone
            if not existing.contact_email and provider.email:
                existing.contact_email = provider.email
            if provider.rating is not None:
                existing.rating = provider.rating
            if provider.review_count is not None:
                existing.review_count = provider.review_count
            if provider.raw_category and not existing.raw_category:
                existing.raw_category = provider.raw_category
            if provider.capabilities:
                existing_caps = set(existing.capabilities or [])
                existing_caps.update(provider.capabilities)
                existing.capabilities = sorted(existing_caps)
            if provider.classification_confidence:
                existing.classification_confidence = max(
                    existing.classification_confidence or 0.0,
                    provider.classification_confidence,
                )
            if provider.base_cost is not None:
                existing.base_cost = provider.base_cost

            if commit:
                self.db.commit()
                self.db.refresh(existing)
            return existing, False

        # Create new vendor
        new_vendor = Vendor(
            name=provider.name.strip(),
            category=cat_upper,
            city=provider.city.strip(),
            address=provider.address,
            latitude=provider.latitude,
            longitude=provider.longitude,
            contact_name=provider.name.strip(),
            contact_email=provider.email,
            contact_phone=provider.phone,
            website=provider.website,
            maps_url=provider.maps_url,
            base_cost=base_cost,
            rating=provider.rating,
            review_count=provider.review_count,
            service_description=provider.description or f"Discovered provider for {cat_upper}",
            status="ACTIVE",
            source=provider.source or "GOOGLE_MAPS",
            source_id=provider.source_id,
            raw_category=provider.raw_category,
            capabilities=provider.capabilities or [],
            classification_confidence=provider.classification_confidence or 0.85,
        )
        self.db.add(new_vendor)
        if commit:
            self.db.commit()
            self.db.refresh(new_vendor)
        return new_vendor, True
