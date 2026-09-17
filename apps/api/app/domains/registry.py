"""Domain Registry for Event Specification and Provider Category Validation"""
from typing import Dict, List, Optional
from app.domains.base import BaseEventDomain
from app.domains.wedding.baseline import WeddingDomain
from app.domains.college_fest.baseline import CollegeFestDomain
from app.domains.conference.baseline import ConferenceDomain


_DOMAIN_INSTANCES: Dict[str, BaseEventDomain] = {
    "wedding": WeddingDomain(),
    "college_fest": CollegeFestDomain(),
    "conference": ConferenceDomain(),
}

# Aliases for flexible matching
_DOMAIN_ALIASES: Dict[str, str] = {
    "wedding": "wedding",
    "weddings": "wedding",
    "college_fest": "college_fest",
    "college-fest": "college_fest",
    "college fest": "college_fest",
    "fest": "college_fest",
    "conference": "conference",
    "conferences": "conference",
}


def normalize_domain_key(domain_name: str) -> Optional[str]:
    """Normalizes input string to canonical domain key."""
    cleaned = domain_name.strip().lower().replace("-", "_").replace(" ", "_")
    return _DOMAIN_ALIASES.get(cleaned, cleaned if cleaned in _DOMAIN_INSTANCES else None)


def get_domain(domain_name: str) -> Optional[BaseEventDomain]:
    """Retrieves domain instance for given event domain name."""
    canonical = normalize_domain_key(domain_name)
    if not canonical:
        return None
    return _DOMAIN_INSTANCES.get(canonical)


def list_supported_domains() -> List[str]:
    """Returns list of canonical supported domains."""
    return list(_DOMAIN_INSTANCES.keys())


def get_domain_provider_categories(domain_name: str) -> List[str]:
    """Returns list of recognized provider categories for domain."""
    domain = get_domain(domain_name)
    if not domain:
        return []
    return [c.lower() for c in domain.provider_categories()]


def is_provider_category_compatible(domain_name: str, category: str) -> bool:
    """Deterministically checks if a provider category is compatible with event domain requirements."""
    categories = get_domain_provider_categories(domain_name)
    return category.strip().lower() in categories
