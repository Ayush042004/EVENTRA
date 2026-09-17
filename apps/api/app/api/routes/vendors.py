"""API Route: Vendors"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.get("/")
def get_vendors_root():
    return {"status": "ok", "resource": "vendors"}
