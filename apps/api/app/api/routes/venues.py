"""API Route: Venues"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/venues", tags=["venues"])

@router.get("/")
def get_venues_root():
    return {"status": "ok", "resource": "venues"}
