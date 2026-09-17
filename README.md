# EVENTRA — Adaptive Event Operations Platform

> **PLAN THE EVENT. RUN THE EVENT. ADAPT WHEN REALITY CHANGES.**

EVENTRA is an Adaptive Event Operations platform engineered to manage live, complex events. Unlike static planning checklists, EVENTRA maintains a persistent, dependency-aware representation of the event and adapts dynamically when real-world disruptions (vendor delays, venue emergencies, resource shortages) occur.

---

## 1. Core Operational Loop

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

---

## 2. Core Architectural Principle

> **"The deterministic engine calculates what is feasible.**  
> **The agent decides what should happen next."**

- **Backend (PostgreSQL + Domain Services):** The authoritative source of truth. Holds all state machines, invariants, and permissions.
- **Deterministic Engines:** Mathematical engines computing critical path DAGs, topological sort order, budget arithmetic, capacity constraints, and temporal feasibility.
- **Single Event Operations Agent:** An LLM-powered orchestrator (using LangGraph) that reasons through ambiguous trade-offs, evaluates strategic options, and coordinates execution via strongly typed tools.
- **Frontend (Next.js PWA):** Mobile-first operational control center organized around user workflows.

---

## 3. Repository Structure

```text
eventra/
├── .agents/                    # Persistent AI context layer & engineering memory
├── apps/
│   ├── web/                    # Next.js 14/15 PWA frontend (React, Tailwind CSS, shadcn/ui)
│   └── api/                    # FastAPI backend (SQLAlchemy, Pydantic, LangGraph)
├── packages/
│   ├── contracts/              # Shared TypeScript data models, schemas & enums
│   └── config/                 # Shared configurations (tsconfig, linting)
├── docs/
│   ├── architecture/           # System design & component boundaries
│   ├── api/                    # API route contracts and specifications
│   ├── product/                # MVP scope definitions & taxonomy
│   └── demo/                   # Simulation scenarios (Vendor No-Show, Venue, Shortage)
├── scripts/                    # Helper scripts (dev server, seeding, linting)
├── docker/
│   ├── postgres/               # PostgreSQL initialization script
│   └── nginx/                  # Reverse proxy configuration
├── docker-compose.yml          # Local containerized development stack
├── .env.example                # Environment variable templates
├── package.json                # Monorepo root workspace configuration
└── pnpm-workspace.yaml         # Monorepo package paths definition
```

---

## 4. Architectural Rules

1. **Backend is Source of Truth:** No authoritative event state resides in the frontend or agent memory.
2. **LLM Output is Probabilistic:** Never trust LLM arithmetic or dates without deterministic validation.
3. **Agent Decides, Deterministic Engines Calculate:** Prompts never compute critical paths or budget sums.
4. **All Integrations Isolated:** Google Maps, WhatsApp, and LLMs live strictly in `apps/api/app/integrations/`.
5. **Server-Side RBAC:** Access control and spending thresholds are validated on the backend.
6. **No Attendee Subsystem:** Guest count is strictly an aggregate scalar (`guest_count: int`) for capacity calculations.
7. **Authentic Simulation:** Demo simulations inject legitimate incident payloads; they never fake outputs.

---

## 5. Getting Started & Setup

### Prerequisites
- Node.js >= 20.0.0 & npm >= 10.0.0
- Python >= 3.11
- Docker & Docker Compose (optional, for containerized PostgreSQL)

### 1. Environment Setup
```bash
cp .env.example .env
```

### 2. Database Setup (Docker)
```bash
docker-compose up -d postgres
```

### 3. Backend Setup
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup
```bash
# In workspace root
npm install
npm run dev --workspace=apps/web
```

---

## 6. MVP Implementation Sequence (20 Phases)

```text
01. Database Model                     11. Risk Engine
02. Event Setup                        12. Recovery Engine
03. Event Specification                13. Agent (Single Operations Agent)
04. Venue / Location Discovery         14. Collaboration + Approval/RBAC
05. Provider Network & Assignments     15. Action + Autonomy Policy
06. Planning Engine                    16. Verification
07. Dependency Engine (DAG)            17. PWA / UI Workflows
08. Live State Engine                  18. Notifications & Integrations
09. Incident Engine                    19. Analytics & Audit
10. Impact Engine (Blast Radius)       20. Simulation / Demo Hardening
```
