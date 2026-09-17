# Feature Scope: EVENTRA

This document defines the strict, authoritative boundaries of what is built, deferred, or strictly excluded.

---

## 1. Feature Taxonomy

### KEEP (Core MVP Scope)
These features represent the essential, active development scope of EVENTRA:
1. **Event Setup:** Event initialization, base specification, budget targets, constraints, dates, guest-count requirement.
2. **Venue Discovery:** Location search, venue capacity & facility matching, driving distance, ETA, and availability filtering.
3. **Vendor / Provider Network:** Provider catalog, operational category matching, availability, cost models, and assignment.
4. **Event Planning:** Schedule synthesis, milestone breakdown, dependency mapping, and deterministic resource allocation.
5. **Live Command Center:** Real-time event execution dashboard, active task tracker, and state visualizer.
6. **Incident Detection:** Discrepancy intake, delay reports, supply failure alerts, and anomaly flagging.
7. **Impact Analysis:** Graph-based blast radius calculation assessing schedule slippage, blocked tasks, and cost changes.
8. **Risk Engine:** Quantitative assessment of incident severity, objective threat levels, and emergency escalation thresholds.
9. **Recovery Engine:** Deterministic alternative synthesis (re-sequencing, vendor swapping, buffer re-allocation).
10. **Human Approval:** Threshold-based human-in-the-loop review queues for high-impact or out-of-policy changes.
11. **Autonomous Operations:** Automated execution of pre-authorized, low-risk, verified operational adjustments.
12. **Procurement:** Generation of supply manifests, replacement orders, and operational resource reservation.
13. **Notifications:** Real-time push, in-app alerts, and critical banner updates for event stakeholders.
14. **Mobile / PWA:** Fast, responsive, installable mobile frontend optimized for on-the-ground operational control.
15. **Analytics:** Post-event and live operational metrics (budget variance, delay tracking, recovery response time).
16. **AI / Agent:** Single Event Operations Agent managing reasoning, tool selection, escalation, and orchestration.
17. **Real-World Integrations:** Maps/geocoding API, external provider APIs, and notification push services.
18. **Verification:** Closed-loop validation of actions against real-world telemetry, provider acknowledgments, or manual check-offs.

---

### SPECIAL DOUBT (Requires Deliberate Validation Before Building)
Features that add value but require external validation or careful boundary checks before MVP commitment:
- **WhatsApp Provider Communication:** Outbound/inbound messaging for vendor status checks. Requires twilio/meta credentials, webhook infrastructure, and template approvals. (Keep behind feature flags).
- **Audit & Trust:** Detailed cryptographic or immutable audit log tracing every automated decision. Basic database audit is kept; advanced trust proofs are deferred.

---

### DOUBT (Post-MVP Candidates)
Deferred until core operational loop is thoroughly verified:
- **Event Memory / Learning:** Cross-event organizational memory and preference embeddings.
- **Provider Performance / Historical Scoring:** Long-term reputation and historical reliability ratings across multiple events.
- **Email / SMS:** Legacy redundant channels unless push notifications or WhatsApp prove insufficient.

---

### REMOVE (Strictly Forbidden / Non-Goals)
The following must **NEVER** be introduced into EVENTRA:
- ❌ **Attendee Layer:** No attendee profiles, individual attendee records, or check-in scanners.
- ❌ **Attendance Tracking:** No individual seat assignments or personalized session check-ins.
- ❌ **RSVP Platform:** No guest invitations, RSVP links, or dietary surveys for individual attendees.
- ❌ **Ticketing:** No barcode generation, payment gateways for tickets, or box office integrations.
- ❌ **Social / Event Feed:** No attendee social networking, activity walls, photo galleries, or chat rooms.
- ❌ **Full Cvent Replacement:** No enterprise exhibition booth sales or multi-track conference agenda builders.
- ❌ **Generic Chatbot:** No free-form conversational bots answering arbitrary trivia outside operational event state.
- ❌ **Autonomous Payments:** No unattended financial transfers or credit card processing.
- ❌ **Ten-Agent Architecture:** No artificial proliferation of separate agents (Planning Agent, Budget Agent, etc.).

> **CRITICAL RULE ON GUEST COUNT:**  
> `guest_count` is permitted strictly as an aggregate integer requirement (e.g. `required_capacity: 150`) used by the deterministic engine to evaluate venue capacity, catering portions, or seating feasibility. It must NEVER spawn an attendee management subsystem or individual attendee entities.

---

## 2. Architectural Homes of Features

Every feature must reside in its designated architectural layers:

### Venue Discovery
- **Frontend:** `web/features/venue-discovery/`
- **API Routes:** `api/routes/venues.py`
- **Services:** `services/venue_service.py`
- **Models:** `models/venue.py`
- **Integrations:** `integrations/maps/`, `integrations/venues/`
- **Agent Tools:** `agent/tools/venue_tools.py`

### Event Setup & Specification
- **Frontend:** `web/features/event-setup/`
- **API Routes:** `api/routes/events.py`, `api/routes/specifications.py`
- **Services:** `services/event_service.py`, `services/specification_service.py`
- **Models:** `models/event.py`, `models/specification.py`, `models/requirement.py`, `models/constraint.py`
- **Agent Tools:** `agent/tools/specification_tools.py`

### Vendor / Provider Network & Procurement
- **Frontend:** `web/features/vendors/`, `web/features/procurement/`
- **API Routes:** `api/routes/vendors.py`, `api/routes/procurement.py`
- **Services:** `services/vendor_service.py`, `services/procurement_service.py`
- **Models:** `models/vendor.py`, `models/vendor_assignment.py`, `models/procurement.py`
- **Agent Tools:** `agent/tools/vendor_tools.py`, `agent/tools/procurement_tools.py`

### Planning & Dependency Engine
- **Frontend:** `web/features/planning/`, `web/features/tasks/`, `web/features/schedule/`
- **API Routes:** `api/routes/plans.py`, `api/routes/tasks.py`
- **Services:** `services/planning_service.py`, `services/dependency_engine.py`
- **Models:** `models/task.py`, `models/dependency.py`, `models/resource.py`
- **Agent Tools:** `agent/tools/planning_tools.py`

### Live Command Center & Incident Detection
- **Frontend:** `web/features/live-command/`, `web/features/incidents/`
- **API Routes:** `api/routes/live_state.py`, `api/routes/incidents.py`
- **Services:** `services/live_state_service.py`, `services/incident_engine.py`
- **Models:** `models/incident.py`, `models/state_transition.py`
- **Agent Tools:** `agent/tools/incident_tools.py`

### Adaptation: Impact, Risk & Recovery Engine
- **Frontend:** `web/features/recovery/`
- **API Routes:** `api/routes/impact.py`, `api/routes/recovery.py`
- **Services:** `services/impact_engine.py`, `services/risk_engine.py`, `services/recovery_engine.py`
- **Models:** `models/recovery.py`
- **Agent Tools:** `agent/tools/recovery_tools.py`

### Human Approval & RBAC
- **Frontend:** `web/features/approvals/`, `web/features/collaborators/`
- **API Routes:** `api/routes/approvals.py`, `api/routes/members.py`
- **Services:** `services/approval_service.py`, `services/rbac_service.py`
- **Models:** `models/approval.py`, `models/event_member.py`, `models/role.py`
- **Agent Tools:** `agent/tools/approval_tools.py`

### Action & Verification
- **Frontend:** `web/features/actions/`, `web/features/verification/`
- **API Routes:** `api/routes/actions.py`, `api/routes/verifications.py`
- **Services:** `services/action_service.py`, `services/verification_service.py`
- **Models:** `models/action.py`, `models/verification.py`
- **Agent Tools:** `agent/tools/action_tools.py`, `agent/tools/verification_tools.py`

### Mobile PWA & Notifications
- **Frontend:** `web/app/manifest.ts`, `web/components/pwa/`, `web/features/notifications/`
- **API Routes:** `api/routes/notifications.py`
- **Services:** `services/notification_service.py`
- **Models:** `models/notification.py`
- **Integrations:** `integrations/notifications/`
- **Agent Tools:** `agent/tools/notification_tools.py`

### Analytics & Audit
- **Frontend:** `web/features/analytics/`, `web/features/activity/`
- **API Routes:** `api/routes/analytics.py`, `api/routes/audit.py`
- **Services:** `services/analytics_service.py`, `services/audit_service.py`
- **Models:** `models/audit.py`

### AI Orchestrator (Single Event Operations Agent)
- **Core Orchestrator:** `agent/event_operations_agent.py`
- **State & Graph Definition:** `agent/graph.py`, `agent/state.py`
- **Tools Bundle:** `agent/tools/`
