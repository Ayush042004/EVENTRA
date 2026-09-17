# Data Model: EVENTRA

## Storage Authority
- **PostgreSQL** is the sole authoritative data store.
- **Dependency Graphs:** Stored relationally via adjacency records (`Dependency` table with `predecessor_id`, `successor_id`, `dependency_type`, `lag_minutes`). Graph traversal (topological sort, critical path calculation, cycle detection) is executed deterministically in Python memory or recursive CTEs.
- **Do NOT introduce Neo4j** or any graph database for the MVP.

---

## Membership & Access Relationship

```text
USER
  └── EVENT_MEMBER (user_id, event_id, role_id)
        └── EVENT
```

Users interact with Events strictly through scoped `EventMember` bindings associated with a defined `Role` containing explicit `Permission` grants.

---

## Event Aggregate Tree

```text
EVENT
├── requirements       (Capacity, power, catering style, sensory needs)
├── constraints        (Hard time limits, quiet hours, budget ceiling)
├── objectives         (Critical must-haves vs. flexible preferences)
├── venue              (Selected venue, facilities, zones, capacity, location)
├── tasks              (Work breakdown units, planned/actual start/end, status)
├── dependencies       (Directed edges connecting predecessor and successor tasks)
├── resources          (Equipment, physical spaces, technical kits)
├── vendors            (External service providers in the network catalog)
├── assignments        (Vendor-to-task bindings, contracts, status)
├── budget             (Allocated, committed, and spent line items)
├── schedule           (Active timeline, baseline snapshots, milestones)
├── incidents          (Disruptions, anomalies, severity, status)
├── recovery           (Recovery proposals, impact mitigation options, chosen plan)
├── approvals          (Pending and resolved sign-offs for high-impact actions)
├── notifications      (Dispatched alerts, recipient state, delivery channel)
└── state history      (StateTransitions and immutable Audit log records)
```

---

## Canonical Entity Definitions

### 1. User
- `id: UUID (PK)`
- `email: String (Unique)`
- `full_name: String`
- `phone_number: String`
- `created_at: DateTime`

### 2. Event
- `id: UUID (PK)`
- `title: String`
- `description: String`
- `status: Enum` (`DRAFT`, `SPECIFIED`, `PLANNED`, `LIVE`, `INCIDENT`, `EMERGENCY`, `CONCLUDED`, `CANCELLED`)
- `start_time: DateTime`
- `end_time: DateTime`
- `guest_count: Integer` (Aggregate scalar requirement; NOT an attendee list)
- `total_budget: Decimal`
- `currency: String`
- `created_by: UUID (FK -> User)`
- `created_at: DateTime`, `updated_at: DateTime`

### 3. EventMember & Role & Permission
- **EventMember:** `id: UUID`, `event_id: UUID (FK)`, `user_id: UUID (FK)`, `role_id: UUID (FK)`, `created_at: DateTime`
- **Role:** `id: UUID`, `name: String` (`MAIN_ORGANIZER`, `EVENT_MANAGER`, `COLLABORATOR`, `VENDOR`, `VIEWER`)
- **Permission:** `id: UUID`, `code: String` (`event:view`, `task:update`, `recovery:approve`, `budget:override`, etc.)

### 4. Specification: Requirement, Constraint, Objective
- **Requirement:** `id: UUID`, `event_id: UUID (FK)`, `category: String`, `key: String`, `value: JSONB`, `is_mandatory: Boolean`
- **Constraint:** `id: UUID`, `event_id: UUID (FK)`, `constraint_type: String` (`TIME_WINDOW`, `BUDGET_CAP`, `NOISE_CURFEW`), `parameters: JSONB`
- **Objective:** `id: UUID`, `event_id: UUID (FK)`, `title: String`, `priority: Enum` (`CRITICAL`, `HIGH`, `MEDIUM`, `FLEXIBLE`), `is_threatened: Boolean`

### 5. Venue
- `id: UUID (PK)`
- `name: String`
- `address: String`
- `latitude: Float`, `longitude: Float`
- `max_capacity: Integer`
- `hourly_rate: Decimal`
- `facilities: JSONB` (Power, sound, loading dock, parking)
- `availability_calendar: JSONB`

### 6. Task, Dependency & Resource
- **Task:** `id: UUID (PK)`, `event_id: UUID (FK)`, `title: String`, `description: String`, `status: Enum` (`PENDING`, `READY`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `FAILED`), `planned_start: DateTime`, `planned_end: DateTime`, `actual_start: DateTime`, `actual_end: DateTime`, `duration_minutes: Integer`, `slack_minutes: Integer`, `is_critical_path: Boolean`
- **Dependency:** `id: UUID (PK)`, `event_id: UUID (FK)`, `predecessor_id: UUID (FK -> Task)`, `successor_id: UUID (FK -> Task)`, `dependency_type: Enum` (`FINISH_TO_START`, `START_TO_START`), `lag_minutes: Integer`
- **Resource:** `id: UUID (PK)`, `event_id: UUID (FK)`, `name: String`, `quantity: Integer`, `unit: String`, `allocated_task_id: UUID (FK -> Task, Nullable)`

### 7. Vendor & VendorAssignment
- **Vendor:** `id: UUID (PK)`, `company_name: String`, `contact_name: String`, `contact_phone: String`, `category: String` (`CATERING`, `AV`, `DECOR`, `SECURITY`), `hourly_rate: Decimal`, `rating: Float`
- **VendorAssignment:** `id: UUID (PK)`, `event_id: UUID (FK)`, `vendor_id: UUID (FK)`, `task_id: UUID (FK -> Task)`, `status: Enum` (`REQUESTED`, `CONFIRMED`, `EN_ROUTE`, `ON_SITE`, `COMPLETED`, `NO_SHOW`, `CANCELLED`), `agreed_fee: Decimal`

### 8. Budget & Procurement
- **Budget:** `id: UUID (PK)`, `event_id: UUID (FK)`, `allocated_amount: Decimal`, `committed_amount: Decimal`, `spent_amount: Decimal`
- **Procurement:** `id: UUID (PK)`, `event_id: UUID (FK)`, `item_name: String`, `quantity: Integer`, `estimated_cost: Decimal`, `vendor_id: UUID (FK -> Vendor, Nullable)`, `status: Enum` (`DRAFT`, `PENDING_APPROVAL`, `ORDERED`, `RECEIVED`, `CANCELLED`)

### 9. Incident & Recovery
- **Incident:** `id: UUID (PK)`, `event_id: UUID (FK)`, `title: String`, `description: String`, `reported_by: UUID (FK -> User, Nullable)`, `severity: Enum` (`LOW`, `MEDIUM`, `HIGH`, `EMERGENCY`), `status: Enum` (`DETECTED`, `ANALYZING`, `RECOVERY_PROPOSED`, `RECOVERING`, `RESOLVED`), `affected_task_ids: JSONB`, `created_at: DateTime`
- **Recovery:** `id: UUID (PK)`, `incident_id: UUID (FK)`, `strategy_type: Enum` (`RESEQUENCE`, `SUBSTITUTE_VENDOR`, `REALLOCATE_RESOURCE`, `SCOPE_SHED`), `details: JSONB`, `cost_impact: Decimal`, `delay_impact_minutes: Integer`, `is_selected: Boolean`

### 10. Approval & Verification
- **Approval:** `id: UUID (PK)`, `event_id: UUID (FK)`, `recovery_id: UUID (FK, Nullable)`, `action_type: String`, `impact_level: Enum` (`MINOR`, `CRITICAL`), `requested_by: String` (`AGENT`, `USER`), `approver_id: UUID (FK -> User, Nullable)`, `status: Enum` (`PENDING`, `APPROVED`, `REJECTED`), `created_at: DateTime`, `resolved_at: DateTime`
- **Verification:** `id: UUID (PK)`, `event_id: UUID (FK)`, `action_id: String`, `verification_type: Enum` (`PROVIDER_CONFIRMATION`, `SUPERVISOR_CHECKOFF`, `TELEMETRY`), `is_verified: Boolean`, `verified_at: DateTime`, `evidence: JSONB`

### 11. Notification, Audit & StateTransition
- **Notification:** `id: UUID (PK)`, `event_id: UUID (FK)`, `recipient_user_id: UUID (FK)`, `channel: Enum` (`PUSH`, `IN_APP`, `WHATSAPP`), `message: String`, `sent_at: DateTime`, `read_at: DateTime`
- **Audit:** `id: UUID (PK)`, `event_id: UUID (FK)`, `actor_id: String`, `actor_type: Enum` (`USER`, `AGENT`, `SYSTEM`), `action: String`, `payload: JSONB`, `created_at: DateTime`
- **StateTransition:** `id: UUID (PK)`, `event_id: UUID (FK)`, `entity_type: String`, `entity_id: UUID`, `previous_state: String`, `new_state: String`, `reason: String`, `transitioned_at: DateTime`
