# Project Context: EVENTRA

## Project Name
**EVENTRA**

## Description
EVENTRA is an **Adaptive Event Operations platform**.

Unlike conventional event planning tools that treat plans as static checklists, EVENTRA maintains a living, dependency-aware representation of an event. When disruptions occur in the real world (delays, cancellations, supply chain breaks, venue issues), EVENTRA detects deviations, evaluates the downstream blast radius, computes feasible recovery strategies, and coordinates verified execution.

---

## Core Promise

```text
PLAN THE EVENT.
RUN THE EVENT.
ADAPT WHEN REALITY CHANGES.
```

---

## Core Operational Loop

```text
PLAN
 ↓
RUN
 ↓
DETECT CHANGE
 ↓
UNDERSTAND
 ↓
IMPACT
 ↓
RISK
 ↓
RECOVER
 ↓
APPROVE
 ↓
ACT
 ↓
VERIFY
 ↓
UPDATED EVENT STATE
 ↺
```

Every disruption or state change passes through this disciplined cycle. State transitions are verified and recorded before returning to the active monitoring state.

---

## Core Architectural Principle

> **"The deterministic engine calculates what is feasible.**  
> **The agent decides what should happen next."**

- Deterministic engines calculate dates, time buffers, dependency graphs, budget sums, capacity, and invariant violations with mathematical certainty.
- The AI Agent reasons through ambiguity, negotiates trade-offs, evaluates strategic alternatives, and coordinates actions through explicit tools.

---

## What EVENTRA Is NOT

EVENTRA explicitly avoids the following patterns and scopes:

- **NOT a generic chatbot:** It is not an ungrounded conversational assistant that guesses or hallucinates schedules and budgets.
- **NOT an AI wrapper:** It does not merely wrap prompts around basic CRUD checklists.
- **NOT a ticketing platform:** It does not issue tickets, manage barcode scanners, or process box-office transactions.
- **NOT an attendee management platform:** It does not manage attendee invitations, RSVP tracking, badge printing, or attendee networking. (Guest count is accepted only as a capacity/resource sizing requirement).
- **NOT a full Cvent replacement:** It avoids sprawling legacy enterprise registration and convention marketing bloat.
- **NOT a marketplace:** It does not host open merchant storefronts or consumer-to-business bidding wars.
- **NOT an autonomous payment system:** It does not independently trigger irreversible bank transfers or credit card charges without human financial controls.

---

## The Core Differentiators

1. **Persistent Live Event State:** A single authoritative state machine capturing tasks, assignments, locations, constraints, and dependencies.
2. **Dependency-Aware Impact Analysis:** Real-time graph traversal that reveals second- and third-order ripple effects across timeline, vendors, and budget.
3. **Adaptive Recovery:** Automated formulation of viable recovery alternatives evaluated against hard physical and temporal constraints.
4. **Human-Controlled / Autonomous Execution:** Flexible autonomy spectrum ranging from strict human approval for high-impact decisions to automated workflows for pre-cleared operations.
5. **Closed-Loop Verification:** Operational actions are validated via external checks, telemetry, or provider confirmations before being marked resolved.
