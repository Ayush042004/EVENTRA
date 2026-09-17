# System Architecture: EVENTRA

## Canonical Architecture Pipeline

```text
EVENT
  ↓
EVENT SPECIFICATION
  ↓
PLAN
  ↓
RUN
  ↓
CHANGE / INCIDENT
  ↓
IMPACT
  ↓
RISK
  ↓
RECOVERY
  ↓
AGENT
  ↓
APPROVAL
  ↓
ACTION
  ↓
VERIFICATION
  ↓
UPDATED EVENT STATE
```

---

## Architectural Zones

The system is partitioned into three major architectural zones:

### 1. Domain Zone
Contains all core business entities, domain services, state machines, and deterministic calculation engines.
- **Event:** Root aggregate managing lifecycle (Draft, Planned, Live, Incident, Emergency, Concluded).
- **Planning:** Specification compilation, venue selection, task scheduling, vendor matching, and budget allocation.
- **Execution:** Live state monitoring, schedule tracking, task progression, check-in, and milestone tracking.
- **Adaptation:** Incident detection, impact analysis (graph traversal), risk assessment, and recovery strategy generation.
- **Action:** Autonomy policy evaluation, approval routing, task dispatch, vendor reallocation, and re-planning.
- **Verification:** Action confirmation, telemetry checks, provider response parsing, and state reconciliation.

### 2. Cross-Cutting Zone
Universal capabilities supporting all domain zones with zero business-rule leaking.
- **Identity & Auth:** User authentication, session management, and credential exchange.
- **Permissions (RBAC):** Server-side role resolution and scoped action-level authorization.
- **Approval Engine:** Human-in-the-loop workflows, threshold checks, signature/acknowledgment collection.
- **Audit Logging:** Tamper-evident recording of every state transition, agent decision, and manual override.
- **Notification Engine:** Event alerting, multi-channel dispatch, recipient fan-out, and delivery state tracking.

### 3. Infrastructure Zone
Hardware, persistence, external gateways, and platform runtime drivers.
- **Database:** PostgreSQL as the single authoritative relational data store.
- **LLM Integrations:** Isolated client adapters for external model APIs with fallback handling.
- **Maps & Geolocation:** External spatial lookups, venue geocoding, driving ETA, and distance matrix services.
- **WhatsApp Gateway:** Secure webhook receiver, message template dispatcher, and conversational state parser.
- **External APIs:** Provider network endpoints, inventory systems, weather feeds, and push gateways.

---

## Separation of Responsibilities

| Subsystem | Primary Role | Architectural Rule |
|---|---|---|
| **Backend** | Authoritative Source of Truth | Enforces all state machines, invariants, database writes, and RBAC rules. Never permits frontend or agent direct DB mutations. |
| **Frontend (PWA)** | User Interface & Operational Control | Presents live event state, captures user intent, queues approvals, and renders operational dashboards. Contains zero calculation logic. |
| **Agent** | Context Reasoning & Orchestration | Reads structured state, detects nuances, selects operational tools, constructs recovery options, and escalates ambiguities. Never calculates math/dates directly. |
| **Deterministic Engines** | Feasibility & Calculation Engine | Traverses dependency DAGs, computes critical paths, checks budgets, validates venue capacity, and proves mathematical feasibility. |
| **Integrations** | External Boundary Isolation | Encapsulates third-party protocols, schemas, rate limits, and network errors behind clean typed internal interfaces. |

---

## Data & Control Flow Principles

1. **State Mutation Boundary:**  
   UI and Agent NEVER write directly to the database. All state mutations pass through backend domain services that validate invariants, enforce permissions, and emit audit logs.
2. **Deterministic Pre-flight & Post-flight:**  
   Whenever the Agent formulates an action or recovery plan, that plan must be submitted to the deterministic engine (e.g., dependency traversal or budget check) to verify mathematical feasibility before any approval is requested or action executed.
3. **Audit Trail:**  
   Every state change produces an immutable `StateTransition` and an `Audit` entry recording the causal actor (user ID or agent ID), previous state, new state, timestamp, and rationale.
