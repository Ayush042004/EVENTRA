"""Tests for 5-tier Provider Deduplication and Upsert Logic."""
import pytest
from sqlalchemy.orm import Session

from app.models.vendor import Vendor
from app.services.deduplication import ProviderDeduplicator
from app.integrations.google_maps_scraper.models import NormalizedProvider


def test_deduplication_by_source_id(db_session: Session):
    dedup = ProviderDeduplicator(db_session)

    # Seed an existing vendor with source_id
    existing = Vendor(
        name="Noida Star Catering",
        category="CATERING",
        city="Noida",
        source="GOOGLE_MAPS",
        source_id="cid_123456",
        base_cost=3000.0,
    )
    db_session.add(existing)
    db_session.commit()

    # Discovered provider with matching source_id but slightly different title
    discovered = NormalizedProvider(
        source="GOOGLE_MAPS",
        source_id="cid_123456",
        name="Noida Star Catering Services Pvt Ltd",
        category="CATERING",
        city="Noida",
        rating=4.8,
        review_count=90,
    )

    matched = dedup.find_match(discovered)
    assert matched is not None
    assert matched.id == existing.id

    upserted, is_new = dedup.upsert_provider(discovered)
    assert is_new is False
    assert upserted.id == existing.id
    assert upserted.rating == 4.8
    assert upserted.review_count == 90


def test_deduplication_by_maps_url(db_session: Session):
    dedup = ProviderDeduplicator(db_session)

    existing = Vendor(
        name="Aura Decorators",
        category="DECOR",
        city="Delhi",
        maps_url="https://maps.google.com/?cid=778899",
    )
    db_session.add(existing)
    db_session.commit()

    discovered = NormalizedProvider(
        name="Aura Luxury Wedding Decor",
        category="DECOR",
        city="Delhi",
        maps_url="https://maps.google.com/?cid=778899&hl=en",
    )

    matched = dedup.find_match(discovered)
    assert matched is not None
    assert matched.id == existing.id


def test_deduplication_by_website_domain(db_session: Session):
    dedup = ProviderDeduplicator(db_session)

    existing = Vendor(
        name="Sound Pro Systems",
        category="AV_TECH",
        city="Gurugram",
        website="https://www.soundprosystems.in",
    )
    db_session.add(existing)
    db_session.commit()

    discovered = NormalizedProvider(
        name="Sound Pro Audio Rentals",
        category="AV_TECH",
        city="Gurugram",
        website="https://soundprosystems.in/catalog",
    )

    matched = dedup.find_match(discovered)
    assert matched is not None
    assert matched.id == existing.id


def test_deduplication_by_phone(db_session: Session):
    dedup = ProviderDeduplicator(db_session)

    existing = Vendor(
        name="City Bouncers & Security",
        category="SECURITY",
        city="Noida",
        contact_phone="+919876543210",
    )
    db_session.add(existing)
    db_session.commit()

    discovered = NormalizedProvider(
        name="City Guard Services",
        category="SECURITY",
        city="Noida",
        phone="+919876543210",
    )

    matched = dedup.find_match(discovered)
    assert matched is not None
    assert matched.id == existing.id


def test_deduplication_by_name_and_city(db_session: Session):
    dedup = ProviderDeduplicator(db_session)

    existing = Vendor(
        name="Moonlight DJ Crew",
        category="DJ_MUSIC",
        city="Noida",
    )
    db_session.add(existing)
    db_session.commit()

    discovered = NormalizedProvider(
        name="moonlight dj crew",
        category="DJ_MUSIC",
        city="noida",
    )

    matched = dedup.find_match(discovered)
    assert matched is not None
    assert matched.id == existing.id


def test_new_provider_creation(db_session: Session):
    dedup = ProviderDeduplicator(db_session)

    discovered = NormalizedProvider(
        name="Brand New Unique Caterers",
        category="CATERING",
        city="Noida",
        address="Sector 18, Noida",
        phone="+919999988888",
        rating=4.9,
        review_count=120,
    )

    matched = dedup.find_match(discovered)
    assert matched is None

    vendor, is_new = dedup.upsert_provider(discovered)
    assert is_new is True
    assert vendor.id is not None
    assert vendor.name == "Brand New Unique Caterers"
    assert vendor.category == "CATERING"
    assert vendor.base_cost is not None  # Baseline cost assigned for recovery engine compatibility
