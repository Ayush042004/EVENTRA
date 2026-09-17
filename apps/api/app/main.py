"""EVENTRA FastAPI Application Entrypoint"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import (
    auth_router, events_router, setup_router, venues_router, vendors_router,
    planning_router, tasks_router, schedule_router, budget_router, live_router,
    incidents_router, impact_router, risk_router, recovery_router, approvals_router,
    procurement_router, notifications_router, collaborators_router, analytics_router,
    audit_router, verification_router, simulation_router
)

app = FastAPI(
    title="EVENTRA Adaptive Event Operations API",
    description="Deterministic calculation engines and AI orchestration for live event operations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All Resource-Oriented Routers
app.include_router(auth_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(setup_router, prefix="/api")
app.include_router(venues_router, prefix="/api")
app.include_router(vendors_router, prefix="/api")
app.include_router(planning_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(schedule_router, prefix="/api")
app.include_router(budget_router, prefix="/api")
app.include_router(live_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(impact_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(recovery_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(procurement_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(collaborators_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "eventra-api", "version": "0.1.0"}
