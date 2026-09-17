"""API Route: Live"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/live", tags=["live"])

@router.get("/")
def get_live_root():
    return {"status": "ok", "resource": "live"}
