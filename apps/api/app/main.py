"""EVENTRA FastAPI Application Entrypoint"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import register_exception_handlers
from app.api.routes.health import router as health_router
from app.api.routes.venues import router as venues_router
from app.api.routes.vendors import router as vendors_router

# Initialize application logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info(
        "EVENTRA API starting up in %s environment (host=%s, port=%d)",
        settings.ENVIRONMENT,
        settings.API_HOST,
        settings.API_PORT,
    )
    yield
    logger.info("EVENTRA API shutting down.")


# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Deterministic calculation engines and AI orchestration for live event operations.",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Global Exception Handlers
register_exception_handlers(app)

# Mount Health Routes
app.include_router(health_router)

# Mount Phase 3 Venue and Provider Network Routes
app.include_router(venues_router, prefix=settings.API_V1_STR)
app.include_router(vendors_router, prefix=settings.API_V1_STR)
