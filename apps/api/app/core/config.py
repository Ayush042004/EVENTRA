"""Application configuration settings."""
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
