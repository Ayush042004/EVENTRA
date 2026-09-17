"""API dependency injection utilities."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db

def get_current_user_id() -> str:
    # Stub dependency for authentication
    return "demo-user-id"

def require_event_permission(permission: str):
    def dependency(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        return True
    return dependency
