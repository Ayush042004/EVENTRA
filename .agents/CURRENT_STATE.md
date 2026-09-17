# Current Development State: EVENTRA

This is a living status document tracking the active engineering state of EVENTRA.

---

## Overall Status
**STATUS:** PHASE 6 COMPLETE

**CURRENT PHASES COMPLETED:**
- Phase 0: Project Architecture & Environment Foundation
- Phase 1: Foundational Domain Models & Core Event Lifecycle
- Phase 2: Domain Intelligence & Event Specification
- Phase 3: Venue Discovery & Provider Network
- Phase 4: Deterministic Planning Engine (Tasks, Dependencies, Resources, Budget Items)
- Phase 5: Dependency Engine (DAG, CPM), Schedule Engine, Budget Engine (Decimal)
- Phase 6: Live Event State Engine (Readiness, State Machine, Status Cascading, Deviations, Conclude)

---

## Phases 4, 5, 6 Implementation Details

### 1. Phase 4: Planning Engine
- **Engines (`app/engines/planning/`)**:
  - `TaskGenerator`: Converts domain baseline tasks into materializable task dictionaries with stable domain `key`, priority, phase, required provider category, and duration.
  - `DependencyBuilder`: Maps domain dependency DAG edges to persisted task IDs with lag minutes.
  - `ResourcePlanner`: Allocates equipment, facility, staff, material, and transport resources based on event requirements.
  - `BudgetPlanner`: Proportionally allocates total event budget across provider categories, with 10% contingency and optional vendor cost overrides.
  - `RequirementInterpreter`: Validates all mandatory requirements have matching allocated resources.
- **Service (`app/services/planning_service.py`)**:
  - `PlanningService`: Orchestrates full pipeline: `EventSpecification` → Tasks → Dependencies → Resources → Budget items → Transitions `lifecycle_state` to `PLANNED` → Records `StateTransition`.
- **API (`app/api/routes/planning.py`)**:
  - `POST /api/events/{event_id}/plan`: Generates operational plan.
  - `GET /api/events/{event_id}/plan`: Retrieves operational plan.

### 2. Phase 5: Dependency, Schedule & Budget Engines
- **Dependency Engine (`app/engines/dependency/`)**:
  - `DependencyGraph`: Pure in-memory DAG supporting topological sort (Kahn's algorithm), cycle detection (DFS), and predecessor/successor/lag queries without database calls.
  - `CriticalPathCalculator`: Pure Critical Path Method (CPM) using forward pass (earliest start/finish) and backward pass (latest start/finish) to calculate slack and identify zero-slack critical path tasks.
- **Schedule Engine (`app/engines/schedule/`)**:
  - `ScheduleEngine`: Forward-pass scheduling assigning concrete `planned_start` and `planned_end` datetimes respecting dependency order and lag.
  - `ScheduleFeasibilityChecker`: Validates schedule fits within event start/end window, computing buffer minutes.
  - `ScheduleAdjuster`: Propagates delays downstream through dependency graph, shifting dependent successors while leaving independent tasks unaffected.
- **Budget Engine (`app/engines/budget/`)**:
  - `BudgetCalculator`: Exact `Decimal` arithmetic computing estimated, actual, committed, and remaining totals, per-category breakdown, variance, and utilization percentage.
  - `BudgetValidator`: Detects total estimated and actual overspend, as well as per-category spending cap violations.
- **API Routes**:
  - `POST /api/events/{event_id}/schedule/compute`: Computes and persists task schedule and critical path.
  - `GET /api/events/{event_id}/schedule`: Retrieves schedule with feasibility and critical path.
  - `GET /api/events/{event_id}/budget/summary`: Aggregated budget summary with variance.
  - `GET /api/events/{event_id}/budget/validate`: Validates budget against total ceiling.

### 3. Phase 6: Live State Engine
- **State Engines (`app/engines/state/`)**:
  - `EventStateMachine`: Validates and enforces lifecycle transitions: `DRAFT → SPECIFIED → PLANNED → LIVE → CONCLUDED`, rejects invalid transitions.
  - `TransitionValidator`: Pre-flight readiness checks for go-live (planned tasks scheduled, none failed/cancelled) and conclude (no active tasks).
  - `DeviationDetector`: Compares actual vs planned start/finish times (`LATE_START`, `LATE_FINISH`, `EARLY_FINISH`) and actual vs estimated budget spend.
- **Service (`app/services/live_state_service.py`)**:
  - `LiveStateService`:
    - `go_live`: Validates readiness, transitions event to `LIVE`, and activates root tasks (`PENDING → READY`).
    - `update_task_status`: Progresses tasks (`READY → IN_PROGRESS → COMPLETED`), records actual start/end datetimes, records transitions, and cascades `READY` status to downstream successor tasks.
    - `get_live_state`: Aggregates operational snapshot, progress percentage, task breakdown, schedule deviations, and budget deviation.
    - `conclude_event`: Concludes event after ensuring all tasks are finished.
- **API (`app/api/routes/live.py`)**:
  - `POST /api/events/{event_id}/go-live`: Transitions event to LIVE.
  - `GET /api/events/{event_id}/live-state`: Retrieves operational snapshot.
  - `PUT /api/events/{event_id}/tasks/{task_id}/status`: Updates task status and timing.
  - `POST /api/events/{event_id}/conclude`: Concludes event.

### 4. Database Migrations
- `0003_phase456_engines_and_live_state.py`:
  - `events.lifecycle_state`: Lifecycle tracking (`DRAFT`, `SPECIFIED`, `PLANNED`, `LIVE`, `CONCLUDED`, `CANCELLED`).
  - `tasks`: `key`, `duration_minutes`, `slack_minutes`, `is_critical_path`, `phase`, `required_provider_category`.
  - `task_dependencies.lag_minutes`: Delay between predecessor finish and successor start.
  - `resources.allocated_task_id`: Task-level resource association.
  - `state_transitions`: Audit table tracking entity transitions across lifecycle and operational states.

### 5. Verification Results
- **Full Test Suite**: PASS (126/126 tests passing).
- **Alembic Migrations**: PASS (0001 -> 0002 -> 0003 upgrade and downgrade cycle passing).
- **FastAPI Startup & Routes**: PASS (All routes mounted cleanly under `/api` prefix).
- **Health**: PASS (`/health` returns HTTP 200).
- **Deterministic**: Zero LLM, zero LangGraph, zero external APIs used in calculation engines.

---

## Next Phase
**NEXT PHASE = PHASE 7 — INCIDENT → IMPACT → RISK**

