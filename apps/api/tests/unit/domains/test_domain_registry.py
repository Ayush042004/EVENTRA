"""Unit tests for DomainRegistry resolution and error handling."""
import pytest
from app.domains.registry import (
    DomainRegistry,
    get_domain,
    UnsupportedEventTypeException,
)
from app.domains.types import EventType
from app.domains.wedding import WeddingDomain
from app.domains.college_fest import CollegeFestDomain
from app.domains.conference import ConferenceDomain


def test_registry_resolves_wedding_domain():
    domain = get_domain(EventType.WEDDING)
    assert isinstance(domain, WeddingDomain)
    assert domain.event_type == EventType.WEDDING

    # Also verify string resolution
    str_domain = get_domain("wedding")
    assert isinstance(str_domain, WeddingDomain)
    assert str_domain.event_type == EventType.WEDDING


def test_registry_resolves_college_fest_domain():
    domain = get_domain(EventType.COLLEGE_FEST)
    assert isinstance(domain, CollegeFestDomain)
    assert domain.event_type == EventType.COLLEGE_FEST

    # Case insensitivity
    str_domain = get_domain("COLLEGE_FEST")
    assert isinstance(str_domain, CollegeFestDomain)


def test_registry_resolves_conference_domain():
    domain = get_domain(EventType.CONFERENCE)
    assert isinstance(domain, ConferenceDomain)
    assert domain.event_type == EventType.CONFERENCE

    str_domain = get_domain("conference")
    assert isinstance(str_domain, ConferenceDomain)


def test_registry_unsupported_event_type_raises_error():
    with pytest.raises(UnsupportedEventTypeException) as exc_info:
        get_domain("UNKNOWN_FESTIVAL")

    err = str(exc_info.value)
    assert "Unsupported event type 'UNKNOWN_FESTIVAL'" in err
    assert "WEDDING" in err
    assert "COLLEGE_FEST" in err
    assert "CONFERENCE" in err


def test_registry_lists_supported_types():
    supported = DomainRegistry.list_supported_event_types()
    assert "WEDDING" in supported
    assert "COLLEGE_FEST" in supported
    assert "CONFERENCE" in supported


def test_future_domain_extensibility_without_core_modifications():
    """Verify that adding a new domain (e.g. FESTIVAL) requires zero modifications to core planning/routes."""
    from app.domains.base import BaseEventDomain
    from app.domains.types import (
        RequirementDefinition,
        TaskDefinition,
        DependencyDefinition,
        DependencyType,
    )

    class MusicFestivalDomain(BaseEventDomain):
        @property
        def event_type(self):
            return "MUSIC_FESTIVAL"

        def baseline_requirements(self):
            return [
                RequirementDefinition(
                    key="music_fest.stage",
                    category="STAGE",
                    name="Main Stage Rig",
                )
            ]

        def baseline_tasks(self):
            return [
                TaskDefinition(key="fest.setup", name="Festival Setup"),
                TaskDefinition(key="fest.gates", name="Open Gates"),
            ]

        def baseline_dependencies(self):
            return [
                DependencyDefinition(
                    predecessor_key="fest.setup",
                    successor_key="fest.gates",
                    dependency_type=DependencyType.FINISH_TO_START,
                )
            ]

        def provider_categories(self):
            return ["STAGE", "SOUND"]

    fest_domain = MusicFestivalDomain()
    DomainRegistry.register(fest_domain)

    # Retrieval works immediately
    resolved = get_domain("MUSIC_FESTIVAL")
    assert resolved.event_type == "MUSIC_FESTIVAL"
    assert len(resolved.baseline_tasks()) == 2
    assert "STAGE" in resolved.provider_categories()

