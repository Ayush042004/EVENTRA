"""HTTP/External Maps Provider Adapter.

Connects to third-party routing and geocoding services (e.g., OSRM, OpenRouteService, Google Maps).
Enforces configurable short timeouts and catches network errors safely.
"""
import time
from typing import Any, Dict, Optional
import httpx
from app.integrations.base import MapProvider, IntegrationResult, IntegrationSource
from app.integrations.maps.mock import MockMapsProvider


class HTTPMapsProvider(MapProvider):
    """Real HTTP Maps Provider with timeout protection and safe error handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://router.project-osrm.org",
        timeout_seconds: int = 5,
        fallback_to_mock: bool = True,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback_to_mock = fallback_to_mock
        self._mock = MockMapsProvider()

    def geocode(self, address: str) -> IntegrationResult[Dict[str, Any]]:
        # If no API key or external service configured, fall back safely
        if not self.api_key:
            if self.fallback_to_mock:
                return self._mock.geocode(address)
            return IntegrationResult(
                data=None,
                source=IntegrationSource.UNAVAILABLE,
                success=False,
                error="MAPS_API_KEY is not configured.",
            )

        start_time = time.time()
        try:
            # Example geocoding request with timeout
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.get(
                    f"{self.base_url}/geocode",
                    params={"q": address, "key": self.api_key},
                )
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    return IntegrationResult(
                        data=resp.json(),
                        source=IntegrationSource.REAL,
                        success=True,
                        latency_ms=latency,
                    )
                else:
                    return self._handle_failure(f"HTTP {resp.status_code}: {resp.text[:100]}", address, "geocode")
        except Exception as err:
            return self._handle_failure(str(err), address, "geocode")

    def get_distance(self, origin: Any, destination: Any) -> IntegrationResult[Dict[str, Any]]:
        if not self.api_key:
            if self.fallback_to_mock:
                return self._mock.get_distance(origin, destination)
            return IntegrationResult(
                data=None,
                source=IntegrationSource.UNAVAILABLE,
                success=False,
                error="MAPS_API_KEY is not configured.",
            )

        start_time = time.time()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.get(
                    f"{self.base_url}/route/v1/driving",
                    params={"origin": str(origin), "destination": str(destination), "key": self.api_key},
                )
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    return IntegrationResult(
                        data=data,
                        source=IntegrationSource.REAL,
                        success=True,
                        latency_ms=latency,
                    )
                else:
                    return self._handle_failure(f"HTTP {resp.status_code}", (origin, destination), "distance")
        except Exception as err:
            return self._handle_failure(str(err), (origin, destination), "distance")

    def get_route(self, origin: Any, destination: Any) -> IntegrationResult[Dict[str, Any]]:
        if not self.api_key:
            if self.fallback_to_mock:
                return self._mock.get_route(origin, destination)
            return IntegrationResult(
                data=None,
                source=IntegrationSource.UNAVAILABLE,
                success=False,
                error="MAPS_API_KEY is not configured.",
            )
        return self._mock.get_route(origin, destination)

    def _handle_failure(self, error_msg: str, payload: Any, op: str) -> IntegrationResult[Dict[str, Any]]:
        if self.fallback_to_mock:
            mock_res = self._mock.geocode(payload) if op == "geocode" else self._mock.get_distance(payload[0], payload[1])
            mock_res.error = f"Primary map service failed ({error_msg}); fell back to mock data."
            return mock_res
        return IntegrationResult(
            data=None,
            source=IntegrationSource.UNAVAILABLE,
            success=False,
            error=f"External maps service failed: {error_msg}",
        )
