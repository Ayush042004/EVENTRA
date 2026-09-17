"""Configuration Tests"""
from app.core.config import Settings


def test_settings_defaults():
    """Verify default configuration attributes are properly loaded."""
    settings = Settings()
    assert settings.PROJECT_NAME == "EVENTRA API"
    assert settings.API_V1_STR == "/api"
    assert "postgresql" in settings.DATABASE_URL
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_cors_origins_parsing():
    """Verify CORS origins field validator converts strings correctly."""
    settings_wildcard = Settings(CORS_ORIGINS="*")
    assert settings_wildcard.CORS_ORIGINS == ["*"]

    settings_comma = Settings(CORS_ORIGINS="http://localhost:3000, http://example.com")
    assert settings_comma.CORS_ORIGINS == ["http://localhost:3000", "http://example.com"]
