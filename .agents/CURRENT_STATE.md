# Current Development State: EVENTRA

This is a living status document tracking the active engineering state of EVENTRA.

---

## Overall Status
**STATUS:** PHASE 2 COMPLETE

**CURRENT PHASE:** PHASE 2 — Event Specification + Domain Intelligence (Completed)

---

## Phase 2 Implementation Details

### 1. Domain Architecture Implemented
- **Base Domain Contract (`app/domains/base.py`)**:
  - `BaseEventDomain(ABC)`: Abstract contract requiring `event_type`, `baseline_requirements()`, `baseline_tasks()`, `baseline_dependencies()`, and `provider_categories()`.
  - Built-in `validate_baseline()`: Deterministic validation asserting unique task keys, valid predecessor/successor endpoints, self-dependency rejection, and duplicate edge prevention.
- **Typed Domain Definitions (`app/domains/types.py`)**:
  - `RequirementDefinition`: Stable key, operational category, name, description, mandatory flag, parameters.
  - `TaskDefinition`: Stable key, name, description, priority (`TaskPriority`), phase, required provider category, critical flag (`is_critical`), duration estimate.
  - `DependencyDefinition`: Predecessor key, successor key, dependency type (`DependencyType`), lag minutes.
  - `ProviderCategoryDefinition`: Category code, display name, description, required flag.
  - `ObjectivePriority`: Controlled priority classification.

### 2. Supported Event Types
1. **WEDDING (`app/domains/wedding/`)**:
   - Baseline requirements: Venue, catering, decoration, photography, videography, music/entertainment, guest seating, lighting, power, ceremony.
   - Baseline tasks: Venue preparation, power infrastructure setup, decor setup, seating setup, catering setup, sound & music setup, ceremony prep, sound check, photo & video setup, guest area prep, readiness check.
   - Baseline dependencies: Logical ordering from venue access through power, sound check, and final readiness check.
   - Provider categories: Catering, decoration, photography, videography, music, lighting, transportation, venue.
2. **COLLEGE_FEST (`app/domains/college_fest/`)**:
   - Baseline requirements: Festival grounds, concert stages, high-voltage power distribution, concert sound reinforcement, stage lighting, security/crowd control, registration/check-in hubs, catering, heavy equipment.
   - Baseline tasks: Ground clearance & prep, 3-phase power distribution, stage construction, truss rigging & equipment mounting, concert sound rigging, stage lighting & effects setup, security perimeter setup, registration booths setup, catering setup, technical checks, final readiness signoff.
   - Baseline dependencies: Structural dependencies from stage/power through rigging, sound/lighting, technical checks, and readiness signoff.
   - Provider categories: Sound, lighting, stage, security, power, equipment, catering, venue, decoration.
3. **CONFERENCE (`app/domains/conference/`)**:
   - Baseline requirements: Convention hall/auditorium, executive seating, keynote stage & lectern, professional AV system, speech & Q&A microphones, 4K LED/displays, high-density enterprise Wi-Fi connectivity, badge printing registration, executive catering, digital signage, clean power grid.
   - Baseline tasks: Venue access & hall handover, AV clean power distribution, auditorium seating setup, keynote stage setup, audio system installation, wireless mic pairing, display & LED wall calibration, registration kiosk setup, Wi-Fi connectivity validation, catering setup, final technical rehearsal check, event readiness verification.
   - Baseline dependencies: Interconnected dependencies verifying power -> AV & displays -> microphone check -> final rehearsal -> readiness verification.
   - Provider categories: AV, catering, stage, lighting, connectivity, internet, equipment, signage, venue, logistics.

### 3. Domain Registry (`app/domains/registry.py`)
- `DomainRegistry`: Central registry mapping canonical `EventType` to domain instances.
- Auto-registers `WeddingDomain`, `CollegeFestDomain`, and `ConferenceDomain` upon initialization.
- `get_domain(event_type)`: Resolves domain handlers via enum or normalized string ("wedding", "COLLEGE_FEST", "conference").
- Strict error handling: Unsupported event types raise `UnsupportedEventTypeException` listing supported options; no silent fallback to generic domains.
- Future extensibility: New event domains (e.g. `FestivalDomain`) can be added by implementing `BaseEventDomain` and registering in `DomainRegistry` without touching any core logic.

### 4. Normalized Event Specification (`app/schemas/specification.py`)
- `EventSpecification`: Complete serializable, deterministic specification containing:
  - Event identity, title, description, event type, status, start/end datetimes, scalar guest capacity, budget, currency, location.
  - Merged domain baseline and custom requirements.
  - Baseline operational tasks and dependency DAG edges referencing stable task keys.
  - Provider categories, operational constraints (`ConstraintDefinition`), and prioritized business objectives (`ObjectiveDefinition`).
  - Custom configuration dictionary for domain-specific parameters.
- `EventSpecificationPreviewRequest`: Schema enabling previewing event specifications prior to persistence.

### 5. Event Specification Service (`app/services/specification_service.py`)
- `SpecificationService`:
  - Builds normalized `EventSpecification` from either raw dictionary payloads or Phase 1 SQLAlchemy `Event` ORM models.
  - Combines domain baselines with event-specific requirement overrides and custom requirement additions.
  - Preserves event-specific constraints and objectives.
  - Standalone `validate_specification()` for deterministic structural validation.
- Validation rules enforced:
  - Valid supported event type.
  - Logical date ordering (`end_time > start_time`).
  - Non-negative scalar guest count.
  - Dependency integrity: all predecessors and successors reference existing tasks; rejects self-dependencies and duplicate edges.
  - Structural constraint and objective integrity.

### 6. API Endpoints (`app/api/routes/events.py`)
- `POST /api/events/specification/preview`: Preview an EventSpecification without database mutation.
- `GET /api/events/{event_id}/specification`: Retrieve deterministic EventSpecification for existing database events or demo events (`wedding_demo`, `college_fest_demo`, `conference_demo`).

### 7. Tests Added (Phase 2 Test Suite)
- `tests/unit/domains/test_domain_registry.py`:
  - Resolution of canonical enum event types (`WEDDING`, `COLLEGE_FEST`, `CONFERENCE`).
  - Resolution with string casing and hyphen normalization.
  - Rejection of unsupported event types with `UnsupportedEventTypeException`.
  - Extensibility: dynamically registering a new `MusicFestivalDomain` without core modifications.
- `tests/unit/domains/test_domain_output.py`:
  - Baseline requirements, tasks, dependencies, and provider categories for all 3 domains.
  - Verification of distinct operational profiles (Wedding != Fest != Conference).
- `tests/unit/domains/test_dependency_validation.py`:
  - Valid task dependency DAG edges.
  - Rejection of self-dependencies.
  - Rejection of unknown predecessor and successor keys.
  - Rejection of duplicate dependency edges and duplicate task keys.
- `tests/unit/services/test_specification_service.py`:
  - Building specifications for Wedding, College Fest, Conference.
  - Requirement override (e.g. making mandatory requirement optional) and custom requirement additions.
  - Preservation of constraints and objectives.
  - Validation rejections: invalid dates (`end <= start`), negative guest count, unsupported event type.
  - Determinism verification: identical inputs produce identical outputs with no drift.
  - Seamless conversion from SQLAlchemy `Event` ORM models with child relationships.
- `tests/integration/api/test_specification_api.py`:
  - `GET /api/events/{event_id}/specification` for demo events and database-persisted events.
  - `GET /api/events/{event_id}/specification` 404 handling.
  - `POST /api/events/specification/preview` with custom requirements, constraints, objectives.
  - Validation error handling (400 Bad Request with standardized `AppException` error payload) for date violations, unsupported types, and negative capacity.

### 8. Verification Results
- **Full Test Suite**: PASS (76/76 tests passing: 46 Phase 1 tests + 30 Phase 2 tests).
- **Phase 2 Unit & Integration Tests**: PASS (30/30 passing in 0.24s).
- **Bytecode Compilation (`compileall`)**: PASS (0 errors).
- **FastAPI Startup & Routes**: PASS (All API routes mounted cleanly under `/api` prefix).
- **Health**: PASS (`/health` returns HTTP 200).

### 9. Known Limitations
- Scheduling, timestamps, and resource allocation are deliberately not computed (deferred to Phase 4 Planning Engine).
- Provider matching and venue search are not performed (deferred to Phase 3 Venue + Provider Network).
- Risk scoring, dependency impact analysis, and incident recovery are deferred to later phases.
- Purely deterministic; no LLM, LangGraph, or external API dependencies.

---

## Next Phase
**NEXT PHASE = PHASE 3 — VENUE + PROVIDER NETWORK**
