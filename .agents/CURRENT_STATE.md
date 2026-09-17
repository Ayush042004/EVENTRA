# Current Development State: EVENTRA

This is a living status document tracking the active engineering state of EVENTRA.

---

## Overall Status
**STATUS:** Phase 2 Complete — Event Specification & Domain Intelligence implemented and verified.

**CURRENT PHASE:** PHASE 2 COMPLETE

**NEXT PHASE:** PHASE 3 — VENUE + PROVIDER NETWORK

---

## Completed

### Phase 0 & Scaffolding
- [x] Product architecture & core operational loop defined (`.agents/PROJECT_CONTEXT.md`, `ARCHITECTURE.md`)
- [x] MVP feature taxonomy and architectural homes finalized (`.agents/FEATURE_SCOPE.md`)
- [x] 25 Non-negotiable engineering rules codified (`.agents/ENGINEERING_RULES.md`)
- [x] 20-Phase implementation roadmap sequenced (`.agents/DEVELOPMENT_ORDER.md`)
- [x] Authoritative relational entity models & graph traversal boundaries specified (`.agents/DATA_MODEL.md`)
- [x] Single Event Operations Agent architecture & tool boundaries established (`.agents/AGENT_ARCHITECTURE.md`)
- [x] Integration adapter boundaries and isolation guidelines documented (`.agents/INTEGRATIONS.md`)
- [x] Workflow-centric PWA route structure & offline policy documented (`.agents/UI_PWA_GUIDELINES.md`)
- [x] Server-side RBAC and autonomous execution guardrails codified (`.agents/SECURITY_RBAC.md`)
- [x] Multi-tier testing strategy & scenario pipeline defined (`.agents/TESTING.md`)
- [x] Authentic simulation test scenarios specified (`.agents/DEMO_SCENARIOS.md`)
- [x] AI Context Layer (`.agents/` directory) fully initialized and validated
- [x] Monorepo root configuration (`package.json`, `pnpm-workspace.yaml`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`)
- [x] Shared packages created (`packages/contracts/`, `packages/config/`)
- [x] Frontend PWA folder structure and stubs established (`apps/web/`)
- [x] Backend architecture scaffolded (`apps/api/`: models, schemas, routes, engines, services, agent, domains, integrations, seeds, tests)

### Phase 2: Event Specification + Domain Intelligence
- [x] Domain Architecture Implemented:
  - Base Domain contract (`BaseEventDomain` in `apps/api/app/domains/base.py`) defining `baseline_requirements()`, `baseline_tasks()`, `baseline_dependencies()`, and `provider_categories()`.
  - Domain Typed Primitives (`apps/api/app/domains/types.py`): `RequirementDefinition`, `TaskDefinition`, `DependencyDefinition`, `ProviderCategoryDefinition`, `EventType`, `DependencyType`, `ObjectivePriority`, `EventStatus`.
  - Domain Registry (`apps/api/app/domains/registry.py`): Central factory resolving `EventType -> BaseEventDomain` with `UnsupportedEventTypeException` and extensible registration.
- [x] Specialized Event Domain Implementations:
  - **WeddingDomain** (`apps/api/app/domains/wedding/`): 11 baseline requirements, 11 baseline tasks, 13 operational dependencies, and 8 provider categories.
  - **CollegeFestDomain** (`apps/api/app/domains/college_fest/`): 10 baseline requirements, 11 baseline tasks, 15 operational dependencies, and 10 provider categories.
  - **ConferenceDomain** (`apps/api/app/domains/conference/`): 11 baseline requirements, 12 baseline tasks, 17 operational dependencies, and 8 provider categories.
- [x] Normalized Event Specification Schema & Service:
  - `EventSpecification`, `ConstraintDefinition`, `ObjectiveDefinition` in `apps/api/app/schemas/specification.py`.
  - `SpecificationService` in `apps/api/app/services/specification_service.py` synthesizing domain baselines with event-specific configuration, requirement overrides/additions, constraints, and objectives.
- [x] Deterministic Validation:
  - Date sanity checks (`end_time > start_time`).
  - Guest count scalar non-negative check.
  - Dependency graph integrity (every predecessor and successor exists in baseline tasks).
  - Rejection of self-dependencies and duplicate dependency edges.
  - Structural constraint and objective validation.
  - 100% deterministic (zero random numbers, zero timestamps inside baselines, zero LLM calls).
- [x] API Specification Preview / Read Endpoints:
  - `GET /api/events/{event_id}/specification` (read preview from demo/database state).
  - `POST /api/events/specification/preview` (read preview without mutation).
- [x] Verification & Tests:
  - Unit tests for DomainRegistry, domain outputs, dependency validation, SpecificationService, determinism, and future extensibility.
  - Integration tests for specification endpoints.
  - 41/41 tests passing with `pytest`.
  - Bytecode compilation passed with `compileall`.
  - FastAPI application startup verified (27 routes).

---

## Known Limitations
- Planning engine (Phase 4 / Phase 6) is not yet implemented; tasks have nominal duration/phase metadata but no scheduled timestamps or assigned vendor instances.
- Concrete database persistence for compiled Task and Dependency entities will occur in downstream phases (Phase 4/6).

---

## Next Steps
1. Proceed to **PHASE 3 — VENUE + PROVIDER NETWORK**
2. Venue schema, geospatial filtering, driving distance & ETA integration.
3. Provider network catalog and service assignment bindings.
