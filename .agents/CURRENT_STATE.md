# Current Development State: EVENTRA

This is a living status document tracking the active engineering state of EVENTRA.

---

## Overall Status
**STATUS:** PHASE 7 COMPLETE

**CURRENT PHASES COMPLETED:**
- Phase 0: Project Architecture & Environment Foundation
- Phase 1: Foundational Domain Models & Core Event Lifecycle
- Phase 2: Domain Intelligence & Event Specification
- Phase 3: Venue Discovery & Provider Network
- Phase 4: Deterministic Planning Engine (Tasks, Dependencies, Resources, Budget Items)
- Phase 5: Dependency Engine (DAG, CPM), Schedule Engine, Budget Engine (Decimal)
- Phase 6: Live Event State Engine (Readiness, State Machine, Status Cascading, Deviations, Conclude)
- Phase 7: Incident Detection, Impact Analysis Engine & Operational Risk Engine

---

## Phase 7: Incident Detection → Impact Analysis → Risk Engine

### 1. Incident Domain & Ingestion
- **Enums (`app/models/enums.py`)**:
  - `IncidentType`: `VENDOR_DELAY`, `VENDOR_NO_SHOW`, `VENUE_ISSUE`, `RESOURCE_SHORTAGE`, `CAPACITY_PROBLEM`, `SCHEDULE_DEVIATION`, `DEPENDENCY_FAILURE`.
  - `IncidentStatus`: `OPEN`, `ACKNOWLEDGED`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`.
  - `IncidentSeverity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, `EMERGENCY`.
- **Data Model (`app/models/incident.py`)**:
  - `Incident`: Operational model with foreign keys to `events`, `tasks`, `vendors`, `resources`, `venues`, JSON storage for `evidence_metadata`, `impact_result`, and `risk_result`, timestamps, and resolution tracking.
  - Linked bidirectionally to `Event.incidents` with cascade delete-orphan.
- **Pydantic Schemas (`app/schemas/incident.py`)**:
  - `IncidentCreate`, `IncidentUpdate`, `IncidentResolveRequest`, `ImpactResultResponse`, `RiskResultResponse`, `IncidentResponse`, `IncidentListResponse`.
- **Database Migration (`alembic/versions/0004_phase7_incident_impact_risk.py`)**:
  - Creates `incidents` table with 8 indexes and foreign key constraints. Passes full upgrade and downgrade verification in `tests/test_migration.py`.

### 2. Deterministic Impact Engine (`app/engines/impact/`)
- **Propagation (`propagation.py`)**:
  - Uses in-memory `DependencyGraph` to discover downstream indirect tasks via DAG traversal.
  - Excludes upstream predecessors from downstream cascade.
  - Flags blocked tasks (tasks where all upstream dependencies are not completed).
- **Severity (`severity.py`)**:
  - Pure deterministic `ImpactSeverityCalculator` evaluating critical path breach, downstream task count, time pressure, and critical objectives (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- **Analyzer (`analyzer.py`)**:
  - Comprehensive `ImpactAnalyzer` evaluating direct vs indirect tasks, schedule consequences (consumed slack, remaining slack, critical path breach, deadline pressure), resource shortages, provider assignments, committed budget exposure, and strategic objective threats.

### 3. Pure Deterministic Risk Engine (`app/engines/risk/`)
- **Classifier (`classifier.py`)**:
  - Explicit threshold mapping without opaque scoring or AI confidence:
    - 0 – 24.9: `LOW` risk → Target state `NORMAL`
    - 25.0 – 49.9: `MEDIUM` risk → Target state `AT_RISK`
    - 50.0 – 74.9: `HIGH` risk → Target state `CRITICAL`
    - 75.0 – 100.0: `CRITICAL` risk → Target state `EMERGENCY`
- **Calculator (`calculator.py`)**:
  - Evaluates 8 explicit, explainable weighted factors:
    1. Time remaining (weight 0.15)
    2. Task criticality (weight 0.20)
    3. Dependency count & depth (weight 0.15)
    4. Schedule slack & critical path breach (weight 0.15)
    5. Resource availability & shortage count (weight 0.10)
    6. Provider network alternatives (weight 0.10)
    7. Budget headroom & committed cost at risk (weight 0.05)
    8. Strategic objective criticality (weight 0.10)
  - Produces human-readable explanations for every factor score.

### 4. Service Layer (`app/services/incident_service.py`)
- `IncidentService`:
  - Enforces event-scoped RBAC authorization (rejects non-members with 403 `ForbiddenException`).
  - Validates operational foreign entities (tasks, vendors, resources, venues) belonging to the event.
  - Ingests and normalizes incidents.
  - Executes Impact Analysis → Risk Engine in single transaction.
  - Updates `Event.state` authoritatively and records audit trail in `StateTransition`.
  - Escalates `Event.lifecycle_state` (`LIVE` → `INCIDENT` / `EMERGENCY`) on high/critical incidents.
  - Supports deterministic re-evaluation (`recalculate_incident`) and resolution (`resolve_incident`) which restores `Event.state` to `NORMAL` when all active incidents are resolved.

### 5. API Routes (`app/api/routes/incidents.py`)
- `POST /api/events/{event_id}/incidents`: Ingests incident, computes impact and risk, escalates state (201 Created).
- `GET /api/events/{event_id}/incidents`: Lists incidents with status and type filters and pagination.
- `GET /api/events/{event_id}/incidents/{incident_id}`: Retrieves single incident with full impact and risk results.
- `GET /api/events/{event_id}/incidents/{incident_id}/impact`: Retrieves structured impact result.
- `GET /api/events/{event_id}/incidents/{incident_id}/risk`: Retrieves structured risk evaluation with 8 factors.
- `POST /api/events/{event_id}/incidents/{incident_id}/recalculate`: Deterministically recalculates impact and risk against live state.
- `POST /api/events/{event_id}/incidents/{incident_id}/resolve`: Resolves incident and re-evaluates event state.

---

## Verification Results
- **Full Test Suite**: PASS (147/147 tests passing).
  - Unit tests: 75 passed (including `test_impact_engine.py`, `test_risk_engine.py`, `test_incident_service.py`).
  - API integration tests: 31 passed (including `test_incidents_api.py` covering all 7 endpoints, 403 RBAC, 400 validation).
  - Scenario integration tests: 4 passed (`test_phase7_scenarios.py` covering vendor no-show, vendor delay, resource shortage, multi-incident resolution).
  - Domain & migration tests: 37 passed (`test_migration.py` full upgrade/downgrade cycle passing through revision 0004).
- **FastAPI Startup & Routes**: PASS (Mounted cleanly under `/api`).
- **Zero AI / Deterministic Rule**: STRICTLY ENFORCED. Zero LLM, zero LangGraph, zero external APIs.

---

## Next Phase
**NEXT PHASE = PHASE 8 — RECOVERY ENGINE**

