# Current Development State: EVENTRA

This is a living status document tracking the active engineering state of EVENTRA.

---

## Overall Status
**STATUS:** PHASE 8 COMPLETE

**CURRENT PHASES COMPLETED:**
- Phase 0: Project Architecture & Environment Foundation
- Phase 1: Foundational Domain Models & Core Event Lifecycle
- Phase 2: Domain Intelligence & Event Specification
- Phase 3: Venue Discovery & Provider Network
- Phase 4: Deterministic Planning Engine (Tasks, Dependencies, Resources, Budget Items)
- Phase 5: Dependency Engine (DAG, CPM), Schedule Engine, Budget Engine (Decimal)
- Phase 6: Live Event State Engine (Readiness, State Machine, Status Cascading, Deviations, Conclude)
- Phase 7: Incident Detection, Impact Analysis Engine & Operational Risk Engine
- Phase 8: Deterministic Recovery Engine (Candidate Generation, Simulation, Validation, Scoring, Deltas)

---

## Phase 8: Deterministic Recovery Engine

### 1. Recovery Engine Module (`app/engines/recovery/`)
- **Candidate Generator (`generator.py`)**:
  - `RecoveryGenerator.generate_candidates(context)`: Generates candidate operational recovery options based strictly on facts in authoritative state.
  - Generates deterministic candidate strategies: `WAIT`, `BACKUP`, `REASSIGN`, `RESCHEDULE`, `COMPRESS`.
  - Filters out providers with missing base cost (`base_cost is None`) — never fabricates availability or prices.
  - Supports resource reassignments for `RESOURCE_SHORTAGE` incidents.
  - Sorts candidates for strict determinism.

- **Recovery Context & Types (`types.py`)**:
  - `RecoveryContext`: Structured container for event, incident, impact, risk, tasks, dependencies, budget items, resources, providers, provider assignments, venue, objectives, constraints, live state, and snapshot version hash.
  - `RecoveryCandidate`, `RecoverySimulation`, `ValidationResult`.

- **Recovery Simulator (`simulator.py`)**:
  - `RecoverySimulator.simulate(candidate, context)`: Re-runs Schedule Engine, Impact Analyzer, and Risk Calculator in memory for hypothetical state without mutating real database objects.
  - Computes structured deltas: `schedule_delta`, `budget_delta`, `resource_delta`, `provider_delta`, `objective_delta`, `constraint_impact`, `risk_after`.

- **Recovery Validator (`validator.py`)**:
  - `RecoveryValidator.validate(simulation, context)`: Enforces hard invariants across dependency graph topology, schedule windows, provider category/availability/cost, resource status/quantity, budget caps, hard constraints, and venue capacity/status.
  - Distinguishes hard constraint violations (`is_feasible=False`) from soft constraint warnings.

- **Recovery Scorer (`scorer.py`)**:
  - `RecoveryScorer.score(simulation, context)`: Pure transparent deterministic scoring model for feasible options:
    `score = risk_reduction (0..50) + schedule_slack (0..25) + objective_restoration (0..15) - budget_penalty (0..10)`.
  - `Scorer.rank(options)`: Ranks feasible options in descending score order with tie-breakers.

### 2. Service Layer & Snapshot Management (`app/services/recovery_service.py`)
- `RecoveryService`:
  - `generate_recovery_options`: Generates candidates, simulates state, validates constraints, calculates scores, and persists `Recovery` records to `recovery_options` table.
  - `list_recovery_options`: Detects snapshot stale status (`is_stale=True`) when live event state changes.
  - `recalculate_options`: Marks stale options as `STALE` and generates fresh recovery options from current live snapshot.
  - Enforces event-scoped authorization (`ForbiddenException` for non-members).
  - Guarantees zero execution or state mutation of tasks, providers, schedule, or event state.

### 3. Data Model & Persistence (`app/models/recovery.py`)
- `Recovery` model (`recovery_options` table):
  - Stores strategy type, feasibility status (`FEASIBLE` / `INFEASIBLE` / `STALE`), score, rank, snapshot hash, affected entities, and structured deltas.

### 4. API Endpoints (`app/api/routes/recovery.py`)
- `POST /api/events/{event_id}/incidents/{incident_id}/recovery/options`: Generates recovery options (201 Created).
- `GET /api/events/{event_id}/incidents/{incident_id}/recovery/options`: Lists options with stale detection.
- `POST /api/events/{event_id}/incidents/{incident_id}/recovery/recalculate`: Recalculates fresh options.
- `GET /api/events/{event_id}/incidents/{incident_id}/recovery/options/{option_id}`: Retrieves single option.

> [!IMPORTANT]
> Phase 8 generates and validates recovery options but does NOT execute them. No booking, no schedule mutation, no money spending occurs in Phase 8.

---

## Verification Results
- **Full Test Suite**: PASS (162/162 tests passing).
  - Engine unit tests: 7 passed (`test_recovery_engine.py`).
  - Service unit tests: 3 passed (`test_recovery_service.py`).
  - API integration tests: 2 passed (`test_recovery_api.py`).
  - Scenario integration tests: 3 passed (`test_phase8_recovery_scenarios.py` covering College Fest Caterer No-Show, Resource Shortage, Venue Issue).
- **FastAPI Startup & Routes**: PASS (Mounted cleanly under `/api`).
- **Zero AI / Deterministic Rule**: STRICTLY ENFORCED. Zero LLM, zero LangGraph, zero external APIs.

---

## Next Phase
**NEXT PHASE = PHASE 9 — Approval + Authorization + Action**


