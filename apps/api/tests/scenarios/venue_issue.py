"""Scenario test: Venue Issue."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.venue import Venue
from tests.scenarios.test_phase7_scenarios import _create_running_live_event


def test_venue_issue_scenario(test_client: TestClient, db_session: Session):
    """Scenario: Venue Issue disrupts live operations."""
    user, event = _create_running_live_event(test_client, db_session)

    venue = Venue(
        name="Convention Center Hall B",
        city="Chicago",
        capacity=500,
    )
    db_session.add(venue)
    db_session.commit()

    resp = test_client.post(
        f"/api/events/{event.id}/incidents",
        json={
            "incident_type": "VENUE_ISSUE",
            "severity": "CRITICAL",
            "title": "HVAC Failure in Main Ballroom",
            "related_venue_id": venue.id,
            "evidence_metadata": {"affected_area": "Ballroom", "temp_celsius": 38},
        },
        headers={"x-user-id": user.id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["incident_type"] == "VENUE_ISSUE"
    assert data["impact_result"] is not None
    assert data["risk_result"] is not None
