# UI & PWA Guidelines: EVENTRA

The EVENTRA frontend is an operational Progressive Web App (PWA) designed for desktop planning and high-stress on-the-ground mobile execution.

---

## Canonical Route Structure

Frontend routes are structured around operational workflows rather than generic CRUD tables:

```text
/events/[eventId]/                  # Overview dashboard & operational summary
/events/[eventId]/setup             # Initial specification, requirements & constraints
/events/[eventId]/venue             # Venue discovery, layout review & spatial details
/events/[eventId]/plan              # High-level plan synthesis & milestone builder
/events/[eventId]/live              # Real-time Command Center (Active execution state)
/events/[eventId]/tasks             # Work breakdown structure & task execution cards
/events/[eventId]/vendors           # Vendor network, assignments & contact cards
/events/[eventId]/schedule          # Timeline view & critical path Gantt visualizer
/events/[eventId]/budget            # Financial allocation, commitments & variance
/events/[eventId]/incidents         # Active disruptions, intake form & severity status
/events/[eventId]/recovery          # Proposed recovery plans & impact comparison
/events/[eventId]/procurement       # Supply manifest, purchase orders & reservations
/events/[eventId]/approvals         # Pending supervisor sign-off queue
/events/[eventId]/collaborators     # Team roles, permissions & member access
/events/[eventId]/analytics         # Post-event KPIs, recovery efficiency & SLA adherence
/events/[eventId]/notifications     # Broadcast alerts, activity stream & channel history
/events/[eventId]/activity          # Immutable audit log & state transition timeline
```

---

## PWA Mobile Operational Priorities

When operating on mobile/PWA devices during a live event, the interface must prioritize high-urgency operations over passive configuration:

1. **Live State:** Instant visibility into overall status (`LIVE`, `INCIDENT`, `EMERGENCY`).
2. **Incidents:** One-tap incident reporting and active disruption feed.
3. **Approvals:** Urgent sign-off queue for critical path adjustments.
4. **Recovery:** Quick-comparison cards for recovery options with impact indicators.
5. **Provider Contact:** Fast-dial, quick-message links to assigned on-site vendors.
6. **Location:** Venue zones, loading dock access notes, and floor maps.
7. **Emergency Actions:** Panic escalation, immediate broadcast triggers.
8. **Timeline:** Next upcoming milestones and critical path tasks.
9. **Notifications:** Real-time push alert toasts and banner warnings.

*Rule: Settings, deep historical analytics, and administrative configuration must be secondary on mobile.*

---

## Offline & Connectivity Degradation Policy

Live events frequently experience spotty venue connectivity or cellular blackouts. The PWA adheres to these strict rules:

- **Safe Read Access:** Service Workers must cache the last known authoritative event state, task list, vendor contact book, and venue details for offline viewing.
- **Visual Stale Indicator:** If offline or disconnected from the WebSocket stream, a persistent top banner must indicate `Offline — Showing state from HH:MM`.
- **Safe Local Queue:** Non-critical user updates (e.g. marking a non-blocking checklist item done, taking an internal note) may be queued locally in IndexedDB with an optimistic pending badge.
- **NEVER Execute Critical Actions Offline:**  
  Approving a venue change, dispatching a vendor replacement, committing budget, or resolving an emergency incident **CANNOT** be executed offline. The UI must disable critical action buttons until backend connectivity and authoritative validation are re-established.
