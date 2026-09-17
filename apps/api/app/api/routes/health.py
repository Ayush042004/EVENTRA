"""Health Check Endpoints"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.db.session import check_db_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="API Process Health")
def get_health():
    """Returns basic process status confirming the API service is alive and listening."""
    return {
        "status": "healthy",
        "service": "eventra-api",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }


@router.get("/db", summary="PostgreSQL Connectivity Health")
def get_db_health():
    """Performs an authentic database ping.

    Returns HTTP 200 if PostgreSQL connection succeeds.
    Returns HTTP 503 if PostgreSQL is unreachable or failing.
    """
    is_connected = check_db_connection()

    if is_connected:
        return {
            "status": "healthy",
            "database": "connected",
            "engine": "postgresql",
        }

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "unhealthy",
            "database": "disconnected",
            "message": "Unable to establish connection to PostgreSQL.",
        },
    )
