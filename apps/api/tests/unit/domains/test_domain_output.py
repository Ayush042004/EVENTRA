"""Unit tests verifying domain output structure and domain operational differentiation."""
from app.domains.wedding import WeddingDomain
from app.domains.college_fest import CollegeFestDomain
from app.domains.conference import ConferenceDomain


def test_wedding_domain_output():
    """Verify Wedding domain baseline requirements, tasks, dependencies, and provider categories."""
    domain = WeddingDomain()

    # Requirements
    reqs = domain.baseline_requirements()
    assert len(reqs) >= 8
    req_keys = {r.key for r in reqs}
    assert "wedding.venue" in req_keys
    assert "wedding.catering" in req_keys
    assert "wedding.decoration" in req_keys
    assert "wedding.photography" in req_keys
    assert "wedding.music" in req_keys
    assert "wedding.power" in req_keys
    assert "wedding.ceremony" in req_keys

    # Tasks
    tasks = domain.baseline_tasks()
    assert len(tasks) >= 8
    task_keys = {t.key for t in tasks}
    assert "wedding.venue_prep" in task_keys
    assert "wedding.power_setup" in task_keys
    assert "wedding.decor_setup" in task_keys
    assert "wedding.catering_setup" in task_keys
    assert "wedding.sound_music_setup" in task_keys
    assert "wedding.ceremony_prep" in task_keys
    assert "wedding.readiness_check" in task_keys

    # Dependencies
    deps = domain.baseline_dependencies()
    assert len(deps) >= 8
    for dep in deps:
        assert dep.predecessor_key in task_keys
        assert dep.successor_key in task_keys
        assert dep.predecessor_key != dep.successor_key

    # Specific operational relationships
    dep_pairs = {(d.predecessor_key, d.successor_key) for d in deps}
    assert ("wedding.venue_prep", "wedding.decor_setup") in dep_pairs
    assert ("wedding.power_setup", "wedding.sound_music_setup") in dep_pairs
    assert ("wedding.sound_music_setup", "wedding.sound_check") in dep_pairs
    assert ("wedding.ceremony_prep", "wedding.readiness_check") in dep_pairs

    # Provider categories
    cats = domain.provider_categories()
    assert "catering" in cats
    assert "decoration" in cats
    assert "photography" in cats
    assert "music" in cats
    assert "lighting" in cats
    assert "transportation" in cats


def test_college_fest_domain_output():
    """Verify College Fest domain baseline requirements, tasks, dependencies, and provider categories."""
    domain = CollegeFestDomain()

    # Requirements
    reqs = domain.baseline_requirements()
    assert len(reqs) >= 8
    req_keys = {r.key for r in reqs}
    assert "college_fest.venue" in req_keys
    assert "college_fest.stage" in req_keys
    assert "college_fest.sound" in req_keys
    assert "college_fest.lighting" in req_keys
    assert "college_fest.power" in req_keys
    assert "college_fest.security" in req_keys
    assert "college_fest.registration" in req_keys

    # Tasks
    tasks = domain.baseline_tasks()
    assert len(tasks) >= 8
    task_keys = {t.key for t in tasks}
    assert "college_fest.venue_prep" in task_keys
    assert "college_fest.power_setup" in task_keys
    assert "college_fest.stage_setup" in task_keys
    assert "college_fest.equipment_setup" in task_keys
    assert "college_fest.sound_setup" in task_keys
    assert "college_fest.lighting_setup" in task_keys
    assert "college_fest.security_prep" in task_keys
    assert "college_fest.technical_checks" in task_keys
    assert "college_fest.final_readiness" in task_keys

    # Dependencies
    deps = domain.baseline_dependencies()
    assert len(deps) >= 8
    for dep in deps:
        assert dep.predecessor_key in task_keys
        assert dep.successor_key in task_keys

    dep_pairs = {(d.predecessor_key, d.successor_key) for d in deps}
    assert ("college_fest.stage_setup", "college_fest.equipment_setup") in dep_pairs
    assert ("college_fest.power_setup", "college_fest.equipment_setup") in dep_pairs
    assert ("college_fest.equipment_setup", "college_fest.sound_setup") in dep_pairs
    assert ("college_fest.sound_setup", "college_fest.technical_checks") in dep_pairs
    assert ("college_fest.technical_checks", "college_fest.final_readiness") in dep_pairs

    # Provider categories
    cats = domain.provider_categories()
    assert "sound" in cats
    assert "lighting" in cats
    assert "stage" in cats
    assert "security" in cats
    assert "power" in cats
    assert "equipment" in cats


def test_conference_domain_output():
    """Verify Conference domain baseline requirements, tasks, dependencies, and provider categories."""
    domain = ConferenceDomain()

    # Requirements
    reqs = domain.baseline_requirements()
    assert len(reqs) >= 9
    req_keys = {r.key for r in reqs}
    assert "conference.venue" in req_keys
    assert "conference.seating" in req_keys
    assert "conference.stage" in req_keys
    assert "conference.av" in req_keys
    assert "conference.microphones" in req_keys
    assert "conference.projector_display" in req_keys
    assert "conference.connectivity" in req_keys
    assert "conference.registration" in req_keys
    assert "conference.catering" in req_keys
    assert "conference.signage" in req_keys
    assert "conference.power" in req_keys

    # Tasks
    tasks = domain.baseline_tasks()
    assert len(tasks) >= 9
    task_keys = {t.key for t in tasks}
    assert "conference.venue_setup" in task_keys
    assert "conference.power_setup" in task_keys
    assert "conference.seating_setup" in task_keys
    assert "conference.stage_setup" in task_keys
    assert "conference.av_setup" in task_keys
    assert "conference.mic_setup" in task_keys
    assert "conference.display_setup" in task_keys
    assert "conference.registration_setup" in task_keys
    assert "conference.connectivity_check" in task_keys
    assert "conference.final_tech_check" in task_keys
    assert "conference.readiness_verification" in task_keys

    # Dependencies
    deps = domain.baseline_dependencies()
    assert len(deps) >= 10
    for dep in deps:
        assert dep.predecessor_key in task_keys
        assert dep.successor_key in task_keys

    dep_pairs = {(d.predecessor_key, d.successor_key) for d in deps}
    assert ("conference.venue_setup", "conference.seating_setup") in dep_pairs
    assert ("conference.power_setup", "conference.av_setup") in dep_pairs
    assert ("conference.av_setup", "conference.mic_setup") in dep_pairs
    assert ("conference.mic_setup", "conference.final_tech_check") in dep_pairs
    assert ("conference.display_setup", "conference.final_tech_check") in dep_pairs
    assert ("conference.final_tech_check", "conference.readiness_verification") in dep_pairs

    # Provider categories
    cats = domain.provider_categories()
    assert "av" in cats
    assert "catering" in cats
    assert "stage" in cats
    assert "lighting" in cats
    assert "connectivity" in cats
    assert "signage" in cats


def test_distinct_domain_operational_structures():
    """Verify domains have clearly distinct operational profiles (Wedding != Fest != Conference)."""
    wedding = WeddingDomain()
    fest = CollegeFestDomain()
    conf = ConferenceDomain()

    wedding_task_keys = {t.key for t in wedding.baseline_tasks()}
    fest_task_keys = {t.key for t in fest.baseline_tasks()}
    conf_task_keys = {t.key for t in conf.baseline_tasks()}

    # No identical keys across domains
    assert not (wedding_task_keys & fest_task_keys)
    assert not (wedding_task_keys & conf_task_keys)
    assert not (fest_task_keys & conf_task_keys)

    # Specific checks
    assert "wedding.ceremony_prep" in wedding_task_keys
    assert "college_fest.stage_setup" in fest_task_keys
    assert "conference.connectivity_check" in conf_task_keys
