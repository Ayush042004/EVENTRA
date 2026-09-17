"""Domain Wedding - Baseline Specification and Provider Categories"""
from typing import Dict, List, Any
from app.domains.base import BaseEventDomain


class WeddingDomain(BaseEventDomain):
    """Domain intelligence baseline for Wedding operations."""

    def baseline_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"category": "venue", "name": "Ceremony & Reception Space", "mandatory": True},
            {"category": "catering", "name": "Dinner & Beverage Catering", "mandatory": True},
            {"category": "decoration", "name": "Stage & Table Decor", "mandatory": True},
            {"category": "photography", "name": "Full Day Photo & Video", "mandatory": True},
        ]

    def baseline_tasks(self) -> List[Dict[str, Any]]:
        return [
            {"name": "Venue Finalization", "phase": "PRE_EVENT"},
            {"name": "Catering Menu Tasting", "phase": "PRE_EVENT"},
            {"name": "Decor Setup", "phase": "DAY_OF"},
        ]

    def baseline_dependencies(self) -> List[Dict[str, Any]]:
        return [
            {"predecessor": "Venue Finalization", "successor": "Decor Setup"},
        ]

    def provider_categories(self) -> List[str]:
        return [
            "catering",
            "decoration",
            "photography",
            "videography",
            "music",
            "lighting",
            "transportation",
        ]
