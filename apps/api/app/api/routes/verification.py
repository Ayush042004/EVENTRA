"""API Route: Verification"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/verification", tags=["verification"])

@router.get("/")
def get_verification_root():
    return {"status": "ok", "resource": "verification"}
