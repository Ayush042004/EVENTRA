# Current Development State: EVENTRA

This is a living status document tracking the active engineering state of EVENTRA.

---

## Overall Status
**STATUS:** PHASE 1 COMPLETE

**CURRENT PHASE:** PHASE 1 — Foundational Relational Domain Model (Completed)

---

## Phase 1 Implementation Details

### 1. Foundational Domain Entities Implemented
- **User**: Foundational identity model (`id`, `name`, `email` [unique, indexed], `created_at`, `updated_at`, `owned_events`, `memberships`).
- **Event**: Authoritative root aggregate (`id`, `owner_id` [FK `users.id`], `name`, `description`, `event_type`, `location`, `start_datetime`, `end_datetime`, `guest_count`, `state` [NORMAL, AT_RISK, CRITICAL, EMERGENCY, RECOVERY], `total_budget`, `currency`, `created_at`, `updated_at`).
  - Strict deliberate cascade lifecycles defined for child entities.
- **EventMember**: Scoped event membership (`id`, `event_id` [FK `events.id`], `user_id` [FK `users.id`], `role` [MAIN_ORGANIZER, EVENT_MANAGER, COLLABORATOR, VENDOR, VIEWER], `role_id` [FK `roles.id`], `created_at`, `updated_at`, `UniqueConstraint(event_id, user_id)`).
- **Role & Permission**: Controlled RBAC foundation (`roles`, `permissions`, and `role_permissions` association table supporting categories VIEW, MINOR_CHANGE, CRITICAL_CHANGE, APPROVE).
- **Requirement**: Event requirement model (`id`, `event_id`, `type`, `name`, `description`, `value` [JSON], `required` [boolean], `created_at`, `updated_at`).
- **Constraint**: Hard/soft constraint model (`id`, `event_id`, `type`, `name`, `description`, `value` [JSON], `severity` [HARD, SOFT], `created_at`, `updated_at`).
- **Objective**: Event objective model (`id`, `event_id`, `type`, `name`, `description`, `priority` [CRITICAL, HIGH, MEDIUM, LOW, FLEXIBLE], `target_value` [JSON], `created_at`, `updated_at`).
- **Venue**: Foundational venue representation with physical capacity, location, rates, and amenities.
- **Vendor / Provider**: Provider catalog entity with operational category, location, contact, and rates.
- **VendorAssignment**: Binding vendor to event with status and agreed cost.
- **Task**: Operational task entity (`id`, `event_id`, `name`, `description`, `status`, `priority`, `planned_start`, `planned_end`, `actual_start`, `actual_end`, `created_at`, `updated_at`).
- **TaskDependency**: Adjacency graph edges (`id`, `event_id`, `predecessor_task_id`, `successor_task_id`, `dependency_type`, `created_at`, `UniqueConstraint(predecessor, successor)`, `CheckConstraint(predecessor != successor)`, Python validator preventing self-dependencies).
- **Resource**: Physical and logistical resources (`id`, `event_id`, `name`, `type`, `quantity`, `unit`, `status`, `created_at`, `updated_at`).
- **BudgetItem**: Financial tracking using exact `Decimal`/`Numeric(12, 2)` monetary semantics (`id`, `event_id`, `name`, `category`, `estimated_amount`, `actual_amount`, `currency`, `status`, `created_at`, `updated_at`).

### 2. Database Migrations
- **Migration Name**: `0002_phase1_foundational_domain_model.py` (Revision ID: `0002_phase1`, Revises: `0001_phase3`).
- Generates clean, transactional DDL for PostgreSQL and batch-mode SQLite.
- Supports complete symmetric upgrade and downgrade.

### 3. Pydantic Contracts
- Clean request/response schemas in `app/schemas/`:
  - `UserCreate`, `UserResponse`, `UserUpdate`
  - `EventCreate`, `EventResponse`, `EventUpdate`
  - `EventMemberCreate`, `EventMemberResponse`
  - `RoleCreate`, `RoleResponse`, `PermissionResponse`
  - `RequirementCreate`, `RequirementResponse`
  - `ConstraintCreate`, `ConstraintResponse`
  - `ObjectiveCreate`, `ObjectiveResponse`
  - `TaskCreate`, `TaskResponse`, `TaskDependencyCreate`, `TaskDependencyResponse`
  - `ResourceCreate`, `ResourceResponse`
  - `BudgetItemCreate`, `BudgetItemResponse`

### 4. Minimal Persistence Service & API Endpoints
- **Service**: `EventService` in `app/services/event_service.py` providing CRUD operations and invariant enforcement for all Phase 1 domain entities without implementing premature business engines.
- **API Endpoints**:
  - `POST /api/events`: Create event with authoritative owner.
  - `GET /api/events/{event_id}`: Retrieve event details.
  - `POST /api/events/{event_id}/members`: Add collaborator to event.
  - `GET /api/events/{event_id}/members`: List event members.

### 5. Tests Added
- `tests/test_phase1_domain.py`: 13 comprehensive model integrity tests:
  - User creation and unique email constraint.
  - Event ownership and owner relationship.
  - Event membership and duplicate membership prevention.
  - Role and permission M2M association.
  - Requirements, Constraints, Objectives event-parenting.
  - Task creation and event binding.
  - TaskDependency integrity: self-dependency rejection and duplicate edge prevention.
  - Resource ownership and capacity tracking.
  - BudgetItem monetary Decimal correctness without float distortion.
  - VendorAssignment dual relationship loading.
  - Cascade deletion lifecycle (deleting event cleans up all child elements).
- `tests/test_migration.py`: Automated upgrade -> downgrade -> re-upgrade cycle testing against live SQLite schema engine.
- `tests/integration/api/test_events_api.py`: Integration testing for event creation, membership assignment, duplicate rejection, and non-existent owner rejection.
- `tests/unit/services/test_event_service.py`: Service-level lifecycle test across all domain entities.

### 6. Verification Results
- **Migrations**: PASS (`alembic upgrade head --sql` dry-run valid PostgreSQL DDL; upgrade, downgrade, re-upgrade cycle PASS).
- **Tests**: PASS (46/46 tests passing).
- **Startup**: PASS (FastAPI application starts up cleanly with lifespan hooks).
- **Health**: PASS (`/health` returns HTTP 200 `healthy`).

### 7. Known Limitations
- Authorization is foundational (ownership, membership, role enum); dynamic impact-aware permission evaluation is deferred to Phase 9.
- Domain engines (planning, dependency DAG cycle detection, schedule algebra, recovery) are deliberately not implemented per Phase 1 scope boundaries.

---

## Next Phase
**NEXT PHASE = PHASE 2 — EVENT SPECIFICATION + DOMAIN INTELLIGENCE**
