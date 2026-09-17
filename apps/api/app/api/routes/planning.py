"""API Route: Planning"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/planning", tags=["planning"])

@router.get("/")
def get_planning_root():
    return {"status": "ok", "resource": "planning"}
