# EVENTRA API Endpoints Overview

All API endpoints are resource-oriented, mounted under `/api/`, and require scoped event authorization:

- `/api/events`: Event lifecycle management (Draft, Planned, Live, Emergency, Concluded).
- `/api/setup`: Specification, requirements, constraints, and objective priority tagging.
- `/api/venues`: Location discovery, spatial capacity, facility matching, and booking.
- `/api/vendors`: Provider catalog, category filtering, assignment, and contract management.
- `/api/planning`: Work breakdown structure, milestone generation, and baseline compilation.
- `/api/tasks`: Individual task progression, status updates, and assignment bindings.
- `/api/schedule`: Timeline views, Gantt data, and critical path metrics.
- `/api/budget`: Line-item allocations, commitments, and variance tracking.
- `/api/live`: Real-time state telemetry, active task trackers, and health status.
- `/api/incidents`: Incident intake, severity scoring, and blast radius reporting.
- `/api/impact`: Dependency impact graph traversal and affected task identification.
- `/api/risk`: Risk calculations and objective threat level assessments.
- `/api/recovery`: Generated recovery plans, feasibility evaluations, and selection.
- `/api/approvals`: Pending approval tickets, authorization checks, and resolution.
- `/api/procurement`: Equipment and supply manifests, replacement order generation.
- `/api/notifications`: Alert broadcasts, push notifications, and delivery history.
- `/api/collaborators`: Team member roles, scopes, and permission matrices.
- `/api/analytics`: Post-event KPIs, recovery efficiency, and budget variance.
- `/api/audit`: Immutable audit log and state transition timeline.
- `/api/verification`: Post-action verification records and evidence checks.
- `/api/simulation`: Scenario injection runner (Vendor No-Show, Venue Issue, Shortage).
