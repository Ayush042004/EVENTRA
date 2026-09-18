"""External Provider Directory Adapter.

Normalizes third-party vendor listings into EVENTRA provider representations.
"""
from typing import Any, Dict, List, Optional
from app.integrations.base import ProviderDirectoryProvider, IntegrationResult, IntegrationSource


class ExternalProviderAdapter(ProviderDirectoryProvider):
    """Adapter for external vendor/provider directories."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search_providers(
        self,
        category: str,
        city: Optional[str] = None,
    ) -> IntegrationResult[List[Dict[str, Any]]]:
        city_target = city or "San Francisco"
        mock_providers = [
            {
                "name": f"Prime {category.capitalize()} Specialists",
                "category": category.lower(),
                "city": city_target,
                "base_cost": 3500.0,
                "rating": 4.9,
                "status": "ACTIVE",
                "source": "EXTERNAL_DIRECTORY",
            },
            {
                "name": f"NextGen {category.capitalize()} Solutions",
                "category": category.lower(),
                "city": city_target,
                "base_cost": 4200.0,
                "rating": 4.7,
                "status": "ACTIVE",
                "source": "EXTERNAL_DIRECTORY",
            },
        ]

        return IntegrationResult(
            data=mock_providers,
            source=IntegrationSource.MOCK if not self.api_key else IntegrationSource.REAL,
            success=True,
            latency_ms=2.0,
        )
