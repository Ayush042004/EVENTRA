"""Integration tests for EventSpecification API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_wedding_demo_specification(client):
    response = client.get("/api/events/wedding_demo/specification")
    assert response.status_code == 200
    data = response.json()

    assert data["event_id"] == "wedding_demo"
    assert data["event_type"] == "WEDDING"
    assert data["guest_count"] == 150
    assert len(data["requirements"]) > 0
    assert len(data["tasks"]) > 0
    assert len(data["dependencies"]) > 0
    assert "CATERING" in data["provider_categories"]


def test_get_college_fest_demo_specification(client):
    response = client.get("/api/events/college_fest_demo/specification")
    assert response.status_code == 200
    data = response.json()

    assert data["event_id"] == "college_fest_demo"
    assert data["event_type"] == "COLLEGE_FEST"
    assert data["guest_count"] == 800
    assert "STAGE" in data["provider_categories"]


def test_get_conference_demo_specification(client):
    response = client.get("/api/events/conference_demo/specification")
    assert response.status_code == 200
    data = response.json()

    assert data["event_id"] == "conference_demo"
    assert data["event_type"] == "CONFERENCE"
    assert data["guest_count"] == 300
    assert "AV_LIGHTING" in data["provider_categories"]


def test_get_specification_not_found(client):
    response = client.get("/api/events/non_existent_event_12345/specification")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_preview_specification_endpoint_valid(client):
    payload = {
        "title": "Summer Tech Conference",
        "description": "Annual developer gathering",
        "event_type": "CONFERENCE",
        "start_time": "2026-07-20T08:00:00",
        "end_time": "2026-07-20T19:00:00",
        "guest_count": 450,
        "total_budget": 60000.0,
        "currency": "USD",
        "constraints": [
            {
                "constraint_type": "NOISE_CURFEW",
                "parameters": {"curfew": "22:00"},
            }
        ],
        "objectives": [
            {
                "title": "Keynote livestreams with zero packet drop",
                "priority": "CRITICAL",
            }
        ],
    }

    response = client.post("/api/events/specification/preview", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["title"] == "Summer Tech Conference"
    assert data["event_type"] == "CONFERENCE"
    assert data["guest_count"] == 450
    assert len(data["constraints"]) == 1
    assert data["constraints"][0]["constraint_type"] == "NOISE_CURFEW"
    assert len(data["objectives"]) == 1
    assert data["objectives"][0]["priority"] == "CRITICAL"


def test_preview_specification_invalid_event_type(client):
    payload = {
        "title": "E-Sports Championship",
        "event_type": "ESPORTS",
        "start_time": "2026-07-20T08:00:00",
        "end_time": "2026-07-20T19:00:00",
        "guest_count": 200,
    }

    response = client.post("/api/events/specification/preview", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported event type" in data["detail"]


def test_preview_specification_invalid_dates(client):
    payload = {
        "title": "Backward Time Conference",
        "event_type": "CONFERENCE",
        "start_time": "2026-07-20T19:00:00",
        "end_time": "2026-07-20T08:00:00",
        "guest_count": 200,
    }

    response = client.post("/api/events/specification/preview", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Logical date violation" in data["detail"]
