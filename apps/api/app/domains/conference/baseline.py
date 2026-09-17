"""Domain Conference - Baseline Specification and Provider Categories"""
from typing import Dict, List, Any
from app.domains.base import BaseEventDomain


class ConferenceDomain(BaseEventDomain):
    """Domain intelligence baseline for Conference operations."""

    def baseline_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"category": "venue", "name": "Convention Center / Auditorium", "mandatory": True},
            {"category": "av", "name": "Audio Visual & Projector Setup", "mandatory": True},
            {"category": "connectivity", "name": "High-Density Dedicated WiFi", "mandatory": True},
            {"category": "catering", "name": "Buffet Lunch & Coffee Breaks", "mandatory": True},
            {"category": "signage", "name": "Directional & Sponsor Signage", "mandatory": True},
        ]

    def baseline_tasks(self) -> List[Dict[str, Any]]:
        return [
            {"name": "AV Testing", "phase": "SETUP"},
            {"name": "WiFi Stress Test", "phase": "SETUP"},
            {"name": "Registration Desk Setup", "phase": "PRE_EVENT"},
        ]

    def baseline_dependencies(self) -> List[Dict[str, Any]]:
        return [
            {"predecessor": "AV Testing", "successor": "Registration Desk Setup"},
        ]

    def provider_categories(self) -> List[str]:
        return [
            "av",
            "catering",
            "stage",
            "lighting",
            "connectivity",
            "equipment",
            "signage",
        ]
