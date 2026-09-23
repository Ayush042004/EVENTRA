"""Tests for Provider Taxonomy Classification and Capabilities Extraction."""
import pytest
from app.services.provider_classifier import ProviderClassifier
from app.models.enums import ProviderCategory


def test_classify_catering():
    result = ProviderClassifier.classify(
        name="Sharma Caterers & Sweets",
        raw_category="Catering food and drink supplier",
        description="Specializing in pure veg live counter buffets for Indian weddings.",
        city="Noida",
    )
    assert result.category == "CATERING"
    assert result.confidence >= 0.85
    assert "pure_veg" in result.capabilities
    assert "live_counters" in result.capabilities or "buffet_setup" in result.capabilities


def test_classify_photography():
    result = ProviderClassifier.classify(
        name="Memories Cinematic Studio",
        raw_category="Wedding photographer",
        description="Award-winning candid photography and aerial drone shoots.",
        city="Delhi",
    )
    assert result.category == "PHOTOGRAPHY"
    assert result.confidence >= 0.80
    assert "candid_photography" in result.capabilities
    assert "aerial_drone_shots" in result.capabilities


def test_classify_dj_music():
    result = ProviderClassifier.classify(
        name="DJ Shadow Sound & Music",
        raw_category="Disc jockey",
        description="Professional party DJ sound console and dance floor setup.",
        city="Mumbai",
    )
    assert result.category == "DJ_MUSIC"
    assert result.confidence >= 0.80


def test_classify_lighting_and_av():
    result_light = ProviderClassifier.classify(
        name="Lumina Stage Lights",
        raw_category="Event lighting service",
        description="Truss lighting and moving heads for corporate galas.",
    )
    assert result_light.category == "LIGHTING"

    result_av = ProviderClassifier.classify(
        name="ClearSound Audiovisual Systems",
        raw_category="Audiovisual equipment rental",
        description="Wireless microphones and high lumen projectors.",
    )
    assert result_av.category == "AV_TECH"


def test_classify_security_and_transport():
    result_sec = ProviderClassifier.classify(
        name="Black Panther Bouncers",
        raw_category="Security guard service",
        description="VIP bouncers and crowd management for concerts.",
    )
    assert result_sec.category == "SECURITY"

    result_trans = ProviderClassifier.classify(
        name="Express Luxury Cab & Coach Rental",
        raw_category="Bus tour agency",
        description="Luxury car and AC coach fleet for wedding guest logistics.",
    )
    assert result_trans.category == "TRANSPORT"


def test_classify_ambiguous_falls_back_to_other():
    result = ProviderClassifier.classify(
        name="XYZ Global Enterprises LLC",
        raw_category="Business service",
        description="General business consultancy and administration.",
    )
    assert result.category == "OTHER"
    assert result.confidence <= 0.50
    assert "Below certainty threshold" in result.reason


def test_all_categories_belong_to_controlled_taxonomy():
    all_controlled = {c.value for c in ProviderCategory}
    for cat_key in ["CATERING", "VENUE", "DECOR", "PHOTOGRAPHY", "VIDEOGRAPHY", "DJ_MUSIC", "LIGHTING", "AV_TECH", "ENTERTAINMENT", "TRANSPORT", "SECURITY", "STAFFING", "MAKEUP_STYLING", "PRINTING", "RENTALS", "FLORIST", "PRODUCTION", "CLEANING", "OTHER"]:
        assert cat_key in all_controlled
