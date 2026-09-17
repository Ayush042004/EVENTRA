"""API Route: Approvals"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/approvals", tags=["approvals"])

@router.get("/")
def get_approvals_root():
    return {"status": "ok", "resource": "approvals"}
