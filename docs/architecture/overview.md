# EVENTRA Architecture Overview

## Structural Zones
1. **Domain Zone (`apps/api/app/domains/`, `models/`, `services/`)**: Core entities, state machines, and business rules.
2. **Deterministic Engine Zone (`apps/api/app/engines/`)**: Invariant checking, critical path calculations, dependency graph traversal, and budget arithmetic.
3. **Reasoning Zone (`apps/api/app/agent/`)**: Single Event Operations Agent orchestrated via LangGraph.
4. **Integration Zone (`apps/api/app/integrations/`)**: Boundary isolation for Maps, WhatsApp, Push Notifications, and LLM APIs.
5. **Workflow Zone (`apps/web/`)**: Mobile-first Next.js Progressive Web App organized around operational workflows.
