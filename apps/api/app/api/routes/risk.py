"""API Route: Risk"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/")
def get_risk_root():
    return {"status": "ok", "resource": "risk"}
