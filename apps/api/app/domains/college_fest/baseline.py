"""Domain College Fest - Baseline Specification and Provider Categories"""
from typing import Dict, List, Any
from app.domains.base import BaseEventDomain


class CollegeFestDomain(BaseEventDomain):
    """Domain intelligence baseline for College Festival operations."""

    def baseline_requirements(self) -> List[Dict[str, Any]]:
        return [
            {"category": "venue", "name": "Open Ground / Auditorium", "mandatory": True},
            {"category": "sound", "name": "Concert Grade Audio System", "mandatory": True},
            {"category": "stage", "name": "Main Stage & Trussing", "mandatory": True},
            {"category": "security", "name": "Crowd Control & Guard Team", "mandatory": True},
            {"category": "power", "name": "Heavy Generator Backup", "mandatory": True},
        ]

    def baseline_tasks(self) -> List[Dict[str, Any]]:
        return [
            {"name": "Stage Construction", "phase": "SETUP"},
            {"name": "Sound & Light Rigging", "phase": "SETUP"},
            {"name": "Soundcheck", "phase": "PRE_EVENT"},
            {"name": "Security Briefing", "phase": "PRE_EVENT"},
        ]

    def baseline_dependencies(self) -> List[Dict[str, Any]]:
        return [
            {"predecessor": "Stage Construction", "successor": "Sound & Light Rigging"},
            {"predecessor": "Sound & Light Rigging", "successor": "Soundcheck"},
        ]

    def provider_categories(self) -> List[str]:
        return [
            "sound",
            "lighting",
            "stage",
            "security",
            "catering",
            "equipment",
            "power",
        ]
