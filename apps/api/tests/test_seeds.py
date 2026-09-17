"""Tests for Development/Demo Seed Data Loading"""
from sqlalchemy.orm import Session
from seeds.seed_runner import seed_venues, seed_vendors, run_seeds
from app.models.venue import Venue
from app.models.vendor import Vendor


def test_seed_runner(db_session: Session):
    """Verifies that demo seeds load deterministically and are idempotent."""
    # First seed run
    summary = run_seeds(db=db_session)
    assert summary["status"] == "success"
    assert summary["venues_seeded"] > 0
    assert summary["vendors_seeded"] > 0

    venues_count = db_session.query(Venue).count()
    vendors_count = db_session.query(Vendor).count()
    assert venues_count == summary["venues_seeded"]
    assert vendors_count == summary["vendors_seeded"]

    # Second seed run (idempotency check: should insert 0 new records)
    second_summary = run_seeds(db=db_session)
    assert second_summary["venues_seeded"] == 0
    assert second_summary["vendors_seeded"] == 0
    assert db_session.query(Venue).count() == venues_count
    assert db_session.query(Vendor).count() == vendors_count
