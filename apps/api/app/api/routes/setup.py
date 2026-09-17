"""API Route: Setup"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/setup", tags=["setup"])

@router.get("/")
def get_setup_root():
    return {"status": "ok", "resource": "setup"}
