"""Unit tests for Domain Registry and Extensibility."""
import pytest
from app.models.enums import EventType, TaskPriority, DependencyType
from app.domains.base import BaseEventDomain
from app.domains.registry import (
    DomainRegistry,
    get_domain,
    UnsupportedEventTypeException,
    list_supported_domains,
)
from app.domains.wedding import WeddingDomain
from app.domains.college_fest import CollegeFestDomain
from app.domains.conference import ConferenceDomain
from app.domains.types import (
    RequirementDefinition,
    TaskDefinition,
    DependencyDefinition,
)


def test_registered_domains_resolution():
    """Verify that canonical event types resolve to their respective domain classes."""
    # Wedding
    wedding_domain = get_domain(EventType.WEDDING)
    assert isinstance(wedding_domain, WeddingDomain)
    assert wedding_domain.event_type == EventType.WEDDING

    # College Fest
    fest_domain = get_domain(EventType.COLLEGE_FEST)
    assert isinstance(fest_domain, CollegeFestDomain)
    assert fest_domain.event_type == EventType.COLLEGE_FEST

    # Conference
    conf_domain = get_domain(EventType.CONFERENCE)
    assert isinstance(conf_domain, ConferenceDomain)
    assert conf_domain.event_type == EventType.CONFERENCE


def test_domain_resolution_by_string_and_casing():
    """Verify registry normalizes strings, lowercase, and hyphens."""
    assert isinstance(get_domain("wedding"), WeddingDomain)
    assert isinstance(get_domain("WEDDING"), WeddingDomain)
    assert isinstance(get_domain("college_fest"), CollegeFestDomain)
    assert isinstance(get_domain("COLLEGE-FEST"), CollegeFestDomain)
    assert isinstance(get_domain("conference"), ConferenceDomain)
    assert isinstance(get_domain("CONFERENCE"), ConferenceDomain)


def test_unsupported_event_type_raises_clear_error():
    """Verify querying an unsupported event type raises UnsupportedEventTypeException with supported types."""
    with pytest.raises(UnsupportedEventTypeException) as exc_info:
        get_domain("UNKNOWN_PARTY")

    err = exc_info.value
    assert err.event_type == "UNKNOWN_PARTY"
    assert "WEDDING" in err.supported
    assert "COLLEGE_FEST" in err.supported
    assert "CONFERENCE" in err.supported
    assert "Unsupported event type 'UNKNOWN_PARTY'" in str(err)


def test_list_supported_domains():
    """Verify supported domains list contains wedding, college_fest, and conference."""
    supported = list_supported_domains()
    assert "wedding" in supported
    assert "college_fest" in supported
    assert "conference" in supported


def test_extensibility_register_new_domain_without_modifying_core():
    """Verify future event types (e.g. FestivalDomain) can be added via BaseEventDomain without core modifications."""
    class MusicFestivalDomain(BaseEventDomain):
        @property
        def event_type(self) -> str:
            return "MUSIC_FESTIVAL"

        def baseline_requirements(self):
            return [
                RequirementDefinition(
                    key="fest.stages",
                    category="STAGE",
                    name="Outdoor Stages",
                    is_mandatory=True,
                )
            ]

        def baseline_tasks(self):
            return [
                TaskDefinition(
                    key="fest.setup_stages",
                    name="Setup Outdoor Stages",
                    priority=TaskPriority.HIGH,
                ),
                TaskDefinition(
                    key="fest.sound_check",
                    name="Sound System Calibration",
                    priority=TaskPriority.HIGH,
                ),
            ]

        def baseline_dependencies(self):
            return [
                DependencyDefinition(
                    predecessor_key="fest.setup_stages",
                    successor_key="fest.sound_check",
                    dependency_type=DependencyType.FINISH_TO_START,
                )
            ]

        def provider_categories(self):
            return ["stage", "sound", "security"]

    custom_domain = MusicFestivalDomain()
    DomainRegistry.register(custom_domain)

    try:
        resolved = get_domain("MUSIC_FESTIVAL")
        assert resolved is custom_domain
        assert "MUSIC_FESTIVAL" in DomainRegistry.list_supported_event_types()
        assert len(resolved.baseline_tasks()) == 2
        assert len(resolved.baseline_dependencies()) == 1
    finally:
        # Clean up so test isolation is maintained
        if "MUSIC_FESTIVAL" in DomainRegistry._domains:
            del DomainRegistry._domains["MUSIC_FESTIVAL"]
