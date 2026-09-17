"""Unit tests verifying baseline outputs for each supported domain."""
import pytest
from app.domains.registry import get_domain
from app.domains.types import EventType, ObjectivePriority, DependencyType


@pytest.mark.parametrize("event_type", [
    EventType.WEDDING,
    EventType.COLLEGE_FEST,
    EventType.CONFERENCE,
])
def test_domains_expose_complete_baselines(event_type):
    domain = get_domain(event_type)

    requirements = domain.baseline_requirements()
    tasks = domain.baseline_tasks()
    dependencies = domain.baseline_dependencies()
    categories = domain.provider_categories()

    assert len(requirements) > 0, f"{event_type} must have baseline requirements"
    assert len(tasks) > 0, f"{event_type} must have baseline tasks"
    assert len(dependencies) > 0, f"{event_type} must have baseline dependencies"
    assert len(categories) > 0, f"{event_type} must have provider categories"

    # Tasks must have stable keys, non-empty names, valid priorities
    task_keys = set()
    for task in tasks:
        assert task.key, f"Task in {event_type} missing key"
        assert task.key.startswith(event_type.value.lower() + "."), f"Task key {task.key} should start with domain prefix"
        assert task.name, f"Task {task.key} missing name"
        assert isinstance(task.priority, ObjectivePriority)
        assert task.phase in {"PRE_EVENT", "SETUP", "EXECUTION", "POST_EVENT"}
        assert task.key not in task_keys, f"Duplicate task key {task.key}"
        task_keys.add(task.key)

    # Dependencies must reference valid task keys
    for dep in dependencies:
        assert dep.predecessor_key in task_keys, f"Dependency predecessor {dep.predecessor_key} not in {event_type} tasks"
        assert dep.successor_key in task_keys, f"Dependency successor {dep.successor_key} not in {event_type} tasks"
        assert dep.predecessor_key != dep.successor_key, f"Self dependency on {dep.predecessor_key}"
        assert isinstance(dep.dependency_type, DependencyType)

    # Baseline self-validation should pass
    domain.validate_baseline()


def test_wedding_domain_specific_content():
    domain = get_domain(EventType.WEDDING)
    req_keys = {r.key for r in domain.baseline_requirements()}
    task_keys = {t.key for t in domain.baseline_tasks()}
    categories = domain.provider_categories()

    # Requirements checks
    assert "wedding.venue" in req_keys
    assert "wedding.catering" in req_keys
    assert "wedding.decoration" in req_keys
    assert "wedding.photography" in req_keys
    assert "wedding.music" in req_keys

    # Tasks checks
    assert "wedding.venue_prep" in task_keys
    assert "wedding.decor_setup" in task_keys
    assert "wedding.sound_music_setup" in task_keys
    assert "wedding.readiness_check" in task_keys

    # Provider categories checks
    assert "CATERING" in categories
    assert "DECOR" in categories
    assert "PHOTOGRAPHY" in categories


def test_college_fest_domain_specific_content():
    domain = get_domain(EventType.COLLEGE_FEST)
    req_keys = {r.key for r in domain.baseline_requirements()}
    task_keys = {t.key for t in domain.baseline_tasks()}
    categories = domain.provider_categories()

    # Requirements checks
    assert "college_fest.stage" in req_keys
    assert "college_fest.sound" in req_keys
    assert "college_fest.lighting" in req_keys
    assert "college_fest.power" in req_keys
    assert "college_fest.security" in req_keys

    # Tasks checks
    assert "college_fest.stage_setup" in task_keys
    assert "college_fest.power_setup" in task_keys
    assert "college_fest.technical_checks" in task_keys
    assert "college_fest.final_readiness" in task_keys

    # Provider categories checks
    assert "STAGE" in categories
    assert "SOUND" in categories
    assert "SECURITY" in categories


def test_conference_domain_specific_content():
    domain = get_domain(EventType.CONFERENCE)
    req_keys = {r.key for r in domain.baseline_requirements()}
    task_keys = {t.key for t in domain.baseline_tasks()}
    categories = domain.provider_categories()

    # Requirements checks
    assert "conference.venue" in req_keys
    assert "conference.av" in req_keys
    assert "conference.microphones" in req_keys
    assert "conference.projector_display" in req_keys
    assert "conference.connectivity" in req_keys

    # Tasks checks
    assert "conference.av_setup" in task_keys
    assert "conference.mic_setup" in task_keys
    assert "conference.display_setup" in task_keys
    assert "conference.final_tech_check" in task_keys

    # Provider categories checks
    assert "AV_LIGHTING" in categories
    assert "LOGISTICS" in categories
    assert "STAGE" in categories
