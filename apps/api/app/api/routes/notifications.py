"""API Route: Notifications"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/")
def get_notifications_root():
    return {"status": "ok", "resource": "notifications"}
