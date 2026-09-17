"""Health Endpoint Tests"""
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_health_returns_200(client: TestClient):
    """Test that GET /health returns HTTP 200 and indicates service status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "eventra-api"
    assert "environment" in data
    assert "version" in data


def test_health_db_connected(client: TestClient):
    """Test that GET /health/db returns HTTP 200 when database connectivity succeeds."""
    with patch("app.api.routes.health.check_db_connection", return_value=True):
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["engine"] == "postgresql"


def test_health_db_disconnected(client: TestClient):
    """Test that GET /health/db returns HTTP 503 when database is unreachable."""
    with patch("app.api.routes.health.check_db_connection", return_value=False):
        response = client.get("/health/db")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert "message" in data
