"""Pytest configuration and test fixtures."""
import pytest
from typing import Generator

@pytest.fixture
def db_session() -> Generator:
    yield None
