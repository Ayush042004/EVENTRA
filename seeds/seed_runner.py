"""Deterministic Seed Runner for EVENTRA Development/Demo Data"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.venue import Venue
from app.models.venue_availability import VenueAvailability
from app.models.vendor import Vendor
from app.models.provider_availability import ProviderAvailability


SEEDS_DIR = Path(__file__).resolve().parent


def seed_venues(db: Session) -> int:
    """Loads demo venues into database if not already present."""
    venues_path = SEEDS_DIR / "venues" / "demo_venues.json"
    if not venues_path.exists():
        return 0

    with open(venues_path, "r", encoding="utf-8") as f:
        venues_data = json.load(f)

    inserted = 0
    for v_data in venues_data:
        existing = db.query(Venue).filter(Venue.id == v_data["id"]).first()
        if existing:
            continue

        venue = Venue(
            id=v_data["id"],
            name=v_data["name"],
            address=v_data.get("address"),
            city=v_data["city"],
            latitude=v_data.get("latitude"),
            longitude=v_data.get("longitude"),
            capacity=v_data["capacity"],
            venue_type=v_data["venue_type"],
            contact_email=v_data.get("contact_email"),
            contact_phone=v_data.get("contact_phone"),
            hourly_rate=v_data.get("hourly_rate"),
            amenities=v_data.get("amenities", []),
            status=v_data.get("status", "ACTIVE"),
        )
        db.add(venue)

        for av in v_data.get("availabilities", []):
            slot = VenueAvailability(
                venue_id=venue.id,
                start_datetime=datetime.fromisoformat(av["start_datetime"]),
                end_datetime=datetime.fromisoformat(av["end_datetime"]),
                status=av.get("status", "AVAILABLE"),
                notes=av.get("notes"),
            )
            db.add(slot)

        inserted += 1

    db.commit()
    return inserted


def seed_vendors(db: Session) -> int:
    """Loads demo vendors into database if not already present."""
    vendors_path = SEEDS_DIR / "vendors" / "demo_vendors.json"
    if not vendors_path.exists():
        return 0

    with open(vendors_path, "r", encoding="utf-8") as f:
        vendors_data = json.load(f)

    inserted = 0
    for v_data in vendors_data:
        existing = db.query(Vendor).filter(Vendor.id == v_data["id"]).first()
        if existing:
            continue

        vendor = Vendor(
            id=v_data["id"],
            name=v_data["name"],
            category=v_data["category"],
            city=v_data["city"],
            contact_name=v_data.get("contact_name"),
            contact_email=v_data.get("contact_email"),
            contact_phone=v_data.get("contact_phone"),
            base_cost=v_data.get("base_cost"),
            service_description=v_data.get("service_description"),
            status=v_data.get("status", "ACTIVE"),
        )
        db.add(vendor)

        for av in v_data.get("availabilities", []):
            slot = ProviderAvailability(
                vendor_id=vendor.id,
                start_datetime=datetime.fromisoformat(av["start_datetime"]),
                end_datetime=datetime.fromisoformat(av["end_datetime"]),
                status=av.get("status", "AVAILABLE"),
                notes=av.get("notes"),
            )
            db.add(slot)

        inserted += 1

    db.commit()
    return inserted


def run_seeds(db: Optional[Session] = None) -> dict:
    """Runs all seed operations and returns summary counts."""
    session = db or SessionLocal()
    try:
        venues_count = seed_venues(session)
        vendors_count = seed_vendors(session)
        return {
            "status": "success",
            "venues_seeded": venues_count,
            "vendors_seeded": vendors_count,
        }
    finally:
        if db is None:
            session.close()


if __name__ == "__main__":
    result = run_seeds()
    print("Seed execution result:", result)
