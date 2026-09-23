"""Tests for Google Maps Scraper Normalizer and Query Generation."""
import pytest
from app.integrations.google_maps_scraper.models import RawScraperBusiness, NormalizedProvider
from app.integrations.google_maps_scraper.mapper import ProviderNormalizer
from app.integrations.google_maps_scraper.queries import build_discovery_query


def test_normalize_phone():
    assert ProviderNormalizer.normalize_phone("+91 (987) 654-3210") == "+919876543210"
    assert ProviderNormalizer.normalize_phone("011-23456789") == "01123456789"
    assert ProviderNormalizer.normalize_phone("123") is None  # Too short
    assert ProviderNormalizer.normalize_phone(None) is None


def test_normalize_website():
    assert ProviderNormalizer.normalize_website("http://www.royal-caterers.com/menu?utm_source=gmaps") == "https://royal-caterers.com/menu"
    assert ProviderNormalizer.normalize_website("eliteevents.in") == "https://eliteevents.in"
    assert ProviderNormalizer.normalize_website(None) is None


def test_extract_city():
    assert ProviderNormalizer.extract_city("Sector 62, Noida, Uttar Pradesh 201301") == "Noida"
    assert ProviderNormalizer.extract_city("Connaught Place, New Delhi, Delhi") == "New Delhi"
    assert ProviderNormalizer.extract_city("SingleStringAddress", default_city="Noida") == "Noida"
    assert ProviderNormalizer.extract_city(None, default_city="Fallback") == "Fallback"


def test_raw_to_normalized_mapping():
    raw = RawScraperBusiness(
        title="Grand Royal Caterers",
        category="Catering food and drink supplier",
        address="124 Expressway Road, Noida, UP 201301",
        phone="+91 9811223344",
        emails="contact@grandroyal.com, info@grandroyal.com",
        website="https://www.grandroyal.com/?ref=google",
        review_rating=4.7,
        review_count=185,
        latitude=28.5355,
        longitude=77.3910,
        link="https://maps.google.com/?cid=9876543210",
        description="Premium buffet catering and live food stalls for weddings and galas.",
    )

    norm = ProviderNormalizer.normalize(raw)
    assert norm.name == "Grand Royal Caterers"
    assert norm.city == "Noida"
    assert norm.phone == "+919811223344"
    assert norm.email == "contact@grandroyal.com"
    assert norm.website == "https://grandroyal.com"
    assert norm.rating == 4.7
    assert norm.review_count == 185
    assert norm.latitude == 28.5355
    assert norm.longitude == 77.3910
    assert norm.source_id == "9876543210"
    assert norm.source == "GOOGLE_MAPS"
    assert norm.raw_category == "Catering food and drink supplier"


def test_malformed_raw_data_handling():
    raw = RawScraperBusiness()
    norm = ProviderNormalizer.normalize(raw, default_city="San Francisco")
    assert norm.name == "Unknown Provider"
    assert norm.city == "San Francisco"
    assert norm.phone is None
    assert norm.rating is None
    assert norm.review_count is None


def test_build_discovery_query():
    # Category based
    queries = build_discovery_query(category="CATERING", location="Noida")
    assert any("cater" in q.lower() for q in queries)
    assert all("Noida" in q for q in queries)

    # Event type prefixing
    wedding_queries = build_discovery_query(category="CATERING", event_type="wedding", location="Delhi")
    assert any("wedding" in q.lower() for q in wedding_queries)

    # Custom query override
    custom = build_discovery_query(custom_query="live tandoor food counter", location="Noida")
    assert "live tandoor food counter in Noida" in custom
