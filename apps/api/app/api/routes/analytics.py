"""API Route: Analytics"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/")
def get_analytics_root():
    return {"status": "ok", "resource": "analytics"}
