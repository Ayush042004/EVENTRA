"""API Route: Schedule"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/schedule", tags=["schedule"])

@router.get("/")
def get_schedule_root():
    return {"status": "ok", "resource": "schedule"}
