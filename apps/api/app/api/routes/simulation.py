"""API Route: Simulation"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/simulation", tags=["simulation"])

@router.get("/")
def get_simulation_root():
    return {"status": "ok", "resource": "simulation"}
