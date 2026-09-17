"""API Route: Procurement"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/procurement", tags=["procurement"])

@router.get("/")
def get_procurement_root():
    return {"status": "ok", "resource": "procurement"}
