"""Mock Maps Provider for deterministic testing and offline execution.

Clearly identifies all outputs as MOCK data.
"""
import hashlib
import math
from typing import Any, Dict, Tuple
from app.integrations.base import MapProvider, IntegrationResult, IntegrationSource


class MockMapsProvider(MapProvider):
    """Deterministic, offline map provider."""

    def geocode(self, address: str) -> IntegrationResult[Dict[str, Any]]:
        # Hash address deterministically to generate consistent plausible coordinates
        addr_clean = (address or "").strip()
        h = int(hashlib.md5(addr_clean.encode("utf-8")).hexdigest(), 16)
        lat = 37.7749 + ((h % 1000) / 10000.0) - 0.05
        lng = -122.4194 + (((h // 1000) % 1000) / 10000.0) - 0.05

        return IntegrationResult(
            data={
                "address": addr_clean,
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "formatted_address": f"{addr_clean} (Mock Geo)",
            },
            source=IntegrationSource.MOCK,
            success=True,
            latency_ms=1.5,
        )

    def get_distance(self, origin: Any, destination: Any) -> IntegrationResult[Dict[str, Any]]:
        # If coordinates provided, compute approximate distance
        coords = self._extract_coords(origin, destination)
        if coords:
            lat1, lon1, lat2, lon2 = coords
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist_km = round(max(1.0, 6371.0 * c), 1)
        else:
            # Deterministic default based on names
            dist_km = 15.0

        # Estimate duration assuming avg speed 40 km/h in city + 5 min buffer
        duration_mins = round((dist_km / 40.0) * 60 + 5, 1)

        return IntegrationResult(
            data={
                "origin": origin,
                "destination": destination,
                "distance_km": dist_km,
                "duration_minutes": duration_mins,
                "traffic_condition": "NORMAL",
            },
            source=IntegrationSource.MOCK,
            success=True,
            latency_ms=2.0,
        )

    def get_route(self, origin: Any, destination: Any) -> IntegrationResult[Dict[str, Any]]:
        dist_res = self.get_distance(origin, destination)
        dist_data = dist_res.data or {}
        return IntegrationResult(
            data={
                "distance_km": dist_data.get("distance_km", 15.0),
                "duration_minutes": dist_data.get("duration_minutes", 25.0),
                "route_summary": "Primary Arterial Corridor via Express Blvd (Mock Route)",
                "steps_count": 5,
            },
            source=IntegrationSource.MOCK,
            success=True,
            latency_ms=3.0,
        )

    def _extract_coords(self, origin: Any, destination: Any) -> Tuple[float, float, float, float] | None:
        try:
            if isinstance(origin, (list, tuple)) and isinstance(destination, (list, tuple)):
                return float(origin[0]), float(origin[1]), float(destination[0]), float(destination[1])
            if isinstance(origin, dict) and isinstance(destination, dict):
                return (
                    float(origin.get("lat") or origin.get("latitude")),
                    float(origin.get("lng") or origin.get("longitude")),
                    float(destination.get("lat") or destination.get("latitude")),
                    float(destination.get("lng") or destination.get("longitude")),
                )
        except Exception:
            return None
        return None
