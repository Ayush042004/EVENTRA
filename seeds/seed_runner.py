"""Deterministic Seed Runner for EVENTRA Development/Demo Data"""
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.venue import Venue
from app.models.venue_availability import VenueAvailability
from app.models.vendor import Vendor
from app.models.provider_availability import ProviderAvailability
from app.models.user import User
from app.models.event import Event
from app.models.task import Task
from app.models.dependency import TaskDependency
from app.services.planning_service import PlanningService
from app.engines.schedule.scheduler import ScheduleEngine
from app.engines.dependency.graph import DependencyGraph
from app.engines.dependency.traversal import CriticalPathCalculator
from app.engines.schedule.feasibility import ScheduleFeasibilityChecker


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


def seed_users(db: Session) -> int:
    """Seeds baseline demo operators and collaborators."""
    demo_users = [
        {
            "id": "anonymous_operator",
            "name": "Elena Vance (Ops Director)",
            "email": "elena.vance@eventra.local",
        },
        {
            "id": "collab_alex",
            "name": "Alex Rivera (Stage Lead)",
            "email": "alex.rivera@eventra.local",
        },
    ]
    inserted = 0
    for u_data in demo_users:
        if not db.query(User).filter(User.id == u_data["id"]).first():
            user = User(id=u_data["id"], name=u_data["name"], email=u_data["email"])
            db.add(user)
            inserted += 1
    db.commit()
    return inserted


def seed_demo_events(db: Session) -> int:
    """Seeds canonical demonstration events and runs planning pipeline."""
    demo_events = [
        {
            "id": "conference_demo",
            "owner_id": "anonymous_operator",
            "name": "Tech Launch Keynote 2026",
            "description": "Deterministic baseline demo tech conference with live operations, keynotes, and exhibition.",
            "event_type": "CONFERENCE",
            "location": "Civic Convention Hall, Seattle",
            "start_datetime": datetime(2026, 12, 1, 8, 0, 0),
            "end_datetime": datetime(2026, 12, 1, 18, 0, 0),
            "guest_count": 300,
            "total_budget": Decimal("60000.00"),
            "currency": "USD",
            "state": "NORMAL",
            "lifecycle_state": "DRAFT",
        },
        {
            "id": "college_fest_demo",
            "owner_id": "anonymous_operator",
            "name": "Springfest Gala 2026",
            "description": "Annual collegiate multi-stage arts and technical festival.",
            "event_type": "COLLEGE_FEST",
            "location": "North Campus Quad, Boston",
            "start_datetime": datetime(2026, 11, 15, 9, 0, 0),
            "end_datetime": datetime(2026, 11, 15, 23, 0, 0),
            "guest_count": 800,
            "total_budget": Decimal("50000.00"),
            "currency": "USD",
            "state": "NORMAL",
            "lifecycle_state": "DRAFT",
        },
    ]
    inserted = 0
    for ev_data in demo_events:
        existing = db.query(Event).filter(Event.id == ev_data["id"]).first()
        if not existing:
            event = Event(**ev_data)
            db.add(event)
            db.commit()
            inserted += 1

            # Generate full plan for conference_demo
            if ev_data["id"] == "conference_demo":
                try:
                    planner = PlanningService(db)
                    planner.generate_plan(event.id)

                    # Compute and persist initial schedule
                    tasks = db.query(Task).filter(Task.event_id == event.id).all()
                    deps = db.query(TaskDependency).filter(TaskDependency.event_id == event.id).all()
                    if tasks and event.start_datetime:
                        engine = ScheduleEngine()
                        sched_res = engine.schedule_tasks(event.start_datetime, tasks, deps)
                        graph = DependencyGraph.from_tasks_and_dependencies(tasks, deps)
                        cpc = CriticalPathCalculator()
                        cp_res = cpc.calculate(graph)

                        for t in tasks:
                            entry = sched_res.entries.get(t.id)
                            if entry:
                                t.planned_start = entry.planned_start
                                t.planned_end = entry.planned_end
                            timing = cp_res.task_timings.get(t.id)
                            if timing:
                                t.slack_minutes = timing.slack
                                t.is_critical_path = timing.is_critical
                        db.commit()
                except Exception as e:
                    print(f"Warning during plan generation: {e}")

    return inserted


def run_seeds(db: Optional[Session] = None) -> dict:
    """Runs all seed operations and returns summary counts."""
    session = db or SessionLocal()
    try:
        users_count = seed_users(session)
        venues_count = seed_venues(session)
        vendors_count = seed_vendors(session)
        events_count = seed_demo_events(session)
        return {
            "status": "success",
            "users_seeded": users_count,
            "venues_seeded": venues_count,
            "vendors_seeded": vendors_count,
            "events_seeded": events_count,
        }
    finally:
        if db is None:
            session.close()


if __name__ == "__main__":
    result = run_seeds()
    print("Seed execution result:", result)
