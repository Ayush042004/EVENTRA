# EVENTRA Engineering Context (.agents/)

This directory serves as the persistent, authoritative engineering context and project memory for AI coding agents working on EVENTRA. It is NOT application code.

> **Rule for AI Agents:**  
> Before implementing or modifying any feature, the AI agent must read the relevant `.agents/` files.

---

## Directory Index

| File | Responsibility |
|---|---|
| [PROJECT_CONTEXT.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/PROJECT_CONTEXT.md) | Product context, core promise, operational loop, and non-goals. |
| [ARCHITECTURE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/ARCHITECTURE.md) | Canonical system architecture pipeline and structural zones. |
| [FEATURE_SCOPE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/FEATURE_SCOPE.md) | Authoritative taxonomy: KEEP, SPECIAL DOUBT, DOUBT, REMOVE, and module mapping. |
| [ENGINEERING_RULES.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/ENGINEERING_RULES.md) | 25 non-negotiable architectural and operational engineering rules. |
| [DEVELOPMENT_ORDER.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/DEVELOPMENT_ORDER.md) | Strict 20-phase dependency-ordered implementation sequence. |
| [DATA_MODEL.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/DATA_MODEL.md) | Canonical relational data model, entity graph, and PostgreSQL authority. |
| [AGENT_ARCHITECTURE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/AGENT_ARCHITECTURE.md) | Single Event Operations Agent architecture and deterministic vs. reasoning boundaries. |
| [INTEGRATIONS.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/INTEGRATIONS.md) | External API boundaries, adapter isolation patterns, and forbidden direct calls. |
| [UI_PWA_GUIDELINES.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/UI_PWA_GUIDELINES.md) | Frontend workflow routes, PWA priorities, and offline policy. |
| [SECURITY_RBAC.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/SECURITY_RBAC.md) | Server-side RBAC, action authorization tiers, and autonomous execution guardrails. |
| [TESTING.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/TESTING.md) | Unit, integration, and end-to-end operational scenario verification requirements. |
| [DEMO_SCENARIOS.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/DEMO_SCENARIOS.md) | Legitimate simulation scenarios (Vendor No-Show, Venue Issue, Resource Shortage). |
| [CURRENT_STATE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/CURRENT_STATE.md) | Living status tracker: current phase, completed work, active focus, and next steps. |

---

## AI Agent Working Protocol

Whenever an AI coding agent is tasked with implementing or changing functionality, it must follow this 10-step protocol:

1. **Step 1: Read Foundational Context**  
   Read [PROJECT_CONTEXT.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/PROJECT_CONTEXT.md), [FEATURE_SCOPE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/FEATURE_SCOPE.md), [ENGINEERING_RULES.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/ENGINEERING_RULES.md), and [CURRENT_STATE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/CURRENT_STATE.md).
2. **Step 2: Read Task-Specific Context**  
   - Architecture & Pipeline: [ARCHITECTURE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/ARCHITECTURE.md)
   - Schema & Entities: [DATA_MODEL.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/DATA_MODEL.md)
   - Agent & Tools: [AGENT_ARCHITECTURE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/AGENT_ARCHITECTURE.md)
   - Web / Mobile / PWA: [UI_PWA_GUIDELINES.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/UI_PWA_GUIDELINES.md)
   - Third-Party APIs: [INTEGRATIONS.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/INTEGRATIONS.md)
   - Roles & Permissions: [SECURITY_RBAC.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/SECURITY_RBAC.md)
   - Tests & Scenarios: [TESTING.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/TESTING.md) & [DEMO_SCENARIOS.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/DEMO_SCENARIOS.md)
3. **Step 3: Inspect Existing Codebase**  
   Verify current directories, files, and schemas before assuming absence or presence.
4. **Step 4: Determine What Already Exists**  
   Check for existing modules, utilities, and models to avoid duplicating logic.
5. **Step 5: Do Not Recreate Existing Functionality**  
   Reuse existing services, validation logic, and models.
6. **Step 6: Identify Dependencies**  
   Check [DEVELOPMENT_ORDER.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/DEVELOPMENT_ORDER.md). If a prerequisite layer does not exist, build or resolve the dependency first. Never skip ahead.
7. **Step 7: Implement Smallest Correct Change**  
   Keep changes modular, focused, and aligned with defined architecture boundaries.
8. **Step 8: Run Relevant Tests & Type Checks**  
   Execute unit, integration, or scenario tests and type verification.
9. **Step 9: Update CURRENT_STATE.md**  
   Record completed work, modified files, and updated roadmap state.
10. **Step 10: Report Findings & Actions**  
    Provide a clear summary covering: what changed, files created, files modified, tests run, remaining work, and architectural decisions.

---

## Context Priority

When guidance or instructions appear to conflict, resolve them using this strict hierarchy:

1. **Explicit current user instruction** (unless violating core architecture/engineering rules—in which case highlight the conflict explicitly)
2. **[FEATURE_SCOPE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/FEATURE_SCOPE.md)** (hard boundaries on KEEP vs. REMOVE)
3. **[ENGINEERING_RULES.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/ENGINEERING_RULES.md)** (non-negotiable constraints)
4. **[ARCHITECTURE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/ARCHITECTURE.md)** (system zones & data flow)
5. **[CURRENT_STATE.md](file:///C:/Users/Tridibesh%20Samantroy/OneDrive/Desktop/EVENTRA/.agents/CURRENT_STATE.md)** (operational reality)
6. **Individual implementation notes**

*Never silently resolve an architectural conflict. If an instruction directly contradicts a core rule, explicitly state the conflict to the user before proceeding.*
