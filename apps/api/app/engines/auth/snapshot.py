"""Deterministic State Snapshot Generator for Optimistic Concurrency"""
import hashlib
import json
from typing import Optional
from sqlalchemy.orm import Session, selectinload

from app.models.event import Event
from app.models.incident import Incident
from app.models.task import Task
from app.models.dependency import TaskDependency
from app.models.resource import Resource
from app.models.vendor import Vendor
from app.models.vendor_assignment import VendorAssignment
from app.models.budget import BudgetItem
from app.models.objective import Objective
from app.models.constraint import Constraint


def compute_event_state_snapshot(db: Session, event_id: str, incident_id: Optional[str] = None) -> str:
    """Computes a deterministic SHA-256 state snapshot of an event and all operational sub-entities."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return ""

    incident = (
        db.query(Incident).filter(Incident.id == incident_id, Incident.event_id == event_id).first()
        if incident_id
        else db.query(Incident).filter(Incident.event_id == event_id).order_by(Incident.created_at.desc()).first()
    )

    tasks = db.query(Task).filter(Task.event_id == event_id).order_by(Task.id).all()
    dependencies = db.query(TaskDependency).filter(TaskDependency.event_id == event_id).order_by(TaskDependency.id).all()
    resources = db.query(Resource).filter(Resource.event_id == event_id).order_by(Resource.id).all()
    assignments = db.query(VendorAssignment).filter(VendorAssignment.event_id == event_id).order_by(VendorAssignment.id).all()
    providers = db.query(Vendor).options(selectinload(Vendor.availabilities)).order_by(Vendor.id).all()
    budget_items = db.query(BudgetItem).filter(BudgetItem.event_id == event_id).order_by(BudgetItem.id).all()
    objectives = db.query(Objective).filter(Objective.event_id == event_id).order_by(Objective.id).all()
    constraints = db.query(Constraint).filter(Constraint.event_id == event_id).order_by(Constraint.id).all()

    records = [
        event,
        *( [incident] if incident else [] ),
        *tasks,
        *dependencies,
        *resources,
        *assignments,
        *providers,
        *budget_items,
        *objectives,
        *constraints,
    ]
    availability_records = [avail for p in providers for avail in getattr(p, "availabilities", [])]

    payload = [
        (
            type(record).__name__,
            str(getattr(record, "id", "")),
            str(getattr(record, "updated_at", "")),
            str(getattr(record, "status", "")),
            str(getattr(record, "planned_start", "")),
            str(getattr(record, "planned_end", "")),
            str(getattr(record, "actual_end", "")),
        )
        for record in [*records, *availability_records]
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
