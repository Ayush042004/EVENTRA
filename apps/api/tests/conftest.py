"""Pytest configuration and test fixtures."""
import sys
from pathlib import Path
from typing import Generator
import pytest

# Ensure app module is in sys.path when running pytest from any directory
API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture
def db_session() -> Generator:
    yield None
