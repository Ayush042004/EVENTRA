"""API Route: Incidents"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("/")
def get_incidents_root():
    return {"status": "ok", "resource": "incidents"}
