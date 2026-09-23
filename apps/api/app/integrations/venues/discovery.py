"""External Venue Discovery Adapter (Live Real-World Venue Discovery).

Connects to the open geospatial network (Komoot Photon + Nominatim) to discover
100% real physical event venues with exact coordinates and real addresses.
"""
import time
import logging
from typing import Any, Dict, List, Optional
from app.integrations.base import VenueDirectoryProvider, IntegrationResult, IntegrationSource
from app.services.geospatial_service import geospatial_discovery

logger = logging.getLogger(__name__)


class ExternalVenueAdapter(VenueDirectoryProvider):
    """Adapter for live real-world venue directory discovery using open geospatial networks."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.service = geospatial_discovery

    def search_venues(
        self,
        query: str,
        city: Optional[str] = None,
        min_capacity: Optional[int] = None,
        limit: int = 20,
    ) -> IntegrationResult[List[Dict[str, Any]]]:
        """Discovers real venues from the live map network."""
        start_time = time.time()
        city_target = city or "Seattle"

        try:
            real_venues = self.service.discover_real_venues(
                city=city_target,
                query=query,
                limit=limit,
            )

            if min_capacity is not None:
                real_venues = [v for v in real_venues if v.get("capacity", 0) >= min_capacity]

            for v in real_venues:
                v["source"] = "EXTERNAL_CATALOG"

            latency = round((time.time() - start_time) * 1000, 2)
            return IntegrationResult(
                data=real_venues,
                source=IntegrationSource.REAL,
                success=True,
                latency_ms=latency,
            )
        except Exception as exc:
            logger.warning(f"Live venue discovery failed: {exc}")
            latency = round((time.time() - start_time) * 1000, 2)
            return IntegrationResult(
                data=[],
                source=IntegrationSource.UNAVAILABLE,
                success=False,
                latency_ms=latency,
                error=f"Live venue discovery failed: {exc}",
            )


DiscoveryAdapter = ExternalVenueAdapter
