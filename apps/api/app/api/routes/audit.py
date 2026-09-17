"""API Route: Audit"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/")
def get_audit_root():
    return {"status": "ok", "resource": "audit"}
