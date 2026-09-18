"""Phase 8 recovery API integration: options only, no operational mutation."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import EventLifecycleState, EventState, TaskPriority, TaskStatus
from app.models.event import Event
from app.models.task import Task
from app.models.dependency import TaskDependency
from app.models.user import User
from app.models.vendor import Vendor


def _setup_recovery_case(client: TestClient, db: Session):
    user = User(name="Recovery Operator", email="recovery.operator@eventra.test")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    db.flush()
    event = Event(owner_id=user.id, name="College Fest", lifecycle_state=EventLifecycleState.LIVE.value,
                  state=EventState.NORMAL.value, start_datetime=now, end_datetime=now + timedelta(hours=6),
                  total_budget=Decimal("1000.00"))
    db.add(event)
    db.flush()
    setup = Task(event_id=event.id, name="Caterer Setup", status=TaskStatus.READY.value,
                 priority=TaskPriority.CRITICAL.value, required_provider_category="catering",
                 duration_minutes=30, slack_minutes=60, is_critical_path=False)
    ready = Task(event_id=event.id, name="Food Service Ready", status=TaskStatus.PENDING.value,
                 priority=TaskPriority.HIGH.value, required_provider_category="catering", duration_minutes=30)
    meal = Task(event_id=event.id, name="Guest Meal Service", status=TaskStatus.PENDING.value,
                priority=TaskPriority.HIGH.value, duration_minutes=30)
    primary = Vendor(name="Caterer A", category="catering", city="Mumbai", base_cost=200.0)
    backup = Vendor(name="Caterer B", category="catering", city="Mumbai", base_cost=250.0)
    db.add_all([setup, ready, meal, primary, backup])
    db.flush()
    db.add_all([
        TaskDependency(event_id=event.id, predecessor_task_id=setup.id, successor_task_id=ready.id),
        TaskDependency(event_id=event.id, predecessor_task_id=ready.id, successor_task_id=meal.id),
    ])
    db.commit()
    # Populate Phase 7's authoritative impact/risk fields through the real endpoint.
    response = client.post(f"/api/events/{event.id}/incidents", json={
        "incident_type": "VENDOR_NO_SHOW", "title": "Caterer A no-show",
        "related_task_id": setup.id, "related_vendor_id": primary.id,
        "evidence_metadata": {"delay_minutes": 45, "provider_eta_minutes": {backup.id: 15}},
    }, headers={"x-user-id": user.id})
    assert response.status_code == 201, response.text
    return user, event, setup, primary, backup, response.json()["id"]


def test_generate_recovery_options_is_read_only_and_ranks_feasible(test_client: TestClient, db_session: Session):
    user, event, setup, primary, backup, incident_id = _setup_recovery_case(test_client, db_session)
    before = (setup.status, setup.planned_start, setup.planned_end, event.state)
    response = test_client.post(
        f"/api/events/{event.id}/incidents/{incident_id}/recovery/options", headers={"x-user-id": user.id}
    )
    assert response.status_code == 201, response.text
    items = response.json()["items"]
    assert items
    assert any(item["strategy_type"] == "BACKUP" for item in items)
    feasible = [item for item in items if item["is_feasible"]]
    assert all(item["score"] is not None and item["rank"] is not None for item in feasible)
    db_session.refresh(setup)
    db_session.refresh(event)
    assert (setup.status, setup.planned_start, setup.planned_end, event.state) == before
    assert primary.status == "ACTIVE" and backup.status == "ACTIVE"


def test_recovery_options_are_detected_stale_after_live_state_changes(test_client: TestClient, db_session: Session):
    user, event, setup, _, _, incident_id = _setup_recovery_case(test_client, db_session)
    generate = test_client.post(f"/api/events/{event.id}/incidents/{incident_id}/recovery/options", headers={"x-user-id": user.id})
    assert generate.status_code == 201
    setup.status = TaskStatus.IN_PROGRESS.value
    db_session.commit()
    listed = test_client.get(f"/api/events/{event.id}/incidents/{incident_id}/recovery/options", headers={"x-user-id": user.id})
    assert listed.status_code == 200
    assert any(item["is_stale"] for item in listed.json()["items"])
    recalculated = test_client.post(f"/api/events/{event.id}/incidents/{incident_id}/recovery/recalculate", headers={"x-user-id": user.id})
    assert recalculated.status_code == 200
    assert any(not item["is_stale"] for item in recalculated.json()["items"])
