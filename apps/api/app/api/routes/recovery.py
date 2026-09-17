"""API Route: Recovery"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/recovery", tags=["recovery"])

@router.get("/")
def get_recovery_root():
    return {"status": "ok", "resource": "recovery"}
