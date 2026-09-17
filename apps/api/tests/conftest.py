"""Pytest Configuration and Shared Test Fixtures"""
import os
import sys
from pathlib import Path
import pytest
from typing import Generator
from fastapi.testclient import TestClient

# Ensure apps/api is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Ensure test environment
os.environ["ENVIRONMENT"] = "test"

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture for making simulated HTTP calls to the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client
