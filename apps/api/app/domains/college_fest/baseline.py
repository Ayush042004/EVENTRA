"""College Fest domain baseline requirements and provider categories."""
from typing import List
from app.domains.types import RequirementDefinition

COLLEGE_FEST_REQUIREMENTS: List[RequirementDefinition] = [
    RequirementDefinition(
        key="college_fest.venue",
        category="VENUE",
        name="Festival Grounds / Arena",
        description="Large open or indoor arena accommodating high-density crowd flow",
        is_mandatory=True,
        parameters={"open_air": True, "crowd_capacity": 1000},
    ),
    RequirementDefinition(
        key="college_fest.stage",
        category="EQUIPMENT",
        name="Performance Stages",
        description="Heavy structural staging with roof canopy and risers for live performers",
        is_mandatory=True,
        parameters={"stage_dimensions": "40x30ft"},
    ),
    RequirementDefinition(
        key="college_fest.power",
        category="EQUIPMENT",
        name="Industrial Power & Generators",
        description="Dual high-capacity silent diesel generators with auto-switchover",
        is_mandatory=True,
        parameters={"kva_capacity": 250, "redundant_backup": True},
    ),
    RequirementDefinition(
        key="college_fest.sound",
        category="EQUIPMENT",
        name="Concert Sound Reinforcement",
        description="High-output line-array speakers, subwoofers, and digital mixing console",
        is_mandatory=True,
        parameters={"spl_db_rating": 110},
    ),
    RequirementDefinition(
        key="college_fest.lighting",
        category="EQUIPMENT",
        name="Intelligent Concert Lighting",
        description="DMX moving heads, strobes, hazers, and stage wash lighting",
        is_mandatory=True,
        parameters={"dmx_controlled": True},
    ),
    RequirementDefinition(
        key="college_fest.security",
        category="STAFFING",
        name="Campus Security & Crowd Control",
        description="Mojo/mojo-type crowd barriers, security guards, and emergency medical station",
        is_mandatory=True,
        parameters={"guard_count": 20, "ambulance_on_site": True},
    ),
    RequirementDefinition(
        key="college_fest.registration",
        category="GENERAL",
        name="Registration & Gate Entry Hub",
        description="Multi-lane turnstiles / queue lanes for digital ticket and student ID scans",
        is_mandatory=True,
        parameters={"entry_lanes": 4},
    ),
    RequirementDefinition(
        key="college_fest.catering",
        category="CATERING",
        name="Festival Food & Refreshments",
        description="Food stall zones, crew catering, and green room artist hospitality",
        is_mandatory=True,
        parameters={"food_stall_count": 8},
    ),
    RequirementDefinition(
        key="college_fest.equipment",
        category="EQUIPMENT",
        name="Staging Truss & Rigging",
        description="Certified overhead aluminium box truss, motors, and safety cables",
        is_mandatory=True,
        parameters={"certified_rigging": True},
    ),
    RequirementDefinition(
        key="college_fest.decoration",
        category="GENERAL",
        name="Festival Theming & Signage",
        description="Campus entrance arch, festival branding banners, and directional signs",
        is_mandatory=False,
        parameters={"vinyl_banners": True},
    ),
]

COLLEGE_FEST_PROVIDER_CATEGORIES: List[str] = [
    "sound",
    "lighting",
    "stage",
    "security",
    "catering",
    "equipment",
    "power",
    "decoration",
    "venue",
    "logistics",
]
