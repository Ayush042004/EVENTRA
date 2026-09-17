"""API Route: Impact"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/impact", tags=["impact"])

@router.get("/")
def get_impact_root():
    return {"status": "ok", "resource": "impact"}
