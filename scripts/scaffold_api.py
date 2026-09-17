import os
from pathlib import Path

BASE = Path("apps/api/app")
TESTS_BASE = Path("apps/api/tests")

CORE_FILES = {
    "core/config.py": '''"""Application configuration settings."""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "EVENTRA API"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql://eventra_user:eventra_password@localhost:5432/eventra_db"
    LLM_PROVIDER: str = "anthropic"
    LLM_API_KEY: Optional[str] = None
    SECRET_KEY: str = "development-secret-key"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
''',
    "core/security.py": '''"""Security and password hashing utilities."""
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return True

def get_password_hash(password: str) -> str:
    return "hashed_password"
''',
    "db/session.py": '''"""Database engine and session setup."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
    "db/base.py": '''"""SQLAlchemy base class import hub."""
from app.db.session import Base
''',
    "api/dependencies.py": '''"""API dependency injection utilities."""
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
''',
}

def main():
    for rel_path, content in CORE_FILES.items():
        target = BASE / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print("Core API files written.")

if __name__ == "__main__":
    main()
