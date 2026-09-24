"""Domain Service: IntakeService

Handles conversational event intake, natural language intent extraction,
missing information detection, deterministic plan generation, and conversational plan edits.
"""
from datetime import datetime, timezone, timedelta
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.requirement import Requirement
from app.models.constraint import Constraint
from app.models.objective import Objective
from app.models.enums import EventType, EventState, EventLifecycleState, ProviderCategory
from app.services.specification_service import SpecificationService
from app.services.planning_service import PlanningService
from app.schemas.planning import EventPlan
from app.observability.audit import AuditRecorder


# Taxonomy mapping of common words to ProviderCategory enum values
CATEGORY_KEYWORDS: Dict[str, str] = {
    "venue": "VENUE",
    "hall": "VENUE",
    "location": "VENUE",
    "auditorium": "VENUE",
    "ground": "VENUE",
    "convention": "VENUE",
    "resort": "VENUE",
    "hotel": "VENUE",
    "cater": "CATERING",
    "catering": "CATERING",
    "food": "CATERING",
    "meal": "CATERING",
    "lunch": "CATERING",
    "dinner": "CATERING",
    "breakfast": "CATERING",
    "snack": "CATERING",
    "buffet": "CATERING",
    "av": "AV_TECH",
    "audio": "AV_TECH",
    "sound": "AV_TECH",
    "speaker": "AV_TECH",
    "mic": "AV_TECH",
    "microphone": "AV_TECH",
    "screen": "AV_TECH",
    "screens": "AV_TECH",
    "projector": "AV_TECH",
    "live stream": "AV_TECH",
    "live streaming": "AV_TECH",
    "streaming": "AV_TECH",
    "stream": "AV_TECH",
    "photo": "PHOTOGRAPHY",
    "photography": "PHOTOGRAPHY",
    "photographer": "PHOTOGRAPHY",
    "video": "VIDEOGRAPHY",
    "videography": "VIDEOGRAPHY",
    "videographer": "VIDEOGRAPHY",
    "decor": "DECOR",
    "decoration": "DECOR",
    "stage": "DECOR",
    "florist": "FLORIST",
    "flower": "FLORIST",
    "transport": "TRANSPORT",
    "transportation": "TRANSPORT",
    "cab": "TRANSPORT",
    "cabs": "TRANSPORT",
    "bus": "TRANSPORT",
    "buses": "TRANSPORT",
    "shuttle": "TRANSPORT",
    "security": "SECURITY",
    "guard": "SECURITY",
    "guards": "SECURITY",
    "bouncers": "SECURITY",
    "bouncer": "SECURITY",
    "staff": "STAFFING",
    "staffing": "STAFFING",
    "host": "STAFFING",
    "volunteer": "STAFFING",
    "dj": "DJ_MUSIC",
    "music": "DJ_MUSIC",
    "band": "DJ_MUSIC",
    "light": "LIGHTING",
    "lighting": "LIGHTING",
    "print": "PRINTING",
    "printing": "PRINTING",
    "badge": "PRINTING",
    "badges": "PRINTING",
    "banner": "PRINTING",
    "banners": "PRINTING",
    "clean": "CLEANING",
    "cleaning": "CLEANING",
}

# Number words mapping for robust NL extraction
NUMBER_WORDS: Dict[str, float] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100,
}


def parse_indian_number_words(text: str) -> Optional[float]:
    """Parses phrases like 'one crore twenty lakh', 'eight lakh', 'ten lakh', '1.2 crore'."""
    text_lower = text.lower()
    total = 0.0
    matched = False

    # Check crore with words: e.g. "one crore", "two crore", "1.2 crore"
    cr_words_match = re.search(r"(\b[a-z]+\b|\d+(?:\.\d+)?)\s*(?:crore|crores|cr)\b", text_lower)
    if cr_words_match:
        val_str = cr_words_match.group(1)
        if val_str in NUMBER_WORDS:
            total += NUMBER_WORDS[val_str] * 10000000.0
            matched = True
        else:
            try:
                total += float(val_str) * 10000000.0
                matched = True
            except ValueError:
                pass

    # Check lakh with words: e.g. "twenty lakh", "eight lakh", "10 lakh", "8.5 lakhs"
    lakh_words_match = re.search(r"(\b[a-z]+(?:\s+[a-z]+)?\b|\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|l)\b", text_lower)
    if lakh_words_match:
        val_str = lakh_words_match.group(1).strip()
        # Parse compound words like "twenty" or "twenty five"
        words = val_str.split()
        subtotal = 0.0
        word_found = False
        for w in words:
            if w in NUMBER_WORDS:
                subtotal += NUMBER_WORDS[w]
                word_found = True
        if word_found:
            total += subtotal * 100000.0
            matched = True
        else:
            try:
                total += float(val_str) * 100000.0
                matched = True
            except ValueError:
                pass

    return total if matched else None


class IntakeService:
    """Coordinates conversational event intake, intent understanding, and plan refinement."""

    def __init__(self, db: Session):
        self.db = db
        self._spec_service = SpecificationService(db)
        self._planning_service = PlanningService(db)
        self._audit = AuditRecorder(db)

    def extract_intent(self, text: str) -> Dict[str, Any]:
        """Extracts structured event intent from natural language input.
        
        Deterministic regex/keyword extraction with support for Indian (Lakh/Crore)
        and Western (K/M) budget notations, attendee counts, cities, and dates.
        """
        text_lower = text.lower()

        # 1. Event Type
        event_type = None
        if any(k in text_lower for k in ["wedding", "marriage", "shaadi", "reception", "anniversary"]):
            event_type = EventType.WEDDING.value
        elif any(k in text_lower for k in ["hackathon", "fest", "college fest", "cultural", "campus"]):
            event_type = EventType.COLLEGE_FEST.value
        elif any(k in text_lower for k in ["conference", "summit", "keynote", "symposium", "corporate", "offsite", "meetup", "tech", "annual meet", "seminar"]):
            event_type = EventType.CONFERENCE.value

        # 2. Location / City
        city = None
        known_cities = [
            "delhi", "new delhi", "gurgaon", "gurugram", "noida", "greater noida",
            "mumbai", "bangalore", "bengaluru", "hyderabad", "pune", "chennai",
            "kolkata", "jaipur", "goa", "chandigarh", "ahmedabad", "faridabad",
            "san francisco", "seattle", "boston", "austin", "new york", "london", "singapore"
        ]
        for c in known_cities:
            if re.search(rf"\b{re.escape(c)}\b", text_lower):
                city = "Gurgaon" if c in ("gurgaon", "gurugram") else ("Delhi" if c in ("delhi", "new delhi") else c.title())
                break

        # 3. Guest Count / Attendance
        guest_count = None
        pax_match = re.search(r"(\d+)\s*[-]?\s*(?:person|people|attendee|attendees|guest|guests|pax|members)", text_lower)
        if pax_match:
            guest_count = int(pax_match.group(1))
        else:
            # Check standalone numbers, ensuring it is not a date (e.g. 15 Nov, 2026), time, or unit
            months_pattern = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)"
            units_pattern = r"(?:lakh|lakhs|l|k|cr|crore|usd|inr|rs|rupees|percent|%|hours|hr|pm|am)"
            for m in re.finditer(r"\b(\d{2,4})\b", text):
                val = int(m.group(1))
                if 2020 <= val <= 2035:
                    continue
                post_text = text_lower[m.end():m.end()+25]
                pre_text = text_lower[max(0, m.start()-15):m.start()]
                if re.search(rf"^\s*(?:st|nd|rd|th)?\s*{months_pattern}\b", post_text):
                    continue
                if re.search(rf"\b{months_pattern}\s*$", pre_text):
                    continue
                if re.search(rf"^\s*{units_pattern}\b", post_text):
                    continue
                if val >= 20:
                    guest_count = val
                    break

        # 4. Budget Extraction
        total_budget = None
        currency = "INR" if any(k in text_lower for k in ["lakh", "lakhs", "lac", "lacs", "crore", "cr", "₹", "inr", "rs", "rupee", "rupees"]) else "USD"

        # Try Indian number words first (e.g. "one crore twenty lakh", "1.2 crore", "8 lakh", "₹8L")
        word_budget = parse_indian_number_words(text_lower)
        if word_budget and word_budget > 0:
            total_budget = word_budget
            currency = "INR"

        if total_budget is None:
            # Check Western K notation: e.g. "$50k", "50 thousand"
            k_match = re.search(r"(?:\$|usd)?\s*(\d+(?:\.\d+)?)\s*(?:k|thousand)\b", text_lower)
            if k_match:
                total_budget = float(k_match.group(1)) * 1000.0

        if total_budget is None:
            raw_budget = re.search(r"(?:budget|around|of|cost)\s*(?:is|of|around)?\s*(?:rs\.?|inr|₹|\$|usd)?\s*([\d,]+(?:\.\d+)?)", text_lower)
            if raw_budget:
                cleaned = raw_budget.group(1).replace(",", "")
                try:
                    val = float(cleaned)
                    if val > 100:  # avoid picking up small counts as budget
                        total_budget = val
                except ValueError:
                    pass

        # 5. Requirements Extraction
        requirements: List[str] = []
        for kw, cat in CATEGORY_KEYWORDS.items():
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                if cat not in requirements:
                    requirements.append(cat)

        # 6. Date / Duration Extraction
        start_time = None
        end_time = None
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if "tomorrow" in text_lower:
            start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=8)
        elif "next week" in text_lower:
            start_time = (now + timedelta(days=7)).replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=8)
        else:
            date_match = re.search(
                r"(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*(\d{4})?",
                text_lower,
            )
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2)[:3]
                year = int(date_match.group(3)) if date_match.group(3) else (now.year if now.month < 11 else now.year + 1)
                months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                month = months.index(month_str) + 1
                try:
                    start_time = datetime(year, month, day, 9, 0, 0)
                    end_time = start_time + timedelta(hours=8)
                except ValueError:
                    pass

        # 7. Generate Descriptive Event Name if possible
        effective_type = event_type or EventType.CONFERENCE.value
        type_title = effective_type.replace("_", " ").title()
        city_title = city or "Metro"
        pax_str = f"{guest_count}-Person " if guest_count else ""
        name = f"{pax_str}{city_title} {type_title} 2026"

        return {
            "name": name,
            "event_type": event_type,
            "location": city,
            "city": city,
            "guest_count": guest_count,
            "total_budget": total_budget,
            "currency": currency,
            "requirements": requirements,
            "start_time": start_time,
            "end_time": end_time,
            "has_date": start_time is not None,
            "has_location": city is not None,
            "has_guest_count": guest_count is not None,
            "has_budget": total_budget is not None,
            "has_event_type": event_type is not None,
        }

    def detect_missing_info(self, intent: Dict[str, Any]) -> List[str]:
        """Determines which mandatory pieces of information are missing before planning."""
        missing = []
        if not intent.get("has_date"):
            missing.append("Event date (e.g. 15 November 2026)")
        if not intent.get("has_location") or not intent.get("location"):
            missing.append("Target city or venue location (e.g. Delhi, Mumbai, Bangalore)")
        if not intent.get("has_guest_count") or not intent.get("guest_count"):
            missing.append("Expected guest/attendee count (e.g. 500 attendees)")
        if not intent.get("has_budget") or not intent.get("total_budget"):
            missing.append("Approximate budget (e.g. 8 lakh or 10 lakh)")
        return missing

    def format_missing_info_response(self, intent: Dict[str, Any], missing: List[str]) -> str:
        """Formats a natural, concise conversational reply acknowledging captured data and asking for missing info."""
        reqs_str = ", ".join(r.replace("_", " ").title() for r in intent.get("requirements", [])) or "Standard operational categories"
        currency_sym = "₹" if intent.get("currency") == "INR" else "$"
        budget_str = f"{currency_sym}{intent.get('total_budget', 0):,.0f}" if intent.get("total_budget") else "Not specified"
        guest_str = f"{intent.get('guest_count')} attendees" if intent.get("guest_count") else "Not specified"
        loc_str = intent.get("location") or "Not specified"
        type_str = (intent.get("event_type") or "Conference").title()
        
        lines = [
            f"Understood! Here is what I have captured so far for your {type_str}:",
            f"• Location: {loc_str}",
            f"• Attendees: {guest_str}",
            f"• Budget: {budget_str}",
            f"• Sourcing Requirements: {reqs_str}",
            "",
            "To generate your authoritative operational plan, please provide:",
        ]
        for i, m in enumerate(missing, 1):
            lines.append(f"{i}. {m}")
        
        return "\n".join(lines)

    def process_intake(
        self,
        message: str,
        event_id: Optional[str] = None,
        user_id: str = "anonymous_operator",
        force_plan: bool = False,
    ) -> Dict[str, Any]:
        """Main entry point for natural language event intake with multi-turn context preservation."""
        turn_intent = self.extract_intent(message)

        # 1. Load existing event context if event_id is supplied
        event: Optional[Event] = None
        if event_id:
            event = self.db.query(Event).filter(Event.id == event_id).first()

        # 2. Merge existing event state with newly extracted intent
        merged_intent = dict(turn_intent)
        if event:
            if not merged_intent["has_event_type"] and event.event_type:
                merged_intent["event_type"] = event.event_type
                merged_intent["has_event_type"] = True
            if not merged_intent["has_location"] and event.location:
                merged_intent["location"] = event.location
                merged_intent["has_location"] = True
            if not merged_intent["has_guest_count"] and event.guest_count:
                merged_intent["guest_count"] = event.guest_count
                merged_intent["has_guest_count"] = True
            if not merged_intent["has_budget"] and event.total_budget:
                merged_intent["total_budget"] = float(event.total_budget)
                merged_intent["has_budget"] = True
            if not merged_intent["has_date"] and event.start_datetime:
                merged_intent["start_time"] = event.start_datetime
                merged_intent["end_time"] = event.end_datetime
                merged_intent["has_date"] = True

            # Merge requirements
            existing_reqs = self.db.query(Requirement).filter(Requirement.event_id == event.id).all()
            existing_types = [r.type for r in existing_reqs]
            if existing_types and not merged_intent["requirements"]:
                merged_intent["requirements"] = existing_types
            else:
                combined = list(set(existing_types + merged_intent["requirements"]))
                if combined:
                    merged_intent["requirements"] = combined

        # Ensure default event type is CONFERENCE if unspecified
        if not merged_intent.get("event_type"):
            merged_intent["event_type"] = EventType.CONFERENCE.value
            merged_intent["has_event_type"] = True

        # Default requirements based on event type if still empty
        if not merged_intent["requirements"]:
            if merged_intent["event_type"] == EventType.CONFERENCE.value:
                merged_intent["requirements"] = ["VENUE", "CATERING", "AV_TECH", "PHOTOGRAPHY", "TRANSPORT"]
            elif merged_intent["event_type"] == EventType.WEDDING.value:
                merged_intent["requirements"] = ["VENUE", "CATERING", "DECOR", "PHOTOGRAPHY", "DJ_MUSIC"]
            elif merged_intent["event_type"] == EventType.COLLEGE_FEST.value:
                merged_intent["requirements"] = ["VENUE", "AV_TECH", "DJ_MUSIC", "SECURITY", "CATERING"]
            else:
                merged_intent["requirements"] = ["VENUE", "CATERING", "AV_TECH"]

        # Check missing information
        missing = self.detect_missing_info(merged_intent)

        # 3. If critical info is missing and not forced, persist DRAFT event and prompt user
        if missing and not force_plan:
            # Persist or update draft event so subsequent turns preserve context
            if not event:
                event = Event(
                    owner_id=user_id,
                    name=merged_intent["name"],
                    description=f"Draft conversational intake from: '{message[:200]}'",
                    event_type=merged_intent["event_type"],
                    location=merged_intent.get("location") or "Pending Location",
                    start_datetime=merged_intent.get("start_time"),
                    end_datetime=merged_intent.get("end_time"),
                    guest_count=merged_intent.get("guest_count") or 100,
                    total_budget=merged_intent.get("total_budget") or 500000.0,
                    currency=merged_intent["currency"],
                    state=EventState.NORMAL.value,
                    lifecycle_state=EventLifecycleState.DRAFT.value,
                )
                self.db.add(event)
                self.db.commit()
                self.db.refresh(event)
            else:
                if merged_intent.get("location"):
                    event.location = merged_intent["location"]
                if merged_intent.get("guest_count"):
                    event.guest_count = merged_intent["guest_count"]
                if merged_intent.get("total_budget"):
                    event.total_budget = merged_intent["total_budget"]
                if merged_intent.get("start_time"):
                    event.start_datetime = merged_intent["start_time"]
                    event.end_datetime = merged_intent["end_time"]
                self.db.commit()
                self.db.refresh(event)

            # Persist any requirements captured so far
            if merged_intent["requirements"]:
                self.db.query(Requirement).filter(Requirement.event_id == event.id).delete()
                for cat in merged_intent["requirements"]:
                    req = Requirement(
                        event_id=event.id,
                        name=f"{cat.replace('_', ' ').title()} Sourcing",
                        type=cat,
                        required=True,
                        description=f"Operational requirement for {cat.replace('_', ' ').title()}",
                        value={"category": cat, "auto_source": True},
                    )
                    self.db.add(req)
                self.db.commit()

            return {
                "status": "MISSING_INFO",
                "message": self.format_missing_info_response(merged_intent, missing),
                "intent": merged_intent,
                "missing_fields": missing,
                "event_id": event.id,
                "event": {
                    "id": event.id,
                    "name": event.name,
                    "event_type": event.event_type,
                    "location": event.location,
                    "start_time": event.start_datetime.isoformat() if event.start_datetime else None,
                    "end_time": event.end_datetime.isoformat() if event.end_datetime else None,
                    "guest_count": event.guest_count,
                    "total_budget": float(event.total_budget or 0),
                    "currency": event.currency,
                    "lifecycle_state": event.lifecycle_state,
                    "requirements": merged_intent["requirements"],
                },
                "plan": None,
            }

        # 4. All critical info is present (or forced): Generate authoritative Event Specification
        if not merged_intent.get("start_time"):
            default_start = (datetime.now(timezone.utc) + timedelta(days=30)).replace(
                hour=9, minute=0, second=0, microsecond=0, tzinfo=None
            )
            merged_intent["start_time"] = default_start
            merged_intent["end_time"] = default_start + timedelta(hours=9)

        if not event:
            event = Event(
                owner_id=user_id,
                name=merged_intent["name"],
                description=f"Authoritative event generated from organizer request: '{message[:200]}'",
                event_type=merged_intent["event_type"],
                location=merged_intent["location"] or "Delhi",
                start_datetime=merged_intent["start_time"],
                end_datetime=merged_intent["end_time"],
                guest_count=merged_intent["guest_count"] or 100,
                total_budget=merged_intent["total_budget"] or 500000.0,
                currency=merged_intent["currency"],
                state=EventState.NORMAL.value,
                lifecycle_state=EventLifecycleState.DRAFT.value,
            )
            self.db.add(event)
            self.db.flush()
        else:
            event.name = merged_intent["name"]
            event.event_type = merged_intent["event_type"]
            event.location = merged_intent["location"] or event.location
            event.start_datetime = merged_intent["start_time"]
            event.end_datetime = merged_intent["end_time"]
            event.guest_count = merged_intent["guest_count"] or event.guest_count
            event.total_budget = merged_intent["total_budget"] or event.total_budget
            event.currency = merged_intent["currency"]

        # Persist authoritative requirements
        self.db.query(Requirement).filter(Requirement.event_id == event.id).delete()
        for cat in merged_intent["requirements"]:
            req = Requirement(
                event_id=event.id,
                name=f"{cat.replace('_', ' ').title()} Sourcing",
                type=cat,
                required=True,
                description=f"Operational requirement for {cat.replace('_', ' ').title()}",
                value={"category": cat, "auto_source": True},
            )
            self.db.add(req)

        event.lifecycle_state = EventLifecycleState.DRAFT.value
        self.db.commit()
        self.db.refresh(event)

        # 5. Generate Authoritative Plan via PlanningService
        plan = self._planning_service.generate_plan(event.id)

        self._audit.record(
            event_id=event.id,
            actor_id=user_id,
            actor_type="USER",
            action="OPERATIONAL_PLAN_GENERATED",
            action_type="PLANNING",
            target_type="EVENT",
            target_id=event.id,
            after_state={
                "event_name": event.name,
                "total_tasks": plan.summary.total_tasks,
                "total_budget": float(event.total_budget),
                "requirements": merged_intent["requirements"],
            },
        )

        currency_sym = "₹" if event.currency == "INR" else "$"
        date_str = event.start_datetime.strftime("%d %B %Y") if event.start_datetime else "TBD"
        resp_msg = (
            f"I have built the complete operational plan for **{event.name}** in {event.location} on {date_str}.\n\n"
            f"**Plan Overview:**\n"
            f"• **Budget Allocation:** {currency_sym}{plan.summary.total_estimated_budget:,.0f} / {currency_sym}{float(event.total_budget):,.0f}\n"
            f"• **Tasks & Milestones:** {plan.summary.total_tasks} executable tasks ({plan.summary.critical_path_tasks} on critical path)\n"
            f"• **Dependencies:** {plan.summary.total_dependencies} dependency relationships tracked\n"
            f"• **Required Resources:** {plan.summary.total_resources} resources mapped\n"
            f"• **Sourcing Slices:** {', '.join(r.replace('_', ' ').title() for r in merged_intent['requirements'])}\n\n"
            f"You can review or modify requirements below, or say **'Start Operations'** to begin autonomous execution."
        )

        return {
            "status": "PLAN_READY",
            "message": resp_msg,
            "intent": merged_intent,
            "event_id": event.id,
            "event": {
                "id": event.id,
                "name": event.name,
                "event_type": event.event_type,
                "location": event.location,
                "start_time": event.start_datetime.isoformat() if event.start_datetime else None,
                "end_time": event.end_datetime.isoformat() if event.end_datetime else None,
                "guest_count": event.guest_count,
                "total_budget": float(event.total_budget or 0),
                "currency": event.currency,
                "lifecycle_state": event.lifecycle_state,
                "requirements": merged_intent["requirements"],
            },
            "plan": plan.model_dump(),
        }

    def modify_plan(
        self,
        event_id: str,
        modification_text: str,
        user_id: str = "anonymous_operator",
    ) -> Dict[str, Any]:
        """Modifies the event specification and regenerates the operational plan.
        
        Handles:
        - Budget updates: 'Increase budget to 12 lakh', 'Increase the budget to 10 lakh', 'budget 15 lakh'
        - Attendance updates: 'Change attendance to 800', '800 attendees'
        - Location shifts: 'Move the event to Gurgaon', 'Change location to Gurgaon'
        - Date shifts: 'Change event date to 20 December 2026'
        - Requirement additions: 'Add security', 'Add live streaming'
        - Requirement removals: 'Remove photography', 'Remove transportation'
        """
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event '{event_id}' not found.")

        mod_lower = modification_text.lower()
        changes_made = []

        # 1. Budget update check
        word_budget = parse_indian_number_words(mod_lower)
        if word_budget and word_budget > 0 and any(k in mod_lower for k in ["budget", "increase", "set", "update", "cost", "to"]):
            event.total_budget = word_budget
            changes_made.append(f"Updated total budget to ₹{word_budget:,.0f}")
        else:
            budget_match = re.search(r"(?:budget|cost)\s*(?:to|is)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|l|cr|crore)\b", mod_lower)
            if budget_match:
                mult = 10000000.0 if "cr" in mod_lower else 100000.0
                new_budget = float(budget_match.group(1)) * mult
                event.total_budget = new_budget
                changes_made.append(f"Updated total budget to ₹{new_budget:,.0f}")

        # 2. Guest count / attendance update check
        guest_match = re.search(r"(?:attendance|guests?|attendees?|people|pax)\s*(?:to|is)?\s*(\d+)", mod_lower)
        if not guest_match:
            guest_match = re.search(r"(?:change|set|update|increase)\s+(?:attendance|guests?|attendees?)\s*(?:to)?\s*(\d+)", mod_lower)
        if guest_match:
            new_guests = int(guest_match.group(1))
            event.guest_count = new_guests
            changes_made.append(f"Updated guest count to {new_guests}")

        # 3. Location / City shift check
        loc_match = re.search(r"(?:move|change|relocate|shift)\s+(?:the\s+)?(?:event\s+)?(?:to\s+|location\s+to\s+)([a-zA-Z\s]+)", mod_lower)
        if loc_match:
            raw_city = loc_match.group(1).strip()
            # Clean trailing words
            clean_city = re.split(r"\s+(?:and|with|on|at|for|also)\b", raw_city)[0].strip()
            if clean_city:
                event.location = "Gurgaon" if "gurgaon" in clean_city.lower() or "gurugram" in clean_city.lower() else clean_city.title()
                changes_made.append(f"Moved event location to {event.location}")

        # 4. Date shift check
        date_match = re.search(
            r"(?:date|to|on)\s*(?:to|is)?\s*(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*(\d{4})?",
            mod_lower,
        )
        if date_match:
            day = int(date_match.group(1))
            month_str = date_match.group(2)[:3]
            year = int(date_match.group(3)) if date_match.group(3) else (event.start_datetime.year if event.start_datetime else 2026)
            months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            month = months.index(month_str) + 1
            try:
                new_start = datetime(year, month, day, 9, 0, 0)
                event.start_datetime = new_start
                event.end_datetime = new_start + timedelta(hours=8)
                changes_made.append(f"Changed event date to {day} {month_str.title()} {year}")
            except ValueError:
                pass

        # 5. Requirement additions and removals
        existing_reqs = self.db.query(Requirement).filter(Requirement.event_id == event.id).all()
        current_cats = {r.type for r in existing_reqs}

        # Check removals
        for kw, cat in CATEGORY_KEYWORDS.items():
            remove_patterns = [
                rf"remove\s+(?:the\s+)?{re.escape(kw)}",
                rf"delete\s+(?:the\s+)?{re.escape(kw)}",
                rf"drop\s+(?:the\s+)?{re.escape(kw)}",
                rf"no\s+{re.escape(kw)}",
                rf"without\s+{re.escape(kw)}",
            ]
            if any(re.search(p, mod_lower) for p in remove_patterns):
                if cat in current_cats:
                    current_cats.remove(cat)
                    changes_made.append(f"Removed {cat.replace('_', ' ').title()}")

        # Check additions
        for kw, cat in CATEGORY_KEYWORDS.items():
            add_patterns = [
                rf"add\s+(?:the\s+)?{re.escape(kw)}",
                rf"include\s+(?:the\s+)?{re.escape(kw)}",
                rf"need\s+(?:the\s+)?{re.escape(kw)}",
                rf"require\s+(?:the\s+)?{re.escape(kw)}",
                rf"with\s+{re.escape(kw)}",
            ]
            if any(re.search(p, mod_lower) for p in add_patterns):
                if cat not in current_cats:
                    current_cats.add(cat)
                    changes_made.append(f"Added {cat.replace('_', ' ').title()}")

        # Update event name to match new params
        pax_str = f"{event.guest_count}-Person " if event.guest_count else ""
        event.name = f"{pax_str}{event.location} {event.event_type.replace('_', ' ').title()} 2026"

        # Re-persist updated requirements
        self.db.query(Requirement).filter(Requirement.event_id == event.id).delete()
        for cat in current_cats:
            req = Requirement(
                event_id=event.id,
                name=f"{cat.replace('_', ' ').title()} Sourcing",
                type=cat,
                required=True,
                description=f"Operational requirement for {cat.replace('_', ' ').title()}",
                value={"category": cat, "auto_source": True},
            )
            self.db.add(req)

        # Reset lifecycle to DRAFT to generate updated plan
        event.lifecycle_state = EventLifecycleState.DRAFT.value
        self.db.commit()
        self.db.refresh(event)

        # Regenerate plan
        updated_plan = self._planning_service.generate_plan(event.id)

        self._audit.record(
            event_id=event.id,
            actor_id=user_id,
            actor_type="USER",
            action="OPERATIONAL_PLAN_MODIFIED",
            action_type="PLANNING",
            target_type="EVENT",
            target_id=event.id,
            after_state={
                "changes": changes_made,
                "total_tasks": updated_plan.summary.total_tasks,
                "requirements": list(current_cats),
                "location": event.location,
                "total_budget": float(event.total_budget or 0),
            },
        )

        currency_sym = "₹" if event.currency == "INR" else "$"
        changes_str = "; ".join(changes_made) if changes_made else "Updated requirements and plan configuration"
        resp_msg = (
            f"Updated the operational plan based on your request ({changes_str}).\n\n"
            f"**New Plan Overview:**\n"
            f"• **Location:** {event.location}\n"
            f"• **Budget Allocation:** {currency_sym}{updated_plan.summary.total_estimated_budget:,.0f} / {currency_sym}{float(event.total_budget):,.0f}\n"
            f"• **Tasks:** {updated_plan.summary.total_tasks} executable tasks ({updated_plan.summary.critical_path_tasks} critical path)\n"
            f"• **Active Requirements:** {', '.join(c.replace('_', ' ').title() for c in current_cats)}\n\n"
            f"Say **'Start Operations'** when you are ready to begin autonomous execution."
        )

        return {
            "status": "PLAN_UPDATED",
            "message": resp_msg,
            "changes": changes_made,
            "event_id": event.id,
            "event": {
                "id": event.id,
                "name": event.name,
                "event_type": event.event_type,
                "location": event.location,
                "start_time": event.start_datetime.isoformat() if event.start_datetime else None,
                "end_time": event.end_datetime.isoformat() if event.end_datetime else None,
                "guest_count": event.guest_count,
                "total_budget": float(event.total_budget or 0),
                "currency": event.currency,
                "lifecycle_state": event.lifecycle_state,
                "requirements": list(current_cats),
            },
            "plan": updated_plan.model_dump(),
            "requirements": list(current_cats),
        }

