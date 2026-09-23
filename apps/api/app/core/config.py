"""Application Configuration Settings"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment or .env file."""

    PROJECT_NAME: str = "EVENTRA API"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api"

    # Server configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Database configuration (PostgreSQL)
    DATABASE_URL: str = "postgresql+psycopg://neondb_owner:npg_SXdJea6ZQmf2@ep-divine-mud-b5u94wxa.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 10
    DB_ECHO: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    # CORS configuration
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3002",
        ]

    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"

    # Phase 12: Real-World Integrations Configuration
    MAP_PROVIDER: str = "mock"  # "mock", "osrm", "openrouteservice", "google"
    MAPS_API_KEY: Union[str, None] = None
    MAPS_TIMEOUT_SECONDS: int = 5

    NOTIFICATION_PROVIDER: str = "in_app"  # "in_app", "webhook", "mock"
    NOTIFICATION_WEBHOOK_URL: Union[str, None] = None

    COMMUNICATION_PROVIDER: str = "mock"  # "mock", "whatsapp"
    WHATSAPP_ENABLED: bool = False
    WHATSAPP_API_TOKEN: Union[str, None] = None
    WHATSAPP_PHONE_NUMBER_ID: Union[str, None] = None
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: Union[str, None] = None

    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    LLM_MODEL: str = "gemini-1.5-pro"
    LLM_API_KEY: Union[str, None] = None
    LLM_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
