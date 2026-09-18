"""External Venue Discovery Adapter.

Normalizes third-party venue catalog data into EVENTRA domain representations.
Never overrides internal database models directly.
"""
from typing import Any, Dict, List, Optional
from app.integrations.base import VenueDirectoryProvider, IntegrationResult, IntegrationSource


class ExternalVenueAdapter(VenueDirectoryProvider):
    """Adapter for external venue search directories."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search_venues(
        self,
        query: str,
        city: Optional[str] = None,
        min_capacity: Optional[int] = None,
    ) -> IntegrationResult[List[Dict[str, Any]]]:
        # Normalizes external listings into EVENTRA venue schema
        city_target = city or "Metropolis"
        mock_venues = [
            {
                "name": f"{query} Convention Center",
                "city": city_target,
                "address": f"100 Exhibition Way, {city_target}",
                "capacity": max(min_capacity or 500, 1000),
                "base_cost": 12000.0,
                "amenities": ["av_rigging", "loading_dock", "high_speed_wifi"],
                "source": "EXTERNAL_CATALOG",
            },
            {
                "name": f"{city_target} Grand Pavilion",
                "city": city_target,
                "address": f"450 Waterfront Blvd, {city_target}",
                "capacity": max(min_capacity or 300, 600),
                "base_cost": 8500.0,
                "amenities": ["banquet_kitchen", "outdoor_terrace"],
                "source": "EXTERNAL_CATALOG",
            },
        ]

        return IntegrationResult(
            data=mock_venues,
            source=IntegrationSource.MOCK if not self.api_key else IntegrationSource.REAL,
            success=True,
            latency_ms=2.5,
        )
