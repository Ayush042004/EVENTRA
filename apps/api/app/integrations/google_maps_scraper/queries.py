"""Deterministic query generation from event requirements and categories."""
from typing import List, Optional


# Controlled taxonomy to canonical Google Maps search queries mapping
CATEGORY_SEARCH_QUERIES = {
    "CATERING": ["catering", "caterer", "event catering", "wedding caterers"],
    "VENUE": ["event venue", "banquet hall", "convention center", "wedding lawn"],
    "DECOR": ["event decorator", "event decor", "stage decoration", "flower decorator"],
    "PHOTOGRAPHY": ["photographer", "photography", "photo studio", "event photographer"],
    "VIDEOGRAPHY": ["videography", "videographer", "video production", "cinematic wedding films"],
    "DJ_MUSIC": ["dj", "disc jockey", "event dj", "wedding dj"],
    "LIGHTING": ["stage lighting", "lighting rental", "event lighting", "ambient lighting"],
    "AV_TECH": ["audiovisual", "audio visual", "sound system rental", "av production"],
    "ENTERTAINMENT": ["live band performers", "event entertainment", "entertainers"],
    "TRANSPORT": ["event transport", "luxury transport", "bus and car rental"],
    "SECURITY": ["security services", "event security", "security guards", "bouncers"],
    "STAFFING": ["event staffing", "hospitality staffing", "banquet waitstaff"],
    "MAKEUP_STYLING": ["makeup artist", "bridal makeup", "event styling studio"],
    "PRINTING": ["event printing", "invitation printers", "backdrop printing"],
    "RENTALS": ["party rentals", "furniture rental", "tent rental", "event rentals"],
    "FLORIST": ["florist", "flower shop", "event florist", "fresh flowers"],
    "PRODUCTION": ["event production", "stage fabrication", "stage setup"],
    "CLEANING": ["event cleaning", "commercial cleaning", "sanitization services"],
    "OTHER": ["event services", "event supplies"],
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


def parse_discovery_query(text: str) -> dict:
    """Deterministically parses a natural language discovery query.

    Resolves:
    - category (EVENTRA controlled taxonomy)
    - radius_km (extracted distance in km)
    - anchor_mode ("NEAR_EVENT" | "NEAR_ME" | "REGION" | None)
    - location (extracted custom region/city name)
    - clean_query (cleaned keywords for business search)
    """
    import re

    if not text or not text.strip():
        return {
            "category": None,
            "radius_km": None,
            "anchor_mode": None,
            "location": None,
            "clean_query": "",
        }

    raw = text.strip()
    lowered = raw.lower()

    # 1. Radius Extraction
    radius_km = None
    # match e.g. "within 10 km", "within 5km", "10km radius"
    km_match = re.search(r"(?:within\s+)?(\d+(?:\.\d+)?)\s*(?:km|kilometres?|kilometers?)(?:\s+radius)?", lowered)
    if km_match:
        try:
            radius_km = float(km_match.group(1))
        except ValueError:
            pass
    else:
        # match miles e.g. "within 5 miles", "10 miles radius"
        mi_match = re.search(r"(?:within\s+)?(\d+(?:\.\d+)?)\s*(?:miles?|mi)(?:\s+radius)?", lowered)
        if mi_match:
            try:
                radius_km = round(float(mi_match.group(1)) * 1.60934, 1)
            except ValueError:
                pass

    # 2. Anchor Mode and Location Extraction
    anchor_mode = None
    location = None

    if re.search(r"\b(?:near\s+(?:the\s+)?venue|near\s+(?:the\s+)?event(?:\s+location)?)\b", lowered):
        anchor_mode = "NEAR_EVENT"
    elif re.search(r"\b(?:near\s+me|close\s+to\s+me|around\s+me)\b", lowered):
        anchor_mode = "NEAR_ME"
    else:
        # check "in <City>" or "near <City>"
        loc_match = re.search(r"\b(?:in|near|around)\s+([A-Za-z\s]+?)(?:\s+within|\s+radius|$)", raw)
        if loc_match:
            candidate = loc_match.group(1).strip()
            # Ignore if candidate is just "the venue", "me", "event"
            if candidate.lower() not in ("me", "venue", "the venue", "event", "the event", "here"):
                anchor_mode = "REGION"
                location = candidate

    # 3. Category Mapping
    category = None
    cat_patterns = [
        ("PHOTOGRAPHY", r"\b(?:photograph(?:er|ers|y)?|photo\s+studio|photoshoot)\b"),
        ("VIDEOGRAPHY", r"\b(?:videograph(?:er|ers|y)?|video\s+production|cinematograph(?:er|y)?)\b"),
        ("CATERING", r"\b(?:cater(?:er|ers|ing)?|food\s+service|buffet|banquet\s+food)\b"),
        ("DECOR", r"\b(?:decor(?:at(?:or|ors|ion|ions))?|stage\s+decor|flower\s+decorator)\b"),
        ("DJ_MUSIC", r"\b(?:dj|djs|disc\s+jockey|live\s+band|music\s+artists?)\b"),
        ("AV_TECH", r"\b(?:av|audio\s*visual|audiovisual|sound\s+system|projectors?|led\s+walls?|screens?)\b"),
        ("LIGHTING", r"\b(?:lighting|stage\s+lights?|ambient\s+light(?:ing)?|uplighting)\b"),
        ("SECURITY", r"\b(?:security|bouncers?|guards?|bodyguards?)\b"),
        ("FLORIST", r"\b(?:florist|florists|flowers?|fresh\s+flowers?)\b"),
        ("RENTALS", r"\b(?:rentals?|furniture\s+rentals?|tent\s+rentals?|canopy)\b"),
        ("STAFFING", r"\b(?:staffing|waitstaff|servers?|bartenders?|hospitality\s+staff)\b"),
        ("ENTERTAINMENT", r"\b(?:entertainment|performers?|artists?|magicians?)\b"),
        ("TRANSPORT", r"\b(?:transport(?:ation)?|limo(?:usine)?|bus\s+rental|car\s+rental)\b"),
        ("MAKEUP_STYLING", r"\b(?:makeup|styling|hairstyl(?:e|ist)|bridal\s+makeup)\b"),
        ("PRINTING", r"\b(?:printing|invitations?|flex|backdrop\s+print(?:ing)?)\b"),
        ("CLEANING", r"\b(?:cleaning|sanitiz(?:ation|ing)|waste\s+management)\b"),
        ("PRODUCTION", r"\b(?:production\s+company|stage\s+fabrication|stage\s+setup)\b"),
        ("VENUE", r"\b(?:venues?|banquet\s+halls?|convention\s+centers?|auditoriums?|ballrooms?)\b"),
    ]

    for cat_name, pat in cat_patterns:
        if re.search(pat, lowered):
            category = cat_name
            break

    # 4. Clean Query
    clean = lowered
    # Strip distance phrases
    clean = re.sub(r"(?:within\s+)?\d+(?:\.\d+)?\s*(?:km|kilometres?|kilometers?|miles?|mi)(?:\s+radius)?", "", clean)
    # Strip location phrases
    clean = re.sub(r"\b(?:near\s+(?:the\s+)?venue|near\s+(?:the\s+)?event(?:\s+location)?)\b", "", clean)
    clean = re.sub(r"\b(?:near\s+me|close\s+to\s+me|around\s+me)\b", "", clean)
    if location:
        clean = re.sub(rf"\b(?:in|near|around)\s+{re.escape(location.lower())}\b", "", clean)
    # Strip leading search words
    clean = re.sub(r"\b(?:find|search(?:\s+for)?|looking\s+for|show(?:\s+me)?|get)\b", "", clean)
    clean = " ".join(clean.split()).strip()

    # 5. Standalone Location & Prefix Resolution (e.g. "Delhi" or "Delhi photographers")
    if not anchor_mode:
        if not category:
            # Entire text is a location/city query with no category keywords (e.g. "Delhi", "Seattle, WA", "Mumbai")
            candidate = raw.strip()
            if candidate and len(candidate) >= 2:
                anchor_mode = "REGION"
                location = candidate
        else:
            # Category was identified, but see if a city prefix or suffix was left in the clean query (e.g. "Delhi photographers")
            # Strip the category keywords from clean to see what remains
            candidate_loc = clean
            for _, pat in cat_patterns:
                candidate_loc = re.sub(pat, "", candidate_loc).strip()
            candidate_loc = " ".join(candidate_loc.split()).strip()
            # If what's left is a substantial name and not a generic modifier
            if candidate_loc and len(candidate_loc) >= 3 and not re.search(r"\b(?:best|top|good|cheap|affordable|pro|local|companies|company|services|service)\b", candidate_loc):
                anchor_mode = "REGION"
                location = candidate_loc.title()

    return {
        "category": category,
        "radius_km": radius_km,
        "anchor_mode": anchor_mode,
        "location": location,
        "clean_query": clean,
    }

