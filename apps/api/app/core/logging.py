"""Structured Application Logging Setup"""
import logging
import sys
from app.core.config import settings


def setup_logging():
    """Configures application-wide logging with consistent format and level."""
    log_level = logging.DEBUG if settings.DEBUG or settings.ENVIRONMENT == "development" else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set third-party loggers to reasonable levels
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.DB_ECHO else logging.WARNING)


logger = logging.getLogger("eventra.api")
