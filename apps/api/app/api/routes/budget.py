"""API Route: Budget"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/budget", tags=["budget"])

@router.get("/")
def get_budget_root():
    return {"status": "ok", "resource": "budget"}
