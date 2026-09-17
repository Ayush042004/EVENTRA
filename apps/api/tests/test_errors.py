"""Error Handling Foundation Tests"""
from fastapi import status
from fastapi.testclient import TestClient
from app.main import app
from app.core.exceptions import AppException


def test_app_exception_returns_predictable_format():
    """Verify AppException triggers standardized JSON error response."""
    # Temporarily register a test route that raises AppException
    @app.get("/test-app-error")
    def trigger_app_error():
        raise AppException(
            message="Test custom exception",
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CUSTOM_TEST_CODE",
            details={"field": "test"},
        )

    with TestClient(app) as client:
        response = client.get("/test-app-error")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "CUSTOM_TEST_CODE"
        assert data["error"]["message"] == "Test custom exception"
        assert data["error"]["details"] == {"field": "test"}


def test_unhandled_exception_does_not_leak_stacktrace():
    """Verify unhandled 500 error returns safe generic message."""
    @app.get("/test-server-error")
    def trigger_server_error():
        raise RuntimeError("Internal crash secret db query trace")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-server-error")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "secret" not in data["error"]["message"]
