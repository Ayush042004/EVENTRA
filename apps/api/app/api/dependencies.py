"""API Dependency Foundation"""
from typing import Generator
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    """Exposes database session as an injectable dependency."""
    yield from get_db()


def get_current_user_id(x_user_id: str = Header(default="anonymous_operator")) -> str:
    """Extracts or stubs current authenticated operator identity."""
    return x_user_id
