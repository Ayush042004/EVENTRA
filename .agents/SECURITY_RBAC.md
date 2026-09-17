# Security & RBAC: EVENTRA

Authorization in EVENTRA is enforced strictly on the backend. Frontend UI visibility toggles are cosmetic conveniences and are never trusted for security.

---

## Canonical Roles

Each `EventMember` has an assigned role within the scope of a specific `Event`:

| Role | Operational Scope | Default Capabilities |
|---|---|---|
| **Main Organizer** | Full Event Owner | Complete administrative, financial, and operational control. Final approval on all emergency and budget escalations. |
| **Event Manager** | Operational Lead | Can manage tasks, assign vendors, resolve non-emergency incidents, and execute pre-approved recoveries. |
| **Collaborator / Family** | Task Collaborator | Can view full plan, mark assigned tasks completed, log incidents, and add operational notes. |
| **Vendor** | External Provider | Restricted view: sees only assigned tasks, schedule windows, venue access details, and dispatch instructions. |
| **Viewer** | Read-Only Stakeholder | Can view timeline, read-only status dashboards, and non-sensitive operational summaries. |

---

## Action Impact Levels

Every system action belongs to one of three impact levels:

```text
VIEW
  └── Read-only access to state, logs, schedules, and metrics.

MINOR CHANGE
  └── Low-risk state changes (e.g. marking a non-critical task in-progress, updating a task note, reallocating standard buffer time).
  └── Can be executed immediately by Event Managers or autonomous agent routines if pre-cleared.

CRITICAL CHANGE
  └── High-risk operational changes (e.g. replacing a vendor, changing venue contract, modifying critical path, committing budget > $500, emergency state transition).
  └── Requires explicit pending Approval sign-off from the Main Organizer.
```

---

## Authorization & Execution Flow

```text
USER
  ↓
IDENTITY (Authentication & Token Verification)
  ↓
EVENT (Scoped Event Membership Check)
  ↓
ROLE (Resolve Role: Main Organizer, Event Manager, etc.)
  ↓
PERMISSION (Verify Permission Grant: e.g., task:reschedule)
  ↓
SCOPE (Ensure Target Resource belongs to Event)
  ↓
IMPACT (Classify Impact Level: VIEW, MINOR, CRITICAL)
  ↓
AUTHORIZATION (Check Policy Matrix & Spending/Time Thresholds)
  ↓
EXECUTE OR APPROVAL (Dispatch Immediately OR Create Pending Approval)
  ↓
VERIFY (Confirm Execution via Verification Engine)
  ↓
AUDIT (Append Immutable Record to Audit Log)
```

---

## Autonomous Operations Guardrails

When the single Event Operations Agent proposes or executes an action, it must strictly obey the exact same security and policy constraints as a human user:

1. **Permission Check:** Agent actions are executed on behalf of the system or an authorizing user; permissions must be validated server-side.
2. **Approval Policy:** Autonomous execution is strictly confined to `MINOR CHANGE` tiers within pre-configured thresholds.
3. **Feasibility Validation:** The action must pass deterministic feasibility checks before execution.
4. **Spending Limits:** Autonomous spend allocations cannot exceed the pre-authorized budget variance cap (e.g., max $200 buffer without human sign-off).
5. **Schedule Limits:** Autonomous schedule shifts cannot compromise downstream critical path buffers.
6. **Critical Objective Protection:** Any action that threatens a marked `CRITICAL` event objective immediately halts autonomy and triggers human escalation.
7. **Verification & Audit:** Every autonomous action must specify verification criteria and log causal entries in `Audit` and `StateTransition` tables.
