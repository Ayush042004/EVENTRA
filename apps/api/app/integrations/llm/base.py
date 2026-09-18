"""LLM Integration Hub reusing Phase 11 LLMProvider architecture with Phase 12 configuration."""
from typing import Optional
from app.core.config import settings
from app.agent.provider import (
    LLMProvider,
    RealLLMProvider,
    MockLLMProvider,
)


def get_configured_llm_provider() -> LLMProvider:
    """Instantiates configured LLMProvider based on application settings.
    
    If LLM_PROVIDER == 'mock' or credentials missing, cleanly defaults to MockLLMProvider.
    """
    provider_type = (settings.LLM_PROVIDER or "mock").lower()
    if provider_type != "mock" and settings.LLM_API_KEY:
        return RealLLMProvider(
            api_key=settings.LLM_API_KEY,
            model_name=settings.LLM_MODEL or "gemini-1.5-pro",
        )
    return MockLLMProvider()


__all__ = [
    "LLMProvider",
    "RealLLMProvider",
    "MockLLMProvider",
    "get_configured_llm_provider",
]
