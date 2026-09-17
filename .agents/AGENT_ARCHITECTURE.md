# Agent Architecture: EVENTRA

## The "One Agent" Principle
EVENTRA uses **ONE unified Event Operations Agent**.

It explicitly rejects the "ten-agent architecture" pattern (e.g. separate Planning Agent, Recovery Agent, Budget Agent, Vendor Agent, Venue Agent). Multiple uncoordinated LLM agents introduce state synchronization chaos, conflicting actions, and unbounded token usage. 

A single orchestrating agent maintains complete contextual awareness of the event state and calls deterministic domain tools.

---

## Agent Operational Loop

```text
OBSERVE
  ↓
INTERPRET
  ↓
INVESTIGATE
  ↓
SELECT TOOL
  ↓
RE-EVALUATE
  ↓
GENERATE OPTIONS
  ↓
VALIDATE
  ↓
DECIDE
  ↓
ACT
  ↓
VERIFY
  ↓
UPDATED STATE
  ↺
```

---

## Division of Responsibilities

The boundary between probabilistic reasoning and deterministic calculation is absolute:

| Agent Responsibilities (Probabilistic Reasoning) | Deterministic Engine Responsibilities (Mathematical Truth) |
|---|---|
| Interpret natural language event prompts and reports | Calculate budget arithmetic, totals, variances, and line-item sums |
| Identify missing or ambiguous operational information | Verify resource quantities and unit balance |
| Investigate discrepancies by querying operational tools | Build and traverse the task dependency Directed Acyclic Graph (DAG) |
| Select appropriate domain tools based on situational context | Compute critical path, earliest/latest start times, and slack buffers |
| Reason over competing qualitative trade-offs | Verify vendor and venue calendar availability |
| Formulate viable recovery strategies and narratives | Enforce hard operational deadlines and time curfews |
| Decide the appropriate next action (escalate vs. dispatch) | Evaluate physical constraints (venue capacity vs. guest count) |
| Compose human-readable escalation notices and justifications | Validate mathematical feasibility of proposed recovery plans |
| Adapt strategy when execution state transitions or fails | Execute authoritative database state transitions |

---

## Tool Invocation Pattern

The Agent **never** calculates authoritative figures or directly mutates the database. It interacts solely through strongly-typed deterministic tools:

```text
               ┌────────────────────────┐
               │ Event Operations Agent │
               │     (LangGraph/LLM)    │
               └───────────┬────────────┘
                           │ Invokes Tool Call
                           ▼
               ┌────────────────────────┐
               │    Deterministic Tool  │
               │ (agent/tools/*_tools)  │
               └───────────┬────────────┘
                           │ Calls Domain Service
                           ▼
               ┌────────────────────────┐
               │  Deterministic Engine  │
               │  (services/*_service)  │
               └───────────┬────────────┘
                           │ Queries/Mutates
                           ▼
               ┌────────────────────────┐
               │       PostgreSQL       │
               │  (Authoritative State) │
               └────────────────────────┘
```

---

## Standard Agent Toolkits

The single Event Operations Agent is provided with distinct toolkits:
1. `specification_tools`: Parse requirements, validate guest count against capacity, identify missing constraints.
2. `venue_tools`: Query matching venues, compute driving distances and travel times via maps integration.
3. `vendor_tools`: Filter provider catalog by operational category, check availability, request quotes.
4. `dependency_tools`: Run topological sort, identify critical path tasks, calculate slack minutes.
5. `incident_tools`: Log reported incidents, query active disruptions, flag threatened objectives.
6. `impact_tools`: Execute dependency graph traversal to calculate downstream delay propagation.
7. `recovery_tools`: Generate re-sequencing options, test feasibility of vendor substitutions against budget and timeline.
8. `approval_tools`: Check authorization policy, create pending approval tickets for human sign-off.
9. `action_tools`: Dispatch pre-approved operational updates, update task progression state.
10. `verification_tools`: Query telemetry, poll vendor confirmation webhooks, record verification evidence.
