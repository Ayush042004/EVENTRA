"""Deterministic query generation from event requirements and categories."""
from typing import List, Optional


# Controlled taxonomy to canonical Google Maps search queries mapping
CATEGORY_SEARCH_QUERIES = {
    "CATERING": ["wedding caterers", "event catering services", "food caterers"],
    "VENUE": ["event venues", "banquet halls", "wedding lawns"],
    "DECOR": ["wedding decorators", "event stage decoration", "flower decorator"],
    "PHOTOGRAPHY": ["wedding photographers", "event photography studio"],
    "VIDEOGRAPHY": ["event videography", "cinematic wedding films"],
    "DJ_MUSIC": ["event DJ sound", "wedding DJ artists"],
    "LIGHTING": ["event lighting rental", "stage and ambient lighting"],
    "AV_TECH": ["audiovisual equipment rental", "sound system rental", "AV production"],
    "ENTERTAINMENT": ["live band performers", "event entertainment artists"],
    "TRANSPORT": ["event luxury transport", "wedding bus and car rental"],
    "SECURITY": ["event bouncers and security services", "licensed event guards"],
    "STAFFING": ["event hospitality staffing", "banquet waitstaff"],
    "MAKEUP_STYLING": ["bridal makeup artist", "event styling studio"],
    "PRINTING": ["event invitation printers", "flex and backdrop printing"],
    "RENTALS": ["event furniture rentals", "tent and canopy rentals"],
    "FLORIST": ["event florist", "fresh flower suppliers"],
    "PRODUCTION": ["event production company", "stage setup fabrication"],
    "CLEANING": ["event post cleaning services", "commercial event sanitization"],
    "OTHER": ["event services and supplies"],
}


def build_discovery_query(
    category: Optional[str] = None,
    custom_query: Optional[str] = None,
    event_type: Optional[str] = None,
    location: Optional[str] = None,
) -> List[str]:
    """Generates 1 to 3 search keyword strings for Google Maps scraper."""
    if custom_query and custom_query.strip():
        q = custom_query.strip()
        if location and location.lower() not in q.lower():
            return [f"{q} in {location}", q]
        return [q]

    cat_key = (category or "OTHER").strip().upper()
    queries = CATEGORY_SEARCH_QUERIES.get(cat_key, [f"{cat_key.lower()} services"])

    # Prefix with event type if given (e.g. "wedding" or "corporate")
    ev_type = (event_type or "").strip().lower()
    if ev_type and ev_type not in ("other", "general"):
        adapted = []
        for q in queries:
            if ev_type not in q.lower():
                adapted.append(f"{ev_type} {q}")
            else:
                adapted.append(q)
        queries = adapted

    if location and location.strip():
        loc_str = location.strip()
        return [f"{q} in {loc_str}" for q in queries]

    return queries
